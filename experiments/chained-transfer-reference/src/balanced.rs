//! Bounded balanced genus2 arithmetic for monic smooth even sextics.
//! Galbraith corrected ch10: Definition10.4.9, Lemmas10.4.10/14,
//! Theorem10.4.19. Finite support plus both infinities are retained.
use super::cubic_transfer::norm_power_support;
use super::reference::{Fp2Ctx, FpPoly, HyperellipticCurveP as Curve, MumfordDivisorP as Divisor};
use num_bigint::BigUint;
use num_traits::{One, ToPrimitive, Zero};
use std::collections::BTreeMap;
type Result<T> = std::result::Result<T, String>;
type Key = (Vec<u64>, Vec<u64>, u8);

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Class {
    f: FpPoly,
    u: FpPoly,
    v: FpPoly,
    /// Effective degree2 divisor: D_fin + plus*inf+ + (2-deg(u)-plus)*inf-.
    /// The class subtracts K=inf+ + inf-. Identity is(u=1,v=0,plus=1).
    plus: u8,
}
impl Class {
    pub(super) fn components(&self) -> (&FpPoly, &FpPoly, u8) {
        (&self.u, &self.v, self.plus)
    }
    fn degree(&self) -> usize {
        self.u.degree().unwrap()
    }
    fn key(&self) -> Key {
        let c = |f: &FpPoly| f.coeffs.iter().map(|c| c.to_u64().unwrap()).collect();
        (c(&self.u), c(&self.v), self.plus)
    }
}

#[derive(Clone)]
pub struct Balanced {
    p: u64,
    f: FpPoly,
    polynomial_part: FpPoly,
}
fn canonical(f: &FpPoly, p: &BigUint) -> bool {
    f.p == *p && f.coeffs.iter().all(|c| c < p) && f.coeffs.last().is_none_or(|c| !c.is_zero())
}
impl Balanced {
    pub(super) fn equation_and_infinity(&self) -> (&FpPoly, &FpPoly) {
        (&self.f, &self.polynomial_part)
    }
    pub fn new(p: u64, coefficients: &[u64]) -> Result<Self> {
        if !(5..=101).contains(&p)
            || coefficients.len() != 7
            || coefficients.iter().any(|c| *c >= p)
        {
            return Err("balanced prototype requires canonical sextic over prime5..101".into());
        }
        Fp2Ctx::try_new(p).map_err(|e| e.to_string())?;
        let modulus = BigUint::from(p);
        let f = FpPoly::from_coeffs(
            coefficients.iter().copied().map(BigUint::from).collect(),
            modulus.clone(),
        );
        if f.lead() != BigUint::one() {
            return Err("only monic split-infinity sextics supported".into());
        }
        let derivative = FpPoly::from_coeffs(
            (1..7)
                .map(|i| BigUint::from(i as u64) * f.coeff(i) % &modulus)
                .collect(),
            modulus.clone(),
        );
        if f.gcd(&derivative) != FpPoly::one(modulus.clone()) {
            return Err("singular sextic".into());
        }
        let inv2 = p.div_ceil(2);
        let c2 = coefficients[5] * inv2 % p;
        let c1 = (coefficients[4] + p - c2 * c2 % p) * inv2 % p;
        let c0 = (coefficients[3] + p - 2 * c2 * c1 % p) * inv2 % p;
        let polynomial_part = FpPoly::from_coeffs(
            [c0, c1, c2, 1].into_iter().map(BigUint::from).collect(),
            modulus,
        );
        if f.sub(&polynomial_part.mul(&polynomial_part))
            .degree()
            .is_some_and(|d| d > 2)
        {
            return Err("invalid infinity expansion".into());
        }
        Ok(Self {
            p,
            f,
            polynomial_part,
        })
    }
    fn poly(&self, c: &[u64]) -> FpPoly {
        FpPoly::from_coeffs(
            c.iter().copied().map(BigUint::from).collect(),
            BigUint::from(self.p),
        )
    }
    pub(super) fn wrap(&self, u: FpPoly, v: FpPoly, plus: u8) -> Result<Class> {
        let d = Class {
            f: self.f.clone(),
            u,
            v,
            plus,
        };
        self.check(&d)?;
        Ok(d)
    }
    pub(super) fn check(&self, d: &Class) -> Result<()> {
        if d.f != self.f || !canonical(&d.u, &self.f.p) || !canonical(&d.v, &self.f.p) {
            return Err("balanced curve/field/canonical tag mismatch".into());
        }
        let m = d.u.degree().ok_or("zero support")?;
        if m > 2
            || usize::from(d.plus) + m > 2
            || d.u.lead() != BigUint::one()
            || d.v.degree().is_some_and(|n| n >= m)
        {
            return Err("noncanonical balanced degree or infinity counts".into());
        }
        if !self.f.sub(&d.v.mul(&d.v)).rem(&d.u).is_zero() {
            return Err("support does not lie on sextic".into());
        }
        Ok(())
    }
    pub fn zero(&self) -> Class {
        self.wrap(self.poly(&[1]), self.poly(&[]), 1).unwrap()
    }
    pub fn delta(&self) -> Class {
        self.wrap(self.poly(&[1]), self.poly(&[]), 2).unwrap()
    }
    pub fn point(&self, x: u64, y: u64, plus: u8) -> Result<Class> {
        if x >= self.p || y >= self.p {
            return Err("noncanonical point".into());
        }
        self.wrap(
            self.poly(&[(self.p - x) % self.p, 1]),
            self.poly(&[y]),
            plus,
        )
    }
    pub fn neg(&self, d: &Class) -> Result<Class> {
        self.check(d)?;
        self.wrap(
            d.u.clone(),
            d.v.neg().rem(&d.u),
            2 - d.degree() as u8 - d.plus,
        )
    }
    /// Semireduced affine Cantor composition; no odd-degree reduction.
    fn compose(&self, a: &Class, b: &Class) -> Result<(FpPoly, FpPoly, usize)> {
        let (d1, e1, e2) = a.u.ext_gcd(&b.u);
        let (d, c1, c2) = d1.ext_gcd(&a.v.add(&b.v));
        let exact = |a: &FpPoly, b: &FpPoly| -> Result<FpPoly> {
            let (q, r) = a.divrem(b);
            if !r.is_zero() {
                return Err("nonexact balanced composition".into());
            }
            Ok(q)
        };
        let u = exact(&a.u.mul(&b.u), &d.mul(&d))?;
        let numerator = c1
            .mul(&e1)
            .mul(&a.u)
            .mul(&b.v)
            .add(&c1.mul(&e2).mul(&b.u).mul(&a.v))
            .add(&c2.mul(&a.v.mul(&b.v).add(&self.f)));
        let v = exact(&numerator, &d)?.rem(&u);
        Ok((u, v, d.degree().unwrap()))
    }
    pub fn add(&self, a: &Class, b: &Class) -> Result<Class> {
        self.check(a)?;
        self.check(b)?;
        let (u, v, removed) = self.compose(a, b)?;
        let m = u.degree().ok_or("zero composed support")?;
        let plus = i64::from(a.plus) + i64::from(b.plus) + removed as i64 - 1;
        if m <= 2 && plus >= 0 && plus <= 2 - m as i64 {
            return self.wrap(u, v, plus as u8);
        }
        // The degree4 effective sum has only one infinity sign if it is
        // outside the reduced range. Match that branch at infinity.
        let line = if m == 4 {
            v
        } else {
            let g = if plus >= 0 {
                self.polynomial_part.clone()
            } else {
                self.polynomial_part.neg()
            };
            g.add(&v.sub(&g).rem(&u))
        };
        let numerator = self.f.sub(&line.mul(&line));
        let total = numerator.degree().ok_or("sextic became a square")?;
        let (raw, remainder) = numerator.divrem(&u);
        if !remainder.is_zero() || raw.is_zero() {
            return Err("nonexact infinity reduction".into());
        }
        let next = raw.monic();
        let r = next.degree().unwrap();
        // For line leading +1, v_inf+(y-line)=3-deg(f-line²).
        // Otherwise the positive branch has pole3. This also handles the
        // exceptional degree4 interpolation with leading coefficient +/-1.
        let valuation = if line.coeff(3) == BigUint::one() {
            3 - total as i64
        } else {
            -3
        };
        let next_plus = plus - valuation - r as i64;
        if r > 2 || next_plus < 0 || next_plus > 2 - r as i64 {
            return Err(format!(
                "unbalanced reduction m={m},n={plus},r={r},n'={next_plus}"
            ));
        }
        let next_v = line.neg().rem(&next);
        self.wrap(next, next_v, next_plus as u8)
    }
    pub fn mul(&self, d: &Class, mut n: u64) -> Result<Class> {
        self.check(d)?;
        let mut a = d.clone();
        let mut out = self.zero();
        while n != 0 {
            if n & 1 != 0 {
                out = self.add(&out, &a)?;
            }
            a = self.add(&a, &a)?;
            n >>= 1;
        }
        Ok(out)
    }
    /// Complete degree2 effective-support enumeration, not a DLP solver.
    /// Rational pairs include tangencies; quadratic Frobenius orbits cover
    /// irreducible support. Hyperelliptic pairs are canonicalized to K.
    pub fn classes(&self) -> Result<Vec<Class>> {
        let mut out = BTreeMap::new();
        for n in 0..=2 {
            let d = self.wrap(self.poly(&[1]), self.poly(&[]), n)?;
            out.insert(d.key(), d);
        }
        let mut points = vec![];
        for x in 0..self.p {
            let rhs = self.f.eval(&BigUint::from(x)).to_u64().unwrap();
            for y in 0..self.p {
                if y * y % self.p == rhs {
                    for n in 0..=1 {
                        let d = self.point(x, y, n)?;
                        out.insert(d.key(), d);
                    }
                    points.push(self.point(x, y, 0)?);
                }
            }
        }
        for (i, a) in points.iter().enumerate() {
            for b in &points[i..] {
                let (u, v, _) = self.compose(a, b)?;
                if u.degree() == Some(2) {
                    let d = self.wrap(u, v, 0)?;
                    out.insert(d.key(), d);
                }
            }
        }
        let ctx = Fp2Ctx::try_new(self.p).map_err(|e| e.to_string())?;
        let mut roots: BTreeMap<(u64, u64), Vec<_>> = BTreeMap::new();
        for a in 0..self.p {
            for b in 0..self.p {
                let y = ctx.element(a, b);
                let square = ctx.square(y);
                roots.entry((square.a, square.b)).or_default().push(y);
            }
        }
        for a in 0..self.p {
            for b in 1..self.p {
                let x = ctx.element(a, b);
                let xp = ctx.pow(x, self.p);
                let mut rhs = ctx.zero();
                for c in self.f.coeffs.iter().rev() {
                    rhs = ctx.add(ctx.mul(rhs, x), ctx.from_fp(c.to_u64().unwrap()));
                }
                if let Some(ys) = roots.get(&(rhs.a, rhs.b)) {
                    for y in ys {
                        let yp = ctx.pow(*y, self.p);
                        if (x.a, x.b, y.a, y.b) > (xp.a, xp.b, yp.a, yp.b) {
                            continue;
                        }
                        let c = ctx.mul(x, xp);
                        let sum = ctx.neg(ctx.add(x, xp));
                        let slope = ctx.mul(
                            ctx.sub(*y, yp),
                            ctx.inv(ctx.sub(x, xp)).ok_or("quadratic orbit collapsed")?,
                        );
                        let constant = ctx.sub(*y, ctx.mul(slope, x));
                        if [c, sum, slope, constant].iter().any(|c| c.b != 0) {
                            return Err("quadratic support did not descend".into());
                        }
                        let d = self.wrap(
                            self.poly(&[c.a, sum.a, 1]),
                            self.poly(&[constant.a, slope.a]),
                            0,
                        )?;
                        out.insert(d.key(), d);
                    }
                }
            }
        }
        Ok(out.into_values().collect())
    }
}

pub struct QuadraticCover {
    pub(super) base: Curve,
    pub balanced: Balanced,
}
impl QuadraticCover {
    pub fn new(p: u64, a: u64, b: u64) -> Result<Self> {
        Self::with_cubic(p, [b, a, 0])
    }
    pub(super) fn with_cubic(p: u64, coefficients: [u64; 3]) -> Result<Self> {
        let modulus = BigUint::from(p);
        let f = FpPoly::from_coeffs(
            coefficients
                .into_iter()
                .chain([1])
                .map(BigUint::from)
                .collect(),
            modulus.clone(),
        );
        let base = Curve::try_new(modulus, f, 1).map_err(|e| e.to_string())?;
        let balanced = Balanced::new(
            p,
            &[
                coefficients[0],
                0,
                coefficients[1],
                0,
                coefficients[2],
                0,
                1,
            ],
        )?;
        Ok(Self { base, balanced })
    }
    pub fn pull(&self, d: &Divisor) -> Result<Class> {
        d.validate(&self.base).map_err(|e| e.to_string())?;
        if d.is_identity() {
            return Ok(self.balanced.zero());
        }
        let u = FpPoly::from_coeffs(
            vec![d.u.coeff(0), BigUint::zero(), BigUint::one()],
            self.base.p.clone(),
        );
        self.balanced.wrap(u, d.v.clone(), 0)
    }
    pub fn norm(&self, d: &Class) -> Result<Divisor> {
        self.balanced.check(d)?;
        // Both split infinities map to O, and the norm of K is2O.
        Ok(norm_power_support(&self.base, &d.u, &d.v, self.balanced.p, 2)?.0)
    }
}

/// Checked prime-field reciprocal curve isomorphism:
/// T=a/x, Y=kappa*y/x^3. Both sextics must be monic split at infinity.
/// The divisor map completes zero support and both old infinities.
struct Reciprocal {
    source: Balanced,
    target: Balanced,
    a: u64,
    kappa: u64,
    inverse_a: u64,
}
impl Reciprocal {
    fn new(source: &Balanced, a: u64, kappa: u64) -> Result<Self> {
        let p = source.p;
        if a == 0 || a >= p || kappa == 0 || kappa >= p {
            return Err("reciprocal needs nonzero canonical coordinate scales".into());
        }
        let inverse_a = BigUint::from(a)
            .modpow(&BigUint::from(p - 2), &BigUint::from(p))
            .to_u64()
            .unwrap();
        let mut coefficients = [0_u64; 7];
        let mut power = 1;
        for (i, c) in coefficients.iter_mut().enumerate() {
            *c = source.f.coeff(6 - i).to_u64().unwrap() * kappa % p * kappa % p * power % p;
            power = power * inverse_a % p;
        }
        let target = Balanced::new(p, &coefficients)?;
        Ok(Self {
            source: source.clone(),
            target,
            a,
            kappa,
            inverse_a,
        })
    }
    fn map(&self, d: &Class) -> Result<Class> {
        self.source.check(d)?;
        let p = self.source.p;
        let m = d.degree();
        let mut u = vec![0_u64; m + 1];
        let mut power = 1;
        for i in 0..=m {
            u[m - i] = d.u.coeff(i).to_u64().unwrap() * power % p;
            power = power * self.a % p;
        }
        let u = self.target.poly(&u).monic();
        let remaining = u.degree().unwrap();
        let lost = m - remaining;
        let scale = self.kappa * self.inverse_a % p * self.inverse_a % p * self.inverse_a % p;
        let mut v = vec![0_u64; 4];
        let mut power = 1;
        for (i, c) in d.v.coeffs.iter().enumerate() {
            v[3 - i] = c.to_u64().unwrap() * power % p * scale % p;
            power = power * self.a % p;
        }
        let v = self.target.poly(&v).rem(&u);
        let mut out = self.target.wrap(u, v, 0)?;
        if lost != 0 {
            let sign = d.v.coeff(0).to_u64().unwrap() * scale % p;
            if sign == 1 {
                out = self
                    .target
                    .add(&out, &self.target.mul(&self.target.delta(), lost as u64)?)?;
            } else if sign != p - 1 {
                return Err("lost reciprocal support has invalid infinity branch".into());
            }
        }
        let plus = self.target.point(0, self.kappa, 1)?;
        let minus = self.target.point(0, p - self.kappa, 1)?;
        out = self
            .target
            .add(&out, &self.target.mul(&plus, u64::from(d.plus))?)?;
        self.target.add(
            &out,
            &self
                .target
                .mul(&minus, (2 - m) as u64 - u64::from(d.plus))?,
        )
    }
}

/// Explicit two-elliptic-quotient coordinates for the bounded even sextic.
/// The square constant fixes a genuine Fp reciprocal isomorphism,no twist.
pub(super) struct SplitQuotients {
    pub(super) first: QuadraticCover,
    pub(super) second: QuadraticCover,
    forward: Reciprocal,
    inverse: Reciprocal,
}
impl SplitQuotients {
    pub(super) fn new(p: u64, coefficients: [u64; 3]) -> Result<Self> {
        let first = QuadraticCover::with_cubic(p, coefficients)?;
        let [b, a4, a2] = coefficients;
        let s = (1..p)
            .find(|s| s * s % p == b)
            .ok_or("split-quotient prototype requires a nonzero square constant")?;
        let second = QuadraticCover::with_cubic(p, [b * b % p, a2 * b % p, a4])?;
        let forward = Reciprocal::new(&first.balanced, s, b)?;
        let inverse = Reciprocal::new(&second.balanced, s, s)?;
        if forward.target.f != second.balanced.f || inverse.target.f != first.balanced.f {
            return Err("reciprocal quotient model mismatch".into());
        }
        Ok(Self {
            first,
            second,
            forward,
            inverse,
        })
    }
    pub(super) fn norms(&self, d: &Class) -> Result<(Divisor, Divisor)> {
        Ok((
            self.first.norm(d)?,
            self.second.norm(&self.forward.map(d)?)?,
        ))
    }
    pub(super) fn pulls(&self, a: &Divisor, b: &Divisor) -> Result<Class> {
        self.first.balanced.add(
            &self.first.pull(a)?,
            &self.inverse.map(&self.second.pull(b)?)?,
        )
    }
    /// Odd annihilators are explicit inputs,not unverified group-order
    /// certificates. Each actual input point must be annihilated by its value.
    pub(super) fn reconstruct(&self, a: &Divisor, b: &Divisor, odd: [u64; 2]) -> Result<Class> {
        let mut halves = vec![];
        for ((d, c), n) in [(a, &self.first.base), (b, &self.second.base)]
            .into_iter()
            .zip(odd)
        {
            if n < 3 || n.is_multiple_of(2) {
                return Err("split reconstruction requires odd annihilators greater than1".into());
            }
            d.validate(c).map_err(|e| e.to_string())?;
            if !d
                .checked_scalar_mul(&BigUint::from(n), c)
                .map_err(|e| e.to_string())?
                .is_identity()
            {
                return Err("supplied odd integer does not annihilate the component".into());
            }
            halves.push(
                d.checked_scalar_mul(&BigUint::from(n.div_ceil(2)), c)
                    .map_err(|e| e.to_string())?,
            );
        }
        self.pulls(&halves[0], &halves[1])
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn complete_split_quotients_reciprocal_and_reconstruction() {
        use std::collections::BTreeSet;
        for (p, coefficients, orders, expected) in [
            (17, [2, 2, 0], [19, 15], 285),
            (101, [56, 13, 6], [109, 113], 12317),
        ] {
            let split = SplitQuotients::new(p, coefficients).unwrap();
            let c = &split.first.balanced;
            let other = &split.second.balanced;
            let count = |curve: &Curve| {
                1 + (0..p)
                    .map(|x| {
                        let y2 = curve.f.eval(&BigUint::from(x));
                        (0..p).filter(|y| BigUint::from(y * y % p) == y2).count() as u64
                    })
                    .sum::<u64>()
            };
            assert_eq!(
                [count(&split.first.base), count(&split.second.base)],
                orders
            );
            let classes = c.classes().unwrap();
            assert_eq!(classes.len(), expected);
            let mut images = BTreeSet::new();
            let mut reciprocal_images = BTreeSet::new();
            let mut zero_multiplicities = BTreeSet::new();
            for (i, d) in classes.iter().enumerate() {
                let changed = split
                    .forward
                    .map(d)
                    .unwrap_or_else(|e| panic!("reciprocal{i}: {e}"));
                assert_eq!(split.inverse.map(&changed).unwrap(), *d);
                reciprocal_images.insert(changed.key());
                let e = &classes[(7919 * i + 37) % classes.len()];
                assert_eq!(
                    split.forward.map(&c.add(d, e).unwrap()).unwrap(),
                    other.add(&changed, &split.forward.map(e).unwrap()).unwrap()
                );
                let norms = split.norms(d).unwrap();
                let second_norms = split.norms(e).unwrap();
                let norm_sum = split.norms(&c.add(d, e).unwrap()).unwrap();
                assert_eq!(
                    norm_sum.0,
                    norms
                        .0
                        .checked_add(&second_norms.0, &split.first.base)
                        .unwrap()
                );
                assert_eq!(
                    norm_sum.1,
                    norms
                        .1
                        .checked_add(&second_norms.1, &split.second.base)
                        .unwrap()
                );
                let pulled1 = split.first.pull(&norms.0).unwrap();
                let pulled2 = split
                    .inverse
                    .map(&split.second.pull(&norms.1).unwrap())
                    .unwrap();
                let cross1 = split.norms(&pulled1).unwrap();
                let cross2 = split.norms(&pulled2).unwrap();
                assert!(cross1.1.is_identity());
                assert!(cross2.0.is_identity());
                assert_eq!(
                    cross1.0,
                    norms
                        .0
                        .checked_scalar_mul(&BigUint::from(2_u64), &split.first.base)
                        .unwrap()
                );
                assert_eq!(
                    cross2.1,
                    norms
                        .1
                        .checked_scalar_mul(&BigUint::from(2_u64), &split.second.base)
                        .unwrap()
                );
                assert_eq!(c.add(&pulled1, &pulled2).unwrap(), c.mul(d, 2).unwrap());
                assert_eq!(split.reconstruct(&norms.0, &norms.1, orders).unwrap(), *d);
                images.insert((
                    norms.0.u.coeffs,
                    norms.0.v.coeffs,
                    norms.1.u.coeffs,
                    norms.1.v.coeffs,
                ));
                zero_multiplicities.insert(d.u.coeffs.iter().take_while(|c| c.is_zero()).count());
            }
            assert_eq!(images.len(), expected);
            assert_eq!(reciprocal_images.len(), expected);
            assert_eq!(zero_multiplicities, BTreeSet::from([0, 1, 2]));
            assert!(split.forward.map(&other.zero()).is_err());
            assert!(Reciprocal::new(c, 0, 1).is_err());
            assert!(Reciprocal::new(c, 1, 0).is_err());
            assert!(split
                .reconstruct(
                    &Divisor::identity(BigUint::from(p)),
                    &Divisor::identity(BigUint::from(p)),
                    [2, 3]
                )
                .is_err());
            println!("PASS F{p} all{expected} reciprocal classes/inverse/bijection/paired additions,zero-support multiplicities0/1/2,both elliptic norm additions,cross norms0,pull1 norm1+pull2 norm2=[2],odd reconstruction; full elliptic product orders{orders:?}; no scalar labels or solver");
        }
        assert!(SplitQuotients::new(17, [3, 2, 0]).is_err());
    }
    use crate::chain;
    use std::collections::BTreeSet;
    fn old_chart(d: &Class) -> chain::Divisor {
        let convert = |p: &FpPoly| {
            p.coeffs
                .iter()
                .map(|c| c.to_u64().unwrap() as i64)
                .collect::<Vec<_>>()
        };
        let homogeneous = |p: &FpPoly, degree: usize| {
            let mut out = vec![];
            for (i, c) in convert(p).iter().enumerate() {
                let mut term = vec![*c];
                for _ in 0..i {
                    term = chain::pmul(&term, &[1, 10]);
                }
                let mut shifted = vec![0; degree - i];
                shifted.extend(term);
                out = chain::padd(&out, &shifted);
            }
            out
        };
        let mut out =
            chain::Divisor::new(homogeneous(&d.u, d.degree()), homogeneous(&d.v, 3)).unwrap();
        let positive = chain::Divisor::new(vec![0, 1], vec![1]).unwrap();
        out = out.add(&positive.mul(u64::from(d.plus)));
        out.add(
            &positive
                .neg()
                .mul((2 - d.degree() - usize::from(d.plus)) as u64),
        )
    }
    fn elliptic_point(d: &Divisor) -> chain::Point {
        if d.is_identity() {
            None
        } else {
            chain::point(
                chain::fp(-(d.u.coeff(0).to_u64().unwrap() as i64)),
                d.v.coeff(0).to_u64().unwrap() as i64,
            )
        }
    }
    #[test]
    fn all_old_classes_chart_addition_infinity_and_norm() {
        let cover = QuadraticCover::new(101, 0, 1).unwrap();
        let c = &cover.balanced;
        let classes = c.classes().unwrap();
        assert_eq!(classes.len(), 10404);
        let mapped = classes.iter().map(old_chart).collect::<BTreeSet<_>>();
        assert_eq!(mapped.len(), 10404);
        assert_eq!(mapped, chain::rational_classes().into_iter().collect());
        let delta = c.delta();
        let old_delta = old_chart(&delta);
        assert_ne!(delta, c.zero());
        assert_eq!(c.mul(&delta, 3).unwrap(), c.zero());
        let mut patterns = BTreeSet::new();
        for (i, d) in classes.iter().enumerate() {
            let e = &classes[(7919 * i + 37) % classes.len()];
            let old = old_chart(d);
            assert_eq!(
                old_chart(&c.add(d, e).unwrap()),
                old.add(&old_chart(e)),
                "pair{i}"
            );
            assert_eq!(old_chart(&c.neg(d).unwrap()), old.neg(), "neg{i}");
            assert_eq!(c.add(d, &c.neg(d).unwrap()).unwrap(), c.zero(), "zero{i}");
            assert_eq!(
                old_chart(&c.add(d, &delta).unwrap()),
                old.add(&old_delta),
                "infinity{i}"
            );
            assert_eq!(
                elliptic_point(&cover.norm(d).unwrap()),
                chain::push(&old, chain::Quotient::F).unwrap(),
                "norm{i}"
            );
            patterns.insert((d.degree(), d.plus));
        }
        assert_eq!(patterns.len(), 6);
        println!("PASS all10404 balanced classes biject with old chart; paired additions/inverses/identity/infinity translations and arbitrary-class norms agree; all6 degree/infinity patterns, delta order3");
    }
    #[test]
    fn prime109_cover_without_weierstrass_point() {
        let cover = QuadraticCover::new(101, 1, 46).unwrap();
        let c = &cover.balanced;
        assert!((0_u64..101).all(|x| !c.f.eval(&BigUint::from(x)).is_zero()));
        let g = Divisor::try_from_point(&cover.base, &BigUint::from(2_u64), &BigUint::from(37_u64))
            .unwrap();
        let image = cover.pull(&g).unwrap();
        assert_ne!(image, c.zero());
        assert_eq!(c.mul(&image, 109).unwrap(), c.zero());
        let mut seen = BTreeSet::new();
        for k in 0..109 {
            let d = g
                .checked_scalar_mul(&BigUint::from(k as u64), &cover.base)
                .unwrap();
            let pulled = cover.pull(&d).unwrap();
            assert_eq!(pulled, c.mul(&image, k as u64).unwrap());
            let norm = cover.norm(&pulled).unwrap();
            assert_eq!(
                norm,
                d.checked_scalar_mul(&BigUint::from(2_u64), &cover.base)
                    .unwrap()
            );
            assert_eq!(
                norm.checked_scalar_mul(&BigUint::from(55_u64), &cover.base)
                    .unwrap(),
                d
            );
            seen.insert(pulled.key());
        }
        assert_eq!(seen.len(), 109);
        let classes = c.classes().unwrap();
        // The observed balanced count is independently predicted by the
        // two elliptic quotient orders, without using class enumeration.
        let other = Curve::try_new(BigUint::from(101_u64), c.poly(&[96, 0, 1, 1]), 1).unwrap();
        assert_eq!(
            super::super::reference::count_points(&cover.base),
            BigUint::from(109_u64)
        );
        assert_eq!(
            super::super::reference::count_points(&other),
            BigUint::from(107_u64)
        );
        assert_eq!(classes.len(), 109 * 107);
        let mut fibers = BTreeMap::new();
        for (i, d) in classes.iter().enumerate() {
            let e = &classes[(7919 * i + 37) % classes.len()];
            let norm = cover.norm(d).unwrap();
            let key = (norm.u.coeffs.clone(), norm.v.coeffs.clone());
            *fibers.entry(key).or_insert(0_usize) += 1;
            assert_eq!(
                cover.norm(&c.add(d, e).unwrap()).unwrap(),
                norm.checked_add(&cover.norm(e).unwrap(), &cover.base)
                    .unwrap()
            );
        }
        assert_eq!(fibers.len(), 109);
        assert!(fibers.values().all(|n| *n == 107));
        assert_eq!(
            cover.norm(&c.delta()).unwrap(),
            Divisor::identity(cover.base.p.clone())
        );
        println!("PASS full prime109 subgroup in balanced genus2 without rational Weierstrass; all109 scalar/norm[2]/inverse55 checks, {} arbitrary-class paired norm additions; quotient orders109/107, norm image109 with equal107 fibers",classes.len());
    }
    #[test]
    fn published_example_tags_smoothness_and_associativity() {
        let c = Balanced::new(37, &[1, 1, 0, 0, 0, 0, 1]).unwrap();
        let classes = c.classes().unwrap();
        for (i, d) in classes.iter().enumerate() {
            let e = &classes[(37 * i + 7) % classes.len()];
            let f = &classes[(13 * i + 11) % classes.len()];
            assert_eq!(
                c.add(&c.add(d, e).unwrap(), f).unwrap(),
                c.add(d, &c.add(e, f).unwrap()).unwrap()
            );
        }
        let d = c.delta();
        assert_ne!(c.mul(&d, 3).unwrap(), c.zero());
        // Galbraith corrected Example10.4.18: the unreduced n=1 pair is
        // the canonical n=0 class plus delta=inf+ - inf-.
        let published = c.wrap(c.poly(&[2, 34, 1]), c.poly(&[27, 32]), 0).unwrap();
        assert_eq!(
            c.add(&published, &d).unwrap(),
            c.wrap(c.poly(&[2, 28, 1]), c.poly(&[22, 7]), 0).unwrap()
        );
        let foreign = Balanced::new(37, &[2, 1, 0, 0, 0, 0, 1]).unwrap();
        assert!(c.add(&d, &foreign.zero()).is_err());
        assert!(Balanced::new(9, &[1, 1, 0, 0, 0, 0, 1]).is_err());
        assert!(Balanced::new(37, &[0, 0, 0, 0, 0, 0, 1]).is_err());
        assert!(Balanced::new(37, &[1, 1, 0, 0, 0, 0, 2]).is_err());
        assert!(c.point(37, 0, 0).is_err());
        assert!(c.wrap(c.poly(&[1]), c.poly(&[]), 3).is_err());
        assert!(c.wrap(c.poly(&[1]), c.poly(&[1]), 1).is_err());
        println!("PASS general monic sextic F37 associativity on {} fixed triples, infinity control and malformed/foreign domains",classes.len());
    }
    #[test]
    fn translated_sextic_full_nonzero_infinity_expansion() {
        let c = Balanced::new(101, &[2, 6, 15, 20, 15, 6, 1]).unwrap();
        let original = Balanced::new(101, &[1, 0, 0, 0, 0, 0, 1]).unwrap();
        assert_eq!(c.polynomial_part, c.poly(&[1, 3, 3, 1]));
        let substitute_minus_one = |f: &FpPoly| {
            let mut out = c.poly(&[]);
            for a in f.coeffs.iter().rev() {
                out = out
                    .mul(&c.poly(&[100, 1]))
                    .add(&FpPoly::constant(a.clone(), f.p.clone()));
            }
            out
        };
        let bridge = |d: &Class| {
            old_chart(
                &original
                    .wrap(
                        substitute_minus_one(&d.u),
                        substitute_minus_one(&d.v),
                        d.plus,
                    )
                    .unwrap(),
            )
        };
        let classes = c.classes().unwrap();
        assert_eq!(classes.len(), 10404);
        let mapped = classes.iter().map(bridge).collect::<BTreeSet<_>>();
        assert_eq!(mapped.len(), 10404);
        assert_eq!(mapped, chain::rational_classes().into_iter().collect());
        for (i, d) in classes.iter().enumerate() {
            let e = &classes[(7919 * i + 37) % classes.len()];
            assert_eq!(bridge(&c.add(d, e).unwrap()), bridge(d).add(&bridge(e)));
            assert_eq!(bridge(&c.neg(d).unwrap()), bridge(d).neg());
        }
        println!("PASS all10404 translated-sextic classes and paired additions/inverses against old engine; nonzero infinity polynomial x³+3x²+3x+1");
    }
}
