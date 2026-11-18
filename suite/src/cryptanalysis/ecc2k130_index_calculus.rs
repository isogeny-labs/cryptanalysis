//! Native exact-parameter plumbing for the Certicom ECC2K-130 index-calculus
//! pipeline.
//!
//! The general Koblitz implementation constructs toy curves by searching for
//! a field polynomial and factoring the group order, which deliberately stops
//! below degree 64. ECC2K-130 already publishes every one of those values.
//! This module imports them without truncation, verifies the public generator
//! and target, and reconstructs the fixed workflow's Hamming-weight-two normal
//! basis factor base as native [`F2mElement`] values.

use std::collections::BTreeSet;

use num_bigint::BigUint;
use num_traits::{One, Zero};

use crate::binary_ecc::{BinaryPoint, F2mElement, IrreduciblePoly};
use crate::cryptanalysis::koblitz_index_calculus::{
    build_explicit_frobenius_orbit_factor_base, points_with_x, FrobeniusFactorBase, KoblitzCurve,
};

pub const DEGREE: u32 = 131;
pub const EXPECTED_ORBIT_COLUMNS: usize = 14;
pub const EXPECTED_SIGNED_POINTS: usize = 3_668;

const SUBGROUP_ORDER_DECIMAL: &str = "680564733841876926932320129493409985129";
const GENERATOR_X: &str = "051C99BFA6F18DE467C80C23B98C7994AA";
const GENERATOR_Y: &str = "042EA2D112ECEC71FCF7E000D7EFC978BD";
const TARGET_X: &str = "06C997F3E7F2C66A4A5D2FDA13756A37B1";
const TARGET_Y: &str = "04A38D11829D32D347BD0C0F584D546E9A";
// Image of the public polynomial generator in the permuted type-II ONB.
const PUBLIC_POLYNOMIAL_ROOT_ONB: &str = "55bced9c666b0fe76e49ce3445ba9eee7";

fn parse_decimal(value: &str) -> Result<BigUint, String> {
    BigUint::parse_bytes(value.as_bytes(), 10).ok_or_else(|| "invalid decimal constant".into())
}

fn parse_hex(value: &str) -> Result<BigUint, String> {
    BigUint::parse_bytes(value.as_bytes(), 16).ok_or_else(|| "invalid hexadecimal constant".into())
}

fn affine(x: &str, y: &str) -> Result<BinaryPoint, String> {
    Ok(BinaryPoint::Affine {
        x: F2mElement::from_biguint(&parse_hex(x)?, DEGREE),
        y: F2mElement::from_biguint(&parse_hex(y)?, DEGREE),
    })
}

/// The exact challenge curve and published subgroup generator.
pub fn curve() -> Result<KoblitzCurve, String> {
    KoblitzCurve::from_exact_parameters(
        0,
        DEGREE,
        IrreduciblePoly {
            degree: DEGREE,
            // x^131 + x^13 + x^2 + x + 1.
            low_terms: vec![0, 1, 2, 13],
        },
        affine(GENERATOR_X, GENERATOR_Y)?,
        parse_decimal(SUBGROUP_ORDER_DECIMAL)?,
        BigUint::from(4u8),
    )
}

/// The exact published target, accepted only after curve and subgroup checks.
pub fn target(curve: &KoblitzCurve) -> Result<BinaryPoint, String> {
    let target = affine(TARGET_X, TARGET_Y)?;
    if !curve.curve.is_on_curve(&target) {
        return Err("ECC2K-130 target is not on the declared curve".into());
    }
    if curve.mul(&target, &curve.subgroup_order) != BinaryPoint::Infinity {
        return Err("ECC2K-130 target is outside the declared prime subgroup".into());
    }
    Ok(target)
}

/// Type-II optimal-normal-basis arithmetic used only to reconstruct the
/// published polynomial/normal-basis isomorphism. Elements are symmetric
/// vectors modulo the all-ones vector, exactly as in the fixed Python engine.
struct Onb {
    m: u32,
    n: u32,
    mask: BigUint,
}

impl Onb {
    fn new(m: u32) -> Self {
        let n = 2 * m + 1;
        Self {
            m,
            n,
            mask: (BigUint::one() << n) - BigUint::one(),
        }
    }

    fn normalize(&self, mut value: BigUint) -> BigUint {
        if value.bit(0) {
            value ^= &self.mask;
        }
        value
    }

    fn encode_coords(&self, coordinates: &BigUint) -> BigUint {
        let mut value = BigUint::zero();
        for i in 1..=self.m {
            if coordinates.bit(u64::from(i - 1)) {
                value.set_bit(u64::from(i), true);
                value.set_bit(u64::from(self.n - i), true);
            }
        }
        value
    }

    fn to_coords(&self, value: &BigUint) -> BigUint {
        let value = self.normalize(value.clone());
        let mut coordinates = BigUint::zero();
        for i in 1..=self.m {
            if value.bit(u64::from(i)) {
                coordinates.set_bit(u64::from(i - 1), true);
            }
        }
        coordinates
    }

    fn rotate(&self, value: &BigUint, amount: u32) -> BigUint {
        let amount = amount % self.n;
        if amount == 0 {
            return value.clone();
        }
        ((value << amount) | (value >> (self.n - amount))) & &self.mask
    }

    fn mul(&self, left: &BigUint, right: &BigUint) -> BigUint {
        let mut result = BigUint::zero();
        let mut bits = right.clone();
        let mut position = 0u32;
        while !bits.is_zero() {
            if bits.bit(0) {
                result ^= self.rotate(left, position);
            }
            bits >>= 1u8;
            position += 1;
        }
        self.normalize(result)
    }

    fn frobenius(&self, value: &BigUint) -> BigUint {
        let mut result = BigUint::zero();
        for i in 0..self.n {
            if value.bit(u64::from(i)) {
                result.set_bit(u64::from((2 * i) % self.n), true);
            }
        }
        self.normalize(result)
    }

    fn one(&self) -> BigUint {
        self.encode_coords(&((BigUint::one() << self.m) - BigUint::one()))
    }
}

fn highest_bit(value: &BigUint) -> Option<usize> {
    (!value.is_zero()).then(|| value.bits() as usize - 1)
}

/// Inverse of the public polynomial-basis -> ONB linear map.
struct OnbToPolynomial {
    pivots: Vec<Option<(BigUint, BigUint)>>,
}

impl OnbToPolynomial {
    fn new() -> Result<Self, String> {
        let onb = Onb::new(DEGREE);
        let root = onb.encode_coords(&parse_hex(PUBLIC_POLYNOMIAL_ROOT_ONB)?);
        let mut power = onb.one();
        let mut pivots = vec![None; DEGREE as usize];
        for polynomial_bit in 0..DEGREE {
            let mut vector = onb.to_coords(&power);
            let mut tag = BigUint::one() << polynomial_bit;
            loop {
                let Some(pivot) = highest_bit(&vector) else {
                    return Err("public polynomial/ONB conversion is singular".into());
                };
                if let Some((basis, basis_tag)) = &pivots[pivot] {
                    vector ^= basis;
                    tag ^= basis_tag;
                } else {
                    pivots[pivot] = Some((vector, tag));
                    break;
                }
            }
            power = onb.mul(&power, &root);
        }
        if pivots.iter().any(Option::is_none) {
            return Err("public polynomial/ONB conversion does not have full rank".into());
        }
        Ok(Self { pivots })
    }

    fn convert(&self, coordinates: &BigUint) -> Result<F2mElement, String> {
        let mut vector = coordinates.clone();
        let mut polynomial = BigUint::zero();
        while let Some(pivot) = highest_bit(&vector) {
            let Some((basis, tag)) = &self.pivots[pivot] else {
                return Err("normal-basis coordinate is outside the conversion image".into());
            };
            vector ^= basis;
            polynomial ^= tag;
        }
        Ok(F2mElement::from_biguint(&polynomial, DEGREE))
    }
}

fn canonical_frobenius_coordinate(coordinates: &BigUint, onb: &Onb) -> BigUint {
    let mut internal = onb.encode_coords(coordinates);
    let mut best = coordinates.clone();
    for _ in 1..DEGREE {
        internal = onb.frobenius(&internal);
        let candidate = onb.to_coords(&internal);
        if candidate < best {
            best = candidate;
        }
    }
    best
}

/// Reconstruct the exact Hamming-weight-two factor base used by the durable
/// fixed workflow, then hand it to the native Rust orbit machinery.
pub fn hamming_weight_two_factor_base(curve: &KoblitzCurve) -> Result<FrobeniusFactorBase, String> {
    if curve.n != DEGREE || curve.a != 0 {
        return Err("the ECC2K-130 Hamming base requires K_0 over GF(2^131)".into());
    }
    let onb = Onb::new(DEGREE);
    let conversion = OnbToPolynomial::new()?;
    let mut candidate_coordinates = BTreeSet::new();
    let singleton = BigUint::one();
    candidate_coordinates.insert(canonical_frobenius_coordinate(&singleton, &onb));
    for tail in 1..DEGREE {
        let coordinate = &singleton | (BigUint::one() << tail);
        candidate_coordinates.insert(canonical_frobenius_coordinate(&coordinate, &onb));
    }

    let mut representatives = Vec::new();
    for coordinates in candidate_coordinates {
        // Odd-order points are doubles, and x(2P) has absolute trace zero.
        if coordinates.count_ones() % 2 == 1 {
            continue;
        }
        let x = conversion.convert(&coordinates)?;
        let points = points_with_x(&curve.curve, &x);
        let Some(point) = points.first() else {
            continue;
        };
        if curve.mul(point, &curve.subgroup_order) == BinaryPoint::Infinity {
            representatives.push(x);
        }
    }

    let base = build_explicit_frobenius_orbit_factor_base(curve, &representatives)
        .ok_or_else(|| "native ECC2K-130 factor-base construction failed".to_string())?;
    if base.unknowns() != EXPECTED_ORBIT_COLUMNS || base.points.len() != EXPECTED_SIGNED_POINTS {
        return Err(format!(
            "native ECC2K-130 factor base disagrees with the fixed profile: got {} columns and {} points",
            base.unknowns(),
            base.points.len()
        ));
    }
    Ok(base)
}

/// Construct and cross-check every public mathematical input needed by the
/// native relation pipeline.
pub fn validated_profile() -> Result<(KoblitzCurve, BinaryPoint, FrobeniusFactorBase), String> {
    let curve = curve()?;
    let target = target(&curve)?;
    let factor_base = hamming_weight_two_factor_base(&curve)?;
    Ok((curve, target, factor_base))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn exact_curve_target_and_factor_base_validate_natively() {
        let (curve, target, base) = validated_profile().expect("exact ECC2K-130 profile");
        assert_eq!(
            curve.group_order,
            &curve.subgroup_order * BigUint::from(4u8)
        );
        assert_eq!(
            curve.mul(&target, &curve.subgroup_order),
            BinaryPoint::Infinity
        );
        assert_eq!(base.unknowns(), EXPECTED_ORBIT_COLUMNS);
        assert_eq!(base.points.len(), EXPECTED_SIGNED_POINTS);
    }
}
