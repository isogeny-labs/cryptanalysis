//! Bounded public proof-fixture preparation, not a timing or relation experiment.
//! Use a known certified divisor of s-1; every candidate proof is checked by the
//! ordinary verifier. This does not claim general fast prime-proof generation.

use hashed_ecdl_tensor::primality::{verify_certificates, PrimeCertificate, PrimeFactor};
use hashed_ecdl_tensor::{BigUint, Error, Limits, Meter};
use num_integer::Integer;
use num_traits::One;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut input: serde_json::Value =
        serde_json::from_str(include_str!("eccp131-certified.json"))?;
    let mut proofs: Vec<PrimeCertificate> =
        serde_json::from_value(input["prime_certificates"].clone())?;
    let p = BigUint::parse_bytes(input["p"].as_str().ok_or("p")?.as_bytes(), 10).ok_or("p")?;
    let q = BigUint::parse_bytes(proofs[0].value.as_bytes(), 10).ok_or("q")?;
    let mut multiplier = ((&p << 1usize) - BigUint::one()).div_ceil(&q);
    if multiplier.bit(0) {
        multiplier += BigUint::one();
    }
    let upper = ((&p << 2usize) - BigUint::one()) / &q;
    let mut meter = Meter::new(Limits {
        steps: 2_000_000,
        ..Limits::default()
    });
    verify_certificates(&proofs, &mut meter)?;
    for attempt in 1..=1000 {
        if multiplier > upper {
            break;
        }
        let value = &multiplier * &q + BigUint::one();
        proofs.push(PrimeCertificate {
            value: value.to_string(),
            witness: "2".into(),
            factors: vec![PrimeFactor {
                prime: q.to_string(),
                exponent: 1,
            }],
        });
        match verify_certificates(&proofs, &mut meter) {
            Ok(_) => {
                input["hash_prime"] = serde_json::json!(value.to_string());
                input["prime_certificates"] = serde_json::to_value(&proofs)?;
                serde_json::to_writer_pretty(std::io::stdout(), &input)?;
                eprintln!("verified public fixture after {attempt} candidates; {} diagnostic steps; not a runtime measurement", meter.used);
                return Ok(());
            }
            Err(Error::Invalid(_)) => {}
            Err(error) => return Err(error.into()),
        }
        proofs.pop();
        multiplier += 2u8;
    }
    Err("bounded fixture proof preparation exhausted".into())
}
