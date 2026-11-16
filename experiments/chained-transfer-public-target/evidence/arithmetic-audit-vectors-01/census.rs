//! Exact aggregation of the retained source-operation census. No prices or ratios.
use serde_json::{json, Value};
use std::{collections::BTreeMap, env, fs};
fn group(scope: &str) -> &'static str {
    if scope.starts_with("solver-original-") {
        "solver-original"
    } else if scope.starts_with("solver-candidate-") {
        "solver-candidate"
    } else if scope.starts_with("sample-original-") {
        "scalar-panel-original"
    } else if scope.starts_with("sample-candidate-") {
        "scalar-panel-candidate"
    } else if scope.starts_with("prepare-") {
        "public-G-preparation"
    } else if scope.starts_with("verification-") {
        "independent-final-verification"
    } else if scope.starts_with("primitive-") || scope.starts_with("corpus-") {
        "primitive-controls-and-references"
    } else if scope.starts_with("model-") {
        "shared-model-setup-and-test-validation"
    } else if scope == "setup" {
        "shared-source-setup"
    } else {
        "residual"
    }
}
fn diagnostic(backend: &str, op: &str) -> bool {
    backend.ends_with(".api")
        || backend.ends_with(".aux")
        || op.ends_with("_api")
        || op == "unsupported_entry"
}
fn main() {
    let args: Vec<_> = env::args().collect();
    assert_eq!(args.len(), 3);
    let raw = fs::read_to_string(&args[1]).unwrap();
    let records: Vec<Value> = raw
        .lines()
        .filter_map(|line| {
            line.split_once("N4_ARITHMETIC_CENSUS ")
                .map(|(_, s)| serde_json::from_str(s).unwrap())
        })
        .collect();
    assert_eq!(records.len(), 1, "one full census required");
    let rows = records[0]["rows"].as_array().unwrap();
    let mut totals: BTreeMap<(String, String, u64, String, bool), u64> = BTreeMap::new();
    let mut scopes: BTreeMap<(String, String, u64, String, bool), u64> = BTreeMap::new();
    let mut all = 0u128;
    let mut control = 0u128;
    for row in rows {
        let scope = row["scope"].as_str().unwrap();
        let backend = row["backend"].as_str().unwrap();
        let p = row["modulus"].as_u64().unwrap();
        let op = row["operation"].as_str().unwrap();
        let n = row["count"].as_u64().unwrap();
        assert!(n > 0);
        assert_ne!(op, "unsupported_entry", "uncovered executed backend");
        all = all.checked_add(n as u128).unwrap();
        for (map, label) in [
            (&mut totals, group(scope).to_owned()),
            (&mut scopes, scope.to_owned()),
        ] {
            let entry = map
                .entry((label, backend.into(), p, op.into(), diagnostic(backend, op)))
                .or_default();
            *entry = entry.checked_add(n).unwrap();
        }
    }
    let table:Vec<_>=totals.iter().map(|((phase,backend,p,op,diag),n)|{
        control=control.checked_add(*n as u128).unwrap();
        json!({"group":phase,"backend":backend,"modulus":p,"operation":op,"diagnostic_or_auxiliary":diag,"count":n})
    }).collect();
    assert_eq!(all, control, "no census row may be dropped");
    let per_scope:Vec<_>=scopes.iter().map(|((scope,backend,p,op,diag),n)|json!({"scope":scope,"backend":backend,"modulus":p,"operation":op,"diagnostic_or_auxiliary":diag,"count":n})).collect();
    let mut sample_rows = vec![];
    for target in ["[1, 0]", "[1, 1]", "[2, 1]"] {
        for arm in ["original", "candidate"] {
            let label = format!("sample-{arm}-{target}");
            let entries: Vec<_> = per_scope
                .iter()
                .filter(|r| r["scope"] == label)
                .cloned()
                .collect();
            assert!(!entries.is_empty());
            sample_rows.push(json!({"target":target,"arm":arm,"samples":75,"counts":entries}));
        }
    }
    let doc = json!({"schema":"n4-arithmetic-summary-v1","source_rows":rows.len(),"all_event_counts_conserved":true,
        "unit":"executed source-level coefficient/word modular arithmetic; API and auxiliary rows separate; no calibrated field-M price",
        "limitations":["shared model group includes setup and test validation","solver arms share cold setup","primitive reference shares instrumented Zp/fpm","hash allocation Big and integer bookkeeping remain unpriced","not machine instructions; no S, ratio or stage-win claim"],
        "grouped":table,"per_scope":per_scope,"scalar_panels":sample_rows});
    fs::write(&args[2], serde_json::to_vec_pretty(&doc).unwrap()).unwrap();
    println!("All{}source rows retained and counts conserved; six75-sample vectors, both60-attempt solver arms, preparation, verification and residual/control work explicit; unpriced.",rows.len());
}
