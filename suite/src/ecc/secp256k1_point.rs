//! Constant-time projective-coordinate point arithmetic over secp256k1.
//!
//! # Why a separate point type?
//!
//! [`crate::ecc::point::Point`] is the textbook affine-coordinate
//! implementation that backs both secp256k1 and P-256.  Every addition
//! and doubling there computes a modular inverse to normalize the
//! output, which (a) is expensive and (b) — more importantly here —
//! routes through a variable-time field inverse and therefore through
//! `num-bigint` arithmetic that leaks operand magnitudes at the limb
//! level.
//!
//! This module sidesteps both problems for secp256k1 specifically:
//!
//! - **Homogeneous projective coordinates** `(X, Y, Z)` represent the
//!   affine point `(X/Z, Y/Z)`.  The identity is `(0, 1, 0)`.  No
//!   inverses are needed inside the addition or doubling chain — only
//!   one final inverse to convert back to affine.
//! - **Renes–Costello–Batina (2015) complete formulas** for the
//!   `y² = x³ + b` family work uniformly for all input combinations,
//!   including doublings, the identity, and `P + (-P)`.  No branches
//!   on input values are needed, so the formula is a fixed sequence
//!   of [`SecpFieldElement`] adds, subs, and muls — every one of which
//!   is constant-time.
//! - **Field arithmetic via [`SecpFieldElement`]** delegates to the
//!   Montgomery-form `mont_mul` over [`U256`], which is built from
//!   `u64×u64→u128` partial products and `u128` accumulators with
//!   no operand-dependent branching.
//!
//! The Montgomery ladder over this point type therefore has uniform
//! work per scalar bit at every layer of the stack — addition,
//! doubling, multiplication, reduction.  See `SECURITY.md` for the
//! wider hardening picture.
//!
//! # Reference
//!
//! Joost Renes, Craig Costello, Lejla Batina, *Complete addition
//! formulas for prime order elliptic curves*, EUROCRYPT 2016.  The
//! algorithms here are **Algorithm 7** (addition) and **Algorithm 9**
//! (doubling) for the special case `a = 0`, which secp256k1 satisfies.

use super::curve::CurveParams;
use super::field::FieldElement;
use super::point::Point;
use super::secp256k1_field::SecpFieldElement;
use crate::ct_bignum::{Uint, U256};
use num_bigint::BigUint;
use subtle::Choice;

/// Curve coefficient `b = 7` in Montgomery form.
///
/// `7·R mod p = 7·(2^32 + 977) = 0x7_0000_1AB7`.  Verified by
/// `tests::b_constant_is_correct`.
pub const B_FE: SecpFieldElement =
    SecpFieldElement::from_montgomery_unchecked(Uint([0x0000_0007_0000_1AB7, 0, 0, 0]));

/// Precomputed `3·b = 21` in Montgomery form, as it appears in the RCB
/// formulas.
///
/// `21·R mod p = 21·(2^32 + 977) = 0x15_0000_5025`.  Verified by
/// `tests::b3_constant_is_correct`.
pub const B3_FE: SecpFieldElement =
    SecpFieldElement::from_montgomery_unchecked(Uint([0x0000_0015_0000_5025, 0, 0, 0]));

/// A projective-coordinate point on secp256k1.  The triple
/// `(X, Y, Z)` encodes the affine point `(X/Z, Y/Z)`; the identity
/// is `(0, 1, 0)`.
#[derive(Copy, Clone, Debug)]
pub struct ProjectivePoint {
    pub x: SecpFieldElement,
    pub y: SecpFieldElement,
    pub z: SecpFieldElement,
}

impl ProjectivePoint {
    /// The point at infinity (curve identity), `(0, 1, 0)`.
    pub const IDENTITY: ProjectivePoint = ProjectivePoint {
        x: SecpFieldElement::ZERO,
        y: SecpFieldElement::ONE,
        z: SecpFieldElement::ZERO,
    };

    /// Build a projective point from canonical affine coordinates
    /// `(x, y) ∈ [0, p)²`.  The `Z` coordinate is set to 1.  Caller
    /// must ensure the point lies on the curve; this is not checked.
    pub fn from_affine(x: &U256, y: &U256) -> Self {
        ProjectivePoint {
            x: SecpFieldElement::from_canonical(x),
            y: SecpFieldElement::from_canonical(y),
            z: SecpFieldElement::ONE,
        }
    }

    /// Convert back to canonical affine coordinates.  Returns `None`
    /// for the point at infinity (`Z == 0`).
    ///
    /// Performs one field inverse — variable-time inside, but the
    /// inverse routine is implemented via the constant-time Fermat
    /// ladder over Montgomery-form arithmetic.  Acceptable as a final
    /// step of scalar multiplication, where the result is no longer
    /// dependent on per-bit secrets.
    pub fn to_affine(&self) -> Option<(U256, U256)> {
        if bool::from(self.z.ct_is_zero()) {
            return None;
        }
        let z_inv = self.z.inv();
        let x = self.x.mul(&z_inv).to_canonical();
        let y = self.y.mul(&z_inv).to_canonical();
        Some((x, y))
    }

    /// Constant-time check for the point at infinity.
    pub fn is_identity(&self) -> Choice {
        self.z.ct_is_zero()
    }

    /// Constant-time conditional move: returns `b` iff `choice == 1`.
    #[inline]
    pub fn cmov(a: &Self, b: &Self, choice: Choice) -> Self {
        ProjectivePoint {
            x: SecpFieldElement::cmov(&a.x, &b.x, choice),
            y: SecpFieldElement::cmov(&a.y, &b.y, choice),
            z: SecpFieldElement::cmov(&a.z, &b.z, choice),
        }
    }

    /// Constant-time conditional swap: swaps `a` and `b` iff `choice == 1`.
    #[inline]
    pub fn cswap(a: &mut Self, b: &mut Self, choice: Choice) {
        SecpFieldElement::cswap(&mut a.x, &mut b.x, choice);
        SecpFieldElement::cswap(&mut a.y, &mut b.y, choice);
        SecpFieldElement::cswap(&mut a.z, &mut b.z, choice);
    }

    /// Renes–Costello–Batina **Algorithm 7**: complete addition for
    /// short-Weierstrass curves with `a = 0`.  Works uniformly for all
    /// input combinations — different points, doublings, identity on
    /// either side, and `P + (-P)` — without branching on operand values.
    ///
    /// 12 multiplications + 2 multiplications by `b3` + 22 add/subs.
    #[inline]
    pub fn add(&self, other: &Self) -> Self {
        let (x1, y1, z1) = (&self.x, &self.y, &self.z);
        let (x2, y2, z2) = (&other.x, &other.y, &other.z);

        let mut t0 = x1.mul(x2); // 1.  t0 = X1*X2
        let mut t1 = y1.mul(y2); // 2.  t1 = Y1*Y2
        let mut t2 = z1.mul(z2); // 3.  t2 = Z1*Z2
        let mut t3 = x1.add(y1); // 4.  t3 = X1+Y1
        let mut t4 = x2.add(y2); // 5.  t4 = X2+Y2
        t3 = t3.mul(&t4); // 6.  t3 = t3*t4
        t4 = t0.add(&t1); // 7.  t4 = t0+t1
        t3 = t3.sub(&t4); // 8.  t3 = t3-t4
        t4 = y1.add(z1); // 9.  t4 = Y1+Z1
        let mut x3 = y2.add(z2); // 10. X3 = Y2+Z2
        t4 = t4.mul(&x3); // 11. t4 = t4*X3
        x3 = t1.add(&t2); // 12. X3 = t1+t2
        t4 = t4.sub(&x3); // 13. t4 = t4-X3
        x3 = x1.add(z1); // 14. X3 = X1+Z1
        let mut y3 = x2.add(z2); // 15. Y3 = X2+Z2
        x3 = x3.mul(&y3); // 16. X3 = X3*Y3
        y3 = t0.add(&t2); // 17. Y3 = t0+t2
        y3 = x3.sub(&y3); // 18. Y3 = X3-Y3
        x3 = t0.add(&t0); // 19. X3 = t0+t0
        t0 = x3.add(&t0); // 20. t0 = X3+t0
        t2 = B3_FE.mul(&t2); // 21. t2 = b3*t2
        let mut z3 = t1.add(&t2); // 22. Z3 = t1+t2
        t1 = t1.sub(&t2); // 23. t1 = t1-t2
        y3 = B3_FE.mul(&y3); // 24. Y3 = b3*Y3
        x3 = t4.mul(&y3); // 25. X3 = t4*Y3
        t2 = t3.mul(&t1); // 26. t2 = t3*t1
        x3 = t2.sub(&x3); // 27. X3 = t2-X3
        y3 = y3.mul(&t0); // 28. Y3 = Y3*t0
        t1 = t1.mul(&z3); // 29. t1 = t1*Z3
        y3 = t1.add(&y3); // 30. Y3 = t1+Y3
        t0 = t0.mul(&t3); // 31. t0 = t0*t3
        z3 = z3.mul(&t4); // 32. Z3 = Z3*t4
        z3 = z3.add(&t0); // 33. Z3 = Z3+t0

        ProjectivePoint {
            x: x3,
            y: y3,
            z: z3,
        }
    }

    /// Renes–Costello–Batina **Algorithm 9**: complete doubling for
    /// short-Weierstrass curves with `a = 0`.  4 multiplications + 2
    /// squarings + 2 multiplications by `b3` + 9 add/subs.  Faster than
    /// calling `add(self, self)` because the formula exploits equality.
    #[inline]
    pub fn double(&self) -> Self {
        let (x, y, z) = (&self.x, &self.y, &self.z);

        let mut t0 = y.sqr(); // 1.  t0 = Y^2
        let mut z3 = t0.add(&t0); // 2.  Z3 = t0+t0
        z3 = z3.add(&z3); // 3.  Z3 = Z3+Z3
        z3 = z3.add(&z3); // 4.  Z3 = Z3+Z3
        let mut t1 = y.mul(z); // 5.  t1 = Y*Z
        let mut t2 = z.sqr(); // 6.  t2 = Z^2
        t2 = B3_FE.mul(&t2); // 7.  t2 = b3*t2
        let mut x3 = t2.mul(&z3); // 8.  X3 = t2*Z3
        let mut y3 = t0.add(&t2); // 9.  Y3 = t0+t2
        z3 = t1.mul(&z3); // 10. Z3 = t1*Z3
        t1 = t2.add(&t2); // 11. t1 = t2+t2
        t2 = t1.add(&t2); // 12. t2 = t1+t2
        t0 = t0.sub(&t2); // 13. t0 = t0-t2
        y3 = t0.mul(&y3); // 14. Y3 = t0*Y3
        y3 = x3.add(&y3); // 15. Y3 = X3+Y3
        t1 = x.mul(y); // 16. t1 = X*Y
        x3 = t0.mul(&t1); // 17. X3 = t0*t1
        x3 = x3.add(&x3); // 18. X3 = X3+X3

        ProjectivePoint {
            x: x3,
            y: y3,
            z: z3,
        }
    }

    /// Negate a point: `-(X, Y, Z) = (X, -Y, Z)`.
    pub fn neg(&self) -> Self {
        ProjectivePoint {
            x: self.x,
            y: self.y.neg(),
            z: self.z,
        }
    }

    /// Construct a `ProjectivePoint` from a textbook affine `Point`,
    /// converting the field elements via the canonical bignum
    /// representation.  The point at infinity maps to
    /// [`ProjectivePoint::IDENTITY`].
    pub fn from_textbook(p: &Point) -> Self {
        match p {
            Point::Infinity => ProjectivePoint::IDENTITY,
            Point::Affine { x, y } => ProjectivePoint::from_affine(
                &U256::from_biguint(&x.value),
                &U256::from_biguint(&y.value),
            ),
        }
    }

    /// Convert back to a textbook affine `Point` over the given prime
    /// modulus.  Returns [`Point::Infinity`] when `Z == 0`.
    pub fn to_textbook(&self, p: &BigUint) -> Point {
        match self.to_affine() {
            None => Point::Infinity,
            Some((x_u, y_u)) => Point::Affine {
                x: FieldElement::new(x_u.to_biguint(), p.clone()),
                y: FieldElement::new(y_u.to_biguint(), p.clone()),
            },
        }
    }

    /// Scalar multiplication via the Montgomery ladder, processing
    /// `scalar_bits` bits MSB-first.
    ///
    /// Every iteration performs **exactly one** addition and one
    /// doubling, regardless of the bit value.  The bit-driven branch
    /// is replaced with [`ProjectivePoint::cmov`] over the two
    /// candidate next-states, so on the Rust source level there is no
    /// `if`/`else` keyed on a secret bit.
    ///
    /// Caller specifies `scalar_bits` so the iteration count is fixed
    /// regardless of the position of the most-significant set bit of
    /// `k`.  For secp256k1 secrets this should be the curve order's
    /// bit length (256), not `k.bits()`.
    pub fn scalar_mul_ct(&self, k: &BigUint, scalar_bits: usize) -> Self {
        let mut r0 = ProjectivePoint::IDENTITY;
        let mut r1 = *self;
        let mut prev_bit = Choice::from(0u8);
        for i in (0..scalar_bits).rev() {
            let bit = Choice::from(k.bit(i as u64) as u8);
            let swap = prev_bit ^ bit;
            ProjectivePoint::cswap(&mut r0, &mut r1, swap);
            prev_bit = bit;
            r1 = r0.add(&r1);
            r0 = r0.double();
        }
        ProjectivePoint::cswap(&mut r0, &mut r1, prev_bit);
        r0
    }
}

/// Drop-in constant-time scalar multiplication for **secp256k1 only**:
/// converts `point` into projective form, runs the
/// [`ProjectivePoint::scalar_mul_ct`] Montgomery ladder over the
/// Renes–Costello–Batina formulas, and returns the result as a
/// textbook [`Point`] for compatibility with the existing ECDH /
/// ECDSA code paths.
///
/// Falls back to the textbook affine [`Point::scalar_mul_ct`] for any
/// other curve, since the projective formulas in this module assume
/// `a = 0` (which only secp256k1 satisfies among the curves the crate
/// supports).
///
/// Use this for **secret** scalars only.  Public-input scalar
/// multiplications (the ECDSA verifier's `u₁·G + u₂·Q`) should keep
/// using the variable-time but faster [`Point::scalar_mul`].
pub fn ct_scalar_mul(point: &Point, k: &BigUint, curve: &CurveParams) -> Point {
    if curve.name == "secp256k1" {
        let pp = ProjectivePoint::from_textbook(point);
        let out = pp.scalar_mul_ct(k, curve.order_bits());
        out.to_textbook(&curve.p)
    } else {
        // Other curves (P-256) fall back to the affine ladder.  The
        // affine ladder still has the operation-count uniformity
        // property; what it lacks is the limb-level constant-time
        // field arithmetic that this module's projective ladder gets
        // from `SecpFieldElement`.
        point.scalar_mul_ct(k, &curve.a_fe(), curve.order_bits())
    }
}

/// CM endomorphism `ψ(X : Y : Z) = (β·X : Y : Z)` on secp256k1 (`j = 0`,
/// `End(E) ≅ Z[ω]`), where `β³ ≡ 1 (mod p)` and `ψ(P) = [λ]P` on the
/// prime-order subgroup.
pub fn secp256k1_glv_params() -> &'static (
    SecpFieldElement,
    BigUint,
    (num_bigint::BigInt, num_bigint::BigInt),
    (num_bigint::BigInt, num_bigint::BigInt),
) {
    use num_bigint::BigInt;
    use num_integer::Integer;
    use num_traits::{One, Signed, Zero};
    static PARAMS: std::sync::OnceLock<(
        SecpFieldElement,
        BigUint,
        (BigInt, BigInt),
        (BigInt, BigInt),
    )> = std::sync::OnceLock::new();
    PARAMS.get_or_init(|| {
        let beta_u = Uint([
            0xC139_6C28_7195_01EE,
            0x9CF0_4975_12F5_8995,
            0x6E64_479E_AC34_34E9,
            0x7AE9_6A2B_657C_0710,
        ]);
        let beta = SecpFieldElement::from_canonical(&beta_u);
        let lambda = BigUint::parse_bytes(
            b"5363ad4cc05c30e0a5261c028812645a122e22ea20816678df02967c1b23bd72",
            16,
        )
        .expect("valid hex");
        let n = BigInt::from(CurveParams::secp256k1().n);
        let lam_i = BigInt::from(lambda.clone());
        let sqrt_n = n.sqrt();

        // Half-GCD on (n, λ) to extract the two short basis vectors of
        // L = { (x, y) ∈ Z² : x + λ·y ≡ 0 (mod n) } with |x|, |y| ≤ √n.
        let (mut r0, mut r1) = (n.clone(), lam_i);
        let (mut t0, mut t1) = (BigInt::zero(), BigInt::one());
        while r1 > sqrt_n {
            let (q, rem) = r0.div_rem(&r1);
            r0 = r1;
            r1 = rem;
            let next_t = &t0 - &q * &t1;
            t0 = t1;
            t1 = next_t;
        }
        let v1 = (r1.clone(), -&t1);
        let (_, rem2) = r0.div_rem(&r1);
        let q2 = (&r0 - &rem2) / &r1;
        let t2 = &t0 - &q2 * &t1;
        let cand_a = (r0, -t0);
        let cand_b = (rem2, -t2);
        let norm_sq = |(x, y): &(BigInt, BigInt)| x * x + y * y;
        let v2 = if norm_sq(&cand_a) <= norm_sq(&cand_b) {
            cand_a
        } else {
            cand_b
        };
        debug_assert!((&v1.0 + &v1.1 * BigInt::from(lambda.clone()))
            .mod_floor(&n)
            .is_zero());
        debug_assert!((&v2.0 + &v2.1 * BigInt::from(lambda.clone()))
            .mod_floor(&n)
            .is_zero());
        debug_assert!(v1.0.abs() > BigInt::zero());
        (beta, lambda, v1, v2)
    })
}

impl ProjectivePoint {
    /// Apply the CM endomorphism `ψ(X, Y, Z) = (β·X, Y, Z)` (cost: 1M).
    #[inline]
    pub fn endomorphism_psi(&self) -> Self {
        let (beta, _, _, _) = secp256k1_glv_params();
        ProjectivePoint {
            x: self.x.mul(beta),
            y: self.y,
            z: self.z,
        }
    }

    /// Decompose a scalar `k mod n` via the `secp256k1` `Z[ω]` Babai lattice
    /// into `(neg1, |k1|, neg2, |k2|)` with `k ≡ (±|k1|) + (±|k2|)·λ (mod n)`
    /// and `|k1|, |k2| < 2^128`.
    fn decompose_glv_scalar(k: &BigUint) -> (bool, BigUint, bool, BigUint) {
        use num_bigint::BigInt;
        use num_integer::Integer;
        use num_traits::{Signed, Zero};

        let (_, _, v1, v2) = secp256k1_glv_params();
        let n_bu = BigUint::parse_bytes(
            b"FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141",
            16,
        )
        .unwrap();
        let k_mod = k % &n_bu;
        if k_mod.is_zero() {
            return (false, BigUint::zero(), false, BigUint::zero());
        }
        let k_i = BigInt::from(k_mod);
        let det = &v1.0 * &v2.1 - &v1.1 * &v2.0;
        let round_div = |num: BigInt, den: &BigInt| -> BigInt {
            if den.is_negative() {
                let d_pos: BigInt = -den;
                let n_adj: BigInt = -num;
                let half: BigInt = &d_pos >> 1usize;
                if n_adj >= BigInt::zero() {
                    (n_adj + half).div_floor(&d_pos)
                } else {
                    (n_adj - half).div_ceil(&d_pos)
                }
            } else {
                let half: BigInt = den >> 1usize;
                if num >= BigInt::zero() {
                    (num + half).div_floor(den)
                } else {
                    (num - half).div_ceil(den)
                }
            }
        };
        let b1 = round_div(&k_i * &v2.1, &det);
        let b2 = round_div(-(&k_i * &v1.1), &det);
        let k1 = &k_i - &b1 * &v1.0 - &b2 * &v2.0;
        let k2 = -(&b1 * &v1.1 + &b2 * &v2.1);
        (
            k1.is_negative(),
            k1.magnitude().clone(),
            k2.is_negative(),
            k2.magnitude().clone(),
        )
    }

    /// 4-dimensional GLV + Shamir multi-scalar multiplication `[u₁]P + [u₂]Q`
    /// on `secp256k1` (~128 doublings total instead of ~512 for two separate
    /// 256-bit scalar multiplications).
    pub fn lincomb_glv(p: &Self, u1: &BigUint, q: &Self, u2: &BigUint) -> Self {
        let (neg_p1, k_p1, neg_p2, k_p2) = Self::decompose_glv_scalar(u1);
        let (neg_q1, k_q1, neg_q2, k_q2) = Self::decompose_glv_scalar(u2);

        let max_bits = k_p1
            .bits()
            .max(k_p2.bits())
            .max(k_q1.bits())
            .max(k_q2.bits()) as usize;
        if max_bits == 0 {
            return ProjectivePoint::IDENTITY;
        }

        let b0 = if neg_p1 { p.neg() } else { *p };
        let psi_p = p.endomorphism_psi();
        let b1 = if neg_p2 { psi_p.neg() } else { psi_p };
        let b2 = if neg_q1 { q.neg() } else { *q };
        let psi_q = q.endomorphism_psi();
        let b3 = if neg_q2 { psi_q.neg() } else { psi_q };

        let mut tab = [ProjectivePoint::IDENTITY; 16];
        tab[1] = b0;
        tab[2] = b1;
        tab[3] = b0.add(&b1);
        tab[4] = b2;
        tab[5] = tab[1].add(&b2);
        tab[6] = tab[2].add(&b2);
        tab[7] = tab[3].add(&b2);
        tab[8] = b3;
        for m in 1..8 {
            tab[8 + m] = tab[m].add(&b3);
        }

        let mut acc = ProjectivePoint::IDENTITY;
        for bit in (0..max_bits).rev() {
            if !bool::from(acc.is_identity()) {
                acc = acc.double();
            }
            let b = bit as u64;
            let idx = (k_p1.bit(b) as usize)
                | ((k_p2.bit(b) as usize) << 1)
                | ((k_q1.bit(b) as usize) << 2)
                | ((k_q2.bit(b) as usize) << 3);
            if idx != 0 {
                acc = if bool::from(acc.is_identity()) {
                    tab[idx]
                } else {
                    acc.add(&tab[idx])
                };
            }
        }
        acc
    }

    /// 2D GLV scalar multiplication `[k]P = [k₁]P + [k₂]ψ(P)` using Babai
    /// nearest-plane lattice decomposition over `Z[ω]` and Shamir's 2-bit
    /// joint table (4×4 = 16 precomputed combinations, ~65 joint steps =
    /// ~130 doublings + ~65 additions instead of 256 doublings + 256 adds).
    pub fn scalar_mul_glv(&self, k: &BigUint) -> Self {
        if bool::from(self.is_identity()) {
            return ProjectivePoint::IDENTITY;
        }
        let (neg1, u1, neg2, u2) = Self::decompose_glv_scalar(k);
        let max_bits = u1.bits().max(u2.bits()) as usize;
        if max_bits == 0 {
            return ProjectivePoint::IDENTITY;
        }

        let p1 = if neg1 { self.neg() } else { *self };
        let psi_p = self.endomorphism_psi();
        let p2 = if neg2 { psi_p.neg() } else { psi_p };

        // 2-bit × 2-bit Shamir table: T[d1 + 4*d2] = [d1]P1 + [d2]P2 for d1, d2 ∈ 0..4.
        let p1_2 = p1.double();
        let p1_3 = p1_2.add(&p1);
        let row1 = [ProjectivePoint::IDENTITY, p1, p1_2, p1_3];

        let p2_2 = p2.double();
        let p2_3 = p2_2.add(&p2);
        let row2 = [ProjectivePoint::IDENTITY, p2, p2_2, p2_3];

        let mut tab = [ProjectivePoint::IDENTITY; 16];
        for d2 in 0..4 {
            for d1 in 0..4 {
                tab[d1 + 4 * d2] = match (d1, d2) {
                    (0, 0) => ProjectivePoint::IDENTITY,
                    (_, 0) => row1[d1],
                    (0, _) => row2[d2],
                    _ => row1[d1].add(&row2[d2]),
                };
            }
        }

        let top_pair = max_bits.div_ceil(2);
        let mut acc = ProjectivePoint::IDENTITY;
        for step in (0..top_pair).rev() {
            if step + 1 < top_pair {
                acc = acc.double().double();
            }
            let b_lo = (2 * step) as u64;
            let b_hi = b_lo + 1;
            let d1 = (u1.bit(b_lo) as usize) | ((u1.bit(b_hi) as usize) << 1);
            let d2 = (u2.bit(b_lo) as usize) | ((u2.bit(b_hi) as usize) << 1);
            let idx = d1 + 4 * d2;
            if idx != 0 {
                acc = if bool::from(acc.is_identity()) {
                    tab[idx]
                } else {
                    acc.add(&tab[idx])
                };
            }
        }
        acc
    }
}

/// Public 2D GLV scalar multiplication on secp256k1, returning an affine [`Point`].
pub fn scalar_mul_glv(point: &Point, k: &BigUint, curve: &CurveParams) -> Point {
    if curve.name == "secp256k1" {
        ProjectivePoint::from_textbook(point)
            .scalar_mul_glv(k)
            .to_textbook(&curve.p)
    } else {
        point.scalar_mul(k, &curve.a_fe())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ecc::curve::CurveParams;
    use crate::ecc::field::FieldElement;
    use crate::ecc::point::Point;
    use num_bigint::BigUint;
    use num_traits::Zero;

    fn secp() -> CurveParams {
        CurveParams::secp256k1()
    }

    /// Convert a textbook `Point` to a `ProjectivePoint` for cross-checking.
    fn proj_from_textbook(p: &Point) -> ProjectivePoint {
        match p {
            Point::Infinity => ProjectivePoint::IDENTITY,
            Point::Affine { x, y } => {
                let xu = U256::from_biguint(&x.value);
                let yu = U256::from_biguint(&y.value);
                ProjectivePoint::from_affine(&xu, &yu)
            }
        }
    }

    /// Compare a `ProjectivePoint` to a textbook `Point` by mapping the
    /// projective one back to affine and comparing canonical coordinates.
    fn proj_eq_textbook(pp: &ProjectivePoint, p: &Point) -> bool {
        match (pp.to_affine(), p) {
            (None, Point::Infinity) => true,
            (Some((x, y)), Point::Affine { x: xf, y: yf }) => {
                x.to_biguint() == xf.value && y.to_biguint() == yf.value
            }
            _ => false,
        }
    }

    #[test]
    fn b_constant_is_correct() {
        let want = SecpFieldElement::from_biguint(&BigUint::from(7u8));
        assert_eq!(B_FE, want);
    }

    #[test]
    fn b3_constant_is_correct() {
        let want = SecpFieldElement::from_biguint(&BigUint::from(21u8));
        assert_eq!(B3_FE, want);
    }

    #[test]
    fn identity_to_affine_is_none() {
        assert!(ProjectivePoint::IDENTITY.to_affine().is_none());
        assert!(bool::from(ProjectivePoint::IDENTITY.is_identity()));
    }

    #[test]
    fn from_affine_roundtrips() {
        let g = secp().generator();
        let (gx_bu, gy_bu) = match &g {
            Point::Affine { x, y } => (x.value.clone(), y.value.clone()),
            Point::Infinity => panic!("generator is not infinity"),
        };
        let pp =
            ProjectivePoint::from_affine(&U256::from_biguint(&gx_bu), &U256::from_biguint(&gy_bu));
        let (x_back, y_back) = pp.to_affine().unwrap();
        assert_eq!(x_back.to_biguint(), gx_bu);
        assert_eq!(y_back.to_biguint(), gy_bu);
    }

    #[test]
    fn add_matches_textbook_for_distinct_points() {
        let curve = secp();
        let g = curve.generator();
        let a = curve.a_fe();
        let g2 = g.double(&a);
        let g3_textbook = g.add(&g2, &a);

        let pg = proj_from_textbook(&g);
        let pg2 = proj_from_textbook(&g2);
        let pg3 = pg.add(&pg2);

        assert!(proj_eq_textbook(&pg3, &g3_textbook));
    }

    #[test]
    fn add_matches_textbook_for_doubling_via_add() {
        let curve = secp();
        let g = curve.generator();
        let a = curve.a_fe();
        let g2_textbook = g.double(&a);

        let pg = proj_from_textbook(&g);
        let pg_plus_pg = pg.add(&pg);

        assert!(proj_eq_textbook(&pg_plus_pg, &g2_textbook));
    }

    #[test]
    fn double_matches_textbook() {
        let curve = secp();
        let g = curve.generator();
        let a = curve.a_fe();
        let g2_textbook = g.double(&a);

        let pg = proj_from_textbook(&g);
        let pg2 = pg.double();

        assert!(proj_eq_textbook(&pg2, &g2_textbook));
    }

    #[test]
    fn add_with_identity_is_identity_law() {
        let g = secp().generator();
        let pg = proj_from_textbook(&g);
        let lhs = pg.add(&ProjectivePoint::IDENTITY);
        let rhs = ProjectivePoint::IDENTITY.add(&pg);
        assert!(proj_eq_textbook(&lhs, &g));
        assert!(proj_eq_textbook(&rhs, &g));
    }

    #[test]
    fn add_with_neg_yields_identity() {
        let g = secp().generator();
        let pg = proj_from_textbook(&g);
        let neg_pg = pg.neg();
        let sum = pg.add(&neg_pg);
        assert!(bool::from(sum.is_identity()));
    }

    #[test]
    fn scalar_mul_ct_matches_textbook_small_scalars() {
        let curve = secp();
        let g = curve.generator();
        let a_fe = curve.a_fe();
        let pg = proj_from_textbook(&g);
        for k in 0u64..=10 {
            let k_bu = BigUint::from(k);
            let want = g.scalar_mul_ct(&k_bu, &a_fe, 4);
            let got = pg.scalar_mul_ct(&k_bu, 4);
            assert!(proj_eq_textbook(&got, &want), "mismatch at k={}", k);
        }
    }

    #[test]
    fn scalar_mul_ct_matches_textbook_full_size_scalars() {
        let curve = secp();
        let g = curve.generator();
        let a_fe = curve.a_fe();
        let pg = proj_from_textbook(&g);
        let bits = curve.order_bits();
        for k_hex in [
            "1",
            "2",
            "deadbeef",
            // Just under the curve order
            "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364140",
            // Random 256-bit value (fits in scalar range)
            "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        ] {
            let k = BigUint::parse_bytes(k_hex.as_bytes(), 16).unwrap();
            let want = g.scalar_mul_ct(&k, &a_fe, bits);
            let got = pg.scalar_mul_ct(&k, bits);
            assert!(proj_eq_textbook(&got, &want), "mismatch at k={}", k_hex);
        }
    }

    #[test]
    fn glv_endomorphism_and_scalar_mul_match_reference() {
        let curve = secp();
        let g = curve.generator();
        let a_fe = curve.a_fe();
        let pg = proj_from_textbook(&g);
        let (beta, lambda, _, _) = secp256k1_glv_params();

        // Certificate checks on (β, λ): β³ = 1, β ≠ 1, ψ(G) = [λ]G.
        assert_eq!(beta.sqr().mul(beta), SecpFieldElement::ONE);
        assert_ne!(*beta, SecpFieldElement::ONE);
        let psi_g = pg.endomorphism_psi();
        let lam_g = g.scalar_mul(&lambda, &a_fe);
        assert!(proj_eq_textbook(&psi_g, &lam_g));

        for k_hex in [
            "0",
            "1",
            "2",
            "3",
            "deadbeef",
            "5363ad4cc05c30e0a5261c028812645a122e22ea20816678df02967c1b23bd72",
            "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364140",
            "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        ] {
            let k = BigUint::parse_bytes(k_hex.as_bytes(), 16).unwrap();
            let want = g.scalar_mul(&k, &a_fe);
            let got = scalar_mul_glv(&g, &k, &curve);
            assert_eq!(got, want, "GLV scalar_mul mismatch at k={}", k_hex);
        }
    }

    #[test]
    fn cmov_selects_correctly() {
        let g = secp().generator();
        let pg = proj_from_textbook(&g);
        let id = ProjectivePoint::IDENTITY;

        let r0 = ProjectivePoint::cmov(&pg, &id, Choice::from(0));
        let r1 = ProjectivePoint::cmov(&pg, &id, Choice::from(1));

        assert!(proj_eq_textbook(&r0, &g));
        assert!(bool::from(r1.is_identity()));
    }

    /// Sanity: scalar mul by curve order should yield identity.
    #[test]
    fn scalar_mul_by_order_is_identity() {
        let curve = secp();
        let g = curve.generator();
        let pg = proj_from_textbook(&g);
        let n = curve.n.clone();
        let bits = curve.order_bits();
        let result = pg.scalar_mul_ct(&n, bits);
        assert!(bool::from(result.is_identity()));
        // (Defeat unused-import warning for FieldElement if reached here.)
        let _ = FieldElement::zero(BigUint::from(7u8));
    }

    /// Sanity: doubling identity stays identity.
    #[test]
    fn double_identity_is_identity() {
        let r = ProjectivePoint::IDENTITY.double();
        assert!(bool::from(r.is_identity()));
        // Suppress `Zero`-import warning if test set narrows.
        let _ = BigUint::zero();
    }
}
