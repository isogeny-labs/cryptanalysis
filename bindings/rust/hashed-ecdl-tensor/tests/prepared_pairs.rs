//! Public known-answer controls for reusable two-slot relation collection.
use hashed_ecdl_tensor::arithmetic::Seeded;
use hashed_ecdl_tensor::curve::{Curve, Point};
use hashed_ecdl_tensor::finite::{self, Options};
use hashed_ecdl_tensor::prepared::{self, PairTable, Statistics};
use hashed_ecdl_tensor::reduction::{self, Config, FactorBase, HashSeed};
use hashed_ecdl_tensor::{Error, Limits, Meter};

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
fn bases(curve: &Curve, thresholds: [u8; 2], shift: u8, meter: &mut Meter) -> Vec<FactorBase> {
    thresholds
        .into_iter()
        .enumerate()
        .map(|(i, threshold)| {
            FactorBase::new(
                curve,
                37u8.into(),
                threshold.into(),
                HashSeed {
                    alpha: (1u8 + i as u8 * 2).into(),
                    beta: shift.into(),
                },
                meter,
            )
            .unwrap()
        })
        .collect()
}

#[test]
fn complete_first_witness_streams_match_across_reused_queries() {
    for thresholds in [[12, 24], [24, 12], [12, 12]] {
        for shift in [0, 4, 7] {
            let mut preparation = Meter::new(Limits::default());
            let curve = curve(&mut preparation);
            let bases = bases(&curve, thresholds, shift, &mut preparation);
            let mut statistics = Statistics::default();
            let table = PairTable::new(&curve, &bases, &mut statistics, &mut preparation).unwrap();
            assert_eq!(statistics.preparations, 1);
            let mut query_work = Meter::new(Limits::default());
            for smallest_first in [false, true] {
                for k in 0..19u8 {
                    let target = curve
                        .mul(curve.generator(), &k.into(), &mut preparation)
                        .unwrap();
                    let expected = finite::prime_decompose(
                        &curve,
                        &bases,
                        &target,
                        &Options {
                            smallest_first,
                            ..Options::default()
                        },
                        &mut finite::Statistics::default(),
                        &mut preparation,
                    )
                    .unwrap();
                    let actual = table
                        .decompose(&target, smallest_first, &mut statistics, &mut query_work)
                        .unwrap();
                    assert_eq!(
                        actual, expected,
                        "{thresholds:?}, shift {shift}, target {k}"
                    );
                }
            }
            assert_eq!(statistics.preparations, 1);
        }
    }
}

#[test]
fn complete_empty_base_is_negative_and_limits_remain_errors() {
    let mut meter = Meter::new(Limits::default());
    let curve = curve(&mut meter);
    let bases = bases(&curve, [1, 12], 3, &mut meter);
    let mut statistics = Statistics::default();
    let table = PairTable::new(&curve, &bases, &mut statistics, &mut meter).unwrap();
    assert_eq!(
        table
            .decompose(curve.generator(), true, &mut statistics, &mut meter)
            .unwrap(),
        None
    );
    assert_eq!(statistics.lookups, 0);
    let mut limited = Meter::new(Limits {
        steps: 0,
        ..Limits::default()
    });
    assert!(matches!(
        table.decompose(curve.generator(), true, &mut statistics, &mut limited),
        Err(Error::Limit(_))
    ));
    let mut limited = Meter::new(Limits {
        vector: 1,
        ..Limits::default()
    });
    assert!(matches!(
        PairTable::new(&curve, &bases, &mut statistics, &mut limited),
        Err(Error::Limit(_))
    ));
}

#[test]
fn fixed_cofactor_queries_keep_original_subgroup_checks() {
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
    let bases: Vec<_> = [0u8, 3]
        .into_iter()
        .map(|beta| {
            FactorBase::new(
                &curve,
                11u8.into(),
                11u8.into(),
                HashSeed {
                    alpha: 1u8.into(),
                    beta: beta.into(),
                },
                &mut meter,
            )
            .unwrap()
        })
        .collect();
    let mut statistics = Statistics::default();
    let table = PairTable::new(&curve, &bases, &mut statistics, &mut meter).unwrap();
    for k in 0..3u8 {
        let target = curve.mul(curve.generator(), &k.into(), &mut meter).unwrap();
        let expected = finite::prime_decompose(
            &curve,
            &bases,
            &target,
            &Options::default(),
            &mut finite::Statistics::default(),
            &mut meter,
        )
        .unwrap();
        assert_eq!(
            table
                .decompose(&target, true, &mut statistics, &mut meter)
                .unwrap(),
            expected
        );
    }
    assert!(matches!(
        table.decompose(
            &Point::Affine {
                x: 2u8.into(),
                y: 2u8.into()
            },
            true,
            &mut statistics,
            &mut meter
        ),
        Err(Error::Invalid(_))
    ));
}

#[test]
fn full_seeded_certificates_and_relation_rng_match_the_selector_control() {
    let mut meter = Meter::new(Limits::default());
    let curve = curve(&mut meter);
    let target = curve
        .mul(curve.generator(), &3u8.into(), &mut meter)
        .unwrap();
    let config = Config {
        slots: 2,
        threshold: Some(12u8.into()),
        columns: 64,
        trials: 32,
        ..Config::default()
    };
    for seed in [1, 42, 83] {
        let mut baseline_rng = Seeded(seed);
        let mut candidate_rng = Seeded(seed);
        let control = reduction::solve_with_oracle(
            &curve,
            &target,
            &config,
            &mut baseline_rng,
            |c, b, q, w| {
                finite::prime_decompose(
                    c,
                    b,
                    q,
                    &Options::default(),
                    &mut finite::Statistics::default(),
                    w,
                )
            },
            &mut meter,
        )
        .unwrap();
        let mut statistics = Statistics::default();
        let candidate = prepared::solve(
            &curve,
            &target,
            &config,
            &mut candidate_rng,
            true,
            &mut statistics,
            &mut meter,
        )
        .unwrap();
        assert_eq!(
            serde_json::to_value(&candidate).unwrap(),
            serde_json::to_value(&control).unwrap()
        );
        assert_eq!(baseline_rng.0, candidate_rng.0);
        assert!(statistics.preparations > 0 && statistics.queries > 1 && statistics.replays > 0);
        reduction::verify(&curve, &target, &candidate, &mut meter).unwrap();
        let mut forged = candidate.clone();
        forged.relations[0].points[0] = Point::Infinity;
        assert!(reduction::verify(&curve, &target, &forged, &mut meter).is_err());
    }
    let unsupported = Config { slots: 3, ..config };
    assert!(matches!(
        prepared::solve(
            &curve,
            &target,
            &unsupported,
            &mut Seeded(1),
            true,
            &mut Statistics::default(),
            &mut meter
        ),
        Err(Error::Invalid(_))
    ));
}

#[test]
fn solve_hashed_cli_replays_and_preserves_existing_outputs() {
    use std::process::Command;
    let nonce = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let dir =
        std::env::temp_dir().join(format!("prepared-pair-cli-{}-{nonce}", std::process::id()));
    std::fs::create_dir(&dir).unwrap();
    let output = dir.join("receipt.json");
    let input = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("examples/fixture.json");
    let binary = env!("CARGO_BIN_EXE_hashed-ecdl");
    let run = || {
        Command::new(binary)
            .arg("solve-hashed")
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
    assert_eq!(receipt["diagnostics"]["backend"], "PreparedPair");
    assert_eq!(receipt["diagnostics"]["scalar_decimal"], "4");
    assert!(
        receipt["diagnostics"]["prepared_pair_builds"]
            .as_u64()
            .unwrap()
            > 0
    );
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
    std::fs::remove_dir_all(dir).unwrap();
}
