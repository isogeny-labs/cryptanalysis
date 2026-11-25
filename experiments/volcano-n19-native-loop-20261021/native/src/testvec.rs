//! Vectors taken from the CPython interpreter (3.12 and 3.13 agree), for the crate tests.
#![cfg(test)]
pub const GEN_E0_BITS32: [u64; 3] = [2712684464, 387638923, 2379344152];
pub const TAU6_0_RANDRANGE: [u64; 3] = [47126, 116442, 17349];
pub const TAU6_0_SHUFFLE19: [u32; 19] = [17, 6, 15, 13, 2, 9, 0, 7, 18, 5, 8, 14, 12, 16, 3, 1, 10, 4, 11];
/// volcano-ic/rho-arm-20261014: protocol.json scalars[0] and arms.tau6.rng_seed % 0, and
/// results/arms.jsonl tau6 instance 0 (run 38520305068, Sage): targets, gb_calls, spurious,
/// relations, log.
pub const ARCH0_SCALAR: u64 = 2003;
pub const ARCH0_SEED: &str = "tau:tau6:0";
pub const ARCH0_COUNTS: (u64, u64, u64, u64, Option<u64>) = (251, 4367, 2, 39, Some(2003));
