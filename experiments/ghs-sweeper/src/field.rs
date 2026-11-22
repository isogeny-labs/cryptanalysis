//! Integer power-basis fields, polynomial arithmetic, and character transforms.

use anyhow::{ensure, Result};
use std::collections::{BTreeMap, BTreeSet};
use std::sync::{Arc, Mutex};

pub fn rem(mut a: u32, b: u32) -> u32 {
    assert_ne!(b, 0);
    while a != 0 && a.ilog2() >= b.ilog2() {
        a ^= b << (a.ilog2() - b.ilog2());
    }
    a
}
fn gcd(mut a: u32, mut b: u32) -> u32 {
    while b != 0 {
        (a, b) = (b, rem(a, b));
    }
    a
}
pub fn bit_mul(mut a: u32, mut b: u32, modulus: u32) -> u32 {
    let degree = modulus.ilog2();
    let mut value = 0;
    while b != 0 {
        if b & 1 != 0 {
            value ^= a;
        }
        b >>= 1;
        a <<= 1;
        if a >> degree != 0 {
            a ^= modulus;
        }
    }
    value
}
pub fn bit_irreducible(poly: u32) -> bool {
    if poly < 2 {
        return false;
    }
    let n = poly.ilog2();
    let x = rem(2, poly);
    let mut value = x;
    for i in 1..=n {
        value = bit_mul(value, value, poly);
        if i <= n / 2 && gcd(value ^ x, poly) != 1 {
            return false;
        }
    }
    value == x
}
pub fn prime_divisors(mut n: u32) -> Vec<u32> {
    let mut values = Vec::new();
    let mut p = 2;
    while p * p <= n {
        if n.is_multiple_of(p) {
            values.push(p);
            while n.is_multiple_of(p) {
                n /= p;
            }
        }
        p += 1;
    }
    if n > 1 {
        values.push(n);
    }
    values
}

#[derive(Debug)]
pub struct Field {
    pub degree: u32,
    pub size: u32,
    pub modulus: u32,
    log: Vec<usize>,
    exp: Vec<u32>,
    pub trace: Vec<u32>,
}
impl Field {
    pub fn new(degree: u32) -> Result<Self> {
        ensure!((1..=20).contains(&degree), "field degree must be in 1..=20");
        let size = 1 << degree;
        let modulus = ((size | 1)..(size << 1))
            .step_by(2)
            .find(|&p| bit_irreducible(p))
            .unwrap();
        let factors = prime_divisors(size - 1);
        let power = |mut a, mut e| {
            let mut r = 1;
            while e != 0 {
                if e & 1 != 0 {
                    r = bit_mul(r, a, modulus);
                }
                a = bit_mul(a, a, modulus);
                e >>= 1;
            }
            r
        };
        let generator = (1..size)
            .find(|&a| factors.iter().all(|p| power(a, (size - 1) / p) != 1))
            .unwrap();
        let mut log = vec![usize::MAX; size as usize];
        let mut exp = Vec::with_capacity(2 * (size - 1) as usize);
        let mut a = 1;
        for i in 0..size - 1 {
            ensure!(log[a as usize] == usize::MAX, "invalid generator");
            log[a as usize] = i as usize;
            exp.push(a);
            a = bit_mul(a, generator, modulus);
        }
        ensure!(a == 1, "generator did not close");
        exp.extend_from_within(..);
        let mut f = Self {
            degree,
            size,
            modulus,
            log,
            exp,
            trace: Vec::with_capacity(size as usize),
        };
        for a in 0..size {
            let (mut v, mut c) = (0, a);
            for _ in 0..degree {
                v ^= c;
                c = f.mul(c, c);
            }
            ensure!(v < 2, "absolute trace left F2");
            f.trace.push(v);
        }
        Ok(f)
    }
    #[inline]
    pub fn mul(&self, a: u32, b: u32) -> u32 {
        if a == 0 || b == 0 {
            0
        } else {
            self.exp[self.log[a as usize] + self.log[b as usize]]
        }
    }
    #[inline]
    pub fn inv(&self, a: u32) -> u32 {
        assert_ne!(a, 0);
        self.exp[(self.size - 1) as usize - self.log[a as usize]]
    }
    pub fn power(&self, a: u32, e: u64) -> u32 {
        if a == 0 {
            u32::from(e == 0)
        } else {
            self.exp[(self.log[a as usize] as u64 * e % (self.size - 1) as u64) as usize]
        }
    }
    pub fn evaluate(&self, p: &[u32], x: u32) -> u32 {
        p.iter().rev().fold(0, |a, &c| self.mul(a, x) ^ c)
    }
    pub fn embedding(&self, base: &Field) -> Result<Vec<u32>> {
        ensure!(
            self.degree.is_multiple_of(base.degree),
            "base is not a subfield"
        );
        if base.degree == 1 {
            return Ok(vec![0, 1]);
        }
        let coefficients = decode(base.modulus, base.degree + 1, 1);
        let root = (0..self.size)
            .find(|&a| self.evaluate(&coefficients, a) == 0)
            .unwrap();
        Ok((0..base.size)
            .map(|a| self.evaluate(&decode(a, base.degree, 1), root))
            .collect())
    }
}

#[derive(Default)]
pub struct FieldCache(Mutex<BTreeMap<u32, Arc<Field>>>);
impl FieldCache {
    pub fn get(&self, degree: u32) -> Result<Arc<Field>> {
        let mut fields = self.0.lock().unwrap();
        if let Some(f) = fields.get(&degree) {
            return Ok(Arc::clone(f));
        }
        let f = Arc::new(Field::new(degree)?);
        fields.insert(degree, Arc::clone(&f));
        Ok(f)
    }
}
pub fn decode(value: u32, length: u32, bits: u32) -> Vec<u32> {
    (0..length)
        .map(|i| (value >> (bits * i)) & ((1 << bits) - 1))
        .collect()
}
pub fn encode(p: &[u32], bits: u32) -> u32 {
    p.iter()
        .enumerate()
        .map(|(i, &c)| c << (bits * i as u32))
        .sum()
}
fn trim(mut p: Vec<u32>) -> Vec<u32> {
    while p.last() == Some(&0) {
        p.pop();
    }
    p
}
fn poly_rem(mut p: Vec<u32>, h: &[u32], f: &Field) -> Vec<u32> {
    p = trim(p);
    let inverse = f.inv(*h.last().unwrap());
    while p.len() >= h.len() {
        let factor = f.mul(*p.last().unwrap(), inverse);
        let offset = p.len() - h.len();
        for (i, &c) in h.iter().enumerate() {
            p[offset + i] ^= f.mul(factor, c);
        }
        p = trim(p);
    }
    p
}
fn poly_gcd(mut a: Vec<u32>, mut b: Vec<u32>, f: &Field) -> Vec<u32> {
    while !b.is_empty() {
        let r = poly_rem(a, &b, f);
        a = b;
        b = r;
    }
    a
}
pub fn irreducible(h: &[u32], f: &Field) -> bool {
    if f.degree == 1 {
        return bit_irreducible(encode(h, 1));
    }
    let n = h.len() - 1;
    let x = vec![0, 1];
    let mut v = x.clone();
    let checks: BTreeSet<_> = prime_divisors(n as u32)
        .iter()
        .map(|p| n / *p as usize)
        .collect();
    for i in 1..=n {
        for _ in 0..f.degree {
            let mut squared = vec![0; v.len().saturating_mul(2).saturating_sub(1)];
            for (i, &c) in v.iter().enumerate() {
                squared[2 * i] = f.mul(c, c);
            }
            v = poly_rem(squared, h, f);
        }
        if checks.contains(&i) {
            let mut difference = v.clone();
            difference.resize(difference.len().max(2), 0);
            difference[1] ^= 1;
            if poly_gcd(h.to_vec(), trim(difference), f).len() != 1 {
                return false;
            }
        }
    }
    v == x
}
pub fn affine(h: &[u32], a: u32, b: u32, f: &Field) -> Vec<u32> {
    let n = h.len() - 1;
    let mut pa = vec![1];
    let mut pb = vec![1];
    for i in 0..n {
        pa.push(f.mul(pa[i], a));
        pb.push(f.mul(pb[i], b));
    }
    let mut result = vec![0; n + 1];
    for (i, &c) in h.iter().enumerate() {
        for j in 0..=i {
            if i & j == j {
                result[j] ^= f.mul(c, f.mul(pa[j], pb[i - j]));
            }
        }
    }
    let inverse = f.inv(result[n]);
    for c in &mut result {
        *c = f.mul(*c, inverse);
    }
    result
}
pub fn walsh(a: &mut [i64]) {
    let mut step = 1;
    while step < a.len() {
        for block in a.chunks_exact_mut(2 * step) {
            let (left, right) = block.split_at_mut(step);
            for (x, y) in left.iter_mut().zip(right) {
                let (u, v) = (*x, *y);
                *x = u + v;
                *y = u - v;
            }
        }
        step *= 2;
    }
}
