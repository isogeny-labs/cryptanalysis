//! The BLAKE2b compression function F (RFC 7693 section 3.2) as a
//! [`Primitive`].
//!
//! The *block* is the 512-bit chaining value `h` (eight little-endian 64-bit
//! words) and the *key* is the 128-byte message block (sixteen little-endian
//! words, one [`KeySchedule::Independent`] round key holding all of them).
//! The 16-word working vector `v` is the state: words 0..8 are `h`, words
//! 8..16 are scratch. The first round begins with the initialisation
//! `v[8..16] = IV` (then `v[12] ^= t_lo`, `v[13] ^= t_hi`, `v[14] ^= !0` if
//! the block is the last one), where the counter `t` and the last-block flag
//! are constructor parameters, not inputs. Round `r` is the eight `G` calls
//! of RFC 7693 with message words selected by `SIGMA[r]`, each `G`
//! being a short [`Layer::Arx`] sequence (`AddKey` supplies the message
//! words). The last round ends with the fold `v[i] ^= v[i+8]`, and the
//! feed-forward ([`FeedForward::Xor`]) XORs `h`, so
//! `eval(&rounds(12), m, h)` equals `h ^ v[0..8] ^ v[8..16]` of the
//! reference `hash::blake2b::compress` (for `t = 0`, not-last).
//!
//! Because the fold lives in the last listed round, `eval_rounds` on a
//! prefix of a longer description omits it; use [`rounds`] /
//! [`rounds_with`] to get a reduced-round primitive whose last round does
//! carry the fold.

use super::round;
use crate::cryptanalysis::sym_ir::{
    ArxOp, Codec, FeedForward, KeySchedule, Kind, Layer, Primitive,
};
use crate::hash::blake2b::{IV, SIGMA};

/// `G` on registers `a, b, c, d` with message words `x`, `y` (indices into
/// the message block).
fn g(ops: &mut Vec<ArxOp>, [a, b, c, d]: [usize; 4], x: usize, y: usize) {
    let key = |dst, word| ArxOp::AddKey {
        dst,
        round_key: 0,
        word,
    };
    ops.push(ArxOp::Add { dst: a, a, b });
    ops.push(key(a, x));
    ops.push(ArxOp::Xor { dst: d, a: d, b: a });
    ops.push(ArxOp::Rotl {
        dst: d,
        src: d,
        k: 32,
    });
    ops.push(ArxOp::Add { dst: c, a: c, b: d });
    ops.push(ArxOp::Xor { dst: b, a: b, b: c });
    ops.push(ArxOp::Rotl {
        dst: b,
        src: b,
        k: 40,
    });
    ops.push(ArxOp::Add { dst: a, a, b });
    ops.push(key(a, y));
    ops.push(ArxOp::Xor { dst: d, a: d, b: a });
    ops.push(ArxOp::Rotl {
        dst: d,
        src: d,
        k: 48,
    });
    ops.push(ArxOp::Add { dst: c, a: c, b: d });
    ops.push(ArxOp::Xor { dst: b, a: b, b: c });
    ops.push(ArxOp::Rotl {
        dst: b,
        src: b,
        k: 1,
    });
}

fn round_ops(r: usize) -> Vec<ArxOp> {
    let s = &SIGMA[r % 12];
    let mut ops = Vec::new();
    let cols = [[0, 4, 8, 12], [1, 5, 9, 13], [2, 6, 10, 14], [3, 7, 11, 15]];
    let diag = [[0, 5, 10, 15], [1, 6, 11, 12], [2, 7, 8, 13], [3, 4, 9, 14]];
    for (q, regs) in cols.iter().chain(diag.iter()).enumerate() {
        g(&mut ops, *regs, s[2 * q], s[2 * q + 1]);
    }
    ops
}

fn init_ops(t: u128, last: bool) -> Vec<ArxOp> {
    let mut ops = Vec::new();
    for (i, &iv) in IV.iter().enumerate() {
        let mut v = iv;
        if i == 4 {
            v ^= t as u64;
        }
        if i == 5 {
            v ^= (t >> 64) as u64;
        }
        if i == 6 && last {
            v ^= u64::MAX;
        }
        ops.push(ArxOp::Xor {
            dst: 8 + i,
            a: 8 + i,
            b: 8 + i,
        });
        ops.push(ArxOp::XorConst {
            dst: 8 + i,
            value: v,
        });
    }
    ops
}

/// BLAKE2b compression with `n` rounds (`1..=12`; round `r` uses
/// `SIGMA[r]`, the reference's 12-row table), byte counter `t` and
/// last-block flag `last`.
pub fn rounds_with(n: usize, t: u128, last: bool) -> Primitive {
    assert!((1..=12).contains(&n), "n must be in 1..=12");
    let rs = (0..n)
        .map(|r| {
            let mut layers = Vec::new();
            if r == 0 {
                layers.push(Layer::Arx {
                    word_bits: 64,
                    ops: init_ops(t, last),
                });
            }
            layers.push(Layer::Arx {
                word_bits: 64,
                ops: round_ops(r),
            });
            if r == n - 1 {
                layers.push(Layer::Arx {
                    word_bits: 64,
                    ops: (0..8)
                        .map(|i| ArxOp::Xor {
                            dst: i,
                            a: i,
                            b: i + 8,
                        })
                        .collect(),
                });
            }
            round(layers)
        })
        .collect();
    Primitive {
        name: if n == 12 {
            "BLAKE2b-compress".into()
        } else {
            format!("BLAKE2b-compress-{n}r")
        },
        block_bits: 512,
        key_bits: 1024,
        scratch_bits: 512,
        block_codec: Codec::little(64),
        key_codec: Codec::little(64),
        sboxes: vec![],
        rounds: rs,
        key_schedule: KeySchedule::Independent {
            round_keys: 1,
            round_key_bits: 1024,
        },
        feed_forward: FeedForward::Xor,
        kind: Kind::Arx,
    }
}

/// BLAKE2b compression with `n` rounds, counter `t = 0`, not the last block.
pub fn rounds(n: usize) -> Primitive {
    rounds_with(n, 0, false)
}

/// The full 12-round BLAKE2b compression function (`t = 0`, not last).
pub fn blake2b_compress() -> Primitive {
    rounds(12)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::sym_ir::eval;
    use crate::hash::blake2b as reference;
    use rand::rngs::SmallRng;
    use rand::{Rng, SeedableRng};

    fn h_bytes(h: &[u64; 8]) -> Vec<u8> {
        h.iter().flat_map(|w| w.to_le_bytes()).collect()
    }

    #[test]
    fn validates() {
        blake2b_compress().validate().unwrap();
        rounds(3).validate().unwrap();
    }

    #[test]
    fn compress_matches_reference_1000_random() {
        let mut r = SmallRng::seed_from_u64(0xb1a2_0001);
        for k in 0..1000 {
            let t: u128 = if k % 3 == 0 {
                0
            } else {
                ((r.gen::<u64>() as u128) << 64) | r.gen::<u64>() as u128
            };
            let last = k % 2 == 1;
            let p = rounds_with(12, t, last);
            let mut h: [u64; 8] = std::array::from_fn(|_| r.gen());
            let mut blk = [0u8; 128];
            r.fill(&mut blk[..]);
            let got = eval(&p, &blk, &h_bytes(&h));
            reference::compress(&mut h, &blk, t, last);
            assert_eq!(got, h_bytes(&h));
        }
    }

    /// One-block BLAKE2b-512 of `abc` computed through the IR.
    #[test]
    fn rfc7693_abc_via_ir() {
        let mut h = reference::IV;
        h[0] ^= 0x0101_0040; // digest 64, key 0, fanout 1, depth 1
        let mut blk = [0u8; 128];
        blk[..3].copy_from_slice(b"abc");
        let p = rounds_with(12, 3, true);
        let out = eval(&p, &blk, &h_bytes(&h));
        assert_eq!(out, reference::blake2b(b"abc", 64));
        assert_eq!(
            hex::encode(&out[..8]),
            "ba80a53f981c4d0d",
            "RFC 7693 appendix A digest prefix"
        );
    }

    /// Independent reduced-round reference (straight from RFC 7693).
    fn reduced_reference(n: usize, h: &[u64; 8], blk: &[u8; 128]) -> [u64; 8] {
        let m: [u64; 16] =
            std::array::from_fn(|i| u64::from_le_bytes(blk[8 * i..8 * i + 8].try_into().unwrap()));
        let mut v = [0u64; 16];
        v[..8].copy_from_slice(h);
        v[8..].copy_from_slice(&reference::IV);
        let gg = |v: &mut [u64; 16], a: usize, b: usize, c: usize, d: usize, x: u64, y: u64| {
            v[a] = v[a].wrapping_add(v[b]).wrapping_add(x);
            v[d] = (v[d] ^ v[a]).rotate_right(32);
            v[c] = v[c].wrapping_add(v[d]);
            v[b] = (v[b] ^ v[c]).rotate_right(24);
            v[a] = v[a].wrapping_add(v[b]).wrapping_add(y);
            v[d] = (v[d] ^ v[a]).rotate_right(16);
            v[c] = v[c].wrapping_add(v[d]);
            v[b] = (v[b] ^ v[c]).rotate_right(63);
        };
        for r in 0..n {
            let s = &reference::SIGMA[r];
            gg(&mut v, 0, 4, 8, 12, m[s[0]], m[s[1]]);
            gg(&mut v, 1, 5, 9, 13, m[s[2]], m[s[3]]);
            gg(&mut v, 2, 6, 10, 14, m[s[4]], m[s[5]]);
            gg(&mut v, 3, 7, 11, 15, m[s[6]], m[s[7]]);
            gg(&mut v, 0, 5, 10, 15, m[s[8]], m[s[9]]);
            gg(&mut v, 1, 6, 11, 12, m[s[10]], m[s[11]]);
            gg(&mut v, 2, 7, 8, 13, m[s[12]], m[s[13]]);
            gg(&mut v, 3, 4, 9, 14, m[s[14]], m[s[15]]);
        }
        std::array::from_fn(|i| h[i] ^ v[i] ^ v[i + 8])
    }

    #[test]
    fn reduced_rounds_match_independent_reference() {
        let mut r = SmallRng::seed_from_u64(0xb1a2_0002);
        for n in 1..=12usize {
            let p = rounds(n);
            for _ in 0..20 {
                let h: [u64; 8] = std::array::from_fn(|_| r.gen());
                let mut blk = [0u8; 128];
                r.fill(&mut blk[..]);
                assert_eq!(
                    eval(&p, &blk, &h_bytes(&h)),
                    h_bytes(&reduced_reference(n, &h, &blk)),
                    "rounds({n})"
                );
            }
        }
    }
}
