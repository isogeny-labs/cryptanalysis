//! ChaCha (Bernstein 2008; RFC 8439 round function) as [`Primitive`]s.
//!
//! The primitive is the *block function*: the 16-word input state (constants,
//! key, counter, nonce) is the **block**, there is no separate key
//! ([`KeySchedule::Independent`] with zero round keys, `key_bits = 0`), the
//! rounds are single ChaCha rounds (round `i`, 0-based, is the column round
//! if `i` is even and the diagonal round if odd; a "double round" is two
//! entries) and the output is the working state plus the input state, word
//! by word ([`FeedForward::AddWords`]). `eval_rounds(p, &[], state, n)` is
//! therefore ChaCha with `n` rounds, e.g. `n = 7` for the 7-round attack
//! target. Words are little-endian, word `j` is state bits
//! `j*w .. (j+1)*w`.
//!
//! # Reduced-width convention
//!
//! [`reduced_width`] keeps the 16-word / four-quarter-round structure and
//! shrinks the word to `w in {8, 16, 32}` bits. This crate's convention
//! (the rest of the literature varies, so nothing here claims to equal any
//! published small variant):
//!
//! * rotation distances `(16, 12, 8, 7)` become `floor(r * w / 32)`, giving
//!   `(8, 6, 4, 3)` for `w = 16` and `(4, 3, 2, 1)` for `w = 8`;
//! * the four constant words are the low `w` bits of the standard 32-bit
//!   constants (see [`constants`]);
//! * addition is modulo `2^w`; the round order is unchanged.

use super::round;
use crate::cryptanalysis::sym_ir::{
    ArxOp, Codec, FeedForward, KeySchedule, Kind, Layer, Primitive,
};
use crate::symmetric::chacha20::SIGMA;

/// Quarter round on registers `a, b, c, d` with rotation distances `rot`.
fn quarter_round(ops: &mut Vec<ArxOp>, [a, b, c, d]: [usize; 4], rot: [usize; 4]) {
    ops.push(ArxOp::Add { dst: a, a, b });
    ops.push(ArxOp::Xor { dst: d, a: d, b: a });
    ops.push(ArxOp::Rotl {
        dst: d,
        src: d,
        k: rot[0],
    });
    ops.push(ArxOp::Add { dst: c, a: c, b: d });
    ops.push(ArxOp::Xor { dst: b, a: b, b: c });
    ops.push(ArxOp::Rotl {
        dst: b,
        src: b,
        k: rot[1],
    });
    ops.push(ArxOp::Add { dst: a, a, b });
    ops.push(ArxOp::Xor { dst: d, a: d, b: a });
    ops.push(ArxOp::Rotl {
        dst: d,
        src: d,
        k: rot[2],
    });
    ops.push(ArxOp::Add { dst: c, a: c, b: d });
    ops.push(ArxOp::Xor { dst: b, a: b, b: c });
    ops.push(ArxOp::Rotl {
        dst: b,
        src: b,
        k: rot[3],
    });
}

fn build(name: String, w: usize, rounds: usize, rot: [usize; 4]) -> Primitive {
    assert!(rounds >= 1);
    let cols = [[0, 4, 8, 12], [1, 5, 9, 13], [2, 6, 10, 14], [3, 7, 11, 15]];
    let diag = [[0, 5, 10, 15], [1, 6, 11, 12], [2, 7, 8, 13], [3, 4, 9, 14]];
    let rs = (0..rounds)
        .map(|i| {
            let mut ops = Vec::new();
            for q in if i.is_multiple_of(2) { cols } else { diag } {
                quarter_round(&mut ops, q, rot);
            }
            round(vec![Layer::Arx { word_bits: w, ops }])
        })
        .collect();
    Primitive {
        name,
        block_bits: 16 * w,
        key_bits: 0,
        scratch_bits: 0,
        block_codec: Codec::little(w),
        key_codec: Codec::little(w),
        sboxes: vec![],
        rounds: rs,
        key_schedule: KeySchedule::Independent {
            round_keys: 0,
            round_key_bits: 0,
        },
        feed_forward: FeedForward::AddWords { word_bits: w },
        kind: Kind::Permutation,
    }
}

/// ChaCha with 32-bit words and the given number of single rounds.
pub fn chacha(rounds: usize) -> Primitive {
    build(format!("ChaCha{rounds}"), 32, rounds, [16, 12, 8, 7])
}

/// ChaCha20 block function (20 rounds), matching
/// `symmetric::chacha20::chacha20_block`.
pub fn chacha20() -> Primitive {
    chacha(20)
}

/// ChaCha12 block function (`symmetric::chacha20::chacha12_block`).
pub fn chacha12() -> Primitive {
    chacha(12)
}

/// ChaCha8 block function (`symmetric::chacha20::chacha8_block`).
pub fn chacha8() -> Primitive {
    chacha(8)
}

/// Scaled rotation distances for width `w` (see the module docs).
pub fn reduced_rotations(word_bits: usize) -> [usize; 4] {
    [16, 12, 8, 7].map(|r| r * word_bits / 32)
}

/// ChaCha on `word_bits`-bit words (`8`, `16` or `32`) with `rounds` single
/// rounds, under this crate's reduced-width convention (module docs).
pub fn reduced_width(word_bits: usize, rounds: usize) -> Primitive {
    assert!(
        matches!(word_bits, 8 | 16 | 32),
        "word_bits must be 8, 16 or 32"
    );
    build(
        format!("ChaCha{rounds}-w{word_bits}"),
        word_bits,
        rounds,
        reduced_rotations(word_bits),
    )
}

/// The four constant words for the given width: the low `word_bits` bits of
/// the standard `"expand 32-byte k"` words.
pub fn constants(word_bits: usize) -> [u64; 4] {
    SIGMA.map(|c| (c as u64) & ((1u64 << word_bits) - 1))
}

/// Assemble a block (input state) for [`reduced_width`] / [`chacha`]:
/// constants, then `key` (8 words), then `counter_nonce` (4 words), each
/// word truncated to `word_bits` bits and written little-endian.
pub fn input_block(word_bits: usize, key: &[u64; 8], counter_nonce: &[u64; 4]) -> Vec<u8> {
    let nb = word_bits / 8;
    let mask = if word_bits == 64 {
        u64::MAX
    } else {
        (1u64 << word_bits) - 1
    };
    constants(word_bits)
        .iter()
        .chain(key.iter())
        .chain(counter_nonce.iter())
        .flat_map(|&v| (v & mask).to_le_bytes()[..nb].to_vec())
        .collect()
}
