//! Prime field `F_p` for `p < 2^32`, with Barrett multiplication.
//!
//! Elements are canonical `u64` values in `[0, p)`. Because `p < 2^32`, a
//! product of two canonical elements fits in a `u64`, and reduction uses a
//! precomputed 64-bit reciprocal `m = floor(2^64 / p)`: with
//! `q = floor(x*m / 2^64)` the remainder `x - q*p` lies in `[0, 2p)`, so a
//! single conditional subtraction finishes the job (valid for every
//! `x < 2^64`). No hardware division is used in [`Fp::mul`].

use super::HgError;
use rand::{Rng, RngCore};
use std::collections::HashMap;

/// A prime field `F_p` with `2 <= p < 2^32`.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct Fp {
    p: u64,
    /// `floor(2^64 / p)`.
    m: u64,
    /// `2^64 mod p`.
    r64: u64,
}

fn mulmod_u128(a: u64, b: u64, n: u64) -> u64 {
    ((a as u128 * b as u128) % n as u128) as u64
}

fn powmod_u128(mut a: u64, mut e: u64, n: u64) -> u64 {
    let mut r = 1 % n;
    a %= n;
    while e > 0 {
        if e & 1 == 1 {
            r = mulmod_u128(r, a, n);
        }
        a = mulmod_u128(a, a, n);
        e >>= 1;
    }
    r
}

/// Deterministic Miller-Rabin primality test, exact for every `u64`
/// (bases 2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37).
pub fn is_prime_u64(n: u64) -> bool {
    const BASES: [u64; 12] = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37];
    if n < 2 {
        return false;
    }
    for &b in &BASES {
        if n == b {
            return true;
        }
        if n.rem_euclid(b) == 0 {
            return false;
        }
    }
    let s = (n - 1).trailing_zeros();
    let d = (n - 1) >> s;
    'bases: for &b in &BASES {
        let mut x = powmod_u128(b, d, n);
        if x == 1 || x == n - 1 {
            continue;
        }
        for _ in 1..s {
            x = mulmod_u128(x, x, n);
            if x == n - 1 {
                continue 'bases;
            }
        }
        return false;
    }
    true
}

/// Smallest prime `>= start` with `prime ≡ residue (mod modulus)` and
/// `prime < 2^32`; `None` if there is none (or `modulus == 0`).
pub fn next_prime_congruent(start: u64, modulus: u64, residue: u64) -> Option<u64> {
    const LIMIT: u64 = 1 << 32;
    if modulus == 0 || start >= LIMIT {
        return None;
    }
    let residue = residue % modulus;
    let adj = (residue + modulus - start % modulus) % modulus;
    let mut c = start.checked_add(adj)?;
    while c < LIMIT {
        if is_prime_u64(c) {
            return Some(c);
        }
        c = c.checked_add(modulus)?;
    }
    None
}

fn gcd_u64(mut a: u64, mut b: u64) -> u64 {
    while b != 0 {
        let t = a % b;
        a = b;
        b = t;
    }
    a
}

/// Inverse of `a` modulo `n` (`n >= 2`), or `None` if not coprime.
fn modinv_i128(a: u64, n: u64) -> Option<u64> {
    let (mut r0, mut r1) = (n as i128, (a % n) as i128);
    let (mut t0, mut t1) = (0i128, 1i128);
    while r1 != 0 {
        let q = r0 / r1;
        (r0, r1) = (r1, r0 - q * r1);
        (t0, t1) = (t1, t0 - q * t1);
    }
    if r0 != 1 {
        return None;
    }
    Some(t0.rem_euclid(n as i128) as u64)
}

impl Fp {
    /// The field `F_p`; requires `p` prime with `2 <= p < 2^32`,
    /// otherwise `Err(HgError::BadPrime(p))`.
    pub fn new(p: u64) -> Result<Fp, HgError> {
        if !(2..(1u64 << 32)).contains(&p) || !is_prime_u64(p) {
            return Err(HgError::BadPrime(p));
        }
        let m = ((1u128 << 64) / p as u128) as u64;
        let r64 = (u64::MAX % p + 1) % p;
        Ok(Fp { p, m, r64 })
    }

    /// The characteristic `p`.
    #[inline]
    pub fn p(&self) -> u64 {
        self.p
    }

    /// Whether `p` is odd.
    #[inline]
    pub fn is_odd(&self) -> bool {
        self.p != 2
    }

    /// Barrett reduction of any `x < 2^64`.
    #[inline(always)]
    fn red64(&self, x: u64) -> u64 {
        let q = ((x as u128 * self.m as u128) >> 64) as u64;
        let r = x - q * self.p;
        if r >= self.p {
            r - self.p
        } else {
            r
        }
    }

    /// Canonical representative of a signed integer.
    #[inline]
    pub fn reduce_i64(&self, a: i64) -> u64 {
        (a as i128).rem_euclid(self.p as i128) as u64
    }

    /// Canonical representative of a `u128`.
    #[inline]
    pub fn reduce_u128(&self, a: u128) -> u64 {
        let hi = self.red64((a >> 64) as u64);
        let t = self.red64(hi * self.r64);
        let lo = self.red64(a as u64);
        self.add(t, lo)
    }

    /// `a + b` (canonical inputs).
    #[inline(always)]
    pub fn add(&self, a: u64, b: u64) -> u64 {
        let s = a + b;
        if s >= self.p {
            s - self.p
        } else {
            s
        }
    }

    /// `a - b` (canonical inputs).
    #[inline(always)]
    pub fn sub(&self, a: u64, b: u64) -> u64 {
        if a >= b {
            a - b
        } else {
            a + self.p - b
        }
    }

    /// `-a` (canonical input).
    #[inline(always)]
    pub fn neg(&self, a: u64) -> u64 {
        if a == 0 {
            0
        } else {
            self.p - a
        }
    }

    /// `a * b` by Barrett reduction (canonical inputs).
    #[inline(always)]
    pub fn mul(&self, a: u64, b: u64) -> u64 {
        self.red64(a * b)
    }

    /// `a * b + c` with one reduction (canonical inputs).
    #[inline(always)]
    pub fn mul_add(&self, a: u64, b: u64, c: u64) -> u64 {
        // (p-1)^2 + (p-1) < 2^64 for p < 2^32.
        self.red64(a * b + c)
    }

    /// `a^2`.
    #[inline(always)]
    pub fn sqr(&self, a: u64) -> u64 {
        self.mul(a, a)
    }

    /// `a^e` (`0^0 = 1`).
    pub fn pow(&self, a: u64, mut e: u64) -> u64 {
        let mut base = a;
        let mut r = 1u64;
        while e > 0 {
            if e & 1 == 1 {
                r = self.mul(r, base);
            }
            base = self.sqr(base);
            e >>= 1;
        }
        r
    }

    /// Multiplicative inverse; `None` for `0`.
    pub fn inv(&self, a: u64) -> Option<u64> {
        if a == 0 {
            return None;
        }
        modinv_i128(a, self.p)
    }

    /// `a / b`; `None` if `b == 0`.
    pub fn div(&self, a: u64, b: u64) -> Option<u64> {
        self.inv(b).map(|bi| self.mul(a, bi))
    }

    /// Whether `a` is a square (Euler's criterion); `0` and everything in
    /// characteristic 2 are squares.
    pub fn is_square(&self, a: u64) -> bool {
        if a == 0 || self.p == 2 {
            return true;
        }
        self.pow(a, (self.p - 1) / 2) == 1
    }

    /// Legendre symbol `0, 1, -1` (in characteristic 2 returns `0` for
    /// `0` and `1` otherwise).
    pub fn legendre(&self, a: u64) -> i8 {
        if a == 0 {
            0
        } else if self.is_square(a) {
            1
        } else {
            -1
        }
    }

    /// Some square root of `a` (Tonelli-Shanks), or `None` for a
    /// non-square. The root returned is not canonicalised; see
    /// [`Fp::sqrt_canonical`].
    pub fn sqrt(&self, a: u64) -> Option<u64> {
        let p = self.p;
        if a == 0 {
            return Some(0);
        }
        if p == 2 {
            return Some(a);
        }
        if !self.is_square(a) {
            return None;
        }
        if p % 4 == 3 {
            return Some(self.pow(a, (p + 1) / 4));
        }
        let s = (p - 1).trailing_zeros();
        let q = (p - 1) >> s;
        let mut z = 2;
        while self.is_square(z) {
            z += 1;
        }
        let mut c = self.pow(z, q);
        let mut r = self.pow(a, q.div_ceil(2));
        let mut t = self.pow(a, q);
        let mut m = s;
        while t != 1 {
            let mut i = 0;
            let mut tt = t;
            while tt != 1 {
                tt = self.sqr(tt);
                i += 1;
            }
            let mut b = c;
            for _ in 0..(m - i - 1) {
                b = self.sqr(b);
            }
            r = self.mul(r, b);
            c = self.sqr(b);
            t = self.mul(t, c);
            m = i;
        }
        Some(r)
    }

    /// The smaller of the two square roots, `min(r, p - r)`.
    pub fn sqrt_canonical(&self, a: u64) -> Option<u64> {
        self.sqrt(a).map(|r| r.min(self.neg(r)))
    }

    /// A uniformly random element.
    pub fn random(&self, rng: &mut impl RngCore) -> u64 {
        rng.gen_range(0..self.p)
    }

    /// A uniformly random nonzero element (`p = 2` gives `1`).
    pub fn random_nonzero(&self, rng: &mut impl RngCore) -> u64 {
        rng.gen_range(1..self.p)
    }

    /// A generator of `F_p^*` (the smallest one).
    pub fn primitive_root(&self) -> u64 {
        let p = self.p;
        if p == 2 {
            return 1;
        }
        let mut n = p - 1;
        let mut primes = Vec::new();
        let mut q = 2;
        while q * q <= n {
            if n.rem_euclid(q) == 0 {
                primes.push(q);
                while n.rem_euclid(q) == 0 {
                    n /= q;
                }
            }
            q += 1;
        }
        if n > 1 {
            primes.push(n);
        }
        let mut g = 2;
        loop {
            if primes.iter().all(|&q| self.pow(g, (p - 1) / q) != 1) {
                return g;
            }
            g += 1;
        }
    }

    /// Discrete log of nonzero `a` to base `g` by baby-step giant-step.
    fn dlog_bsgs(&self, a: u64, g: u64) -> Option<u64> {
        let order = self.p - 1;
        let mut m = (order as f64).sqrt() as u64;
        while m * m < order {
            m += 1;
        }
        let mut table: HashMap<u64, u64> = HashMap::with_capacity(m as usize);
        let mut cur = 1u64;
        for j in 0..m {
            table.entry(cur).or_insert(j);
            cur = self.mul(cur, g);
        }
        let giant = self.inv(self.pow(g, m))?;
        let mut gamma = a;
        for i in 0..=m {
            if let Some(&j) = table.get(&gamma) {
                return Some((i * m + j) % order);
            }
            gamma = self.mul(gamma, giant);
        }
        None
    }

    /// Some `x` with `x^n = a`, or `None` if none exists.
    ///
    /// `n = 0` returns `Some(1)` iff `a = 1`. Otherwise, when
    /// `gcd(n, p-1) = 1` this is `a^(n^{-1} mod p-1)`; else a discrete
    /// logarithm of `a` (baby-step giant-step) is solved against `n`.
    pub fn nth_root(&self, a: u64, n: u64) -> Option<u64> {
        let p = self.p;
        if n == 0 {
            return if a == 1 { Some(1) } else { None };
        }
        if a == 0 {
            return Some(0);
        }
        if p == 2 {
            return Some(1);
        }
        let order = p - 1;
        let nn = n % order;
        let g = gcd_u64(nn, order);
        if g == 1 {
            let e = modinv_i128(nn, order)?;
            return Some(self.pow(a, e));
        }
        let g0 = self.primitive_root();
        let d = self.dlog_bsgs(a, g0)?;
        if d % g != 0 {
            return None;
        }
        let m2 = order / g;
        let x = if m2 == 1 {
            0
        } else {
            let inv = modinv_i128((nn / g) % m2, m2)?;
            ((d / g) as u128 * inv as u128 % m2 as u128) as u64
        };
        Some(self.pow(g0, x))
    }

    /// For `p <= 2^24`: `(g, t)` with `g` a generator, `g^{t[a]} = a` for
    /// `a` in `1..p` and `t[0] = u32::MAX`. `None` for larger `p`.
    pub fn elements_dlog_table(&self) -> Option<(u64, Vec<u32>)> {
        if self.p > (1 << 24) {
            return None;
        }
        let g = self.primitive_root();
        let mut t = vec![u32::MAX; self.p as usize];
        let mut x = 1u64;
        for k in 0..(self.p - 1) {
            t[x as usize] = k as u32;
            x = self.mul(x, g);
        }
        Some((g, t))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    const PRIMES: [u64; 8] = [2, 3, 5, 7, 65537, 2147483647, 4294967291, 1579];

    #[test]
    fn bad_primes() {
        for p in [0u64, 1, 4, 9, 561, 1 << 32, 4294967297, (1 << 32) + 15] {
            assert_eq!(Fp::new(p), Err(HgError::BadPrime(p)));
        }
        assert!(Fp::new(4294967291).is_ok());
    }

    #[test]
    fn primality_and_next_prime() {
        let mut sieve = vec![true; 100000];
        sieve[0] = false;
        sieve[1] = false;
        for i in 2..100000 {
            if sieve[i] {
                let mut j = i * i;
                while j < 100000 {
                    sieve[j] = false;
                    j += i;
                }
            }
        }
        for (n, &s) in sieve.iter().enumerate() {
            assert_eq!(is_prime_u64(n as u64), s, "{n}");
        }
        assert!(is_prime_u64(18446744073709551557));
        assert!(!is_prime_u64(18446744073709551557 - 2));
        assert!(!is_prime_u64(3825123056546413051));
        let q = next_prime_congruent(1000, 8, 1).unwrap();
        assert!(is_prime_u64(q) && q >= 1000 && q % 8 == 1);
        for c in 1000..q {
            assert!(c % 8 != 1 || !is_prime_u64(c));
        }
        assert_eq!(next_prime_congruent(10, 1, 0), Some(11));
        assert_eq!(next_prime_congruent(4294967296, 2, 1), None);
        assert_eq!(next_prime_congruent(4294967292, 4, 0), None);
        assert_eq!(next_prime_congruent(5, 0, 0), None);
    }

    #[test]
    fn mul_vs_u128() {
        let mut rng = StdRng::seed_from_u64(1);
        for &p in &[2u64, 3, 4294967291, 65537, 2147483647, 1000003] {
            let f = Fp::new(p).unwrap();
            for _ in 0..1_000_000 {
                let a = rng.gen_range(0..p);
                let b = rng.gen_range(0..p);
                assert_eq!(f.mul(a, b), ((a as u128 * b as u128) % p as u128) as u64);
            }
            // extremes
            for &a in &[0, 1, p - 1] {
                for &b in &[0, 1, p - 1] {
                    assert_eq!(f.mul(a, b), ((a as u128 * b as u128) % p as u128) as u64);
                }
            }
        }
    }

    #[test]
    fn arithmetic_and_reductions() {
        let mut rng = StdRng::seed_from_u64(2);
        for &p in &PRIMES {
            let f = Fp::new(p).unwrap();
            for _ in 0..2000 {
                let a = f.random(&mut rng);
                let b = f.random(&mut rng);
                assert_eq!(f.add(a, b), (a + b) % p);
                assert_eq!(f.sub(a, b), (a + p - b) % p);
                assert_eq!(f.add(f.neg(a), a), 0);
                assert_eq!(f.sqr(a), f.mul(a, a));
                let w: u128 = rng.gen();
                assert_eq!(f.reduce_u128(w), (w % p as u128) as u64);
                let s: i64 = rng.gen();
                assert_eq!(f.reduce_i64(s), (s as i128).rem_euclid(p as i128) as u64);
                assert_eq!(f.reduce_u128(u128::MAX), (u128::MAX % p as u128) as u64);
                assert_eq!(
                    f.reduce_i64(i64::MIN),
                    (i64::MIN as i128).rem_euclid(p as i128) as u64
                );
                assert_eq!(f.pow(a, 0), 1);
                assert_eq!(f.pow(a, 5), f.mul(f.sqr(f.sqr(a)), a));
            }
        }
    }

    #[test]
    fn inverses() {
        let mut rng = StdRng::seed_from_u64(3);
        for &p in &PRIMES {
            let f = Fp::new(p).unwrap();
            assert_eq!(f.inv(0), None);
            assert_eq!(f.div(1, 0), None);
            for _ in 0..2000 {
                let a = f.random_nonzero(&mut rng);
                let b = f.random_nonzero(&mut rng);
                let ai = f.inv(a).unwrap();
                assert_eq!(f.mul(a, ai), 1);
                assert_eq!(f.mul(f.div(a, b).unwrap(), b), a);
                if p > 2 {
                    assert_eq!(f.pow(a, p - 2), ai);
                }
            }
        }
    }

    #[test]
    fn sqrt_roundtrip() {
        // exhaustively in small fields (including p = 1 mod 4, 1 mod 8, 1 mod 16)
        for &p in &[2u64, 3, 5, 7, 13, 17, 41, 97, 193, 257, 1009, 65537] {
            let f = Fp::new(p).unwrap();
            let mut squares = 0;
            for a in 0..p {
                match f.sqrt(a) {
                    Some(r) => {
                        assert_eq!(f.sqr(r), a);
                        assert!(f.is_square(a));
                        let c = f.sqrt_canonical(a).unwrap();
                        assert!(c <= p - c || c == 0);
                        assert_eq!(f.sqr(c), a);
                        squares += 1;
                    }
                    None => assert!(!f.is_square(a)),
                }
                if p > 2 {
                    assert_eq!(f.legendre(a) == -1, !f.is_square(a));
                }
            }
            assert_eq!(squares, if p == 2 { 2 } else { (p as usize - 1) / 2 + 1 });
        }
        let mut rng = StdRng::seed_from_u64(4);
        for &p in &[
            4294967291u64,
            2147483647,
            3221225473, /* 3*2^30+1 */
            4293918721,
        ] {
            if !is_prime_u64(p) {
                continue;
            }
            let f = Fp::new(p).unwrap();
            for _ in 0..500 {
                let a = f.random(&mut rng);
                if let Some(r) = f.sqrt(a) {
                    assert_eq!(f.sqr(r), a);
                } else {
                    assert_eq!(f.legendre(a), -1);
                }
                let r = f.random(&mut rng);
                let s = f.sqr(r);
                assert_eq!(f.sqr(f.sqrt(s).unwrap()), s);
            }
        }
    }

    #[test]
    fn primitive_roots_and_tables() {
        for &p in &[
            2u64, 3, 5, 7, 13, 97, 1009, 65537, 1579, 2147483647, 4294967291,
        ] {
            let f = Fp::new(p).unwrap();
            let g = f.primitive_root();
            if p == 2 {
                assert_eq!(g, 1);
                continue;
            }
            assert_eq!(f.pow(g, p - 1), 1);
            // order is exactly p-1: check against each prime divisor
            let mut n = p - 1;
            let mut q = 2;
            while q * q <= n {
                if n % q == 0 {
                    assert_ne!(f.pow(g, (p - 1) / q), 1);
                    while n % q == 0 {
                        n /= q;
                    }
                }
                q += 1;
            }
            if n > 1 {
                assert_ne!(f.pow(g, (p - 1) / n), 1);
            }
        }
        let f = Fp::new(65537).unwrap();
        let (g, t) = f.elements_dlog_table().unwrap();
        assert_eq!(t[0], u32::MAX);
        for a in 1..65537u64 {
            assert_eq!(f.pow(g, t[a as usize] as u64), a);
        }
        let f2 = Fp::new(2).unwrap();
        let (g2, t2) = f2.elements_dlog_table().unwrap();
        assert_eq!((g2, t2), (1, vec![u32::MAX, 0]));
        assert!(Fp::new(4294967291).unwrap().elements_dlog_table().is_none());
    }

    #[test]
    fn nth_roots() {
        let mut rng = StdRng::seed_from_u64(5);
        for &p in &[
            2u64, 3, 5, 7, 13, 97, 1009, 65537, 1000003, 4294967291, 2147483647,
        ] {
            let f = Fp::new(p).unwrap();
            for &n in &[1u64, 2, 3, 4, 5, 6, 7, 12, 30, 64, 1 << 20, 1_000_000_007] {
                for _ in 0..6 {
                    let x = f.random(&mut rng);
                    let a = f.pow(x, n);
                    let r = f.nth_root(a, n).expect("root of an n-th power");
                    assert_eq!(f.pow(r, n), a, "p={p} n={n} a={a}");
                }
            }
            // non-powers: compare with brute force in a small field
            if p <= 1009 {
                for n in 1..20u64 {
                    for a in 0..p {
                        let exists = (0..p).any(|x| f.pow(x, n) == a);
                        match f.nth_root(a, n) {
                            Some(r) => assert_eq!(f.pow(r, n), a),
                            None => assert!(!exists, "p={p} n={n} a={a}"),
                        }
                    }
                }
            }
        }
        let f = Fp::new(7).unwrap();
        assert_eq!(f.nth_root(1, 0), Some(1));
        assert_eq!(f.nth_root(2, 0), None);
    }
}
