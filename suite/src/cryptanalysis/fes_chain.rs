//! **Gray-code exhaustive search over summand bits for chained Semaev
//! systems, `m ≥ 3`** — the specialised path behind
//! [`crate::cryptanalysis::mq_fes::mq_fes_decompose`] once there are three
//! or more summands.
//!
//! The generic path Weil-descends the chain
//!
//! ```text
//!     S₃(x₀, x₁, u₀) = 0,  S₃(u₀, x₂, u₁) = 0,  …,  S₃(u_{m−3}, x_{m−1}, x_R) = 0
//! ```
//!
//! into a cubic Boolean system over `m·ℓ` summand bits and `(m−2)·n`
//! intermediate bits (`koblitz_groebner::build_decomposition_system`,
//! capped at 64 unknowns) and hands it to Gröbner, SAT or WDSat.  Here
//! the chain is solved *over the field* instead, branching on summand
//! bits only (as `wide_groebner` does), because once the summands left of
//! a link are fixed every link is a quadratic in one unknown:
//!
//! ```text
//!     S₃(w, x, u) = (w + x)²·u² + (w·x)·u + (w·x)² + b
//! ```
//!
//! - **Gray order, incremental coefficients.**  Summand `x_k` walks its
//!   `2^ℓ` coordinate vectors in Gray order, so each step adds one basis
//!   element `v_j` and the link's coefficients move by XORs alone:
//!   `A ^= v_j²`, `B ^= w·v_j`, `B² ^= (w·v_j)²`, with the `ℓ` products
//!   `w·v_j` taken once per incoming `w`.  The root `u` then costs one
//!   inversion and an Artin–Schreier solve (a linear map), never a
//!   symbolic system.
//! - **Last link by table.**  The final link only involves `x_{m−1}` and
//!   the fixed `x_R`, so the set `{w : ∃ y ∈ V, S₃(w, y, x_R) = 0}` is
//!   tabulated once per target (`2^ℓ` quadratic solves) and each leaf is
//!   a probe.  Leaves are the `(m−1)`-tuples `x₀ … x_{m−2}`.
//! - **Symmetry.**  [`Symmetry::Sorted`] only walks tuples whose summand
//!   Gray ranks are non-decreasing (and keeps last summands of rank at
//!   least the previous one), which divides the leaves by about
//!   `(m−1)!` and the roots by about `m!`.  [`Symmetry::Full`] walks every
//!   ordering and returns **exactly** the generic system's roots.
//!
//! ## What is returned, and in what order
//!
//! A root is the generic system's Boolean solution in structured form
//! ([`ChainRoot`]: summand coordinate vectors and intermediate abscissae;
//! [`ChainRoot::pack`] gives the generic `u64` assignment).
//!
//! - `Full`: the root **set** equals the generic system's (tests compare
//!   against exhaustive evaluation of the generic equations).
//! - `Sorted`: the root set equals the generic roots whose summand Gray
//!   ranks are non-decreasing.  Every *non-degenerate* decomposition —
//!   one whose signed summands have no non-empty proper sub-multiset
//!   summing to `O` — has such a root (its sorted ordering's partial sums
//!   are rational and non-zero, so its intermediates exist), so the
//!   lifted decomposition sets agree on non-degenerate decompositions.
//!   A degenerate one (`R = Q + P − P`, say) can be missed when the
//!   cancelling summands sort first; the generic path finds those
//!   through another ordering.
//!
//! Enumeration order (both modes): lexicographic in
//! `(r₀, r₁, u₀, r₂, u₁, …, r_{m−2}, u_{m−3}, c_{m−1})`, where `r_k` is the
//! Gray rank of summand `k`'s coordinate vector, `u_k` an intermediate
//! abscissa as an integer, and `c_{m−1}` the last summand's coordinate
//! vector as an integer.  [`fes_chain_decompose`] returns the lift of
//! the first root in that order that lifts; tests pin that this is the
//! same decomposition as the first lift of the generic roots sorted by
//! the same key.
//!
//! The path refuses (returns `None` from [`ChainFes::new`]) for `n < 2`,
//! `n > 63`, `ℓ > 32`, `m < 3`, `b = 0`, or a linearly dependent basis;
//! the caller then keeps its generic behaviour.

use crate::binary_ecc::{BinaryPoint, F2mElement, IrreduciblePoly};
use crate::cryptanalysis::koblitz_groebner::FieldStructure;
use crate::cryptanalysis::koblitz_index_calculus::{
    lift_candidate, FrobeniusFactorBase, KoblitzCurve, SatDecompositionStats,
};
use crate::cryptanalysis::semaev_decomp::Gf2;
use num_bigint::BigUint;
use std::collections::HashMap;
use std::ops::ControlFlow;

/// Leaves (summand tuples `x₀ … x_{m−2}`) above which
/// [`fes_chain_decompose`] refuses rather than start a search it cannot
/// finish: `2^40`.
pub const MAX_LEAVES: u128 = 1 << 40;

/// Which orderings of the summands the search walks.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Symmetry {
    /// Every ordering: exactly the generic system's roots.
    Full,
    /// Non-decreasing summand Gray ranks only (see the module docs).
    Sorted,
}

/// One root of the chained system, in structured form.
#[derive(Clone, Debug, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub struct ChainRoot {
    /// Coordinate vector of each summand over the subspace basis (bit `t`
    /// is the coefficient of `basis[t]`), `m` of them.
    pub coords: Vec<u64>,
    /// The intermediate abscissae `u₀ … u_{m−3}`, polynomial-basis bits.
    pub inter: Vec<u64>,
}

impl ChainRoot {
    /// The generic system's Boolean assignment: summand `i`'s bits at
    /// `i·ℓ …`, intermediate `k`'s at `m·ℓ + k·n …` (the layout of
    /// `koblitz_groebner::build_decomposition_system`).  `None` past 64
    /// unknowns.
    pub fn pack(&self, ell: usize, n: usize) -> Option<u64> {
        let m = self.coords.len();
        if m * ell + self.inter.len() * n > 64 {
            return None;
        }
        let mut out = 0u64;
        for (i, &c) in self.coords.iter().enumerate() {
            out |= c << (i * ell);
        }
        for (k, &u) in self.inter.iter().enumerate() {
            out |= u << (m * ell + k * n);
        }
        Some(out)
    }
}

/// Work counters of one search (machine independent).
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct ChainCounters {
    /// Leaf visits: `(x₀ … x_{m−2}, u₀ … u_{m−4})` paths that reached the
    /// last intermediate link.
    pub leaves: u64,
    /// Quadratic solves for intermediates.
    pub solves: u64,
    /// Probes of the last-link table.
    pub probes: u64,
    /// Roots handed to the callback.
    pub roots: u64,
}

/// An `F₂`-linear map on at most 64 bits, applied a byte at a time.
#[derive(Clone, Debug)]
struct LinMap {
    tabs: Vec<[u64; 256]>,
}

impl LinMap {
    /// The map sending input bit `i` to `cols[i]`.
    fn new(cols: &[u64]) -> Self {
        let chunks = cols.len().div_ceil(8).max(1);
        let mut tabs = vec![[0u64; 256]; chunks];
        for (c, tab) in tabs.iter_mut().enumerate() {
            for v in 1usize..256 {
                let bit = c * 8 + v.trailing_zeros() as usize;
                let col = cols.get(bit).copied().unwrap_or(0);
                tab[v] = tab[v & (v - 1)] ^ col;
            }
        }
        Self { tabs }
    }

    #[inline(always)]
    fn apply(&self, mut x: u64) -> u64 {
        let mut acc = 0u64;
        for tab in &self.tabs {
            acc ^= tab[(x & 0xFF) as usize];
            x >>= 8;
        }
        acc
    }
}

/// A linear map `x ↦ Σ x_i · images[i]` (on `n` bits) in reduced row
/// echelon form, for preimages.  Returns `(P, rank)` where `P` is linear
/// and `images·P(y) = y` for every `y` in the image.
fn preimage_map(images: &[u64], n: usize) -> (LinMap, usize) {
    // Rows `(vector, combination)`, pivot at the vector's top bit.
    let mut rows: Vec<(u64, u64)> = Vec::new();
    for (i, &v) in images.iter().enumerate() {
        let (mut v, mut c) = (v, 1u64 << i);
        for &(rv, rc) in &rows {
            let p = 63 - rv.leading_zeros();
            if (v >> p) & 1 == 1 {
                v ^= rv;
                c ^= rc;
            }
        }
        if v != 0 {
            rows.push((v, c));
            rows.sort_unstable_by_key(|r| std::cmp::Reverse(r.0));
        }
    }
    // Back-substitute to RREF: each pivot column holds one 1.
    for i in 0..rows.len() {
        let p = 63 - rows[i].0.leading_zeros();
        for j in 0..rows.len() {
            if j != i && (rows[j].0 >> p) & 1 == 1 {
                rows[j].0 ^= rows[i].0;
                rows[j].1 ^= rows[i].1;
            }
        }
    }
    let mut cols = vec![0u64; n];
    for &(v, c) in &rows {
        cols[(63 - v.leading_zeros()) as usize] = c;
    }
    (LinMap::new(&cols), rows.len())
}

/// The specialised search for one subspace basis, curve constant and
/// number of summands; reusable across targets.
#[derive(Clone, Debug)]
pub struct ChainFes {
    gf: Gf2,
    n: usize,
    ell: usize,
    m: usize,
    b: u64,
    basis: Vec<u64>,
    basis_sq: Vec<u64>,
    /// `y ↦ coordinates over the basis` in the low `ℓ` bits, a non-zero
    /// syndrome above them iff `y ∉ V`.
    coords: LinMap,
    sqrt: LinMap,
    /// A solution of `t² + t = δ` for every `δ` of trace zero.
    artin: LinMap,
    trace_mask: u64,
}

/// `F2mElement` → polynomial-basis bits.
fn bits(e: &F2mElement) -> u64 {
    e.raw_bits().first().copied().unwrap_or(0)
}

/// Gray rank of a Gray code word: the `r` with `r ^ (r >> 1) = c`.
#[inline(always)]
pub fn gray_rank(c: u64) -> u64 {
    let mut r = c;
    r ^= r >> 1;
    r ^= r >> 2;
    r ^= r >> 4;
    r ^= r >> 8;
    r ^= r >> 16;
    r ^= r >> 32;
    r
}

impl ChainFes {
    /// `None` when the path does not apply (see the module docs).
    pub fn new(
        basis: &[F2mElement],
        b: &F2mElement,
        m: usize,
        irr: &IrreduciblePoly,
    ) -> Option<Self> {
        let n = irr.degree as usize;
        let ell = basis.len();
        if !(2..=63).contains(&n) || m < 3 || ell == 0 || ell > 32 || ell > n || b.is_zero() {
            return None;
        }
        let gf = Gf2::new(irr);
        let basis: Vec<u64> = basis.iter().map(bits).collect();
        let mask = (1u64 << n) - 1;
        if basis.iter().any(|&v| v & !mask != 0) {
            return None;
        }
        // Extend the basis by unit vectors to a basis of F_2^n; its
        // preimage map gives coordinates (low ℓ bits) and the syndrome.
        let mut full = basis.clone();
        let (_, rank) = preimage_map(&full, n);
        if rank != ell {
            return None;
        }
        for i in 0..n {
            full.push(1u64 << i);
            if preimage_map(&full, n).1 != full.len() {
                full.pop();
            }
        }
        debug_assert_eq!(full.len(), n);
        let (coords, _) = preimage_map(&full, n);
        let squares: Vec<u64> = (0..n).map(|i| gf.sqr(1u64 << i)).collect();
        let (sqrt, _) = preimage_map(&squares, n);
        let artin_images: Vec<u64> = (0..n).map(|i| gf.sqr(1u64 << i) ^ (1u64 << i)).collect();
        let (artin, artin_rank) = preimage_map(&artin_images, n);
        debug_assert_eq!(artin_rank, n - 1);
        let mut trace_mask = 0u64;
        for i in 0..n {
            let mut t = 1u64 << i;
            let mut acc = t;
            for _ in 1..n {
                t = gf.sqr(t);
                acc ^= t;
            }
            debug_assert!(acc <= 1);
            trace_mask |= acc << i;
        }
        let basis_sq = basis.iter().map(|&v| gf.sqr(v)).collect();
        Some(Self {
            gf,
            n,
            ell,
            m,
            b: bits(b),
            basis,
            basis_sq,
            coords,
            sqrt,
            artin,
            trace_mask,
        })
    }

    /// Extension degree.
    pub fn n(&self) -> usize {
        self.n
    }

    /// Subspace dimension.
    pub fn ell(&self) -> usize {
        self.ell
    }

    /// Number of summands.
    pub fn m(&self) -> usize {
        self.m
    }

    /// Summand tuples `x₀ … x_{m−2}` in the search space.  For `m = 3`
    /// the walk's [`ChainCounters::leaves`] equals it; for longer chains a
    /// tuple whose intermediate link has no root is pruned and one whose
    /// links have two roots is visited once per root path, so the counter
    /// is at most `2^{m−3}` times this.
    pub fn leaves(&self, sym: Symmetry) -> u128 {
        let q = 1u128 << self.ell;
        let k = (self.m - 1) as u128;
        match sym {
            Symmetry::Full => (0..k).fold(1u128, |acc, _| acc.saturating_mul(q)),
            // Multisets of size m − 1 from q values: C(q + k − 1, k).
            Symmetry::Sorted => {
                let mut acc = 1u128;
                for i in 0..k {
                    acc = acc.saturating_mul(q + i) / (i + 1);
                }
                acc
            }
        }
    }

    /// The field element with coordinate vector `c`.
    #[inline]
    pub fn span(&self, c: u64) -> u64 {
        self.basis
            .iter()
            .enumerate()
            .filter(|(t, _)| (c >> t) & 1 == 1)
            .fold(0, |acc, (_, &v)| acc ^ v)
    }

    /// The roots, in increasing order, of `A·y² + B·y + C = 0` with
    /// `C = B² + b` (so `A = B = 0` has none, as `b ≠ 0`).
    #[inline(always)]
    fn solve(&self, a: u64, bb: u64, c: u64) -> ([u64; 2], usize) {
        let gf = &self.gf;
        if a == 0 {
            if bb == 0 {
                return ([0, 0], 0);
            }
            return ([gf.mul(c, gf.inv(bb)), 0], 1);
        }
        if bb == 0 {
            return ([self.sqrt.apply(gf.mul(c, gf.inv(a))), 0], 1);
        }
        // y = (B/A)·t with t² + t = A·C/B².  One inversion d = 1/(A·B²):
        // 1/A = B²·d and 1/B² = A·d.
        let b2 = gf.sqr(bb);
        let d = gf.inv(gf.mul(a, b2));
        let delta = gf.mul(gf.mul(gf.sqr(a), c), d);
        if (delta & self.trace_mask).count_ones() & 1 == 1 {
            return ([0, 0], 0);
        }
        let t = self.artin.apply(delta);
        let k = gf.mul(gf.mul(bb, b2), d);
        let y0 = gf.mul(k, t);
        let y1 = y0 ^ k;
        ([y0.min(y1), y0.max(y1)], 2)
    }

    /// `S₃(w, x, u)` at field points (for checks).
    pub fn s3(&self, w: u64, x: u64, u: u64) -> u64 {
        let gf = &self.gf;
        let p = gf.mul(w, x);
        gf.mul(gf.sqr(w ^ x), gf.sqr(u)) ^ gf.mul(p, u) ^ gf.sqr(p) ^ self.b
    }

    /// The last-link table for `x_r`: every `(w, c)` with `c` a
    /// coordinate vector and `S₃(w, span(c), x_r) = 0`.
    fn last_link(&self, x_r: u64) -> LastLinkTable {
        let gf = &self.gf;
        let q = 1u64 << self.ell;
        let xr2 = gf.sqr(x_r);
        let mut entries: Vec<(u64, u64)> = Vec::with_capacity(2 * q as usize);
        let mut c = 0u64;
        let mut y = 0u64;
        for r in 0..q {
            if r > 0 {
                let j = r.trailing_zeros() as usize;
                c ^= 1 << j;
                y ^= self.basis[j];
            }
            let a = gf.sqr(y) ^ xr2;
            let bb = gf.mul(y, x_r);
            let (ws, k) = self.solve(a, bb, gf.sqr(bb) ^ self.b);
            for &w in &ws[..k] {
                entries.push((w, c));
            }
        }
        LastLinkTable::new(entries)
    }

    /// Walk every root for target abscissa `x_r` in the documented order,
    /// stopping when `f` breaks.
    pub fn for_each_root<F>(&self, x_r: u64, sym: Symmetry, mut f: F) -> ChainCounters
    where
        F: FnMut(&ChainRoot) -> ControlFlow<()>,
    {
        let table = self.last_link(x_r);
        let mut st = Walk {
            root: ChainRoot {
                coords: vec![0; self.m],
                inter: vec![0; self.m - 2],
            },
            ranks: vec![0; self.m],
            counters: ChainCounters::default(),
            wv: vec![vec![0; self.ell]; self.m],
            wv2: vec![vec![0; self.ell]; self.m],
        };
        let q = 1u64 << self.ell;
        let mut c = 0u64;
        let mut x0 = 0u64;
        for r in 0..q {
            if r > 0 {
                let j = r.trailing_zeros() as usize;
                c ^= 1 << j;
                x0 ^= self.basis[j];
            }
            st.root.coords[0] = c;
            st.ranks[0] = r;
            if self
                .level(1, x0, r, sym, &table, &mut st, &mut f)
                .is_break()
            {
                break;
            }
        }
        st.counters
    }

    /// Every root, in the documented order.
    pub fn roots(&self, x_r: u64, sym: Symmetry) -> (Vec<ChainRoot>, ChainCounters) {
        let mut out = Vec::new();
        let counters = self.for_each_root(x_r, sym, |r| {
            out.push(r.clone());
            ControlFlow::Continue(())
        });
        (out, counters)
    }

    /// Summand `k ≥ 1` against incoming abscissa `w`, solving for
    /// `u_{k−1}`.
    #[allow(clippy::too_many_arguments)]
    fn level<F>(
        &self,
        k: usize,
        w: u64,
        prev_rank: u64,
        sym: Symmetry,
        table: &LastLinkTable,
        st: &mut Walk,
        f: &mut F,
    ) -> ControlFlow<()>
    where
        F: FnMut(&ChainRoot) -> ControlFlow<()>,
    {
        let gf = &self.gf;
        let q = 1u64 << self.ell;
        let start = match sym {
            Symmetry::Full => 0,
            Symmetry::Sorted => prev_rank,
        };
        {
            let (wv, wv2) = (&mut st.wv[k], &mut st.wv2[k]);
            for j in 0..self.ell {
                wv[j] = gf.mul(w, self.basis[j]);
                wv2[j] = gf.sqr(wv[j]);
            }
        }
        let mut c = start ^ (start >> 1);
        let x = self.span(c);
        let mut a = gf.sqr(w) ^ gf.sqr(x);
        let mut bb = gf.mul(w, x);
        let mut b2 = gf.sqr(bb);
        let last = k == self.m - 2;
        for r in start..q {
            if r > start {
                let j = r.trailing_zeros() as usize;
                c ^= 1 << j;
                a ^= self.basis_sq[j];
                bb ^= st.wv[k][j];
                b2 ^= st.wv2[k][j];
            }
            st.root.coords[k] = c;
            st.ranks[k] = r;
            st.counters.solves += 1;
            if last {
                st.counters.leaves += 1;
            }
            let (us, cnt) = self.solve(a, bb, b2 ^ self.b);
            for &u in &us[..cnt] {
                st.root.inter[k - 1] = u;
                if last {
                    st.counters.probes += 1;
                    for &cl in table.get(u) {
                        if sym == Symmetry::Sorted && gray_rank(cl) < r {
                            continue;
                        }
                        st.root.coords[k + 1] = cl;
                        st.counters.roots += 1;
                        f(&st.root)?;
                    }
                } else {
                    self.level(k + 1, u, r, sym, table, st, f)?;
                }
            }
        }
        ControlFlow::Continue(())
    }

    /// Whether field element `y` lies in the span, and its coordinates.
    pub fn coordinates(&self, y: u64) -> Option<u64> {
        let v = self.coords.apply(y);
        (v >> self.ell == 0).then_some(v)
    }
}

/// Mutable state of one walk.
struct Walk {
    root: ChainRoot,
    ranks: Vec<u64>,
    counters: ChainCounters,
    /// Per level: `w·v_j` and its square.
    wv: Vec<Vec<u64>>,
    wv2: Vec<Vec<u64>>,
}

/// `w ↦` coordinate vectors `c` (ascending) of the last summand.
/// Open addressing on `w`, linear probing, values in one array.
struct LastLinkTable {
    keys: Vec<u64>,
    /// `(start, len)` into `values`; `len == 0` marks an empty slot.
    spans: Vec<(u32, u32)>,
    values: Vec<u64>,
    shift: u32,
}

impl LastLinkTable {
    fn new(mut entries: Vec<(u64, u64)>) -> Self {
        entries.sort_unstable();
        entries.dedup();
        let distinct = entries.windows(2).filter(|p| p[0].0 != p[1].0).count()
            + usize::from(!entries.is_empty());
        let size = (2 * distinct).next_power_of_two().max(2);
        let bits = size.trailing_zeros();
        let mut t = Self {
            keys: vec![0; size],
            spans: vec![(0, 0); size],
            values: entries.iter().map(|e| e.1).collect(),
            shift: 64 - bits,
        };
        let mut i = 0;
        while i < entries.len() {
            let w = entries[i].0;
            let mut j = i;
            while j < entries.len() && entries[j].0 == w {
                j += 1;
            }
            let mut slot = t.slot(w);
            while t.spans[slot].1 != 0 {
                slot = (slot + 1) & (size - 1);
            }
            t.keys[slot] = w;
            t.spans[slot] = (i as u32, (j - i) as u32);
            i = j;
        }
        t
    }

    #[inline(always)]
    fn slot(&self, w: u64) -> usize {
        (w.wrapping_mul(0x9E37_79B9_7F4A_7C15) >> self.shift) as usize
    }

    #[inline(always)]
    fn get(&self, w: u64) -> &[u64] {
        let mask = self.keys.len() - 1;
        let mut slot = self.slot(w);
        loop {
            let (start, len) = self.spans[slot];
            if len == 0 {
                return &[];
            }
            if self.keys[slot] == w {
                return &self.values[start as usize..(start + len) as usize];
            }
            slot = (slot + 1) & mask;
        }
    }
}

/// Counters of [`fes_chain_decompose`] beyond [`SatDecompositionStats`].
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct FesChainStats {
    pub counters: ChainCounters,
    /// Roots whose lift was tried.
    pub lifts: u64,
}

/// [`fes_chain_decompose`] with an explicit symmetry mode, returning the
/// walk's counters too.  `None` when the path does not apply (the caller
/// keeps its generic behaviour).
#[allow(clippy::type_complexity)]
pub fn fes_chain_decompose_with(
    kc: &KoblitzCurve,
    fb: &FrobeniusFactorBase,
    index_of: &HashMap<(BigUint, BigUint), usize>,
    target: &BinaryPoint,
    m: usize,
    sym: Symmetry,
) -> Option<(Option<Vec<usize>>, SatDecompositionStats, FesChainStats)> {
    let fes = ChainFes::new(&fb.subspace_basis, &kc.curve.b, m, &kc.curve.irreducible)?;
    if fes.leaves(sym) > MAX_LEAVES {
        return None;
    }
    let mut stats = SatDecompositionStats {
        solver_calls: 1,
        ..SatDecompositionStats::default()
    };
    let mut extra = FesChainStats::default();
    let x_r = match target {
        BinaryPoint::Affine { x, .. } => bits(x),
        BinaryPoint::Infinity => return Some((None, stats, extra)),
    };
    let n = kc.n;
    let mut found = None;
    extra.counters = fes.for_each_root(x_r, sym, |root| {
        stats.models += 1;
        extra.lifts += 1;
        let xs: Vec<F2mElement> = root
            .coords
            .iter()
            .map(|&c| F2mElement::from_biguint(&BigUint::from(fes.span(c)), n))
            .collect();
        match lift_candidate(kc, fb, index_of, &xs, target) {
            Some(idxs) => {
                found = Some(idxs);
                ControlFlow::Break(())
            }
            None => ControlFlow::Continue(()),
        }
    });
    if found.is_none() {
        // The walk was exhaustive: no (non-degenerate, for `Sorted`)
        // decomposition exists.
        stats.refuted = true;
    }
    Some((found, stats, extra))
}

/// The `m ≥ 3` specialised decomposition oracle: [`Symmetry::Sorted`]
/// Gray-code search, first liftable root in the documented order.
///
/// Returns `None` when the path does not apply (see [`ChainFes::new`]
/// and [`MAX_LEAVES`]); `mq_fes_decompose` then reports the attempt as
/// exhausted, as it did for every `m ≥ 3` before this path existed.
/// `refuted` means the exhaustive walk found no liftable root, i.e. no
/// non-degenerate decomposition exists.  `_st` is accepted for the
/// generic signature and not needed: the search works on field elements.
pub fn fes_chain_decompose(
    kc: &KoblitzCurve,
    fb: &FrobeniusFactorBase,
    index_of: &HashMap<(BigUint, BigUint), usize>,
    _st: &FieldStructure,
    target: &BinaryPoint,
    m: usize,
) -> Option<(Option<Vec<usize>>, SatDecompositionStats)> {
    fes_chain_decompose_with(kc, fb, index_of, target, m, Symmetry::Sorted).map(|(d, s, _)| (d, s))
}

#[cfg(test)]
#[path = "fes_chain_tests.rs"]
mod tests;
