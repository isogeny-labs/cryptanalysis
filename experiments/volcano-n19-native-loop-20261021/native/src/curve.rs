//! GF(2^19) = F_2[z]/(m) and E: y^2 + x y = x^3 + 1 (run.sage's field and tau.sage's
//! curve, a-invariants [1, 0, 0, 0, 1]), affine coordinates. Field elements are
//! integers, bit i = coefficient of z^i (Sage's `to_integer`).
//!
//! Multiplication is a 4-bit comb with table reduction; the crate tests compare
//! it with the v3 `gf_mul` (the per-shift solve's own arithmetic) on random inputs.
//! Everything here computes values that are unique (a sum of points, a
//! Frobenius image, a square root's two candidates); the only choice Sage makes
//! is which y `lift_x` returns, handled in `lift_x_all`.

use crate::v3::gf_mul;

pub type Pt = Option<(u64, u64)>;

pub struct Field {
    pub n: u32,
    pub modulus: u64,
    mask: u64,
    red: [[u64; 256]; 3],
}

impl Field {
    pub fn new(n: u32, modulus: u64) -> Field {
        assert!(n == 19 && modulus >> n == 1, "this port is written for n = 19");
        let mut red = [[0u64; 256]; 3];
        // red[t][c] = c * z^(n + 8t) mod m, for the high part of a product (at most 2n - 1 bits).
        for t in 0..3u32 {
            let zt = (0..n + 8 * t).fold(1u64, |a, _| gf_mul(a, 2, n, modulus));
            for c in 0..256u64 {
                red[t as usize][c as usize] = gf_mul(c, zt, n, modulus);
            }
        }
        Field { n, modulus, mask: (1u64 << n) - 1, red }
    }

    #[inline]
    pub fn mul(&self, a: u64, b: u64) -> u64 {
        let mut tab = [0u64; 16];
        tab[1] = a;
        for i in 2..16 {
            tab[i] = if i & 1 == 0 { tab[i >> 1] << 1 } else { tab[i - 1] ^ a };
        }
        let mut r = 0u64;
        let mut bb = b;
        let mut sh = 0;
        while bb != 0 {
            r ^= tab[(bb & 15) as usize] << sh;
            bb >>= 4;
            sh += 4;
        }
        let hi = r >> self.n;
        (r & self.mask)
            ^ self.red[0][(hi & 255) as usize]
            ^ self.red[1][((hi >> 8) & 255) as usize]
            ^ self.red[2][((hi >> 16) & 255) as usize]
    }

    #[inline]
    pub fn sq(&self, a: u64) -> u64 {
        self.mul(a, a)
    }

    fn sqn(&self, mut a: u64, k: u32) -> u64 {
        for _ in 0..k {
            a = self.sq(a);
        }
        a
    }

    /// a^(2^19 - 2) by the Itoh-Tsujii chain 1, 2, 4, 8, 16, 18.
    pub fn inv(&self, a: u64) -> u64 {
        assert!(a != 0, "inverse of zero");
        let b1 = a;
        let b2 = self.mul(self.sqn(b1, 1), b1);
        let b4 = self.mul(self.sqn(b2, 2), b2);
        let b8 = self.mul(self.sqn(b4, 4), b4);
        let b16 = self.mul(self.sqn(b8, 8), b8);
        let b18 = self.mul(self.sqn(b16, 2), b2);
        self.sq(b18)
    }

    /// Absolute trace to F_2.
    pub fn trace(&self, a: u64) -> u64 {
        let (mut t, mut s) = (a, a);
        for _ in 0..self.n - 1 {
            t = self.sq(t);
            s ^= t;
        }
        s
    }

    /// tau.sage halfTraceTau(c, n): c + c^4 + ... ((n - 1) / 2 terms after c).
    pub fn half_trace(&self, c: u64) -> u64 {
        let (mut t, mut s) = (c, c);
        for _ in 0..(self.n - 1) / 2 {
            t = self.sq(self.sq(t));
            s ^= t;
        }
        s
    }

    pub fn frob(&self, p: Pt, e: u32) -> Pt {
        p.map(|(x, y)| (self.sqn(x, e), self.sqn(y, e)))
    }

    pub fn neg(&self, p: Pt) -> Pt {
        p.map(|(x, y)| (x, x ^ y))
    }

    pub fn on_curve(&self, p: Pt) -> bool {
        match p {
            None => true,
            Some((x, y)) => self.sq(y) ^ self.mul(x, y) == self.mul(self.sq(x), x) ^ 1,
        }
    }

    pub fn add(&self, p: Pt, q: Pt) -> Pt {
        let (x1, y1) = match p {
            None => return q,
            Some(v) => v,
        };
        let (x2, y2) = match q {
            None => return p,
            Some(v) => v,
        };
        if x1 == x2 {
            if y2 == x1 ^ y1 {
                return None; // q = -p (also covers 2-torsion, x = 0)
            }
            // doubling: lambda = x + y / x; x3 = lambda^2 + lambda; y3 = x^2 + (lambda + 1) x3
            let l = x1 ^ self.mul(y1, self.inv(x1));
            let x3 = self.sq(l) ^ l;
            let y3 = self.sq(x1) ^ self.mul(l ^ 1, x3);
            return Some((x3, y3));
        }
        let l = self.mul(y1 ^ y2, self.inv(x1 ^ x2));
        let x3 = self.sq(l) ^ l ^ x1 ^ x2;
        let y3 = self.mul(l, x1 ^ x3) ^ x3 ^ y1;
        Some((x3, y3))
    }

    /// k * p for k >= 0, left-to-right double and add.
    pub fn mul_pt(&self, k: u64, p: Pt) -> Pt {
        let mut r: Pt = None;
        if k == 0 {
            return None;
        }
        for i in (0..64 - k.leading_zeros()).rev() {
            r = self.add(r, r);
            if (k >> i) & 1 == 1 {
                r = self.add(r, p);
            }
        }
        r
    }

    /// Both points with this x, in Sage 10.10's `lift_x` order: ascending in the
    /// integer encoding of y. (tau.sage takes `lift_x(rx)` for the 29 orbit
    /// representatives and `lift_x(x, all=True)[0]` for the generator; the
    /// archived relations of run 39387473809 fix Sage's choice on all 29
    /// representatives and the archived generator fixes it on the generator's x;
    /// both are the smaller y. The planted arm compares every representative and
    /// the generator with Sage's in every process.)
    pub fn lift_x_all(&self, x: u64) -> Vec<(u64, u64)> {
        if x == 0 {
            return vec![(0, 1)]; // y^2 = 1
        }
        let c = x ^ self.inv(self.sq(x));
        if self.trace(c) != 0 {
            return vec![];
        }
        let w = self.half_trace(c);
        let (y1, y2) = (self.mul(x, w), self.mul(x, w ^ 1));
        if y1 < y2 {
            vec![(x, y1), (x, y2)]
        } else {
            vec![(x, y2), (x, y1)]
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    const M: u64 = 854355;

    #[test]
    fn fast_mul_equals_v3_gf_mul_and_inverse() {
        let f = Field::new(19, M);
        let mut st = 0x9e37_79b9_7f4a_7c15u64;
        for _ in 0..20000 {
            st ^= st << 13;
            st ^= st >> 7;
            st ^= st << 17;
            let a = st & ((1 << 19) - 1);
            let b = (st >> 21) & ((1 << 19) - 1);
            assert_eq!(f.mul(a, b), gf_mul(a, b, 19, M));
            if a != 0 {
                assert_eq!(f.mul(a, f.inv(a)), 1);
            }
        }
    }

    #[test]
    fn group_law() {
        let f = Field::new(19, M);
        let mut pts = vec![];
        for x in 1..400u64 {
            for p in f.lift_x_all(x) {
                assert!(f.on_curve(Some(p)));
                pts.push(Some(p));
            }
        }
        assert!(pts.len() > 300);
        // group order 523492 = 4 * 130873
        for &p in pts.iter().take(40) {
            assert_eq!(f.mul_pt(523492, p), None);
            let q = f.mul_pt(4, p);
            assert_eq!(f.mul_pt(130873, q), None);
        }
        for w in pts.windows(3).take(100) {
            let (a, b, c) = (w[0], w[1], w[2]);
            assert_eq!(f.add(f.add(a, b), c), f.add(a, f.add(b, c)));
            assert_eq!(f.add(a, b), f.add(b, a));
            assert_eq!(f.add(a, f.neg(a)), None);
            assert_eq!(f.add(a, a), f.mul_pt(2, a));
            assert_eq!(f.mul_pt(5, a), f.add(f.mul_pt(3, a), f.mul_pt(2, a)));
        }
    }
}
