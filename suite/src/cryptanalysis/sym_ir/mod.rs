//! # `sym_ir` — a structural intermediate representation of symmetric
//! primitives
//!
//! Work package WP0 of `docs/plans/2026-11-21-generic-symmetric-cryptanalysis.md`
//! (section 2.1). A [`Primitive`] describes a block cipher, permutation or
//! hash compression function as a list of [`Round`]s, each a list of
//! [`Layer`]s (S-box layer, GF(2)-linear layer, bit permutation, ARX word
//! operations, round-key addition, constant addition), plus a
//! [`KeySchedule`]. [`eval`] / [`eval_rounds`] interpret that description
//! directly, with no per-cipher code, so that later technique libraries can
//! read the same structure.
//!
//! The IR is a description, not a claim about any cipher's security. Every
//! description in [`primitives`] is checked bit-for-bit against the existing
//! implementation in `symmetric/`, `hash/` or `cryptanalysis/` by the tests
//! in this module's `tests` submodule.
//!
//! ## Bit ordering
//!
//! * A *bit-vector* is a `Vec<u64>`: bit `i` is bit `i % 64` of word
//!   `i / 64` (see [`gf2`]).
//! * The working state has `block_bits + scratch_bits` bits. Bits
//!   `0..block_bits` are the block; the scratch bits (initially zero, not
//!   part of the output) give ARX layers temporaries.
//! * A [`Codec`] maps a byte string to bits: the string is cut into words
//!   of `word_bits` bits (a multiple of 8) taken in order; word `j` occupies
//!   state bits `j*word_bits .. (j+1)*word_bits`, and within a word the
//!   bytes are read little- or big-endian, bit `k` of the word being bit `k`
//!   of that integer. For a byte-oriented cipher (AES) the codec is
//!   `{word_bits: 8}`; for PRESENT it is one big-endian 64-bit word.
//! * S-box `j` of a [`Layer::SboxParallel`] reads state bits
//!   `bit_offset + j*width .. + width`, least-significant bit first.
//! * [`Layer::Permute`] with `perm`: output bit `i` = input bit `perm[i]`.
//! * ARX registers are the `word_bits`-wide words of the state, register
//!   `r` being bits `r*word_bits .. (r+1)*word_bits`.
//!
//! ## Rounds
//!
//! `rounds` lists the rounds in order, including any initial key whitening
//! (it sits in round 1) and the final-round variation (the last round simply
//! omits layers). [`eval_rounds`]`(p, key, block, n)` runs the first `n`
//! entries of `rounds` and then the feed-forward, so a reduced-round view of
//! a primitive is "its first `n` rounds exactly as described", which for
//! AES and ToySpn means the cut round keeps its own layers rather than
//! being replaced by the final-round form. The `reduced` constructors in
//! [`primitives`] build the final-round form explicitly.
//!
//! ## Deviations from the sketch in the plan
//!
//! The sketch lists the type names only. To make the types evaluable the
//! variants carry the data they need (`bit_offset`, `word_bits`, key-state
//! description), [`Primitive`] additionally holds the S-box tables, the
//! block/key [`Codec`]s, `scratch_bits` and a [`FeedForward`] (the
//! Davies-Meyer / ChaCha final addition), and [`ArxOp`] is a register
//! machine over words with `And`, `Shr`, `Copy` and constant/round-key
//! operands in addition to `Add`, `Rotl`, `Xor`, because Simon, SHA-256
//! and the key schedules need them.

pub mod gf2;
pub mod primitives;

#[cfg(test)]
mod tests;

pub use gf2::Gf2Matrix;

use crate::cryptanalysis::sbox::Sbox;
use gf2::{get_bit, get_bits, set_bit, set_bits, words_for};

/// Index of an S-box in [`Primitive::sboxes`].
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct SboxId(pub usize);

/// Structural family of a primitive; used to decide which techniques apply.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum Kind {
    /// Substitution-permutation network (AES, PRESENT, ToySpn).
    Spn,
    /// Feistel network (Simon).
    Feistel,
    /// Add-rotate-xor design (Speck, SHA-256 compression).
    Arx,
    /// Unkeyed permutation, possibly with a feed-forward (ChaCha core).
    Permutation,
}

/// Byte-string to bit-vector convention; see the [module docs](self).
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Codec {
    /// Width of one word in bits; a multiple of 8.
    pub word_bits: usize,
    /// Whether the bytes of one word are most-significant first.
    pub big_endian: bool,
}

impl Codec {
    /// Plain bytes: `word_bits = 8`, byte `i` is state bits `8i..8i+8`.
    pub const BYTES: Codec = Codec {
        word_bits: 8,
        big_endian: false,
    };

    /// Words of `word_bits` bits, little-endian inside each word.
    pub const fn little(word_bits: usize) -> Codec {
        Codec {
            word_bits,
            big_endian: false,
        }
    }

    /// Words of `word_bits` bits, big-endian inside each word.
    pub const fn big(word_bits: usize) -> Codec {
        Codec {
            word_bits,
            big_endian: true,
        }
    }

    /// Position, within the whole bit string, of bit 0 of byte `i`.
    fn byte_bit_pos(&self, i: usize) -> usize {
        let wb = self.word_bits / 8;
        let (j, b) = (i / wb, i % wb);
        let within = if self.big_endian { wb - 1 - b } else { b };
        j * self.word_bits + 8 * within
    }

    /// Encode `bytes` into a bit-vector of `bytes.len() * 8` bits.
    pub fn encode(&self, bytes: &[u8]) -> Vec<u64> {
        assert!(self.word_bits.is_multiple_of(8) && self.word_bits > 0);
        assert!(
            (bytes.len() * 8).is_multiple_of(self.word_bits),
            "byte string is not a whole number of words"
        );
        let mut out = vec![0u64; words_for(bytes.len() * 8)];
        for (i, &b) in bytes.iter().enumerate() {
            set_bits(&mut out, self.byte_bit_pos(i), 8, b as u64);
        }
        out
    }

    /// Decode the first `bits` bits of a bit-vector into bytes.
    pub fn decode(&self, v: &[u64], bits: usize) -> Vec<u8> {
        assert!(bits.is_multiple_of(8) && bits.is_multiple_of(self.word_bits));
        (0..bits / 8)
            .map(|i| get_bits(v, self.byte_bit_pos(i), 8) as u8)
            .collect()
    }
}

/// One word-level operation of an [`Layer::Arx`] layer.
///
/// Operands `dst`, `a`, `b`, `src` are register numbers (words of the state,
/// see the [module docs](self)); all arithmetic is modulo `2^word_bits` of
/// the enclosing layer. Operations run in order and may overwrite their own
/// operands.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ArxOp {
    /// `dst = a + b mod 2^w`.
    Add {
        /// Destination register.
        dst: usize,
        /// First operand register.
        a: usize,
        /// Second operand register.
        b: usize,
    },
    /// `dst = src <<< k` (rotate left by `k mod w`).
    Rotl {
        /// Destination register.
        dst: usize,
        /// Source register.
        src: usize,
        /// Rotation amount in bits.
        k: usize,
    },
    /// `dst = a XOR b`.
    Xor {
        /// Destination register.
        dst: usize,
        /// First operand register.
        a: usize,
        /// Second operand register.
        b: usize,
    },
    /// `dst = a AND b`.
    And {
        /// Destination register.
        dst: usize,
        /// First operand register.
        a: usize,
        /// Second operand register.
        b: usize,
    },
    /// `dst = src >> k` (logical shift right, zero fill).
    Shr {
        /// Destination register.
        dst: usize,
        /// Source register.
        src: usize,
        /// Shift amount in bits.
        k: usize,
    },
    /// `dst = src`.
    Copy {
        /// Destination register.
        dst: usize,
        /// Source register.
        src: usize,
    },
    /// `dst ^= value` (low `w` bits of `value`).
    XorConst {
        /// Destination register.
        dst: usize,
        /// Constant.
        value: u64,
    },
    /// `dst = dst + value mod 2^w`.
    AddConst {
        /// Destination register.
        dst: usize,
        /// Constant.
        value: u64,
    },
    /// `dst ^= W` where `W` is word number `word` of round key `round_key`.
    XorKey {
        /// Destination register.
        dst: usize,
        /// Round-key index.
        round_key: usize,
        /// Word index inside the round key (words of the layer's width).
        word: usize,
    },
    /// `dst = dst + W mod 2^w`, `W` as for [`ArxOp::XorKey`].
    AddKey {
        /// Destination register.
        dst: usize,
        /// Round-key index.
        round_key: usize,
        /// Word index inside the round key.
        word: usize,
    },
}

/// One layer of a [`Round`].
#[derive(Clone, Debug, PartialEq)]
pub enum Layer {
    /// `count` parallel copies of one S-box on adjacent `width_bits`-bit
    /// fields starting at state bit `bit_offset`.
    SboxParallel {
        /// Which S-box in [`Primitive::sboxes`].
        sbox: SboxId,
        /// Input (and output) width of one S-box in bits.
        width_bits: usize,
        /// Number of S-boxes.
        count: usize,
        /// First state bit of the first S-box.
        bit_offset: usize,
    },
    /// Multiply the whole state by a square GF(2) matrix.
    LinearGf2 {
        /// `(block_bits + scratch_bits)`-square matrix.
        matrix: Gf2Matrix,
    },
    /// Bit permutation of the whole state: output bit `i` = input bit `perm[i]`.
    Permute {
        /// The permutation, a bijection on `0..state_bits`.
        perm: Vec<usize>,
    },
    /// Word-level ARX register machine.
    Arx {
        /// Width of one register in bits (at most 64).
        word_bits: usize,
        /// Operations, executed in order.
        ops: Vec<ArxOp>,
    },
    /// XOR round key `round_key` (all `round_key_bits` bits) into the state
    /// starting at `bit_offset`.
    AddRoundKey {
        /// Round-key index.
        round_key: usize,
        /// First state bit that receives key bit 0.
        bit_offset: usize,
    },
    /// XOR the low `bits` bits of `value` into the state at `bit_offset`.
    AddConst {
        /// First state bit.
        bit_offset: usize,
        /// Number of constant bits (at most 64).
        bits: usize,
        /// The constant.
        value: u64,
    },
}

/// A round: layers applied in order.
#[derive(Clone, Debug, PartialEq)]
pub struct Round {
    /// The layers of this round.
    pub layers: Vec<Layer>,
}

/// How round keys are derived from the master key.
#[derive(Clone, Debug, PartialEq)]
pub enum KeySchedule {
    /// The master key is the concatenation of `round_keys` round keys of
    /// `round_key_bits` bits each (so `key_bits = round_keys * round_key_bits`).
    Independent {
        /// Number of round keys.
        round_keys: usize,
        /// Width of one round key.
        round_key_bits: usize,
    },
    /// All round keys, concatenated, are `matrix * key` (GF(2)-linear in the
    /// key). `matrix` has `cols = key_bits` and `rows = round_keys *
    /// round_key_bits`.
    Linear {
        /// The expansion matrix.
        matrix: Gf2Matrix,
        /// Width of one round key.
        round_key_bits: usize,
    },
    /// A key register of `state_bits` bits is loaded with the master key at
    /// bit 0 (remaining bits zero) and updated by `steps` in turn. Round key
    /// `i` is bits `extract_offset .. extract_offset + round_key_bits` of
    /// the register after `i` updates, so there are `steps.len() + 1` round
    /// keys. Layers inside `steps` use the same semantics as in rounds,
    /// except that [`Layer::AddRoundKey`] and the key operands of
    /// [`ArxOp`] are not allowed.
    Nonlinear {
        /// Width of the key register (master key plus scratch).
        state_bits: usize,
        /// One update per round key after the first.
        steps: Vec<Vec<Layer>>,
        /// First register bit of the extracted round key.
        extract_offset: usize,
        /// Width of one round key.
        round_key_bits: usize,
    },
}

impl KeySchedule {
    /// Width of one round key in bits.
    pub fn round_key_bits(&self) -> usize {
        match self {
            KeySchedule::Independent { round_key_bits, .. }
            | KeySchedule::Linear { round_key_bits, .. }
            | KeySchedule::Nonlinear { round_key_bits, .. } => *round_key_bits,
        }
    }

    /// Number of round keys the schedule produces.
    pub fn num_round_keys(&self) -> usize {
        match self {
            KeySchedule::Independent { round_keys, .. } => *round_keys,
            KeySchedule::Linear {
                matrix,
                round_key_bits,
            } => matrix.rows().checked_div(*round_key_bits).unwrap_or(0),
            KeySchedule::Nonlinear { steps, .. } => steps.len() + 1,
        }
    }
}

/// Final addition of the input block to the output (Davies-Meyer, ChaCha).
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum FeedForward {
    /// No feed-forward: output is the final state.
    None,
    /// Output = final state XOR initial block.
    Xor,
    /// Output = final state + initial block, word-wise modulo
    /// `2^word_bits`, words laid out as in the state.
    AddWords {
        /// Word width in bits (at most 64).
        word_bits: usize,
    },
}

/// A symmetric primitive described structurally.
#[derive(Clone, Debug)]
pub struct Primitive {
    /// Human-readable name, e.g. `"AES-128"` or `"ChaCha20"`.
    pub name: String,
    /// Block (state) width in bits.
    pub block_bits: usize,
    /// Master-key width in bits (0 for unkeyed permutations).
    pub key_bits: usize,
    /// Extra zero-initialised state bits appended after the block, used as
    /// ARX temporaries; not part of the output.
    pub scratch_bits: usize,
    /// How block bytes map to state bits.
    pub block_codec: Codec,
    /// How key bytes map to key bits.
    pub key_codec: Codec,
    /// S-box tables referenced by [`SboxId`].
    pub sboxes: Vec<Sbox>,
    /// The rounds, in order.
    pub rounds: Vec<Round>,
    /// Round-key derivation.
    pub key_schedule: KeySchedule,
    /// Final feed-forward.
    pub feed_forward: FeedForward,
    /// Structural family.
    pub kind: Kind,
}

impl Primitive {
    /// Block size in bytes.
    pub fn block_bytes(&self) -> usize {
        self.block_bits / 8
    }

    /// Key size in bytes.
    pub fn key_bytes(&self) -> usize {
        self.key_bits / 8
    }

    /// Number of rounds in the description.
    pub fn num_rounds(&self) -> usize {
        self.rounds.len()
    }

    /// Total state width: block plus scratch.
    pub fn state_bits(&self) -> usize {
        self.block_bits + self.scratch_bits
    }

    /// Check internal consistency (dimensions, indices). Returns a message
    /// naming the first problem found.
    pub fn validate(&self) -> Result<(), String> {
        let sb = self.state_bits();
        for (what, c, bits) in [
            ("block", self.block_codec, self.block_bits),
            ("key", self.key_codec, self.key_bits),
        ] {
            if c.word_bits == 0
                || !c.word_bits.is_multiple_of(8)
                || !bits.is_multiple_of(c.word_bits)
            {
                return Err(format!("{what} codec does not tile {bits} bits"));
            }
        }
        let nrk = self.key_schedule.num_round_keys();
        let rkb = self.key_schedule.round_key_bits();
        for (ri, r) in self.rounds.iter().enumerate() {
            for l in &r.layers {
                self.validate_layer(l, sb, Some((nrk, rkb)))
                    .map_err(|e| format!("round {}: {e}", ri + 1))?;
            }
        }
        match &self.key_schedule {
            KeySchedule::Independent {
                round_keys,
                round_key_bits,
            } => {
                if round_keys * round_key_bits != self.key_bits {
                    return Err("independent schedule: key_bits mismatch".into());
                }
            }
            KeySchedule::Linear { matrix, .. } => {
                if matrix.cols() != self.key_bits {
                    return Err("linear schedule: matrix cols != key_bits".into());
                }
            }
            KeySchedule::Nonlinear {
                state_bits,
                steps,
                extract_offset,
                round_key_bits,
            } => {
                if *state_bits < self.key_bits || extract_offset + round_key_bits > *state_bits {
                    return Err("nonlinear schedule: register too small".into());
                }
                for (i, s) in steps.iter().enumerate() {
                    for l in s {
                        self.validate_layer(l, *state_bits, None)
                            .map_err(|e| format!("key step {}: {e}", i + 1))?;
                    }
                }
            }
        }
        match self.feed_forward {
            FeedForward::AddWords { word_bits }
                if word_bits == 0 || !self.block_bits.is_multiple_of(word_bits) =>
            {
                Err("feed-forward word width does not tile the block".into())
            }
            _ => Ok(()),
        }
    }

    fn validate_layer(
        &self,
        l: &Layer,
        state_bits: usize,
        keys: Option<(usize, usize)>,
    ) -> Result<(), String> {
        match l {
            Layer::SboxParallel {
                sbox,
                width_bits,
                count,
                bit_offset,
            } => {
                let s = self.sboxes.get(sbox.0).ok_or("unknown S-box id")?;
                if s.n_in() as usize != *width_bits || s.n_out() as usize != *width_bits {
                    return Err("S-box width mismatch".into());
                }
                if bit_offset + width_bits * count > state_bits {
                    return Err("S-box layer out of range".into());
                }
            }
            Layer::LinearGf2 { matrix } => {
                if matrix.rows() != state_bits || matrix.cols() != state_bits {
                    return Err("linear layer is not state-square".into());
                }
            }
            Layer::Permute { perm } => {
                let mut seen = vec![false; state_bits];
                if perm.len() != state_bits {
                    return Err("permutation length != state bits".into());
                }
                for &p in perm {
                    if p >= state_bits || std::mem::replace(&mut seen[p], true) {
                        return Err("not a permutation".into());
                    }
                }
            }
            Layer::Arx { word_bits, ops } => {
                if *word_bits == 0 || *word_bits > 64 || !state_bits.is_multiple_of(*word_bits) {
                    return Err("ARX word width does not tile the state".into());
                }
                let regs = state_bits / word_bits;
                for op in ops {
                    let (rs, key): (Vec<usize>, Option<(usize, usize)>) = match *op {
                        ArxOp::Add { dst, a, b }
                        | ArxOp::Xor { dst, a, b }
                        | ArxOp::And { dst, a, b } => (vec![dst, a, b], None),
                        ArxOp::Rotl { dst, src, .. }
                        | ArxOp::Shr { dst, src, .. }
                        | ArxOp::Copy { dst, src } => (vec![dst, src], None),
                        ArxOp::XorConst { dst, .. } | ArxOp::AddConst { dst, .. } => {
                            (vec![dst], None)
                        }
                        ArxOp::XorKey {
                            dst,
                            round_key,
                            word,
                        }
                        | ArxOp::AddKey {
                            dst,
                            round_key,
                            word,
                        } => (vec![dst], Some((round_key, word))),
                    };
                    if rs.iter().any(|&r| r >= regs) {
                        return Err("ARX register out of range".into());
                    }
                    if let Some((rk, word)) = key {
                        let (n, bits) = keys.ok_or("round-key operand in key schedule")?;
                        if rk >= n || (word + 1) * word_bits > bits {
                            return Err("ARX round-key operand out of range".into());
                        }
                    }
                }
            }
            Layer::AddRoundKey {
                round_key,
                bit_offset,
            } => {
                let (n, bits) = keys.ok_or("AddRoundKey in key schedule")?;
                if *round_key >= n || bit_offset + bits > state_bits {
                    return Err("AddRoundKey out of range".into());
                }
            }
            Layer::AddConst {
                bit_offset, bits, ..
            } => {
                if *bits > 64 || bit_offset + bits > state_bits {
                    return Err("AddConst out of range".into());
                }
            }
        }
        Ok(())
    }
}

// ── Evaluation ───────────────────────────────────────────────────────────

fn mask_w(w: usize) -> u64 {
    if w == 64 {
        u64::MAX
    } else {
        (1u64 << w) - 1
    }
}

fn rotl_w(x: u64, k: usize, w: usize) -> u64 {
    let k = k % w;
    if k == 0 {
        x
    } else {
        ((x << k) | (x >> (w - k))) & mask_w(w)
    }
}

fn extract_bits(v: &[u64], off: usize, n: usize) -> Vec<u64> {
    let mut out = vec![0u64; words_for(n)];
    let mut done = 0;
    while done < n {
        let take = (n - done).min(64);
        set_bits(&mut out, done, take, get_bits(v, off + done, take));
        done += take;
    }
    out
}

fn xor_bits_into(state: &mut [u64], off: usize, src: &[u64], n: usize) {
    let mut done = 0;
    while done < n {
        let take = (n - done).min(64);
        let cur = get_bits(state, off + done, take);
        set_bits(state, off + done, take, cur ^ get_bits(src, done, take));
        done += take;
    }
}

/// Apply one layer to `state`. `rks` are the already-expanded round keys
/// (empty inside the key schedule, where key operands are rejected).
fn apply_layer(layer: &Layer, state: &mut Vec<u64>, sboxes: &[Sbox], rks: &[Vec<u64>], rkb: usize) {
    match layer {
        Layer::SboxParallel {
            sbox,
            width_bits,
            count,
            bit_offset,
        } => {
            let s = &sboxes[sbox.0];
            for j in 0..*count {
                let off = bit_offset + j * width_bits;
                let x = get_bits(state, off, *width_bits) as u32;
                set_bits(state, off, *width_bits, s.lookup(x) as u64);
            }
        }
        Layer::LinearGf2 { matrix } => {
            *state = matrix.mul_vec(state);
        }
        Layer::Permute { perm } => {
            let mut out = vec![0u64; state.len()];
            for (i, &p) in perm.iter().enumerate() {
                if get_bit(state, p) {
                    set_bit(&mut out, i, true);
                }
            }
            *state = out;
        }
        Layer::Arx { word_bits, ops } => apply_arx(state, *word_bits, ops, rks),
        Layer::AddRoundKey {
            round_key,
            bit_offset,
        } => {
            xor_bits_into(state, *bit_offset, &rks[*round_key], rkb);
        }
        Layer::AddConst {
            bit_offset,
            bits,
            value,
        } => {
            let cur = get_bits(state, *bit_offset, *bits);
            set_bits(state, *bit_offset, *bits, cur ^ value);
        }
    }
}

fn apply_arx(state: &mut [u64], w: usize, ops: &[ArxOp], rks: &[Vec<u64>]) {
    let m = mask_w(w);
    let rd = |s: &[u64], r: usize| get_bits(s, r * w, w);
    for op in ops {
        let (dst, v) = match *op {
            ArxOp::Add { dst, a, b } => (dst, rd(state, a).wrapping_add(rd(state, b)) & m),
            ArxOp::Rotl { dst, src, k } => (dst, rotl_w(rd(state, src), k, w)),
            ArxOp::Xor { dst, a, b } => (dst, rd(state, a) ^ rd(state, b)),
            ArxOp::And { dst, a, b } => (dst, rd(state, a) & rd(state, b)),
            ArxOp::Shr { dst, src, k } => (dst, if k >= w { 0 } else { rd(state, src) >> k }),
            ArxOp::Copy { dst, src } => (dst, rd(state, src)),
            ArxOp::XorConst { dst, value } => (dst, (rd(state, dst) ^ value) & m),
            ArxOp::AddConst { dst, value } => (dst, rd(state, dst).wrapping_add(value) & m),
            ArxOp::XorKey {
                dst,
                round_key,
                word,
            } => (dst, rd(state, dst) ^ get_bits(&rks[round_key], word * w, w)),
            ArxOp::AddKey {
                dst,
                round_key,
                word,
            } => (
                dst,
                rd(state, dst).wrapping_add(get_bits(&rks[round_key], word * w, w)) & m,
            ),
        };
        set_bits(state, dst * w, w, v);
    }
}

/// Expand `key` into the first `count` round keys. Each round key is a
/// bit-vector of [`KeySchedule::round_key_bits`] bits. Panics if the key has
/// the wrong length or `count` exceeds the number of round keys.
pub fn expand_key_count(p: &Primitive, key: &[u8], count: usize) -> Vec<Vec<u64>> {
    assert_eq!(
        key.len() * 8,
        p.key_bits,
        "{}: key must be {} bytes",
        p.name,
        p.key_bits / 8
    );
    assert!(count <= p.key_schedule.num_round_keys());
    let kbits = p.key_codec.encode(key);
    let rkb = p.key_schedule.round_key_bits();
    match &p.key_schedule {
        KeySchedule::Independent { .. } => (0..count)
            .map(|i| extract_bits(&kbits, i * rkb, rkb))
            .collect(),
        KeySchedule::Linear { matrix, .. } => {
            let all = matrix.mul_vec(&kbits);
            (0..count)
                .map(|i| extract_bits(&all, i * rkb, rkb))
                .collect()
        }
        KeySchedule::Nonlinear {
            state_bits,
            steps,
            extract_offset,
            ..
        } => {
            let mut st = vec![0u64; words_for(*state_bits)];
            st[..kbits.len()].copy_from_slice(&kbits);
            let mut out = Vec::with_capacity(count);
            for i in 0..count {
                if i > 0 {
                    for l in &steps[i - 1] {
                        apply_layer(l, &mut st, &p.sboxes, &[], 0);
                    }
                }
                out.push(extract_bits(&st, *extract_offset, rkb));
            }
            out
        }
    }
}

/// Expand `key` into all round keys of the primitive (see
/// [`expand_key_count`]).
pub fn expand_key(p: &Primitive, key: &[u8]) -> Vec<Vec<u64>> {
    expand_key_count(p, key, p.key_schedule.num_round_keys())
}

/// Highest round-key index referenced by the first `n` rounds, plus one.
fn round_keys_needed(p: &Primitive, n: usize) -> usize {
    let mut need = 0;
    for r in &p.rounds[..n] {
        for l in &r.layers {
            match l {
                Layer::AddRoundKey { round_key, .. } => need = need.max(round_key + 1),
                Layer::Arx { ops, .. } => {
                    for op in ops {
                        if let ArxOp::XorKey { round_key, .. } | ArxOp::AddKey { round_key, .. } =
                            op
                        {
                            need = need.max(round_key + 1);
                        }
                    }
                }
                _ => {}
            }
        }
    }
    need
}

/// Evaluate the first `n` rounds of `p` on `block` under `key`, then apply
/// the feed-forward. Derived only from the IR. Panics if `n` exceeds the
/// number of rounds or the byte lengths are wrong.
pub fn eval_rounds(p: &Primitive, key: &[u8], block: &[u8], n: usize) -> Vec<u8> {
    assert!(
        n <= p.rounds.len(),
        "{}: only {} rounds",
        p.name,
        p.rounds.len()
    );
    assert_eq!(
        block.len() * 8,
        p.block_bits,
        "{}: block must be {} bytes",
        p.name,
        p.block_bytes()
    );
    let rks = expand_key_count(p, key, round_keys_needed(p, n));
    let rkb = p.key_schedule.round_key_bits();
    let init = p.block_codec.encode(block);
    let mut state = vec![0u64; words_for(p.state_bits())];
    state[..init.len()].copy_from_slice(&init);
    for r in &p.rounds[..n] {
        for l in &r.layers {
            apply_layer(l, &mut state, &p.sboxes, &rks, rkb);
        }
    }
    match p.feed_forward {
        FeedForward::None => {}
        FeedForward::Xor => xor_bits_into(&mut state, 0, &init, p.block_bits),
        FeedForward::AddWords { word_bits: w } => {
            for j in 0..p.block_bits / w {
                let s = get_bits(&state, j * w, w);
                let i = get_bits(&init, j * w, w);
                set_bits(&mut state, j * w, w, s.wrapping_add(i) & mask_w(w));
            }
        }
    }
    p.block_codec.decode(&state, p.block_bits)
}

/// Evaluate all rounds of `p`: encryption for a cipher, the compression or
/// block function for a hash or permutation primitive.
pub fn eval(p: &Primitive, key: &[u8], block: &[u8]) -> Vec<u8> {
    eval_rounds(p, key, block, p.rounds.len())
}
