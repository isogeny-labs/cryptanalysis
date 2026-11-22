//! Constant-time field arithmetic over P-256's prime field F_p.
//!
//! `p = 2^256 - 2^224 + 2^192 + 2^96 - 1`
//!
//! Mirrors [`crate::ecc::secp256k1_field`]: every value is held in
//! Montgomery form `a·R mod p` where `R = 2^256`, and arithmetic
//! delegates to the constant-time [`crate::ct_bignum::U256`]
//! primitives.  All Montgomery constants are computed at compile time
//! via [`crate::ct_bignum::compute_minv64`] and the `from_montgomery_*`
//! constructors, and are cross-checked against `num-bigint` reference
//! computations in this module's tests.
//!
//! See [`crate::ecc::secp256k1_field`] for the design rationale and a
//! more thorough writeup of the Montgomery-form invariants.

use crate::ct_bignum::{compute_minv64, Uint, U256};
use num_bigint::BigUint;
use subtle::{Choice, ConstantTimeEq};

/// P-256 prime modulus, as little-endian limbs.
///
/// `p = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF`
/// `  = 2^256 - 2^224 + 2^192 + 2^96 - 1`
pub const P: U256 = Uint([
    0xFFFF_FFFF_FFFF_FFFF,
    0x0000_0000_FFFF_FFFF,
    0x0000_0000_0000_0000,
    0xFFFF_FFFF_0000_0001,
]);

/// Montgomery constant `m' = -p^(-1) mod 2^64`.
pub const P_INV_LOW: u64 = compute_minv64(P.0[0]);

/// `R mod p`, where `R = 2^256`.  Equal to "1" in Montgomery form.
pub const R_MOD_P: U256 = Uint([
    0x0000_0000_0000_0001,
    0xFFFF_FFFF_0000_0000,
    0xFFFF_FFFF_FFFF_FFFF,
    0x0000_0000_FFFF_FFFE,
]);

/// `R^2 mod p`.  Used to convert canonical values into Montgomery form
/// via `mont_mul(a, R^2 mod p)`.
pub const R_SQUARED_MOD_P: U256 = Uint([
    0x0000_0000_0000_0003,
    0xFFFF_FFFB_FFFF_FFFF,
    0xFFFF_FFFF_FFFF_FFFE,
    0x0000_0004_FFFF_FFFD,
]);

/// Specialized constant-time Montgomery reduction for NIST P-256:
/// `p = 2^256 - 2^224 + 2^192 + 2^96 - 1`.
///
/// Since `p[0] = -1 (mod 2^64)`, each Montgomery step quotient is simply
/// `m = t[i]` (zero `p_inv_low` multiplications), and
/// `(t_i + m·p) / 2^64 = m·2^32 + m·(2^64 - 2^32 + 1)·2^128` requires
/// **zero** `64×64` multiplications — only 32-bit shifts and 128-bit adds!
#[inline(always)]
fn p256_mont_reduce(mut t: [u64; 8]) -> U256 {
    let mut extra: u64 = 0;
    let mut i = 0;
    while i < 4 {
        let m = t[i];
        let u: u128 = ((m as u128) << 64) - ((m as u128) << 32) + (m as u128);
        let u_lo = u as u64;
        let u_hi = (u >> 64) as u64;

        let mut acc = (t[i + 1] as u128) + ((m << 32) as u128);
        t[i + 1] = acc as u64;
        let mut carry = acc >> 64;

        acc = (t[i + 2] as u128) + ((m >> 32) as u128) + carry;
        t[i + 2] = acc as u64;
        carry = acc >> 64;

        acc = (t[i + 3] as u128) + (u_lo as u128) + carry;
        t[i + 3] = acc as u64;
        carry = acc >> 64;

        if i + 4 < 8 {
            acc = (t[i + 4] as u128) + (u_hi as u128) + carry;
            t[i + 4] = acc as u64;
            carry = acc >> 64;
            let mut k = i + 5;
            while k < 8 {
                acc = (t[k] as u128) + carry;
                t[k] = acc as u64;
                carry = acc >> 64;
                k += 1;
            }
            extra = extra.wrapping_add(carry as u64);
        } else {
            extra = extra.wrapping_add(u_hi).wrapping_add(carry as u64);
        }
        i += 1;
    }

    let result = Uint([t[4], t[5], t[6], t[7]]);
    let (sub, borrow) = U256::sbb(&result, &P);
    let need_sub = Choice::from(((extra | (borrow ^ 1)) & 1) as u8);
    U256::cmov(&result, &sub, need_sub)
}

#[inline(always)]
fn p256_mont_mul(a: &U256, b: &U256) -> U256 {
    let [a0, a1, a2, a3] = a.0;
    let [b0, b1, b2, b3] = b.0;

    let mut acc = (a0 as u128) * (b0 as u128);
    let t0 = acc as u64;
    acc = (acc >> 64) + (a1 as u128) * (b0 as u128);
    let mut t1 = acc as u64;
    acc = (acc >> 64) + (a2 as u128) * (b0 as u128);
    let mut t2 = acc as u64;
    acc = (acc >> 64) + (a3 as u128) * (b0 as u128);
    let mut t3 = acc as u64;
    let mut t4 = (acc >> 64) as u64;

    acc = (t1 as u128) + (a0 as u128) * (b1 as u128);
    t1 = acc as u64;
    acc = (t2 as u128) + (a1 as u128) * (b1 as u128) + (acc >> 64);
    t2 = acc as u64;
    acc = (t3 as u128) + (a2 as u128) * (b1 as u128) + (acc >> 64);
    t3 = acc as u64;
    acc = (t4 as u128) + (a3 as u128) * (b1 as u128) + (acc >> 64);
    t4 = acc as u64;
    let mut t5 = (acc >> 64) as u64;

    acc = (t2 as u128) + (a0 as u128) * (b2 as u128);
    t2 = acc as u64;
    acc = (t3 as u128) + (a1 as u128) * (b2 as u128) + (acc >> 64);
    t3 = acc as u64;
    acc = (t4 as u128) + (a2 as u128) * (b2 as u128) + (acc >> 64);
    t4 = acc as u64;
    acc = (t5 as u128) + (a3 as u128) * (b2 as u128) + (acc >> 64);
    t5 = acc as u64;
    let mut t6 = (acc >> 64) as u64;

    acc = (t3 as u128) + (a0 as u128) * (b3 as u128);
    t3 = acc as u64;
    acc = (t4 as u128) + (a1 as u128) * (b3 as u128) + (acc >> 64);
    t4 = acc as u64;
    acc = (t5 as u128) + (a2 as u128) * (b3 as u128) + (acc >> 64);
    t5 = acc as u64;
    acc = (t6 as u128) + (a3 as u128) * (b3 as u128) + (acc >> 64);
    t6 = acc as u64;
    let t7 = (acc >> 64) as u64;

    p256_mont_reduce([t0, t1, t2, t3, t4, t5, t6, t7])
}

#[inline(always)]
fn p256_mont_sqr(a: &U256) -> U256 {
    let [a0, a1, a2, a3] = a.0;

    let mut acc = (a0 as u128) * (a1 as u128);
    let t1 = acc as u64;
    acc = (acc >> 64) + (a0 as u128) * (a2 as u128);
    let t2 = acc as u64;
    acc = (acc >> 64) + (a0 as u128) * (a3 as u128);
    let mut t3 = acc as u64;
    let mut t4 = (acc >> 64) as u64;

    acc = (t3 as u128) + (a1 as u128) * (a2 as u128);
    t3 = acc as u64;
    acc = (t4 as u128) + (a1 as u128) * (a3 as u128) + (acc >> 64);
    t4 = acc as u64;
    let mut t5 = (acc >> 64) as u64;

    acc = (t5 as u128) + (a2 as u128) * (a3 as u128);
    t5 = acc as u64;
    let t6 = (acc >> 64) as u64;

    let t7 = t6 >> 63;
    let d6 = (t6 << 1) | (t5 >> 63);
    let d5 = (t5 << 1) | (t4 >> 63);
    let d4 = (t4 << 1) | (t3 >> 63);
    let d3 = (t3 << 1) | (t2 >> 63);
    let d2 = (t2 << 1) | (t1 >> 63);
    let d1 = t1 << 1;

    let s0 = (a0 as u128) * (a0 as u128);
    let r0 = s0 as u64;
    acc = (d1 as u128) + (s0 >> 64);
    let r1 = acc as u64;

    let s1 = (a1 as u128) * (a1 as u128);
    acc = (d2 as u128) + (s1 as u128 & 0xFFFF_FFFF_FFFF_FFFF) + (acc >> 64);
    let r2 = acc as u64;
    acc = (d3 as u128) + (s1 >> 64) + (acc >> 64);
    let r3 = acc as u64;

    let s2 = (a2 as u128) * (a2 as u128);
    acc = (d4 as u128) + (s2 as u128 & 0xFFFF_FFFF_FFFF_FFFF) + (acc >> 64);
    let r4 = acc as u64;
    acc = (d5 as u128) + (s2 >> 64) + (acc >> 64);
    let r5 = acc as u64;

    let s3 = (a3 as u128) * (a3 as u128);
    acc = (d6 as u128) + (s3 as u128 & 0xFFFF_FFFF_FFFF_FFFF) + (acc >> 64);
    let r6 = acc as u64;
    acc = (t7 as u128) + (s3 >> 64) + (acc >> 64);
    let r7 = acc as u64;

    p256_mont_reduce([r0, r1, r2, r3, r4, r5, r6, r7])
}

/// A field element over P-256's prime, stored in Montgomery form.
#[derive(Copy, Clone, Debug)]
pub struct P256FieldElement(U256);

impl P256FieldElement {
    pub const ZERO: P256FieldElement = P256FieldElement(U256::ZERO);
    pub const ONE: P256FieldElement = P256FieldElement(R_MOD_P);

    pub fn from_canonical(a: &U256) -> Self {
        P256FieldElement(p256_mont_mul(a, &R_SQUARED_MOD_P))
    }

    pub fn to_canonical(&self) -> U256 {
        p256_mont_reduce([
            self.0 .0[0],
            self.0 .0[1],
            self.0 .0[2],
            self.0 .0[3],
            0,
            0,
            0,
            0,
        ])
    }

    pub fn from_biguint(v: &BigUint) -> Self {
        let p_bu = P.to_biguint();
        let reduced = U256::from_biguint(&(v % &p_bu));
        Self::from_canonical(&reduced)
    }

    pub fn to_biguint(&self) -> BigUint {
        self.to_canonical().to_biguint()
    }

    pub fn to_bytes_be(&self) -> [u8; 32] {
        self.to_canonical().to_bytes_be()
    }

    pub fn from_bytes_be(bytes: &[u8; 32]) -> Self {
        Self::from_canonical(&U256::from_bytes_be(bytes))
    }

    #[inline]
    pub fn add(&self, other: &Self) -> Self {
        P256FieldElement(self.0.add_mod(&other.0, &P))
    }

    #[inline]
    pub fn sub(&self, other: &Self) -> Self {
        P256FieldElement(self.0.sub_mod(&other.0, &P))
    }

    #[inline]
    pub fn mul(&self, other: &Self) -> Self {
        P256FieldElement(p256_mont_mul(&self.0, &other.0))
    }

    #[inline]
    pub fn sqr(&self) -> Self {
        P256FieldElement(p256_mont_sqr(&self.0))
    }

    #[inline]
    pub fn neg(&self) -> Self {
        P256FieldElement(U256::ZERO.sub_mod(&self.0, &P))
    }

    /// Multiplicative inverse via Fermat: `a^(p-2) mod p` using a
    /// fixed constant-time addition chain (255 squarings + 12
    /// multiplications; returns zero for zero).
    ///
    /// Exponent identity:
    /// `p - 2 = (2^32 - 1)*2^224 + 2^192 + (2^94 - 1)*2^2 + 1`.
    pub fn inv(&self) -> Self {
        #[inline]
        fn sqr_n(mut x: P256FieldElement, n: usize) -> P256FieldElement {
            for _ in 0..n {
                x = x.sqr();
            }
            x
        }

        let x1 = *self;
        let x2 = x1.sqr().mul(&x1);
        let x3 = x2.sqr().mul(&x1);
        let x6 = sqr_n(x3, 3).mul(&x3);
        let x12 = sqr_n(x6, 6).mul(&x6);
        let x15 = sqr_n(x12, 3).mul(&x3);
        let x30 = sqr_n(x15, 15).mul(&x15);
        let x32 = sqr_n(x30, 2).mul(&x2);

        let mut t = sqr_n(x32, 32).mul(&x1); // 2^64 - 2^32 + 1
        t = sqr_n(t, 128).mul(&x32);
        t = sqr_n(t, 32).mul(&x32);
        t = sqr_n(t, 30).mul(&x30);
        sqr_n(t, 2).mul(&x1)
    }

    #[inline]
    pub fn ct_eq(&self, other: &Self) -> Choice {
        self.0.ct_eq_full(&other.0)
    }

    #[inline]
    pub fn ct_is_zero(&self) -> Choice {
        self.0.ct_is_zero()
    }

    #[inline]
    pub fn cmov(a: &Self, b: &Self, choice: Choice) -> Self {
        P256FieldElement(U256::cmov(&a.0, &b.0, choice))
    }

    #[inline]
    pub fn cswap(a: &mut Self, b: &mut Self, choice: Choice) {
        U256::cswap(&mut a.0, &mut b.0, choice);
    }

    #[inline]
    pub fn as_montgomery(&self) -> &U256 {
        &self.0
    }

    pub const fn from_montgomery_unchecked(limbs: U256) -> Self {
        P256FieldElement(limbs)
    }
}

impl PartialEq for P256FieldElement {
    fn eq(&self, other: &Self) -> bool {
        bool::from(self.ct_eq(other))
    }
}

impl Eq for P256FieldElement {}

impl ConstantTimeEq for P256FieldElement {
    fn ct_eq(&self, other: &Self) -> Choice {
        self.ct_eq(other)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use num_bigint::BigUint;
    use num_traits::{One, Zero};

    fn p_bu() -> BigUint {
        P.to_biguint()
    }

    fn samples() -> Vec<BigUint> {
        let p = p_bu();
        vec![
            BigUint::zero(),
            BigUint::one(),
            BigUint::from(2u8),
            BigUint::from(0xdeadbeefu64),
            BigUint::from(1u8) << 32,
            BigUint::from(1u8) << 96, // exercises the limb boundary in P-256's prime
            BigUint::from(1u8) << 192,
            &p - 1u8,
            &p - 2u8,
            &p / 2u8,
            (&p / 2u8) + 1u8,
            BigUint::parse_bytes(
                b"DEADBEEFCAFEBABE0123456789ABCDEF112233445566778899AABBCCDDEEFF00",
                16,
            )
            .unwrap(),
            BigUint::parse_bytes(
                b"FEDCBA9876543210FEDCBA9876543210FEDCBA9876543210FEDCBA9876543210",
                16,
            )
            .unwrap(),
        ]
    }

    #[test]
    fn p_constant_matches_curve_params() {
        let want = U256::from_biguint(&crate::ecc::CurveParams::p256().p);
        assert!(bool::from(P.ct_eq_full(&want)));
    }

    #[test]
    fn r_mod_p_constant_is_correct() {
        let r = BigUint::one() << 256;
        let want = U256::from_biguint(&(&r % p_bu()));
        assert!(bool::from(R_MOD_P.ct_eq_full(&want)));
    }

    #[test]
    fn r_squared_constant_is_correct() {
        let r = BigUint::one() << 256;
        let want = U256::from_biguint(&((&r * &r) % p_bu()));
        assert!(bool::from(R_SQUARED_MOD_P.ct_eq_full(&want)));
    }

    #[test]
    fn p_inv_low_consistent_with_compute_minv64() {
        let prod = P.0[0].wrapping_mul(P_INV_LOW);
        assert_eq!(prod.wrapping_add(1), 0);
    }

    #[test]
    fn from_to_canonical_roundtrips() {
        for v in samples() {
            let fe = P256FieldElement::from_biguint(&v);
            assert_eq!(fe.to_biguint(), v);
        }
    }

    #[test]
    fn add_matches_biguint() {
        let p = p_bu();
        for a in samples() {
            for b in samples() {
                let fa = P256FieldElement::from_biguint(&a);
                let fb = P256FieldElement::from_biguint(&b);
                assert_eq!(fa.add(&fb).to_biguint(), (&a + &b) % &p);
            }
        }
    }

    #[test]
    fn sub_matches_biguint() {
        let p = p_bu();
        for a in samples() {
            for b in samples() {
                let fa = P256FieldElement::from_biguint(&a);
                let fb = P256FieldElement::from_biguint(&b);
                let want = (&p + (&a % &p) - (&b % &p)) % &p;
                assert_eq!(fa.sub(&fb).to_biguint(), want);
            }
        }
    }

    #[test]
    fn mul_matches_biguint() {
        let p = p_bu();
        for a in samples() {
            for b in samples() {
                let fa = P256FieldElement::from_biguint(&a);
                let fb = P256FieldElement::from_biguint(&b);
                assert_eq!(fa.mul(&fb).to_biguint(), (&a * &b) % &p);
            }
        }
    }

    #[test]
    fn sqr_matches_mul_self() {
        let p = p_bu();
        for a in samples() {
            let fa = P256FieldElement::from_biguint(&a);
            assert_eq!(fa.sqr().to_biguint(), (&a * &a) % &p);
            assert_eq!(fa.sqr(), fa.mul(&fa));
        }
    }

    #[test]
    fn neg_matches_biguint() {
        let p = p_bu();
        for a in samples() {
            let fa = P256FieldElement::from_biguint(&a);
            let want = (&p - (&a % &p)) % &p;
            assert_eq!(fa.neg().to_biguint(), want);
        }
    }

    #[test]
    fn inv_times_self_is_one() {
        for a in samples() {
            if a.is_zero() {
                continue;
            }
            let fa = P256FieldElement::from_biguint(&a);
            assert_eq!(fa.mul(&fa.inv()).to_biguint(), BigUint::one());
        }
    }
}
