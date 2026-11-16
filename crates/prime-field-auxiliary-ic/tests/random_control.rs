use prime_field_auxiliary_ic::*;
use std::collections::BTreeSet;

fn auxiliary() -> FactorBase<7> {
    FactorBase::new(
        Curve::new(2, 51).unwrap(),
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
        Backend::Scalar,
    )
    .unwrap()
}

fn check_sample<const B: u32>(curve: Curve<B>, order: u64, g: Point, cofactor: u64) {
    let (base, stats) = FactorBase::random_control(curve, order, g, 8, 701, 10_000).unwrap();
    let (again, repeated) = FactorBase::random_control(curve, order, g, 8, 701, 10_000).unwrap();
    assert_eq!(base.representatives(), again.representatives());
    assert_eq!(stats, repeated);
    assert_eq!(stats.cofactor, cofactor);
    assert_eq!(base.representatives().len(), 8);
    assert_eq!(base.affine_point_count(), 16);
    assert_eq!(base.encoding(), FactorBaseEncoding::Direct);
    assert!(!base.uses_circuit());
    assert_eq!(
        stats.draws,
        8 + stats.field_rejections
            + stats.non_lifts
            + stats.cleared_to_identity
            + stats.duplicate_columns
    );
    for &point in base.representatives() {
        assert_eq!(curve.mul(Some(point), order).unwrap(), None);
        assert!(point.y() <= curve.modulus() - point.y());
    }
}

#[test]
fn random_bases_match_size_and_subgroup_in_both_requested_fields() {
    let curve = Curve::<31>::new(2, 14).unwrap();
    check_sample(
        curve,
        2_147_505_293,
        curve.point(1, 814_455_902).unwrap(),
        1,
    );
    let curve = Curve::<61>::new(0, 3).unwrap();
    check_sample(
        curve,
        157_632_877_033,
        curve
            .point(78_862_349_111_012_854, 1_899_276_942_447_683_421)
            .unwrap(),
        14_627_932,
    );
}

#[test]
fn cofactor_clearing_matches_the_complete_small_subgroup() {
    let curve = Curve::<7>::new(2, 3).unwrap();
    let g = curve
        .mul(Some(curve.point(2, 53).unwrap()), 2)
        .unwrap()
        .unwrap();
    let (base, stats) = FactorBase::random_control(curve, 53, g, 26, 0, 10_000).unwrap();
    let expected: BTreeSet<_> = (1..53)
        .map(|k| curve.mul(Some(g), k).unwrap().unwrap().x())
        .collect();
    assert_eq!(
        base.representatives()
            .iter()
            .map(|p| p.x())
            .collect::<BTreeSet<_>>(),
        expected
    );
    assert_eq!(stats.cofactor, 2);
    assert!(stats.duplicate_columns > 0);
    PreparedSolver::new(&base, 53, g).unwrap();
}

#[test]
fn three_arms_use_equal_columns_and_recover_the_same_public_targets() {
    let special = auxiliary();
    let curve = special.curve();
    let g = curve.point(3, 46).unwrap();
    let direct = special.direct_control().unwrap();
    let (random, _) =
        FactorBase::random_control(curve, 109, g, special.representatives().len(), 701, 10_000)
            .unwrap();
    assert_ne!(special.representatives(), random.representatives());
    for base in [&special, &direct, &random] {
        assert_eq!(
            base.representatives().len(),
            special.representatives().len()
        );
        let mut all_sums = BTreeSet::new();
        for &p in base.representatives() {
            for &q in base.representatives() {
                for p in [p, curve.negate(p).unwrap()] {
                    for q in [q, curve.negate(q).unwrap()] {
                        if let Some(sum) = curve.add(Some(p), Some(q)).unwrap() {
                            all_sums.insert(sum.coordinates());
                        }
                    }
                }
            }
        }
        let mut workspace = base.workspace();
        // Identical complete public query panel, including unsuccessful queries.
        for k in 1..109 {
            let target = curve.mul(Some(g), k).unwrap().unwrap();
            assert_eq!(
                base.decompose(target, &mut workspace).unwrap().is_some(),
                all_sums.contains(&target.coordinates())
            );
        }
        for scalar in [17, 37, 83] {
            let target = curve.mul(Some(g), scalar).unwrap().unwrap();
            let config = Config {
                seed: 43,
                max_queries: 10_000,
                walk_lanes: 8,
                ..Config::default()
            };
            let SolveOutcome::Solved { certificate, stats } =
                solve(base, 109, g, target, &config).unwrap()
            else {
                panic!("comparison arm exhausted");
            };
            assert_eq!(certificate.scalar, scalar);
            assert!(stats.queries <= config.max_queries);
            verify_certificate(base, &certificate).unwrap();
        }
    }
}

#[test]
fn invalid_random_controls_and_exhausted_preparation_are_explicit() {
    let curve = Curve::<7>::new(2, 51).unwrap();
    let g = curve.point(3, 46).unwrap();
    for (order, columns) in [(109, 0), (109, 55), (108, 8), (107, 8)] {
        assert!(FactorBase::random_control(curve, order, g, columns, 0, 100).is_err());
    }
    assert!(matches!(
        FactorBase::random_control(curve, 109, g, 8, 0, 1),
        Err(Error::ResourceLimit(_))
    ));
    let curve = Curve::<7>::new(0, 1).unwrap();
    assert!(
        matches!(FactorBase::random_control(curve, 3, curve.point(0, 1).unwrap(), 1, 0, 100),
        Err(Error::Invalid(message)) if message.contains("Hasse-certified"))
    );
}

#[test]
fn relation_yield_runs_the_full_matched_prefix_without_early_recovery() {
    let special = auxiliary();
    let curve = special.curve();
    let g = curve.point(3, 46).unwrap();
    let target = curve.mul(Some(g), 37).unwrap().unwrap();
    let direct = special.direct_control().unwrap();
    let (random, _) =
        FactorBase::random_control(curve, 109, g, special.representatives().len(), 701, 10_000)
            .unwrap();
    let config = Config {
        seed: 43,
        max_queries: 513,
        walk_lanes: 8,
        max_relations: 10_000,
        ..Config::default()
    };
    let mut counts = Vec::new();
    for base in [&special, &direct, &random] {
        let prepared = PreparedSolver::new(base, 109, g).unwrap();
        let (reason, stats) = prepared.relation_yield(target, &config).unwrap();
        assert_eq!(reason, StopReason::QueryBudget);
        assert_eq!(stats.queries, config.max_queries);
        assert_eq!(stats.generated_targets, 520);
        assert!(stats.relations > 0);
        assert_eq!(stats.matrix_rank, 0);
        assert_eq!(stats.proof_nodes, 0);
        counts.push((stats.relations, stats.duplicate_rows));
        let capped = Config {
            max_relations: 1,
            ..config.clone()
        };
        assert_eq!(
            prepared.relation_yield(target, &capped).unwrap().0,
            StopReason::RelationBudget
        );
        let timed = Config {
            max_duration: Some(std::time::Duration::ZERO),
            ..config.clone()
        };
        let (reason, stats) = prepared.relation_yield(target, &timed).unwrap();
        assert_eq!(reason, StopReason::TimeBudget);
        assert_eq!(stats.queries, 0);
    }
    assert_eq!(counts[0], counts[1]);
}
