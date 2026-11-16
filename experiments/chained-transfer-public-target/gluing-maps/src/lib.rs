//! Fresh actual gluing maps under prospective protocol626d84.
#![allow(dead_code, static_mut_refs)]
pub mod adapter;
pub mod norm;
pub use adapter::{Adapter, EncodedPoint, Point, QuarticPoint};
pub use norm::NormNew;
#[cfg(test)]
mod tests;
