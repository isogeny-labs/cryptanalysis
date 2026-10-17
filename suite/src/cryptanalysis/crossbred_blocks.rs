//! # Crossbred and XL with `(D, k)` read off the summand blocks.
//!
//! [`crate::cryptanalysis::crossbred`] splits the unknowns of a Boolean
//! system into `k` enumerated and `n − k` solved ones, and the default
//! the Koblitz decomposition oracle used was `k = n_vars / 2` at the
//! system's own degree `D` — a split that ignores what the variables
//! *are*.  A Weil-descended Semaev chain is not an arbitrary system.  Its
//! unknowns come in **blocks**: the `ℓ` coordinates of each summand
//! `X_0 … X_{m−1}` and the `n` coordinates of each intermediate
//! abscissa `U_0 … U_{m−3}` (the layout of
//! [`crate::cryptanalysis::koblitz_groebner::build_decomposition_system`]).
//! Every equation is the descent of one `S₃` link, and `S₃` has degree
//! `≤ 2` in each argument with squaring `F_2`-linear, so every monomial
//! of every equation holds **at most one variable from each block**.
//! Fix the right blocks and the rest of the system is *linear*, with no
//! Macaulay lift at all.
//!
//! This module reads that structure off the equations and uses it two
//! ways.
//!
//! ## Crossbred with a block plan ([`solve_crossbred_blocks`])
//!
//! Build the **block graph**: one vertex per block, an edge between two
//! blocks that share a monomial, a self-loop on a block with two of its
//! own variables in one monomial.  A set `S` of blocks may be left
//! unenumerated with every equation of specialised degree `≤ 1` exactly
//! when `S` is an independent set without self-loops.  The plan takes
//! the one with the most variables ([`plan_crossbred`]; ties prefer
//! intermediate blocks — *keep the intermediates linear* — then the set
//! whose lowest variable is highest, so the longest prefix of low
//! variables stays enumerated as in the generic split, then the smallest
//! block bitmask), so
//!
//! ```text
//!     k = n_vars − max { |S| : S independent },     D = deg(system),
//! ```
//!
//! and the variables are renamed so the enumerated ones come first (the
//! crossbred module always enumerates `0 … k−1`).  At that `(D, k)` the
//! crossbred space already contains every input equation, so the default
//! preprocessing is the identity ([`Preprocess::Direct`]); the Macaulay
//! extraction at the same `(D, k)` ([`Preprocess::Macaulay`]) is kept as
//! an option and finds the same solutions.  For the chain:
//!
//! | `m` | solved blocks | `k` |
//! |---:|---|---|
//! | 2 | `X_1` | `ℓ` |
//! | 3 | `U_0` (if `n ≥ 2ℓ`) | `3ℓ` |
//! | 4 | `{U_0, X_3}` (if `n ≥ 2ℓ`) | `3ℓ + n` |
//!
//! ## XL by block elimination ([`solve_block_xl`])
//!
//! Simultaneous linearity is stronger than needed.  The chain is
//! *triangular*: with `X_0, X_1` fixed, link 0 is linear in `U_0`; with
//! `U_{j−1}` and `X_{j+1}` fixed, link `j` is linear in `U_j`; with
//! `U_{m−3}` fixed the last link is linear in `X_{m−1}`.  So enumerate
//! the summand blocks `X_0 … X_{m−2}` stage by stage and run XL at
//! degree `D = 1` — plain linearisation — on each intermediate block in
//! turn, then on `X_{m−1}`:
//!
//! ```text
//!     k = (m − 1) · ℓ   enumerated in total,     D = 1 per stage,
//! ```
//!
//! independent of `n`.  The plan ([`plan_block_xl`]) checks the
//! linearity of every equation it assigns to a stage against the actual
//! monomials; an equation that is not linear where expected is left to
//! the final verification rather than trusted.
//!
//! ## Exactness
//!
//! Both solvers enumerate their enumerated blocks completely and solve
//! the remaining unknowns as full affine solution spaces of conditions
//! every solution satisfies, so they return **every** root of the
//! system unless `exhausted` is set (a per-point solution space above
//! `max_kernel_dim`).  Every root is re-checked against the original
//! equations before it is returned.  Roots come back **sorted ascending
//! as point masks** (bit `i` = variable `i` of the input system), and
//! [`order_like_generic`] reorders them into the order the generic
//! crossbred path would report them.
//!
//! ## Honest scope
//!
//! - The layout is the chain layout of `build_decomposition_system`; a
//!   system in another variable order (for example the interleaved one
//!   the Gröbner engines take) must be permuted back first.
//! - The block-graph search is exhaustive over block subsets and is
//!   refused above [`MAX_PLAN_BLOCKS`] blocks (`m ≤ 11`).
//! - For `m = 2` the crossbred plan has `k = ℓ = n_vars / 2`, the same
//!   `k` as the generic split: it is a constant-factor gain there, not an
//!   algorithmic one.  For `m = 4` the crossbred plan has `k = 3ℓ + n`,
//!   larger than the generic split's, and was slower than it when
//!   measured on `K_1/2^7`; [`choose_block_solver`] takes block XL there
//!   (it enumerates fewer variables), so the crossbred plan is not
//!   dispatched for `m ≥ 3` on such systems.
//! - An exhausted search is never used to pick a decomposition
//!   (`decompose_via_blocks` defers to the generic path), because it
//!   skips branches that may hold an earlier root.
//! - Nothing here changes the asymptotic cost of the decomposition: it is
//!   still exponential in `ℓ`.  What changes is which exponent: `2^k`
//!   with `k` set by the blocks instead of `n_vars / 2`.

use crate::cryptanalysis::crossbred::{
    extract_crossbred, solve_crossbred, CrossbredParams, CrossbredSystem, ExtractStats,
    SearchOptions, SearchStats,
};
use crate::cryptanalysis::koblitz_groebner::{permute_mask, permute_poly, DecompositionSystem};
use crate::cryptanalysis::pq_groebner_f2::{F2BoolMono, F2BoolPoly};

/// Most blocks the exhaustive block-graph search accepts.
pub const MAX_PLAN_BLOCKS: usize = 20;

/// Bitmask of the low `k` bits, safe at `k = 64`.
fn mask_of(k: usize) -> u64 {
    if k >= 64 {
        u64::MAX
    } else {
        (1u64 << k) - 1
    }
}

// ── The layout ─────────────────────────────────────────────────────

/// What a block of unknowns stands for.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum BlockKind {
    /// The `ℓ` subspace coordinates of summand `i`.
    Summand(usize),
    /// The `n` field coordinates of intermediate abscissa `U_i`.
    Intermediate(usize),
}

/// One block: a contiguous range of variables.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Block {
    /// What the block stands for.
    pub kind: BlockKind,
    /// First variable of the block.
    pub first: usize,
    /// Number of variables.
    pub len: usize,
}

impl Block {
    /// The block's variables as a mask.
    pub fn mask(&self) -> u64 {
        mask_of(self.len) << self.first
    }
}

/// The block layout of a Semaev chain system: summands `X_0 … X_{m−1}`
/// of `ℓ` unknowns each at `i·ℓ`, then intermediates `U_0 … U_{m−3}` of
/// `n` unknowns each at `m·ℓ + i·n`.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct SummandBlocks {
    /// Number of summands.
    pub m: usize,
    /// Unknowns per summand.
    pub ell: usize,
    /// Unknowns per intermediate (the field degree); `0` when `m = 2`.
    pub n: usize,
    /// Total unknowns.
    pub n_vars: usize,
}

impl SummandBlocks {
    /// The layout of an `m`-summand chain with `ℓ` unknowns per summand
    /// and `n_vars` unknowns in all, or `None` if `n_vars` does not
    /// decompose as `m·ℓ + (m−2)·n` with `n ≥ 1` (or `n_vars = 2ℓ` at
    /// `m = 2`), or exceeds 64.
    pub fn new(m: usize, ell: usize, n_vars: usize) -> Option<Self> {
        if m < 2 || ell == 0 || n_vars > 64 {
            return None;
        }
        let summands = m.checked_mul(ell)?;
        let rest = n_vars.checked_sub(summands)?;
        let n = if m == 2 {
            if rest != 0 {
                return None;
            }
            0
        } else {
            if rest == 0 || rest % (m - 2) != 0 {
                return None;
            }
            rest / (m - 2)
        };
        Some(Self { m, ell, n, n_vars })
    }

    /// The layout of a system built by `build_decomposition_system` (or
    /// its template), in its native variable order.
    pub fn of_system(sys: &DecompositionSystem) -> Option<Self> {
        Self::new(sys.m, sys.ell, sys.n_vars)
    }

    /// The blocks, summands first.
    pub fn blocks(&self) -> Vec<Block> {
        let mut out: Vec<Block> = (0..self.m)
            .map(|i| Block {
                kind: BlockKind::Summand(i),
                first: i * self.ell,
                len: self.ell,
            })
            .collect();
        for i in 0..self.m.saturating_sub(2) {
            out.push(Block {
                kind: BlockKind::Intermediate(i),
                first: self.m * self.ell + i * self.n,
                len: self.n,
            });
        }
        out
    }
}

// ── The block graph ────────────────────────────────────────────────

/// Which blocks share a monomial, read off the equations.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct BlockGraph {
    /// Bit `b` set iff some monomial holds two variables of block `b`.
    pub self_loops: u64,
    /// `adj[b]` has bit `c` set iff blocks `b ≠ c` share a monomial.
    pub adj: Vec<u64>,
}

/// The block graph of `system` over `blocks`.  `None` if a monomial
/// holds a variable outside every block, or there are more than 64
/// blocks.
pub fn block_graph(system: &[F2BoolPoly], blocks: &[Block]) -> Option<BlockGraph> {
    if blocks.len() > 64 {
        return None;
    }
    let covered = blocks.iter().fold(0u64, |acc, b| acc | b.mask());
    let mut g = BlockGraph {
        self_loops: 0,
        adj: vec![0; blocks.len()],
    };
    for p in system {
        for t in &p.terms {
            if t.mask & !covered != 0 {
                return None;
            }
            let mut touched = 0u64;
            for (b, blk) in blocks.iter().enumerate() {
                let c = (t.mask & blk.mask()).count_ones();
                if c >= 2 {
                    g.self_loops |= 1 << b;
                }
                if c >= 1 {
                    touched |= 1 << b;
                }
            }
            let mut rest = touched;
            while rest != 0 {
                let b = rest.trailing_zeros() as usize;
                rest &= rest - 1;
                g.adj[b] |= touched & !(1u64 << b);
            }
        }
    }
    Some(g)
}

/// Highest monomial degree in `system`.
fn system_degree(system: &[F2BoolPoly]) -> u32 {
    system
        .iter()
        .flat_map(|p| p.terms.iter())
        .map(|t| t.mask.count_ones())
        .max()
        .unwrap_or(0)
}

// ── Crossbred with a block plan ────────────────────────────────────

/// The `(D, k)` of a block-planned crossbred run and the renaming that
/// puts the enumerated variables first.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CrossbredBlockPlan {
    /// Macaulay degree `D`: the system's own degree.
    pub macaulay_degree: u32,
    /// Enumerated variables `k`.
    pub enumerated: usize,
    /// Bitmask over [`SummandBlocks::blocks`] of the blocks left linear.
    pub solved_blocks: u64,
    /// `perm[old] = new`: enumerated variables (ascending) first, then
    /// the solved ones (ascending).
    pub perm: Vec<u32>,
    /// `order[new] = old`, the inverse of `perm`.
    pub order: Vec<u32>,
}

/// **Plan** a crossbred run from the block structure: leave linear the
/// maximum-weight independent set of the block graph, enumerate the rest.
///
/// `None` when the layout does not fit the system, the graph has more
/// than [`MAX_PLAN_BLOCKS`] blocks, the system has no monomial of
/// positive degree, or no block can be left linear.
pub fn plan_crossbred(system: &[F2BoolPoly], layout: &SummandBlocks) -> Option<CrossbredBlockPlan> {
    let blocks = layout.blocks();
    if blocks.len() > MAX_PLAN_BLOCKS {
        return None;
    }
    let degree = system_degree(system);
    if degree == 0 {
        return None;
    }
    let g = block_graph(system, &blocks)?;
    let mut best: Option<((usize, usize, usize), u64)> = None;
    for s in 1u64..(1u64 << blocks.len()) {
        if s & g.self_loops != 0 {
            continue;
        }
        let mut weight = 0usize;
        let mut inter = 0usize;
        let mut ok = true;
        let mut rest = s;
        while rest != 0 {
            let b = rest.trailing_zeros() as usize;
            rest &= rest - 1;
            if g.adj[b] & s != 0 {
                ok = false;
                break;
            }
            weight += blocks[b].len;
            if matches!(blocks[b].kind, BlockKind::Intermediate(_)) {
                inter += blocks[b].len;
            }
        }
        if !ok || weight == 0 {
            continue;
        }
        // Lowest solved variable: higher keeps a longer prefix of low
        // variables enumerated, the prefix the generic split sweeps.
        // (`blocks` is in increasing variable order.)
        let lowest = blocks[s.trailing_zeros() as usize].first;
        let key = (weight, inter, lowest);
        if best.is_none_or(|(bk, _)| key > bk) {
            best = Some((key, s));
        }
    }
    let ((weight, _, _), solved_blocks) = best?;
    let solved_mask = blocks
        .iter()
        .enumerate()
        .filter(|(b, _)| solved_blocks & (1 << b) != 0)
        .fold(0u64, |acc, (_, blk)| acc | blk.mask());
    let n = layout.n_vars;
    let mut order: Vec<u32> = (0..n as u32)
        .filter(|&v| solved_mask & (1u64 << v) == 0)
        .collect();
    order.extend((0..n as u32).filter(|&v| solved_mask & (1u64 << v) != 0));
    let mut perm = vec![0u32; n];
    for (new, &old) in order.iter().enumerate() {
        perm[old as usize] = new as u32;
    }
    Some(CrossbredBlockPlan {
        macaulay_degree: degree,
        enumerated: n - weight,
        solved_blocks,
        perm,
        order,
    })
}

/// How the crossbred space is produced at the planned `(D, k)`.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Preprocess {
    /// Take the input equations themselves: at the planned `(D, k)` each
    /// already has specialised degree `≤ 1`, so each lies in the
    /// crossbred space.  No Macaulay matrix is built.
    Direct,
    /// Run [`extract_crossbred`] at the planned `(D, k)` with this row
    /// cap; above the cap, fall back to [`Preprocess::Direct`].
    Macaulay {
        /// Macaulay rows the extraction may build.
        max_rows: usize,
    },
}

/// Knobs for [`solve_crossbred_blocks`].
#[derive(Clone, Copy, Debug)]
pub struct CrossbredBlockOptions {
    /// Where the crossbred polynomials come from.
    pub preprocess: Preprocess,
    /// The search phase's options.  `max_enumerated_bits` bounds the
    /// bit-sliced tables; enumerated variables beyond it are swept by an
    /// outer loop of up to `2^max_outer_bits` substitutions.
    pub search: SearchOptions,
    /// Most enumerated variables handled by the outer loop.  The plan is
    /// refused when `k > max_enumerated_bits + max_outer_bits`.
    pub max_outer_bits: u32,
}

impl Default for CrossbredBlockOptions {
    fn default() -> Self {
        Self {
            preprocess: Preprocess::Direct,
            search: SearchOptions::default(),
            max_outer_bits: 0,
        }
    }
}

/// What a block-planned crossbred run cost and found.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct CrossbredBlockStats {
    /// Planned `D`.
    pub macaulay_degree: u32,
    /// Planned `k`.
    pub enumerated: usize,
    /// Of `k`, the variables swept by the outer loop.
    pub outer_bits: u32,
    /// The extraction's measurements (zero under [`Preprocess::Direct`]).
    pub extract: ExtractStats,
    /// Set when [`Preprocess::Macaulay`] exceeded its row cap and the run
    /// fell back to [`Preprocess::Direct`].
    pub preprocess_fallback: bool,
    /// Crossbred polynomials handed to the search.
    pub crossbred_polys: usize,
    /// The search phase, summed over the outer loop.
    pub search: SearchStats,
}

fn add_search(acc: &mut SearchStats, s: &SearchStats) {
    acc.points += s.points;
    acc.survivors += s.survivors;
    acc.linear_solves += s.linear_solves;
    acc.candidates += s.candidates;
    acc.verified += s.verified;
    acc.transform_word_ops += s.transform_word_ops;
    acc.filter_word_ops += s.filter_word_ops;
    acc.solve_row_ops += s.solve_row_ops;
    acc.exhausted |= s.exhausted;
}

/// Fix variables `lo .. hi` to the bits of `values` and close the gap,
/// so variable `v ≥ hi` becomes `v − (hi − lo)`.
fn fix_range(p: &F2BoolPoly, lo: usize, hi: usize, values: u64) -> F2BoolPoly {
    let width = hi - lo;
    let range = mask_of(width) << lo;
    let vals = (values & mask_of(width)) << lo;
    let low = mask_of(lo);
    let monos: Vec<F2BoolMono> = p
        .terms
        .iter()
        .filter(|t| t.mask & range & !vals == 0)
        .map(|t| {
            let high = if hi >= 64 { 0 } else { t.mask >> hi };
            F2BoolMono::from_mask((t.mask & low) | (high << lo))
        })
        .collect();
    F2BoolPoly::from_monos(monos, p.n_vars - width)
}

/// **Solve** a Semaev chain system by crossbred at the block-planned
/// `(D, k)`.
///
/// Returns every root (as point masks in the input's variable order,
/// sorted ascending) with the run's measurements, or `None` when no plan
/// exists or the plan's `k` exceeds the options' budget — the caller's
/// cue to use the generic path.
pub fn solve_crossbred_blocks(
    system: &[F2BoolPoly],
    layout: &SummandBlocks,
    opts: &CrossbredBlockOptions,
) -> Option<(Vec<u64>, CrossbredBlockStats)> {
    let plan = plan_crossbred(system, layout)?;
    let k = plan.enumerated;
    let n = layout.n_vars;
    let table_bits = (opts.search.max_enumerated_bits as usize).min(k);
    let outer = k - table_bits;
    if outer > opts.max_outer_bits as usize || outer >= 64 {
        return None;
    }
    let permuted: Vec<F2BoolPoly> = system
        .iter()
        .filter(|p| !p.is_zero())
        .map(|p| permute_poly(p, &plan.perm))
        .collect();
    if permuted.is_empty() {
        return None;
    }
    let mut stats = CrossbredBlockStats {
        macaulay_degree: plan.macaulay_degree,
        enumerated: k,
        outer_bits: outer as u32,
        ..CrossbredBlockStats::default()
    };
    let polys: Vec<F2BoolPoly> = match opts.preprocess {
        Preprocess::Direct => permuted.clone(),
        Preprocess::Macaulay { max_rows } => {
            let params = CrossbredParams {
                macaulay_degree: plan.macaulay_degree,
                enumerated: k,
                target_degree: 1,
                max_rows,
            };
            match extract_crossbred(&permuted, n, &params) {
                Some(xb) if !xb.polys.is_empty() => {
                    stats.extract = xb.stats;
                    xb.polys
                }
                _ => {
                    stats.preprocess_fallback = true;
                    permuted.clone()
                }
            }
        }
    };
    stats.crossbred_polys = polys.len();

    let mut roots: Vec<u64> = Vec::new();
    for o in 0..(1u64 << outer) {
        let (orig, xpolys) = if outer == 0 {
            (permuted.clone(), polys.clone())
        } else {
            (
                permuted
                    .iter()
                    .map(|p| fix_range(p, table_bits, k, o))
                    .collect::<Vec<_>>(),
                polys
                    .iter()
                    .map(|p| fix_range(p, table_bits, k, o))
                    .filter(|p| !p.is_zero())
                    .collect::<Vec<_>>(),
            )
        };
        // A substitution can make an equation the constant 1: no root.
        if orig
            .iter()
            .any(|p| p.terms.len() == 1 && p.terms[0].mask == 0)
        {
            continue;
        }
        let xb = CrossbredSystem {
            polys: xpolys,
            n_vars: n - outer,
            enumerated: table_bits,
            target_degree: 1,
            stats: ExtractStats::default(),
        };
        if xb.polys.is_empty() {
            // Every equation vanished identically: all points are roots,
            // which this search does not enumerate.
            stats.search.exhausted = true;
            continue;
        }
        let (found, s) = solve_crossbred(&orig, &xb, &opts.search);
        add_search(&mut stats.search, &s);
        for r in found {
            let full = (r & mask_of(table_bits)) | (o << table_bits) | ((r >> table_bits) << k);
            roots.push(permute_mask(full, &plan.order));
        }
    }
    roots.retain(|&r| system.iter().all(|p| p.eval(r) == 0));
    roots.sort_unstable();
    roots.dedup();
    Some((roots, stats))
}

// ── XL by block elimination ────────────────────────────────────────

/// One stage of a block-elimination XL run: enumerate some variables,
/// then solve one block linearly.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct XlStage {
    /// Variables enumerated at this stage, as a mask.
    pub enumerate: u64,
    /// The block solved linearly at this stage.
    pub solve: Block,
    /// Equations fully determined once this stage's enumeration is done,
    /// checked before the solve.
    pub filters: Vec<usize>,
    /// Equations linear in `solve` once the earlier blocks are known.
    pub linear: Vec<usize>,
}

/// The stages of a block-elimination XL run.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct BlockXlPlan {
    /// The stages, in order.
    pub stages: Vec<XlStage>,
    /// Enumerated variables over all stages: `(m − 1)·ℓ` for the chain.
    pub enumerated: usize,
}

/// The variables of a polynomial, as a mask.
fn support(p: &F2BoolPoly) -> u64 {
    p.terms.iter().fold(0u64, |acc, t| acc | t.mask)
}

/// **Plan** block-elimination XL for a Semaev chain: enumerate `X_0, X_1`
/// and solve `U_0`; then for each further link enumerate `X_{j+1}` and
/// solve `U_j`; finally solve `X_{m−1}`.  (`m = 2`: enumerate `X_0`,
/// solve `X_1`.)
///
/// Each equation goes to the first stage at which it is fully known (a
/// filter) or linear in the stage's block with every other variable
/// known.  `None` if a solved block is wider than 63 variables or some
/// stage gets no linear equation.
pub fn plan_block_xl(system: &[F2BoolPoly], layout: &SummandBlocks) -> Option<BlockXlPlan> {
    let blocks = layout.blocks();
    let m = layout.m;
    let summand = |i: usize| blocks[i];
    let inter = |i: usize| blocks[m + i];
    // (enumerated blocks, solved block)
    let mut schedule: Vec<(Vec<Block>, Block)> = Vec::new();
    if m == 2 {
        schedule.push((vec![summand(0)], summand(1)));
    } else {
        schedule.push((vec![summand(0), summand(1)], inter(0)));
        for j in 1..m - 2 {
            schedule.push((vec![summand(j + 1)], inter(j)));
        }
        schedule.push((Vec::new(), summand(m - 1)));
    }
    let supports: Vec<u64> = system.iter().map(support).collect();
    let mut assigned = vec![false; system.len()];
    let mut known = 0u64;
    let mut stages = Vec::new();
    let mut enumerated = 0usize;
    for (enum_blocks, solve) in schedule {
        if solve.len > 63 {
            return None;
        }
        let enumerate = enum_blocks.iter().fold(0u64, |acc, b| acc | b.mask());
        enumerated += enumerate.count_ones() as usize;
        known |= enumerate;
        let bm = solve.mask();
        let mut filters = Vec::new();
        let mut linear = Vec::new();
        for (e, p) in system.iter().enumerate() {
            if assigned[e] || p.is_zero() {
                continue;
            }
            let s = supports[e];
            if s & !known == 0 {
                filters.push(e);
                assigned[e] = true;
            } else if s & !(known | bm) == 0
                && p.terms.iter().all(|t| (t.mask & bm).count_ones() <= 1)
            {
                linear.push(e);
                assigned[e] = true;
            }
        }
        if linear.is_empty() {
            return None;
        }
        known |= bm;
        stages.push(XlStage {
            enumerate,
            solve,
            filters,
            linear,
        });
    }
    Some(BlockXlPlan { stages, enumerated })
}

/// Knobs for [`solve_block_xl`].
#[derive(Clone, Copy, Debug)]
pub struct BlockXlOptions {
    /// Largest affine solution space enumerated per stage solve; above it
    /// the run sets `exhausted` and skips that branch.
    pub max_kernel_dim: u32,
    /// Refuse plans enumerating more variables than this in total.
    pub max_enumerated_bits: u32,
}

impl Default for BlockXlOptions {
    fn default() -> Self {
        Self {
            max_kernel_dim: SearchOptions::default().max_kernel_dim,
            max_enumerated_bits: 30,
        }
    }
}

/// What a block-elimination XL run cost and found.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct BlockXlStats {
    /// Enumerated variables over all stages.
    pub enumerated: usize,
    /// Stages in the plan.
    pub stages: usize,
    /// Enumeration points visited, over all stages.
    pub points: u64,
    /// Points that passed the stage filters.
    pub survivors: u64,
    /// Linear systems assembled and solved.
    pub linear_solves: u64,
    /// Row operations in those solves.
    pub solve_row_ops: u64,
    /// Compiled coefficient terms evaluated assembling them.
    pub term_evals: u64,
    /// Full assignments reached.
    pub candidates: u64,
    /// Full assignments that satisfied every equation.
    pub verified: u64,
    /// Set if a stage's solution space exceeded `max_kernel_dim`, so the
    /// root list may be incomplete.
    pub exhausted: bool,
}

/// A linear-in-a-block equation compiled for evaluation: each entry is
/// `(known part, row bits)` where row bit 0 is the constant and bit
/// `1 + j` the coefficient of the block's `j`-th variable.  Entries with
/// equal known parts are merged.
type Compiled = Vec<(u64, u64)>;

fn compile(p: &F2BoolPoly, block: &Block) -> Compiled {
    let bm = block.mask();
    let mut entries: Vec<(u64, u64)> = p
        .terms
        .iter()
        .map(|t| {
            let u = t.mask & bm;
            let slot = if u == 0 {
                1u64
            } else {
                1u64 << (1 + u.trailing_zeros() as usize - block.first)
            };
            (t.mask & !bm, slot)
        })
        .collect();
    entries.sort_unstable();
    let mut out: Compiled = Vec::with_capacity(entries.len());
    for (k, s) in entries {
        match out.last_mut() {
            Some((lk, ls)) if *lk == k => *ls ^= s,
            _ => out.push((k, s)),
        }
    }
    out.retain(|&(_, s)| s != 0);
    out
}

#[inline]
fn eval_compiled(c: &Compiled, a: u64) -> u64 {
    let mut row = 0u64;
    for &(k, s) in c {
        if k & !a == 0 {
            row ^= s;
        }
    }
    row
}

/// Solve the rows (bit 0 = right-hand side, bit `1 + j` = coefficient of
/// unknown `j`) for all `y` in `len` unknowns.  `None` when the solution
/// space has more than `max_kernel_dim` free variables.
fn solve_rows(
    rows: &mut [u64],
    len: usize,
    max_kernel_dim: u32,
    row_ops: &mut u64,
) -> Option<Vec<u64>> {
    let mut pivots: Vec<usize> = Vec::new();
    let mut r = 0usize;
    for c in 0..len {
        let bit = 1u64 << (c + 1);
        let Some(p) = (r..rows.len()).find(|&i| rows[i] & bit != 0) else {
            continue;
        };
        rows.swap(r, p);
        let pr = rows[r];
        for (i, row) in rows.iter_mut().enumerate() {
            if i != r && *row & bit != 0 {
                *row ^= pr;
                *row_ops += 1;
            }
        }
        pivots.push(c);
        r += 1;
        if r == rows.len() {
            break;
        }
    }
    if rows[r..].contains(&1) {
        return Some(Vec::new());
    }
    let pivot_mask = pivots.iter().fold(0u64, |acc, &c| acc | (1u64 << c));
    let free: Vec<usize> = (0..len).filter(|c| pivot_mask & (1u64 << c) == 0).collect();
    if free.len() as u32 > max_kernel_dim {
        return None;
    }
    let mut out = Vec::with_capacity(1 << free.len());
    for assign in 0..(1u64 << free.len()) {
        let mut y = 0u64;
        for (i, &c) in free.iter().enumerate() {
            y |= ((assign >> i) & 1) << c;
        }
        for (i, &c) in pivots.iter().enumerate() {
            // Reduced echelon form: row `i` holds pivot `c` and free
            // columns only, so its value is the rhs plus the free part.
            let coeffs = (rows[i] >> 1) & !(1u64 << c);
            let v = (rows[i] & 1) ^ u64::from((coeffs & y).count_ones() & 1);
            y |= v << c;
        }
        out.push(y);
    }
    Some(out)
}

struct XlRun<'a> {
    system: &'a [F2BoolPoly],
    plan: &'a BlockXlPlan,
    filters: Vec<Vec<Compiled>>,
    linear: Vec<Vec<Compiled>>,
    max_kernel_dim: u32,
    stats: BlockXlStats,
    roots: Vec<u64>,
    rows: Vec<u64>,
}

impl XlRun<'_> {
    fn dfs(&mut self, stage: usize, a: u64) {
        if stage == self.plan.stages.len() {
            self.stats.candidates += 1;
            if self.system.iter().all(|p| p.eval(a) == 0) {
                self.stats.verified += 1;
                self.roots.push(a);
            }
            return;
        }
        let st = &self.plan.stages[stage];
        let (mask, block) = (st.enumerate, st.solve);
        let mut s = 0u64;
        loop {
            let a2 = a | s;
            self.stats.points += 1;
            let alive = self.filters[stage].iter().all(|c| {
                self.stats.term_evals += c.len() as u64;
                eval_compiled(c, a2) == 0
            });
            if alive {
                self.stats.survivors += 1;
                let mut rows = std::mem::take(&mut self.rows);
                rows.clear();
                for c in &self.linear[stage] {
                    self.stats.term_evals += c.len() as u64;
                    let row = eval_compiled(c, a2);
                    if row != 0 {
                        rows.push(row);
                    }
                }
                self.stats.linear_solves += 1;
                let sols = solve_rows(
                    &mut rows,
                    block.len,
                    self.max_kernel_dim,
                    &mut self.stats.solve_row_ops,
                );
                self.rows = rows;
                match sols {
                    None => self.stats.exhausted = true,
                    Some(ys) => {
                        for y in ys {
                            self.dfs(stage + 1, a2 | (y << block.first));
                        }
                    }
                }
            }
            if s == mask {
                break;
            }
            // Next subset of `mask`, in increasing order.
            s = s.wrapping_sub(mask) & mask;
        }
    }
}

/// **Solve** a Semaev chain system by block-elimination XL.
///
/// Returns every root (point masks in the input's variable order, sorted
/// ascending) with the run's measurements, or `None` when no plan exists
/// or it enumerates more than `opts.max_enumerated_bits` variables.
pub fn solve_block_xl(
    system: &[F2BoolPoly],
    layout: &SummandBlocks,
    opts: &BlockXlOptions,
) -> Option<(Vec<u64>, BlockXlStats)> {
    let plan = plan_block_xl(system, layout)?;
    if plan.enumerated > opts.max_enumerated_bits as usize {
        return None;
    }
    let empty = Block {
        kind: BlockKind::Summand(0),
        first: 0,
        len: 0,
    };
    let filters = plan
        .stages
        .iter()
        .map(|st| {
            st.filters
                .iter()
                .map(|&e| compile(&system[e], &empty))
                .collect()
        })
        .collect();
    let linear = plan
        .stages
        .iter()
        .map(|st| {
            st.linear
                .iter()
                .map(|&e| compile(&system[e], &st.solve))
                .collect()
        })
        .collect();
    let mut run = XlRun {
        system,
        plan: &plan,
        filters,
        linear,
        max_kernel_dim: opts.max_kernel_dim,
        stats: BlockXlStats {
            enumerated: plan.enumerated,
            stages: plan.stages.len(),
            ..BlockXlStats::default()
        },
        roots: Vec::new(),
        rows: Vec::new(),
    };
    run.dfs(0, 0);
    let mut roots = run.roots;
    roots.sort_unstable();
    roots.dedup();
    Some((roots, run.stats))
}

// ── Dispatch ───────────────────────────────────────────────────────

/// Which block solver [`solve_semaev_blocks`] ran.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum BlockSolver {
    /// [`solve_crossbred_blocks`] with default options.
    Crossbred,
    /// [`solve_block_xl`] with default options.
    Xl,
}

/// Whether the decomposition oracle's default crossbred path goes
/// through this module.  `IC_CROSSBRED_BLOCKS=0` restores the generic
/// `k = n_vars / 2` path, as a same-binary control.
pub fn enabled() -> bool {
    static OFF: std::sync::OnceLock<bool> = std::sync::OnceLock::new();
    !*OFF.get_or_init(|| std::env::var("IC_CROSSBRED_BLOCKS").as_deref() == Ok("0"))
}

/// The block solver [`solve_semaev_blocks`] would pick, with its
/// enumerated-variable count: the one enumerating fewer variables, the
/// crossbred plan only when its `k` fits the bit-sliced tables
/// (`SearchOptions::default().max_enumerated_bits`), ties to crossbred.
pub fn choose_block_solver(
    system: &[F2BoolPoly],
    layout: &SummandBlocks,
) -> Option<(BlockSolver, usize)> {
    let table = SearchOptions::default().max_enumerated_bits as usize;
    let xb = plan_crossbred(system, layout)
        .map(|p| p.enumerated)
        .filter(|&k| k <= table);
    let xl = plan_block_xl(system, layout)
        .map(|p| p.enumerated)
        .filter(|&k| k <= BlockXlOptions::default().max_enumerated_bits as usize);
    match (xb, xl) {
        (Some(a), Some(b)) if b < a => Some((BlockSolver::Xl, b)),
        (Some(a), _) => Some((BlockSolver::Crossbred, a)),
        (None, Some(b)) => Some((BlockSolver::Xl, b)),
        (None, None) => None,
    }
}

/// **Solve** a decomposition system with the block solver
/// [`choose_block_solver`] picks, reporting in the crossbred search's
/// units (XL fills `points`, `survivors`, `linear_solves`, `candidates`,
/// `verified`, `solve_row_ops` and `exhausted`).  Roots sorted
/// ascending; `None` when neither plan applies.
pub fn solve_semaev_blocks(
    sys: &DecompositionSystem,
) -> Option<(Vec<u64>, SearchStats, BlockSolver)> {
    solve_semaev_blocks_with(
        sys,
        &CrossbredBlockOptions::default(),
        &BlockXlOptions::default(),
    )
}

/// [`solve_semaev_blocks`] with explicit solver options (the choice of
/// solver is still [`choose_block_solver`]'s).  Tests use it to force an
/// exhausted search with a small `max_kernel_dim`.
pub fn solve_semaev_blocks_with(
    sys: &DecompositionSystem,
    xb: &CrossbredBlockOptions,
    xl: &BlockXlOptions,
) -> Option<(Vec<u64>, SearchStats, BlockSolver)> {
    let layout = SummandBlocks::of_system(sys)?;
    let (which, _) = choose_block_solver(&sys.equations, &layout)?;
    match which {
        BlockSolver::Crossbred => {
            let (roots, st) = solve_crossbred_blocks(&sys.equations, &layout, xb)?;
            Some((roots, st.search, which))
        }
        BlockSolver::Xl => {
            let (roots, st) = solve_block_xl(&sys.equations, &layout, xl)?;
            let search = SearchStats {
                points: st.points,
                survivors: st.survivors,
                linear_solves: st.linear_solves,
                candidates: st.candidates,
                verified: st.verified,
                solve_row_ops: st.solve_row_ops,
                exhausted: st.exhausted,
                ..SearchStats::default()
            };
            Some((roots, search, which))
        }
    }
}

/// Reorder roots into the order the generic crossbred search reports
/// them when it enumerates the low `k_generic` variables: ascending in
/// those bits (its sweep order), then ascending in the full mask.  The
/// generic order *within* one value of the low bits depends on its
/// per-point echelon form and is not reproduced; callers that need the
/// generic path's first root must treat a group of more than one root
/// as ambiguous.
pub fn order_like_generic(roots: &mut [u64], k_generic: usize) {
    let low = mask_of(k_generic);
    roots.sort_unstable_by_key(|&r| (r & low, r));
}

/// Split roots ordered by [`order_like_generic`] into the groups that
/// share their low `k_generic` bits.
pub fn generic_groups(roots: &[u64], k_generic: usize) -> Vec<&[u64]> {
    let low = mask_of(k_generic);
    roots.chunk_by(|a, b| a & low == b & low).collect()
}

/// The Koblitz decomposition oracle's block path
/// ([`crate::cryptanalysis::koblitz_index_calculus::crossbred_decompose`]
/// with default parameters): solve `sys` with [`solve_semaev_blocks`],
/// then lift roots in the generic path's order ([`order_like_generic`]
/// at its `k_generic`) and return the first decomposition.
///
/// Returns `None` — use the generic path — when no block plan applies,
/// when the block search is **exhausted** (whatever it found: an exhausted
/// search skips whole branches, which may hold a root in an earlier
/// low-bit group than the one that lifted, so its first lift need not be
/// the generic path's), or when the first group of roots that lifts lifts
/// to two different decompositions (the generic path's choice inside a
/// group is not reproduced, so the block path defers rather than guess).
pub(crate) fn decompose_via_blocks(
    kc: &crate::cryptanalysis::koblitz_index_calculus::KoblitzCurve,
    fb: &crate::cryptanalysis::koblitz_index_calculus::FrobeniusFactorBase,
    index_of: &std::collections::HashMap<(num_bigint::BigUint, num_bigint::BigUint), usize>,
    sys: &DecompositionSystem,
    target: &crate::binary_ecc::BinaryPoint,
    k_generic: usize,
) -> Option<(Option<Vec<usize>>, SearchStats)> {
    decompose_via_blocks_with(
        kc,
        fb,
        index_of,
        sys,
        target,
        k_generic,
        &CrossbredBlockOptions::default(),
        &BlockXlOptions::default(),
    )
}

/// [`decompose_via_blocks`] with explicit solver options.
#[allow(clippy::too_many_arguments)]
pub(crate) fn decompose_via_blocks_with(
    kc: &crate::cryptanalysis::koblitz_index_calculus::KoblitzCurve,
    fb: &crate::cryptanalysis::koblitz_index_calculus::FrobeniusFactorBase,
    index_of: &std::collections::HashMap<(num_bigint::BigUint, num_bigint::BigUint), usize>,
    sys: &DecompositionSystem,
    target: &crate::binary_ecc::BinaryPoint,
    k_generic: usize,
    xb: &CrossbredBlockOptions,
    xl: &BlockXlOptions,
) -> Option<(Option<Vec<usize>>, SearchStats)> {
    let (mut roots, stats, _) = solve_semaev_blocks_with(sys, xb, xl)?;
    if stats.exhausted {
        return None;
    }
    order_like_generic(&mut roots, k_generic);
    for group in generic_groups(&roots, k_generic) {
        let mut found: Option<Vec<usize>> = None;
        for &root in group {
            let xs: Vec<_> = (0..sys.m)
                .map(|i| sys.summand_x(&fb.subspace_basis, root, i, kc.n))
                .collect();
            if let Some(idxs) = crate::cryptanalysis::koblitz_index_calculus::lift_candidate(
                kc, fb, index_of, &xs, target,
            ) {
                match &found {
                    None => found = Some(idxs),
                    Some(f) if *f == idxs => {}
                    Some(_) => return None,
                }
            }
        }
        if found.is_some() {
            return Some((found, stats));
        }
    }
    Some((None, stats))
}

#[cfg(test)]
mod tests;
