//! Jacobians of one-point superelliptic curves `y^m = F(x)`, `F = ∏ f_i^{e_i}`,
//! by ideal arithmetic in the maximal order — the engine for
//! **non-hyperelliptic** curves of every genus (and, at `m = 2`, a second
//! implementation of the hyperelliptic group law used as a cross-check).
//!
//! ## Model
//!
//! `K = F_p(x, y)`, `y^m = F(x)`, with `p ∤ m`, the `f_i` monic, pairwise
//! coprime and squarefree, `1 ≤ e_i < m`, `gcd(e_i, m) = 1`, and
//! `gcd(m, deg F) = 1`. Then every finite branch point and the point at
//! infinity are totally ramified; `∞` is the unique place above `x = ∞`,
//! rational of degree one; the genus is `g = (m − 1)(s − 1)/2` with
//! `s = Σ deg f_i` (Riemann–Hurwitz); and `Pic⁰(C) ≅ Cl(O)`, the ideal class
//! group of the integral closure `O` of `F_p[x]` in `K`.
//!
//! For `m ≥ 3` and `g ≥ 5` such a curve is never hyperelliptic
//! (Castelnuovo–Severi: a curve with maps of degree 2 and 3 to `P¹` has
//! genus ≤ 2). The trigonal family `y³ = f₁(x) f₂(x)²` realises every genus
//! `g ≥ 1` (`g = deg f₁ + deg f₂ − 1`, `deg F ≢ 0 mod 3`).
//!
//! ## Integral basis and multiplication
//!
//! `O = ⊕_j F_p[x]·b_j`, `b_j = y^j / D_j(x)`, `D_j = ∏_i f_i^{⌊j e_i / m⌋}`,
//! `j = 0..m−1` (standard for tame Kummer extensions). Pole orders at `∞`:
//! `w_j = −v_∞(b_j) = j·deg F − m·deg D_j`, pairwise distinct modulo `m`.
//! Products are `b_j b_k = μ_{jk}(x) b_{(j+k) mod m}` with polynomial `μ_{jk}`.
//!
//! ## Ideals, reduction and the canonical representative
//!
//! An integral ideal is an `F_p[x]`-lattice of rank `m`, stored as the row
//! Hermite normal form of its basis in coordinates (upper triangular, monic
//! pivots, entries above a pivot reduced modulo it); its degree is the sum
//! of the pivot degrees (`= deg N(I)`).
//!
//! For an ideal `I ↔ E` (effective divisor of degree `n`), an element
//! `φ ∈ I` of minimal pole order `t` spans the one-dimensional space
//! `L(t∞ − E)`, and `J = φ I⁻¹ ↔ (φ)₀ − E` is the effective divisor of
//! minimal degree in the class of `−(E − n∞)`. A complete linear system of
//! dimension ≥ 1 has a member through every point, `∞` included, so at the
//! minimal degree the system is a single divisor: **the minimal-degree
//! effective representative of a class is unique**, and `R(R(I))` is a
//! canonical form for `[I]`. That is the group law here:
//! `[I] + [J] = R(R(I·J))`, `−[I] = R(I)`.
//!
//! Minimal elements come from a weighted Popov (reduced) basis under the
//! weight `wdeg(Σ a_j b_j) = max_j (m·deg a_j + w_j)`; inverses from the
//! trace dual, `I⁻¹ = I^∨ · 𝔇`, where the trace form is anti-diagonal
//! (`Tr(b_j b_{m−j}) = m·rad F`) and the different `𝔇 = ∏ P_i^{m−1}` is the
//! diagonal ideal with `𝔇_jj = ∏_{i : j e_i ≢ −1 (mod m)} f_i`.
//!
//! Cost per group operation: `O(m²)` element products of `m²` polynomial
//! multiplications each, two Hermite reductions of `m² × m` polynomial
//! matrices and two weighted reductions. At `m = 3` and `g = 131` the
//! polynomials have degree up to a few hundred; at `m = 2g + 1` (the
//! three-point Jacobi-sum family) the matrices are `m × m` with constant
//! entries and the cost is dominated by `O(m³)` field operations per
//! Hermite form. This engine measures and verifies; it is not tuned.

use std::cell::Cell;

use rand::RngCore;

use super::cantor::hash_polys;
use super::ext::{mth_roots, Fq};
use super::fp::Fp;
use super::poly::Poly;
use super::{HgError, JacobianGroup};

/// The curve `y^m = ∏ f_i^{e_i}` with its integral basis data.
#[derive(Clone, Debug)]
pub struct SuperellipticCurve {
    pub field: Fp,
    pub m: u32,
    /// `(f_i, e_i)`, `f_i` monic squarefree pairwise coprime.
    pub factors: Vec<(Poly, u32)>,
    /// `F = ∏ f_i^{e_i}`.
    pub big_f: Poly,
    /// `rad F = ∏ f_i`.
    pub radical: Poly,
    /// `D_j`, `j = 0..m−1`.
    pub denominators: Vec<Poly>,
    /// Pole orders `w_j`.
    pub weights: Vec<usize>,
    /// `μ_{jk}`: `b_j b_k = μ_{jk} b_{(j+k) mod m}`.
    pub mu: Vec<Vec<Poly>>,
    /// Diagonal of the different `𝔇`.
    pub different_diag: Vec<Poly>,
    /// `m⁻¹ mod p`.
    pub m_inv: u64,
    pub genus: u32,
    ops: Cell<u64>,
    different_two_gens: std::sync::OnceLock<(Elt, Elt)>,
}

/// An integral ideal in row Hermite normal form (`rows[i][j]`, pivot `rows[i][i]` monic).
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct Ideal {
    pub rows: Vec<Vec<Poly>>,
}

impl Ideal {
    /// Degree `deg N(I) = Σ deg pivots`.
    pub fn degree(&self) -> usize {
        self.rows
            .iter()
            .enumerate()
            .map(|(i, r)| r[i].degree().unwrap_or(0))
            .sum()
    }

    /// Whether this is the unit ideal `O`.
    pub fn is_unit(&self) -> bool {
        self.rows.iter().enumerate().all(|(i, r)| r[i].is_one())
    }

    /// `N(I) = ∏ pivots` (monic).
    pub fn norm(&self, f: &Fp) -> Poly {
        let mut n = Poly::one();
        for (i, r) in self.rows.iter().enumerate() {
            n = n.mul(&r[i], f);
        }
        n
    }
}

/// Coordinate vector of an element of `O` (or of `K` after scaling).
pub type Elt = Vec<Poly>;

thread_local! {
    static EUCLID_ITERS: std::cell::Cell<u64> = const { std::cell::Cell::new(0) };
    /// Diagnostic accumulators (seconds): [hnf, mul_elt, two_generators, adjugate, minimal_element].
    static PROFILE: std::cell::RefCell<[f64; 5]> = const { std::cell::RefCell::new([0.0; 5]) };
}

/// Snapshot and reset the thread-local diagnostic timers
/// `[hnf, mul_elt, two_generators, adjugate, minimal_element]` in seconds.
pub fn profile_snapshot() -> [f64; 5] {
    PROFILE.with(|p| std::mem::take(&mut *p.borrow_mut()))
}

fn profile_add(slot: usize, t: std::time::Instant) {
    PROFILE.with(|p| p.borrow_mut()[slot] += t.elapsed().as_secs_f64());
}

impl SuperellipticCurve {
    /// Checked construction from `m` and the factored right-hand side.
    pub fn new(field: Fp, m: u32, factors: Vec<(Poly, u32)>) -> Result<Self, HgError> {
        if m < 2 {
            return Err(HgError::BadCurve("m must be at least 2"));
        }
        if field.p().is_multiple_of(m as u64) || (m as u64).is_multiple_of(field.p()) {
            return Err(HgError::BadCurve("p must not divide m"));
        }
        if factors.is_empty() {
            return Err(HgError::BadCurve("F must be non-constant"));
        }
        let mut big_f = Poly::one();
        let mut radical = Poly::one();
        let mut s = 0usize;
        for (i, (fi, ei)) in factors.iter().enumerate() {
            if fi.deg() < 1 || !fi.is_monic() {
                return Err(HgError::BadCurve("each f_i must be monic non-constant"));
            }
            if !fi.is_squarefree(&field) {
                return Err(HgError::BadCurve("each f_i must be squarefree"));
            }
            if *ei == 0 || *ei >= m || gcd_u64(*ei as u64, m as u64) != 1 {
                return Err(HgError::BadCurve(
                    "exponents must satisfy 1 ≤ e_i < m, gcd(e_i, m) = 1",
                ));
            }
            for (fj, _) in factors.iter().skip(i + 1) {
                if !fi.gcd(fj, &field).is_one() {
                    return Err(HgError::BadCurve("the f_i must be pairwise coprime"));
                }
            }
            for _ in 0..*ei {
                big_f = big_f.mul(fi, &field);
            }
            radical = radical.mul(fi, &field);
            s += fi.degree().unwrap_or(0);
        }
        let d = big_f.degree().unwrap_or(0) as u64;
        if gcd_u64(d, m as u64) != 1 {
            return Err(HgError::BadCurve(
                "gcd(m, deg F) must be 1 (one place at infinity)",
            ));
        }
        let mm = m as usize;
        let mut denominators = Vec::with_capacity(mm);
        for j in 0..mm {
            let mut dj = Poly::one();
            for (fi, ei) in &factors {
                let k = (j * *ei as usize) / mm;
                for _ in 0..k {
                    dj = dj.mul(fi, &field);
                }
            }
            denominators.push(dj);
        }
        let weights: Vec<usize> = (0..mm)
            .map(|j| j * d as usize - mm * denominators[j].degree().unwrap_or(0))
            .collect();
        let mut mu = vec![vec![Poly::zero(); mm]; mm];
        for j in 0..mm {
            for k in 0..mm {
                let num = if j + k < mm {
                    denominators[j + k].clone()
                } else {
                    big_f.mul(&denominators[j + k - mm], &field)
                };
                let den = denominators[j].mul(&denominators[k], &field);
                mu[j][k] = num
                    .div_exact(&den, &field)
                    .ok_or(HgError::BadCurve("integral basis"))?;
            }
        }
        let mut different_diag = Vec::with_capacity(mm);
        for j in 0..mm {
            let mut dj = Poly::one();
            for (fi, ei) in &factors {
                if (j * *ei as usize) % mm != mm - 1 {
                    dj = dj.mul(fi, &field);
                }
            }
            different_diag.push(dj);
        }
        let m_inv = field
            .inv(m as u64 % field.p())
            .ok_or(HgError::BadCurve("m invertible"))?;
        let genus = ((m as usize - 1) * (s - 1) / 2) as u32;
        Ok(Self {
            field,
            m,
            factors,
            big_f,
            radical,
            denominators,
            weights,
            mu,
            different_diag,
            m_inv,
            genus,
            ops: Cell::new(0),
            different_two_gens: std::sync::OnceLock::new(),
        })
    }

    /// `y^m = F(x)` with squarefree `F` (`gcd(m, deg F) = 1`).
    pub fn from_squarefree(field: Fp, m: u32, big_f: Poly) -> Result<Self, HgError> {
        Self::new(field, m, vec![(big_f, 1)])
    }

    /// A random trigonal curve `y³ = f₁ f₂²` of genus `g` (`m = 3`): `deg f₂ = 1`
    /// and `deg f₁ = g` when `g + 2 ≢ 0 (mod 3)`, else `deg f₂ = 2`, `deg f₁ = g − 1`.
    /// Non-hyperelliptic for `g ≥ 5`.
    pub fn random_trigonal(field: Fp, genus: u32, rng: &mut impl RngCore) -> Result<Self, HgError> {
        if field.p() == 3 {
            return Err(HgError::BadCurve(
                "y³ = F is inseparable in characteristic 3",
            ));
        }
        if genus < 1 {
            return Err(HgError::BadCurve("genus must be positive"));
        }
        let g = genus as usize;
        // deg F = d1 + 2 d2, s = d1 + d2 = g + 1.
        let (d1, d2) = if !(g + 2).is_multiple_of(3) {
            (g, 1)
        } else {
            (g - 1, 2)
        };
        for _ in 0..1000 {
            let f2 = Poly::random_squarefree_monic(d2, &field, rng);
            let mut factors = Vec::new();
            if d1 > 0 {
                let f1 = Poly::random_squarefree_monic(d1, &field, rng);
                if !f1.gcd(&f2, &field).is_one() {
                    continue;
                }
                factors.push((f1, 1));
            }
            factors.push((f2, 2));
            if let Ok(c) = Self::new(field, 3, factors) {
                debug_assert_eq!(c.genus, genus);
                return Ok(c);
            }
        }
        Err(HgError::Exhausted("random trigonal curve"))
    }

    /// A random `y^m = F(x)` curve with squarefree `F` of degree `d`, `gcd(m, d) = 1`.
    pub fn random_superelliptic(
        field: Fp,
        m: u32,
        d: usize,
        rng: &mut impl RngCore,
    ) -> Result<Self, HgError> {
        let big_f = Poly::random_squarefree_monic(d, &field, rng);
        Self::from_squarefree(field, m, big_f)
    }

    fn bump(&self) {
        self.ops.set(self.ops.get() + 1);
    }

    fn mm(&self) -> usize {
        self.m as usize
    }

    // ── Elements ────────────────────────────────────────────────────────

    /// Product of two elements of `O` in coordinates.
    pub fn mul_elt(&self, a: &Elt, b: &Elt) -> Elt {
        let _t = std::time::Instant::now();
        let k = &self.field;
        let m = self.mm();
        let mut out = vec![Poly::zero(); m];
        for j in 0..m {
            if a[j].is_zero() {
                continue;
            }
            for l in 0..m {
                if b[l].is_zero() {
                    continue;
                }
                let prod = a[j].mul(&b[l], k).mul(&self.mu[j][l], k);
                let idx = (j + l) % m;
                out[idx].add_assign(&prod, k);
            }
        }
        profile_add(1, _t);
        out
    }

    /// Multiply an element by a polynomial scalar.
    pub fn scale_elt(&self, a: &Elt, s: &Poly) -> Elt {
        a.iter().map(|x| x.mul(s, &self.field)).collect()
    }

    /// Weighted degree (pole order at `∞`); `None` for zero.
    pub fn wdeg(&self, a: &Elt) -> Option<usize> {
        let m = self.mm();
        let mut best: Option<usize> = None;
        for j in 0..m {
            if let Some(d) = a[j].degree() {
                let w = m * d + self.weights[j];
                best = Some(best.map_or(w, |b| b.max(w)));
            }
        }
        best
    }

    /// Index `j` attaining the weighted degree (unique), and that degree.
    fn pivot(&self, a: &Elt) -> Option<(usize, usize)> {
        let m = self.mm();
        let mut best: Option<(usize, usize)> = None;
        for j in 0..m {
            if let Some(d) = a[j].degree() {
                let w = m * d + self.weights[j];
                if best.is_none_or(|(_, bw)| w > bw) {
                    best = Some((j, w));
                }
            }
        }
        best
    }

    /// The element `y` (as `D_1 b_1`).
    pub fn elt_y(&self) -> Elt {
        let m = self.mm();
        let mut e = vec![Poly::zero(); m];
        e[1 % m] = self.denominators[1 % m].clone();
        if m == 1 {
            e[0] = self.big_f.clone();
        }
        e
    }

    /// The element `a(x) ∈ F_p[x] ⊂ O`.
    pub fn elt_poly(&self, a: &Poly) -> Elt {
        let m = self.mm();
        let mut e = vec![Poly::zero(); m];
        e[0] = a.clone();
        e
    }

    // ── Hermite normal form ─────────────────────────────────────────────

    /// Row Hermite normal form of the lattice spanned by `gens` (each of
    /// length `m`); panics if the lattice has rank below `m`.
    pub fn hnf(&self, gens: Vec<Elt>) -> Ideal {
        self.hnf_mod(gens, None)
    }

    /// Row Hermite normal form of the lattice spanned by `gens`, reducing
    /// every entry modulo `modulus` when one is given. The modulus must be
    /// a monic polynomial `D` with `D·F_p[x]^m ⊆ lattice` (for an ideal,
    /// any multiple of its norm): the rows `D·e_j` are then added to the
    /// generators and no entry ever exceeds degree `deg D`, which is what
    /// keeps the elimination from the degree swell of a plain Euclidean
    /// Hermite form.
    pub fn hnf_mod(&self, mut gens: Vec<Elt>, modulus: Option<&Poly>) -> Ideal {
        let _t = std::time::Instant::now();
        let k = &self.field;
        let m = self.mm();
        if let Some(d) = modulus {
            for g in gens.iter_mut() {
                for x in g.iter_mut() {
                    if x.deg() >= d.deg() {
                        *x = x.rem(d, k);
                    }
                }
            }
            for j in 0..m {
                let mut e = vec![Poly::zero(); m];
                e[j] = d.clone();
                gens.push(e);
            }
        }
        let reduce = |x: &mut Poly| {
            if let Some(d) = modulus {
                if x.deg() >= d.deg() {
                    *x = x.rem(d, k);
                }
            }
        };
        let mut rows: Vec<Elt> = Vec::with_capacity(m);
        for col in 0..m {
            // Euclid on column `col` over the remaining generators.
            loop {
                let mut nz: Vec<usize> = (0..gens.len())
                    .filter(|&i| !gens[i][col].is_zero())
                    .collect();
                if nz.len() <= 1 {
                    break;
                }
                EUCLID_ITERS.with(|c| c.set(c.get() + 1));
                if std::env::var_os("HG_DEBUG_HNF").is_some() {
                    let maxdeg = gens
                        .iter()
                        .flat_map(|r| r.iter())
                        .map(|p| p.deg())
                        .max()
                        .unwrap_or(-1);
                    eprintln!(
                        "  col {col}: {} gens, {} nonzero, maxdeg {maxdeg}",
                        gens.len(),
                        nz.len()
                    );
                }
                nz.sort_by_key(|&i| gens[i][col].degree().unwrap_or(0));
                let pivot_i = nz[0];
                let pivot_row = gens[pivot_i].clone();
                for &i in nz.iter().skip(1) {
                    let (q, _) = gens[i][col].divrem(&pivot_row[col], k);
                    if q.is_zero() {
                        continue;
                    }
                    for c in col..m {
                        if pivot_row[c].is_zero() {
                            continue;
                        }
                        let sub = q.mul(&pivot_row[c], k);
                        gens[i][c].sub_assign(&sub, k);
                        reduce(&mut gens[i][c]);
                    }
                }
            }
            let idx = (0..gens.len()).find(|&i| !gens[i][col].is_zero());
            let idx = idx.unwrap_or_else(|| panic!("lattice has rank below m at column {col}"));
            let mut row = gens.swap_remove(idx);
            let lc_inv = k.inv(row[col].leading()).expect("unit");
            for c in col..m {
                row[c] = row[c].mul_scalar(lc_inv, k);
            }
            rows.push(row);
            // Drop generators that are now zero.
            gens.retain(|g| g.iter().any(|x| !x.is_zero()));
        }
        // Reduce entries above each pivot modulo the pivot.
        for i in 0..m {
            let pivot_row = rows[i].clone();
            for r in 0..i {
                let (q, rem) = rows[r][i].divrem(&pivot_row[i], k);
                if q.is_zero() {
                    continue;
                }
                rows[r][i] = rem;
                for c in (i + 1)..m {
                    if pivot_row[c].is_zero() {
                        continue;
                    }
                    let sub = q.mul(&pivot_row[c], k);
                    rows[r][c].sub_assign(&sub, k);
                    reduce(&mut rows[r][c]);
                }
            }
        }
        profile_add(0, _t);
        if std::env::var_os("HG_DEBUG_HNF").is_some() {
            let maxdeg = rows
                .iter()
                .flat_map(|r| r.iter())
                .map(|p| p.deg())
                .max()
                .unwrap_or(-1);
            let total: isize = rows
                .iter()
                .flat_map(|r| r.iter())
                .map(|p| p.deg().max(0))
                .sum();
            eprintln!(
                "hnf: m={m} out maxdeg {maxdeg} total {total} time {:?} euclid_iters {}",
                _t.elapsed(),
                EUCLID_ITERS.with(|c| c.get())
            );
        }
        Ideal { rows }
    }

    /// The unit ideal `O`.
    pub fn unit_ideal(&self) -> Ideal {
        let m = self.mm();
        let mut rows = vec![vec![Poly::zero(); m]; m];
        for (i, r) in rows.iter_mut().enumerate() {
            r[i] = Poly::one();
        }
        Ideal { rows }
    }

    /// Ideal generated (as an `O`-ideal) by the given elements.
    pub fn ideal_from_generators(&self, gens: &[Elt]) -> Ideal {
        self.ideal_from_generators_mod(gens, None)
    }

    /// [`Self::ideal_from_generators`] with a known lattice modulus.
    pub fn ideal_from_generators_mod(&self, gens: &[Elt], modulus: Option<&Poly>) -> Ideal {
        let m = self.mm();
        let mut lattice_gens = Vec::with_capacity(gens.len() * m);
        for g in gens {
            for j in 0..m {
                let mut bj = vec![Poly::zero(); m];
                bj[j] = Poly::one();
                lattice_gens.push(self.mul_elt(g, &bj));
            }
        }
        self.hnf_mod(lattice_gens, modulus)
    }

    /// The principal ideal `(φ)`.
    pub fn principal(&self, phi: &Elt) -> Ideal {
        let n = self.norm_elt(phi);
        self.ideal_from_generators_mod(std::slice::from_ref(phi), Some(&n))
    }

    /// `N(φ)` (monic): determinant of the regular representation of `φ`,
    /// by fraction-free (Bareiss) elimination over `F_p[x]`.
    pub fn norm_elt(&self, phi: &Elt) -> Poly {
        let k = &self.field;
        let m = self.mm();
        let mut mat: Vec<Vec<Poly>> = Vec::with_capacity(m);
        for j in 0..m {
            let mut bj = vec![Poly::zero(); m];
            bj[j] = Poly::one();
            mat.push(self.mul_elt(phi, &bj));
        }
        let d = det_poly(&mat, k);
        d.monic(k)
    }

    /// Rank above which ideals are multiplied through a two-element
    /// `O`-generating set instead of all `m²` basis products.
    const TWO_GENERATOR_RANK: usize = 7;

    /// Two elements `(N(I), γ)` generating `I` as an `O`-ideal (Dedekind
    /// domains are 1½-generated; a random `γ ∈ I` works with high
    /// probability and the result is verified by a Hermite form).
    pub fn two_generators(&self, ideal: &Ideal) -> (Elt, Elt) {
        let _t = std::time::Instant::now();
        let k = &self.field;
        let m = self.mm();
        let n = self.elt_poly(&ideal.norm(k));
        let mut seed = 0x9e37_79b9u64 ^ (ideal.degree() as u64);
        for _ in 0..64 {
            // γ = Σ c_i r_i with small random polynomial coefficients.
            let mut gamma = vec![Poly::zero(); m];
            for r in &ideal.rows {
                seed = seed
                    .wrapping_mul(6364136223846793005)
                    .wrapping_add(1442695040888963407);
                let c0 = (seed >> 33) % k.p();
                seed = seed
                    .wrapping_mul(6364136223846793005)
                    .wrapping_add(1442695040888963407);
                let c1 = (seed >> 33) % k.p();
                let c = Poly::from_coeffs(vec![c0, c1], k);
                if c.is_zero() {
                    continue;
                }
                for j in 0..m {
                    if !r[j].is_zero() {
                        gamma[j].add_assign(&r[j].mul(&c, k), k);
                    }
                }
            }
            if gamma.iter().all(|x| x.is_zero()) {
                continue;
            }
            let test = self.ideal_from_generators_mod(&[n.clone(), gamma.clone()], Some(&n[0]));
            if test == *ideal {
                profile_add(2, _t);
                return (n, gamma);
            }
        }
        panic!("could not find two generators of the ideal");
    }

    /// Product of two ideals.
    pub fn mul_ideals(&self, a: &Ideal, b: &Ideal) -> Ideal {
        let m = self.mm();
        let k = &self.field;
        let modulus = a.norm(k).mul(&b.norm(k), k);
        if m > Self::TWO_GENERATOR_RANK {
            let (ga, gb) = self.two_generators(a);
            let mut gens = Vec::with_capacity(2 * m);
            for s in &b.rows {
                gens.push(self.mul_elt(&ga, s));
                gens.push(self.mul_elt(&gb, s));
            }
            return self.hnf_mod(gens, Some(&modulus));
        }
        let mut gens = Vec::with_capacity(a.rows.len() * b.rows.len());
        for r in &a.rows {
            for s in &b.rows {
                gens.push(self.mul_elt(r, s));
            }
        }
        self.hnf_mod(gens, Some(&modulus))
    }

    /// Whether `e ∈ I` (solve the triangular system).
    pub fn contains(&self, ideal: &Ideal, e: &Elt) -> bool {
        let k = &self.field;
        let m = self.mm();
        let mut v = e.clone();
        for i in 0..m {
            if v[i].is_zero() {
                continue;
            }
            let (q, r) = v[i].divrem(&ideal.rows[i][i], k);
            if !r.is_zero() {
                return false;
            }
            for c in i..m {
                let sub = q.mul(&ideal.rows[i][c], k);
                v[c].sub_assign(&sub, k);
            }
        }
        true
    }

    // ── Minimal element ────────────────────────────────────────────────

    /// A nonzero element of `I` of minimal pole order (weighted Popov reduction).
    pub fn minimal_element(&self, ideal: &Ideal) -> Elt {
        let _t = std::time::Instant::now();
        let k = &self.field;
        let m = self.mm();
        let mut rows: Vec<Elt> = ideal.rows.clone();
        loop {
            let pivots: Vec<(usize, usize)> = rows
                .iter()
                .map(|r| self.pivot(r).expect("basis rows are nonzero"))
                .collect();
            // Find two rows sharing a pivot index.
            let mut clash = None;
            'outer: for i in 0..m {
                for j in 0..m {
                    if i != j && pivots[i].0 == pivots[j].0 && pivots[i].1 >= pivots[j].1 {
                        clash = Some((i, j));
                        break 'outer;
                    }
                }
            }
            let Some((i, j)) = clash else { break };
            let (col, wi) = pivots[i];
            let wj = pivots[j].1;
            debug_assert_eq!((wi - wj) % m, 0);
            let shift = (wi - wj) / m;
            let coef = k
                .div(rows[i][col].leading(), rows[j][col].leading())
                .expect("unit");
            let factor = Poly::monomial(shift, coef);
            let rj = rows[j].clone();
            for c in 0..m {
                if rj[c].is_zero() {
                    continue;
                }
                let sub = rj[c].mul(&factor, k);
                rows[i][c].sub_assign(&sub, k);
            }
            debug_assert!(rows[i].iter().any(|x| !x.is_zero()));
        }
        let mut best = 0;
        let mut best_w = self.wdeg(&rows[0]).unwrap();
        for i in 1..m {
            let w = self.wdeg(&rows[i]).unwrap();
            if w < best_w {
                best_w = w;
                best = i;
            }
        }
        profile_add(4, _t);
        rows.swap_remove(best)
    }

    // ── Inversion and reduction ────────────────────────────────────────

    /// Adjugate of the transpose of the HNF matrix: `adj(Mᵀ)`, by forward
    /// substitution (`Mᵀ` is lower triangular and `adj = det · inverse`,
    /// whose entries are polynomials): column `j` solves `Mᵀ c = det·e_j`.
    fn adjugate_transpose(&self, ideal: &Ideal) -> Vec<Vec<Poly>> {
        let _t = std::time::Instant::now();
        let k = &self.field;
        let m = self.mm();
        let det = ideal.norm(k);
        // A[i][l] = M[l][i] (lower triangular).
        let a = |i: usize, l: usize| &ideal.rows[l][i];
        let mut adj = vec![vec![Poly::zero(); m]; m];
        for j in 0..m {
            // c[i] = 0 for i < j; c[j] = det / A[j][j]; then forward.
            let mut c = vec![Poly::zero(); m];
            c[j] = det.div_exact(a(j, j), k).expect("pivot divides det");
            for i in j + 1..m {
                let mut acc = Poly::zero();
                for l in j..i {
                    if !c[l].is_zero() && !a(i, l).is_zero() {
                        acc.add_assign(&a(i, l).mul(&c[l], k), k);
                    }
                }
                if !acc.is_zero() {
                    c[i] = acc
                        .neg(k)
                        .div_exact(a(i, i), k)
                        .expect("adjugate entries are polynomials");
                }
            }
            for i in 0..m {
                adj[i][j] = std::mem::take(&mut c[i]);
            }
        }
        profile_add(3, _t);
        adj
    }

    /// `(φ) : I = φ·I⁻¹` for `φ ∈ I` (an integral ideal of degree `wdeg φ − deg I`).
    pub fn quotient(&self, ideal: &Ideal, phi: &Elt) -> Ideal {
        let k = &self.field;
        let m = self.mm();
        let n_i = ideal.norm(k);
        let adj = self.adjugate_transpose(ideal);
        // D'_{k,0} = R·A_{k,0}; D'_{k,l} = A_{k,m−l} for l ≥ 1.
        let mut dprime: Vec<Elt> = Vec::with_capacity(m);
        for row in adj.iter() {
            let mut d = vec![Poly::zero(); m];
            d[0] = row[0].mul(&self.radical, k);
            for l in 1..m {
                d[l] = row[m - l].clone();
            }
            dprime.push(d);
        }
        // φ · δ for δ over O-generators of the different (all m diagonal
        // elements at small rank, two generators at high rank).
        let mut phi_d: Vec<Elt> = Vec::with_capacity(m);
        if m > Self::TWO_GENERATOR_RANK {
            let (da, db) = self.different_generators();
            phi_d.push(self.mul_elt(phi, &da));
            phi_d.push(self.mul_elt(phi, &db));
        } else {
            for j in 0..m {
                let mut bj = vec![Poly::zero(); m];
                bj[j] = self.different_diag[j].clone();
                phi_d.push(self.mul_elt(phi, &bj));
            }
        }
        let mut gens = Vec::with_capacity(m * m);
        for d in &dprime {
            for pd in &phi_d {
                gens.push(self.mul_elt(d, pd));
            }
        }
        // The scaled lattice (N(I)·R)·J contains N(I)·R·N(φ)·F_p[x]^m since N(J) | N(φ).
        let den = n_i.mul(&self.radical, k);
        let modulus = den.mul(&self.norm_elt(phi), k);
        let scaled = self.hnf_mod(gens, Some(&modulus));
        // Divide by m·N(I)·R exactly.
        let mut rows = Vec::with_capacity(m);
        for r in scaled.rows {
            let mut out = Vec::with_capacity(m);
            for x in r {
                let q = x.div_exact(&den, k).expect("φ I⁻¹ is integral");
                out.push(q.mul_scalar(self.m_inv, k));
            }
            rows.push(out);
        }
        // Scaling by a constant keeps pivots monic only up to the constant m⁻¹·lc;
        // renormalise to a proper HNF.
        let nj = self.norm_elt(phi).div_exact(&n_i, k).expect("N(I) | N(φ)");
        self.hnf_mod(rows, Some(&nj))
    }

    /// The different as an ideal.
    pub fn different(&self) -> Ideal {
        let m = self.mm();
        let mut rows = vec![vec![Poly::zero(); m]; m];
        for (i, r) in rows.iter_mut().enumerate() {
            r[i] = self.different_diag[i].clone();
        }
        Ideal { rows }
    }

    /// Two `O`-generators of the different (cached).
    fn different_generators(&self) -> (Elt, Elt) {
        self.different_two_gens
            .get_or_init(|| self.two_generators(&self.different()))
            .clone()
    }

    /// One reduction step: the minimal-degree representative of `−[I]`.
    pub fn reduce_once(&self, ideal: &Ideal) -> Ideal {
        let phi = self.minimal_element(ideal);
        let out = self.quotient(ideal, &phi);
        debug_assert_eq!(out.degree() + ideal.degree(), self.wdeg(&phi).unwrap());
        out
    }

    /// Canonical representative of `[I]` (double reduction).
    pub fn canonical(&self, ideal: &Ideal) -> Ideal {
        self.reduce_once(&self.reduce_once(ideal))
    }

    // ── Places ─────────────────────────────────────────────────────────

    /// Places (prime ideals of residue degree one over `π`) above the monic
    /// irreducible `π`: the unique ramified prime if `π | F`, else one prime
    /// `(π, y − r)` per root `r ∈ F_π` of `t^m = F mod π`.
    /// Returns `(prime ideal, r)` with `r = 0` for the ramified prime.
    pub fn places_above(&self, pi: &Poly, rng: &mut impl RngCore) -> Vec<(Ideal, Poly)> {
        let k = &self.field;
        let m = self.mm();
        if self.big_f.rem(pi, k).is_zero() {
            // Ramified: diag(π, 1, …, 1).
            let mut rows = vec![vec![Poly::zero(); m]; m];
            for (i, r) in rows.iter_mut().enumerate() {
                r[i] = if i == 0 { pi.clone() } else { Poly::one() };
            }
            return vec![(Ideal { rows }, Poly::zero())];
        }
        let fq = Fq::new(*k, pi.clone());
        let fbar = fq.reduce(&self.big_f);
        let mut out = Vec::new();
        for r in mth_roots(&fbar, self.m, &fq, rng) {
            let ideal = self.prime_from_root(pi, &r);
            out.push((ideal, r));
        }
        out
    }

    /// The prime `(π, y − r)` with `r^m ≡ F (mod π)`, `π ∤ F`.
    pub fn prime_from_root(&self, pi: &Poly, r: &Poly) -> Ideal {
        let k = &self.field;
        let m = self.mm();
        let mut y_minus_r = vec![Poly::zero(); m];
        y_minus_r[0] = r.neg(k);
        y_minus_r[1 % m].add_assign(&self.denominators[1 % m], k);
        let gens = vec![self.elt_poly(pi), y_minus_r];
        self.ideal_from_generators_mod(&gens, Some(pi))
    }

    /// Evaluate the element at `y = r` modulo `π^a` (for `π ∤ F`):
    /// `Σ a_j D_j⁻¹ r^j mod π^a`. Zero iff the element lies in `(π^a, y − r)`.
    fn eval_at_root_mod(&self, e: &Elt, r: &Poly, modulus: &Poly) -> Poly {
        let k = &self.field;
        let m = self.mm();
        let mut acc = Poly::zero();
        let mut rpow = Poly::one();
        for j in 0..m {
            if !e[j].is_zero() {
                let dinv = self.denominators[j].inv_mod(modulus, k).expect("π ∤ D_j");
                let term = Poly::mulmod(&Poly::mulmod(&e[j], &dinv, modulus, k), &rpow, modulus, k);
                acc = acc.add(&term, k).rem(modulus, k);
            }
            rpow = Poly::mulmod(&rpow, r, modulus, k);
        }
        acc
    }

    /// Valuation `v_P(I)` at the prime `P = (π, y − r)` (`π ∤ F`), given that
    /// `v_π(N(I)) = c`; lifts `r` to a root modulo `π^a` by Newton's method.
    pub fn valuation_unramified(&self, ideal: &Ideal, pi: &Poly, r: &Poly, c: usize) -> usize {
        let k = &self.field;
        let m_poly = Poly::constant(self.m as u64 % k.p());
        let mut modulus = pi.clone();
        let mut root = r.rem(pi, k);
        let mut a = 0usize;
        loop {
            if a == c {
                return a;
            }
            // Check membership modulo the current modulus π^{a+1}.
            let all_in = ideal
                .rows
                .iter()
                .all(|row| self.eval_at_root_mod(row, &root, &modulus).is_zero());
            if !all_in {
                return a;
            }
            a += 1;
            if a == c {
                return a;
            }
            // Lift to π^{a+1}: Newton step r ← r − (r^m − F)/(m r^{m−1}).
            let next = modulus.mul(pi, k);
            let rm1 = root.powmod_u64(self.m as u64 - 1, &next, k);
            let rm = Poly::mulmod(&rm1, &root, &next, k);
            let num = rm.sub(&self.big_f, k).rem(&next, k);
            let den = Poly::mulmod(&m_poly, &rm1, &next, k);
            let den_inv = den.inv_mod(&next, k).expect("simple root lifts");
            let delta = Poly::mulmod(&num, &den_inv, &next, k);
            root = root.sub(&delta, k).rem(&next, k);
            modulus = next;
        }
    }

    /// Valuation at the ramified prime above `π | F`: `min_j (m·v_π(a_j) + (j e_i mod m))`
    /// over the rows, with `e_i` the exponent of the factor containing `π`.
    pub fn valuation_ramified(&self, ideal: &Ideal, pi: &Poly) -> usize {
        let k = &self.field;
        let m = self.mm();
        let e = self
            .factors
            .iter()
            .find(|(fi, _)| fi.rem(pi, k).is_zero())
            .map(|(_, e)| *e as usize)
            .expect("π divides F");
        let mut best = usize::MAX;
        for row in &ideal.rows {
            for j in 0..m {
                if row[j].is_zero() {
                    continue;
                }
                let mut v = 0;
                let mut a = row[j].clone();
                loop {
                    let (q, r) = a.divrem(pi, k);
                    if !r.is_zero() {
                        break;
                    }
                    v += 1;
                    a = q;
                }
                let val = m * v + (j * e) % m;
                best = best.min(val);
            }
        }
        // A prime P with P^m = (π): v_P(I) in units where v_P(π) = m.
        best
    }

    /// A random element: product of random places of degree ≤ `max_place_degree`,
    /// reduced to canonical form.
    pub fn random_element(&self, max_place_degree: usize, rng: &mut impl RngCore) -> Ideal {
        let k = &self.field;
        let g = self.genus as usize;
        let mut acc = self.unit_ideal();
        let mut total = 0usize;
        let mut guard = 0;
        while total < g.max(1) {
            guard += 1;
            if guard > 10_000 {
                break;
            }
            let d = 1 + (rng.next_u64() as usize) % max_place_degree.max(1);
            let pi = Poly::random_irreducible(d, k, rng);
            let places = self.places_above(&pi, rng);
            if places.is_empty() {
                continue;
            }
            let pick = (rng.next_u64() as usize) % places.len();
            acc = self.canonical(&self.mul_ideals(&acc, &places[pick].0));
            total += d;
        }
        acc
    }

    /// Group addition on canonical representatives.
    pub fn add_classes(&self, a: &Ideal, b: &Ideal) -> Ideal {
        self.bump();
        if a.is_unit() {
            return b.clone();
        }
        if b.is_unit() {
            return a.clone();
        }
        self.canonical(&self.mul_ideals(a, b))
    }

    /// Group negation on canonical representatives.
    pub fn neg_class(&self, a: &Ideal) -> Ideal {
        if a.is_unit() {
            return a.clone();
        }
        self.reduce_once(a)
    }

    /// Check that `I` is a canonical representative (`R(R(I)) = I`).
    pub fn is_canonical(&self, a: &Ideal) -> bool {
        a.degree() <= self.genus as usize && self.canonical(a) == *a
    }
}

fn gcd_u64(mut a: u64, mut b: u64) -> u64 {
    while b != 0 {
        let t = a % b;
        a = b;
        b = t;
    }
    a
}

/// Determinant over `F_p[x]` by Laplace expansion for `n ≤ 2`, Bareiss otherwise.
fn det_poly(a: &[Vec<Poly>], k: &Fp) -> Poly {
    let n = a.len();
    match n {
        0 => Poly::one(),
        1 => a[0][0].clone(),
        2 => a[0][0].mul(&a[1][1], k).sub(&a[0][1].mul(&a[1][0], k), k),
        _ => {
            let mut m: Vec<Vec<Poly>> = a.to_vec();
            let mut sign = false;
            let mut prev = Poly::one();
            for i in 0..n - 1 {
                if m[i][i].is_zero() {
                    let Some(sw) = (i + 1..n).find(|&r| !m[r][i].is_zero()) else {
                        return Poly::zero();
                    };
                    m.swap(i, sw);
                    sign = !sign;
                }
                for r in i + 1..n {
                    for c in i + 1..n {
                        let num = m[r][c].mul(&m[i][i], k).sub(&m[r][i].mul(&m[i][c], k), k);
                        m[r][c] = num.div_exact(&prev, k).expect("Bareiss exact division");
                    }
                    m[r][i] = Poly::zero();
                }
                prev = m[i][i].clone();
            }
            let d = m[n - 1][n - 1].clone();
            if sign {
                d.neg(k)
            } else {
                d
            }
        }
    }
}

impl JacobianGroup for SuperellipticCurve {
    type Elem = Ideal;

    fn identity(&self) -> Ideal {
        self.unit_ideal()
    }

    fn add(&self, a: &Ideal, b: &Ideal) -> Ideal {
        self.add_classes(a, b)
    }

    fn neg(&self, a: &Ideal) -> Ideal {
        self.neg_class(a)
    }

    fn is_identity(&self, a: &Ideal) -> bool {
        a.is_unit()
    }

    fn hash64(&self, a: &Ideal) -> u64 {
        let refs: Vec<&Poly> = a.rows.iter().flat_map(|r| r.iter()).collect();
        hash_polys(&refs)
    }

    fn negation_class_key(&self, a: &Ideal) -> u64 {
        let h = self.hash64(a);
        let n = self.hash64(&self.neg_class(a));
        h.min(n) ^ h.max(n).rotate_left(17)
    }

    fn is_negation_representative(&self, a: &Ideal) -> bool {
        // Compare with the negation by the hash order (deterministic, symmetric).
        let h = self.hash64(a);
        let n = self.hash64(&self.neg_class(a));
        h <= n
    }

    fn group_ops(&self) -> u64 {
        self.ops.get()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::highgenus::cantor::{Divisor, HyperellipticCurve};
    use num_bigint::BigUint;
    use rand::rngs::StdRng;
    use rand::SeedableRng;

    /// Mumford `(u, v)` ↔ ideal `(u, y − v)` at `m = 2`.
    fn mumford_to_ideal(c: &SuperellipticCurve, d: &Divisor) -> Ideal {
        let k = &c.field;
        let y_minus_v = vec![d.v.neg(k), Poly::one()];
        c.ideal_from_generators(&[c.elt_poly(&d.u), y_minus_v])
    }

    #[test]
    fn genus_formula_and_construction() {
        let k = Fp::new(7).unwrap();
        let mut rng = StdRng::seed_from_u64(3);
        for g in [1u32, 2, 3, 5, 6, 7, 11, 23] {
            let c = SuperellipticCurve::random_trigonal(k, g, &mut rng).unwrap();
            assert_eq!(c.genus, g);
            assert_eq!(c.m, 3);
        }
        // y^3 = x^4 + 1 over F_13: Picard curve, genus 3.
        let k13 = Fp::new(13).unwrap();
        let c = SuperellipticCurve::from_squarefree(
            k13,
            3,
            Poly::from_coeffs(vec![1, 0, 0, 0, 1], &k13),
        )
        .unwrap();
        assert_eq!(c.genus, 3);
        // y^2 = x^5 + x + 1: genus 2.
        let c = SuperellipticCurve::from_squarefree(
            k13,
            2,
            Poly::from_coeffs(vec![1, 1, 0, 0, 0, 1], &k13),
        )
        .unwrap();
        assert_eq!(c.genus, 2);
        // Bad: gcd(3, 6) ≠ 1.
        assert!(SuperellipticCurve::from_squarefree(
            k13,
            3,
            Poly::from_coeffs(vec![1, 0, 0, 0, 0, 0, 1], &k13)
        )
        .is_err());
    }

    #[test]
    fn m_two_agrees_with_cantor() {
        let mut rng = StdRng::seed_from_u64(4);
        for &(p, g) in &[(23u64, 2u32), (31, 3), (101, 5), (7, 11)] {
            let k = Fp::new(p).unwrap();
            let hc = HyperellipticCurve::random(k, g, &mut rng).unwrap();
            let sc = SuperellipticCurve::from_squarefree(k, 2, hc.f.clone()).unwrap();
            assert_eq!(sc.genus, g);
            for _ in 0..8 {
                let a = hc.random_element(3, &mut rng);
                let b = hc.random_element(3, &mut rng);
                let ia = mumford_to_ideal(&sc, &a);
                let ib = mumford_to_ideal(&sc, &b);
                assert!(
                    sc.is_canonical(&ia),
                    "p={p} g={g}: reduced Mumford is canonical"
                );
                let s = hc.add_divisors(&a, &b);
                let is = sc.add_classes(&ia, &ib);
                assert_eq!(is, mumford_to_ideal(&sc, &s), "p={p} g={g} add");
                let n = hc.neg_divisor(&a);
                assert_eq!(
                    sc.neg_class(&ia),
                    mumford_to_ideal(&sc, &n),
                    "p={p} g={g} neg"
                );
            }
        }
    }

    #[test]
    fn canonical_form_is_class_invariant_and_group_axioms_hold() {
        let mut rng = StdRng::seed_from_u64(5);
        let cases: Vec<(u64, u32, u32)> = vec![
            (7, 3, 5),
            (11, 3, 7),
            (13, 3, 11),
            (5, 3, 23),
            (2, 3, 5),
            (7, 5, 6),
            (23, 11, 5),
        ];
        for (p, m, g) in cases {
            let k = Fp::new(p).unwrap();
            let c = if m == 3 {
                SuperellipticCurve::random_trigonal(k, g, &mut rng).unwrap()
            } else if m == 5 {
                // y^5 = F, deg F = 4: g = (m−1)(s−1)/2 = 4·3/2 = 6.
                SuperellipticCurve::random_superelliptic(k, 5, 4, &mut rng).unwrap()
            } else {
                // Three-point curve y^11 = x (1 − x)^2 over F_23: genus 5.
                let x = Poly::from_coeffs(vec![0, 1], &k);
                let one_minus_x = Poly::from_coeffs(vec![1, p - 1], &k).monic(&k); // (x − 1), same ideal up to unit
                SuperellipticCurve::new(k, 11, vec![(x, 1), (one_minus_x, 2)]).unwrap()
            };
            assert_eq!(c.genus, g, "p={p} m={m}");
            let a = c.random_element(2, &mut rng);
            let b = c.random_element(2, &mut rng);
            let d = c.random_element(2, &mut rng);
            assert!(c.is_canonical(&a));
            assert!(a.degree() <= g as usize);
            // Class invariance: multiply by a principal ideal and re-canonicalise.
            let psi = {
                let mut e = vec![Poly::zero(); m as usize];
                e[0] = Poly::random(2, &k, &mut rng).add(&Poly::x(), &k);
                e[1] = Poly::random(1, &k, &mut rng);
                e
            };
            let shifted = c.mul_ideals(&a, &c.principal(&psi));
            assert_eq!(
                c.canonical(&shifted),
                a,
                "p={p} m={m}: canonical form is class invariant"
            );
            let ab = c.add_classes(&a, &b);
            assert_eq!(ab, c.add_classes(&b, &a), "commutative p={p} m={m}");
            assert_eq!(
                c.add_classes(&ab, &d),
                c.add_classes(&a, &c.add_classes(&b, &d)),
                "associative p={p} m={m}"
            );
            assert!(
                c.add_classes(&a, &c.neg_class(&a)).is_unit(),
                "inverse p={p} m={m}"
            );
            let m1 = BigUint::from(37u32);
            let m2 = BigUint::from(1009u32);
            let lhs = c.scalar_mul(&(&m1 + &m2), &a);
            let rhs = c.add_classes(&c.scalar_mul(&m1, &a), &c.scalar_mul(&m2, &a));
            assert_eq!(lhs, rhs, "distributive p={p} m={m}");
        }
    }

    #[test]
    fn trigonal_group_axioms_at_genus_47_and_131() {
        let mut rng = StdRng::seed_from_u64(8);
        for &(p, g) in &[(7u64, 47u32), (2, 131)] {
            let k = Fp::new(p).unwrap();
            let c = SuperellipticCurve::random_trigonal(k, g, &mut rng).unwrap();
            assert_eq!(c.genus, g);
            let a = c.random_element(3, &mut rng);
            let b = c.random_element(3, &mut rng);
            let d = c.random_element(3, &mut rng);
            assert!(c.is_canonical(&a), "p={p} g={g}");
            let ab = c.add_classes(&a, &b);
            assert_eq!(ab, c.add_classes(&b, &a), "commutative p={p} g={g}");
            assert_eq!(
                c.add_classes(&ab, &d),
                c.add_classes(&a, &c.add_classes(&b, &d)),
                "associative p={p} g={g}"
            );
            assert!(
                c.add_classes(&a, &c.neg_class(&a)).is_unit(),
                "inverse p={p} g={g}"
            );
            let m1 = BigUint::from(5u32);
            let m2 = BigUint::from(12u32);
            let lhs = c.scalar_mul(&(&m1 + &m2), &a);
            let rhs = c.add_classes(&c.scalar_mul(&m1, &a), &c.scalar_mul(&m2, &a));
            assert_eq!(lhs, rhs, "distributive p={p} g={g}");
        }
    }

    #[test]
    fn valuations_recover_place_exponents() {
        let mut rng = StdRng::seed_from_u64(6);
        let k = Fp::new(13).unwrap();
        let c = SuperellipticCurve::random_trigonal(k, 7, &mut rng).unwrap();
        // Build P1^2 · P2 for two distinct unramified degree-1 primes and read the exponents back.
        let mut primes = Vec::new();
        for a in 0..13u64 {
            let pi = Poly::from_coeffs(vec![k.neg(a), 1], &k);
            for (ideal, r) in c.places_above(&pi, &mut rng) {
                if !r.is_zero() || !c.big_f.rem(&pi, &k).is_zero() {
                    primes.push((pi.clone(), r, ideal));
                }
            }
            if primes.len() >= 2 {
                break;
            }
        }
        assert!(primes.len() >= 2, "need two unramified places");
        let (pi1, r1, p1) = &primes[0];
        let (pi2, r2, p2) = &primes[1];
        let prod = c.mul_ideals(&c.mul_ideals(p1, p1), p2);
        let c1 = if pi1 == pi2 { 3 } else { 2 };
        assert_eq!(c.valuation_unramified(&prod, pi1, r1, c1), 2);
        assert_eq!(
            c.valuation_unramified(&prod, pi2, r2, if pi1 == pi2 { 3 } else { 1 }),
            1
        );
        assert_eq!(prod.degree(), 3);
    }
}
