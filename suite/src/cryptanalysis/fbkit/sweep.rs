//! The sweep driver: expand a manifest into `(recipe, m)` cells, measure them
//! in parallel with deterministic per-cell seeds, capture per-cell failures,
//! and derive the `slope` of each `(family, m)` across the swept dimensions.
//!
//! Cells are measured on a rayon pool of `jobs` threads; finished records
//! reach the caller's `on_cell` callback on the calling thread, in completion
//! order, so the callback needs no synchronisation.

use std::collections::{BTreeMap, BTreeSet, HashSet};
use std::panic::{catch_unwind, AssertUnwindSafe};
use std::sync::mpsc;
use std::time::{Duration, Instant};

use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

use super::families::{canonical_modifier, materialize, Curve, Reason, Recipe};
use super::identity;
use super::metrics::{measure, Group, MetricRequest, Status};
use super::registry;
use super::{CellRecord, CELL_SCHEMA, MANIFEST_SCHEMA};

/// Metric limits of a sweep (the `metrics` block of the manifest).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MetricsSpec {
    /// Group names (`construction`, `yield`, `f4`, ...).
    pub groups: Vec<String>,
    /// Targets per class.
    pub targets: u32,
    /// Exact-yield cap.
    pub exact_cap: u64,
    /// Seconds per cell per metric group.
    pub budget_seconds: u64,
    /// SAT conflict budget.
    pub conflict_budget: u64,
    /// Highest Macaulay degree.
    pub d_max: u32,
}

impl Default for MetricsSpec {
    fn default() -> Self {
        Self {
            groups: vec!["construction".into(), "yield".into()],
            targets: 8,
            exact_cap: 1 << 24,
            budget_seconds: 60,
            conflict_budget: 20_000,
            d_max: 6,
        }
    }
}

/// A cross product of families, dimensions, seeds and modifier sets.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct Matrix {
    /// Family names.
    pub families: Vec<String>,
    /// Values of each family's size parameter (`l`, `K`, ...).
    #[serde(default)]
    pub dims: Vec<u64>,
    /// Seeds (families with a `seed` parameter only); empty means one cell.
    #[serde(default)]
    pub seeds: Vec<u64>,
    /// Modifier sets; empty means one cell without modifiers.
    #[serde(default)]
    pub modifiers: Vec<BTreeMap<String, Value>>,
    /// Parameters added to every cell of the matrix.
    #[serde(default)]
    pub params: BTreeMap<String, Value>,
}

/// The frozen sweep manifest (`ic-fbkit-manifest/1`).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Manifest {
    /// `ic-fbkit-manifest/1`.
    pub schema: String,
    /// Curve description (flags of the curve group, as JSON).
    pub curve: Value,
    /// Curve ID `EC1N<n>C<tag>h<12hex>` recorded in every cell.
    #[serde(default)]
    pub curve_id: String,
    /// Lowercase alphanumeric curve tag for PS1 labels (optional).
    #[serde(default)]
    pub curve_tag: Option<String>,
    /// Summand counts.
    pub m: Vec<u32>,
    /// Explicit cells.
    #[serde(default)]
    pub cells: Vec<Recipe>,
    /// Matrix of cells.
    #[serde(default)]
    pub matrix: Option<Matrix>,
    /// Metric limits.
    #[serde(default)]
    pub metrics: MetricsSpec,
    /// Sweep seed (per-cell seeds derive from it and the cell ID).
    #[serde(default)]
    pub seed: u64,
    /// Worker threads; absent means [`default_jobs`].
    #[serde(default)]
    pub jobs: Option<usize>,
    /// `sweep_id`, set by [`Manifest::frozen`].
    #[serde(default)]
    pub sweep_id: Option<String>,
}

impl Manifest {
    /// An empty manifest for a curve.
    pub fn new(curve: Value, m: Vec<u32>) -> Self {
        Self {
            schema: MANIFEST_SCHEMA.into(),
            curve,
            curve_id: String::new(),
            curve_tag: None,
            m,
            cells: Vec::new(),
            matrix: None,
            metrics: MetricsSpec::default(),
            seed: 0,
            jobs: None,
            sweep_id: None,
        }
    }

    /// The manifest with its `sweep_id` filled in.
    pub fn frozen(mut self) -> Result<Self, String> {
        self.sweep_id = None;
        let v = serde_json::to_value(&self).map_err(|e| e.to_string())?;
        self.sweep_id = Some(identity::sweep_id(&v)?);
        Ok(self)
    }

    /// The metric request for one summand count.
    pub fn request(&self, m: u32) -> Result<MetricRequest, String> {
        let groups: BTreeSet<Group> = self
            .metrics
            .groups
            .iter()
            .map(|g| Group::parse(g))
            .collect::<Result<_, _>>()?;
        Ok(MetricRequest {
            groups,
            m,
            targets: self.metrics.targets,
            exact_cap: self.metrics.exact_cap,
            budget: Duration::from_secs(self.metrics.budget_seconds),
            conflict_budget: self.metrics.conflict_budget,
            d_max: self.metrics.d_max,
            system_modifiers: BTreeMap::new(),
        })
    }
}

/// Parse `3-6`, `3,5,8` or `4` into a list of dimensions.
pub fn parse_dims(s: &str) -> Result<Vec<u64>, String> {
    let mut out = Vec::new();
    for part in s.split(',').filter(|p| !p.trim().is_empty()) {
        let part = part.trim();
        match part.split_once('-') {
            Some((a, b)) => {
                let (a, b): (u64, u64) = (
                    a.parse().map_err(|_| format!("bad dimension `{part}`"))?,
                    b.parse().map_err(|_| format!("bad dimension `{part}`"))?,
                );
                out.extend(a..=b);
            }
            None => out.push(
                part.parse()
                    .map_err(|_| format!("bad dimension `{part}`"))?,
            ),
        }
    }
    Ok(out)
}

/// Every `(recipe, m)` of a manifest, explicit cells first, duplicates removed.
pub fn expand(manifest: &Manifest) -> Vec<(Recipe, u32)> {
    let mut recipes: Vec<Recipe> = manifest.cells.clone();
    if let Some(mx) = &manifest.matrix {
        let seeds: Vec<Option<u64>> = if mx.seeds.is_empty() {
            vec![None]
        } else {
            mx.seeds.iter().copied().map(Some).collect()
        };
        let mods: Vec<BTreeMap<String, Value>> = if mx.modifiers.is_empty() {
            vec![BTreeMap::new()]
        } else {
            mx.modifiers.clone()
        };
        for fam in &mx.families {
            let info = registry::find(fam);
            let size_param = info.and_then(|f| f.size_param);
            let has_seed = info.is_some_and(|f| f.parameters.iter().any(|p| p.name == "seed"));
            let dims: Vec<Option<u64>> = match (size_param, mx.dims.is_empty()) {
                (Some(_), false) => mx.dims.iter().copied().map(Some).collect(),
                _ => vec![None],
            };
            for d in &dims {
                for s in &seeds {
                    for ms in &mods {
                        let mut r = Recipe::new(fam);
                        r.params = mx.params.clone();
                        if let (Some(p), Some(d)) = (size_param, d) {
                            r.params.insert(p.to_string(), json!(d));
                        }
                        if let (true, Some(s)) = (has_seed, s) {
                            r.params.insert("seed".into(), json!(s));
                        }
                        for (k, v) in ms {
                            let key = canonical_modifier(k).unwrap_or(k.as_str());
                            r.modifiers.insert(key.to_string(), v.clone());
                        }
                        recipes.push(r);
                    }
                }
            }
        }
    }
    let mut seen = HashSet::new();
    let mut out = Vec::new();
    for r in recipes {
        for &m in &manifest.m {
            if seen.insert((r.to_canonical_json(), m)) {
                out.push((r.clone(), m));
            }
        }
    }
    out
}

fn scalar_slug(v: &Value) -> String {
    match v {
        Value::Array(a) => a.iter().map(scalar_slug).collect::<Vec<_>>().join("-"),
        Value::String(s) => s.trim_start_matches("0x").to_string(),
        other => other.to_string(),
    }
}

/// `<family>-<slug>-m<m>-l<l>-<8hex>` where the digest covers the canonical
/// recipe and `m`.
pub fn cell_id(recipe: &Recipe, m: u32) -> String {
    let size_name = registry::find(&recipe.family).and_then(|f| f.size_param);
    let mut parts: Vec<String> = Vec::new();
    for (k, v) in &recipe.params {
        if Some(k.as_str()) == size_name {
            continue;
        }
        parts.push(format!("{k}{}", scalar_slug(v)));
    }
    for (k, v) in &recipe.modifiers {
        parts.push(format!("{k}{}", scalar_slug(v)));
    }
    let l = recipe.size().unwrap_or(0) as u32;
    let rec = json!({"recipe": recipe.to_value(), "m": m});
    identity::cell_id(&recipe.family, &parts.join("-"), m, l, &rec)
        .unwrap_or_else(|_| format!("{}-m{m}-l{l}", recipe.family))
}

/// Worker threads: all cores, capped at 8 when the 1-minute load average
/// exceeds half the cores.
pub fn default_jobs() -> usize {
    let n = std::thread::available_parallelism().map_or(1, |n| n.get());
    let load = std::fs::read_to_string("/proc/loadavg").ok().and_then(|s| {
        s.split_whitespace()
            .next()
            .and_then(|x| x.parse::<f64>().ok())
    });
    match load {
        Some(l) if l > n as f64 / 2.0 => n.min(8),
        _ => n,
    }
}

/// `sigma = dD*/dlog2|V|` of one `(family, m)` across the swept dimensions.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Slope {
    /// Family name.
    pub family: String,
    /// Summand count.
    pub m: u32,
    /// Least-squares slope of the mean solving degree against `dim V`.
    pub sigma: Option<f64>,
    /// Distinct dimensions with a measured degree.
    pub dims: usize,
    /// Why `sigma` is null.
    pub reason: Option<String>,
}

/// The mean random-class (else planted) Macaulay solving degree of a cell.
fn dstar(rec: &CellRecord) -> Option<f64> {
    let f4 = rec.metrics.get("f4")?;
    ["random", "planted"]
        .iter()
        .find_map(|c| f4.get(*c)?.get("solving_degree_mean")?.as_f64())
}

/// Compute the slope of every `(family, m)` from finished records.
pub fn compute_slopes(cells: &[CellRecord]) -> Vec<Slope> {
    let mut by: BTreeMap<(String, u32), BTreeMap<u64, Vec<f64>>> = BTreeMap::new();
    for c in cells {
        let key = (c.family.clone(), c.m);
        let entry = by.entry(key).or_default();
        let dim = c.metrics["construction"]["dimension"].as_u64();
        if let (Some(d), Some(x)) = (dim, dstar(c)) {
            entry.entry(d).or_default().push(x);
        }
    }
    by.into_iter()
        .map(|((family, m), pts)| {
            let xs: Vec<(f64, f64)> = pts
                .iter()
                .map(|(d, v)| (*d as f64, v.iter().sum::<f64>() / v.len() as f64))
                .collect();
            let n = xs.len() as f64;
            if xs.len() < 2 {
                return Slope {
                    family,
                    m,
                    sigma: None,
                    dims: xs.len(),
                    reason: Some("fewer than two dimensions with a measured degree".into()),
                };
            }
            let (mx, my) = (
                xs.iter().map(|p| p.0).sum::<f64>() / n,
                xs.iter().map(|p| p.1).sum::<f64>() / n,
            );
            let sxx: f64 = xs.iter().map(|p| (p.0 - mx).powi(2)).sum();
            let sxy: f64 = xs.iter().map(|p| (p.0 - mx) * (p.1 - my)).sum();
            Slope {
                family,
                m,
                sigma: Some(sxy / sxx),
                dims: xs.len(),
                reason: None,
            }
        })
        .collect()
}

/// What a sweep did.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct SweepSummary {
    /// Cells in the expanded manifest.
    pub total: usize,
    /// Cells skipped by the resume predicate.
    pub skipped: usize,
    /// Cells measured in this run.
    pub run: usize,
    /// Count per status string.
    pub by_status: BTreeMap<String, usize>,
    /// Worker threads used.
    pub jobs: usize,
    /// Wall seconds.
    pub elapsed_seconds: f64,
    /// Slopes of the cells measured in this run.
    pub slopes: Vec<Slope>,
}

fn panic_text(p: Box<dyn std::any::Any + Send>) -> String {
    p.downcast_ref::<&str>()
        .map(|s| (*s).to_string())
        .or_else(|| p.downcast_ref::<String>().cloned())
        .unwrap_or_else(|| "panic".into())
}

fn fnv(s: &str) -> u64 {
    s.bytes().fold(0xcbf2_9ce4_8422_2325u64, |h, b| {
        (h ^ u64::from(b)).wrapping_mul(0x0100_0000_01b3)
    })
}

fn measure_cell(manifest: &Manifest, curve: &Curve<'_>, recipe: &Recipe, m: u32) -> CellRecord {
    let started = Instant::now();
    let id = cell_id(recipe, m);
    let seed = manifest.seed ^ fnv(&id).rotate_left(17);
    let mut rec = CellRecord {
        schema: CELL_SCHEMA.into(),
        cell_id: id,
        curve_id: manifest.curve_id.clone(),
        family: recipe.family.clone(),
        recipe: recipe.to_value(),
        m,
        status: Status::Complete.as_str().into(),
        reason: None,
        metrics: json!({}),
        ps1_label: None,
        point_set_sha256: None,
        factor_base_sha256: None,
        elapsed_seconds: 0.0,
    };
    let outcome = catch_unwind(AssertUnwindSafe(|| {
        let mat = materialize(recipe, curve, seed)?;
        let mut req = manifest.request(m).map_err(Reason::Error)?;
        req.system_modifiers = recipe.system_modifiers();
        Ok::<_, Reason>(measure(curve, &mat, &req, seed))
    }));
    match outcome {
        Ok(Ok((metrics, status, reason))) => {
            rec.status = status.as_str().into();
            rec.reason = reason;
            rec.point_set_sha256 = metrics["construction"]["point_set_sha256"]
                .as_str()
                .map(str::to_string);
            rec.metrics = metrics;
        }
        Ok(Err(Reason::NotApplicable(why))) => {
            rec.status = Status::NotApplicable.as_str().into();
            rec.reason = Some(why);
        }
        Ok(Err(Reason::Error(why))) => {
            rec.status = Status::Error.as_str().into();
            rec.reason = Some(why);
        }
        Err(p) => {
            rec.status = Status::Error.as_str().into();
            rec.reason = Some(format!("panic: {}", panic_text(p)));
        }
    }
    rec.factor_base_sha256 = identity::sha256_hex(&json!({
        "curve_id": manifest.curve_id,
        "recipe": recipe.to_value(),
    }))
    .ok();
    if let (Some(tag), Some(n), Some(fb), Some(sha)) = (
        manifest.curve_tag.as_deref(),
        curve.degree(),
        rec.metrics["construction"]["fb_points"].as_u64(),
        rec.factor_base_sha256.as_deref(),
    ) {
        let solver = if rec.metrics.get("f4").is_some() {
            "f4"
        } else {
            "sumset"
        };
        rec.ps1_label = identity::ps1_label(
            u64::from(n),
            tag,
            fb,
            u64::from(m),
            solver,
            sha,
            &json!({"m": m, "solver": solver, "targets": manifest.metrics.targets}),
        )
        .ok();
    }
    rec.elapsed_seconds = started.elapsed().as_secs_f64();
    rec
}

/// Run a sweep. `skip` is asked for every cell ID before it is measured;
/// `on_cell` receives each finished record on the calling thread.
pub fn run(
    manifest: &Manifest,
    curve: &Curve<'_>,
    on_cell: &mut dyn FnMut(CellRecord),
    skip: &dyn Fn(&str) -> bool,
    progress: &dyn Fn(&str),
) -> SweepSummary {
    let started = Instant::now();
    let all = expand(manifest);
    let total = all.len();
    let todo: Vec<(Recipe, u32)> = all
        .into_iter()
        .filter(|(r, m)| !skip(&cell_id(r, *m)))
        .collect();
    let jobs = manifest.jobs.unwrap_or_else(default_jobs).max(1);
    let mut summary = SweepSummary {
        total,
        skipped: total - todo.len(),
        jobs,
        ..SweepSummary::default()
    };
    progress(&format!(
        "fbkit sweep: {} cells ({} skipped), {jobs} jobs",
        todo.len(),
        summary.skipped
    ));
    let mut finished: Vec<CellRecord> = Vec::new();
    let pool = rayon::ThreadPoolBuilder::new().num_threads(jobs).build();
    let (tx, rx) = mpsc::channel::<CellRecord>();
    match pool {
        Ok(pool) => std::thread::scope(|scope| {
            scope.spawn(move || {
                pool.install(|| {
                    todo.par_iter().for_each_with(tx, |tx, (r, m)| {
                        let rec = measure_cell(manifest, curve, r, *m);
                        let _ = tx.send(rec);
                    });
                });
            });
            let mut done = 0;
            for rec in rx {
                done += 1;
                progress(&format!(
                    "[{done}/{}] {} {}",
                    total - summary.skipped,
                    rec.cell_id,
                    rec.status
                ));
                *summary.by_status.entry(rec.status.clone()).or_default() += 1;
                finished.push(rec.clone());
                on_cell(rec);
            }
        }),
        Err(e) => progress(&format!("fbkit sweep: cannot start the thread pool: {e}")),
    }
    summary.run = finished.len();
    summary.slopes = compute_slopes(&finished);
    summary.elapsed_seconds = started.elapsed().as_secs_f64();
    summary
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::koblitz_index_calculus::KoblitzCurve;
    use std::sync::Mutex;

    fn manifest() -> Manifest {
        let mut m = Manifest::new(json!({"kind": "koblitz", "n": 11}), vec![2, 3]);
        m.matrix = Some(Matrix {
            families: vec!["coordinate".into(), "random".into()],
            dims: vec![3, 4],
            seeds: vec![1],
            ..Matrix::default()
        });
        m.metrics.groups = vec!["construction".into(), "yield".into()];
        m.metrics.targets = 4;
        m.jobs = Some(2);
        m
    }

    #[test]
    fn expansion_and_ids() {
        let m = manifest();
        let cells = expand(&m);
        assert_eq!(cells.len(), 2 * 2 * 2);
        let ids: HashSet<String> = cells.iter().map(|(r, m)| cell_id(r, *m)).collect();
        assert_eq!(ids.len(), cells.len());
        let id = cell_id(&cells[0].0, 2);
        assert!(
            id.starts_with("coordinate-") && id.contains("-m2-l3-"),
            "{id}"
        );
        assert_eq!(parse_dims("3-5,8").expect("dims"), vec![3, 4, 5, 8]);
        assert!(m.frozen().expect("freeze").sweep_id.is_some());
    }

    #[test]
    fn sweep_runs_resumes_and_captures_errors() {
        let kc = [1u8, 0]
            .into_iter()
            .find_map(|a| KoblitzCurve::new(a, 11))
            .expect("curve");
        let cv = Curve::Koblitz(&kc);
        let mut m = manifest();
        m.cells
            .push(Recipe::new("divisor").with("indices", json!([99])));
        m.cells.push(Recipe::new("coordinate").with("l", json!(40)));
        let got = Mutex::new(Vec::new());
        let mut sink = |c: CellRecord| got.lock().expect("lock").push(c);
        let s = run(&m, &cv, &mut sink, &|_| false, &|_| {});
        let cells = got.into_inner().expect("lock");
        assert_eq!(s.run, cells.len());
        assert_eq!(s.total, 8 + 4);
        assert!(cells.iter().any(|c| c.status == "complete"));
        assert!(cells
            .iter()
            .any(|c| c.status == "not_applicable" || c.status == "error"));
        let first = cell_id(&expand(&m)[0].0, 2);
        let mut n2 = 0;
        let s2 = run(&m, &cv, &mut |_| n2 += 1, &|id| id == first, &|_| {});
        assert_eq!(s2.skipped, 1);
        assert_eq!(n2, s.total - 1);
    }

    #[test]
    fn slopes_need_two_dimensions() {
        let rec = |dim: u64, d: f64| CellRecord {
            schema: CELL_SCHEMA.into(),
            cell_id: format!("x{dim}"),
            curve_id: String::new(),
            family: "coordinate".into(),
            recipe: json!({}),
            m: 2,
            status: "complete".into(),
            reason: None,
            metrics: json!({"construction": {"dimension": dim}, "f4": {"random": {"solving_degree_mean": d}}}),
            ps1_label: None,
            point_set_sha256: None,
            factor_base_sha256: None,
            elapsed_seconds: 0.0,
        };
        let one = compute_slopes(&[rec(3, 3.0)]);
        assert_eq!(one[0].sigma, None);
        let two = compute_slopes(&[rec(3, 3.0), rec(5, 4.0)]);
        assert_eq!(two[0].sigma, Some(0.5));
    }
}
