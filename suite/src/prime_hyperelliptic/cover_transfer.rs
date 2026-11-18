//! Induced maps for the checked odd-prime quadratic cover family.
//!
//! For a short Weierstrass curve
//!
//! ```text
//! E : y^2 = x^3 + A*x + B
//! ```
//!
//! and a field element `c` with a nonzero right-hand side at `c`, this
//! module constructs
//!
//! ```text
//! C : v^2 = (u^2+c)^3 + A*(u^2+c) + B,
//! pi(u,v) = (u^2+c,v).
//! ```
//!
//! The source is a monic split sextic, so its Jacobian uses the balanced
//! `(u,v,n_plus)` representation from [`super::balanced`].  Both source
//! infinities map to the elliptic identity and the deck involution swaps
//! them.  Consequently the exact functorial identities are
//!
//! ```text
//! pi_* pi^* = [2]                 on E,
//! pi^* pi_* = 1 + deck_*          on Jac(C).
//! ```
//!
//! This implementation is deliberately limited to the same direct
//! short-Weierstrass prime-field and strict deterministic primality-proof
//! domain as the balanced backend.  It does not implement extension fields,
//! normalized Montgomery/Edwards target coordinates, exact subgroup-order
//! proofs, or a discrete-log solver.

use super::balanced::{BalancedDivisorP, BalancedHyperellipticError, SplitHyperellipticCurveP};
use super::fp_poly::{fp_inv, FpPoly};
use super::primality::{prime_proof_status, PrimeProofStatus, PSI13_EXCLUSIVE_BOUND_DECIMAL};
use num_bigint::BigUint;
use num_traits::{One, Zero};
use std::fmt;

/// A checked affine point or the identity on the direct short-Weierstrass
/// target.  Coordinates are required to be canonical residues when passed to
/// a [`PrimeQuadraticCoverP`] method.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum PrimeEllipticPointP {
    Infinity,
    Affine { x: BigUint, y: BigUint },
}

/// Checked failure from construction, target arithmetic, or an induced map.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum PrimeQuadraticCoverError {
    UnsupportedCharacteristic,
    UnsupportedPrimeModulusSize {
        maximum_bits: u32,
    },
    UnsupportedPrimalityProofRange {
        exclusive_upper_bound_decimal: &'static str,
    },
    ModulusNotPrime,
    NonCanonicalCoefficient {
        coefficient: &'static str,
    },
    SingularTarget,
    BranchValueZero,
    PointCoordinateOutOfRange {
        coordinate: &'static str,
    },
    PointNotOnTarget,
    Balanced(BalancedHyperellipticError),
    NonInvertibleDenominator {
        stage: &'static str,
    },
    InvalidSubgroupOrder,
    CompositionIdentityMismatch {
        identity: &'static str,
    },
}

impl fmt::Display for PrimeQuadraticCoverError {
    fn fmt(&self, out: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::UnsupportedCharacteristic => {
                write!(
                    out,
                    "quadratic cover transfer requires prime characteristic greater than 3"
                )
            }
            Self::UnsupportedPrimeModulusSize { maximum_bits } => write!(
                out,
                "prime modulus exceeds the deterministic {maximum_bits}-bit validation domain"
            ),
            Self::UnsupportedPrimalityProofRange {
                exclusive_upper_bound_decimal,
            } => write!(
                out,
                "prime modulus is outside the strict deterministic primality-proof range p < {exclusive_upper_bound_decimal}"
            ),
            Self::ModulusNotPrime => write!(out, "modulus is not prime"),
            Self::NonCanonicalCoefficient { coefficient } => {
                write!(out, "target coefficient {coefficient} is not canonical")
            }
            Self::SingularTarget => write!(out, "short-Weierstrass target is singular"),
            Self::BranchValueZero => write!(
                out,
                "chosen quadratic shift has zero elliptic right-hand side"
            ),
            Self::PointCoordinateOutOfRange { coordinate } => {
                write!(out, "target point coordinate {coordinate} is not canonical")
            }
            Self::PointNotOnTarget => write!(out, "point is not on the target elliptic curve"),
            Self::Balanced(error) => write!(out, "balanced source error: {error}"),
            Self::NonInvertibleDenominator { stage } => {
                write!(out, "noninvertible denominator during {stage}")
            }
            Self::InvalidSubgroupOrder => write!(out, "subgroup order must be positive"),
            Self::CompositionIdentityMismatch { identity } => {
                write!(out, "induced-map composition identity failed: {identity}")
            }
        }
    }
}

impl std::error::Error for PrimeQuadraticCoverError {}

impl From<BalancedHyperellipticError> for PrimeQuadraticCoverError {
    fn from(error: BalancedHyperellipticError) -> Self {
        Self::Balanced(error)
    }
}

/// Replayable certificate for `pi_* pi^* = [2]` on a checked target point.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PrimePullPushCertificate {
    pub input: PrimeEllipticPointP,
    pub pullback: BalancedDivisorP,
    pub pushforward: PrimeEllipticPointP,
    pub twice_input: PrimeEllipticPointP,
    pub identity_holds: bool,
}

/// Replayable certificate for `pi^* pi_* = 1 + deck_*` on a checked
/// balanced divisor class.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PrimePushPullCertificate {
    pub input: BalancedDivisorP,
    pub pushforward: PrimeEllipticPointP,
    pub pullback: BalancedDivisorP,
    pub deck_transform: BalancedDivisorP,
    pub input_plus_deck: BalancedDivisorP,
    pub identity_holds: bool,
}

/// What the degree-two composition identity establishes for a declared
/// subgroup order.  The order's exactness remains an external premise.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum PrimeSubgroupTransferStatus {
    InjectiveIfExactSubgroupOrder {
        order: BigUint,
        degree_inverse_mod_order: BigUint,
    },
    KernelIntersectionUnresolved {
        order: BigUint,
        common_factor: u32,
    },
}

/// Checked direct-prime instance of `prime_quadratic_pullback_v1`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PrimeQuadraticCoverP {
    p: BigUint,
    target_a: BigUint,
    target_b: BigUint,
    shift: BigUint,
    source: SplitHyperellipticCurveP,
}

impl PrimeQuadraticCoverP {
    /// Construct and independently recheck the target, branch value, source
    /// sextic, and supported prime-field boundary.
    pub fn try_new(
        p: BigUint,
        target_a: BigUint,
        target_b: BigUint,
        shift: BigUint,
    ) -> Result<Self, PrimeQuadraticCoverError> {
        if p <= BigUint::from(3u32) {
            return Err(PrimeQuadraticCoverError::UnsupportedCharacteristic);
        }
        match prime_proof_status(&p) {
            PrimeProofStatus::ProvedU64 | PrimeProofStatus::ProvedPsi13 => {}
            PrimeProofStatus::Composite => return Err(PrimeQuadraticCoverError::ModulusNotPrime),
            PrimeProofStatus::UnsupportedWithoutPrimalityCertificate => {
                return Err(PrimeQuadraticCoverError::UnsupportedPrimalityProofRange {
                    exclusive_upper_bound_decimal: PSI13_EXCLUSIVE_BOUND_DECIMAL,
                })
            }
        }
        for (coefficient, value) in [("a", &target_a), ("b", &target_b), ("c", &shift)] {
            if value >= &p {
                return Err(PrimeQuadraticCoverError::NonCanonicalCoefficient { coefficient });
            }
        }

        let four_a_cubed = mod_mul(
            &BigUint::from(4u32),
            &mod_mul(&mod_square(&target_a, &p), &target_a, &p),
            &p,
        );
        let twenty_seven_b_squared = mod_mul(&BigUint::from(27u32), &mod_square(&target_b, &p), &p);
        if mod_add(&four_a_cubed, &twenty_seven_b_squared, &p).is_zero() {
            return Err(PrimeQuadraticCoverError::SingularTarget);
        }
        if target_rhs(&shift, &target_a, &target_b, &p).is_zero() {
            return Err(PrimeQuadraticCoverError::BranchValueZero);
        }

        let coordinate_map = FpPoly::from_coeffs(
            vec![shift.clone(), BigUint::zero(), BigUint::one()],
            p.clone(),
        );
        let source_f = coordinate_map
            .mul(&coordinate_map)
            .mul(&coordinate_map)
            .add(&coordinate_map.scalar_mul(&target_a))
            .add(&FpPoly::constant(target_b.clone(), p.clone()));
        let source = SplitHyperellipticCurveP::try_new(p.clone(), source_f)?;

        Ok(Self {
            p,
            target_a,
            target_b,
            shift,
            source,
        })
    }

    pub fn modulus(&self) -> &BigUint {
        &self.p
    }

    pub fn target_a(&self) -> &BigUint {
        &self.target_a
    }

    pub fn target_b(&self) -> &BigUint {
        &self.target_b
    }

    pub fn shift(&self) -> &BigUint {
        &self.shift
    }

    pub fn source_curve(&self) -> &SplitHyperellipticCurveP {
        &self.source
    }

    /// Recheck every public construction invariant.
    pub fn validate(&self) -> Result<(), PrimeQuadraticCoverError> {
        let rebuilt = Self::try_new(
            self.p.clone(),
            self.target_a.clone(),
            self.target_b.clone(),
            self.shift.clone(),
        )?;
        if rebuilt != *self {
            return Err(PrimeQuadraticCoverError::CompositionIdentityMismatch {
                identity: "cover reconstruction",
            });
        }
        Ok(())
    }

    /// Recheck canonical coordinates and membership on the target curve.
    pub fn validate_target_point(
        &self,
        point: &PrimeEllipticPointP,
    ) -> Result<(), PrimeQuadraticCoverError> {
        let PrimeEllipticPointP::Affine { x, y } = point else {
            return Ok(());
        };
        if x >= &self.p {
            return Err(PrimeQuadraticCoverError::PointCoordinateOutOfRange { coordinate: "x" });
        }
        if y >= &self.p {
            return Err(PrimeQuadraticCoverError::PointCoordinateOutOfRange { coordinate: "y" });
        }
        if mod_square(y, &self.p) != target_rhs(x, &self.target_a, &self.target_b, &self.p) {
            return Err(PrimeQuadraticCoverError::PointNotOnTarget);
        }
        Ok(())
    }

    /// Checked target negation.
    pub fn checked_target_neg(
        &self,
        point: &PrimeEllipticPointP,
    ) -> Result<PrimeEllipticPointP, PrimeQuadraticCoverError> {
        self.validate_target_point(point)?;
        Ok(match point {
            PrimeEllipticPointP::Infinity => PrimeEllipticPointP::Infinity,
            PrimeEllipticPointP::Affine { x, y } => PrimeEllipticPointP::Affine {
                x: x.clone(),
                y: mod_neg(y, &self.p),
            },
        })
    }

    /// Checked affine short-Weierstrass addition, including identity,
    /// opposite-point, doubling, and rational two-torsion branches.
    pub fn checked_target_add(
        &self,
        left: &PrimeEllipticPointP,
        right: &PrimeEllipticPointP,
    ) -> Result<PrimeEllipticPointP, PrimeQuadraticCoverError> {
        self.validate_target_point(left)?;
        self.validate_target_point(right)?;
        let (x1, y1, x2, y2) = match (left, right) {
            (PrimeEllipticPointP::Infinity, _) => return Ok(right.clone()),
            (_, PrimeEllipticPointP::Infinity) => return Ok(left.clone()),
            (
                PrimeEllipticPointP::Affine { x: x1, y: y1 },
                PrimeEllipticPointP::Affine { x: x2, y: y2 },
            ) => (x1, y1, x2, y2),
        };

        let lambda = if x1 == x2 {
            if mod_add(y1, y2, &self.p).is_zero() {
                return Ok(PrimeEllipticPointP::Infinity);
            }
            let numerator = mod_add(
                &mod_mul(&BigUint::from(3u32), &mod_square(x1, &self.p), &self.p),
                &self.target_a,
                &self.p,
            );
            let denominator = mod_mul(&BigUint::from(2u32), y1, &self.p);
            let inverse = fp_inv(&denominator, &self.p).ok_or(
                PrimeQuadraticCoverError::NonInvertibleDenominator {
                    stage: "target doubling",
                },
            )?;
            mod_mul(&numerator, &inverse, &self.p)
        } else {
            let numerator = mod_sub(y2, y1, &self.p);
            let denominator = mod_sub(x2, x1, &self.p);
            let inverse = fp_inv(&denominator, &self.p).ok_or(
                PrimeQuadraticCoverError::NonInvertibleDenominator {
                    stage: "target addition",
                },
            )?;
            mod_mul(&numerator, &inverse, &self.p)
        };
        let x3 = mod_sub(
            &mod_sub(&mod_square(&lambda, &self.p), x1, &self.p),
            x2,
            &self.p,
        );
        let y3 = mod_sub(
            &mod_mul(&lambda, &mod_sub(x1, &x3, &self.p), &self.p),
            y1,
            &self.p,
        );
        let result = PrimeEllipticPointP::Affine { x: x3, y: y3 };
        self.validate_target_point(&result)?;
        Ok(result)
    }

    pub fn checked_target_scalar_mul(
        &self,
        point: &PrimeEllipticPointP,
        scalar: &BigUint,
    ) -> Result<PrimeEllipticPointP, PrimeQuadraticCoverError> {
        self.validate_target_point(point)?;
        let mut accumulator = PrimeEllipticPointP::Infinity;
        let mut addend = point.clone();
        for bit in 0..scalar.bits() {
            if scalar.bit(bit) {
                accumulator = self.checked_target_add(&accumulator, &addend)?;
            }
            if bit + 1 < scalar.bits() {
                addend = self.checked_target_add(&addend, &addend)?;
            }
        }
        Ok(accumulator)
    }

    /// Pull a rational target point class back to its complete degree-two
    /// fiber.  A branch fiber remains a valid repeated-support balanced
    /// divisor; it is not discarded or silently square-freed.
    pub fn pullback_point_class(
        &self,
        point: &PrimeEllipticPointP,
    ) -> Result<BalancedDivisorP, PrimeQuadraticCoverError> {
        self.validate_target_point(point)?;
        match point {
            PrimeEllipticPointP::Infinity => {
                BalancedDivisorP::try_identity(&self.source).map_err(Into::into)
            }
            PrimeEllipticPointP::Affine { x, y } => {
                let u = FpPoly::from_coeffs(
                    vec![
                        mod_sub(&self.shift, x, &self.p),
                        BigUint::zero(),
                        BigUint::one(),
                    ],
                    self.p.clone(),
                );
                let v = FpPoly::constant(y.clone(), self.p.clone());
                BalancedDivisorP::try_from_polynomials(&self.source, u, v, 0).map_err(Into::into)
            }
        }
    }

    /// Push an arbitrary canonical balanced genus-two class to the target.
    ///
    /// For quadratic support `U=T^2+sT+t`, `V=alpha*T+beta`, the two
    /// geometric images are summed using symmetric base-field formulas.  No
    /// support factorisation or extension-field choice is required.
    pub fn pushforward_arbitrary_balanced_class(
        &self,
        divisor: &BalancedDivisorP,
    ) -> Result<PrimeEllipticPointP, PrimeQuadraticCoverError> {
        divisor.validate(&self.source)?;
        let degree = divisor.u.degree().expect("validated nonzero u");
        let result = match degree {
            0 => PrimeEllipticPointP::Infinity,
            1 => {
                let root = mod_neg(&divisor.u.coeff(0), &self.p);
                PrimeEllipticPointP::Affine {
                    x: mod_add(&mod_square(&root, &self.p), &self.shift, &self.p),
                    y: divisor.v.coeff(0),
                }
            }
            2 => {
                let t = divisor.u.coeff(0);
                let s = divisor.u.coeff(1);
                let beta = divisor.v.coeff(0);
                let alpha = divisor.v.coeff(1);
                if !s.is_zero() {
                    let s_inverse = fp_inv(&s, &self.p).ok_or(
                        PrimeQuadraticCoverError::NonInvertibleDenominator {
                            stage: "quadratic-support norm",
                        },
                    )?;
                    let lambda = mod_neg(&mod_mul(&alpha, &s_inverse, &self.p), &self.p);
                    let roots_x_sum = mod_add(
                        &mod_sub(
                            &mod_square(&s, &self.p),
                            &mod_mul(&BigUint::from(2u32), &t, &self.p),
                            &self.p,
                        ),
                        &mod_mul(&BigUint::from(2u32), &self.shift, &self.p),
                        &self.p,
                    );
                    let x = mod_sub(&mod_square(&lambda, &self.p), &roots_x_sum, &self.p);
                    let y = mod_add(
                        &mod_neg(&beta, &self.p),
                        &mod_mul(
                            &lambda,
                            &mod_sub(&mod_sub(&self.shift, &t, &self.p), &x, &self.p),
                            &self.p,
                        ),
                        &self.p,
                    );
                    PrimeEllipticPointP::Affine { x, y }
                } else if !alpha.is_zero() {
                    // Divisibility of V^2-f by U forces beta=0 here.  The
                    // roots are opposite and their elliptic images are
                    // inverse points.
                    PrimeEllipticPointP::Infinity
                } else {
                    let point = PrimeEllipticPointP::Affine {
                        x: mod_sub(&self.shift, &t, &self.p),
                        y: beta,
                    };
                    self.checked_target_add(&point, &point)?
                }
            }
            _ => unreachable!("balanced validation restricts support degree to two"),
        };
        self.validate_target_point(&result)?;
        Ok(result)
    }

    /// Apply the cover's non-hyperelliptic deck involution `(u,v)->(-u,v)`.
    /// It swaps the two labelled infinity branches.
    pub fn deck_transform(
        &self,
        divisor: &BalancedDivisorP,
    ) -> Result<BalancedDivisorP, PrimeQuadraticCoverError> {
        divisor.validate(&self.source)?;
        let degree = divisor.u.degree().expect("validated nonzero u");
        let u = FpPoly::from_coeffs(
            (0..=degree)
                .map(|i| {
                    let coefficient = divisor.u.coeff(i);
                    if (degree + i).is_multiple_of(2) {
                        coefficient
                    } else {
                        mod_neg(&coefficient, &self.p)
                    }
                })
                .collect(),
            self.p.clone(),
        );
        let v = FpPoly::from_coeffs(
            divisor
                .v
                .coeffs
                .iter()
                .enumerate()
                .map(|(i, coefficient)| {
                    if i.is_multiple_of(2) {
                        coefficient.clone()
                    } else {
                        mod_neg(coefficient, &self.p)
                    }
                })
                .collect(),
            self.p.clone(),
        );
        let n_plus = (2 - degree) as u32 - divisor.n_plus;
        BalancedDivisorP::try_from_polynomials(&self.source, u, v, n_plus).map_err(Into::into)
    }

    pub fn pull_push_composition_certificate(
        &self,
        point: &PrimeEllipticPointP,
    ) -> Result<PrimePullPushCertificate, PrimeQuadraticCoverError> {
        let pullback = self.pullback_point_class(point)?;
        let pushforward = self.pushforward_arbitrary_balanced_class(&pullback)?;
        let twice_input = self.checked_target_add(point, point)?;
        let identity_holds = pushforward == twice_input;
        if !identity_holds {
            return Err(PrimeQuadraticCoverError::CompositionIdentityMismatch {
                identity: "pi_* pi^* = [2]",
            });
        }
        Ok(PrimePullPushCertificate {
            input: point.clone(),
            pullback,
            pushforward,
            twice_input,
            identity_holds,
        })
    }

    pub fn push_pull_composition_certificate(
        &self,
        divisor: &BalancedDivisorP,
    ) -> Result<PrimePushPullCertificate, PrimeQuadraticCoverError> {
        divisor.validate(&self.source)?;
        let pushforward = self.pushforward_arbitrary_balanced_class(divisor)?;
        let pullback = self.pullback_point_class(&pushforward)?;
        let deck_transform = self.deck_transform(divisor)?;
        let input_plus_deck = divisor.checked_add(&deck_transform, &self.source)?;
        let identity_holds = pullback == input_plus_deck;
        if !identity_holds {
            return Err(PrimeQuadraticCoverError::CompositionIdentityMismatch {
                identity: "pi^* pi_* = 1 + deck_*",
            });
        }
        Ok(PrimePushPullCertificate {
            input: divisor.clone(),
            pushforward,
            pullback,
            deck_transform,
            input_plus_deck,
            identity_holds,
        })
    }

    /// Classify the consequence of `pi_* pi^*=[2]` for a declared order.
    /// This method does not establish that the declared order is exact.
    pub fn subgroup_transfer_status(
        &self,
        order: &BigUint,
    ) -> Result<PrimeSubgroupTransferStatus, PrimeQuadraticCoverError> {
        if order.is_zero() {
            return Err(PrimeQuadraticCoverError::InvalidSubgroupOrder);
        }
        if order.bit(0) {
            let inverse = (order + BigUint::one()) / 2u32;
            debug_assert_eq!((&inverse * 2u32) % order, BigUint::one() % order);
            Ok(PrimeSubgroupTransferStatus::InjectiveIfExactSubgroupOrder {
                order: order.clone(),
                degree_inverse_mod_order: inverse,
            })
        } else {
            Ok(PrimeSubgroupTransferStatus::KernelIntersectionUnresolved {
                order: order.clone(),
                common_factor: 2,
            })
        }
    }
}

fn mod_add(left: &BigUint, right: &BigUint, p: &BigUint) -> BigUint {
    (left + right) % p
}

fn mod_sub(left: &BigUint, right: &BigUint, p: &BigUint) -> BigUint {
    (left + p - right % p) % p
}

fn mod_neg(value: &BigUint, p: &BigUint) -> BigUint {
    if value.is_zero() {
        BigUint::zero()
    } else {
        (p - value % p) % p
    }
}

fn mod_mul(left: &BigUint, right: &BigUint, p: &BigUint) -> BigUint {
    left * right % p
}

fn mod_square(value: &BigUint, p: &BigUint) -> BigUint {
    mod_mul(value, value, p)
}

fn target_rhs(x: &BigUint, a: &BigUint, b: &BigUint, p: &BigUint) -> BigUint {
    mod_add(
        &mod_add(&mod_mul(&mod_square(x, p), x, p), &mod_mul(a, x, p), p),
        b,
        p,
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::prime_hyperelliptic::{enumerate_fp2, Fp2, Fp2Ctx};
    use num_traits::ToPrimitive;
    use std::collections::BTreeSet;

    fn b(value: u64) -> BigUint {
        BigUint::from(value)
    }

    fn decimal(value: &str) -> BigUint {
        BigUint::parse_bytes(value.as_bytes(), 10).unwrap()
    }

    fn decimal_poly(values: &[&str], p: &BigUint) -> FpPoly {
        FpPoly::from_coeffs(
            values.iter().map(|value| decimal(value)).collect(),
            p.clone(),
        )
    }

    fn f5_cover() -> PrimeQuadraticCoverP {
        PrimeQuadraticCoverP::try_new(b(5), b(0), b(1), b(0)).unwrap()
    }

    fn f7_shifted_cover() -> PrimeQuadraticCoverP {
        PrimeQuadraticCoverP::try_new(b(7), b(1), b(0), b(1)).unwrap()
    }

    fn target_points(cover: &PrimeQuadraticCoverP) -> Vec<PrimeEllipticPointP> {
        let p = cover.p.to_u64().unwrap();
        let mut points = vec![PrimeEllipticPointP::Infinity];
        for x in 0..p {
            for y in 0..p {
                let point = PrimeEllipticPointP::Affine { x: b(x), y: b(y) };
                if cover.validate_target_point(&point).is_ok() {
                    points.push(point);
                }
            }
        }
        points
    }

    #[derive(Clone, Copy, Debug, PartialEq, Eq)]
    enum OraclePoint {
        Infinity,
        Affine { x: Fp2, y: Fp2 },
    }

    fn oracle_add(
        context: &Fp2Ctx,
        target_a: u64,
        left: OraclePoint,
        right: OraclePoint,
    ) -> OraclePoint {
        let (x1, y1, x2, y2) = match (left, right) {
            (OraclePoint::Infinity, point) | (point, OraclePoint::Infinity) => return point,
            (OraclePoint::Affine { x: x1, y: y1 }, OraclePoint::Affine { x: x2, y: y2 }) => {
                (x1, y1, x2, y2)
            }
        };
        let lambda = if x1 == x2 {
            if context.is_zero(context.add(y1, y2)) {
                return OraclePoint::Infinity;
            }
            let numerator = context.add(
                context.mul(context.from_fp(3), context.square(x1)),
                context.from_fp(target_a),
            );
            let denominator = context.mul(context.from_fp(2), y1);
            context.mul(numerator, context.inv(denominator).unwrap())
        } else {
            let numerator = context.sub(y2, y1);
            let denominator = context.sub(x2, x1);
            context.mul(numerator, context.inv(denominator).unwrap())
        };
        let x3 = context.sub(context.sub(context.square(lambda), x1), x2);
        let y3 = context.sub(context.mul(lambda, context.sub(x1, x3)), y1);
        OraclePoint::Affine { x: x3, y: y3 }
    }

    fn eval_fp2(context: &Fp2Ctx, polynomial: &FpPoly, value: Fp2) -> Fp2 {
        polynomial
            .coeffs
            .iter()
            .rev()
            .fold(context.zero(), |acc, coefficient| {
                context.add(
                    context.mul(acc, value),
                    context.from_fp(coefficient.to_u64().unwrap()),
                )
            })
    }

    fn oracle_pushforward(cover: &PrimeQuadraticCoverP, divisor: &BalancedDivisorP) -> OraclePoint {
        let p = cover.p.to_u64().unwrap();
        let context = Fp2Ctx::new(p);
        let degree = divisor.u.degree().unwrap();
        if degree == 0 {
            return OraclePoint::Infinity;
        }
        let mut roots: Vec<Fp2> = enumerate_fp2(&context)
            .filter(|root| context.is_zero(eval_fp2(&context, &divisor.u, *root)))
            .collect();
        assert!(!roots.is_empty());
        if roots.len() == 1 && degree == 2 {
            roots.push(roots[0]);
        }
        assert_eq!(roots.len(), degree);
        roots.into_iter().fold(OraclePoint::Infinity, |sum, root| {
            let x = context.add(
                context.square(root),
                context.from_fp(cover.shift.to_u64().unwrap()),
            );
            let y = eval_fp2(&context, &divisor.v, root);
            oracle_add(
                &context,
                cover.target_a.to_u64().unwrap(),
                sum,
                OraclePoint::Affine { x, y },
            )
        })
    }

    fn assert_matches_oracle(cover: &PrimeQuadraticCoverP, divisor: &BalancedDivisorP) {
        let production = cover.pushforward_arbitrary_balanced_class(divisor).unwrap();
        let oracle = oracle_pushforward(cover, divisor);
        match (production, oracle) {
            (PrimeEllipticPointP::Infinity, OraclePoint::Infinity) => {}
            (
                PrimeEllipticPointP::Affine { x, y },
                OraclePoint::Affine {
                    x: oracle_x,
                    y: oracle_y,
                },
            ) => {
                assert_eq!(oracle_x.b, 0, "norm x-coordinate did not descend");
                assert_eq!(oracle_y.b, 0, "norm y-coordinate did not descend");
                assert_eq!(x, b(oracle_x.a));
                assert_eq!(y, b(oracle_y.a));
            }
            mismatch => panic!("production/oracle mismatch: {mismatch:?}"),
        }
    }

    #[test]
    fn constructor_rejects_out_of_scope_and_malformed_models() {
        assert_eq!(
            PrimeQuadraticCoverP::try_new(b(3), b(1), b(1), b(0)).unwrap_err(),
            PrimeQuadraticCoverError::UnsupportedCharacteristic
        );
        assert_eq!(
            PrimeQuadraticCoverP::try_new(b(15), b(1), b(1), b(0)).unwrap_err(),
            PrimeQuadraticCoverError::ModulusNotPrime
        );
        assert!(matches!(
            PrimeQuadraticCoverP::try_new(decimal("3317044064679887385962123"), b(1), b(1), b(0)),
            Err(PrimeQuadraticCoverError::UnsupportedPrimalityProofRange { .. })
        ));
        assert_eq!(
            PrimeQuadraticCoverP::try_new(b(5), b(0), b(0), b(1)).unwrap_err(),
            PrimeQuadraticCoverError::SingularTarget
        );
        assert_eq!(
            PrimeQuadraticCoverP::try_new(b(5), b(1), b(0), b(0)).unwrap_err(),
            PrimeQuadraticCoverError::BranchValueZero
        );
        assert_eq!(
            PrimeQuadraticCoverP::try_new(b(5), b(5), b(1), b(0)).unwrap_err(),
            PrimeQuadraticCoverError::NonCanonicalCoefficient { coefficient: "a" }
        );
    }

    #[test]
    fn exhaustive_f5_maps_and_both_compositions_hold() {
        let cover = f5_cover();
        cover.validate().unwrap();
        let points = target_points(&cover);
        for point in &points {
            let certificate = cover.pull_push_composition_certificate(point).unwrap();
            assert!(certificate.identity_holds);
        }

        let classes = cover.source.enumerate_reduced_divisors().unwrap();
        assert_eq!(classes.len(), 36);
        for divisor in &classes {
            assert_matches_oracle(&cover, divisor);
            let certificate = cover.push_pull_composition_certificate(divisor).unwrap();
            assert!(certificate.identity_holds);
            assert_eq!(
                cover.deck_transform(&certificate.deck_transform).unwrap(),
                *divisor
            );
        }
        for left in &classes {
            for right in &classes {
                let source_sum = left.checked_add(right, &cover.source).unwrap();
                let mapped_sum = cover
                    .pushforward_arbitrary_balanced_class(&source_sum)
                    .unwrap();
                let expected = cover
                    .checked_target_add(
                        &cover.pushforward_arbitrary_balanced_class(left).unwrap(),
                        &cover.pushforward_arbitrary_balanced_class(right).unwrap(),
                    )
                    .unwrap();
                assert_eq!(mapped_sum, expected);
            }
        }
    }

    #[test]
    fn shifted_f7_oracle_covers_nonsplit_and_repeated_support() {
        let cover = f7_shifted_cover();
        let classes = cover.source.enumerate_reduced_divisors().unwrap();
        let context = Fp2Ctx::new(7);
        let mut nonsplit = 0usize;
        let mut repeated = 0usize;
        for divisor in &classes {
            assert_matches_oracle(&cover, divisor);
            assert!(
                cover
                    .push_pull_composition_certificate(divisor)
                    .unwrap()
                    .identity_holds
            );
            if divisor.u.degree() == Some(2) {
                let roots = enumerate_fp2(&context)
                    .filter(|root| context.is_zero(eval_fp2(&context, &divisor.u, *root)))
                    .collect::<Vec<_>>();
                if roots.len() == 1 {
                    repeated += 1;
                } else if roots.iter().any(|root| root.b != 0) {
                    nonsplit += 1;
                }
            }
        }
        assert!(nonsplit > 0);
        assert!(repeated > 0);

        for point in target_points(&cover) {
            assert!(
                cover
                    .pull_push_composition_certificate(&point)
                    .unwrap()
                    .identity_holds
            );
        }
    }

    #[test]
    fn ramification_infinity_kernel_and_subgroup_boundaries_are_explicit() {
        let cover = f5_cover();
        for y in [1u64, 4] {
            let point = PrimeEllipticPointP::Affine { x: b(0), y: b(y) };
            let pullback = cover.pullback_point_class(&point).unwrap();
            assert_eq!(
                pullback.u,
                FpPoly::from_coeffs(vec![b(0), b(0), b(1)], b(5))
            );
            assert_eq!(
                cover
                    .pushforward_arbitrary_balanced_class(&pullback)
                    .unwrap(),
                cover.checked_target_add(&point, &point).unwrap()
            );
        }

        let infinity_difference = BalancedDivisorP::try_infinity_difference(&cover.source).unwrap();
        assert_eq!(
            cover
                .pushforward_arbitrary_balanced_class(&infinity_difference)
                .unwrap(),
            PrimeEllipticPointP::Infinity
        );
        let negative_infinity_difference = cover.deck_transform(&infinity_difference).unwrap();
        assert_eq!(negative_infinity_difference.n_plus, 0);
        assert_eq!(
            infinity_difference
                .checked_add(&negative_infinity_difference, &cover.source)
                .unwrap(),
            BalancedDivisorP::try_identity(&cover.source).unwrap()
        );

        assert_eq!(
            cover.subgroup_transfer_status(&b(3)).unwrap(),
            PrimeSubgroupTransferStatus::InjectiveIfExactSubgroupOrder {
                order: b(3),
                degree_inverse_mod_order: b(2),
            }
        );
        assert_eq!(
            cover.subgroup_transfer_status(&b(4)).unwrap(),
            PrimeSubgroupTransferStatus::KernelIntersectionUnresolved {
                order: b(4),
                common_factor: 2,
            }
        );
        assert_eq!(
            cover
                .subgroup_transfer_status(&BigUint::zero())
                .unwrap_err(),
            PrimeQuadraticCoverError::InvalidSubgroupOrder
        );

        let invalid = PrimeEllipticPointP::Affine { x: b(0), y: b(0) };
        assert_eq!(
            cover.pullback_point_class(&invalid).unwrap_err(),
            PrimeQuadraticCoverError::PointNotOnTarget
        );
    }

    #[test]
    fn f5_pushforward_exercises_every_quadratic_formula_branch() {
        let cover = f5_cover();
        let classes = cover.source.enumerate_reduced_divisors().unwrap();
        let mut branches = BTreeSet::new();
        for divisor in classes {
            if divisor.u.degree() != Some(2) {
                continue;
            }
            let s = divisor.u.coeff(1);
            let alpha = divisor.v.coeff(1);
            branches.insert(if !s.is_zero() {
                "s_nonzero"
            } else if !alpha.is_zero() {
                "opposite_images"
            } else {
                "equal_images"
            });
        }
        assert_eq!(
            branches,
            BTreeSet::from(["equal_images", "opposite_images", "s_nonzero"])
        );
    }

    #[test]
    fn live_73_bit_direct_prime_fixtures_have_proved_transfer_certificates() {
        let p = decimal("5902977611310272157103");
        let order = decimal("5902977611275912361963");
        let inverse_two = decimal("2951488805637956180982");
        assert_eq!(prime_proof_status(&p), PrimeProofStatus::ProvedPsi13);
        assert_eq!(prime_proof_status(&order), PrimeProofStatus::ProvedPsi13);

        struct Fixture<'a> {
            a: &'a str,
            b: &'a str,
            x: &'a str,
            y: &'a str,
            twice_x: &'a str,
            twice_y: &'a str,
            branch_shift: &'a str,
            shift_zero_f: [&'a str; 7],
            branch_f: [&'a str; 7],
        }
        let fixtures = [
            Fixture {
                a: "4168100599208664723916",
                b: "240650161999037164785",
                x: "1",
                y: "1565394211633018828840",
                twice_x: "2166449215995689752841",
                twice_y: "655910884152868570217",
                branch_shift: "1",
                shift_zero_f: [
                    "240650161999037164785",
                    "0",
                    "4168100599208664723916",
                    "0",
                    "0",
                    "0",
                    "1",
                ],
                branch_f: [
                    "4408750761207701888702",
                    "0",
                    "4168100599208664723919",
                    "0",
                    "3",
                    "0",
                    "1",
                ],
            },
            Fixture {
                a: "1104650781063910579104",
                b: "736433854042607052736",
                x: "2",
                y: "1317253133347025070737",
                twice_x: "3055049816379877696639",
                twice_y: "5305973654456394958904",
                branch_shift: "2",
                shift_zero_f: [
                    "736433854042607052736",
                    "0",
                    "1104650781063910579104",
                    "0",
                    "0",
                    "0",
                    "1",
                ],
                branch_f: [
                    "2945735416170428210952",
                    "0",
                    "1104650781063910579116",
                    "0",
                    "6",
                    "0",
                    "1",
                ],
            },
        ];

        for (index, fixture) in fixtures.iter().enumerate() {
            let a = decimal(fixture.a);
            let target_b = decimal(fixture.b);
            let point = PrimeEllipticPointP::Affine {
                x: decimal(fixture.x),
                y: decimal(fixture.y),
            };
            let cover = PrimeQuadraticCoverP::try_new(
                p.clone(),
                a.clone(),
                target_b.clone(),
                BigUint::zero(),
            )
            .unwrap();
            cover.validate().unwrap();
            assert_eq!(
                cover.source_curve().f,
                decimal_poly(&fixture.shift_zero_f, &p)
            );
            cover.validate_target_point(&point).unwrap();
            assert_ne!(point, PrimeEllipticPointP::Infinity);
            assert_eq!(
                cover.checked_target_add(&point, &point).unwrap(),
                PrimeEllipticPointP::Affine {
                    x: decimal(fixture.twice_x),
                    y: decimal(fixture.twice_y),
                }
            );
            assert_eq!(
                cover.checked_target_scalar_mul(&point, &order).unwrap(),
                PrimeEllipticPointP::Infinity
            );

            let pull_push = cover.pull_push_composition_certificate(&point).unwrap();
            assert!(pull_push.identity_holds);
            assert!(!pull_push.pullback.is_identity());
            assert!(pull_push
                .pullback
                .checked_scalar_mul(&order, cover.source_curve())
                .unwrap()
                .is_identity());
            assert_eq!(
                cover
                    .checked_target_scalar_mul(&pull_push.pushforward, &inverse_two)
                    .unwrap(),
                point
            );
            assert_eq!(
                cover.subgroup_transfer_status(&order).unwrap(),
                PrimeSubgroupTransferStatus::InjectiveIfExactSubgroupOrder {
                    order: order.clone(),
                    degree_inverse_mod_order: inverse_two.clone(),
                }
            );

            for shift in 0u32..=3 {
                let shifted = PrimeQuadraticCoverP::try_new(
                    p.clone(),
                    a.clone(),
                    target_b.clone(),
                    BigUint::from(shift),
                )
                .unwrap();
                shifted.validate().unwrap();
                assert!(
                    shifted
                        .pull_push_composition_certificate(&point)
                        .unwrap()
                        .identity_holds
                );
            }

            // The first fixture has a rational source point u=1 over the
            // shift-zero cover. It is not deck invariant and exercises the
            // full source-side composition identity.
            if index == 0 {
                let divisor = BalancedDivisorP::try_from_point(
                    cover.source_curve(),
                    &BigUint::one(),
                    &decimal(fixture.y),
                    0,
                )
                .unwrap();
                assert_eq!(
                    cover
                        .pushforward_arbitrary_balanced_class(&divisor)
                        .unwrap(),
                    point
                );
                assert!(
                    cover
                        .push_pull_composition_certificate(&divisor)
                        .unwrap()
                        .identity_holds
                );
            }

            let branch_cover = PrimeQuadraticCoverP::try_new(
                p.clone(),
                a,
                target_b,
                decimal(fixture.branch_shift),
            )
            .unwrap();
            assert_eq!(
                branch_cover.source_curve().f,
                decimal_poly(&fixture.branch_f, &p)
            );
            let branch_pullback = branch_cover.pullback_point_class(&point).unwrap();
            assert_eq!(
                branch_pullback.u,
                FpPoly::from_coeffs(
                    vec![BigUint::zero(), BigUint::zero(), BigUint::one()],
                    p.clone(),
                )
            );
            assert!(
                branch_cover
                    .pull_push_composition_certificate(&point)
                    .unwrap()
                    .identity_holds
            );
        }
    }
}
