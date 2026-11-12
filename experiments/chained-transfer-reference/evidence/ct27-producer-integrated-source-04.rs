//! Producer fixture generation only. Independent second-engine replay is
//! a separate obligation; no producer operation is used by that checker.
use crate::balanced::{Balanced, Class};
use num_traits::ToPrimitive;
use std::collections::HashMap;

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

fn generate(curve: [u64; 7]) -> [Vec<u8>; 4] {
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
    assert_eq!(indices[&key(&b.zero())], 239);
    [classes, negation, doubling, pairs]
}

struct Case {
    name: &'static str,
    curve: [u64; 7],
    expected: [&'static [u8]; 4],
}

#[test]
fn complete_t0_t1_fixtures_match_existing_balanced_arithmetic() {
    let cases = [
        Case {
            name: "T0",
            curve: [31, 75, 74, 54, 71, 55, 1],
            expected: [
                include_bytes!("../fixtures/full-class/t0-classes.bin"),
                include_bytes!("../fixtures/full-class/t0-negation.bin"),
                include_bytes!("../fixtures/full-class/t0-doubling.bin"),
                include_bytes!("../fixtures/full-class/t0-pairs-37-7.bin"),
            ],
        },
        Case {
            name: "T1",
            curve: [95, 26, 19, 27, 94, 91, 1],
            expected: [
                include_bytes!("../fixtures/full-class/t1-classes.bin"),
                include_bytes!("../fixtures/full-class/t1-negation.bin"),
                include_bytes!("../fixtures/full-class/t1-doubling.bin"),
                include_bytes!("../fixtures/full-class/t1-pairs-37-7.bin"),
            ],
        },
    ];
    for case in cases {
        let actual = generate(case.curve);
        for (i, (got, expected)) in actual.iter().zip(case.expected).enumerate() {
            assert_eq!(
                got.len(),
                expected.len(),
                "{} operator{i} length",
                case.name
            );
            assert!(
                got.as_slice() == expected,
                "{} operator{i} first difference{:?}",
                case.name,
                got.iter().zip(expected).position(|(a, b)| a != b)
            );
        }
        println!("PASS {} all12317 actual Balanced classes,all frozen negation/doubling/paired37i+7 index tables reproduce exactly;separate existing-Cantor replay remains an independent obligation,no timing claim",case.name);
    }
}
