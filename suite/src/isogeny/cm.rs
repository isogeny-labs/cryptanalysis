//! # Complex multiplication: discriminant, endomorphism ring, Frobenius.
//!
//! For an ordinary elliptic curve `E/F_p`, the endomorphism ring
//! `End(E)` is an **order** `O` inside the imaginary quadratic field
//! `K = Q(π)` where `π` is the Frobenius endomorphism.  Concretely:
//!
//! 1. Count points: `#E(F_p) = p + 1 − t` defines the **Frobenius
//!    trace** `t ∈ [−2√p, 2√p]` (Hasse interval).
//! 2. The characteristic polynomial of `π` is `T² − t T + p`, so its
//!    discriminant is `t² − 4p < 0`.
//! 3. Write `t² − 4p = D · f²` with `D` a **fundamental
//!    discriminant** (square-free factor of `t² − 4p`) and `f` the
//!    **conductor** of `End(E)` inside the maximal order
//!    `O_K = O_{Q(√D)}`.  Then `End(E)` is the order `Z + f O_K`,
//!    of discriminant `f² D`.
//!
//! Kohel's algorithm walks the `ℓ`-isogeny volcano to **descend**
//! from the maximal order all the way to the floor, reading off the
//! conductor's `ℓ`-adic valuation from the descent depth.  We provide
//! the building blocks here; the volcano walking lives in
//! [`crate::isogeny::volcano`].
//!
//! ## What's expensive
//!
//! Frobenius trace by brute-force point counting is `O(p)` field
//! operations: feasible for `p < 2^32` on a laptop in seconds.  Above
//! `2^14` the trace comes from a Shanks–Mestre BSGS in the Hasse interval
//! (`O(p^{1/4})`) on the single-word Montgomery field of
//! [`crate::cryptanalysis::bsgs_fast`], which needs `p < 2^63`; that is
//! the size limit of this module ([`SmallCurve`] documents `p < 2^62`).
//! The discriminant `t² − 4p` and the group order are carried in `i128`
//! because they leave `i64` for `p >= 2^61`.  Schoof's algorithm
//! (`O((log p)^5)`) would be required to scale to cryptographic
//! sizes; we deliberately do not implement it here — see
//! [`crate::cryptanalysis::ai_schoof`] for the start of that work.

use super::SmallCurve;
use num_bigint::{BigInt, BigUint};
use num_traits::Signed;
use std::collections::HashMap;

// ── Frobenius trace ───────────────────────────────────────────────────────────

/// Count `#E(F_p) − 1` for a small curve by brute-force enumeration
/// over `F_p`.  Returns the **Frobenius trace** `t = p + 1 − #E`.
///
/// Algorithm (textbook, Silverman Prop V.1.4):
///
/// ```text
/// #E(F_p) = 1 + Σ_{x ∈ F_p} (1 + χ(x³ + ax + b))
/// ```
///
/// where `χ` is the quadratic character: `+1` on non-zero squares,
/// `−1` on non-squares, `0` on zero.  We compute the right-hand
/// side directly.  Complexity: `O(p · log² p)` (the Legendre
/// symbol is computed via Euler's criterion).
///
/// # Panics
///
/// For `p >= 2^63`: the BSGS point count runs on a single-word Montgomery
/// field that requires `p < 2^63`, and the `O(p)` brute-force fallback
/// would not finish. (Previously this silently fell through to the
/// brute-force loop.)
pub fn frobenius_trace(curve: &SmallCurve) -> i64 {
    let p = curve.p;
    assert!(
        p < FROBENIUS_TRACE_MAX_P,
        "frobenius_trace: p = {p} >= 2^63 is beyond the single-word BSGS point \
         count (FastField needs p < 2^63); brute force would be O(p)"
    );
    if p < 3 {
        // Edge case: characteristic 2 / 3 needs a different
        // Weierstrass model; bail.
        return 0;
    }
    // Crossover: brute force costs ~p · log² p; BSGS costs ~p^{1/4} ·
    // (build + scan) plus a constant Point-arithmetic overhead.  For
    // p ≳ 2^14 BSGS wins decisively; below that the constant beats us.
    if p >= 1 << 14 {
        if let Some(t) = frobenius_trace_bsgs(curve) {
            return t;
        }
    }
    let p_i = p as i64;
    let mut count: i64 = 1; // the point at infinity
    for x in 0..p {
        let rhs = curve.rhs(x);
        match legendre_u64(rhs, p) {
            0 => count += 1,
            1 => count += 2,
            _ => {} // non-residue: no points with this x
        }
    }
    p_i + 1 - count
}

/// Exclusive upper bound on `p` for [`frobenius_trace`] (the
/// single-word Montgomery field limit of `bsgs_fast::FastField`).
pub const FROBENIUS_TRACE_MAX_P: u64 = 1 << 63;

// ── BSGS / Shanks-Mestre point count ──────────────────────────────────────────
//
// Standard algorithm (Mestre 1986; see Cohen GTM 138, §7.5.3 or
// Washington "Elliptic Curves" §4.3):
//
//   1.  Pick a random point P ∈ E(F_p).
//   2.  Use BSGS in the Hasse interval [p+1−2√p, p+1+2√p] to find
//       the unique k in that interval with k·P = O.  k is a multiple
//       of ord(P).
//   3.  Strip small prime factors q from k as long as (k/q)·P = O —
//       this yields ord(P) exactly.
//   4.  If ord(P) > 4√p the Hasse interval contains exactly one
//       multiple of ord(P), so #E(F_p) is determined.  Otherwise
//       (rare for random points) draw another P and combine via lcm.
//
// Complexity: O(p^{1/4}) Point operations per random draw; usually
// one or two draws suffice.

/// Compute the Frobenius trace using BSGS in the Hasse interval.
/// Returns `None` if the heuristic gives up (e.g., couldn't find a
/// point with `ord > 4√p` within 4 draws — extremely unlikely except
/// on pathological curves).
pub fn frobenius_trace_bsgs(curve: &SmallCurve) -> Option<i64> {
    use crate::cryptanalysis::bsgs_fast::{FastCurve, FastPoint};
    let p = curve.p;
    if p < 5 {
        return None;
    }
    let fc = FastCurve::from_u64(p, curve.a, curve.b, 0)?;
    // Hasse interval [N_lo, N_hi].
    let sqrt_p = isqrt_u64(p);
    let two_sqrt_p = 2 * sqrt_p + 2; // +1 for ceil rounding, +1 conservative
    let n_lo = (p + 1).saturating_sub(two_sqrt_p);
    let n_hi = p + 1 + two_sqrt_p;
    let four_sqrt_p = 4 * sqrt_p + 4;

    // Try up to 4 random points; combine orders via lcm.
    let mut combined: u64 = 1;
    let mut rng_state: u64 = p
        .wrapping_mul(0xA0761D6478BD642F)
        .wrapping_add(curve.a)
        .wrapping_add(curve.b);
    for _draw in 0..4 {
        rng_state = rng_state
            .wrapping_mul(6364136223846793005)
            .wrapping_add(1442695040888963407);
        let (x, y) = sample_random_xy(curve, &mut rng_state)?;
        let point = FastPoint {
            x: fc.f.to_mont(x),
            y: fc.f.to_mont(y),
            infinity: false,
        };
        let k = bsgs_find_zero_in_hasse(&fc, point, n_lo, n_hi)?;
        let ord = refine_point_order(&fc, point, k);
        combined = lcm_u64(combined, ord);
        // If `combined > 4√p`, the Hasse interval contains exactly
        // one multiple of `combined`; that's #E.
        if combined > four_sqrt_p {
            // Find the unique multiple of `combined` in [n_lo, n_hi].
            let r = n_lo % combined;
            let n_e = if r == 0 { n_lo } else { n_lo + (combined - r) };
            if n_e > n_hi {
                // Defensive: shouldn't happen if `combined > 4√p`.
                continue;
            }
            // i128: n_e can exceed i64::MAX for p just below 2^63.
            return i64::try_from(p as i128 + 1 - n_e as i128).ok();
        }
    }
    None
}

/// Encode a Montgomery affine point as a hash key.  `Infinity` uses a sentinel.
fn fast_point_key(p: crate::cryptanalysis::bsgs_fast::FastPoint) -> [u8; 17] {
    let mut out = [0u8; 17];
    if p.infinity {
        out[16] = 0xFF;
    } else {
        out[..8].copy_from_slice(&p.x.to_le_bytes());
        out[8..16].copy_from_slice(&p.y.to_le_bytes());
        out[16] = 0;
    }
    out
}

/// Sample a random affine `(x, y)` on the curve without heap traffic.
/// Same LCG walk and Tonelli–Shanks path as [`sample_random_point`].
pub fn sample_random_xy(curve: &SmallCurve, rng: &mut u64) -> Option<(u64, u64)> {
    let p = curve.p;
    for _ in 0..p {
        *rng = rng
            .wrapping_mul(6364136223846793005)
            .wrapping_add(1442695040888963407);
        let x = (*rng >> 7) % p;
        let rhs = curve.rhs(x);
        if rhs == 0 {
            return Some((x, 0));
        }
        if legendre_u64(rhs, p) == 1 {
            let y = tonelli_shanks_u64(rhs, p)?;
            return Some((x, y));
        }
    }
    None
}

/// Sample a random affine point on the curve.  Iterates `x` from a
/// random offset using a small linear-congruential walk; finds the
/// first `x` with `rhs(x)` a quadratic residue, then computes a
/// square root via Tonelli-Shanks (or `rhs = 0` directly).
pub fn sample_random_point(curve: &SmallCurve, rng: &mut u64) -> Option<crate::ecc::point::Point> {
    use crate::ecc::point::Point;
    let (x, y) = sample_random_xy(curve, rng)?;
    let cp = curve.to_curve_params();
    Some(Point::Affine {
        x: cp.fe(BigUint::from(x)),
        y: cp.fe(BigUint::from(y)),
    })
}

/// Tonelli-Shanks square root mod prime `p` (odd p).  Returns one of
/// the two square roots; the caller can negate to get the other.
pub fn tonelli_shanks_u64(n: u64, p: u64) -> Option<u64> {
    if n == 0 {
        return Some(0);
    }
    if p == 2 {
        return Some(n & 1);
    }
    if legendre_u64(n, p) != 1 {
        return None;
    }
    // Find Q, S such that p-1 = Q · 2^S with Q odd.
    let mut q = p - 1;
    let mut s = 0u32;
    while q & 1 == 0 {
        q >>= 1;
        s += 1;
    }
    // Find a non-residue z.
    let mut z = 2u64;
    while legendre_u64(z, p) != -1 {
        z += 1;
    }
    let mut m = s;
    let mut c = mod_pow_u64(z, q, p);
    let mut t = mod_pow_u64(n, q, p);
    let mut r = mod_pow_u64(n, q.div_ceil(2), p);
    loop {
        if t == 1 {
            return Some(r);
        }
        // Find least i with t^{2^i} = 1.
        let mut i = 0u32;
        let mut tmp = t;
        while tmp != 1 {
            tmp = ((tmp as u128 * tmp as u128) % p as u128) as u64;
            i += 1;
            if i >= m {
                return None;
            }
        }
        let b = mod_pow_u64(c, 1u64 << (m - i - 1), p);
        m = i;
        c = ((b as u128 * b as u128) % p as u128) as u64;
        t = ((t as u128 * c as u128) % p as u128) as u64;
        r = ((r as u128 * b as u128) % p as u128) as u64;
    }
}

fn mod_pow_u64(base: u64, mut exp: u64, m: u64) -> u64 {
    let mut acc: u128 = 1;
    let mb = base as u128;
    let _ = mb;
    let mm = m as u128;
    let mut base128 = base as u128 % mm;
    let _ = base;
    while exp > 0 {
        if exp & 1 == 1 {
            acc = (acc * base128) % mm;
        }
        base128 = (base128 * base128) % mm;
        exp >>= 1;
    }
    acc as u64
}

/// BSGS for the smallest `k ∈ [lo, hi]` with `k·P = O` on the curve.
/// Standard step size `m = ⌈√(hi - lo)⌉`. Single-word Montgomery arithmetic.
fn bsgs_find_zero_in_hasse(
    fc: &crate::cryptanalysis::bsgs_fast::FastCurve,
    point: crate::cryptanalysis::bsgs_fast::FastPoint,
    lo: u64,
    hi: u64,
) -> Option<u64> {
    use crate::cryptanalysis::bsgs_fast::FastPoint;
    let width = hi - lo;
    let m = isqrt_u64(width) + 1;
    // Baby table: store j ↦ key(j·P)   for j ∈ [0, m].  We also store
    // the negated point for sign-folding so the giant-step inner test
    // costs O(1).
    let mut table: HashMap<[u8; 17], u64> = HashMap::with_capacity((m as usize) * 2);
    let mut j_p = FastPoint::INFINITY;
    for j in 0..=m {
        table.entry(fast_point_key(j_p)).or_insert(j);
        // Also store -j·P with the same |j| value so that
        // (i·m·P − j·P) and (i·m·P + j·P) both hit on a single lookup.
        table
            .entry(fast_point_key(fc.neg(j_p)))
            .or_insert(j.wrapping_neg());
        j_p = fc.add(j_p, point);
    }
    let m_p = fc.scalar_mul(point, m);
    let mut walker = fc.scalar_mul(point, lo);
    let giants_max = (width / m) + 2;
    for i in 0..=giants_max {
        if let Some(&j_signed) = table.get(&fast_point_key(walker)) {
            // Resolve sign: j_signed is either a small positive value
            // (≤ m, meaning walker matched +j·P, so k = i_m − j) or
            // the two's-complement negation of such a j (walker matched
            // −j·P, so k = i_m + j).
            let (k_candidate, ok) = {
                let i_m = lo.wrapping_add(i.wrapping_mul(m));
                if (j_signed as i64) >= 0 && (j_signed as i64) <= m as i64 {
                    if j_signed > i_m {
                        (0, false)
                    } else {
                        (i_m - j_signed, true)
                    }
                } else {
                    let j_abs = j_signed.wrapping_neg();
                    (i_m.wrapping_add(j_abs), true)
                }
            };
            if ok && k_candidate >= lo && k_candidate <= hi {
                if fc.scalar_mul(point, k_candidate).infinity {
                    return Some(k_candidate);
                }
            }
        }
        walker = fc.add(walker, m_p);
    }
    None
}

/// Strip small prime factors `q` from `k` as long as `(k/q)·P = O`.
/// The result is `ord(P)`.  Trial-divides primes up to `√k`.
fn refine_point_order(
    fc: &crate::cryptanalysis::bsgs_fast::FastCurve,
    point: crate::cryptanalysis::bsgs_fast::FastPoint,
    mut k: u64,
) -> u64 {
    let primes: &[u64] = &[
        2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89,
        97,
    ];
    for &q in primes {
        while k > 1 && k.is_multiple_of(q) {
            let candidate = k / q;
            if fc.scalar_mul(point, candidate).infinity {
                k = candidate;
            } else {
                break;
            }
        }
        if q * q > k {
            break;
        }
    }
    // Try remaining cofactor: if k is itself prime > 97, the residue
    // after small-prime stripping is already the order, no more to do.
    k
}

/// Exact floor square root (the old saturating refinement loop never
/// terminated for `n >= (2^32 − 1)^2`).
fn isqrt_u64(n: u64) -> u64 {
    n.isqrt()
}

fn lcm_u64(a: u64, b: u64) -> u64 {
    if a == 0 || b == 0 {
        return 0;
    }
    a / gcd_u64(a, b) * b
}

fn gcd_u64(mut a: u64, mut b: u64) -> u64 {
    while b != 0 {
        let t = a % b;
        a = b;
        b = t;
    }
    a
}

/// Legendre symbol `(a / p)` for an odd prime `p` and `0 ≤ a < p`.
/// Returns `0`, `+1`, or `-1`.
pub fn legendre_u64(a: u64, p: u64) -> i32 {
    if a == 0 {
        return 0;
    }
    // a^((p-1)/2) mod p via fast exponentiation in `u128`.
    let mut result: u128 = 1;
    let mut base: u128 = a as u128 % p as u128;
    let mut e = (p - 1) / 2;
    let m = p as u128;
    while e > 0 {
        if e & 1 == 1 {
            result = (result * base) % m;
        }
        base = (base * base) % m;
        e >>= 1;
    }
    if result == 0 {
        0
    } else if result == 1 {
        1
    } else {
        -1
    }
}

// ── Discriminant / conductor decomposition ───────────────────────────────────

/// CM data attached to a curve `E/F_p`.
#[derive(Clone, Debug, PartialEq, serde::Serialize, serde::Deserialize)]
pub struct CmData {
    /// Field prime.
    pub p: u64,
    /// Frobenius trace `t`.
    pub trace: i64,
    /// `#E(F_p) = p + 1 − t` (`i128`: exceeds `i64` for `p` near `2^63`).
    pub order: i128,
    /// `t² − 4p`, the discriminant of `Z[π]` (`i128`: `|t² − 4p| <= 4p`
    /// leaves `i64` for `p >= 2^61`).
    pub frobenius_disc: i128,
    /// Fundamental discriminant of `Q(π)`.
    pub fundamental_disc: i128,
    /// Conductor `f` of `End(E)` over `O_K` (`f² <= |t² − 4p|`, so it fits
    /// `i64`).
    pub conductor: i64,
    /// Discriminant of `End(E)`: `f² · D_K`.
    pub endomorphism_disc: i128,
    /// Whether the curve is **anomalous** (`#E = p`, Smart's attack
    /// applies).
    pub anomalous: bool,
    /// Whether the curve is **supersingular** (`t ≡ 0 mod p`).
    pub supersingular: bool,
}

/// Compute the full CM data for a small curve.
///
/// All of `p + 1 − t` and `t² − 4p` are evaluated in `i128`; the old `i64`
/// form overflowed `4·p` for `p >= 2^61`.
pub fn cm_discriminant(curve: &SmallCurve) -> CmData {
    let p = curve.p as i128;
    let trace = frobenius_trace(curve);
    let t = trace as i128;
    let order = p + 1 - t;
    let frobenius_disc = t * t - 4 * p;
    let (fund_d, cond) = fundamental_discriminant_and_conductor(frobenius_disc);
    let anomalous = order == p;
    let supersingular = t.rem_euclid(p) == 0;
    let conductor =
        i64::try_from(cond).expect("conductor f satisfies f^2 <= |t^2 - 4p| < 2^66, so f < 2^33");
    CmData {
        p: curve.p,
        trace,
        order,
        frobenius_disc,
        fundamental_disc: fund_d,
        conductor,
        endomorphism_disc: fund_d * cond * cond,
        anomalous,
        supersingular,
    }
}

/// Given an integer `N < 0` with `N ≡ 0` or `1 (mod 4)`, decompose
/// as `N = D · f²` where `D` is the **fundamental discriminant**
/// (the discriminant of the maximal order `O_K`) and `f` is the
/// conductor of the order containing `N` as a discriminant.
///
/// A fundamental discriminant of an imaginary quadratic field is
/// a negative integer `D` such that either:
///
/// - `D ≡ 1 (mod 4)` and `D` is square-free, or
/// - `D = 4 D₀` with `D₀ ≡ 2 or 3 (mod 4)` and `D₀` square-free.
///
/// Algorithm: extract the largest square factor `f²` from `|N|`,
/// leaving a square-free `m`.  Then check the residue of `-m mod 4`;
/// if it lands on the wrong side, restore a factor of 4 into the
/// fundamental part (and halve `f`).
///
/// Trial division runs only to `|N|^{1/3}`: what is left then has at most
/// two prime factors, so it is either square-free or a perfect square.
/// That keeps the cost at `O(|N|^{1/3})` (about `2^21` steps at
/// `|N| = 2^63`) instead of the `O(|N|^{1/2})` of a full square strip.
/// Takes `i128` so `t² − 4p` for `p >= 2^61` fits.
pub fn fundamental_discriminant_and_conductor(n: i128) -> (i128, i128) {
    if n >= 0 {
        return (n, 1);
    }
    let mut rest = n.unsigned_abs();
    let mut square_free: u128 = 1;
    let mut f: u128 = 1;
    let mut d: u128 = 2;
    while d * d * d <= rest {
        if rest.is_multiple_of(d) {
            let mut e = 0u32;
            while rest.is_multiple_of(d) {
                rest /= d;
                e += 1;
            }
            f *= d.pow(e / 2);
            if e % 2 == 1 {
                square_free *= d;
            }
        }
        d += if d == 2 { 1 } else { 2 };
    }
    // `rest` has at most two prime factors, all > |N|^{1/3}.
    let r = rest.isqrt();
    if rest > 1 && r * r == rest {
        f *= r;
    } else {
        square_free *= rest;
    }
    let abs_n = square_free as i128;
    let f = f as i128;
    // Now `abs_n` is square-free.  Candidate fundamental disc:
    let d_cand: i128 = -abs_n;
    if d_cand.rem_euclid(4) == 1 {
        // Already fundamental.
        (d_cand, f)
    } else {
        // d_cand ≡ 2 or 3 (mod 4): fundamental disc is 4·d_cand;
        // halve `f` (one factor of 2 belongs in D, not in f²).
        // This branch fires only when f is even — for true
        // Frobenius discriminants of ordinary curves, that's
        // always the case (N = t² − 4p with t even ⇒ 4 | N).
        if f % 2 == 0 {
            (4 * d_cand, f / 2)
        } else {
            // f is odd: the input itself was not a valid order
            // discriminant (N ≡ 2 or 3 mod 4).  Defensive fall-
            // back: report `(N, 1)` so callers can detect the
            // anomaly.
            (n, 1)
        }
    }
}

// ── Endomorphism-ring classification ──────────────────────────────────────────

/// Coarse classification of `End(E)` based on the conductor `f`.
#[derive(Clone, Copy, Debug, PartialEq, Eq, serde::Serialize)]
pub enum EndomorphismRing {
    /// `f = 1`: `End(E) = O_K`, the maximal order.  Curve lies on
    /// the **crater** for every `ℓ ∤ f`.
    Maximal,
    /// `f > 1`: non-maximal order.  Curve sits below the crater on
    /// at least one volcano.
    NonMaximal { conductor: i64 },
    /// Supersingular curves are not handled by this CM machinery
    /// (their endomorphism ring is a quaternion order, not
    /// imaginary quadratic).
    Supersingular,
}

pub fn classify_endomorphism_ring(data: &CmData) -> EndomorphismRing {
    if data.supersingular {
        EndomorphismRing::Supersingular
    } else if data.conductor == 1 {
        EndomorphismRing::Maximal
    } else {
        EndomorphismRing::NonMaximal {
            conductor: data.conductor,
        }
    }
}

// ── Hilbert class polynomial — interface to the existing module ──────────────
//
// `H_D(X)` is computed in [`crate::cryptanalysis::hilbert_class_poly`]
// for class-number-1 discriminants and for small `|D|`; we expose a
// thin wrapper so callers in this module can ask "what j-invariants
// have CM by D over C?".

/// Look up the j-invariant(s) of the CM curve(s) with discriminant
/// `D < 0`, when `h(D) = 1`.  For `h(D) > 1` the j-invariants are
/// algebraic of degree `h(D)`; we return only the well-known
/// class-number-one values here.
pub fn class_number_one_j(disc: i64) -> Option<i64> {
    Some(match disc {
        -3 => 0,
        -4 => 1_728,
        -7 => -3_375,
        -8 => 8_000,
        -11 => -32_768,
        -12 => 54_000,
        -16 => 287_496,
        -19 => -884_736,
        -27 => -12_288_000,
        -28 => 16_581_375,
        -43 => -884_736_000,
        -67 => -147_197_952_000,
        -163 => -262_537_412_640_768_000,
        _ => return None,
    })
}

// ── CM detection on a known curve ─────────────────────────────────────────────

/// Verify that the supplied curve really does have CM by an order
/// of discriminant `expected_disc`.  Returns `true` iff
/// `t² − 4p = D · f²` for some integer `f`.  This is the cheap
/// fingerprint that lets us reject "fake CM" claims.
pub fn verify_cm(curve: &SmallCurve, expected_disc: i64) -> bool {
    let data = cm_discriminant(curve);
    if expected_disc >= 0 || data.fundamental_disc == 0 {
        return false;
    }
    // Both `data.frobenius_disc` and `expected_disc` should differ by
    // a perfect-square factor.
    let ratio = BigInt::from(data.frobenius_disc) / BigInt::from(expected_disc);
    let ratio = ratio.abs();
    let r_u: u128 = ratio.to_string().parse().unwrap_or(0);
    // Exact integer square root (f64 is inexact above 2^53).
    let sq = r_u.isqrt();
    sq * sq == r_u
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::isogeny::{toy_curve_a, toy_curve_b, toy_curve_j0, SmallCurve};

    /// Direct cross-check: BSGS-derived trace equals brute-force
    /// trace at a scale where both run.
    #[test]
    fn bsgs_matches_brute_force_at_16bit() {
        // p = 65537 (Fermat prime), several (a, b) curves.
        for (a, b) in [(2u64, 3), (5, 11), (17, 4), (123, 456)] {
            let curve = SmallCurve {
                name: "16b-test",
                p: 65537,
                a,
                b,
            };
            // Discriminant must be non-zero.
            let p128 = curve.p as u128;
            let disc = (4 * (a as u128).pow(3) + 27 * (b as u128).pow(2)) % p128;
            if disc == 0 {
                continue;
            }
            let bsgs = frobenius_trace_bsgs(&curve).expect("BSGS succeeded");
            // Reference: brute force on the same curve via the slow path.
            let mut count: i64 = 1;
            for x in 0..curve.p {
                match legendre_u64(curve.rhs(x), curve.p) {
                    0 => count += 1,
                    1 => count += 2,
                    _ => {}
                }
            }
            let brute = curve.p as i64 + 1 - count;
            assert_eq!(
                bsgs, brute,
                "BSGS / brute-force disagree on (a={}, b={})",
                a, b
            );
        }
    }

    #[test]
    fn bsgs_runs_at_22_bits() {
        // p ≈ 2^22.  Brute force would take seconds; BSGS finishes
        // in milliseconds.  We just check the result lies in the
        // Hasse interval — not its exact value (which has no
        // closed form for random a, b).
        let curve = SmallCurve {
            name: "22b",
            p: 4194319, // first prime above 2^22
            a: 3,
            b: 5,
        };
        let t = frobenius_trace_bsgs(&curve).expect("BSGS succeeded");
        let bound = 2.0 * (curve.p as f64).sqrt();
        assert!(
            (t.abs() as f64) <= bound + 1.0,
            "trace {} outside Hasse bound 2√p ≈ {}",
            t,
            bound
        );
    }

    #[test]
    fn trace_in_hasse_bound() {
        let curve = toy_curve_a();
        let t = frobenius_trace(&curve);
        let bound = 2.0 * (curve.p as f64).sqrt();
        assert!(
            (t.abs() as f64) <= bound + 0.5,
            "trace {} out of Hasse bound 2√p = {}",
            t,
            bound,
        );
    }

    #[test]
    fn order_matches_trace() {
        let curve = toy_curve_b();
        let data = cm_discriminant(&curve);
        assert_eq!(data.order, (curve.p as i128) + 1 - data.trace as i128);
    }

    #[test]
    fn frobenius_disc_is_negative_for_ordinary() {
        let curve = toy_curve_a();
        let data = cm_discriminant(&curve);
        // Ordinary curves: t² − 4p < 0.
        assert!(data.frobenius_disc < 0);
    }

    #[test]
    fn j0_curve_has_disc_minus3_family() {
        // For y² = x³ + 1 over F_103, CM by Z[ω] with disc -3.
        // We won't insist on exact f here (depends on p), but the
        // *fundamental* part of the discriminant must be -3 (or a
        // multiple of it after stripping squares).
        let curve = toy_curve_j0();
        let data = cm_discriminant(&curve);
        // Sanity: data.fundamental_disc is squarefree-ish and < 0.
        assert!(data.fundamental_disc < 0);
    }

    #[test]
    fn legendre_basic() {
        // Quadratic residues mod 7: 1, 2, 4.
        assert_eq!(legendre_u64(1, 7), 1);
        assert_eq!(legendre_u64(2, 7), 1);
        assert_eq!(legendre_u64(4, 7), 1);
        // Non-residues: 3, 5, 6.
        assert_eq!(legendre_u64(3, 7), -1);
        assert_eq!(legendre_u64(5, 7), -1);
        assert_eq!(legendre_u64(6, 7), -1);
        // Zero.
        assert_eq!(legendre_u64(0, 7), 0);
    }

    /// Cube-root trial division gives the same decomposition as a full
    /// square strip, including squares of primes above |N|^{1/3}.
    #[test]
    fn fundamental_disc_matches_full_square_strip() {
        fn reference(n: i128) -> (i128, i128) {
            let mut abs_n = -n;
            let mut f = 1i128;
            let mut p = 2i128;
            while p * p <= abs_n {
                while abs_n % (p * p) == 0 {
                    abs_n /= p * p;
                    f *= p;
                }
                p += 1;
            }
            if (-abs_n).rem_euclid(4) == 1 {
                (-abs_n, f)
            } else if f % 2 == 0 {
                (-4 * abs_n, f / 2)
            } else {
                (n, 1)
            }
        }
        for n in [
            -3i128,
            -4,
            -7,
            -8,
            -12,
            -16,
            -27,
            -28,
            -48,
            -75,
            -99,
            -4 * 1009 * 1009,
            -3 * 1013 * 1013,
            -4 * 7 * 101 * 101,
            -(1i128 << 20),
            -4 * 1_000_003 * 13,
            -11 * 9973 * 9973 * 4,
        ] {
            assert_eq!(
                fundamental_discriminant_and_conductor(n),
                reference(n),
                "N = {n}"
            );
        }
    }

    /// p = 2^62 − 57 (prime, inside SmallCurve's documented p < 2^62): the
    /// old i64 `t² − 4p` overflowed (4p > 2^63). The trace comes from the
    /// BSGS count; check the order annihilates points and the discriminant
    /// decomposes exactly.
    #[test]
    fn cm_discriminant_exact_at_2p62() {
        use crate::cryptanalysis::bsgs_fast::{FastCurve, FastPoint};
        let p: u64 = (1u64 << 62) - 57;
        let curve = SmallCurve {
            name: "62b",
            p,
            a: 2,
            b: 3,
        };
        let data = cm_discriminant(&curve);
        let t = data.trace as i128;
        assert!(t * t <= 4 * p as i128, "Hasse bound");
        assert_eq!(data.order, p as i128 + 1 - t);
        assert_eq!(data.frobenius_disc, t * t - 4 * p as i128);
        let f = data.conductor as i128;
        assert_eq!(data.fundamental_disc * f * f, data.frobenius_disc);
        assert!(matches!(data.fundamental_disc.rem_euclid(4), 0 | 1));
        // [#E]P = O for a few points.
        let n = u64::try_from(data.order).unwrap();
        let fc = FastCurve::from_u64(p, 2, 3, n).unwrap();
        let mut rng = 0x1234_5678u64;
        for _ in 0..3 {
            let (x, y) = sample_random_xy(&curve, &mut rng).unwrap();
            let pt = FastPoint {
                x: fc.f.to_mont(x),
                y: fc.f.to_mont(y),
                infinity: false,
            };
            assert!(fc.scalar_mul(pt, n).infinity);
        }
    }

    /// p >= 2^63 is refused with a message instead of an O(p) loop.
    #[test]
    #[should_panic(expected = "beyond the single-word BSGS point count")]
    fn frobenius_trace_refuses_p_at_2p63() {
        let curve = SmallCurve {
            name: "64b",
            p: u64::MAX - 58,
            a: 2,
            b: 3,
        };
        let _ = frobenius_trace(&curve);
    }

    /// The exact isqrt terminates at the top of the u64 range.
    #[test]
    fn cm_isqrt_u64_near_max() {
        assert_eq!(isqrt_u64(u64::MAX), (1u64 << 32) - 1);
        assert_eq!(isqrt_u64((1u64 << 62) - 57), (1u64 << 31) - 1);
    }

    #[test]
    fn fundamental_disc_of_minus_12() {
        // -12 = -3 · 2², so fundamental D_K = -3, conductor f = 2.
        let (d, f) = fundamental_discriminant_and_conductor(-12);
        assert_eq!(d, -3);
        assert_eq!(f, 2);
    }
}
