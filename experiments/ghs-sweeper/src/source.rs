//! Elliptic source matching and the scoped canonical GHS comparison.
use crate::field::{walsh, Field, FieldCache};
use crate::search::Spec;
use anyhow::{ensure, Result};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Baseline {
    pub augmented_frobenius_rank: u32,
    pub coefficient_rank: u32,
    pub formal_canonical_ghs_genus: u64,
    pub canonical_frobenius_lift_exists: bool,
    pub scope: String,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Source {
    pub equation: String,
    pub absolute_degree: u32,
    pub modulus: u32,
    pub a: u32,
    pub b: u32,
    pub elliptic_trace: i64,
    pub order: u64,
    pub b_absolute_degree: u32,
    pub canonical_baseline: Baseline,
    #[serde(default)]
    pub order_independently_verified: bool,
    #[serde(default)]
    pub identification_batch_wall_seconds: Option<f64>,
}
pub fn rank(rows: impl IntoIterator<Item = u32>) -> u32 {
    let mut basis = BTreeMap::new();
    for mut a in rows {
        while a != 0 {
            let k = a.ilog2();
            if let Some(&b) = basis.get(&k) {
                a ^= b;
            } else {
                basis.insert(k, a);
                break;
            }
        }
    }
    basis.len() as u32
}
pub fn coefficient_degree(a: u32, f: &Field) -> u32 {
    let mut c = f.mul(a, a);
    let mut degree = 1;
    while c != a {
        c = f.mul(c, c);
        degree += 1;
    }
    degree
}
pub fn canonical_baseline(b: u32, a: u32, spec: &Spec, f: &Field) -> Result<Baseline> {
    let root = f.power(b, 1 << (f.degree - 1));
    let mut orbit = Vec::new();
    let mut c = root;
    for _ in 0..spec.relative_degree {
        orbit.push(c);
        c = f.power(c, 1 << spec.base_degree);
    }
    ensure!(c == root, "Frobenius orbit did not close");
    let trace = orbit.iter().fold(0, |a, c| a ^ c);
    let s = rank(orbit.iter().copied());
    let m = rank(orbit.iter().map(|c| c | (1 << f.degree)));
    Ok(Baseline { augmented_frobenius_rank: m, coefficient_rank: s,
        formal_canonical_ghs_genus: (1 << (m - 1)) - (1 << (m - s)) + 1,
        canonical_frobenius_lift_exists: f.trace[a as usize] == 0 || trace == 0,
        scope: "Canonical split-pole formula only; formal genus does not certify descent; no cover or full gGHS exclusion".into() })
}
pub fn find_sources(
    spec: &Spec,
    wanted: &BTreeSet<i64>,
    cache: &FieldCache,
) -> Result<BTreeMap<i64, Source>> {
    spec.validate()?;
    if wanted.is_empty() {
        return Ok(BTreeMap::new());
    }
    let f = cache.get(spec.base_degree * spec.relative_degree)?;
    let mut values = vec![0; f.size as usize];
    for x in 1..f.size {
        let mut z = f.inv(f.mul(x, x));
        let mut mask = 0;
        for i in 0..f.degree {
            mask |= f.trace[z as usize] << i;
            z = f.mul(z, 2);
        }
        values[mask as usize] += 1 - 2 * f.trace[x as usize] as i64;
    }
    walsh(&mut values);
    let twist = f.trace.iter().position(|&t| t == 1).unwrap() as u32;
    let mut found: BTreeMap<i64, Source> = BTreeMap::new();
    for b in 1..f.size {
        let trace = -values[b as usize];
        for (t, a) in [(trace, 0), (-trace, twist)] {
            if !wanted.contains(&t) {
                continue;
            }
            let degree = coefficient_degree(b, &f);
            if found
                .get(&t)
                .is_some_and(|old| old.b_absolute_degree >= degree)
            {
                continue;
            }
            found.insert(
                t,
                Source {
                    equation: "y^2+x*y=x^3+a*x^2+b".into(),
                    absolute_degree: f.degree,
                    modulus: f.modulus,
                    a,
                    b,
                    elliptic_trace: t,
                    order: (f.size as i64 + 1 - t) as u64,
                    b_absolute_degree: degree,
                    canonical_baseline: canonical_baseline(b, a, spec, &f)?,
                    order_independently_verified: false,
                    identification_batch_wall_seconds: None,
                },
            );
        }
        if found.len() == wanted.len() && found.values().all(|s| s.b_absolute_degree == f.degree) {
            break;
        }
    }
    ensure!(
        found.keys().copied().collect::<BTreeSet<_>>() == *wanted,
        "no elliptic model for a candidate trace"
    );
    Ok(found)
}
