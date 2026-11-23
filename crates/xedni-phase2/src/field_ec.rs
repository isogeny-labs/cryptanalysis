//! Exact prime-field Weierstrass elliptic-curve arithmetic, deterministic
//! prime-order curve construction, and matched single-target Pollard's rho.

use std::collections::HashMap;

use num_bigint::BigInt;
use num_integer::Integer;
use num_traits::{One, Signed, Zero};
use serde::{Deserialize, Serialize};

/// Deterministic SplitMix64 PRNG for reproducible masks, walks, and controls.
#[derive(Clone, Debug)]
pub struct SplitMix64 {
    state: u64,
}

impl SplitMix64 {
    pub fn new(seed: u64) -> Self {
        Self { state: seed }
    }

    pub fn next_u64(&mut self) -> u64 {
        self.state = self.state.wrapping_add(0x9e37_79b9_7f4a_7c15);
        let mut z = self.state;
        z = (z ^ (z >> 30)).wrapping_mul(0xbf58_476d_1ce4_e5b9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94d0_49bb_1331_11eb);
        z ^ (z >> 31)
    }

    pub fn uniform_u64(&mut self, bound: u64) -> u64 {
        assert!(bound > 0);
        self.next_u64() % bound
    }

    pub fn uniform_below(&mut self, bound: &BigInt) -> BigInt {
        let bits = bound.bits() as usize;
        let words = bits.div_ceil(64).max(1);
        let mut acc = BigInt::zero();
        for _ in 0..words {
            acc = (acc << 64) + BigInt::from(self.next_u64());
        }
        acc.mod_floor(bound)
    }
}

/// Deterministic 64-bit Miller-Rabin primality test (exact for all `u64`).
pub fn is_prime_u64(n: u64) -> bool {
    if n < 2 {
        return false;
    }
    for &p in &[2u64, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37] {
        if n == p {
            return true;
        }
        if n % p == 0 {
            return false;
        }
    }
    let mut d = n - 1;
    let mut s = 0u32;
    while d % 2 == 0 {
        d >>= 1;
        s += 1;
    }
    for &a in &[2u64, 325, 9_375, 28_178, 450_775, 9_780_504, 1_795_265_022] {
        if a % n == 0 {
            continue;
        }
        let mut x = mod_pow_u64(a, d, n);
        if x == 1 || x == n - 1 {
            continue;
        }
        let mut witness = true;
        for _ in 1..s {
            x = mod_mul_u64(x, x, n);
            if x == n - 1 {
                witness = false;
                break;
            }
        }
        if witness {
            return false;
        }
    }
    true
}

#[inline]
pub fn mod_mul_u64(a: u64, b: u64, m: u64) -> u64 {
    ((a as u128 * b as u128) % (m as u128)) as u64
}

#[inline]
pub fn mod_pow_u64(mut base: u64, mut exp: u64, m: u64) -> u64 {
    let mut acc = 1u64 % m;
    base %= m;
    while exp > 0 {
        if exp & 1 == 1 {
            acc = mod_mul_u64(acc, base, m);
        }
        base = mod_mul_u64(base, base, m);
        exp >>= 1;
    }
    acc
}

#[inline]
pub fn mod_inv_u64(a: u64, p: u64) -> Option<u64> {
    let r = a % p;
    if r == 0 {
        None
    } else {
        Some(mod_pow_u64(r, p - 2, p))
    }
}

/// Point on a short-Weierstrass curve over `F_p` (`BigInt` coordinates).
#[derive(Clone, Debug, Eq, PartialEq, Hash)]
pub enum EcPoint {
    Infinity,
    Affine(BigInt, BigInt),
}

/// Short-Weierstrass curve `y^2 = x^3 + a x + b` over prime field `F_p`.
#[derive(Clone, Debug)]
pub struct PrimeWeierstrass {
    pub p: BigInt,
    pub a: BigInt,
    pub b: BigInt,
}

impl PrimeWeierstrass {
    pub fn new(p: BigInt, a: BigInt, b: BigInt) -> Result<Self, String> {
        if p <= BigInt::from(3) {
            return Err("prime modulus p must exceed 3".into());
        }
        let a_mod = a.mod_floor(&p);
        let b_mod = b.mod_floor(&p);
        let disc_part = (BigInt::from(4) * &a_mod * &a_mod * &a_mod
            + BigInt::from(27) * &b_mod * &b_mod)
            .mod_floor(&p);
        if disc_part.is_zero() {
            return Err("short Weierstrass curve is singular modulo p".into());
        }
        Ok(Self {
            p,
            a: a_mod,
            b: b_mod,
        })
    }

    pub fn source_cubic_coefficients(&self) -> Vec<BigInt> {
        vec![
            BigInt::one(),
            BigInt::zero(),
            BigInt::zero(),
            BigInt::zero(),
            BigInt::zero(),
            BigInt::zero(),
            BigInt::from(-1),
            self.a.clone(),
            BigInt::zero(),
            self.b.clone(),
        ]
    }

    pub fn on_curve(&self, pt: &EcPoint) -> bool {
        match pt {
            EcPoint::Infinity => true,
            EcPoint::Affine(x, y) => {
                let xm = x.mod_floor(&self.p);
                let ym = y.mod_floor(&self.p);
                let lhs = (&ym * &ym).mod_floor(&self.p);
                let rhs = (&xm * &xm * &xm + &self.a * &xm + &self.b).mod_floor(&self.p);
                lhs == rhs
            }
        }
    }

    pub fn inv_mod(&self, v: &BigInt) -> Option<BigInt> {
        let r = v.mod_floor(&self.p);
        let eg = r.extended_gcd(&self.p);
        (eg.gcd == BigInt::one()).then(|| eg.x.mod_floor(&self.p))
    }

    pub fn negate(&self, pt: &EcPoint) -> EcPoint {
        match pt {
            EcPoint::Infinity => EcPoint::Infinity,
            EcPoint::Affine(x, y) => EcPoint::Affine(x.mod_floor(&self.p), (-y).mod_floor(&self.p)),
        }
    }

    pub fn add(&self, p1: &EcPoint, p2: &EcPoint, ops: &mut u64) -> Result<EcPoint, String> {
        match (p1, p2) {
            (EcPoint::Infinity, q) => Ok(q.clone()),
            (p, EcPoint::Infinity) => Ok(p.clone()),
            (EcPoint::Affine(x1, y1), EcPoint::Affine(x2, y2)) => {
                *ops += 1;
                if x1 == x2 {
                    if (y1 + y2).mod_floor(&self.p).is_zero() {
                        return Ok(EcPoint::Infinity);
                    }
                    let num = (BigInt::from(3) * x1 * x1 + &self.a).mod_floor(&self.p);
                    let den = (BigInt::from(2) * y1).mod_floor(&self.p);
                    let inv = self
                        .inv_mod(&den)
                        .ok_or_else(|| "non-invertible doubling denominator".to_string())?;
                    let lam = (num * inv).mod_floor(&self.p);
                    let x3 = (&lam * &lam - BigInt::from(2) * x1).mod_floor(&self.p);
                    let y3 = (&lam * (x1 - &x3) - y1).mod_floor(&self.p);
                    return Ok(EcPoint::Affine(x3, y3));
                }
                let num = (y2 - y1).mod_floor(&self.p);
                let den = (x2 - x1).mod_floor(&self.p);
                let inv = self
                    .inv_mod(&den)
                    .ok_or_else(|| "non-invertible secant denominator".to_string())?;
                let lam = (num * inv).mod_floor(&self.p);
                let x3 = (&lam * &lam - x1 - x2).mod_floor(&self.p);
                let y3 = (&lam * (x1 - &x3) - y1).mod_floor(&self.p);
                Ok(EcPoint::Affine(x3, y3))
            }
        }
    }

    pub fn scalar_mul(&self, k: &BigInt, pt: &EcPoint, ops: &mut u64) -> Result<EcPoint, String> {
        let mut s = k.clone();
        let mut addend = pt.clone();
        if s.is_negative() {
            s = -s;
            addend = self.negate(&addend);
        }
        let mut acc = EcPoint::Infinity;
        while !s.is_zero() {
            if s.is_odd() {
                acc = self.add(&acc, &addend, ops)?;
            }
            s >>= 1;
            if !s.is_zero() {
                addend = self.add(&addend, &addend, ops)?;
            }
        }
        Ok(acc)
    }

    pub fn tonelli_shanks_sqrt(&self, n_raw: &BigInt, probes: &mut u64) -> Option<BigInt> {
        *probes += 1;
        let n = n_raw.mod_floor(&self.p);
        if n.is_zero() {
            return Some(BigInt::zero());
        }
        let p_minus_1 = &self.p - 1u64;
        let half = &p_minus_1 >> 1;
        if n.modpow(&half, &self.p) != BigInt::one() {
            return None;
        }
        if (&self.p & BigInt::from(3)) == BigInt::from(3) {
            let exp = (&self.p + 1u64) >> 2;
            return Some(n.modpow(&exp, &self.p));
        }
        let mut q = p_minus_1.clone();
        let mut s = 0u32;
        while q.is_even() {
            q >>= 1;
            s += 1;
        }
        let mut z = BigInt::from(2);
        while z.modpow(&half, &self.p) == BigInt::one() {
            z += 1u64;
        }
        let mut m = s;
        let mut c = z.modpow(&q, &self.p);
        let mut t = n.modpow(&q, &self.p);
        let mut r = n.modpow(&((&q + 1u64) >> 1), &self.p);
        while t != BigInt::one() {
            let mut i = 1u32;
            let mut temp = (&t * &t).mod_floor(&self.p);
            while temp != BigInt::one() {
                temp = (&temp * &temp).mod_floor(&self.p);
                i += 1;
                if i >= m {
                    return None;
                }
            }
            let b = c.modpow(&(BigInt::one() << (m - i - 1)), &self.p);
            m = i;
            c = (&b * &b).mod_floor(&self.p);
            t = (&t * &c).mod_floor(&self.p);
            r = (&r * &b).mod_floor(&self.p);
        }
        Some(r)
    }
}

/// Fast `u64` Weierstrass arithmetic for BSGS curve-order certification up to ~32 bits.
#[derive(Clone, Copy, Debug, Eq, PartialEq, Hash)]
enum PtU64 {
    Inf,
    Aff(u64, u64),
}

#[derive(Clone, Copy, Debug)]
struct CurveU64 {
    p: u64,
    a: u64,
    b: u64,
}

impl CurveU64 {
    fn add(&self, p1: PtU64, p2: PtU64) -> PtU64 {
        let p = self.p;
        match (p1, p2) {
            (PtU64::Inf, q) => q,
            (q, PtU64::Inf) => q,
            (PtU64::Aff(x1, y1), PtU64::Aff(x2, y2)) => {
                if x1 == x2 {
                    if (y1 + y2) % p == 0 {
                        return PtU64::Inf;
                    }
                    let num =
                        (3 * (x1 as u128 * x1 as u128 % p as u128) + self.a as u128) % p as u128;
                    let den = (2 * y1) % p;
                    let inv = mod_inv_u64(den, p).expect("invertible 2y");
                    let lam = mod_mul_u64(num as u64, inv, p);
                    let x3 = (mod_mul_u64(lam, lam, p) + p - (2 * x1 % p)) % p;
                    let y3 = (mod_mul_u64(lam, (x1 + p - x3) % p, p) + p - y1) % p;
                    return PtU64::Aff(x3, y3);
                }
                let num = (y2 + p - y1) % p;
                let den = (x2 + p - x1) % p;
                let inv = mod_inv_u64(den, p).expect("invertible dx");
                let lam = mod_mul_u64(num, inv, p);
                let x3 = (mod_mul_u64(lam, lam, p) + 2 * p - x1 - x2) % p;
                let y3 = (mod_mul_u64(lam, (x1 + p - x3) % p, p) + p - y1) % p;
                PtU64::Aff(x3, y3)
            }
        }
    }

    fn neg(&self, pt: PtU64) -> PtU64 {
        match pt {
            PtU64::Inf => PtU64::Inf,
            PtU64::Aff(x, y) => PtU64::Aff(x, if y == 0 { 0 } else { self.p - y }),
        }
    }

    fn mul(&self, mut k: u64, mut addend: PtU64) -> PtU64 {
        let mut acc = PtU64::Inf;
        while k > 0 {
            if k & 1 == 1 {
                acc = self.add(acc, addend);
            }
            k >>= 1;
            if k > 0 {
                addend = self.add(addend, addend);
            }
        }
        acc
    }

    fn sqrt_mod(&self, n: u64) -> Option<u64> {
        let p = self.p;
        if n % p == 0 {
            return Some(0);
        }
        let half = (p - 1) >> 1;
        if mod_pow_u64(n, half, p) != 1 {
            return None;
        }
        if p & 3 == 3 {
            return Some(mod_pow_u64(n, (p + 1) >> 2, p));
        }
        let mut probes = 0u64;
        let pw = PrimeWeierstrass {
            p: BigInt::from(p),
            a: BigInt::from(self.a),
            b: BigInt::from(self.b),
        };
        let r = pw.tonelli_shanks_sqrt(&BigInt::from(n), &mut probes)?;
        r.try_into().ok()
    }

    fn first_point(&self, start_x: u64) -> Option<PtU64> {
        for off in 0..self.p.min(512) {
            let x = (start_x + off) % self.p;
            let rhs = (mod_mul_u64(mod_mul_u64(x, x, self.p), x, self.p)
                + mod_mul_u64(self.a, x, self.p)
                + self.b)
                % self.p;
            if rhs == 0 {
                continue;
            }
            if let Some(y) = self.sqrt_mod(rhs) {
                if y != 0 {
                    return Some(PtU64::Aff(x, y));
                }
            }
        }
        None
    }

    /// Find any prime curve order in Hasse's interval `[p + 1 - B, p + 1 + B]`
    /// that annihilates two independent random points; verify uniqueness in Hasse's interval.
    fn prime_curve_order(&self) -> Option<(u64, (u64, u64))> {
        let p = self.p;
        let hasse = (2.0 * (p as f64).sqrt()).floor() as u64;
        let lo = (p + 1).saturating_sub(hasse);
        let hi = p + 1 + hasse;

        let g = self.first_point(1)?;
        let g2 = self.first_point(p / 3 + 7)?;

        // BSGS of width m ~ sqrt(2 * hasse + 1) <= 2 * p^(1/4) + 2 (~240 at 28 bits).
        let span = hi - lo + 1;
        let m = ((span as f64).sqrt().ceil() as u64).max(2);
        let mut baby: HashMap<PtU64, Vec<u64>> = HashMap::with_capacity(m as usize + 2);
        let mut cur = PtU64::Inf;
        for j in 0..m {
            baby.entry(cur).or_default().push(j);
            cur = self.add(cur, g);
        }
        let step = self.neg(self.mul(m, g));
        let mut gamma = self.neg(self.mul(lo, g));
        let n_steps = span.div_ceil(m);
        let mut prime_orders = Vec::new();
        for i in 0..=n_steps {
            if let Some(js) = baby.get(&gamma) {
                for &j in js {
                    let cand = lo + i * m + j;
                    if cand >= lo
                        && cand <= hi
                        && is_prime_u64(cand)
                        && self.mul(cand, g) == PtU64::Inf
                        && self.mul(cand, g2) == PtU64::Inf
                    {
                        prime_orders.push(cand);
                    }
                }
            }
            gamma = self.add(gamma, step);
        }
        prime_orders.sort_unstable();
        prime_orders.dedup();
        // For p >= 37, Hasse's interval width 4*sqrt(p) < p + 1 - 2*sqrt(p), so if both
        // points have prime order > 4*sqrt(p) (true for all prime-order curves with p >= 37),
        // the curve order is uniquely determined!
        if prime_orders.len() == 1 && prime_orders[0] > 4 * hasse + 2 {
            if let PtU64::Aff(gx, gy) = g {
                return Some((prime_orders[0], (gx, gy)));
            }
        }
        None
    }
}

/// Certified prime-order short-Weierstrass curve over `F_p`.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PrimeOrderCurveInstance {
    pub p: u64,
    pub a: u64,
    pub b: u64,
    pub order: u64,
    pub generator: [u64; 2],
}

/// Deterministically select the first curve `y^2 = x^3 + 3x + b` (`b = 1, 2, ...`)
/// over `F_p` of certified prime order `#E(F_p) = q`.
pub fn find_prime_order_curve(p: u64) -> Result<PrimeOrderCurveInstance, String> {
    if !is_prime_u64(p) || p < 41 {
        return Err(format!("p={p} must be a prime >= 41"));
    }
    let a = 3u64 % p;
    for b in 1..p {
        let disc = (4 * mod_pow_u64(a, 3, p) + 27 * mod_mul_u64(b, b, p)) % p;
        if disc == 0 {
            continue;
        }
        let c = CurveU64 { p, a, b };
        if let Some((ord, (gx, gy))) = c.prime_curve_order() {
            // Double-check with BigInt arithmetic.
            let pw = PrimeWeierstrass::new(BigInt::from(p), BigInt::from(a), BigInt::from(b))?;
            let g_pt = EcPoint::Affine(BigInt::from(gx), BigInt::from(gy));
            let mut ops = 0u64;
            if pw.on_curve(&g_pt)
                && pw.scalar_mul(&BigInt::from(ord), &g_pt, &mut ops)? == EcPoint::Infinity
            {
                return Ok(PrimeOrderCurveInstance {
                    p,
                    a,
                    b,
                    order: ord,
                    generator: [gx, gy],
                });
            }
        }
    }
    Err(format!(
        "no prime-order curve y^2 = x^3 + 3x + b found mod {p}"
    ))
}

/// Certified single-target Pollard's rho solve receipt.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PollardRhoReceipt {
    pub recovered_scalar: String,
    pub verified: bool,
    pub group_ops: u64,
    pub expected_rho_ops: f64,
}

/// Single-target Teske 16-adding-walk Pollard's rho baseline (scalar-blind,
/// Floyd cycle detection with restart on degenerate denominator, `[k]G == Q` verified).
pub fn solve_pollard_rho_single_target(
    curve: &PrimeWeierstrass,
    generator: &EcPoint,
    order: &BigInt,
    target: &EcPoint,
    seed: u64,
) -> Result<PollardRhoReceipt, String> {
    if !curve.on_curve(generator) || !curve.on_curve(target) {
        return Err("generator or target not on curve".into());
    }
    let mut ops = 0u64;
    if target == &EcPoint::Infinity {
        return Ok(PollardRhoReceipt {
            recovered_scalar: "0".into(),
            verified: true,
            group_ops: 0,
            expected_rho_ops: expected_pollard_rho_ops(order),
        });
    }
    if target == generator {
        return Ok(PollardRhoReceipt {
            recovered_scalar: "1".into(),
            verified: true,
            group_ops: 0,
            expected_rho_ops: expected_pollard_rho_ops(order),
        });
    }

    let mut rng = SplitMix64::new(seed);
    let mut jumps: Vec<(EcPoint, BigInt, BigInt)> = Vec::with_capacity(16);
    for _ in 0..16 {
        let u = BigInt::one() + rng.uniform_below(&(order - 1u64));
        let v = BigInt::one() + rng.uniform_below(&(order - 1u64));
        let ug = curve.scalar_mul(&u, generator, &mut ops)?;
        let vq = curve.scalar_mul(&v, target, &mut ops)?;
        let jpt = curve.add(&ug, &vq, &mut ops)?;
        jumps.push((jpt, u, v));
    }

    let step_fn = |pt: &EcPoint,
                   a: &BigInt,
                   b: &BigInt,
                   ops_ref: &mut u64|
     -> Result<(EcPoint, BigInt, BigInt), String> {
        let bucket = match pt {
            EcPoint::Infinity => 0usize,
            EcPoint::Affine(x, _) => {
                let low: u64 = (x & BigInt::from(15u64)).try_into().unwrap_or(0);
                (low as usize) & 15
            }
        };
        let (jpt, ju, jv) = &jumps[bucket];
        let next_pt = curve.add(pt, jpt, ops_ref)?;
        let next_a = (a + ju).mod_floor(order);
        let next_b = (b + jv).mod_floor(order);
        Ok((next_pt, next_a, next_b))
    };

    for _restart in 0..32 {
        let mut t_a = BigInt::one() + rng.uniform_below(&(order - 1u64));
        let mut t_b = rng.uniform_below(order);
        let mut tortoise = {
            let ag = curve.scalar_mul(&t_a, generator, &mut ops)?;
            let bq = curve.scalar_mul(&t_b, target, &mut ops)?;
            curve.add(&ag, &bq, &mut ops)?
        };
        let mut hare = tortoise.clone();
        let mut h_a = t_a.clone();
        let mut h_b = t_b.clone();

        loop {
            let (nt, na, nb) = step_fn(&tortoise, &t_a, &t_b, &mut ops)?;
            tortoise = nt;
            t_a = na;
            t_b = nb;

            let (h1, ha1, hb1) = step_fn(&hare, &h_a, &h_b, &mut ops)?;
            let (h2, ha2, hb2) = step_fn(&h1, &ha1, &hb1, &mut ops)?;
            hare = h2;
            h_a = ha2;
            h_b = hb2;

            if tortoise == hare {
                let db = (&t_b - &h_b).mod_floor(order);
                let eg = db.extended_gcd(order);
                if eg.gcd == BigInt::one() {
                    let da = (&h_a - &t_a).mod_floor(order);
                    let k = (da * eg.x).mod_floor(order);
                    let mut check_ops = 0u64;
                    let check = curve.scalar_mul(&k, generator, &mut check_ops)?;
                    let verified = &check == target;
                    if verified {
                        return Ok(PollardRhoReceipt {
                            recovered_scalar: k.to_string(),
                            verified,
                            group_ops: ops,
                            expected_rho_ops: expected_pollard_rho_ops(order),
                        });
                    }
                }
                break;
            }
        }
    }
    Err("Pollard rho exceeded restart limit without collision".into())
}

pub fn expected_pollard_rho_ops(order: &BigInt) -> f64 {
    let n_f64 = order.to_string().parse::<f64>().unwrap_or(f64::INFINITY);
    (std::f64::consts::PI * n_f64 / 2.0).sqrt()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn prime_order_curve_finder_and_pollard_rho_verify_end_to_end() {
        for &p in &[251u64, 509, 1021, 2039, 4093, 16_777_259, 268_435_399] {
            let inst = find_prime_order_curve(p).unwrap();
            assert!(is_prime_u64(inst.order));
            let pw = PrimeWeierstrass::new(
                BigInt::from(inst.p),
                BigInt::from(inst.a),
                BigInt::from(inst.b),
            )
            .unwrap();
            let g = EcPoint::Affine(
                BigInt::from(inst.generator[0]),
                BigInt::from(inst.generator[1]),
            );
            let mut ops = 0u64;
            assert_eq!(
                pw.scalar_mul(&BigInt::from(inst.order), &g, &mut ops)
                    .unwrap(),
                EcPoint::Infinity
            );
            if p <= 4093 {
                let secret = BigInt::from((inst.order * 37) / 61);
                let q = pw.scalar_mul(&secret, &g, &mut ops).unwrap();
                let rho = solve_pollard_rho_single_target(
                    &pw,
                    &g,
                    &BigInt::from(inst.order),
                    &q,
                    2026_1119,
                )
                .unwrap();
                assert!(rho.verified);
                assert_eq!(rho.recovered_scalar, secret.to_string());
            }
        }
    }
}
