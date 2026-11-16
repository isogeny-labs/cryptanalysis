use prime_field_auxiliary_ic::*;
use std::collections::BTreeSet;

fn mul(p: u64, a: u64, b: u64) -> u64 {
    (u128::from(a) * u128::from(b) % u128::from(p)) as u64
}
fn pow(p: u64, mut a: u64, mut n: u64) -> u64 {
    let mut r = 1;
    while n != 0 {
        if n & 1 != 0 {
            r = mul(p, r, a);
        }
        a = mul(p, a, a);
        n >>= 1;
    }
    r
}
fn power_roots(p: u64, degree: u32, coset: u64) -> Vec<u64> {
    let n = u64::from(degree);
    let g = (2..4096)
        .map(|g| pow(p, g, (p - 1) / n))
        .find(|&g| {
            [2, 3, 7]
                .iter()
                .all(|&q| n % q != 0 || pow(p, g, n / q) != 1)
        })
        .unwrap();
    let mut v = coset;
    (0..degree)
        .map(|_| {
            let r = v;
            v = mul(p, v, g);
            r
        })
        .collect()
}
fn torus_roots<const B: u32>(base: &FactorBase<B>) -> Vec<u64> {
    let p = base.curve().modulus();
    let FactorBaseEncoding::Torus { depth, trace } = base.encoding() else {
        panic!("wrong encoding")
    };
    let f = |v| (mul(p, v, v) + p - 2) % p;
    let mut order_check = trace;
    for _ in 0..B - 1 {
        order_check = f(order_check);
    }
    assert_eq!(order_check, p - 2);
    let mut expected = trace;
    for _ in 0..depth {
        expected = f(expected);
    }
    assert_eq!(expected, base.terminal_coordinate());
    let mut roots = vec![expected];
    for _ in 0..depth {
        roots = roots
            .into_iter()
            .flat_map(|v| {
                let r = pow(p, (v + 2) % p, (p + 1) / 4);
                assert_ne!(r, 0);
                assert_eq!(mul(p, r, r), (v + 2) % p);
                [r, p - r]
            })
            .collect();
    }
    if p == 127 {
        let enumerated: BTreeSet<_> = (0..p)
            .filter(|&x| {
                let mut v = x;
                for _ in 0..depth {
                    v = f(v);
                }
                v == expected
            })
            .collect();
        assert_eq!(enumerated, roots.iter().copied().collect());
    }
    roots
}
fn explicit_product<const B: u32>(curve: Curve<B>, roots: &[u64], x: u64, target: u64) -> u64 {
    let p = curve.modulus();
    let (a, b) = curve.coefficients();
    let add = |x, y| (x + y) % p;
    let sub = |x, y| (x + p - y) % p;
    let m = |x, y| mul(p, x, y);
    let product = m(x, target);
    let sum = add(x, target);
    let t = sub(product, a);
    let d = m(sub(x, target), sub(x, target));
    let c = m(2, add(m(sum, add(product, a)), m(2, b)));
    let h = sub(m(t, t), m(m(4, b), sum));
    roots
        .iter()
        .fold(1, |acc, &r| m(acc, add(sub(m(d, m(r, r)), m(c, r)), h)))
}
fn compare<const B: u32>(
    curve: Curve<B>,
    roots: &[u64],
    make: impl Fn(Backend) -> Result<FactorBase<B>>,
) {
    let expected_points: Vec<_> = roots
        .iter()
        .filter_map(|&x| curve.lift_x(x).unwrap())
        .collect();
    if expected_points.is_empty() {
        eprintln!(
            "empty target lift: B={B}, raw_roots={}, first_root={}, error={:?}",
            roots.len(),
            roots[0],
            make(Backend::Scalar).unwrap_err()
        );
        assert_eq!(
            FactorBase::without_maps(curve, roots).unwrap_err(),
            Error::Invalid("factor base contains no rational target points")
        );
        for backend in [
            Backend::Scalar,
            Backend::Auto,
            Backend::Avx2,
            Backend::Avx512,
        ] {
            assert_eq!(
                make(backend).unwrap_err(),
                Error::Invalid("factor base contains no rational target points")
            );
        }
        return;
    }
    let direct = FactorBase::without_maps(curve, roots).unwrap();
    let mut dw = direct.workspace();
    let mut targets: BTreeSet<_> = (0..32).collect();
    // Include D=0, signed relations, all vector/tile boundaries, and padding.
    for &a in direct.representatives() {
        targets.insert(a.x());
        for &b in direct.representatives().iter().take(3) {
            for b in [b, curve.negate(b).unwrap()] {
                if let Some(r) = curve.add(Some(a), Some(b)).unwrap() {
                    targets.insert(r.x());
                }
            }
        }
    }
    for backend in [
        Backend::Scalar,
        Backend::Auto,
        Backend::Avx2,
        Backend::Avx512,
    ] {
        let base = match make(backend) {
            Ok(b) => b,
            Err(Error::UnsupportedBackend) => continue,
            Err(e) => panic!("{e}"),
        };
        assert!(base.uses_circuit());
        assert!(!base.uses_auxiliary_maps());
        assert_eq!(base.raw_root_count(), roots.len());
        assert_eq!(base.representatives(), direct.representatives());
        let mut w = base.workspace();
        for &x in &targets {
            base.candidates(x, &mut w).unwrap();
            let expected: Vec<_> = base
                .representatives()
                .iter()
                .map(|v| explicit_product(curve, roots, v.x(), x))
                .collect();
            assert_eq!(
                w.values(),
                expected,
                "B={B} encoding={:?} backend={backend:?} x={x}",
                base.encoding()
            );
            let zeros: Vec<_> = expected
                .iter()
                .enumerate()
                .filter_map(|(i, &v)| (v == 0).then_some(i))
                .collect();
            assert_eq!(w.indices(), zeros);
            if let Some(target) = curve.lift_x(x).unwrap() {
                assert_eq!(
                    base.decompose(target, &mut w).unwrap(),
                    direct.decompose(target, &mut dw).unwrap()
                );
            }
        }
    }
}
#[test]
fn power_fibers_match_explicit_products_and_direct_rows_in_both_fields() {
    fn check<const B: u32>(curve: Curve<B>) {
        for degree in [9, 18, 126] {
            for coset in [1, 3] {
                let roots = power_roots(curve.modulus(), degree, coset);
                compare(curve, &roots, |backend| {
                    FactorBase::multiplicative(curve, degree, coset, backend)
                });
            }
        }
    }
    check(Curve::<31>::new(2, 14).unwrap());
    check(Curve::<61>::new(0, 3).unwrap());
}
#[test]
fn torus_fibers_match_explicit_products_and_direct_rows_in_both_fields() {
    let toy = Curve::<7>::new(2, 51).unwrap();
    for depth in [1, 2, 5] {
        let base = FactorBase::torus(toy, depth, Some(3), Backend::Scalar).unwrap();
        let roots = torus_roots(&base);
        compare(toy, &roots, |backend| {
            FactorBase::torus(toy, depth, Some(3), backend)
        });
    }
    fn check<const B: u32>(curve: Curve<B>) {
        for depth in [3, 5, 7] {
            let base = FactorBase::torus(curve, depth, None, Backend::Scalar).unwrap();
            let roots = torus_roots(&base);
            let FactorBaseEncoding::Torus { trace, .. } = base.encoding() else {
                unreachable!()
            };
            compare(curve, &roots, |backend| {
                FactorBase::torus(curve, depth, Some(trace), backend)
            });
        }
    }
    check(Curve::<31>::new(2, 14).unwrap());
    check(Curve::<61>::new(0, 3).unwrap());
}
#[test]
fn field_circuits_and_direct_controls_have_identical_full_recoveries() {
    let curve = Curve::<7>::new(2, 51).unwrap();
    let g = curve.point(3, 46).unwrap();
    for base in [
        FactorBase::multiplicative(curve, 18, 1, Backend::Auto).unwrap(),
        FactorBase::torus(curve, 3, None, Backend::Auto).unwrap(),
    ] {
        let roots = match base.encoding() {
            FactorBaseEncoding::Multiplicative { degree, coset } => power_roots(127, degree, coset),
            FactorBaseEncoding::Torus { .. } => torus_roots(&base),
            _ => unreachable!(),
        };
        let direct = FactorBase::without_maps(curve, &roots).unwrap();
        for scalar in [1, 17, 37, 108] {
            let target = curve.mul(Some(g), scalar).unwrap().unwrap();
            let config = Config {
                seed: 43,
                max_queries: 10000,
                ..Config::default()
            };
            let SolveOutcome::Solved {
                certificate: a,
                stats: sa,
            } = solve(&base, 109, g, target, &config).unwrap()
            else {
                panic!("circuit exhausted")
            };
            let SolveOutcome::Solved {
                certificate: b,
                stats: sb,
            } = solve(&direct, 109, g, target, &config).unwrap()
            else {
                panic!("direct exhausted")
            };
            assert_eq!(a, b);
            assert_eq!(a.scalar, scalar);
            assert_eq!(sa.queries, sb.queries);
            assert_ne!(sa.circuit_queries, 0);
            assert_eq!(sb.circuit_queries, 0);
            verify_certificate(&base, &a).unwrap();
            verify_certificate(&direct, &b).unwrap();
        }
    }
}
#[test]
fn malformed_field_fibers_are_rejected() {
    let curve = Curve::<31>::new(2, 14).unwrap();
    let p = curve.modulus();
    for degree in [0, 1, 4, 5, 25, 1 << 21] {
        assert!(FactorBase::multiplicative(curve, degree, 1, Backend::Scalar).is_err());
    }
    for coset in [0, p, p + 1] {
        assert!(FactorBase::multiplicative(curve, 18, coset, Backend::Scalar).is_err());
    }
    for depth in [0, 21, 255] {
        assert!(FactorBase::torus(curve, depth, None, Backend::Scalar).is_err());
    }
    for trace in [2, p - 2, p] {
        assert!(FactorBase::torus(curve, 3, Some(trace), Backend::Scalar).is_err());
    }
    assert!(FactorBase::torus(Curve::<7>::new(2, 51).unwrap(), 6, None, Backend::Scalar).is_err());
}
