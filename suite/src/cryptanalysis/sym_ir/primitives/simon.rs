//! Simon (Beaulieu et al., 2013) as [`Primitive`]s.
//!
//! Block bytes are two little-endian `n`-bit words, `y` first then `x`
//! (state words 0 and 1); two further state words are scratch. Round:
//! `(x, y) <- (y ^ f(x) ^ k, x)` with `f(x) = (x<<<1 & x<<<8) ^ x<<<2`; the
//! round-key XOR is a [`Layer::AddRoundKey`] on scratch word 2 (the new
//! `x`). The key is `m` little-endian words `k_0..k_{m-1}`; the key register
//! holds them plus two scratch words and each step appends the next key word
//! with the `z_j` bit and constant `2^n - 4` XORed in.

use super::round;
use crate::cryptanalysis::sym_ir::{
    ArxOp, Codec, FeedForward, KeySchedule, Kind, Layer, Primitive,
};
use crate::symmetric::simon::Z_SIMON;

fn build(name: &str, n: usize, m: usize, t: usize, zj: usize) -> Primitive {
    assert!(
        m == 2 || m == 4,
        "only m = 2 and m = 4 key schedules are described"
    );
    let rounds = (0..t)
        .map(|i| {
            round(vec![
                Layer::Arx {
                    word_bits: n,
                    ops: vec![
                        ArxOp::Rotl {
                            dst: 2,
                            src: 1,
                            k: 1,
                        },
                        ArxOp::Rotl {
                            dst: 3,
                            src: 1,
                            k: 8,
                        },
                        ArxOp::And { dst: 2, a: 2, b: 3 },
                        ArxOp::Rotl {
                            dst: 3,
                            src: 1,
                            k: 2,
                        },
                        ArxOp::Xor { dst: 2, a: 2, b: 3 },
                        ArxOp::Xor { dst: 2, a: 2, b: 0 },
                    ],
                },
                Layer::AddRoundKey {
                    round_key: i,
                    bit_offset: 2 * n,
                },
                Layer::Arx {
                    word_bits: n,
                    ops: vec![
                        ArxOp::Copy { dst: 0, src: 1 },
                        ArxOp::Copy { dst: 1, src: 2 },
                    ],
                },
            ])
        })
        .collect();
    let c: u64 = if n == 64 {
        !3u64
    } else {
        ((1u64 << n) - 1) & !3
    };
    let z = Z_SIMON[zj];
    // Register words: 0..m = window k_i..k_{i+m-1}; m, m+1 = scratch.
    let steps = (0..t - 1)
        .map(|i| {
            let zbit = (z >> (i % 62)) & 1;
            let mut ops = vec![ArxOp::Rotl {
                dst: m,
                src: m - 1,
                k: n - 3,
            }];
            if m == 4 {
                ops.push(ArxOp::Xor { dst: m, a: m, b: 1 });
            }
            ops.push(ArxOp::Rotl {
                dst: m + 1,
                src: m,
                k: n - 1,
            });
            ops.push(ArxOp::Xor {
                dst: m,
                a: m,
                b: m + 1,
            });
            ops.push(ArxOp::Xor { dst: m, a: m, b: 0 });
            ops.push(ArxOp::XorConst {
                dst: m,
                value: c ^ zbit,
            });
            for j in 0..m {
                ops.push(ArxOp::Copy { dst: j, src: j + 1 });
            }
            vec![Layer::Arx { word_bits: n, ops }]
        })
        .collect();
    Primitive {
        name: name.into(),
        block_bits: 2 * n,
        key_bits: m * n,
        scratch_bits: 2 * n,
        block_codec: Codec::little(n),
        key_codec: Codec::little(n),
        sboxes: vec![],
        rounds,
        key_schedule: KeySchedule::Nonlinear {
            state_bits: (m + 2) * n,
            steps,
            extract_offset: 0,
            round_key_bits: n,
        },
        feed_forward: FeedForward::None,
        kind: Kind::Feistel,
    }
}

/// Simon64/128: 64-bit block, 128-bit key, 44 rounds, `z_3`
/// (`symmetric::simon::Simon64_128`).
pub fn simon64_128() -> Primitive {
    build("SIMON64/128", 32, 4, 44, 3)
}

/// Simon128/128: 128-bit block, 128-bit key, 68 rounds, `z_2`
/// (`symmetric::simon::Simon128_128`).
pub fn simon128_128() -> Primitive {
    build("SIMON128/128", 64, 2, 68, 2)
}

/// Simon128/256: 128-bit block, 256-bit key, 72 rounds, `z_4`
/// (`symmetric::simon::Simon128_256`).
pub fn simon128_256() -> Primitive {
    build("SIMON128/256", 64, 4, 72, 4)
}
