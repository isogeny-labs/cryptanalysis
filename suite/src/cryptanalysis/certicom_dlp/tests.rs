use super::*;
use crate::binary_ecc::IrreduciblePoly;

fn options() -> SolverOptions {
    SolverOptions {
        max_iterations: 2048,
        max_restarts: 16,
        max_table_entries: 128,
        factor_base_size: 3,
        max_base_candidates: 64,
        ..SolverOptions::default()
    }
}

// Constructed full-width known-answer preparation. The solver receives only
// public points and query scalars k_i+k_j, not the individual k_i or target log.
// This checks the complete IC data path; it is not a natural-yield experiment.
pub(super) fn index_fixture(group: &ChallengeGroup) -> (IndexInput, BigUint) {
    let k0 = (BigUint::one() << 100u32) + BigUint::from(17u32);
    let k1 = (BigUint::one() << 107u32) + BigUint::from(53u32);
    let k2 = (BigUint::one() << 113u32) + BigUint::from(91u32);
    let input = IndexInput {
        factor_base: [&k0, &k1, &k2]
            .iter()
            .map(|k| group.target_from_scalar(k))
            .collect(),
        relation_queries: vec![
            (&k0 + &k1) % group.order(),
            (&k1 + &k2) % group.order(),
            (&k2 + &k0) % group.order(),
        ],
        descent_shifts: vec![BigUint::zero()],
    };
    (input, (&k0 * BigUint::from(2u32)) % group.order())
}

#[test]
fn bsgs_recovers_full_width_scalars_on_both_exact_challenges() {
    for name in ["ECC2-130", "ECCp-130"] {
        let group = ChallengeGroup::by_name(name).unwrap();
        let lo = BigUint::one() << 100u32;
        let secret = &lo + BigUint::from(42u32);
        let target = group.target_from_scalar(&secret);
        let opts = SolverOptions {
            max_table_entries: 8,
            max_iterations: 32,
            ..options()
        };
        let report = bsgs(&group, &target, &lo, &BigUint::from(256u32), &opts).unwrap();
        assert!(report.verified, "{name}: {report:?}");
        assert_eq!(report.scalar_value, Some(secret));
        assert_eq!(report.method, "bsgs");
        assert_eq!(report.table_entries, 8);
        assert_eq!(group.order().bits(), 131);
    }
}

#[test]
fn rho_recovers_a_full_width_known_answer_by_a_real_collision() {
    // Q=-G is a deliberately special known-answer input that can have short
    // rho cycles even in the exact large subgroup. No small-scalar lookup or
    // special-case Q=-G solver is used. Uniform-target recovery is not claimed.
    for name in ["ECC2-130", "ECCp-130"] {
        let group = ChallengeGroup::by_name(name).unwrap();
        let secret = group.order() - BigUint::one();
        let target = group.target_from_scalar(&secret);
        let report = rho(&group, &target, &options()).unwrap();
        assert!(report.verified, "{name}: {report:?}");
        assert_eq!(report.scalar_value, Some(secret));
        assert_eq!(report.method, "rho");
        assert!(report.iterations.unwrap() > 0);
        assert_eq!(report.table_entries, 0);
    }
}

#[test]
fn index_calculus_collects_solves_and_descends_on_the_exact_131_bit_curves() {
    for name in ["ECC2-130", "ECCp-130"] {
        let group = ChallengeGroup::by_name(name).unwrap();
        let (input, secret) = index_fixture(&group);
        let target = group.target_from_scalar(&secret);
        let report = index_calculus(&group, &target, &options(), Some(&input)).unwrap();
        assert!(report.verified, "{name}: {report:?}");
        assert_eq!(report.scalar_value, Some(secret));
        assert_eq!(report.method, "index-calculus");
        let ic = report.index_calculus.unwrap();
        assert_eq!(ic.factor_base_size, 3);
        assert_eq!(ic.rank, 3);
        assert_eq!(ic.verified_relations, 3);
        assert_eq!(ic.relation_queries, 3);
        assert_eq!(ic.descent_queries, 1);
        assert!(ic.factor_base_logs_verified);
    }
}

#[test]
fn all_three_methods_stop_at_their_limits_on_the_published_targets() {
    for name in ["ECC2-131", "ECCp-131"] {
        let group = ChallengeGroup::by_name(name).unwrap();
        let target = group.published_target();
        let opts = SolverOptions {
            max_iterations: 4,
            max_restarts: 0,
            ..options()
        };
        let reports = [
            rho(&group, &target, &opts).unwrap(),
            bsgs(&group, &target, &BigUint::zero(), group.order(), &opts).unwrap(),
            index_calculus(&group, &target, &opts, None).unwrap(),
        ];
        for (report, method) in reports.iter().zip(["rho", "bsgs", "index-calculus"]) {
            assert_eq!(report.method, method);
            assert!(report.exact_curve);
            assert_eq!(report.status, "budget_exhausted", "{name}: {report:?}");
            assert!(!report.verified);
            assert!(report.scalar.is_none());
        }
        let ic = reports[2].index_calculus.as_ref().unwrap();
        assert_eq!(ic.factor_base_size, 3);
        assert_eq!(ic.factor_base_source, "cofactor-cleared-low-x");
        assert_eq!(ic.relation_queries, 4);
    }
}

#[test]
fn rank_deficient_or_invalid_ic_input_never_becomes_a_solution() {
    for name in ["ECC2-131", "ECCp-131"] {
        let group = ChallengeGroup::by_name(name).unwrap();
        let (mut input, secret) = index_fixture(&group);
        let target = group.target_from_scalar(&secret);
        input.relation_queries.truncate(2);
        let report = index_calculus(&group, &target, &options(), Some(&input)).unwrap();
        assert_eq!(report.status, "budget_exhausted");
        assert_eq!(report.index_calculus.as_ref().unwrap().rank, 2);
        assert!(
            !report
                .index_calculus
                .as_ref()
                .unwrap()
                .factor_base_logs_verified
        );
        assert!(!report.verified);
        input.factor_base[1] = group.neg(&input.factor_base[0]);
        assert!(index_calculus(&group, &target, &options(), Some(&input)).is_err());
        let wrong_field = ChallengeGroup::by_name(if name.starts_with("ECC2") {
            "ECCp-131"
        } else {
            "ECC2-131"
        })
        .unwrap()
        .generator();
        assert!(rho(&group, &wrong_field, &options()).is_err());
    }
}

#[test]
fn bsgs_rejects_bad_bounds_and_reports_an_exhausted_interval() {
    let group = ChallengeGroup::by_name("ECCp-131").unwrap();
    let target = group.target_from_scalar(&BigUint::from(42u32));
    assert!(bsgs(
        &group,
        &target,
        &BigUint::zero(),
        &BigUint::zero(),
        &options()
    )
    .is_err());
    assert!(bsgs(&group, &target, group.order(), &BigUint::one(), &options()).is_err());
    let opts = SolverOptions {
        max_table_entries: 2,
        max_iterations: 4,
        ..options()
    };
    let report = bsgs(
        &group,
        &target,
        &BigUint::zero(),
        &BigUint::from(8u32),
        &opts,
    )
    .unwrap();
    assert_eq!(report.status, "interval_exhausted");
    assert!(!report.verified);
    assert!(group
        .point(group.order(), &(BigUint::one() << 140u32))
        .is_err());
}

#[test]
fn ic_rejects_oversized_matrices_and_counts_dependent_queries_separately() {
    let group = ChallengeGroup::by_name("ECC2-131").unwrap();
    let (mut input, secret) = index_fixture(&group);
    let target = group.target_from_scalar(&secret);
    let too_small = SolverOptions {
        max_matrix_entries: 8,
        ..options()
    };
    assert!(index_calculus(&group, &target, &too_small, Some(&input)).is_err());
    let first = input.relation_queries[0].clone();
    input.relation_queries.insert(1, first);
    input.relation_queries.insert(0, BigUint::zero());
    let report = index_calculus(&group, &target, &options(), Some(&input)).unwrap();
    assert!(report.verified);
    let stages = report.index_calculus.unwrap();
    assert_eq!(stages.rank, 3);
    assert_eq!(stages.verified_relations, 4);
    assert_eq!(stages.dependent_relations, 1);
    assert_eq!(stages.trivial_relations, 1);
}

#[test]
fn rho_also_solves_ordinary_small_prime_and_binary_groups() {
    let prime = CurveParams {
        name: "rho-prime-unit",
        p: BigUint::from(211u32),
        a: BigUint::zero(),
        b: BigUint::from(2u32),
        gx: BigUint::from(4u32),
        gy: BigUint::from(53u32),
        n: BigUint::from(199u32),
        h: 1,
    };
    let prime = ChallengeGroup {
        name: "rho-prime-unit",
        published: ChallengePoint::Prime(prime.generator()),
        curve: Curve::Prime(prime),
    };
    let m = 5;
    let mut binary = BinaryCurve {
        m,
        irreducible: IrreduciblePoly {
            degree: m,
            low_terms: vec![0, 2],
        },
        a: F2mElement::zero(m),
        b: F2mElement::one(m),
        generator: BinaryPoint::Infinity,
        order: BigUint::from(11u32),
        cofactor: BigUint::from(4u32),
    };
    'find: for x in 1..32u32 {
        for y in 0..32u32 {
            let p = BinaryPoint::Affine {
                x: F2mElement::from_biguint(&BigUint::from(x), m),
                y: F2mElement::from_biguint(&BigUint::from(y), m),
            };
            if binary.is_on_curve(&p) {
                let p = binary::scalar_mul(&binary, &p, &binary.cofactor);
                if p != BinaryPoint::Infinity {
                    binary.generator = p;
                    break 'find;
                }
            }
        }
    }
    let binary = ChallengeGroup {
        name: "rho-binary-unit",
        published: ChallengePoint::Binary(binary.generator.clone()),
        curve: Curve::Binary(Box::new(binary)),
    };
    for (group, k) in [(prime, 37u32), (binary, 7u32)] {
        let secret = BigUint::from(k);
        let target = group.target_from_scalar(&secret);
        let report = rho(&group, &target, &options()).unwrap();
        assert_eq!(report.scalar_value, Some(secret), "{report:?}");
        assert!(report.verified);
    }
}
