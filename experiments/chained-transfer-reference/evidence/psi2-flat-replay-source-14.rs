//! Replay only curve-divisor validity and Frobenius,using the pre-existing flat
//! field/poly engines. No producer tower,closed map,or elliptic generator imports.
use isogeny_algos::field::Field;
use isogeny_algos::fpr::{FpR, ER};
use isogeny_algos::poly;
use std::collections::HashSet;

fn parse_polynomial(f: &FpR, text: &str, basis: &[ER; 6]) -> Vec<ER> {
    if text == "[]" {
        return vec![];
    }
    let inner = text.strip_prefix('[').unwrap().strip_suffix(']').unwrap();
    inner
        .split("], [")
        .map(|part| {
            let coefficients = part
                .trim_matches(['[', ']'])
                .split(',')
                .map(|c| c.trim().parse::<u64>().unwrap())
                .collect::<Vec<_>>();
            assert_eq!(coefficients.len(), 6);
            assert!(coefficients.iter().all(|c| *c < 101));
            coefficients
                .iter()
                .zip(basis)
                .fold(f.zero(), |out, (c, b)| {
                    f.add(out, f.mul(f.from_u64(*c), *b))
                })
        })
        .collect()
}

fn replay(witness: &str, header: &str, coefficients: &[u64; 7], prefix: Option<&str>) {
    let f = FpR::from_modulus(101, &[33, 46, 2, 18, 56, 12, 1]);
    let g = f.gen();
    let lift = |p: &[u64]| p.iter().map(|c| f.from_u64(*c)).collect::<Vec<_>>();
    let numerator = poly::eval(&f, &lift(&[68, 19, 6, 1]), g);
    let denominator = poly::eval(&f, &lift(&[15, 12, 3]), g);
    assert_ne!(denominator, f.zero());
    let s = f.div(numerator, denominator);
    let t = f.sub(g, s);
    assert_eq!(f.sq(s), f.from_u64(2));
    assert_eq!(poly::eval(&f, &lift(&[56, 13, 6, 1]), t), f.zero());
    assert_ne!(f.frobenius(t), t);
    assert_eq!(f.frobenius(f.frobenius(f.frobenius(t))), t);
    assert_eq!(f.frobenius(f.frobenius(f.frobenius(s))), f.neg(s));
    let basis = [f.one(), t, f.sq(t), s, f.mul(s, t), f.mul(s, f.sq(t))];
    let mut lines = witness.lines();
    assert_eq!(lines.next().unwrap(), header);
    let curve = lift(coefficients);
    assert_eq!(
        poly::gcd(&f, &curve, &poly::derivative(&f, &curve)),
        vec![f.one()]
    );
    let mut classes = vec![];
    for (i, line) in lines.enumerate() {
        let columns = line.split('\t').collect::<Vec<_>>();
        let offset = usize::from(prefix.is_some());
        assert_eq!(columns.len(), 4 + offset);
        if let Some(prefix) = prefix {
            assert_eq!(columns[0], prefix);
        }
        assert_eq!(columns[offset].parse::<usize>().unwrap(), i);
        let u = parse_polynomial(&f, columns[1 + offset], &basis);
        let v = parse_polynomial(&f, columns[2 + offset], &basis);
        let plus = columns[3 + offset].parse::<u8>().unwrap();
        assert_eq!(u.last(), Some(&f.one()));
        assert!(v.is_empty() || v.last() != Some(&f.zero()));
        assert!(v.len() < u.len());
        if i == 0 {
            assert_eq!((&u, &v, plus), (&vec![f.one()], &vec![], 1));
        } else {
            assert_eq!((u.len(), plus), (3, 0));
        }
        assert!(
            poly::rem(&f, &poly::sub(&f, &curve, &poly::mul(&f, &v, &v)), &u).is_empty(),
            "actual curve{coefficients:?} divisor validity{i}"
        );
        classes.push((u, v, plus));
    }
    assert_eq!(classes.len(), 49);
    assert_eq!(classes.iter().cloned().collect::<HashSet<_>>().len(), 49);
    for (i, (u, v, plus)) in classes.iter().enumerate() {
        let image = (
            u.iter().map(|c| f.frobenius(*c)).collect::<Vec<_>>(),
            v.iter().map(|c| f.frobenius(*c)).collect::<Vec<_>>(),
            *plus,
        );
        let index = ((i / 7 * 5) % 7) * 7 + (i % 7 * 6) % 7;
        assert_eq!(image, classes[index], "flat Frobenius row{i}");
    }
    let fixed: Vec<usize> = [1, 2, 3, 6]
        .map(|degree| {
            classes
                .iter()
                .filter(|(u, v, _)| {
                    u.iter().chain(v).all(|c| {
                        let mut image = *c;
                        for _ in 0..degree {
                            image = f.frobenius(image);
                        }
                        image == *c
                    })
                })
                .count()
        })
        .to_vec();
    assert_eq!(fixed, [1, 7, 1, 49]);
    println!("PASS frozen49 kernel TSV rows for curve{coefficients:?},semantic T/S basis,canonical coefficient/shape/curve validity/distinctness and all Frobenius5/6 permutation checks in unchanged flatFpR/poly engines;fixed counts degrees1/2/3/6={fixed:?};no producer tower/closed-map/generator imported,no independent Jacobian addition or kernel-membership verdict");
}

#[test]
fn explicit_psi_kernel_flat_validity_and_frobenius_replay() {
    replay(include_str!("../fixtures/explicit-psi-kernel-07.tsv"),
        "# explicit-psi-kernel/v1;p101;T^3+6T^2+13T+56=0;S^2=2;basis[1,T,T2,S,ST,ST2];T0[31,75,74,54,71,55,1];index,u_coefficients,v_coefficients,plus",
        &[31,75,74,54,71,55,1], Some("actualPsiKernel"));
}

#[test]
fn explicit_psi2_kernel_flat_validity_and_frobenius_replay() {
    replay(include_str!("../fixtures/explicit-psi2-kernel-12.tsv"),
        "# explicit-psi2-kernel/v1;p101;T^3+6T^2+13T+56=0;S^2=2;basis[1,T,T2,S,ST,ST2];T1[95,26,19,27,94,91,1];index,u_coefficients,v_coefficients,plus",
        &[95,26,19,27,94,91,1], None);
}
