//! **CSIDH** — Commutative Supersingular Isogeny Diffie-Hellman.
//! Castryck, Lange, Martindale, Panny, Renes (ASIACRYPT 2018);
//! projective Edwards-Montgomery codomain formulas of Meyer–Reith
//! (INDOCRYPT 2018).
//!
//! Parameters: a prime `p = 4 · ∏ ℓ_i − 1` (`p ≡ 3 mod 8`) with `{ℓ_i}`
//! small odd primes.  The base curve `E_0: y² = x³ + x` (`A = 0`) over
//! `F_p` is supersingular with `#E(F_p) = p + 1` and `F_p`-rational
//! endomorphism ring `Z[√−p]`.
//!
//! ## Optimisations implemented
//!
//! 1. **Single-word Montgomery `F_p` arithmetic** (`FastField`, `p < 2^63`)
//!    eliminating hardware integer divisions inside the ladder and Vélu steps.
//! 2. **Exact projective `x`-only Montgomery ladder & Meyer–Reith Vélu**:
//!    represents the curve projectively in twisted-Edwards constants
//!    `(a_ed : d_ed) = (A + 2C : A − 2C)` across the entire action, paying
//!    **zero field inversions** inside the isogeny walk and **one** field
//!    inversion at the very end (`A = 2(a_ed + d_ed)/(a_ed − d_ed)`).
//! 3. **Twist-aware quadratic-character sampling**: points with
//!    `χ(C·x·(C·x² + A·x + C)) = +1` lie on `E_A(F_p)` (`+1` exponents),
//!    while `−1` lies on the quadratic twist `E_A^t(F_p)` (`−1` exponents),
//!    realising the exact inverse ideal action `[ℓ_i]⁻¹` and exact DH
//!    commutativity `sk_A · (sk_B · E_0) == sk_B · (sk_A · E_0)`.
//! 4. **Batched cofactor clearing + divide-and-conquer remainder tree**:
//!    clears the dead cofactor `(p + 1) / ∏_{i ∈ S} ℓ_i` once per batch,
//!    pushes the torsion point through each evaluated isogeny, and exposes
//!    [`cofactor_remainder_tree`] (`O(k log k)` vs `O(k²)` scalar mults)
//!    for simultaneous multi-prime torsion extraction.

use crate::cryptanalysis::bsgs_fast::FastField;
use rand::{rngs::OsRng, Rng};

/// Canonical toy CSIDH base-field prime: `p = 4 · 3 · 5 · 7 − 1 = 419` (`419 ≡ 3 mod 8`).
pub const P: u64 = 419;

/// Small primes for the canonical `p = 419` class-group action.
pub const ELL: [u64; 3] = [3, 5, 7];

/// Private-key coefficient range: `e_i ∈ [−M, M]`.
pub const M: i32 = 3;

/// 56-bit supersingular CSIDH prime `p = 4 · ∏ ELL_56 − 1 ≡ 3 (mod 8)`.
pub const P_56: u64 = 37_118_532_150_319_619;

/// Thirteen odd primes dividing `P_56 + 1`.
pub const ELL_56: [u64; 13] = [3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 61];

/// 60-bit supersingular CSIDH prime `p = 4 · ∏ ELL_60_LARGE − 1 ≡ 3 (mod 8)`
/// carrying primes up to `ℓ = 587` to exercise `√élu` (`velu_sqrt_proj`).
pub const P_60_LARGE: u64 = 673_751_282_656_135_979;

/// Nine odd primes dividing `P_60_LARGE + 1` (including `89..587`).
pub const ELL_60_LARGE: [u64; 9] = [3, 5, 89, 107, 131, 199, 251, 307, 587];

/// Degree threshold at and above which [`CsidhParams::action`] dispatches to
/// projective `√élu` ([`velu_sqrt_proj`]) instead of linear Meyer–Reith Vélu.
pub const VELU_SQRT_MIN_ELL: u64 = 89;

// ── Field helpers for P = 419 compatibility ───────────────────────

#[inline(always)]
fn fp_add(a: u64, b: u64) -> u64 {
    (a + b) % P
}
#[inline(always)]
fn fp_sub(a: u64, b: u64) -> u64 {
    ((a + P) - (b % P)) % P
}
#[inline(always)]
fn fp_mul(a: u64, b: u64) -> u64 {
    (a * b) % P
}
#[inline(always)]
fn fp_neg(a: u64) -> u64 {
    (P - (a % P)) % P
}
fn fp_inv(a: u64) -> Option<u64> {
    let a = a % P;
    if a == 0 {
        return None;
    }
    let (mut old_r, mut r) = (a, P);
    let (mut old_s, mut s) = (1i64, 0i64);
    while r != 0 {
        let q = old_r / r;
        (old_r, r) = (r, old_r - q * r);
        (old_s, s) = (s, old_s - (q as i64) * s);
    }
    (old_r == 1).then(|| old_s.rem_euclid(P as i64) as u64)
}
fn fp_sqrt(a: u64) -> Option<u64> {
    if a % P == 0 {
        return Some(0);
    }
    let mut result = 1u64;
    let mut base = a % P;
    let mut e = (P + 1) / 4;
    while e > 0 {
        if e & 1 == 1 {
            result = fp_mul(result, base);
        }
        base = fp_mul(base, base);
        e >>= 1;
    }
    (fp_mul(result, result) == a % P).then_some(result)
}

// ── Projective x-only Montgomery arithmetic over FastField ────────

/// Projective point `(X : Z)` on `E_{A/C}` (`Z = 0` is `O`).
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct ProjX {
    pub x: u64,
    pub z: u64,
}

impl ProjX {
    #[inline(always)]
    pub fn infinity(ff: &FastField) -> Self {
        Self { x: ff.one(), z: 0 }
    }
    #[inline(always)]
    pub fn is_infinity(self) -> bool {
        self.z == 0
    }
}

/// Projective Montgomery curve held in Edwards constants `(a_ed : d_ed)`
/// where `a_ed = A + 2C`, `d_ed = A − 2C`, so `A24 = a_ed` and `C24 = a_ed − d_ed`.
#[derive(Clone, Copy, Debug)]
pub struct ProjCurve {
    pub a_ed: u64,
    pub d_ed: u64,
}

impl ProjCurve {
    #[inline]
    pub fn from_affine_a(a: u64, ff: &FastField) -> Self {
        let am = ff.to_mont(a);
        let two = ff.dbl(ff.one());
        Self {
            a_ed: ff.add(am, two),
            d_ed: ff.sub(am, two),
        }
    }

    #[inline]
    pub fn to_affine_a(self, ff: &FastField) -> u64 {
        let num = ff.dbl(ff.add(self.a_ed, self.d_ed));
        let den = ff.sub(self.a_ed, self.d_ed);
        ff.from_mont(ff.mul(num, ff.inv(den)))
    }
}

#[inline(always)]
fn xdbl(p: ProjX, c: ProjCurve, ff: &FastField) -> ProjX {
    let t0 = ff.sqr(ff.add(p.x, p.z));
    let t1 = ff.sqr(ff.sub(p.x, p.z));
    let t2 = ff.sub(t0, t1);
    let c24 = ff.sub(c.a_ed, c.d_ed);
    let t1c = ff.mul(t1, c24);
    let x2 = ff.mul(t0, t1c);
    let z2 = ff.mul(t2, ff.add(t1c, ff.mul(c.a_ed, t2)));
    ProjX { x: x2, z: z2 }
}

#[inline(always)]
fn xadd(p: ProjX, q: ProjX, pmq: ProjX, ff: &FastField) -> ProjX {
    let t0 = ff.mul(ff.add(p.x, p.z), ff.sub(q.x, q.z));
    let t1 = ff.mul(ff.sub(p.x, p.z), ff.add(q.x, q.z));
    let x3 = ff.mul(pmq.z, ff.sqr(ff.add(t0, t1)));
    let z3 = ff.mul(pmq.x, ff.sqr(ff.sub(t0, t1)));
    ProjX { x: x3, z: z3 }
}

/// Montgomery `XZ` differential ladder computing `[k]P` on `c`.
#[inline]
pub fn xmul(mut k: u64, p: ProjX, c: ProjCurve, ff: &FastField) -> ProjX {
    if k == 0 || p.z == 0 {
        return ProjX::infinity(ff);
    }
    if k == 1 {
        return p;
    }
    let mut r0 = ProjX::infinity(ff);
    let mut r1 = p;
    let top = 63 - k.leading_zeros();
    for bit in (0..=top).rev() {
        if (k >> bit) & 1 == 1 {
            r0 = xadd(r0, r1, p, ff);
            r1 = xdbl(r1, c, ff);
        } else {
            r1 = xadd(r0, r1, p, ff);
            r0 = xdbl(r0, c, ff);
        }
        let _ = &mut k;
    }
    r0
}

/// Divide-and-conquer remainder tree computing `[(∏_{j ≠ i} ℓ_j)] P` for every
/// `i ∈ 0..ells.len()` in `O(k log k)` scalar multiplications instead of `k`
/// independent `[(∏_{j ≠ i} ℓ_j)]` ladders (`O(k²)`).
pub fn cofactor_remainder_tree(
    root: ProjX,
    c: ProjCurve,
    ells: &[u64],
    ff: &FastField,
) -> Vec<ProjX> {
    fn prod_slice(s: &[u64]) -> u64 {
        s.iter().copied().product()
    }
    fn rec(node: ProjX, c: ProjCurve, ells: &[u64], ff: &FastField, out: &mut Vec<ProjX>) {
        match ells.len() {
            0 => {}
            1 => out.push(node),
            n => {
                let mid = n / 2;
                let (left, right) = ells.split_at(mid);
                let p_left = prod_slice(left);
                let p_right = prod_slice(right);
                let node_for_left = xmul(p_right, node, c, ff);
                let node_for_right = xmul(p_left, node, c, ff);
                rec(node_for_left, c, left, ff, out);
                rec(node_for_right, c, right, ff, out);
            }
        }
    }
    let mut out = Vec::with_capacity(ells.len());
    rec(root, c, ells, ff, &mut out);
    out
}

/// Exact Meyer–Reith projective `ℓ`-isogeny codomain and simultaneous point
/// evaluation from an order-`ℓ` kernel generator `k1` (`ℓ ≥ 3` odd).
#[inline]
pub fn velu_isogeny_proj(
    c: ProjCurve,
    k1: ProjX,
    ell: u64,
    push: &mut [ProjX],
    ff: &FastField,
) -> ProjCurve {
    let s = ((ell - 1) / 2) as usize;
    const STACK_S: usize = 64;
    let mut ks_stack = [ProjX { x: 0, z: 0 }; STACK_S];
    let mut ks_heap: Vec<ProjX>;
    let ks: &mut [ProjX] = if s <= STACK_S {
        &mut ks_stack[..s]
    } else {
        ks_heap = vec![ProjX { x: 0, z: 0 }; s];
        &mut ks_heap[..]
    };

    ks[0] = k1;
    if s >= 2 {
        ks[1] = xdbl(k1, c, ff);
    }
    for j in 2..s {
        ks[j] = xadd(ks[j - 1], k1, ks[j - 2], ff);
    }

    let mut prod_plus = ff.one();
    let mut prod_minus = ff.one();
    for kj in ks.iter() {
        let kp = ff.add(kj.x, kj.z);
        let km = ff.sub(kj.x, kj.z);
        prod_plus = ff.mul(prod_plus, kp);
        prod_minus = ff.mul(prod_minus, km);
    }

    // Push auxiliary torsion points through φ_ℓ.
    for q in push.iter_mut() {
        if q.z == 0 {
            continue;
        }
        let qm = ff.sub(q.x, q.z);
        let qp = ff.add(q.x, q.z);
        let mut acc_x = ff.one();
        let mut acc_z = ff.one();
        for kj in ks.iter() {
            let kp = ff.add(kj.x, kj.z);
            let km = ff.sub(kj.x, kj.z);
            let t0 = ff.mul(qm, kp);
            let t1 = ff.mul(qp, km);
            acc_x = ff.mul(acc_x, ff.add(t0, t1));
            acc_z = ff.mul(acc_z, ff.sub(t0, t1));
        }
        q.x = ff.mul(q.x, ff.sqr(acc_x));
        q.z = ff.mul(q.z, ff.sqr(acc_z));
    }

    // (prod_plus)^8 and (prod_minus)^8 via 3 squarings each.
    let pp8 = ff.sqr(ff.sqr(ff.sqr(prod_plus)));
    let pm8 = ff.sqr(ff.sqr(ff.sqr(prod_minus)));
    ProjCurve {
        a_ed: ff.mul(ff.pow(c.a_ed, ell), pp8),
        d_ed: ff.mul(ff.pow(c.d_ed, ell), pm8),
    }
}

// ── Projective x-only √élu (Bernstein–De Feo–Leroux–Smith 2020) ──

fn poly_mul_fp(a: &[u64], b: &[u64], ff: &FastField) -> Vec<u64> {
    if a.is_empty() || b.is_empty() {
        return Vec::new();
    }
    let na = a.len();
    let nb = b.len();
    if na.min(nb) < 8 {
        let mut out = vec![0u64; na + nb - 1];
        for (i, &ai) in a.iter().enumerate() {
            if ai == 0 {
                continue;
            }
            for (j, &bj) in b.iter().enumerate() {
                out[i + j] = ff.add(out[i + j], ff.mul(ai, bj));
            }
        }
        return out;
    }
    let m = na.max(nb) / 2;
    let (a0, a1) = a.split_at(m.min(na));
    let (b0, b1) = b.split_at(m.min(nb));
    let z0 = poly_mul_fp(a0, b0, ff);
    let z2 = poly_mul_fp(a1, b1, ff);
    let mut asum = vec![0u64; a0.len().max(a1.len())];
    for (i, &v) in a0.iter().enumerate() {
        asum[i] = v;
    }
    for (i, &v) in a1.iter().enumerate() {
        asum[i] = ff.add(asum[i], v);
    }
    let mut bsum = vec![0u64; b0.len().max(b1.len())];
    for (i, &v) in b0.iter().enumerate() {
        bsum[i] = v;
    }
    for (i, &v) in b1.iter().enumerate() {
        bsum[i] = ff.add(bsum[i], v);
    }
    let mut z1 = poly_mul_fp(&asum, &bsum, ff);
    for (i, &v) in z0.iter().enumerate() {
        z1[i] = ff.sub(z1[i], v);
    }
    for (i, &v) in z2.iter().enumerate() {
        z1[i] = ff.sub(z1[i], v);
    }
    let mut out = vec![0u64; na + nb - 1];
    for (i, &v) in z0.iter().enumerate() {
        out[i] = ff.add(out[i], v);
    }
    for (i, &v) in z1.iter().enumerate() {
        if i + m < out.len() {
            out[i + m] = ff.add(out[i + m], v);
        }
    }
    for (i, &v) in z2.iter().enumerate() {
        if i + 2 * m < out.len() {
            out[i + 2 * m] = ff.add(out[i + 2 * m], v);
        }
    }
    out
}

/// Fixed-degree pseudo-remainder of `a` (`deg = a.len() - 1`) modulo `m`
/// (`deg = m.len() - 1 >= 1`), scaling uniformly by `m_lead^(deg_a - deg_m + 1)`
/// regardless of zero leading coefficients in `a` so paired projective
/// numerators and denominators pick up identical projective scalars.
#[inline]
fn poly_pseudo_rem_fixed(a: &[u64], m: &[u64], ff: &FastField) -> Vec<u64> {
    let dm = m.len() - 1;
    debug_assert!(dm >= 1);
    if a.len() <= dm {
        let mut r = vec![0u64; dm];
        r[..a.len()].copy_from_slice(a);
        return r;
    }
    let mut work = a.to_vec();
    let lead = m[dm];
    for deg in (dm..work.len()).rev() {
        let top = work[deg];
        let shift = deg - dm;
        for k in 0..deg {
            work[k] = ff.mul(work[k], lead);
        }
        if top != 0 {
            for k in 0..dm {
                work[shift + k] = ff.sub(work[shift + k], ff.mul(top, m[k]));
            }
        }
    }
    work.truncate(dm);
    work
}

enum SubprodTree {
    Leaf(Vec<u64>),
    Node {
        poly: Vec<u64>,
        left: Box<SubprodTree>,
        right: Box<SubprodTree>,
    },
}

impl SubprodTree {
    fn poly(&self) -> &[u64] {
        match self {
            SubprodTree::Leaf(p) => p,
            SubprodTree::Node { poly, .. } => poly,
        }
    }

    fn build_giant(giants: &[ProjX], ff: &FastField) -> Self {
        debug_assert!(!giants.is_empty());
        if giants.len() == 1 {
            let g = giants[0];
            // Z_G * X - X_G
            return SubprodTree::Leaf(vec![ff.neg(g.x), g.z]);
        }
        let mid = giants.len() / 2;
        let left = Box::new(Self::build_giant(&giants[..mid], ff));
        let right = Box::new(Self::build_giant(&giants[mid..], ff));
        let poly = poly_mul_fp(left.poly(), right.poly(), ff);
        SubprodTree::Node { poly, left, right }
    }

    fn eval_pair_product(&self, num: &[u64], den: &[u64], ff: &FastField) -> (u64, u64) {
        let r_num = poly_pseudo_rem_fixed(num, self.poly(), ff);
        let r_den = poly_pseudo_rem_fixed(den, self.poly(), ff);
        match self {
            SubprodTree::Leaf(_) => (r_num[0], r_den[0]),
            SubprodTree::Node { left, right, .. } => {
                let (ln, ld) = left.eval_pair_product(&r_num, &r_den, ff);
                let (rn, rd) = right.eval_pair_product(&r_num, &r_den, ff);
                (ff.mul(ln, rn), ff.mul(ld, rd))
            }
        }
    }
}

fn product_tree_quads(quads: &[[u64; 3]], ff: &FastField) -> Vec<u64> {
    match quads.len() {
        0 => vec![ff.one()],
        1 => quads[0].to_vec(),
        n => {
            let mid = n / 2;
            let l = product_tree_quads(&quads[..mid], ff);
            let r = product_tree_quads(&quads[mid..], ff);
            poly_mul_fp(&l, &r, ff)
        }
    }
}

/// Projective `x`-only **√élu** (`Õ(√ℓ)` baby-step giant-step isogeny codomain
/// and point evaluation, Bernstein–De Feo–Leroux–Smith 2020) over `FastField`
/// with **zero field inversions**.
///
/// Produces a projectively identical codomain `(a_ed : d_ed)` and pushed points
/// `(X' : Z')` to [`velu_isogeny_proj`] for every odd prime `ℓ ≥ 3`.
pub fn velu_sqrt_proj(
    c: ProjCurve,
    k1: ProjX,
    ell: u64,
    push: &mut [ProjX],
    ff: &FastField,
) -> ProjCurve {
    if ell < 17 {
        return velu_isogeny_proj(c, k1, ell, push, ff);
    }
    let m = ((ell - 1) / 2) as usize;
    let b = (((ell - 1) / 4) as f64).sqrt() as usize;
    if b < 2 {
        return velu_isogeny_proj(c, k1, ell, push, ff);
    }
    let g = ((ell - 1) as usize) / (4 * b);
    if g < 2 {
        return velu_isogeny_proj(c, k1, ell, push, ff);
    }

    // Baby steps: B_j = [2j + 1]K for j = 0..b.
    let k2 = xdbl(k1, c, ff);
    let mut baby = Vec::with_capacity(b);
    baby.push(k1);
    baby.push(xadd(k2, k1, k1, ff));
    for j in 2..b {
        let next = xadd(baby[j - 1], k2, baby[j - 2], ff);
        baby.push(next);
    }

    // Giant steps: G_i = [(4i + 2)b]K for i = 0..g.
    let k2b = xmul((2 * b) as u64, k1, c, ff);
    let k4b = xdbl(k2b, c, ff);
    let mut giant = Vec::with_capacity(g);
    giant.push(k2b);
    giant.push(xadd(k4b, k2b, k2b, ff));
    for i in 2..g {
        let next = xadd(giant[i - 1], k4b, giant[i - 2], ff);
        giant.push(next);
    }

    // Leftover odd multiples: {4bg + 1, 4bg + 3, ..., 2m - 1}.
    let rem_cnt = m - 2 * b * g;
    let mut rem_pts = Vec::with_capacity(rem_cnt);
    if rem_cnt >= 1 {
        let s0 = (4 * b * g + 1) as u64;
        let r0 = xmul(s0, k1, c, ff);
        rem_pts.push(r0);
        if rem_cnt >= 2 {
            let r_prev = xmul(s0 - 2, k1, c, ff);
            let r1 = xadd(r0, k2, r_prev, ff);
            rem_pts.push(r1);
            for idx in 2..rem_cnt {
                let next = xadd(rem_pts[idx - 1], k2, rem_pts[idx - 2], ff);
                rem_pts.push(next);
            }
        }
    }

    // Precompute baby biquadratic forms F_0, F_1, F_2 for each baby point B_j.
    let a_c = ff.dbl(ff.add(c.a_ed, c.d_ed));
    let c_c = ff.sub(c.a_ed, c.d_ed);
    let mut f0s = Vec::with_capacity(b);
    let mut f1s = Vec::with_capacity(b);
    let mut f2s = Vec::with_capacity(b);
    for bj in &baby {
        let xb2 = ff.sqr(bj.x);
        let zb2 = ff.sqr(bj.z);
        let two_xbzb = ff.dbl(ff.mul(bj.x, bj.z));
        let c_xb2 = ff.mul(c_c, xb2);
        let c_zb2 = ff.mul(c_c, zb2);
        let c_2xbzb = ff.mul(c_c, two_xbzb);
        let neg_c_2xbzb = ff.neg(c_2xbzb);
        let f1_mid = ff.neg(ff.dbl(ff.add(ff.add(c_xb2, c_zb2), ff.mul(a_c, two_xbzb))));
        f0s.push([c_xb2, neg_c_2xbzb, c_zb2]);
        f1s.push([neg_c_2xbzb, f1_mid, neg_c_2xbzb]);
        f2s.push([c_zb2, neg_c_2xbzb, c_xb2]);
    }

    let giant_tree = SubprodTree::build_giant(&giant, ff);

    // 1. Meyer–Reith codomain products:
    //    prod_plus  <- (1, -1, 1): F_0 - F_1 + F_2
    //    prod_minus <- (1, +1, 1): F_0 + F_1 + F_2
    let mut q_plus = Vec::with_capacity(b);
    let mut q_minus = Vec::with_capacity(b);
    for j in 0..b {
        let s02_0 = ff.add(f0s[j][0], f2s[j][0]);
        let s02_1 = ff.add(f0s[j][1], f2s[j][1]);
        let s02_2 = ff.add(f0s[j][2], f2s[j][2]);
        q_plus.push([
            ff.sub(s02_0, f1s[j][0]),
            ff.sub(s02_1, f1s[j][1]),
            ff.sub(s02_2, f1s[j][2]),
        ]);
        q_minus.push([
            ff.add(s02_0, f1s[j][0]),
            ff.add(s02_1, f1s[j][1]),
            ff.add(s02_2, f1s[j][2]),
        ]);
    }
    let p_plus = product_tree_quads(&q_plus, ff);
    let p_minus = product_tree_quads(&q_minus, ff);
    let (mut prod_plus, mut prod_minus) = giant_tree.eval_pair_product(&p_plus, &p_minus, ff);
    for rj in &rem_pts {
        prod_plus = ff.mul(prod_plus, ff.add(rj.x, rj.z));
        prod_minus = ff.mul(prod_minus, ff.sub(rj.x, rj.z));
    }

    // 2. Push auxiliary torsion points:
    //    acc_x <- Z^2 F_0 + X Z F_1 + X^2 F_2
    //    acc_z <- X^2 F_0 + X Z F_1 + Z^2 F_2
    let mut q_num = vec![[0u64; 3]; b];
    let mut q_den = vec![[0u64; 3]; b];
    for q in push.iter_mut() {
        if q.z == 0 {
            continue;
        }
        let x2 = ff.sqr(q.x);
        let z2 = ff.sqr(q.z);
        let xz = ff.mul(q.x, q.z);
        for j in 0..b {
            for k in 0..3 {
                let mid = ff.mul(xz, f1s[j][k]);
                q_num[j][k] = ff.add(ff.add(ff.mul(z2, f0s[j][k]), mid), ff.mul(x2, f2s[j][k]));
                q_den[j][k] = ff.add(ff.add(ff.mul(x2, f0s[j][k]), mid), ff.mul(z2, f2s[j][k]));
            }
        }
        let p_num = product_tree_quads(&q_num, ff);
        let p_den = product_tree_quads(&q_den, ff);
        let (mut acc_x, mut acc_z) = giant_tree.eval_pair_product(&p_num, &p_den, ff);

        let qm = ff.sub(q.x, q.z);
        let qp = ff.add(q.x, q.z);
        for rj in &rem_pts {
            let kp = ff.add(rj.x, rj.z);
            let km = ff.sub(rj.x, rj.z);
            let t0 = ff.mul(qm, kp);
            let t1 = ff.mul(qp, km);
            acc_x = ff.mul(acc_x, ff.add(t0, t1));
            acc_z = ff.mul(acc_z, ff.sub(t0, t1));
        }
        q.x = ff.mul(q.x, ff.sqr(acc_x));
        q.z = ff.mul(q.z, ff.sqr(acc_z));
    }

    let pp8 = ff.sqr(ff.sqr(ff.sqr(prod_plus)));
    let pm8 = ff.sqr(ff.sqr(ff.sqr(prod_minus)));
    ProjCurve {
        a_ed: ff.mul(ff.pow(c.a_ed, ell), pp8),
        d_ed: ff.mul(ff.pow(c.d_ed, ell), pm8),
    }
}

#[inline]
fn velu_auto_proj(
    c: ProjCurve,
    k1: ProjX,
    ell: u64,
    push: &mut [ProjX],
    ff: &FastField,
) -> ProjCurve {
    if ell >= VELU_SQRT_MIN_ELL {
        velu_sqrt_proj(c, k1, ell, push, ff)
    } else {
        velu_isogeny_proj(c, k1, ell, push, ff)
    }
}

// ── Parameterised CSIDH engine ────────────────────────────────────

/// Parameter set for a single-word (`p < 2^63`) CSIDH instance.
#[derive(Clone, Debug)]
pub struct CsidhParams<'a> {
    pub p: u64,
    pub ells: &'a [u64],
    pub bound: i32,
    ff: FastField,
}

impl<'a> CsidhParams<'a> {
    pub fn new(p: u64, ells: &'a [u64], bound: i32) -> Self {
        let ff = FastField::new(p).expect("CSIDH prime must be odd and < 2^63");
        Self { p, ells, bound, ff }
    }

    /// Canonical `p = 419` instance (`ELL = [3, 5, 7]`).
    pub fn toy_419() -> CsidhParams<'static> {
        CsidhParams::new(P, &ELL, M)
    }

    /// 56-bit supersingular CSIDH instance (`13` odd primes, `|Cl| ≈ 2^28`).
    pub fn csidh_56() -> CsidhParams<'static> {
        CsidhParams::new(P_56, &ELL_56, 5)
    }

    /// 60-bit supersingular CSIDH instance with large odd prime degrees up to
    /// `ℓ = 587` (`ELL_60_LARGE`), exercising `√élu` + SIMBA + remainder trees.
    pub fn csidh_60_large() -> CsidhParams<'static> {
        CsidhParams::new(P_60_LARGE, &ELL_60_LARGE, 3)
    }

    #[inline]
    pub fn field(&self) -> &FastField {
        &self.ff
    }

    /// Evaluate the exact commutative CM class-group action `[e] · E_A` using
    /// projective Edwards-Montgomery arithmetic, twist-aware sampling, and
    /// batched cofactor clearing with pushed torsion points.
    pub fn action(&self, start_a: u64, secret: &[i32]) -> u64 {
        assert_eq!(
            secret.len(),
            self.ells.len(),
            "secret length must match ells"
        );
        if secret.iter().all(|&e| e == 0) {
            return start_a % self.p;
        }
        let ff = &self.ff;
        let p = self.p;
        let mut cur = ProjCurve::from_affine_a(start_a % p, ff);
        let mut rem: [i32; 32] = [0; 32];
        assert!(secret.len() <= 32);
        rem[..secret.len()].copy_from_slice(secret);
        let rem = &mut rem[..secret.len()];

        let exp_leg = (p - 1) / 2;
        let mut x_seed = 2u64;

        while rem.iter().any(|&e| e != 0) {
            let need_pos = rem.iter().any(|&e| e > 0);
            let need_neg = rem.iter().any(|&e| e < 0);

            // Deterministic x-coordinate draw in F_p \ {0}.
            let xm = ff.to_mont(x_seed);
            x_seed += 1;
            if x_seed >= p {
                x_seed = 2;
            }

            // Projective curve equation C²(x³ + (A/C)x² + x) = C·x·(C·x² + A·x + C),
            // where A = 2(a_ed + d_ed), C = 4⁻¹·4(a_ed − d_ed) — up to the common
            // factor 2: A_scaled = a_ed + d_ed, C_scaled = (a_ed − d_ed)/2, or
            // simply A' = 2(a_ed + d_ed), C' = a_ed − d_ed (since C'² > 0 is a square!).
            let a_proj = ff.dbl(ff.add(cur.a_ed, cur.d_ed));
            let c_proj = ff.sub(cur.a_ed, cur.d_ed);
            let inner = ff.add(
                ff.add(ff.mul(c_proj, ff.sqr(xm)), ff.mul(a_proj, xm)),
                c_proj,
            );
            let rhs = ff.mul(ff.mul(c_proj, xm), inner);
            if rhs == 0 {
                continue;
            }
            let leg_val = ff.pow(rhs, exp_leg);
            let sign: i32 = if leg_val == ff.one() { 1 } else { -1 };
            if (sign == 1 && !need_pos) || (sign == -1 && !need_neg) {
                continue;
            }

            // Gather all active primes matching `sign`.
            let mut active = [0usize; 32];
            let mut k_cnt = 0usize;
            let mut k_prod: u64 = 1;
            for (i, &e) in rem.iter().enumerate() {
                if (sign == 1 && e > 0) || (sign == -1 && e < 0) {
                    active[k_cnt] = i;
                    k_cnt += 1;
                    k_prod *= self.ells[i];
                }
            }

            let mut q = xmul((p + 1) / k_prod, ProjX { x: xm, z: ff.one() }, cur, ff);
            for pos in 0..k_cnt {
                if q.is_infinity() {
                    break;
                }
                let idx = active[pos];
                let ell = self.ells[idx];
                let cofactor_step = k_prod / ell;
                let ker = xmul(cofactor_step, q, cur, ff);
                k_prod = cofactor_step;
                if !ker.is_infinity() {
                    if pos + 1 < k_cnt {
                        let mut push = [q];
                        cur = velu_auto_proj(cur, ker, ell, &mut push, ff);
                        q = push[0];
                    } else {
                        cur = velu_auto_proj(cur, ker, ell, &mut [], ff);
                    }
                    rem[idx] -= sign;
                }
            }
        }

        cur.to_affine_a(ff)
    }

    /// Naive reference action: clears the full `(p + 1) / ℓ_i` cofactor
    /// independently for every single exponent unit without batching or
    /// remainder-tree sharing.  Used to verify bit-exact equivalence and
    /// benchmark the SIMBA / cofactor-tree speedup.
    pub fn action_naive_sequential(&self, start_a: u64, secret: &[i32]) -> u64 {
        assert_eq!(secret.len(), self.ells.len());
        let ff = &self.ff;
        let p = self.p;
        let exp_leg = (p - 1) / 2;
        let mut cur_a = start_a % p;

        for (i, &exp) in secret.iter().enumerate() {
            let ell = self.ells[i];
            let sign = exp.signum();
            for _ in 0..exp.unsigned_abs() {
                let cur = ProjCurve::from_affine_a(cur_a, ff);
                let a_proj = ff.dbl(ff.add(cur.a_ed, cur.d_ed));
                let c_proj = ff.sub(cur.a_ed, cur.d_ed);
                let mut x_cand = 2u64;
                loop {
                    let xm = ff.to_mont(x_cand);
                    x_cand += 1;
                    let inner = ff.add(
                        ff.add(ff.mul(c_proj, ff.sqr(xm)), ff.mul(a_proj, xm)),
                        c_proj,
                    );
                    let rhs = ff.mul(ff.mul(c_proj, xm), inner);
                    if rhs == 0 {
                        continue;
                    }
                    let leg = if ff.pow(rhs, exp_leg) == ff.one() {
                        1
                    } else {
                        -1
                    };
                    if leg != sign {
                        continue;
                    }
                    let ker = xmul((p + 1) / ell, ProjX { x: xm, z: ff.one() }, cur, ff);
                    if !ker.is_infinity() {
                        let next = velu_isogeny_proj(cur, ker, ell, &mut [], ff);
                        cur_a = next.to_affine_a(ff);
                        break;
                    }
                }
            }
        }
        cur_a
    }
}

// ── Montgomery curve: By² = x³ + Ax² + x  (with B = 1 always) ────

#[derive(Clone, Debug, Copy, PartialEq, Eq)]
pub struct MontCurve {
    pub a: u64,
}

#[derive(Clone, Debug, Copy, PartialEq, Eq)]
pub enum MontPoint {
    Infinity,
    Affine { x: u64, y: u64 },
}

impl MontCurve {
    pub fn base() -> Self {
        Self { a: 0 }
    }

    /// Check whether `(x, y)` is on the curve `y² = x³ + Ax² + x`.
    pub fn is_on_curve(&self, p: &MontPoint) -> bool {
        match p {
            MontPoint::Infinity => true,
            MontPoint::Affine { x, y } => {
                let lhs = fp_mul(*y, *y);
                let x2 = fp_mul(*x, *x);
                let x3 = fp_mul(x2, *x);
                let ax2 = fp_mul(self.a, x2);
                let rhs = fp_add(fp_add(x3, ax2), *x);
                lhs == rhs
            }
        }
    }

    /// Enumerate all `(x, y)` on the curve (`p = 419`).
    pub fn all_points(&self) -> Vec<MontPoint> {
        let mut out = vec![MontPoint::Infinity];
        for x in 0..P {
            let x2 = fp_mul(x, x);
            let rhs = fp_add(fp_add(fp_mul(x2, x), fp_mul(self.a, x2)), x);
            if let Some(y) = fp_sqrt(rhs) {
                out.push(MontPoint::Affine { x, y });
                if y != 0 {
                    out.push(MontPoint::Affine { x, y: fp_neg(y) });
                }
            }
        }
        out
    }

    /// Point addition on `y² = x³ + Ax² + x` over `F_419`.
    pub fn add(&self, p: &MontPoint, q: &MontPoint) -> MontPoint {
        match (p, q) {
            (MontPoint::Infinity, other) | (other, MontPoint::Infinity) => *other,
            (MontPoint::Affine { x: x1, y: y1 }, MontPoint::Affine { x: x2, y: y2 }) => {
                if x1 == x2 {
                    if fp_add(*y1, *y2) == 0 {
                        return MontPoint::Infinity;
                    }
                    return self.double(p);
                }
                let lambda = fp_mul(fp_sub(*y2, *y1), fp_inv(fp_sub(*x2, *x1)).unwrap());
                let lambda2 = fp_mul(lambda, lambda);
                let x3 = fp_sub(fp_sub(fp_sub(lambda2, self.a), *x1), *x2);
                let y3 = fp_sub(fp_mul(lambda, fp_sub(*x1, x3)), *y1);
                MontPoint::Affine { x: x3, y: y3 }
            }
        }
    }

    pub fn double(&self, p: &MontPoint) -> MontPoint {
        match p {
            MontPoint::Infinity => MontPoint::Infinity,
            MontPoint::Affine { x, y } => {
                if *y == 0 {
                    return MontPoint::Infinity;
                }
                let two_y_inv = fp_inv(fp_mul(2, *y)).unwrap();
                let three_x2 = fp_mul(3, fp_mul(*x, *x));
                let two_ax = fp_mul(2, fp_mul(self.a, *x));
                let lambda = fp_mul(fp_add(fp_add(three_x2, two_ax), 1), two_y_inv);
                let lambda2 = fp_mul(lambda, lambda);
                let x3 = fp_sub(fp_sub(fp_sub(lambda2, self.a), *x), *x);
                let y3 = fp_sub(fp_mul(lambda, fp_sub(*x, x3)), *y);
                MontPoint::Affine { x: x3, y: y3 }
            }
        }
    }

    pub fn scalar_mul(&self, p: &MontPoint, k: u64) -> MontPoint {
        let mut result = MontPoint::Infinity;
        let mut addend = *p;
        let mut e = k;
        while e > 0 {
            if e & 1 == 1 {
                result = self.add(&result, &addend);
            }
            addend = self.double(&addend);
            e >>= 1;
        }
        result
    }

    /// Find a point on `E_A(F_p)` of exact odd order `ell` via `x`-only
    /// Montgomery cofactor multiplication (`O(log p)` instead of `O(p)`).
    pub fn find_point_of_order(&self, ell: u64) -> Option<MontPoint> {
        if !(P + 1).is_multiple_of(ell) {
            return None;
        }
        let ff = FastField::new(P)?;
        let cur = ProjCurve::from_affine_a(self.a % P, &ff);
        let cofactor = (P + 1) / ell;
        for x in 2..P {
            let x2 = fp_mul(x, x);
            let rhs = fp_add(fp_add(fp_mul(x2, x), fp_mul(self.a, x2)), x);
            if rhs == 0 || fp_sqrt(rhs).is_none() {
                continue;
            }
            let ker = xmul(
                cofactor,
                ProjX {
                    x: ff.to_mont(x),
                    z: ff.one(),
                },
                cur,
                &ff,
            );
            if !ker.is_infinity() {
                let kx = ff.from_mont(ff.mul(ker.x, ff.inv(ker.z)));
                let kx2 = fp_mul(kx, kx);
                let krhs = fp_add(fp_add(fp_mul(kx2, kx), fp_mul(self.a, kx2)), kx);
                let ky = fp_sqrt(krhs)?;
                return Some(MontPoint::Affine { x: kx, y: ky });
            }
        }
        None
    }

    /// Find an `x`-only representative `(x, 0)` on the **quadratic twist**
    /// `E_A^t(F_p)` of exact order `ell` (`x³ + Ax² + x` a non-square).
    pub fn find_twist_point_of_order(&self, ell: u64) -> Option<MontPoint> {
        if !(P + 1).is_multiple_of(ell) {
            return None;
        }
        let ff = FastField::new(P)?;
        let cur = ProjCurve::from_affine_a(self.a % P, &ff);
        let cofactor = (P + 1) / ell;
        for x in 2..P {
            let x2 = fp_mul(x, x);
            let rhs = fp_add(fp_add(fp_mul(x2, x), fp_mul(self.a, x2)), x);
            if rhs == 0 || fp_sqrt(rhs).is_some() {
                continue;
            }
            let ker = xmul(
                cofactor,
                ProjX {
                    x: ff.to_mont(x),
                    z: ff.one(),
                },
                cur,
                &ff,
            );
            if !ker.is_infinity() {
                let kx = ff.from_mont(ff.mul(ker.x, ff.inv(ker.z)));
                return Some(MontPoint::Affine { x: kx, y: 0 });
            }
        }
        None
    }
}

// ── Exact Meyer–Reith Vélu codomain formula ───────────────────────

/// Compute the exact Montgomery codomain `A'` of the `ℓ`-isogeny on `E_A`
/// with kernel generated by `p` (works for both curve and twist points).
pub fn velu_codomain(curve: &MontCurve, p: &MontPoint, ell: u64) -> u64 {
    assert!(ell % 2 == 1, "ℓ must be odd");
    let MontPoint::Affine { x, .. } = *p else {
        return curve.a % P;
    };
    let ff = FastField::new(P).expect("P = 419 valid");
    let cur = ProjCurve::from_affine_a(curve.a % P, &ff);
    let k1 = ProjX {
        x: ff.to_mont(x % P),
        z: ff.one(),
    };
    velu_isogeny_proj(cur, k1, ell, &mut [], &ff).to_affine_a(&ff)
}

// ── Class group action ────────────────────────────────────────────

/// Apply one signed `ℓ`-isogeny step (`direction >= 0` on `E_A`,
/// `direction < 0` on the quadratic twist `E_A^t`).
pub fn apply_action_step(curve: &MontCurve, ell: u64, direction: i32) -> MontCurve {
    if direction == 0 {
        return *curve;
    }
    let idx = match ELL.iter().position(|&l| l == ell) {
        Some(i) => i,
        None => {
            let ker = if direction > 0 {
                curve.find_point_of_order(ell)
            } else {
                curve.find_twist_point_of_order(ell)
            };
            return match ker {
                Some(pt) => MontCurve {
                    a: velu_codomain(curve, &pt, ell),
                },
                None => *curve,
            };
        }
    };
    let mut vec = [0i32; 3];
    vec[idx] = direction.signum();
    let new_a = CsidhParams::toy_419().action(curve.a, &vec);
    MontCurve { a: new_a }
}

/// Full commutative class-group action `[ℓ_1^{e_1} … ℓ_n^{e_n}] · E_A`.
pub fn class_group_action(curve: &MontCurve, secret: &[i32]) -> MontCurve {
    static PARAMS_419: std::sync::OnceLock<CsidhParams<'static>> = std::sync::OnceLock::new();
    let params = PARAMS_419.get_or_init(CsidhParams::toy_419);
    MontCurve {
        a: params.action(curve.a, secret),
    }
}

// ── CSIDH key exchange ────────────────────────────────────────────

#[derive(Clone, Debug)]
pub struct CsidhPrivateKey {
    pub vec: Vec<i32>,
}

#[derive(Clone, Debug, Copy)]
pub struct CsidhPublicKey {
    pub curve: MontCurve,
}

/// Generate a CSIDH private key: each coordinate in `[−M, M]`.
pub fn csidh_keygen_private() -> CsidhPrivateKey {
    let mut rng = OsRng;
    let vec: Vec<i32> = ELL.iter().map(|_| rng.gen_range(-M..=M)).collect();
    CsidhPrivateKey { vec }
}

/// Compute the public key by applying the private key to `E_0`.
pub fn csidh_public_key(sk: &CsidhPrivateKey) -> CsidhPublicKey {
    let curve = class_group_action(&MontCurve::base(), &sk.vec);
    CsidhPublicKey { curve }
}

/// Derive the shared secret: apply our private key to the other
/// party's public curve.  Returns the Montgomery `A` coefficient.
pub fn csidh_shared_secret(sk: &CsidhPrivateKey, peer_pk: &CsidhPublicKey) -> u64 {
    let shared = class_group_action(&peer_pk.curve, &sk.vec);
    shared.a
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn p_is_prime() {
        for d in 2..(P as f64).sqrt() as u64 + 1 {
            assert!(!P.is_multiple_of(d), "P = {} divisible by {}", P, d);
        }
    }

    #[test]
    fn base_curve_has_correct_order() {
        let e0 = MontCurve::base();
        let pts = e0.all_points();
        assert_eq!(pts.len(), 420);
    }

    #[test]
    fn find_points_of_each_order() {
        let e0 = MontCurve::base();
        for &ell in &ELL {
            let p = e0.find_point_of_order(ell).expect("should find point");
            assert!(matches!(e0.scalar_mul(&p, ell), MontPoint::Infinity));
            if ell > 1 {
                let lminus = e0.scalar_mul(&p, ell - 1);
                assert!(!matches!(lminus, MontPoint::Infinity));
            }
        }
    }

    #[test]
    fn action_step_changes_curve_and_inverts() {
        let e0 = MontCurve::base();
        for &ell in &ELL {
            let e_fwd = apply_action_step(&e0, ell, 1);
            assert_ne!(e_fwd.a, e0.a);
            let e_back = apply_action_step(&e_fwd, ell, -1);
            assert_eq!(
                e_back.a, e0.a,
                "inverse step must return to E_0 for ell={ell}"
            );
        }
    }

    #[test]
    fn csidh_action_structural_integrity_and_exact_commutativity() {
        let e0 = MontCurve::base();
        for (sk_a, sk_b) in [
            (vec![1, 0, 0], vec![0, 1, 0]),
            (vec![2, -1, 3], vec![-3, 2, -1]),
            (vec![-3, -2, 3], vec![3, -3, -2]),
            (vec![3, 3, 3], vec![-3, 1, -2]),
        ] {
            let pk_a = CsidhPublicKey {
                curve: class_group_action(&e0, &sk_a),
            };
            let pk_b = CsidhPublicKey {
                curve: class_group_action(&e0, &sk_b),
            };
            let ss_ab = csidh_shared_secret(&CsidhPrivateKey { vec: sk_a.clone() }, &pk_b);
            let ss_ba = csidh_shared_secret(&CsidhPrivateKey { vec: sk_b.clone() }, &pk_a);
            assert_eq!(ss_ab, ss_ba, "CSIDH key exchange must commute");

            let neg_a: Vec<i32> = sk_a.iter().map(|e| -e).collect();
            let back = class_group_action(&pk_a.curve, &neg_a);
            assert_eq!(back.a, e0.a, "[-sk] · ([sk] · E_0) must equal E_0");
        }
    }

    #[test]
    fn csidh_56_commutativity_and_remainder_tree_equivalence() {
        let params = CsidhParams::csidh_56();
        let sk_a = [2, -1, 3, -2, 1, 0, -3, 2, -1, 1, -2, 3, -1];
        let sk_b = [-1, 3, -2, 1, -2, 2, 1, -3, 2, -2, 1, -1, 2];

        let pk_a = params.action(0, &sk_a);
        let pk_b = params.action(0, &sk_b);
        assert_eq!(
            params.action(pk_b, &sk_a),
            params.action(pk_a, &sk_b),
            "56-bit 13-prime CSIDH must commute"
        );
        // Batched SIMBA action must match naive sequential action bit-for-bit.
        assert_eq!(pk_a, params.action_naive_sequential(0, &sk_a));

        // Cofactor remainder tree must match individual scalar multiplications.
        let ff = params.field();
        let cur = ProjCurve::from_affine_a(pk_a, ff);
        let root = ProjX {
            x: ff.to_mont(7),
            z: ff.one(),
        };
        let subset = &ELL_56[..8];
        let tree_pts = cofactor_remainder_tree(root, cur, subset, ff);
        let prod_all: u64 = subset.iter().product();
        for (i, &ell) in subset.iter().enumerate() {
            let direct = xmul(prod_all / ell, root, cur, ff);
            assert_eq!(
                ff.mul(tree_pts[i].x, direct.z),
                ff.mul(direct.x, tree_pts[i].z),
                "remainder tree mismatch at ell={ell}"
            );
        }
    }

    #[test]
    fn zero_secret_is_identity() {
        let e0 = MontCurve::base();
        let pk_zero = csidh_public_key(&CsidhPrivateKey { vec: vec![0, 0, 0] });
        assert_eq!(pk_zero.curve.a, e0.a);
    }

    #[test]
    fn csidh_shared_secret_is_deterministic_and_commutative() {
        let sk_a = csidh_keygen_private();
        let sk_b = csidh_keygen_private();
        let pk_a = csidh_public_key(&sk_a);
        let pk_b = csidh_public_key(&sk_b);
        let ss_ab = csidh_shared_secret(&sk_a, &pk_b);
        let ss_ba = csidh_shared_secret(&sk_b, &pk_a);
        assert_eq!(ss_ab, ss_ba);
    }

    #[test]
    fn velu_sqrt_matches_velu_proj_and_csidh_60_large_commutes() {
        let params = CsidhParams::csidh_60_large();
        let ff = params.field();
        let p = params.p;
        let cur = ProjCurve::from_affine_a(0, ff);

        // Verify exact projective agreement between `velu_sqrt_proj` and
        // `velu_isogeny_proj` (both codomain A and pushed point) for every
        // odd prime >= 89 in ELL_60_LARGE: [89, 107, 131, 199, 251, 307, 587].
        for &ell in &ELL_60_LARGE[2..] {
            let mut x_cand = 3u64;
            let ker = loop {
                let xm = ff.to_mont(x_cand);
                x_cand += 1;
                let k = xmul((p + 1) / ell, ProjX { x: xm, z: ff.one() }, cur, ff);
                if !k.is_infinity() {
                    break k;
                }
            };
            let probe = ProjX {
                x: ff.to_mont(11),
                z: ff.one(),
            };
            let mut push_lin = [probe];
            let mut push_sq = [probe];
            let cod_lin = velu_isogeny_proj(cur, ker, ell, &mut push_lin, ff);
            let cod_sq = velu_sqrt_proj(cur, ker, ell, &mut push_sq, ff);
            assert_eq!(
                cod_lin.to_affine_a(ff),
                cod_sq.to_affine_a(ff),
                "codomain mismatch between velu_sqrt_proj and velu_isogeny_proj at ell={ell}"
            );
            assert_eq!(
                ff.mul(push_lin[0].x, push_sq[0].z),
                ff.mul(push_sq[0].x, push_lin[0].z),
                "pushed point mismatch between velu_sqrt_proj and velu_isogeny_proj at ell={ell}"
            );
        }

        // Verify full 60-bit large-prime CSIDH action commutativity & naive equivalence.
        let sk_a = [1, -1, 2, -1, 1, -2, 1, -1, 2];
        let sk_b = [-1, 2, -1, 2, -1, 1, -2, 1, -1];
        let pk_a = params.action(0, &sk_a);
        let pk_b = params.action(0, &sk_b);
        assert_eq!(
            params.action(pk_b, &sk_a),
            params.action(pk_a, &sk_b),
            "60-bit large-prime CSIDH must commute under √élu"
        );
        assert_eq!(
            pk_a,
            params.action_naive_sequential(0, &sk_a),
            "SIMBA + √élu must match naive sequential Meyer–Reith bit-for-bit"
        );
    }
}
