//! # Symbolic Weil descent at four or more summands, and past 64 variables.
//!
//! [`pq_descent_symbolic`](crate::cryptanalysis::pq_descent_symbolic)
//! expands `S_3` and `S_4` over linear forms in the boolean ring
//! `F_{2^n}[v]/(v² − v)`, with one 64-bit mask per monomial.  It stops at
//! three summands and at `m·n' ≤ 64` variables.  This module lifts both
//! caps and leaves that module as the fast case it already is.
//!
//! - **Any number of summands.**  `S_{m+1}` comes from Semaev's resultant
//!   recursion, evaluated in the boolean ring.  Characteristic 2 and the
//!   quadratic `S_3` give a closed form that needs no Sylvester
//!   determinant.  For a polynomial `P(Z) = Σ_{i ≤ d} p_i Z^i` and a
//!   quadratic `Q(Z) = A Z² + B Z + C`,
//!
//!   ```text
//!   Res_Z(P, Q) = Σ_i p_i² C^i A^{d−i} + Σ_{i<j} p_i p_j C^i A^{d−j} s_{j−i},
//!   s_1 = B,  s_2 = B²,  s_k = B s_{k−1} + A C s_{k−2},
//!   ```
//!
//!   where `s_k` is `A^k` times the `k`-th power sum of `Q`'s roots, and
//!   `s_0 = 1 + 1 = 0` explains why no `i = j` cross term appears.  At
//!   `d = 2` this is term for term the `S_4` resultant
//!   [`semaev_s4_word`](crate::cryptanalysis::pq_descent_symbolic::semaev_s4_word)
//!   evaluates.
//! - **A wider mask.**  The ring is generic over a [`BoolMask`] (`u64` or
//!   `u128`), so a descent with `64 < m·n' ≤ 128` variables can be built.
//!   The repository's solvers take 64-bit masks, so a wide descent is a
//!   [`WideDescent`] of its own: it can be evaluated, lifted and narrowed,
//!   but no `SystemSolver` takes it as is.
//!
//! ## Two engines, one polynomial
//!
//! [`Engine::Naive`] is the reference.  It runs the left-to-right chain
//! `S_{k+2}(x_1, …, x_{k+1}, Z) = Res_Y(S_{k+1}(x_1, …, x_k, Y), S_3(x_{k+1}, Z, Y))`
//! with hashed products throughout and evaluates the result at `Z = x_R`.
//!
//! [`Engine::Tensor`] is the specialised path, and the default.  It splits
//! `S_{m+1}(x_1, …, x_m, x_R) = Res_Z(S_3(x_1, x_2, Z), S_m(x_R, x_3, …, x_m, Z))`,
//! so the quadratic `Q` lives on blocks 1–2 only and every `p_i` lives on
//! blocks 3…m only.  Each summand of the closed form is then a product of
//! two polynomials on **disjoint** variables: a tensor product, with no
//! collisions inside one product.  The engine indexes the block-1/2 factors
//! once, transposes the block-3…m factors, and accumulates each output row
//! in a dense buffer.  That replaces the hash-map multiply-accumulate that
//! dominates the naive engine.  The inner chain steps use the same
//! tensor routine.
//!
//! Both engines compute the same polynomial over `F_{2^n}`.  `S_{m+1}` is
//! symmetric and the resultant of two quadratics is symmetric in
//! characteristic 2, so the two associations agree.  A boolean function
//! has a unique algebraic normal form, so the two descents agree monomial
//! for monomial.  The tests check that, and also check both engines
//! against a truth-table descent and against the existing fast path at
//! `m = 2, 3`.
//!
//! ## Caps
//!
//! The descent is bounded by the variable count (`m·n' ≤ 64` narrow,
//! `≤ 128` wide) and by [`field_monomial_bound`].  The bound is the
//! largest number of monomials `S_{m+1}` can have over `m` blocks of `n'`
//! variables: per block the boolean degree is at most
//! `max wt(e ≤ 2^{m−1}) = m − 1`.  A descent whose bound exceeds
//! [`MAX_FIELD_MONOMIAL_BOUND`] is refused rather than started.

use std::collections::HashMap;
use std::fmt::Debug;
use std::hash::{BuildHasherDefault, Hash, Hasher};
use std::ops::{BitAnd, BitOr};

use crate::cryptanalysis::pq_descent_symbolic::{self as narrow, SymbolicDescent};
use crate::cryptanalysis::pq_groebner_f2::{F2BoolMono, F2BoolPoly};
use crate::cryptanalysis::semaev_decomp::Gf2;

/// The most summands this module descends.  Above this, `S_{m+1}` has a
/// monomial bound above [`MAX_FIELD_MONOMIAL_BOUND`] already at `n' = 3`.
pub const MAX_SUMMANDS: u32 = 6;

/// The largest [`field_monomial_bound`] a descent may have before it is
/// refused: `2^22` field monomials, about 100 MB of hash map at worst.
pub const MAX_FIELD_MONOMIAL_BOUND: u64 = 1 << 22;

/// Which construction of `S_{m+1}` to run.  Both return the same descent;
/// see the module documentation.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Engine {
    /// Balanced split, disjoint-block tensor accumulation.  The default.
    Tensor,
    /// Left chain with hashed products, evaluated at `x_R`: the reference.
    Naive,
}

// ── Masks ──────────────────────────────────────────────────────────

/// A monomial mask: bit `k` set iff `v_k` divides the monomial.
pub trait BoolMask:
    Copy
    + Eq
    + Ord
    + Hash
    + Default
    + Debug
    + BitOr<Output = Self>
    + BitAnd<Output = Self>
    + Send
    + Sync
    + 'static
{
    /// The number of variables the mask holds.
    const BITS: u32;
    /// The mask with only bit `i` set.
    fn bit(i: u32) -> Self;
    /// The boolean degree of the monomial.
    fn degree(self) -> u32;
    /// Whether every variable of `self` is in `point`.
    fn within(self, point: Self) -> bool {
        self & point == self
    }
}

impl BoolMask for u64 {
    const BITS: u32 = 64;
    #[inline]
    fn bit(i: u32) -> Self {
        1u64 << i
    }
    #[inline]
    fn degree(self) -> u32 {
        self.count_ones()
    }
}

impl BoolMask for u128 {
    const BITS: u32 = 128;
    #[inline]
    fn bit(i: u32) -> Self {
        1u128 << i
    }
    #[inline]
    fn degree(self) -> u32 {
        self.count_ones()
    }
}

/// The splitmix64 finaliser over each 64-bit word of a mask, as
/// `fx_hash::MaskHasher` does for one word.  A `u128` key mixes its low
/// word first, then the high word into the result.
#[derive(Default, Clone, Copy)]
pub struct WideMaskHasher(u64);

impl Hasher for WideMaskHasher {
    #[inline]
    fn finish(&self) -> u64 {
        self.0
    }

    fn write(&mut self, bytes: &[u8]) {
        for chunk in bytes.chunks(8) {
            let mut w = [0u8; 8];
            w[..chunk.len()].copy_from_slice(chunk);
            self.write_u64(u64::from_le_bytes(w));
        }
    }

    #[inline]
    fn write_u64(&mut self, value: u64) {
        let mut mixed = (self.0 ^ value).wrapping_add(0x9e3779b97f4a7c15);
        mixed = (mixed ^ (mixed >> 30)).wrapping_mul(0xbf58476d1ce4e5b9);
        mixed = (mixed ^ (mixed >> 27)).wrapping_mul(0x94d049bb133111eb);
        self.0 = mixed ^ (mixed >> 31);
    }

    #[inline]
    fn write_u128(&mut self, value: u128) {
        self.write_u64(value as u64);
        self.write_u64((value >> 64) as u64);
    }
}

type TermMap<M> = HashMap<M, u64, BuildHasherDefault<WideMaskHasher>>;

// ── F_{2^n}[v] / (v² − v), generic over the mask ───────────────────

/// A polynomial over `F_{2^n}` in boolean variables: monomial mask to
/// non-zero coefficient.  Every operation accumulates by XOR, so the
/// map's iteration order never reaches a result.
#[derive(Clone, Debug, Default)]
pub struct Ring<M: BoolMask> {
    terms: TermMap<M>,
}

impl<M: BoolMask> Ring<M> {
    /// The constant `c`.
    pub fn constant(c: u64) -> Self {
        let mut p = Self::default();
        p.add_term(M::default(), c);
        p
    }

    /// The linear form `Σ_k v_{offset + k} · basis[k]`.
    pub fn linear(offset: u32, basis: &[u64]) -> Self {
        let mut p = Self::default();
        for (k, &e) in basis.iter().enumerate() {
            p.add_term(M::bit(offset + k as u32), e);
        }
        p
    }

    #[inline]
    fn add_term(&mut self, mask: M, coeff: u64) {
        if coeff == 0 {
            return;
        }
        match self.terms.entry(mask) {
            std::collections::hash_map::Entry::Occupied(mut e) => {
                *e.get_mut() ^= coeff;
                if *e.get() == 0 {
                    e.remove();
                }
            }
            std::collections::hash_map::Entry::Vacant(e) => {
                e.insert(coeff);
            }
        }
    }

    /// `self += other`.
    pub fn add_assign(&mut self, other: &Self) {
        for (&m, &c) in &other.terms {
            self.add_term(m, c);
        }
    }

    pub fn add(&self, other: &Self) -> Self {
        let mut out = self.clone();
        out.add_assign(other);
        out
    }

    /// `M · N = M ∪ N`.
    pub fn mul(&self, other: &Self, gf: &Gf2) -> Self {
        let (small, large) = if self.len() <= other.len() {
            (self, other)
        } else {
            (other, self)
        };
        let mut out = Self::default();
        for (&ma, &ca) in &small.terms {
            for (&mb, &cb) in &large.terms {
                out.add_term(ma | mb, gf.mul(ca, cb));
            }
        }
        out
    }

    /// `(Σ c_M M)² = Σ c_M² M`.
    pub fn sqr(&self, gf: &Gf2) -> Self {
        Self {
            terms: self.terms.iter().map(|(&m, &c)| (m, gf.sqr(c))).collect(),
        }
    }

    pub fn scale(&self, c: u64, gf: &Gf2) -> Self {
        if c == 0 {
            return Self::default();
        }
        Self {
            terms: self
                .terms
                .iter()
                .map(|(&m, &a)| (m, gf.mul(a, c)))
                .collect(),
        }
    }

    pub fn len(&self) -> usize {
        self.terms.len()
    }

    pub fn is_empty(&self) -> bool {
        self.terms.is_empty()
    }

    /// The union of the variables any term uses.
    pub fn support(&self) -> M {
        self.terms.keys().fold(M::default(), |acc, &m| acc | m)
    }

    /// Evaluate at a point of `{0,1}^vars`, as a field element.
    pub fn eval(&self, point: M) -> u64 {
        self.terms
            .iter()
            .filter(|(&m, _)| m.within(point))
            .fold(0u64, |acc, (_, &c)| acc ^ c)
    }

    /// The terms, in no particular order.
    pub fn terms(&self) -> impl Iterator<Item = (M, u64)> + '_ {
        self.terms.iter().map(|(&m, &c)| (m, c))
    }

    fn from_distinct(terms: Vec<(M, u64)>) -> Self {
        let mut map = TermMap::with_capacity_and_hasher(terms.len(), Default::default());
        for (m, c) in terms {
            debug_assert!(c != 0);
            let prev = map.insert(m, c);
            debug_assert!(prev.is_none(), "terms must be distinct");
        }
        Self { terms: map }
    }
}

// ── Univariate polynomials over the ring ───────────────────────────

/// `Σ_k coeffs[k] Z^k` with ring coefficients.
type UPoly<M> = Vec<Ring<M>>;

fn u_trim<M: BoolMask>(mut p: UPoly<M>) -> UPoly<M> {
    while p.len() > 1 && p.last().is_some_and(Ring::is_empty) {
        p.pop();
    }
    p
}

fn u_add<M: BoolMask>(a: &UPoly<M>, b: &UPoly<M>) -> UPoly<M> {
    let len = a.len().max(b.len());
    let mut out: UPoly<M> = (0..len).map(|_| Ring::default()).collect();
    for (k, c) in a.iter().enumerate() {
        out[k].add_assign(c);
    }
    for (k, c) in b.iter().enumerate() {
        out[k].add_assign(c);
    }
    u_trim(out)
}

fn u_mul<M: BoolMask>(a: &UPoly<M>, b: &UPoly<M>, gf: &Gf2) -> UPoly<M> {
    if a.is_empty() || b.is_empty() {
        return vec![Ring::default()];
    }
    let mut out: UPoly<M> = (0..a.len() + b.len() - 1)
        .map(|_| Ring::default())
        .collect();
    for (i, x) in a.iter().enumerate() {
        if x.is_empty() {
            continue;
        }
        for (j, y) in b.iter().enumerate() {
            if y.is_empty() {
                continue;
            }
            out[i + j].add_assign(&x.mul(y, gf));
        }
    }
    u_trim(out)
}

fn u_scale_ring<M: BoolMask>(a: &UPoly<M>, r: &Ring<M>, gf: &Gf2) -> UPoly<M> {
    u_trim(a.iter().map(|c| c.mul(r, gf)).collect())
}

/// `A Z² + B Z + C`: the three coefficients of a quadratic in the
/// eliminated variable, each a polynomial in the free variable.
struct Quadratic<M: BoolMask> {
    a: UPoly<M>,
    b: UPoly<M>,
    c: UPoly<M>,
}

impl<M: BoolMask> Quadratic<M> {
    /// The weights `W_{ij}` of the closed form, for `0 ≤ i ≤ j ≤ d`:
    /// `C^i A^{d−i}` on the diagonal, `C^i A^{d−j} s_{j−i}` above it.
    fn weights(&self, d: usize, gf: &Gf2) -> Vec<((usize, usize), UPoly<M>)> {
        let one: UPoly<M> = vec![Ring::constant(1)];
        let mut pow_a = vec![one.clone()];
        let mut pow_c = vec![one];
        for k in 1..=d {
            pow_a.push(u_mul(&pow_a[k - 1], &self.a, gf));
            pow_c.push(u_mul(&pow_c[k - 1], &self.c, gf));
        }
        // s_0 = 0, s_1 = B, s_k = B s_{k−1} + A C s_{k−2}.
        let ac = u_mul(&self.a, &self.c, gf);
        let mut s: Vec<UPoly<M>> = vec![vec![Ring::default()], self.b.clone()];
        for k in 2..=d {
            let next = u_add(&u_mul(&self.b, &s[k - 1], gf), &u_mul(&ac, &s[k - 2], gf));
            s.push(next);
        }
        let mut out = Vec::with_capacity((d + 1) * (d + 2) / 2);
        for i in 0..=d {
            for j in i..=d {
                let w = if i == j {
                    u_mul(&pow_c[i], &pow_a[d - i], gf)
                } else {
                    u_mul(&u_mul(&pow_c[i], &pow_a[d - j], gf), &s[j - i], gf)
                };
                out.push(((i, j), w));
            }
        }
        out
    }
}

/// The factors `P_{ij}`: `p_i²` on the diagonal, `p_i p_j` above it.
fn pair_products<M: BoolMask>(p: &[Ring<M>], gf: &Gf2) -> Vec<Ring<M>> {
    let d = p.len() - 1;
    let mut out = Vec::with_capacity((d + 1) * (d + 2) / 2);
    for i in 0..=d {
        for j in i..=d {
            out.push(if i == j {
                p[i].sqr(gf)
            } else {
                p[i].mul(&p[j], gf)
            });
        }
    }
    out
}

/// `Res_Z(P, Q)` by the closed form, with hashed products throughout.
fn resultant_naive<M: BoolMask>(p: &[Ring<M>], q: &Quadratic<M>, gf: &Gf2) -> UPoly<M> {
    let d = p.len() - 1;
    let weights = q.weights(d, gf);
    let pairs = pair_products(p, gf);
    let mut acc: UPoly<M> = vec![Ring::default()];
    for (pij, (_, w)) in pairs.iter().zip(&weights) {
        if pij.is_empty() {
            continue;
        }
        acc = u_add(&acc, &u_scale_ring(w, pij, gf));
    }
    acc
}

/// `Σ_{pairs} P_{ij} ⊗ W_{ij}` where every `P` and every `W` coefficient
/// lives on disjoint variables: the specialised accumulation.  Returns one
/// list of distinct terms per power of the free variable.
fn tensor_sum<M: BoolMask>(
    pairs: &[Ring<M>],
    weights: &[((usize, usize), UPoly<M>)],
    gf: &Gf2,
) -> Vec<Vec<(M, u64)>> {
    debug_assert_eq!(pairs.len(), weights.len());
    let p_support = pairs.iter().fold(M::default(), |acc, p| acc | p.support());
    let w_support = weights.iter().fold(M::default(), |acc, (_, w)| {
        w.iter().fold(acc, |a, c| a | c.support())
    });
    assert!(
        p_support & w_support == M::default(),
        "tensor factors must live on disjoint variables"
    );
    // Transpose the P side: each monomial u to its (pair, coefficient)s.
    let mut row_of: HashMap<M, usize, BuildHasherDefault<WideMaskHasher>> = HashMap::default();
    let mut rows: Vec<(M, Vec<(u32, u64)>)> = Vec::new();
    for (k, p) in pairs.iter().enumerate() {
        for (m, c) in p.terms() {
            let r = *row_of.entry(m).or_insert_with(|| {
                rows.push((m, Vec::new()));
                rows.len() - 1
            });
            rows[r].1.push((k as u32, c));
        }
    }
    let z_len = weights.iter().map(|(_, w)| w.len()).max().unwrap_or(1);
    let mut out = Vec::with_capacity(z_len);
    for z in 0..z_len {
        // Index the W side at this power: one dense column per monomial.
        let mut col_of: HashMap<M, u32, BuildHasherDefault<WideMaskHasher>> = HashMap::default();
        let mut cols: Vec<M> = Vec::new();
        let w_lists: Vec<Vec<(u32, u64)>> = weights
            .iter()
            .map(|(_, w)| match w.get(z) {
                Some(coeff) => coeff
                    .terms()
                    .map(|(m, c)| {
                        let col = *col_of.entry(m).or_insert_with(|| {
                            cols.push(m);
                            (cols.len() - 1) as u32
                        });
                        (col, c)
                    })
                    .collect(),
                None => Vec::new(),
            })
            .collect();
        let mut acc = vec![0u64; cols.len()];
        let mut terms = Vec::new();
        for (u, entries) in &rows {
            for &(k, c) in entries {
                for &(col, wc) in &w_lists[k as usize] {
                    acc[col as usize] ^= gf.mul(c, wc);
                }
            }
            for (col, slot) in acc.iter_mut().enumerate() {
                if *slot != 0 {
                    terms.push((*u | cols[col], *slot));
                    *slot = 0;
                }
            }
        }
        out.push(terms);
    }
    out
}

fn resultant_tensor<M: BoolMask>(p: &[Ring<M>], q: &Quadratic<M>, gf: &Gf2) -> Vec<Vec<(M, u64)>> {
    let d = p.len() - 1;
    tensor_sum(&pair_products(p, gf), &q.weights(d, gf), gf)
}

// ── S_{m+1} over linear forms ──────────────────────────────────────

/// One argument of a summation polynomial: a field constant or a linear
/// form over a block of boolean variables.
fn arg_ring<M: BoolMask>(arg: Arg, np: u32, basis: &[u64]) -> Ring<M> {
    match arg {
        Arg::Const(c) => Ring::constant(c),
        Arg::Block(k) => Ring::linear(k * np, basis),
    }
}

#[derive(Clone, Copy)]
enum Arg {
    Const(u64),
    Block(u32),
}

/// `S_3(x, y, Z) = A Z² + B Z + C` as the list `[C, B, A]`.
fn s3_in_z<M: BoolMask>(x: &Ring<M>, y: &Ring<M>, b: u64, gf: &Gf2) -> Vec<Ring<M>> {
    let a = x.add(y).sqr(gf);
    let bb = x.mul(y, gf);
    let c = bb.sqr(gf).add(&Ring::constant(b));
    vec![c, bb, a]
}

/// `S_3(x, Z, Y)` as a quadratic in `Y` whose coefficients are
/// polynomials in `Z`: `A = x² + Z²`, `B = xZ`, `C = x²Z² + b`.
fn s3_quadratic_in_y<M: BoolMask>(x: &Ring<M>, b: u64, gf: &Gf2) -> Quadratic<M> {
    let x2 = x.sqr(gf);
    Quadratic {
        a: vec![x2.clone(), Ring::default(), Ring::constant(1)],
        b: vec![Ring::default(), x.clone()],
        c: vec![Ring::constant(b), Ring::default(), x2],
    }
}

/// `S_{|args|+1}(args, Z)` as a polynomial in `Z`, by the left chain.
fn chain<M: BoolMask>(
    args: &[Arg],
    np: u32,
    basis: &[u64],
    b: u64,
    gf: &Gf2,
    engine: Engine,
) -> UPoly<M> {
    let x0 = arg_ring::<M>(args[0], np, basis);
    let x1 = arg_ring::<M>(args[1], np, basis);
    let mut p = s3_in_z(&x0, &x1, b, gf);
    for &arg in &args[2..] {
        let q = s3_quadratic_in_y(&arg_ring::<M>(arg, np, basis), b, gf);
        p = match engine {
            Engine::Naive => resultant_naive(&p, &q, gf),
            Engine::Tensor => resultant_tensor(&p, &q, gf)
                .into_iter()
                .map(Ring::from_distinct)
                .collect(),
        };
        p = u_trim(p);
    }
    p
}

/// `S_{m+1}(x_1, …, x_m, x_R)` with `x_i` the linear form over block
/// `i − 1`, as a list of distinct terms.
fn semaev_terms<M: BoolMask>(
    gf: &Gf2,
    b: u64,
    x_r: u64,
    basis: &[u64],
    summands: u32,
    engine: Engine,
) -> Vec<(M, u64)> {
    let np = basis.len() as u32;
    if summands == 2 {
        // S_3(x_1, x_2, x_R) = A x_R² + B x_R + C.
        let x1 = Ring::<M>::linear(0, basis);
        let x2 = Ring::<M>::linear(np, basis);
        let [c, bb, a]: [Ring<M>; 3] = s3_in_z(&x1, &x2, b, gf).try_into().ok().unwrap();
        let mut out = a.scale(gf.sqr(x_r), gf);
        out.add_assign(&bb.scale(x_r, gf));
        out.add_assign(&c);
        return out.terms().collect();
    }
    match engine {
        Engine::Naive => {
            let args: Vec<Arg> = (0..summands).map(Arg::Block).collect();
            let p = chain::<M>(&args, np, basis, b, gf, engine);
            // Evaluate at Z = x_R.
            let mut out = Ring::default();
            let mut pw = 1u64;
            for c in &p {
                out.add_assign(&c.scale(pw, gf));
                pw = gf.mul(pw, x_r);
            }
            out.terms().collect()
        }
        Engine::Tensor => {
            // Res_Z(S_3(x_1, x_2, Z), S_m(x_R, x_3, …, x_m, Z)).
            let mut args = vec![Arg::Const(x_r)];
            args.extend((2..summands).map(Arg::Block));
            let p = if args.len() == 2 {
                let x = arg_ring::<M>(args[1], np, basis);
                s3_in_z(&Ring::constant(x_r), &x, b, gf)
            } else {
                chain::<M>(&args, np, basis, b, gf, engine)
            };
            let x1 = Ring::<M>::linear(0, basis);
            let x2 = Ring::<M>::linear(np, basis);
            let [c, bb, a]: [Ring<M>; 3] = s3_in_z(&x1, &x2, b, gf).try_into().ok().unwrap();
            let q = Quadratic {
                a: vec![a],
                b: vec![bb],
                c: vec![c],
            };
            resultant_tensor(&p, &q, gf)
                .into_iter()
                .next()
                .unwrap_or_default()
        }
    }
}

/// Deal the terms out into the `n` coordinate equations, each in
/// canonical order: degree descending, then mask ascending (the order of
/// [`mono_key`](crate::cryptanalysis::pq_groebner_f2::mono_key) on
/// 64-bit masks).
fn split_terms<M: BoolMask>(mut terms: Vec<(M, u64)>, n: u32) -> Vec<Vec<M>> {
    terms.sort_unstable_by(|a, b| b.0.degree().cmp(&a.0.degree()).then(a.0.cmp(&b.0)));
    let mut eqs: Vec<Vec<M>> = (0..n).map(|_| Vec::new()).collect();
    for &(m, c) in &terms {
        let mut bits = c;
        while bits != 0 {
            let j = bits.trailing_zeros();
            if j < n {
                eqs[j as usize].push(m);
            }
            bits &= bits - 1;
        }
    }
    eqs
}

// ── Caps ───────────────────────────────────────────────────────────

/// The most monomials `S_{m+1}` can have over `m` blocks of `n'` boolean
/// variables: `(Σ_{k ≤ min(m−1, n')} C(n', k))^m`, saturating.
pub fn field_monomial_bound(summands: u32, n_prime: u32) -> u64 {
    let deg = summands.saturating_sub(1).min(n_prime);
    let mut per_block: u64 = 0;
    let mut binom: u64 = 1;
    for k in 0..=deg {
        per_block = per_block.saturating_add(binom);
        binom = binom.saturating_mul(u64::from(n_prime - k)) / u64::from(k + 1);
    }
    let mut total: u64 = 1;
    for _ in 0..summands {
        total = total.saturating_mul(per_block);
    }
    total
}

fn check<M: BoolMask>(summands: u32, n_prime: u32, n: u32) -> Result<(), String> {
    if !(2..=MAX_SUMMANDS).contains(&summands) {
        return Err(format!(
            "the symbolic descent takes 2 to {MAX_SUMMANDS} summands, not {summands}"
        ));
    }
    if n_prime == 0 || summands * n_prime > M::BITS {
        return Err(format!(
            "a subspace of dimension {n_prime} at {summands} summands needs {} boolean variables; \
             the monomial mask holds {}",
            summands * n_prime,
            M::BITS
        ));
    }
    if n == 0 || n > 63 {
        return Err(format!("field degree {n} outside 1..=63"));
    }
    let bound = field_monomial_bound(summands, n_prime);
    if bound > MAX_FIELD_MONOMIAL_BOUND {
        return Err(format!(
            "S_{} over n' = {n_prime} may have {bound} field monomials, above the cap of {}",
            summands + 1,
            MAX_FIELD_MONOMIAL_BOUND
        ));
    }
    Ok(())
}

fn largest_n_prime(summands: u32, bits: u32) -> u32 {
    if !(2..=MAX_SUMMANDS).contains(&summands) {
        return 0;
    }
    (1..=bits / summands)
        .take_while(|&np| field_monomial_bound(summands, np) <= MAX_FIELD_MONOMIAL_BOUND)
        .last()
        .unwrap_or(0)
}

/// The largest subspace dimension [`descend_narrow`] takes at `summands`
/// summands.  At 2 and 3 summands it is the fast path's own cap
/// ([`pq_descent_symbolic::max_n_prime`](narrow::max_n_prime)); from 4 on
/// it is the 64-bit mask and the monomial cap together.
pub fn max_n_prime_narrow(summands: u32) -> u32 {
    match summands {
        2 | 3 => narrow::max_n_prime(summands),
        _ => largest_n_prime(summands, u64::BITS),
    }
}

/// The largest subspace dimension [`descend_wide`] takes.
pub fn max_n_prime_wide(summands: u32) -> u32 {
    largest_n_prime(summands, u128::BITS)
}

// ── The descents ───────────────────────────────────────────────────

/// The subspace dimensions at which [`descend_narrow`] sends three
/// summands to the [`Engine::Tensor`] path instead of the fast path.  Both
/// return the same system there.  Measured on one thread at `n = 23` and
/// `31` (best of up to five runs, random basis and target), the tensor
/// engine took 0.79× to 0.80× the fast path's time at `n' = 3`, and
/// 0.17× to 0.70× from `n' = 4` to `14`.  At `n' = 1` and `2` it was
/// slower (1.1× to 1.9×), and nothing past `14` was measured, so the fast
/// path keeps those.  At two summands the tensor engine took 0.71× to
/// 1.06× the fast path's time, too small a difference to move two summands
/// off the fast path.
pub const TENSOR_S4_N_PRIME: std::ops::RangeInclusive<u32> = 3..=14;

/// Descend `S_{m+1}(x_1, …, x_m, x_R) = 0` with every `x_i` in the span of
/// `v_basis`, into a 64-bit system.
///
/// **Dispatch**: at 2 summands, and at 3 summands outside
/// [`TENSOR_S4_N_PRIME`], this is
/// [`pq_descent_symbolic::descend`](narrow::descend), the fast case,
/// unchanged.  Everywhere else it is the [`Engine::Tensor`] path, which
/// returns the same equations term for term where both run.  The
/// variable numbering is the fast path's: bit `i·n' + k` is `v_{i,k}`.
pub fn descend_narrow(
    gf: &Gf2,
    b: u64,
    x_r: u64,
    v_basis: &[u64],
    summands: u32,
) -> Result<SymbolicDescent, String> {
    let n_prime = v_basis.len() as u32;
    match summands {
        3 if TENSOR_S4_N_PRIME.contains(&n_prime) => {
            descend_narrow_with(Engine::Tensor, gf, b, x_r, v_basis, summands)
        }
        2 | 3 => narrow::descend(gf, b, x_r, v_basis, summands),
        _ => descend_narrow_with(Engine::Tensor, gf, b, x_r, v_basis, summands),
    }
}

/// [`descend_narrow`] with the construction chosen explicitly, at any
/// supported number of summands (2 and 3 included).
pub fn descend_narrow_with(
    engine: Engine,
    gf: &Gf2,
    b: u64,
    x_r: u64,
    v_basis: &[u64],
    summands: u32,
) -> Result<SymbolicDescent, String> {
    let n_prime = v_basis.len() as u32;
    check::<u64>(summands, n_prime, gf.n)?;
    let n_vars = (summands * n_prime) as usize;
    let terms = semaev_terms::<u64>(gf, b, x_r, v_basis, summands, engine);
    let field_monomials = terms.len();
    let equations = split_terms(terms, gf.n)
        .into_iter()
        .map(|masks| F2BoolPoly {
            terms: masks.into_iter().map(F2BoolMono::from_mask).collect(),
            n_vars,
        })
        .collect();
    Ok(SymbolicDescent {
        n: gf.n,
        n_prime,
        summands,
        n_vars,
        equations,
        v_basis: v_basis.to_vec(),
        field_monomials,
    })
}

/// One boolean equation over up to 128 variables, terms in canonical
/// order (degree descending, then mask ascending).
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct WideBoolPoly {
    pub terms: Vec<u128>,
    pub n_vars: usize,
}

impl WideBoolPoly {
    /// The value at a point of `{0,1}^n_vars`.
    pub fn eval(&self, point: u128) -> u8 {
        (self.terms.iter().filter(|&&m| m & point == m).count() & 1) as u8
    }

    /// The highest boolean degree of a term, or `None` for zero.
    pub fn degree(&self) -> Option<u32> {
        self.terms.first().map(|m| m.count_ones())
    }
}

/// A descended system with a 128-bit monomial mask.
#[derive(Clone, Debug)]
pub struct WideDescent {
    pub n: u32,
    pub n_prime: u32,
    pub summands: u32,
    pub n_vars: usize,
    pub equations: Vec<WideBoolPoly>,
    pub v_basis: Vec<u64>,
    pub field_monomials: usize,
}

impl WideDescent {
    /// The abscissae a solution names, one word per summand.
    pub fn lift(&self, v: u128) -> Vec<u64> {
        let np = self.n_prime as usize;
        (0..self.summands as usize)
            .map(|i| {
                (0..np)
                    .filter(|&k| (v >> (i * np + k)) & 1 == 1)
                    .fold(0u64, |acc, k| acc ^ self.v_basis[k])
            })
            .collect()
    }

    /// The same system with 64-bit masks, when it has at most 64
    /// variables.
    pub fn to_narrow(&self) -> Option<SymbolicDescent> {
        if self.n_vars > 64 {
            return None;
        }
        Some(SymbolicDescent {
            n: self.n,
            n_prime: self.n_prime,
            summands: self.summands,
            n_vars: self.n_vars,
            equations: self
                .equations
                .iter()
                .map(|e| F2BoolPoly {
                    terms: e
                        .terms
                        .iter()
                        .map(|&m| F2BoolMono::from_mask(m as u64))
                        .collect(),
                    n_vars: self.n_vars,
                })
                .collect(),
            v_basis: self.v_basis.clone(),
            field_monomials: self.field_monomials,
        })
    }
}

/// Descend into a 128-bit system, at any supported number of summands
/// and `m·n' ≤ 128`.
pub fn descend_wide(
    gf: &Gf2,
    b: u64,
    x_r: u64,
    v_basis: &[u64],
    summands: u32,
) -> Result<WideDescent, String> {
    descend_wide_with(Engine::Tensor, gf, b, x_r, v_basis, summands)
}

/// [`descend_wide`] with the construction chosen explicitly.
pub fn descend_wide_with(
    engine: Engine,
    gf: &Gf2,
    b: u64,
    x_r: u64,
    v_basis: &[u64],
    summands: u32,
) -> Result<WideDescent, String> {
    let n_prime = v_basis.len() as u32;
    check::<u128>(summands, n_prime, gf.n)?;
    let n_vars = (summands * n_prime) as usize;
    let terms = semaev_terms::<u128>(gf, b, x_r, v_basis, summands, engine);
    let field_monomials = terms.len();
    let equations = split_terms(terms, gf.n)
        .into_iter()
        .map(|terms| WideBoolPoly { terms, n_vars })
        .collect();
    Ok(WideDescent {
        n: gf.n,
        n_prime,
        summands,
        n_vars,
        equations,
        v_basis: v_basis.to_vec(),
        field_monomials,
    })
}

/// A descent in whichever mask fits.
#[derive(Clone, Debug)]
pub enum Descent {
    Narrow(SymbolicDescent),
    Wide(WideDescent),
}

/// Descend with the 64-bit mask whenever `m·n' ≤ 64` (the fast case,
/// [`descend_narrow`]) and with the 128-bit mask above that.
pub fn descend_any(
    gf: &Gf2,
    b: u64,
    x_r: u64,
    v_basis: &[u64],
    summands: u32,
) -> Result<Descent, String> {
    if summands as usize * v_basis.len() <= 64 {
        descend_narrow(gf, b, x_r, v_basis, summands).map(Descent::Narrow)
    } else {
        descend_wide(gf, b, x_r, v_basis, summands).map(Descent::Wide)
    }
}

// ── The summation polynomials, on words ────────────────────────────

/// `S_{m+1}(x_1, …, x_m, x_R)` on `Gf2` words, `m = xs.len() ≥ 2`, by the
/// same left chain [`Engine::Naive`] expands: at `m = 3` it is
/// [`semaev_s4_word`](narrow::semaev_s4_word).
pub fn semaev_word(gf: &Gf2, b: u64, xs: &[u64], x_r: u64) -> u64 {
    assert!(
        xs.len() >= 2,
        "a summation polynomial takes two summands or more"
    );
    let s3 = |x: u64, y: u64| -> Vec<u64> {
        let bb = gf.mul(x, y);
        vec![gf.sqr(bb) ^ b, bb, gf.sqr(x ^ y)]
    };
    let mul = |a: &[u64], c: &[u64]| -> Vec<u64> {
        let mut out = vec![0u64; a.len() + c.len() - 1];
        for (i, &x) in a.iter().enumerate() {
            for (j, &y) in c.iter().enumerate() {
                out[i + j] ^= gf.mul(x, y);
            }
        }
        out
    };
    let add = |a: &[u64], c: &[u64]| -> Vec<u64> {
        let mut out = vec![0u64; a.len().max(c.len())];
        for (k, &x) in a.iter().enumerate() {
            out[k] ^= x;
        }
        for (k, &x) in c.iter().enumerate() {
            out[k] ^= x;
        }
        out
    };
    let mut p = s3(xs[0], xs[1]);
    for &x in &xs[2..] {
        // Q(Y) = (x² + Z²) Y² + xZ Y + (x²Z² + b), coefficients in Z.
        let x2 = gf.sqr(x);
        let qa = vec![x2, 0, 1];
        let qb = vec![0, x];
        let qc = vec![b, 0, x2];
        let d = p.len() - 1;
        let mut pow_a = vec![vec![1u64]];
        let mut pow_c = vec![vec![1u64]];
        for k in 1..=d {
            pow_a.push(mul(&pow_a[k - 1], &qa));
            pow_c.push(mul(&pow_c[k - 1], &qc));
        }
        let ac = mul(&qa, &qc);
        let mut s = vec![vec![0u64], qb.clone()];
        for k in 2..=d {
            let next = add(&mul(&qb, &s[k - 1]), &mul(&ac, &s[k - 2]));
            s.push(next);
        }
        let mut acc = vec![0u64];
        for i in 0..=d {
            for j in i..=d {
                let (coef, w) = if i == j {
                    (gf.sqr(p[i]), mul(&pow_c[i], &pow_a[d - i]))
                } else {
                    (
                        gf.mul(p[i], p[j]),
                        mul(&mul(&pow_c[i], &pow_a[d - j]), &s[j - i]),
                    )
                };
                let scaled: Vec<u64> = w.iter().map(|&c| gf.mul(c, coef)).collect();
                acc = add(&acc, &scaled);
            }
        }
        p = acc;
    }
    let mut out = 0u64;
    let mut pw = 1u64;
    for &c in &p {
        out ^= gf.mul(c, pw);
        pw = gf.mul(pw, x_r);
    }
    out
}

// ── Tests ──────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::ic_boundary::{
        random_binary_instance, BinaryGroup, CountedGroup, GroupOps,
    };
    use crate::cryptanalysis::pq_descent_symbolic::{descend, semaev_s4_word};
    use rand::rngs::StdRng;
    use rand::{Rng, SeedableRng};

    fn random_basis(rng: &mut StdRng, np: u32, mask: u64) -> Vec<u64> {
        (0..np).map(|_| rng.gen::<u64>() & mask).collect()
    }

    fn standard_basis(np: u32) -> Vec<u64> {
        (0..np).map(|k| 1u64 << k).collect()
    }

    /// The truth-table descent of the word evaluator: evaluate `S_{m+1}`
    /// at every point of `V^m` and Möbius-transform each coordinate bit
    /// into its algebraic normal form.  Independent of the ring code.
    fn truth_table_descent(gf: &Gf2, b: u64, x_r: u64, basis: &[u64], m: u32) -> Vec<Vec<u64>> {
        let np = basis.len();
        let vars = m as usize * np;
        let size = 1usize << vars;
        let lift = |v: usize| -> Vec<u64> {
            (0..m as usize)
                .map(|i| {
                    (0..np)
                        .filter(|&k| (v >> (i * np + k)) & 1 == 1)
                        .fold(0u64, |acc, k| acc ^ basis[k])
                })
                .collect()
        };
        let mut table: Vec<u64> = (0..size)
            .map(|v| semaev_word(gf, b, &lift(v), x_r))
            .collect();
        // Möbius on whole words: each bit position is transformed at once.
        for i in 0..vars {
            for v in 0..size {
                if v >> i & 1 == 1 {
                    table[v] ^= table[v ^ (1 << i)];
                }
            }
        }
        let mut terms: Vec<(u64, u64)> = table
            .into_iter()
            .enumerate()
            .filter(|&(_, c)| c != 0)
            .map(|(m, c)| (m as u64, c))
            .collect();
        terms.sort_unstable();
        split_terms(terms, gf.n)
    }

    fn masks(sys: &SymbolicDescent) -> Vec<Vec<u64>> {
        sys.equations
            .iter()
            .map(|e| e.terms.iter().map(|t| t.mask).collect())
            .collect()
    }

    /// **The word evaluator is the repository's `S_4` at three summands
    /// and Semaev's `S_5` / `S_6` at four and five**: checked against
    /// `semaev_leading_form::semaev`, an independent Sylvester-determinant
    /// construction, evaluated at random field points with `a₆ = b`.
    #[test]
    fn the_word_evaluator_is_semaevs_polynomial() {
        use crate::cryptanalysis::semaev_leading_form::{semaev, A6};
        let inst = random_binary_instance(13, 2, 1 << 20).expect("a curve at n = 13");
        let gf = &inst.gf;
        let mut rng = StdRng::seed_from_u64(77);
        let eval = |poly: &crate::cryptanalysis::semaev_leading_form::F2Poly, xs: &[u64]| -> u64 {
            let mut acc = 0u64;
            for mono in &poly.terms {
                let mut t = 1u64;
                for (slot, &e) in mono.iter().enumerate() {
                    let base = if slot == A6 {
                        inst.b
                    } else if slot < xs.len() {
                        xs[slot]
                    } else {
                        assert_eq!(e, 0, "a variable outside the arguments");
                        continue;
                    };
                    for _ in 0..e {
                        t = gf.mul(t, base);
                    }
                }
                acc ^= t;
            }
            acc
        };
        for m in 2..=4usize {
            let poly = semaev(m);
            for _ in 0..24 {
                let xs: Vec<u64> = (0..=m).map(|_| rng.gen::<u64>() & gf.mask).collect();
                assert_eq!(
                    semaev_word(gf, inst.b, &xs[..m], xs[m]),
                    eval(&poly, &xs),
                    "S_{} at {xs:x?}",
                    m + 1
                );
            }
        }
        for _ in 0..64 {
            let xs: Vec<u64> = (0..4).map(|_| rng.gen::<u64>() & gf.mask).collect();
            assert_eq!(
                semaev_word(gf, inst.b, &xs[..3], xs[3]),
                semaev_s4_word(gf, inst.b, xs[0], xs[1], xs[2], xs[3])
            );
        }
    }

    /// **`S_{m+1}` vanishes on the abscissae of points summing to a
    /// target**, on genuine curve points, for `m` up to six; and it is
    /// symmetric in its arguments.
    #[test]
    fn semaev_word_vanishes_on_point_sums_and_is_symmetric() {
        for &(n, seed) in &[(11u32, 1u64), (17, 4), (23, 6)] {
            let inst = random_binary_instance(n, seed, 1 << 20).expect("a curve");
            let g = BinaryGroup(&inst.fast);
            let mut ops = GroupOps::default();
            let mut rng = StdRng::seed_from_u64(u64::from(n) * 31 + seed);
            for m in 2..=MAX_SUMMANDS as usize {
                for _ in 0..6 {
                    let pts: Vec<_> = (0..m)
                        .map(|_| {
                            g.mul(
                                &mut ops,
                                inst.generator,
                                1 + rng.gen::<u64>() % (inst.r - 1),
                            )
                        })
                        .collect();
                    let mut sum = g.identity();
                    for &p in &pts {
                        sum = g.add(&mut ops, sum, p);
                    }
                    if sum.infinity || pts.iter().any(|p| p.infinity) {
                        continue;
                    }
                    let xs: Vec<u64> = pts.iter().map(|p| p.x).collect();
                    assert_eq!(semaev_word(&inst.gf, inst.b, &xs, sum.x), 0, "m = {m}");
                    // Symmetry: the target swapped with a summand, and a
                    // reversed list of summands.
                    let mut swapped = xs.clone();
                    swapped[0] = sum.x;
                    assert_eq!(semaev_word(&inst.gf, inst.b, &swapped, xs[0]), 0);
                    let rev: Vec<u64> = xs.iter().rev().copied().collect();
                    let x_r = rng.gen::<u64>() & inst.gf.mask;
                    assert_eq!(
                        semaev_word(&inst.gf, inst.b, &rev, x_r),
                        semaev_word(&inst.gf, inst.b, &xs, x_r)
                    );
                }
            }
        }
    }

    /// **Both engines are the truth-table descent, monomial for monomial**,
    /// at every `m` from 2 to 6 on every dimension the table reaches, on
    /// random curves, random and standard bases, and degenerate targets
    /// (`x_R = 0`, `x_R` in the subspace, a repeated basis vector, a zero
    /// basis vector).
    #[test]
    fn both_engines_are_the_truth_table_descent() {
        let mut rng = StdRng::seed_from_u64(0x7AB1E);
        for &(n, seed) in &[(5u32, 1u64), (7, 2), (11, 3), (13, 4)] {
            let inst = random_binary_instance(n, seed, 1 << 20).expect("a curve");
            let gf = &inst.gf;
            for m in 2..=MAX_SUMMANDS {
                let max_np = match m {
                    2 | 3 => 5,
                    4 => 4,
                    _ => 2,
                };
                for np in 1..=max_np {
                    for variant in 0..4u32 {
                        let mut basis = if variant == 0 {
                            standard_basis(np)
                        } else {
                            random_basis(&mut rng, np, gf.mask)
                        };
                        if variant == 3 && np >= 2 {
                            basis[1] = if rng.gen() { basis[0] } else { 0 };
                        }
                        let x_r = match variant {
                            1 => 0,
                            2 => basis[0],
                            _ => rng.gen::<u64>() & gf.mask,
                        };
                        let table = truth_table_descent(gf, inst.b, x_r, &basis, m);
                        for engine in [Engine::Tensor, Engine::Naive] {
                            let sys =
                                descend_narrow_with(engine, gf, inst.b, x_r, &basis, m).unwrap();
                            assert_eq!(sys.n_vars, (m * np) as usize);
                            assert_eq!(
                                masks(&sys),
                                table,
                                "{engine:?} at n = {n}, m = {m}, n' = {np}, variant {variant}"
                            );
                            let wide =
                                descend_wide_with(engine, gf, inst.b, x_r, &basis, m).unwrap();
                            let narrowed = wide.to_narrow().unwrap();
                            assert_eq!(masks(&narrowed), table);
                            assert_eq!(narrowed.field_monomials, sys.field_monomials);
                        }
                    }
                }
            }
        }
    }

    /// **At two and three summands the new engines return exactly what
    /// the fast path returns**: the same `F2BoolPoly`s, term order
    /// included, and the same monomial count, well past the truth table.
    #[test]
    fn the_engines_match_the_fast_path_at_two_and_three_summands() {
        let mut rng = StdRng::seed_from_u64(0xFA57);
        for &(n, seed) in &[(17u32, 1u64), (23, 2), (31, 3)] {
            let inst = random_binary_instance(n, seed, 1 << 20).expect("a curve");
            let gf = &inst.gf;
            for (m, nps) in [
                (2u32, vec![1u32, 6, 13, 20, 32]),
                (3, vec![1, 2, 3, 5, 6, 8, 10, 11, 12, 14, 15]),
            ] {
                for np in nps {
                    let basis = random_basis(&mut rng, np, gf.mask);
                    let x_r = rng.gen::<u64>() & gf.mask;
                    let fast = descend(gf, inst.b, x_r, &basis, m).unwrap();
                    let via = descend_narrow(gf, inst.b, x_r, &basis, m).unwrap();
                    assert_eq!(via.equations, fast.equations);
                    // The naive engine is the slow reference; past n' = 6 only the
                    // tensor engine is compared.
                    let engines: &[Engine] = if np <= 6 {
                        &[Engine::Tensor, Engine::Naive]
                    } else {
                        &[Engine::Tensor]
                    };
                    for &engine in engines {
                        let sys = descend_narrow_with(engine, gf, inst.b, x_r, &basis, m).unwrap();
                        assert_eq!(
                            sys.equations, fast.equations,
                            "{engine:?} m = {m} n' = {np}"
                        );
                        assert_eq!(sys.field_monomials, fast.field_monomials);
                        assert_eq!(sys.lift(5), fast.lift(5));
                    }
                }
            }
        }
    }

    /// **The two engines agree past the truth table** at four and five
    /// summands, and every equation evaluates to its bit of `S_{m+1}`.
    #[test]
    fn the_engines_agree_and_evaluate_correctly_past_the_table() {
        let mut rng = StdRng::seed_from_u64(0x4E4E);
        let inst = random_binary_instance(23, 5, 1 << 20).expect("a curve at n = 23");
        let gf = &inst.gf;
        for (m, np) in [(4u32, 4u32), (4, 5), (5, 3)] {
            let basis = random_basis(&mut rng, np, gf.mask);
            let x_r = rng.gen::<u64>() & gf.mask;
            let tensor = descend_narrow(gf, inst.b, x_r, &basis, m).unwrap();
            let naive = descend_narrow_with(Engine::Naive, gf, inst.b, x_r, &basis, m).unwrap();
            assert_eq!(tensor.equations, naive.equations, "m = {m}, n' = {np}");
            assert!(tensor
                .equations
                .iter()
                .all(|e| e.terms.iter().all(|t| t.degree() <= m * (m - 1))));
            let vars = m * np;
            for _ in 0..300 {
                let v = rng.gen::<u64>() & ((1u64 << vars) - 1);
                let xs = tensor.lift(v);
                let direct = semaev_word(gf, inst.b, &xs, x_r);
                for (j, eq) in tensor.equations.iter().enumerate() {
                    assert_eq!(
                        eq.eval(v) as u64,
                        (direct >> j) & 1,
                        "equation {j} at {v:#x}"
                    );
                }
            }
        }
    }

    /// **The wide mask**: a 128-bit descent below 64 variables is the
    /// narrow one, and above 64 variables (`S_3` at `n' = 40` and `63`)
    /// every equation still evaluates to its bit of the summation
    /// polynomial, with the variables above bit 63 in play.  `S_4` above
    /// 64 variables (`n' ≥ 22`) is past the monomial cap and refused.
    #[test]
    fn the_wide_descent_reaches_past_sixty_four_variables() {
        let mut rng = StdRng::seed_from_u64(0x128);
        // A field and a curve coefficient are all a descent needs; no
        // point count at n = 47.
        let irr = crate::cryptanalysis::koblitz_index_calculus::find_irreducible_sparse(47)
            .expect("an irreducible at n = 47");
        let gf = &Gf2::new(&irr);
        let b = rng.gen::<u64>() & gf.mask | 1;
        // S_4 at n' = 22 (66 variables) is past the monomial cap: refused.
        let basis = random_basis(&mut rng, 22, gf.mask);
        assert!(descend_wide(gf, b, 1, &basis, 3).is_err());
        for (m, np) in [(2u32, 40u32), (2, 63)] {
            let basis = random_basis(&mut rng, np, gf.mask);
            let x_r = rng.gen::<u64>() & gf.mask;
            let sys = descend_wide(gf, b, x_r, &basis, m).unwrap();
            assert_eq!(sys.n_vars, (m * np) as usize);
            assert!(sys.to_narrow().is_none());
            assert!(sys
                .equations
                .iter()
                .any(|e| e.terms.iter().any(|&t| t >> 64 != 0)));
            assert!(sys.equations.iter().all(|e| e.degree().unwrap_or(0) <= 2));
            let naive = descend_wide_with(Engine::Naive, gf, b, x_r, &basis, m).unwrap();
            assert_eq!(naive.equations, sys.equations);
            for _ in 0..500 {
                let v = (u128::from(rng.gen::<u64>()) << 64 | u128::from(rng.gen::<u64>()))
                    & ((1u128 << sys.n_vars) - 1);
                let xs = sys.lift(v);
                let direct = semaev_word(gf, b, &xs, x_r);
                for (j, eq) in sys.equations.iter().enumerate() {
                    assert_eq!(u64::from(eq.eval(v)), (direct >> j) & 1, "equation {j}");
                }
            }
            match descend_any(gf, b, x_r, &basis, m).unwrap() {
                Descent::Wide(w) => assert_eq!(w.equations, sys.equations),
                Descent::Narrow(_) => panic!("{} variables cannot be narrow", sys.n_vars),
            }
        }
        // Below 64 variables the dispatcher picks the fast case.
        let basis = random_basis(&mut rng, 10, gf.mask);
        match descend_any(gf, b, 7, &basis, 2).unwrap() {
            Descent::Narrow(s) => {
                assert_eq!(s.equations, descend(gf, b, 7, &basis, 2).unwrap().equations)
            }
            Descent::Wide(_) => panic!("20 variables fit the narrow mask"),
        }
    }

    /// **The solutions of the descended system are exactly the tuples of
    /// the subspace on which `S_{m+1}` vanishes**, as sets, at four and
    /// five summands, on planted targets (a sum of `m` points of the
    /// subspace) and random ones.
    #[test]
    fn the_solution_set_is_the_vanishing_set() {
        let mut rng = StdRng::seed_from_u64(0x5015);
        for &(n, seed) in &[(7u32, 1u64), (11, 2), (13, 3)] {
            let inst = random_binary_instance(n, seed, 1 << 20).expect("a curve");
            let gf = &inst.gf;
            for (m, np) in [(4u32, 2u32), (4, 3), (5, 2)] {
                let basis = random_basis(&mut rng, np, gf.mask);
                for planted in [true, false] {
                    let x_r = if planted {
                        // The abscissa of a sum of m points over the subspace.
                        let pts: Vec<_> = (0..64)
                            .filter_map(|_| {
                                let v = rng.gen::<u64>() & ((1 << np) - 1);
                                let x = (0..np as usize)
                                    .filter(|&k| v >> k & 1 == 1)
                                    .fold(0u64, |a, k| a ^ basis[k]);
                                inst.points_with_x(x).first().copied()
                            })
                            .take(m as usize)
                            .collect();
                        if pts.len() < m as usize {
                            continue;
                        }
                        let g = BinaryGroup(&inst.fast);
                        let mut ops = GroupOps::default();
                        let s = pts.iter().fold(g.identity(), |a, &p| g.add(&mut ops, a, p));
                        if s.infinity {
                            continue;
                        }
                        s.x
                    } else {
                        rng.gen::<u64>() & gf.mask
                    };
                    let sys = descend_narrow(gf, inst.b, x_r, &basis, m).unwrap();
                    let vars = m * np;
                    let mut by_system = Vec::new();
                    let mut by_word = Vec::new();
                    for v in 0..1u64 << vars {
                        if sys.equations.iter().all(|e| e.eval(v) == 0) {
                            by_system.push(v);
                        }
                        if semaev_word(gf, inst.b, &sys.lift(v), x_r) == 0 {
                            by_word.push(v);
                        }
                    }
                    assert_eq!(by_system, by_word, "n = {n}, m = {m}, n' = {np}");
                    if planted {
                        assert!(!by_system.is_empty(), "a planted target has a solution");
                    }
                }
            }
        }
    }

    /// The caps are refused, never asserted, and the bound is the
    /// documented formula.
    #[test]
    fn the_caps_are_refused() {
        let inst = random_binary_instance(9, 1, 1 << 20).unwrap();
        let gf = &inst.gf;
        assert_eq!(field_monomial_bound(4, 5), 26u64.pow(4));
        assert_eq!(field_monomial_bound(2, 3), 16);
        assert_eq!(field_monomial_bound(6, 1), 64);
        assert_eq!(max_n_prime_narrow(2), 32);
        assert_eq!(max_n_prime_narrow(3), 21);
        assert_eq!(max_n_prime_narrow(4), 6);
        assert_eq!(max_n_prime_narrow(5), 4);
        assert_eq!(max_n_prime_narrow(6), 3);
        assert_eq!(max_n_prime_narrow(7), 0);
        assert_eq!(max_n_prime_wide(2), 64);
        assert_eq!(max_n_prime_wide(4), 6);
        let basis = |np: u32| -> Vec<u64> { (0..np).map(|k| 1u64 << (k % 9)).collect() };
        assert_eq!(max_n_prime_wide(3), 17);
        assert!(descend_narrow(gf, inst.b, 3, &basis(7), 4).is_err());
        assert!(descend_narrow(gf, inst.b, 3, &basis(6), 4).is_ok());
        assert!(descend_narrow(gf, inst.b, 3, &basis(2), 7).is_err());
        assert!(descend_narrow(gf, inst.b, 3, &[], 4).is_err());
        assert!(descend_narrow_with(Engine::Naive, gf, inst.b, 3, &basis(33), 2).is_err());
        assert!(descend_wide(gf, inst.b, 3, &basis(33), 2).is_ok());
        assert!(descend_wide(gf, inst.b, 3, &basis(65), 2).is_err());
        assert!(descend_wide(gf, inst.b, 3, &basis(18), 3).is_err());
    }

    /// **The `descent-algebraic` oracle at four and five summands decides
    /// exactly what brute force decides.**  For every target, it finds a
    /// decomposition iff some tuple of base abscissae lifts to signed base
    /// points that sum to the target.  Every decomposition it returns does
    /// sum to the target.  The exhaustive solver's solution set is the
    /// vanishing set of `S_{m+1}` on the subspace.  At two summands the
    /// dispatcher keeps the fast path and the oracle is unchanged.  The
    /// whole pipeline recovers the planted logarithm at `m = 4`.
    #[test]
    fn the_algebraic_oracle_decomposes_into_four_and_five_points() {
        use crate::cryptanalysis::ic_boundary::Calibration;
        use crate::cryptanalysis::ic_boundary::{lift_abscissae, OracleCounters};
        use crate::cryptanalysis::ic_framework::plugins::{
            BinarySubspaceBase, DescentAlgebraicOracle,
        };
        use crate::cryptanalysis::ic_framework::solvers::solver_by_name;
        use crate::cryptanalysis::ic_framework::stages::{
            BooleanSystem, DecompositionOracle, FactorBaseBuilder, InstanceCtx, Params,
            SolverVerdict, Targets,
        };
        use crate::cryptanalysis::ic_framework::{run_pipeline, PipelineSpec};

        for &(n, seed, m, dim) in &[(11u32, 3u64, 4u32, 2u32), (11, 3, 4, 3), (11, 3, 5, 3)] {
            let inst = random_binary_instance(n, seed, 8).expect("a curve");
            let group = BinaryGroup(&inst.fast);
            let mut ops = GroupOps::default();
            let planted = 1 + 30_011 % (inst.r - 1);
            let ctx = InstanceCtx {
                group: &group,
                generator: inst.generator,
                target: group.mul(&mut ops, inst.generator, planted),
                r: inst.r,
                cofactor: inst.cofactor,
                group_order: inst.group_order,
                name: inst.name.clone(),
                field_degree: Some(inst.n),
            };
            let base = BinarySubspaceBase { instance: &inst };
            let mut fb_params = Params::default();
            fb_params.set("dimension", dim.to_string());
            let fb = base.build(&ctx, &fb_params, &mut ops).unwrap();
            let basis = fb.subspace_basis.clone().expect("a subspace base");
            let mut oracle = DescentAlgebraicOracle::new(
                m,
                &inst,
                solver_by_name("exhaustive").unwrap(),
                Params::default(),
                None,
            );
            oracle
                .prepare(&ctx, &fb, &Params::default(), &mut ops)
                .expect("m >= 4 is accepted");
            let exhaustive = solver_by_name("exhaustive").unwrap();
            let words: Vec<u64> = (0..1u64 << dim)
                .map(|v| {
                    (0..dim as usize)
                        .filter(|&k| v >> k & 1 == 1)
                        .fold(0u64, |a, k| a ^ basis[k])
                })
                .collect();
            let mut hits = 0;
            let mut ctr = OracleCounters::default();
            for k in 1..=40u64 {
                let point = group.mul(&mut ops, inst.generator, k);
                let got = oracle.decompose(&ctx, &fb, &mut ops, &mut ctr, point);
                // Brute force over every tuple of subspace abscissae.
                let tuples = (words.len() as u64).pow(m);
                let mut brute = false;
                for t in 0..tuples {
                    let xs: Vec<u64> = (0..m)
                        .map(|i| words[(t / (words.len() as u64).pow(i)) as usize % words.len()])
                        .collect();
                    if lift_abscissae(&group, &fb, &mut ops, &xs, point).is_some() {
                        brute = true;
                        break;
                    }
                }
                assert_eq!(got.is_some(), brute, "n = {n}, m = {m}, [{k}]G");
                if let Some(indices) = got {
                    assert_eq!(indices.len(), m as usize);
                    let sum = indices.iter().fold(group.identity(), |a, &i| {
                        group.add(&mut ops, a, fb.points[i])
                    });
                    assert_eq!(sum, point);
                    hits += 1;
                }
                // The solver's solutions are the vanishing set (on the
                // first targets only at five summands, where the word
                // evaluator is the slow side).
                if m == 5 && k > 6 {
                    continue;
                }
                let sys = descend_narrow(&inst.gf, inst.b, point.x, &basis, m).unwrap();
                let system = BooleanSystem {
                    equations: sys.equations.clone(),
                    n_vars: sys.n_vars,
                };
                let (verdict, _) = exhaustive.solve(&system, &Params::default(), None);
                let mut solved = match verdict {
                    SolverVerdict::Solved(s) => s,
                    SolverVerdict::Unsatisfiable => Vec::new(),
                    other => panic!("exhaustive search gave {other:?}"),
                };
                solved.sort_unstable();
                let vanishing: Vec<u64> = (0..1u64 << sys.n_vars)
                    .filter(|&v| semaev_word(&inst.gf, inst.b, &sys.lift(v), point.x) == 0)
                    .collect();
                assert_eq!(solved, vanishing, "n = {n}, m = {m}, [{k}]G");
            }
            assert!(
                hits > 0,
                "n = {n}, m = {m}: nothing decomposed, nothing was checked"
            );
        }

        // A whole run at m = 4 recovers the planted logarithm.
        let inst = random_binary_instance(11, 3, 8).expect("a curve at n = 11");
        let group = BinaryGroup(&inst.fast);
        let mut ops = GroupOps::default();
        let planted = 1 + 4_099 % (inst.r - 1);
        let ctx = InstanceCtx {
            group: &group,
            generator: inst.generator,
            target: group.mul(&mut ops, inst.generator, planted),
            r: inst.r,
            cofactor: inst.cofactor,
            group_order: inst.group_order,
            name: inst.name.clone(),
            field_degree: Some(inst.n),
        };
        let base = BinarySubspaceBase { instance: &inst };
        let mut spec = PipelineSpec {
            factor_base: "binary-subspace".into(),
            oracle: "descent-algebraic".into(),
            solver: Some("exhaustive".into()),
            targets: Targets::Walk,
            max_trials: 200_000,
            seed: 7,
            ..Default::default()
        };
        spec.factor_base_params.set("dimension", "3");
        spec.oracle_params.set("m", "4");
        let mut oracle = DescentAlgebraicOracle::new(
            4,
            &inst,
            solver_by_name("exhaustive").unwrap(),
            Params::default(),
            None,
        );
        let report = run_pipeline(
            &ctx,
            &spec,
            &base,
            &mut oracle,
            planted,
            &Calibration::default(),
            None,
        )
        .expect("an m = 4 run");
        assert!(report.verified, "did not recover the planted logarithm");
        assert_eq!(report.recovered, Some(planted));
        assert_eq!(report.decomposition.summands, 4);

        // Past the caps the oracle refuses in prepare.
        let mut fb_params = Params::default();
        fb_params.set("dimension", "7");
        let fb = base.build(&ctx, &fb_params, &mut ops).unwrap();
        let mut oracle = DescentAlgebraicOracle::new(
            4,
            &inst,
            solver_by_name("exhaustive").unwrap(),
            Params::default(),
            None,
        );
        assert!(oracle
            .prepare(&ctx, &fb, &Params::default(), &mut ops)
            .is_err());
        let mut oracle = DescentAlgebraicOracle::new(
            7,
            &inst,
            solver_by_name("exhaustive").unwrap(),
            Params::default(),
            None,
        );
        assert!(oracle
            .prepare(&ctx, &fb, &Params::default(), &mut ops)
            .is_err());
    }
}
