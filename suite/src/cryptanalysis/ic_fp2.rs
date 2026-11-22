//! # The `fp2` regime of `ic bench`: curves over `F_{p²}`.
//!
//! Delaplace–May (NuTMiC 2019, ePrint 2019/800) and Delaplace–Fouque–
//! Kirchner–May (2020) attack ECDLP on `E/F_{p^ℓ}` by writing the
//! unknown as a sum and keeping only partial sums whose abscissa lies
//! in the subfield `F_p`.  This module gives `ic bench` an `F_{p²}`
//! regime so the generic oracles (`subtract`, `mitm`, `rep-join`) and
//! the Gaudry/Diem decomposition for `n = 2` run on such curves with the
//! same counted-cost accounting as the prime and binary regimes.
//!
//! - **Field.** `F_{p²} = F_p[i]/(i² − δ)`, `δ` the smallest quadratic
//!   non-residue of `F_p`; `p < 2^31` so every product fits a `u64`.
//! - **Instance.** `--fp2-bits k`: `p` is the first prime at or above
//!   `2^{k/2}` plus a seeded offset (so `q = p² ≈ 2^k`), `a, b ∈ F_{p²}`
//!   random with non-zero `i`-parts (a generic curve, not defined over
//!   `F_p`), `#E(F_{p²})` by baby-step giant-step in the Hasse interval
//!   on three random points, accepted when `#E = h·r` with `h ≤
//!   max_cofactor` and `r` prime.
//! - **Group.** Affine points, counted exactly as [`PrimeCurve`] counts
//!   them.  `key = ((x₀ + p·x₁ + 1) << 1) | sign(y)`: the abscissa code
//!   `x₀ + p·x₁ < p² < 2^62` is injective, so `key >> 1` names the
//!   abscissa exactly and no hashing is needed.
//! - **Factor base** `fp2-subfield`: the points with abscissa in `F_p`.
//! - **Oracle** `fp2-weil`: `S₃(x₁, x₂, x_R) = 0` with `x₁, x₂ ∈ F_p`,
//!   Weil-restricted to two equations over `F_p` in `e₁ = x₁ + x₂`,
//!   `e₂ = x₁x₂`, `e₂` eliminated (one equation is linear in it), the
//!   quartic in `e₁` solved by `gcd(g, X^p − X)` and Cantor–Zassenhaus.
//!
//! [`PrimeCurve`]: crate::cryptanalysis::ic_boundary::PrimeCurve

use std::collections::BTreeMap;
use std::time::Instant;

use rand::rngs::StdRng;
use rand::{Rng, SeedableRng};
use serde::Serialize;

use crate::cryptanalysis::ic_boundary::{
    fast_map, lift_abscissae, Calibration, CountedGroup, FactorBase, FastMap, GroupOps,
    OracleCounters,
};
use crate::cryptanalysis::ic_framework::stages::{
    DecompositionOracle, FactorBaseBuilder, InstanceCtx, Params,
};
use crate::cryptanalysis::residual_walk::is_prime_u64;

/// An element `x₀ + x₁·i` of `F_{p²}`.
pub type F2 = (u64, u64);

// ── F_p, with a ledger ─────────────────────────────────────────────

/// `F_p` arithmetic that counts what it does: multiplications,
/// inversions and square roots.  Additions are not counted.
#[derive(Clone, Debug, Default)]
pub struct FpWork {
    pub p: u64,
    pub muls: u64,
    pub invs: u64,
    pub sqrts: u64,
}

impl FpWork {
    pub fn new(p: u64) -> Self {
        Self {
            p,
            ..Default::default()
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
    pub fn mul(&mut self, a: u64, b: u64) -> u64 {
        self.muls += 1;
        a * b % self.p
    }
    /// Multiplication by a small constant: an addition chain, not counted.
    #[inline]
    pub fn small(&self, k: u64, a: u64) -> u64 {
        (k % self.p) * a % self.p
    }
    pub fn inv(&mut self, a: u64) -> u64 {
        self.invs += 1;
        fp_inv(a, self.p)
    }
    /// A square root, or `None` for a non-residue.  One counted solve.
    pub fn sqrt(&mut self, a: u64) -> Option<u64> {
        self.sqrts += 1;
        fp_sqrt(a, self.p)
    }
}

#[inline]
fn fp_mul(a: u64, b: u64, p: u64) -> u64 {
    a * b % p
}

fn fp_pow(mut a: u64, mut e: u64, p: u64) -> u64 {
    let mut r = 1u64 % p;
    a %= p;
    while e > 0 {
        if e & 1 == 1 {
            r = fp_mul(r, a, p);
        }
        a = fp_mul(a, a, p);
        e >>= 1;
    }
    r
}

/// Inverse by extended Euclid; `0` maps to `0`.
fn fp_inv(a: u64, p: u64) -> u64 {
    let (mut t, mut new_t) = (0i64, 1i64);
    let (mut r, mut new_r) = (p as i64, (a % p) as i64);
    while new_r != 0 {
        let q = r / new_r;
        (t, new_t) = (new_t, t - q * new_t);
        (r, new_r) = (new_r, r - q * new_r);
    }
    if r != 1 {
        return 0;
    }
    if t < 0 {
        t += p as i64;
    }
    t as u64
}

/// Euler's criterion: `1`, `−1` or `0`.
fn fp_legendre(a: u64, p: u64) -> i32 {
    let a = a % p;
    if a == 0 {
        return 0;
    }
    if fp_pow(a, (p - 1) / 2, p) == 1 {
        1
    } else {
        -1
    }
}

/// Tonelli–Shanks.
fn fp_sqrt(n: u64, p: u64) -> Option<u64> {
    let n = n % p;
    if n == 0 {
        return Some(0);
    }
    if fp_pow(n, (p - 1) / 2, p) != 1 {
        return None;
    }
    if p % 4 == 3 {
        return Some(fp_pow(n, (p + 1) / 4, p));
    }
    let mut q = p - 1;
    let mut s = 0u32;
    while q % 2 == 0 {
        q /= 2;
        s += 1;
    }
    let mut z = 2u64;
    while fp_pow(z, (p - 1) / 2, p) != p - 1 {
        z += 1;
    }
    let (mut m, mut c, mut t, mut r) = (s, fp_pow(z, q, p), fp_pow(n, q, p), fp_pow(n, q.div_ceil(2), p));
    loop {
        if t == 1 {
            return Some(r);
        }
        let mut i = 0u32;
        let mut tt = t;
        while tt != 1 {
            tt = fp_mul(tt, tt, p);
            i += 1;
            if i == m {
                return None;
            }
        }
        let b = fp_pow(c, 1u64 << (m - i - 1), p);
        m = i;
        c = fp_mul(b, b, p);
        t = fp_mul(t, c, p);
        r = fp_mul(r, b, p);
    }
}

// ── F_{p²} ──────────────────────────────────────────────────────────

/// `F_p[i]/(i² − δ)`, uncounted (the group's own arithmetic, which the
/// unit prices per addition, as on the prime curve).
#[derive(Clone, Copy, Debug, Serialize)]
pub struct Fp2Field {
    pub p: u64,
    pub delta: u64,
}

impl Fp2Field {
    pub fn new(p: u64) -> Self {
        assert!(p > 2 && p < (1u64 << 31) && is_prime_u64(p));
        let mut delta = 2u64;
        while fp_legendre(delta, p) != -1 {
            delta += 1;
        }
        Self { p, delta }
    }
    #[inline]
    pub fn add(&self, a: F2, b: F2) -> F2 {
        let p = self.p;
        ((a.0 + b.0) % p, (a.1 + b.1) % p)
    }
    #[inline]
    pub fn sub(&self, a: F2, b: F2) -> F2 {
        let p = self.p;
        ((a.0 + p - b.0) % p, (a.1 + p - b.1) % p)
    }
    #[inline]
    pub fn neg(&self, a: F2) -> F2 {
        let p = self.p;
        ((p - a.0) % p, (p - a.1) % p)
    }
    #[inline]
    pub fn mul(&self, a: F2, b: F2) -> F2 {
        let p = self.p;
        let t = a.1 * b.1 % p;
        ((a.0 * b.0 + self.delta * t) % p, (a.0 * b.1 + a.1 * b.0) % p)
    }
    #[inline]
    pub fn sqr(&self, a: F2) -> F2 {
        self.mul(a, a)
    }
    #[inline]
    pub fn scale(&self, k: u64, a: F2) -> F2 {
        let p = self.p;
        let k = k % p;
        (k * a.0 % p, k * a.1 % p)
    }
    /// The norm `x₀² − δx₁² ∈ F_p`.
    #[inline]
    pub fn norm(&self, a: F2) -> u64 {
        let p = self.p;
        (a.0 * a.0 % p + p - self.delta * (a.1 * a.1 % p) % p) % p
    }
    /// `(x₀ − x₁i) / N(x)`; zero maps to zero.
    pub fn inv(&self, a: F2) -> F2 {
        let p = self.p;
        let n = fp_inv(self.norm(a), p);
        (a.0 * n % p, (p - a.1) % p * n % p)
    }
    pub fn is_square(&self, a: F2) -> bool {
        a == (0, 0) || fp_legendre(self.norm(a), self.p) == 1
    }
    /// A square root in `F_{p²}`, or `None`.
    pub fn sqrt(&self, a: F2) -> Option<F2> {
        let p = self.p;
        if a == (0, 0) {
            return Some((0, 0));
        }
        let candidate = if a.1 == 0 {
            match fp_sqrt(a.0, p) {
                Some(s) => (s, 0),
                // (y·i)² = δy², so y² = a₀/δ.
                None => (0, fp_sqrt(a.0 * fp_inv(self.delta, p) % p, p)?),
            }
        } else {
            let n = fp_sqrt(self.norm(a), p)?;
            let half = fp_inv(2, p);
            let mut x0sq = (a.0 + n) % p * half % p;
            let x0 = match fp_sqrt(x0sq, p) {
                Some(v) if v != 0 => v,
                _ => {
                    x0sq = (a.0 + p - n) % p * half % p;
                    fp_sqrt(x0sq, p)?
                }
            };
            if x0 == 0 {
                return None;
            }
            let x1 = a.1 * fp_inv(2 * x0 % p, p) % p;
            (x0, x1)
        };
        (self.sqr(candidate) == a).then_some(candidate)
    }
    /// Abscissa code `x₀ + p·x₁`, injective below `p² < 2^62`.
    #[inline]
    pub fn code(&self, a: F2) -> u64 {
        a.0 + self.p * a.1
    }
    /// The sign convention: `y` is "high" when it is lexicographically
    /// (by `x₁`, then `x₀`) larger than `−y`.
    #[inline]
    pub fn high(&self, y: F2) -> bool {
        let p = self.p;
        if y.1 != 0 {
            y.1 > p - y.1
        } else {
            y.0 != 0 && y.0 > p - y.0
        }
    }
    pub fn random(&self, rng: &mut StdRng) -> F2 {
        (rng.gen_range(0..self.p), rng.gen_range(0..self.p))
    }
}

// ── The curve and its counted group ────────────────────────────────

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Fp2Point {
    pub x: F2,
    pub y: F2,
    pub infinity: bool,
}

impl Fp2Point {
    pub const INFINITY: Self = Self {
        x: (0, 0),
        y: (0, 0),
        infinity: true,
    };
    pub fn affine(x: F2, y: F2) -> Self {
        Self {
            x,
            y,
            infinity: false,
        }
    }
}

/// `y² = x³ + ax + b` over `F_{p²}`.
#[derive(Clone, Debug, Serialize)]
pub struct Fp2Curve {
    pub field: Fp2Field,
    pub a: F2,
    pub b: F2,
}

impl Fp2Curve {
    pub fn rhs(&self, x: F2) -> F2 {
        let f = &self.field;
        f.add(f.add(f.mul(f.sqr(x), x), f.mul(self.a, x)), self.b)
    }
    pub fn is_on_curve(&self, pt: Fp2Point) -> bool {
        pt.infinity || self.field.sqr(pt.y) == self.rhs(pt.x)
    }
    fn add_raw(&self, a: Fp2Point, b: Fp2Point) -> Fp2Point {
        if a.infinity {
            return b;
        }
        if b.infinity {
            return a;
        }
        let f = &self.field;
        if a.x == b.x {
            if f.add(a.y, b.y) == (0, 0) {
                return Fp2Point::INFINITY;
            }
            return self.double_raw(a);
        }
        let inv = f.inv(f.sub(b.x, a.x));
        let lambda = f.mul(f.sub(b.y, a.y), inv);
        let x3 = f.sub(f.sub(f.sqr(lambda), a.x), b.x);
        let y3 = f.sub(f.mul(lambda, f.sub(a.x, x3)), a.y);
        Fp2Point::affine(x3, y3)
    }
    fn double_raw(&self, a: Fp2Point) -> Fp2Point {
        if a.infinity || a.y == (0, 0) {
            return Fp2Point::INFINITY;
        }
        let f = &self.field;
        let num = f.add(f.scale(3, f.sqr(a.x)), self.a);
        let inv = f.inv(f.scale(2, a.y));
        let lambda = f.mul(num, inv);
        let x3 = f.sub(f.sqr(lambda), f.scale(2, a.x));
        let y3 = f.sub(f.mul(lambda, f.sub(a.x, x3)), a.y);
        Fp2Point::affine(x3, y3)
    }
    /// Uncounted scalar multiplication for instance construction.
    fn mul_raw(&self, p: Fp2Point, k: u64) -> Fp2Point {
        let mut acc = Fp2Point::INFINITY;
        let mut base = p;
        let mut k = k;
        while k > 0 {
            if k & 1 == 1 {
                acc = self.add_raw(acc, base);
            }
            base = self.double_raw(base);
            k >>= 1;
        }
        acc
    }
    /// A random affine point (uncounted).
    pub fn random_point(&self, rng: &mut StdRng) -> Fp2Point {
        loop {
            let x = self.field.random(rng);
            if let Some(y) = self.field.sqrt(self.rhs(x)) {
                let y = if rng.gen::<bool>() { y } else { self.field.neg(y) };
                return Fp2Point::affine(x, y);
            }
        }
    }
    /// Every `M` in `[lo, hi]` with `[M]P = O`, by baby-step giant-step.
    fn killing_multiples(&self, p: Fp2Point, lo: u64, hi: u64) -> Vec<u64> {
        let width = hi - lo + 1;
        let m = ((width as f64).sqrt().ceil() as u64).max(1);
        let mut baby: FastMap<Vec<u64>> = fast_map(m as usize);
        let mut cur = Fp2Point::INFINITY;
        for j in 0..m {
            baby.entry(self.key(&cur)).or_default().push(j);
            cur = self.add_raw(cur, p);
        }
        let step = self.mul_raw(p, m);
        let mut giant = self.mul_raw(p, lo);
        let mut out = Vec::new();
        let mut base = lo;
        while base <= hi {
            // [base + j]P = O  ⇔  [base]P = −[j]P.
            if let Some(js) = baby.get(&self.key(&self.neg(giant))) {
                for &j in js {
                    let cand = base + j;
                    if cand <= hi && self.mul_raw(p, cand).infinity {
                        out.push(cand);
                    }
                }
            }
            giant = self.add_raw(giant, step);
            base += m;
        }
        out.sort_unstable();
        out.dedup();
        out
    }
}

impl CountedGroup for Fp2Curve {
    type Elt = Fp2Point;
    fn identity(&self) -> Fp2Point {
        Fp2Point::INFINITY
    }
    fn is_identity(&self, p: &Fp2Point) -> bool {
        p.infinity
    }
    fn add(&self, ops: &mut GroupOps, p: Fp2Point, q: Fp2Point) -> Fp2Point {
        ops.adds += 1;
        self.add_raw(p, q)
    }
    fn double(&self, ops: &mut GroupOps, p: Fp2Point) -> Fp2Point {
        ops.doubles += 1;
        self.double_raw(p)
    }
    fn neg(&self, p: Fp2Point) -> Fp2Point {
        if p.infinity {
            p
        } else {
            Fp2Point::affine(p.x, self.field.neg(p.y))
        }
    }
    /// The prime-curve convention exactly: `0` for `O`, else the
    /// abscissa code plus one shifted left, the ordinate's sign in the
    /// low bit.  The code is injective, so equal `key >> 1` means equal
    /// abscissa (no false collisions).
    fn key(&self, p: &Fp2Point) -> u64 {
        if p.infinity {
            0
        } else {
            ((self.field.code(p.x) + 1) << 1) | u64::from(self.field.high(p.y))
        }
    }
}

// ── The instance ───────────────────────────────────────────────────

/// An `F_{p²}` instance: curve, prime-order subgroup, generator.
#[derive(Clone, Debug)]
pub struct Fp2Instance {
    pub name: String,
    pub bits: u32,
    pub curve: Fp2Curve,
    pub group_order: u64,
    pub r: u64,
    pub cofactor: u64,
    pub generator: Fp2Point,
    /// Curves tried before this one was accepted (not an attack cost).
    pub curves_tried: u64,
}

impl Fp2Instance {
    pub fn p(&self) -> u64 {
        self.curve.field.p
    }
    pub fn describe(&self) -> serde_json::Value {
        let f = &self.curve.field;
        serde_json::json!({
            "name": self.name,
            "field": {"kind": "fp2", "p": f.p, "delta": f.delta, "q": f.p * f.p,
                      "representation": "F_p[i]/(i^2 - delta), element (x0, x1) = x0 + x1 i"},
            "a": [self.curve.a.0, self.curve.a.1],
            "b": [self.curve.b.0, self.curve.b.1],
            "group_order": self.group_order, "subgroup_order": self.r, "cofactor": self.cofactor,
            "generator": {"x": [self.generator.x.0, self.generator.x.1],
                          "y": [self.generator.y.0, self.generator.y.1]},
            "curves_tried": self.curves_tried,
        })
    }
}

/// **Search an `F_{p²}` curve** whose prime-order subgroup has about
/// `bits` bits: `p` the first prime at or above `⌈2^{bits/2}⌉` plus a
/// seeded offset below `2^{bits/2}/8`, random `a, b` with non-zero
/// `i`-parts, `#E` by baby-step giant-step in the Hasse interval
/// (confirmed on three points: the candidate must be the unique
/// multiple in the interval killing all of them), accepted when `#E =
/// h·r`, `h ≤ max_cofactor`, `r` prime.  Deterministic in the seed.
pub fn find_fp2_curve(bits: u32, seed: u64, max_cofactor: u64) -> Option<Fp2Instance> {
    if !(12..=60).contains(&bits) {
        return None;
    }
    let mut rng = StdRng::seed_from_u64(seed ^ ((bits as u64) << 40) ^ 0xF2F2_0000);
    let base = 2f64.powf(bits as f64 / 2.0).ceil() as u64;
    let mut tried = 0u64;
    for _ in 0..64 {
        let mut p = base + rng.gen_range(0..(base / 8).max(1));
        while !is_prime_u64(p) {
            p += 1;
        }
        if p >= (1u64 << 31) {
            return None;
        }
        let field = Fp2Field::new(p);
        let q = p * p;
        let lo = q + 1 - 2 * p;
        let hi = q + 1 + 2 * p;
        for _ in 0..256 {
            tried += 1;
            let a = (rng.gen_range(0..p), rng.gen_range(1..p));
            let b = (rng.gen_range(0..p), rng.gen_range(1..p));
            // 4a³ + 27b² ≠ 0.
            let disc = field.add(
                field.scale(4, field.mul(field.sqr(a), a)),
                field.scale(27, field.sqr(b)),
            );
            if disc == (0, 0) {
                continue;
            }
            let curve = Fp2Curve { field, a, b };
            let mut cands: Option<Vec<u64>> = None;
            for _ in 0..3 {
                let pt = curve.random_point(&mut rng);
                let ks = curve.killing_multiples(pt, lo, hi);
                cands = Some(match cands {
                    None => ks,
                    Some(prev) => prev.into_iter().filter(|c| ks.contains(c)).collect(),
                });
            }
            let cands = cands.unwrap_or_default();
            if cands.len() != 1 {
                continue;
            }
            let n = cands[0];
            let Some(h) = (1..=max_cofactor.max(1))
                .find(|&h| n % h == 0 && is_prime_u64(n / h) && n / h > max_cofactor)
            else {
                continue;
            };
            let r = n / h;
            let generator = (0..32).find_map(|_| {
                let g = curve.mul_raw(curve.random_point(&mut rng), h);
                (!g.infinity && curve.mul_raw(g, r).infinity).then_some(g)
            })?;
            return Some(Fp2Instance {
                name: format!("fp2-{bits}bit-p{p}"),
                bits,
                curve,
                group_order: n,
                r,
                cofactor: h,
                generator,
                curves_tried: tried,
            });
        }
    }
    None
}

// ── The subfield factor base ───────────────────────────────────────

/// Points whose abscissa lies in `F_p`, smallest `x₀` first, both
/// signs, one column per abscissa.  `size = None` takes every such
/// abscissa that carries a point (about `p/2`).
pub fn fp2_subfield_factor_base(inst: &Fp2Instance, size: Option<usize>) -> FactorBase<Fp2Point> {
    let start = Instant::now();
    let curve = &inst.curve;
    let f = &curve.field;
    let p = f.p;
    let size = size.unwrap_or(usize::MAX);
    let mut fb = FactorBase::empty(match size {
        usize::MAX => "every abscissa in F_p carrying a point".to_string(),
        s => format!("smallest {s} abscissae in F_p"),
    });
    let (mut scanned, mut sqrts) = (0u64, 0u64);
    let mut x0 = 0u64;
    while fb.abscissae < size && x0 < p {
        scanned += 1;
        let x = (x0, 0);
        let rhs = curve.rhs(x);
        if f.is_square(rhs) {
            sqrts += 1;
            if let Some(y) = f.sqrt(rhs) {
                let y = if f.high(y) { f.neg(y) } else { y };
                let pt = Fp2Point::affine(x, y);
                let q = curve.neg(pt);
                let col = fb.abscissae;
                let i = fb.points.len();
                fb.points.push(pt);
                fb.col_of.push(col);
                fb.coef_of.push(1);
                if q != pt {
                    fb.points.push(q);
                    fb.col_of.push(col);
                    fb.coef_of.push(inst.r - 1);
                    fb.neg_index.push(i + 1);
                    fb.neg_index.push(i);
                    fb.x_index.insert(x0, vec![i, i + 1]);
                } else {
                    fb.neg_index.push(i);
                    fb.x_index.insert(x0, vec![i]);
                }
                fb.abscissae += 1;
            }
        }
        x0 += 1;
    }
    fb.columns = fb.abscissae;
    for (i, pt) in fb.points.iter().enumerate() {
        fb.point_index.insert(curve.key(pt), i);
    }
    fb.abscissa_list = fb.x_index.keys().copied().collect();
    fb.abscissa_list.sort_unstable();
    fb.cost.wall_ns = start.elapsed().as_nanos() as u64;
    fb.cost.count("abscissae_scanned", scanned);
    fb.cost.count("legendre_symbols", scanned);
    fb.cost.count("sqrt_solves", sqrts);
    fb
}

/// `fp2-subfield`: the `F_p`-rational abscissae of an `F_{p²}` curve.
pub struct Fp2SubfieldBase<'i> {
    pub instance: &'i Fp2Instance,
}

impl FactorBaseBuilder<Fp2Curve> for Fp2SubfieldBase<'_> {
    fn name(&self) -> &str {
        "fp2-subfield"
    }

    fn describe(&self, params: &Params) -> String {
        match params.get("size") {
            Some(s) => format!("the {s} smallest abscissae in F_p carrying a point, one column each"),
            None => "every abscissa in F_p carrying a point (about p/2), one column each".into(),
        }
    }

    fn parameters(&self) -> &[(&str, &str)] {
        &[("size", "abscissae in the base, smallest x0 first; default all (about p/2)")]
    }

    fn build(
        &self,
        _ctx: &InstanceCtx<Fp2Curve>,
        params: &Params,
        _ops: &mut GroupOps,
    ) -> Result<FactorBase<Fp2Point>, String> {
        let size = match params.get("size") {
            None => None,
            Some(_) => {
                let s = params.u64("size")? as usize;
                if s == 0 {
                    return Err("factor base size must be positive".into());
                }
                Some(s)
            }
        };
        Ok(fp2_subfield_factor_base(self.instance, size))
    }
}

// ── Polynomials over F_p (low degree first), counted ───────────────

type Poly = Vec<u64>;

fn trim(mut a: Poly) -> Poly {
    while a.last() == Some(&0) {
        a.pop();
    }
    a
}

fn deg(a: &Poly) -> isize {
    a.len() as isize - 1
}

fn poly_sub(w: &FpWork, a: &Poly, b: &Poly) -> Poly {
    let n = a.len().max(b.len());
    trim(
        (0..n)
            .map(|k| w.sub(*a.get(k).unwrap_or(&0), *b.get(k).unwrap_or(&0)))
            .collect(),
    )
}

fn poly_add(w: &FpWork, a: &Poly, b: &Poly) -> Poly {
    let n = a.len().max(b.len());
    trim(
        (0..n)
            .map(|k| w.add(*a.get(k).unwrap_or(&0), *b.get(k).unwrap_or(&0)))
            .collect(),
    )
}

fn poly_mul(w: &mut FpWork, a: &Poly, b: &Poly) -> Poly {
    if a.is_empty() || b.is_empty() {
        return Vec::new();
    }
    let mut out = vec![0u64; a.len() + b.len() - 1];
    for (i, &x) in a.iter().enumerate() {
        if x == 0 {
            continue;
        }
        for (j, &y) in b.iter().enumerate() {
            let t = w.mul(x, y);
            out[i + j] = w.add(out[i + j], t);
        }
    }
    trim(out)
}

/// `(quotient, remainder)` of `a / m`, `m` non-zero.
fn poly_divrem(w: &mut FpWork, a: &Poly, m: &Poly) -> (Poly, Poly) {
    let mut r = a.clone();
    let dm = m.len() - 1;
    if r.len() <= dm {
        return (Vec::new(), trim(r));
    }
    let lead_inv = if m[dm] == 1 { 1 } else { w.inv(m[dm]) };
    let mut q = vec![0u64; r.len() - dm];
    for k in (dm..r.len()).rev() {
        let c = if lead_inv == 1 { r[k] } else { w.mul(r[k], lead_inv) };
        q[k - dm] = c;
        if c == 0 {
            continue;
        }
        for (j, &mj) in m.iter().enumerate() {
            let t = w.mul(c, mj);
            r[k - dm + j] = w.sub(r[k - dm + j], t);
        }
    }
    r.truncate(dm);
    (trim(q), trim(r))
}

fn poly_rem(w: &mut FpWork, a: &Poly, m: &Poly) -> Poly {
    poly_divrem(w, a, m).1
}

fn poly_monic(w: &mut FpWork, a: &Poly) -> Poly {
    let Some(&lead) = a.last() else {
        return Vec::new();
    };
    if lead == 1 {
        return a.clone();
    }
    let inv = w.inv(lead);
    a.iter().map(|&c| w.mul(c, inv)).collect()
}

fn poly_gcd(w: &mut FpWork, a: &Poly, b: &Poly) -> Poly {
    let (mut a, mut b) = (trim(a.clone()), trim(b.clone()));
    while !b.is_empty() {
        let r = poly_rem(w, &a, &b);
        a = b;
        b = r;
    }
    poly_monic(w, &a)
}

/// `base^e mod m`.
fn poly_powmod(w: &mut FpWork, base: &Poly, mut e: u64, m: &Poly) -> Poly {
    let mut result: Poly = vec![1];
    let mut b = poly_rem(w, base, m);
    while e > 0 {
        if e & 1 == 1 {
            let t = poly_mul(w, &result, &b);
            result = poly_rem(w, &t, m);
        }
        e >>= 1;
        if e > 0 {
            let t = poly_mul(w, &b, &b);
            b = poly_rem(w, &t, m);
        }
    }
    result
}

/// Roots of a monic squarefree `f` that splits into distinct linear
/// factors over `F_p` (Cantor–Zassenhaus with shifts `X + c`).
fn split_roots(w: &mut FpWork, f: &Poly, out: &mut Vec<u64>) {
    let p = w.p;
    match deg(f) {
        d if d <= 0 => {}
        1 => out.push(w.neg(f[0])),
        2 => {
            // X² + bX + c with b² − 4c a square (f splits).
            let (c, b) = (f[0], f[1]);
            let bb = w.mul(b, b);
            let disc = w.sub(bb, w.small(4, c));
            if let Some(s) = w.sqrt(disc) {
                let half = (p + 1) / 2;
                let r1 = w.mul(w.sub(s, b), half);
                let r2 = w.mul(w.sub(w.neg(s), b), half);
                out.push(r1);
                if r2 != r1 {
                    out.push(r2);
                }
            }
        }
        _ => {
            for c in 0..p {
                let shifted: Poly = vec![c, 1];
                let t = poly_powmod(w, &shifted, (p - 1) / 2, f);
                let t1 = poly_sub(w, &t, &vec![1]);
                let d = poly_gcd(w, f, &t1);
                if deg(&d) > 0 && deg(&d) < deg(f) {
                    let (q, _) = poly_divrem(w, f, &d);
                    let q = poly_monic(w, &q);
                    split_roots(w, &d, out);
                    split_roots(w, &q, out);
                    return;
                }
            }
        }
    }
}

/// Every root of `g` in `F_p` (distinct), via `gcd(g, X^p − X)`.
fn roots_in_fp(w: &mut FpWork, g: &Poly) -> Vec<u64> {
    let g = poly_monic(w, &trim(g.clone()));
    let mut out = Vec::new();
    match deg(&g) {
        d if d <= 0 => return out,
        1 => {
            out.push(w.neg(g[0]));
            return out;
        }
        _ => {}
    }
    let xp = poly_powmod(w, &vec![0, 1], w.p, &g);
    let h = poly_sub(w, &xp, &vec![0, 1]);
    let lin = poly_gcd(w, &g, &h);
    split_roots(w, &lin, &mut out);
    out.sort_unstable();
    out.dedup();
    out
}

fn eval(w: &mut FpWork, f: &Poly, x: u64) -> u64 {
    let mut acc = 0u64;
    for &c in f.iter().rev() {
        let t = w.mul(acc, x);
        acc = w.add(t, c);
    }
    acc
}

// ── The fp2-weil oracle ────────────────────────────────────────────

/// The two `F_p` equations of `S₃(x₁, x₂, x_R) = 0` in `(e₁, e₂)`:
/// `f_k = s_k·e₂² + A_k e₁² + B_k e₁e₂ + C_k e₁ + D_k e₂ + E_k`, with
/// `s₀ = 1`, `s₁ = 0`.  Indices `[A, B, C, D, E]`.
pub fn weil_equations(curve: &Fp2Curve, a2: F2, x_r: F2) -> ([u64; 5], [u64; 5]) {
    let f = &curve.field;
    let x2 = f.sqr(x_r);
    let ax = f.mul(curve.a, x_r);
    let bx = f.mul(curve.b, x_r);
    let ca = x2; // e1²
    let cb = f.neg(f.scale(2, x_r)); // e1 e2
    let cc = f.neg(f.add(f.scale(2, ax), f.scale(4, curve.b))); // e1
    let cd = f.neg(f.add(f.scale(4, x2), f.scale(2, curve.a))); // e2
    let ce = f.sub(a2, f.scale(4, bx)); // 1
    (
        [ca.0, cb.0, cc.0, cd.0, ce.0],
        [ca.1, cb.1, cc.1, cd.1, ce.1],
    )
}

/// **Gaudry/Diem decomposition for `n = 2`** over the subfield base:
/// solve the Weil restriction of `S₃(x₁, x₂, x_R)` for `x₁, x₂ ∈ F_p`.
/// Field work is counted (`fp_muls`, `inversions`, `sqrt_solves`); the
/// sign lift's additions are charged to the group ledger.
pub struct Fp2WeilOracle<'i> {
    instance: &'i Fp2Instance,
    a2: F2,
    /// `F_p` multiplications (the `F_{p²}` coefficient set-up counted at
    /// its `F_p` cost, plus the polynomial arithmetic).
    fp_muls: u64,
    calls: u64,
    degenerate: u64,
    candidates: u64,
    roots_found: u64,
    pairs_not_in_base: u64,
    discriminant_nonresidues: u64,
}

impl<'i> Fp2WeilOracle<'i> {
    pub fn new(instance: &'i Fp2Instance) -> Self {
        let f = &instance.curve.field;
        Self {
            instance,
            a2: f.sqr(instance.curve.a),
            fp_muls: 0,
            calls: 0,
            degenerate: 0,
            candidates: 0,
            roots_found: 0,
            pairs_not_in_base: 0,
            discriminant_nonresidues: 0,
        }
    }

    /// Every `(e₁, e₂) ∈ F_p²` on both equations, or `None` when the
    /// system is degenerate (an equation vanishes identically).
    fn solve_e(&mut self, w: &mut FpWork, x_r: F2) -> Option<Vec<(u64, u64)>> {
        // Coefficient set-up: X², aX, bX are three F_{p²} products at
        // five F_p multiplications each (Schoolbook with δ).
        w.muls += 15;
        let (re, im) = weil_equations(&self.instance.curve, self.a2, x_r);
        let [a1, b1, c1, d1, e1c] = im;
        let [a0, b0, c0, d0, e0] = re;
        let mut sols = Vec::new();
        // f0(e1, ·) as a monic quadratic in e2, solved over F_p.
        let solve_f0 = |w: &mut FpWork, e1: u64, sols: &mut Vec<(u64, u64)>| {
            let t = w.mul(b0, e1);
            let lin = w.add(t, d0);
            let e1sq = w.mul(e1, e1);
            let (t2, t1) = (w.mul(a0, e1sq), w.mul(c0, e1));
            let cst = w.add(w.add(t2, t1), e0);
            let mut roots = Vec::new();
            split_roots(w, &vec![cst, lin, 1], &mut roots);
            for e2 in roots {
                sols.push((e1, e2));
            }
        };
        if b1 == 0 && d1 == 0 {
            // f1 does not involve e2: it is univariate in e1.
            let f1: Poly = trim(vec![e1c, c1, a1]);
            if f1.is_empty() {
                return None;
            }
            for e1 in roots_in_fp(w, &f1) {
                solve_f0(w, e1, &mut sols);
            }
            return Some(sols);
        }
        // e2 = num(e1) / den(e1).
        let num: Poly = trim(vec![w.neg(e1c), w.neg(c1), w.neg(a1)]);
        let den: Poly = trim(vec![d1, b1]);
        // g = num² + (B0 e1 + D0)·num·den + (A0 e1² + C0 e1 + E0)·den².
        let nn = poly_mul(w, &num, &num);
        let nd = poly_mul(w, &num, &den);
        let dd = poly_mul(w, &den, &den);
        let lin0: Poly = trim(vec![d0, b0]);
        let quad0: Poly = trim(vec![e0, c0, a0]);
        let t1 = poly_mul(w, &lin0, &nd);
        let t2 = poly_mul(w, &quad0, &dd);
        let g = poly_add(w, &poly_add(w, &nn, &t1), &t2);
        if g.is_empty() {
            return None;
        }
        for e1 in roots_in_fp(w, &g) {
            let dv = eval(w, &den, e1);
            if dv == 0 {
                continue;
            }
            let nv = eval(w, &num, e1);
            let inv = w.inv(dv);
            sols.push((e1, w.mul(nv, inv)));
        }
        // Where den vanishes, f1 holds for every e2 iff num vanishes too.
        if b1 != 0 {
            let inv = w.inv(b1);
            let t = w.mul(d1, inv);
            let e1s = w.neg(t);
            if eval(w, &num, e1s) == 0 {
                solve_f0(w, e1s, &mut sols);
            }
        }
        Some(sols)
    }
}

impl DecompositionOracle<Fp2Curve> for Fp2WeilOracle<'_> {
    fn name(&self) -> &str {
        "fp2-weil"
    }

    fn summands(&self) -> u32 {
        2
    }

    fn describe(&self, _params: &Params) -> String {
        "Weil-restrict S3(x1, x2, x_R) to F_p in (x1 + x2, x1 x2), eliminate x1 x2, \
         root the quartic by gcd with X^p - X and Cantor-Zassenhaus"
            .into()
    }

    fn prepare(
        &mut self,
        _ctx: &InstanceCtx<Fp2Curve>,
        fb: &FactorBase<Fp2Point>,
        _params: &Params,
        _ops: &mut GroupOps,
    ) -> Result<(), String> {
        if fb.x_index.keys().any(|&x| x >= self.instance.p()) {
            return Err("fp2-weil needs a factor base of F_p-rational abscissae; use fp2-subfield".into());
        }
        Ok(())
    }

    fn relation_counters(&self) -> BTreeMap<String, u64> {
        BTreeMap::from([
            ("fp_muls".into(), self.fp_muls),
            ("fp2_weil_calls".into(), self.calls),
            ("fp2_weil_degenerate".into(), self.degenerate),
            ("fp2_weil_roots".into(), self.roots_found),
            ("fp2_weil_candidates".into(), self.candidates),
            ("fp2_weil_disc_nonresidue".into(), self.discriminant_nonresidues),
            ("fp2_weil_not_in_base".into(), self.pairs_not_in_base),
        ])
    }

    fn decompose(
        &mut self,
        ctx: &InstanceCtx<Fp2Curve>,
        fb: &FactorBase<Fp2Point>,
        ops: &mut GroupOps,
        counters: &mut OracleCounters,
        point: Fp2Point,
    ) -> Option<Vec<usize>> {
        if point.infinity {
            return None;
        }
        self.calls += 1;
        let mut w = FpWork::new(self.instance.p());
        let result = (|| {
            let Some(sols) = self.solve_e(&mut w, point.x) else {
                self.degenerate += 1;
                return None;
            };
            self.roots_found += sols.len() as u64;
            let half = w.p.div_ceil(2);
            for (e1, e2) in sols {
                let e1sq = w.mul(e1, e1);
                let disc = w.sub(e1sq, w.small(4, e2));
                let Some(s) = w.sqrt(disc) else {
                    self.discriminant_nonresidues += 1;
                    continue;
                };
                let x1 = w.mul(w.add(e1, s), half);
                let x2 = w.mul(w.sub(e1, s), half);
                self.candidates += 1;
                counters.lookups += 2;
                if !fb.x_index.contains_key(&x1) || !fb.x_index.contains_key(&x2) {
                    self.pairs_not_in_base += 1;
                    counters.unliftable_systems += 1;
                    continue;
                }
                if let Some(idx) = lift_abscissae(ctx.group, fb, ops, &[x1, x2], point) {
                    return Some(idx);
                }
                counters.lift_failures += 1;
            }
            None
        })();
        self.fp_muls += w.muls;
        counters.inversions += w.invs;
        counters.sqrt_solves += w.sqrts;
        result
    }
}

// ── Calibration ────────────────────────────────────────────────────

/// The `F_p` units the `fp2-weil` oracle and the subfield base count,
/// measured on this instance's `p`: one multiplication, inversion,
/// square root and Legendre symbol.  No pinned ratios exist for this
/// regime, so these are host-measured (the report says so).
pub fn calibrate_fp_units(p: u64, calib: &mut Calibration) {
    let mut rng = StdRng::seed_from_u64(0xF2_CA11B ^ p);
    let values: Vec<u64> = (0..2048).map(|_| rng.gen_range(1..p)).collect();
    let reps = 64usize;
    let start = Instant::now();
    let mut acc = 1u64;
    for _ in 0..reps {
        for &v in &values {
            acc = fp_mul(acc ^ 1, v, p);
        }
    }
    calib.ns_per_fp_mul = Some(start.elapsed().as_nanos() as f64 / (reps * values.len()) as f64);
    std::hint::black_box(acc);
    let start = Instant::now();
    let mut acc = 0u64;
    for _ in 0..8 {
        for &v in &values {
            acc ^= fp_inv(v, p);
        }
    }
    calib.ns_per_inversion = Some(start.elapsed().as_nanos() as f64 / (8 * values.len()) as f64);
    std::hint::black_box(acc);
    let start = Instant::now();
    let mut acc = 0i32;
    for _ in 0..8 {
        for &v in &values {
            acc += fp_legendre(v, p);
        }
    }
    calib.ns_per_legendre = Some(start.elapsed().as_nanos() as f64 / (8 * values.len()) as f64);
    std::hint::black_box(acc);
    let residues: Vec<u64> = values.iter().map(|&v| fp_mul(v, v, p)).collect();
    let start = Instant::now();
    let mut acc = 0u64;
    for _ in 0..8 {
        for &v in &residues {
            acc ^= fp_sqrt(v, p).unwrap_or(0);
        }
    }
    calib.ns_per_sqrt = Some(start.elapsed().as_nanos() as f64 / (8 * residues.len()) as f64);
    std::hint::black_box(acc);
}

#[cfg(test)]
mod tests {
    use super::*;

    fn small_instance() -> Fp2Instance {
        find_fp2_curve(16, 7, 8).expect("a 16-bit fp2 instance")
    }

    #[test]
    fn ic_fp2_field_sqrt_and_inverse() {
        let f = Fp2Field::new(1_000_003);
        let mut rng = StdRng::seed_from_u64(1);
        for _ in 0..500 {
            let a = f.random(&mut rng);
            if a == (0, 0) {
                continue;
            }
            assert_eq!(f.mul(a, f.inv(a)), (1, 0));
            let sq = f.sqr(a);
            let s = f.sqrt(sq).expect("square has a root");
            assert_eq!(f.sqr(s), sq);
        }
    }

    #[test]
    fn ic_fp2_instance_order_and_key() {
        let inst = small_instance();
        let c = &inst.curve;
        assert!(c.a.1 != 0 && c.b.1 != 0);
        assert!(c.is_on_curve(inst.generator));
        assert!(c.mul_raw(inst.generator, inst.r).infinity);
        assert_eq!(inst.group_order, inst.r * inst.cofactor);
        let mut rng = StdRng::seed_from_u64(3);
        for _ in 0..8 {
            let pt = c.random_point(&mut rng);
            assert!(c.mul_raw(pt, inst.group_order).infinity);
            let k = c.key(&pt);
            let nk = c.key(&c.neg(pt));
            if pt.y != (0, 0) {
                assert_eq!(k >> 1, nk >> 1);
                assert_ne!(k & 1, nk & 1);
            }
        }
    }

    #[test]
    fn ic_fp2_weil_decomposes_pair_sums() {
        let inst = small_instance();
        let fb = fp2_subfield_factor_base(&inst, None);
        assert!(fb.abscissae > 0);
        assert!(fb.abscissa_list.iter().all(|&x| x < inst.p()));
        let ctx = InstanceCtx {
            group: &inst.curve,
            generator: inst.generator,
            target: inst.generator,
            r: inst.r,
            cofactor: inst.cofactor,
            group_order: inst.group_order,
            name: inst.name.clone(),
            field_degree: None,
        };
        let mut oracle = Fp2WeilOracle::new(&inst);
        oracle
            .prepare(&ctx, &fb, &Params::default(), &mut GroupOps::default())
            .unwrap();
        let mut rng = StdRng::seed_from_u64(11);
        let mut ops = GroupOps::default();
        let mut ctr = OracleCounters::default();
        let mut tested = 0;
        while tested < 200 {
            let i = rng.gen_range(0..fb.points.len());
            let j = rng.gen_range(0..fb.points.len());
            let r = inst.curve.add(&mut ops, fb.points[i], fb.points[j]);
            if r.infinity {
                continue;
            }
            tested += 1;
            let idx = oracle
                .decompose(&ctx, &fb, &mut ops, &mut ctr, r)
                .unwrap_or_else(|| panic!("P{i} + P{j} not decomposed"));
            assert_eq!(idx.len(), 2);
            let s = inst.curve.add(&mut ops, fb.points[idx[0]], fb.points[idx[1]]);
            assert_eq!(s, r);
        }
        assert!(ctr.sqrt_solves > 0);
        assert!(oracle.fp_muls > 0);
    }

    #[test]
    fn ic_fp2_roots_of_split_quartic() {
        let p = 10_007u64;
        let mut w = FpWork::new(p);
        // (X − 3)(X − 5)(X − 11)(X − 4000).
        let mut g: Poly = vec![1];
        for r in [3u64, 5, 11, 4000] {
            g = poly_mul(&mut w, &g, &vec![p - r, 1]);
        }
        assert_eq!(roots_in_fp(&mut w, &g), vec![3, 5, 11, 4000]);
    }
}
