//! Reusable exact point tables for two-slot prime-field relation collection.
//! Preparation is complete, query order is selector order, and every returned
//! witness is replayed through the original arithmetic predicates. Hash work
//! and allocation costs are not calibrated by the native resource meter.

use crate::arithmetic::{RandomSource, Seeded};
use crate::curve::{Curve, Point};
use crate::reduction::{self, Certificate, Config, FactorBase};
use crate::subgroup::SubgroupPoint;
use crate::{integrity, invalid, overflow, BigUint, Meter, Result};
use num_traits::{One, Zero};
use std::cell::RefCell;
use std::collections::{hash_map::RandomState, BTreeMap, HashMap};
use std::hash::BuildHasher;

/// Observable events, not calibrated work units or runtime measurements.
#[derive(Clone, Debug, Default)]
pub struct Statistics {
    /// Complete pair preparations, including fresh-trial rebuilds.
    pub preparations: u64,
    /// Total validated points retained across completed preparations.
    pub prepared_points: u64,
    /// Valid subgroup queries begun, including misses and later limit errors.
    pub queries: u64,
    /// Derived candidates looked up by full point equality.
    pub lookups: u64,
    /// Witnesses passing original arithmetic membership and sum replay.
    pub replays: u64,
}

fn add(value: &mut u64, amount: usize) -> Result<()> {
    *value = value
        .checked_add(u64::try_from(amount).map_err(|_| overflow("prepared statistics"))?)
        .ok_or_else(|| overflow("prepared statistics"))?;
    Ok(())
}

/// A complete immutable pair bound to its own curve and factor-base seeds.
/// It cannot be deserialized or built publicly from an untrusted partial list.
/// Hash tables select membership only; their iteration order selects no witness.
pub struct PairTable<S = RandomState> {
    curve: Curve,
    bases: [FactorBase; 2],
    ordered: [Vec<Point>; 2],
    // One exact map per slot serves membership, matrix columns and graph IDs.
    // A physical point in both slots has two distinct global column numbers.
    columns: [HashMap<Point, usize, S>; 2],
}

impl PairTable {
    /// Enumerate and validate both bases once, independently of label randomness.
    /// Reuse this object for any number of public query points on this curve.
    pub fn new(
        curve: &Curve,
        bases: &[FactorBase],
        statistics: &mut Statistics,
        meter: &mut Meter,
    ) -> Result<Self> {
        if bases.len() != 2 {
            return Err(invalid("prepared pair requires exactly two bases"));
        }
        let mut rng = Seeded(0x706169727461626c);
        let points = [
            bases[0].enumerate(curve, &mut rng, meter)?,
            bases[1].enumerate(curve, &mut rng, meter)?,
        ];
        Self::from_complete_points(curve, bases, points, RandomState::new(), statistics, meter)
    }

    // Only the reduction's already-complete, validated enumerations enter here.
    // Re-enumerating them would repeat root extraction and consume label RNG.
    pub(crate) fn from_indexes(
        curve: &Curve,
        bases: &[FactorBase],
        indexes: &[BTreeMap<Point, usize>],
        statistics: &mut Statistics,
        meter: &mut Meter,
    ) -> Result<Self> {
        if bases.len() != 2 || indexes.len() != 2 {
            return Err(invalid("prepared pair requires exactly two indexed bases"));
        }
        let table = Self::from_complete_points(
            curve,
            bases,
            [
                indexes[0].keys().cloned().collect(),
                indexes[1].keys().cloned().collect(),
            ],
            RandomState::new(),
            statistics,
            meter,
        )?;
        for (slot, index) in indexes.iter().enumerate() {
            if index.len() != table.columns[slot].len()
                || index
                    .iter()
                    .any(|(point, column)| table.columns[slot].get(point) != Some(column))
            {
                return Err(integrity("prepared column mapping"));
            }
        }
        Ok(table)
    }
}

impl<S: BuildHasher + Clone> PairTable<S> {
    pub(crate) fn from_complete_points(
        curve: &Curve,
        bases: &[FactorBase],
        points: [Vec<Point>; 2],
        hasher: S,
        statistics: &mut Statistics,
        meter: &mut Meter,
    ) -> Result<Self> {
        if bases.len() != 2 {
            return Err(invalid("prepared pair requires exactly two bases"));
        }
        let mut build = |base: &FactorBase,
                         offset: usize,
                         mut points: Vec<Point>|
         -> Result<(Vec<Point>, HashMap<Point, usize, S>)> {
            if base.prime() < &(curve.modulus() << 1) || base.prime() > &(curve.modulus() << 2) {
                return Err(invalid("prepared base belongs to a different field"));
            }
            meter.vector(points.len(), "prepared selector points")?;
            let mut keyed = Vec::with_capacity(points.len());
            let mut columns = HashMap::with_hasher(hasher.clone());
            columns
                .try_reserve(points.len())
                .map_err(|_| crate::Error::Limit("prepared hash allocation".into()))?;
            meter.vector(columns.capacity(), "prepared hash capacity")?;
            // BTreeMap's original column order is the full Point order, not
            // enumeration or selector order. Preserve it before sorting scans.
            points.sort();
            for (local, point) in points.into_iter().enumerate() {
                meter.charge(1, "prepared full point key")?;
                let selector =
                    (&base.seed().alpha * curve.encode(&point)? + &base.seed().beta) % base.prime();
                if &selector >= base.threshold()
                    || columns
                        .insert(
                            point.clone(),
                            offset
                                .checked_add(local)
                                .ok_or_else(|| overflow("prepared column"))?,
                        )
                        .is_some()
                {
                    return Err(integrity("invalid or repeated prepared point"));
                }
                keyed.push((selector, point));
            }
            keyed.sort_by(|a, b| a.0.cmp(&b.0));
            if keyed.windows(2).any(|p| p[0].0 == p[1].0) {
                return Err(integrity("duplicate prepared selector"));
            }
            Ok((keyed.into_iter().map(|(_, point)| point).collect(), columns))
        };
        let [left, right] = points;
        let right_offset = left.len();
        let (left, left_columns) = build(&bases[0], 0, left)?;
        let (right, right_columns) = build(&bases[1], right_offset, right)?;
        let total = left
            .len()
            .checked_add(right.len())
            .ok_or_else(|| overflow("prepared point count"))?;
        add(&mut statistics.prepared_points, total)?;
        add(&mut statistics.preparations, 1)?;
        Ok(Self {
            curve: curve.clone(),
            bases: [bases[0].clone(), bases[1].clone()],
            ordered: [left, right],
            columns: [left_columns, right_columns],
        })
    }

    /// Exact global column for this slot and canonical point.
    pub(crate) fn column(&self, slot: usize, point: &Point) -> Result<usize> {
        self.columns
            .get(slot)
            .and_then(|columns| columns.get(point))
            .copied()
            .ok_or_else(|| integrity("relation point missing from slot base"))
    }

    /// Build a v1 row from the same columns used by membership and the graph.
    pub(crate) fn matrix_row(&self, relation: &reduction::Relation) -> Result<Vec<BigUint>> {
        if relation.points.len() != 2 {
            return Err(integrity("relation slot count"));
        }
        let count = self.columns[0]
            .len()
            .checked_add(self.columns[1].len())
            .ok_or_else(|| overflow("relation columns"))?;
        let mut row = vec![BigUint::zero(); count];
        for (slot, point) in relation.points.iter().enumerate() {
            let column = self.column(slot, point)?;
            *row.get_mut(column)
                .ok_or_else(|| integrity("prepared column range"))? = BigUint::one();
        }
        Ok(row)
    }

    /// Return the same first witness as the final-slot selector oracle.
    /// `smallest_first` compares selector limits (ties keep slot zero), not
    /// realized cardinalities. Exhaustion is None; a resource error stays Err.
    pub fn decompose(
        &self,
        target: &Point,
        smallest_first: bool,
        statistics: &mut Statistics,
        meter: &mut Meter,
    ) -> Result<Option<Vec<Point>>> {
        if !self.curve.in_subgroup(target, meter)? {
            return Err(invalid("prepared query outside the certified subgroup"));
        }
        self.decompose_validated(target, smallest_first, statistics, meter)
    }

    // Only an opaque point admitted by subgroup validation or checked closure
    // reaches this path. Full curve/subgroup equality binds the owned Curve
    // clone; hash lookup still supplies no validation or witness trust.
    pub(crate) fn decompose_subgroup(
        &self,
        target: &SubgroupPoint,
        smallest_first: bool,
        statistics: &mut Statistics,
        meter: &mut Meter,
    ) -> Result<Option<Vec<Point>>> {
        self.decompose_validated(
            target.for_curve(&self.curve)?,
            smallest_first,
            statistics,
            meter,
        )
    }

    // Coefficients never enter this API. The optional callback sees only a
    // replayed, slot-ordered witness and graph connectivity.
    pub(crate) fn decompose_configured(
        &self,
        query: crate::optimized::Query<'_>,
        options: &crate::optimized::Options,
        statistics: &mut crate::optimized::Statistics,
        mut closes: impl FnMut(&[Point], &mut Meter) -> Result<bool>,
        meter: &mut Meter,
    ) -> Result<Option<Vec<Point>>> {
        use crate::optimized::{increment, Query};
        use crate::witness_policy::{self, ScanStep};
        if options.batch_chunk == 1 && options.extra_scans == 0 {
            let before = statistics.prepared.lookups;
            let result = match query {
                Query::Checked(point) => {
                    self.decompose(point, true, &mut statistics.prepared, meter)
                }
                Query::Proven(point) => {
                    point.for_curve(&self.curve)?;
                    increment(&mut statistics.trusted_queries, 1)?;
                    self.decompose_subgroup(point, true, &mut statistics.prepared, meter)
                }
            };
            increment(
                &mut statistics.complements,
                usize::try_from(statistics.prepared.lookups - before)
                    .map_err(|_| overflow("prepared complement events"))?,
            )?;
            return result;
        }
        let target = match query {
            Query::Checked(point) => {
                if !self.curve.in_subgroup(point, meter)? {
                    return Err(invalid("prepared query outside the certified subgroup"));
                }
                point
            }
            Query::Proven(point) => {
                let point = point.for_curve(&self.curve)?;
                increment(&mut statistics.trusted_queries, 1)?;
                point
            }
        };
        add(&mut statistics.prepared.queries, 1)?;
        let first = usize::from(self.bases[1].threshold() < self.bases[0].threshold());
        let last = 1 - first;
        let ordered = &self.ordered[first];
        let mut position = 0usize;
        let mut buffer = Vec::new();
        let mut offset = 0usize;
        let mut computed = 0usize;
        let mut seen_witness = false;
        let mut extra_remaining = options.extra_scans;
        let mut policy = std::mem::take(&mut statistics.policy);
        let result = witness_policy::choose(
            options.extra_scans,
            |work| {
                if position == ordered.len() {
                    return Ok(ScanStep::Exhausted);
                }
                if offset == buffer.len() {
                    let chunk = if seen_witness {
                        options.batch_chunk.min(extra_remaining)
                    } else {
                        options.batch_chunk
                    };
                    if chunk == 0 {
                        return Err(integrity("witness cursor exceeded extra-scan cap"));
                    }
                    let end = position.saturating_add(chunk).min(ordered.len());
                    if options.batch_chunk == 1 {
                        work.vector(1, "prepared complement buffer")?;
                        buffer = vec![self.curve.add(
                            target,
                            &self.curve.negate(&ordered[position])?,
                            work,
                        )?];
                    } else {
                        buffer = crate::batch::complement_chunk_with_statistics(
                            &self.curve,
                            target,
                            &ordered[position..end],
                            &mut statistics.batch,
                            work,
                        )?;
                    }
                    if buffer.len() != end - position {
                        return Err(integrity("prepared complement chunk length"));
                    }
                    computed = computed
                        .checked_add(buffer.len())
                        .ok_or_else(|| overflow("computed complements"))?;
                    increment(&mut statistics.complements, buffer.len())?;
                    offset = 0;
                }
                if seen_witness {
                    extra_remaining = extra_remaining
                        .checked_sub(1)
                        .ok_or_else(|| integrity("witness cursor extra-scan accounting"))?;
                }
                work.charge(1, "prepared pair candidate")?;
                let point = ordered[position].clone();
                let complement = buffer[offset].clone();
                position += 1;
                offset += 1;
                add(&mut statistics.prepared.lookups, 1)?;
                if !self.columns[last].contains_key(&complement) {
                    return Ok(ScanStep::Miss);
                }
                let mut witness = vec![point, complement];
                if first == 1 {
                    witness.swap(0, 1);
                }
                let mut sum = Point::Infinity;
                for (base, point) in self.bases.iter().zip(&witness) {
                    if !base.contains(&self.curve, point, work)? {
                        return Err(integrity("prepared policy witness membership replay"));
                    }
                    sum = self.curve.add(&sum, point, work)?;
                }
                if &sum != target {
                    return Err(integrity("prepared policy witness sum replay"));
                }
                add(&mut statistics.prepared.replays, 1)?;
                seen_witness = true;
                Ok(ScanStep::Witness(witness))
            },
            |witness, work| closes(witness, work),
            &mut policy,
            meter,
        );
        statistics.policy = policy;
        // Already computed batch tails are charged by the arithmetic kernel,
        // even when witness selection does not inspect or retain them.
        increment(
            &mut statistics.unused_complements,
            computed
                .checked_sub(position)
                .ok_or_else(|| integrity("prepared batch tail accounting"))?,
        )?;
        Ok(result?.map(|selection| selection.witness))
    }

    fn decompose_validated(
        &self,
        target: &Point,
        smallest_first: bool,
        statistics: &mut Statistics,
        meter: &mut Meter,
    ) -> Result<Option<Vec<Point>>> {
        add(&mut statistics.queries, 1)?;
        let first =
            usize::from(smallest_first && self.bases[1].threshold() < self.bases[0].threshold());
        let last = 1 - first;
        for point in &self.ordered[first] {
            meter.charge(1, "prepared pair candidate")?;
            let complement = self.curve.add(target, &self.curve.negate(point)?, meter)?;
            add(&mut statistics.lookups, 1)?;
            if !self.columns[last].contains_key(&complement) {
                continue;
            }
            let mut witness = vec![point.clone(), complement];
            if first == 1 {
                witness.swap(0, 1);
            }
            let mut sum = Point::Infinity;
            for (base, point) in self.bases.iter().zip(&witness) {
                // Full arithmetic replay, independent of the lookup table.
                if !base.contains(&self.curve, point, meter)? {
                    return Err(integrity("prepared witness membership replay"));
                }
                sum = self.curve.add(&sum, point, meter)?;
            }
            if &sum != target {
                return Err(integrity("prepared witness sum replay"));
            }
            add(&mut statistics.replays, 1)?;
            return Ok(Some(witness));
        }
        Ok(None)
    }
}

/// Collect two-slot relations using one prepared pair per fresh-seed trial.
/// Original matrix construction, coefficients, elimination and certificate
/// verification are unchanged. No table persists into a different trial.
pub fn solve(
    curve: &Curve,
    target: &Point,
    config: &Config,
    rng: &mut impl RandomSource,
    smallest_first: bool,
    statistics: &mut Statistics,
    meter: &mut Meter,
) -> Result<Certificate> {
    solve_using(
        curve,
        target,
        config,
        rng,
        smallest_first,
        statistics,
        false,
        meter,
    )
}

/// Use the same prepared pair search with a reusable joint target table.
/// Only public coefficient arithmetic changes. Original subgroup validation,
/// label randomness, witness selection and certificate replay remain in place.
pub fn solve_joint(
    curve: &Curve,
    target: &Point,
    config: &Config,
    rng: &mut impl RandomSource,
    smallest_first: bool,
    statistics: &mut Statistics,
    meter: &mut Meter,
) -> Result<Certificate> {
    solve_using(
        curve,
        target,
        config,
        rng,
        smallest_first,
        statistics,
        true,
        meter,
    )
}

fn solve_using(
    curve: &Curve,
    target: &Point,
    config: &Config,
    rng: &mut impl RandomSource,
    smallest_first: bool,
    statistics: &mut Statistics,
    joint_targets: bool,
    meter: &mut Meter,
) -> Result<Certificate> {
    if config.slots != 2 {
        return Err(invalid("prepared relation collection requires two slots"));
    }
    let statistics = RefCell::new(statistics);
    reduction::solve_with_target_preparation(
        curve,
        target,
        config,
        rng,
        |c, bases, indexes, work| {
            PairTable::from_indexes(c, bases, indexes, &mut statistics.borrow_mut(), work)
        },
        |_, _, table, query, work| {
            table.decompose(query, smallest_first, &mut statistics.borrow_mut(), work)
        },
        joint_targets,
        meter,
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Error, Limits};
    use std::hash::{BuildHasherDefault, Hasher};

    fn curve(meter: &mut Meter) -> Curve {
        Curve::new(
            17u8.into(),
            2u8.into(),
            2u8.into(),
            19u8.into(),
            Point::Affine {
                x: 5u8.into(),
                y: 1u8.into(),
            },
            meter,
        )
        .unwrap()
    }
    fn bases(curve: &Curve, meter: &mut Meter) -> Vec<FactorBase> {
        [1u8, 3]
            .into_iter()
            .map(|alpha| {
                FactorBase::new(
                    curve,
                    37u8.into(),
                    12u8.into(),
                    reduction::HashSeed {
                        alpha: alpha.into(),
                        beta: 4u8.into(),
                    },
                    meter,
                )
                .unwrap()
            })
            .collect()
    }
    #[derive(Default)]
    struct ConstantHash;
    impl Hasher for ConstantHash {
        fn finish(&self) -> u64 {
            0
        }
        fn write(&mut self, _: &[u8]) {}
    }
    #[test]
    fn shared_columns_match_independent_tree_rows_even_with_hash_collisions() {
        let mut meter = Meter::new(Limits::default());
        let curve = curve(&mut meter);
        let bases = bases(&curve, &mut meter);
        let old = reduction::indexed_bases(&curve, &bases, &mut Seeded(3), &mut meter).unwrap();
        let points = [
            bases[0]
                .enumerate(&curve, &mut Seeded(3), &mut meter)
                .unwrap(),
            bases[1]
                .enumerate(&curve, &mut Seeded(3), &mut meter)
                .unwrap(),
        ];
        let table = PairTable::from_complete_points(
            &curve,
            &bases,
            points,
            BuildHasherDefault::<ConstantHash>::default(),
            &mut Statistics::default(),
            &mut meter,
        )
        .unwrap();
        let columns = old.iter().map(BTreeMap::len).sum();
        for (slot, index) in old.iter().enumerate() {
            for (point, &column) in index {
                assert_eq!(table.column(slot, point).unwrap(), column);
            }
        }
        let left = old[0].keys().next().unwrap().clone();
        let right = old[1].keys().next().unwrap().clone();
        let relation = reduction::Relation {
            u: BigUint::zero(),
            v: BigUint::zero(),
            points: vec![left, right],
        };
        assert_eq!(
            table.matrix_row(&relation).unwrap(),
            reduction::matrix_row(&relation, &old, columns).unwrap()
        );
        assert!(table.column(1, &relation.points[1]).unwrap() >= old[0].len());
        let foreign = Point::Infinity;
        assert!(table.column(0, &foreign).is_err());
    }
    #[test]
    fn shared_columns_keep_equal_physical_points_in_distinct_graph_slots() {
        let mut meter = Meter::new(Limits::default());
        let curve = curve(&mut meter);
        let base = bases(&curve, &mut meter).remove(0);
        let points = base.enumerate(&curve, &mut Seeded(5), &mut meter).unwrap();
        let table = PairTable::from_complete_points(
            &curve,
            &[base.clone(), base],
            [points.clone(), points.clone()],
            BuildHasherDefault::<ConstantHash>::default(),
            &mut Statistics::default(),
            &mut meter,
        )
        .unwrap();
        let point = points.first().unwrap();
        let left = table.column(0, point).unwrap();
        let right = table.column(1, point).unwrap();
        assert!(left < points.len());
        assert!(right >= points.len());
        let graph = crate::relation_graph::RelationGraph::new(
            [points.len(), points.len()],
            curve.order(),
            &mut meter,
        )
        .unwrap();
        assert!(!graph.would_close(left, right, &mut meter).unwrap());
    }
    #[test]
    fn constant_hashes_keep_complete_answers_and_exact_point_equality() {
        let mut meter = Meter::new(Limits::default());
        let curve = curve(&mut meter);
        let bases = bases(&curve, &mut meter);
        let points = [
            bases[0]
                .enumerate(&curve, &mut Seeded(1), &mut meter)
                .unwrap(),
            bases[1]
                .enumerate(&curve, &mut Seeded(1), &mut meter)
                .unwrap(),
        ];
        let mut statistics = Statistics::default();
        let table = PairTable::from_complete_points(
            &curve,
            &bases,
            points,
            BuildHasherDefault::<ConstantHash>::default(),
            &mut statistics,
            &mut meter,
        )
        .unwrap();
        let normal =
            PairTable::new(&curve, &bases, &mut Statistics::default(), &mut meter).unwrap();
        for k in 0..19u8 {
            let target = curve.mul(curve.generator(), &k.into(), &mut meter).unwrap();
            assert_eq!(
                table
                    .decompose(&target, true, &mut statistics, &mut meter)
                    .unwrap(),
                normal
                    .decompose(&target, true, &mut Statistics::default(), &mut meter)
                    .unwrap()
            );
        }
        assert!(!table.columns[0].contains_key(&Point::Infinity));
        for point in &table.ordered[0] {
            let Point::Affine { x, y } = point else {
                unreachable!()
            };
            assert!(!table.columns[0].contains_key(&Point::Affine {
                x: x + curve.modulus(),
                y: y.clone()
            }));
        }
    }
    #[test]
    fn original_arithmetic_rejects_a_forged_table_hit() {
        let mut meter = Meter::new(Limits::default());
        let curve = curve(&mut meter);
        let bases = bases(&curve, &mut meter);
        let mut statistics = Statistics::default();
        let mut table = PairTable::new(&curve, &bases, &mut statistics, &mut meter).unwrap();
        let foreign = (1..19u8)
            .map(|k| curve.mul(curve.generator(), &k.into(), &mut meter).unwrap())
            .find(|p| !table.columns[1].contains_key(p))
            .unwrap();
        let target = curve
            .add(&table.ordered[0][0], &foreign, &mut meter)
            .unwrap();
        table.columns[1].insert(foreign, usize::MAX);
        assert!(matches!(
            table.decompose(&target, false, &mut statistics, &mut meter),
            Err(Error::Integrity(_))
        ));
        assert_eq!(statistics.replays, 0);
    }
    #[test]
    fn provenance_queries_keep_first_witness_and_remove_only_revalidation() {
        use crate::subgroup::SubgroupContext;
        let mut setup = Meter::new(Limits::default());
        let curve = curve(&mut setup);
        let bases = bases(&curve, &mut setup);
        let table = PairTable::new(&curve, &bases, &mut Statistics::default(), &mut setup).unwrap();
        let context = SubgroupContext::new(&curve);
        for scalar in 0..19u8 {
            let admitted = context
                .mul(&context.generator(), &scalar.into(), &mut setup)
                .unwrap();
            for smallest in [false, true] {
                let mut checked = Meter::new(Limits::default());
                let mut trusted = Meter::new(Limits::default());
                let mut subgroup = Meter::new(Limits::default());
                let (valid, subgroup_groups) =
                    crate::collector_metrics::observe_group_calls(&mut subgroup, |work| {
                        curve.in_subgroup(admitted.point(), work).unwrap()
                    });
                assert!(valid);
                let mut checked_stats = Statistics::default();
                let mut trusted_stats = Statistics::default();
                let (checked_points, checked_groups) =
                    crate::collector_metrics::observe_group_calls(&mut checked, |work| {
                        table
                            .decompose(admitted.point(), smallest, &mut checked_stats, work)
                            .unwrap()
                    });
                let (trusted_points, trusted_groups) =
                    crate::collector_metrics::observe_group_calls(&mut trusted, |work| {
                        table
                            .decompose_subgroup(&admitted, smallest, &mut trusted_stats, work)
                            .unwrap()
                    });
                assert_eq!(checked_points, trusted_points);
                assert_eq!(checked.used, trusted.used + subgroup.used);
                assert_eq!(checked_groups, trusted_groups + subgroup_groups);
                assert_eq!(checked_stats.queries, trusted_stats.queries);
                assert_eq!(checked_stats.lookups, trusted_stats.lookups);
                assert_eq!(checked_stats.replays, trusted_stats.replays);
            }
        }
        let other_generator = curve
            .mul(curve.generator(), &2u8.into(), &mut setup)
            .unwrap();
        let other_curve = Curve::new(
            curve.modulus().clone(),
            curve.a().clone(),
            curve.b().clone(),
            curve.order().clone(),
            other_generator,
            &mut setup,
        )
        .unwrap();
        let wrong = SubgroupContext::new(&other_curve).generator();
        let mut stats = Statistics::default();
        assert!(matches!(
            table.decompose_subgroup(&wrong, false, &mut stats, &mut setup),
            Err(Error::Invalid(_))
        ));
        assert_eq!(stats.queries, 0);
        let mut limited = Meter::new(Limits {
            steps: 0,
            ..Limits::default()
        });
        assert!(matches!(
            table.decompose_subgroup(&context.generator(), false, &mut stats, &mut limited),
            Err(Error::Limit(_))
        ));
    }

    #[test]
    fn provenance_queries_replay_even_a_forged_full_point_hit() {
        use crate::subgroup::SubgroupContext;
        let mut meter = Meter::new(Limits::default());
        let curve = curve(&mut meter);
        let bases = bases(&curve, &mut meter);
        let mut table =
            PairTable::new(&curve, &bases, &mut Statistics::default(), &mut meter).unwrap();
        let foreign = (1..19u8)
            .map(|k| curve.mul(curve.generator(), &k.into(), &mut meter).unwrap())
            .find(|p| !table.columns[1].contains_key(p))
            .unwrap();
        let raw = curve
            .add(&table.ordered[0][0], &foreign, &mut meter)
            .unwrap();
        let admitted = SubgroupContext::new(&curve)
            .validate(&raw, &mut meter)
            .unwrap();
        table.columns[1].insert(foreign, usize::MAX);
        let mut stats = Statistics::default();
        assert!(matches!(
            table.decompose_subgroup(&admitted, false, &mut stats, &mut meter),
            Err(Error::Integrity(_))
        ));
        assert_eq!(stats.replays, 0);
    }
    #[test]
    fn fresh_trials_rebuild_tables_before_their_queries() {
        use std::cell::Cell;
        let mut meter = Meter::new(Limits::default());
        let curve = curve(&mut meter);
        let target = curve.generator().clone();
        let config = Config {
            hash_prime: Some(37u8.into()),
            threshold: Some(37u8.into()),
            slots: 2,
            trials: 3,
            columns: 64,
        };
        let builds = Cell::new(0);
        let queries = Cell::new(0);
        let result = reduction::solve_with_preparation(
            &curve,
            &target,
            &config,
            &mut Seeded(42),
            |c, b, indexes, w| {
                builds.set(builds.get() + 1);
                PairTable::from_indexes(c, b, indexes, &mut Statistics::default(), w)
            },
            |_, b, table, _, _| {
                assert_eq!(table.bases[0].seed(), b[0].seed());
                assert_eq!(table.bases[1].seed(), b[1].seed());
                queries.set(queries.get() + 1);
                Ok(None)
            },
            &mut meter,
        );
        assert!(matches!(result, Err(Error::Limit(_))));
        assert_eq!(builds.get(), 3);
        assert!(queries.get() > builds.get());
    }
}
