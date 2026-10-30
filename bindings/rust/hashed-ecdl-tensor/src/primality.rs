//! Exact bounded primality and independently checked Pocklington certificates.
//!
//! The first twelve prime bases are deterministic on u64, below the bound of
//! Sorenson/Webster, arXiv:1509.00864. Above that range, accepting a certificate
//! requires the integer hypotheses of HAC Fact 4.40, including certified prime
//! factors and F^2 > n. A failed proof is never a probable-prime acceptance.

use crate::{invalid, overflow, BigUint, Meter, Result};
use num_integer::Integer;
use num_traits::{One, ToPrimitive, Zero};
use std::collections::{BTreeMap, BTreeSet};

fn power64(mut base: u64, mut exponent: u64, modulus: u64, meter: &mut Meter) -> Result<u64> {
    let mut result = 1u64;
    while exponent != 0 {
        if exponent & 1 != 0 {
            meter.charge(1, "exact u64 primality product")?;
            result = (u128::from(result) * u128::from(base) % u128::from(modulus)) as u64;
        }
        exponent >>= 1;
        if exponent != 0 {
            meter.charge(1, "exact u64 primality square")?;
            base = (u128::from(base) * u128::from(base) % u128::from(modulus)) as u64;
        }
    }
    Ok(result)
}

/// Exact primality for the entire u64 domain, using the first twelve prime bases.
/// Products are widened to u128 before reduction. This bound is not extended to
/// larger inputs; the general API retains AKS or an explicitly verified proof.
pub fn is_prime_u64(n: u64, meter: &mut Meter) -> Result<bool> {
    meter.charge(1, "exact u64 primality input")?;
    if n < 2 {
        return Ok(false);
    }
    const BASES: [u64; 12] = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37];
    for base in BASES {
        meter.charge(1, "exact u64 primality divisor")?;
        if n == base {
            return Ok(true);
        }
        if n % base == 0 {
            return Ok(false);
        }
    }
    let twos = (n - 1).trailing_zeros();
    let odd = (n - 1) >> twos;
    'bases: for base in BASES {
        let mut x = power64(base, odd, n, meter)?;
        if x == 1 || x == n - 1 {
            continue;
        }
        for _ in 1..twos {
            meter.charge(1, "exact u64 primality witness square")?;
            x = (u128::from(x) * u128::from(x) % u128::from(n)) as u64;
            if x == n - 1 {
                continue 'bases;
            }
        }
        return Ok(false);
    }
    Ok(true)
}

/// One distinct prime-power factor of the certified divisor of n-1.
#[derive(Clone, Debug)]
pub struct PrimeFactor {
    /// Canonical unsigned decimal encoding of the prime factor.
    pub prime: String,
    /// Strictly positive exponent of this prime in F.
    pub exponent: u32,
}
json_record!(PrimeFactor, required { prime, exponent }, optional {});

/// A Pocklington proof node; dependencies can appear in any input order.
#[derive(Clone, Debug)]
pub struct PrimeCertificate {
    /// Canonical unsigned decimal encoding of the candidate n.
    pub value: String,
    /// One common base satisfying the Fermat and gcd conditions for every factor.
    pub witness: String,
    /// Distinct prime-power factors whose product F divides n-1 and F^2 > n.
    pub factors: Vec<PrimeFactor>,
}
json_record!(
    PrimeCertificate,
    required {
        value,
        witness,
        factors
    },
    optional {}
);

fn decimal(value: &str, meter: &Meter) -> Result<BigUint> {
    if value.is_empty()
        || !value.bytes().all(|b| b.is_ascii_digit())
        || (value.len() > 1 && value.starts_with('0'))
    {
        return Err(invalid("noncanonical certificate integer"));
    }
    meter.bits(
        value
            .len()
            .checked_mul(4)
            .ok_or_else(|| overflow("certificate integer width"))?,
        "certificate decimal width",
    )?;
    BigUint::parse_bytes(value.as_bytes(), 10).ok_or_else(|| invalid("certificate integer"))
}

/// Verify all supplied proof nodes, then return only their established primes.
///
/// Dependencies are processed in increasing numerical order, so no recursive
/// call stack or caller assertion can establish a prime. A non-u64 factor must
/// have an earlier verified node. Duplicate nodes/factors, missing dependencies,
/// insufficient F, forged witnesses and resource exhaustion are errors.
pub fn verify_certificates(
    proofs: &[PrimeCertificate],
    meter: &mut Meter,
) -> Result<BTreeSet<BigUint>> {
    meter.vector(proofs.len(), "prime certificate nodes")?;
    let mut nodes = BTreeMap::new();
    for proof in proofs {
        meter.charge(1, "prime certificate node parsing")?;
        let n = decimal(&proof.value, meter)?;
        if nodes.insert(n, proof).is_some() {
            return Err(invalid("duplicate prime certificate"));
        }
    }
    let mut verified = BTreeSet::new();
    for (n, proof) in nodes {
        meter.charge(1, "prime certificate node verification")?;
        if let Some(small) = n.to_u64() {
            if !proof.factors.is_empty() || !is_prime_u64(small, meter)? {
                return Err(invalid("invalid bounded-prime certificate leaf"));
            }
            verified.insert(n);
            continue;
        }
        if !n.bit(0) || proof.factors.is_empty() {
            return Err(invalid("invalid Pocklington candidate"));
        }
        meter.vector(proof.factors.len(), "prime certificate factors")?;
        let pm1 = &n - BigUint::one();
        let a = decimal(&proof.witness, meter)?;
        if a < BigUint::from(2u8) || a >= n {
            return Err(invalid("Pocklington witness range"));
        }
        let mut factors = BTreeSet::new();
        let mut product = BigUint::one();
        for factor in &proof.factors {
            meter.charge(1, "Pocklington factor")?;
            let q = decimal(&factor.prime, meter)?;
            if q < BigUint::from(2u8)
                || q >= n
                || factor.exponent == 0
                || u64::from(factor.exponent) > n.bits()
                || !factors.insert(q.clone())
            {
                return Err(invalid("Pocklington distinct prime powers"));
            }
            // Reject excessive powers before allocating their big integers.
            let mut prime_power = BigUint::one();
            for _ in 0..factor.exponent {
                meter.charge(1, "Pocklington prime power")?;
                if prime_power > &pm1 / &q {
                    return Err(invalid("Pocklington factor exceeds n-1"));
                }
                prime_power *= &q;
            }
            if product > &pm1 / &prime_power {
                return Err(invalid("Pocklington product exceeds n-1"));
            }
            product *= prime_power;
            if &pm1 % &q != BigUint::zero() {
                return Err(invalid("Pocklington factor divisibility"));
            }
            if !verified.contains(&q) {
                let Some(small) = q.to_u64() else {
                    return Err(invalid("missing certified prime-factor dependency"));
                };
                if !is_prime_u64(small, meter)? {
                    return Err(invalid("composite Pocklington factor"));
                }
                verified.insert(q);
            }
        }
        if &pm1 % &product != BigUint::zero() || &product * &product <= n {
            return Err(invalid("insufficient Pocklington factored divisor"));
        }
        if crate::arithmetic::modpow(&a, &pm1, &n, meter)? != BigUint::one() {
            return Err(invalid("Pocklington Fermat condition"));
        }
        for q in factors {
            let x = crate::arithmetic::modpow(&a, &(&pm1 / &q), &n, meter)?;
            let difference = if x.is_zero() {
                pm1.clone()
            } else {
                x - BigUint::one()
            };
            meter.charge(1, "Pocklington gcd")?;
            if difference.gcd(&n) != BigUint::one() {
                return Err(invalid("Pocklington gcd condition"));
            }
        }
        verified.insert(n);
    }
    Ok(verified)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Error, Limits};

    fn proofs() -> Vec<PrimeCertificate> {
        serde_json::from_str(include_str!("../examples/eccp131-prime-proofs.json")).unwrap()
    }

    #[test]
    fn bounded_primality_matches_independent_sieve_and_handles_u64_edges() {
        let mut sieve = vec![true; 100_001];
        sieve[0] = false;
        sieve[1] = false;
        for p in 2..=316 {
            if sieve[p] {
                for multiple in (p * p..sieve.len()).step_by(p) {
                    sieve[multiple] = false;
                }
            }
        }
        let mut meter = Meter::new(Limits {
            steps: 100_000_000,
            ..Limits::default()
        });
        for (n, &expected) in sieve.iter().enumerate() {
            assert_eq!(is_prime_u64(n as u64, &mut meter).unwrap(), expected, "{n}");
        }
        for prime in [65537, 4_294_967_291, 18_446_744_073_709_551_557] {
            assert!(is_prime_u64(prime, &mut meter).unwrap());
        }
        for composite in [
            341,
            561,
            3_215_031_751,
            341_550_071_728_321,
            3_825_123_056_546_413_051,
            u64::MAX,
        ] {
            assert!(!is_prime_u64(composite, &mut meter).unwrap());
        }
        let mut empty = Meter::new(Limits {
            steps: 0,
            ..Limits::default()
        });
        assert!(matches!(
            is_prime_u64(65537, &mut empty),
            Err(Error::Limit(_))
        ));
    }

    #[test]
    fn challenge_proofs_verify_in_any_order_with_exact_u64_leaves() {
        let mut nodes = proofs();
        let mut meter = Meter::new(Limits {
            steps: 2_000_000,
            ..Limits::default()
        });
        let expected = verify_certificates(&nodes, &mut meter).unwrap();
        for node in &nodes {
            assert!(expected.contains(&decimal(&node.value, &meter).unwrap()));
        }
        nodes.reverse();
        assert_eq!(verify_certificates(&nodes, &mut meter).unwrap(), expected);
    }

    #[test]
    fn forged_and_incomplete_pocklington_proofs_are_rejected() {
        let source = proofs();
        let mut malformed = Vec::new();
        let mut nodes = source.clone();
        nodes.push(nodes[0].clone());
        malformed.push(nodes);
        let mut nodes = source.clone();
        nodes.remove(0);
        malformed.push(nodes);
        let mut nodes = source.clone();
        let duplicate = nodes[0].factors[0].clone();
        nodes[0].factors.push(duplicate);
        malformed.push(nodes);
        let mut nodes = source.clone();
        nodes[0].factors[0].exponent = 0;
        malformed.push(nodes);
        let mut nodes = source.clone();
        nodes[0].factors[0].exponent = u32::MAX;
        malformed.push(nodes);
        let mut nodes = source.clone();
        nodes[0].factors.pop();
        malformed.push(nodes);
        let mut nodes = source.clone();
        nodes[3].factors[0].prime = "16".into();
        malformed.push(nodes);
        let mut nodes = source.clone();
        nodes[0].value.insert(0, '0');
        malformed.push(nodes);
        for witness in [
            "0",
            "1",
            "20182705700968071083965838734546092",
            "20182705700968071083965838734546093",
        ] {
            let mut nodes = source.clone();
            nodes[0].witness = witness.into();
            malformed.push(nodes);
        }
        // Fermat's condition alone passes for base 2 and this composite; the
        // prime-power divisor and gcd obligations must still reject it.
        malformed.push(vec![PrimeCertificate {
            value: "18446744073709551617".into(),
            witness: "2".into(),
            factors: vec![PrimeFactor {
                prime: "2".into(),
                exponent: 64,
            }],
        }]);
        for nodes in malformed {
            let mut meter = Meter::new(Limits::default());
            assert!(matches!(
                verify_certificates(&nodes, &mut meter),
                Err(Error::Invalid(_))
            ));
        }
        let mut empty = Meter::new(Limits {
            steps: 0,
            ..Limits::default()
        });
        assert!(matches!(
            verify_certificates(&source, &mut empty),
            Err(Error::Limit(_))
        ));
    }

    #[test]
    fn official_curve_and_target_validate_within_original_budget() {
        let input: serde_json::Value =
            serde_json::from_str(include_str!("../examples/eccp131-certified.json")).unwrap();
        let n =
            |key: &str| BigUint::parse_bytes(input[key].as_str().unwrap().as_bytes(), 10).unwrap();
        let point = |key: &str| crate::curve::Point::Affine {
            x: BigUint::parse_bytes(input[key][0].as_str().unwrap().as_bytes(), 10).unwrap(),
            y: BigUint::parse_bytes(input[key][1].as_str().unwrap().as_bytes(), 10).unwrap(),
        };
        let nodes: Vec<PrimeCertificate> =
            serde_json::from_value(input["prime_certificates"].clone()).unwrap();
        let mut meter = Meter::new(Limits {
            steps: 2_000_000,
            bits: 4096,
            vector: 200_000,
        });
        let curve = crate::curve::Curve::with_cofactor_and_certificates(
            n("p"),
            n("a"),
            n("b"),
            n("r"),
            n("cofactor"),
            point("generator"),
            &nodes,
            &mut meter,
        )
        .unwrap();
        assert!(curve.in_subgroup(&point("target"), &mut meter).unwrap());
        assert!(meter.used < 2_000_000);
        // Removing the declared subgroup-order proof does not promote it to an
        // unchecked prime; the original exact fallback remains budget-limited.
        let mut incomplete = nodes;
        incomplete.retain(|proof| proof.value != n("r").to_string());
        let mut meter = Meter::new(Limits {
            steps: 2_000_000,
            bits: 4096,
            vector: 200_000,
        });
        assert!(matches!(
            crate::curve::Curve::with_cofactor_and_certificates(
                n("p"),
                n("a"),
                n("b"),
                n("r"),
                n("cofactor"),
                point("generator"),
                &incomplete,
                &mut meter
            ),
            Err(Error::Limit(_))
        ));
    }
}
