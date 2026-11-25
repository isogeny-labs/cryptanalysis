//! Exhaustive semantic check for the inversion-free two-chord circuit.
//! This checks an algebraic predicate for a prospective Tseitin CNF; it does
//! not run SAT, survey propagation, or a benchmark screen.

use prime_field_m3_cdclt::{sqrt_mod_canonical, CurveFp, FpOps, PointFp};
use std::collections::HashMap;

fn sub(a: u64, b: u64, p: u64) -> u64 {
    (a + p - b) % p
}
fn add(a: u64, b: u64, p: u64) -> u64 {
    (a + b) % p
}
fn mul(a: u64, b: u64, p: u64) -> u64 {
    ((a as u128 * b as u128) % p as u128) as u64
}

// Numerators (A,B) with affine coordinates (A/d^2,B/d^3).
fn chord_numerators(first: PointFp, second: PointFp, p: u64) -> (u64, u64, u64) {
    let d = sub(second.x, first.x, p);
    assert_ne!(d, 0);
    let n = sub(second.y, first.y, p);
    let d2 = mul(d, d, p);
    let d3 = mul(d2, d, p);
    let a = sub(mul(n, n, p), mul(add(first.x, second.x, p), d2, p), p);
    let b = sub(
        mul(n, sub(mul(first.x, d2, p), a, p), p),
        mul(first.y, d3, p),
        p,
    );
    (a, b, d)
}

fn circuit_predicate(p0: PointFp, p1: PointFp, p2: PointFp, q: PointFp, p: u64) -> bool {
    let neg_p2 = PointFp::affine(p2.x, sub(0, p2.y, p));
    let (a, b, d) = chord_numerators(p0, p1, p);
    let (c, e, f) = chord_numerators(q, neg_p2, p);
    let d2 = mul(d, d, p);
    let f2 = mul(f, f, p);
    mul(a, f2, p) == mul(c, d2, p) && mul(b, mul(f2, f, p), p) == mul(e, mul(d2, d, p), p)
}

fn check(ir: &str, expected_models: usize) {
    let fields: HashMap<_, _> = ir
        .lines()
        .skip(1)
        .map(|line| line.split_once('=').unwrap())
        .collect();
    assert_eq!(ir.lines().next(), Some("prime-field-m3-ir/v2"));
    let parse = |name: &str| fields[name].parse::<u64>().unwrap();
    let curve = CurveFp {
        p: parse("p"),
        a: parse("a"),
        b: parse("b"),
    };
    let (qx, qy) = fields["target"].split_once(',').unwrap();
    let q = PointFp::affine(qx.parse().unwrap(), qy.parse().unwrap());
    let mut ops = FpOps::default();
    assert!(curve.is_nonsingular() && curve.on_curve(q, &mut ops));
    let points: [Vec<PointFp>; 3] = std::array::from_fn(|w| {
        fields[format!("window{w}").as_str()]
            .split(',')
            .flat_map(|word| {
                let x: u64 = word.parse().unwrap();
                let y = sqrt_mod_canonical(curve.rhs(x, &mut ops), curve.p, &mut ops).unwrap();
                assert_ne!(y, 0);
                [
                    curve.point_from_canonical_lift(x, y, 0),
                    curve.point_from_canonical_lift(x, y, 1),
                ]
            })
            .collect()
    });
    for window in &points {
        assert_eq!(window.len(), 64);
    }
    for p0 in &points[0] {
        for p1 in &points[1] {
            assert_ne!(p0.x, p1.x, "first chord must be nonvertical");
        }
    }
    for p2 in &points[2] {
        assert_ne!(q.x, p2.x, "second chord must be nonvertical");
    }

    let mut count = 0;
    for &p0 in &points[0] {
        for &p1 in &points[1] {
            for &p2 in &points[2] {
                let direct = curve.add(curve.add(p0, p1, &mut ops), p2, &mut ops) == q;
                let circuit = circuit_predicate(p0, p1, p2, q, curve.p);
                assert_eq!(circuit, direct, "selection {p0:?}, {p1:?}, {p2:?}");
                count += usize::from(direct);
            }
        }
    }
    assert_eq!(count, expected_models);
}

#[test]
fn all_18_bit_selections_match_exact_group_addition() {
    check(include_str!("../fixtures/s5/lead2b-s5-planted.ir"), 1);
    check(include_str!("../fixtures/s5/lead2b-s5-natural.ir"), 0);
    check(include_str!("../fixtures/s5/lead2b-s5-exact-unsat.ir"), 0);
}
