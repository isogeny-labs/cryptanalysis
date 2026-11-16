//! Complete Fp2 fibre ideals. Prospective5be5e0/32283c precedes code.
//! Literal formula extension of the two immutable adapters, not support images.
use chained_n4_beta_rational_lift::{frob, lift3, lift_curve};
use chained_n4_completed_v2::AdapterV2;
use chained_n4_odd_product_maps::Adapter;
use chained_n4_odd_product_models::er;
use chained_quadratic_picard_engine::{self as pic2, Gen, PicClass, PlaneQuartic};
use ghs_original_engines::pic::PicClass as PrimeClass;
use isogeny_algos::{
    curve::{self, Curve, Pt},
    field::Field,
    fpr::{FpR, ER},
};
use std::collections::BTreeMap;

pub type Result<T> = std::result::Result<T, String>;
type Mono = (u8, u8, u8);
type Poly = BTreeMap<Mono, ER>;
fn k(x: u64) -> ER {
    let mut a = [0; 16];
    a[0] = x % 223;
    a
}
fn liftk(x: [u64; 3]) -> ER {
    lift3(er(x))
}
fn mono(e: Mono, c: ER) -> Poly {
    [(e, c)].into_iter().collect()
}
fn linear(row: [[u64; 3]; 3]) -> Poly {
    [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
        .into_iter()
        .zip(row.map(liftk))
        .filter(|(_, c)| *c != [0; 16])
        .collect()
}
fn padd(f: &FpR, a: &Poly, b: &Poly) -> Poly {
    let mut out = a.clone();
    for (&e, &c) in b {
        let v = f.add(out.get(&e).copied().unwrap_or(f.zero()), c);
        if f.is_zero(v) {
            out.remove(&e);
        } else {
            out.insert(e, v);
        }
    }
    out
}
fn scale(f: &FpR, a: &Poly, c: ER) -> Poly {
    a.iter()
        .filter_map(|(&e, &v)| {
            let v = f.mul(v, c);
            (!f.is_zero(v)).then_some((e, v))
        })
        .collect()
}
fn pmul(f: &FpR, a: &Poly, b: &Poly) -> Poly {
    let mut out = Poly::new();
    for (&(i, j, l), &x) in a {
        for (&(m, n, o), &y) in b {
            let e = (i + m, j + n, l + o);
            let v = f.add(out.get(&e).copied().unwrap_or(f.zero()), f.mul(x, y));
            if f.is_zero(v) {
                out.remove(&e);
            } else {
                out.insert(e, v);
            }
        }
    }
    out
}
fn psub(f: &FpR, a: &Poly, b: &Poly, c: ER) -> Poly {
    padd(f, a, &scale(f, b, f.neg(c)))
}
fn conjugate(f: &FpR, p: &Poly, n: usize) -> Poly {
    p.iter().map(|(&e, &c)| (e, frob(f, c, n))).collect()
}

pub fn embed_class(x: &PrimeClass) -> PicClass {
    match x {
        PrimeClass::Exc(p) => PicClass::Exc(*p),
        PrimeClass::Typ(m) => PicClass::Typ(*m),
    }
}
pub fn descend_class(x: &PicClass) -> Result<PrimeClass> {
    if x.key().0.iter().any(|&a| a >= 223) {
        return Err("class is not fixed by base Frobenius".into());
    }
    Ok(match x {
        PicClass::Exc(p) => PrimeClass::Exc(*p),
        PicClass::Typ(m) => PrimeClass::Typ(*m),
    })
}

enum Formula {
    Old(AdapterV2),
    New(Adapter),
}
pub struct BaseChanged {
    formula: Formula,
    pub f: FpR,
    pub curve: Curve<ER>,
    pub pic: PlaneQuartic,
    pub model: String,
    pub field: String,
    pub origin: PicClass,
    normal6: Vec<Vec<u32>>,
}
impl BaseChanged {
    pub fn old(a: AdapterV2) -> Result<Self> {
        let e = Curve {
            a: er(a.core.ea),
            b: er(a.core.eb),
        };
        let p = PlaneQuartic::base_change_quadratic(
            223,
            3,
            a.core.quartic.map(|x| x as u32),
            a.pic.base_point(),
        )
        .map_err(|e| format!("old quadratic Picard:{e:?}"))?;
        Self::construct(Formula::Old(a), e, p)
    }
    pub fn new(a: Adapter) -> Result<Self> {
        let e = a.source_ec;
        let p = PlaneQuartic::base_change_quadratic(
            223,
            3,
            a.core.quartic.map(|x| x as u32),
            a.pic.base_point(),
        )
        .map_err(|e| format!("new quadratic Picard:{e:?}"))?;
        Self::construct(Formula::New(a), e, p)
    }
    fn construct(formula: Formula, e: Curve<ER>, pic: PlaneQuartic) -> Result<Self> {
        let f = FpR::from_modulus(223, &[220, 0, 0, 0, 0, 0, 1]);
        let mut normal6 = Vec::new();
        for (a, b, c) in pic2::mons_of_degree(6) {
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
        let (model, field) = match &formula {
            Formula::Old(a) => (a.model_tag.clone(), a.field_tag.clone()),
            Formula::New(a) => (a.model_tag.clone(), a.field_tag.clone()),
        };
        let origin = pic.zero();
        let mut out = Self {
            formula,
            f,
            curve: lift_curve(&e),
            pic,
            model,
            field,
            origin,
            normal6,
        };
        out.origin = out.pic.reduce_deg6(&out.trace_space(Pt::Inf, false)?);
        Ok(out)
    }
    pub fn candidate(&self) -> Option<(usize, usize)> {
        match &self.formula {
            Formula::Old(_) => None,
            Formula::New(a) => Some(a.candidate),
        }
    }
    pub fn admit(&self, p: &Pt<ER>) -> Result<()> {
        if let Pt::Aff(x, y) = p {
            if x.iter()
                .chain(y)
                .enumerate()
                .any(|(i, &a)| if i % 16 < 6 { a >= 223 } else { a != 0 })
            {
                return Err("noncanonical L coordinate".into());
            }
        }
        if !curve::on_curve(&self.f, &self.curve, p) {
            return Err("off-curve L point".into());
        }
        Ok(())
    }
    fn oldu(&self, a: &AdapterV2, i: usize, t: ER) -> ER {
        let (mut b, mut c) = (a.ub, a.uc);
        for _ in 0..i {
            b = a.field.frob(&b);
            c = a.field.frob(&c);
        }
        self.f
            .add(self.f.add(self.f.sq(t), self.f.mul(liftk(b), t)), liftk(c))
    }
    fn old_fibre(&self, a: &AdapterV2, p: Pt<ER>) -> Result<(Poly, Poly)> {
        let f = &self.f;
        let [x, y, z] = a.core.omi.map(linear);
        let sq = |v: &Poly| pmul(f, v, v);
        let infinity = |minus: bool| {
            (
                psub(f, &y, &z, if minus { f.neg(f.one()) } else { f.one() }),
                psub(f, &sq(&x), &sq(&z), f.one()),
            )
        };
        let Pt::Aff(xs, yy) = p else {
            return Ok(infinity(false));
        };
        let xx = f.sub(xs, liftk(a.core.wshift));
        let b = f.mul(liftk(a.core.wb), k(112));
        let (t, y0) = if f.is_zero(xx) {
            if yy == f.neg(liftk(a.core.walpha)) {
                return Ok(infinity(true));
            }
            if yy != liftk(a.core.walpha) {
                return Err("invalid xzero L branch".into());
            }
            let c2 = a.field.frob(&a.field.frob(&a.uc));
            let beta = f.sub(f.mul(liftk(a.uc), liftk(c2)), f.sq(liftk(a.core.ws)));
            let t = f.div(f.neg(beta), liftk(a.core.walpha));
            let aa = f.add(f.add(f.sq(t), f.mul(b, t)), liftk(a.core.ws));
            (t, f.neg(aa))
        } else {
            let t = f.div(
                f.sub(f.sub(yy, f.mul(b, xx)), liftk(a.core.walpha)),
                f.mul(k(2), xx),
            );
            let y0 = f.sub(
                f.sub(f.sub(f.mul(xx, k(112)), f.sq(t)), f.mul(b, t)),
                liftk(a.core.ws),
            );
            (t, y0)
        };
        if f.sq(y0) != f.mul(self.oldu(a, 0, t), self.oldu(a, 2, t)) {
            return Err("old L inverse quartic identity".into());
        }
        let u0 = self.oldu(a, 0, t);
        let u1 = self.oldu(a, 1, t);
        if f.is_zero(u0) {
            let u2 = self.oldu(a, 2, t);
            if f.is_zero(u1) || f.is_zero(u2) || !f.is_zero(y0) {
                return Err("invalid L zero-u0 fibre".into());
            }
            Ok((z, psub(f, &sq(&x), &sq(&y), f.div(u1, u2))))
        } else {
            Ok((
                psub(f, &y, &z, f.div(y0, u0)),
                psub(f, &sq(&x), &sq(&z), f.div(u1, u0)),
            ))
        }
    }
    fn new_fibre(&self, a: &Adapter, p: Pt<ER>, negative: bool) -> Result<(Poly, Poly)> {
        let f = &self.f;
        let s = if negative {
            f.neg(a.sqrt_alpha)
        } else {
            a.sqrt_alpha
        };
        let u0 = if negative {
            a.raw_cover_with_sign(a.pic.base_point().map(|x| k(x as u64)), true)?
        } else {
            a.raw_p0
        };
        let q = curve::padd(f, &a.elliptic6, &p, &u0);
        let [x, y, z] = a.core.omi.map(linear);
        let sq = |v: &Poly| pmul(f, v, v);
        let [aa, _, _, d, _, g] = a.ciani.map(lift3);
        let first = scale(f, &sq(&x), f.mul(k(2), aa));
        let infinity = |v: ER| (z.clone(), psub(f, &first, &sq(&y), f.sub(v, d)));
        match q {
            Pt::Inf => Ok(infinity(s)),
            Pt::Aff(xx, yy) => {
                let xn = f.mul(lift3(a.factor), f.sub(xx, lift3(a.root)));
                let yn = f.mul(f.pow(lift3(a.sqrt_d), 3), yy);
                if f.is_zero(xn) {
                    if !f.is_zero(yn) {
                        return Err("bad new L xNzero".into());
                    }
                    return Ok(infinity(f.neg(s)));
                }
                let t = f.div(yn, f.mul(k(2), f.mul(s, xn)));
                let v = f.div(
                    f.sub(
                        f.sub(xn, f.mul(k(2), f.mul(lift3(a.alpha), f.sq(t)))),
                        lift3(a.beta),
                    ),
                    f.mul(k(2), s),
                );
                if f.sq(v)
                    != f.add(
                        f.mul(lift3(a.alpha), f.pow(t, 4)),
                        f.add(f.mul(lift3(a.beta), f.sq(t)), lift3(a.gamma)),
                    )
                {
                    return Err("new L inverse even quartic identity".into());
                }
                Ok((
                    psub(f, &y, &z, t),
                    psub(f, &first, &sq(&z), f.sub(f.sub(v, f.mul(d, f.sq(t))), g)),
                ))
            }
        }
    }
    fn fibre(&self, p: Pt<ER>, negative: bool) -> Result<(Poly, Poly)> {
        self.admit(&p)?;
        match &self.formula {
            Formula::Old(a) => {
                if negative {
                    return Err("old model has no kappa branch parameter".into());
                }
                self.old_fibre(a, p)
            }
            Formula::New(a) => self.new_fibre(a, p, negative),
        }
    }
    pub fn trace_space(&self, p: Pt<ER>, negative: bool) -> Result<Gen> {
        let (mut l, mut q) = self.fibre(p, negative)?;
        let f = &self.f;
        let mut fibres = Vec::new();
        for _ in 0..3 {
            fibres.push((l.clone(), q.clone()));
            l = conjugate(f, &l, 2);
            q = conjugate(f, &q, 2);
        }
        let mut rows = Vec::new();
        let mon6 = pic2::mons_of_degree(6);
        let mut w = [0; 16];
        w[1] = 1;
        let basis = [f.one(), f.pow(w, 2), f.pow(w, 4)];
        for mask in 0..8 {
            let mut product = mono((0, 0, 0), f.one());
            let mut degree = 0;
            for (i, (l, q)) in fibres.iter().enumerate() {
                let quad = (mask >> i) & 1 == 1;
                degree += if quad { 2 } else { 1 };
                product = pmul(f, &product, if quad { q } else { l });
            }
            for e in pic2::mons_of_degree(6 - degree) {
                let homogeneous = pmul(f, &product, &mono(e, f.one()));
                for basis in basis {
                    let mut row = vec![0u32; self.pic.dim_r(6)];
                    for (i, e) in mon6.iter().enumerate() {
                        if let Some(&c) = homogeneous.get(e) {
                            let c = f.mul(c, basis);
                            let tr = f.add(f.add(c, frob(f, c, 2)), frob(f, c, 4));
                            if tr
                                .iter()
                                .enumerate()
                                .any(|(i, &v)| i != 0 && i != 3 && v != 0)
                            {
                                return Err(
                                    "coefficient trace did not descend to actual Fp2".into()
                                );
                            }
                            let tr = (tr[0] + 223 * tr[3]) as u32;
                            for (j, &v) in self.normal6[i].iter().enumerate() {
                                row[j] = self
                                    .pic
                                    .coefficient_add(row[j], self.pic.coefficient_mul(tr, v));
                            }
                        }
                    }
                    rows.push(row);
                }
            }
        }
        Ok(Gen { k: 6, rows })
    }
    pub fn transfer(&self, p: Pt<ER>) -> Result<PicClass> {
        let raw = self.pic.reduce_deg6(&self.trace_space(p, false)?);
        Ok(self.pic.sub(&raw, &self.origin))
    }
    pub fn transfer_negative(&self, p: Pt<ER>) -> Result<PicClass> {
        let origin = self.pic.reduce_deg6(&self.trace_space(Pt::Inf, true)?);
        let raw = self.pic.reduce_deg6(&self.trace_space(p, true)?);
        Ok(self.pic.sub(&raw, &origin))
    }
}

#[cfg(test)]
mod tests;
