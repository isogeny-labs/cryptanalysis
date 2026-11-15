//! Bounded split-leading non-split correspondence. Source support splits
//! in Fp²; coefficients lie in Fp³, so their compositum Fp⁶ suffices.
//! Target fibers remain quadratic Mumford pairs; no target roots are chosen.
use super::{construct, construct_for, Assessment, CubicField, E};
use crate::balanced::{Balanced, Class};
use crate::reference::{Fp2, Fp2Ctx, FpPoly};
use num_bigint::BigUint;
use num_traits::ToPrimitive;
use std::collections::BTreeMap;
#[path = "closed_fibres.rs"]
mod closed_fibres;
#[path = "seven_glue.rs"]
mod seven_glue;
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
        if *a == self.zero() {
            return Ok(b.clone());
        }
        if *b == self.zero() {
            return Ok(a.clone());
        }
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
        self.reduce(u, v, plus)
    }
    // Shared existing reduction, also used for a four-point closed fibre.
    // A raw finite4-2K divisor has signed plus=-1 before reduction.
    fn reduce(&self, u: Poly, v: Poly, plus: i64) -> Result<Divisor> {
        let k = self.k;
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
    target_scale: u64,
    quadratic: Fp2Ctx,
    square_roots: BTreeMap<(u64, u64), Fp2>,
}
impl RichelotMap {
    fn new() -> Self {
        Self::from_assessment(construct()).unwrap()
    }
    fn from_assessment(a: Assessment) -> Result<Self> {
        let pairing = a
            .pairs
            .iter()
            .find(|p| {
                let g = std::array::from_fn(|i| {
                    let (u, v) = p[i];
                    vec![
                        a.field.mul(&a.roots[u], &a.roots[v]),
                        a.roots[u].add(&a.roots[v]).neg(),
                        a.field.c(1),
                    ]
                });
                !a.field.determinant(&g).is_zero()
            })
            .copied()
            .ok_or("no nondegenerate stable kernel")?;
        // Preserve the frozen old-model choice; transported kernels use the
        // separately validated explicit constructor below.
        assert_eq!(pairing, [(0, 4), (1, 5), (2, 3)]);
        Self::from_selected_pairing(a, pairing)
    }
    fn from_selected_pairing(a: Assessment, pairing: super::Pairing) -> Result<Self> {
        let p = a.field.p;
        if a.roots.len() != 6 || a.source.len() != 7 {
            return Err("selected Richelot chart requires six branch roots and a sextic".into());
        }
        let mut used = [false; 6];
        for (u, v) in pairing {
            for i in [u, v] {
                if i >= 6 || used[i] {
                    return Err("selected kernel is not a disjoint six-root matching".into());
                }
                used[i] = true;
            }
        }
        if super::canonical_pairing(pairing) != pairing || !a.pairs.contains(&pairing) {
            return Err("selected kernel is not an inventoried canonical stable matching".into());
        }
        for (i, root) in a.roots.iter().enumerate() {
            if root.p != a.field.q.p
                || root.degree().is_some_and(|d| d >= 3)
                || a.roots[..i].contains(root)
            {
                return Err(
                    "branch roots are not six distinct canonical elements of the field".into(),
                );
            }
        }
        let mut permutation = [0; 6];
        for (i, root) in a.roots.iter().enumerate() {
            permutation[i] = a
                .roots
                .iter()
                .position(|r| *r == a.field.pow(root, p))
                .ok_or("branch roots are not Frobenius stable")?;
        }
        if !super::stable(&pairing, &permutation) {
            return Err("selected kernel is not Frobenius stable".into());
        }
        let k = Field::new(a.field);
        let raw_g = std::array::from_fn(|i| {
            let (u, v) = pairing[i];
            vec![
                k.k.mul(&a.roots[u], &a.roots[v]),
                a.roots[u].add(&a.roots[v]).neg(),
                k.k.c(1),
            ]
        });
        if k.k.product(&raw_g) != a.source.iter().map(|c| k.k.c(*c)).collect::<Vec<_>>() {
            return Err("selected factor product does not equal the source sextic".into());
        }
        let delta = k.k.determinant(&raw_g);
        if delta.is_zero() {
            return Err("selected Richelot determinant is zero".into());
        }
        let raw_h = k.k.dual_factors(&raw_g, &delta);
        let g = std::array::from_fn(|i| raw_g[i].iter().map(|c| k.lift3(c)).collect());
        let h = std::array::from_fn(|i| raw_h[i].iter().map(|c| k.lift3(c)).collect());
        let product = k.k.product(&raw_h);
        if product.iter().any(|c| c.degree().is_some_and(|d| d > 0)) {
            return Err("selected Richelot target coefficients do not descend".into());
        }
        let raw_target = product.iter().map(|c| k.k.base(c)).collect::<Vec<_>>();
        if raw_target.len() != 7 {
            return Err("odd target chart requires explicit coordinate conversion".into());
        }
        let leading = raw_target[6];
        let target_scale = (1..p)
            .find(|y| y * y % p == leading)
            .ok_or("nonsquare target leading requires explicit split-infinity chart")?;
        let leading_inverse = k.k.base(&k.k.inv(&k.k.c(leading)));
        let normalized = raw_target
            .iter()
            .map(|c| c * leading_inverse % p)
            .collect::<Vec<_>>();
        let source = Balanced::new(p, &a.source)?;
        let target = Balanced::new(p, &normalized)?;
        let quadratic = Fp2Ctx::try_new(p).map_err(|e| e.to_string())?;
        let mut square_roots = BTreeMap::new();
        for aa in 0..p {
            for bb in 0..p {
                let value = quadratic.element(aa, bb);
                let square = quadratic.square(value);
                square_roots.entry((square.a, square.b)).or_insert(value);
            }
        }
        Ok(Self {
            k,
            source,
            target,
            g,
            h,
            target_scale,
            quadratic,
            square_roots,
        })
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
        let ctx = self.quadratic;
        let m = u.degree().ok_or("zero source support")?;
        if m == 0 {
            return Ok(vec![]);
        }
        let b = ctx.from_fp(u.coeff(0).to_u64().unwrap());
        if m == 1 {
            return Ok(vec![ctx.neg(b)]);
        }
        if m != 2 {
            return Err("source support degree exceeds2".into());
        }
        let a = ctx.from_fp(u.coeff(1).to_u64().unwrap());
        let discriminant = ctx.sub(ctx.square(a), ctx.mul(ctx.from_fp(4), b));
        let root = self
            .square_roots
            .get(&(discriminant.a, discriminant.b))
            .ok_or("source quadratic discriminant did not split")?;
        let half = ctx.from_fp(self.k.k.p.div_ceil(2));
        Ok(vec![
            ctx.mul(ctx.add(ctx.neg(a), *root), half),
            ctx.mul(ctx.sub(ctx.neg(a), *root), half),
        ])
    }
    fn evaluate(&self, d: &Class, reverse: bool) -> Result<Class> {
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
        source.check(d)?;
        let target_ctx = Jacobian::new(&self.k, target);
        let (u, v, plus) = d.components();
        let mut out = target_ctx.zero();
        let quadratic = self.quadratic;
        for x in self.roots(u)? {
            let y = v.coeffs.iter().rev().fold(quadratic.zero(), |w, c| {
                quadratic.add(quadratic.mul(w, x), quadratic.from_fp(c.to_u64().unwrap()))
            });
            let raw_y = self.k.mul(&self.k.lift2(y), &self.k.c(source_scale));
            let image = self.fiber(&self.k.lift2(x), &raw_y, g, h, target_scale, &target_ctx)?;
            out = target_ctx.add(&out, &image)?;
        }
        let coefficient = 2 * i64::from(plus) + u.degree().unwrap() as i64 - 2;
        if coefficient != 0 {
            let infinity = self.infinity(g, h, source_scale, target_scale, &target_ctx)?;
            let infinity = if coefficient < 0 {
                target_ctx.neg(&infinity)
            } else {
                infinity
            };
            for _ in 0..coefficient.unsigned_abs() {
                out = target_ctx.add(&out, &infinity)?;
            }
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

fn compositum_control(
    p: u64,
    coefficients: [u64; 3],
    wide: bool,
    output_variable: &str,
    header: &str,
) {
    let f = Field::new(CubicField::with_cubic(p, coefficients).unwrap());
    let q = Fp2Ctx::try_new(p).unwrap();
    for a in 0..p {
        for b in 0..p {
            let x = q.element(a, b);
            let y = q.element((a + 3) % p, (7 * b + 2) % p);
            assert_eq!(f.mul(&f.lift2(x), &f.lift2(y)), f.lift2(q.mul(x, y)));
            assert_eq!(f.add(&f.lift2(x), &f.lift2(y)), f.lift2(q.add(x, y)));
        }
    }
    let mut witness = format!("{header}\nn\tx\ty\tproduct\tinverse\tfrobenius3\tfrobenius6\n");
    let encode = |x: &Element| {
        (0..3)
            .map(|i| x.a.coeff(i).to_string())
            .chain((0..3).map(|i| x.b.coeff(i).to_string()))
            .collect::<Vec<_>>()
            .join(",")
    };
    for n in 0..128 {
        let seeds = if wide {
            [
                (37 * p * p + 19) * n + 13,
                (13 * p * p + 7 * p + 29) * n + 23,
                (29 * p * p + 11 * p + 7) * n + 31,
                (11 * p * p + 23 * p + 17) * n + 43,
            ]
        } else {
            [n, 37 * n + 19, 13 * n + 7, 29 * n + 11]
        };
        let x = Element {
            a: f.k.element(seeds[0] % p.pow(3)),
            b: f.k.element(seeds[1] % p.pow(3)),
        };
        assert!(!f.zero(&x));
        let inverse = f.inv(&x);
        assert_eq!(f.mul(&x, &inverse), f.c(1));
        assert_eq!(
            f.pow(&x, p.pow(3)),
            Element {
                a: x.a.clone(),
                b: x.b.neg()
            }
        );
        assert_eq!(f.pow(&x, p.pow(6)), x);
        let y = Element {
            a: f.k.element(seeds[2] % p.pow(3)),
            b: f.k.element(seeds[3] % p.pow(3)),
        };
        witness += &format!(
            "{n}\t{}\t{}\t{}\t{}\t{}\t{}\n",
            encode(&x),
            encode(&y),
            encode(&f.mul(&x, &y)),
            encode(&inverse),
            encode(&f.pow(&x, p.pow(3))),
            encode(&f.pow(&x, p.pow(6)))
        );
    }
    if let Ok(path) = std::env::var(output_variable) {
        std::fs::write(path, witness).unwrap();
    }
    println!("PASS F{p}² embeddings on{} pairs and128 compositum inverse/Frobenius controls, wide_seeds={wide}, using irreducible cubic and nonsquare quadratic adjunction",p*p);
}
#[test]
fn compositum_embeddings_inverses_and_frobenius() {
    compositum_control(
        17,
        [2, 2, 0],
        false,
        "CHAINED_F6_WITNESS_OUT",
        "# chained-nonsplit-field6/v1; p17; T^3+2T+2=0; s^2=3; a(T)+b(T)s",
    );
}
#[test]
fn shifted101_compositum_reference_witnesses() {
    compositum_control(
        101,
        [56, 13, 6],
        true,
        "CHAINED_SHIFTED_F6_WITNESS_OUT",
        "# chained-nonsplit-field6/v2; p101; T^3+6T^2+13T+56=0; s^2=2; a(T)+b(T)s; seeds=wide1",
    );
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

#[test]
fn shifted_prime109_full_domains_and_source_recovery() {
    use crate::balanced::QuadraticCover;
    use crate::reference::{HyperellipticCurveP as Curve, MumfordDivisorP};
    let r = RichelotMap::from_assessment(construct_for(101, [56, 13, 6]).unwrap()).unwrap();
    assert_eq!(r.target_scale, 22);
    let p = BigUint::from(101_u64);
    let base = Curve::try_new(
        p.clone(),
        FpPoly::from_coeffs(
            [56_u64, 13, 6, 1].into_iter().map(BigUint::from).collect(),
            p.clone(),
        ),
        1,
    )
    .unwrap();
    let cover = QuadraticCover::with_cubic(101, [56, 13, 6]).unwrap();
    let g = MumfordDivisorP::try_from_point(&base, &BigUint::from(0_u64), &BigUint::from(37_u64))
        .unwrap();
    let image = r.forward(&cover.pull(&g).unwrap()).unwrap();
    assert_ne!(image, r.target.zero());
    assert_eq!(r.target.mul(&image, 109).unwrap(), r.target.zero());
    for n in 0..109_u64 {
        let point = g.checked_scalar_mul(&BigUint::from(n), &base).unwrap();
        let transferred = r.forward(&cover.pull(&point).unwrap()).unwrap();
        assert_eq!(transferred, r.target.mul(&image, n).unwrap());
        let norm = cover.norm(&r.dual(&transferred).unwrap()).unwrap();
        assert_eq!(
            norm,
            point
                .checked_scalar_mul(&BigUint::from(4_u64), &base)
                .unwrap()
        );
        assert_eq!(
            norm.checked_scalar_mul(&BigUint::from(82_u64), &base)
                .unwrap(),
            point
        );
    }
    let source = r.source.classes().unwrap();
    let target = r.target.classes().unwrap();
    assert_eq!((source.len(), target.len()), (12317, 12317));
    let mut images = BTreeSet::new();
    for (i, d) in source.iter().enumerate() {
        let image = r
            .forward(d)
            .unwrap_or_else(|e| panic!("shifted source{i}: {e}"));
        assert_eq!(
            r.dual(&image).unwrap(),
            r.source.mul(d, 2).unwrap(),
            "shifted source dual{i}"
        );
        let e = &source[(7919 * i + 37) % source.len()];
        assert_eq!(
            r.forward(&r.source.add(d, e).unwrap()).unwrap(),
            r.target.add(&image, &r.forward(e).unwrap()).unwrap(),
            "shifted addition{i}"
        );
        let (u, v, n) = image.components();
        images.insert((u.coeffs.clone(), v.coeffs.clone(), n));
    }
    assert_eq!(images.len(), 12317);
    for (i, d) in target.iter().enumerate() {
        assert_eq!(
            r.forward(&r.dual(d).unwrap()).unwrap(),
            r.target.mul(d, 2).unwrap(),
            "shifted target dual{i}"
        );
    }
    println!("PASS frozen shifted E109/F101, delta63, raw scale22; all12317 source/target classes both dual norms[2], bijection/additivity/coefficient descent; all109 scalar/recovery[4]/inverse82 relations, no scalar labels in maps");
}

#[test]
fn accepted_target_elliptic_components_on_full_source_subgroups() {
    use crate::balanced::SplitQuotients;
    use crate::reference::MumfordDivisorP;
    for (p, coefficients, orders, generator, inverse_four) in [
        (17, [2, 2, 0], [19, 15], (5, 1), 5),
        (101, [56, 13, 6], [109, 113], (0, 37), 82),
    ] {
        let split = SplitQuotients::new(p, coefficients).unwrap();
        let r = RichelotMap::from_assessment(construct_for(p, coefficients).unwrap()).unwrap();
        let base = &split.first.base;
        let g = MumfordDivisorP::try_from_point(
            base,
            &BigUint::from(generator.0 as u64),
            &BigUint::from(generator.1 as u64),
        )
        .unwrap();
        let image = r.forward(&split.first.pull(&g).unwrap()).unwrap();
        for n in 0..orders[0] {
            let point = g.checked_scalar_mul(&BigUint::from(n), base).unwrap();
            let transferred = r.forward(&split.first.pull(&point).unwrap()).unwrap();
            assert_eq!(transferred, r.target.mul(&image, n).unwrap());
            let reversed = r.dual(&transferred).unwrap();
            let components = split.norms(&reversed).unwrap();
            assert_eq!(
                components.0,
                point
                    .checked_scalar_mul(&BigUint::from(4_u64), base)
                    .unwrap()
            );
            assert!(components.1.is_identity());
            assert_eq!(
                components
                    .0
                    .checked_scalar_mul(&BigUint::from(inverse_four as u64), base)
                    .unwrap(),
                point
            );
            assert_eq!(
                split
                    .reconstruct(&components.0, &components.1, orders)
                    .unwrap(),
                reversed
            );
        }
        let identity = MumfordDivisorP::identity(BigUint::from(p));
        assert!(split
            .reconstruct(&g, &identity, [orders[0] + 2, orders[1]])
            .is_err());
        println!("PASS F{p} target full r{} source subgroup has elliptic coordinates([4]P,0) after reversed Richelot/both norms,inverse{inverse_four} recovers P,all scalar/reconstruction controls,no scalar labels or solver", orders[0]);
    }
}

/// Geometric branch-pair classes and coefficient Frobenius. This accepts
/// extension classes directly, independently of the prime-field map wrapper.
fn branch_two_torsion(j: &Jacobian<'_>, roots: &[Element]) -> Vec<Divisor> {
    assert_eq!(roots.len(), 6);
    let k = j.k;
    let mut out = vec![];
    for (i, x) in roots.iter().enumerate() {
        assert!(k.zero(&k.value(&j.f, x)));
        assert!(!roots[..i].contains(x));
        for y in roots.iter().skip(i + 1) {
            let d = j
                .pair(vec![k.mul(x, y), k.neg(&k.add(x, y)), k.c(1)], vec![], 0)
                .unwrap();
            assert_ne!(d, j.zero());
            assert!(!out.contains(&d));
            assert_eq!(j.add(&d, &d).unwrap(), j.zero());
            out.push(d);
        }
    }
    assert_eq!(out.len(), 15);
    out
}

fn frobenius_class(k: &Field, d: &Divisor, power: u32) -> Divisor {
    let exponent = k.k.p.pow(power);
    Divisor {
        u: d.u.iter().map(|c| k.pow(c, exponent)).collect(),
        v: d.v.iter().map(|c| k.pow(c, exponent)).collect(),
        plus: d.plus,
    }
}

#[test]
fn accepted_targets_frobenius_two_torsion_and_next_kernels() {
    use super::{canonical_pairing, pairings, stable};
    for (p, coefficients) in [(17, [2, 2, 0]), (101, [56, 13, 6])] {
        let assessment = construct_for(p, coefficients).unwrap();
        let source_roots = assessment.roots.clone();
        let r = RichelotMap::from_assessment(assessment).unwrap();
        let k = &r.k;
        let cubic = &k.k;
        let source = Jacobian::new(k, &r.source);
        let target = Jacobian::new(k, &r.target);
        let mut target_roots = vec![];
        let mut discriminant_characters = vec![];
        for h in &r.h {
            assert_eq!(h.len(), 3);
            assert!(h.iter().all(|c| c.b.is_zero()));
            let d = cubic
                .mul(&h[1].a, &h[1].a)
                .sub(&cubic.mul(&cubic.c(4), &cubic.mul(&h[0].a, &h[2].a)));
            assert!(!d.is_zero());
            let square = if let Some(root) = cubic.sqrt(&d) {
                discriminant_characters.push(1_i8);
                k.lift3(&root)
            } else {
                discriminant_characters.push(-1_i8);
                let quotient = cubic.mul(&d, &cubic.inv(&k.nonresidue));
                Element {
                    a: cubic.z(),
                    b: cubic.sqrt(&quotient).unwrap(),
                }
            };
            assert_eq!(k.mul(&square, &square), k.lift3(&d));
            let denominator = k.inv(&k.mul(&k.c(2), &h[2]));
            target_roots.push(k.mul(&k.add(&k.neg(&h[1]), &square), &denominator));
            target_roots.push(k.mul(&k.sub(&k.neg(&h[1]), &square), &denominator));
        }
        // Label by actual Frobenius orbits, without assuming3+3 or a6-cycle.
        let mut ordered = vec![];
        for root in &target_roots {
            let mut x = root.clone();
            while !ordered.contains(&x) {
                assert!(target_roots.contains(&x));
                ordered.push(x.clone());
                x = k.pow(&x, p);
            }
        }
        assert_eq!(ordered.len(), 6);
        let permutation = std::array::from_fn(|i| {
            ordered
                .iter()
                .position(|x| *x == k.pow(&ordered[i], p))
                .unwrap()
        });
        let dual_pairing = canonical_pairing(std::array::from_fn(|i| {
            (
                ordered
                    .iter()
                    .position(|x| *x == target_roots[2 * i])
                    .unwrap(),
                ordered
                    .iter()
                    .position(|x| *x == target_roots[2 * i + 1])
                    .unwrap(),
            )
        }));
        let next = pairings()
            .into_iter()
            .filter(|pairing| stable(pairing, &permutation))
            .collect::<Vec<_>>();
        assert!(next.contains(&dual_pairing));
        assert_eq!(discriminant_characters, [-1, -1, -1]);
        assert_eq!(permutation, [1, 2, 3, 4, 5, 0]);
        assert_eq!(next, [dual_pairing]);
        let geometric_source = source_roots.iter().map(|x| k.lift3(x)).collect::<Vec<_>>();
        let source_torsion = branch_two_torsion(&source, &geometric_source);
        let target_torsion = branch_two_torsion(&target, &ordered);
        let source_fixed = 1 + source_torsion
            .iter()
            .filter(|d| frobenius_class(k, d, 3) == **d)
            .count();
        let target_fixed = 1 + target_torsion
            .iter()
            .filter(|d| frobenius_class(k, d, 3) == **d)
            .count();
        assert_eq!(source_fixed, 16);
        assert_eq!(target_fixed, 4);
        for d in source_torsion.iter().chain(&target_torsion) {
            assert_eq!(frobenius_class(k, d, 6), *d);
        }
        let mut kernel = 1;
        let mut images = vec![target.zero()];
        let mut ordered_images = vec![target.zero()];
        // For a degree2 branch pair, the completed infinity coefficient is0.
        // Evaluate both completed branch fibers, including y=0 cases.
        for i in 0..6 {
            for j in i + 1..6 {
                let a = r
                    .fiber(
                        &geometric_source[i],
                        &k.c(0),
                        &r.g,
                        &r.h,
                        r.target_scale,
                        &target,
                    )
                    .unwrap();
                let b = r
                    .fiber(
                        &geometric_source[j],
                        &k.c(0),
                        &r.g,
                        &r.h,
                        r.target_scale,
                        &target,
                    )
                    .unwrap();
                let image = target.add(&a, &b).unwrap();
                assert_eq!(target.add(&image, &image).unwrap(), target.zero());
                kernel += usize::from(image == target.zero());
                ordered_images.push(image.clone());
                if !images.contains(&image) {
                    images.push(image);
                }
            }
        }
        assert_eq!((kernel, images.len()), (4, 4));
        let mut all_source = vec![source.zero()];
        all_source.extend(source_torsion);
        for (i, d) in all_source.iter().enumerate() {
            let conjugate = frobenius_class(k, d, 1);
            source.check(&conjugate).unwrap();
            let index = all_source.iter().position(|a| *a == conjugate).unwrap();
            assert_eq!(
                ordered_images[index],
                frobenius_class(k, &ordered_images[i], 1)
            );
            for (j, e) in all_source.iter().enumerate() {
                let sum = source.add(d, e).unwrap();
                let index = all_source.iter().position(|a| *a == sum).unwrap();
                assert_eq!(
                    ordered_images[index],
                    target.add(&ordered_images[i], &ordered_images[j]).unwrap()
                );
            }
        }
        for d in &target_torsion {
            let conjugate = frobenius_class(k, d, 1);
            target.check(&conjugate).unwrap();
            assert!(target_torsion.contains(&conjugate));
        }
        println!("F{p} target discriminant characters{discriminant_characters:?}, branch Frobenius{permutation:?}, next stable{next:?}, previous dual{dual_pairing:?}; source/target2-torsion over Fp³ {source_fixed}/{target_fixed}; full geometric2-torsion16 each, map kernel{kernel}/image{}; all256 torsion additions and Frobenius-equivariant branch images pass", images.len());
    }
}

use std::collections::BTreeSet;
