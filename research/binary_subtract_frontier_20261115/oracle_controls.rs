//! Audit facade: tests the actual production library and canonical controls.
#[cfg(test)]
pub use frontier_core::{binary_ecc, cryptanalysis};

#[cfg(test)]
#[path = "../../suite/src/cryptanalysis/ic_framework/binary_subtract_tests.rs"]
mod production_controls;
