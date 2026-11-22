//! MILP encoding of the minimum-active-S-box problem and a small from-scratch
//! branch-and-bound solver for 0/1 models.
//!
//! The encoding follows A. Mouha, Q. Wang, D. Gu and B. Preneel,
//! "Differential and linear cryptanalysis using mixed-integer linear
//! programming" (Inscrypt 2011): binary variables mark active S-boxes (and,
//! at bit level, the bits of S-box input and output differences or masks),
//! the objective is the number of active S-boxes, and each linear layer is a
//! set of linear inequalities.
//!
//! * **Word level**: per connected component of a linear layer a dummy `d`
//!   with `d >= v` for every word variable `v`; if the component's feasible
//!   patterns are exactly `|P| + |Q| >= b` (a maximum-distance-separable
//!   column, `b = 5` for AES) the single inequality `sum v >= b d`, otherwise
//!   one inequality `sum_{v not in F} v >= d` per maximal infeasible pattern
//!   `F` ([`WordComp::maximal_forbidden`]).
//! * **Bit level** (permutation linear layers only): each S-box excludes its
//!   infeasible `(input, output)` bit patterns by one inequality per prime
//!   implicant cube of the DDT (LAT) support.
//!
//! [`MilpModel`] is a plain 0/1 model with an exporter to CPLEX `.lp` text
//! ([`MilpModel::to_lp`]) so that an external solver (HiGHS, CBC, Gurobi) can
//! be used in place of the built-in solver, which is a depth-first branch and
//! bound over the LP relaxation (dense two-phase simplex, objective
//! integrality rounding; rows are generated lazily, a row entering the LP only
//! when an LP optimum violates it). The LP is solved in `f64` with tolerances
//! (`1e-6`), so MILP optima are float-based cross-checks, not exact
//! certificates: an integral-looking LP point is rounded and re-checked
//! exactly against every row, and when that check fails the node is branched
//! on rather than dropped, but a pruning decision taken on a bound within
//! float tolerance is not independently certified. Use the value, word and SAT
//! engines for exact statements. Optionally the already-proved minima of shorter
//! windows are added as cuts (`window_cuts`), the MILP form of Matsui's
//! per-round bounds; they are only added when all stages repeat.

use super::sat::Level;
use super::{
    transition_nogoods, word_components, Direction, Stage, TrailError, TrailModel, WordComp,
};
use crate::cryptanalysis::sym_ir::Primitive;

/// Sense of a linear constraint.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Sense {
    /// `sum <= rhs`.
    Le,
    /// `sum >= rhs`.
    Ge,
    /// `sum == rhs`.
    Eq,
}

/// A linear constraint `sum coef * x_var (sense) rhs`.
#[derive(Clone, Debug)]
pub struct MilpRow {
    /// `(variable, coefficient)` terms.
    pub terms: Vec<(usize, f64)>,
    /// Comparison.
    pub sense: Sense,
    /// Right-hand side.
    pub rhs: f64,
}

/// A 0/1 integer program: minimise `obj . x` subject to the rows, `x` binary.
#[derive(Clone, Debug, Default)]
pub struct MilpModel {
    /// Variable names (used by [`MilpModel::to_lp`]).
    pub names: Vec<String>,
    /// Objective coefficient per variable.
    pub obj: Vec<f64>,
    /// Constraints.
    pub rows: Vec<MilpRow>,
}

/// Options for [`MilpModel::solve`].
#[derive(Clone, Copy, Debug)]
pub struct MilpSolveOptions {
    /// Maximum number of branch-and-bound nodes.
    pub node_budget: u64,
    /// Wall-clock limit in milliseconds (`BudgetExceeded` when hit).
    pub time_limit_ms: u64,
}

impl Default for MilpSolveOptions {
    fn default() -> Self {
        MilpSolveOptions {
            node_budget: 2_000_000,
            time_limit_ms: u64::MAX,
        }
    }
}

/// An optimal solution of a [`MilpModel`].
#[derive(Clone, Debug)]
pub struct MilpSolution {
    /// Optimal objective value.
    pub objective: f64,
    /// Value of every variable.
    pub values: Vec<bool>,
    /// Branch-and-bound nodes (LP relaxations) solved.
    pub nodes: u64,
}

impl MilpModel {
    /// An empty model.
    pub fn new() -> Self {
        Self::default()
    }

    /// Add a binary variable with objective coefficient `obj`; returns its
    /// index.
    pub fn add_var(&mut self, name: &str, obj: f64) -> usize {
        self.names.push(name.to_string());
        self.obj.push(obj);
        self.names.len() - 1
    }

    /// Add the constraint `sum terms (sense) rhs`.
    pub fn add_row(&mut self, terms: Vec<(usize, f64)>, sense: Sense, rhs: f64) {
        self.rows.push(MilpRow { terms, sense, rhs });
    }

    /// Number of variables.
    pub fn num_vars(&self) -> usize {
        self.names.len()
    }

    /// Render the model in CPLEX `.lp` format (accepted by HiGHS, CBC,
    /// SCIP and Gurobi).
    pub fn to_lp(&self) -> String {
        fn term(c: f64, name: &str, first: bool) -> String {
            let sign = if c < 0.0 { "-" } else { "+" };
            if first {
                format!("{}{} {}", if c < 0.0 { "- " } else { "" }, c.abs(), name)
            } else {
                format!(" {sign} {} {}", c.abs(), name)
            }
        }
        let mut s = String::from(
            "\\ generated by cryptanalysis_suite sym_techniques::trails::milp\nMinimize\n obj:",
        );
        let mut first = true;
        for (i, &c) in self.obj.iter().enumerate() {
            if c != 0.0 {
                s.push(' ');
                s.push_str(&term(c, &self.names[i], first));
                first = false;
            }
        }
        if first {
            s.push_str(" 0 ");
            s.push_str(self.names.first().map_or("x", |n| n.as_str()));
        }
        s.push_str("\nSubject To\n");
        for (r, row) in self.rows.iter().enumerate() {
            s.push_str(&format!(" c{r}:"));
            let mut first = true;
            for &(v, c) in &row.terms {
                s.push(' ');
                s.push_str(&term(c, &self.names[v], first));
                first = false;
            }
            if first {
                s.push_str(" 0 ");
                s.push_str(self.names.first().map_or("x", |n| n.as_str()));
            }
            let op = match row.sense {
                Sense::Le => "<=",
                Sense::Ge => ">=",
                Sense::Eq => "=",
            };
            s.push_str(&format!(" {op} {}\n", row.rhs));
        }
        s.push_str("Binary\n");
        for n in &self.names {
            s.push(' ');
            s.push_str(n);
            s.push('\n');
        }
        s.push_str("End\n");
        s
    }

    /// Solve to optimality by branch and bound over the LP relaxation.
    /// Returns `Ok(None)` if infeasible and
    /// [`TrailError::BudgetExceeded`] if the node budget runs out.
    pub fn solve(&self, opts: &MilpSolveOptions) -> Result<Option<MilpSolution>, TrailError> {
        let n = self.num_vars();
        let int_obj = self.obj.iter().all(|c| (c - c.round()).abs() < 1e-12);
        let mut bb = Bb {
            m: self,
            int_obj,
            best: None,
            nodes: 0,
            budget: opts.node_budget,
            aborted: false,
            active: vec![false; self.rows.len()],
            started: std::time::Instant::now(),
            time_limit_ms: opts.time_limit_ms,
            deadline: std::time::Instant::now()
                .checked_add(std::time::Duration::from_millis(opts.time_limit_ms)),
        };
        let mut fixed = vec![-1i8; n];
        bb.rec(&mut fixed);
        if bb.aborted {
            return Err(TrailError::BudgetExceeded);
        }
        Ok(bb.best.map(|(objective, values)| MilpSolution {
            objective,
            values,
            nodes: bb.nodes,
        }))
    }

    fn feasible(&self, x: &[bool]) -> bool {
        self.rows.iter().all(|r| {
            let lhs: f64 = r
                .terms
                .iter()
                .map(|&(v, c)| if x[v] { c } else { 0.0 })
                .sum();
            match r.sense {
                Sense::Le => lhs <= r.rhs + 1e-9,
                Sense::Ge => lhs >= r.rhs - 1e-9,
                Sense::Eq => (lhs - r.rhs).abs() <= 1e-9,
            }
        })
    }
}

struct Bb<'a> {
    m: &'a MilpModel,
    int_obj: bool,
    best: Option<(f64, Vec<bool>)>,
    nodes: u64,
    budget: u64,
    aborted: bool,
    /// Rows currently part of the LP relaxation (lazily generated: a row is
    /// added, globally, once an LP optimum violates it).
    active: Vec<bool>,
    started: std::time::Instant,
    time_limit_ms: u64,
    deadline: Option<std::time::Instant>,
}

/// Most violated rows added per separation round.
const ROWS_PER_ROUND: usize = 64;

impl Bb<'_> {
    /// Build the LP rows over the free variables from the active rows, or
    /// `None` if an active row with all variables fixed is violated.
    #[allow(clippy::type_complexity)]
    fn assemble(
        &self,
        fixed: &[i8],
        idx: &[usize],
    ) -> Option<Vec<(Vec<(usize, f64)>, Sense, f64)>> {
        let mut rows = Vec::new();
        for (ri, r) in self.m.rows.iter().enumerate() {
            if !self.active[ri] {
                continue;
            }
            let mut rhs = r.rhs;
            let mut terms = Vec::new();
            for &(v, c) in &r.terms {
                match fixed[v] {
                    1 => rhs -= c,
                    0 => {}
                    _ => terms.push((idx[v], c)),
                }
            }
            if terms.is_empty() {
                let ok = match r.sense {
                    Sense::Le => 0.0 <= rhs + 1e-9,
                    Sense::Ge => 0.0 >= rhs - 1e-9,
                    Sense::Eq => rhs.abs() <= 1e-9,
                };
                if !ok {
                    return None;
                }
            } else {
                rows.push((terms, r.sense, rhs));
            }
        }
        Some(rows)
    }

    fn rec(&mut self, fixed: &mut Vec<i8>) {
        if self.aborted {
            return;
        }
        self.nodes += 1;
        if self.nodes > self.budget
            || self.started.elapsed().as_millis() > u128::from(self.time_limit_ms)
        {
            self.aborted = true;
            return;
        }
        let free: Vec<usize> = (0..fixed.len()).filter(|&i| fixed[i] < 0).collect();
        let mut idx = vec![usize::MAX; fixed.len()];
        for (k, &v) in free.iter().enumerate() {
            idx[v] = k;
        }
        let konst: f64 = (0..fixed.len())
            .filter(|&i| fixed[i] == 1)
            .map(|i| self.m.obj[i])
            .sum();
        let c: Vec<f64> = free.iter().map(|&v| self.m.obj[v]).collect();
        let (lp_obj, y) = loop {
            if self.started.elapsed().as_millis() > u128::from(self.time_limit_ms) {
                self.aborted = true;
                return;
            }
            let Some(rows) = self.assemble(fixed, &idx) else {
                return;
            };
            let sol = if free.is_empty() {
                (0.0, Vec::new())
            } else {
                match solve_lp(free.len(), &c, &rows, self.deadline) {
                    LpOutcome::Optimal(o, y) => (o, y),
                    LpOutcome::Infeasible => return,
                    LpOutcome::Aborted => {
                        self.aborted = true;
                        return;
                    }
                }
            };
            let xv = |v: usize| match fixed[v] {
                1 => 1.0,
                0 => 0.0,
                _ => sol.1[idx[v]],
            };
            let mut viol: Vec<(f64, usize)> = Vec::new();
            for (ri, r) in self.m.rows.iter().enumerate() {
                if self.active[ri] {
                    continue;
                }
                let lhs: f64 = r.terms.iter().map(|&(v, co)| co * xv(v)).sum();
                let amount = match r.sense {
                    Sense::Le => lhs - r.rhs,
                    Sense::Ge => r.rhs - lhs,
                    Sense::Eq => (lhs - r.rhs).abs(),
                };
                if amount > 1e-6 {
                    viol.push((amount, ri));
                }
            }
            if viol.is_empty() {
                break sol;
            }
            viol.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap());
            for &(_, ri) in viol.iter().take(ROWS_PER_ROUND) {
                self.active[ri] = true;
            }
        };
        let mut lower = konst + lp_obj;
        if self.int_obj {
            lower = (lower - 1e-6).ceil();
        }
        if let Some((inc, _)) = &self.best {
            if lower >= inc - 1e-9 {
                return;
            }
        }
        // Most fractional free variable.
        let mut pick: Option<(usize, f64)> = None;
        for (k, &yv) in y.iter().enumerate() {
            let frac = (yv - yv.round()).abs();
            if frac > 1e-6 && pick.is_none_or(|(_, f)| frac > f) {
                pick = Some((k, frac));
            }
        }
        if pick.is_none() {
            // Integral to tolerance: round and check exactly against the rows.
            let mut x: Vec<bool> = (0..fixed.len()).map(|i| fixed[i] == 1).collect();
            for (k, &v) in free.iter().enumerate() {
                x[v] = y[k] > 0.5;
            }
            if self.m.feasible(&x) {
                let obj: f64 = x
                    .iter()
                    .enumerate()
                    .filter(|(_, &b)| b)
                    .map(|(i, _)| self.m.obj[i])
                    .sum();
                if self.best.as_ref().is_none_or(|(b, _)| obj < b - 1e-9) {
                    self.best = Some((obj, x));
                }
                return;
            }
            // Integral-looking LP point that fails the exact check (float
            // tolerance artefact): do not drop the node; branch on the free
            // variable furthest from an integer, however small.
            let mut far: Option<(usize, f64)> = None;
            for (k, &yv) in y.iter().enumerate() {
                let frac = (yv - yv.round()).abs();
                if far.is_none_or(|(_, f)| frac > f) {
                    far = Some((k, frac));
                }
            }
            // With no free variable the assignment is fully fixed and the
            // exact check failing means this leaf is genuinely infeasible.
            pick = far;
        }
        if let Some((k, _)) = pick {
            let v = free[k];
            let first = if y[k] >= 0.5 { 1 } else { 0 };
            for val in [first, 1 - first] {
                fixed[v] = val;
                self.rec(fixed);
                fixed[v] = -1;
                if self.aborted {
                    return;
                }
            }
        }
    }
}

/// Result of an LP relaxation solve.
enum LpOutcome {
    /// Optimum and a primal solution.
    Optimal(f64, Vec<f64>),
    /// No point satisfies the rows.
    Infeasible,
    /// The simplex was stopped (deadline, iteration cap or numerical
    /// failure); nothing is known about the LP.
    Aborted,
}

/// Minimise `c . y` over `0 <= y <= 1` and the rows; dense two-phase simplex.
fn solve_lp(
    n: usize,
    c: &[f64],
    rows: &[(Vec<(usize, f64)>, Sense, f64)],
    deadline: Option<std::time::Instant>,
) -> LpOutcome {
    let m = rows.len() + n;
    // Normalised rows with rhs >= 0: (dense coefs, sense, rhs).
    let mut dense: Vec<(Vec<f64>, Sense, f64)> = Vec::with_capacity(m);
    for (terms, sense, rhs) in rows {
        let mut a = vec![0.0; n];
        for &(v, co) in terms {
            a[v] += co;
        }
        dense.push((a, *sense, *rhs));
    }
    for i in 0..n {
        let mut a = vec![0.0; n];
        a[i] = 1.0;
        dense.push((a, Sense::Le, 1.0));
    }
    let mut n_slack = 0;
    let mut n_art = 0;
    for (a, s, b) in dense.iter_mut() {
        if *b < 0.0 {
            for x in a.iter_mut() {
                *x = -*x;
            }
            *b = -*b;
            *s = match *s {
                Sense::Le => Sense::Ge,
                Sense::Ge => Sense::Le,
                Sense::Eq => Sense::Eq,
            };
        }
        match s {
            Sense::Le => n_slack += 1,
            Sense::Ge => {
                n_slack += 1;
                n_art += 1;
            }
            Sense::Eq => n_art += 1,
        }
    }
    let cols = n + n_slack + n_art;
    let stride = cols + 1;
    let mut t = vec![0.0f64; m * stride];
    let mut basis = vec![0usize; m];
    let (mut si, mut ai) = (n, n + n_slack);
    for (i, (a, s, b)) in dense.iter().enumerate() {
        t[i * stride..i * stride + n].copy_from_slice(a);
        t[i * stride + cols] = *b;
        match s {
            Sense::Le => {
                t[i * stride + si] = 1.0;
                basis[i] = si;
                si += 1;
            }
            Sense::Ge => {
                t[i * stride + si] = -1.0;
                si += 1;
                t[i * stride + ai] = 1.0;
                basis[i] = ai;
                ai += 1;
            }
            Sense::Eq => {
                t[i * stride + ai] = 1.0;
                basis[i] = ai;
                ai += 1;
            }
        }
    }
    let enter_all = n + n_slack;
    if n_art > 0 {
        let mut cost1 = vec![0.0; cols];
        for x in cost1.iter_mut().skip(enter_all) {
            *x = 1.0;
        }
        let Some(obj) = simplex(&mut t, m, stride, &mut basis, &cost1, cols, deadline) else {
            return LpOutcome::Aborted;
        };
        if obj > 1e-7 {
            return LpOutcome::Infeasible;
        }
        // Pivot remaining artificials out where possible.
        for i in 0..m {
            if basis[i] >= enter_all {
                if let Some(j) = (0..enter_all).find(|&j| t[i * stride + j].abs() > 1e-9) {
                    pivot(&mut t, m, stride, i, j, None);
                    basis[i] = j;
                }
            }
        }
    }
    let mut cost2 = vec![0.0; cols];
    cost2[..n].copy_from_slice(c);
    let Some(obj) = simplex(&mut t, m, stride, &mut basis, &cost2, enter_all, deadline) else {
        return LpOutcome::Aborted;
    };
    let mut y = vec![0.0; n];
    for i in 0..m {
        if basis[i] < n {
            y[basis[i]] = t[i * stride + cols].clamp(0.0, 1.0);
        }
    }
    LpOutcome::Optimal(obj, y)
}

fn pivot(t: &mut [f64], m: usize, stride: usize, r: usize, j: usize, z: Option<&mut Vec<f64>>) {
    let p = t[r * stride + j];
    for k in 0..stride {
        t[r * stride + k] /= p;
    }
    let prow: Vec<f64> = t[r * stride..(r + 1) * stride].to_vec();
    for i in 0..m {
        if i != r {
            let f = t[i * stride + j];
            if f.abs() > 1e-12 {
                for k in 0..stride {
                    t[i * stride + k] -= f * prow[k];
                }
            }
        }
    }
    if let Some(z) = z {
        let f = z[j];
        if f.abs() > 1e-12 {
            for k in 0..stride {
                z[k] -= f * prow[k];
            }
        }
    }
}

/// Primal simplex on the tableau `t` (rows `m`, row stride `stride`, rhs in
/// the last column) from the current basis; columns `>= enter_limit` never
/// enter. Returns the objective value, or `None` on deadline, iteration
/// failure or unboundedness.
fn simplex(
    t: &mut [f64],
    m: usize,
    stride: usize,
    basis: &mut [usize],
    cost: &[f64],
    enter_limit: usize,
    deadline: Option<std::time::Instant>,
) -> Option<f64> {
    let cols = stride - 1;
    let mut z = vec![0.0; stride];
    z[..cols].copy_from_slice(cost);
    for i in 0..m {
        let cb = cost[basis[i]];
        if cb != 0.0 {
            for k in 0..stride {
                z[k] -= cb * t[i * stride + k];
            }
        }
    }
    let mut iter = 0usize;
    loop {
        iter += 1;
        if iter > 200_000
            || (iter.is_multiple_of(64) && deadline.is_some_and(|d| std::time::Instant::now() > d))
        {
            return None;
        }
        let bland = iter > 5_000;
        let mut enter = None;
        let mut best = -1e-9;
        for j in 0..enter_limit {
            if z[j] < best {
                enter = Some(j);
                if bland {
                    break;
                }
                best = z[j];
            }
        }
        let Some(j) = enter else {
            return Some(-z[cols]);
        };
        let mut row = None;
        let mut best_ratio = f64::INFINITY;
        for i in 0..m {
            let a = t[i * stride + j];
            if a > 1e-9 {
                let ratio = t[i * stride + cols] / a;
                if ratio < best_ratio - 1e-12
                    || (ratio < best_ratio + 1e-12 && row.is_some_and(|r| basis[i] < basis[r]))
                {
                    best_ratio = ratio;
                    row = Some(i);
                }
            }
        }
        let r = row?;
        pivot(t, m, stride, r, j, Some(&mut z));
        basis[r] = j;
    }
}

// ── Encodings ────────────────────────────────────────────────────────────

/// A MILP encoding of a trail model.
#[derive(Clone, Debug)]
pub struct TrailMilp {
    /// The model.
    pub milp: MilpModel,
    /// `active[s][j]`: variable index of S-box `j` of stage `s`.
    pub active: Vec<Vec<usize>>,
    /// The encoding that produced it.
    pub level: Level,
}

fn add_window_cuts(milp: &mut MilpModel, active: &[Vec<usize>], cuts: &[(usize, u32)]) {
    let n = active.len();
    for &(len, bound) in cuts {
        if len > n || bound == 0 {
            continue;
        }
        for s in 0..=n - len {
            let terms = active[s..s + len]
                .iter()
                .flatten()
                .map(|&v| (v, 1.0))
                .collect();
            milp.add_row(terms, Sense::Ge, f64::from(bound));
        }
    }
}

/// Word-level encoding. `cuts` lists `(window length, minimum active)`
/// facts to add as redundant constraints (pass only facts that hold for
/// every window of the model).
pub fn encode_word(model: &TrailModel, cuts: &[(usize, u32)]) -> Result<TrailMilp, TrailError> {
    let mut milp = MilpModel::new();
    let mut active: Vec<Vec<usize>> = Vec::new();
    for (s, st) in model.stages.iter().enumerate() {
        active.push(
            (0..st.count)
                .map(|j| milp.add_var(&format!("x_{s}_{j}"), 1.0))
                .collect(),
        );
    }
    milp.add_row(
        active[0].iter().map(|&v| (v, 1.0)).collect(),
        Sense::Ge,
        1.0,
    );
    for s in 1..model.stages.len() {
        for (ci, comp) in word_components(&model.stages[s - 1], &model.stages[s])?
            .iter()
            .enumerate()
        {
            encode_comp(&mut milp, &active, s, ci, comp);
        }
    }
    add_window_cuts(&mut milp, &active, cuts);
    Ok(TrailMilp {
        milp,
        active,
        level: Level::Word,
    })
}

fn encode_comp(milp: &mut MilpModel, active: &[Vec<usize>], s: usize, ci: usize, comp: &WordComp) {
    let vars: Vec<usize> = comp
        .out_words
        .iter()
        .map(|&j| active[s - 1][j])
        .chain(comp.in_words.iter().map(|&k| active[s][k]))
        .collect();
    let d = milp.add_var(&format!("d_{s}_{ci}"), 0.0);
    for &v in &vars {
        milp.add_row(vec![(d, 1.0), (v, -1.0)], Sense::Ge, 0.0);
    }
    if let Some(b) = comp.threshold() {
        let mut terms: Vec<(usize, f64)> = vars.iter().map(|&v| (v, 1.0)).collect();
        terms.push((d, -(b as f64)));
        milp.add_row(terms, Sense::Ge, 0.0);
    } else {
        for f in comp.maximal_forbidden() {
            let mut terms: Vec<(usize, f64)> = vars
                .iter()
                .enumerate()
                .filter(|(i, _)| f >> i & 1 == 0)
                .map(|(_, &v)| (v, 1.0))
                .collect();
            terms.push((d, -1.0));
            milp.add_row(terms, Sense::Ge, 0.0);
        }
    }
}

/// Bit-level encoding; every inter-stage linear layer must be a bit
/// permutation. `cuts` as for [`encode_word`].
pub fn encode_bit(model: &TrailModel, cuts: &[(usize, u32)]) -> Result<TrailMilp, TrailError> {
    if model.max_width() > 6 {
        return Err(TrailError::TooLarge(
            "bit level needs S-box width <= 6".into(),
        ));
    }
    let mut milp = MilpModel::new();
    let n = model.state_bits;
    let mut xin: Vec<usize> = (0..n)
        .map(|i| milp.add_var(&format!("xi_0_{i}"), 0.0))
        .collect();
    let mut active = Vec::new();
    for (s, st) in model.stages.iter().enumerate() {
        if s > 0 {
            let perm = st
                .lin
                .as_ref()
                .and_then(|l| l.as_permutation())
                .ok_or_else(|| {
                    TrailError::Unsupported("bit-level MILP needs permutation linear layers".into())
                })?;
            xin = (0..n).map(|i| xin_prev_alias(&xin, &perm, i)).collect();
        }
        let yout: Vec<usize> = (0..n)
            .map(|i| milp.add_var(&format!("y_{s}_{i}"), 0.0))
            .collect();
        let w = st.width;
        let cubes = transition_nogoods(&st.sbox, model.direction);
        let mut act = Vec::new();
        for j in 0..st.count {
            let xs: Vec<usize> = (0..w).map(|i| xin[j * w + i]).collect();
            let ys: Vec<usize> = (0..w).map(|i| yout[j * w + i]).collect();
            for &(mask, val) in &cubes {
                let mut terms = Vec::new();
                let mut rhs = 1.0;
                for b in 0..2 * w {
                    if mask >> b & 1 == 1 {
                        let v = if b < w { xs[b] } else { ys[b - w] };
                        if val >> b & 1 == 1 {
                            terms.push((v, -1.0));
                            rhs -= 1.0;
                        } else {
                            terms.push((v, 1.0));
                        }
                    }
                }
                milp.add_row(terms, Sense::Ge, rhs);
            }
            let a = milp.add_var(&format!("a_{s}_{j}"), 1.0);
            for &v in &xs {
                milp.add_row(vec![(a, 1.0), (v, -1.0)], Sense::Ge, 0.0);
            }
            let mut terms: Vec<(usize, f64)> = xs.iter().map(|&v| (v, 1.0)).collect();
            terms.push((a, -1.0));
            milp.add_row(terms, Sense::Ge, 0.0);
            act.push(a);
        }
        active.push(act);
        // Next stage inputs are built from `yout` at the top of the loop.
        xin = yout;
    }
    milp.add_row(
        active[0].iter().map(|&v| (v, 1.0)).collect(),
        Sense::Ge,
        1.0,
    );
    add_window_cuts(&mut milp, &active, cuts);
    Ok(TrailMilp {
        milp,
        active,
        level: Level::Bit,
    })
}

/// Input bit `i` of the next stage is previous output bit `perm[i]`.
fn xin_prev_alias(prev: &[usize], perm: &[usize], i: usize) -> usize {
    prev[perm[i]]
}

/// Options for [`min_active_sboxes`].
#[derive(Clone, Copy, Debug)]
pub struct MilpOptions {
    /// Encoding choice (`Auto`: bit level for S-box width at most 4 with
    /// permutation layers, word level otherwise).
    pub level: Level,
    /// Branch-and-bound node budget per solve.
    pub node_budget: u64,
    /// Wall-clock limit per solve in milliseconds.
    pub time_limit_ms: u64,
    /// Add the proved minima of shorter windows as cuts (only when all
    /// stages repeat).
    pub window_cuts: bool,
}

impl Default for MilpOptions {
    fn default() -> Self {
        MilpOptions {
            level: Level::Auto,
            node_budget: 2_000_000,
            time_limit_ms: u64::MAX,
            window_cuts: true,
        }
    }
}

/// Result of a MILP-based search.
#[derive(Clone, Debug)]
pub struct MilpResult {
    /// Minimum number of active S-boxes found by the solver.
    pub min_active: u32,
    /// Per stage, the active S-boxes of the optimal solution.
    pub pattern: Vec<Vec<usize>>,
    /// Encoding used.
    pub level: Level,
    /// Minimum for `r` stages, `r = 1..=stages`, as solved in turn.
    pub minima_by_rounds: Vec<u32>,
    /// Total branch-and-bound nodes over all solves.
    pub nodes: u64,
    /// Variables of the final model.
    pub n_vars: usize,
    /// Rows of the final model.
    pub n_rows: usize,
}

fn same_stage(a: &Stage, b: &Stage) -> bool {
    a.width == b.width
        && a.count == b.count
        && a.lin == b.lin
        && (0..1u32 << a.width).all(|x| a.sbox.lookup(x) == b.sbox.lookup(x))
}

/// Whether every stage after the first repeats and the first has the same
/// S-box, so that the minimum over `L` stages is window-independent.
fn uniform(model: &TrailModel) -> bool {
    let st = &model.stages;
    st.len() > 2
        && (2..st.len()).all(|i| same_stage(&st[i], &st[1]))
        && st[0].width == st[1].width
        && st[0].count == st[1].count
        && (0..1u32 << st[0].width).all(|x| st[0].sbox.lookup(x) == st[1].sbox.lookup(x))
}

/// MILP-based minimum number of active S-boxes of a trail model, solved with
/// the built-in branch and bound.
pub fn min_active_sboxes_model(
    model: &TrailModel,
    opts: &MilpOptions,
) -> Result<MilpResult, TrailError> {
    let n = model.num_stages();
    let level = match opts.level {
        Level::Auto => {
            if model.max_width() <= 4
                && model
                    .stages
                    .iter()
                    .skip(1)
                    .all(|s| s.lin.as_ref().and_then(|l| l.as_permutation()).is_some())
            {
                Level::Bit
            } else {
                Level::Word
            }
        }
        l => l,
    };
    let can_cut = opts.window_cuts && uniform(model);
    let mut minima: Vec<u32> = Vec::new();
    let mut nodes = 0u64;
    let mut last = None;
    for r in 1..=n {
        let sub = TrailModel {
            stages: model.stages[..r].to_vec(),
            ..model.clone()
        };
        let cuts: Vec<(usize, u32)> = if can_cut {
            minima
                .iter()
                .enumerate()
                .map(|(i, &b)| (i + 1, b))
                .collect()
        } else {
            Vec::new()
        };
        let enc = match level {
            Level::Bit => encode_bit(&sub, &cuts)?,
            _ => encode_word(&sub, &cuts)?,
        };
        let sol = enc
            .milp
            .solve(&MilpSolveOptions {
                node_budget: opts.node_budget,
                time_limit_ms: opts.time_limit_ms,
            })?
            .ok_or_else(|| TrailError::Unsupported("MILP is infeasible".into()))?;
        nodes += sol.nodes;
        minima.push(sol.objective.round() as u32);
        if r == n {
            let pattern = enc
                .active
                .iter()
                .map(|vs| {
                    vs.iter()
                        .enumerate()
                        .filter(|(_, &v)| sol.values[v])
                        .map(|(j, _)| j)
                        .collect()
                })
                .collect();
            last = Some((pattern, enc.milp.num_vars(), enc.milp.rows.len()));
        }
    }
    let (pattern, n_vars, n_rows) = last.unwrap();
    Ok(MilpResult {
        min_active: *minima.last().unwrap(),
        pattern,
        level,
        minima_by_rounds: minima,
        nodes,
        n_vars,
        n_rows,
    })
}

/// MILP-based minimum number of active S-boxes over the first `rounds` rounds
/// of `p`.
pub fn min_active_sboxes(
    p: &Primitive,
    rounds: usize,
    direction: Direction,
    opts: &MilpOptions,
) -> Result<MilpResult, TrailError> {
    let model = TrailModel::from_primitive(p, rounds, direction)?;
    min_active_sboxes_model(&model, opts)
}
