//! `ic fbkit`: the factor-base toolkit command line.
//!
//! Wires `cryptanalysis::fbkit` (registry, families, metrics, sweep, rank,
//! identity, store) into `ca-ic`. The design record is
//! `docs/ic/FBKIT_SPEC.md`, the user guide `docs/ic/FBKIT.md`.
//!
//! ```text
//! ic fbkit list
//! ic fbkit explain geometric
//! ic fbkit sweep --koblitz-degree 13 --curve-a 1 --families coordinate,geometric \
//!     --dims 3-5 --m 2,3 --metrics construction,yield,f4,sat --dir runs/k13
//! ic fbkit sweep --manifest docs/ic/sweeps/fbkit-m2-8-n7.json --dir runs/m2-8
//! ic fbkit rank --dir runs/k13 --objective solving-degree
//! ic fbkit export --dir runs/k13 --cell <cell-id>
//! ic fbkit upload --dir runs/k13 --s3 s3://bucket/prefix
//! ```
//!
//! Every number is a stage diagnostic: nothing here is an `IC1` result or a
//! speedup.

use std::collections::BTreeSet;
use std::fmt::Write as _;
use std::fs::OpenOptions;
use std::io::Write as _;
use std::panic::{catch_unwind, AssertUnwindSafe};
use std::path::{Path, PathBuf};
use std::time::Instant;

use clap::{Args, Subcommand};
use num_traits::ToPrimitive;
use rayon::prelude::*;
use serde_json::{json, Value};

use super::experiment::resources;
use super::params;
use crate::cryptanalysis::fbkit::families::{base_points_binary, materialize, Ctx, Curve, Recipe};
use crate::cryptanalysis::fbkit::identity;
use crate::cryptanalysis::fbkit::metrics::Group;
use crate::cryptanalysis::fbkit::rank::{rank, Objective, Weights};
use crate::cryptanalysis::fbkit::registry::{self, Kind};
use crate::cryptanalysis::fbkit::store::{
    archive_index_row, download, export_archive_document, upload, AwsCli, DownloadOptions,
    S3Target, Store, UploadOptions, ARCHIVE_SCHEMA,
};
use crate::cryptanalysis::fbkit::sweep::{
    compute_slopes, expand, parse_dims, run as run_sweep_driver, Manifest, Matrix,
};
use crate::cryptanalysis::fbkit::{CellRecord, MANIFEST_SCHEMA};
use crate::cryptanalysis::ic_boundary::{
    random_binary_instance, roster_prime_instance, BinaryInstance, PrimeInstance,
};
use crate::cryptanalysis::koblitz_index_calculus::{KoblitzCurve, MAX_N};

const WHAT_THIS_IS: &str = "factor-base stage diagnostics for one curve: construction, relation-yield and solver-stage measurements of named factor-base families at chosen summand counts";
const WHAT_THIS_IS_NOT: &str = "not an IC1 result and not a speedup: every number is a stage diagnostic; fb<B> counts distinct usable points before sign/Frobenius folding (effective columns are reported separately); ranking is relative within the sweep only; null means not measured";

/// Largest point count for which a sweep stores `points/<cell>.jsonl` without
/// `--points`.
const AUTO_POINTS_LIMIT: u64 = 65_536;

// ── Command line ───────────────────────────────────────────────────

/// Arguments of `ic fbkit`.
#[derive(Args, Clone)]
pub struct FbkitArgs {
    #[command(subcommand)]
    cmd: FbkitCmd,
}

/// The curve selector shared by `build` and `sweep`: exactly one of the four
/// forms (a manifest may carry it instead).
#[derive(Args, Clone, Default)]
pub struct CurveArgs {
    /// Koblitz curve K_a over GF(2^N) (N odd; N <= 62 for measured metrics). Needs --curve-a.
    #[arg(long)]
    koblitz_degree: Option<u32>,
    /// The Koblitz coefficient a (0 or 1) with --koblitz-degree.
    #[arg(long, value_parser = clap::value_parser!(u8).range(0..=1))]
    curve_a: Option<u8>,
    /// Random binary curve over GF(2^N) with a prime-order subgroup (N <= 62).
    #[arg(long)]
    char2_degree: Option<u32>,
    /// Seed of the random binary curve (default 1), with --char2-degree.
    #[arg(long)]
    curve_seed: Option<u64>,
    /// Largest cofactor of the random binary curve (default 8), with --char2-degree.
    #[arg(long)]
    max_cofactor: Option<u64>,
    /// A named profile from `ca-ic list`; inspection and construction-only, solver metrics are not applicable.
    #[arg(long = "curve")]
    curve: Option<String>,
    /// Prime-field curve of about B bits from the bench roster (only prime-abscissa applies).
    #[arg(long)]
    bits: Option<u32>,
}

/// Limits and outputs shared by `build` and `sweep`. Unset values fall back
/// to the manifest (when one is given) and then to the defaults.
#[derive(Args, Clone, Default)]
pub struct RunOpts {
    /// Metric groups: construction,yield,system,f4,sat,xl,derived (default construction for build, construction,yield for sweep).
    #[arg(long)]
    metrics: Option<String>,
    /// Targets per class for yield sampling and the solver classes (default 8).
    #[arg(long)]
    targets: Option<u32>,
    /// Sweep seed; per-cell seeds derive from it and the cell id (default 0).
    #[arg(long)]
    seed: Option<u64>,
    /// Wall seconds per cell per metric group (default 60).
    #[arg(long)]
    budget_seconds: Option<u64>,
    /// SAT conflict budget per target (default 20000).
    #[arg(long)]
    conflict_budget: Option<u64>,
    /// Highest Macaulay degree tried by the F4 group (default 6).
    #[arg(long)]
    d_max: Option<u32>,
    /// Exact yield when |F|^(m-1) does not exceed this (default 2^24).
    #[arg(long)]
    exact_cap: Option<u64>,
    /// Worker threads (default: all cores, at most 8 when the machine is loaded).
    #[arg(long)]
    jobs: Option<usize>,
    /// Run directory (default fbkit-<curve_id>-<sweep_id> in the current directory).
    #[arg(long)]
    dir: Option<PathBuf>,
    /// Store points/<cell>.jsonl for every cell (default: cells with at most 65536 points).
    #[arg(long)]
    points: bool,
}

#[derive(Subcommand, Clone)]
enum FbkitCmd {
    /// List the technique registry with prior verdicts.
    List,
    /// Show one family: definition, parameters, prior verdict, citations.
    Explain {
        /// Family name from `fbkit list`.
        family: String,
    },
    /// Build and measure one factor base (a one-cell sweep).
    Build {
        #[command(flatten)]
        curve: CurveArgs,
        /// Recipe `name[:k=v,k=v][;modifier=v]`, for example `geometric:l=4,seed=3;trace_zero=1`.
        #[arg(long)]
        family: String,
        /// Summand count, 2..=8.
        #[arg(long, default_value_t = 3)]
        m: u32,
        #[command(flatten)]
        opts: RunOpts,
    },
    /// Sweep factor-base constructions over a manifest or a family/dimension matrix.
    Sweep {
        #[command(flatten)]
        curve: CurveArgs,
        /// A JSON manifest (ic-fbkit-manifest/1; keys starting with `_` are comments). It may carry the curve selector.
        #[arg(long)]
        manifest: Option<PathBuf>,
        /// Families of the matrix, comma separated.
        #[arg(long, value_delimiter = ',')]
        families: Vec<String>,
        /// Explicit recipe `name[:k=v,k=v][;modifier=v]`; repeatable.
        #[arg(long = "cell")]
        cells: Vec<String>,
        /// Values of each family's size parameter: `3-6`, `3,5,8`.
        #[arg(long)]
        dims: Option<String>,
        /// Summand counts, 2..=8 (default 2,3).
        #[arg(long = "m", value_delimiter = ',')]
        m: Vec<u32>,
        /// Seeds for families with a seed parameter, comma separated.
        #[arg(long, value_delimiter = ',')]
        seeds: Vec<u64>,
        /// A modifier set `trace_zero=1,shift=invariant` or `none`; repeatable, each is a column of the matrix.
        #[arg(long = "modifiers")]
        modifiers: Vec<String>,
        #[command(flatten)]
        opts: RunOpts,
        /// Skip cells of an existing run directory whose status is complete, not_applicable or caps_hit (a cap is deterministic for one manifest); budget and error cells re-run.
        #[arg(long)]
        resume: bool,
        /// Ranking objective: expected-ops|solving-degree|sat-clauses|sat-conflicts|columns|composite.
        #[arg(long, default_value = "expected-ops")]
        objective: String,
    },
    /// Re-rank the cells of a run directory.
    Rank {
        /// Run directory.
        #[arg(long)]
        dir: PathBuf,
        /// expected-ops|solving-degree|sat-clauses|sat-conflicts|columns|composite.
        #[arg(long, default_value = "expected-ops")]
        objective: String,
        /// Rows of the top table.
        #[arg(long, default_value_t = 10)]
        top: usize,
        /// Composite weights `ops=1,dreg=1,clauses=0.5,conflicts=0.5,columns=0.5`.
        #[arg(long)]
        weights: Option<String>,
    },
    /// Write the ic-factor-base-archive/1 document and PS1 label of one cell.
    Export {
        /// Run directory.
        #[arg(long)]
        dir: PathBuf,
        /// Cell id (or a unique prefix).
        #[arg(long)]
        cell: String,
        /// Write the archive document to a new file (never overwrites).
        #[arg(long)]
        archive_out: Option<PathBuf>,
    },
    /// Upload a run directory to S3 through the aws CLI.
    Upload {
        /// Run directory.
        #[arg(long)]
        dir: PathBuf,
        /// s3://bucket/prefix (else FBKIT_S3_URI, else IC_ARCHIVE_S3_URI).
        #[arg(long)]
        s3: Option<String>,
        /// List what would be uploaded without transferring.
        #[arg(long)]
        dry_run: bool,
        /// Fail (exit 1) instead of skipping when there is no destination or no credentials.
        #[arg(long)]
        require: bool,
    },
    /// Download and verify a run directory from S3.
    Download {
        /// s3://bucket/prefix/fbkit/<curve_id>/<sweep_id> (not needed with --verify-only).
        #[arg(long)]
        s3: Option<String>,
        /// A new or empty directory (with --verify-only: the existing run directory).
        #[arg(long)]
        dir: PathBuf,
        /// Only re-verify an existing directory against its inventory.json.
        #[arg(long)]
        verify_only: bool,
    },
}

/// Run `ic fbkit`. Progress goes to stderr unless `json_only`.
pub fn run(args: FbkitArgs, json_only: bool) -> Result<Value, String> {
    match args.cmd {
        FbkitCmd::List => list(),
        FbkitCmd::Explain { family } => explain(&family),
        FbkitCmd::Build {
            curve,
            family,
            m,
            opts,
        } => {
            let recipe = Recipe::parse(&family)?;
            let mut manifest = Manifest::new(Value::Null, vec![m]);
            manifest.cells.push(recipe);
            run_sweep(
                "fbkit-build",
                &curve,
                manifest,
                false,
                "construction",
                &opts,
                false,
                "expected-ops",
                json_only,
            )
        }
        FbkitCmd::Sweep {
            curve,
            manifest,
            families,
            cells,
            dims,
            m,
            seeds,
            modifiers,
            opts,
            resume,
            objective,
        } => {
            let (manifest, from_file) = match manifest {
                Some(path) => {
                    if !families.is_empty()
                        || !cells.is_empty()
                        || dims.is_some()
                        || !seeds.is_empty()
                        || !modifiers.is_empty()
                    {
                        return Err("--manifest already lists the cells: drop --families, --cell, --dims, --seeds and --modifiers (limits such as --seed, --jobs and --m may override)".into());
                    }
                    (
                        load_manifest(&path, if m.is_empty() { None } else { Some(&m) })?,
                        true,
                    )
                }
                None => (
                    manifest_from_flags(
                        &families,
                        &cells,
                        dims.as_deref(),
                        &m,
                        &seeds,
                        &modifiers,
                    )?,
                    false,
                ),
            };
            let mut manifest = manifest;
            if from_file && !m.is_empty() {
                manifest.m = m;
            }
            run_sweep(
                "fbkit-sweep",
                &curve,
                manifest,
                from_file,
                "construction,yield",
                &opts,
                resume,
                &objective,
                json_only,
            )
        }
        FbkitCmd::Rank {
            dir,
            objective,
            top,
            weights,
        } => rerank(&dir, &objective, top, weights.as_deref()),
        FbkitCmd::Export {
            dir,
            cell,
            archive_out,
        } => export(&dir, &cell, archive_out.as_deref()),
        FbkitCmd::Upload {
            dir,
            s3,
            dry_run,
            require,
        } => upload_cmd(&dir, s3.as_deref(), dry_run, require),
        FbkitCmd::Download {
            s3,
            dir,
            verify_only,
        } => download_cmd(s3.as_deref(), &dir, verify_only),
    }
}

// ── Report plumbing ────────────────────────────────────────────────

fn report(op: &str, status: &str, config: Value, started: Instant, markdown: String) -> Value {
    json!({
        "schema_version": 1,
        "operation": op,
        "status": status,
        "what_this_is": WHAT_THIS_IS,
        "what_this_is_not": WHAT_THIS_IS_NOT,
        "config": config,
        "elapsed_seconds": started.elapsed().as_secs_f64(),
        "resources": resources(),
        "markdown": markdown,
    })
}

fn put(v: &mut Value, key: &str, val: Value) {
    if let Some(o) = v.as_object_mut() {
        o.insert(key.to_string(), val);
    }
}

fn cellv(v: &Value) -> String {
    match v {
        Value::Null => "null".into(),
        Value::String(s) => s.clone(),
        Value::Number(n) => match (n.as_u64(), n.as_f64()) {
            (Some(i), _) => i.to_string(),
            (None, Some(f)) if f != 0.0 && (f.abs() >= 1e6 || f.abs() < 1e-3) => {
                format!("{f:.3e}")
            }
            (None, Some(f)) => format!("{f:.3}"),
            _ => n.to_string(),
        },
        other => other.to_string(),
    }
}

// ── list and explain ───────────────────────────────────────────────

fn list() -> Result<Value, String> {
    let started = Instant::now();
    let reg = registry::to_json();
    let mut md = String::new();
    let _ = writeln!(
        md,
        "| family | regime | kind | status | prior verdict |\n|---|---|---|---|---|"
    );
    for f in registry::families() {
        let _ = writeln!(
            md,
            "| `{}` | {} | {} | {} | {} |",
            f.name,
            f.regime.as_str(),
            f.kind.as_str(),
            f.status.as_str(),
            f.prior_verdict.replace('|', "/")
        );
    }
    let mut r = report("fbkit-list", "complete", json!({}), started, md);
    put(&mut r, "count", json!(registry::families().len()));
    put(&mut r, "families", reg["families"].clone());
    Ok(r)
}

fn explain(name: &str) -> Result<Value, String> {
    let started = Instant::now();
    let Some(f) = registry::find(name) else {
        let near: Vec<&str> = registry::families()
            .iter()
            .map(|f| f.name)
            .filter(|n| n.contains(name) || name.contains(n))
            .collect();
        return Err(format!(
            "unknown family `{name}`{}; try `ca-ic fbkit list`",
            if near.is_empty() {
                String::new()
            } else {
                format!(" (did you mean {}?)", near.join(", "))
            }
        ));
    };
    let mut md = String::new();
    let _ = writeln!(
        md,
        "# {}\n\n{}\n\n- regime: {}\n- kind: {}\n- status: {}\n- size parameter: {}\n- modifiers allowed: {}\n- prior verdict: {}",
        f.name,
        f.definition,
        f.regime.as_str(),
        f.kind.as_str(),
        f.status.as_str(),
        f.size_param.unwrap_or("none"),
        f.modifiers_allowed,
        f.prior_verdict
    );
    if !f.parameters.is_empty() {
        let _ = writeln!(
            md,
            "\n| parameter | type | default | range |\n|---|---|---|---|"
        );
        for p in &f.parameters {
            let _ = writeln!(
                md,
                "| `{}` | {} | {} | {} |",
                p.name, p.ty, p.default, p.range
            );
        }
    }
    let _ = writeln!(md, "\nCitations:");
    for c in &f.citations {
        let _ = writeln!(md, "- {c}");
    }
    let mut r = report(
        "fbkit-explain",
        "complete",
        json!({"family": name}),
        started,
        md,
    );
    put(
        &mut r,
        "family",
        serde_json::to_value(f).map_err(|e| e.to_string())?,
    );
    Ok(r)
}

// ── Curves ─────────────────────────────────────────────────────────

#[derive(Clone, Debug, PartialEq)]
enum CurveSpec {
    Koblitz {
        a: u8,
        n: u32,
    },
    Random {
        n: u32,
        seed: u64,
        max_cofactor: u64,
    },
    Named(String),
    Prime {
        bits: u32,
    },
}

impl CurveSpec {
    fn to_json(&self) -> Value {
        match self {
            CurveSpec::Koblitz { a, n } => json!({"koblitz_degree": n, "curve_a": a}),
            CurveSpec::Random {
                n,
                seed,
                max_cofactor,
            } => json!({"char2_degree": n, "curve_seed": seed, "max_cofactor": max_cofactor}),
            CurveSpec::Named(name) => json!({"curve": name}),
            CurveSpec::Prime { bits } => json!({"bits": bits}),
        }
    }
}

const SELECTOR_HELP: &str = "supply exactly one curve selector: --koblitz-degree N --curve-a {0,1}, --char2-degree N [--curve-seed S] [--max-cofactor C], --curve NAME, or --bits B";

impl CurveArgs {
    /// The selector, `Ok(None)` when none was given.
    fn spec(&self) -> Result<Option<CurveSpec>, String> {
        let koblitz = self.koblitz_degree.is_some() || self.curve_a.is_some();
        let random = self.char2_degree.is_some();
        let named = self.curve.is_some();
        let prime = self.bits.is_some();
        match [koblitz, random, named, prime]
            .iter()
            .filter(|b| **b)
            .count()
        {
            0 => {
                if self.curve_seed.is_some() || self.max_cofactor.is_some() {
                    return Err("--curve-seed and --max-cofactor need --char2-degree".into());
                }
                return Ok(None);
            }
            1 => {}
            _ => return Err(format!("conflicting curve selectors: {SELECTOR_HELP}")),
        }
        if !random && (self.curve_seed.is_some() || self.max_cofactor.is_some()) {
            return Err("--curve-seed and --max-cofactor need --char2-degree".into());
        }
        if koblitz {
            return match (self.koblitz_degree, self.curve_a) {
                (Some(n), Some(a)) => Ok(Some(CurveSpec::Koblitz { a, n })),
                _ => Err("--koblitz-degree and --curve-a go together".into()),
            };
        }
        if let Some(n) = self.char2_degree {
            return Ok(Some(CurveSpec::Random {
                n,
                seed: self.curve_seed.unwrap_or(1),
                max_cofactor: self.max_cofactor.unwrap_or(8),
            }));
        }
        if let Some(name) = &self.curve {
            return Ok(Some(CurveSpec::Named(name.clone())));
        }
        Ok(self.bits.map(|bits| CurveSpec::Prime { bits }))
    }

    /// The selector recorded in a manifest or `curve.json` (`null` or an
    /// object without selector keys means none).
    fn from_json(v: &Value) -> Result<Option<CurveSpec>, String> {
        let Some(o) = v.as_object() else {
            return Ok(None);
        };
        let u = |k: &str| o.get(k).and_then(Value::as_u64);
        let a = Self {
            koblitz_degree: u("koblitz_degree").map(|x| x as u32),
            curve_a: u("curve_a").map(|x| x as u8),
            char2_degree: u("char2_degree").map(|x| x as u32),
            curve_seed: u("curve_seed"),
            max_cofactor: u("max_cofactor"),
            curve: o.get("curve").and_then(Value::as_str).map(str::to_string),
            bits: u("bits").map(|x| x as u32),
        };
        if a.curve_a.is_some_and(|x| x > 1) {
            return Err("curve_a must be 0 or 1".into());
        }
        a.spec()
    }
}

/// An owned curve, or the reason a selector cannot be built.
enum Built {
    Koblitz(Box<KoblitzCurve>),
    Binary(Box<BinaryInstance>),
    Prime(Box<PrimeInstance>),
    Unbuildable(String),
}

impl Built {
    fn curve(&self) -> Option<Curve<'_>> {
        match self {
            Built::Koblitz(k) => Some(Curve::Koblitz(k)),
            Built::Binary(b) => Some(Curve::Binary(b)),
            Built::Prime(p) => Some(Curve::Prime(p)),
            Built::Unbuildable(_) => None,
        }
    }
}

fn build_curve(spec: &CurveSpec) -> Result<Built, String> {
    match spec {
        CurveSpec::Koblitz { a, n } => {
            if !(3..=MAX_N).contains(n) {
                return Err(format!(
                    "--koblitz-degree must be in 3..={MAX_N} (measured metrics need 5..=62), got {n}"
                ));
            }
            KoblitzCurve::new(*a, *n)
                .map(|k| Built::Koblitz(Box::new(k)))
                .ok_or_else(|| {
                    format!("K_{a}/GF(2^{n}) has no usable prime-order subgroup in the existing constructor")
                })
        }
        CurveSpec::Random {
            n,
            seed,
            max_cofactor,
        } => {
            if !(5..=62).contains(n) {
                return Err(format!("--char2-degree must be in 5..=62, got {n}"));
            }
            if *max_cofactor == 0 {
                return Err("--max-cofactor must be at least 1".into());
            }
            catch_unwind(|| random_binary_instance(*n, *seed, *max_cofactor))
                .map_err(|_| format!("random binary curve construction failed at n = {n}"))?
                .map(|i| Built::Binary(Box::new(i)))
                .ok_or_else(|| {
                    format!("no random binary curve at n = {n} with cofactor <= {max_cofactor} for seed {seed}; raise --max-cofactor or change --curve-seed")
                })
        }
        CurveSpec::Prime { bits } => roster_prime_instance(*bits)
            .map(|i| Built::Prime(Box::new(i)))
            .ok_or_else(|| format!("no bench-roster prime curve of {bits} bits")),
        CurveSpec::Named(name) => {
            let p = params::named(name)?;
            let (degree, binary) = match &p.field {
                params::Field::Binary { degree, .. }
                | params::Field::BinaryAbstract { degree, .. } => (Some(*degree), true),
                params::Field::Prime { .. } => (None, false),
            };
            if !binary {
                return Ok(Built::Unbuildable(format!(
                    "named prime profile {name} is inspection-only (use --bits B for a scaled prime curve)"
                )));
            }
            let n = degree.unwrap_or(0);
            let ab = (p.a.as_str(), p.b.as_str());
            let a = match ab {
                ("0", "1") => Some(0u8),
                ("1", "1") => Some(1u8),
                _ => None,
            };
            match a {
                Some(a) if (3..=MAX_N).contains(&n) => KoblitzCurve::new(a, n)
                    .map(|k| Built::Koblitz(Box::new(k)))
                    .ok_or_else(|| format!("{name}: no usable prime-order subgroup at n = {n}")),
                _ => Ok(Built::Unbuildable(format!(
                    "named profile {name} (GF(2^{n})) is inspection-only: this toolkit builds curves with n <= {MAX_N}, so every cell would be not_applicable; use --koblitz-degree for a scaled Koblitz curve"
                ))),
            }
        }
    }
}

/// `field`, `curve` records, curve tag and display label.
struct Identity {
    field: Value,
    curve: Value,
    tag: String,
    label: String,
}

fn identity_of(built: &Built) -> Result<Identity, String> {
    let curve = built.curve().ok_or("curve cannot be built")?;
    match built {
        Built::Koblitz(_) | Built::Binary(_) => {
            let ctx = Ctx::new(&curve).map_err(|e| e.to_string())?;
            let (poly, order, label, tag) = match built {
                Built::Koblitz(k) => (
                    &k.curve.irreducible,
                    k.group_order.to_u64(),
                    k.label(),
                    format!("kb{}", k.a),
                ),
                Built::Binary(b) => (
                    &b.irreducible,
                    Some(b.group_order),
                    b.name.clone(),
                    "rb".into(),
                ),
                _ => unreachable!(),
            };
            let order = order.ok_or("group order exceeds a word")?;
            let mut exps: Vec<u32> = vec![poly.degree];
            let mut low = poly.low_terms.clone();
            low.sort_unstable_by(|a, b| b.cmp(a));
            exps.extend(low);
            let trace = (1i64 << ctx.n) + 1 - order as i64;
            Ok(Identity {
                field: identity::binary_field_record(ctx.n, &exps),
                curve: identity::binary_curve_record(
                    ctx.a,
                    ctx.b,
                    order,
                    trace,
                    ctx.r,
                    ctx.h,
                    (ctx.generator.x, ctx.generator.y),
                ),
                tag,
                label,
            })
        }
        Built::Prime(p) => Ok(Identity {
            field: identity::prime_field_record(p.curve.p),
            curve: identity::prime_curve_record(
                p.curve.a,
                p.curve.b,
                p.group_order,
                p.r,
                p.cofactor,
                p.generator,
            ),
            tag: "p".into(),
            label: p.name.clone(),
        }),
        Built::Unbuildable(why) => Err(why.clone()),
    }
}

// ── Manifests ──────────────────────────────────────────────────────

fn strip_comments(v: &mut Value) {
    match v {
        Value::Object(o) => {
            o.retain(|k, _| !k.starts_with('_'));
            o.values_mut().for_each(strip_comments);
        }
        Value::Array(a) => a.iter_mut().for_each(strip_comments),
        _ => {}
    }
}

fn load_manifest(path: &Path, m_flag: Option<&Vec<u32>>) -> Result<Manifest, String> {
    let text = std::fs::read_to_string(path)
        .map_err(|e| format!("cannot read manifest {}: {e}", path.display()))?;
    let mut v: Value = serde_json::from_str(&text)
        .map_err(|e| format!("manifest {} is not JSON: {e}", path.display()))?;
    strip_comments(&mut v);
    let o = v
        .as_object_mut()
        .ok_or_else(|| format!("manifest {} must be a JSON object", path.display()))?;
    if o.get("schema").is_none() {
        o.insert("schema".into(), json!(MANIFEST_SCHEMA));
    }
    if o.get("curve").is_none() {
        o.insert("curve".into(), Value::Null);
    }
    if o.get("m").is_none() {
        o.insert(
            "m".into(),
            json!(m_flag.cloned().unwrap_or_else(|| vec![2, 3])),
        );
    }
    let manifest: Manifest = serde_json::from_value(v)
        .map_err(|e| format!("manifest {} is invalid: {e}", path.display()))?;
    if manifest.schema != MANIFEST_SCHEMA {
        return Err(format!(
            "manifest schema must be {MANIFEST_SCHEMA}, got {}",
            manifest.schema
        ));
    }
    Ok(manifest)
}

fn manifest_from_flags(
    families: &[String],
    cells: &[String],
    dims: Option<&str>,
    m: &[u32],
    seeds: &[u64],
    modifiers: &[String],
) -> Result<Manifest, String> {
    if families.is_empty() && cells.is_empty() {
        return Err("supply --manifest FILE, --families a,b,c or --cell RECIPE".into());
    }
    let mut manifest = Manifest::new(
        Value::Null,
        if m.is_empty() { vec![2, 3] } else { m.to_vec() },
    );
    for c in cells {
        manifest.cells.push(Recipe::parse(c)?);
    }
    if !families.is_empty() {
        let mut matrix = Matrix::default();
        for f in families {
            let info = registry::find(f.trim())
                .ok_or_else(|| format!("unknown family `{f}`; try `ca-ic fbkit list`"))?;
            if matches!(info.kind, Kind::SystemModifier | Kind::SetModifier) {
                return Err(format!(
                    "`{}` is a modifier, not a family: pass it with --modifiers",
                    info.name
                ));
            }
            matrix.families.push(info.name.to_string());
        }
        if let Some(d) = dims {
            matrix.dims = parse_dims(d)?;
        }
        matrix.seeds = seeds.to_vec();
        for set in modifiers {
            let set = set.trim();
            if set.is_empty() || set == "none" {
                matrix.modifiers.push(Default::default());
            } else {
                let r = Recipe::parse(&format!("coordinate;{set}"))?;
                matrix.modifiers.push(r.modifiers);
            }
        }
        manifest.matrix = Some(matrix);
    } else if dims.is_some() || !seeds.is_empty() || !modifiers.is_empty() {
        return Err("--dims, --seeds and --modifiers apply to --families; write them into the --cell recipes".into());
    }
    Ok(manifest)
}

fn normalise_groups(names: &[String]) -> Result<Vec<String>, String> {
    let mut set: BTreeSet<Group> = names
        .iter()
        .map(|g| Group::parse(g))
        .collect::<Result<_, _>>()?;
    set.insert(Group::Construction);
    if set.contains(&Group::F4) || set.contains(&Group::Sat) {
        set.insert(Group::System);
    }
    if set.contains(&Group::Yield) || set.contains(&Group::F4) || set.contains(&Group::Sat) {
        set.insert(Group::Derived);
    }
    Ok(set.iter().map(|g| g.as_str().to_string()).collect())
}

fn apply_opts(
    m: &mut Manifest,
    o: &RunOpts,
    from_file: bool,
    default_metrics: &str,
) -> Result<(), String> {
    if let Some(s) = o.seed {
        m.seed = s;
    }
    if let Some(j) = o.jobs {
        if j == 0 {
            return Err("--jobs must be at least 1".into());
        }
        m.jobs = Some(j);
    }
    if let Some(t) = o.targets {
        m.metrics.targets = t;
    }
    if let Some(b) = o.budget_seconds {
        m.metrics.budget_seconds = b;
    }
    if let Some(c) = o.conflict_budget {
        m.metrics.conflict_budget = c;
    }
    if let Some(d) = o.d_max {
        m.metrics.d_max = d;
    }
    if let Some(e) = o.exact_cap {
        m.metrics.exact_cap = e;
    }
    let names: Vec<String> = match (&o.metrics, from_file) {
        (Some(s), _) => s.split(',').map(str::to_string).collect(),
        (None, true) => m.metrics.groups.clone(),
        (None, false) => default_metrics.split(',').map(str::to_string).collect(),
    };
    m.metrics.groups = normalise_groups(&names)?;
    if m.m.is_empty() || m.m.iter().any(|x| !(2..=8).contains(x)) {
        return Err("--m values must be in 2..=8".into());
    }
    m.m.sort_unstable();
    m.m.dedup();
    if m.metrics.targets == 0 {
        return Err("--targets must be at least 1".into());
    }
    Ok(())
}

// ── Sweep ──────────────────────────────────────────────────────────

fn fnv(s: &str) -> u64 {
    s.bytes().fold(0xcbf2_9ce4_8422_2325u64, |h, b| {
        (h ^ u64::from(b)).wrapping_mul(0x0100_0000_01b3)
    })
}

/// Usable points of a cell as sorted-hex pairs, by deterministic
/// re-materialisation (the seed derivation of `sweep::measure_cell`).
fn cell_points(
    sweep_seed: u64,
    curve: &Curve<'_>,
    rec: &CellRecord,
) -> Result<Vec<(String, String)>, String> {
    let recipe: Recipe = serde_json::from_value(rec.recipe.clone())
        .map_err(|e| format!("cell {} has an unreadable recipe: {e}", rec.cell_id))?;
    let seed = sweep_seed ^ fnv(&rec.cell_id).rotate_left(17);
    catch_unwind(AssertUnwindSafe(|| -> Result<_, String> {
        let ctx = Ctx::new(curve).map_err(|e| e.to_string())?;
        let mat = materialize(&recipe, curve, seed).map_err(|e| e.to_string())?;
        let view = base_points_binary(&ctx, &mat);
        Ok(view
            .usable
            .iter()
            .map(|p| (format!("{:x}", p.x), format!("{:x}", p.y)))
            .collect())
    }))
    .map_err(|_| format!("panic while rebuilding the points of {}", rec.cell_id))?
}

fn cell_dimension(c: &CellRecord) -> Value {
    serde_json::from_value::<Recipe>(c.recipe.clone())
        .ok()
        .and_then(|r| r.size())
        .map_or_else(
            || c.metrics["construction"]["dimension"].clone(),
            |l| json!(l),
        )
}

fn cell_row(c: &CellRecord) -> Value {
    let m = &c.metrics;
    json!({
        "cell_id": c.cell_id,
        "family": c.family,
        "l": cell_dimension(c),
        "m": c.m,
        "status": c.status,
        "reason": c.reason,
        "fb_points": m["construction"]["fb_points"],
        "effective_columns": m["construction"]["effective_columns"],
        "coverage": m["yield"]["coverage"],
        "expected_trials": m["yield"]["expected_trials"],
        "solving_degree_mean": m["f4"]["random"]["solving_degree_mean"],
        "sat_clauses": m["sat"]["clauses"],
        "conflicts_mean": m["sat"]["random"]["conflicts_mean"],
        "expected_pdp_ops": m["derived"]["expected_pdp_ops"],
    })
}

fn rows_markdown(rows: &[Value]) -> String {
    let mut md = String::from(
        "| cell | family | l | m | status | fb | columns | coverage | E[trials] | D mean | clauses | conflicts | E[ops] |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|\n",
    );
    for r in rows {
        let _ = writeln!(
            md,
            "| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |",
            r["cell_id"].as_str().unwrap_or("?"),
            r["family"].as_str().unwrap_or("?"),
            cellv(&r["l"]),
            cellv(&r["m"]),
            r["status"].as_str().unwrap_or("?"),
            cellv(&r["fb_points"]),
            cellv(&r["effective_columns"]),
            cellv(&r["coverage"]),
            cellv(&r["expected_trials"]),
            cellv(&r["solving_degree_mean"]),
            cellv(&r["sat_clauses"]),
            cellv(&r["conflicts_mean"]),
            cellv(&r["expected_pdp_ops"]),
        );
    }
    md
}

fn is_nonempty_dir(p: &Path) -> bool {
    std::fs::read_dir(p).is_ok_and(|mut r| r.next().is_some())
}

#[allow(clippy::too_many_arguments)]
fn run_sweep(
    op: &str,
    curve_args: &CurveArgs,
    mut manifest: Manifest,
    from_file: bool,
    default_metrics: &str,
    opts: &RunOpts,
    resume: bool,
    objective: &str,
    json_only: bool,
) -> Result<Value, String> {
    let started = Instant::now();
    let objective = Objective::parse(objective)?;
    // Curve: flags, else the manifest.
    let flag_spec = curve_args.spec()?;
    let file_spec = CurveArgs::from_json(&manifest.curve)?;
    let spec = match (flag_spec, file_spec) {
        (Some(f), Some(m)) if f != m => {
            return Err(format!(
                "the curve flags ({}) disagree with the manifest curve ({})",
                f.to_json(),
                m.to_json()
            ))
        }
        (Some(f), _) => f,
        (None, Some(m)) => m,
        (None, None) => {
            return Err(SELECTOR_HELP.replacen(
                "supply",
                "supply (flags or the manifest `curve`)",
                1,
            ))
        }
    };
    apply_opts(&mut manifest, opts, from_file, default_metrics)?;
    let progress = |s: &str| {
        if !json_only {
            eprintln!("{s}");
        }
    };
    let built = build_curve(&spec)?;
    let config_base = json!({
        "curve": spec.to_json(),
        "m": manifest.m,
        "metrics": manifest.metrics,
        "seed": manifest.seed,
        "objective": objective.as_str(),
        "resume": resume,
    });
    let Some(curve) = built.curve() else {
        let why = match &built {
            Built::Unbuildable(w) => w.clone(),
            _ => String::new(),
        };
        let mut r = report(
            op,
            "skipped",
            config_base,
            started,
            format!("Skipped: {why}\n"),
        );
        put(&mut r, "reason", json!(why));
        put(&mut r, "cells", json!([]));
        return Ok(r);
    };
    let id = identity_of(&built)?;
    let curve_id = identity::curve_id(&id.field, &id.curve, &id.tag)?;
    manifest.curve = spec.to_json();
    manifest.curve_id = curve_id.clone();
    manifest.curve_tag = Some(id.tag.clone());
    let manifest = manifest.frozen()?;
    let sweep_id = manifest.sweep_id.clone().unwrap_or_default();
    let dir = opts
        .dir
        .clone()
        .unwrap_or_else(|| PathBuf::from(format!("fbkit-{curve_id}-{sweep_id}")));
    let store = if resume && is_nonempty_dir(&dir) {
        let s = Store::open(&dir)?;
        let old = s.read_manifest().map_err(|_| {
            format!(
                "{}: not a fbkit run directory (no manifest.json)",
                dir.display()
            )
        })?;
        if old["sweep_id"].as_str() != Some(sweep_id.as_str()) {
            return Err(format!(
                "{}: holds sweep {} but this manifest is sweep {sweep_id}; use a new --dir",
                dir.display(),
                old["sweep_id"].as_str().unwrap_or("?")
            ));
        }
        s
    } else {
        Store::create(&dir)?
    };
    store.write_manifest(&serde_json::to_value(&manifest).map_err(|e| e.to_string())?)?;
    store.write_curve(&json!({
        "field": id.field,
        "curve": id.curve,
        "curve_id": curve_id,
        "curve_tag": id.tag,
        "label": id.label,
        "selector": spec.to_json(),
    }))?;
    progress(&format!(
        "fbkit: curve {} ({curve_id}), sweep {sweep_id}, {} cells, directory {}",
        id.label,
        expand(&manifest).len(),
        dir.display()
    ));

    let mut warnings: Vec<String> = Vec::new();
    let skip = |cell: &str| {
        resume
            && matches!(
                store.cell_status(cell).as_deref(),
                Some("complete" | "not_applicable" | "caps_hit")
            )
    };
    let mut on_cell = |rec: CellRecord| {
        if let Err(e) = store.write_cell(&rec) {
            warnings.push(format!("cannot store {}: {e}", rec.cell_id));
        }
    };
    let summary = run_sweep_driver(&manifest, &curve, &mut on_cell, &skip, &progress);
    drop(on_cell);

    let cells = store.read_cells()?;
    // Point lists: rebuilt in parallel from the recipes (also for cells of an
    // earlier, interrupted run that lack one), checked against the cell digest.
    let missing: Vec<&CellRecord> = cells
        .iter()
        .filter(|c| {
            matches!(c.status.as_str(), "complete" | "caps_hit" | "budget")
                && c.metrics["construction"]["usable_points"]
                    .as_u64()
                    .is_some_and(|n| opts.points || n <= AUTO_POINTS_LIMIT)
                && !store
                    .root()
                    .join(format!("points/{}.jsonl", c.cell_id))
                    .exists()
        })
        .collect();
    if !missing.is_empty() {
        progress(&format!("fbkit: storing {} point lists", missing.len()));
        let store_points = |c: &CellRecord| -> Option<String> {
            match cell_points(manifest.seed, &curve, c) {
                Ok(pts) => {
                    let digest = identity::point_set_sha256(&pts);
                    if c.point_set_sha256.as_deref() != Some(digest.as_str()) {
                        return Some(format!(
                            "points of {} not stored: rebuilt digest differs from the cell digest",
                            c.cell_id
                        ));
                    }
                    store
                        .write_points(&c.cell_id, &pts)
                        .err()
                        .map(|e| format!("cannot store points of {}: {e}", c.cell_id))
                }
                Err(e) => Some(format!("points of {} not stored: {e}", c.cell_id)),
            }
        };
        let found: Vec<Option<String>> = match rayon::ThreadPoolBuilder::new()
            .num_threads(summary.jobs.max(1))
            .build()
        {
            Ok(pool) => pool.install(|| missing.par_iter().map(|c| store_points(c)).collect()),
            Err(_) => missing.iter().map(|c| store_points(c)).collect(),
        };
        warnings.extend(found.into_iter().flatten());
    }
    let slopes = compute_slopes(&cells);
    let ranking = rank(&cells, objective, &Weights::default());
    store.write_ranking(&ranking.to_json())?;
    let rows: Vec<Value> = cells.iter().map(cell_row).collect();
    let errors: Vec<Value> = cells
        .iter()
        .filter(|c| c.status == "error")
        .map(|c| json!({"cell_id": c.cell_id, "family": c.family, "reason": c.reason}))
        .collect();
    let status = if errors.is_empty() && warnings.is_empty() {
        "complete"
    } else {
        "incomplete"
    };
    let mut md = String::new();
    let _ = writeln!(
        md,
        "# fbkit {} on {} ({curve_id})\n\nSweep `{sweep_id}`: {} cells ({} run now, {} skipped by resume); statuses {}. Directory `{}`.\n",
        if op == "fbkit-build" { "build" } else { "sweep" },
        id.label,
        summary.total,
        summary.run,
        summary.skipped,
        serde_json::to_string(&summary.by_status).unwrap_or_default(),
        dir.display()
    );
    md.push_str(&rows_markdown(&rows));
    let sigma: Vec<_> = slopes.iter().filter(|s| s.sigma.is_some()).collect();
    if !sigma.is_empty() {
        let _ = writeln!(
            md,
            "\nSlope sigma = dD*/d dim V per (family, m) (interior optimum needs sigma <= 1/4):"
        );
        for s in sigma {
            let _ = writeln!(
                md,
                "- {} m={}: sigma {} over {} dimensions",
                s.family,
                s.m,
                s.sigma.map_or("null".into(), |x| format!("{x:.3}")),
                s.dims
            );
        }
    }
    md.push('\n');
    md.push_str(&ranking.render(10));
    if !errors.is_empty() {
        let _ = writeln!(md, "\nErrors ({}):", errors.len());
        for e in &errors {
            let _ = writeln!(
                md,
                "- {}: {}",
                e["cell_id"].as_str().unwrap_or("?"),
                e["reason"].as_str().unwrap_or("?")
            );
        }
    }
    for w in &warnings {
        let _ = writeln!(md, "\nWarning: {w}");
    }
    md.push_str("\nStage diagnostics only: not an IC1 result, not a speedup; fb<B> counts points before folding; ranking is relative within this sweep.\n");

    let mut config = config_base;
    put(&mut config, "dir", json!(dir.display().to_string()));
    put(&mut config, "jobs", json!(summary.jobs));
    let mut r = report(op, status, config, started, md);
    put(&mut r, "curve_id", json!(curve_id));
    put(&mut r, "curve_label", json!(id.label));
    put(&mut r, "sweep_id", json!(sweep_id));
    put(&mut r, "run_directory", json!(dir.display().to_string()));
    put(
        &mut r,
        "counts",
        json!({"total": summary.total, "run": summary.run, "skipped": summary.skipped, "by_status": summary.by_status}),
    );
    put(&mut r, "cells", Value::Array(rows));
    put(
        &mut r,
        "slopes",
        serde_json::to_value(&slopes).unwrap_or(Value::Null),
    );
    put(&mut r, "errors", Value::Array(errors));
    put(&mut r, "warnings", json!(warnings));
    put(&mut r, "ranking", ranking_summary(&ranking, 10));
    store.write_report(&r, r["markdown"].as_str().unwrap_or(""))?;
    store.write_inventory()?;
    Ok(r)
}

fn ranking_summary(ranking: &crate::cryptanalysis::fbkit::rank::Ranking, top: usize) -> Value {
    let full = ranking.to_json();
    let ordered: Vec<Value> = full["ordered"]
        .as_array()
        .map(|a| a.iter().take(top).cloned().collect())
        .unwrap_or_default();
    json!({
        "objective": full["objective"],
        "top": ordered,
        "pareto_front": full["pareto_front"],
        "pareto_axes": full["pareto_axes"],
        "per_family_best": full["per_family_best"],
        "unranked": full["unranked_with_reason"],
    })
}

// ── rank ───────────────────────────────────────────────────────────

fn rerank(dir: &Path, objective: &str, top: usize, weights: Option<&str>) -> Result<Value, String> {
    let started = Instant::now();
    let obj = Objective::parse(objective)?;
    let w = Weights::parse(weights.unwrap_or(""))?;
    let store = Store::open(dir)?;
    let cells = store.read_cells()?;
    if cells.is_empty() {
        return Err(format!("{}: no cells to rank", dir.display()));
    }
    let ranking = rank(&cells, obj, &w);
    store.write_ranking(&ranking.to_json())?;
    let md = ranking.render(top.max(1));
    let rows: Vec<Value> = cells.iter().map(cell_row).collect();
    let mut r = report(
        "fbkit-rank",
        "complete",
        json!({"dir": dir.display().to_string(), "objective": obj.as_str(), "top": top, "weights": w}),
        started,
        md,
    );
    put(&mut r, "cells", Value::Array(rows));
    put(&mut r, "ranking", ranking.to_json());
    store.write_report(&r, r["markdown"].as_str().unwrap_or(""))?;
    store.write_inventory()?;
    Ok(r)
}

// ── export ─────────────────────────────────────────────────────────

fn export(dir: &Path, cell: &str, archive_out: Option<&Path>) -> Result<Value, String> {
    let started = Instant::now();
    if let Some(p) = archive_out {
        if std::fs::symlink_metadata(p).is_ok() {
            return Err(format!("archive output already exists: {}", p.display()));
        }
    }
    let store = Store::open(dir)?;
    let cells = store.read_cells()?;
    let exact = cells.iter().find(|c| c.cell_id == cell);
    let hits: Vec<&CellRecord> = cells
        .iter()
        .filter(|c| c.cell_id.starts_with(cell))
        .collect();
    let rec = match (exact, hits.as_slice()) {
        (Some(c), _) => c,
        (None, [c]) => *c,
        (None, []) => return Err(format!("no cell `{cell}` in {}", dir.display())),
        _ => {
            return Err(format!(
                "`{cell}` matches {} cells; give the whole id",
                hits.len()
            ))
        }
    };
    if !matches!(rec.status.as_str(), "complete" | "caps_hit" | "budget") {
        return Err(format!(
            "cell {} has status {} ({}): nothing to export",
            rec.cell_id,
            rec.status,
            rec.reason.as_deref().unwrap_or("no reason recorded")
        ));
    }
    let curve_doc = store.read_curve()?;
    let (points, points_source) = match store.read_points(&rec.cell_id) {
        Ok(p) => (p, "stored"),
        Err(_) => {
            let spec = CurveArgs::from_json(&curve_doc["selector"])?
                .ok_or("curve.json has no curve selector; cannot rebuild the points")?;
            let built = build_curve(&spec)?;
            let curve = built.curve().ok_or("curve cannot be rebuilt")?;
            let seed = store.read_manifest()?["seed"].as_u64().unwrap_or(0);
            (
                cell_points(seed, &curve, rec)?,
                "re-materialised from the recipe",
            )
        }
    };
    let builder = format!("ca-ic fbkit {}", env!("CARGO_PKG_VERSION"));
    let mut doc = export_archive_document(rec, &curve_doc, &points, &builder)?;
    let label = rec.ps1_label.clone();
    put(&mut doc, "ps1_label", json!(label));
    put(&mut doc, "candidate_id", Value::Null);
    let text = serde_json::to_string_pretty(&doc).map_err(|e| e.to_string())?;
    if let Some(p) = archive_out {
        let mut f = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(p)
            .map_err(|e| format!("cannot create {}: {e}", p.display()))?;
        f.write_all(text.as_bytes())
            .and_then(|()| f.write_all(b"\n"))
            .and_then(|()| f.sync_all())
            .map_err(|e| format!("cannot write {}: {e}", p.display()))?;
    }
    let index_row = archive_index_row(
        &doc,
        archive_out.map_or("", |p| p.to_str().unwrap_or("")),
        text.len() as u64,
        &identity::sha256_hex_bytes(text.as_bytes()),
    );
    let embed = if points.len() <= 4096 {
        doc.clone()
    } else {
        let mut d = doc.clone();
        put(&mut d, "points", Value::Null);
        put(&mut d, "points_omitted", json!(points.len()));
        d
    };
    let mut md = String::new();
    let _ = writeln!(
        md,
        "Archive document {ARCHIVE_SCHEMA} for cell `{}`\n\n- PS1 label: {} (candidate_id null: a stage label, not an IC1 result)\n- points: {} ({points_source})\n- archive written: {}\n\nThe fb-archive rule applies: published archive records are append-only; never rewrite one.",
        rec.cell_id,
        label.as_deref().unwrap_or("null (no PS1 label for this cell)"),
        points.len(),
        archive_out.map_or("no (add --archive-out FILE)".to_string(), |p| p.display().to_string())
    );
    let mut r = report(
        "fbkit-export",
        "complete",
        json!({"dir": dir.display().to_string(), "cell": rec.cell_id, "archive_out": archive_out.map(|p| p.display().to_string())}),
        started,
        md,
    );
    put(&mut r, "schema", json!(ARCHIVE_SCHEMA));
    put(&mut r, "cell_id", json!(rec.cell_id));
    put(&mut r, "ps1_label", json!(label));
    put(&mut r, "candidate_id", Value::Null);
    put(&mut r, "point_count", json!(points.len()));
    put(&mut r, "points_source", json!(points_source));
    put(&mut r, "index_row", json!(index_row));
    put(&mut r, "archive", embed);
    Ok(r)
}

// ── upload and download ────────────────────────────────────────────

fn upload_cmd(dir: &Path, s3: Option<&str>, dry_run: bool, require: bool) -> Result<Value, String> {
    let started = Instant::now();
    let store = Store::open(dir)?;
    let target = S3Target::resolve(s3)?;
    let aws = AwsCli::from_env();
    let rep = upload(
        &store,
        target.as_ref(),
        &aws,
        UploadOptions { dry_run, require },
    )?;
    let status = match rep.status.as_str() {
        "skipped" => "skipped",
        "complete" | "dry_run" => "complete",
        _ => "incomplete",
    };
    let mut md = String::new();
    let _ = writeln!(
        md,
        "Upload: {} ({})",
        rep.status,
        rep.reason.as_deref().unwrap_or("ok")
    );
    if let Some(d) = &rep.destination {
        let _ = writeln!(
            md,
            "\nDestination `{d}`: {} objects ({} bytes), {} uploaded, {} unchanged, {} would upload.",
            rep.objects.len(),
            rep.total_bytes,
            rep.count("uploaded"),
            rep.count("skipped"),
            rep.count("would_upload"),
        );
    }
    if let Some(p) = &rep.receipt {
        let _ = writeln!(md, "\nReceipt: {}", p.display());
    }
    let mut r = report(
        "fbkit-upload",
        status,
        json!({"dir": dir.display().to_string(), "s3": s3, "dry_run": dry_run, "require": require}),
        started,
        md,
    );
    put(&mut r, "upload_status", json!(rep.status));
    put(&mut r, "reason", json!(rep.reason));
    put(&mut r, "destination", json!(rep.destination));
    put(
        &mut r,
        "receipt",
        json!(rep.receipt.as_ref().map(|p| p.display().to_string())),
    );
    put(&mut r, "total_bytes", json!(rep.total_bytes));
    put(&mut r, "uploaded_bytes", json!(rep.uploaded_bytes));
    put(
        &mut r,
        "objects",
        serde_json::to_value(&rep.objects).map_err(|e| e.to_string())?,
    );
    Ok(r)
}

fn download_cmd(s3: Option<&str>, dir: &Path, verify_only: bool) -> Result<Value, String> {
    let started = Instant::now();
    let aws = AwsCli::from_env();
    let uri: String = match (s3, verify_only) {
        (Some(u), _) => {
            S3Target::parse(u)?;
            u.trim_end_matches('/').to_string()
        }
        (None, true) => String::new(),
        (None, false) => {
            return Err("--s3 s3://bucket/prefix/fbkit/<curve_id>/<sweep_id> is required".into())
        }
    };
    let rep = download(&uri, dir, &aws, DownloadOptions { verify_only })?;
    let md = format!(
        "Download: {}; {} files, {} verified ({} bytes) in `{}`. Receipt: {}\n",
        rep.status,
        rep.files,
        rep.verified,
        rep.bytes,
        dir.display(),
        rep.receipt
            .as_ref()
            .map_or("none".into(), |p| p.display().to_string())
    );
    let mut r = report(
        "fbkit-download",
        "complete",
        json!({"s3": s3, "dir": dir.display().to_string(), "verify_only": verify_only}),
        started,
        md,
    );
    put(&mut r, "download_status", json!(rep.status));
    put(&mut r, "source", json!(rep.source));
    put(&mut r, "files", json!(rep.files));
    put(&mut r, "verified", json!(rep.verified));
    put(&mut r, "bytes", json!(rep.bytes));
    put(&mut r, "extra_remote", json!(rep.extra_remote));
    put(
        &mut r,
        "receipt",
        json!(rep.receipt.as_ref().map(|p| p.display().to_string())),
    );
    Ok(r)
}
