//! Checked composition of the quadratic cover with a Montgomery target model.
//!
//! Let `pi_s : C -> E_s` be [`PrimeQuadraticCoverP`] and let
//! `phi : E_s -> E_m` be [`PrimeMontgomeryAdapterP`]. This module exposes
//! the composed cover `pi_m = phi o pi_s` without ever interpreting a point
//! in the wrong coordinate model. Since `phi` is a projective isomorphism,
//! the cover degree remains two and the induced maps satisfy
//!
//! ```text
//! pi_m* pi_m^* = [2]
//! pi_m^* pi_m* = 1 + deck_*
//! ```
//!
//! This is intentionally Montgomery-only. The repository's Edwards
//! normalizations are birational affine charts with exceptional points and
//! require a separate, typed projective implementation.

use super::balanced::{BalancedDivisorP, SplitHyperellipticCurveP};
use super::cover_transfer::{
    PrimePushPullCertificate, PrimeQuadraticCoverError, PrimeQuadraticCoverP,
    PrimeSubgroupTransferStatus,
};
use super::model_transfer::{
    PrimeMontgomeryAdapterError, PrimeMontgomeryAdapterP, PrimeMontgomeryPointP,
};
use num_bigint::BigUint;
use std::fmt;

/// Checked failure from a Montgomery isomorphism, the short-model cover, or
/// an identity rechecked after composing the two maps.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum PrimeMontgomeryQuadraticCoverError {
    Adapter(PrimeMontgomeryAdapterError),
    Cover(PrimeQuadraticCoverError),
    CompositionIdentityMismatch { identity: &'static str },
}

impl fmt::Display for PrimeMontgomeryQuadraticCoverError {
    fn fmt(&self, out: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Adapter(error) => write!(out, "Montgomery target adapter error: {error}"),
            Self::Cover(error) => write!(out, "quadratic cover error: {error}"),
            Self::CompositionIdentityMismatch { identity } => {
                write!(out, "composed induced-map identity failed: {identity}")
            }
        }
    }
}

impl std::error::Error for PrimeMontgomeryQuadraticCoverError {}

impl From<PrimeMontgomeryAdapterError> for PrimeMontgomeryQuadraticCoverError {
    fn from(error: PrimeMontgomeryAdapterError) -> Self {
        Self::Adapter(error)
    }
}

impl From<PrimeQuadraticCoverError> for PrimeMontgomeryQuadraticCoverError {
    fn from(error: PrimeQuadraticCoverError) -> Self {
        Self::Cover(error)
    }
}

/// Replayable certificate for `pi_m* pi_m^* = [2]` in Montgomery
/// coordinates.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PrimeMontgomeryPullPushCertificate {
    pub input: PrimeMontgomeryPointP,
    pub pullback: BalancedDivisorP,
    pub pushforward: PrimeMontgomeryPointP,
    pub twice_input: PrimeMontgomeryPointP,
    pub identity_holds: bool,
}

/// Replayable certificate for `pi_m^* pi_m* = 1 + deck_*` with the target
/// values represented in Montgomery coordinates.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PrimeMontgomeryPushPullCertificate {
    pub input: BalancedDivisorP,
    pub pushforward: PrimeMontgomeryPointP,
    pub pullback: BalancedDivisorP,
    pub deck_transform: BalancedDivisorP,
    pub input_plus_deck: BalancedDivisorP,
    pub identity_holds: bool,
}

/// A checked degree-two genus-two cover whose public target coordinates are
/// the original Montgomery model.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PrimeMontgomeryQuadraticCoverP {
    adapter: PrimeMontgomeryAdapterP,
    short_cover: PrimeQuadraticCoverP,
}

impl PrimeMontgomeryQuadraticCoverP {
    /// Construct `phi o pi_s` from the Montgomery coefficients and the
    /// quadratic shift in normalized short-Weierstrass coordinates.
    pub fn try_new(
        p: BigUint,
        montgomery_a: BigUint,
        montgomery_b: BigUint,
        short_shift: BigUint,
    ) -> Result<Self, PrimeMontgomeryQuadraticCoverError> {
        let adapter = PrimeMontgomeryAdapterP::try_new(p, montgomery_a, montgomery_b)?;
        let short_cover = PrimeQuadraticCoverP::try_new(
            adapter.modulus().clone(),
            adapter.short_a().clone(),
            adapter.short_b().clone(),
            short_shift,
        )?;
        Ok(Self {
            adapter,
            short_cover,
        })
    }

    pub fn adapter(&self) -> &PrimeMontgomeryAdapterP {
        &self.adapter
    }

    pub fn short_cover(&self) -> &PrimeQuadraticCoverP {
        &self.short_cover
    }

    pub fn modulus(&self) -> &BigUint {
        self.adapter.modulus()
    }

    pub fn source_curve(&self) -> &SplitHyperellipticCurveP {
        self.short_cover.source_curve()
    }

    /// Reconstruct both component maps and their shared coefficients.
    pub fn validate(&self) -> Result<(), PrimeMontgomeryQuadraticCoverError> {
        self.adapter.validate()?;
        self.short_cover.validate()?;
        if self.adapter.modulus() != self.short_cover.modulus()
            || self.adapter.short_a() != self.short_cover.target_a()
            || self.adapter.short_b() != self.short_cover.target_b()
        {
            return Err(
                PrimeMontgomeryQuadraticCoverError::CompositionIdentityMismatch {
                    identity: "adapter/cover coefficient agreement",
                },
            );
        }
        let rebuilt = Self::try_new(
            self.modulus().clone(),
            self.adapter.montgomery_a().clone(),
            self.adapter.montgomery_b().clone(),
            self.short_cover.shift().clone(),
        )?;
        if rebuilt != *self {
            return Err(
                PrimeMontgomeryQuadraticCoverError::CompositionIdentityMismatch {
                    identity: "composed cover reconstruction",
                },
            );
        }
        Ok(())
    }

    pub fn validate_target_point(
        &self,
        point: &PrimeMontgomeryPointP,
    ) -> Result<(), PrimeMontgomeryQuadraticCoverError> {
        self.adapter.validate_montgomery_point(point)?;
        Ok(())
    }

    pub fn checked_target_neg(
        &self,
        point: &PrimeMontgomeryPointP,
    ) -> Result<PrimeMontgomeryPointP, PrimeMontgomeryQuadraticCoverError> {
        let short = self.adapter.montgomery_to_short(point)?;
        let negated = self.short_cover.checked_target_neg(&short)?;
        Ok(self.adapter.short_to_montgomery(&negated)?)
    }

    pub fn checked_target_add(
        &self,
        left: &PrimeMontgomeryPointP,
        right: &PrimeMontgomeryPointP,
    ) -> Result<PrimeMontgomeryPointP, PrimeMontgomeryQuadraticCoverError> {
        let short_left = self.adapter.montgomery_to_short(left)?;
        let short_right = self.adapter.montgomery_to_short(right)?;
        let sum = self
            .short_cover
            .checked_target_add(&short_left, &short_right)?;
        Ok(self.adapter.short_to_montgomery(&sum)?)
    }

    pub fn checked_target_scalar_mul(
        &self,
        point: &PrimeMontgomeryPointP,
        scalar: &BigUint,
    ) -> Result<PrimeMontgomeryPointP, PrimeMontgomeryQuadraticCoverError> {
        let short = self.adapter.montgomery_to_short(point)?;
        let multiple = self.short_cover.checked_target_scalar_mul(&short, scalar)?;
        Ok(self.adapter.short_to_montgomery(&multiple)?)
    }

    /// Pull back a point expressed on the original Montgomery model.
    pub fn pullback_point_class(
        &self,
        point: &PrimeMontgomeryPointP,
    ) -> Result<BalancedDivisorP, PrimeMontgomeryQuadraticCoverError> {
        let short = self.adapter.montgomery_to_short(point)?;
        Ok(self.short_cover.pullback_point_class(&short)?)
    }

    /// Push a balanced divisor class through the short target and then the
    /// checked projective isomorphism to Montgomery coordinates.
    pub fn pushforward_arbitrary_balanced_class(
        &self,
        divisor: &BalancedDivisorP,
    ) -> Result<PrimeMontgomeryPointP, PrimeMontgomeryQuadraticCoverError> {
        let short = self
            .short_cover
            .pushforward_arbitrary_balanced_class(divisor)?;
        Ok(self.adapter.short_to_montgomery(&short)?)
    }

    pub fn deck_transform(
        &self,
        divisor: &BalancedDivisorP,
    ) -> Result<BalancedDivisorP, PrimeMontgomeryQuadraticCoverError> {
        Ok(self.short_cover.deck_transform(divisor)?)
    }

    pub fn pull_push_composition_certificate(
        &self,
        point: &PrimeMontgomeryPointP,
    ) -> Result<PrimeMontgomeryPullPushCertificate, PrimeMontgomeryQuadraticCoverError> {
        let pullback = self.pullback_point_class(point)?;
        let pushforward = self.pushforward_arbitrary_balanced_class(&pullback)?;
        let twice_input = self.checked_target_add(point, point)?;
        let identity_holds = pushforward == twice_input;
        if !identity_holds {
            return Err(
                PrimeMontgomeryQuadraticCoverError::CompositionIdentityMismatch {
                    identity: "pi_m* pi_m^* = [2]",
                },
            );
        }
        Ok(PrimeMontgomeryPullPushCertificate {
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
    ) -> Result<PrimeMontgomeryPushPullCertificate, PrimeMontgomeryQuadraticCoverError> {
        let PrimePushPullCertificate {
            input,
            pushforward,
            pullback,
            deck_transform,
            input_plus_deck,
            identity_holds,
        } = self
            .short_cover
            .push_pull_composition_certificate(divisor)?;
        let pushforward = self.adapter.short_to_montgomery(&pushforward)?;
        if !identity_holds {
            return Err(
                PrimeMontgomeryQuadraticCoverError::CompositionIdentityMismatch {
                    identity: "pi_m^* pi_m* = 1 + deck_*",
                },
            );
        }
        Ok(PrimeMontgomeryPushPullCertificate {
            input,
            pushforward,
            pullback,
            deck_transform,
            input_plus_deck,
            identity_holds,
        })
    }

    pub fn subgroup_transfer_status(
        &self,
        order: &BigUint,
    ) -> Result<PrimeSubgroupTransferStatus, PrimeMontgomeryQuadraticCoverError> {
        Ok(self.short_cover.subgroup_transfer_status(order)?)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::prime_hyperelliptic::{FpPoly, PrimeEllipticPointP};
    use num_traits::{ToPrimitive, Zero};

    fn n(value: u64) -> BigUint {
        BigUint::from(value)
    }

    fn fixture() -> PrimeMontgomeryQuadraticCoverP {
        // E_m/F_7: y^2=x^3+3x^2+x. Its normalized short model is
        // Y^2=X^3+5X+1 and c=0 gives C: v^2=u^6+5u^2+1.
        PrimeMontgomeryQuadraticCoverP::try_new(n(7), n(3), n(1), n(0)).unwrap()
    }

    fn target_points(cover: &PrimeMontgomeryQuadraticCoverP) -> Vec<PrimeMontgomeryPointP> {
        let p = cover.modulus().to_u64().unwrap();
        let mut points = vec![PrimeMontgomeryPointP::Infinity];
        for x in 0..p {
            for y in 0..p {
                let point = PrimeMontgomeryPointP::Affine { x: n(x), y: n(y) };
                if cover.validate_target_point(&point).is_ok() {
                    points.push(point);
                }
            }
        }
        points
    }

    #[test]
    fn fixture_binds_the_exact_models_source_and_infinity() {
        let cover = fixture();
        cover.validate().unwrap();
        assert_eq!(cover.adapter().montgomery_a(), &n(3));
        assert_eq!(cover.adapter().montgomery_b(), &n(1));
        assert_eq!(cover.adapter().short_a(), &n(5));
        assert_eq!(cover.adapter().short_b(), &n(1));
        assert_eq!(cover.short_cover().shift(), &n(0));
        assert_eq!(
            cover.source_curve().f,
            FpPoly::from_coeffs(vec![n(1), n(0), n(5), n(0), n(0), n(0), n(1)], n(7),)
        );
        assert_eq!(target_points(&cover).len(), 12);

        let identity = cover
            .pullback_point_class(&PrimeMontgomeryPointP::Infinity)
            .unwrap();
        assert!(identity.is_identity());
        assert_eq!(identity.n_plus, 1);
        assert_eq!(
            cover
                .pushforward_arbitrary_balanced_class(&identity)
                .unwrap(),
            PrimeMontgomeryPointP::Infinity
        );
        assert_eq!(
            cover
                .adapter()
                .montgomery_to_short(&PrimeMontgomeryPointP::Infinity),
            Ok(PrimeEllipticPointP::Infinity)
        );
    }

    #[test]
    fn nontrivial_scaling_and_shift_are_composed_at_the_map_junction() {
        // E_m/F_7: 2*y^2=x^3+3*x^2+x, c=1.  The normalized short model is
        // Y^2=X^3+3*X+1 and C: v^2=u^6+3*u^4+6*u^2+5.
        let cover = PrimeMontgomeryQuadraticCoverP::try_new(n(7), n(3), n(2), n(1)).unwrap();
        cover.validate().unwrap();
        assert_eq!(cover.adapter().short_a(), &n(3));
        assert_eq!(cover.adapter().short_b(), &n(1));
        assert_eq!(cover.short_cover().shift(), &n(1));
        assert_eq!(
            cover.source_curve().f,
            FpPoly::from_coeffs(vec![n(5), n(0), n(6), n(0), n(3), n(0), n(1)], n(7),)
        );
        assert_eq!(target_points(&cover).len(), 12);
        assert_eq!(
            cover
                .source_curve()
                .enumerate_reduced_divisors()
                .unwrap()
                .len(),
            120
        );

        // Montgomery (3,2) maps to short (2,1). Its pullback has U=u^2-1,
        // and pushing it forward returns [2](3,2)=(2,2) in Montgomery
        // coordinates. This simultaneously exercises B != 1 and c != 0.
        let point = PrimeMontgomeryPointP::Affine { x: n(3), y: n(2) };
        let certificate = cover.pull_push_composition_certificate(&point).unwrap();
        assert!(certificate.identity_holds);
        assert_eq!(
            certificate.pullback.u,
            FpPoly::from_coeffs(vec![n(6), n(0), n(1)], n(7))
        );
        assert_eq!(
            certificate.pullback.v,
            FpPoly::from_coeffs(vec![n(1)], n(7))
        );
        assert_eq!(certificate.pullback.n_plus, 0);
        assert_eq!(
            certificate.pushforward,
            PrimeMontgomeryPointP::Affine { x: n(2), y: n(2) }
        );

        let generator = PrimeMontgomeryPointP::Affine { x: n(4), y: n(4) };
        assert_eq!(
            cover.checked_target_scalar_mul(&generator, &n(3)).unwrap(),
            PrimeMontgomeryPointP::Infinity
        );
        let PrimeSubgroupTransferStatus::InjectiveIfExactSubgroupOrder {
            degree_inverse_mod_order,
            ..
        } = cover.subgroup_transfer_status(&n(3)).unwrap()
        else {
            panic!("odd order must be conditionally injective")
        };
        let generator_certificate = cover.pull_push_composition_certificate(&generator).unwrap();
        assert_eq!(
            cover
                .checked_target_scalar_mul(
                    &generator_certificate.pushforward,
                    &degree_inverse_mod_order,
                )
                .unwrap(),
            generator
        );
    }

    #[test]
    fn every_small_point_and_divisor_satisfies_both_compositions() {
        let cover = fixture();
        let points = target_points(&cover);
        for point in &points {
            let certificate = cover.pull_push_composition_certificate(point).unwrap();
            assert!(certificate.identity_holds);
            assert_eq!(certificate.input, *point);
            assert_eq!(certificate.pushforward, certificate.twice_input);
        }

        let classes = cover.source_curve().enumerate_reduced_divisors().unwrap();
        assert_eq!(classes.len(), 72);
        for divisor in &classes {
            let certificate = cover.push_pull_composition_certificate(divisor).unwrap();
            assert!(certificate.identity_holds);
            assert_eq!(certificate.input, *divisor);
            assert_eq!(certificate.pullback, certificate.input_plus_deck);
        }
    }

    #[test]
    fn pullback_and_pushforward_are_homomorphisms_on_the_complete_fixture() {
        let cover = fixture();
        let points = target_points(&cover);
        for left in &points {
            for right in &points {
                let sum = cover.checked_target_add(left, right).unwrap();
                let pull_sum = cover.pullback_point_class(&sum).unwrap();
                let expected = cover
                    .pullback_point_class(left)
                    .unwrap()
                    .checked_add(
                        &cover.pullback_point_class(right).unwrap(),
                        cover.source_curve(),
                    )
                    .unwrap();
                assert_eq!(pull_sum, expected, "left={left:?}, right={right:?}");
            }
        }

        let classes = cover.source_curve().enumerate_reduced_divisors().unwrap();
        for left in &classes {
            for right in &classes {
                let sum = left.checked_add(right, cover.source_curve()).unwrap();
                let push_sum = cover.pushforward_arbitrary_balanced_class(&sum).unwrap();
                let expected = cover
                    .checked_target_add(
                        &cover.pushforward_arbitrary_balanced_class(left).unwrap(),
                        &cover.pushforward_arbitrary_balanced_class(right).unwrap(),
                    )
                    .unwrap();
                assert_eq!(push_sum, expected, "left={left:?}, right={right:?}");
            }
        }
    }

    #[test]
    fn odd_subgroup_recovery_is_checked_but_exactness_stays_a_premise() {
        let cover = fixture();
        let generator = PrimeMontgomeryPointP::Affine { x: n(4), y: n(2) };
        assert_eq!(
            cover.checked_target_scalar_mul(&generator, &n(3)).unwrap(),
            PrimeMontgomeryPointP::Infinity
        );
        let pullback = cover.pullback_point_class(&generator).unwrap();
        assert!(!pullback.is_identity());
        assert!(pullback
            .checked_scalar_mul(&n(3), cover.source_curve())
            .unwrap()
            .is_identity());

        let status = cover.subgroup_transfer_status(&n(3)).unwrap();
        let PrimeSubgroupTransferStatus::InjectiveIfExactSubgroupOrder {
            degree_inverse_mod_order,
            ..
        } = status
        else {
            panic!("odd order must be conditionally injective")
        };
        assert_eq!(degree_inverse_mod_order, n(2));
        let certificate = cover.pull_push_composition_certificate(&generator).unwrap();
        assert_eq!(
            cover
                .checked_target_scalar_mul(&certificate.pushforward, &degree_inverse_mod_order)
                .unwrap(),
            generator
        );

        assert!(matches!(
            cover.subgroup_transfer_status(&n(2)).unwrap(),
            PrimeSubgroupTransferStatus::KernelIntersectionUnresolved {
                common_factor: 2,
                ..
            }
        ));
        assert!(cover.subgroup_transfer_status(&BigUint::zero()).is_err());
    }

    #[test]
    fn malformed_models_points_and_coordinate_confusion_fail_closed() {
        assert!(matches!(
            PrimeMontgomeryQuadraticCoverP::try_new(n(3), n(1), n(1), n(0)),
            Err(PrimeMontgomeryQuadraticCoverError::Adapter(
                PrimeMontgomeryAdapterError::UnsupportedCharacteristic
            ))
        ));
        assert!(matches!(
            PrimeMontgomeryQuadraticCoverP::try_new(n(15), n(1), n(1), n(0)),
            Err(PrimeMontgomeryQuadraticCoverError::Adapter(
                PrimeMontgomeryAdapterError::ModulusNotPrime
            ))
        ));
        assert!(matches!(
            PrimeMontgomeryQuadraticCoverP::try_new(n(7), n(2), n(1), n(0)),
            Err(PrimeMontgomeryQuadraticCoverError::Adapter(
                PrimeMontgomeryAdapterError::SingularMontgomeryModel
            ))
        ));

        let cover = fixture();
        // Short (0,1) is valid, but the same coordinate pair is not on the
        // Montgomery target. The composed API never guesses the model.
        assert!(cover
            .short_cover()
            .validate_target_point(&PrimeEllipticPointP::Affine { x: n(0), y: n(1) })
            .is_ok());
        assert!(matches!(
            cover.validate_target_point(&PrimeMontgomeryPointP::Affine { x: n(0), y: n(1) }),
            Err(PrimeMontgomeryQuadraticCoverError::Adapter(
                PrimeMontgomeryAdapterError::PointNotOnMontgomeryModel
            ))
        ));
        assert!(matches!(
            cover.validate_target_point(&PrimeMontgomeryPointP::Affine { x: n(7), y: n(1) }),
            Err(PrimeMontgomeryQuadraticCoverError::Adapter(
                PrimeMontgomeryAdapterError::PointCoordinateOutOfRange { coordinate: "x" }
            ))
        ));
    }
}
