//! Explicit experimental composition of five prepared relation-collection paths.
//!
//! Defaults call the original joint prepared solver. Optional paths retain
//! checked witnesses and the unchanged version-one N+1-row certificate. Event
//! counters are development diagnostics, not calibrated costs or runtime data.

use crate::arithmetic::{hash_prime_by, inverse, random_below, RandomSource};
use crate::curve::{Curve, Point};
use crate::prepared::{self, PairTable};
use crate::reduction::{self, Certificate, Config, FactorBase, HashSeed, Relation};
use crate::relation_graph::{CycleDependency, Insertion, RelationGraph};
use crate::subgroup::{SubgroupContext, SubgroupPoint};
use crate::{integrity, invalid, overflow, BigUint, Error, Meter, Result};
use num_traits::{One, Zero};
use serde_json::{json, Value};

/// Explicit adding-walk setup and independent-anchor policy.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct WalkOptions {
    /// Number of prepared increments, 16 or 32.
    pub table_size: usize,
    /// Targets per independently sampled anchor, 16, 64 or 256.
    pub block_length: usize,
}
json_record!(
    WalkOptions,
    required {
        table_size,
        block_length
    },
    optional {}
);

/// Independently switchable native paths; defaults preserve the joint control.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Options {
    /// Retain sealed subgroup provenance instead of checking every query again.
    pub subgroup_provenance: bool,
    /// Complement batch size: 1 (checked affine control), 8, 32 or 128.
    pub batch_chunk: usize,
    /// Use slot-tagged weighted forest dependencies instead of dense elimination.
    pub relation_graph: bool,
    /// Additional candidate checks after the first witness: 0, 4 or 16.
    pub extra_scans: usize,
    /// Optional correlated target policy, with independently sampled anchors.
    pub walk: Option<WalkOptions>,
    /// Share public coefficient doubling chains for independent target sampling.
    pub joint_targets: bool,
}

// The direct map visitor rejects sequences and duplicate fields even after
// null. Reuse the existing no-procedural-macro record path in both repos.
struct OptionRecord {
    subgroup_provenance: Option<bool>,
    batch_chunk: Option<usize>,
    relation_graph: Option<bool>,
    extra_scans: Option<usize>,
    walk: Option<WalkOptions>,
    joint_targets: Option<bool>,
}
json_record!(
    OptionRecord,
    required {},
    optional {
        subgroup_provenance,
        batch_chunk,
        relation_graph,
        extra_scans,
        walk,
        joint_targets
    }
);

impl serde::Serialize for Options {
    fn serialize<S: serde::Serializer>(
        &self,
        serializer: S,
    ) -> std::result::Result<S::Ok, S::Error> {
        serde::Serialize::serialize(
            &OptionRecord {
                subgroup_provenance: Some(self.subgroup_provenance),
                batch_chunk: Some(self.batch_chunk),
                relation_graph: Some(self.relation_graph),
                extra_scans: Some(self.extra_scans),
                walk: self.walk.clone(),
                joint_targets: Some(self.joint_targets),
            },
            serializer,
        )
    }
}

impl<'de> serde::Deserialize<'de> for Options {
    fn deserialize<D: serde::Deserializer<'de>>(
        deserializer: D,
    ) -> std::result::Result<Self, D::Error> {
        struct OptionsVisitor;
        impl<'de> serde::de::Visitor<'de> for OptionsVisitor {
            type Value = Options;
            fn expecting(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
                formatter.write_str("an optimized options object")
            }
            fn visit_map<A: serde::de::MapAccess<'de>>(
                self,
                mut map: A,
            ) -> std::result::Result<Options, A::Error> {
                let (mut subgroup_provenance, mut batch_chunk, mut relation_graph) =
                    (None, None, None);
                let (mut extra_scans, mut walk, mut joint_targets) = (None, None, None);
                macro_rules! field {
                    ($field:ident) => {{
                        if $field.is_some() {
                            return Err(serde::de::Error::duplicate_field(stringify!($field)));
                        }
                        $field = Some(map.next_value()?);
                    }};
                }
                const FIELDS: &[&str] = &[
                    "subgroup_provenance",
                    "batch_chunk",
                    "relation_graph",
                    "extra_scans",
                    "walk",
                    "joint_targets",
                ];
                while let Some(key) = map.next_key::<String>()? {
                    match key.as_str() {
                        "subgroup_provenance" => field!(subgroup_provenance),
                        "batch_chunk" => field!(batch_chunk),
                        "relation_graph" => field!(relation_graph),
                        "extra_scans" => field!(extra_scans),
                        "walk" => field!(walk),
                        "joint_targets" => field!(joint_targets),
                        _ => return Err(serde::de::Error::unknown_field(&key, FIELDS)),
                    }
                }
                let defaults = Options::default();
                Ok(Options {
                    subgroup_provenance: subgroup_provenance
                        .unwrap_or(defaults.subgroup_provenance),
                    batch_chunk: batch_chunk.unwrap_or(defaults.batch_chunk),
                    relation_graph: relation_graph.unwrap_or(defaults.relation_graph),
                    extra_scans: extra_scans.unwrap_or(defaults.extra_scans),
                    walk: walk.unwrap_or(defaults.walk),
                    joint_targets: joint_targets.unwrap_or(defaults.joint_targets),
                })
            }
        }
        deserializer.deserialize_map(OptionsVisitor)
    }
}

impl Default for Options {
    fn default() -> Self {
        Self {
            subgroup_provenance: false,
            batch_chunk: 1,
            relation_graph: false,
            extra_scans: 0,
            walk: None,
            joint_targets: true,
        }
    }
}

impl Options {
    /// Check the supported draft policy choices before allocating or sampling.
    pub fn validate(&self) -> Result<()> {
        if !matches!(self.batch_chunk, 1 | 8 | 32 | 128) || !matches!(self.extra_scans, 0 | 4 | 16)
        {
            return Err(invalid("optimized batch or extra-scan policy"));
        }
        if self.extra_scans != 0 && !self.relation_graph {
            return Err(invalid(
                "cycle-aware witness choice requires the relation graph",
            ));
        }
        if let Some(walk) = &self.walk {
            walk_config(walk).validate()?;
        }
        Ok(())
    }

    fn is_control(&self) -> bool {
        !self.subgroup_provenance
            && self.batch_chunk == 1
            && !self.relation_graph
            && self.extra_scans == 0
            && self.walk.is_none()
    }
}

fn walk_config(options: &WalkOptions) -> crate::target_walk::Config {
    crate::target_walk::Config {
        table_size: options.table_size,
        block_length: options.block_length,
    }
}

/// Observable events, including setup and unused arithmetic; not timing units.
#[derive(Clone, Debug, Default)]
pub struct Statistics {
    pub(crate) prepared: prepared::Statistics,
    pub(crate) batch: crate::batch::BatchStatistics,
    pub(crate) policy: crate::witness_policy::Statistics,
    pub(crate) walk: crate::target_walk::Statistics,
    pub(crate) complements: u64,
    pub(crate) unused_complements: u64,
    pub(crate) trusted_queries: u64,
    graph_rows: u64,
    graph_tree_edges: u64,
    graph_zero_v_cycles: u64,
    graph_useful_dependencies: u64,
    graph_cycles_after_dependency: u64,
}

impl Statistics {
    /// Export event counts without attesting history or calibrated work.
    pub fn diagnostics(&self) -> Value {
        json!({
            "standing": "unpriced development events; not runtime or signed execution evidence",
            "prepared_pair_builds": self.prepared.preparations,
            "prepared_points": self.prepared.prepared_points,
            "prepared_queries": self.prepared.queries,
            "full_point_lookups": self.prepared.lookups,
            "arithmetic_replays": self.prepared.replays,
            "trusted_queries": self.trusted_queries,
            "complements_computed": self.complements,
            "unused_precomputed_complements": self.unused_complements,
            "batch": {
                "batches": self.batch.batches, "complements": self.batch.complements,
                "ordinary_inversions": self.batch.ordinary_inversions,
                "exceptional_fallbacks": self.batch.exceptional_fallbacks,
                "product_multiplications": self.batch.product_multiplications
            },
            "witness_policy": {
                "queries": self.policy.queries, "scan_calls": self.policy.scan_calls,
                "candidates": self.policy.candidates, "extra_scan_calls": self.policy.extra_scan_calls,
                "extra_candidates": self.policy.extra_candidates, "witnesses": self.policy.witnesses,
                "graph_probes": self.policy.graph_probes,
                "first_hit_selections": self.policy.first_hit_selections,
                "cycle_closing_selections": self.policy.cycle_closing_selections,
                "fallback_selections": self.policy.fallback_selections
            },
            "graph": {
                "rows": self.graph_rows, "tree_edges": self.graph_tree_edges,
                "zero_v_cycles": self.graph_zero_v_cycles,
                "useful_dependencies": self.graph_useful_dependencies,
                "cycles_screened_after_saved_dependency": self.graph_cycles_after_dependency
            },
            "walk": {
                "preparations": self.walk.preparations, "table_attempts": self.walk.table_attempts,
                "sampled_increment_labels": self.walk.sampled_increment_labels,
                "table_redraws": self.walk.table_redraws,
                "increment_points": self.walk.increment_points,
                "identity_increment_points": self.walk.identity_increment_points,
                "partition_seed_bytes": self.walk.partition_seed_bytes,
                "anchors": self.walk.anchors, "steps": self.walk.steps, "partitions": self.walk.partitions
            }
        })
    }
}

pub(crate) fn increment(value: &mut u64, amount: usize) -> Result<()> {
    *value = value
        .checked_add(u64::try_from(amount).map_err(|_| overflow("optimized statistics"))?)
        .ok_or_else(|| overflow("optimized statistics"))?;
    Ok(())
}

pub(crate) enum Query<'a> {
    Checked(&'a Point),
    Proven(&'a SubgroupPoint),
}

/// Solve with explicit policies, retaining full witness and certificate replay.
///
/// Adding walks change the coefficient stream and introduce correlation; no
/// independent-target coverage theorem is asserted for that optional policy.
/// Graph mode still collects exactly N+1 rows. It tries further fundamental
/// cycles before discarding a trial, and never relaxes the v1 verifier.
pub fn solve(
    curve: &Curve,
    target: &Point,
    config: &Config,
    options: &Options,
    rng: &mut impl RandomSource,
    statistics: &mut Statistics,
    meter: &mut Meter,
) -> Result<Certificate> {
    options.validate()?;
    if config.slots != 2 || config.trials == 0 {
        return Err(invalid(
            "optimized reduction requires two slots and nonzero trials",
        ));
    }
    if options.is_control() {
        let before = statistics.prepared.lookups;
        let result = if options.joint_targets {
            prepared::solve_joint(
                curve,
                target,
                config,
                rng,
                true,
                &mut statistics.prepared,
                meter,
            )
        } else {
            prepared::solve(
                curve,
                target,
                config,
                rng,
                true,
                &mut statistics.prepared,
                meter,
            )
        };
        increment(
            &mut statistics.complements,
            usize::try_from(statistics.prepared.lookups - before)
                .map_err(|_| overflow("complement statistics"))?,
        )?;
        return result;
    }
    meter.vector(config.slots, "factor-base slots")?;
    let context = SubgroupContext::new(curve);
    let g = context.generator();
    config.validate_hash_prime(curve, meter)?;
    if target == &Point::Infinity {
        crate::collector_metrics::phase("target_validation")?;
        context.validate(target, meter)?;
        return Ok(Certificate {
            version: 1,
            prime: BigUint::zero(),
            threshold: BigUint::zero(),
            seeds: vec![],
            relations: vec![],
            dependency: vec![],
            scalar: BigUint::zero(),
        });
    }
    let mut validated_target = None;
    let mut joint = None;
    for _ in 0..config.trials {
        crate::collector_metrics::phase("factor_base")?;
        meter.charge(1, "fresh-seed trial")?;
        let prime = match &config.hash_prime {
            Some(prime) => prime.clone(),
            None => hash_prime_by(curve.modulus(), rng, meter, |p, w| {
                curve.certifies_prime(p, w)
            })?,
        };
        let tau = reduction::threshold(curve, &prime, config, meter)?;
        let mut bases = Vec::with_capacity(2);
        for _ in 0..2 {
            bases.push(FactorBase::new(
                curve,
                prime.clone(),
                tau.clone(),
                HashSeed {
                    alpha: random_below(&(&prime - BigUint::one()), rng, meter)? + BigUint::one(),
                    beta: random_below(&prime, rng, meter)?,
                },
                meter,
            )?);
        }
        let indexes = reduction::indexed_bases(curve, &bases, rng, meter)?;
        let columns: usize = indexes.iter().map(std::collections::BTreeMap::len).sum();
        if columns > config.columns {
            return Err(Error::Limit("factor-base column policy".into()));
        }
        if indexes.iter().any(std::collections::BTreeMap::is_empty) {
            continue;
        }
        let required = columns
            .checked_add(1)
            .ok_or_else(|| overflow("relation count"))?;
        meter.vector(required, "optimized relation records")?;
        let mut graph = if options.relation_graph {
            Some(RelationGraph::new(
                [indexes[0].len(), indexes[1].len()],
                curve.order(),
                meter,
            )?)
        } else {
            None
        };
        if graph.is_none() {
            meter.vector(
                required
                    .checked_mul(columns)
                    .ok_or_else(|| overflow("relation matrix"))?,
                "relation matrix",
            )?;
        }
        let attempts = required
            .checked_mul(20)
            .ok_or_else(|| overflow("relation attempts"))?;
        let mut relations = Vec::with_capacity(required);
        let mut matrix = Vec::new();
        let mut saved_dependency: Option<CycleDependency> = None;
        let table =
            PairTable::from_indexes(curve, &bases, &indexes, &mut statistics.prepared, meter)?;
        // Preserve the mirror's boundary: reusable initial base preparation
        // precedes per-target validation; every retry remains charged online.
        if validated_target.is_none() {
            crate::collector_metrics::phase("target_validation")?;
            validated_target = Some(context.validate(target, meter)?);
        }
        let q = validated_target.as_ref().expect("validated target");
        crate::collector_metrics::phase("target_preparation")?;
        let mut walk = match &options.walk {
            Some(policy) => Some(crate::target_walk::TargetWalk::from_context(
                &context,
                q,
                walk_config(policy),
                rng,
                &mut statistics.walk,
                meter,
            )?),
            None => None,
        };
        for _ in 0..attempts {
            crate::collector_metrics::phase("relation_target")?;
            let (point, u, v) = if let Some(walk) = &mut walk {
                let next = walk.next_trusted(rng, &mut statistics.walk, meter)?;
                (next.subgroup_point, next.labels.u, next.labels.v)
            } else {
                let u = random_below(curve.order(), rng, meter)?;
                let v = random_below(curve.order(), rng, meter)?;
                let point = if options.joint_targets {
                    if joint.is_none() {
                        joint = Some(context.joint_table(&g, q, meter)?);
                    }
                    joint
                        .as_ref()
                        .expect("initialized joint table")
                        .evaluate(&u, &v, meter)?
                } else {
                    context.add(
                        &context.mul(&g, &u, meter)?,
                        &context.mul(q, &v, meter)?,
                        meter,
                    )?
                };
                (point, u, v)
            };
            crate::collector_metrics::phase("relation_search")?;
            let query = if options.subgroup_provenance {
                Query::Proven(&point)
            } else {
                Query::Checked(point.point())
            };
            let points = table.decompose_configured(
                query,
                options,
                statistics,
                |points, work| {
                    let left = *indexes[0]
                        .get(&points[0])
                        .ok_or_else(|| integrity("left witness index"))?;
                    let right = *indexes[1]
                        .get(&points[1])
                        .ok_or_else(|| integrity("right witness index"))?;
                    match &mut graph {
                        Some(graph) => graph.would_close(left, right, work),
                        None => Ok(false),
                    }
                },
                meter,
            )?;
            if let Some(points) = points {
                crate::collector_metrics::phase("matrix_build")?;
                let relation = Relation { u, v, points };
                if let Some(graph) = &mut graph {
                    increment(&mut statistics.graph_rows, 1)?;
                    let left = *indexes[0]
                        .get(&relation.points[0])
                        .ok_or_else(|| integrity("left relation index"))?;
                    let right = *indexes[1]
                        .get(&relation.points[1])
                        .ok_or_else(|| integrity("right relation index"))?;
                    if saved_dependency.is_some() && graph.would_close(left, right, meter)? {
                        increment(&mut statistics.graph_cycles_after_dependency, 1)?;
                    } else {
                        match graph.insert(
                            left,
                            right,
                            relations.len(),
                            &relation.u,
                            &relation.v,
                            meter,
                        )? {
                            Insertion::Tree => increment(&mut statistics.graph_tree_edges, 1)?,
                            Insertion::ZeroV { combined_u } => {
                                if !combined_u.is_zero() {
                                    return Err(integrity("zero-v cycle group replay"));
                                }
                                increment(&mut statistics.graph_zero_v_cycles, 1)?;
                            }
                            Insertion::Dependency(dependency) => {
                                increment(&mut statistics.graph_useful_dependencies, 1)?;
                                saved_dependency = Some(dependency);
                            }
                        }
                    }
                } else {
                    matrix.push(reduction::matrix_row(&relation, &indexes, columns)?);
                }
                relations.push(relation);
                if relations.len() == required {
                    break;
                }
            }
        }
        if relations.len() != required {
            continue;
        }
        crate::collector_metrics::phase("linear_algebra")?;
        let dependency = if options.relation_graph {
            let Some(saved) = saved_dependency else {
                continue;
            };
            meter.vector(required, "graph certificate dependency")?;
            let mut dense = vec![BigUint::zero(); required];
            for (row, coefficient) in saved.coefficients {
                let cell = dense
                    .get_mut(row)
                    .ok_or_else(|| integrity("cycle provenance row"))?;
                *cell = (&*cell + coefficient) % curve.order();
            }
            let combined = reduction::combined_scalars(&relations, &dense, curve.order());
            if combined != (saved.combined_u, saved.combined_v) {
                return Err(integrity("cycle coefficient replay"));
            }
            dense
        } else {
            reduction::row_dependency(&matrix, curve.order(), meter)?
        };
        let (u, v) = reduction::combined_scalars(&relations, &dependency, curve.order());
        if v.is_zero() {
            continue;
        }
        crate::collector_metrics::phase("recovery_check")?;
        let scalar = (curve.order() - u) * inverse(&v, curve.order())? % curve.order();
        if curve.mul(curve.generator(), &scalar, meter)? != *target {
            return Err(integrity("optimized scalar replay"));
        }
        let certificate = Certificate {
            version: 1,
            prime,
            threshold: tau,
            seeds: bases.iter().map(|b| b.seed().clone()).collect(),
            relations,
            dependency,
            scalar,
        };
        reduction::verify_with_rng(curve, target, &certificate, rng, meter)?;
        return Ok(certificate);
    }
    Err(Error::Limit("fresh-seed trials exhausted".into()))
}
