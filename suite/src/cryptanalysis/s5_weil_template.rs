//! # `m = 4` Weil descent from a hardcoded `S₅`, restricted once per subspace.
//!
//! The generic decomposition system for `R = P₁ + P₂ + P₃ + P₄`
//! ([`build_decomposition_system`](crate::cryptanalysis::koblitz_groebner::build_decomposition_system),
//! reused through [`build_decomposition_system_reusing`]) chains three
//! `S₃` links and pays `(m − 2)·n = 2n` intermediate unknowns for it: at
//! `n = 17`, `ℓ = 3` that is 46 Boolean unknowns, 34 of them for points
//! nobody asked about.  This module descends Semaev's fifth summation
//! polynomial `S₅(x₁, x₂, x₃, x₄, x_R)` directly instead, so the system
//! has the `4ℓ` subspace unknowns and nothing else.
//!
//! ## The template
//!
//! `S₅` is fixed (hardcoded below as its 106 orbits under permuting
//! `x₁ … x₄`, pinned by a test to
//! [`semaev(4)`](crate::cryptanalysis::semaev_leading_form::semaev)), so
//! for a field, a subspace basis and the curve coefficient `b = a₆` it is
//!
//! ```text
//!   S₅ = Σ_{e=0}^{8} C_e(x₁, x₂, x₃, x₄) · x_R^e,
//! ```
//!
//! and every `C_e` is target-independent.  [`S5Template::build_x`]
//! restricts the nine `C_e` once — as `F_{2^n}`-valued Boolean
//! polynomials, one field coefficient per monomial — and
//! [`S5Template::instantiate`] forms `Σ_e C_e · x_R^e` per target: nine
//! constant multiplications per monomial, then the `n` coordinate
//! equations are read back.  No symbolic field arithmetic runs per target.
//!
//! The restriction is computed by **evaluation and Möbius inversion**,
//! not by symbolic multiplication.  Each `C_e` is a function of the `4ℓ`
//! bits, evaluated on all `2^{4ℓ}` points by contracting one summand
//! block at a time (`Σ_{e₄} c · x₄^{e₄}`, then `x₃`, …: about
//! `81 · 2^{4ℓ}` field products for the last block), and the algebraic
//! normal form of the values — the multilinear Boolean polynomial, which
//! is unique — is their binary Möbius transform, done on `n`-bit words so
//! all coordinates at once.  The result is the same polynomials, term for
//! term, as Weil-restricting `S₅` with
//! [`SymElement`](crate::cryptanalysis::koblitz_groebner::SymElement)
//! arithmetic (`templates_equal_the_symbolic_restriction`), at a cost
//! that does not depend on how many terms `S₅` has.  It is dense in
//! `2^{4ℓ}`, so it is capped at [`MAX_DENSE_VARS`] unknowns.
//!
//! ## The symmetrised variant
//!
//! `S₅` is symmetric in `x₁ … x₄`, so it is a polynomial in their
//! elementary symmetric functions `e₁ … e₄` (100 terms, also hardcoded
//! and pinned).  With every `xᵢ` in `V = span(basis)`, `e_k` lies in
//! `W_k = span{b_{t₁} ⋯ b_{t_k}}` (products of `k` basis vectors,
//! repetition allowed), so [`S5Template::build_symmetrised`] takes the
//! coordinates of `e_k` in a basis of `W_k` as the unknowns: `Σ dim W_k`
//! of them (`2 + 3 + 4 + 5 = 14` for `ℓ = 2`, generically
//! `Σ_k C(ℓ+k−1, k)`), one root per *unordered* decomposition instead of
//! up to `4!` ordered ones, and lower degree per block.  A root is
//! accepted only when `T⁴ + e₁T³ + e₂T² + e₃T + e₄` splits over `V`
//! (roots counted with multiplicity); the rest are spurious, counted, and
//! dropped.  The unknown count grows as `ℓ⁴/24`, so this variant is only
//! available for small `ℓ` (the same [`MAX_DENSE_VARS`] cap).
//!
//! ## What is returned, and in which order
//!
//! A *decomposition* here is the sorted list of factor-base indices of
//! four points summing to `R` whose abscissae form a root.
//! [`decompose_all_m4`] returns all of them as a sorted set, for every
//! [`M4Descent`]: the chained system, the `S₅` template and the
//! symmetrised template give **the same set** wherever all three run
//! (pinned by the differential tests below against each other and against
//! brute force over `V⁴`).  Their raw root sets differ, and that is
//! expected: a chained root projects to an `x`-tuple whose intermediate
//! points are `F_{2^n}`-rational, while `S₅` vanishes whenever the
//! intermediates exist over the algebraic closure, so the `S₅` roots are
//! a superset whose extra members never lift (a rational decomposition
//! has rational partial sums).  [`M4Outcome::roots`] counts them.
//!
//! [`groebner_decompose_m4`] is the first-found oracle
//! [`groebner_decompose`] is for the chain: it stops at the first root that
//! lifts.  Which decomposition that is depends on the search order of the
//! system being solved, so the specialised and the chained oracle may
//! return different members of the same set; whether one is found at all
//! is the same (tested).  [`groebner_decompose`] dispatches to it for
//! `m = 4` when `KIC_M4_DESCENT=s5` (opt-in; `s5sym` is not an
//! environment choice); unset (or anything else) keeps the chain, which
//! also stays the fallback whenever a template cannot be built (unknowns
//! past [`MAX_DENSE_VARS`], `n` outside `2..=64`).
//!
//! ## Solving, and what it costs
//!
//! The template system is small but dense: Boolean degree up to
//! `m(m−1) = 12` (three per summand block) and over a thousand terms an
//! equation at `ℓ = 3`, where the chain is cubic with a few dozen.  The
//! Gröbner engines consume it unchanged, except that the default
//! [`SolverEngine::InheritedF4`] is run as [`SolverEngine::MatrixF4`]
//! ([`template_engine`]): same row space, same roots, about a tenth of the work
//! on these rows.  Whether the template beats the chain then depends on
//! the cell — it wins where the chain's `2n` intermediates dominate
//! (`n ≥ 17` at `ℓ = 3`) and loses where its own `4ℓ`-variable tree does
//! (`ℓ = 4`) or where the chain is already cheap (the subfield `F_8` at
//! `n = 15`); the perfbench kernels `pdp/spec_s5_*` pin those cells.
//!
//! ## Scope
//!
//! Binary curves `y² + xy = x³ + a x² + b` (the summation polynomials
//! depend on `b` only), subspace factor bases, `m = 4` only.  Only the
//! Gröbner engines consume these systems here; SAT, crossbred, WDSat and
//! SMT still take the chain.

use std::cell::RefCell;
use std::collections::{BTreeMap, BTreeSet, HashMap};
use std::rc::Rc;

use num_bigint::BigUint;

use crate::binary_ecc::{BinaryPoint, F2mElement};
use crate::cryptanalysis::koblitz_groebner::{
    chain_order_interleaved, invert_permutation, permute_mask, permute_poly,
    solve_boolean_system_filtered, split_rule_default, FieldStructure, SolveOptions, SolveStats,
    SolverEngine,
};
use crate::cryptanalysis::koblitz_index_calculus::{
    groebner_decompose, lift_candidate, point_key, points_with_x, FrobeniusFactorBase, KoblitzCurve,
};
use crate::cryptanalysis::polynomial_reuse::build_decomposition_system_reusing;
use crate::cryptanalysis::pq_groebner_f2::{sort_masks_descending, F2BoolMono, F2BoolPoly};

/// Number of summands this module serves.
pub const M: usize = 4;

/// Largest number of Boolean unknowns a template is built for: the
/// restriction is dense in `2^{unknowns}` (one `n`-bit word per point,
/// 8 MiB at this cap, one `x_R` power at a time).
pub const MAX_DENSE_VARS: usize = 20;

/// Powers of `x_R` in `S₅`: `deg_{x_R} S₅ = 2^{m−1} = 8`.
const NE: usize = 9;

/// `S₅(x₁, x₂, x₃, x₄, x_R)` for `y² + xy = x³ + a x² + b`, as its orbits
/// under permuting `x₁ … x₄`: `(sorted exponents of x₁…x₄, exponent of
/// x_R, exponent of b)`, every coefficient `1`.  The 729 terms are the
/// distinct permutations of these 106 entries.  Generated from
/// [`crate::cryptanalysis::semaev_leading_form::semaev`]`(4)` and pinned
/// to it by `hardcoded_s5_is_semaev_4`.
#[rustfmt::skip]
const S5_ORBITS: &[([u8; 4], u8, u8)] = &[
    ([0, 0, 0, 0], 0, 8),
    ([0, 0, 0, 8], 8, 4),
    ([0, 0, 4, 4], 4, 4),
    ([0, 0, 8, 8], 0, 4),
    ([0, 2, 2, 2], 2, 5),
    ([0, 2, 2, 6], 6, 3),
    ([0, 2, 6, 6], 2, 3),
    ([0, 4, 4, 4], 0, 4),
    ([0, 4, 4, 4], 8, 2),
    ([0, 4, 4, 8], 4, 2),
    ([0, 6, 6, 6], 6, 1),
    ([0, 8, 8, 8], 8, 0),
    ([1, 1, 1, 1], 1, 6),
    ([1, 1, 1, 3], 3, 5),
    ([1, 1, 1, 5], 5, 4),
    ([1, 1, 1, 7], 7, 3),
    ([1, 1, 3, 3], 1, 5),
    ([1, 1, 3, 3], 3, 4),
    ([1, 1, 3, 5], 5, 3),
    ([1, 1, 3, 5], 7, 3),
    ([1, 1, 3, 7], 5, 3),
    ([1, 1, 5, 5], 1, 4),
    ([1, 1, 5, 5], 3, 3),
    ([1, 1, 5, 7], 3, 3),
    ([1, 1, 7, 7], 1, 3),
    ([1, 3, 3, 3], 1, 4),
    ([1, 3, 3, 3], 3, 4),
    ([1, 3, 3, 5], 5, 3),
    ([1, 3, 3, 5], 7, 2),
    ([1, 3, 3, 7], 5, 2),
    ([1, 3, 3, 7], 7, 2),
    ([1, 3, 5, 5], 1, 3),
    ([1, 3, 5, 5], 3, 3),
    ([1, 3, 5, 7], 1, 3),
    ([1, 3, 5, 7], 3, 2),
    ([1, 3, 7, 7], 3, 2),
    ([1, 5, 5, 5], 5, 2),
    ([1, 5, 5, 5], 7, 1),
    ([1, 5, 5, 7], 5, 1),
    ([1, 5, 5, 7], 7, 1),
    ([1, 5, 7, 7], 5, 1),
    ([1, 7, 7, 7], 7, 0),
    ([2, 2, 2, 2], 0, 5),
    ([2, 2, 2, 2], 4, 4),
    ([2, 2, 2, 4], 2, 4),
    ([2, 2, 2, 4], 4, 3),
    ([2, 2, 2, 4], 6, 3),
    ([2, 2, 2, 6], 4, 3),
    ([2, 2, 2, 6], 8, 2),
    ([2, 2, 2, 8], 6, 2),
    ([2, 2, 4, 4], 2, 3),
    ([2, 2, 4, 4], 6, 2),
    ([2, 2, 4, 6], 2, 3),
    ([2, 2, 4, 6], 4, 2),
    ([2, 2, 4, 6], 6, 2),
    ([2, 2, 6, 6], 0, 3),
    ([2, 2, 6, 6], 4, 2),
    ([2, 2, 6, 8], 2, 2),
    ([2, 4, 4, 6], 2, 2),
    ([2, 4, 4, 6], 6, 1),
    ([2, 4, 6, 6], 2, 2),
    ([2, 4, 6, 6], 4, 1),
    ([2, 4, 6, 6], 6, 1),
    ([2, 6, 6, 6], 4, 1),
    ([2, 6, 6, 6], 8, 0),
    ([2, 6, 6, 8], 6, 0),
    ([3, 3, 3, 3], 1, 4),
    ([3, 3, 3, 3], 5, 2),
    ([3, 3, 3, 5], 3, 2),
    ([3, 3, 3, 5], 7, 2),
    ([3, 3, 3, 7], 5, 2),
    ([3, 3, 3, 7], 7, 1),
    ([3, 3, 5, 5], 1, 3),
    ([3, 3, 5, 5], 5, 1),
    ([3, 3, 5, 7], 1, 2),
    ([3, 3, 5, 7], 3, 2),
    ([3, 3, 7, 7], 1, 2),
    ([3, 3, 7, 7], 3, 1),
    ([3, 5, 5, 5], 3, 1),
    ([3, 5, 5, 5], 7, 1),
    ([3, 5, 5, 7], 5, 1),
    ([3, 5, 5, 7], 7, 0),
    ([3, 5, 7, 7], 5, 0),
    ([3, 5, 7, 7], 7, 0),
    ([3, 7, 7, 7], 5, 0),
    ([4, 4, 4, 4], 4, 1),
    ([4, 4, 4, 8], 0, 2),
    ([4, 4, 4, 8], 8, 0),
    ([4, 4, 6, 6], 2, 1),
    ([4, 4, 6, 6], 6, 0),
    ([4, 4, 8, 8], 4, 0),
    ([4, 6, 6, 6], 2, 1),
    ([4, 6, 6, 6], 4, 0),
    ([4, 6, 6, 6], 6, 0),
    ([5, 5, 5, 5], 1, 2),
    ([5, 5, 5, 5], 5, 0),
    ([5, 5, 5, 7], 1, 1),
    ([5, 5, 5, 7], 3, 1),
    ([5, 5, 7, 7], 1, 1),
    ([5, 5, 7, 7], 3, 0),
    ([5, 7, 7, 7], 3, 0),
    ([6, 6, 6, 6], 0, 1),
    ([6, 6, 6, 6], 4, 0),
    ([6, 6, 6, 8], 2, 0),
    ([7, 7, 7, 7], 1, 0),
    ([8, 8, 8, 8], 0, 0),];

/// `S₅` in the elementary symmetric functions `e₁ … e₄` of `x₁ … x₄`:
/// `(exponents of e₁, e₂, e₃, e₄, exponent of x_R, exponent of b)`, every
/// coefficient `1`.  100 terms; pinned by
/// `hardcoded_symmetric_s5_expands_to_semaev_4`.
#[rustfmt::skip]
const S5_SYMMETRIC: &[([u8; 4], u8, u8)] = &[
    ([0, 0, 0, 0], 0, 8),
    ([0, 0, 0, 1], 1, 6),
    ([0, 0, 0, 2], 0, 5),
    ([0, 0, 0, 2], 4, 4),
    ([0, 0, 0, 3], 1, 4),
    ([0, 0, 0, 3], 5, 2),
    ([0, 0, 0, 4], 4, 1),
    ([0, 0, 0, 5], 1, 2),
    ([0, 0, 0, 5], 5, 0),
    ([0, 0, 0, 6], 0, 1),
    ([0, 0, 0, 6], 4, 0),
    ([0, 0, 0, 7], 1, 0),
    ([0, 0, 0, 8], 0, 0),
    ([0, 0, 2, 0], 2, 5),
    ([0, 0, 2, 1], 1, 4),
    ([0, 0, 2, 1], 3, 4),
    ([0, 0, 2, 1], 5, 3),
    ([0, 0, 2, 2], 4, 2),
    ([0, 0, 2, 3], 1, 2),
    ([0, 0, 2, 3], 3, 1),
    ([0, 0, 2, 3], 5, 1),
    ([0, 0, 2, 4], 2, 1),
    ([0, 0, 2, 4], 4, 0),
    ([0, 0, 2, 5], 3, 0),
    ([0, 0, 4, 0], 0, 4),
    ([0, 0, 4, 0], 8, 2),
    ([0, 0, 4, 1], 3, 2),
    ([0, 0, 4, 1], 5, 2),
    ([0, 0, 4, 1], 7, 1),
    ([0, 0, 4, 2], 4, 1),
    ([0, 0, 4, 2], 8, 0),
    ([0, 0, 4, 3], 5, 0),
    ([0, 0, 6, 0], 6, 1),
    ([0, 0, 6, 1], 7, 0),
    ([0, 0, 8, 0], 8, 0),
    ([0, 2, 0, 1], 1, 5),
    ([0, 2, 0, 1], 3, 4),
    ([0, 2, 0, 2], 2, 3),
    ([0, 2, 0, 2], 6, 2),
    ([0, 2, 0, 3], 5, 1),
    ([0, 2, 0, 4], 2, 1),
    ([0, 2, 0, 4], 6, 0),
    ([0, 2, 0, 5], 1, 1),
    ([0, 2, 0, 5], 3, 0),
    ([0, 2, 2, 1], 1, 3),
    ([0, 2, 2, 2], 4, 1),
    ([0, 2, 2, 3], 5, 0),
    ([0, 2, 4, 1], 5, 1),
    ([0, 4, 0, 0], 4, 4),
    ([0, 4, 0, 1], 1, 4),
    ([0, 4, 0, 1], 3, 3),
    ([0, 4, 0, 2], 0, 3),
    ([0, 4, 0, 2], 4, 2),
    ([0, 4, 0, 3], 1, 2),
    ([0, 4, 0, 3], 3, 1),
    ([0, 4, 0, 4], 4, 0),
    ([0, 4, 2, 0], 2, 3),
    ([0, 4, 2, 1], 3, 2),
    ([0, 6, 0, 1], 1, 3),
    ([0, 8, 0, 0], 0, 4),
    ([2, 0, 0, 1], 3, 5),
    ([2, 0, 0, 2], 2, 4),
    ([2, 0, 0, 2], 4, 3),
    ([2, 0, 0, 3], 1, 3),
    ([2, 0, 0, 3], 3, 2),
    ([2, 0, 0, 3], 5, 2),
    ([2, 0, 0, 4], 4, 1),
    ([2, 0, 0, 5], 1, 1),
    ([2, 0, 0, 5], 3, 1),
    ([2, 0, 0, 5], 5, 0),
    ([2, 0, 0, 6], 2, 0),
    ([2, 0, 2, 1], 7, 2),
    ([2, 0, 2, 2], 2, 2),
    ([2, 0, 2, 2], 6, 1),
    ([2, 0, 2, 3], 7, 0),
    ([2, 0, 4, 1], 5, 1),
    ([2, 0, 4, 1], 7, 1),
    ([2, 0, 4, 2], 6, 0),
    ([2, 2, 0, 1], 5, 3),
    ([2, 2, 0, 2], 4, 2),
    ([2, 2, 0, 3], 1, 2),
    ([2, 2, 2, 1], 3, 2),
    ([2, 4, 0, 1], 3, 3),
    ([2, 4, 0, 2], 2, 2),
    ([4, 0, 0, 1], 5, 4),
    ([4, 0, 0, 2], 4, 3),
    ([4, 0, 0, 2], 8, 2),
    ([4, 0, 0, 3], 3, 2),
    ([4, 0, 0, 3], 5, 2),
    ([4, 0, 0, 3], 7, 1),
    ([4, 0, 0, 4], 0, 2),
    ([4, 0, 0, 4], 8, 0),
    ([4, 0, 2, 0], 6, 3),
    ([4, 0, 2, 1], 5, 2),
    ([4, 0, 2, 1], 7, 2),
    ([4, 0, 4, 0], 4, 2),
    ([4, 2, 0, 1], 5, 3),
    ([6, 0, 0, 1], 7, 3),
    ([6, 0, 0, 2], 6, 2),
    ([8, 0, 0, 0], 8, 4),];

/// The 729 terms of `S₅` in `x`: every distinct permutation of the
/// summand exponents of each orbit in [`S5_ORBITS`].
fn s5_x_terms() -> Vec<([u8; 4], u8, u8)> {
    let mut out = BTreeSet::new();
    for &(e, e5, j) in S5_ORBITS {
        for p in PERMUTATIONS_4 {
            out.insert(([e[p[0]], e[p[1]], e[p[2]], e[p[3]]], e5, j));
        }
    }
    out.into_iter().collect()
}

const PERMUTATIONS_4: [[usize; 4]; 24] = {
    let mut out = [[0usize; 4]; 24];
    let mut k = 0;
    let mut a = 0;
    while a < 4 {
        let mut b = 0;
        while b < 4 {
            let mut c = 0;
            while c < 4 {
                if a != b && a != c && b != c && a + b + c >= 3 {
                    let d = 6 - a - b - c;
                    out[k] = [a, b, c, d];
                    k += 1;
                }
                c += 1;
            }
            b += 1;
        }
        a += 1;
    }
    out
};

// ── Constant field arithmetic ──────────────────────────────────────

/// `F_{2^n}` on `u64` words, from the structure constants of a
/// [`FieldStructure`]: a product is a carry-less multiplication by 4-bit
/// windows followed by a byte-table reduction of its high half.
#[derive(Clone, Debug)]
struct Gf2n {
    n: u32,
    mask: u64,
    /// `z^n mod f`.
    zn: u64,
    /// `fold[j][v] = (v · z^{n + 8j}) mod f`.
    fold: Vec<[u64; 256]>,
}

impl Gf2n {
    /// `None` outside `2 ≤ n ≤ 64` or for tables short of `n × n`.
    fn new(st: &FieldStructure) -> Option<Self> {
        let n = st.n;
        if !(2..=64).contains(&n)
            || st.reduced.len() < n as usize
            || st.reduced[..n as usize]
                .iter()
                .any(|r| r.len() < n as usize)
        {
            return None;
        }
        let mask = if n == 64 { u64::MAX } else { (1u64 << n) - 1 };
        let zn = st.reduced[n as usize - 1][1] & mask;
        let mut f = Self {
            n,
            mask,
            zn,
            fold: Vec::new(),
        };
        let bytes = (n as usize - 1).div_ceil(8);
        let mut row = zn;
        for _ in 0..bytes {
            let mut table = [0u64; 256];
            let mut rows = [0u64; 8];
            for r in rows.iter_mut() {
                *r = row;
                row = f.mulz(row);
            }
            for v in 1..256usize {
                table[v] = table[v & (v - 1)] ^ rows[v.trailing_zeros() as usize];
            }
            f.fold.push(table);
        }
        Some(f)
    }

    /// `x · z`.
    fn mulz(&self, x: u64) -> u64 {
        let top = (x >> (self.n - 1)) & 1;
        ((x << 1) & self.mask) ^ if top == 1 { self.zn } else { 0 }
    }

    fn reduce(&self, p: u128) -> u64 {
        let mut lo = (p as u64) & self.mask;
        let mut hi = p >> self.n;
        let mut j = 0;
        while hi != 0 {
            lo ^= self.fold[j][(hi & 0xff) as usize];
            hi >>= 8;
            j += 1;
        }
        lo
    }

    /// The 16 carry-less multiples of `a` by a nibble.
    fn window(a: u64) -> [u128; 16] {
        let mut w = [0u128; 16];
        for v in 1..16usize {
            w[v] = w[v & (v - 1)] ^ (u128::from(a) << v.trailing_zeros());
        }
        w
    }

    fn mul_window(&self, w: &[u128; 16], mut b: u64) -> u64 {
        let mut acc = 0u128;
        let mut shift = 0;
        while b != 0 {
            acc ^= w[(b & 15) as usize] << shift;
            b >>= 4;
            shift += 4;
        }
        self.reduce(acc)
    }

    fn mul(&self, a: u64, b: u64) -> u64 {
        self.mul_window(&Self::window(a), b)
    }

    /// `[1, a, a², …, a^{len−1}]`.
    fn powers(&self, a: u64, len: usize) -> Vec<u64> {
        let mut out = Vec::with_capacity(len);
        let mut p = 1u64;
        for _ in 0..len {
            out.push(p);
            p = self.mul(p, a);
        }
        out
    }
}

/// Multiplication by one constant `c`, as byte tables of the linear map
/// `x ↦ c·x`: `⌈n/8⌉` lookups a product.
struct ConstMul {
    tables: Vec<[u64; 256]>,
}

impl ConstMul {
    fn new(f: &Gf2n, c: u64) -> Self {
        let bytes = (f.n as usize).div_ceil(8);
        let mut row = c;
        let mut tables = Vec::with_capacity(bytes);
        for _ in 0..bytes {
            let mut rows = [0u64; 8];
            for r in rows.iter_mut() {
                *r = row;
                row = f.mulz(row);
            }
            let mut table = [0u64; 256];
            for v in 1..256usize {
                table[v] = table[v & (v - 1)] ^ rows[v.trailing_zeros() as usize];
            }
            tables.push(table);
        }
        Self { tables }
    }

    #[inline]
    fn apply(&self, mut x: u64) -> u64 {
        let mut acc = 0;
        for t in &self.tables {
            acc ^= t[(x & 0xff) as usize];
            x >>= 8;
        }
        acc
    }
}

fn bits_of(e: &F2mElement) -> u64 {
    e.raw_bits().first().copied().unwrap_or(0)
}

fn element(bits: u64, n: u32) -> F2mElement {
    F2mElement::from_biguint(&BigUint::from(bits), n)
}

/// `Σ_{t ∈ bits(i)} basis[t]` for every `i < 2^{len}`.
fn span_table(basis: &[u64]) -> Vec<u64> {
    let mut out = vec![0u64; 1 << basis.len()];
    for i in 1..out.len() {
        out[i] = out[i & (i - 1)] ^ basis[i.trailing_zeros() as usize];
    }
    out
}

// ── Dense restriction ──────────────────────────────────────────────

/// The values on every point of `F_2^{Σ dims}` of
/// `Σ_terms c · Π_k y_k^{a_k}`, where `y_k` ranges over the span table
/// `values[k]` of block `k` (block `k` owns the next `dims[k]` bits of the
/// point index, block 0 the lowest).  Contracts the last block first:
/// every prefix of exponents keeps one array over the blocks already
/// summed.
fn evaluate_blocks(
    terms: &[([u8; 4], u64)],
    powers: &[Vec<Vec<u64>>; 4],
    dims: [usize; 4],
    f: &Gf2n,
) -> Vec<u64> {
    let mut level: BTreeMap<[u8; 4], Vec<u64>> = BTreeMap::new();
    for &(a, c) in terms {
        level.entry(a).or_insert_with(|| vec![0])[0] ^= c;
    }
    for k in (0..4).rev() {
        let d = dims[k];
        let mut next: BTreeMap<[u8; 4], Vec<u64>> = BTreeMap::new();
        for (key, src) in level {
            let e = key[k] as usize;
            let mut prefix = key;
            prefix[k] = 0;
            let dst = next
                .entry(prefix)
                .or_insert_with(|| vec![0u64; src.len() << d]);
            for (t, pw) in powers[k].iter().enumerate() {
                let c = pw[e];
                if c == 0 {
                    continue;
                }
                if c == 1 {
                    for (r, &v) in src.iter().enumerate() {
                        dst[t | (r << d)] ^= v;
                    }
                } else {
                    let w = Gf2n::window(c);
                    for (r, &v) in src.iter().enumerate() {
                        if v != 0 {
                            dst[t | (r << d)] ^= f.mul_window(&w, v);
                        }
                    }
                }
            }
        }
        level = next;
    }
    level
        .remove(&[0; 4])
        .unwrap_or_else(|| vec![0u64; 1 << dims.iter().sum::<usize>()])
}

/// In-place binary Möbius transform: values on `F_2^k` to the
/// coefficients of their algebraic normal form (monomial `s` at index
/// `s`), on every bit of the words at once.
fn mobius(a: &mut [u64]) {
    let len = a.len();
    let mut h = 1;
    while h < len {
        for block in (0..len).step_by(2 * h) {
            let (lo, hi) = a[block..block + 2 * h].split_at_mut(h);
            for (x, y) in hi.iter_mut().zip(lo.iter()) {
                *x ^= *y;
            }
        }
        h <<= 1;
    }
}

// ── The template ───────────────────────────────────────────────────

/// Which system a template restricts.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum S5Variant {
    /// `S₅` in `x₁ … x₄`; unknowns are the `4ℓ` subspace coordinates,
    /// laid out as the chain's first `4ℓ` (summand `i` owns
    /// `[iℓ, (i+1)ℓ)`).
    X,
    /// `S₅` in `e₁ … e₄`; unknowns are the coordinates of `e_k` in a
    /// basis of `W_k`, block `k` after block `k − 1`.
    Symmetrised,
}

/// Everything a template depends on, compared in full before a memoised
/// template is reused.
#[derive(Clone, Debug, PartialEq, Eq)]
struct TemplateKey {
    variant: S5Variant,
    n: u32,
    reduced: Vec<Vec<u64>>,
    basis: Vec<u64>,
    b: u64,
}

/// `S₅` restricted once to a subspace: per monomial of the unknowns, the
/// nine field coefficients of `x_R⁰ … x_R⁸`.  See the module docs.
#[derive(Clone, Debug)]
pub struct S5Template {
    variant: S5Variant,
    field: Gf2n,
    n: u32,
    /// Unknowns per block (summand for [`S5Variant::X`], `e_k` for
    /// [`S5Variant::Symmetrised`]).
    dims: [usize; 4],
    /// The basis each block's unknowns are coordinates in: the subspace
    /// basis four times, or the `W_k` bases.
    block_bases: [Vec<u64>; 4],
    /// The subspace basis.
    basis: Vec<u64>,
    /// Every monomial with a nonzero coefficient, in canonical order.
    monomials: Vec<u64>,
    /// `coefficients[s·NE + e]`: the coefficient of `x_R^e` at monomial `s`.
    coefficients: Vec<u64>,
}

/// One target's system.
#[derive(Clone, Debug)]
pub struct S5System {
    /// The `n` coordinate equations of `S₅ = 0`.
    pub equations: Vec<F2BoolPoly>,
    /// Boolean unknowns.
    pub n_vars: usize,
}

impl S5Template {
    /// The `x`-template for `S₅` over `span(basis)`, curve coefficient `b`.
    /// `None` past [`MAX_DENSE_VARS`] unknowns or for a field `n ∉ 2..=64`.
    pub fn build_x(basis: &[F2mElement], b: &F2mElement, st: &FieldStructure) -> Option<Self> {
        let ell = basis.len();
        if ell == 0 || M * ell > MAX_DENSE_VARS {
            return None;
        }
        let basis: Vec<u64> = basis.iter().map(bits_of).collect();
        let terms = s5_x_terms();
        Self::build(
            S5Variant::X,
            &terms,
            [basis.clone(), basis.clone(), basis.clone(), basis.clone()],
            basis,
            bits_of(b),
            st,
        )
    }

    /// The symmetrised template: `S₅` in `e₁ … e₄` with `e_k` over a basis
    /// of `W_k`.  `None` past [`MAX_DENSE_VARS`] unknowns in all, or for a
    /// field `n ∉ 2..=64`.
    pub fn build_symmetrised(
        basis: &[F2mElement],
        b: &F2mElement,
        st: &FieldStructure,
    ) -> Option<Self> {
        let field = Gf2n::new(st)?;
        let ell = basis.len();
        if ell == 0 {
            return None;
        }
        let basis: Vec<u64> = basis.iter().map(bits_of).collect();
        let w = symmetric_bases(&basis, &field);
        if w.iter().map(Vec::len).sum::<usize>() > MAX_DENSE_VARS {
            return None;
        }
        Self::build(
            S5Variant::Symmetrised,
            S5_SYMMETRIC,
            w,
            basis,
            bits_of(b),
            st,
        )
    }

    fn build(
        variant: S5Variant,
        terms: &[([u8; 4], u8, u8)],
        block_bases: [Vec<u64>; 4],
        basis: Vec<u64>,
        b: u64,
        st: &FieldStructure,
    ) -> Option<Self> {
        let field = Gf2n::new(st)?;
        let b = b & field.mask;
        let dims = [0, 1, 2, 3].map(|k| block_bases[k].len());
        let total: usize = dims.iter().sum();
        if total > MAX_DENSE_VARS || total == 0 {
            return None;
        }
        let max_exp = terms.iter().flat_map(|t| t.0).max().unwrap_or(0) as usize;
        let powers: [Vec<Vec<u64>>; 4] = [0, 1, 2, 3].map(|k| {
            span_table(&block_bases[k])
                .into_iter()
                .map(|v| field.powers(v, max_exp + 1))
                .collect()
        });
        let b_powers = field.powers(b, 9);
        let mut sparse: Vec<(u64, usize, u64)> = Vec::new();
        for e in 0..NE {
            let level: Vec<([u8; 4], u64)> = terms
                .iter()
                .filter(|t| t.1 as usize == e)
                .map(|t| (t.0, b_powers[t.2 as usize]))
                .filter(|t| t.1 != 0)
                .collect();
            if level.is_empty() {
                continue;
            }
            let mut values = evaluate_blocks(&level, &powers, dims, &field);
            mobius(&mut values);
            sparse.extend(
                values
                    .iter()
                    .enumerate()
                    .filter(|(_, &c)| c != 0)
                    .map(|(s, &c)| (s as u64, e, c)),
            );
        }
        let mut monomials: Vec<u64> = sparse.iter().map(|t| t.0).collect();
        monomials.sort_unstable();
        monomials.dedup();
        sort_masks_descending(&mut monomials);
        let position: HashMap<u64, usize> =
            monomials.iter().enumerate().map(|(i, &s)| (s, i)).collect();
        let mut coefficients = vec![0u64; monomials.len() * NE];
        for (s, e, c) in sparse {
            coefficients[position[&s] * NE + e] = c;
        }
        Some(Self {
            variant,
            n: st.n,
            field,
            dims,
            block_bases,
            basis,
            monomials,
            coefficients,
        })
    }

    /// Which system this restricts.
    pub fn variant(&self) -> S5Variant {
        self.variant
    }

    /// Boolean unknowns of every instantiated system.
    pub fn n_vars(&self) -> usize {
        self.dims.iter().sum()
    }

    /// Unknowns per block.
    pub fn dims(&self) -> [usize; 4] {
        self.dims
    }

    /// Monomials carrying a coefficient (the union over the nine powers
    /// of `x_R`).
    pub fn support_len(&self) -> usize {
        self.monomials.len()
    }

    /// The system for target abscissa `x_r`: `Σ_e C_e · x_R^e`, read back
    /// as `n` coordinate equations, each in canonical order.
    pub fn instantiate(&self, x_r: &F2mElement) -> S5System {
        let f = &self.field;
        let n_vars = self.n_vars();
        let p = f.powers(bits_of(x_r) & f.mask, NE);
        let muls: Vec<Option<ConstMul>> = p
            .iter()
            .map(|&c| (c > 1).then(|| ConstMul::new(f, c)))
            .collect();
        let n = self.n as usize;
        let mut values = Vec::with_capacity(self.monomials.len());
        let mut counts = vec![0usize; n];
        for row in self.coefficients.chunks_exact(NE) {
            let mut v = 0u64;
            for ((&c, m), &pe) in row.iter().zip(&muls).zip(&p) {
                if c == 0 || pe == 0 {
                    continue;
                }
                v ^= match m {
                    Some(m) => m.apply(c),
                    None => c,
                };
            }
            let mut bits = v;
            while bits != 0 {
                counts[bits.trailing_zeros() as usize] += 1;
                bits &= bits - 1;
            }
            values.push(v);
        }
        let mut coords: Vec<Vec<F2BoolMono>> = counts.into_iter().map(Vec::with_capacity).collect();
        for (&s, &v) in self.monomials.iter().zip(&values) {
            let mut bits = v;
            while bits != 0 {
                coords[bits.trailing_zeros() as usize].push(F2BoolMono::from_mask(s));
                bits &= bits - 1;
            }
        }
        S5System {
            equations: coords
                .into_iter()
                .map(|terms| F2BoolPoly { terms, n_vars })
                .collect(),
            n_vars,
        }
    }

    /// The value of block `k` at a root: `Σ_{t ∈ bits} block_bases[k][t]`.
    fn block_value(&self, root: u64, k: usize) -> u64 {
        let offset: usize = self.dims[..k].iter().sum();
        let mut v = 0;
        for (t, &w) in self.block_bases[k].iter().enumerate() {
            if (root >> (offset + t)) & 1 == 1 {
                v ^= w;
            }
        }
        v
    }

    /// The summand abscissae a root stands for: the four `xᵢ` of an
    /// `x`-root in summand order, or, for a symmetrised root, the roots
    /// in `V` of `T⁴ + e₁T³ + e₂T² + e₃T + e₄` with multiplicity, in
    /// ascending bit order — `None` when that quartic does not split
    /// over `V` (a spurious root).
    pub fn summands(&self, root: u64) -> Option<[F2mElement; 4]> {
        let v = match self.variant {
            S5Variant::X => [0, 1, 2, 3].map(|k| self.block_value(root, k)),
            S5Variant::Symmetrised => {
                let e = [0, 1, 2, 3].map(|k| self.block_value(root, k));
                quartic_roots_in_span(&self.field, e, &self.basis)?
            }
        };
        Some(v.map(|x| element(x, self.n)))
    }
}

/// Bases of `W_k = span{b_{t₁}⋯b_{t_k}}`, `k = 1 … 4`, over the
/// multisets `t₁ ≤ … ≤ t_k` in lexicographic order, keeping each product
/// independent of those before it.
fn symmetric_bases(basis: &[u64], f: &Gf2n) -> [Vec<u64>; 4] {
    let mut out: [Vec<u64>; 4] = Default::default();
    // `layer`: (largest index, product) over the multisets of the current size.
    let mut layer: Vec<(usize, u64)> = basis.iter().copied().enumerate().collect();
    for slot in out.iter_mut() {
        let mut echelon: Vec<u64> = Vec::new();
        for &(_, p) in &layer {
            let mut r = p;
            for &row in &echelon {
                r = r.min(r ^ row);
            }
            if r != 0 {
                echelon.push(r);
                echelon.sort_unstable_by(|a, b| b.cmp(a));
                slot.push(p);
            }
        }
        let mut next = Vec::new();
        for &(last, p) in &layer {
            for (t, &bt) in basis.iter().enumerate().skip(last) {
                next.push((t, f.mul(p, bt)));
            }
        }
        layer = next;
    }
    out
}

/// The roots of `T⁴ + e₁T³ + e₂T² + e₃T + e₄` in `span(basis)`, with
/// multiplicity, ascending; `None` unless there are four.
fn quartic_roots_in_span(f: &Gf2n, e: [u64; 4], basis: &[u64]) -> Option<[u64; 4]> {
    // Coefficients, highest degree first.
    let mut poly: Vec<u64> = vec![1, e[0], e[1], e[2], e[3]];
    let eval = |poly: &[u64], x: u64| poly.iter().fold(0u64, |acc, &c| f.mul(acc, x) ^ c);
    let mut roots = Vec::with_capacity(4);
    for x in span_table(basis) {
        while poly.len() > 1 && eval(&poly, x) == 0 {
            // Synthetic division by (T + x).
            let mut q = Vec::with_capacity(poly.len() - 1);
            let mut acc = 0u64;
            for &c in &poly[..poly.len() - 1] {
                acc = f.mul(acc, x) ^ c;
                q.push(acc);
            }
            poly = q;
            roots.push(x);
        }
    }
    if roots.len() != 4 {
        return None;
    }
    roots.sort_unstable();
    Some([roots[0], roots[1], roots[2], roots[3]])
}

// ── Template memo ──────────────────────────────────────────────────

/// Templates kept per thread; a decomposition run asks one `(field,
/// basis, b)` for every target.
const LOCAL_TEMPLATES: usize = 8;

thread_local! {
    static TEMPLATES: RefCell<Vec<(TemplateKey, Option<Rc<S5Template>>)>> =
        const { RefCell::new(Vec::new()) };
}

/// The memoised template for these inputs (a failed build is memoised
/// too, so a fallback is decided once per base).
pub fn template_cached(
    variant: S5Variant,
    basis: &[F2mElement],
    b: &F2mElement,
    st: &FieldStructure,
) -> Option<Rc<S5Template>> {
    let key = TemplateKey {
        variant,
        n: st.n,
        reduced: st.reduced.clone(),
        basis: basis.iter().map(bits_of).collect(),
        b: bits_of(b),
    };
    if let Some(hit) = TEMPLATES.with(|t| {
        t.borrow()
            .iter()
            .find(|(k, _)| *k == key)
            .map(|(_, v)| v.clone())
    }) {
        return hit;
    }
    let built = match variant {
        S5Variant::X => S5Template::build_x(basis, b, st),
        S5Variant::Symmetrised => S5Template::build_symmetrised(basis, b, st),
    }
    .map(Rc::new);
    TEMPLATES.with(|t| {
        let mut t = t.borrow_mut();
        if t.len() == LOCAL_TEMPLATES {
            t.remove(0);
        }
        t.push((key, built.clone()));
    });
    built
}

// ── Decompositions ─────────────────────────────────────────────────

/// How an `m = 4` decomposition system is built.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum M4Descent {
    /// The generic chain of three `S₃` links with `2n` intermediate
    /// unknowns (the production default).
    Chained,
    /// `S₅` in `x`, [`S5Template::build_x`].
    S5Template,
    /// `S₅` in `e₁ … e₄`, [`S5Template::build_symmetrised`].
    S5Symmetrised,
}

impl M4Descent {
    /// `KIC_M4_DESCENT`: `s5` selects the `S₅` template; anything else
    /// (or unset) is [`M4Descent::Chained`].  Read once per process.
    ///
    /// `s5sym` is deliberately not accepted: the symmetrised template was
    /// not faster than the chain on any cell measured (0.91x in
    /// instructions on the one cell where it builds), so it stays an
    /// explicit-argument API ([`decompose_all_m4`],
    /// [`groebner_decompose_m4`]) and never an environment switch.
    pub fn from_env() -> Self {
        static CHOICE: std::sync::OnceLock<M4Descent> = std::sync::OnceLock::new();
        *CHOICE.get_or_init(|| match std::env::var("KIC_M4_DESCENT").as_deref() {
            Ok("s5") => M4Descent::S5Template,
            _ => M4Descent::Chained,
        })
    }

    /// The descent [`dispatch_groebner_m4`] uses: the test override when
    /// set on this thread, otherwise [`M4Descent::from_env`].
    fn dispatch_choice() -> Self {
        #[cfg(test)]
        if let Some(d) = DISPATCH_OVERRIDE.with(|c| c.get()) {
            return d;
        }
        Self::from_env()
    }

    fn variant(self) -> Option<S5Variant> {
        match self {
            M4Descent::Chained => None,
            M4Descent::S5Template => Some(S5Variant::X),
            M4Descent::S5Symmetrised => Some(S5Variant::Symmetrised),
        }
    }
}

/// Everything [`decompose_all_m4`] found for one target.
#[derive(Clone, Debug, Default)]
pub struct M4Outcome {
    /// Every decomposition, as sorted factor-base indices, sorted.
    pub decompositions: BTreeSet<Vec<usize>>,
    /// Distinct roots of the system solved, projected to the summand
    /// unknowns for the chain.
    pub roots: usize,
    /// Roots that gave no decomposition: `x`-tuples with no lift, and for
    /// the symmetrised system also quartics that do not split over `V`.
    pub spurious: usize,
    /// The solver's counters.
    pub stats: SolveStats,
    /// Boolean unknowns of the system solved.
    pub n_vars: usize,
    /// The descent that actually ran (the chain when a template could not
    /// be built).
    pub descent: Option<M4Descent>,
}

impl M4Outcome {
    /// Lift one root's abscissae into the set, counting it spurious when
    /// nothing lifts.
    fn lift(
        &mut self,
        kc: &KoblitzCurve,
        fb: &FrobeniusFactorBase,
        index_of: &HashMap<(BigUint, BigUint), usize>,
        xs: &[F2mElement],
        target: &BinaryPoint,
    ) {
        let mut found = BTreeSet::new();
        lift_all(kc, fb, index_of, xs, target, &mut found);
        if found.is_empty() {
            self.spurious += 1;
        }
        self.decompositions.extend(found);
    }
}

/// Every choice of factor-base points over the abscissae `xs` that sums
/// to `target`, each as sorted indices.
pub fn lift_all(
    kc: &KoblitzCurve,
    fb: &FrobeniusFactorBase,
    index_of: &HashMap<(BigUint, BigUint), usize>,
    xs: &[F2mElement],
    target: &BinaryPoint,
    out: &mut BTreeSet<Vec<usize>>,
) {
    let choices: Vec<Vec<usize>> = xs
        .iter()
        .map(|x| {
            points_with_x(&kc.curve, x)
                .iter()
                .filter_map(|p| index_of.get(&point_key(p)).copied())
                .collect()
        })
        .collect();
    if choices.iter().any(Vec::is_empty) {
        return;
    }
    fn walk(
        kc: &KoblitzCurve,
        fb: &FrobeniusFactorBase,
        choices: &[Vec<usize>],
        acc: &BinaryPoint,
        chosen: &mut Vec<usize>,
        target: &BinaryPoint,
        out: &mut BTreeSet<Vec<usize>>,
    ) {
        let depth = chosen.len();
        if depth == choices.len() {
            if acc == target {
                let mut d = chosen.clone();
                d.sort_unstable();
                out.insert(d);
            }
            return;
        }
        for &i in &choices[depth] {
            chosen.push(i);
            let next = kc.add(acc, &fb.points[i]);
            walk(kc, fb, choices, &next, chosen, target, out);
            chosen.pop();
        }
    }
    walk(
        kc,
        fb,
        &choices,
        &BinaryPoint::Infinity,
        &mut Vec::new(),
        target,
        out,
    );
}

/// The engine a template system is solved with: [`SolverEngine::InheritedF4`]
/// (the default) becomes [`SolverEngine::MatrixF4`] at the same degree,
/// every other engine is kept.
///
/// The two reduce to the same row space at every node, so the verdicts
/// and roots are the same.  The cost is not: a template equation has
/// Boolean degree up to 12 and over a thousand terms, and specialising
/// those dense rows down the tree measured about ten times the work of
/// rebuilding the node's Macaulay matrix (`n = 13`, `ℓ = 3`: 212 ms
/// against 25 ms for one refuted target, both near 250 reductions),
/// where on the chain's cubic links inheriting is what wins.
pub fn template_engine(engine: SolverEngine) -> SolverEngine {
    match engine {
        SolverEngine::InheritedF4 { max_degree } => SolverEngine::MatrixF4 { max_degree },
        other => other,
    }
}

fn all_roots_options(engine: SolverEngine, node_budget: usize) -> SolveOptions {
    SolveOptions {
        engine,
        max_solutions: usize::MAX,
        node_budget,
        split_rule: split_rule_default(),
    }
}

/// The summand abscissae of `root` (a chained root's first `4ℓ` bits).
fn chain_summands(basis: &[F2mElement], root: u64, n: u32) -> Vec<F2mElement> {
    let ell = basis.len();
    (0..M)
        .map(|i| {
            let mut v = 0u64;
            for (t, b) in basis.iter().enumerate() {
                if (root >> (i * ell + t)) & 1 == 1 {
                    v ^= bits_of(b);
                }
            }
            element(v, n)
        })
        .collect()
}

/// **Every** `m = 4` decomposition of `target` over `fb`, by `descent`.
///
/// The system is solved to exhaustion (`max_solutions` unbounded); each
/// distinct root is lifted by [`lift_all`].  A specialised descent whose
/// template cannot be built runs the chain instead, and
/// [`M4Outcome::descent`] says so.  `None` for the point at infinity or
/// when not even the chain can be built.  The set is the same for every
/// descent; `stats.exhausted` marks a solve the node budget cut short,
/// whose set may be incomplete.
#[allow(clippy::too_many_arguments)]
pub fn decompose_all_m4(
    kc: &KoblitzCurve,
    fb: &FrobeniusFactorBase,
    index_of: &HashMap<(BigUint, BigUint), usize>,
    st: &FieldStructure,
    target: &BinaryPoint,
    descent: M4Descent,
    engine: SolverEngine,
    node_budget: usize,
) -> Option<M4Outcome> {
    let BinaryPoint::Affine { x: x_r, .. } = target else {
        return None;
    };
    let opts = all_roots_options(engine, node_budget);
    let template = descent
        .variant()
        .and_then(|v| template_cached(v, &fb.subspace_basis, &kc.curve.b, st));
    let mut out = M4Outcome::default();
    match template {
        Some(t) => {
            let sys = t.instantiate(x_r);
            let opts = all_roots_options(template_engine(engine), node_budget);
            let (roots, stats) =
                solve_boolean_system_filtered(&sys.equations, sys.n_vars, &opts, |_| false);
            let roots: BTreeSet<u64> = roots.into_iter().collect();
            for &root in &roots {
                match t.summands(root) {
                    Some(xs) => out.lift(kc, fb, index_of, &xs, target),
                    None => out.spurious += 1,
                }
            }
            out.roots = roots.len();
            out.stats = stats;
            out.n_vars = sys.n_vars;
            out.descent = Some(descent);
        }
        None => {
            let sys =
                build_decomposition_system_reusing(&fb.subspace_basis, x_r, &kc.curve.b, M, st)?;
            let order = chain_order_interleaved(opts.resolve().split_rule)
                .then(|| sys.interleaved_order(kc.n));
            let equations: Vec<F2BoolPoly> = match &order {
                Some(perm) => sys
                    .equations
                    .iter()
                    .map(|e| permute_poly(e, perm))
                    .collect(),
                None => sys.equations.clone(),
            };
            let back = order.as_deref().map(invert_permutation);
            let (roots, stats) =
                solve_boolean_system_filtered(&equations, sys.n_vars, &opts, |_| false);
            let low = (1u64 << (M * sys.ell)) - 1;
            let projected: BTreeSet<u64> = roots
                .into_iter()
                .map(|r| back.as_deref().map_or(r, |inv| permute_mask(r, inv)) & low)
                .collect();
            for &root in &projected {
                let xs = chain_summands(&fb.subspace_basis, root, kc.n);
                out.lift(kc, fb, index_of, &xs, target);
            }
            out.roots = projected.len();
            out.stats = stats;
            out.n_vars = sys.n_vars;
            out.descent = Some(M4Descent::Chained);
        }
    }
    Some(out)
}

thread_local! {
    /// Set while [`groebner_decompose_m4`] runs the chain through
    /// [`groebner_decompose`], so its `m = 4` dispatch does not redirect
    /// an explicit request for the chain.
    static CHAIN_REQUESTED: std::cell::Cell<bool> = const { std::cell::Cell::new(false) };
}

#[cfg(test)]
thread_local! {
    /// Test-only per-thread stand-in for `KIC_M4_DESCENT`, which is read
    /// once per process and so cannot be varied inside one test binary.
    static DISPATCH_OVERRIDE: std::cell::Cell<Option<M4Descent>> =
        const { std::cell::Cell::new(None) };
}

/// The first-found `m = 4` oracle by `descent`: solve, lift each root as
/// it is found (`lift_candidate`, as [`groebner_decompose`] does), stop
/// at the first that closes.  Falls back to the chain
/// ([`groebner_decompose`]) when the template cannot be built.  Returns
/// the decomposition (in `lift_candidate`'s summand order, not sorted),
/// the solver's counters and the descent that ran.
#[allow(clippy::too_many_arguments)]
pub fn groebner_decompose_m4(
    kc: &KoblitzCurve,
    fb: &FrobeniusFactorBase,
    index_of: &HashMap<(BigUint, BigUint), usize>,
    st: &FieldStructure,
    target: &BinaryPoint,
    descent: M4Descent,
    engine: SolverEngine,
    node_budget: usize,
) -> (Option<Vec<usize>>, SolveStats, M4Descent) {
    if let Some((d, s)) =
        specialised_first(kc, fb, index_of, st, target, descent, engine, node_budget)
    {
        return (d, s, descent);
    }
    let _chain = ChainGuard::request();
    let (d, s) = groebner_decompose(kc, fb, index_of, st, target, M, engine, node_budget);
    (d, s, M4Descent::Chained)
}

/// Scope guard for [`CHAIN_REQUESTED`]: restores the previous value on
/// drop, including when a panic unwinds through the chain call (a caught
/// panic must not leave the dispatch disabled on this thread).
struct ChainGuard {
    was: bool,
}

impl ChainGuard {
    fn request() -> Self {
        Self {
            was: CHAIN_REQUESTED.with(|c| c.replace(true)),
        }
    }
}

impl Drop for ChainGuard {
    fn drop(&mut self) {
        CHAIN_REQUESTED.with(|c| c.set(self.was));
    }
}

#[allow(clippy::too_many_arguments)]
fn specialised_first(
    kc: &KoblitzCurve,
    fb: &FrobeniusFactorBase,
    index_of: &HashMap<(BigUint, BigUint), usize>,
    st: &FieldStructure,
    target: &BinaryPoint,
    descent: M4Descent,
    engine: SolverEngine,
    node_budget: usize,
) -> Option<(Option<Vec<usize>>, SolveStats)> {
    let template = template_cached(descent.variant()?, &fb.subspace_basis, &kc.curve.b, st)?;
    let BinaryPoint::Affine { x: x_r, .. } = target else {
        return Some((None, SolveStats::default()));
    };
    let sys = template.instantiate(x_r);
    let opts = SolveOptions {
        engine: template_engine(engine),
        max_solutions: usize::MAX,
        node_budget,
        split_rule: split_rule_default(),
    };
    let mut found = None;
    let (_, stats) = solve_boolean_system_filtered(&sys.equations, sys.n_vars, &opts, |root| {
        match template
            .summands(root)
            .and_then(|xs| lift_candidate(kc, fb, index_of, &xs, target))
        {
            Some(d) => {
                found = Some(d);
                true
            }
            None => false,
        }
    });
    Some((found, stats))
}

/// The `m = 4` hook of [`groebner_decompose`]: `Some` when
/// `KIC_M4_DESCENT=s5` selects the template and it builds, `None` to run
/// the chain.
#[allow(clippy::too_many_arguments)]
pub(crate) fn dispatch_groebner_m4(
    kc: &KoblitzCurve,
    fb: &FrobeniusFactorBase,
    index_of: &HashMap<(BigUint, BigUint), usize>,
    st: &FieldStructure,
    target: &BinaryPoint,
    engine: SolverEngine,
    node_budget: usize,
) -> Option<(Option<Vec<usize>>, SolveStats)> {
    if CHAIN_REQUESTED.with(|c| c.get()) {
        return None;
    }
    let descent = M4Descent::dispatch_choice();
    if descent == M4Descent::Chained {
        return None;
    }
    specialised_first(kc, fb, index_of, st, target, descent, engine, node_budget)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::koblitz_groebner::{SolverEngine, SymElement};
    use crate::cryptanalysis::koblitz_index_calculus::{
        build_frobenius_factor_base_from_divisor, invariant_factors,
    };
    use crate::cryptanalysis::koblitz_symmetrised::{
        plain_subspace_factor_base, random_subspace_containing_one, sym_polynomial,
    };
    use crate::cryptanalysis::semaev_leading_form::{semaev, F2Poly, Mono, A6};
    use rand::rngs::StdRng;
    use rand::{Rng, SeedableRng};

    fn mono(e: [u8; 4], e5: u8, j: u8) -> Mono {
        let mut m: Mono = [0; 11];
        m[..4].copy_from_slice(&e);
        m[4] = e5;
        m[A6] = j;
        m
    }

    #[test]
    fn hardcoded_s5_is_semaev_4() {
        let expanded: std::collections::HashSet<Mono> = s5_x_terms()
            .into_iter()
            .map(|(e, e5, j)| mono(e, e5, j))
            .collect();
        assert_eq!(expanded.len(), 729);
        let reference: std::collections::HashSet<Mono> = semaev(4).terms.into_iter().collect();
        assert_eq!(expanded, reference);
    }

    #[test]
    fn hardcoded_symmetric_s5_expands_to_semaev_4() {
        let elementary = |k: usize| {
            let mut p = F2Poly::zero();
            for s in 0u32..16 {
                if s.count_ones() as usize == k {
                    let e = [0, 1, 2, 3].map(|i| (s >> i & 1) as u8);
                    p.terms.insert(mono(e, 0, 0));
                }
            }
            p
        };
        let es: Vec<F2Poly> = (1..=4).map(elementary).collect();
        let mut acc = F2Poly::zero();
        for &(b, e5, j) in S5_SYMMETRIC {
            let mut t = F2Poly::zero();
            t.terms.insert(mono([0; 4], e5, j));
            for k in 0..4 {
                for _ in 0..b[k] {
                    t = t.mul(&es[k]);
                }
            }
            acc = acc.add(&t);
        }
        assert_eq!(S5_SYMMETRIC.len(), 100);
        assert_eq!(acc, semaev(4));
    }

    #[test]
    fn permutations_are_the_symmetric_group() {
        let set: BTreeSet<[usize; 4]> = PERMUTATIONS_4.iter().copied().collect();
        assert_eq!(set.len(), 24);
        assert!(set.iter().all(|p| {
            let mut q = *p;
            q.sort_unstable();
            q == [0, 1, 2, 3]
        }));
    }

    fn field(n: u32) -> (KoblitzCurve, FieldStructure) {
        let kc = KoblitzCurve::new(0, n)
            .or_else(|| KoblitzCurve::new(1, n))
            .expect("a Koblitz curve over F_2^n");
        let st = FieldStructure::new(n, &kc.curve.irreducible);
        (kc, st)
    }

    /// The table field arithmetic against the structure constants it is
    /// built from.
    #[test]
    fn constant_arithmetic_matches_the_structure_constants() {
        let mut rng = StdRng::seed_from_u64(5);
        for n in [3u32, 5, 7, 9, 13, 17, 23] {
            let (_, st) = field(n);
            let f = Gf2n::new(&st).unwrap();
            for _ in 0..300 {
                let a = rng.gen::<u64>() & f.mask;
                let b = rng.gen::<u64>() & f.mask;
                let mut want = 0u64;
                for i in 0..n as usize {
                    for j in 0..n as usize {
                        if a >> i & 1 == 1 && b >> j & 1 == 1 {
                            want ^= st.reduced[i][j];
                        }
                    }
                }
                assert_eq!(f.mul(a, b), want, "n = {n}");
                assert_eq!(ConstMul::new(&f, a).apply(b), want, "n = {n}");
            }
        }
    }

    fn random_basis(rng: &mut StdRng, n: u32, ell: usize) -> Vec<F2mElement> {
        // Independent vectors, plus the edge cases 1 and z^{n−1}.
        loop {
            let mut v: Vec<u64> = (0..ell)
                .map(|_| rng.gen::<u64>() & ((1 << n) - 1))
                .collect();
            if rng.gen_bool(0.3) {
                v[0] = 1;
            }
            if ell > 1 && rng.gen_bool(0.3) {
                v[ell - 1] = 1 << (n - 1);
            }
            let mut echelon: Vec<u64> = Vec::new();
            let mut ok = true;
            for &x in &v {
                let mut r = x;
                for &row in &echelon {
                    r = r.min(r ^ row);
                }
                if r == 0 {
                    ok = false;
                    break;
                }
                echelon.push(r);
                echelon.sort_unstable_by(|a, b| b.cmp(a));
            }
            if ok {
                return v.into_iter().map(|x| element(x, n)).collect();
            }
        }
    }

    /// The Möbius route against the symbolic Weil restriction of the
    /// same polynomial, term for term, for both variants: random bases,
    /// curve coefficients and targets, plus the targets `0`, `1` and the
    /// all-ones word.
    #[test]
    fn templates_equal_the_symbolic_restriction() {
        let mut rng = StdRng::seed_from_u64(0x55);
        for (n, ell, cases) in [
            (3u32, 1usize, 4),
            (5, 1, 4),
            (5, 2, 4),
            (7, 2, 3),
            (9, 2, 2),
            (7, 3, 1),
        ] {
            let (_, st) = field(n);
            let f = Gf2n::new(&st).unwrap();
            for case in 0..cases {
                let basis = random_basis(&mut rng, n, ell);
                let b = if case == 0 {
                    1
                } else {
                    rng.gen::<u64>() & f.mask
                };
                let b_el = element(b, n);
                let mut targets = vec![0u64, 1, f.mask];
                targets.extend((0..3).map(|_| rng.gen::<u64>() & f.mask));
                // x-template.
                let t = S5Template::build_x(&basis, &b_el, &st).unwrap();
                let nv = M * ell;
                for &xr in &targets {
                    let mut vars: Vec<SymElement> = (0..M)
                        .map(|i| SymElement::from_subspace_vars(&basis, i * ell, n, nv))
                        .collect();
                    vars.push(SymElement::constant(&element(xr, n), n, nv));
                    vars.push(SymElement::constant(&b_el, n, nv));
                    let terms: Vec<Vec<u32>> = s5_x_terms()
                        .iter()
                        .map(|(e, e5, j)| {
                            let mut v: Vec<u32> = e.iter().map(|&x| u32::from(x)).collect();
                            v.push(u32::from(*e5));
                            v.push(u32::from(*j));
                            v
                        })
                        .collect();
                    let want = sym_polynomial(&vars, &terms, &st);
                    let got = t.instantiate(&element(xr, n));
                    assert_eq!(got.n_vars, nv);
                    assert_eq!(got.equations, want, "x: n={n} ell={ell} b={b} xr={xr}");
                }
                // Symmetrised template.
                let Some(ts) = S5Template::build_symmetrised(&basis, &b_el, &st) else {
                    continue;
                };
                let w = symmetric_bases(&basis.iter().map(bits_of).collect::<Vec<_>>(), &f);
                let total = ts.n_vars();
                let mut offset = 0;
                let mut vars: Vec<SymElement> = Vec::new();
                for wk in &w {
                    let els: Vec<F2mElement> = wk.iter().map(|&x| element(x, n)).collect();
                    vars.push(SymElement::from_subspace_vars(&els, offset, n, total));
                    offset += wk.len();
                }
                for &xr in &targets {
                    let mut v = vars.clone();
                    v.push(SymElement::constant(&element(xr, n), n, total));
                    v.push(SymElement::constant(&b_el, n, total));
                    let terms: Vec<Vec<u32>> = S5_SYMMETRIC
                        .iter()
                        .map(|(e, e5, j)| {
                            let mut v: Vec<u32> = e.iter().map(|&x| u32::from(x)).collect();
                            v.push(u32::from(*e5));
                            v.push(u32::from(*j));
                            v
                        })
                        .collect();
                    let want = sym_polynomial(&v, &terms, &st);
                    assert_eq!(
                        ts.instantiate(&element(xr, n)).equations,
                        want,
                        "sym: n={n} ell={ell} xr={xr}"
                    );
                }
            }
        }
    }

    /// `W_k` is spanned by the values of `e_k` on `V⁴`: every value lies in
    /// the span, and the bases are independent.
    #[test]
    fn symmetric_bases_span_the_elementary_values() {
        let mut rng = StdRng::seed_from_u64(9);
        for (n, ell) in [(5u32, 1usize), (7, 2), (9, 2), (11, 3)] {
            let (_, st) = field(n);
            let f = Gf2n::new(&st).unwrap();
            let basis: Vec<u64> = random_basis(&mut rng, n, ell).iter().map(bits_of).collect();
            let w = symmetric_bases(&basis, &f);
            let v = span_table(&basis);
            for (k, wk) in w.iter().enumerate() {
                let span: BTreeSet<u64> = span_table(wk).into_iter().collect();
                assert_eq!(span.len(), 1 << wk.len(), "independent");
                for _ in 0..200 {
                    let x = [0; 4].map(|_: u8| v[rng.gen_range(0..v.len())]);
                    let mut e = [0u64; 5];
                    e[0] = 1;
                    for &xi in &x {
                        for j in (1..5).rev() {
                            e[j] ^= f.mul(e[j - 1], xi);
                        }
                    }
                    assert!(span.contains(&e[k + 1]), "e_{} outside W", k + 1);
                }
            }
        }
    }

    #[test]
    fn quartic_roots_recover_split_quartics_and_refuse_the_rest() {
        let mut rng = StdRng::seed_from_u64(77);
        let (_, st) = field(9);
        let f = Gf2n::new(&st).unwrap();
        let basis: Vec<u64> = random_basis(&mut rng, 9, 3).iter().map(bits_of).collect();
        let v = span_table(&basis);
        for trial in 0..400 {
            let mut x = [0; 4].map(|_: u8| v[rng.gen_range(0..v.len())]);
            if trial % 7 == 0 {
                x[1] = x[0];
                x[3] = x[2];
            }
            let mut e = [0u64; 5];
            e[0] = 1;
            for &xi in &x {
                for j in (1..5).rev() {
                    e[j] ^= f.mul(e[j - 1], xi);
                }
            }
            x.sort_unstable();
            assert_eq!(
                quartic_roots_in_span(&f, [e[1], e[2], e[3], e[4]], &basis),
                Some(x)
            );
            // A random quartic: brute-force the split over V.
            let r = [0; 4].map(|_: u8| rng.gen::<u64>() & f.mask);
            let got = quartic_roots_in_span(&f, r, &basis);
            if let Some(y) = got {
                let mut e = [0u64; 5];
                e[0] = 1;
                for &yi in &y {
                    for j in (1..5).rev() {
                        e[j] ^= f.mul(e[j - 1], yi);
                    }
                }
                assert_eq!([e[1], e[2], e[3], e[4]], r);
            }
        }
    }

    /// A Koblitz curve and a factor base of dimension `ell` (first in
    /// divisor order that can decompose with four summands).
    fn base(n: u32, ell: usize) -> Option<(KoblitzCurve, FrobeniusFactorBase)> {
        for a in 0u8..=1 {
            let Some(kc) = KoblitzCurve::new(a, n) else {
                continue;
            };
            let degs: Vec<usize> = invariant_factors(&kc)
                .iter()
                .map(|f| f.degree().unwrap_or(0))
                .collect();
            let k = degs.len().min(12);
            for mask in 1u32..1 << k {
                let idx: Vec<usize> = (0..k).filter(|&i| mask >> i & 1 == 1).collect();
                if idx.iter().map(|&i| degs[i]).sum::<usize>() != ell {
                    continue;
                }
                if let Some(fb) = build_frobenius_factor_base_from_divisor(&kc, &idx) {
                    if !fb.points.is_empty() {
                        return Some((kc, fb));
                    }
                }
            }
        }
        None
    }

    /// The differential cases: Frobenius-invariant bases (subfield ones
    /// among them: `ℓ = 3` at `n = 9, 15` is `F_8`) and random
    /// non-invariant bases containing `1`.
    fn cases(rng: &mut StdRng) -> Vec<(KoblitzCurve, FrobeniusFactorBase)> {
        let mut out = Vec::new();
        for (n, ell) in [(5u32, 1usize), (7, 1), (9, 2), (9, 3), (15, 2), (15, 3)] {
            out.push(base(n, ell).expect("a Frobenius base"));
        }
        for (n, ell) in [(7u32, 2usize), (11, 2), (13, 2), (13, 3)] {
            let (kc, _) = field(n);
            let basis = random_subspace_containing_one(&kc, ell, rng);
            out.push((kc.clone(), plain_subspace_factor_base(&kc, &basis).unwrap()));
        }
        out
    }

    /// Brute force: every `x`-tuple in `V⁴`, lifted.
    fn brute_force(
        kc: &KoblitzCurve,
        fb: &FrobeniusFactorBase,
        index_of: &HashMap<(BigUint, BigUint), usize>,
        target: &BinaryPoint,
    ) -> BTreeSet<Vec<usize>> {
        let v = span_table(&fb.subspace_basis.iter().map(bits_of).collect::<Vec<_>>());
        let mut out = BTreeSet::new();
        for a in &v {
            for b in &v {
                for c in &v {
                    for d in &v {
                        let xs = [a, b, c, d].map(|&x| element(x, kc.n));
                        lift_all(kc, fb, index_of, &xs, target, &mut out);
                    }
                }
            }
        }
        out
    }

    fn targets(kc: &KoblitzCurve, fb: &FrobeniusFactorBase, rng: &mut StdRng) -> Vec<BinaryPoint> {
        let pts = &fb.points;
        let pick = |rng: &mut StdRng| pts[rng.gen_range(0..pts.len())].clone();
        let mut out = Vec::new();
        for _ in 0..8 {
            let s = (0..4).fold(BinaryPoint::Infinity, |acc, _| kc.add(&acc, &pick(rng)));
            out.push(s);
        }
        // Degenerate plantings: P + P + Q + Q, P − P + Q + R, 4P.
        let (p, q, r) = (pick(rng), pick(rng), pick(rng));
        out.push(kc.add(&kc.add(&p, &p), &kc.add(&q, &q)));
        let neg_p = crate::binary_ecc::curve::point_neg(&p);
        out.push(kc.add(&kc.add(&p, &neg_p), &kc.add(&q, &r)));
        out.push(kc.add(&kc.add(&p, &p), &kc.add(&p, &p)));
        for _ in 0..3 {
            out.push(kc.mul(kc.generator(), &BigUint::from(rng.gen_range(1u64..1 << 40))));
        }
        // The 2-torsion point (0, √b).
        out.extend(points_with_x(&kc.curve, &F2mElement::zero(kc.n)));
        out.retain(|t| matches!(t, BinaryPoint::Affine { .. }));
        out
    }

    /// The differential test: brute force, the chain, the `S₅` template
    /// and (where it builds) the symmetrised template give the same set
    /// of decompositions; the first-found oracles agree on whether one
    /// exists and return members of it.
    #[test]
    fn every_descent_finds_the_same_decompositions() {
        let mut rng = StdRng::seed_from_u64(0x5e5);
        let engine = SolverEngine::default();
        let mut compared = 0;
        let mut nonempty = 0;
        let mut sym_compared = 0;
        for (kc, fb) in cases(&mut rng) {
            let (n, ell) = (kc.n, fb.subspace_basis.len());
            let st = FieldStructure::new(n, &kc.curve.irreducible);
            let index_of = fb.index_map();
            for target in targets(&kc, &fb, &mut rng) {
                let truth = brute_force(&kc, &fb, &index_of, &target);
                let run = |d| {
                    decompose_all_m4(&kc, &fb, &index_of, &st, &target, d, engine, 1 << 30).unwrap()
                };
                let chain = run(M4Descent::Chained);
                let s5 = run(M4Descent::S5Template);
                assert!(!chain.stats.exhausted && !s5.stats.exhausted);
                assert_eq!(s5.descent, Some(M4Descent::S5Template));
                assert_eq!(chain.decompositions, truth, "chain n={n} ell={ell}");
                assert_eq!(s5.decompositions, truth, "s5 n={n} ell={ell}");
                assert!(s5.roots >= chain.roots, "S5 roots contain the chain's");
                assert_eq!(s5.n_vars, 4 * ell);
                let sym = run(M4Descent::S5Symmetrised);
                if sym.descent == Some(M4Descent::S5Symmetrised) {
                    assert_eq!(sym.decompositions, truth, "sym n={n} ell={ell}");
                    sym_compared += 1;
                }
                for d in [
                    M4Descent::S5Template,
                    M4Descent::S5Symmetrised,
                    M4Descent::Chained,
                ] {
                    let (found, _, _) = groebner_decompose_m4(
                        &kc,
                        &fb,
                        &index_of,
                        &st,
                        &target,
                        d,
                        engine,
                        1 << 30,
                    );
                    assert_eq!(found.is_some(), !truth.is_empty(), "{d:?} n={n}");
                    if let Some(mut idx) = found {
                        let sum = idx
                            .iter()
                            .fold(BinaryPoint::Infinity, |acc, &i| kc.add(&acc, &fb.points[i]));
                        assert_eq!(sum, target);
                        idx.sort_unstable();
                        assert!(truth.contains(&idx));
                    }
                }
                let (generic, _) =
                    groebner_decompose(&kc, &fb, &index_of, &st, &target, M, engine, 1 << 30);
                assert_eq!(generic.is_some(), !truth.is_empty());
                compared += 1;
                nonempty += usize::from(!truth.is_empty());
            }
        }
        eprintln!("compared {compared}, nonempty {nonempty}, symmetrised {sym_compared}");
        assert!(compared >= 95, "compared {compared}");
        assert!(nonempty >= 60, "nonempty {nonempty}");
        assert!(sym_compared >= 80, "sym {sym_compared}");
    }

    /// The other Gröbner engines consume the template to the same set.
    #[test]
    fn f5_and_buchberger_engines_agree() {
        let mut rng = StdRng::seed_from_u64(0xf5);
        let (kc, fb) = base(9, 2).unwrap();
        let st = FieldStructure::new(9, &kc.curve.irreducible);
        let index_of = fb.index_map();
        for target in targets(&kc, &fb, &mut rng) {
            let truth = brute_force(&kc, &fb, &index_of, &target);
            for engine in [
                SolverEngine::MatrixF4 { max_degree: 3 },
                SolverEngine::MatrixF5 { max_degree: 3 },
                SolverEngine::Buchberger,
            ] {
                for d in [M4Descent::S5Template, M4Descent::S5Symmetrised] {
                    let o = decompose_all_m4(&kc, &fb, &index_of, &st, &target, d, engine, 1 << 30)
                        .unwrap();
                    assert_eq!(o.decompositions, truth, "{engine:?} {d:?}");
                }
            }
        }
    }

    /// Past the dense cap the template is refused and the chain runs; the
    /// explicit chain is not redirected by the dispatch hook.
    #[test]
    fn oversize_templates_fall_back_to_the_chain() {
        // W dimensions 3 + 6 + 7 + 7 = 23 > MAX_DENSE_VARS.
        let (kc, fb) = base(7, 3).unwrap();
        let st = FieldStructure::new(7, &kc.curve.irreducible);
        assert!(S5Template::build_symmetrised(&fb.subspace_basis, &kc.curve.b, &st).is_none());
        let index_of = fb.index_map();
        let mut rng = StdRng::seed_from_u64(3);
        let target = targets(&kc, &fb, &mut rng).remove(0);
        let o = decompose_all_m4(
            &kc,
            &fb,
            &index_of,
            &st,
            &target,
            M4Descent::S5Symmetrised,
            SolverEngine::default(),
            1 << 30,
        )
        .unwrap();
        assert_eq!(o.descent, Some(M4Descent::Chained));
        assert_eq!(o.decompositions, brute_force(&kc, &fb, &index_of, &target));
        let (_, _, used) = groebner_decompose_m4(
            &kc,
            &fb,
            &index_of,
            &st,
            &target,
            M4Descent::S5Symmetrised,
            SolverEngine::default(),
            1 << 30,
        );
        assert_eq!(used, M4Descent::Chained);
        let big = random_basis(&mut rng, 23, 6);
        let (_, st23) = field(23);
        assert!(S5Template::build_x(&big, &F2mElement::one(23), &st23).is_none());
        assert!(S5Template::build_x(&big[..5], &F2mElement::one(23), &st23).is_some());
    }
}

/// Review differential tests on inputs the first round did not use:
/// subfield curves with `b ≠ 1`, bases without `1`, the boundary
/// `4ℓ = MAX_DENSE_VARS` on the full field, the smallest field, targets
/// built from the 2-torsion point and targets inside the factor base.
#[cfg(test)]
mod review_tests {
    use super::*;
    use crate::cryptanalysis::koblitz_groebner::SolverEngine;
    use crate::cryptanalysis::koblitz_symmetrised::{
        plain_subspace_factor_base, random_subspace_containing_one,
    };
    use rand::rngs::StdRng;
    use rand::{Rng, SeedableRng};

    fn brute(
        kc: &KoblitzCurve,
        fb: &FrobeniusFactorBase,
        target: &BinaryPoint,
    ) -> BTreeSet<Vec<usize>> {
        // Over the factor-base points themselves, not over V⁴.
        let p = &fb.points;
        let mut out = BTreeSet::new();
        for a in 0..p.len() {
            let pa = kc.add(&BinaryPoint::Infinity, &p[a]);
            for b in 0..p.len() {
                let pb = kc.add(&pa, &p[b]);
                for c in 0..p.len() {
                    let pc = kc.add(&pb, &p[c]);
                    for d in 0..p.len() {
                        if kc.add(&pc, &p[d]) == *target {
                            let mut v = vec![a, b, c, d];
                            v.sort_unstable();
                            out.insert(v);
                        }
                    }
                }
            }
        }
        out
    }

    fn random_basis_any(n: u32, ell: usize, rng: &mut StdRng) -> Vec<F2mElement> {
        loop {
            let v: Vec<u64> = (0..ell)
                .map(|_| rng.gen::<u64>() & ((1 << n) - 1))
                .collect();
            if span_table(&v).iter().skip(1).all(|&x| x != 0)
                && span_table(&v).iter().collect::<BTreeSet<_>>().len() == 1 << ell
            {
                return v.into_iter().map(|x| element(x, n)).collect();
            }
        }
    }

    fn review_targets(
        kc: &KoblitzCurve,
        fb: &FrobeniusFactorBase,
        rng: &mut StdRng,
    ) -> Vec<BinaryPoint> {
        let pts = &fb.points;
        let pick = |rng: &mut StdRng| pts[rng.gen_range(0..pts.len())].clone();
        let mut out = Vec::new();
        for _ in 0..4 {
            out.push((0..4).fold(BinaryPoint::Infinity, |acc, _| kc.add(&acc, &pick(rng))));
        }
        // Sums of 2 and 3 factor-base points (only padded decompositions exist).
        out.push(kc.add(&pick(rng), &pick(rng)));
        out.push(kc.add(&kc.add(&pick(rng), &pick(rng)), &pick(rng)));
        // A factor-base point itself.
        out.push(pick(rng));
        // 2-torsion T = (0, √b): P + Q + R + T, and T itself.
        let t = points_with_x(&kc.curve, &F2mElement::zero(kc.n));
        if let Some(t) = t.first() {
            out.push(kc.add(&kc.add(&pick(rng), &pick(rng)), &kc.add(&pick(rng), t)));
            out.push(t.clone());
        }
        // Random points of the curve (mostly no decomposition).
        for _ in 0..3 {
            out.push(kc.mul(kc.generator(), &BigUint::from(rng.gen_range(1u64..1 << 40))));
        }
        out.retain(|t| matches!(t, BinaryPoint::Affine { .. }));
        out
    }

    fn check(kc: &KoblitzCurve, fb: &FrobeniusFactorBase, rng: &mut StdRng, label: &str) -> usize {
        let st = FieldStructure::new(kc.n, &kc.curve.irreducible);
        let index_of = fb.index_map();
        let mut nonempty = 0;
        for target in review_targets(kc, fb, rng) {
            let truth = brute(kc, fb, &target);
            nonempty += usize::from(!truth.is_empty());
            for engine in [SolverEngine::default()] {
                for d in [
                    M4Descent::Chained,
                    M4Descent::S5Template,
                    M4Descent::S5Symmetrised,
                ] {
                    let o = decompose_all_m4(kc, fb, &index_of, &st, &target, d, engine, 1 << 30)
                        .unwrap();
                    assert!(!o.stats.exhausted);
                    assert_eq!(o.decompositions, truth, "{label} {d:?} {engine:?} all");
                    let (found, _, _) =
                        groebner_decompose_m4(kc, fb, &index_of, &st, &target, d, engine, 1 << 30);
                    assert_eq!(found.is_some(), !truth.is_empty(), "{label} {d:?} first");
                    if let Some(mut idx) = found {
                        idx.sort_unstable();
                        assert!(truth.contains(&idx), "{label} {d:?} member");
                    }
                }
            }
        }
        nonempty
    }

    #[test]
    fn review_subfield_curves_with_b_not_one() {
        let mut rng = StdRng::seed_from_u64(0xbee5);
        let mut nonempty = 0;
        for (k, n, ell) in [
            (3u32, 9u32, 2usize),
            (3, 9, 3),
            (3, 15, 2),
            (3, 15, 3),
            (5, 15, 3),
        ] {
            for b_index in [2u64, 3, (1 << k) - 1] {
                for a_index in [0u64, 1] {
                    let Some(kc) = KoblitzCurve::subfield(k, n, a_index, b_index) else {
                        continue;
                    };
                    assert_ne!(bits_of(&kc.curve.b), 1);
                    let basis = if rng.gen_bool(0.5) {
                        random_subspace_containing_one(&kc, ell, &mut rng)
                    } else {
                        random_basis_any(n, ell, &mut rng)
                    };
                    let Some(fb) = plain_subspace_factor_base(&kc, &basis) else {
                        continue;
                    };
                    if fb.points.is_empty() {
                        continue;
                    }
                    nonempty += check(&kc, &fb, &mut rng, &format!("k{k} n{n} l{ell} b{b_index}"));
                }
            }
        }
        eprintln!("nonempty {nonempty}");
        assert!(nonempty >= 20, "nonempty {nonempty}");
    }

    /// The smallest field, and the full field at the dense cap:
    /// `n = 5`, `ℓ = 5` is `4ℓ = 20 = MAX_DENSE_VARS`.
    #[test]
    fn review_edge_fields_and_the_cap() {
        let mut rng = StdRng::seed_from_u64(0xed6e);
        for (n, ell) in [(3u32, 1usize), (3, 2), (3, 3), (5, 2)] {
            for a in 0u8..=1 {
                let Some(kc) = KoblitzCurve::new(a, n) else {
                    continue;
                };
                let basis = random_basis_any(n, ell, &mut rng);
                let Some(fb) = plain_subspace_factor_base(&kc, &basis) else {
                    continue;
                };
                if fb.points.is_empty() {
                    continue;
                }
                check(&kc, &fb, &mut rng, &format!("edge n{n} l{ell} a{a}"));
            }
        }
        let kc = KoblitzCurve::new(0, 5).unwrap();
        let st = FieldStructure::new(5, &kc.curve.irreducible);
        let basis = random_basis_any(5, 5, &mut rng);
        let t = S5Template::build_x(&basis, &kc.curve.b, &st).expect("4ℓ = 20 builds");
        assert_eq!(t.n_vars(), MAX_DENSE_VARS);
    }
    /// The `groebner_decompose` hook itself (the path `KIC_M4_DESCENT=s5`
    /// takes): with the dispatch forced to the template it must find a
    /// decomposition exactly when brute force does, return a member of
    /// the brute-force set, and actually run the template; with the
    /// chain requested it must not.
    #[test]
    fn dispatch_hook_agrees_with_brute_force_and_the_chain() {
        use crate::cryptanalysis::koblitz_index_calculus::groebner_decompose;
        let mut rng = StdRng::seed_from_u64(0xd15b);
        let engine = SolverEngine::default();
        let mut hooked = 0;
        let mut nonempty = 0;
        for (n, ell) in [(5u32, 2usize), (7, 2), (7, 3)] {
            let Some(kc) = KoblitzCurve::new(0, n) else {
                continue;
            };
            let basis = random_basis_any(n, ell, &mut rng);
            let Some(fb) = plain_subspace_factor_base(&kc, &basis) else {
                continue;
            };
            if fb.points.is_empty() {
                continue;
            }
            let st = FieldStructure::new(n, &kc.curve.irreducible);
            let index_of = fb.index_map();
            for target in review_targets(&kc, &fb, &mut rng) {
                let truth = brute(&kc, &fb, &target);
                nonempty += usize::from(!truth.is_empty());
                DISPATCH_OVERRIDE.with(|c| c.set(Some(M4Descent::S5Template)));
                let direct =
                    dispatch_groebner_m4(&kc, &fb, &index_of, &st, &target, engine, 1 << 30);
                let (found, _) =
                    groebner_decompose(&kc, &fb, &index_of, &st, &target, 4, engine, 1 << 30);
                // Under a chain request the hook stays out of the way.
                let guard = ChainGuard::request();
                let skipped =
                    dispatch_groebner_m4(&kc, &fb, &index_of, &st, &target, engine, 1 << 30);
                let (chain_found, _) =
                    groebner_decompose(&kc, &fb, &index_of, &st, &target, 4, engine, 1 << 30);
                drop(guard);
                DISPATCH_OVERRIDE.with(|c| c.set(None));
                assert!(skipped.is_none(), "chain request must bypass the hook");
                assert_eq!(chain_found.is_some(), !truth.is_empty(), "chain n{n}");
                if direct.is_some() {
                    hooked += 1;
                }
                assert_eq!(found.is_some(), !truth.is_empty(), "hook n{n} l{ell}");
                if let Some(mut idx) = found {
                    idx.sort_unstable();
                    assert!(truth.contains(&idx), "hook member n{n} l{ell}");
                }
            }
        }
        assert!(nonempty >= 6, "nonempty {nonempty}");
        assert!(hooked >= 6, "the template path ran {hooked} times");
    }

    /// A panic caught while the chain is requested must not leave the
    /// dispatch disabled on the thread.
    #[test]
    fn chain_request_is_restored_after_a_caught_panic() {
        assert!(!CHAIN_REQUESTED.with(|c| c.get()));
        let r = std::panic::catch_unwind(|| {
            let _g = ChainGuard::request();
            assert!(CHAIN_REQUESTED.with(|c| c.get()));
            panic!("unwind through the chain call");
        });
        assert!(r.is_err());
        assert!(!CHAIN_REQUESTED.with(|c| c.get()), "flag leaked");
    }
}
