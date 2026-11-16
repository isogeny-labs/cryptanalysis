//! Seal/replay the quadratic norm polynomial using the unchanged native issuer.
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
    let [a, b, c, d, n] = ["a", "b", "c", "d", "nu"].map(Expr::var);
    let real = add(
        mul(a.clone(), c.clone()),
        mul(n.clone(), mul(b.clone(), d.clone())),
    );
    let imag = add(mul(a.clone(), d.clone()), mul(b.clone(), c.clone()));
    let lhs = if bad {
        sq(real)
    } else {
        add(sq(real), neg(mul(n.clone(), sq(imag))))
    };
    let rhs = mul(
        add(sq(a), neg(mul(n.clone(), sq(b)))),
        add(sq(c), neg(mul(n, sq(d)))),
    );
    IdentityStatement {name:"Multiplicativity of a^2-nu*b^2 for quadratic coordinates".into(),source:"BETA_RATIONAL_LIFT_DERIVATION_01; elementary coefficient expansion, supporting quadratic-field inversion; no novelty claim".into(),variables:vec!["a".into(),"b".into(),"c".into(),"d".into(),"nu".into()],degree_bound:6,lhs,rhs}
}
type Poly = BTreeMap<[u8; 5], i64>;
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
            let mut k = [0; 5];
            for i in 0..5 {
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
            let mut k = [0; 5];
            k[["a", "b", "c", "d", "nu"]
                .iter()
                .position(|s| *s == v)
                .unwrap()] = 1;
            [(k, 1)].into_iter().collect()
        }
        Expr::Const(n) => {
            if *n == 0 {
                Poly::new()
            } else {
                [([0; 5], *n)].into_iter().collect()
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
            .fold([([0; 5], 1)].into_iter().collect(), product),
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
            original::check_with_extra(&cert, Some((0x734c494654, 32))).unwrap(),
            Verdict::Accept { .. }
        ));
        println!(
            "ORIGINAL_IDENTITY_CHECK {} exact-Z-coefficients and extra32points",
            cert.id
        );
        return;
    }
    let bad = args.get(1).map(String::as_str) == Some("--missing-imaginary-term");
    assert!(args.len() == 1 || bad);
    let statement = statement(bad);
    if !bad {
        assert_eq!(expand(&statement.lhs), expand(&statement.rhs));
    }
    let proof = original::ProofRef {
        kind: "lean4".into(),
        path: "experiments/chained-transfer-public-target/beta-rational-lift/lean/QuadraticNormIdentity.lean".into(),
        sha256: hex::encode(original_sha256::sha256(include_bytes!("../../lean/QuadraticNormIdentity.lean"))),
    };
    let cert = original::issue(
        statement, 0x734e4f524d, 64,
        "unchanged producer3d49 native issuer/checker; exact integer coefficient expansion in caller; Lean source pointer checked separately; unsigned process evidence",
        Some(proof),
    ).expect("original issuer rejects a false quadratic norm identity");
    assert!(matches!(
        original::check_with_extra(&cert, Some((0x734c494654, 32))).unwrap(),
        Verdict::Accept { .. }
    ));
    eprintln!("ORIGINAL_IDENTITY_CHECK {} exact-Z-coefficients/64sealed+32extra; Lean source pointer attached; original checker does not run Lean",cert.id);
    println!("{}", serde_json::to_string_pretty(&cert).unwrap());
}
