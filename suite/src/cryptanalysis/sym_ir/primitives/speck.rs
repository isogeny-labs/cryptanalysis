//! Speck (Beaulieu et al., 2013) as [`Primitive`]s.
//!
//! Block bytes are two little-endian `n`-bit words, `y` first then `x`
//! (state words 0 and 1); the key is `m` little-endian words `k_0, l_0,
//! ..., l_{m-2}` (key-register words `0..m`). Round: `x = (x >>> 8) + y`,
//! `x ^= k`, `y = (y <<< 3) ^ x`; the round-key XOR is a
//! [`Layer::AddRoundKey`] at bit offset `n`. The key register has one
//! scratch word.

use super::round;
use crate::cryptanalysis::sym_ir::{
    ArxOp, Codec, FeedForward, KeySchedule, Kind, Layer, Primitive,
};

const ALPHA: usize = 8;
const BETA: usize = 3;

fn build(name: &str, n: usize, m: usize, t: usize) -> Primitive {
    let rounds = (0..t)
        .map(|i| {
            round(vec![
                Layer::Arx {
                    word_bits: n,
                    ops: vec![
                        ArxOp::Rotl {
                            dst: 1,
                            src: 1,
                            k: n - ALPHA,
                        },
                        ArxOp::Add { dst: 1, a: 1, b: 0 },
                    ],
                },
                Layer::AddRoundKey {
                    round_key: i,
                    bit_offset: n,
                },
                Layer::Arx {
                    word_bits: n,
                    ops: vec![
                        ArxOp::Rotl {
                            dst: 0,
                            src: 0,
                            k: BETA,
                        },
                        ArxOp::Xor { dst: 0, a: 0, b: 1 },
                    ],
                },
            ])
        })
        .collect();
    // Register words: 0 = k, 1..m = l_0..l_{m-2}, m = scratch.
    let steps = (0..t - 1)
        .map(|i| {
            let mut ops = vec![
                ArxOp::Rotl {
                    dst: m,
                    src: 1,
                    k: n - ALPHA,
                },
                ArxOp::Add { dst: m, a: 0, b: m },
                ArxOp::XorConst {
                    dst: m,
                    value: i as u64,
                },
                ArxOp::Rotl {
                    dst: 0,
                    src: 0,
                    k: BETA,
                },
                ArxOp::Xor { dst: 0, a: 0, b: m },
            ];
            for j in 1..m - 1 {
                ops.push(ArxOp::Copy { dst: j, src: j + 1 });
            }
            ops.push(ArxOp::Copy { dst: m - 1, src: m });
            vec![Layer::Arx { word_bits: n, ops }]
        })
        .collect();
    Primitive {
        name: name.into(),
        block_bits: 2 * n,
        key_bits: m * n,
        scratch_bits: 0,
        block_codec: Codec::little(n),
        key_codec: Codec::little(n),
        sboxes: vec![],
        rounds,
        key_schedule: KeySchedule::Nonlinear {
            state_bits: (m + 1) * n,
            steps,
            extract_offset: 0,
            round_key_bits: n,
        },
        feed_forward: FeedForward::None,
        kind: Kind::Arx,
    }
}

/// Speck64/128: 64-bit block, 128-bit key, 27 rounds
/// (`symmetric::speck::Speck64_128`).
pub fn speck64_128() -> Primitive {
    build("SPECK64/128", 32, 4, 27)
}

/// Speck128/128: 128-bit block, 128-bit key, 32 rounds
/// (`symmetric::speck::Speck128_128`).
pub fn speck128_128() -> Primitive {
    build("SPECK128/128", 64, 2, 32)
}

/// Speck128/256: 128-bit block, 256-bit key, 34 rounds
/// (`symmetric::speck::Speck128_256`).
pub fn speck128_256() -> Primitive {
    build("SPECK128/256", 64, 4, 34)
}
