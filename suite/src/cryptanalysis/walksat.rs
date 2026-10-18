//! WalkSAT local search for the Weil-descended decomposition systems.
//!
//! An **incomplete** alternative backend next to the CDCL / native-XOR
//! solver of [`crate::cryptanalysis::sat`].  Local search can only ever
//! *find* an assignment; it cannot prove that none exists.  Every entry
//! point here therefore has two outcomes, [`WalkResult::Sat`] — returned
//! only after the model has been re-checked against every constraint —
//! and [`WalkResult::Unknown`].  Nothing in this module ever reports
//! UNSAT, and [`walksat_decompose`] never sets a refutation flag.
//!
//! # Two engines
//!
//! * [`WalkSat`] — WalkSAT/SKC (Selman–Kautz–Cohen 1994) over CNF
//!   clauses **and native parity rows**.  A parity row is scored like a
//!   clause: flipping any of its variables repairs it, and flipping a
//!   variable of a satisfied row breaks it, so the break count of a
//!   variable is "clauses it is the only true literal of" plus
//!   "satisfied rows it appears in".  [`WalkSat::from_bool_system`]
//!   builds exactly the instance `semaev_sat::encode_boolean_system_with`
//!   hands the CDCL solver with [`XorEncoding::Native`](crate::cryptanalysis::semaev_sat::XorEncoding):
//!   one Tseitin AND per monomial of degree ≥ 2, one parity row per
//!   equation.
//! * [`AnfWalk`] — the same search directly on the algebraic normal
//!   form, over the problem variables only (at most 64, packed in a
//!   `u64`).  Flipping `v` toggles equation `e` exactly when the formal
//!   derivative `∂e/∂v` is one at the current point, so no Tseitin
//!   auxiliary is ever introduced and the search space is `2^{n_vars}`
//!   rather than `2^{n_vars + #monomials}`.  Candidate flips for an
//!   unsatisfied equation are the variables whose derivative is one
//!   (every such flip repairs it); when the derivative vanishes for all
//!   of them the step falls back to a random variable of its support.
//!
//! # Decomposition oracle
//!
//! [`walksat_decompose`] runs either engine on the system that
//! `polynomial_reuse::build_decomposition_system_reusing` builds — the
//! same chained `S_3` system, plus the same optional trace row, that
//! [`sat_decompose_with`] gives the CDCL solver — and lifts each model
//! with the same `lift_candidate` the CDCL path uses.  A model that fails
//! to lift is blocked (one "not this assignment" constraint) and the
//! walk continues, up to `max_models` models.  Its result is one valid
//! element of the decomposition set; *which* one depends on the seed, so
//! it is in general not the element the CDCL path returns.  Determinism:
//! the seed is mixed with the target's abscissa, so a fixed
//! `(options, target)` always returns the same decomposition and the same
//! counters, independent of thread scheduling.
//!
//! [`walksat_then_sat_decompose`] is the complete portfolio wired behind
//! [`DecompositionStrategy::WalkSat`](crate::cryptanalysis::koblitz_index_calculus::DecompositionStrategy):
//! local search first, and when it ends `Unknown` the unchanged CDCL path
//! ([`sat_decompose_with`]) decides the target.  Its verdicts are exactly
//! the CDCL verdicts; a refutation always comes from the CDCL fallback.
//!
//! # Cost and sameness caveats
//!
//! * On targets that do **not** decompose the portfolio is slower than
//!   CDCL alone: the walk spends its whole budget (4 tries x 4000 flips
//!   by default) before the fallback runs.  Measured on `K1/2^9`, `m = 3`,
//!   40 random undecomposable targets: 0.043 s (CDCL) against 0.065 s
//!   (portfolio), about +50%, in one noisy probe.  The walk wins when most
//!   targets decompose.
//! * The walk and CDCL may return different, equally valid decompositions
//!   of the same target, so the duplicate and dependent relations
//!   collected downstream can differ: relation counts are not guaranteed
//!   equal between [`DecompositionStrategy::WalkSat`](crate::cryptanalysis::koblitz_index_calculus::DecompositionStrategy)
//!   and `Sat`, only the discrete logarithms.
//! * The CNF + native-XOR engine ([`WalkSat`]) is slower than CDCL on the
//!   measured cells; [`AnfWalk`] is the only engine the default dispatch
//!   uses.
//!
//! # References
//!
//! - **B. Selman, H. Kautz, B. Cohen**, *Noise strategies for improving
//!   local search*, AAAI 1994 — WalkSAT/SKC.
//! - **H. Hoos, T. Stützle**, *Stochastic Local Search*, 2004.

use std::collections::HashMap;

use num_bigint::BigUint;

use crate::binary_ecc::{BinaryPoint, F2mElement, IrreduciblePoly};
use crate::cryptanalysis::fx_hash::FxMap;
use crate::cryptanalysis::koblitz_groebner::FieldStructure;
use crate::cryptanalysis::koblitz_index_calculus::{
    lift_candidate, sat_decompose_with, FrobeniusFactorBase, KoblitzCurve, SatDecompositionOptions,
    SatDecompositionStats,
};
use crate::cryptanalysis::pq_groebner_f2::{F2BoolMono, F2BoolPoly};
use crate::cryptanalysis::sat::Lit;

// ── Options, results, counters ──────────────────────────────────────

/// Search controls shared by both engines.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct WalkSatOptions {
    /// Seed of the walk's private SplitMix64 stream.
    pub seed: u64,
    /// Restarts from a fresh random assignment.
    pub max_tries: u32,
    /// Flips per try.
    pub max_flips: u64,
    /// Probability, in thousandths, of a random-walk step when no
    /// candidate is free to flip (WalkSAT's noise parameter `p`).
    pub noise_permille: u32,
}

impl Default for WalkSatOptions {
    fn default() -> Self {
        Self {
            seed: 0x5741_4c4b_5341_5400,
            max_tries: 4,
            max_flips: 4_000,
            noise_permille: 400,
        }
    }
}

/// Outcome of a local search.  There is deliberately no `Unsat`.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum WalkResult {
    /// A model was found and re-verified against every constraint.
    Sat,
    /// The flip budget ran out.  Says nothing about satisfiability.
    Unknown,
}

/// Counted work of one or more `solve` calls (cumulative).
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct WalkStats {
    /// Tries started (fresh random assignments).
    pub tries: u64,
    /// Variable flips performed.
    pub flips: u64,
    /// Steps that took a random candidate (noise) rather than a
    /// minimum-break one.
    pub noise_steps: u64,
    /// Candidate break counts evaluated.
    pub break_evals: u64,
    /// Fewest unsatisfied constraints seen in the last `solve` call.
    pub best_unsat: u64,
}

/// SplitMix64: the walk's private, platform-stable random stream.
#[derive(Clone, Debug)]
struct SplitMix(u64);

impl SplitMix {
    fn next(&mut self) -> u64 {
        self.0 = self.0.wrapping_add(0x9e37_79b9_7f4a_7c15);
        let mut z = self.0;
        z = (z ^ (z >> 30)).wrapping_mul(0xbf58_476d_1ce4_e5b9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94d0_49bb_1331_11eb);
        z ^ (z >> 31)
    }
    /// Uniform in `0..n` (`n > 0`).
    fn below(&mut self, n: u64) -> u64 {
        ((self.next() as u128 * n as u128) >> 64) as u64
    }
}

/// An unordered set of constraint ids with O(1) insert, remove and
/// uniform sampling.
#[derive(Clone, Debug, Default)]
struct UnsatSet {
    items: Vec<u32>,
    pos: Vec<u32>,
}

impl UnsatSet {
    const ABSENT: u32 = u32::MAX;

    fn reset(&mut self, n: usize) {
        self.items.clear();
        self.pos.clear();
        self.pos.resize(n, Self::ABSENT);
    }
    fn insert(&mut self, c: u32) {
        if self.pos[c as usize] == Self::ABSENT {
            self.pos[c as usize] = self.items.len() as u32;
            self.items.push(c);
        }
    }
    fn remove(&mut self, c: u32) {
        let p = self.pos[c as usize];
        if p != Self::ABSENT {
            let last = self.items.pop().expect("present implies non-empty");
            if last != c {
                self.items[p as usize] = last;
                self.pos[last as usize] = p;
            }
            self.pos[c as usize] = Self::ABSENT;
        }
    }
    fn len(&self) -> usize {
        self.items.len()
    }
}

/// The shared WalkSAT/SKC choice: given candidates and their break
/// counts, a zero-break candidate is taken outright (ties uniformly),
/// otherwise a random one with probability `noise`, else a minimum-break
/// one (ties uniformly).
fn pick(
    rng: &mut SplitMix,
    candidates: &[u32],
    breaks: &[u32],
    noise_permille: u32,
    stats: &mut WalkStats,
) -> u32 {
    debug_assert!(!candidates.is_empty() && candidates.len() == breaks.len());
    let min = *breaks.iter().min().expect("non-empty");
    if min > 0 && rng.below(1000) < u64::from(noise_permille) {
        stats.noise_steps += 1;
        return candidates[rng.below(candidates.len() as u64) as usize];
    }
    let ties = breaks.iter().filter(|&&b| b == min).count() as u64;
    let mut k = rng.below(ties);
    for (&v, &b) in candidates.iter().zip(breaks) {
        if b == min {
            if k == 0 {
                return v;
            }
            k -= 1;
        }
    }
    unreachable!("a tie was counted")
}

// ── Engine 1: CNF + native parity rows ──────────────────────────────

/// WalkSAT over CNF clauses and native parity rows.  Variables and
/// literals use the DIMACS convention of [`crate::cryptanalysis::sat`]:
/// variable `v` is `1..=n_vars`, literal `-v` its negation.
#[derive(Clone, Debug)]
pub struct WalkSat {
    n_vars: u32,
    clauses: Vec<Vec<Lit>>,
    /// Parity rows over 0-based variables, with their right-hand side.
    xors: Vec<(Vec<u32>, bool)>,
    trivially_unsat: bool,
    model: Vec<bool>,
    /// Cumulative work counters.
    pub stats: WalkStats,
}

impl WalkSat {
    /// An empty instance over `n_vars` variables.
    pub fn new(n_vars: u32) -> Self {
        Self {
            n_vars,
            clauses: Vec::new(),
            xors: Vec::new(),
            trivially_unsat: false,
            model: Vec::new(),
            stats: WalkStats::default(),
        }
    }

    /// Number of variables.
    pub fn n_vars(&self) -> u32 {
        self.n_vars
    }

    /// Add a clause.  Duplicate literals are merged, a tautology is
    /// dropped, and the empty clause makes the instance trivially
    /// unsatisfiable (the search then ends `Unknown` at once — it still
    /// never reports UNSAT).
    pub fn add_clause(&mut self, mut lits: Vec<Lit>) {
        for &l in &lits {
            assert!(
                l != 0 && l.unsigned_abs() <= self.n_vars,
                "literal {l} out of range"
            );
        }
        lits.sort_unstable_by_key(|l| (l.unsigned_abs(), *l));
        lits.dedup();
        if lits.windows(2).any(|w| w[0] == -w[1]) {
            return;
        }
        if lits.is_empty() {
            self.trivially_unsat = true;
        }
        self.clauses.push(lits);
    }

    /// Add the parity row `⊕ vars = rhs` (1-indexed variables; a
    /// repeated variable cancels).
    pub fn add_xor(&mut self, vars: &[u32], rhs: bool) {
        let mut vs: Vec<u32> = vars
            .iter()
            .map(|&v| {
                assert!(v >= 1 && v <= self.n_vars, "variable {v} out of range");
                v - 1
            })
            .collect();
        vs.sort_unstable();
        let mut kept: Vec<u32> = Vec::with_capacity(vs.len());
        for v in vs {
            if kept.last() == Some(&v) {
                kept.pop();
            } else {
                kept.push(v);
            }
        }
        if kept.is_empty() {
            if rhs {
                self.trivially_unsat = true;
            }
            return;
        }
        self.xors.push((kept, rhs));
    }

    /// The instance `encode_boolean_system_with(n_vars, equations, &[],
    /// XorEncoding::Native)` gives the CDCL solver: problem variables
    /// `1..=n_vars`, then one Tseitin AND auxiliary per distinct
    /// monomial of degree ≥ 2 (in increasing mask order), then one parity
    /// row per equation.  [`Self::assignment`] decodes the problem bits.
    pub fn from_bool_system(n_vars: usize, equations: &[F2BoolPoly]) -> Self {
        assert!(n_vars <= 64, "problem variables are packed into a u64");
        let mut monomials: Vec<u64> = equations
            .iter()
            .flat_map(|e| e.terms.iter().map(|t| t.mask))
            .filter(|m| m.count_ones() >= 2)
            .collect();
        monomials.sort_unstable();
        monomials.dedup();
        let aux_of: HashMap<u64, u32> = monomials
            .iter()
            .enumerate()
            .map(|(i, &m)| (m, (n_vars + 1 + i) as u32))
            .collect();
        let mut w = WalkSat::new((n_vars + monomials.len()) as u32);
        for &mask in &monomials {
            let z = aux_of[&mask] as Lit;
            let vars: Vec<Lit> = (0..64)
                .filter(|i| (mask >> i) & 1 == 1)
                .map(|i| i + 1)
                .collect();
            let mut big: Vec<Lit> = vars.iter().map(|v| -v).collect();
            big.push(z);
            w.add_clause(big);
            for v in vars {
                w.add_clause(vec![v, -z]);
            }
        }
        for eq in equations {
            let mut vars = Vec::with_capacity(eq.terms.len());
            let mut rhs = false;
            for t in &eq.terms {
                match t.mask.count_ones() {
                    0 => rhs = !rhs,
                    1 => vars.push(t.mask.trailing_zeros() + 1),
                    _ => vars.push(aux_of[&t.mask]),
                }
            }
            w.add_xor(&vars, rhs);
        }
        w
    }

    /// Exclude one assignment of the first `n_problem` variables (bit
    /// `i` of `root` is variable `i + 1`).
    pub fn block_assignment(&mut self, root: u64, n_problem: usize) {
        assert!(n_problem <= 64 && n_problem as u32 <= self.n_vars);
        let clause = (0..n_problem)
            .map(|i| {
                let lit = (i + 1) as Lit;
                if (root >> i) & 1 == 1 {
                    -lit
                } else {
                    lit
                }
            })
            .collect();
        self.add_clause(clause);
    }

    /// The last model (empty before the first `Sat`).
    pub fn model(&self) -> &[bool] {
        &self.model
    }

    /// The first `min(n_vars, 64)` variables of the last model, packed.
    pub fn assignment(&self) -> u64 {
        self.model
            .iter()
            .take(64)
            .enumerate()
            .fold(0u64, |acc, (i, &b)| acc | (u64::from(b) << i))
    }

    /// Does `model` satisfy every clause and parity row?
    pub fn check(&self, model: &[bool]) -> bool {
        if self.trivially_unsat || model.len() != self.n_vars as usize {
            return false;
        }
        let clauses_ok = self.clauses.iter().all(|c| {
            c.iter().any(|&l| {
                let v = model[(l.unsigned_abs() - 1) as usize];
                if l < 0 {
                    !v
                } else {
                    v
                }
            })
        });
        clauses_ok
            && self
                .xors
                .iter()
                .all(|(vs, rhs)| vs.iter().fold(false, |p, &v| p ^ model[v as usize]) == *rhs)
    }

    /// Run WalkSAT.  `Sat` only with a model that [`Self::check`]
    /// accepts; otherwise `Unknown`.
    pub fn solve(&mut self, opts: &WalkSatOptions) -> WalkResult {
        if self.trivially_unsat {
            return WalkResult::Unknown;
        }
        let n = self.n_vars as usize;
        let nc = self.clauses.len();
        let ncons = nc + self.xors.len();
        // Occurrence lists in CSR form: (constraint id, literal sign).
        let mut deg = vec![0u32; n + 1];
        for c in &self.clauses {
            for &l in c {
                deg[(l.unsigned_abs() - 1) as usize] += 1;
            }
        }
        for (vs, _) in &self.xors {
            for &v in vs {
                deg[v as usize] += 1;
            }
        }
        let mut start = vec![0u32; n + 1];
        for v in 0..n {
            start[v + 1] = start[v] + deg[v];
        }
        let mut fill = start.clone();
        let mut occ = vec![(0u32, false); start[n] as usize];
        for (ci, c) in self.clauses.iter().enumerate() {
            for &l in c {
                let v = (l.unsigned_abs() - 1) as usize;
                occ[fill[v] as usize] = (ci as u32, l > 0);
                fill[v] += 1;
            }
        }
        for (xi, (vs, _)) in self.xors.iter().enumerate() {
            for &v in vs {
                occ[fill[v as usize] as usize] = ((nc + xi) as u32, true);
                fill[v as usize] += 1;
            }
        }

        let mut rng = SplitMix(opts.seed);
        let mut assign = vec![false; n];
        let mut true_count = vec![0u32; nc];
        let mut parity = vec![false; self.xors.len()];
        let mut unsat = UnsatSet::default();
        let mut cands: Vec<u32> = Vec::new();
        let mut breaks: Vec<u32> = Vec::new();
        self.stats.best_unsat = u64::MAX;

        for _ in 0..opts.max_tries {
            self.stats.tries += 1;
            for a in assign.iter_mut() {
                *a = rng.next() & 1 == 1;
            }
            unsat.reset(ncons);
            for (ci, c) in self.clauses.iter().enumerate() {
                let t = c
                    .iter()
                    .filter(|&&l| assign[(l.unsigned_abs() - 1) as usize] == (l > 0))
                    .count() as u32;
                true_count[ci] = t;
                if t == 0 {
                    unsat.insert(ci as u32);
                }
            }
            for (xi, (vs, rhs)) in self.xors.iter().enumerate() {
                parity[xi] = vs.iter().fold(false, |p, &v| p ^ assign[v as usize]);
                if parity[xi] != *rhs {
                    unsat.insert((nc + xi) as u32);
                }
            }
            let mut flips = 0u64;
            loop {
                self.stats.best_unsat = self.stats.best_unsat.min(unsat.len() as u64);
                if unsat.len() == 0 {
                    if self.check(&assign) {
                        self.model = assign;
                        return WalkResult::Sat;
                    }
                    // Unreachable unless the bookkeeping is wrong; fail
                    // closed rather than report an unchecked model.
                    break;
                }
                if flips >= opts.max_flips {
                    break;
                }
                let c = unsat.items[rng.below(unsat.len() as u64) as usize] as usize;
                cands.clear();
                if c < nc {
                    cands.extend(self.clauses[c].iter().map(|l| l.unsigned_abs() - 1));
                } else {
                    cands.extend_from_slice(&self.xors[c - nc].0);
                }
                breaks.clear();
                for &v in &cands {
                    let mut b = 0u32;
                    for &(cid, pos) in
                        &occ[start[v as usize] as usize..start[v as usize + 1] as usize]
                    {
                        let cid = cid as usize;
                        if cid < nc {
                            if assign[v as usize] == pos && true_count[cid] == 1 {
                                b += 1;
                            }
                        } else if parity[cid - nc] == self.xors[cid - nc].1 {
                            b += 1;
                        }
                    }
                    breaks.push(b);
                }
                self.stats.break_evals += cands.len() as u64;
                let v = pick(
                    &mut rng,
                    &cands,
                    &breaks,
                    opts.noise_permille,
                    &mut self.stats,
                ) as usize;
                // Flip v and update every constraint it touches.
                assign[v] = !assign[v];
                for &(cid, pos) in &occ[start[v] as usize..start[v + 1] as usize] {
                    let cid_u = cid as usize;
                    if cid_u < nc {
                        if assign[v] == pos {
                            true_count[cid_u] += 1;
                            if true_count[cid_u] == 1 {
                                unsat.remove(cid);
                            }
                        } else {
                            true_count[cid_u] -= 1;
                            if true_count[cid_u] == 0 {
                                unsat.insert(cid);
                            }
                        }
                    } else {
                        let xi = cid_u - nc;
                        parity[xi] = !parity[xi];
                        if parity[xi] == self.xors[xi].1 {
                            unsat.remove(cid);
                        } else {
                            unsat.insert(cid);
                        }
                    }
                }
                flips += 1;
                self.stats.flips += 1;
            }
        }
        WalkResult::Unknown
    }
}

// ── Engine 2: local search on the algebraic normal form ─────────────

/// WalkSAT directly on a sparse Boolean polynomial system over at most
/// 64 variables, plus "not this assignment" blocks.
#[derive(Clone, Debug)]
pub struct AnfWalk {
    n_vars: usize,
    equations: Vec<F2BoolPoly>,
    /// Variables each equation depends on.
    support: Vec<u64>,
    /// Per variable: `(equation, first, end)` ranges into `rest`.
    var_eqs: Vec<Vec<(u32, u32, u32)>>,
    /// Term masks with the owning variable removed: `∂e/∂v` at `a` is
    /// the parity of `{ r : r ⊆ a }` over its range.
    rest: Vec<u64>,
    /// Blocked assignments and their constraint slot.
    blocked: FxMap<u64, u32>,
    model: u64,
    /// Cumulative work counters.
    pub stats: WalkStats,
}

impl AnfWalk {
    /// The system `equations = 0` over `n_vars ≤ 64` variables.
    pub fn new(n_vars: usize, equations: &[F2BoolPoly]) -> Self {
        assert!(n_vars <= 64, "problem variables are packed into a u64");
        let full = Self::var_mask(n_vars);
        let mut var_eqs: Vec<Vec<(u32, u32, u32)>> = vec![Vec::new(); n_vars];
        let mut rest = Vec::new();
        let mut support = Vec::with_capacity(equations.len());
        for (e, eq) in equations.iter().enumerate() {
            let mut sup = 0u64;
            for t in &eq.terms {
                assert!(t.mask & !full == 0, "monomial outside the system");
                sup |= t.mask;
            }
            support.push(sup);
            for (v, ranges) in var_eqs.iter_mut().enumerate() {
                if (sup >> v) & 1 == 0 {
                    continue;
                }
                let first = rest.len() as u32;
                rest.extend(
                    eq.terms
                        .iter()
                        .filter(|t| (t.mask >> v) & 1 == 1)
                        .map(|t| t.mask & !(1u64 << v)),
                );
                ranges.push((e as u32, first, rest.len() as u32));
            }
        }
        Self {
            n_vars,
            equations: equations.to_vec(),
            support,
            var_eqs,
            rest,
            blocked: FxMap::default(),
            model: 0,
            stats: WalkStats::default(),
        }
    }

    fn var_mask(n_vars: usize) -> u64 {
        if n_vars == 64 {
            u64::MAX
        } else {
            (1u64 << n_vars) - 1
        }
    }

    /// Exclude `root` from the models this walk may return.
    pub fn block(&mut self, root: u64) {
        let next = self.blocked.len() as u32;
        self.blocked
            .entry(root & Self::var_mask(self.n_vars))
            .or_insert(next);
    }

    /// The last model (bit `i` is variable `i`).
    pub fn model(&self) -> u64 {
        self.model
    }

    /// Does `a` satisfy every equation and avoid every block?
    pub fn check(&self, a: u64) -> bool {
        a & !Self::var_mask(self.n_vars) == 0
            && self.equations.iter().all(|e| e.eval(a) == 0)
            && !self.blocked.contains_key(&a)
    }

    /// Run the local search.  `Sat` only with a model that
    /// [`Self::check`] accepts; otherwise `Unknown`.
    pub fn solve(&mut self, opts: &WalkSatOptions) -> WalkResult {
        let ne = self.equations.len();
        let ncons = ne + self.blocked.len();
        let full = Self::var_mask(self.n_vars);
        // An equation with no support is a constant: `1 = 0` can never
        // be repaired by a flip.
        if self
            .equations
            .iter()
            .zip(&self.support)
            .any(|(e, &s)| s == 0 && e.eval(0) == 1)
            || (self.n_vars == 0 && !self.check(0))
        {
            return WalkResult::Unknown;
        }
        let deriv = |rest: &[u64], a: u64, first: u32, end: u32| -> bool {
            rest[first as usize..end as usize]
                .iter()
                .fold(false, |p, &r| p ^ (a & r == r))
        };
        let mut rng = SplitMix(opts.seed);
        let mut unsat = UnsatSet::default();
        let mut cands: Vec<u32> = Vec::new();
        let mut breaks: Vec<u32> = Vec::new();
        self.stats.best_unsat = u64::MAX;

        for _ in 0..opts.max_tries {
            self.stats.tries += 1;
            let mut a = rng.next() & full;
            let mut val: Vec<bool> = self.equations.iter().map(|e| e.eval(a) == 1).collect();
            unsat.reset(ncons);
            for (e, &bad) in val.iter().enumerate() {
                if bad {
                    unsat.insert(e as u32);
                }
            }
            if let Some(&k) = self.blocked.get(&a) {
                unsat.insert(ne as u32 + k);
            }
            let mut flips = 0u64;
            loop {
                self.stats.best_unsat = self.stats.best_unsat.min(unsat.len() as u64);
                if unsat.len() == 0 {
                    if self.check(a) {
                        self.model = a;
                        return WalkResult::Sat;
                    }
                    break;
                }
                if flips >= opts.max_flips {
                    break;
                }
                let c = unsat.items[rng.below(unsat.len() as u64) as usize] as usize;
                cands.clear();
                breaks.clear();
                // Candidate set: every variable whose flip repairs c.
                let pool = if c < ne { self.support[c] } else { full };
                let mut bits = pool;
                while bits != 0 {
                    let v = bits.trailing_zeros() as usize;
                    bits &= bits - 1;
                    let mut fixes = c >= ne;
                    let mut b = 0u32;
                    for &(e, first, end) in &self.var_eqs[v] {
                        if deriv(&self.rest, a, first, end) {
                            if e as usize == c {
                                fixes = true;
                            } else if !val[e as usize] {
                                b += 1;
                            }
                        }
                    }
                    let flipped = a ^ (1u64 << v);
                    b += u32::from(self.blocked.contains_key(&flipped));
                    self.stats.break_evals += 1;
                    if fixes {
                        cands.push(v as u32);
                        breaks.push(b);
                    }
                }
                let v = if cands.is_empty() {
                    // ∂c/∂v vanishes for every v of the support: no
                    // single flip repairs c, so step at random inside it.
                    self.stats.noise_steps += 1;
                    let k = rng.below(u64::from(pool.count_ones()));
                    let mut bits = pool;
                    for _ in 0..k {
                        bits &= bits - 1;
                    }
                    bits.trailing_zeros()
                } else {
                    pick(
                        &mut rng,
                        &cands,
                        &breaks,
                        opts.noise_permille,
                        &mut self.stats,
                    )
                } as usize;
                for &(e, first, end) in &self.var_eqs[v] {
                    if deriv(&self.rest, a, first, end) {
                        let e = e as usize;
                        val[e] = !val[e];
                        if val[e] {
                            unsat.insert(e as u32);
                        } else {
                            unsat.remove(e as u32);
                        }
                    }
                }
                let before = a;
                a ^= 1u64 << v;
                if let Some(&k) = self.blocked.get(&before) {
                    unsat.remove(ne as u32 + k);
                }
                if let Some(&k) = self.blocked.get(&a) {
                    unsat.insert(ne as u32 + k);
                }
                flips += 1;
                self.stats.flips += 1;
            }
        }
        WalkResult::Unknown
    }
}

// ── Decomposition oracle ────────────────────────────────────────────

/// Which engine [`walksat_decompose`] runs.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum WalkEncoding {
    /// [`AnfWalk`] on the polynomial system itself (the default).
    Anf,
    /// [`WalkSat`] on the Tseitin CNF + native parity rows the CDCL
    /// solver sees.
    CnfXor,
}

/// Controls for [`walksat_decompose`].
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct WalkSatDecompositionOptions {
    /// Per-`solve` search budget and the base seed.
    pub walk: WalkSatOptions,
    pub encoding: WalkEncoding,
    /// Add the group trace row `Σ Tr(x_i) = Tr(x_R) + (m+1)Tr(a)`, as
    /// [`SatDecompositionOptions::trace_constraint`] does for CDCL.
    pub trace_constraint: bool,
    /// Models examined (lifted or rejected) before giving up.
    pub max_models: usize,
}

impl Default for WalkSatDecompositionOptions {
    fn default() -> Self {
        Self {
            walk: WalkSatOptions::default(),
            encoding: WalkEncoding::Anf,
            trace_constraint: true,
            max_models: 64,
        }
    }
}

/// What a [`walksat_decompose`] call did.  There is no `refuted` field:
/// local search never proves that no decomposition exists.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct WalkSatDecompositionStats {
    /// `solve` calls (one per model examined, plus a final one).
    pub solver_calls: usize,
    /// Models found, including ones that failed to lift.
    pub models: usize,
    /// Models that satisfied the system but did not lift to a point
    /// decomposition over the factor base (blocked and skipped).
    pub rejected: usize,
    /// Models that did not satisfy the original system — always zero
    /// unless an engine is wrong; a non-zero value ends the call.
    pub spurious: usize,
    /// The walk ended without a decomposition (budget or model cap).
    pub exhausted: bool,
    /// The instance shape is not handled here (three-point union base,
    /// system wider than 64 unknowns, `m < 2`).
    pub unsupported: bool,
    /// Engine work, summed over every `solve` call.
    pub walk: WalkStats,
}

/// Absolute trace `F_{2^n} → F_2`.
fn absolute_trace_bit(x: &F2mElement, n: u32, irr: &IrreduciblePoly) -> bool {
    let mut t = F2mElement::zero(n);
    let mut power = x.clone();
    for _ in 0..n {
        t = t.add(&power);
        power = power.square(irr);
    }
    !t.is_zero()
}

/// The trace row `sat_decompose_with` adds (Kosters–Yeo): for rational
/// points `Tr(x(P) + a)` is a homomorphism to `F_2`, so
/// `Σ_i Tr(x_i) = Tr(x_R) + (m + 1)·Tr(a)`.
fn trace_row(
    kc: &KoblitzCurve,
    fb: &FrobeniusFactorBase,
    x_r: &F2mElement,
    m: usize,
    n_vars: usize,
) -> F2BoolPoly {
    let irr = &kc.curve.irreducible;
    let rhs = absolute_trace_bit(x_r, kc.n, irr)
        ^ (m.is_multiple_of(2) && absolute_trace_bit(&kc.curve.a, kc.n, irr));
    let ell = fb.subspace_basis.len();
    let mut terms = Vec::new();
    for (j, basis_element) in fb.subspace_basis.iter().enumerate() {
        if absolute_trace_bit(basis_element, kc.n, irr) {
            for i in 0..m {
                terms.push(F2BoolMono::var((i * ell + j) as u32));
            }
        }
    }
    if rhs {
        terms.push(F2BoolMono::one());
    }
    F2BoolPoly::from_monos(terms, n_vars)
}

/// The per-target seed: the base seed mixed with the target abscissa.
fn target_seed(base: u64, x_r: &F2mElement) -> u64 {
    let mut s = SplitMix(base);
    let mut h = s.next();
    for &w in x_r.raw_bits() {
        h = SplitMix(h ^ w).next();
    }
    h
}

/// Either engine behind one interface.
enum Engine {
    Anf(AnfWalk),
    Cnf(WalkSat, usize),
}

impl Engine {
    fn solve(&mut self, opts: &WalkSatOptions) -> WalkResult {
        match self {
            Engine::Anf(w) => w.solve(opts),
            Engine::Cnf(w, _) => w.solve(opts),
        }
    }
    fn root(&self) -> u64 {
        match self {
            Engine::Anf(w) => w.model(),
            Engine::Cnf(w, n) => w.assignment() & AnfWalk::var_mask(*n),
        }
    }
    fn block(&mut self, root: u64) {
        match self {
            Engine::Anf(w) => w.block(root),
            Engine::Cnf(w, n) => w.block_assignment(root, *n),
        }
    }
    fn stats(&self) -> WalkStats {
        match self {
            Engine::Anf(w) => w.stats,
            Engine::Cnf(w, _) => w.stats,
        }
    }
}

/// **Local-search decomposition** (incomplete): look for
/// `R = P_1 + … + P_m` over the factor base with WalkSAT on the chained
/// Semaev system [`sat_decompose_with`] solves.
///
/// Returns factor-base indices (sorted) only for a model that satisfies
/// the original equations *and* lifts to points whose sum is the target
/// in the group.  `None` always means "not found", never "none exists".
/// Linear-subspace and subspace-subset bases are handled; a model whose
/// coordinates fall outside a subset base fails to lift and is blocked.
pub fn walksat_decompose(
    kc: &KoblitzCurve,
    fb: &FrobeniusFactorBase,
    index_of: &HashMap<(BigUint, BigUint), usize>,
    st: &FieldStructure,
    target: &BinaryPoint,
    m: usize,
    options: &WalkSatDecompositionOptions,
) -> (Option<Vec<usize>>, WalkSatDecompositionStats) {
    let mut stats = WalkSatDecompositionStats::default();
    let x_r = match target {
        BinaryPoint::Affine { x, .. } => x.clone(),
        BinaryPoint::Infinity => {
            stats.exhausted = true;
            return (None, stats);
        }
    };
    if fb.uses_ambient_basis() {
        stats.unsupported = true;
        stats.exhausted = true;
        return (None, stats);
    }
    let Some(sys) = crate::cryptanalysis::polynomial_reuse::build_decomposition_system_reusing(
        &fb.subspace_basis,
        &x_r,
        &kc.curve.b,
        m,
        st,
    ) else {
        stats.unsupported = true;
        stats.exhausted = true;
        return (None, stats);
    };
    let mut equations = sys.equations.clone();
    if options.trace_constraint {
        equations.push(trace_row(kc, fb, &x_r, m, sys.n_vars));
    }
    let mut engine = match options.encoding {
        WalkEncoding::Anf => Engine::Anf(AnfWalk::new(sys.n_vars, &equations)),
        WalkEncoding::CnfXor => Engine::Cnf(
            WalkSat::from_bool_system(sys.n_vars, &equations),
            sys.n_vars,
        ),
    };
    let mut walk = options.walk;
    walk.seed = target_seed(options.walk.seed, &x_r);
    let result = loop {
        stats.solver_calls += 1;
        if engine.solve(&walk) == WalkResult::Unknown {
            stats.exhausted = true;
            break None;
        }
        let root = engine.root();
        if !sys.equations.iter().all(|e| e.eval(root) == 0) {
            stats.spurious += 1;
            stats.exhausted = true;
            break None;
        }
        stats.models += 1;
        let xs: Vec<F2mElement> = (0..m)
            .map(|i| sys.summand_x(&fb.subspace_basis, root, i, kc.n))
            .collect();
        if let Some(idxs) = lift_candidate(kc, fb, index_of, &xs, target) {
            break Some(idxs);
        }
        stats.rejected += 1;
        if stats.models >= options.max_models {
            stats.exhausted = true;
            break None;
        }
        engine.block(root);
        // A fresh stream per call, still a function of (seed, target).
        walk.seed = SplitMix(walk.seed).next();
    };
    stats.walk = engine.stats();
    (result, stats)
}

/// **Portfolio decomposition** (complete): [`walksat_decompose`] first;
/// when it ends without a decomposition, the unchanged CDCL path
/// [`sat_decompose_with`] decides.  Verdicts are therefore exactly the
/// CDCL verdicts (a refutation always comes from CDCL), and when the
/// walk finds nothing the returned decomposition *is* the CDCL one.
///
/// The returned [`SatDecompositionStats`] are the CDCL ones (default
/// when the walk succeeded), with the walk's models added to `models`
/// and its spurious models to `spurious` — the relation collector fails
/// closed on either engine's bad model.
#[allow(clippy::too_many_arguments)]
pub fn walksat_then_sat_decompose(
    kc: &KoblitzCurve,
    fb: &FrobeniusFactorBase,
    index_of: &HashMap<(BigUint, BigUint), usize>,
    st: &FieldStructure,
    target: &BinaryPoint,
    m: usize,
    max_models: usize,
    macaulay_degree: Option<u32>,
    sat_options: SatDecompositionOptions,
    walk_options: &WalkSatDecompositionOptions,
) -> (Option<Vec<usize>>, SatDecompositionStats) {
    let (found, w) = walksat_decompose(kc, fb, index_of, st, target, m, walk_options);
    if w.spurious != 0 {
        let stats = SatDecompositionStats {
            models: w.models,
            spurious: w.spurious,
            exhausted: true,
            ..SatDecompositionStats::default()
        };
        return (None, stats);
    }
    if found.is_some() {
        let stats = SatDecompositionStats {
            models: w.models,
            ..SatDecompositionStats::default()
        };
        return (found, stats);
    }
    let (out, mut stats) = sat_decompose_with(
        kc,
        fb,
        index_of,
        st,
        target,
        m,
        max_models,
        macaulay_degree,
        sat_options,
    );
    stats.models += w.models;
    (out, stats)
}

#[cfg(test)]
mod tests;
