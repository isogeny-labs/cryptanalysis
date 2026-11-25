//! Arithmetic in `F_q = F_p[x]/(π)` for an irreducible `π`, and polynomials
//! over `F_q` in a second variable `t`, with root finding.
//!
//! The higher-genus engines need this for places of degree `d > 1`: a place
//! of a hyperelliptic curve above the monic irreducible `π` of degree `d` is
//! a root of `t² = f(x) mod π` in `F_q`; a place of the superelliptic model
//! `y^m = f(x)` above `π` (unramified, residue degree one) is a root of
//! `t^m = f mod π`. Both are the roots of a univariate polynomial over `F_q`,
//! found with a Cantor–Zassenhaus split (odd `q`) or a trace split (`q`
//! even).
//!
//! Elements of `F_q` are [`Poly`]s reduced modulo `π`; nothing here is
//! optimised, the degrees involved are the factor-base bound `B` (≤ ~12).

use num_bigint::BigUint;
use num_traits::{One, Zero};
use rand::RngCore;

use super::fp::Fp;
use super::poly::Poly;

/// The field `F_q = F_p[x]/(π)`.
#[derive(Clone, Debug)]
pub struct Fq {
    /// The prime field.
    pub f: Fp,
    /// Monic irreducible modulus of degree `d ≥ 1`.
    pub pi: Poly,
    /// `q = p^d`.
    pub q: BigUint,
}

impl Fq {
    /// Build `F_p[x]/(π)`; `π` must be monic of degree `≥ 1` (irreducibility
    /// is the caller's responsibility; it is checked in debug builds).
    pub fn new(f: Fp, pi: Poly) -> Self {
        debug_assert!(pi.is_monic() && pi.deg() >= 1);
        debug_assert!(pi.is_irreducible(&f));
        let d = pi.degree().unwrap_or(0) as u32;
        let q = BigUint::from(f.p()).pow(d);
        Self { f, pi, q }
    }

    /// Extension degree `d`.
    pub fn degree(&self) -> usize {
        self.pi.degree().unwrap_or(0)
    }

    /// Reduce a polynomial modulo `π`.
    pub fn reduce(&self, a: &Poly) -> Poly {
        a.rem(&self.pi, &self.f)
    }

    pub fn add(&self, a: &Poly, b: &Poly) -> Poly {
        a.add(b, &self.f)
    }

    pub fn sub(&self, a: &Poly, b: &Poly) -> Poly {
        a.sub(b, &self.f)
    }

    pub fn mul(&self, a: &Poly, b: &Poly) -> Poly {
        Poly::mulmod(a, b, &self.pi, &self.f)
    }

    pub fn pow(&self, a: &Poly, e: &BigUint) -> Poly {
        a.powmod(e, &self.pi, &self.f)
    }

    /// Multiplicative inverse (None for zero).
    pub fn inv(&self, a: &Poly) -> Option<Poly> {
        a.inv_mod(&self.pi, &self.f)
    }

    /// Whether `a` is a square in `F_q` (odd `q`).
    pub fn is_square(&self, a: &Poly) -> bool {
        if a.is_zero() {
            return true;
        }
        if self.f.p() == 2 {
            return true;
        }
        let e = (&self.q - BigUint::one()) >> 1u32;
        self.pow(a, &e).is_one()
    }

    /// A uniformly random element.
    pub fn random(&self, rng: &mut impl RngCore) -> Poly {
        let d = self.degree();
        if d == 0 {
            return Poly::zero();
        }
        Poly::random(d - 1, &self.f, rng)
    }
}

/// A polynomial in `t` with coefficients in `F_q`, ascending, normalised.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ExtPoly {
    pub c: Vec<Poly>,
}

impl ExtPoly {
    pub fn zero() -> Self {
        Self { c: Vec::new() }
    }

    pub fn from_coeffs(mut c: Vec<Poly>, k: &Fq) -> Self {
        for x in c.iter_mut() {
            *x = k.reduce(x);
        }
        let mut s = Self { c };
        s.normalize();
        s
    }

    /// `t^n`.
    pub fn t_pow(n: usize) -> Self {
        let mut c = vec![Poly::zero(); n + 1];
        c[n] = Poly::one();
        Self { c }
    }

    pub fn normalize(&mut self) {
        while matches!(self.c.last(), Some(x) if x.is_zero()) {
            self.c.pop();
        }
    }

    pub fn deg(&self) -> isize {
        self.c.len() as isize - 1
    }

    pub fn is_zero(&self) -> bool {
        self.c.is_empty()
    }

    pub fn is_monic(&self) -> bool {
        matches!(self.c.last(), Some(x) if x.is_one())
    }

    pub fn add(&self, o: &Self, k: &Fq) -> Self {
        let n = self.c.len().max(o.c.len());
        let mut c = Vec::with_capacity(n);
        for i in 0..n {
            let a = self.c.get(i).cloned().unwrap_or_default();
            let b = o.c.get(i).cloned().unwrap_or_default();
            c.push(k.add(&a, &b));
        }
        let mut s = Self { c };
        s.normalize();
        s
    }

    pub fn sub(&self, o: &Self, k: &Fq) -> Self {
        let n = self.c.len().max(o.c.len());
        let mut c = Vec::with_capacity(n);
        for i in 0..n {
            let a = self.c.get(i).cloned().unwrap_or_default();
            let b = o.c.get(i).cloned().unwrap_or_default();
            c.push(k.sub(&a, &b));
        }
        let mut s = Self { c };
        s.normalize();
        s
    }

    pub fn mul(&self, o: &Self, k: &Fq) -> Self {
        if self.is_zero() || o.is_zero() {
            return Self::zero();
        }
        let mut c = vec![Poly::zero(); self.c.len() + o.c.len() - 1];
        for (i, a) in self.c.iter().enumerate() {
            if a.is_zero() {
                continue;
            }
            for (j, b) in o.c.iter().enumerate() {
                if b.is_zero() {
                    continue;
                }
                let prod = k.mul(a, b);
                c[i + j] = k.add(&c[i + j], &prod);
            }
        }
        let mut s = Self { c };
        s.normalize();
        s
    }

    pub fn mul_scalar(&self, s: &Poly, k: &Fq) -> Self {
        let c = self.c.iter().map(|a| k.mul(a, s)).collect();
        let mut r = Self { c };
        r.normalize();
        r
    }

    /// Make monic (nonzero input).
    pub fn monic(&self, k: &Fq) -> Self {
        if self.is_zero() {
            return self.clone();
        }
        let lc = self.c.last().unwrap();
        if lc.is_one() {
            return self.clone();
        }
        let inv = k.inv(lc).expect("leading coefficient is a unit");
        self.mul_scalar(&inv, k)
    }

    /// Remainder modulo a nonzero divisor.
    pub fn rem(&self, d: &Self, k: &Fq) -> Self {
        assert!(!d.is_zero(), "division by zero ExtPoly");
        let dd = d.c.len() - 1;
        if self.c.len() < d.c.len() {
            return self.clone();
        }
        let lc_inv = k
            .inv(d.c.last().unwrap())
            .expect("leading coefficient is a unit");
        let mut r = self.c.clone();
        let mut i = r.len();
        while i > dd {
            i -= 1;
            if r[i].is_zero() {
                continue;
            }
            let q = k.mul(&r[i], &lc_inv);
            let shift = i - dd;
            for j in 0..=dd {
                let sub = k.mul(&q, &d.c[j]);
                r[shift + j] = k.sub(&r[shift + j], &sub);
            }
        }
        r.truncate(dd);
        let mut s = Self { c: r };
        s.normalize();
        s
    }

    pub fn mulmod(a: &Self, b: &Self, m: &Self, k: &Fq) -> Self {
        a.mul(b, k).rem(m, k)
    }

    pub fn powmod(&self, e: &BigUint, m: &Self, k: &Fq) -> Self {
        let mut result = Self::from_coeffs(vec![Poly::one()], k).rem(m, k);
        if e.is_zero() {
            return result;
        }
        let base = self.rem(m, k);
        let bits = e.bits();
        for i in (0..bits).rev() {
            result = Self::mulmod(&result, &result, m, k);
            if e.bit(i) {
                result = Self::mulmod(&result, &base, m, k);
            }
        }
        result
    }

    /// Monic gcd.
    pub fn gcd(&self, o: &Self, k: &Fq) -> Self {
        let mut a = self.clone();
        let mut b = o.clone();
        while !b.is_zero() {
            let r = a.rem(&b, k);
            a = b;
            b = r;
        }
        a.monic(k)
    }

    /// Exact quotient by a monic divisor known to divide (remainder discarded).
    pub fn quo_monic(&self, d: &Self, k: &Fq) -> Self {
        assert!(d.is_monic());
        let dd = d.c.len() - 1;
        if self.c.len() < d.c.len() {
            return Self::zero();
        }
        let mut r = self.c.clone();
        let mut q = vec![Poly::zero(); r.len() - dd];
        let mut i = r.len();
        while i > dd {
            i -= 1;
            let coef = r[i].clone();
            if coef.is_zero() {
                continue;
            }
            let shift = i - dd;
            q[shift] = coef.clone();
            for j in 0..=dd {
                let sub = k.mul(&coef, &d.c[j]);
                r[shift + j] = k.sub(&r[shift + j], &sub);
            }
        }
        let mut s = Self { c: q };
        s.normalize();
        s
    }

    /// Evaluate at `a ∈ F_q`.
    pub fn eval(&self, a: &Poly, k: &Fq) -> Poly {
        let mut acc = Poly::zero();
        for c in self.c.iter().rev() {
            acc = k.add(&k.mul(&acc, a), c);
        }
        acc
    }

    /// All distinct roots in `F_q` of this polynomial (any degree ≥ 1).
    pub fn roots(&self, k: &Fq, rng: &mut impl RngCore) -> Vec<Poly> {
        if self.deg() < 1 {
            return Vec::new();
        }
        let m = self.monic(k);
        // g = gcd(m, t^q - t): the product of the distinct linear factors.
        let t = Self::t_pow(1);
        let tq = t.powmod(&k.q, &m, k);
        let tq_minus_t = tq.sub(&t, k);
        let g = m.gcd(&tq_minus_t, k);
        let mut out = Vec::new();
        Self::split_linear(&g, k, rng, &mut out);
        out.sort_by(|a, b| a.c.cmp(&b.c));
        out.dedup();
        out
    }

    /// Equal-degree splitting of a product of distinct linear factors.
    fn split_linear(g: &Self, k: &Fq, rng: &mut impl RngCore, out: &mut Vec<Poly>) {
        match g.deg() {
            d if d < 1 => {}
            1 => {
                // g = t + c0 → root −c0
                let root = k.sub(&Poly::zero(), &g.c[0]);
                out.push(root);
            }
            _ => {
                let mut attempts = 0;
                loop {
                    attempts += 1;
                    assert!(attempts < 10_000, "equal-degree splitting did not converge");
                    let a = k.random(rng);
                    let h = if k.f.p() == 2 {
                        // Trace split: Tr(c·t) = Σ_{i<log2 q} (c t)^{2^i} for a random c ≠ 0.
                        let mut c = a;
                        if c.is_zero() {
                            c = Poly::one();
                        }
                        let ct = Self::from_coeffs(vec![Poly::zero(), c], k);
                        let bits = k.q.bits() - 1; // q = 2^bits
                        let mut acc = Self::zero();
                        let mut cur = ct.rem(g, k);
                        for _ in 0..bits {
                            acc = acc.add(&cur, k);
                            cur = Self::mulmod(&cur, &cur, g, k);
                        }
                        acc
                    } else {
                        let shifted = Self::from_coeffs(vec![a, Poly::one()], k); // t + a
                        let e = (&k.q - BigUint::one()) >> 1u32;
                        let pw = shifted.powmod(&e, g, k);
                        pw.sub(&Self::from_coeffs(vec![Poly::one()], k), k)
                    };
                    let d = g.gcd(&h, k);
                    if d.deg() >= 1 && d.deg() < g.deg() {
                        let other = g.quo_monic(&d, k);
                        Self::split_linear(&d, k, rng, out);
                        Self::split_linear(&other, k, rng, out);
                        return;
                    }
                }
            }
        }
    }
}

/// Roots `r ∈ F_q` of `t^m = c` (all of them), `c ∈ F_q`.
pub fn mth_roots(c: &Poly, m: u32, k: &Fq, rng: &mut impl RngCore) -> Vec<Poly> {
    let mut coeffs = vec![Poly::zero(); m as usize + 1];
    coeffs[0] = k.sub(&Poly::zero(), c);
    coeffs[m as usize] = Poly::one();
    ExtPoly::from_coeffs(coeffs, k).roots(k, rng)
}

#[cfg(test)]
mod tests {
    use super::*;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    #[test]
    fn roots_in_extension_fields() {
        let mut rng = StdRng::seed_from_u64(7);
        for &p in &[2u64, 3, 7, 1579] {
            let f = Fp::new(p).unwrap();
            for d in 1..=3usize {
                let pi = Poly::random_irreducible(d, &f, &mut rng);
                let k = Fq::new(f, pi);
                // Build ∏ (t − r_i) for random distinct r_i and recover them.
                let mut rs: Vec<Poly> = (0..3).map(|_| k.random(&mut rng)).collect();
                rs.sort_by(|a, b| a.c.cmp(&b.c));
                rs.dedup();
                let mut poly = ExtPoly::from_coeffs(vec![Poly::one()], &k);
                for r in &rs {
                    let lin = ExtPoly::from_coeffs(vec![k.sub(&Poly::zero(), r), Poly::one()], &k);
                    poly = poly.mul(&lin, &k);
                }
                let found = poly.roots(&k, &mut rng);
                assert_eq!(found, rs, "p={p} d={d}");
                // Squares: r^2 has the roots ±r.
                if p != 2 {
                    let r = k.random(&mut rng);
                    let sq = k.mul(&r, &r);
                    let roots = mth_roots(&sq, 2, &k, &mut rng);
                    assert!(roots.contains(&r));
                    assert!(k.is_square(&sq));
                }
                // Cubes.
                let r = k.random(&mut rng);
                let cube = k.mul(&k.mul(&r, &r), &r);
                let roots = mth_roots(&cube, 3, &k, &mut rng);
                assert!(roots.contains(&r), "p={p} d={d}");
            }
        }
    }
}
