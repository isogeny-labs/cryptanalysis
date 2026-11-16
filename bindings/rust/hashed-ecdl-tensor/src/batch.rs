//! Checked chunks of affine complements for prepared point-table queries.
//!
//! The nonexceptional `R - P` denominators share Montgomery simultaneous
//! inversion (Bos, Kaihara and Montgomery, SHARCS '09, section 3.5:
//! <https://www.hyperelliptic.org/tanja/SHARCS/record2.pdf>). Equal-x and
//! identity cases use the existing checked affine addition. Output order is
//! input order, including repeated points and computed-but-unused chunk tails.
//!
//! Each complement keeps the ordinary `curve addition` semantic event. Batch
//! products, inversion and affine field operations carry additional explicit
//! resource charges. These are uncalibrated development events, not runtime,
//! GAE pricing or a performance comparison with the original affine routine.

use crate::arithmetic::inverse;
use crate::curve::{Curve, Point};
use crate::{invalid, overflow, BigUint, Error, Meter, Result};

/// Events incurred by complement chunks; not calibrated arithmetic prices.
#[derive(Clone, Debug, Default)]
pub struct BatchStatistics {
    /// Nonempty chunks begun after all input coordinates were checked.
    pub batches: u64,
    /// Complements attempted, including an attempt later limited by resources.
    pub complements: u64,
    /// Inversions attempted for nonzero products of ordinary denominators.
    /// Inversions inside checked exceptional fallbacks are not included.
    pub ordinary_inversions: u64,
    /// Complements delegated to the checked identity/equal-x arithmetic.
    pub exceptional_fallbacks: u64,
    /// Multiplications used only by prefix and inverse-recovery products.
    /// Slope and output-coordinate arithmetic is charged separately.
    pub product_multiplications: u64,
}

fn increment(value: &mut u64) -> Result<()> {
    *value = value
        .checked_add(1)
        .ok_or_else(|| overflow("batch complement statistics"))?;
    Ok(())
}

struct Ordinary {
    point_index: usize,
    denominator: BigUint,
    numerator: BigUint,
    prefix: BigUint,
}

fn product(
    left: &BigUint,
    right: &BigUint,
    modulus: &BigUint,
    statistics: &mut BatchStatistics,
    meter: &mut Meter,
) -> Result<BigUint> {
    meter.charge(1, "batch denominator product")?;
    increment(&mut statistics.product_multiplications)?;
    Ok(left * right % modulus)
}

/// Compute every `target - points[i]`, preserving point order and exceptions.
///
/// This is checked curve arithmetic, not a subgroup-validity certificate.
/// Invalid/noncanonical inputs and resource errors propagate as errors. Chunk
/// validation/allocation precede arithmetic; error ordering can consequently
/// differ from calling the scalar affine routine until its first early hit.
pub fn complement_chunk(
    curve: &Curve,
    target: &Point,
    points: &[Point],
    meter: &mut Meter,
) -> Result<Vec<Point>> {
    complement_chunk_with_statistics(
        curve,
        target,
        points,
        &mut BatchStatistics::default(),
        meter,
    )
}

/// Compute a complete chunk while retaining batch-stage event counts.
pub fn complement_chunk_with_statistics(
    curve: &Curve,
    target: &Point,
    points: &[Point],
    statistics: &mut BatchStatistics,
    meter: &mut Meter,
) -> Result<Vec<Point>> {
    meter.vector(points.len(), "batch complement chunk")?;
    meter.charge(1, "batch target validation")?;
    if !curve.contains(target) {
        return Err(invalid("batch complement curve point"));
    }
    for point in points {
        meter.charge(1, "batch point validation")?;
        if !curve.contains(point) {
            return Err(invalid("batch complement curve point"));
        }
    }
    if points.is_empty() {
        return Ok(Vec::new());
    }
    increment(&mut statistics.batches)?;
    let mut output = Vec::new();
    output
        .try_reserve_exact(points.len())
        .map_err(|_| Error::Limit("batch complement output allocation".into()))?;
    output.resize(points.len(), Point::Infinity);
    let mut ordinary: Vec<Ordinary> = Vec::new();
    ordinary
        .try_reserve_exact(points.len())
        .map_err(|_| Error::Limit("batch denominator allocation".into()))?;
    let modulus = curve.modulus();

    for (point_index, point) in points.iter().enumerate() {
        increment(&mut statistics.complements)?;
        match (target, point) {
            (Point::Affine { x, y }, Point::Affine { x: xx, y: yy }) if x != xx => {
                // The checked scalar operation charges once per R + (-P).
                // Retain that event even though its inversion is now shared.
                meter.charge(1, "curve addition")?;
                crate::collector_metrics::batch_group(false)?;
                let denominator = curve.sub(x, xx);
                let numerator = (y + yy) % modulus;
                let prefix = if let Some(previous) = ordinary.last() {
                    product(&previous.prefix, &denominator, modulus, statistics, meter)?
                } else {
                    denominator.clone()
                };
                ordinary.push(Ordinary {
                    point_index,
                    denominator,
                    numerator,
                    prefix,
                });
            }
            _ => {
                increment(&mut statistics.exceptional_fallbacks)?;
                output[point_index] = curve.add(target, &curve.negate(point)?, meter)?;
            }
        }
    }
    let Some(last) = ordinary.last() else {
        return Ok(output);
    };
    meter.charge(1, "batch denominator inversion")?;
    increment(&mut statistics.ordinary_inversions)?;
    let mut inverse_product = inverse(&last.prefix, modulus)?;
    // An ordinary job exists only when the target is affine and x differs.
    let Point::Affine { x, y } = target else {
        unreachable!("ordinary complement target must be affine")
    };
    for index in (0..ordinary.len()).rev() {
        let job = &ordinary[index];
        let denominator_inverse = if index == 0 {
            inverse_product.clone()
        } else {
            product(
                &inverse_product,
                &ordinary[index - 1].prefix,
                modulus,
                statistics,
                meter,
            )?
        };
        meter.charge(1, "batch affine multiplication")?;
        let slope = &job.numerator * denominator_inverse % modulus;
        meter.charge(1, "batch affine square")?;
        let slope_squared = &slope * &slope % modulus;
        let Point::Affine { x: xx, .. } = &points[job.point_index] else {
            unreachable!("ordinary complement input must be affine")
        };
        let nx = curve.sub(&curve.sub(&slope_squared, x), xx);
        meter.charge(1, "batch affine multiplication")?;
        let ny = curve.sub(&(&slope * curve.sub(x, &nx) % modulus), y);
        output[job.point_index] = Point::Affine { x: nx, y: ny };
        if index != 0 {
            inverse_product = product(
                &inverse_product,
                &job.denominator,
                modulus,
                statistics,
                meter,
            )?;
        }
    }
    Ok(output)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Limits, Meter};
    use num_traits::ToPrimitive;

    fn prime_curve() -> Curve {
        Curve::new(
            17u8.into(),
            2u8.into(),
            2u8.into(),
            19u8.into(),
            Point::Affine {
                x: 5u8.into(),
                y: 1u8.into(),
            },
            &mut Meter::new(Limits::default()),
        )
        .unwrap()
    }

    fn cofactor_curve() -> Curve {
        Curve::with_cofactor(
            5u8.into(),
            0u8.into(),
            1u8.into(),
            3u8.into(),
            2u8.into(),
            Point::Affine {
                x: 0u8.into(),
                y: 1u8.into(),
            },
            &mut Meter::new(Limits::default()),
        )
        .unwrap()
    }

    fn all_points(curve: &Curve) -> Vec<Point> {
        let mut points = vec![Point::Infinity];
        for x in 0..curve.modulus().to_u8().unwrap() {
            for y in 0..curve.modulus().to_u8().unwrap() {
                let point = Point::Affine {
                    x: x.into(),
                    y: y.into(),
                };
                if curve.contains(&point) {
                    points.push(point);
                }
            }
        }
        points
    }

    fn scalar_control(curve: &Curve, target: &Point, points: &[Point]) -> Vec<Point> {
        let mut meter = Meter::new(Limits::default());
        points
            .iter()
            .map(|point| {
                curve
                    .add(target, &curve.negate(point).unwrap(), &mut meter)
                    .unwrap()
            })
            .collect()
    }

    #[test]
    fn exhaustive_curve_inputs_match_scalar_arithmetic_across_chunk_boundaries() {
        for curve in [prime_curve(), cofactor_curve()] {
            let mut points = all_points(&curve);
            let targets = points.clone();
            // Repeated denominators and reordered/repeated keys are allowed.
            points.extend(targets.iter().rev().cloned());
            for target in targets {
                let expected = scalar_control(&curve, &target, &points);
                for size in [1, 2, 8, 32, 128] {
                    let mut meter = Meter::new(Limits::default());
                    let (actual, groups) =
                        crate::collector_metrics::observe_group_calls(&mut meter, |work| {
                            points
                                .chunks(size)
                                .flat_map(|chunk| {
                                    complement_chunk(&curve, &target, chunk, work).unwrap()
                                })
                                .collect::<Vec<Point>>()
                        });
                    assert_eq!(actual, expected);
                    assert_eq!(groups, points.len() as u64);
                }
            }
        }
    }

    #[test]
    fn ordinary_batch_uses_one_inverse_and_keeps_all_addition_events() {
        let curve = prime_curve();
        let target = curve.generator();
        let Point::Affine { x, .. } = target else {
            unreachable!()
        };
        let points: Vec<Point> = all_points(&curve)
            .into_iter()
            .filter(|point| matches!(point, Point::Affine { x: xx, .. } if x != xx))
            .collect();
        let mut statistics = BatchStatistics::default();
        let mut meter = Meter::new(Limits::default());
        let (actual, groups) = crate::collector_metrics::observe_group_calls(&mut meter, |work| {
            complement_chunk_with_statistics(&curve, target, &points, &mut statistics, work)
                .unwrap()
        });
        assert_eq!(actual, scalar_control(&curve, target, &points));
        assert_eq!(statistics.batches, 1);
        assert_eq!(statistics.complements, points.len() as u64);
        assert_eq!(statistics.ordinary_inversions, 1);
        assert_eq!(statistics.exceptional_fallbacks, 0);
        assert_eq!(
            statistics.product_multiplications,
            3 * (points.len() as u64 - 1)
        );
        assert_eq!(groups, points.len() as u64);
    }

    #[test]
    fn identity_equal_x_and_zero_y_use_checked_fallbacks_without_batch_inverse() {
        let curve = cofactor_curve();
        let zero_y = Point::Affine {
            x: 4u8.into(),
            y: 0u8.into(),
        };
        assert!(curve.contains(&zero_y));
        let points = [zero_y.clone(), Point::Infinity, zero_y.clone()];
        let mut statistics = BatchStatistics::default();
        let mut meter = Meter::new(Limits::default());
        let (actual, groups) = crate::collector_metrics::observe_group_calls(&mut meter, |work| {
            complement_chunk_with_statistics(&curve, &zero_y, &points, &mut statistics, work)
                .unwrap()
        });
        assert_eq!(actual, scalar_control(&curve, &zero_y, &points));
        assert_eq!(statistics.ordinary_inversions, 0);
        assert_eq!(statistics.exceptional_fallbacks, 3);
        assert_eq!(groups, 3);
        let all = all_points(&curve);
        assert_eq!(
            complement_chunk(&curve, &Point::Infinity, &all, &mut meter).unwrap(),
            scalar_control(&curve, &Point::Infinity, &all)
        );
    }

    #[test]
    fn empty_chunk_is_checked_and_performs_no_batch_work() {
        let curve = prime_curve();
        let mut statistics = BatchStatistics::default();
        let mut meter = Meter::new(Limits::default());
        assert!(complement_chunk_with_statistics(
            &curve,
            curve.generator(),
            &[],
            &mut statistics,
            &mut meter
        )
        .unwrap()
        .is_empty());
        assert_eq!(statistics.batches, 0);
        assert_eq!(statistics.ordinary_inversions, 0);
        // Even an empty chunk checks its untrusted target once.
        assert_eq!(meter.used, 1);
        let invalid = Point::Affine {
            x: 17u8.into(),
            y: 1u8.into(),
        };
        assert!(matches!(
            complement_chunk(&curve, &invalid, &[], &mut meter),
            Err(Error::Invalid(_))
        ));
    }

    #[test]
    fn noncanonical_and_off_curve_inputs_are_errors_before_arithmetic() {
        let curve = prime_curve();
        for invalid in [
            Point::Affine {
                x: 17u8.into(),
                y: 1u8.into(),
            },
            Point::Affine {
                x: 1u8.into(),
                y: 1u8.into(),
            },
        ] {
            let mut meter = Meter::new(Limits::default());
            let (_, groups) = crate::collector_metrics::observe_group_calls(&mut meter, |work| {
                assert!(matches!(
                    complement_chunk(&curve, &invalid, &[Point::Infinity], work),
                    Err(Error::Invalid(_))
                ));
                assert!(matches!(
                    complement_chunk(
                        &curve,
                        curve.generator(),
                        &[curve.generator().clone(), invalid],
                        work
                    ),
                    Err(Error::Invalid(_))
                ));
            });
            assert_eq!(groups, 0);
        }
    }

    #[test]
    fn allocation_work_and_statistics_limits_propagate_as_errors() {
        let curve = prime_curve();
        let points = all_points(&curve);
        let mut short = Meter::new(Limits {
            vector: 1,
            ..Limits::default()
        });
        assert!(matches!(
            complement_chunk(&curve, curve.generator(), &points, &mut short),
            Err(Error::Limit(_))
        ));
        for steps in [0, 1, 3] {
            let mut meter = Meter::new(Limits {
                steps,
                ..Limits::default()
            });
            assert!(matches!(
                complement_chunk(&curve, curve.generator(), &points, &mut meter),
                Err(Error::Limit(_))
            ));
        }
        let mut statistics = BatchStatistics {
            batches: u64::MAX,
            ..BatchStatistics::default()
        };
        assert!(matches!(
            complement_chunk_with_statistics(
                &curve,
                curve.generator(),
                &points,
                &mut statistics,
                &mut Meter::new(Limits::default())
            ),
            Err(Error::Limit(_))
        ));
    }
}
