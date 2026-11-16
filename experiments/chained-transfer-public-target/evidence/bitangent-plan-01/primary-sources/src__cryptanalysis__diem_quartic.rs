//! W2a: Diem line relations on `m = 2` GHS plane quartics, linear algebra mod `ell`,
//! and a priced Pollard rho arm on the transfer elliptic curve `E0/F_{q^3}`.
//!
//! Protocol: `research/diem_quartic_relations_20261018/PROTOCOL.md` (frozen before any
//! cost was measured). Synthetic instances only; no target descent (that is W2b); no
//! claim about any deployed curve; not compared with an external implementation.
//!
//! Layout of this file (std only, dependency-free):
//!
//! 1. arithmetic: `SplitMix64`, `Fq` (counted multiplications and inversions),
//!    `Kf` (the cubic extension `K = F_q[g]/(g^3 + a g + b)`), `Mont` (mod `ell`),
//!    polynomial root finding over `F_q`.
//! 2. instance generation (`gen_instance`): the quartic of the GHS `m = 2` build in
//!    `F_q` coordinates, smoothness, `#E0(K)` by baby-step giant-step, the explicit map
//!    `pi0 : C -> E0` used for the independent pushforward checks.
//! 3. relation collection (`collect`): FULL, SLP, DLP arms, verification.
//! 4. linear algebra mod `ell` (`solve_mod_ell`).
//! 5. rho on `E0(K)` (`rho_run`).
//!
//! Cost unit: `F_q` multiplications (`Fq::mul`), inversions counted separately and priced
//! by the caller at the measured multiplication equivalent.

use std::cell::Cell;
use std::collections::{BinaryHeap, HashMap, HashSet};
use std::hash::{BuildHasherDefault, Hasher};

// ---------------------------------------------------------------------------
// 1. arithmetic
// ---------------------------------------------------------------------------

/// SplitMix64 PRNG (frozen in the protocol; independent of any external crate).
#[derive(Clone, Debug)]
pub struct SplitMix64(pub u64);

impl SplitMix64 {
    pub fn new(seed: u64) -> Self {
        SplitMix64(seed)
    }
    #[inline]
    pub fn next_u64(&mut self) -> u64 {
        self.0 = self.0.wrapping_add(0x9E37_79B9_7F4A_7C15);
        let mut z = self.0;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        z ^ (z >> 31)
    }
    /// Uniform-enough value in `[0, n)` (modulo bias below `2^-40` for the sizes used).
    #[inline]
    pub fn below(&mut self, n: u64) -> u64 {
        ((self.next_u64() as u128 * n as u128) >> 64) as u64
    }
}

/// Cheap multiplicative hasher for integer-like keys.
#[derive(Default, Clone, Copy)]
pub struct FxHasher(u64);
impl Hasher for FxHasher {
    #[inline]
    fn finish(&self) -> u64 {
        self.0
    }
    #[inline]
    fn write(&mut self, bytes: &[u8]) {
        for &b in bytes {
            self.0 = (self.0.rotate_left(5) ^ b as u64).wrapping_mul(0x517C_C1B7_2722_0A95);
        }
    }
    #[inline]
    fn write_u64(&mut self, i: u64) {
        self.0 = (self.0.rotate_left(5) ^ i).wrapping_mul(0x517C_C1B7_2722_0A95);
    }
    #[inline]
    fn write_u32(&mut self, i: u32) {
        self.write_u64(i as u64)
    }
    #[inline]
    fn write_usize(&mut self, i: usize) {
        self.write_u64(i as u64)
    }
}
pub type FxMap<K, V> = HashMap<K, V, BuildHasherDefault<FxHasher>>;
pub type FxSet<K> = HashSet<K, BuildHasherDefault<FxHasher>>;

/// `F_q`, `q` an odd prime `< 2^31`, with counted multiplications and inversions.
/// Additions and subtractions are not counted (protocol).
pub struct Fq {
    pub p: u64,
    pub muls: Cell<u64>,
    pub invs: Cell<u64>,
    pub sqrts: Cell<u64>,
}

impl Fq {
    pub fn new(p: u64) -> Fq {
        assert!(p % 2 == 1 && p < (1 << 31));
        Fq {
            p,
            muls: Cell::new(0),
            invs: Cell::new(0),
            sqrts: Cell::new(0),
        }
    }
    #[inline]
    pub fn add(&self, a: u64, b: u64) -> u64 {
        let s = a + b;
        if s >= self.p {
            s - self.p
        } else {
            s
        }
    }
    #[inline]
    pub fn sub(&self, a: u64, b: u64) -> u64 {
        if a >= b {
            a - b
        } else {
            a + self.p - b
        }
    }
    #[inline]
    pub fn neg(&self, a: u64) -> u64 {
        if a == 0 {
            0
        } else {
            self.p - a
        }
    }
    #[inline]
    pub fn mul(&self, a: u64, b: u64) -> u64 {
        self.muls.set(self.muls.get() + 1);
        a * b % self.p
    }
    /// Multiplication by a small public constant realised as repeated additions
    /// (not counted, protocol: additions are free).
    #[inline]
    pub fn smul(&self, c: u64, a: u64) -> u64 {
        let mut r = 0;
        for _ in 0..c {
            r = self.add(r, a);
        }
        r
    }
    pub fn int(&self, c: i64) -> u64 {
        c.rem_euclid(self.p as i64) as u64
    }
    pub fn pow(&self, mut a: u64, mut e: u64) -> u64 {
        let mut r = 1;
        while e > 0 {
            if e & 1 == 1 {
                r = self.mul(r, a);
            }
            e >>= 1;
            if e > 0 {
                a = self.mul(a, a);
            }
        }
        r
    }
    /// Inverse by the extended Euclidean algorithm (counted as one inversion).
    pub fn inv(&self, a: u64) -> u64 {
        assert!(a != 0, "inverse of zero");
        self.invs.set(self.invs.get() + 1);
        let (mut t, mut newt) = (0i64, 1i64);
        let (mut r, mut newr) = (self.p as i64, a as i64);
        while newr != 0 {
            let qt = r / newr;
            let tmp = t - qt * newt;
            t = newt;
            newt = tmp;
            let tmp = r - qt * newr;
            r = newr;
            newr = tmp;
        }
        t.rem_euclid(self.p as i64) as u64
    }
    /// Square root for `p = 3 (mod 4)`: `a^((p+1)/4)`, checked (one exponentiation).
    pub fn sqrt(&self, a: u64) -> Option<u64> {
        self.sqrts.set(self.sqrts.get() + 1);
        if a == 0 {
            return Some(0);
        }
        let r = self.pow(a, (self.p + 1) / 4);
        if self.mul(r, r) == a {
            Some(r)
        } else {
            None
        }
    }
    pub fn counts(&self) -> (u64, u64) {
        (self.muls.get(), self.invs.get())
    }
}

/// Miller-Rabin, deterministic for `n < 2^64`.
pub fn is_prime_u64(n: u64) -> bool {
    if n < 2 {
        return false;
    }
    for &p in &[2u64, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37] {
        if n.is_multiple_of(p) {
            return n == p;
        }
    }
    let (mut d, mut s) = (n - 1, 0);
    while d % 2 == 0 {
        d /= 2;
        s += 1;
    }
    let mulm = |a: u64, b: u64| ((a as u128 * b as u128) % n as u128) as u64;
    'w: for &a in &[2u64, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37] {
        let mut x = 1u64;
        let (mut b, mut e) = (a % n, d);
        while e > 0 {
            if e & 1 == 1 {
                x = mulm(x, b);
            }
            b = mulm(b, b);
            e >>= 1;
        }
        if x == 1 || x == n - 1 {
            continue;
        }
        for _ in 0..s - 1 {
            x = mulm(x, x);
            if x == n - 1 {
                continue 'w;
            }
        }
        return false;
    }
    true
}

/// Smallest prime `>= 2^k` that is `3 (mod 4)` (the frozen `q_k`).
pub fn q_of_k(k: u32) -> u64 {
    let mut n = 1u64 << k;
    loop {
        if n % 4 == 3 && is_prime_u64(n) {
            return n;
        }
        n += 1;
    }
}

pub fn isqrt_u128(n: u128) -> u128 {
    if n == 0 {
        return 0;
    }
    let mut x = (n as f64).sqrt() as u128;
    while x * x > n {
        x -= 1;
    }
    while (x + 1) * (x + 1) <= n {
        x += 1;
    }
    x
}

/// Montgomery arithmetic modulo an odd `n < 2^63` (the group order `ell`).
#[derive(Clone, Copy, Debug)]
pub struct Mont {
    pub n: u64,
    ninv: u64, // -n^{-1} mod 2^64
    r2: u64,   // 2^128 mod n
    pub one: u64,
}

impl Mont {
    pub fn new(n: u64) -> Mont {
        assert!(n % 2 == 1 && n < (1u64 << 63));
        let mut inv = n;
        for _ in 0..6 {
            inv = inv.wrapping_mul(2u64.wrapping_sub(n.wrapping_mul(inv)));
        }
        let ninv = inv.wrapping_neg();
        let r = ((1u128 << 64) % n as u128) as u64;
        let r2 = ((r as u128 * r as u128) % n as u128) as u64;
        Mont {
            n,
            ninv,
            r2,
            one: r,
        }
    }
    #[inline]
    fn redc(&self, t: u128) -> u64 {
        let m = (t as u64).wrapping_mul(self.ninv);
        let u = ((t + m as u128 * self.n as u128) >> 64) as u64;
        if u >= self.n {
            u - self.n
        } else {
            u
        }
    }
    #[inline]
    pub fn mul(&self, a: u64, b: u64) -> u64 {
        self.redc(a as u128 * b as u128)
    }
    #[inline]
    pub fn add(&self, a: u64, b: u64) -> u64 {
        let s = a + b;
        if s >= self.n {
            s - self.n
        } else {
            s
        }
    }
    #[inline]
    pub fn sub(&self, a: u64, b: u64) -> u64 {
        if a >= b {
            a - b
        } else {
            a + self.n - b
        }
    }
    #[inline]
    pub fn neg(&self, a: u64) -> u64 {
        if a == 0 {
            0
        } else {
            self.n - a
        }
    }
    /// Plain residue -> Montgomery form.
    #[inline]
    pub fn to(&self, a: u64) -> u64 {
        self.mul(a % self.n, self.r2)
    }
    /// Montgomery form -> plain residue.
    #[inline]
    pub fn from(&self, a: u64) -> u64 {
        self.redc(a as u128)
    }
    pub fn pow(&self, a: u64, mut e: u64) -> u64 {
        let (mut r, mut b) = (self.one, a);
        while e > 0 {
            if e & 1 == 1 {
                r = self.mul(r, b);
            }
            b = self.mul(b, b);
            e >>= 1;
        }
        r
    }
    /// Inverse for prime `n` (Fermat), Montgomery form in and out.
    pub fn inv(&self, a: u64) -> u64 {
        self.pow(a, self.n - 2)
    }
    /// Signed small integer to Montgomery form.
    pub fn from_i(&self, c: i64) -> u64 {
        if c >= 0 {
            self.to(c as u64)
        } else {
            self.neg(self.to((-c) as u64))
        }
    }
}

// ---- univariate polynomials over F_q (low-degree, root finding) ----

pub fn ptrim(a: &mut Vec<u64>) {
    while let Some(&0) = a.last() {
        a.pop();
    }
}

fn pmul(f: &Fq, a: &[u64], b: &[u64]) -> Vec<u64> {
    if a.is_empty() || b.is_empty() {
        return vec![];
    }
    let mut r = vec![0u64; a.len() + b.len() - 1];
    for (i, &x) in a.iter().enumerate() {
        if x == 0 {
            continue;
        }
        for (j, &y) in b.iter().enumerate() {
            let t = f.mul(x, y);
            r[i + j] = f.add(r[i + j], t);
        }
    }
    ptrim(&mut r);
    r
}

/// `a mod m` (m non-zero, leading coefficient inverted once).
fn pmod(f: &Fq, a: &[u64], m: &[u64]) -> Vec<u64> {
    let mut r = a.to_vec();
    ptrim(&mut r);
    let dm = m.len() - 1;
    if dm == 0 {
        return vec![];
    }
    let lead_inv = f.inv(m[dm]);
    while r.len() > dm {
        let c = f.mul(*r.last().unwrap(), lead_inv);
        let sh = r.len() - 1 - dm;
        if c != 0 {
            for i in 0..=dm {
                let t = f.mul(c, m[i]);
                r[sh + i] = f.sub(r[sh + i], t);
            }
        }
        r.pop();
        ptrim(&mut r);
    }
    r
}

fn pgcd(f: &Fq, a: &[u64], b: &[u64]) -> Vec<u64> {
    let (mut x, mut y) = (a.to_vec(), b.to_vec());
    ptrim(&mut x);
    ptrim(&mut y);
    while !y.is_empty() {
        let r = pmod(f, &x, &y);
        x = y;
        y = r;
    }
    // make monic
    if let Some(&l) = x.last() {
        if l != 1 {
            let li = f.inv(l);
            for c in x.iter_mut() {
                *c = f.mul(*c, li);
            }
        }
    }
    x
}

/// `base^e mod m`.
fn ppowmod(f: &Fq, base: &[u64], mut e: u64, m: &[u64]) -> Vec<u64> {
    let mut r = vec![1u64];
    let mut b = pmod(f, base, m);
    while e > 0 {
        if e & 1 == 1 {
            r = pmod(f, &pmul(f, &r, &b), m);
        }
        e >>= 1;
        if e > 0 {
            b = pmod(f, &pmul(f, &b, &b), m);
        }
    }
    r
}

/// All roots in `F_q` of `poly` (distinct roots), `q` odd. Cantor-Zassenhaus splitting
/// with deterministic shifts. Cost is charged to `f`'s multiplication counter.
pub fn roots_fq(f: &Fq, poly: &[u64]) -> Vec<u64> {
    let mut p = poly.to_vec();
    ptrim(&mut p);
    if p.len() <= 1 {
        return vec![];
    }
    // g = gcd(x^q - x, p)
    let xq = ppowmod(f, &[0, 1], f.p, &p);
    let mut d = xq;
    if d.len() < 2 {
        d.resize(2, 0);
    }
    d[1] = f.sub(d[1], 1);
    ptrim(&mut d);
    let g = if d.is_empty() {
        {
            let mut m = p.clone();
            let li = f.inv(*m.last().unwrap());
            for c in m.iter_mut() {
                *c = f.mul(*c, li);
            }
            m
        }
    } else {
        pgcd(f, &p, &d)
    };
    let mut out = vec![];
    split_roots(f, &g, &mut out, 1);
    out.sort_unstable();
    out
}

fn split_roots(f: &Fq, g: &[u64], out: &mut Vec<u64>, shift: u64) {
    let d = g.len() - 1;
    if d == 0 {
        return;
    }
    if d == 1 {
        // g monic: x + g0
        out.push(f.neg(g[0]));
        return;
    }
    let mut s = shift;
    loop {
        // gcd(g, (x + s)^((q-1)/2) - 1)
        let h = ppowmod(f, &[s % f.p, 1], (f.p - 1) / 2, g);
        let mut hm = h;
        if hm.is_empty() {
            hm.push(0);
        }
        hm[0] = f.sub(hm[0], 1);
        ptrim(&mut hm);
        let a = if hm.is_empty() {
            g.to_vec()
        } else {
            pgcd(f, g, &hm)
        };
        let da = a.len() - 1;
        if da > 0 && da < d {
            // other factor: g / a
            let b = pdiv_exact(f, g, &a);
            split_roots(f, &a, out, s + 1);
            split_roots(f, &b, out, s + 1);
            return;
        }
        s += 1;
    }
}

fn pdiv_exact(f: &Fq, a: &[u64], b: &[u64]) -> Vec<u64> {
    let mut r = a.to_vec();
    let db = b.len() - 1;
    let li = f.inv(b[db]);
    let mut qv = vec![0u64; r.len() - db];
    while r.len() > db {
        let c = f.mul(*r.last().unwrap(), li);
        let sh = r.len() - 1 - db;
        qv[sh] = c;
        if c != 0 {
            for i in 0..=db {
                let t = f.mul(c, b[i]);
                r[sh + i] = f.sub(r[sh + i], t);
            }
        }
        r.pop();
    }
    ptrim(&mut qv);
    qv
}

// ---- K = F_q[g]/(g^3 + a g + b) ----

pub type K = [u64; 3];

/// The cubic extension, with the data for its `q`-Frobenius.
pub struct Kf {
    pub f: Fq,
    pub a: u64,
    pub b: u64,
    pub gq: K,
    pub gq2: K,
}

impl Kf {
    /// `(a, b)` lexicographically first with `x^3 + a x + b` irreducible over `F_q`.
    pub fn new(q: u64) -> Kf {
        let f = Fq::new(q);
        let (mut aa, mut bb) = (0u64, 1u64);
        loop {
            let mut irreducible = true;
            for x in 0..q {
                let v = (x * x % q * x + aa * x + bb) % q;
                if v == 0 {
                    irreducible = false;
                    break;
                }
            }
            if irreducible {
                break;
            }
            bb += 1;
            if bb == q {
                bb = 0;
                aa += 1;
            }
        }
        let mut kf = Kf {
            f,
            a: aa,
            b: bb,
            gq: [0; 3],
            gq2: [0; 3],
        };
        let g: K = [0, 1, 0];
        kf.gq = kf.pow(g, q as u128);
        kf.gq2 = kf.mul(&kf.gq, &kf.gq); // (g^2)^q = (g^q)^2
                                         // Frobenius images must be the other roots: gq = g^q, gq2 = g^(q^2); reset counters
        kf.f.muls.set(0);
        kf.f.invs.set(0);
        kf
    }
    pub fn q(&self) -> u64 {
        self.f.p
    }
    #[inline]
    pub fn zero(&self) -> K {
        [0; 3]
    }
    #[inline]
    pub fn one(&self) -> K {
        [1, 0, 0]
    }
    #[inline]
    pub fn from_fq(&self, c: u64) -> K {
        [c, 0, 0]
    }
    #[inline]
    pub fn add(&self, x: &K, y: &K) -> K {
        [
            self.f.add(x[0], y[0]),
            self.f.add(x[1], y[1]),
            self.f.add(x[2], y[2]),
        ]
    }
    #[inline]
    pub fn sub(&self, x: &K, y: &K) -> K {
        [
            self.f.sub(x[0], y[0]),
            self.f.sub(x[1], y[1]),
            self.f.sub(x[2], y[2]),
        ]
    }
    #[inline]
    pub fn neg(&self, x: &K) -> K {
        [self.f.neg(x[0]), self.f.neg(x[1]), self.f.neg(x[2])]
    }
    #[inline]
    pub fn is_zero(&self, x: &K) -> bool {
        x[0] == 0 && x[1] == 0 && x[2] == 0
    }
    /// Product: 9 coefficient products and 4 reduction products (13 counted `F_q` mults).
    pub fn mul(&self, x: &K, y: &K) -> K {
        let f = &self.f;
        let c0 = f.mul(x[0], y[0]);
        let c1 = f.add(f.mul(x[0], y[1]), f.mul(x[1], y[0]));
        let c2 = f.add(
            f.add(f.mul(x[0], y[2]), f.mul(x[1], y[1])),
            f.mul(x[2], y[0]),
        );
        let c3 = f.add(f.mul(x[1], y[2]), f.mul(x[2], y[1]));
        let c4 = f.mul(x[2], y[2]);
        // g^3 = -a g - b ; g^4 = -a g^2 - b g
        let r0 = f.sub(c0, f.mul(self.b, c3));
        let r1 = f.sub(f.sub(c1, f.mul(self.a, c3)), f.mul(self.b, c4));
        let r2 = f.sub(c2, f.mul(self.a, c4));
        [r0, r1, r2]
    }
    /// Scalar (`F_q`) multiple: 3 counted mults.
    pub fn scale(&self, x: &K, c: u64) -> K {
        [
            self.f.mul(x[0], c),
            self.f.mul(x[1], c),
            self.f.mul(x[2], c),
        ]
    }
    pub fn pow(&self, x: K, mut e: u128) -> K {
        let (mut r, mut b) = (self.one(), x);
        while e > 0 {
            if e & 1 == 1 {
                r = self.mul(&r, &b);
            }
            e >>= 1;
            if e > 0 {
                b = self.mul(&b, &b);
            }
        }
        r
    }
    /// `x^q`.
    pub fn frob(&self, x: &K) -> K {
        let t1 = self.scale(&self.gq, x[1]);
        let t2 = self.scale(&self.gq2, x[2]);
        let s = self.add(&t1, &t2);
        [self.f.add(s[0], x[0]), s[1], s[2]]
    }
    /// Inverse through the norm: `x^{-1} = x^q x^{q^2} / N(x)`.
    pub fn inv(&self, x: &K) -> K {
        let x1 = self.frob(x);
        let x2 = self.frob(&x1);
        let t = self.mul(&x1, &x2);
        let n = self.mul(x, &t);
        debug_assert!(n[1] == 0 && n[2] == 0);
        let ni = self.f.inv(n[0]);
        self.scale(&t, ni)
    }
    pub fn in_fq(&self, x: &K) -> bool {
        x[1] == 0 && x[2] == 0
    }
    /// Square root in `K` (`q^3 = 3 mod 4`): `x^((q^3+1)/4)`, checked.
    pub fn sqrt(&self, x: &K) -> Option<K> {
        if self.is_zero(x) {
            return Some(self.zero());
        }
        let q = self.q() as u128;
        let e = (q * q * q + 1) / 4;
        let r = self.pow(*x, e);
        if self.mul(&r, &r) == *x {
            Some(r)
        } else {
            None
        }
    }
    pub fn rand(&self, rng: &mut SplitMix64) -> K {
        let q = self.q();
        [rng.below(q), rng.below(q), rng.below(q)]
    }
}

/// Normalised key of a rational projective point `(x, y, z)` with first non-zero
/// coordinate 1. Valid for `q < 2^22`.
#[inline]
pub fn pt_key(p: &[u64; 3]) -> u64 {
    if p[0] == 1 {
        (p[1] << 22) | p[2]
    } else if p[1] == 1 {
        (1u64 << 60) | p[2]
    } else {
        2u64 << 60
    }
}

pub fn normalize_pt(f: &Fq, p: &[u64; 3]) -> [u64; 3] {
    if p[0] != 0 {
        if p[0] == 1 {
            return *p;
        }
        let i = f.inv(p[0]);
        [1, f.mul(p[1], i), f.mul(p[2], i)]
    } else if p[1] != 0 {
        if p[1] == 1 {
            return *p;
        }
        let i = f.inv(p[1]);
        [0, 1, f.mul(p[2], i)]
    } else {
        assert!(p[2] != 0);
        [0, 0, 1]
    }
}

// ---------------------------------------------------------------------------
// 2. instances
// ---------------------------------------------------------------------------

/// Monomials `W0^i W1^j W2^k` of degree 4 in lexicographically descending order.
pub const MON4: [(u8, u8, u8); 15] = [
    (4, 0, 0),
    (3, 1, 0),
    (3, 0, 1),
    (2, 2, 0),
    (2, 1, 1),
    (2, 0, 2),
    (1, 3, 0),
    (1, 2, 1),
    (1, 1, 2),
    (1, 0, 3),
    (0, 4, 0),
    (0, 3, 1),
    (0, 2, 2),
    (0, 1, 3),
    (0, 0, 4),
];

pub fn mon4_index(e: (u8, u8, u8)) -> usize {
    MON4.iter()
        .position(|&m| m == e)
        .expect("degree-4 monomial")
}

pub type Mono = (u8, u8, u8);
pub type Poly3 = std::collections::BTreeMap<Mono, K>;

pub fn poly3_mul(kf: &Kf, a: &Poly3, b: &Poly3) -> Poly3 {
    let mut r = Poly3::new();
    for (ea, ca) in a {
        for (eb, cb) in b {
            let e = (ea.0 + eb.0, ea.1 + eb.1, ea.2 + eb.2);
            let t = kf.mul(ca, cb);
            let cur = r.entry(e).or_insert([0; 3]);
            *cur = kf.add(cur, &t);
        }
    }
    r.retain(|_, v| !(v[0] == 0 && v[1] == 0 && v[2] == 0));
    r
}

pub fn poly3_add(kf: &Kf, a: &Poly3, b: &Poly3) -> Poly3 {
    let mut r = a.clone();
    for (e, c) in b {
        let cur = r.entry(*e).or_insert([0; 3]);
        *cur = kf.add(cur, c);
    }
    r.retain(|_, v| !(v[0] == 0 && v[1] == 0 && v[2] == 0));
    r
}

pub fn poly3_scale(kf: &Kf, a: &Poly3, c: &K) -> Poly3 {
    let mut r = Poly3::new();
    for (e, v) in a {
        let t = kf.mul(v, c);
        if !kf.is_zero(&t) {
            r.insert(*e, t);
        }
    }
    r
}

pub type M3 = [[K; 3]; 3];

fn det3(kf: &Kf, a: &M3) -> K {
    let m = |x: &K, y: &K| kf.mul(x, y);
    let t0 = m(
        &a[0][0],
        &kf.sub(&m(&a[1][1], &a[2][2]), &m(&a[1][2], &a[2][1])),
    );
    let t1 = m(
        &a[0][1],
        &kf.sub(&m(&a[1][0], &a[2][2]), &m(&a[1][2], &a[2][0])),
    );
    let t2 = m(
        &a[0][2],
        &kf.sub(&m(&a[1][0], &a[2][1]), &m(&a[1][1], &a[2][0])),
    );
    kf.add(&kf.sub(&t0, &t1), &t2)
}

fn inv3(kf: &Kf, a: &M3) -> Option<M3> {
    let d = det3(kf, a);
    if kf.is_zero(&d) {
        return None;
    }
    let di = kf.inv(&d);
    let mut r = [[[0u64; 3]; 3]; 3];
    for i in 0..3 {
        for j in 0..3 {
            let (i1, i2, j1, j2) = ((i + 1) % 3, (i + 2) % 3, (j + 1) % 3, (j + 2) % 3);
            let cof = kf.sub(
                &kf.mul(&a[i1][j1], &a[i2][j2]),
                &kf.mul(&a[i1][j2], &a[i2][j1]),
            );
            r[j][i] = kf.mul(&di, &cof);
        }
    }
    Some(r)
}

/// Elliptic-curve point on the short Weierstrass model over `K`; `None` is the origin.
pub type EPt = Option<(K, K)>;

/// A frozen instance: the GHS quartic over `F_q`, the transfer curve and the explicit map
/// `pi0 : C -> E0`.
pub struct Inst {
    pub q: u64,
    pub kf: Kf,
    pub k: u32,
    pub idx: u32,
    /// `u = t^2 + ub t + uc` over `K`.
    pub ub: K,
    pub uc: K,
    /// The quartic `G(W0, W1, W2)` over `F_q`, coefficients in `MON4` order, first non-zero is 1.
    pub quartic: [u64; 15],
    /// `Omega^{-1}`: `(X, Y, Z)^T = omi * W` (K-coordinates of a point of `C`).
    pub omi: M3,
    /// Rows `R_0, R_1, R_2` with `(1, t, t^2)^T = R (u, u', u'')^T`.
    pub rmat: M3,
    /// Short Weierstrass `Y^2 = X^3 + ea X + eb` over `K`, and map constants.
    pub ea: K,
    pub eb: K,
    wb: K,     // b3: coefficient of t^3 in f = u u''
    ws: K,     // s
    walpha: K, // alpha
    wshift: K, // a2/3
    pub order: u64,
    pub h: u64,
    pub ell: u64,
    pub trace: i128,
    pub candidates: u64,
    /// Number of F_q-quartic generation attempts that were rejected at each filter.
    pub rejects: [u64; 6],
}

impl Inst {
    pub fn f(&self) -> &Fq {
        &self.kf.f
    }

    // ---- elliptic curve E0 over K (affine, one inversion per addition) ----

    pub fn e_neg(&self, p: &EPt) -> EPt {
        p.as_ref().map(|(x, y)| (*x, self.kf.neg(y)))
    }
    pub fn e_add(&self, p: &EPt, r: &EPt) -> EPt {
        let kf = &self.kf;
        match (p, r) {
            (None, _) => *r,
            (_, None) => *p,
            (Some((x1, y1)), Some((x2, y2))) => {
                let lam = if x1 == x2 {
                    if kf.add(y1, y2) == [0; 3] {
                        return None;
                    }
                    // doubling: (3 x^2 + a) / (2 y)
                    let x2s = kf.mul(x1, x1);
                    let num = kf.add(&kf.add(&kf.add(&x2s, &x2s), &x2s), &self.ea);
                    let den = kf.add(y1, y1);
                    kf.mul(&num, &kf.inv(&den))
                } else {
                    let num = kf.sub(y2, y1);
                    let den = kf.sub(x2, x1);
                    kf.mul(&num, &kf.inv(&den))
                };
                let x3 = kf.sub(&kf.sub(&kf.mul(&lam, &lam), x1), x2);
                let y3 = kf.sub(&kf.mul(&lam, &kf.sub(x1, &x3)), y1);
                Some((x3, y3))
            }
        }
    }
    pub fn e_mul(&self, p: &EPt, mut n: u128) -> EPt {
        let mut r: EPt = None;
        let mut b = *p;
        while n > 0 {
            if n & 1 == 1 {
                r = self.e_add(&r, &b);
            }
            n >>= 1;
            if n > 0 {
                b = self.e_add(&b, &b);
            }
        }
        r
    }
    pub fn e_on_curve(&self, p: &EPt) -> bool {
        match p {
            None => true,
            Some((x, y)) => {
                let kf = &self.kf;
                let rhs = kf.add(
                    &kf.add(&kf.mul(x, &kf.mul(x, x)), &kf.mul(&self.ea, x)),
                    &self.eb,
                );
                kf.mul(y, y) == rhs
            }
        }
    }
    pub fn e_random_point(&self, rng: &mut SplitMix64) -> EPt {
        let kf = &self.kf;
        loop {
            let x = kf.rand(rng);
            let rhs = kf.add(
                &kf.add(&kf.mul(&x, &kf.mul(&x, &x)), &kf.mul(&self.ea, &x)),
                &self.eb,
            );
            if let Some(y) = kf.sqrt(&rhs) {
                if !kf.is_zero(&y) {
                    return Some((x, y));
                }
            }
        }
    }

    /// The map `pi0 : C -> E0` on a rational point `W` of `C` (projective coordinates over
    /// `F_q`). Returns `None` if `W` fails `y0^2 = f(t)` (i.e. the point is not on the cover).
    pub fn pi0(&self, w: &[u64; 3]) -> Option<EPt> {
        let kf = &self.kf;
        let wk = [kf.from_fq(w[0]), kf.from_fq(w[1]), kf.from_fq(w[2])];
        let mut xyz = [[0u64; 3]; 3];
        for i in 0..3 {
            let mut s = [0u64; 3];
            for j in 0..3 {
                s = kf.add(&s, &kf.mul(&self.omi[i][j], &wk[j]));
            }
            xyz[i] = s;
        }
        let (x, y, z) = (xyz[0], xyz[1], xyz[2]);
        let ww = [kf.mul(&z, &z), kf.mul(&x, &x), kf.mul(&y, &y)]; // (Z^2, X^2, Y^2)
        let row = |r: &[K; 3]| {
            let mut s = [0u64; 3];
            for j in 0..3 {
                s = kf.add(&s, &kf.mul(&r[j], &ww[j]));
            }
            s
        };
        let s0 = row(&self.rmat[0]);
        let s1 = row(&self.rmat[1]);
        let short = |xw: &K, yp: &K| -> EPt {
            let xs = kf.add(xw, &self.wshift);
            Some((xs, *yp))
        };
        if kf.is_zero(&s0) {
            // t = infinity: y0 / t^2 -> Y / Z = +-1
            if kf.is_zero(&z) {
                return None;
            }
            let r = kf.mul(&y, &kf.inv(&z));
            if r == kf.one() {
                return Some(None);
            }
            if r == kf.neg(&kf.one()) {
                return Some(short(&kf.zero(), &kf.neg(&self.walpha)));
            }
            return None;
        }
        let t = kf.mul(&s1, &kf.inv(&s0));
        // u(t)
        let ut = kf.add(&kf.add(&kf.mul(&t, &t), &kf.mul(&self.ub, &t)), &self.uc);
        let y0 = if kf.is_zero(&z) {
            kf.zero()
        } else {
            kf.mul(&ut, &kf.mul(&y, &kf.inv(&z)))
        };
        // f(t) = u(t) u''(t) is verified via the Weierstrass equation below; also check y0^2 = f(t)
        let u2 = kf.frob(&kf.frob(&self.ub));
        let c2 = kf.frob(&kf.frob(&self.uc));
        let upp = kf.add(&kf.add(&kf.mul(&t, &t), &kf.mul(&u2, &t)), &c2);
        if kf.mul(&y0, &y0) != kf.mul(&ut, &upp) {
            return None;
        }
        // x_W = 2 (y0 + t^2 + (b/2) t + s) ; Y' = 2 x_W t + (b/2) x_W + alpha
        let half = kf.f.inv(2);
        let tt = kf.mul(&t, &t);
        let bh = kf.scale(&self.wb, half);
        let inner = kf.add(&kf.add(&kf.add(&y0, &tt), &kf.mul(&bh, &t)), &self.ws);
        let xw = kf.add(&inner, &inner);
        let yp = kf.add(
            &kf.add(&kf.mul(&kf.add(&xw, &xw), &t), &kf.mul(&bh, &xw)),
            &self.walpha,
        );
        Some(short(&xw, &yp))
    }
}

fn is_square_ratio_ok(_kf: &Kf) -> bool {
    true
}

/// Result of a rejected candidate.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Reject {
    Disc,
    Resultant,
    Independent,
    Ciani,
    Descent,
    Alpha,
    Order,
}

pub struct Core {
    pub quartic: [u64; 15],
    pub omi: M3,
    pub rmat: M3,
    pub ea: K,
    pub eb: K,
    pub wb: K,
    pub ws: K,
    pub walpha: K,
    pub wshift: K,
}

fn resultant_zero(kf: &Kf, a: &[K; 3], b: &[K; 3]) -> bool {
    // monic quadratics share a root iff d0^2 - d1 (a1 b0 - b1 a0) = 0
    let d0 = kf.sub(&a[0], &b[0]);
    let d1 = kf.sub(&a[1], &b[1]);
    let t = kf.sub(&kf.mul(&a[1], &b[0]), &kf.mul(&b[1], &a[0]));
    kf.sub(&kf.mul(&d0, &d0), &kf.mul(&d1, &t)) == [0; 3]
}

pub fn build_core(kf: &Kf, ub: &K, uc: &K) -> Result<Core, Reject> {
    let u = [*uc, *ub, kf.one()];
    let u1 = [kf.frob(&u[0]), kf.frob(&u[1]), kf.one()];
    let u2 = [kf.frob(&u1[0]), kf.frob(&u1[1]), kf.one()];
    let four = kf.from_fq(kf.f.int(4));
    let disc = kf.sub(&kf.mul(&u[1], &u[1]), &kf.mul(&four, &u[0]));
    if kf.is_zero(&disc) {
        return Err(Reject::Disc);
    }
    if resultant_zero(kf, &u, &u1) || resultant_zero(kf, &u, &u2) || resultant_zero(kf, &u1, &u2) {
        return Err(Reject::Resultant);
    }
    let m: M3 = [u, u1, u2];
    let rmat = match inv3(kf, &m) {
        Some(r) => r,
        None => return Err(Reject::Independent),
    };
    // G = s1^2 - s0 s2 with s_i = R_i1 a + R_i2 b + R_i0 c, (a, b, c) = (X^2, Y^2, Z^2)
    let al: Vec<K> = (0..3).map(|i| rmat[i][1]).collect();
    let be: Vec<K> = (0..3).map(|i| rmat[i][2]).collect();
    let ga: Vec<K> = (0..3).map(|i| rmat[i][0]).collect();
    let mm = |x: &K, y: &K| kf.mul(x, y);
    let two = kf.from_fq(2);
    let quad = |p: &Vec<K>, q: &Vec<K>| -> K {
        // coefficient pattern for p_i p_i terms: p1^2 - p0 p2
        let _ = q;
        kf.sub(&mm(&p[1], &p[1]), &mm(&p[0], &p[2]))
    };
    let ca = quad(&al, &al); // X^4
    let cb = quad(&be, &be); // Y^4
    let cc = quad(&ga, &ga); // Z^4
    let cross = |p: &Vec<K>, q: &Vec<K>| -> K {
        kf.sub(
            &mm(&two, &mm(&p[1], &q[1])),
            &kf.add(&mm(&p[0], &q[2]), &mm(&p[2], &q[0])),
        )
    };
    let cd = cross(&al, &be); // X^2 Y^2
    let ce = cross(&be, &ga); // Y^2 Z^2
    let ch = cross(&ga, &al); // Z^2 X^2
                              // Ciani smoothness conditions
    let disc2 = |x: &K, y: &K, z: &K| kf.sub(&mm(z, z), &mm(&four, &mm(x, y)));
    let t2 = kf.from_fq(kf.f.inv(2));
    let mat: M3 = [
        [ca, mm(&cd, &t2), mm(&ch, &t2)],
        [mm(&cd, &t2), cb, mm(&ce, &t2)],
        [mm(&ch, &t2), mm(&ce, &t2), cc],
    ];
    let smooth = !kf.is_zero(&ca)
        && !kf.is_zero(&cb)
        && !kf.is_zero(&cc)
        && !kf.is_zero(&disc2(&ca, &cb, &cd))
        && !kf.is_zero(&disc2(&cb, &cc, &ce))
        && !kf.is_zero(&disc2(&ca, &cc, &ch))
        && !kf.is_zero(&det3(kf, &mat));
    if !smooth {
        return Err(Reject::Ciani);
    }
    // descent coordinates: W_j = w_j X + w_j^s Y + w_j^{s^2} Z, w = (1, g, g^2)
    let basis: [K; 3] = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
    let mut om: M3 = [[[0; 3]; 3]; 3];
    for j in 0..3 {
        om[j] = [basis[j], kf.frob(&basis[j]), kf.frob(&kf.frob(&basis[j]))];
    }
    let omi = inv3(kf, &om).expect("Moore matrix of a basis is invertible");
    // X, Y, Z as linear forms in W
    let lin = |row: &[K; 3]| -> Poly3 {
        let mut p = Poly3::new();
        for (i, e) in [(1u8, 0u8, 0u8), (0, 1, 0), (0, 0, 1)].iter().enumerate() {
            if !kf.is_zero(&row[i]) {
                p.insert(*e, row[i]);
            }
        }
        p
    };
    let (lx, ly, lz) = (lin(&omi[0]), lin(&omi[1]), lin(&omi[2]));
    let (sx, sy, sz) = (
        poly3_mul(kf, &lx, &lx),
        poly3_mul(kf, &ly, &ly),
        poly3_mul(kf, &lz, &lz),
    );
    let mut g = Poly3::new();
    for (coef, p1, p2) in [
        (&ca, &sx, &sx),
        (&cb, &sy, &sy),
        (&cc, &sz, &sz),
        (&cd, &sx, &sy),
        (&ce, &sy, &sz),
        (&ch, &sz, &sx),
    ] {
        let prod = poly3_mul(kf, p1, p2);
        g = poly3_add(kf, &g, &poly3_scale(kf, &prod, coef));
    }
    let mut lead: Option<K> = None;
    for e in MON4.iter() {
        if let Some(c) = g.get(e) {
            lead = Some(*c);
            break;
        }
    }
    let lead = lead.ok_or(Reject::Descent)?;
    let li = kf.inv(&lead);
    let mut quartic = [0u64; 15];
    for (i, e) in MON4.iter().enumerate() {
        if let Some(c) = g.get(e) {
            let n = kf.mul(c, &li);
            if !kf.in_fq(&n) {
                return Err(Reject::Descent);
            }
            quartic[i] = n[0];
        }
    }
    // Weierstrass map constants from f = u u'' = t^4 + b t^3 + c t^2 + d t + e
    let (bb, cc2) = (u[1], u[0]);
    let (b2, c2) = (u2[1], u2[0]);
    let b3 = kf.add(&bb, &b2);
    let c_ = kf.add(&kf.add(&cc2, &c2), &kf.mul(&bb, &b2));
    let d_ = kf.add(&kf.mul(&bb, &c2), &kf.mul(&b2, &cc2));
    let e_ = kf.mul(&cc2, &c2);
    let inv2 = kf.f.inv(2);
    let inv3c = kf.f.inv(3);
    let inv4 = kf.f.inv(4);
    let inv27 = kf.f.inv(27);
    let b3sq = kf.mul(&b3, &b3);
    let s = kf.scale(&kf.sub(&c_, &kf.scale(&b3sq, inv4)), inv2);
    let alpha = kf.sub(&d_, &kf.mul(&b3, &s));
    if kf.is_zero(&alpha) {
        return Err(Reject::Alpha);
    }
    let beta = kf.sub(&e_, &kf.mul(&s, &s));
    let a2c = kf.sub(&b3sq, &kf.scale(&s, kf.f.int(16)));
    let a4c = kf.sub(
        &kf.scale(&kf.mul(&b3, &alpha), 2),
        &kf.scale(&beta, kf.f.int(8)),
    );
    let a2 = kf.scale(&a2c, inv4);
    let a4 = kf.scale(&a4c, inv2);
    let a6 = kf.mul(&alpha, &alpha);
    let shift = kf.scale(&a2, inv3c);
    // x = X - a2/3 ; A = a4 - a2^2/3 ; B = a6 - a2 a4/3 + 2 a2^3/27
    let a2sq = kf.mul(&a2, &a2);
    let ea = kf.sub(&a4, &kf.scale(&a2sq, inv3c));
    let eb = kf.add(
        &kf.sub(&a6, &kf.scale(&kf.mul(&a2, &a4), inv3c)),
        &kf.scale(&kf.mul(&a2sq, &a2), kf.f.int(2) * inv27 % kf.q()),
    );
    let _ = is_square_ratio_ok(kf);
    Ok(Core {
        quartic,
        omi,
        rmat,
        ea,
        eb,
        wb: b3,
        ws: s,
        walpha: alpha,
        wshift: shift,
    })
}

/// `#E0(K)` by baby-step giant-step on the Hasse interval, using several random points
/// until the intersection of the candidate sets is a single multiple.
fn bsgs_order(inst: &Inst, rng: &mut SplitMix64) -> Option<u64> {
    let qq = inst.q as u128;
    let big = qq * qq * qq;
    let r = isqrt_u128(big);
    let lo = big + 1 - 2 * r - 2;
    let hi = big + 1 + 2 * r + 2;
    let width = hi - lo + 1;
    let s = isqrt_u128(width) + 1;
    let mut cands: Option<Vec<u128>> = None;
    for _try in 0..8 {
        let p = inst.e_random_point(rng);
        // baby steps jP, j = 1..s
        let mut table: FxMap<[u64; 3], (u32, K)> = FxMap::default();
        let mut cur = p;
        for j in 1..=s as u32 {
            if let Some((x, y)) = &cur {
                table.entry(*x).or_insert((j, *y));
            } else {
                // jP = O : order j
                let m: u128 = j as u128;
                let _ = m;
            }
            cur = inst.e_add(&cur, &p);
        }
        let gstep = inst.e_mul(&p, s);
        let mut t = inst.e_mul(&p, lo);
        let mut found: Vec<u128> = vec![];
        let mut m = lo;
        while m <= hi {
            match &t {
                None => found.push(m),
                Some((x, y)) => {
                    if let Some((j, yj)) = table.get(x) {
                        if y == yj {
                            // T = jP => (m - j) P = O
                            found.push(m - *j as u128);
                        } else {
                            found.push(m + *j as u128);
                        }
                    }
                }
            }
            t = inst.e_add(&t, &gstep);
            m += s;
        }
        found.retain(|&c| c >= lo && c <= hi && inst.e_mul(&p, c).is_none());
        found.sort_unstable();
        found.dedup();
        let new = match cands.take() {
            None => found,
            Some(prev) => prev.into_iter().filter(|c| found.contains(c)).collect(),
        };
        if new.len() == 1 {
            let n = new[0];
            if n < (1u128 << 64) {
                return Some(n as u64);
            }
            return None;
        }
        if new.is_empty() {
            return None;
        }
        cands = Some(new);
    }
    None
}

/// Generate (or re-derive, deterministically) the frozen instance `(k, idx)` of the protocol.
pub fn gen_instance(k: u32, idx: u32) -> Inst {
    let q = q_of_k(k);
    let kf = Kf::new(q);
    let mut rng = SplitMix64::new(0x5732_414C_0000_0000u64 ^ (q << 8) ^ idx as u64);
    let mut cand = 0u64;
    let mut rej = [0u64; 6];
    loop {
        cand += 1;
        let ub = [rng.below(q), rng.below(q), rng.below(q)];
        let uc = [rng.below(q), rng.below(q), rng.below(q)];
        let core = match build_core(&kf, &ub, &uc) {
            Ok(c) => c,
            Err(r) => {
                rej[match r {
                    Reject::Disc | Reject::Resultant => 0,
                    Reject::Independent => 1,
                    Reject::Ciani => 2,
                    Reject::Descent => 3,
                    Reject::Alpha => 4,
                    Reject::Order => 5,
                }] += 1;
                continue;
            }
        };
        let mut inst = Inst {
            q,
            kf: Kf::new(q),
            k,
            idx,
            ub,
            uc,
            quartic: core.quartic,
            omi: core.omi,
            rmat: core.rmat,
            ea: core.ea,
            eb: core.eb,
            wb: core.wb,
            ws: core.ws,
            walpha: core.walpha,
            wshift: core.wshift,
            order: 0,
            h: 0,
            ell: 0,
            trace: 0,
            candidates: cand,
            rejects: rej,
        };
        let mut orng = SplitMix64::new(0x4F52_4445_0000_0000u64 ^ (q << 8) ^ cand);
        let n = match bsgs_order(&inst, &mut orng) {
            Some(n) => n,
            None => {
                rej[5] += 1;
                continue;
            }
        };
        let mut chosen = None;
        for h in 1..=16u64 {
            if n % h == 0 {
                let l = n / h;
                if is_prime_u64(l)
                    && l < (1u64 << 63)
                    && (l as u128) * (l as u128) > (q as u128).pow(5)
                {
                    chosen = Some((h, l));
                    break;
                }
            }
        }
        let (h, l) = match chosen {
            Some(x) => x,
            None => {
                rej[5] += 1;
                continue;
            }
        };
        inst.order = n;
        inst.h = h;
        inst.ell = l;
        inst.trace = (q as i128).pow(3) + 1 - n as i128;
        inst.candidates = cand;
        inst.rejects = rej;
        inst.kf.f.muls.set(0);
        inst.kf.f.invs.set(0);
        return inst;
    }
}

// ---------------------------------------------------------------------------
// 3. points of C(F_q) and line relations
// ---------------------------------------------------------------------------

/// Evaluate `G` at `p` by direct monomial evaluation (the verification path; independent
/// of the polarisation formulas used for relation collection).
pub fn eval_g(f: &Fq, g: &[u64; 15], p: &[u64; 3]) -> u64 {
    let pw = |x: u64| -> [u64; 5] {
        let x2 = f.mul(x, x);
        let x3 = f.mul(x2, x);
        let x4 = f.mul(x3, x);
        [1, x, x2, x3, x4]
    };
    let (px, py, pz) = (pw(p[0]), pw(p[1]), pw(p[2]));
    let mut s = 0u64;
    for (i, m) in MON4.iter().enumerate() {
        if g[i] != 0 {
            let t = f.mul(
                g[i],
                f.mul(px[m.0 as usize], f.mul(py[m.1 as usize], pz[m.2 as usize])),
            );
            s = f.add(s, t);
        }
    }
    s
}

/// Polynomial in `x` for the slice `W1 = y`, `W2 = 1`.
fn slice_poly(f: &Fq, g: &[u64; 15], y: u64) -> Vec<u64> {
    let mut yp = [1u64; 5];
    for j in 1..5 {
        yp[j] = f.mul(yp[j - 1], y);
    }
    let mut c = vec![0u64; 5];
    for (i, m) in MON4.iter().enumerate() {
        if g[i] != 0 {
            let t = f.mul(g[i], yp[m.1 as usize]);
            c[m.0 as usize] = f.add(c[m.0 as usize], t);
        }
    }
    ptrim(&mut c);
    c
}

/// All `q + 1` rational points of `C` (affine slices plus the line `W2 = 0`), normalised.
pub fn enumerate_points(f: &Fq, g: &[u64; 15]) -> Vec<[u64; 3]> {
    let q = f.p;
    let mut pts = Vec::with_capacity(q as usize + 1);
    for y in 0..q {
        let poly = slice_poly(f, g, y);
        if poly.is_empty() {
            // the whole slice lies on C: impossible for a smooth irreducible quartic
            panic!("line inside C");
        }
        for x in roots_fq(f, &poly) {
            pts.push([x, y, 1]);
        }
    }
    // line at infinity W2 = 0: points (x : 1 : 0) with sum c(i, 4-i, 0) x^i = 0, and (1 : 0 : 0)
    let mut c = vec![0u64; 5];
    for (i, m) in MON4.iter().enumerate() {
        if m.2 == 0 {
            c[m.0 as usize] = g[i];
        }
    }
    ptrim(&mut c);
    if !c.is_empty() {
        for x in roots_fq(f, &c) {
            pts.push(normalize_pt(f, &[x, 1, 0]));
        }
    }
    // (1:0:0) lies on C iff the coefficient of W0^4 vanishes
    if g[0] == 0 {
        pts.push([1, 0, 0]);
    }
    pts
}

/// Sample a uniform rational point of `C` with `W2 != 0` (rejection on the number of roots).
pub fn sample_point(f: &Fq, g: &[u64; 15], rng: &mut SplitMix64) -> [u64; 3] {
    loop {
        let y = rng.below(f.p);
        let poly = slice_poly(f, g, y);
        let r = roots_fq(f, &poly);
        if r.is_empty() {
            continue;
        }
        // accept with probability |r| / 4, then a uniform root
        if (rng.below(4) as usize) < r.len() {
            let x = r[rng.below(r.len() as u64) as usize];
            return [x, y, 1];
        }
    }
}

/// A factor-base point with the Taylor data used to split a line section.
#[derive(Clone)]
pub struct FbPt {
    pub c: [u64; 3],
    /// gradient `(G_x, G_y, G_z)` at `c`
    pub grad: [u64; 3],
    /// `(H_xx/2, H_yy/2, H_zz/2, H_xy, H_xz, H_yz)` at `c`
    pub hess: [u64; 6],
}

/// First and second derivatives of `G` at `p` (counted).
pub fn taylor_data(f: &Fq, g: &[u64; 15], p: &[u64; 3]) -> ([u64; 3], [u64; 6]) {
    let pw = |x: u64| -> [u64; 5] {
        let x2 = f.mul(x, x);
        let x3 = f.mul(x2, x);
        let x4 = f.mul(x3, x);
        [1, x, x2, x3, x4]
    };
    let pp = [pw(p[0]), pw(p[1]), pw(p[2])];
    let mut grad = [0u64; 3];
    let mut hess = [0u64; 6];
    let inv2 = f.inv(2);
    for (idx, m) in MON4.iter().enumerate() {
        if g[idx] == 0 {
            continue;
        }
        let e = [m.0 as usize, m.1 as usize, m.2 as usize];
        let coef = g[idx];
        // monomial value pieces
        let val = |ex: [i32; 3]| -> u64 {
            if ex.iter().any(|&v| v < 0) {
                return 0;
            }
            f.mul(
                pp[0][ex[0] as usize],
                f.mul(pp[1][ex[1] as usize], pp[2][ex[2] as usize]),
            )
        };
        for a in 0..3 {
            if e[a] == 0 {
                continue;
            }
            let mut ex = [e[0] as i32, e[1] as i32, e[2] as i32];
            ex[a] -= 1;
            let t = f.mul(f.smul(e[a] as u64, coef), val(ex));
            grad[a] = f.add(grad[a], t);
        }
        // second derivatives
        let pairs = [(0usize, 0usize), (1, 1), (2, 2), (0, 1), (0, 2), (1, 2)];
        for (pi, &(a, b)) in pairs.iter().enumerate() {
            let mut ex = [e[0] as i32, e[1] as i32, e[2] as i32];
            let ff;
            if a == b {
                if e[a] < 2 {
                    continue;
                }
                ff = (e[a] * (e[a] - 1)) as u64;
                ex[a] -= 2;
            } else {
                if e[a] < 1 || e[b] < 1 {
                    continue;
                }
                ff = (e[a] * e[b]) as u64;
                ex[a] -= 1;
                ex[b] -= 1;
            }
            let t = f.mul(f.smul(ff, coef), val(ex));
            hess[pi] = f.add(hess[pi], t);
        }
    }
    for pi in 0..3 {
        hess[pi] = f.mul(hess[pi], inv2);
    }
    (grad, hess)
}

pub fn make_fb_pt(f: &Fq, g: &[u64; 15], c: [u64; 3]) -> FbPt {
    let (grad, hess) = taylor_data(f, g, &c);
    FbPt { c, grad, hess }
}

/// One residual section of a line: the coefficients `(c1, c2, c3)` of `lambda mu (c1 l^2 +
/// c2 l m + c3 m^2)` in `G(lambda P1 + mu P2)`.
#[inline]
pub fn line_coeffs(f: &Fq, p1: &FbPt, p2: &FbPt) -> (u64, u64, u64) {
    let dot = |a: &[u64; 3], b: &[u64; 3]| {
        f.add(
            f.add(f.mul(a[0], b[0]), f.mul(a[1], b[1])),
            f.mul(a[2], b[2]),
        )
    };
    let c1 = dot(&p1.grad, &p2.c);
    let c3 = dot(&p2.grad, &p1.c);
    let v = &p2.c;
    let (x2, y2, z2) = (f.mul(v[0], v[0]), f.mul(v[1], v[1]), f.mul(v[2], v[2]));
    let (xy, xz, yz) = (f.mul(v[0], v[1]), f.mul(v[0], v[2]), f.mul(v[1], v[2]));
    let h = &p1.hess;
    let c2 = f.add(
        f.add(
            f.add(f.mul(h[0], x2), f.mul(h[1], y2)),
            f.add(f.mul(h[2], z2), f.mul(h[3], xy)),
        ),
        f.add(f.mul(h[4], xz), f.mul(h[5], yz)),
    );
    (c1, c2, c3)
}

/// The (up to two) rational residual points of the line through `P1`, `P2`, as `(lambda, mu)`
/// pairs in `lambda P1 + mu P2` (unnormalised). `None` when the residual does not split.
pub fn residual_roots(f: &Fq, c: (u64, u64, u64)) -> Option<[(u64, u64); 2]> {
    let (c1, c2, c3) = c;
    if c1 == 0 {
        // roots: (1:0) and the root of c2 l + c3 m = 0
        let other = if c2 == 0 { (1, 0) } else { (f.neg(c3), c2) };
        return Some([(1, 0), other]);
    }
    let disc = f.sub(f.mul(c2, c2), f.smul(4, f.mul(c1, c3)));
    let d = f.sqrt(disc)?;
    let two_c1 = f.add(c1, c1);
    let nc2 = f.neg(c2);
    Some([(f.add(nc2, d), two_c1), (f.sub(nc2, d), two_c1)])
}

#[inline]
fn comb(f: &Fq, l: u64, m: u64, p1: &[u64; 3], p2: &[u64; 3]) -> [u64; 3] {
    [
        f.add(f.mul(l, p1[0]), f.mul(m, p2[0])),
        f.add(f.mul(l, p1[1]), f.mul(m, p2[1])),
        f.add(f.mul(l, p1[2]), f.mul(m, p2[2])),
    ]
}

/// Solve `R = lambda P1 + mu P2` for (lambda, mu) (up to scale) from the coordinates alone.
fn recover_lm(f: &Fq, p1: &[u64; 3], p2: &[u64; 3], r: &[u64; 3]) -> Option<(u64, u64)> {
    for (a, b) in [(0usize, 1usize), (0, 2), (1, 2)] {
        let det = f.sub(f.mul(p1[a], p2[b]), f.mul(p1[b], p2[a]));
        if det != 0 {
            let l = f.sub(f.mul(r[a], p2[b]), f.mul(r[b], p2[a]));
            let m = f.sub(f.mul(p1[a], r[b]), f.mul(p1[b], r[a]));
            // check the remaining coordinate
            let c = 3 - a - b;
            let lhs = f.add(f.mul(l, p1[c]), f.mul(m, p2[c]));
            let rhs = f.mul(det, r[c]);
            if lhs != rhs {
                return None;
            }
            return Some((l, m));
        }
    }
    None
}

/// Independent verification of a line relation: the four points, with multiplicity, are
/// exactly the zero divisor of `G` restricted to the line through `P1`, `P2`.
/// `pts` are normalised coordinates. Returns true if verified.
pub fn verify_line(
    f: &Fq,
    g: &[u64; 15],
    p1: &[u64; 3],
    p2: &[u64; 3],
    pts: &[[u64; 3]; 4],
) -> bool {
    // binary quartic F(l, m) = sum c_k l^{4-k} m^k by evaluation at five points of the pencil
    let ev = |l: u64, m: u64| -> u64 {
        let pt = comb(f, l, m, p1, p2);
        eval_g(f, g, &pt)
    };
    // use (l, m) = (1, s) for s in {0, 1, -1, 2, -2}
    let ss = [0u64, 1, f.neg(1), 2, f.neg(2)];
    let vals: Vec<u64> = ss.iter().map(|&s| ev(1, s)).collect();
    // solve Vandermonde for c_0..c_4 (F(1, s) = sum c_k s^k) by Lagrange interpolation
    let mut coef = vec![0u64; 5];
    for i in 0..5 {
        // basis polynomial prod_{j != i} (s - s_j) / (s_i - s_j)
        let mut num = vec![1u64];
        let mut den = 1u64;
        for j in 0..5 {
            if j == i {
                continue;
            }
            num = pmul(f, &num, &[f.neg(ss[j]), 1]);
            den = f.mul(den, f.sub(ss[i], ss[j]));
        }
        let sc = f.mul(vals[i], f.inv(den));
        for (k, c) in num.iter().enumerate() {
            coef[k] = f.add(coef[k], f.mul(sc, *c));
        }
    }
    // F as a binary form; product of linear forms (mu_i l - lambda_i m) over the four points
    let mut prod = vec![1u64]; // polynomial in s (l = 1): (mu_i - lambda_i s) = mu_i - lambda_i s
    let mut deg_drop = 0usize; // points at s = infinity (mu_i = ... ) contribute degree loss handled below
    let mut scale_fix = 1u64;
    for r in pts.iter() {
        let (l, m) = match recover_lm(f, p1, p2, r) {
            Some(x) => x,
            None => return false,
        };
        // linear form in (1, s): m - ... Point (l : m) corresponds to s = m / l when l != 0.
        // factor: (l s - m)
        if l == 0 {
            // s = infinity: factor degenerates to constant m (degree drops by one)
            deg_drop += 1;
            scale_fix = f.mul(scale_fix, m);
        } else {
            prod = pmul(f, &prod, &[f.neg(m), l]);
        }
    }
    // F(1, s) must equal c * prod where deg F = 4 - deg_drop
    let mut fpoly = coef.clone();
    ptrim(&mut fpoly);
    let _ = scale_fix;
    if fpoly.len() != prod.len() || fpoly.len() + deg_drop != 5 {
        return false;
    }
    // proportionality: fpoly[i] * prod[0] == fpoly[0] * prod[i]
    if fpoly.is_empty() {
        return false;
    }
    for i in 0..fpoly.len() {
        if f.mul(fpoly[i], prod[0]) != f.mul(fpoly[0], prod[i]) {
            return false;
        }
    }
    // all points on C
    for r in pts.iter() {
        if eval_g(f, g, r) != 0 {
            return false;
        }
    }
    true
}

/// Fixed Feistel-based pseudo-random permutation of `[0, n)` (cycle walking), for sampling
/// line indices without replacement.
pub struct Perm {
    n: u64,
    bits: u32,
    keys: [u64; 4],
}

impl Perm {
    pub fn new(n: u64, rng: &mut SplitMix64) -> Perm {
        let mut bits = 2;
        while (1u64 << bits) < n {
            bits += 1;
        }
        if bits % 2 == 1 {
            bits += 1;
        }
        Perm {
            n,
            bits,
            keys: [
                rng.next_u64(),
                rng.next_u64(),
                rng.next_u64(),
                rng.next_u64(),
            ],
        }
    }
    fn enc(&self, x: u64) -> u64 {
        let h = self.bits / 2;
        let mask = (1u64 << h) - 1;
        let (mut l, mut r) = (x >> h, x & mask);
        for k in self.keys.iter() {
            let mut z = (r ^ k).wrapping_mul(0x9E37_79B9_7F4A_7C15);
            z ^= z >> 29;
            z = z.wrapping_mul(0xBF58_476D_1CE4_E5B9);
            z ^= z >> 32;
            let nl = r;
            let nr = l ^ (z & mask);
            l = nl;
            r = nr;
        }
        (l << h) | r
    }
    pub fn at(&self, i: u64) -> u64 {
        let mut x = self.enc(i);
        while x >= self.n {
            x = self.enc(x);
        }
        x
    }
}

/// Decode a triangular index into an unordered pair `i < j < f`.
pub fn pair_of_index(idx: u64, f: u64) -> (usize, usize) {
    // idx in [0, f(f-1)/2): row i has (f-1-i) entries
    // find largest i with i*(2f - i - 1)/2 <= idx
    let ff = f as f64;
    let mut i = ((2.0 * ff
        - 1.0
        - ((2.0 * ff - 1.0).powi(2) - 8.0 * idx as f64)
            .max(0.0)
            .sqrt())
        / 2.0) as u64;
    let start = |i: u64| i * (2 * f - i - 1) / 2;
    while i > 0 && start(i) > idx {
        i -= 1;
    }
    while start(i + 1) <= idx {
        i += 1;
    }
    let j = i + 1 + (idx - start(i));
    (i as usize, j as usize)
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Arm {
    Full,
    Slp,
    Dlp,
}

impl Arm {
    pub fn name(&self) -> &'static str {
        match self {
            Arm::Full => "FULL",
            Arm::Slp => "SLP",
            Arm::Dlp => "DLP",
        }
    }
    pub fn fb_size(&self, q: u64, kappa: f64) -> u64 {
        match self {
            Arm::Full => q + 1,
            Arm::Slp => ((kappa * (q as f64).powf(2.0 / 3.0)).ceil() as u64).min(q + 1),
            Arm::Dlp => ((kappa * (q as f64).sqrt()).ceil() as u64).min(q + 1),
        }
    }
}

/// One relation: `sum_fb c x_P + sum_lp c y_v - h = 0` (the `h` coefficient is `-1`).
#[derive(Clone, Debug)]
pub struct Rel {
    pub fb: Vec<(u32, i32)>,
    pub lp: Vec<(u32, i32)>,
    /// the two factor-base points (indices into the FB) that define the line
    pub line: (u32, u32),
}

/// Counters emitted by the relation phase (all arms).
#[derive(Clone, Debug, Default)]
pub struct IcCounters {
    pub lines: u64,
    pub split: u64,
    pub rel_full: u64,
    pub rel_slp: u64,
    pub rel_dlp: u64,
    pub dups: u64,
    pub verified: u64,
    pub verify_failed: u64,
    pub hash_lookups: u64,
    pub hash_inserts: u64,
    pub rng_draws: u64,
    pub uf_ops: u64,
    pub root_calls: u64,
    pub norm_calls: u64,
    pub fq_mul_collect: u64,
    pub fq_inv_collect: u64,
    pub fq_mul_verify: u64,
    pub fq_inv_verify: u64,
    pub fq_mul_fb: u64,
    pub fq_inv_fb: u64,
    // linear-algebra phase (mod-ell operations and bookkeeping)
    pub elim_ops: u64,
    pub elim_entries: u64,
    pub wied_ops: u64,
    pub bm_ops: u64,
    pub matvecs: u64,
}

/// Parity union-find over large-prime vertices; vertex 0 is the sink (the factor base).
/// Used only to decide when enough FB-only relations are obtainable (`E - V + B`); the
/// matrix itself is produced by the real elimination below.
pub struct LpGraph {
    parent: Vec<u32>,
    parity: Vec<u8>,
    sink: Vec<bool>,
    odd: Vec<bool>,
    pub edges: u64,
    pub verts: u64,
    pub bip: i64,
    pub ops: u64,
}

impl Default for LpGraph {
    fn default() -> Self {
        Self {
            parent: vec![0],
            parity: vec![0],
            sink: vec![true],
            odd: vec![false],
            edges: 0,
            verts: 0,
            bip: 0,
            ops: 0,
        }
    }
}

impl LpGraph {
    pub fn new() -> LpGraph {
        Self::default()
    }
    fn find(&mut self, mut v: u32) -> (u32, u8) {
        let mut path = vec![];
        let mut par = 0u8;
        while self.parent[v as usize] != v {
            path.push(v);
            par ^= self.parity[v as usize];
            v = self.parent[v as usize];
            self.ops += 1;
        }
        let mut acc = par;
        for &u in path.iter() {
            let pu = self.parity[u as usize];
            self.parent[u as usize] = v;
            self.parity[u as usize] = acc;
            acc ^= pu;
        }
        (v, par)
    }
    fn is_b(&self, r: u32) -> i64 {
        (!self.sink[r as usize] && !self.odd[r as usize]) as i64
    }
    fn ensure(&mut self, v: u32) {
        while self.parent.len() <= v as usize {
            let id = self.parent.len() as u32;
            self.parent.push(id);
            self.parity.push(0);
            self.sink.push(false);
            self.odd.push(false);
            self.verts += 1;
            self.bip += 1;
        }
    }
    pub fn add_edge(&mut self, a: u32, b: u32) {
        self.ensure(a.max(b));
        self.edges += 1;
        let (ra, pa) = self.find(a);
        let (rb, pb) = self.find(b);
        if ra == rb {
            if pa == pb && !self.odd[ra as usize] {
                self.bip -= self.is_b(ra);
                self.odd[ra as usize] = true;
            }
        } else {
            self.bip -= self.is_b(ra) + self.is_b(rb);
            self.parent[rb as usize] = ra;
            self.parity[rb as usize] = pa ^ pb ^ 1;
            self.sink[ra as usize] |= self.sink[rb as usize];
            self.odd[ra as usize] |= self.odd[rb as usize];
            self.bip += self.is_b(ra);
        }
    }
    /// Number of FB-only relations the large-prime part can yield: `E - V + B`.
    pub fn yield_count(&self) -> i64 {
        self.edges as i64 - self.verts as i64 + self.bip
    }
}

/// Build the factor base for an arm. FULL: all rational points (sorted by key). Reduced:
/// `size` uniform random rational points (with `W2 != 0`), deduplicated.
pub fn build_fb(
    inst: &Inst,
    arm: Arm,
    kappa: f64,
    rng: &mut SplitMix64,
    ctr: &mut IcCounters,
) -> Vec<FbPt> {
    let f = inst.f();
    let g = &inst.quartic;
    let size = arm.fb_size(inst.q, kappa) as usize;
    let mut pts: Vec<[u64; 3]>;
    if arm == Arm::Full {
        pts = enumerate_points(f, g);
        assert_eq!(pts.len() as u64, inst.q + 1, "N1 != q + 1");
        pts = pts.iter().map(|p| normalize_pt(f, p)).collect();
        pts.sort_by_key(pt_key);
    } else {
        let mut seen: FxSet<u64> = FxSet::default();
        pts = Vec::with_capacity(size);
        while pts.len() < size {
            let p = sample_point(f, g, rng);
            ctr.rng_draws += 1;
            ctr.hash_lookups += 1;
            let p = normalize_pt(f, &p);
            if seen.insert(pt_key(&p)) {
                ctr.hash_inserts += 1;
                pts.push(p);
            }
        }
    }
    // projective normalisation (first non-zero coordinate 1) so that `pt_key` identifies points
    pts.iter().map(|p| make_fb_pt(f, g, *p)).collect()
}

fn line_key(pts: &[[u64; 3]; 4]) -> u64 {
    let mut k: Vec<u64> = pts.iter().map(pt_key).collect();
    k.sort_unstable();
    let mut h = 0x9E37_79B9_7F4A_7C15u64;
    for x in k {
        h = (h.rotate_left(7) ^ x).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        h ^= h >> 29;
    }
    h
}

/// Resumable relation collector (one arm, one factor base).
pub struct Collector<'a> {
    pub inst: &'a Inst,
    pub arm: Arm,
    pub kappa: f64,
    pub fb: Vec<FbPt>,
    fb_index: FxMap<u64, u32>,
    lp_map: FxMap<u64, u32>,
    pub lp_pts: Vec<[u64; 3]>,
    pub graph: LpGraph,
    pub rels: Vec<Rel>,
    seen: FxSet<u64>,
    pub full_rels: u64,
    pub ctr: IcCounters,
    perm: Perm,
    next_idx: u64,
    npairs: u64,
    max_lp: usize,
    pub exhausted: bool,
}

impl<'a> Collector<'a> {
    pub fn new(inst: &'a Inst, arm: Arm, kappa: f64, seed: u64) -> Collector<'a> {
        let f = inst.f();
        let mut rng = SplitMix64::new(seed);
        let mut ctr = IcCounters::default();
        let (m0, i0) = f.counts();
        let fb = build_fb(inst, arm, kappa, &mut rng, &mut ctr);
        let (m1, i1) = f.counts();
        ctr.fq_mul_fb = m1 - m0;
        ctr.fq_inv_fb = i1 - i0;
        let nfb = fb.len() as u64;
        let mut fb_index: FxMap<u64, u32> = FxMap::default();
        for (i, p) in fb.iter().enumerate() {
            fb_index.insert(pt_key(&p.c), i as u32);
            ctr.hash_inserts += 1;
        }
        let npairs = nfb * (nfb - 1) / 2;
        ctr.rng_draws += 4;
        let perm = Perm::new(npairs, &mut rng);
        let max_lp = match arm {
            Arm::Full => 0,
            Arm::Slp => 1,
            Arm::Dlp => 2,
        };
        Collector {
            inst,
            arm,
            kappa,
            fb,
            fb_index,
            lp_map: FxMap::default(),
            lp_pts: vec![],
            graph: LpGraph::new(),
            rels: vec![],
            seen: FxSet::default(),
            full_rels: 0,
            ctr,
            perm,
            next_idx: 0,
            npairs,
            max_lp,
            exhausted: false,
        }
    }

    /// FB-only relations obtainable now: full relations plus the cyclomatic count.
    pub fn available(&self) -> i64 {
        self.full_rels as i64 + self.graph.yield_count().max(0)
    }

    /// Process lines until `available() >= target` (true) or the pairs are exhausted, the
    /// line budget is hit or the deadline passes (false).
    pub fn run_until(
        &mut self,
        target: i64,
        max_lines: u64,
        deadline: Option<std::time::Instant>,
    ) -> bool {
        let inst = self.inst;
        let f = inst.f();
        let g = inst.quartic;
        let nfb = self.fb.len();
        loop {
            if self.available() >= target {
                return true;
            }
            if self.next_idx >= self.npairs {
                self.exhausted = true;
                return false;
            }
            if self.ctr.lines >= max_lines {
                return false;
            }
            if self.ctr.lines.is_multiple_of(4096) {
                if let Some(d) = deadline {
                    if std::time::Instant::now() > d {
                        return false;
                    }
                }
            }
            let pidx = self.perm.at(self.next_idx);
            self.next_idx += 1;
            self.ctr.lines += 1;
            let (i, j) = pair_of_index(pidx, nfb as u64);
            let (mb, ib) = f.counts();
            let mut vm = 0u64;
            let mut vi = 0u64;
            self.process_line(i, j, &g, &mut vm, &mut vi);
            let (ma, ia) = f.counts();
            self.ctr.fq_mul_collect += (ma - mb) - vm;
            self.ctr.fq_inv_collect += (ia - ib) - vi;
        }
    }

    fn process_line(&mut self, i: usize, j: usize, g: &[u64; 15], vm: &mut u64, vi: &mut u64) {
        let f = self.inst.f();
        let c = line_coeffs(f, &self.fb[i], &self.fb[j]);
        self.ctr.root_calls += 1;
        let roots = match residual_roots(f, c) {
            Some(r) => r,
            None => return,
        };
        self.ctr.split += 1;
        let (p1, p2) = (self.fb[i].c, self.fb[j].c);
        let mut pts4: [[u64; 3]; 4] = [p1, p2, [0; 3], [0; 3]];
        for (k, &(l, m)) in roots.iter().enumerate() {
            let r = comb(f, l, m, &p1, &p2);
            self.ctr.norm_calls += 1;
            pts4[2 + k] = normalize_pt(f, &r);
        }
        let mut fbs: Vec<(u32, i32)> = vec![];
        let mut lps: Vec<(u64, i32, [u64; 3])> = vec![];
        let add_fb = |idx: u32, fbs: &mut Vec<(u32, i32)>| {
            if let Some(e) = fbs.iter_mut().find(|e| e.0 == idx) {
                e.1 += 1;
            } else {
                fbs.push((idx, 1));
            }
        };
        add_fb(i as u32, &mut fbs);
        add_fb(j as u32, &mut fbs);
        for k in 2..4 {
            let key = pt_key(&pts4[k]);
            self.ctr.hash_lookups += 1;
            if let Some(&idx) = self.fb_index.get(&key) {
                add_fb(idx, &mut fbs);
            } else if let Some(e) = lps.iter_mut().find(|e| e.0 == key) {
                e.1 += 1;
            } else {
                lps.push((key, 1, pts4[k]));
            }
        }
        if lps.len() > self.max_lp {
            return;
        }
        // duplicate lines (the same section reached from another pair of its points)
        let lk = line_key(&pts4);
        self.ctr.hash_lookups += 1;
        if self.seen.contains(&lk) {
            self.ctr.dups += 1;
            return;
        }
        // independent verification (cost recorded separately, excluded from the attack cost)
        let (mv0, iv0) = f.counts();
        let good = verify_line(f, g, &p1, &p2, &pts4);
        let (mv1, iv1) = f.counts();
        *vm = mv1 - mv0;
        *vi = iv1 - iv0;
        self.ctr.fq_mul_verify += *vm;
        self.ctr.fq_inv_verify += *vi;
        self.ctr.verified += 1;
        if !good {
            self.ctr.verify_failed += 1;
            return;
        }
        self.seen.insert(lk);
        self.ctr.hash_inserts += 1;
        let mut lpv: Vec<(u32, i32)> = vec![];
        for (key, cf, pt) in lps.iter() {
            self.ctr.hash_lookups += 1;
            let id = match self.lp_map.get(key) {
                Some(&id) => id,
                None => {
                    let id = self.lp_pts.len() as u32 + 1;
                    self.lp_map.insert(*key, id);
                    self.lp_pts.push(*pt);
                    self.ctr.hash_inserts += 1;
                    id
                }
            };
            lpv.push((id, *cf));
        }
        match lpv.len() {
            0 => {
                self.full_rels += 1;
                self.ctr.rel_full += 1;
            }
            1 => {
                self.graph.add_edge(lpv[0].0, 0);
                self.ctr.rel_slp += 1;
            }
            _ => {
                self.graph.add_edge(lpv[0].0, lpv[1].0);
                self.ctr.rel_dlp += 1;
            }
        }
        self.rels.push(Rel {
            fb: fbs,
            lp: lpv,
            line: (i as u32, j as u32),
        });
    }

    pub fn finish_counters(&mut self) {
        self.ctr.uf_ops = self.graph.ops + self.graph.edges;
    }
}

// ---------------------------------------------------------------------------
// 4. sparse structured elimination and Wiedemann mod ell
// ---------------------------------------------------------------------------

/// Sparse row: `(column, value in Montgomery form)` sorted by column.
pub type SRow = Vec<(u32, u64)>;

/// Matrix rows from relations. Column 0 is the unknown `h` (coefficient `-1`), FB point
/// `i >= 1` is column `i` (`x_{P0} = 0` is dropped), large prime `id >= 1` is column `nfb + id`.
pub fn build_rows(mont: &Mont, nfb: usize, rels: &[Rel]) -> Vec<SRow> {
    rels.iter()
        .map(|r| {
            let mut row: SRow = vec![(0, mont.from_i(-1))];
            for &(idx, c) in &r.fb {
                if idx != 0 {
                    row.push((idx, mont.from_i(c as i64)));
                }
            }
            for &(id, c) in &r.lp {
                row.push((nfb as u32 + id, mont.from_i(c as i64)));
            }
            row.sort_unstable_by_key(|e| e.0);
            row
        })
        .collect()
}

/// `a - f * b` for sparse rows, counting one mod-ell operation per entry of `b`.
fn axpy_sub(mont: &Mont, a: &SRow, f: u64, b: &SRow, ops: &mut u64) -> SRow {
    let mut out = Vec::with_capacity(a.len() + b.len());
    let (mut i, mut j) = (0, 0);
    while i < a.len() || j < b.len() {
        if j >= b.len() || (i < a.len() && a[i].0 < b[j].0) {
            out.push(a[i]);
            i += 1;
        } else if i >= a.len() || b[j].0 < a[i].0 {
            *ops += 1;
            out.push((b[j].0, mont.neg(mont.mul(f, b[j].1))));
            j += 1;
        } else {
            *ops += 1;
            let v = mont.sub(a[i].1, mont.mul(f, b[j].1));
            if v != 0 {
                out.push((a[i].0, v));
            }
            i += 1;
            j += 1;
        }
    }
    out
}

fn row_coef(row: &SRow, c: u32) -> u64 {
    match row.binary_search_by_key(&c, |e| e.0) {
        Ok(p) => row[p].1,
        Err(_) => 0,
    }
}

/// Eliminate every large-prime column (columns `>= nfb`) by minimum-weight pivoting
/// (weight 1: row dropped; weight 2: the two rows merged; general weight: Markowitz-style
/// pivot on the shortest row). Returns FB-only rows. All mod-ell work is counted in
/// `ops` / `entries`.
pub fn eliminate_lp(
    mont: &Mont,
    nfb: usize,
    rows_in: Vec<SRow>,
    ops: &mut u64,
    entries: &mut u64,
) -> Vec<SRow> {
    use std::cmp::Reverse;
    let mut rows: Vec<Option<SRow>> = rows_in.into_iter().map(Some).collect();
    let mut colset: FxMap<u32, FxSet<u32>> = FxMap::default();
    for (r, row) in rows.iter().enumerate() {
        for &(c, _) in row.as_ref().unwrap() {
            if c as usize >= nfb {
                colset.entry(c).or_default().insert(r as u32);
                *entries += 1;
            }
        }
    }
    let mut heap: BinaryHeap<Reverse<(usize, u32)>> =
        colset.iter().map(|(&c, s)| Reverse((s.len(), c))).collect();
    while let Some(Reverse((w, c))) = heap.pop() {
        let cur = colset.get(&c).map(|s| s.len()).unwrap_or(0);
        if cur == 0 {
            colset.remove(&c);
            continue;
        }
        if cur != w {
            heap.push(Reverse((cur, c)));
            continue;
        }
        let pr = *colset[&c]
            .iter()
            .min_by_key(|&&r| (rows[r as usize].as_ref().unwrap().len(), r))
            .unwrap();
        let mut prow = rows[pr as usize].take().unwrap();
        for &(cc, _) in &prow {
            if cc as usize >= nfb {
                colset.get_mut(&cc).unwrap().remove(&pr);
            }
        }
        let pc = row_coef(&prow, c);
        let inv = mont.inv(pc);
        *ops += 128; // Fermat inversion: ~ 2 log2(ell) multiplications
        for e in prow.iter_mut() {
            e.1 = mont.mul(e.1, inv);
        }
        *ops += prow.len() as u64;
        let mut others: Vec<u32> = colset
            .get(&c)
            .map(|s| s.iter().cloned().collect())
            .unwrap_or_default();
        others.sort_unstable();
        for r in others {
            let row = rows[r as usize].take().unwrap();
            let fct = row_coef(&row, c);
            let newrow = axpy_sub(mont, &row, fct, &prow, ops);
            *entries += (row.len() + prow.len()) as u64;
            // update column sets
            for &(cc, _) in &row {
                if cc as usize >= nfb && newrow.binary_search_by_key(&cc, |e| e.0).is_err() {
                    let s = colset.get_mut(&cc).unwrap();
                    s.remove(&r);
                    if cc != c {
                        heap.push(Reverse((s.len(), cc)));
                    }
                }
            }
            for &(cc, _) in &newrow {
                if cc as usize >= nfb && row.binary_search_by_key(&cc, |e| e.0).is_err() {
                    let s = colset.entry(cc).or_default();
                    s.insert(r);
                    heap.push(Reverse((s.len(), cc)));
                }
            }
            rows[r as usize] = Some(newrow);
        }
        colset.remove(&c);
    }
    rows.into_iter()
        .flatten()
        .filter(|r| !r.is_empty())
        .collect()
}

/// Dense rank of the rows over `F_ell` (cross-check only; not part of any attack cost).
pub fn dense_rank(mont: &Mont, rows: &[SRow], ncols: usize) -> usize {
    let mut m: Vec<Vec<u64>> = rows
        .iter()
        .map(|r| {
            let mut d = vec![0u64; ncols];
            for &(c, v) in r {
                d[c as usize] = v;
            }
            d
        })
        .collect();
    let mut rank = 0;
    for col in 0..ncols {
        let mut piv = None;
        for r in rank..m.len() {
            if m[r][col] != 0 {
                piv = Some(r);
                break;
            }
        }
        let Some(p) = piv else { continue };
        m.swap(rank, p);
        let inv = mont.inv(m[rank][col]);
        for c in col..ncols {
            m[rank][c] = mont.mul(m[rank][c], inv);
        }
        let prow = m[rank].clone();
        for r in (rank + 1)..m.len() {
            let f = m[r][col];
            if f != 0 {
                for c in col..ncols {
                    if prow[c] != 0 {
                        m[r][c] = mont.sub(m[r][c], mont.mul(f, prow[c]));
                    }
                }
            }
        }
        rank += 1;
        if rank == m.len() {
            break;
        }
    }
    rank
}

/// Berlekamp-Massey; returns the connection polynomial `C` (`C[0] = 1`) and its length `L`.
pub fn berlekamp_massey(mont: &Mont, s: &[u64], ops: &mut u64) -> (Vec<u64>, usize) {
    let one = mont.one;
    let mut c = vec![one];
    let mut b = vec![one];
    let (mut l, mut m) = (0usize, 1usize);
    let mut binv = one;
    for i in 0..s.len() {
        let mut d = s[i];
        let top = l.min(c.len() - 1);
        for j in 1..=top {
            d = mont.add(d, mont.mul(c[j], s[i - j]));
        }
        *ops += top as u64;
        if d == 0 {
            m += 1;
            continue;
        }
        let coef = mont.mul(d, binv);
        let t = if 2 * l <= i { Some(c.clone()) } else { None };
        if c.len() < b.len() + m {
            c.resize(b.len() + m, 0);
        }
        for j in 0..b.len() {
            c[j + m] = mont.sub(c[j + m], mont.mul(coef, b[j]));
        }
        *ops += b.len() as u64;
        if let Some(tc) = t {
            l = i + 1 - l;
            b = tc;
            binv = mont.inv(d);
            *ops += 128;
            m = 1;
        } else {
            m += 1;
        }
    }
    c.resize(l + 1, 0);
    (c, l)
}

pub struct LaResult {
    pub ok: bool,
    pub fail: &'static str,
    /// `v[0] = 1` (the `h` unknown), `v[i]` the log of `[P_i - P_0]` in units of `h`, plain residues.
    pub v: Vec<u64>,
    pub wied_ops: u64,
    pub bm_ops: u64,
    pub matvecs: u64,
    pub deg: usize,
    pub rows_used: usize,
    pub holdout: usize,
    pub holdout_ok: bool,
}

/// Solve `A v = 0` with `v[0] = 1` by Wiedemann on `M = A'^T D A'` (`A'` = `A` without column 0).
/// The last `holdout` rows are not used in the solve and checked afterwards, as are all rows.
pub fn wiedemann_solve(
    mont: &Mont,
    rows: &[SRow],
    ncols: usize,
    holdout: usize,
    seed: u64,
    deadline: Option<std::time::Instant>,
) -> LaResult {
    let mut res = LaResult {
        ok: false,
        fail: "",
        v: vec![],
        wied_ops: 0,
        bm_ops: 0,
        matvecs: 0,
        deg: 0,
        rows_used: 0,
        holdout,
        holdout_ok: false,
    };
    let nc = ncols - 1;
    if rows.len() < holdout + nc {
        res.fail = "too_few_rows";
        return res;
    }
    let m = rows.len() - holdout;
    res.rows_used = m;
    let mut rng = SplitMix64::new(seed);
    // CSR of A' (columns shifted by one) and the right-hand side r = -A[:, 0]
    let mut ptr = vec![0usize; m + 1];
    let mut cols: Vec<u32> = vec![];
    let mut vals: Vec<u64> = vec![];
    let mut rhs_r = vec![0u64; m];
    for (r, row) in rows[..m].iter().enumerate() {
        for &(c, v) in row {
            if c == 0 {
                rhs_r[r] = mont.neg(v);
            } else {
                cols.push(c - 1);
                vals.push(v);
            }
        }
        ptr[r + 1] = cols.len();
    }
    let nnz = cols.len() as u64;
    let diag: Vec<u64> = (0..m).map(|_| mont.to(1 + rng.below(mont.n - 1))).collect();
    let mut ops = 0u64;
    let mut mv = 0u64;
    let mut tmp = vec![0u64; m];
    let matvec =
        |x: &[u64], out: &mut Vec<u64>, tmp: &mut Vec<u64>, ops: &mut u64, mv: &mut u64| {
            for r in 0..m {
                let mut acc = 0u64;
                for p in ptr[r]..ptr[r + 1] {
                    acc = mont.add(acc, mont.mul(vals[p], x[cols[p] as usize]));
                }
                tmp[r] = mont.mul(acc, diag[r]);
            }
            for o in out.iter_mut() {
                *o = 0;
            }
            for r in 0..m {
                let t = tmp[r];
                if t == 0 {
                    continue;
                }
                for p in ptr[r]..ptr[r + 1] {
                    let c = cols[p] as usize;
                    out[c] = mont.add(out[c], mont.mul(vals[p], t));
                }
            }
            *ops += 2 * nnz + m as u64;
            *mv += 1;
        };
    // b = A'^T D r
    let mut b = vec![0u64; nc];
    for r in 0..m {
        let t = mont.mul(rhs_r[r], diag[r]);
        if t == 0 {
            continue;
        }
        for p in ptr[r]..ptr[r + 1] {
            let c = cols[p] as usize;
            b[c] = mont.add(b[c], mont.mul(vals[p], t));
        }
    }
    ops += nnz + m as u64;
    let u: Vec<u64> = (0..nc).map(|_| mont.to(rng.below(mont.n))).collect();
    let mut seq = Vec::with_capacity(2 * nc);
    let mut cur = b.clone();
    let mut nxt = vec![0u64; nc];
    for _ in 0..2 * nc {
        let mut d = 0u64;
        for i in 0..nc {
            d = mont.add(d, mont.mul(u[i], cur[i]));
        }
        ops += nc as u64;
        seq.push(d);
        matvec(&cur, &mut nxt, &mut tmp, &mut ops, &mut mv);
        std::mem::swap(&mut cur, &mut nxt);
        if let Some(dl) = deadline {
            if mv.is_multiple_of(64) && std::time::Instant::now() > dl {
                res.fail = "timeout";
                res.wied_ops = ops;
                res.matvecs = mv;
                return res;
            }
        }
    }
    let mut bm_ops = 0u64;
    let (cpoly, l) = berlekamp_massey(mont, &seq, &mut bm_ops);
    res.bm_ops = bm_ops;
    res.deg = l;
    // f_j = C[L - j]
    let f0 = cpoly[l];
    if l == 0 || f0 == 0 {
        res.fail = "minpoly_zero_constant";
        res.wied_ops = ops;
        res.matvecs = mv;
        return res;
    }
    // w = -f0^{-1} sum_{j=1}^{L} f_j M^{j-1} b
    let mut acc = vec![0u64; nc];
    let mut cur = b.clone();
    for j in 1..=l {
        let fj = cpoly[l - j];
        if fj != 0 {
            for i in 0..nc {
                acc[i] = mont.add(acc[i], mont.mul(fj, cur[i]));
            }
            ops += nc as u64;
        }
        if j < l {
            matvec(&cur, &mut nxt, &mut tmp, &mut ops, &mut mv);
            std::mem::swap(&mut cur, &mut nxt);
        }
        if let Some(dl) = deadline {
            if mv.is_multiple_of(64) && std::time::Instant::now() > dl {
                res.fail = "timeout";
                res.wied_ops = ops;
                res.matvecs = mv;
                return res;
            }
        }
    }
    let sc = mont.neg(mont.inv(f0));
    for i in 0..nc {
        acc[i] = mont.mul(acc[i], sc);
    }
    ops += nc as u64;
    // verify on all rows (used and held out)
    let mut v = vec![0u64; ncols];
    v[0] = mont.one;
    v[1..].copy_from_slice(&acc);
    let mut all_ok = true;
    let mut hold_ok = true;
    for (r, row) in rows.iter().enumerate() {
        let mut s = 0u64;
        for &(c, val) in row {
            s = mont.add(s, mont.mul(val, v[c as usize]));
        }
        ops += row.len() as u64;
        if s != 0 {
            all_ok = false;
            if r >= m {
                hold_ok = false;
            }
        }
    }
    res.wied_ops = ops;
    res.matvecs = mv;
    res.holdout_ok = hold_ok;
    res.ok = all_ok;
    if !all_ok {
        res.fail = "verification_failed";
    }
    res.v = v.iter().map(|&x| mont.from(x)).collect();
    res
}

// ---------------------------------------------------------------------------
// 5. rho on E0(K)
// ---------------------------------------------------------------------------

/// `K` arithmetic with the same operation tallies as `Kf` (13 `F_q` products per `K` product,
/// 6 per Frobenius, one counted inversion per `K` inversion) but without per-operation cell
/// traffic: tallies are plain integer increments. Equivalence with `Kf` (results and tallies)
/// is unit-tested.
pub struct KFast {
    pub q: u64,
    a: u64,
    b: u64,
    gq: K,
    gq2: K,
    pub fqm: Cell<u64>,
    pub fqi: Cell<u64>,
}

impl KFast {
    pub fn new(kf: &Kf) -> KFast {
        KFast {
            q: kf.q(),
            a: kf.a,
            b: kf.b,
            gq: kf.gq,
            gq2: kf.gq2,
            fqm: Cell::new(0),
            fqi: Cell::new(0),
        }
    }
    #[inline]
    pub fn add(&self, x: &K, y: &K) -> K {
        let q = self.q;
        let r = |a: u64, b: u64| {
            let s = a + b;
            if s >= q {
                s - q
            } else {
                s
            }
        };
        [r(x[0], y[0]), r(x[1], y[1]), r(x[2], y[2])]
    }
    #[inline]
    pub fn sub(&self, x: &K, y: &K) -> K {
        let q = self.q;
        let r = |a: u64, b: u64| if a >= b { a - b } else { a + q - b };
        [r(x[0], y[0]), r(x[1], y[1]), r(x[2], y[2])]
    }
    #[inline]
    pub fn mul(&self, x: &K, y: &K) -> K {
        self.fqm.set(self.fqm.get() + 13);
        let q = self.q;
        let c0 = x[0] * y[0];
        let c1 = x[0] * y[1] + x[1] * y[0];
        let c2 = x[0] * y[2] + x[1] * y[1] + x[2] * y[0];
        let c3 = (x[1] * y[2] + x[2] * y[1]) % q;
        let c4 = (x[2] * y[2]) % q;
        // g^3 = -a g - b, g^4 = -a g^2 - b g
        let nb = q - self.b;
        let na = q - self.a;
        [
            (c0 + nb * c3) % q,
            (c1 + na * c3 + nb * c4) % q,
            (c2 + na * c4) % q,
        ]
    }
    #[inline]
    fn scale(&self, x: &K, c: u64) -> K {
        self.fqm.set(self.fqm.get() + 3);
        [x[0] * c % self.q, x[1] * c % self.q, x[2] * c % self.q]
    }
    fn frob(&self, x: &K) -> K {
        let t1 = self.scale(&self.gq, x[1]);
        let t2 = self.scale(&self.gq2, x[2]);
        let s = self.add(&t1, &t2);
        [(s[0] + x[0]) % self.q, s[1], s[2]]
    }
    fn fq_inv(&self, a: u64) -> u64 {
        self.fqi.set(self.fqi.get() + 1);
        let (mut t, mut newt) = (0i64, 1i64);
        let (mut r, mut newr) = (self.q as i64, a as i64);
        while newr != 0 {
            let qt = r / newr;
            let tmp = t - qt * newt;
            t = newt;
            newt = tmp;
            let tmp = r - qt * newr;
            r = newr;
            newr = tmp;
        }
        t.rem_euclid(self.q as i64) as u64
    }
    pub fn inv(&self, x: &K) -> K {
        let x1 = self.frob(x);
        let x2 = self.frob(&x1);
        let t = self.mul(&x1, &x2);
        let n = self.mul(x, &t);
        let ni = self.fq_inv(n[0]);
        self.scale(&t, ni)
    }
}

#[inline]
fn kmix(x: &K) -> u64 {
    let mut h = x[0].wrapping_mul(0x9E37_79B9_7F4A_7C15)
        ^ x[1].wrapping_mul(0xBF58_476D_1CE4_E5B9).rotate_left(21)
        ^ x[2].wrapping_mul(0x94D0_49BB_1331_11EB).rotate_left(42);
    h ^= h >> 31;
    h = h.wrapping_mul(0xD6E8_FEB8_6659_FD93);
    h ^= h >> 32;
    h
}

#[derive(Clone, Debug, Default)]
pub struct RhoOut {
    pub ok: bool,
    pub verified: bool,
    pub timeout: bool,
    pub steps: u64,
    pub dps: u64,
    pub dp_lookups: u64,
    pub dp_inserts: u64,
    pub dp_checks: u64,
    pub part_hashes: u64,
    pub rng_draws: u64,
    pub modl_adds: u64,
    pub canon: u64,
    pub restarts: u64,
    pub fallbacks: u64,
    pub fq_mul: u64,
    pub fq_inv: u64,
    pub setup_fq_mul: u64,
    pub setup_fq_inv: u64,
    pub restart_fq_mul: u64,
    pub restart_fq_inv: u64,
    pub d: u32,
    pub m: usize,
    pub r: usize,
    pub wall_s: f64,
}

pub const RHO_R: usize = 32;
pub const RHO_M: usize = 64;

/// `a G0 + b Q` by double-and-add through the counted `Kf` arithmetic.
fn lin_comb(inst: &Inst, g0: &EPt, qq: &EPt, a: u64, b: u64) -> EPt {
    let x = inst.e_mul(g0, a as u128);
    let y = inst.e_mul(qq, b as u128);
    inst.e_add(&x, &y)
}

/// Pollard rho (r-adding walk, `m` lock-step walkers, Montgomery batch inversion in `K`,
/// distinguished points, no negation map) for `Q = s G0` in the order-`ell` subgroup.
pub fn rho_run(inst: &Inst, seed: u64, deadline: Option<std::time::Instant>) -> RhoOut {
    let t0 = std::time::Instant::now();
    let ell = inst.ell;
    let mut out = RhoOut {
        m: RHO_M,
        r: RHO_R,
        ..Default::default()
    };
    let mut rng = SplitMix64::new(seed ^ 0x52_48_4F_00_00_00_00_00);
    let f = inst.f();
    let (sm0, si0) = f.counts();
    // generator and target
    let g0 = loop {
        out.rng_draws += 1;
        let p = inst.e_random_point(&mut rng);
        let g = inst.e_mul(&p, inst.h as u128);
        if g.is_some() {
            break g;
        }
    };
    let s = 1 + rng.below(ell - 1);
    out.rng_draws += 1;
    let qq = inst.e_mul(&g0, s as u128);
    // multipliers
    let mut mult: Vec<(K, K, u64, u64)> = vec![];
    while mult.len() < RHO_R {
        let (mj, nj) = (rng.below(ell), rng.below(ell));
        out.rng_draws += 2;
        if let Some((x, y)) = lin_comb(inst, &g0, &qq, mj, nj) {
            mult.push((x, y, mj, nj));
        }
    }
    let rd = (isqrt_u128(ell as u128).max(1) as f64).log2().floor() as i64 - 10;
    let d = rd.max(0) as u32;
    out.d = d;
    let mask = (1u64 << d) - 1;
    let nw = RHO_M;
    let mut px: Vec<K> = vec![[0; 3]; nw];
    let mut py: Vec<K> = vec![[0; 3]; nw];
    let mut wa = vec![0u64; nw];
    let mut wb = vec![0u64; nw];
    let start_walker = |i: usize,
                        rng: &mut SplitMix64,
                        px: &mut Vec<K>,
                        py: &mut Vec<K>,
                        wa: &mut Vec<u64>,
                        wb: &mut Vec<u64>,
                        out: &mut RhoOut| {
        loop {
            let (a, b) = (rng.below(ell), rng.below(ell));
            out.rng_draws += 2;
            if let Some((x, y)) = lin_comb(inst, &g0, &qq, a, b) {
                px[i] = x;
                py[i] = y;
                wa[i] = a;
                wb[i] = b;
                return;
            }
        }
    };
    for i in 0..nw {
        start_walker(i, &mut rng, &mut px, &mut py, &mut wa, &mut wb, &mut out);
    }
    let (sm1, si1) = f.counts();
    out.setup_fq_mul = sm1 - sm0;
    out.setup_fq_inv = si1 - si0;
    let kf = KFast::new(&inst.kf);
    let mut table: FxMap<[u32; 6], (u64, u64)> = FxMap::default();
    let cap = 60 * (isqrt_u128(ell as u128) as u64 + 1) + 200_000;
    let mut hs: Vec<u64> = px.iter().map(kmix).collect();
    out.part_hashes += nw as u64;
    let one: K = [1, 0, 0];
    let mut pre: Vec<K> = vec![one; nw];
    let mut den: Vec<K> = vec![one; nw];
    let mut jsel = vec![0usize; nw];
    let mut special = vec![false; nw];
    loop {
        if out.steps >= cap {
            break;
        }
        if out.steps % (1 << 16) < nw as u64 {
            if let Some(dl) = deadline {
                if std::time::Instant::now() > dl {
                    out.timeout = true;
                    break;
                }
            }
        }
        // partition and denominators
        let mut run = one;
        for i in 0..nw {
            let j = ((hs[i] >> 40) as usize) % RHO_R;
            jsel[i] = j;
            let dd = kf.sub(&mult[j].0, &px[i]);
            special[i] = dd == [0; 3];
            den[i] = if special[i] { one } else { dd };
            pre[i] = run;
            run = kf.mul(&run, &den[i]);
        }
        // run = product of all den; invert once, sweep back
        let mut inv_run = kf.inv(&run);
        for i in (0..nw).rev() {
            let inv_i = kf.mul(&inv_run, &pre[i]);
            inv_run = kf.mul(&inv_run, &den[i]);
            let j = jsel[i];
            let (mx, my, mj, nj) = &mult[j];
            if special[i] {
                out.fallbacks += 1;
                let cur: EPt = Some((px[i], py[i]));
                let nw_pt = inst.e_add(&cur, &Some((*mx, *my)));
                match nw_pt {
                    Some((x, y)) => {
                        px[i] = x;
                        py[i] = y;
                    }
                    None => {
                        out.restarts += 1;
                        start_walker(i, &mut rng, &mut px, &mut py, &mut wa, &mut wb, &mut out);
                    }
                }
            } else {
                let lam = kf.mul(&kf.sub(my, &py[i]), &inv_i);
                let x3 = kf.sub(&kf.sub(&kf.mul(&lam, &lam), &px[i]), mx);
                let y3 = kf.sub(&kf.mul(&lam, &kf.sub(&px[i], &x3)), &py[i]);
                px[i] = x3;
                py[i] = y3;
            }
            wa[i] = {
                let t = wa[i] + mj;
                if t >= ell {
                    t - ell
                } else {
                    t
                }
            };
            wb[i] = {
                let t = wb[i] + nj;
                if t >= ell {
                    t - ell
                } else {
                    t
                }
            };
        }
        out.steps += nw as u64;
        out.modl_adds += 2 * nw as u64;
        // new hashes, distinguished-point checks
        for i in 0..nw {
            hs[i] = kmix(&px[i]);
            out.part_hashes += 1;
            out.dp_checks += 1;
            if hs[i] & mask == 0 {
                out.dps += 1;
                let key = [
                    px[i][0] as u32,
                    px[i][1] as u32,
                    px[i][2] as u32,
                    py[i][0] as u32,
                    py[i][1] as u32,
                    py[i][2] as u32,
                ];
                out.dp_lookups += 1;
                let mut solved = None;
                let mut solved_none_cycle = false;
                if let Some(&(a2, b2)) = table.get(&key) {
                    if (a2, b2) == (wa[i], wb[i]) {
                        solved_none_cycle = true;
                    }
                    if (a2, b2) != (wa[i], wb[i]) && b2 != wb[i] {
                        // a + b s = a2 + b2 s  =>  s = (a - a2) / (b2 - b)
                        let mt = Mont::new(ell);
                        let num = mt.sub(mt.to(wa[i]), mt.to(a2));
                        let dn = mt.sub(mt.to(b2), mt.to(wb[i]));
                        solved = Some(mt.from(mt.mul(num, mt.inv(dn))));
                    }
                } else {
                    table.insert(key, (wa[i], wb[i]));
                    out.dp_inserts += 1;
                }
                if let Some(sc) = solved {
                    out.ok = true;
                    out.verified = inst.e_mul(&g0, sc as u128) == qq && sc == s;
                    // the verified solution must equal the planted scalar
                    out.fq_mul = kf.fqm.get();
                    out.fq_inv = kf.fqi.get();
                    out.wall_s = t0.elapsed().as_secs_f64();
                    return out;
                }
                // walkers continue after a distinguished point; one that reproduces an
                // already stored (a, b) is on a cycle and is restarted at a fresh point
                if table.get(&key) == Some(&(wa[i], wb[i])) && solved_none_cycle {
                    out.restarts += 1;
                    let (rm0, ri0) = f.counts();
                    start_walker(i, &mut rng, &mut px, &mut py, &mut wa, &mut wb, &mut out);
                    let (rm1, ri1) = f.counts();
                    out.restart_fq_mul += rm1 - rm0;
                    out.restart_fq_inv += ri1 - ri0;
                    hs[i] = kmix(&px[i]);
                }
            }
        }
    }
    out.fq_mul = kf.fqm.get();
    out.fq_inv = kf.fqi.get();
    out.wall_s = t0.elapsed().as_secs_f64();
    out
}

/// Measured multiplication-equivalent of one `F_q` inversion (extended Euclid vs `a*b % q`),
/// dependent chains, `samples` each; median of 5 repeats.
pub fn measure_rho_inv(q: u64, samples: u64) -> f64 {
    let f = Fq::new(q);
    let mut ratios = vec![];
    for rep in 0..5u64 {
        let mut x = 12345 + rep;
        let t = std::time::Instant::now();
        for _ in 0..samples {
            x = (x * (x | 1) + 7) % q;
        }
        let tm = t.elapsed().as_secs_f64();
        let t = std::time::Instant::now();
        let mut y = 12345 + rep;
        for _ in 0..samples {
            y = f.inv(y % (q - 1) + 1) + 1;
        }
        let ti = t.elapsed().as_secs_f64();
        std::hint::black_box((x, y));
        ratios.push(ti / tm);
    }
    ratios.sort_by(|a, b| a.partial_cmp(b).unwrap());
    ratios[2]
}

// ---------------------------------------------------------------------------
// 6. cells: relation phase + linear algebra + verification (the measurement unit)
// ---------------------------------------------------------------------------

/// Tiny JSON-object builder (numbers via `Display`, strings escaped minimally).
pub struct J(pub String);
impl Default for J {
    fn default() -> Self {
        Self(String::from("{"))
    }
}

impl J {
    pub fn new() -> J {
        Self::default()
    }
    fn sep(&mut self) {
        if self.0.len() > 1 {
            self.0.push(',');
        }
    }
    pub fn n<T: std::fmt::Display>(&mut self, k: &str, v: T) -> &mut J {
        self.sep();
        let s = format!("{}", v);
        let s = if s == "NaN" || s == "inf" || s == "-inf" {
            "null".to_string()
        } else {
            s
        };
        self.0.push_str(&format!("\"{}\":{}", k, s));
        self
    }
    pub fn s(&mut self, k: &str, v: &str) -> &mut J {
        self.sep();
        self.0.push_str(&format!(
            "\"{}\":\"{}\"",
            k,
            v.replace('\\', "\\\\").replace('"', "\\\"")
        ));
        self
    }
    pub fn raw(&mut self, k: &str, v: &str) -> &mut J {
        self.sep();
        self.0.push_str(&format!("\"{}\":{}", k, v));
        self
    }
    pub fn done(&self) -> String {
        format!("{}}}", self.0)
    }
}

/// Pushforward of a relation: `sum cnt * pi0(point)` in `E0(K)`. `None` if some point is
/// not on the cover.
pub fn pushforward_sum(inst: &Inst, col: &Collector, rel: &Rel) -> Option<EPt> {
    let mut acc: EPt = None;
    for &(idx, c) in &rel.fb {
        let p = inst.pi0(&col.fb[idx as usize].c)?;
        acc = inst.e_add(&acc, &inst.e_mul(&p, c as u128));
    }
    for &(id, c) in &rel.lp {
        let p = inst.pi0(&col.lp_pts[id as usize - 1])?;
        acc = inst.e_add(&acc, &inst.e_mul(&p, c as u128));
    }
    Some(acc)
}

#[derive(Clone, Debug, Default)]
pub struct IcCell {
    pub k: u32,
    pub idx: u32,
    pub arm: &'static str,
    pub kappa: f64,
    pub q: u64,
    pub ell: u64,
    pub h: u64,
    pub nfb: usize,
    pub ncols: usize,
    pub status: String,
    pub rounds: u32,
    pub target_final: i64,
    pub rows_collected: usize,
    pub rows_after_elim: usize,
    pub ctr: IcCounters,
    pub rel_wall_s: f64,
    pub la_wall_s: f64,
    pub la_ok: bool,
    pub la_fail: String,
    pub la_deg: usize,
    pub holdout: usize,
    pub holdout_ok: bool,
    pub coverage: bool,
    pub cross_pairs: u32,
    pub cross_ok: u32,
    pub push_checked: u64,
    pub push_fail: u64,
    pub rank_profile: Vec<(f64, usize, usize, usize)>,
    pub v: Vec<u64>,
}

impl IcCell {
    /// Attack cost in `F_q`-multiplication equivalents with inversion price `rinv` and
    /// mod-ell weight `w_ell`: relation phase (incl. FB construction, excl. verification) +
    /// linear algebra.
    pub fn cost_rel(&self, rinv: f64) -> f64 {
        (self.ctr.fq_mul_collect + self.ctr.fq_mul_fb) as f64
            + rinv * (self.ctr.fq_inv_collect + self.ctr.fq_inv_fb) as f64
    }
    pub fn lops(&self) -> u64 {
        self.ctr.elim_ops + self.ctr.wied_ops + self.ctr.bm_ops
    }
    pub fn to_json(&self) -> String {
        let c = &self.ctr;
        let mut j = J::new();
        j.n("k", self.k)
            .n("idx", self.idx)
            .s("arm", self.arm)
            .n("kappa", self.kappa)
            .n("q", self.q)
            .n("ell", self.ell)
            .n("h", self.h);
        j.n("nfb", self.nfb)
            .n("ncols", self.ncols)
            .s("status", &self.status)
            .n("rounds", self.rounds)
            .n("target_final", self.target_final);
        j.n("rows_collected", self.rows_collected)
            .n("rows_after_elim", self.rows_after_elim);
        j.n("lines", c.lines)
            .n("split", c.split)
            .n("rel_full", c.rel_full)
            .n("rel_slp", c.rel_slp)
            .n("rel_dlp", c.rel_dlp)
            .n("dups", c.dups);
        j.n("verified", c.verified)
            .n("verify_failed", c.verify_failed);
        j.n("fq_mul_collect", c.fq_mul_collect)
            .n("fq_inv_collect", c.fq_inv_collect)
            .n("fq_mul_fb", c.fq_mul_fb)
            .n("fq_inv_fb", c.fq_inv_fb);
        j.n("fq_mul_verify", c.fq_mul_verify)
            .n("fq_inv_verify", c.fq_inv_verify);
        j.n("elim_ops", c.elim_ops)
            .n("elim_entries", c.elim_entries)
            .n("wied_ops", c.wied_ops)
            .n("bm_ops", c.bm_ops)
            .n("matvecs", c.matvecs);
        j.n("lops", self.lops());
        j.n("hash_lookups", c.hash_lookups)
            .n("hash_inserts", c.hash_inserts)
            .n("rng_draws", c.rng_draws)
            .n("uf_ops", c.uf_ops)
            .n("root_calls", c.root_calls)
            .n("norm_calls", c.norm_calls);
        j.n("rel_wall_s", self.rel_wall_s)
            .n("la_wall_s", self.la_wall_s);
        j.n("la_ok", self.la_ok as u32)
            .s("la_fail", &self.la_fail)
            .n("la_deg", self.la_deg)
            .n("holdout", self.holdout)
            .n("holdout_ok", self.holdout_ok as u32);
        j.n("coverage", self.coverage as u32)
            .n("cross_pairs", self.cross_pairs)
            .n("cross_ok", self.cross_ok);
        j.n("push_checked", self.push_checked)
            .n("push_fail", self.push_fail);
        let rp: Vec<String> = self
            .rank_profile
            .iter()
            .map(|(f, t, r, k)| format!("[{},{},{},{}]", f, t, r, k))
            .collect();
        j.raw("rank_profile", &format!("[{}]", rp.join(",")));
        j.done()
    }
}

fn ceil_i(x: f64) -> i64 {
    x.ceil() as i64
}

/// Execute one IC cell: relation phase, structured elimination, Wiedemann, with the
/// protocol's verification and ell-part tests. `wall_cap_s` bounds relation + LA wall time.
pub fn run_ic_cell(
    inst: &Inst,
    arm: Arm,
    kappa: f64,
    seed: u64,
    wall_cap_s: f64,
    do_rank_profile: bool,
    skip_la: bool,
) -> IcCell {
    let start = std::time::Instant::now();
    let deadline = start + std::time::Duration::from_secs_f64(wall_cap_s);
    let mont = Mont::new(inst.ell);
    let mut col = Collector::new(inst, arm, kappa, seed);
    let nfb = col.fb.len();
    let ncols = nfb;
    let mut cell = IcCell {
        k: inst.k,
        idx: inst.idx,
        arm: arm.name(),
        kappa,
        q: inst.q,
        ell: inst.ell,
        h: inst.h,
        nfb,
        ncols,
        rounds: 1,
        ..Default::default()
    };
    let mut target = ceil_i(1.1 * (nfb as f64 + 1.0) + 20.0);
    let mut la_best: Option<LaResult> = None;
    let mut rows_final: Vec<SRow> = vec![];
    loop {
        let t = std::time::Instant::now();
        let ok = col.run_until(target, u64::MAX, Some(deadline));
        cell.rel_wall_s += t.elapsed().as_secs_f64();
        if std::env::var("DQ_DEBUG").is_ok() {
            eprintln!(
                "[dq] rel done ok={} lines={} rels={} avail={} t={:.2}",
                ok,
                col.ctr.lines,
                col.rels.len(),
                col.available(),
                cell.rel_wall_s
            );
        }
        if !ok {
            cell.status = if col.exhausted {
                "pairs_exhausted".into()
            } else {
                "timeout_relations".into()
            };
            break;
        }
        let t = std::time::Instant::now();
        let rows0 = build_rows(&mont, nfb, &col.rels);
        cell.rows_collected = rows0.len();
        let (mut eo, mut ee) = (0u64, 0u64);
        let rows = eliminate_lp(&mont, nfb, rows0, &mut eo, &mut ee);
        col.ctr.elim_ops += eo;
        col.ctr.elim_entries += ee;
        cell.rows_after_elim = rows.len();
        if skip_la {
            cell.la_wall_s += t.elapsed().as_secs_f64();
            cell.status = "rel_only".into();
            cell.target_final = target;
            break;
        }
        if std::env::var("DQ_DEBUG").is_ok() {
            eprintln!(
                "[dq] elim done rows={} ops={} t={:.2}",
                rows.len(),
                eo,
                t.elapsed().as_secs_f64()
            );
        }
        let holdout = ((rows.len() / 20).max(20)).min(rows.len());
        let la = wiedemann_solve(
            &mont,
            &rows,
            ncols,
            holdout,
            seed ^ 0x4C41 ^ cell.rounds as u64,
            Some(deadline),
        );
        cell.la_wall_s += t.elapsed().as_secs_f64();
        col.ctr.wied_ops += la.wied_ops;
        col.ctr.bm_ops += la.bm_ops;
        col.ctr.matvecs += la.matvecs;
        cell.la_deg = la.deg;
        cell.holdout = la.holdout;
        cell.holdout_ok = la.holdout_ok;
        cell.la_fail = la.fail.to_string();
        cell.target_final = target;
        if la.ok {
            cell.la_ok = true;
            cell.status = "ok".into();
            rows_final = rows;
            la_best = Some(la);
            break;
        }
        if la.fail == "timeout" {
            cell.status = "timeout_la".into();
            break;
        }
        if cell.rounds >= 6 {
            cell.status = "la_failed".into();
            break;
        }
        cell.rounds += 1;
        target = ceil_i(target as f64 * 1.25);
    }
    col.finish_counters();
    let _ = rows_final;
    // ---- verification and ell-part tests (not part of the attack cost) ----
    // pushforward of relations
    {
        let mut rng = SplitMix64::new(seed ^ 0x5055_5348);
        let n = col.rels.len();
        let idxs: Vec<usize> = if inst.k <= 12 || n <= 2000 {
            (0..n).collect()
        } else {
            (0..2000).map(|_| rng.below(n as u64) as usize).collect()
        };
        let mut first: Option<EPt> = None;
        for &i in &idxs {
            let s = pushforward_sum(inst, &col, &col.rels[i]);
            cell.push_checked += 1;
            match s {
                None => cell.push_fail += 1,
                Some(sv) => match &first {
                    None => first = Some(sv),
                    Some(f0) => {
                        if *f0 != sv {
                            cell.push_fail += 1;
                        }
                    }
                },
            }
        }
    }
    // ell-part coverage
    let p0 = inst.pi0(&col.fb[0].c).unwrap_or(None);
    let mut tvec: Vec<EPt> = Vec::with_capacity(nfb);
    {
        let np0 = inst.e_neg(&p0);
        let mut any = false;
        let limit = if nfb > 4000 { 4000 } else { nfb };
        for i in 0..limit {
            let pi = inst.pi0(&col.fb[i].c).unwrap_or(None);
            let t = inst.e_mul(&inst.e_add(&pi, &np0), inst.h as u128);
            if t.is_some() {
                any = true;
            }
            tvec.push(t);
        }
        cell.coverage = any;
    }
    if let Some(la) = &la_best {
        cell.v = la.v.clone();
        let mut rng = SplitMix64::new(seed ^ 0x4352_4F53);
        let lim = tvec.len() as u64;
        for _ in 0..20 {
            let a = rng.below(lim) as usize;
            let b = rng.below(lim) as usize;
            let (va, vb) = (
                if a == 0 { 0 } else { la.v[a] },
                if b == 0 { 0 } else { la.v[b] },
            );
            let l = inst.e_mul(&tvec[b], va as u128);
            let r = inst.e_mul(&tvec[a], vb as u128);
            cell.cross_pairs += 1;
            if l == r {
                cell.cross_ok += 1;
            }
        }
    }
    cell.ctr = col.ctr.clone();
    // rank profile (separate collector, same seed; cost excluded)
    if do_rank_profile && ncols <= 1500 {
        for &fct in &[1.0f64, 1.05, 1.1, 1.25, 1.5] {
            let mut c2 = Collector::new(inst, arm, kappa, seed);
            let tgt = ceil_i(fct * ncols as f64);
            if !c2.run_until(
                tgt,
                u64::MAX,
                Some(deadline + std::time::Duration::from_secs(600)),
            ) {
                break;
            }
            let rows0 = build_rows(&mont, nfb, &c2.rels);
            let (mut eo, mut ee) = (0u64, 0u64);
            let rows = eliminate_lp(&mont, nfb, rows0, &mut eo, &mut ee);
            let rk = dense_rank(&mont, &rows, ncols);
            cell.rank_profile.push((fct, rows.len(), rk, ncols - rk));
        }
    }
    cell
}

/// One rho measurement as a JSON line (raw counters; pricing is done by the analysis).
pub fn rho_json(inst: &Inst, run: u32, o: &RhoOut, rinv: f64) -> String {
    let mut j = J::new();
    j.n("k", inst.k)
        .n("idx", inst.idx)
        .n("run", run)
        .n("q", inst.q)
        .n("ell", inst.ell)
        .n("h", inst.h);
    j.n("ok", o.ok as u32)
        .n("verified", o.verified as u32)
        .n("timeout", o.timeout as u32);
    j.n("steps", o.steps)
        .n("dps", o.dps)
        .n("dp_lookups", o.dp_lookups)
        .n("dp_inserts", o.dp_inserts)
        .n("dp_checks", o.dp_checks);
    j.n("part_hashes", o.part_hashes)
        .n("rng_draws", o.rng_draws)
        .n("modl_adds", o.modl_adds)
        .n("canon", o.canon);
    j.n("restarts", o.restarts).n("fallbacks", o.fallbacks);
    j.n("fq_mul", o.fq_mul)
        .n("fq_inv", o.fq_inv)
        .n("setup_fq_mul", o.setup_fq_mul)
        .n("setup_fq_inv", o.setup_fq_inv);
    j.n("restart_fq_mul", o.restart_fq_mul)
        .n("restart_fq_inv", o.restart_fq_inv);
    j.n("d", o.d)
        .n("m", o.m)
        .n("r", o.r)
        .n("wall_s", o.wall_s)
        .n("rho_inv", rinv);
    j.done()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn kfast_matches_kf() {
        let q = q_of_k(9);
        let kf = Kf::new(q);
        let fast = KFast::new(&kf);
        let mut rng = SplitMix64::new(7);
        for _ in 0..50 {
            let x = kf.rand(&mut rng);
            let y = kf.rand(&mut rng);
            kf.f.muls.set(0);
            kf.f.invs.set(0);
            fast.fqm.set(0);
            fast.fqi.set(0);
            assert_eq!(kf.mul(&x, &y), fast.mul(&x, &y));
            assert_eq!(kf.f.counts().0, fast.fqm.get());
            if x != [0; 3] {
                kf.f.muls.set(0);
                kf.f.invs.set(0);
                fast.fqm.set(0);
                fast.fqi.set(0);
                assert_eq!(kf.inv(&x), fast.inv(&x));
                assert_eq!(kf.f.counts(), (fast.fqm.get(), fast.fqi.get()));
            }
        }
    }

    #[test]
    fn mont_and_bm() {
        let m = Mont::new(1_000_000_007);
        let a = m.to(123456789);
        assert_eq!(m.from(m.mul(a, m.inv(a))), 1);
        // Fibonacci-like recurrence
        let mut s = vec![m.to(1), m.to(1)];
        for i in 2..20 {
            let v = m.add(s[i - 1], s[i - 2]);
            s.push(v);
        }
        let mut ops = 0;
        let (_c, l) = berlekamp_massey(&m, &s, &mut ops);
        assert_eq!(l, 2);
    }

    fn check_instance(k: u32, idx: u32) -> Inst {
        let inst = gen_instance(k, idx);
        assert!(is_prime_u64(inst.ell));
        assert_eq!(inst.order, inst.h * inst.ell);
        let f = inst.f();
        let pts = enumerate_points(f, &inst.quartic);
        assert_eq!(pts.len() as u64, inst.q + 1);
        for p in &pts {
            assert_eq!(eval_g(f, &inst.quartic, p), 0);
            let e = inst.pi0(p).expect("point lies on the cover");
            assert!(inst.e_on_curve(&e), "pi0 image on E0");
            assert!(inst.e_mul(&e, inst.order as u128).is_none(), "N pi0(P) = O");
        }
        inst
    }

    #[test]
    fn instance_k8() {
        check_instance(8, 0);
    }

    #[test]
    fn full_cell_k8() {
        let inst = gen_instance(8, 0);
        let c = run_ic_cell(&inst, Arm::Full, 1.0, 11, 300.0, true, false);
        eprintln!("{}", c.to_json());
        assert_eq!(c.ctr.verify_failed, 0);
        assert_eq!(c.push_fail, 0);
        assert!(c.la_ok);
        assert!(c.coverage);
        assert_eq!(c.cross_ok, c.cross_pairs);
    }

    #[test]
    fn slp_dlp_cells_k10() {
        let inst = gen_instance(10, 0);
        for (arm, kappa) in [(Arm::Slp, 2.0), (Arm::Dlp, 4.0)] {
            let c = run_ic_cell(&inst, arm, kappa, 5, 300.0, false, false);
            eprintln!("{}", c.to_json());
            assert_eq!(c.ctr.verify_failed, 0);
            assert_eq!(c.push_fail, 0);
            assert!(c.la_ok, "{:?}", c.status);
            assert_eq!(c.cross_ok, c.cross_pairs);
        }
    }

    #[test]
    fn rho_k8_k10() {
        for k in [8u32, 10] {
            let inst = gen_instance(k, 0);
            let o = rho_run(&inst, 3, None);
            eprintln!("{:?}", o);
            assert!(o.ok && o.verified);
        }
    }
}
