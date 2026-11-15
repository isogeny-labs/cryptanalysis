//! Reusable simultaneous multiplication for public relation coefficients.
//!
//! This is HAC Algorithm 14.88 in additive notation for two fixed subgroup
//! points. It is variable-time and is not an API for secret scalar arithmetic.

use crate::curve::{Curve, Point};
use crate::{invalid, overflow, BigUint, Meter, Result};

/// Immutable three-point table, bound to its own certified curve.
/// Construction and all checked affine operations consume the caller's meter.
pub struct JointTable {
    curve: Curve,
    points: [Point; 3],
}

impl JointTable {
    /// Validate both points in the certified subgroup and prepare their sum.
    /// Identity, equal and opposite points are allowed.
    pub fn new(curve: &Curve, left: &Point, right: &Point, meter: &mut Meter) -> Result<Self> {
        if !curve.in_subgroup(left, meter)? || !curve.in_subgroup(right, meter)? {
            return Err(invalid("joint point outside the certified subgroup"));
        }
        Self::from_subgroup_points(curve, left, right, meter)
    }

    // Only used after the collector's original target validation. The other
    // point is its curve's certified generator. No unchecked group formula.
    pub(crate) fn from_subgroup_points(
        curve: &Curve,
        left: &Point,
        right: &Point,
        meter: &mut Meter,
    ) -> Result<Self> {
        meter.vector(3, "joint point table")?;
        let sum = curve.add(left, right, meter)?;
        Ok(Self {
            curve: curve.clone(),
            points: [left.clone(), right.clone(), sum],
        })
    }

    /// Compute `u*left + v*right` with one shared doubling chain.
    /// Scalars are not reduced. Width/step failures remain errors.
    pub fn evaluate(&self, u: &BigUint, v: &BigUint, meter: &mut Meter) -> Result<Point> {
        let bits = u.bits().max(v.bits());
        meter.bits(
            usize::try_from(bits).map_err(|_| overflow("joint scalar width"))?,
            "joint scalar multiplication",
        )?;
        if bits == 0 {
            return Ok(Point::Infinity);
        }
        let digit = |bit| usize::from(u.bit(bit)) + 2 * usize::from(v.bit(bit));
        // The leading column is nonzero; assigning it avoids an identity
        // doubling/addition. Zero columns below require only a doubling.
        let mut result = self.points[digit(bits - 1) - 1].clone();
        for bit in (0..bits - 1).rev() {
            result = self.curve.add(&result, &result, meter)?;
            let index = digit(bit);
            if index != 0 {
                result = self.curve.add(&result, &self.points[index - 1], meter)?;
            }
        }
        Ok(result)
    }
}
