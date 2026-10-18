//! Measurements of one factor-base cell (spec section 4): construction,
//! yield, the Weil-descent system, F4 and SAT solver costs and the derived
//! expected operation counts.
//!
//! Every value that was not measured is `null` with a sibling `*_reason`;
//! an unmeasured group is `{"measured": false, "reason": ...}`. Nothing here
//! is an `IC1` result: the numbers are stage diagnostics.
//!
//! Conventions fixed by this module:
//! * a point is *usable* when `[h]P != O` (cofactor-projection policy);
//!   `fb_points` counts usable points before folding;
//! * `effective_columns` is the number of distinct projected signed
//!   Frobenius (Koblitz) or sign (other curves) orbits `[h]P`;
//! * yield is the fraction of `<G> \ {O}` that is a sum of `m` usable points
//!   (repeats allowed): exact by sumset enumeration when
//!   `|F|^(m-1) <= exact_cap`, else over `targets` random subgroup points
//!   with a Wilson 95% interval;
//! * the system ranges over the seed subspace `V` (plus shift) of the
//!   recipe, so on a non-invariant Koblitz seed it describes one Frobenius
//!   pattern of the closed base;
//! * the F4 class `planted` has a known decomposition, `random` is a uniform
//!   subgroup point.

use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};
use std::time::{Duration, Instant};

use num_traits::ToPrimitive;
use rand::rngs::StdRng;
use rand::{Rng, SeedableRng};
use serde_json::{json, Map, Value};

use crate::binary_ecc::F2mElement;
use crate::cryptanalysis::ic_boundary::{BinaryGroup, CountedGroup, GroupOps, PrimeInstance};
use crate::cryptanalysis::ic_framework::solvers::solver_by_name;
use crate::cryptanalysis::ic_framework::stages::{BooleanSystem, Params, SolverVerdict};
use crate::cryptanalysis::koblitz_fast::FastPoint;
use crate::cryptanalysis::koblitz_groebner::{
    matrix_f4_f2, solving_degree, sym_semaev_s3, FieldStructure, SymElement, MAX_VARS,
};
use crate::cryptanalysis::pq_groebner_f2::{F2BoolMono, F2BoolPoly};
use crate::cryptanalysis::semaev_sat::{encode_boolean_system_with, XorEncoding};

use super::families::{base_points_binary, span, BasePoints, Ctx, Curve, Materialized};
use super::identity::point_set_sha256;

/// A metric group of spec section 4.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum Group {
    /// Point counts, columns, subspace invariants, digests.
    Construction,
    /// Relation yield at the requested `m`.
    Yield,
    /// Shape of the Weil-descent system.
    System,
    /// F4 / Macaulay solving degree and cost.
    F4,
    /// CDCL cost with native XOR rows.
    Sat,
    /// XL degree (optional; not built in this release).
    Xl,
    /// Expected operation counts.
    Derived,
}

impl Group {
    /// All groups.
    pub const ALL: [Group; 7] = [
        Group::Construction,
        Group::Yield,
        Group::System,
        Group::F4,
        Group::Sat,
        Group::Xl,
        Group::Derived,
    ];

    /// Lowercase name.
    pub fn as_str(self) -> &'static str {
        match self {
            Group::Construction => "construction",
            Group::Yield => "yield",
            Group::System => "system",
            Group::F4 => "f4",
            Group::Sat => "sat",
            Group::Xl => "xl",
            Group::Derived => "derived",
        }
    }

    /// Parse one name.
    pub fn parse(s: &str) -> Result<Group, String> {
        Group::ALL
            .into_iter()
            .find(|g| g.as_str() == s.trim())
            .ok_or_else(|| format!("unknown metric group `{s}`"))
    }

    /// Parse a comma-separated list.
    pub fn parse_list(s: &str) -> Result<BTreeSet<Group>, String> {
        s.split(',')
            .filter(|p| !p.trim().is_empty())
            .map(Group::parse)
            .collect()
    }
}

/// Outcome of a measurement (the `status` of a cell record).
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum Status {
    /// Every requested group was measured or is not applicable.
    Complete,
    /// A cap (exact cap, matrix size, work guard) stopped a group.
    CapsHit,
    /// The wall-clock budget stopped a group.
    Budget,
    /// The base does not apply (set by the sweep for a failed materialization).
    NotApplicable,
    /// A group failed.
    Error,
}

impl Status {
    /// The string stored in a cell record.
    pub fn as_str(self) -> &'static str {
        match self {
            Status::Complete => "complete",
            Status::CapsHit => "caps_hit",
            Status::Budget => "budget",
            Status::NotApplicable => "not_applicable",
            Status::Error => "error",
        }
    }
}

/// What to measure and under which limits.
#[derive(Debug, Clone)]
pub struct MetricRequest {
    /// Groups to measure (construction is always computed).
    pub groups: BTreeSet<Group>,
    /// Summand count, `2..=8`.
    pub m: u32,
    /// Targets per class (yield sample and solver classes).
    pub targets: u32,
    /// Exact yield when `|F|^(m-1)` does not exceed this.
    pub exact_cap: u64,
    /// Wall budget per metric group.
    pub budget: Duration,
    /// SAT conflict budget per target.
    pub conflict_budget: u64,
    /// Highest Macaulay degree tried.
    pub d_max: u32,
    /// System modifiers applied on top of the recipe's own.
    pub system_modifiers: BTreeMap<String, Value>,
}

impl Default for MetricRequest {
    fn default() -> Self {
        Self {
            groups: [Group::Construction, Group::Yield].into_iter().collect(),
            m: 2,
            targets: 8,
            exact_cap: 1 << 24,
            budget: Duration::from_secs(60),
            conflict_budget: 20_000,
            d_max: 6,
            system_modifiers: BTreeMap::new(),
        }
    }
}

/// Worst-status tracker.
struct Tracker {
    status: Status,
    reason: Option<String>,
}

impl Tracker {
    fn note(&mut self, s: Status, why: &str) {
        if s > self.status {
            self.status = s;
            self.reason = Some(why.to_string());
        }
    }
}

fn unmeasured(reason: &str) -> Value {
    json!({"measured": false, "reason": reason})
}

fn hex_pair(p: &FastPoint) -> (String, String) {
    (format!("{:x}", p.x), format!("{:x}", p.y))
}

fn wilson(k: usize, n: usize) -> (f64, f64) {
    if n == 0 {
        return (0.0, 1.0);
    }
    let (n, p, z) = (n as f64, k as f64 / n as f64, 1.959_963_984_540_054);
    let d = 1.0 + z * z / n;
    let centre = (p + z * z / (2.0 * n)) / d;
    let half = z * (p * (1.0 - p) / n + z * z / (4.0 * n * n)).sqrt() / d;
    ((centre - half).max(0.0), (centre + half).min(1.0))
}

fn mulmod(a: u64, b: u64, m: u64) -> u64 {
    (u128::from(a) * u128::from(b) % u128::from(m)) as u64
}

fn powmod(mut a: u64, mut e: u64, m: u64) -> u64 {
    let mut acc = 1 % m;
    while e > 0 {
        if e & 1 == 1 {
            acc = mulmod(acc, a, m);
        }
        a = mulmod(a, a, m);
        e >>= 1;
    }
    acc
}

// ── Yield ──────────────────────────────────────────────────────────

/// A pool of summand candidates: `(point, index into the usable list)`.
type Pool<E> = Vec<(E, usize)>;

struct YieldInput<'a, G: CountedGroup> {
    g: &'a G,
    generator: G::Elt,
    r: u64,
    h: u64,
    usable: &'a [G::Elt],
    loc: &'a [(usize, u32, bool)],
    columns: usize,
    /// Pool of the first summand, as indices into `usable`.
    pool0: Vec<usize>,
    /// Frobenius power `j` applied to a point (identity when absent).
    twist: Option<&'a dyn Fn(G::Elt, u32) -> G::Elt>,
    /// Frobenius eigenvalue on the subgroup.
    lambda: u64,
    /// Extension degree (Frobenius order).
    ext: u32,
    patterns: usize,
    use_pattern_shift: bool,
}

struct YieldOut {
    json: Value,
    coverage: Option<f64>,
    expected: Option<f64>,
    status: Status,
    reason: Option<String>,
}

fn pools_for<G: CountedGroup>(
    inp: &YieldInput<'_, G>,
    idx_of: &HashMap<u64, usize>,
    m: usize,
    pattern: usize,
) -> Vec<Pool<G::Elt>> {
    (0..m)
        .map(|i| {
            let j = if inp.use_pattern_shift {
                ((i * pattern) % inp.ext as usize) as u32
            } else {
                0
            };
            inp.pool0
                .iter()
                .filter_map(|&u| {
                    let p = inp.usable[u];
                    if j == 0 {
                        return Some((p, u));
                    }
                    let q = (inp.twist?)(p, j);
                    idx_of.get(&inp.g.key(&q)).map(|&ix| (q, ix))
                })
                .collect()
        })
        .collect()
}

type PairTable = HashMap<u64, Vec<(u32, u32)>>;

fn pair_table<G: CountedGroup>(g: &G, a: &Pool<G::Elt>, b: &Pool<G::Elt>) -> PairTable {
    let mut ops = GroupOps::default();
    let mut t: PairTable = HashMap::with_capacity(a.len() * b.len());
    for (i, (p, _)) in a.iter().enumerate() {
        for (j, (q, _)) in b.iter().enumerate() {
            t.entry(g.key(&g.add(&mut ops, *p, *q)))
                .or_default()
                .push((i as u32, j as u32));
        }
    }
    t
}

/// All witnesses (usable indices, in summand order) of `target`, at most `limit`.
fn witnesses<G: CountedGroup>(
    g: &G,
    pools: &[Pool<G::Elt>],
    pairs: &PairTable,
    target: G::Elt,
    limit: usize,
) -> Vec<Vec<usize>> {
    let m = pools.len();
    let mut out = Vec::new();
    let mut ops = GroupOps::default();
    let mut chosen: Vec<usize> = Vec::new();
    #[allow(clippy::too_many_arguments)]
    fn rec<G: CountedGroup>(
        g: &G,
        ops: &mut GroupOps,
        pools: &[Pool<G::Elt>],
        pairs: &PairTable,
        depth: usize,
        acc: G::Elt,
        target: G::Elt,
        chosen: &mut Vec<usize>,
        out: &mut Vec<Vec<usize>>,
        limit: usize,
    ) {
        let m = pools.len();
        if out.len() >= limit {
            return;
        }
        if depth == m - 2 {
            let rest = g.add(ops, target, g.neg(acc));
            if let Some(list) = pairs.get(&g.key(&rest)) {
                for &(i, j) in list {
                    let (a, b) = (&pools[m - 2][i as usize], &pools[m - 1][j as usize]);
                    if g.key(&g.add(ops, a.0, b.0)) == g.key(&rest) {
                        let mut w = chosen.clone();
                        w.push(a.1);
                        w.push(b.1);
                        out.push(w);
                        if out.len() >= limit {
                            return;
                        }
                    }
                }
            }
            return;
        }
        for (p, ix) in &pools[depth] {
            chosen.push(*ix);
            let next = g.add(ops, acc, *p);
            rec(
                g,
                ops,
                pools,
                pairs,
                depth + 1,
                next,
                target,
                chosen,
                out,
                limit,
            );
            chosen.pop();
            if out.len() >= limit {
                return;
            }
        }
    }
    rec(
        g,
        &mut ops,
        pools,
        pairs,
        0,
        g.identity(),
        target,
        &mut chosen,
        &mut out,
        limit,
    );
    let _ = m;
    out
}

fn in_subgroup<G: CountedGroup>(g: &G, e: G::Elt, r: u64, h: u64) -> bool {
    if g.is_identity(&e) {
        return false;
    }
    h == 1 || g.is_identity(&g.mul(&mut GroupOps::default(), e, r))
}

fn yield_group<G: CountedGroup>(
    inp: &YieldInput<'_, G>,
    req: &MetricRequest,
    seed: u64,
) -> YieldOut {
    let m = req.m as usize;
    let g = inp.g;
    let mut status = Status::Complete;
    let mut reason: Option<String> = None;
    let idx_of: HashMap<u64, usize> = inp
        .usable
        .iter()
        .enumerate()
        .map(|(i, p)| (g.key(p), i))
        .collect();
    let pool_n = inp.pool0.len();
    let order = inp.r.saturating_mul(inp.h);
    let mut out = Map::new();
    out.insert("m".into(), json!(m));
    out.insert("patterns".into(), json!(inp.patterns));
    out.insert("pool_points".into(), json!(pool_n));
    let targets_n = (inp.r.saturating_sub(1)).min(u64::from(req.targets)) as usize;
    // Poisson model (a model, not a measurement).
    let multisets = (pool_n as f64).powi(m as i32) / (1..=m).map(|k| k as f64).product::<f64>();
    out.insert(
        "coverage_poisson_model".into(),
        json!(1.0 - (-(multisets * inp.patterns as f64) / order as f64).exp()),
    );
    if pool_n == 0 {
        out.insert("coverage".into(), json!(0.0));
        out.insert("expected_trials".into(), Value::Null);
        out.insert("expected_trials_reason".into(), json!("empty pool"));
        return YieldOut {
            json: Value::Object(out),
            coverage: Some(0.0),
            expected: None,
            status,
            reason,
        };
    }
    let started = Instant::now();
    let pattern_pools: Vec<Vec<Pool<G::Elt>>> = (1..=inp.patterns)
        .map(|s| pools_for(inp, &idx_of, m, s % inp.ext.max(1) as usize))
        .collect();
    // Exact coverage by layered sumsets.
    let blowup = (pool_n as f64).powi(m as i32 - 1);
    let work = blowup.min(order as f64) * pool_n as f64;
    let exact = blowup <= req.exact_cap as f64 && work <= 64.0 * req.exact_cap as f64;
    let mut coverage = None;
    let mut ci = Value::Null;
    if exact {
        let mut covered: HashSet<u64> = HashSet::new();
        let mut ops = GroupOps::default();
        let mut aborted = false;
        'pat: for pools in &pattern_pools {
            let mut layer: HashMap<u64, G::Elt> =
                pools[0].iter().map(|(p, _)| (g.key(p), *p)).collect();
            for pool in &pools[1..] {
                let mut next: HashMap<u64, G::Elt> = HashMap::new();
                for a in layer.values() {
                    for (b, _) in pool {
                        let s = g.add(&mut ops, *a, *b);
                        next.insert(g.key(&s), s);
                    }
                    if next.len() as u64 > 2 * req.exact_cap || started.elapsed() > req.budget {
                        aborted = true;
                        break 'pat;
                    }
                }
                layer = next;
            }
            for (k, e) in layer {
                if !covered.contains(&k) && in_subgroup(g, e, inp.r, inp.h) {
                    covered.insert(k);
                }
            }
        }
        if aborted {
            status = Status::CapsHit;
            reason = Some(
                "caps_hit: exact sumset layer exceeded the cap; falling back to sampling".into(),
            );
        } else {
            coverage = Some(covered.len() as f64 / (inp.r - 1).max(1) as f64);
            out.insert("mode".into(), json!("exact"));
            out.insert("targets_evaluated".into(), json!(inp.r - 1));
        }
    }
    // Sampled search: relations for rank / column rate, and coverage if not exact.
    let tables_cost = (pool_n as f64) * (pool_n as f64);
    let search_cost = (pool_n as f64).powi(m as i32 - 2) * targets_n as f64 * inp.patterns as f64;
    let mut relations: Vec<Vec<usize>> = Vec::new();
    let mut covered_targets = 0usize;
    let mut witness_total = 0usize;
    let mut searched = 0usize;
    let guard = (req.exact_cap as f64 * 4.0).max(1e6);
    if tables_cost > guard || search_cost > guard {
        let why = format!(
            "caps_hit: decomposition search |F|^(m-2)*targets = {search_cost:.3e} exceeds {guard:.3e}"
        );
        if status < Status::CapsHit {
            status = Status::CapsHit;
            reason = Some(why.clone());
        }
        out.insert("relations_reason".into(), json!(why));
    } else {
        let tables: Vec<PairTable> = pattern_pools
            .iter()
            .map(|p| pair_table(g, &p[m - 2], &p[m - 1]))
            .collect();
        let mut rng = StdRng::seed_from_u64(seed ^ 0x7969_656c_6400);
        let mut ops = GroupOps::default();
        for _ in 0..targets_n {
            if started.elapsed() > req.budget {
                if status < Status::Budget {
                    status = Status::Budget;
                    reason = Some("budget: yield sampling stopped at the wall budget".into());
                }
                break;
            }
            let k = rng.gen_range(1..inp.r);
            let t = g.mul(&mut ops, inp.generator, k);
            searched += 1;
            let mut found = false;
            for (pools, table) in pattern_pools.iter().zip(&tables) {
                let w = witnesses(g, pools, table, t, 8);
                if !w.is_empty() {
                    found = true;
                    witness_total += w.len();
                    relations.extend(w);
                    break;
                }
            }
            if found {
                covered_targets += 1;
            }
        }
        if coverage.is_none() && searched > 0 {
            coverage = Some(covered_targets as f64 / searched as f64);
            let (lo, hi) = wilson(covered_targets, searched);
            ci = json!([lo, hi]);
            out.insert("mode".into(), json!("sampled"));
            out.insert("targets_evaluated".into(), json!(searched));
        }
    }
    out.insert(
        "coverage".into(),
        coverage.map_or(Value::Null, |c| json!(c)),
    );
    out.insert("coverage_ci95".into(), ci);
    if coverage.is_none() {
        out.insert(
            "coverage_reason".into(),
            json!(reason
                .clone()
                .unwrap_or_else(|| "no targets evaluated".into())),
        );
    }
    let expected = coverage
        .filter(|&c| c > 0.0)
        .map(|c| (inp.columns as f64 + 1.0) / c);
    out.insert(
        "expected_trials".into(),
        expected.map_or(Value::Null, |e| json!(e)),
    );
    if expected.is_none() {
        out.insert(
            "expected_trials_reason".into(),
            json!("coverage unknown or zero"),
        );
    }
    // Column statistics from the sampled relations.
    if searched > 0 && !relations.is_empty() {
        let mut hits = vec![0usize; inp.columns];
        let mut rows: Vec<Vec<u64>> = Vec::new();
        for w in &relations {
            let mut row = vec![0u64; inp.columns];
            let mut seen = HashSet::new();
            for &u in w {
                let (col, k, neg) = inp.loc[u];
                let mut c = powmod(inp.lambda, u64::from(k), inp.r);
                if neg {
                    c = (inp.r - c) % inp.r;
                }
                row[col] = (row[col] + c) % inp.r;
                seen.insert(col);
            }
            for c in seen {
                hits[c] += 1;
            }
            rows.push(row);
        }
        let rate = hits.iter().copied().min().unwrap_or(0) as f64 / relations.len() as f64;
        out.insert("min_column_rate".into(), json!(rate));
        out.insert(
            "columns_never_hit".into(),
            json!(hits.iter().filter(|&&h| h == 0).count()),
        );
        out.insert("relations_found".into(), json!(relations.len()));
        out.insert(
            "rows_per_target".into(),
            json!(witness_total as f64 / searched as f64),
        );
        if inp.columns <= 2048 && rows.len() <= 8192 {
            out.insert(
                "achievable_rank".into(),
                json!(rank_mod(rows, inp.columns, inp.r)),
            );
        } else {
            out.insert("achievable_rank".into(), Value::Null);
            out.insert(
                "achievable_rank_reason".into(),
                json!("caps_hit: matrix larger than 2048 columns"),
            );
        }
    } else {
        for k in ["min_column_rate", "achievable_rank", "rows_per_target"] {
            out.insert(k.into(), Value::Null);
            out.insert(format!("{k}_reason"), json!("no relation sampled"));
        }
    }
    YieldOut {
        json: Value::Object(out),
        coverage,
        expected,
        status,
        reason,
    }
}

/// Rank over `Z/rZ` (`r` prime) of dense rows.
fn rank_mod(mut rows: Vec<Vec<u64>>, cols: usize, r: u64) -> usize {
    let mut pivot_row: Vec<Option<usize>> = vec![None; cols];
    let mut basis: Vec<Vec<u64>> = Vec::new();
    for row in rows.drain(..) {
        let mut row = row;
        for c in 0..cols {
            if row[c] == 0 {
                continue;
            }
            match pivot_row[c] {
                Some(b) => {
                    let f = row[c];
                    for (x, y) in row.iter_mut().zip(&basis[b]) {
                        *x = (*x + r - mulmod(f, *y, r)) % r;
                    }
                }
                None => {
                    let inv = powmod(row[c], r - 2, r);
                    for x in row.iter_mut() {
                        *x = mulmod(*x, inv, r);
                    }
                    pivot_row[c] = Some(basis.len());
                    basis.push(row);
                    break;
                }
            }
        }
    }
    basis.len()
}

// ── Systems, F4, SAT ───────────────────────────────────────────────

/// Domain of one summand: `x = shift + span(basis)`.
struct Domain {
    basis: Vec<F2mElement>,
    words: Vec<u64>,
    shift: u64,
}

struct SystemBuilder<'a> {
    ctx: &'a Ctx<'a>,
    st: FieldStructure,
    domains: Vec<Domain>,
    b: F2mElement,
    trace_rows: bool,
    n_vars: usize,
    ell: usize,
}

impl SystemBuilder<'_> {
    fn build(&self, x_r: &F2mElement) -> Vec<F2BoolPoly> {
        let (n, m, ell, nv) = (self.ctx.n, self.domains.len(), self.ell, self.n_vars);
        let summands: Vec<SymElement> = self
            .domains
            .iter()
            .enumerate()
            .map(|(i, d)| {
                let v = SymElement::from_subspace_vars(&d.basis, i * ell, n, nv);
                v.add(&SymElement::constant(
                    &self.ctx.gf.to_element(d.shift),
                    n,
                    nv,
                ))
            })
            .collect();
        let target = SymElement::constant(x_r, n, nv);
        let mut eqs = Vec::new();
        if m == 2 {
            eqs.extend(sym_semaev_s3(
                &summands[0],
                &summands[1],
                &target,
                &self.b,
                &self.st,
            ));
        } else {
            let inter: Vec<SymElement> = (0..m - 2)
                .map(|i| SymElement::from_free_vars(m * ell + i * n as usize, n, nv))
                .collect();
            eqs.extend(sym_semaev_s3(
                &summands[0],
                &summands[1],
                &inter[0],
                &self.b,
                &self.st,
            ));
            for i in 0..m - 3 {
                eqs.extend(sym_semaev_s3(
                    &inter[i],
                    &summands[i + 2],
                    &inter[i + 1],
                    &self.b,
                    &self.st,
                ));
            }
            eqs.extend(sym_semaev_s3(
                &inter[m - 3],
                &summands[m - 1],
                &target,
                &self.b,
                &self.st,
            ));
        }
        if self.trace_rows {
            eqs.extend(self.trace_equations());
        }
        eqs
    }

    /// Per summand, the exact ANF of "the abscissa lifts to a curve point".
    fn trace_equations(&self) -> Vec<F2BoolPoly> {
        let ctx = self.ctx;
        let mut out = Vec::new();
        for (i, d) in self.domains.iter().enumerate() {
            let l = self.ell;
            let mut table: Vec<u8> = span_with_shift(&d.words, d.shift)
                .into_iter()
                .map(|x| {
                    if x == 0 {
                        0
                    } else {
                        let v = x ^ ctx.a ^ ctx.gf.mul(ctx.b, ctx.gf.sqr(ctx.gf.inv(x)));
                        ctx.trace(v) as u8
                    }
                })
                .collect();
            // Moebius transform to the ANF.
            for bit in 0..l {
                for idx in 0..table.len() {
                    if idx & (1 << bit) != 0 {
                        table[idx] ^= table[idx ^ (1 << bit)];
                    }
                }
            }
            let monos: Vec<F2BoolMono> = table
                .iter()
                .enumerate()
                .filter(|(_, &c)| c == 1)
                .map(|(idx, _)| F2BoolMono::from_mask((idx as u64) << (i * l)))
                .collect();
            if !monos.is_empty() {
                out.push(F2BoolPoly::from_monos(monos, self.n_vars));
            }
        }
        out
    }
}

/// `span(basis) + shift` in the order whose index bit `t` selects `basis[t]`.
fn span_with_shift(basis: &[u64], shift: u64) -> Vec<u64> {
    span(basis).into_iter().map(|x| x ^ shift).collect()
}

fn mean(v: &[f64]) -> Value {
    if v.is_empty() {
        Value::Null
    } else {
        json!(v.iter().sum::<f64>() / v.len() as f64)
    }
}

fn max_of(v: &[f64]) -> Value {
    v.iter()
        .copied()
        .reduce(f64::max)
        .map_or(Value::Null, |x| json!(x))
}

/// Largest Macaulay degree whose column count stays below `2^22`.
fn degree_cap(n_vars: usize, d_max: u32) -> u32 {
    let mut cols = 1f64;
    let mut term = 1f64;
    let mut best = 0;
    for d in 1..=d_max {
        term = term * (n_vars as f64 - d as f64 + 1.0) / d as f64;
        cols += term;
        if cols > 4_194_304.0 {
            break;
        }
        best = d;
    }
    best
}

fn add_symmetry_breaking(solver: &mut crate::cryptanalysis::sat::Solver, m: usize, ell: usize) {
    use crate::cryptanalysis::sat::Lit;
    for i in 0..m - 1 {
        let (a0, b0) = ((i * ell) as Lit + 1, ((i + 1) * ell) as Lit + 1);
        // eq_t: blocks equal on the first t bits (most significant bit last).
        let mut prev: Option<Lit> = None;
        for t in (0..ell as Lit).rev() {
            let (a, b) = (a0 + t, b0 + t);
            let guard: Vec<Lit> = prev.map_or(Vec::new(), |p| vec![-p]);
            let mut c = guard.clone();
            c.extend([-a, b]);
            solver.add_clause(c);
            if t > 0 {
                let e = *solver.add_vars(1).start() as Lit;
                for (x, y) in [(a, b), (-a, -b)] {
                    let mut c = guard.clone();
                    c.extend([e, x, y]);
                    // e <- prev & (a == b): (e | !prev | a | b) and (e | !prev | !a | !b)
                    solver.add_clause(c);
                }
                prev = Some(e);
            }
        }
    }
}

// ── Public entry point ─────────────────────────────────────────────

fn projected_lambda(ctx: &Ctx) -> u64 {
    ctx.kc.and_then(|kc| kc.lambda.to_u64()).unwrap_or(1)
}

fn construction_json(
    mat: &Materialized,
    geometric: usize,
    usable: usize,
    strict: Option<usize>,
    columns: usize,
    n: Option<u32>,
    hash: String,
) -> Value {
    let info = mat.info();
    let e = match (n, info.dimension, info.dim_v2) {
        (Some(n), Some(d), Some(d2)) => json!(i64::from(n) - i64::from(d) - i64::from(d2)),
        _ => Value::Null,
    };
    let mut c = json!({
        "fb_points": usable,
        "geometric_points": geometric,
        "usable_points": usable,
        "strict_subgroup_points": strict,
        "effective_columns": columns,
        "fold_ratio": if columns > 0 { json!(usable as f64 / columns as f64) } else { Value::Null },
        "abscissae": info.abscissae,
        "dimension": info.dimension,
        "dim_v2": info.dim_v2,
        "linearization_excess": e,
        "trace_class": info.trace_class,
        "basis_weight": info.basis_weight,
        "build_ms": info.build_ms,
        "point_set_sha256": hash,
        "notes": info.notes,
        "extra": info.extra,
    });
    if let (Materialized::Koblitz { fb, .. }, Some(map)) = (mat, c.as_object_mut()) {
        map.insert("signed_orbits_unprojected".into(), json!(fb.unknowns()));
    }
    c
}

/// Measure one cell. Returns the `metrics` object, the status and, when the
/// status is not `complete`, the reason.
pub fn measure(
    curve: &Curve<'_>,
    mat: &Materialized,
    req: &MetricRequest,
    seed: u64,
) -> (Value, Status, Option<String>) {
    let mut tr = Tracker {
        status: Status::Complete,
        reason: None,
    };
    let mut metrics = Map::new();
    let mut mods = mat.info().system_modifiers.clone();
    for (k, v) in &req.system_modifiers {
        mods.entry(k.clone()).or_insert_with(|| v.clone());
    }
    metrics.insert("m".into(), json!(req.m));
    metrics.insert(
        "system_modifiers".into(),
        Value::Object(mods.clone().into_iter().collect()),
    );
    let want = |g: Group| req.groups.contains(&g);
    if !(2..=8).contains(&req.m) {
        tr.note(Status::Error, "m must be in 2..=8");
        return (Value::Object(metrics), tr.status, tr.reason);
    }
    match (curve, mat) {
        (
            Curve::Prime(inst),
            Materialized::Prime {
                points, abscissae, ..
            },
        ) => {
            measure_prime(
                inst,
                mat,
                points,
                *abscissae,
                req,
                seed,
                &mut metrics,
                &mut tr,
            );
        }
        _ => match Ctx::new(curve) {
            Ok(ctx) => measure_binary(&ctx, curve, mat, req, seed, &mods, &mut metrics, &mut tr),
            Err(e) => {
                let why = e.to_string();
                large_construction(mat, &mut metrics);
                for g in [
                    Group::Yield,
                    Group::System,
                    Group::F4,
                    Group::Sat,
                    Group::Derived,
                ] {
                    if want(g) {
                        metrics.insert(g.as_str().into(), unmeasured(&why));
                    }
                }
            }
        },
    }
    if want(Group::Xl) {
        metrics.insert(
            "xl".into(),
            unmeasured("not_applicable: the optional XL group is not built in this release"),
        );
    }
    (Value::Object(metrics), tr.status, tr.reason)
}

/// Construction for fields too wide for single-word arithmetic.
fn large_construction(mat: &Materialized, metrics: &mut Map<String, Value>) {
    if let Materialized::Koblitz { fb, info, .. } = mat {
        let pairs: Vec<(String, String)> = fb
            .points
            .iter()
            .filter_map(|p| match p {
                crate::binary_ecc::BinaryPoint::Affine { x, y } => Some((
                    x.to_biguint().to_str_radix(16),
                    y.to_biguint().to_str_radix(16),
                )),
                crate::binary_ecc::BinaryPoint::Infinity => None,
            })
            .collect();
        let mut c = construction_json(
            mat,
            fb.points.len(),
            pairs.len(),
            None,
            fb.unknowns(),
            None,
            point_set_sha256(&pairs),
        );
        if let Some(map) = c.as_object_mut() {
            map.insert(
                "usable_points_reason".into(),
                json!("n > 62: cofactor projection needs single-word arithmetic; geometric points reported as usable"),
            );
            map.insert("abscissae".into(), json!(info.abscissae));
        }
        metrics.insert("construction".into(), c);
    }
}

#[allow(clippy::too_many_arguments)]
fn measure_binary(
    ctx: &Ctx<'_>,
    curve: &Curve<'_>,
    mat: &Materialized,
    req: &MetricRequest,
    seed: u64,
    mods: &BTreeMap<String, Value>,
    metrics: &mut Map<String, Value>,
    tr: &mut Tracker,
) {
    let want = |g: Group| req.groups.contains(&g);
    let view = base_points_binary(ctx, mat);
    let pairs: Vec<(String, String)> = view.usable.iter().map(hex_pair).collect();
    metrics.insert(
        "construction".into(),
        construction_json(
            mat,
            view.geometric,
            view.usable.len(),
            view.strict,
            view.columns,
            Some(ctx.n),
            point_set_sha256(&pairs),
        ),
    );
    let on = |k: &str| match mods.get(k) {
        None => 0,
        Some(v) => v.as_u64().unwrap_or(1),
    };
    let patterns = if on("per-summand-shift") > 0 {
        on("per-summand-shift") as usize
    } else {
        usize::from(on("tau-twist") > 0)
    };
    let shifted = patterns > 0;
    if shifted && ctx.kc.is_none() {
        let why = "not_applicable: per-summand shifts need the Frobenius of a Koblitz curve";
        for g in [
            Group::Yield,
            Group::System,
            Group::F4,
            Group::Sat,
            Group::Derived,
        ] {
            if want(g) {
                metrics.insert(g.as_str().into(), unmeasured(why));
            }
        }
        return;
    }
    // Pool of the first summand.
    let pool0: Vec<usize> = match &mat.info().pool_abscissae {
        Some(set) => {
            let s: HashSet<u64> = set.iter().copied().collect();
            let mut ps: Vec<usize> = (0..view.usable.len())
                .filter(|&i| s.contains(&view.usable[i].x))
                .collect();
            if let Materialized::Koblitz { shift: Some(_), .. }
            | Materialized::Binary { shift: Some(_), .. } = mat
            {
                ps.sort_unstable();
            }
            ps
        }
        None => (0..view.usable.len()).collect(),
    };
    let group = BinaryGroup(&ctx.fast);
    let kfrob = ctx.kc.map_or(1, |kc| kc.k);
    let twist = |p: FastPoint, j: u32| ctx.fast.frobenius_k(p, kfrob * j);
    let mut yld: Option<YieldOut> = None;
    if want(Group::Yield) || want(Group::Derived) {
        let inp = YieldInput {
            g: &group,
            generator: ctx.generator,
            r: ctx.r,
            h: ctx.h,
            usable: &view.usable,
            loc: &view.loc,
            columns: view.columns,
            pool0,
            twist: Some(&twist),
            lambda: projected_lambda(ctx),
            ext: ctx.kc.map_or(1, |kc| kc.extension_degree()),
            patterns: patterns.max(1),
            use_pattern_shift: shifted,
        };
        let y = yield_group(&inp, req, seed);
        tr.note(y.status, y.reason.as_deref().unwrap_or(""));
        if want(Group::Yield) {
            metrics.insert("yield".into(), y.json.clone());
        }
        yld = Some(y);
    }
    // Solver groups share one system builder.
    let solver_groups = [Group::System, Group::F4, Group::Sat];
    let need_system = solver_groups.iter().any(|g| want(*g)) || want(Group::Derived);
    let mut f4_ops: Option<f64> = None;
    let mut sat_ops: Option<f64> = None;
    if need_system {
        match build_builder(ctx, curve, mat, req, shifted, on("trace-constraint") > 0) {
            Err(why) => {
                for g in solver_groups {
                    if want(g) {
                        metrics.insert(g.as_str().into(), unmeasured(&why));
                    }
                }
            }
            Ok(sb) => {
                let solved = run_solvers(
                    ctx,
                    &sb,
                    req,
                    seed,
                    mods,
                    want(Group::F4),
                    want(Group::Sat),
                    want(Group::System),
                );
                for (name, v, st, why) in solved.groups {
                    metrics.insert(name.into(), v);
                    tr.note(st, &why);
                }
                f4_ops = solved.f4_ops;
                sat_ops = solved.sat_ops;
            }
        }
    }
    if want(Group::Derived) {
        let trials = yld.as_ref().and_then(|y| y.expected);
        let solves = patterns.max(1) as f64;
        let derive = |ops: Option<f64>| match (trials, ops) {
            (Some(t), Some(o)) => json!(t * o * solves),
            _ => Value::Null,
        };
        let pick_f4 = f4_ops.is_some();
        let (ops_json, unit) = if pick_f4 {
            (derive(f4_ops), "f4 word XORs (elimination only)")
        } else {
            (derive(sat_ops), "sat conflicts")
        };
        metrics.insert(
            "derived".into(),
            json!({
                "expected_pdp_ops": ops_json,
                "op_unit": if ops_json.is_null() { Value::Null } else { json!(unit) },
                "expected_pdp_ops_f4": derive(f4_ops),
                "expected_pdp_ops_sat": derive(sat_ops),
                "ops_reason": if ops_json.is_null() {
                    json!("needs expected_trials and a measured solver cost (random-target class mean)")
                } else { Value::Null },
                "solves_per_attempt": solves,
                "la_cost_estimate": (view.columns as f64).powi(2) * f64::from(req.m),
                "la_cost_label": "estimate: effective_columns^2 * avg_row_weight (= m)",
                "composite": Value::Null,
                "composite_reason": "computed by fbkit rank",
            }),
        );
    }
}

fn build_builder<'a>(
    ctx: &'a Ctx<'a>,
    curve: &Curve<'_>,
    mat: &Materialized,
    req: &MetricRequest,
    shifted: bool,
    trace_rows: bool,
) -> Result<SystemBuilder<'a>, String> {
    let (basis_words, shift): (Vec<u64>, u64) = match mat {
        Materialized::Koblitz {
            basis: Some(b),
            shift,
            ..
        } => (
            b.iter().map(|e| ctx.gf.from_element(e)).collect(),
            shift.as_ref().map_or(0, |c| ctx.gf.from_element(c)),
        ),
        Materialized::Binary {
            subspace_basis,
            shift,
            ..
        } if !subspace_basis.is_empty() => (subspace_basis.clone(), shift.unwrap_or(0)),
        _ => {
            return Err(
                "not_applicable: no subspace basis in the x-frame (non-subspace set)".into(),
            )
        }
    };
    let (m, ell, n) = (req.m as usize, basis_words.len(), ctx.n as usize);
    let n_vars = m * ell + (m - 2) * n;
    if n_vars > MAX_VARS {
        return Err(format!("not_applicable: n_vars {n_vars} > {MAX_VARS}"));
    }
    if trace_rows && ell > 12 {
        return Err("not_applicable: trace-constraint needs dim V <= 12".into());
    }
    let irr = match curve {
        Curve::Koblitz(kc) => kc.curve.irreducible.clone(),
        Curve::Binary(i) => i.irreducible.clone(),
        Curve::Prime(_) => return Err("not_applicable: prime regime".into()),
    };
    let kfrob = ctx.kc.map_or(1, |kc| kc.k);
    let ext = ctx.kc.map_or(1, |kc| kc.extension_degree()) as usize;
    let domains: Vec<Domain> = (0..m)
        .map(|i| {
            let j = if shifted { (i % ext) as u32 } else { 0 };
            let words: Vec<u64> = basis_words
                .iter()
                .map(|&w| ctx.gf.sqr_k(w, kfrob * j))
                .collect();
            Domain {
                basis: words.iter().map(|&w| ctx.gf.to_element(w)).collect(),
                shift: ctx.gf.sqr_k(shift, kfrob * j),
                words,
            }
        })
        .collect();
    Ok(SystemBuilder {
        ctx,
        st: FieldStructure::new(ctx.n, &irr),
        domains,
        b: ctx.gf.to_element(ctx.b),
        trace_rows,
        n_vars,
        ell,
    })
}

struct Solved {
    groups: Vec<(&'static str, Value, Status, String)>,
    f4_ops: Option<f64>,
    sat_ops: Option<f64>,
}

#[allow(clippy::too_many_arguments)]
fn run_solvers(
    ctx: &Ctx<'_>,
    sb: &SystemBuilder<'_>,
    req: &MetricRequest,
    seed: u64,
    mods: &BTreeMap<String, Value>,
    want_f4: bool,
    want_sat: bool,
    want_sys: bool,
) -> Solved {
    let mut rng = StdRng::seed_from_u64(seed ^ 0x736f_6c76);
    let per_class = (req.targets as usize).max(1);
    // Targets: planted decompositions and uniform subgroup points.
    let mut classes: Vec<(&'static str, Vec<F2mElement>)> =
        vec![("planted", Vec::new()), ("random", Vec::new())];
    let liftable: Vec<Vec<u64>> = sb
        .domains
        .iter()
        .map(|d| {
            span_with_shift(&d.words, d.shift)
                .into_iter()
                .filter(|&x| x != 0 && !ctx.points_with_x(x).is_empty())
                .collect()
        })
        .collect();
    let mut guard = 0;
    while classes[0].1.len() < per_class
        && guard < 100 * per_class
        && liftable.iter().all(|l| !l.is_empty())
    {
        guard += 1;
        let mut acc = FastPoint::INFINITY;
        for l in &liftable {
            let x = l[rng.gen_range(0..l.len())];
            let pts = ctx.points_with_x(x);
            acc = ctx.fast.add(acc, pts[rng.gen_range(0..pts.len())]);
        }
        if !acc.infinity {
            classes[0].1.push(ctx.gf.to_element(acc.x));
        }
    }
    guard = 0;
    while classes[1].1.len() < per_class && guard < 100 * per_class {
        guard += 1;
        let k = rng.gen_range(1..ctx.r.max(2));
        let t = ctx.mul(ctx.generator, k);
        if !t.infinity {
            classes[1].1.push(ctx.gf.to_element(t.x));
        }
    }
    let deadline = Duration::from_secs_f64(req.budget.as_secs_f64().max(0.1));
    let mut out = Solved {
        groups: Vec::new(),
        f4_ops: None,
        sat_ops: None,
    };
    let first_eqs = classes[0].1.first().map(|x| sb.build(x));
    if want_sys {
        let v = match &first_eqs {
            Some(eqs) => {
                let sys = BooleanSystem {
                    equations: eqs.clone(),
                    n_vars: sb.n_vars,
                };
                let shape = sys.shape();
                let terms: usize = eqs.iter().map(|e| e.terms.len()).sum();
                json!({
                    "n_vars": sb.n_vars,
                    "n_equations": shape.n_equations,
                    "degrees": shape.degrees,
                    "semi_regular_degree": shape.semi_regular_degree,
                    "anf_terms": terms,
                    "summand_dimension": sb.ell,
                    "trace_rows": sb.trace_rows,
                })
            }
            None => unmeasured("no planted target could be drawn"),
        };
        out.groups
            .push(("system", v, Status::Complete, String::new()));
    }
    if want_f4 {
        let started = Instant::now();
        let mut status = Status::Complete;
        let mut why = String::new();
        let mut per_class_json = Map::new();
        let f4 = solver_by_name("f4-f2").ok();
        for (name, targets) in &classes {
            let (mut sd, mut dr, mut rows, mut cols, mut ops, mut ms) =
                (vec![], vec![], vec![], vec![], vec![], vec![]);
            let (mut gb_sd, mut over) = (vec![], vec![]);
            let (mut refuted, mut solved, mut timed_out, mut done) = (0, 0, 0, 0);
            for x in targets {
                if started.elapsed() > deadline {
                    status = Status::Budget;
                    why = "budget: f4 stopped at the wall budget".into();
                    break;
                }
                let eqs = sb.build(x);
                done += 1;
                let dcap = degree_cap(sb.n_vars, req.d_max);
                let (found, profiles) = solving_degree(&eqs, sb.n_vars, dcap);
                if let Some(d) = found {
                    sd.push(f64::from(d));
                    let sr = BooleanSystem {
                        equations: eqs.clone(),
                        n_vars: sb.n_vars,
                    }
                    .shape()
                    .semi_regular_degree;
                    if let Some(s) = sr {
                        over.push(f64::from(d) - f64::from(s));
                    }
                } else {
                    status = status.max(Status::CapsHit);
                    if why.is_empty() {
                        why = format!("caps_hit: no resolution up to Macaulay degree {dcap}");
                    }
                }
                rows.push(profiles.iter().map(|p| p.rows).max().unwrap_or(0) as f64);
                cols.push(profiles.iter().map(|p| p.cols).max().unwrap_or(0) as f64);
                if profiles.iter().any(|p| p.refuted) {
                    refuted += 1;
                }
                if let Some(f4) = &f4 {
                    let sys = BooleanSystem {
                        equations: eqs,
                        n_vars: sb.n_vars,
                    };
                    let budget = Duration::from_secs_f64(
                        (deadline.as_secs_f64() / (2.0 * targets.len() as f64)).max(0.05),
                    );
                    let (verdict, cost) = f4.solve(&sys, &Params::default(), Some(budget));
                    ops.push(cost.ops as f64);
                    ms.push(cost.wall_ns as f64 / 1e6);
                    if let Some(d) = cost.degree_reached {
                        dr.push(f64::from(d));
                    }
                    if let Some(d) = cost.solving_degree {
                        gb_sd.push(f64::from(d));
                    }
                    if cost.timed_out {
                        timed_out += 1;
                    }
                    match verdict {
                        SolverVerdict::Solved(_) => solved += 1,
                        SolverVerdict::Unsatisfiable => {}
                        SolverVerdict::BudgetExceeded => {}
                    }
                }
            }
            per_class_json.insert(
                (*name).to_string(),
                json!({
                    "targets": done,
                    "solving_degree_mean": mean(&sd),
                    "solving_degree_max": max_of(&sd),
                    "solving_degree_resolved": sd.len(),
                    "degree_over_bound_mean": mean(&over),
                    "degree_reached_max": max_of(&dr),
                    "gb_solving_degree_max": max_of(&gb_sd),
                    "matrix_rows_max": max_of(&rows),
                    "matrix_cols_max": max_of(&cols),
                    "word_ops_mean": mean(&ops),
                    "ms_mean": mean(&ms),
                    "refuted": refuted,
                    "solved": solved,
                    "timed_out": timed_out,
                }),
            );
            if *name == "random" {
                out.f4_ops = ops
                    .iter()
                    .copied()
                    .reduce(|a, b| a + b)
                    .map(|s| s / ops.len() as f64);
            }
        }
        out.groups
            .push(("f4", Value::Object(per_class_json), status, why));
    }
    if want_sat {
        let started = Instant::now();
        let mut status = Status::Complete;
        let mut why = String::new();
        let mut per_class_json = Map::new();
        let mut shape = (0u32, 0usize, 0usize);
        for (name, targets) in &classes {
            let (mut conf, mut dec, mut prop, mut learnt, mut ms) =
                (vec![], vec![], vec![], vec![], vec![]);
            let (mut sat, mut unsat, mut unknown) = (0, 0, 0);
            for x in targets {
                if started.elapsed() > deadline {
                    status = Status::Budget;
                    why = "budget: sat stopped at the wall budget".into();
                    break;
                }
                let mut eqs = sb.build(x);
                if let Some(d) = mods
                    .get("macaulay-implied")
                    .and_then(Value::as_u64)
                    .filter(|&d| d >= 2)
                {
                    if degree_cap(sb.n_vars, d as u32) >= d as u32 {
                        if let Some(rows) = matrix_f4_f2(&eqs, sb.n_vars, d as u32) {
                            eqs.extend(rows.into_iter().take(4096));
                        }
                    } else {
                        status = status.max(Status::CapsHit);
                        why =
                            format!("caps_hit: macaulay-implied degree {d} exceeds the matrix cap");
                    }
                }
                let t0 = Instant::now();
                let mut enc = encode_boolean_system_with(sb.n_vars, &eqs, &[], XorEncoding::Native);
                if mods
                    .get("symmetry-breaking")
                    .and_then(Value::as_u64)
                    .unwrap_or(0)
                    > 0
                {
                    add_symmetry_breaking(&mut enc.solver, sb.domains.len(), sb.ell);
                }
                enc.solver.conflict_budget = req.conflict_budget;
                use crate::cryptanalysis::sat::SolveResult;
                let verdict = if enc.trivially_unsat {
                    SolveResult::Unsat
                } else {
                    enc.solver.solve()
                };
                let s = &enc.solver.stats;
                conf.push(s.conflicts as f64);
                dec.push(s.decisions as f64);
                prop.push(s.propagations as f64);
                learnt.push(s.learnt_clauses as f64);
                ms.push(t0.elapsed().as_secs_f64() * 1e3);
                shape = (
                    enc.solver.n_vars(),
                    enc.solver.n_original_clauses(),
                    enc.solver.n_xors(),
                );
                match verdict {
                    SolveResult::Sat => sat += 1,
                    SolveResult::Unsat => unsat += 1,
                    SolveResult::Unknown => unknown += 1,
                }
            }
            per_class_json.insert(
                (*name).to_string(),
                json!({
                    "targets": conf.len(),
                    "conflicts_mean": mean(&conf),
                    "conflicts_max": max_of(&conf),
                    "decisions_mean": mean(&dec),
                    "propagations_mean": mean(&prop),
                    "learnt_clauses_mean": mean(&learnt),
                    "ms_mean": mean(&ms),
                    "sat": sat, "unsat": unsat, "unknown": unknown,
                }),
            );
            if *name == "random" {
                out.sat_ops = conf
                    .iter()
                    .copied()
                    .reduce(|a, b| a + b)
                    .map(|s| s / conf.len() as f64);
            }
        }
        per_class_json.insert("variables".into(), json!(shape.0));
        per_class_json.insert("clauses".into(), json!(shape.1));
        per_class_json.insert("xors".into(), json!(shape.2));
        per_class_json.insert("conflict_budget".into(), json!(req.conflict_budget));
        out.groups
            .push(("sat", Value::Object(per_class_json), status, why));
    }
    out
}

#[allow(clippy::too_many_arguments)]
fn measure_prime(
    inst: &PrimeInstance,
    mat: &Materialized,
    points: &[(u64, u64)],
    abscissae: usize,
    req: &MetricRequest,
    seed: u64,
    metrics: &mut Map<String, Value>,
    tr: &mut Tracker,
) {
    use crate::cryptanalysis::ic_boundary::PrimePoint;
    let g = &inst.curve;
    let mut ops = GroupOps::default();
    let mut usable = Vec::new();
    let mut proj = Vec::new();
    for &(x, y) in points {
        let p = PrimePoint::affine(x, y);
        let q = if inst.cofactor == 1 {
            p
        } else {
            g.mul(&mut ops, p, inst.cofactor)
        };
        if !q.infinity {
            usable.push(p);
            proj.push(q);
        }
    }
    let mut cols: HashMap<u64, usize> = HashMap::new();
    let mut loc = Vec::new();
    for q in &proj {
        let (k1, k2) = (g.key(q), g.key(&g.neg(*q)));
        let canon = k1.min(k2);
        let next = cols.len();
        let c = *cols.entry(canon).or_insert(next);
        loc.push((c, 0u32, k1 != canon));
    }
    let pairs: Vec<(String, String)> = usable
        .iter()
        .map(|p| (format!("{:x}", p.x), format!("{:x}", p.y)))
        .collect();
    let strict = (points.len() <= 1 << 17).then(|| {
        points
            .iter()
            .filter(|&&(x, y)| {
                g.mul(&mut GroupOps::default(), PrimePoint::affine(x, y), inst.r)
                    .infinity
            })
            .count()
    });
    metrics.insert(
        "construction".into(),
        construction_json(
            mat,
            points.len(),
            usable.len(),
            strict,
            cols.len(),
            None,
            point_set_sha256(&pairs),
        ),
    );
    let _ = abscissae;
    if req.groups.contains(&Group::Yield) || req.groups.contains(&Group::Derived) {
        let inp = YieldInput {
            g,
            generator: inst.generator_point(),
            r: inst.r,
            h: inst.cofactor,
            usable: &usable,
            loc: &loc,
            columns: cols.len(),
            pool0: (0..usable.len()).collect(),
            twist: None,
            lambda: 1,
            ext: 1,
            patterns: 1,
            use_pattern_shift: false,
        };
        let y = yield_group(&inp, req, seed);
        tr.note(y.status, y.reason.as_deref().unwrap_or(""));
        let _ = y.coverage;
        if req.groups.contains(&Group::Yield) {
            metrics.insert("yield".into(), y.json);
        }
    }
    for g in [Group::System, Group::F4, Group::Sat, Group::Derived] {
        if req.groups.contains(&g) {
            metrics.insert(
                g.as_str().into(),
                unmeasured("not_applicable: prime regime"),
            );
        }
    }
}

// Silence an unused-import warning when `BasePoints` is only used in signatures.
#[allow(dead_code)]
fn _assert_view(_: &BasePoints<FastPoint>) {}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::fbkit::families::{materialize, Recipe};
    use crate::cryptanalysis::koblitz_index_calculus::KoblitzCurve;

    fn curve(n: u32) -> KoblitzCurve {
        [1u8, 0]
            .into_iter()
            .find_map(|a| KoblitzCurve::new(a, n))
            .expect("curve")
    }

    fn req(m: u32, groups: &str) -> MetricRequest {
        MetricRequest {
            groups: Group::parse_list(groups).expect("groups"),
            m,
            targets: 4,
            d_max: 4,
            budget: Duration::from_secs(60),
            ..MetricRequest::default()
        }
    }

    #[test]
    fn toy_cell_completes_every_group() {
        let kc = curve(11);
        let cv = Curve::Koblitz(&kc);
        for m in [2u32, 3] {
            let t = Instant::now();
            let r = Recipe::parse("coordinate:l=5").expect("recipe");
            let mat = materialize(&r, &cv, 1).expect("builds");
            let (v, st, why) = measure(
                &cv,
                &mat,
                &req(m, "construction,yield,system,f4,sat,derived"),
                5,
            );
            assert!(st <= Status::CapsHit, "{why:?} {v}");
            assert!(v["construction"]["point_set_sha256"].as_str().is_some());
            assert!(v["yield"]["coverage"].is_number(), "{v}");
            assert!(v["system"]["n_vars"].is_number());
            assert!(
                v["f4"]["planted"]["targets"].as_u64().unwrap_or(0) >= 1,
                "{v}"
            );
            assert!(v["sat"]["planted"]["sat"].as_u64().unwrap_or(0) >= 1, "{v}");
            assert!(v["derived"]["la_cost_estimate"].is_number());
            assert!(
                t.elapsed() < Duration::from_secs(600),
                "toy cell took too long"
            );
        }
    }

    #[test]
    fn large_m_is_not_applicable_for_solvers_but_yields() {
        let kc = curve(9);
        let cv = Curve::Koblitz(&kc);
        let r = Recipe::parse("coordinate:l=2").expect("recipe");
        let mat = materialize(&r, &cv, 1).expect("builds");
        let (v, st, _) = measure(&cv, &mat, &req(8, "construction,yield,f4,sat"), 5);
        assert_eq!(st, Status::Complete, "{v}");
        let nv = 8 * 2 + 6 * 9;
        let want = format!("not_applicable: n_vars {nv} > 64");
        assert_eq!(v["f4"]["reason"], json!(want));
        assert_eq!(v["sat"]["reason"], json!(want));
        assert!(v["construction"]["fb_points"].is_number());
        assert!(v["yield"].get("coverage").is_some());
    }

    #[test]
    fn modifiers_and_binary_regime() {
        let kc = curve(9);
        let cv = Curve::Koblitz(&kc);
        let r = Recipe::parse("coordinate:l=2;tau-twist=1;trace-constraint=1;symmetry-breaking=1")
            .expect("recipe");
        let mat = materialize(&r, &cv, 1).expect("builds");
        let (v, st, why) = measure(
            &cv,
            &mat,
            &req(2, "construction,yield,system,f4,sat,derived"),
            5,
        );
        assert!(st <= Status::CapsHit, "{why:?} {v}");
        let inst =
            crate::cryptanalysis::ic_boundary::random_binary_instance(11, 3, 8).expect("curve");
        let bc = Curve::Binary(&inst);
        let mat = materialize(&Recipe::parse("random:l=3").expect("r"), &bc, 1).expect("builds");
        let (v, st, why) = measure(
            &bc,
            &mat,
            &req(2, "construction,yield,system,f4,sat,derived"),
            5,
        );
        assert!(st <= Status::CapsHit, "{why:?} {v}");
        assert!(v["yield"]["coverage"].is_number());
    }

    #[test]
    fn rank_mod_counts_independent_rows() {
        let rows = vec![vec![1, 2, 3], vec![2, 4, 6], vec![0, 1, 1]];
        assert_eq!(rank_mod(rows, 3, 101), 2);
    }
}
