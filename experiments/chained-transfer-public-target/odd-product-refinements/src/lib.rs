//! Additive refinements under prospective579e08, published c37ad390 before code.
#![allow(dead_code, static_mut_refs)]
pub mod fast_source;
pub use fast_source::FastSourceChain;
#[cfg(test)]
mod kernels;
#[cfg(test)]
mod tests;
