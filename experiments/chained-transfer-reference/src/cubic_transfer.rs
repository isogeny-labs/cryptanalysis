//! Bounded arbitrary-divisor norm on y²=f(x³), with genuine closed support.
//! Reuses pre-existing checked BigUint Cantor and polynomial arithmetic.
//! No DLP solver, scalar label or benchmark is used by a map evaluation.
use super::reference::{FpPoly, HyperellipticCurveP as Curve, MumfordDivisorP as Divisor};
use num_bigint::BigUint;
use num_traits::{One, Zero};
type Result<T> = std::result::Result<T, String>;
type ExtensionPoint = Option<(FpPoly, FpPoly)>;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Class {
    level: usize,
    polynomial: FpPoly,
    d: Divisor,
}
impl Class {
    pub fn degree(&self) -> usize {
        self.d.u.degree().unwrap()
    }
}

pub struct CubicChain {
    curves: [Curve; 3],
    p: u64,
}
fn power_substitution(f: &FpPoly, k: usize) -> FpPoly {
    if f.is_zero() {
        return FpPoly::zero(f.p.clone());
    }
    let mut out = vec![BigUint::zero(); k * f.degree().unwrap() + 1];
    for (i, c) in f.coeffs.iter().enumerate() {
        out[k * i] = c.clone();
    }
    FpPoly::from_coeffs(out, f.p.clone())
}
fn deflate(f: &FpPoly, k: usize) -> Result<FpPoly> {
    if f.coeffs
        .iter()
        .enumerate()
        .any(|(i, c)| i % k != 0 && !c.is_zero())
    {
        return Err("class is outside the coefficient image".into());
    }
    Ok(FpPoly::from_coeffs(
        f.coeffs.iter().step_by(k).cloned().collect(),
        f.p.clone(),
    ))
}

impl CubicChain {
    pub fn new(p: u64, a: u64, b: u64) -> Result<Self> {
        if !(5..=101).contains(&p) || b.is_multiple_of(p) {
            return Err("prototype requires prime5..101 and nonzero constant".into());
        }
        let modulus = BigUint::from(p);
        let f = FpPoly::from_coeffs(
            [b, a, 0, 1].into_iter().map(BigUint::from).collect(),
            modulus.clone(),
        );
        let base = Curve::try_new(modulus.clone(), f, 1).map_err(|e| e.to_string())?;
        let cover = Curve::try_new(modulus.clone(), power_substitution(&base.f, 3), 4)
            .map_err(|e| e.to_string())?;
        let next = Curve::try_new(modulus, power_substitution(&cover.f, 3), 13)
            .map_err(|e| e.to_string())?;
        Ok(Self {
            curves: [base, cover, next],
            p,
        })
    }
    fn wrap(&self, level: usize, d: Divisor) -> Result<Class> {
        let curve = self.curves.get(level).ok_or("unknown curve level")?;
        d.validate(curve).map_err(|e| e.to_string())?;
        Ok(Class {
            level,
            polynomial: curve.f.clone(),
            d,
        })
    }
    fn check(&self, d: &Class) -> Result<&Curve> {
        let curve = self.curves.get(d.level).ok_or("unknown curve level")?;
        if curve.f != d.polynomial {
            return Err("curve/field tag mismatch".into());
        }
        d.d.validate(curve).map_err(|e| e.to_string())?;
        Ok(curve)
    }
    fn zero(&self, level: usize) -> Class {
        self.wrap(level, Divisor::identity(BigUint::from(self.p)))
            .unwrap()
    }
    pub fn point(&self, level: usize, x: u64, y: u64) -> Result<Class> {
        let curve = self.curves.get(level).ok_or("unknown curve level")?;
        self.wrap(
            level,
            Divisor::try_from_point(curve, &BigUint::from(x), &BigUint::from(y))
                .map_err(|e| e.to_string())?,
        )
    }
    pub fn add(&self, a: &Class, b: &Class) -> Result<Class> {
        let curve = self.check(a)?;
        self.check(b)?;
        if a.level != b.level {
            return Err("curve level mismatch".into());
        }
        self.wrap(
            a.level,
            a.d.checked_add(&b.d, curve).map_err(|e| e.to_string())?,
        )
    }
    pub fn neg(&self, d: &Class) -> Result<Class> {
        let curve = self.check(d)?;
        self.wrap(d.level, d.d.checked_neg(curve).map_err(|e| e.to_string())?)
    }
    pub fn mul(&self, d: &Class, n: u64) -> Result<Class> {
        let curve = self.check(d)?;
        self.wrap(
            d.level,
            d.d.checked_scalar_mul(&BigUint::from(n), curve)
                .map_err(|e| e.to_string())?,
        )
    }
    /// Whole-fiber pullback, including nonsplit and ramified support. The
    /// degree bound3g <=3g+1 makes this already reduced on the target.
    pub fn pull(&self, d: &Class) -> Result<Class> {
        self.check(d)?;
        if d.level >= 2 {
            return Err("no next cover".into());
        }
        let target = &self.curves[d.level + 1];
        self.wrap(
            d.level + 1,
            Divisor::try_from_polynomials(
                target,
                power_substitution(&d.d.u, 3),
                power_substitution(&d.d.v, 3),
            )
            .map_err(|e| e.to_string())?,
        )
    }
    /// Image-restricted inverse; this is not a global norm on genus13.
    pub fn recover_image(&self, d: &Class) -> Result<Class> {
        self.check(d)?;
        if d.level == 0 {
            return Err("not a pullback target".into());
        }
        let source = &self.curves[d.level - 1];
        let back = self.wrap(
            d.level - 1,
            Divisor::try_from_polynomials(source, deflate(&d.d.u, 3)?, deflate(&d.d.v, 3)?)
                .map_err(|e| e.to_string())?,
        )?;
        if self.pull(&back)? != *d {
            return Err("class is outside the exact image".into());
        }
        Ok(back)
    }
    /// Actual divisor norm on the ENTIRE canonical genus4 domain. Every
    /// irreducible support factor is traced in its own residue field.
    pub fn norm(&self, d: &Class) -> Result<(Class, Vec<(usize, u32)>)> {
        self.check(d)?;
        if d.level != 1 {
            return Err("arbitrary-class norm is implemented only for genus4".into());
        }
        let (out, degrees) = norm_power_support(&self.curves[0], &d.d.u, &d.d.v, self.p, 3)?;
        Ok((self.wrap(0, out)?, degrees))
    }
    pub fn rational_points(&self, level: usize) -> Result<Vec<Class>> {
        let curve = self.curves.get(level).ok_or("unknown curve level")?;
        let mut out = vec![self.zero(level)];
        for x in 0..self.p {
            let rhs = curve.f.eval(&BigUint::from(x));
            for y in 0..self.p {
                if BigUint::from(y * y % self.p) == rhs {
                    out.push(self.point(level, x, y)?);
                }
            }
        }
        Ok(out)
    }
}

/// Shared finite-support pushforward for (x,y) -> (x^power,y). Callers
/// validate their source model and its infinity contribution separately.
/// Degree<=4 factorization and elliptic target arithmetic are unchanged.
pub(super) fn norm_power_support(
    target: &Curve,
    u: &FpPoly,
    v: &FpPoly,
    p: u64,
    power: u64,
) -> Result<(Divisor, Vec<(usize, u32)>)> {
    target.validate().map_err(|e| e.to_string())?;
    if target.genus != 1 || target.p != BigUint::from(p) || u.p != target.p || v.p != target.p {
        return Err("finite norm target/field mismatch".into());
    }
    let factors = factor_at_most_four(u, p)?;
    let mut out = Divisor::identity(target.p.clone());
    let mut degrees = vec![];
    for (q, e) in factors {
        let degree = q.degree().unwrap();
        degrees.push((degree, e));
        let ext = Extension { q };
        let x = ext.reduce(&FpPoly::x(target.p.clone()));
        let mut point = Some((ext.pow(&x, power), ext.reduce(v)));
        if !ext.on_curve(&point, &target.f) {
            return Err("projected support outside elliptic curve".into());
        }
        let original = point.clone();
        let mut sum = None;
        for _ in 0..degree {
            sum = ext.add_points(&sum, &point, &target.f)?;
            point = point.map(|(x, y)| (ext.pow(&x, p), ext.pow(&y, p)));
        }
        if point != original {
            return Err("support Frobenius orbit did not close".into());
        }
        let trace = match sum {
            None => Divisor::identity(target.p.clone()),
            Some((x, y)) => {
                if x.coeffs.len() > 1 || y.coeffs.len() > 1 {
                    return Err("elliptic trace did not descend".into());
                }
                Divisor::try_from_point(target, &x.coeff(0), &y.coeff(0))
                    .map_err(|e| e.to_string())?
            }
        };
        let contribution = trace
            .checked_scalar_mul(&BigUint::from(e), target)
            .map_err(|e| e.to_string())?;
        out = out
            .checked_add(&contribution, target)
            .map_err(|e| e.to_string())?;
    }
    Ok((out, degrees))
}

/// Complete bounded factorization: strip all linear factors; a remaining
/// degree2/3 polynomial is irreducible, and degree4 needs only quadratic
/// divisibility checks. Multiplicities are preserved. No heuristic factor
/// choice or rational-root-only omission is permitted.
fn factor_at_most_four(u: &FpPoly, p: u64) -> Result<Vec<(FpPoly, u32)>> {
    if p > 101 || u.degree().is_none_or(|d| d > 4) || u.is_zero() || u.lead() != BigUint::one() {
        return Err("norm factorization domain exceeded".into());
    }
    let mut remaining = u.clone();
    let mut out = vec![];
    for root in 0..p {
        let q = FpPoly::from_coeffs(
            vec![BigUint::from((p - root) % p), BigUint::one()],
            BigUint::from(p),
        );
        let mut e = 0;
        while remaining.degree().unwrap() > 0 {
            let (d, r) = remaining.divrem(&q);
            if !r.is_zero() {
                break;
            }
            remaining = d;
            e += 1;
        }
        if e > 0 {
            out.push((q, e));
        }
    }
    if remaining.degree() == Some(4) {
        'factor: for b in 0..p {
            for c in 0..p {
                let q = FpPoly::from_coeffs(
                    vec![BigUint::from(c), BigUint::from(b), BigUint::one()],
                    BigUint::from(p),
                );
                let mut e = 0;
                while remaining.degree().unwrap() >= 2 {
                    let (d, r) = remaining.divrem(&q);
                    if !r.is_zero() {
                        break;
                    }
                    remaining = d;
                    e += 1;
                }
                if e > 0 {
                    out.push((q, e));
                    break 'factor;
                }
            }
        }
    }
    if remaining.degree().unwrap() > 0 {
        out.push((remaining, 1));
    }
    let mut product = FpPoly::one(BigUint::from(p));
    for (q, e) in &out {
        for _ in 0..*e {
            product = product.mul(q);
        }
    }
    if product != *u {
        return Err("support factorization did not reconstruct u".into());
    }
    Ok(out)
}

struct Extension {
    q: FpPoly,
}
impl Extension {
    fn zero(&self) -> FpPoly {
        FpPoly::zero(self.q.p.clone())
    }
    fn one(&self) -> FpPoly {
        FpPoly::one(self.q.p.clone())
    }
    fn constant(&self, n: u64) -> FpPoly {
        FpPoly::from_coeffs(vec![BigUint::from(n)], self.q.p.clone())
    }
    fn reduce(&self, a: &FpPoly) -> FpPoly {
        a.divrem(&self.q).1
    }
    fn mul(&self, a: &FpPoly, b: &FpPoly) -> FpPoly {
        self.reduce(&a.mul(b))
    }
    fn pow(&self, a: &FpPoly, mut n: u64) -> FpPoly {
        let mut a = self.reduce(a);
        let mut out = self.one();
        while n != 0 {
            if n & 1 != 0 {
                out = self.mul(&out, &a);
            }
            a = self.mul(&a, &a);
            n >>= 1;
        }
        out
    }
    fn inv(&self, a: &FpPoly) -> Result<FpPoly> {
        let (g, s, _) = a.ext_gcd(&self.q);
        if g != self.one() {
            return Err("nonunit in closed-point residue field".into());
        }
        Ok(self.reduce(&s))
    }
    fn coefficient(&self, f: &FpPoly, i: usize) -> FpPoly {
        FpPoly::from_coeffs(
            vec![f.coeffs.get(i).cloned().unwrap_or_default()],
            self.q.p.clone(),
        )
    }
    fn on_curve(&self, p: &ExtensionPoint, f: &FpPoly) -> bool {
        p.as_ref().is_none_or(|(x, y)| {
            let mut rhs = self.zero();
            for c in f.coeffs.iter().rev() {
                rhs = self
                    .mul(&rhs, x)
                    .add(&FpPoly::from_coeffs(vec![c.clone()], self.q.p.clone()));
            }
            self.mul(y, y) == rhs
        })
    }
    fn add_points(
        &self,
        p: &ExtensionPoint,
        q: &ExtensionPoint,
        f: &FpPoly,
    ) -> Result<ExtensionPoint> {
        let ((x, y), (u, v)) = match (p, q) {
            (None, _) => return Ok(q.clone()),
            (_, None) => return Ok(p.clone()),
            (Some(p), Some(q)) => (p, q),
        };
        if x == u && y.add(v).is_zero() {
            return Ok(None);
        }
        let a2 = self.coefficient(f, 2);
        let a4 = self.coefficient(f, 1);
        let slope = if x == u {
            if y != v {
                return Err("invalid coincident elliptic x coordinates".into());
            }
            let numerator = self
                .mul(&self.constant(3), &self.mul(x, x))
                .add(&self.mul(&self.constant(2), &self.mul(&a2, x)))
                .add(&a4);
            self.mul(&numerator, &self.inv(&self.mul(&self.constant(2), y))?)
        } else {
            self.mul(&v.sub(y), &self.inv(&u.sub(x))?)
        };
        let xx = self.mul(&slope, &slope).sub(&a2).sub(x).sub(u);
        let yy = self.mul(&slope, &x.sub(&xx)).sub(y);
        let result = Some((xx, yy));
        if !self.on_curve(&result, f) {
            return Err("elliptic trace addition left curve".into());
        }
        Ok(result)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn prime_order_source_and_quadratic_constructor_obstruction() {
        let c = CubicChain::new(101, 1, 46).unwrap();
        let points = c.rational_points(0).unwrap();
        assert_eq!(points.len(), 109);
        let g = c.point(0, 2, 37).unwrap();
        assert_ne!(g, c.zero(0));
        assert_eq!(c.mul(&g, 109).unwrap(), c.zero(0));
        assert_eq!(
            points.iter().filter(|d| c.neg(d).unwrap() == **d).count(),
            1
        );
        let sextic = power_substitution(&c.curves[0].f, 2);
        assert!((0_u64..101).all(|x| !sextic.eval(&BigUint::from(x)).is_zero()));
        for b in 0_u64..101 {
            for a in 0_u64..101 {
                let q = FpPoly::from_coeffs(
                    vec![BigUint::from(a), BigUint::from(b), BigUint::one()],
                    BigUint::from(101_u32),
                );
                assert!(!sextic.divrem(&q).1.is_zero());
            }
        }
        println!("PASS full source order109, no finite2-torsion, no rational branch point or quadratic divisor of f(x²); this restricts individually rational Richelot factors, not all Galois-stable kernels");
    }
    #[test]
    fn every_source_scalar_whole_fibers_and_chain_recovery() {
        let c = CubicChain::new(101, 1, 46).unwrap();
        let g = c.point(0, 2, 37).unwrap();
        for k in 0..109 {
            let d = c.mul(&g, k).unwrap();
            let image = c.pull(&d).unwrap();
            let next = c.pull(&image).unwrap();
            assert_eq!(c.recover_image(&image).unwrap(), d);
            assert_eq!(c.recover_image(&next).unwrap(), image);
            let (norm, _) = c.norm(&image).unwrap();
            assert_eq!(norm, c.mul(&d, 3).unwrap());
            assert_eq!(c.mul(&norm, 73).unwrap(), d);
            let restricted_second_norm = c.mul(&c.recover_image(&next).unwrap(), 3).unwrap();
            let (composed, _) = c.norm(&restricted_second_norm).unwrap();
            assert_eq!(composed, c.mul(&d, 9).unwrap());
            assert_eq!(c.mul(&composed, 97).unwrap(), d);
        }
        assert!(c.norm(&c.zero(2)).is_err());
        for point in c.rational_points(2).unwrap().into_iter().skip(1) {
            assert!(c.recover_image(&point).is_err());
        }
        println!("PASS all109 source scalars, complete cubic fibers, genera4/13 chain, actual first norm[3] and image-restricted second norm/composed[9]; point recovery only");
    }
    #[test]
    fn arbitrary_genus_four_norm_and_witnesses() {
        let c = CubicChain::new(101, 1, 46).unwrap();
        let a = c.point(1, 26, 37).unwrap();
        let b = c.point(1, 4, 19).unwrap();
        let g = c.point(0, 2, 37).unwrap();
        let q = c.point(0, 64, 19).unwrap();
        let mut covered = std::collections::BTreeSet::new();
        let mut witness=String::from("# chained-cubic-norm-witness/v1; p101; E=y²=x³+x+46; A=(26,37); B=(4,19)\noffset\tk\tu\tv\tnorm_u\tnorm_v\tdegrees\n");
        for k in 0..=64 {
            for offset in [false, true] {
                let mut d = c.mul(&a, k).unwrap();
                let mut expected = c.mul(&g, k).unwrap();
                if offset {
                    d = c.add(&d, &b).unwrap();
                    expected = c.add(&expected, &q).unwrap();
                }
                let (norm, factors) = c.norm(&d).unwrap();
                assert_eq!(norm, expected);
                for (degree, _) in &factors {
                    covered.insert(*degree);
                }
                let next = c.pull(&d).unwrap();
                assert_eq!(c.recover_image(&next).unwrap(), d);
                let coeff = |p: &FpPoly| {
                    p.coeffs
                        .iter()
                        .map(ToString::to_string)
                        .collect::<Vec<_>>()
                        .join(",")
                };
                let degrees = factors
                    .iter()
                    .map(|(d, e)| format!("{d}^{e}"))
                    .collect::<Vec<_>>()
                    .join(";");
                witness += &format!(
                    "{}\t{k}\t{}\t{}\t{}\t{}\t{degrees}\n",
                    u8::from(offset),
                    coeff(&d.d.u),
                    coeff(&d.d.v),
                    coeff(&norm.d.u),
                    coeff(&norm.d.v)
                );
            }
        }
        assert!(
            covered.contains(&3) && covered.contains(&4),
            "retain missing closed-support coverage: {covered:?}"
        );
        if let Ok(path) = std::env::var("CHAINED_CUBIC_WITNESS_OUT") {
            std::fs::write(path, witness).unwrap();
        }
        println!("PASS130 arbitrary genus4 norms with fixed translation, closed support degrees{covered:?}, coefficient-image round trips; no scalar labels used by norm");
    }
    #[test]
    fn secondary_prime19_additivity_and_ramification() {
        let c = CubicChain::new(17, 2, 2).unwrap();
        assert_eq!(c.rational_points(0).unwrap().len(), 19);
        let g = c.point(0, 5, 1).unwrap();
        let mut images = vec![];
        for k in 0..19 {
            let d = c.mul(&g, k).unwrap();
            images.push((
                d.clone(),
                c.pull(&d).unwrap(),
                c.pull(&c.pull(&d).unwrap()).unwrap(),
            ));
        }
        for (a, b, z) in &images {
            for (x, y, w) in &images {
                assert_eq!(c.pull(&c.add(a, x).unwrap()).unwrap(), c.add(b, y).unwrap());
                assert_eq!(c.pull(&c.add(b, y).unwrap()).unwrap(), c.add(z, w).unwrap());
            }
        }
        let ramified = c.point(1, 0, 6).unwrap();
        let base = c.point(0, 0, 6).unwrap();
        let mut max_degree = 0;
        for k in 0..=16 {
            let d = c.mul(&ramified, k).unwrap();
            let image = c.pull(&d).unwrap();
            max_degree = max_degree.max(image.degree());
            assert_eq!(c.recover_image(&image).unwrap(), d);
            assert_eq!(c.norm(&d).unwrap().0, c.mul(&base, k).unwrap());
        }
        assert_eq!(max_degree, 12);
        assert!(CubicChain::new(3, 1, 1).is_err());
        assert!(CubicChain::new(101, 1, 0).is_err());
        assert!(c.add(&g, &ramified).is_err());
        println!("PASS all361 ordered prime19 subgroup pairs through both pullbacks, ramification/multiplicity controls and degree12 target representatives");
    }
}
