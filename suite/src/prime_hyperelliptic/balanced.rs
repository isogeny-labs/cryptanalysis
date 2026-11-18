//! Balanced divisor arithmetic for split, even-degree genus-two curves.
//!
//! This module is deliberately separate from the odd-degree one-infinity
//! implementation in [`super::curve`].  Its supported curve model is
//!
//! ```text
//! C : y^2 = f(x),   deg(f) = 6,   f monic and squarefree,
//! ```
//!
//! over a checked odd prime field.  The two rational points at infinity are
//! labelled by `y / x^3 = +1` and `y / x^3 = -1`.  For genus two the balanced
//! representative `(u, v, n_plus)` denotes
//!
//! ```text
//! div(u, y-v)_affine
//!   + n_plus * infinity_plus
//!   + (2 - deg(u) - n_plus) * infinity_minus
//!   - (infinity_plus + infinity_minus).
//! ```
//!
//! Canonical representatives satisfy `deg(u) <= 2` and
//! `0 <= n_plus <= 2 - deg(u)`.  This is the even-genus specialization of
//! Galbraith, corrected Chapter 10, Definition 10.4.9 and Theorem 10.4.19.
//! Composition and reduction retain the infinity counter as required by
//! Lemmas 10.4.10 and 10.4.14.
//!
//! No cover map, subgroup claim, extension-field model, or solver is supplied
//! here.  Exhaustive enumeration is a separate toy-field reference routine.

use super::fp2::is_prime_u64;
use super::fp_poly::FpPoly;
use num_bigint::BigUint;
use num_traits::{One, ToPrimitive, Zero};
use std::fmt;

/// Exhaustive balanced-class enumeration is intentionally restricted to
/// small fields.  Arithmetic itself is not restricted to this bound.
pub const MAX_BALANCED_ENUMERATION_PRIME: u64 = 31;

/// Checked-construction or checked-arithmetic failure for the split
/// two-infinity genus-two model.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum BalancedHyperellipticError {
    ModulusNotOddPrime,
    UnsupportedPrimeModulusSize { maximum_bits: u32 },
    CurvePolynomialFieldMismatch,
    CurvePolynomialNotCanonical,
    CurveDegreeMismatch { actual: Option<usize> },
    CurvePolynomialNotMonic,
    CurvePolynomialNotSquarefree,
    InfinityPolynomialMismatch,
    CoordinateOutOfRange { coordinate: &'static str },
    PointNotOnCurve,
    DivisorCurveMismatch,
    DivisorPolynomialFieldMismatch { component: &'static str },
    NonCanonicalPolynomial { component: &'static str },
    DivisorUIsZero,
    DivisorUNotMonic,
    DivisorDegreeTooLarge { degree: usize },
    DivisorVNotReduced { v_degree: usize, u_degree: usize },
    InfinityCountOutOfRange { degree: usize, n_plus: u32 },
    DivisorEquationMismatch,
    NonExactDivision { stage: &'static str },
    ReductionProducedZero,
    ReductionOutsideCanonicalRange { support_degree: usize, n_plus: i64 },
    EnumerationFieldTooLarge { maximum: u64 },
}

impl fmt::Display for BalancedHyperellipticError {
    fn fmt(&self, out: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::ModulusNotOddPrime => write!(out, "modulus is not an odd prime"),
            Self::UnsupportedPrimeModulusSize { maximum_bits } => write!(
                out,
                "prime modulus exceeds the deterministic {maximum_bits}-bit validation domain"
            ),
            Self::CurvePolynomialFieldMismatch => {
                write!(out, "curve polynomial uses a different coefficient field")
            }
            Self::CurvePolynomialNotCanonical => {
                write!(out, "curve polynomial is not canonically encoded")
            }
            Self::CurveDegreeMismatch { actual } => write!(
                out,
                "split genus-two curve polynomial must have degree 6, got {actual:?}"
            ),
            Self::CurvePolynomialNotMonic => write!(out, "curve polynomial is not monic"),
            Self::CurvePolynomialNotSquarefree => {
                write!(out, "curve polynomial is not squarefree")
            }
            Self::InfinityPolynomialMismatch => write!(
                out,
                "stored polynomial part at infinity does not match the sextic"
            ),
            Self::CoordinateOutOfRange { coordinate } => {
                write!(out, "point coordinate {coordinate} is not canonical")
            }
            Self::PointNotOnCurve => write!(out, "point is not on the curve"),
            Self::DivisorCurveMismatch => write!(out, "divisor belongs to a different curve"),
            Self::DivisorPolynomialFieldMismatch { component } => write!(
                out,
                "divisor polynomial {component} uses a different coefficient field"
            ),
            Self::NonCanonicalPolynomial { component } => {
                write!(out, "divisor polynomial {component} is not canonical")
            }
            Self::DivisorUIsZero => write!(out, "balanced divisor u polynomial is zero"),
            Self::DivisorUNotMonic => write!(out, "balanced divisor u polynomial is not monic"),
            Self::DivisorDegreeTooLarge { degree } => {
                write!(out, "balanced divisor u degree {degree} exceeds genus two")
            }
            Self::DivisorVNotReduced { v_degree, u_degree } => write!(
                out,
                "balanced divisor v degree {v_degree} is not below u degree {u_degree}"
            ),
            Self::InfinityCountOutOfRange { degree, n_plus } => write!(
                out,
                "balanced infinity count {n_plus} exceeds 2 - support degree {degree}"
            ),
            Self::DivisorEquationMismatch => {
                write!(out, "balanced divisor u does not divide v^2-f")
            }
            Self::NonExactDivision { stage } => {
                write!(out, "non-exact polynomial division during {stage}")
            }
            Self::ReductionProducedZero => {
                write!(out, "balanced reduction produced zero support")
            }
            Self::ReductionOutsideCanonicalRange {
                support_degree,
                n_plus,
            } => write!(
                out,
                "balanced reduction ended at degree {support_degree}, infinity count {n_plus}"
            ),
            Self::EnumerationFieldTooLarge { maximum } => write!(
                out,
                "balanced-class enumeration requires a word-sized prime at most {maximum}"
            ),
        }
    }
}

impl std::error::Error for BalancedHyperellipticError {}

/// `C : y^2 = f(x)` with a monic squarefree sextic over an odd prime field.
///
/// The leading coefficient `1` makes both infinity branches rational and
/// labels them canonically by the sign of `y/x^3`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct SplitHyperellipticCurveP {
    pub p: BigUint,
    pub f: FpPoly,
    infinity_polynomial: FpPoly,
}

impl SplitHyperellipticCurveP {
    /// Checked construction of the supported monic split-sextic model.
    pub fn try_new(p: BigUint, f: FpPoly) -> Result<Self, BalancedHyperellipticError> {
        validate_modulus(&p)?;
        let infinity_polynomial = polynomial_part_at_infinity(&p, &f)?;
        let curve = Self {
            p,
            f,
            infinity_polynomial,
        };
        curve.validate()?;
        Ok(curve)
    }

    /// Recheck the public field, equation, smoothness, and infinity data.
    pub fn validate(&self) -> Result<(), BalancedHyperellipticError> {
        validate_modulus(&self.p)?;
        if self.f.p != self.p {
            return Err(BalancedHyperellipticError::CurvePolynomialFieldMismatch);
        }
        if !canonical_polynomial(&self.f, &self.p) {
            return Err(BalancedHyperellipticError::CurvePolynomialNotCanonical);
        }
        if self.f.degree() != Some(6) {
            return Err(BalancedHyperellipticError::CurveDegreeMismatch {
                actual: self.f.degree(),
            });
        }
        if self.f.lead() != BigUint::one() {
            return Err(BalancedHyperellipticError::CurvePolynomialNotMonic);
        }
        let derivative = FpPoly::from_coeffs(
            (1..=6)
                .map(|i| (self.f.coeff(i) * BigUint::from(i)) % &self.p)
                .collect(),
            self.p.clone(),
        );
        if self.f.gcd(&derivative).degree() != Some(0) {
            return Err(BalancedHyperellipticError::CurvePolynomialNotSquarefree);
        }
        if self.infinity_polynomial != polynomial_part_at_infinity(&self.p, &self.f)? {
            return Err(BalancedHyperellipticError::InfinityPolynomialMismatch);
        }
        Ok(())
    }

    /// The unique monic cubic `G_+` for which `deg(f-G_+^2) <= 2`.
    /// `G_-=-G_+` labels the other infinity branch.
    pub fn infinity_polynomial(&self) -> &FpPoly {
        &self.infinity_polynomial
    }

    /// Checked affine membership test.
    pub fn checked_is_on_curve(
        &self,
        x: &BigUint,
        y: &BigUint,
    ) -> Result<bool, BalancedHyperellipticError> {
        self.validate()?;
        if x >= &self.p {
            return Err(BalancedHyperellipticError::CoordinateOutOfRange { coordinate: "x" });
        }
        if y >= &self.p {
            return Err(BalancedHyperellipticError::CoordinateOutOfRange { coordinate: "y" });
        }
        Ok((y * y) % &self.p == self.f.eval(x))
    }

    /// Enumerate every canonical balanced class.  This is a deterministic
    /// small-field reference routine, not a scalable group-order algorithm.
    pub fn enumerate_reduced_divisors(
        &self,
    ) -> Result<Vec<BalancedDivisorP>, BalancedHyperellipticError> {
        self.validate()?;
        let Some(p) = self.p.to_u64() else {
            return Err(BalancedHyperellipticError::EnumerationFieldTooLarge {
                maximum: MAX_BALANCED_ENUMERATION_PRIME,
            });
        };
        if p > MAX_BALANCED_ENUMERATION_PRIME {
            return Err(BalancedHyperellipticError::EnumerationFieldTooLarge {
                maximum: MAX_BALANCED_ENUMERATION_PRIME,
            });
        }

        let mut classes = Vec::new();
        let one = FpPoly::one(self.p.clone());
        let zero = FpPoly::zero(self.p.clone());
        for n_plus in 0..=2 {
            classes.push(BalancedDivisorP::try_from_polynomials(
                self,
                one.clone(),
                zero.clone(),
                n_plus,
            )?);
        }

        for u0 in 0..p {
            let u = self.poly_u64(&[u0, 1]);
            for v0 in 0..p {
                let v = self.poly_u64(&[v0]);
                if !self.f.sub(&v.mul(&v)).rem(&u).is_zero() {
                    continue;
                }
                for n_plus in 0..=1 {
                    classes.push(BalancedDivisorP::try_from_polynomials(
                        self,
                        u.clone(),
                        v.clone(),
                        n_plus,
                    )?);
                }
            }
        }

        for u0 in 0..p {
            for u1 in 0..p {
                let u = self.poly_u64(&[u0, u1, 1]);
                for v0 in 0..p {
                    for v1 in 0..p {
                        let v = self.poly_u64(&[v0, v1]);
                        if self.f.sub(&v.mul(&v)).rem(&u).is_zero() {
                            classes.push(BalancedDivisorP::try_from_polynomials(
                                self,
                                u.clone(),
                                v,
                                0,
                            )?);
                        }
                    }
                }
            }
        }
        Ok(classes)
    }

    fn poly_u64(&self, coefficients: &[u64]) -> FpPoly {
        FpPoly::from_coeffs(
            coefficients.iter().copied().map(BigUint::from).collect(),
            self.p.clone(),
        )
    }

    fn exact_divide(
        &self,
        numerator: &FpPoly,
        denominator: &FpPoly,
        stage: &'static str,
    ) -> Result<FpPoly, BalancedHyperellipticError> {
        let (quotient, remainder) = numerator.divrem(denominator);
        if !remainder.is_zero() {
            return Err(BalancedHyperellipticError::NonExactDivision { stage });
        }
        Ok(quotient)
    }

    /// Semireduced affine Cantor composition.  Infinity accounting is
    /// applied by [`BalancedDivisorP::checked_add`].
    fn compose_affine(
        &self,
        left: &BalancedDivisorP,
        right: &BalancedDivisorP,
    ) -> Result<(FpPoly, FpPoly, usize), BalancedHyperellipticError> {
        let (d1, e1, e2) = left.u.ext_gcd(&right.u);
        let (d, c1, c2) = d1.ext_gcd(&left.v.add(&right.v));
        let u = self.exact_divide(
            &left.u.mul(&right.u),
            &d.mul(&d),
            "balanced Cantor composition u1*u2/d^2",
        )?;
        let numerator = c1
            .mul(&e1)
            .mul(&left.u)
            .mul(&right.v)
            .add(&c1.mul(&e2).mul(&right.u).mul(&left.v))
            .add(&c2.mul(&left.v.mul(&right.v).add(&self.f)));
        let v = self
            .exact_divide(&numerator, &d, "balanced Cantor composition v numerator/d")?
            .rem(&u);
        Ok((u, v, d.degree().unwrap_or(0)))
    }

    fn reduce_semireduced(
        &self,
        u: FpPoly,
        v: FpPoly,
        n_plus: i64,
    ) -> Result<BalancedDivisorP, BalancedHyperellipticError> {
        let degree = u
            .degree()
            .ok_or(BalancedHyperellipticError::ReductionProducedZero)?;
        if degree <= 2 && n_plus >= 0 && n_plus <= 2 - degree as i64 {
            return BalancedDivisorP::try_from_polynomials(self, u, v, n_plus as u32);
        }
        if degree > 4 {
            return Err(BalancedHyperellipticError::ReductionOutsideCanonicalRange {
                support_degree: degree,
                n_plus,
            });
        }

        // A degree-four composition already supplies the cubic interpolant.
        // Otherwise choose G_+ or G_- according to which infinity counter
        // needs moving into the canonical range, then retain v modulo u.
        let line = if degree == 4 {
            v
        } else {
            let branch = if n_plus >= 0 {
                self.infinity_polynomial.clone()
            } else {
                self.infinity_polynomial.neg()
            };
            branch.add(&v.sub(&branch).rem(&u))
        };
        let numerator = self.f.sub(&line.mul(&line));
        let total_degree = numerator
            .degree()
            .ok_or(BalancedHyperellipticError::ReductionProducedZero)?;
        let raw = self.exact_divide(
            &numerator,
            &u,
            "balanced composition and reduction at infinity",
        )?;
        if raw.is_zero() {
            return Err(BalancedHyperellipticError::ReductionProducedZero);
        }
        let next_u = raw.monic();
        let next_degree = next_u
            .degree()
            .ok_or(BalancedHyperellipticError::ReductionProducedZero)?;

        // For a line with leading +1, v_inf+(y-line)=3-deg(f-line^2).
        // Every other leading coefficient has pole order three at infinity+.
        let valuation_at_plus = if line.coeff(3) == BigUint::one() {
            3 - total_degree as i64
        } else {
            -3
        };
        let next_n_plus = n_plus - valuation_at_plus - next_degree as i64;
        if next_degree > 2 || next_n_plus < 0 || next_n_plus > 2 - next_degree as i64 {
            return Err(BalancedHyperellipticError::ReductionOutsideCanonicalRange {
                support_degree: next_degree,
                n_plus: next_n_plus,
            });
        }
        let next_v = line.neg().rem(&next_u);
        BalancedDivisorP::try_from_polynomials(self, next_u, next_v, next_n_plus as u32)
    }
}

/// Canonical balanced genus-two divisor `(u, v, n_plus)`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct BalancedDivisorP {
    curve_f: FpPoly,
    pub u: FpPoly,
    pub v: FpPoly,
    pub n_plus: u32,
}

impl BalancedDivisorP {
    /// Checked construction from a purported canonical balanced triple.
    pub fn try_from_polynomials(
        curve: &SplitHyperellipticCurveP,
        u: FpPoly,
        v: FpPoly,
        n_plus: u32,
    ) -> Result<Self, BalancedHyperellipticError> {
        let divisor = Self {
            curve_f: curve.f.clone(),
            u,
            v,
            n_plus,
        };
        divisor.validate(curve)?;
        Ok(divisor)
    }

    /// The identity is `(1, 0, 1)`, representing the balanced base divisor
    /// `infinity_plus + infinity_minus` minus itself.
    pub fn try_identity(
        curve: &SplitHyperellipticCurveP,
    ) -> Result<Self, BalancedHyperellipticError> {
        Self::try_from_polynomials(
            curve,
            FpPoly::one(curve.p.clone()),
            FpPoly::zero(curve.p.clone()),
            1,
        )
    }

    /// The infinity-difference class `infinity_plus - infinity_minus`.
    pub fn try_infinity_difference(
        curve: &SplitHyperellipticCurveP,
    ) -> Result<Self, BalancedHyperellipticError> {
        Self::try_from_polynomials(
            curve,
            FpPoly::one(curve.p.clone()),
            FpPoly::zero(curve.p.clone()),
            2,
        )
    }

    /// Build a degree-one finite support class.  `n_plus` is zero or one and
    /// selects the second point of the balanced degree-two effective divisor.
    pub fn try_from_point(
        curve: &SplitHyperellipticCurveP,
        x: &BigUint,
        y: &BigUint,
        n_plus: u32,
    ) -> Result<Self, BalancedHyperellipticError> {
        if !curve.checked_is_on_curve(x, y)? {
            return Err(BalancedHyperellipticError::PointNotOnCurve);
        }
        let constant = if x.is_zero() {
            BigUint::zero()
        } else {
            (&curve.p - x) % &curve.p
        };
        Self::try_from_polynomials(
            curve,
            FpPoly::from_coeffs(vec![constant, BigUint::one()], curve.p.clone()),
            FpPoly::constant(y.clone(), curve.p.clone()),
            n_plus,
        )
    }

    /// Revalidate the curve binding, canonical representative, and equation.
    pub fn validate(
        &self,
        curve: &SplitHyperellipticCurveP,
    ) -> Result<(), BalancedHyperellipticError> {
        curve.validate()?;
        if self.curve_f != curve.f {
            return Err(BalancedHyperellipticError::DivisorCurveMismatch);
        }
        for (component, polynomial) in [("u", &self.u), ("v", &self.v)] {
            if polynomial.p != curve.p {
                return Err(BalancedHyperellipticError::DivisorPolynomialFieldMismatch {
                    component,
                });
            }
            if !canonical_polynomial(polynomial, &curve.p) {
                return Err(BalancedHyperellipticError::NonCanonicalPolynomial { component });
            }
        }
        let degree = self
            .u
            .degree()
            .ok_or(BalancedHyperellipticError::DivisorUIsZero)?;
        if self.u.lead() != BigUint::one() {
            return Err(BalancedHyperellipticError::DivisorUNotMonic);
        }
        if degree > 2 {
            return Err(BalancedHyperellipticError::DivisorDegreeTooLarge { degree });
        }
        if let Some(v_degree) = self.v.degree() {
            if degree == 0 || v_degree >= degree {
                return Err(BalancedHyperellipticError::DivisorVNotReduced {
                    v_degree,
                    u_degree: degree,
                });
            }
        }
        if usize::try_from(self.n_plus).unwrap_or(usize::MAX) + degree > 2 {
            return Err(BalancedHyperellipticError::InfinityCountOutOfRange {
                degree,
                n_plus: self.n_plus,
            });
        }
        if !curve.f.sub(&self.v.mul(&self.v)).rem(&self.u).is_zero() {
            return Err(BalancedHyperellipticError::DivisorEquationMismatch);
        }
        Ok(())
    }

    pub fn is_identity(&self) -> bool {
        self.u == FpPoly::one(self.u.p.clone()) && self.v.is_zero() && self.n_plus == 1
    }

    pub fn checked_eq(
        &self,
        other: &Self,
        curve: &SplitHyperellipticCurveP,
    ) -> Result<bool, BalancedHyperellipticError> {
        self.validate(curve)?;
        other.validate(curve)?;
        Ok(self == other)
    }

    pub fn checked_neg(
        &self,
        curve: &SplitHyperellipticCurveP,
    ) -> Result<Self, BalancedHyperellipticError> {
        self.validate(curve)?;
        let degree = self.u.degree().expect("validated nonzero u");
        Self::try_from_polynomials(
            curve,
            self.u.clone(),
            self.v.neg().rem(&self.u),
            (2 - degree) as u32 - self.n_plus,
        )
    }

    pub fn checked_add(
        &self,
        other: &Self,
        curve: &SplitHyperellipticCurveP,
    ) -> Result<Self, BalancedHyperellipticError> {
        self.validate(curve)?;
        other.validate(curve)?;
        let (u, v, removed_degree) = curve.compose_affine(self, other)?;
        let n_plus = i64::from(self.n_plus) + i64::from(other.n_plus) + removed_degree as i64 - 1;
        curve.reduce_semireduced(u, v, n_plus)
    }

    pub fn checked_scalar_mul(
        &self,
        scalar: &BigUint,
        curve: &SplitHyperellipticCurveP,
    ) -> Result<Self, BalancedHyperellipticError> {
        self.validate(curve)?;
        let mut accumulator = Self::try_identity(curve)?;
        let mut addend = self.clone();
        for bit in 0..scalar.bits() {
            if scalar.bit(bit) {
                accumulator = accumulator.checked_add(&addend, curve)?;
            }
            if bit + 1 < scalar.bits() {
                addend = addend.checked_add(&addend, curve)?;
            }
        }
        Ok(accumulator)
    }
}

fn canonical_polynomial(polynomial: &FpPoly, p: &BigUint) -> bool {
    polynomial.p == *p
        && polynomial.coeffs.iter().all(|coefficient| coefficient < p)
        && polynomial
            .coeffs
            .last()
            .is_none_or(|coefficient| !coefficient.is_zero())
}

fn validate_modulus(p: &BigUint) -> Result<u64, BalancedHyperellipticError> {
    if p.bits() > 64 {
        return Err(BalancedHyperellipticError::UnsupportedPrimeModulusSize { maximum_bits: 64 });
    }
    let Some(word) = p.to_u64() else {
        return Err(BalancedHyperellipticError::UnsupportedPrimeModulusSize { maximum_bits: 64 });
    };
    if word == 2 || !is_prime_u64(word) {
        return Err(BalancedHyperellipticError::ModulusNotOddPrime);
    }
    Ok(word)
}

fn polynomial_part_at_infinity(
    p: &BigUint,
    f: &FpPoly,
) -> Result<FpPoly, BalancedHyperellipticError> {
    if f.p != *p {
        return Err(BalancedHyperellipticError::CurvePolynomialFieldMismatch);
    }
    if !canonical_polynomial(f, p) {
        return Err(BalancedHyperellipticError::CurvePolynomialNotCanonical);
    }
    if f.degree() != Some(6) {
        return Err(BalancedHyperellipticError::CurveDegreeMismatch { actual: f.degree() });
    }
    if f.lead() != BigUint::one() {
        return Err(BalancedHyperellipticError::CurvePolynomialNotMonic);
    }
    let two = BigUint::from(2u32);
    let inverse_two = two.modpow(&(p - 2u32), p);
    let c2 = (&f.coeff(5) * &inverse_two) % p;
    let c1 = ((&f.coeff(4) + p - (&c2 * &c2) % p) * &inverse_two) % p;
    let twice_c2_c1 = (&two * &c2 * &c1) % p;
    let c0 = ((&f.coeff(3) + p - twice_c2_c1) * &inverse_two) % p;
    let polynomial = FpPoly::from_coeffs(vec![c0, c1, c2, BigUint::one()], p.clone());
    if f.sub(&polynomial.mul(&polynomial))
        .degree()
        .is_some_and(|degree| degree > 2)
    {
        return Err(BalancedHyperellipticError::InfinityPolynomialMismatch);
    }
    Ok(polynomial)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::prime_hyperelliptic::{brute_force_jac_order, HyperellipticCurveP, MumfordDivisorP};
    use std::collections::BTreeSet;

    fn f5_split_curve() -> SplitHyperellipticCurveP {
        let p = BigUint::from(5u32);
        SplitHyperellipticCurveP::try_new(
            p.clone(),
            FpPoly::from_coeffs(
                vec![
                    BigUint::one(),
                    BigUint::zero(),
                    BigUint::zero(),
                    BigUint::zero(),
                    BigUint::zero(),
                    BigUint::zero(),
                    BigUint::one(),
                ],
                p,
            ),
        )
        .unwrap()
    }

    fn odd_chart() -> HyperellipticCurveP {
        let p = BigUint::from(5u32);
        HyperellipticCurveP::try_new(
            p.clone(),
            FpPoly::from_coeffs(
                vec![
                    BigUint::one(),
                    BigUint::one(),
                    BigUint::zero(),
                    BigUint::zero(),
                    BigUint::zero(),
                    BigUint::one(),
                ],
                p,
            ),
            2,
        )
        .unwrap()
    }

    /// A second F5 fixture with a genuinely nontrivial polynomial part at
    /// infinity.  The simple branch `(x,y)=(0,0)` permits the independent
    /// reciprocal chart used below.
    fn generic_split_curve() -> SplitHyperellipticCurveP {
        let p = BigUint::from(5u32);
        SplitHyperellipticCurveP::try_new(
            p.clone(),
            FpPoly::from_coeffs(
                vec![
                    BigUint::zero(),
                    BigUint::one(),
                    BigUint::zero(),
                    BigUint::from(2u32),
                    BigUint::one(),
                    BigUint::one(),
                    BigUint::one(),
                ],
                p,
            ),
        )
        .unwrap()
    }

    /// Under `z=1/x, w=y/x^3`, the generic split fixture becomes the odd
    /// model `w^2=z^5+2z^3+z^2+z+1`.
    fn generic_odd_chart() -> HyperellipticCurveP {
        let p = BigUint::from(5u32);
        HyperellipticCurveP::try_new(
            p.clone(),
            FpPoly::from_coeffs(
                vec![
                    BigUint::one(),
                    BigUint::one(),
                    BigUint::one(),
                    BigUint::from(2u32),
                    BigUint::zero(),
                    BigUint::one(),
                ],
                p,
            ),
            2,
        )
        .unwrap()
    }

    fn poly_pow(mut base: FpPoly, mut exponent: usize) -> FpPoly {
        let mut out = FpPoly::one(base.p.clone());
        while exponent != 0 {
            if exponent & 1 == 1 {
                out = out.mul(&base);
            }
            exponent >>= 1;
            if exponent != 0 {
                base = base.mul(&base);
            }
        }
        out
    }

    /// Independent chart control for the exact F5 fixture.  The change
    /// `z=2/(u-2), w=v/(u-2)^3` sends `v^2=u^6+1` to
    /// `w^2=z^5+z+1`.  Old infinity+/- map to `(0,+/-1)` and the branch
    /// `(u,v)=(2,0)` maps to the odd chart's unique infinity.
    fn map_to_odd_chart(
        source: &SplitHyperellipticCurveP,
        divisor: &BalancedDivisorP,
        target: &HyperellipticCurveP,
    ) -> MumfordDivisorP {
        divisor.validate(source).unwrap();
        let p = BigUint::from(5u32);
        let degree = divisor.u.degree().unwrap();
        let z = FpPoly::x(p.clone());
        let two_z_plus_two = z
            .scalar_mul(&BigUint::from(2u32))
            .add(&FpPoly::constant(BigUint::from(2u32), p.clone()));
        let mut transformed_u = FpPoly::zero(p.clone());
        for i in 0..=degree {
            let term = poly_pow(two_z_plus_two.clone(), i)
                .mul(&poly_pow(z.clone(), degree - i))
                .scalar_mul(&divisor.u.coeff(i));
            transformed_u = transformed_u.add(&term);
        }
        let transformed_u = transformed_u.monic();

        // v(u)=v0+v1*u.  After substitution and multiplication by
        // z^3/8, w=((v0+2v1)z^3+2v1 z^2)/8.
        let v0 = divisor.v.coeff(0);
        let v1 = divisor.v.coeff(1);
        let a = (&v0 + BigUint::from(2u32) * &v1) % &p;
        let b = (BigUint::from(2u32) * &v1) % &p;
        let inverse_eight = BigUint::from(2u32);
        let transformed_v =
            FpPoly::from_coeffs(vec![BigUint::zero(), BigUint::zero(), b, a], p.clone())
                .scalar_mul(&inverse_eight)
                .rem(&transformed_u);
        let mut out =
            MumfordDivisorP::try_from_polynomials(target, transformed_u, transformed_v).unwrap();

        let plus =
            MumfordDivisorP::try_from_point(target, &BigUint::zero(), &BigUint::one()).unwrap();
        let minus = MumfordDivisorP::try_from_point(target, &BigUint::zero(), &BigUint::from(4u32))
            .unwrap();
        let n_minus = 2 - degree as u32 - divisor.n_plus;
        out = out
            .checked_add(
                &plus
                    .checked_scalar_mul(&BigUint::from(divisor.n_plus), target)
                    .unwrap(),
                target,
            )
            .unwrap();
        out = out
            .checked_add(
                &minus
                    .checked_scalar_mul(&BigUint::from(n_minus), target)
                    .unwrap(),
                target,
            )
            .unwrap();
        out = out
            .checked_add(&plus.checked_neg(target).unwrap(), target)
            .unwrap();
        out.checked_add(&minus.checked_neg(target).unwrap(), target)
            .unwrap()
    }

    /// Independent reciprocal-chart control for the generic fixture.
    /// `z=1/x, w=y/x^3` maps the finite branch `(0,0)` to the target's
    /// infinity and maps the source infinity+/- to `(0,+/-1)`.
    fn map_reciprocal_to_odd_chart(
        source: &SplitHyperellipticCurveP,
        divisor: &BalancedDivisorP,
        target: &HyperellipticCurveP,
    ) -> MumfordDivisorP {
        divisor.validate(source).unwrap();
        let p = BigUint::from(5u32);
        let degree = divisor.u.degree().unwrap();
        let z = FpPoly::x(p.clone());
        let mut transformed_u = FpPoly::zero(p.clone());
        for i in 0..=degree {
            transformed_u =
                transformed_u.add(&poly_pow(z.clone(), degree - i).scalar_mul(&divisor.u.coeff(i)));
        }
        let transformed_u = transformed_u.monic();

        // For genus two `v(x)=v0+v1*x`, hence
        // `w=z^3*v(1/z)=v0*z^3+v1*z^2` on the transformed support.
        let transformed_v = FpPoly::from_coeffs(
            vec![
                BigUint::zero(),
                BigUint::zero(),
                divisor.v.coeff(1),
                divisor.v.coeff(0),
            ],
            p.clone(),
        )
        .rem(&transformed_u);
        let mut out =
            MumfordDivisorP::try_from_polynomials(target, transformed_u, transformed_v).unwrap();

        let plus =
            MumfordDivisorP::try_from_point(target, &BigUint::zero(), &BigUint::one()).unwrap();
        let minus = MumfordDivisorP::try_from_point(target, &BigUint::zero(), &BigUint::from(4u32))
            .unwrap();
        let n_minus = 2 - degree as u32 - divisor.n_plus;
        out = out
            .checked_add(
                &plus
                    .checked_scalar_mul(&BigUint::from(divisor.n_plus), target)
                    .unwrap(),
                target,
            )
            .unwrap();
        out = out
            .checked_add(
                &minus
                    .checked_scalar_mul(&BigUint::from(n_minus), target)
                    .unwrap(),
                target,
            )
            .unwrap();
        out = out
            .checked_add(&plus.checked_neg(target).unwrap(), target)
            .unwrap();
        out.checked_add(&minus.checked_neg(target).unwrap(), target)
            .unwrap()
    }

    fn odd_key(divisor: &MumfordDivisorP) -> (Vec<BigUint>, Vec<BigUint>) {
        (divisor.u.coeffs.clone(), divisor.v.coeffs.clone())
    }

    #[test]
    fn f5_fixture_has_36_unique_balanced_classes_and_chart_images() {
        let split = f5_split_curve();
        let odd = odd_chart();
        let classes = split.enumerate_reduced_divisors().unwrap();
        assert_eq!(classes.len(), 36);
        assert_eq!(brute_force_jac_order(&odd), BigUint::from(36u32));

        let images = classes
            .iter()
            .map(|divisor| odd_key(&map_to_odd_chart(&split, divisor, &odd)))
            .collect::<BTreeSet<_>>();
        assert_eq!(images.len(), 36);

        for left in &classes {
            assert_eq!(
                left.checked_add(&left.checked_neg(&split).unwrap(), &split)
                    .unwrap(),
                BalancedDivisorP::try_identity(&split).unwrap()
            );
            for right in &classes {
                let sum = left.checked_add(right, &split).unwrap();
                let mapped_sum = map_to_odd_chart(&split, &sum, &odd);
                let expected = map_to_odd_chart(&split, left, &odd)
                    .checked_add(&map_to_odd_chart(&split, right, &odd), &odd)
                    .unwrap();
                assert_eq!(mapped_sum, expected);
            }
        }
    }

    #[test]
    fn generic_f5_fixture_checks_nontrivial_infinity_polynomial_and_group_law() {
        let split = generic_split_curve();
        let odd = generic_odd_chart();
        assert_eq!(
            split.infinity_polynomial(),
            &FpPoly::from_coeffs(
                vec![
                    BigUint::from(3u32),
                    BigUint::one(),
                    BigUint::from(3u32),
                    BigUint::one(),
                ],
                BigUint::from(5u32),
            )
        );

        let classes = split.enumerate_reduced_divisors().unwrap();
        assert_eq!(classes.len(), 32);
        assert_eq!(brute_force_jac_order(&odd), BigUint::from(32u32));
        let images = classes
            .iter()
            .map(|divisor| odd_key(&map_reciprocal_to_odd_chart(&split, divisor, &odd)))
            .collect::<BTreeSet<_>>();
        assert_eq!(images.len(), classes.len());

        for left in &classes {
            let triple_by_addition = left
                .checked_add(left, &split)
                .unwrap()
                .checked_add(left, &split)
                .unwrap();
            assert_eq!(
                left.checked_scalar_mul(&BigUint::from(3u32), &split)
                    .unwrap(),
                triple_by_addition
            );
            for right in &classes {
                let mapped_sum = map_reciprocal_to_odd_chart(
                    &split,
                    &left.checked_add(right, &split).unwrap(),
                    &odd,
                );
                let expected = map_reciprocal_to_odd_chart(&split, left, &odd)
                    .checked_add(&map_reciprocal_to_odd_chart(&split, right, &odd), &odd)
                    .unwrap();
                assert_eq!(mapped_sum, expected);
            }
        }
    }

    #[test]
    fn f5_fixture_exercises_shared_support_delta_and_associativity() {
        let curve = f5_split_curve();
        let classes = curve.enumerate_reduced_divisors().unwrap();
        let identity = BalancedDivisorP::try_identity(&curve).unwrap();
        let delta = BalancedDivisorP::try_infinity_difference(&curve).unwrap();
        assert_ne!(delta, identity);

        let mut shared_support = None;
        for (i, left) in classes.iter().enumerate() {
            for right in &classes[i + 1..] {
                if left.u == right.u {
                    shared_support = Some((left, right));
                    break;
                }
            }
            if shared_support.is_some() {
                break;
            }
        }
        let (left, right) = shared_support.expect("fixture has nontrivial shared support");
        left.checked_add(right, &curve)
            .unwrap()
            .validate(&curve)
            .unwrap();

        let branch =
            BalancedDivisorP::try_from_point(&curve, &BigUint::from(2u32), &BigUint::zero(), 0)
                .unwrap();
        branch
            .checked_add(&branch, &curve)
            .unwrap()
            .validate(&curve)
            .unwrap();

        for (i, a) in classes.iter().enumerate() {
            let b = &classes[(7 * i + 3) % classes.len()];
            let c = &classes[(11 * i + 5) % classes.len()];
            assert_eq!(
                a.checked_add(b, &curve)
                    .unwrap()
                    .checked_add(c, &curve)
                    .unwrap(),
                a.checked_add(&b.checked_add(c, &curve).unwrap(), &curve)
                    .unwrap()
            );
        }
    }

    #[test]
    fn corrected_chapter10_example_retains_infinity_translation() {
        let p = BigUint::from(37u32);
        let curve = SplitHyperellipticCurveP::try_new(
            p.clone(),
            FpPoly::from_coeffs(
                vec![
                    BigUint::one(),
                    BigUint::one(),
                    BigUint::zero(),
                    BigUint::zero(),
                    BigUint::zero(),
                    BigUint::zero(),
                    BigUint::one(),
                ],
                p.clone(),
            ),
        )
        .unwrap();
        assert_eq!(
            curve.infinity_polynomial(),
            &FpPoly::from_coeffs(
                vec![
                    BigUint::zero(),
                    BigUint::zero(),
                    BigUint::zero(),
                    BigUint::one(),
                ],
                p.clone(),
            )
        );
        let original = BalancedDivisorP::try_from_polynomials(
            &curve,
            FpPoly::from_coeffs(
                vec![BigUint::from(2u32), BigUint::from(34u32), BigUint::one()],
                p.clone(),
            ),
            FpPoly::from_coeffs(vec![BigUint::from(27u32), BigUint::from(32u32)], p.clone()),
            0,
        )
        .unwrap();
        let expected = BalancedDivisorP::try_from_polynomials(
            &curve,
            FpPoly::from_coeffs(
                vec![BigUint::from(2u32), BigUint::from(28u32), BigUint::one()],
                p.clone(),
            ),
            FpPoly::from_coeffs(vec![BigUint::from(22u32), BigUint::from(7u32)], p),
            0,
        )
        .unwrap();
        assert_eq!(
            original
                .checked_add(
                    &BalancedDivisorP::try_infinity_difference(&curve).unwrap(),
                    &curve,
                )
                .unwrap(),
            expected
        );
    }

    #[test]
    fn malformed_and_foreign_divisors_are_rejected() {
        let curve = f5_split_curve();
        let p = BigUint::from(5u32);
        assert!(SplitHyperellipticCurveP::try_new(BigUint::from(9u32), curve.f.clone()).is_err());
        assert!(SplitHyperellipticCurveP::try_new(
            p.clone(),
            FpPoly::from_coeffs(
                vec![
                    BigUint::one(),
                    BigUint::zero(),
                    BigUint::zero(),
                    BigUint::zero(),
                    BigUint::zero(),
                    BigUint::zero(),
                    BigUint::from(2u32),
                ],
                p.clone(),
            )
        )
        .is_err());
        assert!(BalancedDivisorP::try_from_polynomials(
            &curve,
            FpPoly::one(p.clone()),
            FpPoly::zero(p.clone()),
            3
        )
        .is_err());
        assert!(BalancedDivisorP::try_from_polynomials(
            &curve,
            FpPoly::from_coeffs(vec![BigUint::one(), BigUint::one()], p.clone()),
            FpPoly::constant(BigUint::from(2u32), p.clone()),
            0
        )
        .is_err());

        let foreign = SplitHyperellipticCurveP::try_new(
            p.clone(),
            FpPoly::from_coeffs(
                vec![
                    BigUint::from(2u32),
                    BigUint::one(),
                    BigUint::zero(),
                    BigUint::zero(),
                    BigUint::zero(),
                    BigUint::zero(),
                    BigUint::one(),
                ],
                p,
            ),
        )
        .unwrap();
        let foreign_identity = BalancedDivisorP::try_identity(&foreign).unwrap();
        assert_eq!(
            foreign_identity.validate(&curve),
            Err(BalancedHyperellipticError::DivisorCurveMismatch)
        );
    }
}
