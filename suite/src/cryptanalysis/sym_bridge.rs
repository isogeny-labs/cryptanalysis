//! Bridge between the [`sym_ir`](crate::cryptanalysis::sym_ir) cipher IR and the generic cryptanalysis
//! consumers.
//!
//! * [`KeyedPrimitive`] binds a [`Primitive`] to a key and implements
//!   [`boomerang::BlockCipher`](BlockCipher), so the boomerang
//!   distinguisher, rectangle attack, sandwich and trail-search code run on
//!   any primitive of the IR.
//! * [`ModeCipher`] adapts a
//!   [`symmetric::modes::cipher::BlockCipher<N>`](ModesBlockCipher)
//!   implementation to the boomerang trait.
//!
//! ## Decryption
//!
//! The IR describes the forward direction only. [`KeyedPrimitive`] derives an
//! inverse when the description admits one, and records the outcome in
//! [`KeyedPrimitive::is_invertible`]:
//!
//! * layer by layer, for descriptions whose layers are all invertible
//!   (bijective S-boxes, invertible GF(2) matrices, permutations, key and
//!   constant additions, and in-place ARX word operations such as Speck's);
//! * for [`Kind::Feistel`], round by round using the forward round function
//!   with one half zeroed (Simon).
//!
//! A primitive with a feed-forward (ChaCha, SHA-256 compression) has no
//! decryption. Before reporting a primitive as invertible the constructor
//! checks `decrypt(encrypt(x)) = x` on a few fixed blocks; a failure marks it
//! non-invertible rather than guessing. [`BlockCipher::decrypt`] on a
//! non-invertible primitive panics, so callers should consult
//! [`KeyedPrimitive::is_invertible`] (or [`is_invertible`]) first.

use crate::cryptanalysis::boomerang::BlockCipher;
use crate::cryptanalysis::sym_ir::gf2::{get_bit, get_bits, set_bit, set_bits, words_for};
use crate::cryptanalysis::sym_ir::{
    apply_round, eval_rounds_with_keys, expand_key, ArxOp, FeedForward, Gf2Matrix, Kind, Layer,
    Primitive,
};
use crate::symmetric::modes::cipher::BlockCipher as ModesBlockCipher;

/// A deterministic, non-trivial key for `p`: byte `i` is
/// `0x5A + 0x1F * i` (mod 256). Empty for unkeyed primitives.
pub fn default_key(p: &Primitive) -> Vec<u8> {
    (0..p.key_bytes())
        .map(|i| 0x5Au8.wrapping_add(0x1F_u8.wrapping_mul(i as u8)))
        .collect()
}

/// Whether [`KeyedPrimitive`] can decrypt `p` (see the module docs). Builds a
/// throw-away instance under [`default_key`] and runs the round-trip check.
pub fn is_invertible(p: &Primitive) -> bool {
    KeyedPrimitive::new(p.clone(), default_key(p)).is_invertible()
}

/// One inverted layer (see [`KeyedPrimitive`]).
#[derive(Clone, Debug)]
enum InvLayer {
    Sbox {
        inv: Vec<u32>,
        width: usize,
        count: usize,
        off: usize,
    },
    Matrix(Gf2Matrix),
    /// `out[perm_inv[i]] = in[i]` is applied as `out[i] = in[src[i]]`.
    Perm(Vec<usize>),
    XorKey {
        round_key: usize,
        off: usize,
    },
    XorConst {
        off: usize,
        bits: usize,
        value: u64,
    },
    Arx {
        w: usize,
        ops: Vec<InvOp>,
    },
}

/// Inverse of one in-place ARX word operation.
#[derive(Clone, Copy, Debug)]
enum InvOp {
    SubReg { dst: usize, other: usize },
    Rotr { dst: usize, k: usize },
    XorReg { dst: usize, other: usize },
    XorConst { dst: usize, value: u64 },
    SubConst { dst: usize, value: u64 },
    XorKey { dst: usize, rk: usize, word: usize },
    SubKey { dst: usize, rk: usize, word: usize },
}

fn invert_arx(ops: &[ArxOp]) -> Option<Vec<InvOp>> {
    let mut out = Vec::with_capacity(ops.len());
    for op in ops.iter().rev() {
        out.push(match *op {
            ArxOp::Add { dst, a, b } if dst == a && b != dst => InvOp::SubReg { dst, other: b },
            ArxOp::Add { dst, a, b } if dst == b && a != dst => InvOp::SubReg { dst, other: a },
            ArxOp::Rotl { dst, src, k } if dst == src => InvOp::Rotr { dst, k },
            ArxOp::Xor { dst, a, b } if dst == a && b != dst => InvOp::XorReg { dst, other: b },
            ArxOp::Xor { dst, a, b } if dst == b && a != dst => InvOp::XorReg { dst, other: a },
            ArxOp::XorConst { dst, value } => InvOp::XorConst { dst, value },
            ArxOp::AddConst { dst, value } => InvOp::SubConst { dst, value },
            ArxOp::XorKey {
                dst,
                round_key,
                word,
            } => InvOp::XorKey {
                dst,
                rk: round_key,
                word,
            },
            ArxOp::AddKey {
                dst,
                round_key,
                word,
            } => InvOp::SubKey {
                dst,
                rk: round_key,
                word,
            },
            _ => return None,
        });
    }
    Some(out)
}

fn invert_layer(p: &Primitive, l: &Layer) -> Option<InvLayer> {
    Some(match l {
        Layer::SboxParallel {
            sbox,
            width_bits,
            count,
            bit_offset,
        } => InvLayer::Sbox {
            inv: p.sboxes[sbox.0].inverse_table()?,
            width: *width_bits,
            count: *count,
            off: *bit_offset,
        },
        Layer::LinearGf2 { matrix } => InvLayer::Matrix(matrix.inverse()?),
        Layer::Permute { perm } => {
            // Forward: out[i] = in[perm[i]]. Inverse: out[perm[i]] = in[i],
            // i.e. out[j] = in[src[j]] with src[perm[i]] = i.
            let mut src = vec![0usize; perm.len()];
            for (i, &pi) in perm.iter().enumerate() {
                src[pi] = i;
            }
            InvLayer::Perm(src)
        }
        Layer::Arx { word_bits, ops } => InvLayer::Arx {
            w: *word_bits,
            ops: invert_arx(ops)?,
        },
        Layer::AddRoundKey {
            round_key,
            bit_offset,
        } => InvLayer::XorKey {
            round_key: *round_key,
            off: *bit_offset,
        },
        Layer::AddConst {
            bit_offset,
            bits,
            value,
        } => InvLayer::XorConst {
            off: *bit_offset,
            bits: *bits,
            value: *value,
        },
    })
}

fn mask(w: usize) -> u64 {
    if w == 64 {
        u64::MAX
    } else {
        (1u64 << w) - 1
    }
}

fn xor_range(state: &mut [u64], off: usize, src: &[u64], n: usize) {
    let mut done = 0;
    while done < n {
        let take = (n - done).min(64);
        let cur = get_bits(state, off + done, take);
        set_bits(state, off + done, take, cur ^ get_bits(src, done, take));
        done += take;
    }
}

fn apply_inv_layer(l: &InvLayer, state: &mut Vec<u64>, rks: &[Vec<u64>], rkb: usize) {
    match l {
        InvLayer::Sbox {
            inv,
            width,
            count,
            off,
        } => {
            for j in 0..*count {
                let o = off + j * width;
                let x = get_bits(state, o, *width) as usize;
                set_bits(state, o, *width, inv[x] as u64);
            }
        }
        InvLayer::Matrix(m) => *state = m.mul_vec(state),
        InvLayer::Perm(src) => {
            let mut out = vec![0u64; state.len()];
            for (i, &s) in src.iter().enumerate() {
                if get_bit(state, s) {
                    set_bit(&mut out, i, true);
                }
            }
            *state = out;
        }
        InvLayer::XorKey { round_key, off } => xor_range(state, *off, &rks[*round_key], rkb),
        InvLayer::XorConst { off, bits, value } => {
            let cur = get_bits(state, *off, *bits);
            set_bits(state, *off, *bits, cur ^ value);
        }
        InvLayer::Arx { w, ops } => {
            let w = *w;
            let m = mask(w);
            for op in ops {
                let rd = |s: &[u64], r: usize| get_bits(s, r * w, w);
                let (dst, v) = match *op {
                    InvOp::SubReg { dst, other } => {
                        (dst, rd(state, dst).wrapping_sub(rd(state, other)) & m)
                    }
                    InvOp::Rotr { dst, k } => {
                        let k = k % w;
                        let x = rd(state, dst);
                        (
                            dst,
                            if k == 0 {
                                x
                            } else {
                                ((x >> k) | (x << (w - k))) & m
                            },
                        )
                    }
                    InvOp::XorReg { dst, other } => (dst, rd(state, dst) ^ rd(state, other)),
                    InvOp::XorConst { dst, value } => (dst, (rd(state, dst) ^ value) & m),
                    InvOp::SubConst { dst, value } => (dst, rd(state, dst).wrapping_sub(value) & m),
                    InvOp::XorKey { dst, rk, word } => {
                        (dst, rd(state, dst) ^ get_bits(&rks[rk], word * w, w))
                    }
                    InvOp::SubKey { dst, rk, word } => (
                        dst,
                        rd(state, dst).wrapping_sub(get_bits(&rks[rk], word * w, w)) & m,
                    ),
                };
                set_bits(state, dst * w, w, v);
            }
        }
    }
}

/// How decryption is done for a [`KeyedPrimitive`].
#[derive(Clone, Debug)]
enum Inverse {
    /// Not available.
    None,
    /// Invert each layer of each round, last round first.
    Layers(Vec<Vec<InvLayer>>),
    /// Round-by-round Feistel inversion through the forward round function.
    Feistel,
}

/// A [`Primitive`] bound to a key: an encryption oracle (and, when the IR
/// description is invertible, a decryption oracle) for the generic
/// cryptanalysis code. See the [module docs](self).
#[derive(Clone, Debug)]
pub struct KeyedPrimitive {
    primitive: Primitive,
    key: Vec<u8>,
    round_keys: Vec<Vec<u64>>,
    inverse: Inverse,
}

impl KeyedPrimitive {
    /// Bind `primitive` to `key` (`primitive.key_bytes()` bytes; empty for an
    /// unkeyed primitive). Panics if the key length is wrong.
    pub fn new(primitive: Primitive, key: Vec<u8>) -> Self {
        let round_keys = expand_key(&primitive, &key);
        let mut s = KeyedPrimitive {
            primitive,
            key,
            round_keys,
            inverse: Inverse::None,
        };
        s.inverse = s.build_inverse();
        s
    }

    /// Bind `primitive` to [`default_key`].
    pub fn with_default_key(primitive: Primitive) -> Self {
        let key = default_key(&primitive);
        Self::new(primitive, key)
    }

    /// The underlying description.
    pub fn primitive(&self) -> &Primitive {
        &self.primitive
    }

    /// The key bytes.
    pub fn key(&self) -> &[u8] {
        &self.key
    }

    /// Whether [`BlockCipher::decrypt`] is available.
    pub fn is_invertible(&self) -> bool {
        !matches!(self.inverse, Inverse::None)
    }

    /// Encrypt `block` (the block function, including any feed-forward).
    pub fn eval(&self, block: &[u8]) -> Vec<u8> {
        eval_rounds_with_keys(
            &self.primitive,
            &self.round_keys,
            block,
            self.primitive.rounds.len(),
        )
    }

    /// Decrypt `block`, or `None` if the primitive is not invertible.
    pub fn try_decrypt(&self, block: &[u8]) -> Option<Vec<u8>> {
        let p = &self.primitive;
        let rkb = p.key_schedule.round_key_bits();
        let init = p.block_codec.encode(block);
        let mut state = vec![0u64; words_for(p.state_bits())];
        state[..init.len()].copy_from_slice(&init);
        match &self.inverse {
            Inverse::None => return None,
            Inverse::Layers(rounds) => {
                for r in rounds {
                    for l in r {
                        apply_inv_layer(l, &mut state, &self.round_keys, rkb);
                    }
                }
            }
            Inverse::Feistel => {
                let half = p.block_bits / 2;
                for i in (0..p.rounds.len()).rev() {
                    // Round: (a, b) -> (b, a ^ F(b)). Run it on (0, c) to get
                    // F(c), then (c, d) -> (d ^ F(c), c).
                    let c = get_bits_vec(&state, 0, half);
                    let d = get_bits_vec(&state, half, half);
                    let mut t = vec![0u64; state.len()];
                    put_bits_vec(&mut t, half, &c, half);
                    apply_round(p, i, &mut t, &self.round_keys);
                    let fc = get_bits_vec(&t, half, half);
                    let mut next = vec![0u64; state.len()];
                    let a: Vec<u64> = d.iter().zip(&fc).map(|(x, y)| x ^ y).collect();
                    put_bits_vec(&mut next, 0, &a, half);
                    put_bits_vec(&mut next, half, &c, half);
                    state = next;
                }
            }
        }
        Some(p.block_codec.decode(&state, p.block_bits))
    }

    fn build_inverse(&self) -> Inverse {
        let p = &self.primitive;
        if p.feed_forward != FeedForward::None {
            return Inverse::None;
        }
        let mut cand = Vec::new();
        let layers: Option<Vec<Vec<InvLayer>>> = p
            .rounds
            .iter()
            .rev()
            .map(|r| {
                r.layers
                    .iter()
                    .rev()
                    .map(|l| invert_layer(p, l))
                    .collect::<Option<Vec<_>>>()
            })
            .collect();
        if let Some(l) = layers {
            cand.push(Inverse::Layers(l));
        }
        if p.kind == Kind::Feistel && p.block_bits.is_multiple_of(2) {
            cand.push(Inverse::Feistel);
        }
        for c in cand {
            let mut trial = self.clone();
            trial.inverse = c.clone();
            let bb = p.block_bytes();
            let ok = (0..3u8).all(|t| {
                let x: Vec<u8> = (0..bb)
                    .map(|i| (i as u8).wrapping_mul(37).wrapping_add(t.wrapping_mul(101)) ^ 0xA5)
                    .collect();
                trial.try_decrypt(&trial.eval(&x)).as_deref() == Some(&x[..])
            });
            if ok {
                return c;
            }
        }
        Inverse::None
    }
}

fn get_bits_vec(v: &[u64], off: usize, n: usize) -> Vec<u64> {
    let mut out = vec![0u64; words_for(n)];
    let mut done = 0;
    while done < n {
        let take = (n - done).min(64);
        set_bits(&mut out, done, take, get_bits(v, off + done, take));
        done += take;
    }
    out
}

fn put_bits_vec(v: &mut [u64], off: usize, src: &[u64], n: usize) {
    let mut done = 0;
    while done < n {
        let take = (n - done).min(64);
        set_bits(v, off + done, take, get_bits(src, done, take));
        done += take;
    }
}

impl BlockCipher for KeyedPrimitive {
    fn block_bytes(&self) -> usize {
        self.primitive.block_bytes()
    }
    fn encrypt(&self, block: &[u8]) -> Vec<u8> {
        self.eval(block)
    }
    /// Panics if the primitive is not invertible; check
    /// [`KeyedPrimitive::is_invertible`] first.
    fn decrypt(&self, block: &[u8]) -> Vec<u8> {
        self.try_decrypt(block).unwrap_or_else(|| {
            panic!(
                "{}: no decryption (feed-forward or non-invertible layer)",
                self.primitive.name
            )
        })
    }
}

/// Adapter from a [`symmetric::modes::cipher::BlockCipher<N>`](ModesBlockCipher)
/// implementation (in-place fixed-size blocks) to the boomerang
/// [`BlockCipher`] trait (byte vectors).
#[derive(Clone, Debug)]
pub struct ModeCipher<C, const N: usize>(
    /// The wrapped cipher.
    pub C,
);

impl<C: ModesBlockCipher<N>, const N: usize> BlockCipher for ModeCipher<C, N> {
    fn block_bytes(&self) -> usize {
        N
    }
    fn encrypt(&self, block: &[u8]) -> Vec<u8> {
        let mut b: [u8; N] = block.try_into().expect("ModeCipher: wrong block length");
        self.0.encrypt_block(&mut b);
        b.to_vec()
    }
    fn decrypt(&self, block: &[u8]) -> Vec<u8> {
        let mut b: [u8; N] = block.try_into().expect("ModeCipher: wrong block length");
        self.0.decrypt_block(&mut b);
        b.to_vec()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::sym_ir::eval;
    use crate::cryptanalysis::sym_ir::primitives::{aes128, chacha, present80, simon, speck};

    fn blocks(p: &Primitive) -> Vec<Vec<u8>> {
        (0..4u8)
            .map(|t| {
                (0..p.block_bytes())
                    .map(|i| (i as u8).wrapping_mul(29).wrapping_add(t * 71))
                    .collect()
            })
            .collect()
    }

    #[test]
    fn encrypt_matches_eval_and_decrypt_round_trips() {
        for p in [
            aes128::reduced(3, true),
            aes128::aes128(),
            aes128::small_scale(4),
            present80::present80(),
            speck::speck64_128(),
            speck::speck128_256(),
            simon::simon64_128(),
            simon::simon128_256(),
        ] {
            let k = KeyedPrimitive::with_default_key(p.clone());
            assert!(k.is_invertible(), "{} should be invertible", p.name);
            for b in blocks(&p) {
                let c = k.encrypt(&b);
                assert_eq!(c, eval(&p, k.key(), &b), "{}", p.name);
                assert_eq!(k.decrypt(&c), b, "{}", p.name);
            }
        }
    }

    #[test]
    fn feed_forward_primitives_are_not_invertible() {
        for p in [chacha::chacha8(), chacha::reduced_width(16, 8)] {
            let k = KeyedPrimitive::with_default_key(p.clone());
            assert!(!k.is_invertible(), "{}", p.name);
            assert!(k.try_decrypt(&vec![0u8; p.block_bytes()]).is_none());
        }
    }

    #[test]
    fn mode_cipher_adapter_round_trips() {
        use crate::symmetric::aes::AesKey;
        let key = AesKey::new(&[7u8; 16]).unwrap();
        let c = ModeCipher::<_, 16>(key);
        let p = [3u8; 16];
        let e = BlockCipher::encrypt(&c, &p);
        assert_ne!(e, p.to_vec());
        assert_eq!(BlockCipher::decrypt(&c, &e), p.to_vec());
    }
}
