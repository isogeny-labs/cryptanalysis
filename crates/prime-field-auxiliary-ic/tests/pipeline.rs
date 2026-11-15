mod common;
use common::*;
use prime_field_auxiliary_ic::*;
use std::{collections::BTreeSet, time::Duration};

fn toy(backend: Backend) -> Result<FactorBase<7>> {
    FactorBase::new(
        Curve::new(2, 51)?,
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
    )
}

fn product_reference<const B: u32>(
    base: &FactorBase<B>,
    roots: &[u64],
    x: u64,
    target: u64,
) -> u64 {
    let p = base.curve().modulus();
    let (a, b) = base.curve().coefficients();
    let m = |x: u64, y: u64| (u128::from(x) * u128::from(y) % u128::from(p)) as u64;
    let add = |x: u64, y: u64| ((u128::from(x) + u128::from(y)) % u128::from(p)) as u64;
    let sub = |x: u64, y: u64| (x + p - y) % p;
    let dx = sub(x, target);
    let product = m(x, target);
    let sum = add(x, target);
    let alpha = m(dx, dx);
    let beta = sub(0, m(2, add(m(sum, add(product, a)), m(2, b))));
    let gamma = sub(m(sub(product, a), sub(product, a)), m(m(4, b), sum));
    roots.iter().fold(1, |acc, &v| {
        m(acc, add(add(m(alpha, m(v, v)), m(beta, v)), gamma))
    })
}

fn exact_circuit<const B: u32>(
    curve: Curve<B>,
    maps: &[AuxiliaryMap],
    terminal: u64,
    roots: &[u64],
) {
    let scalar = FactorBase::new(curve, maps.to_vec(), terminal, roots, Backend::Scalar).unwrap();
    let direct = FactorBase::without_maps(curve, roots).unwrap();
    let mut direct_workspace = direct.workspace();
    let mut targets = BTreeSet::new();
    for x in 0..25 {
        if let Some(p) = curve.lift_x(x).unwrap() {
            targets.insert(p.coordinates());
        }
    }
    for &p in scalar.representatives() {
        for &q in scalar.representatives() {
            for q in [q, curve.negate(q).unwrap()] {
                if let Some(r) = curve.add(Some(p), Some(q)).unwrap() {
                    targets.insert(r.coordinates());
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
        let base = match FactorBase::new(curve, maps.to_vec(), terminal, roots, backend) {
            Ok(base) => base,
            Err(Error::UnsupportedBackend) => continue,
            Err(error) => panic!("{error}"),
        };
        let mut workspace = base.workspace();
        for &(x, y) in &targets {
            let target = curve.point(x, y).unwrap();
            base.candidates(x, &mut workspace).unwrap();
            let expected: Vec<_> = base
                .representatives()
                .iter()
                .map(|p| product_reference(&base, roots, p.x(), x))
                .collect();
            assert_eq!(workspace.values(), expected);
            let expected_indices: Vec<_> = expected
                .iter()
                .enumerate()
                .filter_map(|(i, &v)| (v == 0).then_some(i))
                .collect();
            assert_eq!(workspace.indices(), expected_indices);
            let decomposition = base.decompose(target, &mut workspace).unwrap();
            assert_eq!(
                decomposition,
                direct.decompose(target, &mut direct_workspace).unwrap()
            );
            if let Some(row) = decomposition {
                assert!(base.check_relation(Some(target), row));
            }
        }
    }
}

#[test]
fn direct_control_has_identical_rows_and_recovery_on_identical_walks() {
    let base = toy(Backend::Auto).unwrap();
    let curve = base.curve();
    let direct = FactorBase::without_maps(curve, &[3, 111, 78, 67, 85, 119, 57, 91]).unwrap();
    let generator = curve.point(3, 46).unwrap();
    let target = curve.mul(Some(generator), 37).unwrap().unwrap();
    let mut left = base.workspace();
    let mut right = direct.workspace();
    for x in 0..127 {
        if let Some(point) = curve.lift_x(x).unwrap() {
            assert_eq!(
                base.decompose(point, &mut left).unwrap(),
                direct.decompose(point, &mut right).unwrap()
            );
        }
    }
    let config = Config {
        seed: 43,
        max_queries: 10_000,
        ..Config::default()
    };
    let SolveOutcome::Solved {
        certificate: a,
        stats: a_stats,
    } = solve(&base, 109, generator, target, &config).unwrap()
    else {
        panic!("auxiliary search exhausted");
    };
    let SolveOutcome::Solved {
        certificate: b,
        stats: b_stats,
    } = solve(&direct, 109, generator, target, &config).unwrap()
    else {
        panic!("direct search exhausted");
    };
    assert_eq!(a, b);
    assert_eq!(a_stats.queries, b_stats.queries);
    assert_eq!(a_stats.duplicate_rows, b_stats.duplicate_rows);
    assert_eq!(b_stats.circuit_queries, 0);
    // Independent bases do not need a complete map fiber or a power-of-two size.
    assert!(FactorBase::without_maps(curve, &[3, 6, 7]).is_ok());
    assert!(FactorBase::without_maps(curve, &[3, 3]).is_err());
}

#[test]
fn scalar_and_simd_are_exact_products_in_both_fields() {
    exact_circuit(
        Curve::<31>::new(2, 14).unwrap(),
        &MAPS31,
        TERMINAL31,
        &ROOTS31,
    );
    exact_circuit(
        Curve::<61>::new(0, 3).unwrap(),
        &MAPS61,
        TERMINAL61,
        &ROOTS61,
    );
}

#[test]
fn nonzero_first_pole_and_root_order_are_supported() {
    let curve = Curve::<31>::new(2, 14).unwrap();
    let mut maps = MAPS31;
    maps[0].r = 17;
    let roots: Vec<_> = ROOTS31
        .iter()
        .rev()
        .map(|x| (x + 17) % curve.modulus())
        .collect();
    exact_circuit(curve, &maps, TERMINAL31, &roots);
}

#[test]
fn complete_small_solves_use_distinct_nontrivial_rows() {
    let curve = Curve::<7>::new(2, 51).unwrap();
    let generator = curve.point(3, 46).unwrap();
    for scalar in [1, 17, 37, 108] {
        let target = curve.mul(Some(generator), scalar).unwrap().unwrap();
        for lanes in [1, 4, 64] {
            for backend in [Backend::Scalar, Backend::Auto] {
                let base = toy(backend).unwrap();
                let config = Config {
                    seed: scalar,
                    walk_lanes: lanes,
                    max_queries: 10_000,
                    ..Config::default()
                };
                let outcome = solve(&base, 109, generator, target, &config).unwrap();
                let SolveOutcome::Solved { certificate, stats } = outcome else {
                    panic!("{outcome:?}");
                };
                assert_eq!(certificate.scalar, scalar);
                assert!(certificate.weights.iter().filter(|&&w| w != 0).count() >= 3);
                assert!(stats.generated_targets >= stats.queries);
                assert!(stats.generated_targets - stats.queries < lanes as u64);
                verify_certificate(&base, &certificate).unwrap();
            }
        }
    }
}

#[test]
fn original_31_bit_rows_recover_without_search_or_private_input() {
    let base = FactorBase::<31>::new(
        Curve::new(2, 14).unwrap(),
        MAPS31.to_vec(),
        TERMINAL31,
        &ROOTS31,
        Backend::Scalar,
    )
    .unwrap();
    let curve = base.curve();
    let generator = curve.point(1, 814455902).unwrap();
    let target = curve.point(988441464, 1643383878).unwrap();
    let solver = PreparedSolver::new(&base, 2147505293, generator).unwrap();
    let certificate = solver
        .recover_from_relations(target, &RELATIONS31, 10000)
        .unwrap()
        .unwrap();
    assert_eq!(certificate.scalar, 123456789);
    verify_certificate(&base, &certificate).unwrap();
    let mut forged = certificate.clone();
    forged.scalar += 1;
    assert!(verify_certificate(&base, &forged).is_err());
    let mut forged = certificate.clone();
    forged.weights[0] = (forged.weights[0] + 1) % forged.order;
    assert!(verify_certificate(&base, &forged).is_err());
    let mut forged = certificate;
    forged.relations[0].a = (forged.relations[0].a + 1) % forged.order;
    assert!(verify_certificate(&base, &forged).is_err());
}

#[test]
fn resource_boundaries_are_explicit_and_do_not_report_recovery() {
    let base = toy(Backend::Scalar).unwrap();
    let curve = base.curve();
    let generator = curve.point(3, 46).unwrap();
    let target = curve.point(6, 122).unwrap();
    let config = Config {
        max_queries: 1,
        walk_lanes: 4,
        ..Config::default()
    };
    let outcome = solve(&base, 109, generator, target, &config).unwrap();
    assert!(matches!(
        outcome,
        SolveOutcome::Exhausted {
            reason: StopReason::QueryBudget,
            ..
        }
    ));
    assert_eq!(outcome.stats().queries, 1);
    assert_eq!(outcome.stats().generated_targets, 4);
    let config = Config {
        max_duration: Some(Duration::ZERO),
        ..Config::default()
    };
    assert!(matches!(
        solve(&base, 109, generator, target, &config).unwrap(),
        SolveOutcome::Exhausted {
            reason: StopReason::TimeBudget,
            ..
        }
    ));
    let config = Config {
        max_proof_nodes: 1,
        max_queries: 1000,
        ..Config::default()
    };
    let outcome = solve(&base, 109, generator, target, &config).unwrap();
    assert!(matches!(
        outcome,
        SolveOutcome::Exhausted {
            reason: StopReason::ProofBudget,
            ..
        }
    ));
    assert_eq!(outcome.stats().proof_nodes, 1);
    let config = Config {
        max_relations: 1,
        max_queries: 1000,
        ..Config::default()
    };
    assert!(matches!(
        solve(&base, 109, generator, target, &config).unwrap(),
        SolveOutcome::Exhausted {
            reason: StopReason::RelationBudget,
            ..
        }
    ));
}

#[test]
fn malformed_fibers_and_subgroups_are_rejected() {
    let curve = Curve::<31>::new(2, 14).unwrap();
    assert!(Curve::<8>::new(2, 14).is_err());
    assert!(Curve::<31>::new(0, 0).is_err());
    assert!(FactorBase::new(
        curve,
        MAPS31.to_vec(),
        TERMINAL31,
        &ROOTS31[..31],
        Backend::Scalar
    )
    .is_err());
    let mut roots = ROOTS31;
    roots[1] = roots[0];
    assert!(FactorBase::new(curve, MAPS31.to_vec(), TERMINAL31, &roots, Backend::Scalar).is_err());
    roots = ROOTS31;
    roots[0] += 1;
    assert!(FactorBase::new(curve, MAPS31.to_vec(), TERMINAL31, &roots, Backend::Scalar).is_err());
    let mut maps = MAPS31;
    maps[0].residue = 0;
    assert!(FactorBase::new(curve, maps.to_vec(), TERMINAL31, &ROOTS31, Backend::Scalar).is_err());
    let base = toy(Backend::Scalar).unwrap();
    let generator = base.curve().point(3, 46).unwrap();
    assert!(PreparedSolver::new(&base, 108, generator).is_err());
    assert!(PreparedSolver::new(&base, 107, generator).is_err());
}
