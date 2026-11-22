//! # The factor bases, oracles and matrices that ship with the framework.
//!
//! Each of these wraps a component the repository already measures, so
//! a framework run reproduces a ledger row rather than approximating
//! one.  They are also the worked examples: a new plug-in looks like
//! these, and `docs/ic/FRAMEWORK.md` walks through writing one.
//!
//! ## Factor bases
//!
//! | name | regime | what it is |
//! |:--|:--|:--|
//! | `prime-abscissa` | prime | the smallest abscissae carrying a point, one column each |
//! | `binary-subspace` | binary, Koblitz | points whose abscissa lies in an `F_2`-subspace |
//! | `koblitz-orbit` | Koblitz | the same, each signed Frobenius orbit folded onto one column |
//!
//! The column map is the interesting part.  `koblitz-orbit` gives a
//! whole orbit of `2n` points one unknown, which cuts the relations
//! needed by `2n`; setting its `no_fold` parameter gives the control
//! that shows what the fold buys.  That pair is the one place this
//! ledger records an *advance* in the `AGENTS.md` §3 sense rather than
//! engineering, and it is a two-word change in a sweep file.
//!
//! ## Decomposition oracles
//!
//! | name | summands | how |
//! |:--|:--|:--|
//! | `subtract` | 2 | test `R − P ∈ F` for every signed base point; no table |
//! | `mitm` | 2 or 3 | a pair table probed once per target, or once per `R − P` |
//! | `mitm-frobenius` | 2 or 3 | the same on a Frobenius-folded table (Koblitz) |
//!
//! The pair table is where memory buys time, and `mitm`'s
//! `negation_folded` parameter halves the additions that build it.

use std::time::{Duration, Instant};

use super::stages::{
    BooleanSystem, DecompositionOracle, FactorBaseBuilder, InstanceCtx, Params, SolverCost,
    SolverTotals, SolverVerdict, SystemShape, SystemSolver,
};
use crate::cryptanalysis::ic_boundary::{
    binary_subspace_factor_base, decompose_mitm, decompose_mitm_frobenius, koblitz_factor_base,
    prime_factor_base, BinaryGroup, BinaryInstance, ColumnFold, CountedGroup, FactorBase,
    FrobeniusPairTable, GroupOps, OracleCounters, PairTable, PrimeCurve, PrimeInstance, PrimePoint,
};
use crate::cryptanalysis::koblitz_fast::FastPoint;
use crate::cryptanalysis::koblitz_index_calculus::build_frobenius_factor_base_from_divisor;
use crate::cryptanalysis::pq_descent_symbolic::{descend, max_n_prime, SymbolicDescent};

// ── Factor bases ───────────────────────────────────────────────────

/// The smallest abscissae of a prime-field curve that carry a point,
/// one column each.
pub struct PrimeAbscissaBase<'i> {
    pub instance: &'i PrimeInstance,
}

impl FactorBaseBuilder<PrimeCurve> for PrimeAbscissaBase<'_> {
    fn name(&self) -> &str {
        "prime-abscissa"
    }

    fn describe(&self, params: &Params) -> String {
        format!(
            "the {} smallest abscissae carrying a point, one column each",
            params.get("size").unwrap_or("?")
        )
    }

    fn parameters(&self) -> &[(&str, &str)] {
        &[(
            "size",
            "abscissae in the base; the family optimum is about #E^(1/3)",
        )]
    }

    fn build(
        &self,
        _ctx: &InstanceCtx<PrimeCurve>,
        params: &Params,
        _ops: &mut GroupOps,
    ) -> Result<FactorBase<PrimePoint>, String> {
        let size = params.u64("size")? as usize;
        if size == 0 {
            return Err("factor base size must be positive".into());
        }
        Ok(prime_factor_base(self.instance, size))
    }
}

/// Points of a binary curve whose abscissa lies in an `F_2`-subspace
/// of the field, one column per abscissa.
pub struct BinarySubspaceBase<'i> {
    pub instance: &'i BinaryInstance,
}

impl<'a> FactorBaseBuilder<BinaryGroup<'a>> for BinarySubspaceBase<'_> {
    fn name(&self) -> &str {
        "binary-subspace"
    }

    fn describe(&self, params: &Params) -> String {
        format!(
            "points whose abscissa lies in the {}-dimensional subspace spanned by {{1, z, …}}",
            params.get("dimension").unwrap_or("?")
        )
    }

    fn parameters(&self) -> &[(&str, &str)] {
        &[(
            "dimension",
            "F_2-dimension of the abscissa subspace; about 2^dimension abscissae",
        )]
    }

    fn build(
        &self,
        _ctx: &InstanceCtx<BinaryGroup<'a>>,
        params: &Params,
        _ops: &mut GroupOps,
    ) -> Result<FactorBase<FastPoint>, String> {
        let dim = params.u64("dimension")? as u32;
        if dim == 0 || dim > 30 {
            return Err(format!("subspace dimension {dim} outside 1..=30"));
        }
        let basis: Vec<u64> = (0..dim).map(|k| 1u64 << k).collect();
        Ok(binary_subspace_factor_base(self.instance, &basis))
    }
}

/// A Koblitz base with each signed Frobenius orbit folded onto one
/// column: `2n` points, one unknown.
pub struct KoblitzOrbitBase<'i> {
    pub instance: &'i BinaryInstance,
}

impl<'a> FactorBaseBuilder<BinaryGroup<'a>> for KoblitzOrbitBase<'_> {
    fn name(&self) -> &str {
        "koblitz-orbit"
    }

    fn describe(&self, params: &Params) -> String {
        format!(
            "the Frobenius-invariant subspace spanned by divisor factors {}, {}",
            params.get("divisor").unwrap_or("?"),
            if params.flag("no_fold") {
                "one column per abscissa (the unfolded control)"
            } else {
                "each signed Frobenius orbit folded onto one column"
            }
        )
    }

    fn parameters(&self) -> &[(&str, &str)] {
        &[
            (
                "divisor",
                "comma-separated indices into the factorisation of the Frobenius characteristic \
                 polynomial; the invariant subspace they span becomes the abscissa set. This is \
                 the knob that chooses the base, so sweeping it sweeps factor bases",
            ),
            (
                "no_fold",
                "1 to give every abscissa its own column: the control that shows what the fold buys",
            ),
        ]
    }

    fn build(
        &self,
        _ctx: &InstanceCtx<BinaryGroup<'a>>,
        params: &Params,
        _ops: &mut GroupOps,
    ) -> Result<FactorBase<FastPoint>, String> {
        let kc = self
            .instance
            .koblitz
            .as_ref()
            .ok_or("this instance is not a Koblitz curve, so it has no Frobenius to fold by")?;
        let raw = params
            .get("divisor")
            .ok_or("missing parameter `divisor`; try 0 or 0,1")?;
        let idx: Result<Vec<usize>, String> = raw
            .split([',', ';'])
            .filter(|s| !s.is_empty())
            .map(|s| {
                s.trim()
                    .parse::<usize>()
                    .map_err(|_| format!("divisor index `{s}` is not a number"))
            })
            .collect();
        let idx = idx?;
        if idx.is_empty() {
            return Err("parameter `divisor` selected no factors".into());
        }
        let frob = build_frobenius_factor_base_from_divisor(kc, &idx)
            .ok_or_else(|| format!("no invariant subspace for divisor {idx:?} on this curve"))?;
        let fold = if params.flag("no_fold") {
            ColumnFold::Abscissa
        } else {
            ColumnFold::SignedFrobeniusOrbit
        };
        koblitz_factor_base(
            self.instance,
            &frob,
            fold,
            format!(
                "invariant subspace, divisor {idx:?}, dimension {}",
                frob.ell
            ),
        )
        .ok_or_else(|| "the invariant subspace produced no usable factor base".into())
    }
}

// ── Decomposition oracles ──────────────────────────────────────────

/// Test `R − P ∈ F` for every signed base point: no table, `|F|` group
/// operations a target, and the honest baseline every table oracle is
/// an improvement on.
pub struct SubtractOracle;

impl<G: CountedGroup> DecompositionOracle<G> for SubtractOracle {
    fn name(&self) -> &str {
        "subtract"
    }

    fn summands(&self) -> u32 {
        2
    }

    fn describe(&self, _params: &Params) -> String {
        "for each signed base point P, test whether R − P is in the base".into()
    }

    fn decompose(
        &mut self,
        ctx: &InstanceCtx<G>,
        fb: &FactorBase<G::Elt>,
        ops: &mut GroupOps,
        counters: &mut OracleCounters,
        point: G::Elt,
    ) -> Option<Vec<usize>> {
        for (i, p) in fb.points.iter().enumerate() {
            let rest = ctx.group.add(ops, point, ctx.group.neg(*p));
            counters.lookups += 1;
            let key = ctx.group.key(&rest);
            if let Some(j) = fb.index_of_key(key) {
                return Some(vec![i, j]);
            }
        }
        None
    }
}

/// How a pair table's coset filter labelled the base, for the report.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct CosetFilter {
    /// `off` (not asked, `m ≠ 2` or cofactor 1), `trace` (cofactor 2, the
    /// free `Tr(x) = Tr(a)` test) or `scalar` (`[r]P` per base point,
    /// charged as scalar multiplications).
    pub mode: &'static str,
    /// Points of the base that lie in the subgroup `⟨G⟩`.
    pub in_subgroup: u64,
    /// Distinct classes seen among the base points.
    pub classes: u64,
}

/// The coset filter for a two-summand pair table.
///
/// A target `R = [a]G + [b]Q` lies in the subgroup `⟨G⟩` of index `h`
/// (the cofactor), and `P_i + P_j = R` forces the classes of `P_i` and
/// `P_j` in `E/⟨G⟩` to cancel.  Every other pair of the table is an
/// addition that no subgroup target can ever hit; with `h` classes about
/// `1 − 1/h` of a full table is such dead weight, and the table is the
/// bulk of the two-summand cost on every binary ledger instance.  The
/// relations a filtered table yields are identical: a key that a subgroup
/// target can hit is only ever witnessed by a pair whose classes cancel
/// (`±R` share a class), and the surviving pairs are visited in the full
/// build's order, so the first witness is the same.
///
/// Returns the per-point class keys `(key(T_i), key(−T_i))` with
/// `T_i = [r]P_i ∈ E[h]`, or the parity classes when the group reads them
/// for free and the cofactor is 2; `None` when the filter does nothing.
pub fn coset_classes<G: CountedGroup>(
    ctx: &InstanceCtx<G>,
    fb: &FactorBase<G::Elt>,
    ops: &mut GroupOps,
    report: &mut CosetFilter,
) -> Option<Vec<(u64, u64)>> {
    let g = ctx.group;
    if ctx.cofactor <= 1 {
        report.mode = "off";
        return None;
    }
    let parity: Option<Vec<u8>> = if ctx.cofactor == 2 {
        fb.points.iter().map(|p| g.coset_parity(p)).collect()
    } else {
        None
    };
    let classes: Vec<(u64, u64)> = match parity {
        Some(par) => {
            report.mode = "trace";
            // Class 0 is the subgroup; with two classes each is its own
            // negative, so the pair key is the class itself.
            par.iter().map(|&c| (c as u64, c as u64)).collect()
        }
        None => {
            report.mode = "scalar";
            // One `[r]P` per ± pair: `[r](−P) = −[r]P`, so the negative's
            // keys are the same pair swapped.
            let mut out: Vec<Option<(u64, u64)>> = vec![None; fb.points.len()];
            for i in 0..fb.points.len() {
                if out[i].is_some() {
                    continue;
                }
                let t = g.mul(ops, fb.points[i], ctx.r);
                let (k, nk) = (g.key(&t), g.key(&g.neg(t)));
                out[i] = Some((k, nk));
                let j = fb.neg_index[i];
                if j < out.len() && out[j].is_none() {
                    out[j] = Some((nk, k));
                }
            }
            out.into_iter().map(|c| c.expect("every point labelled")).collect()
        }
    };
    let identity_key = if report.mode == "trace" {
        0
    } else {
        g.key(&g.identity())
    };
    report.in_subgroup = classes.iter().filter(|(k, _)| *k == identity_key).count() as u64;
    let mut seen: Vec<u64> = classes.iter().map(|(k, _)| *k).collect();
    seen.sort_unstable();
    seen.dedup();
    report.classes = seen.len() as u64;
    Some(classes)
}

fn read_coset_flag(params: &Params) -> Result<bool, String> {
    match params.u64_or("coset_filter", 0)? {
        0 => Ok(false),
        1 => Ok(true),
        _ => Err("coset_filter must be 0 or 1".into()),
    }
}

/// Meet in the middle over a pair table: memory for time, the lever
/// that makes a two-summand search `O(1)` a target instead of `O(|F|)`.
pub struct MitmOracle {
    m: u32,
    table: Option<PairTable>,
    native_setup_ns: u64,
    pub coset: CosetFilter,
}

impl MitmOracle {
    pub fn new(m: u32) -> Self {
        Self {
            m,
            table: None,
            native_setup_ns: 0,
            coset: CosetFilter::default(),
        }
    }
}

impl<G: CountedGroup> DecompositionOracle<G> for MitmOracle {
    fn name(&self) -> &str {
        "mitm"
    }

    fn summands(&self) -> u32 {
        self.m
    }

    fn describe(&self, params: &Params) -> String {
        format!(
            "a table of pair sums probed once per target (m = 2) or once per R − P (m = 3), {}{}",
            if params.flag("negation_folded") {
                "built with the negation fold"
            } else {
                "built in full"
            },
            if params.flag("coset_filter") {
                ", coset-filtered to the pairs whose classes in E/⟨G⟩ cancel"
            } else {
                ""
            }
        )
    }

    fn parameters(&self) -> &[(&str, &str)] {
        &[(
            "negation_folded",
            "1 to build only one of each ±pair, halving the table's additions",
        ), ("native_setup_pricing", "0 or1, default0; price whole preparation in nanoseconds and retain additions as diagnostics"),
        ("coset_filter", "1 to build only the pairs whose coset classes in E/<G> cancel: with cofactor h only those can sum to a subgroup target, so about 1 - 1/h of the table's additions are skipped; m = 2 only, no-op at m = 3 and with cofactor 1; cofactor 2 reads the class from Tr(x) = Tr(a) for free, larger cofactors charge one [r]P per base point")]
    }

    fn prepare(
        &mut self,
        ctx: &InstanceCtx<G>,
        fb: &FactorBase<G::Elt>,
        params: &Params,
        ops: &mut GroupOps,
    ) -> Result<(), String> {
        let native = params.u64_or("native_setup_pricing", 0)?;
        if native > 1 {
            return Err("native_setup_pricing must be0 or1".into());
        }
        let started = Instant::now();
        let mut label_ops = GroupOps::default();
        self.coset = CosetFilter { mode: "off", ..Default::default() };
        let classes = if read_coset_flag(params)? && self.m == 2 {
            coset_classes(ctx, fb, &mut label_ops, &mut self.coset)
        } else {
            None
        };
        let keep = classes
            .as_ref()
            .map(|c| move |i: usize, j: usize| c[i].0 == c[j].1);
        let keep_ref: Option<&dyn Fn(usize, usize) -> bool> =
            keep.as_ref().map(|k| k as &dyn Fn(usize, usize) -> bool);
        let table = if params.flag("negation_folded") {
            PairTable::build_negation_folded_filtered(ctx.group, fb, keep_ref)
        } else {
            PairTable::build_filtered(ctx.group, fb, keep_ref)
        };
        // The table's construction is part of the pipeline's cost, and so
        // are the class labels when they cost group operations.
        ops.merge(label_ops);
        if native == 0 {
            ops.merge(table.build_ops);
        }
        self.table = Some(table);
        self.native_setup_ns = if native == 1 {
            started.elapsed().as_nanos() as u64
        } else {
            0
        };
        Ok(())
    }

    fn setup_native(&self) -> std::collections::BTreeMap<String, u64> {
        let mut out = std::collections::BTreeMap::new();
        if self.coset.mode != "off" && !self.coset.mode.is_empty() {
            out.insert("mitm_coset_filter_in_subgroup".into(), self.coset.in_subgroup);
            out.insert("mitm_coset_filter_classes".into(), self.coset.classes);
            out.insert(
                "mitm_coset_filter_scalar_labels".into(),
                u64::from(self.coset.mode == "scalar"),
            );
        }
        if self.native_setup_ns == 0 {
            return out;
        }
        let observed = self.table.as_ref().unwrap().build_ops;
        out.extend([
            ("mitm_native_setup_ns".into(), self.native_setup_ns),
            ("mitm_setup_observed_adds".into(), observed.adds),
            ("mitm_setup_observed_doubles".into(), observed.doubles),
            (
                "mitm_setup_observed_scalar_mults".into(),
                observed.scalar_mults,
            ),
        ]);
        out
    }

    fn decompose(
        &mut self,
        ctx: &InstanceCtx<G>,
        fb: &FactorBase<G::Elt>,
        ops: &mut GroupOps,
        counters: &mut OracleCounters,
        point: G::Elt,
    ) -> Option<Vec<usize>> {
        let table = self.table.as_ref()?;
        decompose_mitm(ctx.group, fb, table, self.m, ops, counters, point)
    }
}

/// Meet in the middle on a table folded by the signed Frobenius: the
/// same probe over a table `2n` times smaller.
pub struct FrobeniusMitmOracle<'i> {
    m: u32,
    instance: &'i BinaryInstance,
    table: Option<FrobeniusPairTable>,
    pub coset: CosetFilter,
}

impl<'i> FrobeniusMitmOracle<'i> {
    pub fn new(m: u32, instance: &'i BinaryInstance) -> Self {
        Self {
            m,
            instance,
            table: None,
            coset: CosetFilter::default(),
        }
    }
}

impl<'a> DecompositionOracle<BinaryGroup<'a>> for FrobeniusMitmOracle<'_> {
    fn name(&self) -> &str {
        "mitm-frobenius"
    }

    fn summands(&self) -> u32 {
        self.m
    }

    fn describe(&self, params: &Params) -> String {
        format!(
            "a pair table folded by the signed Frobenius, one entry per orbit{}",
            if params.flag("coset_filter") {
                ", coset-filtered to the pairs whose classes in E/⟨G⟩ cancel"
            } else {
                ""
            }
        )
    }

    fn parameters(&self) -> &[(&str, &str)] {
        &[("coset_filter", "1 to build only the representative-point pairs whose coset classes in E/<G> cancel (the Frobenius preserves the class); m = 2 only, no-op at m = 3 and with cofactor 1")]
    }

    fn setup_native(&self) -> std::collections::BTreeMap<String, u64> {
        if self.coset.mode == "off" || self.coset.mode.is_empty() {
            return Default::default();
        }
        std::collections::BTreeMap::from([
            ("mitm_coset_filter_in_subgroup".into(), self.coset.in_subgroup),
            ("mitm_coset_filter_classes".into(), self.coset.classes),
            (
                "mitm_coset_filter_scalar_labels".into(),
                u64::from(self.coset.mode == "scalar"),
            ),
        ])
    }

    fn prepare(
        &mut self,
        ctx: &InstanceCtx<BinaryGroup<'a>>,
        fb: &FactorBase<FastPoint>,
        params: &Params,
        ops: &mut GroupOps,
    ) -> Result<(), String> {
        let mut label_ops = GroupOps::default();
        self.coset = CosetFilter { mode: "off", ..Default::default() };
        let classes = if read_coset_flag(params)? && self.m == 2 {
            coset_classes(ctx, fb, &mut label_ops, &mut self.coset)
        } else {
            None
        };
        let keep = classes
            .as_ref()
            .map(|c| move |i: usize, j: usize| c[i].0 == c[j].1);
        let keep_ref: Option<&dyn Fn(usize, usize) -> bool> =
            keep.as_ref().map(|k| k as &dyn Fn(usize, usize) -> bool);
        let table = FrobeniusPairTable::build_filtered(self.instance, fb, keep_ref)
            .ok_or("this instance has no Koblitz structure to fold by")?;
        ops.merge(label_ops);
        ops.merge(table.build_ops);
        self.table = Some(table);
        Ok(())
    }

    fn decompose(
        &mut self,
        ctx: &InstanceCtx<BinaryGroup<'a>>,
        fb: &FactorBase<FastPoint>,
        ops: &mut GroupOps,
        counters: &mut OracleCounters,
        point: FastPoint,
    ) -> Option<Vec<usize>> {
        let table = self.table.as_ref()?;
        decompose_mitm_frobenius(ctx.group, fb, table, self.m, ops, counters, point)
    }
}

// ── The bridge to the solver plug point ────────────────────────────

/// Holds a [`SystemSolver`] and the record of what it cost, so an
/// algebraic oracle can be written without repeating the bookkeeping.
///
/// This is what makes the solver plug point reachable from a whole
/// pipeline: swap `buchberger-f2` for `sat-cdcl` and the change
/// propagates through the relation phase to the recovered key, with
/// every stage still counted.
pub struct SolverHarness {
    pub solver: Box<dyn SystemSolver>,
    pub params: Params,
    pub budget: Option<Duration>,
    last_shape: Option<SystemShape>,
    last_cost: Option<SolverCost>,
    /// Targets whose solver hit its budget.  Counted, never silently
    /// folded into "did not decompose": an oracle that did that would
    /// quietly lower its own hit rate and make the relation phase it
    /// feeds unmeasurable.
    pub budget_exceeded: u64,
}

impl SolverHarness {
    pub fn new(solver: Box<dyn SystemSolver>, params: Params, budget: Option<Duration>) -> Self {
        Self {
            solver,
            params,
            budget,
            last_shape: None,
            last_cost: None,
            budget_exceeded: 0,
        }
    }

    /// Solve one descended system, recording what it cost.
    pub fn solve(&mut self, system: &BooleanSystem) -> SolverVerdict {
        let shape = system.shape();
        self.last_shape = Some(shape.clone());
        if !self.solver.accepts(&shape) {
            self.last_cost = None;
            self.budget_exceeded += 1;
            return SolverVerdict::BudgetExceeded;
        }
        let (verdict, cost) = self.solver.solve(system, &self.params, self.budget);
        self.last_cost = Some(cost);
        if matches!(verdict, SolverVerdict::BudgetExceeded) {
            self.budget_exceeded += 1;
        }
        verdict
    }

    pub fn shape(&self) -> Option<&SystemShape> {
        self.last_shape.as_ref()
    }

    pub fn cost(&self) -> Option<&SolverCost> {
        self.last_cost.as_ref()
    }
}

// ── The algebraic oracle ───────────────────────────────────────────

/// Descend the Semaev polynomial over the base's abscissa subspace and
/// hand the boolean system to the chosen [`SystemSolver`].
///
/// This is the oracle that makes the solver plug point reach the `S`
/// column: swap `buchberger-f2` for `sat-cdcl` and the change
/// propagates through the relation phase to the recovered logarithm,
/// with every stage still counted.  It requires a factor base whose
/// abscissae form an `F_2`-subspace — `binary-subspace` and
/// `koblitz-orbit` both record theirs in `FactorBase::subspace_basis`.
///
/// ## What it charges
///
/// The descent and the solver are engine work, not group operations,
/// and are reported through [`DecompositionOracle::solver_totals`] in
/// the solver's own unit; the runner prices them into `S`.  Lifting a
/// solution back to signed base points costs real group additions,
/// which are charged to `ops` like any other oracle's.
///
/// ## The cap
///
/// The descent is symbolic — the summation polynomial expanded in
/// `F_{2^n}[v]/(v² − v)` term by term — so it builds no table and is
/// capped only by the monomial mask: `m·n' ≤ 64` boolean variables,
/// `n' ≤ 32` at two summands and `n' ≤ 21` at three.  What limits a
/// row above that is the engine, which says so through `accepts`.
pub struct DescentAlgebraicOracle<'i> {
    summands: u32,
    instance: &'i BinaryInstance,
    v_basis: Vec<u64>,
    harness: SolverHarness,
    totals: SolverTotals,
    descent_setup_ns: u64,
    descent_relation_ns: u64,
    /// Systems the solver decided satisfiable none of whose solutions
    /// lifted to base points summing to the target.  Expected, not a
    /// defect: a summation polynomial vanishes over the algebraic
    /// closure, so a solution may name abscissae whose points live on
    /// the quadratic twist (`y ∈ F_{2^{2n}}`, never in the base), and
    /// the pair table never sees those.  Reported as
    /// `unliftable_systems` beside `lift_failures` so the hit rate can
    /// be read against what the solver actually found.
    pub unliftable: u64,
}

impl<'i> DescentAlgebraicOracle<'i> {
    pub fn new(
        summands: u32,
        instance: &'i BinaryInstance,
        solver: Box<dyn SystemSolver>,
        solver_params: Params,
        budget: Option<Duration>,
    ) -> Self {
        let totals = SolverTotals {
            solver: solver.name().to_string(),
            ..Default::default()
        };
        Self {
            summands,
            instance,
            v_basis: Vec::new(),
            harness: SolverHarness::new(solver, solver_params, budget),
            totals,
            descent_setup_ns: 0,
            descent_relation_ns: 0,
            unliftable: 0,
        }
    }

    pub fn solver_name(&self) -> &str {
        self.harness.solver.name()
    }

    /// The descended system for a target abscissa; its `lift` maps a
    /// solution back to abscissae.  `prepare` must have run.
    fn descend(&self, x_r: u64) -> SymbolicDescent {
        descend(
            &self.instance.gf,
            self.instance.b,
            x_r,
            &self.v_basis,
            self.summands,
        )
        .expect("prepare checked the dimension")
    }
}

fn system_of(sys: &SymbolicDescent) -> BooleanSystem {
    BooleanSystem {
        equations: sys.equations.clone(),
        n_vars: sys.n_vars,
    }
}

impl<'a> DecompositionOracle<BinaryGroup<'a>> for DescentAlgebraicOracle<'_> {
    fn name(&self) -> &str {
        "descent-algebraic"
    }

    fn summands(&self) -> u32 {
        self.summands
    }

    fn describe(&self, _params: &Params) -> String {
        format!(
            "Weil-descend S_{} over the base's abscissa subspace and solve with {}",
            self.summands + 1,
            self.harness.solver.name()
        )
    }

    fn parameters(&self) -> &[(&str, &str)] {
        &[("m", "summands, 2 (descends S3) or 3 (descends S4)")]
    }

    fn setup_native(&self) -> std::collections::BTreeMap<String, u64> {
        std::collections::BTreeMap::from([("symbolic_descent_ns".into(), self.descent_setup_ns)])
    }

    fn relation_counters(&self) -> std::collections::BTreeMap<String, u64> {
        std::collections::BTreeMap::from([("symbolic_descent_ns".into(), self.descent_relation_ns)])
    }

    fn prepare(
        &mut self,
        _ctx: &InstanceCtx<BinaryGroup<'a>>,
        fb: &FactorBase<FastPoint>,
        _params: &Params,
        _ops: &mut GroupOps,
    ) -> Result<(), String> {
        if !(2..=3).contains(&self.summands) {
            return Err(format!(
                "descent-algebraic takes m = 2 or 3, got {}",
                self.summands
            ));
        }
        let basis = fb.subspace_basis.as_ref().ok_or(
            "descent-algebraic needs a factor base whose abscissae form an F_2-subspace; \
             use binary-subspace or koblitz-orbit",
        )?;
        let cap = max_n_prime(self.summands);
        if basis.len() as u32 > cap {
            return Err(format!(
                "the descent's monomial mask holds n' ≤ {cap} at m = {}; this base has n' = {}",
                self.summands,
                basis.len()
            ));
        }
        self.v_basis = basis.clone();
        // Every system on one base has the same shape, so descend one
        // abscissa now and let the engine decline the shape here, once,
        // with a reason a sweep can report — rather than target by
        // target, which would run the whole relation phase for nothing.
        let started = Instant::now();
        let shape = system_of(&self.descend(self.instance.generator.x)).shape();
        self.descent_setup_ns = self
            .descent_setup_ns
            .saturating_add(started.elapsed().as_nanos() as u64);
        if !self.harness.solver.accepts(&shape) {
            return Err(format!(
                "solver `{}` declines a system of {} unknowns and {} equations; \
                 use a smaller base or another engine",
                self.harness.solver.name(),
                shape.n_vars,
                shape.n_equations
            ));
        }
        Ok(())
    }

    fn decompose(
        &mut self,
        ctx: &InstanceCtx<BinaryGroup<'a>>,
        fb: &FactorBase<FastPoint>,
        ops: &mut GroupOps,
        counters: &mut OracleCounters,
        point: FastPoint,
    ) -> Option<Vec<usize>> {
        if self.v_basis.is_empty() {
            return None;
        }
        // Charge descent, system packing and shape construction separately
        // from the solver interval, so failed queries pay the same work too.
        let started = Instant::now();
        let sys = self.descend(point.x);
        let system = system_of(&sys);
        let shape = system.shape();
        self.descent_relation_ns = self
            .descent_relation_ns
            .saturating_add(started.elapsed().as_nanos() as u64);
        let verdict = self.harness.solve(&system);
        let exceeded = matches!(verdict, SolverVerdict::BudgetExceeded);
        self.totals.absorb(&shape, self.harness.cost(), exceeded);
        let SolverVerdict::Solved(solutions) = verdict else {
            return None;
        };
        for v in solutions {
            let xs = sys.lift(v);
            if let Some(indices) =
                crate::cryptanalysis::ic_boundary::lift_abscissae(ctx.group, fb, ops, &xs, point)
            {
                return Some(indices);
            }
            counters.lift_failures += 1;
        }
        self.unliftable += 1;
        counters.unliftable_systems += 1;
        None
    }

    fn last_system(&self) -> Option<SystemShape> {
        self.totals.shape.clone()
    }

    fn solver_totals(&self) -> Option<SolverTotals> {
        Some(self.totals.clone())
    }
}

#[cfg(test)]
mod coset_filter_tests {
    use super::*;
    use crate::cryptanalysis::ic_boundary::{random_binary_instance, FrobeniusPairTable};
    use rand::rngs::StdRng;
    use rand::{Rng, SeedableRng};

    fn ctx_for<'a>(inst: &'a BinaryInstance, g: &'a BinaryGroup<'a>) -> InstanceCtx<'a, BinaryGroup<'a>> {
        InstanceCtx {
            group: g,
            generator: inst.generator,
            target: inst.generator,
            r: inst.r,
            cofactor: inst.cofactor,
            group_order: inst.group_order,
            name: inst.name.clone(),
            field_degree: Some(inst.n),
        }
    }

    /// Instances with cofactor 2, 4 and 8 where the search finds them.
    fn instances() -> Vec<BinaryInstance> {
        let mut out = Vec::new();
        for (n, max_h) in [(13u32, 2u64), (15, 4), (17, 8), (14, 8)] {
            for seed in 1..40u64 {
                if let Some(inst) = random_binary_instance(n, seed, max_h) {
                    if inst.cofactor > 1
                        && !out.iter().any(|o: &BinaryInstance| o.cofactor == inst.cofactor && o.n == n)
                    {
                        out.push(inst);
                        break;
                    }
                }
            }
        }
        assert!(out.len() >= 3, "need cofactor-2, -4 and -8 instances");
        out
    }

    /// **The trace test is the coset class when the cofactor is 2.**
    /// `P ∈ 2E ⇔ Tr(x) = Tr(a)`, and `2E` is the index-2 subgroup.
    #[test]
    fn trace_parity_is_the_subgroup_test_at_cofactor_two() {
        let inst = instances().into_iter().find(|i| i.cofactor == 2).expect("a cofactor-2 instance");
        let g = BinaryGroup(&inst.fast);
        let fb = binary_subspace_factor_base(&inst, &[1, 2, 4, 8, 16]);
        let mut ops = GroupOps::default();
        let (mut zero, mut one) = (0, 0);
        for &p in &fb.points {
            let in_subgroup = g.is_identity(&g.mul(&mut ops, p, inst.r));
            let parity = g.coset_parity(&p).expect("binary groups read the parity");
            assert_eq!(parity == 0, in_subgroup, "x = {:#x}", p.x);
            if parity == 0 { zero += 1 } else { one += 1 }
        }
        assert!(zero > 0 && one > 0, "the base must straddle both cosets ({zero}/{one})");
    }

    /// **A coset-filtered table decomposes every subgroup target exactly
    /// as the full table does, with fewer additions.**  Same witnesses,
    /// same `None`s, on cofactors 2, 4 and 8, folded and unfolded.
    #[test]
    fn coset_filtered_table_agrees_with_the_full_table_on_subgroup_targets() {
        for inst in instances() {
            let g = BinaryGroup(&inst.fast);
            let ctx = ctx_for(&inst, &g);
            let fb = binary_subspace_factor_base(&inst, &[1, 2, 4, 8, 16, 32]);
            let mut label_ops = GroupOps::default();
            let mut report = CosetFilter::default();
            let classes = coset_classes(&ctx, &fb, &mut label_ops, &mut report)
                .expect("cofactor > 1 yields classes");
            assert_eq!(report.mode, if inst.cofactor == 2 { "trace" } else { "scalar" });
            assert!(report.classes >= 2 && report.classes <= inst.cofactor, "{report:?}");
            let keep = |i: usize, j: usize| classes[i].0 == classes[j].1;
            for folded in [false, true] {
                let (full, filtered) = if folded {
                    (
                        PairTable::build_negation_folded(&g, &fb),
                        PairTable::build_negation_folded_filtered(&g, &fb, Some(&keep)),
                    )
                } else {
                    (PairTable::build(&g, &fb), PairTable::build_filtered(&g, &fb, Some(&keep)))
                };
                assert!(
                    filtered.build_ops.adds * 3 <= full.build_ops.adds * 2,
                    "h = {}: filtered {} vs full {} additions",
                    inst.cofactor,
                    filtered.build_ops.adds,
                    full.build_ops.adds
                );
                let mut rng = StdRng::seed_from_u64(inst.cofactor * 1000 + inst.n as u64);
                let (mut hits, mut ops_a, mut ops_b, mut la, mut lb) =
                    (0, GroupOps::default(), GroupOps::default(), 0u64, 0u64);
                for _ in 0..400 {
                    let k = rng.gen_range(1..inst.r);
                    let target = g.mul(&mut GroupOps::default(), inst.generator, k);
                    let a = full.probe(&g, &fb, &mut ops_a, &mut la, target);
                    let b = filtered.probe(&g, &fb, &mut ops_b, &mut lb, target);
                    assert_eq!(a, b, "h = {} folded = {folded}: k = {k}", inst.cofactor);
                    hits += usize::from(a.is_some());
                }
                assert!(hits > 0, "h = {}: no target decomposed", inst.cofactor);
            }
        }
    }

    /// **The Frobenius-folded table obeys the same identity on a Koblitz
    /// instance**, where the cofactor is 2 or 4.
    #[test]
    fn coset_filtered_frobenius_table_agrees_with_the_full_one() {
        use crate::cryptanalysis::ic_boundary::koblitz_instance;
        let Some(inst) = koblitz_instance(1, 13) else {
            return;
        };
        if inst.cofactor <= 1 {
            return;
        }
        let g = BinaryGroup(&inst.fast);
        let ctx = ctx_for(&inst, &g);
        let Some(frob) = build_frobenius_factor_base_from_divisor(inst.koblitz.as_ref().unwrap(), &[0]) else {
            return;
        };
        let Some(fb) = koblitz_factor_base(&inst, &frob, ColumnFold::SignedFrobeniusOrbit, String::new()) else {
            return;
        };
        let mut report = CosetFilter::default();
        let classes = coset_classes(&ctx, &fb, &mut GroupOps::default(), &mut report).unwrap();
        let keep = |i: usize, j: usize| classes[i].0 == classes[j].1;
        let full = FrobeniusPairTable::build(&inst, &fb).unwrap();
        let filtered = FrobeniusPairTable::build_filtered(&inst, &fb, Some(&keep)).unwrap();
        assert!(filtered.build_ops.adds < full.build_ops.adds);
        let mut rng = StdRng::seed_from_u64(13);
        let mut hits = 0;
        for _ in 0..300 {
            let k = rng.gen_range(1..inst.r);
            let target = g.mul(&mut GroupOps::default(), inst.generator, k);
            let (mut ca, mut cb) = (OracleCounters::default(), OracleCounters::default());
            let a = full.probe(&g, &fb, &mut GroupOps::default(), &mut ca, target);
            let b = filtered.probe(&g, &fb, &mut GroupOps::default(), &mut cb, target);
            assert_eq!(a, b, "k = {k}");
            hits += usize::from(a.is_some());
        }
        assert!(hits > 0);
    }

    /// The flag is a no-op at m = 3 and rejects values other than 0/1.
    #[test]
    fn the_flag_is_ignored_at_three_summands_and_validated() {
        let inst = instances().remove(0);
        let g = BinaryGroup(&inst.fast);
        let ctx = ctx_for(&inst, &g);
        let fb = binary_subspace_factor_base(&inst, &[1, 2, 4, 8]);
        let mut params = Params::default();
        params.set("coset_filter", "1");
        let mut three = MitmOracle::new(3);
        three.prepare(&ctx, &fb, &params, &mut GroupOps::default()).unwrap();
        assert_eq!(three.coset.mode, "off");
        let mut two = MitmOracle::new(2);
        two.prepare(&ctx, &fb, &params, &mut GroupOps::default()).unwrap();
        assert_ne!(two.coset.mode, "off");
        params.set("coset_filter", "2");
        assert!(MitmOracle::new(2).prepare(&ctx, &fb, &params, &mut GroupOps::default()).is_err());
    }
}
