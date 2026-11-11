//! Operational fixed F17 non-split correspondence. Source support is split
//! only in F17²; coefficients lie in F17³, so their compositum F17⁶ suffices.
//! Target fibers remain quadratic Mumford pairs; no target roots are chosen.
use super::{construct, CubicField, E};
use crate::balanced::{Balanced, Class};
use crate::reference::{Fp2, Fp2Ctx, FpPoly};
use num_bigint::BigUint;
use num_traits::ToPrimitive;
type Result<T> = std::result::Result<T, String>;

#[derive(Clone, Debug, PartialEq, Eq)]
struct Element {
    a: E,
    b: E,
}
type Poly = Vec<Element>;
struct Field {
    k: CubicField,
    nonresidue: E,
}
impl Field {
    fn new(k: CubicField) -> Self {
        let nr = Fp2Ctx::try_new(k.p).unwrap().nonresidue();
        let nonresidue = k.c(nr);
        assert_eq!(k.pow(&nonresidue, (k.p.pow(3) - 1) / 2), k.c(k.p - 1));
        Self { k, nonresidue }
    }
    fn c(&self, n: u64) -> Element {
        Element {
            a: self.k.c(n),
            b: self.k.z(),
        }
    }
    fn lift3(&self, a: &E) -> Element {
        Element {
            a: a.clone(),
            b: self.k.z(),
        }
    }
    fn lift2(&self, x: Fp2) -> Element {
        Element {
            a: self.k.c(x.a),
            b: self.k.c(x.b),
        }
    }
    fn zero(&self, a: &Element) -> bool {
        a.a.is_zero() && a.b.is_zero()
    }
    fn add(&self, a: &Element, b: &Element) -> Element {
        Element {
            a: a.a.add(&b.a),
            b: a.b.add(&b.b),
        }
    }
    fn neg(&self, a: &Element) -> Element {
        Element {
            a: a.a.neg(),
            b: a.b.neg(),
        }
    }
    fn sub(&self, a: &Element, b: &Element) -> Element {
        self.add(a, &self.neg(b))
    }
    fn mul(&self, a: &Element, b: &Element) -> Element {
        Element {
            a: self
                .k
                .mul(&a.a, &b.a)
                .add(&self.k.mul(&self.nonresidue, &self.k.mul(&a.b, &b.b))),
            b: self.k.mul(&a.a, &b.b).add(&self.k.mul(&a.b, &b.a)),
        }
    }
    fn inv(&self, a: &Element) -> Element {
        assert!(!self.zero(a), "zero in compositum inverse");
        let norm = self
            .k
            .mul(&a.a, &a.a)
            .sub(&self.k.mul(&self.nonresidue, &self.k.mul(&a.b, &a.b)));
        let inverse = self.k.inv(&norm);
        Element {
            a: self.k.mul(&a.a, &inverse),
            b: self.k.mul(&a.b.neg(), &inverse),
        }
    }
    fn pow(&self, a: &Element, mut n: u64) -> Element {
        let mut a = a.clone();
        let mut out = self.c(1);
        while n != 0 {
            if n & 1 != 0 {
                out = self.mul(&out, &a);
            }
            a = self.mul(&a, &a);
            n >>= 1;
        }
        out
    }
    fn base(&self, a: &Element) -> Result<BigUint> {
        if !a.b.is_zero() || a.a.degree().is_some_and(|d| d > 0) {
            return Err(format!("completed image did not descend: {a:?}"));
        }
        Ok(a.a.coeff(0))
    }
    fn trim(&self, mut a: Poly) -> Poly {
        while a.last().is_some_and(|c| self.zero(c)) {
            a.pop();
        }
        a
    }
    fn addp(&self, a: &Poly, b: &Poly) -> Poly {
        self.trim(
            (0..a.len().max(b.len()))
                .map(|i| {
                    self.add(
                        &a.get(i).cloned().unwrap_or_else(|| self.c(0)),
                        &b.get(i).cloned().unwrap_or_else(|| self.c(0)),
                    )
                })
                .collect(),
        )
    }
    fn negp(&self, a: &Poly) -> Poly {
        a.iter().map(|c| self.neg(c)).collect()
    }
    fn subp(&self, a: &Poly, b: &Poly) -> Poly {
        self.addp(a, &self.negp(b))
    }
    fn mulp(&self, a: &Poly, b: &Poly) -> Poly {
        if a.is_empty() || b.is_empty() {
            return vec![];
        }
        let mut out = vec![self.c(0); a.len() + b.len() - 1];
        for (i, x) in a.iter().enumerate() {
            for (j, y) in b.iter().enumerate() {
                out[i + j] = self.add(&out[i + j], &self.mul(x, y));
            }
        }
        self.trim(out)
    }
    fn scale(&self, a: &Poly, b: &Element) -> Poly {
        self.trim(a.iter().map(|c| self.mul(c, b)).collect())
    }
    fn divrem(&self, a: &Poly, b: &Poly) -> (Poly, Poly) {
        assert!(!b.is_empty());
        let mut r = a.clone();
        let mut q = vec![self.c(0); (a.len() + 1).saturating_sub(b.len())];
        let inverse = self.inv(b.last().unwrap());
        while !r.is_empty() && r.len() >= b.len() {
            let shift = r.len() - b.len();
            let value = self.mul(r.last().unwrap(), &inverse);
            q[shift] = value.clone();
            for (i, c) in b.iter().enumerate() {
                r[i + shift] = self.sub(&r[i + shift], &self.mul(c, &value));
            }
            r = self.trim(r);
        }
        (self.trim(q), r)
    }
    fn exact(&self, a: &Poly, b: &Poly) -> Result<Poly> {
        let (q, r) = self.divrem(a, b);
        if !r.is_empty() {
            return Err("nonexact compositum polynomial division".into());
        }
        Ok(q)
    }
    fn monic(&self, a: &Poly) -> Poly {
        self.scale(a, &self.inv(a.last().unwrap()))
    }
    fn xgcd(&self, a: &Poly, b: &Poly) -> (Poly, Poly, Poly) {
        let (mut a, mut b) = (a.clone(), b.clone());
        let (mut s, mut ss, mut t, mut tt) = (vec![self.c(1)], vec![], vec![], vec![self.c(1)]);
        while !b.is_empty() {
            let (q, r) = self.divrem(&a, &b);
            a = b;
            b = r;
            (s, ss) = (ss.clone(), self.subp(&s, &self.mulp(&q, &ss)));
            (t, tt) = (tt.clone(), self.subp(&t, &self.mulp(&q, &tt)));
        }
        let inverse = self.inv(a.last().unwrap());
        (
            self.scale(&a, &inverse),
            self.scale(&s, &inverse),
            self.scale(&t, &inverse),
        )
    }
    fn value(&self, a: &Poly, x: &Element) -> Element {
        a.iter()
            .rev()
            .fold(self.c(0), |v, c| self.add(&self.mul(&v, x), c))
    }
    fn lift_poly(&self, a: &FpPoly) -> Poly {
        a.coeffs
            .iter()
            .map(|c| self.c(c.to_u64().unwrap()))
            .collect()
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
struct Divisor {
    u: Poly,
    v: Poly,
    plus: u8,
}
struct Jacobian<'a> {
    k: &'a Field,
    f: Poly,
    infinity: Poly,
}
impl<'a> Jacobian<'a> {
    fn new(k: &'a Field, c: &Balanced) -> Self {
        let (f, infinity) = c.equation_and_infinity();
        Self {
            k,
            f: k.lift_poly(f),
            infinity: k.lift_poly(infinity),
        }
    }
    fn zero(&self) -> Divisor {
        Divisor {
            u: vec![self.k.c(1)],
            v: vec![],
            plus: 1,
        }
    }
    fn check(&self, d: &Divisor) -> Result<()> {
        if d.u.is_empty()
            || d.u.len() > 3
            || d.u.last() != Some(&self.k.c(1))
            || d.v.len() >= d.u.len()
            || d.u.len() - 1 + usize::from(d.plus) > 2
        {
            return Err("invalid compositum balanced representation".into());
        }
        if !self
            .k
            .divrem(&self.k.subp(&self.f, &self.k.mulp(&d.v, &d.v)), &d.u)
            .1
            .is_empty()
        {
            return Err("compositum divisor left target curve".into());
        }
        Ok(())
    }
    fn pair(&self, u: Poly, v: Poly, plus: u8) -> Result<Divisor> {
        let d = Divisor { u, v, plus };
        self.check(&d)?;
        Ok(d)
    }
    fn neg(&self, d: &Divisor) -> Divisor {
        Divisor {
            u: d.u.clone(),
            v: self.k.negp(&d.v),
            plus: 3 - d.u.len() as u8 - d.plus,
        }
    }
    fn add(&self, a: &Divisor, b: &Divisor) -> Result<Divisor> {
        self.check(a)?;
        self.check(b)?;
        let k = self.k;
        let (d1, e1, e2) = k.xgcd(&a.u, &b.u);
        let (d, c1, c2) = k.xgcd(&d1, &k.addp(&a.v, &b.v));
        let u = k.exact(&k.mulp(&a.u, &b.u), &k.mulp(&d, &d))?;
        let numerator = k.addp(
            &k.addp(
                &k.mulp(&k.mulp(&k.mulp(&c1, &e1), &a.u), &b.v),
                &k.mulp(&k.mulp(&k.mulp(&c1, &e2), &b.u), &a.v),
            ),
            &k.mulp(&c2, &k.addp(&k.mulp(&a.v, &b.v), &self.f)),
        );
        let v = k.divrem(&k.exact(&numerator, &d)?, &u).1;
        let plus = i64::from(a.plus) + i64::from(b.plus) + d.len() as i64 - 2;
        let m = u.len() - 1;
        if m <= 2 && plus >= 0 && plus <= 2 - m as i64 {
            return self.pair(u, v, plus as u8);
        }
        let line = if m == 4 {
            v
        } else {
            let g = if plus >= 0 {
                self.infinity.clone()
            } else {
                k.negp(&self.infinity)
            };
            k.addp(&g, &k.divrem(&k.subp(&v, &g), &u).1)
        };
        let numerator = k.subp(&self.f, &k.mulp(&line, &line));
        if numerator.is_empty() {
            return Err("compositum sextic became a square".into());
        }
        let raw = k.exact(&numerator, &u)?;
        if raw.is_empty() {
            return Err("zero compositum reduced support".into());
        }
        let next = k.monic(&raw);
        let r = next.len() - 1;
        let valuation = if line.get(3) == Some(&k.c(1)) {
            4 - numerator.len() as i64
        } else {
            -3
        };
        let next_plus = plus - valuation - r as i64;
        if r > 2 || next_plus < 0 || next_plus > 2 - r as i64 {
            return Err("compositum infinity count did not reduce".into());
        }
        let next_v = k.divrem(&k.negp(&line), &next).1;
        self.pair(next, next_v, next_plus as u8)
    }
    fn descend(&self, d: &Divisor, target: &Balanced) -> Result<Class> {
        self.check(d)?;
        let poly = |p: &Poly| -> Result<FpPoly> {
            Ok(FpPoly::from_coeffs(
                p.iter()
                    .map(|c| self.k.base(c))
                    .collect::<Result<Vec<_>>>()?,
                BigUint::from(self.k.k.p),
            ))
        };
        target.wrap(poly(&d.u)?, poly(&d.v)?, d.plus)
    }
}

struct RichelotMap {
    k: Field,
    source: Balanced,
    target: Balanced,
    g: [Poly; 3],
    h: [Poly; 3],
}
impl RichelotMap {
    fn new() -> Self {
        let a = construct();
        let k = Field::new(a.field);
        let pairing = a
            .pairs
            .iter()
            .find(|p| {
                let g = std::array::from_fn(|i| {
                    let (u, v) = p[i];
                    vec![
                        k.k.mul(&a.roots[u], &a.roots[v]),
                        a.roots[u].add(&a.roots[v]).neg(),
                        k.k.c(1),
                    ]
                });
                !k.k.determinant(&g).is_zero()
            })
            .unwrap();
        assert_eq!(*pairing, [(0, 4), (1, 5), (2, 3)]);
        let raw_g = std::array::from_fn(|i| {
            let (u, v) = pairing[i];
            vec![
                k.k.mul(&a.roots[u], &a.roots[v]),
                a.roots[u].add(&a.roots[v]).neg(),
                k.k.c(1),
            ]
        });
        let delta = k.k.determinant(&raw_g);
        assert_eq!(k.k.base(&delta), 11);
        let raw_h = k.k.dual_factors(&raw_g, &delta);
        let g = std::array::from_fn(|i| raw_g[i].iter().map(|c| k.lift3(c)).collect());
        let h = std::array::from_fn(|i| raw_h[i].iter().map(|c| k.lift3(c)).collect());
        let source = Balanced::new(17, &[2, 0, 2, 0, 0, 0, 1]).unwrap();
        let target = Balanced::new(17, &[3, 12, 11, 4, 7, 3, 1]).unwrap();
        Self {
            k,
            source,
            target,
            g,
            h,
        }
    }
    fn fiber(
        &self,
        x: &Element,
        y: &Element,
        g: &[Poly; 3],
        h: &[Poly; 3],
        target_scale: u64,
        target: &Jacobian<'_>,
    ) -> Result<Divisor> {
        let k = &self.k;
        let g1 = k.value(&g[0], x);
        let g2 = k.value(&g[1], x);
        if k.zero(y) {
            if k.zero(&g1) {
                return target.pair(k.monic(&h[1]), vec![], 0);
            }
            if k.zero(&g2) {
                return target.pair(k.monic(&h[0]), vec![], 0);
            }
            if k.zero(&k.value(&g[2], x)) {
                return Ok(target.zero());
            }
            return Err("zero-y support outside branch locus".into());
        }
        let u = k.addp(&k.scale(&h[0], &g1), &k.scale(&h[1], &g2));
        if u.is_empty() {
            return Err("correspondence fiber has excess dimension".into());
        }
        let scale = k.inv(&k.mul(y, &k.c(target_scale)));
        let numerator = k.scale(
            &k.mulp(&h[0], &vec![x.clone(), k.neg(&k.c(1))]),
            &k.mul(&g1, &scale),
        );
        let monic = k.monic(&u);
        let v = k.divrem(&numerator, &monic).1;
        let m = u.len() - 1;
        if m == 2 {
            return target.pair(monic, v, 0);
        }
        if m > 2 {
            return Err("correspondence is not quadratic".into());
        }
        let cap = k.neg(&k.mul(&k.mul(&g1, h[0].last().unwrap()), &scale));
        let sign = if cap == k.c(1) {
            true
        } else if cap == k.neg(&k.c(1)) {
            false
        } else {
            return Err("degree-drop target infinity is not on curve".into());
        };
        let plus = if sign { (2 - m) as u8 } else { 0 };
        target.pair(monic, v, plus)
    }
    fn infinity(
        &self,
        g: &[Poly; 3],
        h: &[Poly; 3],
        source_scale: u64,
        target_scale: u64,
        target: &Jacobian<'_>,
    ) -> Result<Divisor> {
        let k = &self.k;
        let u = k.addp(
            &k.scale(&h[0], g[0].last().unwrap()),
            &k.scale(&h[1], g[1].last().unwrap()),
        );
        if u.len() != 3 {
            return Err("fixed source-infinity fiber requires explicit completion".into());
        }
        let u = k.monic(&u);
        let scale = k.mul(
            g[0].last().unwrap(),
            &k.inv(&k.c(source_scale * target_scale)),
        );
        let v = k.divrem(&k.scale(&h[0], &scale), &u).1;
        target.pair(u, v, 0)
    }
    fn roots(&self, u: &FpPoly) -> Result<Vec<Fp2>> {
        let ctx = Fp2Ctx::try_new(17).unwrap();
        let m = u.degree().ok_or("zero source support")?;
        if m == 0 {
            return Ok(vec![]);
        }
        let mut out = vec![];
        for a in 0..17 {
            for b in 0..17 {
                let x = ctx.element(a, b);
                let value = u.coeffs.iter().rev().fold(ctx.zero(), |v, c| {
                    ctx.add(ctx.mul(v, x), ctx.from_fp(c.to_u64().unwrap()))
                });
                if ctx.is_zero(value) {
                    out.push(x);
                }
            }
        }
        if m == 2 && out.len() == 1 {
            out.push(out[0]);
        }
        if out.len() != m {
            return Err("source support did not split over F17²".into());
        }
        Ok(out)
    }
    fn evaluate(&self, d: &Class, reverse: bool) -> Result<Class> {
        let (source, target, g, h, source_scale, target_scale) = if reverse {
            (&self.target, &self.source, &self.h, &self.g, 3, 1)
        } else {
            (&self.source, &self.target, &self.g, &self.h, 1, 3)
        };
        source.check(d)?;
        let target_ctx = Jacobian::new(&self.k, target);
        let (u, v, plus) = d.components();
        let mut out = target_ctx.zero();
        let quadratic = Fp2Ctx::try_new(17).unwrap();
        for x in self.roots(u)? {
            let y = v.coeffs.iter().rev().fold(quadratic.zero(), |w, c| {
                quadratic.add(quadratic.mul(w, x), quadratic.from_fp(c.to_u64().unwrap()))
            });
            let raw_y = self.k.mul(&self.k.lift2(y), &self.k.c(source_scale));
            let image = self.fiber(&self.k.lift2(x), &raw_y, g, h, target_scale, &target_ctx)?;
            out = target_ctx.add(&out, &image)?;
        }
        let infinity = self.infinity(g, h, source_scale, target_scale, &target_ctx)?;
        let coefficient = 2 * i64::from(plus) + u.degree().unwrap() as i64 - 2;
        let infinity = if coefficient < 0 {
            target_ctx.neg(&infinity)
        } else {
            infinity
        };
        for _ in 0..coefficient.unsigned_abs() {
            out = target_ctx.add(&out, &infinity)?;
        }
        if reverse {
            out = target_ctx.neg(&out);
        }
        target_ctx.descend(&out, target)
    }
    fn forward(&self, d: &Class) -> Result<Class> {
        self.evaluate(d, false)
    }
    fn dual(&self, d: &Class) -> Result<Class> {
        self.evaluate(d, true)
    }
}

#[test]
fn compositum_embeddings_inverses_and_frobenius() {
    let f = Field::new(CubicField::new());
    let q = Fp2Ctx::try_new(17).unwrap();
    for a in 0..17 {
        for b in 0..17 {
            let x = q.element(a, b);
            let y = q.element((a + 3) % 17, (7 * b + 2) % 17);
            assert_eq!(f.mul(&f.lift2(x), &f.lift2(y)), f.lift2(q.mul(x, y)));
            assert_eq!(f.add(&f.lift2(x), &f.lift2(y)), f.lift2(q.add(x, y)));
        }
    }
    let mut witness=String::from("# chained-nonsplit-field6/v1; p17; T^3+2T+2=0; s^2=3; a(T)+b(T)s\nn\tx\ty\tproduct\tinverse\tfrobenius3\tfrobenius6\n");
    let encode = |x: &Element| {
        (0..3)
            .map(|i| x.a.coeff(i).to_string())
            .chain((0..3).map(|i| x.b.coeff(i).to_string()))
            .collect::<Vec<_>>()
            .join(",")
    };
    for n in 0..128 {
        let x = Element {
            a: f.k.element(n),
            b: f.k.element((37 * n + 19) % 4913),
        };
        assert!(!f.zero(&x));
        let inverse = f.inv(&x);
        assert_eq!(f.mul(&x, &inverse), f.c(1));
        assert_eq!(
            f.pow(&x, 17_u64.pow(3)),
            Element {
                a: x.a.clone(),
                b: x.b.neg()
            }
        );
        assert_eq!(f.pow(&x, 17_u64.pow(6)), x);
        let y = Element {
            a: f.k.element((13 * n + 7) % 4913),
            b: f.k.element((29 * n + 11) % 4913),
        };
        witness += &format!(
            "{n}\t{}\t{}\t{}\t{}\t{}\t{}\n",
            encode(&x),
            encode(&y),
            encode(&f.mul(&x, &y)),
            encode(&inverse),
            encode(&f.pow(&x, 17_u64.pow(3))),
            encode(&f.pow(&x, 17_u64.pow(6)))
        );
    }
    if let Ok(path) = std::env::var("CHAINED_F6_WITNESS_OUT") {
        std::fs::write(path, witness).unwrap();
    }
    println!("PASS F17² embeddings on289 pairs and128 compositum inverse/Frobenius controls using irreducible cubic and nonsquare quadratic adjunction");
}
#[test]
fn complete_rational_domains_duals_and_additivity() {
    let r = RichelotMap::new();
    let source = r.source.classes().unwrap();
    let target = r.target.classes().unwrap();
    assert_eq!((source.len(), target.len()), (285, 285));
    let mut images = BTreeSet::new();
    for (i, d) in source.iter().enumerate() {
        let image = r.forward(d).unwrap_or_else(|e| panic!("source{i}: {e}"));
        assert_eq!(
            r.dual(&image).unwrap(),
            r.source.mul(d, 2).unwrap(),
            "source dual{i}"
        );
        let e = &source[(37 * i + 7) % source.len()];
        assert_eq!(
            r.forward(&r.source.add(d, e).unwrap()).unwrap(),
            r.target.add(&image, &r.forward(e).unwrap()).unwrap(),
            "addition{i}"
        );
        let (u, v, n) = image.components();
        images.insert((u.coeffs.clone(), v.coeffs.clone(), n));
    }
    assert_eq!(images.len(), 285);
    for (i, d) in target.iter().enumerate() {
        assert_eq!(
            r.forward(&r.dual(d).unwrap()).unwrap(),
            r.target.mul(d, 2).unwrap(),
            "target dual{i}"
        );
    }
    assert!(r.forward(&r.target.zero()).is_err());
    println!("PASS all285 source/target rational classes, both dual norms[2],285-image bijection, paired additivity, balanced infinities and coefficientwise F17 descent");
}
#[test]
fn full_prime19_subgroup_and_source_recovery() {
    use crate::balanced::QuadraticCover;
    use crate::reference::{HyperellipticCurveP as Curve, MumfordDivisorP};
    let r = RichelotMap::new();
    let cover = QuadraticCover::new(17, 2, 2).unwrap();
    let base = Curve::try_new(
        BigUint::from(17_u64),
        FpPoly::from_coeffs(
            [2_u64, 2, 0, 1].into_iter().map(BigUint::from).collect(),
            BigUint::from(17_u64),
        ),
        1,
    )
    .unwrap();
    let g = MumfordDivisorP::try_from_point(&base, &BigUint::from(5_u64), &BigUint::from(1_u64))
        .unwrap();
    let image = r.forward(&cover.pull(&g).unwrap()).unwrap();
    assert_ne!(image, r.target.zero());
    assert_eq!(r.target.mul(&image, 19).unwrap(), r.target.zero());
    for k in 0..19_u64 {
        let p = g.checked_scalar_mul(&BigUint::from(k), &base).unwrap();
        let d = r.forward(&cover.pull(&p).unwrap()).unwrap();
        assert_eq!(d, r.target.mul(&image, k).unwrap());
        let recovered = cover.norm(&r.dual(&d).unwrap()).unwrap();
        assert_eq!(
            recovered,
            p.checked_scalar_mul(&BigUint::from(4_u64), &base).unwrap()
        );
        assert_eq!(
            recovered
                .checked_scalar_mul(&BigUint::from(5_u64), &base)
                .unwrap(),
            p
        );
    }
    println!("PASS nonzero full prime19 source through quadratic pullback/non-split Richelot, all19 scalar relations, reversed-chain/source norm[4] and inverse5 recovery; no scalar label in map");
}

use std::collections::BTreeSet;
