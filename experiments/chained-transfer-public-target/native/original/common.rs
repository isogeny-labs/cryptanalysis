// Shared primitives for the N4 solver: operation counters, F_q, K = F_{q^3}, rng.
//
// Cost unit: F_q multiplications (`MUL`), with inversions (`INV`) priced by a measured
// time ratio, and additions only counted. Every arm (IC, rho) uses these same
// primitives, so the same counter measures both. A K-multiplication is charged 11 F_q
// multiplications (schoolbook 9 plus 2 for the reduction by x^3 = c), a K-Frobenius 2.
#![allow(dead_code)]

pub static mut MUL: u64 = 0;
pub static mut INV: u64 = 0;
pub static mut ADD: u64 = 0;
// native work in other rings / not priced in F_q multiplications
pub static mut LMUL: u64 = 0; // mod-ell multiplications (linear algebra)
pub static mut LADD: u64 = 0;
pub static mut HASH: u64 = 0; // hash-table inserts and lookups
pub static mut CMP: u64 = 0; // distinguished-point / partition checks

#[derive(Clone, Copy, Debug, Default)]
pub struct Cnt {
    pub mul: u64,
    pub inv: u64,
    pub add: u64,
    pub lmul: u64,
    pub ladd: u64,
    pub hash: u64,
    pub cmp: u64,
}
impl Cnt {
    pub fn since(&self, o: &Cnt) -> Cnt {
        Cnt {
            mul: self.mul - o.mul,
            inv: self.inv - o.inv,
            add: self.add - o.add,
            lmul: self.lmul - o.lmul,
            ladd: self.ladd - o.ladd,
            hash: self.hash - o.hash,
            cmp: self.cmp - o.cmp,
        }
    }
}
pub fn snap() -> Cnt {
    unsafe {
        Cnt { mul: MUL, inv: INV, add: ADD, lmul: LMUL, ladd: LADD, hash: HASH, cmp: CMP }
    }
}
#[inline(always)]
pub fn bump_mul(n: u64) {
    unsafe { MUL += n }
}
#[inline(always)]
pub fn bump_inv(n: u64) {
    unsafe { INV += n }
}
#[inline(always)]
pub fn bump_add(n: u64) {
    unsafe { ADD += n }
}
#[inline(always)]
pub fn bump_lmul(n: u64) {
    unsafe { LMUL += n }
}
#[inline(always)]
pub fn bump_ladd(n: u64) {
    unsafe { LADD += n }
}
#[inline(always)]
pub fn bump_hash(n: u64) {
    unsafe { HASH += n }
}
#[inline(always)]
pub fn bump_cmp(n: u64) {
    unsafe { CMP += n }
}

pub struct Rng(pub u64);
impl Rng {
    pub fn new(seed: u64) -> Rng {
        let mut r = Rng(seed ^ 0x9E3779B97F4A7C15);
        for _ in 0..4 {
            r.next();
        }
        r
    }
    pub fn next(&mut self) -> u64 {
        let mut x = self.0;
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        self.0 = x;
        x.wrapping_mul(0x2545F4914F6CDD1D)
    }
    pub fn below(&mut self, n: u64) -> u64 {
        self.next() % n
    }
}

pub fn is_prime(n: u64) -> bool {
    if n < 2 {
        return false;
    }
    for p in [2u64, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37] {
        if n % p == 0 {
            return n == p;
        }
    }
    let mut d = n - 1;
    let mut s = 0;
    while d % 2 == 0 {
        d /= 2;
        s += 1;
    }
    'w: for a in [2u64, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37] {
        let mut x = powmod(a, d, n);
        if x == 1 || x == n - 1 {
            continue;
        }
        for _ in 0..s - 1 {
            x = ((x as u128 * x as u128) % n as u128) as u64;
            if x == n - 1 {
                continue 'w;
            }
        }
        return false;
    }
    true
}
pub fn powmod(mut a: u64, mut e: u64, m: u64) -> u64 {
    let mut r = 1u64;
    a %= m;
    while e > 0 {
        if e & 1 == 1 {
            r = ((r as u128 * a as u128) % m as u128) as u64;
        }
        a = ((a as u128 * a as u128) % m as u128) as u64;
        e >>= 1;
    }
    r
}
pub fn inv_mod_u64(a: u64, m: u64) -> u64 {
    // m prime or gcd(a,m)=1
    let (mut t, mut nt) = (0i128, 1i128);
    let (mut r, mut nr) = (m as i128, (a % m) as i128);
    while nr != 0 {
        let qq = r / nr;
        let tmp = t - qq * nt;
        t = nt;
        nt = tmp;
        let tmp = r - qq * nr;
        r = nr;
        nr = tmp;
    }
    assert!(r == 1, "not invertible");
    (((t % m as i128) + m as i128) % m as i128) as u64
}

/// Prime field F_q, q < 2^31.
#[derive(Clone, Copy)]
pub struct Fp {
    pub q: u64,
}
impl Fp {
    #[inline(always)]
    pub fn mul(&self, a: u64, b: u64) -> u64 {
        bump_mul(1);
        a * b % self.q
    }
    #[inline(always)]
    pub fn add(&self, a: u64, b: u64) -> u64 {
        bump_add(1);
        let s = a + b;
        if s >= self.q {
            s - self.q
        } else {
            s
        }
    }
    #[inline(always)]
    pub fn sub(&self, a: u64, b: u64) -> u64 {
        bump_add(1);
        if a >= b {
            a - b
        } else {
            a + self.q - b
        }
    }
    #[inline(always)]
    pub fn neg(&self, a: u64) -> u64 {
        if a == 0 {
            0
        } else {
            self.q - a
        }
    }
    pub fn inv(&self, a: u64) -> u64 {
        bump_inv(1);
        assert!(a != 0);
        let (mut t, mut nt) = (0i64, 1i64);
        let (mut r, mut nr) = (self.q as i64, a as i64);
        while nr != 0 {
            let qq = r / nr;
            let tmp = t - qq * nt;
            t = nt;
            nt = tmp;
            let tmp = r - qq * nr;
            r = nr;
            nr = tmp;
        }
        if t < 0 {
            t += self.q as i64;
        }
        t as u64
    }
    pub fn pow(&self, a: u64, mut e: u64) -> u64 {
        let mut r = 1u64;
        let mut b = a;
        while e > 0 {
            if e & 1 == 1 {
                r = self.mul(r, b);
            }
            e >>= 1;
            if e > 0 {
                b = self.mul(b, b);
            }
        }
        r
    }
    /// q = 3 mod 4 only.
    pub fn is_sq(&self, a: u64) -> bool {
        a == 0 || self.pow(a, (self.q - 1) / 2) == 1
    }
    pub fn sqrt(&self, a: u64) -> Option<u64> {
        if a == 0 {
            return Some(0);
        }
        let s = self.pow(a, (self.q + 1) / 4);
        if self.mul(s, s) == a {
            Some(s)
        } else {
            None
        }
    }
    pub fn rand(&self, r: &mut Rng) -> u64 {
        r.below(self.q)
    }
}

pub type K = [u64; 3];
pub const KZERO: K = [0, 0, 0];
pub const KONE: K = [1, 0, 0];

/// K = F_q[x]/(x^3 - c), q = 1 mod 3 (c a non-cube) and q = 3 mod 4.
#[derive(Clone)]
pub struct Kf {
    pub fp: Fp,
    pub c: u64,
    pub w: u64,  // c^((q-1)/3): x^q = w x
    pub w2: u64, // w^2
    pub size: u128,
}
impl Kf {
    pub fn new(q: u64) -> Kf {
        assert!(q % 12 == 7, "q must be 7 mod 12");
        let fp = Fp { q };
        let mut c = 2;
        loop {
            // c is a non-cube iff c^((q-1)/3) != 1
            if powmod(c, (q - 1) / 3, q) != 1 {
                break;
            }
            c += 1;
        }
        let w = powmod(c, (q - 1) / 3, q);
        Kf { fp, c, w, w2: w * w % q, size: (q as u128).pow(3) }
    }
    pub fn q(&self) -> u64 {
        self.fp.q
    }
    #[inline]
    pub fn add(&self, a: &K, b: &K) -> K {
        let f = &self.fp;
        [f.add(a[0], b[0]), f.add(a[1], b[1]), f.add(a[2], b[2])]
    }
    #[inline]
    pub fn sub(&self, a: &K, b: &K) -> K {
        let f = &self.fp;
        [f.sub(a[0], b[0]), f.sub(a[1], b[1]), f.sub(a[2], b[2])]
    }
    #[inline]
    pub fn neg(&self, a: &K) -> K {
        let f = &self.fp;
        [f.neg(a[0]), f.neg(a[1]), f.neg(a[2])]
    }
    pub fn mul(&self, a: &K, b: &K) -> K {
        bump_mul(11);
        bump_add(8);
        let q = self.fp.q;
        let t0 = a[0] * b[0] % q;
        let t1 = (a[0] * b[1] + a[1] * b[0]) % q;
        let t2 = (a[0] * b[2] + a[1] * b[1] + a[2] * b[0]) % q;
        let t3 = (a[1] * b[2] + a[2] * b[1]) % q;
        let t4 = a[2] * b[2] % q;
        [(t0 + self.c * t3) % q, (t1 + self.c * t4) % q, t2]
    }
    pub fn mul_fq(&self, a: &K, s: u64) -> K {
        let f = &self.fp;
        [f.mul(a[0], s), f.mul(a[1], s), f.mul(a[2], s)]
    }
    pub fn frob(&self, a: &K) -> K {
        let f = &self.fp;
        [a[0], f.mul(a[1], self.w), f.mul(a[2], self.w2)]
    }
    pub fn inv(&self, a: &K) -> K {
        // 1/a = a^q a^{q^2} / N(a)
        let a1 = self.frob(a);
        let a2 = self.frob(&a1);
        let p = self.mul(&a1, &a2);
        // N = a * p lies in F_q: only the constant coordinate is needed
        let f = &self.fp;
        let n = {
            bump_mul(5);
            let q = self.fp.q;
            let t0 = a[0] * p[0] % q;
            let t3 = (a[1] * p[2] + a[2] * p[1]) % q;
            (t0 + self.c * t3) % q
        };
        let ni = f.inv(n);
        self.mul_fq(&p, ni)
    }
    pub fn pow(&self, a: &K, mut e: u128) -> K {
        let mut r = KONE;
        let mut b = *a;
        while e > 0 {
            if e & 1 == 1 {
                r = self.mul(&r, &b);
            }
            e >>= 1;
            if e > 0 {
                b = self.mul(&b, &b);
            }
        }
        r
    }
    /// q^3 = 3 mod 4
    pub fn sqrt(&self, a: &K) -> Option<K> {
        if *a == KZERO {
            return Some(KZERO);
        }
        let s = self.pow(a, (self.size + 1) / 4);
        if self.mul(&s, &s) == *a {
            Some(s)
        } else {
            None
        }
    }
    pub fn rand(&self, r: &mut Rng) -> K {
        [r.below(self.fp.q), r.below(self.fp.q), r.below(self.fp.q)]
    }
    pub fn is_fq(&self, a: &K) -> bool {
        a[1] == 0 && a[2] == 0
    }
    pub fn from_fq(&self, s: u64) -> K {
        [s % self.fp.q, 0, 0]
    }
}
