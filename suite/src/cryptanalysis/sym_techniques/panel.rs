//! Panel registration of the work-package techniques: one [`Technique`]
//! wrapper per [`TechniqueId`] that runs a package's main entry point under a
//! [`Budget`] and reports a [`TechniqueResult`] with a JSON outcome.
//!
//! Every wrapper
//!
//! * returns an outcome whose `status` is one of `"ok"`, `"not_found"` (the
//!   search finished without the object it looks for), `"budget_exhausted"`,
//!   `"unsupported"` (the package reports that it cannot model the
//!   primitive) or `"error"` (the package panicked; the message is kept);
//! * checks [`Budget::wall_expired`] between units of work. The packages'
//!   own searches are not preemptible, so each is given node, conflict, pair
//!   or sample limits sized to finish in seconds, and a wrapper that loops
//!   over round counts stops at the first round count after the wall clock
//!   has expired;
//! * counts cost in the attack's own units: `cost.time_evals` is primitive
//!   evaluations, and search nodes, SAT conflicts or pair checks (which are
//!   not primitive evaluations) are reported in the outcome instead.
//!
//! Applicability is decided by
//! [`applicable_techniques`](super::applicable_techniques) from the IR; the
//! structural recognisers [`chacha_word_bits`] and [`sha2_family`] used there
//! compare the primitive's function with the reference IR description of the
//! same round count on fixed inputs, never its name.
//!
//! Numbers returned here are observations under the stated budget, not
//! claims about the primitive.

use crate::cryptanalysis::hash_attacks::{
    birthday_collision_search, joux_multicollision, length_extension_attack, HashFunction,
    MerkleDamgardHash,
};
use crate::cryptanalysis::sym_ir::gf2::words_for;
use crate::cryptanalysis::sym_ir::primitives::{
    chacha, md5_compress, sha256_compress, sha512_compress,
};
use crate::cryptanalysis::sym_ir::{eval, Primitive};
use crate::cryptanalysis::sym_techniques::arx::diff_linear::{
    bit_vector, chacha_nonce_counter_bits, DlTarget,
};
use crate::cryptanalysis::sym_techniques::arx::pnb::{best_significant, PnbTarget};
use crate::cryptanalysis::sym_techniques::arx::rotational::{
    empirical_rx, rotational_applicable, rotational_chain, rx_chain,
};
use crate::cryptanalysis::sym_techniques::hash::local_collision::Sha2Params;
use crate::cryptanalysis::sym_techniques::hash::md_adaptor::IrMdHash;
use crate::cryptanalysis::sym_techniques::hash::semi_free_start::{
    best_placement, sfs_by_local_collision, verify as verify_sfs,
};
use crate::cryptanalysis::sym_techniques::integral::division_property::{
    longest_integral_distinguisher, IntegralError,
};
use crate::cryptanalysis::sym_techniques::trails::{
    self, Direction, Engine, SearchOptions, TrailError,
};
use crate::cryptanalysis::sym_techniques::{
    impossible, mitm, zero_correlation, Budget, Cost, Technique, TechniqueId, TechniqueResult,
};
use serde_json::{json, Value};
use std::panic::{catch_unwind, AssertUnwindSafe};

// ── Structural recognisers (used by `applicable_techniques`) ────────────

/// The hash families the panel has reference descriptions for.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Sha2Family {
    /// SHA-256 steps (32-bit words).
    Sha256,
    /// SHA-512 steps (64-bit words).
    Sha512,
    /// MD5 steps.
    Md5,
}

/// Deterministic pseudo-random bytes (xorshift64*), for function
/// comparisons.
fn fixed_bytes(n: usize, seed: u64) -> Vec<u8> {
    let mut s = seed | 1;
    (0..n)
        .map(|_| {
            s ^= s >> 12;
            s ^= s << 25;
            s ^= s >> 27;
            (s.wrapping_mul(0x2545_F491_4F6C_DD1D) >> 56) as u8
        })
        .collect()
}

/// Whether `p` and `q` agree on three fixed (key, block) inputs.
fn same_function(p: &Primitive, q: &Primitive) -> bool {
    if p.block_bits != q.block_bits || p.key_bits != q.key_bits {
        return false;
    }
    (0..3u64).all(|i| {
        let k = fixed_bytes(p.key_bytes(), 0xA5 + i);
        let b = fixed_bytes(p.block_bytes(), 0x5A + i);
        eval(p, &k, &b) == eval(q, &k, &b)
    })
}

/// The word width `w` when `p` computes the reduced-width ChaCha
/// permutation (with feed-forward) of its round count, else `None`.
pub fn chacha_word_bits(p: &Primitive) -> Option<usize> {
    if p.key_bits != 0 || !p.block_bits.is_multiple_of(16) || p.num_rounds() == 0 {
        return None;
    }
    let w = p.block_bits / 16;
    if !matches!(w, 8 | 16 | 32) {
        return None;
    }
    same_function(p, &chacha::reduced_width(w, p.num_rounds())).then_some(w)
}

/// The hash family when `p` computes the first `num_rounds()` steps of the
/// SHA-256, SHA-512 or MD5 compression function, else `None`.
pub fn sha2_family(p: &Primitive) -> Option<Sha2Family> {
    let n = p.num_rounds();
    if p.key_bits == 0 || n == 0 {
        return None;
    }
    match (p.block_bits, p.key_bits) {
        (256, 512) if n <= 64 => {
            same_function(p, &sha256_compress::steps(n)).then_some(Sha2Family::Sha256)
        }
        (512, 1024) if n <= 80 => {
            same_function(p, &sha512_compress::steps(n)).then_some(Sha2Family::Sha512)
        }
        (128, 512) if n <= 64 => {
            same_function(p, &md5_compress::steps(n)).then_some(Sha2Family::Md5)
        }
        _ => None,
    }
}

/// Window of the delta-set cost table: `(front, inner)` rounds. The window
/// is four inner rounds (Demirci-Selcuk) with one front round when at least
/// six rounds exist; with fewer rounds the window is all of them (so the
/// table is not the published 7-round structure, which needs seven).
pub fn delta_set_window(p: &Primitive) -> (usize, usize) {
    let r = p.num_rounds();
    (usize::from(r >= 6), r.min(4))
}

/// Whether the trail model can be built for `p` in `direction` (the rule
/// behind the trail techniques' applicability).
pub fn trail_model_ok(p: &Primitive, direction: Direction) -> bool {
    trails::TrailModel::from_primitive(p, p.num_rounds(), direction).is_ok()
}

// ── Result helpers ──────────────────────────────────────────────────────

fn result(
    id: TechniqueId,
    p: &Primitive,
    cost: Cost,
    outcome: Value,
    budget_exhausted: bool,
) -> TechniqueResult {
    TechniqueResult {
        technique: id,
        primitive: p.name.clone(),
        cost,
        outcome,
        budget_exhausted,
    }
}

fn unsupported(id: TechniqueId, p: &Primitive, reason: impl Into<String>) -> TechniqueResult {
    result(
        id,
        p,
        Cost::default(),
        json!({"status": "unsupported", "reason": reason.into()}),
        false,
    )
}

fn exhausted(id: TechniqueId, p: &Primitive, what: &str) -> TechniqueResult {
    result(
        id,
        p,
        Cost::default(),
        json!({"status": "budget_exhausted", "reason": what}),
        true,
    )
}

/// Run `f`, turning a panic into an `"error"` row instead of aborting the
/// panel.
fn guarded(id: TechniqueId, p: &Primitive, f: impl FnOnce() -> TechniqueResult) -> TechniqueResult {
    match catch_unwind(AssertUnwindSafe(f)) {
        Ok(r) => r,
        Err(e) => {
            let msg = e
                .downcast_ref::<String>()
                .cloned()
                .or_else(|| e.downcast_ref::<&str>().map(|s| s.to_string()))
                .unwrap_or_else(|| "panic".into());
            result(
                id,
                p,
                Cost::default(),
                json!({"status": "error", "panic": msg}),
                false,
            )
        }
    }
}

/// Add a `budget_note` string to the outcome object of `r`: where the panel
/// number is below the package's own reproduction because of the panel
/// budget, the row says so and points at the test that reaches more.
fn with_budget_note(mut r: TechniqueResult, note: &str) -> TechniqueResult {
    if let Some(o) = r.outcome.as_object_mut() {
        o.insert("budget_note".into(), json!(note));
    }
    r
}

fn status_of(o: &Value) -> &str {
    o["status"].as_str().unwrap_or("?")
}

/// The default table layout plus the outcome status.
fn md_outcome(r: &TechniqueResult) -> String {
    format!(
        "- **status**: {}\n- **cost**: data {}, evals {}, memory {} B\n- **budget exhausted**: {}\n- **outcome**: `{}`\n",
        status_of(&r.outcome),
        r.cost.data,
        r.cost.time_evals,
        r.cost.memory,
        r.budget_exhausted,
        r.outcome,
    )
}

// ── Trails ──────────────────────────────────────────────────────────────

/// Minimum active S-boxes of differential or linear trails
/// (`trails::{differential,linear}::min_active_sboxes`) over all rounds of
/// the primitive: exact value engine for S-boxes of at most 4 bits (falling
/// back to the word engine, a lower bound, when its node budget, 32 times `max_time_evals`, runs out),
/// word engine otherwise. When the S-boxes are at most 4 bits wide the best
/// concrete trail is also searched (`with_concrete`) and compared with the
/// panel's `trail_threshold`. `trail_top_k` is not used.
pub struct TrailSearchTechnique {
    direction: Direction,
}

impl TrailSearchTechnique {
    /// Differential trails ([`TechniqueId::DifferentialTrails`]).
    pub fn differential() -> Self {
        Self {
            direction: Direction::Differential,
        }
    }
    /// Linear trails ([`TechniqueId::LinearTrails`]).
    pub fn linear() -> Self {
        Self {
            direction: Direction::Linear,
        }
    }
}

impl Technique for TrailSearchTechnique {
    fn id(&self) -> TechniqueId {
        match self.direction {
            Direction::Differential => TechniqueId::DifferentialTrails,
            Direction::Linear => TechniqueId::LinearTrails,
        }
    }
    fn title(&self) -> String {
        match self.direction {
            Direction::Differential => "Differential trail search".into(),
            Direction::Linear => "Linear trail search".into(),
        }
    }
    fn run(&self, p: &Primitive, budget: &Budget) -> TechniqueResult {
        let id = self.id();
        guarded(id, p, || {
            if budget.wall_expired() {
                return exhausted(id, p, "wall clock expired before start");
            }
            let rounds = p.num_rounds();
            let mut opts = SearchOptions {
                engine: Engine::Auto,
                node_budget: budget.max_time_evals.saturating_mul(32),
                with_concrete: true,
            };
            let search = |o: &SearchOptions| match self.direction {
                Direction::Differential => trails::differential::min_active_sboxes(p, rounds, o),
                Direction::Linear => trails::linear::min_active_sboxes(p, rounds, o),
            };
            let mut fell_back = false;
            let r = match search(&opts) {
                Err(TrailError::BudgetExceeded) => {
                    fell_back = true;
                    opts.engine = Engine::Word;
                    opts.with_concrete = false;
                    search(&opts)
                }
                other => other,
            };
            match r {
                Err(TrailError::BudgetExceeded) => exhausted(id, p, "node budget"),
                Err(e) => unsupported(id, p, e.to_string()),
                Ok(a) => {
                    let th = budget.params.trail_threshold;
                    let concrete = a.concrete.as_ref().map(|c| {
                        json!({
                            "weight": c.weight,
                            "meets_threshold": c.weight <= -th.log2() + 1e-9,
                            "threshold_log2": th.log2(),
                        })
                    });
                    result(
                        id,
                        p,
                        Cost::default(),
                        json!({
                            "status": "ok",
                            "rounds": rounds,
                            "min_active_sboxes": a.min_active,
                            "best_by_rounds": a.best_by_rounds,
                            "exact": a.exact,
                            "engine": format!("{:?}", a.engine),
                            "engine_fell_back_to_word": fell_back,
                            "search_nodes": a.nodes,
                            "pattern": a.pattern,
                            "best_concrete_trail": concrete,
                            "concrete_budget_exceeded": a.concrete_budget_exceeded,
                        }),
                        fell_back,
                    )
                }
            }
        })
    }
    fn markdown(&self, r: &TechniqueResult) -> String {
        let o = &r.outcome;
        if status_of(o) != "ok" {
            return md_outcome(r);
        }
        let mut s = format!(
            "Minimum number of active S-boxes over {} rounds: **{}** ({}; engine {}).\n\n- **per-round minima** (suffix windows): `{}`\n- **search nodes**: {}\n",
            o["rounds"],
            o["min_active_sboxes"],
            if o["exact"].as_bool() == Some(true) {
                "exact for the model"
            } else {
                "lower bound, word-level relaxation"
            },
            o["engine"].as_str().unwrap_or("?"),
            o["best_by_rounds"],
            o["search_nodes"],
        );
        if let Some(c) = o["best_concrete_trail"].as_object() {
            s.push_str(&format!(
                "- **best concrete trail**: weight {:.2} (log2 p or |corr| = {:.2}); meets threshold 2^{}: {}\n",
                c["weight"].as_f64().unwrap_or(f64::NAN),
                -c["weight"].as_f64().unwrap_or(f64::NAN),
                c["threshold_log2"].as_f64().unwrap_or(f64::NAN).round(),
                c["meets_threshold"]
            ));
        }
        s
    }
}

/// Rounds given to the MILP and SAT cells (the solvers prove each prefix in
/// turn, so cost grows quickly with rounds).
pub const SOLVER_MAX_ROUNDS: usize = 5;

/// MILP and SAT encodings of the same minimum-active-S-box question
/// (`trails::milp`, `trails::sat`), differential direction, over at most
/// [`SOLVER_MAX_ROUNDS`] rounds with small node, conflict and time limits (the MILP time limit is per solve, at most 12 s and the remaining wall clock).
pub struct SolverTrailTechnique {
    sat: bool,
}

impl SolverTrailTechnique {
    /// MILP ([`TechniqueId::MilpTrails`]).
    pub fn milp() -> Self {
        Self { sat: false }
    }
    /// SAT ([`TechniqueId::SatTrails`]).
    pub fn sat() -> Self {
        Self { sat: true }
    }
}

impl Technique for SolverTrailTechnique {
    fn id(&self) -> TechniqueId {
        if self.sat {
            TechniqueId::SatTrails
        } else {
            TechniqueId::MilpTrails
        }
    }
    fn title(&self) -> String {
        if self.sat {
            "SAT trail bound".into()
        } else {
            "MILP trail bound".into()
        }
    }
    fn run(&self, p: &Primitive, budget: &Budget) -> TechniqueResult {
        let id = self.id();
        guarded(id, p, || {
            if budget.wall_expired() {
                return exhausted(id, p, "wall clock expired before start");
            }
            let rounds = p.num_rounds().min(SOLVER_MAX_ROUNDS);
            let left_ms = budget
                .max_wall
                .saturating_sub(budget.started.elapsed())
                .as_millis() as u64;
            let out = if self.sat {
                let o = trails::sat::SatOptions {
                    level: trails::sat::Level::Auto,
                    conflict_budget: 200_000,
                };
                trails::sat::min_active_sboxes(p, rounds, Direction::Differential, &o).map(|r| {
                    (
                        r.min_active,
                        r.pattern,
                        json!({"solver_calls": r.solver_calls, "conflicts": r.conflicts,
                               "vars": r.n_vars, "clauses": r.n_clauses,
                               "level": format!("{:?}", r.level)}),
                    )
                })
            } else {
                let o = trails::milp::MilpOptions {
                    level: trails::sat::Level::Auto,
                    node_budget: 5_000,
                    time_limit_ms: left_ms.clamp(500, 12_000),
                    window_cuts: true,
                };
                trails::milp::min_active_sboxes(p, rounds, Direction::Differential, &o).map(|r| {
                    (
                        r.min_active,
                        r.pattern,
                        json!({"bnb_nodes": r.nodes, "vars": r.n_vars, "rows": r.n_rows,
                               "minima_by_rounds": r.minima_by_rounds,
                               "level": format!("{:?}", r.level)}),
                    )
                })
            };
            match out {
                Err(TrailError::BudgetExceeded) => exhausted(id, p, "solver budget"),
                Err(e) => unsupported(id, p, e.to_string()),
                Ok((min_active, pattern, detail)) => result(
                    id,
                    p,
                    Cost::default(),
                    json!({
                        "status": "ok",
                        "rounds": rounds,
                        "min_active_sboxes": min_active,
                        "pattern": pattern,
                        "solver": detail,
                    }),
                    false,
                ),
            }
        })
    }
}

// ── Integral ────────────────────────────────────────────────────────────

/// SAT conflict budget of each bit-level division-property query (the
/// 4-round all-but-one-bit AES queries are out of reach of this solver at
/// any small budget and are skipped and flagged).
pub const DIVISION_CONFLICTS: u64 = 1_000;

/// `integral::division_property::longest_integral_distinguisher` over all
/// rounds, with [`DIVISION_CONFLICTS`] conflicts per bit-level query.
pub struct DivisionPropertyTechnique;

impl Technique for DivisionPropertyTechnique {
    fn id(&self) -> TechniqueId {
        TechniqueId::DivisionProperty
    }
    fn title(&self) -> String {
        "Division-property integral distinguisher".into()
    }
    fn run(&self, p: &Primitive, budget: &Budget) -> TechniqueResult {
        let id = self.id();
        guarded(id, p, || {
            if budget.wall_expired() {
                return exhausted(id, p, "wall clock expired before start");
            }
            match longest_integral_distinguisher(p, p.num_rounds(), DIVISION_CONFLICTS) {
                Err(IntegralError::Unsupported(s)) => unsupported(id, p, s),
                Err(IntegralError::BudgetExceeded) => exhausted(id, p, "conflict budget"),
                Ok(s) => {
                    let best = s.best.as_ref().map(|d| {
                        json!({
                            "rounds": d.rounds,
                            "level": format!("{:?}", d.level),
                            "log2_data": d.log2_data,
                            "active_bits": d.active_bits.len(),
                            "balanced_bits": d.balanced_bits.len(),
                        })
                    });
                    let status = if best.is_some() { "ok" } else { "not_found" };
                    let r = result(
                        id,
                        p,
                        Cost::default(),
                        json!({
                            "status": status,
                            "best": best,
                            "best_word_rounds": s.best_word.as_ref().map(|d| d.rounds),
                            "bit_candidates_tried": s.bit_candidates_tried,
                        }),
                        s.budget_exhausted,
                    );
                    if p.name.to_ascii_lowercase().starts_with("present") {
                        with_budget_note(
                            r,
                            "panel budget 1000 conflicts/query; package reaches 9 rounds \
                             with larger budget \u{2014} see integral tests",
                        )
                    } else {
                        r
                    }
                }
            }
        })
    }
}

// ── Impossible differential / zero correlation / delta-set MITM ─────────

/// Miss-in-the-middle searches (`impossible::longest_impossible_differential`
/// and `zero_correlation::longest_zero_correlation`) over all rounds with
/// patterns of at most two active cells and 5 million pair checks.
pub struct MissInTheMiddleTechnique {
    zero_correlation: bool,
}

impl MissInTheMiddleTechnique {
    /// Impossible differential ([`TechniqueId::ImpossibleDifferential`]).
    pub fn impossible() -> Self {
        Self {
            zero_correlation: false,
        }
    }
    /// Zero correlation ([`TechniqueId::ZeroCorrelation`]).
    pub fn zero_correlation() -> Self {
        Self {
            zero_correlation: true,
        }
    }
}

impl Technique for MissInTheMiddleTechnique {
    fn id(&self) -> TechniqueId {
        if self.zero_correlation {
            TechniqueId::ZeroCorrelation
        } else {
            TechniqueId::ImpossibleDifferential
        }
    }
    fn title(&self) -> String {
        if self.zero_correlation {
            "Zero-correlation linear hull".into()
        } else {
            "Impossible differential".into()
        }
    }
    fn run(&self, p: &Primitive, budget: &Budget) -> TechniqueResult {
        let id = self.id();
        guarded(id, p, || {
            if budget.wall_expired() {
                return exhausted(id, p, "wall clock expired before start");
            }
            let sb = impossible::SearchBudget {
                max_rounds: p.num_rounds(),
                max_pattern_weight: 2,
                max_pair_checks: 5_000_000,
            };
            let r = if self.zero_correlation {
                zero_correlation::longest_zero_correlation(p, &sb)
            } else {
                impossible::longest_impossible_differential(p, &sb)
            };
            match r {
                Err(e) => unsupported(id, p, e.to_string()),
                Ok(rep) => {
                    let best = rep.best.as_ref().map(|m| {
                        json!({
                            "rounds": m.rounds,
                            "propagation": format!("{:?}", m.propagation),
                            "model": format!("{:?}", m.model),
                            "final_linear_dropped": m.final_linear_dropped,
                            "cell_bits": m.cell_bits,
                            "input_active_cells": m.input.len(),
                            "output_active_cells": m.output.len(),
                        })
                    });
                    result(
                        id,
                        p,
                        Cost::default(),
                        json!({
                            "status": if best.is_some() { "ok" } else { "not_found" },
                            "best": best,
                            "attempts": rep.attempts.len(),
                            "pair_checks": rep.pair_checks,
                        }),
                        rep.budget_exhausted,
                    )
                }
            }
        })
    }
}

/// `mitm::delta_set_cost_table` for the window of [`delta_set_window`] with
/// cell 0 active and cell 0 as the target (the Demirci-Selcuk setting).
/// Reports the model cost table only; no attack is run.
pub struct DeltaSetTechnique;

impl Technique for DeltaSetTechnique {
    fn id(&self) -> TechniqueId {
        TechniqueId::DeltaSetMitm
    }
    fn title(&self) -> String {
        "Delta-set MITM cost table".into()
    }
    fn run(&self, p: &Primitive, budget: &Budget) -> TechniqueResult {
        let id = self.id();
        guarded(id, p, || {
            if budget.wall_expired() {
                return exhausted(id, p, "wall clock expired before start");
            }
            let (front, inner) = delta_set_window(p);
            match mitm::delta_set_cost_table(p, front, inner, 0, 0) {
                Err(e) => unsupported(id, p, e.to_string()),
                Ok(t) => {
                    let inner = t.inner_rounds;
                    let r = result(
                        id,
                        p,
                        Cost::default(),
                        json!({
                            "status": "ok",
                            "front_rounds": t.front_rounds,
                            "inner_rounds": t.inner_rounds,
                            "back_rounds": t.back_rounds,
                            "params_ordered": t.params_ordered,
                            "params_multiset": t.params_multiset,
                            "data_log2": t.data_log2,
                            "table_ordered_log2": t.table_ordered_log2,
                            "table_multiset_log2": t.table_multiset_log2,
                            "guesses_log2": t.guesses_log2,
                            "online_time_log2": t.online_time_log2,
                            "time_ordered_log2": t.time_ordered_log2,
                            "memory_ordered_log2": t.memory_ordered_log2,
                            "model_only": true,
                        }),
                        false,
                    );
                    if p.name.to_ascii_lowercase().starts_with("aes") && inner == 4 {
                        with_budget_note(
                            r,
                            "4-round window at panel defaults; 7-round counts 25/24 in \
                             mitm tests",
                        )
                    } else {
                        r
                    }
                }
            }
        })
    }
}

// ── ARX ─────────────────────────────────────────────────────────────────

/// Block bits flipped by the single-bit differential-linear search: the
/// counter/nonce words for ChaCha, otherwise every block bit when the block
/// has at most 64 bits and 64 evenly spaced bits when it is larger.
fn dl_in_bits(p: &Primitive) -> Vec<usize> {
    if let Some(w) = chacha_word_bits(p) {
        return chacha_nonce_counter_bits(w).collect();
    }
    if p.block_bits <= 64 {
        (0..p.block_bits).collect()
    } else {
        let step = p.block_bits / 64;
        (0..64).map(|i| i * step).collect()
    }
}

/// Largest round count tried by the differential-linear cell (single-bit
/// differentials against single-bit masks have no resolvable bias beyond
/// about four ChaCha rounds).
pub const DL_MAX_ROUNDS: usize = 4;

fn chacha_constants(p: &Primitive) -> Vec<(usize, u64)> {
    match chacha_word_bits(p) {
        Some(w) => chacha::constants(w).iter().copied().enumerate().collect(),
        None => Vec::new(),
    }
}

/// `arx::diff_linear` single-bit search: for `r = 1..=min(R, 4)` rounds,
/// every input bit of the scanned set against every single output-bit mask,
/// top candidates re-estimated on fresh samples. The headline is the longest
/// `r` whose confirmed bias has `|z| >= 5`. The ChaCha constants are pinned.
pub struct ArxDiffLinearTechnique;

impl Technique for ArxDiffLinearTechnique {
    fn id(&self) -> TechniqueId {
        TechniqueId::ArxDiffLinear
    }
    fn title(&self) -> String {
        "Differential-linear single-bit search".into()
    }
    fn run(&self, p: &Primitive, budget: &Budget) -> TechniqueResult {
        let id = self.id();
        guarded(id, p, || {
            let in_bits = dl_in_bits(p);
            let keyed = p.key_bits > 0;
            // The compiled evaluator (key-free primitives) is much faster
            // than `eval_rounds`; size the samples accordingly.
            let (n_search, n_confirm): (u64, u64) = if keyed {
                (1 << 11, 1 << 14)
            } else {
                (1 << 15, 1 << 18)
            };
            let top_k = 3;
            let consts = chacha_constants(p);
            let mut per_round = Vec::new();
            let (mut evals, mut stopped) = (0u64, false);
            let mut longest: Option<usize> = None;
            for r in 1..=p.num_rounds().min(DL_MAX_ROUNDS) {
                if budget.wall_expired() || evals >= budget.max_time_evals {
                    stopped = true;
                    break;
                }
                let t = DlTarget::new(p, r).with_fixed_words(&consts);
                let c = t.search_single_bit(&in_bits, n_search, top_k, n_confirm, 0xD1 + r as u64);
                evals += 2 * (in_bits.len() as u64 * n_search + top_k as u64 * n_confirm);
                if let Some(b) = c.first() {
                    let significant = b.confirm.z.abs() >= 5.0;
                    if significant {
                        longest = Some(r);
                    }
                    per_round.push(json!({
                        "rounds": r,
                        "in_bit": b.in_bit,
                        "out_bit": b.out_bit,
                        "eps": b.confirm.eps,
                        "abs_eps": b.confirm.eps.abs(),
                        "z": b.confirm.z,
                        "std_err": b.confirm.eps_std_err(),
                        "search_eps": b.search.eps,
                        "samples_confirm": b.confirm.samples,
                        "significant": significant,
                    }));
                }
            }
            // Published control (Aumasson et al., FSE 2008): ChaCha, 3
            // rounds, input difference at bit 13 of word 13, output mask bit
            // 0 of word 11, |eps| about 0.027. Measured on 2^22 pairs when
            // the primitive is 32-bit ChaCha with at least 3 rounds.
            let control = (chacha_word_bits(p) == Some(32) && p.num_rounds() >= 3).then(|| {
                let n = 1u64 << 22;
                let e = DlTarget::new(p, 3)
                    .with_fixed_words(&consts)
                    .estimate_bias_bits(&[13 * 32 + 13], &[11 * 32], n, 0xC0);
                evals += 2 * n;
                json!({"rounds": 3, "in_bit": 13 * 32 + 13, "out_bit": 11 * 32,
                       "eps": e.eps, "std_err": e.eps_std_err(), "samples": e.samples,
                       "published_abs_eps": 0.027})
            });
            let cost = Cost {
                data: evals,
                time_evals: evals,
                memory: 0,
            };
            result(
                id,
                p,
                cost,
                json!({
                    "published_control": control,
                    "status": if longest.is_some() { "ok" } else { "not_found" },
                    "longest_significant_rounds": longest,
                    "input_bits_scanned": in_bits.len(),
                    "n_search": n_search,
                    "n_confirm": n_confirm,
                    "per_round": per_round,
                    "compiled_evaluator": !keyed,
                }),
                stopped,
            )
        })
    }
}

/// `arx::pnb` on ChaCha-like permutations (recognised by
/// [`chacha_word_bits`]; other ARX primitives have no PNB target). A
/// distinguisher is searched at `r = min(3, R - 1)` rounds (single-bit
/// counter/nonce differences, as in [`ArxDiffLinearTechnique`]); if its
/// confirmed bias has `|z| >= 5`, neutrality measures and a threshold sweep
/// give the attack-complexity estimate (`eps* = eps_d * eps_a`, the Aumasson
/// et al. 2008 formula) of the best significant row. Sample sizes are
/// smaller than in the published-control test (`arx::tests`), so `m` and the
/// time estimate are noisier.
pub struct ArxPnbTechnique;

impl Technique for ArxPnbTechnique {
    fn id(&self) -> TechniqueId {
        TechniqueId::ArxPnb
    }
    fn title(&self) -> String {
        "Probabilistic neutral bits (ChaCha)".into()
    }
    fn run(&self, p: &Primitive, budget: &Budget) -> TechniqueResult {
        let id = self.id();
        guarded(id, p, || {
            let Some(w) = chacha_word_bits(p) else {
                return unsupported(id, p, "not a ChaCha-like permutation");
            };
            let big_r = p.num_rounds();
            if big_r < 2 {
                return unsupported(id, p, "needs at least 2 rounds");
            }
            if budget.wall_expired() {
                return exhausted(id, p, "wall clock expired before start");
            }
            let r = 3.min(big_r - 1);
            let t = PnbTarget::chacha(p);
            let in_bits = chacha_nonce_counter_bits(w).collect::<Vec<_>>();
            let (n_search, n_confirm) = (1u64 << 15, 1u64 << 19);
            let (dist, cand) = t.find_distinguisher(r, &in_bits, n_search, 3, n_confirm, 0x9B);
            let mut evals = 2 * (in_bits.len() as u64 * n_search + 3 * n_confirm);
            let dl = json!({
                "rounds": r, "in_bit": cand.in_bit, "out_bit": cand.out_bit,
                "eps_d": dist.eps_d, "z": cand.confirm.z,
            });
            if cand.confirm.z.abs() < 5.0 {
                return result(
                    id,
                    p,
                    Cost {
                        data: evals,
                        time_evals: evals,
                        memory: 0,
                    },
                    json!({"status": "not_found", "reason": "no distinguisher with |z| >= 5",
                           "distinguisher": dl, "total_rounds": big_r}),
                    false,
                );
            }
            if budget.wall_expired() {
                return exhausted(id, p, "wall clock expired after distinguisher search");
            }
            let n_neut = 1u64 << 10;
            let gam = t.neutrality_measures(&dist, n_neut, 0x9C);
            evals += n_neut * t.key_bits() as u64 * 2;
            let n_sweep = 1u64 << 15;
            let thresholds = [0.9, 0.8, 0.7, 0.6, 0.5];
            let rows = t.sweep(&dist, &gam, &thresholds, n_sweep, 0x9D);
            evals += thresholds.len() as u64 * n_sweep * 2;
            let best = best_significant(&rows).map(|r| {
                json!({
                    "gamma": r.gamma, "m": r.m,
                    "eps_a": r.backward.eps_a.eps,
                    "log2_time": r.complexity.log2_time,
                    "log2_data_pairs": r.complexity.log2_data_pairs,
                    "key_bits": r.complexity.n,
                    "beats_brute_force": r.complexity.beats_brute_force,
                })
            });
            let r = result(
                id,
                p,
                Cost {
                    data: evals,
                    time_evals: evals,
                    memory: 0,
                },
                json!({
                    "status": if best.is_some() { "ok" } else { "not_found" },
                    "total_rounds": big_r,
                    "distinguisher": dl,
                    "best_significant_row": best,
                    "rows": rows.iter().map(|r| json!({
                        "gamma": r.gamma, "m": r.m,
                        "significant": r.significant(),
                        "log2_time": r.complexity.log2_time,
                    })).collect::<Vec<_>>(),
                    "estimate_only": true,
                }),
                false,
            );
            if w == 32 && big_r == 6 {
                with_budget_note(
                    r,
                    "small sample sizes; package estimate 2^135.7, published 2^139",
                )
            } else {
                r
            }
        })
    }
}

/// `arx::rotational::rotational_chain` over every rotation amount
/// `gamma = 1..w-1` (`w` = block word width): the pure-rotational
/// probability estimate of the primitive. The estimate is a product of exact
/// per-addition probabilities along one trajectory; a rotation-variant
/// constant makes it zero (reported as `symmetry_broken`).
pub struct ArxRotationalTechnique;

impl Technique for ArxRotationalTechnique {
    fn id(&self) -> TechniqueId {
        TechniqueId::ArxRotational
    }
    fn title(&self) -> String {
        "Rotational estimate".into()
    }
    fn run(&self, p: &Primitive, budget: &Budget) -> TechniqueResult {
        let id = self.id();
        guarded(id, p, || {
            if let Err(reason) = rotational_applicable(p) {
                return unsupported(id, p, reason);
            }
            let w = p.block_codec.word_bits;
            let rounds = p.num_rounds();
            let mut best: Option<(usize, f64)> = None;
            let (mut tried, mut stopped) = (0usize, false);
            let mut sample = (0, 0, 0, 0);
            for gamma in 1..w {
                if budget.wall_expired() {
                    stopped = true;
                    break;
                }
                let c = rotational_chain(p, rounds, gamma);
                tried += 1;
                if !c.supported {
                    return unsupported(id, p, "operations outside the rotational model");
                }
                if best.is_none_or(|(_, l)| c.log2_prob > l) {
                    best = Some((gamma, c.log2_prob));
                    sample = (
                        c.data_adds,
                        c.key_schedule_adds,
                        c.const_adds,
                        c.flags.len(),
                    );
                }
            }
            let Some((gamma, l)) = best else {
                return unsupported(id, p, "no rotation amount to try");
            };
            result(
                id,
                p,
                Cost::default(),
                json!({
                    "status": "ok",
                    "rounds": rounds,
                    "best_gamma": gamma,
                    "log2_prob": if l.is_finite() { json!(l) } else { Value::Null },
                    "symmetry_broken": !l.is_finite(),
                    "data_adds": sample.0, "key_schedule_adds": sample.1,
                    "const_adds": sample.2, "flags": sample.3,
                    "gammas_tried": tried,
                    "estimate_only": true,
                }),
                stopped,
            )
        })
    }
}

/// `arx::rotational::rx_chain` for each single-bit block difference at
/// `gamma = 1` with zero key difference (the best estimate is then measured
/// with `empirical_rx` over 2^14 random pairs). The estimate follows one
/// trajectory and is a lower bound on the probability of the predicted
/// output difference; the measured probability is reported next to it.
pub struct ArxRxTechnique;

impl Technique for ArxRxTechnique {
    fn id(&self) -> TechniqueId {
        TechniqueId::ArxRx
    }
    fn title(&self) -> String {
        "Rotational-XOR estimate".into()
    }
    fn run(&self, p: &Primitive, budget: &Budget) -> TechniqueResult {
        let id = self.id();
        guarded(id, p, || {
            let rounds = p.num_rounds();
            let nb = p.block_bits;
            let zero_key = vec![0u64; words_for(p.key_bits.max(1))];
            let positions: Vec<usize> = if nb <= 64 {
                (0..nb).collect()
            } else {
                (0..64).map(|i| i * (nb / 64)).collect()
            };
            let mut best: Option<(usize, f64, Vec<u64>)> = None;
            let mut stopped = false;
            for &b in &positions {
                if budget.wall_expired() {
                    stopped = true;
                    break;
                }
                let d = bit_vector(nb, &[b]);
                let c = rx_chain(p, rounds, 1, &d, &zero_key);
                if !c.supported {
                    return unsupported(id, p, "operations outside the RX model");
                }
                if best.as_ref().is_none_or(|(_, l, _)| c.log2_prob > *l) {
                    best = Some((b, c.log2_prob, c.out_delta));
                }
            }
            let Some((bit, l, out)) = best else {
                return unsupported(id, p, "no input difference tried");
            };
            let samples = 1u64 << 14;
            // Measurable only when the expected number of hits is at least
            // 2^RX_MIN_HIT_BITS: estimate >= -log2(samples) + that margin.
            let floor = RX_MIN_HIT_BITS - (samples as f64).log2();
            if stopped {
                return exhausted(
                    id,
                    p,
                    "wall clock expired before every difference was tried",
                );
            }
            if !l.is_finite() || l < floor {
                let est = if l.is_finite() {
                    format!("2^{l:.0}")
                } else {
                    "0".to_string()
                };
                return result(
                    id,
                    p,
                    Cost::default(),
                    json!({
                        "status": "not_found",
                        "reason": format!(
                            "estimate {est} below measurable range at N={samples} samples \
                             (measurable from 2^{floor:.0})"
                        ),
                        "rounds": rounds,
                        "gamma": 1,
                        "best_in_bit": bit,
                        "log2_prob_estimate": if l.is_finite() { json!(l) } else { Value::Null },
                        "measurable_floor_log2": floor,
                        "samples": samples,
                        "differences_tried": positions.len(),
                        "estimate_only": true,
                    }),
                    false,
                );
            }
            let m = empirical_rx(
                p,
                rounds,
                1,
                &bit_vector(nb, &[bit]),
                &zero_key,
                &out,
                samples,
                0x77,
            );
            let (pe, n) = (l.exp2(), m.samples as f64);
            let z_vs_estimate = (m.ones as f64 - n * pe) / (n * pe * (1.0 - pe)).sqrt();
            let evals = 2 * samples;
            result(
                id,
                p,
                Cost {
                    data: evals,
                    time_evals: evals,
                    memory: 0,
                },
                json!({
                    "status": "ok",
                    "rounds": rounds,
                    "gamma": 1,
                    "best_in_bit": bit,
                    "log2_prob_estimate": l,
                    "measured_p": m.p1,
                    "measured_hits": m.ones,
                    "measured_samples": m.samples,
                    "z_vs_estimate": z_vs_estimate,
                    "measurable_floor_log2": floor,
                    "differences_tried": positions.len(),
                    "estimate_only": true,
                }),
                false,
            )
        })
    }
}

/// Bits of margin above one expected hit that an RX estimate needs before
/// the panel measures it (expected hits at least `2^RX_MIN_HIT_BITS`).
const RX_MIN_HIT_BITS: f64 = 4.0;

// ── Hash ────────────────────────────────────────────────────────────────

fn params_of(f: Sha2Family) -> Option<Sha2Params> {
    match f {
        Sha2Family::Sha256 => Some(Sha2Params::sha256()),
        Sha2Family::Sha512 => Some(Sha2Params::sha512()),
        Sha2Family::Md5 => None,
    }
}

/// Fewest steps a SHA-2 local collision spans.
pub const LOCAL_COLLISION_MIN_STEPS: usize = 9;

/// `hash::semi_free_start::sfs_by_local_collision` for SHA-2 steps (as
/// recognised by [`sha2_family`]): a semi-free-start collision over all the
/// primitive's steps from a local collision with message-schedule placement,
/// re-checked by evaluating the IR on both messages. Reports `not_found`
/// with the longest reachable placement when the step count is beyond what
/// placement reaches, and `unsupported` below nine steps.
pub struct HashLocalCollisionTechnique;

impl Technique for HashLocalCollisionTechnique {
    fn id(&self) -> TechniqueId {
        TechniqueId::HashLocalCollision
    }
    fn title(&self) -> String {
        "SHA-2 local collision".into()
    }
    fn run(&self, p: &Primitive, budget: &Budget) -> TechniqueResult {
        let id = self.id();
        guarded(id, p, || {
            let Some(params) = sha2_family(p).and_then(params_of) else {
                return unsupported(id, p, "not a SHA-2 step-reduced compression function");
            };
            let n = p.num_rounds();
            if n < LOCAL_COLLISION_MIN_STEPS {
                return unsupported(id, p, "fewer than 9 steps: no local collision fits");
            }
            if budget.wall_expired() {
                return exhausted(id, p, "wall clock expired before start");
            }
            let (start, max_steps) = best_placement(&params);
            match sfs_by_local_collision(&params, n, 0x10CA1) {
                Some(c) => {
                    let ok = verify_sfs(&params, &c);
                    result(
                        id,
                        p,
                        Cost {
                            data: 0,
                            time_evals: 2,
                            memory: 0,
                        },
                        json!({
                            "status": if ok { "ok" } else { "error" },
                            "collision_found": ok,
                            "steps": c.steps,
                            "method": c.method,
                            "verified_by_ir_eval": ok,
                            "best_placement_start": start,
                            "best_placement_max_steps": max_steps,
                        }),
                        false,
                    )
                }
                None => result(
                    id,
                    p,
                    Cost::default(),
                    json!({
                        "status": "not_found",
                        "collision_found": false,
                        "steps": n,
                        "best_placement_start": start,
                        "best_placement_max_steps": max_steps,
                    }),
                    false,
                ),
            }
        })
    }
}

fn truncate_state(state: &mut [u8], bits: u32) {
    let bytes = (bits as usize).div_ceil(8);
    if bytes > 0 && !bits.is_multiple_of(8) {
        state[bytes - 1] &= 0xFFu8 >> (8 - bits % 8);
    }
    state[bytes..].fill(0);
}

/// Generic Merkle-Damgard attacks (`hash::md_adaptor::IrMdHash` with
/// `hash_attacks`) on the SHA-256, SHA-512 or MD5 step function recognised
/// by [`sha2_family`], used as a hash with the family's IV and padding:
/// length extension (checked against the direct hash), a 3-block Joux chain
/// at 16-bit truncated state (replayed over all 8 paths) and a 24-bit
/// truncated birthday collision (at most 2^17 trials, so the cost is an
/// upper bound).
pub struct HashMdGenericTechnique;

impl Technique for HashMdGenericTechnique {
    fn id(&self) -> TechniqueId {
        TechniqueId::HashMdGeneric
    }
    fn title(&self) -> String {
        "Generic Merkle-Damgard attacks".into()
    }
    fn run(&self, p: &Primitive, budget: &Budget) -> TechniqueResult {
        let id = self.id();
        guarded(id, p, || {
            let Some(fam) = sha2_family(p) else {
                return unsupported(id, p, "not a recognised MD compression function");
            };
            if budget.wall_expired() {
                return exhausted(id, p, "wall clock expired before start");
            }
            let base = match fam {
                Sha2Family::Sha256 => IrMdHash::sha256(),
                Sha2Family::Sha512 => IrMdHash::sha512(),
                Sha2Family::Md5 => IrMdHash::md5(),
            };
            let h = base.with_primitive("IR MD hash (panel)", p.clone());
            // Length extension.
            let (secret, msg, suffix) = (b"panel-secret-16".to_vec(), b"data".to_vec(), b"&x=1");
            let mut full = secret.clone();
            full.extend_from_slice(&msg);
            let digest = h.hash(&full);
            let (forged, glue) = length_extension_attack(&h, &digest, full.len(), suffix);
            let mut direct = full.clone();
            direct.extend_from_slice(&glue);
            direct.extend_from_slice(suffix);
            let le_ok = forged == h.hash(&direct);
            // Joux multicollision on a 16-bit reduced state.
            let t = 3usize;
            let joux = joux_multicollision(&h, 16, t, 1 << 12, 0x30);
            let joux_ok = joux.as_ref().map(|chain| {
                let mut finals = std::collections::BTreeSet::new();
                for mask in 0..1u32 << t {
                    let mut st = h.hash(&[])[..h.state_bytes()].to_vec();
                    truncate_state(&mut st, 16);
                    for (i, (a, b)) in chain.iter().enumerate() {
                        h.compress(&mut st, if mask >> i & 1 == 0 { a } else { b });
                        truncate_state(&mut st, 16);
                    }
                    finals.insert(st);
                }
                finals.len() == 1
            });
            // Truncated birthday.
            let trials = 1usize << 17;
            let bday = birthday_collision_search(&h, 24, trials, 0x31);
            let bday_ok = bday.as_ref().map(|(m1, m2, d)| {
                let mut a = h.hash(m1);
                a.truncate(d.len());
                let mut b = h.hash(m2);
                b.truncate(d.len());
                m1 != m2 && a == b
            });
            let evals = 8 + (1u64 << 12) * t as u64 + 2 * trials as u64;
            let all = le_ok && joux_ok == Some(true) && bday_ok == Some(true);
            result(
                id,
                p,
                Cost {
                    data: 0,
                    time_evals: evals,
                    memory: trials as u64 * 24,
                },
                json!({
                    "status": if all { "ok" } else { "not_found" },
                    "family": format!("{fam:?}"),
                    "length_extension_verified": le_ok,
                    "joux_chain_length": joux.as_ref().map(|c| c.len()),
                    "joux_replay_single_final_state": joux_ok,
                    "birthday_24bit_found": bday.is_some(),
                    "birthday_24bit_verified": bday_ok,
                    "cost_is_upper_bound": true,
                }),
                false,
            )
        })
    }
}

/// The panel's work-package techniques, in report order.
pub fn wp_techniques() -> Vec<Box<dyn Technique>> {
    vec![
        Box::new(TrailSearchTechnique::differential()),
        Box::new(TrailSearchTechnique::linear()),
        Box::new(SolverTrailTechnique::milp()),
        Box::new(SolverTrailTechnique::sat()),
        Box::new(DivisionPropertyTechnique),
        Box::new(MissInTheMiddleTechnique::impossible()),
        Box::new(MissInTheMiddleTechnique::zero_correlation()),
        Box::new(DeltaSetTechnique),
        Box::new(ArxDiffLinearTechnique),
        Box::new(ArxPnbTechnique),
        Box::new(ArxRotationalTechnique),
        Box::new(ArxRxTechnique),
        Box::new(HashLocalCollisionTechnique),
        Box::new(HashMdGenericTechnique),
    ]
}
