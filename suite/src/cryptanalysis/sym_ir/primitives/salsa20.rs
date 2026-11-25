//! The Salsa20 core (Bernstein 2005) as a [`Primitive`], following the
//! ChaCha conventions of [`super::chacha`].
//!
//! The *block* is the 16-word input state (constants at words 0, 5, 10, 15,
//! key, nonce and counter elsewhere, little-endian 32-bit words), there is
//! no separate key ([`KeySchedule::Independent`] with zero round keys), one
//! [`Round`](crate::cryptanalysis::sym_ir::Round) is one Salsa20 round (round
//! `i`, 0-based, is the column round if `i` is even and the row round if odd,
//! so Salsa20/20 is 20 rounds) and the feed-forward adds the input state word
//! by word ([`FeedForward::AddWords`]). Register 16 is a one-word scratch
//! used by the quarter round `b ^= rotl(a + d, 7)` and its three siblings.
//! `eval(&salsa20(20), &[], &state)` equals the 64-byte block of
//! `symmetric::salsa20::salsa20_block` for the state that function builds.

use super::round;
use crate::cryptanalysis::sym_ir::{
    ArxOp, Codec, FeedForward, KeySchedule, Kind, Layer, Primitive,
};
use crate::symmetric::salsa20::SIGMA;

const TMP: usize = 16;

/// Salsa quarter round on `[y0, y1, y2, y3]` (the reference's `a, b, c, d`
/// argument order is `[y0, y1, y2, y3]` with `qr(state, 0, 4, 8, 12)`).
fn quarter_round(ops: &mut Vec<ArxOp>, [a, b, c, d]: [usize; 4]) {
    for (x, y, dst, k) in [(a, d, b, 7), (b, a, c, 9), (c, b, d, 13), (d, c, a, 18)] {
        ops.push(ArxOp::Add {
            dst: TMP,
            a: x,
            b: y,
        });
        ops.push(ArxOp::Rotl {
            dst: TMP,
            src: TMP,
            k,
        });
        ops.push(ArxOp::Xor {
            dst,
            a: dst,
            b: TMP,
        });
    }
}

/// Salsa20 with `n` single rounds (`n = 20` is Salsa20/20).
pub fn salsa20(n: usize) -> Primitive {
    assert!(n >= 1);
    let cols = [[0, 4, 8, 12], [5, 9, 13, 1], [10, 14, 2, 6], [15, 3, 7, 11]];
    let rows = [[0, 1, 2, 3], [5, 6, 7, 4], [10, 11, 8, 9], [15, 12, 13, 14]];
    let rs = (0..n)
        .map(|i| {
            let mut ops = Vec::new();
            for q in if i.is_multiple_of(2) { cols } else { rows } {
                quarter_round(&mut ops, q);
            }
            round(vec![Layer::Arx { word_bits: 32, ops }])
        })
        .collect();
    Primitive {
        name: format!("Salsa20/{n}"),
        block_bits: 512,
        key_bits: 0,
        scratch_bits: 32,
        block_codec: Codec::little(32),
        key_codec: Codec::little(32),
        sboxes: vec![],
        rounds: rs,
        key_schedule: KeySchedule::Independent {
            round_keys: 0,
            round_key_bits: 0,
        },
        feed_forward: FeedForward::AddWords { word_bits: 32 },
        kind: Kind::Permutation,
    }
}

/// Salsa20/20, matching `symmetric::salsa20::salsa20_block`.
pub fn salsa20_20() -> Primitive {
    salsa20(20)
}

/// Assemble the 64-byte input state exactly as `salsa20_block` does.
pub fn input_block(key: &[u8; 32], nonce: &[u8; 8], counter: u64) -> Vec<u8> {
    let mut w = [0u32; 16];
    w[0] = SIGMA[0];
    w[5] = SIGMA[1];
    w[10] = SIGMA[2];
    w[15] = SIGMA[3];
    for i in 0..4 {
        w[1 + i] = u32::from_le_bytes(key[i * 4..i * 4 + 4].try_into().unwrap());
        w[11 + i] = u32::from_le_bytes(key[16 + i * 4..20 + i * 4].try_into().unwrap());
    }
    w[6] = u32::from_le_bytes(nonce[0..4].try_into().unwrap());
    w[7] = u32::from_le_bytes(nonce[4..8].try_into().unwrap());
    w[8] = counter as u32;
    w[9] = (counter >> 32) as u32;
    w.iter().flat_map(|x| x.to_le_bytes()).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::sym_ir::eval;
    use crate::symmetric::salsa20::salsa20_block;
    use rand::rngs::SmallRng;
    use rand::{Rng, SeedableRng};

    #[test]
    fn validates() {
        salsa20_20().validate().unwrap();
        salsa20(5).validate().unwrap();
    }

    #[test]
    fn matches_salsa20_block_1000_random() {
        let p = salsa20_20();
        let mut r = SmallRng::seed_from_u64(0x5a15_a001);
        for _ in 0..1000 {
            let mut key = [0u8; 32];
            let mut nonce = [0u8; 8];
            r.fill(&mut key[..]);
            r.fill(&mut nonce[..]);
            let counter: u64 = r.gen();
            let got = eval(&p, &[], &input_block(&key, &nonce, counter));
            assert_eq!(got, salsa20_block(&key, &nonce, counter).to_vec());
        }
    }

    /// Independent reduced-round reference: `n` single rounds, alternating
    /// column and row rounds, plus the input state.
    fn reference(n: usize, x: &[u32; 16]) -> [u32; 16] {
        let mut y = *x;
        let qr = |y: &mut [u32; 16], a: usize, b: usize, c: usize, d: usize| {
            y[b] ^= y[a].wrapping_add(y[d]).rotate_left(7);
            y[c] ^= y[b].wrapping_add(y[a]).rotate_left(9);
            y[d] ^= y[c].wrapping_add(y[b]).rotate_left(13);
            y[a] ^= y[d].wrapping_add(y[c]).rotate_left(18);
        };
        for i in 0..n {
            if i % 2 == 0 {
                qr(&mut y, 0, 4, 8, 12);
                qr(&mut y, 5, 9, 13, 1);
                qr(&mut y, 10, 14, 2, 6);
                qr(&mut y, 15, 3, 7, 11);
            } else {
                qr(&mut y, 0, 1, 2, 3);
                qr(&mut y, 5, 6, 7, 4);
                qr(&mut y, 10, 11, 8, 9);
                qr(&mut y, 15, 12, 13, 14);
            }
        }
        std::array::from_fn(|i| y[i].wrapping_add(x[i]))
    }

    #[test]
    fn reduced_rounds_match_independent_reference() {
        let mut r = SmallRng::seed_from_u64(0x5a15_a002);
        for n in 1..=20usize {
            let p = salsa20(n);
            for _ in 0..30 {
                let x: [u32; 16] = std::array::from_fn(|_| r.gen());
                let blk: Vec<u8> = x.iter().flat_map(|w| w.to_le_bytes()).collect();
                let want: Vec<u8> = reference(n, &x)
                    .iter()
                    .flat_map(|w| w.to_le_bytes())
                    .collect();
                assert_eq!(eval(&p, &[], &blk), want, "salsa20({n})");
            }
        }
    }
}
