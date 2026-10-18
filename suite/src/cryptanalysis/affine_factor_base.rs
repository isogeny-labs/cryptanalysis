//! # Affine (shifted) factor bases `V + c` for binary index calculus.
//!
//! Every binary-field index-calculus path in this crate takes its factor
//! base to be the points whose abscissa lies in an `F₂`-**subspace** `V`
//! of `F_{2ⁿ}`.  This module adds the **cosets** `V + c = {c + v : v ∈ V}`
//! and gives each specialised decomposition oracle a version that works
//! on the coset directly, rather than on the linear hull `V ⊕ ⟨c⟩` with
//! a membership filter afterwards.
//!
//! ## Why a coset
//!
//! - **It avoids the 2-torsion abscissa.**  `0 ∈ V` always, and `x = 0`
//!   carries the rational 2-torsion point; for `c ∉ V` the coset misses
//!   it.
//! - **Frobenius invariance.**  For an invariant `V` the coset is
//!   invariant iff `π(c) + c ∈ V` (`π` the `q`-power Frobenius).  The
//!   solutions form a subspace `W ⊇ V`, and `W / V` names the invariant
//!   cosets; for a Koblitz curve (`q = 2`) `dim W/V ≤ 1`, so there is at
//!   most one invariant shifted copy of each invariant subspace, and for
//!   a subfield curve over `F_{2^k}` up to `k`.  [`frobenius_invariant_shifts`]
//!   computes them.
//! - **Same size, different points.**  `|V + c| = |V|`, so a coset is a
//!   second factor base of the same size and the same descent shape; the
//!   linear hull would double the base and add one unknown per summand.
//!
//! ## The specialised oracles
//!
//! | `m` | route | work per target | where |
//! |---|---|---|---|
//! | 2 | [`AffineRoute::S3Solve`] | `2^ℓ` quadratic solves | `S₃(x₁, x₂, x_R)` is quadratic in `x₂`: one inversion and one Artin–Schreier solve per `x₁ ∈ V + c` |
//! | 3 | [`AffineRoute::S4PairsAndSolve`] | `2^ℓ(2^ℓ+1)/2` pairs | [`AffineSubspaceOracle`]: `S₄` quartic in `x₃`, coset roots from `gcd(f, L_V mod f + L_V(c))` |
//! | any | [`AffineRoute::Algebraic`] | one Boolean solve | Weil descent with `x_i = c + Σ_j t_{ij} v_j`: `ℓ` unknowns per summand, the generic chain of `S₃` links |
//! | any | [`AffineRoute::Sat`] | CDCL model enumeration | the same system, native XOR rows, a trace row with the shift folded in, and the exact coordinate domain |
//!
//! Point-based oracles need no change: [`crate::cryptanalysis::koblitz_index_calculus::PairSumTable`]
//! and enumeration index the materialised points, so an affine base built
//! by [`build_affine_frobenius_factor_base`] works with them as it is
//! (pinned by the differential tests below).
//!
//! ## The generic path, kept and tested
//!
//! [`build_affine_frobenius_factor_base`] returns an ordinary
//! [`FrobeniusFactorBase`] whose `subspace_basis` is the linear hull
//! `V ⊕ ⟨c⟩` and whose domain is
//! [`FactorBaseDomain::SubspaceSubset`]: every existing entry point
//! (`groebner_decompose`, `sat_decompose`, `crossbred_decompose`, the
//! WDSat oracle, `enumerate_decompose`, the pair table, the IC driver)
//! accepts it unchanged, descends over the hull with `ℓ + 1` unknowns per
//! summand, and filters by membership (`lift_candidate` for the algebraic
//! routes, the domain trie for SAT).  [`AffineRoute::GenericAlgebraic`] is
//! that hull descent in all-solutions form.  [`affine_koblitz_decompose`]
//! is the explicit dispatch: [`AffineDispatch::Specialised`] or
//! [`AffineDispatch::Generic`] with any existing strategy as fallback.
//!
//! ## What "the same decompositions" means
//!
//! A decomposition is a non-decreasing index tuple `i_1 ≤ … ≤ i_m` into
//! the base's point list with `Σ P_{i_k} = R`.  Every route returns the
//! **set** of them, sorted lexicographically ([`AffineDecompositions`]);
//! the canonical single answer is the lexicographically smallest, which
//! is what [`crate::cryptanalysis::koblitz_index_calculus::enumerate_decompose`]
//! returns.  The reference is [`AffineRoute::Enumerate`], an exhaustive
//! search over the explicit point set.
//!
//! - `S3Solve`, `S4PairsAndSolve` and `Enumerate` return exactly the
//!   reference set: `S_{m+1}` vanishes iff some choice of signs sums to
//!   `O` (Semaev), and every root is lifted over every sign choice.
//! - `Algebraic`, `Sat` and `GenericAlgebraic` use the **chain** of
//!   `S₃` links, whose intermediate unknowns are affine abscissae: they
//!   find exactly the reference tuples that have an ordering whose
//!   partial sums `P_{σ1} + … + P_{σj}`, `2 ≤ j ≤ m − 1`, are all
//!   affine ([`chain_representable`]).  For `m = 2` that is every tuple;
//!   for `m = 3` over a coset with `c ∉ V` it is every tuple too (a
//!   non-representable triple needs three equal 2-torsion summands, and
//!   `x = 0 ∉ V + c`).  A budget exhausted mid-search clears
//!   [`AffineStats::complete`].
//! - `R = O` is not an affine target: every route returns no
//!   decomposition for it.
//!
//! Single-word fields only (`n ≤ 62`, the [`FastCurve`] range).
//!
//! ## Measured (perfbench `spec_affine` kernels, one thread)
//!
//! Engineering measurements of the oracles on fixed toy instances
//! (2026-10-10, one host; time per pass over the same targets, median of
//! five paired rounds; Ir from callgrind):
//!
//! | instance | route | ms / pass | Ir / pass |
//! |---|---|--:|--:|
//! | `K_1/2^15`, `ℓ = 8`, `m = 2`, 8 targets | `S3Solve` | 0.57 | 3.5 M |
//! | | `Algebraic` (affine, MatrixF4 d3) | 59.8 | 640 M |
//! | | `GenericAlgebraic` (hull) | 162.8 | 1 765 M |
//! | | `Sat` (affine) | 198.0 | 975 M |
//! | | `Enumerate` | 0.44 | 2.7 M |
//! | `K_1/2^7`, `ℓ = 3`, `m = 3`, 8 targets | `S4PairsAndSolve` | 0.165 | 1.4 M |
//! | | `Algebraic` (affine chain) | 34.7 | 301 M |
//! | | `GenericAlgebraic` (hull chain) | 220.3 | 1 911 M |
//! | | `Enumerate` | 0.118 | 0.83 M |
//! | random `2^18` curve, `ℓ = 6`, `m = 3`, 16 targets | `S4PairsAndSolve` | 9.5 | 110 M |
//! | | `Enumerate` | 5.4 | 34 M |
//!
//! Against the generic hull descent the affine descent is 2.7× (`m = 2`)
//! and 6.3× (`m = 3`) faster in wall time on the same targets, and the
//! solve-per-summand oracles are two to three orders of magnitude faster
//! still.  **Point enumeration remains faster than every algebraic route
//! at these sizes** (0.6–0.75× the time of `S3Solve`/`S4PairsAndSolve`):
//! for `m ≤ 3` both do `Θ(2^{(m−1)ℓ})` work and a single-word group
//! addition is cheaper than a quadratic or quartic root extraction.  No
//! claim about relation-collection cost or asymptotics follows.

use std::collections::{BTreeSet, HashMap};

use crate::binary_ecc::{BinaryCurve, BinaryPoint, F2mElement};
use crate::cryptanalysis::koblitz_fast::{FastCurve, FastPoint};
use crate::cryptanalysis::koblitz_groebner::{
    build_decomposition_system, chain_order_interleaved, invert_permutation, permute_mask,
    permute_poly, solve_boolean_system_filtered, split_rule_default, sym_semaev_s3,
    DecompositionSystem, FieldStructure, SolveOptions, SolverEngine, SymElement, MAX_VARS,
};
use crate::cryptanalysis::koblitz_index_calculus::{
    build_explicit_frobenius_orbit_factor_base, crossbred_decompose, enumerate_decompose,
    groebner_decompose, sat_decompose, DecompositionStrategy, FactorBaseDomain,
    FrobeniusFactorBase, KoblitzCurve, PairSumTable,
};
use crate::cryptanalysis::pq_groebner_f2::{F2BoolMono, F2BoolPoly};
use crate::cryptanalysis::sat::{SolveResult, Solver};
use crate::cryptanalysis::semaev_decomp::{AffineSubspaceOracle, Gf2};
use crate::cryptanalysis::semaev_sat::{encode_boolean_system_with, XorEncoding};

// ── Cosets of F₂-subspaces, one word per element ───────────────────

/// A coset `V + c` of an `F₂`-subspace of `F_{2ⁿ}`, `n ≤ 63`, elements as
/// words in the polynomial basis.
///
/// The shift is stored **canonically**: reduced against an echelon form
/// of `V`, so it has no bit at any pivot position and two shifts name
/// the same coset iff their canonical forms are equal.  Element `w`
/// (a coordinate word, bit `j` selecting `basis[j]`) is
/// `shift ⊕ Σ_j w_j·basis[j]`; that is the order of [`Self::elements`].
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct AffineSubspace {
    basis: Vec<u64>,
    shift: u64,
    /// Rows with distinct highest bits, highest first.
    echelon: Vec<u64>,
}

impl AffineSubspace {
    /// `span(basis) + shift`; `None` when the basis is dependent or longer
    /// than 30 vectors (the coset is materialised by the oracles).
    pub fn new(basis: &[u64], shift: u64) -> Option<Self> {
        if basis.len() > 30 {
            return None;
        }
        let mut echelon: Vec<u64> = Vec::with_capacity(basis.len());
        for &v in basis {
            let r = reduce_by(&echelon, v);
            if r == 0 {
                return None;
            }
            echelon.push(r);
            echelon.sort_unstable_by_key(|&row| std::cmp::Reverse(64 - row.leading_zeros()));
        }
        let shift = reduce_by(&echelon, shift);
        Some(Self {
            basis: basis.to_vec(),
            shift,
            echelon,
        })
    }

    /// Dimension `ℓ` of `V`.
    pub fn dim(&self) -> u32 {
        self.basis.len() as u32
    }

    /// The basis of `V`, as given.
    pub fn basis(&self) -> &[u64] {
        &self.basis
    }

    /// The canonical shift; zero iff the coset is `V` itself.
    pub fn shift(&self) -> u64 {
        self.shift
    }

    /// Whether the coset is the subspace (`c ∈ V`).
    pub fn is_linear(&self) -> bool {
        self.shift == 0
    }

    /// The canonical representative of `x + V`.
    pub fn reduce(&self, x: u64) -> u64 {
        reduce_by(&self.echelon, x)
    }

    /// Whether `x ∈ V + c`.
    pub fn contains(&self, x: u64) -> bool {
        self.reduce(x) == self.shift
    }

    /// Element number `w` (coordinate word).
    pub fn element(&self, w: u64) -> u64 {
        self.basis
            .iter()
            .enumerate()
            .filter(|(j, _)| (w >> j) & 1 == 1)
            .fold(self.shift, |acc, (_, &v)| acc ^ v)
    }

    /// All `2^ℓ` elements, by coordinate word.
    pub fn elements(&self) -> Vec<u64> {
        (0..1u64 << self.basis.len())
            .map(|w| self.element(w))
            .collect()
    }

    /// A basis of the linear hull `V ⊕ ⟨c⟩`: `basis` followed by the
    /// canonical shift.  `None` for a linear coset.
    pub fn hull_basis(&self) -> Option<Vec<u64>> {
        (!self.is_linear()).then(|| {
            let mut b = self.basis.clone();
            b.push(self.shift);
            b
        })
    }
}

fn reduce_by(echelon: &[u64], mut x: u64) -> u64 {
    for &row in echelon {
        let top = 63 - row.leading_zeros();
        if (x >> top) & 1 == 1 {
            x ^= row;
        }
    }
    x
}

// ── Artin–Schreier on words ─────────────────────────────────────────

/// Solves `z² + z = a` in `F_{2ⁿ}` for any `n ≤ 63` (odd or even) by a
/// precomputed elimination of the `F₂`-linear map `z ↦ z² + z`: `O(n)`
/// word operations per solve.
#[derive(Clone, Debug)]
struct ArtinSchreier {
    /// `(image, preimage)` with distinct image top bits, highest first.
    rows: Vec<(u64, u64)>,
}

impl ArtinSchreier {
    fn new(gf: &Gf2) -> Self {
        let mut rows: Vec<(u64, u64)> = Vec::new();
        for i in 0..gf.n {
            let e = 1u64 << i;
            let (mut img, mut pre) = (gf.sqr(e) ^ e, e);
            for &(ri, rp) in &rows {
                if (img >> (63 - ri.leading_zeros())) & 1 == 1 {
                    img ^= ri;
                    pre ^= rp;
                }
            }
            if img != 0 {
                rows.push((img, pre));
                rows.sort_unstable_by_key(|&(ri, _)| std::cmp::Reverse(64 - ri.leading_zeros()));
            }
        }
        Self { rows }
    }

    /// One root `z` of `z² + z = a` (the other is `z + 1`), or `None`
    /// when `Tr(a) = 1`.
    fn solve(&self, a: u64) -> Option<u64> {
        let (mut r, mut z) = (a, 0u64);
        for &(ri, rp) in &self.rows {
            if (r >> (63 - ri.leading_zeros())) & 1 == 1 {
                r ^= ri;
                z ^= rp;
            }
        }
        (r == 0).then_some(z)
    }
}

/// Absolute trace of `x`, as a bit.
fn trace_bit(x: u64, gf: &Gf2) -> bool {
    let (mut t, mut p) = (0u64, x);
    for _ in 0..gf.n {
        t ^= p;
        p = gf.sqr(p);
    }
    t & 1 == 1
}

// ── Points over a coset ─────────────────────────────────────────────

/// The rational points of `curve` whose abscissa lies in `coset`, in
/// coset element order; for each abscissa `x ≠ 0` the two points
/// `(x, y)` and `(x, x + y)` with the smaller `y` first, for `x = 0` the
/// single point `(0, √b)`.  `None` beyond the single-word range.
pub fn affine_points(curve: &BinaryCurve, coset: &AffineSubspace) -> Option<Vec<BinaryPoint>> {
    let fc = FastCurve::new(curve)?;
    let gf = &fc.field;
    let solver = ArtinSchreier::new(gf);
    let mut out = Vec::new();
    for x in coset.elements() {
        for p in points_over(&fc, &solver, x) {
            out.push(fc.lower(p));
        }
    }
    Some(out)
}

fn points_over(fc: &FastCurve, solver: &ArtinSchreier, x: u64) -> Vec<FastPoint> {
    let gf = &fc.field;
    if x == 0 {
        return vec![FastPoint::affine(0, gf.sqr_k(fc.b, fc.n - 1))];
    }
    // y = x·u, u² + u = x + a + b/x².
    let inv = gf.inv(x);
    let rhs = x ^ fc.a ^ gf.mul(fc.b, gf.sqr(inv));
    match solver.solve(rhs) {
        None => Vec::new(),
        Some(u) => {
            let y0 = gf.mul(x, u);
            let y1 = y0 ^ x;
            vec![
                FastPoint::affine(x, y0.min(y1)),
                FastPoint::affine(x, y0.max(y1)),
            ]
        }
    }
}

// ── Frobenius-invariant cosets for Koblitz / subfield curves ────────

/// The shifts `c ∉ V` for which `V + c` is invariant under the curve's
/// `q`-power Frobenius, one canonical representative per coset, sorted.
///
/// Empty when `V` itself is not invariant or `n > 62`.  The solutions of
/// `π(c) + c ∈ V` form a subspace `W ⊇ V` (the map is `F₂`-linear and
/// kills `V` modulo `V` because `V` is invariant); the result lists the
/// `2^{dim W/V} − 1` non-trivial cosets of `V` in `W`.
pub fn frobenius_invariant_shifts(kc: &KoblitzCurve, basis: &[F2mElement]) -> Vec<F2mElement> {
    let Some(fc) = FastCurve::new(&kc.curve) else {
        return Vec::new();
    };
    let gf = &fc.field;
    let words: Vec<u64> = basis.iter().map(|e| gf.from_element(e)).collect();
    let Some(v) = AffineSubspace::new(&words, 0) else {
        return Vec::new();
    };
    let frob = |x: u64| gf.sqr_k(x, kc.k);
    if words.iter().any(|&w| !v.contains(frob(w))) {
        return Vec::new();
    }
    // Kernel of c ↦ reduce(π(c) + c) on F_2^n, by elimination tracking
    // the combination of unit vectors.
    let mut rows: Vec<(u64, u64)> = Vec::new();
    let mut kernel: Vec<u64> = Vec::new();
    for i in 0..kc.n {
        let e = 1u64 << i;
        let (mut img, mut pre) = (v.reduce(frob(e) ^ e), e);
        for &(ri, rp) in &rows {
            if (img >> (63 - ri.leading_zeros())) & 1 == 1 {
                img ^= ri;
                pre ^= rp;
            }
        }
        if img == 0 {
            kernel.push(pre);
        } else {
            rows.push((img, pre));
            rows.sort_unstable_by_key(|&(ri, _)| std::cmp::Reverse(64 - ri.leading_zeros()));
        }
    }
    // Representatives of W / V: kernel vectors independent modulo V.
    let mut reps: Vec<u64> = Vec::new();
    let mut ext = words.clone();
    for k in kernel {
        let mut trial = ext.clone();
        trial.push(k);
        if AffineSubspace::new(&trial, 0).is_some() {
            ext = trial;
            reps.push(k);
        }
    }
    let mut shifts: BTreeSet<u64> = BTreeSet::new();
    for w in 1..(1u64 << reps.len()) {
        let c = reps
            .iter()
            .enumerate()
            .filter(|(j, _)| (w >> j) & 1 == 1)
            .fold(0u64, |a, (_, &r)| a ^ r);
        shifts.insert(v.reduce(c));
    }
    shifts.into_iter().map(|c| gf.to_element(c)).collect()
}

/// A Frobenius-invariant affine factor base: the generic-path base and
/// the coset it was built from.
#[derive(Clone, Debug)]
pub struct AffineFrobeniusFactorBase {
    /// An ordinary factor base over the points with `x ∈ V + c`, whose
    /// `subspace_basis` is the hull `V ⊕ ⟨c⟩` (`ell = ℓ + 1`) and whose
    /// domain is [`FactorBaseDomain::SubspaceSubset`], so every existing
    /// oracle takes it as it is.  Points are in increasing abscissa
    /// order, as [`build_explicit_frobenius_orbit_factor_base`] lists them.
    pub fb: FrobeniusFactorBase,
    /// The coset itself.
    pub coset: AffineSubspace,
}

/// **Build the affine factor base** `{P : x(P) ∈ span(basis) + shift}`
/// on a Koblitz or subfield curve.
///
/// `None` unless the field is single-word (`n ≤ 62`), the basis is
/// independent, `shift ∉ V`, the coset is Frobenius invariant (see
/// [`frobenius_invariant_shifts`]) and it carries at least one point.
pub fn build_affine_frobenius_factor_base(
    kc: &KoblitzCurve,
    basis: &[F2mElement],
    shift: &F2mElement,
) -> Option<AffineFrobeniusFactorBase> {
    let fc = FastCurve::new(&kc.curve)?;
    let gf = &fc.field;
    let words: Vec<u64> = basis.iter().map(|e| gf.from_element(e)).collect();
    let coset = AffineSubspace::new(&words, gf.from_element(shift))?;
    if coset.is_linear() {
        return None;
    }
    let frob = |x: u64| gf.sqr_k(x, kc.k);
    if words.iter().any(|&w| coset.reduce(frob(w)) != 0) || !coset.contains(frob(coset.shift())) {
        return None;
    }
    let elements: Vec<F2mElement> = coset.elements().iter().map(|&x| gf.to_element(x)).collect();
    let mut fb = build_explicit_frobenius_orbit_factor_base(kc, &elements)?;
    if fb.subspace.len() != elements.len() || fb.points.is_empty() {
        return None;
    }
    fb.subspace_basis = coset
        .hull_basis()?
        .iter()
        .map(|&w| gf.to_element(w))
        .collect();
    fb.ell = coset.dim() + 1;
    fb.domain = FactorBaseDomain::SubspaceSubset {
        retained_orbits: fb.signed_orbits.len(),
    };
    Some(AffineFrobeniusFactorBase { fb, coset })
}

// ── The affine descent ──────────────────────────────────────────────

/// **The decomposition system over a coset**: [`build_decomposition_system`]
/// with each summand `x_i = c + Σ_t v_{iℓ+t}·basis[t]`.
///
/// Same layout (`m·ℓ` summand unknowns, then `(m − 2)·n` chain
/// intermediates), same equations up to the constant shift, `ℓ`
/// unknowns per summand where the hull would need `ℓ + 1`.  Decode a
/// root with [`affine_summand_word`].  `None` for `m < 2` or past
/// [`MAX_VARS`].
pub fn build_affine_decomposition_system(
    basis: &[F2mElement],
    shift: &F2mElement,
    x_r: &F2mElement,
    b: &F2mElement,
    m: usize,
    st: &FieldStructure,
) -> Option<DecompositionSystem> {
    if m < 2 {
        return None;
    }
    let ell = basis.len();
    let n = st.n;
    let n_vars = m * ell + m.saturating_sub(2) * n as usize;
    if n_vars > MAX_VARS {
        return None;
    }
    let c = SymElement::constant(shift, n, n_vars);
    let summands: Vec<SymElement> = (0..m)
        .map(|i| SymElement::from_subspace_vars(basis, i * ell, n, n_vars).add(&c))
        .collect();
    let target = SymElement::constant(x_r, n, n_vars);
    let mut equations = Vec::new();
    if m == 2 {
        equations.extend(sym_semaev_s3(&summands[0], &summands[1], &target, b, st));
    } else {
        let inter: Vec<SymElement> = (0..m - 2)
            .map(|i| SymElement::from_free_vars(m * ell + i * n as usize, n, n_vars))
            .collect();
        equations.extend(sym_semaev_s3(&summands[0], &summands[1], &inter[0], b, st));
        for i in 0..m - 3 {
            equations.extend(sym_semaev_s3(
                &inter[i],
                &summands[i + 2],
                &inter[i + 1],
                b,
                st,
            ));
        }
        equations.extend(sym_semaev_s3(
            &inter[m - 3],
            &summands[m - 1],
            &target,
            b,
            st,
        ));
    }
    Some(DecompositionSystem {
        equations,
        n_vars,
        ell,
        m,
    })
}

/// The abscissa a root of [`build_affine_decomposition_system`] gives to
/// summand `i`, as a word.
pub fn affine_summand_word(coset: &AffineSubspace, ell: usize, root: u64, i: usize) -> u64 {
    coset.element((root >> (i * ell)) & ((1u64 << ell) - 1))
}

// ── Routes, results, counters ───────────────────────────────────────

/// Which oracle answers "which `m`-tuples of base points sum to `R`?".
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum AffineRoute {
    /// The specialised route for `m`: [`Self::Enumerate`] for `m = 1`,
    /// [`Self::S3Solve`] for `m = 2`,
    /// [`Self::S4PairsAndSolve`] for `m = 3`, otherwise
    /// [`Self::Algebraic`] with the default engine when the system fits
    /// [`MAX_VARS`], else [`Self::Enumerate`].
    Auto,
    /// `m = 2`: solve `S₃(x₁, x₂, x_R) = 0` for `x₂` per coset `x₁`.
    S3Solve,
    /// `m = 3`: [`AffineSubspaceOracle`] over the coset.
    S4PairsAndSolve,
    /// The affine descent, all roots, by the Boolean solver.
    Algebraic {
        engine: SolverEngine,
        node_budget: usize,
    },
    /// The affine descent, all models, by CDCL with native XOR rows.
    Sat { conflict_budget: u64 },
    /// **Generic**: the hull descent `V ⊕ ⟨c⟩` (`ℓ + 1` unknowns per
    /// summand), every root lifted and filtered by membership — what the
    /// existing Gröbner path does with an affine base, in all-solutions
    /// form.
    GenericAlgebraic {
        engine: SolverEngine,
        node_budget: usize,
    },
    /// **Reference**: exhaustive search over the explicit point set.
    Enumerate,
}

/// Native counters of one decomposition call.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct AffineStats {
    /// `S₃` quadratics solved (`S3Solve`).
    pub quadratics: u64,
    /// `S₄` pairs processed (`S4PairsAndSolve`).
    pub pairs: u64,
    /// Abscissa tuples handed to the lift (roots, models, witnesses).
    pub candidates: u64,
    /// Group additions spent lifting and enumerating.
    pub additions: u64,
    /// Algebraic reductions (`Algebraic`, `GenericAlgebraic`).
    pub reductions: u64,
    /// SAT conflicts (`Sat`).
    pub conflicts: u64,
    /// `false` when a budget ran out, a system did not fit, or a model
    /// failed verification: the set may then be partial.
    pub complete: bool,
}

/// Every decomposition a route found, sorted, and its counters.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct AffineDecompositions {
    /// Non-decreasing index tuples, sorted lexicographically, no repeats.
    pub decompositions: Vec<Vec<usize>>,
    pub stats: AffineStats,
}

impl AffineDecompositions {
    /// The canonical decomposition: the lexicographically smallest.
    pub fn first(&self) -> Option<&Vec<usize>> {
        self.decompositions.first()
    }
}

// ── The decomposer ──────────────────────────────────────────────────

/// All the per-base state the affine routes need, built once.
#[derive(Clone, Debug)]
pub struct AffineDecomposer {
    fc: FastCurve,
    coset: AffineSubspace,
    points: Vec<FastPoint>,
    /// Abscissa → indices of its base points (one or two).
    by_x: HashMap<u64, Vec<usize>>,
    /// Packed point → index.
    by_point: HashMap<u64, usize>,
    /// Coordinate words of coset elements that carry a base point.
    domain_codes: Vec<u64>,
    solver: ArtinSchreier,
    s4: AffineSubspaceOracle,
    st: FieldStructure,
    basis_el: Vec<F2mElement>,
    shift_el: F2mElement,
    b_el: F2mElement,
}

impl AffineDecomposer {
    /// The decomposer for the base `points` over `coset` on `curve`.
    ///
    /// `None` beyond `n = 62`, for `b = 0`, or unless every point is
    /// affine, distinct, on the curve and has its abscissa in the coset.
    /// The base may be any such list (all points over the coset, a
    /// Frobenius-closed one, or a subset); indices refer to it.
    pub fn new(
        curve: &BinaryCurve,
        coset: &AffineSubspace,
        points: &[BinaryPoint],
    ) -> Option<Self> {
        let fc = FastCurve::new(curve)?;
        if fc.b == 0 {
            return None;
        }
        let gf = &fc.field;
        let mut by_x: HashMap<u64, Vec<usize>> = HashMap::new();
        let mut by_point = HashMap::new();
        let mut fast = Vec::with_capacity(points.len());
        for (i, p) in points.iter().enumerate() {
            if *p == BinaryPoint::Infinity {
                return None;
            }
            let q = fc.lift(p);
            if !fc.is_on_curve(q) || !coset.contains(q.x) || by_point.insert(q.pack(), i).is_some()
            {
                return None;
            }
            by_x.entry(q.x).or_default().push(i);
            fast.push(q);
        }
        let mut domain_codes: Vec<u64> = (0..1u64 << coset.dim())
            .filter(|&w| by_x.contains_key(&coset.element(w)))
            .collect();
        domain_codes.sort_unstable();
        let s4 = AffineSubspaceOracle::new(coset.basis(), coset.shift(), fc.b, gf);
        let st = FieldStructure::new(curve.m, &curve.irreducible);
        Some(Self {
            solver: ArtinSchreier::new(gf),
            s4,
            st,
            basis_el: coset.basis().iter().map(|&w| gf.to_element(w)).collect(),
            shift_el: gf.to_element(coset.shift()),
            b_el: curve.b.clone(),
            coset: coset.clone(),
            points: fast,
            by_x,
            by_point,
            domain_codes,
            fc,
        })
    }

    /// The coset.
    pub fn coset(&self) -> &AffineSubspace {
        &self.coset
    }

    /// Number of base points.
    pub fn len(&self) -> usize {
        self.points.len()
    }

    /// Whether the base is empty.
    pub fn is_empty(&self) -> bool {
        self.points.is_empty()
    }

    /// The route [`AffineRoute::Auto`] resolves to for `m`.
    pub fn resolve(&self, m: usize, route: AffineRoute) -> AffineRoute {
        if route != AffineRoute::Auto {
            return route;
        }
        match m {
            1 => AffineRoute::Enumerate,
            2 => AffineRoute::S3Solve,
            3 => AffineRoute::S4PairsAndSolve,
            _ if m * self.coset.dim() as usize + m.saturating_sub(2) * self.fc.n as usize
                <= MAX_VARS =>
            {
                AffineRoute::Algebraic {
                    engine: SolverEngine::default(),
                    node_budget: usize::MAX,
                }
            }
            _ => AffineRoute::Enumerate,
        }
    }

    /// **Every decomposition** of `target` into `m ≥ 1` base points by
    /// `route` (see the module documentation for which tuples each route
    /// is complete for).  A route that does not apply to `m` (`S3Solve`
    /// off `m = 2`, `S4PairsAndSolve` off `m = 3`, an algebraic route at
    /// `m < 2` or past [`MAX_VARS`]) returns nothing with
    /// `complete = false`.
    pub fn decompositions(
        &self,
        target: &BinaryPoint,
        m: usize,
        route: AffineRoute,
    ) -> AffineDecompositions {
        let mut found: BTreeSet<Vec<usize>> = BTreeSet::new();
        let mut stats = AffineStats {
            complete: true,
            ..AffineStats::default()
        };
        let t = self.fc.lift(target);
        if !t.infinity && m >= 1 {
            match self.resolve(m, route) {
                AffineRoute::Auto => unreachable!("resolved above"),
                AffineRoute::Enumerate => self.enumerate(t, m, &mut found, &mut stats),
                AffineRoute::S3Solve if m == 2 => self.s3(t, &mut found, &mut stats),
                AffineRoute::S4PairsAndSolve if m == 3 => self.s4(t, &mut found, &mut stats),
                AffineRoute::Algebraic {
                    engine,
                    node_budget,
                } if m >= 2 => {
                    self.algebraic(t, m, engine, node_budget, false, &mut found, &mut stats)
                }
                AffineRoute::GenericAlgebraic {
                    engine,
                    node_budget,
                } if m >= 2 => {
                    self.algebraic(t, m, engine, node_budget, true, &mut found, &mut stats)
                }
                AffineRoute::Sat { conflict_budget } if m >= 2 => {
                    self.sat(t, m, conflict_budget, &mut found, &mut stats)
                }
                _ => stats.complete = false,
            }
        }
        AffineDecompositions {
            decompositions: found.into_iter().collect(),
            stats,
        }
    }

    /// The canonical (lexicographically smallest) decomposition by
    /// `route`, or `None`.
    pub fn decompose(
        &self,
        target: &BinaryPoint,
        m: usize,
        route: AffineRoute,
    ) -> Option<Vec<usize>> {
        self.decompositions(target, m, route)
            .decompositions
            .into_iter()
            .next()
    }

    /// Add every sign choice of base points over the abscissae `xs` that
    /// sums to `t`.
    fn lift(
        &self,
        xs: &[u64],
        t: FastPoint,
        found: &mut BTreeSet<Vec<usize>>,
        stats: &mut AffineStats,
    ) {
        stats.candidates += 1;
        let mut chosen = Vec::with_capacity(xs.len());
        self.lift_walk(xs, FastPoint::INFINITY, t, &mut chosen, found, stats);
    }

    fn lift_walk(
        &self,
        xs: &[u64],
        acc: FastPoint,
        t: FastPoint,
        chosen: &mut Vec<usize>,
        found: &mut BTreeSet<Vec<usize>>,
        stats: &mut AffineStats,
    ) {
        let Some((&x, rest)) = xs.split_first() else {
            if acc == t {
                let mut tuple = chosen.clone();
                tuple.sort_unstable();
                found.insert(tuple);
            }
            return;
        };
        let Some(idxs) = self.by_x.get(&x) else {
            return;
        };
        for &i in idxs {
            chosen.push(i);
            stats.additions += 1;
            let next = self.fc.add(acc, self.points[i]);
            self.lift_walk(rest, next, t, chosen, found, stats);
            chosen.pop();
        }
    }

    /// Reference: non-decreasing tuples over the explicit points, the
    /// last summand by lookup.
    fn enumerate(
        &self,
        t: FastPoint,
        m: usize,
        found: &mut BTreeSet<Vec<usize>>,
        stats: &mut AffineStats,
    ) {
        let mut chosen = Vec::with_capacity(m);
        self.enumerate_walk(t, m, 0, &mut chosen, found, stats);
    }

    fn enumerate_walk(
        &self,
        rest: FastPoint,
        m: usize,
        start: usize,
        chosen: &mut Vec<usize>,
        found: &mut BTreeSet<Vec<usize>>,
        stats: &mut AffineStats,
    ) {
        if m == 1 {
            if let Some(&i) = (!rest.infinity)
                .then(|| self.by_point.get(&rest.pack()))
                .flatten()
            {
                if i >= start {
                    let mut tuple = chosen.clone();
                    tuple.push(i);
                    found.insert(tuple);
                }
            }
            return;
        }
        for i in start..self.points.len() {
            stats.additions += 1;
            let next = self.fc.add(rest, self.fc.neg(self.points[i]));
            chosen.push(i);
            self.enumerate_walk(next, m - 1, i, chosen, found, stats);
            chosen.pop();
        }
    }

    /// `m = 2`.  `S₃(x₁, x₂, x_R) = A x₂² + B x₂ + C` with
    /// `A = x₁² + x_R²`, `B = x₁x_R`, `C = x₁²x_R² + b`.
    fn s3(&self, t: FastPoint, found: &mut BTreeSet<Vec<usize>>, stats: &mut AffineStats) {
        let gf = &self.fc.field;
        let xr = t.x;
        let xr2 = gf.sqr(xr);
        let n = self.fc.n;
        let mut roots: Vec<u64> = Vec::with_capacity(2);
        for w in 0..1u64 << self.coset.dim() {
            let x1 = self.coset.element(w);
            if !self.by_x.contains_key(&x1) {
                continue;
            }
            stats.quadratics += 1;
            let x12 = gf.sqr(x1);
            let a = x12 ^ xr2;
            let bq = gf.mul(x1, xr);
            let c = gf.mul(x12, xr2) ^ self.fc.b;
            roots.clear();
            match (a == 0, bq == 0) {
                // 0·x₂ + C with C = b (x₁ = x_R = 0): no root.
                (true, true) => {}
                (true, false) => roots.push(gf.mul(c, gf.inv(bq))),
                (false, true) => roots.push(gf.sqr_k(gf.mul(c, gf.inv(a)), n - 1)),
                (false, false) => {
                    // x₂ = (B/A)·z with z² + z = AC/B².
                    let inv_b = gf.inv(bq);
                    let rhs = gf.mul(gf.mul(a, c), gf.sqr(inv_b));
                    if let Some(z) = self.solver.solve(rhs) {
                        let scale = gf.mul(bq, gf.inv(a));
                        roots.push(gf.mul(scale, z));
                        roots.push(gf.mul(scale, z ^ 1));
                    }
                }
            }
            for &x2 in &roots {
                if self.by_x.contains_key(&x2) {
                    self.lift(&[x1, x2], t, found, stats);
                }
            }
        }
    }

    /// `m = 3`: every coset triple from the pairs-and-solve oracle.
    fn s4(&self, t: FastPoint, found: &mut BTreeSet<Vec<usize>>, stats: &mut AffineStats) {
        let (triples, pairs) = self.s4.decompose_all(t.x, &self.fc.field);
        stats.pairs += pairs;
        for xs in triples {
            if xs.iter().all(|x| self.by_x.contains_key(x)) {
                self.lift(&xs, t, found, stats);
            }
        }
    }

    /// The affine (or, with `hull`, the generic hull) descent, every root.
    #[allow(clippy::too_many_arguments)]
    fn algebraic(
        &self,
        t: FastPoint,
        m: usize,
        engine: SolverEngine,
        node_budget: usize,
        hull: bool,
        found: &mut BTreeSet<Vec<usize>>,
        stats: &mut AffineStats,
    ) {
        let gf = &self.fc.field;
        let x_r = gf.to_element(t.x);
        let hull_basis: Vec<F2mElement>;
        let sys = if hull {
            // A linear coset is its own hull.
            let words = self
                .coset
                .hull_basis()
                .unwrap_or_else(|| self.coset.basis().to_vec());
            hull_basis = words.iter().map(|&w| gf.to_element(w)).collect();
            build_decomposition_system(&hull_basis, &x_r, &self.b_el, m, &self.st)
        } else {
            hull_basis = Vec::new();
            build_affine_decomposition_system(
                &self.basis_el,
                &self.shift_el,
                &x_r,
                &self.b_el,
                m,
                &self.st,
            )
        };
        let Some(sys) = sys else {
            stats.complete = false;
            return;
        };
        let opts = SolveOptions {
            engine,
            max_solutions: usize::MAX,
            node_budget,
            split_rule: split_rule_default(),
        };
        // As `groebner_decompose`: a chain is solved in its interleaved
        // order and the roots renamed back.
        let order = (m >= 3 && chain_order_interleaved(opts.resolve().split_rule))
            .then(|| sys.interleaved_order(self.fc.n));
        let reordered: Vec<F2BoolPoly>;
        let equations = match &order {
            Some(perm) => {
                reordered = sys
                    .equations
                    .iter()
                    .map(|e| permute_poly(e, perm))
                    .collect();
                &reordered
            }
            None => &sys.equations,
        };
        let back = order.as_deref().map(invert_permutation);
        let n = self.fc.n;
        let (_, solve) = solve_boolean_system_filtered(equations, sys.n_vars, &opts, |root| {
            let root = back.as_deref().map_or(root, |inv| permute_mask(root, inv));
            let xs: Vec<u64> = (0..m)
                .map(|i| {
                    if hull {
                        gf.from_element(&sys.summand_x(&hull_basis, root, i, n))
                    } else {
                        affine_summand_word(&self.coset, sys.ell, root, i)
                    }
                })
                .collect();
            if xs.iter().all(|x| self.by_x.contains_key(x)) {
                self.lift(&xs, t, found, stats);
            }
            false
        });
        stats.reductions += solve.reductions as u64;
        if solve.exhausted {
            stats.complete = false;
        }
    }

    /// The affine descent by CDCL: native XOR rows, the trace row with
    /// the shift folded in, the coordinate domain, every model.
    fn sat(
        &self,
        t: FastPoint,
        m: usize,
        conflict_budget: u64,
        found: &mut BTreeSet<Vec<usize>>,
        stats: &mut AffineStats,
    ) {
        let gf = &self.fc.field;
        let x_r = gf.to_element(t.x);
        let Some(sys) = build_affine_decomposition_system(
            &self.basis_el,
            &self.shift_el,
            &x_r,
            &self.b_el,
            m,
            &self.st,
        ) else {
            stats.complete = false;
            return;
        };
        let ell = sys.ell;
        let mut equations = sys.equations.clone();
        // δ(P) = Tr(x(P) + a) is a homomorphism to F₂ (Kosters–Yeo), so
        // Σ Tr(x_i) = Tr(x_R) + (m + 1)·Tr(a); with x_i = c + Σ t v the
        // left side is m·Tr(c) + Σ t_{ij} Tr(v_j).
        let rhs = trace_bit(t.x, gf)
            ^ (m.is_multiple_of(2) && trace_bit(self.fc.a, gf))
            ^ (m % 2 == 1 && trace_bit(self.coset.shift(), gf));
        let mut terms = Vec::new();
        for (j, &v) in self.coset.basis().iter().enumerate() {
            if trace_bit(v, gf) {
                for i in 0..m {
                    terms.push(F2BoolMono::var((i * ell + j) as u32));
                }
            }
        }
        if rhs {
            terms.push(F2BoolMono::one());
        }
        equations.push(F2BoolPoly::from_monos(terms, sys.n_vars));
        let mut enc = encode_boolean_system_with(sys.n_vars, &equations, &[], XorEncoding::Native);
        enc.solver.conflict_budget = conflict_budget;
        for i in 0..m {
            add_coordinate_domain(&mut enc.solver, i * ell, ell, &self.domain_codes);
        }
        loop {
            if enc.trivially_unsat {
                return;
            }
            let outcome = enc.solver.solve();
            stats.conflicts = enc.solver.conflicts();
            match outcome {
                SolveResult::Unsat => return,
                SolveResult::Unknown => {
                    stats.complete = false;
                    return;
                }
                SolveResult::Sat => {
                    let root = enc.model_assignment();
                    if !sys.equations.iter().all(|e| e.eval(root) == 0) {
                        // Fail closed.
                        stats.complete = false;
                        return;
                    }
                    let xs: Vec<u64> = (0..m)
                        .map(|i| affine_summand_word(&self.coset, ell, root, i))
                        .collect();
                    self.lift(&xs, t, found, stats);
                    enc.solver.reset_search();
                    let clause: Vec<i32> = (0..sys.n_vars)
                        .map(|i| {
                            let lit = (i + 1) as i32;
                            if (root >> i) & 1 == 1 {
                                -lit
                            } else {
                                lit
                            }
                        })
                        .collect();
                    enc.solver.add_clause(clause);
                }
            }
        }
    }
}

/// Forbid every `ell`-bit code at solver variables `offset + 1 ..` that is
/// not in the sorted list `codes`, by the missing branches of a binary
/// trie (as the Koblitz SAT oracle constrains its domain).
fn add_coordinate_domain(solver: &mut Solver, offset: usize, ell: usize, codes: &[u64]) {
    fn visit(solver: &mut Solver, offset: usize, bit: usize, codes: &[u64], prefix: &mut Vec<i32>) {
        if codes.is_empty() {
            solver.add_clause(prefix.clone());
            return;
        }
        if bit == 0 {
            return;
        }
        let b = bit - 1;
        let split = codes.partition_point(|code| (code >> b) & 1 == 0);
        let lit = (offset + b + 1) as i32;
        prefix.push(lit);
        visit(solver, offset, b, &codes[..split], prefix);
        *prefix.last_mut().unwrap() = -lit;
        visit(solver, offset, b, &codes[split..], prefix);
        prefix.pop();
    }
    // The trie splits on the top bit first, so the codes must be sorted
    // by their value restricted to `ell` bits — they are words `< 2^ell`.
    visit(solver, offset, ell, codes, &mut Vec::new());
}

/// Whether the tuple of base points has an ordering whose partial sums of
/// lengths `2 ..= m − 1` are all affine — the tuples the chained `S₃`
/// descent can represent (see the module documentation).
pub fn chain_representable(curve: &BinaryCurve, points: &[BinaryPoint], tuple: &[usize]) -> bool {
    let Some(fc) = FastCurve::new(curve) else {
        return false;
    };
    let ps: Vec<FastPoint> = tuple.iter().map(|&i| fc.lift(&points[i])).collect();
    fn go(
        fc: &FastCurve,
        ps: &[FastPoint],
        used: &mut Vec<bool>,
        acc: FastPoint,
        depth: usize,
    ) -> bool {
        let m = ps.len();
        if depth == m {
            return true;
        }
        for i in 0..m {
            if used[i] {
                continue;
            }
            let next = fc.add(acc, ps[i]);
            if depth + 1 >= 2 && depth + 1 < m && next.infinity {
                continue;
            }
            used[i] = true;
            let ok = go(fc, ps, used, next, depth + 1);
            used[i] = false;
            if ok {
                return true;
            }
        }
        false
    }
    go(&fc, &ps, &mut vec![false; ps.len()], FastPoint::INFINITY, 0)
}

// ── Koblitz dispatch ────────────────────────────────────────────────

/// How [`affine_koblitz_decompose`] answers.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum AffineDispatch {
    /// A route of [`AffineDecomposer`]: the canonical decomposition.
    Specialised(AffineRoute),
    /// The existing generic oracle on the hull-based base
    /// ([`AffineFrobeniusFactorBase::fb`]), unchanged: `Groebner`
    /// (default engine, unlimited budget), `Sat`, `Crossbred`,
    /// `Enumerate`, `PairTable` (`2 ≤ m ≤ 5`).  `Wdsat`, `MqFes` and
    /// `WalkSat` are not dispatched here: they answer `None` with
    /// `complete = false`.
    Generic(DecompositionStrategy),
}

/// What [`affine_koblitz_decompose`] found, and whether a `None` is final.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct AffineAnswer {
    /// A decomposition, re-checked in the group by the route that found it.
    pub decomposition: Option<Vec<usize>>,
    /// The search covered its whole space.  With `decomposition = None`
    /// this proves there is no decomposition in the tuples the route
    /// covers (see the module documentation); `false` means `None` is
    /// inconclusive: the strategy is not dispatched here, `m` or the
    /// system is outside its range, a budget ran out, or `R = O`.  A
    /// specialised `Some` with `complete = false` may not be the canonical
    /// (lexicographically smallest) decomposition.
    pub complete: bool,
}

impl AffineAnswer {
    fn inconclusive() -> Self {
        AffineAnswer {
            decomposition: None,
            complete: false,
        }
    }
}

/// **Decompose a target over an affine Koblitz base**, specialised or
/// generic.
///
/// `Specialised` returns the lexicographically smallest decomposition of
/// its route; `Generic` returns what the existing entry point returns on
/// `afb.fb` (for `Enumerate` the same lexicographically smallest tuple;
/// for the algebraic and SAT strategies the first root that lifts, which
/// the differential tests check is a member of the specialised set).
/// [`AffineAnswer::complete`] tells "no decomposition" apart from "not
/// searched to the end".
pub fn affine_koblitz_decompose(
    kc: &KoblitzCurve,
    afb: &AffineFrobeniusFactorBase,
    decomposer: &AffineDecomposer,
    target: &BinaryPoint,
    m: usize,
    dispatch: AffineDispatch,
) -> AffineAnswer {
    if matches!(target, BinaryPoint::Infinity) {
        return AffineAnswer::inconclusive();
    }
    match dispatch {
        AffineDispatch::Specialised(route) => {
            let all = decomposer.decompositions(target, m, route);
            AffineAnswer {
                decomposition: all.decompositions.into_iter().next(),
                complete: all.stats.complete,
            }
        }
        AffineDispatch::Generic(strategy) => {
            let index_of = afb.fb.index_map();
            let st = FieldStructure::new(kc.n, &kc.curve.irreducible);
            // `build_decomposition_system`'s range on the hull base: past
            // it the algebraic and SAT entry points return `None` unsolved.
            let fits =
                m >= 2 && m * afb.fb.subspace_basis.len() + (m - 2) * kc.n as usize <= MAX_VARS;
            let solved = |decomposition: Option<Vec<usize>>, exhausted: bool| AffineAnswer {
                complete: decomposition.is_some() || (fits && !exhausted),
                decomposition,
            };
            match strategy {
                DecompositionStrategy::Enumerate => AffineAnswer {
                    decomposition: enumerate_decompose(kc, &afb.fb, &index_of, target, m),
                    complete: true,
                },
                DecompositionStrategy::Groebner => {
                    let (decomposition, stats) = groebner_decompose(
                        kc,
                        &afb.fb,
                        &index_of,
                        &st,
                        target,
                        m,
                        SolverEngine::default(),
                        usize::MAX,
                    );
                    solved(decomposition, stats.exhausted)
                }
                DecompositionStrategy::Sat => {
                    let (decomposition, stats) =
                        sat_decompose(kc, &afb.fb, &index_of, &st, target, m, usize::MAX, None);
                    // Only a final UNSAT proves there is none.
                    AffineAnswer {
                        complete: decomposition.is_some() || stats.refuted,
                        decomposition,
                    }
                }
                DecompositionStrategy::Crossbred => {
                    let (decomposition, stats) =
                        crossbred_decompose(kc, &afb.fb, &index_of, &st, target, m, None);
                    solved(decomposition, stats.exhausted)
                }
                DecompositionStrategy::PairTable => {
                    if !(2..=5).contains(&m) {
                        return AffineAnswer::inconclusive();
                    }
                    match PairSumTable::build(kc, &afb.fb) {
                        Some(table) => AffineAnswer {
                            decomposition: table.decompose(kc, &afb.fb, target, m),
                            complete: true,
                        },
                        None => AffineAnswer::inconclusive(),
                    }
                }
                DecompositionStrategy::Wdsat
                | DecompositionStrategy::MqFes
                | DecompositionStrategy::WalkSat => AffineAnswer::inconclusive(),
            }
        }
    }
}

/// The decomposer for an affine Koblitz base.
pub fn affine_koblitz_decomposer(
    kc: &KoblitzCurve,
    afb: &AffineFrobeniusFactorBase,
) -> Option<AffineDecomposer> {
    AffineDecomposer::new(&kc.curve, &afb.coset, &afb.fb.points)
}

#[cfg(test)]
mod tests;
