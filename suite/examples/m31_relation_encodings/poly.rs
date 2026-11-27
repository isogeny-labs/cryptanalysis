//! Small sparse Fp builder. Leaf-domain reduction is explicit and common to
//! every encoding; this is not Boolean arithmetic.
use cryptanalysis_suite::cryptanalysis::f4_fp::{self, Ordering, Poly};
use std::collections::BTreeMap;
use std::time::Instant;

#[derive(Clone, Debug)]
pub struct P(pub BTreeMap<Vec<u32>, u64>);
pub struct Ring {
    pub p: u64,
    pub n: usize,
    pub domains: Vec<Option<Vec<u64>>>,
    pub deadline: Instant,
    pub term_cap: usize,
}
pub fn mul(a: u64, b: u64, p: u64) -> u64 {
    (u128::from(a) * u128::from(b) % u128::from(p)) as u64
}
pub fn pow(mut a: u64, mut e: u64, p: u64) -> u64 {
    let mut r = 1;
    while e != 0 {
        if e & 1 != 0 {
            r = mul(r, a, p);
        }
        a = mul(a, a, p);
        e >>= 1;
    }
    r
}
impl Ring {
    pub fn check(&self) -> Result<(), String> {
        if Instant::now() > self.deadline {
            Err("construction_budget".into())
        } else {
            Ok(())
        }
    }
    pub fn c(&self, c: u64) -> P {
        let mut t = BTreeMap::new();
        if c % self.p != 0 {
            t.insert(vec![0; self.n], c % self.p);
        }
        P(t)
    }
    pub fn v(&self, i: usize) -> P {
        let mut e = vec![0; self.n];
        e[i] = 1;
        P(BTreeMap::from([(e, 1)]))
    }
    pub fn add(&self, a: &P, b: &P) -> P {
        let mut r = a.0.clone();
        for (e, c) in &b.0 {
            let x = r.entry(e.clone()).or_default();
            *x = (*x + c) % self.p;
        }
        r.retain(|_, v| *v != 0);
        P(r)
    }
    pub fn scale(&self, a: &P, c: u64) -> P {
        P(a.0
            .iter()
            .filter_map(|(e, x)| {
                let v = mul(*x, c, self.p);
                (v != 0).then(|| (e.clone(), v))
            })
            .collect())
    }
    pub fn sub(&self, a: &P, b: &P) -> P {
        self.add(a, &self.scale(b, self.p - 1))
    }
    fn domain_coeffs(&self, roots: &[u64]) -> Vec<u64> {
        let mut coeff = vec![1];
        for &root in roots {
            let mut out = vec![0; coeff.len() + 1];
            for (i, &c) in coeff.iter().enumerate() {
                out[i] = (out[i] + mul(c, (self.p - root) % self.p, self.p)) % self.p;
                out[i + 1] = (out[i + 1] + c) % self.p;
            }
            coeff = out;
        }
        coeff
    }
    pub fn product(&self, a: &P, b: &P) -> Result<P, String> {
        self.check()?;
        let mut terms = BTreeMap::new();
        for (ea, ca) in &a.0 {
            for (eb, cb) in &b.0 {
                let e: Vec<u32> = ea.iter().zip(eb).map(|(a, b)| a + b).collect();
                let x = terms.entry(e).or_insert(0u64);
                *x = (*x + mul(*ca, *cb, self.p)) % self.p;
            }
            if terms.len() > self.term_cap {
                return Err("construction_term_cap".into());
            }
        }
        terms.retain(|_, c| *c != 0);
        // Remainder modulo each monic leaf-membership polynomial. Reducing
        // determinants in this quotient preserves their zero set on the base.
        for (variable, domain) in self.domains.iter().enumerate() {
            let Some(roots) = domain else { continue };
            let d = roots.len() as u32;
            if d == 0 {
                return Err("empty leaf domain".into());
            }
            let coeff = self.domain_coeffs(roots);
            loop {
                let mut next = BTreeMap::new();
                let mut changed = false;
                for (e, c) in terms {
                    if e[variable] < d {
                        let v = next.entry(e).or_insert(0u64);
                        *v = (*v + c) % self.p;
                        continue;
                    }
                    changed = true;
                    for k in 0..d as usize {
                        if coeff[k] == 0 {
                            continue;
                        }
                        let mut f = e.clone();
                        f[variable] = e[variable] - d + k as u32;
                        let v = mul(c, (self.p - coeff[k]) % self.p, self.p);
                        let x = next.entry(f).or_insert(0u64);
                        *x = (*x + v) % self.p;
                    }
                }
                next.retain(|_, c| *c != 0);
                terms = next;
                if !changed {
                    break;
                }
                self.check()?;
                if terms.len() > self.term_cap {
                    return Err("construction_term_cap".into());
                }
            }
        }
        Ok(P(terms))
    }
    pub fn sq(&self, a: &P) -> Result<P, String> {
        self.product(a, a)
    }
    #[cfg(test)]
    pub fn eval(&self, a: &P, x: &[u64]) -> u64 {
        a.0.iter().fold(0, |sum, (e, c)| {
            let term = e
                .iter()
                .zip(x)
                .fold(*c, |t, (&e, &x)| mul(t, pow(x, e as u64, self.p), self.p));
            (sum + term) % self.p
        })
    }
    pub fn export(&self, a: &P, n: usize) -> Poly {
        let t: Vec<_> =
            a.0.iter()
                .map(|(e, c)| {
                    assert!(e[n..].iter().all(|&v| v == 0));
                    (e[..n].to_vec(), *c)
                })
                .collect();
        f4_fp::normalise(&t, self.p, Ordering::Grevlex)
    }
    pub fn membership(&self, x: &P, roots: &[u64]) -> Result<P, String> {
        // Do not use quotient reduction here: this is the domain generator.
        let mut out = self.c(1);
        for &a in roots {
            let factor = self.sub(x, &self.c(a));
            let mut t = BTreeMap::new();
            for (e, c) in &out.0 {
                for (f, d) in &factor.0 {
                    let k = e.iter().zip(f).map(|(a, b)| a + b).collect();
                    let v = t.entry(k).or_insert(0u64);
                    *v = (*v + mul(*c, *d, self.p)) % self.p;
                }
            }
            t.retain(|_, c| *c != 0);
            out = P(t);
        }
        Ok(out)
    }
    pub fn coefficient(&self, a: &P, index: usize) -> Vec<P> {
        let degree = a.0.keys().map(|e| e[index]).max().unwrap_or(0) as usize;
        let mut v = vec![self.c(0); degree + 1];
        for (e, c) in &a.0 {
            let mut f = e.clone();
            let i = f[index] as usize;
            f[index] = 0;
            v[i].0.insert(f, *c);
        }
        v
    }
    pub fn resultant(&self, a: &[P], b: &[P]) -> Result<P, String> {
        let da = a.len() - 1;
        let db = b.len() - 1;
        let size = da + db;
        let mut matrix = vec![vec![self.c(0); size]; size];
        for row in 0..db {
            for j in 0..=da {
                matrix[row][row + j] = a[da - j].clone();
            }
        }
        for row in 0..da {
            for j in 0..=db {
                matrix[db + row][row + j] = b[db - j].clone();
            }
        }
        // Subset determinant DP: no division or unguarded pivots. At most
        // 2^6 states for S5's quartic/quadratic Sylvester matrix.
        if size > 6 {
            return Err("resultant_matrix_cap".into());
        }
        let mut dp = vec![self.c(0); 1usize << size];
        dp[0] = self.c(1);
        for mask in 0usize..(1usize << size) - 1 {
            let row = mask.count_ones() as usize;
            for col in 0..size {
                if mask >> col & 1 != 0 {
                    continue;
                }
                let mut term = self.product(&dp[mask], &matrix[row][col])?;
                if (mask >> (col + 1)).count_ones() % 2 != 0 {
                    term = self.scale(&term, self.p - 1);
                }
                let next = mask | 1 << col;
                dp[next] = self.add(&dp[next], &term);
            }
            self.check()?;
        }
        Ok(dp.pop().unwrap())
    }
}

pub fn s3(r: &Ring, x: &P, y: &P, z: &P, a: u64, b: u64) -> Result<P, String> {
    let xy = r.product(x, y)?;
    let sum = r.add(x, y);
    let d = r.sub(x, y);
    let t1 = r.product(&r.sq(&d)?, &r.sq(z)?)?;
    let inner = r.add(
        &r.product(&sum, &r.add(&xy, &r.c(a)))?,
        &r.c(mul(2, b, r.p)),
    );
    let t2 = r.scale(&r.product(&inner, z)?, (r.p - 2) % r.p);
    let t3 = r.sub(&r.sq(&r.sub(&xy, &r.c(a)))?, &r.scale(&sum, mul(4, b, r.p)));
    Ok(r.add(&r.add(&t1, &t2), &t3))
}
