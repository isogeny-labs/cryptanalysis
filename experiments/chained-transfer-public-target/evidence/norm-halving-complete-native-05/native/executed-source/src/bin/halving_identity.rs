//! Exact integer coefficient expansion plus the unchanged original issuer/checker.
#![allow(dead_code)]
#[path = "../../../../../../crypto/src/hash/sha256.rs"]
mod original_sha256;
mod hash {
    pub mod sha256 {
        pub use crate::original_sha256::*;
    }
}
#[path = "../../../../../../crypto/src/cryptanalysis/identity_certificate.rs"]
mod original;
use original::{Expr, IdentityStatement, Verdict};
use std::collections::BTreeMap;

fn add(xs: Vec<Expr>) -> Expr {
    Expr::Add(xs)
}
fn mul(xs: Vec<Expr>) -> Expr {
    Expr::Mul(xs)
}
fn neg(x: Expr) -> Expr {
    Expr::Neg(Box::new(x))
}
fn power(x: Expr, n: usize) -> Expr {
    mul(vec![x; n])
}
fn scale(n: i64, x: Expr) -> Expr {
    mul(vec![Expr::Const(n), x])
}
fn curve(x: Expr, a: Expr, b: Expr) -> Expr {
    add(vec![power(x.clone(), 3), mul(vec![a, x]), b])
}
fn quartic(x: Expr, a: Expr, b: Expr, u: Expr) -> Expr {
    add(vec![
        power(x.clone(), 4),
        scale(-4, mul(vec![u.clone(), power(x.clone(), 3)])),
        scale(-2, mul(vec![a.clone(), power(x.clone(), 2)])),
        scale(
            -4,
            mul(vec![
                add(vec![mul(vec![a.clone(), u.clone()]), scale(2, b.clone())]),
                x,
            ]),
        ),
        power(a, 2),
        scale(-4, mul(vec![b, u])),
    ])
}
fn statement(index: usize, bad: bool) -> IdentityStatement {
    let [x, a, b, u] = ["x", "a", "b", "u"].map(Expr::var);
    let h = quartic(x.clone(), a.clone(), b.clone(), u.clone());
    let (lhs, rhs, name, degree) = if index == 0 {
        (
            add(vec![
                power(add(vec![scale(3, power(x.clone(), 2)), a.clone()]), 2),
                scale(
                    -4,
                    mul(vec![
                        curve(x.clone(), a.clone(), b.clone()),
                        add(vec![scale(2, x.clone()), u.clone()]),
                    ]),
                ),
            ]),
            h,
            "Existing complete halving abscissa quartic",
            4,
        )
    } else {
        let mut terms = vec![
            power(x.clone(), 3),
            scale(-3, mul(vec![u.clone(), power(x.clone(), 2)])),
            neg(mul(vec![a.clone(), x.clone()])),
            neg(mul(vec![a.clone(), u.clone()])),
        ];
        if !bad {
            terms.push(scale(-2, b.clone()))
        }
        let t = add(terms);
        (
            add(vec![
                power(t, 2),
                scale(
                    -4,
                    mul(vec![
                        curve(u.clone(), a.clone(), b.clone()),
                        curve(x.clone(), a.clone(), b.clone()),
                    ]),
                ),
            ]),
            mul(vec![h, power(add(vec![x, neg(u)]), 2)]),
            "Complete halving cleared ordinate identity",
            6,
        )
    };
    IdentityStatement{name:name.into(),source:"NORM_HALVING_PROTOCOL_01; Sutherland2025Lecture2sec2.2; NormHalving.halving_abscissa_identity and halving_ordinate_identity; source/field/geometry bridges separate".into(),variables:["x","a","b","u"].map(String::from).to_vec(),degree_bound:degree,lhs,rhs}
}
type Poly = BTreeMap<[u8; 4], i64>;
fn plus(mut a: Poly, b: Poly) -> Poly {
    for (k, v) in b {
        let n = a.get(&k).copied().unwrap_or(0).checked_add(v).unwrap();
        if n == 0 {
            a.remove(&k);
        } else {
            a.insert(k, n);
        }
    }
    a
}
fn product(a: Poly, b: Poly) -> Poly {
    let mut out = Poly::new();
    for (ka, va) in &a {
        for (kb, vb) in &b {
            let k = std::array::from_fn(|i| ka[i].checked_add(kb[i]).unwrap());
            let v = va.checked_mul(*vb).unwrap();
            out = plus(out, [(k, v)].into_iter().collect());
        }
    }
    out
}
fn expand(x: &Expr) -> Poly {
    match x {
        Expr::Var(v) => {
            let mut k = [0; 4];
            k[["x", "a", "b", "u"].iter().position(|s| *s == v).unwrap()] = 1;
            [(k, 1)].into_iter().collect()
        }
        Expr::Const(n) => {
            if *n == 0 {
                Poly::new()
            } else {
                [([0; 4], *n)].into_iter().collect()
            }
        }
        Expr::Neg(x) => expand(x)
            .into_iter()
            .map(|(k, v)| (k, v.checked_neg().unwrap()))
            .collect(),
        Expr::Add(xs) => xs.iter().map(expand).fold(Poly::new(), plus),
        Expr::Mul(xs) => xs
            .iter()
            .map(expand)
            .fold([([0; 4], 1)].into_iter().collect(), product),
    }
}
fn check_exact(s: &IdentityStatement) {
    assert!(
        expand(&s.lhs) == expand(&s.rhs),
        "exact universal-Z coefficient mismatch"
    );
}
fn main() {
    let args: Vec<_> = std::env::args().collect();
    if args.get(1).map(String::as_str) == Some("--verify") {
        assert_eq!(args.len(), 3);
        let certs: Vec<original::IdentityCertificate> =
            serde_json::from_slice(&std::fs::read(&args[2]).unwrap()).unwrap();
        assert_eq!(certs.len(), 2);
        for (i, cert) in certs.iter().enumerate() {
            let expected = statement(i, false);
            assert_eq!(cert.statement.name, expected.name);
            assert_eq!(cert.statement.variables, expected.variables);
            assert_eq!(cert.statement.degree_bound, expected.degree_bound);
            assert!(
                expand(&cert.statement.lhs) == expand(&expected.lhs)
                    && expand(&cert.statement.rhs) == expand(&expected.rhs)
            );
            check_exact(&cert.statement);
            assert!(matches!(
                original::check_with_extra(cert, Some((0x7448414c5600 + i as u64, 32))).unwrap(),
                Verdict::Accept { .. }
            ));
            println!(
                "ORIGINAL_HALVING_IDENTITY_CHECK {} exact-Z/64sealed32extra",
                cert.id
            );
        }
        return;
    }
    let bad = args.get(1).map(String::as_str) == Some("--missing-linear-term");
    assert!(args.len() == 1 || (bad && args.len() == 2));
    let mut certs = Vec::new();
    for i in if bad { 1..2 } else { 0..2 } {
        let s = statement(i, bad);
        if bad {
            let difference = plus(
                expand(&s.lhs),
                expand(&s.rhs).into_iter().map(|(k, v)| (k, -v)).collect(),
            );
            assert!(!difference.is_empty());
            eprintln!(
                "FALSE_ORDINATE_EXACT_Z_DIFFERENCE {}",
                serde_json::to_string(
                    &difference
                        .iter()
                        .map(|(k, v)| serde_json::json!({"powers":k,"coefficient":v}))
                        .collect::<Vec<_>>()
                )
                .unwrap()
            );
        } else {
            check_exact(&s)
        }
        let proof=original::ProofRef{kind:"lean4".into(),path:"experiments/chained-transfer-public-target/norm-halving-evaluator/lean/NormHalving.lean".into(),sha256:hex::encode(original_sha256::sha256(include_bytes!("../../lean/NormHalving.lean")))};
        let cert=original::issue(s,0x7448414c56+i as u64,64,"unchanged producer issuer/checker; exact integer coefficient expansion in caller; Lean pointer checked separately, issuer does not run Lean; unsigned process evidence",Some(proof)).expect("original issuer rejects a missing ordinate term");
        assert!(matches!(
            original::check_with_extra(&cert, Some((0x7448414c5600 + i as u64, 32))).unwrap(),
            Verdict::Accept { .. }
        ));
        eprintln!(
            "ORIGINAL_HALVING_IDENTITY_CHECK {} exact-Z/64sealed32extra",
            cert.id
        );
        certs.push(cert);
    }
    println!("{}", serde_json::to_string_pretty(&certs).unwrap());
}
