//! Fresh actual gluing maps under prospective protocol56fbbb.
#![allow(dead_code, static_mut_refs)]
pub mod adapter;
pub mod chain;
pub mod norm;
pub use adapter::{Adapter, EncodedPoint, Point, QuarticPoint};
pub use chain::Chain;
pub use norm::NormNew;
#[cfg(test)]
mod tests;
