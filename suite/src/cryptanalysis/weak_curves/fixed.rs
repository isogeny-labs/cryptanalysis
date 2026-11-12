//! Fixed-width modular arithmetic for the affine/Jacobian curve code in
//! [`super::arith`]: an odd modulus of at most four 64-bit limbs held in
//! `[u64; N]` arrays, multiplied by Montgomery reduction (CIOS).
//!
//! Every function returns the canonical residue in `[0, p)`, the same value
//! the `BigUint` `(a * b) % p` formulas return, with no heap allocation per
//! field operation.  [`ModN::new`] and [`ModN::load`] return `None` for
//! anything outside that contract (even or tiny modulus, an operand that is
//! wider than `N` limbs or not reduced), and the callers then run their
//! original `BigUint` code.  Variable time, like the code it replaces.

use num_bigint::BigUint;
use num_traits::One;

pub(crate) type Limbs<const N: usize> = [u64; N];

/// Odd modulus `p` (`3 <= p < 2^(64N)`, top limb non-zero) and its
/// Montgomery constants.
pub(crate) struct ModN<const N: usize> {
    p: Limbs<N>,
    /// `-p^{-1} mod 2^64`.
    ninv: u64,
    /// `2^{128 N} mod p`.
    r2: Limbs<N>,
}

impl<const N: usize> ModN<N> {
    pub fn new(p: &BigUint) -> Option<Self> {
        let d = p.to_u64_digits();
        if d.len() != N || d[0] & 1 == 0 || (N == 1 && d[0] < 3) {
            return None;
        }
        let mut pl = [0u64; N];
        pl.copy_from_slice(&d);
        let mut inv = 1u64;
        for _ in 0..6 {
            inv = inv.wrapping_mul(2u64.wrapping_sub(pl[0].wrapping_mul(inv)));
        }
        let r2big = (BigUint::one() << (128 * N)) % p;
        let mut r2 = [0u64; N];
        for (slot, v) in r2.iter_mut().zip(r2big.iter_u64_digits()) {
            *slot = v;
        }
        Some(Self {
            p: pl,
            ninv: inv.wrapping_neg(),
            r2,
        })
    }

    /// `x` as limbs, if it is already reduced.
    pub fn load(&self, x: &BigUint) -> Option<Limbs<N>> {
        let mut out = [0u64; N];
        for (i, v) in x.iter_u64_digits().enumerate() {
            if i >= N {
                return None;
            }
            out[i] = v;
        }
        (!geq(&out, &self.p)).then_some(out)
    }

    pub fn store(&self, x: &Limbs<N>) -> BigUint {
        let mut w = [0u32; 8];
        for (i, &v) in x.iter().enumerate() {
            w[2 * i] = v as u32;
            w[2 * i + 1] = (v >> 32) as u32;
        }
        BigUint::from_slice(&w[..2 * N])
    }

    #[inline]
    pub fn is_zero(x: &Limbs<N>) -> bool {
        x.iter().all(|&v| v == 0)
    }

    /// `a · b · 2^{-64N} mod p`.
    #[inline]
    fn mont_mul(&self, a: &Limbs<N>, b: &Limbs<N>) -> Limbs<N> {
        let p = &self.p;
        // N + 2 words: the running sum stays below 2p·2^64.
        let mut t = [0u64; 8];
        for i in 0..N {
            let mut carry = 0u64;
            for j in 0..N {
                let v = t[j] as u128 + a[i] as u128 * b[j] as u128 + carry as u128;
                t[j] = v as u64;
                carry = (v >> 64) as u64;
            }
            let v = t[N] as u128 + carry as u128;
            t[N] = v as u64;
            t[N + 1] = (v >> 64) as u64;
            let m = t[0].wrapping_mul(self.ninv);
            let v = t[0] as u128 + m as u128 * p[0] as u128;
            let mut carry = (v >> 64) as u64;
            for j in 1..N {
                let v = t[j] as u128 + m as u128 * p[j] as u128 + carry as u128;
                t[j - 1] = v as u64;
                carry = (v >> 64) as u64;
            }
            let v = t[N] as u128 + carry as u128;
            t[N - 1] = v as u64;
            t[N] = t[N + 1] + (v >> 64) as u64;
            t[N + 1] = 0;
        }
        let mut out = [0u64; N];
        out.copy_from_slice(&t[..N]);
        if t[N] != 0 || geq(&out, p) {
            sub_in_place(&mut out, p);
        }
        out
    }

    /// `a · b mod p` for reduced `a`, `b`.
    #[inline]
    pub fn mul(&self, a: &Limbs<N>, b: &Limbs<N>) -> Limbs<N> {
        self.mont_mul(&self.mont_mul(a, b), &self.r2)
    }

    #[inline]
    pub fn add(&self, a: &Limbs<N>, b: &Limbs<N>) -> Limbs<N> {
        let mut out = *a;
        let mut carry = 0u64;
        for i in 0..N {
            let (s1, c1) = out[i].overflowing_add(b[i]);
            let (s2, c2) = s1.overflowing_add(carry);
            out[i] = s2;
            carry = (c1 | c2) as u64;
        }
        if carry != 0 || geq(&out, &self.p) {
            sub_in_place(&mut out, &self.p);
        }
        out
    }

    #[inline]
    pub fn sub(&self, a: &Limbs<N>, b: &Limbs<N>) -> Limbs<N> {
        let mut out = *a;
        if geq(a, b) {
            sub_in_place(&mut out, b);
        } else {
            // a - b + p, wrapping: the true result is below p.
            sub_in_place(&mut out, b);
            let mut carry = 0u64;
            for i in 0..N {
                let (s1, c1) = out[i].overflowing_add(self.p[i]);
                let (s2, c2) = s1.overflowing_add(carry);
                out[i] = s2;
                carry = (c1 | c2) as u64;
            }
        }
        out
    }

    #[inline]
    pub fn dbl(&self, a: &Limbs<N>) -> Limbs<N> {
        self.add(a, a)
    }
}

#[inline]
fn geq<const N: usize>(a: &Limbs<N>, b: &Limbs<N>) -> bool {
    for i in (0..N).rev() {
        if a[i] != b[i] {
            return a[i] > b[i];
        }
    }
    true
}

/// `a -= b` modulo `2^{64N}`.
#[inline]
fn sub_in_place<const N: usize>(a: &mut Limbs<N>, b: &Limbs<N>) {
    let mut borrow = 0u64;
    for i in 0..N {
        let (d1, b1) = a[i].overflowing_sub(b[i]);
        let (d2, b2) = d1.overflowing_sub(borrow);
        a[i] = d2;
        borrow = (b1 | b2) as u64;
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use rand::rngs::StdRng;
    use rand::{RngCore, SeedableRng};

    fn check<const N: usize>(p: &BigUint) {
        let m = ModN::<N>::new(p).expect("odd modulus of N limbs");
        let mut rng = StdRng::seed_from_u64(0xf1_0ed_u64 ^ N as u64);
        let mut draw = |rng: &mut StdRng| {
            let mut bytes = vec![0u8; 8 * N + 8];
            rng.fill_bytes(&mut bytes);
            BigUint::from_bytes_le(&bytes) % p
        };
        let edge = [BigUint::from(0u32), BigUint::one(), p - 1u32, p - 2u32];
        for i in 0..400 {
            let a = if i < 16 { edge[i % 4].clone() } else { draw(&mut rng) };
            let b = if i < 16 { edge[i / 4].clone() } else { draw(&mut rng) };
            let (la, lb) = (m.load(&a).unwrap(), m.load(&b).unwrap());
            assert_eq!(m.store(&m.mul(&la, &lb)), (&a * &b) % p, "mul");
            assert_eq!(m.store(&m.add(&la, &lb)), (&a + &b) % p, "add");
            assert_eq!(m.store(&m.sub(&la, &lb)), (p + &a - &b) % p, "sub");
        }
        assert!(m.load(p).is_none());
    }

    #[test]
    fn matches_biguint_at_every_width() {
        check::<1>(&BigUint::from(18_446_744_073_709_551_557u64));
        check::<1>(&BigUint::from(10_007u32));
        check::<2>(&((BigUint::one() << 127u32) - 1u32));
        check::<2>(&((BigUint::one() << 128u32) - 159u32));
        check::<3>(&((BigUint::one() << 160u32) - 47u32));
        check::<4>(&((BigUint::one() << 256u32) - 189u32));
        check::<4>(&((BigUint::one() << 255u32) - 19u32));
    }
}
