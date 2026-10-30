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

/// Deterministic exact primality (AKS, §4 of *PRIMES is in P*).
///
/// A fixed finite range uses trial division. Above it, perfect-power rejection,
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
    SquareRootContext::new(p)?.root(a, rng, meter)
}

/// Reusable Tonelli–Shanks setup for one fixed odd prime modulus.
///
/// The caller must certify primality, just as for [`square_root`]. Parameters
/// are prepared lazily; a nonresidue is sampled from the caller's randomness
/// only when a nonzero square first needs it, then reused. This stores O(log p)
/// bits rather than a table of roots. The returned root's sign is unspecified.
pub struct SquareRootContext<'p> {
    modulus: &'p BigUint,
    parameters: Option<SquareRootParameters>,
}

struct SquareRootParameters {
    minus_one: BigUint,
    legendre_exponent: BigUint,
    odd_part: BigUint,
    root_exponent: BigUint,
    twos: usize,
    nonresidue_power: Option<BigUint>,
}

impl<'p> SquareRootContext<'p> {
    /// Bind a context to an odd prime greater than two, without consuming
    /// randomness or allocating its arithmetic parameters yet.
    pub fn new(modulus: &'p BigUint) -> Result<Self> {
        if modulus <= &BigUint::from(2u8) || !modulus.bit(0) {
            return Err(invalid("square-root parameters"));
        }
        Ok(Self {
            modulus,
            parameters: None,
        })
    }

    /// Extract a root of a canonical residue. A nonsquare returns `None`;
    /// random-source failures and resource exhaustion remain errors. Cached
    /// parameters never bypass the bounds of a subsequent caller's meter.
    pub fn root(
        &mut self,
        a: &BigUint,
        rng: &mut impl RandomSource,
        meter: &mut Meter,
    ) -> Result<Option<BigUint>> {
        let p = self.modulus;
        if a >= p {
            return Err(invalid("square-root parameters"));
        }
        if a.is_zero() {
            return Ok(Some(BigUint::zero()));
        }
        let width = usize::try_from(p.bits()).map_err(|_| overflow("square-root width"))?;
        meter.bits(width, "square-root parameters")?;
        if self.parameters.is_none() {
            let minus_one = p - BigUint::one();
            let legendre_exponent = &minus_one >> 1;
            let mut odd_part = minus_one.clone();
            let mut twos = 0;
            while !odd_part.bit(0) {
                odd_part >>= 1;
                twos += 1;
            }
            let root_exponent = (&odd_part + BigUint::one()) >> 1;
            self.parameters = Some(SquareRootParameters {
                minus_one,
                legendre_exponent,
                odd_part,
                root_exponent,
                twos,
                nonresidue_power: None,
            });
        }
        let parameters = self.parameters.as_mut().unwrap();
        let one = BigUint::one();
        if parameters.twos == 1 {
            // For p=3 mod4, square the candidate instead of first computing a
            // separate Legendre symbol. This also rejects every nonsquare.
            let root = modpow(a, &parameters.root_exponent, p, meter)?;
            return Ok((&root * &root % p == *a).then_some(root));
        }
        if modpow(a, &parameters.legendre_exponent, p, meter)? != one {
            return Ok(None);
        }
        let mut c = if let Some(initial) = &parameters.nonresidue_power {
            initial.clone()
        } else {
            let z = loop {
                let z = random_below(p, rng, meter)?;
                if !z.is_zero()
                    && modpow(&z, &parameters.legendre_exponent, p, meter)? == parameters.minus_one
                {
                    break z;
                }
            };
            let initial = modpow(&z, &parameters.odd_part, p, meter)?;
            parameters.nonresidue_power = Some(initial.clone());
            initial
        };
        let mut x = modpow(a, &parameters.root_exponent, p, meter)?;
        let mut t = modpow(a, &parameters.odd_part, p, meter)?;
        let mut m = parameters.twos;
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
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::Limits;

    #[test]
    fn three_mod_four_roots_fit_a_single_exponentiation_budget() {
        struct NoRandom;
        impl RandomSource for NoRandom {
            fn fill(&mut self, _: &mut [u8]) -> Result<()> {
                Err(invalid("shortcut must not consume randomness"))
            }
        }
        let p = BigUint::from(7u8);
        let mut roots = SquareRootContext::new(&p).unwrap();
        // One two-bit modular exponentiation is charged five abstract steps.
        // Squaring the returned candidate independently certifies membership.
        for (a, expected) in [(2u8, Some(4u8)), (3, None)] {
            let mut meter = Meter::new(Limits {
                steps: 5,
                ..Limits::default()
            });
            let got = roots.root(&a.into(), &mut NoRandom, &mut meter).unwrap();
            assert_eq!(got, expected.map(BigUint::from));
            if let Some(root) = got {
                assert_eq!(&root * &root % &p, a.into());
            }
        }
    }

    #[test]
    fn reused_square_roots_match_independent_residue_tables_in_both_orders() {
        for p in [3u64, 5, 7, 17, 19, 43, 97, 257] {
            let modulus = BigUint::from(p);
            let mut roots = SquareRootContext::new(&modulus).unwrap();
            let mut rng = Seeded(11);
            let mut meter = Meter::new(Limits::default());
            let inputs: Vec<_> = (0..p).chain((0..p).rev()).collect();
            for a in inputs {
                let root = roots.root(&a.into(), &mut rng, &mut meter).unwrap();
                let exists = (0..p).any(|x| x * x % p == a);
                assert_eq!(root.is_some(), exists, "p={p}, a={a}");
                if let Some(root) = root {
                    assert!(root < modulus);
                    assert_eq!(&root * &root % &modulus, a.into());
                }
            }
        }
    }

    #[test]
    fn root_setup_is_lazy_reused_and_charged_only_when_performed() {
        struct Nonresidue(usize);
        impl RandomSource for Nonresidue {
            fn fill(&mut self, bytes: &mut [u8]) -> Result<()> {
                self.0 += 1;
                bytes.fill(3);
                Ok(())
            }
        }
        let p = BigUint::from(17u8);
        let mut roots = SquareRootContext::new(&p).unwrap();
        let mut cached_rng = Nonresidue(0);
        let mut fresh_rng = Nonresidue(0);
        let mut cached_meter = Meter::new(Limits::default());
        let mut fresh_meter = Meter::new(Limits::default());
        for a in [0u8, 3, 4, 9, 16, 8, 2, 1] {
            let cached = roots
                .root(&a.into(), &mut cached_rng, &mut cached_meter)
                .unwrap();
            let fresh = square_root(&a.into(), &p, &mut fresh_rng, &mut fresh_meter).unwrap();
            assert_eq!(cached.is_some(), fresh.is_some());
            if a == 0 || a == 3 {
                assert_eq!(
                    cached_rng.0, 0,
                    "zero/nonsquare must not sample a nonresidue"
                );
            }
            if let Some(root) = cached {
                assert_eq!(&root * &root % &p, a.into());
            }
        }
        assert_eq!(cached_rng.0, 1);
        assert_eq!(fresh_rng.0, 6);
        assert!(cached_meter.used < fresh_meter.used);
    }

    #[test]
    fn reused_roots_preserve_failures_and_enforce_each_new_meter() {
        struct Broken;
        impl RandomSource for Broken {
            fn fill(&mut self, _: &mut [u8]) -> Result<()> {
                Err(Error::Limit("test randomness unavailable".into()))
            }
        }
        for p in [0u8, 1, 2, 4] {
            assert!(SquareRootContext::new(&p.into()).is_err());
        }
        let p = BigUint::from(17u8);
        let mut roots = SquareRootContext::new(&p).unwrap();
        let mut meter = Meter::new(Limits::default());
        assert!(matches!(
            roots.root(&4u8.into(), &mut Broken, &mut meter),
            Err(Error::Limit(_))
        ));
        let mut rng = Seeded(19);
        let root = roots
            .root(&4u8.into(), &mut rng, &mut meter)
            .unwrap()
            .unwrap();
        assert_eq!(&root * &root % &p, 4u8.into());
        assert!(matches!(
            roots.root(&p, &mut rng, &mut meter),
            Err(Error::Invalid(_))
        ));
        let mut narrow = Meter::new(Limits {
            bits: 2,
            ..Limits::default()
        });
        assert!(matches!(
            roots.root(&4u8.into(), &mut rng, &mut narrow),
            Err(Error::Limit(_))
        ));
        let mut exhausted = Meter::new(Limits {
            steps: 0,
            ..Limits::default()
        });
        assert!(matches!(
            roots.root(&4u8.into(), &mut rng, &mut exhausted),
            Err(Error::Limit(_))
        ));
        assert_eq!(
            roots
                .root(&BigUint::zero(), &mut Broken, &mut exhausted)
                .unwrap(),
            Some(BigUint::zero())
        );
    }

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
