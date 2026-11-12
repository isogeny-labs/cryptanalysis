//! Producer fixture generation only. Independent second-engine replay is
//! a separate obligation; no producer operation is used by that checker.
use crate::balanced::{Balanced, Class};
use num_traits::ToPrimitive;
use std::collections::HashMap;
use std::path::PathBuf;

type Key = (Vec<u64>, Vec<u64>, u8);
fn key(d: &Class) -> Key {
    let (u, v, plus) = d.components();
    let coefficients =
        |p: &crate::reference::FpPoly| p.coeffs.iter().map(|c| c.to_u64().unwrap()).collect();
    (coefficients(u), coefficients(v), plus)
}

fn header(magic: &[u8; 8], curve: &[u64; 7], count: usize) -> Vec<u8> {
    let mut out = magic.to_vec();
    out.push(101);
    out.extend(curve.iter().map(|c| u8::try_from(*c).unwrap()));
    out.extend(u16::try_from(count).unwrap().to_le_bytes());
    out
}

#[test]
fn export_complete_balanced_t1_corpus_and_operator_fixtures() {
    let output =
        PathBuf::from(std::env::var_os("CHAINED_CT27_OUT").expect("explicit fixture directory"));
    std::fs::create_dir_all(&output).unwrap();
    let curve = [95, 26, 19, 27, 94, 91, 1];
    let b = Balanced::new(101, &curve).unwrap();
    let all = b.classes().unwrap();
    assert_eq!(all.len(), 12317);
    let indices: HashMap<Key, u16> = all
        .iter()
        .enumerate()
        .map(|(i, d)| (key(d), u16::try_from(i).unwrap()))
        .collect();
    assert_eq!(indices.len(), all.len());
    let mut classes = header(b"CT27CLS1", &curve, all.len());
    let mut negation = header(b"CT27NEG1", &curve, all.len());
    let mut doubling = header(b"CT27DBL1", &curve, all.len());
    let mut pairs = header(b"CT27ADD1", &curve, all.len());
    let mut degrees = [0_usize; 3];
    let mut infinity = [0_usize; 5];
    for (i, d) in all.iter().enumerate() {
        let (u, v, plus) = d.components();
        let degree = u.degree().unwrap();
        assert!(degree <= 2 && usize::from(plus) <= 2 - degree);
        degrees[degree] += 1;
        let correction = 2 * i32::from(plus) + degree as i32 - 2;
        infinity[usize::try_from(correction + 2).unwrap()] += 1;
        let coefficient =
            |p: &crate::reference::FpPoly, i| u8::try_from(p.coeff(i).to_u64().unwrap()).unwrap();
        let row = [
            u8::try_from(3 * degree).unwrap() + plus,
            if degree > 0 { coefficient(u, 0) } else { 0 },
            if degree == 2 { coefficient(u, 1) } else { 0 },
            coefficient(v, 0),
            coefficient(v, 1),
        ];
        assert!(row.iter().all(|c| *c < 101));
        classes.extend(row);
        let negative = b.neg(d).unwrap();
        let double = b.add(d, d).unwrap();
        let partner = &all[(37 * i + 7) % all.len()];
        let sum = b.add(d, partner).unwrap();
        for (table, image) in [
            (&mut negation, negative),
            (&mut doubling, double),
            (&mut pairs, sum),
        ] {
            table.extend(indices[&key(&image)].to_le_bytes());
        }
    }
    assert_eq!(degrees, [3, 236, 12078]);
    assert_eq!(infinity, [1, 118, 12079, 118, 1]);
    assert_eq!(classes.len(), 18 + 5 * all.len());
    for table in [&negation, &doubling, &pairs] {
        assert_eq!(table.len(), 18 + 2 * all.len());
    }
    for (name, data) in [
        ("t1-classes.bin", classes),
        ("t1-negation.bin", negation),
        ("t1-doubling.bin", doubling),
        ("t1-pairs-37-7.bin", pairs),
    ] {
        std::fs::write(output.join(name), data).unwrap();
    }
    let identity = indices[&key(&b.zero())];
    let manifest = format!("CT27 producer fixture v1\np=101\ncurve={curve:?}\ncount={}\nidentity_index={identity}\ndegrees={degrees:?}\ninfinity_corrections_minus2_to2={infinity:?}\nheader=magic8,p_u8,curve7_u8,count_u16le\nclass_row=degree_times3_plus_n,u0,u1,v0,v1;implicit_monic_lead;unused_support_coefficients_zero\noperator_row=result_index_u16le\npaired_partner=(37*i+7)%12317\nstanding=unsigned;independent_replay_pending\n",all.len());
    std::fs::write(output.join("t1-manifest.txt"), manifest).unwrap();
    println!("PRODUCER T1 complete{} classes;degree counts{degrees:?};infinity corrections{infinity:?};all negation/doubling/paired-addition indices exported. Independent second-engine replay remains pending;no timing claim.",all.len());
}
