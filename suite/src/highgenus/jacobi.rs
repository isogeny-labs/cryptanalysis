//! Exact `#Jac(C)(F_p)` for two families of curves whose zeta function is
//! given by Jacobi sums (Weil 1949), with a unique point at infinity on the
//! smooth model:
//!
//! - family A, [`JacobiSumCurve::PowerSum`]: `y^m = x^n + a`,
//!   `gcd(m, n) = 1`, `p ≡ 1 (mod m·n)`, genus `(m − 1)(n − 1)/2`;
//! - family B, [`JacobiSumCurve::ThreePoint`]: `y^m = x^a (1 − x)^b`,
//!   `gcd(a, m) = gcd(b, m) = gcd(a + b, m) = 1` (so `m` is odd),
//!   `p ≡ 1 (mod m)`, genus `(m − 1)/2`.
//!
//! ## Conventions (checked numerically by the tests in this file)
//!
//! Fix a generator `g` of `F_p^*` and `L` = [`JacobiSumCurve::required_modulus`].
//! The character of index `i ∈ Z/L` is `χ_i(g^k) = ζ_L^{i·k}`, with
//! `χ_i(0) = 0` for `i ≠ 0`. `J(χ_i, χ_j) = Σ_t χ_i(t) χ_j(1 − t)`.
//!
//! - A: with `ψ = χ_{m·r}` (`r = 1..n−1`, the `ψ^n = 1` characters) and
//!   `χ = χ_{n·s}` (`s = 1..m−1`, the `χ^m = 1` characters), the affine count
//!   is `p + Σ χ(a) ψ(−a) J(ψ, χ)` and `#C(F_p)` adds the single point at
//!   infinity. Frobenius eigenvalues `α = −χ(a) ψ(−a) J(ψ, χ)`.
//! - B: the affine (singular) model has `p + Σ_{k≠0} J(χ_k^a, χ_k^b)`
//!   points (one each over `x = 0` and `x = 1`, which are also the single
//!   rational places of the smooth model above those points because
//!   `gcd(a, m) = gcd(b, m) = 1`); `#C(F_p)` adds the place at infinity.
//!   Eigenvalues `α_k = −J(χ_k^a, χ_k^b)`.
//!
//! In both cases `#Jac(F_p) = L(1) = ∏ (1 − α)`. Every factor `1 − α` is an
//! element of the group ring `Z[Z/L]` (index = exponent of `ζ_L`), computed
//! exactly as a histogram over residues mod `L`. Factors are multiplied over
//! each Galois orbit (the action `ζ ↦ ζ^u`, `u ∈ (Z/L)^*`, which permutes
//! the index set), the orbit product is reduced modulo the cyclotomic
//! polynomial `Φ_L`, and the remainder is required to be a positive
//! constant: a non-constant remainder is reported as
//! [`HgError::BadCurve`], which catches convention errors. The order is the
//! product of the orbit norms.
//!
//! Cost: a discrete-log table of `2p` bytes and `O(p)` work per character
//! sum (or `O(p + L²)` via a joint histogram when `L² < p`), then
//! `O(2g · L²)` big-integer additions for the products.

use super::HgError;
use num_bigint::{BigInt, BigUint, Sign};
use num_integer::Integer;
use num_traits::{One, ToPrimitive, Zero};
use rayon::prelude::*;
use std::collections::HashMap;

/// Which family and parameters.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum JacobiSumCurve {
    /// `y^m = x^n + a` (family A).
    PowerSum {
        /// Exponent of `y`.
        m: u32,
        /// Exponent of `x`.
        n: u32,
        /// Constant term, nonzero mod `p`.
        a: u64,
    },
    /// `y^m = x^a (1 − x)^b` (family B).
    ThreePoint {
        /// Exponent of `y` (odd, `≥ 3`).
        m: u32,
        /// Exponent of `x`.
        a: u32,
        /// Exponent of `1 − x`.
        b: u32,
    },
}

fn gcd_u64(mut a: u64, mut b: u64) -> u64 {
    while b != 0 {
        let t = a % b;
        a = b;
        b = t;
    }
    a
}

fn mulmod(a: u64, b: u64, m: u64) -> u64 {
    ((a as u128 * b as u128) % m as u128) as u64
}

fn powmod(mut b: u64, mut e: u64, m: u64) -> u64 {
    let mut r = 1 % m;
    b %= m;
    while e > 0 {
        if e & 1 == 1 {
            r = mulmod(r, b, m);
        }
        b = mulmod(b, b, m);
        e >>= 1;
    }
    r
}

/// Deterministic Miller–Rabin primality test for all `u64`
/// (bases 2, 3, 5, …, 37 are a proven witness set below `3.3·10^24`).
pub fn is_prime_u64(n: u64) -> bool {
    const BASES: [u64; 12] = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37];
    if n < 2 {
        return false;
    }
    for &q in &BASES {
        if n == q {
            return true;
        }
        if n.is_multiple_of(q) {
            return false;
        }
    }
    let mut d = n - 1;
    let mut s = 0;
    while d.is_multiple_of(2) {
        d /= 2;
        s += 1;
    }
    'outer: for &a in &BASES {
        let mut x = powmod(a, d, n);
        if x == 1 || x == n - 1 {
            continue;
        }
        for _ in 1..s {
            x = mulmod(x, x, n);
            if x == n - 1 {
                continue 'outer;
            }
        }
        return false;
    }
    true
}

/// Distinct prime factors of `n` by trial division (`n < 2^64`, small in practice).
fn prime_factors_u64(mut n: u64) -> Vec<u64> {
    let mut out = Vec::new();
    let mut q = 2u64;
    while q.saturating_mul(q) <= n {
        if n.is_multiple_of(q) {
            out.push(q);
            while n.is_multiple_of(q) {
                n /= q;
            }
        }
        q += if q == 2 { 1 } else { 2 };
    }
    if n > 1 {
        out.push(n);
    }
    out
}

fn primitive_root(p: u64) -> u64 {
    let fac = prime_factors_u64(p - 1);
    (2..p)
        .find(|&g| fac.iter().all(|&q| powmod(g, (p - 1) / q, p) != 1))
        .unwrap_or(1)
}

impl JacobiSumCurve {
    /// Genus of the smooth projective model, after checking the parameter
    /// conditions (`gcd(m, n) = 1`, `m, n ≥ 2` for A; `m ≥ 3`,
    /// `0 < a, b < m`, `gcd(a, m) = gcd(b, m) = gcd(a + b, m) = 1` for B).
    pub fn genus(&self) -> Result<u32, HgError> {
        match *self {
            Self::PowerSum { m, n, .. } => {
                if m < 2 || n < 2 {
                    return Err(HgError::BadCurve("PowerSum needs m, n >= 2"));
                }
                if gcd_u64(m as u64, n as u64) != 1 {
                    return Err(HgError::BadCurve("PowerSum needs gcd(m, n) = 1"));
                }
                let g = (m as u64 - 1) * (n as u64 - 1) / 2;
                u32::try_from(g).map_err(|_| HgError::Unsupported("genus does not fit u32"))
            }
            Self::ThreePoint { m, a, b } => {
                if m < 3 {
                    return Err(HgError::BadCurve("ThreePoint needs m >= 3"));
                }
                if a == 0 || b == 0 || a >= m || b >= m {
                    return Err(HgError::BadCurve("ThreePoint needs 0 < a, b < m"));
                }
                let (m6, a6, b6) = (m as u64, a as u64, b as u64);
                if gcd_u64(a6, m6) != 1 || gcd_u64(b6, m6) != 1 || gcd_u64(a6 + b6, m6) != 1 {
                    return Err(HgError::BadCurve(
                        "ThreePoint needs gcd(a, m) = gcd(b, m) = gcd(a + b, m) = 1",
                    ));
                }
                Ok((m - 1) / 2)
            }
        }
    }

    /// The modulus `L` with `p ≡ 1 (mod L)` required: `m·n` for A, `m` for B.
    /// All Frobenius eigenvalues lie in `Z[ζ_L]`.
    pub fn required_modulus(&self) -> u64 {
        match *self {
            Self::PowerSum { m, n, .. } => m as u64 * n as u64,
            Self::ThreePoint { m, .. } => m as u64,
        }
    }

    /// Check that the curve parameters are valid and `p` is usable: `p` an
    /// odd prime below `2^32`, `p ≡ 1 (mod L)`, `p ∤ m` (and `p ∤ n`),
    /// `a ≢ 0 (mod p)` for A, and `L ≤ 65535` (the discrete-log table is `u16`).
    pub fn validate(&self, p: u64) -> Result<(), HgError> {
        self.genus()?;
        if p == 2 || p >= (1u64 << 32) || !is_prime_u64(p) {
            return Err(HgError::BadPrime(p));
        }
        let l = self.required_modulus();
        if l > u16::MAX as u64 {
            return Err(HgError::Unsupported("required modulus above 65535"));
        }
        if !(p - 1).is_multiple_of(l) {
            return Err(HgError::Unsupported("p is not 1 mod the required modulus"));
        }
        match *self {
            Self::PowerSum { m, n, a } => {
                if (m as u64).is_multiple_of(p) || (n as u64).is_multiple_of(p) {
                    return Err(HgError::BadPrime(p));
                }
                if a.is_multiple_of(p) {
                    return Err(HgError::BadCurve("PowerSum needs a != 0 mod p"));
                }
            }
            Self::ThreePoint { m, .. } => {
                if (m as u64).is_multiple_of(p) {
                    return Err(HgError::BadPrime(p));
                }
            }
        }
        Ok(())
    }

    /// `f(x)` of the model `y^m = f(x)` as ascending coefficients mod `p`:
    /// A: `x^n + a`; B: `x^a (1 − x)^b` expanded.
    pub fn rhs_poly(&self, p: u64) -> Vec<u64> {
        match *self {
            Self::PowerSum { n, a, .. } => {
                let mut f = vec![0u64; n as usize + 1];
                f[0] = a % p;
                f[n as usize] = 1 % p;
                f
            }
            Self::ThreePoint { a, b, .. } => {
                // (1 − x)^b by repeated multiplication by (1 − x).
                let mut q = vec![1 % p];
                for _ in 0..b {
                    let mut next = vec![0u64; q.len() + 1];
                    for (k, &c) in q.iter().enumerate() {
                        next[k] = (next[k] + c) % p;
                        next[k + 1] = (next[k + 1] + p - c) % p;
                    }
                    q = next;
                }
                let mut f = vec![0u64; a as usize];
                f.extend(q);
                f
            }
        }
    }

    /// The factorization of `f` into coprime squarefree pieces with
    /// exponents, for the superelliptic engine: A: `[(x^n + a, 1)]`;
    /// B: `[(x, a), (1 − x, b)]` as ascending coefficients mod `p`.
    pub fn rhs_factored(&self, p: u64) -> Vec<(Vec<u64>, u32)> {
        match *self {
            Self::PowerSum { .. } => vec![(self.rhs_poly(p), 1)],
            Self::ThreePoint { a, b, .. } => {
                vec![(vec![0, 1 % p], a), (vec![1 % p, p - 1], b)]
            }
        }
    }
}

/// Everything the character machinery needs for one `(curve, p)`.
struct Setup {
    p: u64,
    l: usize,
    /// `dlog_g(t) mod L` for `t = 1..p−1` (entry 0 unused).
    tab: Vec<u16>,
    /// Index pairs `(i, j)`: the factor is `1 + ζ^{e0(i,j)} J(χ_i, χ_j)`.
    pairs: Vec<(usize, usize)>,
    /// `e0(i, j) = i·c1 + j·c2 mod L`.
    c1: usize,
    c2: usize,
}

impl Setup {
    fn new(curve: &JacobiSumCurve, p: u64) -> Result<Self, HgError> {
        curve.validate(p)?;
        let l = curve.required_modulus() as usize;
        let g = primitive_root(p);
        let mut tab = vec![0u16; p as usize];
        let mut x = 1u64;
        let mut k = 0usize;
        for _ in 0..p - 1 {
            tab[x as usize] = k as u16;
            k += 1;
            if k == l {
                k = 0;
            }
            x = mulmod(x, g, p);
        }
        let (pairs, c1, c2) = match *curve {
            JacobiSumCurve::PowerSum { m, n, a } => {
                let (m, n) = (m as usize, n as usize);
                let mut pairs = Vec::new();
                for r in 1..n {
                    for s in 1..m {
                        pairs.push(((m * r) % l, (n * s) % l));
                    }
                }
                let a = a % p;
                // ψ = χ_i is evaluated at −a, χ = χ_j at a.
                (
                    pairs,
                    tab[(p - a) as usize] as usize,
                    tab[a as usize] as usize,
                )
            }
            JacobiSumCurve::ThreePoint { m, a, b } => {
                let (a, b) = (a as usize, b as usize);
                let pairs = (1..m as usize)
                    .map(|k| ((a * k) % l, (b * k) % l))
                    .collect();
                (pairs, 0, 0)
            }
        };
        Ok(Self {
            p,
            l,
            tab,
            pairs,
            c1,
            c2,
        })
    }

    /// Histograms over residues mod `L` of `J(χ_i, χ_j)` for every pair.
    fn jacobi_histograms(&self) -> Vec<Vec<i64>> {
        let (p, l) = (self.p as usize, self.l);
        let tab = &self.tab;
        if l * l < p && l <= 4096 {
            // Joint table T[u][v] = #{t ≠ 0, 1 : dlog t ≡ u, dlog(1 − t) ≡ v}.
            let mut joint = vec![0u32; l * l];
            for t in 2..p {
                joint[tab[t] as usize * l + tab[p + 1 - t] as usize] += 1;
            }
            self.pairs
                .par_iter()
                .map(|&(i, j)| {
                    let mut h = vec![0i64; l];
                    for u in 0..l {
                        let iu = (i * u) % l;
                        let row = &joint[u * l..(u + 1) * l];
                        let mut e = iu;
                        for &c in row {
                            h[e] += c as i64;
                            e += j;
                            if e >= l {
                                e -= l;
                            }
                        }
                    }
                    h
                })
                .collect()
        } else {
            self.pairs
                .par_iter()
                .map(|&(i, j)| {
                    let mut h = vec![0i64; l];
                    for t in 2..p {
                        let e = (i * tab[t] as usize + j * tab[p + 1 - t] as usize) % l;
                        h[e] += 1;
                    }
                    h
                })
                .collect()
        }
    }

    /// `ζ^{e0} J(χ_i, χ_j)` (the negated eigenvalue `−α`) for every pair.
    fn neg_eigenvalues(&self) -> Vec<Vec<i64>> {
        let l = self.l;
        self.jacobi_histograms()
            .into_iter()
            .zip(&self.pairs)
            .map(|(h, &(i, j))| {
                let e0 = (i * self.c1 + j * self.c2) % l;
                let mut out = vec![0i64; l];
                for (e, &c) in h.iter().enumerate() {
                    out[(e + e0) % l] = c;
                }
                out
            })
            .collect()
    }

    /// Galois orbits of the pair indices under `(i, j) ↦ (u i, u j)`, `u ∈ (Z/L)^*`.
    fn orbits(&self) -> Vec<Vec<usize>> {
        let l = self.l;
        let pos: HashMap<(usize, usize), usize> = self
            .pairs
            .iter()
            .enumerate()
            .map(|(k, &pr)| (pr, k))
            .collect();
        let units: Vec<usize> = (1..l)
            .filter(|&u| gcd_u64(u as u64, l as u64) == 1)
            .collect();
        let mut seen = vec![false; self.pairs.len()];
        let mut out = Vec::new();
        for start in 0..self.pairs.len() {
            if seen[start] {
                continue;
            }
            let (i, j) = self.pairs[start];
            let mut orbit = Vec::new();
            for &u in &units {
                if let Some(&k) = pos.get(&((u * i) % l, (u * j) % l)) {
                    if !seen[k] {
                        seen[k] = true;
                        orbit.push(k);
                    }
                }
            }
            out.push(orbit);
        }
        out
    }
}

/// `Φ_L` as ascending integer coefficients (monic, degree `φ(L)`).
fn cyclotomic(l: usize) -> Result<Vec<i64>, HgError> {
    let primes = prime_factors_u64(l as u64);
    let rad: usize = primes.iter().map(|&q| q as usize).product();
    let deg_r: usize = primes.iter().map(|&q| q as usize - 1).product();
    // Φ_rad = ∏_{d | rad} (1 − x^d)^{μ(rad/d)} as a power series truncated
    // to degree φ(rad) (the overall sign is +1 for rad > 1).
    let mut c = vec![0i128; deg_r + 1];
    c[0] = 1;
    let nd = primes.len();
    let mut muls = Vec::new();
    let mut divs = Vec::new();
    for mask in 0u32..(1 << nd) {
        let d: usize = (0..nd)
            .filter(|&b| mask & (1 << b) != 0)
            .map(|b| primes[b] as usize)
            .product();
        // μ(rad/d) = (−1)^{#primes not in d}.
        if (nd - mask.count_ones() as usize).is_multiple_of(2) {
            muls.push(d);
        } else {
            divs.push(d);
        }
    }
    let overflow = HgError::Unsupported("cyclotomic coefficient overflow");
    for &d in &muls {
        for k in (d..=deg_r).rev() {
            c[k] = c[k].checked_sub(c[k - d]).ok_or(overflow.clone())?;
        }
    }
    for &d in &divs {
        for k in d..=deg_r {
            c[k] = c[k].checked_add(c[k - d]).ok_or(overflow.clone())?;
        }
    }
    let step = l / rad;
    let mut out = vec![0i64; deg_r * step + 1];
    for (k, &v) in c.iter().enumerate() {
        out[k * step] = i64::try_from(v).map_err(|_| overflow.clone())?;
    }
    Ok(out)
}

/// Reduce a group-ring element (`L` coefficients, i.e. mod `x^L − 1`)
/// modulo `Φ_L`; returns the remainder of degree `< φ(L)`.
fn reduce_mod_cyclotomic(poly: &[BigInt], phi: &[i64]) -> Vec<BigInt> {
    let d = phi.len() - 1;
    let mut r: Vec<BigInt> = poly.to_vec();
    for k in (d..r.len()).rev() {
        if r[k].is_zero() {
            continue;
        }
        let c = std::mem::take(&mut r[k]);
        for (t, &ph) in phi[..d].iter().enumerate() {
            if ph != 0 {
                r[k - d + t] -= &c * ph;
            }
        }
    }
    r.truncate(d.min(r.len()));
    r
}

/// The constant of a reduced element, or `BadCurve` if it is not constant.
fn constant_of(poly: &[BigInt], phi: &[i64]) -> Result<BigInt, HgError> {
    let r = reduce_mod_cyclotomic(poly, phi);
    if r.iter().skip(1).any(|c| !c.is_zero()) {
        return Err(HgError::BadCurve(
            "Jacobi-sum product is not rational: convention error",
        ));
    }
    Ok(r.into_iter().next().unwrap_or_default())
}

/// Multiply a big group-ring element by a small one (cyclic convolution of
/// length `L`), grouping the small factor's residues by value so the inner
/// loop is in-place additions.
fn cyclic_mul(acc: &[BigInt], small: &[i64]) -> Vec<BigInt> {
    let l = small.len();
    let mut groups: HashMap<i64, Vec<usize>> = HashMap::new();
    for (e, &v) in small.iter().enumerate() {
        if v != 0 {
            groups.entry(v).or_default().push(e);
        }
    }
    let mut groups: Vec<(i64, Vec<usize>)> = groups.into_iter().collect();
    groups.sort_unstable();
    (0..l)
        .into_par_iter()
        .map(|k| {
            let mut total = BigInt::zero();
            for (v, es) in &groups {
                let mut s = BigInt::zero();
                for &e in es {
                    s += &acc[(k + l - e) % l];
                }
                if *v != 1 {
                    s *= *v;
                }
                total += s;
            }
            total
        })
        .collect()
}

/// Number of `F_p` points of the smooth projective curve (one point at
/// infinity), from the same Jacobi-sum machinery as [`jacobian_order`]:
/// `p + 1 + Σ ζ^{e0} J(χ_i, χ_j)`. Use it to cross-check against
/// [`curve_point_count_bruteforce`].
pub fn curve_point_count(curve: &JacobiSumCurve, p: u64) -> Result<u64, HgError> {
    let setup = Setup::new(curve, p)?;
    let phi = cyclotomic(setup.l)?;
    let mut sum = vec![0i64; setup.l];
    for v in setup.neg_eigenvalues() {
        for (s, x) in sum.iter_mut().zip(v) {
            *s += x;
        }
    }
    let poly: Vec<BigInt> = sum.into_iter().map(BigInt::from).collect();
    let c: BigInt = constant_of(&poly, &phi)? + BigInt::from(p) + 1u32;
    c.to_u64()
        .ok_or(HgError::BadCurve("negative point count: convention error"))
}

/// Brute-force point count of the smooth projective model: the affine
/// count `Σ_x #{y : y^m = f(x)}` (with the `m`-th power map tabulated) plus
/// the single point at infinity. For `p ≤ 2^20`.
pub fn curve_point_count_bruteforce(curve: &JacobiSumCurve, p: u64) -> Result<u64, HgError> {
    curve.validate(p)?;
    if p > 1 << 20 {
        return Err(HgError::Unsupported("brute-force count needs p <= 2^20"));
    }
    let m = match *curve {
        JacobiSumCurve::PowerSum { m, .. } | JacobiSumCurve::ThreePoint { m, .. } => m as u64,
    };
    let mut roots = vec![0u64; p as usize];
    for y in 0..p {
        roots[powmod(y, m, p) as usize] += 1;
    }
    let mut total = 1u64;
    for x in 0..p {
        let v = match *curve {
            JacobiSumCurve::PowerSum { n, a, .. } => (powmod(x, n as u64, p) + a % p) % p,
            JacobiSumCurve::ThreePoint { a, b, .. } => mulmod(
                powmod(x, a as u64, p),
                powmod((p + 1 - x) % p, b as u64, p),
                p,
            ),
        };
        total += roots[v as usize];
    }
    Ok(total)
}

/// Exact `#Jac(C)(F_p) = ∏ (1 − α)` over the `2g` Frobenius eigenvalues.
pub fn jacobian_order(curve: &JacobiSumCurve, p: u64) -> Result<BigUint, HgError> {
    jacobian_order_with_orbit_norms(curve, p).map(|(order, _)| order)
}

/// Exact `#Jac(C)(F_p)` together with the norms `N(1 − α)` over the Galois
/// orbits of the eigenvalue index set (orbits under `ζ_L ↦ ζ_L^u`,
/// `u ∈ (Z/L)^*`). Each orbit norm is a positive integer and their product
/// is the order, which often factors the order for free.
pub fn jacobian_order_with_orbit_norms(
    curve: &JacobiSumCurve,
    p: u64,
) -> Result<(BigUint, Vec<BigUint>), HgError> {
    let setup = Setup::new(curve, p)?;
    let phi = cyclotomic(setup.l)?;
    let factors: Vec<Vec<i64>> = setup
        .neg_eigenvalues()
        .into_iter()
        .map(|mut v| {
            v[0] += 1;
            v
        })
        .collect();
    let mut norms = Vec::new();
    let mut order = BigUint::one();
    for orbit in setup.orbits() {
        let mut acc: Vec<BigInt> = factors[orbit[0]].iter().map(|&c| BigInt::from(c)).collect();
        for &k in &orbit[1..] {
            acc = cyclic_mul(&acc, &factors[k]);
        }
        let c = constant_of(&acc, &phi)?;
        if c.sign() != Sign::Plus {
            return Err(HgError::BadCurve(
                "orbit norm is not positive: convention error",
            ));
        }
        let c = c.magnitude().clone();
        order *= &c;
        norms.push(c);
    }
    Ok((order, norms))
}

fn small_primes(limit: u32) -> Vec<u32> {
    let n = limit as usize;
    let mut sieve = vec![true; n];
    let mut out = Vec::new();
    for i in 2..n {
        if sieve[i] {
            out.push(i as u32);
            let mut k = i * i;
            while k < n {
                sieve[k] = false;
                k += i;
            }
        }
    }
    out
}

/// Probabilistic Miller–Rabin on `BigUint` (deterministic for `n < 2^64`,
/// otherwise 20 fixed small-prime bases).
pub fn is_probable_prime_big(n: &BigUint) -> bool {
    if let Some(v) = n.to_u64() {
        return is_prime_u64(v);
    }
    if n.is_even() {
        return false;
    }
    let one = BigUint::one();
    let nm1 = n - &one;
    let s = nm1.trailing_zeros().unwrap_or(0);
    let d = &nm1 >> s;
    'outer: for a in small_primes(72).into_iter().take(20) {
        let mut x = BigUint::from(a).modpow(&d, n);
        if x == one || x == nm1 {
            continue;
        }
        for _ in 1..s {
            x = (&x * &x) % n;
            if x == nm1 {
                continue 'outer;
            }
        }
        return false;
    }
    true
}

fn abs_diff_big(a: &BigUint, b: &BigUint) -> BigUint {
    if a >= b {
        a - b
    } else {
        b - a
    }
}

/// Brent's Pollard rho on a composite `n`; consumes `budget` steps.
fn rho_brent(n: &BigUint, budget: &mut u64) -> Option<BigUint> {
    if n.is_even() {
        return Some(BigUint::from(2u32));
    }
    let one = BigUint::one();
    for add in 1u32..16 {
        let c = BigUint::from(add);
        let f = |x: &BigUint| (x * x + &c) % n;
        let mut y = BigUint::from(2u32);
        let mut x = y.clone();
        let mut ys = y.clone();
        let mut q = one.clone();
        let mut g = one.clone();
        let mut r = 1u64;
        const M: u64 = 128;
        while g == one {
            x = y.clone();
            for _ in 0..r {
                y = f(&y);
            }
            let mut k = 0;
            while k < r && g == one {
                ys = y.clone();
                let steps = M.min(r - k);
                if *budget < steps {
                    return None;
                }
                *budget -= steps;
                for _ in 0..steps {
                    y = f(&y);
                    q = (&q * abs_diff_big(&x, &y)) % n;
                }
                g = q.gcd(n);
                k += M;
            }
            r *= 2;
        }
        if &g == n {
            loop {
                if *budget == 0 {
                    return None;
                }
                *budget -= 1;
                ys = f(&ys);
                g = abs_diff_big(&x, &ys).gcd(n);
                if g != one {
                    break;
                }
            }
        }
        if &g != n {
            return Some(g);
        }
    }
    None
}

fn split_big(n: BigUint, budget: &mut u64, found: &mut Vec<BigUint>) {
    if n.is_one() {
        return;
    }
    if is_probable_prime_big(&n) {
        found.push(n);
        return;
    }
    if n.bits() > 100 {
        return;
    }
    if let Some(d) = rho_brent(&n, budget) {
        let co = &n / &d;
        split_big(d, budget, found);
        split_big(co, budget, found);
    }
}

/// Find a prime factor `N` of `order` with `lo ≤ N ≤ hi`: trial division by
/// the primes below `2^22` on each orbit norm (on `order` itself when
/// `orbit_norms` is empty), then a primality test on the cofactor and
/// Brent–Pollard rho (shared budget `max_rho_steps`) on composite cofactors
/// below `2^100`. Returns the largest prime found in range that divides
/// `order`, with the cofactor `order / N`, or `None`.
pub fn find_prime_subgroup_order(
    order: &BigUint,
    orbit_norms: &[BigUint],
    lo: &BigUint,
    hi: &BigUint,
    max_rho_steps: u64,
) -> Option<(BigUint, BigUint)> {
    if order.is_zero() {
        return None;
    }
    let sources: Vec<BigUint> = if orbit_norms.is_empty() {
        vec![order.clone()]
    } else {
        orbit_norms.to_vec()
    };
    let primes = small_primes(1 << 22);
    let mut found: Vec<BigUint> = Vec::new();
    let mut budget = max_rho_steps;
    for src in sources {
        let mut c = src;
        for &q in &primes {
            if c.is_one() {
                break;
            }
            let qq = BigUint::from(q as u64 * q as u64);
            if qq > c {
                break;
            }
            while (&c % q).is_zero() {
                found.push(BigUint::from(q));
                c /= q;
            }
        }
        split_big(c, &mut budget, &mut found);
    }
    found
        .into_iter()
        .filter(|n| n >= lo && n <= hi && (order % n).is_zero())
        .max()
        .map(|n| {
            let co = order / &n;
            (n, co)
        })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn a_curve(m: u32, n: u32, a: u64) -> JacobiSumCurve {
        JacobiSumCurve::PowerSum { m, n, a }
    }
    fn b_curve(m: u32, a: u32, b: u32) -> JacobiSumCurve {
        JacobiSumCurve::ThreePoint { m, a, b }
    }

    #[test]
    fn genus_formulas() {
        for (m, n, g) in [
            (2, 5, 2),
            (2, 7, 3),
            (3, 4, 3),
            (3, 8, 7),
            (4, 5, 6),
            (2, 263, 131),
        ] {
            assert_eq!(a_curve(m, n, 1).genus(), Ok(g), "A({m},{n})");
        }
        assert_eq!(b_curve(11, 1, 2).genus(), Ok(5));
        assert_eq!(b_curve(263, 1, 2).genus(), Ok(131));
        assert!(a_curve(3, 6, 1).genus().is_err());
        assert!(a_curve(1, 5, 1).genus().is_err());
        assert!(b_curve(4, 1, 1).genus().is_err());
        assert!(b_curve(6, 1, 1).genus().is_err());
        assert!(b_curve(9, 3, 1).genus().is_err());
        assert!(b_curve(7, 3, 4).genus().is_err());
        assert!(b_curve(7, 0, 2).genus().is_err());
        assert!(b_curve(7, 7, 2).genus().is_err());
    }

    #[test]
    fn validate_rejects() {
        assert_eq!(
            a_curve(2, 5, 1).validate(13),
            Err(HgError::Unsupported("p is not 1 mod the required modulus"))
        );
        assert_eq!(a_curve(2, 5, 1).validate(21), Err(HgError::BadPrime(21)));
        assert!(matches!(
            a_curve(2, 5, 11).validate(11),
            Err(HgError::BadCurve(_))
        ));
        assert!(a_curve(2, 5, 3).validate(11).is_ok());
        assert_eq!(a_curve(2, 5, 1).required_modulus(), 10);
        assert_eq!(b_curve(11, 1, 2).required_modulus(), 11);
    }

    #[test]
    fn rhs_polys() {
        assert_eq!(a_curve(2, 3, 5).rhs_poly(7), vec![5, 0, 0, 1]);
        // x (1 − x)^2 = x − 2x² + x³ mod 11
        assert_eq!(b_curve(5, 1, 2).rhs_poly(11), vec![0, 1, 9, 1]);
        assert_eq!(
            b_curve(5, 1, 2).rhs_factored(11),
            vec![(vec![0, 1], 1), (vec![1, 10], 2)]
        );
        assert_eq!(
            a_curve(2, 3, 5).rhs_factored(7),
            vec![(vec![5, 0, 0, 1], 1)]
        );
    }

    #[test]
    fn cyclotomic_polys() {
        assert_eq!(cyclotomic(3).unwrap(), vec![1, 1, 1]);
        assert_eq!(cyclotomic(4).unwrap(), vec![1, 0, 1]);
        assert_eq!(cyclotomic(6).unwrap(), vec![1, -1, 1]);
        assert_eq!(cyclotomic(12).unwrap(), vec![1, 0, -1, 0, 1]);
        assert_eq!(cyclotomic(10).unwrap(), vec![1, -1, 1, -1, 1]);
        let c105 = cyclotomic(105).unwrap();
        assert_eq!(c105.len(), 49);
        assert_eq!(c105[7], -2);
    }

    #[test]
    fn point_counts_match_bruteforce() {
        let mut cases: Vec<(JacobiSumCurve, u64)> = Vec::new();
        for p in [11, 31, 41] {
            for a in [1, 2, 3, 5, 7] {
                cases.push((a_curve(2, 5, a), p));
            }
        }
        for p in [13, 37] {
            for a in [1, 2, 5] {
                cases.push((a_curve(3, 4, a), p));
            }
        }
        for a in [1, 3, 10] {
            cases.push((a_curve(2, 7, a), 29));
            cases.push((a_curve(3, 8, a), 73));
        }
        cases.push((b_curve(11, 1, 2), 23));
        cases.push((b_curve(11, 1, 2), 67));
        cases.push((b_curve(11, 3, 5), 67));
        cases.push((b_curve(7, 1, 3), 29));
        cases.push((b_curve(5, 1, 2), 11));
        for (c, p) in cases {
            assert_eq!(
                curve_point_count(&c, p).unwrap(),
                curve_point_count_bruteforce(&c, p).unwrap(),
                "{c:?} p={p}"
            );
        }
    }

    #[test]
    fn genus_one_order_equals_point_count() {
        let mut cases = Vec::new();
        for p in [7u64, 13, 19, 31, 37, 43] {
            for a in 1..p.min(8) {
                cases.push((a_curve(2, 3, a), p));
                cases.push((a_curve(3, 2, a), p));
            }
            cases.push((b_curve(3, 1, 1), p));
        }
        for (c, p) in cases {
            assert_eq!(c.genus(), Ok(1));
            let n = curve_point_count_bruteforce(&c, p).unwrap();
            assert_eq!(
                jacobian_order(&c, p).unwrap(),
                BigUint::from(n),
                "{c:?} p={p}"
            );
        }
    }

    /// `#C(F_{p²})` for `y² = x⁵ + a` by brute force in `F_p[s]/(s² − ν)`.
    fn count_fp2_y2_x5(p: u64, a: u64) -> u64 {
        let nu = (2..p)
            .find(|&v| powmod(v, (p - 1) / 2, p) == p - 1)
            .unwrap();
        let mul = |x: (u64, u64), y: (u64, u64)| {
            (
                (mulmod(x.0, y.0, p) + mulmod(mulmod(x.1, y.1, p), nu, p)) % p,
                (mulmod(x.0, y.1, p) + mulmod(x.1, y.0, p)) % p,
            )
        };
        let pow = |mut b: (u64, u64), mut e: u64| {
            let mut r = (1u64, 0u64);
            while e > 0 {
                if e & 1 == 1 {
                    r = mul(r, b);
                }
                b = mul(b, b);
                e >>= 1;
            }
            r
        };
        let q = p * p;
        let mut total = 1u64; // point at infinity
        for u in 0..p {
            for v in 0..p {
                let x = (u, v);
                let x5 = pow(x, 5);
                let z = ((x5.0 + a) % p, x5.1);
                if z == (0, 0) {
                    total += 1;
                } else if pow(z, (q - 1) / 2) == (1, 0) {
                    total += 2;
                }
            }
        }
        total
    }

    #[test]
    fn genus_two_order_from_l_polynomial() {
        for p in [11u64, 31, 41] {
            for a in [1u64, 2, 3, 6] {
                let c = a_curve(2, 5, a);
                let n1 = curve_point_count_bruteforce(&c, p).unwrap() as i128;
                let n2 = count_fp2_y2_x5(p, a) as i128;
                let pi = p as i128;
                let a1 = n1 - pi - 1;
                let two_a2 = n2 - pi * pi - 1 + a1 * a1;
                assert_eq!(two_a2 % 2, 0);
                let a2 = two_a2 / 2;
                let jac = 1 + a1 + a2 + pi * a1 + pi * pi;
                assert!(jac > 0);
                assert_eq!(
                    jacobian_order(&c, p).unwrap(),
                    BigUint::from(jac as u128),
                    "p={p} a={a}"
                );
            }
        }
    }

    fn check_hasse_weil(c: &JacobiSumCurve, p: u64) -> (BigUint, Vec<BigUint>) {
        let g = c.genus().unwrap() as f64;
        let (order, norms) = jacobian_order_with_orbit_norms(c, p).unwrap();
        let prod = norms.iter().fold(BigUint::one(), |acc, x| acc * x);
        assert_eq!(prod, order);
        // log2 via the top 53 bits.
        let shift = order.bits().saturating_sub(53);
        let top = (&order >> shift).to_f64().unwrap();
        let log_order = top.log2() + shift as f64;
        let sp = (p as f64).sqrt();
        let lo = 2.0 * g * (sp - 1.0).log2();
        let hi = 2.0 * g * (sp + 1.0).log2();
        assert!(
            log_order >= lo - 1e-6 && log_order <= hi + 1e-6,
            "{c:?} p={p}: {log_order} not in [{lo}, {hi}]"
        );
        (order, norms)
    }

    #[test]
    fn hasse_weil_larger() {
        for (c, p) in [
            (a_curve(2, 23, 1), 47),
            (a_curve(2, 47, 1), 283),
            (a_curve(3, 8, 1), 73),
            (a_curve(4, 5, 3), 41),
            (b_curve(11, 1, 2), 23),
            (b_curve(23, 1, 2), 47),
            (b_curve(47, 1, 2), 283),
        ] {
            check_hasse_weil(&c, p);
        }
    }

    #[test]
    fn hasse_weil_genus_131() {
        for (c, p) in [(b_curve(263, 1, 2), 1579u64), (a_curve(2, 263, 1), 1579)] {
            let t = std::time::Instant::now();
            let (order, norms) = check_hasse_weil(&c, p);
            eprintln!(
                "{c:?} p={p}: #Jac has {} bits, {} orbit norms, {:.2?}",
                order.bits(),
                norms.len(),
                t.elapsed()
            );
        }
    }

    #[test]
    fn big_prime_test() {
        assert!(is_probable_prime_big(&BigUint::from(
            18446744073709551557u64
        )));
        let m61 = (BigUint::one() << 61) - 1u32;
        let m89 = (BigUint::one() << 89) - 1u32;
        assert!(is_probable_prime_big(&m89));
        assert!(!is_probable_prime_big(&(&m61 * &m89)));
        assert!(is_prime_u64(4294967291));
        assert!(!is_prime_u64(4294967297));
        // rho splits a 2^61-ish × 2^31-ish product.
        let mut found = Vec::new();
        let mut budget = 1_000_000;
        split_big(&m61 * BigUint::from(2147483647u32), &mut budget, &mut found);
        found.sort();
        assert_eq!(found, vec![BigUint::from(2147483647u32), m61]);
    }

    #[test]
    fn prime_subgroup_found() {
        for (c, p) in [
            (b_curve(11, 1, 2), 23u64),
            (a_curve(2, 23, 1), 47),
            (b_curve(23, 1, 2), 47),
        ] {
            let (order, norms) = jacobian_order_with_orbit_norms(&c, p).unwrap();
            let lo = BigUint::from(2u32);
            let (n, co) = find_prime_subgroup_order(&order, &norms, &lo, &order, 1 << 20)
                .unwrap_or_else(|| panic!("{c:?}: no prime"));
            assert!(is_probable_prime_big(&n));
            assert_eq!(&n * &co, order);
            assert!(n >= lo && n <= order);
            // A narrower window that excludes the largest prime still works or returns None.
            if n > BigUint::from(3u32) {
                let hi = &n - 1u32;
                if let Some((n2, co2)) =
                    find_prime_subgroup_order(&order, &norms, &lo, &hi, 1 << 20)
                {
                    assert!(n2 < n && is_probable_prime_big(&n2));
                    assert_eq!(&n2 * &co2, order);
                }
            }
        }
    }
}
