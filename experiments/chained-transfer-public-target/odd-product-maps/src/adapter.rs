//! New model/P0/origin/normal forms; original field and Picard operations only.
use chained_n4_completed_v2::AdapterV2;
use chained_n4_odd_product_models::SourceE;
use chained_n4_odd_product_models::{
    adj, det, er,
    even::{back6, lift6},
    k, three, GluingModel,
};
use ghs_original_engines::{
    cover::{self, Kf, Mono, Poly3, K},
    pic::{self, Gen, PicClass, PlaneQuartic},
};
use isogeny_algos::{
    curve::{self, Curve, Pt},
    field::{Field, Rng},
    fpr::{FpR, ER},
    poly,
};
use serde::{Deserialize, Serialize};
pub type Result<T> = std::result::Result<T, String>;
pub type Point = Option<(K, K)>;
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EncodedPoint {
    pub field: String,
    pub model: String,
    pub coordinates: Point,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum QuarticPoint {
    Finite(K, K),
    Infinity(K),
}
pub struct Core {
    pub quartic: [u64; 15],
    pub omi: [[K; 3]; 3],
}
pub struct Adapter {
    pub q: u64,
    pub field: Kf,
    pub core: Core,
    pub pic: PlaneQuartic,
    pub ell: u64,
    pub expected_order: u64,
    pub field_tag: String,
    pub model_tag: String,
    pub modulus: Vec<u64>,
    pub f6: FpR,
    pub f3: FpR,
    pub source_ec: Curve<ER>,
    pub elliptic6: Curve<ER>,
    pub root: ER,
    pub factor: ER,
    pub sqrt_d: ER,
    pub alpha: ER,
    pub beta: ER,
    pub gamma: ER,
    pub sqrt_alpha: ER,
    pub ciani: [ER; 6],
    pub candidate: (usize, usize),
    pub kernel_mask: u64,
    pub raw_p0: Pt<ER>,
    normal6: Vec<Vec<u32>>,
    origin: PicClass,
}
fn sha(bytes: &[u8]) -> String {
    ghs_original_engines::digest::sha256(bytes)
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect()
}
fn linear(row: &[K; 3]) -> Poly3 {
    [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
        .into_iter()
        .zip(row.iter().copied())
        .filter(|(_, c)| *c != [0; 3])
        .collect()
}
fn monomial(e: Mono, c: K) -> Poly3 {
    [(e, c)].into_iter().collect()
}
fn conjugate(f: &Kf, p: &Poly3) -> Poly3 {
    p.iter().map(|(&e, c)| (e, f.frob(c))).collect()
}
fn project6(x: ER) -> Result<K> {
    if x.iter()
        .enumerate()
        .any(|(i, &v)| i != 0 && i != 2 && i != 4 && v != 0)
    {
        return Err("coordinate does not descend to original K".into());
    }
    Ok([x[0], x[2], x[4]])
}
impl Adapter {
    pub fn new(c: &SourceE, old: &AdapterV2, m: GluingModel) -> Result<Self> {
        Self::with_base_point(c, old, m, None)
    }
    pub fn with_base_point(
        c: &SourceE,
        old: &AdapterV2,
        m: GluingModel,
        base: Option<[u32; 3]>,
    ) -> Result<Self> {
        if !m.p0.is_some() || m.square_root.is_none() {
            return Err("singular or nonsquare-twist gluing is not eligible".into());
        }
        let f3 = FpR::from_modulus(223, &[220, 0, 0, 1]);
        let f6 = FpR::from_modulus(223, &[220, 0, 0, 0, 0, 0, 1]);
        if det(&f3, &m.h_matrix) != m.determinant
            || adj(&f3, &m.h_matrix) != m.q_matrix
            || f3.mul(k(16), m.determinant) != m.factor
            || f3.mul(m.square_root.unwrap(), m.square_root.unwrap()) != m.factor
        {
            return Err("gluing model identity rejected".into());
        }
        let source_ec = *c.curve();
        if !curve::on_curve(&f3, &source_ec, &Pt::Aff(m.root, f3.zero())) {
            return Err("foreign source root".into());
        }
        let mut actual_a = f3.mul(k(3), m.root);
        let mut actual_b = f3.add(f3.mul(k(3), f3.mul(m.root, m.root)), source_ec.a);
        for i in 0..3 {
            if m.source_a[i] != actual_a || m.source_b[i] != actual_b {
                return Err("foreign translated source or conjugate coefficients".into());
            }
            actual_a = f3.frobenius(actual_a);
            actual_b = f3.frobenius(actual_b);
        }
        let cs = chained_n4_odd_product_models::coefficients(&f3, &m.q_matrix);
        let [a, b, cc, d, _e, g] = cs;
        let alpha = f3.sub(f3.mul(d, d), f3.mul(k(4), f3.mul(a, b)));
        let beta = f3.sub(f3.mul(k(2), f3.mul(d, g)), f3.mul(k(4), f3.mul(a, cs[4])));
        let gamma = f3.sub(f3.mul(g, g), f3.mul(k(4), f3.mul(a, cc)));
        if alpha == k(0)
            || f3.neg(f3.mul(k(2), beta)) != f3.mul(m.factor, m.source_a[0])
            || f3.sub(f3.mul(beta, beta), f3.mul(k(4), f3.mul(alpha, gamma)))
                != f3.mul(f3.mul(m.factor, m.factor), m.source_b[0])
        {
            return Err("quotient/source identity rejected".into());
        }
        let mut roots = poly::roots(
            &f6,
            &vec![f6.neg(lift6(alpha)), f6.zero(), f6.one()],
            &mut Rng::new(0x6021),
        );
        roots.sort();
        if roots.len() != 2 {
            return Err("quotient leading root not in L6".into());
        }
        let p0 = base.unwrap_or(
            pic::first_rational_point_canonical(223, &m.normalized).ok_or("no canonical P0")?,
        );
        let pic = PlaneQuartic::new(223, m.normalized, p0)
            .map_err(|e| format!("original Picard:{e:?}"))?;
        let core = Core {
            quartic: m.normalized.map(u64::from),
            omi: old.core.omi,
        };
        let mut field = Kf {
            f: cover::Fq::new(223),
            a: 0,
            b: 220,
            gq: [0; 3],
            gq2: [0; 3],
        };
        field.gq = field.pow([0, 1, 0], 223);
        field.gq2 = field.mul(&field.gq, &field.gq);
        for x in [[1, 0, 0], [0, 1, 0], [0, 0, 1]] {
            if field.frob(&x) != three(f3.frobenius(er(x))) {
                return Err("actual cubic Frobenius basis mismatch".into());
            }
            for y in [[1, 0, 0], [0, 1, 0], [0, 0, 1]] {
                if field.mul(&x, &y) != three(f3.mul(er(x), er(y))) {
                    return Err("actual cubic product basis mismatch".into());
                }
            }
        }
        if field.q() != 223 {
            return Err("field prime mismatch".into());
        }
        let mut normal6 = Vec::new();
        for (a, b, c) in pic::mons_of_degree(6) {
            let mut v = vec![1u32];
            let mut degree = 0;
            for (axis, n) in [a, b, c].into_iter().enumerate() {
                for _ in 0..n {
                    let mut x = vec![0; 3];
                    x[axis] = 1;
                    v = pic.mul_forms(degree, &v, 1, &x);
                    degree += 1;
                }
            }
            normal6.push(v);
        }
        let field_tag = c.field_tag().to_owned();
        let model_tag = format!(
            "Ciani-odd-product-v1-{}",
            sha(format!(
                "{}:{:?}:{p0:?}:{:?}:{:?}:{:?}",
                c.source_tag(),
                m.normalized,
                three(m.root),
                three(m.factor),
                three(m.square_root.unwrap())
            )
            .as_bytes())
        );
        let elliptic6 = Curve::new(lift6(source_ec.a), lift6(source_ec.b));
        let origin = pic.zero();
        let mut out = Self {
            q: 223,
            field,
            core,
            pic,
            ell: c.ell(),
            expected_order: c.order() as u64,
            field_tag,
            model_tag,
            modulus: vec![220, 0, 0, 1],
            f6,
            f3,
            source_ec,
            elliptic6,
            root: m.root,
            factor: m.factor,
            sqrt_d: m.square_root.unwrap(),
            alpha,
            beta,
            gamma,
            sqrt_alpha: roots[0],
            ciani: cs,
            candidate: (m.root_index, m.sign_index),
            kernel_mask: m.kernel_mask,
            raw_p0: Pt::Inf,
            normal6,
            origin,
        };
        out.raw_p0 = out.raw_cover(out.pic.base_point().map(|x| k(x as u64)))?;
        out.origin = out.pic.reduce_deg6(&out.trace_space(&None)?);
        Ok(out)
    }
    pub fn admit(&self, p: &Point) -> Result<()> {
        if let Some((x, y)) = p {
            if x.iter().chain(y).any(|&v| v >= 223)
                || !curve::on_curve(&self.f3, &self.source_ec, &Pt::Aff(er(*x), er(*y)))
            {
                return Err("noncanonical/off-source point".into());
            }
        }
        Ok(())
    }
    pub fn encode(&self, p: Point) -> EncodedPoint {
        EncodedPoint {
            field: self.field_tag.clone(),
            model: self.model_tag.clone(),
            coordinates: p,
        }
    }
    pub fn decode(&self, p: &EncodedPoint) -> Result<Point> {
        if p.field != self.field_tag || p.model != self.model_tag {
            return Err("foreign field/model/P0 tag".into());
        }
        self.admit(&p.coordinates)?;
        Ok(p.coordinates)
    }
    pub fn moore_point(&self, w: [ER; 3]) -> [ER; 3] {
        let f = &self.f6;
        std::array::from_fn(|i| {
            (0..3).fold(f.zero(), |v, j| {
                f.add(v, f.mul(lift6(er(self.core.omi[i][j])), w[j]))
            })
        })
    }
    pub fn point_on_quartic(&self, w: [ER; 3]) -> bool {
        if w.iter().all(|&x| self.f6.is_zero(x)) {
            return false;
        }
        let f = &self.f6;
        let value = pic::mons_of_degree(4)
            .into_iter()
            .zip(self.core.quartic)
            .fold(f.zero(), |v, ((a, b, c), co)| {
                f.add(
                    v,
                    f.mul(
                        k(co),
                        f.mul(
                            f.pow(w[0], a as u128),
                            f.mul(f.pow(w[1], b as u128), f.pow(w[2], c as u128)),
                        ),
                    ),
                )
            });
        f.is_zero(value)
    }
    pub fn raw_cover_with_sign(&self, w: [ER; 3], negative: bool) -> Result<Pt<ER>> {
        if !self.point_on_quartic(w) {
            return Err("cover point is off new quartic".into());
        }
        let f = &self.f6;
        let [x, y, z] = self.moore_point(w);
        let [a, _b, _c, d, _e, g] = self.ciani.map(lift6);
        let s = if negative {
            f.neg(self.sqrt_alpha)
        } else {
            self.sqrt_alpha
        };
        let out = if f.is_zero(z) {
            if f.is_zero(y) {
                return Err("invalid quotient infinity".into());
            }
            let leading = f.add(f.mul(k(2), f.mul(a, f.sq(f.div(x, y)))), d);
            if leading == s {
                Pt::Inf
            } else if leading == f.neg(s) {
                Pt::Aff(lift6(self.root), f.zero())
            } else {
                return Err("wrong infinity leading sign".into());
            }
        } else {
            let t = f.div(y, z);
            let u = f.div(x, z);
            let v = f.add(f.mul(k(2), f.mul(a, f.sq(u))), f.add(f.mul(d, f.sq(t)), g));
            if f.sq(v)
                != f.add(
                    f.mul(lift6(self.alpha), f.pow(t, 4)),
                    f.add(f.mul(lift6(self.beta), f.sq(t)), lift6(self.gamma)),
                )
            {
                return Err("quotient equation".into());
            }
            let xn = f.add(
                f.mul(k(2), f.mul(s, v)),
                f.add(
                    f.mul(k(2), f.mul(lift6(self.alpha), f.sq(t))),
                    lift6(self.beta),
                ),
            );
            let yn = f.mul(k(2), f.mul(s, f.mul(xn, t)));
            Pt::Aff(
                f.add(f.div(xn, lift6(self.factor)), lift6(self.root)),
                f.div(yn, f.pow(lift6(self.sqrt_d), 3)),
            )
        };
        if !curve::on_curve(f, &self.elliptic6, &out) {
            return Err("raw quotient source model identity".into());
        }
        Ok(out)
    }
    pub fn raw_cover(&self, w: [ER; 3]) -> Result<Pt<ER>> {
        self.raw_cover_with_sign(w, false)
    }
    pub fn quartic_point_with_sign(&self, p: &Point, negative: bool) -> Result<QuarticPoint> {
        self.admit(p)?;
        let f = &self.f6;
        let s = if negative {
            f.neg(self.sqrt_alpha)
        } else {
            self.sqrt_alpha
        };
        let u0 = if negative {
            self.raw_cover_with_sign(self.pic.base_point().map(|x| k(x as u64)), true)?
        } else {
            self.raw_p0
        };
        let q = match p {
            None => Pt::Inf,
            Some((x, y)) => Pt::Aff(lift6(er(*x)), lift6(er(*y))),
        };
        let r = curve::padd(f, &self.elliptic6, &q, &u0);
        match r {
            Pt::Inf => Ok(QuarticPoint::Infinity(project6(s)?)),
            Pt::Aff(x, y) => {
                let xn = f.mul(lift6(self.factor), f.sub(x, lift6(self.root)));
                let yn = f.mul(f.pow(lift6(self.sqrt_d), 3), y);
                if f.is_zero(xn) {
                    if !f.is_zero(yn) {
                        return Err("bad xNzero branch".into());
                    }
                    return Ok(QuarticPoint::Infinity(project6(f.neg(s))?));
                }
                let t = f.div(yn, f.mul(k(2), f.mul(s, xn)));
                let v = f.div(
                    f.sub(
                        f.sub(xn, f.mul(k(2), f.mul(lift6(self.alpha), f.sq(t)))),
                        lift6(self.beta),
                    ),
                    f.mul(k(2), s),
                );
                if f.sq(v)
                    != f.add(
                        f.mul(lift6(self.alpha), f.pow(t, 4)),
                        f.add(f.mul(lift6(self.beta), f.sq(t)), lift6(self.gamma)),
                    )
                {
                    return Err("inverse even quartic equation".into());
                }
                Ok(QuarticPoint::Finite(project6(t)?, project6(v)?))
            }
        }
    }
    pub fn quartic_point(&self, p: &Point) -> Result<QuarticPoint> {
        self.quartic_point_with_sign(p, false)
    }
    pub fn source_point(&self, p: QuarticPoint) -> Result<Point> {
        let f = &self.f6;
        let s = self.sqrt_alpha;
        let raw = match p {
            QuarticPoint::Infinity(v) => {
                let v = lift6(er(v));
                if v == s {
                    Pt::Inf
                } else if v == f.neg(s) {
                    Pt::Aff(lift6(self.root), f.zero())
                } else {
                    return Err("foreign infinity coefficient".into());
                }
            }
            QuarticPoint::Finite(t, v) => {
                let t = lift6(er(t));
                let v = lift6(er(v));
                if f.sq(v)
                    != f.add(
                        f.mul(lift6(self.alpha), f.pow(t, 4)),
                        f.add(f.mul(lift6(self.beta), f.sq(t)), lift6(self.gamma)),
                    )
                {
                    return Err("foreign H point".into());
                }
                let xn = f.add(
                    f.mul(k(2), f.mul(s, v)),
                    f.add(
                        f.mul(k(2), f.mul(lift6(self.alpha), f.sq(t))),
                        lift6(self.beta),
                    ),
                );
                let yn = f.mul(k(2), f.mul(s, f.mul(xn, t)));
                Pt::Aff(
                    f.add(f.div(xn, lift6(self.factor)), lift6(self.root)),
                    f.div(yn, f.pow(lift6(self.sqrt_d), 3)),
                )
            }
        };
        let q = curve::padd(f, &self.elliptic6, &raw, &curve::neg(f, &self.raw_p0));
        let out = match q {
            Pt::Inf => None,
            Pt::Aff(x, y) => Some((project6(x)?, project6(y)?)),
        };
        self.admit(&out)?;
        Ok(out)
    }
    pub fn fibre(&self, p: &Point) -> Result<(Poly3, Poly3)> {
        let f = &self.field;
        let [x, y, z] = self.core.omi.map(|r| linear(&r));
        let sq = |v: &Poly3| cover::poly3_mul(f, v, v);
        let sub = |a: &Poly3, b: &Poly3, c: K| {
            cover::poly3_add(f, a, &cover::poly3_scale(f, b, &f.neg(&c)))
        };
        let [a, _b, _c, d, _e, g] = self.ciani.map(three);
        let first = cover::poly3_scale(f, &sq(&x), &f.scale(&a, 2));
        Ok(match self.quartic_point(p)? {
            QuarticPoint::Finite(t, v) => (
                sub(&y, &z, t),
                sub(
                    &first,
                    &sq(&z),
                    f.sub(&f.sub(&v, &f.mul(&d, &f.mul(&t, &t))), &g),
                ),
            ),
            QuarticPoint::Infinity(s) => (z, sub(&first, &sq(&y), f.sub(&s, &d))),
        })
    }
    pub fn trace_space(&self, p: &Point) -> Result<Gen> {
        self.trace_space_gauged(p, None)
    }
    pub fn trace_space_gauged(&self, p: &Point, gauge: Option<K>) -> Result<Gen> {
        let f = &self.field;
        let (mut l, mut q) = self.fibre(p)?;
        if let Some(c) = gauge {
            if f.is_zero(&c) {
                return Err("zero fibre gauge".into());
            }
            l = cover::poly3_scale(f, &l, &c);
            q = cover::poly3_scale(f, &q, &c);
        }
        let mut fibres = vec![];
        for _ in 0..3 {
            fibres.push((l.clone(), q.clone()));
            l = conjugate(f, &l);
            q = conjugate(f, &q);
        }
        let mut rows = vec![];
        let mon6 = pic::mons_of_degree(6);
        for mask in 0..8 {
            let mut product = monomial((0, 0, 0), f.one());
            let mut degree = 0;
            for (i, (l, q)) in fibres.iter().enumerate() {
                let quad = (mask >> i) & 1 == 1;
                degree += if quad { 2 } else { 1 };
                product = cover::poly3_mul(f, &product, if quad { q } else { l });
            }
            for e in pic::mons_of_degree(6 - degree) {
                let homogeneous = cover::poly3_mul(f, &product, &monomial(e, f.one()));
                for basis in [[1, 0, 0], [0, 1, 0], [0, 0, 1]] {
                    let mut row = vec![0u32; self.pic.dim_r(6)];
                    for (i, e) in mon6.iter().enumerate() {
                        if let Some(c) = homogeneous.get(e) {
                            let c = f.mul(c, &basis);
                            let tr = f.add(&f.add(&c, &f.frob(&c)), &f.frob(&f.frob(&c)));
                            if !f.in_fq(&tr) {
                                return Err("trace coefficient not Fp".into());
                            }
                            for (j, &v) in self.normal6[i].iter().enumerate() {
                                row[j] = f.f.add(row[j] as u64, f.f.mul(tr[0], v as u64)) as u32;
                            }
                        }
                    }
                    rows.push(row);
                }
            }
        }
        Ok(Gen { k: 6, rows })
    }
    pub fn transfer_point(&self, p: &Point) -> Result<PicClass> {
        let raw = self.pic.reduce_deg6(&self.trace_space(p)?);
        Ok(self.pic.sub(&raw, &self.origin))
    }
    pub fn transfer(&self, p: &EncodedPoint) -> Result<PicClass> {
        self.transfer_point(&self.decode(p)?)
    }
    pub fn origin_shift(&self) -> &PicClass {
        &self.origin
    }
}
