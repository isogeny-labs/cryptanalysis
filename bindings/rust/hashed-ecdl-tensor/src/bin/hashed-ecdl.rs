//! File-based native runner and independent certificate replay.

use hashed_ecdl_tensor::arithmetic::{OsRandom, RandomSource, Seeded};
use hashed_ecdl_tensor::contraction::Counter;
use hashed_ecdl_tensor::curve::{Curve, Point};
use hashed_ecdl_tensor::primality::PrimeCertificate;
use hashed_ecdl_tensor::reduction::{self, Certificate, Config};
use hashed_ecdl_tensor::{finite, width};
use hashed_ecdl_tensor::{BigUint, Error, Limits, Meter};
use serde_json::{json, Value};
use std::io::Read;
use std::path::Path;

#[macro_use]
#[path = "../serialization.rs"]
mod serialization;

struct Problem {
    p: String,
    a: String,
    b: String,
    r: String,
    cofactor: String,
    generator: [String; 2],
    // null denotes the identity; coordinates and integers use decimal strings.
    target: Option<[String; 2]>,
    slots: Option<usize>,
    threshold: Option<String>,
    hash_prime: Option<String>,
    trials: Option<usize>,
    columns: Option<usize>,
    steps: Option<u64>,
    vector: Option<usize>,
    bits: Option<usize>,
    // Only for reproducible public fixtures. Omit to use operating-system RNG.
    fixture_seed: Option<u64>,
    prime_certificates: Option<Vec<PrimeCertificate>>,
}
json_record!(
    Problem,
    required {
        p,
        a,
        b,
        r,
        cofactor,
        generator,
        target
    },
    optional {
        slots,
        threshold,
        hash_prime,
        trials,
        columns,
        steps,
        vector,
        bits,
        fixture_seed,
        prime_certificates
    }
);

struct Receipt {
    schema: String,
    problem: Problem,
    certificate: Certificate,
    // Diagnostic data are informational; replay never trusts execution history.
    diagnostics: Value,
}
json_record!(
    Receipt,
    required {
        schema,
        problem,
        certificate,
        diagnostics
    },
    optional {}
);

fn integer(s: &str) -> Result<BigUint, Error> {
    if s.is_empty() || !s.bytes().all(|c| c.is_ascii_digit()) {
        return Err(Error::Invalid("expected unsigned decimal string".into()));
    }
    BigUint::parse_bytes(s.as_bytes(), 10).ok_or_else(|| Error::Invalid("decimal integer".into()))
}

fn point(pair: &[String; 2]) -> Result<Point, Error> {
    Ok(Point::Affine {
        x: integer(&pair[0])?,
        y: integer(&pair[1])?,
    })
}

fn prepare(problem: &Problem) -> Result<(Curve, Point, Config, Meter), Error> {
    let defaults = Limits::default();
    let mut meter = Meter::new(Limits {
        steps: problem.steps.unwrap_or(defaults.steps),
        vector: problem.vector.unwrap_or(defaults.vector),
        bits: problem.bits.unwrap_or(defaults.bits),
    });
    let curve = Curve::with_cofactor_and_certificates(
        integer(&problem.p)?,
        integer(&problem.a)?,
        integer(&problem.b)?,
        integer(&problem.r)?,
        integer(&problem.cofactor)?,
        point(&problem.generator)?,
        problem.prime_certificates.as_deref().unwrap_or(&[]),
        &mut meter,
    )?;
    let target = problem
        .target
        .as_ref()
        .map(point)
        .transpose()?
        .unwrap_or(Point::Infinity);
    let mut config = Config::for_curve(&curve);
    if let Some(slots) = problem.slots {
        config.slots = slots;
    }
    config.threshold = problem.threshold.as_deref().map(integer).transpose()?;
    config.hash_prime = problem.hash_prime.as_deref().map(integer).transpose()?;
    if let Some(trials) = problem.trials {
        config.trials = trials;
    }
    if let Some(columns) = problem.columns {
        config.columns = columns;
    }
    Ok((curve, target, config, meter))
}

const INPUT_LIMIT: usize = 16 * 1024 * 1024;

fn read_input(input: impl Read) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    let mut bytes = Vec::new();
    // One extra byte distinguishes an exact-limit input from a truncated input.
    // This also bounds growing files and streams whose metadata reports zero.
    input.take(INPUT_LIMIT as u64 + 1).read_to_end(&mut bytes)?;
    if bytes.len() > INPUT_LIMIT {
        return Err("input file exceeds 16 MiB runner policy".into());
    }
    Ok(bytes)
}

fn read(path: &str) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    read_input(std::fs::File::open(path)?)
}

fn solve_command(
    command: &str,
    curve: &Curve,
    target: &Point,
    config: &Config,
    rng: &mut impl RandomSource,
    counter: &mut Counter,
    statistics: &mut finite::Statistics,
    meter: &mut Meter,
) -> Result<Certificate, Error> {
    match command {
        "solve-selectors" => reduction::solve_with_oracle(
            curve,
            target,
            config,
            rng,
            |c, b, q, w| {
                finite::prime_decompose(c, b, q, &finite::Options::default(), statistics, w)
            },
            meter,
        ),
        "solve-width" => reduction::solve_with_oracle(
            curve,
            target,
            config,
            rng,
            |c, b, q, w| {
                reduction::decompose_with(
                    c,
                    b,
                    q,
                    |network, work| {
                        let pins = vec![None; network.edge_count()];
                        let plan = width::plan(network, &pins, &width::Policy::default(), work)?;
                        width::witness(network, &pins, &plan, work)
                    },
                    w,
                )
            },
            meter,
        ),
        _ => reduction::solve(curve, target, config, rng, counter, meter),
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args().collect();
    match args.get(1).map(String::as_str) {
        Some("validate") if args.len() == 3 => {
            let problem: Problem = serde_json::from_slice(&read(&args[2])?)?;
            let (curve, target, config, mut meter) = prepare(&problem)?;
            config.validate_hash_prime(&curve, &mut meter)?;
            if !curve.in_subgroup(&target, &mut meter)? {
                return Err("target is outside the certified subgroup".into());
            }
            println!("{}", json!({"status":"validated", "p":curve.modulus().to_string(),
                "r":curve.order().to_string(), "charged_steps":meter.used,
                "hash_prime":config.hash_prime.as_ref().map(ToString::to_string),
                "challenge_solved":false}));
        }
        Some("solve" | "solve-selectors" | "solve-width") if args.len() == 4 => {
            let problem: Problem = serde_json::from_slice(&read(&args[2])?)?;
            let (curve, target, config, mut meter) = prepare(&problem)?;
            let mut counter = Counter::default();
            let mut finite_statistics = finite::Statistics::default();
            let certificate = if let Some(seed) = problem.fixture_seed {
                solve_command(&args[1], &curve, &target, &config, &mut Seeded(seed), &mut counter, &mut finite_statistics, &mut meter)?
            } else {
                solve_command(&args[1], &curve, &target, &config, &mut OsRandom, &mut counter, &mut finite_statistics, &mut meter)?
            };
            let mut diagnostics = json!({
                "backend": format!("{:?}", counter.statistics.last_backend),
                "contractions": counter.statistics.contractions,
                "recursive_calls": counter.statistics.recursive_calls,
                "edge_assignments": counter.statistics.edge_assignments,
                "functional_assignments": counter.statistics.functional_assignments,
                "witness_searches": counter.statistics.witness_searches,
                "charged_steps": meter.used,
                "scalar_decimal": certificate.scalar.to_string(),
            });
            if args[1] == "solve-selectors" {
                diagnostics["backend"] = json!("SelectorWitness");
                diagnostics["selector_decodes"] = json!(finite_statistics.decodes);
                diagnostics["selector_cache_hits"] = json!(finite_statistics.cache_hits);
                diagnostics["derived_checks"] = json!(finite_statistics.derived_checks);
            } else if args[1] == "solve-width" {
                diagnostics["backend"] = json!("WidthWitness");
            }
            let receipt = Receipt { schema: "hashed-ecdl-tensor/v1".into(), problem, certificate, diagnostics };
            // Creation is exclusive: evidence files are never silently replaced.
            let file = std::fs::OpenOptions::new().write(true).create_new(true).open(Path::new(&args[3]))?;
            serde_json::to_writer_pretty(file, &receipt)?;
            println!("verified scalar {}; receipt {}", receipt.certificate.scalar, args[3]);
        }
        Some("verify") if args.len() == 3 => {
            let receipt: Receipt = serde_json::from_slice(&read(&args[2])?)?;
            if receipt.schema != "hashed-ecdl-tensor/v1" { return Err("unsupported receipt schema".into()); }
            let (curve, target, config, mut meter) = prepare(&receipt.problem)?;
            config.validate_hash_prime(&curve, &mut meter)?;
            if target != Point::Infinity && config.hash_prime.as_ref().is_some_and(|s| s != &receipt.certificate.prime) {
                return Err("receipt hash prime differs from the configured modulus".into());
            }
            reduction::verify(&curve, &target, &receipt.certificate, &mut meter)?;
            println!("certificate verified: scalar {}", receipt.certificate.scalar);
        }
        _ => return Err("usage: hashed-ecdl validate PROBLEM.json | hashed-ecdl solve|solve-selectors|solve-width PROBLEM.json NEW_RECEIPT.json | hashed-ecdl verify RECEIPT.json".into()),
    }
    Ok(())
}

fn main() {
    if let Err(error) = run() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const FIXTURE: &str = include_str!("../../examples/fixture.json");

    #[test]
    fn strict_json_problem_rejects_duplicates_even_after_null() {
        for field in ["target", "slots", "fixture_seed"] {
            let duplicate = format!("{{\"{field}\":null,{}", &FIXTURE.trim()[1..]);
            let error = serde_json::from_str::<Problem>(&duplicate)
                .err()
                .expect("duplicate must be rejected")
                .to_string();
            assert!(error.contains("duplicate field"), "{field}: {error}");
        }
    }

    #[test]
    fn strict_json_problem_keeps_optional_defaults_and_required_target() {
        let mut problem: Value = serde_json::from_str(FIXTURE).unwrap();
        for field in [
            "slots",
            "threshold",
            "trials",
            "columns",
            "steps",
            "vector",
            "bits",
            "fixture_seed",
        ] {
            problem.as_object_mut().unwrap().remove(field);
        }
        problem["target"] = Value::Null;
        let minimal: Problem = serde_json::from_value(problem.clone()).unwrap();
        assert!(minimal.target.is_none());
        assert!(minimal.slots.is_none());
        assert!(minimal.fixture_seed.is_none());
        problem.as_object_mut().unwrap().remove("target");
        assert!(serde_json::from_value::<Problem>(problem.clone()).is_err());
        problem["target"] = Value::Null;
        problem["unknown"] = Value::Null;
        assert!(serde_json::from_value::<Problem>(problem).is_err());
    }

    #[test]
    fn strict_json_receipt_rejects_duplicate_fields_and_nested_problems() {
        let value = json!({
            "schema": "hashed-ecdl-tensor/v1",
            "problem": serde_json::to_value(serde_json::from_str::<Problem>(FIXTURE).unwrap()).unwrap(),
            "certificate": {
                "version": 1, "prime": [], "threshold": [], "seeds": [],
                "relations": [], "dependency": [], "scalar": []
            },
            "diagnostics": null
        });
        let encoded = value.to_string();
        let receipt: Receipt = serde_json::from_str(&encoded).unwrap();
        assert_eq!(serde_json::to_value(receipt).unwrap(), value);
        for (field, content) in value.as_object().unwrap() {
            let duplicate = format!("{{\"{field}\":{content},{}", &encoded[1..]);
            let error = serde_json::from_str::<Receipt>(&duplicate)
                .err()
                .expect("duplicate receipt field must be rejected")
                .to_string();
            assert!(error.contains("duplicate field"), "{field}: {error}");
        }
        let duplicate = encoded.replace("\"target\":", "\"target\":null,\"target\":");
        let error = serde_json::from_str::<Receipt>(&duplicate)
            .err()
            .expect("nested duplicate must be rejected")
            .to_string();
        assert!(error.contains("duplicate field"), "{error}");
    }

    #[test]
    fn input_limit_applies_to_bytes_read_from_a_stream() {
        let empty = read_input(std::io::empty()).unwrap();
        assert!(empty.is_empty());
        let exact = read_input(std::io::repeat(b' ').take(INPUT_LIMIT as u64)).unwrap();
        assert_eq!(exact.len(), INPUT_LIMIT);
        // Model a source without EOF, but fail promptly if the reader overreads.
        struct Stream(usize);
        impl Read for Stream {
            fn read(&mut self, buffer: &mut [u8]) -> std::io::Result<usize> {
                assert!(self.0 > 0, "read beyond the one-byte lookahead");
                let n = buffer.len().min(self.0);
                buffer[..n].fill(b' ');
                self.0 -= n;
                Ok(n)
            }
        }
        let mut stream = Stream(INPUT_LIMIT + 1);
        let error = read_input(&mut stream).unwrap_err().to_string();
        assert!(error.contains("exceeds 16 MiB"), "{error}");
        assert_eq!(stream.0, 0);
    }

    #[test]
    fn input_reader_preserves_io_errors() {
        struct Broken;
        impl Read for Broken {
            fn read(&mut self, _: &mut [u8]) -> std::io::Result<usize> {
                Err(std::io::Error::other("test read failure"))
            }
        }
        let error = read_input(Broken).unwrap_err().to_string();
        assert!(error.contains("test read failure"), "{error}");
    }
}
