//! Known-answer correctness controls, not scientific measurements.
use hashed_ecdl_tensor::arithmetic::Seeded;
use hashed_ecdl_tensor::curve::{Curve, Point};
use hashed_ecdl_tensor::finite::{self, Options, Statistics};
use hashed_ecdl_tensor::partial::{self, Collector, NestedBase, Outcome};
use hashed_ecdl_tensor::reduction::{self, Config, FactorBase, HashSeed, Relation};
use hashed_ecdl_tensor::{BigUint, Error, Limits, Meter};

fn curve(meter: &mut Meter) -> Curve {
    Curve::new(
        5u8.into(),
        2u8.into(),
        1u8.into(),
        7u8.into(),
        Point::Affine {
            x: 0u8.into(),
            y: 1u8.into(),
        },
        meter,
    )
    .unwrap()
}
fn base(curve: &Curve, threshold: u8, alpha: u8, beta: u8, meter: &mut Meter) -> FactorBase {
    FactorBase::new(
        curve,
        11u8.into(),
        threshold.into(),
        HashSeed {
            alpha: alpha.into(),
            beta: beta.into(),
        },
        meter,
    )
    .unwrap()
}
fn brute(curve: &Curve, bases: &[FactorBase], target: &Point, meter: &mut Meter) -> bool {
    let a = bases[0].enumerate(curve, &mut Seeded(21), meter).unwrap();
    let b = bases[1].enumerate(curve, &mut Seeded(22), meter).unwrap();
    for x in &a {
        for y in &b {
            if curve.add(x, y, meter).unwrap() == *target {
                return true;
            }
        }
    }
    false
}

#[test]
fn selectors_match_exhaustive_sets_including_invalid_codes_and_unsat() {
    let mut meter = Meter::new(Limits::default());
    let curve = curve(&mut meter);
    for threshold in [1, 4, 11] {
        let bases = vec![
            base(&curve, threshold, 2, 1, &mut meter),
            base(&curve, threshold, 3, 4, &mut meter),
        ];
        for scalar in 0..7u8 {
            let target = curve
                .mul(curve.generator(), &scalar.into(), &mut meter)
                .unwrap();
            let expected = brute(&curve, &bases, &target, &mut meter);
            for derive_last in [false, true] {
                for smallest_first in [false, true] {
                    let mut stats = Statistics::default();
                    let answer = finite::prime_decompose(
                        &curve,
                        &bases,
                        &target,
                        &Options {
                            derive_last,
                            smallest_first,
                            cache_entries: 8,
                        },
                        &mut stats,
                        &mut meter,
                    )
                    .unwrap();
                    assert_eq!(answer.is_some(), expected);
                    if let Some(points) = answer {
                        assert!(bases[0].contains(&curve, &points[0], &mut meter).unwrap());
                        assert!(bases[1].contains(&curve, &points[1], &mut meter).unwrap());
                        assert_eq!(
                            curve.add(&points[0], &points[1], &mut meter).unwrap(),
                            target
                        );
                    }
                }
            }
        }
    }
}

#[test]
fn selector_cofactor_projection_has_unique_points_and_limits_are_unknown() {
    let mut meter = Meter::new(Limits::default());
    let curve = Curve::with_cofactor(
        5u8.into(),
        0u8.into(),
        1u8.into(),
        3u8.into(),
        2u8.into(),
        Point::Affine {
            x: 0u8.into(),
            y: 1u8.into(),
        },
        &mut meter,
    )
    .unwrap();
    let bases = vec![
        base(&curve, 11, 1, 0, &mut meter),
        base(&curve, 11, 1, 0, &mut meter),
    ];
    for scalar in 0..3u8 {
        let target = curve
            .mul(curve.generator(), &scalar.into(), &mut meter)
            .unwrap();
        let answer = finite::prime_decompose(
            &curve,
            &bases,
            &target,
            &Options::default(),
            &mut Statistics::default(),
            &mut meter,
        )
        .unwrap()
        .unwrap();
        assert!(answer
            .iter()
            .all(|p| curve.in_subgroup(p, &mut meter).unwrap()));
    }
    meter.limits.steps = meter.used;
    assert!(matches!(
        finite::prime_decompose(
            &curve,
            &bases,
            curve.generator(),
            &Options::default(),
            &mut Statistics::default(),
            &mut meter
        ),
        Err(Error::Limit(_))
    ));
}

#[test]
fn selector_oracle_runs_full_reduction_and_rejects_forged_witnesses() {
    let mut meter = Meter::new(Limits::default());
    let curve = curve(&mut meter);
    let target = curve
        .mul(curve.generator(), &3u8.into(), &mut meter)
        .unwrap();
    let config = Config {
        threshold: Some(11u8.into()),
        columns: 64,
        trials: 32,
        ..Config::default()
    };
    let mut stats = Statistics::default();
    let certificate = reduction::solve_with_oracle(
        &curve,
        &target,
        &config,
        &mut Seeded(42),
        |c, b, q, w| finite::prime_decompose(c, b, q, &Options::default(), &mut stats, w),
        &mut meter,
    )
    .unwrap();
    assert_eq!(certificate.scalar, BigUint::from(3u8));
    reduction::verify(&curve, &target, &certificate, &mut meter).unwrap();
    assert!(stats.derived_checks > 0);
    let error = reduction::solve_with_oracle(
        &curve,
        &target,
        &config,
        &mut Seeded(42),
        |_, _, _, _| Ok(Some(vec![Point::Infinity; 2])),
        &mut meter,
    )
    .unwrap_err();
    assert!(matches!(error, Error::Integrity(_)));
}

#[test]
fn external_oracle_replay_has_independent_group_work_and_matrix_accounting() {
    let mut setup = Meter::new(Limits::default());
    let curve = curve(&mut setup);
    let target = curve
        .mul(curve.generator(), &3u8.into(), &mut setup)
        .unwrap();
    let config = Config {
        threshold: Some(11u8.into()),
        columns: 64,
        trials: 32,
        ..Config::default()
    };
    let mut plain = Meter::new(Limits::default());
    let mut plain_rng = Seeded(42);
    let solve = |rng: &mut Seeded, work: &mut Meter| {
        reduction::solve_with_oracle(
            &curve,
            &target,
            &config,
            rng,
            |c, b, q, w| {
                finite::prime_decompose(c, b, q, &Options::default(), &mut Statistics::default(), w)
            },
            work,
        )
        .unwrap()
    };
    let expected = solve(&mut plain_rng, &mut plain);
    let session = hashed_ecdl_tensor::metrics::Session::start().unwrap();
    let mut observed = Meter::new(Limits::default());
    let mut observed_rng = Seeded(42);
    let actual = solve(&mut observed_rng, &mut observed);
    let snapshot = session.finish().unwrap();
    assert_eq!(actual.scalar, expected.scalar);
    assert_eq!(actual.relations, expected.relations);
    assert_eq!(actual.dependency, expected.dependency);
    assert_eq!(observed_rng.0, plain_rng.0);
    assert_eq!(observed.used, plain.used);
    let replay = &snapshot.phases["relation_check"];
    assert!(replay.scalar_mults > 0, "membership needs subgroup replay");
    assert!(
        replay.adds + replay.doubles > 0,
        "group-sum replay is charged"
    );
    let matrix = &snapshot.phases["matrix_build"];
    assert_eq!(matrix.adds + matrix.doubles + matrix.scalar_mults, 0);
    assert_eq!(
        snapshot.phases.values().map(|p| p.meter_steps).sum::<u64>(),
        observed.used
    );
    assert_eq!(
        snapshot.online_phases_ns.values().sum::<u64>(),
        snapshot.online_wall_ns.unwrap()
    );
    reduction::verify(&curve, &target, &actual, &mut setup).unwrap();
}

fn nested(curve: &Curve, slots: usize, meter: &mut Meter) -> Vec<NestedBase> {
    (0..slots)
        .map(|_| {
            NestedBase::new(base(curve, 1, 1, 0, meter), base(curve, 11, 1, 0, meter)).unwrap()
        })
        .collect()
}
fn relation(curve: &Curve, slots: usize, v: u8) -> Relation {
    // Q=[3]P and all slot points equal P: u+3v=slots (mod 7).
    Relation {
        u: ((slots as u8 + 21 - 3 * v) % 7).into(),
        v: v.into(),
        points: vec![curve.generator().clone(); slots],
    }
}

#[test]
fn two_outer_points_cancel_with_odd_order_coefficients_and_replay_provenance() {
    let mut meter = Meter::new(Limits::default());
    let curve = curve(&mut meter);
    let target = curve
        .mul(curve.generator(), &3u8.into(), &mut meter)
        .unwrap();
    let bases = nested(&curve, 2, &mut meter);
    let mut collector = Collector::new(&curve, &target, bases.clone(), 16, 16, &mut meter).unwrap();
    assert!(matches!(
        collector.push(relation(&curve, 2, 0), &mut meter).unwrap(),
        Outcome::Pivot(true)
    ));
    let Outcome::Solved(mut certificate) =
        collector.push(relation(&curve, 2, 1), &mut meter).unwrap()
    else {
        panic!("dependency did not solve");
    };
    assert_eq!(certificate.scalar, BigUint::from(3u8));
    assert_eq!(
        certificate.dependency,
        vec![BigUint::from(6u8), BigUint::from(1u8)]
    );
    partial::verify(&curve, &target, &bases, &certificate, &mut meter).unwrap();
    certificate.dependency[0] = 1u8.into();
    assert!(partial::verify(&curve, &target, &bases, &certificate, &mut meter).is_err());
    assert!(collector.push(relation(&curve, 2, 0), &mut meter).is_err());
}

#[test]
fn partial_admission_limits_and_invalid_rows_fail_closed() {
    let mut meter = Meter::new(Limits::default());
    let curve = curve(&mut meter);
    let target = curve
        .mul(curve.generator(), &3u8.into(), &mut meter)
        .unwrap();
    let bases = nested(&curve, 3, &mut meter);
    let mut collector = Collector::new(&curve, &target, bases, 8, 8, &mut meter).unwrap();
    assert!(matches!(
        collector.push(relation(&curve, 3, 0), &mut meter).unwrap(),
        Outcome::Rejected
    ));
    let mut forged = relation(&curve, 3, 0);
    forged.u = 0u8.into();
    assert!(collector.push(forged, &mut meter).is_err());
    let bases = nested(&curve, 2, &mut meter);
    let mut collector = Collector::new(&curve, &target, bases, 1, 16, &mut meter).unwrap();
    collector.push(relation(&curve, 2, 0), &mut meter).unwrap();
    assert!(matches!(
        collector.push(relation(&curve, 2, 1), &mut meter),
        Err(Error::Limit(_))
    ));
    assert!(NestedBase::new(
        base(&curve, 1, 1, 0, &mut meter),
        base(&curve, 11, 2, 0, &mut meter)
    )
    .is_err());
}

#[test]
fn partial_collection_recovers_from_bounded_random_label_queries() {
    let mut meter = Meter::new(Limits::default());
    let curve = curve(&mut meter);
    let target = curve
        .mul(curve.generator(), &3u8.into(), &mut meter)
        .unwrap();
    let bases = nested(&curve, 2, &mut meter);
    let certificate = partial::solve(
        &curve,
        &target,
        bases.clone(),
        64,
        64,
        128,
        &mut Seeded(701),
        &mut meter,
    )
    .unwrap();
    assert_eq!(certificate.scalar, BigUint::from(3u8));
    partial::verify(&curve, &target, &bases, &certificate, &mut meter).unwrap();
}

#[test]
fn observed_explicit_partial_defaults_preserve_certificate_rng_and_work() {
    let mut setup = Meter::new(Limits::default());
    let curve = curve(&mut setup);
    let target = curve
        .mul(curve.generator(), &3u8.into(), &mut setup)
        .unwrap();
    let bases = nested(&curve, 2, &mut setup);
    let mut plain = Meter::new(Limits::default());
    let mut plain_rng = Seeded(701);
    let expected = partial::solve(
        &curve,
        &target,
        bases.clone(),
        64,
        64,
        128,
        &mut plain_rng,
        &mut plain,
    )
    .unwrap();
    let session = hashed_ecdl_tensor::metrics::Session::start().unwrap();
    let mut observed = Meter::new(Limits::default());
    let mut observed_rng = Seeded(701);
    let mut statistics = Statistics::default();
    let actual = partial::solve_with_options(
        &curve,
        &target,
        bases,
        64,
        64,
        128,
        &Options::default(),
        &mut statistics,
        &mut observed_rng,
        &mut observed,
    )
    .unwrap();
    let snapshot = session.finish().unwrap();
    assert_eq!(actual.scalar, expected.scalar);
    assert_eq!(actual.relations, expected.relations);
    assert_eq!(actual.dependency, expected.dependency);
    assert_eq!(observed_rng.0, plain_rng.0);
    assert_eq!(observed.used, plain.used);
    assert_eq!(
        snapshot.phases.values().map(|p| p.meter_steps).sum::<u64>(),
        observed.used
    );
    assert!(
        snapshot
            .phases
            .values()
            .map(|p| p.adds + p.doubles)
            .sum::<u64>()
            > 0
    );
    assert!(statistics.decodes > 0);
}

#[test]
fn selector_tensor_counts_distinct_decoded_tuples_and_replays_edges() {
    use hashed_ecdl_tensor::contraction::Counter;
    let mut meter = Meter::new(Limits::default());
    let curve = curve(&mut meter);
    let bases = vec![
        base(&curve, 4, 2, 1, &mut meter),
        base(&curve, 4, 3, 4, &mut meter),
    ];
    let a = bases[0]
        .enumerate(&curve, &mut Seeded(31), &mut meter)
        .unwrap();
    let b = bases[1]
        .enumerate(&curve, &mut Seeded(32), &mut meter)
        .unwrap();
    for k in 0..7u8 {
        let target = curve.mul(curve.generator(), &k.into(), &mut meter).unwrap();
        let network = finite::selector_network(&curve, &bases, &target, &mut meter).unwrap();
        assert_eq!(network.input_bit_count(), Some(4));
        let expected = a
            .iter()
            .map(|x| {
                b.iter()
                    .filter(|y| curve.add(x, y, &mut meter).unwrap() == target)
                    .count()
            })
            .sum::<usize>();
        let count = Counter::default()
            .count(&network, &vec![None; network.edge_count()], &mut meter)
            .unwrap();
        assert_eq!(count, BigUint::from(expected));
        let mut accepted = 0;
        for value in 0..16u8 {
            let bits: Vec<_> = (0..4).map(|i| value & (1 << i) != 0).collect();
            if let Some(mut assignment) =
                network.witness_from_input_bits(&bits, &mut meter).unwrap()
            {
                accepted += 1;
                assignment[network.interface()[1]] ^= true;
                assert!(!network.evaluate(&assignment, &mut meter).unwrap());
            }
        }
        assert_eq!(accepted, expected);
    }
}

#[test]
fn optional_schoolbook_encodings_preserve_full_products() {
    use hashed_ecdl_tensor::encoding::Encoder;
    let mut meter = Meter::new(Limits::default());
    for (aw, bw) in [(1, 1), (2, 3), (4, 4)] {
        let mut encoder = Encoder::new();
        let a = encoder.input_word(aw, &meter).unwrap();
        let b = encoder.input_word(bw, &meter).unwrap();
        let product = encoder.schoolbook_multiply(&a, &b, &meter).unwrap();
        encoder.mark_interface(&product, &meter).unwrap();
        let graph = encoder.finish(&meter).unwrap();
        for a in 0..1usize << aw {
            for b in 0..1usize << bw {
                let bits: Vec<_> = (0..aw)
                    .map(|i| a & (1 << i) != 0)
                    .chain((0..bw).map(|i| b & (1 << i) != 0))
                    .collect();
                let assignment = graph
                    .witness_from_input_bits(&bits, &mut meter)
                    .unwrap()
                    .unwrap();
                let actual = graph
                    .interface()
                    .iter()
                    .enumerate()
                    .fold(0, |n, (i, &edge)| n | (usize::from(assignment[edge]) << i));
                assert_eq!(actual, a * b);
            }
        }
    }
}

#[test]
fn selector_cli_receipt_replays_with_the_original_verifier_and_is_exclusive() {
    use std::process::Command;
    let nonce = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let directory = std::env::temp_dir().join(format!(
        "hashed-selector-cli-{}-{nonce}",
        std::process::id()
    ));
    std::fs::create_dir(&directory).unwrap();
    let output = directory.join("receipt.json");
    let input = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("examples/fixture.json");
    let binary = env!("CARGO_BIN_EXE_hashed-ecdl");
    let run = || {
        Command::new(binary)
            .arg("solve-selectors")
            .arg(&input)
            .arg(&output)
            .output()
            .unwrap()
    };
    let result = run();
    assert!(
        result.status.success(),
        "{}",
        String::from_utf8_lossy(&result.stderr)
    );
    let bytes = std::fs::read(&output).unwrap();
    let receipt: serde_json::Value = serde_json::from_slice(&bytes).unwrap();
    assert_eq!(receipt["diagnostics"]["backend"], "SelectorWitness");
    assert_eq!(receipt["diagnostics"]["scalar_decimal"], "4");
    let verified = Command::new(binary)
        .arg("verify")
        .arg(&output)
        .output()
        .unwrap();
    assert!(
        verified.status.success(),
        "{}",
        String::from_utf8_lossy(&verified.stderr)
    );
    assert!(!run().status.success());
    assert_eq!(std::fs::read(&output).unwrap(), bytes);
    std::fs::remove_dir_all(directory).unwrap();
}
