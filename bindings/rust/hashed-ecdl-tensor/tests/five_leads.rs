//! Complete-solver controls for opt-in point-table leads, without timings.

use hashed_ecdl_tensor::arithmetic::Seeded;
use hashed_ecdl_tensor::curve::{Curve, Point};
use hashed_ecdl_tensor::optimized::{self, Options, WalkOptions};
use hashed_ecdl_tensor::prepared;
use hashed_ecdl_tensor::reduction::{self, Certificate, Config, FactorBase};
use hashed_ecdl_tensor::{BigUint, Error, Limits, Meter};

fn curve(meter: &mut Meter) -> Curve {
    Curve::new(
        17u8.into(),
        2u8.into(),
        2u8.into(),
        19u8.into(),
        Point::Affine {
            x: 5u8.into(),
            y: 1u8.into(),
        },
        meter,
    )
    .unwrap()
}

fn cofactor_curve(meter: &mut Meter) -> Curve {
    Curve::with_cofactor(
        5u8.into(),
        0u8.into(),
        1u8.into(),
        3u8.into(),
        2u8.into(),
        Point::Affine {
            x: 0u8.into(),
            y: 1u8.into(),
        },
        meter,
    )
    .unwrap()
}

fn config() -> Config {
    Config {
        hash_prime: Some(37u8.into()),
        threshold: Some(37u8.into()),
        slots: 2,
        columns: 64,
        trials: 8,
    }
}

fn arms() -> Vec<(&'static str, Options)> {
    let defaults = Options::default();
    vec![
        ("control", defaults.clone()),
        (
            "L1 provenance",
            Options {
                subgroup_provenance: true,
                ..defaults.clone()
            },
        ),
        (
            "L2 batching",
            Options {
                batch_chunk: 8,
                ..defaults.clone()
            },
        ),
        (
            "L3 graph",
            Options {
                relation_graph: true,
                ..defaults.clone()
            },
        ),
        (
            "L4 witness policy with graph foundation",
            Options {
                relation_graph: true,
                extra_scans: 4,
                ..defaults.clone()
            },
        ),
        (
            "L5 adding walk",
            Options {
                walk: Some(WalkOptions {
                    table_size: 16,
                    block_length: 16,
                }),
                ..defaults.clone()
            },
        ),
        (
            "all five",
            Options {
                subgroup_provenance: true,
                batch_chunk: 8,
                relation_graph: true,
                extra_scans: 4,
                walk: Some(WalkOptions {
                    table_size: 16,
                    block_length: 16,
                }),
                ..defaults
            },
        ),
    ]
}

fn run(
    curve: &Curve,
    target: &Point,
    config: &Config,
    options: &Options,
    seed: u64,
) -> (Certificate, u64, serde_json::Value) {
    let mut rng = Seeded(seed);
    let mut statistics = optimized::Statistics::default();
    let certificate = optimized::solve(
        curve,
        target,
        config,
        options,
        &mut rng,
        &mut statistics,
        &mut Meter::new(Limits::default()),
    )
    .unwrap_or_else(|error| panic!("seed {seed}, target {target:?}, options {options:?}: {error}"));
    (certificate, rng.0, statistics.diagnostics())
}

fn certificate_columns(curve: &Curve, certificate: &Certificate) -> usize {
    let mut meter = Meter::new(Limits::default());
    certificate
        .seeds
        .iter()
        .map(|seed| {
            FactorBase::new(
                curve,
                certificate.prime.clone(),
                certificate.threshold.clone(),
                seed.clone(),
                &mut meter,
            )
            .unwrap()
            .enumerate(curve, &mut Seeded(0x766572696679), &mut meter)
            .unwrap()
            .len()
        })
        .sum()
}

fn events(diagnostics: &serde_json::Value, path: &[&str]) -> u64 {
    let mut value = diagnostics;
    for key in path {
        value = &value[*key];
    }
    value
        .as_u64()
        .unwrap_or_else(|| panic!("missing event counter {path:?}: {diagnostics}"))
}

fn assert_routes(options: &Options, diagnostics: &serde_json::Value) {
    assert!(events(diagnostics, &["prepared_queries"]) > 0);
    let lookups = events(diagnostics, &["full_point_lookups"]);
    let computed = events(diagnostics, &["complements_computed"]);
    assert!(computed >= lookups);
    assert_eq!(
        events(diagnostics, &["trusted_queries"]) > 0,
        options.subgroup_provenance
    );
    if options.batch_chunk > 1 {
        assert!(events(diagnostics, &["batch", "batches"]) > 0);
        // Full bases produce early hits, so the unused suffix must be counted.
        assert!(events(diagnostics, &["unused_precomputed_complements"]) > 0);
    }
    assert_eq!(
        events(diagnostics, &["graph", "rows"]) > 0,
        options.relation_graph
    );
    if options.relation_graph {
        assert!(events(diagnostics, &["graph", "useful_dependencies"]) > 0);
    }
    if options.extra_scans > 0 {
        assert!(events(diagnostics, &["witness_policy", "extra_scan_calls"]) > 0);
        assert!(events(diagnostics, &["witness_policy", "graph_probes"]) > 0);
    }
    assert_eq!(
        events(diagnostics, &["walk", "preparations"]) > 0,
        options.walk.is_some()
    );
    if options.walk.is_some() {
        assert!(events(diagnostics, &["walk", "anchors"]) > 0);
        assert!(events(diagnostics, &["walk", "steps"]) > 0);
    }
}

#[test]
fn arithmetic_only_profiles_keep_whole_certificates_and_label_rng() {
    let mut setup = Meter::new(Limits::default());
    let curve = curve(&mut setup);
    let target = curve
        .mul(curve.generator(), &3u8.into(), &mut setup)
        .unwrap();
    for seed in [1, 42, 83] {
        let mut expected_rng = Seeded(seed);
        let expected = prepared::solve_joint(
            &curve,
            &target,
            &config(),
            &mut expected_rng,
            true,
            &mut prepared::Statistics::default(),
            &mut Meter::new(Limits::default()),
        )
        .unwrap();
        for subgroup_provenance in [false, true] {
            for batch_chunk in [1, 8, 32, 128] {
                let options = Options {
                    subgroup_provenance,
                    batch_chunk,
                    ..Options::default()
                };
                let (actual, final_rng, diagnostics) =
                    run(&curve, &target, &config(), &options, seed);
                assert_eq!(
                    actual, expected,
                    "seed {seed}, provenance {subgroup_provenance}, chunk {batch_chunk}"
                );
                assert_eq!(final_rng, expected_rng.0);
                assert!(diagnostics.is_object());
                assert_routes(&options, &diagnostics);
            }
        }
    }
}

#[test]
fn arithmetic_profiles_also_preserve_sparse_base_misses_and_trial_streams() {
    let mut setup = Meter::new(Limits::default());
    let curve = curve(&mut setup);
    let target = curve
        .mul(curve.generator(), &3u8.into(), &mut setup)
        .unwrap();
    let sparse = Config {
        threshold: Some(12u8.into()),
        trials: 32,
        ..config()
    };
    for seed in [1, 42, 83] {
        let mut expected_rng = Seeded(seed);
        let expected = prepared::solve_joint(
            &curve,
            &target,
            &sparse,
            &mut expected_rng,
            true,
            &mut prepared::Statistics::default(),
            &mut Meter::new(Limits::default()),
        )
        .unwrap();
        for subgroup_provenance in [false, true] {
            for batch_chunk in [8, 32, 128] {
                let options = Options {
                    subgroup_provenance,
                    batch_chunk,
                    ..Options::default()
                };
                let (actual, final_rng, _) = run(&curve, &target, &sparse, &options, seed);
                assert_eq!(actual, expected);
                assert_eq!(final_rng, expected_rng.0);
            }
        }
    }
}

#[test]
fn each_lead_and_the_combination_recover_and_replay_known_answers() {
    let mut setup = Meter::new(Limits::default());
    let curve = curve(&mut setup);
    for scalar in [1u8, 3, 7, 18] {
        let target = curve
            .mul(curve.generator(), &scalar.into(), &mut setup)
            .unwrap();
        for (name, options) in arms() {
            for seed in [1, 42, 83] {
                let (certificate, _, diagnostics) = run(&curve, &target, &config(), &options, seed);
                assert_eq!(
                    certificate.scalar,
                    BigUint::from(scalar),
                    "{name}, seed {seed}"
                );
                assert_eq!(certificate.version, 1, "{name}");
                assert!(diagnostics.is_object(), "{name}");
                assert_routes(&options, &diagnostics);
                reduction::verify(&curve, &target, &certificate, &mut setup).unwrap();
            }
        }
    }
}

#[test]
fn graph_certificates_keep_the_exact_v1_row_contract() {
    let mut setup = Meter::new(Limits::default());
    let curve = curve(&mut setup);
    let target = curve
        .mul(curve.generator(), &7u8.into(), &mut setup)
        .unwrap();
    for extra_scans in [0, 4] {
        let options = Options {
            relation_graph: true,
            extra_scans,
            ..Options::default()
        };
        let (certificate, _, _) = run(&curve, &target, &config(), &options, 42);
        assert_eq!(
            certificate.relations.len(),
            certificate_columns(&curve, &certificate) + 1
        );
        assert_eq!(certificate.dependency.len(), certificate.relations.len());
        reduction::verify(&curve, &target, &certificate, &mut setup).unwrap();

        // This keeps the actual dependency and all group equations valid,
        // changing only the number of rows. V1 must still reject it.
        let mut too_many = certificate.clone();
        too_many.relations.push(certificate.relations[0].clone());
        too_many.dependency.push(0u8.into());
        assert!(reduction::verify(&curve, &target, &too_many, &mut setup).is_err());

        if let Some(index) = certificate
            .dependency
            .iter()
            .position(|c| c == &BigUint::from(0u8))
        {
            let mut too_few = certificate.clone();
            too_few.relations.remove(index);
            too_few.dependency.remove(index);
            assert!(reduction::verify(&curve, &target, &too_few, &mut setup).is_err());
        }
    }
}

#[test]
fn composed_certificates_reject_corruption_without_trusting_diagnostics() {
    let mut setup = Meter::new(Limits::default());
    let curve = curve(&mut setup);
    let target = curve
        .mul(curve.generator(), &3u8.into(), &mut setup)
        .unwrap();
    let options = arms().pop().unwrap().1;
    let (certificate, _, _) = run(&curve, &target, &config(), &options, 83);
    let mut forged = certificate.clone();
    forged.relations[0].points[0] = Point::Infinity;
    assert!(reduction::verify(&curve, &target, &forged, &mut setup).is_err());
    let mut forged = certificate.clone();
    forged.scalar = (&forged.scalar + 1u8) % curve.order();
    assert!(reduction::verify(&curve, &target, &forged, &mut setup).is_err());
    let mut forged = certificate.clone();
    forged.dependency.fill(0u8.into());
    assert!(reduction::verify(&curve, &target, &forged, &mut setup).is_err());
    let mut forged = certificate.clone();
    forged.relations[0].u += curve.order();
    assert!(reduction::verify(&curve, &target, &forged, &mut setup).is_err());
    let mut forged = certificate;
    forged.version = 999;
    assert!(reduction::verify(&curve, &target, &forged, &mut setup).is_err());
}

#[test]
fn every_arm_keeps_external_subgroup_and_resource_errors() {
    let mut setup = Meter::new(Limits::default());
    let curve = cofactor_curve(&mut setup);
    let cofactor_config = Config {
        hash_prime: Some(11u8.into()),
        threshold: Some(11u8.into()),
        ..config()
    };
    for (name, options) in arms() {
        for invalid in [
            Point::Affine {
                x: 4u8.into(),
                y: 0u8.into(),
            },
            Point::Affine {
                x: 5u8.into(),
                y: 1u8.into(),
            },
            Point::Affine {
                x: 1u8.into(),
                y: 1u8.into(),
            },
        ] {
            let result = optimized::solve(
                &curve,
                &invalid,
                &cofactor_config,
                &options,
                &mut Seeded(1),
                &mut optimized::Statistics::default(),
                &mut setup,
            );
            assert!(matches!(result, Err(Error::Invalid(_))), "{name}");
        }
        for limits in [
            Limits {
                steps: 0,
                ..Limits::default()
            },
            Limits {
                vector: 1,
                ..Limits::default()
            },
            Limits {
                bits: 1,
                ..Limits::default()
            },
        ] {
            let result = optimized::solve(
                &curve,
                curve.generator(),
                &cofactor_config,
                &options,
                &mut Seeded(1),
                &mut optimized::Statistics::default(),
                &mut Meter::new(limits),
            );
            assert!(matches!(result, Err(Error::Limit(_))), "{name}: {result:?}");
        }
    }
}

#[test]
fn identity_keeps_the_existing_zero_certificate_in_every_arm() {
    let mut setup = Meter::new(Limits::default());
    let curve = curve(&mut setup);
    for (name, options) in arms() {
        let (certificate, _, _) = run(&curve, &Point::Infinity, &config(), &options, 1);
        assert_eq!(certificate.version, 1, "{name}");
        assert_eq!(certificate.scalar, BigUint::from(0u8), "{name}");
        assert!(certificate.seeds.is_empty() && certificate.relations.is_empty());
        reduction::verify(&curve, &Point::Infinity, &certificate, &mut setup).unwrap();
    }
}

#[test]
fn optimized_option_json_is_strict_and_defaults_preserve_the_control() {
    let defaults: Options = serde_json::from_str("{}").unwrap();
    assert!(!defaults.subgroup_provenance);
    assert_eq!(defaults.batch_chunk, 1);
    assert!(!defaults.relation_graph);
    assert_eq!(defaults.extra_scans, 0);
    assert!(defaults.walk.is_none());
    assert!(defaults.joint_targets);
    for text in [
        r#"{"unknown":true}"#,
        r#"{"batch_chunk":1,"batch_chunk":8}"#,
        r#"{"subgroup_provenance":true,"subgroup_provenance":false}"#,
        r#"{"batch_chunk":-1}"#,
        r#"{"walk":{"table_size":16,"block_length":16,"unknown":1}}"#,
        r#"{"walk":{"table_size":16,"table_size":32,"block_length":16}}"#,
    ] {
        assert!(serde_json::from_str::<Options>(text).is_err(), "{text}");
    }
}

#[test]
fn zero_batch_and_walk_dimensions_are_invalid_instead_of_silent_fallbacks() {
    let mut meter = Meter::new(Limits::default());
    let curve = curve(&mut meter);
    let bad = [
        Options {
            batch_chunk: 0,
            ..Options::default()
        },
        Options {
            walk: Some(WalkOptions {
                table_size: 0,
                block_length: 16,
            }),
            ..Options::default()
        },
        Options {
            walk: Some(WalkOptions {
                table_size: 16,
                block_length: 0,
            }),
            ..Options::default()
        },
        Options {
            extra_scans: 4,
            ..Options::default()
        },
    ];
    for options in bad {
        let result = optimized::solve(
            &curve,
            curve.generator(),
            &config(),
            &options,
            &mut Seeded(1),
            &mut optimized::Statistics::default(),
            &mut meter,
        );
        assert!(matches!(result, Err(Error::Invalid(_))), "{result:?}");
    }
}
