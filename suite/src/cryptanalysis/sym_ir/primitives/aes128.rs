//! AES-128 and small-scale AES `SR(n, 2, 2, 4)` as [`Primitive`]s.
//!
//! State layout: byte `4c + r` of the block (row `r`, column `c`) is state
//! bits `8(4c+r) .. 8(4c+r)+8`, so the block bytes are the state bytes in
//! FIPS 197 order. Round `i` is `[AddRoundKey(0) if i = 1, SubBytes,
//! ShiftRows (Permute), MixColumns (LinearGf2), AddRoundKey(i)]`, with
//! MixColumns omitted from the last round unless requested. The key
//! schedule is a [`KeySchedule::Nonlinear`] register of four 32-bit words
//! plus one scratch word.

use super::{round, sbox_from_u8};
use crate::cryptanalysis::aes::reduced::{RCON, SBOX};
use crate::cryptanalysis::aes::small_scale::{gf16_mul, SBOX4};
use crate::cryptanalysis::sym_ir::{
    ArxOp, Codec, FeedForward, Gf2Matrix, KeySchedule, Kind, Layer, Primitive, SboxId,
};

/// Multiply by `x` in GF(2^8) modulo `x^8 + x^4 + x^3 + x + 1`.
fn xtime(a: u8) -> u8 {
    (a << 1) ^ if a & 0x80 != 0 { 0x1b } else { 0 }
}

/// Multiply two bytes in GF(2^8) (independent of the reference code).
fn gmul(mut a: u8, mut b: u8) -> u8 {
    let mut p = 0;
    while b != 0 {
        if b & 1 != 0 {
            p ^= a;
        }
        a = xtime(a);
        b >>= 1;
    }
    p
}

/// ShiftRows as a bit permutation: new byte `(c, r)` is old byte
/// `((c + r) mod 4, r)`.
fn shift_rows_perm() -> Vec<usize> {
    let mut perm = vec![0usize; 128];
    for c in 0..4 {
        for r in 0..4 {
            let dst = 4 * c + r;
            let src = 4 * ((c + r) % 4) + r;
            for k in 0..8 {
                perm[8 * dst + k] = 8 * src + k;
            }
        }
    }
    perm
}

/// MixColumns as a 128 x 128 GF(2) matrix (circulant `[2 3 1 1]` per column).
fn mix_columns_matrix() -> Gf2Matrix {
    let coef = [2u8, 3, 1, 1];
    let mut m = Gf2Matrix::zero(128, 128);
    for c in 0..4 {
        for r in 0..4 {
            for i in 0..4 {
                let k = coef[(i + 4 - r) % 4];
                for t in 0..8 {
                    let out = gmul(k, 1 << t);
                    for s in 0..8 {
                        if (out >> s) & 1 == 1 {
                            m.set(8 * (4 * c + r) + s, 8 * (4 * c + i) + t, true);
                        }
                    }
                }
            }
        }
    }
    m
}

/// AES-128 with `nr` rounds (`1..=10`); the last round omits MixColumns
/// unless `last_round_mix_columns` is set. Matches
/// `cryptanalysis::aes::reduced::ReducedAes128::new(key, nr, last_round_mix_columns)`
/// and, for `nr = 10`, `false`, the FIPS 197 cipher.
pub fn reduced(nr: usize, last_round_mix_columns: bool) -> Primitive {
    assert!((1..=10).contains(&nr), "nr must be in 1..=10");
    let mc = mix_columns_matrix();
    let sr = shift_rows_perm();
    let mut rounds = Vec::new();
    for i in 1..=nr {
        let mut layers = Vec::new();
        if i == 1 {
            layers.push(Layer::AddRoundKey {
                round_key: 0,
                bit_offset: 0,
            });
        }
        layers.push(Layer::SboxParallel {
            sbox: SboxId(0),
            width_bits: 8,
            count: 16,
            bit_offset: 0,
        });
        layers.push(Layer::Permute { perm: sr.clone() });
        if i < nr || last_round_mix_columns {
            layers.push(Layer::LinearGf2 { matrix: mc.clone() });
        }
        layers.push(Layer::AddRoundKey {
            round_key: i,
            bit_offset: 0,
        });
        rounds.push(round(layers));
    }
    // Key register: words 0..4 hold the current round key, word 4 is scratch.
    let steps = (1..=nr)
        .map(|i| {
            vec![
                Layer::Arx {
                    word_bits: 32,
                    ops: vec![
                        ArxOp::Copy { dst: 4, src: 3 },
                        ArxOp::Rotl {
                            dst: 4,
                            src: 4,
                            k: 24,
                        }, // RotWord on a little-endian word
                    ],
                },
                Layer::SboxParallel {
                    sbox: SboxId(0),
                    width_bits: 8,
                    count: 4,
                    bit_offset: 128,
                },
                Layer::Arx {
                    word_bits: 32,
                    ops: vec![
                        ArxOp::XorConst {
                            dst: 4,
                            value: RCON[i] as u64,
                        },
                        ArxOp::Xor { dst: 0, a: 0, b: 4 },
                        ArxOp::Xor { dst: 1, a: 1, b: 0 },
                        ArxOp::Xor { dst: 2, a: 2, b: 1 },
                        ArxOp::Xor { dst: 3, a: 3, b: 2 },
                    ],
                },
            ]
        })
        .collect();
    Primitive {
        name: format!(
            "AES-128-{nr}r{}",
            if last_round_mix_columns { "-mc" } else { "" }
        ),
        block_bits: 128,
        key_bits: 128,
        scratch_bits: 0,
        block_codec: Codec::BYTES,
        key_codec: Codec::BYTES,
        sboxes: vec![sbox_from_u8(8, &SBOX)],
        rounds,
        key_schedule: KeySchedule::Nonlinear {
            state_bits: 160,
            steps,
            extract_offset: 0,
            round_key_bits: 128,
        },
        feed_forward: FeedForward::None,
        kind: Kind::Spn,
    }
}

/// Full AES-128 (10 rounds, FIPS 197).
pub fn aes128() -> Primitive {
    reduced(10, false)
}

/// Small-scale AES `SR(nr, 2, 2, 4)` (Cid-Murphy-Robshaw), matching
/// `cryptanalysis::aes::small_scale::SmallAes::new(key, nr)`: a 2 x 2 state
/// of 4-bit cells, last round without MixColumns.
///
/// Cell `c` (index `2*col + row`) is state bits `4c .. 4c+4`; a 16-bit block
/// or key is 2 bytes, cell `c` being nibble `c % 2` (low nibble first) of
/// byte `c / 2`. `nr` is in `1..=15` (the reference constant table).
pub fn small_scale(nr: usize) -> Primitive {
    assert!((1..=15).contains(&nr), "nr must be in 1..=15");
    // MixColumns [[3,2],[2,3]] on each column pair of cells.
    let mut mc = Gf2Matrix::zero(16, 16);
    for col in 0..2 {
        for (r, row) in [[3u8, 2], [2, 3]].iter().enumerate() {
            for (i, &k) in row.iter().enumerate() {
                for t in 0..4 {
                    let out = gf16_mul(k, 1 << t);
                    for s in 0..4 {
                        if (out >> s) & 1 == 1 {
                            mc.set(4 * (2 * col + r) + s, 4 * (2 * col + i) + t, true);
                        }
                    }
                }
            }
        }
    }
    // ShiftRows: swap cells 1 and 3 (row 1 of both columns).
    let mut sr: Vec<usize> = (0..16).collect();
    for k in 0..4 {
        sr.swap(4 + k, 12 + k);
    }
    let mut rounds = Vec::new();
    for i in 1..=nr {
        let mut layers = Vec::new();
        if i == 1 {
            layers.push(Layer::AddRoundKey {
                round_key: 0,
                bit_offset: 0,
            });
        }
        layers.push(Layer::SboxParallel {
            sbox: SboxId(0),
            width_bits: 4,
            count: 4,
            bit_offset: 0,
        });
        layers.push(Layer::Permute { perm: sr.clone() });
        if i < nr {
            layers.push(Layer::LinearGf2 { matrix: mc.clone() });
        }
        layers.push(Layer::AddRoundKey {
            round_key: i,
            bit_offset: 0,
        });
        rounds.push(round(layers));
    }
    // Key register: 4 cells (regs 0..4) plus 2 scratch cells (regs 4, 5).
    let mut rcon = 1u8;
    let steps = (1..=nr)
        .map(|i| {
            if i > 1 {
                rcon = gf16_mul(rcon, 2);
            }
            vec![
                Layer::Arx {
                    word_bits: 4,
                    ops: vec![
                        ArxOp::Copy { dst: 4, src: 3 },
                        ArxOp::Copy { dst: 5, src: 2 },
                    ],
                },
                Layer::SboxParallel {
                    sbox: SboxId(0),
                    width_bits: 4,
                    count: 2,
                    bit_offset: 16,
                },
                Layer::Arx {
                    word_bits: 4,
                    ops: vec![
                        ArxOp::XorConst {
                            dst: 4,
                            value: rcon as u64,
                        },
                        ArxOp::Xor { dst: 0, a: 0, b: 4 },
                        ArxOp::Xor { dst: 1, a: 1, b: 5 },
                        ArxOp::Xor { dst: 2, a: 2, b: 0 },
                        ArxOp::Xor { dst: 3, a: 3, b: 1 },
                    ],
                },
            ]
        })
        .collect();
    Primitive {
        name: format!("SR({nr},2,2,4)"),
        block_bits: 16,
        key_bits: 16,
        scratch_bits: 0,
        block_codec: Codec::BYTES,
        key_codec: Codec::BYTES,
        sboxes: vec![crate::cryptanalysis::sbox::Sbox::new(
            4,
            4,
            SBOX4.iter().map(|&v| v as u32).collect(),
        )
        .expect("SBOX4")],
        rounds,
        key_schedule: KeySchedule::Nonlinear {
            state_bits: 24,
            steps,
            extract_offset: 0,
            round_key_bits: 16,
        },
        feed_forward: FeedForward::None,
        kind: Kind::Spn,
    }
}
