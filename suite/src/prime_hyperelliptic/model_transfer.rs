//! Checked degree-one changes of target model for odd-prime transfers.
//!
//! The quadratic-cover backend works on a short-Weierstrass target
//!
//! ```text
//! E_s : Y^2 = X^3 + a*X + b.
//! ```
//!
//! This module supplies the exact projective isomorphism to a Montgomery
//! model
//!
//! ```text
//! E_m : B*y^2 = x^3 + A*x^2 + x
//! ```
//!
//! in characteristic greater than three.  With `s=A/3`,
//!
//! ```text
//! a = (1 - A^2/3)/B^2,       b = (2*s^3 - s)/B^3,
//! x = B*X - s,                y = B*Y.
//! ```
//!
//! On the smooth plane cubics the maps are defined everywhere:
//!
//! ```text
//! [X:Y:Z] -> [B*X-s*Z : B*Y : Z]
//! [x:y:z] -> [x+s*z : y : B*z].
//! ```
//!
//! Their compositions multiply every homogeneous coordinate by the nonzero
//! scalar `B`, and the unique point at infinity `[0:1:0]` is therefore
//! retained.  This is different from the rational Edwards charts, whose
//! affine exceptional points still need a separate typed implementation.
//!
//! Construction uses the same deterministic prime-proof boundary as the
//! checked quadratic-cover backend.  A catalog normalization whose modulus
//! lies outside that boundary remains unsupported until it carries an
//! accepted primality certificate; an algebraic coordinate identity alone is
//! not field or subgroup evidence.

use super::cover_transfer::PrimeEllipticPointP;
use super::fp_poly::fp_inv;
use super::primality::{prime_proof_status, PrimeProofStatus, PSI13_EXCLUSIVE_BOUND_DECIMAL};
use num_bigint::BigUint;
use num_traits::{One, Zero};
use std::fmt;

/// An affine point or the identity on `B*y^2=x^3+A*x^2+x`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum PrimeMontgomeryPointP {
    Infinity,
    Affine { x: BigUint, y: BigUint },
}

/// A coordinate-bounded homogeneous triple on one of the two plane-cubic models.
///
/// The all-zero triple is never a point.  Equivalent nonzero scalar multiples
/// represent the same projective point; map round trips consequently need not
/// return the byte-identical triple.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PrimeProjectivePointP {
    pub x: BigUint,
    pub y: BigUint,
    pub z: BigUint,
}

/// Checked failure while constructing or applying a Montgomery model map.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum PrimeMontgomeryAdapterError {
    UnsupportedCharacteristic,
    UnsupportedPrimalityProofRange {
        exclusive_upper_bound_decimal: &'static str,
    },
    ModulusNotPrime,
    NonCanonicalCoefficient {
        coefficient: &'static str,
    },
    SingularMontgomeryModel,
    CoefficientIdentityMismatch,
    PointCoordinateOutOfRange {
        coordinate: &'static str,
    },
    InvalidProjectivePoint,
    PointNotOnShortModel,
    PointNotOnMontgomeryModel,
}

impl fmt::Display for PrimeMontgomeryAdapterError {
    fn fmt(&self, out: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::UnsupportedCharacteristic => write!(
                out,
                "Montgomery target normalization requires prime characteristic greater than 3"
            ),
            Self::UnsupportedPrimalityProofRange {
                exclusive_upper_bound_decimal,
            } => write!(
                out,
                "prime modulus is outside the strict deterministic primality-proof range p < {exclusive_upper_bound_decimal}"
            ),
            Self::ModulusNotPrime => write!(out, "modulus is not prime"),
            Self::NonCanonicalCoefficient { coefficient } => {
                write!(out, "Montgomery coefficient {coefficient} is not canonical")
            }
            Self::SingularMontgomeryModel => {
                write!(out, "Montgomery model requires B*(A^2-4) != 0")
            }
            Self::CoefficientIdentityMismatch => {
                write!(out, "Montgomery/short-Weierstrass coefficient identity failed")
            }
            Self::PointCoordinateOutOfRange { coordinate } => {
                write!(out, "point coordinate {coordinate} is not canonical")
            }
            Self::InvalidProjectivePoint => write!(out, "the all-zero projective triple is invalid"),
            Self::PointNotOnShortModel => {
                write!(out, "point is not on the short-Weierstrass model")
            }
            Self::PointNotOnMontgomeryModel => {
                write!(out, "point is not on the Montgomery model")
            }
        }
    }
}

impl std::error::Error for PrimeMontgomeryAdapterError {}

/// A checked projective isomorphism from a short-Weierstrass curve to a
/// Montgomery curve over the same prime field.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PrimeMontgomeryAdapterP {
    p: BigUint,
    montgomery_a: BigUint,
    montgomery_b: BigUint,
    shift_a_over_3: BigUint,
    inverse_b: BigUint,
    short_a: BigUint,
    short_b: BigUint,
}

impl PrimeMontgomeryAdapterP {
    /// Construct the exact map and recheck its coefficient identities.
    pub fn try_new(
        p: BigUint,
        montgomery_a: BigUint,
        montgomery_b: BigUint,
    ) -> Result<Self, PrimeMontgomeryAdapterError> {
        if p <= BigUint::from(3u32) {
            return Err(PrimeMontgomeryAdapterError::UnsupportedCharacteristic);
        }
        match prime_proof_status(&p) {
            PrimeProofStatus::ProvedU64 | PrimeProofStatus::ProvedPsi13 => {}
            PrimeProofStatus::Composite => {
                return Err(PrimeMontgomeryAdapterError::ModulusNotPrime)
            }
            PrimeProofStatus::UnsupportedWithoutPrimalityCertificate => {
                return Err(
                    PrimeMontgomeryAdapterError::UnsupportedPrimalityProofRange {
                        exclusive_upper_bound_decimal: PSI13_EXCLUSIVE_BOUND_DECIMAL,
                    },
                )
            }
        }
        for (coefficient, value) in [("A", &montgomery_a), ("B", &montgomery_b)] {
            if value >= &p {
                return Err(PrimeMontgomeryAdapterError::NonCanonicalCoefficient { coefficient });
            }
        }
        let four = BigUint::from(4u32) % &p;
        if montgomery_b.is_zero() || mod_square(&montgomery_a, &p) == four {
            return Err(PrimeMontgomeryAdapterError::SingularMontgomeryModel);
        }

        // p > 3 is prime and B != 0, so these inverses exist.
        let inverse_3 = fp_inv(&BigUint::from(3u32), &p)
            .ok_or(PrimeMontgomeryAdapterError::CoefficientIdentityMismatch)?;
        let inverse_b = fp_inv(&montgomery_b, &p)
            .ok_or(PrimeMontgomeryAdapterError::CoefficientIdentityMismatch)?;
        let shift_a_over_3 = mod_mul(&montgomery_a, &inverse_3, &p);
        let inverse_b_squared = mod_square(&inverse_b, &p);
        let inverse_b_cubed = mod_mul(&inverse_b_squared, &inverse_b, &p);
        let a_squared_over_3 = mod_mul(&mod_square(&montgomery_a, &p), &inverse_3, &p);
        let short_a = mod_mul(
            &mod_sub(&BigUint::one(), &a_squared_over_3, &p),
            &inverse_b_squared,
            &p,
        );
        let two_shift_cubed = mod_mul(
            &BigUint::from(2u32),
            &mod_mul(&mod_square(&shift_a_over_3, &p), &shift_a_over_3, &p),
            &p,
        );
        let short_b = mod_mul(
            &mod_sub(&two_shift_cubed, &shift_a_over_3, &p),
            &inverse_b_cubed,
            &p,
        );

        // Recheck the exact identities in the direction stored by the cover
        // catalog instead of trusting the derivation above.
        let b_squared = mod_square(&montgomery_b, &p);
        let b_cubed = mod_mul(&b_squared, &montgomery_b, &p);
        if mod_add(&mod_mul(&short_a, &b_squared, &p), &a_squared_over_3, &p) != BigUint::one()
            || mod_add(&mod_mul(&short_b, &b_cubed, &p), &shift_a_over_3, &p) != two_shift_cubed
        {
            return Err(PrimeMontgomeryAdapterError::CoefficientIdentityMismatch);
        }
        let short_discriminant = mod_add(
            &mod_mul(
                &BigUint::from(4u32),
                &mod_mul(&mod_square(&short_a, &p), &short_a, &p),
                &p,
            ),
            &mod_mul(&BigUint::from(27u32), &mod_square(&short_b, &p), &p),
            &p,
        );
        if short_discriminant.is_zero() {
            return Err(PrimeMontgomeryAdapterError::CoefficientIdentityMismatch);
        }

        Ok(Self {
            p,
            montgomery_a,
            montgomery_b,
            shift_a_over_3,
            inverse_b,
            short_a,
            short_b,
        })
    }

    pub fn modulus(&self) -> &BigUint {
        &self.p
    }

    pub fn montgomery_a(&self) -> &BigUint {
        &self.montgomery_a
    }

    pub fn montgomery_b(&self) -> &BigUint {
        &self.montgomery_b
    }

    pub fn shift_a_over_3(&self) -> &BigUint {
        &self.shift_a_over_3
    }

    pub fn short_a(&self) -> &BigUint {
        &self.short_a
    }

    pub fn short_b(&self) -> &BigUint {
        &self.short_b
    }

    /// Reconstruct the adapter from its public parameters.
    pub fn validate(&self) -> Result<(), PrimeMontgomeryAdapterError> {
        let rebuilt = Self::try_new(
            self.p.clone(),
            self.montgomery_a.clone(),
            self.montgomery_b.clone(),
        )?;
        if rebuilt != *self {
            return Err(PrimeMontgomeryAdapterError::CoefficientIdentityMismatch);
        }
        Ok(())
    }

    /// Check an affine short-Weierstrass point (or its identity).
    pub fn validate_short_point(
        &self,
        point: &PrimeEllipticPointP,
    ) -> Result<(), PrimeMontgomeryAdapterError> {
        let PrimeEllipticPointP::Affine { x, y } = point else {
            return Ok(());
        };
        self.validate_affine_coordinates(x, y)?;
        if mod_square(y, &self.p) != short_rhs(x, &self.short_a, &self.short_b, &self.p) {
            return Err(PrimeMontgomeryAdapterError::PointNotOnShortModel);
        }
        Ok(())
    }

    /// Check an affine Montgomery point (or its identity).
    pub fn validate_montgomery_point(
        &self,
        point: &PrimeMontgomeryPointP,
    ) -> Result<(), PrimeMontgomeryAdapterError> {
        let PrimeMontgomeryPointP::Affine { x, y } = point else {
            return Ok(());
        };
        self.validate_affine_coordinates(x, y)?;
        let lhs = mod_mul(&self.montgomery_b, &mod_square(y, &self.p), &self.p);
        if lhs != montgomery_rhs(x, &self.montgomery_a, &self.p) {
            return Err(PrimeMontgomeryAdapterError::PointNotOnMontgomeryModel);
        }
        Ok(())
    }

    /// Map a checked affine short-Weierstrass point to Montgomery coordinates.
    pub fn short_to_montgomery(
        &self,
        point: &PrimeEllipticPointP,
    ) -> Result<PrimeMontgomeryPointP, PrimeMontgomeryAdapterError> {
        self.validate_short_point(point)?;
        let image = match point {
            PrimeEllipticPointP::Infinity => PrimeMontgomeryPointP::Infinity,
            PrimeEllipticPointP::Affine { x, y } => PrimeMontgomeryPointP::Affine {
                x: mod_sub(
                    &mod_mul(&self.montgomery_b, x, &self.p),
                    &self.shift_a_over_3,
                    &self.p,
                ),
                y: mod_mul(&self.montgomery_b, y, &self.p),
            },
        };
        self.validate_montgomery_point(&image)?;
        Ok(image)
    }

    /// Map a checked affine Montgomery point to short-Weierstrass coordinates.
    pub fn montgomery_to_short(
        &self,
        point: &PrimeMontgomeryPointP,
    ) -> Result<PrimeEllipticPointP, PrimeMontgomeryAdapterError> {
        self.validate_montgomery_point(point)?;
        let image = match point {
            PrimeMontgomeryPointP::Infinity => PrimeEllipticPointP::Infinity,
            PrimeMontgomeryPointP::Affine { x, y } => PrimeEllipticPointP::Affine {
                x: mod_mul(
                    &mod_add(x, &self.shift_a_over_3, &self.p),
                    &self.inverse_b,
                    &self.p,
                ),
                y: mod_mul(y, &self.inverse_b, &self.p),
            },
        };
        self.validate_short_point(&image)?;
        Ok(image)
    }

    /// Check a homogeneous point on the short-Weierstrass plane cubic.
    pub fn validate_short_projective(
        &self,
        point: &PrimeProjectivePointP,
    ) -> Result<(), PrimeMontgomeryAdapterError> {
        self.validate_projective_coordinates(point)?;
        let z_squared = mod_square(&point.z, &self.p);
        let lhs = mod_mul(&mod_square(&point.y, &self.p), &point.z, &self.p);
        let rhs = mod_add(
            &mod_add(
                &mod_mul(&mod_square(&point.x, &self.p), &point.x, &self.p),
                &mod_mul(
                    &self.short_a,
                    &mod_mul(&point.x, &z_squared, &self.p),
                    &self.p,
                ),
                &self.p,
            ),
            &mod_mul(
                &self.short_b,
                &mod_mul(&z_squared, &point.z, &self.p),
                &self.p,
            ),
            &self.p,
        );
        if lhs != rhs {
            return Err(PrimeMontgomeryAdapterError::PointNotOnShortModel);
        }
        Ok(())
    }

    /// Check a homogeneous point on the Montgomery plane cubic.
    pub fn validate_montgomery_projective(
        &self,
        point: &PrimeProjectivePointP,
    ) -> Result<(), PrimeMontgomeryAdapterError> {
        self.validate_projective_coordinates(point)?;
        let z_squared = mod_square(&point.z, &self.p);
        let lhs = mod_mul(
            &self.montgomery_b,
            &mod_mul(&mod_square(&point.y, &self.p), &point.z, &self.p),
            &self.p,
        );
        let rhs = mod_add(
            &mod_add(
                &mod_mul(&mod_square(&point.x, &self.p), &point.x, &self.p),
                &mod_mul(
                    &self.montgomery_a,
                    &mod_mul(&mod_square(&point.x, &self.p), &point.z, &self.p),
                    &self.p,
                ),
                &self.p,
            ),
            &mod_mul(&point.x, &z_squared, &self.p),
            &self.p,
        );
        if lhs != rhs {
            return Err(PrimeMontgomeryAdapterError::PointNotOnMontgomeryModel);
        }
        Ok(())
    }

    /// Apply `[X:Y:Z] -> [B*X-s*Z:B*Y:Z]`.
    pub fn short_projective_to_montgomery(
        &self,
        point: &PrimeProjectivePointP,
    ) -> Result<PrimeProjectivePointP, PrimeMontgomeryAdapterError> {
        self.validate_short_projective(point)?;
        let image = PrimeProjectivePointP {
            x: mod_sub(
                &mod_mul(&self.montgomery_b, &point.x, &self.p),
                &mod_mul(&self.shift_a_over_3, &point.z, &self.p),
                &self.p,
            ),
            y: mod_mul(&self.montgomery_b, &point.y, &self.p),
            z: point.z.clone(),
        };
        self.validate_montgomery_projective(&image)?;
        Ok(image)
    }

    /// Apply `[x:y:z] -> [x+s*z:y:B*z]`.
    pub fn montgomery_projective_to_short(
        &self,
        point: &PrimeProjectivePointP,
    ) -> Result<PrimeProjectivePointP, PrimeMontgomeryAdapterError> {
        self.validate_montgomery_projective(point)?;
        let image = PrimeProjectivePointP {
            x: mod_add(
                &point.x,
                &mod_mul(&self.shift_a_over_3, &point.z, &self.p),
                &self.p,
            ),
            y: point.y.clone(),
            z: mod_mul(&self.montgomery_b, &point.z, &self.p),
        };
        self.validate_short_projective(&image)?;
        Ok(image)
    }

    fn validate_affine_coordinates(
        &self,
        x: &BigUint,
        y: &BigUint,
    ) -> Result<(), PrimeMontgomeryAdapterError> {
        if x >= &self.p {
            return Err(PrimeMontgomeryAdapterError::PointCoordinateOutOfRange { coordinate: "x" });
        }
        if y >= &self.p {
            return Err(PrimeMontgomeryAdapterError::PointCoordinateOutOfRange { coordinate: "y" });
        }
        Ok(())
    }

    fn validate_projective_coordinates(
        &self,
        point: &PrimeProjectivePointP,
    ) -> Result<(), PrimeMontgomeryAdapterError> {
        for (coordinate, value) in [("X", &point.x), ("Y", &point.y), ("Z", &point.z)] {
            if value >= &self.p {
                return Err(PrimeMontgomeryAdapterError::PointCoordinateOutOfRange { coordinate });
            }
        }
        if point.x.is_zero() && point.y.is_zero() && point.z.is_zero() {
            return Err(PrimeMontgomeryAdapterError::InvalidProjectivePoint);
        }
        Ok(())
    }
}

fn mod_add(left: &BigUint, right: &BigUint, p: &BigUint) -> BigUint {
    (left + right) % p
}

fn mod_sub(left: &BigUint, right: &BigUint, p: &BigUint) -> BigUint {
    (left + p - right % p) % p
}

fn mod_mul(left: &BigUint, right: &BigUint, p: &BigUint) -> BigUint {
    (left * right) % p
}

fn mod_square(value: &BigUint, p: &BigUint) -> BigUint {
    mod_mul(value, value, p)
}

fn short_rhs(x: &BigUint, a: &BigUint, b: &BigUint, p: &BigUint) -> BigUint {
    mod_add(
        &mod_add(&mod_mul(&mod_square(x, p), x, p), &mod_mul(a, x, p), p),
        b,
        p,
    )
}

fn montgomery_rhs(x: &BigUint, a: &BigUint, p: &BigUint) -> BigUint {
    mod_add(
        &mod_add(
            &mod_mul(&mod_square(x, p), x, p),
            &mod_mul(a, &mod_square(x, p), p),
            p,
        ),
        x,
        p,
    )
}
