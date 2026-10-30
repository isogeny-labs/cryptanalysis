//! Exact integer helpers, certified primality, and public-input randomness.

use crate::{integrity, invalid, overflow, BigInt, BigUint, Error, Meter, Result};
use num_integer::Integer;
use num_traits::{One, ToPrimitive, Zero};

/// Reduce a signed integer to its canonical residue.
pub fn residue(a: &BigInt, modulus: &BigUint) -> BigUint {
    a.mod_floor(&BigInt::from(modulus.clone()))
        .to_biguint()
        .unwrap()
}

/// Invert a unit modulo an arbitrary positive modulus, without a primality assumption.
pub fn inverse(a: &BigUint, modulus: &BigUint) -> Result<BigUint> {
    if modulus <= &BigUint::one() {
        return Err(invalid("inverse modulus"));
    }
    let eg = BigInt::from(a.clone()).extended_gcd(&BigInt::from(modulus.clone()));
    if eg.gcd != BigInt::one() {
        return Err(invalid("nonunit denominator"));
    }
    Ok(residue(&eg.x, modulus))
}

/// Charged modular exponentiation. Counts are abstract arithmetic diagnostics.
pub fn modpow(
    a: &BigUint,
    exponent: &BigUint,
    modulus: &BigUint,
    meter: &mut Meter,
) -> Result<BigUint> {
    if modulus.is_zero() {
        return Err(invalid("zero modulus"));
    }
    meter.bits(modulus.bits() as usize, "modular exponentiation width")?;
    meter.charge(
        exponent.bits().saturating_mul(2).saturating_add(1),
        "modular exponentiation",
    )?;
    Ok(a.modpow(exponent, modulus))
}

/// Integer floor of the k-th root. No floating-point rounding is used.
pub fn floor_root(n: &BigUint, k: usize, meter: &mut Meter) -> Result<BigUint> {
    if k == 0 {
        return Err(invalid("zeroth root"));
    }
    if k == 1 || n <= &BigUint::one() {
        return Ok(n.clone());
    }
    let exponent = u32::try_from(k).map_err(|_| overflow("integer root exponent"))?;
    let width = usize::try_from(n.bits()).map_err(|_| overflow("integer root width"))?;
    meter.bits(width, "integer root")?;
    let mut lo = BigUint::zero();
    let mut hi = BigUint::one() << width.div_ceil(k);
    while &lo + BigUint::one() < hi {
        meter.charge(1, "integer root")?;
        let mid: BigUint = (&lo + &hi) >> 1usize;
        if mid.pow(exponent) <= *n {
            lo = mid;
        } else {
            hi = mid;
        }
    }
    if hi.pow(exponent) <= *n {
        Ok(hi)
    } else {
        Ok(lo)
    }
}

fn small_prime(n: u64) -> bool {
    n >= 2 && (2..).take_while(|d| d * d <= n).all(|d| n % d != 0)
}

fn cyclic_mul(
    a: &[BigUint],
    b: &[BigUint],
    n: &BigUint,
    meter: &mut Meter,
) -> Result<Vec<BigUint>> {
    let r = a.len();
    let mut out = vec![BigUint::zero(); r];
    for i in 0..r {
        if a[i].is_zero() {
            continue;
        }
        for j in 0..r {
            if b[j].is_zero() {
                continue;
            }
            meter.charge(1, "AKS cyclic polynomial product")?;
            let k = (i + j) % r;
            out[k] = (&out[k] + &a[i] * &b[j]) % n;
        }
    }
    Ok(out)
}

fn aks_identity(n: &BigUint, r: usize, a: usize, meter: &mut Meter) -> Result<bool> {
    meter.vector(r, "AKS polynomial degree")?;
    let mut base = vec![BigUint::zero(); r];
    base[0] = BigUint::from(a) % n;
    base[1 % r] += BigUint::one();
    let mut answer = vec![BigUint::zero(); r];
    answer[0] = BigUint::one();
    let mut exponent = n.clone();
    while !exponent.is_zero() {
        if exponent.bit(0) {
            answer = cyclic_mul(&answer, &base, n, meter)?;
        }
        exponent >>= 1;
        if !exponent.is_zero() {
            base = cyclic_mul(&base, &base, n, meter)?;
        }
    }
    let mut expected = vec![BigUint::zero(); r];
    expected[0] = BigUint::from(a) % n;
    let exponent_residue = (n % BigUint::from(r))
        .to_usize()
        .ok_or_else(|| overflow("AKS residue"))?;
    expected[exponent_residue] = (&expected[exponent_residue] + BigUint::one()) % n;
    Ok(answer == expected)
}

/// Deterministic exact primality (bounded u64 tests, then AKS).
///
/// A fixed finite range uses trial division and exact bounded-base tests. Above
/// u64, perfect-power rejection,
/// the multiplicative-order parameter, gcd tests and cyclic polynomial identities
/// give a polynomial-bit-complexity algorithm. Resource exhaustion is an error;
/// no probable prime is ever silently accepted as a certified prime.
pub fn is_prime(n: &BigUint, meter: &mut Meter) -> Result<bool> {
    if n < &BigUint::from(2u8) {
        return Ok(false);
    }
    let bits = usize::try_from(n.bits()).map_err(|_| overflow("primality width"))?;
    meter.bits(bits, "primality width")?;
    if bits <= 16 {
        meter.charge(256, "small exact primality")?;
        return Ok(small_prime(n.to_u64().unwrap()));
    }
    if let Some(value) = n.to_u64() {
        return crate::primality::is_prime_u64(value, meter);
    }
    aks(n, bits, meter)
}

fn aks(n: &BigUint, bits: usize, meter: &mut Meter) -> Result<bool> {
    if !n.bit(0) {
        return Ok(false);
    }
    for k in 2..=bits {
        meter.charge(1, "AKS perfect-power tests")?;
        let root = floor_root(n, k, meter)?;
        if root.pow(u32::try_from(k).map_err(|_| overflow("AKS exponent"))?) == *n {
            return Ok(false);
        }
    }
    let order_bound = bits
        .checked_mul(bits)
        .ok_or_else(|| overflow("AKS order bound"))?;
    let mut r = 2usize;
    loop {
        meter.vector(r, "AKS order parameter")?;
        meter.charge(1, "AKS order search")?;
        let rb = BigUint::from(r);
        let gcd = n.gcd(&rb);
        if gcd > BigUint::one() && gcd < *n {
            return Ok(false);
        }
        if gcd.is_one() {
            let nr = (n % &rb)
                .to_u64()
                .ok_or_else(|| overflow("AKS machine modulus"))?;
            let mut value = 1u128;
            let mut long = true;
            for _ in 0..order_bound {
                meter.charge(1, "AKS multiplicative order")?;
                value = value * u128::from(nr) % (r as u128);
                if value == 1 {
                    long = false;
                    break;
                }
            }
            if long {
                break;
            }
        }
        r = r
            .checked_add(1)
            .ok_or_else(|| overflow("AKS order parameter"))?;
    }
    for a in 2..=r {
        meter.charge(1, "AKS gcd tests")?;
        let gcd = n.gcd(&BigUint::from(a));
        if gcd > BigUint::one() && gcd < *n {
            return Ok(false);
        }
    }
    if n <= &BigUint::from(r) {
        return Ok(true);
    }
    let mut phi = 0usize;
    for a in 1..=r {
        if a.gcd(&r) == 1 {
            phi += 1;
        }
    }
    // A conservative integer ceiling of sqrt(phi(r))*log2(n) is sufficient.
    let sqrt_phi = floor_root(&BigUint::from(phi), 2, meter)?
        .to_usize()
        .unwrap();
    let sqrt_phi = if sqrt_phi * sqrt_phi == phi {
        sqrt_phi
    } else {
        sqrt_phi + 1
    };
    let checks = bits
        .checked_mul(sqrt_phi)
        .ok_or_else(|| overflow("AKS identity bound"))?;
    for a in 1..=checks {
        if !aks_identity(n, r, a, meter)? {
            return Ok(false);
        }
    }
    Ok(true)
}

/// Source of independent random bytes, or an explicitly reproducible test source.
pub trait RandomSource {
    /// Fill the whole buffer or return an error.
    fn fill(&mut self, bytes: &mut [u8]) -> Result<()>;
}

/// Operating-system randomness for the randomized reduction.
#[derive(Default)]
pub struct OsRandom;
impl RandomSource for OsRandom {
    fn fill(&mut self, bytes: &mut [u8]) -> Result<()> {
        getrandom::getrandom(bytes).map_err(|e| Error::Invalid(format!("OS randomness: {e}")))
    }
}

/// SplitMix64 for repeatable public correctness fixtures, not secret material.
pub struct Seeded(pub u64);
impl RandomSource for Seeded {
    fn fill(&mut self, bytes: &mut [u8]) -> Result<()> {
        for chunk in bytes.chunks_mut(8) {
            self.0 = self.0.wrapping_add(0x9e3779b97f4a7c15);
            let mut x = self.0;
            x = (x ^ (x >> 30)).wrapping_mul(0xbf58476d1ce4e5b9);
            x = (x ^ (x >> 27)).wrapping_mul(0x94d049bb133111eb);
            x ^= x >> 31;
            chunk.copy_from_slice(&x.to_le_bytes()[..chunk.len()]);
        }
        Ok(())
    }
}

/// Uniform rejection sampling from `[0,n)` given uniform random bytes.
pub fn random_below(
    n: &BigUint,
    rng: &mut impl RandomSource,
    meter: &mut Meter,
) -> Result<BigUint> {
    if n.is_zero() {
        return Err(invalid("empty random range"));
    }
    let bits = usize::try_from(n.bits()).map_err(|_| overflow("random width"))?;
    meter.bits(bits, "random integer")?;
    let mut bytes = vec![0u8; bits.div_ceil(8)];
    loop {
        meter.charge(1, "rejection sampling")?;
        rng.fill(&mut bytes)?;
        if bits % 8 != 0 {
            *bytes.last_mut().unwrap() &= (1u8 << (bits % 8)) - 1;
        }
        let value = BigUint::from_bytes_le(&bytes);
        if &value < n {
            return Ok(value);
        }
    }
}

/// Choose and certify a prime in `[2p,4p]` by uniform sampling and exact AKS.
pub fn hash_prime(p: &BigUint, rng: &mut impl RandomSource, meter: &mut Meter) -> Result<BigUint> {
    let lo = p << 1;
    let range = (p << 1) + BigUint::one();
    loop {
        let candidate = &lo + random_below(&range, rng, meter)?;
        if is_prime(&candidate, meter)? {
            return Ok(candidate);
        }
    }
}

/// Tonelli–Shanks with a randomized nonresidue, hence expected polynomial time.
pub fn square_root(
    a: &BigUint,
    p: &BigUint,
    rng: &mut impl RandomSource,
    meter: &mut Meter,
) -> Result<Option<BigUint>> {
    if a >= p || p <= &BigUint::from(2u8) || !p.bit(0) {
        return Err(invalid("square-root parameters"));
    }
    if a.is_zero() {
        return Ok(Some(BigUint::zero()));
    }
    let one = BigUint::one();
    let pm1 = p - &one;
    if modpow(a, &(&pm1 >> 1), p, meter)? != one {
        return Ok(None);
    }
    if p % 4u8 == BigUint::from(3u8) {
        return Ok(Some(modpow(a, &((p + &one) >> 2), p, meter)?));
    }
    let mut q = pm1.clone();
    let mut s = 0usize;
    while !q.bit(0) {
        q >>= 1;
        s += 1;
    }
    let z = loop {
        let z = random_below(p, rng, meter)?;
        if !z.is_zero() && modpow(&z, &(&pm1 >> 1), p, meter)? == pm1 {
            break z;
        }
    };
    let mut c = modpow(&z, &q, p, meter)?;
    let mut x = modpow(a, &((&q + &one) >> 1), p, meter)?;
    let mut t = modpow(a, &q, p, meter)?;
    let mut m = s;
    while t != one {
        meter.charge(1, "Tonelli-Shanks")?;
        let mut power = t.clone();
        let mut i = 0;
        while power != one && i < m {
            power = &power * &power % p;
            i += 1;
        }
        if i == m {
            return Err(integrity("Tonelli-Shanks requires an odd prime modulus"));
        }
        let b = modpow(&c, &(BigUint::one() << (m - i - 1)), p, meter)?;
        x = x * &b % p;
        c = &b * &b % p;
        t = t * &c % p;
        m = i;
    }
    if &x * &x % p != *a {
        return Err(integrity("square-root replay"));
    }
    Ok(Some(x))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::Limits;
    #[test]
    fn exact_small_primality_and_square_roots() {
        let mut meter = Meter::new(Limits::default());
        let mut rng = Seeded(7);
        for p in [5u64, 7, 17, 19, 43, 97] {
            assert!(is_prime(&p.into(), &mut meter).unwrap());
            for a in 0..p {
                let got = square_root(&a.into(), &p.into(), &mut rng, &mut meter).unwrap();
                let exists = (0..p).any(|x| x * x % p == a);
                assert_eq!(got.is_some(), exists);
                if let Some(x) = got {
                    assert_eq!(&x * &x % p, BigUint::from(a));
                }
            }
        }
        for n in [0u64, 1, 4, 9, 15, 341, 561, 65535, 65536, 65537 * 3] {
            assert!(!is_prime(&n.into(), &mut meter).unwrap());
        }
    }
    #[test]
    fn aks_cyclic_identity_and_large_prime_path() {
        let mut meter = Meter::new(Limits {
            steps: 50_000_000,
            ..Limits::default()
        });
        assert!(aks_identity(&BigUint::from(17u8), 7, 3, &mut meter).unwrap());
        assert!(!aks_identity(&BigUint::from(15u8), 7, 3, &mut meter).unwrap());
        // Force the polynomial branch below its normal fixed-range cutoff.
        assert!(aks(&BigUint::from(257u32), 9, &mut meter).unwrap());
        assert!(!is_prime(&BigUint::from(257u32).pow(3), &mut meter).unwrap());
    }
    #[test]
    fn limits_do_not_turn_unknown_primes_into_true_or_false() {
        let mut meter = Meter::new(Limits {
            steps: 0,
            ..Limits::default()
        });
        assert!(matches!(
            is_prime(&BigUint::from(65537u32), &mut meter),
            Err(Error::Limit(_))
        ));
    }
}
