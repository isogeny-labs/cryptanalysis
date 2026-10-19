//! Shared `icx solve` interface for exact Certicom challenge solvers.

use std::path::PathBuf;

use clap::{ArgGroup, Args, ValueEnum};
use num_bigint::BigUint;
use num_traits::Num;
use serde::Deserialize;
use serde_json::{json, Value};

use super::certicom_dlp::{self as dlp, ChallengeGroup, IndexInput, SolverOptions};

#[derive(Clone, Copy, Debug, PartialEq, Eq, ValueEnum)]
pub enum Method {
    Rho,
    Bsgs,
    #[value(alias = "ic")]
    IndexCalculus,
}

#[derive(Args, Debug)]
#[command(group(ArgGroup::new("target").required(true).args(["challenge", "secret", "point"])))]
pub struct SolveArgs {
    /// Exact Certicom challenge name (ECC2-130/ECCp-130 aliases accepted).
    pub curve: String,
    #[arg(long, value_enum)]
    pub method: Method,
    /// Load the published unknown-log challenge point Q.
    #[arg(long)]
    pub challenge: bool,
    /// Construct a known-answer target [k]G (decimal or 0x hex).
    #[arg(long)]
    pub secret: Option<String>,
    /// Externally supplied target X,Y (decimal or 0x hex).
    #[arg(long)]
    pub point: Option<String>,
    /// Rho iterations per restart, BSGS giant steps, or IC queries per phase.
    #[arg(long, default_value_t = 10_000)]
    pub max_iterations: u64,
    #[arg(long, default_value_t = 8)]
    pub max_restarts: u32,
    #[arg(long, default_value_t = 65_536)]
    pub max_table_entries: usize,
    #[arg(long, default_value_t = 1_048_576)]
    pub max_matrix_entries: usize,
    #[arg(long, default_value_t = 16)]
    pub factor_base_size: usize,
    #[arg(long, default_value_t = 4096)]
    pub max_base_candidates: u64,
    #[arg(long, default_value_t = 1)]
    pub seed: u64,
    /// BSGS interval lower bound (default 0).
    #[arg(long)]
    pub interval_lo: Option<String>,
    /// BSGS interval width (default n - lo); every scalar bound is full-width.
    #[arg(long)]
    pub interval_width: Option<String>,
    /// IC public factor-base points, relation queries and descent shifts JSON.
    #[arg(long)]
    pub preparation: Option<PathBuf>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct PointInput {
    x: String,
    y: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Preparation {
    curve: String,
    factor_base: Vec<PointInput>,
    relation_queries: Vec<String>,
    descent_shifts: Vec<String>,
    #[serde(default)]
    label: Option<String>,
}

pub fn parse_uint(value: &str) -> Result<BigUint, String> {
    let text = value.trim();
    let (digits, radix) = match text.strip_prefix("0x").or_else(|| text.strip_prefix("0X")) {
        Some(hex) => (hex, 16),
        None => (text, 10),
    };
    BigUint::from_str_radix(digits, radix)
        .map_err(|_| format!("invalid unsigned integer {value:?}"))
}

/// Execute exactly the selected method, with its own incomplete status and
/// independently replayed result. No analogue selection is involved here.
pub fn run(args: &SolveArgs) -> Result<Value, String> {
    let group = ChallengeGroup::by_name(&args.curve)?;
    let planted = args
        .secret
        .as_deref()
        .map(parse_uint)
        .transpose()?
        .map(|k| k % group.order());
    let target = if args.challenge {
        group.published_target()
    } else if let Some(k) = &planted {
        group.target_from_scalar(k)
    } else {
        let (x, y) = args
            .point
            .as_deref()
            .ok_or("supply --challenge, --secret, or --point")?
            .split_once(',')
            .ok_or("--point needs X,Y")?;
        group.point(&parse_uint(x)?, &parse_uint(y)?)?
    };
    let opts = SolverOptions {
        max_iterations: args.max_iterations,
        max_restarts: args.max_restarts,
        max_table_entries: args.max_table_entries,
        max_matrix_entries: args.max_matrix_entries,
        factor_base_size: args.factor_base_size,
        max_base_candidates: args.max_base_candidates,
        seed: args.seed,
    };
    if args.method != Method::Bsgs && (args.interval_lo.is_some() || args.interval_width.is_some())
    {
        return Err("scalar intervals apply to BSGS only".into());
    }
    if args.method != Method::IndexCalculus && args.preparation.is_some() {
        return Err("--preparation applies to index-calculus only".into());
    }
    let mut preparation_label = None;
    let report = match args.method {
        Method::Rho => dlp::rho(&group, &target, &opts)?,
        Method::Bsgs => {
            let lo = args
                .interval_lo
                .as_deref()
                .map(parse_uint)
                .transpose()?
                .unwrap_or_default();
            if lo >= *group.order() {
                return Err("interval lower bound must be below the subgroup order".into());
            }
            let width = args
                .interval_width
                .as_deref()
                .map(parse_uint)
                .transpose()?
                .unwrap_or_else(|| group.order() - &lo);
            dlp::bsgs(&group, &target, &lo, &width, &opts)?
        }
        Method::IndexCalculus => {
            let input = match &args.preparation {
                Some(path) => {
                    let text = std::fs::read_to_string(path)
                        .map_err(|e| format!("read {}: {e}", path.display()))?;
                    let input: Preparation = serde_json::from_str(&text)
                        .map_err(|e| format!("parse IC preparation: {e}"))?;
                    if ChallengeGroup::by_name(&input.curve)?.name() != group.name() {
                        return Err("IC preparation belongs to a different exact curve".into());
                    }
                    preparation_label = input.label;
                    Some(IndexInput {
                        factor_base: input
                            .factor_base
                            .iter()
                            .map(|p| group.point(&parse_uint(&p.x)?, &parse_uint(&p.y)?))
                            .collect::<Result<_, String>>()?,
                        relation_queries: input
                            .relation_queries
                            .iter()
                            .map(|s| parse_uint(s))
                            .collect::<Result<_, _>>()?,
                        descent_shifts: input
                            .descent_shifts
                            .iter()
                            .map(|s| parse_uint(s))
                            .collect::<Result<_, _>>()?,
                    })
                }
                None => None,
            };
            dlp::index_calculus(&group, &target, &opts, input.as_ref())?
        }
    };
    let matches_planted = planted
        .as_ref()
        .map(|k| report.scalar_value.as_ref() == Some(k));
    let mut value = serde_json::to_value(report).map_err(|e| e.to_string())?;
    value["operation"] = json!("solve");
    value["schema_version"] = json!(1);
    value["parameters"] = group.parameters();
    value["target"] = group.point_json(&target);
    value["planted_scalar"] = json!(planted.map(|k| k.to_string()));
    value["planted_recovered"] = json!(matches_planted);
    value["preparation_label"] = json!(preparation_label);
    value["limits"] = json!({"max_iterations": opts.max_iterations, "max_restarts": opts.max_restarts, "max_table_entries": opts.max_table_entries, "max_matrix_entries": opts.max_matrix_entries, "factor_base_size": opts.factor_base_size, "max_base_candidates": opts.max_base_candidates});
    Ok(value)
}

pub fn display(report: &Value) {
    println!(
        "{}: {} on the exact {}-bit {} field",
        report["curve"].as_str().unwrap_or("?"),
        report["method"].as_str().unwrap_or("?"),
        report["parameters"]["field_bits"],
        report["parameters"]["field_type"].as_str().unwrap_or("?")
    );
    if report["verified"] == true {
        println!(
            "scalar: {} (verified [k]G = Q)",
            report["scalar"].as_str().unwrap_or("?")
        );
    } else {
        println!(
            "{}: {}",
            report["status"].as_str().unwrap_or("incomplete"),
            report["reason"].as_str().unwrap_or("no verified scalar")
        );
    }
    if let Some(stages) = report.get("index_calculus").filter(|v| !v.is_null()) {
        println!(
            "IC: {} base points, {} verified relations, rank {}, {} descent queries",
            stages["factor_base_size"],
            stages["verified_relations"],
            stages["rank"],
            stages["descent_queries"]
        );
    }
}
