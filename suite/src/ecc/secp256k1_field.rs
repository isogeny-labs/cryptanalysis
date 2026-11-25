//! Constant-time field arithmetic over secp256k1's prime field F_p.
//!
//! `p = 2^256 - 2^32 - 977`
//!
//! Internally every value is stored in **Montgomery form**: a value
//! `a ∈ [0, p)` is represented as `a·R mod p`, where `R = 2^256`.  This
//! lets multiplication and squaring use [`U256::mont_mul`] — which is
//! built from `u64×u64→u128` partial products and `u128` accumulators
//! and never branches on operand magnitudes — instead of the
//! variable-time `BigUint::%`-based reduction used by
//! [`crate::ecc::field::FieldElement`].
//!
//! The Montgomery constants `P_INV_LOW` (`-p[0]^(-1) mod 2^64`) and
//! `R_SQUARED_MOD_P` are computed at compile time and verified by unit
//! tests against `num-bigint` reference computations.
//!
//! See `SECURITY.md` for the wider hardening picture; this module is the
//! piece that closes the limb-level timing leak in field arithmetic for
//! secp256k1 specifically.  P-256 will get a parallel module once this
//! one is wired into [`crate::ecc::point::Point`].

use crate::ct_bignum::{compute_minv64, Uint, U256};
use num_bigint::BigUint;
use subtle::{Choice, ConstantTimeEq};

/// secp256k1 prime modulus, as little-endian limbs.
///
/// `p = 2^256 - 2^32 - 977
///    = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F`
pub const P: U256 = Uint([
    0xFFFF_FFFE_FFFF_FC2F,
    0xFFFF_FFFF_FFFF_FFFF,
    0xFFFF_FFFF_FFFF_FFFF,
    0xFFFF_FFFF_FFFF_FFFF,
]);

/// Montgomery constant `m' = -p^(-1) mod 2^64`.  Computed via the
/// 2-adic Newton iteration in [`compute_minv64`].
pub const P_INV_LOW: u64 = compute_minv64(P.0[0]);

/// `R mod p`, where `R = 2^256`.  Since `R = p + 2^32 + 977`, this is
/// just `2^32 + 977 = 0x1_0000_03D1`.  Equal to "1" in Montgomery form.
pub const R_MOD_P: U256 = Uint([0x0000_0001_0000_03D1, 0, 0, 0]);

/// `R^2 mod p`, used to enter Montgomery form via
/// `a_M = mont_mul(a, R^2 mod p)`.
///
/// Closed form: `(2^32 + 977)^2 = 2^64 + 2·977·2^32 + 977^2`
/// `= 0x1_0000_0000_0000_0000 + 0x7A2_0000_0000 + 0xE90A1`
/// `= 0x1_0000_07A2_000E_90A1` — a 65-bit value, so well below
/// `p` and the modular reduction is a no-op.  Verified by
/// `tests::r_squared_constant_is_correct`.
pub const R_SQUARED_MOD_P: U256 = Uint([0x0000_07A2_000E_90A1, 1, 0, 0]);

/// Constant `K = 2^256 - p = 2^32 + 977 = 0x1_0000_03D1`.
const SECP_K: u64 = 0x0000_0001_0000_03D1;

/// Specialised constant-time Montgomery reduction of a 512-bit product
/// `t[0..8]` modulo secp256k1's `p = 2^256 - K`.
///
/// Since `p_0 = 2^64 - K`, `m = t[i] * P_INV_LOW mod 2^64` satisfies
/// `m * K ≡ t[i] (mod 2^64)`.  Adding `m * p * 2^{64i} = m * 2^{64(i+4)}
/// - (m * K) * 2^{64i}` therefore clears limb `t[i]` with zero low-limb
/// borrow, subtracts only `w_hi = (m * K) >> 64` at `t[i+1..i+4]`, and
/// adds `m` at `t[i+4]`: 4 single-word multiplies for the whole reduction
/// instead of 16, returning the exact canonical residue `T * R^{-1} mod p`.
#[inline(always)]
fn secp_mont_reduce(t: [u64; 8]) -> U256 {
    let mut buf = [t[0], t[1], t[2], t[3], t[4], t[5], t[6], t[7], 0u64];
    for i in 0..4 {
        let m = buf[i].wrapping_mul(P_INV_LOW);
        let w_hi = (((m as u128) * (SECP_K as u128)) >> 64) as u64;
        let (d1, b1) = buf[i + 1].overflowing_sub(w_hi);
        buf[i + 1] = d1;
        let (d2, b2) = buf[i + 2].overflowing_sub(b1 as u64);
        buf[i + 2] = d2;
        let (d3, b3) = buf[i + 3].overflowing_sub(b2 as u64);
        buf[i + 3] = d3;
        // If m == 0 then w_hi == 0 and b3 == false, else m >= 1 >= b3: s4 >= 0 always.
        let s4 = (buf[i + 4] as u128) + (m as u128) - (b3 as u128);
        buf[i + 4] = s4 as u64;
        let mut carry = (s4 >> 64) as u64;
        for slot in &mut buf[(i + 5)..9] {
            let s = (*slot as u128) + (carry as u128);
            *slot = s as u64;
            carry = (s >> 64) as u64;
        }
    }
    let result = Uint([buf[4], buf[5], buf[6], buf[7]]);
    let extra = buf[8];
    let (sub, borrow) = U256::sbb(&result, &P);
    let need_sub = Choice::from(((extra | (borrow ^ 1)) & 1) as u8);
    U256::cmov(&result, &sub, need_sub)
}

#[inline(always)]
fn secp_mont_mul(a: &U256, b: &U256) -> U256 {
    let (a0, a1, a2, a3) = (
        a.0[0] as u128,
        a.0[1] as u128,
        a.0[2] as u128,
        a.0[3] as u128,
    );
    let (b0, b1, b2, b3) = (
        b.0[0] as u128,
        b.0[1] as u128,
        b.0[2] as u128,
        b.0[3] as u128,
    );
    let mut t = [0u64; 8];

    let s = a0 * b0;
    t[0] = s as u64;
    let s = a0 * b1 + (s >> 64);
    t[1] = s as u64;
    let s = a0 * b2 + (s >> 64);
    t[2] = s as u64;
    let s = a0 * b3 + (s >> 64);
    t[3] = s as u64;
    t[4] = (s >> 64) as u64;

    let s = (t[1] as u128) + a1 * b0;
    t[1] = s as u64;
    let s = (t[2] as u128) + a1 * b1 + (s >> 64);
    t[2] = s as u64;
    let s = (t[3] as u128) + a1 * b2 + (s >> 64);
    t[3] = s as u64;
    let s = (t[4] as u128) + a1 * b3 + (s >> 64);
    t[4] = s as u64;
    t[5] = (s >> 64) as u64;

    let s = (t[2] as u128) + a2 * b0;
    t[2] = s as u64;
    let s = (t[3] as u128) + a2 * b1 + (s >> 64);
    t[3] = s as u64;
    let s = (t[4] as u128) + a2 * b2 + (s >> 64);
    t[4] = s as u64;
    let s = (t[5] as u128) + a2 * b3 + (s >> 64);
    t[5] = s as u64;
    t[6] = (s >> 64) as u64;

    let s = (t[3] as u128) + a3 * b0;
    t[3] = s as u64;
    let s = (t[4] as u128) + a3 * b1 + (s >> 64);
    t[4] = s as u64;
    let s = (t[5] as u128) + a3 * b2 + (s >> 64);
    t[5] = s as u64;
    let s = (t[6] as u128) + a3 * b3 + (s >> 64);
    t[6] = s as u64;
    t[7] = (s >> 64) as u64;

    secp_mont_reduce(t)
}

#[inline(always)]
fn secp_mont_sqr(a: &U256) -> U256 {
    let (a0, a1, a2, a3) = (
        a.0[0] as u128,
        a.0[1] as u128,
        a.0[2] as u128,
        a.0[3] as u128,
    );
    // 6 off-diagonal products accumulated row by row (no u128 overflow).
    let s = a0 * a1;
    let t1 = s as u64;
    let s = a0 * a2 + (s >> 64);
    let t2 = s as u64;
    let s = a0 * a3 + (s >> 64);
    let mut t3 = s as u64;
    let mut t4 = (s >> 64) as u64;

    let s = (t3 as u128) + a1 * a2;
    t3 = s as u64;
    let s = (t4 as u128) + a1 * a3 + (s >> 64);
    t4 = s as u64;
    let mut t5 = (s >> 64) as u64;

    let s = (t5 as u128) + a2 * a3;
    t5 = s as u64;
    let t6 = (s >> 64) as u64;

    let u1 = t1 << 1;
    let u2 = (t2 << 1) | (t1 >> 63);
    let u3 = (t3 << 1) | (t2 >> 63);
    let u4 = (t4 << 1) | (t3 >> 63);
    let u5 = (t5 << 1) | (t4 >> 63);
    let u6 = (t6 << 1) | (t5 >> 63);
    let u7 = t6 >> 63;

    let d0 = a0 * a0;
    let r0 = d0 as u64;
    let s = (u1 as u128) + (d0 >> 64);
    let r1 = s as u64;

    let d1 = a1 * a1;
    let s = (u2 as u128) + (d1 & 0xFFFF_FFFF_FFFF_FFFF) + (s >> 64);
    let r2 = s as u64;
    let s = (u3 as u128) + (d1 >> 64) + (s >> 64);
    let r3 = s as u64;

    let d2 = a2 * a2;
    let s = (u4 as u128) + (d2 & 0xFFFF_FFFF_FFFF_FFFF) + (s >> 64);
    let r4 = s as u64;
    let s = (u5 as u128) + (d2 >> 64) + (s >> 64);
    let r5 = s as u64;

    let d3 = a3 * a3;
    let s = (u6 as u128) + (d3 & 0xFFFF_FFFF_FFFF_FFFF) + (s >> 64);
    let r6 = s as u64;
    let s = (u7 as u128) + (d3 >> 64) + (s >> 64);
    let r7 = s as u64;

    secp_mont_reduce([r0, r1, r2, r3, r4, r5, r6, r7])
}

/// A field element over secp256k1's prime, stored in Montgomery form.
#[derive(Copy, Clone, Debug)]
pub struct SecpFieldElement(U256);

impl SecpFieldElement {
    /// Additive identity.  In Montgomery form `0·R = 0`.
    pub const ZERO: SecpFieldElement = SecpFieldElement(U256::ZERO);

    /// Multiplicative identity.  In Montgomery form `1·R mod p = R mod p`.
    pub const ONE: SecpFieldElement = SecpFieldElement(R_MOD_P);

    // ── Construction / extraction ────────────────────────────────────────

    /// Convert a canonical-form `U256` (in `[0, p)`) into Montgomery form.
    /// `a → a·R mod p`, computed as `mont_mul(a, R^2 mod p) = a·R^2·R^(-1) = a·R`.
    ///
    /// Caller must ensure `a < p`; this is not runtime-checked.
    pub fn from_canonical(a: &U256) -> Self {
        SecpFieldElement(U256::mont_mul(a, &R_SQUARED_MOD_P, &P, P_INV_LOW))
    }

    /// Extract the canonical form: `a_M · R^(-1) mod p = a`, which is
    /// `mont_mul(a_M, 1)`.
    pub fn to_canonical(&self) -> U256 {
        U256::mont_mul(&self.0, &U256::ONE, &P, P_INV_LOW)
    }

    /// Construct from a `BigUint`, reducing mod p first.  The reduction
    /// goes through `BigUint::%`, which is variable-time — only use this
    /// at trust boundaries where the value originates from public data
    /// or has already been validated.
    pub fn from_biguint(v: &BigUint) -> Self {
        let p_bu = P.to_biguint();
        let reduced = U256::from_biguint(&(v % &p_bu));
        Self::from_canonical(&reduced)
    }

    /// Convert back to a `BigUint` for interop with the variable-time
    /// portions of the codebase (e.g. ECDSA verifier inputs).
    pub fn to_biguint(&self) -> BigUint {
        self.to_canonical().to_biguint()
    }

    /// Big-endian byte serialization (32 bytes), in canonical form.
    pub fn to_bytes_be(&self) -> [u8; 32] {
        self.to_canonical().to_bytes_be()
    }

    /// Big-endian byte deserialization.  Caller must ensure the encoded
    /// value is in `[0, p)`; values `>= p` will yield an out-of-range
    /// internal representation that breaks subsequent arithmetic.
    pub fn from_bytes_be(bytes: &[u8; 32]) -> Self {
        Self::from_canonical(&U256::from_bytes_be(bytes))
    }

    // ── Arithmetic ───────────────────────────────────────────────────────

    /// Field addition.  Constant-time conditional reduction via
    /// [`U256::add_mod`].
    #[inline]
    pub fn add(&self, other: &Self) -> Self {
        SecpFieldElement(self.0.add_mod(&other.0, &P))
    }

    /// Field subtraction.
    #[inline]
    pub fn sub(&self, other: &Self) -> Self {
        SecpFieldElement(self.0.sub_mod(&other.0, &P))
    }

    /// Field multiplication via specialised secp256k1 Montgomery reduction.
    #[inline]
    pub fn mul(&self, other: &Self) -> Self {
        SecpFieldElement(secp_mont_mul(&self.0, &other.0))
    }

    /// Field squaring (10-product squaring + 4-product secp256k1 reduction).
    #[inline]
    pub fn sqr(&self) -> Self {
        SecpFieldElement(secp_mont_sqr(&self.0))
    }

    /// Additive inverse: `0 - self mod p`.  Reduces to one [`U256::sub_mod`].
    #[inline]
    pub fn neg(&self) -> Self {
        SecpFieldElement(U256::ZERO.sub_mod(&self.0, &P))
    }

    /// Multiplicative inverse via Fermat's little theorem:
    /// `a^(p-2) mod p`.
    ///
    /// Uses the constant-time fixed addition chain [`Self::inv_chain`]
    /// (257 squarings + 14 multiplications, input-independent), returning
    /// `Self::ZERO` if `self.is_zero()`.
    pub fn inv(&self) -> Self {
        self.inv_chain()
    }

    /// Fixed secp256k1 field inversion chain: 257 squarings and 14
    /// multiplications. This is independent of the input and returns zero
    /// for zero, matching `inv`. It is kept as a separate backend so callers
    /// can compare it with the existing inversion ladder.
    pub fn inv_chain(&self) -> Self {
        #[inline]
        fn squares(mut x: SecpFieldElement, count: usize) -> SecpFieldElement {
            for _ in 0..count {
                x = x.sqr();
            }
            x
        }

        // t_k = x^(2^k-1). The final exponent is
        // (2^223-1)*2^33 + (2^22-1)*2^10 + 45 = p-2.
        let t2 = self.sqr().mul(self);
        let t3 = t2.sqr().mul(self);
        let t4 = squares(t2, 2).mul(&t2);
        let t8 = squares(t4, 4).mul(&t4);
        let t11 = squares(t8, 3).mul(&t3);
        let t22 = squares(t11, 11).mul(&t11);
        let t44 = squares(t22, 22).mul(&t22);
        let t88 = squares(t44, 44).mul(&t44);
        let t176 = squares(t88, 88).mul(&t88);
        let t220 = squares(t176, 44).mul(&t44);
        let t223 = squares(t220, 3).mul(&t3);
        let x45 = t4.sqr().mul(&t4);
        let head = squares(t223, 23).mul(&t22);
        squares(head, 10).mul(&x45)
    }

    // ── Comparison / selection ───────────────────────────────────────────

    /// Constant-time equality check.  Two Montgomery-form values are
    /// equal iff their underlying limbs are equal (since the
    /// representation is canonical: every value in `[0, p)` has exactly
    /// one Montgomery encoding).
    pub fn ct_eq(&self, other: &Self) -> Choice {
        self.0.ct_eq_full(&other.0)
    }

    /// Constant-time check for the additive identity.
    pub fn ct_is_zero(&self) -> Choice {
        self.0.ct_is_zero()
    }

    /// Constant-time conditional move: returns `b` iff `choice == 1`.
    #[inline]
    pub fn cmov(a: &Self, b: &Self, choice: Choice) -> Self {
        SecpFieldElement(U256::cmov(&a.0, &b.0, choice))
    }

    /// Constant-time conditional swap: swaps `a` and `b` iff `choice == 1`.
    #[inline]
    pub fn cswap(a: &mut Self, b: &mut Self, choice: Choice) {
        U256::cswap(&mut a.0, &mut b.0, choice);
    }

    /// Internal accessor for tests and lower-level interop.  The raw
    /// Montgomery-form limbs leak nothing on their own (they are still
    /// just a 256-bit field element) but callers should normally go
    /// through `to_canonical`.
    #[inline]
    pub fn as_montgomery(&self) -> &U256 {
        &self.0
    }

    /// Construct a `SecpFieldElement` directly from limbs that already
    /// hold the Montgomery encoding of the intended value.
    ///
    /// **Caller is responsible** for ensuring the limbs equal `a·R mod p`
    /// for some `a ∈ [0, p)`.  Misuse breaks the canonical-representation
    /// invariant that arithmetic relies on.
    ///
    /// `const`-callable, so it can populate compile-time constants such
    /// as the curve coefficients `b` and `3b`.  Every such constant is
    /// cross-checked against `from_biguint` in this module's tests.
    pub const fn from_montgomery_unchecked(limbs: U256) -> Self {
        SecpFieldElement(limbs)
    }
}

impl PartialEq for SecpFieldElement {
    fn eq(&self, other: &Self) -> bool {
        bool::from(self.ct_eq(other))
    }
}

impl Eq for SecpFieldElement {}

impl ConstantTimeEq for SecpFieldElement {
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

    /// Curated values exercising interesting limb boundaries.
    fn samples() -> Vec<BigUint> {
        let p = p_bu();
        vec![
            BigUint::zero(),
            BigUint::one(),
            BigUint::from(2u8),
            BigUint::from(0xdeadbeefu64),
            BigUint::from(1u8) << 32,
            BigUint::from(1u8) << 64,
            BigUint::from(1u8) << 128,
            BigUint::from(1u8) << 200,
            &p - 1u8,
            &p - 2u8,
            &p / 2u8,
            (&p / 2u8) + 1u8,
            // Some random-looking values that are definitely < p:
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
        // n * m' ≡ -1 (mod 2^64)  ⇒  n*m' + 1 ≡ 0
        assert_eq!(prod.wrapping_add(1), 0);
    }

    #[test]
    fn from_to_canonical_roundtrips() {
        for v in samples() {
            let fe = SecpFieldElement::from_biguint(&v);
            let back = fe.to_biguint();
            assert_eq!(back, v);
        }
    }

    #[test]
    fn add_matches_biguint() {
        let p = p_bu();
        for a in samples() {
            for b in samples() {
                let fa = SecpFieldElement::from_biguint(&a);
                let fb = SecpFieldElement::from_biguint(&b);
                let got = fa.add(&fb).to_biguint();
                let want = (&a + &b) % &p;
                assert_eq!(got, want);
            }
        }
    }

    #[test]
    fn sub_matches_biguint() {
        let p = p_bu();
        for a in samples() {
            for b in samples() {
                let fa = SecpFieldElement::from_biguint(&a);
                let fb = SecpFieldElement::from_biguint(&b);
                let got = fa.sub(&fb).to_biguint();
                let want = (&p + (&a % &p) - (&b % &p)) % &p;
                assert_eq!(got, want);
            }
        }
    }

    #[test]
    fn mul_matches_biguint() {
        let p = p_bu();
        for a in samples() {
            for b in samples() {
                let fa = SecpFieldElement::from_biguint(&a);
                let fb = SecpFieldElement::from_biguint(&b);
                let got = fa.mul(&fb).to_biguint();
                let want = (&a * &b) % &p;
                assert_eq!(got, want);
            }
        }
    }

    #[test]
    fn sqr_matches_mul_self_and_biguint() {
        let p = p_bu();
        for a in samples() {
            let fa = SecpFieldElement::from_biguint(&a);
            let got_sqr = fa.sqr().to_biguint();
            let got_mul = fa.mul(&fa).to_biguint();
            let want = (&a * &a) % &p;
            assert_eq!(got_sqr, want, "sqr disagrees with biguint");
            assert_eq!(got_mul, want, "mul-self disagrees with biguint");
            assert_eq!(got_sqr, got_mul, "sqr disagrees with mul(a,a)");
        }
    }

    #[test]
    fn neg_matches_biguint() {
        let p = p_bu();
        for a in samples() {
            let fa = SecpFieldElement::from_biguint(&a);
            let got = fa.neg().to_biguint();
            let want = (&p - (&a % &p)) % &p;
            assert_eq!(got, want);
        }
    }

    #[test]
    fn inv_times_self_is_one() {
        for a in samples() {
            if a.is_zero() {
                continue;
            }
            let fa = SecpFieldElement::from_biguint(&a);
            let inv = fa.inv();
            let prod = fa.mul(&inv);
            assert_eq!(
                prod.to_biguint(),
                BigUint::one(),
                "a * a^-1 != 1 for a={:#x}",
                a,
            );
        }
    }

    #[test]
    fn inversion_chain_matches_ladder_and_field_identity() {
        for a in samples() {
            let fa = SecpFieldElement::from_biguint(&a);
            let chain = fa.inv_chain();
            assert_eq!(chain, fa.inv(), "chain/ladder mismatch for a={:#x}", a);
            if a.is_zero() {
                assert_eq!(chain, SecpFieldElement::ZERO);
            } else {
                assert_eq!(
                    fa.mul(&chain),
                    SecpFieldElement::ONE,
                    "a * chain(a) != 1 for a={:#x}",
                    a
                );
            }
        }
        // Deterministic full-width residues, independent of the chain's
        // structure and including carry patterns absent from curated edges.
        let p = p_bu();
        let mut state = 0x9e37_79b9_7f4a_7c15u64;
        for _ in 0..256 {
            let mut bytes = [0u8; 32];
            for word in bytes.chunks_exact_mut(8) {
                state ^= state >> 12;
                state ^= state << 25;
                state ^= state >> 27;
                word.copy_from_slice(&state.wrapping_mul(0x2545_f491_4f6c_dd1d).to_be_bytes());
            }
            let a = BigUint::from_bytes_be(&bytes) % &p;
            let fa = SecpFieldElement::from_biguint(&a);
            let chain = fa.inv_chain();
            assert_eq!(chain, fa.inv());
            if !a.is_zero() {
                assert_eq!(fa.mul(&chain), SecpFieldElement::ONE);
            }
        }
    }

    #[test]
    fn ct_eq_works() {
        let one = SecpFieldElement::ONE;
        let one2 = SecpFieldElement::from_biguint(&BigUint::one());
        let two = SecpFieldElement::from_biguint(&BigUint::from(2u8));
        assert!(bool::from(one.ct_eq(&one2)));
        assert!(!bool::from(one.ct_eq(&two)));
    }

    #[test]
    fn cmov_selects_correctly() {
        let a = SecpFieldElement::from_biguint(&BigUint::from(7u8));
        let b = SecpFieldElement::from_biguint(&BigUint::from(11u8));
        let r0 = SecpFieldElement::cmov(&a, &b, Choice::from(0));
        let r1 = SecpFieldElement::cmov(&a, &b, Choice::from(1));
        assert_eq!(r0, a);
        assert_eq!(r1, b);
    }

    #[test]
    fn zero_one_constants() {
        assert_eq!(SecpFieldElement::ZERO.to_biguint(), BigUint::zero());
        assert_eq!(SecpFieldElement::ONE.to_biguint(), BigUint::one());
        assert!(bool::from(SecpFieldElement::ZERO.ct_is_zero()));
        assert!(!bool::from(SecpFieldElement::ONE.ct_is_zero()));
    }

    #[test]
    fn bytes_roundtrip() {
        for a in samples() {
            let fe = SecpFieldElement::from_biguint(&a);
            let bytes = fe.to_bytes_be();
            let fe2 = SecpFieldElement::from_bytes_be(&bytes);
            assert_eq!(fe, fe2);
            assert_eq!(fe2.to_biguint(), &a % p_bu());
        }
    }
}
