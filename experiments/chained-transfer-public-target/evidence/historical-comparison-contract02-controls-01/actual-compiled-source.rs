//! Whole-record historical equality under published contract b5e431/5493385.
//! Original same-run auditors and every raw input remain unchanged.
#[allow(dead_code)]
#[path = "../../../../../../crypto/src/hash/sha256.rs"]
mod original_sha256;
use serde_json::{json, Value};
use std::{env, fs, path::Path, process::ExitCode};

type Result<T> = std::result::Result<T, String>;
const PHASES: [&str; 7] = [
    "fb",
    "relations",
    "matrix",
    "linear_algebra",
    "log_recovery",
    "descent",
    "verify",
];
fn family(label: &str) -> Result<(usize, &'static str, &'static str, &'static [&'static str])> {
    match label {
        "original-ic" => Ok((
            100,
            "N4_ORIGINAL_MODEL_IC_ATTEMPT",
            "N4_ORIGINAL_MODEL_IC_INPUT",
            &["report"],
        )),
        "original-sampler" => Ok((
            101,
            "N4_ORIGINAL_FIXED_SAMPLER_ATTEMPT",
            "N4_ORIGINAL_FIXED_SAMPLER_INPUT",
            &["original", "candidate"],
        )),
        _ => Err("unknown frozen record family".into()),
    }
}
fn elapsed(value: &Value, path: &str) -> Result<f64> {
    let v = value
        .as_f64()
        .ok_or_else(|| format!("missing/non-numeric elapsed value {path}"))?;
    if !v.is_finite() || v < 0.0 {
        return Err(format!("invalid elapsed value {path}"));
    }
    Ok(v)
}
fn project(value: &mut Value, label: &str) -> Result<Vec<Value>> {
    let (count, attempt_kind, _, reports) = family(label)?;
    let records = value.as_array_mut().ok_or("whole record array required")?;
    if records.len() != count {
        return Err(format!("whole record count must be {count}"));
    }
    let mut attempts = 0;
    let mut slots = Vec::new();
    for (ri, row) in records.iter_mut().enumerate() {
        if row["kind"].as_str() != Some(attempt_kind) {
            continue;
        }
        attempts += 1;
        for key in reports {
            let report = row["data"]
                .get_mut(*key)
                .ok_or_else(|| format!("missing report {ri}.{key}"))?;
            let phases = report
                .get_mut("phases")
                .and_then(Value::as_array_mut)
                .ok_or("phase array required")?;
            if phases.len() != PHASES.len() {
                return Err("exactly seven original phases required".into());
            }
            for (pi, phase) in phases.iter_mut().enumerate() {
                if phase["phase"].as_str() != Some(PHASES[pi]) {
                    return Err("original phase order/name mismatch".into());
                }
                let path = format!("$[{ri}].data.{key}.phases[{pi}].wall");
                let v = phase.get_mut("wall").ok_or("missing wall field")?;
                let seconds = elapsed(v, &path)?;
                slots.push(json!({"path":path,"seconds":seconds}));
                *v = Value::Null;
            }
            let stats = report
                .get_mut("stats")
                .and_then(Value::as_array_mut)
                .ok_or("statistics array required")?;
            let mut totals = 0;
            for (si, stat) in stats.iter_mut().enumerate() {
                let pair = stat.as_array_mut().ok_or("statistic pair required")?;
                if pair.len() != 2 || !pair[0].is_string() {
                    return Err("malformed statistic pair".into());
                }
                if pair[0].as_str() == Some("wall_total") {
                    totals += 1;
                    let path = format!("$[{ri}].data.{key}.stats[{si}][1]");
                    let seconds = elapsed(&pair[1], &path)?;
                    slots.push(json!({"path":path,"seconds":seconds}));
                    pair[1] = Value::Null;
                }
            }
            if totals != 1 {
                return Err("exactly one wall_total statistic required".into());
            }
        }
    }
    if attempts != 60 {
        return Err("all sixty attempt records required".into());
    }
    Ok(slots)
}
fn hash(data: &[u8]) -> String {
    original_sha256::sha256(data)
        .iter()
        .map(|v| format!("{v:02x}"))
        .collect()
}
fn compare(label: &str, expected: &Path, actual: &Path, output: &Path) -> Result<()> {
    if output.exists() {
        return Err("accepted output must not already exist".into());
    }
    let a_bytes = fs::read(expected).map_err(|e| e.to_string())?;
    let b_bytes = fs::read(actual).map_err(|e| e.to_string())?;
    let mut a: Value = serde_json::from_slice(&a_bytes).map_err(|e| e.to_string())?;
    let mut b: Value = serde_json::from_slice(&b_bytes).map_err(|e| e.to_string())?;
    let old_times = project(&mut a, label)?;
    let new_times = project(&mut b, label)?;
    if a != b {
        return Err("whole historical non-time fields differ; no accepted output".into());
    }
    let receipt = json!({"schema":"original-fixed-IC-historical-equality/v1","family":label,
        "contract":"b5e431/5493385305de052bc6e84cc9dc7fe7bf08596436",
        "whole_records":family(label)?.0,"all_non_time_values_equal":true,
        "historical_whole_sha256":hash(&a_bytes),"fresh_whole_sha256":hash(&b_bytes),
        "historical_elapsed_values":old_times,"fresh_elapsed_values":new_times,
        "all_counters_and_non_time_statistics_compared_exactly":true,
        "inputs_rewritten":false,"scope":"unsigned whole-record equality; elapsed values retained unpriced"});
    fs::write(output, serde_json::to_vec_pretty(&receipt).unwrap()).map_err(|e| e.to_string())?;
    println!("whole historical non-time equality: {label}");
    Ok(())
}
fn report_mut<'a>(value: &'a mut Value, label: &str) -> Result<&'a mut Value> {
    let (_, kind, _, keys) = family(label)?;
    let rows = value.as_array_mut().ok_or("record array required")?;
    let row = rows
        .iter_mut()
        .find(|v| v["kind"].as_str() == Some(kind))
        .ok_or("attempt required")?;
    row["data"].get_mut(keys[0]).ok_or("report required".into())
}
fn mutations(label: &str, input: &Path, directory: &Path) -> Result<()> {
    if directory.exists() {
        return Err("control directory must be new".into());
    }
    let value: Value = serde_json::from_slice(&fs::read(input).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())?;
    let mut admitted = value.clone();
    project(&mut admitted, label)?;
    fs::create_dir(directory).map_err(|e| e.to_string())?;
    let mut rows = Vec::new();
    for name in [
        "missing-record-class",
        "changed-scalar",
        "changed-counter",
        "unexpected-report-field",
        "timing-only",
    ] {
        let mut changed = value.clone();
        match name {
            "missing-record-class" => {
                let (_, _, kind, _) = family(label)?;
                changed
                    .as_array_mut()
                    .unwrap()
                    .retain(|v| v["kind"].as_str() != Some(kind));
            }
            "changed-scalar" => {
                let r = report_mut(&mut changed, label)?;
                let k = r["k_found"].as_u64().ok_or("scalar required")?;
                r["k_found"] = json!(k + 1);
            }
            "changed-counter" => {
                let r = report_mut(&mut changed, label)?;
                let v = r["phases"][0]["mul"].as_u64().ok_or("counter required")?;
                r["phases"][0]["mul"] = json!(v + 1);
            }
            "unexpected-report-field" => {
                report_mut(&mut changed, label)?
                    .as_object_mut()
                    .unwrap()
                    .insert("unexpected_historical_field".into(), json!(true));
            }
            "timing-only" => {
                let r = report_mut(&mut changed, label)?;
                r["phases"][0]["wall"] =
                    json!(elapsed(&r["phases"][0]["wall"], "positive-control")? + 1.0);
                for pair in r["stats"].as_array_mut().unwrap() {
                    if pair[0].as_str() == Some("wall_total") {
                        pair[1] = json!(elapsed(&pair[1], "positive-control-total")? + 1.0);
                    }
                }
            }
            _ => unreachable!(),
        }
        let bytes = serde_json::to_vec(&changed).unwrap();
        fs::write(directory.join(format!("{name}.json")), &bytes).map_err(|e| e.to_string())?;
        rows.push(json!({"name":name,"bytes":bytes.len(),"sha256":hash(&bytes),"expected_exit":if name=="timing-only"{0}else{1}}));
    }
    fs::write(
        directory.join("whole-controls.json"),
        serde_json::to_vec_pretty(&rows).unwrap(),
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}
fn run() -> Result<()> {
    let a: Vec<_> = env::args().collect();
    match a.get(1).map(String::as_str) {
        Some("--compare") if a.len() == 6 => {
            compare(&a[2], Path::new(&a[3]), Path::new(&a[4]), Path::new(&a[5]))
        }
        Some("--mutations") if a.len() == 5 => mutations(&a[2], Path::new(&a[3]), Path::new(&a[4])),
        _ => Err(
            "usage: --compare FAMILY EXPECTED ACTUAL OUT | --mutations FAMILY INPUT NEWDIR".into(),
        ),
    }
}
fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("historical verifier: {e}");
            ExitCode::FAILURE
        }
    }
}
