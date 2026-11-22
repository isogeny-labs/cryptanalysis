//! Dense univariate polynomials over a prime field [`Fp`].
//!
//! Coefficients are ascending, canonical in `[0, p)`, and always
//! normalized (no trailing zeros; the zero polynomial is the empty
//! vector). The field is passed explicitly to every operation.
//!
//! Multiplication accumulates products in `u128` and reduces once per
//! output coefficient (schoolbook), switching to Karatsuba above
//! [`KARATSUBA_THRESHOLD`]. Division uses one Barrett reduction per
//! multiply-add. Factorization is Yun-style square-free decomposition,
//! distinct-degree factorization and Cantor-Zassenhaus equal-degree
//! splitting (the trace map for `p = 2`).

use super::fp::Fp;
use num_bigint::BigUint;
use num_traits::{One, Zero};
use rand::rngs::StdRng;
use rand::{Rng, RngCore, SeedableRng};
use std::fmt;

/// Operand length at or below which multiplication is schoolbook.
pub const KARATSUBA_THRESHOLD: usize = 32;

/// A polynomial over `F_p` (see the module documentation for invariants).
#[derive(Clone, Debug, PartialEq, Eq, Hash, Default)]
pub struct Poly {
    /// Ascending canonical coefficients, no trailing zero.
    pub c: Vec<u64>,
}

fn trim(v: &mut Vec<u64>) {
    while v.last() == Some(&0) {
        v.pop();
    }
}

fn school(a: &[u64], b: &[u64], f: &Fp) -> Vec<u64> {
    if a.is_empty() || b.is_empty() {
        return Vec::new();
    }
    let (na, nb) = (a.len(), b.len());
    let mut out = Vec::with_capacity(na + nb - 1);
    for k in 0..na + nb - 1 {
        let lo = k.saturating_sub(nb - 1);
        let hi = k.min(na - 1);
        let mut acc: u128 = 0;
        for (x, y) in a[lo..=hi].iter().zip(b[k - hi..=k - lo].iter().rev()) {
            acc += (x * y) as u128;
        }
        out.push(f.reduce_u128(acc));
    }
    out
}

fn add_into(res: &mut [u64], off: usize, v: &[u64], f: &Fp) {
    for (r, &x) in res[off..off + v.len()].iter_mut().zip(v) {
        *r = f.add(*r, x);
    }
}

fn sub_into(res: &mut [u64], off: usize, v: &[u64], f: &Fp) {
    for (r, &x) in res[off..off + v.len()].iter_mut().zip(v) {
        *r = f.sub(*r, x);
    }
}

fn sum_slices(a: &[u64], b: &[u64], f: &Fp) -> Vec<u64> {
    let (long, short) = if a.len() >= b.len() { (a, b) } else { (b, a) };
    let mut r = long.to_vec();
    add_into(&mut r, 0, short, f);
    r
}

/// Product of raw coefficient slices, exact length `a.len()+b.len()-1`
/// (not normalized).
fn kara(a: &[u64], b: &[u64], f: &Fp) -> Vec<u64> {
    if a.is_empty() || b.is_empty() {
        return Vec::new();
    }
    let (a, b) = if a.len() >= b.len() { (a, b) } else { (b, a) };
    let (la, lb) = (a.len(), b.len());
    if lb <= KARATSUBA_THRESHOLD {
        return school(a, b, f);
    }
    if la >= 2 * lb {
        let mut res = vec![0u64; la + lb - 1];
        for (i, chunk) in a.chunks(lb).enumerate() {
            let prod = kara(chunk, b, f);
            add_into(&mut res, i * lb, &prod, f);
        }
        return res;
    }
    let h = la / 2;
    let (a0, a1) = a.split_at(h);
    let (b0, b1) = b.split_at(h);
    let z0 = kara(a0, b0, f);
    let z2 = kara(a1, b1, f);
    let mut z1 = kara(&sum_slices(a0, a1, f), &sum_slices(b0, b1, f), f);
    sub_into(&mut z1, 0, &z0, f);
    sub_into(&mut z1, 0, &z2, f);
    let mut res = vec![0u64; la + lb - 1];
    add_into(&mut res, 0, &z0, f);
    add_into(&mut res, h, &z1, f);
    add_into(&mut res, 2 * h, &z2, f);
    res
}

/// Reduces `r` modulo `d` (nonempty, normalized, with `inv` the inverse of
/// its leading coefficient) in place; fills `q` (length
/// `r.len() - d.len() + 1` beforehand) when given. `r` is normalized after.
fn divrem_raw(r: &mut Vec<u64>, d: &[u64], inv: u64, f: &Fp, mut q: Option<&mut [u64]>) {
    let dn = d.len() - 1;
    if r.len() > dn {
        let qn = r.len() - dn;
        for i in (0..qn).rev() {
            let top = r[i + dn];
            if top == 0 {
                continue;
            }
            let qc = f.mul(top, inv);
            if let Some(q) = q.as_deref_mut() {
                q[i] = qc;
            }
            let nq = f.neg(qc);
            for (rj, &dj) in r[i..i + dn].iter_mut().zip(&d[..dn]) {
                *rj = f.mul_add(nq, dj, *rj);
            }
            r[i + dn] = 0;
        }
        r.truncate(dn);
    }
    trim(r);
}

/// `a*b mod m` with `inv` the inverse of `m`'s leading coefficient.
fn mm(a: &Poly, b: &Poly, m: &Poly, inv: u64, f: &Fp) -> Poly {
    let mut r = kara(&a.c, &b.c, f);
    trim(&mut r);
    divrem_raw(&mut r, &m.c, inv, f, None);
    Poly { c: r }
}

fn small_factor_primes(mut n: usize) -> Vec<usize> {
    let mut v = Vec::new();
    let mut q = 2;
    while q * q <= n {
        if n.rem_euclid(q) == 0 {
            v.push(q);
            while n.rem_euclid(q) == 0 {
                n /= q;
            }
        }
        q += 1;
    }
    if n > 1 {
        v.push(n);
    }
    v
}

impl Poly {
    /// The zero polynomial.
    pub fn zero() -> Poly {
        Poly { c: Vec::new() }
    }
    /// The constant polynomial `1`.
    pub fn one() -> Poly {
        Poly { c: vec![1] }
    }
    /// The polynomial `x`.
    pub fn x() -> Poly {
        Poly { c: vec![0, 1] }
    }
    /// The constant `a` (canonical); `constant(0)` is zero.
    pub fn constant(a: u64) -> Poly {
        if a == 0 {
            Poly::zero()
        } else {
            Poly { c: vec![a] }
        }
    }
    /// `coeff * x^deg` (coefficient canonical).
    pub fn monomial(deg: usize, coeff: u64) -> Poly {
        if coeff == 0 {
            return Poly::zero();
        }
        let mut c = vec![0; deg + 1];
        c[deg] = coeff;
        Poly { c }
    }
    /// Builds from ascending coefficients, reducing each mod `p`.
    pub fn from_coeffs(v: Vec<u64>, f: &Fp) -> Poly {
        let mut c: Vec<u64> = v.into_iter().map(|a| f.reduce_u128(a as u128)).collect();
        trim(&mut c);
        Poly { c }
    }
    /// Builds from signed ascending coefficients.
    pub fn from_i64(v: &[i64], f: &Fp) -> Poly {
        let mut c: Vec<u64> = v.iter().map(|&a| f.reduce_i64(a)).collect();
        trim(&mut c);
        Poly { c }
    }
    /// Removes trailing zero coefficients.
    pub fn normalize(&mut self) {
        trim(&mut self.c);
    }
    /// Degree, `None` for zero.
    pub fn degree(&self) -> Option<usize> {
        if self.c.is_empty() {
            None
        } else {
            Some(self.c.len() - 1)
        }
    }
    /// Degree, `-1` for zero.
    pub fn deg(&self) -> isize {
        self.c.len() as isize - 1
    }
    /// Whether this is the zero polynomial.
    pub fn is_zero(&self) -> bool {
        self.c.is_empty()
    }
    /// Whether this is the constant `1`.
    pub fn is_one(&self) -> bool {
        self.c.len() == 1 && self.c[0] == 1
    }
    /// Whether the degree is `<= 0` (zero counts as constant).
    pub fn is_constant(&self) -> bool {
        self.c.len() <= 1
    }
    /// Leading coefficient (`0` for zero).
    pub fn leading(&self) -> u64 {
        self.c.last().copied().unwrap_or(0)
    }
    /// Whether the leading coefficient is `1`.
    pub fn is_monic(&self) -> bool {
        self.leading() == 1
    }
    /// Coefficient of `x^i` (`0` beyond the length).
    pub fn coeff(&self, i: usize) -> u64 {
        self.c.get(i).copied().unwrap_or(0)
    }

    /// `self + o`.
    pub fn add(&self, o: &Poly, f: &Fp) -> Poly {
        let mut r = self.clone();
        r.add_assign(o, f);
        r
    }
    /// `self - o`.
    pub fn sub(&self, o: &Poly, f: &Fp) -> Poly {
        let mut r = self.clone();
        r.sub_assign(o, f);
        r
    }
    /// `-self`.
    pub fn neg(&self, f: &Fp) -> Poly {
        Poly {
            c: self.c.iter().map(|&a| f.neg(a)).collect(),
        }
    }
    /// `self += o`.
    pub fn add_assign(&mut self, o: &Poly, f: &Fp) {
        if self.c.len() < o.c.len() {
            self.c.resize(o.c.len(), 0);
        }
        add_into(&mut self.c, 0, &o.c, f);
        trim(&mut self.c);
    }
    /// `self -= o`.
    pub fn sub_assign(&mut self, o: &Poly, f: &Fp) {
        if self.c.len() < o.c.len() {
            self.c.resize(o.c.len(), 0);
        }
        sub_into(&mut self.c, 0, &o.c, f);
        trim(&mut self.c);
    }

    /// `self * o` (schoolbook below [`KARATSUBA_THRESHOLD`], Karatsuba above).
    pub fn mul(&self, o: &Poly, f: &Fp) -> Poly {
        let mut c = kara(&self.c, &o.c, f);
        trim(&mut c);
        Poly { c }
    }
    /// `self * o` by schoolbook only (reference implementation).
    pub fn mul_schoolbook(&self, o: &Poly, f: &Fp) -> Poly {
        let mut c = school(&self.c, &o.c, f);
        trim(&mut c);
        Poly { c }
    }
    /// `s * self`.
    pub fn mul_scalar(&self, s: u64, f: &Fp) -> Poly {
        if s == 0 {
            return Poly::zero();
        }
        Poly {
            c: self.c.iter().map(|&a| f.mul(a, s)).collect(),
        }
    }
    /// `x^k * self`.
    pub fn mul_xk(&self, k: usize) -> Poly {
        if self.is_zero() {
            return Poly::zero();
        }
        let mut c = vec![0; k];
        c.extend_from_slice(&self.c);
        Poly { c }
    }
    /// `self^2`.
    pub fn sqr(&self, f: &Fp) -> Poly {
        self.mul(self, f)
    }

    /// Quotient and remainder, `self = q*d + r`, `deg r < deg d`.
    ///
    /// # Panics
    /// If `d` is zero.
    pub fn divrem(&self, d: &Poly, f: &Fp) -> (Poly, Poly) {
        assert!(!d.is_zero(), "polynomial division by zero");
        if self.c.len() < d.c.len() {
            return (Poly::zero(), self.clone());
        }
        let inv = f.inv(d.leading()).expect("leading coefficient is nonzero");
        let mut r = self.c.clone();
        let mut q = vec![0u64; self.c.len() - d.c.len() + 1];
        divrem_raw(&mut r, &d.c, inv, f, Some(&mut q));
        trim(&mut q);
        (Poly { c: q }, Poly { c: r })
    }
    /// Remainder of `self` modulo `d` (panics if `d` is zero).
    pub fn rem(&self, d: &Poly, f: &Fp) -> Poly {
        assert!(!d.is_zero(), "polynomial division by zero");
        if self.c.len() < d.c.len() {
            return self.clone();
        }
        let inv = f.inv(d.leading()).expect("leading coefficient is nonzero");
        let mut r = self.c.clone();
        divrem_raw(&mut r, &d.c, inv, f, None);
        Poly { c: r }
    }
    /// Quotient of `self` by `d` (panics if `d` is zero).
    pub fn quo(&self, d: &Poly, f: &Fp) -> Poly {
        self.divrem(d, f).0
    }
    /// The quotient if `d` divides `self` exactly, else `None`.
    pub fn div_exact(&self, d: &Poly, f: &Fp) -> Option<Poly> {
        let (q, r) = self.divrem(d, f);
        if r.is_zero() {
            Some(q)
        } else {
            None
        }
    }
    /// Whether `self` divides `o` (`false` for `self = 0` unless `o = 0`).
    pub fn divides(&self, o: &Poly, f: &Fp) -> bool {
        if self.is_zero() {
            return o.is_zero();
        }
        o.rem(self, f).is_zero()
    }
    /// Monic gcd (`gcd(0, 0) = 0`).
    pub fn gcd(&self, o: &Poly, f: &Fp) -> Poly {
        let (mut x, mut y) = (self.clone(), o.clone());
        while !y.is_zero() {
            let r = x.rem(&y, f);
            x = y;
            y = r;
        }
        x.monic(f)
    }
    /// Extended Euclid: `(g, s, t)` with `s*self + t*o = g`, `g` monic.
    pub fn xgcd(&self, o: &Poly, f: &Fp) -> (Poly, Poly, Poly) {
        let (mut r0, mut r1) = (self.clone(), o.clone());
        let (mut s0, mut s1) = (Poly::one(), Poly::zero());
        let (mut t0, mut t1) = (Poly::zero(), Poly::one());
        while !r1.is_zero() {
            let (q, r) = r0.divrem(&r1, f);
            let s2 = s0.sub(&q.mul(&s1, f), f);
            let t2 = t0.sub(&q.mul(&t1, f), f);
            r0 = r1;
            r1 = r;
            s0 = s1;
            s1 = s2;
            t0 = t1;
            t1 = t2;
        }
        if r0.is_zero() {
            return (Poly::zero(), Poly::zero(), Poly::zero());
        }
        let inv = f.inv(r0.leading()).expect("nonzero");
        (
            r0.mul_scalar(inv, f),
            s0.mul_scalar(inv, f),
            t0.mul_scalar(inv, f),
        )
    }
    /// `self` scaled to leading coefficient `1` (zero stays zero).
    pub fn monic(&self, f: &Fp) -> Poly {
        if self.is_zero() || self.is_monic() {
            return self.clone();
        }
        self.mul_scalar(f.inv(self.leading()).expect("nonzero"), f)
    }
    /// Formal derivative.
    pub fn derivative(&self, f: &Fp) -> Poly {
        let p = f.p();
        let mut c: Vec<u64> = (1..self.c.len())
            .map(|i| f.mul(self.c[i], (i as u64) % p))
            .collect();
        trim(&mut c);
        Poly { c }
    }
    /// Horner evaluation at `x`.
    pub fn eval(&self, x: u64, f: &Fp) -> u64 {
        let mut acc = 0;
        for &a in self.c.iter().rev() {
            acc = f.mul_add(acc, x, a);
        }
        acc
    }
    /// `p(x + a)` (Taylor shift, quadratic time).
    pub fn shift(&self, a: u64, f: &Fp) -> Poly {
        if self.c.len() <= 1 || a == 0 {
            return self.clone();
        }
        let mut c = self.c.clone();
        let n = c.len() - 1;
        for i in 0..n {
            for j in (i..n).rev() {
                c[j] = f.mul_add(a, c[j + 1], c[j]);
            }
        }
        trim(&mut c);
        Poly { c }
    }

    /// `a*b mod m` (panics if `m` is zero).
    pub fn mulmod(a: &Poly, b: &Poly, m: &Poly, f: &Fp) -> Poly {
        assert!(!m.is_zero(), "modulus is zero");
        let inv = f.inv(m.leading()).expect("nonzero");
        mm(a, b, m, inv, f)
    }

    fn powmod_bits(&self, bits: impl Iterator<Item = bool>, m: &Poly, f: &Fp) -> Poly {
        assert!(!m.is_zero(), "modulus is zero");
        if m.is_constant() {
            return Poly::zero();
        }
        let inv = f.inv(m.leading()).expect("nonzero");
        let base = self.rem(m, f);
        let mut r = Poly::one();
        for bit in bits {
            r = mm(&r, &r, m, inv, f);
            if bit {
                r = mm(&r, &base, m, inv, f);
            }
        }
        r
    }

    /// `self^e mod m` (`m` nonzero; the result is zero if `m` is constant).
    pub fn powmod(&self, e: &BigUint, m: &Poly, f: &Fp) -> Poly {
        let n = e.bits();
        self.powmod_bits((0..n).rev().map(|i| e.bit(i)), m, f)
    }
    /// `self^e mod m`, 64-bit exponent.
    pub fn powmod_u64(&self, e: u64, m: &Poly, f: &Fp) -> Poly {
        let n = 64 - e.leading_zeros() as u64;
        self.powmod_bits((0..n).rev().map(|i| (e >> i) & 1 == 1), m, f)
    }
    /// `self^p mod m`.
    pub fn frobenius_mod(&self, m: &Poly, f: &Fp) -> Poly {
        self.powmod_u64(f.p(), m, f)
    }
    /// Inverse of `self` modulo `m` when `gcd = 1`, reduced mod `m`.
    pub fn inv_mod(&self, m: &Poly, f: &Fp) -> Option<Poly> {
        let (g, s, _) = self.rem(m, f).xgcd(m, f);
        if g.is_one() {
            Some(s.rem(m, f))
        } else {
            None
        }
    }

    /// Whether `gcd(self, self') = 1`. Nonzero constants are squarefree,
    /// zero is not; a nonconstant `p`-th power is not.
    pub fn is_squarefree(&self, f: &Fp) -> bool {
        if self.is_zero() {
            return false;
        }
        if self.is_constant() {
            return true;
        }
        let d = self.derivative(f);
        if d.is_zero() {
            return false;
        }
        self.gcd(&d, f).is_constant()
    }

    /// Rabin's irreducibility test (degree `>= 1`; the leading
    /// coefficient is irrelevant).
    pub fn is_irreducible(&self, f: &Fp) -> bool {
        let n = match self.degree() {
            None | Some(0) => return false,
            Some(1) => return true,
            Some(n) => n,
        };
        let m = self.monic(f);
        let checks = small_factor_primes(n)
            .into_iter()
            .map(|q| n / q)
            .collect::<Vec<_>>();
        let x = Poly::x();
        let mut h = x.clone();
        for k in 1..=n {
            h = h.frobenius_mod(&m, f);
            if k == n {
                return h == x;
            }
            if checks.contains(&k) && !h.sub(&x, f).gcd(&m, f).is_one() {
                return false;
            }
        }
        unreachable!()
    }

    /// Distinct roots in `F_p`, ascending (empty for the zero polynomial).
    /// Brute force for `p <= 64`; otherwise `gcd(x^p - x, self)` then
    /// Cantor-Zassenhaus splitting with a fixed internal seed.
    pub fn roots(&self, f: &Fp) -> Vec<u64> {
        let p = f.p();
        if self.is_constant() {
            return Vec::new();
        }
        if p <= 64 {
            return (0..p).filter(|&x| self.eval(x, f) == 0).collect();
        }
        let xp = Poly::x().frobenius_mod(self, f);
        let g = xp.sub(&Poly::x(), f).gcd(self, f);
        let mut out = Vec::new();
        let mut rng = StdRng::seed_from_u64(0x5eed_0000 ^ p);
        split_roots(&g, f, &mut rng, &mut out);
        out.sort_unstable();
        out
    }

    /// Square-free decomposition: monic pairs `(g, e)` (sorted by `e`,
    /// each `g` squarefree, pairwise coprime) with `self = lc * ∏ g^e`.
    /// Empty for zero and constants.
    pub fn squarefree_decomposition(&self, f: &Fp) -> Vec<(Poly, usize)> {
        let mut out = Vec::new();
        if !self.is_constant() {
            sfd_rec(&self.monic(f), 1, f, &mut out);
        }
        out.sort_by(|a, b| (a.1, a.0.degree(), &a.0.c).cmp(&(b.1, b.0.degree(), &b.0.c)));
        out
    }

    /// Distinct-degree factorization of a monic squarefree polynomial:
    /// `(d, product of the irreducible factors of degree d)`, ascending `d`.
    pub fn distinct_degree_factorization(&self, f: &Fp) -> Vec<(usize, Poly)> {
        self.ddf_impl(f, None).expect("no bound")
    }

    /// DDF with an optional smoothness bound: `None` as soon as a factor
    /// of degree `> bound` is certain.
    fn ddf_impl(&self, f: &Fp, bound: Option<usize>) -> Option<Vec<(usize, Poly)>> {
        let mut out = Vec::new();
        let mut g = self.clone();
        let mut h = Poly::x();
        let x = Poly::x();
        let mut d = 1;
        while g.deg() >= 2 * d as isize {
            if let Some(b) = bound {
                if g.deg() <= b as isize {
                    return Some(out);
                }
                if d > b {
                    return None;
                }
            }
            h = h.frobenius_mod(&g, f);
            let fac = h.sub(&x, f).gcd(&g, f);
            if !fac.is_constant() {
                g = g.quo(&fac, f);
                h = h.rem(&g, f);
                out.push((d, fac));
            }
            d += 1;
        }
        if g.deg() > 0 {
            if let Some(b) = bound {
                if g.deg() > b as isize {
                    return None;
                }
            }
            out.push((g.deg() as usize, g));
        }
        Some(out)
    }

    /// Equal-degree factorization of a monic squarefree product of
    /// irreducibles of degree `d` (Cantor-Zassenhaus; trace map for
    /// `p = 2`). The factors are returned in no particular order.
    pub fn equal_degree_factorization(
        &self,
        d: usize,
        f: &Fp,
        rng: &mut impl RngCore,
    ) -> Vec<Poly> {
        let mut out = Vec::new();
        edf_rec(self, d, f, rng, &mut out);
        out
    }

    /// Full factorization: monic irreducible factors with multiplicities,
    /// sorted by `(degree, coefficients)`. The leading coefficient is
    /// discarded; zero and constants give an empty list.
    pub fn factor(&self, f: &Fp, rng: &mut impl RngCore) -> Vec<(Poly, usize)> {
        let mut out = Vec::new();
        for (w, e) in self.squarefree_decomposition(f) {
            for (d, prod) in w.distinct_degree_factorization(f) {
                for g in prod.equal_degree_factorization(d, f, rng) {
                    out.push((g, e));
                }
            }
        }
        out.sort_by(|a, b| (a.0.degree(), &a.0.c).cmp(&(b.0.degree(), &b.0.c)));
        out
    }

    /// Largest degree of an irreducible factor (SFD + DDF, no splitting);
    /// `None` for zero and constants.
    pub fn max_irreducible_degree(&self, f: &Fp) -> Option<usize> {
        let mut best = None;
        for (w, _) in self.squarefree_decomposition(f) {
            for (d, _) in w.distinct_degree_factorization(f) {
                best = best.max(Some(d));
            }
        }
        best
    }

    /// Whether every irreducible factor has degree `<= bound` (SFD + DDF
    /// with early exit). Zero is not smooth; constants are.
    pub fn is_smooth(&self, bound: usize, f: &Fp) -> bool {
        if self.is_zero() {
            return false;
        }
        for (w, _) in self.squarefree_decomposition(f) {
            if w.deg() <= bound as isize {
                continue;
            }
            if w.ddf_impl(f, Some(bound)).is_none() {
                return false;
            }
        }
        true
    }

    /// Uniformly random polynomial of degree `<= deg`.
    pub fn random(deg: usize, f: &Fp, rng: &mut impl RngCore) -> Poly {
        let mut c: Vec<u64> = (0..=deg).map(|_| f.random(rng)).collect();
        trim(&mut c);
        Poly { c }
    }
    /// Random monic polynomial of exact degree `deg`.
    pub fn random_monic(deg: usize, f: &Fp, rng: &mut impl RngCore) -> Poly {
        let mut c: Vec<u64> = (0..deg).map(|_| f.random(rng)).collect();
        c.push(1);
        Poly { c }
    }
    /// Random monic irreducible polynomial of degree `deg >= 1`
    /// (rejection sampling; expected `deg` trials).
    pub fn random_irreducible(deg: usize, f: &Fp, rng: &mut impl RngCore) -> Poly {
        assert!(deg >= 1, "no irreducible polynomial of degree 0");
        loop {
            let g = Poly::random_monic(deg, f, rng);
            if g.is_irreducible(f) {
                return g;
            }
        }
    }
    /// Random monic squarefree polynomial of exact degree `deg`.
    pub fn random_squarefree_monic(deg: usize, f: &Fp, rng: &mut impl RngCore) -> Poly {
        loop {
            let g = Poly::random_monic(deg, f, rng);
            if g.is_squarefree(f) {
                return g;
            }
        }
    }
    /// All monic irreducibles of degree `deg`, sorted (high coefficient
    /// first). Cost: enumerates all `p^deg` monic polynomials and runs
    /// Rabin's test on each; intended for `p^deg <= 2^26`.
    pub fn all_monic_irreducibles(deg: usize, f: &Fp) -> Vec<Poly> {
        let p = f.p();
        let mut out = Vec::new();
        if deg == 0 {
            return out;
        }
        let mut c = vec![0u64; deg + 1];
        c[deg] = 1;
        'outer: loop {
            if deg == 1 || c[0] != 0 {
                let g = Poly { c: c.clone() };
                if g.is_irreducible(f) {
                    out.push(g);
                }
            }
            // increment the low coefficients like an odometer
            for ci in c.iter_mut().take(deg) {
                *ci += 1;
                if *ci < p {
                    continue 'outer;
                }
                *ci = 0;
            }
            break;
        }
        out.sort_by(|a, b| a.c.iter().rev().cmp(b.c.iter().rev()));
        out
    }
    /// Number of monic irreducibles of degree `deg` over `F_p`:
    /// `(1/d) Σ_{e|d} μ(e) p^{d/e}`. Saturates at `u128::MAX` on overflow.
    pub fn count_monic_irreducibles(deg: usize, p: u64) -> u128 {
        if deg == 0 {
            return 0;
        }
        let mut pos = BigUint::zero();
        let mut neg = BigUint::zero();
        for e in 1..=deg {
            if deg.rem_euclid(e) != 0 {
                continue;
            }
            let mu = mobius(e);
            if mu == 0 {
                continue;
            }
            let t = BigUint::from(p).pow((deg / e) as u32);
            if mu > 0 {
                pos += t;
            } else {
                neg += t;
            }
        }
        let r = (pos - neg) / BigUint::from(deg);
        num_traits::ToPrimitive::to_u128(&r).unwrap_or(u128::MAX)
    }

    /// Pretty printing in variable `var`, e.g. `x^3 + 2*x + 1`.
    pub fn to_string_pretty(&self, var: &str) -> String {
        if self.is_zero() {
            return "0".to_string();
        }
        let mut parts = Vec::new();
        for (i, &a) in self.c.iter().enumerate().rev() {
            if a == 0 {
                continue;
            }
            let s = match (i, a) {
                (0, _) => a.to_string(),
                (1, 1) => var.to_string(),
                (1, _) => format!("{a}*{var}"),
                (_, 1) => format!("{var}^{i}"),
                _ => format!("{a}*{var}^{i}"),
            };
            parts.push(s);
        }
        parts.join(" + ")
    }
}

impl fmt::Display for Poly {
    fn fmt(&self, out: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(out, "{}", self.to_string_pretty("x"))
    }
}

fn mobius(n: usize) -> i32 {
    let ps = small_factor_primes(n);
    let prod: usize = ps.iter().product();
    if prod != n {
        0
    } else if ps.len().rem_euclid(2) == 0 {
        1
    } else {
        -1
    }
}

fn split_roots(g: &Poly, f: &Fp, rng: &mut StdRng, out: &mut Vec<u64>) {
    match g.degree() {
        None | Some(0) => {}
        Some(1) => out.push(f.neg(g.c[0])),
        Some(n) => {
            let p = f.p();
            loop {
                let a = rng.gen_range(0..p);
                let base = Poly { c: vec![a, 1] };
                let h = base.powmod_u64((p - 1) / 2, g, f).sub(&Poly::one(), f);
                let d = h.gcd(g, f);
                if let Some(k) = d.degree() {
                    if k > 0 && k < n {
                        let rest = g.quo(&d, f);
                        split_roots(&d, f, rng, out);
                        split_roots(&rest, f, rng, out);
                        return;
                    }
                }
            }
        }
    }
}

/// `w` is monic nonconstant; multiplicities are scaled by `mult`.
fn sfd_rec(w: &Poly, mult: usize, f: &Fp, out: &mut Vec<(Poly, usize)>) {
    if w.is_constant() {
        return;
    }
    let p = f.p() as usize;
    let d = w.derivative(f);
    if d.is_zero() {
        sfd_rec(&p_th_root(w, p), mult * p, f, out);
        return;
    }
    let mut c = w.gcd(&d, f);
    let mut wq = w.quo(&c, f);
    let mut i = 1;
    while !wq.is_constant() {
        let y = wq.gcd(&c, f);
        let fac = wq.quo(&y, f);
        if !fac.is_constant() {
            out.push((fac, i * mult));
        }
        c = c.quo(&y, f);
        wq = y;
        i += 1;
    }
    if !c.is_constant() {
        sfd_rec(&p_th_root(&c, p), mult * p, f, out);
    }
}

/// `p`-th root of a polynomial in `x^p` over `F_p` (coefficients at
/// multiples of `p`; `a^p = a` on `F_p`).
fn p_th_root(w: &Poly, p: usize) -> Poly {
    let mut c: Vec<u64> = w.c.iter().step_by(p).copied().collect();
    trim(&mut c);
    Poly { c }
}

fn edf_rec<R: RngCore>(w: &Poly, d: usize, f: &Fp, rng: &mut R, out: &mut Vec<Poly>) {
    let n = match w.degree() {
        None | Some(0) => return,
        Some(n) => n,
    };
    if n == d {
        out.push(w.clone());
        return;
    }
    debug_assert!(n % d == 0);
    let p = f.p();
    let exp = if p != 2 {
        let e = (BigUint::from(p).pow(d as u32) - BigUint::one()) >> 1usize;
        Some(e)
    } else {
        None
    };
    loop {
        let a = Poly::random(n - 1, f, rng);
        let g = match &exp {
            Some(e) => {
                let b = a.powmod(e, w, f);
                b.sub(&Poly::one(), f).gcd(w, f)
            }
            None => {
                // trace map a + a^2 + ... + a^(2^(d-1)) over F_2
                let mut t = a.rem(w, f);
                let mut acc = t.clone();
                let inv = f.inv(w.leading()).expect("nonzero");
                for _ in 1..d {
                    t = mm(&t, &t, w, inv, f);
                    acc.add_assign(&t, f);
                }
                acc.gcd(w, f)
            }
        };
        if let Some(k) = g.degree() {
            if k > 0 && k < n {
                let rest = w.quo(&g, f);
                edf_rec(&g, d, f, rng, out);
                edf_rec(&rest, d, f, rng, out);
                return;
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    const TEST_PRIMES: [u64; 7] = [2, 3, 5, 7, 23, 1579, 2147483647];

    fn field(p: u64) -> Fp {
        Fp::new(p).unwrap()
    }

    fn product(fs: &[(Poly, usize)], f: &Fp) -> Poly {
        let mut r = Poly::one();
        for (g, e) in fs {
            for _ in 0..*e {
                r = r.mul(g, f);
            }
        }
        r
    }

    #[test]
    fn basics_and_display() {
        let f = field(7);
        let a = Poly::from_i64(&[1, 2, 0, 1], &f);
        assert_eq!(a.to_string(), "x^3 + 2*x + 1");
        assert_eq!(Poly::zero().to_string(), "0");
        assert_eq!(Poly::from_coeffs(vec![7, 14, 21], &f), Poly::zero());
        assert_eq!(Poly::from_i64(&[-1, 0, 0], &f).c, vec![6]);
        assert_eq!(a.deg(), 3);
        assert_eq!(Poly::zero().deg(), -1);
        assert_eq!(Poly::monomial(4, 3).to_string_pretty("t"), "3*t^4");
        assert_eq!(Poly::constant(0), Poly::zero());
        assert_eq!(a.eval(2, &f), (8 + 4 + 1) % 7);
        assert_eq!(a.derivative(&f).c, vec![2, 0, 3]);
        assert_eq!(a.coeff(10), 0);
        assert!(Poly::x().is_monic() && Poly::one().is_one() && Poly::zero().is_constant());
        assert_eq!(a.mul_xk(2).c, vec![0, 0, 1, 2, 0, 1]);
    }

    #[test]
    fn ring_axioms() {
        let mut rng = StdRng::seed_from_u64(10);
        for &p in &TEST_PRIMES {
            let f = field(p);
            for _ in 0..30 {
                let a = Poly::random(rng.gen_range(0..25), &f, &mut rng);
                let b = Poly::random(rng.gen_range(0..25), &f, &mut rng);
                let c = Poly::random(rng.gen_range(0..25), &f, &mut rng);
                assert_eq!(a.mul(&b, &f), b.mul(&a, &f));
                assert_eq!(a.mul(&b, &f).mul(&c, &f), a.mul(&b.mul(&c, &f), &f));
                assert_eq!(
                    a.mul(&b.add(&c, &f), &f),
                    a.mul(&b, &f).add(&a.mul(&c, &f), &f)
                );
                assert_eq!(a.add(&b, &f).sub(&b, &f), a);
                assert_eq!(a.add(&a.neg(&f), &f), Poly::zero());
                assert_eq!(a.sqr(&f), a.mul(&a, &f));
                if !b.is_zero() {
                    let prod = a.mul(&b, &f);
                    let (q, r) = prod.divrem(&b, &f);
                    assert_eq!(q, a);
                    assert!(r.is_zero());
                    assert_eq!(prod.div_exact(&b, &f), Some(a.clone()));
                    assert!(b.divides(&prod, &f));
                    let (q, r) = a.divrem(&b, &f);
                    assert_eq!(q.mul(&b, &f).add(&r, &f), a);
                    assert!(r.deg() < b.deg());
                    assert_eq!(a.rem(&b, &f), r);
                    assert_eq!(a.quo(&b, &f), q);
                    // xgcd identity
                    let (g, s, t) = a.xgcd(&b, &f);
                    assert_eq!(s.mul(&a, &f).add(&t.mul(&b, &f), &f), g);
                    assert!(g.is_monic());
                    assert_eq!(g, a.gcd(&b, &f));
                    assert!(g.divides(&a, &f) && g.divides(&b, &f));
                }
            }
        }
        let f = field(5);
        assert_eq!(Poly::zero().gcd(&Poly::zero(), &f), Poly::zero());
        let (g, s, t) = Poly::zero().xgcd(&Poly::from_i64(&[2, 2], &f), &f);
        assert_eq!(g, Poly::from_i64(&[1, 1], &f));
        assert_eq!(s, Poly::zero());
        assert_eq!(t, Poly::constant(3));
    }

    #[test]
    fn karatsuba_vs_schoolbook() {
        let mut rng = StdRng::seed_from_u64(11);
        for &p in &[2u64, 3, 65537, 4294967291] {
            let f = field(p);
            for da in (0..300).step_by(7) {
                for db in (0..300).step_by(13) {
                    let a = Poly::random(da, &f, &mut rng);
                    let b = Poly::random(db, &f, &mut rng);
                    assert_eq!(a.mul(&b, &f), a.mul_schoolbook(&b, &f), "p={p} {da} {db}");
                }
            }
            // all-maximal coefficients stress the lazy accumulation
            let m = Poly {
                c: vec![p - 1; 300],
            };
            assert_eq!(m.mul(&m, &f), m.mul_schoolbook(&m, &f));
        }
    }

    #[test]
    fn shift_powmod_inv() {
        let mut rng = StdRng::seed_from_u64(12);
        for &p in &[3u64, 1579, 4294967291] {
            let f = field(p);
            for _ in 0..20 {
                let a = Poly::random(15, &f, &mut rng);
                let s = f.random(&mut rng);
                let sh = a.shift(s, &f);
                for _ in 0..5 {
                    let x = f.random(&mut rng);
                    assert_eq!(sh.eval(x, &f), a.eval(f.add(x, s), &f));
                }
                let m = Poly::random_monic(9, &f, &mut rng);
                let e = rng.gen_range(0..2000u64);
                let mut r = Poly::one().rem(&m, &f);
                for _ in 0..e {
                    r = Poly::mulmod(&r, &a, &m, &f);
                }
                assert_eq!(a.powmod_u64(e, &m, &f), r);
                assert_eq!(a.powmod(&BigUint::from(e), &m, &f), r);
                assert_eq!(a.frobenius_mod(&m, &f), a.powmod_u64(p, &m, &f));
                if let Some(i) = a.inv_mod(&m, &f) {
                    assert!(Poly::mulmod(&a, &i, &m, &f).is_one());
                } else {
                    assert!(!a.gcd(&m, &f).is_one());
                }
            }
        }
    }

    #[test]
    fn roots_recovered() {
        let mut rng = StdRng::seed_from_u64(13);
        for &p in &[2u64, 3, 7, 65537, 4294967291] {
            let f = field(p);
            for _ in 0..10 {
                let k = rng.gen_range(1..=(p.min(25) as usize));
                let mut rs: Vec<u64> = Vec::new();
                while rs.len() < k {
                    let r = f.random(&mut rng);
                    if !rs.contains(&r) {
                        rs.push(r);
                    }
                }
                let mut g = Poly::one();
                for &r in &rs {
                    g = g.mul(&Poly::from_coeffs(vec![f.neg(r), 1], &f), &f);
                }
                // an extra irreducible quadratic-or-higher factor and a repeated root
                let extra = Poly::random_irreducible(3, &f, &mut rng);
                let h = g
                    .mul(&extra, &f)
                    .mul(&Poly::from_coeffs(vec![f.neg(rs[0]), 1], &f), &f);
                rs.sort_unstable();
                assert_eq!(g.roots(&f), rs, "p={p}");
                assert_eq!(h.roots(&f), rs, "p={p} with extras");
            }
        }
        let f = field(7);
        assert!(Poly::zero().roots(&f).is_empty());
        assert!(Poly::one().roots(&f).is_empty());
    }

    #[test]
    fn irreducibility_and_counts() {
        let f = field(2);
        // x^2+x+1 irreducible, x^4+x+1 irreducible, x^4+x^2+1 = (x^2+x+1)^2
        assert!(Poly::from_i64(&[1, 1, 1], &f).is_irreducible(&f));
        assert!(Poly::from_i64(&[1, 1, 0, 0, 1], &f).is_irreducible(&f));
        assert!(!Poly::from_i64(&[1, 0, 1, 0, 1], &f).is_irreducible(&f));
        for (p, dmax) in [(2u64, 10usize), (3, 6), (7, 4)] {
            let f = field(p);
            for d in 1..=dmax {
                let all = Poly::all_monic_irreducibles(d, &f);
                assert_eq!(
                    all.len() as u128,
                    Poly::count_monic_irreducibles(d, p),
                    "p={p} d={d}"
                );
                let mut sorted = all.clone();
                sorted.sort_by(|a, b| a.c.iter().rev().cmp(b.c.iter().rev()));
                assert_eq!(sorted, all);
                assert!(all.iter().all(|g| g.deg() == d as isize && g.is_monic()));
            }
        }
        assert_eq!(Poly::count_monic_irreducibles(1, 5), 5);
        assert_eq!(Poly::count_monic_irreducibles(6, 2), 9);
    }

    #[test]
    fn squarefree_and_factor() {
        let mut rng = StdRng::seed_from_u64(14);
        for &p in &TEST_PRIMES {
            let f = field(p);
            for trial in 0..12 {
                // random product of random irreducibles with repeated factors
                let mut facs: Vec<(Poly, usize)> = Vec::new();
                let mut total = 0usize;
                while total < 60 && facs.len() < 8 {
                    let d = rng.gen_range(1..=14usize);
                    let e = rng.gen_range(1..=if p == 2 { 5 } else { 3 }) as usize;
                    if total + d * e > 60 {
                        break;
                    }
                    let g = Poly::random_irreducible(d, &f, &mut rng);
                    if facs.iter().any(|(h, _)| *h == g) {
                        continue;
                    }
                    total += d * e;
                    facs.push((g, e));
                }
                let lc = f.random_nonzero(&mut rng);
                let prod = product(&facs, &f).mul_scalar(lc, &f);
                let mut want = facs.clone();
                want.sort_by(|a, b| (a.0.degree(), &a.0.c).cmp(&(b.0.degree(), &b.0.c)));
                let got = prod.factor(&f, &mut rng);
                assert_eq!(got, want, "p={p} trial={trial}");
                for (g, _) in &got {
                    assert!(g.is_irreducible(&f));
                }
                assert_eq!(product(&got, &f).mul_scalar(lc, &f), prod);

                // SFD reconstructs
                let sfd = prod.squarefree_decomposition(&f);
                assert_eq!(product(&sfd, &f).mul_scalar(lc, &f), prod);
                for (g, _) in &sfd {
                    assert!(g.is_squarefree(&f) && g.is_monic());
                }

                // DDF degrees agree with the known factorization
                let sqf = product(
                    &facs.iter().map(|(g, _)| (g.clone(), 1)).collect::<Vec<_>>(),
                    &f,
                );
                let ddf = sqf.distinct_degree_factorization(&f);
                let mut prev = 0;
                for (d, g) in &ddf {
                    assert!(*d > prev);
                    prev = *d;
                    let expect: usize = facs
                        .iter()
                        .filter(|(h, _)| h.deg() == *d as isize)
                        .map(|_| *d)
                        .sum();
                    assert_eq!(g.deg() as usize, expect);
                    assert!(expect > 0);
                }
                let tot: usize = ddf.iter().map(|(_, g)| g.deg() as usize).sum();
                assert_eq!(tot, sqf.deg() as usize);

                // smoothness and max degree agree with factor()
                let maxd = got.iter().map(|(g, _)| g.degree().unwrap()).max();
                assert_eq!(prod.max_irreducible_degree(&f), maxd);
                if let Some(m) = maxd {
                    for b in 0..=m + 1 {
                        assert_eq!(prod.is_smooth(b, &f), m <= b, "p={p} bound={b}");
                    }
                }
            }
        }
        let f = field(5);
        let mut rng = StdRng::seed_from_u64(1);
        assert!(Poly::constant(3).factor(&f, &mut rng).is_empty());
        assert!(Poly::zero().factor(&f, &mut rng).is_empty());
        assert!(Poly::constant(3).is_smooth(0, &f));
        assert!(!Poly::zero().is_smooth(100, &f));
        assert_eq!(Poly::constant(3).max_irreducible_degree(&f), None);
    }

    #[test]
    fn p_th_powers() {
        // (x^2+x+1)^p in char p is a p-th power with zero derivative
        let mut rng = StdRng::seed_from_u64(15);
        for &p in &[2u64, 3, 5, 7] {
            let f = field(p);
            let g = Poly::random_irreducible(3, &f, &mut rng);
            let mut h = Poly::one();
            for _ in 0..p {
                h = h.mul(&g, &f);
            }
            assert!(h.derivative(&f).is_zero());
            assert!(!h.is_squarefree(&f));
            assert_eq!(
                h.squarefree_decomposition(&f),
                vec![(g.clone(), p as usize)]
            );
            assert_eq!(h.factor(&f, &mut rng), vec![(g.clone(), p as usize)]);
            let g2 = g.mul(&g, &f);
            assert!(!g2.is_squarefree(&f));
        }
    }

    #[test]
    fn random_helpers() {
        let mut rng = StdRng::seed_from_u64(16);
        for &p in &[2u64, 3, 1579] {
            let f = field(p);
            for d in 1..12 {
                assert_eq!(Poly::random_monic(d, &f, &mut rng).deg(), d as isize);
                assert!(Poly::random(d, &f, &mut rng).deg() <= d as isize);
                let s = Poly::random_squarefree_monic(d, &f, &mut rng);
                assert!(s.is_squarefree(&f) && s.is_monic() && s.deg() == d as isize);
                let g = Poly::random_irreducible(d, &f, &mut rng);
                assert!(g.is_irreducible(&f) && g.deg() == d as isize);
            }
        }
    }

    #[test]
    fn edf_direct() {
        let mut rng = StdRng::seed_from_u64(17);
        for &p in &[2u64, 3, 1579] {
            let f = field(p);
            for d in [1usize, 2, 3, 5] {
                let want_n = Poly::count_monic_irreducibles(d, p).min(4) as usize;
                let mut facs: Vec<Poly> = Vec::new();
                while facs.len() < want_n {
                    let g = Poly::random_irreducible(d, &f, &mut rng);
                    if !facs.contains(&g) {
                        facs.push(g);
                    }
                }
                let mut prod = Poly::one();
                for g in &facs {
                    prod = prod.mul(g, &f);
                }
                let mut got = prod.equal_degree_factorization(d, &f, &mut rng);
                got.sort_by(|a, b| a.c.cmp(&b.c));
                facs.sort_by(|a, b| a.c.cmp(&b.c));
                assert_eq!(got, facs, "p={p} d={d}");
            }
        }
    }
}
