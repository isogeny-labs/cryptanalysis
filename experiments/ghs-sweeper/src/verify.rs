//! Separate carryless-product/Euclid implementation. No log tables or Walsh.
use crate::search::{Candidate, Spec};
use crate::source::Source;
use anyhow::{ensure, Result};
use std::collections::BTreeMap;
use std::sync::Arc;

pub struct RawField {
    pub degree: u32,
    pub size: u32,
    pub modulus: u32,
    pub traces: Vec<u32>,
    pub inverses: Vec<u32>,
}
impl RawField {
    pub fn new(degree: u32, modulus: u32) -> Result<Self> {
        ensure!(
            (1..=20).contains(&degree) && modulus > 1 && modulus.ilog2() == degree,
            "invalid raw field modulus"
        );
        let mut f = Self {
            degree,
            modulus,
            size: 1 << degree,
            traces: Vec::new(),
            inverses: vec![0],
        };
        for a in 0..f.size {
            let (mut value, mut c) = (0, a);
            for _ in 0..degree {
                value ^= c;
                c = f.mul(c, c);
            }
            ensure!(value < 2, "raw trace left F2");
            f.traces.push(value);
        }
        for a in 1..f.size {
            f.inverses.push(f.inverse(a)?);
        }
        Ok(f)
    }
    pub fn mul(&self, a: u32, b: u32) -> u32 {
        let mut product = 0_u64;
        for i in 0..32 - b.leading_zeros() {
            if b & (1 << i) != 0 {
                product ^= (a as u64) << i;
            }
        }
        while product >= 1_u64 << self.degree {
            product ^= (self.modulus as u64) << (product.ilog2() - self.degree);
        }
        product as u32
    }
    fn inverse(&self, a: u32) -> Result<u32> {
        let (mut u, mut v, mut s, mut t) = (a as u64, self.modulus as u64, 1_u64, 0_u64);
        while u != 1 {
            ensure!(u != 0, "raw modulus is reducible");
            if u.ilog2() < v.ilog2() {
                std::mem::swap(&mut u, &mut v);
                std::mem::swap(&mut s, &mut t);
            }
            let shift = u.ilog2() - v.ilog2();
            u ^= v << shift;
            s ^= t << shift;
        }
        while s >= 1_u64 << self.degree {
            s ^= (self.modulus as u64) << (s.ilog2() - self.degree);
        }
        ensure!(self.mul(a, s as u32) == 1, "raw inverse failed");
        Ok(s as u32)
    }
    pub fn evaluate(&self, p: &[u32], x: u32) -> u32 {
        let (mut value, mut power) = (0, 1);
        for &c in p {
            value ^= self.mul(c, power);
            power = self.mul(power, x);
        }
        value
    }
}
#[derive(Default)]
pub struct RawCache(BTreeMap<(u32, u32), Arc<RawField>>);
impl RawCache {
    pub fn get(&mut self, degree: u32, modulus: u32) -> Result<Arc<RawField>> {
        let key = (degree, modulus);
        if let Some(f) = self.0.get(&key) {
            return Ok(Arc::clone(f));
        }
        let f = Arc::new(RawField::new(degree, modulus)?);
        self.0.insert(key, Arc::clone(&f));
        Ok(f)
    }
}

pub fn verify_candidate(c: &Candidate, cache: &mut RawCache) -> Result<Vec<u64>> {
    let m = &c.model;
    let (d, n) = (m.base_degree, m.relative_degree);
    let spec = Spec {
        base_degree: d,
        relative_degree: n,
    };
    spec.validate()?;
    ensure!(
        c.spectral_model_id == crate::identifier(m)?,
        "model ID does not match equation"
    );
    ensure!(
        m.genus == n
            && m.h.len() == n as usize + 1
            && m.h.last() == Some(&1)
            && m.r.len() == n as usize
            && m.r.iter().any(|&v| v != 0)
            && m.h.iter().chain(&m.r).all(|&v| v < spec.q())
            && m.a > 0
            && m.a < spec.q()
            && m.c < spec.q(),
        "invalid model parameters"
    );
    let t = c.elliptic_trace;
    ensure!(
        t.unsigned_abs() <= 2 * spec.size() as u64 && t & 1 != 0 && t * t <= 4 * spec.size() as i64,
        "invalid elliptic trace"
    );
    ensure!(
        c.source_order as i64 == spec.size() as i64 + 1 - t,
        "invalid source order"
    );
    ensure!(
        c.point_counts.len() == n as usize
            && c.field_moduli.len() == n as usize
            && c.base_embeddings.len() == n as usize,
        "incomplete field data"
    );
    let mut counts = Vec::new();
    for e in 1..=n {
        let f = cache.get(d * e, c.field_moduli[(e - 1) as usize])?;
        let embed = &c.base_embeddings[(e - 1) as usize];
        ensure!(
            embed.len() == spec.q() as usize
                && embed[0..2] == [0, 1]
                && embed.iter().all(|&v| v < f.size),
            "invalid embedding"
        );
        let root = if d == 1 { 1 } else { embed[2] };
        let base_poly: Vec<_> = (0..=d).map(|j| (c.field_moduli[0] >> j) & 1).collect();
        ensure!(
            f.evaluate(&base_poly, root) == 0,
            "embedding violates base modulus"
        );
        for (i, &a) in embed.iter().enumerate() {
            let mut v = a;
            for _ in 0..d {
                v = f.mul(v, v);
            }
            let coefficients: Vec<_> = (0..d).map(|j| ((i as u32) >> j) & 1).collect();
            ensure!(
                v == a && a == f.evaluate(&coefficients, root),
                "embedding basis mismatch"
            );
        }
        let h: Vec<_> = m.h.iter().map(|&v| embed[v as usize]).collect();
        let r: Vec<_> = m.r.iter().map(|&v| embed[v as usize]).collect();
        let (mut count, mut poles) = (1_u64, 0);
        for x in 0..f.size {
            let den = f.evaluate(&h, x);
            if den == 0 {
                count += 1;
                poles += 1;
            } else {
                let v = f.mul(embed[m.a as usize], x)
                    ^ embed[m.c as usize]
                    ^ f.mul(f.evaluate(&r, x), f.inverses[den as usize]);
                if f.traces[v as usize] == 0 {
                    count += 2;
                }
            }
        }
        ensure!(
            poles == if e == n { n } else { 0 },
            "independent pole orbit mismatch"
        );
        let expected = f.size as i64 + 1 - if e == n { n as i64 * t } else { 0 };
        ensure!(
            expected >= 0 && count == expected as u64 && count == c.point_counts[(e - 1) as usize],
            "independent point count mismatch in degree {e}"
        );
        counts.push(count);
    }
    Ok(counts)
}
pub fn verify_source(source: &Source, cache: &mut RawCache) -> Result<u64> {
    let f = cache.get(source.absolute_degree, source.modulus)?;
    ensure!(
        source.b > 0 && source.b < f.size && source.a < f.size,
        "invalid elliptic source"
    );
    let mut count = 2;
    for x in 1..f.size {
        let v = x ^ source.a ^ f.mul(source.b, f.inverses[f.mul(x, x) as usize]);
        if f.traces[v as usize] == 0 {
            count += 2;
        }
    }
    ensure!(
        count == source.order && count as i64 == f.size as i64 + 1 - source.elliptic_trace,
        "independent source order mismatch"
    );
    Ok(count)
}
