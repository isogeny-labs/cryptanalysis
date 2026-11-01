//! Divisor-prefix counting and search from Hexagon 2610.00600v1, section 4.
//!
//! The multiplication encoding has one extension per pair `(d,e)`. Constraining
//! `d*e=N` and `d>1` therefore counts divisors, including `N`, without counting
//! auxiliary arithmetic witnesses more than once. Prefixes are MSB first with
//! leading zeros to the bit length of `N`.
//!
//! This uses this crate's existing exact counter (OpenAI Appendix D), not the
//! Anthropic engine formalized by the Hexagon authors. Correctness tests do not
//! establish their asymptotic bound for this implementation. Finite-size leaves
//! can enumerate exponentially many assignments; limits return `Error::Limit`.

use crate::contraction::Counter;
use crate::encoding::Encoder;
use crate::network::Network;
use crate::{integrity, invalid, overflow, BigUint, Meter, Result};
use num_traits::{One, Zero};

/// Exact multiplication network for the nontrivial positive divisors of `N`.
pub struct DivisorNetwork {
    /// Built-in parsimonious Boolean network. The interface is `d`, LSB first.
    pub network: Network,
    /// Fixed divisor encoding width, equal to the bit length of `N`.
    pub width: usize,
}

impl DivisorNetwork {
    /// Encode `d*e=N`, `d>1`, using the compact Fourier multiplication gadget.
    pub fn new(n: &BigUint, meter: &Meter) -> Result<Self> {
        if n < &BigUint::from(2u8) {
            return Err(invalid("divisor network requires N >= 2"));
        }
        let width = usize::try_from(n.bits()).map_err(|_| overflow("factor width"))?;
        let product_width = width
            .checked_mul(2)
            .ok_or_else(|| overflow("factor product"))?;
        meter.bits(product_width, "factor product width")?;
        let mut encoder = Encoder::new();
        let d = encoder.input_word(width, meter)?;
        let e = encoder.input_word(width, meter)?;
        let one = Encoder::constant(width, &BigUint::one())?;
        let nontrivial = encoder.less_than(&one, &d, meter)?;
        encoder.assert_equal(&nontrivial, &Encoder::constant(1, &BigUint::one())?, meter)?;
        let product = encoder.integer_multiply(&d, &e, meter)?;
        encoder.assert_equal(&product, &Encoder::constant(product_width, n)?, meter)?;
        encoder.mark_interface(&d, meter)?;
        Ok(Self {
            network: encoder.finish(meter)?,
            width,
        })
    }

    /// Count divisors `d>1` with the specified MSB-first, zero-padded prefix.
    /// A returned zero is exact; resource exhaustion propagates as an error.
    pub fn count_prefix(
        &self,
        prefix: &[bool],
        counter: &mut Counter,
        meter: &mut Meter,
    ) -> Result<BigUint> {
        if prefix.len() > self.width {
            return Err(invalid("divisor prefix exceeds input width"));
        }
        meter.vector(self.network.edge_count(), "divisor pins")?;
        let mut pins = vec![None; self.network.edge_count()];
        for (i, &bit) in prefix.iter().enumerate() {
            pins[self.network.interface()[self.width - 1 - i]] = Some(bit);
        }
        counter.count(&self.network, &pins, meter)
    }
}

/// Find the smallest prime factor by choosing the least feasible divisor prefix.
/// Prime inputs return themselves. Match Mathlib's `Nat.minFac` conventions:
/// zero returns two and one returns one. Complete factorization rejects zero.
pub fn smallest_prime_factor(
    n: &BigUint,
    counter: &mut Counter,
    meter: &mut Meter,
) -> Result<BigUint> {
    if n < &BigUint::from(2u8) {
        meter.charge(1, "Mathlib minFac boundary convention")?;
        meter.bits(2, "minFac boundary output")?;
        return Ok(if n.is_zero() {
            BigUint::from(2u8)
        } else {
            BigUint::one()
        });
    }
    let divisors = DivisorNetwork::new(n, meter)?;
    meter.vector(divisors.width, "factor prefix")?;
    let mut prefix = Vec::with_capacity(divisors.width);
    let mut factor = BigUint::zero();
    for _ in 0..divisors.width {
        meter.charge(1, "divisor prefix search")?;
        prefix.push(false);
        let take_one = divisors.count_prefix(&prefix, counter, meter)?.is_zero();
        *prefix
            .last_mut()
            .ok_or_else(|| integrity("empty factor prefix"))? = take_one;
        factor <<= 1usize;
        if take_one {
            factor += BigUint::one();
        }
    }
    meter.charge(1, "factor divisibility check")?;
    if factor < BigUint::from(2u8) || n % &factor != BigUint::zero() {
        return Err(integrity("divisor self-reduction returned a non-divisor"));
    }
    Ok(factor)
}

/// Complete prime factorization, with multiplicity, by repeated smallest factors.
/// One has the empty factorization. Zero is rejected. A shared meter bounds all
/// rounds together; no partial factor list is returned as a complete result.
pub fn factor_integer(
    n: &BigUint,
    counter: &mut Counter,
    meter: &mut Meter,
) -> Result<Vec<BigUint>> {
    if n.is_zero() {
        return Err(invalid("zero has no finite prime factorization"));
    }
    meter.bits(
        usize::try_from(n.bits()).map_err(|_| overflow("factor width"))?,
        "factor input",
    )?;
    let mut remaining = n.clone();
    let mut factors = Vec::new();
    while remaining > BigUint::one() {
        meter.charge(1, "factorization round")?;
        let factor = smallest_prime_factor(&remaining, counter, meter)?;
        meter.vector(
            factors
                .len()
                .checked_add(1)
                .ok_or_else(|| overflow("factor list"))?,
            "factor list",
        )?;
        remaining /= &factor;
        factors.push(factor);
    }
    Ok(factors)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Error, Limits};

    fn meter() -> Meter {
        Meter::new(Limits {
            steps: 100_000_000,
            vector: 200_000,
            bits: 200_000,
        })
    }

    #[test]
    fn tensor_divisor_counts_match_independent_trial_division_for_every_prefix() {
        for n in [2u32, 7, 9, 12] {
            let mut work = meter();
            let graph = DivisorNetwork::new(&n.into(), &work).unwrap();
            let mut counter = Counter::default();
            // Every prefix, including empty and complete, checks bit order,
            // leading zeros, exclusion of 1, and inclusion of the prime N.
            for len in 0..=graph.width {
                for value in 0..(1u32 << len) {
                    let prefix: Vec<_> = (0..len).rev().map(|i| value & (1 << i) != 0).collect();
                    let expected = (2..=n)
                        .filter(|d| n % d == 0 && d >> (graph.width - len) == value)
                        .count();
                    assert_eq!(
                        graph
                            .count_prefix(&prefix, &mut counter, &mut work)
                            .unwrap(),
                        BigUint::from(expected)
                    );
                }
            }
            assert!(graph
                .count_prefix(&vec![false; graph.width + 1], &mut counter, &mut work)
                .is_err());
        }
    }

    #[test]
    fn complete_factorization_handles_primes_powers_and_identity() {
        for (n, expected) in [
            (1u32, vec![]),
            (2, vec![2]),
            (7, vec![7]),
            (8, vec![2, 2, 2]),
            (12, vec![2, 2, 3]),
        ] {
            let got = factor_integer(&n.into(), &mut Counter::default(), &mut meter()).unwrap();
            assert_eq!(
                got,
                expected
                    .into_iter()
                    .map(|p: u32| BigUint::from(p))
                    .collect::<Vec<_>>()
            );
        }
    }

    #[test]
    fn invalid_inputs_and_exhaustion_never_become_zero_counts_or_partial_success() {
        assert!(factor_integer(&BigUint::zero(), &mut Counter::default(), &mut meter()).is_err());
        assert_eq!(
            smallest_prime_factor(&BigUint::one(), &mut Counter::default(), &mut meter()).unwrap(),
            BigUint::one()
        );
        assert_eq!(
            smallest_prime_factor(&BigUint::zero(), &mut Counter::default(), &mut meter()).unwrap(),
            BigUint::from(2u8)
        );
        let mut work = meter();
        work.limits.steps = 0;
        assert!(matches!(
            factor_integer(&12u32.into(), &mut Counter::default(), &mut work),
            Err(Error::Limit(_))
        ));
        let mut work = meter();
        work.limits.vector = 1;
        assert!(matches!(
            DivisorNetwork::new(&12u32.into(), &work),
            Err(Error::Limit(_))
        ));
    }
}
