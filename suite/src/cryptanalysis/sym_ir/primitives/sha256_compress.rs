//! The SHA-256 compression function (FIPS 180-4) as a [`Primitive`] in
//! Davies-Meyer form.
//!
//! The *block* is the 256-bit chaining value (eight 32-bit big-endian words
//! `a..h`, state words 0..8) and the *key* is the 512-bit message block
//! (sixteen big-endian words). The message schedule is a
//! [`KeySchedule::Nonlinear`] register holding a 16-word sliding window plus
//! scratch; round key `t` is `W_t`. Step `t` is one [`Layer::Arx`] layer
//! with the round constant `K_t` as an [`ArxOp::AddConst`]. The feed-forward
//! adds the chaining value word by word modulo `2^32`, so
//! `eval(&steps(64), msg, h)` equals `hash::sha256::compress(h, msg)`.
//! The IR uses four scratch words (state words 8..12).

use super::round;
use crate::cryptanalysis::sym_ir::{
    ArxOp, Codec, FeedForward, KeySchedule, Kind, Layer, Primitive,
};
use crate::hash::sha256::K;

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

/// `dst = rotr(src, r0) ^ rotr(src, r1) ^ rotr(src, r2)` (the SHA-256
/// `Sigma` functions), using `tmp` as a temporary.
fn sigma(ops: &mut Vec<ArxOp>, dst: usize, src: usize, tmp: usize, rot: [usize; 3]) {
    ops.push(ArxOp::Rotl {
        dst,
        src,
        k: 32 - rot[0],
    });
    ops.push(ArxOp::Rotl {
        dst: tmp,
        src,
        k: 32 - rot[1],
    });
    ops.push(ArxOp::Xor {
        dst,
        a: dst,
        b: tmp,
    });
    ops.push(ArxOp::Rotl {
        dst: tmp,
        src,
        k: 32 - rot[2],
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
    sigma(&mut ops, T1, E, T3, [6, 11, 25]);
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
        value: K[t] as u64,
    });
    ops.push(ArxOp::AddKey {
        dst: T1,
        round_key: t,
        word: 0,
    });
    // T2 = Sigma0(a) + Maj(a,b,c)
    sigma(&mut ops, T2, A, T3, [2, 13, 22]);
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
            k: 32 - rot[0],
        });
        ops.push(ArxOp::Rotl {
            dst: 17,
            src,
            k: 32 - rot[1],
        });
        ops.push(ArxOp::Xor { dst, a: dst, b: 17 });
        ops.push(ArxOp::Shr {
            dst: 17,
            src,
            k: shr,
        });
        ops.push(ArxOp::Xor { dst, a: dst, b: 17 });
    };
    g(&mut ops, 16, 14, [17, 19], 10);
    g(&mut ops, 18, 1, [7, 18], 3);
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

/// The first `n` steps (`1..=64`) of the SHA-256 compression function,
/// Davies-Meyer feed-forward included. `steps(64)` is the full function.
pub fn steps(n: usize) -> Primitive {
    assert!((1..=64).contains(&n), "n must be in 1..=64");
    let rounds = (0..n)
        .map(|t| {
            round(vec![Layer::Arx {
                word_bits: 32,
                ops: step_ops(t),
            }])
        })
        .collect();
    let ks_step = vec![Layer::Arx {
        word_bits: 32,
        ops: schedule_ops(),
    }];
    Primitive {
        name: if n == 64 {
            "SHA-256-compress".into()
        } else {
            format!("SHA-256-compress-{n}step")
        },
        block_bits: 256,
        key_bits: 512,
        scratch_bits: 128,
        block_codec: Codec::big(32),
        key_codec: Codec::big(32),
        sboxes: vec![],
        rounds,
        key_schedule: KeySchedule::Nonlinear {
            state_bits: 20 * 32,
            steps: vec![ks_step; n - 1],
            extract_offset: 0,
            round_key_bits: 32,
        },
        feed_forward: FeedForward::AddWords { word_bits: 32 },
        kind: Kind::Arx,
    }
}

/// The full 64-step SHA-256 compression function.
pub fn sha256_compress() -> Primitive {
    steps(64)
}
