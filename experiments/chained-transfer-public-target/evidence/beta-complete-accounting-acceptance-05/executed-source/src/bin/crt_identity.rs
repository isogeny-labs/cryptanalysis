//! Seal/replay the CRT projection polynomial using the unchanged native issuer.
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

fn add(x: Expr, y: Expr) -> Expr {
    Expr::Add(vec![x, y])
}
fn mul(x: Expr, y: Expr) -> Expr {
    Expr::Mul(vec![x, y])
}
fn neg(x: Expr) -> Expr {
    Expr::Neg(Box::new(x))
}
fn sq(x: Expr) -> Expr {
    mul(x.clone(), x)
}
fn statement(bad: bool) -> IdentityStatement {
    let m = Expr::var("m");
    let e = add(mul(Expr::Const(4), m.clone()), Expr::Const(1));
    let lhs = if bad {
        sq(e.clone())
    } else {
        add(sq(e.clone()), neg(e.clone()))
    };
    let rhs = mul(mul(Expr::Const(4), m), e);
    IdentityStatement{name:"Cofactor projection scalar identity for ell=4m+1".into(),source:"BETA_COMPLETE_RATIONAL_DERIVATION_01 and CompleteRationalBeta.rational_decomposition; elementary exact coefficient identity, not a certificate of actual group maps or geometry".into(),variables:vec!["m".into()],degree_bound:2,lhs,rhs}
}
type Poly = BTreeMap<[u8; 1], i64>;
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
    let mut r = Poly::new();
    for (ka, va) in &a {
        for (kb, vb) in &b {
            let mut k = [0; 1];
            for i in 0..1 {
                k[i] = ka[i].checked_add(kb[i]).unwrap();
            }
            let t = va.checked_mul(*vb).unwrap();
            r = plus(r, [(k, t)].into_iter().collect());
        }
    }
    r
}
fn expand(x: &Expr) -> Poly {
    match x {
        Expr::Var(v) => {
            let mut k = [0; 1];
            k[["m"].iter().position(|s| *s == v).unwrap()] = 1;
            [(k, 1)].into_iter().collect()
        }
        Expr::Const(n) => {
            if *n == 0 {
                Poly::new()
            } else {
                [([0; 1], *n)].into_iter().collect()
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
            .fold([([0; 1], 1)].into_iter().collect(), product),
    }
}
fn main() {
    let args: Vec<_> = std::env::args().collect();
    if args.get(1).map(String::as_str) == Some("--verify") {
        assert_eq!(args.len(), 3);
        let cert: original::IdentityCertificate =
            serde_json::from_slice(&std::fs::read(&args[2]).unwrap()).unwrap();
        assert_eq!(expand(&cert.statement.lhs), expand(&cert.statement.rhs));
        assert!(matches!(
            original::check_with_extra(&cert, Some((0x734352544c, 32))).unwrap(),
            Verdict::Accept { .. }
        ));
        println!(
            "ORIGINAL_CRT_IDENTITY_CHECK {} exact-Z-coefficients and extra32points",
            cert.id
        );
        return;
    }
    let bad = args.get(1).map(String::as_str) == Some("--missing-linear-term");
    assert!(args.len() == 1 || (bad && args.len() == 2));
    let statement = statement(bad);
    if !bad {
        assert_eq!(expand(&statement.lhs), expand(&statement.rhs));
    }
    let proof = original::ProofRef {
        kind: "lean4".into(),
        path: "experiments/chained-transfer-public-target/beta-complete-evaluator/lean/CRTProjectionIdentity.lean".into(),
        sha256: hex::encode(original_sha256::sha256(include_bytes!("../../lean/CRTProjectionIdentity.lean"))),
    };
    let cert = original::issue(
        statement, 0x73435254, 64,
        "unchanged producer3d49 native issuer/checker; exact integer coefficient expansion in caller; Lean source pointer checked separately; unsigned process evidence",
        Some(proof),
    ).expect("original issuer rejects a false CRT projection identity");
    assert!(matches!(
        original::check_with_extra(&cert, Some((0x734352544c, 32))).unwrap(),
        Verdict::Accept { .. }
    ));
    eprintln!("ORIGINAL_CRT_IDENTITY_CHECK {} exact-Z-coefficients/64sealed+32extra; Lean source pointer attached; original checker does not run Lean",cert.id);
    println!("{}", serde_json::to_string_pretty(&cert).unwrap());
}
