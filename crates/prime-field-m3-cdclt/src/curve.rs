//! Short Weierstrass prime-field curves `E/F_p: y^2 = x^3 + a x + b`,
//! exact prime whole-group order finder, chained-`S_3` and quadratic `lambda` lift
//! `(2 t lambda - s_0)^2 = f(x)` (`disc = 16 t^2 f(x)`), canonical IR, and exact
//! two-window (`e = 2`) and `F_{p^2}` reference enumerators.

use std::collections::{BTreeSet, HashMap};
use std::fmt::Write as _;

use crate::field::{
    add_mod, first_nonsquare, inv_mod, is_prime_u64, mul_mod, neg_mod, next_prime_at_least,
    sha256_hex, sqrt_mod_canonical, sub_mod, DeterministicRng, Fp2, FpOps, MontDomain,
};

/// Short Weierstrass curve `y^2 = x^3 + a x + b` over `F_p` (`p > 3`).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CurveFp {
    pub p: u64,
    pub a: u64,
    pub b: u64,
}

/// Affine/infinite point on `E(F_p)`.
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct PointFp {
    pub infinity: bool,
    pub x: u64,
    pub y: u64,
}

/// Affine/infinite point on `E(F_{p^2})`.
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub struct PointFp2 {
    pub infinity: bool,
    pub x: Fp2,
    pub y: Fp2,
}

impl PointFp {
    #[inline]
    pub const fn identity() -> Self {
        Self {
            infinity: true,
            x: 0,
            y: 0,
        }
    }

    #[inline]
    pub const fn affine(x: u64, y: u64) -> Self {
        Self {
            infinity: false,
            x,
            y,
        }
    }
}

impl CurveFp {
    /// Check `4 a^3 + 27 b^2 != 0 (mod p)`.
    pub fn is_nonsingular(self) -> bool {
        if self.p <= 3 || self.a >= self.p || self.b >= self.p {
            return false;
        }
        let mut ops = FpOps::default();
        let a2 = mul_mod(self.a, self.a, self.p, &mut ops);
        let a3 = mul_mod(a2, self.a, self.p, &mut ops);
        let term_a = mul_mod(4 % self.p, a3, self.p, &mut ops);
        let b2 = mul_mod(self.b, self.b, self.p, &mut ops);
        let term_b = mul_mod(27 % self.p, b2, self.p, &mut ops);
        add_mod(term_a, term_b, self.p, &mut ops) != 0
    }

    /// Evaluate `f(x) = x^3 + a x + b (mod p)`.
    #[inline]
    pub fn rhs(self, x: u64, ops: &mut FpOps) -> u64 {
        let x2 = mul_mod(x, x, self.p, ops);
        let x3 = mul_mod(x2, x, self.p, ops);
        let ax = mul_mod(self.a, x, self.p, ops);
        let s = add_mod(x3, ax, self.p, ops);
        add_mod(s, self.b, self.p, ops)
    }

    /// Check whether `pt` lies on `E(F_p)`.
    pub fn on_curve(self, pt: PointFp, ops: &mut FpOps) -> bool {
        if pt.infinity {
            return true;
        }
        if pt.x >= self.p || pt.y >= self.p {
            return false;
        }
        let lhs = mul_mod(pt.y, pt.y, self.p, ops);
        let rhs = self.rhs(pt.x, ops);
        lhs == rhs
    }

    /// Canonical sign bit `0` iff `y <= p - y`, `1` iff `y > p - y` (matches `development_oracle.cpp`).
    #[inline]
    pub fn point_sign(self, pt: PointFp) -> u8 {
        assert!(!pt.infinity, "sign of point at infinity is undefined");
        let opp = if pt.y == 0 { 0 } else { self.p - pt.y };
        u8::from(pt.y > opp)
    }

    /// Recover the signed rational point from canonical `y_canon in [0, (p-1)/2]` and `sign in {0, 1}`.
    #[inline]
    pub fn point_from_canonical_lift(self, x: u64, y_canon: u64, sign: u8) -> PointFp {
        let y = if sign == 0 || y_canon == 0 {
            y_canon
        } else {
            self.p - y_canon
        };
        PointFp::affine(x, y)
    }

    /// Negate `pt` on `E(F_p)`.
    #[inline]
    pub fn neg(self, pt: PointFp, ops: &mut FpOps) -> PointFp {
        if pt.infinity {
            pt
        } else {
            PointFp::affine(pt.x, neg_mod(pt.y, self.p, ops))
        }
    }

    /// Exact affine chord-and-tangent addition on `E(F_p)`.
    pub fn add(self, lhs: PointFp, rhs: PointFp, ops: &mut FpOps) -> PointFp {
        if lhs.infinity {
            return rhs;
        }
        if rhs.infinity {
            return lhs;
        }
        if lhs.x == rhs.x {
            let sum_y = add_mod(lhs.y, rhs.y, self.p, ops);
            if sum_y == 0 {
                return PointFp::identity();
            }
            let x2 = mul_mod(lhs.x, lhs.x, self.p, ops);
            let three_x2 = mul_mod(3 % self.p, x2, self.p, ops);
            let num = add_mod(three_x2, self.a, self.p, ops);
            let den = mul_mod(2 % self.p, lhs.y, self.p, ops);
            let lam = mul_mod(num, inv_mod(den, self.p, ops), self.p, ops);
            let lam2 = mul_mod(lam, lam, self.p, ops);
            let x3_a = sub_mod(lam2, lhs.x, self.p, ops);
            let x3 = sub_mod(x3_a, rhs.x, self.p, ops);
            let dx = sub_mod(lhs.x, x3, self.p, ops);
            let ldx = mul_mod(lam, dx, self.p, ops);
            let y3 = sub_mod(ldx, lhs.y, self.p, ops);
            return PointFp::affine(x3, y3);
        }
        let dy = sub_mod(rhs.y, lhs.y, self.p, ops);
        let dx = sub_mod(rhs.x, lhs.x, self.p, ops);
        let lam = mul_mod(dy, inv_mod(dx, self.p, ops), self.p, ops);
        let lam2 = mul_mod(lam, lam, self.p, ops);
        let x3_a = sub_mod(lam2, lhs.x, self.p, ops);
        let x3 = sub_mod(x3_a, rhs.x, self.p, ops);
        let dx3 = sub_mod(lhs.x, x3, self.p, ops);
        let ldx = mul_mod(lam, dx3, self.p, ops);
        let y3 = sub_mod(ldx, lhs.y, self.p, ops);
        PointFp::affine(x3, y3)
    }

    /// Exact affine subtraction `lhs - rhs` on `E(F_p)`.
    #[inline]
    pub fn sub(self, lhs: PointFp, rhs: PointFp, ops: &mut FpOps) -> PointFp {
        let neg_r = self.neg(rhs, ops);
        self.add(lhs, neg_r, ops)
    }

    /// Double-and-add scalar multiplication `[k] pt` using Jacobian coordinates for speed.
    pub fn scalar_mul(self, pt: PointFp, k: u64) -> PointFp {
        self.scalar_mul_wide(pt, k as u128)
    }

    /// `[k] pt` for a 128-bit scalar (used when `p + 1 + 2 sqrt(p)` exceeds `u64::MAX`).
    fn scalar_mul_wide(self, pt: PointFp, mut k: u128) -> PointFp {
        if pt.infinity || k == 0 {
            return PointFp::identity();
        }
        let dom = MontDomain::new(self.p);
        let mut ops = FpOps::default();
        let a_m = dom.to_mont(self.a);
        let mut acc = JacPoint::identity();
        let mut base = JacPoint {
            x: dom.to_mont(pt.x),
            y: dom.to_mont(pt.y),
            z: dom.one(),
            infinity: false,
        };
        while k != 0 {
            if (k & 1) != 0 {
                acc = jac_add(dom, a_m, acc, base, &mut ops);
            }
            k >>= 1;
            if k != 0 {
                base = jac_double(dom, a_m, base, &mut ops);
            }
        }
        jac_to_affine(dom, acc, &mut ops)
    }

    /// Evaluate Semaev's third summation polynomial `S_3(x_1, x_2, x_3) mod p`.
    pub fn semaev_s3(self, x1: u64, x2: u64, x3: u64, ops: &mut FpOps) -> u64 {
        let p = self.p;
        let dx = sub_mod(x1, x2, p, ops);
        let dx2 = mul_mod(dx, dx, p, ops);
        let x3_2 = mul_mod(x3, x3, p, ops);
        let leading = mul_mod(dx2, x3_2, p, ops);

        let x1x2 = mul_mod(x1, x2, p, ops);
        let sum12 = add_mod(x1, x2, p, ops);
        let x1x2_plus_a = add_mod(x1x2, self.a, p, ops);
        let prod_inner = mul_mod(sum12, x1x2_plus_a, p, ops);
        let two_b = mul_mod(2 % p, self.b, p, ops);
        let mid_inner = add_mod(prod_inner, two_b, p, ops);
        let two_mid = mul_mod(2 % p, mid_inner, p, ops);
        let middle = mul_mod(two_mid, x3, p, ops);

        let x1x2_minus_a = sub_mod(x1x2, self.a, p, ops);
        let tail_sq = mul_mod(x1x2_minus_a, x1x2_minus_a, p, ops);
        let four_b = mul_mod(4 % p, self.b, p, ops);
        let tail_b = mul_mod(four_b, sum12, p, ops);

        let pos = add_mod(leading, tail_sq, p, ops);
        let neg = add_mod(middle, tail_b, p, ops);
        sub_mod(pos, neg, p, ops)
    }

    /// Check the quadratic `lambda` lift `(2 t lambda - s_0)^2 == f(x) (mod p)`.
    #[inline]
    pub fn check_lambda_lift(
        self,
        x: u64,
        t: u64,
        s0: u64,
        lambda: u64,
        ops: &mut FpOps,
    ) -> bool {
        let two_t = mul_mod(2 % self.p, t, self.p, ops);
        let two_t_lam = mul_mod(two_t, lambda, self.p, ops);
        let disp = sub_mod(two_t_lam, s0, self.p, ops);
        let lhs = mul_mod(disp, disp, self.p, ops);
        let rhs = self.rhs(x, ops);
        lhs == rhs
    }

    /// Exact discriminant `16 t^2 f(x) (mod p)` of `(2 t lambda - s_0)^2 = f(x)` in `lambda`.
    #[inline]
    pub fn lambda_lift_discriminant(self, x: u64, t: u64, ops: &mut FpOps) -> u64 {
        let t2 = mul_mod(t, t, self.p, ops);
        let sixteen_t2 = mul_mod(16 % self.p, t2, self.p, ops);
        let fx = self.rhs(x, ops);
        mul_mod(sixteen_t2, fx, self.p, ops)
    }

    /// Compute the exact rational group order `#E(F_p)` for small primes (`p < 512`) by census,
    /// or via Hasse-interval baby-step giant-step when `p >= 512` (returning `Some(r)` iff `#E(F_p)`
    /// is an odd prime `r`).
    pub fn prime_whole_group_order(self) -> Option<u64> {
        if !self.is_nonsingular() || !is_prime_u64(self.p) {
            return None;
        }
        let mut ops = FpOps::default();
        if self.p < 512 {
            let mut count = 1u64;
            for x in 0..self.p {
                let rhs = self.rhs(x, &mut ops);
                if rhs == 0 {
                    count += 1;
                } else if sqrt_mod_canonical(rhs, self.p, &mut ops).is_some() {
                    count += 2;
                }
            }
            return (is_prime_u64(count) && (count & 1) == 1).then_some(count);
        }

        // Find a rational point on E(F_p).
        let mut pt = None;
        for x in 1..self.p {
            let rhs = self.rhs(x, &mut ops);
            if rhs != 0 {
                if let Some(y) = sqrt_mod_canonical(rhs, self.p, &mut ops) {
                    pt = Some(PointFp::affine(x, y));
                    break;
                }
            }
        }
        let pt = pt?;

        // Hasse interval [p + 1 - B, p + 1 + B] with B = floor(2 * sqrt(p)).
        // Exact integer bound (the f64 estimate is inexact above 2^52); u128 so nothing wraps near 2^64.
        let bound: u128 = 2 * (isqrt_u128(self.p as u128) + 1) + 2;
        let m: u64 = (isqrt_u128(2 * bound) + 2) as u64;
        let dom = MontDomain::new(self.p);
        let a_m = dom.to_mont(self.a);

        // Baby steps: j * P for j = 0..m-1, converted to affine x (storing y).
        let mut baby: HashMap<u64, Vec<(u64, u64)>> = HashMap::with_capacity(m as usize + 4);
        let p_jac = JacPoint {
            x: dom.to_mont(pt.x),
            y: dom.to_mont(pt.y),
            z: dom.one(),
            infinity: false,
        };
        let mut cur = JacPoint::identity();
        for j in 0..m {
            let aff = jac_to_affine(dom, cur, &mut ops);
            let key = if aff.infinity { u64::MAX } else { aff.x };
            baby.entry(key).or_default().push((aff.y, j));
            cur = jac_add(dom, a_m, cur, p_jac, &mut ops);
        }
        // cur is now [m]P. Giant step searches (p + 1 + bound - i * m) P == j P
        // i.e. [p + 1 + bound] P - [i * m] P == [j] P.
        let step_neg = {
            let aff = jac_to_affine(dom, cur, &mut ops);
            if aff.infinity {
                JacPoint::identity()
            } else {
                let neg_aff = self.neg(aff, &mut ops);
                JacPoint {
                    x: dom.to_mont(neg_aff.x),
                    y: dom.to_mont(neg_aff.y),
                    z: dom.one(),
                    infinity: false,
                }
            }
        };
        let top: u128 = self.p as u128 + 1 + bound;
        let top_pt = self.scalar_mul_wide(pt, top);
        let mut giant = if top_pt.infinity {
            JacPoint::identity()
        } else {
            JacPoint {
                x: dom.to_mont(top_pt.x),
                y: dom.to_mont(top_pt.y),
                z: dom.one(),
                infinity: false,
            }
        };
        let max_i = (2 * bound) / (m as u128) + 2;
        let mut candidates = Vec::new();
        for i in 0..=max_i {
            let aff = jac_to_affine(dom, giant, &mut ops);
            let key = if aff.infinity { u64::MAX } else { aff.x };
            if let Some(entries) = baby.get(&key) {
                for &(by, j) in entries {
                    if aff.infinity || aff.y == by {
                        let im_plus_j = i * (m as u128) + j as u128;
                        if top >= im_plus_j {
                            let n = top - im_plus_j;
                            let low = (self.p as u128 + 1).saturating_sub(bound);
                            let high = self.p as u128 + 1 + bound;
                            // An order above u64::MAX cannot be represented in the return type.
                            if n >= low
                                && n <= high
                                && n <= u64::MAX as u128
                                && (n & 1) == 1
                                && is_prime_u64(n as u64)
                            {
                                candidates.push(n as u64);
                            }
                        }
                    }
                }
            }
            giant = jac_add(dom, a_m, giant, step_neg, &mut ops);
        }
        candidates.sort_unstable();
        candidates.dedup();
        // By Mestre/Hasse uniqueness for p >= 37, a prime order r in the Hasse interval
        // that annihilates two independent rational points is uniquely #E(F_p).
        for r in candidates {
            if !self.scalar_mul(pt, r).infinity {
                continue;
            }
            // Verify on 3 independent rational points and reject if any is 2-torsion.
            let mut verified = 0usize;
            for x in (pt.x + 1)..self.p {
                let rhs = self.rhs(x, &mut ops);
                if rhs != 0 {
                    if let Some(y) = sqrt_mod_canonical(rhs, self.p, &mut ops) {
                        let q = PointFp::affine(x, y);
                        if !self.scalar_mul(q, r).infinity {
                            verified = 0;
                            break;
                        }
                        verified += 1;
                        if verified == 3 {
                            break;
                        }
                    }
                }
            }
            if verified > 0 {
                return Some(r);
            }
        }
        None
    }
}

#[derive(Debug, Clone, Copy)]
struct JacPoint {
    x: u64,
    y: u64,
    z: u64,
    infinity: bool,
}

impl JacPoint {
    const fn identity() -> Self {
        Self {
            x: 0,
            y: 0,
            z: 0,
            infinity: true,
        }
    }
}

fn jac_double(dom: MontDomain, a_m: u64, p: JacPoint, ops: &mut FpOps) -> JacPoint {
    if p.infinity || p.y == 0 {
        return JacPoint::identity();
    }
    let xx = dom.sqr(p.x, ops);
    let yy = dom.sqr(p.y, ops);
    let yyyy = dom.sqr(yy, ops);
    let zz = dom.sqr(p.z, ops);
    let x_plus_yy = dom.add(p.x, yy, ops);
    let t0 = dom.sqr(x_plus_yy, ops);
    let t1 = dom.sub(t0, xx, ops);
    let t2 = dom.sub(t1, yyyy, ops);
    let s = dom.add(t2, t2, ops);
    let zzzz = dom.sqr(zz, ops);
    let a_zzzz = dom.mul(a_m, zzzz, ops);
    let two_xx = dom.add(xx, xx, ops);
    let three_xx = dom.add(two_xx, xx, ops);
    let m = dom.add(three_xx, a_zzzz, ops);
    let m2 = dom.sqr(m, ops);
    let two_s = dom.add(s, s, ops);
    let x3 = dom.sub(m2, two_s, ops);
    let s_minus_x3 = dom.sub(s, x3, ops);
    let m_diff = dom.mul(m, s_minus_x3, ops);
    let two_yyyy = dom.add(yyyy, yyyy, ops);
    let four_yyyy = dom.add(two_yyyy, two_yyyy, ops);
    let eight_yyyy = dom.add(four_yyyy, four_yyyy, ops);
    let y3 = dom.sub(m_diff, eight_yyyy, ops);
    let yz = dom.mul(p.y, p.z, ops);
    let z3 = dom.add(yz, yz, ops);
    JacPoint {
        x: x3,
        y: y3,
        z: z3,
        infinity: false,
    }
}

fn jac_add(dom: MontDomain, a_m: u64, p1: JacPoint, p2: JacPoint, ops: &mut FpOps) -> JacPoint {
    if p1.infinity {
        return p2;
    }
    if p2.infinity {
        return p1;
    }
    let z1z1 = dom.sqr(p1.z, ops);
    let z2z2 = dom.sqr(p2.z, ops);
    let u1 = dom.mul(p1.x, z2z2, ops);
    let u2 = dom.mul(p2.x, z1z1, ops);
    let z2_3 = dom.mul(p2.z, z2z2, ops);
    let z1_3 = dom.mul(p1.z, z1z1, ops);
    let s1 = dom.mul(p1.y, z2_3, ops);
    let s2 = dom.mul(p2.y, z1_3, ops);
    if u1 == u2 {
        if s1 == s2 {
            return jac_double(dom, a_m, p1, ops);
        }
        return JacPoint::identity();
    }
    let h = dom.sub(u2, u1, ops);
    let two_h = dom.add(h, h, ops);
    let i = dom.sqr(two_h, ops);
    let j = dom.mul(h, i, ops);
    let diff_s = dom.sub(s2, s1, ops);
    let r = dom.add(diff_s, diff_s, ops);
    let v = dom.mul(u1, i, ops);
    let r2 = dom.sqr(r, ops);
    let two_v = dom.add(v, v, ops);
    let x3_a = dom.sub(r2, j, ops);
    let x3 = dom.sub(x3_a, two_v, ops);
    let v_minus_x3 = dom.sub(v, x3, ops);
    let r_v = dom.mul(r, v_minus_x3, ops);
    let s1_j = dom.mul(s1, j, ops);
    let two_s1_j = dom.add(s1_j, s1_j, ops);
    let y3 = dom.sub(r_v, two_s1_j, ops);
    let z1_plus_z2 = dom.add(p1.z, p2.z, ops);
    let z_sq = dom.sqr(z1_plus_z2, ops);
    let z_sub1 = dom.sub(z_sq, z1z1, ops);
    let z_sub2 = dom.sub(z_sub1, z2z2, ops);
    let z3 = dom.mul(z_sub2, h, ops);
    JacPoint {
        x: x3,
        y: y3,
        z: z3,
        infinity: false,
    }
}

fn jac_to_affine(dom: MontDomain, p: JacPoint, ops: &mut FpOps) -> PointFp {
    if p.infinity || p.z == 0 {
        return PointFp::identity();
    }
    let z_inv = dom.inv_mont(p.z, ops);
    let z2 = dom.sqr(z_inv, ops);
    let z3 = dom.mul(z2, z_inv, ops);
    let x_m = dom.mul(p.x, z2, ops);
    let y_m = dom.mul(p.y, z3, ops);
    PointFp::affine(dom.from_mont(x_m), dom.from_mont(y_m))
}

/// Target class for the `m = 3` scaling screen.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum TargetClass {
    /// Uniform random nonzero subgroup point `R in E(F_p) \ {O}`.
    Natural,
    /// Sum `P_0 + P_1 + P_2` of three uniformly chosen signed window points.
    Planted,
    /// Certified exact-UNSAT rational target `R in E(F_p) \ {O}` having zero decompositions.
    ExactUnsat,
}

impl TargetClass {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Natural => "natural",
            Self::Planted => "planted",
            Self::ExactUnsat => "exact-unsat",
        }
    }
}

/// Canonical typed semantic instance for fixed-arity `m = 3` disjoint-window point decomposition.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct M3Instance {
    pub instance_id: String,
    pub rung_s: u32,
    pub curve: CurveFp,
    pub group_order: u64,
    pub windows: [Vec<u64>; 3],
    pub target: PointFp,
    pub target_class: TargetClass,
    pub planted_witness: Option<[PointFp; 3]>,
}

/// Projected signed decomposition witness `((idx_0, sign_0), (idx_1, sign_1), (idx_2, sign_2))`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct SignedWitness {
    pub indices: [usize; 3],
    pub signs: [u8; 3],
    pub abscissae: [u64; 3],
}

impl SignedWitness {
    /// Canonical model key `"x0:s0;x1:s1;x2:s2"` matching `development_oracle.cpp`.
    pub fn model_key(&self) -> String {
        format!(
            "{}:{};{}:{};{}:{}",
            self.abscissae[0],
            self.signs[0],
            self.abscissae[1],
            self.signs[1],
            self.abscissae[2],
            self.signs[2]
        )
    }
}

/// Validate all semantic invariants of an `M3Instance` (used by both producer and independent checker).
pub fn validate_instance(inst: &M3Instance, verify_group_order: bool) -> Result<(), String> {
    let c = inst.curve;
    if !is_prime_u64(c.p) || c.p <= 3 {
        return Err(format!("invalid prime p={}", c.p));
    }
    if !c.is_nonsingular() {
        return Err("singular Weierstrass curve".to_string());
    }
    if !is_prime_u64(inst.group_order) || (inst.group_order & 1) == 0 {
        return Err(format!(
            "whole-group order {} is not an odd prime",
            inst.group_order
        ));
    }
    if verify_group_order {
        let computed = c
            .prime_whole_group_order()
            .ok_or_else(|| "curve failed independent prime whole-group order check".to_string())?;
        if computed != inst.group_order {
            return Err(format!(
                "declared group_order {} != computed {}",
                inst.group_order, computed
            ));
        }
    }
    let mut ops = FpOps::default();
    if inst.target.infinity || !c.on_curve(inst.target, &mut ops) || inst.target.y == 0 {
        return Err("target is not a finite non-2-torsion rational curve point".to_string());
    }
    if !c.scalar_mul(inst.target, inst.group_order).infinity {
        return Err("target is not annihilated by declared odd prime group order".to_string());
    }
    let mut seen = BTreeSet::new();
    for (w_idx, win) in inst.windows.iter().enumerate() {
        if win.is_empty() {
            return Err(format!("window {w_idx} is empty"));
        }
        for &x in win {
            if x >= c.p {
                return Err(format!("window {w_idx} word {x} >= p={}", c.p));
            }
            if !seen.insert(x) {
                return Err(format!("overlapping abscissa {x} across windows"));
            }
        }
    }
    if let Some(planted) = inst.planted_witness {
        let mut sum = PointFp::identity();
        for (w_idx, pt) in planted.into_iter().enumerate() {
            if pt.infinity || !c.on_curve(pt, &mut ops) {
                return Err(format!("planted summand {w_idx} is off curve"));
            }
            if !inst.windows[w_idx].contains(&pt.x) {
                return Err(format!("planted summand {w_idx} outside window {w_idx}"));
            }
            sum = c.add(sum, pt, &mut ops);
        }
        if sum != inst.target {
            return Err("planted witness does not sum to target".to_string());
        }
    }
    Ok(())
}

/// Deterministic canonical IR string (`prime-field-m3-ir/v2-compact-binary`).
pub fn canonical_ir(inst: &M3Instance) -> String {
    let mut out = String::new();
    let _ = writeln!(out, "prime-field-m3-ir/v2");
    let _ = writeln!(out, "instance_id={}", inst.instance_id);
    let _ = writeln!(out, "rung_s={}", inst.rung_s);
    let _ = writeln!(out, "p={}", inst.curve.p);
    let _ = writeln!(out, "a={}", inst.curve.a);
    let _ = writeln!(out, "b={}", inst.curve.b);
    let _ = writeln!(out, "group_order={}", inst.group_order);
    let _ = writeln!(out, "target={},{}", inst.target.x, inst.target.y);
    let _ = writeln!(out, "target_class={}", inst.target_class.as_str());
    let _ = writeln!(
        out,
        "selector_semantics=compact-binary-radix-index-plus-rational-lift-sign"
    );
    let _ = writeln!(out, "window_range=unsigned-less-than-window-len");
    for (i, win) in inst.windows.iter().enumerate() {
        let _ = write!(out, "window{i}=");
        for (j, &x) in win.iter().enumerate() {
            if j != 0 {
                out.push(',');
            }
            let _ = write!(out, "{x}");
        }
        out.push('\n');
    }
    out
}

/// SHA-256 hex digest of `canonical_ir(inst)`.
pub fn canonical_ir_sha256(inst: &M3Instance) -> String {
    sha256_hex(canonical_ir(inst).as_bytes())
}

/// Exact reproduction of `development_oracle.cpp::make_fixture()` (`E/F_7: y^2 = x^3 + 3`, order 13).
pub fn make_development_fixture() -> M3Instance {
    let primes = [5u64, 7, 11, 13, 17, 19, 23, 29];
    let mut ops = FpOps::default();
    for p in primes {
        for a in 0..p {
            for b in 1..p {
                let curve = CurveFp { p, a, b };
                if !curve.is_nonsingular() {
                    continue;
                }
                let Some(order) = curve.prime_whole_group_order() else {
                    continue;
                };
                if order < 11 {
                    continue;
                }
                let mut reps = Vec::new();
                for x in 0..p {
                    let rhs = curve.rhs(x, &mut ops);
                    if let Some(y) = sqrt_mod_canonical(rhs, p, &mut ops) {
                        reps.push(PointFp::affine(x, y));
                    }
                }
                if reps.len() < 3 {
                    continue;
                }
                for i in 0..reps.len() {
                    for j in (i + 1)..reps.len() {
                        for k in (j + 1)..reps.len() {
                            let planted = [reps[i], reps[j], reps[k]];
                            let s01 = curve.add(planted[0], planted[1], &mut ops);
                            let target = curve.add(s01, planted[2], &mut ops);
                            if target.infinity {
                                continue;
                            }
                            let mut windows: [Vec<u64>; 3] = [Vec::new(), Vec::new(), Vec::new()];
                            let mut assigned = BTreeSet::new();
                            for w in 0..3 {
                                windows[w].push(planted[w].x);
                                assigned.insert(planted[w].x);
                            }
                            let mut next = 0usize;
                            for x in 0..p {
                                if !assigned.contains(&x) {
                                    windows[next % 3].push(x);
                                    next += 1;
                                }
                            }
                            for win in &mut windows {
                                win.sort_unstable();
                            }
                            let inst = M3Instance {
                                instance_id: "dev-fixture-p7-order13".to_string(),
                                rung_s: 2,
                                curve,
                                group_order: order,
                                windows,
                                target,
                                target_class: TargetClass::Planted,
                                planted_witness: Some(planted),
                            };
                            validate_instance(&inst, true).expect("valid fixture");
                            return inst;
                        }
                    }
                }
            }
        }
    }
    panic!("could not construct development fixture");
}

/// Exhaustive `E(F_{p^2})` enumeration across `W_0 x W_1 x W_2` for small development cells,
/// verifying the Frobenius 3-summand rationality theorem (`b == 0` on every summing triple).
pub fn exhaustive_fp2_models(inst: &M3Instance) -> (BTreeSet<String>, u64) {
    let p = inst.curve.p;
    assert!(p <= 31, "exhaustive_fp2_models is only for tiny fields");
    let nonsquare = first_nonsquare(p);
    let fp2_roots = |x: u64| -> Vec<Fp2> {
        let mut ops = FpOps::default();
        let rhs = Fp2::rational(inst.curve.rhs(x, &mut ops));
        let mut roots = Vec::new();
        for a in 0..p {
            for b in 0..p {
                let cand = Fp2 { a, b };
                if cand.mul(cand, p, nonsquare) == rhs {
                    roots.push(cand);
                }
            }
        }
        roots.sort();
        roots.dedup();
        roots
    };
    let add_fp2 = |lhs: PointFp2, rhs: PointFp2| -> PointFp2 {
        if lhs.infinity {
            return rhs;
        }
        if rhs.infinity {
            return lhs;
        }
        if lhs.x == rhs.x && lhs.y.add(rhs.y, p).is_zero() {
            return PointFp2 {
                infinity: true,
                x: Fp2::default(),
                y: Fp2::default(),
            };
        }
        let lam = if lhs == rhs {
            assert!(!lhs.y.is_zero(), "2-torsion doubling");
            let num = Fp2::rational(3 % p)
                .mul(lhs.x.mul(lhs.x, p, nonsquare), p, nonsquare)
                .add(Fp2::rational(inst.curve.a), p);
            let den = Fp2::rational(2 % p).mul(lhs.y, p, nonsquare);
            num.mul(den.inv(p, nonsquare), p, nonsquare)
        } else {
            rhs.y
                .sub(lhs.y, p)
                .mul(rhs.x.sub(lhs.x, p).inv(p, nonsquare), p, nonsquare)
        };
        let x3 = lam.mul(lam, p, nonsquare).sub(lhs.x, p).sub(rhs.x, p);
        let y3 = lam.mul(lhs.x.sub(x3, p), p, nonsquare).sub(lhs.y, p);
        PointFp2 {
            infinity: false,
            x: x3,
            y: y3,
        }
    };

    let target_fp2 = PointFp2 {
        infinity: false,
        x: Fp2::rational(inst.target.x),
        y: Fp2::rational(inst.target.y),
    };
    let mut models = BTreeSet::new();
    let mut candidates = 0u64;
    let mut ops = FpOps::default();
    for &x0 in &inst.windows[0] {
        for y0 in fp2_roots(x0) {
            let p0 = PointFp2 {
                infinity: false,
                x: Fp2::rational(x0),
                y: y0,
            };
            for &x1 in &inst.windows[1] {
                for y1 in fp2_roots(x1) {
                    let p1 = PointFp2 {
                        infinity: false,
                        x: Fp2::rational(x1),
                        y: y1,
                    };
                    for &x2 in &inst.windows[2] {
                        for y2 in fp2_roots(x2) {
                            candidates += 1;
                            let p2 = PointFp2 {
                                infinity: false,
                                x: Fp2::rational(x2),
                                y: y2,
                            };
                            let inter = add_fp2(p0, p1);
                            let sum = add_fp2(inter, p2);
                            if sum != target_fp2 {
                                continue;
                            }
                            assert!(
                                y0.is_rational() && y1.is_rational() && y2.is_rational(),
                                "Frobenius three-summand rationality counterexample"
                            );
                            assert!(!inter.infinity && inter.x.is_rational());
                            assert_eq!(inst.curve.semaev_s3(x0, x1, inter.x.a, &mut ops), 0);
                            assert_eq!(
                                inst.curve.semaev_s3(inter.x.a, x2, inst.target.x, &mut ops),
                                0
                            );
                            let pts = [
                                PointFp::affine(x0, y0.a),
                                PointFp::affine(x1, y1.a),
                                PointFp::affine(x2, y2.a),
                            ];
                            let w = SignedWitness {
                                indices: [
                                    inst.windows[0].iter().position(|&v| v == x0).unwrap(),
                                    inst.windows[1].iter().position(|&v| v == x1).unwrap(),
                                    inst.windows[2].iter().position(|&v| v == x2).unwrap(),
                                ],
                                signs: [
                                    inst.curve.point_sign(pts[0]),
                                    inst.curve.point_sign(pts[1]),
                                    inst.curve.point_sign(pts[2]),
                                ],
                                abscissae: [x0, x1, x2],
                            };
                            models.insert(w.model_key());
                        }
                    }
                }
            }
        }
    }
    (models, candidates)
}

/// Target-independent prepared state for the exact two-window enumeration (`enum-ref`, `e = 2`).
#[derive(Debug, Clone)]
pub struct PreparedTwoWindow {
    pub curve: CurveFp,
    pub dom: MontDomain,
    pub windows: [Vec<u64>; 3],
    pub lifts: [Vec<Option<u64>>; 3],
    pub w2_lookup: HashMap<u64, usize>,
    pub setup_ops: FpOps,
}

impl PreparedTwoWindow {
    /// Prepare window canonical lifts and `W_2` index map (target-independent setup).
    pub fn prepare(curve: CurveFp, windows: [Vec<u64>; 3]) -> Self {
        let dom = MontDomain::new(curve.p);
        let mut setup_ops = FpOps::default();
        let mut lifts: [Vec<Option<u64>>; 3] = [Vec::new(), Vec::new(), Vec::new()];
        for w in 0..3 {
            lifts[w].reserve(windows[w].len());
            for &x in &windows[w] {
                let rhs = curve.rhs(x, &mut setup_ops);
                lifts[w].push(sqrt_mod_canonical(rhs, curve.p, &mut setup_ops));
            }
        }
        let mut w2_lookup = HashMap::with_capacity(windows[2].len() * 2);
        for (idx, &x) in windows[2].iter().enumerate() {
            w2_lookup.insert(x, idx);
        }
        Self {
            curve,
            dom,
            windows,
            lifts,
            w2_lookup,
            setup_ops,
        }
    }

    /// Exact two-window enumeration (`enum-ref`) over `W_0 x W_1` using batched Montgomery
    /// inversion across blocks of 64 abscissa pairs. Returns `(witnesses, online_ops)`.
    /// When `stop_after_first` is `false`, returns the complete projected signed model set.
    pub fn enumerate(&self, target: PointFp, stop_after_first: bool) -> (Vec<SignedWitness>, FpOps) {
        let mut ops = FpOps::default();
        let p = self.curve.p;
        let dom = self.dom;
        let rx_m = dom.to_mont(target.x);
        let ry_m = dom.to_mont(target.y);
        let two_target = self.curve.add(target, target, &mut ops);

        // Collect rational entries in W0 and W1 with their Montgomery coordinates.
        let r0: Vec<(usize, u64, u64, u64)> = self.windows[0]
            .iter()
            .enumerate()
            .filter_map(|(i, &x)| {
                self.lifts[0][i].map(|y| (i, x, dom.to_mont(x), dom.to_mont(y)))
            })
            .collect();
        let r1: Vec<(usize, u64, u64, u64)> = self.windows[1]
            .iter()
            .enumerate()
            .filter_map(|(i, &x)| {
                self.lifts[1][i].map(|y| (i, x, dom.to_mont(x), dom.to_mont(y)))
            })
            .collect();

        let mut witnesses = Vec::new();
        const BATCH: usize = 64;
        let mut den_batch = Vec::with_capacity(BATCH);
        let mut prefix = Vec::with_capacity(BATCH);
        let mut pair_meta = Vec::with_capacity(BATCH);

        let flush_batch = |den_batch: &mut Vec<u64>,
                           prefix: &mut Vec<u64>,
                           pair_meta: &mut Vec<(usize, u64, u64, u64, usize, u64, u64, u64, u64, u64, u64, u64, u64)>,
                           ops: &mut FpOps,
                           witnesses: &mut Vec<SignedWitness>|
         -> bool {
            if den_batch.is_empty() {
                return false;
            }
            prefix.clear();
            let mut acc = dom.one();
            for &d in den_batch.iter() {
                prefix.push(acc);
                acc = dom.mul(acc, d, ops);
            }
            let mut inv_acc = dom.inv_mont(acc, ops);
            for k in (0..den_batch.len()).rev() {
                let g_inv = dom.mul(inv_acc, prefix[k], ops);
                inv_acc = dom.mul(inv_acc, den_batch[k], ops);
                let (i0, x0, x0_m, y0_m, i1, x1, _x1_m, _y1_m, d1_m, u_plus, u_minus, t_plus, t_minus) =
                    pair_meta[k];
                // Recover d1^{-1}, t_plus^{-1} (if nonzero), t_minus^{-1} (if nonzero).
                let tp_nz = if t_plus == 0 { dom.one() } else { t_plus };
                let tm_nz = if t_minus == 0 { dom.one() } else { t_minus };
                let tp_tm = dom.mul(tp_nz, tm_nz, ops);
                let d1_inv = dom.mul(g_inv, tp_tm, ops);
                let d1_g = dom.mul(d1_m, g_inv, ops);
                let tp_inv = dom.mul(d1_g, tm_nz, ops);
                let tm_inv = dom.mul(d1_g, tp_nz, ops);
                let d1_inv2 = dom.sqr(d1_inv, ops);
                let d1_inv3 = dom.mul(d1_inv2, d1_inv, ops);

                // Check all 4 sign combinations (s0, s1) in {0, 1}^2.
                for (s0, s1) in [(0u8, 0u8), (0, 1), (1, 0), (1, 1)] {
                    let y0_s = if s0 == 0 { y0_m } else { dom.neg(y0_m, ops) };
                    let y1_s = if s1 == 0 {
                        pair_meta[k].7
                    } else {
                        dom.neg(pair_meta[k].7, ops)
                    };
                    let same_diff = s0 == s1;
                    let u_num = if same_diff { u_plus } else { u_minus };
                    let t_num = if same_diff { t_plus } else { t_minus };
                    let t_num_inv = if same_diff { tp_inv } else { tm_inv };
                    let u_m = dom.mul(u_num, d1_inv2, ops);

                    // Compute v_m: N1 = y1_s - y0_s; lam1 = N1 * d1_inv;
                    // v = -2 * lam1 * (u - x0) - y0_s.
                    let n1 = dom.sub(y1_s, y0_s, ops);
                    let lam1 = dom.mul(n1, d1_inv, ops);
                    let two_lam1 = dom.add(lam1, lam1, ops);
                    let u_minus_x0 = dom.sub(u_m, x0_m, ops);
                    let prod_v = dom.mul(two_lam1, u_minus_x0, ops);
                    let v_m = dom.neg(dom.add(prod_v, y0_s, ops), ops);

                    let (x2_cand, y2_cand) = if t_num == 0 {
                        // Exceptional branch u == x_R!
                        if v_m == ry_m {
                            // U == R => P_2 = O (impossible for finite window).
                            continue;
                        }
                        if two_target.infinity {
                            continue;
                        }
                        (two_target.x, two_target.y)
                    } else {
                        // Non-exceptional quadratic lambda lift:
                        // t_u = (u - x_R) = t_num * d1^{-2}, so (2 * t_u)^{-1} = d1^2 * (2 * t_num)^{-1}.
                        // Actually: 2 * lam2 = (v + y_R) / (u - x_R) = (v + y_R) * d1^2 * t_num^{-1}.
                        let _ = d1_inv3;
                        let d1_sq = dom.sqr(d1_m, ops);
                        let tu_inv = dom.mul(d1_sq, t_num_inv, ops);
                        let v_plus_ry = dom.add(v_m, ry_m, ops);
                        let m2 = dom.mul(v_plus_ry, tu_inv, ops); // m2 = 2 * lam2
                        let m2_sq = dom.sqr(m2, ops);
                        let u_plus_rx = dom.add(u_m, rx_m, ops);
                        let x2_m = dom.sub(m2_sq, u_plus_rx, ops);
                        let x2_minus_rx = dom.sub(x2_m, rx_m, ops);
                        let m2_dx = dom.mul(m2, x2_minus_rx, ops);
                        let y2_m = dom.sub(m2_dx, ry_m, ops);
                        (dom.from_mont(x2_m), dom.from_mont(y2_m))
                    };

                    if let Some(&i2) = self.w2_lookup.get(&x2_cand) {
                        if self.lifts[2][i2].is_some() {
                            let s2 = u8::from(y2_cand > (p - y2_cand));
                            witnesses.push(SignedWitness {
                                indices: [i0, i1, i2],
                                signs: [s0, s1, s2],
                                abscissae: [x0, x1, x2_cand],
                            });
                            if stop_after_first {
                                den_batch.clear();
                                pair_meta.clear();
                                return true;
                            }
                        }
                    }
                }
            }
            den_batch.clear();
            pair_meta.clear();
            false
        };

        for &(i0, x0, x0_m, y0_m) in &r0 {
            for &(i1, x1, x1_m, y1_m) in &r1 {
                let t01 = dom.sub(x1_m, x0_m, &mut ops);
                let d1_m = dom.add(t01, t01, &mut ops); // 2 * (x1 - x0) != 0
                let d1_sq = dom.sqr(d1_m, &mut ops);
                let sum01 = dom.add(x0_m, x1_m, &mut ops);
                let sum01_d1sq = dom.mul(sum01, d1_sq, &mut ops);
                let rx_d1sq = dom.mul(rx_m, d1_sq, &mut ops);

                // Same-sign pair: N_+ = y1 - y0; opposite-sign pair: N_- = -y1 - y0 = -(y1 + y0).
                let diff_y = dom.sub(y1_m, y0_m, &mut ops);
                let sum_y = dom.add(y1_m, y0_m, &mut ops);
                let two_diff = dom.add(diff_y, diff_y, &mut ops);
                let two_sum = dom.add(sum_y, sum_y, &mut ops);
                let four_n_plus_sq = dom.sqr(two_diff, &mut ops);
                let four_n_minus_sq = dom.sqr(two_sum, &mut ops);

                let u_plus = dom.sub(four_n_plus_sq, sum01_d1sq, &mut ops);
                let u_minus = dom.sub(four_n_minus_sq, sum01_d1sq, &mut ops);
                let t_plus = dom.sub(u_plus, rx_d1sq, &mut ops);
                let t_minus = dom.sub(u_minus, rx_d1sq, &mut ops);

                let tp_nz = if t_plus == 0 { dom.one() } else { t_plus };
                let tm_nz = if t_minus == 0 { dom.one() } else { t_minus };
                let tp_tm = dom.mul(tp_nz, tm_nz, &mut ops);
                let g = dom.mul(d1_m, tp_tm, &mut ops);

                den_batch.push(g);
                pair_meta.push((
                    i0, x0, x0_m, y0_m, i1, x1, x1_m, y1_m, d1_m, u_plus, u_minus, t_plus, t_minus,
                ));
                if den_batch.len() == BATCH
                    && flush_batch(&mut den_batch, &mut prefix, &mut pair_meta, &mut ops, &mut witnesses)
                {
                    return (witnesses, ops);
                }
            }
        }
        let _ = flush_batch(
            &mut den_batch,
            &mut prefix,
            &mut pair_meta,
            &mut ops,
            &mut witnesses,
        );
        witnesses.sort();
        witnesses.dedup();
        (witnesses, ops)
    }
}

/// Largest rung `s` for which the prime bound `27 * 2^(3s)` fits in `u64`.
pub const MAX_RUNG_S: u32 = 19;

/// Floor integer square root of a `u128` (exact; no floating point).
fn isqrt_u128(n: u128) -> u128 {
    if n < 2 {
        return n;
    }
    let mut x = 1u128 << ((128 - n.leading_zeros()).div_ceil(2));
    loop {
        let y = (x + n / x) / 2;
        if y >= x {
            return x;
        }
        x = y;
    }
}

/// Deterministically generate a curve `E/F_p` of odd prime whole-group order `r` and three
/// disjoint rational factor-base windows of cardinality `2^s` each at rung `s`, with prime
/// `p >= 27 * 2^{3s}` so total factor base `3 * 2^s ≈ p^{1/3}` (matching the `m = 3` IC density
/// `E[#models] ≈ (2 W)^3 / r ≈ 8/27 ≈ 0.296`, so natural targets include both SAT and UNSAT).
pub fn generate_rung_curve_and_windows(
    protocol_seed_prefix: &str,
    rung_s: u32,
) -> (CurveFp, u64, [Vec<u64>; 3]) {
    // 27 * 2^(3s) must fit u64: s = 19 gives 27 * 2^57 < 2^62, s = 20 gives 27 * 2^60 > 2^64.
    assert!(
        (2..=MAX_RUNG_S).contains(&rung_s),
        "rung_s must be in 2..={MAX_RUNG_S} (27 * 2^(3s) must fit u64)"
    );
    let w_size = 1usize << rung_s;
    let min_p = 27u64
        .checked_mul(1u64 << (3 * rung_s))
        .expect("prime bound fits u64");
    let mut rng = DeterministicRng::from_label(&format!("{protocol_seed_prefix}:curve:s={rung_s}"));

    let mut p = next_prime_at_least(min_p + (rng.uniform(256) * 2));
    let (curve, order) = loop {
        for _ in 0..24 {
            let a = 1 + rng.uniform(p - 1);
            let b = 1 + rng.uniform(p - 1);
            let c = CurveFp { p, a, b };
            if !c.is_nonsingular() {
                continue;
            }
            if let Some(r) = c.prime_whole_group_order() {
                if (r - 1) / 2 >= (3 * w_size) as u64 {
                    break;
                }
            }
        }
        // Deterministic scan from `a = 1..` on `p` if random draws missed, else advance `p`.
        let mut found = None;
        for trial in 0..32 {
            let a = (1 + rng.uniform(p - 1) + trial) % p;
            let b = (1 + rng.uniform(p - 1) + 3 * trial) % p;
            let c = CurveFp { p, a, b };
            if let Some(r) = c.prime_whole_group_order() {
                if (r - 1) / 2 >= (3 * w_size) as u64 {
                    found = Some((c, r));
                    break;
                }
            }
        }
        if let Some(pair) = found {
            break pair;
        }
        p = next_prime_at_least(p + 2);
    };

    // Collect `3 * 2^s` distinct rational abscissae deterministically and partition into 3 disjoint windows.
    let mut ops = FpOps::default();
    let needed = 3 * w_size;
    let mut rational_xs = Vec::with_capacity(needed);
    let mut x_cursor = 1 + rng.uniform(p / 4);
    let mut seen = BTreeSet::new();
    while rational_xs.len() < needed {
        x_cursor = (x_cursor + 1) % p;
        if seen.contains(&x_cursor) {
            continue;
        }
        let rhs = curve.rhs(x_cursor, &mut ops);
        if rhs != 0 && sqrt_mod_canonical(rhs, p, &mut ops).is_some() {
            seen.insert(x_cursor);
            rational_xs.push(x_cursor);
        }
    }
    let mut windows: [Vec<u64>; 3] = [
        Vec::with_capacity(w_size),
        Vec::with_capacity(w_size),
        Vec::with_capacity(w_size),
    ];
    for (idx, x) in rational_xs.into_iter().enumerate() {
        windows[idx % 3].push(x);
    }
    for win in &mut windows {
        win.sort_unstable();
    }
    (curve, order, windows)
}

/// Sample a deterministic uniform finite point on `E(F_p) \ {O}`.
pub fn sample_random_curve_point(curve: CurveFp, rng: &mut DeterministicRng) -> PointFp {
    let mut ops = FpOps::default();
    loop {
        let x = rng.uniform(curve.p);
        let rhs = curve.rhs(x, &mut ops);
        if rhs == 0 {
            continue;
        }
        if let Some(y_canon) = sqrt_mod_canonical(rhs, curve.p, &mut ops) {
            let sign = (rng.next_u64() & 1) as u8;
            return curve.point_from_canonical_lift(x, y_canon, sign);
        }
    }
}

/// Generate an `M3Instance` of the specified `TargetClass` from prepared curve & windows.
pub fn generate_instance_for_class(
    instance_id: String,
    rung_s: u32,
    prepared: &PreparedTwoWindow,
    target_class: TargetClass,
    rng: &mut DeterministicRng,
) -> M3Instance {
    let curve = prepared.curve;
    let mut ops = FpOps::default();
    match target_class {
        TargetClass::Natural => {
            let target = sample_random_curve_point(curve, rng);
            M3Instance {
                instance_id,
                rung_s,
                curve,
                group_order: 0, // filled by caller
                windows: prepared.windows.clone(),
                target,
                target_class,
                planted_witness: None,
            }
        }
        TargetClass::Planted => loop {
            let mut pts = [PointFp::identity(); 3];
            for w in 0..3 {
                let idx = rng.uniform(prepared.windows[w].len() as u64) as usize;
                let x = prepared.windows[w][idx];
                let y_canon = prepared.lifts[w][idx].expect("rational factor-base window");
                let sign = (rng.next_u64() & 1) as u8;
                pts[w] = curve.point_from_canonical_lift(x, y_canon, sign);
            }
            let s01 = curve.add(pts[0], pts[1], &mut ops);
            let target = curve.add(s01, pts[2], &mut ops);
            if !target.infinity && target.y != 0 {
                return M3Instance {
                    instance_id,
                    rung_s,
                    curve,
                    group_order: 0,
                    windows: prepared.windows.clone(),
                    target,
                    target_class,
                    planted_witness: Some(pts),
                };
            }
        },
        TargetClass::ExactUnsat => loop {
            let candidate = sample_random_curve_point(curve, rng);
            let (models, _) = prepared.enumerate(candidate, true);
            if models.is_empty() {
                return M3Instance {
                    instance_id,
                    rung_s,
                    curve,
                    group_order: 0,
                    windows: prepared.windows.clone(),
                    target: candidate,
                    target_class,
                    planted_witness: None,
                };
            }
        },
    }
}

#[cfg(test)]
mod large_prime_tests {
    use super::*;
    use crate::field::MontDomain;

    /// Largest prime below 2^64 and below 2^63.
    const P64: u64 = u64::MAX - 58;
    const P63: u64 = (1u64 << 63) - 25;

    #[test]
    fn montgomery_full_u64_range() {
        for p in [P63, P64, (1u64 << 62) + 135] {
            assert!(is_prime_u64(p), "{p}");
            let dom = MontDomain::new(p);
            let mut ops = FpOps::default();
            for (x, y) in [(p - 1, p - 1), (p - 2, 12345), (1, p - 1), (p / 2, p / 3)] {
                let got = dom.from_mont(dom.mul(dom.to_mont(x), dom.to_mont(y), &mut ops));
                assert_eq!(got as u128, (x as u128 * y as u128) % p as u128, "p={p}");
                assert_eq!(dom.from_mont(dom.to_mont(x)), x);
            }
        }
    }

    #[test]
    fn isqrt_exact_above_2_53() {
        for n in [
            u64::MAX as u128,
            (1u128 << 106) - 1,
            (1u128 << 106),
            1u128 << 127,
        ] {
            let r = isqrt_u128(n);
            assert!(r * r <= n && (r + 1) * (r + 1) > n);
        }
    }

    fn order_roundtrip(p: u64) {
        let mut found = None;
        for a in 1..4000u64 {
            let c = CurveFp { p, a, b: 7 };
            if !c.is_nonsingular() {
                continue;
            }
            if let Some(r) = c.prime_whole_group_order() {
                found = Some((c, r));
                break;
            }
        }
        let (c, r) = found.expect("a curve of odd prime order in a:1..4000");
        let mut ops = FpOps::default();
        let x = (2..p)
            .find(|&x| {
                c.rhs(x, &mut ops) != 0
                    && sqrt_mod_canonical(c.rhs(x, &mut ops), p, &mut ops).is_some()
            })
            .unwrap();
        let y = sqrt_mod_canonical(c.rhs(x, &mut ops), p, &mut ops).unwrap();
        let pt = PointFp::affine(x, y);
        assert!(c.scalar_mul(pt, r).infinity);
        assert!(!c.scalar_mul(pt, r - 1).infinity);
        let inst_ok = validate_instance_prime_only(&c, r);
        assert!(inst_ok);
    }

    fn validate_instance_prime_only(c: &CurveFp, r: u64) -> bool {
        is_prime_u64(c.p) && c.is_nonsingular() && c.prime_whole_group_order() == Some(r)
    }

    #[test]
    fn group_order_p_above_2_62() {
        order_roundtrip(P63);
    }

    #[test]
    fn group_order_p_near_2_64() {
        order_roundtrip(P64);
    }

    #[test]
    #[should_panic(expected = "rung_s must be in")]
    fn rung_20_refused_explicitly() {
        let _ = generate_rung_curve_and_windows("t", 20);
    }
}
