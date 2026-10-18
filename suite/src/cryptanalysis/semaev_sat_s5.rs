//! # Specialised `m = 4` SAT decomposition: the symmetrised binary `S₅`.
//!
//! Four-summand decomposition (`m = 4`, Semaev `S₅`) of a target abscissa
//! `x_R` over a factor-base subspace `V = ⟨v₀, …, v_{ℓ−1}⟩ ⊆ F_{2ⁿ}`.
//! The generic route ([`crate::cryptanalysis::polynomial_reuse::build_decomposition_system_reusing`])
//! chains three `S₃` links through `2n` free intermediate unknowns and is
//! capped at 64 Boolean variables.  This module is the hardcoded
//! alternative, built the way [`crate::cryptanalysis::semaev_sat::encode_semaev_s4_with`]
//! builds `m = 3`:
//!
//! * **the symmetrised `S₅` itself**, hardcoded ([`S5_SYMMETRISED`]): 68
//!   terms `c_T(x_R, b) · e₁^{a₁} e₂^{a₂} e₃^{a₃} e₄^{a₄}` over the
//!   elementary symmetric functions of `X₁ … X₄`, valid for **every**
//!   binary curve `y² + xy = x³ + a₂x² + b` (`S₅` does not depend on
//!   `a₂`); the `b`-powers are kept, unlike the `b = 1` specialisation of
//!   [`crate::cryptanalysis::binary_semaev_s4`];
//! * **the correspondence block** `ε_{i,t} = σ_i(X₁, …, X₄)_t` tying each
//!   `e`-coordinate to the summand bits, with one Tseitin auxiliary per
//!   monomial of degree ≥ 2 on either side (`e`-monomials of the descended
//!   `S₅` reach degree 4: `popcount` of each exponent, summed, since every
//!   `e_i^{2^s}` is linear in the `ε`);
//! * parity constraints as native XOR rows or Tseitin-chained CNF
//!   ([`XorEncoding`]), and an optional `X₁ ≤ X₂ ≤ X₃ ≤ X₄` order on the
//!   subspace codes (the whole system is symmetric in the summands).
//!
//! The `e_i` live in `W_i = span{v_{k₁}⋯v_{k_i}}` rather than all of
//! `F_{2ⁿ}`: for the polynomial basis `vₖ = zᵏ` that is `i(ℓ−1)+1`
//! coordinates per `e_i` (the unreduced layout of the `S₄` module), and for
//! an arbitrary basis it is the rank of the products, found by elimination.
//!
//! ## Derivation of the table
//!
//! `S₅(x₁,…,x₄,x_R) = Res_X(S₃(x₁,x₂,X), S₄(x₃,x₄,x_R,X))` with
//! `S₄(x₃,x₄,x_R,X) = Res_Y(S₃(x₃,x₄,Y), S₃(x_R,X,Y))`, both taken in
//! characteristic 2 over `F₂[b, x_R]`, then rewritten over `e₁ … e₄` by
//! the leading-term algorithm (degree 8 in every `xᵢ`; 729 terms over the
//! `xᵢ`, 68 over the `eᵢ`).  The same script reproduces the twelve-term
//! `S₄` of [`crate::cryptanalysis::binary_semaev_s4`] exactly at `b = 1`.
//! The table is pinned in the tests by the Sylvester-determinant resultant
//! evaluated at random points of `F_{2³¹}` and `F_{2⁶¹}`
//! (`table_is_the_resultant`) and by planted four-point sums on random
//! curves (`s5_vanishes_on_planted_four_point_sums`).
//!
//! ## Semantics: the same decompositions as the generic chain
//!
//! `S₅ = 0` is necessary for a chain solution but not sufficient: the
//! chained system asks for intermediates `X₁ = x(±P₁±P₂)`,
//! `X₂ = x(±X₁-point ± P₃)` **in `F_{2ⁿ}`**, while `S₅` also vanishes
//! when they exist only over an extension or at infinity (repeated
//! summands, twist points).  Every model of the specialised encoding is
//! therefore filtered by an explicit `F_{2ⁿ}` chain check over all
//! orderings of the four summands ([`chain_compatible`]); what survives is
//! exactly the set of sorted code tuples of the generic system's models,
//! which the differential tests pin.  Models removed by the filter are
//! counted (`DecompositionCounters::rejected_by_chain`).
//!
//! ## Output order
//!
//! A decomposition is the four summands' subspace codes (bit `k` = the
//! coefficient of `v_k`), ascending within the tuple; the list is sorted
//! ascending lexicographically, for both paths.
//!
//! ## Dispatch
//!
//! [`sat_decompositions`] takes the specialised path for `m = 4` when it
//! applies (`n ≤ 63`, linearly independent basis) under
//! [`SatPath::Auto`], and the generic chain otherwise — for any `m`.
//! [`sat_decompose_dispatch`] does the same for the Koblitz driver's
//! first-liftable-decomposition oracle, falling back to
//! [`crate::cryptanalysis::koblitz_index_calculus::sat_decompose_with`].
//!
//! ## Measured
//!
//! Perfbench `sat/spec_s5_pair_*` (enumerate every decomposition of the
//! same targets; generic chain as base, this encoder as candidate;
//! polynomial basis, random `b`, one thread, 2026-10-09):
//!
//! | kernel | generic Ir | specialised Ir | ratio | paired wall speedup (5 rounds) |
//! |:--|--:|--:|--:|--:|
//! | `pair_native_n8l2` (4 targets) | 364.7 M | 60.7 M | 6.0× | 8.3× |
//! | `pair_cnf_n8l2` (4 targets) | 5 425.7 M | 229.7 M | 23.6× | 38.7× |
//! | `pair_native_n9l3` (2 planted) | 6 789.8 M | 1 473.2 M | 4.6× | 7.6× |
//! | `pair_native_n11l3` (2 planted) | 19 923.3 M | 1 346.2 M | 14.8× | 22.5× |
//!
//! It is not uniformly faster: the encoding carries one Tseitin auxiliary
//! per `ε`-monomial (about 5 300 at `n = 10, ℓ = 3` and 19 600 at
//! `n = 13, ℓ = 4`), so every target pays tens of milliseconds of search
//! over that graph even when the generic chain refutes it in under one
//! millisecond (seen on some random targets at `n = 8, 9`).  At
//! `n = 13, ℓ = 4` one target took 0.2–6 s here, and the generic chain
//! did not finish its first target within the remaining 100 s of a 120 s
//! probe — an observation, not a measured ratio.

use std::collections::{BTreeSet, HashMap};
use std::rc::Rc;

use num_bigint::BigUint;

use crate::binary_ecc::{BinaryPoint, F2mElement, IrreduciblePoly};
use crate::cryptanalysis::binary_semaev::{
    binary_semaev_s3, binary_semaev_s3_in_x3, solve_quadratic_f2m,
};
use crate::cryptanalysis::koblitz_groebner::FieldStructure;
use crate::cryptanalysis::koblitz_index_calculus::{
    lift_candidate, sat_decompose_with, FactorBaseDomain, FrobeniusFactorBase, KoblitzCurve,
    SatDecompositionOptions, SatDecompositionStats,
};
use crate::cryptanalysis::polynomial_reuse::build_decomposition_system_reusing;
use crate::cryptanalysis::sat::{Lit, SolveResult, Solver};
use crate::cryptanalysis::semaev_sat::{
    encode_boolean_system_with, encode_lex_le, encode_xor_eq_zero, xor_chain_aux_needed,
    XorEncoding,
};

// ── The hardcoded symmetrised S₅ ────────────────────────────────────

/// The symmetrised fifth summation polynomial of
/// `y² + xy = x³ + a₂x² + b` over `F_{2ⁿ}`:
///
/// ```text
///   S₅ = Σ_T  c_T(x_R, b) · e₁^{a₁} e₂^{a₂} e₃^{a₃} e₄^{a₄},
///   c_T = Σ_{(u, v)} x_R^u b^v,
/// ```
///
/// one entry `([a₁, a₂, a₃, a₄], [(u, v), …])` per term, `eᵢ` the
/// elementary symmetric functions of the four summand abscissae.  See the
/// module documentation for how it was derived and how it is pinned.
pub const S5_SYMMETRISED: [([u8; 4], &[(u8, u8)]); 68] = [
    ([0, 0, 0, 0], &[(0, 8)]),
    ([0, 0, 0, 1], &[(1, 6)]),
    ([0, 0, 0, 2], &[(0, 5), (4, 4)]),
    ([0, 0, 0, 3], &[(1, 4), (5, 2)]),
    ([0, 0, 0, 4], &[(4, 1)]),
    ([0, 0, 0, 5], &[(1, 2), (5, 0)]),
    ([0, 0, 0, 6], &[(0, 1), (4, 0)]),
    ([0, 0, 0, 7], &[(1, 0)]),
    ([0, 0, 0, 8], &[(0, 0)]),
    ([0, 0, 2, 0], &[(2, 5)]),
    ([0, 0, 2, 1], &[(1, 4), (3, 4), (5, 3)]),
    ([0, 0, 2, 2], &[(4, 2)]),
    ([0, 0, 2, 3], &[(1, 2), (3, 1), (5, 1)]),
    ([0, 0, 2, 4], &[(2, 1), (4, 0)]),
    ([0, 0, 2, 5], &[(3, 0)]),
    ([0, 0, 4, 0], &[(0, 4), (8, 2)]),
    ([0, 0, 4, 1], &[(3, 2), (5, 2), (7, 1)]),
    ([0, 0, 4, 2], &[(4, 1), (8, 0)]),
    ([0, 0, 4, 3], &[(5, 0)]),
    ([0, 0, 6, 0], &[(6, 1)]),
    ([0, 0, 6, 1], &[(7, 0)]),
    ([0, 0, 8, 0], &[(8, 0)]),
    ([0, 2, 0, 1], &[(1, 5), (3, 4)]),
    ([0, 2, 0, 2], &[(2, 3), (6, 2)]),
    ([0, 2, 0, 3], &[(5, 1)]),
    ([0, 2, 0, 4], &[(2, 1), (6, 0)]),
    ([0, 2, 0, 5], &[(1, 1), (3, 0)]),
    ([0, 2, 2, 1], &[(1, 3)]),
    ([0, 2, 2, 2], &[(4, 1)]),
    ([0, 2, 2, 3], &[(5, 0)]),
    ([0, 2, 4, 1], &[(5, 1)]),
    ([0, 4, 0, 0], &[(4, 4)]),
    ([0, 4, 0, 1], &[(1, 4), (3, 3)]),
    ([0, 4, 0, 2], &[(0, 3), (4, 2)]),
    ([0, 4, 0, 3], &[(1, 2), (3, 1)]),
    ([0, 4, 0, 4], &[(4, 0)]),
    ([0, 4, 2, 0], &[(2, 3)]),
    ([0, 4, 2, 1], &[(3, 2)]),
    ([0, 6, 0, 1], &[(1, 3)]),
    ([0, 8, 0, 0], &[(0, 4)]),
    ([2, 0, 0, 1], &[(3, 5)]),
    ([2, 0, 0, 2], &[(2, 4), (4, 3)]),
    ([2, 0, 0, 3], &[(1, 3), (3, 2), (5, 2)]),
    ([2, 0, 0, 4], &[(4, 1)]),
    ([2, 0, 0, 5], &[(1, 1), (3, 1), (5, 0)]),
    ([2, 0, 0, 6], &[(2, 0)]),
    ([2, 0, 2, 1], &[(7, 2)]),
    ([2, 0, 2, 2], &[(2, 2), (6, 1)]),
    ([2, 0, 2, 3], &[(7, 0)]),
    ([2, 0, 4, 1], &[(5, 1), (7, 1)]),
    ([2, 0, 4, 2], &[(6, 0)]),
    ([2, 2, 0, 1], &[(5, 3)]),
    ([2, 2, 0, 2], &[(4, 2)]),
    ([2, 2, 0, 3], &[(1, 2)]),
    ([2, 2, 2, 1], &[(3, 2)]),
    ([2, 4, 0, 1], &[(3, 3)]),
    ([2, 4, 0, 2], &[(2, 2)]),
    ([4, 0, 0, 1], &[(5, 4)]),
    ([4, 0, 0, 2], &[(4, 3), (8, 2)]),
    ([4, 0, 0, 3], &[(3, 2), (5, 2), (7, 1)]),
    ([4, 0, 0, 4], &[(0, 2), (8, 0)]),
    ([4, 0, 2, 0], &[(6, 3)]),
    ([4, 0, 2, 1], &[(5, 2), (7, 2)]),
    ([4, 0, 4, 0], &[(4, 2)]),
    ([4, 2, 0, 1], &[(5, 3)]),
    ([6, 0, 0, 1], &[(7, 3)]),
    ([6, 0, 0, 2], &[(6, 2)]),
    ([8, 0, 0, 0], &[(8, 4)]),
];

/// Highest power of `x_R` in any coefficient of [`S5_SYMMETRISED`].
const XR_DEGREE: usize = 8;

/// Elementary symmetric functions `(e₁, e₂, e₃, e₄)` of four field
/// elements.
pub fn elementary_symmetric_4(x: [&F2mElement; 4], irr: &IrreduciblePoly) -> [F2mElement; 4] {
    let m = x[0].m_value();
    let mut e = [
        F2mElement::one(m),
        F2mElement::zero(m),
        F2mElement::zero(m),
        F2mElement::zero(m),
        F2mElement::zero(m),
    ];
    // Multiply out Π (1 + xᵢ T), one factor at a time, top degree first.
    for xi in x {
        for d in (1..=4).rev() {
            let t = e[d - 1].mul(xi, irr);
            e[d] = e[d].add(&t);
        }
    }
    [e[1].clone(), e[2].clone(), e[3].clone(), e[4].clone()]
}

/// Evaluate the hardcoded symmetrised `S₅` ([`S5_SYMMETRISED`]) at
/// `(e₁, …, e₄)`, target abscissa `x_R` and curve coefficient `b`.
pub fn symmetrised_s5_eval(
    e: [&F2mElement; 4],
    x_r: &F2mElement,
    b: &F2mElement,
    irr: &IrreduciblePoly,
) -> F2mElement {
    let m = x_r.m_value();
    let powers = |z: &F2mElement, top: usize| {
        let mut out = vec![F2mElement::one(m)];
        for k in 1..=top {
            let next = out[k - 1].mul(z, irr);
            out.push(next);
        }
        out
    };
    let ep: Vec<Vec<F2mElement>> = e.iter().map(|z| powers(z, 8)).collect();
    let rp = powers(x_r, XR_DEGREE);
    let bp = powers(b, 8);
    let mut acc = F2mElement::zero(m);
    for (a, coef) in S5_SYMMETRISED.iter() {
        let mut c = F2mElement::zero(m);
        for &(u, v) in coef.iter() {
            c = c.add(&rp[u as usize].mul(&bp[v as usize], irr));
        }
        let mut t = c;
        for i in 0..4 {
            t = t.mul(&ep[i][a[i] as usize], irr);
        }
        acc = acc.add(&t);
    }
    acc
}

/// `S₅(x₁, x₂, x₃, x₄, x_R)` through the hardcoded table: the elementary
/// symmetric functions, then [`symmetrised_s5_eval`].
pub fn semaev_s5_eval(
    x: [&F2mElement; 4],
    x_r: &F2mElement,
    b: &F2mElement,
    irr: &IrreduciblePoly,
) -> F2mElement {
    let e = elementary_symmetric_4(x, irr);
    symmetrised_s5_eval([&e[0], &e[1], &e[2], &e[3]], x_r, b, irr)
}

// ── Word-sized field arithmetic (n ≤ 63) ────────────────────────────

/// `F_{2ⁿ}` for `n ≤ 63`, elements as `u64` bit vectors.  The encoder's
/// one hot loop is evaluating the template's `x_R`-polynomials, which is
/// a few word operations per coefficient here.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct Gf {
    n: u32,
    /// The low terms of the irreducible, `z^n ≡ low`.
    low: u64,
}

impl Gf {
    fn new(n: u32, irr: &IrreduciblePoly) -> Option<Self> {
        if n == 0 || n > 63 || irr.degree != n {
            return None;
        }
        let mut low = 0u64;
        for &t in &irr.low_terms {
            if t >= n {
                return None;
            }
            low ^= 1 << t;
        }
        Some(Self { n, low })
    }

    fn mask(self) -> u64 {
        (1u64 << self.n) - 1
    }

    fn mul(self, a: u64, b: u64) -> u64 {
        let mut prod = 0u128;
        let mut a = a;
        while a != 0 {
            prod ^= (b as u128) << a.trailing_zeros();
            a &= a - 1;
        }
        self.reduce(prod)
    }

    fn reduce(self, mut x: u128) -> u64 {
        let n = self.n;
        let mut k = 127 - x.leading_zeros().min(127);
        while x >> n != 0 {
            if (x >> k) & 1 == 1 {
                x ^= 1u128 << k;
                x ^= (self.low as u128) << (k - n);
            }
            k -= 1;
        }
        x as u64
    }

    fn pow(self, a: u64, e: u32) -> u64 {
        let mut out = 1u64;
        for _ in 0..e {
            out = self.mul(out, a);
        }
        out
    }

    /// `t ↦ c·t` as a table: `table[k] = c·zᵏ`.
    fn mul_table(self, c: u64) -> Vec<u64> {
        (0..self.n).map(|k| self.mul(c, 1u64 << k)).collect()
    }
}

fn apply_table(table: &[u64], x: u64) -> u64 {
    let mut out = 0u64;
    let mut x = x;
    while x != 0 {
        out ^= table[x.trailing_zeros() as usize];
        x &= x - 1;
    }
    out
}

fn to_word(e: &F2mElement) -> u64 {
    e.raw_bits().first().copied().unwrap_or(0)
}

fn from_word(w: u64, n: u32) -> F2mElement {
    let bits: Vec<u32> = (0..n).filter(|k| (w >> k) & 1 == 1).collect();
    F2mElement::from_bit_positions(&bits, n)
}

// ── Monomials ───────────────────────────────────────────────────────

/// A squarefree Boolean monomial of degree ≤ 4: sorted variable indices.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
struct Mono {
    len: u8,
    v: [u16; 4],
}

impl Mono {
    const ONE: Mono = Mono { len: 0, v: [0; 4] };

    fn vars(&self) -> &[u16] {
        &self.v[..self.len as usize]
    }

    /// `self · x_var`, with `x² = x`.
    fn times(self, var: u16) -> Mono {
        let vs = self.vars();
        if vs.contains(&var) {
            return self;
        }
        assert!(self.len < 4, "monomials of S₅ have degree ≤ 4");
        let mut out = Mono::ONE;
        let mut placed = false;
        for &x in vs {
            if !placed && var < x {
                out.v[out.len as usize] = var;
                out.len += 1;
                placed = true;
            }
            out.v[out.len as usize] = x;
            out.len += 1;
        }
        if !placed {
            out.v[out.len as usize] = var;
            out.len += 1;
        }
        out
    }
}

// ── The target-independent template ─────────────────────────────────

/// Everything about the `m = 4` encoding that does not depend on the
/// target: the `e`-space layout, the correspondence block, and the
/// descended `S₅` as `F_{2ⁿ}`-valued coefficients per `ε`-monomial, each a
/// polynomial of degree ≤ 8 in `x_R`.
#[derive(Debug)]
pub struct S5Template {
    gf: Gf,
    l: usize,
    basis: Vec<u64>,
    b: u64,
    /// `dims[i]` = number of `ε`-coordinates of `e_{i+1}`.
    dims: [usize; 4],
    /// First `e`-space index of `e_{i+1}`.
    base: [usize; 4],
    /// `corr[k] = (e-space index, x-monomials)` — `ε ⊕ Σ monos = 0`.
    corr: Vec<(u32, Vec<Mono>)>,
    /// The distinct x-monomials of degree ≥ 2 (all of them, in order).
    x_monos: Vec<Mono>,
    /// `semaev[k] = (ε-monomial, h)`: the monomial's coefficient in the
    /// descended `S₅` is `Σ_u h[u] x_R^u`.  The constant monomial, if
    /// present, is first.
    semaev: Vec<(Mono, [u64; XR_DEGREE + 1])>,
}

impl S5Template {
    /// Build the template for the factor base `basis` of `F_{2ⁿ}` (field
    /// given by `irr`) and curve coefficient `b`.  `None` when the
    /// specialised path does not apply: `n > 63`, an empty or linearly
    /// dependent basis, `b = 0`, or more than `u16::MAX` variables.
    pub fn build(basis: &[F2mElement], b: &F2mElement, irr: &IrreduciblePoly) -> Option<Self> {
        let gf = Gf::new(irr.degree, irr)?;
        let l = basis.len();
        if l == 0 || 4 * l > u16::MAX as usize || basis.iter().any(|v| v.m_value() != gf.n) {
            return None;
        }
        let basis: Vec<u64> = basis.iter().map(to_word).collect();
        let b = to_word(b);
        if b == 0 || basis.iter().chain([&b]).any(|&w| w & !gf.mask() != 0) {
            return None;
        }
        // The basis must be independent, or codes would not name elements.
        if Span::new().extend_rank(&basis) != l {
            return None;
        }

        // W_i = span of the i-fold products, and every product's
        // coordinates in the chosen basis of W_i.
        let mut dims = [0usize; 4];
        let mut base = [0usize; 4];
        let mut w_vals: Vec<Vec<u64>> = Vec::with_capacity(4);
        let mut coords: Vec<HashMap<Vec<usize>, u64>> = Vec::with_capacity(4);
        for i in 1..=4usize {
            let mut span = Span::new();
            let mut map = HashMap::new();
            let mut vals = Vec::new();
            for ks in multisets(l, i) {
                let prod = ks.iter().fold(1u64, |acc, &k| gf.mul(acc, basis[k]));
                let c = span.coords_or_insert(prod, &mut vals);
                map.insert(ks, c);
            }
            dims[i - 1] = vals.len();
            w_vals.push(vals);
            coords.push(map);
        }
        for i in 1..4 {
            base[i] = base[i - 1] + dims[i - 1];
        }
        let n_e = base[3] + dims[3];
        if n_e > u16::MAX as usize {
            return None;
        }

        // Correspondence: ε_{i,t} = coordinate t of σ_i(X₁, …, X₄).
        let mut corr: Vec<(u32, Vec<Mono>)> = Vec::with_capacity(n_e);
        for i in 0..4 {
            for t in 0..dims[i] {
                corr.push(((base[i] + t) as u32, Vec::new()));
            }
        }
        let mut x_mono_set = BTreeSet::new();
        for size in 1..=4usize {
            for positions in subsets(4, size) {
                for ks in tuples(l, size) {
                    let mut sorted = ks.clone();
                    sorted.sort_unstable();
                    let c = coords[size - 1][&sorted];
                    let mut mono = Mono::ONE;
                    for (&p, &k) in positions.iter().zip(&ks) {
                        mono = mono.times((p * l + k) as u16);
                    }
                    if size >= 2 {
                        x_mono_set.insert(mono);
                    }
                    let mut bits = c;
                    while bits != 0 {
                        let t = bits.trailing_zeros() as usize;
                        corr[base[size - 1] + t].1.push(mono);
                        bits &= bits - 1;
                    }
                }
            }
        }
        for (_, monos) in &mut corr {
            monos.sort_unstable();
        }

        // Descended S₅: expand every term's product of linear forms.
        let b_pow: Vec<u64> = (0..=8).map(|v| gf.pow(b, v)).collect();
        let mut acc: HashMap<Mono, [u64; XR_DEGREE + 1]> = HashMap::new();
        for (a, coef) in S5_SYMMETRISED.iter() {
            let mut terms: HashMap<Mono, u64> = HashMap::new();
            terms.insert(Mono::ONE, 1);
            for i in 0..4 {
                for s in 0..4 {
                    if (a[i] >> s) & 1 == 0 {
                        continue;
                    }
                    // e_{i+1}^{2^s} = Σ_t ε_{i,t} · w_{i,t}^{2^s}.
                    let form: Vec<(u16, u64)> = w_vals[i]
                        .iter()
                        .enumerate()
                        .map(|(t, &w)| {
                            let mut c = w;
                            for _ in 0..s {
                                c = gf.mul(c, c);
                            }
                            ((base[i] + t) as u16, c)
                        })
                        .collect();
                    let mut next: HashMap<Mono, u64> =
                        HashMap::with_capacity(terms.len() * form.len());
                    for (mono, &c) in &terms {
                        for &(var, w) in &form {
                            *next.entry(mono.times(var)).or_insert(0) ^= gf.mul(c, w);
                        }
                    }
                    next.retain(|_, c| *c != 0);
                    terms = next;
                }
            }
            for (mono, c) in terms {
                let slot = acc.entry(mono).or_insert([0; XR_DEGREE + 1]);
                for &(u, v) in coef.iter() {
                    slot[u as usize] ^= gf.mul(c, b_pow[v as usize]);
                }
            }
        }
        let mut semaev: Vec<(Mono, [u64; XR_DEGREE + 1])> = acc
            .into_iter()
            .filter(|(_, h)| h.iter().any(|&w| w != 0))
            .collect();
        semaev.sort_unstable_by_key(|(m, _)| *m);

        Some(Self {
            gf,
            l,
            basis,
            b,
            dims,
            base,
            corr,
            x_monos: x_mono_set.into_iter().collect(),
            semaev,
        })
    }

    /// Factor-base dimension `ℓ`.
    pub fn ell(&self) -> usize {
        self.l
    }

    /// Number of `ε`-coordinates of `e₁ … e₄`.
    pub fn e_dims(&self) -> [usize; 4] {
        self.dims
    }

    /// Distinct `ε`-monomials of the descended `S₅` (before a target
    /// zeroes any of them).
    pub fn n_semaev_monomials(&self) -> usize {
        self.semaev.len()
    }

    fn matches(&self, basis: &[F2mElement], b: &F2mElement, irr: &IrreduciblePoly) -> bool {
        Gf::new(irr.degree, irr) == Some(self.gf)
            && to_word(b) == self.b
            && basis.len() == self.basis.len()
            && basis.iter().zip(&self.basis).all(|(e, &w)| to_word(e) == w)
    }

    /// The field value of a subspace code.
    fn element(&self, code: u64) -> u64 {
        let mut x = 0u64;
        for (k, &v) in self.basis.iter().enumerate() {
            if (code >> k) & 1 == 1 {
                x ^= v;
            }
        }
        x
    }

    /// The descended `S₅` coefficients at target `x_R`: one field value
    /// per `ε`-monomial (constant first if present), in template order.
    fn coefficients_at(&self, x_r: u64) -> Vec<(Mono, u64)> {
        let table = self.gf.mul_table(x_r);
        self.semaev
            .iter()
            .filter_map(|(mono, h)| {
                let mut acc = h[XR_DEGREE];
                for u in (0..XR_DEGREE).rev() {
                    acc = apply_table(&table, acc) ^ h[u];
                }
                (acc != 0).then_some((*mono, acc))
            })
            .collect()
    }

    /// `S₅` at four field values through the table (word arithmetic).
    fn s5_at(&self, xs: [u64; 4], x_r: u64) -> u64 {
        let gf = self.gf;
        let mut e = [1u64, 0, 0, 0, 0];
        for &x in &xs {
            for d in (1..=4).rev() {
                e[d] ^= gf.mul(e[d - 1], x);
            }
        }
        let mut acc = 0u64;
        for (a, coef) in S5_SYMMETRISED.iter() {
            let mut c = 0u64;
            for &(u, v) in coef.iter() {
                c ^= gf.mul(gf.pow(x_r, u as u32), gf.pow(self.b, v as u32));
            }
            for i in 0..4 {
                c = gf.mul(c, gf.pow(e[i + 1], a[i] as u32));
            }
            acc ^= c;
        }
        acc
    }
}

/// Echelon form over `F₂` of `n ≤ 64`-bit vectors, with each pivot's
/// coordinates in the inserted basis.
struct Span {
    /// `(reduced vector, coordinates)`, leading bits distinct, sorted by
    /// leading bit descending.
    pivots: Vec<(u64, u64)>,
}

impl Span {
    fn new() -> Self {
        Self { pivots: Vec::new() }
    }

    fn reduce(&self, v: u64) -> (u64, u64) {
        let (mut r, mut c) = (v, 0u64);
        for &(p, pc) in &self.pivots {
            let lead = 63 - p.leading_zeros();
            if (r >> lead) & 1 == 1 {
                r ^= p;
                c ^= pc;
            }
        }
        (r, c)
    }

    /// Coordinates of `v` in the basis `vals`; a vector outside the span
    /// becomes the next basis vector.
    fn coords_or_insert(&mut self, v: u64, vals: &mut Vec<u64>) -> u64 {
        let (r, c) = self.reduce(v);
        if r == 0 {
            return c;
        }
        let t = vals.len();
        assert!(t < 64, "a subspace of F_2^n with n ≤ 63");
        vals.push(v);
        self.pivots.push((r, c ^ (1 << t)));
        self.pivots
            .sort_unstable_by_key(|&(p, _)| std::cmp::Reverse(63 - p.leading_zeros()));
        1 << t
    }

    fn extend_rank(mut self, vs: &[u64]) -> usize {
        let mut vals = Vec::new();
        for &v in vs {
            self.coords_or_insert(v, &mut vals);
        }
        vals.len()
    }
}

/// Non-decreasing `size`-tuples over `0..l`, lexicographic.
fn multisets(l: usize, size: usize) -> Vec<Vec<usize>> {
    let mut out = Vec::new();
    let mut cur = vec![0usize; size];
    loop {
        out.push(cur.clone());
        let Some(pos) = (0..size).rev().find(|&p| cur[p] + 1 < l) else {
            return out;
        };
        cur[pos] += 1;
        for q in pos + 1..size {
            cur[q] = cur[pos];
        }
    }
}

/// Strictly increasing `size`-subsets of `0..m`.
fn subsets(m: usize, size: usize) -> Vec<Vec<usize>> {
    (0u32..1 << m)
        .filter(|s| s.count_ones() as usize == size)
        .map(|s| (0..m).filter(|&i| (s >> i) & 1 == 1).collect())
        .collect()
}

/// All `size`-tuples over `0..l`.
fn tuples(l: usize, size: usize) -> Vec<Vec<usize>> {
    let mut out = vec![Vec::new()];
    for _ in 0..size {
        out = out
            .into_iter()
            .flat_map(|t| {
                (0..l).map(move |k| {
                    let mut t = t.clone();
                    t.push(k);
                    t
                })
            })
            .collect();
    }
    out
}

const LOCAL_TEMPLATES: usize = 4;

thread_local! {
    static TEMPLATES: std::cell::RefCell<Vec<Rc<S5Template>>> =
        const { std::cell::RefCell::new(Vec::new()) };
}

/// [`S5Template::build`] through a small per-thread memo, exact-match
/// keyed on the field, basis and `b` (as
/// [`crate::cryptanalysis::polynomial_reuse::build_decomposition_system_reusing`]
/// memoises the generic template).
pub fn s5_template(
    basis: &[F2mElement],
    b: &F2mElement,
    irr: &IrreduciblePoly,
) -> Option<Rc<S5Template>> {
    if let Some(hit) = TEMPLATES.with(|t| {
        t.borrow()
            .iter()
            .find(|x| x.matches(basis, b, irr))
            .cloned()
    }) {
        return Some(hit);
    }
    let built = Rc::new(S5Template::build(basis, b, irr)?);
    TEMPLATES.with(|t| {
        let mut t = t.borrow_mut();
        if t.len() == LOCAL_TEMPLATES {
            t.remove(0);
        }
        t.push(built.clone());
    });
    Some(built)
}

// ── Encoding ────────────────────────────────────────────────────────

/// Knobs for the `S₅` encoder.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct S5Options {
    /// How parity constraints reach the solver.
    pub encoding: XorEncoding,
    /// Add `code(X₁) ≤ code(X₂) ≤ code(X₃) ≤ code(X₄)` (bit `ℓ−1` most
    /// significant).  Exact: the system is symmetric in the summands.
    pub break_symmetry: bool,
}

impl Default for S5Options {
    fn default() -> Self {
        Self {
            encoding: XorEncoding::Native,
            break_symmetry: true,
        }
    }
}

/// A SAT-encoded symmetrised `S₅` system for one target.
pub struct S5SatEncoding {
    pub n: u32,
    pub l: u32,
    /// `4ℓ` summand bits at SAT indices `1..=4ℓ`, `X_{i+1}` bit `k` at
    /// `1 + iℓ + k`.
    pub n_x_vars: u32,
    /// `ε`-coordinates of `e₁ … e₄`, after the summand bits.
    pub n_e_vars: u32,
    /// Tseitin monomial auxiliaries (correspondence and `S₅` sides).
    pub n_aux_vars: u32,
    /// `ε`-monomials with a nonzero coefficient at this target.
    pub n_semaev_monomials: u32,
    pub solver: Solver,
    pub trivially_unsat: bool,
}

impl S5SatEncoding {
    /// The four subspace codes of the current model.
    pub fn decode_codes(&self) -> [u64; 4] {
        let model = self.solver.model();
        let l = self.l as usize;
        std::array::from_fn(|i| {
            (0..l).fold(0u64, |acc, k| acc | (u64::from(model[i * l + k]) << k))
        })
    }

    /// The clause forbidding the current summand codes.
    fn blocking_clause(&self) -> Vec<Lit> {
        let model = self.solver.model();
        (0..self.n_x_vars as usize)
            .map(|i| {
                if model[i] {
                    -((i + 1) as Lit)
                } else {
                    (i + 1) as Lit
                }
            })
            .collect()
    }
}

/// **Encode the symmetrised `S₅` decomposition system** of target
/// abscissa `x_r` over the factor base `basis` (see the module docs).
/// `None` when the specialised path does not apply
/// ([`S5Template::build`]).
pub fn encode_semaev_s5_with(
    basis: &[F2mElement],
    irr: &IrreduciblePoly,
    b: &F2mElement,
    x_r: &F2mElement,
    opts: S5Options,
) -> Option<S5SatEncoding> {
    let tpl = s5_template(basis, b, irr)?;
    Some(encode_from_template(&tpl, to_word(x_r), opts))
}

fn encode_from_template(tpl: &S5Template, x_r: u64, opts: S5Options) -> S5SatEncoding {
    let l = tpl.l;
    let n_x = 4 * l as u32;
    let n_e = (tpl.base[3] + tpl.dims[3]) as u32;
    let x_sat = |v: u16| u32::from(v) + 1;
    let e_sat = |v: u16| n_x + u32::from(v) + 1;

    let coefficients = tpl.coefficients_at(x_r);
    let mut next = n_x + n_e + 1;
    // Monomial auxiliaries: x-side first, then ε-side, each in template
    // order.
    let mut x_aux: HashMap<Mono, u32> = HashMap::with_capacity(tpl.x_monos.len());
    for m in &tpl.x_monos {
        x_aux.insert(*m, next);
        next += 1;
    }
    let mut e_aux: HashMap<Mono, u32> = HashMap::new();
    let mut e_aux_order: Vec<Mono> = Vec::new();
    for (m, _) in &coefficients {
        if m.len >= 2 {
            e_aux.insert(*m, next);
            e_aux_order.push(*m);
            next += 1;
        }
    }
    let n_aux = next - (n_x + n_e + 1);

    // Rows: correspondence, then the n descended equations.
    let mut rows: Vec<(Vec<u32>, bool)> = Vec::with_capacity(tpl.corr.len() + tpl.gf.n as usize);
    for (e, monos) in &tpl.corr {
        let mut vars = Vec::with_capacity(monos.len() + 1);
        vars.push(e_sat(*e as u16));
        for m in monos {
            vars.push(if m.len == 1 { x_sat(m.v[0]) } else { x_aux[m] });
        }
        rows.push((vars, false));
    }
    let mut constant = 0u64;
    let mut eq_vars: Vec<Vec<u32>> = vec![Vec::new(); tpl.gf.n as usize];
    for (m, c) in &coefficients {
        if m.len == 0 {
            constant = *c;
            continue;
        }
        let var = if m.len == 1 { e_sat(m.v[0]) } else { e_aux[m] };
        let mut bits = *c;
        while bits != 0 {
            eq_vars[bits.trailing_zeros() as usize].push(var);
            bits &= bits - 1;
        }
    }
    for (j, vars) in eq_vars.into_iter().enumerate() {
        rows.push((vars, (constant >> j) & 1 == 1));
    }

    let mut chains: Vec<Vec<u32>> = Vec::with_capacity(rows.len());
    for (vars, _) in &rows {
        let count = match opts.encoding {
            XorEncoding::Native => 0,
            XorEncoding::Cnf => xor_chain_aux_needed(vars.len()) as u32,
        };
        chains.push((next..next + count).collect());
        next += count;
    }
    let sym_base = next;
    if opts.break_symmetry {
        next += 3 * l as u32;
    }

    let mut solver = Solver::new(next - 1);
    let mut trivially_unsat = false;
    if opts.break_symmetry {
        for pair in 0..3u32 {
            let a: Vec<u32> = (0..l as u32).map(|k| 1 + pair * l as u32 + k).collect();
            let bb: Vec<u32> = (0..l as u32)
                .map(|k| 1 + (pair + 1) * l as u32 + k)
                .collect();
            let eq: Vec<u32> = (0..l as u32)
                .map(|k| sym_base + pair * l as u32 + k)
                .collect();
            encode_lex_le(&mut solver, &a, &bb, &eq);
        }
    }
    // AND definitions z ↔ v₁ ∧ … ∧ v_k.
    let and_defs = tpl
        .x_monos
        .iter()
        .map(|m| (m, x_aux[m], true))
        .chain(e_aux_order.iter().map(|m| (m, e_aux[m], false)));
    for (m, z, is_x) in and_defs {
        let zi = z as Lit;
        let mut big = Vec::with_capacity(m.len as usize + 1);
        big.push(zi);
        for &v in m.vars() {
            let v = if is_x { x_sat(v) } else { e_sat(v) } as Lit;
            solver.add_clause(vec![-zi, v]);
            big.push(-v);
        }
        solver.add_clause(big);
    }
    for ((vars, rhs), chain) in rows.iter().zip(&chains) {
        if vars.is_empty() {
            if *rhs {
                solver.add_clause(vec![]);
                trivially_unsat = true;
            }
            continue;
        }
        match opts.encoding {
            XorEncoding::Native => {
                if !solver.add_xor(vars, *rhs) {
                    trivially_unsat = true;
                }
            }
            XorEncoding::Cnf => {
                let lits: Vec<Lit> = vars.iter().map(|&v| v as Lit).collect();
                if encode_xor_eq_zero(&mut solver, &lits, *rhs, chain) {
                    trivially_unsat = true;
                }
            }
        }
    }
    // Every other variable is determined by the summand bits.
    let free: Vec<u32> = (1..=n_x).collect();
    solver.set_branch_priority(&free);

    S5SatEncoding {
        n: tpl.gf.n,
        l: l as u32,
        n_x_vars: n_x,
        n_e_vars: n_e,
        n_aux_vars: n_aux,
        n_semaev_monomials: coefficients.iter().filter(|(m, _)| m.len > 0).count() as u32,
        solver,
        trivially_unsat,
    }
}

// ── The F_{2ⁿ} chain check ──────────────────────────────────────────

/// Roots in `F_{2ⁿ}` of `S₃(a, c, X)` as a polynomial in `X`.
fn s3_roots(
    a: &F2mElement,
    c: &F2mElement,
    b: &F2mElement,
    irr: &IrreduciblePoly,
) -> Vec<F2mElement> {
    let (qa, qb, qc) = binary_semaev_s3_in_x3(a, c, b, irr);
    // qa = qb = 0 forces a = c = 0, where qc = b ≠ 0: no root.
    solve_quadratic_f2m(&qa, &qb, &qc, irr.degree, irr)
}

/// Whether the ordered summands admit the generic chain's intermediates
/// in `F_{2ⁿ}`: `S₃(x₁,x₂,X₁) = S₃(X₁,x₃,X₂) = S₃(X₂,x₄,x_R) = 0`.
fn ordered_chain(
    x: [&F2mElement; 4],
    x_r: &F2mElement,
    b: &F2mElement,
    irr: &IrreduciblePoly,
) -> bool {
    s3_roots(x[0], x[1], b, irr).iter().any(|x1| {
        s3_roots(x1, x[2], b, irr)
            .iter()
            .any(|x2| binary_semaev_s3(x2, x[3], x_r, b, irr).is_zero())
    })
}

/// **Whether some ordering of the four summands satisfies the generic
/// chained `m = 4` system** — i.e. whether this multiset is among the
/// sorted code tuples of
/// [`crate::cryptanalysis::polynomial_reuse::build_decomposition_system_reusing`]'s
/// models.  The filter that makes the specialised path return exactly the
/// generic path's decompositions (module docs).
pub fn chain_compatible(
    x: [&F2mElement; 4],
    x_r: &F2mElement,
    b: &F2mElement,
    irr: &IrreduciblePoly,
) -> bool {
    let mut seen: Vec<[u64; 4]> = Vec::new();
    for p in PERMUTATIONS_4.iter() {
        let ordered = [x[p[0]], x[p[1]], x[p[2]], x[p[3]]];
        let key = ordered.map(to_word);
        if seen.contains(&key) {
            continue;
        }
        seen.push(key);
        if ordered_chain(ordered, x_r, b, irr) {
            return true;
        }
    }
    false
}

const PERMUTATIONS_4: [[usize; 4]; 24] = [
    [0, 1, 2, 3],
    [0, 1, 3, 2],
    [0, 2, 1, 3],
    [0, 2, 3, 1],
    [0, 3, 1, 2],
    [0, 3, 2, 1],
    [1, 0, 2, 3],
    [1, 0, 3, 2],
    [1, 2, 0, 3],
    [1, 2, 3, 0],
    [1, 3, 0, 2],
    [1, 3, 2, 0],
    [2, 0, 1, 3],
    [2, 0, 3, 1],
    [2, 1, 0, 3],
    [2, 1, 3, 0],
    [2, 3, 0, 1],
    [2, 3, 1, 0],
    [3, 0, 1, 2],
    [3, 0, 2, 1],
    [3, 1, 0, 2],
    [3, 1, 2, 0],
    [3, 2, 0, 1],
    [3, 2, 1, 0],
];

// ── Enumeration and dispatch ────────────────────────────────────────

/// Which SAT encoding answers a decomposition query.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub enum SatPath {
    /// The specialised encoder where it applies (`m = 4`), the generic
    /// chain otherwise.
    #[default]
    Auto,
    /// The specialised encoder only; `None` where it does not apply.
    Specialised,
    /// The generic chained system, for any `m`.
    Generic,
}

/// The path a query actually took.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum SatPathTaken {
    SymmetrisedS5,
    GenericChain,
}

/// Options for [`sat_decompositions`].
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct SatEnumOptions {
    pub path: SatPath,
    pub encoding: XorEncoding,
    /// Symmetry breaking for the specialised encoder (the generic one is
    /// enumerated as it is built).
    pub break_symmetry: bool,
    /// Cumulative conflict cap over the whole enumeration.
    pub conflict_budget: u64,
    /// Models examined before giving up.
    pub max_models: usize,
}

impl Default for SatEnumOptions {
    fn default() -> Self {
        Self {
            path: SatPath::Auto,
            encoding: XorEncoding::Native,
            break_symmetry: true,
            conflict_budget: u64::MAX,
            max_models: usize::MAX,
        }
    }
}

/// Work counters of one enumeration.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct DecompositionCounters {
    /// Solve calls (one per model plus the final refutation).
    pub solver_calls: u64,
    /// Models the solver produced.
    pub models: u64,
    /// Specialised path: models whose summands have no `F_{2ⁿ}` chain in
    /// any order (`S₅ = 0` over an extension only).  Zero on the generic
    /// path.
    pub rejected_by_chain: u64,
    /// Models that failed the independent check against the polynomial
    /// system — always zero unless an encoding is wrong.
    pub spurious: u64,
    pub conflicts: u64,
    pub decisions: u64,
    pub propagations: u64,
    /// Encoding size: variables, original clauses, native XOR rows.
    pub vars: u64,
    pub clauses: u64,
    pub xor_rows: u64,
}

/// The decompositions of one target (see the module docs for the order).
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct DecompositionSet {
    /// Each entry: the `m` summand codes ascending; the list ascending.
    pub decompositions: Vec<Vec<u64>>,
    /// `true` when the final solve refuted the remainder, so the list is
    /// every decomposition; `false` after a budget or model cap, or a
    /// spurious model (fail closed).
    pub complete: bool,
    pub counters: DecompositionCounters,
}

/// **Every `m = 4` decomposition through the symmetrised `S₅` encoder.**
/// `None` when the specialised path does not apply.
pub fn s5_decompositions(
    basis: &[F2mElement],
    x_r: &F2mElement,
    b: &F2mElement,
    irr: &IrreduciblePoly,
    opts: SatEnumOptions,
) -> Option<DecompositionSet> {
    let tpl = s5_template(basis, b, irr)?;
    let mut enc = encode_from_template(
        &tpl,
        to_word(x_r),
        S5Options {
            encoding: opts.encoding,
            break_symmetry: opts.break_symmetry,
        },
    );
    let mut found: BTreeSet<Vec<u64>> = BTreeSet::new();
    let mut counters = DecompositionCounters::default();
    let complete = enumerate_s5(&tpl, &mut enc, x_r, b, irr, opts, &mut counters, |codes| {
        let mut t = codes.to_vec();
        t.sort_unstable();
        found.insert(t);
        false
    });
    Some(DecompositionSet {
        decompositions: found.into_iter().collect(),
        complete,
        counters,
    })
}

/// The shared model loop of the specialised path.  `accept` sees each
/// chain-compatible model's codes and returns `true` to stop early.
/// Returns `true` when the search ended in a refutation.
#[allow(clippy::too_many_arguments)]
fn enumerate_s5(
    tpl: &S5Template,
    enc: &mut S5SatEncoding,
    x_r: &F2mElement,
    b: &F2mElement,
    irr: &IrreduciblePoly,
    opts: SatEnumOptions,
    counters: &mut DecompositionCounters,
    mut accept: impl FnMut([u64; 4]) -> bool,
) -> bool {
    enc.solver.conflict_budget = opts.conflict_budget;
    counters.vars = u64::from(enc.solver.n_vars());
    counters.clauses = enc.solver.n_original_clauses() as u64;
    counters.xor_rows = enc.solver.n_xors() as u64;
    let n = tpl.gf.n;
    let finish = |enc: &S5SatEncoding, counters: &mut DecompositionCounters, done: bool| {
        counters.conflicts = enc.solver.conflicts();
        counters.decisions = enc.solver.stats.decisions;
        counters.propagations = enc.solver.stats.propagations;
        done
    };
    if enc.trivially_unsat {
        return finish(enc, counters, true);
    }
    loop {
        counters.solver_calls += 1;
        match enc.solver.solve() {
            SolveResult::Unsat => return finish(enc, counters, true),
            SolveResult::Unknown => return finish(enc, counters, false),
            SolveResult::Sat => {}
        }
        counters.models += 1;
        let codes = enc.decode_codes();
        let words = codes.map(|c| tpl.element(c));
        if tpl.s5_at(words, to_word(x_r)) != 0 {
            counters.spurious += 1;
            return finish(enc, counters, false);
        }
        let xs = words.map(|w| from_word(w, n));
        if chain_compatible([&xs[0], &xs[1], &xs[2], &xs[3]], x_r, b, irr) {
            if accept(codes) {
                return finish(enc, counters, false);
            }
        } else {
            counters.rejected_by_chain += 1;
        }
        if counters.models as usize >= opts.max_models {
            return finish(enc, counters, false);
        }
        let clause = enc.blocking_clause();
        enc.solver.reset_search();
        enc.solver.add_clause(clause);
    }
}

/// **Every decomposition through the generic chained system** (any
/// `m ≥ 2`): the models of
/// [`crate::cryptanalysis::polynomial_reuse::build_decomposition_system_reusing`]'s
/// system under [`encode_boolean_system_with`], projected onto the
/// summand codes and sorted.  `None` when the system does not fit the
/// 64-variable layout.
pub fn generic_chain_decompositions(
    basis: &[F2mElement],
    x_r: &F2mElement,
    b: &F2mElement,
    m: usize,
    irr: &IrreduciblePoly,
    opts: SatEnumOptions,
) -> Option<DecompositionSet> {
    let n = irr.degree;
    if n == 0 || n > 64 {
        return None;
    }
    let st = FieldStructure::new(n, irr);
    let sys = build_decomposition_system_reusing(basis, x_r, b, m, &st)?;
    let l = basis.len();
    let mut enc = encode_boolean_system_with(sys.n_vars, &sys.equations, &[], opts.encoding);
    enc.solver.conflict_budget = opts.conflict_budget;
    let mut counters = DecompositionCounters {
        vars: u64::from(enc.solver.n_vars()),
        clauses: enc.solver.n_original_clauses() as u64,
        xor_rows: enc.solver.n_xors() as u64,
        ..Default::default()
    };
    let mut found: BTreeSet<Vec<u64>> = BTreeSet::new();
    let mut complete = enc.trivially_unsat;
    if !enc.trivially_unsat {
        loop {
            counters.solver_calls += 1;
            match enc.solver.solve() {
                SolveResult::Unsat => {
                    complete = true;
                    break;
                }
                SolveResult::Unknown => break,
                SolveResult::Sat => {}
            }
            counters.models += 1;
            let root = enc.model_assignment();
            if !sys.equations.iter().all(|e| e.eval(root) == 0) {
                counters.spurious += 1;
                break;
            }
            let mut codes: Vec<u64> = (0..m)
                .map(|i| (root >> (i * l)) & ((1u64 << l) - 1))
                .collect();
            codes.sort_unstable();
            found.insert(codes);
            if counters.models as usize >= opts.max_models {
                break;
            }
            let clause: Vec<Lit> = (0..m * l)
                .map(|i| {
                    let lit = (i + 1) as Lit;
                    if (root >> i) & 1 == 1 {
                        -lit
                    } else {
                        lit
                    }
                })
                .collect();
            enc.solver.reset_search();
            enc.solver.add_clause(clause);
        }
    }
    counters.conflicts = enc.solver.conflicts();
    counters.decisions = enc.solver.stats.decisions;
    counters.propagations = enc.solver.stats.propagations;
    Some(DecompositionSet {
        decompositions: found.into_iter().collect(),
        complete,
        counters,
    })
}

/// **Dispatch**: every `m`-summand decomposition of `x_r` by SAT, through
/// the specialised encoder for `m = 4` where it applies and the generic
/// chain otherwise (see [`SatPath`]).  Both paths return the same list
/// where both complete (module docs).  `None` when the requested path
/// cannot encode the instance.
pub fn sat_decompositions(
    basis: &[F2mElement],
    x_r: &F2mElement,
    b: &F2mElement,
    m: usize,
    irr: &IrreduciblePoly,
    opts: SatEnumOptions,
) -> Option<(DecompositionSet, SatPathTaken)> {
    let specialised = || {
        if m != 4 {
            return None;
        }
        s5_decompositions(basis, x_r, b, irr, opts).map(|d| (d, SatPathTaken::SymmetrisedS5))
    };
    let generic = || {
        generic_chain_decompositions(basis, x_r, b, m, irr, opts)
            .map(|d| (d, SatPathTaken::GenericChain))
    };
    match opts.path {
        SatPath::Specialised => specialised(),
        SatPath::Generic => generic(),
        SatPath::Auto => specialised().or_else(generic),
    }
}

/// `Tr_{F_{2ⁿ}/F₂}(x)`.
fn trace_bit(x: &F2mElement, irr: &IrreduciblePoly) -> bool {
    let mut acc = x.clone();
    let mut t = x.clone();
    for _ in 1..irr.degree {
        acc = acc.square(irr);
        t = t.add(&acc);
    }
    !t.is_zero()
}

/// **The Koblitz driver's SAT oracle with `m = 4` dispatch.**  For
/// `m = 4` on a linear-subspace factor base (and without
/// `restrict_to_factor_base`), under [`SatPath::Auto`] or
/// [`SatPath::Specialised`], models of the symmetrised `S₅` encoder are
/// lifted one at a time by the same group check as
/// [`sat_decompose_with`] until one lifts or the search refutes; the
/// trace row of `options.trace_constraint` is added on the summand bits.
/// Everything else — other `m`, other factor bases, [`SatPath::Generic`],
/// or an instance the specialised encoder cannot take — goes to
/// [`sat_decompose_with`] unchanged.  Both answer "is there a
/// decomposition" identically where both complete; which decomposition
/// is returned first may differ.
#[allow(clippy::too_many_arguments)]
pub fn sat_decompose_dispatch(
    kc: &KoblitzCurve,
    fb: &FrobeniusFactorBase,
    index_of: &HashMap<(BigUint, BigUint), usize>,
    st: &FieldStructure,
    target: &BinaryPoint,
    m: usize,
    max_models: usize,
    macaulay_degree: Option<u32>,
    options: SatDecompositionOptions,
    path: SatPath,
) -> (Option<Vec<usize>>, SatDecompositionStats) {
    let generic = || {
        sat_decompose_with(
            kc,
            fb,
            index_of,
            st,
            target,
            m,
            max_models,
            macaulay_degree,
            options,
        )
    };
    let eligible = m == 4
        && path != SatPath::Generic
        && fb.domain == FactorBaseDomain::LinearSubspace
        && !options.restrict_to_factor_base;
    let BinaryPoint::Affine { x: x_r, .. } = target else {
        return generic();
    };
    let tpl = if eligible {
        s5_template(&fb.subspace_basis, &kc.curve.b, &kc.curve.irreducible)
    } else {
        None
    };
    let Some(tpl) = tpl else {
        return generic();
    };
    let irr = &kc.curve.irreducible;
    let mut enc = encode_from_template(
        &tpl,
        to_word(x_r),
        S5Options {
            encoding: options.encoding,
            break_symmetry: true,
        },
    );
    if options.trace_constraint && !enc.trivially_unsat {
        // Σ Tr(xᵢ) = Tr(x_R) + (m+1)·Tr(a) for rational points, m = 4.
        let rhs = trace_bit(x_r, irr) ^ trace_bit(&kc.curve.a, irr);
        let ell = tpl.l;
        let vars: Vec<u32> = (0..4)
            .flat_map(|i| {
                fb.subspace_basis
                    .iter()
                    .enumerate()
                    .filter(|(_, v)| trace_bit(v, irr))
                    .map(move |(k, _)| (1 + i * ell + k) as u32)
            })
            .collect();
        let ok = if vars.is_empty() {
            !rhs
        } else {
            enc.solver.add_xor(&vars, rhs)
        };
        if !ok {
            enc.trivially_unsat = true;
        }
    }
    let mut stats = SatDecompositionStats::default();
    let mut counters = DecompositionCounters::default();
    let mut lifted = None;
    let opts = SatEnumOptions {
        path,
        encoding: options.encoding,
        break_symmetry: true,
        conflict_budget: options.conflict_budget,
        max_models,
    };
    let n = tpl.gf.n;
    let refuted = enumerate_s5(
        &tpl,
        &mut enc,
        x_r,
        &kc.curve.b,
        irr,
        opts,
        &mut counters,
        |codes| {
            let xs: Vec<F2mElement> = codes
                .iter()
                .map(|&c| from_word(tpl.element(c), n))
                .collect();
            lifted = lift_candidate(kc, fb, index_of, &xs, target);
            lifted.is_some()
        },
    );
    stats.solver_calls = counters.solver_calls as usize;
    stats.models = counters.models as usize;
    stats.spurious = counters.spurious as usize;
    stats.conflicts = counters.conflicts;
    stats.refuted = refuted;
    stats.exhausted = !refuted && lifted.is_none();
    (lifted, stats)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::binary_ecc::curve::point_add;
    use crate::binary_ecc::BinaryCurve;
    use crate::cryptanalysis::binary_semaev::solve_artin_schreier;
    use rand::{rngs::StdRng, Rng, SeedableRng};

    /// Irreducible polynomials (low terms) by degree, all standard
    /// primitive trinomials/pentanomials.
    fn irr(n: u32) -> IrreduciblePoly {
        let low: Vec<u32> = match n {
            3 => vec![0, 1],
            4 => vec![0, 1],
            5 => vec![0, 2],
            6 => vec![0, 1],
            7 => vec![0, 1],
            8 => vec![0, 2, 3, 4],
            9 => vec![0, 4],
            10 => vec![0, 3],
            11 => vec![0, 2],
            12 => vec![0, 1, 4, 6],
            13 => vec![0, 1, 3, 4],
            14 => vec![0, 1, 6, 10],
            15 => vec![0, 1],
            16 => vec![0, 1, 3, 12],
            17 => vec![0, 3],
            19 => vec![0, 1, 2, 5],
            31 => vec![0, 3],
            _ => panic!("no irreducible tabulated for n = {n}"),
        };
        IrreduciblePoly {
            degree: n,
            low_terms: low,
        }
    }

    /// The tabulated polynomials really are irreducible: `z^{2^n} = z`
    /// and `z^{2^{n/p}} ≠ z` for every prime `p | n` (Rabin).
    #[test]
    fn tabulated_polynomials_are_irreducible() {
        for n in [
            3u32, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 31,
        ] {
            let f = irr(n);
            let z = F2mElement::z(n);
            let frob = |k: u32| z.square_k_times(k, &f);
            assert_eq!(frob(n), z, "n = {n}");
            for p in [2u32, 3, 5, 7, 11, 13, 17, 19, 31] {
                if n % p == 0 && n != 1 {
                    assert_ne!(frob(n / p), z, "n = {n}, p = {p}");
                }
            }
        }
    }

    fn rand_elem(rng: &mut StdRng, n: u32) -> F2mElement {
        from_word(rng.gen::<u64>() & ((1u64 << n) - 1), n)
    }

    // ── An independent S₅: the Sylvester determinant ────────────────

    type Poly = Vec<F2mElement>;

    fn padd(a: &Poly, b: &Poly, n: u32) -> Poly {
        (0..a.len().max(b.len()))
            .map(|i| {
                let z = F2mElement::zero(n);
                a.get(i).unwrap_or(&z).add(b.get(i).unwrap_or(&z))
            })
            .collect()
    }

    fn pmul(a: &Poly, b: &Poly, f: &IrreduciblePoly) -> Poly {
        let n = f.degree;
        let mut out = vec![F2mElement::zero(n); a.len() + b.len() - 1];
        for (i, x) in a.iter().enumerate() {
            for (j, y) in b.iter().enumerate() {
                out[i + j] = out[i + j].add(&x.mul(y, f));
            }
        }
        out
    }

    fn det(mut m: Vec<Vec<F2mElement>>, f: &IrreduciblePoly) -> F2mElement {
        let n = f.degree;
        let size = m.len();
        let mut d = F2mElement::one(n);
        for c in 0..size {
            let Some(p) = (c..size).find(|&r| !m[r][c].is_zero()) else {
                return F2mElement::zero(n);
            };
            m.swap(c, p);
            let inv = m[c][c].flt_inverse(f).unwrap();
            d = d.mul(&m[c][c], f);
            for r in c + 1..size {
                if m[r][c].is_zero() {
                    continue;
                }
                let k = m[r][c].mul(&inv, f);
                for j in c..size {
                    let t = k.mul(&m[c][j], f);
                    m[r][j] = m[r][j].add(&t);
                }
            }
        }
        d
    }

    /// `Res_X(S₃(x₁,x₂,X), S₄(x₃,x₄,x_R,X))` as a 6 × 6 Sylvester
    /// determinant, with `S₄` in `X` built as the quadratic resultant in
    /// `Y` of `S₃(x₃,x₄,Y)` and `S₃(x_R,X,Y)`.
    fn s5_by_sylvester(
        x: [&F2mElement; 4],
        x_r: &F2mElement,
        b: &F2mElement,
        f: &IrreduciblePoly,
    ) -> F2mElement {
        let n = f.degree;
        let zero = F2mElement::zero(n);
        let c = |e: &F2mElement| vec![e.clone()];
        let (a1, b1, c1) = binary_semaev_s3_in_x3(x[2], x[3], b, f);
        let xr2 = x_r.square(f);
        // S₃(x_R, X, Y) = (X² + x_R²) Y² + x_R X Y + (x_R² X² + b).
        let a2: Poly = vec![xr2.clone(), zero.clone(), F2mElement::one(n)];
        let b2: Poly = vec![zero.clone(), x_r.clone()];
        let c2: Poly = vec![b.clone(), zero.clone(), xr2.clone()];
        let t = padd(&pmul(&c(&a1), &c2, f), &pmul(&a2, &c(&c1), f), n);
        let u = padd(&pmul(&c(&a1), &b2, f), &pmul(&a2, &c(&b1), f), n);
        let v = padd(&pmul(&c(&b1), &c2, f), &pmul(&b2, &c(&c1), f), n);
        let mut q = padd(&pmul(&t, &t, f), &pmul(&u, &v, f), n);
        q.resize(5, zero.clone());
        let (pa, pb, pc) = binary_semaev_s3_in_x3(x[0], x[1], b, f);
        let p = [pa, pb, pc];
        let mut m = vec![vec![zero.clone(); 6]; 6];
        for r in 0..4 {
            for (k, e) in p.iter().enumerate() {
                m[r][r + k] = e.clone();
            }
        }
        for r in 0..2 {
            for k in 0..5 {
                m[4 + r][r + k] = q[4 - k].clone();
            }
        }
        det(m, f)
    }

    #[test]
    fn table_is_the_resultant() {
        let mut rng = StdRng::seed_from_u64(0x55);
        for n in [5u32, 8, 13, 31] {
            let f = irr(n);
            for _ in 0..40 {
                let x: Vec<F2mElement> = (0..4).map(|_| rand_elem(&mut rng, n)).collect();
                let x_r = rand_elem(&mut rng, n);
                let mut b = rand_elem(&mut rng, n);
                if b.is_zero() {
                    b = F2mElement::one(n);
                }
                let xs = [&x[0], &x[1], &x[2], &x[3]];
                let want = s5_by_sylvester(xs, &x_r, &b, &f);
                assert_eq!(semaev_s5_eval(xs, &x_r, &b, &f), want, "n = {n}");
                // And the word-arithmetic evaluator agrees.
                let basis: Vec<F2mElement> = (0..n).map(|k| from_word(1 << k, n)).collect();
                let tpl = S5Template::build(&basis[..1], &b, &f).unwrap();
                assert_eq!(tpl.s5_at(xs.map(to_word), to_word(&x_r)), to_word(&want));
            }
        }
    }

    // ── Curves and planted sums ─────────────────────────────────────

    fn curve(n: u32, a: &F2mElement, b: &F2mElement) -> BinaryCurve {
        BinaryCurve {
            m: n,
            irreducible: irr(n),
            a: a.clone(),
            b: b.clone(),
            generator: BinaryPoint::Infinity,
            order: BigUint::from(0u8),
            cofactor: BigUint::from(1u8),
        }
    }

    /// A point with abscissa `x`, if one exists over `F_{2ⁿ}`.
    fn lift(c: &BinaryCurve, x: &F2mElement) -> Option<BinaryPoint> {
        let f = &c.irreducible;
        let n = c.m;
        if x.is_zero() {
            // y² = b.
            let y = c.b.square_k_times(n - 1, f);
            return Some(BinaryPoint::Affine { x: x.clone(), y });
        }
        // y = x·t, t² + t = x + a + b/x².
        let x2inv = x.square(f).flt_inverse(f)?;
        let rhs = x.add(&c.a).add(&c.b.mul(&x2inv, f));
        let t = solve_artin_schreier(&rhs, n, f)?;
        Some(BinaryPoint::Affine {
            x: x.clone(),
            y: x.mul(&t, f),
        })
    }

    fn x_of(p: &BinaryPoint) -> Option<F2mElement> {
        match p {
            BinaryPoint::Affine { x, .. } => Some(x.clone()),
            BinaryPoint::Infinity => None,
        }
    }

    #[test]
    fn s5_vanishes_on_planted_four_point_sums() {
        let mut rng = StdRng::seed_from_u64(0x5e5);
        let mut checked = 0;
        for n in [7u32, 11, 13, 17, 31] {
            let f = irr(n);
            for _ in 0..30 {
                let a = rand_elem(&mut rng, n);
                let mut b = rand_elem(&mut rng, n);
                if b.is_zero() {
                    b = F2mElement::one(n);
                }
                let c = curve(n, &a, &b);
                let mut pts = Vec::new();
                while pts.len() < 4 {
                    if let Some(p) = lift(&c, &rand_elem(&mut rng, n)) {
                        assert!(c.is_on_curve(&p));
                        pts.push(p);
                    }
                }
                let r = pts
                    .iter()
                    .fold(BinaryPoint::Infinity, |acc, p| point_add(&c, &acc, p));
                let Some(x_r) = x_of(&r) else { continue };
                let xs: Vec<F2mElement> = pts.iter().map(|p| x_of(p).unwrap()).collect();
                let v = semaev_s5_eval([&xs[0], &xs[1], &xs[2], &xs[3]], &x_r, &b, &f);
                assert!(v.is_zero(), "n = {n}");
                assert!(chain_compatible(
                    [&xs[0], &xs[1], &xs[2], &xs[3]],
                    &x_r,
                    &b,
                    &f
                ));
                checked += 1;
            }
        }
        assert!(checked > 100);
    }

    // ── Instances for the differential tests ────────────────────────

    struct Instance {
        n: u32,
        f: IrreduciblePoly,
        basis: Vec<F2mElement>,
        b: F2mElement,
        x_r: F2mElement,
        label: String,
    }

    fn random_basis(rng: &mut StdRng, n: u32, l: usize, polynomial: bool) -> Vec<F2mElement> {
        if polynomial {
            return (0..l).map(|k| from_word(1 << k, n)).collect();
        }
        loop {
            let words: Vec<u64> = (0..l)
                .map(|_| rng.gen::<u64>() & ((1u64 << n) - 1))
                .collect();
            if Span::new().extend_rank(&words) == l {
                return words.into_iter().map(|w| from_word(w, n)).collect();
            }
        }
    }

    fn span_element(basis: &[F2mElement], code: u64, n: u32) -> F2mElement {
        basis
            .iter()
            .enumerate()
            .filter(|(k, _)| (code >> k) & 1 == 1)
            .fold(F2mElement::zero(n), |acc, (_, v)| acc.add(v))
    }

    /// Random, edge and planted targets over random fields, bases and
    /// curves, all small enough for the generic chain (`4ℓ + 2n ≤ 64`).
    fn instances(seed: u64, count: usize, ns: &[u32], max_l: usize) -> Vec<Instance> {
        let mut rng = StdRng::seed_from_u64(seed);
        let mut out = Vec::new();
        for i in 0..count {
            let n = ns[i % ns.len()];
            let f = irr(n);
            let l = rng.gen_range(1..=max_l.min(n as usize));
            let basis = random_basis(&mut rng, n, l, i % 3 == 0);
            let a = rand_elem(&mut rng, n);
            let b = if i % 4 == 0 {
                F2mElement::one(n)
            } else {
                loop {
                    let b = rand_elem(&mut rng, n);
                    if !b.is_zero() {
                        break b;
                    }
                }
            };
            let c = curve(n, &a, &b);
            let kind = i % 6;
            let x_r = match kind {
                0 => F2mElement::zero(n),
                1 => F2mElement::one(n),
                2 => span_element(&basis, rng.gen_range(0..1u64 << l), n),
                3 | 4 => {
                    // Planted: four lifted factor-base points, repeats allowed.
                    let mut pts = Vec::new();
                    let mut tries = 0;
                    while pts.len() < 4 && tries < 200 {
                        tries += 1;
                        let code = rng.gen_range(0..1u64 << l);
                        if let Some(p) = lift(&c, &span_element(&basis, code, n)) {
                            pts.push(p.clone());
                            if kind == 4 && pts.len() < 4 {
                                pts.push(p); // a repeated summand
                            }
                        }
                    }
                    pts.truncate(4);
                    let r = pts
                        .iter()
                        .fold(BinaryPoint::Infinity, |acc, p| point_add(&c, &acc, p));
                    x_of(&r).unwrap_or_else(|| rand_elem(&mut rng, n))
                }
                _ => rand_elem(&mut rng, n),
            };
            out.push(Instance {
                n,
                f,
                basis,
                b,
                x_r,
                label: format!("#{i} n={n} l={l} kind={kind}"),
            });
        }
        out
    }

    fn enum_opts(encoding: XorEncoding, break_symmetry: bool) -> SatEnumOptions {
        SatEnumOptions {
            encoding,
            break_symmetry,
            ..Default::default()
        }
    }

    fn specialised(inst: &Instance, o: SatEnumOptions) -> DecompositionSet {
        s5_decompositions(&inst.basis, &inst.x_r, &inst.b, &inst.f, o).expect("applies")
    }

    fn generic(inst: &Instance, o: SatEnumOptions) -> DecompositionSet {
        generic_chain_decompositions(&inst.basis, &inst.x_r, &inst.b, 4, &inst.f, o).expect("fits")
    }

    /// **The differential pin**: on every instance both paths complete and
    /// return the same sorted list, under both XOR encodings and with
    /// symmetry breaking on and off.
    #[test]
    fn specialised_matches_generic_chain_on_random_and_edge_instances() {
        let (mut empty, mut nonempty, mut rejected) = (0, 0, 0u64);
        for inst in instances(0x5a7_0001, 120, &[3, 4, 5, 6, 7, 8, 9], 3) {
            let reference = generic(&inst, enum_opts(XorEncoding::Native, false));
            assert!(
                reference.complete && reference.counters.spurious == 0,
                "{}",
                inst.label
            );
            for (encoding, sym) in [
                (XorEncoding::Native, true),
                (XorEncoding::Native, false),
                (XorEncoding::Cnf, true),
            ] {
                let got = specialised(&inst, enum_opts(encoding, sym));
                assert!(got.complete, "{} {encoding:?} {sym}", inst.label);
                assert_eq!(got.counters.spurious, 0, "{}", inst.label);
                assert_eq!(
                    got.decompositions, reference.decompositions,
                    "{} {encoding:?} sym={sym}",
                    inst.label
                );
                rejected += got.counters.rejected_by_chain;
            }
            if reference.decompositions.is_empty() {
                empty += 1;
            } else {
                nonempty += 1;
            }
        }
        // Both verdicts, and the chain filter, were exercised.
        assert!(
            empty >= 10 && nonempty >= 10,
            "empty {empty}, nonempty {nonempty}"
        );
        assert!(rejected > 0, "no instance exercised the F_2^n chain filter");
    }

    /// The generic CNF control agrees too (fewer instances: it is slow).
    #[test]
    fn specialised_matches_generic_cnf_control() {
        for inst in instances(0x5a7_0002, 24, &[4, 5, 6, 7], 2) {
            let reference = generic(&inst, enum_opts(XorEncoding::Cnf, false));
            assert!(reference.complete, "{}", inst.label);
            let got = specialised(&inst, enum_opts(XorEncoding::Native, true));
            assert_eq!(
                got.decompositions, reference.decompositions,
                "{}",
                inst.label
            );
        }
    }

    /// **Brute force**, independent of both SAT encodings: every sorted
    /// code tuple, `S₅` evaluated by the table over `F_{2ⁿ}`.  The
    /// specialised path's raw models (before the chain filter) are exactly
    /// the zeros of `S₅`, and its output exactly the chain-compatible ones.
    #[test]
    fn specialised_matches_brute_force_over_every_tuple() {
        for inst in instances(0x5a7_0003, 60, &[3, 4, 5, 6, 7, 8, 11, 13], 3) {
            let l = inst.basis.len();
            let codes: Vec<u64> = (0..1u64 << l).collect();
            let (mut zeros, mut chained) = (0u64, Vec::new());
            for (i0, &c0) in codes.iter().enumerate() {
                for (i1, &c1) in codes.iter().enumerate().skip(i0) {
                    for (i2, &c2) in codes.iter().enumerate().skip(i1) {
                        for &c3 in &codes[i2..] {
                            let t = [c0, c1, c2, c3];
                            let x = t.map(|c| span_element(&inst.basis, c, inst.n));
                            let xs = [&x[0], &x[1], &x[2], &x[3]];
                            if semaev_s5_eval(xs, &inst.x_r, &inst.b, &inst.f).is_zero() {
                                zeros += 1;
                                if chain_compatible(xs, &inst.x_r, &inst.b, &inst.f) {
                                    chained.push(t.to_vec());
                                }
                            }
                        }
                    }
                }
            }
            for encoding in [XorEncoding::Native, XorEncoding::Cnf] {
                let got = specialised(&inst, enum_opts(encoding, true));
                assert!(got.complete, "{}", inst.label);
                assert_eq!(got.counters.models, zeros, "{} {encoding:?}", inst.label);
                assert_eq!(
                    got.counters.models - got.counters.rejected_by_chain,
                    chained.len() as u64,
                    "{}",
                    inst.label
                );
                assert_eq!(got.decompositions, chained, "{} {encoding:?}", inst.label);
            }
        }
    }

    /// Larger fields than the generic chain's 64-variable layout admits at
    /// the same `ℓ` are still encoded, and planted decompositions found.
    #[test]
    fn specialised_finds_planted_decompositions_beyond_the_generic_cap() {
        let mut rng = StdRng::seed_from_u64(0x5a7_0004);
        // 4ℓ + 2n > 64 for both: the generic layout refuses them.
        for (n, l, polynomial) in [(31u32, 3usize, true), (31, 4, false)] {
            let f = irr(n);
            let basis = random_basis(&mut rng, n, l, polynomial);
            let b = loop {
                let b = rand_elem(&mut rng, n);
                if !b.is_zero() {
                    break b;
                }
            };
            let c = curve(n, &F2mElement::zero(n), &b);
            let mut codes = Vec::new();
            let mut pts = Vec::new();
            while pts.len() < 4 {
                let code = rng.gen_range(0..1u64 << l);
                if let Some(p) = lift(&c, &span_element(&basis, code, n)) {
                    pts.push(p);
                    codes.push(code);
                }
            }
            let r = pts
                .iter()
                .fold(BinaryPoint::Infinity, |acc, p| point_add(&c, &acc, p));
            let x_r = x_of(&r).unwrap();
            assert!(generic_chain_decompositions(
                &basis,
                &x_r,
                &b,
                4,
                &f,
                enum_opts(XorEncoding::Native, false)
            )
            .is_none());
            let got = s5_decompositions(&basis, &x_r, &b, &f, SatEnumOptions::default()).unwrap();
            assert!(got.complete);
            codes.sort_unstable();
            assert!(got.decompositions.contains(&codes), "n = {n}, l = {l}");
        }
    }

    #[test]
    fn dispatch_takes_the_specialised_path_for_m4_and_the_chain_otherwise() {
        let inst = &instances(0x5a7_0005, 6, &[6], 2)[3];
        let auto = sat_decompositions(
            &inst.basis,
            &inst.x_r,
            &inst.b,
            4,
            &inst.f,
            SatEnumOptions::default(),
        )
        .unwrap();
        assert_eq!(auto.1, SatPathTaken::SymmetrisedS5);
        let forced = SatEnumOptions {
            path: SatPath::Generic,
            ..Default::default()
        };
        let gen = sat_decompositions(&inst.basis, &inst.x_r, &inst.b, 4, &inst.f, forced).unwrap();
        assert_eq!(gen.1, SatPathTaken::GenericChain);
        assert_eq!(auto.0.decompositions, gen.0.decompositions);
        for m in [2usize, 3] {
            let r = sat_decompositions(
                &inst.basis,
                &inst.x_r,
                &inst.b,
                m,
                &inst.f,
                SatEnumOptions::default(),
            )
            .unwrap();
            assert_eq!(r.1, SatPathTaken::GenericChain);
            let only = SatEnumOptions {
                path: SatPath::Specialised,
                ..Default::default()
            };
            assert!(
                sat_decompositions(&inst.basis, &inst.x_r, &inst.b, m, &inst.f, only).is_none()
            );
        }
        // A dependent basis is refused by the specialised path, and Auto
        // falls back to the chain.
        let mut dependent = inst.basis.clone();
        dependent.push(inst.basis[0].clone());
        assert!(S5Template::build(&dependent, &inst.b, &inst.f).is_none());
        let r = sat_decompositions(
            &dependent,
            &inst.x_r,
            &inst.b,
            4,
            &inst.f,
            SatEnumOptions::default(),
        )
        .unwrap();
        assert_eq!(r.1, SatPathTaken::GenericChain);
    }

    #[test]
    fn budgets_make_the_result_incomplete_never_wrong() {
        for inst in instances(0x5a7_0006, 12, &[7, 8], 3) {
            let full = specialised(&inst, enum_opts(XorEncoding::Native, true));
            let capped = specialised(
                &inst,
                SatEnumOptions {
                    max_models: 1,
                    ..Default::default()
                },
            );
            if full.counters.models > 1 {
                assert!(!capped.complete, "{}", inst.label);
            }
            assert!(capped
                .decompositions
                .iter()
                .all(|d| full.decompositions.contains(d)));
            let tight = specialised(
                &inst,
                SatEnumOptions {
                    conflict_budget: 1,
                    ..Default::default()
                },
            );
            assert!(tight.complete || tight.counters.conflicts >= 1);
            assert!(tight
                .decompositions
                .iter()
                .all(|d| full.decompositions.contains(d)));
        }
    }

    #[test]
    fn template_layout_matches_the_polynomial_basis_count() {
        // Polynomial basis: e_i has i(ℓ−1)+1 coordinates while that is ≤ n.
        let n = 13;
        let f = irr(n);
        for l in 1..=4usize {
            let basis: Vec<F2mElement> = (0..l).map(|k| from_word(1 << k, n)).collect();
            let tpl = S5Template::build(&basis, &F2mElement::one(n), &f).unwrap();
            let want: [usize; 4] = std::array::from_fn(|i| ((i + 1) * (l - 1) + 1).min(n as usize));
            assert_eq!(tpl.e_dims(), want, "l = {l}");
            assert_eq!(tpl.ell(), l);
            assert!(tpl.n_semaev_monomials() > 0);
        }
        assert!(S5Template::build(&[], &F2mElement::one(n), &f).is_none());
        let basis = [F2mElement::one(n)];
        assert!(S5Template::build(&basis, &F2mElement::zero(n), &f).is_none());
    }

    /// The Koblitz driver hook agrees with `sat_decompose_with` on whether a
    /// decomposition exists, and what it returns is one.
    #[test]
    fn koblitz_dispatch_agrees_with_the_generic_oracle() {
        use crate::cryptanalysis::koblitz_index_calculus::build_frobenius_factor_base;
        let mut checked = 0;
        let mut found = 0;
        for (a, n) in [(0u8, 7u32), (1, 7), (0, 9), (1, 9)] {
            let Some(kc) = KoblitzCurve::new(a, n) else {
                continue;
            };
            for idx in 0..4 {
                let Some(fb) = build_frobenius_factor_base(&kc, idx) else {
                    continue;
                };
                let l = fb.subspace_basis.len();
                if fb.domain != FactorBaseDomain::LinearSubspace
                    || 4 * l + 2 * n as usize > 64
                    || !fb.m_can_decompose(&kc, 4)
                {
                    continue;
                }
                let st = FieldStructure::new(kc.n, &kc.curve.irreducible);
                let index_of = fb.index_map();
                let mut rng = StdRng::seed_from_u64(u64::from(n) * 31 + idx as u64);
                for t in 0..4 {
                    let target = if t < 2 {
                        (0..4).fold(BinaryPoint::Infinity, |acc, _| {
                            kc.add(&acc, &fb.points[rng.gen_range(0..fb.points.len())])
                        })
                    } else {
                        kc.mul(kc.generator(), &BigUint::from(rng.gen_range(1u64..1000)))
                    };
                    if target == BinaryPoint::Infinity {
                        continue;
                    }
                    let options = SatDecompositionOptions::default();
                    let (g, gs) = sat_decompose_with(
                        &kc,
                        &fb,
                        &index_of,
                        &st,
                        &target,
                        4,
                        usize::MAX,
                        None,
                        options,
                    );
                    let (s, ss) = sat_decompose_dispatch(
                        &kc,
                        &fb,
                        &index_of,
                        &st,
                        &target,
                        4,
                        usize::MAX,
                        None,
                        options,
                        SatPath::Auto,
                    );
                    assert!(gs.refuted || g.is_some());
                    assert!(ss.refuted || s.is_some());
                    assert_eq!(g.is_some(), s.is_some(), "a={a} n={n} idx={idx} t={t}");
                    if let Some(idxs) = &s {
                        let sum = idxs
                            .iter()
                            .fold(BinaryPoint::Infinity, |acc, &i| kc.add(&acc, &fb.points[i]));
                        assert_eq!(sum, target);
                        found += 1;
                    }
                    checked += 1;
                }
            }
        }
        assert!(
            checked >= 6 && found >= 1,
            "checked {checked}, found {found}"
        );
    }
}
