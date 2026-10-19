//! Published Certicom ECC2-131 and ECCp-131 challenge parameters and targets.
//!
//! `ECC2-130` and `ECCp-130` are accepted lookup aliases. The canonical
//! published names use 131; ECC2K-130 is a different, Koblitz challenge.
//!
//! Source: <https://www.certicom.com/en/curves-list>, retrieved 2026-10-19.
//! HTML SHA-256: 34ca84c9ef1021ad2f7a46726cdfd68b209a362fbd0e82a2e55903151d2ef857.

use super::{CurveParams, Point};
use crate::binary_ecc::curve::{BinaryCurve, BinaryPoint};
use crate::binary_ecc::f2m::{F2mElement, IrreduciblePoly};
use num_bigint::BigUint;

fn hex(value: &str) -> BigUint {
    BigUint::parse_bytes(value.as_bytes(), 16).expect("published Certicom hex constant")
}

/// The random binary challenge over GF(2^131), in the published polynomial
/// basis z^131 + z^13 + z^2 + z + 1, and its published target Q.
pub fn binary_challenge(name: &str) -> Option<(BinaryCurve, BinaryPoint)> {
    if !name.eq_ignore_ascii_case("ecc2-131") && !name.eq_ignore_ascii_case("ecc2-130") {
        return None;
    }
    let point = |x: &str, y: &str| BinaryPoint::Affine {
        x: F2mElement::from_hex(x, 131),
        y: F2mElement::from_hex(y, 131),
    };
    Some((
        BinaryCurve {
            m: 131,
            irreducible: IrreduciblePoly {
                degree: 131,
                low_terms: vec![0, 1, 2, 13],
            },
            a: F2mElement::from_hex("07EBCB7EECC296A1C4A1A14F2C9E44352E", 131),
            b: F2mElement::from_hex("00610B0A57C73649AD0093BDD622A61D81", 131),
            generator: point(
                "00439CBC8DC73AA981030D5BC57B331663",
                "014904C07D4F25A16C2DE036D60B762BD4",
            ),
            order: hex("0400000000000000026ABB991FE311FE83"),
            cofactor: BigUint::from(2u32),
        },
        point(
            "0602339C5DB0E9C694AC8908528C51C440",
            "04F7B99169FA1A0F2737813742B1588CB8",
        ),
    ))
}

/// The prime-field short-Weierstrass challenge and its published target Q.
pub fn prime_challenge(name: &str) -> Option<(CurveParams, Point)> {
    if !name.eq_ignore_ascii_case("eccp-131") && !name.eq_ignore_ascii_case("eccp-130") {
        return None;
    }
    let curve = CurveParams {
        name: "ECCp-131",
        p: hex("048E1D43F293469E33194C43186B3ABC0B"),
        a: hex("041CB121CE2B31F608A76FC8F23D73CB66"),
        b: hex("02F74F717E8DEC90991E5EA9B2FF03DA58"),
        gx: hex("03DF84A96B5688EF574FA91A32E197198A"),
        gy: hex("014721161917A44FB7B4626F36F0942E71"),
        n: hex("048E1D43F293469E317F7ED728F6B8E6F1"),
        h: 1,
    };
    let target = Point::Affine {
        x: curve.fe(hex("03AA6F004FC62E2DA1ED0BFB62C3FFB568")),
        y: curve.fe(hex("009C21C284BA8A445BB2701BF55E3A67ED")),
    };
    Some((curve, target))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::binary_ecc::curve::scalar_mul;
    use crate::cryptanalysis::curve_catalog;

    #[test]
    fn certicom_131_points_and_orders_match_published_parameters() {
        let (binary, q) = binary_challenge("ECC2-131").unwrap();
        assert_eq!(binary.m, 131);
        assert_eq!(binary.irreducible.low_terms, [0, 1, 2, 13]);
        assert_eq!(binary.order.bits(), 131);
        assert_eq!(binary.cofactor, BigUint::from(2u32));
        // This random curve must never acquire the Koblitz model or folding.
        assert_ne!(binary.b, F2mElement::one(131));
        for point in [&binary.generator, &q] {
            assert_ne!(*point, BinaryPoint::Infinity);
            assert!(binary.is_on_curve(point));
            assert_eq!(
                scalar_mul(&binary, point, &binary.order),
                BinaryPoint::Infinity
            );
        }

        let (prime, q) = prime_challenge("ECCp-131").unwrap();
        assert_eq!(prime.p.bits(), 131);
        assert_eq!(prime.n.bits(), 131);
        assert_eq!(prime.h, 1);
        for point in [&prime.generator(), &q] {
            assert_ne!(*point, Point::Infinity);
            assert!(prime.is_on_curve(point));
            assert_eq!(point.scalar_mul(&prime.n, &prime.a_fe()), Point::Infinity);
        }
    }

    #[test]
    fn certicom_130_aliases_preserve_the_canonical_curve_and_target() {
        let (binary, q) = binary_challenge("ECC2-130").unwrap();
        let (canonical, expected_q) = binary_challenge("ecc2-131").unwrap();
        assert_eq!(binary.generator, canonical.generator);
        assert_eq!(binary.order, canonical.order);
        assert_eq!(q, expected_q);
        let (prime, q) = prime_challenge("ECCP-130").unwrap();
        let (canonical, expected_q) = prime_challenge("eccp-131").unwrap();
        assert_eq!(prime.name, "ECCp-131");
        assert_eq!(prime.p, canonical.p);
        assert_eq!(prime.generator(), canonical.generator());
        assert_eq!(q, expected_q);
        for (alias, canonical) in [("ECC2-130", "ecc2-131"), ("ECCp-130", "eccp-131")] {
            let entry = curve_catalog::by_name(alias).unwrap();
            assert_eq!(entry.name, canonical);
            assert!(entry.verify().iter().all(|check| check.passed));
        }
        assert!(binary_challenge("ECC2K-130").is_none());
        assert!(binary_challenge("ECCp-131").is_none());
        assert!(prime_challenge("ECC2-131").is_none());
        assert!(prime_challenge("ECCp-132").is_none());
    }
}
