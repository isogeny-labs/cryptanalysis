// Relation-collection index calculus on the GHS plane quartic (lead N4).
// No subgroup enumeration: every discrete log comes from a kernel vector of a relation
// matrix mod ell and a descent of the target classes through the canonical Pic^0 arithmetic.
#![allow(dead_code)]
use crate::common::*;
use crate::ghs::*;
use crate::pic;
use std::collections::HashMap;

// ---------------------------------------------------------------- polynomials over F_q
type Poly = Vec<u64>;
fn ptrim(a: &mut Poly) {
    while let Some(&0) = a.last() {
        a.pop();
    }
}
fn pmonic(f: &Fp, a: &mut Poly) {
    ptrim(a);
    if let Some(&l) = a.last() {
        if l != 1 {
            let il = f.inv(l);
            for c in a.iter_mut() {
                *c = f.mul(*c, il);
            }
        }
    }
}
/// remainder of a mod m (m monic)
fn prem(f: &Fp, a: &Poly, m: &Poly) -> Poly {
    let mut r = a.clone();
    ptrim(&mut r);
    let dm = m.len() - 1;
    while r.len() > dm {
        let lead = *r.last().unwrap();
        let sh = r.len() - 1 - dm;
        if lead != 0 {
            for i in 0..m.len() {
                let t = f.mul(lead, m[i]);
                r[sh + i] = f.sub(r[sh + i], t);
            }
        }
        r.pop();
        ptrim(&mut r);
    }
    r
}
fn pmul(f: &Fp, a: &Poly, b: &Poly) -> Poly {
    if a.is_empty() || b.is_empty() {
        return vec![];
    }
    let mut r = vec![0u64; a.len() + b.len() - 1];
    for i in 0..a.len() {
        for j in 0..b.len() {
            let t = f.mul(a[i], b[j]);
            r[i + j] = f.add(r[i + j], t);
        }
    }
    r
}
fn pgcd(f: &Fp, a: &Poly, b: &Poly) -> Poly {
    let (mut a, mut b) = (a.clone(), b.clone());
    ptrim(&mut a);
    ptrim(&mut b);
    while !b.is_empty() {
        let mut bm = b.clone();
        pmonic(f, &mut bm);
        let r = prem(f, &a, &bm);
        a = bm;
        b = r;
    }
    pmonic(f, &mut a);
    a
}
fn pdiv_exact(f: &Fp, a: &Poly, d: &Poly) -> Poly {
    // a / d (d monic, exact)
    let mut r = a.clone();
    let dd = d.len() - 1;
    let mut qt = vec![0u64; r.len() - dd];
    for i in (0..qt.len()).rev() {
        let lead = r[i + dd];
        qt[i] = lead;
        if lead != 0 {
            for j in 0..d.len() {
                let t = f.mul(lead, d[j]);
                r[i + j] = f.sub(r[i + j], t);
            }
        }
    }
    qt
}
fn ppowx(f: &Fp, base: &Poly, mut e: u64, m: &Poly) -> Poly {
    let mut r: Poly = vec![1];
    let mut b = prem(f, base, m);
    while e > 0 {
        if e & 1 == 1 {
            r = prem(f, &pmul(f, &r, &b), m);
        }
        e >>= 1;
        if e > 0 {
            b = prem(f, &pmul(f, &b, &b), m);
        }
    }
    r
}
/// all roots in F_q of g (degree <= 4), distinct
pub fn roots(f: &Fp, g: &Poly, rng: &mut Rng) -> Vec<u64> {
    let mut g = g.clone();
    ptrim(&mut g);
    if g.len() <= 1 {
        return vec![];
    }
    pmonic(f, &mut g);
    if g.len() == 2 {
        return vec![f.neg(g[0])];
    }
    // h = x^q mod g ; d = gcd(g, h - x)
    let h = ppowx(f, &vec![0, 1], f.q, &g);
    let mut hx = h.clone();
    if hx.len() < 2 {
        hx.resize(2, 0);
    }
    hx[1] = f.sub(hx[1], 1);
    ptrim(&mut hx);
    let d = pgcd(f, &g, &hx);
    split(f, &d, rng)
}
fn split(f: &Fp, d: &Poly, rng: &mut Rng) -> Vec<u64> {
    let deg = d.len() - 1;
    if deg == 0 {
        return vec![];
    }
    if deg == 1 {
        return vec![f.neg(d[0])];
    }
    if deg == 2 {
        let (b, c) = (d[1], d[0]);
        let disc = f.sub(f.mul(b, b), f.mul(4, c));
        let s = match f.sqrt(disc) {
            Some(s) => s,
            None => return vec![],
        };
        let i2 = f.inv(2);
        let r1 = f.mul(f.sub(s, b), i2);
        let r2 = f.mul(f.sub(f.neg(s), b), i2);
        return if r1 == r2 { vec![r1] } else { vec![r1, r2] };
    }
    loop {
        let delta = rng.below(f.q);
        let e = ppowx(f, &vec![delta, 1], (f.q - 1) / 2, d);
        let mut e1 = e.clone();
        if e1.is_empty() {
            e1.push(0);
        }
        e1[0] = f.sub(e1[0], 1);
        ptrim(&mut e1);
        let g1 = pgcd(f, d, &e1);
        let dg = g1.len() - 1;
        if dg > 0 && dg < deg {
            let g2 = pdiv_exact(f, d, &g1);
            let mut r = split(f, &g1, rng);
            r.extend(split(f, &g2, rng));
            return r;
        }
    }
}

// ---------------------------------------------------------------- points and lines
pub type P3 = [u64; 3];
pub fn pack(p: &P3) -> u64 {
    (p[0] << 42) | (p[1] << 21) | p[2]
}
pub fn pnorm(f: &Fp, p: &P3) -> P3 {
    let l = *p.iter().find(|x| **x != 0).expect("zero point");
    if l == 1 {
        return *p;
    }
    let il = f.inv(l);
    [f.mul(p[0], il), f.mul(p[1], il), f.mul(p[2], il)]
}

pub struct Curve {
    pub f: Fp,
    pub coef: [u64; 15],
    pub mons: Vec<(u8, u8, u8)>,
}
impl Curve {
    pub fn new(q: u64, f: &[u32; 15]) -> Curve {
        let mut coef = [0u64; 15];
        for i in 0..15 {
            coef[i] = f[i] as u64;
        }
        Curve { f: Fp { q }, coef, mons: pic::mons_of_degree(4) }
    }
    pub fn eval(&self, p: &P3) -> u64 {
        let f = &self.f;
        let mut pw = [[1u64; 5]; 3];
        for i in 0..3 {
            for e in 1..5 {
                pw[i][e] = f.mul(pw[i][e - 1], p[i]);
            }
        }
        let mut s = 0u64;
        for (i, &(a, b, c)) in self.mons.iter().enumerate() {
            if self.coef[i] == 0 {
                continue;
            }
            let t = f.mul(f.mul(pw[0][a as usize], pw[1][b as usize]), pw[2][c as usize]);
            s = f.add(s, f.mul(self.coef[i], t));
        }
        s
    }
    /// g(s) = F(s A + B), coefficients low -> high (degree <= 4)
    pub fn restrict(&self, a: &P3, b: &P3) -> Poly {
        let f = &self.f;
        // L_i(s) = A_i s + B_i ; powers
        let mut lp: Vec<Vec<Poly>> = Vec::new();
        for i in 0..3 {
            let l: Poly = vec![b[i], a[i]];
            let mut pws: Vec<Poly> = vec![vec![1], l.clone()];
            for e in 2..5 {
                let nx = pmul(f, &pws[e - 1], &l);
                pws.push(nx);
            }
            lp.push(pws);
        }
        let mut g = vec![0u64; 5];
        for (i, &(x, y, z)) in self.mons.iter().enumerate() {
            if self.coef[i] == 0 {
                continue;
            }
            let t = pmul(f, &pmul(f, &lp[0][x as usize], &lp[1][y as usize]), &lp[2][z as usize]);
            for (k, c) in t.iter().enumerate() {
                let m = f.mul(self.coef[i], *c);
                g[k] = f.add(g[k], m);
            }
        }
        g
    }
    /// all rational points of C on the line through A, B (distinct)
    pub fn line_points(&self, a: &P3, b: &P3, rng: &mut Rng) -> Vec<P3> {
        let f = &self.f;
        let g = self.restrict(a, b);
        let mut out = Vec::new();
        if g[4] == 0 {
            out.push(pnorm(f, a));
        }
        for s in roots(f, &g, rng) {
            let p = [
                f.add(f.mul(s, a[0]), b[0]),
                f.add(f.mul(s, a[1]), b[1]),
                f.add(f.mul(s, a[2]), b[2]),
            ];
            out.push(pnorm(f, &p));
        }
        out
    }
}

pub fn cross(f: &Fp, a: &P3, b: &P3) -> P3 {
    [
        f.sub(f.mul(a[1], b[2]), f.mul(a[2], b[1])),
        f.sub(f.mul(a[2], b[0]), f.mul(a[0], b[2])),
        f.sub(f.mul(a[0], b[1]), f.mul(a[1], b[0])),
    ]
}

// ---------------------------------------------------------------- relations
#[derive(Clone)]
pub struct Rel {
    pub c: Vec<(u32, u8)>, // (fb index, multiplicity) of the FB points
    pub lp: Option<u32>,   // large prime id
}

pub struct RelOut {
    pub full: Vec<Rel>,
    pub lp: Vec<Rel>,
    pub lp_pts: Vec<P3>,
    pub pairs: u64,
    pub multi_lines: u64,
    pub unsure: u64,
}

pub fn find_relations(cv: &Curve, fb: &[P3], rng: &mut Rng) -> RelOut {
    let f = &cv.f;
    let n = fb.len();
    let idx: HashMap<u64, u32> = fb.iter().enumerate().map(|(i, p)| (pack(p), i as u32)).collect();
    bump_hash(n as u64);
    let mut first: HashMap<u64, (u32, u32)> = HashMap::with_capacity(n * n / 2 + 16);
    let mut multi: HashMap<u64, Vec<u32>> = HashMap::new();
    let mut pairs = 0u64;
    for i in 0..n {
        // lines through fb[i] and fb[j], j>i, normalised by batch inversion of the pivot
        let m = n - i - 1;
        if m == 0 {
            break;
        }
        let mut ls: Vec<P3> = Vec::with_capacity(m);
        let mut piv: Vec<u64> = Vec::with_capacity(m);
        for j in i + 1..n {
            let l = cross(f, &fb[i], &fb[j]);
            let pv = *l.iter().find(|x| **x != 0).unwrap_or(&1);
            piv.push(pv);
            ls.push(l);
        }
        // Montgomery batch inversion
        let mut pref = Vec::with_capacity(m);
        let mut acc = 1u64;
        for &p in &piv {
            pref.push(acc);
            acc = f.mul(acc, p);
        }
        let mut inv_acc = f.inv(acc);
        let mut invs = vec![0u64; m];
        for k in (0..m).rev() {
            invs[k] = f.mul(inv_acc, pref[k]);
            inv_acc = f.mul(inv_acc, piv[k]);
        }
        for (k, l) in ls.iter().enumerate() {
            let key = pack(&[f.mul(l[0], invs[k]), f.mul(l[1], invs[k]), f.mul(l[2], invs[k])]);
            let j = (i + 1 + k) as u32;
            pairs += 1;
            bump_hash(1);
            match first.get(&key) {
                None => {
                    first.insert(key, (i as u32, j));
                }
                Some(&(a, b)) => {
                    let e = multi.entry(key).or_insert_with(|| vec![a, b]);
                    e.push(i as u32);
                    e.push(j);
                }
            }
        }
    }
    drop(first);
    let n_multi = multi.len() as u64;
    let mut out = RelOut {
        full: vec![],
        lp: vec![],
        lp_pts: vec![],
        pairs,
        multi_lines: n_multi,
        unsure: 0,
    };
    let mut lp_ids: HashMap<u64, u32> = HashMap::new();
    let mut multi_v: Vec<(u64, Vec<u32>)> = multi.into_iter().collect();
    multi_v.sort_by_key(|x| x.0);
    for (_key, mut pts) in multi_v {
        pts.sort_unstable();
        pts.dedup();
        if pts.len() >= 4 {
            if pts.len() > 4 {
                out.unsure += 1;
                continue;
            }
            out.full.push(Rel { c: pts.iter().map(|&i| (i, 1u8)).collect(), lp: None });
            continue;
        }
        // three distinct FB points A, B, C on the line: the fourth intersection
        let (ia, ib, ic) = (pts[0], pts[1], pts[2]);
        let (a, b, c) = (fb[ia as usize], fb[ib as usize], fb[ic as usize]);
        let g = cv.restrict(&a, &b);
        // g(s)=F(sA+B): roots: s=inf (A), s=0 (B), and the quadratic g3 s^2+g2 s+g1 (C, P4)
        if g[0] != 0 || g[4] != 0 {
            out.unsure += 1;
            continue;
        }
        // parameter of C = s A + t B: use a nonzero minor of A x B
        let ab = cross(f, &a, &b);
        let k = (0..3).find(|&k| ab[k] != 0).unwrap();
        let cb = cross(f, &c, &b);
        let ac = cross(f, &a, &c);
        let ik = f.inv(ab[k]);
        let sc = f.mul(cb[k], ik);
        let tc = f.mul(ac[k], ik);
        if tc == 0 {
            out.unsure += 1;
            continue;
        }
        let rho_c = f.mul(sc, f.inv(tc));
        // fourth point
        let mut mult = [1u8, 1, 1];
        let mut lp_pt: Option<P3> = None;
        if g[3] == 0 {
            mult[0] = 2; // quadratic degenerates: its second root is s = infinity, i.e. A
        } else {
            let sum = f.neg(f.mul(g[2], f.inv(g[3])));
            let rho4 = f.sub(sum, rho_c);
            let p4 = [
                f.add(f.mul(rho4, a[0]), b[0]),
                f.add(f.mul(rho4, a[1]), b[1]),
                f.add(f.mul(rho4, a[2]), b[2]),
            ];
            let p4 = pnorm(f, &p4);
            if p4 == a {
                mult[0] = 2;
            } else if p4 == b {
                mult[1] = 2;
            } else if p4 == c {
                mult[2] = 2;
            } else {
                bump_hash(1);
                if idx.contains_key(&pack(&p4)) {
                    out.unsure += 1;
                    continue;
                }
                lp_pt = Some(p4);
            }
        }
        let cs = vec![(ia, mult[0]), (ib, mult[1]), (ic, mult[2])];
        match lp_pt {
            None => {
                // 4 FB points with multiplicity
                let tot: u8 = cs.iter().map(|x| x.1).sum();
                if tot == 4 {
                    out.full.push(Rel { c: cs, lp: None });
                } else {
                    out.unsure += 1;
                }
            }
            Some(p4) => {
                let id = *lp_ids.entry(pack(&p4)).or_insert_with(|| {
                    out.lp_pts.push(p4);
                    (out.lp_pts.len() - 1) as u32
                });
                out.lp.push(Rel { c: cs, lp: Some(id) });
            }
        }
    }
    out
}

// ---------------------------------------------------------------- mod-ell linear algebra
#[inline(always)]
pub fn lm(a: u64, b: u64, ell: u64) -> u64 {
    bump_lmul(1);
    ((a as u128 * b as u128) % ell as u128) as u64
}
#[inline(always)]
pub fn la(a: u64, b: u64, ell: u64) -> u64 {
    bump_ladd(1);
    let s = a + b;
    if s >= ell {
        s - ell
    } else {
        s
    }
}
#[inline(always)]
pub fn ls(a: u64, b: u64, ell: u64) -> u64 {
    bump_ladd(1);
    if a >= b {
        a - b
    } else {
        a + ell - b
    }
}

pub type Row = Vec<(u32, u64)>;

fn matvec(rows: &[Row], d: &[u64], v: &[u64], ell: u64, out: &mut Vec<u64>, tmp: &mut Vec<u64>) {
    // out = A^T D A v
    for (i, r) in rows.iter().enumerate() {
        let mut s = 0u64;
        for &(c, a) in r {
            s = la(s, lm(a, v[c as usize], ell), ell);
        }
        tmp[i] = lm(s, d[i], ell);
    }
    for o in out.iter_mut() {
        *o = 0;
    }
    for (i, r) in rows.iter().enumerate() {
        let t = tmp[i];
        if t == 0 {
            continue;
        }
        for &(c, a) in r {
            out[c as usize] = la(out[c as usize], lm(a, t, ell), ell);
        }
    }
}
fn dot(a: &[u64], b: &[u64], ell: u64) -> u64 {
    let mut s = 0u64;
    for i in 0..a.len() {
        s = la(s, lm(a[i], b[i], ell), ell);
    }
    s
}

/// One kernel vector of A (rows over n columns) via Lanczos on A^T D A. None on breakdown.
pub fn lanczos_kernel(rows: &[Row], n: usize, ell: u64, rng: &mut Rng) -> Option<Vec<u64>> {
    let d: Vec<u64> = (0..rows.len()).map(|_| 1 + rng.below(ell - 1)).collect();
    let b: Vec<u64> = (0..n).map(|_| rng.below(ell)).collect();
    let mut tmp = vec![0u64; rows.len()];
    let mut y = vec![0u64; n];
    matvec(rows, &d, &b, ell, &mut y, &mut tmp);
    // solve M x = y
    let mut x = vec![0u64; n];
    let mut w = y.clone();
    let mut w_prev: Vec<u64> = vec![0; n];
    let mut v = vec![0u64; n];
    let mut v_prev: Vec<u64> = vec![0; n];
    let mut s_prev = 0u64;
    let mut first = true;
    let mut iters = 0;
    loop {
        if w.iter().all(|&e| e == 0) {
            break;
        }
        matvec(rows, &d, &w, ell, &mut v, &mut tmp);
        let s = dot(&w, &v, ell);
        if s == 0 {
            return None;
        }
        let si = inv_mod_u64(s, ell);
        let cy = lm(dot(&w, &y, ell), si, ell);
        for i in 0..n {
            x[i] = la(x[i], lm(cy, w[i], ell), ell);
        }
        let a1 = lm(dot(&v, &v, ell), si, ell);
        let mut wn = vec![0u64; n];
        if first {
            for i in 0..n {
                wn[i] = ls(v[i], lm(a1, w[i], ell), ell);
            }
        } else {
            let b1 = lm(dot(&v, &v_prev, ell), inv_mod_u64(s_prev, ell), ell);
            for i in 0..n {
                let t = ls(v[i], lm(a1, w[i], ell), ell);
                wn[i] = ls(t, lm(b1, w_prev[i], ell), ell);
            }
        }
        first = false;
        w_prev = w;
        w = wn;
        v_prev = v.clone();
        s_prev = s;
        iters += 1;
        if iters > n + 5 {
            return None;
        }
    }
    let z: Vec<u64> = (0..n).map(|i| ls(x[i], b[i], ell)).collect();
    if z.iter().all(|&e| e == 0) {
        return None;
    }
    Some(z)
}

pub fn row_apply(r: &Row, z: &[u64], ell: u64) -> u64 {
    let mut s = 0u64;
    for &(c, a) in r {
        s = la(s, lm(a, z[c as usize], ell), ell);
    }
    s
}

// ---------------------------------------------------------------- splitting a degree-3 divisor
/// Base points of the net of conics (3 x 6 rows over mons_of_degree(2)) as three distinct
/// rational points, or None if the divisor does not split into three distinct rational points.
pub fn split3(f: &Fp, conics: &[[u32; 6]; 3], mons2: &[(u8, u8, u8)], rng: &mut Rng) -> Option<[P3; 3]> {
    // coordinates along the line through R0=(0,0,1) and T(s)=(1,s,0): point (v, s v, u)
    // conic = alpha u^2 + (b0 + s b1) u v + (g0 + s g1 + s^2 g2) v^2
    let mut al = [0u64; 3];
    let mut b0 = [0u64; 3];
    let mut b1 = [0u64; 3];
    let mut g0 = [0u64; 3];
    let mut g1 = [0u64; 3];
    let mut g2 = [0u64; 3];
    for i in 0..3 {
        for (m, &(a, b, c)) in mons2.iter().enumerate() {
            let co = conics[i][m] as u64;
            match (a, b, c) {
                (0, 0, 2) => al[i] = co,
                (1, 0, 1) => b0[i] = co,
                (0, 1, 1) => b1[i] = co,
                (2, 0, 0) => g0[i] = co,
                (1, 1, 0) => g1[i] = co,
                (0, 2, 0) => g2[i] = co,
                _ => unreachable!(),
            }
        }
    }
    let row_at = |i: usize, s: u64| -> [u64; 3] {
        [al[i], f.add(b0[i], f.mul(s, b1[i])), f.add(f.add(g0[i], f.mul(s, g1[i])), f.mul(f.mul(s, s), g2[i]))]
    };
    let det_at = |s: u64| -> u64 {
        let r = [row_at(0, s), row_at(1, s), row_at(2, s)];
        let t0 = f.sub(f.mul(r[1][1], r[2][2]), f.mul(r[1][2], r[2][1]));
        let t1 = f.sub(f.mul(r[1][0], r[2][2]), f.mul(r[1][2], r[2][0]));
        let t2 = f.sub(f.mul(r[1][0], r[2][1]), f.mul(r[1][1], r[2][0]));
        f.add(f.sub(f.mul(r[0][0], t0), f.mul(r[0][1], t1)), f.mul(r[0][2], t2))
    };
    let d = [det_at(0), det_at(1), det_at(2), det_at(3)];
    // Lagrange on nodes 0..3 -> coefficients c0..c3
    let i2 = f.inv(2);
    let i6 = f.inv(6);
    let c3 = {
        // d0*(-1/6) + d1*(1/2) + d2*(-1/2) + d3*(1/6)
        let a = f.mul(f.sub(d[3], d[0]), i6);
        let b = f.mul(f.sub(d[1], d[2]), i2);
        f.add(a, b)
    };
    let c2 = {
        // l0: -(x^3 -6x^2+11x-6)/6 -> x^2: +1 ; l1: x(x^2-5x+6)/2 -> -5/2 ; l2: -x(x^2-4x+3)/2 -> +4/2 ; l3: x(x^2-3x+2)/6 -> -3/6
        let t0 = d[0];
        let t1 = f.mul(d[1], f.neg(f.mul(5, i2)));
        let t2 = f.mul(d[2], f.mul(4, i2));
        let t3 = f.mul(d[3], f.neg(f.mul(3, i6)));
        f.add(f.add(t0, t1), f.add(t2, t3))
    };
    let c1 = {
        // l0: -11/6 ; l1: 6/2=3 ; l2: -3/2 ; l3: 2/6
        let t0 = f.mul(d[0], f.neg(f.mul(11, i6)));
        let t1 = f.mul(d[1], 3);
        let t2 = f.mul(d[2], f.neg(f.mul(3, i2)));
        let t3 = f.mul(d[3], f.mul(2, i6));
        f.add(f.add(t0, t1), f.add(t2, t3))
    };
    let c0 = d[0];
    if c3 == 0 {
        return None;
    }
    let rs = roots(f, &vec![c0, c1, c2, c3], rng);
    if rs.len() != 3 {
        return None;
    }
    let mut pts = [[0u64; 3]; 3];
    for (k, &s) in rs.iter().enumerate() {
        let r = [row_at(0, s), row_at(1, s), row_at(2, s)];
        // common root: nullvector (u^2, uv, v^2) = cross of two independent rows
        let mut nv = None;
        for (i, j) in [(0, 1), (0, 2), (1, 2)] {
            let c = cross(f, &r[i], &r[j]);
            if c != [0, 0, 0] {
                nv = Some(c);
                break;
            }
        }
        let c = nv?;
        // (u:v) from (u^2 : uv : v^2)
        let (u, v) = if c[0] != 0 {
            (c[0], c[1])
        } else if c[2] != 0 {
            (c[1], c[2])
        } else {
            return None;
        };
        let p = [v, f.mul(s, v), u];
        if p == [0, 0, 0] {
            return None;
        }
        pts[k] = pnorm(f, &p);
    }
    if pts[0] == pts[1] || pts[0] == pts[2] || pts[1] == pts[2] {
        return None;
    }
    Some(pts)
}


// ---------------------------------------------------------------- structured Gaussian elimination
/// A solved column: `row` is a true relation containing `col`; after the rest of `row` is known,
/// `col = -(sum of the other terms) / coef`.
pub struct Elim {
    pub col: u32,
    pub row: Row,
}
pub struct SgeOut {
    pub core: Vec<Row>,    // rows over core column indices 0..cols.len()
    pub cols: Vec<u32>,    // core index -> original column
    pub elims: Vec<Elim>,  // in elimination order
    pub singles: u64,
    pub merges: u64,
    pub pruned: u64,
    pub skipped_wide: u64,
}

fn coef_of(r: &Row, c: u32) -> u64 {
    match r.binary_search_by_key(&c, |x| x.0) {
        Ok(i) => r[i].1,
        Err(_) => 0,
    }
}
/// a*r1 - b*r2 over mod ell, dropping column `skip` and zeros
fn row_comb(r1: &Row, a: u64, r2: &Row, b: u64, skip: u32, ell: u64) -> Row {
    let mut out: Row = Vec::with_capacity(r1.len() + r2.len());
    let (mut i, mut j) = (0, 0);
    while i < r1.len() || j < r2.len() {
        let c1 = if i < r1.len() { r1[i].0 } else { u32::MAX };
        let c2 = if j < r2.len() { r2[j].0 } else { u32::MAX };
        let (c, v) = if c1 < c2 {
            let v = lm(a, r1[i].1, ell);
            i += 1;
            (c1, v)
        } else if c2 < c1 {
            let v = ls(0, lm(b, r2[j].1, ell), ell);
            j += 1;
            (c2, v)
        } else {
            let v = ls(lm(a, r1[i].1, ell), lm(b, r2[j].1, ell), ell);
            i += 1;
            j += 1;
            (c1, v)
        };
        if c != skip && v != 0 {
            out.push((c, v));
        }
    }
    out
}

/// Eliminate columns of weight 1 (drop their row) and 2 (merge their two rows, if the merged
/// row has at most `maxw` entries); when rows exceed columns by more than a margin, drop the
/// heaviest rows and continue. `protected` is never eliminated.
pub fn sge(rows_in: Vec<Row>, ncols: usize, protected: u32, ell: u64, maxw: usize) -> SgeOut {
    let mut rows: Vec<Option<Row>> = rows_in.into_iter().map(Some).collect();
    let mut col_rows: Vec<Vec<u32>> = vec![vec![]; ncols];
    let mut weight = vec![0u32; ncols];
    for (i, r) in rows.iter().enumerate() {
        for &(c, _) in r.as_ref().unwrap() {
            col_rows[c as usize].push(i as u32);
            weight[c as usize] += 1;
        }
    }
    let mut elims: Vec<Elim> = Vec::new();
    let (mut singles, mut merges, mut pruned, mut skipped) = (0u64, 0u64, 0u64, 0u64);
    let mut eliminated = vec![false; ncols];
    let mut tried_wide = vec![false; ncols];
    let live_rows_of = |rows: &Vec<Option<Row>>, col_rows: &Vec<Vec<u32>>, c: u32| -> Vec<u32> {
        col_rows[c as usize]
            .iter()
            .copied()
            .filter(|&r| rows[r as usize].as_ref().map_or(false, |row| coef_of(row, c) != 0))
            .collect()
    };
    let mut work: Vec<u32> = (0..ncols as u32).filter(|&c| weight[c as usize] >= 1 && weight[c as usize] <= 2 && c != protected).collect();
    loop {
        while let Some(c) = work.pop() {
            bump_hash(1);
            let ci = c as usize;
            if eliminated[ci] || c == protected || weight[ci] == 0 || weight[ci] > 2 {
                continue;
            }
            let lr = live_rows_of(&rows, &col_rows, c);
            if lr.len() == 1 {
                let r = lr[0] as usize;
                let row = rows[r].take().unwrap();
                for &(cc, _) in &row {
                    weight[cc as usize] -= 1;
                    if cc != c && weight[cc as usize] >= 1 && weight[cc as usize] <= 2 {
                        work.push(cc);
                    }
                }
                eliminated[ci] = true;
                elims.push(Elim { col: c, row });
                singles += 1;
            } else if lr.len() == 2 {
                let (r1, r2) = (lr[0] as usize, lr[1] as usize);
                let (a1, a2) = (coef_of(rows[r1].as_ref().unwrap(), c), coef_of(rows[r2].as_ref().unwrap(), c));
                // new = a2*r1 - a1*r2 eliminates c
                let newrow = row_comb(rows[r1].as_ref().unwrap(), a2, rows[r2].as_ref().unwrap(), a1, c, ell);
                if newrow.len() > maxw {
                    if !tried_wide[ci] {
                        tried_wide[ci] = true;
                        skipped += 1;
                    }
                    continue;
                }
                let row1 = rows[r1].take().unwrap();
                let row2 = rows[r2].take().unwrap();
                for &(cc, _) in row1.iter().chain(row2.iter()) {
                    weight[cc as usize] -= 1;
                }
                let id = rows.len() as u32;
                for &(cc, _) in &newrow {
                    weight[cc as usize] += 1;
                    col_rows[cc as usize].push(id);
                }
                for &(cc, _) in &newrow {
                    if cc != protected && weight[cc as usize] >= 1 && weight[cc as usize] <= 2 {
                        work.push(cc);
                    }
                }
                rows.push(Some(newrow));
                eliminated[ci] = true;
                elims.push(Elim { col: c, row: row1 });
                merges += 1;
            }
        }
        // prune the heaviest rows while rows exceed columns by more than a margin
        let alive_rows: Vec<usize> = (0..rows.len()).filter(|&i| rows[i].is_some()).collect();
        let alive_cols = (0..ncols).filter(|&c| weight[c] > 0).count();
        let margin = (alive_cols / 20).max(30);
        if alive_rows.len() <= alive_cols + margin {
            break;
        }
        let excess = alive_rows.len() - alive_cols - margin;
        let k = excess.min((alive_rows.len() / 8).max(1));
        let mut byw: Vec<(usize, usize)> = alive_rows.iter().map(|&i| (rows[i].as_ref().unwrap().len(), i)).collect();
        byw.sort_by(|a, b| b.cmp(a));
        for &(_, i) in byw.iter().take(k) {
            let row = rows[i].take().unwrap();
            for &(cc, _) in &row {
                weight[cc as usize] -= 1;
                if cc != protected && weight[cc as usize] >= 1 && weight[cc as usize] <= 2 {
                    work.push(cc);
                }
            }
            pruned += 1;
        }
        for c in 0..ncols as u32 {
            if weight[c as usize] >= 1 && weight[c as usize] <= 2 && c != protected && !eliminated[c as usize] {
                work.push(c);
            }
        }
        tried_wide.iter_mut().for_each(|x| *x = false);
    }
    let cols: Vec<u32> = (0..ncols as u32).filter(|&c| weight[c as usize] > 0 && !eliminated[c as usize]).collect();
    let mut remap = vec![u32::MAX; ncols];
    for (i, &c) in cols.iter().enumerate() {
        remap[c as usize] = i as u32;
    }
    let core: Vec<Row> = rows
        .into_iter()
        .flatten()
        .map(|r| r.into_iter().map(|(c, a)| (remap[c as usize], a)).collect())
        .collect();
    SgeOut { core, cols, elims, singles, merges, pruned, skipped_wide: skipped }
}

/// Fill the eliminated columns from the core solution (reverse elimination order).
pub fn back_substitute(out: &SgeOut, vals: &mut Vec<Option<u64>>, ell: u64) {
    for e in out.elims.iter().rev() {
        let mut s = 0u64;
        let mut a_c = 0u64;
        let mut ok = true;
        for &(j, a) in &e.row {
            if j == e.col {
                a_c = a;
            } else {
                match vals[j as usize] {
                    Some(v) => s = la(s, lm(a, v, ell), ell),
                    None => {
                        ok = false;
                        break;
                    }
                }
            }
        }
        if ok && a_c != 0 {
            bump_lmul(60);
            vals[e.col as usize] = Some(lm(ls(0, s, ell), inv_mod_u64(a_c, ell), ell));
        }
    }
}

// ---------------------------------------------------------------- double large primes
/// Raw relations of the double-large-prime search. A line through factor-base points A, B meets C
/// in two more rational points X, Y (roots of the residual quadratic):
///  * X, Y both factor-base points: `full` (four-term relation);
///  * exactly one factor-base point: `ground` (the other becomes a vertex with a known log);
///  * a double root X = Y outside the base: `ground` with `half` (2*lambda_X = eta - lambda_A - lambda_B);
///  * both outside: an `edge` between two large primes.
pub struct Rel2Out {
    pub full: Vec<Vec<(u32, u8)>>,
    pub ground: Vec<(u32, Vec<(u32, u8)>, bool)>, // (vertex, factor-base part, half)
    pub edges: Vec<(u32, u32, u32, u32)>,         // (vertex x, vertex y, fb index of A, fb index of B)
    pub vertex_pts: Vec<P3>,
    pub pairs: u64,
    pub no_roots: u64,
}

pub fn find_relations_2lp(cv: &Curve, fb: &[P3]) -> Rel2Out {
    let f = &cv.f;
    let n = fb.len();
    let idx: HashMap<u64, u32> = fb.iter().enumerate().map(|(i, p)| (pack(p), i as u32)).collect();
    bump_hash(n as u64);
    let mut vid: HashMap<u64, u32> = HashMap::new();
    let mut out = Rel2Out { full: vec![], ground: vec![], edges: vec![], vertex_pts: vec![], pairs: 0, no_roots: 0 };
    let inv2 = f.inv(2);
    // partial derivatives of F at A, by monomial
    let grad = |a: &P3| -> [u64; 3] {
        let mut pw = [[1u64; 5]; 3];
        for i in 0..3 {
            for e in 1..5 {
                pw[i][e] = f.mul(pw[i][e - 1], a[i]);
            }
        }
        let mut g = [0u64; 3];
        for (m, &(x, y, z)) in cv.mons.iter().enumerate() {
            let co = cv.coef[m];
            if co == 0 {
                continue;
            }
            let ex = [x as usize, y as usize, z as usize];
            for v in 0..3 {
                if ex[v] == 0 {
                    continue;
                }
                let mut e2 = ex;
                e2[v] -= 1;
                let t = f.mul(f.mul(pw[0][e2[0]], pw[1][e2[1]]), pw[2][e2[2]]);
                let t = f.mul(f.mul(t, co), ex[v] as u64);
                g[v] = f.add(g[v], t);
            }
        }
        g
    };
    let mut get_vertex = |p: P3, out: &mut Rel2Out| -> u32 {
        bump_hash(1);
        let k = pack(&p);
        if let Some(&v) = vid.get(&k) {
            return v;
        }
        let v = out.vertex_pts.len() as u32;
        out.vertex_pts.push(p);
        vid.insert(k, v);
        v
    };
    for i in 0..n {
        let a = fb[i];
        let ga = grad(&a);
        for j in i + 1..n {
            let b = fb[j];
            out.pairs += 1;
            let d = [f.sub(b[0], a[0]), f.sub(b[1], a[1]), f.sub(b[2], a[2])];
            let c4 = cv.eval(&d);
            let c1 = f.add(f.add(f.mul(ga[0], d[0]), f.mul(ga[1], d[1])), f.mul(ga[2], d[2]));
            let am = [f.sub(a[0], d[0]), f.sub(a[1], d[1]), f.sub(a[2], d[2])];
            let g1 = cv.eval(&am);
            let s_ = f.neg(f.add(c1, c4));
            let t_ = f.sub(f.add(g1, c1), c4);
            let c2 = f.mul(f.add(s_, t_), inv2);
            let c3 = f.mul(f.sub(s_, t_), inv2);
            let bq = f.add(c4, c3);
            // residual quadratic c4 s^2 + bq s - c1 ; points A + s D (s = infinity: D)
            let mut pts: Vec<P3> = Vec::with_capacity(2);
            let mk = |s: u64| -> P3 { pnorm(f, &[f.add(a[0], f.mul(s, d[0])), f.add(a[1], f.mul(s, d[1])), f.add(a[2], f.mul(s, d[2]))]) };
            if c4 == 0 {
                if d != [0, 0, 0] {
                    pts.push(pnorm(f, &d));
                }
                if bq != 0 {
                    pts.push(mk(f.mul(c1, f.inv(bq))));
                } else if c1 == 0 {
                    // degenerate (line inside C cannot happen for a smooth quartic)
                    out.no_roots += 1;
                    continue;
                } else {
                    out.no_roots += 1;
                    continue;
                }
            } else {
                let disc = f.add(f.mul(bq, bq), f.mul(4, f.mul(c4, c1)));
                match f.sqrt(disc) {
                    None => {
                        out.no_roots += 1;
                        continue;
                    }
                    Some(sq) => {
                        let i2c = f.inv(f.mul(2, c4));
                        let r1 = f.mul(f.sub(sq, bq), i2c);
                        let r2 = f.mul(f.sub(f.neg(sq), bq), i2c);
                        pts.push(mk(r1));
                        pts.push(mk(r2));
                    }
                }
            }
            if pts.len() != 2 {
                out.no_roots += 1;
                continue;
            }
            // classify
            let fi = |p: &P3| -> Option<u32> {
                bump_hash(1);
                idx.get(&pack(p)).copied()
            };
            let (x, y) = (pts[0], pts[1]);
            let (fx, fy) = (fi(&x), fi(&y));
            let mut fpart: Vec<(u32, u8)> = vec![(i as u32, 1), (j as u32, 1)];
            let mut add_f = |fp: &mut Vec<(u32, u8)>, k: u32| {
                if let Some(e) = fp.iter_mut().find(|e| e.0 == k) {
                    e.1 += 1;
                } else {
                    fp.push((k, 1));
                }
            };
            match (fx, fy) {
                (Some(kx), Some(ky)) => {
                    add_f(&mut fpart, kx);
                    add_f(&mut fpart, ky);
                    out.full.push(fpart);
                }
                (Some(kx), None) => {
                    add_f(&mut fpart, kx);
                    let v = get_vertex(y, &mut out);
                    out.ground.push((v, fpart, false));
                }
                (None, Some(ky)) => {
                    add_f(&mut fpart, ky);
                    let v = get_vertex(x, &mut out);
                    out.ground.push((v, fpart, false));
                }
                (None, None) => {
                    if x == y {
                        let v = get_vertex(x, &mut out);
                        out.ground.push((v, fpart, true));
                    } else {
                        let vx = get_vertex(x, &mut out);
                        let vy = get_vertex(y, &mut out);
                        out.edges.push((vx, vy, i as u32, j as u32));
                    }
                }
            }
        }
    }
    out
}

fn vec_from(map: HashMap<u32, u64>) -> Row {
    let mut v: Row = map.into_iter().filter(|x| x.1 != 0).collect();
    v.sort();
    v
}
fn acc(map: &mut HashMap<u32, u64>, c: u32, v: u64, ell: u64) {
    let e = map.entry(c).or_insert(0);
    *e = la(*e, v, ell);
}

/// Relation rows from the large-prime graph. Every vertex gets a potential `p_v` (a sparse
/// vector over the factor-base columns and eta, with lambda_v = p_v . (lambda, eta)): grounded
/// vertices from their ground relation, others along breadth-first tree edges. Each non-tree edge
/// (and each repeated grounding) gives a relation among factor-base logs and eta only.
pub fn cycle_rows_2lp(ro: &Rel2Out, ell: u64, eta_col: u32, target: usize) -> Vec<Row> {
    let nv = ro.vertex_pts.len();
    let mut p: Vec<Option<Row>> = vec![None; nv];
    let mut adj: Vec<Vec<(u32, u32)>> = vec![vec![]; nv];
    for (e, &(x, y, _, _)) in ro.edges.iter().enumerate() {
        adj[x as usize].push((y, e as u32));
        adj[y as usize].push((x, e as u32));
    }
    let col = |i: u32| -> Option<u32> { if i == 0 { None } else { Some(i - 1) } };
    let minus1 = ell - 1;
    let inv2 = (ell + 1) / 2;
    let mut rows: Vec<Row> = Vec::new();
    let mut queue: std::collections::VecDeque<u32> = std::collections::VecDeque::new();
    for (v, fpart, half) in &ro.ground {
        let mut m: HashMap<u32, u64> = HashMap::new();
        let sc = if *half { inv2 } else { 1 };
        acc(&mut m, eta_col, sc, ell);
        for &(i, mu) in fpart {
            if let Some(c) = col(i) {
                acc(&mut m, c, lm(lm(mu as u64, sc, ell), minus1, ell), ell);
            }
        }
        let newp = vec_from(m);
        match &p[*v as usize] {
            None => {
                p[*v as usize] = Some(newp);
                queue.push_back(*v);
            }
            Some(old) => {
                let mut m2: HashMap<u32, u64> = HashMap::new();
                for &(c, a) in &newp {
                    acc(&mut m2, c, a, ell);
                }
                for &(c, a) in old {
                    acc(&mut m2, c, lm(a, minus1, ell), ell);
                }
                let r = vec_from(m2);
                if !r.is_empty() {
                    rows.push(r);
                }
            }
        }
    }
    let mut used = vec![false; ro.edges.len()];
    'bfs: while let Some(x) = queue.pop_front() {
        let px = p[x as usize].clone().unwrap();
        for &(y, e) in &adj[x as usize] {
            if used[e as usize] {
                continue;
            }
            used[e as usize] = true;
            let (_, _, ia, ib) = ro.edges[e as usize];
            let mut fe: HashMap<u32, u64> = HashMap::new();
            for i in [ia, ib] {
                if let Some(c) = col(i) {
                    acc(&mut fe, c, 1, ell);
                }
            }
            match &p[y as usize] {
                None => {
                    // p_y = eta - F_e - p_x
                    let mut m: HashMap<u32, u64> = HashMap::new();
                    acc(&mut m, eta_col, 1, ell);
                    for (&c, &a) in &fe {
                        acc(&mut m, c, lm(a, minus1, ell), ell);
                    }
                    for &(c, a) in &px {
                        acc(&mut m, c, lm(a, minus1, ell), ell);
                    }
                    p[y as usize] = Some(vec_from(m));
                    queue.push_back(y);
                }
                Some(py) => {
                    // F_e + p_x + p_y - eta = 0
                    let mut m: HashMap<u32, u64> = HashMap::new();
                    for (&c, &a) in &fe {
                        acc(&mut m, c, a, ell);
                    }
                    for &(c, a) in &px {
                        acc(&mut m, c, a, ell);
                    }
                    for &(c, a) in py {
                        acc(&mut m, c, a, ell);
                    }
                    acc(&mut m, eta_col, minus1, ell);
                    let r = vec_from(m);
                    if !r.is_empty() {
                        rows.push(r);
                    }
                    if rows.len() >= target {
                        break 'bfs;
                    }
                }
            }
        }
    }
    rows
}

/// After the factor-base logs and eta are known, the log of every vertex reachable from a
/// grounded vertex, by the same breadth-first propagation with numbers instead of vectors.
pub fn propagate_2lp(ro: &Rel2Out, fb_log: &dyn Fn(u32) -> Option<u64>, eta: u64, ell: u64) -> Vec<Option<u64>> {
    let nv = ro.vertex_pts.len();
    let mut lam: Vec<Option<u64>> = vec![None; nv];
    let mut adj: Vec<Vec<(u32, u32)>> = vec![vec![]; nv];
    for (e, &(x, y, _, _)) in ro.edges.iter().enumerate() {
        adj[x as usize].push((y, e as u32));
        adj[y as usize].push((x, e as u32));
    }
    let inv2 = (ell + 1) / 2;
    let mut queue: std::collections::VecDeque<u32> = std::collections::VecDeque::new();
    for (v, fpart, half) in &ro.ground {
        if lam[*v as usize].is_some() {
            continue;
        }
        let mut s = 0u64;
        let mut ok = true;
        for &(i, mu) in fpart {
            match fb_log(i) {
                Some(l) => s = la(s, lm(mu as u64, l, ell), ell),
                None => {
                    ok = false;
                    break;
                }
            }
        }
        if ok {
            let mut v0 = ls(eta, s, ell);
            if *half {
                v0 = lm(v0, inv2, ell);
            }
            lam[*v as usize] = Some(v0);
            queue.push_back(*v);
        }
    }
    while let Some(x) = queue.pop_front() {
        let lx = lam[x as usize].unwrap();
        for &(y, e) in &adj[x as usize] {
            if lam[y as usize].is_some() {
                continue;
            }
            let (_, _, ia, ib) = ro.edges[e as usize];
            if let (Some(la_), Some(lb)) = (fb_log(ia), fb_log(ib)) {
                let v = ls(ls(ls(eta, la_, ell), lb, ell), lx, ell);
                lam[y as usize] = Some(v);
                queue.push_back(y);
            }
        }
    }
    lam
}
