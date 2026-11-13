// GHS m=2 instance over F_q (q = 7 mod 12) at scale: E0/K, its Weierstrass model, the plane
// quartic over F_q, the transfer divisors. Independent of quartic_ic.rs (whose Zech-table
// field caps at q ~ 200). Construction as in research/ghs_cubic_genus3_build_20261012.
#![allow(dead_code)]
use crate::common::*;
use crate::pic;
use std::collections::{BTreeMap, HashMap};

pub type T = BTreeMap<(u8, u8, u8), K>;

fn tadd(kf: &Kf, a: &T, b: &T) -> T {
    let mut r = a.clone();
    for (k, v) in b {
        let e = r.entry(*k).or_insert(KZERO);
        *e = kf.add(e, v);
    }
    r.retain(|_, v| *v != KZERO);
    r
}
fn tmul(kf: &Kf, a: &T, b: &T) -> T {
    let mut r = T::new();
    for (k1, v1) in a {
        for (k2, v2) in b {
            let e = r.entry((k1.0 + k2.0, k1.1 + k2.1, k1.2 + k2.2)).or_insert(KZERO);
            *e = kf.add(e, &kf.mul(v1, v2));
        }
    }
    r.retain(|_, v| *v != KZERO);
    r
}
fn tscale(kf: &Kf, a: &T, c: &K) -> T {
    a.iter().map(|(k, v)| (*k, kf.mul(v, c))).filter(|x| x.1 != KZERO).collect()
}
fn tlin(c: [K; 3]) -> T {
    let mut r = T::new();
    for (i, k) in [(1u8, 0u8, 0u8), (0, 1, 0), (0, 0, 1)].iter().enumerate() {
        if c[i] != KZERO {
            r.insert(*k, c[i]);
        }
    }
    r
}

pub type M3 = [[K; 3]; 3];
fn det3(kf: &Kf, m: &M3) -> K {
    let mm = |x: &K, y: &K| kf.mul(x, y);
    let a = mm(&m[0][0], &kf.sub(&mm(&m[1][1], &m[2][2]), &mm(&m[1][2], &m[2][1])));
    let b = mm(&m[0][1], &kf.sub(&mm(&m[1][0], &m[2][2]), &mm(&m[1][2], &m[2][0])));
    let c = mm(&m[0][2], &kf.sub(&mm(&m[1][0], &m[2][1]), &mm(&m[1][1], &m[2][0])));
    kf.add(&kf.sub(&a, &b), &c)
}
fn inv3(kf: &Kf, m: &M3) -> Option<M3> {
    let d = det3(kf, m);
    if d == KZERO {
        return None;
    }
    let di = kf.inv(&d);
    let mm = |x: &K, y: &K| kf.mul(x, y);
    let cof = |r0: usize, r1: usize, c0: usize, c1: usize| {
        kf.sub(&mm(&m[r0][c0], &m[r1][c1]), &mm(&m[r0][c1], &m[r1][c0]))
    };
    // adjugate / det
    let mut out = [[KZERO; 3]; 3];
    for i in 0..3 {
        for j in 0..3 {
            let (r0, r1) = match j {
                0 => (1, 2),
                1 => (0, 2),
                _ => (0, 1),
            };
            let (c0, c1) = match i {
                0 => (1, 2),
                1 => (0, 2),
                _ => (0, 1),
            };
            let mut v = cof(r0, r1, c0, c1);
            if (i + j) % 2 == 1 {
                v = kf.neg(&v);
            }
            out[i][j] = mm(&v, &di);
        }
    }
    Some(out)
}

#[derive(Clone, Copy, PartialEq, Eq, Debug, Hash)]
pub enum EP {
    Inf,
    A(K, K),
}

/// w^2 = V^3 + a2 V^2 + a4 V + a6 over K.
#[derive(Clone)]
pub struct Ec {
    pub kf: Kf,
    pub a2: K,
    pub a4: K,
    pub a6: K,
}
impl Ec {
    pub fn on(&self, p: &EP) -> bool {
        match p {
            EP::Inf => true,
            EP::A(x, y) => {
                let kf = &self.kf;
                let x2 = kf.mul(x, x);
                let r = kf.add(
                    &kf.add(&kf.mul(&x2, x), &kf.mul(&self.a2, &x2)),
                    &kf.add(&kf.mul(&self.a4, x), &self.a6),
                );
                kf.mul(y, y) == r
            }
        }
    }
    pub fn neg(&self, p: &EP) -> EP {
        match p {
            EP::Inf => EP::Inf,
            EP::A(x, y) => EP::A(*x, self.kf.neg(y)),
        }
    }
    pub fn add(&self, p: &EP, q: &EP) -> EP {
        let kf = &self.kf;
        match (p, q) {
            (EP::Inf, _) => *q,
            (_, EP::Inf) => *p,
            (EP::A(x1, y1), EP::A(x2, y2)) => {
                let lam;
                if x1 == x2 {
                    if kf.add(y1, y2) == KZERO {
                        return EP::Inf;
                    }
                    let x12 = kf.mul(x1, x1);
                    let three = kf.add(&kf.add(&x12, &x12), &x12);
                    let num = kf.add(
                        &kf.add(&three, &kf.mul(&kf.add(&self.a2, &self.a2), x1)),
                        &self.a4,
                    );
                    let den = kf.add(y1, y1);
                    lam = kf.mul(&num, &kf.inv(&den));
                } else {
                    let num = kf.sub(y2, y1);
                    let den = kf.sub(x2, x1);
                    lam = kf.mul(&num, &kf.inv(&den));
                }
                let l2 = kf.mul(&lam, &lam);
                let x3 = kf.sub(&kf.sub(&kf.sub(&l2, &self.a2), x1), x2);
                let y3 = kf.sub(&kf.mul(&lam, &kf.sub(x1, &x3)), y1);
                EP::A(x3, y3)
            }
        }
    }
    pub fn mul(&self, p: &EP, mut k: u128) -> EP {
        let mut r = EP::Inf;
        let mut b = *p;
        while k > 0 {
            if k & 1 == 1 {
                r = self.add(&r, &b);
            }
            k >>= 1;
            if k > 0 {
                b = self.add(&b, &b);
            }
        }
        r
    }
    pub fn rand_point(&self, rng: &mut Rng) -> EP {
        let kf = &self.kf;
        loop {
            let x = kf.rand(rng);
            let x2 = kf.mul(&x, &x);
            let r = kf.add(
                &kf.add(&kf.mul(&x2, &x), &kf.mul(&self.a2, &x2)),
                &kf.add(&kf.mul(&self.a4, &x), &self.a6),
            );
            if let Some(y) = kf.sqrt(&r) {
                return EP::A(x, y);
            }
        }
    }
    /// Group order by Hasse-interval baby-step giant-step on one point; None if the
    /// interval holds more than one multiple of the point order.
    pub fn order_bsgs(&self, rng: &mut Rng) -> Option<u128> {
        let q = self.kf.q() as u128;
        let n0 = q * q * q + 1;
        let h = (2.0 * (q as f64).powf(1.5)) as u128 + 2;
        let p = self.rand_point(rng);
        if p == EP::Inf {
            return None;
        }
        let s = (((2 * h + 1) as f64).sqrt().ceil() as u128) + 1;
        let mut baby: HashMap<EP, u128> = HashMap::new();
        let mut cur = EP::Inf;
        for b in 0..s {
            baby.entry(cur).or_insert(b);
            cur = self.add(&cur, &p);
        }
        // T' = -(n0 - h)P  ->  find m' in [0, 2h] with m' P = (n0 - h) P ... use m'P = -Q0' where Q0'=(n0-h)P
        // we need n with nP = O, n = n0 - h + m'  =>  m'P = -(n0-h)P
        let q0 = self.mul(&p, n0 - h);
        let target = self.neg(&q0);
        let sp = self.mul(&p, s);
        let mut hits = Vec::new();
        let mut g = target;
        let nsp = self.neg(&sp);
        let mut a = 0u128;
        while a * s <= 2 * h + s {
            if let Some(&b) = baby.get(&g) {
                let m = a * s + b;
                if m <= 2 * h {
                    hits.push(n0 - h + m);
                }
            }
            g = self.add(&g, &nsp);
            a += 1;
        }
        // note: target - a*sP = bP  =>  (a*s + b)P = target
        hits.sort();
        hits.dedup();
        if hits.len() == 1 {
            Some(hits[0])
        } else {
            None
        }
    }
}

/// Cubic-curve data and the plane quartic of one instance.
#[derive(Clone)]
pub struct Inst {
    pub q: u64,
    pub kf: Kf,
    pub u: [K; 2], // u = t^2 + u[1] t + u[0]
    pub u1: [K; 2],
    pub u2: [K; 2],
    pub qa: K, // f0 = t^4 + a t^3 + b t^2 + c t + d  (a,b,c,d in K)
    pub qb: K,
    pub qc: K,
    pub qd: K,
    pub ec: Ec,
    pub order: u128,
    pub ell: u64,
    pub g: EP,
    pub om: M3,
    pub f: [u32; 15], // quartic over F_q, order of pic::mons_of_degree(4)
    pub tries: u64,
}

fn ev_u(kf: &Kf, u: &[K; 2], t: &K) -> K {
    // t^2 + u1 t + u0
    kf.add(&kf.add(&kf.mul(t, t), &kf.mul(&u[1], t)), &u[0])
}
fn res_nonzero(kf: &Kf, a: &[K; 2], b: &[K; 2]) -> bool {
    // monic quadratics t^2 + b1 t + c1 ; resultant = d0^2 - b1 d0 d1 + c1 d1^2
    let (c1, b1) = (a[0], a[1]);
    let d0 = kf.sub(&a[0], &b[0]);
    let d1 = kf.sub(&a[1], &b[1]);
    let r = kf.add(
        &kf.sub(&kf.mul(&d0, &d0), &kf.mul(&kf.mul(&b1, &d0), &d1)),
        &kf.mul(&c1, &kf.mul(&d1, &d1)),
    );
    r != KZERO
}

impl Inst {
    /// Seeded search: first (b,c) in the rng stream with all conditions. `None` after `max`.
    pub fn search(q: u64, seed: u64, max: u64) -> Option<Inst> {
        let kf = Kf::new(q);
        let mut rng = Rng::new(seed ^ (q << 20));
        let m4 = pic::mons_of_degree(4);
        let inv2 = inv_mod_u64(2, q);
        let _ = inv2;
        let mut tries = 0u64;
        while tries < max {
            tries += 1;
            let c0 = kf.rand(&mut rng);
            let b0 = kf.rand(&mut rng);
            let u = [c0, b0];
            let u1 = [kf.frob(&u[0]), kf.frob(&u[1])];
            let u2 = [kf.frob(&u1[0]), kf.frob(&u1[1])];
            let disc = kf.sub(&kf.mul(&u[1], &u[1]), &kf.mul_fq(&u[0], 4));
            if disc == KZERO
                || !res_nonzero(&kf, &u, &u1)
                || !res_nonzero(&kf, &u, &u2)
                || !res_nonzero(&kf, &u1, &u2)
            {
                continue;
            }
            let mrows: M3 = [[u[0], u[1], KONE], [u1[0], u1[1], KONE], [u2[0], u2[1], KONE]];
            if det3(&kf, &mrows) == KZERO {
                continue;
            }
            // f0 = u * u2 = t^4 + a t^3 + b t^2 + c t + d
            let qa = kf.add(&u[1], &u2[1]);
            let qb = kf.add(&kf.add(&u[0], &u2[0]), &kf.mul(&u[1], &u2[1]));
            let qc = kf.add(&kf.mul(&u[1], &u2[0]), &kf.mul(&u2[1], &u[0]));
            let qd = kf.mul(&u[0], &u2[0]);
            let a2 = qb;
            let a4 = kf.sub(&kf.mul(&qa, &qc), &kf.mul_fq(&qd, 4));
            let a6 = kf.add(
                &kf.sub(&kf.mul(&qc, &qc), &kf.mul_fq(&kf.mul(&qb, &qd), 4)),
                &kf.mul(&kf.mul(&qa, &qa), &qd),
            );
            let ec = Ec { kf: kf.clone(), a2, a4, a6 };
            let n = match ec.order_bsgs(&mut rng) {
                Some(n) => n,
                None => continue,
            };
            if n % 4 != 0 {
                continue;
            }
            let ell = n / 4;
            if ell > u64::MAX as u128 || !is_prime(ell as u64) {
                continue;
            }
            // confirm the order with a second point
            let p2 = ec.rand_point(&mut rng);
            if ec.mul(&p2, n) != EP::Inf {
                continue;
            }
            let ell = ell as u64;
            // generator of the ell-part
            let mut g = EP::Inf;
            for _ in 0..50 {
                let r = ec.rand_point(&mut rng);
                g = ec.mul(&r, 4);
                if g != EP::Inf {
                    break;
                }
            }
            if g == EP::Inf || ec.mul(&g, ell as u128) != EP::Inf {
                continue;
            }
            // plane quartic
            let rinv = match inv3(&kf, &mrows) {
                Some(r) => r,
                None => continue,
            };
            let om = om_matrix(&kf);
            let omi = match inv3(&kf, &om) {
                Some(r) => r,
                None => continue,
            };
            let lin = [tlin(omi[0]), tlin(omi[1]), tlin(omi[2])];
            let sqx = tmul(&kf, &lin[0], &lin[0]);
            let sqy = tmul(&kf, &lin[1], &lin[1]);
            let sqz = tmul(&kf, &lin[2], &lin[2]);
            let li = |i: usize| -> T {
                // R_i . (Z^2, X^2, Y^2)
                let a = tscale(&kf, &sqz, &rinv[i][0]);
                let b = tscale(&kf, &sqx, &rinv[i][1]);
                let c = tscale(&kf, &sqy, &rinv[i][2]);
                tadd(&kf, &tadd(&kf, &a, &b), &c)
            };
            let (l0, l1, l2) = (li(0), li(1), li(2));
            let g1 = tmul(&kf, &l1, &l1);
            let g2 = tscale(&kf, &tmul(&kf, &l0, &l2), &kf.neg(&KONE));
            let gw = tadd(&kf, &g1, &g2);
            let lead = m4.iter().find_map(|m| gw.get(m)).copied();
            let lead = match lead {
                Some(l) => l,
                None => continue,
            };
            let li = kf.inv(&lead);
            let gwn = tscale(&kf, &gw, &li);
            if !gwn.values().all(|v| kf.is_fq(v)) {
                continue;
            }
            let mut f = [0u32; 15];
            for (i, m) in m4.iter().enumerate() {
                if let Some(v) = gwn.get(m) {
                    f[i] = v[0] as u32;
                }
            }
            if !pic::smoothness_certificate(q as u32, &f) {
                continue;
            }
            return Some(Inst {
                q,
                kf: kf.clone(),
                u,
                u1,
                u2,
                qa,
                qb,
                qc,
                qd,
                ec,
                order: n,
                ell,
                g,
                om,
                f,
                tries,
            });
        }
        None
    }

    /// E0 (Weierstrass) -> quartic coordinates (t, y0); None at the exceptional fibres.
    pub fn ec_to_quartic(&self, p: &EP) -> Option<(K, K)> {
        let kf = &self.kf;
        let (v, w) = match p {
            EP::Inf => return None,
            EP::A(v, w) => (*v, *w),
        };
        let q = kf.q();
        let inv2 = inv_mod_u64(2, q);
        let inv4 = inv2 * inv2 % q;
        // A = b - a^2/4 + V ; B = c + a V/2
        let a2q = kf.mul_fq(&kf.mul(&self.qa, &self.qa), inv4);
        let aa = kf.add(&kf.sub(&self.qb, &a2q), &v);
        if aa == KZERO {
            return None;
        }
        let bb = kf.add(&self.qc, &kf.mul_fq(&kf.mul(&self.qa, &v), inv2));
        let t = kf.mul(&kf.sub(&w, &bb), &kf.inv(&kf.mul_fq(&aa, 2)));
        // y = -V/2 + t^2 + (a/2) t
        let y = kf.add(
            &kf.add(&kf.mul_fq(&v, q - inv2), &kf.mul(&t, &t)),
            &kf.mul_fq(&kf.mul(&self.qa, &t), inv2),
        );
        Some((t, y))
    }
    pub fn quartic_to_ec(&self, t: &K, y: &K) -> EP {
        let kf = &self.kf;
        let q = kf.q();
        let inv2 = inv_mod_u64(2, q);
        let t2 = kf.mul(t, t);
        // V = 2 t^2 + a t - 2 y
        let v = kf.sub(&kf.add(&kf.mul_fq(&t2, 2), &kf.mul(&self.qa, t)), &kf.mul_fq(y, 2));
        let inv4 = inv2 * inv2 % q;
        let a2q = kf.mul_fq(&kf.mul(&self.qa, &self.qa), inv4);
        let aa = kf.add(&kf.sub(&self.qb, &a2q), &v);
        let bb = kf.add(&self.qc, &kf.mul_fq(&kf.mul(&self.qa, &v), inv2));
        // w = 2 t A + B
        let w = kf.add(&kf.mul(&kf.mul_fq(t, 2), &aa), &bb);
        EP::A(v, w)
    }

    /// f0(t)^{...}: u(t), u'(t)
    pub fn u_at(&self, t: &K) -> (K, K) {
        (ev_u(&self.kf, &self.u, t), ev_u(&self.kf, &self.u1, t))
    }

    /// Transfer divisor of E0-point p: the two Frobenius orbits of lifts W^{+-} (each
    /// three K-points of the plane quartic). None if p is not a valid transfer.
    pub fn transfer_w(&self, p: &EP) -> Option<Vec<[K; 3]>> {
        let kf = &self.kf;
        let (t, y0) = self.ec_to_quartic(p)?;
        let (ut, u1t) = self.u_at(&t);
        let v1 = kf.mul(&ut, &u1t);
        if v1 == KZERO || ut == KZERO {
            return None;
        }
        let s = kf.sqrt(&v1)?;
        let iu = kf.inv(&ut);
        let mut out = Vec::new();
        for sgn in 0..2 {
            let y1 = if sgn == 0 { s } else { kf.neg(&s) };
            let y2 = kf.mul(&kf.mul(&y0, &y1), &iu);
            let xyz = [kf.mul(&y1, &y2), kf.mul(&y0, &y2), kf.mul(&y0, &y1)];
            let mut w = [KZERO; 3];
            for j in 0..3 {
                for i in 0..3 {
                    w[j] = kf.add(&w[j], &kf.mul(&self.om[j][i], &xyz[i]));
                }
            }
            let l = *w.iter().find(|x| **x != KZERO)?;
            let li = kf.inv(&l);
            let wn = [kf.mul(&w[0], &li), kf.mul(&w[1], &li), kf.mul(&w[2], &li)];
            out.push(wn);
        }
        Some(out)
    }

    /// Cubics (over F_q, order of mons_of_degree(3)) through the divisor of `transfer_w`;
    /// the 4-dimensional space as 4 rows, or None if degenerate.
    pub fn transfer_cubics(&self, p: &EP) -> Option<Vec<Vec<u32>>> {
        let kf = &self.kf;
        let ws = self.transfer_w(p)?;
        let m3 = pic::mons_of_degree(3);
        let mut eqs: Vec<Vec<u64>> = Vec::new();
        for w in &ws {
            // powers
            let mut pw = [[KONE; 4]; 3];
            for i in 0..3 {
                for e in 1..4 {
                    pw[i][e] = kf.mul(&pw[i][e - 1], &w[i]);
                }
            }
            let vals: Vec<K> = m3
                .iter()
                .map(|&(a, b, c)| {
                    kf.mul(&kf.mul(&pw[0][a as usize], &pw[1][b as usize]), &pw[2][c as usize])
                })
                .collect();
            for coord in 0..3 {
                eqs.push(vals.iter().map(|v| v[coord]).collect());
            }
        }
        let ns = nullspace_fq(&kf.fp, eqs, 10);
        if ns.len() != 4 {
            return None;
        }
        Some(ns.into_iter().map(|v| v.into_iter().map(|x| x as u32).collect()).collect())
    }
}

pub fn om_matrix(kf: &Kf) -> M3 {
    // omega_j = x^j ; row j = (omega_j, omega_j^sigma, omega_j^sigma^2)
    let mut m = [[KZERO; 3]; 3];
    for j in 0..3 {
        let mut w = [0u64; 3];
        w[j] = 1;
        let w0 = w;
        let w1 = kf.frob(&w0);
        let w2 = kf.frob(&w1);
        m[j] = [w0, w1, w2];
    }
    m
}

/// Nullspace of a matrix (rows = equations) over F_q, n unknowns.
pub fn nullspace_fq(f: &Fp, mut rows: Vec<Vec<u64>>, n: usize) -> Vec<Vec<u64>> {
    let mut piv_cols = Vec::new();
    let mut r = 0usize;
    for c in 0..n {
        let mut p = None;
        for i in r..rows.len() {
            if rows[i][c] != 0 {
                p = Some(i);
                break;
            }
        }
        let Some(p) = p else { continue };
        rows.swap(r, p);
        let iv = f.inv(rows[r][c]);
        for j in 0..n {
            rows[r][j] = f.mul(rows[r][j], iv);
        }
        for i in 0..rows.len() {
            if i != r && rows[i][c] != 0 {
                let fct = rows[i][c];
                for j in 0..n {
                    let t = f.mul(fct, rows[r][j]);
                    rows[i][j] = f.sub(rows[i][j], t);
                }
            }
        }
        piv_cols.push(c);
        r += 1;
        if r == rows.len() {
            break;
        }
    }
    let free: Vec<usize> = (0..n).filter(|c| !piv_cols.contains(c)).collect();
    let mut out = Vec::new();
    for &fc in &free {
        let mut v = vec![0u64; n];
        v[fc] = 1;
        for (ri, &pc) in piv_cols.iter().enumerate() {
            v[pc] = f.neg(rows[ri][fc]);
        }
        out.push(v);
    }
    out
}
