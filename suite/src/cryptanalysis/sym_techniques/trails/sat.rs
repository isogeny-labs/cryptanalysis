//! SAT encoding of "at most `k` active S-boxes", solved with the repository's
//! CDCL solver ([`crate::cryptanalysis::sat`]).
//!
//! Two encodings of the same [`TrailModel`]:
//!
//! * **Word level** ([`Level::Word`]): one Boolean per S-box (active or not)
//!   and, for every connected component of every linear layer, a dummy `d`
//!   with `v -> d` for each word variable `v` of the component and, for each
//!   maximal infeasible pattern `F` of [`WordComp::maximal_forbidden`](super::WordComp::maximal_forbidden), the
//!   clause `d -> OR_{v not in F} v`. For an MDS column this is the
//!   branch-number constraint of A. Mouha, Q. Wang, D. Gu and B. Preneel,
//!   "Differential and linear cryptanalysis using mixed-integer linear
//!   programming" (Inscrypt 2011), expressed as clauses.
//! * **Bit level** ([`Level::Bit`]): one Boolean per state bit before and
//!   after every S-box layer. Each S-box forbids its infeasible
//!   `(input, output)` difference (mask) pairs by prime-implicant clauses of
//!   the DDT (LAT) support; linear layers are native XOR constraints of the
//!   solver; the activity of an S-box is the OR of its input bits. This
//!   captures facts the word model cannot, for example that a one-bit input
//!   difference of the PRESENT S-box has an output difference of weight at
//!   least two.
//!
//! The cardinality bound is a sequential counter (C. Sinz, "Towards an
//! optimal CNF encoding of Boolean cardinality constraints", CP 2005). The
//! minimum is found by descent: solve with no bound, then with `count - 1`
//! until UNSAT. The final UNSAT answer is the lower-bound argument, relative
//! to the model.

use super::{transition_nogoods, word_components, Direction, TrailError, TrailModel};
use crate::cryptanalysis::sat::{SolveResult, Solver};
use crate::cryptanalysis::sym_ir::Primitive;

/// Which encoding to use.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Level {
    /// Bit level for S-boxes of width at most 4, word level otherwise.
    Auto,
    /// Word-level (truncated) encoding.
    Word,
    /// Bit-level encoding (S-box width at most 6).
    Bit,
}

/// A CNF-with-XOR encoding of a trail model, before any cardinality bound.
#[derive(Clone, Debug)]
pub struct TrailCnf {
    /// Number of variables (DIMACS numbering `1..=n_vars`).
    pub n_vars: u32,
    /// Clauses over signed variables.
    pub clauses: Vec<Vec<i32>>,
    /// XOR constraints `x_1 ^ ... ^ x_n = 0` as lists of variables.
    pub xors: Vec<Vec<u32>>,
    /// `active[s][j]`: the variable that is true iff S-box `j` of stage `s`
    /// is active.
    pub active: Vec<Vec<u32>>,
    /// Which encoding produced this CNF.
    pub level: Level,
}

impl TrailCnf {
    fn new(level: Level) -> Self {
        TrailCnf {
            n_vars: 0,
            clauses: Vec::new(),
            xors: Vec::new(),
            active: Vec::new(),
            level,
        }
    }

    fn var(&mut self) -> u32 {
        self.n_vars += 1;
        self.n_vars
    }

    /// Append the sequential-counter clauses for "at most `k` of the active
    /// S-boxes".
    pub fn add_at_most(&mut self, k: usize) {
        let lits: Vec<u32> = self.active.iter().flatten().copied().collect();
        let n = lits.len();
        if k >= n {
            return;
        }
        if k == 0 {
            for &l in &lits {
                self.clauses.push(vec![-(l as i32)]);
            }
            return;
        }
        // s[i][j]: among the first i+1 literals at least j+1 are true.
        let mut s = vec![vec![0u32; k]; n - 1];
        for row in s.iter_mut() {
            for v in row.iter_mut() {
                *v = self.var();
            }
        }
        let x = |i: usize| lits[i] as i32;
        self.clauses.push(vec![-x(0), s[0][0] as i32]);
        for j in 1..k {
            self.clauses.push(vec![-(s[0][j] as i32)]);
        }
        for i in 1..n - 1 {
            self.clauses.push(vec![-x(i), s[i][0] as i32]);
            self.clauses
                .push(vec![-(s[i - 1][0] as i32), s[i][0] as i32]);
            for j in 1..k {
                self.clauses
                    .push(vec![-x(i), -(s[i - 1][j - 1] as i32), s[i][j] as i32]);
                self.clauses
                    .push(vec![-(s[i - 1][j] as i32), s[i][j] as i32]);
            }
            self.clauses.push(vec![-x(i), -(s[i - 1][k - 1] as i32)]);
        }
        self.clauses
            .push(vec![-x(n - 1), -(s[n - 2][k - 1] as i32)]);
    }

    /// Render as DIMACS CNF; XOR constraints use the `x` line prefix of
    /// CryptoMiniSat.
    pub fn to_dimacs(&self) -> String {
        let mut out = format!("p cnf {} {}\n", self.n_vars, self.clauses.len());
        for c in &self.clauses {
            for l in c {
                out.push_str(&format!("{l} "));
            }
            out.push_str("0\n");
        }
        for x in &self.xors {
            out.push('x');
            for v in x {
                out.push_str(&format!("{v} "));
            }
            out.push_str("0\n");
        }
        out
    }
}

fn resolve_level(model: &TrailModel, level: Level) -> Level {
    match level {
        Level::Auto => {
            if model.max_width() <= 4 {
                Level::Bit
            } else {
                Level::Word
            }
        }
        l => l,
    }
}

/// Encode `model` as CNF with XORs (no cardinality bound yet; stage 0 is
/// required to be nonzero).
pub fn encode(model: &TrailModel, level: Level) -> Result<TrailCnf, TrailError> {
    match resolve_level(model, level) {
        Level::Bit => encode_bit(model),
        _ => encode_word(model),
    }
}

fn encode_word(model: &TrailModel) -> Result<TrailCnf, TrailError> {
    let mut cnf = TrailCnf::new(Level::Word);
    for st in &model.stages {
        let vs: Vec<u32> = (0..st.count).map(|_| cnf.var()).collect();
        cnf.active.push(vs);
    }
    cnf.clauses
        .push(cnf.active[0].iter().map(|&v| v as i32).collect());
    for s in 1..model.stages.len() {
        for comp in word_components(&model.stages[s - 1], &model.stages[s])? {
            let vars: Vec<u32> = comp
                .out_words
                .iter()
                .map(|&j| cnf.active[s - 1][j])
                .chain(comp.in_words.iter().map(|&k| cnf.active[s][k]))
                .collect();
            let d = cnf.var();
            for &v in &vars {
                cnf.clauses.push(vec![-(v as i32), d as i32]);
            }
            for f in comp.maximal_forbidden() {
                let mut c = vec![-(d as i32)];
                for (i, &v) in vars.iter().enumerate() {
                    if f >> i & 1 == 0 {
                        c.push(v as i32);
                    }
                }
                cnf.clauses.push(c);
            }
        }
    }
    Ok(cnf)
}

fn encode_bit(model: &TrailModel) -> Result<TrailCnf, TrailError> {
    if model.max_width() > 6 {
        return Err(TrailError::TooLarge(
            "bit level needs S-box width <= 6".into(),
        ));
    }
    let mut cnf = TrailCnf::new(Level::Bit);
    let n = model.state_bits;
    let mut xin: Vec<u32> = (0..n).map(|_| cnf.var()).collect();
    for (s, st) in model.stages.iter().enumerate() {
        if s > 0 {
            // Inputs of this stage are the linear image of the previous outputs.
            let lin = st.lin.as_ref().unwrap();
            let yprev = std::mem::take(&mut xin);
            xin = (0..n)
                .map(|i| {
                    let terms: Vec<u32> = (0..n)
                        .filter(|&j| lin.get(i, j))
                        .map(|j| yprev[j])
                        .collect();
                    if terms.len() == 1 {
                        terms[0]
                    } else {
                        let v = cnf.var();
                        let mut row = terms;
                        row.push(v);
                        cnf.xors.push(row);
                        v
                    }
                })
                .collect();
        }
        let cubes = transition_nogoods(&st.sbox, model.direction);
        let w = st.width;
        let yout: Vec<u32> = (0..n).map(|_| cnf.var()).collect();
        let mut act = Vec::with_capacity(st.count);
        for j in 0..st.count {
            let xs: Vec<u32> = (0..w).map(|i| xin[j * w + i]).collect();
            let ys: Vec<u32> = (0..w).map(|i| yout[j * w + i]).collect();
            for &(mask, val) in &cubes {
                let mut c = Vec::new();
                for b in 0..2 * w {
                    if mask >> b & 1 == 1 {
                        let v = if b < w { xs[b] } else { ys[b - w] } as i32;
                        c.push(if val >> b & 1 == 1 { -v } else { v });
                    }
                }
                cnf.clauses.push(c);
            }
            let a = cnf.var();
            for &v in &xs {
                cnf.clauses.push(vec![-(v as i32), a as i32]);
            }
            let mut c = vec![-(a as i32)];
            c.extend(xs.iter().map(|&v| v as i32));
            cnf.clauses.push(c);
            act.push(a);
        }
        cnf.active.push(act);
        xin = yout;
    }
    cnf.clauses
        .push(cnf.active[0].iter().map(|&v| v as i32).collect());
    Ok(cnf)
}

/// Options for [`min_active_sboxes`].
#[derive(Clone, Copy, Debug)]
pub struct SatOptions {
    /// Encoding choice.
    pub level: Level,
    /// Conflict budget of each solver call.
    pub conflict_budget: u64,
}

impl Default for SatOptions {
    fn default() -> Self {
        SatOptions {
            level: Level::Auto,
            conflict_budget: 50_000_000,
        }
    }
}

/// Result of a SAT-based minimum-active-S-box search.
#[derive(Clone, Debug)]
pub struct SatResult {
    /// Minimum number of active S-boxes (SAT at this bound, UNSAT one below).
    pub min_active: u32,
    /// Per stage, the active S-boxes of the satisfying assignment found at
    /// the minimum.
    pub pattern: Vec<Vec<usize>>,
    /// Encoding used.
    pub level: Level,
    /// Number of solver calls.
    pub solver_calls: usize,
    /// Total conflicts over all calls.
    pub conflicts: u64,
    /// Variables in the base encoding.
    pub n_vars: u32,
    /// Clauses in the base encoding.
    pub n_clauses: usize,
}

/// SAT-based minimum number of active S-boxes of a trail model.
pub fn min_active_sboxes_model(
    model: &TrailModel,
    opts: &SatOptions,
) -> Result<SatResult, TrailError> {
    let base = encode(model, opts.level)?;
    let total: usize = base.active.iter().map(Vec::len).sum();
    let mut k = total;
    let mut calls = 0usize;
    let mut conflicts = 0u64;
    let mut best: Option<(u32, Vec<Vec<usize>>)> = None;
    loop {
        let mut cnf = base.clone();
        cnf.add_at_most(k);
        let mut solver = Solver::new(cnf.n_vars);
        solver.conflict_budget = opts.conflict_budget;
        let mut ok = true;
        for c in &cnf.clauses {
            ok &= solver.add_clause(c.clone());
        }
        for x in &cnf.xors {
            ok &= solver.add_xor(x, false);
        }
        calls += 1;
        let res = if ok {
            solver.solve()
        } else {
            SolveResult::Unsat
        };
        conflicts += solver.conflicts();
        match res {
            SolveResult::Sat => {
                let m = solver.model();
                let pattern: Vec<Vec<usize>> = base
                    .active
                    .iter()
                    .map(|vs| {
                        vs.iter()
                            .enumerate()
                            .filter(|(_, &v)| m[(v - 1) as usize])
                            .map(|(j, _)| j)
                            .collect()
                    })
                    .collect();
                let c: usize = pattern.iter().map(Vec::len).sum();
                best = Some((c as u32, pattern));
                if c <= 1 {
                    break;
                }
                k = c - 1;
            }
            SolveResult::Unsat => break,
            SolveResult::Unknown => return Err(TrailError::BudgetExceeded),
        }
    }
    let (min_active, pattern) = best.ok_or_else(|| {
        TrailError::Unsupported("encoding is unsatisfiable even without a bound".into())
    })?;
    Ok(SatResult {
        min_active,
        pattern,
        level: base.level,
        solver_calls: calls,
        conflicts,
        n_vars: base.n_vars,
        n_clauses: base.clauses.len(),
    })
}

/// SAT-based minimum number of active S-boxes over the first `rounds` rounds
/// of `p` (differential or linear per `direction`).
pub fn min_active_sboxes(
    p: &Primitive,
    rounds: usize,
    direction: Direction,
    opts: &SatOptions,
) -> Result<SatResult, TrailError> {
    let model = TrailModel::from_primitive(p, rounds, direction)?;
    min_active_sboxes_model(&model, opts)
}
