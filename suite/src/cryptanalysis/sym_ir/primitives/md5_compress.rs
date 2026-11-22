//! The MD5 compression function (RFC 1321) as a [`Primitive`] in
//! Davies-Meyer form.
//!
//! The *block* is the 128-bit chaining value (four little-endian 32-bit
//! words `A, B, C, D`) and the *key* is the 64-byte message block (sixteen
//! little-endian words, one [`KeySchedule::Independent`] round key). Step `r`
//! is one [`Layer::Arx`] layer: the round function (`F`, `G`, `H` or `I`
//! written with `And`/`Xor` and a constant mask for the complement), the
//! constant `T[r]`, message word `word_index(r)` through `AddKey`, rotation
//! `S[r]`, then the register shuffle. The feed-forward adds the chaining
//! value word by word, so `eval(&steps(n), m, h)` equals
//! `cryptanalysis::md5_differential::md5_compress(h, m, n)` for every
//! `n` in `1..=64`; `steps(64)` is RFC 1321 MD5's compression function.
//! Registers 4..7 are scratch.

use super::round;
use crate::cryptanalysis::md5_differential::{word_index, S, T};
use crate::cryptanalysis::sym_ir::{
    ArxOp, Codec, FeedForward, KeySchedule, Kind, Layer, Primitive,
};

const A: usize = 0;
const B: usize = 1;
const C: usize = 2;
const D: usize = 3;
const T1: usize = 4;
const T2: usize = 5;

fn step_ops(r: usize) -> Vec<ArxOp> {
    let mut ops = Vec::new();
    let xor = |dst, a, b| ArxOp::Xor { dst, a, b };
    let and = |dst, a, b| ArxOp::And { dst, a, b };
    match r / 16 {
        // F = D ^ (B & (C ^ D))
        0 => {
            ops.push(xor(T1, C, D));
            ops.push(and(T1, B, T1));
            ops.push(xor(T1, T1, D));
        }
        // G = C ^ (D & (B ^ C))
        1 => {
            ops.push(xor(T1, B, C));
            ops.push(and(T1, D, T1));
            ops.push(xor(T1, T1, C));
        }
        // H = B ^ C ^ D
        2 => {
            ops.push(xor(T1, B, C));
            ops.push(xor(T1, T1, D));
        }
        // I = C ^ (B | !D), with x | y = x ^ y ^ (x & y)
        _ => {
            ops.push(ArxOp::Copy { dst: T2, src: D });
            ops.push(ArxOp::XorConst {
                dst: T2,
                value: 0xffff_ffff,
            });
            ops.push(and(T1, B, T2));
            ops.push(xor(T1, T1, B));
            ops.push(xor(T1, T1, T2));
            ops.push(xor(T1, T1, C));
        }
    }
    ops.push(ArxOp::Add {
        dst: T1,
        a: T1,
        b: A,
    });
    ops.push(ArxOp::AddConst {
        dst: T1,
        value: T[r] as u64,
    });
    ops.push(ArxOp::AddKey {
        dst: T1,
        round_key: 0,
        word: word_index(r),
    });
    ops.push(ArxOp::Rotl {
        dst: T1,
        src: T1,
        k: S[r] as usize,
    });
    ops.push(ArxOp::Add {
        dst: T1,
        a: T1,
        b: B,
    });
    ops.push(ArxOp::Copy { dst: A, src: D });
    ops.push(ArxOp::Copy { dst: D, src: C });
    ops.push(ArxOp::Copy { dst: C, src: B });
    ops.push(ArxOp::Copy { dst: B, src: T1 });
    ops
}

/// The first `n` steps (`1..=64`) of the MD5 compression function,
/// Davies-Meyer feed-forward included.
pub fn steps(n: usize) -> Primitive {
    assert!((1..=64).contains(&n), "n must be in 1..=64");
    let rounds = (0..n)
        .map(|r| {
            round(vec![Layer::Arx {
                word_bits: 32,
                ops: step_ops(r),
            }])
        })
        .collect();
    Primitive {
        name: if n == 64 {
            "MD5-compress".into()
        } else {
            format!("MD5-compress-{n}step")
        },
        block_bits: 128,
        key_bits: 512,
        scratch_bits: 64,
        block_codec: Codec::little(32),
        key_codec: Codec::little(32),
        sboxes: vec![],
        rounds,
        key_schedule: KeySchedule::Independent {
            round_keys: 1,
            round_key_bits: 512,
        },
        feed_forward: FeedForward::AddWords { word_bits: 32 },
        kind: Kind::Arx,
    }
}

/// The full 64-step MD5 compression function.
pub fn md5_compress() -> Primitive {
    steps(64)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::md5_differential::{md5_compress as reference, MD5_IV};
    use crate::cryptanalysis::sym_ir::eval;
    use rand::rngs::SmallRng;
    use rand::{Rng, SeedableRng};

    fn state_bytes(s: &[u32; 4]) -> Vec<u8> {
        s.iter().flat_map(|w| w.to_le_bytes()).collect()
    }

    fn md5_via_ir(msg: &[u8]) -> Vec<u8> {
        let p = md5_compress();
        let mut st = state_bytes(&MD5_IV);
        for blk in crate::hash::md5::md5_pad(msg.len())
            .iter()
            .fold(msg.to_vec(), |mut m, &b| {
                m.push(b);
                m
            })
            .chunks_exact(64)
        {
            st = eval(&p, blk, &st);
        }
        st
    }

    #[test]
    fn validates() {
        md5_compress().validate().unwrap();
        steps(17).validate().unwrap();
    }

    #[test]
    fn rfc1321_known_answers() {
        assert_eq!(
            md5_via_ir(b""),
            hex::decode("d41d8cd98f00b204e9800998ecf8427e").unwrap()
        );
        assert_eq!(
            md5_via_ir(b"abc"),
            hex::decode("900150983cd24fb0d6963f7d28e17f72").unwrap()
        );
        assert_eq!(
            md5_via_ir(b"message digest"),
            hex::decode("f96b697d7cb7938d525a2f31aaf161d0").unwrap()
        );
    }

    #[test]
    fn full_compress_matches_reference_1000_random() {
        let p = md5_compress();
        let mut r = SmallRng::seed_from_u64(0x3d5_0001);
        for _ in 0..1000 {
            let mut st: [u32; 4] = std::array::from_fn(|_| r.gen());
            let mut blk = [0u8; 64];
            r.fill(&mut blk[..]);
            let got = eval(&p, &blk, &state_bytes(&st));
            reference(&mut st, &blk, 64);
            assert_eq!(got, state_bytes(&st));
        }
    }

    #[test]
    fn every_reduced_step_count_matches_reference() {
        let mut r = SmallRng::seed_from_u64(0x3d5_0002);
        for n in 1..=64usize {
            let p = steps(n);
            for _ in 0..16 {
                let mut st: [u32; 4] = std::array::from_fn(|_| r.gen());
                let mut blk = [0u8; 64];
                r.fill(&mut blk[..]);
                let got = eval(&p, &blk, &state_bytes(&st));
                reference(&mut st, &blk, n);
                assert_eq!(got, state_bytes(&st), "steps({n})");
            }
        }
    }
}
