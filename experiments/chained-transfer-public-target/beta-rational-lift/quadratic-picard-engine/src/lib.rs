//! Canonical `Pic^0` arithmetic on a smooth plane quartic over `F_q` (W1 of the
//! plane-quartic index-calculus program).
//!
//! Study: `research/quartic_pic_canonical_20261018/` (frozen `PROTOCOL.md`).
//!
//! # Representation
//!
//! `C : F(X,Y,Z) = 0` is a smooth plane quartic over `F_q` (`q` an odd prime,
//! `q < 2^31`), `K` its canonical class (the line section), `P0` a fixed
//! rational point and `D_inf = (tangent line at P0) - P0 ~ K - P0`. A class
//! `x` in `Pic^0(C)(F_q)` is stored through `x + D_inf in Pic^3`.
//!
//! By Riemann-Roch every degree-3 class has `h^0 = 1` (a unique effective
//! divisor `D`, not collinear) or `h^0 = 2` (the class is `K - P` for a unique
//! rational point `P`). Hence the canonical forms:
//!
//! * [`PicClass::Typ`]: the reduced row-echelon basis of the 3-dimensional
//!   space of conics through `D` (it determines `D`);
//! * [`PicClass::Exc`]: the normalised coordinates of `P`. The zero class is
//!   `Exc(P0)`.
//!
//! Divisors are never stored as point lists. An effective divisor is carried by
//! a *generating space* of forms in the coordinate ring `R = F_q[X,Y,Z]/(F)`
//! whose common zero scheme on `C` is exactly the divisor; residuals use the
//! ideal-quotient rule `e in I(R) iff e*v in (c) for all v in I(Z)`. Everything
//! is `F_q` linear algebra (no extension fields, no root finding).
//!
//! # Group law
//!
//! `add`: `Z6 = D_x + D_y`; the 4-dimensional space of cubics through `Z6`;
//! impose `P0` to get the 3-dimensional space `V` of cubics through
//! `E7 = Z6 + P0`. A conic through `E7` means `E7 ~ 2K - P`, so the sum is
//! `Exc(P)`. Otherwise, for a cubic `c in V` the unique conic `q'` through the
//! residual `R5 = div(c) - E7` satisfies `q' v = c g_v` for `v in V`, and the
//! `g_v` span the conics through the sum divisor `D_z` (`D_z + K ~ E7`).
//!
//! `neg`: the conic through `D_x + 2 P0` (a pencil gives `Exc(P)`), residual.
//!
//! # Cost accounting
//!
//! Every `F_q` multiplication and inversion is counted in [`FqCounter`]
//! (additions are counted but not priced). Fallbacks (generating spaces that
//! needed lifting to a higher degree, `P0` in the support of the sum, the
//! exceptional paths) are counted in [`PicStats`] and are never silent.

use std::cell::Cell;
use std::collections::HashMap;

/// A projective point of `P^2(F_q)`, normalised so that its first nonzero
/// coordinate is 1 (see [`PlaneQuartic::normalize_point`]).
pub type Pt = [u32; 3];

/// Maximum degree of the coordinate ring tables.
const MAXD: usize = 8;

/// Counters of `F_q` operations. `mul` and `inv` are priced; `add` is only
/// counted.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct FqCounter {
    pub mul: u64,
    pub inv: u64,
    pub add: u64,
}

impl FqCounter {
    /// Componentwise difference `self - earlier`.
    pub fn since(&self, earlier: &FqCounter) -> FqCounter {
        FqCounter {
            mul: self.mul - earlier.mul,
            inv: self.inv - earlier.inv,
            add: self.add - earlier.add,
        }
    }
}

/// Counters of the non-generic paths taken (never silent; the fraction of
/// operations that took each is reported by the study).
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct PicStats {
    /// Operations started (`add`, `neg`, `reduce_deg6`).
    pub ops: u64,
    /// Generating spaces lifted to a higher degree to become complete.
    pub lifts: u64,
    /// `P0` was in the support of the degree-6 divisor (general E7 path).
    pub p0_in_support: u64,
    /// A conic through `E7` existed (exceptional result of `add`).
    pub exc_results: u64,
    /// A pencil of conics through `D_x + 2 P0` (exceptional result of `neg`).
    pub neg_pencil: u64,
    /// An exceptional operand had to be expanded by a line section.
    pub exc_operands: u64,
    /// `F_q` operations spent normalising results into canonical form
    /// (the "key encoding" share of the totals).
    pub norm_mul: u64,
    pub norm_inv: u64,
}

/// Canonical class key. `key(x) == key(y)` iff `x == y` in `Pic^0`.
/// `[tag, data...]` with tag 0 = exceptional (`data[0..3]` = point), tag 1 =
/// typical (`data[0..18]` = the echelon matrix of conics, row-major).
#[derive(Clone, Debug, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub struct PicKey(pub [u32; 19]);

/// A class of `Pic^0(C)(F_q)` in canonical form.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub enum PicClass {
    /// `h^0 = 2`: the class `x` with `x + D_inf = K - P`; `P` normalised.
    Exc(Pt),
    /// `h^0 = 1`: reduced echelon basis of the conics through the unique
    /// effective degree-3 divisor in `x + D_inf`.
    Typ([[u32; 6]; 3]),
}

impl PicClass {
    /// The canonical key (a function of the class only).
    pub fn key(&self) -> PicKey {
        let mut k = [0u32; 19];
        match self {
            PicClass::Exc(p) => {
                k[1..4].copy_from_slice(p);
            }
            PicClass::Typ(m) => {
                k[0] = 1;
                for (i, row) in m.iter().enumerate() {
                    k[1 + 6 * i..7 + 6 * i].copy_from_slice(row);
                }
            }
        }
        PicKey(k)
    }
}

/// A generating space: forms of degree `k` (vectors in `R_k`) whose common zero
/// scheme on `C` is the divisor. Not necessarily complete.
#[derive(Clone, Debug)]
pub struct Gen {
    pub k: usize,
    pub rows: Vec<Vec<u32>>,
}

/// Errors from constructing a curve.
#[derive(Debug, PartialEq, Eq)]
pub enum PicError {
    /// `q` is not an odd prime below `2^31`.
    BadField,
    /// The smoothness certificate (`(F_X,F_Y,F_Z)_7 = S_7`) failed.
    NotSmooth,
    /// No rational point was found / supplied point not on the curve.
    NoPoint,
}

struct Fq {
    q: u64,
    quadratic_nu: Option<u32>,
    c_mul: Cell<u64>,
    c_inv: Cell<u64>,
    c_add: Cell<u64>,
}

impl Fq {
    #[inline]
    fn mul(&self, a: u32, b: u32) -> u32 {
        self.c_mul.set(self.c_mul.get() + 1);
        self.mulu(a, b)
    }
    #[inline]
    fn mulu(&self, a: u32, b: u32) -> u32 {
        if let Some(nu) = self.quadratic_nu {
            let p = self.q;
            let (a0, a1) = (a as u64 % p, a as u64 / p);
            let (b0, b1) = (b as u64 % p, b as u64 / p);
            assert!(a1 < p && b1 < p);
            let real = (a0 * b0 + nu as u64 * a1 * b1) % p;
            let imag = (a0 * b1 + a1 * b0) % p;
            return (real + p * imag) as u32;
        }
        ((a as u64 * b as u64) % self.q) as u32
    }
    fn add_nc(&self, a: u32, b: u32) -> u32 {
        if self.quadratic_nu.is_some() {
            let p = self.q;
            return (((a as u64 % p + b as u64 % p) % p) + p * ((a as u64 / p + b as u64 / p) % p))
                as u32;
        }
        let s = a as u64 + b as u64;
        (if s >= self.q { s - self.q } else { s }) as u32
    }
    #[inline]
    fn add(&self, a: u32, b: u32) -> u32 {
        self.c_add.set(self.c_add.get() + 1);
        self.add_nc(a, b)
    }
    #[inline]
    fn sub(&self, a: u32, b: u32) -> u32 {
        self.c_add.set(self.c_add.get() + 1);
        self.sub_nc(a, b)
    }
    #[inline]
    fn neg(&self, a: u32) -> u32 {
        if self.quadratic_nu.is_some() {
            return self.sub_nc(0, a);
        }
        if a == 0 {
            0
        } else {
            (self.q - a as u64) as u32
        }
    }
    fn invu(&self, a: u32) -> u32 {
        if let Some(nu) = self.quadratic_nu {
            let p = self.q;
            let (a0, a1) = (a as u64 % p, a as u64 / p);
            assert!(a1 < p);
            let norm = (a0 * a0 + p - (nu as u64 * a1 * a1) % p) % p;
            assert!(norm != 0, "quadratic field inversion of zero");
            let inv_norm = self.base_invu(norm as u32) as u64;
            return ((a0 * inv_norm) % p + p * ((p - a1) * inv_norm % p)) as u32;
        }
        self.base_invu(a)
    }
    fn base_invu(&self, a: u32) -> u32 {
        // extended Euclid on (q, a)
        let (mut r0, mut r1) = (self.q as i64, a as i64);
        let (mut t0, mut t1) = (0i64, 1i64);
        while r1 != 0 {
            let qt = r0 / r1;
            let r2 = r0 - qt * r1;
            r0 = r1;
            r1 = r2;
            let t2 = t0 - qt * t1;
            t0 = t1;
            t1 = t2;
        }
        debug_assert_eq!(r0, 1);
        (((t0 % self.q as i64) + self.q as i64) % self.q as i64) as u32
    }
    fn inv(&self, a: u32) -> u32 {
        assert!(a != 0, "inversion of zero");
        self.c_inv.set(self.c_inv.get() + 1);
        self.invu(a)
    }
    fn powu(&self, mut a: u32, mut e: u64) -> u32 {
        let mut r = 1u32;
        while e > 0 {
            if e & 1 == 1 {
                r = self.mulu(r, a);
            }
            a = self.mulu(a, a);
            e >>= 1;
        }
        r
    }
}

/// A subspace of `R_n` in reduced echelon form together with the quotient map
/// `R_n -> R_n / W` (unit vectors sent to quotient coordinates).
struct Quot {
    rows: Vec<Vec<u32>>,
    free_rank: Vec<Option<usize>>,
    /// For a pivot position `p` (row index `r`): coordinates of `e_p` mod `W`.
    red: Vec<Vec<u32>>,
    qdim: usize,
}

/// Monomials of degree `n` in the fixed order (`a` descending, then `b`).
pub fn mons_of_degree(n: usize) -> Vec<(u8, u8, u8)> {
    let mut v = Vec::new();
    for a in (0..=n).rev() {
        for b in (0..=n - a).rev() {
            v.push((a as u8, b as u8, (n - a - b) as u8));
        }
    }
    v
}

/// A smooth plane quartic with `Pic^0` arithmetic.
pub struct PlaneQuartic {
    fq: Fq,
    q: u32,
    /// Coefficients of `F` in the order of `mons_of_degree(4)`.
    f: [u32; 15],
    mons: Vec<Vec<(u8, u8, u8)>>,
    dim: Vec<usize>,
    std_mon: Vec<Vec<usize>>,
    nf: Vec<Vec<Vec<(usize, u32)>>>,
    prod: Vec<Vec<Vec<usize>>>,
    p0: Pt,
    p0_vals: Vec<Vec<u32>>,
    lines_p0: Gen,
    cons2p0: Gen,
    stats: Cell<PicStats>,
    setup_cost: FqCounter,
}

/// Is the quartic `f` smooth over `\bar F_q`? Certificate: the partials
/// `F_X,F_Y,F_Z` (a regular sequence iff smooth, `q` odd) satisfy
/// `(F_X,F_Y,F_Z)_7 = S_7`, since `S/(F_X,F_Y,F_Z)` has Hilbert series
/// `(1+t+t^2)^3` (top degree 6) when smooth and never vanishes in a degree when
/// the partials have a common zero.
pub fn smoothness_certificate(q: u32, f: &[u32; 15]) -> bool {
    let fq = Fq {
        q: q as u64,
        quadratic_nu: None,
        c_mul: Cell::new(0),
        c_inv: Cell::new(0),
        c_add: Cell::new(0),
    };
    let m4 = mons_of_degree(4);
    let m3 = mons_of_degree(3);
    let m7 = mons_of_degree(7);
    let m7i: HashMap<(u8, u8), usize> = m7
        .iter()
        .enumerate()
        .map(|(i, m)| ((m.0, m.1), i))
        .collect();
    let m3i: HashMap<(u8, u8), usize> = m3
        .iter()
        .enumerate()
        .map(|(i, m)| ((m.0, m.1), i))
        .collect();
    // partials
    let mut part = vec![vec![0u32; 10]; 3];
    for (i, &(a, b, c)) in m4.iter().enumerate() {
        let co = f[i];
        if co == 0 {
            continue;
        }
        if a > 0 {
            let v = fq.mulu(co, a as u32);
            part[0][m3i[&(a - 1, b)]] = v;
        }
        if b > 0 {
            let v = fq.mulu(co, b as u32);
            part[1][m3i[&(a, b - 1)]] = v;
        }
        if c > 0 {
            let v = fq.mulu(co, c as u32);
            part[2][m3i[&(a, b)]] = v;
        }
    }
    let mut rows: Vec<Vec<u32>> = Vec::new();
    for p in &part {
        for &(a2, b2, _c2) in &m4 {
            let mut r = vec![0u32; 36];
            for (j, &(a, b, _)) in m3.iter().enumerate() {
                if p[j] != 0 {
                    let idx = m7i[&(a + a2, b + b2)];
                    r[idx] = p[j];
                }
            }
            rows.push(r);
        }
    }
    let rank = rank_mod(&fq, rows, 36);
    rank == 36
}

fn rank_mod(fq: &Fq, mut rows: Vec<Vec<u32>>, ncols: usize) -> usize {
    let mut r = 0;
    for col in 0..ncols {
        let Some(p) = (r..rows.len()).find(|&i| rows[i][col] != 0) else {
            continue;
        };
        rows.swap(r, p);
        let iv = fq.invu(rows[r][col]);
        for c in col..ncols {
            rows[r][c] = fq.mulu(rows[r][c], iv);
        }
        let prow = rows[r].clone();
        for i in r + 1..rows.len() {
            let fct = rows[i][col];
            if fct != 0 {
                for c in col..ncols {
                    let t = fq.mulu(fct, prow[c]);
                    rows[i][c] = fq.sub_nc(rows[i][c], t);
                }
            }
        }
        r += 1;
        if r == rows.len() {
            break;
        }
    }
    r
}

impl Fq {
    fn sub_nc(&self, a: u32, b: u32) -> u32 {
        if self.quadratic_nu.is_some() {
            let p = self.q;
            return (((a as u64 % p + p - b as u64 % p) % p)
                + p * ((a as u64 / p + p - b as u64 / p) % p)) as u32;
        }
        if a >= b {
            a - b
        } else {
            (a as u64 + self.q - b as u64) as u32
        }
    }
}

/// Is `q` an odd prime below `2^31`?
pub fn is_odd_prime_below_2_31(q: u64) -> bool {
    if !(3..(1u64 << 31)).contains(&q) || q.is_multiple_of(2) {
        return false;
    }
    let mut d = 3u64;
    while d * d <= q {
        if q.is_multiple_of(d) {
            return false;
        }
        d += 2;
    }
    true
}

impl PlaneQuartic {
    /// Build the arithmetic for `F = sum f[i] * mons_of_degree(4)[i]` with the
    /// rational point `p0` as the base point. Fails unless `q` is an odd prime
    /// `< 2^31`, the smoothness certificate passes and `p0` lies on `C`.
    pub fn new(q: u32, f: [u32; 15], p0: Pt) -> Result<PlaneQuartic, PicError> {
        if !is_odd_prime_below_2_31(q as u64) {
            return Err(PicError::BadField);
        }
        if f.iter().any(|&c| c >= q) {
            return Err(PicError::BadField);
        }
        if !smoothness_certificate(q, &f) {
            return Err(PicError::NotSmooth);
        }
        let fq = Fq {
            q: q as u64,
            quadratic_nu: None,
            c_mul: Cell::new(0),
            c_inv: Cell::new(0),
            c_add: Cell::new(0),
        };
        // monomial tables
        let mons: Vec<Vec<(u8, u8, u8)>> = (0..=MAXD).map(mons_of_degree).collect();
        let midx: Vec<Vec<usize>> = (0..=MAXD)
            .map(|n| {
                let mut t = vec![usize::MAX; (n + 1) * (n + 1)];
                for (i, m) in mons[n].iter().enumerate() {
                    t[m.0 as usize * (n + 1) + m.1 as usize] = i;
                }
                t
            })
            .collect();
        let m4 = &mons[4];
        let lead_i = (0..15).find(|&i| f[i] != 0).ok_or(PicError::NotSmooth)?;
        let lead = m4[lead_i];
        let lcoef = f[lead_i];
        let ilc = fq.invu(lcoef);
        let mut dim = vec![0usize; MAXD + 1];
        let mut std_mon: Vec<Vec<usize>> = vec![vec![]; MAXD + 1];
        let mut nf: Vec<Vec<Vec<(usize, u32)>>> = vec![vec![]; MAXD + 1];
        for n in 0..=MAXD {
            let ms = &mons[n];
            let is_std =
                |m: &(u8, u8, u8)| !(n >= 4 && m.0 >= lead.0 && m.1 >= lead.1 && m.2 >= lead.2);
            let mut pos = vec![usize::MAX; ms.len()];
            for (i, m) in ms.iter().enumerate() {
                if is_std(m) {
                    pos[i] = std_mon[n].len();
                    std_mon[n].push(i);
                }
            }
            dim[n] = std_mon[n].len();
            let mut tab: Vec<Vec<(usize, u32)>> = vec![vec![]; ms.len()];
            for i in (0..ms.len()).rev() {
                let m = ms[i];
                if is_std(&m) {
                    tab[i] = vec![(pos[i], 1)];
                } else {
                    let t = (m.0 - lead.0, m.1 - lead.1, m.2 - lead.2);
                    let mut acc = vec![0u32; dim[n]];
                    for (fi, &fm) in m4.iter().enumerate() {
                        if fi == lead_i || f[fi] == 0 {
                            continue;
                        }
                        let mm = (fm.0 + t.0, fm.1 + t.1);
                        let mi = midx[n][mm.0 as usize * (n + 1) + mm.1 as usize];
                        let coef = fq.mulu(fq.neg(f[fi]), ilc);
                        for &(p, cf) in &tab[mi] {
                            let add = fq.mulu(coef, cf);
                            acc[p] = fq.sub_nc(acc[p], fq.neg(add));
                        }
                    }
                    tab[i] = acc
                        .iter()
                        .enumerate()
                        .filter(|(_, &c)| c != 0)
                        .map(|(p, &c)| (p, c))
                        .collect();
                }
            }
            nf[n] = tab;
        }
        // product index tables prod[i][j][x*dim[j]+y] = monomial index in S_{i+j}
        let mut prod: Vec<Vec<Vec<usize>>> = vec![vec![vec![]; MAXD + 1]; MAXD + 1];
        for i in 0..=MAXD {
            for j in 0..=MAXD - i {
                let n = i + j;
                let mut t = Vec::with_capacity(dim[i] * dim[j]);
                for &xi in &std_mon[i] {
                    let a = mons[i][xi];
                    for &yj in &std_mon[j] {
                        let b = mons[j][yj];
                        t.push(midx[n][(a.0 + b.0) as usize * (n + 1) + (b.1 + a.1) as usize]);
                    }
                }
                prod[i][j] = t;
            }
        }
        let mut s = PlaneQuartic {
            fq,
            q,
            f,
            mons,
            dim,
            std_mon,
            nf,
            prod,
            p0: [0; 3],
            p0_vals: vec![],
            lines_p0: Gen { k: 1, rows: vec![] },
            cons2p0: Gen { k: 2, rows: vec![] },
            stats: Cell::new(PicStats::default()),
            setup_cost: FqCounter::default(),
        };
        let p0 = s.normalize_point(p0);
        if p0 == [0, 0, 0] || s.eval_f(p0) != 0 {
            return Err(PicError::NoPoint);
        }
        s.p0 = p0;
        s.setup_base_point();
        Ok(s)
    }

    /// Scalar extension of a validated prime curve. Encodings are a+p*b in
    /// F_p[v]/(v^2-nu), never integers modulo p^2. The base curve, P0 and
    /// prime normal-form caches stay fixed; all caches have coefficients in F_p.
    pub fn base_change_quadratic(p: u32, nu: u32, f: [u32; 15], p0: Pt) -> Result<Self, PicError> {
        if ![5, 7, 11, 223].contains(&p) || nu == 0 || nu >= p || p0.iter().any(|&x| x >= p) {
            return Err(PicError::BadField);
        }
        let mut out = Self::new(p, f, p0)?;
        if out.fq.powu(nu, (p as u64 - 1) / 2) != p - 1 {
            return Err(PicError::BadField);
        }
        let cached = (
            out.p0_vals.clone(),
            out.lines_p0.rows.clone(),
            out.cons2p0.rows.clone(),
        );
        out.fq.quadratic_nu = Some(nu);
        out.q = p * p;
        out.setup_base_point();
        assert_eq!(
            cached,
            (
                out.p0_vals.clone(),
                out.lines_p0.rows.clone(),
                out.cons2p0.rows.clone()
            ),
            "actual scalar-extension base-point caches must be identical"
        );
        Ok(out)
    }
    pub fn coefficient_add(&self, a: u32, b: u32) -> u32 {
        self.fq.add_nc(a, b)
    }
    pub fn coefficient_sub(&self, a: u32, b: u32) -> u32 {
        self.fq.sub_nc(a, b)
    }
    pub fn coefficient_mul(&self, a: u32, b: u32) -> u32 {
        self.fq.mulu(a, b)
    }
    pub fn coefficient_inv(&self, a: u32) -> u32 {
        self.fq.invu(a)
    }
    pub fn coefficient_frobenius(&self, a: u32) -> u32 {
        if self.fq.quadratic_nu.is_none() {
            return a;
        }
        let p = self.fq.q as u32;
        a % p + p * ((p - a / p) % p)
    }
    /// Frobenius preserves normalized pivots, hence the canonical class form.
    pub fn frobenius_class(&self, x: &PicClass) -> PicClass {
        match x {
            PicClass::Exc(p) => PicClass::Exc(p.map(|a| self.coefficient_frobenius(a))),
            PicClass::Typ(m) => {
                PicClass::Typ(m.map(|row| row.map(|a| self.coefficient_frobenius(a))))
            }
        }
    }

    /// Order of the base field.
    pub fn q(&self) -> u32 {
        self.q
    }
    /// The quartic's coefficients in the order of `mons_of_degree(4)`.
    pub fn coefficients(&self) -> &[u32; 15] {
        &self.f
    }
    /// The fixed rational base point `P0`.
    pub fn base_point(&self) -> Pt {
        self.p0
    }
    /// Snapshot of the `F_q` operation counters.
    pub fn counter(&self) -> FqCounter {
        FqCounter {
            mul: self.fq.c_mul.get(),
            inv: self.fq.c_inv.get(),
            add: self.fq.c_add.get(),
        }
    }
    /// Reset the counters and the path statistics.
    pub fn reset_counter(&self) {
        self.fq.c_mul.set(0);
        self.fq.c_inv.set(0);
        self.fq.c_add.set(0);
        self.stats.set(PicStats::default());
    }
    /// Snapshot of the path statistics.
    pub fn stats(&self) -> PicStats {
        self.stats.get()
    }
    /// Cost of the one-time base-point setup (not charged to operations).
    pub fn setup_cost(&self) -> FqCounter {
        self.setup_cost
    }

    fn bump<F: FnOnce(&mut PicStats)>(&self, f: F) {
        let mut s = self.stats.get();
        f(&mut s);
        self.stats.set(s);
    }

    /// Scale a projective point so that its first nonzero coordinate is 1.
    pub fn normalize_point(&self, p: Pt) -> Pt {
        let Some(i) = (0..3).find(|&i| p[i] != 0) else {
            return [0, 0, 0];
        };
        let iv = self.fq.invu(p[i]);
        [
            self.fq.mulu(p[0], iv),
            self.fq.mulu(p[1], iv),
            self.fq.mulu(p[2], iv),
        ]
    }

    /// `F(p)` (uncounted helper).
    pub fn eval_f(&self, p: Pt) -> u32 {
        let mut s = 0u32;
        for (i, &(a, b, c)) in self.mons[4].iter().enumerate() {
            if self.f[i] == 0 {
                continue;
            }
            let t = self.fq.mulu(
                self.fq
                    .mulu(self.fq.powu(p[0], a as u64), self.fq.powu(p[1], b as u64)),
                self.fq.powu(p[2], c as u64),
            );
            s = self.fq.add_nc(s, self.fq.mulu(t, self.f[i]));
        }
        s
    }

    /// Dimension of `R_n = S_n / F S_{n-4}`.
    pub fn dim_r(&self, n: usize) -> usize {
        self.dim[n]
    }

    /// Value of the standard monomials of `R_n` at `p` (uncounted).
    pub fn std_values(&self, n: usize, p: Pt) -> Vec<u32> {
        self.std_mon[n]
            .iter()
            .map(|&mi| {
                let (a, b, c) = self.mons[n][mi];
                self.fq.mulu(
                    self.fq
                        .mulu(self.fq.powu(p[0], a as u64), self.fq.powu(p[1], b as u64)),
                    self.fq.powu(p[2], c as u64),
                )
            })
            .collect()
    }

    /// Standard monomials of `R_n`.
    pub fn std_monomials(&self, n: usize) -> Vec<(u8, u8, u8)> {
        self.std_mon[n].iter().map(|&i| self.mons[n][i]).collect()
    }

    // ---------------------------------------------------------------------
    // linear algebra over F_q (counted)
    // ---------------------------------------------------------------------

    fn rref(&self, rows: &mut Vec<Vec<u32>>, ncols: usize) -> Vec<usize> {
        let mut piv = Vec::new();
        let mut r = 0;
        for col in 0..ncols {
            if r == rows.len() {
                break;
            }
            let Some(p) = (r..rows.len()).find(|&i| rows[i][col] != 0) else {
                continue;
            };
            rows.swap(r, p);
            if rows[r][col] != 1 {
                let iv = self.fq.inv(rows[r][col]);
                rows[r][col] = 1;
                for c in col + 1..ncols {
                    if rows[r][c] != 0 {
                        rows[r][c] = self.fq.mul(rows[r][c], iv);
                    }
                }
            }
            let prow = rows[r].clone();
            for i in 0..rows.len() {
                if i == r {
                    continue;
                }
                let fct = rows[i][col];
                if fct == 0 {
                    continue;
                }
                rows[i][col] = 0;
                for c in col + 1..ncols {
                    if prow[c] != 0 {
                        let t = self.fq.mul(fct, prow[c]);
                        rows[i][c] = self.fq.sub(rows[i][c], t);
                    }
                }
            }
            piv.push(col);
            r += 1;
        }
        rows.truncate(r);
        piv
    }

    /// Basis of `{x : A x = 0}` for the equation rows `eqs` (each of length `n`).
    fn nullspace(&self, mut eqs: Vec<Vec<u32>>, n: usize) -> Vec<Vec<u32>> {
        let piv = self.rref(&mut eqs, n);
        let mut is_piv = vec![false; n];
        for &p in &piv {
            is_piv[p] = true;
        }
        let mut out = Vec::new();
        for f in 0..n {
            if is_piv[f] {
                continue;
            }
            let mut x = vec![0u32; n];
            x[f] = 1;
            for (r, &p) in piv.iter().enumerate() {
                x[p] = self.fq.neg(eqs[r][f]);
            }
            out.push(x);
        }
        out
    }

    /// Access to the existing counted linear kernel for divisor adapters.
    pub fn linear_kernel(&self, eqs: Vec<Vec<u32>>, n: usize) -> Vec<Vec<u32>> {
        assert!(eqs.iter().all(|row| row.len() == n));
        assert!(eqs.iter().flatten().all(|&c| c < self.q));
        self.nullspace(eqs, n)
    }

    /// Complete a degree-six divisor's generating space and extract its cubics.
    /// The original completeness and rank requirements apply unchanged.
    pub fn cubic_space_deg6(&self, z6: &Gen) -> Vec<Vec<u32>> {
        let (k, w) = self.complete(z6.clone(), 6);
        self.forms_through(&w, k, 3)
    }

    fn quot_from(&self, mut rows: Vec<Vec<u32>>, n: usize) -> Quot {
        let piv = self.rref(&mut rows, n);
        let mut free_rank = vec![None; n];
        let mut free = Vec::new();
        let mut is_piv = vec![false; n];
        for &p in &piv {
            is_piv[p] = true;
        }
        for i in 0..n {
            if !is_piv[i] {
                free_rank[i] = Some(free.len());
                free.push(i);
            }
        }
        let mut red = vec![vec![]; n];
        for (r, &p) in piv.iter().enumerate() {
            red[p] = free.iter().map(|&f| self.fq.neg(rows[r][f])).collect();
        }
        Quot {
            rows,
            free_rank,
            red,
            qdim: free.len(),
        }
    }

    fn quot_apply(&self, qt: &Quot, v: &[u32]) -> Vec<u32> {
        let mut out = vec![0u32; qt.qdim];
        for (i, &vi) in v.iter().enumerate() {
            if vi == 0 {
                continue;
            }
            if let Some(k) = qt.free_rank[i] {
                out[k] = self.fq.add(out[k], vi);
            } else {
                for (k, &rk) in qt.red[i].iter().enumerate() {
                    if rk != 0 {
                        let t = self.fq.mul(vi, rk);
                        out[k] = self.fq.add(out[k], t);
                    }
                }
            }
        }
        out
    }

    fn quot_apply_sparse(&self, qt: &Quot, v: &[(usize, u32)]) -> Vec<u32> {
        let mut out = vec![0u32; qt.qdim];
        for &(i, vi) in v {
            if let Some(k) = qt.free_rank[i] {
                out[k] = if vi == 1 {
                    self.fq.add(out[k], 1)
                } else {
                    self.fq.add(out[k], vi)
                };
            } else {
                for (k, &rk) in qt.red[i].iter().enumerate() {
                    if rk != 0 {
                        let t = if vi == 1 { rk } else { self.fq.mul(vi, rk) };
                        out[k] = self.fq.add(out[k], t);
                    }
                }
            }
        }
        out
    }

    /// Product in the coordinate ring: `a in R_i`, `b in R_j` gives `R_{i+j}`.
    pub fn mul_forms(&self, i: usize, a: &[u32], j: usize, b: &[u32]) -> Vec<u32> {
        let n = i + j;
        let mut res = vec![0u32; self.dim[n]];
        let pt = &self.prod[i][j];
        let dj = self.dim[j];
        for (x, &ax) in a.iter().enumerate() {
            if ax == 0 {
                continue;
            }
            for (y, &by) in b.iter().enumerate() {
                if by == 0 {
                    continue;
                }
                let t = if ax == 1 {
                    by
                } else if by == 1 {
                    ax
                } else {
                    self.fq.mul(ax, by)
                };
                for &(pos, cf) in &self.nf[n][pt[x * dj + y]] {
                    let u = if cf == 1 { t } else { self.fq.mul(t, cf) };
                    res[pos] = self.fq.add(res[pos], u);
                }
            }
        }
        res
    }

    fn unit(&self, n: usize, i: usize) -> Vec<u32> {
        let mut v = vec![0u32; self.dim[n]];
        v[i] = 1;
        v
    }

    /// `e in R_m` with `e * x in W` for every `x in R_{k-m}`, where `W` is a
    /// complete space of degree-`k` forms through a divisor `Z` (all of
    /// `H^0(kK - Z)`, with `deg(kK-Z) >= 6`). Equivalent to `div(e) >= Z`.
    fn forms_through(&self, w: &Quot, k: usize, m: usize) -> Vec<Vec<u32>> {
        let t = k - m;
        let nm = self.dim[m];
        let nt = self.dim[t];
        let qd = w.qdim;
        let pt = &self.prod[m][t];
        let mut eqs = vec![vec![0u32; nm]; nt * qd];
        for j in 0..nm {
            for s in 0..nt {
                let img = self.quot_apply_sparse(w, &self.nf[k][pt[j * nt + s]]);
                for (r, &v) in img.iter().enumerate() {
                    eqs[s * qd + r][j] = v;
                }
            }
        }
        self.nullspace(eqs, nm)
    }

    /// `e in R_m` with `e * v in c * R_{m+vk-cn}` for every `v` in `vs`
    /// (`vs` generate the ideal of `Z`): `div(e) >= div(c) - Z`.
    fn colon(&self, c: &[u32], cn: usize, vs: &[Vec<u32>], vk: usize, m: usize) -> Vec<Vec<u32>> {
        let n = m + vk;
        let t = n - cn;
        let crows: Vec<Vec<u32>> = (0..self.dim[t])
            .map(|i| self.mul_forms(cn, c, t, &self.unit(t, i)))
            .collect();
        let qt = self.quot_from(crows, self.dim[n]);
        assert_eq!(
            qt.rows.len(),
            self.dim[t],
            "multiplication by c not injective"
        );
        let nm = self.dim[m];
        let qd = qt.qdim;
        let mut eqs = vec![vec![0u32; nm]; vs.len() * qd];
        for j in 0..nm {
            let uj = self.unit(m, j);
            for (s, v) in vs.iter().enumerate() {
                let prod = self.mul_forms(m, &uj, vk, v);
                let img = self.quot_apply(&qt, &prod);
                for (r, &val) in img.iter().enumerate() {
                    eqs[s * qd + r][j] = val;
                }
            }
        }
        self.nullspace(eqs, nm)
    }

    /// Solve `sum_j x_j cols[j] = rhs[s]` for each `s`; `None` unless unique.
    fn solve_multi(&self, cols: &[Vec<u32>], rhs: &[Vec<u32>]) -> Option<Vec<Vec<u32>>> {
        let u = cols.len();
        let nr = cols[0].len();
        let width = u + rhs.len();
        let mut rows = vec![vec![0u32; width]; nr];
        for r in 0..nr {
            for (j, c) in cols.iter().enumerate() {
                rows[r][j] = c[r];
            }
            for (s, b) in rhs.iter().enumerate() {
                rows[r][u + s] = b[r];
            }
        }
        let piv = self.rref(&mut rows, width);
        if piv.iter().any(|&p| p >= u) || piv.len() != u {
            return None;
        }
        let mut out = vec![vec![0u32; u]; rhs.len()];
        for (r, &p) in piv.iter().enumerate() {
            for s in 0..rhs.len() {
                out[s][p] = rows[r][u + s];
            }
        }
        Some(out)
    }

    // ---------------------------------------------------------------------
    // generating spaces
    // ---------------------------------------------------------------------

    /// Product of two generating spaces (generates the ideal of `Z_a + Z_b`).
    pub fn gen_mul(&self, a: &Gen, b: &Gen) -> Gen {
        let k = a.k + b.k;
        let mut rows = Vec::with_capacity(a.rows.len() * b.rows.len());
        for x in &a.rows {
            for y in &b.rows {
                rows.push(self.mul_forms(a.k, x, b.k, y));
            }
        }
        let n = self.dim[k];
        self.rref(&mut rows, n);
        Gen { k, rows }
    }

    /// Lift a generating space of a divisor of degree `dz` to the lowest
    /// degree `k` where it spans all of `H^0(kK - Z)` (and that system is base
    /// point free: `4k - dz >= 6`). Returns the degree and the quotient data.
    fn complete(&self, g: Gen, dz: usize) -> (usize, Quot) {
        let mut g = g;
        let mut first = true;
        loop {
            let k = g.k;
            let expect = self.dim[k] as isize - dz as isize;
            let n = self.dim[k];
            let mut rows = g.rows.clone();
            let r = self.rref(&mut rows, n).len();
            if 4 * k as isize - dz as isize >= 6 && r as isize == expect {
                return (k, self.quot_from(rows, n));
            }
            assert!(
                (r as isize) <= expect.max(0),
                "generating space too large: rank {} > {} at degree {} for deg-{} divisor",
                r,
                expect,
                k,
                dz
            );
            assert!(
                k + 1 < MAXD,
                "generating space did not complete by degree {}",
                MAXD - 1
            );
            if first {
                self.bump(|s| s.lifts += 1);
                first = false;
            }
            let r1 = Gen {
                k: 1,
                rows: (0..3).map(|i| self.unit(1, i)).collect(),
            };
            g = self.gen_mul(&Gen { k, rows }, &r1);
        }
    }

    fn eval_p0(&self, n: usize, v: &[u32]) -> u32 {
        let mut s = 0u32;
        for (i, &vi) in v.iter().enumerate() {
            if vi != 0 {
                let t = self.fq.mul(vi, self.p0_vals[n][i]);
                s = self.fq.add(s, t);
            }
        }
        s
    }

    fn setup_base_point(&mut self) {
        let p0 = self.p0;
        self.p0_vals = (0..=MAXD).map(|n| self.std_values(n, p0)).collect();
        // lines through P0
        let eq = vec![self.p0_vals[1].clone()];
        let ls = self.nullspace(eq, 3);
        assert_eq!(ls.len(), 2);
        self.lines_p0 = Gen { k: 1, rows: ls };
        // gradient of F at P0
        let mut grad = [0u32; 3];
        for (i, &(a, b, c)) in self.mons[4].iter().enumerate() {
            let co = self.f[i];
            if co == 0 {
                continue;
            }
            let pw = |e: u8, x: u32| self.fq.powu(x, e as u64);
            if a > 0 {
                let t = self.fq.mulu(
                    self.fq.mulu(co, a as u32),
                    self.fq
                        .mulu(self.fq.mulu(pw(a - 1, p0[0]), pw(b, p0[1])), pw(c, p0[2])),
                );
                grad[0] = self.fq.add_nc(grad[0], t);
            }
            if b > 0 {
                let t = self.fq.mulu(
                    self.fq.mulu(co, b as u32),
                    self.fq
                        .mulu(self.fq.mulu(pw(a, p0[0]), pw(b - 1, p0[1])), pw(c, p0[2])),
                );
                grad[1] = self.fq.add_nc(grad[1], t);
            }
            if c > 0 {
                let t = self.fq.mulu(
                    self.fq.mulu(co, c as u32),
                    self.fq
                        .mulu(self.fq.mulu(pw(a, p0[0]), pw(b, p0[1])), pw(c - 1, p0[2])),
                );
                grad[2] = self.fq.add_nc(grad[2], t);
            }
        }
        assert!(grad != [0, 0, 0], "singular base point");
        // tangent vector tau: grad . tau = 0, tau not proportional to P0
        let tau = {
            let ns = self.nullspace(vec![grad.to_vec()], 3);
            let mut pick = None;
            for v in &ns {
                let n = self.normalize_point([v[0], v[1], v[2]]);
                if n != p0 {
                    pick = Some([v[0], v[1], v[2]]);
                    break;
                }
            }
            pick.expect("tangent direction")
        };
        // conics e with e(P0)=0 and grad e(P0) . tau = 0
        let m2 = &self.mons[2];
        let mut r1 = vec![0u32; 6];
        let mut r2 = vec![0u32; 6];
        for (i, &(a, b, c)) in m2.iter().enumerate() {
            r1[i] = self.p0_vals[2][i];
            let pw = |e: u8, x: u32| self.fq.powu(x, e as u64);
            let mut d = 0u32;
            let parts = [(a, 0usize), (b, 1), (c, 2)];
            for &(e, v) in &parts {
                if e == 0 {
                    continue;
                }
                let ex = [a, b, c];
                let mut t = self.fq.mulu(e as u32, 1);
                for w in 0..3 {
                    let ee = if w == v { ex[w] - 1 } else { ex[w] };
                    t = self.fq.mulu(t, pw(ee, p0[w]));
                }
                t = self.fq.mulu(t, tau[v]);
                d = self.fq.add_nc(d, t);
            }
            r2[i] = d;
        }
        let ns = self.nullspace(vec![r1, r2], 6);
        assert_eq!(ns.len(), 4);
        self.cons2p0 = Gen { k: 2, rows: ns };
        self.setup_cost = self.counter();
        self.fq.c_mul.set(0);
        self.fq.c_inv.set(0);
        self.fq.c_add.set(0);
    }

    // ---------------------------------------------------------------------
    // classes
    // ---------------------------------------------------------------------

    /// The zero class `Exc(P0)`.
    pub fn zero(&self) -> PicClass {
        PicClass::Exc(self.p0)
    }

    /// Is `x` the zero class?
    pub fn is_zero(&self, x: &PicClass) -> bool {
        matches!(x, PicClass::Exc(p) if *p == self.p0)
    }

    /// The exceptional class `K - P - D_inf = [P0 - P]`.
    pub fn exceptional(&self, p: Pt) -> PicClass {
        PicClass::Exc(self.normalize_point(p))
    }

    /// The class of the point difference `[P - P0] = -Exc(P)`.
    pub fn point_class(&self, p: Pt) -> PicClass {
        self.neg(&self.exceptional(p))
    }

    /// Canonical class from three independent conics through a non-collinear
    /// effective degree-3 divisor.
    pub fn class_from_conics(&self, rows: Vec<Vec<u32>>) -> PicClass {
        let c0 = self.counter();
        let mut r = rows;
        let n = self.dim[2];
        let piv = self.rref(&mut r, n);
        assert_eq!(
            piv.len(),
            3,
            "conic space of a degree-3 divisor must have dimension 3"
        );
        let mut m = [[0u32; 6]; 3];
        for i in 0..3 {
            m[i].copy_from_slice(&r[i]);
        }
        let c1 = self.counter().since(&c0);
        self.bump(|s| {
            s.norm_mul += c1.mul;
            s.norm_inv += c1.inv;
        });
        PicClass::Typ(m)
    }

    /// Generating space of an effective degree-3 divisor in the class
    /// `x + D_inf`. `variant` picks the line section used for an exceptional
    /// class (any value gives a valid representative).
    pub fn gen_of_with(&self, x: &PicClass, variant: u32) -> Gen {
        match x {
            PicClass::Typ(m) => Gen {
                k: 2,
                rows: m.iter().map(|r| r.to_vec()).collect(),
            },
            PicClass::Exc(p) => {
                self.bump(|s| s.exc_operands += 1);
                let vals = self.std_values(1, *p);
                let ls = self.nullspace(vec![vals], 3);
                // l = l0 + variant * l1
                let mut l = ls[0].clone();
                if variant != 0 {
                    for i in 0..3 {
                        let t = self.fq.mul(variant, ls[1][i]);
                        l[i] = self.fq.add(l[i], t);
                    }
                }
                let cubics = self.colon(&l, 1, &ls, 1, 3);
                debug_assert_eq!(cubics.len(), self.dim[3] - 3);
                let mut rows = cubics;
                let n = self.dim[3];
                self.rref(&mut rows, n);
                assert_eq!(rows.len(), 7, "cubics through a line residual");
                Gen { k: 3, rows }
            }
        }
    }

    /// [`gen_of_with`](Self::gen_of_with) with the default line section.
    pub fn gen_of(&self, x: &PicClass) -> Gen {
        self.gen_of_with(x, 0)
    }

    /// Group addition.
    pub fn add(&self, x: &PicClass, y: &PicClass) -> PicClass {
        self.add_with(x, y, 0, 0)
    }

    /// Group addition with explicit line-section variants for exceptional
    /// operands (results do not depend on them).
    pub fn add_with(&self, x: &PicClass, y: &PicClass, vx: u32, vy: u32) -> PicClass {
        if self.is_zero(x) {
            return y.clone();
        }
        if self.is_zero(y) {
            return x.clone();
        }
        let gx = self.gen_of_with(x, vx);
        let z6 = if x == y && vx == vy && gx.k == 2 {
            // doubling: the 6 products q_i q_j of a conic space span only a
            // 6-dimensional space of quartics (8 are needed), so go straight
            // to degree 5 (designed path, not counted as a lift)
            let g2 = self.gen_mul(&gx, &gx);
            let r1 = Gen {
                k: 1,
                rows: (0..3).map(|i| self.unit(1, i)).collect(),
            };
            self.gen_mul(&g2, &r1)
        } else {
            let gy = self.gen_of_with(y, vy);
            self.gen_mul(&gx, &gy)
        };
        self.reduce_deg6(&z6)
    }

    /// Doubling.
    pub fn double(&self, x: &PicClass) -> PicClass {
        self.add(x, x)
    }

    /// Subtraction.
    pub fn sub(&self, x: &PicClass, y: &PicClass) -> PicClass {
        let ny = self.neg(y);
        self.add(x, &ny)
    }

    /// Scalar multiplication (left-to-right double and add).
    pub fn mul_scalar(&self, x: &PicClass, k: u128) -> PicClass {
        let mut r = self.zero();
        if k == 0 {
            return r;
        }
        let top = 127 - k.leading_zeros();
        for i in (0..=top).rev() {
            r = self.double(&r);
            if (k >> i) & 1 == 1 {
                r = self.add(&r, x);
            }
        }
        r
    }

    /// Class (in `Pic^0`) of an effective divisor `Z` of degree 6 minus
    /// `2 D_inf`: the reduction core of `add`. `z6` must generate the ideal of
    /// `Z` (e.g. a product of two degree-3 generating spaces).
    pub fn reduce_deg6(&self, z6: &Gen) -> PicClass {
        self.reduce_deg6_aux(z6, 0)
    }

    /// [`reduce_deg6`](Self::reduce_deg6) using the `aux`-th (0, 1 or 2) echelon
    /// cubic through `E7` as the auxiliary cubic (the result does not depend on
    /// it; exposed so that the independence is tested).
    pub fn reduce_deg6_aux(&self, z6: &Gen, aux: usize) -> PicClass {
        self.bump(|s| s.ops += 1);
        let (k, w) = self.complete(z6.clone(), 6);
        let u4 = self.forms_through(&w, k, 3);
        assert_eq!(u4.len(), 4, "cubics through a degree-6 divisor");
        let in_supp = w.rows.iter().all(|r| self.eval_p0(k, r) == 0);
        let mut e7: Option<(usize, Quot)> = None;
        let v3: Vec<Vec<u32>> = if !in_supp {
            let vals: Vec<u32> = u4.iter().map(|u| self.eval_p0(3, u)).collect();
            let ker = self.nullspace(vec![vals], 4);
            ker.iter()
                .map(|c| {
                    let mut v = vec![0u32; self.dim[3]];
                    for (j, &cj) in c.iter().enumerate() {
                        if cj != 0 {
                            for (t, &ut) in u4[j].iter().enumerate() {
                                if ut != 0 {
                                    let m = self.fq.mul(cj, ut);
                                    v[t] = self.fq.add(v[t], m);
                                }
                            }
                        }
                    }
                    v
                })
                .collect()
        } else {
            self.bump(|s| s.p0_in_support += 1);
            let g = self.gen_mul(
                &Gen {
                    k,
                    rows: w.rows.clone(),
                },
                &self.lines_p0,
            );
            let (k2, w2) = self.complete(g, 7);
            let v = self.forms_through(&w2, k2, 3);
            e7 = Some((k2, w2));
            v
        };
        assert_eq!(v3.len(), 3, "cubics through E7");
        let v3q = self.quot_from(v3, self.dim[3]);
        assert_eq!(v3q.rows.len(), 3);
        let conics = self.forms_through(&v3q, 3, 2);
        if conics.len() == 1 {
            // E7 ~ 2K - P
            self.bump(|s| s.exc_results += 1);
            let (k2, w2) = match e7 {
                Some(x) => x,
                None => {
                    let g = self.gen_mul(
                        &Gen {
                            k,
                            rows: w.rows.clone(),
                        },
                        &self.lines_p0,
                    );
                    self.complete(g, 7)
                }
            };
            let ls = self.colon(&conics[0], 2, &w2.rows, k2, 1);
            assert_eq!(ls.len(), 2, "lines through the residual point");
            let p = self.cross(&ls[0], &ls[1]);
            let p = self.normalize_counted(p);
            debug_assert_eq!(self.eval_f(p), 0);
            return PicClass::Exc(p);
        }
        assert_eq!(conics.len(), 0, "more than one conic through E7");
        let c = v3q.rows[aux].clone();
        let others: Vec<Vec<u32>> = (0..3)
            .filter(|&i| i != aux)
            .map(|i| v3q.rows[i].clone())
            .collect();
        let qp = self.colon(&c, 3, &others, 3, 2);
        assert_eq!(qp.len(), 1, "conic through R5");
        let q1 = qp[0].clone();
        let cols: Vec<Vec<u32>> = (0..self.dim[2])
            .map(|j| self.mul_forms(3, &c, 2, &self.unit(2, j)))
            .collect();
        let rhs: Vec<Vec<u32>> = others
            .iter()
            .map(|v| self.mul_forms(2, &q1, 3, v))
            .collect();
        let gs = self
            .solve_multi(&cols, &rhs)
            .expect("g_v exist and are unique");
        let mut rows = vec![q1];
        rows.extend(gs);
        self.class_from_conics(rows)
    }

    /// Cross product of two lines (counted).
    fn cross(&self, a: &[u32], b: &[u32]) -> Pt {
        let m = |x: u32, y: u32| self.fq.mul(x, y);
        let s = |x: u32, y: u32| self.fq.sub(x, y);
        [
            s(m(a[1], b[2]), m(a[2], b[1])),
            s(m(a[2], b[0]), m(a[0], b[2])),
            s(m(a[0], b[1]), m(a[1], b[0])),
        ]
    }

    fn normalize_counted(&self, p: Pt) -> Pt {
        let c0 = self.counter();
        let Some(i) = (0..3).find(|&i| p[i] != 0) else {
            panic!("zero point");
        };
        let iv = self.fq.inv(p[i]);
        let mut o = [0u32; 3];
        for j in 0..3 {
            o[j] = if j == i { 1 } else { self.fq.mul(p[j], iv) };
        }
        let c1 = self.counter().since(&c0);
        self.bump(|s| {
            s.norm_mul += c1.mul;
            s.norm_inv += c1.inv;
        });
        o
    }

    /// Negation.
    pub fn neg(&self, x: &PicClass) -> PicClass {
        self.neg_with(x, 0)
    }

    /// Negation with an explicit line-section variant for an exceptional
    /// operand.
    pub fn neg_with(&self, x: &PicClass, vx: u32) -> PicClass {
        if self.is_zero(x) {
            return x.clone();
        }
        self.bump(|s| s.ops += 1);
        let gx = self.gen_of_with(x, vx);
        let g = self.gen_mul(&gx, &self.cons2p0);
        let (k, w) = self.complete(g, 5);
        let conics = self.forms_through(&w, k, 2);
        match conics.len() {
            1 => {
                let q1 = conics[0].clone();
                let v = self.forms_through(&w, k, 3);
                assert_eq!(v.len(), 5, "cubics through D_x + 2 P0");
                let rows = self.colon(&q1, 2, &v, 3, 2);
                self.class_from_conics(rows)
            }
            2 => {
                // pencil of conics L * l_i through D_x + 2P0: P = l_1 ^ l_2
                self.bump(|s| s.neg_pencil += 1);
                let (q1, q2) = (&conics[0], &conics[1]);
                let mut cols: Vec<Vec<u32>> = Vec::new();
                for j in 0..3 {
                    let u = self.unit(1, j);
                    let col = self.mul_forms(2, q2, 1, &u);
                    cols.push(col.iter().map(|&c| self.fq.neg(c)).collect());
                }
                for j in 0..3 {
                    let u = self.unit(1, j);
                    cols.push(self.mul_forms(2, q1, 1, &u));
                }
                // nullspace of the 10 x 6 matrix with the given columns
                let nr = self.dim[3];
                let mut eqs = vec![vec![0u32; 6]; nr];
                for (j, c) in cols.iter().enumerate() {
                    for r in 0..nr {
                        eqs[r][j] = c[r];
                    }
                }
                let ns = self.nullspace(eqs, 6);
                assert_eq!(ns.len(), 1, "common line factor of a pencil");
                let p = self.cross(&ns[0][0..3], &ns[0][3..6]);
                let p = self.normalize_counted(p);
                debug_assert_eq!(self.eval_f(p), 0);
                PicClass::Exc(p)
            }
            n => panic!("{} conics through D_x + 2 P0", n),
        }
    }

    /// Class equality (canonical forms are unique, so structural equality).
    pub fn eq(&self, x: &PicClass, y: &PicClass) -> bool {
        x == y
    }

    /// All rational points of `C` by brute force (small `q` only).
    pub fn rational_points_bruteforce(&self) -> Vec<Pt> {
        let q = self.q;
        let mut v = Vec::new();
        for x in 0..q {
            for y in 0..q {
                let p = [1, x, y];
                if self.eval_f(p) == 0 {
                    v.push(p);
                }
            }
        }
        for y in 0..q {
            let p = [0, 1, y];
            if self.eval_f(p) == 0 {
                v.push(p);
            }
        }
        if self.eval_f([0, 0, 1]) == 0 {
            v.push([0, 0, 1]);
        }
        v
    }
}

// -------------------------------------------------------------------------
// instance generation (setup; not charged to the group operations)
// -------------------------------------------------------------------------

/// xorshift64* step (the generator named in the W1 protocol).
pub fn xorshift_next(s: &mut u64) -> u64 {
    let mut x = *s;
    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;
    *s = x;
    x.wrapping_mul(0x2545F4914F6CDD1D)
}

/// The largest prime below `2^k`.
pub fn largest_prime_below_pow2(k: u32) -> u32 {
    let mut n = (1u64 << k) - 1;
    while !is_odd_prime_below_2_31(n) {
        n -= 1;
    }
    n as u32
}

fn pmod_trim(a: &mut Vec<u64>) {
    while a.last() == Some(&0) {
        a.pop();
    }
}

fn pmod_mul(q: u64, a: &[u64], b: &[u64]) -> Vec<u64> {
    if a.is_empty() || b.is_empty() {
        return vec![];
    }
    let mut r = vec![0u64; a.len() + b.len() - 1];
    for (i, &x) in a.iter().enumerate() {
        for (j, &y) in b.iter().enumerate() {
            r[i + j] = (r[i + j] + x * y % q) % q;
        }
    }
    pmod_trim(&mut r);
    r
}

fn pinv(q: u64, a: u64) -> u64 {
    let (mut r0, mut r1, mut t0, mut t1) = (q as i128, a as i128, 0i128, 1i128);
    while r1 != 0 {
        let d = r0 / r1;
        (r0, r1) = (r1, r0 - d * r1);
        (t0, t1) = (t1, t0 - d * t1);
    }
    t0.rem_euclid(q as i128) as u64
}

fn pmod_rem(q: u64, a: &[u64], g: &[u64]) -> Vec<u64> {
    let mut r = a.to_vec();
    pmod_trim(&mut r);
    let ig = pinv(q, *g.last().unwrap());
    while r.len() >= g.len() {
        let c = r.last().copied().unwrap() * ig % q;
        let sh = r.len() - g.len();
        for (i, &gi) in g.iter().enumerate() {
            r[sh + i] = (r[sh + i] + q - c * gi % q) % q;
        }
        pmod_trim(&mut r);
    }
    r
}

fn pmod_gcd(q: u64, a: &[u64], b: &[u64]) -> Vec<u64> {
    let (mut a, mut b) = (a.to_vec(), b.to_vec());
    pmod_trim(&mut a);
    pmod_trim(&mut b);
    while !b.is_empty() {
        let r = pmod_rem(q, &a, &b);
        a = b;
        b = r;
    }
    if let Some(&l) = a.last() {
        let il = pinv(q, l);
        for c in a.iter_mut() {
            *c = *c * il % q;
        }
    }
    a
}

fn pmod_powx(q: u64, base: &[u64], mut e: u64, g: &[u64]) -> Vec<u64> {
    let mut r = vec![1u64];
    let mut b = pmod_rem(q, base, g);
    while e > 0 {
        if e & 1 == 1 {
            r = pmod_rem(q, &pmod_mul(q, &r, &b), g);
        }
        b = pmod_rem(q, &pmod_mul(q, &b, &b), g);
        e >>= 1;
    }
    r
}

/// All roots in `F_q` of the polynomial with ascending coefficients `c`
/// (Cantor-Zassenhaus; setup only).
pub fn poly_roots(q: u32, c: &[u32], rng: &mut u64) -> Vec<u32> {
    let q = q as u64;
    let mut g: Vec<u64> = c.iter().map(|&x| x as u64).collect();
    pmod_trim(&mut g);
    if g.len() <= 1 {
        return vec![];
    }
    // g1 = gcd(x^q - x, g)
    let xq = pmod_powx(q, &[0, 1], q, &g);
    let mut diff = xq.clone();
    if diff.len() < 2 {
        diff.resize(2, 0);
    }
    diff[1] = (diff[1] + q - 1) % q;
    pmod_trim(&mut diff);
    let g1 = if diff.is_empty() {
        g.clone()
    } else {
        pmod_gcd(q, &g, &diff)
    };
    let mut roots = Vec::new();
    let mut stack = vec![g1];
    while let Some(h) = stack.pop() {
        if h.len() <= 1 {
            continue;
        }
        if h.len() == 2 {
            roots.push(((q - h[0]) % q * pinv(q, h[1]) % q) as u32);
            continue;
        }
        loop {
            let a = xorshift_next(rng) % q;
            let t = pmod_powx(q, &[a, 1], (q - 1) / 2, &h);
            let mut t1 = t.clone();
            if t1.is_empty() {
                t1.push(0);
            }
            t1[0] = (t1[0] + q - 1) % q;
            pmod_trim(&mut t1);
            let d = if t1.is_empty() {
                h.clone()
            } else {
                pmod_gcd(q, &h, &t1)
            };
            if d.len() > 1 && d.len() < h.len() {
                // divide h by d
                let mut quo = vec![0u64; h.len() - d.len() + 1];
                let mut r = h.clone();
                let id = pinv(q, *d.last().unwrap());
                while r.len() >= d.len() {
                    let cf = r.last().copied().unwrap() * id % q;
                    let sh = r.len() - d.len();
                    quo[sh] = cf;
                    for (i, &di) in d.iter().enumerate() {
                        r[sh + i] = (r[sh + i] + q - cf * di % q) % q;
                    }
                    pmod_trim(&mut r);
                }
                stack.push(d);
                stack.push(quo);
                break;
            }
        }
    }
    roots.sort();
    roots
}

/// Find a rational point of the quartic `f` by random search on lines
/// `(1 : y : z)`, `z` a root of `F(1,y,z)` (setup only).
pub fn find_rational_point(q: u32, f: &[u32; 15], rng: &mut u64, max_tries: usize) -> Option<Pt> {
    let m4 = mons_of_degree(4);
    let qq = q as u64;
    for _ in 0..max_tries {
        let y = xorshift_next(rng) % qq;
        // F(1,y,z) = sum_c z^c * (sum coef * y^b)
        let mut coef = vec![0u32; 5];
        for (i, &(_a, b, c)) in m4.iter().enumerate() {
            if f[i] == 0 {
                continue;
            }
            let mut yp = 1u64;
            for _ in 0..b {
                yp = yp * y % qq;
            }
            coef[c as usize] = ((coef[c as usize] as u64 + f[i] as u64 * yp) % qq) as u32;
        }
        let roots = poly_roots(q, &coef, rng);
        if let Some(&z) = roots.first() {
            return Some([1, y as u32, z]);
        }
    }
    None
}

/// First rational point in the canonical order `[1,x,y]` (by `x`, then `y`),
/// then `[0,1,y]`, then `[0,0,1]` (brute force; small `q`).
pub fn first_rational_point_canonical(q: u32, f: &[u32; 15]) -> Option<Pt> {
    let fq = Fq {
        q: q as u64,
        quadratic_nu: None,
        c_mul: Cell::new(0),
        c_inv: Cell::new(0),
        c_add: Cell::new(0),
    };
    let m4 = mons_of_degree(4);
    let eval = |p: Pt| -> bool {
        let mut s = 0u64;
        for (i, &(a, b, c)) in m4.iter().enumerate() {
            let t = fq.mulu(
                fq.mulu(fq.powu(p[0], a as u64), fq.powu(p[1], b as u64)),
                fq.powu(p[2], c as u64),
            );
            s += fq.mulu(t, f[i]) as u64;
        }
        s.is_multiple_of(q as u64)
    };
    for x in 0..q {
        for y in 0..q {
            if eval([1, x, y]) {
                return Some([1, x, y]);
            }
        }
    }
    for y in 0..q {
        if eval([0, 1, y]) {
            return Some([0, 1, y]);
        }
    }
    if eval([0, 0, 1]) {
        return Some([0, 0, 1]);
    }
    None
}

/// The first smooth quartic with a rational point from the xorshift64* stream
/// seeded at `seed`: coefficients are consecutive outputs mod `q` in the order of
/// `mons_of_degree(4)`; rejected quartics continue the same stream. Returns
/// the coefficients and the base point (the first point of
/// `rational_points_bruteforce` for `q <= 64`, else the first point found by
/// `find_rational_point`).
pub fn next_smooth_quartic_with_point(q: u32, rng: &mut u64) -> ([u32; 15], Pt) {
    loop {
        let mut f = [0u32; 15];
        for c in f.iter_mut() {
            *c = (xorshift_next(rng) % q as u64) as u32;
        }
        if !smoothness_certificate(q, &f) {
            continue;
        }
        if q <= 64 {
            if let Some(p) = first_rational_point_canonical(q, &f) {
                return (f, p);
            }
        } else if let Some(p) = find_rational_point(q, &f, rng, 4 * 64) {
            return (f, p);
        }
    }
}
