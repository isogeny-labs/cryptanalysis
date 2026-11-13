//! Complete fixed-panel GHS/Ciani trace pullback. Protocol394e14 precedes code.
//! Runtime uses ideal products, coefficient traces and the ORIGINAL Picard reducer.
use ghs_original_engines::cover::{self, Core, Fq, Kf, Mono, Poly3, K};
use ghs_original_engines::pic::{self, Gen, PicClass, PlaneQuartic};
use isogeny_algos::fpr::FpR;
use serde::{Deserialize, Serialize};
use serde_json::Value;

pub type Point = Option<(K, K)>;
pub type Result<T> = std::result::Result<T, String>;
pub const MAX_INPUT_BYTES: usize = 65536;
pub const MAX_POINTS: usize = 256;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EncodedPoint {
    pub field: String,
    pub model: String,
    pub coordinates: Point,
}
#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Request {
    pub schema: String,
    pub q: u64,
    pub points: Vec<EncodedPoint>,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum QuarticPoint {
    Finite(K, K),
    InfinityPlus,
    InfinityMinus,
}
#[derive(Clone, Debug)]
pub struct Fibre {
    pub line: Poly3,
    pub conic: Poly3,
    pub point: QuarticPoint,
}
pub struct AdapterV2 {
    pub q: u64,
    pub field: Kf,
    pub core: Core,
    pub pic: PlaneQuartic,
    pub ub: K,
    pub uc: K,
    pub expected_order: u64,
    pub ell: u64,
    pub field_tag: String,
    pub model_tag: String,
    pub modulus: Vec<u64>,
    pub moore_shift: u64,
    pub transport_scale: u64,
    pub historical_record: Value,
    normal6: Vec<Vec<u32>>,
    origin: PicClass,
}

fn sha(bytes: &[u8]) -> String {
    ghs_original_engines::digest::sha256(bytes)
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect()
}
fn kindex(q: u64, mut n: u64) -> Result<K> {
    let mut a = [0; 3];
    for x in &mut a {
        *x = n % q;
        n /= q;
    }
    if n != 0 {
        return Err("field coefficient index exceeds cubic field".into());
    }
    Ok(a)
}
fn monomial(e: Mono, c: K) -> Poly3 {
    [(e, c)].into_iter().collect()
}
fn linear(row: &[K; 3]) -> Poly3 {
    [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
        .into_iter()
        .zip(row.iter().copied())
        .filter(|(_, c)| *c != [0; 3])
        .collect()
}
fn ktrace(f: &Kf, c: K) -> K {
    let c1 = f.frob(&c);
    let c2 = f.frob(&c1);
    f.add(&f.add(&c, &c1), &c2)
}
fn conjugate(f: &Kf, p: &Poly3) -> Poly3 {
    p.iter().map(|(&e, c)| (e, f.frob(c))).collect()
}

/// Restore the original builder's primitive-element Moore basis, while keeping
/// the frozen polynomial basis for every K coefficient. Addendum6a3cfe.
fn historical_transport(f: &Kf, core: &mut Core, old: &[u64; 15]) -> Result<(u64, u64)> {
    let q = f.q();
    let order = q.pow(3) - 1;
    let factors = isogeny_algos::field::factor_u64(order);
    let shift = (0..q)
        .find(|&s| {
            let gamma = [s, 1, 0];
            f.pow(gamma, order as u128) == f.one()
                && factors
                    .iter()
                    .all(|&(p, _)| f.pow(gamma, (order / p) as u128) != f.one())
        })
        .ok_or("historical primitive Moore basis not found")?;
    let s2 = f.f.mul(shift, shift);
    let two_s = f.f.mul(2, shift);
    let basis = [
        linear(&[f.one(), f.zero(), f.zero()]),
        linear(&[f.from_fq(shift), f.one(), f.zero()]),
        linear(&[f.from_fq(s2), f.from_fq(two_s), f.one()]),
    ];
    let mut expanded = Poly3::new();
    for (e, &coefficient) in pic::mons_of_degree(4).into_iter().zip(old) {
        let mut term = monomial((0, 0, 0), f.from_fq(coefficient));
        for (axis, exponent) in [e.0, e.1, e.2].into_iter().enumerate() {
            for _ in 0..exponent {
                term = cover::poly3_mul(f, &term, &basis[axis]);
            }
        }
        expanded = cover::poly3_add(f, &expanded, &term);
    }
    let monomials = pic::mons_of_degree(4);
    let first = core
        .quartic
        .iter()
        .position(|&x| x != 0)
        .ok_or("zero core curve")?;
    let lead = expanded.get(&monomials[first]).copied().unwrap_or(f.zero());
    if !f.in_fq(&lead) || f.is_zero(&lead) {
        return Err("transport leading term did not descend".into());
    }
    let scale = f.f.mul(lead[0], f.f.inv(core.quartic[first]));
    for (i, e) in monomials.iter().enumerate() {
        if expanded.get(e).copied().unwrap_or(f.zero())
            != f.from_fq(f.f.mul(scale, core.quartic[i]))
        {
            return Err("full historical quartic transport identity failed".into());
        }
    }
    // XYZ = omi_g B_s^-1 W_gamma; all source elliptic constants stay fixed.
    for row in &mut core.omi {
        let [a, b, c] = *row;
        *row = [
            f.add(&f.sub(&a, &f.scale(&b, shift)), &f.scale(&c, s2)),
            f.sub(&b, &f.scale(&c, two_s)),
            c,
        ];
    }
    let first_old = old
        .iter()
        .position(|&x| x != 0)
        .ok_or("zero historical curve")?;
    let inverse = f.f.inv(old[first_old]);
    core.quartic = old.map(|x| f.f.mul(x, inverse));
    Ok((shift, scale))
}

impl AdapterV2 {
    /// Fresh q223 field/plane/P0/normal forms/origin. No V1 state is reused.
    pub fn new(checked: &chained_n4_public_target::CheckedInstance) -> Result<Self> {
        Self::with_base_point(checked, None)
    }

    pub fn with_base_point(
        checked: &chained_n4_public_target::CheckedInstance,
        base_point: Option<[u32; 3]>,
    ) -> Result<Self> {
        checked.check_field_basis()?;
        let inst = &checked.inst;
        let q = inst.q;
        if q != 223 { return Err("unsupported V2 constructor".into()); }
        let modulus = vec![q-inst.kf.c, 0, 0, 1];
        let _checked = FpR::from_modulus(q, &modulus);
        let mut field = Kf { f: Fq::new(q), a: 0, b: q-inst.kf.c, gq: [0;3], gq2: [0;3] };
        field.gq = field.pow([0,1,0], q as u128);
        field.gq2 = field.mul(&field.gq, &field.gq);
        for a in [[1,0,0],[0,1,0],[0,0,1]] {
            if field.frob(&a) != inst.kf.frob(&a) { return Err("actual Frobenius basis mismatch".into()); }
            for b in [[1,0,0],[0,1,0],[0,0,1]] {
                if field.mul(&a,&b) != inst.kf.mul(&a,&b) { return Err("actual product basis mismatch".into()); }
            }
        }
        let (ub, uc) = (inst.u[1], inst.u[0]);
        let core = cover::build_core(&field, &ub, &uc).map_err(|e|format!("original core rejects:{e:?}"))?;
        if core.quartic.map(|v|v as u32) != inst.f { return Err("actual all15 quartic mismatch".into()); }
        if core.ea != checked.independent_curve.a[..3] || core.eb != checked.independent_curve.b[..3] {
            return Err("actual independent short-model mismatch".into());
        }
        let coeffs = core.quartic.map(|x|x as u32);
        let p0 = match base_point {
            Some(p) => p,
            None => pic::first_rational_point_canonical(q as u32, &coeffs).ok_or("no actual canonical base point")?,
        };
        let pic = PlaneQuartic::new(q as u32, coeffs, p0).map_err(|e|format!("original Picard rejects:{e:?}"))?;
        let mut normal6 = Vec::new();
        for (a,b,c) in pic::mons_of_degree(6) {
            let mut v = vec![1u32];
            let mut degree = 0;
            for (axis,n) in [a,b,c].into_iter().enumerate() {
                for _ in 0..n {
                    let mut x = vec![0;3]; x[axis] = 1;
                    v = pic.mul_forms(degree,&v,1,&x); degree += 1;
                }
            }
            normal6.push(v);
        }
        let field_tag = checked.field_tag.clone();
        let model_tag = format!("Ciani-E0-completed-v2-{}",sha(format!("{q}:{ub:?}:{uc:?}:{:?}:{:?}:{:?}:{p0:?}",core.ea,core.eb,core.quartic).as_bytes()));
        let origin = pic.zero();
        let mut adapter = Self { q,field,core,pic,ub,uc,expected_order:inst.order as u64,ell:inst.ell,
            field_tag,model_tag,modulus,moore_shift:0,transport_scale:1,historical_record:checked.description(),normal6,origin };
        adapter.origin = adapter.pic.reduce_deg6(&adapter.trace_space(&None)?);
        Ok(adapter)
    }
    pub fn encode(&self, p: Point) -> EncodedPoint {
        EncodedPoint {
            field: self.field_tag.clone(),
            model: self.model_tag.clone(),
            coordinates: p,
        }
    }
    pub fn admit(&self, p: &Point) -> Result<()> {
        let Some((x, y)) = p else { return Ok(()) };
        if x.iter().chain(y).any(|&c| c >= self.q) {
            return Err("noncanonical coordinate".into());
        }
        let f = &self.field;
        let rhs = f.add(
            &f.add(&f.mul(x, &f.mul(x, x)), &f.mul(&self.core.ea, x)),
            &self.core.eb,
        );
        if f.mul(y, y) != rhs {
            return Err("off-curve point".into());
        }
        Ok(())
    }
    pub fn decode(&self, p: &EncodedPoint) -> Result<Point> {
        if p.field != self.field_tag || p.model != self.model_tag {
            return Err("foreign field or cover model".into());
        }
        self.admit(&p.coordinates)?;
        Ok(p.coordinates)
    }
    fn u(&self, i: usize, t: &K) -> K {
        let f = &self.field;
        let mut b = self.ub;
        let mut c = self.uc;
        for _ in 0..i {
            b = f.frob(&b);
            c = f.frob(&c);
        }
        f.add(&f.add(&f.mul(t, t), &f.mul(&b, t)), &c)
    }
    pub fn quartic_point(&self, p: &Point) -> Result<QuarticPoint> {
        self.admit(p)?;
        let Some((xs, yy)) = p else {
            return Ok(QuarticPoint::InfinityPlus);
        };
        let f = &self.field;
        let x = f.sub(xs, &self.core.wshift);
        let half = f.f.inv(2);
        let b = f.scale(&self.core.wb, half);
        if f.is_zero(&x) {
            if *yy == f.neg(&self.core.walpha) {
                return Ok(QuarticPoint::InfinityMinus);
            }
            if *yy != self.core.walpha {
                return Err("invalid x=0 branch".into());
            }
            let c2 = f.frob(&f.frob(&self.uc));
            let beta = f.sub(&f.mul(&self.uc, &c2), &f.mul(&self.core.ws, &self.core.ws));
            let t = f.mul(&f.neg(&beta), &f.inv(&self.core.walpha));
            let a = f.add(&f.add(&f.mul(&t, &t), &f.mul(&b, &t)), &self.core.ws);
            return Ok(QuarticPoint::Finite(t, f.neg(&a)));
        }
        let t = f.mul(
            &f.sub(&f.sub(yy, &f.mul(&b, &x)), &self.core.walpha),
            &f.inv(&f.scale(&x, 2)),
        );
        let y = f.sub(
            &f.sub(&f.sub(&f.scale(&x, half), &f.mul(&t, &t)), &f.mul(&b, &t)),
            &self.core.ws,
        );
        if f.mul(&y, &y) != f.mul(&self.u(0, &t), &self.u(2, &t)) {
            return Err("quartic inverse identity failed".into());
        }
        Ok(QuarticPoint::Finite(t, y))
    }
    pub fn short_point(&self, p: QuarticPoint) -> Result<Point> {
        let f = &self.field;
        let out = match p {
            QuarticPoint::InfinityPlus => None,
            QuarticPoint::InfinityMinus => Some((self.core.wshift, f.neg(&self.core.walpha))),
            QuarticPoint::Finite(t, y) => {
                if t.iter().chain(y.iter()).any(|&c| c >= self.q)
                    || f.mul(&y, &y) != f.mul(&self.u(0, &t), &self.u(2, &t))
                {
                    return Err("invalid quartic point".into());
                }
                let b = f.scale(&self.core.wb, f.f.inv(2));
                let a = f.add(&f.add(&f.mul(&t, &t), &f.mul(&b, &t)), &self.core.ws);
                let x = f.scale(&f.add(&y, &a), 2);
                let yy = f.add(
                    &f.add(&f.mul(&f.scale(&x, 2), &t), &f.mul(&b, &x)),
                    &self.core.walpha,
                );
                Some((f.add(&x, &self.core.wshift), yy))
            }
        };
        self.admit(&out)?;
        Ok(out)
    }
    pub fn fibre(&self, p: &Point) -> Result<Fibre> {
        let point = self.quartic_point(p)?;
        let f = &self.field;
        let [x, y, z] = self.core.omi.map(|r| linear(&r));
        let sq = |v: &Poly3| cover::poly3_mul(f, v, v);
        let sub = |a: &Poly3, b: &Poly3, c: K| {
            cover::poly3_add(f, a, &cover::poly3_scale(f, b, &f.neg(&c)))
        };
        let (line, conic) = match point {
            QuarticPoint::InfinityPlus => (sub(&y, &z, f.one()), sub(&sq(&x), &sq(&z), f.one())),
            QuarticPoint::InfinityMinus => {
                (sub(&y, &z, f.neg(&f.one())), sub(&sq(&x), &sq(&z), f.one()))
            }
            QuarticPoint::Finite(t, y0) => {
                let u0 = self.u(0, &t);
                let u1 = self.u(1, &t);
                if f.is_zero(&u0) {
                    let u2 = self.u(2, &t);
                    if f.is_zero(&u1) || f.is_zero(&u2) || !f.is_zero(&y0) {
                        return Err("invalid zero-u0 fibre".into());
                    }
                    (z.clone(), sub(&sq(&x), &sq(&y), f.mul(&u1, &f.inv(&u2))))
                } else {
                    let inv = f.inv(&u0);
                    (
                        sub(&y, &z, f.mul(&y0, &inv)),
                        sub(&sq(&x), &sq(&z), f.mul(&u1, &inv)),
                    )
                }
            }
        };
        Ok(Fibre { line, conic, point })
    }
    pub fn trace_space(&self, p: &Point) -> Result<Gen> {
        self.trace_space_gauged(p, None)
    }
    /// Nonzero rescaling is a positive scheme-invariance control.
    pub fn trace_space_gauged(&self, p: &Point, gauge: Option<K>) -> Result<Gen> {
        let fibre = self.fibre(p)?;
        let f = &self.field;
        let mut l = fibre.line;
        let mut q = fibre.conic;
        if let Some(c) = gauge {
            if f.is_zero(&c) {
                return Err("zero fibre gauge".into());
            }
            l = cover::poly3_scale(f, &l, &c);
            q = cover::poly3_scale(f, &q, &c);
        }
        let mut fibres = Vec::new();
        for _ in 0..3 {
            fibres.push((l.clone(), q.clone()));
            l = conjugate(f, &l);
            q = conjugate(f, &q);
        }
        let mut rows = Vec::new();
        let mon6 = pic::mons_of_degree(6);
        for mask in 0..8 {
            let mut product = monomial((0, 0, 0), f.one());
            let mut degree = 0;
            for (i, (line, quad)) in fibres.iter().enumerate() {
                let quad_used = (mask >> i) & 1 == 1;
                degree += if quad_used { 2 } else { 1 };
                product = cover::poly3_mul(f, &product, if quad_used { quad } else { line });
            }
            for e in pic::mons_of_degree(6 - degree) {
                let homogeneous = cover::poly3_mul(f, &product, &monomial(e, f.one()));
                for basis in [[1, 0, 0], [0, 1, 0], [0, 0, 1]] {
                    let mut row = vec![0u32; self.pic.dim_r(6)];
                    for (i, e) in mon6.iter().enumerate() {
                        if let Some(c) = homogeneous.get(e) {
                            let tr = ktrace(f, f.mul(c, &basis));
                            if !f.in_fq(&tr) {
                                return Err("trace did not descend".into());
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
        let space = self.trace_space(p)?;
        let out = self.pic.reduce_deg6(&space);
        Ok(self.pic.sub(&out, &self.origin))
    }
    pub fn transfer(&self, p: &EncodedPoint) -> Result<PicClass> {
        self.transfer_point(&self.decode(p)?)
    }
    pub fn origin_shift(&self) -> &PicClass {
        &self.origin
    }
}

pub fn parse_request(bytes: &[u8]) -> Result<Request> {
    if bytes.len() > MAX_INPUT_BYTES {
        return Err("oversized input".into());
    }
    let r: Request = serde_json::from_slice(bytes).map_err(|e| e.to_string())?;
    if r.schema != "ghs-prime-descent/v2" || r.points.is_empty() || r.points.len() > MAX_POINTS {
        return Err("unsupported schema or point bound".into());
    }
    Ok(r)
}
