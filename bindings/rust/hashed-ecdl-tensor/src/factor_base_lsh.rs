//! Bit-sampling buckets for exact factor-base point lookup.
//!
//! This is the Hamming-coordinate bit-sampling LSH family applied only as a
//! cheap candidate index. Coordinate closeness has no established relation to
//! elliptic-curve addition. Equal points always share every sampled bit;
//! full point equality, not bucket membership, decides a hit.

use crate::arithmetic::{random_below, Seeded};
use crate::curve::Point;
use crate::{integrity, invalid, BigUint, Error, Meter, Result};
use num_traits::ToPrimitive;
use std::collections::HashMap;

pub(crate) struct BitSampleIndex {
    width: u64,
    positions: Vec<u64>,
    buckets: HashMap<u32, Vec<usize>>,
}

impl BitSampleIndex {
    pub(crate) fn new(
        points: &[Point],
        width: u64,
        bits: u8,
        seed: u64,
        meter: &mut Meter,
    ) -> Result<Self> {
        let span = width
            .checked_mul(2)
            .ok_or_else(|| invalid("LSH coordinate width"))?;
        if bits == 0 || bits > 24 || u64::from(bits) > span {
            return Err(invalid(
                "LSH sample bits must fit both coordinates and be at most 24",
            ));
        }
        meter.vector(usize::from(bits), "LSH sampled positions")?;
        meter.vector(points.len(), "LSH factor-base points")?;
        let mut rng = Seeded(seed);
        let mut positions = Vec::new();
        positions
            .try_reserve_exact(usize::from(bits))
            .map_err(|_| Error::Limit("LSH position allocation".into()))?;
        // Floyd sampling: distinct uniform positions without a width-sized
        // shuffle buffer. This RNG never touches relation-label randomness.
        for j in (span - u64::from(bits))..span {
            let choice = random_below(&BigUint::from(j + 1), &mut rng, meter)?
                .to_u64()
                .ok_or_else(|| integrity("LSH sampled position width"))?;
            positions.push(if positions.contains(&choice) {
                j
            } else {
                choice
            });
        }
        let mut buckets: HashMap<u32, Vec<usize>> = HashMap::new();
        buckets
            .try_reserve(points.len())
            .map_err(|_| Error::Limit("LSH bucket allocation".into()))?;
        meter.vector(buckets.capacity(), "LSH bucket capacity")?;
        let mut index = Self {
            width,
            positions,
            buckets,
        };
        for (position, point) in points.iter().enumerate() {
            meter.charge(u64::from(bits), "LSH base projection bits")?;
            let signature = index
                .signature(point)
                .ok_or_else(|| integrity("identity in LSH factor base"))?;
            let bucket = index.buckets.entry(signature).or_default();
            bucket
                .try_reserve(1)
                .map_err(|_| Error::Limit("LSH bucket entry allocation".into()))?;
            bucket.push(position);
        }
        Ok(index)
    }

    fn signature(&self, point: &Point) -> Option<u32> {
        let Point::Affine { x, y } = point else {
            return None;
        };
        let mut signature = 0u32;
        for (out, &position) in self.positions.iter().enumerate() {
            let bit = if position < self.width {
                x.bit(position)
            } else {
                y.bit(position - self.width)
            };
            if bit {
                signature |= 1u32 << out;
            }
        }
        Some(signature)
    }

    pub(crate) fn contains_exact(
        &self,
        points: &[Point],
        query: &Point,
        meter: &mut Meter,
    ) -> Result<(bool, usize)> {
        meter.charge(
            u64::try_from(self.positions.len()).unwrap_or(u64::MAX),
            "LSH query projection bits",
        )?;
        let Some(signature) = self.signature(query) else {
            return Ok((false, 0));
        };
        let mut compared = 0usize;
        if let Some(bucket) = self.buckets.get(&signature) {
            for &position in bucket {
                meter.charge(1, "LSH full-point comparison")?;
                compared += 1;
                let candidate = points
                    .get(position)
                    .ok_or_else(|| integrity("LSH candidate index range"))?;
                if candidate == query {
                    return Ok((true, compared));
                }
            }
        }
        Ok((false, compared))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::Limits;

    fn point(x: u8) -> Point {
        Point::Affine {
            x: x.into(),
            y: (x ^ 7).into(),
        }
    }

    #[test]
    fn one_bit_collisions_never_become_point_hits() {
        let mut meter = Meter::new(Limits::default());
        let points: Vec<_> = (0..8).map(point).collect();
        let index = BitSampleIndex::new(&points, 4, 1, 9, &mut meter).unwrap();
        for p in &points {
            assert!(index.contains_exact(&points, p, &mut meter).unwrap().0);
        }
        let absent = (8..16)
            .map(point)
            .find(|p| index.buckets.contains_key(&index.signature(p).unwrap()))
            .unwrap();
        let (found, compared) = index.contains_exact(&points, &absent, &mut meter).unwrap();
        assert!(!found);
        assert!(compared > 0);
        assert!(
            !index
                .contains_exact(&points, &Point::Infinity, &mut meter)
                .unwrap()
                .0
        );
    }

    #[test]
    fn invalid_sample_width_is_rejected() {
        let mut meter = Meter::new(Limits::default());
        assert!(BitSampleIndex::new(&[], 4, 0, 0, &mut meter).is_err());
        assert!(BitSampleIndex::new(&[], 4, 9, 0, &mut meter).is_err());
    }
}
