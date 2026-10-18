//! # The `m = 4` linearised oracle: triples and an octic in the fourth.
//!
//! [`super::SubspaceOracle`] decides `m = 3` by looping over **pairs** of
//! factor-base abscissae and solving the quartic `S₄` leaves in the
//! third, through `gcd(q, L_V mod q)`.  This module is the same idea one
//! summand further: loop over **triples** `X₁ ≤ X₂ ≤ X₃` of the subspace
//! `V` and solve for the fourth abscissa, whose polynomial now has
//! degree 8.
//!
//! ```text
//!   for each triple (X₁ ≤ X₂ ≤ X₃):           ~2^{3l}/6 of them
//!       R(x) = Res_U( S₄(X₁, X₂, X₃, U), S₃(x, x_R, U) )   degree ≤ 8
//!       G    = gcd(R, L_V mod R)                           its roots in V
//!       every root x₄ of G gives a candidate {X₁, X₂, X₃, x₄}
//! ```
//!
//! `R` is Semaev's recursion `S₅ = Res_U(S₄(·, ·, ·, U), S₃(·, ·, U))`
//! specialised at the triple and the target, as a polynomial in the
//! fourth abscissa.  Its coefficients are built from a per-target table
//! (the resultant is a fixed quadratic form in the quartic's five
//! coefficients; see `ResultantTable`), `L_V mod R` by the same
//! Horner-under-Frobenius evaluation the quartic route uses with an
//! octic squaring table, and one field inversion is spent per *row*
//! `(X₁, X₂)` of the triple loop, by [`Gf2::batch_inv`].
//!
//! # What "the same decompositions" means
//!
//! The generic `m = 4` path is the chained Weil descent of
//! [`crate::cryptanalysis::koblitz_groebner::build_decomposition_system`]:
//! unknowns `X₁ … X₄ ∈ V` and intermediate abscissae `e₁, e₂ ∈ F_{2ⁿ}`
//! with
//!
//! ```text
//!   S₃(X₁, X₂, e₁) = 0,   S₃(e₁, X₃, e₂) = 0,   S₃(e₂, X₄, x_R) = 0.
//! ```
//!
//! Its decompositions, projected to the summands, are the abscissa
//! tuples for which some *rational* chain exists.  A zero of the
//! resultant only promises a chain over the algebraic closure, so the
//! linearised candidates are a superset: every candidate is therefore
//! checked for a rational chain in some ordering of its four abscissae
//! (at most two roots of a quadratic per link, solved through a
//! precomputed Artin–Schreier map), and only those that pass are
//! returned.  Completeness holds because a rational chain for
//! `(X₁, X₂, X₃, X₄)` makes `e₂` a common root of `S₄(X₁, X₂, X₃, ·)`
//! and `S₃(X₄, x_R, ·)`, so `X₄` is a root of `R` for the triple
//! `{X₁, X₂, X₃}`, and `L_V(X₄) = 0` puts it in `G`.  Extra factors the
//! resultant may carry (it is a formal resultant, so a vanishing leading
//! coefficient can add roots) only add candidates the chain check
//! removes.
//!
//! [`TripleOracle::decompose_all`] returns that set of multisets, each
//! sorted ascending and the list sorted lexicographically, which is the
//! order [`decompose_all_generic`] also returns them in; the two are
//! compared on random, planted, refuted, degenerate and boundary
//! instances by this module's tests.
//!
//! # Cost
//!
//! Per triple: the quartic (about ten products), fifteen pairwise
//! products of its coefficients, about sixty carry-less products for
//! the resultant's nine coefficients, a 48-product squaring table,
//! `l` octic squarings (32 products each) and a pseudo-remainder gcd of
//! degrees 8 and 7.  `O(l)` field operations per triple instead of the
//! `2^l` evaluations of walking the fourth summand, and no intermediate
//! unknowns: the generic system has `4l + 2n` Boolean unknowns.  Like
//! the `m = 3` oracle this does **not** change index calculus's `2^n`
//! accounting (`super`'s "This does not rescue index calculus"): with
//! `m = 4` the factor of `2^{3l}` per target cancels against the
//! `4!·2^{n−4l}` targets per relation the same way.

use super::{quartic_general_with, subspace_poly_for_basis, GeneralTargetPowers, Gf2, LvHorner};
use crate::binary_ecc::{F2mElement, IrreduciblePoly};
use crate::cryptanalysis::koblitz_groebner::{
    chain_order_interleaved, invert_permutation, permute_mask, permute_poly, solve_boolean_system,
    split_rule_default, FieldStructure, SolveOptions, SolveStats, SolverEngine,
};
use crate::cryptanalysis::polynomial_reuse::build_decomposition_system_reusing;
use std::collections::BTreeSet;

/// Degree of `S₅` in its last argument.
const OCT: usize = 8;

/// A polynomial of degree at most 8 in the fourth abscissa, low first.
type P9 = [u64; OCT + 1];

/// Wide enough for the square of a degree-7 remainder.
const WIDE: usize = 2 * OCT - 1;
type PW = [u64; WIDE];

/// Index of the product `a_i a_k`, `i ≤ k ≤ 4`, in [`ResultantTable`].
const fn pair_index(i: usize, k: usize) -> usize {
    // Rows of the upper triangle: i = 0 holds 5, i = 1 holds 4, …
    i * 5 - i * (i.saturating_sub(1)) / 2 + (k - i)
}

/// `(i, k)` for each of the fifteen pair indices.
const PAIRS: [(usize, usize); 15] = {
    let mut out = [(0usize, 0usize); 15];
    let mut i = 0;
    while i < 5 {
        let mut k = i;
        while k < 5 {
            out[pair_index(i, k)] = (i, k);
            k += 1;
        }
        i += 1;
    }
    out
};

// ── Small polynomial helpers over `Gf2` (setup and cold paths) ─────

fn pmul(a: &[u64], b: &[u64], gf: &Gf2) -> Vec<u64> {
    let mut out = vec![0u64; a.len() + b.len() - 1];
    for (i, &x) in a.iter().enumerate() {
        for (j, &y) in b.iter().enumerate() {
            out[i + j] ^= gf.mul(x, y);
        }
    }
    out
}

fn padd(a: &[u64], b: &[u64]) -> Vec<u64> {
    let mut out = vec![0u64; a.len().max(b.len())];
    for (i, &x) in a.iter().enumerate() {
        out[i] ^= x;
    }
    for (i, &x) in b.iter().enumerate() {
        out[i] ^= x;
    }
    out
}

fn ppow(a: &[u64], e: usize, gf: &Gf2) -> Vec<u64> {
    let mut out = vec![1u64];
    for _ in 0..e {
        out = pmul(&out, a, gf);
    }
    out
}

fn deg_of(p: &[u64]) -> Option<usize> {
    (0..p.len()).rev().find(|&i| p[i] != 0)
}

fn eval(p: &[u64], x: u64, gf: &Gf2) -> u64 {
    p.iter().rev().fold(0u64, |acc, &c| gf.mul(acc, x) ^ c)
}

/// `S₃(x₁, x₂, x₃) = (x₁ + x₂)² x₃² + x₁x₂x₃ + x₁²x₂² + b`, the link
/// every equation of the generic chain is a copy of.
fn s3(x1: u64, x2: u64, x3: u64, b: u64, gf: &Gf2) -> u64 {
    let p = gf.mul(x1, x2);
    gf.mul(gf.sqr(x1 ^ x2), gf.sqr(x3)) ^ gf.mul(p, x3) ^ gf.sqr(p) ^ b
}

// ── The resultant as a quadratic form in the quartic ───────────────

/// `Res_U(A, B)` for `A = Σ a_i Uⁱ` (the quartic `S₄(X₁, X₂, X₃, U)`)
/// and `B = β₂U² + β₁U + β₀ = S₃(x, x_R, U)`, as a polynomial in `x`.
///
/// With `u₁, u₂` the roots of `B`, `Res = β₂⁴ A(u₁)A(u₂)`, and
/// expanding the product by the symmetric functions `e₁ = β₁/β₂`,
/// `e₂ = β₀/β₂` (power sums `P₁ = e₁`, `P₂ = e₁²`, `P₃ = e₁³ + e₁e₂`,
/// `P₄ = e₁⁴` in characteristic 2) gives
///
/// ```text
///   Res = Σᵢ aᵢ² β₀ⁱ β₂^{4−i} + Σ_{i<k} aᵢa_k β₀ⁱ β₂^{4−k} Q_{k−i},
///   Q₁ = β₁, Q₂ = β₁², Q₃ = β₁³ + β₁β₀β₂, Q₄ = β₁⁴,
/// ```
///
/// a polynomial identity, so it is the formal (Sylvester) resultant
/// everywhere, including where `β₂` vanishes.  With
/// `β₂ = x² + x_R²`, `β₁ = x_R x`, `β₀ = x_R² x² + b` every `M_{ik}` is
/// a polynomial of degree `8 − (k − i)` in `x` that depends on the target
/// alone; this table holds its non-zero coefficients, grouped by the
/// power of `x` they feed.
#[derive(Clone, Debug)]
struct ResultantTable {
    /// `idx[start[j]..start[j + 1]]`: pair indices feeding `x^j`.
    idx: Vec<u8>,
    /// Matching coefficients of `M_{ik}` at `x^j`.
    coef: Vec<u64>,
    start: [usize; OCT + 2],
}

impl ResultantTable {
    fn new(xr: u64, b: u64, gf: &Gf2) -> Self {
        let xr2 = gf.sqr(xr);
        let beta2 = [xr2, 0, 1];
        let beta1 = [0, xr];
        let beta0 = [b, 0, xr2];
        let q: [Vec<u64>; 5] = [
            vec![1],
            beta1.to_vec(),
            ppow(&beta1, 2, gf),
            padd(
                &ppow(&beta1, 3, gf),
                &pmul(&pmul(&beta1, &beta0, gf), &beta2, gf),
            ),
            ppow(&beta1, 4, gf),
        ];
        let mut m: Vec<Vec<u64>> = Vec::with_capacity(15);
        for &(i, k) in PAIRS.iter() {
            let poly = pmul(
                &pmul(&ppow(&beta0, i, gf), &ppow(&beta2, 4 - k, gf), gf),
                &q[k - i],
                gf,
            );
            debug_assert!(deg_of(&poly).is_none_or(|d| d <= OCT));
            m.push(poly);
        }
        let mut idx = Vec::new();
        let mut coef = Vec::new();
        let mut start = [0usize; OCT + 2];
        for j in 0..=OCT {
            start[j] = idx.len();
            for (t, poly) in m.iter().enumerate() {
                let c = poly.get(j).copied().unwrap_or(0);
                if c != 0 {
                    idx.push(t as u8);
                    coef.push(c);
                }
            }
        }
        start[OCT + 1] = idx.len();
        Self { idx, coef, start }
    }

    /// The resultant's nine coefficients for the quartic `a`.
    #[inline(always)]
    fn apply(&self, a: &[u64; 5], gf: &Gf2) -> P9 {
        let mut pr = [0u64; 15];
        for (t, &(i, k)) in PAIRS.iter().enumerate() {
            pr[t] = if i == k {
                gf.sqr_fused(a[i])
            } else {
                gf.mul(a[i], a[k])
            };
        }
        let mut out = [0u64; OCT + 1];
        for (j, o) in out.iter_mut().enumerate() {
            let mut acc = 0u128;
            for t in self.start[j]..self.start[j + 1] {
                acc ^= gf.clmul(pr[usize::from(self.idx[t])], self.coef[t]);
            }
            *o = gf.reduce(acc);
        }
        out
    }
}

// ── Octic arithmetic ────────────────────────────────────────────────

/// `L_V mod f` for a monic `f` of degree `d ≥ 1`, by the plain sum
/// `Σ aᵢ (t^{2^i} mod f)` with remainders taken one leading term at a
/// time.  The reference the octic route is checked against, and the
/// route for the rare `R` of degree below 8.
fn lv_mod_generic(f: &[u64], d: usize, lv: &[u64], gf: &Gf2) -> P9 {
    debug_assert!((1..=OCT).contains(&d));
    let rem = |w: &mut PW| {
        for top in (d..WIDE).rev() {
            let c = w[top];
            if c != 0 {
                for i in 0..d {
                    w[top - d + i] ^= gf.mul(f[i], c);
                }
                w[top] = 0;
            }
        }
    };
    let mut pow: PW = [0; WIDE];
    pow[1] = 1;
    rem(&mut pow);
    let mut acc = [0u64; OCT + 1];
    for (i, &ai) in lv.iter().enumerate() {
        if ai != 0 {
            for j in 0..d {
                acc[j] ^= gf.mul(pow[j], ai);
            }
        }
        if i + 1 < lv.len() {
            let mut sq: PW = [0; WIDE];
            for j in 0..d {
                sq[2 * j] = gf.sqr(pow[j]);
            }
            rem(&mut sq);
            pow = sq;
        }
    }
    acc
}

/// `L_V mod f` for a monic octic `f` (its eight low coefficients):
/// [`LvHorner`] under `φ(u) = u² mod f`, with `φ` by a table of
/// `t^8, t^10, t^12, t^14 mod f`.  The same remainder as
/// [`lv_mod_generic`], coefficient for coefficient.
#[inline(always)]
fn lv_mod_octic(f: &[u64; OCT], lv: &Horner, gf: &Gf2) -> [u64; OCT] {
    // t^8 ≡ Σ f_j t^j, then one factor of t at a time.
    let mut tab = [[0u64; OCT]; 4];
    let mut cur = *f;
    tab[0] = cur;
    for step in 1..=6 {
        let c = cur[OCT - 1];
        let mut next = [0u64; OCT];
        next[0] = gf.mul(c, f[0]);
        for j in 1..OCT {
            next[j] = cur[j - 1] ^ gf.mul(c, f[j]);
        }
        cur = next;
        if step % 2 == 0 {
            tab[step / 2] = cur;
        }
    }
    let mut u = [0u64; OCT];
    u[1] = lv.lin[0];
    u[2] = lv.lin[1];
    u[4] = lv.top;
    for &bj in &lv.steps {
        let s = [
            gf.sqr_fused(u[4]),
            gf.sqr_fused(u[5]),
            gf.sqr_fused(u[6]),
            gf.sqr_fused(u[7]),
        ];
        let mut next = [0u64; OCT];
        for (j, o) in next.iter_mut().enumerate() {
            let mut acc = if j % 2 == 0 { gf.sqr_wide(u[j / 2]) } else { 0 };
            for (si, row) in s.iter().zip(tab.iter()) {
                acc ^= gf.clmul(*si, row[j]);
            }
            *o = gf.reduce(acc);
        }
        next[1] ^= bj;
        u = next;
    }
    u
}

/// [`LvHorner`]'s coefficients, owned so the oracle can be cloned.
#[derive(Clone, Debug)]
struct Horner {
    top: u64,
    lin: [u64; 2],
    steps: Vec<u64>,
}

impl Horner {
    fn new(lv: &[u64], gf: &Gf2) -> Self {
        let h = LvHorner::new(lv, gf);
        Self {
            top: h.top,
            lin: h.lin,
            steps: h.steps,
        }
    }
}

/// Greatest common divisor up to a non-zero scalar, by pseudo-remainders
/// (no inversion), as `super::Poly::gcd` does for the quartic.
fn gcd9(a: &P9, b: &P9, gf: &Gf2) -> P9 {
    let mut a = *a;
    let mut b = *b;
    loop {
        let db = match deg_of(&b) {
            None => return a,
            Some(0) => return b,
            Some(d) => d,
        };
        let lb = b[db];
        let mut r = a;
        while let Some(dr) = deg_of(&r) {
            if dr < db {
                break;
            }
            let lr = r[dr];
            for c in r[..dr].iter_mut() {
                *c = gf.mul(*c, lb);
            }
            for i in 0..db {
                r[dr - db + i] ^= gf.mul(b[i], lr);
            }
            r[dr] = 0;
        }
        a = b;
        b = r;
    }
}

// ── Rational chains ─────────────────────────────────────────────────

/// Solves `z² + z = δ` over `F_{2ⁿ}` by a reduced basis of the image of
/// the `F₂`-linear map `z ↦ z² + z` (whose kernel is `{0, 1}`), so
/// even and odd `n` go through the same code.
#[derive(Clone, Debug)]
struct ArtinSchreier {
    /// `(pivot bit, image vector, preimage)`, pivots descending, each
    /// vector's highest set bit its pivot.
    rows: Vec<(u32, u64, u64)>,
}

impl ArtinSchreier {
    fn new(gf: &Gf2) -> Self {
        let mut rows: Vec<(u32, u64, u64)> = Vec::new();
        for i in 0..gf.n {
            let e = 1u64 << i;
            let mut v = gf.sqr(e) ^ e;
            let mut pre = e;
            for &(p, rv, rp) in &rows {
                if (v >> p) & 1 == 1 {
                    v ^= rv;
                    pre ^= rp;
                }
            }
            if v != 0 {
                let p = 63 - v.leading_zeros();
                let at = rows.partition_point(|&(q, _, _)| q > p);
                rows.insert(at, (p, v, pre));
            }
        }
        Self { rows }
    }

    fn solve(&self, mut delta: u64) -> Option<u64> {
        let mut z = 0u64;
        for &(p, v, pre) in &self.rows {
            if (delta >> p) & 1 == 1 {
                delta ^= v;
                z ^= pre;
            }
        }
        (delta == 0).then_some(z)
    }
}

/// Roots in `F_{2ⁿ}` of `a U² + c₁ U + c₀`, which must not be the zero
/// polynomial.
fn quadratic_roots(a: u64, c1: u64, c0: u64, gf: &Gf2, as_: &ArtinSchreier) -> ([u64; 2], usize) {
    if a == 0 {
        if c1 == 0 {
            assert!(c0 != 0, "the zero polynomial has every root");
            return ([0; 2], 0);
        }
        return ([gf.mul(c0, gf.inv(c1)), 0], 1);
    }
    let ia = gf.inv(a);
    if c1 == 0 {
        // U² = c₀/a: the unique square root is the (n−1)-th Frobenius.
        return ([gf.sqr_k(gf.mul(c0, ia), gf.n - 1), 0], 1);
    }
    // U = (c₁/a) z turns it into z² + z = a c₀ / c₁².
    let ic1 = gf.inv(c1);
    let delta = gf.mul(gf.mul(a, c0), gf.sqr(ic1));
    match as_.solve(delta) {
        None => ([0; 2], 0),
        Some(z) => {
            let k = gf.mul(c1, ia);
            ([gf.mul(k, z), gf.mul(k, z ^ 1)], 2)
        }
    }
}

/// Roots in `F_{2ⁿ}` of `S₃(x₁, x₂, ·)`.  Never the zero polynomial:
/// that needs `x₁ = x₂` (no `U²` term) and `x₁x₂ = 0` (no `U` term),
/// leaving the constant `b ≠ 0`.
fn s3_roots(x1: u64, x2: u64, b: u64, gf: &Gf2, as_: &ArtinSchreier) -> ([u64; 2], usize) {
    let p = gf.mul(x1, x2);
    quadratic_roots(gf.sqr(x1 ^ x2), p, gf.sqr(p) ^ b, gf, as_)
}

/// Whether the chain `S₃(o₁, o₂, e₁) = S₃(e₁, o₃, e₂) = S₃(e₂, o₄, x_R)
/// = 0` has a solution `e₁, e₂ ∈ F_{2ⁿ}` — the generic system's
/// condition on one ordered tuple.
fn chain_rational(o: [u64; 4], xr: u64, b: u64, gf: &Gf2, as_: &ArtinSchreier) -> bool {
    let (r1, n1) = s3_roots(o[0], o[1], b, gf, as_);
    for &e1 in &r1[..n1] {
        let (r2, n2) = s3_roots(e1, o[2], b, gf, as_);
        for &e2 in &r2[..n2] {
            if s3(e2, o[3], xr, b, gf) == 0 {
                return true;
            }
        }
    }
    false
}

/// Whether some ordering of the multiset `xs` has a rational chain.
/// `S₃` is symmetric, so only which two abscissae close the chain (and
/// in which order) matters: twelve ordered choices at most.
fn any_order_rational(xs: [u64; 4], xr: u64, b: u64, gf: &Gf2, as_: &ArtinSchreier) -> bool {
    let mut tried: Vec<(u64, u64, u64, u64)> = Vec::with_capacity(12);
    for i3 in 0..4 {
        for i4 in 0..4 {
            if i3 == i4 {
                continue;
            }
            let rest: Vec<u64> = (0..4)
                .filter(|&i| i != i3 && i != i4)
                .map(|i| xs[i])
                .collect();
            let (lo, hi) = (rest[0].min(rest[1]), rest[0].max(rest[1]));
            let key = (lo, hi, xs[i3], xs[i4]);
            if tried.contains(&key) {
                continue;
            }
            tried.push(key);
            if chain_rational([lo, hi, xs[i3], xs[i4]], xr, b, gf, as_) {
                return true;
            }
        }
    }
    false
}

// ── The oracle ──────────────────────────────────────────────────────

/// Native counters of one [`TripleOracle`] search.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct M4Counters {
    /// Triples `X₁ ≤ X₂ ≤ X₃` processed: the full
    /// `C(2^l + 2, 3)` when the search runs to the end, fewer when
    /// [`TripleOracle::decompose`] stops at a witness — the analogue of
    /// [`super::SubspaceOracle`]'s pair count.
    pub triples: u64,
    /// Triples whose `gcd(R, L_V mod R)` was non-constant.
    pub gcd_hits: u64,
    /// Triples whose resultant had degree below 8 (or vanished), which
    /// take the generic remainder route.
    pub low_degree: u64,
    /// Distinct candidate multisets checked for a rational chain.
    pub candidates: u64,
    /// Candidates no ordering of which has a rational chain.
    pub chain_rejected: u64,
}

/// **Triples-and-solve over any subspace, for any `b`** — the `m = 4`
/// analogue of [`super::SubspaceOracle`].
#[derive(Clone)]
pub struct TripleOracle {
    /// Dimension of the factor-base subspace.
    pub l: u32,
    /// Curve constant.
    pub b: u64,
    /// Every element of the subspace, indexed by its coordinate word.
    pub span: Vec<u64>,
    /// Coefficients of `L_V`.
    pub lv: Vec<u64>,
    horner: Horner,
    /// `S₄`'s target powers at each span element, which is the third
    /// abscissa's role in the quartic.
    third: Vec<GeneralTargetPowers>,
    artin_schreier: ArtinSchreier,
}

impl std::fmt::Debug for TripleOracle {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("TripleOracle")
            .field("l", &self.l)
            .field("b", &self.b)
            .field("span", &self.span)
            .field("lv", &self.lv)
            .finish_non_exhaustive()
    }
}

impl TripleOracle {
    /// The oracle for the span of `basis` on the curve with constant
    /// `b`.  Panics if `b = 0` or the basis is dependent, as
    /// [`super::SubspaceOracle::new`] does.
    pub fn new(basis: &[u64], b: u64, gf: &Gf2) -> Self {
        let inner = super::SubspaceOracle::new(basis, b, gf);
        let lv = subspace_poly_for_basis(basis, gf);
        debug_assert_eq!(lv, inner.lv);
        let horner = Horner::new(&lv, gf);
        let third = inner
            .span
            .iter()
            .map(|&x| GeneralTargetPowers::new(x, b, gf))
            .collect();
        Self {
            l: inner.l,
            b,
            span: inner.span,
            lv,
            horner,
            third,
            artin_schreier: ArtinSchreier::new(gf),
        }
    }

    /// The low-order subspace `⟨1, z, …, z^{l−1}⟩`.
    pub fn low_order(l: u32, b: u64, gf: &Gf2) -> Self {
        let basis: Vec<u64> = (0..l).map(|i| 1u64 << i).collect();
        Self::new(&basis, b, gf)
    }

    /// Whether the abscissae `xs` (in any order) decompose `x_R` in the
    /// generic chain's sense: some ordering has rational intermediate
    /// abscissae.  Does not check that the `xs` lie in the subspace.
    pub fn chain_check(&self, xs: [u64; 4], xr: u64, gf: &Gf2) -> bool {
        any_order_rational(xs, xr, self.b, gf, &self.artin_schreier)
    }

    /// A target that the ordered abscissae `xs` decompose through a
    /// rational chain (the first such, roots taken in the order the
    /// quadratic solver returns them), or `None` when no chain through
    /// them is rational.  For planting decomposable targets.
    pub fn chain_target(&self, xs: [u64; 4], gf: &Gf2) -> Option<u64> {
        let as_ = &self.artin_schreier;
        let (r1, n1) = s3_roots(xs[0], xs[1], self.b, gf, as_);
        for &e1 in &r1[..n1] {
            let (r2, n2) = s3_roots(e1, xs[2], self.b, gf, as_);
            for &e2 in &r2[..n2] {
                let (r3, n3) = s3_roots(e2, xs[3], self.b, gf, as_);
                if n3 > 0 {
                    return Some(r3[0]);
                }
            }
        }
        None
    }

    /// **Every decomposition of `x_R`**: the multisets `{X₁, …, X₄}` of
    /// subspace abscissae with a rational chain, each sorted ascending,
    /// the list sorted — exactly the summand tuples of
    /// [`decompose_all_generic`]'s roots, in the same order.
    pub fn decompose_all(&self, xr: u64, gf: &Gf2) -> (Vec<[u64; 4]>, M4Counters) {
        let mut out = BTreeSet::new();
        let ctr = self.search(xr, gf, false, &mut out);
        (out.into_iter().collect(), ctr)
    }

    /// **Does `x_R` decompose?**  The first decomposition the triple
    /// loop meets (triples in span-index order `i₁ ≤ i₂ ≤ i₃`; within
    /// the triple that meets one, the least multiset), sorted, and the
    /// number of triples processed up to and including that triple —
    /// all of them when it refutes.
    pub fn decompose(&self, xr: u64, gf: &Gf2) -> (Option<[u64; 4]>, u64) {
        let mut out = BTreeSet::new();
        let ctr = self.search(xr, gf, true, &mut out);
        (out.into_iter().next(), ctr.triples)
    }

    fn search(&self, xr: u64, gf: &Gf2, first: bool, out: &mut BTreeSet<[u64; 4]>) -> M4Counters {
        // As [`super::SubspaceOracle::decompose`]: compile the loop with
        // the carry-less multiply enabled where the CPU has it.
        #[cfg(target_arch = "x86_64")]
        if gf.has_clmul {
            // SAFETY: `has_clmul` records `is_x86_feature_detected!("pclmulqdq")`.
            return unsafe { self.search_pclmulqdq(xr, gf, first, out) };
        }
        self.search_body(xr, gf, first, out)
    }

    #[cfg(target_arch = "x86_64")]
    #[target_feature(enable = "pclmulqdq")]
    unsafe fn search_pclmulqdq(
        &self,
        xr: u64,
        gf: &Gf2,
        first: bool,
        out: &mut BTreeSet<[u64; 4]>,
    ) -> M4Counters {
        self.search_body(xr, gf, first, out)
    }

    #[inline(always)]
    fn search_body(
        &self,
        xr: u64,
        gf: &Gf2,
        first: bool,
        out: &mut BTreeSet<[u64; 4]>,
    ) -> M4Counters {
        let table = ResultantTable::new(xr, self.b, gf);
        let span = &self.span;
        let count = span.len();
        let mut ctr = M4Counters::default();
        let mut seen: BTreeSet<[u64; 4]> = BTreeSet::new();

        let mut rs: Vec<P9> = Vec::with_capacity(count);
        let mut leads: Vec<u64> = Vec::with_capacity(count);
        let mut scratch: Vec<u64> = Vec::with_capacity(count);
        let mut roots: Vec<u64> = Vec::new();

        for i1 in 0..count {
            let x1 = span[i1];
            for i2 in i1..count {
                let x2 = span[i2];
                rs.clear();
                leads.clear();
                for i3 in i2..count {
                    let q = quartic_general_with(x1, x2, &self.third[i3], gf);
                    let a = [q.c[0], q.c[1], q.c[2], q.c[3], q.c[4]];
                    let r = table.apply(&a, gf);
                    leads.push(deg_of(&r).map_or(0, |d| r[d]));
                    rs.push(r);
                }
                gf.batch_inv(&mut leads, &mut scratch);

                for (k, r) in rs.iter().enumerate() {
                    let x3 = span[i2 + k];
                    ctr.triples += 1;
                    roots.clear();
                    match deg_of(r) {
                        // A non-zero constant has no roots.
                        Some(0) => continue,
                        // The resultant vanishes identically: every
                        // subspace element is a candidate.
                        None => {
                            ctr.low_degree += 1;
                            ctr.gcd_hits += 1;
                            roots.extend_from_slice(span);
                        }
                        Some(d) => {
                            let inv = leads[k];
                            let mut f = [0u64; OCT + 1];
                            for j in 0..d {
                                f[j] = gf.mul(r[j], inv);
                            }
                            f[d] = 1;
                            let g = if d == OCT {
                                let low: [u64; OCT] = f[..OCT].try_into().expect("eight");
                                let u = lv_mod_octic(&low, &self.horner, gf);
                                let mut g = [0u64; OCT + 1];
                                g[..OCT].copy_from_slice(&u);
                                gcd9(&f, &g, gf)
                            } else {
                                ctr.low_degree += 1;
                                gcd9(&f, &lv_mod_generic(&f, d, &self.lv, gf), gf)
                            };
                            match deg_of(&g) {
                                None | Some(0) => continue,
                                Some(1) => {
                                    ctr.gcd_hits += 1;
                                    roots.push(gf.mul(g[0], gf.inv(g[1])));
                                }
                                Some(_) => {
                                    // Several subspace roots (distinct:
                                    // `L_V` is squarefree).  Rare, so
                                    // find them by evaluation.
                                    ctr.gcd_hits += 1;
                                    roots.extend(
                                        span.iter().copied().filter(|&t| eval(&g, t, gf) == 0),
                                    );
                                }
                            }
                        }
                    }
                    let mut hit = false;
                    for &x4 in &roots {
                        let mut m = [x1, x2, x3, x4];
                        m.sort_unstable();
                        if !seen.insert(m) {
                            hit |= out.contains(&m);
                            continue;
                        }
                        ctr.candidates += 1;
                        if any_order_rational(m, xr, self.b, gf, &self.artin_schreier) {
                            out.insert(m);
                            hit = true;
                        } else {
                            ctr.chain_rejected += 1;
                        }
                    }
                    if first && hit {
                        // Keep only this triple's least decomposition
                        // (an earlier triple met none).
                        let least = roots
                            .iter()
                            .map(|&x4| {
                                let mut m = [x1, x2, x3, x4];
                                m.sort_unstable();
                                m
                            })
                            .filter(|m| out.contains(m))
                            .min()
                            .expect("a hit is in the set");
                        out.clear();
                        out.insert(least);
                        return ctr;
                    }
                }
            }
        }
        ctr
    }
}

// ── The generic path and the dispatch ───────────────────────────────

/// The `IrreduciblePoly` a [`Gf2`] was built from.
fn irreducible_of(gf: &Gf2) -> IrreduciblePoly {
    IrreduciblePoly {
        degree: gf.n,
        low_terms: (0..gf.n).filter(|&k| (gf.irr >> k) & 1 == 1).collect(),
    }
}

/// **The generic `m = 4` path**: the chained `S₃` system of
/// [`build_decomposition_system_reusing`] solved for every root by
/// [`solve_boolean_system`] (default engine and split rule, in the
/// interleaved chain order `groebner_decompose` uses), each root's four
/// summand abscissae sorted, the set returned sorted.
///
/// `None` when the system cannot be built (`4l + 2n` above the solver's
/// variable cap) or the node budget ran out, so the root set may be
/// incomplete.
pub fn decompose_all_generic(
    basis: &[u64],
    xr: u64,
    b: u64,
    gf: &Gf2,
    node_budget: usize,
) -> Option<(Vec<[u64; 4]>, SolveStats)> {
    let n = gf.n;
    let st = FieldStructure::new(n, &irreducible_of(gf));
    let basis_e: Vec<F2mElement> = basis.iter().map(|&v| gf.to_element(v)).collect();
    let sys = build_decomposition_system_reusing(
        &basis_e,
        &gf.to_element(xr),
        &gf.to_element(b),
        4,
        &st,
    )?;
    let opts = SolveOptions {
        engine: SolverEngine::default(),
        max_solutions: usize::MAX,
        node_budget,
        split_rule: split_rule_default(),
    };
    let order =
        chain_order_interleaved(opts.resolve().split_rule).then(|| sys.interleaved_order(n));
    let equations: Vec<_> = match &order {
        Some(perm) => sys
            .equations
            .iter()
            .map(|e| permute_poly(e, perm))
            .collect(),
        None => sys.equations.clone(),
    };
    let (roots, stats) = solve_boolean_system(&equations, sys.n_vars, &opts);
    if stats.exhausted {
        return None;
    }
    let back = order.as_deref().map(invert_permutation);
    let mut out = BTreeSet::new();
    for root in roots {
        let root = back.as_deref().map_or(root, |inv| permute_mask(root, inv));
        let mut m = [0u64; 4];
        for (i, x) in m.iter_mut().enumerate() {
            *x = gf.from_element(&sys.summand_x(&basis_e, root, i, n));
        }
        m.sort_unstable();
        out.insert(m);
    }
    Some((out.into_iter().collect(), stats))
}

/// The largest factor-base dimension [`M4Path::Auto`] sends to the
/// linearised route.  A cost bound, not a measured crossover: the triple
/// loop visits `C(2^l + 2, 3) ≈ 2^{3l}/6` triples and holds `2^l` target
/// tables, so at `l = 10` that is already about `1.8·10⁸` triples per
/// target; past it [`M4Path::Auto`] takes the generic route, which
/// declines a system over its unknown cap at once.  An explicit
/// [`M4Path::Linearised`] is not capped.
pub const AUTO_LINEARISED_MAX_DIM: usize = 10;

/// Whether `basis` is linearly independent over `F₂`.
fn f2_independent(basis: &[u64]) -> bool {
    let mut rows: Vec<u64> = Vec::with_capacity(basis.len());
    for &v in basis {
        let r = rows.iter().fold(v, |r, &p| r.min(r ^ p));
        if r == 0 {
            return false;
        }
        rows.push(r);
        rows.sort_unstable_by(|a, b| b.cmp(a));
    }
    true
}

/// Which `m = 4` decomposition route [`decompose_all_m4`] runs.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum M4Path {
    /// [`TripleOracle::decompose_all`] when the basis is `F₂`-independent,
    /// its dimension is at most [`AUTO_LINEARISED_MAX_DIM`] and the curve
    /// is non-singular, the generic chain otherwise.
    Auto,
    /// The linearised triples oracle.
    Linearised,
    /// The chained `S₃` system and the Boolean solver.
    Generic,
}

/// What [`decompose_all_m4`] returns: the decompositions and which
/// route produced them.
#[derive(Clone, Debug)]
pub struct M4Outcome {
    /// Sorted multisets of abscissae, sorted; `None` when the generic
    /// route could not decide (see [`decompose_all_generic`]).
    pub decompositions: Option<Vec<[u64; 4]>>,
    /// The route that ran.
    pub path: M4Path,
    /// The linearised route's counters (zero on the generic route).
    pub counters: M4Counters,
}

/// **All `m = 4` decompositions of `x_R` over the span of `basis`**,
/// by the route `path` selects; both routes return the same list where
/// both decide.
pub fn decompose_all_m4(
    basis: &[u64],
    xr: u64,
    b: u64,
    gf: &Gf2,
    path: M4Path,
    node_budget: usize,
) -> M4Outcome {
    let linearised = match path {
        M4Path::Auto => basis.len() <= AUTO_LINEARISED_MAX_DIM && b != 0 && f2_independent(basis),
        M4Path::Linearised => true,
        M4Path::Generic => false,
    };
    if linearised {
        let oracle = TripleOracle::new(basis, b, gf);
        let (d, counters) = oracle.decompose_all(xr, gf);
        M4Outcome {
            decompositions: Some(d),
            path: M4Path::Linearised,
            counters,
        }
    } else {
        M4Outcome {
            decompositions: decompose_all_generic(basis, xr, b, gf, node_budget).map(|(d, _)| d),
            path: M4Path::Generic,
            counters: M4Counters::default(),
        }
    }
}

#[cfg(test)]
mod tests;
