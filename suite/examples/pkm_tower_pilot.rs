//! **Design-validation pilot for the PKM tower oracle.**
//!
//! `research/notes/index-calculus/RESEARCH_PKM_TOWER_ORACLE.md` designs an
//! algebraic decomposition oracle for prime-field curves on
//! Petit–Kosters–Messeng tower factor bases, and pre-registers (§5.2) the one
//! measurement that decides whether to build it: how the F4 solving degree
//! of a tower system grows with the number of tower unknowns `N = m·t`.
//! This example runs a small subset of those cells with the repository's
//! degree-bounded F4 (`f4_fp`), with the §5.3 controls that fit a pilot:
//!
//! - `tower`: PKM's system, i.e. `S₃` (or the `S₃` chain at `m ≥ 3`) plus
//!   the tower equations, raw presentation;
//! - `ladder`: the same system plus `g − 1` random quadrics that vanish at
//!   the planted solution (the generator-count ladder, instrument power);
//! - `naive`: the same `V`, membership as one univariate `x^{2^t} = g^{2^t}`
//!   (Kummer only);
//! - `null`: `S₃`'s monomial support with random coefficients and a
//!   planted zero, under the same tower.
//!
//! Every tower, every Vélu map and every planted decomposition is checked
//! before anything is measured, so a construction bug stops the run instead
//! of reading as a degree.
//!
//! It is a stage diagnostic of the solver axis (`AGENTS.md` §2): it prices
//! no pipeline, reports no `S`, and decides nothing on its own. Stage A of
//! the note decides, on its full ladder.
//!
//! `--engine tower` runs the same systems on the sparse tower engine
//! `f4_fp_tower` instead (note §11): the tower equations become its
//! rewriting rules, the other equations its input in normal form (the
//! `reduced` presentation), and the naive control, which has no tower, is
//! skipped. `--max-nnz` stops a system whose matrices grow past a size, and
//! `--trace` prints its step trace.
//!
//! The committed runs, their exact flags and the scripts that tabulate and
//! cross-check them are in `research/pkm_tower_pilot_20260924/` (the pilot,
//! `f4_fp`) and `research/pkm_tower_round2_20260925/` (round 2,
//! `f4_fp_tower`).
//!
//! ```bash
//! cargo run --release --example pkm_tower_pilot -- --out pilot.jsonl
//! cargo run --release --example pkm_tower_pilot -- --kinds kummer --max-t 6 --budget 30
//! # What F4 knows at degree 4 on one N = 16 system: its basis elements of
//! # degree at most 3 (`--cap` bounds the degree, `--dump` prints the basis).
//! cargo run --release --example pkm_tower_pilot -- --kinds kummer --m 2 --controls tower \
//!     --t-min 8 --max-t 8 --planted 0 --random 1 --cap 4 --dump 3 --ladder-t none
//! # The same system on the tower engine, with its step trace.
//! cargo run --release --example pkm_tower_pilot -- --engine tower --kinds kummer --m 2 \
//!     --controls tower --t-min 8 --max-t 8 --planted 0 --random 1 --ladder-t none --trace
//! # M31's auxiliary curve y² = x³ + x has order p+1; no curve search.
//! # Export a small system first; a ten-level membership chain can be
//! # constructed and checked without asking F4 to solve that full system.
//! cargo run --release --example pkm_tower_pilot -- --p 2147483647 --kinds isogeny \
//!     --aux-supersingular --m 2 --t-min 2 --max-t 2 --ladder-t none --export systems
//! ```

use std::collections::BTreeMap;
use std::fs::File;
use std::io::Write;
use std::time::{Duration, Instant};

use cryptanalysis_suite::cryptanalysis::f4_fp::{self, F4Options, F4Report, Ordering, Poly};
use cryptanalysis_suite::cryptanalysis::f4_fp_tower::{
    self, RPoly, SquareRule, TowerF4Options, TowerRing,
};
use cryptanalysis_suite::cryptanalysis::ic_boundary::{
    CountedGroup, GroupOps, PrimeCurve, PrimePoint,
};
use rand::rngs::StdRng;
use rand::{Rng, SeedableRng};
use serde_json::{json, Value};

// ── Field arithmetic ───────────────────────────────────────────────

fn mulm(a: u64, b: u64, p: u64) -> u64 {
    ((a as u128 * b as u128) % p as u128) as u64
}

fn addm(a: u64, b: u64, p: u64) -> u64 {
    (a + b) % p
}

fn subm(a: u64, b: u64, p: u64) -> u64 {
    (a + p - b % p) % p
}

fn powm(mut a: u64, mut e: u64, p: u64) -> u64 {
    let mut r = 1u64;
    a %= p;
    while e > 0 {
        if e & 1 == 1 {
            r = mulm(r, a, p);
        }
        a = mulm(a, a, p);
        e >>= 1;
    }
    r
}

fn invm(a: u64, p: u64) -> u64 {
    assert!(!a.is_multiple_of(p), "inverse of zero");
    powm(a, p - 2, p)
}

// ── Polynomials while building a system ────────────────────────────

/// A polynomial over `F_p` in `n` variables, as a map from exponent
/// vectors to non-zero coefficients.
#[derive(Clone, Debug)]
struct Pol {
    n: usize,
    terms: BTreeMap<Vec<u32>, u64>,
}

impl Pol {
    fn zero(n: usize) -> Self {
        Pol {
            n,
            terms: BTreeMap::new(),
        }
    }

    fn constant(n: usize, c: u64, p: u64) -> Self {
        let mut f = Pol::zero(n);
        if !c.is_multiple_of(p) {
            f.terms.insert(vec![0; n], c % p);
        }
        f
    }

    fn var(n: usize, i: usize) -> Self {
        let mut e = vec![0; n];
        e[i] = 1;
        let mut f = Pol::zero(n);
        f.terms.insert(e, 1);
        f
    }

    fn add(&self, o: &Pol, p: u64) -> Pol {
        let mut f = self.clone();
        for (e, c) in &o.terms {
            let v = f.terms.entry(e.clone()).or_insert(0);
            *v = addm(*v, *c, p);
        }
        f.terms.retain(|_, c| *c != 0);
        f
    }

    fn scale(&self, k: u64, p: u64) -> Pol {
        let mut f = Pol::zero(self.n);
        for (e, c) in &self.terms {
            let v = mulm(*c, k, p);
            if v != 0 {
                f.terms.insert(e.clone(), v);
            }
        }
        f
    }

    fn sub(&self, o: &Pol, p: u64) -> Pol {
        self.add(&o.scale(p - 1, p), p)
    }

    fn mul(&self, o: &Pol, p: u64) -> Pol {
        let mut f = Pol::zero(self.n);
        for (e1, c1) in &self.terms {
            for (e2, c2) in &o.terms {
                let e: Vec<u32> = e1.iter().zip(e2).map(|(a, b)| a + b).collect();
                let v = f.terms.entry(e).or_insert(0);
                *v = addm(*v, mulm(*c1, *c2, p), p);
            }
        }
        f.terms.retain(|_, c| *c != 0);
        f
    }

    fn eval(&self, x: &[u64], p: u64) -> u64 {
        let mut acc = 0u64;
        for (e, c) in &self.terms {
            let mut t = *c;
            for (i, k) in e.iter().enumerate() {
                if *k > 0 {
                    t = mulm(t, powm(x[i], *k as u64, p), p);
                }
            }
            acc = addm(acc, t, p);
        }
        acc
    }

    fn degree(&self) -> u32 {
        self.terms
            .keys()
            .map(|e| e.iter().sum::<u32>())
            .max()
            .unwrap_or(0)
    }

    fn to_poly(&self, p: u64) -> Poly {
        let terms: Vec<(Vec<u32>, u64)> = self.terms.iter().map(|(e, c)| (e.clone(), *c)).collect();
        f4_fp::normalise(&terms, p, Ordering::Grevlex)
    }
}

/// Semaev's third summation polynomial for `y² = x³ + ax + b`, on three
/// polynomial arguments:
/// `(X1 − X2)²X3² − 2((X1 + X2)(X1X2 + a) + 2b)X3 + (X1X2 − a)² − 4b(X1 + X2)`.
fn s3(x1: &Pol, x2: &Pol, x3: &Pol, a: u64, b: u64, p: u64) -> Pol {
    let n = x1.n;
    let d = x1.sub(x2, p);
    let t1 = d.mul(&d, p).mul(x3, p).mul(x3, p);
    let s = x1.add(x2, p);
    let pr = x1.mul(x2, p);
    let inner = s
        .mul(&pr.add(&Pol::constant(n, a, p), p), p)
        .add(&Pol::constant(n, mulm(2, b, p), p), p);
    let t2 = inner.mul(x3, p).scale(p - 2, p);
    let q = pr.sub(&Pol::constant(n, a, p), p);
    let t3 = q.mul(&q, p).sub(&s.scale(mulm(4, b, p), p), p);
    t1.add(&t2, p).add(&t3, p)
}

// ── Towers ─────────────────────────────────────────────────────────

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum Kind {
    Kummer,
    Dickson,
    /// Dickson steps on the norm-one torus side: `V = {w + w⁻¹}` for `w` in a
    /// coset of the `2^t` subgroup of `T₂ ⊂ F_{p²}*` (needs `2^t | p + 1`).
    Torus,
    Isogeny,
}

impl Kind {
    fn name(self) -> &'static str {
        match self {
            Kind::Kummer => "kummer",
            Kind::Dickson => "dickson",
            Kind::Torus => "torus",
            Kind::Isogeny => "isogeny",
        }
    }
}

/// One level of a tower: how `y_{j+1}` (or the final constant) follows
/// from `y_j`.
#[derive(Clone, Debug)]
enum Step {
    /// `y_{j+1} = y_j²` (Kummer).
    Square,
    /// `y_{j+1} = y_j² − 2` (Dickson `D_2`).
    Dickson,
    /// `y_{j+1} = y_j + τ/(y_j − ξ)`, the x-map of a 2-isogeny with
    /// kernel `(ξ, 0)`.
    Velu { xi: u64, tau: u64 },
    /// The x-map of an isogeny of odd prime degree `d` (Vélu), from half
    /// its kernel `S` (one point of each pair `±Q`):
    /// `y_{j+1} = y_j + Σ_{Q∈S} ( v_Q/(y_j − x_Q) + u_Q/(y_j − x_Q)² )`,
    /// `v_Q = 6x_Q² + 2a`, `u_Q = 4y_Q²`.  Entries are `(x_Q, v_Q, u_Q)`;
    /// the level equation has degree `d = 2|S| + 1`.
    VeluOdd { pts: Vec<(u64, u64, u64)> },
}

struct Tower {
    kind: Kind,
    t: usize,
    /// The factor-base abscissa set: `size` distinct elements of `F_p`
    /// (`2^t` unless the isogeny tower has odd-degree levels).
    v: Vec<u64>,
    /// `|V|`, the product of the level degrees.
    size: usize,
    /// `x = scale · y_0` (Kummer: the coset representative `g`).
    scale: u64,
    steps: Vec<Step>,
    /// The value the last step must reach.
    c: u64,
    info: Value,
}

impl Tower {
    /// Rational membership, with every pole rejected before clearing a
    /// denominator. This does not use the enumerated coset `v`.
    fn contains(&self, x: u64, p: u64) -> bool {
        let mut y = mulm(x % p, invm(self.scale, p), p);
        for (j, step) in self.steps.iter().enumerate() {
            let pole = match step {
                Step::Velu { xi, .. } => y == *xi,
                Step::VeluOdd { pts } => pts.iter().any(|&(xq, _, _)| y == xq),
                _ => false,
            };
            if pole {
                return false;
            }
            y = self.apply(j, y, p);
        }
        y == self.c
    }

    fn apply(&self, j: usize, y: u64, p: u64) -> u64 {
        match &self.steps[j] {
            Step::Square => mulm(y, y, p),
            Step::Dickson => subm(mulm(y, y, p), 2, p),
            Step::Velu { xi, tau } => addm(y, mulm(*tau, invm(subm(y, *xi, p), p), p), p),
            Step::VeluOdd { pts } => velu_odd_x(pts, y, p),
        }
    }

    /// `y_0 … y_{t−1}` for an abscissa of `V`.
    fn values(&self, x: u64, p: u64) -> Vec<u64> {
        let mut y = vec![0u64; self.t];
        y[0] = mulm(x, invm(self.scale, p), p);
        for j in 0..self.t - 1 {
            y[j + 1] = self.apply(j, y[j], p);
        }
        y
    }

    /// The `t` equations of one block whose variables start at `base`.
    fn equations(&self, n: usize, base: usize, p: u64) -> Vec<Pol> {
        (0..self.t)
            .map(|j| {
                let yj = Pol::var(n, base + j);
                let next = if j + 1 < self.t {
                    Pol::var(n, base + j + 1)
                } else {
                    Pol::constant(n, self.c, p)
                };
                let sq = yj.mul(&yj, p);
                match &self.steps[j] {
                    Step::Square => next.sub(&sq, p),
                    Step::Dickson => next.sub(&sq.sub(&Pol::constant(n, 2, p), p), p),
                    Step::Velu { xi, tau } => {
                        let (xi, tau) = (*xi, *tau);
                        let lhs = next.mul(&yj.sub(&Pol::constant(n, xi, p), p), p);
                        let rhs = sq
                            .sub(&yj.scale(xi, p), p)
                            .add(&Pol::constant(n, tau, p), p);
                        lhs.sub(&rhs, p)
                    }
                    Step::VeluOdd { pts } => {
                        // next·L = y·L + Σ_Q (v_Q(y − x_Q) + u_Q)·L/(y − x_Q)²,
                        // L = Π_Q (y − x_Q)²: degree 2|S| + 1 in y.
                        let lin = |xq: u64| yj.sub(&Pol::constant(n, xq, p), p);
                        let sq_of = |xq: u64| lin(xq).mul(&lin(xq), p);
                        let mut l = Pol::constant(n, 1, p);
                        for &(xq, _, _) in pts {
                            l = l.mul(&sq_of(xq), p);
                        }
                        let mut rhs = yj.mul(&l, p);
                        for (i, &(xq, vq, uq)) in pts.iter().enumerate() {
                            let mut others = Pol::constant(n, 1, p);
                            for (k, &(xr, _, _)) in pts.iter().enumerate() {
                                if k != i {
                                    others = others.mul(&sq_of(xr), p);
                                }
                            }
                            let num = lin(xq).scale(vq, p).add(&Pol::constant(n, uq, p), p);
                            rhs = rhs.add(&num.mul(&others, p), p);
                        }
                        next.mul(&l, p).sub(&rhs, p)
                    }
                }
            })
            .collect()
    }

    /// The tower equations of one block (variables from `base`) as the
    /// square rules of [`f4_fp_tower`]: each equation solved for `y_j²`.
    fn square_rules(&self, base: usize, p: u64) -> Vec<SquareRule> {
        (0..self.t)
            .map(|j| {
                let top = j + 1 == self.t;
                let next = (!top).then_some((base + j + 1) as u8);
                match (&self.steps[j], top) {
                    // y_{j+1} = y_j²; on top, y_j² = c
                    (Step::Square, false) => SquareRule {
                        next,
                        a: 0,
                        b: 1,
                        c: 0,
                        d: 0,
                    },
                    (Step::Square, true) => SquareRule {
                        next,
                        a: 0,
                        b: 0,
                        c: 0,
                        d: self.c % p,
                    },
                    // y_{j+1} = y_j² − 2; on top, y_j² = c + 2
                    (Step::Dickson, false) => SquareRule {
                        next,
                        a: 0,
                        b: 1,
                        c: 0,
                        d: 2 % p,
                    },
                    (Step::Dickson, true) => SquareRule {
                        next,
                        a: 0,
                        b: 0,
                        c: 0,
                        d: addm(self.c, 2, p),
                    },
                    // y_{j+1}(y_j − ξ) = y_j² − ξ·y_j + τ, so
                    // y_j² = y_j·y_{j+1} − ξ·y_{j+1} + ξ·y_j − τ
                    (Step::Velu { xi, tau }, false) => SquareRule {
                        next,
                        a: 1,
                        b: subm(0, *xi, p),
                        c: *xi,
                        d: subm(0, *tau, p),
                    },
                    // c·(y_j − ξ) = y_j² − ξ·y_j + τ, so
                    // y_j² = (c + ξ)·y_j − (c·ξ + τ)
                    (Step::Velu { xi, tau }, true) => SquareRule {
                        next,
                        a: 0,
                        b: 0,
                        c: addm(self.c, *xi, p),
                        d: subm(0, addm(mulm(self.c, *xi, p), *tau, p), p),
                    },
                    (Step::VeluOdd { .. }, _) => panic!(
                        "the tower engine rewrites only degree-2 levels; odd-degree isogeny \
                         levels need --engine f4"
                    ),
                }
            })
            .collect()
    }

    /// Every element of `V` satisfies the tower, `|V| = 2^t` and the
    /// elements are distinct.  Panics otherwise: a wrong tower would make
    /// every degree below meaningless.
    fn check(&self, p: u64) {
        let mut sorted = self.v.clone();
        sorted.sort_unstable();
        sorted.dedup();
        assert_eq!(sorted.len(), self.size, "{:?}: V has repeats", self.kind);
        assert_eq!(
            self.v.len(),
            self.size,
            "{:?}: |V| is not the degree product",
            self.kind
        );
        let n = self.t;
        let eqs = self.equations(n, 0, p);
        for &x in &self.v {
            assert!(
                self.contains(x, p),
                "coset element fails rational membership"
            );
            let y = self.values(x, p);
            for (j, e) in eqs.iter().enumerate() {
                assert_eq!(
                    e.eval(&y, p),
                    0,
                    "{:?}: level {j} fails at x = {x}",
                    self.kind
                );
            }
        }
    }
}

/// An element of exact order `2^t` in `F_p^*`.
fn root_of_unity(p: u64, t: usize, rng: &mut StdRng) -> u64 {
    assert!(
        (p - 1).is_multiple_of(1u64 << t),
        "2^{t} does not divide p − 1"
    );
    loop {
        let h = rng.gen_range(2..p);
        if powm(h, (p - 1) / 2, p) == p - 1 {
            return powm(h, (p - 1) >> t, p);
        }
    }
}

fn kummer(p: u64, t: usize, rng: &mut StdRng) -> Tower {
    let zeta = root_of_unity(p, t, rng);
    let g = rng.gen_range(2..p);
    let v: Vec<u64> = (0..1u64 << t)
        .map(|k| mulm(g, powm(zeta, k, p), p))
        .collect();
    Tower {
        kind: Kind::Kummer,
        t,
        size: 1 << t,
        v,
        scale: g,
        steps: vec![Step::Square; t],
        c: 1,
        info: json!({"g": g, "zeta": zeta}),
    }
}

fn dickson(p: u64, t: usize, rng: &mut StdRng) -> Tower {
    let zeta = root_of_unity(p, t, rng);
    loop {
        let u = rng.gen_range(2..p);
        if powm(u, 1u64 << (t + 1), p) == 1 {
            continue;
        }
        let v: Vec<u64> = (0..1u64 << t)
            .map(|k| {
                let w = mulm(u, powm(zeta, k, p), p);
                addm(w, invm(w, p), p)
            })
            .collect();
        let mut s = v.clone();
        s.sort_unstable();
        s.dedup();
        if s.len() != 1 << t {
            continue;
        }
        let ut = powm(u, 1u64 << t, p);
        return Tower {
            kind: Kind::Dickson,
            t,
            size: 1 << t,
            v,
            scale: 1,
            steps: vec![Step::Dickson; t],
            c: addm(ut, invm(ut, p), p),
            info: json!({"u": u, "zeta": zeta}),
        };
    }
}

/// `F_{p²} = F_p[√d]` with `d` a non-residue; elements `(re, im)`.
fn fp2_mul(a: (u64, u64), b: (u64, u64), d: u64, p: u64) -> (u64, u64) {
    (
        addm(mulm(a.0, b.0, p), mulm(d, mulm(a.1, b.1, p), p), p),
        addm(mulm(a.0, b.1, p), mulm(a.1, b.0, p), p),
    )
}

fn fp2_pow(mut a: (u64, u64), mut e: u64, d: u64, p: u64) -> (u64, u64) {
    let mut r = (1, 0);
    while e > 0 {
        if e & 1 == 1 {
            r = fp2_mul(r, a, d, p);
        }
        a = fp2_mul(a, a, d, p);
        e >>= 1;
    }
    r
}

/// Dickson tower on the `p + 1` side: for `w ∈ T₂` (norm one) `w⁻¹ = w̄`,
/// so `w + w⁻¹ = 2·Re(w) ∈ F_p` and `D₂(x) = x² − 2` maps the trace of `w`
/// to the trace of `w²`. `V` is the trace image of `u·⟨ζ⟩`, `ζ` of order
/// `2^t` in `T₂`; the final constant is `Tr(u^{2^t})`.
fn torus(p: u64, t: usize, rng: &mut StdRng) -> Tower {
    assert!(
        (p + 1).is_multiple_of(1u64 << t),
        "2^{t} does not divide p + 1"
    );
    let d = loop {
        let d = rng.gen_range(2..p);
        if powm(d, (p - 1) / 2, p) == p - 1 {
            break d;
        }
    };
    // z^{p-1} = z̄ / z ∈ T₂ (Frobenius is conjugation)
    let to_t2 = |z: (u64, u64)| fp2_pow(z, p - 1, d, p);
    let zeta = loop {
        let z = (rng.gen_range(0..p), rng.gen_range(1..p));
        let zt = fp2_pow(to_t2(z), (p + 1) >> t, d, p);
        if t == 0 || fp2_pow(zt, 1u64 << (t - 1), d, p) != (1, 0) {
            break zt;
        }
    };
    loop {
        let u = to_t2((rng.gen_range(0..p), rng.gen_range(1..p)));
        let mut w = u;
        let mut v = Vec::with_capacity(1 << t);
        for _ in 0..1u64 << t {
            v.push(addm(w.0, w.0, p));
            w = fp2_mul(w, zeta, d, p);
        }
        let mut s = v.clone();
        s.sort_unstable();
        s.dedup();
        if s.len() != 1 << t {
            continue;
        }
        let ut = fp2_pow(u, 1u64 << t, d, p);
        return Tower {
            kind: Kind::Torus,
            t,
            size: 1 << t,
            v,
            scale: 1,
            steps: vec![Step::Dickson; t],
            c: addm(ut.0, ut.0, p),
            info: json!({"d": d, "u": [u.0, u.1], "zeta": [zeta.0, zeta.1]}),
        };
    }
}

fn random_point(curve: &PrimeCurve, rng: &mut StdRng) -> PrimePoint {
    loop {
        let x = rng.gen_range(0..curve.p);
        let r = curve.rhs(x);
        if r == 0 {
            continue;
        }
        if let Some(y) = curve.sqrt(r) {
            let y = if rng.gen::<bool>() { y } else { curve.p - y };
            return PrimePoint::affine(x, y);
        }
    }
}

/// The 2-isogeny with kernel `(ξ, 0)`, on a point (Vélu).
fn velu_map(pt: PrimePoint, xi: u64, tau: u64, p: u64) -> PrimePoint {
    if pt.infinity || pt.x == xi {
        return PrimePoint::INFINITY;
    }
    let d = invm(subm(pt.x, xi, p), p);
    let x = addm(pt.x, mulm(tau, d, p), p);
    let y = mulm(pt.y, subm(1, mulm(tau, mulm(d, d, p), p), p), p);
    PrimePoint::affine(x, y)
}

fn nonsingular(a: u64, b: u64, p: u64) -> bool {
    let d = addm(
        mulm(4, mulm(mulm(a, a, p), a, p), p),
        mulm(27, mulm(b, b, p), p),
        p,
    );
    d != 0
}

/// A tower of 2-isogenies on an auxiliary curve `E'` with a rational
/// point `Q` of order `2^t`; `V = x(R' + ⟨Q⟩)`.  The search for `E'` is
/// the per-curve precomputation the oracle's base charges; here it is
/// only reported.
fn isogeny(p: u64, t: usize, rng: &mut StdRng) -> Tower {
    isogeny_with_auxiliary(p, t, rng, false)
}

/// The opt-in auxiliary curve is independent of the target curve. For a
/// prime p = 3 (mod 4), y² = x³ + x has trace zero and order p+1.
/// Its rational 2-primary subgroup is cyclic (only (0,0) is 2-torsion).
/// This avoids exhaustive point counting on every trial curve at M31.
fn isogeny_with_auxiliary(p: u64, t: usize, rng: &mut StdRng, supersingular: bool) -> Tower {
    assert!((1..63).contains(&t), "isogeny tower needs 1 <= t < 63");
    let two_t = 1u64 << t;
    if supersingular {
        assert_eq!(p % 4, 3, "--aux-supersingular requires p = 3 mod 4");
        assert!((p + 1).is_multiple_of(two_t), "2^t must divide p+1");
        assert!(
            two_t <= (p + 1) / 4,
            "auxiliary curve needs a non-2-torsion quotient coset"
        );
    }
    let mut ops = GroupOps::default();
    let mut curves_tried = 0u64;
    loop {
        curves_tried += 1;
        let (a, b) = if supersingular {
            (1, 0)
        } else {
            (rng.gen_range(0..p), rng.gen_range(1..p))
        };
        if !nonsingular(a, b, p) {
            continue;
        }
        let e = PrimeCurve { p, a, b };
        let n = if supersingular {
            p + 1
        } else {
            e.point_count()
        };
        if !n.is_multiple_of(two_t) {
            continue;
        }
        // Q of exact order 2^t.
        let mut q = None;
        for _ in 0..16 {
            let cand = e.mul(&mut ops, random_point(&e, rng), n / two_t);
            let half = e.mul(&mut ops, cand, two_t / 2);
            if !half.infinity && e.mul(&mut ops, cand, two_t).infinity {
                q = Some(cand);
                break;
            }
        }
        let Some(q) = q else { continue };
        let multiples: Vec<PrimePoint> = (0..two_t).map(|k| e.mul(&mut ops, q, k)).collect();
        // R' with 2R' outside <Q>, so R' + <Q> and its negative are disjoint.
        let r0 = loop {
            let r = random_point(&e, rng);
            let r2 = e.double(&mut ops, r);
            if !multiples.contains(&r2) {
                break r;
            }
        };
        let v: Vec<u64> = multiples
            .iter()
            .map(|&m| e.add(&mut ops, r0, m))
            .filter(|pt| !pt.infinity)
            .map(|pt| pt.x)
            .collect();
        let mut s = v.clone();
        s.sort_unstable();
        s.dedup();
        if s.len() != two_t as usize {
            continue;
        }
        // The chain: kernel of step j is [2^{t−1−j}] Q_j on E'_j.
        let (mut aj, mut bj) = (a, b);
        let (mut qj, mut rj) = (q, r0);
        let mut steps = Vec::with_capacity(t);
        for j in 0..t {
            let cj = PrimeCurve { p, a: aj, b: bj };
            let kj = cj.mul(&mut ops, qj, 1u64 << (t - 1 - j));
            assert!(
                !kj.infinity && kj.y == 0,
                "step {j}: kernel point is not 2-torsion"
            );
            let xi = kj.x;
            let tau = addm(mulm(3, mulm(xi, xi, p), p), aj, p);
            steps.push(Step::Velu { xi, tau });
            qj = velu_map(qj, xi, tau, p);
            rj = velu_map(rj, xi, tau, p);
            aj = subm(aj, mulm(5, tau, p), p);
            bj = subm(bj, mulm(7, mulm(xi, tau, p), p), p);
            let next = PrimeCurve { p, a: aj, b: bj };
            assert!(
                next.is_on_curve(qj),
                "step {j}: Vélu image of Q is off the codomain"
            );
            assert!(
                next.is_on_curve(rj),
                "step {j}: Vélu image of R' is off the codomain"
            );
        }
        // V itself, since it cannot be rebuilt from two numbers: the
        // exhaustive cross-check (`verify.py`) needs it.
        let info = json!({"aux_a": a, "aux_b": b, "aux_order": n,
            "aux_curves_tried": curves_tried, "v": &v,
            "aux_construction": if supersingular { "supersingular-p-plus-one" } else { "random-search" },
            "kernel_generator": { "x": q.x, "y": q.y },
            "coset_representative": { "x": r0.x, "y": r0.y }});
        return Tower {
            kind: Kind::Isogeny,
            t,
            size: 1 << t,
            v,
            scale: 1,
            steps,
            c: rj.x,
            info,
        };
    }
}

/// `X(x) = x + Σ (v_Q/(x − x_Q) + u_Q/(x − x_Q)²)`, Vélu's x-map for
/// an odd-degree kernel given by half its non-zero points.
fn velu_odd_x(pts: &[(u64, u64, u64)], x: u64, p: u64) -> u64 {
    let mut out = x;
    for &(xq, vq, uq) in pts {
        let d = invm(subm(x, xq, p), p);
        out = addm(out, mulm(vq, d, p), p);
        out = addm(out, mulm(uq, mulm(d, d, p), p), p);
    }
    out
}

/// The degree of each level: `degrees` repeated cyclically (`[2]` is the
/// original tower).
fn level_degrees(degrees: &[u64], t: usize) -> Vec<u64> {
    (0..t).map(|j| degrees[j % degrees.len()]).collect()
}

/// `|V|` for a tower of `t` levels.
fn tower_size(kind: Kind, t: usize, degrees: &[u64]) -> u64 {
    match kind {
        Kind::Isogeny => level_degrees(degrees, t).iter().product(),
        _ => 1u64 << t,
    }
}

/// `#E(F_p)` by baby-step giant-step in the Hasse interval: every `M`
/// there with `[M]P = O` is found for random points `P`, and the
/// candidates are intersected until one is left (`O(p^{1/4})` group
/// operations a point).  Falls back to the exact `O(p)` count.
fn point_count_bsgs(e: &PrimeCurve, rng: &mut StdRng) -> u64 {
    let p = e.p;
    let mut ops = GroupOps::default();
    let s = (p as f64).sqrt() as u64 + 1;
    let lo = (p + 1).saturating_sub(2 * s);
    let width = 4 * s + 2;
    let m = (width as f64).sqrt() as u64 + 1;
    let key = |pt: PrimePoint| (pt.infinity, pt.x, pt.y);
    let mut cands: Option<Vec<u64>> = None;
    for _ in 0..24 {
        let pt = random_point(e, rng);
        let mut baby = std::collections::HashMap::new();
        let mut acc = PrimePoint::INFINITY;
        for j in 0..m {
            baby.entry(key(acc)).or_insert_with(Vec::new).push(j);
            acc = e.add(&mut ops, acc, pt);
        }
        let giant = e.mul(&mut ops, pt, m);
        let mut q = e.mul(&mut ops, pt, lo);
        let mut found = Vec::new();
        for i in 0..=width / m + 1 {
            // (lo + i·m + j)·P = O  ⇔  lo·P + i·mP = −jP
            let neg = if q.infinity {
                q
            } else {
                PrimePoint::affine(q.x, (p - q.y) % p)
            };
            if let Some(js) = baby.get(&key(neg)) {
                for &j in js {
                    let mm = lo + i * m + j;
                    if mm >= lo && mm <= lo + width {
                        found.push(mm);
                    }
                }
            }
            q = e.add(&mut ops, q, giant);
        }
        let next: Vec<u64> = match cands {
            None => found,
            Some(c) => c.into_iter().filter(|x| found.contains(x)).collect(),
        };
        if next.len() == 1 {
            return next[0];
        }
        cands = Some(next);
    }
    e.point_count()
}

fn is_prime_small(n: u64) -> bool {
    n >= 2
        && (2..)
            .take_while(|d| d * d <= n)
            .all(|d| !n.is_multiple_of(d))
}

/// An isogeny tower whose level `j` has prime degree `degrees[j mod k]`
/// (2, 3, 5, 7, …), x-only: an auxiliary curve `E'` with a point `Q` of
/// exact order `N = Π d_j`, `V = x(R' + ⟨Q⟩)` with `2R' ∉ ⟨Q⟩`, and level
/// `j` the Vélu isogeny whose kernel is the image of the order-`d_j` part
/// of `⟨[N/(d_0⋯d_j)]Q⟩`.  Kernel abscissae on each codomain are the
/// images of abscissae on `E'` under the levels before, so no
/// y-coordinate is carried; `y_Q² = x_Q³ + a_j x_Q + b_j` on `E'_j`.
/// `#E'` comes from [`point_count_bsgs`].
fn isogeny_general(p: u64, t: usize, degrees: &[u64], rng: &mut StdRng) -> Tower {
    let degs = level_degrees(degrees, t);
    for &d in &degs {
        assert!(is_prime_small(d), "isogeny level degree {d} is not prime");
    }
    let big_n: u64 = degs.iter().product();
    let mut primes: Vec<u64> = degs.clone();
    primes.sort_unstable();
    primes.dedup();
    let mut ops = GroupOps::default();
    let mut curves_tried = 0u64;
    loop {
        curves_tried += 1;
        let a = rng.gen_range(0..p);
        let b = rng.gen_range(1..p);
        if !nonsingular(a, b, p) {
            continue;
        }
        let e = PrimeCurve { p, a, b };
        let n = point_count_bsgs(&e, rng);
        if !n.is_multiple_of(big_n) {
            continue;
        }
        let mut q = None;
        for _ in 0..16 {
            let cand = e.mul(&mut ops, random_point(&e, rng), n / big_n);
            let exact = e.mul(&mut ops, cand, big_n).infinity
                && primes
                    .iter()
                    .all(|&l| !e.mul(&mut ops, cand, big_n / l).infinity);
            if exact {
                q = Some(cand);
                break;
            }
        }
        let Some(q) = q else { continue };
        let multiples: Vec<PrimePoint> = (0..big_n).map(|k| e.mul(&mut ops, q, k)).collect();
        let r0 = loop {
            let r = random_point(&e, rng);
            let r2 = e.double(&mut ops, r);
            if !multiples.contains(&r2) {
                break r;
            }
        };
        let v: Vec<u64> = multiples
            .iter()
            .map(|&m| e.add(&mut ops, r0, m))
            .filter(|pt| !pt.infinity)
            .map(|pt| pt.x)
            .collect();
        let mut sorted = v.clone();
        sorted.sort_unstable();
        sorted.dedup();
        if sorted.len() != big_n as usize {
            continue;
        }
        let (mut aj, mut bj) = (a, b);
        let mut steps: Vec<Step> = Vec::with_capacity(t);
        let mut done = 1u64;
        for (j, &d) in degs.iter().enumerate() {
            done *= d;
            let base = e.mul(&mut ops, q, big_n / done);
            // Half the kernel, as abscissae on E'_j: images of k·base on E'.
            let half: Vec<u64> = (1..=d / 2)
                .map(|k| {
                    let pt = e.mul(&mut ops, base, k);
                    assert!(!pt.infinity, "level {j}: kernel point at infinity on E'");
                    steps.iter().fold(pt.x, |x, st| match st {
                        Step::Velu { xi, tau } => {
                            addm(x, mulm(*tau, invm(subm(x, *xi, p), p), p), p)
                        }
                        Step::VeluOdd { pts } => velu_odd_x(pts, x, p),
                        _ => unreachable!(),
                    })
                })
                .collect();
            let cj = PrimeCurve { p, a: aj, b: bj };
            for &xq in &half {
                let r = cj.rhs(xq);
                assert!(
                    r == 0 || cj.legendre(r) == 1,
                    "level {j}: kernel abscissa {xq} is not on E'_{j}"
                );
            }
            if d == 2 {
                let xi = half[0];
                assert_eq!(
                    cj.rhs(xi),
                    0,
                    "level {j}: degree-2 kernel point is not 2-torsion"
                );
                let tau = addm(mulm(3, mulm(xi, xi, p), p), aj, p);
                steps.push(Step::Velu { xi, tau });
                aj = subm(aj, mulm(5, tau, p), p);
                bj = subm(bj, mulm(7, mulm(xi, tau, p), p), p);
            } else {
                let pts: Vec<(u64, u64, u64)> = half
                    .iter()
                    .map(|&xq| {
                        let vq = addm(mulm(6, mulm(xq, xq, p), p), mulm(2, aj, p), p);
                        let uq = mulm(4, cj.rhs(xq), p);
                        (xq, vq, uq)
                    })
                    .collect();
                let tsum = pts.iter().fold(0, |acc, &(_, vq, _)| addm(acc, vq, p));
                let wsum = pts.iter().fold(0, |acc, &(xq, vq, uq)| {
                    addm(acc, addm(uq, mulm(xq, vq, p), p), p)
                });
                aj = subm(aj, mulm(5, tsum, p), p);
                bj = subm(bj, mulm(7, wsum, p), p);
                steps.push(Step::VeluOdd { pts });
            }
            assert!(nonsingular(aj, bj, p), "level {j}: singular codomain");
        }
        let tower = Tower {
            kind: Kind::Isogeny,
            t,
            size: big_n as usize,
            v: v.clone(),
            scale: 1,
            steps,
            c: 0,
            info: Value::Null,
        };
        // Every element of V reaches one value; a random point of E' lands
        // on the last codomain (32 checks: a wrong codomain fails each
        // with probability about 1/2).
        let c = *tower.values(v[0], p).last().unwrap();
        let c = tower.apply(t - 1, c, p);
        for &x in &v {
            let y = tower.values(x, p);
            assert_eq!(
                tower.apply(t - 1, y[t - 1], p),
                c,
                "V does not reach one value"
            );
        }
        let last = PrimeCurve { p, a: aj, b: bj };
        let mut landed = 0;
        let mut tried = 0;
        while tried < 32 {
            let pt = random_point(&e, rng);
            let y = tower.values(pt.x, p);
            if y.iter().any(|&yj| {
                tower.steps.iter().any(|st| match st {
                    Step::Velu { xi, .. } => *xi == yj,
                    Step::VeluOdd { pts } => pts.iter().any(|&(xq, _, _)| xq == yj),
                    _ => false,
                })
            }) {
                continue;
            }
            tried += 1;
            let x_end = tower.apply(t - 1, y[t - 1], p);
            let r = last.rhs(x_end);
            if r == 0 || last.legendre(r) == 1 {
                landed += 1;
            }
        }
        assert_eq!(landed, 32, "a point of E' maps off the last codomain");
        let info = json!({"aux_a": a, "aux_b": b, "aux_order": n, "aux_curves_tried": curves_tried,
                          "degrees": degs, "size": big_n, "v": &v});
        return Tower { c, info, ..tower };
    }
}

fn build_tower(kind: Kind, p: u64, t: usize, degrees: &[u64], rng: &mut StdRng) -> Tower {
    let tower = match kind {
        Kind::Kummer => kummer(p, t, rng),
        Kind::Dickson => dickson(p, t, rng),
        Kind::Torus => torus(p, t, rng),
        Kind::Isogeny if degrees == [2] => isogeny(p, t, rng),
        Kind::Isogeny => isogeny_general(p, t, degrees, rng),
    };
    tower.check(p);
    tower
}

// ── Targets ────────────────────────────────────────────────────────

/// A target and, when planted, the full solution of its system.
struct Target {
    planted: bool,
    x_r: u64,
    /// Values of every variable at the planted solution.
    solution: Option<Vec<u64>>,
    /// The planted abscissae, for the naive control.
    xs: Vec<u64>,
}

/// Plant `R = P_1 + … + P_m` over distinct base abscissae with random
/// signs; `None` when the partial sums hit the identity.
fn plant(
    curve: &PrimeCurve,
    tower: &Tower,
    m: usize,
    on: &[u64],
    rng: &mut StdRng,
) -> Option<Target> {
    let p = curve.p;
    let mut ops = GroupOps::default();
    let mut pick: Vec<u64> = Vec::with_capacity(m);
    while pick.len() < m {
        let x = on[rng.gen_range(0..on.len())];
        if !pick.contains(&x) {
            pick.push(x);
        }
    }
    let pts: Vec<PrimePoint> = pick
        .iter()
        .map(|&x| {
            let y = curve.sqrt(curve.rhs(x)).expect("abscissa on the curve");
            PrimePoint::affine(x, if rng.gen::<bool>() { y } else { p - y })
        })
        .collect();
    let mut acc = pts[0];
    let mut partial = Vec::new();
    for pt in &pts[1..] {
        acc = curve.add(&mut ops, acc, *pt);
        if acc.infinity {
            return None;
        }
        partial.push(acc.x);
    }
    let x_r = acc.x;
    let t = tower.t;
    let mut sol = vec![0u64; m * t + (m - 2)];
    for (i, &x) in pick.iter().enumerate() {
        sol[i * t..(i + 1) * t].copy_from_slice(&tower.values(x, p));
    }
    // The chain's free unknowns are the partial-sum abscissae x(P_1 + … + P_{k+1}).
    for k in 0..m - 2 {
        sol[m * t + k] = partial[k];
    }
    Some(Target {
        planted: true,
        x_r,
        solution: Some(sol),
        xs: pick,
    })
}

fn random_target(curve: &PrimeCurve, rng: &mut StdRng) -> Target {
    let x_r = random_point(curve, rng).x;
    Target {
        planted: false,
        x_r,
        solution: None,
        xs: Vec::new(),
    }
}

// ── Systems ────────────────────────────────────────────────────────

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum Control {
    Tower,
    Ladder,
    Naive,
    Null,
    /// The symmetrised presentation: unknowns are the elementary symmetric
    /// functions `e_k` of each tower level, `S̃_{m+1}(e; x_R)` replaces the
    /// `S₃` chain, and each Dickson level is the Graeffe-type map of the
    /// `e`'s (quadratic). Dickson-step towers with `scale = 1` only.
    Sym,
}

impl Control {
    fn name(self) -> &'static str {
        match self {
            Control::Tower => "tower",
            Control::Ladder => "ladder",
            Control::Naive => "naive",
            Control::Null => "null",
            Control::Sym => "sym",
        }
    }
}

/// The summation part: `S₃(x_1, x_2, x_R)` at `m = 2`; for `m ≥ 3` the
/// chain `S₃(x_1, x_2, u_1)`, `S₃(u_k, x_{k+2}, u_{k+1})`,
/// `S₃(u_{m−2}, x_m, x_R)`, whose free unknowns `u_k` are the abscissae of
/// the partial sums.
fn summation(tower: &Tower, curve: &PrimeCurve, m: usize, n: usize, x_r: u64) -> Vec<Pol> {
    let p = curve.p;
    let (a, b) = (curve.a, curve.b);
    let x = |i: usize| Pol::var(n, i * tower.t).scale(tower.scale, p);
    let xr = Pol::constant(n, x_r, p);
    if m == 2 {
        return vec![s3(&x(0), &x(1), &xr, a, b, p)];
    }
    let u = |k: usize| Pol::var(n, m * tower.t + k);
    let mut eqs = vec![s3(&x(0), &x(1), &u(0), a, b, p)];
    for k in 1..m - 2 {
        eqs.push(s3(&u(k - 1), &x(k + 1), &u(k), a, b, p));
    }
    eqs.push(s3(&u(m - 3), &x(m - 1), &xr, a, b, p));
    eqs
}

/// A random polynomial of degree at most two in `n` variables that
/// vanishes at `at`.
fn random_quadric(n: usize, at: &[u64], p: u64, rng: &mut StdRng) -> Pol {
    let mut f = Pol::zero(n);
    for i in 0..n {
        for j in i..n {
            let mut e = vec![0u32; n];
            e[i] += 1;
            e[j] += 1;
            f.terms.insert(e, rng.gen_range(1..p));
        }
        let mut e = vec![0u32; n];
        e[i] = 1;
        f.terms.insert(e, rng.gen_range(1..p));
    }
    let c = f.eval(at, p);
    f.sub(&Pol::constant(n, c, p), p)
}

/// The system for one (control, target), with its number of variables
/// and the planted solution in that system's variables.
fn system(
    control: Control,
    tower: &Tower,
    curve: &PrimeCurve,
    m: usize,
    target: &Target,
    g: usize,
    rng: &mut StdRng,
) -> (Vec<Pol>, usize, Option<Vec<u64>>, std::ops::Range<usize>) {
    let p = curve.p;
    let t = tower.t;
    if control == Control::Naive {
        // Two unknowns x_1, x_2 and one univariate membership each.
        assert_eq!(m, 2);
        let n = 2;
        let k = 1u64 << t;
        let member = |i: usize| {
            let xi = Pol::var(n, i);
            let mut pw = Pol::constant(n, 1, p);
            for _ in 0..k {
                pw = pw.mul(&xi, p);
            }
            pw.sub(&Pol::constant(n, powm(tower.scale, k, p), p), p)
        };
        let s = s3(
            &Pol::var(n, 0),
            &Pol::var(n, 1),
            &Pol::constant(n, target.x_r, p),
            curve.a,
            curve.b,
            p,
        );
        let sol = target.planted.then(|| target.xs.clone());
        return (vec![s, member(0), member(1)], n, sol, 0..0);
    }
    if control == Control::Sym {
        let (eqs, n, sol) = sym_system(tower, curve, m, target);
        return (eqs, n, sol, 0..0);
    }
    let n = m * t + (m - 2);
    let mut eqs = summation(tower, curve, m, n, target.x_r);
    if control == Control::Null {
        // S₃'s support, random coefficients, planted zero.
        assert_eq!(m, 2);
        let mut f = Pol::zero(n);
        for e in eqs[0].terms.keys() {
            f.terms.insert(e.clone(), rng.gen_range(1..p));
        }
        if let Some(sol) = &target.solution {
            let c = f.eval(sol, p);
            f = f.sub(&Pol::constant(n, c, p), p);
        }
        eqs[0] = f;
    }
    let towers_from = eqs.len();
    for i in 0..m {
        eqs.extend(tower.equations(n, i * t, p));
    }
    let towers = towers_from..eqs.len();
    if control == Control::Ladder {
        let sol = target
            .solution
            .as_ref()
            .expect("the ladder runs on planted targets");
        for _ in 1..g {
            eqs.push(random_quadric(n, sol, p, rng));
        }
    }
    (eqs, n, target.solution.clone(), towers)
}

// ── Symmetrised presentation ───────────────────────────────────────

/// Determinant of a square matrix over `F_p` (Gaussian elimination).
fn det_mod(mut a: Vec<Vec<u64>>, p: u64) -> u64 {
    let n = a.len();
    let mut det = 1u64;
    for c in 0..n {
        let Some(r) = (c..n).find(|&r| a[r][c] != 0) else {
            return 0;
        };
        if r != c {
            a.swap(r, c);
            det = subm(0, det, p);
        }
        det = mulm(det, a[c][c], p);
        let inv = invm(a[c][c], p);
        for r in c + 1..n {
            if a[r][c] != 0 {
                let f = mulm(a[r][c], inv, p);
                for k in c..n {
                    a[r][k] = subm(a[r][k], mulm(f, a[c][k], p), p);
                }
            }
        }
    }
    det
}

/// `Res_U(f, g)` of two univariate polynomials given low → high with their
/// formal degrees `len − 1` (Sylvester determinant).
fn resultant(f: &[u64], g: &[u64], p: u64) -> u64 {
    let (df, dg) = (f.len() - 1, g.len() - 1);
    let n = df + dg;
    let mut m = vec![vec![0u64; n]; n];
    for i in 0..dg {
        for (j, &c) in f.iter().rev().enumerate() {
            m[i][i + j] = c;
        }
    }
    for i in 0..df {
        for (j, &c) in g.iter().rev().enumerate() {
            m[dg + i][i + j] = c;
        }
    }
    det_mod(m, p)
}

/// Coefficients (low → high) of the polynomial through `(xs, ys)`.
fn interpolate(xs: &[u64], ys: &[u64], p: u64) -> Vec<u64> {
    let n = xs.len();
    let mut out = vec![0u64; n];
    for i in 0..n {
        // basis polynomial Π_{j≠i} (X − x_j) / (x_i − x_j)
        let mut num = vec![1u64];
        let mut den = 1u64;
        for j in 0..n {
            if j != i {
                let mut nx = vec![0u64; num.len() + 1];
                for (k, &c) in num.iter().enumerate() {
                    nx[k + 1] = addm(nx[k + 1], c, p);
                    nx[k] = subm(nx[k], mulm(c, xs[j], p), p);
                }
                num = nx;
                den = mulm(den, subm(xs[i], xs[j], p), p);
            }
        }
        let w = mulm(ys[i], invm(den, p), p);
        for (k, &c) in num.iter().enumerate() {
            out[k] = addm(out[k], mulm(c, w, p), p);
        }
    }
    out
}

/// `S₃(x_1, x_2, U)` as a polynomial in `U`, low → high.
fn s3_in_u(x1: u64, x2: u64, a: u64, b: u64, p: u64) -> Vec<u64> {
    let s = addm(x1, x2, p);
    let pr = mulm(x1, x2, p);
    let q = subm(pr, a, p);
    let c0 = subm(mulm(q, q, p), mulm(mulm(4, b, p), s, p), p);
    let inner = addm(mulm(s, addm(pr, a, p), p), mulm(2, b, p), p);
    let c1 = subm(0, mulm(2, inner, p), p);
    let d = subm(x1, x2, p);
    vec![c0, c1, mulm(d, d, p)]
}

/// `S_{k+1}(x_1, …, x_k, x_R)` at a point, by
/// `S_{k+1} = Res_U(S₃(x_1, x_2, U), S_k(U, x_3, …, x_k, x_R))`.
fn semaev_eval(xs: &[u64], x_r: u64, a: u64, b: u64, p: u64) -> u64 {
    let k = xs.len();
    let s3 = s3_in_u(xs[0], xs[1], a, b, p);
    if k == 2 {
        return addm(addm(s3[0], mulm(s3[1], x_r, p), p), mulm(s3[2], mulm(x_r, x_r, p), p), p);
    }
    let deg = 1usize << (k - 2);
    let us: Vec<u64> = (1..=deg as u64 + 1).collect();
    let ys: Vec<u64> = us
        .iter()
        .map(|&u| {
            let mut args = vec![u];
            args.extend_from_slice(&xs[2..]);
            semaev_eval(&args, x_r, a, b, p)
        })
        .collect();
    let g = interpolate(&us, &ys, p);
    resultant(&s3, &g, p)
}

/// Elementary symmetric functions `e_1 … e_m` of `xs`.
fn elementary(xs: &[u64], p: u64) -> Vec<u64> {
    let mut e = vec![1u64];
    for &x in xs {
        let mut ne = vec![0u64; e.len() + 1];
        for (k, &c) in e.iter().enumerate() {
            ne[k] = addm(ne[k], c, p);
            ne[k + 1] = addm(ne[k + 1], mulm(c, x, p), p);
        }
        e = ne;
    }
    e[1..].to_vec()
}

/// All exponent vectors of length `m` with sum at most `d`.
fn monomials(m: usize, d: u32) -> Vec<Vec<u32>> {
    let mut out = Vec::new();
    let mut cur = vec![0u32; m];
    fn rec(i: usize, left: u32, cur: &mut Vec<u32>, out: &mut Vec<Vec<u32>>) {
        if i == cur.len() {
            out.push(cur.clone());
            return;
        }
        for k in 0..=left {
            cur[i] = k;
            rec(i + 1, left - k, cur, out);
        }
        cur[i] = 0;
    }
    rec(0, d, &mut cur, &mut out);
    out
}

/// `S̃_{m+1}(e_1, …, e_m; x_R)`: the unique polynomial with
/// `S̃(e(x)) = S_{m+1}(x, x_R)`, over the monomials `e^α`, `Σα ≤ 2^{m−1}`
/// (the degree of `S_{m+1}` in each argument). Fitted on random points and
/// checked on 16 more; a mismatch stops the run.
fn semaev_symmetric(m: usize, x_r: u64, a: u64, b: u64, p: u64) -> Vec<(Vec<u32>, u64)> {
    let mons = monomials(m, 1u32 << (m - 1));
    let nm = mons.len();
    let rows = nm + 16;
    let mut rng = StdRng::seed_from_u64(x_r ^ 0x5eed_5e3a);
    let mut mat: Vec<Vec<u64>> = Vec::with_capacity(rows);
    while mat.len() < rows {
        let xs: Vec<u64> = (0..m).map(|_| rng.gen_range(0..p)).collect();
        let e = elementary(&xs, p);
        let mut row: Vec<u64> = mons
            .iter()
            .map(|al| {
                al.iter()
                    .zip(&e)
                    .fold(1u64, |acc, (&k, &ek)| mulm(acc, powm(ek, k as u64, p), p))
            })
            .collect();
        row.push(semaev_eval(&xs, x_r, a, b, p));
        mat.push(row);
    }
    // Row-reduce the overdetermined system; leftover rows must vanish.
    let mut piv_row = 0usize;
    let mut pivots = Vec::with_capacity(nm);
    for c in 0..nm {
        let Some(r) = (piv_row..rows).find(|&r| mat[r][c] != 0) else {
            panic!("S̃ fit: monomial {c} undetermined");
        };
        mat.swap(r, piv_row);
        let inv = invm(mat[piv_row][c], p);
        for k in c..=nm {
            mat[piv_row][k] = mulm(mat[piv_row][k], inv, p);
        }
        for r in 0..rows {
            if r != piv_row && mat[r][c] != 0 {
                let f = mat[r][c];
                for k in c..=nm {
                    mat[r][k] = subm(mat[r][k], mulm(f, mat[piv_row][k], p), p);
                }
            }
        }
        pivots.push(piv_row);
        piv_row += 1;
    }
    for r in piv_row..rows {
        assert_eq!(mat[r][nm], 0, "S̃ fit inconsistent: S_{} is not symmetric of this degree", m + 1);
    }
    mons.into_iter()
        .zip(pivots)
        .map(|(al, r)| (al, mat[r][nm]))
        .filter(|(_, c)| *c != 0)
        .collect()
}

/// One squaring level on the `e`'s: from `e` (the elementary symmetric
/// functions of the `y_i`) the elementary symmetric functions of
/// `y_i² − shift` (`shift = 2`: Dickson `D_2`; `shift = 0`: Kummer). With
/// `f(X) = Π(X − y_i)`, `Π(Z − y_i²) = (−1)^m f(√Z) f(−√Z)` (the even part
/// of `f(X)·f(−X)`), then `Z = Y + shift`.
fn graeffe_shifted(e: &[Pol], shift: u64, p: u64) -> Vec<Pol> {
    let m = e.len();
    let n = e[0].n;
    // f low → high: f[m] = 1, f[m−k] = (−1)^k e_k
    let mut f = vec![Pol::zero(n); m + 1];
    f[m] = Pol::constant(n, 1, p);
    for k in 1..=m {
        f[m - k] = if k % 2 == 0 { e[k - 1].clone() } else { e[k - 1].scale(p - 1, p) };
    }
    let fneg: Vec<Pol> = f
        .iter()
        .enumerate()
        .map(|(i, c)| if i % 2 == 0 { c.clone() } else { c.scale(p - 1, p) })
        .collect();
    let mut prod = vec![Pol::zero(n); 2 * m + 1];
    for i in 0..=m {
        for j in 0..=m {
            prod[i + j] = prod[i + j].add(&f[i].mul(&fneg[j], p), p);
        }
    }
    let sign = if m % 2 == 0 { 1 } else { p - 1 };
    let h: Vec<Pol> = (0..=m).map(|j| prod[2 * j].scale(sign, p)).collect();
    // g(Y) = h(Y + shift): g_i = Σ_{j ≥ i} C(j, i) shift^{j−i} h_j
    let mut g = vec![Pol::zero(n); m + 1];
    for (j, hj) in h.iter().enumerate() {
        let mut binom = 1u64;
        for i in (0..=j).rev() {
            // C(j, i) for i descending from j
            let coef = mulm(binom % p, powm(shift, (j - i) as u64, p), p);
            g[i] = g[i].add(&hj.scale(coef, p), p);
            if i > 0 {
                binom = binom * i as u64 / (j - i + 1) as u64;
            }
        }
    }
    (1..=m)
        .map(|k| if k % 2 == 0 { g[m - k].clone() } else { g[m - k].scale(p - 1, p) })
        .collect()
}

fn binom_u64(n: usize, k: usize) -> u64 {
    let mut r = 1u64;
    for i in 0..k {
        r = r * (n - i) as u64 / (i + 1) as u64;
    }
    r
}

/// Whether the symmetrised presentation is defined for this tower: every
/// step a Dickson `D_2` or every step a squaring (Kummer, any scale). Vélu
/// steps are rational maps with no polynomial map on the `e`'s.
fn sym_applies(tower: &Tower) -> bool {
    (tower.scale == 1 && tower.steps.iter().all(|s| matches!(s, Step::Dickson)))
        || tower.steps.iter().all(|s| matches!(s, Step::Square))
}

/// The symmetrised system: variables `E^{(j)}_k` at `j·m + (k − 1)`,
/// `j < t`, the elementary symmetric functions of the level-`j` values
/// `y_{i,j}` (`x_i = scale · y_{i,0}`); `S̃(scale^k E^{(0)}_k; x_R) = 0`,
/// `G(E^{(j)}) = E^{(j+1)}`, `G(E^{(t−1)}) = (C(m,k) c^k)_k`, with `G` the
/// Graeffe map of the tower's step (shifted by 2 for Dickson).
fn sym_system(tower: &Tower, curve: &PrimeCurve, m: usize, target: &Target) -> (Vec<Pol>, usize, Option<Vec<u64>>) {
    let p = curve.p;
    let t = tower.t;
    assert!(
        sym_applies(tower),
        "the sym presentation needs a Dickson-step tower with scale 1 or a Kummer (squaring) tower"
    );
    let shift = if matches!(tower.steps[0], Step::Dickson) { 2 } else { 0 };
    let n = m * t;
    let var = |j: usize, k: usize| Pol::var(n, j * m + k);
    let mut eqs = Vec::new();
    let mut s = Pol::zero(n);
    for (al, c) in semaev_symmetric(m, target.x_r, curve.a, curve.b, p) {
        // e_k(x) = scale^k e_k(y_0): the monomial Π e_k^{α_k} picks up
        // scale^{Σ k α_k}.
        let weight: u64 = al.iter().enumerate().map(|(k, &a)| (k as u64 + 1) * a as u64).sum();
        let c = mulm(c, powm(tower.scale, weight, p), p);
        let mut e = al.clone();
        e.resize(n, 0);
        s.terms.insert(e, c);
    }
    eqs.push(s);
    for j in 0..t {
        let lvl: Vec<Pol> = (0..m).map(|k| var(j, k)).collect();
        let next = graeffe_shifted(&lvl, shift, p);
        for k in 0..m {
            let rhs = if j + 1 < t {
                var(j + 1, k)
            } else {
                Pol::constant(n, mulm(binom_u64(m, k + 1) % p, powm(tower.c, (k + 1) as u64, p), p), p)
            };
            eqs.push(next[k].sub(&rhs, p));
        }
    }
    let sol = target.solution.as_ref().map(|raw| {
        let mut v = vec![0u64; n];
        for j in 0..t {
            let ys: Vec<u64> = (0..m).map(|i| raw[i * t + j]).collect();
            v[j * m..(j + 1) * m].copy_from_slice(&elementary(&ys, p));
        }
        v
    });
    (eqs, n, sol)
}

// ── Measuring ──────────────────────────────────────────────────────

struct Measured {
    report: F4Report,
    planted_ok: Option<bool>,
    zero_dim: bool,
    linear: usize,
}

fn measure(
    eqs: &[Pol],
    n: usize,
    p: u64,
    sol: Option<&[u64]>,
    max_degree: u32,
    budget: Duration,
    stop_below: Option<usize>,
) -> Measured {
    if let Some(s) = sol {
        for (k, e) in eqs.iter().enumerate() {
            assert_eq!(
                e.eval(s, p),
                0,
                "equation {k} does not vanish at the planted solution"
            );
        }
    }
    let input: Vec<Poly> = eqs
        .iter()
        .map(|e| e.to_poly(p))
        .filter(|f| !f.is_empty())
        .collect();
    // Optionally stop once at most `stop_below` candidate points remain: the
    // steps after that only certify the basis, and on planted systems at
    // large N it is they, not the solve, that exhaust memory.
    let mut opts = F4Options::new(Ordering::Grevlex, max_degree).with_budget(budget);
    if let Some(b) = stop_below {
        opts = opts.stopping_below(b);
    }
    let report = f4_fp::f4(&input, n, p, &opts);
    let planted_ok =
        sol.map(|s| !report.inconsistent && report.basis.iter().all(|f| f4_fp::eval(f, s, p) == 0));
    let pure = |k: usize| {
        report.basis.iter().any(|f| {
            f.first()
                .map(|(e, _)| e.iter().enumerate().all(|(i, &x)| (i == k) == (x > 0)))
                .unwrap_or(false)
        })
    };
    let zero_dim = report.inconsistent || (0..n).all(pure);
    let linear = report
        .basis
        .iter()
        .filter(|f| {
            f.first()
                .map(|(e, _)| e.iter().sum::<u32>() == 1)
                .unwrap_or(false)
        })
        .count();
    Measured {
        report,
        planted_ok,
        zero_dim,
        linear,
    }
}

/// What one run reports, in the fields every row carries; `extra` holds
/// the engine's own fields and is merged into the row.
struct Outcome {
    solving_degree_max: u32,
    last_productive_degree: u32,
    degree_reached: u32,
    max_cols_to_solution: usize,
    steps_to_solution: usize,
    inconsistent: bool,
    zero_dim: bool,
    linear: usize,
    basis_len: usize,
    steps: usize,
    max_rows: usize,
    max_cols: usize,
    ms: f64,
    timed_out: bool,
    pairs_above_bound: usize,
    staircase_at_stop: Option<usize>,
    planted_ok: Option<bool>,
    extra: Value,
}

impl Outcome {
    fn from_f4(r: &Measured) -> Self {
        Outcome {
            solving_degree_max: r.report.solving_degree_max,
            last_productive_degree: r.report.solving_degree,
            degree_reached: r.report.degree_reached,
            max_cols_to_solution: r.report.max_cols_to_solution,
            steps_to_solution: r.report.steps_to_solution,
            inconsistent: r.report.inconsistent,
            zero_dim: r.zero_dim,
            linear: r.linear,
            basis_len: r.report.basis.len(),
            steps: r.report.steps,
            max_rows: r.report.max_rows,
            max_cols: r.report.max_cols,
            ms: r.report.ms,
            timed_out: r.report.timed_out,
            pairs_above_bound: r.report.pairs_above_bound,
            staircase_at_stop: r.report.staircase_at_stop,
            planted_ok: r.planted_ok,
            extra: json!({"engine": "f4_fp"}),
        }
    }
}

/// The tower quotient ring of an `m`-summand system: `m` blocks of the
/// tower's rules, then the chain's `m − 2` free unknowns.
fn tower_ring(tower: &Tower, m: usize, p: u64) -> TowerRing {
    let mut rules = Vec::with_capacity(m * tower.t);
    for i in 0..m {
        rules.extend(tower.square_rules(i * tower.t, p));
    }
    TowerRing {
        p,
        rules,
        n_free: m - 2,
    }
}

fn raw_terms(e: &Pol) -> Vec<(Vec<u32>, u64)> {
    e.terms.iter().map(|(k, v)| (k.clone(), *v)).collect()
}

/// Run `f4_fp_tower` on a system: the tower equations become the ring's
/// rewriting, and the other equations its input in normal form.
fn measure_tower(
    eqs: &[Pol],
    towers: std::ops::Range<usize>,
    ring: &TowerRing,
    sol: Option<&[u64]>,
    max_degree: u32,
    budget: Duration,
    stop_below: Option<usize>,
    max_nnz: Option<u64>,
    trace: bool,
) -> (Outcome, Vec<RPoly>) {
    let p = ring.p;
    if let Some(s) = sol {
        for (k, e) in eqs.iter().enumerate() {
            assert_eq!(
                e.eval(s, p),
                0,
                "equation {k} does not vanish at the planted solution"
            );
        }
    }
    for k in towers.clone() {
        assert!(
            ring.from_raw(&raw_terms(&eqs[k])).is_empty(),
            "tower equation {k} is not zero in the ring: the square rules are wrong"
        );
    }
    let input: Vec<RPoly> = eqs
        .iter()
        .enumerate()
        .filter(|(k, _)| !towers.contains(k))
        .map(|(_, e)| ring.from_raw(&raw_terms(e)))
        .filter(|f| !f.is_empty())
        .collect();
    let ring_degrees: Vec<u32> = input.iter().map(RPoly::degree).collect();
    let mut opts = TowerF4Options::new(max_degree).with_budget(budget);
    if let Some(b) = stop_below {
        opts = opts.stopping_below(b);
    }
    if let Some(c) = max_nnz {
        opts = opts.with_max_nnz(c);
    }
    let r = f4_fp_tower::f4_tower(&input, ring, &opts);
    if trace {
        for (k, st) in r.trace.iter().enumerate() {
            eprintln!(
                "tower step {}: degree {}, {} critical + {} tower pairs, {} S-rows + {} reducers + {} promoted x {} cols, nnz {}, residue {} x {}, fresh {} (lowest degree {}), basis {}, pairs left {}, {:.1} ms (rows {:.0}, A {:.0}, B {:.0}, update {:.0})",
                k + 1,
                st.degree,
                st.critical_pairs,
                st.tower_pairs,
                st.s_rows,
                st.reducer_rows,
                st.promoted_rows,
                st.cols,
                st.nnz,
                st.residual_rows,
                st.residual_cols,
                st.fresh,
                st.fresh_min_degree,
                st.basis_active,
                st.pairs_left,
                st.ms,
                st.ms_rows,
                st.ms_reduce,
                st.ms_echelon,
                st.ms_update
            );
        }
    }
    let planted_ok = sol.map(|s| !r.inconsistent && r.basis.iter().all(|f| ring.eval(f, s) == 0));
    let lms: Vec<u128> = r.basis.iter().filter_map(RPoly::lm).collect();
    let pure = |k: usize| {
        lms.iter().any(|&m| {
            let f = f4_fp_tower::free_of(m);
            f4_fp_tower::mask_of(m) == 0
                && (0..f4_fp_tower::MAX_FREE).all(|i| (i == k) == (f[i] > 0))
        })
    };
    let zero_dim = r.inconsistent || (0..ring.n_free).all(pure);
    let linear = lms
        .iter()
        .filter(|&&m| f4_fp_tower::degree_of(m) == 1)
        .count();
    let out = Outcome {
        solving_degree_max: r.solving_degree_max,
        last_productive_degree: r.last_productive_degree,
        degree_reached: r.degree_reached,
        max_cols_to_solution: r.max_cols_to_solution,
        steps_to_solution: r.steps_to_solution,
        inconsistent: r.inconsistent,
        zero_dim,
        linear,
        basis_len: r.basis.len(),
        steps: r.steps,
        max_rows: r.max_rows,
        max_cols: r.max_cols,
        ms: r.ms,
        // A run stopped for size did not finish either: its degree is a
        // lower bound, like a timeout's.
        timed_out: r.timed_out || r.oversize,
        pairs_above_bound: r.pairs_above_bound,
        staircase_at_stop: r.staircase_at_stop,
        planted_ok,
        extra: json!({
            "engine": "f4_fp_tower",
            "input_ring_degrees": ring_degrees,
            "muladds": r.muladds,
            "max_nnz": r.max_nnz,
            "max_residual_rows": r.max_residual_rows,
            "oversize": r.oversize,
            "critical_pairs_reduced": r.critical_pairs_reduced,
            "tower_pairs_reduced": r.tower_pairs_reduced,
            "pairs_product_skipped": r.pairs_product_skipped,
            "pairs_chain_skipped": r.pairs_chain_skipped,
            "reducer_rows": r.reducer_rows,
        }),
    };
    (out, r.basis)
}

// ── Driver ─────────────────────────────────────────────────────────

struct Args {
    p: u64,
    kinds: Vec<Kind>,
    ms: Vec<usize>,
    controls: Vec<Control>,
    t_min: usize,
    max_t: usize,
    max_t_m3: usize,
    max_t_m4: usize,
    planted: usize,
    /// Above this `t`, cells run refutations only: a planted system keeps
    /// processing pairs that reduce to zero long after it is solved, and at
    /// large `N` that tail, not the solve, exhausts memory.
    planted_max_t: usize,
    random: usize,
    budget: u64,
    seed: u64,
    ladder_ts: Vec<usize>,
    ladder_gs: Vec<usize>,
    out: Option<String>,
    /// Stop F4 once at most this many candidate points remain (off by
    /// default; every committed run was made without it).
    stop_below: Option<usize>,
    /// Diagnostic: F4's degree bound for every system, in place of
    /// `n + d + 6`. With `--dump`, shows what F4 knows at a given degree.
    cap: Option<u32>,
    /// Diagnostic: print every basis element of degree at most this, with
    /// tower variables named `y<summand>_<level>`.
    dump: Option<u32>,
    /// The engine: `f4_fp` on the raw system (the default, and every
    /// committed pilot row), or `f4_fp_tower` on the tower quotient ring.
    engine: Engine,
    /// `--presentation sym`: the `tower` control solves the symmetrised
    /// system (see `sym_system`) where the tower allows it, and the raw one
    /// elsewhere (Vélu towers); each row records which. Default `raw`, the
    /// presentation of every committed pilot row.
    sym_presentation: bool,
    /// `f4_fp_tower` only: stop before a matrix with more non-zeros.
    max_nnz: Option<u64>,
    /// `f4_fp_tower` only: print one line per F4 step.
    trace: bool,
    /// Write every input system, before it is solved, to this directory in
    /// msolve's input format (`<id>.ms`), with the planted solution, if any,
    /// in `<id>.sol.json`; each row then carries `export_id` and the file's
    /// `export_sha256`, so an external solver's run on the same bytes can be
    /// joined to the `f4_fp` row.
    export: Option<String>,
    /// Isogeny kind only: the prime degree of each level, repeated
    /// cyclically (`--iso-degrees 3`, `--iso-degrees 2,3`).  `[2]`, the
    /// default, is the original tower and its code path.
    degrees: Vec<u64>,
    /// Opt in to the known-order auxiliary y²=x³+x at p=3 mod 4.
    aux_supersingular: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum Engine {
    F4,
    Tower,
}

/// Rows as they are measured: every row reaches `--out` and is flushed
/// before the next system is built, so a run that exhausts memory on a
/// large cell keeps every cell before it.
struct Sink {
    rows: Vec<Value>,
    file: Option<File>,
}

impl Sink {
    fn push(&mut self, row: Value) {
        if let Some(f) = self.file.as_mut() {
            writeln!(f, "{row}").expect("write --out");
            f.flush().expect("flush --out");
        }
        self.rows.push(row);
    }
}

fn parse_args() -> Args {
    let mut a = Args {
        p: 786_433, // 3·2^18 + 1, so 2^t | p − 1 for every t ≤ 18
        kinds: vec![Kind::Kummer, Kind::Dickson, Kind::Isogeny],
        ms: vec![2, 3],
        controls: vec![Control::Tower, Control::Null, Control::Naive],
        t_min: 1,
        max_t: 10,
        max_t_m3: 5,
        max_t_m4: 3,
        planted: 3,
        planted_max_t: usize::MAX,
        random: 3,
        budget: 60,
        seed: 0x504B_4D54,
        ladder_ts: vec![4, 6],
        ladder_gs: vec![1, 2, 4, 8],
        out: None,
        stop_below: None,
        cap: None,
        dump: None,
        engine: Engine::F4,
        sym_presentation: false,
        max_nnz: None,
        trace: false,
        export: None,
        degrees: vec![2],
        aux_supersingular: false,
    };
    let args: Vec<String> = std::env::args().skip(1).collect();
    let list = |s: &str| -> Vec<usize> {
        if s == "none" {
            return Vec::new();
        }
        s.split(',').map(|x| x.parse().expect("a number")).collect()
    };
    let mut i = 0;
    while i < args.len() {
        if args[i] == "--trace" {
            a.trace = true;
            i += 1;
            continue;
        }
        if args[i] == "--aux-supersingular" {
            a.aux_supersingular = true;
            i += 1;
            continue;
        }
        let v = args.get(i + 1).cloned().unwrap_or_default();
        match args[i].as_str() {
            "--p" => a.p = v.parse().expect("--p"),
            "--kinds" => {
                a.kinds = v
                    .split(',')
                    .map(|k| match k {
                        "kummer" => Kind::Kummer,
                        "dickson" => Kind::Dickson,
                        "torus" => Kind::Torus,
                        "isogeny" => Kind::Isogeny,
                        other => panic!("unknown kind `{other}`"),
                    })
                    .collect()
            }
            "--m" => a.ms = list(&v),
            "--controls" => {
                a.controls = v
                    .split(',')
                    .map(|c| match c {
                        "tower" => Control::Tower,
                        "null" => Control::Null,
                        "naive" => Control::Naive,
                        "sym" => Control::Sym,
                        other => panic!("unknown control `{other}` (the ladder has its own flags)"),
                    })
                    .collect()
            }
            "--t-min" => a.t_min = v.parse().expect("--t-min"),
            "--max-t" => a.max_t = v.parse().expect("--max-t"),
            "--max-t-m3" => a.max_t_m3 = v.parse().expect("--max-t-m3"),
            "--max-t-m4" => a.max_t_m4 = v.parse().expect("--max-t-m4"),
            "--planted" => a.planted = v.parse().expect("--planted"),
            "--planted-max-t" => a.planted_max_t = v.parse().expect("--planted-max-t"),
            "--random" => a.random = v.parse().expect("--random"),
            "--budget" => a.budget = v.parse().expect("--budget"),
            "--seed" => a.seed = v.parse().expect("--seed"),
            "--ladder-t" => a.ladder_ts = list(&v),
            "--ladder-g" => a.ladder_gs = list(&v),
            "--out" => a.out = Some(v),
            "--stop-below" => a.stop_below = Some(v.parse().expect("--stop-below")),
            "--cap" => a.cap = Some(v.parse().expect("--cap")),
            "--engine" => {
                a.engine = match v.as_str() {
                    "f4" | "f4_fp" => Engine::F4,
                    "tower" | "f4_fp_tower" => Engine::Tower,
                    other => panic!("unknown engine `{other}`"),
                }
            }
            "--presentation" => {
                a.sym_presentation = match v.as_str() {
                    "raw" => false,
                    "sym" => true,
                    other => panic!("unknown presentation `{other}` (raw, sym)"),
                }
            }
            "--max-nnz" => a.max_nnz = Some(v.parse().expect("--max-nnz")),
            "--dump" => a.dump = Some(v.parse().expect("--dump")),
            "--export" => a.export = Some(v),
            "--iso-degrees" => {
                a.degrees = v
                    .split(',')
                    .map(|d| d.trim().parse().expect("--iso-degrees"))
                    .collect();
                assert!(!a.degrees.is_empty(), "--iso-degrees needs a degree");
            }
            other => panic!("unknown flag `{other}`"),
        }
        i += 2;
    }
    if a.aux_supersingular {
        assert_eq!(a.p % 4, 3, "--aux-supersingular requires p = 3 mod 4");
        assert_eq!(
            a.degrees,
            vec![2],
            "--aux-supersingular supports degree-2 chains"
        );
        assert!(
            a.kinds == [Kind::Isogeny],
            "--aux-supersingular requires --kinds isogeny"
        );
    }
    a
}

/// A target curve over `F_p` on which at least `need` abscissae of `V`
/// carry points.
fn target_curve(p: u64, tower: &Tower, need: usize, rng: &mut StdRng) -> (PrimeCurve, Vec<u64>) {
    loop {
        let a = rng.gen_range(0..p);
        let b = rng.gen_range(1..p);
        if !nonsingular(a, b, p) {
            continue;
        }
        let curve = PrimeCurve { p, a, b };
        let on: Vec<u64> = tower
            .v
            .iter()
            .copied()
            .filter(|&x| curve.legendre(curve.rhs(x)) == 1)
            .collect();
        if on.len() >= need {
            return (curve, on);
        }
    }
}

struct Cell {
    kind: Kind,
    m: usize,
    control: Control,
    t: usize,
    g: usize,
}

fn run_cell(cell: &Cell, a: &Args, sink: &mut Sink) -> bool {
    let p = a.p;
    let cell_seed = a.seed
        ^ ((cell.kind as u64) << 40)
        ^ ((cell.m as u64) << 32)
        ^ ((cell.t as u64) << 16)
        ^ (cell.g as u64);
    let mut rng = StdRng::seed_from_u64(cell_seed);
    let tower = if a.aux_supersingular {
        let tower = isogeny_with_auxiliary(p, cell.t, &mut rng, true);
        tower.check(p);
        tower
    } else {
        build_tower(cell.kind, p, cell.t, &a.degrees, &mut rng)
    };
    let (curve, on) = target_curve(p, &tower, cell.m.max(2), &mut rng);
    let mut targets = Vec::new();
    let planted = if cell.t > a.planted_max_t && cell.control != Control::Ladder {
        0
    } else {
        a.planted
    };
    while targets.len() < planted {
        if let Some(tg) = plant(&curve, &tower, cell.m, &on, &mut rng) {
            targets.push(tg);
        }
    }
    if cell.control != Control::Ladder {
        for _ in 0..a.random {
            targets.push(random_target(&curve, &mut rng));
        }
    }
    let mut any_finished = false;
    // `--presentation sym`: the tower control on the symmetrised system.
    let (sys_control, presentation) = match cell.control {
        Control::Sym => (Control::Sym, "sym"),
        Control::Tower if a.sym_presentation && sym_applies(&tower) => (Control::Sym, "sym"),
        Control::Tower if a.sym_presentation => (Control::Tower, "raw (sym undefined for this tower)"),
        c => (c, "raw"),
    };
    for (k, target) in targets.iter().enumerate() {
        let (eqs, n, sol, towers) = system(
            sys_control,
            &tower,
            &curve,
            cell.m,
            target,
            cell.g,
            &mut rng,
        );
        if a.engine == Engine::Tower && matches!(sys_control, Control::Naive | Control::Sym) {
            // The naive control has no tower to rewrite by.
            continue;
        }
        let exported = a.export.as_ref().map(|dir| {
            let id = format!(
                "{}-m{}-{}-t{}-g{}-{}{}-p{}",
                cell.kind.name(),
                cell.m,
                cell.control.name(),
                cell.t,
                cell.g,
                if target.planted { "planted" } else { "random" },
                k,
                p
            );
            export_system(dir, &id, &eqs, n, p, sol.as_deref())
        });
        let d_in: Vec<u32> = eqs.iter().map(Pol::degree).collect();
        let d_max = d_in.iter().copied().max().unwrap_or(1);
        let max_degree = match (a.cap, cell.control) {
            (Some(cap), _) => cap,
            (None, Control::Naive) => 2 * d_max + 8,
            (None, _) => n as u32 + d_max + 6,
        };
        let started = Instant::now();
        let (r, basis) = match a.engine {
            Engine::F4 => {
                let m = measure(
                    &eqs,
                    n,
                    p,
                    sol.as_deref(),
                    max_degree,
                    Duration::from_secs(a.budget),
                    a.stop_below,
                );
                let out = Outcome::from_f4(&m);
                (out, Dumpable::Raw(m.report.basis))
            }
            Engine::Tower => {
                let ring = tower_ring(&tower, cell.m, p);
                let (out, basis) = measure_tower(
                    &eqs,
                    towers,
                    &ring,
                    sol.as_deref(),
                    max_degree,
                    Duration::from_secs(a.budget),
                    a.stop_below,
                    a.max_nnz,
                    a.trace,
                );
                (out, Dumpable::Ring(basis))
            }
        };
        let wall = started.elapsed().as_secs_f64();
        if !r.timed_out {
            any_finished = true;
        }
        let mut row = json!({
            "kind": cell.kind.name(),
            "m": cell.m,
            "control": cell.control.name(),
            "presentation": presentation,
            "t": cell.t,
            "N": cell.m * cell.t,
            "V_size": tower.size,
            "log2_V": (tower.size as f64).log2(),
            "iso_degrees": if cell.kind == Kind::Isogeny { json!(level_degrees(&a.degrees, cell.t)) } else { Value::Null },
            "g": cell.g,
            "n_vars": n,
            "n_equations": eqs.len(),
            "input_degrees": d_in,
            "target": if target.planted { "planted" } else { "random" },
            "target_index": k,
            "x_r": target.x_r,
            "p": p,
            "curve": {"a": curve.a, "b": curve.b},
            "tower": tower.info,
            "max_degree_bound": max_degree,
            "solving_degree_max": r.solving_degree_max,
            "last_productive_degree": r.last_productive_degree,
            "degree_reached": r.degree_reached,
            "max_cols_to_solution": r.max_cols_to_solution,
            "steps_to_solution": r.steps_to_solution,
            "inconsistent": r.inconsistent,
            "zero_dim": r.zero_dim,
            "linear_basis_elements": r.linear,
            "basis_len": r.basis_len,
            "steps": r.steps,
            "max_rows": r.max_rows,
            "max_cols": r.max_cols,
            "ms": r.ms,
            "wall_s": wall,
            "timed_out": r.timed_out,
            "pairs_above_bound": r.pairs_above_bound,
            "staircase_at_stop": r.staircase_at_stop,
            "planted_ok": r.planted_ok,
        });
        if let (Some((id, sha)), Some(obj)) = (exported, row.as_object_mut()) {
            obj.insert("export_id".into(), json!(id));
            obj.insert("export_sha256".into(), json!(sha));
        }
        if let (Some(obj), Some(extra)) = (row.as_object_mut(), r.extra.as_object()) {
            for (k, v) in extra {
                obj.insert(k.clone(), v.clone());
            }
        }
        eprintln!(
            "{:8} m={} {:6} t={:2} N={:2} g={:2} {:7} Dmax={:3} reached={:3} cols_to_sol={:7} cols={:7} {:8.1} ms{}{}",
            cell.kind.name(),
            cell.m,
            cell.control.name(),
            cell.t,
            cell.m * cell.t,
            cell.g,
            if target.planted { "planted" } else { "random" },
            r.solving_degree_max,
            r.degree_reached,
            r.max_cols_to_solution,
            r.max_cols,
            r.ms,
            if r.timed_out { "  TIMEOUT" } else { "" },
            if r.planted_ok == Some(false) {
                "  PLANTED-VIOLATION"
            } else {
                ""
            },
        );
        if let Some(k) = a.dump {
            match &basis {
                Dumpable::Raw(b) => dump_basis(b, cell, k),
                Dumpable::Ring(b) => dump_ring_basis(b, cell, k),
            }
        }
        sink.push(row);
    }
    any_finished
}

/// Writes one input system in msolve's format: the variable names on the
/// first line, the characteristic on the second, then the polynomials
/// separated by commas. Variables are `x0 .. x{n-1}` in the pilot's own
/// order. Returns the id and the SHA-256 of the `.ms` bytes.
fn export_system(
    dir: &str,
    id: &str,
    eqs: &[Pol],
    n: usize,
    p: u64,
    sol: Option<&[u64]>,
) -> (String, String) {
    use sha2::{Digest, Sha256};
    use std::fmt::Write as _;
    std::fs::create_dir_all(dir).expect("create --export directory");
    let vars: Vec<String> = (0..n).map(|i| format!("x{i}")).collect();
    let mut text = format!("{}\n{p}\n", vars.join(","));
    let polys: Vec<String> = eqs
        .iter()
        .filter(|e| !e.terms.is_empty())
        .map(|e| {
            let mut f = String::new();
            for (k, (exp, c)) in e.terms.iter().rev().enumerate() {
                if k > 0 {
                    f.push('+');
                }
                write!(f, "{c}").unwrap();
                for (i, &d) in exp.iter().enumerate() {
                    match d {
                        0 => {}
                        1 => write!(f, "*x{i}").unwrap(),
                        _ => write!(f, "*x{i}^{d}").unwrap(),
                    }
                }
            }
            f
        })
        .collect();
    text.push_str(&polys.join(",\n"));
    text.push('\n');
    let path = format!("{dir}/{id}.ms");
    std::fs::write(&path, &text).expect("write --export system");
    let sha = hex::encode(Sha256::digest(text.as_bytes()));
    let side = json!({
        "id": id, "p": p, "n_vars": n, "n_equations": polys.len(),
        "variables": vars, "solution": sol, "ms_sha256": sha,
    });
    std::fs::write(format!("{dir}/{id}.sol.json"), format!("{side}\n"))
        .expect("write --export solution");
    (id.to_string(), sha)
}

/// A basis to print with `--dump`, from either engine.
enum Dumpable {
    Raw(Vec<Poly>),
    Ring(Vec<RPoly>),
}

/// `dump_basis` for a basis in the tower ring: the monomials are masks of
/// tower variables and free exponents.
fn dump_ring_basis(basis: &[RPoly], cell: &Cell, k: u32) {
    let as_raw: Vec<Poly> = basis
        .iter()
        .map(|f| {
            f.monos
                .iter()
                .zip(&f.coefs)
                .map(|(&m, &c)| {
                    let n_t = cell.m * cell.t;
                    let mut e = vec![0u32; n_t + cell.m.saturating_sub(2)];
                    let mask = f4_fp_tower::mask_of(m);
                    for (j, x) in e.iter_mut().enumerate().take(n_t) {
                        *x = ((mask >> j) & 1) as u32;
                    }
                    let fr = f4_fp_tower::free_of(m);
                    for k2 in 0..cell.m.saturating_sub(2) {
                        e[n_t + k2] = u32::from(fr[k2]);
                    }
                    (e, u64::from(c))
                })
                .collect()
        })
        .collect();
    dump_basis(&as_raw, cell, k);
}

/// Print the basis elements of degree at most `k`, low degree first, with
/// tower variables named `y<summand>_<level>` and the chain unknowns
/// `u<k>`.
fn dump_basis(basis: &[Poly], cell: &Cell, k: u32) {
    let name = |v: usize| -> String {
        if cell.control == Control::Naive {
            format!("x{v}")
        } else if v >= cell.m * cell.t {
            format!("u{}", v - cell.m * cell.t)
        } else {
            format!("y{}_{}", v / cell.t, v % cell.t)
        }
    };
    let degree = |f: &Poly| {
        f.iter()
            .map(|(e, _)| e.iter().sum::<u32>())
            .max()
            .unwrap_or(0)
    };
    let mut low: Vec<&Poly> = basis.iter().filter(|f| degree(f) <= k).collect();
    low.sort_by_key(|f| degree(f));
    for f in low {
        let terms: Vec<String> = f
            .iter()
            .map(|(e, c)| {
                let mon: Vec<String> = e
                    .iter()
                    .enumerate()
                    .filter(|&(_, &x)| x > 0)
                    .map(|(v, &x)| {
                        if x == 1 {
                            name(v)
                        } else {
                            format!("{}^{x}", name(v))
                        }
                    })
                    .collect();
                if mon.is_empty() {
                    c.to_string()
                } else {
                    format!("{c}·{}", mon.join("·"))
                }
            })
            .collect();
        eprintln!("  [deg {}] {}", degree(f), terms.join(" + "));
    }
}

fn main() {
    let a = parse_args();
    assert!(
        !(a.sym_presentation && a.engine == Engine::Tower),
        "--presentation sym runs on the f4_fp engine (f4_fp_tower rewrites by the raw tower)"
    );
    let started = Instant::now();
    let mut sink = Sink {
        rows: Vec::new(),
        file: a
            .out
            .as_ref()
            .map(|path| File::create(path).expect("create --out")),
    };
    // The tower systems and their naive and null controls, t upward until
    // a whole cell times out.
    for &kind in &a.kinds {
        for &m in &a.ms {
            let max_t = match m {
                2 => a.max_t,
                3 => a.max_t_m3,
                _ => a.max_t_m4,
            };
            // The null and naive controls are written for m = 2, and the
            // naive membership for the Kummer coset only.
            let controls: Vec<Control> = a
                .controls
                .iter()
                .copied()
                .filter(|c| match c {
                    Control::Tower => true,
                    Control::Null => m == 2,
                    Control::Naive => m == 2 && kind == Kind::Kummer,
                    Control::Ladder => false,
                    Control::Sym => m >= 2,
                })
                .collect();
            // m ≥ 3 needs m distinct base abscissae, so |V| ≥ 4.
            let t_min = if m >= 3 { a.t_min.max(2) } else { a.t_min };
            for control in controls {
                for t in t_min..=max_t {
                    // A coset larger than p/16 leaves too few target-curve
                    // abscissae outside it to mean anything, and an
                    // auxiliary curve with that much torsion is rare.
                    if tower_size(kind, t, &a.degrees) > a.p / 16 {
                        eprintln!(
                            "-- {} m={m} {}: |V| = {} > p/16 at t = {t}; stopping",
                            kind.name(),
                            control.name(),
                            tower_size(kind, t, &a.degrees)
                        );
                        break;
                    }
                    let cell = Cell {
                        kind,
                        m,
                        control,
                        t,
                        g: 1,
                    };
                    if !run_cell(&cell, &a, &mut sink) {
                        eprintln!(
                            "-- {} m={m} {}: every run at t = {t} timed out; stopping",
                            kind.name(),
                            control.name()
                        );
                        break;
                    }
                }
            }
        }
    }
    // The generator-count ladder, on planted targets.
    for &kind in &a.kinds {
        for &t in &a.ladder_ts {
            for &g in &a.ladder_gs {
                let cell = Cell {
                    kind,
                    m: 2,
                    control: Control::Ladder,
                    t,
                    g,
                };
                run_cell(&cell, &a, &mut sink);
            }
        }
    }
    let rows = &sink.rows;
    let summary = json!({
        "p": a.p,
        "budget_seconds": a.budget,
        "seed": a.seed,
        "planted_per_cell": a.planted,
        "random_per_cell": a.random,
        "wall_seconds": started.elapsed().as_secs_f64(),
        "rows": rows.len(),
        "planted_violations": rows.iter().filter(|r| r["planted_ok"] == json!(false)).count(),
    });
    eprintln!("{summary}");
    if let Some(f) = sink.file.as_mut() {
        writeln!(f, "{}", json!({ "summary": summary })).expect("write --out");
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Independent backward quadratic solve: unlike the forward coset
    /// generator, this reconstructs all rational preimages of the terminal
    /// coordinate without any auxiliary-curve group additions.
    fn quadratic_fiber(tower: &Tower, p: u64) -> Vec<u64> {
        let field = PrimeCurve { p, a: 1, b: 0 };
        let half = invm(2, p);
        let mut fiber = vec![tower.c];
        for step in tower.steps.iter().rev() {
            let Step::Velu { xi, tau } = step else {
                panic!("quadratic_fiber needs a degree-2 isogeny chain");
            };
            let mut previous = Vec::new();
            for z in fiber {
                // z = x + tau/(x-xi): x²-(z+xi)x+z*xi+tau=0.
                let sum = addm(z, *xi, p);
                let product = addm(mulm(z, *xi, p), *tau, p);
                let discriminant = subm(mulm(sum, sum, p), mulm(4, product, p), p);
                if let Some(root) = field.sqrt(discriminant) {
                    for numerator in [addm(sum, root, p), subm(sum, root, p)] {
                        let x = mulm(numerator, half, p);
                        if x != *xi {
                            previous.push(x);
                        }
                    }
                }
            }
            previous.sort_unstable();
            previous.dedup();
            fiber = previous;
        }
        for x in &mut fiber {
            *x = mulm(*x, tower.scale, p);
        }
        fiber.sort_unstable();
        fiber
    }

    #[test]
    fn supersingular_membership_matches_exhaustive_small_fields() {
        for (p, max_t) in [(31, 3), (127, 5), (1019, 2)] {
            let aux = PrimeCurve { p, a: 1, b: 0 };
            assert_eq!(aux.point_count(), p + 1);
            for t in 1..=max_t {
                let mut rng = StdRng::seed_from_u64(p + t as u64);
                let tower = isogeny_with_auxiliary(p, t, &mut rng, true);
                tower.check(p);
                let mut expected = tower.v.clone();
                expected.sort_unstable();
                assert_eq!(quadratic_fiber(&tower, p), expected);
                let actual: Vec<_> = (0..p).filter(|&x| tower.contains(x, p)).collect();
                assert_eq!(actual, expected);
                // Clearing the first denominator must not admit its pole.
                let Step::Velu { xi, .. } = tower.steps[0] else {
                    unreachable!()
                };
                assert!(!tower.contains(xi, p));
            }
        }
    }

    #[test]
    fn m31_ten_level_membership_and_independent_target_relations() {
        let p = (1u64 << 31) - 1;
        let t = 10;
        let mut rng = StdRng::seed_from_u64(31);
        let tower = isogeny_with_auxiliary(p, t, &mut rng, true);
        tower.check(p);
        assert_eq!(tower.size, 1024);
        assert_eq!(tower.info["aux_order"], json!(p + 1));
        let mut expected = tower.v.clone();
        expected.sort_unstable();
        assert_eq!(quadratic_fiber(&tower, p), expected);
        assert!(tower.equations(t, 0, p).iter().all(|eq| eq.degree() == 2));

        // Different group orders certify these two curves are not F_p-isogenous.
        // No transfer from the auxiliary curve to this target is used.
        let curve = PrimeCurve { p, a: 1, b: 4 };
        assert_ne!(curve.point_count_fast(), p + 1);
        let on: Vec<_> = tower
            .v
            .iter()
            .copied()
            .filter(|&x| curve.legendre(curve.rhs(x)) == 1)
            .collect();
        assert!(on.len() >= 9);
        for m in 2..=9 {
            let target = loop {
                if let Some(target) = plant(&curve, &tower, m, &on, &mut rng) {
                    break target;
                }
            };
            let (eqs, n, solution, _) =
                system(Control::Tower, &tower, &curve, m, &target, 1, &mut rng);
            let solution = solution.unwrap();
            assert_eq!(n, m * t + m - 2);
            assert!(eqs.iter().all(|eq| eq.eval(&solution, p) == 0));
            assert!(target.xs.iter().all(|&x| tower.contains(x, p)));

            // Check an actual signed point relation, not merely Semaev=0.
            let points: Vec<_> = target
                .xs
                .iter()
                .map(|&x| PrimePoint::affine(x, curve.sqrt(curve.rhs(x)).unwrap()))
                .collect();
            let rhs = PrimePoint::affine(target.x_r, curve.sqrt(curve.rhs(target.x_r)).unwrap());
            let mut ops = GroupOps::default();
            assert!((0..1usize << m).any(|signs| {
                let total = points
                    .iter()
                    .enumerate()
                    .fold(PrimePoint::INFINITY, |acc, (i, pt)| {
                        let signed = if signs & (1 << i) == 0 {
                            *pt
                        } else {
                            PrimePoint::affine(pt.x, subm(0, pt.y, p))
                        };
                        curve.add(&mut ops, acc, signed)
                    });
                total == rhs
            }));
        }
    }

    #[test]
    fn auxiliary_chain_f4_solutions_match_target_point_relations() {
        let p = 127;
        let mut rng = StdRng::seed_from_u64(0x504b4d);
        let tower = isogeny_with_auxiliary(p, 2, &mut rng, true);
        tower.check(p);
        let (curve, on) = target_curve(p, &tower, 2, &mut rng);
        let target = loop {
            if let Some(target) = plant(&curve, &tower, 2, &on, &mut rng) {
                break target;
            }
        };
        let (eqs, n, _, _) = system(Control::Tower, &tower, &curve, 2, &target, 1, &mut rng);
        let input: Vec<_> = eqs.iter().map(|eq| eq.to_poly(p)).collect();
        let options = F4Options::new(Ordering::Grevlex, 12).with_budget(Duration::from_secs(10));
        let solved = f4_fp::solve(&input, n, p, &options);
        assert!(!solved.timed_out);
        let f4_fp::Verdict::Solutions(solutions) = solved.verdict else {
            panic!("planted auxiliary system did not produce solutions");
        };
        let mut actual = std::collections::BTreeSet::new();
        for solution in solutions {
            assert!(eqs.iter().all(|eq| eq.eval(&solution, p) == 0));
            assert!(tower.contains(solution[0], p));
            assert!(tower.contains(solution[tower.t], p));
            actual.insert((solution[0], solution[tower.t]));
        }
        // Expected decompositions come from signed point additions on E,
        // independently of both Semaev polynomials and the F4 solver.
        let mut expected = std::collections::BTreeSet::new();
        let mut ops = GroupOps::default();
        for &x in &tower.v {
            for &u in &tower.v {
                let (Some(y), Some(v)) = (curve.sqrt(curve.rhs(x)), curve.sqrt(curve.rhs(u)))
                else {
                    continue;
                };
                for sign_y in [y, subm(0, y, p)] {
                    for sign_v in [v, subm(0, v, p)] {
                        let sum = curve.add(
                            &mut ops,
                            PrimePoint::affine(x, sign_y),
                            PrimePoint::affine(u, sign_v),
                        );
                        if !sum.infinity && sum.x == target.x_r {
                            expected.insert((x, u));
                        }
                    }
                }
            }
        }
        assert!(!expected.is_empty());
        assert_eq!(actual, expected);
    }

    #[test]
    #[should_panic(expected = "non-2-torsion quotient coset")]
    fn supersingular_auxiliary_rejects_order_two_quotient() {
        let mut rng = StdRng::seed_from_u64(1);
        isogeny_with_auxiliary(127, 6, &mut rng, true);
    }

    #[test]
    #[should_panic(expected = "requires p = 3 mod 4")]
    fn supersingular_rejects_incompatible_field() {
        isogeny_with_auxiliary(61, 2, &mut StdRng::seed_from_u64(31), true);
    }

    #[test]
    #[should_panic(expected = "2^t must divide p+1")]
    fn supersingular_rejects_unavailable_torsion() {
        isogeny_with_auxiliary(1019, 3, &mut StdRng::seed_from_u64(31), true);
    }

    /// The worked example of the auxiliary-curves guide: over F_61,
    /// E': y² = x³ + x + 14, kernel abscissae 12 then 5, gives
    /// r₁(x) = x + 12/(x − 12) + 1/(x − 12)², r₂(u) = u + 32/(u − 5) + 13/(u − 5)²,
    /// and the fiber V = {5, 11, 15, 16, 17, 19, 25, 37, 58} over χ = 60.
    #[test]
    fn guide_f61_two_three_isogenies() {
        let p = 61;
        let (a, b) = (1u64, 14u64);
        let e1 = PrimeCurve { p, a, b };
        let x1 = 12u64;
        let v1 = addm(mulm(6, mulm(x1, x1, p), p), mulm(2, a, p), p);
        let u1 = mulm(4, e1.rhs(x1), p);
        assert_eq!((v1, u1), (12, 1));
        let a2 = subm(a, mulm(5, v1, p), p);
        let b2 = subm(b, mulm(7, addm(u1, mulm(x1, v1, p), p), p), p);
        let e2 = PrimeCurve { p, a: a2, b: b2 };
        let x2 = 5u64;
        let v2 = addm(mulm(6, mulm(x2, x2, p), p), mulm(2, a2, p), p);
        let u2 = mulm(4, e2.rhs(x2), p);
        assert_eq!((v2, u2), (32, 13));
        let tower = Tower {
            kind: Kind::Isogeny,
            t: 2,
            size: 9,
            v: vec![5, 11, 15, 16, 17, 19, 25, 37, 58],
            scale: 1,
            steps: vec![
                Step::VeluOdd {
                    pts: vec![(x1, v1, u1)],
                },
                Step::VeluOdd {
                    pts: vec![(x2, v2, u2)],
                },
            ],
            c: 60,
            info: Value::Null,
        };
        tower.check(p);
        assert_eq!(tower.values(5, p), vec![5, 17]);
        assert_eq!(tower.apply(1, 17, p), 60);
        // x = 2 is rejected: 2 → 49 → 25.
        assert_eq!(tower.values(2, p), vec![2, 49]);
        assert_eq!(tower.apply(1, 49, p), 25);
        // The membership polynomial Π_{x: chain(x) = 60} (x − ·) has exactly V as roots.
        let hits: Vec<u64> = (0..p)
            .filter(|&x| {
                x != 12 && {
                    let u = tower.apply(0, x, p);
                    u != 5 && tower.apply(1, u, p) == 60
                }
            })
            .collect();
        assert_eq!(hits, tower.v);
    }

    /// Generated towers of every degree mix check, at a 20-bit prime.
    #[test]
    fn bsgs_count_matches_exact() {
        let mut rng = StdRng::seed_from_u64(3);
        for (a, b) in [(1u64, 14u64), (2, 3), (5, 7), (0, 1), (100, 7)] {
            for p in [61u64, 1009, 786_433] {
                let e = PrimeCurve {
                    p,
                    a: a % p,
                    b: b % p,
                };
                if !nonsingular(e.a, e.b, p) {
                    continue;
                }
                assert_eq!(
                    point_count_bsgs(&e, &mut rng),
                    e.point_count(),
                    "p={p} a={a} b={b}"
                );
            }
        }
    }

    #[test]
    fn general_isogeny_towers_build() {
        let p = 786_433;
        for degrees in [vec![3u64], vec![5], vec![2, 3], vec![3, 2], vec![7]] {
            for t in 1..=3 {
                let mut rng = StdRng::seed_from_u64(7 + t as u64);
                let tower = build_tower(Kind::Isogeny, p, t, &degrees, &mut rng);
                assert_eq!(tower.size as u64, tower_size(Kind::Isogeny, t, &degrees));
                for (j, e) in tower.equations(t, 0, p).iter().enumerate() {
                    assert_eq!(e.degree() as u64, level_degrees(&degrees, t)[j]);
                }
            }
        }
    }
}
