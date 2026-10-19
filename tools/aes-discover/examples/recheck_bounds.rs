//! Recompute validation bounds from preserved counts without replaying AES or
//! drawing any new samples. Intended for post-review corrections to the
//! statistical analysis of a frozen run.
use aes_discover::{digest, stats};
use serde_json::{json, Value};
use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args_os().collect();
    if args.len() != 2 {
        return Err("usage: recheck_bounds RUN-DIRECTORY".into());
    }
    let directory = Path::new(&args[1]);
    let mut paths: Vec<_> = fs::read_dir(directory)?
        .map(|entry| entry.map(|entry| entry.path()))
        .collect::<Result<_, _>>()?;
    paths.sort();

    let mut families = Vec::new();
    for path in paths {
        let name = path.file_name().unwrap().to_string_lossy();
        if !name.ends_with("-validation.json") {
            continue;
        }
        let bytes = fs::read(&path)?;
        let report: Value = serde_json::from_slice(&bytes)?;
        let n = report["validation_plan"]["samples_per_key_per_event"]
            .as_u64()
            .ok_or("missing samples per key per event")?;
        let keys = report["validation_plan"]["keys"]
            .as_u64()
            .ok_or("missing key count")?;
        let alpha = report["validation_plan"]["alpha"]
            .as_f64()
            .ok_or("missing alpha")?;
        let tests = report["family_tests"]
            .as_u64()
            .ok_or("missing test count")? as usize;
        let events = tests as u64 / (2 * keys);
        let q = 2 * n * events;
        let mut candidate_passes: BTreeMap<String, bool> = BTreeMap::new();
        let mut control_pass = true;
        let mut rows = Vec::new();

        for row in report["rows"].as_array().ok_or("missing rows")? {
            let candidate_id = row["candidate_id"].as_str().ok_or("missing candidate ID")?;
            let primary_hits = row["primary_hits"].as_u64().ok_or("missing primary hits")?;
            let control_hits = row["control_hits"].as_u64().ok_or("missing control hits")?;
            let p = row["ideal_pair_probability"]
                .as_f64()
                .ok_or("missing null probability")?;
            let primary_bound = stats::corrected_bound(primary_hits, n, p, tests, q);
            let control_bound = stats::corrected_bound(control_hits, n, p, tests, q);
            let direction_matches = row["direction_matches"]
                .as_bool()
                .ok_or("missing direction")?;
            let candidate_pass = primary_bound <= alpha && direction_matches;
            candidate_passes
                .entry(candidate_id.to_string())
                .and_modify(|pass| *pass &= candidate_pass)
                .or_insert(candidate_pass);
            control_pass &= control_bound > alpha;
            rows.push(json!({
                "candidate_id": candidate_id,
                "key_index": row["key_index"],
                "primary_hits": primary_hits,
                "control_hits": control_hits,
                "samples": n,
                "ideal_pair_probability": p,
                "direction_matches": direction_matches,
                "primary_family_bound": primary_bound,
                "control_family_bound": control_bound,
                "candidate_pass": candidate_pass
            }));
        }
        let validated_candidates: Vec<_> = candidate_passes
            .iter()
            .filter_map(|(id, pass)| pass.then_some(id.clone()))
            .collect();
        let mut previous_validated_candidates: Vec<_> = report["validated_candidates"]
            .as_array()
            .ok_or("missing previous validated candidate IDs")?
            .iter()
            .map(|id| {
                id.as_str()
                    .map(str::to_owned)
                    .ok_or("invalid previous candidate ID")
            })
            .collect::<Result<_, _>>()?;
        previous_validated_candidates.sort();
        let classification_unchanged = previous_validated_candidates == validated_candidates;
        families.push(json!({
            "file": name,
            "raw_sha256": digest(&bytes),
            "alpha": alpha,
            "family_tests": tests,
            "prp_coupling_slack_per_test": stats::coupling_slack(q),
            "previous_validated_candidates": previous_validated_candidates,
            "classification_unchanged": classification_unchanged,
            "corrected_validated_candidates": validated_candidates,
            "random_control_passed": control_pass,
            "rows": rows
        }));
    }
    println!(
        "{}",
        serde_json::to_string_pretty(&json!({
            "schema": "aes-discover/statistical-recheck/v1",
            "method": "two-sided Bernoulli Chernoff bound with separate lower and upper KL divergences, plus the original finite-query PRP coupling slack and Bonferroni family correction",
            "scope": "reanalysis of preserved counts only; no cipher calls, new samples, search, or experiment replay",
            "families": families
        }))?
    );
    Ok(())
}

fn main() {
    if let Err(e) = run() {
        eprintln!("recheck_bounds: {e}");
        std::process::exit(2);
    }
}
