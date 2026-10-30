//! Exact tensor machinery for the conditional hashed-factor-base ECDL algorithm.
//!
//! Encodings follow Bochum v0.2, sections 2 and 3, commit
//! `1ee44e562b1b9a50ea339f3b8f81112b5a24b96f`. Recursive contraction follows
//! OpenAI's October 25 manuscript, Appendix D, commit
//! `7ef5c0cc5ca4b0e072b7a050fca09ab24bc6fa3a`.
//! The asymptotic theorem is conditional on that source. It gives no practical
//! speedup for deployed curves. Work limits always return an error, never an
//! incorrect zero count or a false nonexistence certificate.

#![deny(missing_docs)]

#[macro_use]
mod serialization;

pub mod arithmetic;
pub mod binary;
pub mod contraction;
pub mod curve;
pub mod encoding;
pub mod factoring;
pub mod finite;
pub mod network;
pub mod partial;
pub mod primality;
pub mod reduction;
pub mod ring;
pub mod weighted;
pub mod width;

pub use num_bigint::{BigInt, BigUint};

/// Invalid input, exhausted resources, or a failed internal consistency check.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Error {
    /// A stated precondition is false.
    Invalid(String),
    /// A caller's explicit bound was exhausted. The mathematical result is unknown.
    Limit(String),
    /// Arithmetic or a certificate failed an exact consistency check.
    Integrity(String),
}

impl std::fmt::Display for Error {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Invalid(s) => write!(f, "invalid input: {s}"),
            Self::Limit(s) => write!(f, "resource limit: {s}"),
            Self::Integrity(s) => write!(f, "verification failed: {s}"),
        }
    }
}
impl std::error::Error for Error {}

/// Fallible exact computation.
pub type Result<T> = std::result::Result<T, Error>;

/// Explicit development/resource limits, independent of mathematical assumptions.
#[derive(Clone, Debug)]
pub struct Limits {
    /// Maximum charged primitive steps across a whole operation.
    pub steps: u64,
    /// Maximum length of one allocated vector, including graph edges.
    pub vector: usize,
    /// Maximum coefficient precision or integer word width in bits.
    pub bits: usize,
}
impl Default for Limits {
    fn default() -> Self {
        Self {
            steps: 100_000_000,
            vector: 2_000_000,
            bits: 1_000_000,
        }
    }
}

/// Shared work meter. Counts are diagnostics, not calibrated benchmark units.
#[derive(Clone, Debug)]
pub struct Meter {
    /// The bounds governing this operation.
    pub limits: Limits,
    /// Primitive steps charged so far.
    pub used: u64,
}
impl Meter {
    /// Start an operation with explicit bounds.
    pub fn new(limits: Limits) -> Self {
        Self { limits, used: 0 }
    }
    /// Charge before doing work; limits never wrap or become successful results.
    pub fn charge(&mut self, n: u64, phase: &str) -> Result<()> {
        self.used = self
            .used
            .checked_add(n)
            .ok_or_else(|| Error::Limit(phase.into()))?;
        if self.used > self.limits.steps {
            return Err(Error::Limit(phase.into()));
        }
        Ok(())
    }
    /// Check a vector length before allocating it.
    pub fn vector(&self, n: usize, phase: &str) -> Result<()> {
        if n > self.limits.vector {
            return Err(Error::Limit(phase.into()));
        }
        Ok(())
    }
    /// Check an arithmetic width before allocating it.
    pub fn bits(&self, n: usize, phase: &str) -> Result<()> {
        if n > self.limits.bits {
            return Err(Error::Limit(phase.into()));
        }
        Ok(())
    }
}

pub(crate) fn invalid(s: &str) -> Error {
    Error::Invalid(s.into())
}
pub(crate) fn integrity(s: &str) -> Error {
    Error::Integrity(s.into())
}
pub(crate) fn overflow(s: &str) -> Error {
    Error::Limit(format!("{s}: machine index overflow"))
}
