//! Bounded elliptic-curve index calculus over Mersenne prime fields.
//!
//! The auxiliary curve supplies a low-degree rational-map encoding of the
//! factor base. Its group order does not replace the target curve's order.
//! Candidate zeros are checked by target-curve addition before becoming rows.
//! This is research code for small instances, not a cryptographic primitive.
#![doc = include_str!("../README.md")]
#![deny(missing_docs)]

mod circuit;
mod field;
mod graph;
mod kernel;
mod solve;

pub use circuit::{
    AuxiliaryMap, Backend, CandidateWorkspace, FactorBase, FactorBaseEncoding, RandomBaseStats,
    SignedRelation,
};
pub use field::{BatchScratch, Curve, Point};
pub use solve::{
    solve, verify_certificate, Certificate, Config, PreparedSolver, Relation, SearchStats,
    SolveOutcome, StopReason,
};

/// Invalid parameters, unsupported execution, or a rejected certificate.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Error {
    /// An input fails a mathematical or resource precondition.
    Invalid(&'static str),
    /// The requested SIMD backend is unavailable on this build or machine.
    UnsupportedBackend,
    /// A configured memory or proof-arena budget was reached.
    ResourceLimit(&'static str),
    /// A public relation or recovery certificate fails replay.
    InvalidCertificate(&'static str),
}

impl std::fmt::Display for Error {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Invalid(message) => write!(f, "invalid auxiliary IC input: {message}"),
            Self::UnsupportedBackend => write!(f, "requested auxiliary IC backend is unavailable"),
            Self::ResourceLimit(message) => write!(f, "auxiliary IC resource limit: {message}"),
            Self::InvalidCertificate(message) => {
                write!(f, "invalid auxiliary IC certificate: {message}")
            }
        }
    }
}

impl std::error::Error for Error {}

/// Result of a checked public API operation.
pub type Result<T> = std::result::Result<T, Error>;
