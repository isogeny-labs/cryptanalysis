//! End-to-end controls for the composed split-sextic-to-Montgomery transfer.
//!
//! This is an integration test so it remains runnable even when unrelated
//! unit-test modules elsewhere in the library have a compile-time collision.

use cryptanalysis_suite::prime_hyperelliptic::{
    PrimeEllipticPointP, PrimeMontgomeryAdapterError, PrimeMontgomeryPointP,
    PrimeMontgomeryQuadraticCoverError, PrimeMontgomeryQuadraticCoverP,
    PrimeSubgroupTransferStatus,
};
use num_bigint::BigUint;
use num_traits::{ToPrimitive, Zero};

fn n(value: u64) -> BigUint {
    BigUint::from(value)
}

fn fixture() -> PrimeMontgomeryQuadraticCoverP {
    // y^2=x^3+3x^2+x over F_7, normalized to Y^2=X^3+5X+1.
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
fn exhaustive_f7_composed_transfer_and_subgroup_boundary() {
    let cover = fixture();
    cover.validate().unwrap();

    let points = target_points(&cover);
    assert_eq!(points.len(), 12);
    for point in &points {
        let certificate = cover.pull_push_composition_certificate(point).unwrap();
        assert!(certificate.identity_holds);
        assert_eq!(certificate.input, *point);
        assert_eq!(certificate.pushforward, certificate.twice_input);
    }
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
    assert_eq!(classes.len(), 72);
    for divisor in &classes {
        let certificate = cover.push_pull_composition_certificate(divisor).unwrap();
        assert!(certificate.identity_holds);
        assert_eq!(certificate.pullback, certificate.input_plus_deck);
    }
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
    let PrimeSubgroupTransferStatus::InjectiveIfExactSubgroupOrder {
        degree_inverse_mod_order,
        ..
    } = cover.subgroup_transfer_status(&n(3)).unwrap()
    else {
        panic!("odd annihilator must be conditionally injective")
    };
    let certificate = cover.pull_push_composition_certificate(&generator).unwrap();
    assert_eq!(degree_inverse_mod_order, n(2));
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
fn nontrivial_scaling_and_cover_shift_cross_the_public_api_junction() {
    let cover = PrimeMontgomeryQuadraticCoverP::try_new(n(7), n(3), n(2), n(1)).unwrap();
    cover.validate().unwrap();
    assert_eq!(cover.adapter().short_a(), &n(3));
    assert_eq!(cover.adapter().short_b(), &n(1));
    assert_eq!(cover.short_cover().shift(), &n(1));
    assert_eq!(
        (0..=6)
            .map(|index| cover.source_curve().f.coeff(index).clone())
            .collect::<Vec<_>>(),
        vec![n(5), n(0), n(6), n(0), n(3), n(0), n(1)]
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

    let point = PrimeMontgomeryPointP::Affine { x: n(3), y: n(2) };
    let certificate = cover.pull_push_composition_certificate(&point).unwrap();
    assert!(certificate.identity_holds);
    assert_eq!(
        (0..=2)
            .map(|index| certificate.pullback.u.coeff(index).clone())
            .collect::<Vec<_>>(),
        vec![n(6), n(0), n(1)]
    );
    assert_eq!(certificate.pullback.v.coeff(0), n(1));
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
        panic!("odd annihilator must be conditionally injective")
    };
    let certificate = cover.pull_push_composition_certificate(&generator).unwrap();
    assert_eq!(
        cover
            .checked_target_scalar_mul(&certificate.pushforward, &degree_inverse_mod_order)
            .unwrap(),
        generator
    );
}

#[test]
fn coordinate_models_and_malformed_inputs_fail_closed() {
    let cover = fixture();
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
        PrimeMontgomeryQuadraticCoverP::try_new(n(15), n(1), n(1), n(0)),
        Err(PrimeMontgomeryQuadraticCoverError::Adapter(
            PrimeMontgomeryAdapterError::ModulusNotPrime
        ))
    ));
}
