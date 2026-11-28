use crate::field::{add_mod, is_prime, mul_mod, sub_mod};
use crate::graph::{GainGraph, SparseSystem};
use crate::phases::{Phase, Profiler, Recorder};
use crate::{
    Backend, BatchScratch, Error, FactorBase, MultiSignedRelation, PairIndex, PairIndexStats,
    Point, Result, SearchPhases, SignedRelation,
};
use std::collections::BTreeSet;
use std::time::{Duration, Instant};

/// Resource envelope and deterministic public-coefficient sampler.
#[derive(Clone, Debug)]
pub struct Config {
    /// SplitMix64 seed; this is not a cryptographic randomness source.
    pub seed: u64,
    /// Maximum processed targets, including infinity and failed queries.
    pub max_queries: u64,
    /// Independent target walks sharing a batch inversion, in 1..=1024.
    pub walk_lanes: usize,
    /// Maximum retained distinct rows; zero selects `4*columns+64`.
    pub max_relations: usize,
    /// Maximum nodes in the sparse certificate DAG, including its zero node.
    pub max_proof_nodes: usize,
    /// Optional soft deadline, checked between complete lane batches.
    pub max_duration: Option<Duration>,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            seed: 0,
            max_queries: 1_000_000,
            walk_lanes: 64,
            max_relations: 0,
            max_proof_nodes: 1 << 22,
            max_duration: None,
        }
    }
}

/// Exact work counters; no benchmark time or performance qualification implied.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct SearchStats {
    /// Targets actually passed through the search loop.
    pub queries: u64,
    /// Targets generated, including unused final-batch lanes.
    pub generated_targets: u64,
    /// Finite target queries passed to the algebraic circuit.
    pub circuit_queries: u64,
    /// Completed target-walk lane rounds.
    pub lane_rounds: u64,
    /// Distinct signed relation rows retained.
    pub relations: usize,
    /// Repeated or sign-reversed rows discarded.
    pub duplicate_rows: u64,
    /// Rank of the factor-base coefficient matrix.
    pub matrix_rank: usize,
    /// Nodes retained in the sparse certificate DAG.
    pub proof_nodes: usize,
    /// Selected arithmetic backend.
    pub backend: Backend,
}

/// Public known-coefficient equation `aG+bQ = ±F_i±F_j`.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Relation {
    /// Coefficient of the public generator, modulo the prime order.
    pub a: u64,
    /// Coefficient of the public target, modulo the prime order.
    pub b: u64,
    /// Signed factor-base row.
    pub decomposition: SignedRelation,
}

/// Public recovery witness; every row and the final cancellation are replayed.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Certificate {
    /// Prime order of the target subgroup.
    pub order: u64,
    /// Public generator of that subgroup.
    pub generator: Point,
    /// Public target whose logarithm is recovered.
    pub target: Point,
    /// Recovered scalar in `[0, order)`.
    pub scalar: u64,
    /// Retained distinct signed rows, in insertion order.
    pub relations: Vec<Relation>,
    /// Linear-combination weights that cancel every factor-base column.
    pub weights: Vec<u64>,
}

/// Public known-coefficient equation `aG+bQ = sum_{t=1..m} s_t F_{i_t}` for `m in 2..=4`.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct MultiRelation {
    /// Coefficient of the public generator, modulo the prime order.
    pub a: u64,
    /// Coefficient of the public target, modulo the prime order.
    pub b: u64,
    /// Signed multi-summand factor-base row.
    pub decomposition: MultiSignedRelation,
}

/// Public recovery witness for `2..=4`-summand index calculus.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct MultiCertificate {
    /// Declared summand arity (`2`, `3`, or `4`).
    pub summands: u8,
    /// Prime order of the target subgroup.
    pub order: u64,
    /// Public generator of that subgroup.
    pub generator: Point,
    /// Public target whose logarithm is recovered.
    pub target: Point,
    /// Recovered scalar in `[0, order)`.
    pub scalar: u64,
    /// Retained distinct signed rows, in insertion order.
    pub relations: Vec<MultiRelation>,
    /// Linear-combination weights that cancel every factor-base column.
    pub weights: Vec<u64>,
}

/// A complete checked `2..=4`-summand recovery or an explicitly bounded incomplete search.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum MultiSolveOutcome {
    /// The public multi-summand certificate has passed local arithmetic replay.
    Solved {
        /// Recovery and cancellation witness.
        certificate: MultiCertificate,
        /// Actual work performed.
        stats: SearchStats,
    },
    /// No recovery was established within the declared envelope.
    Exhausted {
        /// Resource boundary encountered.
        reason: StopReason,
        /// Actual work performed, including unsuccessful targets.
        stats: SearchStats,
    },
}

impl MultiSolveOutcome {
    /// Work counters for either outcome.
    pub fn stats(&self) -> &SearchStats {
        match self {
            Self::Solved { stats, .. } | Self::Exhausted { stats, .. } => stats,
        }
    }
}

/// The configured resource boundary at which a search stopped.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum StopReason {
    /// Processed-target budget.
    QueryBudget,
    /// Distinct-relation storage budget.
    RelationBudget,
    /// Certificate DAG budget.
    ProofBudget,
    /// Soft between-batch wall deadline.
    TimeBudget,
}

/// A complete checked recovery or an explicitly bounded incomplete search.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum SolveOutcome {
    /// The public certificate has passed local arithmetic replay.
    Solved {
        /// Recovery and cancellation witness.
        certificate: Certificate,
        /// Actual work performed.
        stats: SearchStats,
    },
    /// No recovery was established within the declared envelope.
    Exhausted {
        /// Resource boundary encountered.
        reason: StopReason,
        /// Actual work performed, including unsuccessful targets.
        stats: SearchStats,
    },
}

impl SolveOutcome {
    /// Work counters for either outcome.
    pub fn stats(&self) -> &SearchStats {
        match self {
            Self::Solved { stats, .. } | Self::Exhausted { stats, .. } => stats,
        }
    }
}

/// Target-independent generator/subgroup validation reusable across targets.
pub struct PreparedSolver<'a, const B: u32> {
    base: &'a FactorBase<B>,
    order: u64,
    generator: Point,
    full_group: bool,
}

fn integer_sqrt(value: u128) -> u128 {
    if value == 0 {
        return 0;
    }
    let mut root = 1u128 << (128 - value.leading_zeros()).div_ceil(2);
    loop {
        let next = (root + value / root) / 2;
        if next >= root {
            return root;
        }
        root = next;
    }
}

// Requires a separately checked point of prime order `order` on the curve.
pub(crate) fn hasse_cofactor(modulus: u64, order: u64) -> Option<u64> {
    let p = u128::from(modulus);
    let radius = integer_sqrt(4 * p);
    let lo = p + 1 - radius;
    let hi = p + 1 + radius;
    let n = u128::from(order);
    let lower = lo.div_ceil(n);
    (lower == hi / n).then_some(lower as u64)
}

impl<'a, const B: u32> PreparedSolver<'a, B> {
    /// Check an odd prime subgroup, generator, and every usable base point.
    /// A unique full-order multiple in the Hasse interval avoids redundant
    /// per-base scalar multiplications when it certifies the whole group.
    pub fn new(base: &'a FactorBase<B>, order: u64, generator: Point) -> Result<Self> {
        let curve = base.curve();
        if !(3..1u64 << 63).contains(&order) || !is_prime(order) {
            return Err(Error::Invalid(
                "odd prime subgroup order below 2^63 required",
            ));
        }
        if !curve.contains(Some(generator)) || curve.mul_inner(Some(generator), order).is_some() {
            return Err(Error::Invalid(
                "generator does not have the claimed prime order",
            ));
        }
        let full_group = hasse_cofactor(curve.modulus(), order) == Some(1);
        if !full_group
            && base
                .representatives()
                .iter()
                .any(|&point| curve.mul_inner(Some(point), order).is_some())
        {
            return Err(Error::Invalid(
                "factor-base point is outside the target subgroup",
            ));
        }
        Ok(Self {
            base,
            order,
            generator,
            full_group,
        })
    }
    fn validate_target(&self, target: Point) -> Result<()> {
        if !self.base.curve().contains(Some(target))
            || (!self.full_group
                && self
                    .base
                    .curve()
                    .mul_inner(Some(target), self.order)
                    .is_some())
        {
            return Err(Error::Invalid("target is outside the target subgroup"));
        }
        Ok(())
    }
    fn check_row(&self, target: Point, relation: Relation) -> bool {
        relation.a < self.order
            && relation.b < self.order
            && relation.decomposition.i < self.base.representatives().len()
            && relation.decomposition.j < self.base.representatives().len()
            && self.base.curve().matches_linear_combination(
                (self.generator, relation.a),
                (target, relation.b),
                self.base.signed_points(relation.decomposition),
            )
    }
    fn check_multi_row(&self, summands: u8, target: Point, relation: MultiRelation) -> bool {
        let arity = relation.decomposition.arity();
        if arity != usize::from(summands)
            || relation.a >= self.order
            || relation.b >= self.order
            || relation
                .decomposition
                .summands()
                .iter()
                .any(|t| t.index >= self.base.representatives().len())
        {
            return false;
        }
        let (pts, len) = self.base.multi_signed_points(relation.decomposition);
        self.base.curve().matches_multi_linear_combination(
            (self.generator, relation.a),
            (target, relation.b),
            &pts[..len],
        )
    }
    /// Replay public `2..=4`-summand rows through sparse mod-`n` elimination.
    pub fn recover_from_multi_relations(
        &self,
        summands: u8,
        target: Point,
        relations: &[MultiRelation],
        max_proof_nodes: usize,
    ) -> Result<Option<MultiCertificate>> {
        if !(2..=4).contains(&summands) {
            return Err(Error::Invalid("summand count must be 2, 3, or 4"));
        }
        self.validate_target(target)?;
        if max_proof_nodes < 1 {
            return Err(Error::Invalid("empty proof-node budget"));
        }
        let mut system = SparseSystem::new(
            self.base.representatives().len(),
            self.order,
            max_proof_nodes,
        );
        let mut seen = BTreeSet::new();
        for (index, row) in relations.iter().copied().enumerate() {
            if !self.check_multi_row(summands, target, row) {
                return Err(Error::InvalidCertificate("public relation replay failed"));
            }
            let key = row
                .decomposition
                .key()
                .ok_or(Error::InvalidCertificate("zero factor-base row"))?;
            if !seen.insert(key) {
                return Err(Error::InvalidCertificate(
                    "duplicate signed factor-base row",
                ));
            }
            if let Some(dependency) = system.insert(row.decomposition, row.a, row.b, index)? {
                let certificate = MultiCertificate {
                    summands,
                    order: self.order,
                    generator: self.generator,
                    target,
                    scalar: dependency.scalar,
                    relations: relations[..=index].to_vec(),
                    weights: dependency.weights,
                };
                verify_multi_certificate(self.base, &certificate)?;
                return Ok(Some(certificate));
            }
        }
        Ok(None)
    }
    /// Collect exact `2..=4`-summand relations and recover through sparse mod-`n` elimination.
    pub fn solve_multi(
        &self,
        summands: u8,
        target: Point,
        config: &Config,
    ) -> Result<MultiSolveOutcome> {
        self.search_multi(summands, target, config, false, &mut ())
    }
    /// Profiled `2..=4`-summand search with exclusive phase accounting.
    pub fn solve_multi_profiled(
        &self,
        summands: u8,
        target: Point,
        config: &Config,
    ) -> Result<(MultiSolveOutcome, SearchPhases)> {
        let mut recorder = Recorder::start();
        let outcome = self.search_multi(summands, target, config, false, &mut recorder)?;
        Ok((outcome, recorder.finish()))
    }
    /// End-to-end recovery with a target-independent signed pair index.
    /// Setup of `index` is external and must be charged by the caller.
    /// The original sampler, sparse elimination and complete certificate
    /// verification are shared with the direct/algebraic search.
    pub fn solve_multi_indexed(
        &self,
        summands: u8,
        target: Point,
        config: &Config,
        index: &PairIndex<B>,
    ) -> Result<(MultiSolveOutcome, PairIndexStats)> {
        if !index.matches(self.base) {
            return Err(Error::Invalid("pair index does not match solver base"));
        }
        let mut workspace = index.workspace();
        let outcome = self.search_multi_with(
            summands,
            target,
            config,
            false,
            &mut (),
            Backend::Scalar,
            false,
            |m, q| index.decompose(m, q, &mut workspace),
            None,
        )?;
        Ok((outcome, workspace.stats().clone()))
    }
    /// Batch the lane-round decomposition interface while retaining the same
    /// walk, row checks, elimination and certificate path. This scalar adapter
    /// is the correctness control for an optional accelerator backend.
    pub fn solve_multi_indexed_batched(
        &self,
        summands: u8,
        target: Point,
        config: &Config,
        index: &PairIndex<B>,
    ) -> Result<(MultiSolveOutcome, PairIndexStats)> {
        if !index.matches(self.base) {
            return Err(Error::Invalid("pair index does not match solver base"));
        }
        let mut workspace = index.workspace();
        let mut batch =
            |m: u8, points: &[Option<Point>]| -> Result<Vec<Option<MultiSignedRelation>>> {
                points
                    .iter()
                    .map(|point| {
                        point.map_or(Ok(None), |point| index.decompose(m, point, &mut workspace))
                    })
                    .collect()
            };
        let outcome = self.search_multi_with(
            summands,
            target,
            config,
            false,
            &mut (),
            Backend::Scalar,
            false,
            |_, _| unreachable!("batch adapter handles every lane"),
            Some(&mut batch),
        )?;
        Ok((outcome, workspace.stats().clone()))
    }
    /// Run the indexed collector with a caller-supplied lane-round candidate
    /// screen. Each target receives two flags per canonical pair entry, in
    /// the order exposed by `PairIndex::screen_points`. The screen may skip
    /// work but never supplies accepted relations: exact CPU lookup and
    /// complete certificate replay remain mandatory.
    pub fn solve_multi_indexed_screened<F>(
        &self,
        target: Point,
        config: &Config,
        index: &PairIndex<B>,
        mut screen: F,
    ) -> Result<(MultiSolveOutcome, PairIndexStats)>
    where
        F: FnMut(&[Option<Point>]) -> Result<Vec<u8>>,
    {
        if !index.matches(self.base) || index.screen_bitmap().is_empty() {
            return Err(Error::Invalid("screened pair index or bitmap"));
        }
        let mut workspace = index.workspace();
        let width = index
            .stats()
            .entries
            .checked_mul(2)
            .ok_or(Error::ResourceLimit("screen width"))?;
        let mut batch =
            |_: u8, points: &[Option<Point>]| -> Result<Vec<Option<MultiSignedRelation>>> {
                let flags = screen(points)?;
                if flags.len() != width * points.len() {
                    return Err(Error::Invalid("screened lane mask length"));
                }
                points
                    .iter()
                    .enumerate()
                    .map(|(i, point)| {
                        point.map_or(Ok(None), |point| {
                            index.decompose_masked(
                                point,
                                &mut workspace,
                                &flags[i * width..(i + 1) * width],
                            )
                        })
                    })
                    .collect()
            };
        let outcome = self.search_multi_with(
            4,
            target,
            config,
            false,
            &mut (),
            Backend::Scalar,
            false,
            |_, _| unreachable!("screened batch handles every lane"),
            Some(&mut batch),
        )?;
        Ok((outcome, workspace.stats().clone()))
    }
    /// Indexed recovery with exclusive native search phases. These phases
    /// include instrumentation overhead and are for diagnosis, not speed claims.
    pub fn solve_multi_indexed_profiled(
        &self,
        summands: u8,
        target: Point,
        config: &Config,
        index: &PairIndex<B>,
    ) -> Result<(MultiSolveOutcome, PairIndexStats, SearchPhases)> {
        if !index.matches(self.base) {
            return Err(Error::Invalid("pair index does not match solver base"));
        }
        let mut workspace = index.workspace();
        let mut recorder = Recorder::start();
        let outcome = self.search_multi_with(
            summands,
            target,
            config,
            false,
            &mut recorder,
            Backend::Scalar,
            false,
            |m, q| index.decompose(m, q, &mut workspace),
            None,
        )?;
        Ok((outcome, workspace.stats().clone(), recorder.finish()))
    }
    /// Measure `2..=4`-summand relation counts on an identical public query prefix.
    pub fn relation_yield_multi(
        &self,
        summands: u8,
        target: Point,
        config: &Config,
    ) -> Result<(StopReason, SearchStats)> {
        match self.search_multi(summands, target, config, true, &mut ())? {
            MultiSolveOutcome::Exhausted { reason, stats } => Ok((reason, stats)),
            MultiSolveOutcome::Solved { .. } => {
                unreachable!("yield collection does not attempt recovery")
            }
        }
    }
    /// Profiled fixed-prefix `2..=4`-summand relation yield collection.
    pub fn relation_yield_multi_profiled(
        &self,
        summands: u8,
        target: Point,
        config: &Config,
    ) -> Result<(StopReason, SearchStats, SearchPhases)> {
        let mut recorder = Recorder::start();
        match self.search_multi(summands, target, config, true, &mut recorder)? {
            MultiSolveOutcome::Exhausted { reason, stats } => {
                Ok((reason, stats, recorder.finish()))
            }
            MultiSolveOutcome::Solved { .. } => {
                unreachable!("yield collection does not attempt recovery")
            }
        }
    }
    fn search_multi<P: Profiler>(
        &self,
        summands: u8,
        target: Point,
        config: &Config,
        yield_only: bool,
        profiler: &mut P,
    ) -> Result<MultiSolveOutcome> {
        let mut workspace = self.base.workspace();
        self.search_multi_with(
            summands,
            target,
            config,
            yield_only,
            profiler,
            if summands == 2 {
                self.base.backend()
            } else {
                Backend::Scalar
            },
            summands == 2 && self.base.uses_circuit(),
            |m, q| self.base.decompose_multi_inner(m, q, &mut workspace),
            None,
        )
    }
    #[allow(clippy::too_many_arguments)]
    fn search_multi_with<
        P: Profiler,
        D: FnMut(u8, Point) -> Result<Option<MultiSignedRelation>>,
    >(
        &self,
        summands: u8,
        target: Point,
        config: &Config,
        yield_only: bool,
        profiler: &mut P,
        backend: Backend,
        circuit_oracle: bool,
        mut decompose: D,
        mut batch_decompose: Option<
            &mut dyn FnMut(u8, &[Option<Point>]) -> Result<Vec<Option<MultiSignedRelation>>>,
        >,
    ) -> Result<MultiSolveOutcome> {
        if !(2..=4).contains(&summands) {
            return Err(Error::Invalid("summand count must be 2, 3, or 4"));
        }
        self.validate_target(target)?;
        if !(1..=1024).contains(&config.walk_lanes)
            || config.max_proof_nodes < 1
            || config.max_queries > u64::MAX - 1024
        {
            return Err(Error::Invalid(
                "invalid walk lanes, query budget, or proof budget",
            ));
        }
        let started = config.max_duration.map(|_| Instant::now());
        let expired = || {
            started
                .zip(config.max_duration)
                .is_some_and(|(start, limit)| start.elapsed() >= limit)
        };
        let mut stats = SearchStats {
            backend,
            ..SearchStats::default()
        };
        if config.max_queries == 0 {
            return Ok(MultiSolveOutcome::Exhausted {
                reason: StopReason::QueryBudget,
                stats,
            });
        }
        if expired() {
            return Ok(MultiSolveOutcome::Exhausted {
                reason: StopReason::TimeBudget,
                stats,
            });
        }
        let mut rng = SplitMix64(config.seed);
        let curve = self.base.curve();
        let mut jump_points = [None; 32];
        let mut jump_a = [0; 32];
        let mut jump_b = [0; 32];
        for i in 0..32 {
            jump_a[i] = rng.below(self.order);
            jump_b[i] = rng.below(self.order);
            jump_points[i] = curve.add_inner(
                curve.mul_inner(Some(self.generator), jump_a[i]),
                curve.mul_inner(Some(target), jump_b[i]),
            );
        }
        let lanes = config.walk_lanes;
        let mut points = vec![None; lanes];
        let mut a = vec![0; lanes];
        let mut b = vec![0; lanes];
        let mut steps = vec![None; lanes];
        for i in 0..lanes {
            a[i] = rng.below(self.order);
            b[i] = rng.below(self.order);
            points[i] = curve.add_inner(
                curve.mul_inner(Some(self.generator), a[i]),
                curve.mul_inner(Some(target), b[i]),
            );
        }
        let columns = self.base.representatives().len();
        let row_limit = if config.max_relations == 0 {
            4 * columns + 64
        } else {
            config.max_relations
        };
        let mut system =
            (!yield_only).then(|| SparseSystem::new(columns, self.order, config.max_proof_nodes));
        stats.proof_nodes = system.as_ref().map_or(0, SparseSystem::proof_nodes);
        let mut relations = Vec::new();
        let mut seen = BTreeSet::new();
        let mut batch = BatchScratch::default();
        profiler.enter(Phase::Bookkeeping);
        while stats.queries < config.max_queries {
            if expired() {
                return Ok(MultiSolveOutcome::Exhausted {
                    reason: StopReason::TimeBudget,
                    stats,
                });
            }
            profiler.enter(Phase::TargetWalk);
            for i in 0..lanes {
                let jump = (rng.next() & 31) as usize;
                a[i] = add_mod(a[i], jump_a[jump], self.order);
                b[i] = add_mod(b[i], jump_b[jump], self.order);
                steps[i] = jump_points[jump];
            }
            if lanes == 1 {
                points[0] = curve.add_inner(points[0], steps[0]);
            } else {
                curve.batch_add_inner(&mut points, &steps, &mut batch);
            }
            stats.generated_targets += lanes as u64;
            stats.lane_rounds += 1;
            let mut batch_rows = if let Some(ref mut batch) = batch_decompose {
                let rows = batch(summands, &points)?;
                if rows.len() != lanes {
                    return Err(Error::Invalid("batch decomposition result length"));
                }
                Some(rows)
            } else {
                None
            };
            profiler.enter(Phase::Bookkeeping);
            for i in 0..lanes {
                if stats.queries == config.max_queries {
                    break;
                }
                stats.queries += 1;
                let Some(query) = points[i] else {
                    continue;
                };
                stats.circuit_queries += u64::from(circuit_oracle);
                profiler.enter(Phase::Decomposition);
                let decomposition = if let Some(ref mut rows) = batch_rows {
                    rows[i].take()
                } else {
                    decompose(summands, query)?
                };
                profiler.enter(Phase::Bookkeeping);
                let Some(decomposition) = decomposition else {
                    continue;
                };
                let Some(key) = decomposition.key() else {
                    continue;
                };
                if !seen.insert(key) {
                    stats.duplicate_rows += 1;
                    continue;
                }
                if stats.relations == row_limit {
                    return Ok(MultiSolveOutcome::Exhausted {
                        reason: StopReason::RelationBudget,
                        stats,
                    });
                }
                let row = MultiRelation {
                    a: a[i],
                    b: b[i],
                    decomposition,
                };
                profiler.enter(Phase::RowValidation);
                let checked = self.check_multi_row(summands, target, row);
                profiler.enter(Phase::Bookkeeping);
                if !checked {
                    return Err(Error::InvalidCertificate(
                        "walk coefficient or point replay failed",
                    ));
                }
                stats.relations += 1;
                let Some(system) = system.as_mut() else {
                    continue;
                };
                profiler.enter(Phase::GraphRecovery);
                relations.push(row);
                let inserted = system.insert(decomposition, row.a, row.b, relations.len() - 1);
                profiler.enter(Phase::Bookkeeping);
                let dependency = match inserted {
                    Ok(value) => value,
                    Err(Error::ResourceLimit(_)) => {
                        stats.matrix_rank = system.rank();
                        stats.proof_nodes = system.proof_nodes();
                        return Ok(MultiSolveOutcome::Exhausted {
                            reason: StopReason::ProofBudget,
                            stats,
                        });
                    }
                    Err(error) => return Err(error),
                };
                stats.matrix_rank = system.rank();
                stats.proof_nodes = system.proof_nodes();
                if let Some(dependency) = dependency {
                    let certificate = MultiCertificate {
                        summands,
                        order: self.order,
                        generator: self.generator,
                        target,
                        scalar: dependency.scalar,
                        relations,
                        weights: dependency.weights,
                    };
                    profiler.enter(Phase::CertificateReplay);
                    verify_multi_certificate(self.base, &certificate)?;
                    profiler.enter(Phase::Bookkeeping);
                    return Ok(MultiSolveOutcome::Solved { certificate, stats });
                }
            }
        }
        Ok(MultiSolveOutcome::Exhausted {
            reason: StopReason::QueryBudget,
            stats,
        })
    }
    /// Replay public rows through the sparse solver, without a search or secret.
    /// This is useful for imported correctness certificates, not timing yield.
    pub fn recover_from_relations(
        &self,
        target: Point,
        relations: &[Relation],
        max_proof_nodes: usize,
    ) -> Result<Option<Certificate>> {
        self.validate_target(target)?;
        if max_proof_nodes < 1 {
            return Err(Error::Invalid("empty proof-node budget"));
        }
        let mut graph = GainGraph::new(
            self.base.representatives().len(),
            self.order,
            max_proof_nodes,
        );
        let mut seen = BTreeSet::new();
        for (index, row) in relations.iter().copied().enumerate() {
            if !self.check_row(target, row) {
                return Err(Error::InvalidCertificate("public relation replay failed"));
            }
            let key = row
                .decomposition
                .key()
                .ok_or(Error::InvalidCertificate("zero factor-base row"))?;
            if !seen.insert(key) {
                return Err(Error::InvalidCertificate(
                    "duplicate signed factor-base row",
                ));
            }
            if let Some(dependency) = graph.insert(row.decomposition, row.a, row.b, index)? {
                let certificate = Certificate {
                    order: self.order,
                    generator: self.generator,
                    target,
                    scalar: dependency.scalar,
                    relations: relations[..=index].to_vec(),
                    weights: dependency.weights,
                };
                verify_certificate(self.base, &certificate)?;
                return Ok(Some(certificate));
            }
        }
        Ok(None)
    }
    /// Collect exact algebraic relations and recover through distinct rows.
    /// The optional duration is a soft limit checked between lane batches.
    pub fn solve(&self, target: Point, config: &Config) -> Result<SolveOutcome> {
        self.search(target, config, false, &mut ())
    }
    /// Search with an exclusive wall-clock partition, including local replay.
    /// Clock overhead is charged and may affect soft time limits. Without a
    /// time limit, this uses the same queries, rows and recovery as `solve`.
    /// No reusable preparation, CLI work or independent replay is included.
    pub fn solve_profiled(
        &self,
        target: Point,
        config: &Config,
    ) -> Result<(SolveOutcome, SearchPhases)> {
        let mut recorder = Recorder::start();
        let outcome = self.search(target, config, false, &mut recorder)?;
        Ok((outcome, recorder.finish()))
    }
    /// Measure relation counts on the same public query prefix for every base.
    /// This skips recovery and never stops because a logarithm became available.
    /// Only `QueryBudget` completes the requested prefix; other stop reasons
    /// retain partial counts. No elapsed-time or performance claim is implied.
    pub fn relation_yield(
        &self,
        target: Point,
        config: &Config,
    ) -> Result<(StopReason, SearchStats)> {
        match self.search(target, config, true, &mut ())? {
            SolveOutcome::Exhausted { reason, stats } => Ok((reason, stats)),
            SolveOutcome::Solved { .. } => {
                unreachable!("yield collection does not attempt recovery")
            }
        }
    }
    /// Fixed-prefix collection with the same optional accounting as
    /// `solve_profiled`. Graph/recovery and certificate replay remain absent.
    pub fn relation_yield_profiled(
        &self,
        target: Point,
        config: &Config,
    ) -> Result<(StopReason, SearchStats, SearchPhases)> {
        let mut recorder = Recorder::start();
        match self.search(target, config, true, &mut recorder)? {
            SolveOutcome::Exhausted { reason, stats } => Ok((reason, stats, recorder.finish())),
            SolveOutcome::Solved { .. } => {
                unreachable!("yield collection does not attempt recovery")
            }
        }
    }
    fn search<P: Profiler>(
        &self,
        target: Point,
        config: &Config,
        yield_only: bool,
        profiler: &mut P,
    ) -> Result<SolveOutcome> {
        self.validate_target(target)?;
        if !(1..=1024).contains(&config.walk_lanes)
            || config.max_proof_nodes < 1
            || config.max_queries > u64::MAX - 1024
        {
            return Err(Error::Invalid(
                "invalid walk lanes, query budget, or proof budget",
            ));
        }
        let started = config.max_duration.map(|_| Instant::now());
        let expired = || {
            started
                .zip(config.max_duration)
                .is_some_and(|(start, limit)| start.elapsed() >= limit)
        };
        let mut stats = SearchStats {
            backend: self.base.backend(),
            ..SearchStats::default()
        };
        if config.max_queries == 0 {
            return Ok(SolveOutcome::Exhausted {
                reason: StopReason::QueryBudget,
                stats,
            });
        }
        if expired() {
            return Ok(SolveOutcome::Exhausted {
                reason: StopReason::TimeBudget,
                stats,
            });
        }
        let mut rng = SplitMix64(config.seed);
        let curve = self.base.curve();
        let mut jump_points = [None; 32];
        let mut jump_a = [0; 32];
        let mut jump_b = [0; 32];
        for i in 0..32 {
            jump_a[i] = rng.below(self.order);
            jump_b[i] = rng.below(self.order);
            jump_points[i] = curve.add_inner(
                curve.mul_inner(Some(self.generator), jump_a[i]),
                curve.mul_inner(Some(target), jump_b[i]),
            );
        }
        let lanes = config.walk_lanes;
        let mut points = vec![None; lanes];
        let mut a = vec![0; lanes];
        let mut b = vec![0; lanes];
        let mut steps = vec![None; lanes];
        for i in 0..lanes {
            a[i] = rng.below(self.order);
            b[i] = rng.below(self.order);
            points[i] = curve.add_inner(
                curve.mul_inner(Some(self.generator), a[i]),
                curve.mul_inner(Some(target), b[i]),
            );
        }
        let columns = self.base.representatives().len();
        let row_limit = if config.max_relations == 0 {
            4 * columns + 64
        } else {
            config.max_relations
        };
        let mut graph =
            (!yield_only).then(|| GainGraph::new(columns, self.order, config.max_proof_nodes));
        stats.proof_nodes = graph.as_ref().map_or(0, GainGraph::proof_nodes);
        let mut relations = Vec::new();
        let mut seen = BTreeSet::new();
        let mut batch = BatchScratch::default();
        let mut workspace = self.base.workspace();
        profiler.enter(Phase::Bookkeeping);
        while stats.queries < config.max_queries {
            if expired() {
                return Ok(SolveOutcome::Exhausted {
                    reason: StopReason::TimeBudget,
                    stats,
                });
            }
            profiler.enter(Phase::TargetWalk);
            for i in 0..lanes {
                let jump = (rng.next() & 31) as usize;
                a[i] = add_mod(a[i], jump_a[jump], self.order);
                b[i] = add_mod(b[i], jump_b[jump], self.order);
                steps[i] = jump_points[jump];
            }
            if lanes == 1 {
                points[0] = curve.add_inner(points[0], steps[0]);
            } else {
                curve.batch_add_inner(&mut points, &steps, &mut batch);
            }
            stats.generated_targets += lanes as u64;
            stats.lane_rounds += 1;
            profiler.enter(Phase::Bookkeeping);
            for i in 0..lanes {
                if stats.queries == config.max_queries {
                    break;
                }
                stats.queries += 1;
                let Some(query) = points[i] else {
                    continue;
                };
                stats.circuit_queries += u64::from(self.base.uses_circuit());
                profiler.enter(Phase::Decomposition);
                let decomposition = self.base.decompose_inner(query, &mut workspace)?;
                profiler.enter(Phase::Bookkeeping);
                let Some(decomposition) = decomposition else {
                    continue;
                };
                let Some(key) = decomposition.key() else {
                    continue;
                };
                if !seen.insert(key) {
                    stats.duplicate_rows += 1;
                    continue;
                }
                if stats.relations == row_limit {
                    return Ok(SolveOutcome::Exhausted {
                        reason: StopReason::RelationBudget,
                        stats,
                    });
                }
                let row = Relation {
                    a: a[i],
                    b: b[i],
                    decomposition,
                };
                profiler.enter(Phase::RowValidation);
                let checked = self.check_row(target, row);
                profiler.enter(Phase::Bookkeeping);
                if !checked {
                    return Err(Error::InvalidCertificate(
                        "walk coefficient or point replay failed",
                    ));
                }
                stats.relations += 1;
                let Some(graph) = graph.as_mut() else {
                    continue;
                };
                profiler.enter(Phase::GraphRecovery);
                relations.push(row);
                let inserted = graph.insert(decomposition, row.a, row.b, relations.len() - 1);
                profiler.enter(Phase::Bookkeeping);
                let dependency = match inserted {
                    Ok(value) => value,
                    Err(Error::ResourceLimit(_)) => {
                        stats.matrix_rank = graph.rank();
                        stats.proof_nodes = graph.proof_nodes();
                        return Ok(SolveOutcome::Exhausted {
                            reason: StopReason::ProofBudget,
                            stats,
                        });
                    }
                    Err(error) => return Err(error),
                };
                stats.matrix_rank = graph.rank();
                stats.proof_nodes = graph.proof_nodes();
                if let Some(dependency) = dependency {
                    let certificate = Certificate {
                        order: self.order,
                        generator: self.generator,
                        target,
                        scalar: dependency.scalar,
                        relations,
                        weights: dependency.weights,
                    };
                    profiler.enter(Phase::CertificateReplay);
                    verify_certificate(self.base, &certificate)?;
                    profiler.enter(Phase::Bookkeeping);
                    return Ok(SolveOutcome::Solved { certificate, stats });
                }
            }
        }
        Ok(SolveOutcome::Exhausted {
            reason: StopReason::QueryBudget,
            stats,
        })
    }
}

/// One-shot checked wrapper; use `PreparedSolver` to separate reusable setup.
pub fn solve<const B: u32>(
    base: &FactorBase<B>,
    order: u64,
    generator: Point,
    target: Point,
    config: &Config,
) -> Result<SolveOutcome> {
    PreparedSolver::new(base, order, generator)?.solve(target, config)
}

/// Check every public equation, distinct row, nontrivial cancellation, and key.
/// Local replay is a correctness check, not a signed independent PCC verdict.
pub fn verify_certificate<const B: u32>(
    base: &FactorBase<B>,
    certificate: &Certificate,
) -> Result<()> {
    let prepared = PreparedSolver::new(base, certificate.order, certificate.generator)?;
    prepared.validate_target(certificate.target)?;
    let n = certificate.order;
    if certificate.scalar >= n
        || certificate.weights.len() != certificate.relations.len()
        || certificate.weights.iter().filter(|&&w| w != 0).count() < 3
    {
        return Err(Error::InvalidCertificate(
            "invalid scalar, weight count, or dependency support",
        ));
    }
    let mut seen = BTreeSet::new();
    let mut columns = vec![0; base.representatives().len()];
    let (mut a, mut b) = (0, 0);
    for (row, &weight) in certificate.relations.iter().zip(&certificate.weights) {
        if weight >= n || !prepared.check_row(certificate.target, *row) {
            return Err(Error::InvalidCertificate(
                "relation or weight replay failed",
            ));
        }
        let key = row
            .decomposition
            .key()
            .ok_or(Error::InvalidCertificate("zero factor-base row"))?;
        if !seen.insert(key) {
            return Err(Error::InvalidCertificate(
                "duplicate signed factor-base row",
            ));
        }
        let signed = |negative: bool| {
            if negative && weight != 0 {
                n - weight
            } else {
                weight
            }
        };
        columns[row.decomposition.i] = add_mod(
            columns[row.decomposition.i],
            signed(row.decomposition.negative_i),
            n,
        );
        columns[row.decomposition.j] = add_mod(
            columns[row.decomposition.j],
            signed(row.decomposition.negative_j),
            n,
        );
        a = sub_mod(a, mul_mod(weight, row.a, n), n);
        b = sub_mod(b, mul_mod(weight, row.b, n), n);
    }
    if columns.iter().any(|&v| v != 0)
        || b == 0
        || add_mod(a, mul_mod(b, certificate.scalar, n), n) != 0
        || base
            .curve()
            .mul_inner(Some(certificate.generator), certificate.scalar)
            != Some(certificate.target)
    {
        return Err(Error::InvalidCertificate(
            "factor-base cancellation or scalar equation failed",
        ));
    }
    Ok(())
}

/// One-shot checked wrapper for `2..=4`-summand index calculus.
pub fn solve_multi<const B: u32>(
    base: &FactorBase<B>,
    summands: u8,
    order: u64,
    generator: Point,
    target: Point,
    config: &Config,
) -> Result<MultiSolveOutcome> {
    PreparedSolver::new(base, order, generator)?.solve_multi(summands, target, config)
}

/// Check every `2..=4`-summand public equation, distinct row, cancellation, and key.
/// Local replay is a correctness check, not a signed independent PCC verdict.
pub fn verify_multi_certificate<const B: u32>(
    base: &FactorBase<B>,
    certificate: &MultiCertificate,
) -> Result<()> {
    if !(2..=4).contains(&certificate.summands) {
        return Err(Error::InvalidCertificate("unsupported summand arity"));
    }
    let prepared = PreparedSolver::new(base, certificate.order, certificate.generator)?;
    prepared.validate_target(certificate.target)?;
    let n = certificate.order;
    let min_support = if certificate.summands == 2 || n > 13 {
        3
    } else {
        2
    };
    if certificate.scalar >= n
        || certificate.weights.len() != certificate.relations.len()
        || certificate.weights.iter().filter(|&&w| w != 0).count() < min_support
    {
        return Err(Error::InvalidCertificate(
            "invalid scalar, weight count, or dependency support",
        ));
    }
    let mut seen = BTreeSet::new();
    let mut columns = vec![0; base.representatives().len()];
    let (mut a, mut b) = (0, 0);
    for (row, &weight) in certificate.relations.iter().zip(&certificate.weights) {
        if weight >= n || !prepared.check_multi_row(certificate.summands, certificate.target, *row)
        {
            return Err(Error::InvalidCertificate(
                "relation or weight replay failed",
            ));
        }
        let key = row
            .decomposition
            .key()
            .ok_or(Error::InvalidCertificate("zero factor-base row"))?;
        if !seen.insert(key) {
            return Err(Error::InvalidCertificate(
                "duplicate signed factor-base row",
            ));
        }
        let signed = |negative: bool| {
            if negative && weight != 0 {
                n - weight
            } else {
                weight
            }
        };
        for term in row.decomposition.summands() {
            columns[term.index] = add_mod(columns[term.index], signed(term.negative), n);
        }
        a = sub_mod(a, mul_mod(weight, row.a, n), n);
        b = sub_mod(b, mul_mod(weight, row.b, n), n);
    }
    if columns.iter().any(|&v| v != 0)
        || b == 0
        || add_mod(a, mul_mod(b, certificate.scalar, n), n) != 0
        || base
            .curve()
            .mul_inner(Some(certificate.generator), certificate.scalar)
            != Some(certificate.target)
    {
        return Err(Error::InvalidCertificate(
            "factor-base cancellation or scalar equation failed",
        ));
    }
    Ok(())
}

pub(crate) struct SplitMix64(pub(crate) u64);
impl SplitMix64 {
    pub(crate) fn next(&mut self) -> u64 {
        self.0 = self.0.wrapping_add(0x9e3779b97f4a7c15);
        let mut z = self.0;
        z = (z ^ (z >> 30)).wrapping_mul(0xbf58476d1ce4e5b9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94d049bb133111eb);
        z ^ (z >> 31)
    }
    fn below(&mut self, modulus: u64) -> u64 {
        let threshold = modulus.wrapping_neg() % modulus;
        loop {
            let value = self.next();
            if value >= threshold {
                return value % modulus;
            }
        }
    }
}
