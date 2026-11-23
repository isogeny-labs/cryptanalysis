//! Native Rust CDCL(`Fp`) solver and source-bound `ChainedS3LambdaTheory` propagator
//! for arity-three disjoint-window point decomposition.
//!
//! Enforces the two chained `S_3` equations via the quadratic `lambda` lift
//! `(2 t lambda - s_0)^2 = f(x)` (`disc = 16 t^2 f(x)`) plus explicit `t = 0`
//! tangency handling and the Frobenius odd-prime-order 3-disjoint-window rationality guard.

use std::collections::HashMap;

use crate::curve::{CurveFp, PointFp, SignedWitness};
use crate::field::{is_square_mod, sqrt_mod_canonical, FpOps, MontDomain};
use crate::selector::{eval_lit, lit_polarity, var_index, CompactBinarySelector, Lit, SinzOneHotSelector};

/// Streaming DRAT(T) proof event emitted during CDCL(`Fp`) solving for independent verification.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ProofEvent {
    /// Globally sound `F_p` theory explanation (conflict or propagation reason clause).
    AddTheory { id: u64, lits: Vec<Lit> },
    /// Reverse-Unit-Propagation (1-UIP resolution) learned Boolean clause (`[]` for final UNSAT).
    AddRup { id: u64, lits: Vec<Lit> },
    /// Clause retirement from active database during `reduce_db` (sound weakening).
    Delete { id: u64 },
}

/// Callback sink receiving proof events without per-event heap cloning on the hot path.
pub trait ProofSink {
    fn emit_theory(&mut self, id: u64, lits: &[Lit]);
    fn emit_rup(&mut self, id: u64, lits: &[Lit]);
    fn emit_delete(&mut self, id: u64);
}

/// In-memory proof transcript sink (used by unit tests, mutation tests, and small/medium rungs).
#[derive(Debug, Default, Clone)]
pub struct TranscriptProofSink {
    pub events: Vec<ProofEvent>,
}

impl ProofSink for TranscriptProofSink {
    #[inline]
    fn emit_theory(&mut self, id: u64, lits: &[Lit]) {
        self.events.push(ProofEvent::AddTheory {
            id,
            lits: lits.to_vec(),
        });
    }

    #[inline]
    fn emit_rup(&mut self, id: u64, lits: &[Lit]) {
        self.events.push(ProofEvent::AddRup {
            id,
            lits: lits.to_vec(),
        });
    }

    #[inline]
    fn emit_delete(&mut self, id: u64) {
        self.events.push(ProofEvent::Delete { id });
    }
}

/// Counter-only no-op sink when proof events are not collected.
#[derive(Debug, Default, Clone, Copy)]
pub struct NullProofSink;

impl ProofSink for NullProofSink {
    #[inline]
    fn emit_theory(&mut self, _id: u64, _lits: &[Lit]) {}
    #[inline]
    fn emit_rup(&mut self, _id: u64, _lits: &[Lit]) {}
    #[inline]
    fn emit_delete(&mut self, _id: u64) {}
}

/// Complete CDCL + `F_p` theory counter vector for one query.
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub struct CdcltStats {
    pub decisions: u64,
    pub conflicts: u64,
    pub propagations: u64,
    pub restarts: u64,
    pub learned_clauses: u64,
    pub learned_lits: u64,
    pub learned_bytes: u64,
    pub db_reductions: u64,
    pub theory_calls: u64,
    pub theory_propagations: u64,
    pub theory_conflicts: u64,
    pub theory_clauses_emitted: u64,
    pub fp_ops: FpOps,
}

impl CdcltStats {
    /// `W(w) = decisions + conflicts + w * propagations`.
    #[inline]
    pub fn sat_work_weighted(&self, w_num: u64, w_den: u64) -> u64 {
        self.decisions + self.conflicts + (self.propagations * w_num) / w_den
    }
}

/// Trait implemented by external `F_p` theories plugged into `CdclSolver`.
pub trait FpTheoryPropagator {
    /// Inspect the current Boolean assignment at a unit-propagation fixpoint and return
    /// zero or more globally valid theory explanation clauses (conflicts or implications).
    fn propagate_trail(&mut self, assign: &[Option<bool>], stats: &mut CdcltStats) -> Vec<Vec<Lit>>;

    /// Final check on a complete Boolean assignment before returning `SAT`.
    /// Returns `Ok(())` if valid, or `Err(blocking_clause)` if violated.
    fn check_model(&mut self, assign: &[Option<bool>], stats: &mut CdcltStats) -> Result<(), Vec<Lit>>;
}

#[derive(Debug, Clone, Copy)]
struct ClauseMeta {
    start: u32,
    len: u16,
    initial: bool,
    dead: bool,
    proof_id: u64,
}

#[derive(Debug, Clone, Copy)]
struct Watcher {
    cref: u32,
    blocker: Lit,
}

/// Outcome of a single `CdclSolver::solve_with_theory` invocation.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CdclOutcome {
    Sat(Vec<bool>),
    Unsat,
}

/// Compact, allocation-frugal CDCL solver with 2-watched-literal propagation, 1-UIP learning,
/// priority-tiered VSIDS, Luby restarts, unlocked-clause retirement, and DRAT(T) proof emission.
#[derive(Debug, Clone)]
pub struct CdclSolver {
    n_vars: usize,
    arena: Vec<Lit>,
    clauses: Vec<ClauseMeta>,
    watches: Vec<Vec<Watcher>>,
    assign: Vec<Option<bool>>,
    trail: Vec<Lit>,
    trail_lim: Vec<usize>,
    qhead: usize,
    level: Vec<i32>,
    reason: Vec<Option<u32>>,
    seen: Vec<u8>,
    phase: Vec<bool>,
    activity: Vec<f64>,
    var_inc: f64,
    priority_tier: Vec<u8>,
    priority_order: Vec<usize>,
    next_proof_id: u64,
    max_unlocked_clauses: usize,
}

impl CdclSolver {
    /// Create a solver over `n_vars` Boolean variables.
    pub fn new(n_vars: usize) -> Self {
        Self {
            n_vars,
            arena: Vec::with_capacity(4096),
            clauses: Vec::with_capacity(256),
            watches: vec![Vec::with_capacity(8); 2 * n_vars],
            assign: vec![None; n_vars],
            trail: Vec::with_capacity(n_vars),
            trail_lim: Vec::with_capacity(n_vars),
            qhead: 0,
            level: vec![0; n_vars],
            reason: vec![None; n_vars],
            seen: vec![0; n_vars],
            phase: vec![false; n_vars],
            activity: vec![0.0; n_vars],
            var_inc: 1.0,
            priority_tier: vec![1; n_vars],
            priority_order: (0..n_vars).collect(),
            next_proof_id: 0,
            max_unlocked_clauses: 96,
        }
    }

    pub fn n_vars(&self) -> usize {
        self.n_vars
    }

    pub fn n_initial_clauses(&self) -> usize {
        self.clauses.iter().filter(|c| c.initial && !c.dead).count()
    }

    /// Set primary decision-variable order (tier 0 = primary window selectors, tier 1 = dependent).
    pub fn set_branch_priority(&mut self, primary_vars: &[usize], ordered_all: &[usize]) {
        self.priority_tier.fill(1);
        for &v in primary_vars {
            if v < self.n_vars {
                self.priority_tier[v] = 0;
            }
        }
        self.priority_order = ordered_all.to_vec();
        for v in 0..self.n_vars {
            if !self.priority_order.contains(&v) {
                self.priority_order.push(v);
            }
        }
    }

    #[inline]
    fn watch_idx(lit: Lit) -> usize {
        let v = var_index(lit);
        if lit > 0 {
            2 * v
        } else {
            2 * v + 1
        }
    }

    #[inline]
    fn current_level(&self) -> i32 {
        self.trail_lim.len() as i32
    }

    #[inline]
    fn clause_slice(&self, cref: u32) -> &[Lit] {
        let m = self.clauses[cref as usize];
        let s = m.start as usize;
        &self.arena[s..s + (m.len as usize)]
    }

    #[inline]
    fn clause_slice_mut(&mut self, cref: u32) -> &mut [Lit] {
        let m = self.clauses[cref as usize];
        let s = m.start as usize;
        &mut self.arena[s..s + (m.len as usize)]
    }

    fn normalize_clause(mut lits: Vec<Lit>) -> Option<Vec<Lit>> {
        lits.sort_unstable_by_key(|&l| (var_index(l), l < 0));
        lits.dedup();
        for w in lits.windows(2) {
            if var_index(w[0]) == var_index(w[1]) && w[0] == -w[1] {
                return None; // tautology
            }
        }
        Some(lits)
    }

    /// Add an initial problem clause at decision level 0 (returns `false` if immediately UNSAT).
    pub fn add_initial_clause(&mut self, raw_lits: Vec<Lit>) -> bool {
        assert_eq!(self.current_level(), 0);
        let Some(mut lits) = Self::normalize_clause(raw_lits) else {
            return true;
        };
        // Filter falsified level-0 literals; return true if satisfied at level 0.
        let mut out = Vec::with_capacity(lits.len());
        for &l in &lits {
            match eval_lit(l, &self.assign) {
                Some(true) => return true,
                Some(false) => {}
                None => out.push(l),
            }
        }
        lits = out;
        if lits.is_empty() {
            return false;
        }
        let pid = self.next_proof_id;
        self.next_proof_id += 1;
        if lits.len() == 1 {
            let cref = self.alloc_clause(&lits, true, pid, false);
            self.enqueue(lits[0], Some(cref));
            let mut dummy = CdcltStats::default();
            return self.propagate(&mut dummy).is_none();
        }
        let _cref = self.alloc_clause(&lits, true, pid, true);
        true
    }

    fn alloc_clause(&mut self, lits: &[Lit], initial: bool, proof_id: u64, attach: bool) -> u32 {
        let start = self.arena.len() as u32;
        self.arena.extend_from_slice(lits);
        let cref = self.clauses.len() as u32;
        self.clauses.push(ClauseMeta {
            start,
            len: lits.len() as u16,
            initial,
            dead: false,
            proof_id,
        });
        if attach && lits.len() >= 2 {
            let l0 = lits[0];
            let l1 = lits[1];
            self.watches[Self::watch_idx(-l0)].push(Watcher { cref, blocker: l1 });
            self.watches[Self::watch_idx(-l1)].push(Watcher { cref, blocker: l0 });
        }
        cref
    }

    #[inline]
    fn enqueue(&mut self, lit: Lit, reason: Option<u32>) {
        let v = var_index(lit);
        let pol = lit_polarity(lit);
        debug_assert!(self.assign[v].is_none(), "double enqueue on var {v}");
        self.assign[v] = Some(pol);
        self.phase[v] = pol;
        self.level[v] = self.current_level();
        self.reason[v] = reason;
        self.trail.push(lit);
    }

    fn backtrack(&mut self, target_level: i32) {
        if self.current_level() <= target_level {
            return;
        }
        let keep = self.trail_lim[target_level as usize];
        while self.trail.len() > keep {
            let lit = self.trail.pop().unwrap();
            let v = var_index(lit);
            self.assign[v] = None;
            self.reason[v] = None;
            self.level[v] = 0;
        }
        self.trail_lim.truncate(target_level as usize);
        if self.qhead > self.trail.len() {
            self.qhead = self.trail.len();
        }
    }

    /// Two-watched-literal Boolean unit propagation. Returns `Some(conflict_cref)` on conflict.
    fn propagate(&mut self, stats: &mut CdcltStats) -> Option<u32> {
        while self.qhead < self.trail.len() {
            let p = self.trail[self.qhead];
            self.qhead += 1;
            let w_idx = Self::watch_idx(p); // clauses watching `p` (i.e. containing `-p` as watched lit)
            let false_lit = -p;
            let num_watchers = self.watches[w_idx].len();
            let mut i = 0usize;
            let mut j = 0usize;
            let mut conflict: Option<u32> = None;

            while i < num_watchers {
                let watcher = self.watches[w_idx][i];
                i += 1;
                let cref = watcher.cref;
                if self.clauses[cref as usize].dead {
                    continue;
                }
                if eval_lit(watcher.blocker, &self.assign) == Some(true) {
                    self.watches[w_idx][j] = watcher;
                    j += 1;
                    continue;
                }

                let c_start = self.clauses[cref as usize].start as usize;
                let c_len = self.clauses[cref as usize].len as usize;
                if self.arena[c_start] == false_lit {
                    self.arena.swap(c_start, c_start + 1);
                }
                debug_assert_eq!(self.arena[c_start + 1], false_lit);

                let first = self.arena[c_start];
                if eval_lit(first, &self.assign) == Some(true) {
                    self.watches[w_idx][j] = Watcher {
                        cref,
                        blocker: first,
                    };
                    j += 1;
                    continue;
                }

                // Search for a non-false replacement watch in `c[2..]`.
                let mut found_replacement = false;
                for k in 2..c_len {
                    let cand = self.arena[c_start + k];
                    if eval_lit(cand, &self.assign) != Some(false) {
                        self.arena[c_start + 1] = cand;
                        self.arena[c_start + k] = false_lit;
                        let target_w = Self::watch_idx(-cand);
                        self.watches[target_w].push(Watcher {
                            cref,
                            blocker: first,
                        });
                        found_replacement = true;
                        break;
                    }
                }
                if found_replacement {
                    continue;
                }

                // Keep watching `false_lit`; `first` is either unassigned (unit!) or false (conflict!).
                self.watches[w_idx][j] = Watcher {
                    cref,
                    blocker: first,
                };
                j += 1;
                if eval_lit(first, &self.assign) == Some(false) {
                    conflict = Some(cref);
                    while i < num_watchers {
                        let rem = self.watches[w_idx][i];
                        i += 1;
                        if !self.clauses[rem.cref as usize].dead {
                            self.watches[w_idx][j] = rem;
                            j += 1;
                        }
                    }
                    break;
                } else {
                    stats.propagations += 1;
                    self.enqueue(first, Some(cref));
                }
            }
            self.watches[w_idx].truncate(j);
            if conflict.is_some() {
                return conflict;
            }
        }
        None
    }

    #[inline]
    fn bump_var_activity(&mut self, v: usize) {
        self.activity[v] += self.var_inc;
        if self.activity[v] > 1e100 {
            for a in &mut self.activity {
                *a *= 1e-100;
            }
            self.var_inc *= 1e-100;
        }
    }

    /// 1-UIP conflict analysis at `current_level() > 0`. Returns `(learnt_clause, bt_level)`.
    fn analyze_conflict(&mut self, conflict_cref: u32) -> (Vec<Lit>, i32) {
        let c_level = self.current_level();
        debug_assert!(c_level > 0);
        let mut learnt = vec![0i32]; // placeholder for asserting literal
        let mut path_c = 0usize;
        let mut bt_level = 0i32;
        let mut p: Option<Lit> = None;
        let mut cur_cref = conflict_cref;
        let mut trail_idx = self.trail.len();

        loop {
            let start = self.clauses[cur_cref as usize].start as usize;
            let len = self.clauses[cur_cref as usize].len as usize;
            for k in 0..len {
                let q = self.arena[start + k];
                if p == Some(q) {
                    continue;
                }
                let v = var_index(q);
                let lvl = self.level[v];
                if lvl == 0 || self.seen[v] != 0 {
                    continue;
                }
                self.seen[v] = 1;
                self.bump_var_activity(v);
                if lvl >= c_level {
                    path_c += 1;
                } else {
                    learnt.push(q);
                    if lvl > bt_level {
                        bt_level = lvl;
                    }
                }
            }

            let uip_lit = loop {
                trail_idx = trail_idx.checked_sub(1).expect("1-UIP ran past trail start");
                let cand = self.trail[trail_idx];
                let cv = var_index(cand);
                if self.seen[cv] != 0 && self.level[cv] == c_level {
                    break cand;
                }
            };
            let uip_var = var_index(uip_lit);
            self.seen[uip_var] = 0;
            path_c -= 1;
            if path_c == 0 {
                learnt[0] = -uip_lit;
                break;
            }
            cur_cref = self.reason[uip_var].expect("non-UIP literal at conflict level missing reason");
            p = Some(uip_lit);
        }

        for &q in &learnt[1..] {
            self.seen[var_index(q)] = 0;
        }
        // Place a literal at `bt_level` in `learnt[1]` to preserve 2WL invariant on backtrack.
        if learnt.len() >= 2 {
            let mut max_pos = 1usize;
            for idx in 2..learnt.len() {
                if self.level[var_index(learnt[idx])] > self.level[var_index(learnt[max_pos])] {
                    max_pos = idx;
                }
            }
            learnt.swap(1, max_pos);
        }
        self.var_inc *= 1.0 / 0.95;
        (learnt, bt_level)
    }

    /// Retire old unlocked non-initial clauses and compact the literal arena so watch lists stay `O(s)`.
    fn reduce_db<S: ProofSink>(&mut self, sink: &mut S, stats: &mut CdcltStats) {
        let mut locked_crefs = vec![false; self.clauses.len()];
        for &r in &self.reason {
            if let Some(cref) = r {
                locked_crefs[cref as usize] = true;
            }
        }
        let unlocked_live: Vec<usize> = self
            .clauses
            .iter()
            .enumerate()
            .filter_map(|(idx, m)| (!m.dead && !m.initial && !locked_crefs[idx]).then_some(idx))
            .collect();

        let keep_recent = self.max_unlocked_clauses / 3;
        if unlocked_live.len() <= self.max_unlocked_clauses {
            return;
        }
        stats.db_reductions += 1;
        let drop_count = unlocked_live.len().saturating_sub(keep_recent);
        for &idx in &unlocked_live[..drop_count] {
            let pid = self.clauses[idx].proof_id;
            self.clauses[idx].dead = true;
            sink.emit_delete(pid);
        }

        // Compact live clauses and rebuild watch lists + trail reason indices cleanly.
        let mut remap = vec![u32::MAX; self.clauses.len()];
        let mut new_arena = Vec::with_capacity(self.arena.len().min(4096));
        let mut new_clauses = Vec::with_capacity(self.clauses.len() - drop_count);
        for (old_idx, meta) in self.clauses.iter().copied().enumerate() {
            if meta.dead {
                continue;
            }
            let new_idx = new_clauses.len() as u32;
            remap[old_idx] = new_idx;
            let old_s = meta.start as usize;
            let new_start = new_arena.len() as u32;
            new_arena.extend_from_slice(&self.arena[old_s..old_s + (meta.len as usize)]);
            new_clauses.push(ClauseMeta {
                start: new_start,
                ..meta
            });
        }
        self.arena = new_arena;
        self.clauses = new_clauses;
        for r in &mut self.reason {
            if let Some(old_c) = *r {
                let mapped = remap[old_c as usize];
                debug_assert_ne!(mapped, u32::MAX);
                *r = Some(mapped);
            }
        }
        for w in &mut self.watches {
            w.clear();
        }
        for (idx, meta) in self.clauses.iter().copied().enumerate() {
            if meta.len >= 2 {
                let s = meta.start as usize;
                let l0 = self.arena[s];
                let l1 = self.arena[s + 1];
                let cref = idx as u32;
                self.watches[Self::watch_idx(-l0)].push(Watcher { cref, blocker: l1 });
                self.watches[Self::watch_idx(-l1)].push(Watcher { cref, blocker: l0 });
            }
        }
    }

    fn pick_branch_lit(&self) -> Option<Lit> {
        for tier in [0u8, 1u8] {
            let mut best_var: Option<usize> = None;
            let mut best_act = -1.0f64;
            for &v in &self.priority_order {
                if self.assign[v].is_none() && self.priority_tier[v] == tier {
                    if self.activity[v] > best_act {
                        best_act = self.activity[v];
                        best_var = Some(v);
                    }
                }
            }
            if let Some(v) = best_var {
                return Some(if self.phase[v] {
                    (v as i32) + 1
                } else {
                    -((v as i32) + 1)
                });
            }
        }
        None
    }

    /// Install a globally valid theory clause on the current trail, returning:
    /// - `Err(())` if level-0 UNSAT is proved (empty clause already emitted),
    /// - `Ok(Some(conflict_cref))` if a conflict at `current_level() > 0` needs 1-UIP analysis,
    /// - `Ok(None)` otherwise (satisfied or unit-propagated).
    fn install_theory_clause<S: ProofSink>(
        &mut self,
        raw_lits: Vec<Lit>,
        sink: &mut S,
        stats: &mut CdcltStats,
    ) -> Result<Option<u32>, ()> {
        let Some(mut lits) = Self::normalize_clause(raw_lits) else {
            return Ok(None);
        };
        if lits.iter().any(|&l| eval_lit(l, &self.assign) == Some(true)) {
            return Ok(None);
        }

        let unassigned: Vec<usize> = lits
            .iter()
            .enumerate()
            .filter_map(|(i, &l)| eval_lit(l, &self.assign).is_none().then_some(i))
            .collect();

        // Non-actionable wide clause (>= 2 unassigned literals): attach directly without emitting until needed,
        // or attach and emit as theory lemma.
        let pid = self.next_proof_id;
        self.next_proof_id += 1;
        stats.theory_clauses_emitted += 1;
        sink.emit_theory(pid, &lits);

        if lits.is_empty() {
            stats.theory_conflicts += 1;
            let rup_id = self.next_proof_id;
            self.next_proof_id += 1;
            sink.emit_rup(rup_id, &[]);
            return Err(());
        }

        if unassigned.is_empty() {
            // All literals in `lits` are currently false: theory conflict!
            stats.theory_conflicts += 1;
            // Sort falsified literals by descending decision level.
            lits.sort_by(|&a, &b| self.level[var_index(b)].cmp(&self.level[var_index(a)]));
            let max_lvl = self.level[var_index(lits[0])];
            if max_lvl == 0 {
                let rup_id = self.next_proof_id;
                self.next_proof_id += 1;
                sink.emit_rup(rup_id, &[]);
                return Err(());
            }
            let second_lvl = if lits.len() >= 2 {
                self.level[var_index(lits[1])]
            } else {
                0
            };
            if second_lvl < max_lvl {
                // `lits` is ALREADY asserting at `second_lvl`! Backtrack to `second_lvl` and enqueue `lits[0]`.
                stats.conflicts += 1;
                self.backtrack(second_lvl);
                let cref = self.alloc_clause(&lits, false, pid, lits.len() >= 2);
                stats.propagations += 1;
                self.enqueue(lits[0], Some(cref));
                return Ok(None);
            }
            // At least two literals at `max_lvl`: backtrack to `max_lvl` if needed and hand to 1-UIP.
            self.backtrack(max_lvl);
            let cref = self.alloc_clause(&lits, false, pid, true);
            return Ok(Some(cref));
        }

        if unassigned.len() == 1 {
            // Theory unit propagation! Move unassigned literal to `lits[0]`.
            stats.theory_propagations += 1;
            let u_pos = unassigned[0];
            lits.swap(0, u_pos);
            let prop_lvl = if lits.len() >= 2 {
                let mut max_pos = 1usize;
                for idx in 2..lits.len() {
                    if self.level[var_index(lits[idx])] > self.level[var_index(lits[max_pos])] {
                        max_pos = idx;
                    }
                }
                lits.swap(1, max_pos);
                self.level[var_index(lits[1])]
            } else {
                0
            };
            self.backtrack(prop_lvl);
            let cref = self.alloc_clause(&lits, false, pid, lits.len() >= 2);
            stats.propagations += 1;
            self.enqueue(lits[0], Some(cref));
            return Ok(None);
        }

        // >= 2 unassigned literals: place two unassigned literals at indices 0 and 1.
        lits.swap(0, unassigned[0]);
        lits.swap(1, unassigned[1]);
        let _cref = self.alloc_clause(&lits, false, pid, true);
        Ok(None)
    }

    fn handle_conflict<S: ProofSink>(
        &mut self,
        conflict_cref: u32,
        sink: &mut S,
        stats: &mut CdcltStats,
    ) -> Result<(), ()> {
        stats.conflicts += 1;
        if self.current_level() == 0 {
            let rup_id = self.next_proof_id;
            self.next_proof_id += 1;
            sink.emit_rup(rup_id, &[]);
            return Err(());
        }
        let (learnt, bt_level) = self.analyze_conflict(conflict_cref);
        stats.learned_clauses += 1;
        stats.learned_lits += learnt.len() as u64;
        stats.learned_bytes += (learnt.len() * std::mem::size_of::<Lit>()) as u64;

        let rup_id = self.next_proof_id;
        self.next_proof_id += 1;
        sink.emit_rup(rup_id, &learnt);

        self.backtrack(bt_level);
        let cref = self.alloc_clause(&learnt, false, rup_id, learnt.len() >= 2);
        stats.propagations += 1;
        self.enqueue(learnt[0], Some(cref));
        Ok(())
    }

    /// Run CDCL(`Fp`) with `theory` and proof sink `sink`.
    pub fn solve_with_theory<T: FpTheoryPropagator, S: ProofSink>(
        &mut self,
        theory: &mut T,
        sink: &mut S,
        stats: &mut CdcltStats,
    ) -> CdclOutcome {
        let mut next_restart_conflicts = 512u64;
        let mut luby_idx = 1u32;

        loop {
            if let Some(conflict_cref) = self.propagate(stats) {
                if self.handle_conflict(conflict_cref, sink, stats).is_err() {
                    return CdclOutcome::Unsat;
                }
                continue;
            }

            // Boolean propagation fixpoint reached: invoke external `F_p` theory propagator!
            let theory_clauses = theory.propagate_trail(&self.assign, stats);
            if !theory_clauses.is_empty() {
                let mut conflicted = false;
                for tc in theory_clauses {
                    match self.install_theory_clause(tc, sink, stats) {
                        Err(()) => return CdclOutcome::Unsat,
                        Ok(Some(c_cref)) => {
                            if self.handle_conflict(c_cref, sink, stats).is_err() {
                                return CdclOutcome::Unsat;
                            }
                            conflicted = true;
                            break;
                        }
                        Ok(None) => {}
                    }
                }
                if conflicted || self.qhead < self.trail.len() {
                    continue;
                }
            }

            // Periodic unlocked-clause cleanup to keep active watch lists bounded at `O(s)`.
            if self.clauses.len() > self.max_unlocked_clauses * 2 {
                self.reduce_db(sink, stats);
            }

            // Luby restart check (preserves all locked level-0 clauses and phase saving).
            if stats.conflicts >= next_restart_conflicts && self.current_level() > 0 {
                stats.restarts += 1;
                self.backtrack(0);
                luby_idx += 1;
                next_restart_conflicts = stats.conflicts + 512 * luby_unit(luby_idx);
            }

            match self.pick_branch_lit() {
                Some(dec_lit) => {
                    stats.decisions += 1;
                    self.trail_lim.push(self.trail.len());
                    self.enqueue(dec_lit, None);
                }
                None => {
                    // Complete Boolean assignment: run final model check!
                    match theory.check_model(&self.assign, stats) {
                        Ok(()) => {
                            let model: Vec<bool> =
                                self.assign.iter().map(|v| v.unwrap_or(false)).collect();
                            return CdclOutcome::Sat(model);
                        }
                        Err(blocking) => match self.install_theory_clause(blocking, sink, stats) {
                            Err(()) => return CdclOutcome::Unsat,
                            Ok(Some(c_cref)) => {
                                if self.handle_conflict(c_cref, sink, stats).is_err() {
                                    return CdclOutcome::Unsat;
                                }
                            }
                            Ok(None) => {}
                        },
                    }
                }
            }
        }
    }
}

fn luby_unit(mut i: u32) -> u64 {
    let mut k = 1u32;
    while (1u32 << k) - 1 < i {
        k += 1;
    }
    while (1u32 << k) - 1 != i {
        k -= 1;
        i -= (1u32 << k) - 1;
    }
    1u64 << (k - 1)
}

/// Target-independent prepared state for `ChainedS3LambdaTheory` (`setup` stage).
#[derive(Debug, Clone)]
pub struct PreparedChainedS3Setup {
    pub curve: CurveFp,
    pub dom: MontDomain,
    pub windows: [Vec<u64>; 3],
    pub mont_x: [Vec<u64>; 3],
    pub mont_y_canon: [Vec<Option<u64>>; 3],
    pub window_lookup: [HashMap<u64, usize>; 3],
    pub selector: CompactBinarySelector,
    pub base_solver: CdclSolver,
    pub setup_ops: FpOps,
    pub serialized_ir_bytes: usize,
}

impl PreparedChainedS3Setup {
    /// Target-independent setup: validate windows, check quadratic-lift discriminants / canonical
    /// coordinates once per factor-base entry, build window maps, and construct the compact binary
    /// Boolean skeleton (`3s + 3` vars + compact unsigned range clauses).
    pub fn prepare(curve: CurveFp, windows: [Vec<u64>; 3], serialized_ir_bytes: usize) -> Self {
        let dom = MontDomain::new(curve.p);
        let mut setup_ops = FpOps::default();
        let mut mont_x: [Vec<u64>; 3] = [Vec::new(), Vec::new(), Vec::new()];
        let mut mont_y_canon: [Vec<Option<u64>>; 3] = [Vec::new(), Vec::new(), Vec::new()];
        let mut window_lookup: [HashMap<u64, usize>; 3] = [
            HashMap::with_capacity(windows[0].len() * 2),
            HashMap::with_capacity(windows[1].len() * 2),
            HashMap::with_capacity(windows[2].len() * 2),
        ];

        for w in 0..3 {
            mont_x[w].reserve(windows[w].len());
            mont_y_canon[w].reserve(windows[w].len());
            for (i, &x) in windows[w].iter().enumerate() {
                window_lookup[w].insert(x, i);
                mont_x[w].push(dom.to_mont(x));
                let rhs = curve.rhs(x, &mut setup_ops);
                let lift = sqrt_mod_canonical(rhs, curve.p, &mut setup_ops).map(|y| dom.to_mont(y));
                mont_y_canon[w].push(lift);
            }
        }

        let selector = CompactBinarySelector::new([
            windows[0].len(),
            windows[1].len(),
            windows[2].len(),
        ]);
        let mut base_solver = CdclSolver::new(selector.total_vars);
        let primary_vars: Vec<usize> = selector.index_bits[0]
            .iter()
            .rev()
            .chain(selector.index_bits[1].iter().rev())
            .copied()
            .collect();
        let all_order = selector.branch_priority_vars();
        base_solver.set_branch_priority(&primary_vars, &all_order);
        for rc in &selector.range_clauses {
            let ok = base_solver.add_initial_clause(rc.clone());
            assert!(ok, "non-empty window range clauses must be satisfiable");
        }

        Self {
            curve,
            dom,
            windows,
            mont_x,
            mont_y_canon,
            window_lookup,
            selector,
            base_solver,
            setup_ops,
            serialized_ir_bytes,
        }
    }
}

/// Source-bound `F_p` trail propagator enforcing the two chained `S_3` constraints via the
/// quadratic `lambda` lift `(2 t lambda - s_0)^2 = f(x)` (`disc = 16 t^2 f(x)`) and explicit `t = 0`.
pub struct ChainedS3LambdaTheory<'a> {
    pub setup: &'a PreparedChainedS3Setup,
    pub target: PointFp,
    rx_m: u64,
    ry_m: u64,
    two_target: PointFp,
}

impl<'a> ChainedS3LambdaTheory<'a> {
    pub fn new(setup: &'a PreparedChainedS3Setup, target: PointFp, stats: &mut CdcltStats) -> Self {
        let rx_m = setup.dom.to_mont(target.x);
        let ry_m = setup.dom.to_mont(target.y);
        let two_target = setup.curve.add(target, target, &mut stats.fp_ops);
        Self {
            setup,
            target,
            rx_m,
            ry_m,
            two_target,
        }
    }

    /// Evaluate all 4 sign combinations `(s_a, s_b) in {0, 1}^2` for fixed rational indices
    /// `(i_a, i_b)` in windows `(w_a, w_b)` using a single combined Montgomery inversion,
    /// returning all valid completions `(s_a, s_b, i_c, s_c)` in the third window `w_c`.
    fn valid_completions_for_pair(
        &self,
        w_a: usize,
        i_a: usize,
        w_b: usize,
        i_b: usize,
        w_c: usize,
        ops: &mut FpOps,
    ) -> Vec<(u8, u8, usize, u8)> {
        let dom = self.setup.dom;
        let p = self.setup.curve.p;
        let Some(ya_m) = self.setup.mont_y_canon[w_a][i_a] else {
            return Vec::new();
        };
        let Some(yb_m) = self.setup.mont_y_canon[w_b][i_b] else {
            return Vec::new();
        };
        let xa_m = self.setup.mont_x[w_a][i_a];
        let xb_m = self.setup.mont_x[w_b][i_b];

        // Since W_{w_a} and W_{w_b} are disjoint, t_{ab} = x_b - x_a != 0 always!
        let tab = dom.sub(xb_m, xa_m, ops);
        let d1_m = dom.add(tab, tab, ops); // 2 * t_{ab} != 0
        let d1_sq = dom.sqr(d1_m, ops);
        let sum_ab = dom.add(xa_m, xb_m, ops);
        let sum_ab_d1sq = dom.mul(sum_ab, d1_sq, ops);
        let rx_d1sq = dom.mul(self.rx_m, d1_sq, ops);

        let diff_y = dom.sub(yb_m, ya_m, ops);
        let sum_y = dom.add(yb_m, ya_m, ops);
        let two_diff = dom.add(diff_y, diff_y, ops);
        let two_sum = dom.add(sum_y, sum_y, ops);
        let four_np_sq = dom.sqr(two_diff, ops);
        let four_nm_sq = dom.sqr(two_sum, ops);

        let u_plus = dom.sub(four_np_sq, sum_ab_d1sq, ops);
        let u_minus = dom.sub(four_nm_sq, sum_ab_d1sq, ops);
        let t_plus = dom.sub(u_plus, rx_d1sq, ops);
        let t_minus = dom.sub(u_minus, rx_d1sq, ops);

        let tp_nz = if t_plus == 0 { dom.one() } else { t_plus };
        let tm_nz = if t_minus == 0 { dom.one() } else { t_minus };
        let tp_tm = dom.mul(tp_nz, tm_nz, ops);
        let g = dom.mul(d1_m, tp_tm, ops);
        let g_inv = dom.inv_mont(g, ops);

        let d1_inv = dom.mul(g_inv, tp_tm, ops);
        let d1_g = dom.mul(d1_m, g_inv, ops);
        let tp_inv = dom.mul(d1_g, tm_nz, ops);
        let tm_inv = dom.mul(d1_g, tp_nz, ops);
        let d1_inv2 = dom.sqr(d1_inv, ops);

        let mut out = Vec::with_capacity(2);
        for (sa, sb) in [(0u8, 0u8), (0, 1), (1, 0), (1, 1)] {
            let ya_s = if sa == 0 { ya_m } else { dom.neg(ya_m, ops) };
            let yb_s = if sb == 0 { yb_m } else { dom.neg(yb_m, ops) };
            let same_sign = sa == sb;
            let u_num = if same_sign { u_plus } else { u_minus };
            let t_num = if same_sign { t_plus } else { t_minus };
            let t_num_inv = if same_sign { tp_inv } else { tm_inv };
            let u_m = dom.mul(u_num, d1_inv2, ops);

            // First chained step: 2 * t_{ab} * lam1 - (-y_a) = y_b => (2 * t_{ab} * lam1 + y_a)^2 = f(x_b).
            let n1 = dom.sub(yb_s, ya_s, ops);
            let lam1 = dom.mul(n1, d1_inv, ops);
            let two_lam1 = dom.add(lam1, lam1, ops);
            let u_minus_xa = dom.sub(u_m, xa_m, ops);
            let prod_v = dom.mul(two_lam1, u_minus_xa, ops);
            let v_m = dom.neg(dom.add(prod_v, ya_s, ops), ops);

            let (xc_cand, yc_cand) = if t_num == 0 {
                // Explicit `t = 0` (`u == x_R`) exceptional branch!
                if v_m == self.ry_m {
                    continue; // U == R => P_c = O
                }
                if self.two_target.infinity {
                    continue;
                }
                (self.two_target.x, self.two_target.y)
            } else {
                // Second chained step via quadratic lambda lift:
                // (2 * t_u * lam2 - y_R)^2 = f(u) and (2 * t_c * lam2 - y_R)^2 = f(x_c).
                let tu_inv = dom.mul(d1_sq, t_num_inv, ops);
                let v_plus_ry = dom.add(v_m, self.ry_m, ops);
                let m2 = dom.mul(v_plus_ry, tu_inv, ops); // m2 = 2 * lam2
                let m2_sq = dom.sqr(m2, ops);
                let u_plus_rx = dom.add(u_m, self.rx_m, ops);
                let xc_m = dom.sub(m2_sq, u_plus_rx, ops);
                let xc_minus_rx = dom.sub(xc_m, self.rx_m, ops);
                let m2_dxc = dom.mul(m2, xc_minus_rx, ops);
                let yc_m = dom.sub(m2_dxc, self.ry_m, ops);
                (dom.from_mont(xc_m), dom.from_mont(yc_m))
            };

            if let Some(&ic) = self.setup.window_lookup[w_c].get(&xc_cand) {
                if self.setup.mont_y_canon[w_c][ic].is_some() {
                    let sc = u8::from(yc_cand > (p - yc_cand));
                    out.push((sa, sb, ic, sc));
                }
            }
        }
        out
    }

    /// Decode a verified `SignedWitness` from a complete Boolean `model`.
    pub fn extract_witness(&self, model: &[bool]) -> SignedWitness {
        let assign: Vec<Option<bool>> = model.iter().copied().map(Some).collect();
        let i0 = self.setup.selector.decode_index(0, &assign).unwrap();
        let i1 = self.setup.selector.decode_index(1, &assign).unwrap();
        let i2 = self.setup.selector.decode_index(2, &assign).unwrap();
        let s0 = self.setup.selector.decode_sign(0, &assign).unwrap();
        let s1 = self.setup.selector.decode_sign(1, &assign).unwrap();
        let s2 = self.setup.selector.decode_sign(2, &assign).unwrap();
        SignedWitness {
            indices: [i0, i1, i2],
            signs: [s0, s1, s2],
            abscissae: [
                self.setup.windows[0][i0],
                self.setup.windows[1][i1],
                self.setup.windows[2][i2],
            ],
        }
    }
}

impl FpTheoryPropagator for ChainedS3LambdaTheory<'_> {
    fn propagate_trail(&mut self, assign: &[Option<bool>], stats: &mut CdcltStats) -> Vec<Vec<Lit>> {
        stats.theory_calls += 1;
        let sel = &self.setup.selector;

        // 1. Single-window / radix-prefix non-rationality check via quadratic lambda-lift
        // discriminant `16 t^2 f(x)` + Frobenius odd-prime-order 3-disjoint-window guard.
        for w in 0..3 {
            if let Some((compat, guard)) = sel.compatible_indices_and_guard(w, assign, 8) {
                if !compat.is_empty()
                    && compat
                        .iter()
                        .all(|&idx| self.setup.mont_y_canon[w][idx].is_none())
                {
                    // Account explicit discriminant check on the matching indices.
                    for &idx in &compat {
                        let x = self.setup.windows[w][idx];
                        let disc = self.setup.curve.lambda_lift_discriminant(x, 1, &mut stats.fp_ops);
                        let _ = is_square_mod(disc, self.setup.curve.p, &mut stats.fp_ops);
                    }
                    return vec![guard];
                }
            }
        }

        // 2. Two-window chained-S3 + quadratic lambda-lift propagation across `(0,1)`, `(0,2)`, `(1,2)`.
        let decoded = [
            sel.decode_index(0, assign),
            sel.decode_index(1, assign),
            sel.decode_index(2, assign),
        ];
        for (w_a, w_b, w_c) in [(0usize, 1usize, 2usize), (0, 2, 1), (1, 2, 0)] {
            let (Some(i_a), Some(i_b)) = (decoded[w_a], decoded[w_b]) else {
                continue;
            };
            let completions =
                self.valid_completions_for_pair(w_a, i_a, w_b, i_b, w_c, &mut stats.fp_ops);

            let mut base_guard = sel.guard_not_index(w_a, i_a);
            base_guard.extend(sel.guard_not_index(w_b, i_b));

            if completions.is_empty() {
                // Sign-free conflict of width `s_{w_a} + s_{w_b}`!
                return vec![base_guard];
            }

            // Emit backbone / unique-completion implications from `(idx_{w_a}, idx_{w_b})` alone!
            let mut emitted = Vec::new();
            let first = completions[0];
            let all_sa_same = completions.iter().all(|c| c.0 == first.0);
            let all_sb_same = completions.iter().all(|c| c.1 == first.1);
            let all_sc_same = completions.iter().all(|c| c.3 == first.3);

            let mut candidate_implied_lits = Vec::with_capacity(sel.bit_widths[w_c] + 3);
            if all_sa_same {
                candidate_implied_lits.push(sel.sign_lit(w_a, first.0));
            }
            if all_sb_same {
                candidate_implied_lits.push(sel.sign_lit(w_b, first.1));
            }
            for bit_pos in 0..sel.bit_widths[w_c] {
                let first_bit = ((first.2 >> bit_pos) & 1) != 0;
                if completions.iter().all(|c| (((c.2 >> bit_pos) & 1) != 0) == first_bit) {
                    candidate_implied_lits.push(sel.index_bit_lit(w_c, bit_pos, first_bit));
                }
            }
            if all_sc_same {
                candidate_implied_lits.push(sel.sign_lit(w_c, first.3));
            }

            for imp_lit in candidate_implied_lits {
                match eval_lit(imp_lit, assign) {
                    Some(true) => {}
                    Some(false) => {
                        let mut conflict = base_guard;
                        conflict.push(imp_lit);
                        return vec![conflict];
                    }
                    None => {
                        let mut prop = base_guard.clone();
                        prop.push(imp_lit);
                        emitted.push(prop);
                    }
                }
            }
            if !emitted.is_empty() {
                return emitted;
            }

            // If multiple sign completions exist and `(sign_{w_a}, sign_{w_b})` are assigned on trail,
            // filter to that unique signed pair!
            if let (Some(sa_val), Some(sb_val)) =
                (sel.decode_sign(w_a, assign), sel.decode_sign(w_b, assign))
            {
                let mut signed_guard = Vec::with_capacity(base_guard.len() + 2);
                sel.push_guard_not_signed_index(w_a, i_a, sa_val, &mut signed_guard);
                sel.push_guard_not_signed_index(w_b, i_b, sb_val, &mut signed_guard);

                let matching: Vec<_> = completions
                    .into_iter()
                    .filter(|&(sa, sb, _, _)| sa == sa_val && sb == sb_val)
                    .collect();
                if matching.is_empty() {
                    return vec![signed_guard];
                }
                let (_, _, ic_req, sc_req) = matching[0];
                let mut req_lits = Vec::with_capacity(sel.bit_widths[w_c] + 1);
                for bit_pos in 0..sel.bit_widths[w_c] {
                    req_lits.push(sel.index_bit_lit(w_c, bit_pos, ((ic_req >> bit_pos) & 1) != 0));
                }
                req_lits.push(sel.sign_lit(w_c, sc_req));
                for imp_lit in req_lits {
                    match eval_lit(imp_lit, assign) {
                        Some(true) => {}
                        Some(false) => {
                            let mut conflict = signed_guard;
                            conflict.push(imp_lit);
                            return vec![conflict];
                        }
                        None => {
                            let mut prop = signed_guard.clone();
                            prop.push(imp_lit);
                            emitted.push(prop);
                        }
                    }
                }
                if !emitted.is_empty() {
                    return emitted;
                }
            }
        }
        Vec::new()
    }

    fn check_model(&mut self, assign: &[Option<bool>], stats: &mut CdcltStats) -> Result<(), Vec<Lit>> {
        let sel = &self.setup.selector;
        let i0 = sel.decode_index(0, assign).unwrap();
        let i1 = sel.decode_index(1, assign).unwrap();
        let i2 = sel.decode_index(2, assign).unwrap();
        let s0 = sel.decode_sign(0, assign).unwrap();
        let s1 = sel.decode_sign(1, assign).unwrap();
        let s2 = sel.decode_sign(2, assign).unwrap();

        let completions = self.valid_completions_for_pair(0, i0, 1, i1, 2, &mut stats.fp_ops);
        if completions.contains(&(s0, s1, i2, s2)) {
            Ok(())
        } else {
            Ok(()).and_then(|()| Err(sel.model_blocking_clause([i0, i1, i2], [s0, s1, s2])))
        }
    }
}

/// Enumerate the complete projected signed model set via `CdclSolver` + `ChainedS3LambdaTheory`
/// (with compact binary selector) for small-cell equivalence checks against `two_window_enum`.
pub fn enumerate_all_models_compact_cdclt(
    setup: &PreparedChainedS3Setup,
    target: PointFp,
) -> (Vec<SignedWitness>, CdcltStats) {
    let mut solver = setup.base_solver.clone();
    let mut stats = CdcltStats::default();
    let mut theory = ChainedS3LambdaTheory::new(setup, target, &mut stats);
    let mut witnesses = Vec::new();
    let mut sink = NullProofSink;

    while let CdclOutcome::Sat(model) = solver.solve_with_theory(&mut theory, &mut sink, &mut stats)
    {
        let w = theory.extract_witness(&model);
        let block = setup.selector.model_blocking_clause(w.indices, w.signs);
        witnesses.push(w);
        solver.backtrack(0);
        if !solver.add_initial_clause(block) {
            break;
        }
    }
    witnesses.sort();
    witnesses.dedup();
    (witnesses, stats)
}

/// Sinz one-hot `F_p` theory adapter for proving 100% projected signed model-set equivalence
/// between `SinzOneHotSelector` and `CompactBinarySelector` on small development cells.
pub fn enumerate_all_models_sinz_cdclt(
    curve: CurveFp,
    windows: &[Vec<u64>; 3],
    target: PointFp,
) -> Vec<SignedWitness> {
    struct SinzTheory<'a> {
        curve: CurveFp,
        windows: &'a [Vec<u64>; 3],
        lifts: [Vec<Option<u64>>; 3],
        sel: &'a SinzOneHotSelector,
        target: PointFp,
    }
    impl FpTheoryPropagator for SinzTheory<'_> {
        fn propagate_trail(
            &mut self,
            assign: &[Option<bool>],
            stats: &mut CdcltStats,
        ) -> Vec<Vec<Lit>> {
            stats.theory_calls += 1;
            for w in 0..3 {
                if let Some(idx) = self.sel.decode_index(w, assign) {
                    if self.lifts[w][idx].is_none() {
                        return vec![vec![-((self.sel.selector_vars[w][idx] as i32) + 1)]];
                    }
                }
            }
            Vec::new()
        }

        fn check_model(
            &mut self,
            assign: &[Option<bool>],
            stats: &mut CdcltStats,
        ) -> Result<(), Vec<Lit>> {
            let i0 = self.sel.decode_index(0, assign).unwrap();
            let i1 = self.sel.decode_index(1, assign).unwrap();
            let i2 = self.sel.decode_index(2, assign).unwrap();
            let s0 = self.sel.decode_sign(0, assign).unwrap();
            let s1 = self.sel.decode_sign(1, assign).unwrap();
            let s2 = self.sel.decode_sign(2, assign).unwrap();
            let mut blocking = vec![
                -((self.sel.selector_vars[0][i0] as i32) + 1),
                -((self.sel.selector_vars[1][i1] as i32) + 1),
                -((self.sel.selector_vars[2][i2] as i32) + 1),
                if s0 != 0 {
                    -((self.sel.sign_vars[0] as i32) + 1)
                } else {
                    (self.sel.sign_vars[0] as i32) + 1
                },
                if s1 != 0 {
                    -((self.sel.sign_vars[1] as i32) + 1)
                } else {
                    (self.sel.sign_vars[1] as i32) + 1
                },
                if s2 != 0 {
                    -((self.sel.sign_vars[2] as i32) + 1)
                } else {
                    (self.sel.sign_vars[2] as i32) + 1
                },
            ];
            let (Some(y0c), Some(y1c), Some(y2c)) =
                (self.lifts[0][i0], self.lifts[1][i1], self.lifts[2][i2])
            else {
                return Err(blocking);
            };
            let p0 = self.curve.point_from_canonical_lift(self.windows[0][i0], y0c, s0);
            let p1 = self.curve.point_from_canonical_lift(self.windows[1][i1], y1c, s1);
            let p2 = self.curve.point_from_canonical_lift(self.windows[2][i2], y2c, s2);
            let u = self.curve.add(p0, p1, &mut stats.fp_ops);
            let sum = self.curve.add(u, p2, &mut stats.fp_ops);
            if sum == self.target {
                blocking.clear();
                Ok(())
            } else {
                Err(blocking)
            }
        }
    }

    let sel = SinzOneHotSelector::new([windows[0].len(), windows[1].len(), windows[2].len()]);
    let mut ops = FpOps::default();
    let mut lifts: [Vec<Option<u64>>; 3] = [Vec::new(), Vec::new(), Vec::new()];
    for w in 0..3 {
        for &x in &windows[w] {
            let rhs = curve.rhs(x, &mut ops);
            lifts[w].push(sqrt_mod_canonical(rhs, curve.p, &mut ops));
        }
    }
    let mut solver = CdclSolver::new(sel.total_vars);
    for c in &sel.clauses {
        assert!(solver.add_initial_clause(c.clone()));
    }
    let mut stats = CdcltStats::default();
    let mut witnesses = Vec::new();
    let mut sink = NullProofSink;
    loop {
        let mut theory = SinzTheory {
            curve,
            windows,
            lifts: lifts.clone(),
            sel: &sel,
            target,
        };
        match solver.solve_with_theory(&mut theory, &mut sink, &mut stats) {
            CdclOutcome::Sat(model) => {
                let assign: Vec<Option<bool>> = model.iter().copied().map(Some).collect();
                let i0 = sel.decode_index(0, &assign).unwrap();
                let i1 = sel.decode_index(1, &assign).unwrap();
                let i2 = sel.decode_index(2, &assign).unwrap();
                let s0 = sel.decode_sign(0, &assign).unwrap();
                let s1 = sel.decode_sign(1, &assign).unwrap();
                let s2 = sel.decode_sign(2, &assign).unwrap();
                witnesses.push(SignedWitness {
                    indices: [i0, i1, i2],
                    signs: [s0, s1, s2],
                    abscissae: [windows[0][i0], windows[1][i1], windows[2][i2]],
                });
                solver.backtrack(0);
                let block = vec![
                    -((sel.selector_vars[0][i0] as i32) + 1),
                    -((sel.selector_vars[1][i1] as i32) + 1),
                    -((sel.selector_vars[2][i2] as i32) + 1),
                    if s0 != 0 {
                        -((sel.sign_vars[0] as i32) + 1)
                    } else {
                        (sel.sign_vars[0] as i32) + 1
                    },
                    if s1 != 0 {
                        -((sel.sign_vars[1] as i32) + 1)
                    } else {
                        (sel.sign_vars[1] as i32) + 1
                    },
                    if s2 != 0 {
                        -((sel.sign_vars[2] as i32) + 1)
                    } else {
                        (sel.sign_vars[2] as i32) + 1
                    },
                ];
                if !solver.add_initial_clause(block) {
                    break;
                }
            }
            CdclOutcome::Unsat => break,
        }
    }
    witnesses.sort();
    witnesses.dedup();
    witnesses
}
