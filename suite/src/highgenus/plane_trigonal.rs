//! Birational affine plane chart for the existing trigonal Kummer family.
//!
//! For `y^3 = f1(x) f2(x)^2`, put `u = y/f2(x)` where `f2(x) != 0`.
//! Then `f2(x) u^3 = f1(x)`. The Kummer maximal-order engine is the
//! normalization arithmetic behind this chart. Points above roots of `f2`,
//! infinity, and other singular branches require separate local treatment.
//! This module does not turn plane line sections into Jacobian relations.

use rand::RngCore;
use std::collections::BTreeMap;

use num_bigint::BigUint;
use num_traits::Zero;

use super::fp::Fp;
use super::ic::{FactorBase, IndexCalculusCurve, Relation};
use super::kummer::{Ideal, SuperellipticCurve};
use super::poly::Poly;
use super::HgError;

#[derive(Clone, Debug)]
pub struct TrigonalPlaneChart {
    pub field: Fp,
    pub genus: u32,
    /// Degree of the homogeneous plane equation in `(X,U,Z)`.
    pub degree: usize,
    pub f1: Poly,
    pub f2: Poly,
}

impl TrigonalPlaneChart {
    /// Accept the genus-4/5 one-point family with exponent-one and
    /// exponent-two factors. The resulting plane chart has degree five for
    /// both genera; its geometric genus is recovered by normalization.
    pub fn new(curve: &SuperellipticCurve) -> Result<Self, HgError> {
        if curve.m != 3 || !(4..=5).contains(&curve.genus) || curve.factors.len() != 2 {
            return Err(HgError::Unsupported(
                "needs a genus-4/5 trigonal two-factor model",
            ));
        }
        let f1 = curve.factors.iter().find(|(_, e)| *e == 1).map(|(f, _)| f);
        let f2 = curve.factors.iter().find(|(_, e)| *e == 2).map(|(f, _)| f);
        let (Some(f1), Some(f2)) = (f1, f2) else {
            return Err(HgError::Unsupported("needs exponents one and two"));
        };
        let expected_degrees = if curve.genus == 4 { (3, 2) } else { (5, 1) };
        if (f1.degree(), f2.degree()) != (Some(expected_degrees.0), Some(expected_degrees.1)) {
            return Err(HgError::Unsupported(
                "needs the standard genus-4/5 trigonal degrees",
            ));
        }
        let degree = f1.degree().unwrap_or(0).max(f2.degree().unwrap_or(0) + 3);
        Ok(Self {
            field: curve.field,
            genus: curve.genus,
            degree,
            f1: f1.clone(),
            f2: f2.clone(),
        })
    }

    /// Homogeneous terms `(X exponent, U exponent, Z exponent, coefficient)`
    /// of `F2(X,Z) U^3 Z^(degree−deg(f2)−3) − F1(X,Z) Z^(degree−deg(f1))`.
    /// Coefficients are canonical residues in `F_p`.
    pub fn homogeneous_terms(&self) -> Vec<(usize, usize, usize, u64)> {
        let p = self.field.p();
        let mut out = Vec::new();
        for (i, &c) in self.f2.c.iter().enumerate() {
            if c != 0 {
                out.push((i, 3, self.degree - i - 3, c));
            }
        }
        for (i, &c) in self.f1.c.iter().enumerate() {
            if c != 0 {
                out.push((i, 0, self.degree - i, (p - c) % p));
            }
        }
        out
    }

    /// Evaluate the affine plane equation at `(x,u)`.
    pub fn affine_eval(&self, x: u64, u: u64) -> u64 {
        let k = &self.field;
        let x = x % k.p();
        let lhs = k.mul(self.f2.eval(x, k), k.pow(u % k.p(), 3));
        k.sub(lhs, self.f1.eval(x, k))
    }

    /// `u = y/f2(x)` on the birational open set.
    pub fn plane_u(&self, x: u64, y: u64) -> Option<u64> {
        self.field.div(
            y % self.field.p(),
            self.f2.eval(x % self.field.p(), &self.field),
        )
    }

    /// `y = u f2(x)` on the birational open set. Reject points on the
    /// exceptional fibers and off the plane curve.
    pub fn source_y(&self, x: u64, u: u64) -> Option<u64> {
        let k = &self.field;
        let x = x % k.p();
        let f2x = self.f2.eval(x, k);
        (f2x != 0 && self.affine_eval(x, u) == 0).then(|| k.mul(u % k.p(), f2x))
    }

    /// The corresponding degree-one prime of the normalized Kummer model.
    /// This is an ideal class input for the existing Jacobian arithmetic.
    pub fn source_place(
        &self,
        curve: &SuperellipticCurve,
        x: u64,
        u: u64,
        rng: &mut impl RngCore,
    ) -> Option<Ideal> {
        if curve.m != 3 || curve.genus != self.genus || curve.field.p() != self.field.p() {
            return None;
        }
        let same_factors = curve.factors.iter().any(|(f, e)| *e == 1 && *f == self.f1)
            && curve.factors.iter().any(|(f, e)| *e == 2 && *f == self.f2);
        if !same_factors {
            return None;
        }
        let y = self.source_y(x, u)?;
        let k = &self.field;
        let xx = x % k.p();
        let pi = Poly::from_coeffs(vec![k.neg(xx), 1], k);
        let place = curve
            .places_above(&pi, rng)
            .into_iter()
            .find(|(_, root)| root.c.first().copied().unwrap_or(0) == y)?;
        Some(curve.canonical(&place.0))
    }

    /// Zeros of the affine line function `u−slope*x−intercept` on the
    /// normalization, when all are rational. Roots of
    /// `f1−(slope*x+intercept)^3 f2` carry their intersection multiplicity.
    /// Its exceptional/infinite poles are independent of the intercept for
    /// fixed slope. For genus 4, compare nonzero slopes with nonzero slopes;
    /// a horizontal line has a different pole order at infinity.
    pub fn affine_line_divisor(
        &self,
        curve: &SuperellipticCurve,
        slope: u64,
        intercept: u64,
        rng: &mut impl RngCore,
    ) -> Option<Vec<(Ideal, usize)>> {
        let k = &self.field;
        let slope = slope % k.p();
        let intercept = intercept % k.p();
        let line = Poly::from_coeffs(vec![intercept, slope], k);
        let cube = line.mul(&line, k).mul(&line, k);
        let h = self.f1.sub(&self.f2.mul(&cube, k), k);
        let mut divisor = Vec::new();
        for (factor, multiplicity) in h.factor(k, rng) {
            if factor.degree() != Some(1) {
                return None;
            }
            let x = k.neg(factor.c.first().copied().unwrap_or(0));
            let u = k.add(k.mul(slope, x), intercept);
            let place = self.source_place(curve, x, u, rng)?;
            divisor.push((place, multiplicity));
        }
        (divisor
            .iter()
            .map(|(_, multiplicity)| multiplicity)
            .sum::<usize>()
            == h.degree().unwrap_or(0))
        .then_some(divisor)
    }

    /// The horizontal special case `u=c`; all heights share the same pole
    /// divisor, including the exceptional fibers and infinity.
    pub fn horizontal_divisor(
        &self,
        curve: &SuperellipticCurve,
        c: u64,
        rng: &mut impl RngCore,
    ) -> Option<Vec<(Ideal, usize)>> {
        self.affine_line_divisor(curve, 0, c, rng)
    }

    /// A homogeneous factor-base relation from two completely rational
    /// affine lines. At genus 4, horizontal and nonhorizontal lines have
    /// different pole orders at infinity and cannot be paired here.
    pub fn affine_line_relation(
        &self,
        curve: &SuperellipticCurve,
        factor_base: &FactorBase<Ideal>,
        first: (u64, u64),
        second: (u64, u64),
        rng: &mut impl RngCore,
    ) -> Option<Relation> {
        let p = self.field.p();
        if self.genus == 4 && (first.0 % p == 0) != (second.0 % p == 0) {
            return None;
        }
        let a = self.affine_line_divisor(curve, first.0, first.1, rng)?;
        let b = self.affine_line_divisor(curve, second.0, second.1, rng)?;
        let mut coefficients = BTreeMap::<usize, i64>::new();
        for (divisor, sign) in [(&a, 1i64), (&b, -1i64)] {
            for (place, multiplicity) in divisor {
                let decomposed = curve.decompose(place, 1, rng)?;
                if decomposed.len() != 1 || decomposed[0].1 != 1 {
                    return None;
                }
                let column = *factor_base.index.get(&decomposed[0].0)?;
                *coefficients.entry(column).or_default() += sign * (*multiplicity as i64);
            }
        }
        Some(Relation {
            coeffs: coefficients
                .into_iter()
                .filter(|(_, coefficient)| *coefficient != 0)
                .collect(),
            alpha: BigUint::zero(),
            beta: BigUint::zero(),
        })
    }
}

#[cfg(test)]
mod tests {
    use rand::{rngs::StdRng, SeedableRng};

    use super::super::ic::build_factor_base;
    use super::super::JacobianGroup;
    use super::*;

    fn split_poly(field: &Fp, roots: &[u64]) -> Poly {
        roots.iter().fold(Poly::one(), |product, &root| {
            product.mul(&Poly::from_coeffs(vec![field.neg(root), 1], field), field)
        })
    }

    #[test]
    fn genus_four_and_five_plane_charts_match_normalized_places() {
        let mut rng = StdRng::seed_from_u64(20261128);
        let field = Fp::new(11).unwrap();
        for genus in [4, 5] {
            let curve = SuperellipticCurve::random_trigonal(field, genus, &mut rng).unwrap();
            let chart = TrigonalPlaneChart::new(&curve).unwrap();
            assert_eq!(chart.degree, 5);
            let mut checked = 0;
            let mut exceptional_x = 0;
            for x in 0..field.p() {
                if chart.f2.eval(x, &field) == 0 {
                    exceptional_x += 1;
                    assert!(chart.source_y(x, 0).is_none());
                }
                for u in 0..field.p() {
                    let homogeneous = chart.homogeneous_terms().into_iter().fold(
                        0u64,
                        |acc, (x_exp, u_exp, _, coeff)| {
                            let term = field.mul(
                                coeff,
                                field.mul(field.pow(x, x_exp as u64), field.pow(u, u_exp as u64)),
                            );
                            field.add(acc, term)
                        },
                    );
                    assert_eq!(homogeneous, chart.affine_eval(x, u));
                    if chart.affine_eval(x, u) != 0 {
                        continue;
                    }
                    if chart.f2.eval(x, &field) == 0 {
                        panic!("coprime factors forbid affine chart points at f2=0");
                    }
                    let y = chart.source_y(x, u).unwrap();
                    assert_eq!(field.pow(y, 3), curve.big_f.eval(x, &field));
                    assert_eq!(chart.plane_u(x, y), Some(u));
                    assert_eq!(chart.source_y(x + field.p(), u + field.p()), Some(y));
                    assert_eq!(chart.plane_u(x + field.p(), y + field.p()), Some(u));
                    let ideal = chart.source_place(&curve, x, u, &mut rng).unwrap();
                    assert!(curve.is_canonical(&ideal));
                    assert_eq!(ideal.degree(), 1);
                    checked += 1;
                }
            }
            assert!(checked > 0, "genus {genus}: no ordinary affine points");
            if genus == 5 {
                assert!(exceptional_x > 0, "linear f2 must have a rational root");
            }
            for (x_exp, u_exp, z_exp, coeff) in chart.homogeneous_terms() {
                assert_eq!(x_exp + u_exp + z_exp, chart.degree);
                assert!(coeff < field.p());
            }
        }
    }

    #[test]
    fn split_horizontal_sections_agree_in_genus_four_and_five_jacobians() {
        // Exhaustively selected split fixtures; no scalar or target is planted.
        let cases: &[(u64, u32, &[u64], &[u64], u64, &[u64])] = &[
            (11, 4, &[0, 1, 2], &[3, 4], 2, &[5, 8, 9]),
            (17, 5, &[0, 1, 2, 3, 7], &[13], 13, &[8, 11, 14, 15, 16]),
        ];
        let mut rng = StdRng::seed_from_u64(20261128);
        for &(p, genus, roots1, roots2, height, other_roots) in cases {
            let field = Fp::new(p).unwrap();
            let f1 = split_poly(&field, roots1);
            let f2 = split_poly(&field, roots2);
            let curve = SuperellipticCurve::new(field, 3, vec![(f1, 1), (f2, 2)]).unwrap();
            assert_eq!(curve.genus, genus);
            let chart = TrigonalPlaneChart::new(&curve).unwrap();
            let first = chart.horizontal_divisor(&curve, 0, &mut rng).unwrap();
            let second = chart.horizontal_divisor(&curve, height, &mut rng).unwrap();
            assert_eq!(first.len(), roots1.len());
            assert_eq!(second.len(), other_roots.len());
            assert!(chart.horizontal_divisor(&curve, 1, &mut rng).is_none());
            assert!(first
                .iter()
                .chain(&second)
                .all(|(_, multiplicity)| *multiplicity == 1));
            let roots_of = |divisor: &[(Ideal, usize)]| {
                let mut roots: Vec<_> = divisor
                    .iter()
                    .map(|(place, _)| field.neg(place.norm(&field).c[0]))
                    .collect();
                roots.sort_unstable();
                roots
            };
            assert_eq!(roots_of(&first), roots1);
            assert_eq!(roots_of(&second), other_roots);
            let sum = |divisor: &[(Ideal, usize)]| {
                divisor
                    .iter()
                    .fold(curve.identity(), |acc, (place, multiplicity)| {
                        let mut acc = acc;
                        for _ in 0..*multiplicity {
                            acc = curve.add(&acc, place);
                        }
                        acc
                    })
            };
            assert_eq!(
                sum(&first),
                sum(&second),
                "genus {genus} horizontal line relation"
            );
        }
    }

    #[test]
    fn split_nonhorizontal_lines_agree_in_genus_four_and_five_jacobians() {
        let cases: &[(u32, &[u64], &[u64], (u64, u64, &[u64]), (u64, u64, &[u64]))] = &[
            (
                4,
                &[0, 1, 2],
                &[3, 7],
                (2, 0, &[0, 6, 10, 13, 15]),
                (16, 13, &[5, 8, 10, 12, 14]),
            ),
            (
                5,
                &[0, 1, 2, 3, 5],
                &[6],
                (7, 12, &[4, 7, 9, 12, 16]),
                (8, 0, &[0, 8, 12, 13, 14]),
            ),
        ];
        let field = Fp::new(17).unwrap();
        let mut rng = StdRng::seed_from_u64(0x2026_1128);
        for &(genus, roots1, roots2, a, b) in cases {
            let f1 = split_poly(&field, roots1);
            let f2 = split_poly(&field, roots2);
            let curve = SuperellipticCurve::new(field, 3, vec![(f1, 1), (f2, 2)]).unwrap();
            assert_eq!(curve.genus, genus);
            let chart = TrigonalPlaneChart::new(&curve).unwrap();
            let first = chart
                .affine_line_divisor(&curve, a.0, a.1, &mut rng)
                .unwrap();
            let second = chart
                .affine_line_divisor(&curve, b.0, b.1, &mut rng)
                .unwrap();
            let roots_of = |divisor: &[(Ideal, usize)]| {
                let mut roots: Vec<_> = divisor
                    .iter()
                    .map(|(place, _)| field.neg(place.norm(&field).c[0]))
                    .collect();
                roots.sort_unstable();
                roots
            };
            assert_eq!(roots_of(&first), a.2);
            assert_eq!(roots_of(&second), b.2);
            assert!(first
                .iter()
                .chain(&second)
                .all(|(_, multiplicity)| *multiplicity == 1));
            let sum = |divisor: &[(Ideal, usize)]| {
                divisor
                    .iter()
                    .fold(curve.identity(), |acc, (place, multiplicity)| {
                        let mut acc = acc;
                        for _ in 0..*multiplicity {
                            acc = curve.add(&acc, place);
                        }
                        acc
                    })
            };
            assert_eq!(
                sum(&first),
                sum(&second),
                "genus {genus} affine line relation"
            );
            let factor_base = build_factor_base(&curve, 1, &mut rng).unwrap();
            let relation = chart
                .affine_line_relation(&curve, &factor_base, (a.0, a.1), (b.0, b.1), &mut rng)
                .unwrap();
            assert!(relation.alpha.is_zero() && relation.beta.is_zero());
            assert!(!relation.coeffs.is_empty());
            let row_sum = relation
                .coeffs
                .iter()
                .fold(curve.identity(), |acc, &(index, coeff)| {
                    let term = curve.scalar_mul(
                        &BigUint::from(coeff.unsigned_abs()),
                        &factor_base.places[index].elem,
                    );
                    curve.add(&acc, &if coeff < 0 { curve.neg(&term) } else { term })
                });
            assert!(curve.is_identity(&row_sum));
            if genus == 5 {
                let horizontal = chart.horizontal_divisor(&curve, 0, &mut rng).unwrap();
                assert_eq!(sum(&first), sum(&horizontal));
            } else {
                assert!(chart
                    .affine_line_relation(&curve, &factor_base, (0, 0), (a.0, a.1), &mut rng)
                    .is_none());
            }
        }
    }
}
