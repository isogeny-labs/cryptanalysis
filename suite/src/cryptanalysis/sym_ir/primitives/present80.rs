//! PRESENT-80 as a [`Primitive`] (Bogdanov et al., CHES 2007).
//!
//! Block and key are read as big-endian integers (`bytes[0]` most
//! significant) with state bit `i` the integer's bit `i`. Round `i` is
//! `[AddRoundKey(i-1), sBoxLayer, pLayer]`; the final key addition is the
//! last layer of round 31. The key schedule is the 80-bit register with
//! rotate-by-61, S-box on bits 76..80 and the round counter XORed into bits
//! 15..20.

use super::{round, sbox_from_u8};
use crate::cryptanalysis::sym_ir::{
    Codec, FeedForward, KeySchedule, Kind, Layer, Primitive, SboxId,
};
use crate::symmetric::present::SBOX;

/// The pLayer as a [`Layer::Permute`] permutation: input bit `i` moves to
/// bit `16 i mod 63` (bit 63 is fixed).
fn p_layer_perm() -> Vec<usize> {
    let mut perm = vec![0usize; 64];
    for i in 0..64 {
        let to = if i == 63 { 63 } else { (16 * i) % 63 };
        perm[to] = i;
    }
    perm
}

/// PRESENT-80, 31 rounds plus post-whitening.
pub fn present80() -> Primitive {
    let sbox_layer = Layer::SboxParallel {
        sbox: SboxId(0),
        width_bits: 4,
        count: 16,
        bit_offset: 0,
    };
    let rounds = (1..=31)
        .map(|i| {
            let mut l = vec![
                Layer::AddRoundKey {
                    round_key: i - 1,
                    bit_offset: 0,
                },
                sbox_layer.clone(),
                Layer::Permute {
                    perm: p_layer_perm(),
                },
            ];
            if i == 31 {
                l.push(Layer::AddRoundKey {
                    round_key: 31,
                    bit_offset: 0,
                });
            }
            round(l)
        })
        .collect();
    let rot61: Vec<usize> = (0..80).map(|j| (j + 80 - 61) % 80).collect();
    let steps = (1..=31u64)
        .map(|i| {
            vec![
                Layer::Permute {
                    perm: rot61.clone(),
                },
                Layer::SboxParallel {
                    sbox: SboxId(0),
                    width_bits: 4,
                    count: 1,
                    bit_offset: 76,
                },
                Layer::AddConst {
                    bit_offset: 15,
                    bits: 5,
                    value: i,
                },
            ]
        })
        .collect();
    Primitive {
        name: "PRESENT-80".into(),
        block_bits: 64,
        key_bits: 80,
        scratch_bits: 0,
        block_codec: Codec::big(64),
        key_codec: Codec::big(80),
        sboxes: vec![sbox_from_u8(4, &SBOX)],
        rounds,
        key_schedule: KeySchedule::Nonlinear {
            state_bits: 80,
            steps,
            extract_offset: 16,
            round_key_bits: 64,
        },
        feed_forward: FeedForward::None,
        kind: Kind::Spn,
    }
}
