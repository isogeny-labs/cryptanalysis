//! Birational affine plane chart for the existing trigonal Kummer family.
//!
//! For `y^3 = f1(x) f2(x)^2`, put `u = y/f2(x)` where `f2(x) != 0`.
//! Then `f2(x) u^3 = f1(x)`. The Kummer maximal-order engine is the
//! normalization arithmetic behind this chart. Points above roots of `f2`,
//! infinity, and other singular branches require separate local treatment;
//! vertical fibers above rational roots of `f2` use normalized places.
//! Completely split affine line sections give homogeneous factor-base
//! relations when their pole divisors agree.

use rand::RngCore;
use std::collections::{BTreeMap, HashSet};

use num_bigint::BigUint;
use num_traits::Zero;

use super::fp::Fp;
use super::ic::{FactorBase, IndexCalculusCurve, Relation};
use super::kummer::{Ideal, SuperellipticCurve};
use super::poly::Poly;
use super::{HgError, JacobianGroup};

#[derive(Clone, Debug)]
pub struct TrigonalPlaneChart {
    pub field: Fp,
    pub genus: u32,
    /// Degree of the homogeneous plane equation in `(X,U,Z)`.
    pub degree: usize,
    pub f1: Poly,
    pub f2: Poly,
}

/// A bounded scan of affine lines in lexicographic `(slope, intercept)` order.
#[derive(Clone, Debug, Default)]
pub struct AffineLineScan {
    pub scanned: usize,
    pub split: usize,
    pub relations: Vec<Relation>,
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
        if !self.matches_curve(curve) {
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

    fn matches_curve(&self, curve: &SuperellipticCurve) -> bool {
        curve.m == 3
            && curve.genus == self.genus
            && curve.field.p() == self.field.p()
            && curve.factors.iter().any(|(f, e)| *e == 1 && *f == self.f1)
            && curve.factors.iter().any(|(f, e)| *e == 2 && *f == self.f2)
    }

    /// At the unique normalized infinity place, `ord∞(x)=-3` and
    /// `ord∞(u)=-(deg(f1)-deg(f2))`. The two orders differ in both
    /// supported genera, so the pole order of `u-mx-b` is their maximum.
    fn affine_infinity_pole_order(&self, slope: u64) -> usize {
        let u_order = self.f1.degree().unwrap() - self.f2.degree().unwrap();
        u_order.max(if slope % self.field.p() == 0 { 0 } else { 3 })
    }

    /// The affine `u` coordinate of an ordinary quadratic normalized place.
    fn quadratic_plane_u(&self, pi: &Poly, y: &Poly) -> Option<Poly> {
        if pi.degree() != Some(2) {
            return None;
        }
        let k = &self.field;
        let f2 = self.f2.rem(pi, k);
        let u = Poly::mulmod(y, &f2.inv_mod(pi, k)?, pi, k);
        let cube = Poly::mulmod(&Poly::mulmod(&u, &u, pi, k), &u, pi, k);
        Poly::mulmod(&f2, &cube, pi, k)
            .sub(&self.f1, k)
            .rem(pi, k)
            .is_zero()
            .then_some(u)
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

    /// Zeros of the vertical line function `x−a`. The pole divisor at
    /// infinity is the same for every `a`. A root of `f2` is exceptional
    /// in this chart, but the unique ramified place above it is available
    /// directly from the normalized Kummer model with multiplicity three.
    pub fn vertical_divisor(
        &self,
        curve: &SuperellipticCurve,
        a: u64,
        rng: &mut impl RngCore,
    ) -> Option<Vec<(Ideal, usize)>> {
        let k = &self.field;
        let x = a % k.p();
        let f2x = self.f2.eval(x, k);
        if f2x == 0 {
            if !self.matches_curve(curve) {
                return None;
            }
            let pi = Poly::from_coeffs(vec![k.neg(x), 1], k);
            let places = curve.places_above(&pi, rng);
            if places.len() != 1 || !places[0].1.is_zero() {
                return None;
            }
            return Some(vec![(curve.canonical(&places[0].0), 3)]);
        }
        let h = Poly::from_coeffs(vec![k.neg(self.f1.eval(x, k)), 0, 0, f2x], k);
        let mut divisor = Vec::new();
        for (factor, multiplicity) in h.factor(k, rng) {
            if factor.degree() != Some(1) {
                return None;
            }
            let u = k.neg(factor.c.first().copied().unwrap_or(0));
            divisor.push((self.source_place(curve, x, u, rng)?, multiplicity));
        }
        (divisor
            .iter()
            .map(|(_, multiplicity)| multiplicity)
            .sum::<usize>()
            == 3)
            .then_some(divisor)
    }

    /// A homogeneous factor-base row from two completely rational vertical
    /// fibers. Unlike affine `u=mx+b` sections, this uses the function
    /// `(x−a)/(x−b)` and its common pole divisor at infinity.
    pub fn vertical_line_relation(
        &self,
        curve: &SuperellipticCurve,
        factor_base: &FactorBase<Ideal>,
        first: u64,
        second: u64,
        rng: &mut impl RngCore,
    ) -> Option<Relation> {
        let a = self.vertical_divisor(curve, first, rng)?;
        let b = self.vertical_divisor(curve, second, rng)?;
        self.divisor_relation(curve, factor_base, &a, &b, rng)
    }

    /// Compare an affine line `u=mx+b` with a vertical line `x=a`.
    /// The affine function has a simple pole at every place above `f2=0`,
    /// while the vertical function has none there. Their remaining pole
    /// difference is supported at the rational point at infinity, whose
    /// degree-zero class is the identity. An irreducible quadratic factor
    /// of `f2` is accepted when the factor base includes degree-two places.
    pub fn mixed_line_relation(
        &self,
        curve: &SuperellipticCurve,
        factor_base: &FactorBase<Ideal>,
        affine: (u64, u64),
        vertical_x: u64,
        rng: &mut impl RngCore,
    ) -> Option<Relation> {
        let a = self.affine_line_divisor(curve, affine.0, affine.1, rng)?;
        let mut b = self.vertical_divisor(curve, vertical_x, rng)?;
        for (factor, multiplicity) in self.f2.factor(&self.field, rng) {
            let degree = factor.degree()?;
            if degree == 0 || degree > factor_base.bound || multiplicity != 1 {
                return None;
            }
            let fiber = curve.places_above(&factor, rng);
            if fiber.len() != 1 || !fiber[0].1.is_zero() {
                return None;
            }
            b.push((curve.canonical(&fiber[0].0), 1));
        }
        self.divisor_relation(curve, factor_base, &a, &b, rng)
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
        if self.affine_infinity_pole_order(first.0) != self.affine_infinity_pole_order(second.0) {
            return None;
        }
        let a = self.affine_line_divisor(curve, first.0, first.1, rng)?;
        let b = self.affine_line_divisor(curve, second.0, second.1, rng)?;
        self.divisor_relation(curve, factor_base, &a, &b, rng)
    }

    fn divisor_relation(
        &self,
        curve: &SuperellipticCurve,
        factor_base: &FactorBase<Ideal>,
        a: &[(Ideal, usize)],
        b: &[(Ideal, usize)],
        rng: &mut impl RngCore,
    ) -> Option<Relation> {
        let mut coefficients = BTreeMap::<usize, i64>::new();
        for (divisor, sign) in [(a, 1i64), (b, -1i64)] {
            for (place, multiplicity) in divisor {
                let decomposed = curve.decompose(place, factor_base.bound, rng)?;
                if decomposed.len() != 1 || decomposed[0].1 != 1 {
                    return None;
                }
                let column = *factor_base.index.get(&decomposed[0].0)?;
                if factor_base.places.get(column)?.elem != *place {
                    return None;
                }
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

    /// Direct target descent when a normalized target ideal has only places
    /// of degree at most the supplied factor-base bound (one or two). Each
    /// place is checked against the plane chart, mapped to the factor base,
    /// and replayed in the source Jacobian. No target scalar is used.
    /// Support above degree two needs a separate descent step.
    pub fn direct_target_relation(
        &self,
        curve: &SuperellipticCurve,
        factor_base: &FactorBase<Ideal>,
        target: &Ideal,
        rng: &mut impl RngCore,
    ) -> Option<Relation> {
        if !self.matches_curve(curve)
            || !curve.is_canonical(target)
            || !(1..=2).contains(&factor_base.bound)
        {
            return None;
        }
        let support = curve.decompose(target, factor_base.bound, rng)?;
        let mut coefficients = BTreeMap::<usize, i64>::new();
        let mut replay = curve.identity();
        for (key, multiplicity) in support {
            let degree = key.pi.degree()?;
            if degree == 0 || degree > factor_base.bound {
                return None;
            }
            let source = if degree == 1 {
                let x = self.field.neg(*key.pi.c.first()?);
                if self.f2.eval(x, &self.field) == 0 {
                    if !key.r.is_zero() {
                        return None;
                    }
                    let fiber = self.vertical_divisor(curve, x, rng)?;
                    if fiber.len() != 1 || fiber[0].1 != 3 {
                        return None;
                    }
                    fiber[0].0.clone()
                } else {
                    let y = *key.r.c.first().unwrap_or(&0);
                    let u = self.plane_u(x, y)?;
                    self.source_place(curve, x, u, rng)?
                }
            } else {
                let k = &self.field;
                let f2 = self.f2.rem(&key.pi, k);
                if f2.is_zero() {
                    // An irreducible quadratic f2 gives one ramified
                    // normalized place, absent from the affine chart.
                    if !key.r.is_zero() {
                        return None;
                    }
                } else {
                    self.quadratic_plane_u(&key.pi, &key.r)?;
                }
                let place = curve
                    .places_above(&key.pi, rng)
                    .into_iter()
                    .find(|(_, residue)| *residue == key.r)?;
                curve.canonical(&place.0)
            };
            let column = *factor_base.index.get(&key)?;
            if factor_base.places.get(column)?.elem != source {
                return None;
            }
            *coefficients.entry(column).or_default() += i64::from(multiplicity);
            for _ in 0..multiplicity {
                replay = curve.add(&replay, &source);
            }
        }
        if replay != *target {
            return None;
        }
        Some(Relation {
            coeffs: coefficients.into_iter().collect(),
            alpha: BigUint::zero(),
            beta: BigUint::from(1u32),
        })
    }

    /// Descend one ordinary quadratic target place through its unique
    /// rational affine line `u=mx+b`. If the remaining line section splits
    /// into rational places, compare it with a split anchor line in the same
    /// pole family and return a degree-one factor-base row for the target.
    pub fn descend_quadratic_target_line(
        &self,
        curve: &SuperellipticCurve,
        factor_base: &FactorBase<Ideal>,
        target: &Ideal,
        anchor: (u64, u64),
        rng: &mut impl RngCore,
    ) -> Option<Relation> {
        if !self.matches_curve(curve) || !curve.is_canonical(target) || factor_base.bound != 1 {
            return None;
        }
        let support = curve.decompose(target, 2, rng)?;
        if support.len() != 1 || support[0].1 != 1 {
            return None;
        }
        let key = &support[0].0;
        let u = self.quadratic_plane_u(&key.pi, &key.r)?;
        let line = (*u.c.get(1).unwrap_or(&0), *u.c.first().unwrap_or(&0));
        if self.affine_infinity_pole_order(line.0) != self.affine_infinity_pole_order(anchor.0) {
            return None;
        }
        let anchor_divisor = self.affine_line_divisor(curve, anchor.0, anchor.1, rng)?;
        let k = &self.field;
        let cube = u.mul(&u, k).mul(&u, k);
        let h = self.f1.sub(&self.f2.mul(&cube, k), k);
        let mut residual = Vec::new();
        let mut target_count = 0;
        for (factor, multiplicity) in h.factor(k, rng) {
            if factor == key.pi {
                target_count += multiplicity;
                continue;
            }
            if factor.degree() != Some(1) {
                return None;
            }
            let x = k.neg(*factor.c.first()?);
            let height = k.add(k.mul(line.0, x), line.1);
            residual.push((self.source_place(curve, x, height, rng)?, multiplicity));
        }
        if target_count != 1 {
            return None;
        }
        let mut coefficients = BTreeMap::<usize, i64>::new();
        let mut replay = curve.identity();
        for (divisor, sign) in [(&anchor_divisor, 1i64), (&residual, -1i64)] {
            for (place, multiplicity) in divisor {
                let decomposed = curve.decompose(place, 1, rng)?;
                if decomposed.len() != 1 || decomposed[0].1 != 1 {
                    return None;
                }
                let column = *factor_base.index.get(&decomposed[0].0)?;
                if factor_base.places.get(column)?.elem != *place {
                    return None;
                }
                *coefficients.entry(column).or_default() += sign * (*multiplicity as i64);
                for _ in 0..*multiplicity {
                    replay = curve.add(
                        &replay,
                        &if sign < 0 {
                            curve.neg(place)
                        } else {
                            place.clone()
                        },
                    );
                }
            }
        }
        if replay != *target {
            return None;
        }
        Some(Relation {
            coeffs: coefficients
                .into_iter()
                .filter(|(_, coefficient)| *coefficient != 0)
                .collect(),
            alpha: BigUint::zero(),
            beta: BigUint::from(1u32),
        })
    }

    /// Try rational anchor lines in lexicographic `(slope, intercept)` order.
    /// `max_lines` bounds all candidates, including lines in the wrong pole
    /// family or with a nonsplit section. The returned row is checked by
    /// `descend_quadratic_target_line` in the source Jacobian.
    pub fn descend_quadratic_target_line_bounded(
        &self,
        curve: &SuperellipticCurve,
        factor_base: &FactorBase<Ideal>,
        target: &Ideal,
        max_lines: usize,
        rng: &mut impl RngCore,
    ) -> Option<Relation> {
        if !self.matches_curve(curve) || !curve.is_canonical(target) || factor_base.bound != 1 {
            return None;
        }
        let mut scanned = 0;
        for slope in 0..self.field.p() {
            for intercept in 0..self.field.p() {
                if scanned == max_lines {
                    return None;
                }
                scanned += 1;
                if let Some(row) = self.descend_quadratic_target_line(
                    curve,
                    factor_base,
                    target,
                    (slope, intercept),
                    rng,
                ) {
                    return Some(row);
                }
            }
        }
        None
    }

    /// Scan at most `max_lines` affine lines and retain one homogeneous row
    /// per distinct split line after the first in its pole-divisor family.
    /// Genus four has separate horizontal and nonhorizontal families; genus
    /// five has one family. Zero and duplicate rows are omitted.
    pub fn collect_affine_line_relations(
        &self,
        curve: &SuperellipticCurve,
        factor_base: &FactorBase<Ideal>,
        max_lines: usize,
        rng: &mut impl RngCore,
    ) -> AffineLineScan {
        let mut result = AffineLineScan::default();
        let mut anchors: [Option<(u64, u64)>; 2] = [None, None];
        let mut seen = HashSet::new();
        let p = self.field.p();
        for slope in 0..p {
            for intercept in 0..p {
                if result.scanned == max_lines {
                    return result;
                }
                result.scanned += 1;
                if self
                    .affine_line_divisor(curve, slope, intercept, rng)
                    .is_none()
                {
                    continue;
                }
                result.split += 1;
                let family = usize::from(self.genus == 4 && slope != 0);
                let Some(anchor) = anchors[family] else {
                    anchors[family] = Some((slope, intercept));
                    continue;
                };
                if let Some(row) =
                    self.affine_line_relation(curve, factor_base, anchor, (slope, intercept), rng)
                {
                    if !row.coeffs.is_empty() && seen.insert(row.coeffs.clone()) {
                        result.relations.push(row);
                    }
                }
            }
        }
        result
    }
}

#[cfg(test)]
mod tests {
    use rand::{rngs::StdRng, SeedableRng};

    use super::super::ic::{
        build_factor_base, index_calculus_dlp_with_seed_relations, index_calculus_group_order,
        largest_prime_factor, IcParams,
    };
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

    #[test]
    fn bounded_line_scan_collects_distinct_verified_rows() {
        let field = Fp::new(17).unwrap();
        let mut rng = StdRng::seed_from_u64(0x5ca1_2026);
        for (genus, roots1, roots2) in [
            (4, vec![0, 1, 2], vec![3, 7]),
            (5, vec![0, 1, 2, 3, 5], vec![6]),
        ] {
            let curve = SuperellipticCurve::new(
                field,
                3,
                vec![
                    (split_poly(&field, &roots1), 1),
                    (split_poly(&field, &roots2), 2),
                ],
            )
            .unwrap();
            let chart = TrigonalPlaneChart::new(&curve).unwrap();
            let base = build_factor_base(&curve, 1, &mut rng).unwrap();
            let empty = chart.collect_affine_line_relations(&curve, &base, 0, &mut rng);
            assert_eq!(empty.scanned, 0);
            assert!(empty.relations.is_empty());
            let scan = chart.collect_affine_line_relations(
                &curve,
                &base,
                (field.p() * field.p()) as usize,
                &mut rng,
            );
            assert_eq!(scan.scanned, (field.p() * field.p()) as usize);
            assert!(scan.split >= 2, "genus {genus}");
            assert!(!scan.relations.is_empty(), "genus {genus}");
            let mut seen = HashSet::new();
            for row in &scan.relations {
                assert!(seen.insert(row.coeffs.clone()));
                assert!(row.alpha.is_zero() && row.beta.is_zero());
                let value = row.coeffs.iter().fold(curve.identity(), |acc, &(i, c)| {
                    let term =
                        curve.scalar_mul(&BigUint::from(c.unsigned_abs()), &base.places[i].elem);
                    curve.add(&acc, &if c < 0 { curve.neg(&term) } else { term })
                });
                assert!(curve.is_identity(&value), "genus {genus}");
            }
        }
    }

    #[test]
    fn tangent_line_multiplicities_are_preserved_in_relations() {
        let field = Fp::new(17).unwrap();
        let mut rng = StdRng::seed_from_u64(0x7a6e_2026);
        let cases: &[(u32, &[u64], &[u64], (u64, u64), (u64, u64), &[(u64, usize)])] = &[
            (4, &[0, 1, 2], &[3, 7], (2, 0), (1, 10), &[(9, 2), (10, 3)]),
            (
                5,
                &[0, 1, 2, 3, 5],
                &[6],
                (7, 12),
                (6, 16),
                &[(3, 1), (4, 3), (8, 1)],
            ),
        ];
        for &(genus, roots1, roots2, anchor, tangent, expected) in cases {
            let curve = SuperellipticCurve::new(
                field,
                3,
                vec![
                    (split_poly(&field, roots1), 1),
                    (split_poly(&field, roots2), 2),
                ],
            )
            .unwrap();
            let chart = TrigonalPlaneChart::new(&curve).unwrap();
            let divisor = chart
                .affine_line_divisor(&curve, tangent.0, tangent.1, &mut rng)
                .unwrap();
            let mut actual: Vec<_> = divisor
                .iter()
                .map(|(place, mult)| (field.neg(place.norm(&field).c[0]), *mult))
                .collect();
            actual.sort_unstable();
            assert_eq!(actual, expected, "genus {genus}");
            let base = build_factor_base(&curve, 1, &mut rng).unwrap();
            let row = chart
                .affine_line_relation(&curve, &base, anchor, tangent, &mut rng)
                .unwrap();
            assert!(row
                .coeffs
                .iter()
                .any(|&(_, coefficient)| coefficient.abs() >= 2));
            let value = row.coeffs.iter().fold(curve.identity(), |acc, &(i, c)| {
                let term = curve.scalar_mul(&BigUint::from(c.unsigned_abs()), &base.places[i].elem);
                curve.add(&acc, &if c < 0 { curve.neg(&term) } else { term })
            });
            assert!(curve.is_identity(&value), "genus {genus}");
        }
    }

    #[test]
    fn plane_line_rows_feed_a_verified_trigonal_dlp() {
        // Public panel curve: #Jac(F_7)=83088=144*577 (order candidate).
        // The test independently checks the chosen generator's prime order
        // and verifies the returned scalar against the target group element.
        let field = Fp::new(7).unwrap();
        let curve = SuperellipticCurve::new(
            field,
            3,
            vec![
                (Poly::from_coeffs(vec![4, 3, 6, 0, 5, 1], &field), 1),
                (Poly::from_coeffs(vec![4, 1], &field), 2),
            ],
        )
        .unwrap();
        assert_eq!(curve.genus, 5);
        let chart = TrigonalPlaneChart::new(&curve).unwrap();
        let mut rng = StdRng::seed_from_u64(0x2026_577);
        let base = build_factor_base(&curve, 1, &mut rng).unwrap();
        let mut line_scan = chart.collect_affine_line_relations(&curve, &base, 49, &mut rng);
        assert!(!line_scan.relations.is_empty());
        line_scan.relations.push(
            chart
                .vertical_line_relation(&curve, &base, 0, 1, &mut rng)
                .unwrap(),
        );
        line_scan.relations.push(
            chart
                .mixed_line_relation(&curve, &base, (0, 1), 0, &mut rng)
                .unwrap(),
        );
        let n = BigUint::from(577u64);
        let mut d1 = curve.identity();
        for _ in 0..64 {
            d1 = curve.scalar_mul(&BigUint::from(144u64), &curve.random_element(2, &mut rng));
            if !curve.is_identity(&d1) {
                break;
            }
        }
        assert!(!curve.is_identity(&d1));
        assert!(curve.is_identity(&curve.scalar_mul(&n, &d1)));
        let target = curve.scalar_mul(&BigUint::from(36u64), &d1);
        let params = IcParams {
            extra_relations: 8,
            max_trials: 100_000,
            seed: 20261128,
            ..Default::default()
        };
        let mut corrupt = line_scan.relations[0].clone();
        corrupt.coeffs[0].1 += 1;
        assert_eq!(
            index_calculus_dlp_with_seed_relations(
                &curve,
                &base,
                &d1,
                &target,
                &n,
                &[corrupt],
                &params,
            )
            .unwrap_err(),
            HgError::BadDivisor("seed relation fails group replay")
        );
        let mut invalid_index = line_scan.relations[0].clone();
        invalid_index.coeffs[0].0 = base.len();
        assert_eq!(
            index_calculus_dlp_with_seed_relations(
                &curve,
                &base,
                &d1,
                &target,
                &n,
                &[invalid_index],
                &params,
            )
            .unwrap_err(),
            HgError::BadDivisor("seed relation factor-base index out of range")
        );
        let report = index_calculus_dlp_with_seed_relations(
            &curve,
            &base,
            &d1,
            &target,
            &n,
            &line_scan.relations,
            &params,
        )
        .unwrap();
        assert_eq!(report.k, BigUint::from(36u64));
        assert_eq!(curve.scalar_mul(&report.k, &d1), target);
        assert!(report.relations >= line_scan.relations.len());
    }

    #[test]
    fn vertical_ramified_fibers_give_verified_rows() {
        let field = Fp::new(17).unwrap();
        let mut rng = StdRng::seed_from_u64(0x2026_11ab);
        for (genus, roots1, roots2, exceptional, partial) in [
            (4, vec![0, 1, 2], vec![3, 7], 3, 5),
            (5, vec![0, 1, 2, 3, 5], vec![6], 6, 9),
        ] {
            let curve = SuperellipticCurve::new(
                field,
                3,
                vec![
                    (split_poly(&field, &roots1), 1),
                    (split_poly(&field, &roots2), 2),
                ],
            )
            .unwrap();
            let chart = TrigonalPlaneChart::new(&curve).unwrap();
            let base = build_factor_base(&curve, 1, &mut rng).unwrap();
            let exceptional_fiber = chart
                .vertical_divisor(&curve, exceptional, &mut rng)
                .unwrap();
            assert_eq!(exceptional_fiber.len(), 1);
            assert_eq!(exceptional_fiber[0].1, 3);
            assert_eq!(
                field.neg(exceptional_fiber[0].0.norm(&field).c[0]),
                exceptional
            );
            assert!(chart.vertical_divisor(&curve, partial, &mut rng).is_none());
            for x in [0, 1] {
                let divisor = chart.vertical_divisor(&curve, x, &mut rng).unwrap();
                assert_eq!(divisor.len(), 1);
                assert_eq!(divisor[0].1, 3);
                assert_eq!(field.neg(divisor[0].0.norm(&field).c[0]), x);
            }
            for b in [1, exceptional] {
                let row = chart
                    .vertical_line_relation(&curve, &base, 0, b, &mut rng)
                    .unwrap();
                assert_eq!(row.coeffs.len(), 2);
                assert!(row
                    .coeffs
                    .iter()
                    .all(|&(_, coefficient)| coefficient.abs() == 3));
                assert!(row.alpha.is_zero() && row.beta.is_zero());
                let value = row.coeffs.iter().fold(curve.identity(), |acc, &(i, c)| {
                    let term =
                        curve.scalar_mul(&BigUint::from(c.unsigned_abs()), &base.places[i].elem);
                    curve.add(&acc, &if c < 0 { curve.neg(&term) } else { term })
                });
                assert!(curve.is_identity(&value), "genus {genus}");
            }
            assert_eq!(
                chart.vertical_divisor(&curve, 17, &mut rng).unwrap()[0].1,
                3
            );
        }
    }

    #[test]
    fn mixed_line_rows_include_exceptional_pole_places() {
        let field = Fp::new(17).unwrap();
        let mut rng = StdRng::seed_from_u64(0x2026_11ac);
        for (genus, roots1, roots2, affine_lines) in [
            (4, vec![0, 1, 2], vec![3, 7], [(0, 0), (2, 0)]),
            (5, vec![0, 1, 2, 3, 5], vec![6], [(0, 0), (7, 12)]),
        ] {
            let curve = SuperellipticCurve::new(
                field,
                3,
                vec![
                    (split_poly(&field, &roots1), 1),
                    (split_poly(&field, &roots2), 2),
                ],
            )
            .unwrap();
            let chart = TrigonalPlaneChart::new(&curve).unwrap();
            let base = build_factor_base(&curve, 1, &mut rng).unwrap();
            assert_eq!(
                chart.affine_infinity_pole_order(0),
                if genus == 4 { 1 } else { 4 }
            );
            assert_eq!(
                chart.affine_infinity_pole_order(1),
                if genus == 4 { 3 } else { 4 }
            );
            for line in affine_lines {
                let row = chart
                    .mixed_line_relation(&curve, &base, line, 0, &mut rng)
                    .unwrap();
                assert!(!row.coeffs.is_empty());
                assert!(row.alpha.is_zero() && row.beta.is_zero());
                let value = row.coeffs.iter().fold(curve.identity(), |acc, &(i, c)| {
                    let term =
                        curve.scalar_mul(&BigUint::from(c.unsigned_abs()), &base.places[i].elem);
                    curve.add(&acc, &if c < 0 { curve.neg(&term) } else { term })
                });
                assert!(curve.is_identity(&value), "genus {genus}, line {line:?}");
            }
        }
        let field = Fp::new(11).unwrap();
        let curve = SuperellipticCurve::new(
            field,
            3,
            vec![
                (split_poly(&field, &[0, 1, 2]), 1),
                (Poly::from_coeffs(vec![1, 0, 1], &field), 2),
            ],
        )
        .unwrap();
        let chart = TrigonalPlaneChart::new(&curve).unwrap();
        let base = build_factor_base(&curve, 1, &mut rng).unwrap();
        assert!(chart
            .mixed_line_relation(&curve, &base, (0, 0), 0, &mut rng)
            .is_none());
        let extended = build_factor_base(&curve, 2, &mut rng).unwrap();
        let row = chart
            .mixed_line_relation(&curve, &extended, (0, 0), 0, &mut rng)
            .unwrap();
        assert!(!row.coeffs.is_empty());
        let value = row.coeffs.iter().fold(curve.identity(), |acc, &(i, c)| {
            let term = curve.scalar_mul(&BigUint::from(c.unsigned_abs()), &extended.places[i].elem);
            curve.add(&acc, &if c < 0 { curve.neg(&term) } else { term })
        });
        assert!(curve.is_identity(&value));
    }

    #[test]
    fn genus_four_plane_line_rows_feed_a_verified_dlp() {
        let field = Fp::new(17).unwrap();
        let curve = SuperellipticCurve::new(
            field,
            3,
            vec![
                (split_poly(&field, &[0, 1, 2]), 1),
                (split_poly(&field, &[3, 7]), 2),
            ],
        )
        .unwrap();
        let chart = TrigonalPlaneChart::new(&curve).unwrap();
        let mut rng = StdRng::seed_from_u64(0x2026_04d1);
        let base = build_factor_base(&curve, 1, &mut rng).unwrap();
        let params = IcParams {
            extra_relations: 16,
            max_trials: 200_000,
            seed: 0x2026_04d1,
            ..Default::default()
        };
        let candidate = index_calculus_group_order(&curve, &base, &params).unwrap();
        assert!(candidate.within_hasse_weil);
        let (n, cofactor) = largest_prime_factor(&candidate.order, 1_000_000).unwrap();
        assert!(
            n > BigUint::from(7u64),
            "candidate order {} has largest prime factor {n}",
            candidate.order
        );
        let mut d1 = curve.identity();
        for _ in 0..64 {
            let trial = curve.scalar_mul(&cofactor, &curve.random_element(2, &mut rng));
            if !curve.is_identity(&trial) && curve.is_identity(&curve.scalar_mul(&n, &trial)) {
                d1 = trial;
                break;
            }
        }
        assert!(!curve.is_identity(&d1));
        let target = curve.scalar_mul(&BigUint::from(7u64), &d1);
        assert!(!curve.is_identity(&target));
        let mut seeds = chart
            .collect_affine_line_relations(&curve, &base, 289, &mut rng)
            .relations;
        seeds.push(
            chart
                .vertical_line_relation(&curve, &base, 0, 3, &mut rng)
                .unwrap(),
        );
        seeds.push(
            chart
                .mixed_line_relation(&curve, &base, (2, 0), 0, &mut rng)
                .unwrap(),
        );
        let report = index_calculus_dlp_with_seed_relations(
            &curve, &base, &d1, &target, &n, &seeds, &params,
        )
        .unwrap();
        assert_eq!(report.k, BigUint::from(7u64));
        assert_eq!(curve.scalar_mul(&report.k, &d1), target);
        assert!(report.relations >= seeds.len());

        // A separate subgroup target has degree-one normalized support.
        // Its target coefficient comes directly from that public ideal.
        let smooth_target = curve.scalar_mul(&BigUint::from(2u64), &d1);
        let target_row = chart
            .direct_target_relation(&curve, &base, &smooth_target, &mut rng)
            .unwrap();
        assert_eq!(target_row.beta, BigUint::from(1u32));
        let mut direct_seeds = seeds;
        direct_seeds.push(target_row);
        let direct_report = index_calculus_dlp_with_seed_relations(
            &curve,
            &base,
            &d1,
            &smooth_target,
            &n,
            &direct_seeds,
            &params,
        )
        .unwrap();
        assert_eq!(direct_report.k, BigUint::from(2u64));
        assert_eq!(curve.scalar_mul(&direct_report.k, &d1), smooth_target);
    }

    #[test]
    fn direct_target_descent_replays_ordinary_and_exceptional_places() {
        let field = Fp::new(17).unwrap();
        let mut rng = StdRng::seed_from_u64(0x2026_11d2);
        for (roots1, roots2) in [(vec![0, 1, 2], vec![3, 7]), (vec![0, 1, 2, 3, 5], vec![6])] {
            let curve = SuperellipticCurve::new(
                field,
                3,
                vec![
                    (split_poly(&field, &roots1), 1),
                    (split_poly(&field, &roots2), 2),
                ],
            )
            .unwrap();
            let chart = TrigonalPlaneChart::new(&curve).unwrap();
            let base = build_factor_base(&curve, 1, &mut rng).unwrap();
            let ordinary = chart.source_place(&curve, 0, 0, &mut rng).unwrap();
            let exceptional = chart.vertical_divisor(&curve, roots2[0], &mut rng).unwrap();
            assert_eq!(exceptional.len(), 1);
            assert_eq!(exceptional[0].1, 3);
            let target = curve.add(&ordinary, &exceptional[0].0);
            assert!(!curve.is_identity(&target));
            let relation = chart
                .direct_target_relation(&curve, &base, &target, &mut rng)
                .unwrap();
            assert_eq!(relation.alpha, BigUint::zero());
            assert_eq!(relation.beta, BigUint::from(1u32));
            let replay = relation
                .coeffs
                .iter()
                .fold(curve.identity(), |acc, &(i, c)| {
                    assert!(c > 0);
                    let mut sum = acc;
                    for _ in 0..c {
                        sum = curve.add(&sum, &base.places[i].elem);
                    }
                    sum
                });
            assert_eq!(replay, target);
        }
    }

    #[test]
    fn degree_two_target_support_is_certified_in_the_plane_chart() {
        let field = Fp::new(11).unwrap();
        let mut rng = StdRng::seed_from_u64(0x2026_112a);
        let f2 = Poly::from_coeffs(vec![1, 0, 1], &field);
        assert_eq!(f2.degree(), Some(2));
        let curve = SuperellipticCurve::new(
            field,
            3,
            vec![(split_poly(&field, &[0, 1, 2]), 1), (f2.clone(), 2)],
        )
        .unwrap();
        let chart = TrigonalPlaneChart::new(&curve).unwrap();
        let degree_one = build_factor_base(&curve, 1, &mut rng).unwrap();
        let degree_two = build_factor_base(&curve, 2, &mut rng).unwrap();
        let replay = |target: &Ideal, row: &Relation| {
            assert_eq!(row.beta, BigUint::from(1u32));
            let mut sum = curve.identity();
            for &(i, coefficient) in &row.coeffs {
                assert!(coefficient > 0);
                for _ in 0..coefficient {
                    sum = curve.add(&sum, &degree_two.places[i].elem);
                }
            }
            assert_eq!(&sum, target);
        };

        let ramified = curve.places_above(&f2, &mut rng);
        assert_eq!(ramified.len(), 1);
        assert!(ramified[0].1.is_zero());
        let exceptional = curve.canonical(&ramified[0].0);
        assert!(chart
            .direct_target_relation(&curve, &degree_one, &exceptional, &mut rng)
            .is_none());
        let exceptional_row = chart
            .direct_target_relation(&curve, &degree_two, &exceptional, &mut rng)
            .unwrap();
        replay(&exceptional, &exceptional_row);

        let mut ordinary = None;
        for pi in Poly::all_monic_irreducibles(2, &field) {
            if f2.rem(&pi, &field).is_zero() {
                continue;
            }
            for (place, _) in curve.places_above(&pi, &mut rng) {
                let target = curve.canonical(&place);
                if chart
                    .direct_target_relation(&curve, &degree_one, &target, &mut rng)
                    .is_some()
                {
                    continue;
                }
                if let Some(row) =
                    chart.direct_target_relation(&curve, &degree_two, &target, &mut rng)
                {
                    ordinary = Some((target, row));
                    break;
                }
            }
            if ordinary.is_some() {
                break;
            }
        }
        let (target, row) = ordinary.expect("no ordinary degree-two target place");
        replay(&target, &row);
    }

    fn check_quadratic_target_descends(
        roots1: &[u64],
        roots2: &[u64],
        anchor: (u64, u64),
        seed: u64,
    ) {
        let field = Fp::new(17).unwrap();
        let mut rng = StdRng::seed_from_u64(seed);
        let curve = SuperellipticCurve::new(
            field,
            3,
            vec![
                (split_poly(&field, roots1), 1),
                (split_poly(&field, roots2), 2),
            ],
        )
        .unwrap();
        let chart = TrigonalPlaneChart::new(&curve).unwrap();
        let base = build_factor_base(&curve, 1, &mut rng).unwrap();
        assert!(chart
            .affine_line_divisor(&curve, anchor.0, anchor.1, &mut rng)
            .is_some());
        let mut found = None;
        'lines: for slope in 1..field.p() {
            for intercept in 0..field.p() {
                let line = Poly::from_coeffs(vec![intercept, slope], &field);
                let h = chart.f1.sub(
                    &chart
                        .f2
                        .mul(&line.mul(&line, &field).mul(&line, &field), &field),
                    &field,
                );
                let factors = h.factor(&field, &mut rng);
                if factors
                    .iter()
                    .filter(|(pi, _)| pi.degree() == Some(2))
                    .count()
                    != 1
                    || factors
                        .iter()
                        .any(|(pi, m)| pi.degree().unwrap_or(0) > 2 || *m != 1)
                {
                    continue;
                }
                let pi = &factors
                    .iter()
                    .find(|(pi, _)| pi.degree() == Some(2))
                    .unwrap()
                    .0;
                for (place, residue) in curve.places_above(pi, &mut rng) {
                    if chart.quadratic_plane_u(pi, &residue) != Some(line.clone()) {
                        continue;
                    }
                    let target = curve.canonical(&place);
                    if let Some(row) = chart
                        .descend_quadratic_target_line(&curve, &base, &target, anchor, &mut rng)
                    {
                        found = Some((target, row));
                        break 'lines;
                    }
                }
            }
        }
        let (target, row) = found.expect("no split residual cubic for a quadratic target");
        assert_eq!(row.beta, BigUint::from(1u32));
        assert!(chart
            .descend_quadratic_target_line_bounded(&curve, &base, &target, 0, &mut rng)
            .is_none());
        let searched = chart
            .descend_quadratic_target_line_bounded(
                &curve,
                &base,
                &target,
                (field.p() * field.p()) as usize,
                &mut rng,
            )
            .expect("bounded anchor scan did not find a split line");
        assert_eq!(searched.beta, BigUint::from(1u32));
        assert!(chart
            .direct_target_relation(&curve, &base, &target, &mut rng)
            .is_none());
        if chart.genus == 4 {
            assert!(chart
                .descend_quadratic_target_line(&curve, &base, &target, (0, 0), &mut rng)
                .is_none());
        }
        let replay = row
            .coeffs
            .iter()
            .fold(curve.identity(), |sum, &(i, coefficient)| {
                let mut sum = sum;
                let term = &base.places[i].elem;
                for _ in 0..coefficient.unsigned_abs() {
                    sum = curve.add(
                        &sum,
                        &if coefficient < 0 {
                            curve.neg(term)
                        } else {
                            term.clone()
                        },
                    );
                }
                sum
            });
        assert_eq!(replay, target);
        let searched_replay =
            searched
                .coeffs
                .iter()
                .fold(curve.identity(), |sum, &(i, coefficient)| {
                    let mut sum = sum;
                    let term = &base.places[i].elem;
                    for _ in 0..coefficient.unsigned_abs() {
                        sum = curve.add(
                            &sum,
                            &if coefficient < 0 {
                                curve.neg(term)
                            } else {
                                term.clone()
                            },
                        );
                    }
                    sum
                });
        assert_eq!(searched_replay, target);
    }

    #[test]
    fn quadratic_target_descends_to_degree_one_line_places() {
        check_quadratic_target_descends(&[0, 1, 2], &[3, 7], (2, 0), 0x2026_11d3);
        check_quadratic_target_descends(&[0, 1, 2, 3, 5], &[6], (7, 12), 0x2026_11d4);
    }
}
