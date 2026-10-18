//! # Five-summand decomposition in the symmetrised frame.
//!
//! [`crate::cryptanalysis::koblitz_symmetrised`] writes the summation
//! polynomials of a Koblitz curve in the Artin–Schreier invariants of the
//! frame `u = 1/(x + 1)` — `w = u² + u` per point and `s = Σ u` — and solves
//! `m = 2, 3` directly and `m = 4` as a chain of three symmetrised `S₃`
//! links.  This module takes the same frame to `m = 5`, where the only
//! production route is the generic `x`-frame chain of four `S₃` links
//! ([`crate::cryptanalysis::koblitz_groebner::build_decomposition_system`],
//! `5ℓ + 3n` unknowns).
//!
//! ## The chains
//!
//! A chain is a list of link arities, each `3` (the symmetrised `S₃`,
//! [`symmetrised_terms`]`(2)`) or `4` (the symmetrised `S₄`,
//! [`symmetrised_terms`]`(3)`).  The first link holds `a₁ − 1` summands and
//! the first intermediate point `Q₁`; a middle link holds `Q_{j−1}`,
//! `a_j − 2` summands and `Q_j`; the last holds `Q_{L−1}`, `a_L − 2`
//! summands and the target `R`.  So
//!
//! ```text
//!   [3, 3, 3, 3]  S3-links: 4 links, 3 intermediates   5(ℓ−1) + 1 + 3n unknowns, degree 3, 4n equations
//!   [4, 4]        S4-pair:  2 links, 1 intermediate    5(ℓ−1) + 1 +  n unknowns, degree 5, 2n equations
//! ```
//!
//! `[3, 3, 3]` is, equation for equation, the `m = 4` chain of
//! [`crate::cryptanalysis::koblitz_symmetrised::build_chained_symmetrised_system`]
//! (a test pins it), and `[4, 4]` is the
//! specialised `m = 5` frame: one intermediate point instead of three, at
//! the price of the degree-5 `w₁w₂w₃w_Q·s` term in the first link.
//!
//! **Parity folding.**  Every summand is `u_i = ε_i + ũ_i` with `ũ_i` in the
//! span of `v_basis[1..]`.  `AS(u + 1) = AS(u)`, so `w_i` depends on `ũ_i`
//! alone, and with `U_j = u(Q_j) + Σ_{i ≤ link j} ε_i` the link sums become
//! `s₁ = Σũ + U₁`, `s_j = U_{j−1} + Σũ + U_j` and
//! `s_L = U_{L−1} + Σũ + u_R + ε` with `ε = Σ_i ε_i`: one parity bit instead
//! of five.  The layout is the `m = 4` chain's — five blocks of `ℓ − 1`, then
//! `ε`, then `U₁ … U_{L−1}` — so
//! [`SymmetrisedSystem::summand_u0`] and [`SymmetrisedSystem::parity`] read a
//! root unchanged and [`lift_symmetrised_root_accepting`] lifts it.
//!
//! **The generic comparator on the same base.**  `S^{sym}(AS(u), Σu)` *is*
//! Semaev's polynomial written in `u` (for `S₃`:
//! `w₁w₂w₃ + Σw + s = w₁w₂w₃ + s²`, which is `x`'s `S₃` times `u₁²u₂²u₃²`
//! after `x = 1/u + 1`).  Without the folding — each summand a full `ℓ`-bit
//! `u_i ∈ V`, each intermediate its true `u(Q_j)` — the `[3, 3, 3, 3]` chain
//! is therefore the generic `S₃` chain transported to the `u`-coordinate:
//! [`ChainShape::PlainU`], `5ℓ + 3n` unknowns, the same count as the
//! `x`-chain.  It is the reference the folded chains are tested against on
//! the same factor base `F_u`; the production `x`-chain runs on a different
//! base (`x(P) ∈ V`), so it is compared on cost, not on its decompositions.
//!
//! ## What a solve returns
//!
//! [`SymChainOracle::decompose_all`] solves to completion, lifts every root
//! under every parity mask and every sign walk, and returns the set of
//! [`Decomposition`]s sorted ascending by `(via_t, indices)`: `indices` is
//! a sorted multiset of five factor-base indices summing to `R`
//! (`via_t = false`) or to `R + T` (`via_t = true`, `T = (0, 1)`).  A mask
//! of parity `ε` lifts to `R`, the other parity to `R + T`, because
//! `u(R + T) = u(R) + 1`.
//!
//! Which multisets a chain reaches is exact and computable: a multiset
//! `{P₁, …, P₅}` with `Σ P_i = R'` (`R' ∈ {R, R + T}`) is a root's lift iff
//! some ordering and signing `Σ s_i P_{σ(i)} = ±R'` has every *cut* partial
//! sum — after the summands of each link but the last — off the line
//! `x = 1` (`u = ∞` there).  An intermediate at `O` is *not* degenerate:
//! `u(O) = 0` is a value like any other, and the `u`-frame polynomials keep
//! their meaning there (`S₃^u(u₁, u₂, 0) = (u₁ + u₂)²`, i.e. `P₁ = ±P₂`).
//! [`reference_decompositions`] enumerates that set by brute force; the tests hold every shape to it, and the folded
//! `[3, 3, 3, 3]` chain to [`ChainShape::PlainU`] exactly.  The `[4, 4]`
//! chain has one cut where the `S₃` chains have three, so on a degenerate
//! target it can reach a multiset they miss (never the converse is claimed:
//! the reference decides per shape).  On every frozen instance of the test
//! suite (220+ targets) the two sets are identical.
//!
//! [`SymChainOracle::decompose_first`] is the index-calculus oracle: the
//! first root, in the solver's order, whose lift
//! [`lift_symmetrised_root_accepting`] accepts — the same lift and the same
//! `used_t` convention as the `m = 4` chained oracle.  Whenever
//! `decompose_all` holds a decomposition of `R` itself (`via_t = false`) it
//! finds a relation (tested); which relation depends on the solver's order.
//!
//! ## Solvers
//!
//! - [`ChainSolver::Groebner`]: the Weil-descended system through
//!   [`solve_boolean_system_filtered`] (matrix-F4 with splitting), for every
//!   shape.
//! - [`ChainSolver::Meet`], the specialised solver of a two-link chain such
//!   as the `[4, 4]` pair ([`meet_roots`]): with the one intermediate `U`
//!   left free, each link is, once its own summand bits (and `ε` on the
//!   last link) are fixed, a univariate polynomial of degree at most 4 in
//!   `U`.  Root-find the second link for each of its `2^{2(ℓ−1)+1}`
//!   assignments into a table keyed by `U`, root-find the first for each of
//!   its `2^{3(ℓ−1)}` and join.  It returns exactly F4's root set of the same
//!   system (tested), with no node budget.  Its cost is
//!   `2^{3(ℓ−1)} + 2^{2(ℓ−1)+1}` degree-4 root-finds, i.e. exponential in
//!   `ℓ`: a meet in the middle over the summand halves, not an algebraic
//!   attack, and it is cheap only while `ℓ` is small.
//!
//! ## Dispatch
//!
//! [`symmetrised_decompose_dispatch`] routes `m = 2, 3` to
//! [`symmetrised_groebner_decompose`] and `m = 4` to
//! [`chained_symmetrised_groebner_decompose`] (both unchanged), and `m = 5`
//! under [`ChainShape::Auto`] to the `[4, 4]` pair solved by
//! [`ChainSolver::Meet`].  An explicit shape runs that shape's chain under
//! F4; when a path declines (layout past [`MAX_VARS`]),
//! [`ChainShape::S3Links`] under F4 is the generic fallback.  The `[4, 4]`
//! pair has `5(ℓ − 1) + 1 + n` unknowns, so it runs at `n` where the
//! `S₃` chains (`+ 3n`) no longer fit 64 variables (tested at `n ≥ 19`).
//!
//! ## Honest scope
//!
//! Toy `n` (`n_vars ≤ 64`, single-word fields); no SAT arm; the brute-force
//! reference costs `C(|F| + 4, 5)` additions.  Timings in the module tests
//! are not measurements — the paired numbers come from the
//! `pdp/spec_sym_m5_*` perfbench kernels.

use std::collections::{BTreeSet, HashMap};

use num_bigint::BigUint;

use crate::binary_ecc::{BinaryPoint, F2mElement, IrreduciblePoly};
use crate::cryptanalysis::koblitz_fast::{FastCurve, FastPoint};
use crate::cryptanalysis::koblitz_groebner::{
    solve_boolean_system_filtered, split_rule_default, FieldStructure, SolveOptions, SolveStats,
    SolverEngine, SymElement, MAX_VARS,
};
use crate::cryptanalysis::koblitz_index_calculus::KoblitzCurve;
use crate::cryptanalysis::koblitz_symmetrised::{
    chained_symmetrised_groebner_decompose, lift_symmetrised_root_accepting, sym_polynomial,
    symmetrised_groebner_decompose, symmetrised_terms, u_of_x, OracleOutcome,
    SymmetrisedFactorBase, SymmetrisedSystem,
};
use crate::cryptanalysis::pq_groebner_f2::{F2BoolMono, F2BoolPoly};
use crate::cryptanalysis::semaev_decomp::Gf2;

fn bits_of(e: &F2mElement) -> u64 {
    e.raw_bits().first().copied().unwrap_or(0)
}

fn artin_schreier_in(u: &F2mElement, irr: &IrreduciblePoly) -> F2mElement {
    u.square(irr).add(u)
}

// ── Shapes ─────────────────────────────────────────────────────────

/// Which chain carries an `m`-summand decomposition.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum ChainShape {
    /// The specialised shape for `m`: the `[4, 4]` pair at `m = 5`, the
    /// existing `[3, 3, 3]` chain at `m = 4`, a single link below.
    Auto,
    /// Symmetrised `S₄` links, greedy: `[4, 4]` at `m = 5`, `[4, 3]` at
    /// `m = 4`, `[4]` at `m = 3`.
    S4Pair,
    /// Symmetrised `S₃` links, folded parities: `[3; m − 1]`.  The generic
    /// fallback.
    S3Links,
    /// The generic `S₃` chain in the `u`-coordinate, no parity folding:
    /// the same-base reference.
    PlainU,
}

impl ChainShape {
    /// The link arities of this shape at `m` summands, or `None` if the
    /// shape has no chain there.
    pub fn arities(self, m: usize) -> Option<Vec<usize>> {
        if m < 2 {
            return None;
        }
        match self {
            ChainShape::Auto => match m {
                2 => Some(vec![3]),
                3 => Some(vec![4]),
                4 => Some(vec![3, 3, 3]),
                _ => ChainShape::S4Pair.arities(m),
            },
            ChainShape::S4Pair => {
                if m == 2 {
                    return Some(vec![3]);
                }
                // First link: 3 summands (arity 4); then 2 per arity-4
                // link, a final arity-3 link for an odd remainder.
                let mut out = vec![4];
                let mut left = m - 3;
                while left >= 2 {
                    out.push(4);
                    left -= 2;
                }
                if left == 1 {
                    out.push(3);
                }
                Some(out)
            }
            ChainShape::S3Links | ChainShape::PlainU => Some(vec![3; m - 1]),
        }
    }

    /// Whether the shape folds the summand parities into one bit.
    pub fn folded(self) -> bool {
        !matches!(self, ChainShape::PlainU)
    }

    /// A short label for reports and fingerprints.
    pub fn label(self) -> &'static str {
        match self {
            ChainShape::Auto => "auto",
            ChainShape::S4Pair => "s4-pair",
            ChainShape::S3Links => "s3-links",
            ChainShape::PlainU => "plain-u",
        }
    }
}

/// Summands carried by a chain of the given link arities, or `None` if an
/// arity is not `3` or `4`.
pub fn summands_of(arities: &[usize]) -> Option<usize> {
    if arities.is_empty() || arities.iter().any(|&a| a != 3 && a != 4) {
        return None;
    }
    Some(link_summands(arities).iter().sum())
}

/// Summand counts per link: the first link's own summands, then each later
/// link's.
fn link_summands(arities: &[usize]) -> Vec<usize> {
    arities
        .iter()
        .enumerate()
        .map(|(j, &a)| if j == 0 { a - 1 } else { a - 2 })
        .collect()
}

// ── Systems ────────────────────────────────────────────────────────

/// A chained decomposition system and how to read its roots.
#[derive(Clone, Debug)]
pub struct SymChainSystem {
    pub equations: Vec<F2BoolPoly>,
    pub n_vars: usize,
    pub m: usize,
    /// Link arities.
    pub arities: Vec<usize>,
    /// Parities folded (`ℓ − 1` bits per summand plus `ε`) or not (`ℓ`).
    pub folded: bool,
    /// Bits per summand block.
    pub block: usize,
    /// `u(R)`.
    pub u_r: F2mElement,
}

impl SymChainSystem {
    /// The folded system in the shape
    /// [`lift_symmetrised_root_accepting`] reads.  `None` for an unfolded
    /// one.
    pub fn as_symmetrised(&self) -> Option<SymmetrisedSystem> {
        self.folded.then(|| SymmetrisedSystem {
            equations: self.equations.clone(),
            n_vars: self.n_vars,
            ell_w: self.block,
            m: self.m,
            u_r: self.u_r.clone(),
        })
    }

    /// Bits of the root's summand `i` before any parity choice: over
    /// `v_basis[1..]` (folded) or `v_basis` (unfolded), as a field word.
    fn summand_word(&self, v_bits: &[u64], root: u64, i: usize) -> u64 {
        let basis = if self.folded { &v_bits[1..] } else { v_bits };
        let mut acc = 0u64;
        for (t, &b) in basis.iter().enumerate() {
            if (root >> (i * self.block + t)) & 1 == 1 {
                acc ^= b;
            }
        }
        acc
    }

    fn parity(&self, root: u64) -> bool {
        self.folded && (root >> (self.m * self.block)) & 1 == 1
    }
}

/// **Build a chained decomposition system** in the `u`-frame over
/// `V = span(v_basis)` (`v_basis[0] = 1`) for the target abscissa `x_r`.
/// `arities` as in [`ChainShape::arities`]; `folded` selects the
/// parity-folded layout (`m` blocks of `ℓ − 1`, `ε`, the `U_j`) or the
/// plain one (`m` blocks of `ℓ`, the true `u(Q_j)`).  `None` if an arity is
/// not `3`/`4`, `u(R)` is `∞` (`x_r = 1`), or the layout exceeds
/// [`MAX_VARS`].
pub fn build_sym_chain_system(
    v_basis: &[F2mElement],
    irr: &IrreduciblePoly,
    x_r: &F2mElement,
    arities: &[usize],
    folded: bool,
    st: &FieldStructure,
) -> Option<SymChainSystem> {
    let u_r = x_r.add(&F2mElement::one(st.n)).flt_inverse(irr)?;
    build_sym_chain_system_u(v_basis, irr, &u_r, arities, folded, st)
}

/// [`build_sym_chain_system`] for a target given by `u_r = u(R)`.  `u_r = 0`
/// is the target `O` (`x = ∞`), where the `u`-frame polynomials stay
/// valid: the plain-`u` chain's `R + T` pass at `R = T` needs it.
pub fn build_sym_chain_system_u(
    v_basis: &[F2mElement],
    irr: &IrreduciblePoly,
    u_r: &F2mElement,
    arities: &[usize],
    folded: bool,
    st: &FieldStructure,
) -> Option<SymChainSystem> {
    let n = st.n;
    let m = summands_of(arities)?;
    if v_basis.first().map(bits_of) != Some(1) || v_basis.len() < 2 {
        return None;
    }
    let u_r = u_r.clone();
    let links = arities.len();
    let block = if folded {
        v_basis.len() - 1
    } else {
        v_basis.len()
    };
    let head = m * block + usize::from(folded);
    let n_vars = head + (links - 1) * n as usize;
    if n_vars > MAX_VARS {
        return None;
    }
    let u_basis: &[F2mElement] = if folded { &v_basis[1..] } else { v_basis };
    let w_basis: Vec<F2mElement> = u_basis.iter().map(|b| artin_schreier_in(b, irr)).collect();
    let as_unit: Vec<F2mElement> = (0..n)
        .map(|k| artin_schreier_in(&F2mElement::from_bit_positions(&[k], n), irr))
        .collect();
    let w: Vec<SymElement> = (0..m)
        .map(|i| SymElement::from_subspace_vars(&w_basis, i * block, n, n_vars))
        .collect();
    let u: Vec<SymElement> = (0..m)
        .map(|i| SymElement::from_subspace_vars(u_basis, i * block, n, n_vars))
        .collect();
    let q_u: Vec<SymElement> = (0..links - 1)
        .map(|j| SymElement::from_free_vars(head + j * n as usize, n, n_vars))
        .collect();
    let q_w: Vec<SymElement> = (0..links - 1)
        .map(|j| SymElement::from_subspace_vars(&as_unit, head + j * n as usize, n, n_vars))
        .collect();
    let w_r = SymElement::constant(&artin_schreier_in(&u_r, irr), n, n_vars);
    let mut tail = SymElement::constant(&u_r, n, n_vars);
    if folded {
        let mut eps = SymElement::zero(n, n_vars);
        eps.coords[0] = F2BoolPoly::from_monos(vec![F2BoolMono::var((m * block) as u32)], n_vars);
        tail = tail.add(&eps);
    }
    let per_link = link_summands(arities);
    let mut equations = Vec::with_capacity(links * n as usize);
    let mut next = 0usize;
    for (j, &a) in arities.iter().enumerate() {
        let terms = symmetrised_terms(a - 1)?;
        let mut ws: Vec<SymElement> = Vec::with_capacity(a + 1);
        let mut s = SymElement::zero(n, n_vars);
        if j > 0 {
            ws.push(q_w[j - 1].clone());
            s = s.add(&q_u[j - 1]);
        }
        for i in next..next + per_link[j] {
            ws.push(w[i].clone());
            s = s.add(&u[i]);
        }
        next += per_link[j];
        if j + 1 < links {
            ws.push(q_w[j].clone());
            s = s.add(&q_u[j]);
        } else {
            ws.push(w_r.clone());
            s = s.add(&tail);
        }
        ws.push(s);
        equations.extend(sym_polynomial(&ws, &terms, st));
    }
    debug_assert_eq!(next, m);
    Some(SymChainSystem {
        equations,
        n_vars,
        m,
        arities: arities.to_vec(),
        folded,
        block,
        u_r,
    })
}

// ── The meet-in-the-middle solver of two-link chains ───────────────

/// Polynomials in one unknown over `F_{2^n}`, coefficients low to high,
/// trimmed (no trailing zero; the zero polynomial is empty).
fn trim(mut p: Vec<u64>) -> Vec<u64> {
    while p.last() == Some(&0) {
        p.pop();
    }
    p
}

fn pmul(a: &[u64], b: &[u64], gf: &Gf2) -> Vec<u64> {
    if a.is_empty() || b.is_empty() {
        return Vec::new();
    }
    let mut out = vec![0u64; a.len() + b.len() - 1];
    for (i, &x) in a.iter().enumerate() {
        if x == 0 {
            continue;
        }
        for (j, &y) in b.iter().enumerate() {
            out[i + j] ^= gf.mul(x, y);
        }
    }
    trim(out)
}

fn padd(a: &[u64], b: &[u64]) -> Vec<u64> {
    let mut out = vec![0u64; a.len().max(b.len())];
    for (i, &x) in a.iter().enumerate() {
        out[i] ^= x;
    }
    for (i, &x) in b.iter().enumerate() {
        out[i] ^= x;
    }
    trim(out)
}

/// `(q, r)` with `a = q·b + r`, `deg r < deg b`; `b` non-zero.
fn pdivrem(a: &[u64], b: &[u64], gf: &Gf2) -> (Vec<u64>, Vec<u64>) {
    let db = b.len() - 1;
    let lead_inv = gf.inv(b[db]);
    let mut r = a.to_vec();
    let mut q = vec![0u64; a.len().saturating_sub(db)];
    while r.len() > db {
        let k = r.len() - 1 - db;
        let c = gf.mul(*r.last().expect("non-empty"), lead_inv);
        q[k] = c;
        for (j, &y) in b.iter().enumerate() {
            r[k + j] ^= gf.mul(c, y);
        }
        r = trim(r);
    }
    (trim(q), r)
}

fn pgcd(a: &[u64], b: &[u64], gf: &Gf2) -> Vec<u64> {
    let (mut a, mut b) = (a.to_vec(), b.to_vec());
    while !b.is_empty() {
        let (_, r) = pdivrem(&a, &b, gf);
        a = b;
        b = r;
    }
    a
}

/// `p² mod f`: squaring is coefficient-wise in characteristic 2.
fn psqr_mod(p: &[u64], f: &[u64], gf: &Gf2) -> Vec<u64> {
    let mut sq = vec![0u64; (2 * p.len()).saturating_sub(1)];
    for (i, &c) in p.iter().enumerate() {
        sq[2 * i] = gf.sqr(c);
    }
    pdivrem(&trim(sq), f, gf).1
}

/// The distinct roots of a non-zero `f` in `F_{2^n}`, ascending: the
/// linear factors of `gcd(f, X^{2^n} + X)`, split by `gcd(g, Tr(βX))` over
/// the polynomial basis `β = z^k` (the trace form is non-degenerate, so
/// some `z^k` separates any two distinct roots).
fn roots_in_field(f: &[u64], gf: &Gf2) -> Vec<u64> {
    let n = gf.n;
    let f = trim(f.to_vec());
    if f.len() <= 1 {
        return Vec::new();
    }
    let x = vec![0u64, 1];
    let mut h = pdivrem(&x, &f, gf).1;
    for _ in 0..n {
        h = psqr_mod(&h, &f, gf);
    }
    let g = pgcd(&f, &padd(&h, &x), gf);
    let mut out = Vec::new();
    let mut stack = vec![g];
    while let Some(g) = stack.pop() {
        match g.len() {
            0 | 1 => {}
            2 => out.push(gf.mul(g[0], gf.inv(g[1]))),
            _ => {
                let mut split = false;
                for k in 0..n {
                    // Tr(βX) mod g.
                    let mut t = pdivrem(&[0, 1u64 << k], &g, gf).1;
                    let mut acc = t.clone();
                    for _ in 1..n {
                        t = psqr_mod(&t, &g, gf);
                        acc = padd(&acc, &t);
                    }
                    let d = pgcd(&g, &acc, gf);
                    if d.len() > 1 && d.len() < g.len() {
                        let (q, _) = pdivrem(&g, &d, gf);
                        stack.push(d);
                        stack.push(q);
                        split = true;
                        break;
                    }
                }
                assert!(split, "a square-free split polynomial always separates");
            }
        }
    }
    out.sort_unstable();
    out
}

/// `Σ_terms Π slots[i]^{e_i}` as a polynomial in the one unknown.
fn link_poly(slots: &[Vec<u64>], terms: &[Vec<u32>], gf: &Gf2) -> Vec<u64> {
    let mut acc = Vec::new();
    for term in terms {
        let mut prod = vec![1u64];
        for (i, &e) in term.iter().enumerate() {
            for _ in 0..e {
                prod = pmul(&prod, &slots[i], gf);
            }
        }
        acc = padd(&acc, &prod);
    }
    acc
}

/// The roots of a link in its intermediate: `None` when the link
/// polynomial vanishes identically (every value is a root).
fn link_roots(slots: &[Vec<u64>], terms: &[Vec<u32>], gf: &Gf2) -> Option<Vec<u64>> {
    let p = link_poly(slots, terms, gf);
    (!p.is_empty()).then(|| roots_in_field(&p, gf))
}

/// Counters of [`meet_roots`].
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct MeetStats {
    /// Link polynomials built and root-found (one per half assignment).
    pub root_finds: u64,
    /// Half assignments whose link polynomial vanished identically.
    pub identically_zero: u64,
    /// `(first half, second half, U)` triples emitted.
    pub roots: u64,
}

/// **Every root of a folded two-link chain, without Gröbner bases.**  With
/// one intermediate `U`, each link is, once its own summands (and `ε` on
/// the last link) are fixed, a univariate polynomial of degree at most 4
/// in `U` (`w_Q = U² + U`, `s = c + U`).  Root-find the second link for
/// each of its `2^{k₂(ℓ−1)+1}` assignments into a table `U ↦ assignments`,
/// root-find the first link for each of its `2^{k₁(ℓ−1)}` and join on `U`.
/// The result is the Boolean root set of the system
/// [`build_sym_chain_system`] builds for the same `arities` (folded), in
/// the same layout, sorted ascending — the test suite compares it with
/// matrix-F4's.  `None` unless the chain has exactly two links.
pub fn meet_roots(
    v_basis: &[F2mElement],
    irr: &IrreduciblePoly,
    x_r: &F2mElement,
    arities: &[usize],
) -> Option<(Vec<u64>, MeetStats)> {
    meet_roots_within(v_basis, irr, x_r, arities, u64::MAX).map(|(roots, stats, _)| (roots, stats))
}

/// [`meet_roots`] under a root-find budget.  The meet's cost is known
/// before it starts (`2^{k₂(ℓ−1)+1} + 2^{k₁(ℓ−1)}` root-finds, and the
/// join needs the whole table), so a chain over `max_root_finds` is not
/// started: it returns no roots, zero root-finds and `false` (incomplete).
/// The third field is `true` when the root set is the whole set.
fn meet_roots_within(
    v_basis: &[F2mElement],
    irr: &IrreduciblePoly,
    x_r: &F2mElement,
    arities: &[usize],
    max_root_finds: u64,
) -> Option<(Vec<u64>, MeetStats, bool)> {
    let n = irr.degree;
    if arities.len() != 2 || summands_of(arities).is_none() || v_basis.len() < 2 {
        return None;
    }
    if v_basis.first().map(bits_of) != Some(1) {
        return None;
    }
    let u_r = x_r.add(&F2mElement::one(n)).flt_inverse(irr)?;
    if u_r.is_zero() {
        return None;
    }
    let gf = Gf2::new(irr);
    let per = link_summands(arities);
    let (k1, k2) = (per[0], per[1]);
    let m = k1 + k2;
    let block = v_basis.len() - 1;
    let head = m * block + 1;
    if head + n as usize > MAX_VARS {
        return None;
    }
    let mut stats = MeetStats::default();
    let cost = (1u64 << (k2 * block + 1)) + (1u64 << (k1 * block));
    if cost > max_root_finds {
        return Some((Vec::new(), stats, false));
    }
    let ub: Vec<u64> = v_basis[1..].iter().map(bits_of).collect();
    let u_r = bits_of(&u_r);
    let w_r = gf.sqr(u_r) ^ u_r;
    let word = |bits: u64| -> u64 {
        let mut acc = 0;
        for (t, &b) in ub.iter().enumerate() {
            if (bits >> t) & 1 == 1 {
                acc ^= b;
            }
        }
        acc
    };
    let w_q = vec![0u64, 1, 1];
    let terms1 = symmetrised_terms(arities[0] - 1)?;
    let terms2 = symmetrised_terms(arities[1] - 1)?;
    let mask_of = |k: usize| -> u64 { (1u64 << (k * block)) - 1 };
    let blk = (1u64 << block) - 1;
    // Second link: Q, summands k1 … m−1, R; s = U + Σũ + u_R + ε.
    let mut table: HashMap<u64, Vec<u64>> = HashMap::new();
    let mut any_u: Vec<u64> = Vec::new();
    for a2 in 0..(1u64 << (k2 * block + 1)) {
        let eps = (a2 >> (k2 * block)) & 1;
        let mut slots = vec![w_q.clone()];
        let mut c = u_r ^ eps;
        for i in 0..k2 {
            let u = word((a2 >> (i * block)) & blk);
            slots.push(vec![gf.sqr(u) ^ u]);
            c ^= u;
        }
        slots.push(vec![w_r]);
        slots.push(trim(vec![c, 1]));
        for s in slots.iter_mut() {
            *s = trim(std::mem::take(s));
        }
        stats.root_finds += 1;
        match link_roots(&slots, &terms2, &gf) {
            Some(rs) => {
                for u in rs {
                    table.entry(u).or_default().push(a2);
                }
            }
            None => {
                stats.identically_zero += 1;
                any_u.push(a2);
            }
        }
    }
    let mut out = Vec::new();
    let compose = |a1: u64, a2: u64, u: u64| -> u64 {
        a1 | ((a2 & mask_of(k2)) << (k1 * block))
            | (((a2 >> (k2 * block)) & 1) << (m * block))
            | (u << head)
    };
    for a1 in 0..(1u64 << (k1 * block)) {
        let mut slots = Vec::with_capacity(k1 + 2);
        let mut c = 0u64;
        for i in 0..k1 {
            let u = word((a1 >> (i * block)) & blk);
            slots.push(trim(vec![gf.sqr(u) ^ u]));
            c ^= u;
        }
        slots.push(w_q.clone());
        slots.push(trim(vec![c, 1]));
        stats.root_finds += 1;
        match link_roots(&slots, &terms1, &gf) {
            Some(rs) => {
                for u in rs {
                    if let Some(a2s) = table.get(&u) {
                        out.extend(a2s.iter().map(|&a2| compose(a1, a2, u)));
                    }
                    out.extend(any_u.iter().map(|&a2| compose(a1, a2, u)));
                }
            }
            None => {
                stats.identically_zero += 1;
                for (&u, a2s) in &table {
                    out.extend(a2s.iter().map(|&a2| compose(a1, a2, u)));
                }
                for u in 0..(1u64 << n) {
                    out.extend(any_u.iter().map(|&a2| compose(a1, a2, u)));
                }
            }
        }
    }
    out.sort_unstable();
    stats.roots = out.len() as u64;
    Some((out, stats, true))
}

// ── Decompositions ─────────────────────────────────────────────────

/// One decomposition: a sorted multiset of factor-base indices summing to
/// `R` (`via_t = false`) or `R + T` (`via_t = true`).  Ordered by
/// `(via_t, indices)`.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Decomposition {
    pub via_t: bool,
    pub indices: Vec<usize>,
}

/// How a chain's roots are found.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ChainSolver {
    /// [`solve_boolean_system_filtered`] on the Weil-descended system.
    Groebner {
        engine: SolverEngine,
        node_budget: usize,
    },
    /// [`meet_roots`]: two-link folded chains only (the `[4, 4]` pair at
    /// `m = 5`); never exhausts a budget.
    Meet,
}

/// Outcome of [`SymChainOracle::decompose_all`].
#[derive(Clone, Debug)]
pub struct ChainEnumeration {
    /// Every decomposition the roots lift to, sorted ascending.
    pub decompositions: Vec<Decomposition>,
    /// Roots the solver returned (both systems for [`ChainShape::PlainU`]).
    pub roots: usize,
    /// The solve completed (no budget exhaustion): the set is the whole
    /// set this shape reaches.
    pub complete: bool,
    pub n_vars: usize,
    /// Equations and Boolean degree of the system; `0` under
    /// [`ChainSolver::Meet`], which never builds it.
    pub n_equations: usize,
    pub degree: u32,
    /// Gröbner counters, summed over the systems solved (zero for
    /// [`ChainSolver::Meet`]).
    pub stats: SolveStats,
    /// Meet counters (zero for [`ChainSolver::Groebner`]).
    pub meet: MeetStats,
}

/// Per-base state for the chained oracles: the curve on single words, the
/// factor base indexed by `u`-value, `T`.
pub struct SymChainOracle<'a> {
    pub kc: &'a KoblitzCurve,
    pub fb: &'a SymmetrisedFactorBase,
    pub st: &'a FieldStructure,
    fc: FastCurve,
    points: Vec<FastPoint>,
    by_u: HashMap<u64, Vec<usize>>,
    v_bits: Vec<u64>,
    t: FastPoint,
}

/// Roots of one system plus what the solve cost.
struct Solved {
    roots: Vec<u64>,
    stats: SolveStats,
    meet: MeetStats,
    /// The roots are the whole root set (no budget ran out).
    complete: bool,
}

impl<'a> SymChainOracle<'a> {
    /// `None` if the field does not fit a word or a base point has
    /// `u = ∞`.
    pub fn new(
        kc: &'a KoblitzCurve,
        fb: &'a SymmetrisedFactorBase,
        st: &'a FieldStructure,
    ) -> Option<Self> {
        let fc = FastCurve::new(&kc.curve)?;
        let points: Vec<FastPoint> = fb.points.iter().map(|p| fc.lift(p)).collect();
        let mut by_u: HashMap<u64, Vec<usize>> = HashMap::new();
        for (i, p) in fb.points.iter().enumerate() {
            let BinaryPoint::Affine { x, .. } = p else {
                return None;
            };
            by_u.entry(bits_of(&u_of_x(x, kc)?)).or_default().push(i);
        }
        let t = fc.lift(&fb.two_torsion);
        Some(Self {
            kc,
            fb,
            st,
            fc,
            points,
            by_u,
            v_bits: fb.v_basis.iter().map(bits_of).collect(),
            t,
        })
    }

    /// The system for `target` under `shape`, `None` where
    /// [`build_sym_chain_system`] declines.
    pub fn system(
        &self,
        target: &BinaryPoint,
        m: usize,
        shape: ChainShape,
    ) -> Option<SymChainSystem> {
        let BinaryPoint::Affine { x, .. } = target else {
            return None;
        };
        build_sym_chain_system(
            &self.fb.v_basis,
            &self.kc.curve.irreducible,
            x,
            &shape.arities(m)?,
            shape.folded(),
            self.st,
        )
    }

    /// The layout of `shape`'s system without its equations (what the
    /// meet solver and the lift read), checked as [`Self::system`] would.
    fn layout(&self, target: &BinaryPoint, m: usize, shape: ChainShape) -> Option<SymChainSystem> {
        let BinaryPoint::Affine { x, .. } = target else {
            return None;
        };
        let arities = shape.arities(m)?;
        if summands_of(&arities)? != m || !shape.folded() || self.fb.v_basis.len() < 2 {
            return None;
        }
        let n = self.kc.n;
        let u_r = u_of_x(x, self.kc)?;
        let block = self.fb.v_basis.len() - 1;
        let n_vars = m * block + 1 + (arities.len() - 1) * n as usize;
        (n_vars <= MAX_VARS && !u_r.is_zero()).then(|| SymChainSystem {
            equations: Vec::new(),
            n_vars,
            m,
            arities,
            folded: true,
            block,
            u_r,
        })
    }

    /// `meet_budget` caps [`ChainSolver::Meet`]'s root-finds (see
    /// [`meet_roots_within`]); the Gröbner solver has its own budget.
    fn solve(
        &self,
        sys: &SymChainSystem,
        target: &BinaryPoint,
        solver: ChainSolver,
        meet_budget: u64,
    ) -> Option<Solved> {
        match solver {
            ChainSolver::Groebner {
                engine,
                node_budget,
            } => {
                let opts = SolveOptions {
                    engine,
                    max_solutions: usize::MAX,
                    node_budget,
                    split_rule: split_rule_default(),
                };
                let (roots, stats) =
                    solve_boolean_system_filtered(&sys.equations, sys.n_vars, &opts, |_| false);
                Some(Solved {
                    roots,
                    complete: !stats.exhausted,
                    stats,
                    meet: MeetStats::default(),
                })
            }
            ChainSolver::Meet => {
                let BinaryPoint::Affine { x, .. } = target else {
                    return None;
                };
                if !sys.folded {
                    return None;
                }
                let (roots, meet, complete) = meet_roots_within(
                    &self.fb.v_basis,
                    &self.kc.curve.irreducible,
                    x,
                    &sys.arities,
                    meet_budget,
                )?;
                Some(Solved {
                    roots,
                    stats: SolveStats::default(),
                    meet,
                    complete,
                })
            }
        }
    }

    /// Every decomposition one root lifts to, into `out`.  A folded root
    /// is lifted under every parity mask (`via_t` by the mask's parity); an
    /// unfolded root lifts to `goal` with the given `via_t`.
    fn lift_all(
        &self,
        sys: &SymChainSystem,
        root: u64,
        target: FastPoint,
        shifted: FastPoint,
        plain_via_t: bool,
        out: &mut BTreeSet<Decomposition>,
    ) {
        let m = sys.m;
        let u0: Vec<u64> = (0..m)
            .map(|i| sys.summand_word(&self.v_bits, root, i))
            .collect();
        let parity = sys.parity(root);
        let masks = if sys.folded { 1u32 << m } else { 1 };
        let mut chosen = Vec::with_capacity(m);
        for mask in 0..masks {
            let mut cands: Vec<&[usize]> = Vec::with_capacity(m);
            for (i, &w) in u0.iter().enumerate() {
                let u = w ^ u64::from((mask >> i) & 1);
                match self.by_u.get(&u) {
                    Some(v) if u != 0 => cands.push(v),
                    _ => break,
                }
            }
            if cands.len() < m {
                continue;
            }
            // A folded mask of the root's parity is a plain root for `R`;
            // the other parity, for `R + T` (`u(R + T) = u(R) + 1`).
            let via_t = if sys.folded {
                (mask.count_ones() % 2 == 1) != parity
            } else {
                plain_via_t
            };
            let goal = if via_t { shifted } else { target };
            chosen.clear();
            self.walk(
                &cands,
                0,
                FastPoint::INFINITY,
                goal,
                via_t,
                &mut chosen,
                out,
            );
        }
    }

    #[allow(clippy::too_many_arguments)]
    fn walk(
        &self,
        cands: &[&[usize]],
        depth: usize,
        acc: FastPoint,
        goal: FastPoint,
        via_t: bool,
        chosen: &mut Vec<usize>,
        out: &mut BTreeSet<Decomposition>,
    ) {
        if depth == cands.len() {
            if acc == goal {
                let mut indices = chosen.clone();
                indices.sort_unstable();
                out.insert(Decomposition { via_t, indices });
            }
            return;
        }
        for &i in cands[depth] {
            chosen.push(i);
            let next = self.fc.add(acc, self.points[i]);
            self.walk(cands, depth + 1, next, goal, via_t, chosen, out);
            chosen.pop();
        }
    }

    /// **Every decomposition** of `target` this shape reaches: solve to
    /// completion and lift every root (see the module docs for the set and
    /// its order).  [`ChainShape::PlainU`] solves two systems, for `R` and
    /// for `R + T`.  `None` where the system does not build or the solver
    /// does not apply.  The list includes the `T`-shifted copies of each
    /// decomposition (summands `P_i ↦ P_i + T`, which stay in the base as
    /// `1 ∈ V`) as separate entries: they are distinct valid index tuples,
    /// so the count overstates the distinct relations modulo `T`.
    pub fn decompose_all(
        &self,
        target: &BinaryPoint,
        m: usize,
        shape: ChainShape,
        solver: ChainSolver,
    ) -> Option<ChainEnumeration> {
        let ft = self.fc.lift(target);
        let shifted = self.fc.add(ft, self.t);
        let mut set = BTreeSet::new();
        let mut roots = 0;
        let mut stats = SolveStats::default();
        let mut meet = MeetStats::default();
        let mut shape_info = None;
        let first = match solver {
            ChainSolver::Meet => self.layout(target, m, shape)?,
            ChainSolver::Groebner { .. } => self.system(target, m, shape)?,
        };
        let mut passes = vec![(first, false)];
        if !shape.folded() {
            // `u(R + T) = u(R) + 1`, which is `0` when `R + T = O`.
            let u_rt = passes[0].0.u_r.add(&F2mElement::one(self.kc.n));
            let sys = build_sym_chain_system_u(
                &self.fb.v_basis,
                &self.kc.curve.irreducible,
                &u_rt,
                &shape.arities(m)?,
                false,
                self.st,
            )?;
            passes.push((sys, true));
        }
        for (sys, via_t) in &passes {
            let solved = self.solve(sys, target, solver, u64::MAX)?;
            for &root in &solved.roots {
                self.lift_all(sys, root, ft, shifted, *via_t, &mut set);
            }
            roots += solved.roots.len();
            stats.reductions += solved.stats.reductions;
            stats.infeasible_branches += solved.stats.infeasible_branches;
            stats.propagations += solved.stats.propagations;
            stats.splits += solved.stats.splits;
            stats.exhausted |= solved.stats.exhausted;
            stats.max_degree_built = stats.max_degree_built.max(solved.stats.max_degree_built);
            stats.oversize += solved.stats.oversize;
            stats.eliminated += solved.stats.eliminated;
            meet.root_finds += solved.meet.root_finds;
            meet.identically_zero += solved.meet.identically_zero;
            meet.roots += solved.meet.roots;
            shape_info.get_or_insert((
                sys.n_vars,
                sys.equations.len(),
                system_degree(&sys.equations),
            ));
        }
        let (n_vars, n_equations, degree) = shape_info?;
        Some(ChainEnumeration {
            decompositions: set.into_iter().collect(),
            roots,
            complete: !stats.exhausted,
            n_vars,
            n_equations,
            degree,
            stats,
            meet,
        })
    }

    /// **The index-calculus oracle**: the first root, in the solver's
    /// order, whose lift [`lift_symmetrised_root_accepting`] accepts — the
    /// `m = 4` chained oracle's lift and `used_t` convention (`T` appended
    /// when the lift went through `R + T`).  A plain-`u` shape lifts its
    /// roots directly to `R`.  For [`ChainSolver::Meet`], `effort` is the
    /// number of root-finds and the counters F4 fills stay zero.
    pub fn decompose_first(
        &self,
        target: &BinaryPoint,
        m: usize,
        shape: ChainShape,
        solver: ChainSolver,
    ) -> Option<OracleOutcome> {
        self.decompose_first_within(target, m, shape, solver, u64::MAX)
    }

    /// [`Self::decompose_first`] with [`ChainSolver::Meet`] capped at
    /// `meet_budget` root-finds: a meet over it is not run and reports no
    /// relation with `complete = false`, never a refutation.
    fn decompose_first_within(
        &self,
        target: &BinaryPoint,
        m: usize,
        shape: ChainShape,
        solver: ChainSolver,
        meet_budget: u64,
    ) -> Option<OracleOutcome> {
        let ft = self.fc.lift(target);
        let mut found: Option<(Vec<usize>, bool)> = None;
        let mut lift = |sys: &SymChainSystem, root: u64| -> bool {
            let hit = match sys.as_symmetrised() {
                Some(s) => {
                    lift_symmetrised_root_accepting(self.kc, self.fb, &s, root, target, |_| true)
                }
                None => {
                    let mut one = BTreeSet::new();
                    self.lift_all(sys, root, ft, ft, false, &mut one);
                    one.into_iter().next().map(|d| (d.indices, false))
                }
            };
            match hit {
                Some(r) => {
                    found = Some(r);
                    true
                }
                None => false,
            }
        };
        let (sys, complete, effort, built_degree, oversize) = match solver {
            ChainSolver::Groebner {
                engine,
                node_budget,
            } => {
                let sys = self.system(target, m, shape)?;
                let opts = SolveOptions {
                    engine,
                    max_solutions: usize::MAX,
                    node_budget,
                    split_rule: split_rule_default(),
                };
                let (_, stats) =
                    solve_boolean_system_filtered(&sys.equations, sys.n_vars, &opts, |root| {
                        lift(&sys, root)
                    });
                (
                    sys,
                    !stats.exhausted,
                    stats.splits as u64,
                    stats.max_degree_built,
                    stats.oversize,
                )
            }
            ChainSolver::Meet => {
                let sys = self.layout(target, m, shape)?;
                let solved = self.solve(&sys, target, solver, meet_budget)?;
                for &root in &solved.roots {
                    if lift(&sys, root) {
                        break;
                    }
                }
                (sys, solved.complete, solved.meet.root_finds, 0, 0)
            }
        };
        let used_t = found.as_ref().is_some_and(|r| r.1);
        Some(OracleOutcome {
            relation: found.map(|r| r.0),
            used_t,
            complete,
            n_vars: sys.n_vars,
            n_equations: sys.equations.len(),
            degree: system_degree(&sys.equations),
            effort,
            built_degree,
            oversize,
        })
    }
}

fn system_degree(eqs: &[F2BoolPoly]) -> u32 {
    eqs.iter()
        .flat_map(|p| p.terms.iter())
        .map(|t| t.mask.count_ones())
        .max()
        .unwrap_or(0)
}

// ── Dispatch ───────────────────────────────────────────────────────

/// **Symmetrised decomposition at any supported `m`**, one entry point
/// returning the first accepted relation:
///
/// - `m = 2, 3`, [`ChainShape::Auto`] → [`symmetrised_groebner_decompose`]
///   (the direct system, unchanged);
/// - `m = 4`, `Auto` → [`chained_symmetrised_groebner_decompose`]
///   (unchanged);
/// - `m = 5`, `Auto` → the specialised path: the `[4, 4]` pair solved by
///   [`ChainSolver::Meet`], which is exact, with its root-finds charged
///   against `node_budget`: a meet that would need more is not run and
///   returns no relation with `complete = false`;
/// - an explicit shape, or a specialised path that declines (layout over
///   [`MAX_VARS`]) → that shape's chain under matrix-F4 with `engine` and
///   `node_budget`, and finally the generic [`ChainShape::S3Links`] chain.
#[allow(clippy::too_many_arguments)]
pub fn symmetrised_decompose_dispatch(
    kc: &KoblitzCurve,
    fb: &SymmetrisedFactorBase,
    st: &FieldStructure,
    target: &BinaryPoint,
    m: usize,
    shape: ChainShape,
    engine: SolverEngine,
    node_budget: usize,
) -> Option<OracleOutcome> {
    let groebner = ChainSolver::Groebner {
        engine,
        node_budget,
    };
    match (m, shape) {
        (2 | 3, ChainShape::Auto) => {
            symmetrised_groebner_decompose(kc, fb, st, target, m, engine, node_budget)
        }
        (4, ChainShape::Auto) => {
            chained_symmetrised_groebner_decompose(kc, fb, st, target, engine, node_budget)
        }
        _ => {
            let oracle = SymChainOracle::new(kc, fb, st)?;
            let special = (m == 5 && shape == ChainShape::Auto)
                .then(|| {
                    oracle.decompose_first_within(
                        target,
                        m,
                        ChainShape::S4Pair,
                        ChainSolver::Meet,
                        u64::try_from(node_budget).unwrap_or(u64::MAX),
                    )
                })
                .flatten();
            special
                .or_else(|| oracle.decompose_first(target, m, shape, groebner))
                .or_else(|| oracle.decompose_first(target, m, ChainShape::S3Links, groebner))
        }
    }
}

// ── Reference ──────────────────────────────────────────────────────

/// Positions after which a chain of `arities` has an intermediate point:
/// the partial sums of the per-link summand counts, all but the last.
pub fn cut_positions(arities: &[usize]) -> Vec<usize> {
    let per = link_summands(arities);
    let mut acc = 0;
    let mut out = Vec::new();
    for &k in &per[..per.len().saturating_sub(1)] {
        acc += k;
        out.push(acc);
    }
    out
}

/// **Brute-force reference**: every multiset of `m` base points summing to
/// `target` or `target + T`, kept iff the chain with these `arities` reaches
/// it (some ordering and signing with total `±R'` and every cut partial sum
/// off the line `x = 1`; `O` allowed).  Sorted as [`ChainEnumeration::decompositions`].
/// Cost `C(|F| + m − 1, m)` additions plus `m!·2^{m−1}` per hit: toy bases
/// only.
pub fn reference_decompositions(
    kc: &KoblitzCurve,
    fb: &SymmetrisedFactorBase,
    target: &BinaryPoint,
    m: usize,
    arities: &[usize],
) -> Option<Vec<Decomposition>> {
    let fc = FastCurve::new(&kc.curve)?;
    let pts: Vec<FastPoint> = fb.points.iter().map(|p| fc.lift(p)).collect();
    let ft = fc.lift(target);
    let shifted = fc.add(ft, fc.lift(&fb.two_torsion));
    let cuts = cut_positions(arities);
    let mut out = Vec::new();
    let mut idx = vec![0usize; m];
    let mut partial = vec![FastPoint::INFINITY; m + 1];
    #[allow(clippy::too_many_arguments)]
    fn rec(
        fc: &FastCurve,
        pts: &[FastPoint],
        depth: usize,
        start: usize,
        idx: &mut [usize],
        partial: &mut [FastPoint],
        ft: FastPoint,
        shifted: FastPoint,
        cuts: &[usize],
        out: &mut Vec<Decomposition>,
    ) {
        let m = idx.len();
        if depth == m {
            let sum = partial[m];
            for (goal, via_t) in [(ft, false), (shifted, true)] {
                if sum == goal && reachable(fc, pts, idx, goal, cuts) {
                    out.push(Decomposition {
                        via_t,
                        indices: idx.to_vec(),
                    });
                }
            }
            return;
        }
        for i in start..pts.len() {
            idx[depth] = i;
            partial[depth + 1] = fc.add(partial[depth], pts[i]);
            rec(fc, pts, depth + 1, i, idx, partial, ft, shifted, cuts, out);
        }
    }
    rec(
        &fc,
        &pts,
        0,
        0,
        &mut idx,
        &mut partial,
        ft,
        shifted,
        &cuts,
        &mut out,
    );
    out.sort();
    Some(out)
}

/// Some ordering of `idx` and signing (first sign `+`) whose total is
/// `±goal` with no cut partial sum on the line `x = 1`.
fn reachable(
    fc: &FastCurve,
    pts: &[FastPoint],
    idx: &[usize],
    goal: FastPoint,
    cuts: &[usize],
) -> bool {
    let m = idx.len();
    let neg_goal = fc.neg(goal);
    let mut perm: Vec<usize> = idx.to_vec();
    perm.sort_unstable();
    loop {
        for signs in 0..(1u32 << (m - 1)) {
            let mut acc = FastPoint::INFINITY;
            let mut ok = true;
            for (k, &i) in perm.iter().enumerate() {
                let p = if k > 0 && (signs >> (k - 1)) & 1 == 1 {
                    fc.neg(pts[i])
                } else {
                    pts[i]
                };
                acc = fc.add(acc, p);
                if cuts.contains(&(k + 1)) && !acc.infinity && acc.x == 1 {
                    ok = false;
                    break;
                }
            }
            if ok && (acc == goal || acc == neg_goal) {
                return true;
            }
        }
        if !next_permutation(&mut perm) {
            return false;
        }
    }
}

fn next_permutation(v: &mut [usize]) -> bool {
    let n = v.len();
    if n < 2 {
        return false;
    }
    let mut i = n - 1;
    while i > 0 && v[i - 1] >= v[i] {
        i -= 1;
    }
    if i == 0 {
        return false;
    }
    let mut j = n - 1;
    while v[j] <= v[i - 1] {
        j -= 1;
    }
    v.swap(i - 1, j);
    v[i..].reverse();
    true
}

/// `R`'s subgroup targets for tests and kernels: `count` points `[k]G`,
/// `k` drawn from `seed`, with `x ∉ {0, 1}`.
pub fn subgroup_targets(kc: &KoblitzCurve, count: usize, seed: u64) -> Vec<BinaryPoint> {
    use rand::{rngs::StdRng, Rng, SeedableRng};
    let mut rng = StdRng::seed_from_u64(seed);
    let r = kc
        .subgroup_order
        .to_u64_digits()
        .first()
        .copied()
        .unwrap_or(2)
        .max(2);
    let n = kc.n;
    let mut out = Vec::with_capacity(count);
    while out.len() < count {
        let t = kc.mul(kc.generator(), &BigUint::from(rng.gen_range(1..r)));
        if matches!(&t, BinaryPoint::Affine { x, .. } if *x != F2mElement::one(n) && !x.is_zero()) {
            out.push(t);
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::koblitz_symmetrised::{
        build_chained_symmetrised_system, build_symmetrised_factor_base_from_basis,
        build_symmetrised_system, random_subspace_containing_one,
    };
    use rand::{rngs::StdRng, Rng, SeedableRng};

    fn f4() -> ChainSolver {
        ChainSolver::Groebner {
            engine: SolverEngine::default(),
            node_budget: 1_000_000,
        }
    }

    /// Curve, structure and a random non-invariant `V ∋ 1` of dimension
    /// `ell`, with its base.
    fn instance(
        a: u8,
        n: u32,
        ell: usize,
        seed: u64,
    ) -> (KoblitzCurve, FieldStructure, SymmetrisedFactorBase) {
        let kc = KoblitzCurve::new(a, n).expect("curve");
        let st = FieldStructure::new(n, &kc.curve.irreducible);
        let mut rng = StdRng::seed_from_u64(seed);
        loop {
            let v = random_subspace_containing_one(&kc, ell, &mut rng);
            if let Some(fb) = build_symmetrised_factor_base_from_basis(&kc, v) {
                return (kc, st, fb);
            }
        }
    }

    /// Random subgroup targets, sums of five base points (planted), the
    /// same plus `T` (planted through `T`), and `T` itself; with a flag for
    /// the planted ones.
    fn targets_flagged(
        kc: &KoblitzCurve,
        fb: &SymmetrisedFactorBase,
        seed: u64,
    ) -> Vec<(BinaryPoint, bool)> {
        let mut out: Vec<(BinaryPoint, bool)> = subgroup_targets(kc, 3, seed)
            .into_iter()
            .map(|t| (t, false))
            .collect();
        let mut rng = StdRng::seed_from_u64(seed ^ 0xA5A5);
        let n = kc.n;
        let ok = |p: &BinaryPoint| matches!(p, BinaryPoint::Affine { x, .. } if *x != F2mElement::one(n));
        // A base whose sums all land on `O` or `x = 1` has nothing to
        // plant; bounded tries keep such a base from looping.
        let mut planted = 0;
        for _ in 0..10_000 {
            if planted == 4 {
                break;
            }
            let idx: Vec<usize> = (0..5).map(|_| rng.gen_range(0..fb.points.len())).collect();
            let mut r = fb.sum(kc, &idx);
            if planted % 2 == 1 {
                r = kc.add(&r, &fb.two_torsion);
            }
            if ok(&r) {
                out.push((r, true));
                planted += 1;
            }
        }
        out.push((fb.two_torsion.clone(), false));
        out
    }

    fn targets(kc: &KoblitzCurve, fb: &SymmetrisedFactorBase, seed: u64) -> Vec<BinaryPoint> {
        targets_flagged(kc, fb, seed)
            .into_iter()
            .map(|t| t.0)
            .collect()
    }

    fn check_resums(
        kc: &KoblitzCurve,
        fb: &SymmetrisedFactorBase,
        t: &BinaryPoint,
        ds: &[Decomposition],
    ) {
        let shifted = kc.add(t, &fb.two_torsion);
        for d in ds {
            assert_eq!(d.indices.len(), 5);
            assert!(d.indices.windows(2).all(|w| w[0] <= w[1]));
            let sum = fb.sum(kc, &d.indices);
            assert_eq!(
                sum,
                if d.via_t { shifted.clone() } else { t.clone() },
                "{d:?}"
            );
        }
        assert!(ds.windows(2).all(|w| w[0] < w[1]), "sorted, distinct");
    }

    #[test]
    fn arities_and_cuts() {
        assert_eq!(ChainShape::Auto.arities(5), Some(vec![4, 4]));
        assert_eq!(ChainShape::S4Pair.arities(5), Some(vec![4, 4]));
        assert_eq!(ChainShape::S4Pair.arities(4), Some(vec![4, 3]));
        assert_eq!(ChainShape::S4Pair.arities(6), Some(vec![4, 4, 3]));
        assert_eq!(ChainShape::S3Links.arities(5), Some(vec![3, 3, 3, 3]));
        assert_eq!(ChainShape::PlainU.arities(5), Some(vec![3, 3, 3, 3]));
        assert_eq!(ChainShape::Auto.arities(4), Some(vec![3, 3, 3]));
        assert_eq!(ChainShape::Auto.arities(1), None);
        for m in 2..=8 {
            for shape in [ChainShape::Auto, ChainShape::S4Pair, ChainShape::S3Links] {
                assert_eq!(
                    summands_of(&shape.arities(m).unwrap()),
                    Some(m),
                    "{shape:?} m={m}"
                );
            }
        }
        assert_eq!(summands_of(&[5]), None);
        assert_eq!(summands_of(&[]), None);
        assert_eq!(cut_positions(&[4, 4]), vec![3]);
        assert_eq!(cut_positions(&[3, 3, 3, 3]), vec![2, 3, 4]);
        assert_eq!(cut_positions(&[4]), Vec::<usize>::new());
    }

    #[test]
    fn general_builder_reproduces_the_existing_systems() {
        let (kc, st, fb) = instance(1, 11, 4, 0x11);
        let irr = &kc.curve.irreducible;
        for t in subgroup_targets(&kc, 6, 0x22) {
            let BinaryPoint::Affine { x, .. } = &t else {
                unreachable!()
            };
            let old = build_chained_symmetrised_system(&fb.v_basis, irr, x, &st).unwrap();
            let new = build_sym_chain_system(&fb.v_basis, irr, x, &[3, 3, 3], true, &st).unwrap();
            assert_eq!(new.n_vars, old.n_vars);
            assert_eq!(new.block, old.ell_w);
            assert_eq!(new.equations, old.equations, "m = 4 chain");
            for m in [2usize, 3] {
                let old = build_symmetrised_system(&kc, &fb, &t, m, &st).unwrap();
                let new = build_sym_chain_system(&fb.v_basis, irr, x, &[m + 1], true, &st).unwrap();
                assert_eq!(new.n_vars, old.n_vars);
                assert_eq!(new.equations, old.equations, "direct m = {m}");
            }
        }
    }

    #[test]
    fn layouts_and_declines() {
        let (kc, st, fb) = instance(1, 11, 4, 0x33);
        let irr = &kc.curve.irreducible;
        let x = F2mElement::from_bit_positions(&[1, 4], 11);
        let s4 = build_sym_chain_system(&fb.v_basis, irr, &x, &[4, 4], true, &st).unwrap();
        assert_eq!((s4.n_vars, s4.equations.len()), (5 * 3 + 1 + 11, 22));
        assert_eq!(system_degree(&s4.equations), 5);
        let s3 = build_sym_chain_system(&fb.v_basis, irr, &x, &[3; 4], true, &st).unwrap();
        assert_eq!((s3.n_vars, s3.equations.len()), (5 * 3 + 1 + 33, 44));
        assert_eq!(system_degree(&s3.equations), 3);
        let p = build_sym_chain_system(&fb.v_basis, irr, &x, &[3; 4], false, &st).unwrap();
        assert_eq!(p.n_vars, 5 * 4 + 33);
        // u(R) = ∞ at x = 1; arities outside {3, 4}; a basis not led by 1.
        let one = F2mElement::one(11);
        assert!(build_sym_chain_system(&fb.v_basis, irr, &one, &[4, 4], true, &st).is_none());
        assert!(build_sym_chain_system(&fb.v_basis, irr, &x, &[5], true, &st).is_none());
        let mut rev = fb.v_basis.clone();
        rev.reverse();
        assert!(build_sym_chain_system(&rev, irr, &x, &[4, 4], true, &st).is_none());
        assert!(meet_roots(&fb.v_basis, irr, &one, &[4, 4]).is_none());
        assert!(meet_roots(&fb.v_basis, irr, &x, &[3, 3, 3]).is_none());
        let o = SymChainOracle::new(&kc, &fb, &st).unwrap();
        assert!(o
            .decompose_all(
                &BinaryPoint::Infinity,
                5,
                ChainShape::S4Pair,
                ChainSolver::Meet
            )
            .is_none());
        assert!(o
            .decompose_all(&BinaryPoint::Infinity, 5, ChainShape::S3Links, f4())
            .is_none());
    }

    #[test]
    fn roots_in_field_match_exhaustive_evaluation() {
        let mut rng = StdRng::seed_from_u64(0x77);
        for n in [3u32, 5, 7, 11] {
            let kc = KoblitzCurve::new(1, n).unwrap();
            let gf = Gf2::new(&kc.curve.irreducible);
            let eval = |p: &[u64], x: u64| p.iter().rev().fold(0u64, |acc, &c| gf.mul(acc, x) ^ c);
            for trial in 0..60 {
                let mut p: Vec<u64> = (0..=4).map(|_| rng.gen_range(0..(1u64 << n))).collect();
                if trial % 3 == 0 {
                    // Plant roots: (X − r₁)(X − r₂)·(random quadratic).
                    let r1 = rng.gen_range(0..(1u64 << n));
                    let r2 = rng.gen_range(0..(1u64 << n));
                    p = pmul(&pmul(&[r1, 1], &[r2, 1], &gf), &p[..3], &gf);
                }
                let p = trim(p);
                if p.is_empty() {
                    continue;
                }
                let want: Vec<u64> = (0..(1u64 << n)).filter(|&x| eval(&p, x) == 0).collect();
                assert_eq!(roots_in_field(&p, &gf), want, "n={n} p={p:?}");
            }
        }
    }

    /// The meet solver returns exactly matrix-F4's root set of the same
    /// system, and every root satisfies it.
    #[test]
    fn meet_roots_equal_groebner_roots() {
        for &(a, n, ell, m) in &[
            (0u8, 7u32, 3usize, 5usize),
            (1, 9, 3, 5),
            (1, 7, 4, 5),
            (1, 11, 4, 5),
            (1, 9, 3, 4),
            (0, 5, 2, 5),
        ] {
            let (kc, st, fb) = instance(a, n, ell, 0x44 + u64::from(n));
            let irr = &kc.curve.irreducible;
            let arities = ChainShape::S4Pair.arities(m).unwrap();
            for t in targets(&kc, &fb, 0x55).iter().take(5) {
                let BinaryPoint::Affine { x, .. } = t else {
                    unreachable!()
                };
                let sys = build_sym_chain_system(&fb.v_basis, irr, x, &arities, true, &st).unwrap();
                let opts = SolveOptions {
                    engine: SolverEngine::default(),
                    max_solutions: usize::MAX,
                    node_budget: 1_000_000,
                    split_rule: split_rule_default(),
                };
                let (mut want, stats) =
                    solve_boolean_system_filtered(&sys.equations, sys.n_vars, &opts, |_| false);
                assert!(!stats.exhausted);
                want.sort_unstable();
                let (got, meet) = meet_roots(&fb.v_basis, irr, x, &arities).unwrap();
                assert_eq!(got, want, "a={a} n={n} l={ell} m={m}");
                assert_eq!(meet.roots as usize, got.len());
                for &r in &got {
                    assert!(sys.equations.iter().all(|e| e.eval(r) == 0));
                }
            }
        }
    }

    /// **The differential**: at `m = 5`, on random, planted, planted-via-`T`
    /// and `T` targets, every shape and solver returns exactly the
    /// brute-force set for its cuts; the folded `S₃` chain returns exactly
    /// the plain-`u` generic chain's set; the `[4, 4]` pair under meet and
    /// under F4 coincide.
    #[test]
    fn m5_decompositions_agree_with_generic_chain_and_reference() {
        let mut nonempty = 0;
        let mut differ = 0;
        for &(a, n, ell, seed) in &[
            (0u8, 7u32, 3usize, 1u64),
            (1, 7, 3, 2),
            (1, 9, 3, 3),
            (0, 9, 3, 4),
            (1, 7, 4, 5),
            (0, 5, 2, 6),
            (1, 5, 2, 7),
        ] {
            let (kc, st, fb) = instance(a, n, ell, seed);
            let o = SymChainOracle::new(&kc, &fb, &st).unwrap();
            for (k, (t, is_planted)) in targets_flagged(&kc, &fb, seed * 17).iter().enumerate() {
                let ctx = format!("a={a} n={n} l={ell} target {k}");
                let ref44 = reference_decompositions(&kc, &fb, t, 5, &[4, 4]).unwrap();
                let ref3 = reference_decompositions(&kc, &fb, t, 5, &[3; 4]).unwrap();
                let meet = o
                    .decompose_all(t, 5, ChainShape::S4Pair, ChainSolver::Meet)
                    .unwrap();
                let s4 = o.decompose_all(t, 5, ChainShape::S4Pair, f4()).unwrap();
                let s3 = o.decompose_all(t, 5, ChainShape::S3Links, f4()).unwrap();
                let plain = o.decompose_all(t, 5, ChainShape::PlainU, f4()).unwrap();
                for e in [&meet, &s4, &s3, &plain] {
                    assert!(e.complete, "{ctx}");
                    check_resums(&kc, &fb, t, &e.decompositions);
                }
                assert_eq!(meet.roots, s4.roots, "{ctx}");
                assert_eq!(meet.decompositions, ref44, "{ctx}: meet vs reference");
                assert_eq!(s4.decompositions, ref44, "{ctx}: F4 [4,4] vs reference");
                assert_eq!(s3.decompositions, ref3, "{ctx}: S3 links vs reference");
                assert_eq!(
                    plain.decompositions, s3.decompositions,
                    "{ctx}: folded vs generic"
                );
                nonempty += usize::from(!ref44.is_empty());
                differ += usize::from(ref44 != ref3);
                // Planted targets always decompose (some ordering of a
                // planted multiset avoids every degenerate cut here).
                if *is_planted {
                    assert!(!ref44.is_empty(), "{ctx}: planted");
                }
            }
        }
        eprintln!(
            "m5 differential: {nonempty} non-empty targets, {differ} with different cut sets"
        );
        assert!(nonempty >= 20, "{nonempty}");
        // The two cut patterns could differ on a degenerate target; on these
        // frozen instances they never do, so the specialised set is the
        // generic chain's set exactly.
        assert_eq!(differ, 0);
    }

    /// A wider, cheaper sweep: 24 random bases on four small curves, every
    /// target kind; the specialised meet against the brute-force set and
    /// against the generic folded `S₃` chain under F4 (equal wherever the
    /// two cut patterns' reference sets are).
    #[test]
    fn m5_sweep_meet_vs_generic_chain() {
        let (mut checked, mut equal, mut nonempty) = (0, 0, 0);
        for seed in 0..6u64 {
            for &(a, n, ell) in &[(0u8, 5u32, 2usize), (1, 5, 2), (0, 7, 3), (1, 7, 3)] {
                let (kc, st, fb) = instance(a, n, ell, 0x1000 + seed);
                let o = SymChainOracle::new(&kc, &fb, &st).unwrap();
                for t in targets(&kc, &fb, 0x2000 + seed) {
                    let ref44 = reference_decompositions(&kc, &fb, &t, 5, &[4, 4]).unwrap();
                    let ref3 = reference_decompositions(&kc, &fb, &t, 5, &[3; 4]).unwrap();
                    let meet = o
                        .decompose_all(&t, 5, ChainShape::Auto, ChainSolver::Meet)
                        .unwrap();
                    let s3 = o.decompose_all(&t, 5, ChainShape::S3Links, f4()).unwrap();
                    assert!(s3.complete);
                    check_resums(&kc, &fb, &t, &meet.decompositions);
                    assert_eq!(meet.decompositions, ref44, "a={a} n={n} seed={seed}");
                    assert_eq!(s3.decompositions, ref3, "a={a} n={n} seed={seed}");
                    if ref44 == ref3 {
                        assert_eq!(meet.decompositions, s3.decompositions);
                        equal += 1;
                    }
                    nonempty += usize::from(!ref44.is_empty());
                    checked += 1;
                }
            }
        }
        eprintln!("m5 sweep: {checked} targets, {nonempty} non-empty, {equal} with equal cut sets");
        assert!(checked >= 150 && nonempty >= 40, "{checked} {nonempty}");
        assert_eq!(
            equal, checked,
            "frozen instances: no degenerate cut differs"
        );
    }

    /// The single-relation oracle: every relation re-sums, and the verdict
    /// matches the full set (a decomposition of `R` itself ⇒ found).
    #[test]
    fn decompose_first_is_consistent_with_decompose_all() {
        for &(a, n, ell, seed) in &[(1u8, 9u32, 3usize, 8u64), (0, 7, 3, 9), (1, 11, 4, 10)] {
            let (kc, st, fb) = instance(a, n, ell, seed);
            let o = SymChainOracle::new(&kc, &fb, &st).unwrap();
            for t in targets(&kc, &fb, seed) {
                let all = o
                    .decompose_all(&t, 5, ChainShape::S4Pair, ChainSolver::Meet)
                    .unwrap();
                let direct = all.decompositions.iter().any(|d| !d.via_t);
                for (shape, solver) in [
                    (ChainShape::S4Pair, ChainSolver::Meet),
                    (ChainShape::S4Pair, f4()),
                    (ChainShape::S3Links, f4()),
                ] {
                    let first = o.decompose_first(&t, 5, shape, solver).unwrap();
                    assert!(first.complete);
                    if direct {
                        assert!(first.relation.is_some(), "{shape:?} missed a relation");
                    }
                    if let Some(rel) = &first.relation {
                        let sum = fb.sum(&kc, rel);
                        assert_eq!(sum, t, "{shape:?}");
                        if !first.used_t {
                            let mut s = rel.clone();
                            s.sort_unstable();
                            assert!(all.decompositions.contains(&Decomposition {
                                via_t: false,
                                indices: s
                            }));
                        }
                    }
                }
            }
        }
    }

    /// The dispatch hook: `m ≤ 4` under `Auto` is the existing oracle
    /// bit for bit; `m = 5` under `Auto` is the meet; an explicit shape is
    /// its F4 chain; past the generic chain's 64 unknowns only the
    /// specialised path runs.
    #[test]
    fn dispatch_routes() {
        let (kc, st, fb) = instance(1, 9, 3, 0x99);
        let engine = SolverEngine::default();
        let o = SymChainOracle::new(&kc, &fb, &st).unwrap();
        for t in subgroup_targets(&kc, 4, 0x98) {
            for m in [2usize, 3] {
                let d = symmetrised_decompose_dispatch(
                    &kc,
                    &fb,
                    &st,
                    &t,
                    m,
                    ChainShape::Auto,
                    engine,
                    50_000,
                )
                .unwrap();
                let e =
                    symmetrised_groebner_decompose(&kc, &fb, &st, &t, m, engine, 50_000).unwrap();
                assert_eq!(
                    (d.relation, d.effort, d.n_vars),
                    (e.relation, e.effort, e.n_vars)
                );
            }
            let d = symmetrised_decompose_dispatch(
                &kc,
                &fb,
                &st,
                &t,
                4,
                ChainShape::Auto,
                engine,
                50_000,
            )
            .unwrap();
            let e =
                chained_symmetrised_groebner_decompose(&kc, &fb, &st, &t, engine, 50_000).unwrap();
            assert_eq!(
                (d.relation, d.effort, d.n_vars),
                (e.relation, e.effort, e.n_vars)
            );
            let d = symmetrised_decompose_dispatch(
                &kc,
                &fb,
                &st,
                &t,
                5,
                ChainShape::Auto,
                engine,
                50_000,
            )
            .unwrap();
            let e = o
                .decompose_first(&t, 5, ChainShape::S4Pair, ChainSolver::Meet)
                .unwrap();
            assert_eq!(
                (d.relation, d.effort, d.n_vars),
                (e.relation, e.effort, e.n_vars)
            );
            let d = symmetrised_decompose_dispatch(
                &kc,
                &fb,
                &st,
                &t,
                5,
                ChainShape::S3Links,
                engine,
                50_000,
            )
            .unwrap();
            let e = o
                .decompose_first(
                    &t,
                    5,
                    ChainShape::S3Links,
                    ChainSolver::Groebner {
                        engine,
                        node_budget: 50_000,
                    },
                )
                .unwrap();
            assert_eq!(
                (d.relation, d.effort, d.n_vars),
                (e.relation, e.effort, e.n_vars)
            );
        }
        // n ≥ 19, ℓ = 3: the S₃ chains need 5·2 + 1 + 3n ≥ 68 and
        // 15 + 3n ≥ 72 unknowns and decline; the pair needs 11 + n and the
        // meet decides every target, against the brute-force set.
        let n = [19u32, 23, 25, 27]
            .into_iter()
            .find(|&n| KoblitzCurve::new(1, n).is_some())
            .expect("a Koblitz curve past the generic chain's cap");
        let (kc, st, fb) = instance(1, n, 3, 0x21);
        let o = SymChainOracle::new(&kc, &fb, &st).unwrap();
        for t in targets(&kc, &fb, 0x21) {
            assert!(o.system(&t, 5, ChainShape::S3Links).is_none());
            assert!(o.system(&t, 5, ChainShape::PlainU).is_none());
            let all = o
                .decompose_all(&t, 5, ChainShape::Auto, ChainSolver::Meet)
                .unwrap();
            assert_eq!(all.n_vars, 11 + n as usize);
            assert_eq!(
                all.decompositions,
                reference_decompositions(&kc, &fb, &t, 5, &[4, 4]).unwrap()
            );
            let d = symmetrised_decompose_dispatch(
                &kc,
                &fb,
                &st,
                &t,
                5,
                ChainShape::Auto,
                engine,
                1_000,
            )
            .unwrap();
            assert!(d.complete);
            assert_eq!(
                d.relation.is_some(),
                all.decompositions.iter().any(|x| !x.via_t) || d.used_t
            );
        }
    }

    /// The `m = 5` meet charges its root-finds against the dispatch's
    /// `node_budget`: under too small a budget it reports no relation and
    /// `complete = false` (never a refutation); at its exact cost it is the
    /// unbudgeted meet.
    #[test]
    fn the_meet_respects_the_node_budget() {
        let (kc, st, fb) = instance(1, 9, 3, 0x77);
        let engine = SolverEngine::default();
        let o = SymChainOracle::new(&kc, &fb, &st).unwrap();
        let mut found = 0;
        for t in targets(&kc, &fb, 0x77) {
            let full = o
                .decompose_first(&t, 5, ChainShape::S4Pair, ChainSolver::Meet)
                .unwrap();
            assert!(full.complete);
            found += usize::from(full.relation.is_some());
            let cost = full.effort as usize;
            let dispatch = |budget| {
                symmetrised_decompose_dispatch(
                    &kc,
                    &fb,
                    &st,
                    &t,
                    5,
                    ChainShape::Auto,
                    engine,
                    budget,
                )
                .unwrap()
            };
            let tiny = dispatch(cost - 1);
            assert!(!tiny.complete);
            assert!(tiny.relation.is_none());
            assert_eq!(tiny.effort, 0);
            let ample = dispatch(cost);
            assert!(ample.complete);
            assert_eq!(
                (ample.relation, ample.used_t, ample.effort),
                (full.relation, full.used_t, full.effort)
            );
        }
        assert!(found > 0, "no target had a relation to lose");
    }
}
