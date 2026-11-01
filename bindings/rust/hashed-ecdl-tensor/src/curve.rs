//! Arbitrary-precision, certified short-Weierstrass curves and subgroups.

use crate::arithmetic::{floor_root, inverse, is_prime, modpow, RandomSource, SquareRootContext};
use crate::{integrity, invalid, overflow, BigUint, Meter, Result};
use num_integer::Integer;
use num_traits::{One, Zero};
use std::collections::BTreeSet;

/// Canonical point representation; the identity has no affine coordinates.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum Point {
    /// The identity.
    Infinity,
    /// An affine point with coordinates in `[0,p)`.
    Affine {
        /// Abscissa.
        x: BigUint,
        /// Ordinate.
        y: BigUint,
    },
}

impl serde::Serialize for Point {
    fn serialize<S: serde::Serializer>(
        &self,
        serializer: S,
    ) -> std::result::Result<S::Ok, S::Error> {
        let value = match self {
            Self::Infinity => serde_json::Value::String("Infinity".into()),
            Self::Affine { x, y } => serde_json::json!({ "Affine": { "x": x, "y": y } }),
        };
        serde::Serialize::serialize(&value, serializer)
    }
}

struct AffineCoordinates {
    x: BigUint,
    y: BigUint,
}
json_record!(AffineCoordinates, required { x, y }, optional {});

impl<'de> serde::Deserialize<'de> for Point {
    fn deserialize<D: serde::Deserializer<'de>>(
        deserializer: D,
    ) -> std::result::Result<Self, D::Error> {
        struct PointVisitor;
        impl<'de> serde::de::Visitor<'de> for PointVisitor {
            type Value = Point;

            fn expecting(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
                formatter.write_str("\"Infinity\" or a single Affine object")
            }

            fn visit_str<E: serde::de::Error>(
                self,
                variant: &str,
            ) -> std::result::Result<Point, E> {
                if variant == "Infinity" {
                    Ok(Point::Infinity)
                } else {
                    Err(serde::de::Error::unknown_variant(variant, &["Infinity"]))
                }
            }

            fn visit_map<A: serde::de::MapAccess<'de>>(
                self,
                mut map: A,
            ) -> std::result::Result<Point, A::Error> {
                match map.next_key::<String>()?.as_deref() {
                    Some("Affine") => {
                        let AffineCoordinates { x, y } = map.next_value()?;
                        if let Some(field) = map.next_key::<String>()? {
                            return Err(if field == "Affine" {
                                serde::de::Error::duplicate_field("Affine")
                            } else {
                                serde::de::Error::unknown_field(&field, &["Affine"])
                            });
                        }
                        Ok(Point::Affine { x, y })
                    }
                    Some(variant) => Err(serde::de::Error::unknown_variant(variant, &["Affine"])),
                    None => Err(serde::de::Error::missing_field("Affine")),
                }
            }
        }
        deserializer.deserialize_any(PointVisitor)
    }
}

/// Certified nonsingular curve with a prime-order subgroup and full cardinality
/// `cofactor*r`.
#[derive(Clone, Debug)]
pub struct Curve {
    p: BigUint,
    a: BigUint,
    b: BigUint,
    r: BigUint,
    cofactor: BigUint,
    generator: Point,
    // Only the checked proof verifier populates this private context. Retain
    // auxiliary hash primes as well as p/r for construction and replay.
    certified_primes: BTreeSet<BigUint>,
}

impl Curve {
    /// Certify prime moduli, nonsingularity, the generator and full order.
    ///
    /// A nonzero point killed by prime `r` certifies a subgroup of order `r`.
    /// If the Hasse interval contains only the multiple `r`, this also certifies
    /// cofactor one. Ambiguous cases are counted exactly; no assumption
    /// that a declared subgroup is the entire group is silently accepted.
    pub fn new(
        p: BigUint,
        a: BigUint,
        b: BigUint,
        r: BigUint,
        generator: Point,
        meter: &mut Meter,
    ) -> Result<Self> {
        Self::with_cofactor(p, a, b, r, BigUint::one(), generator, meter)
    }

    /// Certify a full cardinality `cofactor*r`, with prime `r > cofactor` and
    /// a nonzero generator of the r-subgroup. The paper's unchanged asymptotic
    /// bound applies when the cofactor is fixed, not when it grows with p.
    pub fn with_cofactor(
        p: BigUint,
        a: BigUint,
        b: BigUint,
        r: BigUint,
        cofactor: BigUint,
        generator: Point,
        meter: &mut Meter,
    ) -> Result<Self> {
        Self::with_cofactor_and_certificates(p, a, b, r, cofactor, generator, &[], meter)
    }

    /// Certify the same curve using optional, independently verified primality
    /// proofs. Uncovered p/r values retain the exact default primality path;
    /// invalid supplied proofs are errors, never trusted prime assertions.
    pub fn with_cofactor_and_certificates(
        p: BigUint,
        a: BigUint,
        b: BigUint,
        r: BigUint,
        cofactor: BigUint,
        generator: Point,
        proofs: &[crate::primality::PrimeCertificate],
        meter: &mut Meter,
    ) -> Result<Self> {
        let primes = crate::primality::verify_certificates(proofs, meter)?;
        if p <= BigUint::from(3u8)
            || r <= BigUint::from(2u8)
            || (!primes.contains(&p) && !is_prime(&p, meter)?)
            || (!primes.contains(&r) && !is_prime(&r, meter)?)
            || a >= p
            || b >= p
            || cofactor.is_zero()
            || cofactor >= r
        {
            return Err(invalid("prime curve parameters"));
        }
        if (BigUint::from(4u8) * &a * &a * &a + BigUint::from(27u8) * &b * &b) % &p
            == BigUint::zero()
        {
            return Err(invalid("singular curve"));
        }
        let curve = Self {
            p,
            a,
            b,
            r,
            cofactor,
            generator,
            certified_primes: primes,
        };
        if curve.generator == Point::Infinity
            || !curve.contains(&curve.generator)
            || curve.mul(&curve.generator, &curve.r, meter)? != Point::Infinity
        {
            return Err(invalid("generator has not certified prime order"));
        }
        let radius = floor_root(&(&curve.p << 2), 2, meter)?;
        let center = &curve.p + BigUint::one();
        let lower = if center >= radius {
            &center - &radius
        } else {
            BigUint::zero()
        };
        let upper = &center + &radius;
        let first = lower.div_ceil(&curve.r);
        let last = upper / &curve.r;
        if first == curve.cofactor && last == curve.cofactor {
            return Ok(curve);
        }
        let mut cardinality = BigUint::one();
        let pm1 = &curve.p - BigUint::one();
        let mut x = BigUint::zero();
        while x < curve.p {
            meter.charge(1, "ambiguous Hasse interval point count")?;
            let rhs = curve.rhs(&x);
            if rhs.is_zero() {
                cardinality += BigUint::one();
            } else if modpow(&rhs, &(&pm1 >> 1), &curve.p, meter)? == BigUint::one() {
                cardinality += BigUint::from(2u8);
            }
            x += BigUint::one();
        }
        if cardinality != &curve.r * &curve.cofactor {
            return Err(invalid("declared order is not full cardinality"));
        }
        Ok(curve)
    }

    pub(crate) fn certifies_prime(&self, value: &BigUint, meter: &mut Meter) -> Result<bool> {
        if self.certified_primes.contains(value) {
            meter.bits(
                usize::try_from(value.bits()).map_err(|_| overflow("certified prime width"))?,
                "certified prime width",
            )?;
            meter.charge(1, "checked prime reuse")?;
            Ok(true)
        } else {
            is_prime(value, meter)
        }
    }

    /// Field modulus.
    pub fn modulus(&self) -> &BigUint {
        &self.p
    }
    /// Curve coefficient `a`.
    pub fn a(&self) -> &BigUint {
        &self.a
    }
    /// Curve coefficient `b`.
    pub fn b(&self) -> &BigUint {
        &self.b
    }
    /// Certified prime group order.
    pub fn order(&self) -> &BigUint {
        &self.r
    }
    /// Certified cofactor of the prime-order subgroup.
    pub fn cofactor(&self) -> &BigUint {
        &self.cofactor
    }
    /// Certified nonzero generator.
    pub fn generator(&self) -> &Point {
        &self.generator
    }

    pub(crate) fn rhs(&self, x: &BigUint) -> BigUint {
        (x * x % &self.p * x + &self.a * x + &self.b) % &self.p
    }

    /// Canonical coordinate and curve-equation check.
    pub fn contains(&self, point: &Point) -> bool {
        match point {
            Point::Infinity => true,
            Point::Affine { x, y } => x < &self.p && y < &self.p && y * y % &self.p == self.rhs(x),
        }
    }
    /// Check membership in the certified prime-order subgroup.
    pub fn in_subgroup(&self, point: &Point, meter: &mut Meter) -> Result<bool> {
        if !self.contains(point) {
            return Ok(false);
        }
        Ok(self.mul(point, &self.r, meter)? == Point::Infinity)
    }

    /// Checked affine group addition, including every exceptional branch.
    pub fn add(&self, left: &Point, right: &Point, meter: &mut Meter) -> Result<Point> {
        meter.charge(1, "curve addition")?;
        crate::metrics::group(left == right && left != &Point::Infinity)?;
        if !self.contains(left) || !self.contains(right) {
            return Err(invalid("curve point"));
        }
        let (x, y, xx, yy) = match (left, right) {
            (Point::Infinity, _) => return Ok(right.clone()),
            (_, Point::Infinity) => return Ok(left.clone()),
            (Point::Affine { x, y }, Point::Affine { x: xx, y: yy }) => (x, y, xx, yy),
        };
        if x == xx && (y + yy) % &self.p == BigUint::zero() {
            return Ok(Point::Infinity);
        }
        let (num, den) = if x == xx {
            (
                (BigUint::from(3u8) * x * x + &self.a) % &self.p,
                (y << 1) % &self.p,
            )
        } else {
            (self.sub(yy, y), self.sub(xx, x))
        };
        let slope = num * inverse(&den, &self.p)? % &self.p;
        let nx = self.sub(&self.sub(&(&slope * &slope % &self.p), x), xx);
        let ny = self.sub(&(&slope * self.sub(x, &nx) % &self.p), y);
        Ok(Point::Affine { x: nx, y: ny })
    }

    pub(crate) fn sub(&self, x: &BigUint, y: &BigUint) -> BigUint {
        (x + &self.p - y) % &self.p
    }

    /// Checked point negation.
    pub fn negate(&self, point: &Point) -> Result<Point> {
        if !self.contains(point) {
            return Err(invalid("curve point"));
        }
        Ok(match point {
            Point::Infinity => Point::Infinity,
            Point::Affine { x, y } => Point::Affine {
                x: x.clone(),
                y: (&self.p - y) % &self.p,
            },
        })
    }

    /// Scalar multiplication without reducing the scalar first (also used to
    /// certify the declared order).
    pub fn mul(&self, point: &Point, scalar: &BigUint, meter: &mut Meter) -> Result<Point> {
        crate::metrics::scalar()?;
        if !self.contains(point) {
            return Err(invalid("curve point"));
        }
        meter.bits(scalar.bits() as usize, "scalar multiplication")?;
        let mut n = scalar.clone();
        let mut base = point.clone();
        let mut out = Point::Infinity;
        while !n.is_zero() {
            if n.bit(0) {
                out = self.add(&out, &base, meter)?;
            }
            n >>= 1;
            if !n.is_zero() {
                base = self.add(&base, &base, meter)?;
            }
        }
        Ok(out)
    }

    /// Section 3.2's injective compressed encoding, excluding the identity.
    pub fn encode(&self, point: &Point) -> Result<BigUint> {
        if !self.contains(point) {
            return Err(invalid("curve point"));
        }
        match point {
            Point::Infinity => Err(invalid("identity has no factor-base encoding")),
            Point::Affine { x, y } => Ok((x << 1) + BigUint::from(u8::from(y.bit(0)))),
        }
    }

    /// Decode an affine compressed point, using expected-polynomial-time root
    /// extraction rather than an O(p) root table.
    pub fn decode(
        &self,
        z: &BigUint,
        rng: &mut impl RandomSource,
        meter: &mut Meter,
    ) -> Result<Option<Point>> {
        self.decoder()?.decode(z, rng, meter)
    }

    /// Prepare a decoder that reuses square-root setup for many encodings of
    /// this certified curve. Randomness and work are consumed lazily by decode.
    pub fn decoder(&self) -> Result<PointDecoder<'_>> {
        Ok(PointDecoder {
            curve: self,
            roots: SquareRootContext::new(&self.p)?,
        })
    }
}

/// Batch compressed-point decoding tied to one certified curve.
/// Modulus parameters and one lazily sampled nonresidue are reused; coordinate
/// parity and the curve equation are checked for every decoded point.
pub struct PointDecoder<'curve> {
    curve: &'curve Curve,
    roots: SquareRootContext<'curve>,
}

impl PointDecoder<'_> {
    /// Decode one nonidentity encoding, preserving canonical point selection.
    /// Nonsquares and out-of-range encodings return `None`; exhausted resources
    /// and random-source failures remain errors.
    pub fn decode(
        &mut self,
        z: &BigUint,
        rng: &mut impl RandomSource,
        meter: &mut Meter,
    ) -> Result<Option<Point>> {
        let curve = self.curve;
        if z >= &(&curve.p << 1) {
            return Ok(None);
        }
        let x = z >> 1;
        let Some(mut y) = self.roots.root(&curve.rhs(&x), rng, meter)? else {
            return Ok(None);
        };
        if y.bit(0) != z.bit(0) {
            y = (&curve.p - y) % &curve.p;
        }
        if y.bit(0) != z.bit(0) {
            return Ok(None);
        }
        let point = Point::Affine { x, y };
        if !curve.contains(&point) {
            return Err(integrity("compressed point replay"));
        }
        Ok(Some(point))
    }
}

#[cfg(test)]
pub(crate) fn tiny(meter: &mut Meter) -> Curve {
    Curve::new(
        5u8.into(),
        2u8.into(),
        1u8.into(),
        7u8.into(),
        Point::Affine {
            x: 0u8.into(),
            y: 1u8.into(),
        },
        meter,
    )
    .unwrap()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::arithmetic::Seeded;
    use crate::Limits;
    #[test]
    fn prime_order_certificate_and_point_encoding() {
        let mut meter = Meter::new(Limits::default());
        let curve = tiny(&mut meter);
        let mut rng = Seeded(5);
        for k in 1..7u8 {
            let point = curve.mul(curve.generator(), &k.into(), &mut meter).unwrap();
            assert_eq!(
                curve
                    .decode(&curve.encode(&point).unwrap(), &mut rng, &mut meter)
                    .unwrap(),
                Some(point.clone())
            );
            assert_eq!(
                curve
                    .add(&point, &curve.negate(&point).unwrap(), &mut meter)
                    .unwrap(),
                Point::Infinity
            );
        }
        assert!(Curve::new(
            5u8.into(),
            2u8.into(),
            1u8.into(),
            3u8.into(),
            curve.generator().clone(),
            &mut meter
        )
        .is_err());
        assert!(Curve::new(
            15u8.into(),
            2u8.into(),
            1u8.into(),
            7u8.into(),
            curve.generator().clone(),
            &mut meter
        )
        .is_err());
    }
}
