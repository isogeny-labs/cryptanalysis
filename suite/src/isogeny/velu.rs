//! # Vélu's formulas: explicit isogenies from a kernel subgroup.
//!
//! Vélu (1971) gave a closed-form expression for the isogeny
//! `φ: E → E/G` once a finite subgroup `G ⊂ E(F̄)` is specified by
//! its non-identity points.  Given `E: y² = x³ + a x + b` and a
//! kernel `G = {O} ∪ {±P_1, …, ±P_s}` (so `|G| = 2s + 1` for odd
//! cyclic; `|G| = 2s + 2` for cyclic of even order with the 2-torsion
//! point `T = (x_T, 0)` adjoined), define for each `Q = (x_Q, y_Q)`
//! in `G \ {O}`:
//!
//! ```text
//!   g_x(Q) = 3 x_Q² + a
//!   g_y(Q) = -2 y_Q
//!   v(Q)   =   g_x(Q)            if 2Q = O          (T-row)
//!          = 2 g_x(Q)            otherwise
//!   u(Q)   = g_y(Q)²              (for the y-coordinate map)
//! ```
//!
//! Then summing over a half-set `R` (one representative of each
//! `{±Q}`):
//!
//! ```text
//!   x'  =  x + Σ_{Q ∈ R} [ v(Q) / (x − x_Q)  +  u(Q) / (x − x_Q)² ]
//!   y'  =  y · ( 1 − Σ_{Q ∈ R} [ v(Q) / (x − x_Q)²
//!                                + 2 u(Q) / (x − x_Q)³ ] )
//! ```
//!
//! and the codomain curve is `E' : Y² = X³ + a' X + b'` with
//!
//! ```text
//!   a' = a − 5 · Σ v(Q)
//!   b' = b − 7 · Σ ( u(Q) + x_Q · v(Q) )
//! ```
//!
//! (Both sums are over `R`.)
//!
//! ## Why we keep a separate, small implementation
//!
//! [`crate::cryptanalysis::modular_polynomial`] gives the
//! "algebraic" view: `Φ_ℓ(j(E), j(E')) = 0` constrains *which*
//! `E'` can be reached, but does not tell us **how** to construct
//! the isogeny rationally.  Vélu does both: codomain curve **and**
//! the rational maps for evaluating `φ` on points.
//!
//! ## Scope
//!
//! This module enumerates pointwise-rational kernels over `F_p` and
//! computes Vélu's sums directly. It is not a complete enumerator of
//! isogenies defined over `F_p`: Frobenius-stable kernels may have
//! no nonidentity `F_p`-points. For degree 3, see `stable_three`.  This is `O(ℓ)` field operations
//! per isogeny — fine for `ℓ ≤ 100` and the toy curves used here.
//! Production-grade `√ℓ`-style algorithms (Bernstein–De Feo–
//! Leroux–Smith, 2020) are deliberately not implemented.

use super::SmallCurve;
use num_bigint::BigUint;

/// An `ℓ`-isogeny `φ: E → E'` constructed via Vélu's formulas.
#[derive(Clone, Debug)]
pub struct VeluIsogeny {
    /// The source curve.
    pub domain: SmallCurve,
    /// The codomain curve `E'`.  Computed by Vélu's `a'`, `b'`
    /// formulas above.  `name` is reused from the domain (we do
    /// not invent a new label here).
    pub codomain: SmallCurve,
    /// The degree `ℓ`.
    pub degree: u64,
    /// The kernel's non-identity points as `(x, y)` pairs over
    /// `F_p`, listed as a half-set `R` (one representative per
    /// `{±Q}`).
    pub kernel_half: Vec<(u64, u64)>,
}

impl VeluIsogeny {
    /// Evaluate the isogeny at an affine point `(x, y)`.  Returns
    /// `None` when `(x, y)` is in the kernel (image is the point
    /// at infinity).
    ///
    /// Uses Montgomery's simultaneous batch inversion across all
    /// `(x - x_Q)` denominators so the whole evaluation pays **one**
    /// extended-GCD inversion instead of `(ℓ - 1)/2` modular
    /// exponentiations.
    pub fn evaluate(&self, x: u64, y: u64) -> Option<(u64, u64)> {
        let klen = self.kernel_half.len();
        let p64 = self.domain.p;
        let p = p64 as u128;
        let xm = (x % p64) as u128;
        let ym = (y % p64) as u128;
        if klen == 0 {
            return Some((xm as u64, ym as u64));
        }
        let a = (self.domain.a % p64) as u128;

        const STACK_CAP: usize = 64;
        let mut stack_dx = [0u128; STACK_CAP];
        let mut stack_pre = [0u128; STACK_CAP];
        let mut heap_dx: Vec<u128>;
        let mut heap_pre: Vec<u128>;
        let (dxs, pres): (&mut [u128], &mut [u128]) = if klen <= STACK_CAP {
            (&mut stack_dx[..klen], &mut stack_pre[..klen])
        } else {
            heap_dx = vec![0u128; klen];
            heap_pre = vec![0u128; klen];
            (&mut heap_dx[..], &mut heap_pre[..])
        };

        let mut run = 1u128;
        for (i, &(xq_raw, _)) in self.kernel_half.iter().enumerate() {
            let xq = (xq_raw % p64) as u128;
            if xm == xq {
                return None;
            }
            let dx = if xm >= xq { xm - xq } else { xm + p - xq };
            dxs[i] = dx;
            pres[i] = run;
            run = (run * dx) % p;
        }

        let mut inv_acc = mod_inv(run, p)?;
        let mut acc_x = xm;
        let mut acc_y = ym;

        for i in (0..klen).rev() {
            let dx_inv = (inv_acc * pres[i]) % p;
            inv_acc = (inv_acc * dxs[i]) % p;

            let (xq_raw, yq_raw) = self.kernel_half[i];
            let xq = (xq_raw % p64) as u128;
            let yq = (yq_raw % p64) as u128;

            let gx_q = ((3 * ((xq * xq) % p)) + a) % p;
            let gy_q = if yq == 0 { 0 } else { p - ((2 * yq) % p) };
            let v_q = if yq == 0 { gx_q } else { (2 * gx_q) % p };
            let u_q = (gy_q * gy_q) % p;

            let dx_inv2 = (dx_inv * dx_inv) % p;
            let dx_inv3 = (dx_inv2 * dx_inv) % p;

            acc_x = (acc_x + (v_q * dx_inv) % p + (u_q * dx_inv2) % p) % p;
            let bracket = ((v_q * dx_inv2) % p + (((2 * u_q) % p) * dx_inv3) % p) % p;
            let term_y = (ym * bracket) % p;
            acc_y = if acc_y >= term_y {
                acc_y - term_y
            } else {
                acc_y + p - term_y
            };
        }
        Some((acc_x as u64, acc_y as u64))
    }
}

// ── Modular arithmetic helpers in u128 ────────────────────────────────────────

#[inline(always)]
fn mod_add(a: u128, b: u128, p: u128) -> u128 {
    ((a % p) + (b % p)) % p
}
#[inline(always)]
fn mod_sub(a: u128, b: u128, p: u128) -> u128 {
    ((a % p) + p - (b % p)) % p
}
#[inline(always)]
fn mod_mul(a: u128, b: u128, p: u128) -> u128 {
    // For p < 2^62 this fits comfortably in u128 (operands < 2^62
    // each, product < 2^124).
    ((a % p) * (b % p)) % p
}
#[inline]
fn mod_inv(a: u128, p: u128) -> Option<u128> {
    let a64 = (a % p) as u64;
    let p64 = p as u64;
    if a64 == 0 || p64 == 0 {
        return None;
    }
    let (mut old_r, mut r) = (a64, p64);
    let (mut old_s, mut s) = (1i128, 0i128);
    while r != 0 {
        let q = old_r / r;
        (old_r, r) = (r, old_r - q * r);
        (old_s, s) = (s, old_s - (q as i128) * s);
    }
    if old_r != 1 {
        return None;
    }
    Some(old_s.rem_euclid(p as i128) as u128)
}

// ── Vélu codomain construction ────────────────────────────────────────────────

/// Compute the codomain curve and kernel-half representation from a
/// list of affine kernel points.  The list must contain at least one
/// representative of each `{±Q}` orbit.  Duplicate `{±Q}` orbits in
/// the input are silently de-duplicated.
fn velu_codomain_from_kernel(domain: &SmallCurve, kernel: &[(u64, u64)]) -> VeluIsogeny {
    let p = domain.p as u128;
    let a = domain.a as u128 % p;
    let b = domain.b as u128 % p;

    // Reduce to a half-set R: keep `Q` and drop `-Q`.
    let mut seen_x = std::collections::HashSet::<u64>::new();
    let mut half = Vec::new();
    for &(x, y) in kernel {
        if seen_x.insert(x) {
            half.push((x, y));
        }
    }

    let mut sum_v = 0u128;
    let mut sum_uvx = 0u128;
    for &(xq, yq) in &half {
        let xq = xq as u128 % p;
        let yq = yq as u128 % p;

        let gx_q = mod_add(3 * mod_mul(xq, xq, p) % p, a, p);
        let gy_q = mod_sub(0, 2 * yq % p, p);
        let t_row = yq == 0;
        // Vélu: v(Q) = g_x(Q) when 2Q = O, and 2·g_x(Q) otherwise.
        let v_q = if t_row { gx_q } else { (2 * gx_q) % p };
        let u_q = mod_mul(gy_q, gy_q, p);

        sum_v = mod_add(sum_v, v_q, p);
        sum_uvx = mod_add(sum_uvx, mod_add(u_q, mod_mul(xq, v_q, p), p), p);
    }

    let new_a = mod_sub(a, (5 * sum_v) % p, p) as u64;
    let new_b = mod_sub(b, (7 * sum_uvx) % p, p) as u64;
    let codomain = SmallCurve {
        name: domain.name,
        p: domain.p,
        a: new_a,
        b: new_b,
    };
    // For a cyclic kernel of odd order ℓ: |G| = 2·|half| + 1.
    // For a cyclic kernel of even order ℓ that includes the
    // 2-torsion point T = (x_T, 0): |G| = 2·|half| (T appears in
    // `half` as its own inverse).
    let degree = if half.iter().any(|&(_, y)| y == 0) {
        2 * (half.len() as u64)
    } else {
        2 * (half.len() as u64) + 1
    };

    VeluIsogeny {
        domain: *domain,
        codomain,
        degree,
        kernel_half: half,
    }
}

// ── ℓ = 2 isogeny ────────────────────────────────────────────────────────────

/// Compute a 2-isogeny with the specified 2-torsion point `T = (x_T, 0)`
/// as kernel.  `T` must satisfy `y² = x³ + a x + b` with `y = 0`,
/// i.e. `x_T` is a root of `x³ + a x + b` over `F_p`.
pub fn velu_isogeny_2(domain: &SmallCurve, x_t: u64) -> Option<VeluIsogeny> {
    let p = domain.p as u128;
    let xt = x_t as u128 % p;
    let a = domain.a as u128 % p;
    let b = domain.b as u128 % p;
    // Check x_T is on the curve with y = 0.
    let rhs = mod_add(
        mod_add(mod_mul(mod_mul(xt, xt, p), xt, p), mod_mul(a, xt, p), p),
        b,
        p,
    );
    if rhs != 0 {
        return None;
    }
    Some(velu_codomain_from_kernel(domain, &[(x_t, 0)]))
}

// ── ℓ-odd isogeny via cofactor sampling ──────────────────────────────────────

/// Sample degree-`ℓ` isogenies with **pointwise Fp-rational** kernels.
/// This is a partial, bounded random sampler, NOT an enumerator of all
/// Fp-defined degree-`ℓ` isogenies. The result may be empty even when a
/// Frobenius-stable kernel exists (e.g. p=103, E:y²=x³+3, ℓ=3).
/// For exhaustive rational degree-3 kernels over small fields, use
/// `super::stable_three::three_isogenies_over_fp_small`.
/// `ℓ` must be an odd prime.
///
/// Algorithm (random-point cofactor method, Schoof 1995 §3):
///
/// 1. Compute `#E(F_p) = p + 1 − t` via [`crate::isogeny::cm::cm_discriminant`].
/// 2. If `ℓ ∤ #E`, no nonzero `F_p`-rational point has order `ℓ`.
///    Return `[]` **for this pointwise-kernel sampler only**. Rational
///    isogenies with nonrational kernel generators are not excluded.
/// 3. Otherwise let `m = #E / ℓ`.  Repeatedly sample random
///    `P ∈ E(F_p)` and form `Q = m·P`; if `Q ≠ O`, then `Q` has
///    order dividing `ℓ`, and (since `ℓ` is prime) its order is
///    exactly `ℓ`, so `⟨Q⟩` is a cyclic subgroup of order `ℓ`.
/// 4. Stop after the sampling cap or `ℓ+1` distinct subgroups.
///    The sampling cap does not certify that all such subgroups were found.
///
/// Cost: `O(ℓ² · log² p)` total — `O(log² p)` per scalar mult,
/// `O(ℓ)` samples expected per distinct subgroup, `O(ℓ)` subgroups
/// in the saturated case.  Compared to the previous
/// `O(ℓ² · p · log² p)` enumeration: at `p = 2^30` and `ℓ = 3`,
/// roughly a `10^9×` speed-up.
pub fn velu_isogeny_odd(domain: &SmallCurve, ell: u64) -> Vec<VeluIsogeny> {
    assert!(ell >= 3 && ell % 2 == 1, "ℓ must be an odd prime");

    use crate::cryptanalysis::bsgs_fast::{FastField, FastPoint};
    use crate::isogeny::cm::{cm_discriminant, legendre_u64, tonelli_shanks_u64};
    use std::collections::HashSet;

    let cm = cm_discriminant(domain);
    if cm.order <= 0 {
        return Vec::new();
    }
    let order = cm.order as u64;
    if !order.is_multiple_of(ell) {
        // No pointwise Fp-rational ℓ-torsion; other stable kernels may exist.
        return Vec::new();
    }
    let cofactor = order / ell;
    let p = domain.p;

    let Some(ff) = FastField::new(p) else {
        return Vec::new();
    };
    let a_m = ff.to_mont(domain.a % p);

    // Single-word Jacobian scalar multiplication on `domain` (zero heap allocations).
    let jac_dbl = |jx: u64, jy: u64, jz: u64| -> (u64, u64, u64, bool) {
        if jy == 0 {
            return (0, 0, 0, true);
        }
        let xx = ff.sqr(jx);
        let yy = ff.sqr(jy);
        let yyyy = ff.sqr(yy);
        let zz = ff.sqr(jz);
        let t = ff.add(jx, yy);
        let s = ff.dbl(ff.sub(ff.sub(ff.sqr(t), xx), yyyy));
        let m = ff.add(ff.add(ff.dbl(xx), xx), ff.mul(a_m, ff.sqr(zz)));
        let x3 = ff.sub(ff.sqr(m), ff.dbl(s));
        let y8 = ff.dbl(ff.dbl(ff.dbl(yyyy)));
        let y3 = ff.sub(ff.mul(m, ff.sub(s, x3)), y8);
        let z3 = ff.sub(ff.sub(ff.sqr(ff.add(jy, jz)), yy), zz);
        (x3, y3, z3, false)
    };
    let fast_add = |p1: FastPoint, p2: FastPoint| -> FastPoint {
        if p1.infinity {
            return p2;
        }
        if p2.infinity {
            return p1;
        }
        if p1.x == p2.x {
            if p1.y != p2.y || p1.y == 0 {
                return FastPoint::INFINITY;
            }
            let x2 = ff.sqr(p1.x);
            let num = ff.add(ff.add(ff.dbl(x2), x2), a_m);
            let den = ff.dbl(p1.y);
            let lam = ff.mul(num, ff.inv(den));
            let x3 = ff.sub(ff.sqr(lam), ff.dbl(p1.x));
            let y3 = ff.sub(ff.mul(lam, ff.sub(p1.x, x3)), p1.y);
            return FastPoint {
                x: x3,
                y: y3,
                infinity: false,
            };
        }
        let lam = ff.mul(ff.sub(p2.y, p1.y), ff.inv(ff.sub(p2.x, p1.x)));
        let x3 = ff.sub(ff.sub(ff.sqr(lam), p1.x), p2.x);
        let y3 = ff.sub(ff.mul(lam, ff.sub(p1.x, x3)), p1.y);
        FastPoint {
            x: x3,
            y: y3,
            infinity: false,
        }
    };
    let fast_scalar_mul = |pt: FastPoint, mut k: u64| -> FastPoint {
        if pt.infinity || k == 0 {
            return FastPoint::INFINITY;
        }
        let mut jx = 0u64;
        let mut jy = 0u64;
        let mut jz = 0u64;
        let mut j_inf = true;
        let top = 63 - k.leading_zeros();
        for bit in (0..=top).rev() {
            if !j_inf {
                let (nx, ny, nz, inf) = jac_dbl(jx, jy, jz);
                jx = nx;
                jy = ny;
                jz = nz;
                j_inf = inf;
            }
            if (k >> bit) & 1 == 1 {
                if j_inf {
                    jx = pt.x;
                    jy = pt.y;
                    jz = ff.one();
                    j_inf = false;
                } else {
                    let z1z1 = ff.sqr(jz);
                    let u2 = ff.mul(pt.x, z1z1);
                    let s2 = ff.mul(pt.y, ff.mul(jz, z1z1));
                    let h = ff.sub(u2, jx);
                    let r = ff.sub(s2, jy);
                    if h == 0 {
                        if r == 0 {
                            let (nx, ny, nz, inf) = jac_dbl(jx, jy, jz);
                            jx = nx;
                            jy = ny;
                            jz = nz;
                            j_inf = inf;
                        } else {
                            j_inf = true;
                        }
                    } else {
                        let hh = ff.sqr(h);
                        let hhh = ff.mul(h, hh);
                        let v = ff.mul(jx, hh);
                        let x3 = ff.sub(ff.sub(ff.sqr(r), hhh), ff.dbl(v));
                        let y3 = ff.sub(ff.mul(r, ff.sub(v, x3)), ff.mul(jy, hhh));
                        let z3 = ff.mul(jz, h);
                        jx = x3;
                        jy = y3;
                        jz = z3;
                    }
                }
            }
            let _ = &mut k;
        }
        if j_inf {
            return FastPoint::INFINITY;
        }
        let zi = ff.inv(jz);
        let zi2 = ff.sqr(zi);
        FastPoint {
            x: ff.mul(jx, zi2),
            y: ff.mul(jy, ff.mul(zi2, zi)),
            infinity: false,
        }
    };

    let mut seen_subgroups: HashSet<Vec<u64>> = HashSet::new();
    let mut result = Vec::new();
    let mut rng_state: u64 = domain
        .p
        .wrapping_mul(0x9E3779B97F4A7C15)
        .wrapping_add(domain.a)
        .wrapping_mul(0xC6BC279692B5C323)
        .wrapping_add(domain.b)
        .wrapping_add(ell);
    let max_attempts: u64 = 4 * ell + 16;
    let max_subgroups = (ell + 1) as usize;

    for _ in 0..max_attempts {
        rng_state = rng_state
            .wrapping_mul(6364136223846793005)
            .wrapping_add(1442695040888963407);
        // Sample random affine point directly in u64 without BigUint conversions.
        let mut sampled = None;
        for _ in 0..p {
            rng_state = rng_state
                .wrapping_mul(6364136223846793005)
                .wrapping_add(1442695040888963407);
            let x = (rng_state >> 7) % p;
            let rhs = domain.rhs(x);
            if rhs == 0 {
                sampled = Some(FastPoint {
                    x: ff.to_mont(x),
                    y: 0,
                    infinity: false,
                });
                break;
            }
            if legendre_u64(rhs, p) == 1 {
                if let Some(y) = tonelli_shanks_u64(rhs, p) {
                    sampled = Some(FastPoint {
                        x: ff.to_mont(x),
                        y: ff.to_mont(y),
                        infinity: false,
                    });
                    break;
                }
            }
        }
        let Some(point) = sampled else {
            continue;
        };
        let q = fast_scalar_mul(point, cofactor);
        if q.infinity {
            continue;
        }
        let mut xs: Vec<u64> = Vec::with_capacity((ell - 1) as usize);
        let mut kernel: Vec<(u64, u64)> = Vec::with_capacity((ell - 1) as usize);
        let mut acc = q;
        let mut bad = false;
        for _ in 1..ell {
            if acc.infinity {
                bad = true;
                break;
            }
            let xv = ff.from_mont(acc.x);
            let yv = ff.from_mont(acc.y);
            xs.push(xv);
            kernel.push((xv, yv));
            acc = fast_add(acc, q);
        }
        if bad || kernel.len() as u64 != ell - 1 {
            continue;
        }
        let mut key = xs;
        key.sort_unstable();
        if !seen_subgroups.insert(key) {
            continue;
        }
        result.push(velu_codomain_from_kernel(domain, &kernel));
        if result.len() >= max_subgroups {
            break;
        }
    }
    result
}

// ── Dual isogeny ──────────────────────────────────────────────────────────────
//
// For φ: E → E' of degree ℓ, the dual `φ̂: E' → E` is again degree ℓ
// and satisfies `φ̂ ∘ φ = [ℓ]_E`.  The kernel of `φ̂` is `φ(E[ℓ])`,
// which over `F_p` is the image of any `ℓ`-torsion subgroup of `E'`
// not equal to `ker(φ̂)` itself.
//
// We provide a `dual_isogeny_naive` that simply searches the
// codomain's `ℓ`-torsion subgroups and picks the one that completes
// the round-trip on a probe point.

/// Find the dual `ℓ`-isogeny of a `VeluIsogeny` by exhaustive search
/// over the codomain's `ℓ`-isogeny family.  `O(deg)`-many candidates
/// (one per cyclic subgroup); each is tested by checking that the
/// composition is `[ℓ]` on a single probe point.
pub fn dual_isogeny_naive(phi: &VeluIsogeny) -> Option<VeluIsogeny> {
    let ell = phi.degree;
    let cands = if ell == 2 {
        // 2-isogeny: search the codomain's 2-torsion.
        let mut v = Vec::new();
        for x in 0..phi.codomain.p {
            if phi.codomain.rhs(x) == 0 {
                if let Some(iso) = velu_isogeny_2(&phi.codomain, x) {
                    v.push(iso);
                }
            }
        }
        v
    } else {
        velu_isogeny_odd(&phi.codomain, ell)
    };

    // Probe: pick a point on the domain that's not in ker(φ).
    let p = phi.domain.p;
    for x in 2..p {
        let rhs = phi.domain.rhs(x);
        if rhs == 0 {
            continue;
        }
        let y = match crate::isogeny::cm::legendre_u64(rhs, p) {
            1 => match crate::isogeny::cm::tonelli_shanks_u64(rhs, p) {
                Some(y) if y != 0 => y,
                _ => continue,
            },
            _ => continue,
        };
        let _ = y; // explicit binding for clarity below

        if let Some(image) = phi.evaluate(x, y) {
            // For each candidate ψ, compute ψ(image) and check it equals [ell] · (x, y).
            let curve = phi.domain.to_curve_params();
            let a_fe = curve.a_fe();
            let p_point = crate::ecc::point::Point::Affine {
                x: curve.fe(BigUint::from(x)),
                y: curve.fe(BigUint::from(y)),
            };
            let ell_p = p_point.scalar_mul(&BigUint::from(ell), &a_fe);
            for psi in &cands {
                if let Some((px, py)) = psi.evaluate(image.0, image.1) {
                    if let crate::ecc::point::Point::Affine { x: ex, y: ey } = &ell_p {
                        let exv = ex.value.iter_u64_digits().next().unwrap_or(0);
                        let eyv = ey.value.iter_u64_digits().next().unwrap_or(0);
                        if exv == px && eyv == py {
                            return Some(psi.clone());
                        }
                    }
                }
            }
            // No probe → too small; bail.
            break;
        }
    }
    None
}

// ── Composition of isogenies ─────────────────────────────────────────────────

/// Compose two Vélu isogenies `φ: E → E'` and `ψ: E' → E''`.  The
/// returned record's `kernel_half` field is the *pull-back* of
/// `ψ`'s kernel under `φ` (computed by evaluating `φ` on a curve
/// enumeration), so the resulting record correctly represents the
/// composite as a single isogeny.  Note: the **degree** of the
/// composite is `phi.degree · psi.degree`.
pub fn compose_isogenies(phi: &VeluIsogeny, psi: &VeluIsogeny) -> Option<VeluIsogeny> {
    if phi.codomain.a != psi.domain.a
        || phi.codomain.b != psi.domain.b
        || phi.codomain.p != psi.domain.p
    {
        return None;
    }
    // Enumerate ker(ψ ∘ φ) by walking E(F_p) and keeping points
    // whose image under φ lies in ker(ψ).  Tonelli-Shanks per x
    // gives O(p · log² p) instead of O(p²).
    let mut kernel = Vec::new();
    let p = phi.domain.p;
    for x in 0..p {
        let rhs = phi.domain.rhs(x);
        let y = if rhs == 0 {
            0u64
        } else {
            match crate::isogeny::cm::legendre_u64(rhs, p) {
                1 => match crate::isogeny::cm::tonelli_shanks_u64(rhs, p) {
                    Some(y) => y,
                    None => continue,
                },
                _ => continue,
            }
        };
        if let Some(image) = phi.evaluate(x, y) {
            if psi.kernel_half.iter().any(|&(kx, _)| kx == image.0) {
                kernel.push((x, y));
            }
        }
    }
    let mut iso = velu_codomain_from_kernel(&phi.domain, &kernel);
    iso.codomain = psi.codomain;
    iso.degree = phi.degree * psi.degree;
    Some(iso)
}

// ── Low-degree isogeny scalar multiplication (2-isogeny factoring & Montgomery bridge) ──

/// Factored doubling `[2]_E = φ̂₂ ∘ φ₂` via dual degree-2 isogenies on a
/// short Weierstrass curve `E: y² = x³ + ax + b` over `F_p` (`p < 2^63`)
/// carrying a rational 2-torsion point `T = (x₀, 0)`.
///
/// Translating `X = x − x₀` writes `E_tr: y² = X³ + A X² + B X` with
/// `A = 3 x₀`, `B = 3 x₀² + a`, and `E'_2: v² = u³ − 2A u² + (A² − 4B) u`.
/// In Jacobian coordinates `(X : Y : Z)`, each 2-isogeny step costs only
/// `3M + 4S` (vs `4M + 4S` / `3M + 5S` for generic Weierstrass doubling),
/// and a chain `[2^e]P` alternates `φ₂` and `φ̂₂` with a single inversion at
/// the end.
#[derive(Clone, Copy, Debug)]
pub struct Isogeny2Doubler {
    ff: crate::cryptanalysis::bsgs_fast::FastField,
    x0_m: u64,
    b_tr_m: u64,
    b_p_m: u64,
}

impl Isogeny2Doubler {
    /// Construct for `curve` given a rational 2-torsion abscissa `x0`
    /// (`x0³ + a·x0 + b ≡ 0 mod p`).
    pub fn new(curve: &SmallCurve, x0: u64) -> Option<Self> {
        use crate::cryptanalysis::bsgs_fast::FastField;
        let p = curve.p;
        if curve.rhs(x0 % p) != 0 {
            return None;
        }
        let ff = FastField::new(p)?;
        let x0_m = ff.to_mont(x0 % p);
        let a_m = ff.to_mont(curve.a % p);
        let x0_sq = ff.sqr(x0_m);
        let a_tr_m = ff.add(ff.dbl(x0_m), x0_m);
        let b_tr_m = ff.add(ff.add(ff.dbl(x0_sq), x0_sq), a_m);
        if b_tr_m == 0 {
            return None;
        }
        let four_b = ff.dbl(ff.dbl(b_tr_m));
        let b_p_m = ff.sub(ff.sqr(a_tr_m), four_b);
        if b_p_m == 0 {
            return None;
        }
        Some(Self {
            ff,
            x0_m,
            b_tr_m,
            b_p_m,
        })
    }

    /// Compute `[2]P` via `φ̂₂(φ₂(P))`.  Returns `None` for `O`.
    pub fn double_affine(&self, pt: Option<(u64, u64)>) -> Option<(u64, u64)> {
        self.double_k_affine(pt, 1)
    }

    /// Compute `[2^k]P` by alternating `φ₂` and `φ̂₂` in Jacobian coordinates
    /// with a single field inversion at the end.
    pub fn double_k_affine(&self, pt: Option<(u64, u64)>, k: usize) -> Option<(u64, u64)> {
        let (x, y) = pt?;
        if k == 0 {
            return Some((x % self.ff.modulus(), y % self.ff.modulus()));
        }
        let ff = &self.ff;
        let mut jx = ff.sub(ff.to_mont(x), self.x0_m);
        let mut jy = ff.to_mont(y);
        let mut jz = ff.one();

        for _ in 0..k {
            // φ₂: (X : Y : Z) ↦ (Y² : Y·X·(X² − B_tr·Z⁴) : X·Z)
            if jy == 0 || jx == 0 || jz == 0 {
                return None;
            }
            let x2 = ff.sqr(jx);
            let z2 = ff.sqr(jz);
            let z4 = ff.sqr(z2);
            let z1 = ff.mul(jx, jz);
            let x1 = ff.sqr(jy);
            let y1 = ff.mul(ff.mul(jy, jx), ff.sub(x2, ff.mul(self.b_tr_m, z4)));

            // φ̂₂: (X₁ : Y₁ : Z₁) ↦ (Y₁² : Y₁·X₁·(X₁² − B'·Z₁⁴) : 2·X₁·Z₁)
            if x1 == 0 || z1 == 0 {
                return None;
            }
            let z1_2 = ff.sqr(z1);
            let z1_4 = ff.sqr(z1_2);
            let x1_2 = ff.sqr(x1);
            jz = ff.dbl(ff.mul(x1, z1));
            jx = ff.sqr(y1);
            jy = ff.mul(ff.mul(y1, x1), ff.sub(x1_2, ff.mul(self.b_p_m, z1_4)));
        }

        if jz == 0 {
            return None;
        }
        let zi = ff.inv(jz);
        let zi2 = ff.sqr(zi);
        let rx = ff.add(ff.mul(jx, zi2), self.x0_m);
        let ry = ff.mul(jy, ff.mul(zi2, zi));
        Some((ff.from_mont(rx), ff.from_mont(ry)))
    }
}

/// Low-degree isogeny conjugation bridge `φ̂_ℓ ∘ ψ⁻¹ ∘ [k']_{E_M} ∘ ψ ∘ φ_ℓ`
/// (`k' = k · ℓ⁻¹ mod r`) mapping scalar multiplication from a short
/// Weierstrass curve `E` into an `XZ` differential Montgomery ladder (`5M + 4S`
/// per bit with normalised `a24`) with Okeya–Sakurai `O(1)` projective
/// `y`-recovery (`1I` total for the entire scalar multiplication!).
///
/// Supports both `ℓ = 1` (direct isomorphism when `E` itself has a rational
/// 2-torsion point `x₀` with `3x₀² + a` a non-zero square in `F_p`) and
/// `ℓ ≥ 2` (crossing a low-degree Vélu isogeny `φ_ℓ: E → E_cod` and its dual
/// `φ̂_ℓ: E_cod → E` once at the endpoints).
#[derive(Clone, Copy, Debug)]
struct Fast2IsoBridge {
    x0_dom_m: u64,
    b_tr_dom_m: u64,
    b_p_m: u64,
    two_inv_r: u64,
    r_ord: u64,
}

#[derive(Clone, Debug)]
pub struct MontgomeryIsogenyBridge {
    ff: crate::cryptanalysis::bsgs_fast::FastField,
    /// Optional outer Vélu pair `(φ_ℓ, φ̂_ℓ)` and `ℓ⁻¹ mod r` when `ℓ > 1`.
    outer: Option<(VeluIsogeny, VeluIsogeny, u64, u64)>,
    /// Optional zero-inversion projective dual 2-isogeny bridge for curves
    /// whose rational 2-torsion point has `3x₀² + a` a non-square over `F_p`,
    /// while the 2-isogenous codomain `E'_2` admits a Montgomery model.
    fast_2iso: Option<Fast2IsoBridge>,
    x0_m: u64,
    s_m: u64,
    s_inv_m: u64,
    two_am_m: u64,
    bm_m: u64,
    a24_m: u64,
}

impl MontgomeryIsogenyBridge {
    /// Build a direct (`ℓ = 1`) bridge on `curve` at the 2-torsion root `x0`
    /// when `3x0² + a` is a non-zero quadratic residue mod `p`.
    pub fn new_direct(curve: &SmallCurve, x0: u64) -> Option<Self> {
        use crate::cryptanalysis::bsgs_fast::FastField;
        use crate::isogeny::cm::{legendre_u64, tonelli_shanks_u64};

        let p = curve.p;
        if curve.rhs(x0 % p) != 0 {
            return None;
        }
        let p128 = p as u128;
        let x0_128 = (x0 % p) as u128;
        let c = ((3 * ((x0_128 * x0_128) % p128) + (curve.a % p) as u128) % p128) as u64;
        if c == 0 || legendre_u64(c, p) != 1 {
            return None;
        }
        let s = tonelli_shanks_u64(c, p)?;
        let ff = FastField::new(p)?;
        let x0_m = ff.to_mont(x0 % p);
        let s_m = ff.to_mont(s);
        let s_inv_m = ff.inv(s_m);
        let three_x0 = ff.add(ff.dbl(x0_m), x0_m);
        let am_m = ff.mul(three_x0, s_inv_m);
        let two_am_m = ff.dbl(am_m);
        let bm_m = s_inv_m;
        let four_inv = ff.inv(ff.to_mont(4 % p));
        let a24_m = ff.mul(ff.add(am_m, ff.to_mont(2 % p)), four_inv);
        Some(Self {
            ff,
            outer: None,
            fast_2iso: None,
            x0_m,
            s_m,
            s_inv_m,
            two_am_m,
            bm_m,
            a24_m,
        })
    }

    /// Build a zero-inversion projective 2-isogeny Montgomery bridge on `curve`
    /// at a rational 2-torsion root `x0_dom` whose own `3x0_dom² + a` need NOT
    /// be a square in `F_p`, provided the 2-isogenous codomain `E'_2` has
    /// `B' = 9x0_dom² − 4(3x0_dom² + a)` a non-zero square in `F_p` and
    /// `subgroup_order` is odd.
    pub fn new_2iso_zero_inv(curve: &SmallCurve, x0_dom: u64, subgroup_order: u64) -> Option<Self> {
        use crate::cryptanalysis::bsgs_fast::FastField;
        use crate::isogeny::cm::{legendre_u64, tonelli_shanks_u64};

        if subgroup_order == 0 || (subgroup_order & 1) == 0 {
            return None;
        }
        let p = curve.p;
        if curve.rhs(x0_dom % p) != 0 {
            return None;
        }
        let ff = FastField::new(p)?;
        let x0_dom_m = ff.to_mont(x0_dom % p);
        let a_m = ff.to_mont(curve.a % p);
        let x0_sq = ff.sqr(x0_dom_m);
        let a_tr_m = ff.add(ff.dbl(x0_dom_m), x0_dom_m); // 3*x0
        let b_tr_m = ff.add(ff.add(ff.dbl(x0_sq), x0_sq), a_m); // 3*x0^2 + a
        if b_tr_m == 0 {
            return None;
        }
        let b_p_m = ff.sub(ff.sqr(a_tr_m), ff.dbl(ff.dbl(b_tr_m))); // A_tr^2 - 4*B_tr
        let b_p_can = ff.from_mont(b_p_m);
        if b_p_can == 0 || legendre_u64(b_p_can, p) != 1 {
            return None;
        }
        let s = tonelli_shanks_u64(b_p_can, p)?;
        let s_m = ff.to_mont(s);
        let s_inv_m = ff.inv(s_m);
        // E'_2: v^2 = u^3 - 2*A_tr*u^2 + B'*u. Setting u = s*u_M, v = s*v_M:
        // (1/s) v_M^2 = u_M^3 + (-2*A_tr/s) u_M^2 + u_M.
        let am_m = ff.neg(ff.mul(ff.dbl(a_tr_m), s_inv_m));
        let two_am_m = ff.dbl(am_m);
        let bm_m = s_inv_m;
        let four_inv = ff.inv(ff.to_mont(4 % p));
        let a24_m = ff.mul(ff.add(am_m, ff.to_mont(2 % p)), four_inv);
        let two_inv_r = (subgroup_order + 1) / 2;
        Some(Self {
            ff,
            outer: None,
            fast_2iso: Some(Fast2IsoBridge {
                x0_dom_m,
                b_tr_dom_m: b_tr_m,
                b_p_m,
                two_inv_r,
                r_ord: subgroup_order,
            }),
            x0_m: 0,
            s_m,
            s_inv_m,
            two_am_m,
            bm_m,
            a24_m,
        })
    }

    /// Build a degree-`ℓ` isogeny conjugation bridge `φ̂_ℓ ∘ [k']_{E_M} ∘ φ_ℓ`
    /// for a subgroup of odd order `subgroup_order` (`gcd(ℓ, subgroup_order) = 1`),
    /// given `phi: E → E_cod` and a 2-torsion point `x0_cod` on `E_cod`.
    pub fn with_isogeny(phi: VeluIsogeny, x0_cod: u64, subgroup_order: u64) -> Option<Self> {
        let ell = phi.degree;
        let ell_inv = mod_inv(ell as u128, subgroup_order as u128)? as u64;
        let dual = dual_isogeny_naive(&phi)?;
        let mut bridge = Self::new_direct(&phi.codomain, x0_cod)?;
        bridge.outer = Some((phi, dual, ell_inv, subgroup_order));
        Some(bridge)
    }

    /// Zero-inversion projective scalar multiplication `[k]P` returning short
    /// Weierstrass Jacobian coordinates `(X : Y : Z)` in canonical `[0, p)`
    /// representation (`Z == 0` encodes `O`).
    ///
    /// Executes **zero field inversions** across the entire scalar
    /// multiplication — both on direct Montgomery-model curves (`5M + 4S`/bit)
    /// and on `new_2iso_zero_inv` curves that have NO direct Montgomery model
    /// over `F_p` (fusing projective `φ₂`, `XZ` ladder, Okeya–Sakurai `Y`
    /// recovery, and projective dual `φ̂₂`)!
    #[inline]
    pub fn scalar_mul_jacobian(&self, pt: Option<(u64, u64)>, k: u64) -> (u64, u64, u64) {
        let Some((in_x, in_y)) = pt else {
            return (1, 1, 0);
        };
        if k == 0 {
            return (1, 1, 0);
        }
        let ff = &self.ff;
        let p = ff.modulus();

        if let Some(f2) = self.fast_2iso {
            let k_eff = ((k as u128 * f2.two_inv_r as u128) % f2.r_ord as u128) as u64;
            if k_eff == 0 {
                return (1, 1, 0);
            }
            let xm = ff.to_mont(in_x % p);
            let ym = ff.to_mont(in_y % p);
            let w0 = ff.sub(xm, f2.x0_dom_m);
            if w0 == 0 || ym == 0 {
                return (1, 1, 0);
            }
            // φ₂(x, y): u = y² / w0², v = y·(w0² − B_tr) / w0³.
            let zu0 = ff.sqr(w0);
            let u0_num = ff.mul(ff.sqr(ym), self.s_inv_m);
            let v0_num = ff.mul(ff.mul(ym, ff.sub(zu0, f2.b_tr_dom_m)), self.s_inv_m);
            if v0_num == 0 {
                return (1, 1, 0);
            }
            let (u1, v1, z1) =
                self.ladder_projective_jacobian_raw(u0_num, zu0, v0_num, w0, k_eff, false);
            if z1 == 0 || u1 == 0 {
                return (1, 1, 0);
            }
            // Projective dual φ̂₂: (U₁ : V₁ : Z₁) ↦ (V₁² + x0_dom·Z_out² : V₁·U₁·(U₁² − B'·Z₁⁴) : 2·U₁·Z₁)
            let z_out = ff.dbl(ff.mul(u1, z1));
            let z1_2 = ff.sqr(z1);
            let z1_4 = ff.sqr(z1_2);
            let u1_2 = ff.sqr(u1);
            let x_out = ff.add(ff.sqr(v1), ff.mul(f2.x0_dom_m, ff.sqr(z_out)));
            let y_out = ff.mul(ff.mul(v1, u1), ff.sub(u1_2, ff.mul(f2.b_p_m, z1_4)));
            return (
                ff.from_mont(x_out),
                ff.from_mont(y_out),
                ff.from_mont(z_out),
            );
        }

        if self.outer.is_some() {
            return match self.scalar_mul(pt, k) {
                None => (1, 1, 0),
                Some((ax, ay)) => (ax, ay, 1),
            };
        }

        let xm = ff.to_mont(in_x % p);
        let ym = ff.to_mont(in_y % p);
        let u0 = ff.mul(ff.sub(xm, self.x0_m), self.s_inv_m);
        let v0 = ff.mul(ym, self.s_inv_m);
        if v0 == 0 {
            return if k & 1 == 0 {
                (1, 1, 0)
            } else {
                (in_x % p, 0, 1)
            };
        }
        let (jx, jy, jz) = self.ladder_projective_jacobian_raw(u0, ff.one(), v0, ff.one(), k, true);
        if jz == 0 {
            return (1, 1, 0);
        }
        (ff.from_mont(jx), ff.from_mont(jy), ff.from_mont(jz))
    }

    /// Normalise a Jacobian triple `(X : Y : Z)` returned by
    /// [`Self::scalar_mul_jacobian`] to affine coordinates (`1` inversion).
    #[inline]
    pub fn jacobian_to_affine(&self, jac: (u64, u64, u64)) -> Option<(u64, u64)> {
        let (x, y, z) = jac;
        if z == 0 {
            return None;
        }
        let ff = &self.ff;
        let zm = ff.to_mont(z);
        if zm == ff.one() {
            return Some((x, y));
        }
        let zi = ff.inv(zm);
        let zi2 = ff.sqr(zi);
        let rx = ff.mul(ff.to_mont(x), zi2);
        let ry = ff.mul(ff.to_mont(y), ff.mul(zi2, zi));
        Some((ff.from_mont(rx), ff.from_mont(ry)))
    }

    #[inline]
    fn ladder_projective_jacobian_raw(
        &self,
        u0_num: u64,
        zu0: u64,
        v0_num: u64,
        w0: u64,
        k: u64,
        unit_zu0: bool,
    ) -> (u64, u64, u64) {
        let ff = &self.ff;
        let mut x0 = ff.one();
        let mut z0 = 0u64;
        let mut x1 = u0_num;
        let mut z1 = zu0;

        let top = 63 - k.leading_zeros();
        for bit in (0..=top).rev() {
            let b = (k >> bit) & 1;
            if b == 1 {
                std::mem::swap(&mut x0, &mut x1);
                std::mem::swap(&mut z0, &mut z1);
            }
            let t0 = ff.add(x0, z0);
            let t1 = ff.sub(x0, z0);
            let t2 = ff.add(x1, z1);
            let t3 = ff.sub(x1, z1);
            let da = ff.mul(t0, t3);
            let cb = ff.mul(t1, t2);
            let sum_sq = ff.sqr(ff.add(da, cb));
            let x_add = if unit_zu0 {
                sum_sq
            } else {
                ff.mul(zu0, sum_sq)
            };
            let z_add = ff.mul(u0_num, ff.sqr(ff.sub(da, cb)));
            let aa = ff.sqr(t0);
            let bb = ff.sqr(t1);
            let ee = ff.sub(aa, bb);
            let x_dbl = ff.mul(aa, bb);
            let z_dbl = ff.mul(ee, ff.add(bb, ff.mul(self.a24_m, ee)));

            if b == 1 {
                x0 = x_add;
                z0 = z_add;
                x1 = x_dbl;
                z1 = z_dbl;
            } else {
                x0 = x_dbl;
                z0 = z_dbl;
                x1 = x_add;
                z1 = z_add;
            }
        }

        if z0 == 0 {
            return (ff.one(), ff.one(), 0);
        }
        if z1 == 0 {
            // [k+1]Q = O => [k]Q = -Q: u_k = U0/W0^2, v_k = -V0/W0^3.
            let u_s = ff.mul(self.s_m, u0_num);
            let x_j = if unit_zu0 {
                ff.add(u_s, self.x0_m)
            } else {
                ff.add(u_s, ff.mul(self.x0_m, zu0))
            };
            let y_j = ff.neg(ff.mul(self.s_m, v0_num));
            return (x_j, y_j, w0);
        }

        // Zero-inversion projective Okeya–Sakurai recovery!
        let (t1, t2, two_am_zu0_sq_z0_sq, diff) = if unit_zu0 {
            let t1 = ff.add(ff.mul(x0, u0_num), z0);
            let t2 = ff.add(x0, ff.mul(ff.add(u0_num, self.two_am_m), z0));
            let z0_sq = ff.sqr(z0);
            let mid = ff.mul(self.two_am_m, z0_sq);
            let diff = ff.sub(x0, ff.mul(u0_num, z0));
            (t1, t2, mid, diff)
        } else {
            let x0_zu0 = ff.mul(x0, zu0);
            let u0_z0 = ff.mul(u0_num, z0);
            let t1 = ff.add(x0_zu0, u0_z0);
            let two_am_zu0 = ff.mul(self.two_am_m, zu0);
            let t2 = ff.add(x0_zu0, ff.mul(ff.add(u0_num, two_am_zu0), z0));
            let zu0_z0 = ff.mul(zu0, z0);
            let mid = ff.mul(self.two_am_m, ff.sqr(zu0_z0));
            let diff = ff.sub(x0_zu0, u0_z0);
            (t1, t2, mid, diff)
        };
        let left = ff.mul(ff.sub(ff.mul(t1, t2), two_am_zu0_sq_z0_sq), z1);
        let right = ff.mul(ff.sqr(diff), x1);
        let num_v = ff.sub(left, right);

        let two_bm_v0 = ff.dbl(ff.mul(self.bm_m, v0_num));
        let d_fac = if unit_zu0 {
            ff.mul(two_bm_v0, z1)
        } else {
            ff.mul(ff.mul(two_bm_v0, w0), z1)
        };
        let z_j = ff.mul(d_fac, z0);
        let d_sq = ff.sqr(d_fac);
        let z0_d_sq = ff.mul(z0, d_sq);
        let sx0 = if unit_zu0 {
            ff.add(ff.mul(self.s_m, x0), ff.mul(self.x0_m, z0))
        } else {
            ff.mul(self.s_m, x0)
        };
        let x_j = ff.mul(sx0, z0_d_sq);
        let y_j = ff.mul(ff.mul(self.s_m, num_v), z0_d_sq);
        (x_j, y_j, z_j)
    }

    /// Compute `[k]P` on `E(F_p)` via the Montgomery `XZ` ladder (`5M + 4S`/bit)
    /// and Okeya–Sakurai `y`-recovery (`1` field inversion).
    #[inline]
    pub fn scalar_mul(&self, pt: Option<(u64, u64)>, k: u64) -> Option<(u64, u64)> {
        if self.fast_2iso.is_some() {
            return self.jacobian_to_affine(self.scalar_mul_jacobian(pt, k));
        }
        let (in_x, in_y) = pt?;
        if k == 0 {
            return None;
        }
        let (k_eff, px, py) = if let Some((ref phi, _, ell_inv, r_ord)) = self.outer {
            let k_mod = ((k as u128 * ell_inv as u128) % r_ord as u128) as u64;
            if k_mod == 0 {
                return None;
            }
            let (qx, qy) = phi.evaluate(in_x, in_y)?;
            (k_mod, qx, qy)
        } else {
            (k, in_x, in_y)
        };

        let cod_pt = self.ladder_montgomery(px, py, k_eff);
        if let Some((_, ref dual, _, _)) = self.outer {
            let (cx, cy) = cod_pt?;
            dual.evaluate(cx, cy)
        } else {
            cod_pt
        }
    }

    #[inline]
    fn ladder_montgomery(&self, x: u64, y: u64, k: u64) -> Option<(u64, u64)> {
        let ff = &self.ff;
        let p = ff.modulus();
        let xm = ff.to_mont(x % p);
        let ym = ff.to_mont(y % p);
        let u0 = ff.mul(ff.sub(xm, self.x0_m), self.s_inv_m);
        let v0 = ff.mul(ym, self.s_inv_m);
        if v0 == 0 {
            // Order-2 point on E_cod.
            return if k & 1 == 0 { None } else { Some((x % p, 0)) };
        }

        let mut x0 = ff.one();
        let mut z0 = 0u64;
        let mut x1 = u0;
        let mut z1 = ff.one();

        let top = 63 - k.leading_zeros();
        for bit in (0..=top).rev() {
            let b = (k >> bit) & 1;
            if b == 1 {
                std::mem::swap(&mut x0, &mut x1);
                std::mem::swap(&mut z0, &mut z1);
            }
            // Normalised xDBLAD: 5M + 4S (since Z_{P-Q} = 1).
            let t0 = ff.add(x0, z0);
            let t1 = ff.sub(x0, z0);
            let t2 = ff.add(x1, z1);
            let t3 = ff.sub(x1, z1);
            let da = ff.mul(t0, t3);
            let cb = ff.mul(t1, t2);
            let x_add = ff.sqr(ff.add(da, cb));
            let z_add = ff.mul(u0, ff.sqr(ff.sub(da, cb)));
            let aa = ff.sqr(t0);
            let bb = ff.sqr(t1);
            let ee = ff.sub(aa, bb);
            let x_dbl = ff.mul(aa, bb);
            let z_dbl = ff.mul(ee, ff.add(bb, ff.mul(self.a24_m, ee)));

            if b == 1 {
                x0 = x_add;
                z0 = z_add;
                x1 = x_dbl;
                z1 = z_dbl;
            } else {
                x0 = x_dbl;
                z0 = z_dbl;
                x1 = x_add;
                z1 = z_add;
            }
        }

        if z0 == 0 {
            return None;
        }
        if z1 == 0 {
            // [k+1]Q = O ⟹ [k]Q = -Q.
            let neg_y = if y % p == 0 { 0 } else { p - (y % p) };
            return Some((x % p, neg_y));
        }

        // Projective Okeya–Sakurai y-recovery with ONE shared field inversion.
        let one = ff.one();
        let t1 = ff.add(ff.mul(x0, u0), z0);
        let t2 = ff.add(x0, ff.mul(ff.add(u0, self.two_am_m), z0));
        let z0_sq = ff.sqr(z0);
        let left = ff.mul(ff.sub(ff.mul(t1, t2), ff.mul(self.two_am_m, z0_sq)), z1);
        let right = ff.mul(ff.sqr(ff.sub(x0, ff.mul(u0, z0))), x1);
        let num_v = ff.sub(left, right);

        let two_bm_v0 = ff.dbl(ff.mul(self.bm_m, v0));
        let two_bm_v0_z0_z1 = ff.mul(two_bm_v0, ff.mul(z0, z1));
        let den = ff.mul(two_bm_v0_z0_z1, z0);
        let den_inv = ff.inv(den);
        let _ = one;

        let v_k = ff.mul(num_v, den_inv);
        let z0_inv = ff.mul(two_bm_v0_z0_z1, den_inv);
        let u_k = ff.mul(x0, z0_inv);

        let rx = ff.add(ff.mul(self.s_m, u_k), self.x0_m);
        let ry = ff.mul(self.s_m, v_k);
        Some((ff.from_mont(rx), ff.from_mont(ry)))
    }
}

// ── Small-Discriminant CM Endomorphism GLV-2 (D ∈ {-7, -8}, Aut(E) = {±1}) ──

#[derive(Clone, Copy, Debug)]
struct JacPt {
    x: u64,
    y: u64,
    z: u64,
}

impl JacPt {
    #[inline(always)]
    fn infinity(ff: &crate::cryptanalysis::bsgs_fast::FastField) -> Self {
        Self {
            x: ff.one(),
            y: ff.one(),
            z: 0,
        }
    }

    #[inline(always)]
    fn is_infinity(self) -> bool {
        self.z == 0
    }
}

#[inline]
fn jac_neg(p: JacPt, ff: &crate::cryptanalysis::bsgs_fast::FastField) -> JacPt {
    if p.z == 0 {
        p
    } else {
        JacPt {
            x: p.x,
            y: ff.neg(p.y),
            z: p.z,
        }
    }
}

#[inline]
fn jac_dbl(p: JacPt, a_m: u64, ff: &crate::cryptanalysis::bsgs_fast::FastField) -> JacPt {
    if p.z == 0 || p.y == 0 {
        return JacPt::infinity(ff);
    }
    let xx = ff.sqr(p.x);
    let yy = ff.sqr(p.y);
    let yyyy = ff.sqr(yy);
    let zz = ff.sqr(p.z);
    let s = ff.dbl(ff.sub(ff.sqr(ff.add(p.x, yy)), ff.add(xx, yyyy)));
    let three_xx = ff.add(ff.dbl(xx), xx);
    let m = ff.add(three_xx, ff.mul(a_m, ff.sqr(zz)));
    let x3 = ff.sub(ff.sqr(m), ff.dbl(s));
    let eight_yyyy = ff.dbl(ff.dbl(ff.dbl(yyyy)));
    let y3 = ff.sub(ff.mul(m, ff.sub(s, x3)), eight_yyyy);
    let z3 = ff.sub(ff.sqr(ff.add(p.y, p.z)), ff.add(yy, zz));
    JacPt {
        x: x3,
        y: y3,
        z: z3,
    }
}

#[inline]
fn jac_add(p: JacPt, q: JacPt, a_m: u64, ff: &crate::cryptanalysis::bsgs_fast::FastField) -> JacPt {
    if p.z == 0 {
        return q;
    }
    if q.z == 0 {
        return p;
    }
    let z1z1 = ff.sqr(p.z);
    let z2z2 = ff.sqr(q.z);
    let u1 = ff.mul(p.x, z2z2);
    let u2 = ff.mul(q.x, z1z1);
    let s1 = ff.mul(p.y, ff.mul(q.z, z2z2));
    let s2 = ff.mul(q.y, ff.mul(p.z, z1z1));
    if u1 == u2 {
        return if s1 == s2 {
            jac_dbl(p, a_m, ff)
        } else {
            JacPt::infinity(ff)
        };
    }
    let h = ff.sub(u2, u1);
    let i = ff.sqr(ff.dbl(h));
    let j = ff.mul(h, i);
    let r = ff.dbl(ff.sub(s2, s1));
    let v = ff.mul(u1, i);
    let x3 = ff.sub(ff.sub(ff.sqr(r), j), ff.dbl(v));
    let y3 = ff.sub(ff.mul(r, ff.sub(v, x3)), ff.dbl(ff.mul(s1, j)));
    let z3 = ff.mul(ff.sub(ff.sqr(ff.add(p.z, q.z)), ff.add(z1z1, z2z2)), h);
    JacPt {
        x: x3,
        y: y3,
        z: z3,
    }
}

#[inline]
fn jac_scalar_mul(
    mut k: u64,
    p: JacPt,
    a_m: u64,
    ff: &crate::cryptanalysis::bsgs_fast::FastField,
) -> JacPt {
    let mut acc = JacPt::infinity(ff);
    let mut base = p;
    while k != 0 {
        if k & 1 == 1 {
            acc = jac_add(acc, base, a_m, ff);
        }
        k >>= 1;
        if k != 0 {
            base = jac_dbl(base, a_m, ff);
        }
    }
    acc
}

/// 2-dimensional GLV scalar multiplication driven by an explicit degree-2 Vélu
/// Complex-Multiplication endomorphism `ψ = ι_u ∘ φ₂ ∈ End(E)` on ordinary
/// curves with CM by `D ∈ {-7, -8}` (`j ∈ {-3375, 8000}`), where
/// `Aut(E) = {±1}` admits **no** non-trivial curve automorphisms!
///
/// Evaluates `ψ(P)` in projective Jacobian coordinates with `4M + 1S` and
/// **zero** inversions, decomposes `k ≡ k₁ + k₂ λ (mod r)` via half-GCD +
/// Babai rounding (`|k₁|, |k₂| ≲ √r`), and executes a 2-bit `4×4` Shamir
/// cascade in `FastField` Montgomery arithmetic.
#[derive(Clone, Copy, Debug)]
pub struct CmVeluGlv2 {
    ff: crate::cryptanalysis::bsgs_fast::FastField,
    a_m: u64,
    x0_m: u64,
    t0_m: u64,
    u_m: u64,
    r_ord: u64,
    lambda: u64,
    v1: (i128, i128),
    v2: (i128, i128),
}

impl CmVeluGlv2 {
    /// Construct from a rational 2-torsion abscissa `x0` on `curve` (`E: y² = x³ + ax + b`),
    /// prime subgroup order `r_ord`, and a subgroup generator `gen = (gx, gy)`.
    ///
    /// Automatically verifies that Vélu's 2-isogeny codomain at `x0` is
    /// `F_p`-isomorphic to `E` (`A' = u⁴ a, B' = u⁶ b`), solves the quadratic
    /// CM eigenvalue equation `λ² − τ λ + 2 ≡ 0 (mod r)` (`τ ∈ {0, ±1}`),
    /// matches the sign of `u` to `ψ(G) = [λ]G`, and reduces the 2D GLV
    /// lattice via half-GCD.
    pub fn new(curve: &SmallCurve, x0: u64, r_ord: u64, gen: (u64, u64)) -> Option<Self> {
        use crate::cryptanalysis::bsgs_fast::FastField;
        use crate::isogeny::cm::{legendre_u64, tonelli_shanks_u64};

        let p = curve.p;
        if curve.a % p == 0 || curve.b % p == 0 || curve.rhs(x0 % p) != 0 || r_ord < 5 {
            return None;
        }
        let ff = FastField::new(p)?;
        let a_m = ff.to_mont(curve.a % p);
        let b_m = ff.to_mont(curve.b % p);
        let x0_m = ff.to_mont(x0 % p);
        let x0_2 = ff.sqr(x0_m);
        let t0_m = ff.add(ff.add(ff.dbl(x0_2), x0_2), a_m);
        let w0_m = ff.mul(x0_m, t0_m);
        let five_t0 = ff.add(ff.dbl(ff.dbl(t0_m)), t0_m);
        let seven_w0 = ff.sub(ff.dbl(ff.dbl(ff.dbl(w0_m))), w0_m);
        let ap_m = ff.sub(a_m, five_t0);
        let bp_m = ff.sub(b_m, seven_w0);
        if ap_m == 0 || bp_m == 0 {
            return None;
        }
        // u^4 = A'/a, u^6 = B'/b => u^2 = (B'/b) * (a/A').
        let ratio_a = ff.mul(ap_m, ff.inv(a_m));
        let ratio_b = ff.mul(bp_m, ff.inv(b_m));
        let u2_m = ff.mul(ratio_b, ff.inv(ratio_a));
        if ff.sqr(u2_m) != ratio_a || ff.mul(u2_m, ratio_a) != ratio_b {
            return None;
        }
        let u2_can = ff.from_mont(u2_m);
        if legendre_u64(u2_can, p) != 1 {
            return None;
        }
        let u_pos = tonelli_shanks_u64(u2_can, p)?;
        let u_pos_m = ff.to_mont(u_pos);

        // Candidate eigenvalues λ ∈ [1, r_ord): λ² - τ λ + 2 ≡ 0 (mod r_ord), τ ∈ {0, 1, -1}.
        let mut cands = Vec::with_capacity(6);
        if r_ord > 2 && legendre_u64(r_ord - 2, r_ord) == 1 {
            if let Some(s) = tonelli_shanks_u64(r_ord - 2, r_ord) {
                cands.push(s);
                if s != 0 {
                    cands.push(r_ord - s);
                }
            }
        }
        if r_ord > 7 && legendre_u64(r_ord - 7, r_ord) == 1 {
            if let Some(s) = tonelli_shanks_u64(r_ord - 7, r_ord) {
                let inv2 = (r_ord + 1) / 2;
                for root in [s, r_ord - s] {
                    for tau in [1u64, r_ord - 1] {
                        let lam =
                            (((tau + root) % r_ord) as u128 * inv2 as u128 % r_ord as u128) as u64;
                        cands.push(lam);
                    }
                }
            }
        }

        let g_jac = JacPt {
            x: ff.to_mont(gen.0 % p),
            y: ff.to_mont(gen.1 % p),
            z: ff.one(),
        };
        let mut chosen = None;
        for &u_cand_m in &[u_pos_m, ff.neg(u_pos_m)] {
            let w = ff.sub(g_jac.x, x0_m);
            if w == 0 {
                continue;
            }
            let w2 = ff.sqr(w);
            let psi_g = JacPt {
                x: ff.mul(w, ff.add(ff.mul(g_jac.x, w), t0_m)),
                y: ff.mul(g_jac.y, ff.sub(w2, t0_m)),
                z: ff.mul(u_cand_m, w),
            };
            for &lam in &cands {
                let lg = jac_scalar_mul(lam, g_jac, a_m, &ff);
                if lg.z != 0 {
                    let z1_2 = ff.sqr(psi_g.z);
                    let z2_2 = ff.sqr(lg.z);
                    if ff.mul(psi_g.x, z2_2) == ff.mul(lg.x, z1_2)
                        && ff.mul(psi_g.y, ff.mul(lg.z, z2_2))
                            == ff.mul(lg.y, ff.mul(psi_g.z, z1_2))
                    {
                        chosen = Some((u_cand_m, lam));
                        break;
                    }
                }
            }
            if chosen.is_some() {
                break;
            }
        }
        let (u_m, lambda) = chosen?;

        // Half-GCD on (r_ord, 0) and (-lambda, 1).
        let bound = (r_ord as f64).sqrt() as i128 + 1;
        let (mut r0, mut r1) = (r_ord as i128, lambda as i128);
        let (mut t0, mut t1) = (0i128, 1i128);
        while r1 >= bound {
            let q = r0 / r1;
            let nr = r0 - q * r1;
            let nt = t0 - q * t1;
            r0 = r1;
            r1 = nr;
            t0 = t1;
            t1 = nt;
        }
        let v1 = (r1, -t1);
        let cand_a = (r0, -t0);
        let (r2, t2) = if r1 != 0 {
            let q = r0 / r1;
            (r0 - q * r1, t0 - q * t1)
        } else {
            (r0, t0)
        };
        let cand_b = (r2, -t2);
        let norm_a = cand_a.0 * cand_a.0 + cand_a.1 * cand_a.1;
        let norm_b = cand_b.0 * cand_b.0 + cand_b.1 * cand_b.1;
        let v2 = if norm_a <= norm_b { cand_a } else { cand_b };

        Some(Self {
            ff,
            a_m,
            x0_m,
            t0_m,
            u_m,
            r_ord,
            lambda,
            v1,
            v2,
        })
    }

    #[inline]
    pub fn lambda(&self) -> u64 {
        self.lambda
    }

    #[inline]
    fn eval_psi_jacobian(&self, xm: u64, ym: u64) -> JacPt {
        let ff = &self.ff;
        let w = ff.sub(xm, self.x0_m);
        if w == 0 {
            return JacPt::infinity(ff);
        }
        let w2 = ff.sqr(w);
        JacPt {
            x: ff.mul(w, ff.add(ff.mul(xm, w), self.t0_m)),
            y: ff.mul(ym, ff.sub(w2, self.t0_m)),
            z: ff.mul(self.u_m, w),
        }
    }

    #[inline]
    fn round_div_i128(num: i128, den: i128) -> i128 {
        let (n, d) = if den < 0 { (-num, -den) } else { (num, den) };
        if n >= 0 {
            (n + (d >> 1)) / d
        } else {
            (n - (d >> 1)) / d
        }
    }

    /// Zero-inversion projective CM GLV-2 scalar multiplication `[k]P`,
    /// returning canonical Jacobian coordinates `(X : Y : Z)` (`Z == 0` for `O`).
    #[inline]
    pub fn scalar_mul_jacobian(&self, pt: Option<(u64, u64)>, k: u64) -> (u64, u64, u64) {
        let Some((in_x, in_y)) = pt else {
            return (1, 1, 0);
        };
        let k_mod = k % self.r_ord;
        if k_mod == 0 {
            return (1, 1, 0);
        }
        let ff = &self.ff;
        let p = ff.modulus();
        let xm = ff.to_mont(in_x % p);
        let ym = ff.to_mont(in_y % p);

        let det = self.v1.0 * self.v2.1 - self.v1.1 * self.v2.0;
        let ki = k_mod as i128;
        let b1 = Self::round_div_i128(ki * self.v2.1, det);
        let b2 = Self::round_div_i128(-(ki * self.v1.1), det);
        let k1 = ki - b1 * self.v1.0 - b2 * self.v2.0;
        let k2 = -(b1 * self.v1.1 + b2 * self.v2.1);

        let p_base = JacPt {
            x: xm,
            y: ym,
            z: ff.one(),
        };
        let p1 = if k1 < 0 { jac_neg(p_base, ff) } else { p_base };
        let psi = self.eval_psi_jacobian(xm, ym);
        let p2 = if k2 < 0 { jac_neg(psi, ff) } else { psi };

        let u1 = k1.unsigned_abs() as u64;
        let u2 = k2.unsigned_abs() as u64;
        let or_u = u1 | u2;
        if or_u == 0 {
            return (1, 1, 0);
        }

        let p1_2 = jac_dbl(p1, self.a_m, ff);
        let p1_3 = jac_add(p1_2, p1, self.a_m, ff);
        let row1 = [JacPt::infinity(ff), p1, p1_2, p1_3];

        let p2_2 = jac_dbl(p2, self.a_m, ff);
        let p2_3 = jac_add(p2_2, p2, self.a_m, ff);
        let row2 = [JacPt::infinity(ff), p2, p2_2, p2_3];

        let mut tab = [JacPt::infinity(ff); 16];
        for d2 in 0..4 {
            for d1 in 0..4 {
                tab[d1 + 4 * d2] = match (d1, d2) {
                    (0, 0) => JacPt::infinity(ff),
                    (_, 0) => row1[d1],
                    (0, _) => row2[d2],
                    _ => jac_add(row1[d1], row2[d2], self.a_m, ff),
                };
            }
        }

        let top_bits = (64 - or_u.leading_zeros()) as usize;
        let top_pair = top_bits.div_ceil(2);
        let mut acc = JacPt::infinity(ff);
        for step in (0..top_pair).rev() {
            if !acc.is_infinity() {
                acc = jac_dbl(jac_dbl(acc, self.a_m, ff), self.a_m, ff);
            }
            let sh = 2 * step;
            let d1 = ((u1 >> sh) & 3) as usize;
            let d2 = ((u2 >> sh) & 3) as usize;
            let idx = d1 + 4 * d2;
            if idx != 0 {
                acc = if acc.is_infinity() {
                    tab[idx]
                } else {
                    jac_add(acc, tab[idx], self.a_m, ff)
                };
            }
        }
        if acc.is_infinity() {
            (1, 1, 0)
        } else {
            (
                ff.from_mont(acc.x),
                ff.from_mont(acc.y),
                ff.from_mont(acc.z),
            )
        }
    }

    /// Affine CM GLV-2 scalar multiplication `[k]P` (`1` final inversion).
    #[inline]
    pub fn scalar_mul(&self, pt: Option<(u64, u64)>, k: u64) -> Option<(u64, u64)> {
        let (x, y, z) = self.scalar_mul_jacobian(pt, k);
        if z == 0 {
            return None;
        }
        let ff = &self.ff;
        let zm = ff.to_mont(z);
        if zm == ff.one() {
            return Some((x, y));
        }
        let zi = ff.inv(zm);
        let zi2 = ff.sqr(zi);
        let rx = ff.mul(ff.to_mont(x), zi2);
        let ry = ff.mul(ff.to_mont(y), ff.mul(zi2, zi));
        Some((ff.from_mont(rx), ff.from_mont(ry)))
    }
}

// ── Unit tests ───────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use crate::isogeny::toy_curve_a;

    #[test]
    fn two_isogeny_round_trip() {
        // On the toy-2003 curve, search for a 2-torsion point and
        // build the 2-isogeny.  Codomain should be a valid curve
        // with non-zero discriminant.
        let curve = toy_curve_a();
        let mut found = None;
        for x in 0..curve.p {
            if curve.rhs(x) == 0 {
                found = Some(x);
                break;
            }
        }
        if let Some(x_t) = found {
            let iso = velu_isogeny_2(&curve, x_t).expect("2-iso constructs");
            assert_eq!(iso.degree, 2);
            // Codomain is a *different* curve (unless x_T is degenerate).
            assert!(iso.codomain.p == curve.p);
        }
    }

    #[test]
    fn three_isogeny_count_for_toy() {
        // On a small ordinary curve, the number of 3-isogenies is
        // bounded by the number of order-3 cyclic subgroups, which
        // is 0, 1, 2, or 4 depending on rank of E[3].
        let curve = toy_curve_a();
        let isos = velu_isogeny_odd(&curve, 3);
        assert!(isos.len() <= 4, "got {} 3-isogenies", isos.len());
    }

    // ── The transfer that lever L5 rests on ───────────────────────────────
    //
    // `research/notes/ecc2k130/RESEARCH_ISOGENY_CLASS_SEARCH.md` opens by
    // asserting that "the ECDLP transports along an isogeny of degree
    // coprime to the subgroup order".  §1.1 of that note derives it; these
    // two tests are what make it a checked statement rather than a cited
    // one, and they are the reason the thread may treat every curve in the
    // class as carrying the same discrete logarithm.

    use crate::ecc::field::FieldElement;
    use crate::ecc::point::Point;

    fn pt(x: u64, y: u64, p: u64) -> Point {
        Point::Affine {
            x: FieldElement::new(BigUint::from(x), BigUint::from(p)),
            y: FieldElement::new(BigUint::from(y), BigUint::from(p)),
        }
    }

    fn xy(point: &Point) -> Option<(u64, u64)> {
        match point {
            Point::Affine { x, y } => Some((
                x.value.iter_u64_digits().next().unwrap_or(0),
                y.value.iter_u64_digits().next().unwrap_or(0),
            )),
            Point::Infinity => None,
        }
    }

    /// An isogeny is a group homomorphism, so `φ([k]P) = [k]φ(P)` and the
    /// discrete logarithm crosses **unchanged** — no factor of the degree
    /// appears anywhere in the transfer.
    ///
    /// `toy_curve_a` has `#E = 2019 = 3 · 673`, so with `ℓ = 3` the kernel
    /// has order 3 and `⟨P⟩` has prime order `n = 673`.  `gcd(3, 673) = 1`
    /// makes `φ` injective on `⟨P⟩`, which is exactly the note's side
    /// condition.  Every `k` in `1..n` is checked, not a sample.
    #[test]
    fn transfer_preserves_the_discrete_logarithm() {
        let curve = toy_curve_a();
        let (ell, n) = (3u64, 673u64);
        assert_eq!(2019, ell * n, "toy_curve_a order must factor as 3 · 673");
        assert_eq!(
            1,
            num_integer::gcd(ell, n),
            "side condition gcd(deg, n) = 1"
        );

        let iso = velu_isogeny_odd(&curve, ell)
            .into_iter()
            .next()
            .expect("toy_curve_a admits a 3-isogeny");

        let dom = curve.to_curve_params();
        let cod = iso.codomain.to_curve_params();
        let (a_dom, a_cod) = (dom.a_fe(), cod.a_fe());

        // A generator of the order-n subgroup: kill the cofactor ℓ.
        let mut rng: u64 = 0x5DEE_CE66_D4A5_1B2D;
        let base = loop {
            if let Some(p0) = crate::isogeny::cm::sample_random_point(&curve, &mut rng) {
                let q = p0.scalar_mul(&BigUint::from(ell), &a_dom);
                if !matches!(q, Point::Infinity) {
                    break q;
                }
            }
        };
        assert!(
            matches!(base.scalar_mul(&BigUint::from(n), &a_dom), Point::Infinity),
            "base point must have order n"
        );

        let (bx, by) = xy(&base).expect("base is affine");
        let image = iso.evaluate(bx, by).expect("P is not in ker φ");
        let p_img = pt(image.0, image.1, iso.codomain.p);

        // φ([k]P) == [k]φ(P) for every k in 1..n.
        for k in 1..n {
            let kp = base.scalar_mul(&BigUint::from(k), &a_dom);
            let (kx, ky) = xy(&kp).expect("[k]P affine for 0 < k < n");
            let lhs = iso.evaluate(kx, ky).expect("[k]P not in ker φ");
            let rhs = xy(&p_img.scalar_mul(&BigUint::from(k), &a_cod)).expect("[k]φ(P) affine");
            assert_eq!(
                lhs, rhs,
                "φ([{k}]P) != [{k}]φ(P) — the log did not transfer"
            );
        }
    }

    /// Regression pin for the `v(Q)` formula.  Until 2026-09, this module
    /// used `v(Q) = 4 x_Q g_y(Q)² + 2 g_x(Q)²` for non-2-torsion `Q`, which
    /// is not Vélu's: the correct value is `2 g_x(Q)` (and `g_x(Q)` on the
    /// T-row).  The bug was invisible to the older tests because they only
    /// checked a subgroup *count* and that the codomain shared the domain's
    /// prime — never that a point's image satisfies the codomain equation,
    /// which it did not.
    ///
    /// The expected values here come from an independent implementation
    /// cross-checked for the homomorphism property; they are not read back
    /// from this code.
    #[test]
    fn codomain_and_image_match_an_independent_reference() {
        let curve = toy_curve_a();
        let iso = velu_isogeny_odd(&curve, 3)
            .into_iter()
            .next()
            .expect("toy_curve_a admits a 3-isogeny");

        assert_eq!(iso.kernel_half, vec![(594u64, 805u64)], "kernel generator");
        assert_eq!(
            (iso.codomain.a, iso.codomain.b),
            (739, 792),
            "Vélu codomain"
        );
        assert_eq!(
            iso.evaluate(24, 118),
            Some((643, 1661)),
            "image of (24, 118)"
        );

        // …and the image really is a point of the codomain.
        let (p, a2, b2) = (
            curve.p as u128,
            iso.codomain.a as u128,
            iso.codomain.b as u128,
        );
        let (x, y) = iso.evaluate(24, 118).expect("not in kernel");
        let (x, y) = (x as u128, y as u128);
        assert_eq!(
            y * y % p,
            (x * x % p * x % p + a2 * x % p + b2) % p,
            "φ(P) must satisfy the codomain equation"
        );
    }

    /// The side condition, from the other direction: `ker φ ∩ ⟨P⟩` is a
    /// subgroup of a group of prime order `n`, so it is trivial unless
    /// `n | deg φ`.  Kernel points themselves must die.
    #[test]
    fn kernel_points_die_and_the_subgroup_survives() {
        let curve = toy_curve_a();
        let iso = velu_isogeny_odd(&curve, 3)
            .into_iter()
            .next()
            .expect("toy_curve_a admits a 3-isogeny");

        for &(kx, ky) in &iso.kernel_half {
            assert!(
                iso.evaluate(kx, ky).is_none(),
                "kernel point ({kx}, {ky}) should map to the point at infinity"
            );
        }
        assert_eq!(
            iso.kernel_half.len() as u64,
            (iso.degree - 1) / 2,
            "half-set of a degree-{} kernel has (ℓ-1)/2 points",
            iso.degree
        );
    }

    #[test]
    fn isogeny2_doubler_and_montgomery_bridge_match_textbook() {
        // Curve E: y² = x³ − 11x + 14 over F_65537 (translated from y² = u³ + 6u² + u at x0 = 2).
        let p = 65537u64;
        let curve = SmallCurve {
            name: "mont-bridge-65537",
            p,
            a: p - 11,
            b: 14,
        };
        let cp = curve.to_curve_params();
        let a_fe = cp.a_fe();
        let doubler = Isogeny2Doubler::new(&curve, 2).expect("2-isogeny doubler builds");
        let bridge = MontgomeryIsogenyBridge::new_direct(&curve, 2).expect("direct bridge builds");

        // Find a generic point (gx = 5) and an order-4 point (gx = 3, where [2]P = (2, 0)).
        let y5 = crate::isogeny::cm::tonelli_shanks_u64(curve.rhs(5), p).unwrap();
        let p5 = pt(5, y5, p);
        let y3 = crate::isogeny::cm::tonelli_shanks_u64(curve.rhs(3), p).unwrap();
        let p3 = pt(3, y3, p);

        // Edge case: order-4 point whose double is (2, 0) and quadruple is O.
        assert_eq!(doubler.double_affine(Some((3, y3))), xy(&p3.double(&a_fe)));
        assert_eq!(doubler.double_k_affine(Some((3, y3)), 2), None);
        for k in 1..=8u64 {
            assert_eq!(
                bridge.scalar_mul(Some((3, y3)), k),
                xy(&p3.scalar_mul(&BigUint::from(k), &a_fe)),
                "order-4 point mismatch at k={k}"
            );
        }

        // Sweep 128 scalars on the generic point.
        for k in 1..=128u64 {
            let pk = p5.scalar_mul(&BigUint::from(k), &a_fe);
            let got_bridge = bridge.scalar_mul(Some((5, y5)), k);
            assert_eq!(got_bridge, xy(&pk), "bridge mismatch at k={k}");
            let got_jac = bridge.jacobian_to_affine(bridge.scalar_mul_jacobian(Some((5, y5)), k));
            assert_eq!(got_jac, xy(&pk), "0-inv jacobian bridge mismatch at k={k}");
            if let Some(coords) = xy(&pk) {
                assert_eq!(
                    doubler.double_affine(Some(coords)),
                    xy(&pk.double(&a_fe)),
                    "2-isogeny double mismatch at k={k}"
                );
            }
        }
    }

    #[test]
    fn zero_inv_2iso_bridge_and_cm_velu_glv2_d7_d8_match_reference() {
        // 1. Curve with NO direct Montgomery model at x0=4 over F_108087495404080729:
        //    E_{-8}: y^2 = x^3 - 30x + 56 (CM by Z[sqrt(-2)], D = -8, j = 8000).
        //    At x0 = 4: 3*4^2 - 30 = 18; check whether new_2iso_zero_inv or new_direct works,
        //    and verify CmVeluGlv2 on BOTH D = -8 and D = -7!
        let p8 = 108_087_495_404_080_729u64;
        let r8 = 27_021_873_716_802_043u64;
        let curve_d8 = SmallCurve {
            name: "cm-d8-57b",
            p: p8,
            a: p8 - 30,
            b: 56,
        };
        let cp8 = curve_d8.to_curve_params();
        let a8 = cp8.a_fe();
        let mut rng = 0x1234_5678_9ABC_DEF0u64;
        let gen8 = loop {
            if let Some(p0) = crate::isogeny::cm::sample_random_point(&curve_d8, &mut rng) {
                let q = p0.scalar_mul(&BigUint::from(4u64), &a8);
                if !matches!(q, Point::Infinity) {
                    break q;
                }
            }
        };
        assert!(matches!(
            gen8.scalar_mul(&BigUint::from(r8), &a8),
            Point::Infinity
        ));
        let g8 = xy(&gen8).unwrap();
        let glv_d8 = CmVeluGlv2::new(&curve_d8, 4, r8, g8).expect("CM D=-8 GLV-2 builds");
        for &k in &[1u64, 2, 3, 17, 0xDEAD_BEEF_CAFE, r8 - 1, r8 / 3 + 77] {
            let want = xy(&gen8.scalar_mul(&BigUint::from(k), &a8));
            assert_eq!(
                glv_d8.scalar_mul(Some(g8), k),
                want,
                "CM D=-8 mismatch at k={k}"
            );
        }

        // 2. CM by O_{-7} (D = -7, j = -3375): E_{-7}: y^2 = x^3 - 35x + 98 over 58-bit prime.
        //    Roots of x^2 - 7x + 14 ≡ 0 (mod p7) give the degree-2 CM endomorphism ψ = (1±√-7)/2!
        let p7 = 144_116_352_954_942_391u64;
        let r7 = 18_014_544_203_254_097u64;
        let curve_d7 = SmallCurve {
            name: "cm-d7-58b",
            p: p7,
            a: p7 - 35,
            b: 98,
        };
        let cp7 = curve_d7.to_curve_params();
        let a7 = cp7.a_fe();
        let sqrt_neg7 = crate::isogeny::cm::tonelli_shanks_u64(p7 - 7, p7).unwrap();
        let inv2_p7 = (p7 + 1) / 2;
        let x0_d7 = (((7 + sqrt_neg7) % p7) as u128 * inv2_p7 as u128 % p7 as u128) as u64;
        assert_eq!(curve_d7.rhs(x0_d7), 0);
        let gen7 = loop {
            if let Some(p0) = crate::isogeny::cm::sample_random_point(&curve_d7, &mut rng) {
                let q = p0.scalar_mul(&BigUint::from(8u64), &a7);
                if !matches!(q, Point::Infinity) {
                    break q;
                }
            }
        };
        assert!(matches!(
            gen7.scalar_mul(&BigUint::from(r7), &a7),
            Point::Infinity
        ));
        let g7 = xy(&gen7).unwrap();
        let glv_d7 = CmVeluGlv2::new(&curve_d7, x0_d7, r7, g7).expect("CM D=-7 GLV-2 builds");
        for &k in &[1u64, 2, 5, 42, 0x1234_5678_9ABC, r7 - 1, r7 / 5 + 99] {
            let want = xy(&gen7.scalar_mul(&BigUint::from(k), &a7));
            assert_eq!(
                glv_d7.scalar_mul(Some(g7), k),
                want,
                "CM D=-7 mismatch at k={k}"
            );
        }

        // 3. Zero-inversion 2-isogeny Montgomery bridge on a curve whose 2-torsion
        //    root x0 = 0 has 3*x0^2 + a NON-SQUARE in F_p, while B' = -4a IS a square?
        //    Find any small prime curve where new_direct(x0) is None and new_2iso_zero_inv(x0) is Some!
        //    Take p = 2003 (p ≡ 3 mod 4, so -1 is non-square): x0 = 1, a = 1 =>
        //    B_tr = 3 + 1 = 4 (square), try x0 = 2, a = 2003 - 13 = 1990 =>
        //    B_tr = 12 - 13 = -1 (NON-SQUARE mod 2003!), while A_tr^2 - 4 B_tr = 36 + 4 = 40!
        //    Check legendre(40, 2003): 40 = 4 * 10; if non-square, search a in 1..50!
        let p_br = 2003u64;
        let mut tested_2iso = false;
        for a_cand in 1..100u64 {
            let x0 = 2u64;
            let b_cand = (p_br - ((8 + a_cand * x0) % p_br)) % p_br;
            let c_br = SmallCurve {
                name: "no-direct-mont",
                p: p_br,
                a: a_cand,
                b: b_cand,
            };
            let disc = (4 * a_cand.pow(3) + 27 * b_cand * b_cand) % p_br;
            if disc != 0 && MontgomeryIsogenyBridge::new_direct(&c_br, x0).is_none() {
                let ord = (p_br as i64 + 1 - crate::isogeny::cm::frobenius_trace(&c_br)) as u64;
                let mut odd_r = ord;
                while odd_r % 2 == 0 {
                    odd_r /= 2;
                }
                if odd_r > 25 {
                    if let Some(br2) = MontgomeryIsogenyBridge::new_2iso_zero_inv(&c_br, x0, odd_r)
                    {
                        let cp_b = c_br.to_curve_params();
                        let ab = cp_b.a_fe();
                        let cof = ord / odd_r;
                        let gb_pt = loop {
                            if let Some(p0) =
                                crate::isogeny::cm::sample_random_point(&c_br, &mut rng)
                            {
                                let q = p0.scalar_mul(&BigUint::from(cof), &ab);
                                if !matches!(q, Point::Infinity) {
                                    break q;
                                }
                            }
                        };
                        let gb = xy(&gb_pt).unwrap();
                        for k in 1..30u64 {
                            let want = xy(&gb_pt.scalar_mul(&BigUint::from(k), &ab));
                            let got = br2.jacobian_to_affine(br2.scalar_mul_jacobian(Some(gb), k));
                            assert_eq!(got, want, "new_2iso_zero_inv mismatch at k={k}");
                        }
                        tested_2iso = true;
                        break;
                    }
                }
            }
        }
        assert!(
            tested_2iso,
            "must find and verify a curve with no direct Montgomery model"
        );
    }
}
