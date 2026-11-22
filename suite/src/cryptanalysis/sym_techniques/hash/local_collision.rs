//! Signed-difference machinery for SHA-2-class step functions and the
//! 9-step SHA-2 local collision.
//!
//! # Generalized conditions
//!
//! A [`Gc`] is a set of allowed *bit pairs* `(x, x')`, where `x` is the bit in
//! message pair member 1 and `x'` in member 2 (de Cannière and Rechberger,
//! "Finding SHA-1 characteristics: general results and applications",
//! ASIACRYPT 2006, generalised conditions; the 16 subsets of the four pairs).
//! Symbols used by [`Gc::symbol`] (this crate's convention; the hexadecimal
//! letters are the subset bitmask with pair `(x, x')` at bit `x + 2x'`):
//!
//! | symbol | pairs | meaning |
//! |---|---|---|
//! | `?` | all four | unconstrained |
//! | `-` | `00, 11` | equal |
//! | `x` | `01, 10` | different |
//! | `0` / `1` | `00` / `11` | equal and fixed |
//! | `u` | `01` | `x = 0`, `x' = 1` (difference `+2^i`) |
//! | `n` | `10` | `x = 1`, `x' = 0` (difference `-2^i`) |
//! | `3 5 7 A B C D E` | other subsets | hexadecimal subset mask |
//! | `#` | none | contradiction |
//!
//! [`GcWord`] is a vector of [`Gc`], one per bit. Propagation through XOR,
//! AND, NOT, rotation, shift, modular addition (an exact carry-state-set
//! propagation), `Ch`, `Maj`, `Sigma` and `sigma`, and one full step
//! ([`step_gc`]) is a forward image: every output bit's set contains every
//! pair reachable from the product of the input sets, and for a single
//! operation on independent bits it is the exact projection (checked by brute
//! force on small words in the tests). Correlations between bits are dropped,
//! so a multi-operation propagation is a sound over-approximation, not the
//! tightest one.
//!
//! # The 9-step local collision
//!
//! Chabaud and Joux (CRYPTO 1998) described local collisions for SHA-0; Gilbert
//! and Handschuh (SAC 2003) and, for step-reduced SHA-256, Mendel, Pramstaller,
//! Rechberger, Kontak and Szmidt (FSE 2006), Nikolic and Biryukov (FSE 2008) and
//! Sanadhya and Sarkar (ACISP 2008) use the SHA-2 analogue: a modular
//! perturbation `+-2^j` in `W_i` makes `a_{i+1}` and `e_{i+1}` differ by the
//! same amount; corrections in the following message words cancel it.
//!
//! **Derivation used here.** Write `a_t`, `e_t` for the registers after step
//! `t-1`. Since `a_{t+1} - e_{t+1} = T2_t - a_{t-3}` and `T2_t` reads only
//! `a_t, a_{t-1}, a_{t-2}`, requiring all eight registers to agree again after
//! step `i+8` forces `Delta a_{t} = 0` for every `t` except `t = i+1`, where
//! `Delta a = +-2^j`. Each correction `Delta W_t` is then determined: choose
//! `W'_t` so that `a'_{t+1}` and `e'_{t+1}` take the forced values
//! ([`solve_corrections`]). The `Delta W_t` are modular differences that
//! depend on the actual register values, so *which* of them vanish is a matter
//! of conditions on those values. Over 3e7 random states and `j = 0`, and over
//! 5e6 with `j = 7`, the support of `(Delta W_i, ..., Delta W_{i+8})` is always
//! a superset of `{i, i+1, i+2, i+3, i+5, i+8}` ([`MIN_SUPPORT`]); that set is
//! reached with frequency about `2^-11`. `Delta W_{i+5}` contains both
//! `Sigma0`-spread and `Sigma1`-spread terms of the perturbation, which no
//! condition on the `Ch`/`Maj` selector bits can cancel, so the five-word
//! pattern `{i, i+1, i+2, i+3, i+8}` is *not* reachable by this local
//! collision (see `no_five_word_support_in_sample`).
//!
//! [`find_local_collision`] samples register values until the minimal support
//! appears, [`observe_characteristic`] collects the generalized conditions
//! that the found solutions satisfy (as the per-bit union of observed pairs,
//! hence empirical, not derived), and [`embed`] turns a local collision into a
//! concrete chaining value and two message blocks that can be run through the
//! IR (`sym_ir::primitives::{sha256_compress, sha512_compress}`).

use crate::hash::sha256 as sha256_ref;
use crate::hash::sha512 as sha512_ref;
use rand::rngs::StdRng;
use rand::{Rng, SeedableRng};
use std::collections::BTreeMap;

// ── Generalized conditions ───────────────────────────────────────────────

/// A set of allowed bit pairs `(x, x')`; bit `x + 2 x'` of the mask is set
/// when the pair is allowed.
#[derive(Clone, Copy, PartialEq, Eq, Hash, Debug)]
pub struct Gc(pub u8);

impl Gc {
    /// No pair (contradiction).
    pub const NONE: Gc = Gc(0);
    /// Any pair (`?`).
    pub const ANY: Gc = Gc(0xF);
    /// `x = x'` (`-`).
    pub const EQ: Gc = Gc(0b1001);
    /// `x != x'` (`x`).
    pub const DIFF: Gc = Gc(0b0110);
    /// The pair `(0, 0)`.
    pub const ZERO: Gc = Gc(0b0001);
    /// The pair `(1, 1)`.
    pub const ONE: Gc = Gc(0b1000);
    /// The pair `(0, 1)` (`u`).
    pub const UP: Gc = Gc(0b0100);
    /// The pair `(1, 0)` (`n`).
    pub const DOWN: Gc = Gc(0b0010);

    fn idx(x: bool, y: bool) -> u8 {
        x as u8 | (y as u8) << 1
    }

    /// The set containing only the pair `(x, y)`.
    pub fn pair(x: bool, y: bool) -> Gc {
        Gc(1 << Self::idx(x, y))
    }

    /// Whether the pair `(x, y)` is allowed.
    pub fn contains(self, x: bool, y: bool) -> bool {
        self.0 >> Self::idx(x, y) & 1 == 1
    }

    /// Whether every pair of `self` is allowed by `other`.
    pub fn subset_of(self, other: Gc) -> bool {
        self.0 & !other.0 == 0
    }

    /// Union of the two sets.
    pub fn union(self, other: Gc) -> Gc {
        Gc(self.0 | other.0)
    }

    /// Intersection of the two sets.
    pub fn intersect(self, other: Gc) -> Gc {
        Gc(self.0 & other.0)
    }

    /// Number of allowed pairs.
    pub fn len(self) -> u32 {
        self.0.count_ones()
    }

    /// Whether no pair is allowed.
    pub fn is_empty(self) -> bool {
        self.0 == 0
    }

    /// The allowed pairs.
    pub fn pairs(self) -> impl Iterator<Item = (bool, bool)> {
        (0..4u8)
            .filter(move |i| self.0 >> i & 1 == 1)
            .map(|i| (i & 1 == 1, i >> 1 & 1 == 1))
    }

    /// The symbol of the table in the module docs.
    pub fn symbol(self) -> char {
        match self.0 {
            0 => '#',
            0xF => '?',
            0b1001 => '-',
            0b0110 => 'x',
            0b0001 => '0',
            0b1000 => '1',
            0b0100 => 'u',
            0b0010 => 'n',
            m => char::from_digit(m as u32, 16).unwrap().to_ascii_uppercase(),
        }
    }

    /// Inverse of [`Gc::symbol`].
    pub fn from_symbol(c: char) -> Option<Gc> {
        (0..16u8).map(Gc).find(|g| g.symbol() == c)
    }

    /// Image of a unary bit function over the allowed pairs.
    pub fn map1(self, f: impl Fn(bool) -> bool) -> Gc {
        let mut m = 0;
        for (x, y) in self.pairs() {
            m |= Gc::pair(f(x), f(y)).0;
        }
        Gc(m)
    }

    /// Image of a binary bit function over the product of two sets.
    pub fn map2(self, other: Gc, f: impl Fn(bool, bool) -> bool) -> Gc {
        let mut m = 0;
        for (x, x2) in self.pairs() {
            for (y, y2) in other.pairs() {
                m |= Gc::pair(f(x, y), f(x2, y2)).0;
            }
        }
        Gc(m)
    }

    /// Image of a ternary bit function over the product of three sets.
    pub fn map3(a: Gc, b: Gc, c: Gc, f: impl Fn(bool, bool, bool) -> bool) -> Gc {
        let mut m = 0;
        for (x, x2) in a.pairs() {
            for (y, y2) in b.pairs() {
                for (z, z2) in c.pairs() {
                    m |= Gc::pair(f(x, y, z), f(x2, y2, z2)).0;
                }
            }
        }
        Gc(m)
    }
}

/// A word of generalized conditions, least significant bit first.
#[derive(Clone, PartialEq, Eq, Debug)]
pub struct GcWord {
    /// One condition per bit.
    pub bits: Vec<Gc>,
}

impl GcWord {
    /// `w` copies of `g`.
    pub fn filled(w: usize, g: Gc) -> GcWord {
        GcWord { bits: vec![g; w] }
    }

    /// Unconstrained word.
    pub fn any(w: usize) -> GcWord {
        Self::filled(w, Gc::ANY)
    }

    /// Both members equal, value unknown.
    pub fn equal(w: usize) -> GcWord {
        Self::filled(w, Gc::EQ)
    }

    /// The constant `v` in both members.
    pub fn constant(v: u64, w: usize) -> GcWord {
        GcWord {
            bits: (0..w)
                .map(|i| Gc::pair((v >> i) & 1 == 1, (v >> i) & 1 == 1))
                .collect(),
        }
    }

    /// The exact pair `(x, y)` of concrete values.
    pub fn from_pair(x: u64, y: u64, w: usize) -> GcWord {
        GcWord {
            bits: (0..w)
                .map(|i| Gc::pair((x >> i) & 1 == 1, (y >> i) & 1 == 1))
                .collect(),
        }
    }

    /// Word width in bits.
    pub fn width(&self) -> usize {
        self.bits.len()
    }

    /// Whether the concrete pair `(x, y)` satisfies every bit condition.
    pub fn contains_pair(&self, x: u64, y: u64) -> bool {
        self.bits
            .iter()
            .enumerate()
            .all(|(i, g)| g.contains((x >> i) & 1 == 1, (y >> i) & 1 == 1))
    }

    /// Whether every bit set is contained in the matching bit set of `other`.
    pub fn subset_of(&self, other: &GcWord) -> bool {
        self.bits
            .iter()
            .zip(&other.bits)
            .all(|(a, b)| a.subset_of(*b))
    }

    /// Bitwise union.
    pub fn union(&self, other: &GcWord) -> GcWord {
        GcWord {
            bits: self
                .bits
                .iter()
                .zip(&other.bits)
                .map(|(a, b)| a.union(*b))
                .collect(),
        }
    }

    /// Symbols, most significant bit first.
    pub fn render(&self) -> String {
        self.bits.iter().rev().map(|g| g.symbol()).collect()
    }

    /// Parse the output of [`GcWord::render`].
    pub fn parse(s: &str) -> Option<GcWord> {
        let mut bits: Vec<Gc> = s.chars().map(Gc::from_symbol).collect::<Option<_>>()?;
        bits.reverse();
        Some(GcWord { bits })
    }
}

fn zip2(a: &GcWord, b: &GcWord, f: impl Fn(bool, bool) -> bool + Copy) -> GcWord {
    assert_eq!(a.width(), b.width());
    GcWord {
        bits: a
            .bits
            .iter()
            .zip(&b.bits)
            .map(|(x, y)| x.map2(*y, f))
            .collect(),
    }
}

/// Bitwise XOR propagation.
pub fn gc_xor(a: &GcWord, b: &GcWord) -> GcWord {
    zip2(a, b, |x, y| x ^ y)
}

/// Bitwise AND propagation.
pub fn gc_and(a: &GcWord, b: &GcWord) -> GcWord {
    zip2(a, b, |x, y| x & y)
}

/// Bitwise NOT propagation.
pub fn gc_not(a: &GcWord) -> GcWord {
    GcWord {
        bits: a.bits.iter().map(|g| g.map1(|x| !x)).collect(),
    }
}

/// Rotate right by `r`.
pub fn gc_rotr(a: &GcWord, r: usize) -> GcWord {
    let w = a.width();
    GcWord {
        bits: (0..w).map(|i| a.bits[(i + r) % w]).collect(),
    }
}

/// Logical shift right by `r` (vacated bits are the constant 0).
pub fn gc_shr(a: &GcWord, r: usize) -> GcWord {
    let w = a.width();
    GcWord {
        bits: (0..w)
            .map(|i| if i + r < w { a.bits[i + r] } else { Gc::ZERO })
            .collect(),
    }
}

/// Modular addition propagation: per bit, the set of carry pairs reachable
/// from lower bits is carried along, so each output bit is the exact
/// projection for independent input bit sets.
pub fn gc_add(a: &GcWord, b: &GcWord) -> GcWord {
    assert_eq!(a.width(), b.width());
    let mut carry = Gc::ZERO;
    let mut out = Vec::with_capacity(a.width());
    for (x, y) in a.bits.iter().zip(&b.bits) {
        let mut s = 0u8;
        let mut c = 0u8;
        for (xa, xb) in x.pairs() {
            for (ya, yb) in y.pairs() {
                for (ca, cb) in carry.pairs() {
                    s |= Gc::pair(xa ^ ya ^ ca, xb ^ yb ^ cb).0;
                    let maj = |p: bool, q: bool, r: bool| (p & q) | (p & r) | (q & r);
                    c |= Gc::pair(maj(xa, ya, ca), maj(xb, yb, cb)).0;
                }
            }
        }
        out.push(Gc(s));
        carry = Gc(c);
    }
    GcWord { bits: out }
}

fn zip3(a: &GcWord, b: &GcWord, c: &GcWord, f: impl Fn(bool, bool, bool) -> bool + Copy) -> GcWord {
    GcWord {
        bits: (0..a.width())
            .map(|i| Gc::map3(a.bits[i], b.bits[i], c.bits[i], f))
            .collect(),
    }
}

/// `Ch(e, f, g) = (e & f) ^ (!e & g)`, propagated jointly per bit.
pub fn gc_ch(e: &GcWord, f: &GcWord, g: &GcWord) -> GcWord {
    zip3(e, f, g, |e, f, g| if e { f } else { g })
}

/// `Maj(a, b, c)`, propagated jointly per bit.
pub fn gc_maj(a: &GcWord, b: &GcWord, c: &GcWord) -> GcWord {
    zip3(a, b, c, |a, b, c| (a & b) | (a & c) | (b & c))
}

// ── SHA-2 parameters, concrete step function ─────────────────────────────

/// Word size, rotation amounts and round constants of a SHA-2 family member.
#[derive(Clone, Debug)]
pub struct Sha2Params {
    /// Name for reports.
    pub name: &'static str,
    /// Word width in bits.
    pub w: usize,
    /// `Sigma0` rotation amounts.
    pub big0: [usize; 3],
    /// `Sigma1` rotation amounts.
    pub big1: [usize; 3],
    /// `sigma0`: two rotations and a shift.
    pub small0: [usize; 3],
    /// `sigma1`: two rotations and a shift.
    pub small1: [usize; 3],
    /// Round constants `K_t`.
    pub k: Vec<u64>,
}

impl Sha2Params {
    /// SHA-256 (FIPS 180-4).
    pub fn sha256() -> Self {
        Sha2Params {
            name: "SHA-256",
            w: 32,
            big0: [2, 13, 22],
            big1: [6, 11, 25],
            small0: [7, 18, 3],
            small1: [17, 19, 10],
            k: sha256_ref::K.iter().map(|&k| k as u64).collect(),
        }
    }

    /// SHA-512 (FIPS 180-4).
    pub fn sha512() -> Self {
        Sha2Params {
            name: "SHA-512",
            w: 64,
            big0: [28, 34, 39],
            big1: [14, 18, 41],
            small0: [1, 8, 7],
            small1: [19, 61, 6],
            k: sha512_ref::K.to_vec(),
        }
    }

    /// Word mask.
    pub fn mask(&self) -> u64 {
        if self.w == 64 {
            u64::MAX
        } else {
            (1u64 << self.w) - 1
        }
    }

    fn rotr(&self, x: u64, r: usize) -> u64 {
        ((x >> r) | (x << (self.w - r))) & self.mask()
    }

    /// `Sigma0`.
    pub fn sigma0_big(&self, x: u64) -> u64 {
        let [a, b, c] = self.big0;
        self.rotr(x, a) ^ self.rotr(x, b) ^ self.rotr(x, c)
    }

    /// `Sigma1`.
    pub fn sigma1_big(&self, x: u64) -> u64 {
        let [a, b, c] = self.big1;
        self.rotr(x, a) ^ self.rotr(x, b) ^ self.rotr(x, c)
    }

    /// Message-schedule `sigma0`.
    pub fn sigma0_small(&self, x: u64) -> u64 {
        let [a, b, s] = self.small0;
        self.rotr(x, a) ^ self.rotr(x, b) ^ (x >> s)
    }

    /// Message-schedule `sigma1`.
    pub fn sigma1_small(&self, x: u64) -> u64 {
        let [a, b, s] = self.small1;
        self.rotr(x, a) ^ self.rotr(x, b) ^ (x >> s)
    }

    /// `Ch`.
    pub fn ch(&self, e: u64, f: u64, g: u64) -> u64 {
        ((e & f) ^ (!e & g)) & self.mask()
    }

    /// `Maj`.
    pub fn maj(&self, a: u64, b: u64, c: u64) -> u64 {
        (a & b) ^ (a & c) ^ (b & c)
    }

    fn add(&self, x: u64, y: u64) -> u64 {
        x.wrapping_add(y) & self.mask()
    }

    fn sub(&self, x: u64, y: u64) -> u64 {
        x.wrapping_sub(y) & self.mask()
    }

    /// One compression step on `(a, b, c, d, e, f, g, h)`.
    pub fn step(&self, s: &[u64; 8], w: u64, k: u64) -> [u64; 8] {
        let t1 = self.add(
            self.add(
                self.add(
                    self.add(s[7], self.sigma1_big(s[4])),
                    self.ch(s[4], s[5], s[6]),
                ),
                k,
            ),
            w,
        );
        let t2 = self.add(self.sigma0_big(s[0]), self.maj(s[0], s[1], s[2]));
        [
            self.add(t1, t2),
            s[0],
            s[1],
            s[2],
            self.add(s[3], t1),
            s[4],
            s[5],
            s[6],
        ]
    }

    /// Inverse of [`Sha2Params::step`] for known `w`, `k`.
    pub fn step_inverse(&self, s: &[u64; 8], w: u64, k: u64) -> [u64; 8] {
        let (a, b, c) = (s[1], s[2], s[3]);
        let (e, f, g) = (s[5], s[6], s[7]);
        let t2 = self.add(self.sigma0_big(a), self.maj(a, b, c));
        let t1 = self.sub(s[0], t2);
        let d = self.sub(s[4], t1);
        let h = self.sub(
            self.sub(
                self.sub(self.sub(t1, self.sigma1_big(e)), self.ch(e, f, g)),
                k,
            ),
            w,
        );
        [a, b, c, d, e, f, g, h]
    }

    /// The message schedule `W_0..W_{n-1}` of a 16-word block.
    pub fn expand(&self, block: &[u64; 16], n: usize) -> Vec<u64> {
        let mut w: Vec<u64> = block.to_vec();
        for t in 16..n {
            let v = self.add(
                self.add(self.sigma1_small(w[t - 2]), w[t - 7]),
                self.add(self.sigma0_small(w[t - 15]), w[t - 16]),
            );
            w.push(v);
        }
        w.truncate(n);
        w
    }
}

// ── Generalized-condition propagation of steps and of the schedule ───────

fn gc_rot_xor3(x: &GcWord, r: [usize; 3]) -> GcWord {
    gc_xor(
        &gc_xor(&gc_rotr(x, r[0]), &gc_rotr(x, r[1])),
        &gc_rotr(x, r[2]),
    )
}

/// `Sigma0` propagation.
pub fn gc_big_sigma0(p: &Sha2Params, x: &GcWord) -> GcWord {
    gc_rot_xor3(x, p.big0)
}

/// `Sigma1` propagation.
pub fn gc_big_sigma1(p: &Sha2Params, x: &GcWord) -> GcWord {
    gc_rot_xor3(x, p.big1)
}

/// Message-schedule `sigma0` propagation.
pub fn gc_small_sigma0(p: &Sha2Params, x: &GcWord) -> GcWord {
    let [a, b, s] = p.small0;
    gc_xor(&gc_xor(&gc_rotr(x, a), &gc_rotr(x, b)), &gc_shr(x, s))
}

/// Message-schedule `sigma1` propagation.
pub fn gc_small_sigma1(p: &Sha2Params, x: &GcWord) -> GcWord {
    let [a, b, s] = p.small1;
    gc_xor(&gc_xor(&gc_rotr(x, a), &gc_rotr(x, b)), &gc_shr(x, s))
}

/// Propagate generalized conditions through one compression step.
pub fn step_gc(p: &Sha2Params, st: &[GcWord; 8], w: &GcWord, k: u64) -> [GcWord; 8] {
    let kw = GcWord::constant(k, p.w);
    let s1 = gc_big_sigma1(p, &st[4]);
    let chv = gc_ch(&st[4], &st[5], &st[6]);
    let t1 = gc_add(&gc_add(&gc_add(&gc_add(&st[7], &s1), &chv), &kw), w);
    let s0 = gc_big_sigma0(p, &st[0]);
    let mj = gc_maj(&st[0], &st[1], &st[2]);
    let t2 = gc_add(&s0, &mj);
    [
        gc_add(&t1, &t2),
        st[0].clone(),
        st[1].clone(),
        st[2].clone(),
        gc_add(&st[3], &t1),
        st[4].clone(),
        st[5].clone(),
        st[6].clone(),
    ]
}

/// Propagate conditions on the 16 block words through the message schedule
/// to `n` words.
pub fn gc_expand(p: &Sha2Params, block: &[GcWord; 16], n: usize) -> Vec<GcWord> {
    let mut w: Vec<GcWord> = block.to_vec();
    for t in 16..n {
        let a = gc_small_sigma1(p, &w[t - 2]);
        let b = gc_small_sigma0(p, &w[t - 15]);
        let v = gc_add(&gc_add(&a, &w[t - 7]), &gc_add(&b, &w[t - 16]));
        w.push(v);
    }
    w.truncate(n);
    w
}

// ── The local collision ──────────────────────────────────────────────────

/// Number of steps spanned by the local collision.
pub const LOCAL_COLLISION_STEPS: usize = 9;

/// The smallest message-difference support observed: offsets `0, 1, 2, 3, 5,
/// 8` from the perturbed step (see the module docs).
pub const MIN_SUPPORT: [bool; LOCAL_COLLISION_STEPS] =
    [true, true, true, true, false, true, false, false, true];

/// Where and how the local collision is injected.
#[derive(Clone, Copy, Debug)]
pub struct LocalCollisionSpec {
    /// Step index `i` of the perturbed message word `W_i`.
    pub start: usize,
    /// Bit position `j` of the perturbation.
    pub bit: usize,
    /// `true` for `+2^j`, `false` for `-2^j`.
    pub positive: bool,
}

/// A concrete local collision: register values before step `start` and the
/// two message-word sequences `W_i..W_{i+8}`, `W'_i..W'_{i+8}`.
#[derive(Clone, Debug)]
pub struct LocalCollision {
    /// Parameters used.
    pub params: Sha2Params,
    /// Injection point.
    pub spec: LocalCollisionSpec,
    /// `(a..h)` before step `start`, equal in both members.
    pub state: [u64; 8],
    /// Message words of member 1 at steps `start..start+9`.
    pub w: [u64; 9],
    /// Message words of member 2.
    pub w2: [u64; 9],
    /// Modular differences `W'_t - W_t`.
    pub delta_w: [u64; 9],
    /// Random states tried by the search that produced this solution.
    pub trials: u64,
}

impl LocalCollision {
    /// Which of the nine message differences are nonzero.
    pub fn support(&self) -> [bool; LOCAL_COLLISION_STEPS] {
        std::array::from_fn(|t| self.delta_w[t] != 0)
    }

    /// Register values before each of the steps `start..=start+9`, for the
    /// two members.
    pub fn trace(&self) -> Vec<([u64; 8], [u64; 8])> {
        let p = &self.params;
        let (mut s1, mut s2) = (self.state, self.state);
        let mut out = vec![(s1, s2)];
        for t in 0..LOCAL_COLLISION_STEPS {
            let k = p.k[self.spec.start + t];
            s1 = p.step(&s1, self.w[t], k);
            s2 = p.step(&s2, self.w2[t], k);
            out.push((s1, s2));
        }
        out
    }
}

/// One forced correction: given both members' registers before step `t` and
/// member 1's message word, the word `W'` that makes
/// `a' = a_next (+ perturbation if first)` and `e' = a' - T2' + d'`.
fn solve_correction(
    p: &Sha2Params,
    spec: &LocalCollisionSpec,
    first: bool,
    s1_next_a: u64,
    s2: &[u64; 8],
    k: u64,
) -> u64 {
    let delta = if spec.positive {
        1u64 << spec.bit
    } else {
        (1u64 << spec.bit).wrapping_neg() & p.mask()
    };
    let at = if first {
        p.add(s1_next_a, delta)
    } else {
        s1_next_a
    };
    let t2p = p.add(p.sigma0_big(s2[0]), p.maj(s2[0], s2[1], s2[2]));
    let e_next = p.add(p.sub(at, t2p), s2[3]);
    let t1p = p.sub(e_next, s2[3]);
    p.sub(
        p.sub(
            p.sub(p.sub(t1p, s2[7]), p.sigma1_big(s2[4])),
            p.ch(s2[4], s2[5], s2[6]),
        ),
        k,
    )
}

/// Given register values before step `spec.start` and the member-1 message
/// words, compute the forced member-2 words (the "corrections") so that
/// `Delta a = +-2^j` at step `start + 1` only; returns `W'` for the nine
/// steps. After step `start + 8` both members' registers agree.
pub fn solve_corrections(
    p: &Sha2Params,
    spec: &LocalCollisionSpec,
    state: [u64; 8],
    w: &[u64; 9],
) -> [u64; 9] {
    let (mut s1, mut s2) = (state, state);
    let mut w2 = [0u64; 9];
    for t in 0..LOCAL_COLLISION_STEPS {
        let k = p.k[spec.start + t];
        let n1 = p.step(&s1, w[t], k);
        w2[t] = solve_correction(p, spec, t == 0, n1[0], &s2, k);
        s1 = n1;
        s2 = p.step(&s2, w2[t], k);
    }
    debug_assert_eq!(s1, s2);
    w2
}

/// Search random register values for a local collision whose message
/// difference support equals [`MIN_SUPPORT`], giving up after `max_trials`
/// states.
pub fn find_local_collision(
    p: &Sha2Params,
    spec: LocalCollisionSpec,
    seed: u64,
    max_trials: u64,
) -> Option<LocalCollision> {
    let mut rng = StdRng::seed_from_u64(seed);
    let mask = p.mask();
    'trial: for trial in 1..=max_trials {
        let state: [u64; 8] = std::array::from_fn(|_| rng.gen::<u64>() & mask);
        let (mut s1, mut s2) = (state, state);
        let mut w = [0u64; 9];
        let mut w2 = [0u64; 9];
        let mut dw = [0u64; 9];
        for t in 0..LOCAL_COLLISION_STEPS {
            let k = p.k[spec.start + t];
            w[t] = rng.gen::<u64>() & mask;
            let n1 = p.step(&s1, w[t], k);
            w2[t] = solve_correction(p, &spec, t == 0, n1[0], &s2, k);
            dw[t] = p.sub(w2[t], w[t]);
            if (dw[t] != 0) != MIN_SUPPORT[t] {
                continue 'trial;
            }
            s1 = n1;
            s2 = p.step(&s2, w2[t], k);
        }
        debug_assert_eq!(s1, s2);
        return Some(LocalCollision {
            params: p.clone(),
            spec,
            state,
            w,
            w2,
            delta_w: dw,
            trials: trial,
        });
    }
    None
}

/// Histogram of message-difference supports (bit `t` of the key set iff
/// `Delta W_{i+t} != 0`) over `samples` random register values, with no early
/// exit.
pub fn support_histogram(
    p: &Sha2Params,
    spec: LocalCollisionSpec,
    samples: u64,
    seed: u64,
) -> BTreeMap<u16, u64> {
    let mut rng = StdRng::seed_from_u64(seed);
    let mask = p.mask();
    let mut hist = BTreeMap::new();
    for _ in 0..samples {
        let state: [u64; 8] = std::array::from_fn(|_| rng.gen::<u64>() & mask);
        let w: [u64; 9] = std::array::from_fn(|_| rng.gen::<u64>() & mask);
        let w2 = solve_corrections(p, &spec, state, &w);
        let m = (0..9).fold(0u16, |m, t| m | ((w2[t] != w[t]) as u16) << t);
        *hist.entry(m).or_insert(0) += 1;
    }
    hist
}

// ── Observed characteristic (generalized conditions) ─────────────────────

/// Generalized conditions observed over a set of local collisions: the
/// per-bit union of the `(member 1, member 2)` bit pairs.
#[derive(Clone, Debug)]
pub struct Characteristic {
    /// Parameters used.
    pub params: Sha2Params,
    /// Injection point.
    pub spec: LocalCollisionSpec,
    /// Register conditions before steps `start..=start+9`.
    pub regs: Vec<[GcWord; 8]>,
    /// Message-word conditions at steps `start..start+9`.
    pub w: Vec<GcWord>,
    /// Number of local collisions merged.
    pub solutions: usize,
}

/// A bit whose observed condition is a single pair, i.e. a value (or
/// difference) that every observed solution had in common.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct BitCondition {
    /// Index `t` of the step the register is read before (`start + t`).
    pub offset: usize,
    /// Register index `0..8` for `a..h`.
    pub register: usize,
    /// Bit position.
    pub bit: usize,
    /// The observed condition.
    pub gc: Gc,
}

impl Characteristic {
    /// Bits whose observed condition is one pair, except where both members
    /// hold the same bit but the sample did not fix it (those read `-`, not a
    /// single pair).
    pub fn conditions(&self) -> Vec<BitCondition> {
        let mut out = Vec::new();
        for (t, regs) in self.regs.iter().enumerate() {
            for (r, wd) in regs.iter().enumerate() {
                for (b, g) in wd.bits.iter().enumerate() {
                    if g.len() == 1 {
                        out.push(BitCondition {
                            offset: t,
                            register: r,
                            bit: b,
                            gc: *g,
                        });
                    }
                }
            }
        }
        out
    }

    /// Human-readable table: one line per step and register (MSB first).
    pub fn render(&self) -> String {
        let names = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
        let mut s = String::new();
        for (t, regs) in self.regs.iter().enumerate() {
            for (r, wd) in regs.iter().enumerate() {
                s += &format!(
                    "step {:>2} {}: {}\n",
                    self.spec.start + t,
                    names[r],
                    wd.render()
                );
            }
            if t < self.w.len() {
                s += &format!(
                    "step {:>2} W: {}\n",
                    self.spec.start + t,
                    self.w[t].render()
                );
            }
        }
        s
    }

    /// Check that propagating the conditions of each step through
    /// [`step_gc`] gives sets containing the observed conditions of the next
    /// step; returns the number of bits where the propagated set is strictly
    /// larger (the looseness of the propagation), or `None` if containment
    /// fails.
    pub fn propagation_looseness(&self) -> Option<usize> {
        let p = &self.params;
        let mut loose = 0;
        for t in 0..LOCAL_COLLISION_STEPS {
            let out = step_gc(p, &self.regs[t], &self.w[t], p.k[self.spec.start + t]);
            for r in 0..8 {
                if !self.regs[t + 1][r].subset_of(&out[r]) {
                    return None;
                }
                loose += self.regs[t + 1][r]
                    .bits
                    .iter()
                    .zip(&out[r].bits)
                    .filter(|(a, b)| a != b)
                    .count();
            }
        }
        Some(loose)
    }
}

/// Collect `solutions` local collisions (distinct seeds derived from `seed`)
/// and merge their per-bit pairs into a [`Characteristic`].
pub fn observe_characteristic(
    p: &Sha2Params,
    spec: LocalCollisionSpec,
    solutions: usize,
    seed: u64,
) -> Characteristic {
    let w = p.w;
    let mut regs: Vec<[GcWord; 8]> = vec![std::array::from_fn(|_| GcWord::filled(w, Gc::NONE)); 10];
    let mut wc: Vec<GcWord> = vec![GcWord::filled(w, Gc::NONE); 9];
    for n in 0..solutions {
        let lc = find_local_collision(p, spec, seed.wrapping_add(n as u64 * 0x9e37_79b9), u64::MAX)
            .expect("unbounded search");
        for (t, (s1, s2)) in lc.trace().iter().enumerate() {
            for r in 0..8 {
                regs[t][r] = regs[t][r].union(&GcWord::from_pair(s1[r], s2[r], w));
            }
        }
        for t in 0..9 {
            wc[t] = wc[t].union(&GcWord::from_pair(lc.w[t], lc.w2[t], w));
        }
    }
    Characteristic {
        params: p.clone(),
        spec,
        regs,
        w: wc,
        solutions,
    }
}

// ── Embedding into a compression-function instance ───────────────────────

/// A concrete pair for the IR: a shared chaining value and two message
/// blocks, as big-endian byte strings in the layout of
/// `sym_ir::primitives::{sha256_compress, sha512_compress}` (block =
/// chaining value, key = message block).
#[derive(Clone, Debug)]
pub struct EmbeddedPair {
    /// Chaining value `a..h`.
    pub chaining: Vec<u8>,
    /// Message block 1.
    pub m1: Vec<u8>,
    /// Message block 2.
    pub m2: Vec<u8>,
    /// Message words of member 1.
    pub words1: [u64; 16],
    /// Message words of member 2.
    pub words2: [u64; 16],
}

fn be_bytes(words: &[u64], w: usize) -> Vec<u8> {
    words
        .iter()
        .flat_map(|x| x.to_be_bytes()[8 - w / 8..].to_vec())
        .collect()
}

/// Build the chaining value and message blocks for a local collision that
/// starts at step `start`: the steps before it use random words common to
/// both members, run backwards from `lc.state` to the chaining value; words
/// `W_start..W_{start+8}` come from the collision; the remaining words
/// (indices `< 16`) are random and common. Requires `start + 9 <= 16`.
pub fn embed(lc: &LocalCollision, seed: u64) -> EmbeddedPair {
    let p = &lc.params;
    let i = lc.spec.start;
    assert!(
        i + LOCAL_COLLISION_STEPS <= 16,
        "collision words must lie in W_0..W_15"
    );
    let mut rng = StdRng::seed_from_u64(seed);
    let mask = p.mask();
    let mut w1: [u64; 16] = std::array::from_fn(|_| rng.gen::<u64>() & mask);
    let mut w2 = w1;
    w1[i..i + 9].copy_from_slice(&lc.w);
    w2[i..i + 9].copy_from_slice(&lc.w2);
    let mut st = lc.state;
    for t in (0..i).rev() {
        st = p.step_inverse(&st, w1[t], p.k[t]);
    }
    EmbeddedPair {
        chaining: be_bytes(&st, p.w),
        m1: be_bytes(&w1, p.w),
        m2: be_bytes(&w2, p.w),
        words1: w1,
        words2: w2,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::sym_ir::eval;
    use crate::cryptanalysis::sym_ir::primitives::{sha256_compress, sha512_compress};
    use std::time::Instant;

    fn all_gc() -> impl Iterator<Item = Gc> {
        (1..16u8).map(Gc)
    }

    #[test]
    fn symbols_round_trip_and_are_distinct() {
        let mut seen = std::collections::HashSet::new();
        for g in (0..16u8).map(Gc) {
            assert!(seen.insert(g.symbol()), "duplicate symbol");
            assert_eq!(Gc::from_symbol(g.symbol()), Some(g));
        }
        assert_eq!(Gc::EQ.symbol(), '-');
        assert_eq!(Gc::UP.symbol(), 'u');
        assert_eq!(Gc::DOWN.symbol(), 'n');
        let w = GcWord::parse("-u?x01n").unwrap();
        assert_eq!(w.render(), "-u?x01n");
    }

    /// Enumerate every concrete pair of values consistent with `gc` words of
    /// width `w` and return the exact set of output pairs of `f`, as a
    /// per-bit [`Gc`].
    fn brute_binary(a: &GcWord, b: &GcWord, f: impl Fn(u64, u64) -> u64) -> GcWord {
        let w = a.width();
        let pairs = |g: &GcWord| -> Vec<(u64, u64)> {
            let mut v = vec![(0u64, 0u64)];
            for (i, bit) in g.bits.iter().enumerate() {
                let mut nv = Vec::new();
                for (x, y) in &v {
                    for (bx, by) in bit.pairs() {
                        nv.push((x | (bx as u64) << i, y | (by as u64) << i));
                    }
                }
                v = nv;
            }
            v
        };
        let mut out = vec![Gc::NONE; w];
        for (x, x2) in pairs(a) {
            for (y, y2) in pairs(b) {
                let (r, r2) = (f(x, y), f(x2, y2));
                for (i, o) in out.iter_mut().enumerate() {
                    *o = o.union(Gc::pair((r >> i) & 1 == 1, (r2 >> i) & 1 == 1));
                }
            }
        }
        GcWord { bits: out }
    }

    fn rand_gcword(r: &mut StdRng, w: usize) -> GcWord {
        let gs: Vec<Gc> = all_gc().collect();
        GcWord {
            bits: (0..w).map(|_| gs[r.gen_range(0..gs.len())]).collect(),
        }
    }

    #[test]
    fn xor_and_add_propagation_equal_the_exact_projection_width4() {
        let mut r = StdRng::seed_from_u64(7);
        for _ in 0..150 {
            let a = rand_gcword(&mut r, 4);
            let b = rand_gcword(&mut r, 4);
            assert_eq!(gc_xor(&a, &b), brute_binary(&a, &b, |x, y| x ^ y), "xor");
            assert_eq!(gc_and(&a, &b), brute_binary(&a, &b, |x, y| x & y), "and");
            assert_eq!(
                gc_add(&a, &b),
                brute_binary(&a, &b, |x, y| (x + y) & 0xf),
                "add {} {}",
                a.render(),
                b.render()
            );
        }
    }

    #[test]
    fn ch_maj_rotr_shr_not_are_exact_on_independent_bits() {
        let mut r = StdRng::seed_from_u64(8);
        for _ in 0..40 {
            let (a, b, c) = (
                rand_gcword(&mut r, 3),
                rand_gcword(&mut r, 3),
                rand_gcword(&mut r, 3),
            );
            // Ch and Maj act bitwise, so check bit by bit against map3.
            let ch = gc_ch(&a, &b, &c);
            let mj = gc_maj(&a, &b, &c);
            for i in 0..3 {
                assert_eq!(
                    ch.bits[i],
                    Gc::map3(a.bits[i], b.bits[i], c.bits[i], |e, f, g| (e & f)
                        ^ (!e & g))
                );
                assert_eq!(
                    mj.bits[i],
                    Gc::map3(a.bits[i], b.bits[i], c.bits[i], |x, y, z| (x & y)
                        | (x & z)
                        | (y & z))
                );
            }
            assert_eq!(gc_rotr(&a, 1).bits[0], a.bits[1]);
            assert_eq!(gc_shr(&a, 1).bits[2], Gc::ZERO);
            assert_eq!(gc_not(&gc_not(&a)), a);
        }
    }

    /// Soundness of the one-step propagation on real SHA-256/SHA-512 steps:
    /// random per-bit conditions, concrete pairs drawn inside them.
    #[test]
    fn step_gc_is_sound_on_random_conforming_pairs() {
        for p in [Sha2Params::sha256(), Sha2Params::sha512()] {
            let mut r = StdRng::seed_from_u64(9);
            let gs: Vec<Gc> = all_gc().collect();
            for trial in 0..400 {
                // Mostly-narrow sets so that the propagated sets are informative.
                let pick = |r: &mut StdRng| -> Gc {
                    if trial % 2 == 0 {
                        gs[r.gen_range(0..gs.len())]
                    } else {
                        [Gc::EQ, Gc::EQ, Gc::UP, Gc::DOWN, Gc::ZERO, Gc::ONE][r.gen_range(0..6)]
                    }
                };
                let st: [GcWord; 8] = std::array::from_fn(|_| GcWord {
                    bits: (0..p.w).map(|_| pick(&mut r)).collect(),
                });
                let wg = GcWord {
                    bits: (0..p.w).map(|_| pick(&mut r)).collect(),
                };
                let draw = |g: &GcWord, r: &mut StdRng| -> (u64, u64) {
                    let (mut x, mut y) = (0u64, 0u64);
                    for (i, bit) in g.bits.iter().enumerate() {
                        let ps: Vec<_> = bit.pairs().collect();
                        let (a, b) = ps[r.gen_range(0..ps.len())];
                        x |= (a as u64) << i;
                        y |= (b as u64) << i;
                    }
                    (x, y)
                };
                let mut s1 = [0u64; 8];
                let mut s2 = [0u64; 8];
                for i in 0..8 {
                    (s1[i], s2[i]) = draw(&st[i], &mut r);
                }
                let (w1, w2) = draw(&wg, &mut r);
                let k = p.k[trial % 16];
                let out = step_gc(&p, &st, &wg, k);
                let n1 = p.step(&s1, w1, k);
                let n2 = p.step(&s2, w2, k);
                for i in 0..8 {
                    assert!(
                        out[i].contains_pair(n1[i], n2[i]),
                        "{} reg {i}: {} lacks ({:x},{:x})",
                        p.name,
                        out[i].render(),
                        n1[i],
                        n2[i]
                    );
                }
            }
        }
    }

    #[test]
    fn step_inverse_inverts_step() {
        for p in [Sha2Params::sha256(), Sha2Params::sha512()] {
            let mut r = StdRng::seed_from_u64(10);
            for t in 0..20 {
                let s: [u64; 8] = std::array::from_fn(|_| r.gen::<u64>() & p.mask());
                let w = r.gen::<u64>() & p.mask();
                let n = p.step(&s, w, p.k[t]);
                assert_eq!(p.step_inverse(&n, w, p.k[t]), s);
            }
        }
    }

    #[test]
    fn corrections_always_close_the_local_collision() {
        let p = Sha2Params::sha256();
        let mut r = StdRng::seed_from_u64(11);
        for j in [0usize, 5, 31] {
            for positive in [true, false] {
                let spec = LocalCollisionSpec {
                    start: 2,
                    bit: j,
                    positive,
                };
                for _ in 0..200 {
                    let st: [u64; 8] = std::array::from_fn(|_| r.gen::<u64>() & p.mask());
                    let w: [u64; 9] = std::array::from_fn(|_| r.gen::<u64>() & p.mask());
                    let w2 = solve_corrections(&p, &spec, st, &w);
                    let (mut a, mut b) = (st, st);
                    for t in 0..9 {
                        a = p.step(&a, w[t], p.k[2 + t]);
                        b = p.step(&b, w2[t], p.k[2 + t]);
                    }
                    assert_eq!(a, b);
                    assert_eq!(
                        w2[0],
                        p.add(
                            w[0],
                            if positive {
                                1 << j
                            } else {
                                (1u64 << j).wrapping_neg() & p.mask()
                            }
                        )
                    );
                }
            }
        }
    }

    /// Positive control: nine-step SHA-256 local collision at several
    /// positions and bits, found, and each pair run through the IR.
    #[test]
    fn sha256_nine_step_local_collision_through_the_ir() {
        let p = Sha2Params::sha256();
        for (start, bit, positive) in [(0usize, 0usize, true), (3, 7, false), (7, 31, true)] {
            let spec = LocalCollisionSpec {
                start,
                bit,
                positive,
            };
            let t0 = Instant::now();
            let lc = find_local_collision(&p, spec, 1, 1 << 24).expect("local collision");
            let dt = t0.elapsed();
            assert_eq!(lc.support(), MIN_SUPPORT);
            let nz: Vec<usize> = (0..9).filter(|&t| lc.delta_w[t] != 0).collect();
            assert_eq!(nz, vec![0, 1, 2, 3, 5, 8]);
            let want = if positive {
                1u64 << bit
            } else {
                (1u64 << bit).wrapping_neg() & p.mask()
            };
            assert_eq!(lc.delta_w[0], want);
            let e = embed(&lc, 5);
            assert_ne!(e.m1, e.m2);
            // differences outside the nine words are zero
            for t in 0..16 {
                if t < start || t >= start + 9 {
                    assert_eq!(e.words1[t], e.words2[t]);
                }
            }
            let n = start + 9;
            let prim = sha256_compress::steps(n);
            let (o1, o2) = (
                eval(&prim, &e.m1, &e.chaining),
                eval(&prim, &e.m2, &e.chaining),
            );
            assert_eq!(o1, o2, "IR outputs of steps({n}) must collide");
            // one step fewer: not yet a collision
            let short = sha256_compress::steps(n - 1);
            assert_ne!(
                eval(&short, &e.m1, &e.chaining),
                eval(&short, &e.m2, &e.chaining)
            );
            eprintln!(
                "local collision start={start} bit={bit} sign={} trials={} time={dt:?} dW={:x?}",
                if positive { '+' } else { '-' },
                lc.trials,
                lc.delta_w
            );
        }
    }

    #[test]
    fn sha512_nine_step_local_collision_through_the_ir() {
        let p = Sha2Params::sha512();
        let spec = LocalCollisionSpec {
            start: 2,
            bit: 40,
            positive: true,
        };
        let lc = find_local_collision(&p, spec, 3, 1 << 26).expect("local collision");
        assert_eq!(lc.support(), MIN_SUPPORT);
        let e = embed(&lc, 6);
        let prim = sha512_compress::steps(2 + 9);
        assert_eq!(
            eval(&prim, &e.m1, &e.chaining),
            eval(&prim, &e.m2, &e.chaining)
        );
        assert_ne!(e.m1, e.m2);
    }

    /// In a sample, offsets 0, 1, 2, 5 and 8 are always nonzero, so the
    /// five-word pattern (offset 5 zero) is absent.
    #[test]
    fn no_five_word_support_in_sample() {
        let p = Sha2Params::sha256();
        let spec = LocalCollisionSpec {
            start: 0,
            bit: 0,
            positive: true,
        };
        let hist = support_histogram(&p, spec, 1 << 21, 12);
        let min_mask: u16 = [0, 1, 2, 5, 8].iter().fold(0, |m, &t| m | 1 << t);
        assert!(!hist.is_empty());
        for (&m, &c) in &hist {
            assert_eq!(
                m & min_mask,
                min_mask,
                "support {m:09b} (count {c}) lacks one of offsets 0,1,2,5,8"
            );
        }
        assert!(
            !hist.contains_key(&0b1_0000_1111),
            "five-word pattern reached"
        );
        eprintln!("support histogram (LSB = offset 0): {hist:?}");
    }

    /// The empirical characteristic is consistent with `step_gc` and has
    /// fixed-bit conditions.
    #[test]
    fn observed_characteristic_is_propagation_consistent() {
        let p = Sha2Params::sha256();
        let spec = LocalCollisionSpec {
            start: 0,
            bit: 0,
            positive: true,
        };
        let t0 = Instant::now();
        let ch = observe_characteristic(&p, spec, 200, 77);
        let dt = t0.elapsed();
        let loose = ch
            .propagation_looseness()
            .expect("propagation must contain observations");
        let conds = ch.conditions();
        // the perturbation itself: a_1 and e_1 differ at bit 0
        // (the modular +1 flips bit 0 in either direction, hence `x`)
        for reg in [0usize, 4] {
            assert_eq!(ch.regs[1][reg].bits[0], Gc::DIFF, "register {reg}");
            assert!(ch.regs[1][reg].bits[1..].iter().all(|g| g.len() >= 2));
        }
        assert_eq!(ch.regs[0][0].bits[0], Gc::EQ);
        eprintln!(
            "characteristic from 200 solutions in {dt:?}: {} single-pair bits, propagation looseness {loose} bits\n{}",
            conds.len(),
            ch.render()
        );
    }

    /// The placement analysis in `semi_free_start` relies on this: conditions
    /// on the message words propagate through the schedule.
    #[test]
    fn gc_schedule_keeps_equal_words_equal() {
        let p = Sha2Params::sha256();
        let w = p.w;
        let mut block: [GcWord; 16] = std::array::from_fn(|_| GcWord::equal(w));
        let out = gc_expand(&p, &block, 40);
        assert!(out.iter().all(|x| *x == GcWord::equal(w)));
        block[3] = GcWord::any(w);
        let out = gc_expand(&p, &block, 40);
        assert_eq!(
            out[16],
            GcWord::equal(w),
            "W_16 reads W_14, W_9, W_1, W_0 only"
        );
        assert_ne!(out[18], GcWord::equal(w), "W_18 reads W_3");
    }
}
