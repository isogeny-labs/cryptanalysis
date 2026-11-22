//! Structural descriptions of concrete primitives, written once each.
//!
//! Every constructor returns a [`Primitive`](super::Primitive) that
//! [`eval`](super::eval) can run; the regression tests in
//! `sym_ir/tests.rs` compare each against the existing implementation.
//! Reduced-round and reduced-width variants are constructors on the same
//! description, not separate code.

pub mod aes128;
pub mod chacha;
pub mod present80;
pub mod sha256_compress;
pub mod simon;
pub mod speck;
pub mod toyspn;

use super::{Layer, Round};
use crate::cryptanalysis::sbox::Sbox;

/// Build an `bits`-in / `bits`-out S-box from a byte-valued table.
pub(crate) fn sbox_from_u8(bits: u32, table: &[u8]) -> Sbox {
    Sbox::new(bits, bits, table.iter().map(|&v| v as u32).collect())
        .expect("sym_ir: invalid S-box table")
}

/// A round made of the given layers.
pub(crate) fn round(layers: Vec<Layer>) -> Round {
    Round { layers }
}
