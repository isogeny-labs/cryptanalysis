//! Additive q223 completed maps; original V1 admission and original N4 stay fixed.
#![allow(dead_code, static_mut_refs)]
pub mod adapter;
pub use adapter::{AdapterV2, EncodedPoint, Point, QuarticPoint};
pub mod norm;
pub use norm::NormV2;

#[cfg(test)]
mod tests;
