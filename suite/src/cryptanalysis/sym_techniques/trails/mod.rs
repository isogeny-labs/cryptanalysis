//! Minimum-active-S-box trail search over a [`Primitive`].
//!
//! A *trail model* ([`TrailModel`]) is read off the IR: the first `n` rounds
//! are cut into *stages*, one per [`Layer::SboxParallel`], and everything
//! between two consecutive S-box layers (`Permute`, `LinearGf2`; key and
//! constant additions do not move differences or masks) is composed into one
//! GF(2)-linear map. For differential trails the map carries S-box output
//! differences to the next S-box input differences; for linear trails the
//! mask flows through the inverse transpose `M^{-T}`, so one search engine
//! serves both directions ([`Direction`]).
//!
//! Two exact engines are provided; both minimise the number of active S-boxes
//! and return the per-stage active pattern.
//!
//! * **Value level** ([`Engine::Value`]): explicit difference (mask) vectors,
//!   S-box transitions taken from the DDT (LAT) support, Matsui-style
//!   round-by-round branch and bound (M. Matsui, "On correlation between the
//!   order of S-boxes and the strength of DES", EUROCRYPT 1994): the best
//!   known suffix bound `best[s]` of every stage prunes, and the bound is
//!   found by iterative deepening on the threshold. For S-boxes of width at
//!   most 4 it also yields the best concrete trail (probability or
//!   correlation, [`best_concrete_trail`]). Practical up to 6-bit S-boxes and
//!   128 state bits.
//! * **Word level** ([`Engine::Word`]): the *truncated* model for wide
//!   S-boxes (AES). Each state word is active or not; the linear layer is
//!   split into connected components and for every component the exact set
//!   of feasible `(input pattern, output pattern)` pairs is derived by GF(2)
//!   linear algebra ([`WordComp`]), which for a maximum-distance-separable
//!   column is the branch-number condition of the wide-trail strategy
//!   (J. Daemen, V. Rijmen, *The Design of Rijndael*, 2002). The search is a
//!   Matsui-style branch and bound over stages that memoises the exact
//!   optimum of every suffix pattern and prunes child enumeration with the
//!   per-round bounds and the incumbent. The 8-bit DDT is never enumerated.
//!   The word model is a *relaxation* of the value model (every real trail
//!   is a model trail), so its optimum is a valid lower bound that equals the
//!   true minimum when the component relations are tight, as for AES.
//!   AES is run by this engine only: the value engine rejects S-boxes wider
//!   than 6 bits, and [`Engine::Auto`] picks the word engine. The word SAT
//!   and word MILP encodings ([`sat`], [`milp`]) read the same
//!   [`word_components`] table, so for AES the three solvers share one model
//!   and are not independent derivations. Exactness for AES follows from
//!   MixColumns being GF(2^8)-linear and MDS: a column pattern is feasible
//!   iff `|P| + |Q| >= 5`.
//!
//! Encodings of the same model for MILP (A. Mouha, Q. Wang, D. Gu, B.
//! Preneel, "Differential and linear cryptanalysis using mixed-integer linear
//! programming", Inscrypt 2011) and SAT are in [`milp`] and [`sat`].
//!
//! Restrictions: every S-box layer must cover the whole state starting at bit
//! 0, S-boxes must be bijective, and linear layers must be invertible.
//! `Arx` layers are rejected ([`TrailError::Unsupported`]).

pub mod differential;
pub mod linear;
pub mod milp;
pub mod sat;

use crate::cryptanalysis::sbox::Sbox;
use crate::cryptanalysis::sym_ir::{Gf2Matrix, Layer, Primitive};
use std::fmt;

/// Which kind of trail a [`TrailModel`] describes.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Direction {
    /// Differential trail: differences propagate through `M`.
    Differential,
    /// Linear trail: masks propagate (forwards through the rounds) through
    /// `M^{-T}`.
    Linear,
}

/// Why a trail search could not be run or finished.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum TrailError {
    /// The primitive has a structure the model cannot express.
    Unsupported(String),
    /// A table or enumeration would exceed the supported size.
    TooLarge(String),
    /// The node or conflict budget ran out before the search finished.
    BudgetExceeded,
}

impl fmt::Display for TrailError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            TrailError::Unsupported(s) => write!(f, "unsupported: {s}"),
            TrailError::TooLarge(s) => write!(f, "too large: {s}"),
            TrailError::BudgetExceeded => write!(f, "budget exceeded"),
        }
    }
}

impl std::error::Error for TrailError {}

/// One S-box layer together with the linear map feeding it.
#[derive(Clone, Debug)]
pub struct Stage {
    /// The S-box applied `count` times.
    pub sbox: Sbox,
    /// S-box width in bits.
    pub width: usize,
    /// Number of parallel S-boxes; `width * count` is the state width.
    pub count: usize,
    /// Linear map from the previous stage's S-box output (difference or
    /// mask) to this stage's input; `None` for the first stage.
    pub lin: Option<Gf2Matrix>,
}

/// The structure a trail search runs on, extracted from a [`Primitive`].
#[derive(Clone, Debug)]
pub struct TrailModel {
    /// Name of the primitive the model was read from.
    pub name: String,
    /// Differential or linear.
    pub direction: Direction,
    /// State width in bits.
    pub state_bits: usize,
    /// The S-box stages, in round order.
    pub stages: Vec<Stage>,
}

impl TrailModel {
    /// Extract the model of the first `rounds` rounds of `p`.
    ///
    /// Stages are the S-box layers met in those rounds; the linear layers
    /// between them are composed. Round-key and constant additions are
    /// ignored (they do not change differences or masks). For
    /// [`Direction::Linear`] each inter-stage map is replaced by its inverse
    /// transpose.
    pub fn from_primitive(
        p: &Primitive,
        rounds: usize,
        direction: Direction,
    ) -> Result<Self, TrailError> {
        if rounds == 0 || rounds > p.num_rounds() {
            return Err(TrailError::Unsupported(format!(
                "{}: rounds must be in 1..={}",
                p.name,
                p.num_rounds()
            )));
        }
        let sb = p.state_bits();
        let mut pending: Option<Gf2Matrix> = None;
        let mut stages: Vec<Stage> = Vec::new();
        for r in &p.rounds[..rounds] {
            for l in &r.layers {
                match l {
                    Layer::AddRoundKey { .. } | Layer::AddConst { .. } => {}
                    Layer::Permute { perm } => {
                        let m = Gf2Matrix::from_permutation(perm);
                        pending = Some(match pending.take() {
                            Some(q) => m.mul(&q),
                            None => m,
                        });
                    }
                    Layer::LinearGf2 { matrix } => {
                        pending = Some(match pending.take() {
                            Some(q) => matrix.mul(&q),
                            None => matrix.clone(),
                        });
                    }
                    Layer::Arx { .. } => {
                        return Err(TrailError::Unsupported(format!(
                            "{}: ARX layers are not trail-searchable here",
                            p.name
                        )));
                    }
                    Layer::SboxParallel {
                        sbox,
                        width_bits,
                        count,
                        bit_offset,
                    } => {
                        if *bit_offset != 0 || width_bits * count != sb {
                            return Err(TrailError::Unsupported(format!(
                                "{}: S-box layer does not cover the whole state",
                                p.name
                            )));
                        }
                        let s = p.sboxes[sbox.0].clone();
                        if !s.is_bijective() {
                            return Err(TrailError::Unsupported(format!(
                                "{}: non-bijective S-box",
                                p.name
                            )));
                        }
                        let lin = if stages.is_empty() {
                            pending = None;
                            None
                        } else {
                            let m = pending.take().unwrap_or_else(|| Gf2Matrix::identity(sb));
                            let inv = m.inverse().ok_or_else(|| {
                                TrailError::Unsupported(format!(
                                    "{}: singular linear layer",
                                    p.name
                                ))
                            })?;
                            Some(match direction {
                                Direction::Differential => m,
                                Direction::Linear => inv.transpose(),
                            })
                        };
                        stages.push(Stage {
                            sbox: s,
                            width: *width_bits,
                            count: *count,
                            lin,
                        });
                    }
                }
            }
        }
        if stages.is_empty() {
            return Err(TrailError::Unsupported(format!(
                "{}: no S-box layer in the first {rounds} rounds",
                p.name
            )));
        }
        Ok(TrailModel {
            name: p.name.clone(),
            direction,
            state_bits: sb,
            stages,
        })
    }

    /// Number of S-box stages.
    pub fn num_stages(&self) -> usize {
        self.stages.len()
    }

    /// Largest S-box width over all stages.
    pub fn max_width(&self) -> usize {
        self.stages.iter().map(|s| s.width).max().unwrap_or(0)
    }
}

/// Which search engine to run.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Engine {
    /// [`Engine::Value`] for S-boxes of width at most 4 (and at most 128
    /// state bits), [`Engine::Word`] otherwise.
    Auto,
    /// Explicit-vector Matsui search over the DDT/LAT support.
    Value,
    /// Truncated word-level search.
    Word,
}

/// Options for [`min_active_sboxes`].
#[derive(Clone, Copy, Debug)]
pub struct SearchOptions {
    /// Engine choice.
    pub engine: Engine,
    /// Upper limit on search nodes (value engine) before
    /// [`TrailError::BudgetExceeded`].
    pub node_budget: u64,
    /// Also compute the best concrete trail when all S-boxes have width at
    /// most 4 (a second, probability-weighted search with the same budget).
    pub with_concrete: bool,
}

impl Default for SearchOptions {
    fn default() -> Self {
        SearchOptions {
            engine: Engine::Auto,
            node_budget: 2_000_000_000,
            with_concrete: false,
        }
    }
}

/// A concrete trail: explicit differences (or masks) per stage.
#[derive(Clone, Debug, PartialEq)]
pub struct ConcreteTrail {
    /// `-log2` of the trail probability (differential) or of the absolute
    /// correlation (linear). The linear bias is `2^-(weight + 1)`.
    pub weight: f64,
    /// Per stage, the S-box layer input difference or mask; bit `i` of the
    /// state is bit `i` of the integer.
    pub inputs: Vec<u128>,
    /// Per stage, the S-box layer output difference or mask.
    pub outputs: Vec<u128>,
}

/// Result of a minimum-active-S-box search.
#[derive(Clone, Debug)]
pub struct ActiveSboxResult {
    /// Number of S-box stages searched.
    pub stages: usize,
    /// Minimum number of active S-boxes over all stages (a lower bound when
    /// `exact` is false).
    pub min_active: u32,
    /// `best_by_rounds[r - 1]` is the minimum over `r` consecutive stages
    /// ending at the last stage (the exact suffix bounds the search used);
    /// `best_by_rounds[stages - 1] == min_active`.
    pub best_by_rounds: Vec<u32>,
    /// Per stage, the indices of the active S-boxes in one optimal trail.
    pub pattern: Vec<Vec<usize>>,
    /// Engine that produced the result.
    pub engine: Engine,
    /// True when the model is exact for the primitive (value engine); false
    /// for the word-level relaxation.
    pub exact: bool,
    /// Search nodes visited (value engine) or pattern-table entries filled
    /// (word engine).
    pub nodes: u64,
    /// Best concrete trail, if requested and available (S-box width at most
    /// 4, value engine).
    pub concrete: Option<ConcreteTrail>,
    /// True when `with_concrete` was requested, the S-boxes qualify, and the
    /// concrete-trail search ran out of `node_budget`: `concrete` is then
    /// `None` because the search was cut off, not because no trail exists.
    /// The active-S-box numbers are unaffected (they come from a separate,
    /// completed search).
    pub concrete_budget_exceeded: bool,
}

// ── S-box transition tables ──────────────────────────────────────────────

/// Possible (input, output) transitions of one S-box for a direction, with
/// weights `-log2(probability or |correlation|)`, per nonzero input.
#[derive(Clone, Debug)]
struct SboxTransitions {
    /// `next[a]` for `a >= 1`: `(b, weight)` sorted by ascending weight.
    next: Vec<Vec<(u32, f64)>>,
    min_weight: f64,
}

impl SboxTransitions {
    fn new(sbox: &Sbox, dir: Direction) -> Self {
        let n = sbox.n_in() as usize;
        let size = 1usize << n;
        let mut next = vec![Vec::new(); size];
        match dir {
            Direction::Differential => {
                let ddt = sbox.ddt();
                for (a, row) in ddt.iter().enumerate().skip(1) {
                    for (b, &c) in row.iter().enumerate() {
                        if c > 0 {
                            next[a].push((b as u32, n as f64 - f64::from(c).log2()));
                        }
                    }
                }
            }
            Direction::Linear => {
                let lat = sbox.lat();
                let half = (size / 2) as f64;
                for (a, row) in lat.iter().enumerate().skip(1) {
                    for (b, &c) in row.iter().enumerate() {
                        if c != 0 {
                            next[a].push((b as u32, -(f64::from(c.abs()) / half).log2()));
                        }
                    }
                }
            }
        }
        let mut min_weight = f64::INFINITY;
        for v in next.iter_mut() {
            v.sort_by(|x, y| x.1.partial_cmp(&y.1).unwrap());
            if let Some(f) = v.first() {
                min_weight = min_weight.min(f.1);
            }
        }
        SboxTransitions { next, min_weight }
    }
}

// ── Value-level engine ───────────────────────────────────────────────────

struct ValueStage {
    width: usize,
    count: usize,
    trans: SboxTransitions,
    /// `cols[j]` = image of unit vector `e_j` under the stage's `lin`.
    cols: Option<Vec<u128>>,
    /// Whether `lin` is a bit permutation (then the image of a partial
    /// output already fixes the active fields of the next stage).
    perm: bool,
}

struct ValueModel {
    stages: Vec<ValueStage>,
}

impl ValueModel {
    fn new(m: &TrailModel) -> Result<Self, TrailError> {
        if m.state_bits > 128 {
            return Err(TrailError::TooLarge(format!(
                "value engine needs at most 128 state bits, got {}",
                m.state_bits
            )));
        }
        if m.max_width() > 6 {
            return Err(TrailError::TooLarge(format!(
                "value engine needs S-box width <= 6, got {}",
                m.max_width()
            )));
        }
        let stages = m
            .stages
            .iter()
            .map(|s| ValueStage {
                width: s.width,
                count: s.count,
                trans: SboxTransitions::new(&s.sbox, m.direction),
                perm: s.lin.as_ref().is_some_and(|l| l.as_permutation().is_some()),
                cols: s.lin.as_ref().map(|l| {
                    (0..m.state_bits)
                        .map(|j| {
                            let mut c = 0u128;
                            for i in 0..m.state_bits {
                                if l.get(i, j) {
                                    c |= 1u128 << i;
                                }
                            }
                            c
                        })
                        .collect()
                }),
            })
            .collect();
        Ok(ValueModel { stages })
    }

    fn apply(&self, s: usize, mut x: u128) -> u128 {
        let cols = self.stages[s].cols.as_ref().expect("stage has no lin");
        let mut out = 0u128;
        while x != 0 {
            let j = x.trailing_zeros() as usize;
            out ^= cols[j];
            x &= x - 1;
        }
        out
    }
}

const EPS: f64 = 1e-9;

struct Dfs<'a> {
    vm: &'a ValueModel,
    start: usize,
    limit: f64,
    best: &'a [f64],
    weighted: bool,
    nodes: u64,
    budget: u64,
    aborted: bool,
    ins: Vec<u128>,
    outs: Vec<u128>,
    found: Option<(f64, Vec<u128>, Vec<u128>)>,
}

impl Dfs<'_> {
    fn minc(&self, s: usize) -> f64 {
        if self.weighted {
            self.vm.stages[s].trans.min_weight
        } else {
            1.0
        }
    }

    fn record(&mut self, cost: f64) {
        self.found = Some((
            cost,
            self.ins[self.start..].to_vec(),
            self.outs[self.start..].to_vec(),
        ));
        if self.weighted {
            self.limit = cost - 1e-7;
        }
    }

    /// Enter stage `s` with nonzero input `input`; `cost` is the cost of the
    /// earlier stages. Returns true to stop the whole search.
    fn stage(&mut self, s: usize, input: u128, cost: f64) -> bool {
        self.nodes += 1;
        if self.nodes > self.budget {
            self.aborted = true;
            return true;
        }
        let vm = self.vm;
        let st = &vm.stages[s];
        let mask = (1u128 << st.width) - 1;
        let act: Vec<(usize, u32)> = (0..st.count)
            .filter_map(|j| {
                let a = ((input >> (j * st.width)) & mask) as u32;
                (a != 0).then_some((j, a))
            })
            .collect();
        debug_assert!(!act.is_empty());
        let minc = self.minc(s);
        if cost + act.len() as f64 * minc + self.best[s + 1] > self.limit + EPS {
            return false;
        }
        self.ins[s] = input;
        self.outputs(s, &act, 0, 0, cost)
    }

    fn outputs(&mut self, s: usize, act: &[(usize, u32)], k: usize, out: u128, acc: f64) -> bool {
        let vm = self.vm;
        let st = &vm.stages[s];
        if k == act.len() {
            self.outs[s] = out;
            if s + 1 == vm.stages.len() {
                self.record(acc);
                return !self.weighted;
            }
            let next = vm.apply(s + 1, out);
            return self.stage(s + 1, next, acc);
        }
        let minc = self.minc(s);
        let rest = (act.len() - k - 1) as f64 * minc;
        let (j, a) = act[k];
        let last = s + 1 == vm.stages.len();
        for &(b, w) in &st.trans.next[a as usize] {
            let c = if self.weighted { w } else { 1.0 };
            let out2 = out | (u128::from(b) << (j * st.width));
            let mut tail = self.best[s + 1];
            // Transitions are sorted by weight, so this bound is monotone
            // along the list and ends the loop.
            if acc + c + rest + tail > self.limit + EPS {
                break;
            }
            if !last && vm.stages[s + 1].perm {
                // The next stage has at least as many active S-boxes as
                // fields already touched by the chosen outputs.
                let nx = &vm.stages[s + 1];
                let mask = (1u128 << nx.width) - 1;
                let img = vm.apply(s + 1, out2);
                let touched = (0..nx.count)
                    .filter(|&f| (img >> (f * nx.width)) & mask != 0)
                    .count() as f64;
                let mc = if self.weighted {
                    nx.trans.min_weight
                } else {
                    1.0
                };
                tail = tail.max(touched * mc + self.best[s + 2]);
            }
            if acc + c + rest + tail > self.limit + EPS {
                continue;
            }
            if self.outputs(s, act, k + 1, out2, acc + c) {
                return true;
            }
        }
        false
    }

    /// Enumerate every nonzero first-stage input with few enough active
    /// S-boxes, each exactly once.
    fn first(&mut self, pos: usize, used: usize, input: u128) -> bool {
        let st = &self.vm.stages[self.start];
        let (w, count) = (st.width, st.count);
        let minc = self.minc(self.start);
        let room = self.limit + EPS - self.best[self.start + 1];
        let amax = if room < minc {
            0
        } else {
            (room / minc).floor() as usize
        };
        if used >= amax {
            return false;
        }
        for j in pos..count {
            for a in 1..(1u128 << w) {
                let inp = input | (a << (j * w));
                if self.stage(self.start, inp, 0.0) {
                    return true;
                }
                if used + 1 < amax && self.first(j + 1, used + 1, inp) {
                    return true;
                }
            }
        }
        false
    }
}

struct ValueOutcome {
    best: Vec<f64>,
    trail: Option<(f64, Vec<u128>, Vec<u128>)>,
    nodes: u64,
}

/// Iterative-deepening Matsui search; `best[s]` becomes the exact optimum of
/// the suffix starting at stage `s`.
fn value_search(
    vm: &ValueModel,
    weighted: bool,
    budget: u64,
    start_stage_min: usize,
) -> Result<ValueOutcome, TrailError> {
    let n = vm.stages.len();
    let mut best = vec![0.0f64; n + 1];
    let mut nodes = 0u64;
    let mut final_trail = None;
    for s in (start_stage_min..n).rev() {
        let minc = if weighted {
            vm.stages[s].trans.min_weight
        } else {
            1.0
        };
        let mut limit = best[s + 1] + minc;
        loop {
            let mut d = Dfs {
                vm,
                start: s,
                limit,
                best: &best,
                weighted,
                nodes: 0,
                budget: budget.saturating_sub(nodes),
                aborted: false,
                ins: vec![0; n],
                outs: vec![0; n],
                found: None,
            };
            d.first(0, 0, 0);
            nodes += d.nodes;
            if d.aborted {
                return Err(TrailError::BudgetExceeded);
            }
            if let Some(f) = d.found {
                best[s] = f.0;
                if s == start_stage_min {
                    final_trail = Some(f);
                }
                break;
            }
            limit += 1.0;
            if limit > 1.0e4 {
                return Err(TrailError::BudgetExceeded);
            }
        }
    }
    Ok(ValueOutcome {
        best,
        trail: final_trail,
        nodes,
    })
}

fn concrete_from(model: &TrailModel, t: (f64, Vec<u128>, Vec<u128>)) -> ConcreteTrail {
    let _ = model;
    ConcreteTrail {
        weight: t.0,
        inputs: t.1,
        outputs: t.2,
    }
}

/// Best concrete trail (maximum probability for a differential model,
/// maximum absolute correlation for a linear one) over all stages of the
/// model, by weighted Matsui branch and bound. Needs S-box width at most 6
/// for tractability; the intended use is width at most 4.
pub fn best_concrete_trail(
    model: &TrailModel,
    node_budget: u64,
) -> Result<ConcreteTrail, TrailError> {
    let vm = ValueModel::new(model)?;
    let o = value_search(&vm, true, node_budget, 0)?;
    Ok(concrete_from(model, o.trail.expect("search found a trail")))
}

// ── Word-level engine ────────────────────────────────────────────────────

/// One connected component of the word-level bipartite graph of a linear
/// layer: the previous stage's output words `out_words`, the next stage's
/// input words `in_words`, and the set of feasible activity patterns.
///
/// A pair `(P, Q)` of local activity masks (bit `i` of `P` for
/// `out_words[i]`, bit `i` of `Q` for `in_words[i]`) is *feasible* iff
/// `P = Q = 0`, or some nonzero vector supported on the words of `P` is
/// mapped by the layer to a vector supported on the words of `Q`. This
/// contains every pattern pair of a real trail. For an MDS column it is
/// exactly `|P| + |Q| >= 5` (AES).
#[derive(Clone, Debug)]
pub struct WordComp {
    /// Word positions in the previous stage (inputs of the linear layer).
    pub out_words: Vec<usize>,
    /// Word positions in the next stage (outputs of the linear layer).
    pub in_words: Vec<usize>,
    allowed: Vec<bool>,
}

impl WordComp {
    /// Number of previous-stage words in the component.
    pub fn p(&self) -> usize {
        self.out_words.len()
    }

    /// Number of next-stage words in the component.
    pub fn q(&self) -> usize {
        self.in_words.len()
    }

    /// Whether the local patterns `(pmask, qmask)` are feasible.
    pub fn is_allowed(&self, pmask: u32, qmask: u32) -> bool {
        self.allowed[(pmask | (qmask << self.p())) as usize]
    }

    /// If the nonempty feasible pairs are exactly those with
    /// `|P| + |Q| >= b`, return `b` (the branch number of the component).
    pub fn threshold(&self) -> Option<usize> {
        let mut b = usize::MAX;
        for (m, &ok) in self.allowed.iter().enumerate().skip(1) {
            if ok {
                b = b.min(m.count_ones() as usize);
            }
        }
        if b == usize::MAX {
            return None;
        }
        for (m, &ok) in self.allowed.iter().enumerate().skip(1) {
            if ok != (m.count_ones() as usize >= b) {
                return None;
            }
        }
        Some(b)
    }

    /// Maximal infeasible nonzero combined masks (`P | Q << p`): every
    /// nonzero activity assignment that is a subset of one of them is
    /// infeasible and every other nonzero assignment is feasible.
    pub fn maximal_forbidden(&self) -> Vec<u32> {
        let total = self.p() + self.q();
        let mut out = Vec::new();
        for m in 1..(1u32 << total) {
            if self.allowed[m as usize] {
                continue;
            }
            let maximal = (0..total).all(|i| {
                let m2 = m | (1 << i);
                m2 == m || self.allowed[m2 as usize]
            });
            if maximal {
                out.push(m);
            }
        }
        out
    }
}

/// Largest component size (`p + q`) the word model will tabulate.
const MAX_COMP_BITS: usize = 22;

/// The components of the linear layer feeding `cur` (whose `lin` must be
/// set) from `prev`, with their feasible pattern pairs.
pub fn word_components(prev: &Stage, cur: &Stage) -> Result<Vec<WordComp>, TrailError> {
    let m = cur
        .lin
        .as_ref()
        .ok_or_else(|| TrailError::Unsupported("first stage has no incoming layer".into()))?;
    let (cp, cc, wp, wc) = (prev.count, cur.count, prev.width, cur.width);
    let mut parent: Vec<usize> = (0..cp + cc).collect();
    fn find(p: &mut [usize], mut x: usize) -> usize {
        while p[x] != x {
            p[x] = p[p[x]];
            x = p[x];
        }
        x
    }
    for k in 0..cc {
        for i in 0..wc {
            for j in 0..cp {
                for b in 0..wp {
                    if m.get(k * wc + i, j * wp + b) {
                        let (a, c) = (find(&mut parent, j), find(&mut parent, cp + k));
                        parent[a] = c;
                    }
                }
            }
        }
    }
    let mut groups: Vec<(usize, Vec<usize>, Vec<usize>)> = Vec::new();
    for v in 0..cp + cc {
        let r = find(&mut parent, v);
        let gi = match groups.iter().position(|g| g.0 == r) {
            Some(i) => i,
            None => {
                groups.push((r, vec![], vec![]));
                groups.len() - 1
            }
        };
        if v < cp {
            groups[gi].1.push(v);
        } else {
            groups[gi].2.push(v - cp);
        }
    }
    let mut comps = Vec::new();
    for (_, outs, ins) in groups {
        let (p, q) = (outs.len(), ins.len());
        if p + q > MAX_COMP_BITS {
            return Err(TrailError::TooLarge(format!(
                "word component with {} words",
                p + q
            )));
        }
        let (outs_r, ins_r) = (&outs, &ins);
        let mut allowed = vec![false; 1 << (p + q)];
        for (mask, slot) in allowed.iter_mut().enumerate() {
            let pm = mask & ((1 << p) - 1);
            let qm = mask >> p;
            *slot = if mask == 0 {
                true
            } else {
                let cols: Vec<usize> = (0..p)
                    .filter(|i| pm >> i & 1 == 1)
                    .flat_map(|i| (0..wp).map(move |b| outs_r[i] * wp + b))
                    .collect();
                let rows: Vec<usize> = (0..q)
                    .filter(|i| qm >> i & 1 == 0)
                    .flat_map(|i| (0..wc).map(move |b| ins_r[i] * wc + b))
                    .collect();
                if cols.is_empty() {
                    false
                } else if rows.is_empty() {
                    true
                } else {
                    let mut sub = Gf2Matrix::zero(rows.len(), cols.len());
                    for (ri, &r) in rows.iter().enumerate() {
                        for (ci, &c) in cols.iter().enumerate() {
                            if m.get(r, c) {
                                sub.set(ri, ci, true);
                            }
                        }
                    }
                    sub.rank() < cols.len()
                }
            };
        }
        comps.push(WordComp {
            out_words: outs,
            in_words: ins,
            allowed,
        });
    }
    Ok(comps)
}

struct CompTables {
    out_words: Vec<usize>,
    /// `children[pmask]`: feasible local `Q` masks sorted by popcount.
    children: Vec<Vec<u32>>,
    /// `qmap[qmask]`: the global next-stage word mask.
    qmap: Vec<u64>,
}

impl CompTables {
    fn new(c: &WordComp) -> Self {
        let (p, q) = (c.p(), c.q());
        let mut children = vec![Vec::new(); 1 << p];
        for (pm, ch) in children.iter_mut().enumerate() {
            for qm in 0..(1u32 << q) {
                if c.is_allowed(pm as u32, qm) {
                    ch.push(qm);
                }
            }
            ch.sort_by_key(|x| x.count_ones());
        }
        let qmap = (0..1u32 << q)
            .map(|qm| {
                (0..q)
                    .filter(|i| qm >> i & 1 == 1)
                    .fold(0u64, |a, i| a | 1u64 << c.in_words[i])
            })
            .collect();
        CompTables {
            out_words: c.out_words.clone(),
            children,
            qmap,
        }
    }
}

struct ChildEnum<'a> {
    comps: &'a [CompTables],
    plocal: &'a [usize],
    minrest: &'a [u32],
    next_cost: &'a [u32],
    lb_after: u32,
    best: u32,
    arg: u64,
}

impl ChildEnum<'_> {
    fn rec(&mut self, c: usize, mask: u64, pop: u32) {
        if c == self.comps.len() {
            let v = self.next_cost[mask as usize];
            if v < self.best {
                self.best = v;
                self.arg = mask;
            }
            return;
        }
        if pop + self.minrest[c] + self.lb_after >= self.best {
            return;
        }
        let ct = &self.comps[c];
        for &q in &ct.children[self.plocal[c]] {
            let pc = q.count_ones();
            if pop + pc + self.minrest[c + 1] + self.lb_after >= self.best {
                break;
            }
            self.rec(c + 1, mask | ct.qmap[q as usize], pop + pc);
        }
    }
}

struct WordOutcome {
    best: Vec<u32>,
    chain: Vec<u64>,
    nodes: u64,
}

const INF32: u32 = u32::MAX / 4;

fn word_search(model: &TrailModel) -> Result<WordOutcome, TrailError> {
    let n = model.stages.len();
    for s in &model.stages {
        if s.count > MAX_COMP_BITS {
            return Err(TrailError::TooLarge(format!(
                "{} words per stage exceeds the pattern table limit",
                s.count
            )));
        }
    }
    let comps: Vec<Vec<CompTables>> = (1..n)
        .map(|s| {
            word_components(&model.stages[s - 1], &model.stages[s])
                .map(|v| v.iter().map(CompTables::new).collect())
        })
        .collect::<Result<_, _>>()?;
    let size = |s: usize| 1usize << model.stages[s].count;
    let mut cost: Vec<Vec<u32>> = vec![Vec::new(); n];
    let mut next: Vec<Vec<u64>> = vec![Vec::new(); n];
    let mut gmin = vec![0u32; n + 2];
    cost[n - 1] = (0..size(n - 1))
        .map(|a| if a == 0 { INF32 } else { a.count_ones() })
        .collect();
    gmin[n - 1] = 1;
    let mut nodes = 0u64;
    for s in (0..n.saturating_sub(1)).rev() {
        let ct = &comps[s];
        let mut cs = vec![INF32; size(s)];
        let mut ns = vec![0u64; size(s)];
        let lb_after = gmin[s + 2];
        let mut gm = INF32;
        let mut plocal = vec![0usize; ct.len()];
        let mut minrest = vec![0u32; ct.len() + 1];
        for a in 1..size(s) {
            for (ci, c) in ct.iter().enumerate() {
                plocal[ci] = c
                    .out_words
                    .iter()
                    .enumerate()
                    .fold(0, |acc, (i, &w)| acc | ((a >> w) & 1) << i);
            }
            for ci in (0..ct.len()).rev() {
                let mn = ct[ci].children[plocal[ci]]
                    .first()
                    .map_or(0, |q| q.count_ones());
                minrest[ci] = minrest[ci + 1] + mn;
            }
            let mut ce = ChildEnum {
                comps: ct,
                plocal: &plocal,
                minrest: &minrest,
                next_cost: &cost[s + 1],
                lb_after: if s + 1 == n - 1 { 0 } else { lb_after },
                best: INF32,
                arg: 0,
            };
            ce.rec(0, 0, 0);
            debug_assert!(ce.best < INF32);
            cs[a] = a.count_ones() + ce.best;
            ns[a] = ce.arg;
            gm = gm.min(cs[a]);
            nodes += 1;
        }
        gmin[s] = gm;
        cost[s] = cs;
        next[s] = ns;
    }
    let (a0, _) = (1..size(0))
        .map(|a| (a, cost[0][a]))
        .min_by_key(|x| x.1)
        .expect("nonempty pattern table");
    let mut chain = vec![a0 as u64];
    for s in 0..n - 1 {
        let a = *chain.last().unwrap() as usize;
        chain.push(next[s][a]);
    }
    gmin.truncate(n + 1);
    gmin[n] = 0;
    Ok(WordOutcome {
        best: gmin,
        chain,
        nodes,
    })
}

// ── Shared S-box constraint minimisation ─────────────────────────────────

/// Cubes (partial assignments) that together cover exactly the infeasible
/// `(input, output)` bit patterns of one S-box layer element.
///
/// Bit `i < width` of the pattern is input bit `i`, bit `width + i` is output
/// bit `i` (least significant first). A pair is feasible iff it is
/// `(0, 0)` or lies in the DDT (LAT) support of the direction. Each returned
/// `(care_mask, value)` is a prime implicant of the infeasible set chosen by
/// a greedy cover (Quine-McCluskey); a pattern `m` is excluded by the cube
/// iff `m & care_mask == value`. Used by the SAT and MILP bit-level
/// encodings, where each cube becomes one clause.
pub(crate) fn transition_nogoods(sbox: &Sbox, dir: Direction) -> Vec<(u32, u32)> {
    use std::collections::HashSet;
    let w = sbox.n_in() as usize;
    let t = SboxTransitions::new(sbox, dir);
    let nbits = 2 * w;
    let mut feasible = vec![false; 1 << nbits];
    feasible[0] = true;
    for (a, list) in t.next.iter().enumerate() {
        for &(b, _) in list {
            feasible[a | ((b as usize) << w)] = true;
        }
    }
    let minterms: Vec<u32> = (0..1u32 << nbits)
        .filter(|&m| !feasible[m as usize])
        .collect();
    let full = (1u32 << nbits) - 1;
    let mut cur: HashSet<(u32, u32)> = minterms.iter().map(|&m| (full, m)).collect();
    let mut primes: Vec<(u32, u32)> = Vec::new();
    while !cur.is_empty() {
        let mut next: HashSet<(u32, u32)> = HashSet::new();
        let mut merged: HashSet<(u32, u32)> = HashSet::new();
        for &(mask, val) in &cur {
            for i in 0..nbits {
                if mask >> i & 1 == 1 {
                    let other = (mask, val ^ (1 << i));
                    if cur.contains(&other) {
                        next.insert((mask & !(1 << i), val & !(1 << i)));
                        merged.insert((mask, val));
                        merged.insert(other);
                    }
                }
            }
        }
        primes.extend(cur.iter().filter(|c| !merged.contains(c)));
        cur = next;
    }
    primes.sort_unstable();
    let mut uncovered: Vec<u32> = minterms;
    let mut chosen = Vec::new();
    while !uncovered.is_empty() {
        let (bi, _) = primes
            .iter()
            .enumerate()
            .map(|(i, &(mask, val))| (i, uncovered.iter().filter(|&&m| m & mask == val).count()))
            .max_by_key(|x| x.1)
            .expect("primes cover all minterms");
        let (mask, val) = primes[bi];
        uncovered.retain(|&m| m & mask != val);
        chosen.push((mask, val));
    }
    chosen
}

// ── Public driver ────────────────────────────────────────────────────────

fn pattern_of_value(model: &TrailModel, ins: &[u128]) -> Vec<Vec<usize>> {
    ins.iter()
        .zip(&model.stages)
        .map(|(&x, st)| {
            let mask = (1u128 << st.width) - 1;
            (0..st.count)
                .filter(|&j| (x >> (j * st.width)) & mask != 0)
                .collect()
        })
        .collect()
}

/// Minimum number of active S-boxes of `model`, the per-stage active pattern
/// of one optimal trail, and the exact per-round suffix bounds.
///
/// See the [module documentation](self) for the two engines.
pub fn min_active_sboxes(
    model: &TrailModel,
    opts: &SearchOptions,
) -> Result<ActiveSboxResult, TrailError> {
    let n = model.num_stages();
    let engine = match opts.engine {
        Engine::Auto => {
            if model.max_width() <= 4 && model.state_bits <= 128 {
                Engine::Value
            } else {
                Engine::Word
            }
        }
        e => e,
    };
    match engine {
        Engine::Value | Engine::Auto => {
            let vm = ValueModel::new(model)?;
            let o = value_search(&vm, false, opts.node_budget, 0)?;
            let (_, ins, _) = o.trail.expect("search found a trail");
            let mut concrete_budget_exceeded = false;
            let concrete = if opts.with_concrete && model.max_width() <= 4 {
                match best_concrete_trail(model, opts.node_budget) {
                    Ok(c) => Some(c),
                    Err(TrailError::BudgetExceeded) => {
                        concrete_budget_exceeded = true;
                        None
                    }
                    Err(e) => return Err(e),
                }
            } else {
                None
            };
            Ok(ActiveSboxResult {
                stages: n,
                min_active: o.best[0].round() as u32,
                best_by_rounds: (1..=n).map(|r| o.best[n - r].round() as u32).collect(),
                pattern: pattern_of_value(model, &ins),
                engine: Engine::Value,
                exact: true,
                nodes: o.nodes,
                concrete,
                concrete_budget_exceeded,
            })
        }
        Engine::Word => {
            let o = word_search(model)?;
            let pattern = o
                .chain
                .iter()
                .zip(&model.stages)
                .map(|(&m, st)| (0..st.count).filter(|&j| m >> j & 1 == 1).collect())
                .collect();
            Ok(ActiveSboxResult {
                stages: n,
                min_active: o.best[0],
                best_by_rounds: (1..=n).map(|r| o.best[n - r]).collect(),
                pattern,
                engine: Engine::Word,
                exact: false,
                nodes: o.nodes,
                concrete: None,
                concrete_budget_exceeded: false,
            })
        }
    }
}

#[cfg(test)]
mod tests;
