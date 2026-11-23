use crate::{Error, Result};

#[derive(Clone, Copy, Debug)]
pub(crate) struct F<const B: u32>;

impl<const B: u32> F<B> {
    pub(crate) const P: u64 = if B > 1 && B < 64 { (1u64 << B) - 1 } else { 0 };
    pub(crate) fn supported() -> bool {
        matches!(B, 3 | 5 | 7 | 13 | 17 | 19 | 31 | 61)
    }
    #[inline(always)]
    pub(crate) fn add(a: u64, b: u64) -> u64 {
        let sum = a + b;
        if sum >= Self::P {
            sum - Self::P
        } else {
            sum
        }
    }
    #[inline(always)]
    pub(crate) fn sub(a: u64, b: u64) -> u64 {
        if a >= b {
            a - b
        } else {
            a + Self::P - b
        }
    }
    #[inline(always)]
    pub(crate) fn mul(a: u64, b: u64) -> u64 {
        let value = if B <= 31 {
            let product = a * b;
            (product & Self::P) + (product >> B)
        } else {
            let product = u128::from(a) * u128::from(b);
            (product & u128::from(Self::P)) as u64 + (product >> B) as u64
        };
        if value >= Self::P {
            value - Self::P
        } else {
            value
        }
    }
    #[inline(always)]
    pub(crate) fn sq(a: u64) -> u64 {
        Self::mul(a, a)
    }
    pub(crate) fn pow(mut a: u64, mut exponent: u64) -> u64 {
        let mut result = 1;
        while exponent != 0 {
            if exponent & 1 != 0 {
                result = Self::mul(result, a);
            }
            a = Self::sq(a);
            exponent >>= 1;
        }
        result
    }
    #[inline(always)]
    fn squares<const N: usize>(mut a: u64) -> u64 {
        for _ in 0..N {
            a = Self::sq(a);
        }
        a
    }
    /// Internal inv(0)=0 agrees with exponentiation; callers exclude zero.
    #[inline]
    pub(crate) fn inv(a: u64) -> u64 {
        if B == 31 || B == 61 || B == 19 {
            let a2 = Self::mul(Self::sq(a), a);
            let a4 = Self::mul(Self::squares::<2>(a2), a2);
            let a8 = Self::mul(Self::squares::<4>(a4), a4);
            let a16 = Self::mul(Self::squares::<8>(a8), a8);
            let power = if B == 19 {
                Self::mul(Self::sq(a16), a)
            } else if B == 31 {
                let a24 = Self::mul(Self::squares::<8>(a16), a8);
                let a28 = Self::mul(Self::squares::<4>(a24), a4);
                Self::mul(Self::sq(a28), a)
            } else {
                let a32 = Self::mul(Self::squares::<16>(a16), a16);
                let a48 = Self::mul(Self::squares::<16>(a32), a16);
                let a56 = Self::mul(Self::squares::<8>(a48), a8);
                let a58 = Self::mul(Self::squares::<2>(a56), a2);
                Self::mul(Self::sq(a58), a)
            };
            Self::mul(Self::squares::<2>(power), a)
        } else {
            Self::pow(a, Self::P - 2)
        }
    }
}

/// Canonical affine coordinates; infinity is represented by `None`.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct Point {
    x: u64,
    y: u64,
}

impl Point {
    /// Canonical x coordinate.
    pub fn x(self) -> u64 {
        self.x
    }
    /// Canonical y coordinate.
    pub fn y(self) -> u64 {
        self.y
    }
    /// Affine coordinate pair.
    pub fn coordinates(self) -> (u64, u64) {
        (self.x, self.y)
    }
}

/// Nonsingular `y²=x³+ax+b` over `F_(2^B-1)` for a supported Mersenne prime.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Curve<const B: u32> {
    pub(crate) a: u64,
    pub(crate) b: u64,
}

/// Reusable storage for simultaneous affine additions.
#[derive(Clone, Debug, Default)]
pub struct BatchScratch {
    prefix: Vec<u64>,
    denominators: Vec<u64>,
}

// Jacobian coordinates (X/Z^2, Y/Z^3); Z=0 denotes infinity.
// Scalar multiplication keeps all intermediate points here, with at most
// one field inversion at the final affine conversion. Affine addition stays
// separate for the batched walker and as a correctness-test reference.
#[derive(Clone, Copy)]
struct Jacobian {
    x: u64,
    y: u64,
    z: u64,
}

impl Jacobian {
    const IDENTITY: Self = Self { x: 0, y: 1, z: 0 };

    fn double<const B: u32>(self, curve: Curve<B>) -> Self {
        if self.z == 0 || self.y == 0 {
            return Self::IDENTITY;
        }
        let xx = F::<B>::sq(self.x);
        let yy = F::<B>::sq(self.y);
        let yyyy = F::<B>::sq(yy);
        let xyy = F::<B>::mul(self.x, yy);
        let twice_xyy = F::<B>::add(xyy, xyy);
        let s = F::<B>::add(twice_xyy, twice_xyy);
        let three_xx = F::<B>::add(xx, F::<B>::add(xx, xx));
        let m = if curve.a == 0 {
            three_xx
        } else {
            F::<B>::add(
                three_xx,
                F::<B>::mul(curve.a, F::<B>::sq(F::<B>::sq(self.z))),
            )
        };
        let x = F::<B>::sub(F::<B>::sq(m), F::<B>::add(s, s));
        let twice_yyyy = F::<B>::add(yyyy, yyyy);
        let four_yyyy = F::<B>::add(twice_yyyy, twice_yyyy);
        let y = F::<B>::sub(
            F::<B>::mul(m, F::<B>::sub(s, x)),
            F::<B>::add(four_yyyy, four_yyyy),
        );
        Self {
            x,
            y,
            z: F::<B>::mul(F::<B>::add(self.y, self.y), self.z),
        }
    }

    fn add_affine<const B: u32>(self, point: Point, curve: Curve<B>) -> Self {
        if self.z == 0 {
            return Self {
                x: point.x,
                y: point.y,
                z: 1,
            };
        }
        let zz = F::<B>::sq(self.z);
        let u = F::<B>::mul(point.x, zz);
        let s = F::<B>::mul(point.y, F::<B>::mul(self.z, zz));
        let h = F::<B>::sub(u, self.x);
        let r = F::<B>::sub(s, self.y);
        if h == 0 {
            return if r == 0 {
                self.double(curve)
            } else {
                Self::IDENTITY
            };
        }
        let hh = F::<B>::sq(h);
        let hhh = F::<B>::mul(h, hh);
        let v = F::<B>::mul(self.x, hh);
        let x = F::<B>::sub(F::<B>::sub(F::<B>::sq(r), hhh), F::<B>::add(v, v));
        let y = F::<B>::sub(F::<B>::mul(r, F::<B>::sub(v, x)), F::<B>::mul(self.y, hhh));
        Self {
            x,
            y,
            z: F::<B>::mul(self.z, h),
        }
    }

    fn affine<const B: u32>(self) -> Option<Point> {
        if self.z == 0 {
            return None;
        }
        if self.z == 1 {
            return Some(Point {
                x: self.x,
                y: self.y,
            });
        }
        let inverse = F::<B>::inv(self.z);
        let inverse_squared = F::<B>::sq(inverse);
        Some(Point {
            x: F::<B>::mul(self.x, inverse_squared),
            y: F::<B>::mul(self.y, F::<B>::mul(inverse, inverse_squared)),
        })
    }

    fn equals<const B: u32>(self, other: Self) -> bool {
        if self.z == 0 || other.z == 0 {
            return self.z == other.z;
        }
        let zz = F::<B>::sq(self.z);
        let other_zz = F::<B>::sq(other.z);
        F::<B>::mul(self.x, other_zz) == F::<B>::mul(other.x, zz)
            && F::<B>::mul(self.y, F::<B>::mul(other.z, other_zz))
                == F::<B>::mul(other.y, F::<B>::mul(self.z, zz))
    }
}

impl<const B: u32> Curve<B> {
    /// Validate the field, canonical coefficients, and discriminant.
    pub fn new(a: u64, b: u64) -> Result<Self> {
        if !F::<B>::supported() {
            return Err(Error::Invalid("unsupported Mersenne prime exponent"));
        }
        let p = F::<B>::P;
        if a >= p || b >= p {
            return Err(Error::Invalid("noncanonical curve coefficient"));
        }
        let delta = F::<B>::add(
            F::<B>::mul(4 % p, F::<B>::mul(F::<B>::sq(a), a)),
            F::<B>::mul(27 % p, F::<B>::sq(b)),
        );
        if delta == 0 {
            return Err(Error::Invalid("singular curve"));
        }
        Ok(Self { a, b })
    }
    /// Prime field modulus.
    pub fn modulus(self) -> u64 {
        F::<B>::P
    }
    /// Short-Weierstrass coefficients.
    pub fn coefficients(self) -> (u64, u64) {
        (self.a, self.b)
    }
    /// Validate canonical affine coordinates and curve membership.
    pub fn point(self, x: u64, y: u64) -> Result<Point> {
        let point = Point { x, y };
        if self.contains(Some(point)) {
            Ok(point)
        } else {
            Err(Error::Invalid("point is not on target curve"))
        }
    }
    /// Test canonical coordinates and curve membership, including infinity.
    pub fn contains(self, point: Option<Point>) -> bool {
        let Some(point) = point else {
            return true;
        };
        point.x < F::<B>::P
            && point.y < F::<B>::P
            && F::<B>::sq(point.y)
                == F::<B>::add(
                    F::<B>::add(
                        F::<B>::mul(F::<B>::sq(point.x), point.x),
                        F::<B>::mul(self.a, point.x),
                    ),
                    self.b,
                )
    }
    /// Lift an x coordinate to the smaller y representative, if it lifts.
    pub fn lift_x(self, x: u64) -> Result<Option<Point>> {
        if x >= F::<B>::P {
            return Err(Error::Invalid("noncanonical x coordinate"));
        }
        let rhs = F::<B>::add(
            F::<B>::add(F::<B>::mul(F::<B>::sq(x), x), F::<B>::mul(self.a, x)),
            self.b,
        );
        let y = F::<B>::pow(rhs, (F::<B>::P + 1) / 4);
        Ok((F::<B>::sq(y) == rhs).then(|| Point {
            x,
            y: y.min(F::<B>::sub(0, y)),
        }))
    }
    /// Negate a checked affine point.
    pub fn negate(self, point: Point) -> Result<Point> {
        if !self.contains(Some(point)) {
            return Err(Error::Invalid("point is not on target curve"));
        }
        Ok(self.neg_inner(point))
    }
    pub(crate) fn neg_inner(self, point: Point) -> Point {
        Point {
            x: point.x,
            y: F::<B>::sub(0, point.y),
        }
    }
    /// Add points after checking that they belong to this curve.
    pub fn add(self, left: Option<Point>, right: Option<Point>) -> Result<Option<Point>> {
        if !self.contains(left) || !self.contains(right) {
            return Err(Error::Invalid("point is not on target curve"));
        }
        Ok(self.add_inner(left, right))
    }
    pub(crate) fn add_inner(self, left: Option<Point>, right: Option<Point>) -> Option<Point> {
        let (left, right) = match (left, right) {
            (None, r) => return r,
            (l, None) => return l,
            (Some(l), Some(r)) => (l, r),
        };
        let (num, den) = if left.x == right.x {
            if F::<B>::add(left.y, right.y) == 0 {
                return None;
            }
            (
                F::<B>::add(F::<B>::mul(3, F::<B>::sq(left.x)), self.a),
                F::<B>::add(left.y, left.y),
            )
        } else {
            (F::<B>::sub(right.y, left.y), F::<B>::sub(right.x, left.x))
        };
        let slope = F::<B>::mul(num, F::<B>::inv(den));
        Some(self.finish_add(left, right, slope))
    }
    fn finish_add(self, left: Point, right: Point, slope: u64) -> Point {
        let x = if B == 31 {
            let p = F::<B>::P;
            // Canonical coordinates keep the offset nonnegative and the accumulator below 2^62.
            let accumulator = slope * slope + (2 * p - left.x - right.x);
            F::<B>::add(accumulator >> 31, accumulator & p)
        } else {
            F::<B>::sub(F::<B>::sub(F::<B>::sq(slope), left.x), right.x)
        };
        Point {
            x,
            y: F::<B>::sub(F::<B>::mul(slope, F::<B>::sub(left.x, x)), left.y),
        }
    }
    /// Multiply a checked point by an unsigned scalar.
    pub fn mul(self, point: Option<Point>, scalar: u64) -> Result<Option<Point>> {
        if !self.contains(point) {
            return Err(Error::Invalid("point is not on target curve"));
        }
        Ok(self.mul_inner(point, scalar))
    }
    pub(crate) fn mul_inner(self, point: Option<Point>, scalar: u64) -> Option<Point> {
        let point = point?;
        if scalar == 0 {
            return None;
        }
        let mut result = Jacobian {
            x: point.x,
            y: point.y,
            z: 1,
        };
        for bit in (0..(u64::BITS - scalar.leading_zeros() - 1)).rev() {
            result = result.double(self);
            if scalar & (1u64 << bit) != 0 {
                result = result.add_affine(point, self);
            }
        }
        result.affine::<B>()
    }
    // Simultaneously compute aG+bQ and compare with F+H, without affine
    // normalization or field inversion on either side. All inputs are
    // already checked by preparation and the caller's row-index bounds.
    pub(crate) fn matches_linear_combination(
        self,
        left: (Point, u64),
        right: (Point, u64),
        sum: (Point, Point),
    ) -> bool {
        let ((g, a), (q, b)) = (left, right);
        let mut result = Jacobian::IDENTITY;
        for bit in (0..(u64::BITS - (a | b).leading_zeros())).rev() {
            result = result.double(self);
            if a & (1u64 << bit) != 0 {
                result = result.add_affine(g, self);
            }
            if b & (1u64 << bit) != 0 {
                result = result.add_affine(q, self);
            }
        }
        let expected = Jacobian {
            x: sum.0.x,
            y: sum.0.y,
            z: 1,
        }
        .add_affine(sum.1, self);
        result.equals::<B>(expected)
    }
    // Simultaneously compute aG+bQ and compare with an m-term signed base sum
    // in Jacobian coordinates without affine normalization or field inversion.
    pub(crate) fn matches_multi_linear_combination(
        self,
        left: (Point, u64),
        right: (Point, u64),
        summands: &[Point],
    ) -> bool {
        let ((g, a), (q, b)) = (left, right);
        let mut result = Jacobian::IDENTITY;
        for bit in (0..(u64::BITS - (a | b).leading_zeros())).rev() {
            result = result.double(self);
            if a & (1u64 << bit) != 0 {
                result = result.add_affine(g, self);
            }
            if b & (1u64 << bit) != 0 {
                result = result.add_affine(q, self);
            }
        }
        let mut expected = Jacobian::IDENTITY;
        for &point in summands {
            expected = expected.add_affine(point, self);
        }
        result.equals::<B>(expected)
    }
    /// Advance independent points with one shared inversion and checked exceptions.
    pub fn batch_add(
        self,
        points: &mut [Option<Point>],
        steps: &[Option<Point>],
        scratch: &mut BatchScratch,
    ) -> Result<()> {
        if points.len() != steps.len() {
            return Err(Error::Invalid("batch length mismatch"));
        }
        if points.iter().chain(steps).any(|p| !self.contains(*p)) {
            return Err(Error::Invalid("batch contains an off-curve point"));
        }
        self.batch_add_inner(points, steps, scratch);
        Ok(())
    }
    pub(crate) fn batch_add_inner(
        self,
        points: &mut [Option<Point>],
        steps: &[Option<Point>],
        scratch: &mut BatchScratch,
    ) {
        scratch.prefix.resize(points.len(), 0);
        scratch.denominators.resize(points.len(), 0);
        let mut product = 1;
        for i in 0..points.len() {
            scratch.prefix[i] = product;
            let den = match (points[i], steps[i]) {
                (Some(a), Some(b)) if a.x != b.x => F::<B>::sub(b.x, a.x),
                _ => 0,
            };
            scratch.denominators[i] = den;
            if den != 0 {
                product = F::<B>::mul(product, den);
            }
        }
        let mut inverse = F::<B>::inv(product);
        for i in (0..points.len()).rev() {
            let den = scratch.denominators[i];
            if den == 0 {
                points[i] = self.add_inner(points[i], steps[i]);
                continue;
            }
            let inv = F::<B>::mul(inverse, scratch.prefix[i]);
            inverse = F::<B>::mul(inverse, den);
            let a = points[i].expect("generic batch point");
            let b = steps[i].expect("generic batch step");
            points[i] = Some(self.finish_add(a, b, F::<B>::mul(F::<B>::sub(b.y, a.y), inv)));
        }
    }
}

pub(crate) fn mul_mod(a: u64, b: u64, n: u64) -> u64 {
    (u128::from(a) * u128::from(b) % u128::from(n)) as u64
}
pub(crate) fn add_mod(a: u64, b: u64, n: u64) -> u64 {
    let sum = a + b;
    if sum >= n {
        sum - n
    } else {
        sum
    }
}
pub(crate) fn sub_mod(a: u64, b: u64, n: u64) -> u64 {
    if a >= b {
        a - b
    } else {
        a + n - b
    }
}
pub(crate) fn pow_mod(mut a: u64, mut e: u64, n: u64) -> u64 {
    let mut result = 1;
    while e != 0 {
        if e & 1 != 0 {
            result = mul_mod(result, a, n);
        }
        a = mul_mod(a, a, n);
        e >>= 1;
    }
    result
}
pub(crate) fn is_prime(n: u64) -> bool {
    if n < 2 {
        return false;
    }
    for p in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37] {
        if n == p {
            return true;
        }
        if n % p == 0 {
            return false;
        }
    }
    let s = (n - 1).trailing_zeros();
    let d = (n - 1) >> s;
    for base in [2, 325, 9375, 28178, 450775, 9780504, 1795265022] {
        let a = base % n;
        if a == 0 {
            continue;
        }
        let mut x = pow_mod(a, d, n);
        if x == 1 || x == n - 1 {
            continue;
        }
        let mut witness = true;
        for _ in 1..s {
            x = mul_mod(x, x, n);
            if x == n - 1 {
                witness = false;
                break;
            }
        }
        if witness {
            return false;
        }
    }
    true
}

#[cfg(test)]
mod tests {
    use super::*;

    fn affine_multiply<const B: u32>(
        curve: Curve<B>,
        mut point: Option<Point>,
        mut scalar: u64,
    ) -> Option<Point> {
        let mut result = None;
        while scalar != 0 {
            if scalar & 1 != 0 {
                result = curve.add(result, point).unwrap();
            }
            point = curve.add(point, point).unwrap();
            scalar >>= 1;
        }
        result
    }

    fn exhaustive_multiplication<const B: u32>(curve: Curve<B>) {
        assert_eq!(curve.mul(None, u64::MAX).unwrap(), None);
        for x in 0..curve.modulus() {
            let Some(point) = curve.lift_x(x).unwrap() else {
                continue;
            };
            for point in [point, curve.negate(point).unwrap()] {
                let mut expected = None;
                // Repeated affine addition is independent of the projective
                // formulas and crosses the group order at least once.
                for scalar in 0..=2 * curve.modulus() + 3 {
                    assert_eq!(curve.mul(Some(point), scalar).unwrap(), expected);
                    expected = curve.add(expected, Some(point)).unwrap();
                }
                for scalar in [1u64 << 63, u64::MAX - 1, u64::MAX] {
                    assert_eq!(
                        curve.mul(Some(point), scalar).unwrap(),
                        affine_multiply(curve, Some(point), scalar)
                    );
                }
            }
        }
    }

    #[test]
    fn projective_multiplication_matches_affine_addition_in_small_groups() {
        // All nonsingular curves over F_7, including 2-torsion, inverses,
        // intermediate infinity and equal-point mixed additions.
        for a in 0..7 {
            for b in 0..7 {
                if let Ok(curve) = Curve::<3>::new(a, b) {
                    exhaustive_multiplication(curve);
                }
            }
        }
        exhaustive_multiplication(Curve::<5>::new(1, 0).unwrap());
        exhaustive_multiplication(Curve::<7>::new(2, 51).unwrap());
    }

    fn large_field_multiplication<const B: u32>(curve: Curve<B>) {
        for x in 0..32 {
            let Some(point) = curve.lift_x(x).unwrap() else {
                continue;
            };
            for point in [point, curve.negate(point).unwrap()] {
                for scalar in [0, 1, 2, 3, 31, 32, (1u64 << 31) - 1, 1u64 << 63, u64::MAX] {
                    assert_eq!(
                        curve.mul(Some(point), scalar).unwrap(),
                        affine_multiply(curve, Some(point), scalar)
                    );
                }
            }
        }
    }

    #[test]
    fn projective_multiplication_matches_affine_reference_in_both_requested_fields() {
        large_field_multiplication(Curve::<31>::new(2, 14).unwrap());
        large_field_multiplication(Curve::<61>::new(0, 3).unwrap());
    }

    #[test]
    fn joint_row_validation_matches_exhaustive_affine_equations() {
        let curve = Curve::<3>::new(1, 0).unwrap();
        let mut points = Vec::new();
        for x in 0..7 {
            for y in 0..7 {
                if let Ok(point) = curve.point(x, y) {
                    points.push(point);
                }
            }
        }
        let sums: Vec<_> = points
            .iter()
            .flat_map(|&p| {
                points
                    .iter()
                    .map(move |&q| ((p, q), curve.add(Some(p), Some(q)).unwrap()))
            })
            .collect();
        for &g in &points {
            for &q in &points {
                for a in 0..=8 {
                    for b in 0..=8 {
                        let expected = curve
                            .add(
                                affine_multiply(curve, Some(g), a),
                                affine_multiply(curve, Some(q), b),
                            )
                            .unwrap();
                        for &(sum, point) in &sums {
                            assert_eq!(
                                curve.matches_linear_combination((g, a), (q, b), sum),
                                expected == point
                            );
                        }
                    }
                }
            }
        }
    }

    fn large_field_joint_rows<const B: u32>(curve: Curve<B>, generator: Point) {
        let target = affine_multiply(curve, Some(generator), 37).unwrap();
        for (a, b) in [
            (0, 0),
            (0, 1),
            (1, 0),
            (1, 1),
            (17, 23),
            (u64::MAX, 0),
            (0, u64::MAX),
            (u64::MAX, u64::MAX),
            (1u64 << 63, u64::MAX - 1),
        ] {
            let expected = curve
                .add(
                    affine_multiply(curve, Some(generator), a),
                    affine_multiply(curve, Some(target), b),
                )
                .unwrap();
            let mut first = generator;
            let mut second = curve
                .add(expected, Some(curve.negate(first).unwrap()))
                .unwrap();
            if second.is_none() {
                first = curve.negate(first).unwrap();
                second = curve
                    .add(expected, Some(curve.negate(first).unwrap()))
                    .unwrap();
            }
            let second = second.unwrap();
            assert!(curve.matches_linear_combination((generator, a), (target, b), (first, second)));
            assert!(!curve.matches_linear_combination(
                (generator, a),
                (target, b),
                (first, curve.negate(second).unwrap())
            ));
        }
    }

    #[test]
    fn joint_row_validation_matches_affine_reference_in_both_requested_fields() {
        let curve = Curve::<31>::new(2, 14).unwrap();
        large_field_joint_rows(curve, curve.point(1, 814455902).unwrap());
        let curve = Curve::<61>::new(0, 3).unwrap();
        large_field_joint_rows(
            curve,
            curve.point(78862349111012854, 1899276942447683421).unwrap(),
        );
    }

    fn reference_pow(mut a: u128, mut e: u64, modulus: u128) -> u64 {
        let mut result = 1;
        while e != 0 {
            if e & 1 != 0 {
                result = result * a % modulus;
            }
            a = a * a % modulus;
            e >>= 1;
        }
        result as u64
    }
    fn field_case<const B: u32>() {
        let p = F::<B>::P;
        let mut state = 0x12345678u64;
        for i in 0..1000 {
            state = state
                .wrapping_mul(6364136223846793005)
                .wrapping_add(1442695040888963407);
            let a = if i == 0 { p - 1 } else { state % p };
            state = state.rotate_left(17).wrapping_add(1);
            let b = if i == 0 { p - 1 } else { state % p };
            assert_eq!(
                F::<B>::mul(a, b),
                (u128::from(a) * u128::from(b) % u128::from(p)) as u64
            );
            assert_eq!(
                F::<B>::inv(a),
                reference_pow(u128::from(a), p - 2, u128::from(p))
            );
            if a != 0 {
                assert_eq!(F::<B>::mul(a, F::<B>::inv(a)), 1);
            }
        }
    }
    #[test]
    fn reduction_and_fixed_inverse_match_integer_reference() {
        field_case::<7>();
        field_case::<19>();
        field_case::<31>();
        field_case::<61>();
    }
    #[test]
    fn m31_affine_coordinates_match_wide_remainders() {
        let curve = Curve::<31>::new(2, 14).unwrap();
        let p = u128::from(curve.modulus());
        let edges = [0, 1, 2, (p / 2) as u64, (p - 2) as u64, (p - 1) as u64];
        // finish_add is a polynomial once the slope is supplied. Testing
        // arbitrary canonical inputs includes rare edge cases of the fold.
        for slope in edges {
            for x1 in edges {
                for x2 in edges {
                    let left = Point { x: x1, y: x2 };
                    let right = Point { x: x2, y: x1 };
                    let got = curve.finish_add(left, right, slope);
                    let s = u128::from(slope);
                    let x = (s * s + 2 * p - u128::from(x1) - u128::from(x2)) % p;
                    let y = (s * (u128::from(x1) + p - x) + p - u128::from(left.y)) % p;
                    assert_eq!(got.coordinates(), (x as u64, y as u64));
                }
            }
        }
    }

    #[test]
    fn batched_exceptions_match_individual_additions() {
        let curve = Curve::<7>::new(2, 51).unwrap();
        let g = curve.point(3, 46).unwrap();
        let mut points: Vec<_> = (0..64).map(|k| curve.mul(Some(g), k).unwrap()).collect();
        let mut steps: Vec<_> = (0..64)
            .map(|k| curve.mul(Some(g), 2 * k + 1).unwrap())
            .collect();
        points[0] = None;
        steps[1] = None;
        points[2] = Some(g);
        steps[2] = Some(g);
        points[3] = Some(g);
        steps[3] = Some(curve.negate(g).unwrap());
        points[4] = None;
        steps[4] = None;
        let expected: Vec<_> = points
            .iter()
            .zip(&steps)
            .map(|(&a, &b)| curve.add(a, b).unwrap())
            .collect();
        curve
            .batch_add(&mut points, &steps, &mut BatchScratch::default())
            .unwrap();
        assert_eq!(points, expected);
        assert!(curve
            .batch_add(&mut points, &steps[..63], &mut BatchScratch::default())
            .is_err());
    }
    #[test]
    fn primality_handles_small_values_and_pseudoprimes() {
        for n in [0, 1, 4, 108, 341, 561, 3215031751, 3825123056546413051] {
            assert!(!is_prime(n), "{n}");
        }
        for n in [2, 3, 109, 2147505293, 2305843009213693951] {
            assert!(is_prime(n), "{n}");
        }
    }
}
