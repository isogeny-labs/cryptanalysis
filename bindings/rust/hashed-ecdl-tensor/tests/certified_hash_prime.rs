use hashed_ecdl_tensor::arithmetic::Seeded;
use hashed_ecdl_tensor::contraction::Counter;
use hashed_ecdl_tensor::curve::{Curve, Point};
use hashed_ecdl_tensor::primality::{verify_certificates, PrimeCertificate, PrimeFactor};
use hashed_ecdl_tensor::reduction::{self, Certificate, Config, FactorBase, HashSeed};
use hashed_ecdl_tensor::{BigUint, Error, Limits, Meter};
use serde_json::Value;
use std::io::Write;
use std::process::Command;

fn input() -> Value {
    serde_json::from_str(include_str!("../examples/eccp131-certified-hash.json")).unwrap()
}

fn integer(value: &Value) -> BigUint {
    BigUint::parse_bytes(value.as_str().unwrap().as_bytes(), 10).unwrap()
}

fn curve(input: &Value) -> Curve {
    let mut meter = Meter::new(Limits {
        steps: 2_000_000,
        ..Limits::default()
    });
    Curve::with_cofactor_and_certificates(
        integer(&input["p"]),
        integer(&input["a"]),
        integer(&input["b"]),
        integer(&input["r"]),
        integer(&input["cofactor"]),
        Point::Affine {
            x: integer(&input["generator"][0]),
            y: integer(&input["generator"][1]),
        },
        &serde_json::from_value::<Vec<PrimeCertificate>>(input["prime_certificates"].clone())
            .unwrap(),
        &mut meter,
    )
    .unwrap()
}

fn config(input: &Value) -> Config {
    Config {
        hash_prime: Some(integer(&input["hash_prime"])),
        ..Config::default()
    }
}

#[test]
fn certified_hash_and_multiple_slot_bases_reuse_only_checked_proofs() {
    let input = input();
    let curve = curve(&input).clone();
    let prime = integer(&input["hash_prime"]);
    assert_eq!(prime.bits(), 132);
    let mut meter = Meter::new(Limits {
        steps: 1,
        ..Limits::default()
    });
    config(&input)
        .validate_hash_prime(&curve, &mut meter)
        .unwrap();
    assert_eq!(meter.used, 1);
    for alpha in [1u8, 2] {
        let mut meter = Meter::new(Limits {
            steps: 1,
            ..Limits::default()
        });
        let base = FactorBase::new(
            &curve,
            prime.clone(),
            1u8.into(),
            HashSeed {
                alpha: alpha.into(),
                beta: 0u8.into(),
            },
            &mut meter,
        )
        .unwrap();
        assert_eq!(base.prime(), &prime);
        assert_eq!(meter.used, 1);
    }
}

#[test]
fn cached_proofs_preserve_width_work_range_and_seed_checks() {
    let input = input();
    let curve = curve(&input);
    for limits in [
        Limits {
            steps: 0,
            ..Limits::default()
        },
        Limits {
            bits: 64,
            ..Limits::default()
        },
    ] {
        assert!(matches!(
            config(&input).validate_hash_prime(&curve, &mut Meter::new(limits)),
            Err(Error::Limit(_))
        ));
    }
    let prime = integer(&input["hash_prime"]);
    let mut meter = Meter::new(Limits::default());
    for (threshold, alpha, beta) in [
        (0u8.into(), 1u8.into(), 0u8.into()),
        (1u8.into(), 0u8.into(), 0u8.into()),
        (1u8.into(), 1u8.into(), prime.clone()),
    ] {
        assert!(matches!(
            FactorBase::new(
                &curve,
                prime.clone(),
                threshold,
                HashSeed { alpha, beta },
                &mut meter
            ),
            Err(Error::Invalid(_))
        ));
    }
    // Even a proven prime may not violate the factor-base interval.
    let wrong_range = Config {
        hash_prime: Some(curve.order().clone()),
        ..Config::default()
    };
    assert!(matches!(
        wrong_range.validate_hash_prime(&curve, &mut meter),
        Err(Error::Invalid(_))
    ));
    let composite = Config {
        hash_prime: Some(&prime + 1u8),
        ..Config::default()
    };
    assert!(matches!(
        composite.validate_hash_prime(&curve, &mut meter),
        Err(Error::Invalid(_))
    ));
}

#[test]
fn an_uncovered_hash_prime_still_requires_the_exact_fallback() {
    let mut input = input();
    let selected = input["hash_prime"].clone();
    input["prime_certificates"]
        .as_array_mut()
        .unwrap()
        .retain(|proof| proof["value"] != selected);
    let curve = curve(&input);
    let mut meter = Meter::new(Limits {
        steps: 1000,
        ..Limits::default()
    });
    assert!(matches!(
        config(&input).validate_hash_prime(&curve, &mut meter),
        Err(Error::Limit(_))
    ));
}

#[test]
fn the_65bit_boundary_has_an_exact_bounded_pocklington_control() {
    // GNU factor supplied this untrusted divisor; the native verifier must
    // establish its primality and both Pocklington conditions independently.
    let proofs = [PrimeCertificate {
        value: "18446744073709551629".into(),
        witness: "2".into(),
        factors: vec![PrimeFactor {
            prime: "658812288346769701".into(),
            exponent: 1,
        }],
    }];
    let mut meter = Meter::new(Limits {
        steps: 20_000,
        ..Limits::default()
    });
    let primes = verify_certificates(&proofs, &mut meter).unwrap();
    let value = BigUint::parse_bytes(proofs[0].value.as_bytes(), 10).unwrap();
    assert_eq!(value.bits(), 65);
    assert!(primes.contains(&value));
    let mut forged = proofs;
    forged[0].witness = "1".into();
    assert!(matches!(
        verify_certificates(&forged, &mut meter),
        Err(Error::Invalid(_))
    ));
}

#[test]
fn fixed_hash_solve_and_algebraic_replay_agree() {
    let mut meter = Meter::new(Limits {
        steps: 2_000_000_000,
        ..Limits::default()
    });
    let curve = Curve::with_cofactor_and_certificates(
        5u8.into(),
        2u8.into(),
        1u8.into(),
        7u8.into(),
        1u8.into(),
        Point::Affine {
            x: 0u8.into(),
            y: 1u8.into(),
        },
        &[PrimeCertificate {
            value: "11".into(),
            witness: "2".into(),
            factors: vec![],
        }],
        &mut meter,
    )
    .unwrap();
    let target = curve
        .mul(curve.generator(), &4u8.into(), &mut meter)
        .unwrap();
    let config = Config {
        hash_prime: Some(11u8.into()),
        ..Config::default()
    };
    let certificate = reduction::solve(
        &curve,
        &target,
        &config,
        &mut Seeded(1),
        &mut Counter::default(),
        &mut meter,
    )
    .unwrap();
    assert_eq!(certificate.scalar, 4u8.into());
    assert_eq!(certificate.prime, 11u8.into());
    reduction::verify_with_rng(&curve, &target, &certificate, &mut Seeded(7), &mut meter).unwrap();
}

#[test]
fn runner_preflight_checks_the_hash_prime_and_replay_enforces_its_pin() {
    let output = Command::new(env!("CARGO_BIN_EXE_hashed-ecdl"))
        .args([
            "validate",
            concat!(
                env!("CARGO_MANIFEST_DIR"),
                "/examples/eccp131-certified-hash.json"
            ),
        ])
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let result: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(result["hash_prime"], input()["hash_prime"]);
    assert_eq!(result["challenge_solved"], false);
    assert!(result["charged_steps"].as_u64().unwrap() < 2_000_000);
    println!(
        "parameter/target/hash preflight diagnostic steps: {}",
        result["charged_steps"]
    );

    let receipt = serde_json::json!({
        "schema": "hashed-ecdl-tensor/v1", "problem": input(), "diagnostics": {},
        "certificate": Certificate { version: 1, prime: 0u8.into(), threshold: 0u8.into(),
            seeds: vec![], relations: vec![], dependency: vec![], scalar: 0u8.into() },
    });
    let path = std::env::temp_dir().join(format!(
        "hashed-ecdl-pinned-receipt-{}.json",
        std::process::id()
    ));
    let mut file = std::fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&path)
        .unwrap();
    file.write_all(&serde_json::to_vec(&receipt).unwrap())
        .unwrap();
    drop(file);
    let output = Command::new(env!("CARGO_BIN_EXE_hashed-ecdl"))
        .arg("verify")
        .arg(&path)
        .output()
        .unwrap();
    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("receipt hash prime differs"));
    std::fs::remove_file(path).unwrap();
}
