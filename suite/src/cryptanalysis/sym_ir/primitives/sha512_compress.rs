//! The SHA-512 compression function (FIPS 180-4) as a [`Primitive`] in
//! Davies-Meyer form (64-bit words, 80 steps).
//!
//! The *block* is the 512-bit chaining value (eight 64-bit big-endian words
//! `a..h`, state words 0..8) and the *key* is the 512-bit message block
//! (sixteen big-endian 64-bit words). The message schedule is a
//! [`KeySchedule::Nonlinear`] register holding a 16-word sliding window plus
//! scratch; round key `t` is `W_t`. Step `t` is one [`Layer::Arx`] layer
//! with the round constant `K_t` as an [`ArxOp::AddConst`]. The feed-forward
//! adds the chaining value word by word modulo `2^64`, so
//! `eval(&steps(80), msg, h)` equals `hash::sha512::compress(h, msg)`.
//! The IR uses four scratch words (state words 8..12).

use super::round;
use crate::cryptanalysis::sym_ir::{
    ArxOp, Codec, FeedForward, KeySchedule, Kind, Layer, Primitive,
};
use crate::hash::sha512::K;

const A: usize = 0;
const B: usize = 1;
const C: usize = 2;
const D: usize = 3;
const E: usize = 4;
const F: usize = 5;
const G: usize = 6;
const H: usize = 7;
const T1: usize = 8;
const T2: usize = 9;
const T3: usize = 10;
const T4: usize = 11;

/// `dst = rotr(src, r0) ^ rotr(src, r1) ^ rotr(src, r2)` (the SHA-512
/// `Sigma` functions), using `tmp` as a temporary.
fn sigma(ops: &mut Vec<ArxOp>, dst: usize, src: usize, tmp: usize, rot: [usize; 3]) {
    ops.push(ArxOp::Rotl {
        dst,
        src,
        k: 64 - rot[0],
    });
    ops.push(ArxOp::Rotl {
        dst: tmp,
        src,
        k: 64 - rot[1],
    });
    ops.push(ArxOp::Xor {
        dst,
        a: dst,
        b: tmp,
    });
    ops.push(ArxOp::Rotl {
        dst: tmp,
        src,
        k: 64 - rot[2],
    });
    ops.push(ArxOp::Xor {
        dst,
        a: dst,
        b: tmp,
    });
}

fn step_ops(t: usize) -> Vec<ArxOp> {
    let mut ops = Vec::new();
    // T1 = h + Sigma1(e) + Ch(e,f,g) + K_t + W_t
    sigma(&mut ops, T1, E, T3, [14, 18, 41]);
    ops.push(ArxOp::Add {
        dst: T1,
        a: T1,
        b: H,
    });
    ops.push(ArxOp::Xor {
        dst: T3,
        a: F,
        b: G,
    });
    ops.push(ArxOp::And {
        dst: T3,
        a: E,
        b: T3,
    });
    ops.push(ArxOp::Xor {
        dst: T3,
        a: T3,
        b: G,
    });
    ops.push(ArxOp::Add {
        dst: T1,
        a: T1,
        b: T3,
    });
    ops.push(ArxOp::AddConst {
        dst: T1,
        value: K[t],
    });
    ops.push(ArxOp::AddKey {
        dst: T1,
        round_key: t,
        word: 0,
    });
    // T2 = Sigma0(a) + Maj(a,b,c)
    sigma(&mut ops, T2, A, T3, [28, 34, 39]);
    ops.push(ArxOp::And {
        dst: T3,
        a: A,
        b: B,
    });
    ops.push(ArxOp::And {
        dst: T4,
        a: A,
        b: C,
    });
    ops.push(ArxOp::Xor {
        dst: T3,
        a: T3,
        b: T4,
    });
    ops.push(ArxOp::And {
        dst: T4,
        a: B,
        b: C,
    });
    ops.push(ArxOp::Xor {
        dst: T3,
        a: T3,
        b: T4,
    });
    ops.push(ArxOp::Add {
        dst: T2,
        a: T2,
        b: T3,
    });
    // register shuffle
    ops.push(ArxOp::Copy { dst: H, src: G });
    ops.push(ArxOp::Copy { dst: G, src: F });
    ops.push(ArxOp::Copy { dst: F, src: E });
    ops.push(ArxOp::Add {
        dst: E,
        a: D,
        b: T1,
    });
    ops.push(ArxOp::Copy { dst: D, src: C });
    ops.push(ArxOp::Copy { dst: C, src: B });
    ops.push(ArxOp::Copy { dst: B, src: A });
    ops.push(ArxOp::Add {
        dst: A,
        a: T1,
        b: T2,
    });
    ops
}

/// Message-schedule step: append `W_{t+16}` to the 16-word window (words
/// 0..16, scratch words 16..19) and drop `W_t`.
fn schedule_ops() -> Vec<ArxOp> {
    let mut ops = Vec::new();
    // gamma1(w14) -> 16 ; gamma0(w1) -> 18 ; tmp 17
    let g = |ops: &mut Vec<ArxOp>, dst: usize, src: usize, rot: [usize; 2], shr: usize| {
        ops.push(ArxOp::Rotl {
            dst,
            src,
            k: 64 - rot[0],
        });
        ops.push(ArxOp::Rotl {
            dst: 17,
            src,
            k: 64 - rot[1],
        });
        ops.push(ArxOp::Xor { dst, a: dst, b: 17 });
        ops.push(ArxOp::Shr {
            dst: 17,
            src,
            k: shr,
        });
        ops.push(ArxOp::Xor { dst, a: dst, b: 17 });
    };
    g(&mut ops, 16, 14, [19, 61], 6);
    g(&mut ops, 18, 1, [1, 8], 7);
    ops.push(ArxOp::Add {
        dst: 16,
        a: 16,
        b: 9,
    });
    ops.push(ArxOp::Add {
        dst: 16,
        a: 16,
        b: 18,
    });
    ops.push(ArxOp::Add {
        dst: 16,
        a: 16,
        b: 0,
    });
    for j in 0..15 {
        ops.push(ArxOp::Copy { dst: j, src: j + 1 });
    }
    ops.push(ArxOp::Copy { dst: 15, src: 16 });
    ops
}

/// The first `n` steps (`1..=80`) of the SHA-512 compression function,
/// Davies-Meyer feed-forward included. `steps(80)` is the full function.
pub fn steps(n: usize) -> Primitive {
    assert!((1..=80).contains(&n), "n must be in 1..=80");
    let rounds = (0..n)
        .map(|t| {
            round(vec![Layer::Arx {
                word_bits: 64,
                ops: step_ops(t),
            }])
        })
        .collect();
    let ks_step = vec![Layer::Arx {
        word_bits: 64,
        ops: schedule_ops(),
    }];
    Primitive {
        name: if n == 80 {
            "SHA-512-compress".into()
        } else {
            format!("SHA-512-compress-{n}step")
        },
        block_bits: 512,
        key_bits: 1024,
        scratch_bits: 256,
        block_codec: Codec::big(64),
        key_codec: Codec::big(64),
        sboxes: vec![],
        rounds,
        key_schedule: KeySchedule::Nonlinear {
            state_bits: 20 * 64,
            steps: vec![ks_step; n - 1],
            extract_offset: 0,
            round_key_bits: 64,
        },
        feed_forward: FeedForward::AddWords { word_bits: 64 },
        kind: Kind::Arx,
    }
}

/// The full 80-step SHA-512 compression function.
pub fn sha512_compress() -> Primitive {
    steps(80)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::sym_ir::{eval, eval_rounds};
    use crate::hash::sha512 as reference;
    use rand::rngs::SmallRng;
    use rand::{Rng, SeedableRng};

    fn state_bytes(s: &[u64; 8]) -> Vec<u8> {
        s.iter().flat_map(|w| w.to_be_bytes()).collect()
    }

    fn pad(msg: &[u8]) -> Vec<u8> {
        let mut out = msg.to_vec();
        out.push(0x80);
        while out.len() % 128 != 112 {
            out.push(0);
        }
        out.extend_from_slice(&((msg.len() as u128) * 8).to_be_bytes());
        out
    }

    fn sha512_via_ir(msg: &[u8]) -> Vec<u8> {
        let p = sha512_compress();
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
        let mut st = state_bytes(&iv);
        for blk in pad(msg).chunks_exact(128) {
            st = eval(&p, blk, &st);
        }
        st
    }

    #[test]
    fn validates() {
        sha512_compress().validate().unwrap();
        steps(20).validate().unwrap();
    }

    #[test]
    fn fips_known_answers() {
        let cases: [(&[u8], &str); 2] = [
            (
                b"",
                "cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e",
            ),
            (
                b"abc",
                "ddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a2192992a274fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f",
            ),
        ];
        for (msg, digest) in cases {
            assert_eq!(sha512_via_ir(msg), hex::decode(digest).unwrap());
        }
    }

    #[test]
    fn matches_sha512_on_assorted_lengths() {
        let mut r = SmallRng::seed_from_u64(0x5a51_2000);
        for len in [0usize, 1, 111, 112, 127, 128, 129, 300] {
            let mut msg = vec![0u8; len];
            r.fill(&mut msg[..]);
            assert_eq!(
                sha512_via_ir(&msg),
                reference::sha512(&msg).to_vec(),
                "len {len}"
            );
        }
    }

    #[test]
    fn compress_matches_reference_1000_random() {
        let p = sha512_compress();
        let mut r = SmallRng::seed_from_u64(0x5a51_2001);
        for _ in 0..1000 {
            let mut st: [u64; 8] = std::array::from_fn(|_| r.gen());
            let mut blk = [0u8; 128];
            r.fill(&mut blk[..]);
            let got = eval(&p, &blk, &state_bytes(&st));
            reference::compress(&mut st, &blk);
            assert_eq!(got, state_bytes(&st));
        }
    }

    /// Independent reference for the first `n` steps with feed-forward.
    fn steps_reference(n: usize, st: &[u64; 8], blk: &[u8]) -> [u64; 8] {
        let mut w = [0u64; 80];
        for i in 0..16 {
            w[i] = u64::from_be_bytes(blk[8 * i..8 * i + 8].try_into().unwrap());
        }
        for i in 16..80 {
            let g0 = w[i - 15].rotate_right(1) ^ w[i - 15].rotate_right(8) ^ (w[i - 15] >> 7);
            let g1 = w[i - 2].rotate_right(19) ^ w[i - 2].rotate_right(61) ^ (w[i - 2] >> 6);
            w[i] = g1
                .wrapping_add(w[i - 7])
                .wrapping_add(g0)
                .wrapping_add(w[i - 16]);
        }
        let [mut a, mut b, mut c, mut d, mut e, mut f, mut g, mut hh] = *st;
        for i in 0..n {
            let s1 = e.rotate_right(14) ^ e.rotate_right(18) ^ e.rotate_right(41);
            let t1 = hh
                .wrapping_add(s1)
                .wrapping_add((e & f) ^ (!e & g))
                .wrapping_add(K[i])
                .wrapping_add(w[i]);
            let s0 = a.rotate_right(28) ^ a.rotate_right(34) ^ a.rotate_right(39);
            let t2 = s0.wrapping_add((a & b) ^ (a & c) ^ (b & c));
            hh = g;
            g = f;
            f = e;
            e = d.wrapping_add(t1);
            d = c;
            c = b;
            b = a;
            a = t1.wrapping_add(t2);
        }
        let v = [a, b, c, d, e, f, g, hh];
        std::array::from_fn(|i| st[i].wrapping_add(v[i]))
    }

    #[test]
    fn reduced_steps_match_independent_reference() {
        let mut r = SmallRng::seed_from_u64(0x5a51_2002);
        for n in 1..=80usize {
            let p = steps(n);
            for _ in 0..12 {
                let st: [u64; 8] = std::array::from_fn(|_| r.gen());
                let mut blk = [0u8; 128];
                r.fill(&mut blk[..]);
                assert_eq!(
                    eval(&p, &blk, &state_bytes(&st)),
                    state_bytes(&steps_reference(n, &st, &blk)),
                    "steps({n})"
                );
            }
        }
        let full = sha512_compress();
        let st = state_bytes(&[0x0123456789abcdef; 8]);
        let blk = [0x5au8; 128];
        for n in [1usize, 9, 20, 79] {
            assert_eq!(eval_rounds(&full, &blk, &st, n), eval(&steps(n), &blk, &st));
        }
    }
}
