//! Affine-orbit enumeration and exact Walsh character-sum filtering.

use crate::field::{affine, decode, encode, irreducible, walsh, Field, FieldCache};
use crate::identifier;
use anyhow::{ensure, Context, Result};
use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;
use std::time::Instant;

pub const ENGINE: &str = "binary-ordinary-1-plus-N-rust-v1";
pub const SCOPE: &str = "Ordinary binary hyperelliptic w^2+w=A*x+c+R/H with pole pattern 1+N. Exhaustive only within this model family modulo affine x changes. Necessity for genus-N covers assumes ordinary E and simple Res(E); simplicity, explicit maps and subgroup transfer are not checked.";

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
#[serde(deny_unknown_fields)]
pub struct Spec {
    pub base_degree: u32,
    pub relative_degree: u32,
}
impl Spec {
    pub fn validate(&self) -> Result<()> {
        let (d, n) = (self.base_degree, self.relative_degree);
        ensure!((1..=4).contains(&d), "base_degree must be in 1..=4");
        ensure!(
            n >= 3 && n % 2 == 1,
            "relative_degree must be odd and at least 3"
        );
        let width = if d == 1 {
            Some(n)
        } else {
            n.checked_add(1).and_then(|v| d.checked_mul(v))
        };
        ensure!(
            width.is_some_and(|w| w <= 20),
            "Walsh width must be at most 20 bits"
        );
        Ok(())
    }
    pub fn q(&self) -> u32 {
        1 << self.base_degree
    }
    pub fn size(&self) -> u32 {
        1 << (self.base_degree * self.relative_degree)
    }
    pub fn width(&self) -> u32 {
        if self.base_degree == 1 {
            self.relative_degree
        } else {
            self.base_degree * (self.relative_degree + 1)
        }
    }
    pub fn models_per_job(&self) -> u64 {
        2 * (self.q() - 1) as u64 * (self.size() - 1) as u64
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Config {
    pub schema_version: u32,
    pub searches: Vec<Spec>,
}
impl Config {
    pub fn validate(&mut self) -> Result<()> {
        ensure!(
            self.schema_version == 1 && !self.searches.is_empty(),
            "config needs schema_version=1 and nonempty searches"
        );
        for s in &self.searches {
            s.validate()?;
        }
        self.searches.sort();
        ensure!(
            self.searches.windows(2).all(|w| w[0] != w[1]),
            "duplicate search parameters"
        );
        Ok(())
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Job {
    pub engine: String,
    #[serde(flatten)]
    pub spec: Spec,
    #[serde(rename = "H")]
    pub h: Vec<u32>,
    pub orbit_size: usize,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PlannedJob {
    pub job_id: String,
    pub params: Job,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PlannedSearch {
    #[serde(flatten)]
    pub spec: Spec,
    pub q: u32,
    pub genus: u32,
    pub source_field_size: u32,
    pub irreducible_denominators: usize,
    pub denominator_representatives: usize,
    pub orbit_sizes: BTreeSet<usize>,
    pub normalized_models: u64,
    pub walsh_entries: usize,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Plan {
    pub engine: String,
    pub config: Config,
    pub scope: String,
    pub searches: Vec<PlannedSearch>,
    pub total_jobs: usize,
    pub normalized_models: u64,
    pub normalization: String,
    pub rho_is_acceptance_gate: bool,
}

pub type DenominatorOrbit = (Vec<u32>, usize);
pub fn denominators(spec: &Spec, f: &Field) -> Result<(Vec<DenominatorOrbit>, usize)> {
    spec.validate()?;
    let (d, n) = (spec.base_degree, spec.relative_degree);
    let mut seen = BTreeSet::new();
    let mut reps = Vec::new();
    let mut count = 0;
    for value in 1..spec.size() {
        let encoded = value | spec.size();
        if seen.contains(&encoded) {
            continue;
        }
        let mut h = decode(value, n, d);
        h.push(1);
        if !irreducible(&h, f) {
            continue;
        }
        let mut orbit = BTreeSet::new();
        for a in 1..f.size {
            for b in 0..f.size {
                orbit.insert(encode(&affine(&h, a, b, f), d));
            }
        }
        ensure!(
            orbit.first() == Some(&encoded),
            "affine enumeration missed orbit minimum"
        );
        count += orbit.len();
        reps.push((h, orbit.len()));
        seen.extend(orbit);
    }
    Ok((reps, count))
}

pub fn make_plan(mut config: Config, cache: &FieldCache) -> Result<(Plan, Vec<PlannedJob>)> {
    config.validate()?;
    let mut searches = Vec::new();
    let mut jobs = Vec::new();
    for spec in &config.searches {
        let base = cache.get(spec.base_degree)?;
        let (reps, count) = denominators(spec, &base)?;
        searches.push(PlannedSearch {
            spec: spec.clone(),
            q: spec.q(),
            genus: spec.relative_degree,
            source_field_size: spec.size(),
            irreducible_denominators: count,
            denominator_representatives: reps.len(),
            orbit_sizes: reps.iter().map(|(_, s)| *s).collect(),
            normalized_models: spec.models_per_job() * reps.len() as u64,
            walsh_entries: 1 << spec.width(),
        });
        for (h, orbit_size) in reps {
            let params = Job {
                engine: ENGINE.into(),
                spec: spec.clone(),
                h,
                orbit_size,
            };
            jobs.push(PlannedJob {
                job_id: identifier(&params)?,
                params,
            });
        }
    }
    let plan = Plan {
        engine: ENGINE.into(),
        config,
        scope: SCOPE.into(),
        total_jobs: jobs.len(),
        normalized_models: searches.iter().map(|s| s.normalized_models).sum(),
        searches,
        normalization: "H affine orbits only; stabilizers can duplicate isomorphic models".into(),
        rho_is_acceptance_gate: false,
    };
    Ok((plan, jobs))
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct Model {
    pub base_degree: u32,
    pub relative_degree: u32,
    pub genus: u32,
    #[serde(rename = "H")]
    pub h: Vec<u32>,
    #[serde(rename = "R")]
    pub r: Vec<u32>,
    #[serde(rename = "A")]
    pub a: u32,
    pub c: u32,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Candidate {
    #[serde(alias = "candidate_id")]
    pub spectral_model_id: String,
    #[serde(flatten)]
    pub model: Model,
    #[serde(rename = "H_encoding")]
    pub h_encoding: u32,
    #[serde(rename = "R_encoding")]
    pub r_encoding: u32,
    pub elliptic_trace: i64,
    pub source_order: u64,
    pub point_counts: Vec<u64>,
    pub direct_counts_checked: bool,
    pub field_moduli: Vec<u32>,
    pub base_embeddings: Vec<Vec<u32>>,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct JobResult {
    pub normalized_models: u64,
    pub survivors_by_extension_degree: Vec<u64>,
    #[serde(default)]
    pub candidates: Vec<Candidate>,
    pub wall_seconds: f64,
}

pub fn direct_count(model: &Model, f: &Field, embed: &[u32]) -> u64 {
    let h: Vec<_> = model.h.iter().map(|&c| embed[c as usize]).collect();
    let r: Vec<_> = model.r.iter().map(|&c| embed[c as usize]).collect();
    let mut count = 1;
    for x in 0..f.size {
        let denominator = f.evaluate(&h, x);
        if denominator == 0 {
            count += 1;
        } else {
            let v = f.mul(embed[model.a as usize], x)
                ^ embed[model.c as usize]
                ^ f.mul(f.evaluate(&r, x), f.inv(denominator));
            count += 2 * (1 - f.trace[v as usize]) as u64;
        }
    }
    count
}

fn histogram(job: &Job, f: &Field, embed: &[u32], e: u32) -> Result<Vec<i64>> {
    let (d, n) = (job.spec.base_degree, job.spec.relative_degree);
    let h: Vec<_> = job.h.iter().map(|&c| embed[c as usize]).collect();
    let mut values = vec![0; 1 << job.spec.width()];
    let mut poles = 0;
    for x in 0..f.size {
        let den = f.evaluate(&h, x);
        if den == 0 {
            poles += 1;
            continue;
        }
        let mut z = f.inv(den);
        let mut mask = 0;
        for j in 0..n {
            for b in 0..d {
                mask |= f.trace[f.mul(embed[1 << b], z) as usize] << (d * j + b);
            }
            z = f.mul(z, x);
        }
        if d == 1 {
            values[mask as usize] += 1 - 2 * f.trace[x as usize] as i64;
        } else {
            for b in 0..d {
                mask |= f.trace[f.mul(embed[1 << b], x) as usize] << (d * n + b);
            }
            values[mask as usize] += 1;
        }
    }
    ensure!(poles == if e == n { n } else { 0 }, "incorrect pole orbit");
    Ok(values)
}

pub fn search_job(job: &Job, cache: &FieldCache) -> Result<JobResult> {
    job.spec.validate()?;
    let began = Instant::now();
    let s = &job.spec;
    let (d, n) = (s.base_degree, s.relative_degree);
    let base = cache.get(d)?;
    ensure!(
        job.h.len() == n as usize + 1
            && job.h.last() == Some(&1)
            && job.h.iter().all(|&c| c < s.q())
            && irreducible(&job.h, &base),
        "invalid job denominator"
    );
    let mut alive = Vec::new();
    for a in 1..s.q() {
        for r in 1..s.size() {
            alive.push(if d == 1 { r } else { r | (a << (d * n)) });
        }
    }
    let mut survival = vec![0; n as usize];
    let mut spectrum = Vec::new();
    for e in 1..=n {
        let f = cache.get(d * e)?;
        let embed = f.embedding(&base)?;
        spectrum = histogram(job, &f, &embed, e)?;
        walsh(&mut spectrum);
        if e < n {
            alive.retain(|&r| spectrum[r as usize] == 0);
        }
        survival[(e - 1) as usize] = 2 * alive.len() as u64;
        if alive.is_empty() {
            break;
        }
    }
    let twist = base
        .trace
        .iter()
        .position(|&v| v == 1)
        .context("no trace-one constant")? as u32;
    let mut candidates = Vec::new();
    for parameter in alive {
        ensure!(
            spectrum[parameter as usize] % n as i64 == 0,
            "nonintegral elliptic trace"
        );
        let t = -spectrum[parameter as usize] / n as i64;
        if t & 1 == 0 || t * t > 4 * s.size() as i64 {
            continue;
        }
        let numerator = parameter & (s.size() - 1);
        let leading = if d == 1 { 1 } else { parameter >> (d * n) };
        for c in [0, twist] {
            let trace = if c == 0 { t } else { -t };
            let model = Model {
                base_degree: d,
                relative_degree: n,
                genus: n,
                h: job.h.clone(),
                r: decode(numerator, n, d),
                a: leading,
                c,
            };
            let mut point_counts = Vec::new();
            let mut moduli = Vec::new();
            let mut embeddings = Vec::new();
            for e in 1..=n {
                let f = cache.get(d * e)?;
                let embed = f.embedding(&base)?;
                let expected = f.size as i64 + 1 - if e == n { n as i64 * trace } else { 0 };
                ensure!(
                    expected >= 0 && direct_count(&model, &f, &embed) == expected as u64,
                    "Walsh and direct counts disagree"
                );
                point_counts.push(expected as u64);
                moduli.push(f.modulus);
                embeddings.push(embed);
            }
            candidates.push(Candidate {
                spectral_model_id: identifier(&model)?,
                model,
                h_encoding: encode(&job.h, d),
                r_encoding: numerator,
                elliptic_trace: trace,
                source_order: (s.size() as i64 + 1 - trace) as u64,
                point_counts,
                direct_counts_checked: true,
                field_moduli: moduli,
                base_embeddings: embeddings,
            });
        }
    }
    Ok(JobResult {
        normalized_models: s.models_per_job(),
        survivors_by_extension_degree: survival,
        candidates,
        wall_seconds: began.elapsed().as_secs_f64(),
    })
}

pub fn subfield_config(absolute_degree: u32) -> Result<serde_json::Value> {
    ensure!(
        absolute_degree > 0 && absolute_degree <= 1_000_000,
        "absolute_degree must be in 1..=1000000"
    );
    let mut accepted = Vec::new();
    let mut excluded = Vec::new();
    for d in 1..=absolute_degree {
        if !absolute_degree.is_multiple_of(d) {
            continue;
        }
        let spec = Spec {
            base_degree: d,
            relative_degree: absolute_degree / d,
        };
        match spec.validate() {
            Ok(()) => accepted.push(spec),
            Err(e) => excluded.push(serde_json::json!({"base_degree":d,"relative_degree":absolute_degree/d,"reason":e.to_string()})),
        }
    }
    Ok(
        serde_json::json!({"absolute_degree":absolute_degree,"config":{"schema_version":1,"searches":accepted},
        "excluded_divisors":excluded,"scope":"All divisors reported; only supported choices scheduled"}),
    )
}

pub fn proper_subfield_traces(degree: u32) -> BTreeSet<i64> {
    let mut traces = BTreeSet::new();
    for d in 1..degree {
        if !degree.is_multiple_of(d) {
            continue;
        }
        let q = 1_i64 << d;
        let mut bound = 0_i64;
        while (bound + 1) * (bound + 1) <= 4 * q {
            bound += 1;
        }
        for t in -bound..=bound {
            if t & 1 == 0 {
                continue;
            }
            let (mut previous, mut current) = (2, t);
            for _ in 1..degree / d {
                (previous, current) = (current, t * current - q * previous);
            }
            traces.insert(current);
            traces.insert(-current);
        }
    }
    traces
}
