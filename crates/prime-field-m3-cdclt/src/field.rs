//! Exact counted prime-field `F_p` and quadratic-extension `F_{p^2}` arithmetic
//! for odd primes `3 < p < 2^64`, plus standalone SHA-256 and deterministic PRNG.

use std::ops::AddAssign;

/// Exact arithmetic operation vector over `F_p`.
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub struct FpOps {
    /// Modular additions, subtractions, and negations in `F_p`.
    pub additions: u64,
    /// Modular multiplications and squarings in `F_p`.
    pub multiplications: u64,
    /// Modular inversions in `F_p^*`.
    pub inversions: u64,
}

impl FpOps {
    /// Total native `F_p` operations (`additions + multiplications + inversions`).
    #[inline]
    pub const fn total(self) -> u64 {
        self.additions + self.multiplications + self.inversions
    }
}

impl AddAssign for FpOps {
    #[inline]
    fn add_assign(&mut self, rhs: Self) {
        self.additions += rhs.additions;
        self.multiplications += rhs.multiplications;
        self.inversions += rhs.inversions;
    }
}

/// Canonical modular addition `x + y mod p` (`x, y < p < 2^64`; the sum is never formed above `p`).
#[inline]
pub fn add_mod(x: u64, y: u64, p: u64, ops: &mut FpOps) -> u64 {
    debug_assert!(x < p && y < p);
    ops.additions += 1;
    let d = p - y;
    if x >= d {
        x - d
    } else {
        x + y
    }
}

/// Canonical modular subtraction `x - y mod p` (`x, y < p < 2^63`).
#[inline]
pub fn sub_mod(x: u64, y: u64, p: u64, ops: &mut FpOps) -> u64 {
    debug_assert!(x < p && y < p);
    ops.additions += 1;
    if x >= y {
        x - y
    } else {
        p - (y - x)
    }
}

/// Canonical modular negation `-x mod p` (`x < p`).
#[inline]
pub fn neg_mod(x: u64, p: u64, ops: &mut FpOps) -> u64 {
    debug_assert!(x < p);
    ops.additions += 1;
    if x == 0 {
        0
    } else {
        p - x
    }
}

/// Reference `u128` modular multiplication `x * y mod p`.
#[inline]
pub fn mul_mod(x: u64, y: u64, p: u64, ops: &mut FpOps) -> u64 {
    debug_assert!(x < p && y < p);
    ops.multiplications += 1;
    ((x as u128 * y as u128) % (p as u128)) as u64
}

/// Modular exponentiation `base^exp mod p`.
pub fn pow_mod(mut base: u64, mut exp: u64, p: u64, ops: &mut FpOps) -> u64 {
    base %= p;
    let mut acc = 1u64 % p;
    while exp != 0 {
        if (exp & 1) != 0 {
            acc = mul_mod(acc, base, p, ops);
        }
        exp >>= 1;
        if exp != 0 {
            base = mul_mod(base, base, p, ops);
        }
    }
    acc
}

/// Fast exact modular inverse `x^{-1} mod p` for odd prime `p` and `0 < x < p`
/// using signed 64-bit extended Euclidean / binary GCD steps.
#[inline]
pub fn inv_mod(x: u64, p: u64, ops: &mut FpOps) -> u64 {
    assert!(x != 0 && x < p, "inv_mod called on zero or noncanonical input");
    ops.inversions += 1;
    let m = p as i128;
    let mut a = x as i128;
    let mut b = m;
    let mut u: i128 = 1;
    let mut v: i128 = 0;
    while a != 0 {
        let tz = a.trailing_zeros();
        for _ in 0..tz {
            a >>= 1;
            if (u & 1) != 0 {
                u += m;
            }
            u >>= 1;
        }
        if a < b {
            std::mem::swap(&mut a, &mut b);
            std::mem::swap(&mut u, &mut v);
        }
        a -= b;
        u -= v;
        if u < 0 {
            u += m;
        }
    }
    debug_assert_eq!(b, 1, "modulus is not coprime to input");
    let res = (v.rem_euclid(m)) as u64;
    debug_assert_eq!(((res as u128 * x as u128) % (p as u128)) as u64, 1);
    res
}

/// Fast 64-bit Montgomery domain for odd primes `3 < p < 2^64`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct MontDomain {
    /// Odd prime modulus `p`.
    pub p: u64,
    /// `-p^{-1} mod 2^64`.
    n_prime: u64,
    /// `2^{128} mod p`.
    r2: u64,
    /// `2^{64} mod p` (Montgomery representation of `1`).
    one_mont: u64,
}

impl MontDomain {
    /// Construct the Montgomery domain for odd modulus `3 < p < 2^64` (every odd `u64` above 3).
    pub fn new(p: u64) -> Self {
        assert!(p > 3 && (p & 1) == 1, "unsupported modulus for MontDomain");
        // Newton iteration for p * inv == 1 (mod 2^64).
        let mut inv = 1u64;
        for _ in 0..6 {
            inv = inv.wrapping_mul(2u64.wrapping_sub(p.wrapping_mul(inv)));
        }
        let n_prime = inv.wrapping_neg();
        let r_mod_p = ((1u128 << 64) % (p as u128)) as u64;
        let r2 = (((r_mod_p as u128) * (r_mod_p as u128)) % (p as u128)) as u64;
        Self {
            p,
            n_prime,
            r2,
            one_mont: r_mod_p,
        }
    }

    #[inline]
    fn redc(self, t: u128) -> u64 {
        // `t + m*p` can exceed 2^128 when p >= 2^63, so add the high halves separately:
        // the low 64 bits of `t + m*p` are zero, contributing a carry iff `t mod 2^64 != 0`.
        let m = (t as u64).wrapping_mul(self.n_prime);
        let mp = (m as u128) * (self.p as u128);
        let carry = ((t as u64) != 0) as u128;
        let u = (t >> 64) + (mp >> 64) + carry; // < 2p + 1, fits u128
        let p = self.p as u128;
        (if u >= p { u - p } else { u }) as u64
    }

    /// Convert canonical residue `x < p` into Montgomery representation.
    #[inline]
    pub fn to_mont(self, x: u64) -> u64 {
        debug_assert!(x < self.p);
        self.redc((x as u128) * (self.r2 as u128))
    }

    /// Convert Montgomery element back to canonical residue in `[0, p)`.
    #[inline]
    pub fn from_mont(self, x_mont: u64) -> u64 {
        self.redc(x_mont as u128)
    }

    /// Montgomery representation of `1`.
    #[inline]
    pub const fn one(self) -> u64 {
        self.one_mont
    }

    /// Counted addition in Montgomery domain.
    #[inline]
    pub fn add(self, a: u64, b: u64, ops: &mut FpOps) -> u64 {
        add_mod(a, b, self.p, ops)
    }

    /// Counted subtraction in Montgomery domain.
    #[inline]
    pub fn sub(self, a: u64, b: u64, ops: &mut FpOps) -> u64 {
        sub_mod(a, b, self.p, ops)
    }

    /// Counted negation in Montgomery domain.
    #[inline]
    pub fn neg(self, a: u64, ops: &mut FpOps) -> u64 {
        neg_mod(a, self.p, ops)
    }

    /// Counted Montgomery multiplication `(a * b * R^{-1}) mod p`.
    #[inline]
    pub fn mul(self, a: u64, b: u64, ops: &mut FpOps) -> u64 {
        ops.multiplications += 1;
        self.redc((a as u128) * (b as u128))
    }

    /// Counted Montgomery squaring.
    #[inline]
    pub fn sqr(self, a: u64, ops: &mut FpOps) -> u64 {
        self.mul(a, a, ops)
    }

    /// Invert a nonzero Montgomery residue, returning `(a^{-1})_mont`.
    #[inline]
    pub fn inv_mont(self, a_mont: u64, ops: &mut FpOps) -> u64 {
        let a_std = self.from_mont(a_mont);
        let inv_std = inv_mod(a_std, self.p, ops);
        self.to_mont(inv_std)
    }
}

/// Deterministic 64-bit Miller-Rabin primality test (exact for all `u64` via Sinckov/Jimenez bases).
pub fn is_prime_u64(n: u64) -> bool {
    if n < 2 {
        return false;
    }
    for small in [2u64, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37] {
        if n == small {
            return true;
        }
        if n % small == 0 {
            return false;
        }
    }
    let d_full = n - 1;
    let s = d_full.trailing_zeros();
    let d = d_full >> s;
    let mut dummy = FpOps::default();
    for a in [2u64, 325, 9375, 28178, 450775, 9780504, 1795265022] {
        let base = a % n;
        if base == 0 {
            continue;
        }
        let mut x = pow_mod(base, d, n, &mut dummy);
        if x == 1 || x == n - 1 {
            continue;
        }
        let mut composite = true;
        for _ in 1..s {
            x = mul_mod(x, x, n, &mut dummy);
            if x == n - 1 {
                composite = false;
                break;
            }
        }
        if composite {
            return false;
        }
    }
    true
}

/// Next prime strictly greater than or equal to `start`.
pub fn next_prime_at_least(start: u64) -> u64 {
    let mut candidate = if start <= 2 {
        2
    } else if (start & 1) == 0 {
        start + 1
    } else {
        start
    };
    while !is_prime_u64(candidate) {
        candidate = candidate.checked_add(2).expect("prime search overflow");
    }
    candidate
}

/// Euler quadratic-residuosity test: `true` iff `exists y in F_p: y^2 == a (mod p)`.
pub fn is_square_mod(a: u64, p: u64, ops: &mut FpOps) -> bool {
    if a == 0 {
        return true;
    }
    pow_mod(a, (p - 1) / 2, p, ops) == 1
}

/// Least quadratic non-residue in `F_p`.
pub fn first_nonsquare(p: u64) -> u64 {
    let mut ops = FpOps::default();
    for d in 2..p {
        if pow_mod(d, (p - 1) / 2, p, &mut ops) == p - 1 {
            return d;
        }
    }
    panic!("no quadratic non-residue found for p={p}");
}

/// Canonical Tonelli-Shanks square root in `[0, (p - 1) / 2]`, if `a` is a square in `F_p`.
/// Used during setup/fixture construction and independent checking, never as a CNF circuit.
pub fn sqrt_mod_canonical(a: u64, p: u64, ops: &mut FpOps) -> Option<u64> {
    let a = a % p;
    if a == 0 {
        return Some(0);
    }
    if pow_mod(a, (p - 1) / 2, p, ops) != 1 {
        return None;
    }
    let root = if p & 3 == 3 {
        pow_mod(a, (p + 1) / 4, p, ops)
    } else {
        let mut q = p - 1;
        let mut s = 0u32;
        while (q & 1) == 0 {
            q >>= 1;
            s += 1;
        }
        let mut z = 2u64;
        while pow_mod(z, (p - 1) / 2, p, ops) != p - 1 {
            z += 1;
        }
        let mut m = s;
        let mut c = pow_mod(z, q, p, ops);
        let mut t = pow_mod(a, q, p, ops);
        let mut r = pow_mod(a, (q + 1) / 2, p, ops);
        while t != 1 {
            let mut i = 1u32;
            let mut tmp = mul_mod(t, t, p, ops);
            while tmp != 1 {
                tmp = mul_mod(tmp, tmp, p, ops);
                i += 1;
                assert!(i < m, "Tonelli-Shanks failed to converge");
            }
            let mut b = c;
            for _ in 0..(m - i - 1) {
                b = mul_mod(b, b, p, ops);
            }
            m = i;
            c = mul_mod(b, b, p, ops);
            t = mul_mod(t, c, p, ops);
            r = mul_mod(r, b, p, ops);
        }
        r
    };
    let opp = p - root;
    let canon = root.min(opp);
    debug_assert_eq!(((canon as u128 * canon as u128) % (p as u128)) as u64, a);
    Some(canon)
}

/// Element `a + b * sqrt(nonsquare)` of `F_{p^2}` for exhaustive small-cell checks.
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq, PartialOrd, Ord)]
pub struct Fp2 {
    pub a: u64,
    pub b: u64,
}

impl Fp2 {
    #[inline]
    pub const fn rational(a: u64) -> Self {
        Self { a, b: 0 }
    }

    #[inline]
    pub const fn is_zero(self) -> bool {
        self.a == 0 && self.b == 0
    }

    #[inline]
    pub const fn is_rational(self) -> bool {
        self.b == 0
    }

    pub fn add(self, rhs: Self, p: u64) -> Self {
        let mut ops = FpOps::default();
        Self {
            a: add_mod(self.a, rhs.a, p, &mut ops),
            b: add_mod(self.b, rhs.b, p, &mut ops),
        }
    }

    pub fn neg(self, p: u64) -> Self {
        let mut ops = FpOps::default();
        Self {
            a: neg_mod(self.a, p, &mut ops),
            b: neg_mod(self.b, p, &mut ops),
        }
    }

    pub fn sub(self, rhs: Self, p: u64) -> Self {
        self.add(rhs.neg(p), p)
    }

    pub fn mul(self, rhs: Self, p: u64, nonsquare: u64) -> Self {
        let mut ops = FpOps::default();
        let aa = mul_mod(self.a, rhs.a, p, &mut ops);
        let bb = mul_mod(self.b, rhs.b, p, &mut ops);
        let nbb = mul_mod(nonsquare, bb, p, &mut ops);
        let ab = mul_mod(self.a, rhs.b, p, &mut ops);
        let ba = mul_mod(self.b, rhs.a, p, &mut ops);
        Self {
            a: add_mod(aa, nbb, p, &mut ops),
            b: add_mod(ab, ba, p, &mut ops),
        }
    }

    pub fn inv(self, p: u64, nonsquare: u64) -> Self {
        let mut ops = FpOps::default();
        let aa = mul_mod(self.a, self.a, p, &mut ops);
        let bb = mul_mod(self.b, self.b, p, &mut ops);
        let nbb = mul_mod(nonsquare, bb, p, &mut ops);
        let norm = sub_mod(aa, nbb, p, &mut ops);
        assert!(norm != 0, "Fp2 inverse of zero");
        let scale = inv_mod(norm, p, &mut ops);
        let neg_b = neg_mod(self.b, p, &mut ops);
        Self {
            a: mul_mod(self.a, scale, p, &mut ops),
            b: mul_mod(neg_b, scale, p, &mut ops),
        }
    }
}

/// Standalone FIPS 180-4 SHA-256 implementation for deterministic protocol-hash seed derivation.
pub fn sha256_bytes(input: &[u8]) -> [u8; 32] {
    const K: [u32; 64] = [
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4,
        0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe,
        0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f,
        0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
        0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc,
        0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
        0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116,
        0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
        0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7,
        0xc67178f2,
    ];
    let mut h: [u32; 8] = [
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab,
        0x5be0cd19,
    ];
    let bit_len = (input.len() as u64) * 8;
    let mut padded = input.to_vec();
    padded.push(0x80);
    while (padded.len() % 64) != 56 {
        padded.push(0);
    }
    padded.extend_from_slice(&bit_len.to_be_bytes());
    for chunk in padded.chunks_exact(64) {
        let mut w = [0u32; 64];
        for i in 0..16 {
            w[i] = u32::from_be_bytes([
                chunk[4 * i],
                chunk[4 * i + 1],
                chunk[4 * i + 2],
                chunk[4 * i + 3],
            ]);
        }
        for i in 16..64 {
            let s0 = w[i - 15].rotate_right(7) ^ w[i - 15].rotate_right(18) ^ (w[i - 15] >> 3);
            let s1 = w[i - 2].rotate_right(17) ^ w[i - 2].rotate_right(19) ^ (w[i - 2] >> 10);
            w[i] = w[i - 16]
                .wrapping_add(s0)
                .wrapping_add(w[i - 7])
                .wrapping_add(s1);
        }
        let mut a = h[0];
        let mut b = h[1];
        let mut c = h[2];
        let mut d = h[3];
        let mut e = h[4];
        let mut f = h[5];
        let mut g = h[6];
        let mut hh = h[7];
        for i in 0..64 {
            let s1 = e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25);
            let ch = (e & f) ^ ((!e) & g);
            let temp1 = hh
                .wrapping_add(s1)
                .wrapping_add(ch)
                .wrapping_add(K[i])
                .wrapping_add(w[i]);
            let s0 = a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22);
            let maj = (a & b) ^ (a & c) ^ (b & c);
            let temp2 = s0.wrapping_add(maj);
            hh = g;
            g = f;
            f = e;
            e = d.wrapping_add(temp1);
            d = c;
            c = b;
            b = a;
            a = temp1.wrapping_add(temp2);
        }
        h[0] = h[0].wrapping_add(a);
        h[1] = h[1].wrapping_add(b);
        h[2] = h[2].wrapping_add(c);
        h[3] = h[3].wrapping_add(d);
        h[4] = h[4].wrapping_add(e);
        h[5] = h[5].wrapping_add(f);
        h[6] = h[6].wrapping_add(g);
        h[7] = h[7].wrapping_add(hh);
    }
    let mut out = [0u8; 32];
    for (i, word) in h.iter().enumerate() {
        out[4 * i..4 * i + 4].copy_from_slice(&word.to_be_bytes());
    }
    out
}

/// Lowercase hex SHA-256 digest of `input`.
pub fn sha256_hex(input: &[u8]) -> String {
    let bytes = sha256_bytes(input);
    let mut out = String::with_capacity(64);
    for b in bytes {
        use std::fmt::Write;
        let _ = write!(&mut out, "{b:02x}");
    }
    out
}

/// Deterministic SHA-256-seeded SplitMix64 PRNG for reproducible instance & null generation.
#[derive(Debug, Clone)]
pub struct DeterministicRng {
    state: u64,
}

impl DeterministicRng {
    /// Derive initial 64-bit state from domain-separated label bytes via SHA-256.
    pub fn from_label(label: &str) -> Self {
        let digest = sha256_bytes(label.as_bytes());
        let seed = u64::from_le_bytes([
            digest[0], digest[1], digest[2], digest[3], digest[4], digest[5], digest[6], digest[7],
        ]);
        Self { state: seed }
    }

    /// Next 64-bit pseudorandom word.
    #[inline]
    pub fn next_u64(&mut self) -> u64 {
        self.state = self.state.wrapping_add(0x9e37_79b9_7f4a_7c15);
        let mut z = self.state;
        z = (z ^ (z >> 30)).wrapping_mul(0xbf58_476d_1ce4_e5b9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94d0_49bb_1331_11eb);
        z ^ (z >> 31)
    }

    /// Uniform unbiased draw in `[0, bound)`.
    pub fn uniform(&mut self, bound: u64) -> u64 {
        assert!(bound > 0);
        let zone = u64::MAX - (u64::MAX % bound);
        loop {
            let v = self.next_u64();
            if v < zone {
                return v % bound;
            }
        }
    }
}
