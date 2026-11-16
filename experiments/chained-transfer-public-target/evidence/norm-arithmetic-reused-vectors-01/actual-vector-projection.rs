//! Rendering projection only; all numerical grouping is native and unpriced.
use serde_json::{json, Value};
use std::{collections::BTreeMap, fs};
fn diagnostic(b: &str, op: &str) -> bool {
    b.ends_with(".api")
        || b.ends_with(".aux")
        || b.ends_with(".encoding")
        || op.ends_with("_api")
        || op == "unsupported_entry"
}
fn main() {
    let a: Vec<_> = std::env::args().collect();
    assert_eq!(a.len(), 3);
    let input: Value = serde_json::from_slice(&fs::read(&a[1]).unwrap()).unwrap();
    assert_eq!(input["schema"], "n4-norm-arithmetic-incomplete-panel-v1");
    assert_eq!(input["full_cold_population_accepted"], false);
    assert_eq!(input["complete_reused_context_processes"], 2);
    let mut arms = vec![];
    for arm in input["reused_all_source_vectors_and_deltas"]
        .as_array()
        .unwrap()
    {
        let mut all: u128 = 0;
        let mut kept: u128 = 0;
        let mut excluded: u128 = 0;
        let mut phases = BTreeMap::<String, BTreeMap<String, u64>>::new();
        let mut classified = vec![];
        for row in arm["whole_source_vector"].as_array().unwrap() {
            let b = row["backend"].as_str().unwrap();
            let op = row["operation"].as_str().unwrap();
            let p = row["modulus"].as_u64().unwrap();
            let n = row["count"].as_u64().unwrap();
            all = all.checked_add(n as u128).unwrap();
            let diag = diagnostic(b, op);
            if p == 223 && !diag {
                let cell = phases
                    .entry(row["phase"].as_str().unwrap().into())
                    .or_default()
                    .entry(op.into())
                    .or_default();
                *cell = cell.checked_add(n).unwrap();
                kept = kept.checked_add(n as u128).unwrap();
            } else {
                excluded = excluded.checked_add(n as u128).unwrap();
            }
            let mut r = row.clone();
            r["diagnostic_or_auxiliary"] = json!(diag);
            classified.push(r);
        }
        assert_eq!(
            all,
            kept.checked_add(excluded).unwrap(),
            "all event rows conserved including excluded diagnostics and moduli"
        );
        let p223: Vec<_> = phases
            .into_iter()
            .map(|(phase, counts)| json!({"phase":phase,"all_operations":counts}))
            .collect();
        arms.push(json!({"arm":arm["arm"],"all_classified_source_vectors":classified,"q223_by_phase":p223,"conservation_only_not_cost":{"all_event_counts":all,"included_q223_leaf_events":kept,"excluded_diagnostic_auxiliary_other_modulus_events":excluded}}));
    }
    let out = json!({"schema":"n4-norm-arithmetic-reused-render-v1","status":"incomplete cold population; complete fixed60-case reuse processes only","protocol":"01e617","cold_complete":12,"cold_missing_or_incomplete":108,"cold_accepted":false,"reused_processes":2,"operations_per_reused_process":60,"unit":"unpriced executed source-operation events; q223 coefficient/word leaves, not machine instructions or calibrated field-M","all_arms":arms,"diagnostic_rule":"original .api/.aux/_api classification plus new .encoding. All excluded rows remain in full classified vectors and conservation checks.","all_unit_differences_original_partial_record":"all-partial-vectors.json","interpretation":"No operation prices, time ratio, cold extrapolation, cross-population averaging or ECDLP advantage. All60 individual online vectors/differences remain in original partial analysis."});
    fs::write(&a[2], serde_json::to_vec_pretty(&out).unwrap()).unwrap();
    for arm in out["all_arms"].as_array().unwrap() {
        for row in arm["q223_by_phase"].as_array().unwrap() {
            println!("{} {} {}", arm["arm"], row["phase"], row["all_operations"]);
        }
    }
}
