//! Certified same-field genus-3 covers of ordinary binary elliptic curves.
//!
//! This module deliberately implements one construction family only.  Over
//! `k = GF(2^m)`, let
//!
//! ```text
//! E : y^2 + x*y = x^3 + a*x^2 + b,        b != 0,
//! d = sqrt(b),
//! H : v^2 + u^2*v = u^7 + a*u^4 + d*u.
//! ```
//!
//! Then
//!
//! ```text
//! phi : H -> E,       (u, v) |-> (u^3, u*v + d)
//! ```
//!
//! is a separable degree-three morphism over `k`.  The smooth projective
//! model of `H` has genus three and one rational point at infinity.  The map
//! is tamely ramified with index three at infinity and at `(u,v)=(0,0)`;
//! the latter maps to the rational two-torsion point `(0,d)` on `E`.
//!
//! The implementation constructs and validates the equations, maps rational
//! points, constructs `phi^*([P]-[O])` in reduced Mumford form, and pushes
//! arbitrary reduced Mumford classes forward.  The arbitrary-class path
//! factors the degree-at-most-three support over the base field and evaluates
//! each closed point by summing its residue-field Frobenius orbit.  The exact
//! exhaustive `GF(8)` fixture `a=1`, `b=3` retains its independently built
//! 486-class lookup table as a complete cross-check.  This module contains no
//! discrete-log solver or performance claim.

use super::{
    hyperelliptic::HyperellipticError, BinaryPoint, F2mElement, F2mPoly, HyperellipticCurve,
    IrreduciblePoly, MumfordDivisor,
};
use num_bigint::BigUint;
use num_traits::{One, Zero};
use std::collections::{HashMap, HashSet};
use std::fmt;
use std::sync::OnceLock;

/// Construction and transfer failures.  Unsupported operations are distinct
/// from invalid mathematical input.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum CoverTransferError {
    InvalidField(&'static str),
    FieldWidthMismatch {
        object: &'static str,
        expected: u32,
        actual: u32,
    },
    SingularTarget,
    PointNotOnTarget,
    PointNotOnCover,
    InvalidSubgroupOrder,
    ProjectorOrderNotCoprime {
        common_factor: u32,
    },
    DivisorNotInDeclaredTorsion,
    DivisorPolynomialTooLong {
        polynomial: &'static str,
        maximum_coefficients: usize,
        actual_coefficients: usize,
    },
    CertificateFailure(&'static str),
    Hyperelliptic(HyperellipticError),
    Unsupported(UnsupportedCoverOperation),
}

impl fmt::Display for CoverTransferError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InvalidField(reason) => write!(f, "invalid binary field: {reason}"),
            Self::FieldWidthMismatch {
                object,
                expected,
                actual,
            } => write!(f, "{object} has field width {actual}, expected {expected}"),
            Self::SingularTarget => write!(f, "ordinary binary target requires b != 0"),
            Self::PointNotOnTarget => write!(f, "point is not on the target elliptic curve"),
            Self::PointNotOnCover => write!(f, "point is not on the source cover"),
            Self::InvalidSubgroupOrder => write!(f, "subgroup order must be positive"),
            Self::ProjectorOrderNotCoprime { common_factor } => write!(
                f,
                "projector requires cover degree coprime to the declared torsion order (gcd={common_factor})"
            ),
            Self::DivisorNotInDeclaredTorsion => {
                write!(f, "divisor is not annihilated by the declared torsion order")
            }
            Self::DivisorPolynomialTooLong {
                polynomial,
                maximum_coefficients,
                actual_coefficients,
            } => write!(
                f,
                "fixed-fixture divisor polynomial {polynomial} has {actual_coefficients} coefficients, maximum {maximum_coefficients}"
            ),
            Self::CertificateFailure(reason) => write!(f, "cover certificate failed: {reason}"),
            Self::Hyperelliptic(error) => write!(f, "hyperelliptic validation failed: {error}"),
            Self::Unsupported(op) => write!(f, "unsupported cover operation: {op}"),
        }
    }
}

impl std::error::Error for CoverTransferError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            Self::Hyperelliptic(error) => Some(error),
            _ => None,
        }
    }
}

impl From<HyperellipticError> for CoverTransferError {
    fn from(error: HyperellipticError) -> Self {
        Self::Hyperelliptic(error)
    }
}

/// Operations intentionally outside the certified implementation boundary.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum UnsupportedCoverOperation {
    /// Retained for wire/source compatibility with pre-general-norm callers.
    /// Current checked covers implement this operation.
    ArbitraryJacobianPushforward,
}

impl fmt::Display for UnsupportedCoverOperation {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::ArbitraryJacobianPushforward => {
                write!(f, "pushforward of an arbitrary Jacobian class")
            }
        }
    }
}

/// A rational point on the genus-three source, including its unique point at
/// infinity.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum BinaryCoverPoint {
    Infinity,
    Affine { u: F2mElement, v: F2mElement },
}

/// Replayable fixed-family geometry facts checked during construction.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct BinaryCoverCertificate {
    pub construction: &'static str,
    pub field_degree: u32,
    pub modulus_irreducible: bool,
    pub target_nonsingular: bool,
    pub d_square_equals_b: bool,
    pub defining_equation_substitution: bool,
    pub source_model_validated: bool,
    pub source_genus: u32,
    pub map_degree: u32,
    pub map_separable: bool,
    pub unique_rational_infinity: bool,
    pub affine_smooth_at_u_zero: bool,
    pub infinity_smooth: bool,
    pub infinity_maps_to_target_infinity: bool,
    pub infinity_ramification_index: u32,
    pub exceptional_maps_to_two_torsion: bool,
    pub exceptional_ramification_index: u32,
    pub riemann_hurwitz_ramification_total: u32,
    pub artin_schreier_pole_orders: [u32; 2],
}

/// The three possible shapes of a point-class pullback.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum PullbackFiberKind {
    InfinityRamified { ramification_index: u32 },
    ExceptionalTwoTorsionRamified { ramification_index: u32 },
    GenericSeparable { geometric_degree: u32 },
}

/// A computable witness for `phi_* phi^* = [3]` on a rational elliptic
/// point class.  This specialized certificate does not claim a general
/// Jacobian pushforward implementation.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PullPushCompositionCertificate {
    pub input: BinaryPoint,
    pub pullback: MumfordDivisor,
    pub fiber_kind: PullbackFiberKind,
    pub formal_pushforward: BinaryPoint,
    pub three_times_input: BinaryPoint,
    pub identity_holds: bool,
}

/// One irreducible closed-point component of a reduced Mumford support and
/// its residue-field pushforward.
///
/// `support` is monic and irreducible over the base field.  Its degree is the
/// residue degree of the closed point.  `image` is the sum of the complete
/// Frobenius orbit after applying `phi`, represented in `E(k)`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ClosedPointPushforwardCertificate {
    pub support: F2mPoly,
    pub degree: usize,
    pub image: BinaryPoint,
}

/// Replayable decomposition of an arbitrary Jacobian pushforward into its
/// irreducible closed-point norms.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct JacobianPushforwardCertificate {
    pub input: MumfordDivisor,
    pub components: Vec<ClosedPointPushforwardCertificate>,
    pub reconstructed_support: F2mPoly,
    pub component_image_sum: BinaryPoint,
    pub general_pushforward: BinaryPoint,
    pub support_reconstruction_holds: bool,
    pub component_sum_holds: bool,
}

/// Closed-point certificate for one point-class pullback.
///
/// For a generic rational target point the component degrees sum to the
/// geometric cover degree three.  At a ramified point the reduced Mumford
/// support can have smaller degree; `fiber_kind` records the scheme-theoretic
/// multiplicity separately.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PullbackClosedPointCertificate {
    pub input: BinaryPoint,
    pub pullback: MumfordDivisor,
    pub fiber_kind: PullbackFiberKind,
    pub components: Vec<ClosedPointPushforwardCertificate>,
    pub reduced_support_degree: usize,
    pub component_image_sum: BinaryPoint,
    pub three_times_input: BinaryPoint,
    pub every_component_is_degree_times_input: bool,
    pub total_matches_three_times_input: bool,
}

/// Conditional subgroup-preservation consequence of `phi_* phi^* = [3]`.
///
/// This type does not certify that the caller's integer is the order of a
/// particular subgroup or generator.  `InjectiveIfExactSubgroupOrder` applies
/// only after that exact-order premise has been established independently.
/// If `3` divides the order, the composition identity alone does not settle
/// the kernel intersection.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum SubgroupTransferStatus {
    InjectiveIfExactSubgroupOrder {
        order: BigUint,
        degree_inverse_mod_order: BigUint,
    },
    KernelIntersectionUnresolved {
        order: BigUint,
        common_factor: u32,
    },
}

/// Replayable arbitrary-class certificate for `e=phi^* phi_*` and
/// `e^2=[3]e`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ImageEndomorphismCertificate {
    pub input: MumfordDivisor,
    pub pushforward: BinaryPoint,
    pub endomorphism: MumfordDivisor,
    pub endomorphism_squared: MumfordDivisor,
    pub three_times_endomorphism: MumfordDivisor,
    pub quadratic_identity_holds: bool,
    pub pushforward_kernel_member: bool,
}

/// Checked normalized projector on a declared order-`r` torsion module.
///
/// The certificate verifies that the input is killed by `r` and that three is
/// invertible modulo `r`.  It does not prove that `r` is prime or the exact
/// order of the input; callers bind those facts independently.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct TorsionProjectorCertificate {
    pub order: BigUint,
    pub degree_inverse_mod_order: BigUint,
    pub input: MumfordDivisor,
    pub normalized_projection: MumfordDivisor,
    pub complementary_component: MumfordDivisor,
    pub projection_is_idempotent: bool,
    pub projected_component_is_in_image: bool,
    pub complementary_component_is_in_pushforward_kernel: bool,
    pub input_is_in_image: bool,
    pub input_is_in_pushforward_kernel: bool,
    pub decomposition_holds: bool,
}

/// The checked fixed-family cover and its exact field/model data.
#[derive(Clone, Debug)]
pub struct OrdinaryBinaryCover {
    m: u32,
    irreducible: IrreduciblePoly,
    a: F2mElement,
    b: F2mElement,
    d: F2mElement,
    source: HyperellipticCurve,
    certificate: BinaryCoverCertificate,
}

type FixedF8DivisorKey = (Vec<BigUint>, Vec<BigUint>);

#[derive(Clone, Debug, PartialEq, Eq)]
enum ExtensionPoint {
    Infinity,
    Affine { x: F2mPoly, y: F2mPoly },
}

#[derive(Clone, Debug)]
struct FixedF8NormTable {
    images: HashMap<FixedF8DivisorKey, BinaryPoint>,
}

static FIXED_F8_NORM_TABLE: OnceLock<Result<FixedF8NormTable, CoverTransferError>> =
    OnceLock::new();

impl OrdinaryBinaryCover {
    /// Construct and validate the fixed ordinary-binary cover family.
    ///
    /// The polynomial basis is accepted only after an exact Rabin
    /// irreducibility check.  Field elements must already use that field
    /// width; unlike `F2mElement::from_biguint`, this API never truncates an
    /// input coefficient.
    pub fn new(
        m: u32,
        irreducible: IrreduciblePoly,
        a: F2mElement,
        b: F2mElement,
    ) -> Result<Self, CoverTransferError> {
        validate_field(m, &irreducible)?;
        check_width("a", &a, m)?;
        check_width("b", &b, m)?;
        if b.is_zero() {
            return Err(CoverTransferError::SingularTarget);
        }

        // The squaring map is an automorphism of GF(2^m), and its inverse is
        // the (m-1)-fold Frobenius: d = b^(2^(m-1)).
        let d = b.square_k_times(m - 1, &irreducible);
        if d.square(&irreducible) != b {
            return Err(CoverTransferError::CertificateFailure(
                "computed square root does not square to b",
            ));
        }

        let zero = F2mElement::zero(m);
        let one = F2mElement::one(m);
        let h = F2mPoly::from_coeffs(vec![zero.clone(), zero.clone(), one.clone()], m);
        let mut f_coeffs = vec![zero; 8];
        f_coeffs[1] = d.clone();
        f_coeffs[4] = a.clone();
        f_coeffs[7] = one;
        let f = F2mPoly::from_coeffs(f_coeffs, m);
        let source = HyperellipticCurve::try_new(m, irreducible.clone(), h, f, 3)?;

        if !verify_substitution(&source, &a, &b, &d) {
            return Err(CoverTransferError::CertificateFailure(
                "defining-equation substitution failed",
            ));
        }

        // For this exact equation, h'=0 and f'=u^6+d.  The only affine
        // zero of h is u=0, where f'=d != 0.  At infinity, t=1/u and
        // w=v/u^4 give w^2+t^2*w=t+a*t^4+d*t^7, whose t-derivative at
        // (0,0) is one.  The two AS poles have order three.
        let certificate = BinaryCoverCertificate {
            construction: "binary_cubic_pullback_v1",
            field_degree: m,
            modulus_irreducible: true,
            target_nonsingular: true,
            d_square_equals_b: true,
            defining_equation_substitution: true,
            source_model_validated: true,
            source_genus: 3,
            map_degree: 3,
            map_separable: true,
            unique_rational_infinity: true,
            affine_smooth_at_u_zero: !d.is_zero(),
            infinity_smooth: true,
            infinity_maps_to_target_infinity: true,
            infinity_ramification_index: 3,
            exceptional_maps_to_two_torsion: true,
            exceptional_ramification_index: 3,
            riemann_hurwitz_ramification_total: 4,
            artin_schreier_pole_orders: [3, 3],
        };
        if !certificate.affine_smooth_at_u_zero {
            return Err(CoverTransferError::CertificateFailure(
                "source is singular at u=0",
            ));
        }

        let cover = Self {
            m,
            irreducible,
            a,
            b,
            d,
            source,
            certificate,
        };
        cover.verify_certificate()?;
        Ok(cover)
    }

    pub fn field_degree(&self) -> u32 {
        self.m
    }

    pub fn irreducible_polynomial(&self) -> &IrreduciblePoly {
        &self.irreducible
    }

    pub fn target_a(&self) -> &F2mElement {
        &self.a
    }

    pub fn target_b(&self) -> &F2mElement {
        &self.b
    }

    pub fn square_root_b(&self) -> &F2mElement {
        &self.d
    }

    pub fn source_curve(&self) -> &HyperellipticCurve {
        &self.source
    }

    pub fn certificate(&self) -> &BinaryCoverCertificate {
        &self.certificate
    }

    /// Recompute every executable part of the fixed-family certificate.
    ///
    /// The infinity and ramification checks are deductions from the exact
    /// equation shape checked here: the infinity chart is
    /// `w^2+t^2*w=t+a*t^4+d*t^7`, while the Artin--Schreier form has pole
    /// order three at `u=0` and `u=infinity`.
    pub fn verify_certificate(&self) -> Result<(), CoverTransferError> {
        validate_field(self.m, &self.irreducible)?;
        check_width("a", &self.a, self.m)?;
        check_width("b", &self.b, self.m)?;
        check_width("d", &self.d, self.m)?;
        if self.b.is_zero() {
            return Err(CoverTransferError::SingularTarget);
        }
        if self.d.square(&self.irreducible) != self.b {
            return Err(CoverTransferError::CertificateFailure(
                "d^2 does not equal b",
            ));
        }
        self.source.validate()?;
        if self.source.m != self.m
            || self.source.irr.degree != self.irreducible.degree
            || self.source.irr.low_terms != self.irreducible.low_terms
            || self.source.genus != 3
        {
            return Err(CoverTransferError::CertificateFailure(
                "source curve field or genus changed",
            ));
        }

        let zero = F2mElement::zero(self.m);
        let one = F2mElement::one(self.m);
        let expected_h =
            F2mPoly::from_coeffs(vec![zero.clone(), zero.clone(), one.clone()], self.m);
        let mut expected_f_coefficients = vec![zero; 8];
        expected_f_coefficients[1] = self.d.clone();
        expected_f_coefficients[4] = self.a.clone();
        expected_f_coefficients[7] = one;
        let expected_f = F2mPoly::from_coeffs(expected_f_coefficients, self.m);
        if self.source.h != expected_h || self.source.f != expected_f {
            return Err(CoverTransferError::CertificateFailure(
                "source equation is not the certified fixed family",
            ));
        }
        if !verify_substitution(&self.source, &self.a, &self.b, &self.d) {
            return Err(CoverTransferError::CertificateFailure(
                "defining-equation substitution failed",
            ));
        }

        let exceptional_source = BinaryCoverPoint::Affine {
            u: F2mElement::zero(self.m),
            v: F2mElement::zero(self.m),
        };
        let exceptional_target = BinaryPoint::Affine {
            x: F2mElement::zero(self.m),
            y: self.d.clone(),
        };
        if self.map_point(&exceptional_source)? != exceptional_target
            || self.target_add(&exceptional_target, &exceptional_target)? != BinaryPoint::Infinity
            || self.map_point(&BinaryCoverPoint::Infinity)? != BinaryPoint::Infinity
        {
            return Err(CoverTransferError::CertificateFailure(
                "branch-point map certificate failed",
            ));
        }

        let cert = &self.certificate;
        let riemann_hurwitz_left = 2 * cert.source_genus - 2;
        let riemann_hurwitz_right =
            (cert.infinity_ramification_index - 1) + (cert.exceptional_ramification_index - 1);
        if !cert.modulus_irreducible
            || !cert.target_nonsingular
            || !cert.d_square_equals_b
            || !cert.defining_equation_substitution
            || !cert.source_model_validated
            || cert.field_degree != self.m
            || cert.source_genus != 3
            || cert.map_degree != 3
            || !cert.map_separable
            || !cert.unique_rational_infinity
            || !cert.affine_smooth_at_u_zero
            || !cert.infinity_smooth
            || !cert.infinity_maps_to_target_infinity
            || cert.infinity_ramification_index != 3
            || !cert.exceptional_maps_to_two_torsion
            || cert.exceptional_ramification_index != 3
            || cert.artin_schreier_pole_orders != [3, 3]
            || cert.riemann_hurwitz_ramification_total != riemann_hurwitz_right
            || riemann_hurwitz_left != riemann_hurwitz_right
        {
            return Err(CoverTransferError::CertificateFailure(
                "fixed-family geometry certificate is inconsistent",
            ));
        }
        Ok(())
    }

    /// Check the normalized ordinary target equation.
    pub fn target_is_on_curve(&self, point: &BinaryPoint) -> bool {
        match point {
            BinaryPoint::Infinity => true,
            BinaryPoint::Affine { x, y } => {
                if x.m_value() != self.m || y.m_value() != self.m {
                    return false;
                }
                let lhs = y
                    .square(&self.irreducible)
                    .add(&x.mul(y, &self.irreducible));
                let x2 = x.square(&self.irreducible);
                let rhs = x2
                    .mul(x, &self.irreducible)
                    .add(&self.a.mul(&x2, &self.irreducible))
                    .add(&self.b);
                lhs == rhs
            }
        }
    }

    /// Check the affine source equation, with infinity handled explicitly.
    pub fn source_is_on_curve(&self, point: &BinaryCoverPoint) -> bool {
        match point {
            BinaryCoverPoint::Infinity => true,
            BinaryCoverPoint::Affine { u, v } => {
                if u.m_value() != self.m || v.m_value() != self.m {
                    return false;
                }
                self.source.is_on_curve(u, v)
            }
        }
    }

    /// Evaluate `phi` on a rational source point.
    pub fn map_point(&self, point: &BinaryCoverPoint) -> Result<BinaryPoint, CoverTransferError> {
        if !self.source_is_on_curve(point) {
            return Err(CoverTransferError::PointNotOnCover);
        }
        let image = match point {
            BinaryCoverPoint::Infinity => BinaryPoint::Infinity,
            BinaryCoverPoint::Affine { u, v } => {
                let u2 = u.square(&self.irreducible);
                let x = u2.mul(u, &self.irreducible);
                let y = u.mul(v, &self.irreducible).add(&self.d);
                BinaryPoint::Affine { x, y }
            }
        };
        if !self.target_is_on_curve(&image) {
            return Err(CoverTransferError::CertificateFailure(
                "point map failed target equation",
            ));
        }
        Ok(image)
    }

    /// Push `[Q]-[infinity_H]` forward for one rational source point.
    /// The result is represented by the corresponding point of `E`, with
    /// `Infinity` denoting the identity class.
    pub fn pushforward_rational_point_divisor(
        &self,
        point: &BinaryCoverPoint,
    ) -> Result<BinaryPoint, CoverTransferError> {
        self.map_point(point)
    }

    /// Pull `[P]-[O_E]` back and reduce it in `Jac(H)`.
    ///
    /// For `x != 0`, the degree-three fiber has
    /// `U(t)=t^3+x` and `V(t)=((y+d)/x)t^2`.  At the exceptional
    /// two-torsion point `T=(0,d)`, the scheme fiber is `3(0,0)` and its
    /// reduced class is `(U,V)=(t,0)`.
    pub fn pullback_point_class(
        &self,
        point: &BinaryPoint,
    ) -> Result<MumfordDivisor, CoverTransferError> {
        if !self.target_is_on_curve(point) {
            return Err(CoverTransferError::PointNotOnTarget);
        }
        let divisor = match point {
            BinaryPoint::Infinity => MumfordDivisor::identity(self.m),
            BinaryPoint::Affine { x, y } if x.is_zero() => {
                if *y != self.d {
                    return Err(CoverTransferError::CertificateFailure(
                        "the unique point above x=0 is not (0,d)",
                    ));
                }
                MumfordDivisor::try_new(&self.source, F2mPoly::x(self.m), F2mPoly::zero(self.m))?
            }
            BinaryPoint::Affine { x, y } => {
                let x_inv = x.flt_inverse(&self.irreducible).ok_or(
                    CoverTransferError::CertificateFailure("nonzero x is not invertible"),
                )?;
                let c = y.add(&self.d).mul(&x_inv, &self.irreducible);
                let zero = F2mElement::zero(self.m);
                let one = F2mElement::one(self.m);
                MumfordDivisor::try_new(
                    &self.source,
                    F2mPoly::from_coeffs(vec![x.clone(), zero.clone(), zero.clone(), one], self.m),
                    F2mPoly::from_coeffs(vec![zero.clone(), zero, c], self.m),
                )?
            }
        };
        if !divisor.is_reduced(&self.source) {
            return Err(CoverTransferError::CertificateFailure(
                "pullback did not produce a reduced valid Mumford divisor",
            ));
        }
        Ok(divisor)
    }

    /// Return the fiber type used by the point-class pullback certificate.
    pub fn pullback_fiber_kind(
        &self,
        point: &BinaryPoint,
    ) -> Result<PullbackFiberKind, CoverTransferError> {
        if !self.target_is_on_curve(point) {
            return Err(CoverTransferError::PointNotOnTarget);
        }
        Ok(match point {
            BinaryPoint::Infinity => PullbackFiberKind::InfinityRamified {
                ramification_index: 3,
            },
            BinaryPoint::Affine { x, .. } if x.is_zero() => {
                PullbackFiberKind::ExceptionalTwoTorsionRamified {
                    ramification_index: 3,
                }
            }
            BinaryPoint::Affine { .. } => PullbackFiberKind::GenericSeparable {
                geometric_degree: 3,
            },
        })
    }

    /// Build a specialized, replayable certificate for
    /// `phi_* phi^*([P]-[O]) = [3]([P]-[O])`.
    pub fn pull_push_composition_certificate(
        &self,
        point: &BinaryPoint,
    ) -> Result<PullPushCompositionCertificate, CoverTransferError> {
        let pullback = self.pullback_point_class(point)?;
        let fiber_kind = self.pullback_fiber_kind(point)?;
        let formal_pushforward =
            self.formal_pushforward_of_point_pullback(point, &pullback, &fiber_kind)?;
        let three_times_input = self.target_scalar_mul_small(point, 3)?;
        let identity_holds = formal_pushforward == three_times_input;
        if !identity_holds {
            return Err(CoverTransferError::CertificateFailure(
                "push-pull composition did not equal multiplication by three",
            ));
        }
        Ok(PullPushCompositionCertificate {
            input: point.clone(),
            pullback,
            fiber_kind,
            formal_pushforward,
            three_times_input,
            identity_holds,
        })
    }

    /// Factor a point-class pullback into closed points and certify every
    /// component norm separately.
    ///
    /// A component of residue degree `s` in a fiber above a rational point
    /// `P` must push to `[s]P`.  This exposes that equality directly, including
    /// nonsplit degree-two and degree-three support, before the component
    /// images are summed.
    pub fn pullback_closed_point_certificate(
        &self,
        point: &BinaryPoint,
    ) -> Result<PullbackClosedPointCertificate, CoverTransferError> {
        let pullback = self.pullback_point_class(point)?;
        let fiber_kind = self.pullback_fiber_kind(point)?;
        let certificate = self.jacobian_pushforward_certificate(&pullback)?;
        let reduced_support_degree = certificate
            .components
            .iter()
            .map(|component| component.degree)
            .sum();
        let every_component_is_degree_times_input =
            certificate.components.iter().all(|component| {
                self.target_scalar_mul_small(point, component.degree as u32)
                    .is_ok_and(|expected| expected == component.image)
            });
        if !every_component_is_degree_times_input {
            return Err(CoverTransferError::CertificateFailure(
                "closed-point pullback component did not push to its residue degree times the input",
            ));
        }
        let three_times_input = self.target_scalar_mul_small(point, 3)?;
        let total_matches_three_times_input = certificate.component_image_sum == three_times_input;
        if !total_matches_three_times_input {
            return Err(CoverTransferError::CertificateFailure(
                "closed-point pullback components did not sum to three times the input",
            ));
        }
        Ok(PullbackClosedPointCertificate {
            input: point.clone(),
            pullback,
            fiber_kind,
            components: certificate.components,
            reduced_support_degree,
            component_image_sum: certificate.component_image_sum,
            three_times_input,
            every_component_is_degree_times_input,
            total_matches_three_times_input,
        })
    }

    /// Push the typed pullback witness forward without invoking a general
    /// Jacobian norm.  This is deliberately private: it is valid only for
    /// the three point fibers constructed by `pullback_point_class`.
    fn formal_pushforward_of_point_pullback(
        &self,
        point: &BinaryPoint,
        pullback: &MumfordDivisor,
        fiber_kind: &PullbackFiberKind,
    ) -> Result<BinaryPoint, CoverTransferError> {
        match (point, fiber_kind) {
            (
                BinaryPoint::Infinity,
                PullbackFiberKind::InfinityRamified {
                    ramification_index: 3,
                },
            ) => {
                if !pullback.is_identity() {
                    return Err(CoverTransferError::CertificateFailure(
                        "infinity pullback is not the identity class",
                    ));
                }
                self.pushforward_rational_point_divisor(&BinaryCoverPoint::Infinity)
            }
            (
                BinaryPoint::Affine { x, y },
                PullbackFiberKind::ExceptionalTwoTorsionRamified {
                    ramification_index: 3,
                },
            ) if x.is_zero() && *y == self.d => {
                let expected = MumfordDivisor::try_new(
                    &self.source,
                    F2mPoly::x(self.m),
                    F2mPoly::zero(self.m),
                )?;
                if pullback != &expected {
                    return Err(CoverTransferError::CertificateFailure(
                        "exceptional reduced pullback witness changed",
                    ));
                }
                if !expected.try_double(&self.source)?.is_identity() {
                    return Err(CoverTransferError::CertificateFailure(
                        "exceptional source-point class is not two-torsion",
                    ));
                }
                let image = self.pushforward_rational_point_divisor(&BinaryCoverPoint::Affine {
                    u: F2mElement::zero(self.m),
                    v: F2mElement::zero(self.m),
                })?;
                // Scheme-theoretically, phi^*(T-O)=3D for
                // D=[(0,0)]-[infinity].  The checked equality 2D=0 makes
                // the returned reduced pair represent 3D=D.  We push this
                // one rational-point class only; this is not a general
                // Jacobian norm.  Its image T=(0,d) also has order two, so
                // phi_*(3D)=phi_*(D)=T=[3]T.
                if self.target_scalar_mul_small(&image, 3)? != image {
                    return Err(CoverTransferError::CertificateFailure(
                        "exceptional image is not fixed by multiplication by three",
                    ));
                }
                Ok(image)
            }
            (
                BinaryPoint::Affine { x, y },
                PullbackFiberKind::GenericSeparable { geometric_degree },
            ) if !x.is_zero() && *geometric_degree == 3 => {
                let x_inverse = x.flt_inverse(&self.irreducible).ok_or(
                    CoverTransferError::CertificateFailure("generic fiber x is not invertible"),
                )?;
                let coefficient = y.add(&self.d).mul(&x_inverse, &self.irreducible);
                let zero = F2mElement::zero(self.m);
                let expected = MumfordDivisor::try_new(
                    &self.source,
                    F2mPoly::from_coeffs(
                        vec![
                            x.clone(),
                            zero.clone(),
                            zero.clone(),
                            F2mElement::one(self.m),
                        ],
                        self.m,
                    ),
                    F2mPoly::from_coeffs(vec![zero.clone(), zero, coefficient], self.m),
                )?;
                if pullback != &expected {
                    return Err(CoverTransferError::CertificateFailure(
                        "generic pullback witness changed",
                    ));
                }

                // U=t^3+x is separable for x!=0: U'=t^2 has no common
                // root with U.  Its three geometric support points all map
                // to P, so sum their point classes directly.
                let mut image_sum = BinaryPoint::Infinity;
                for _ in 0..*geometric_degree {
                    image_sum = self.target_add(&image_sum, point)?;
                }
                Ok(image_sum)
            }
            _ => Err(CoverTransferError::CertificateFailure(
                "point and pullback fiber kind are inconsistent",
            )),
        }
    }

    /// Derive the subgroup-preservation condition from `phi_* phi^* = [3]`.
    ///
    /// The integer is not bound to a subgroup or generator by this method.
    /// Therefore the injective result is conditional on the caller separately
    /// proving that `order` is the exact order of the subgroup in question.
    pub fn subgroup_transfer_status(
        &self,
        order: &BigUint,
    ) -> Result<SubgroupTransferStatus, CoverTransferError> {
        if order.is_zero() {
            return Err(CoverTransferError::InvalidSubgroupOrder);
        }
        let three = BigUint::from(3u32);
        let residue = order % &three;
        if residue.is_zero() {
            return Ok(SubgroupTransferStatus::KernelIntersectionUnresolved {
                order: order.clone(),
                common_factor: 3,
            });
        }
        let inverse = if residue == BigUint::one() {
            (order * 2u32 + 1u32) / 3u32
        } else {
            (order + 1u32) / 3u32
        };
        debug_assert_eq!((&inverse * 3u32) % order, BigUint::one() % order);
        Ok(SubgroupTransferStatus::InjectiveIfExactSubgroupOrder {
            order: order.clone(),
            degree_inverse_mod_order: inverse,
        })
    }

    /// Push an arbitrary reduced Jacobian class to the target elliptic curve.
    ///
    /// A reduced genus-three class has degree-at-most-three support.  The
    /// implementation factors its monic support polynomial over the base
    /// field.  A linear factor is mapped directly.  For an irreducible factor
    /// `g` of degree two or three it evaluates `phi` in `k[t]/(g)` and sums
    /// the complete `q`-Frobenius orbit, which is the pushforward of that
    /// closed point.  Repeated linear factors retain their multiplicity.  This
    /// covers split and nonsplit support without enumerating the base field.
    ///
    /// On the exact exhaustive `GF(8)`, `a=1`, `b=3` fixture, construction
    /// of the retained 486-class lookup table compares every entry with this
    /// residue-field implementation before the table is used as a fast exact
    /// cross-check.
    pub fn pushforward_arbitrary_jacobian_class(
        &self,
        divisor: &MumfordDivisor,
    ) -> Result<BinaryPoint, CoverTransferError> {
        if divisor.u.coeffs.len() > 4 {
            return Err(CoverTransferError::DivisorPolynomialTooLong {
                polynomial: "u",
                maximum_coefficients: 4,
                actual_coefficients: divisor.u.coeffs.len(),
            });
        }
        if divisor.v.coeffs.len() > 3 {
            return Err(CoverTransferError::DivisorPolynomialTooLong {
                polynomial: "v",
                maximum_coefficients: 3,
                actual_coefficients: divisor.v.coeffs.len(),
            });
        }
        divisor.validate(&self.source)?;
        if self.is_fixed_f8_norm_fixture() {
            let table = FIXED_F8_NORM_TABLE
                .get_or_init(|| self.build_fixed_f8_norm_table())
                .as_ref()
                .map_err(Clone::clone)?;
            return table
                .images
                .get(&fixed_f8_divisor_key(divisor))
                .cloned()
                .ok_or(CoverTransferError::CertificateFailure(
                    "validated fixed-fixture divisor is absent from the 486-class norm table",
                ));
        }
        self.pushforward_via_residue_fields(divisor)
    }

    /// Certify an arbitrary pushforward component by component.
    ///
    /// This is the public evidence surface for the residue-field norm used by
    /// [`Self::pushforward_arbitrary_jacobian_class`].  It reconstructs the
    /// Mumford support from monic irreducible factors, reports each factor's
    /// closed-point image, sums those images, and compares the result with the
    /// general pushforward path.  On the fixed `GF(8)` fixture the latter is
    /// the independently enumerated 486-class lookup table.
    pub fn jacobian_pushforward_certificate(
        &self,
        divisor: &MumfordDivisor,
    ) -> Result<JacobianPushforwardCertificate, CoverTransferError> {
        if divisor.u.coeffs.len() > 4 {
            return Err(CoverTransferError::DivisorPolynomialTooLong {
                polynomial: "u",
                maximum_coefficients: 4,
                actual_coefficients: divisor.u.coeffs.len(),
            });
        }
        if divisor.v.coeffs.len() > 3 {
            return Err(CoverTransferError::DivisorPolynomialTooLong {
                polynomial: "v",
                maximum_coefficients: 3,
                actual_coefficients: divisor.v.coeffs.len(),
            });
        }
        divisor.validate(&self.source)?;
        let factors = self.factor_small_support(&divisor.u)?;
        let reconstructed_support = factors
            .iter()
            .fold(F2mPoly::one(self.m), |product, factor| {
                product.mul(factor, &self.irreducible)
            });
        let support_reconstruction_holds = reconstructed_support == divisor.u;
        if !support_reconstruction_holds {
            return Err(CoverTransferError::CertificateFailure(
                "closed-point certificate did not reconstruct the Mumford support",
            ));
        }

        let mut components = Vec::with_capacity(factors.len());
        let mut component_image_sum = BinaryPoint::Infinity;
        for support in factors {
            let degree = support
                .degree()
                .ok_or(CoverTransferError::CertificateFailure(
                    "closed-point certificate contains the zero polynomial",
                ))?;
            let image = self.pushforward_irreducible_support(&support, &divisor.v)?;
            component_image_sum = self.target_add(&component_image_sum, &image)?;
            components.push(ClosedPointPushforwardCertificate {
                support,
                degree,
                image,
            });
        }
        let general_pushforward = self.pushforward_arbitrary_jacobian_class(divisor)?;
        let component_sum_holds = component_image_sum == general_pushforward;
        if !component_sum_holds {
            return Err(CoverTransferError::CertificateFailure(
                "closed-point component sum differs from the general pushforward",
            ));
        }
        Ok(JacobianPushforwardCertificate {
            input: divisor.clone(),
            components,
            reconstructed_support,
            component_image_sum,
            general_pushforward,
            support_reconstruction_holds,
            component_sum_holds,
        })
    }

    /// Evaluate `e=phi^* phi_*` on an arbitrary reduced class.
    pub fn elliptic_image_endomorphism(
        &self,
        divisor: &MumfordDivisor,
    ) -> Result<MumfordDivisor, CoverTransferError> {
        let image = self.pushforward_arbitrary_jacobian_class(divisor)?;
        self.pullback_point_class(&image)
    }

    /// Certify `e^2=[3]e` for one arbitrary reduced class.
    pub fn image_endomorphism_certificate(
        &self,
        divisor: &MumfordDivisor,
    ) -> Result<ImageEndomorphismCertificate, CoverTransferError> {
        divisor.validate(&self.source)?;
        let pushforward = self.pushforward_arbitrary_jacobian_class(divisor)?;
        let endomorphism = self.pullback_point_class(&pushforward)?;
        let endomorphism_squared = self.elliptic_image_endomorphism(&endomorphism)?;
        let three_times_endomorphism =
            endomorphism.try_scalar_mul(&BigUint::from(3u32), &self.source)?;
        let quadratic_identity_holds = endomorphism_squared == three_times_endomorphism;
        if !quadratic_identity_holds {
            return Err(CoverTransferError::CertificateFailure(
                "elliptic-image endomorphism did not satisfy e^2=[3]e",
            ));
        }
        let pushforward_kernel_member = pushforward == BinaryPoint::Infinity;
        Ok(ImageEndomorphismCertificate {
            input: divisor.clone(),
            pushforward,
            endomorphism,
            endomorphism_squared,
            three_times_endomorphism,
            quadratic_identity_holds,
            pushforward_kernel_member,
        })
    }

    /// Normalize `e` to the idempotent `[3^-1]e` on declared order-`r`
    /// torsion and separate image and complementary components.
    pub fn torsion_projector_certificate(
        &self,
        divisor: &MumfordDivisor,
        order: &BigUint,
    ) -> Result<TorsionProjectorCertificate, CoverTransferError> {
        divisor.validate(&self.source)?;
        if !divisor.try_scalar_mul(order, &self.source)?.is_identity() {
            return Err(CoverTransferError::DivisorNotInDeclaredTorsion);
        }
        let degree_inverse_mod_order = match self.subgroup_transfer_status(order)? {
            SubgroupTransferStatus::InjectiveIfExactSubgroupOrder {
                degree_inverse_mod_order,
                ..
            } => degree_inverse_mod_order,
            SubgroupTransferStatus::KernelIntersectionUnresolved { common_factor, .. } => {
                return Err(CoverTransferError::ProjectorOrderNotCoprime { common_factor });
            }
        };

        let endomorphism = self.elliptic_image_endomorphism(divisor)?;
        let normalized_projection =
            endomorphism.try_scalar_mul(&degree_inverse_mod_order, &self.source)?;
        let projection_twice = self
            .elliptic_image_endomorphism(&normalized_projection)?
            .try_scalar_mul(&degree_inverse_mod_order, &self.source)?;
        let projection_is_idempotent = projection_twice == normalized_projection;
        if !projection_is_idempotent {
            return Err(CoverTransferError::CertificateFailure(
                "normalized elliptic-image projector is not idempotent",
            ));
        }

        let complementary_component =
            divisor.try_add(&normalized_projection.try_neg(&self.source)?, &self.source)?;
        let projected_pushforward =
            self.pushforward_arbitrary_jacobian_class(&normalized_projection)?;
        let projected_roundtrip = self.pullback_point_class(&projected_pushforward)?;
        let three_times_projection =
            normalized_projection.try_scalar_mul(&BigUint::from(3u32), &self.source)?;
        let projected_component_is_in_image = projected_roundtrip == three_times_projection;
        let complementary_component_is_in_pushforward_kernel = self
            .pushforward_arbitrary_jacobian_class(&complementary_component)?
            == BinaryPoint::Infinity;
        let input_is_in_image = &normalized_projection == divisor;
        let input_is_in_pushforward_kernel =
            self.pushforward_arbitrary_jacobian_class(divisor)? == BinaryPoint::Infinity;
        let decomposition_holds = normalized_projection
            .try_add(&complementary_component, &self.source)?
            == divisor.clone();
        if !projected_component_is_in_image
            || !complementary_component_is_in_pushforward_kernel
            || !decomposition_holds
        {
            return Err(CoverTransferError::CertificateFailure(
                "normalized projector decomposition certificate failed",
            ));
        }
        Ok(TorsionProjectorCertificate {
            order: order.clone(),
            degree_inverse_mod_order,
            input: divisor.clone(),
            normalized_projection,
            complementary_component,
            projection_is_idempotent,
            projected_component_is_in_image,
            complementary_component_is_in_pushforward_kernel,
            input_is_in_image,
            input_is_in_pushforward_kernel,
            decomposition_holds,
        })
    }

    fn pushforward_via_residue_fields(
        &self,
        divisor: &MumfordDivisor,
    ) -> Result<BinaryPoint, CoverTransferError> {
        divisor.validate(&self.source)?;
        let factors = self.factor_small_support(&divisor.u)?;
        let mut image = BinaryPoint::Infinity;
        for factor in factors {
            let closed_point_image = self.pushforward_irreducible_support(&factor, &divisor.v)?;
            image = self.target_add(&image, &closed_point_image)?;
        }
        Ok(image)
    }

    fn factor_small_support(
        &self,
        polynomial: &F2mPoly,
    ) -> Result<Vec<F2mPoly>, CoverTransferError> {
        let mut factors = Vec::new();
        self.factor_small_support_recursive(polynomial, &mut factors)?;
        let product = factors
            .iter()
            .fold(F2mPoly::one(self.m), |product, factor| {
                product.mul(factor, &self.irreducible)
            });
        if product != *polynomial {
            return Err(CoverTransferError::CertificateFailure(
                "small-support factorization did not reconstruct the input",
            ));
        }
        Ok(factors)
    }

    fn factor_small_support_recursive(
        &self,
        polynomial: &F2mPoly,
        factors: &mut Vec<F2mPoly>,
    ) -> Result<(), CoverTransferError> {
        let degree = polynomial
            .degree()
            .ok_or(CoverTransferError::CertificateFailure(
                "cannot factor the zero support polynomial",
            ))?;
        if degree == 0 {
            return Ok(());
        }
        if degree == 1 {
            factors.push(polynomial.clone());
            return Ok(());
        }
        if degree > 3 || polynomial.lead() != F2mElement::one(self.m) {
            return Err(CoverTransferError::CertificateFailure(
                "small-support factorization requires a monic polynomial of degree at most three",
            ));
        }

        let derivative = formal_derivative_over_base(polynomial);
        if derivative.is_zero() {
            let mut square_root_coefficients = Vec::with_capacity(degree / 2 + 1);
            for exponent in (0..=degree).step_by(2) {
                square_root_coefficients.push(
                    polynomial
                        .coeff(exponent)
                        .square_k_times(self.m - 1, &self.irreducible),
                );
            }
            let square_root = F2mPoly::from_coeffs(square_root_coefficients, self.m);
            if square_root.mul(&square_root, &self.irreducible) != *polynomial {
                return Err(CoverTransferError::CertificateFailure(
                    "inseparable support square root did not reconstruct the polynomial",
                ));
            }
            let start = factors.len();
            self.factor_small_support_recursive(&square_root, factors)?;
            let repeated = factors[start..].to_vec();
            factors.extend(repeated);
            return Ok(());
        }

        let repeated_part = polynomial.gcd(&derivative, &self.irreducible);
        let repeated_degree = repeated_part.degree().unwrap_or(0);
        if repeated_degree > 0 && repeated_degree < degree {
            return self.factor_split_parts(polynomial, &repeated_part, factors);
        }

        let x = F2mPoly::x(self.m);
        let mut x_to_q = x.rem(polynomial, &self.irreducible);
        for _ in 0..self.m {
            x_to_q = x_to_q.square_mod(polynomial, &self.irreducible);
        }
        let rational_part = polynomial.gcd(&x_to_q.add(&x), &self.irreducible);
        let rational_degree = rational_part.degree().unwrap_or(0);
        if rational_degree == 0 {
            factors.push(polynomial.clone());
            return Ok(());
        }
        if rational_degree < degree {
            return self.factor_split_parts(polynomial, &rational_part, factors);
        }

        // Absolute traces Tr(c*x) separate distinct rational roots because
        // the finite-field trace pairing is nondegenerate.
        for bit in 0..self.m {
            let coefficient = F2mElement::from_bit_positions(&[bit], self.m);
            let mut conjugate = x
                .scalar_mul(&coefficient, &self.irreducible)
                .rem(polynomial, &self.irreducible);
            let mut trace = F2mPoly::zero(self.m);
            for _ in 0..self.m {
                trace = trace.add(&conjugate);
                conjugate = conjugate.square_mod(polynomial, &self.irreducible);
            }
            let split = polynomial.gcd(&trace, &self.irreducible);
            let split_degree = split.degree().unwrap_or(0);
            if split_degree > 0 && split_degree < degree {
                return self.factor_split_parts(polynomial, &split, factors);
            }
        }
        Err(CoverTransferError::CertificateFailure(
            "absolute-trace factorization did not split rational support",
        ))
    }

    fn factor_split_parts(
        &self,
        polynomial: &F2mPoly,
        factor: &F2mPoly,
        factors: &mut Vec<F2mPoly>,
    ) -> Result<(), CoverTransferError> {
        let (quotient, remainder) = polynomial.divrem(factor, &self.irreducible);
        if !remainder.is_zero() || quotient.is_zero() {
            return Err(CoverTransferError::CertificateFailure(
                "small-support factor division was not exact",
            ));
        }
        self.factor_small_support_recursive(factor, factors)?;
        self.factor_small_support_recursive(&quotient, factors)
    }

    fn pushforward_irreducible_support(
        &self,
        factor: &F2mPoly,
        source_v: &F2mPoly,
    ) -> Result<BinaryPoint, CoverTransferError> {
        let degree = factor
            .degree()
            .ok_or(CoverTransferError::CertificateFailure(
                "zero residue-field modulus",
            ))?;
        if degree == 1 {
            let u = factor.coeff(0);
            let v = source_v.eval(&u, &self.irreducible);
            return self.map_point(&BinaryCoverPoint::Affine { u, v });
        }
        if !(2..=3).contains(&degree) {
            return Err(CoverTransferError::CertificateFailure(
                "residue-field support degree exceeds three",
            ));
        }

        let t = F2mPoly::x(self.m).rem(factor, &self.irreducible);
        let t_squared = self.extension_mul(&t, &t, factor);
        let x = self.extension_mul(&t_squared, &t, factor);
        let v = source_v.rem(factor, &self.irreducible);
        let y = self
            .extension_mul(&t, &v, factor)
            .add(&F2mPoly::constant(self.d.clone()))
            .rem(factor, &self.irreducible);
        let point = ExtensionPoint::Affine { x, y };
        if !self.extension_target_is_on_curve(&point, factor) {
            return Err(CoverTransferError::CertificateFailure(
                "residue-field image is not on the elliptic target",
            ));
        }

        let mut trace = ExtensionPoint::Infinity;
        let mut conjugate = point.clone();
        for _ in 0..degree {
            trace = self.extension_target_add(&trace, &conjugate, factor)?;
            conjugate = self.extension_point_frobenius_q(&conjugate, factor);
        }
        if conjugate != point {
            return Err(CoverTransferError::CertificateFailure(
                "residue-field Frobenius orbit did not close",
            ));
        }
        if self.extension_point_frobenius_q(&trace, factor) != trace {
            return Err(CoverTransferError::CertificateFailure(
                "closed-point trace did not descend to the base field",
            ));
        }
        self.extension_point_to_base(&trace)
    }

    fn extension_mul(&self, left: &F2mPoly, right: &F2mPoly, modulus: &F2mPoly) -> F2mPoly {
        left.mul(right, &self.irreducible)
            .rem(modulus, &self.irreducible)
    }

    fn extension_inverse(
        &self,
        value: &F2mPoly,
        modulus: &F2mPoly,
    ) -> Result<F2mPoly, CoverTransferError> {
        let (gcd, coefficient, _) = value.ext_gcd(modulus, &self.irreducible);
        if gcd != F2mPoly::one(self.m) {
            return Err(CoverTransferError::CertificateFailure(
                "nonzero residue-field denominator is not invertible",
            ));
        }
        Ok(coefficient.rem(modulus, &self.irreducible))
    }

    fn extension_target_is_on_curve(&self, point: &ExtensionPoint, modulus: &F2mPoly) -> bool {
        let ExtensionPoint::Affine { x, y } = point else {
            return true;
        };
        let y_squared = self.extension_mul(y, y, modulus);
        let xy = self.extension_mul(x, y, modulus);
        let x_squared = self.extension_mul(x, x, modulus);
        let x_cubed = self.extension_mul(&x_squared, x, modulus);
        let a_x_squared =
            self.extension_mul(&F2mPoly::constant(self.a.clone()), &x_squared, modulus);
        let lhs = y_squared.add(&xy).rem(modulus, &self.irreducible);
        let rhs = x_cubed
            .add(&a_x_squared)
            .add(&F2mPoly::constant(self.b.clone()))
            .rem(modulus, &self.irreducible);
        lhs == rhs
    }

    fn extension_target_add(
        &self,
        left: &ExtensionPoint,
        right: &ExtensionPoint,
        modulus: &F2mPoly,
    ) -> Result<ExtensionPoint, CoverTransferError> {
        if !self.extension_target_is_on_curve(left, modulus)
            || !self.extension_target_is_on_curve(right, modulus)
        {
            return Err(CoverTransferError::CertificateFailure(
                "residue-field target addition received an off-curve point",
            ));
        }
        let result = match (left, right) {
            (ExtensionPoint::Infinity, point) | (point, ExtensionPoint::Infinity) => point.clone(),
            (ExtensionPoint::Affine { x: x1, y: y1 }, ExtensionPoint::Affine { x: x2, y: y2 }) => {
                if x1 == x2 {
                    if y1.add(y2) == *x1 || x1.is_zero() {
                        ExtensionPoint::Infinity
                    } else {
                        let inverse = self.extension_inverse(x1, modulus)?;
                        let lambda = x1.add(&self.extension_mul(y1, &inverse, modulus));
                        let x3 = self
                            .extension_mul(&lambda, &lambda, modulus)
                            .add(&lambda)
                            .add(&F2mPoly::constant(self.a.clone()))
                            .rem(modulus, &self.irreducible);
                        let lambda_plus_one = lambda.add(&F2mPoly::one(self.m));
                        let y3 = self
                            .extension_mul(x1, x1, modulus)
                            .add(&self.extension_mul(&lambda_plus_one, &x3, modulus))
                            .rem(modulus, &self.irreducible);
                        ExtensionPoint::Affine { x: x3, y: y3 }
                    }
                } else {
                    let denominator = x1.add(x2).rem(modulus, &self.irreducible);
                    let inverse = self.extension_inverse(&denominator, modulus)?;
                    let lambda = self.extension_mul(&y1.add(y2), &inverse, modulus);
                    let x3 = self
                        .extension_mul(&lambda, &lambda, modulus)
                        .add(&lambda)
                        .add(x1)
                        .add(x2)
                        .add(&F2mPoly::constant(self.a.clone()))
                        .rem(modulus, &self.irreducible);
                    let y3 = self
                        .extension_mul(&lambda, &x1.add(&x3), modulus)
                        .add(&x3)
                        .add(y1)
                        .rem(modulus, &self.irreducible);
                    ExtensionPoint::Affine { x: x3, y: y3 }
                }
            }
        };
        if !self.extension_target_is_on_curve(&result, modulus) {
            return Err(CoverTransferError::CertificateFailure(
                "residue-field target addition left the curve",
            ));
        }
        Ok(result)
    }

    fn extension_point_frobenius_q(
        &self,
        point: &ExtensionPoint,
        modulus: &F2mPoly,
    ) -> ExtensionPoint {
        let frobenius = |value: &F2mPoly| {
            let mut result = value.clone();
            for _ in 0..self.m {
                result = result.square_mod(modulus, &self.irreducible);
            }
            result
        };
        match point {
            ExtensionPoint::Infinity => ExtensionPoint::Infinity,
            ExtensionPoint::Affine { x, y } => ExtensionPoint::Affine {
                x: frobenius(x),
                y: frobenius(y),
            },
        }
    }

    fn extension_point_to_base(
        &self,
        point: &ExtensionPoint,
    ) -> Result<BinaryPoint, CoverTransferError> {
        let base_coordinate = |value: &F2mPoly| match value.degree() {
            None => Ok(F2mElement::zero(self.m)),
            Some(0) => Ok(value.coeff(0)),
            Some(_) => Err(CoverTransferError::CertificateFailure(
                "Frobenius-fixed residue-field coordinate is not constant",
            )),
        };
        let result = match point {
            ExtensionPoint::Infinity => BinaryPoint::Infinity,
            ExtensionPoint::Affine { x, y } => BinaryPoint::Affine {
                x: base_coordinate(x)?,
                y: base_coordinate(y)?,
            },
        };
        if !self.target_is_on_curve(&result) {
            return Err(CoverTransferError::CertificateFailure(
                "descended closed-point trace is not on the target",
            ));
        }
        Ok(result)
    }

    fn is_fixed_f8_norm_fixture(&self) -> bool {
        self.m == 3
            && self.irreducible.degree == 3
            && self.irreducible.low_terms.as_slice() == [0u32, 1u32]
            && self.a == F2mElement::one(3)
            && self.b == F2mElement::from_biguint(&BigUint::from(3u32), 3)
            && self.d == F2mElement::from_biguint(&BigUint::from(7u32), 3)
    }

    fn build_fixed_f8_norm_table(&self) -> Result<FixedF8NormTable, CoverTransferError> {
        if !self.is_fixed_f8_norm_fixture() {
            return Err(CoverTransferError::Unsupported(
                UnsupportedCoverOperation::ArbitraryJacobianPushforward,
            ));
        }
        self.verify_certificate()?;

        let a_u = F2mElement::from_biguint(&BigUint::from(2u32), 3);
        let a_v = F2mElement::from_biguint(&BigUint::from(3u32), 3);
        let b_u = F2mElement::from_biguint(&BigUint::from(3u32), 3);
        let b_v = F2mElement::one(3);
        let a = MumfordDivisor::try_from_point(&self.source, &a_u, &a_v)?;
        let b = MumfordDivisor::try_from_point(&self.source, &b_u, &b_v)?;
        let a_point = BinaryCoverPoint::Affine { u: a_u, v: a_v };
        let b_point = BinaryCoverPoint::Affine { u: b_u, v: b_v };
        let image_a = self.pushforward_rational_point_divisor(&a_point)?;
        let image_b = self.pushforward_rational_point_divisor(&b_point)?;
        let expected_image_a = BinaryPoint::Affine {
            x: F2mElement::from_biguint(&BigUint::from(3u32), 3),
            y: F2mElement::one(3),
        };
        let expected_image_b = BinaryPoint::Affine {
            x: F2mElement::from_biguint(&BigUint::from(4u32), 3),
            y: F2mElement::from_biguint(&BigUint::from(4u32), 3),
        };

        if !a
            .try_scalar_mul(&BigUint::from(27u32), &self.source)?
            .is_identity()
            || a.try_scalar_mul(&BigUint::from(9u32), &self.source)?
                .is_identity()
        {
            return Err(CoverTransferError::CertificateFailure(
                "fixed F8 norm generator A does not have order 27",
            ));
        }
        if !b
            .try_scalar_mul(&BigUint::from(54u32), &self.source)?
            .is_identity()
            || b.try_scalar_mul(&BigUint::from(27u32), &self.source)?
                .is_identity()
            || b.try_scalar_mul(&BigUint::from(18u32), &self.source)?
                .is_identity()
        {
            return Err(CoverTransferError::CertificateFailure(
                "fixed F8 norm generator B does not have order 54",
            ));
        }
        if a.try_scalar_mul(&BigUint::from(9u32), &self.source)?
            != b.try_scalar_mul(&BigUint::from(18u32), &self.source)?
        {
            return Err(CoverTransferError::CertificateFailure(
                "fixed F8 norm generators do not satisfy 9A=18B",
            ));
        }
        if image_a != expected_image_a
            || image_b != expected_image_b
            || image_a != self.target_scalar_mul_small(&image_b, 2)?
            || self.target_scalar_mul_small(&image_b, 6)? != BinaryPoint::Infinity
            || self.target_scalar_mul_small(&image_b, 3)? == BinaryPoint::Infinity
            || self.target_scalar_mul_small(&image_b, 2)? == BinaryPoint::Infinity
        {
            return Err(CoverTransferError::CertificateFailure(
                "fixed F8 point images do not satisfy phi(A)=2Q with Q of order six",
            ));
        }

        let a_multiples = self.fixed_f8_jacobian_multiples(&a, 9)?;
        let b_multiples = self.fixed_f8_jacobian_multiples(&b, 54)?;
        let image_a_multiples = self.fixed_f8_target_multiples(&image_a, 9)?;
        let image_b_multiples = self.fixed_f8_target_multiples(&image_b, 54)?;
        let mut images = HashMap::with_capacity(486);
        for (a_multiple, image_a_multiple) in a_multiples.iter().zip(image_a_multiples.iter()) {
            for (b_multiple, image_b_multiple) in b_multiples.iter().zip(image_b_multiples.iter()) {
                let divisor = a_multiple.try_add(b_multiple, &self.source)?;
                let image = self.target_add(image_a_multiple, image_b_multiple)?;
                let residue_field_image = self.pushforward_via_residue_fields(&divisor)?;
                if residue_field_image != image {
                    return Err(CoverTransferError::CertificateFailure(
                        "residue-field norm disagrees with the independent fixed F8 presentation",
                    ));
                }
                let key = fixed_f8_divisor_key(&divisor);
                if let Some(previous) = images.insert(key, image.clone()) {
                    if previous != image {
                        return Err(CoverTransferError::CertificateFailure(
                            "fixed F8 norm presentation assigns inconsistent images",
                        ));
                    }
                }
            }
        }
        if images.len() != 486 {
            return Err(CoverTransferError::CertificateFailure(
                "fixed F8 norm presentation does not contain 486 unique classes",
            ));
        }
        Ok(FixedF8NormTable { images })
    }

    fn fixed_f8_jacobian_multiples(
        &self,
        base: &MumfordDivisor,
        count: usize,
    ) -> Result<Vec<MumfordDivisor>, CoverTransferError> {
        let mut multiples = Vec::with_capacity(count);
        let mut current = MumfordDivisor::identity(self.m);
        for _ in 0..count {
            multiples.push(current.clone());
            current = current.try_add(base, &self.source)?;
        }
        Ok(multiples)
    }

    fn fixed_f8_target_multiples(
        &self,
        base: &BinaryPoint,
        count: usize,
    ) -> Result<Vec<BinaryPoint>, CoverTransferError> {
        let mut multiples = Vec::with_capacity(count);
        let mut current = BinaryPoint::Infinity;
        for _ in 0..count {
            multiples.push(current.clone());
            current = self.target_add(&current, base)?;
        }
        Ok(multiples)
    }

    fn target_scalar_mul_small(
        &self,
        point: &BinaryPoint,
        scalar: u32,
    ) -> Result<BinaryPoint, CoverTransferError> {
        if !self.target_is_on_curve(point) {
            return Err(CoverTransferError::PointNotOnTarget);
        }
        let mut acc = BinaryPoint::Infinity;
        let mut base = point.clone();
        let mut k = scalar;
        while k != 0 {
            if k & 1 == 1 {
                acc = self.target_add(&acc, &base)?;
            }
            k >>= 1;
            if k != 0 {
                base = self.target_add(&base, &base)?;
            }
        }
        Ok(acc)
    }

    fn target_add(
        &self,
        left: &BinaryPoint,
        right: &BinaryPoint,
    ) -> Result<BinaryPoint, CoverTransferError> {
        if !self.target_is_on_curve(left) || !self.target_is_on_curve(right) {
            return Err(CoverTransferError::PointNotOnTarget);
        }
        let result = match (left, right) {
            (BinaryPoint::Infinity, p) | (p, BinaryPoint::Infinity) => p.clone(),
            (BinaryPoint::Affine { x: x1, y: y1 }, BinaryPoint::Affine { x: x2, y: y2 }) => {
                if x1 == x2 {
                    if y1.add(y2) == *x1 || x1.is_zero() {
                        BinaryPoint::Infinity
                    } else {
                        let inv = x1.flt_inverse(&self.irreducible).ok_or(
                            CoverTransferError::CertificateFailure(
                                "doubling denominator is not invertible",
                            ),
                        )?;
                        let lambda = x1.add(&y1.mul(&inv, &self.irreducible));
                        let x3 = lambda.square(&self.irreducible).add(&lambda).add(&self.a);
                        let y3 = x1.square(&self.irreducible).add(
                            &lambda
                                .add(&F2mElement::one(self.m))
                                .mul(&x3, &self.irreducible),
                        );
                        BinaryPoint::Affine { x: x3, y: y3 }
                    }
                } else {
                    let denominator = x1.add(x2);
                    let inv = denominator.flt_inverse(&self.irreducible).ok_or(
                        CoverTransferError::CertificateFailure(
                            "addition denominator is not invertible",
                        ),
                    )?;
                    let lambda = y1.add(y2).mul(&inv, &self.irreducible);
                    let x3 = lambda
                        .square(&self.irreducible)
                        .add(&lambda)
                        .add(x1)
                        .add(x2)
                        .add(&self.a);
                    let y3 = lambda.mul(&x1.add(&x3), &self.irreducible).add(&x3).add(y1);
                    BinaryPoint::Affine { x: x3, y: y3 }
                }
            }
        };
        if !self.target_is_on_curve(&result) {
            return Err(CoverTransferError::CertificateFailure(
                "target group operation left the curve",
            ));
        }
        Ok(result)
    }
}

fn formal_derivative_over_base(polynomial: &F2mPoly) -> F2mPoly {
    let mut coefficients =
        vec![F2mElement::zero(polynomial.m); polynomial.coeffs.len().saturating_sub(1)];
    for degree in (1..polynomial.coeffs.len()).step_by(2) {
        coefficients[degree - 1] = polynomial.coeffs[degree].clone();
    }
    F2mPoly::from_coeffs(coefficients, polynomial.m)
}

fn fixed_f8_divisor_key(divisor: &MumfordDivisor) -> FixedF8DivisorKey {
    (
        divisor
            .u
            .coeffs
            .iter()
            .map(F2mElement::to_biguint)
            .collect(),
        divisor
            .v
            .coeffs
            .iter()
            .map(F2mElement::to_biguint)
            .collect(),
    )
}

fn check_width(
    object: &'static str,
    value: &F2mElement,
    expected: u32,
) -> Result<(), CoverTransferError> {
    let actual = value.m_value();
    if actual != expected {
        return Err(CoverTransferError::FieldWidthMismatch {
            object,
            expected,
            actual,
        });
    }
    Ok(())
}

fn validate_field(m: u32, polynomial: &IrreduciblePoly) -> Result<(), CoverTransferError> {
    if !(1..=4096).contains(&m) {
        return Err(CoverTransferError::InvalidField(
            "degree must lie in 1..=4096",
        ));
    }
    if polynomial.degree != m {
        return Err(CoverTransferError::InvalidField(
            "modulus degree does not equal field width",
        ));
    }
    if polynomial.low_terms.first() != Some(&0) {
        return Err(CoverTransferError::InvalidField(
            "modulus must have nonzero constant term and canonical term order",
        ));
    }
    if polynomial.low_terms.iter().any(|&term| term >= m)
        || polynomial.low_terms.windows(2).any(|w| w[0] >= w[1])
    {
        return Err(CoverTransferError::InvalidField(
            "modulus low terms must be unique, increasing, and below m",
        ));
    }
    if !rabin_irreducible(polynomial) {
        return Err(CoverTransferError::InvalidField(
            "modulus is reducible over GF(2)",
        ));
    }
    Ok(())
}

fn modulus_bits(polynomial: &IrreduciblePoly) -> BigUint {
    let mut modulus = BigUint::one() << polynomial.degree as usize;
    for &term in &polynomial.low_terms {
        modulus |= BigUint::one() << term as usize;
    }
    modulus
}

fn bit_remainder(mut value: BigUint, modulus: &BigUint) -> BigUint {
    while !value.is_zero() && value.bits() >= modulus.bits() {
        let shift = (value.bits() - modulus.bits()) as usize;
        value ^= modulus << shift;
    }
    value
}

fn bit_gcd(mut left: BigUint, mut right: BigUint) -> BigUint {
    while !right.is_zero() {
        let remainder = bit_remainder(left, &right);
        left = right;
        right = remainder;
    }
    left
}

/// Rabin's exact irreducibility criterion over GF(2).
fn rabin_irreducible(polynomial: &IrreduciblePoly) -> bool {
    let m = polynomial.degree;
    let modulus = modulus_bits(polynomial);
    let mut remaining = m;
    let mut checkpoints = HashSet::new();
    let mut prime = 2u32;
    while prime * prime <= remaining {
        if remaining.is_multiple_of(prime) {
            checkpoints.insert(m / prime);
            while remaining.is_multiple_of(prime) {
                remaining /= prime;
            }
        }
        prime += 1;
    }
    if remaining > 1 {
        checkpoints.insert(m / remaining);
    }

    let z = bit_remainder(BigUint::from(2u32), &modulus);
    let mut frobenius = F2mElement::from_biguint(&z, m);
    for i in 1..=m {
        frobenius = frobenius.square(polynomial);
        if checkpoints.contains(&i)
            && bit_gcd(frobenius.to_biguint() ^ &z, modulus.clone()) != BigUint::one()
        {
            return false;
        }
    }
    frobenius.to_biguint() == z
}

fn verify_substitution(
    source: &HyperellipticCurve,
    a: &F2mElement,
    b: &F2mElement,
    d: &F2mElement,
) -> bool {
    let m = source.m;
    let irr = &source.irr;
    let t = F2mPoly::x(m);
    let t2 = t.mul(&t, irr);
    let x = t2.mul(&t, irr);
    let x2 = x.mul(&x, irr);
    let x3 = x2.mul(&x, irr);
    let aa = t2;

    // y=t*v+d.  Reducing y^2+x*y modulo v^2=h*v+f leaves a coefficient
    // of v and a constant coefficient, both of which must match the target
    // right-hand side.
    let linear = aa.mul(&source.h, irr).add(&x.mul(&t, irr));
    let constant = aa
        .mul(&source.f, irr)
        .add(&F2mPoly::constant(d.square(irr)))
        .add(&x.scalar_mul(d, irr))
        .add(&x3)
        .add(&x2.scalar_mul(a, irr))
        .add(&F2mPoly::constant(b.clone()));
    linear.is_zero() && constant.is_zero()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::binary_ecc::{hcdlp_bsgs_counted, hcdlp_pollard_rho_counted};

    fn f8_modulus() -> IrreduciblePoly {
        // z^3 + z + 1.
        IrreduciblePoly {
            degree: 3,
            low_terms: vec![0, 1],
        }
    }

    fn elt(value: u32) -> F2mElement {
        F2mElement::from_biguint(&BigUint::from(value), 3)
    }

    fn cover(a: u32, b: u32) -> OrdinaryBinaryCover {
        OrdinaryBinaryCover::new(3, f8_modulus(), elt(a), elt(b)).unwrap()
    }

    fn point_one_zero(m: u32) -> BinaryPoint {
        BinaryPoint::Affine {
            x: F2mElement::one(m),
            y: F2mElement::zero(m),
        }
    }

    fn coefficients_from_code(mut code: usize, length: usize) -> Vec<F2mElement> {
        (0..length)
            .map(|_| {
                let coefficient = elt((code % 8) as u32);
                code /= 8;
                coefficient
            })
            .collect()
    }

    fn all_fixed_f8_reduced_divisors(curve: &HyperellipticCurve) -> Vec<MumfordDivisor> {
        let mut divisors = vec![MumfordDivisor::identity(3)];
        for u_degree in 1..=3usize {
            let coefficient_vectors = 8usize.pow(u_degree as u32);
            for u_code in 0..coefficient_vectors {
                let mut u_coefficients = coefficients_from_code(u_code, u_degree);
                u_coefficients.push(F2mElement::one(3));
                let u = F2mPoly::from_coeffs(u_coefficients, 3);
                for v_code in 0..coefficient_vectors {
                    let v = F2mPoly::from_coeffs(coefficients_from_code(v_code, u_degree), 3);
                    // These loops already enforce monic U and
                    // deg(V)<deg(U)<=3.  Check the remaining Mumford
                    // invariant directly so exhaustive enumeration does not
                    // revalidate the fixed field for all 266,304 candidates.
                    let equation = v
                        .mul(&v, &curve.irr)
                        .add(&curve.h.mul(&v, &curve.irr))
                        .add(&curve.f);
                    let (_quotient, remainder) = equation.divrem(&u, &curve.irr);
                    if remainder.is_zero() {
                        divisors.push(MumfordDivisor { u: u.clone(), v });
                    }
                }
            }
        }
        divisors
    }

    #[test]
    fn closed_point_pullback_certificate_detects_odd_and_even_fiber_splitting() {
        let odd = cover(0, 1);
        let odd_certificate = odd
            .pullback_closed_point_certificate(&point_one_zero(3))
            .unwrap();
        let mut odd_degrees: Vec<_> = odd_certificate
            .components
            .iter()
            .map(|component| component.degree)
            .collect();
        odd_degrees.sort_unstable();
        assert_eq!(odd_degrees, vec![1, 2]);
        assert_eq!(odd_certificate.reduced_support_degree, 3);
        assert!(odd_certificate.every_component_is_degree_times_input);
        assert!(odd_certificate.total_matches_three_times_input);

        let even = OrdinaryBinaryCover::new(
            2,
            IrreduciblePoly {
                degree: 2,
                low_terms: vec![0, 1],
            },
            F2mElement::zero(2),
            F2mElement::one(2),
        )
        .unwrap();
        let even_certificate = even
            .pullback_closed_point_certificate(&point_one_zero(2))
            .unwrap();
        let mut even_degrees: Vec<_> = even_certificate
            .components
            .iter()
            .map(|component| component.degree)
            .collect();
        even_degrees.sort_unstable();
        assert_eq!(even_degrees, vec![1, 1, 1]);
        assert_eq!(even_certificate.reduced_support_degree, 3);
        assert!(even_certificate.every_component_is_degree_times_input);
        assert!(even_certificate.total_matches_three_times_input);
    }

    #[test]
    fn closed_point_pullback_certificate_keeps_ramification_separate() {
        let c = cover(0, 1);
        let ramified = BinaryPoint::Affine {
            x: F2mElement::zero(3),
            y: F2mElement::one(3),
        };
        let certificate = c.pullback_closed_point_certificate(&ramified).unwrap();
        assert_eq!(certificate.reduced_support_degree, 1);
        assert_eq!(certificate.components.len(), 1);
        assert!(matches!(
            certificate.fiber_kind,
            PullbackFiberKind::ExceptionalTwoTorsionRamified {
                ramification_index: 3
            }
        ));
        assert!(certificate.every_component_is_degree_times_input);
        assert!(certificate.total_matches_three_times_input);
    }

    fn target_point(x: u32, y: u32) -> BinaryPoint {
        BinaryPoint::Affine {
            x: elt(x),
            y: elt(y),
        }
    }

    fn checked_divisor(curve: &HyperellipticCurve, u: &[u32], v: &[u32]) -> MumfordDivisor {
        MumfordDivisor::try_new(
            curve,
            F2mPoly::from_coeffs(u.iter().copied().map(elt).collect(), 3),
            F2mPoly::from_coeffs(v.iter().copied().map(elt).collect(), 3),
        )
        .unwrap()
    }

    #[test]
    fn construction_checks_geometry_and_rejects_invalid_inputs() {
        let c = cover(1, 1);
        let cert = c.certificate();
        assert_eq!(cert.construction, "binary_cubic_pullback_v1");
        assert!(cert.modulus_irreducible);
        assert!(cert.target_nonsingular);
        assert!(cert.d_square_equals_b);
        assert!(cert.defining_equation_substitution);
        assert!(cert.source_model_validated);
        assert_eq!(cert.source_genus, 3);
        assert_eq!(cert.map_degree, 3);
        assert!(cert.map_separable);
        assert!(cert.unique_rational_infinity);
        assert!(cert.affine_smooth_at_u_zero);
        assert!(cert.infinity_smooth);
        assert_eq!(cert.artin_schreier_pole_orders, [3, 3]);
        assert_eq!(cert.riemann_hurwitz_ramification_total, 4);
        assert_eq!(c.field_degree(), 3);
        assert_eq!(c.irreducible_polynomial().degree, 3);
        assert_eq!(c.target_a(), &elt(1));
        assert_eq!(c.target_b(), &elt(1));
        assert_eq!(c.square_root_b(), &elt(1));
        c.verify_certificate().unwrap();

        assert_eq!(
            OrdinaryBinaryCover::new(3, f8_modulus(), elt(0), elt(0)).unwrap_err(),
            CoverTransferError::SingularTarget
        );
        let reducible = IrreduciblePoly {
            degree: 3,
            low_terms: vec![0, 1, 2], // z^3+z^2+z+1=(z+1)^3
        };
        assert!(matches!(
            OrdinaryBinaryCover::new(3, reducible, elt(0), elt(1)),
            Err(CoverTransferError::InvalidField(_))
        ));
        assert!(matches!(
            OrdinaryBinaryCover::new(3, f8_modulus(), F2mElement::one(4), elt(1)),
            Err(CoverTransferError::FieldWidthMismatch { object: "a", .. })
        ));

        let off_target = BinaryPoint::Affine {
            x: elt(0),
            y: elt(0),
        };
        assert_eq!(
            c.pullback_point_class(&off_target).unwrap_err(),
            CoverTransferError::PointNotOnTarget
        );
        let off_source = BinaryCoverPoint::Affine {
            u: elt(0),
            v: elt(1),
        };
        assert_eq!(
            c.map_point(&off_source).unwrap_err(),
            CoverTransferError::PointNotOnCover
        );
    }

    #[test]
    fn infinity_and_exceptional_two_torsion_are_explicit() {
        let c = cover(1, 1);
        assert_eq!(
            c.map_point(&BinaryCoverPoint::Infinity).unwrap(),
            BinaryPoint::Infinity
        );
        let infinity = c
            .pull_push_composition_certificate(&BinaryPoint::Infinity)
            .unwrap();
        assert!(infinity.pullback.is_identity());
        assert_eq!(
            infinity.fiber_kind,
            PullbackFiberKind::InfinityRamified {
                ramification_index: 3
            }
        );
        assert!(infinity.identity_holds);

        let p0 = BinaryCoverPoint::Affine {
            u: elt(0),
            v: elt(0),
        };
        let t = BinaryPoint::Affine {
            x: elt(0),
            y: c.d.clone(),
        };
        assert!(c.source_is_on_curve(&p0));
        assert_eq!(c.map_point(&p0).unwrap(), t);
        let pullback = c.pullback_point_class(&t).unwrap();
        assert_eq!(pullback.u, F2mPoly::x(3));
        assert!(pullback.v.is_zero());
        assert!(pullback.is_reduced(c.source_curve()));
        assert!(pullback.try_double(c.source_curve()).unwrap().is_identity());
        let cert = c.pull_push_composition_certificate(&t).unwrap();
        assert_eq!(
            cert.fiber_kind,
            PullbackFiberKind::ExceptionalTwoTorsionRamified {
                ramification_index: 3
            }
        );
        assert_eq!(cert.formal_pushforward, t);
        assert!(cert.identity_holds);
    }

    #[test]
    fn exhaustive_f8_models_points_maps_and_compositions() {
        let mut target_points = 0usize;
        let mut source_points = 0usize;
        let mut generic_pullbacks = 0usize;
        for a in 0..8 {
            for b in 1..8 {
                let c = cover(a, b);
                for x in 0..8 {
                    for y in 0..8 {
                        let point = BinaryPoint::Affine {
                            x: elt(x),
                            y: elt(y),
                        };
                        if !c.target_is_on_curve(&point) {
                            continue;
                        }
                        target_points += 1;
                        let cert = c.pull_push_composition_certificate(&point).unwrap();
                        assert!(cert.pullback.is_reduced(c.source_curve()));
                        assert!(cert.identity_holds);
                        if x != 0 {
                            assert_eq!(cert.pullback.u.degree(), Some(3));
                            assert!(matches!(
                                cert.fiber_kind,
                                PullbackFiberKind::GenericSeparable {
                                    geometric_degree: 3
                                }
                            ));
                            generic_pullbacks += 1;
                        }
                    }
                }
                let infinity = c
                    .pull_push_composition_certificate(&BinaryPoint::Infinity)
                    .unwrap();
                assert!(infinity.identity_holds);

                for u in 0..8 {
                    for v in 0..8 {
                        let point = BinaryCoverPoint::Affine {
                            u: elt(u),
                            v: elt(v),
                        };
                        if !c.source_is_on_curve(&point) {
                            continue;
                        }
                        source_points += 1;
                        let image = c.pushforward_rational_point_divisor(&point).unwrap();
                        assert!(c.target_is_on_curve(&image));
                        if u != 0 {
                            let pullback = c.pullback_point_class(&image).unwrap();
                            assert!(pullback.u.eval(&elt(u), &c.irreducible).is_zero());
                            assert_eq!(pullback.v.eval(&elt(u), &c.irreducible), elt(v));
                        }
                    }
                }
            }
        }
        assert!(target_points > 0);
        assert!(source_points > 0);
        assert!(generic_pullbacks > 0);
    }

    #[test]
    fn subgroup_status_general_pushforward_and_projector() {
        let c = cover(0, 1);
        assert_eq!(
            c.subgroup_transfer_status(&BigUint::from(7u32)).unwrap(),
            SubgroupTransferStatus::InjectiveIfExactSubgroupOrder {
                order: BigUint::from(7u32),
                degree_inverse_mod_order: BigUint::from(5u32),
            }
        );
        assert_eq!(
            c.subgroup_transfer_status(&BigUint::from(21u32)).unwrap(),
            SubgroupTransferStatus::KernelIntersectionUnresolved {
                order: BigUint::from(21u32),
                common_factor: 3,
            }
        );
        assert_eq!(
            c.subgroup_transfer_status(&BigUint::zero()).unwrap_err(),
            CoverTransferError::InvalidSubgroupOrder
        );
        let id = MumfordDivisor::identity(3);
        assert_eq!(
            c.pushforward_arbitrary_jacobian_class(&id).unwrap(),
            BinaryPoint::Infinity
        );

        // Exact EC1/ICV1 catalog fixture:
        // EC1N7Ce0hb6d297a2ca08 on z^7+z+1, subgroup order 29,
        // generator (0x26,0x5).  Because 29 is prime, [29]G=O and G!=O
        // certify the order.  The checked pullback has the same order, and
        // multiplying its pushforward [3]G by 3^{-1}=10 recovers G.
        let catalog = OrdinaryBinaryCover::new(
            7,
            IrreduciblePoly {
                degree: 7,
                low_terms: vec![0, 1],
            },
            F2mElement::zero(7),
            F2mElement::one(7),
        )
        .unwrap();
        let generator = BinaryPoint::Affine {
            x: F2mElement::from_biguint(&BigUint::from(0x26u32), 7),
            y: F2mElement::from_biguint(&BigUint::from(0x05u32), 7),
        };
        assert!(catalog.target_is_on_curve(&generator));
        assert_ne!(generator, BinaryPoint::Infinity);
        assert_eq!(
            catalog.target_scalar_mul_small(&generator, 29).unwrap(),
            BinaryPoint::Infinity
        );
        assert_eq!(
            catalog
                .subgroup_transfer_status(&BigUint::from(29u32))
                .unwrap(),
            SubgroupTransferStatus::InjectiveIfExactSubgroupOrder {
                order: BigUint::from(29u32),
                degree_inverse_mod_order: BigUint::from(10u32),
            }
        );
        let image = catalog.pullback_point_class(&generator).unwrap();
        assert!(!image.is_identity());
        assert!(image
            .try_scalar_mul(&BigUint::from(29u32), catalog.source_curve())
            .unwrap()
            .is_identity());
        let composition = catalog
            .pull_push_composition_certificate(&generator)
            .unwrap();
        assert_eq!(
            catalog
                .target_scalar_mul_small(&composition.formal_pushforward, 10)
                .unwrap(),
            generator
        );
        let endomorphism = catalog.image_endomorphism_certificate(&image).unwrap();
        assert!(endomorphism.quadratic_identity_holds);
        assert_eq!(endomorphism.pushforward, composition.formal_pushforward);
        assert!(!endomorphism.pushforward_kernel_member);
        let projector = catalog
            .torsion_projector_certificate(&image, &BigUint::from(29u32))
            .unwrap();
        assert_eq!(projector.degree_inverse_mod_order, BigUint::from(10u32));
        assert_eq!(projector.normalized_projection, image);
        assert!(projector.complementary_component.is_identity());
        assert!(projector.projection_is_idempotent);
        assert!(projector.projected_component_is_in_image);
        assert!(projector.complementary_component_is_in_pushforward_kernel);
        assert!(projector.input_is_in_image);
        assert!(!projector.input_is_in_pushforward_kernel);
        assert!(projector.decomposition_holds);
        assert_eq!(
            catalog.torsion_projector_certificate(&image, &BigUint::from(2u32)),
            Err(CoverTransferError::DivisorNotInDeclaredTorsion)
        );
        assert_eq!(
            catalog
                .torsion_projector_certificate(&MumfordDivisor::identity(7), &BigUint::from(3u32),),
            Err(CoverTransferError::ProjectorOrderNotCoprime { common_factor: 3 })
        );

        // Both named destination solvers operate on the pulled-back
        // Jacobian image, receive no planted logarithm, and verify their
        // recovered scalar in that image subgroup.
        let scalar = BigUint::from(13u32);
        let target = catalog.target_scalar_mul_small(&generator, 13).unwrap();
        let target_image = catalog.pullback_point_class(&target).unwrap();
        assert_eq!(
            image
                .try_scalar_mul(&scalar, catalog.source_curve())
                .unwrap(),
            target_image
        );
        let bsgs = hcdlp_bsgs_counted(
            &image,
            &target_image,
            &BigUint::from(29u32),
            catalog.source_curve(),
        )
        .unwrap();
        assert_eq!(bsgs.recovered, Some(scalar.clone()));
        assert!(!bsgs.exhausted);
        assert!(bsgs.table_inserts > 0);

        let rho = hcdlp_pollard_rho_counted(
            &image,
            &target_image,
            &BigUint::from(29u32),
            catalog.source_curve(),
            0x83_03,
            1_024,
            64,
        )
        .unwrap();
        assert_eq!(rho.recovered, Some(scalar));
        assert!(!rho.exhausted);
        assert!(rho.walk_steps > 0);
    }

    #[test]
    fn n83_prym_point_counts_and_order_factors_are_coprime_to_r() {
        fn counts(degree: u32, low_terms: Vec<u32>) -> (u64, u64) {
            let cover = OrdinaryBinaryCover::new(
                degree,
                IrreduciblePoly { degree, low_terms },
                F2mElement::zero(degree),
                F2mElement::one(degree),
            )
            .unwrap();
            let mut elliptic = 1u64;
            let mut genus_three = 1u64;
            for x in 0..(1u32 << degree) {
                for y in 0..(1u32 << degree) {
                    let x = F2mElement::from_biguint(&BigUint::from(x), degree);
                    let y = F2mElement::from_biguint(&BigUint::from(y), degree);
                    if cover.target_is_on_curve(&BinaryPoint::Affine {
                        x: x.clone(),
                        y: y.clone(),
                    }) {
                        elliptic += 1;
                    }
                    if cover.source_is_on_curve(&BinaryCoverPoint::Affine { u: x, v: y }) {
                        genus_three += 1;
                    }
                }
            }
            (elliptic, genus_three)
        }

        fn gcd(mut left: BigUint, mut right: BigUint) -> BigUint {
            while !right.is_zero() {
                let remainder = &left % &right;
                left = right;
                right = remainder;
            }
            left
        }

        assert_eq!(counts(1, vec![0]), (4, 4));
        assert_eq!(counts(2, vec![0, 1]), (8, 8));
        assert_eq!(counts(3, vec![0, 1]), (4, 4));

        let q = BigUint::one() << 83usize;
        let trace = BigUint::one() << 42usize;
        let r = BigUint::parse_bytes(b"2417851639230796216685689", 10).unwrap();
        let factor_plus_order = &q + 1u32 - &trace;
        let factor_minus_order = &q + 1u32 + &trace;
        let prym_order = &q * &q + 1u32;
        assert_eq!(&factor_plus_order * &factor_minus_order, prym_order);
        assert_eq!(gcd(r.clone(), factor_plus_order), BigUint::one());
        assert_eq!(gcd(r.clone(), factor_minus_order), BigUint::one());
        assert_eq!(gcd(r.clone(), prym_order), BigUint::one());
        assert_eq!(&q + 1u32 + BigUint::from(6_151_469_093_347u64), r * 4u32);
    }

    #[test]
    fn n83_general_norm_and_r_torsion_projector_replay() {
        let cover = OrdinaryBinaryCover::new(
            83,
            IrreduciblePoly {
                degree: 83,
                low_terms: vec![0, 1, 2, 45],
            },
            F2mElement::zero(83),
            F2mElement::one(83),
        )
        .unwrap();
        let generator = BinaryPoint::Affine {
            x: F2mElement::from_hex("477f77103dfad59850800", 83),
            y: F2mElement::from_hex("2fa5e737d542c4e4fd5c3", 83),
        };
        let order = BigUint::parse_bytes(b"2417851639230796216685689", 10).unwrap();
        let image = cover.pullback_point_class(&generator).unwrap();
        assert!(image
            .try_scalar_mul(&order, cover.source_curve())
            .unwrap()
            .is_identity());

        let general_pushforward = cover.pushforward_arbitrary_jacobian_class(&image).unwrap();
        let typed = cover.pull_push_composition_certificate(&generator).unwrap();
        assert_eq!(general_pushforward, typed.formal_pushforward);
        assert!(typed.identity_holds);

        let endomorphism = cover.image_endomorphism_certificate(&image).unwrap();
        assert!(endomorphism.quadratic_identity_holds);
        let projector = cover.torsion_projector_certificate(&image, &order).unwrap();
        assert!(projector.projection_is_idempotent);
        assert!(projector.projected_component_is_in_image);
        assert!(projector.complementary_component_is_in_pushforward_kernel);
        assert!(projector.input_is_in_image);
        assert!(!projector.input_is_in_pushforward_kernel);
        assert!(projector.complementary_component.is_identity());
        assert!(projector.decomposition_holds);
    }

    #[test]
    fn fixed_f8_arbitrary_pushforward_is_complete_and_homomorphic() {
        let c = cover(1, 3);
        let divisors = all_fixed_f8_reduced_divisors(c.source_curve());
        let divisor_keys: HashSet<_> = divisors.iter().map(fixed_f8_divisor_key).collect();
        let mut degree_counts = [0usize; 4];
        for divisor in &divisors {
            divisor.validate(c.source_curve()).unwrap();
            degree_counts[divisor.u.degree().unwrap()] += 1;
        }
        assert_eq!(degree_counts, [1, 5, 56, 424]);
        assert_eq!(divisors.len(), 486);
        assert_eq!(divisor_keys.len(), 486);

        let identity = MumfordDivisor::identity(3);
        assert_eq!(
            c.pushforward_arbitrary_jacobian_class(&identity).unwrap(),
            BinaryPoint::Infinity
        );
        let table = FIXED_F8_NORM_TABLE.get().unwrap().as_ref().unwrap();
        assert_eq!(table.images.len(), 486);
        assert_eq!(
            table.images.keys().cloned().collect::<HashSet<_>>(),
            divisor_keys
        );

        let q = target_point(4, 4);
        let target_group = c.fixed_f8_target_multiples(&q, 6).unwrap();
        assert_eq!(target_group.len(), 6);
        assert_eq!(
            c.target_scalar_mul_small(&q, 6).unwrap(),
            BinaryPoint::Infinity
        );
        let mut fiber_sizes = [0usize; 6];
        let mut images = Vec::with_capacity(divisors.len());
        let mut kernel_size = 0usize;
        for divisor in &divisors {
            let image = c.pushforward_arbitrary_jacobian_class(divisor).unwrap();
            assert!(c.target_is_on_curve(&image));
            let image_index = target_group
                .iter()
                .position(|candidate| candidate == &image)
                .expect("fixed-fixture norm image lies in the six-element target");
            fiber_sizes[image_index] += 1;

            let inverse = divisor.try_neg(c.source_curve()).unwrap();
            let inverse_image = c.pushforward_arbitrary_jacobian_class(&inverse).unwrap();
            assert_eq!(
                c.target_add(&image, &inverse_image).unwrap(),
                BinaryPoint::Infinity
            );
            let endomorphism = c.image_endomorphism_certificate(divisor).unwrap();
            assert!(endomorphism.quadratic_identity_holds);
            if endomorphism.pushforward_kernel_member {
                kernel_size += 1;
            }
            images.push(image);
        }
        assert_eq!(fiber_sizes, [81; 6]);
        assert_eq!(kernel_size, 81);

        for (left_index, left) in divisors.iter().enumerate() {
            for (right_index, right) in divisors.iter().enumerate() {
                let sum = left.try_add(right, c.source_curve()).unwrap();
                let actual = c.pushforward_arbitrary_jacobian_class(&sum).unwrap();
                let expected = c
                    .target_add(&images[left_index], &images[right_index])
                    .unwrap();
                assert_eq!(
                    actual, expected,
                    "norm homomorphism failed for ordered pair ({left_index},{right_index})"
                );
            }
        }

        let mut rational_source_points = vec![BinaryCoverPoint::Infinity];
        for u in 0..8 {
            for v in 0..8 {
                let point = BinaryCoverPoint::Affine {
                    u: elt(u),
                    v: elt(v),
                };
                if c.source_is_on_curve(&point) {
                    rational_source_points.push(point);
                }
            }
        }
        assert_eq!(rational_source_points.len(), 6);
        for point in rational_source_points {
            let divisor = match &point {
                BinaryCoverPoint::Infinity => MumfordDivisor::identity(3),
                BinaryCoverPoint::Affine { u, v } => {
                    MumfordDivisor::try_from_point(c.source_curve(), u, v).unwrap()
                }
            };
            assert_eq!(
                c.pushforward_arbitrary_jacobian_class(&divisor).unwrap(),
                c.pushforward_rational_point_divisor(&point).unwrap()
            );
        }

        let mut target_points = vec![BinaryPoint::Infinity];
        for x in 0..8 {
            for y in 0..8 {
                let point = target_point(x, y);
                if c.target_is_on_curve(&point) {
                    target_points.push(point);
                }
            }
        }
        assert_eq!(target_points.len(), 6);
        for point in target_points {
            let pullback = c.pullback_point_class(&point).unwrap();
            assert_eq!(
                c.pushforward_arbitrary_jacobian_class(&pullback).unwrap(),
                c.target_scalar_mul_small(&point, 3).unwrap()
            );
        }

        assert_eq!(
            c.pushforward_arbitrary_jacobian_class(&checked_divisor(
                c.source_curve(),
                &[0, 1],
                &[],
            ))
            .unwrap(),
            target_point(0, 7)
        );
        assert_eq!(
            c.pushforward_arbitrary_jacobian_class(&checked_divisor(
                c.source_curve(),
                &[4, 0, 1],
                &[2, 5],
            ))
            .unwrap(),
            target_point(3, 2)
        );
        assert_eq!(
            c.pushforward_arbitrary_jacobian_class(&checked_divisor(
                c.source_curve(),
                &[1, 1, 1],
                &[3, 2],
            ))
            .unwrap(),
            BinaryPoint::Infinity
        );
        assert_eq!(
            c.pushforward_arbitrary_jacobian_class(&checked_divisor(
                c.source_curve(),
                &[6, 1, 0, 1],
                &[6, 7, 6],
            ))
            .unwrap(),
            target_point(4, 0)
        );
    }

    #[test]
    fn arbitrary_pushforward_rejects_malformed_inputs_and_accepts_all_models() {
        let c = cover(1, 3);
        let identity = MumfordDivisor::identity(3);
        let zero_u = MumfordDivisor {
            u: F2mPoly::zero(3),
            v: F2mPoly::zero(3),
        };
        assert_eq!(
            c.pushforward_arbitrary_jacobian_class(&zero_u),
            Err(CoverTransferError::Hyperelliptic(
                HyperellipticError::ZeroDivisorPolynomial
            ))
        );
        let non_monic = MumfordDivisor {
            u: F2mPoly::constant(elt(2)),
            v: F2mPoly::zero(3),
        };
        assert_eq!(
            c.pushforward_arbitrary_jacobian_class(&non_monic),
            Err(CoverTransferError::Hyperelliptic(
                HyperellipticError::NonMonicDivisorPolynomial
            ))
        );
        let wrong_width = MumfordDivisor::identity(2);
        assert!(matches!(
            c.pushforward_arbitrary_jacobian_class(&wrong_width),
            Err(CoverTransferError::Hyperelliptic(
                HyperellipticError::PolynomialFieldMismatch { .. }
            ))
        ));
        let wrong_equation = MumfordDivisor {
            u: F2mPoly::from_coeffs(vec![elt(1), elt(1)], 3),
            v: F2mPoly::zero(3),
        };
        assert_eq!(
            c.pushforward_arbitrary_jacobian_class(&wrong_equation),
            Err(CoverTransferError::Hyperelliptic(
                HyperellipticError::DivisorEquationNotDivisible
            ))
        );

        for a in 0..8 {
            for b in 1..8 {
                assert_eq!(
                    cover(a, b)
                        .pushforward_arbitrary_jacobian_class(&identity)
                        .unwrap(),
                    BinaryPoint::Infinity,
                    "model a={a}, b={b} must accept the identity"
                );
            }
        }
        let other_basis = OrdinaryBinaryCover::new(
            3,
            IrreduciblePoly {
                degree: 3,
                low_terms: vec![0, 2],
            },
            elt(1),
            elt(3),
        )
        .unwrap();
        assert_eq!(
            other_basis
                .pushforward_arbitrary_jacobian_class(&identity)
                .unwrap(),
            BinaryPoint::Infinity
        );
    }

    #[test]
    fn arbitrary_pushforward_rejects_oversized_polynomials_before_validation() {
        let c = cover(1, 3);
        let oversized_u = MumfordDivisor {
            u: F2mPoly {
                m: 2,
                coeffs: vec![F2mElement::one(2); 5],
            },
            v: F2mPoly::zero(3),
        };
        assert_eq!(
            c.pushforward_arbitrary_jacobian_class(&oversized_u),
            Err(CoverTransferError::DivisorPolynomialTooLong {
                polynomial: "u",
                maximum_coefficients: 4,
                actual_coefficients: 5,
            })
        );

        let oversized_v = MumfordDivisor {
            u: F2mPoly::one(3),
            v: F2mPoly {
                m: 2,
                coeffs: vec![F2mElement::one(2); 4],
            },
        };
        assert_eq!(
            c.pushforward_arbitrary_jacobian_class(&oversized_v),
            Err(CoverTransferError::DivisorPolynomialTooLong {
                polynomial: "v",
                maximum_coefficients: 3,
                actual_coefficients: 4,
            })
        );
    }
}
