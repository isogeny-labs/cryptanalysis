//! `ToySpn` of `cryptanalysis::boomerang` as a [`Primitive`].
//!
//! 16-bit SPN: four 4-bit S-boxes, the bit permutation `i -> 4 i mod 15`
//! (15 fixed), round keys from the 64-bit master key by
//! `k <- rotl(k, 7) + 0x9E37` (low 16 bits used). The last round has no
//! permutation. Block bytes are the 16-bit block little-endian; key bytes
//! are the 64-bit master key little-endian.

use super::round;
use crate::cryptanalysis::sbox::Sbox;
use crate::cryptanalysis::sym_ir::{
    ArxOp, Codec, FeedForward, KeySchedule, Kind, Layer, Primitive, SboxId,
};

/// ToySpn with the given 4-bit bijection-or-not S-box and round count
/// (`rounds >= 1`); matches `ToySpn::new(sbox, rounds, key)` with
/// `key.to_le_bytes()` as the IR key.
pub fn toyspn(sbox: &Sbox, rounds: usize) -> Primitive {
    assert!(rounds >= 1);
    assert_eq!(
        (sbox.n_in(), sbox.n_out()),
        (4, 4),
        "ToySpn needs a 4-bit S-box"
    );
    let mut perm = vec![0usize; 16];
    for i in 0..16 {
        let to = if i < 15 { (4 * i) % 15 } else { 15 };
        perm[to] = i;
    }
    let rs = (1..=rounds)
        .map(|r| {
            let mut l = Vec::new();
            if r == 1 {
                l.push(Layer::AddRoundKey {
                    round_key: 0,
                    bit_offset: 0,
                });
            }
            l.push(Layer::SboxParallel {
                sbox: SboxId(0),
                width_bits: 4,
                count: 4,
                bit_offset: 0,
            });
            if r < rounds {
                l.push(Layer::Permute { perm: perm.clone() });
            }
            l.push(Layer::AddRoundKey {
                round_key: r,
                bit_offset: 0,
            });
            round(l)
        })
        .collect();
    let step = vec![Layer::Arx {
        word_bits: 64,
        ops: vec![
            ArxOp::Rotl {
                dst: 0,
                src: 0,
                k: 7,
            },
            ArxOp::AddConst {
                dst: 0,
                value: 0x9E37,
            },
        ],
    }];
    Primitive {
        name: format!("ToySpn-{rounds}r"),
        block_bits: 16,
        key_bits: 64,
        scratch_bits: 0,
        block_codec: Codec::BYTES,
        key_codec: Codec::little(64),
        sboxes: vec![sbox.clone()],
        rounds: rs,
        key_schedule: KeySchedule::Nonlinear {
            state_bits: 64,
            steps: vec![step; rounds],
            extract_offset: 0,
            round_key_bits: 16,
        },
        feed_forward: FeedForward::None,
        kind: Kind::Spn,
    }
}
