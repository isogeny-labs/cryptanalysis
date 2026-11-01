//! Appendix D.4.1: an unramified extension of Z/(2^p), with exact arithmetic.

use crate::{integrity, invalid, overflow, BigInt, BigUint, Meter, Result};
use num_traits::{One, Zero};

fn gf_remainder(mut value: BigUint, modulus: &BigUint) -> BigUint {
    while !value.is_zero() && value.bits() >= modulus.bits() {
        let shift = (value.bits() - modulus.bits()) as usize;
        value ^= modulus << shift;
    }
    value
}

fn gf_gcd(mut a: BigUint, mut b: BigUint) -> BigUint {
    while !b.is_zero() {
        let next = gf_remainder(a, &b);
        a = b;
        b = next;
    }
    a
}

fn gf_product(a: &BigUint, b: &BigUint, modulus: &BigUint) -> BigUint {
    let mut answer = BigUint::zero();
    for i in 0..b.bits() {
        if b.bit(i) {
            answer ^= a << (i as usize);
        }
    }
    gf_remainder(answer, modulus)
}

fn irreducible(f: &BigUint, degree: usize, meter: &mut Meter) -> Result<bool> {
    let x = gf_remainder(BigUint::from(2u8), f);
    let mut value = x.clone();
    for i in 1..=degree {
        meter.charge(1, "GF(2) irreducibility")?;
        value = gf_product(&value, &value, f);
        if i <= degree / 2 && gf_gcd(&value ^ &x, f.clone()) != BigUint::one() {
            return Ok(false);
        }
    }
    Ok(value == x)
}

fn gf_inverse(a: &BigUint, f: &BigUint) -> Result<BigUint> {
    if a.is_zero() {
        return Err(invalid("zero residue-field unit"));
    }
    let mut u = a.clone();
    let mut v = f.clone();
    let mut left = BigUint::one();
    let mut right = BigUint::zero();
    while !u.is_one() {
        if u.is_zero() {
            return Err(integrity("reducible extension polynomial"));
        }
        if u.bits() < v.bits() {
            std::mem::swap(&mut u, &mut v);
            std::mem::swap(&mut left, &mut right);
        }
        let shift = (u.bits() - v.bits()) as usize;
        u ^= &v << shift;
        left ^= &right << shift;
    }
    Ok(gf_remainder(left, f))
}

/// Coordinates in the power basis, always canonical at their context's precision.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Element(pub(crate) Vec<BigUint>);
impl Element {
    /// Coordinates as integer representatives. Lifting retains these exact values.
    pub fn coordinates(&self) -> &[BigUint] {
        &self.0
    }
    /// Test zero in this representation.
    pub fn is_zero(&self) -> bool {
        self.0.iter().all(Zero::is_zero)
    }
}

/// `(Z/2^precision)[U]/f`, where f has irreducible reduction modulo two.
#[derive(Clone, Debug)]
pub struct Ring {
    degree: usize,
    polynomial: BigUint,
    precision: usize,
    modulus: BigUint,
    mask: BigUint,
}

impl Ring {
    /// Deterministically select the binary-coefficient irreducible polynomial.
    pub fn new(degree: usize, precision: usize, meter: &mut Meter) -> Result<Self> {
        if degree == 0 || precision == 0 {
            return Err(invalid("extension degree or precision is zero"));
        }
        meter.bits(degree, "residue field degree")?;
        meter.bits(precision, "coefficient precision")?;
        meter.vector(degree, "extension coordinates")?;
        let leading = BigUint::one() << degree;
        let mut lower = BigUint::one();
        loop {
            meter.charge(1, "irreducible polynomial search")?;
            let polynomial = &leading + &lower;
            if irreducible(&polynomial, degree, meter)? {
                let modulus = BigUint::one() << precision;
                let mask = &modulus - BigUint::one();
                return Ok(Self {
                    degree,
                    polynomial,
                    precision,
                    modulus,
                    mask,
                });
            }
            lower += BigUint::from(2u8);
            if lower >= leading {
                return Err(integrity("irreducible polynomial search exhausted"));
            }
        }
    }

    /// Change only precision; the same extension polynomial is retained.
    pub fn at_precision(&self, precision: usize, meter: &Meter) -> Result<Self> {
        if precision == 0 {
            return Err(invalid("zero precision"));
        }
        meter.bits(precision, "lifted coefficient precision")?;
        let modulus = BigUint::one() << precision;
        Ok(Self {
            degree: self.degree,
            polynomial: self.polynomial.clone(),
            precision,
            mask: &modulus - BigUint::one(),
            modulus,
        })
    }

    /// Number of power-basis coordinates.
    pub fn degree(&self) -> usize {
        self.degree
    }
    /// Precision exponent of 2.
    pub fn precision(&self) -> usize {
        self.precision
    }
    /// Canonical coefficient modulus 2^p.
    pub fn modulus(&self) -> &BigUint {
        &self.modulus
    }
    /// The binary-coefficient monic polynomial, as a bit pattern.
    pub fn polynomial(&self) -> &BigUint {
        &self.polynomial
    }
    /// Additive identity.
    pub fn zero(&self) -> Element {
        Element(vec![BigUint::zero(); self.degree])
    }
    /// Multiplicative identity.
    pub fn one(&self) -> Element {
        self.integer(&BigUint::one())
    }
    /// Embed an unsigned integer.
    pub fn integer(&self, x: &BigUint) -> Element {
        let mut answer = self.zero();
        answer.0[0] = x & &self.mask;
        answer
    }
    /// Embed a signed integer.
    pub fn signed(&self, x: &BigInt) -> Element {
        self.integer(&crate::arithmetic::residue(x, &self.modulus))
    }
    /// Canonical coefficient lift/reduction. This is deliberately not claimed
    /// to preserve multiplication when precision increases.
    pub fn lift(&self, x: &Element) -> Result<Element> {
        if x.0.len() != self.degree {
            return Err(invalid("extension degree mismatch"));
        }
        Ok(Element(x.0.iter().map(|a| a & &self.mask).collect()))
    }
    /// Binary-coordinate lift of a residue-field element, for interpolation.
    pub fn point(&self, index: &BigUint) -> Result<Element> {
        if index.bits() > self.degree as u64 {
            return Err(invalid("interpolation point outside residue field"));
        }
        Ok(Element(
            (0..self.degree)
                .map(|i| BigUint::from(u8::from(index.bit(i as u64))))
                .collect(),
        ))
    }

    fn check(&self, a: &Element) -> Result<()> {
        if a.0.len() != self.degree || a.0.iter().any(|x| x >= &self.modulus) {
            return Err(invalid("noncanonical extension element"));
        }
        Ok(())
    }
    /// Ring addition at this fixed precision.
    pub fn add(&self, a: &Element, b: &Element, meter: &mut Meter) -> Result<Element> {
        self.check(a)?;
        self.check(b)?;
        meter.charge(self.degree as u64, "extension addition")?;
        Ok(Element(
            a.0.iter()
                .zip(&b.0)
                .map(|(x, y)| (x + y) & &self.mask)
                .collect(),
        ))
    }
    /// Ring subtraction at this fixed precision.
    pub fn sub(&self, a: &Element, b: &Element, meter: &mut Meter) -> Result<Element> {
        self.check(a)?;
        self.check(b)?;
        meter.charge(self.degree as u64, "extension subtraction")?;
        Ok(Element(
            a.0.iter()
                .zip(&b.0)
                .map(|(x, y)| (x + &self.modulus - y) & &self.mask)
                .collect(),
        ))
    }
    /// Ring multiplication, including reduction by the integral polynomial f.
    pub fn mul(&self, a: &Element, b: &Element, meter: &mut Meter) -> Result<Element> {
        self.check(a)?;
        self.check(b)?;
        let len = self
            .degree
            .checked_mul(2)
            .and_then(|n| n.checked_sub(1))
            .ok_or_else(|| overflow("extension product"))?;
        meter.vector(len, "extension product")?;
        let mut out = vec![BigUint::zero(); len];
        for i in 0..self.degree {
            if a.0[i].is_zero() {
                continue;
            }
            for j in 0..self.degree {
                if b.0[j].is_zero() {
                    continue;
                }
                meter.charge(1, "extension coefficient product")?;
                out[i + j] = (&out[i + j] + &a.0[i] * &b.0[j]) & &self.mask;
            }
        }
        for i in (self.degree..len).rev() {
            let coefficient = out[i].clone();
            if coefficient.is_zero() {
                continue;
            }
            for j in 0..self.degree {
                if self.polynomial.bit(j as u64) {
                    meter.charge(1, "extension reduction")?;
                    out[i - self.degree + j] =
                        (&out[i - self.degree + j] + &self.modulus - &coefficient) & &self.mask;
                }
            }
        }
        out.truncate(self.degree);
        Ok(Element(out))
    }
    /// Exponentiation at fixed precision.
    pub fn pow(&self, a: &Element, exponent: usize, meter: &mut Meter) -> Result<Element> {
        let mut n = exponent;
        let mut base = a.clone();
        let mut out = self.one();
        while n != 0 {
            if n & 1 != 0 {
                out = self.mul(&out, &base, meter)?;
            }
            n >>= 1;
            if n != 0 {
                base = self.mul(&base, &base, meter)?;
            }
        }
        Ok(out)
    }
    /// Invert an element whose residue modulo two is nonzero, by Newton lifting.
    pub fn inverse(&self, a: &Element, meter: &mut Meter) -> Result<Element> {
        self.check(a)?;
        let mut residue = BigUint::zero();
        for i in 0..self.degree {
            if a.0[i].bit(0) {
                residue.set_bit(i as u64, true);
            }
        }
        let inv = gf_inverse(&residue, &self.polynomial)?;
        let mut out = self.point(&inv)?;
        let mut precision = 1usize;
        while precision < self.precision {
            let product = self.mul(a, &out, meter)?;
            let correction = self.sub(&self.integer(&BigUint::from(2u8)), &product, meter)?;
            out = self.mul(&out, &correction, meter)?;
            precision = precision.saturating_mul(2);
        }
        if self.mul(a, &out, meter)? != self.one() {
            return Err(integrity("extension unit inversion"));
        }
        Ok(out)
    }
    /// Multiply by a power of two, without losing precision through division.
    pub fn shift(&self, a: &Element, bits: usize) -> Result<Element> {
        self.check(a)?;
        if bits >= self.precision {
            return Ok(self.zero());
        }
        Ok(Element(
            a.0.iter().map(|c| (c << bits) & &self.mask).collect(),
        ))
    }
}

/// Truncated polynomial product over a fixed coefficient ring.
pub fn polynomial_mul(
    a: &[Element],
    b: &[Element],
    limit: usize,
    ring: &Ring,
    meter: &mut Meter,
) -> Result<Vec<Element>> {
    meter.vector(limit, "polynomial coefficients")?;
    let mut out = vec![ring.zero(); limit];
    for i in 0..a.len().min(limit) {
        if a[i].is_zero() {
            continue;
        }
        for j in 0..b.len().min(limit - i) {
            if b[j].is_zero() {
                continue;
            }
            let value = ring.mul(&a[i], &b[j], meter)?;
            out[i + j] = ring.add(&out[i + j], &value, meter)?;
        }
    }
    Ok(out)
}

/// Polynomial evaluation by Horner's rule.
pub fn polynomial_value(
    coefficients: &[Element],
    x: &Element,
    ring: &Ring,
    meter: &mut Meter,
) -> Result<Element> {
    let mut out = ring.zero();
    for c in coefficients.iter().rev() {
        out = ring.mul(&out, x, meter)?;
        out = ring.add(&out, c, meter)?;
    }
    Ok(out)
}

/// Lagrange interpolation at distinct binary-coordinate lifts. Unit differences
/// are explicitly checked by inversion, rather than assumed for arbitrary points.
pub fn interpolate(
    points: &[Element],
    values: &[Element],
    ring: &Ring,
    meter: &mut Meter,
) -> Result<Vec<Element>> {
    if points.len() != values.len() || points.is_empty() {
        return Err(invalid("interpolation shape"));
    }
    let n = points.len();
    meter.vector(n, "interpolation coefficients")?;
    let mut result = vec![ring.zero(); n];
    for i in 0..n {
        let mut numerator = vec![ring.one()];
        let mut denominator = ring.one();
        for j in 0..n {
            if i == j {
                continue;
            }
            let negative = ring.sub(&ring.zero(), &points[j], meter)?;
            numerator = polynomial_mul(
                &numerator,
                &[negative, ring.one()],
                numerator.len() + 1,
                ring,
                meter,
            )?;
            let difference = ring.sub(&points[i], &points[j], meter)?;
            denominator = ring.mul(&denominator, &difference, meter)?;
        }
        let inverse = ring.inverse(&denominator, meter)?;
        let scale = ring.mul(&values[i], &inverse, meter)?;
        for j in 0..n {
            let value = ring.mul(&scale, &numerator[j], meter)?;
            result[j] = ring.add(&result[j], &value, meter)?;
        }
    }
    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::Limits;
    #[test]
    fn units_and_interpolation_over_nonfields() {
        let mut meter = Meter::new(Limits::default());
        for degree in [1, 4, 8] {
            let ring = Ring::new(degree, 17, &mut meter).unwrap();
            for value in 1..(1usize << degree).min(25) {
                let a = ring.point(&BigUint::from(value)).unwrap();
                let inverse = ring.inverse(&a, &mut meter).unwrap();
                assert_eq!(ring.mul(&a, &inverse, &mut meter).unwrap(), ring.one());
            }
            assert!(ring
                .inverse(&ring.integer(&BigUint::from(2u8)), &mut meter)
                .is_err());
        }
        let ring = Ring::new(4, 24, &mut meter).unwrap();
        let coefficients: Vec<_> = (0..7u8)
            .map(|i| ring.signed(&BigInt::from(i as i64 - 3)))
            .collect();
        let points: Vec<_> = (0..7u8).map(|i| ring.point(&i.into()).unwrap()).collect();
        let values: Vec<_> = points
            .iter()
            .map(|x| polynomial_value(&coefficients, x, &ring, &mut meter).unwrap())
            .collect();
        assert_eq!(
            interpolate(&points, &values, &ring, &mut meter).unwrap(),
            coefficients
        );
    }
    #[test]
    fn creation_precision_lifts_are_not_silently_ring_homomorphisms() {
        let mut meter = Meter::new(Limits::default());
        let low = Ring::new(1, 2, &mut meter).unwrap();
        let high = low.at_precision(8, &meter).unwrap();
        let a = low.integer(&BigUint::from(3u8));
        let low_product = low.mul(&a, &a, &mut meter).unwrap();
        assert_ne!(
            high.lift(&low_product).unwrap(),
            high.mul(&high.lift(&a).unwrap(), &high.lift(&a).unwrap(), &mut meter)
                .unwrap()
        );
    }
}
