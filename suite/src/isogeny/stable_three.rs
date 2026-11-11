//! Fp-rational degree-three isogenies, including non-rational kernel points.
//!
//! For p > 3 and E: y²=x³+ax+b, a Frobenius-stable cyclic subgroup of
//! order three is {O, ±P}. Its common x-coordinate r is in Fp, even when
//! y(P) is not. Therefore the rational roots of the 3-division polynomial
//! ψ₃(r)=3r⁴+6ar²+12br−a² enumerate *all* Fp-rational degree-3
//! kernel subgroup schemes, without requiring 3 | #E(Fp).
//!
//! This deliberately bounded O(p) root scanner is for small fields only.
//! It does not repair the general odd-prime enumerator for degrees >3,
//! and it is not wired into the old volcano graph's partial enumeration.
//!
//! References: Pizzo–Pomerance–Voight (2019), §2, Lemma 2.4 (over Q;
//! the Galois argument extends to finite fields of characteristic >3);
//! Banegas et al., "Fast and Frobenius" (2023), §5.

use super::SmallCurve;

/// A degree-3 Fp-rational isogeny whose kernel is {O, ±(r, √f(r))}.
///
/// Unlike `VeluIsogeny.kernel_half`, this type never invents an Fp
/// y-coordinate when the kernel's nonzero points are not Fp-rational.
#[derive(Clone, Debug)]
pub struct StableThreeIsogeny {
    pub domain: SmallCurve,
    pub codomain: SmallCurve,
    pub kernel_x: u64,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum StableThreeError {
    /// This formula requires a characteristic greater than three.
    UnsupportedCharacteristic,
    /// The input cubic is singular.
    SingularCurve,
    /// Refuse a potentially huge linear scan without an explicit caller cap.
    ScanLimitExceeded,
}

fn add(a: u128, b: u128, p: u128) -> u128 {
    (a % p + b % p) % p
}
fn sub(a: u128, b: u128, p: u128) -> u128 {
    (a % p + p - b % p) % p
}
fn mul(a: u128, b: u128, p: u128) -> u128 {
    (a % p * (b % p)) % p
}
fn power(mut x: u128, mut e: u128, p: u128) -> u128 {
    let mut result = 1u128;
    x %= p;
    while e != 0 {
        if e & 1 != 0 {
            result = mul(result, x, p);
        }
        x = mul(x, x, p);
        e >>= 1;
    }
    result
}

fn three_polynomial(r: u128, a: u128, b: u128, p: u128) -> u128 {
    let r2 = mul(r, r, p);
    let r4 = mul(r2, r2, p);
    sub(
        add(
            add(mul(3, r4, p), mul(6, mul(a, r2, p), p), p),
            mul(12, mul(b, r, p), p),
            p,
        ),
        mul(a, a, p),
        p,
    )
}

impl StableThreeIsogeny {
    /// Evaluate the rational map on a source point, including infinity.
    ///
    /// `None` represents the point at infinity; it is also the image of
    /// both nonidentity kernel points over an algebraic closure. The input
    /// must already lie on `domain`.
    pub fn evaluate(&self, point: Option<(u64, u64)>) -> Option<(u64, u64)> {
        let (x, y) = point?;
        let p = self.domain.p as u128;
        let x = (x as u128) % p;
        let y = (y as u128) % p;
        let r = self.kernel_x as u128;
        if x == r {
            return None;
        }
        let a = (self.domain.a as u128) % p;
        let b = (self.domain.b as u128) % p;
        let r2 = mul(r, r, p);
        let rhs = add(add(mul(r2, r, p), mul(a, r, p), p), b, p);
        let v = mul(2, add(mul(3, r2, p), a, p), p);
        let u = mul(4, rhs, p);
        let inv = power(sub(x, r, p), p - 2, p);
        let inv2 = mul(inv, inv, p);
        let inv3 = mul(inv2, inv, p);
        let xx = add(add(x, mul(v, inv, p), p), mul(u, inv2, p), p);
        let factor = sub(
            sub(1, mul(v, inv2, p), p),
            mul(2, mul(u, inv3, p), p),
            p,
        );
        Some((xx as u64, mul(y, factor, p) as u64))
    }
}

/// Exhaustively enumerate every Fp-rational degree-3 kernel for a small
/// nonsingular Weierstrass curve over a prime field p > 3.
///
/// The caller supplies `scan_limit` to make the O(p) scope explicit.
/// No roots means there is no Fp-rational degree-3 kernel; this statement
/// is *only* guaranteed for degree 3, unlike pointwise torsion sampling.
pub fn three_isogenies_over_fp_small(
    curve: &SmallCurve,
    scan_limit: u64,
) -> Result<Vec<StableThreeIsogeny>, StableThreeError> {
    let p = curve.p as u128;
    if curve.p <= 3 {
        return Err(StableThreeError::UnsupportedCharacteristic);
    }
    if curve.p > scan_limit {
        return Err(StableThreeError::ScanLimitExceeded);
    }
    let a = (curve.a as u128) % p;
    let b = (curve.b as u128) % p;
    let delta = add(mul(4, mul(mul(a, a, p), a, p), p), mul(27, mul(b, b, p), p), p);
    if delta == 0 {
        return Err(StableThreeError::SingularCurve);
    }
    let mut results = Vec::new();
    for r in 0..curve.p {
        let r = r as u128;
        if three_polynomial(r, a, b, p) != 0 {
            continue;
        }
        let r2 = mul(r, r, p);
        // 3-torsion cannot simultaneously have y=0 in char >3 on
        // a nonsingular curve, so each root gives exactly one ± pair.
        let rhs = add(add(mul(r2, r, p), mul(a, r, p), p), b, p);
        if rhs == 0 {
            continue;
        }
        let v = mul(2, add(mul(3, r2, p), a, p), p);
        let u = mul(4, rhs, p);
        let aa = sub(a, mul(5, v, p), p);
        let bb = sub(b, mul(7, add(u, mul(r, v, p), p), p), p);
        results.push(StableThreeIsogeny {
            domain: *curve,
            codomain: SmallCurve {
                name: curve.name,
                p: curve.p,
                a: aa as u64,
                b: bb as u64,
            },
            kernel_x: r as u64,
        });
    }
    Ok(results)
}

#[cfg(test)]
mod tests {
    use super::*;

    type Point = Option<(u64, u64)>;

    fn add_points(p: u64, a: u64, left: Point, right: Point) -> Point {
        match (left, right) {
            (None, q) | (q, None) => q,
            (Some((x, y)), Some((z, w))) => {
                let modulus = p as u128;
                let (x, y, z, w) = (x as u128, y as u128, z as u128, w as u128);
                if x == z && add(y, w, modulus) == 0 {
                    return None;
                }
                let slope = if x == z {
                    let numerator = add(mul(3, mul(x, x, modulus), modulus), a as u128, modulus);
                    let denominator = mul(2, y, modulus);
                    mul(numerator, power(denominator, modulus - 2, modulus), modulus)
                } else {
                    mul(
                        sub(w, y, modulus),
                        power(sub(z, x, modulus), modulus - 2, modulus),
                        modulus,
                    )
                };
                let x3 = sub(sub(mul(slope, slope, modulus), x, modulus), z, modulus);
                let y3 = sub(mul(slope, sub(x, x3, modulus), modulus), y, modulus);
                Some((x3 as u64, y3 as u64))
            }
        }
    }

    fn all_points(curve: &SmallCurve) -> Vec<Point> {
        let mut result = vec![None];
        for x in 0..curve.p {
            for y in 0..curve.p {
                if mul(y as u128, y as u128, curve.p as u128)
                    == curve.rhs(x) as u128
                {
                    result.push(Some((x, y)));
                }
            }
        }
        result
    }

    fn exhaustive_homomorphism(curve: &SmallCurve, expected_count: usize) {
        let domain = all_points(curve);
        let maps = three_isogenies_over_fp_small(curve, 200).expect("valid small curve");
        assert_eq!(maps.len(), expected_count);
        for iso in maps {
            let codomain = all_points(&iso.codomain);
            assert_eq!(domain.len(), codomain.len(), "isogenous curves have equal orders");
            for &p in &domain {
                let fp = iso.evaluate(p);
                assert!(codomain.contains(&fp), "image lies on codomain");
                for &q in &domain {
                    let fq = iso.evaluate(q);
                    assert_eq!(
                        iso.evaluate(add_points(curve.p, curve.a, p, q)),
                        add_points(curve.p, iso.codomain.a, fp, fq),
                        "homomorphism violation for r={}, p={p:?}, q={q:?}",
                        iso.kernel_x
                    );
                }
            }
        }
    }

    #[test]
    fn irrational_three_kernel_with_order_not_divisible_by_three() {
        let curve = SmallCurve { name: "103-3", p: 103, a: 0, b: 3 };
        let maps = three_isogenies_over_fp_small(&curve, 200).unwrap();
        assert_eq!(maps.len(), 1);
        assert_eq!(maps[0].kernel_x, 0);
        assert_eq!((maps[0].codomain.a, maps[0].codomain.b), (0, 22));
        assert_eq!(power(3, 51, 103), 102, "kernel y coordinate is not rational");
        assert_eq!(all_points(&curve).len(), 124);
        assert_ne!(124 % 3, 0);
        exhaustive_homomorphism(&curve, 1);
    }

    #[test]
    fn discovers_both_rational_and_irrational_kernel_points() {
        let curve = SmallCurve { name: "101-2", p: 101, a: 0, b: 2 };
        let maps = three_isogenies_over_fp_small(&curve, 200).unwrap();
        assert_eq!(maps.iter().map(|m| m.kernel_x).collect::<Vec<_>>(), vec![0, 99]);
        assert_eq!((maps[0].codomain.a, maps[0].codomain.b), (0, 47));
        exhaustive_homomorphism(&curve, 2);
    }

    #[test]
    fn bounded_scope_and_singularity_rejection() {
        let curve = SmallCurve { name: "103-3", p: 103, a: 0, b: 3 };
        assert!(matches!(
            three_isogenies_over_fp_small(&curve, 100),
            Err(StableThreeError::ScanLimitExceeded)
        ));
        let singular = SmallCurve { name: "bad", p: 101, a: 0, b: 0 };
        assert!(matches!(
            three_isogenies_over_fp_small(&singular, 200),
            Err(StableThreeError::SingularCurve)
        ));
    }
}
