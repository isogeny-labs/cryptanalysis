//! Exact bounded primality and independently checked Pocklington certificates.
//!
//! The first thirteen prime bases are deterministic strictly below the bound of
//! Sorenson/Webster, arXiv:1509.00864. Above that range, accepting a certificate
//! requires the integer hypotheses of HAC Fact 4.40, including certified prime
//! factors and F^2 > n. A failed proof is never a probable-prime acceptance.

use crate::{invalid, overflow, BigUint, Meter, Result};
use num_integer::Integer;
use num_traits::{One, ToPrimitive, Zero};
use std::collections::{BTreeMap, BTreeSet};
use std::sync::OnceLock;

// Sorenson/Webster, Theorem 1.1: the smallest strong pseudoprime to
// the first thirteen prime bases. The inequality must be STRICT.
const BOUNDED_LIMIT: u128 = 3_317_044_064_679_887_385_961_981;
const BASES: [u64; 13] = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41];

/// Exact below the published bound; above it only a failed witness decides.
/// `None` means that all witnesses passed outside the deterministic range.
pub(crate) fn bounded_primality(n: &BigUint, meter: &mut Meter) -> Result<Option<bool>> {
    if let Some(value) = n.to_u64() {
        return is_prime_u64(value, meter).map(Some);
    }
    let minus_one = n - BigUint::one();
    let twos = minus_one.trailing_zeros().unwrap();
    let odd = &minus_one >> twos;
    'bases: for base in BASES {
        meter.charge(1, "bounded primality divisor")?;
        if n % base == BigUint::zero() {
            return Ok(Some(false));
        }
        let mut x = crate::arithmetic::modpow(&base.into(), &odd, n, meter)?;
        if x.is_one() || x == minus_one {
            continue;
        }
        for _ in 1..twos {
            meter.charge(1, "bounded primality witness square")?;
            x = &x * &x % n;
            if x == minus_one {
                continue 'bases;
            }
        }
        return Ok(Some(false));
    }
    Ok((n < &BigUint::from(BOUNDED_LIMIT)).then_some(true))
}

struct ProofSearch {
    rho_left: usize,
    known: BTreeSet<BigUint>,
    nodes: Vec<PrimeCertificate>,
}

impl ProofSearch {
    // Bounded small-factor search, HAC Algorithm 3.9, with deterministic
    // restarts. Failure establishes nothing about the candidate's primality.
    fn split(&mut self, n: &BigUint, meter: &mut Meter) -> Result<Option<BigUint>> {
        for c in 1u8..=4 {
            let mut x = BigUint::from(2u8);
            let mut y = x.clone();
            for _ in 0..4096 {
                if self.rho_left == 0 {
                    return Ok(None);
                }
                self.rho_left -= 1;
                meter.charge(4, "Pocklington bounded factor search")?;
                x = (&x * &x + c) % n;
                y = (&y * &y + c) % n;
                y = (&y * &y + c) % n;
                let d = if x >= y { &x - &y } else { &y - &x }.gcd(n);
                if d == *n {
                    break;
                }
                if !d.is_one() {
                    return Ok(Some(d));
                }
            }
        }
        Ok(None)
    }

    fn prove(&mut self, n: &BigUint, depth: usize, meter: &mut Meter) -> Result<bool> {
        meter.charge(1, "Pocklington proof search")?;
        if self.known.contains(n) {
            return Ok(true);
        }
        if self.nodes.len() >= 64 || depth >= 32 {
            return Ok(false);
        }
        match bounded_primality(n, meter)? {
            Some(false) => return Ok(false),
            Some(true) => {
                // u64 factors need no explicit leaf. Wider exact bounded
                // decisions are serialized so the verifier can replay them.
                if n.to_u64().is_none() {
                    meter.vector(self.nodes.len() + 1, "generated prime proofs")?;
                    self.nodes.push(PrimeCertificate {
                        value: n.to_string(),
                        witness: "2".into(),
                        factors: vec![],
                    });
                }
                self.known.insert(n.clone());
                return Ok(true);
            }
            None => {}
        }
        let minus_one = n - BigUint::one();
        let mut remaining = minus_one.clone();
        let mut product = BigUint::one();
        let mut factors = BTreeMap::<BigUint, u32>::new();
        // All divisors through 97 suffice here: once smaller prime powers
        // are removed, a composite divisor cannot divide the remainder.
        for divisor in 2u32..=97 {
            meter.charge(1, "Pocklington trial divisor")?;
            let q = BigUint::from(divisor);
            while (&remaining % &q).is_zero() {
                meter.charge(1, "Pocklington trial factor")?;
                remaining /= &q;
                product *= &q;
                *factors.entry(q.clone()).or_default() += 1;
            }
        }
        meter.vector(1, "Pocklington pending factors")?;
        let mut pending = vec![remaining];
        while &product * &product <= *n {
            let Some(value) = pending.pop() else {
                return Ok(false);
            };
            if value.is_one() {
                continue;
            }
            if self.prove(&value, depth + 1, meter)? {
                product *= &value;
                *factors.entry(value).or_default() += 1;
            } else if let Some(factor) = self.split(&value, meter)? {
                meter.vector(pending.len() + 2, "Pocklington pending factors")?;
                pending.push(&value / &factor);
                pending.push(factor);
            } else {
                return Ok(false);
            }
        }
        for witness in 2u32..=257 {
            let a = BigUint::from(witness);
            if crate::arithmetic::modpow(&a, &minus_one, n, meter)? != BigUint::one() {
                return Ok(false);
            }
            let mut valid = true;
            for q in factors.keys() {
                let x = crate::arithmetic::modpow(&a, &(&minus_one / q), n, meter)?;
                let difference = if x.is_zero() {
                    minus_one.clone()
                } else {
                    x - BigUint::one()
                };
                meter.charge(1, "Pocklington witness gcd")?;
                if !difference.gcd(n).is_one() {
                    valid = false;
                    break;
                }
            }
            if valid {
                if self.nodes.len() >= 64 {
                    return Ok(false);
                }
                meter.vector(self.nodes.len() + 1, "generated prime proofs")?;
                self.nodes.push(PrimeCertificate {
                    value: n.to_string(),
                    witness: a.to_string(),
                    factors: factors
                        .into_iter()
                        .map(|(prime, exponent)| PrimeFactor {
                            prime: prime.to_string(),
                            exponent,
                        })
                        .collect(),
                });
                self.known.insert(n.clone());
                return Ok(true);
            }
        }
        Ok(false)
    }
}

/// Attempt a bounded, deterministic Pocklington proof without external tools.
///
/// Small trial factors, certified cofactors and at most 16,384 rho iterations
/// are used; recursion is capped at 32 levels, proof output at 64 nodes, and
/// each node tries at most 256 common witnesses.
/// Bundled public challenge proofs avoid factoring their n-1 again; their
/// integer conditions are verified under the caller's meter on every use.
/// Every successful output is replayed through [`verify_certificates`].
/// `None` means no proof was produced, NEVER that the input is composite.
/// Caller resource exhaustion is an error, not a failed or accepted proof.
pub fn prime_certificate(n: &BigUint, meter: &mut Meter) -> Result<Option<Vec<PrimeCertificate>>> {
    let bits = usize::try_from(n.bits()).map_err(|_| overflow("prime proof width"))?;
    meter.bits(bits, "prime proof width")?;
    meter.charge(1, "prime proof lookup")?;
    if n.bits() > 82 {
        static PUBLIC_PROOFS: OnceLock<Result<Vec<PrimeCertificate>>> = OnceLock::new();
        let proofs = PUBLIC_PROOFS
            .get_or_init(|| {
                serde_json::from_str(include_str!("../examples/eccp131-prime-proofs.json"))
                    .map_err(|_| crate::integrity("bundled public prime proofs"))
            })
            .as_ref()
            .map_err(Clone::clone)?;
        let value = n.to_string();
        if proofs.iter().any(|proof| proof.value == value) {
            let verified = verify_certificates(proofs, meter)?;
            if !verified.contains(n) {
                return Err(crate::integrity("bundled prime proof omitted its root"));
            }
            return Ok(Some(proofs.clone()));
        }
    }
    let mut search = ProofSearch {
        rho_left: 16_384,
        known: BTreeSet::new(),
        nodes: vec![],
    };
    if !search.prove(n, 0, meter)? {
        return Ok(None);
    }
    if search.nodes.is_empty() {
        meter.vector(1, "generated prime proofs")?;
        search.nodes.push(PrimeCertificate {
            value: n.to_string(),
            witness: "2".into(),
            factors: vec![],
        });
    }
    let verified = verify_certificates(&search.nodes, meter)?;
    if !verified.contains(n) {
        return Err(crate::integrity("generated prime proof omitted its root"));
    }
    Ok(Some(search.nodes))
}

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
        if proof.factors.is_empty() {
            if bounded_primality(&n, meter)? != Some(true) {
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

    #[test]
    fn published_bound_is_strict_and_the_65bit_cliff_is_removed() {
        let mut meter = Meter::new(Limits {
            steps: 50_000,
            ..Limits::default()
        });
        let prime = BigUint::from(u64::MAX) + 14u8;
        assert!(crate::arithmetic::is_prime(&prime, &mut meter).unwrap());
        // This is the smallest composite passing all thirteen witnesses.
        // In particular it must never be accepted as a bounded proof leaf.
        let boundary = BigUint::from(BOUNDED_LIMIT);
        assert_eq!(bounded_primality(&boundary, &mut meter).unwrap(), None);
        let forged_leaf = PrimeCertificate {
            value: boundary.to_string(),
            witness: "2".into(),
            factors: vec![],
        };
        assert!(matches!(
            verify_certificates(&[forged_leaf], &mut meter),
            Err(Error::Invalid(_))
        ));
        // The first twelve bases' pseudoprime is rejected by the thirteenth.
        assert_eq!(
            bounded_primality(
                &BigUint::from(318_665_857_834_031_151_167_461u128),
                &mut meter
            )
            .unwrap(),
            Some(false)
        );
    }

    #[test]
    fn automatic_proofs_replay_for_large_known_primes() {
        for exponent in [89usize, 107, 127] {
            let n = (BigUint::one() << exponent) - BigUint::one();
            let mut meter = Meter::new(Limits {
                steps: 2_000_000,
                ..Limits::default()
            });
            let nodes = prime_certificate(&n, &mut meter)
                .unwrap()
                .unwrap_or_else(|| {
                    panic!(
                        "bounded proof for exponent {exponent}, charged {}",
                        meter.used
                    )
                });
            assert!(verify_certificates(&nodes, &mut meter)
                .unwrap()
                .contains(&n));
            assert!(crate::arithmetic::is_prime(&n, &mut meter).unwrap());
            let mut forged = nodes;
            forged.last_mut().unwrap().witness = "1".into();
            assert!(matches!(
                verify_certificates(&forged, &mut meter),
                Err(Error::Invalid(_))
            ));
        }
    }

    #[test]
    fn large_composites_are_rejected_and_missing_proofs_remain_unknown() {
        let mut meter = Meter::new(Limits::default());
        for n in [
            BigUint::zero(),
            BigUint::one(),
            BigUint::one() << 131usize,
            ((BigUint::one() << 127usize) - BigUint::one()) * 101u8,
            BigUint::from(BOUNDED_LIMIT),
        ] {
            assert!(prime_certificate(&n, &mut meter).unwrap().is_none());
        }
        let n = BigUint::parse_bytes(b"1550031797834347859219047037805205710577", 10).unwrap();
        let mut search = ProofSearch {
            rho_left: 0,
            known: BTreeSet::new(),
            nodes: vec![],
        };
        // A known prime whose n-1 needs more factoring than trial division.
        // A failed bounded attempt must not be interpreted as composite.
        assert!(!search.prove(&n, 0, &mut meter).unwrap());
        let mut depth_limited = ProofSearch {
            rho_left: 16_384,
            known: BTreeSet::new(),
            nodes: vec![],
        };
        assert!(!depth_limited.prove(&n, 32, &mut meter).unwrap());
    }

    #[test]
    fn automatic_proofs_enforce_caller_limits() {
        let n = (BigUint::one() << 89usize) - BigUint::one();
        for limits in [
            Limits {
                steps: 0,
                ..Limits::default()
            },
            Limits {
                bits: 64,
                ..Limits::default()
            },
            Limits {
                vector: 0,
                ..Limits::default()
            },
        ] {
            assert!(matches!(
                prime_certificate(&n, &mut Meter::new(limits)),
                Err(Error::Limit(_))
            ));
        }
    }

    #[test]
    fn parsed_public_proofs_never_bypass_a_new_callers_limits() {
        let n = BigUint::parse_bytes(b"1550031797834347859248576414813139942411", 10).unwrap();
        assert!(prime_certificate(&n, &mut Meter::new(Limits::default()))
            .unwrap()
            .is_some());
        for limits in [
            Limits {
                steps: 0,
                ..Limits::default()
            },
            Limits {
                bits: 64,
                ..Limits::default()
            },
            Limits {
                vector: 0,
                ..Limits::default()
            },
        ] {
            assert!(matches!(
                prime_certificate(&n, &mut Meter::new(limits)),
                Err(Error::Limit(_))
            ));
        }
    }

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
        // The ordinary constructor now finds and checks the bundled proofs
        // even when the caller supplies no certificate nodes.
        let mut incomplete = nodes;
        incomplete.clear();
        let mut meter = Meter::new(Limits {
            steps: 2_000_000,
            bits: 4096,
            vector: 200_000,
        });
        let automatic = crate::curve::Curve::with_cofactor_and_certificates(
            n("p"),
            n("a"),
            n("b"),
            n("r"),
            n("cofactor"),
            point("generator"),
            &incomplete,
            &mut meter,
        )
        .unwrap();
        assert!(automatic.in_subgroup(&point("target"), &mut meter).unwrap());
    }
}
