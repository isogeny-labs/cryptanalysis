//! Deterministic primality evidence for the checked prime-field backends.
//!
//! One-word inputs retain the repository's deterministic `u64` test. Wider
//! inputs are accepted only below the strict Sorenson--Webster `psi_13`
//! bound after strong Miller--Rabin tests to the first thirteen prime bases.
//! We execute the first sixteen prime bases through 53, so the proof premise
//! is a subset of the recorded tests. All-passing values at or above the
//! exclusive bound are unsupported unless a separate primality certificate
//! is introduced; a strong-MR witness still establishes compositeness there.

use super::fp2::is_prime_u64;
use num_bigint::BigUint;
use num_traits::{One, Zero};
use serde::Serialize;
use std::cell::RefCell;

/// Sorenson--Webster's exclusive upper bound for the first thirteen prime
/// strong Miller--Rabin bases.
pub const PSI13_EXCLUSIVE_BOUND_DECIMAL: &str = "3317044064679887385961981";

/// The first thirteen bases through 41 prove primality below `psi_13`; the
/// final three bases are retained as additional deterministic controls.
pub const PRIME_BASES_THROUGH_53: [u64; 16] =
    [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53];

/// Complete deterministic Miller--Rabin witness set used by the word-sized
/// backend.
pub const DETERMINISTIC_U64_BASES: [u64; 7] =
    [2, 325, 9_375, 28_178, 450_775, 9_780_504, 1_795_265_022];
pub const U64_EXCLUSIVE_BOUND_DECIMAL: &str = "18446744073709551616";

pub const PSI13_THEOREM_REFERENCE: &str = "Sorenson-Webster-2015-Theorem-1.1-psi13-exclusive-bound";

/// Outcome of the bounded deterministic primality gate.
#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum PrimeProofStatus {
    /// Deterministic one-word primality test succeeded.
    ProvedU64,
    /// The strict `psi_13` theorem and recorded strong-MR bases prove prime.
    ProvedPsi13,
    /// A deterministic test produced a compositeness witness.
    Composite,
    /// No compositeness witness was found, but the theorem's proof range does
    /// not cover the value.
    UnsupportedWithoutPrimalityCertificate,
}

/// Serializable description of the exact proof gate applied to one value.
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct PrimeProofEvidence {
    pub value_decimal: String,
    pub status: PrimeProofStatus,
    pub method: &'static str,
    pub theorem_reference: &'static str,
    pub configured_bases: &'static [u64],
    pub exclusive_upper_bound_decimal: &'static str,
}

fn classify_uncached(n: &BigUint) -> PrimeProofStatus {
    if n.bits() <= u64::BITS as u64 {
        let word = n.to_u64_digits().first().copied().unwrap_or(0);
        return if is_prime_u64(word) {
            PrimeProofStatus::ProvedU64
        } else {
            PrimeProofStatus::Composite
        };
    }

    // These divisions give unconditional composite results even outside the
    // theorem range. They also handle even inputs before n-1 is decomposed.
    for base in PRIME_BASES_THROUGH_53 {
        let base = BigUint::from(base);
        if n == &base {
            return PrimeProofStatus::ProvedU64;
        }
        if (n % &base).is_zero() {
            return PrimeProofStatus::Composite;
        }
    }

    let one = BigUint::one();
    let n_minus_one = n - &one;
    let mut odd_part = n_minus_one.clone();
    let mut twos = 0u32;
    while !odd_part.bit(0) {
        odd_part >>= 1usize;
        twos += 1;
    }

    for base in PRIME_BASES_THROUGH_53 {
        let base = BigUint::from(base);
        if &base >= n {
            continue;
        }
        let mut residue = base.modpow(&odd_part, n);
        if residue == one || residue == n_minus_one {
            continue;
        }
        let mut passed = false;
        for _ in 1..twos {
            residue = (&residue * &residue) % n;
            if residue == n_minus_one {
                passed = true;
                break;
            }
        }
        if !passed {
            return PrimeProofStatus::Composite;
        }
    }
    let bound = BigUint::parse_bytes(PSI13_EXCLUSIVE_BOUND_DECIMAL.as_bytes(), 10)
        .expect("static psi13 proof bound");
    if n < &bound {
        PrimeProofStatus::ProvedPsi13
    } else {
        PrimeProofStatus::UnsupportedWithoutPrimalityCertificate
    }
}

/// Return the deterministic proof status, caching the most recent wide
/// modulus per thread because checked divisor operations revalidate curves.
pub fn prime_proof_status(n: &BigUint) -> PrimeProofStatus {
    if n.bits() <= u64::BITS as u64 {
        return classify_uncached(n);
    }
    thread_local! {
        static CACHE: RefCell<Option<(Vec<u32>, PrimeProofStatus)>> = const { RefCell::new(None) };
    }
    let key = n.to_u32_digits();
    CACHE.with(|cache| {
        if let Some((cached, status)) = cache.borrow().as_ref() {
            if cached == &key {
                return *status;
            }
        }
        let status = classify_uncached(n);
        *cache.borrow_mut() = Some((key, status));
        status
    })
}

/// Produce an exact, serializable receipt for the bounded proof decision.
pub fn prime_proof_evidence(n: &BigUint) -> PrimeProofEvidence {
    let status = prime_proof_status(n);
    let word_sized = n.bits() <= u64::BITS as u64;
    let (method, theorem_reference, configured_bases, exclusive_upper_bound_decimal) = if word_sized
    {
        (
            "deterministic_u64",
            "deterministic-Miller-Rabin-complete-u64-seven-witness-set",
            DETERMINISTIC_U64_BASES.as_slice(),
            U64_EXCLUSIVE_BOUND_DECIMAL,
        )
    } else {
        (
            match status {
                PrimeProofStatus::ProvedPsi13 => "strong_miller_rabin_first_16_prime_bases",
                PrimeProofStatus::Composite => "deterministic_compositeness_witness",
                PrimeProofStatus::UnsupportedWithoutPrimalityCertificate => {
                    "outside_strict_psi13_proof_range"
                }
                PrimeProofStatus::ProvedU64 => unreachable!("wide input cannot be proved_u64"),
            },
            PSI13_THEOREM_REFERENCE,
            PRIME_BASES_THROUGH_53.as_slice(),
            PSI13_EXCLUSIVE_BOUND_DECIMAL,
        )
    };
    PrimeProofEvidence {
        value_decimal: n.to_str_radix(10),
        status,
        method,
        theorem_reference,
        configured_bases,
        exclusive_upper_bound_decimal,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn decimal(value: &str) -> BigUint {
        BigUint::parse_bytes(value.as_bytes(), 10).unwrap()
    }

    #[test]
    fn strict_psi13_gate_distinguishes_proof_composite_and_boundary() {
        assert_eq!(
            prime_proof_status(&BigUint::from(59u32)),
            PrimeProofStatus::ProvedU64
        );
        assert_eq!(
            prime_proof_status(&BigUint::from(15u32)),
            PrimeProofStatus::Composite
        );

        let pilot_prime = decimal("5902977611310272157103");
        assert_eq!(
            prime_proof_status(&pilot_prime),
            PrimeProofStatus::ProvedPsi13
        );
        assert_eq!(
            prime_proof_evidence(&pilot_prime).configured_bases,
            &PRIME_BASES_THROUGH_53
        );
        let receipt = serde_json::to_value(prime_proof_evidence(&pilot_prime)).unwrap();
        assert_eq!(receipt["status"], "proved_psi13");
        assert_eq!(receipt["configured_bases"][12], 41);
        assert_eq!(
            receipt["exclusive_upper_bound_decimal"],
            PSI13_EXCLUSIVE_BOUND_DECIMAL
        );

        // psi_12 is a strong pseudoprime to the first twelve prime bases and
        // is rejected by base 41, which the psi_13 premise requires.
        assert_eq!(
            prime_proof_status(&decimal("318665857834031151167461")),
            PrimeProofStatus::Composite
        );
        assert_eq!(
            prime_proof_status(&decimal(PSI13_EXCLUSIVE_BOUND_DECIMAL)),
            PrimeProofStatus::Composite
        );
        assert_eq!(
            prime_proof_status(&decimal("3317044064679887385962123")),
            PrimeProofStatus::UnsupportedWithoutPrimalityCertificate
        );
    }
}
