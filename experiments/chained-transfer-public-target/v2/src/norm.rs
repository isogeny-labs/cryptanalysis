//! Independent actual canonical-class norm. Frozen protocol ac58df predates code.
//! All field, polynomial, linear-kernel, elliptic and Picard engines are original.
use ghs_original_engines::pic;
pub use ghs_original_engines::pic::{PicClass, PicKey};
use crate::{AdapterV2 as Adapter, EncodedPoint, Point};
use isogeny_algos::curve::{self, Curve, Pt};
use isogeny_algos::field::{Field, Rng};
use isogeny_algos::fpr::{FpR, ER};
use isogeny_algos::poly;
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet, HashMap, VecDeque};

pub type Result<T> = std::result::Result<T, String>;
type A3 = [u32; 3];
pub type GeoPoint = [ER; 3];
pub const MAX_INPUT_BYTES: usize = 65536;
pub const MAX_CLASSES: usize = 256;

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EncodedClass {
    pub field: String,
    pub model: String,
    pub key: [u32; 19],
}
#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Request {
    pub schema: String,
    pub q: u64,
    pub classes: Vec<EncodedClass>,
}
pub fn parse_request(bytes: &[u8]) -> Result<Request> {
    if bytes.len() > MAX_INPUT_BYTES {
        return Err("input exceeds byte bound".into());
    }
    let r: Request = serde_json::from_slice(bytes).map_err(|e| e.to_string())?;
    if r.schema != "g3-canonical-norm/v2" || r.classes.len() > MAX_CLASSES {
        return Err("schema or class-count bound".into());
    }
    Ok(r)
}
fn er(k: [u64; 3]) -> ER {
    let mut x = [0; 16];
    x[..3].copy_from_slice(&k);
    x
}
fn coeffs(q: u64, mut i: u64, r: usize) -> ER {
    let mut x = [0; 16];
    for c in x.iter_mut().take(r) {
        *c = i % q;
        i /= q;
    }
    assert_eq!(i, 0);
    x
}
fn digest(bytes: &[u8]) -> String {
    ghs_original_engines::digest::sha256(bytes)
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect()
}

pub struct NormV2 {
    pub a: Adapter,
    pub f: FpR,
    theta: ER,
    theta2: ER,
    b: ER,
    s: ER,
    alpha: ER,
    shift: ER,
    pub elliptic: Curve<ER>,
    pub offset: Pt<ER>,
    pub field_tag: String,
    pub model_tag: String,
}
impl NormV2 {
    pub fn new(a: Adapter) -> Result<Self> {
        let q = a.q;
        let f = FpR::new(q, 6);
        let modulus = a.modulus.iter().map(|&c| f.from_u64(c)).collect();
        let roots = poly::roots(&f, &modulus, &mut Rng::new(20261113 + q));
        if roots.len() != 3 {
            return Err("cubic embedding".into());
        }
        let theta = roots[0];
        let theta2 = f.sq(theta);
        let embed = |x: [u64; 3]| {
            f.add(
                f.add(f.from_u64(x[0]), f.mul(f.from_u64(x[1]), theta)),
                f.mul(f.from_u64(x[2]), theta2),
            )
        };
        let u0 = vec![embed(a.uc), embed(a.ub), f.one()];
        let u2 = u0.iter().map(|&x| f.pow(x, q.pow(2) as u128)).collect();
        let quartic = poly::mul(&f, &u0, &u2);
        let b = f.div(quartic[3], f.from_u64(2));
        let s = f.div(f.sub(quartic[2], f.sq(b)), f.from_u64(2));
        let alpha = f.sub(quartic[1], f.mul(f.from_u64(2), f.mul(b, s)));
        let beta = f.sub(quartic[0], f.sq(s));
        if f.is_zero(alpha) {
            return Err("unsupported alpha zero".into());
        }
        let c2 = f.sub(f.sq(b), f.mul(f.from_u64(4), s));
        let c4 = f.sub(
            f.mul(f.from_u64(2), f.mul(b, alpha)),
            f.mul(f.from_u64(4), beta),
        );
        let shift = f.div(c2, f.from_u64(3));
        let ea = f.sub(c4, f.div(f.sq(c2), f.from_u64(3)));
        let eb = f.add(
            f.sub(f.sq(alpha), f.div(f.mul(c2, c4), f.from_u64(3))),
            f.div(f.mul(f.from_u64(2), f.mul(f.sq(c2), c2)), f.from_u64(27)),
        );
        if ea != embed(a.core.ea)
            || eb != embed(a.core.eb)
            || shift != embed(a.core.wshift)
            || alpha != embed(a.core.walpha)
        {
            return Err("independent short-model mismatch".into());
        }
        let field_tag = format!("Fq-{q}");
        let model_tag = format!(
            "Ciani-Jac-pi0-v2-{}",
            digest(
                format!(
                    "{q}:{:?}:{:?}:{}:{}",
                    a.core.quartic,
                    a.pic.base_point(),
                    a.field_tag,
                    a.model_tag
                )
                .as_bytes()
            )
        );
        let mut n = Self {
            a,
            f,
            theta,
            theta2,
            b,
            s,
            alpha,
            shift,
            elliptic: Curve::new(ea, eb),
            offset: Pt::Inf,
            field_tag,
            model_tag,
        };
        let offsets = n.line_offsets()?;
        if offsets.len() != q as usize + 1 || !offsets.iter().all(|x| *x == offsets[0]) {
            return Err("plane-line norm offset not invariant".into());
        }
        n.offset = offsets[0];
        Ok(n)
    }
    pub fn embed(&self, x: [u64; 3]) -> ER {
        self.f.add(
            self.f.add(
                self.f.from_u64(x[0]),
                self.f.mul(self.f.from_u64(x[1]), self.theta),
            ),
            self.f.mul(self.f.from_u64(x[2]), self.theta2),
        )
    }
    pub fn addq(&self, x: u32, y: u32) -> u32 {
        self.a.field.f.add(x as u64, y as u64) as u32
    }
    pub fn mulq(&self, x: u32, y: u32) -> u32 {
        self.a.field.f.mul(x as u64, y as u64) as u32
    }
    pub fn negq(&self, x: u32) -> u32 {
        self.a.field.f.neg(x as u64) as u32
    }
    fn dot(&self, a: &[u32], b: &[u32]) -> u32 {
        assert_eq!(a.len(), b.len());
        a.iter()
            .zip(b)
            .fold(0, |sum, (&x, &y)| self.addq(sum, self.mulq(x, y)))
    }
    fn project(&self, rows: &[Vec<u32>], value: &[u32]) -> A3 {
        assert_eq!(rows.len(), 3);
        std::array::from_fn(|i| self.dot(&rows[i], value))
    }
    fn solve(&self, matrix: &[Vec<u32>], rhs: &[u32]) -> Result<A3> {
        if matrix.len() != rhs.len() || matrix.iter().any(|r| r.len() != 3) {
            return Err("linear-system shape".into());
        }
        let eqs: Vec<_> = matrix
            .iter()
            .zip(rhs)
            .map(|(row, &v)| {
                let mut r = row.clone();
                r.push(self.negq(v));
                r
            })
            .collect();
        let kernel = self.a.pic.linear_kernel(eqs, 4);
        if kernel.len() != 1 || kernel[0][3] == 0 {
            return Err("nonunique original-kernel solve".into());
        }
        let inv = self.a.field.f.inv(kernel[0][3] as u64) as u32;
        Ok(std::array::from_fn(|i| self.mulq(kernel[0][i], inv)))
    }
    fn matrix(cols: &[A3; 3]) -> Vec<Vec<u32>> {
        (0..3)
            .map(|r| (0..3).map(|c| cols[c][r]).collect())
            .collect()
    }
    pub fn point_on_quartic(&self, p: GeoPoint) -> bool {
        let f = &self.f;
        let value = pic::mons_of_degree(4)
            .into_iter()
            .zip(self.a.core.quartic.iter())
            .fold(f.zero(), |sum, ((i, j, k), &c)| {
                f.add(
                    sum,
                    f.mul(
                        f.from_u64(c),
                        f.mul(
                            f.mul(f.pow(p[0], i as u128), f.pow(p[1], j as u128)),
                            f.pow(p[2], k as u128),
                        ),
                    ),
                )
            });
        p.iter().any(|&x| !f.is_zero(x)) && f.is_zero(value)
    }
    pub fn cover(&self, w: GeoPoint) -> Result<Pt<ER>> {
        if !self.point_on_quartic(w) {
            return Err("point off actual quartic".into());
        }
        let f = &self.f;
        let xyz: GeoPoint = std::array::from_fn(|i| {
            (0..3).fold(f.zero(), |s, j| {
                f.add(s, f.mul(self.embed(self.a.core.omi[i][j]), w[j]))
            })
        });
        let squares = [f.sq(xyz[2]), f.sq(xyz[0]), f.sq(xyz[1])];
        let row = |i: usize| {
            (0..3).fold(f.zero(), |s, j| {
                f.add(s, f.mul(self.embed(self.a.core.rmat[i][j]), squares[j]))
            })
        };
        let s0 = row(0);
        let s1 = row(1);
        let result = if f.is_zero(s0) {
            if f.is_zero(xyz[2]) {
                return Err("invalid infinity cover chart".into());
            }
            let ratio = f.div(xyz[1], xyz[2]);
            if ratio == f.one() {
                Pt::Inf
            } else if ratio == f.neg(f.one()) {
                Pt::Aff(self.shift, f.neg(self.alpha))
            } else {
                return Err("invalid infinity sign".into());
            }
        } else {
            let t = f.div(s1, s0);
            let u0 = f.add(
                f.add(f.sq(t), f.mul(self.embed(self.a.ub), t)),
                self.embed(self.a.uc),
            );
            let y = if f.is_zero(xyz[2]) {
                if !f.is_zero(u0) {
                    return Err("invalid u0 chart".into());
                }
                f.zero()
            } else {
                f.mul(u0, f.div(xyz[1], xyz[2]))
            };
            let x = f.mul(
                f.from_u64(2),
                f.add(f.add(f.add(y, f.sq(t)), f.mul(self.b, t)), self.s),
            );
            let yy = f.add(
                f.add(f.mul(f.mul(f.from_u64(2), x), t), f.mul(self.b, x)),
                self.alpha,
            );
            Pt::Aff(f.add(x, self.shift), yy)
        };
        if !curve::on_curve(f, &self.elliptic, &result) {
            return Err("cover image off independent elliptic model".into());
        }
        Ok(result)
    }
    fn weighted_sum(&self, cycle: &[(GeoPoint, usize)]) -> Result<Pt<ER>> {
        let mut sum = Pt::Inf;
        for &(p, m) in cycle {
            let point = self.cover(p)?;
            sum = curve::padd(
                &self.f,
                &self.elliptic,
                &sum,
                &curve::pmul(&self.f, &self.elliptic, &point, m as u128),
            );
        }
        Ok(sum)
    }
    pub fn roots_with_multiplicity(&self, p: &[ER]) -> Result<Vec<(ER, usize)>> {
        let f = &self.f;
        let mut remaining = p.to_vec();
        poly::trim(f, &mut remaining);
        if remaining.is_empty() {
            return Err("zero cycle polynomial".into());
        }
        let degree = remaining.len() - 1;
        let roots = poly::roots(f, &remaining, &mut Rng::new(2026111300 + self.a.q));
        let mut out = vec![];
        for root in roots {
            let mut m = 0;
            while remaining.len() > 1 && f.is_zero(poly::eval(f, &remaining, root)) {
                let (quotient, remainder) =
                    poly::divrem(f, &remaining, &vec![f.neg(root), f.one()]);
                if remainder.iter().any(|&x| !f.is_zero(x)) {
                    return Err("inexact original root division".into());
                }
                remaining = quotient;
                m += 1;
            }
            if m == 0 {
                return Err("duplicate root".into());
            }
            out.push((root, m));
        }
        if out.iter().map(|x| x.1).sum::<usize>() != degree || remaining.len() != 1 {
            return Err("cycle did not split completely".into());
        }
        Ok(out)
    }
    pub fn line_offsets(&self) -> Result<Vec<Pt<ER>>> {
        let p0 = self.a.pic.base_point();
        let q = self.a.q;
        let mut lines = BTreeSet::new();
        for i in 1..q.pow(3) {
            let x = coeffs(q, i, 3);
            let mut l = [x[0] as u32, x[1] as u32, x[2] as u32];
            if self.dot(&l, &p0) != 0 {
                continue;
            }
            let first = *l.iter().find(|&&x| x != 0).unwrap();
            let inv = self.a.field.f.inv(first as u64) as u32;
            for v in &mut l {
                *v = self.mulq(*v, inv);
            }
            lines.insert(l);
        }
        let f = &self.f;
        let mut offsets = vec![];
        for line in lines {
            let basis = self.a.pic.linear_kernel(vec![line.to_vec()], 3);
            let r = basis
                .iter()
                .find(|v| {
                    (0..3).any(|i| (0..3).any(|j| self.mulq(p0[i], v[j]) != self.mulq(p0[j], v[i])))
                })
                .ok_or("line parameter basis")?;
            let axes: [Vec<ER>; 3] =
                std::array::from_fn(|i| vec![f.from_u64(p0[i] as u64), f.from_u64(r[i] as u64)]);
            let mut restriction = vec![];
            for ((i, j, k), &c) in pic::mons_of_degree(4)
                .into_iter()
                .zip(self.a.core.quartic.iter())
            {
                let mut term = vec![f.from_u64(c)];
                for (axis, e) in [(0, i), (1, j), (2, k)] {
                    for _ in 0..e {
                        term = poly::mul(f, &term, &axes[axis]);
                    }
                }
                restriction = poly::add(f, &restriction, &term);
            }
            poly::trim(f, &mut restriction);
            if restriction.is_empty() || restriction.len() < 2 || !f.is_zero(restriction[0]) {
                return Err("invalid plane line restriction".into());
            }
            let infinity = 5 - restriction.len();
            let residual = restriction[1..].to_vec();
            let mut cycle = vec![];
            for (t, m) in self.roots_with_multiplicity(&residual)? {
                cycle.push((
                    std::array::from_fn(|i| f.add(axes[i][0], f.mul(t, axes[i][1]))),
                    m,
                ));
            }
            if infinity > 0 {
                cycle.push((std::array::from_fn(|i| axes[i][1]), infinity));
            }
            if cycle.iter().map(|x| x.1).sum::<usize>() != 3 {
                return Err("wrong Dinf degree".into());
            }
            offsets.push(self.weighted_sum(&cycle)?);
        }
        Ok(offsets)
    }
    pub fn norm_ext(&self, class: &PicClass, chart_variant: usize) -> Result<Pt<ER>> {
        match class {
            PicClass::Exc(p) => {
                if p.iter().any(|&x| x as u64 >= self.a.q)
                    || p.iter().find(|&&x| x != 0) != Some(&1)
                {
                    return Err("noncanonical exceptional point".into());
                }
                let p0 = self.a.pic.base_point().map(|x| self.f.from_u64(x as u64));
                let pp = p.map(|x| self.f.from_u64(x as u64));
                let result = curve::padd(
                    &self.f,
                    &self.elliptic,
                    &self.cover(p0)?,
                    &curve::neg(&self.f, &self.cover(pp)?),
                );
                Ok(result)
            }
            PicClass::Typ(m) => {
                let algebra = Algebra::new(self, m, chart_variant)?;
                let cycle = algebra.cycle(self)?;
                Ok(curve::padd(
                    &self.f,
                    &self.elliptic,
                    &self.weighted_sum(&cycle)?,
                    &curve::neg(&self.f, &self.offset),
                ))
            }
        }
    }
    fn project_k(&self, x: ER) -> Result<[u64; 3]> {
        if self.f.pow(x, self.a.q.pow(3) as u128) != x {
            return Err("norm not K-rational".into());
        }
        let basis = [self.f.one(), self.theta, self.theta2];
        let matrix: Vec<_> = (0..16)
            .map(|i| (0..3).map(|j| basis[j][i] as u32).collect())
            .collect();
        let rhs: Vec<_> = x.iter().map(|&v| v as u32).collect();
        let a = self.solve(&matrix, &rhs)?.map(u64::from);
        if self.embed(a) != x {
            return Err("K projection check".into());
        }
        Ok(a)
    }
    pub fn norm(&self, class: &PicClass) -> Result<Point> {
        let point = match self.norm_ext(class, 0)? {
            Pt::Inf => None,
            Pt::Aff(x, y) => Some((self.project_k(x)?, self.project_k(y)?)),
        };
        self.a.admit(&point)?;
        Ok(point)
    }
    pub fn encode(&self, class: &PicClass) -> EncodedClass {
        EncodedClass {
            field: self.field_tag.clone(),
            model: self.model_tag.clone(),
            key: class.key().0,
        }
    }
    pub fn decode(&self, packet: &EncodedClass) -> Result<PicClass> {
        if packet.field != self.field_tag
            || packet.model != self.model_tag
            || packet.key.iter().any(|&x| x as u64 >= self.a.q)
        {
            return Err("foreign or noncanonical class".into());
        }
        let class = match packet.key[0] {
            0 => {
                if packet.key[4..].iter().any(|&x| x != 0) {
                    return Err("exceptional trailing data".into());
                }
                PicClass::Exc([packet.key[1], packet.key[2], packet.key[3]])
            }
            1 => PicClass::Typ(std::array::from_fn(|i| {
                std::array::from_fn(|j| packet.key[1 + 6 * i + j])
            })),
            _ => return Err("unknown class tag".into()),
        };
        self.norm_ext(&class, 0)?;
        Ok(class)
    }
    /// Additive diagnostic: expose the original scheme cycle and omission control.
    pub fn multiplicity_audit(&self, class: &PicClass) -> Result<(Vec<usize>, bool)> {
        let PicClass::Typ(rows) = class else { return Err("typical scheme required".into()); };
        let algebra = Algebra::new(self, rows, 0)?;
        let cycle = algebra.cycle(self)?;
        let reduced: Vec<_> = cycle.iter().map(|&(p, _)| (p, 1)).collect();
        let wrong = curve::padd(&self.f, &self.elliptic, &self.weighted_sum(&reduced)?, &curve::neg(&self.f, &self.offset));
        Ok((cycle.iter().map(|x| x.1).collect(), wrong != self.norm_ext(class, 0)?))
    }
    pub fn evaluate(&self, packet: &EncodedClass) -> Result<EncodedPoint> {
        Ok(self.a.encode(self.norm(&self.decode(packet)?)?))
    }

}

struct Algebra {
    q4: Vec<Vec<u32>>,
    basis: [Vec<u32>; 3],
    m4: Vec<Vec<u32>>,
    unit: A3,
    coordinates: [A3; 3],
    variant: usize,
}
impl Algebra {
    fn new(n: &NormV2, rows: &[[u32; 6]; 3], variant: usize) -> Result<Self> {
        if rows.iter().flatten().any(|&x| x as u64 >= n.a.q) {
            return Err("noncanonical conic coefficient".into());
        }
        let conics: Vec<_> = rows.iter().map(|x| x.to_vec()).collect();
        if n.a.pic.linear_kernel(conics.clone(), 6).len() != 3
            || n.a.pic.class_from_conics(conics.clone()) != PicClass::Typ(*rows)
        {
            return Err("noncanonical conic RREF/rank".into());
        }
        let q2 = n.a.pic.linear_kernel(conics.clone(), 6);
        let mut products = vec![];
        for c in &conics {
            for i in 0..6 {
                let mut e = vec![0; 6];
                e[i] = 1;
                products.push(n.a.pic.mul_forms(2, c, 2, &e));
            }
        }
        let width = products[0].len();
        let q4 = n.a.pic.linear_kernel(products, width);
        if q4.len() != 3 {
            return Err("conics do not define degree-three scheme".into());
        }
        let mut chosen = None;
        'find: for i in 0..6 {
            for j in i + 1..6 {
                for k in j + 1..6 {
                    let indices = [i, j, k];
                    let cols = indices.map(|c| std::array::from_fn(|r| q2[r][c]));
                    let m = NormV2::matrix(&cols);
                    if n.a.pic.linear_kernel(m.clone(), 3).is_empty() {
                        chosen = Some((indices, m));
                        break 'find;
                    }
                }
            }
        }
        let (indices, m2) = chosen.ok_or("degree-two quotient basis")?;
        let basis = indices.map(|i| {
            let mut v = vec![0; 6];
            v[i] = 1;
            v
        });
        let mut result = None;
        let mut charts = 0;
        let mut seen = BTreeSet::new();
        for i in 1..n.a.q.pow(3) {
            let raw = coeffs(n.a.q, i, 3);
            let mut l = [raw[0] as u32, raw[1] as u32, raw[2] as u32];
            let first = *l.iter().find(|&&x| x != 0).unwrap();
            let inv = n.a.field.f.inv(first as u64) as u32;
            for v in &mut l {
                *v = n.mulq(*v, inv);
            }
            if !seen.insert(l) {
                continue;
            }
            let l2 = n.a.pic.mul_forms(1, &l, 1, &l);
            let cols =
                std::array::from_fn(|j| n.project(&q4, &n.a.pic.mul_forms(2, &l2, 2, &basis[j])));
            let m4 = NormV2::matrix(&cols);
            if !n.a.pic.linear_kernel(m4.clone(), 3).is_empty() {
                continue;
            }
            if charts < variant {
                charts += 1;
                continue;
            }
            let unit = n.solve(&m2, &n.project(&q2, &l2))?;
            let mut coordinates = [[0; 3]; 3];
            for axis in 0..3 {
                let mut e = [0; 3];
                e[axis] = 1;
                coordinates[axis] =
                    n.solve(&m2, &n.project(&q2, &n.a.pic.mul_forms(1, &e, 1, &l)))?;
            }
            result = Some(Self {
                q4: q4.clone(),
                basis: basis.clone(),
                m4,
                unit,
                coordinates,
                variant,
            });
            break;
        }
        let a = result.ok_or("no valid affine divisor chart")?;
        for i in 0..3 {
            let mut e = [0; 3];
            e[i] = 1;
            if a.mul(n, a.unit, e)? != e {
                return Err("algebra unit".into());
            }
            for j in 0..3 {
                let mut b = [0; 3];
                b[j] = 1;
                if a.mul(n, e, b)? != a.mul(n, b, e)? {
                    return Err("algebra commutativity".into());
                }
                for k in 0..3 {
                    let mut c = [0; 3];
                    c[k] = 1;
                    if a.mul(n, a.mul(n, e, b)?, c)? != a.mul(n, e, a.mul(n, b, c)?)? {
                        return Err("algebra associativity".into());
                    }
                }
            }
        }
        let mut value = [0; 3];
        for ((i, j, k), &c) in pic::mons_of_degree(4)
            .into_iter()
            .zip(n.a.core.quartic.iter())
        {
            let term = a.monomial(n, (i, j, k))?;
            for r in 0..3 {
                value[r] = n.addq(value[r], n.mulq(c as u32, term[r]));
            }
        }
        if value != [0; 3] {
            return Err("actual quartic fails in nilpotent algebra".into());
        }
        for row in rows {
            let mut value = [0; 3];
            for (e, &c) in pic::mons_of_degree(2).into_iter().zip(row) {
                let term = a.monomial(n, e)?;
                for r in 0..3 {
                    value[r] = n.addq(value[r], n.mulq(c, term[r]));
                }
            }
            if value != [0; 3] {
                return Err("conic fails in divisor algebra".into());
            }
        }
        Ok(a)
    }
    fn polynomial(&self, n: &NormV2, x: A3) -> Vec<u32> {
        (0..6)
            .map(|i| (0..3).fold(0, |s, j| n.addq(s, n.mulq(x[j], self.basis[j][i]))))
            .collect()
    }
    fn mul(&self, n: &NormV2, x: A3, y: A3) -> Result<A3> {
        n.solve(
            &self.m4,
            &n.project(
                &self.q4,
                &n.a.pic
                    .mul_forms(2, &self.polynomial(n, x), 2, &self.polynomial(n, y)),
            ),
        )
    }
    fn monomial(&self, n: &NormV2, e: (u8, u8, u8)) -> Result<A3> {
        let mut v = self.unit;
        for (i, power) in [e.0, e.1, e.2].into_iter().enumerate() {
            for _ in 0..power {
                v = self.mul(n, v, self.coordinates[i])?;
            }
        }
        Ok(v)
    }
    fn cycle(&self, n: &NormV2) -> Result<Vec<(GeoPoint, usize)>> {
        let mut chosen = None;
        let mut count = 0;
        for i in 0..n.a.q.pow(3) {
            let raw = coeffs(n.a.q, i, 3);
            let t = [raw[0] as u32, raw[1] as u32, raw[2] as u32];
            let t2 = self.mul(n, t, t)?;
            let matrix = NormV2::matrix(&[self.unit, t, t2]);
            if !n.a.pic.linear_kernel(matrix.clone(), 3).is_empty() {
                continue;
            }
            if count < self.variant {
                count += 1;
                continue;
            }
            let t3 = self.mul(n, t2, t)?;
            let c = n.solve(&matrix, &t3)?;
            chosen = Some((matrix, c));
            break;
        }
        let (matrix, c) = chosen.ok_or("degree-three algebra not monogenic")?;
        let polynomial = vec![
            n.f.from_u64(n.negq(c[0]) as u64),
            n.f.from_u64(n.negq(c[1]) as u64),
            n.f.from_u64(n.negq(c[2]) as u64),
            n.f.one(),
        ];
        let coordinates: Vec<Vec<ER>> = self
            .coordinates
            .iter()
            .map(|&x| {
                n.solve(&matrix, &x)
                    .map(|v| v.into_iter().map(|x| n.f.from_u64(x as u64)).collect())
            })
            .collect::<Result<_>>()?;
        let mut out = vec![];
        for (root, m) in n.roots_with_multiplicity(&polynomial)? {
            let p = std::array::from_fn(|i| poly::eval(&n.f, &coordinates[i], root));
            if !n.point_on_quartic(p) {
                return Err("decoded divisor point off curve".into());
            }
            out.push((p, m));
        }
        if out.iter().map(|x| x.1).sum::<usize>() != 3 {
            return Err("cycle degree".into());
        }
        Ok(out)
    }
}
