//! Adaptor that exposes any IR-described Merkle-Damgard compression function
//! to the generic attacks of `cryptanalysis::hash_attacks`
//! ([`length_extension_attack`](crate::cryptanalysis::hash_attacks::length_extension_attack),
//! [`joux_multicollision`](crate::cryptanalysis::hash_attacks::joux_multicollision),
//! [`birthday_collision_search`](crate::cryptanalysis::hash_attacks::birthday_collision_search)).
//!
//! [`IrMdHash`] wraps a [`Primitive`] in the convention used by the hash
//! descriptions in `sym_ir::primitives` (the *block* is the chaining value,
//! the *key* is the message block, the feed-forward is part of the
//! description) together with an initial value and a length-padding rule, and
//! implements [`HashFunction`] and [`MerkleDamgardHash`] by calling
//! [`eval`]. The existing hand-written impls in `hash_attacks.rs` are not
//! touched; the tests there check that this adaptor reproduces their digests
//! and that the attacks give the same results on both.

use crate::cryptanalysis::hash_attacks::{HashFunction, MerkleDamgardHash};
use crate::cryptanalysis::md5_differential::MD5_IV;
use crate::cryptanalysis::sym_ir::primitives::{md5_compress, sha256_compress, sha512_compress};
use crate::cryptanalysis::sym_ir::{eval, Primitive};
use crate::hash::sha256::H0;

/// Length-encoding trailer of Merkle-Damgard strengthening.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum LengthPadding {
    /// `0x80`, zeros, 64-bit big-endian bit length (SHA-1, SHA-256).
    Be64,
    /// `0x80`, zeros, 128-bit big-endian bit length (SHA-512).
    Be128,
    /// `0x80`, zeros, 64-bit little-endian bit length (MD4, MD5).
    Le64,
}

/// A Merkle-Damgard hash defined by an IR compression function.
pub struct IrMdHash {
    name: &'static str,
    prim: Primitive,
    iv: Vec<u8>,
    padding: LengthPadding,
}

impl IrMdHash {
    /// Wrap `prim` (block = chaining value, key = message block) with
    /// initial value `iv`; the digest is the whole chaining value.
    pub fn new(name: &'static str, prim: Primitive, iv: Vec<u8>, padding: LengthPadding) -> Self {
        assert_eq!(iv.len(), prim.block_bytes());
        IrMdHash {
            name,
            prim,
            iv,
            padding,
        }
    }

    /// SHA-256 from `sha256_compress::sha256_compress`.
    pub fn sha256() -> Self {
        Self::new(
            "SHA-256 (IR)",
            sha256_compress::sha256_compress(),
            H0.iter().flat_map(|w| w.to_be_bytes()).collect(),
            LengthPadding::Be64,
        )
    }

    /// SHA-512 from `sha512_compress::sha512_compress`.
    pub fn sha512() -> Self {
        let iv: [u64; 8] = [
            0x6a09e667f3bcc908,
            0xbb67ae8584caa73b,
            0x3c6ef372fe94f82b,
            0xa54ff53a5f1d36f1,
            0x510e527fade682d1,
            0x9b05688c2b3e6c1f,
            0x1f83d9abfb41bd6b,
            0x5be0cd19137e2179,
        ];
        Self::new(
            "SHA-512 (IR)",
            sha512_compress::sha512_compress(),
            iv.iter().flat_map(|w| w.to_be_bytes()).collect(),
            LengthPadding::Be128,
        )
    }

    /// MD5 from `md5_compress::md5_compress`.
    pub fn md5() -> Self {
        Self::new(
            "MD5 (IR)",
            md5_compress::md5_compress(),
            MD5_IV.iter().flat_map(|w| w.to_le_bytes()).collect(),
            LengthPadding::Le64,
        )
    }

    /// The same hash with a reduced-step compression function (any IR
    /// primitive of the right shape), keeping `iv` and padding.
    pub fn with_primitive(&self, name: &'static str, prim: Primitive) -> Self {
        Self::new(name, prim, self.iv.clone(), self.padding)
    }

    fn pad_bytes(&self, message_bytes: usize) -> Vec<u8> {
        let bb = self.prim.key_bytes();
        let len_bytes = match self.padding {
            LengthPadding::Be128 => 16,
            _ => 8,
        };
        let mut out = vec![0x80u8];
        while (message_bytes + out.len()) % bb != bb - len_bytes {
            out.push(0);
        }
        let bits = (message_bytes as u128).wrapping_mul(8);
        match self.padding {
            LengthPadding::Be64 => out.extend_from_slice(&(bits as u64).to_be_bytes()),
            LengthPadding::Be128 => out.extend_from_slice(&bits.to_be_bytes()),
            LengthPadding::Le64 => out.extend_from_slice(&(bits as u64).to_le_bytes()),
        }
        out
    }
}

impl HashFunction for IrMdHash {
    fn name(&self) -> &'static str {
        self.name
    }
    fn output_bytes(&self) -> usize {
        self.prim.block_bytes()
    }
    fn block_bytes(&self) -> usize {
        self.prim.key_bytes()
    }
    fn hash(&self, message: &[u8]) -> Vec<u8> {
        let mut padded = message.to_vec();
        padded.extend_from_slice(&self.pad_bytes(message.len()));
        let mut state = self.iv.clone();
        for chunk in padded.chunks_exact(self.block_bytes()) {
            self.compress(&mut state, chunk);
        }
        state
    }
}

impl MerkleDamgardHash for IrMdHash {
    fn compress(&self, state: &mut [u8], block: &[u8]) {
        let out = eval(&self.prim, block, state);
        state.copy_from_slice(&out);
    }
    fn padding_for_length(&self, message_bytes: usize) -> Vec<u8> {
        self.pad_bytes(message_bytes)
    }
}
