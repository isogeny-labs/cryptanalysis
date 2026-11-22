//! Exhaustive brute-force and end-to-end checks for m=2, 3, 4 resultant circuits.
use prime_field_auxiliary_ic::*;
use std::collections::BTreeSet;

#[allow(clippy::needless_range_loop)]
fn brute_force_noncancelling<const B: u32>(
    base: &FactorBase<B>,
    summands: u8,
) -> BTreeSet<(u64, u64)> {
    let curve = base.curve();
    let pts = base.representatives();
    let k = pts.len();
    let signed = |idx: usize, neg: bool| {
        if neg {
            curve.negate(pts[idx]).unwrap()
        } else {
            pts[idx]
        }
    };
    let mut reachable = BTreeSet::new();
    match summands {
        2 => {
            for i1 in 0..k {
                for neg1 in [false, true] {
                    if pts[i1].y() == 0 && neg1 {
                        continue;
                    }
                    let p1 = Some(signed(i1, neg1));
                    for i2 in i1..k {
                        for neg2 in [false, true] {
                            if pts[i2].y() == 0 && neg2 {
                                continue;
                            }
                            if i2 == i1 && neg2 != neg1 {
                                continue;
                            }
                            if let Some(sum) = curve.add(p1, Some(signed(i2, neg2))).unwrap() {
                                reachable.insert(sum.coordinates());
                            }
                        }
                    }
                }
            }
        }
        3 => {
            for i1 in 0..k {
                for neg1 in [false, true] {
                    if pts[i1].y() == 0 && neg1 {
                        continue;
                    }
                    let p1 = Some(signed(i1, neg1));
                    for i2 in i1..k {
                        for neg2 in [false, true] {
                            if pts[i2].y() == 0 && neg2 {
                                continue;
                            }
                            if i2 == i1 && neg2 != neg1 {
                                continue;
                            }
                            let p12 = curve.add(p1, Some(signed(i2, neg2))).unwrap();
                            for i3 in i2..k {
                                for neg3 in [false, true] {
                                    if pts[i3].y() == 0 && neg3 {
                                        continue;
                                    }
                                    if i3 == i2 && neg3 != neg2 {
                                        continue;
                                    }
                                    if let Some(sum) =
                                        curve.add(p12, Some(signed(i3, neg3))).unwrap()
                                    {
                                        reachable.insert(sum.coordinates());
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        4 => {
            for i1 in 0..k {
                for neg1 in [false, true] {
                    if pts[i1].y() == 0 && neg1 {
                        continue;
                    }
                    let p1 = Some(signed(i1, neg1));
                    for i2 in i1..k {
                        for neg2 in [false, true] {
                            if pts[i2].y() == 0 && neg2 {
                                continue;
                            }
                            if i2 == i1 && neg2 != neg1 {
                                continue;
                            }
                            let p12 = curve.add(p1, Some(signed(i2, neg2))).unwrap();
                            for i3 in i2..k {
                                for neg3 in [false, true] {
                                    if pts[i3].y() == 0 && neg3 {
                                        continue;
                                    }
                                    if i3 == i2 && neg3 != neg2 {
                                        continue;
                                    }
                                    let p123 = curve.add(p12, Some(signed(i3, neg3))).unwrap();
                                    for i4 in i3..k {
                                        for neg4 in [false, true] {
                                            if pts[i4].y() == 0 && neg4 {
                                                continue;
                                            }
                                            if i4 == i3 && neg4 != neg3 {
                                                continue;
                                            }
                                            if let Some(sum) =
                                                curve.add(p123, Some(signed(i4, neg4))).unwrap()
                                            {
                                                reachable.insert(sum.coordinates());
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        _ => unreachable!(),
    }
    reachable
}

fn check_exhaustive_curve<const B: u32>(
    base: &FactorBase<B>,
    direct: &FactorBase<B>,
    targets: &[Point],
) {
    for summands in [2u8, 3, 4] {
        let oracle = brute_force_noncancelling(base, summands);
        let mut w_circuit = base.workspace();
        let mut w_direct = direct.workspace();
        for &target in targets {
            let found_circuit = base
                .decompose_multi(summands, target, &mut w_circuit)
                .unwrap();
            let found_direct = direct
                .decompose_multi(summands, target, &mut w_direct)
                .unwrap();
            assert_eq!(
                found_circuit.is_some(),
                oracle.contains(&target.coordinates()),
                "B={B} summands={summands} target={target:?} encoding={:?}",
                base.encoding()
            );
            assert_eq!(
                found_circuit, found_direct,
                "circuit vs direct mismatch at B={B} summands={summands} target={target:?}"
            );
            if let Some(rel) = found_circuit {
                assert_eq!(rel.arity(), usize::from(summands));
                assert!(base.check_multi_relation(Some(target), rel));
                assert!(direct.check_multi_relation(Some(target), rel));
            }
        }
    }
}

fn all_affine_points<const B: u32>(curve: Curve<B>) -> Vec<Point> {
    let mut points = Vec::new();
    for x in 0..curve.modulus() {
        if let Some(p) = curve.lift_x(x).unwrap() {
            points.push(p);
            let neg = curve.negate(p).unwrap();
            if neg != p {
                points.push(neg);
            }
        }
    }
    points
}

#[test]
fn exhaustive_m3_and_m4_match_bruteforce_on_p127_and_2torsion_curves() {
    // 2-torsion curve y^2 = x^3 + x over F_31 (point (0, 0) has y = 0).
    let curve31 = Curve::<5>::new(1, 0).unwrap();
    let pts31 = all_affine_points(curve31);
    let torus31 = FactorBase::torus(curve31, 3, None, Backend::Auto).unwrap();
    let mut roots31: Vec<_> = torus31.representatives().iter().map(|p| p.x()).collect();
    if !roots31.contains(&0) {
        roots31.push(0);
    }
    let direct31 = FactorBase::without_maps(curve31, &roots31).unwrap();
    check_exhaustive_curve(&torus31, &torus31.direct_control().unwrap(), &pts31);
    check_exhaustive_curve(&direct31, &direct31, &pts31);

    // Auxiliary, multiplicative, and torus fibers over p = 127 across all curve points.
    let curve127 = Curve::<7>::new(2, 51).unwrap();
    let pts127 = all_affine_points(curve127);
    for backend in [
        Backend::Scalar,
        Backend::Auto,
        Backend::Avx2,
        Backend::Avx512,
    ] {
        let aux127 = match FactorBase::new(
            curve127,
            vec![
                AuxiliaryMap {
                    r: 0,
                    offset: 0,
                    residue: 1,
                },
                AuxiliaryMap {
                    r: 2,
                    offset: 6,
                    residue: 8,
                },
                AuxiliaryMap {
                    r: 70,
                    offset: 71,
                    residue: 70,
                },
            ],
            38,
            &[3, 111, 78, 67, 85, 119, 57, 91],
            backend,
        ) {
            Ok(b) => b,
            Err(Error::UnsupportedBackend) => continue,
            Err(e) => panic!("{e}"),
        };
        check_exhaustive_curve(&aux127, &aux127.direct_control().unwrap(), &pts127);
        let mul127 = FactorBase::multiplicative(curve127, 18, 1, backend).unwrap();
        check_exhaustive_curve(&mul127, &mul127.direct_control().unwrap(), &pts127);
        let tor127 = FactorBase::torus(curve127, 4, Some(3), backend).unwrap();
        check_exhaustive_curve(&tor127, &tor127.direct_control().unwrap(), &pts127);
    }
}

#[test]
fn p8191_m3_and_m4_match_bruteforce_and_recover_end_to_end() {
    // Find a certified prime-order curve over p = 8191 = 2^13 - 1.
    let (curve, pts, order) = {
        let mut chosen = None;
        for b in 1..100u64 {
            let Ok(c) = Curve::<13>::new(2, b) else {
                continue;
            };
            let all = all_affine_points(c);
            let ord = (all.len() + 1) as u64;
            let prime = ord > 3 && (2..100).all(|d| d * d > ord || ord % d != 0);
            if prime {
                chosen = Some((c, all, ord));
                break;
            }
        }
        chosen.expect("prime-order curve over F_8191")
    };
    let generator = pts[0];

    for backend in [
        Backend::Scalar,
        Backend::Auto,
        Backend::Avx2,
        Backend::Avx512,
    ] {
        // Multi-tile torus fiber (depth 5 -> 32 raw roots, spans >1 AVX2 tile) and multiplicative fiber (degree 18).
        let tor = match FactorBase::torus(curve, 5, None, backend) {
            Ok(b) => b,
            Err(Error::UnsupportedBackend) => continue,
            Err(e) => panic!("{e}"),
        };
        let tor_direct = tor.direct_control().unwrap();
        let sample_targets: Vec<_> = pts.iter().step_by(37).copied().collect();
        check_exhaustive_curve(&tor, &tor_direct, &sample_targets);

        let mul = FactorBase::multiplicative(curve, 18, 1, backend).unwrap();
        let mul_direct = mul.direct_control().unwrap();
        check_exhaustive_curve(&mul, &mul_direct, &sample_targets);

        // End-to-end m=2, 3, 4 solves on F_8191 with verify_multi_certificate and replay.
        let secret = 4321u64 % order;
        let target = curve.mul(Some(generator), secret).unwrap().unwrap();
        for summands in [2u8, 3, 4] {
            let config = Config {
                seed: 99,
                max_queries: 50_000,
                walk_lanes: 16,
                ..Config::default()
            };
            let MultiSolveOutcome::Solved {
                certificate: cert_c,
                stats: stats_c,
            } = solve_multi(&mul, summands, order, generator, target, &config).unwrap()
            else {
                panic!("m={summands} circuit solve exhausted on F_8191");
            };
            let MultiSolveOutcome::Solved {
                certificate: cert_d,
                stats: stats_d,
            } = solve_multi(&mul_direct, summands, order, generator, target, &config).unwrap()
            else {
                panic!("m={summands} direct solve exhausted on F_8191");
            };
            assert_eq!(cert_c.scalar, secret);
            assert_eq!(cert_c, cert_d);
            assert_eq!(stats_c.queries, stats_d.queries);
            verify_multi_certificate(&mul, &cert_c).unwrap();
            verify_multi_certificate(&mul_direct, &cert_d).unwrap();

            // Replay public relations without search.
            let prepared = PreparedSolver::new(&mul, order, generator).unwrap();
            let replayed = prepared
                .recover_from_multi_relations(summands, target, &cert_c.relations, 100_000)
                .unwrap()
                .unwrap();
            assert_eq!(replayed.scalar, secret);

            // Forgery controls.
            let mut bad_scalar = cert_c.clone();
            bad_scalar.scalar = (bad_scalar.scalar + 1) % order;
            assert!(verify_multi_certificate(&mul, &bad_scalar).is_err());

            let mut bad_weight = cert_c.clone();
            bad_weight.weights[0] = (bad_weight.weights[0] + 1) % order;
            assert!(verify_multi_certificate(&mul, &bad_weight).is_err());

            let mut bad_arity = cert_c.clone();
            bad_arity.summands = if summands == 4 { 3 } else { summands + 1 };
            assert!(verify_multi_certificate(&mul, &bad_arity).is_err());
        }
    }
}

#[test]
fn multi_summand_relation_yield_increases_with_arity_and_rejects_invalid_arities() {
    let curve = Curve::<13>::new(2, 1).unwrap_or_else(|_| Curve::<13>::new(2, 3).unwrap());
    let pts = all_affine_points(curve);
    let mut chosen = None;
    for b in 1..100u64 {
        if let Ok(c) = Curve::<13>::new(2, b) {
            let all = all_affine_points(c);
            let ord = (all.len() + 1) as u64;
            if ord > 3 && (2..100).all(|d| d * d > ord || ord % d != 0) {
                chosen = Some((c, all[0], all[17], ord));
                break;
            }
        }
    }
    let _ = pts;
    let (curve, g, target, order) = chosen.unwrap();
    let base = FactorBase::multiplicative(curve, 18, 1, Backend::Scalar).unwrap();
    let mut w = base.workspace();
    assert!(base.decompose_multi(1, target, &mut w).is_err());
    assert!(base.decompose_multi(5, target, &mut w).is_err());

    let prepared = PreparedSolver::new(&base, order, g).unwrap();
    let cfg = Config {
        seed: 77,
        max_queries: 256,
        walk_lanes: 8,
        max_relations: 10_000,
        ..Config::default()
    };
    let (_, s2, p2) = prepared
        .relation_yield_multi_profiled(2, target, &cfg)
        .unwrap();
    let (_, s3, p3) = prepared
        .relation_yield_multi_profiled(3, target, &cfg)
        .unwrap();
    let (_, s4, p4) = prepared
        .relation_yield_multi_profiled(4, target, &cfg)
        .unwrap();
    assert_eq!(p2.graph_recovery.as_nanos(), 0);
    assert_eq!(p3.graph_recovery.as_nanos(), 0);
    assert_eq!(p4.graph_recovery.as_nanos(), 0);
    assert!(s2.relations <= s3.relations);
    assert!(s3.relations <= s4.relations);
    assert!(s4.relations > s2.relations);
}
