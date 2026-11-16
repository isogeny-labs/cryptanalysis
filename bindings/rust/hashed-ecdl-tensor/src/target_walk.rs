//! Independently anchored adding targets with public two-dimensional labels.
//!
//! The increment construction follows the adding-walk description in Bos,
//! Kaihara and Montgomery, SHARCS 2009, section 3.4. This opt-in target policy
//! does not assume that successive targets or successful relations are iid.
//! Its event counters are development diagnostics, not calibrated work or time.
//!
//! Setup consumes 32 caller-RNG bytes for a public partition seed and two uniform
//! public coefficients per sampled increment. Each block starts with two fresh
//! caller-RNG coefficient samples; steps within a block consume no caller RNG.
//! Thus this policy deliberately changes the baseline's coefficient stream.

use crate::arithmetic::{random_below, RandomSource};
use crate::curve::{Curve, Point};
use crate::subgroup::{SubgroupContext, SubgroupJointTable, SubgroupPoint};
use crate::{invalid, overflow, BigUint, Error, Meter, Result};
use num_traits::Zero;
use sha2::{Digest, Sha256};

const MAX_TABLE_ATTEMPTS: usize = 16;

/// Bounded draft adding-table and anchor-block choices.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Config {
    /// Number of increment entries, either 16 or 32.
    pub table_size: usize,
    /// Emitted targets per independent anchor, either 16, 64 or 256.
    pub block_length: usize,
}

impl Config {
    /// Check the explicitly supported draft policy choices.
    pub fn validate(&self) -> Result<()> {
        if !matches!(self.table_size, 16 | 32) || !matches!(self.block_length, 16 | 64 | 256) {
            return Err(invalid("target walk table or block choice"));
        }
        Ok(())
    }
}

/// Observable setup, anchor and step events, without a runtime interpretation.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct Statistics {
    /// Completely prepared adding tables.
    pub preparations: u64,
    /// Attempted full coefficient tables, including rank-deficient redraws.
    pub table_attempts: u64,
    /// Coefficient pairs sampled for increment-table setup.
    pub sampled_increment_labels: u64,
    /// Candidate tables rejected for lacking two-dimensional coefficient span.
    pub table_redraws: u64,
    /// Increment points actually constructed with checked joint arithmetic.
    pub increment_points: u64,
    /// Constructed increment points equal to the group identity, retained.
    pub identity_increment_points: u64,
    /// Caller bytes successfully supplied for public partition-seed setup.
    pub partition_seed_bytes: u64,
    /// Fresh coefficient-pair anchors actually emitted.
    pub anchors: u64,
    /// Checked incremental additions actually emitted.
    pub steps: u64,
    /// Canonical partition decisions completed, including later failed steps.
    pub partitions: u64,
}

/// A public target and its exact coefficients relative to the constructor's G,Q.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LabelledTarget {
    /// Canonical target point R.
    pub point: Point,
    /// Canonical coefficient u in R = uG + vQ.
    pub u: BigUint,
    /// Canonical coefficient v in R = uG + vQ.
    pub v: BigUint,
    /// Whether this output starts a fresh independently sampled block.
    pub is_anchor: bool,
}

/// The same public output with its sealed subgroup construction provenance.
pub(crate) struct ProvenTarget {
    pub(crate) labels: LabelledTarget,
    pub(crate) subgroup_point: SubgroupPoint,
}

struct Increment {
    u: BigUint,
    v: BigUint,
    point: SubgroupPoint,
}

struct State {
    u: BigUint,
    v: BigUint,
    point: SubgroupPoint,
    emitted: usize,
}

/// Stateful adding target generator bound to its certified curve and public Q.
///
/// Table labels have two-dimensional span, but this is only a setup condition.
/// Output relations are never accepted or rejected by an augmented-rank rule;
/// the collector must check their actual dependency and replay its certificate.
pub struct TargetWalk {
    context: SubgroupContext,
    joint: SubgroupJointTable,
    increments: Vec<Increment>,
    partition_prefix: Sha256,
    config: Config,
    current: Option<State>,
}

fn increase(counter: &mut u64, amount: u64) -> Result<()> {
    *counter = counter
        .checked_add(amount)
        .ok_or_else(|| overflow("target walk statistics"))?;
    Ok(())
}

fn hash_integer(hasher: &mut Sha256, value: &BigUint, meter: &mut Meter) -> Result<()> {
    let bits = usize::try_from(value.bits()).map_err(|_| overflow("target walk hash width"))?;
    meter.bits(bits, "target walk hash integer")?;
    meter.vector(bits.div_ceil(8), "target walk hash bytes")?;
    let bytes = value.to_bytes_le();
    let length = u64::try_from(bytes.len()).map_err(|_| overflow("target walk hash length"))?;
    hasher.update(length.to_le_bytes());
    hasher.update(&bytes);
    Ok(())
}

fn hash_point(hasher: &mut Sha256, curve: &Curve, point: &Point, meter: &mut Meter) -> Result<()> {
    meter.charge(1, "target walk canonical point")?;
    if !curve.contains(point) {
        return Err(invalid("target walk partition point"));
    }
    match point {
        Point::Infinity => hasher.update([0]),
        Point::Affine { x, y } => {
            hasher.update([1]);
            hash_integer(hasher, x, meter)?;
            hash_integer(hasher, y, meter)?;
        }
    }
    Ok(())
}

fn partition_prefix(
    curve: &Curve,
    target: &Point,
    config: Config,
    seed: &[u8; 32],
    meter: &mut Meter,
) -> Result<Sha256> {
    let mut hasher = Sha256::new();
    hasher.update(b"hashed-ecdl/anchored-adding-target/partition/v1\0");
    // Public walk partition input, not a password/KDF salt or secret key.
    // Deterministic seeds are intentional in correctness fixtures.
    hasher.update(seed);
    hasher.update((config.table_size as u64).to_le_bytes());
    hasher.update((config.block_length as u64).to_le_bytes());
    for value in [
        curve.modulus(),
        curve.a(),
        curve.b(),
        curve.order(),
        curve.cofactor(),
    ] {
        hash_integer(&mut hasher, value, meter)?;
    }
    hash_point(&mut hasher, curve, curve.generator(), meter)?;
    hash_point(&mut hasher, curve, target, meter)?;
    Ok(hasher)
}

fn spans_two(labels: &[(BigUint, BigUint)], order: &BigUint, meter: &mut Meter) -> Result<bool> {
    let Some((left_u, left_v)) = labels.iter().find(|(u, v)| !u.is_zero() || !v.is_zero()) else {
        return Ok(false);
    };
    for (u, v) in labels {
        meter.charge(1, "target walk increment label span")?;
        if (left_u * v + order - (left_v * u) % order) % order != BigUint::zero() {
            return Ok(true);
        }
    }
    Ok(false)
}

impl TargetWalk {
    /// Validate public Q, prepare a bounded table and public partition seed.
    ///
    /// The curve already certified G. Every increment and anchor uses checked
    /// joint arithmetic, and identity increment points are deliberately kept.
    pub fn new(
        curve: &Curve,
        target: &Point,
        config: Config,
        rng: &mut impl RandomSource,
        statistics: &mut Statistics,
        meter: &mut Meter,
    ) -> Result<Self> {
        config.validate()?;
        meter.vector(config.table_size, "target walk increment table")?;
        let context = SubgroupContext::new(curve);
        let target = context.validate(target, meter)?;
        Self::from_context(&context, &target, config, rng, statistics, meter)
    }

    /// Reuse the collector's existing sealed validation and construction context.
    pub(crate) fn from_context(
        context: &SubgroupContext,
        target: &SubgroupPoint,
        config: Config,
        rng: &mut impl RandomSource,
        statistics: &mut Statistics,
        meter: &mut Meter,
    ) -> Result<Self> {
        config.validate()?;
        meter.vector(config.table_size, "target walk increment table")?;
        meter.charge(1, "target walk preparation")?;
        let joint = context.joint_table(&context.generator(), target, meter)?;
        let mut partition_seed = [0u8; 32];
        meter.vector(partition_seed.len(), "target walk partition seed")?;
        meter.charge(1, "target walk partition seed")?;
        rng.fill(&mut partition_seed)?;
        increase(
            &mut statistics.partition_seed_bytes,
            partition_seed.len() as u64,
        )?;
        let prefix = partition_prefix(
            context.curve(),
            target.point(),
            config,
            &partition_seed,
            meter,
        )?;

        let mut labels = Vec::new();
        labels
            .try_reserve_exact(config.table_size)
            .map_err(|_| Error::Limit("target walk label allocation".into()))?;
        for _ in 0..MAX_TABLE_ATTEMPTS {
            increase(&mut statistics.table_attempts, 1)?;
            labels.clear();
            for _ in 0..config.table_size {
                let u = random_below(context.curve().order(), rng, meter)?;
                let v = random_below(context.curve().order(), rng, meter)?;
                increase(&mut statistics.sampled_increment_labels, 1)?;
                labels.push((u, v));
            }
            if spans_two(&labels, context.curve().order(), meter)? {
                let mut increments = Vec::new();
                increments
                    .try_reserve_exact(config.table_size)
                    .map_err(|_| Error::Limit("target walk increment allocation".into()))?;
                for (u, v) in labels {
                    let point = joint.evaluate(&u, &v, meter)?;
                    increase(&mut statistics.increment_points, 1)?;
                    if point.point() == &Point::Infinity {
                        increase(&mut statistics.identity_increment_points, 1)?;
                    }
                    increments.push(Increment { u, v, point });
                }
                increase(&mut statistics.preparations, 1)?;
                return Ok(Self {
                    context: context.clone(),
                    joint,
                    increments,
                    partition_prefix: prefix,
                    config,
                    current: None,
                });
            }
            increase(&mut statistics.table_redraws, 1)?;
        }
        Err(Error::Limit(
            "target walk two-dimensional label setup attempts".into(),
        ))
    }

    fn partition(&self, point: &Point, meter: &mut Meter) -> Result<usize> {
        meter.charge(1, "target walk partition")?;
        let mut hasher = self.partition_prefix.clone();
        hash_point(&mut hasher, self.context.curve(), point, meter)?;
        // Both supported table sizes divide 256, so this byte projection has
        // no modulo-bias issue conditional on the hash output model.
        Ok(usize::from(hasher.finalize()[0]) % self.config.table_size)
    }

    /// Emit a fresh uniform-coefficient anchor or the next checked adding step.
    ///
    /// Only anchors use caller randomness. A resource/RNG error stays an error,
    /// and does not produce a target or advance the current walk position.
    pub fn next(
        &mut self,
        rng: &mut impl RandomSource,
        statistics: &mut Statistics,
        meter: &mut Meter,
    ) -> Result<LabelledTarget> {
        let ProvenTarget {
            labels,
            subgroup_point,
        } = self.next_trusted(rng, statistics, meter)?;
        debug_assert_eq!(subgroup_point.point(), &labels.point);
        Ok(labels)
    }

    /// Emit the same labels and point while retaining its sealed provenance.
    pub(crate) fn next_trusted(
        &mut self,
        rng: &mut impl RandomSource,
        statistics: &mut Statistics,
        meter: &mut Meter,
    ) -> Result<ProvenTarget> {
        let order = self.context.curve().order();
        let state = if let Some(current) = self
            .current
            .as_ref()
            .filter(|current| current.emitted < self.config.block_length)
        {
            let index = self.partition(current.point.point(), meter)?;
            increase(&mut statistics.partitions, 1)?;
            let increment = &self.increments[index];
            let point = self.context.add(&current.point, &increment.point, meter)?;
            let u = (&current.u + &increment.u) % order;
            let v = (&current.v + &increment.v) % order;
            increase(&mut statistics.steps, 1)?;
            State {
                point,
                u,
                v,
                emitted: current.emitted + 1,
            }
        } else {
            let u = random_below(order, rng, meter)?;
            let v = random_below(order, rng, meter)?;
            let point = self.joint.evaluate(&u, &v, meter)?;
            increase(&mut statistics.anchors, 1)?;
            State {
                point,
                u,
                v,
                emitted: 1,
            }
        };
        let output = ProvenTarget {
            labels: LabelledTarget {
                point: state.point.point().clone(),
                u: state.u.clone(),
                v: state.v.clone(),
                is_anchor: state.emitted == 1,
            },
            subgroup_point: state.point.clone(),
        };
        self.current = Some(state);
        Ok(output)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::arithmetic::{inverse, Seeded};
    use crate::Limits;
    use std::collections::VecDeque;

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

    fn config() -> Config {
        Config {
            table_size: 16,
            block_length: 16,
        }
    }

    fn replay(curve: &Curve, target: &Point, output: &LabelledTarget, meter: &mut Meter) {
        assert!(&output.u < curve.order() && &output.v < curve.order());
        let left = curve.mul(curve.generator(), &output.u, meter).unwrap();
        let right = curve.mul(target, &output.v, meter).unwrap();
        assert_eq!(curve.add(&left, &right, meter).unwrap(), output.point);
    }

    struct Bytes(VecDeque<u8>);
    impl RandomSource for Bytes {
        fn fill(&mut self, output: &mut [u8]) -> Result<()> {
            for byte in output {
                *byte = self
                    .0
                    .pop_front()
                    .ok_or_else(|| invalid("test RNG empty"))?;
            }
            Ok(())
        }
    }

    struct ZeroRandom;
    impl RandomSource for ZeroRandom {
        fn fill(&mut self, output: &mut [u8]) -> Result<()> {
            output.fill(0);
            Ok(())
        }
    }

    struct Broken;
    impl RandomSource for Broken {
        fn fill(&mut self, _: &mut [u8]) -> Result<()> {
            Err(invalid("test RNG failure"))
        }
    }

    #[test]
    fn every_supported_policy_replays_and_reanchors_at_exact_boundaries() {
        let mut meter = Meter::new(Limits::default());
        let curve = curve(&mut meter);
        let target = curve
            .mul(curve.generator(), &7u8.into(), &mut meter)
            .unwrap();
        for table_size in [16, 32] {
            for block_length in [16, 64, 256] {
                let policy = Config {
                    table_size,
                    block_length,
                };
                let mut stats = Statistics::default();
                let mut rng = Seeded(0x756e69742d77616c);
                let mut walk =
                    TargetWalk::new(&curve, &target, policy, &mut rng, &mut stats, &mut meter)
                        .unwrap();
                let count = 2 * block_length + 3;
                for index in 0..count {
                    let output = walk.next_trusted(&mut rng, &mut stats, &mut meter).unwrap();
                    assert_eq!(output.labels.is_anchor, index % block_length == 0);
                    assert_eq!(
                        output.subgroup_point.for_curve(&curve).unwrap(),
                        &output.labels.point
                    );
                    replay(&curve, &target, &output.labels, &mut meter);
                }
                assert_eq!(stats.preparations, 1);
                assert_eq!(stats.increment_points, table_size as u64);
                assert_eq!(stats.anchors, 3);
                assert_eq!(stats.steps, count as u64 - 3);
                assert_eq!(stats.partitions, stats.steps);
                assert_eq!(stats.partition_seed_bytes, 32);
                let labels: Vec<_> = walk
                    .increments
                    .iter()
                    .map(|i| (i.u.clone(), i.v.clone()))
                    .collect();
                assert!(spans_two(&labels, curve.order(), &mut meter).unwrap());
            }
        }
    }

    #[test]
    fn same_public_seed_and_context_reproduce_labels_and_partitions() {
        let mut meter = Meter::new(Limits::default());
        let curve = curve(&mut meter);
        let target = curve
            .mul(curve.generator(), &3u8.into(), &mut meter)
            .unwrap();
        let mut left_rng = Seeded(63);
        let mut right_rng = Seeded(63);
        let mut left_stats = Statistics::default();
        let mut right_stats = Statistics::default();
        let mut left = TargetWalk::new(
            &curve,
            &target,
            config(),
            &mut left_rng,
            &mut left_stats,
            &mut meter,
        )
        .unwrap();
        let mut right = TargetWalk::new(
            &curve,
            &target,
            config(),
            &mut right_rng,
            &mut right_stats,
            &mut meter,
        )
        .unwrap();
        for _ in 0..100 {
            assert_eq!(
                left.next(&mut left_rng, &mut left_stats, &mut meter)
                    .unwrap(),
                right
                    .next(&mut right_rng, &mut right_stats, &mut meter)
                    .unwrap()
            );
        }
        assert_eq!(left_rng.0, right_rng.0);
        assert_eq!(left_stats, right_stats);
    }

    #[test]
    fn fresh_anchor_coefficients_are_sampled_and_steps_need_no_rng() {
        let mut meter = Meter::new(Limits::default());
        let curve = curve(&mut meter);
        let mut stats = Statistics::default();
        let mut walk = TargetWalk::new(
            &curve,
            curve.generator(),
            config(),
            &mut Seeded(91),
            &mut stats,
            &mut meter,
        )
        .unwrap();
        let mut anchors = Bytes([1, 2, 3, 4].into_iter().collect());
        let first = walk.next(&mut anchors, &mut stats, &mut meter).unwrap();
        assert_eq!((first.u, first.v), (1u8.into(), 2u8.into()));
        for _ in 1..config().block_length {
            assert!(
                !walk
                    .next(&mut Broken, &mut stats, &mut meter)
                    .unwrap()
                    .is_anchor
            );
        }
        let next = walk.next(&mut anchors, &mut stats, &mut meter).unwrap();
        assert!(next.is_anchor);
        assert_eq!((next.u, next.v), (3u8.into(), 4u8.into()));
        assert!(anchors.0.is_empty());
    }

    #[test]
    fn bad_policy_rng_and_rank_deficiency_are_errors() {
        let mut meter = Meter::new(Limits::default());
        let curve = curve(&mut meter);
        for bad in [
            Config {
                table_size: 0,
                block_length: 16,
            },
            Config {
                table_size: 17,
                block_length: 16,
            },
            Config {
                table_size: 16,
                block_length: 0,
            },
            Config {
                table_size: 16,
                block_length: 17,
            },
        ] {
            assert!(matches!(
                TargetWalk::new(
                    &curve,
                    curve.generator(),
                    bad,
                    &mut Seeded(1),
                    &mut Statistics::default(),
                    &mut meter
                ),
                Err(Error::Invalid(_))
            ));
        }
        assert!(matches!(
            TargetWalk::new(
                &curve,
                curve.generator(),
                config(),
                &mut Broken,
                &mut Statistics::default(),
                &mut meter
            ),
            Err(Error::Invalid(_))
        ));
        let mut stats = Statistics::default();
        assert!(matches!(
            TargetWalk::new(
                &curve,
                curve.generator(),
                config(),
                &mut ZeroRandom,
                &mut stats,
                &mut meter
            ),
            Err(Error::Limit(_))
        ));
        assert_eq!(stats.table_attempts, MAX_TABLE_ATTEMPTS as u64);
        assert_eq!(stats.table_redraws, stats.table_attempts);
        assert_eq!(
            stats.sampled_increment_labels,
            (MAX_TABLE_ATTEMPTS * config().table_size) as u64
        );
        assert_eq!(stats.preparations, 0);
        assert_eq!(stats.increment_points, 0);
    }

    #[test]
    fn noncanonical_and_outside_subgroup_points_never_acquire_provenance() {
        let mut meter = Meter::new(Limits::default());
        let curve = Curve::with_cofactor(
            5u8.into(),
            0u8.into(),
            1u8.into(),
            3u8.into(),
            2u8.into(),
            Point::Affine {
                x: 0u8.into(),
                y: 1u8.into(),
            },
            &mut meter,
        )
        .unwrap();
        for bad in [
            Point::Affine {
                x: 4u8.into(),
                y: 0u8.into(),
            },
            Point::Affine {
                x: 5u8.into(),
                y: 1u8.into(),
            },
            Point::Affine {
                x: 1u8.into(),
                y: 1u8.into(),
            },
        ] {
            assert!(matches!(
                TargetWalk::new(
                    &curve,
                    &bad,
                    config(),
                    &mut Seeded(33),
                    &mut Statistics::default(),
                    &mut meter
                ),
                Err(Error::Invalid(_))
            ));
        }
        let mut stats = Statistics::default();
        let mut rng = Seeded(33);
        let mut walk = TargetWalk::new(
            &curve,
            curve.generator(),
            config(),
            &mut rng,
            &mut stats,
            &mut meter,
        )
        .unwrap();
        for _ in 0..40 {
            let point = walk.next(&mut rng, &mut stats, &mut meter).unwrap();
            replay(&curve, curve.generator(), &point, &mut meter);
        }
    }

    #[test]
    fn identity_equal_and_opposite_targets_are_admissible() {
        let mut meter = Meter::new(Limits::default());
        let curve = curve(&mut meter);
        for target in [
            Point::Infinity,
            curve.generator().clone(),
            curve.negate(curve.generator()).unwrap(),
        ] {
            let mut stats = Statistics::default();
            let mut rng = Seeded(17);
            let mut walk =
                TargetWalk::new(&curve, &target, config(), &mut rng, &mut stats, &mut meter)
                    .unwrap();
            for _ in 0..40 {
                replay(
                    &curve,
                    &target,
                    &walk.next(&mut rng, &mut stats, &mut meter).unwrap(),
                    &mut meter,
                );
            }
        }
    }

    #[test]
    fn identity_increment_with_useful_label_difference_is_retained_and_replayed() {
        let mut meter = Meter::new(Limits::default());
        let curve = curve(&mut meter);
        let target = curve
            .mul(curve.generator(), &3u8.into(), &mut meter)
            .unwrap();
        let prefix = partition_prefix(&curve, &target, config(), &[0; 32], &mut meter).unwrap();
        let mut hash = prefix.clone();
        hash_point(&mut hash, &curve, &Point::Infinity, &mut meter).unwrap();
        let index = usize::from(hash.finalize()[0]) % config().table_size;
        let independent_index = (index + 1) % config().table_size;
        let mut bytes = vec![0; 32];
        for slot in 0..config().table_size {
            bytes.extend(if slot == independent_index {
                [1, 0]
            } else {
                [16, 1]
            });
        }
        let mut stats = Statistics::default();
        let mut walk = TargetWalk::new(
            &curve,
            &target,
            config(),
            &mut Bytes(bytes.into()),
            &mut stats,
            &mut meter,
        )
        .unwrap();
        assert_eq!(stats.identity_increment_points, 15);
        let first = walk.next(&mut ZeroRandom, &mut stats, &mut meter).unwrap();
        let second = walk.next(&mut Broken, &mut stats, &mut meter).unwrap();
        assert_eq!(first.point, Point::Infinity);
        assert_eq!(first.point, second.point);
        assert_ne!((&first.u, &first.v), (&second.u, &second.v));
        let du = (&second.u + curve.order() - &first.u) % curve.order();
        let dv = (&second.v + curve.order() - &first.v) % curve.order();
        assert!(!dv.is_zero());
        let scalar = (curve.order() - du) * inverse(&dv, curve.order()).unwrap() % curve.order();
        assert_eq!(scalar, 3u8.into());
        assert_eq!(
            curve.mul(curve.generator(), &scalar, &mut meter).unwrap(),
            target
        );
        replay(&curve, &target, &first, &mut meter);
        replay(&curve, &target, &second, &mut meter);
    }

    #[test]
    fn fixed_v_four_edge_control_has_zero_extraction_coefficient() {
        let mut meter = Meter::new(Limits::default());
        let curve = curve(&mut meter);
        let target = curve
            .mul(curve.generator(), &3u8.into(), &mut meter)
            .unwrap();
        let logs = [4u8, 5, 6, 5];
        let signs = [1u8, 18, 1, 18];
        let mut combined_u = BigUint::zero();
        let mut combined_v = BigUint::zero();
        for (log, sign) in logs.into_iter().zip(signs) {
            let output = LabelledTarget {
                point: curve
                    .mul(curve.generator(), &log.into(), &mut meter)
                    .unwrap(),
                u: (BigUint::from(log) + curve.order() - BigUint::from(6u8)) % curve.order(),
                v: 2u8.into(),
                is_anchor: false,
            };
            replay(&curve, &target, &output, &mut meter);
            combined_u = (combined_u + BigUint::from(sign) * output.u) % curve.order();
            combined_v = (combined_v + BigUint::from(sign) * output.v) % curve.order();
        }
        assert!(combined_u.is_zero() && combined_v.is_zero());
        // The four targets are G+3G, G+4G, 2G+4G, 2G+3G: a
        // slot-cancelling rectangle, not four unrelated arbitrary labels.
        for (left, right, log) in [(1u8, 3u8, 4u8), (1, 4, 5), (2, 4, 6), (2, 3, 5)] {
            let p = curve
                .mul(curve.generator(), &left.into(), &mut meter)
                .unwrap();
            let q = curve
                .mul(curve.generator(), &right.into(), &mut meter)
                .unwrap();
            assert_eq!(
                curve.add(&p, &q, &mut meter).unwrap(),
                curve
                    .mul(curve.generator(), &log.into(), &mut meter)
                    .unwrap()
            );
        }
    }

    #[test]
    fn limits_rng_failures_and_context_mismatch_do_not_yield_targets() {
        let mut meter = Meter::new(Limits::default());
        let curve = curve(&mut meter);
        let context = SubgroupContext::new(&curve);
        let other = SubgroupContext::new(&curve);
        assert!(matches!(
            TargetWalk::from_context(
                &context,
                &other.generator(),
                config(),
                &mut Seeded(1),
                &mut Statistics::default(),
                &mut meter
            ),
            Err(Error::Invalid(_))
        ));
        let mut stats = Statistics::default();
        let mut walk = TargetWalk::new(
            &curve,
            curve.generator(),
            config(),
            &mut Seeded(1),
            &mut stats,
            &mut meter,
        )
        .unwrap();
        assert!(matches!(
            walk.next(&mut Broken, &mut stats, &mut meter),
            Err(Error::Invalid(_))
        ));
        assert!(walk.current.is_none());
        walk.next(&mut Seeded(2), &mut stats, &mut meter).unwrap();
        let previous = walk.current.as_ref().unwrap().point.point().clone();
        let mut exhausted = Meter::new(Limits {
            steps: 0,
            ..Limits::default()
        });
        assert!(matches!(
            walk.next(&mut Broken, &mut stats, &mut exhausted),
            Err(Error::Limit(_))
        ));
        assert_eq!(walk.current.as_ref().unwrap().point.point(), &previous);
        assert_eq!(walk.current.as_ref().unwrap().emitted, 1);
        walk.next(&mut Broken, &mut stats, &mut meter).unwrap();
        assert_eq!(stats.steps, 1);
        let mut short = Meter::new(Limits {
            vector: 8,
            ..Limits::default()
        });
        assert!(matches!(
            TargetWalk::new(
                &curve,
                curve.generator(),
                config(),
                &mut Seeded(1),
                &mut Statistics::default(),
                &mut short
            ),
            Err(Error::Limit(_))
        ));
    }
}
