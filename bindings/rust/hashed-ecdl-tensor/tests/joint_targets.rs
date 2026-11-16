//! Known-answer controls for joint public-coefficient relation targets.
use hashed_ecdl_tensor::arithmetic::Seeded;
use hashed_ecdl_tensor::curve::{Curve, Point};
use hashed_ecdl_tensor::joint::JointTable;
use hashed_ecdl_tensor::prepared::{self, Statistics};
use hashed_ecdl_tensor::reduction::{self, Config};
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

fn independent(
    curve: &Curve,
    p: &Point,
    q: &Point,
    u: &BigUint,
    v: &BigUint,
    meter: &mut Meter,
) -> Point {
    let left = curve.mul(p, u, meter).unwrap();
    let right = curve.mul(q, v, meter).unwrap();
    curve.add(&left, &right, meter).unwrap()
}

#[test]
fn every_small_scalar_pair_and_exceptional_point_pair_match() {
    let mut meter = Meter::new(Limits::default());
    let curve = curve(&mut meter);
    let g = curve.generator();
    let negative = curve.negate(g).unwrap();
    for (p, q) in [
        (g, g),
        (g, &negative),
        (g, &Point::Infinity),
        (&Point::Infinity, g),
    ] {
        let table = JointTable::new(&curve, p, q, &mut meter).unwrap();
        for u in 0..19u8 {
            for v in 0..19u8 {
                let expected = independent(&curve, p, q, &u.into(), &v.into(), &mut meter);
                assert_eq!(
                    table.evaluate(&u.into(), &v.into(), &mut meter).unwrap(),
                    expected
                );
            }
        }
    }
}

#[test]
fn mixed_width_unreduced_scalars_and_zeroes_match() {
    let mut meter = Meter::new(Limits::default());
    let curve = curve(&mut meter);
    let g = curve.generator();
    let q = curve.mul(g, &3u8.into(), &mut meter).unwrap();
    let table = JointTable::new(&curve, g, &q, &mut meter).unwrap();
    let scalars = [
        0u8.into(),
        1u8.into(),
        18u8.into(),
        19u8.into(),
        BigUint::from(1u8) << 130,
        (BigUint::from(1u8) << 131) - 1u8,
        (BigUint::from(1u8) << 1023) + 5u8,
    ];
    for u in &scalars {
        for v in &scalars {
            assert_eq!(
                table.evaluate(u, v, &mut meter).unwrap(),
                independent(&curve, g, &q, u, v, &mut meter)
            );
        }
    }
}

#[test]
fn subgroup_canonical_and_resource_boundaries_remain_errors() {
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
        assert!(matches!(
            JointTable::new(&curve, curve.generator(), &invalid, &mut meter),
            Err(Error::Invalid(_))
        ));
    }
    let table = JointTable::new(&curve, curve.generator(), curve.generator(), &mut meter).unwrap();
    let mut width = Meter::new(Limits {
        bits: 4,
        ..Limits::default()
    });
    assert!(matches!(
        table.evaluate(&32u8.into(), &0u8.into(), &mut width),
        Err(Error::Limit(_))
    ));
    let mut work = Meter::new(Limits {
        steps: 0,
        ..Limits::default()
    });
    assert!(matches!(
        table.evaluate(&3u8.into(), &2u8.into(), &mut work),
        Err(Error::Limit(_))
    ));
    let mut space = Meter::new(Limits {
        vector: 2,
        ..Limits::default()
    });
    assert!(matches!(
        JointTable::new(&curve, curve.generator(), curve.generator(), &mut space),
        Err(Error::Limit(_))
    ));
}

#[test]
fn whole_seeded_certificates_rng_and_search_events_match() {
    let mut setup = Meter::new(Limits::default());
    let curve = curve(&mut setup);
    let target = curve
        .mul(curve.generator(), &3u8.into(), &mut setup)
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
        let mut joint_rng = Seeded(seed);
        let mut baseline_stats = Statistics::default();
        let mut joint_stats = Statistics::default();
        let control = prepared::solve(
            &curve,
            &target,
            &config,
            &mut baseline_rng,
            true,
            &mut baseline_stats,
            &mut Meter::new(Limits::default()),
        )
        .unwrap();
        let candidate = prepared::solve_joint(
            &curve,
            &target,
            &config,
            &mut joint_rng,
            true,
            &mut joint_stats,
            &mut Meter::new(Limits::default()),
        )
        .unwrap();
        assert_eq!(
            serde_json::to_value(&candidate).unwrap(),
            serde_json::to_value(&control).unwrap()
        );
        assert_eq!(baseline_rng.0, joint_rng.0);
        assert_eq!(format!("{joint_stats:?}"), format!("{baseline_stats:?}"));
        reduction::verify(&curve, &target, &candidate, &mut setup).unwrap();
    }
    // An identity solve must not allocate the joint table or enumerate bases.
    let mut stats = Statistics::default();
    let certificate = prepared::solve_joint(
        &curve,
        &Point::Infinity,
        &config,
        &mut Seeded(1),
        true,
        &mut stats,
        &mut setup,
    )
    .unwrap();
    assert_eq!(certificate.scalar, 0u8.into());
    assert_eq!(stats.preparations, 0);
}

#[test]
fn actual_cli_receipts_match_and_replay() {
    use std::process::Command;
    let nonce = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let dir = std::env::temp_dir().join(format!("joint-cli-{}-{nonce}", std::process::id()));
    std::fs::create_dir(&dir).unwrap();
    let input = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("examples/fixture.json");
    let binary = env!("CARGO_BIN_EXE_hashed-ecdl");
    let mut certificates = Vec::new();
    for command in ["solve-hashed", "solve-hashed-joint"] {
        let output = dir.join(format!("{command}.json"));
        let run = || {
            Command::new(binary)
                .arg(command)
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
        assert_eq!(
            receipt["diagnostics"]["backend"],
            if command == "solve-hashed" {
                "PreparedPair"
            } else {
                "PreparedPairJoint"
            }
        );
        certificates.push(receipt["certificate"].clone());
        assert!(Command::new(binary)
            .arg("verify")
            .arg(&output)
            .status()
            .unwrap()
            .success());
        assert!(!run().status.success());
        assert_eq!(bytes, std::fs::read(&output).unwrap());
    }
    assert_eq!(certificates[0], certificates[1]);
    std::fs::remove_dir_all(dir).unwrap();
}
