//! Small fixed-purpose arbitrary-precision signed integer.
//!
//! The crate is dependency-free by design, so this type supplies only what the
//! Frobenius polynomial filter needs: parsing decimal and `2^k` text, addition,
//! subtraction, multiplication, comparison, and decimal printing. It is
//! variable-time schoolbook arithmetic for exact bookkeeping, not for secrets.

use std::{cmp::Ordering, fmt};

/// Largest exponent accepted in a `2^k` input (bounds memory for hostile input).
pub const MAX_POWER_OF_TWO: u32 = 1 << 14;
/// Longest decimal input accepted, in digits.
pub const MAX_DECIMAL_DIGITS: usize = 5_000;

/// Sign and magnitude; the magnitude is little-endian base 2^32 with no
/// trailing zero limb, and zero is the empty magnitude with `negative == false`.
#[derive(Clone, Debug, PartialEq, Eq, Hash, Default)]
pub struct BigInt {
    negative: bool,
    mag: Vec<u32>,
}

fn trim(mag: &mut Vec<u32>) {
    while mag.last() == Some(&0) {
        mag.pop();
    }
}

fn cmp_mag(a: &[u32], b: &[u32]) -> Ordering {
    a.len()
        .cmp(&b.len())
        .then_with(|| a.iter().rev().cmp(b.iter().rev()))
}

fn add_mag(a: &[u32], b: &[u32]) -> Vec<u32> {
    let (long, short) = if a.len() >= b.len() { (a, b) } else { (b, a) };
    let mut out = Vec::with_capacity(long.len() + 1);
    let mut carry = 0_u64;
    for (i, &limb) in long.iter().enumerate() {
        let sum = u64::from(limb) + u64::from(short.get(i).copied().unwrap_or(0)) + carry;
        out.push(sum as u32);
        carry = sum >> 32;
    }
    if carry > 0 {
        out.push(carry as u32);
    }
    out
}

/// a - b for |a| >= |b|.
fn sub_mag(a: &[u32], b: &[u32]) -> Vec<u32> {
    let mut out = Vec::with_capacity(a.len());
    let mut borrow = 0_i64;
    for (i, &limb) in a.iter().enumerate() {
        let mut diff = i64::from(limb) - i64::from(b.get(i).copied().unwrap_or(0)) - borrow;
        borrow = 0;
        if diff < 0 {
            diff += 1 << 32;
            borrow = 1;
        }
        out.push(diff as u32);
    }
    trim(&mut out);
    out
}

fn mul_mag(a: &[u32], b: &[u32]) -> Vec<u32> {
    if a.is_empty() || b.is_empty() {
        return Vec::new();
    }
    let mut out = vec![0_u32; a.len() + b.len()];
    for (i, &x) in a.iter().enumerate() {
        let mut carry = 0_u64;
        for (j, &y) in b.iter().enumerate() {
            let cur = u64::from(out[i + j]) + u64::from(x) * u64::from(y) + carry;
            out[i + j] = cur as u32;
            carry = cur >> 32;
        }
        out[i + b.len()] = carry as u32;
    }
    trim(&mut out);
    out
}

/// Multiply by `m` and add `add` in place.
fn mul_small_add(mag: &mut Vec<u32>, m: u32, add: u32) {
    let mut carry = u64::from(add);
    for limb in mag.iter_mut() {
        let cur = u64::from(*limb) * u64::from(m) + carry;
        *limb = cur as u32;
        carry = cur >> 32;
    }
    if carry > 0 {
        mag.push(carry as u32);
    }
}

/// Divide in place by `d`, returning the remainder.
fn div_small(mag: &mut Vec<u32>, d: u32) -> u32 {
    let mut rem = 0_u64;
    for limb in mag.iter_mut().rev() {
        let cur = (rem << 32) | u64::from(*limb);
        *limb = (cur / u64::from(d)) as u32;
        rem = cur % u64::from(d);
    }
    trim(mag);
    rem as u32
}

impl BigInt {
    pub fn zero() -> Self {
        Self::default()
    }

    fn from_parts(negative: bool, mut mag: Vec<u32>) -> Self {
        trim(&mut mag);
        Self {
            negative: negative && !mag.is_empty(),
            mag,
        }
    }

    /// 2^k.
    pub fn pow2(k: u32) -> Self {
        let mut mag = vec![0_u32; (k / 32) as usize + 1];
        mag[(k / 32) as usize] = 1 << (k % 32);
        Self::from_parts(false, mag)
    }

    pub fn is_zero(&self) -> bool {
        self.mag.is_empty()
    }

    pub fn is_negative(&self) -> bool {
        self.negative
    }

    /// Bit length of the magnitude (0 for zero).
    pub fn bit_len(&self) -> u32 {
        match self.mag.last() {
            None => 0,
            Some(top) => (self.mag.len() as u32 - 1) * 32 + (32 - top.leading_zeros()),
        }
    }

    pub fn neg(&self) -> Self {
        Self::from_parts(!self.negative, self.mag.clone())
    }

    pub fn add(&self, other: &Self) -> Self {
        if self.negative == other.negative {
            return Self::from_parts(self.negative, add_mag(&self.mag, &other.mag));
        }
        match cmp_mag(&self.mag, &other.mag) {
            Ordering::Equal => Self::zero(),
            Ordering::Greater => Self::from_parts(self.negative, sub_mag(&self.mag, &other.mag)),
            Ordering::Less => Self::from_parts(other.negative, sub_mag(&other.mag, &self.mag)),
        }
    }

    pub fn sub(&self, other: &Self) -> Self {
        self.add(&other.neg())
    }

    pub fn mul(&self, other: &Self) -> Self {
        Self::from_parts(
            self.negative != other.negative,
            mul_mag(&self.mag, &other.mag),
        )
    }

    /// Parse `[+-]digits`, `[+-]2^k`, or `[+-]0x<hex>`; no other forms.
    pub fn parse(text: &str) -> Result<Self, String> {
        let invalid = || format!("Invalid integer {text:?}.");
        let trimmed = text.trim();
        let (negative, body) = match trimmed.as_bytes().first() {
            Some(b'-') => (true, &trimmed[1..]),
            Some(b'+') => (false, &trimmed[1..]),
            _ => (false, trimmed),
        };
        if let Some(exponent) = body.strip_prefix("2^") {
            let k: u32 = exponent.parse().map_err(|_| invalid())?;
            if k > MAX_POWER_OF_TWO {
                return Err(format!("Exponent in {text:?} exceeds {MAX_POWER_OF_TWO}."));
            }
            let value = Self::pow2(k);
            return Ok(if negative { value.neg() } else { value });
        }
        let (radix, digits) = match body.strip_prefix("0x") {
            Some(hex) => (16, hex),
            None => (10, body),
        };
        if digits.is_empty() || digits.len() > MAX_DECIMAL_DIGITS {
            return Err(invalid());
        }
        let mut mag = Vec::new();
        for c in digits.chars() {
            let digit = c.to_digit(radix).ok_or_else(invalid)?;
            mul_small_add(&mut mag, radix, digit);
        }
        Ok(Self::from_parts(negative, mag))
    }

    /// Value as i128 if it fits.
    pub fn to_i128(&self) -> Option<i128> {
        if self.mag.len() > 4 {
            return None;
        }
        let mut m = 0_u128;
        for (i, &limb) in self.mag.iter().enumerate() {
            m |= u128::from(limb) << (32 * i);
        }
        if self.negative {
            if m <= 1_u128 << 127 {
                Some((m as i128).wrapping_neg())
            } else {
                None
            }
        } else {
            i128::try_from(m).ok()
        }
    }
}

impl fmt::Display for BigInt {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if self.mag.is_empty() {
            return f.write_str("0");
        }
        let mut mag = self.mag.clone();
        let mut chunks = Vec::new();
        while !mag.is_empty() {
            chunks.push(div_small(&mut mag, 1_000_000_000));
        }
        let mut out = String::new();
        if self.negative {
            out.push('-');
        }
        out.push_str(&chunks.pop().unwrap().to_string());
        for chunk in chunks.iter().rev() {
            out.push_str(&format!("{chunk:09}"));
        }
        f.write_str(&out)
    }
}

impl Ord for BigInt {
    fn cmp(&self, other: &Self) -> Ordering {
        match (self.negative, other.negative) {
            (false, true) => Ordering::Greater,
            (true, false) => Ordering::Less,
            (false, false) => cmp_mag(&self.mag, &other.mag),
            (true, true) => cmp_mag(&other.mag, &self.mag),
        }
    }
}

impl PartialOrd for BigInt {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl From<i128> for BigInt {
    fn from(value: i128) -> Self {
        let m = value.unsigned_abs();
        let mag = (0..4).map(|i| (m >> (32 * i)) as u32).collect();
        Self::from_parts(value < 0, mag)
    }
}
impl From<i64> for BigInt {
    fn from(value: i64) -> Self {
        Self::from(i128::from(value))
    }
}
impl From<i32> for BigInt {
    fn from(value: i32) -> Self {
        Self::from(i128::from(value))
    }
}
impl From<u64> for BigInt {
    fn from(value: u64) -> Self {
        Self::from(i128::from(value))
    }
}

macro_rules! eq_primitive {
    ($($t:ty),*) => {$(
        impl PartialEq<$t> for BigInt {
            fn eq(&self, other: &$t) -> bool {
                self.to_i128() == i128::try_from(*other).ok()
            }
        }
    )*};
}
eq_primitive!(i32, i64, i128, u64);

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn round_trips_and_signs() {
        for text in [
            "0",
            "1",
            "-1",
            "4294967296",
            "-18446744073709551616",
            "9671406556917033397649408",
        ] {
            assert_eq!(BigInt::parse(text).unwrap().to_string(), text);
        }
        assert_eq!(BigInt::parse("-0").unwrap().to_string(), "0");
        assert_eq!(
            BigInt::parse("2^83").unwrap().to_string(),
            "9671406556917033397649408"
        );
        assert_eq!(BigInt::parse("0xff").unwrap(), 255);
        assert!(BigInt::parse("").is_err());
        assert!(BigInt::parse("12a").is_err());
        assert!(BigInt::parse("2^99999999").is_err());
    }

    #[test]
    fn arithmetic_matches_i128_on_small_values() {
        let samples: [i128; 9] = [
            0,
            1,
            -1,
            7,
            -7,
            1 << 70,
            -(1 << 70),
            u64::MAX as i128,
            i64::MIN as i128,
        ];
        for &a in &samples {
            for &b in &samples {
                let (x, y) = (BigInt::from(a), BigInt::from(b));
                assert_eq!(x.add(&y), a + b);
                assert_eq!(x.sub(&y), a - b);
                if let Some(p) = a.checked_mul(b) {
                    assert_eq!(x.mul(&y), p);
                }
                assert_eq!(x.cmp(&y), a.cmp(&b));
            }
        }
        assert_eq!(BigInt::from(i128::MIN).to_i128(), Some(i128::MIN));
    }

    #[test]
    fn exceeds_i128() {
        let big = BigInt::pow2(83)
            .mul(&BigInt::pow2(83))
            .mul(&BigInt::pow2(83));
        assert_eq!(big, BigInt::pow2(249));
        assert_eq!(big.to_i128(), None);
        assert_eq!(big.bit_len(), 250);
    }
}
