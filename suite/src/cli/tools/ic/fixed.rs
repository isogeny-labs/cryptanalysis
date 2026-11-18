//! Fixed-parameter wide-field workflow.
//!
//! The `preflight` stage is entirely native Rust and reconstructs the exact
//! ECC2K-130 curve, published target, Frobenius eigenvalue, and fixed factor
//! base. Persistent relation collection remains in the existing Python ONB
//! engine; every ECC2K-130 invocation carries the native preflight result.
use clap::Args;
use serde_json::{json, Value};
use std::{
    fs,
    path::PathBuf,
    process::{Command, Stdio},
};

use crate::cryptanalysis::ecc2k130_index_calculus;

#[derive(Args, Clone)]
pub struct FixedArgs {
    /// Fixed K_0 parameters and target coordinates, including the field basis.
    #[arg(long)]
    pub params: PathBuf,
    /// Durable campaign directory. Rerun with the same parameters to resume.
    #[arg(long)]
    pub dir: PathBuf,
    /// Use status to check subgroup membership and candidate scalars. The all stage
    /// also attempts target-specific relations when base logs are incomplete.
    #[arg(long, default_value = "all", value_parser = ["preflight", "select", "pairs", "collect", "logs", "solve", "all", "status"])]
    pub stage: String,
    /// Exact pair table, bounded SAT, or an opt-in learned policy with pair fallback.
    #[arg(long, default_value = "pairs", value_parser = ["pairs", "sat", "learned"])]
    pub solver: String,
    /// JSON selector trained with indexcalc_selector.py; required for learned.
    #[arg(long)]
    pub selector_model: Option<PathBuf>,
    /// Additional probes per collection stream or target in this invocation.
    #[arg(long, default_value_t = 32)]
    pub attempts: u32,
    /// Maximum new pair candidates built in this invocation.
    #[arg(long, default_value_t = 10000)]
    pub pair_budget: u64,
    /// Native SAT solve budget; a separate watchdog bounds each complete SAT query.
    #[arg(long, default_value_t = 0.25)]
    pub query_seconds: f64,
    /// Python interpreter; python-sat and pycryptosat are needed only for SAT.
    #[arg(long, default_value = "python3")]
    pub python: PathBuf,
}

fn exact_ecc2k130_document(path: &PathBuf) -> Result<bool, String> {
    let supplied: Value = serde_json::from_slice(
        &fs::read(path).map_err(|error| format!("could not read {}: {error}", path.display()))?,
    )
    .map_err(|error| format!("could not parse {}: {error}", path.display()))?;
    let expected: Value = serde_json::from_str(include_str!(
        "../../../../docs/ic/params/ecc2k130-fixed.json"
    ))
    .expect("checked-in ECC2K-130 parameters are valid JSON");
    Ok(supplied == expected)
}

fn native_preflight(path: &PathBuf) -> Result<Value, String> {
    if !exact_ecc2k130_document(path)? {
        return Err(
            "native preflight currently accepts the checked-in exact ECC2K-130 profile; use the persistent engine for other fixed profiles"
                .into(),
        );
    }
    let (curve, target, factor_base) = ecc2k130_index_calculus::validated_profile()?;
    Ok(json!({
        "schema_version": 1,
        "operation": "fixed",
        "stage": "preflight",
        "status": "complete",
        "engine": "rust-native",
        "degree": curve.n,
        "curve_a": curve.a,
        "subgroup_order": curve.subgroup_order.to_string(),
        "cofactor": curve.cofactor.to_string(),
        "generator_on_curve": curve.curve.is_on_curve(curve.generator()),
        "generator_in_subgroup": curve.mul(curve.generator(), &curve.subgroup_order) == crate::binary_ecc::BinaryPoint::Infinity,
        "target_on_curve": curve.curve.is_on_curve(&target),
        "target_in_subgroup": curve.mul(&target, &curve.subgroup_order) == crate::binary_ecc::BinaryPoint::Infinity,
        "frobenius_eigenvalue": curve.lambda.to_string(),
        "factor_base": {
            "kind": "hamming-weight",
            "weight": 2,
            "orbit_columns": factor_base.unknowns(),
            "signed_points": factor_base.points.len(),
            "native_orbit_transport_checked": true
        },
        "base_point": "known",
        "targets": {"ecc2k-130": {"scalar_known": false, "scalar_source": Value::Null}},
        "ready_for_persistent_collection": true,
        "claim_boundary": "Native validation and factor-base construction only; no relation yield, recovered scalar, or challenge solve is claimed"
    }))
}

pub fn run(args: FixedArgs) -> Result<Value, String> {
    if args.stage == "preflight" {
        return native_preflight(&args.params);
    }
    let exact_ecc2k130 = exact_ecc2k130_document(&args.params).unwrap_or(false);
    let rust_preflight = if exact_ecc2k130 {
        Some(native_preflight(&args.params)?)
    } else {
        None
    };
    let script =
        PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("python/indexcalc/indexcalc_fixed.py");
    if !script.is_file() {
        return Err(format!(
            "fixed workflow engine is missing: {}",
            script.display()
        ));
    }
    let mut command = Command::new(&args.python);
    command.arg(script);
    if let Some(model) = &args.selector_model {
        command.arg("--selector-model").arg(model);
    }
    let result = command
        .arg("--params")
        .arg(&args.params)
        .arg("--dir")
        .arg(&args.dir)
        .arg("--stage")
        .arg(&args.stage)
        .arg("--solver")
        .arg(&args.solver)
        .arg("--attempts")
        .arg(args.attempts.to_string())
        .arg("--pair-budget")
        .arg(args.pair_budget.to_string())
        .arg("--query-seconds")
        .arg(args.query_seconds.to_string())
        .stdin(Stdio::null())
        .stderr(Stdio::inherit())
        .output()
        .map_err(|e| {
            format!(
                "could not run fixed workflow with {}: {e}",
                args.python.display()
            )
        })?;
    let mut report: Value = serde_json::from_slice(&result.stdout).map_err(|e| {
        format!(
            "fixed workflow exited {} without a valid JSON report: {e}",
            result.status
        )
    })?;
    if report["operation"] != "fixed" {
        return Err("fixed workflow returned an unexpected report".into());
    }
    if !result.status.success() && matches!(report["status"].as_str(), Some("complete" | "stopped"))
    {
        return Err(format!(
            "fixed workflow reported success but exited {}",
            result.status
        ));
    }
    if let Some(preflight) = rust_preflight {
        report["rust_native_preflight"] = preflight;
    }
    Ok(report)
}
