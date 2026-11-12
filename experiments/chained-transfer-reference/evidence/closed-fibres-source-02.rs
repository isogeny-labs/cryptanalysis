//! Closed quadratic-source Richelot fibres over the existing coefficient field.
//! Resultant/coordinate elimination only; polynomial and Cantor engines are reused.
use super::{Class, Divisor, Jacobian, Poly, Result, RichelotMap};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(super) enum ClosedRoute {
    LowerDegree,
    Quadratic,
    ResultantDegree,
    ProjectionNonunit,
    OrdinateNonunit,
}

pub(super) enum ClosedFibre {
    Image(Divisor, ClosedRoute),
    Boundary(ClosedRoute),
}

impl RichelotMap {
    fn compose_mod(&self, p: &Poly, x: &Poly, modulus: &Poly) -> Poly {
        let k = &self.k;
        p.iter().rev().fold(vec![], |out, coefficient| {
            k.divrem(
                &k.addp(&k.mulp(&out, x), &vec![coefficient.clone()]),
                modulus,
            )
            .1
        })
    }

    fn inverse_mod(&self, p: &Poly, modulus: &Poly) -> Option<Poly> {
        let (gcd, coefficient, _) = self.k.xgcd(p, modulus);
        (gcd == vec![self.k.c(1)]).then(|| self.k.divrem(&coefficient, modulus).1)
    }

    /// Supports already in the existing Fp6 tower need no support-root search.
    /// A boundary is explicit and does not assert that the map is undefined.
    pub(super) fn closed_extension(&self, d: &Divisor, reverse: bool) -> Result<ClosedFibre> {
        let (source, target, g, h, source_scale, target_scale) = if reverse {
            (
                &self.target,
                &self.source,
                &self.h,
                &self.g,
                self.target_scale,
                1,
            )
        } else {
            (
                &self.source,
                &self.target,
                &self.g,
                &self.h,
                1,
                self.target_scale,
            )
        };
        let k = &self.k;
        Jacobian::new(k, source).check(d)?;
        let target = Jacobian::new(k, target);
        let degree = d.u.len() - 1;
        let (mut out, route) = if degree < 2 {
            let image = if degree == 0 {
                target.zero()
            } else {
                let x = k.neg(&d.u[0]);
                let y = k.mul(&k.value(&d.v, &x), &k.c(source_scale));
                self.fiber(&x, &y, g, h, target_scale, &target)?
            };
            (image, ClosedRoute::LowerDegree)
        } else {
            let left = k.divrem(&g[0], &d.u).1;
            let right = k.divrem(&g[1], &d.u).1;
            let coefficient = |p: &Poly, i| p.get(i).cloned().unwrap_or_else(|| k.c(0));
            let a = k.addp(
                &k.scale(&h[0], &coefficient(&left, 1)),
                &k.scale(&h[1], &coefficient(&right, 1)),
            );
            let b = k.addp(
                &k.scale(&h[0], &coefficient(&left, 0)),
                &k.scale(&h[1], &coefficient(&right, 0)),
            );
            // Norm of A(z)x+B(z) in K[x]/(x²+u1*x+u0).
            let resultant = k.addp(
                &k.subp(&k.mulp(&b, &b), &k.scale(&k.mulp(&a, &b), &d.u[1])),
                &k.scale(&k.mulp(&a, &a), &d.u[0]),
            );
            if resultant.len() != 5 {
                return Ok(ClosedFibre::Boundary(ClosedRoute::ResultantDegree));
            }
            let u = k.monic(&resultant);
            let Some(inverse_a) = self.inverse_mod(&a, &u) else {
                return Ok(ClosedFibre::Boundary(ClosedRoute::ProjectionNonunit));
            };
            let x = k.divrem(&k.negp(&k.mulp(&b, &inverse_a)), &u).1;
            if !self.compose_mod(&d.u, &x, &u).is_empty()
                || !k.divrem(&k.addp(&k.mulp(&a, &x), &b), &u).1.is_empty()
            {
                return Err("closed Richelot source-coordinate elimination failed".into());
            }
            let source_y = self.compose_mod(&d.v, &x, &u);
            let denominator = k.scale(&source_y, &k.c(source_scale * target_scale));
            let Some(inverse_y) = self.inverse_mod(&denominator, &u) else {
                return Ok(ClosedFibre::Boundary(ClosedRoute::OrdinateNonunit));
            };
            let x_minus_z = k.subp(&x, &vec![k.c(0), k.c(1)]);
            let numerator = k.mulp(&k.mulp(&self.compose_mod(&g[0], &x, &u), &h[0]), &x_minus_z);
            let v = k.divrem(&k.mulp(&numerator, &inverse_y), &u).1;
            if !k
                .divrem(&k.subp(&target.f, &k.mulp(&v, &v)), &u)
                .1
                .is_empty()
            {
                return Err("closed Richelot ordinate left target curve".into());
            }
            (target.reduce(u, v, -1)?, ClosedRoute::Quadratic)
        };
        let coefficient = 2 * i64::from(d.plus) + degree as i64 - 2;
        if coefficient != 0 {
            let infinity = self.infinity(g, h, source_scale, target_scale, &target)?;
            let infinity = if coefficient < 0 {
                target.neg(&infinity)
            } else {
                infinity
            };
            for _ in 0..coefficient.unsigned_abs() {
                out = target.add(&out, &infinity)?;
            }
        }
        if reverse {
            out = target.neg(&out);
        }
        target.check(&out)?;
        Ok(ClosedFibre::Image(out, route))
    }

    /// Complete prime-input adapter: every chart boundary uses the old map.
    pub(super) fn evaluate_closed(&self, d: &Class, reverse: bool) -> Result<(Class, ClosedRoute)> {
        let (source, target) = if reverse {
            (&self.target, &self.source)
        } else {
            (&self.source, &self.target)
        };
        source.check(d)?;
        let (u, v, plus) = d.components();
        let extension = Divisor {
            u: self.k.lift_poly(u),
            v: self.k.lift_poly(v),
            plus,
        };
        match self.closed_extension(&extension, reverse)? {
            ClosedFibre::Image(image, route) => Ok((
                Jacobian::new(&self.k, target).descend(&image, target)?,
                route,
            )),
            ClosedFibre::Boundary(route) => Ok((self.evaluate(d, reverse)?, route)),
        }
    }
}
