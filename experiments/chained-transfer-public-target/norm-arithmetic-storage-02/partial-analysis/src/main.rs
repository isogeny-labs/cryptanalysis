//! Whole-record/packet/cumulative-ledger checks and exact source-count differences.
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::Path,
};
type Key = (String, String, String, u64, String);
fn load(p: impl AsRef<Path>) -> Value {
    serde_json::from_slice(&fs::read(p).unwrap()).unwrap()
}
fn record(path: &Path) -> Value {
    let text = fs::read_to_string(path).unwrap();
    let rows: Vec<Value> = text
        .lines()
        .filter_map(|l| {
            l.find("N4_NORM_ARITHMETIC_CASE ")
                .map(|i| serde_json::from_str(&l[i + 24..]).unwrap())
        })
        .collect();
    assert_eq!(rows.len(), 1, "missing or duplicate complete census record");
    rows.into_iter().next().unwrap()
}
fn ledger(value: &Value) -> BTreeMap<Key, u64> {
    assert_eq!(value["schema"], "n4-source-arithmetic-v2");
    assert_eq!(value["single_thread"], true);
    let mut map = BTreeMap::new();
    for r in value["rows"].as_array().unwrap() {
        let key = (
            r["phase"].as_str().unwrap().into(),
            r["scope"].as_str().unwrap().into(),
            r["backend"].as_str().unwrap().into(),
            r["modulus"].as_u64().unwrap(),
            r["operation"].as_str().unwrap().into(),
        );
        let count = r["count"].as_u64().unwrap();
        assert_ne!(
            r["operation"], "unsupported_entry",
            "unsupported coverage cannot be an accepted census"
        );
        assert!(map.insert(key, count).is_none());
    }
    assert!(!map.is_empty());
    map
}
fn delta(before: &BTreeMap<Key, u64>, after: &BTreeMap<Key, u64>) -> BTreeMap<Key, u64> {
    for (k, v) in before {
        assert!(
            after.get(k).copied().unwrap_or(0) >= *v,
            "ledger reset or row loss"
        );
    }
    after
        .iter()
        .filter_map(|(k, v)| {
            let difference = v.checked_sub(before.get(k).copied().unwrap_or(0)).unwrap();
            (difference != 0).then(|| (k.clone(), difference))
        })
        .collect()
}
fn group(phase: &str) -> &str {
    let parts: Vec<_> = phase.split('/').collect();
    if phase.starts_with("construct.instance") {
        "construct.instance"
    } else if phase.starts_with("construct.arm") {
        "construct.arm"
    } else if phase.starts_with("validation.output") {
        "validation.output"
    } else if parts.contains(&"input.norm") {
        "input.norm"
    } else if parts.contains(&"input.order") {
        "input.order"
    } else if phase.starts_with("runtime") && parts.last() == Some(&"full.inverse") {
        "inverse.scalar"
    } else if phase.starts_with("runtime") {
        "transfer"
    } else {
        "residual"
    }
}
fn vector(rows: &BTreeMap<Key, u64>) -> BTreeMap<(String, String, u64, String), u64> {
    let mut out = BTreeMap::<_, u64>::new();
    for ((phase, _, backend, p, op), n) in rows {
        let key = (group(phase).to_string(), backend.clone(), *p, op.clone());
        let cell = out.entry(key).or_default();
        *cell = cell.checked_add(*n).unwrap();
    }
    out
}
fn array(rows: &BTreeMap<(String, String, u64, String), u64>) -> Value {
    json!(rows.iter().map(|((phase,backend,p,op),n)|json!({"phase":phase,"backend":backend,"modulus":p,"operation":op,"count":n})).collect::<Vec<_>>())
}
fn check(
    v: &Value,
    arm: &str,
    expected: &[Value],
    indices: &[usize],
) -> (BTreeMap<Key, u64>, Vec<BTreeMap<Key, u64>>) {
    assert_eq!(v["arm"], arm);
    assert_eq!(v["protocol"], "01e617");
    assert_eq!(v["source"], "5ac59843a0cc6546b0f007c0bd2f79212d169c43");
    assert_eq!(v["observer_enabled"], true);
    assert_eq!(v["covered_known_executed_field_backends"], true);
    let mut prior = ledger(&v["setup_ledger"]);
    let rows = v["all_outputs_and_full_cumulative_ledgers"]
        .as_array()
        .unwrap();
    assert_eq!(rows.len(), indices.len());
    let mut changes = vec![];
    for (row, &index) in rows.iter().zip(indices) {
        assert_eq!(row["index"], index);
        assert_eq!(row["kind"], expected[index]["kind"]);
        assert_eq!(row["input"], expected[index]["input"]);
        assert_eq!(row["expected"], expected[index]["expected"]);
        assert_eq!(
            row["actual"], expected[index]["expected"],
            "whole field/model/key differs"
        );
        let next = ledger(&row["complete_cumulative_ledger_after_output_validation"]);
        changes.push(delta(&prior, &next));
        prior = next;
    }
    assert_eq!(prior, ledger(&v["final_ledger"]));
    (prior, changes)
}
// Retrospective partial report after actual cold timeout b5fd45. This does not
// weaken or replace the original full120+2 comparator, which rejected101.
fn differences(
    b: &BTreeMap<(String, String, u64, String), u64>,
    d: &BTreeMap<(String, String, u64, String), u64>,
) -> Value {
    let keys: BTreeSet<_> = b.keys().chain(d.keys()).cloned().collect();
    json!(keys.into_iter().map(|k|{let baseline=b.get(&k).copied().unwrap_or(0);let direct=d.get(&k).copied().unwrap_or(0);json!({"phase":k.0,"backend":k.1,"modulus":k.2,"operation":k.3,"baseline":baseline,"direct":direct,"direct_minus_baseline":direct as i128-baseline as i128})}).collect::<Vec<_>>())
}
fn exit(p: &Path) -> Option<i32> {
    fs::read_to_string(p)
        .ok()
        .map(|s| s.trim().parse().unwrap())
}
fn main() {
    let args: Vec<_> = std::env::args().collect();
    assert_eq!(args.len(), 4);
    let root = Path::new(&args[1]);
    let fixture = load(&args[2]);
    let cases = fixture["cases"].as_array().unwrap();
    assert_eq!(cases.len(), 60);
    assert_eq!(exit(&root.join("cold-panel.exit")), Some(124));
    assert_eq!(exit(&root.join("reused-panel.exit")), Some(0));
    let mut cold_records = vec![];
    let mut missing = vec![];
    let mut cold_differences = vec![];
    for i in 0..60 {
        let mut complete = BTreeMap::new();
        for arm in ["baseline", "direct"] {
            let stem = format!("cold-{arm}-{i}");
            let status = exit(&root.join(format!("{stem}.exit")));
            if status != Some(0) {
                missing.push(json!({"index":i,"arm":arm,"actual_exit":status,"raw_log_exists":root.join(format!("{stem}.txt")).exists(),"accepted":false}));
                continue;
            }
            let v = record(&root.join(format!("{stem}.txt")));
            assert_eq!(v["population"], "separate-case-process");
            let (total, delta) = check(&v, arm, cases, &[i]);
            assert_eq!(delta.len(), 1);
            let t = vector(&total);
            let online = vector(&delta[0]);
            cold_records.push(json!({"index":i,"arm":arm,"population":"observed_prefix_of_incomplete_cold_panel","whole_source_vector":array(&t),"online_delta":array(&online)}));
            complete.insert(arm, t);
        }
        if complete.len() == 2 {
            cold_differences.push(json!({"index":i,"scope":"this observed pair only, incomplete full cold population","all_units":differences(&complete["baseline"],&complete["direct"])}));
        }
    }
    assert!(
        !missing.is_empty(),
        "this report must remain explicitly incomplete"
    );
    let mut reused = vec![];
    let mut reuse_deltas = vec![];
    let mut reuse_totals = vec![];
    for arm in ["baseline", "direct"] {
        assert_eq!(exit(&root.join(format!("reused-{arm}.exit"))), Some(0));
        let v = record(&root.join(format!("reused-{arm}.txt")));
        assert_eq!(v["population"], "fixed-reused-context-process");
        let (total, delta) = check(&v, arm, cases, &(0..60).collect::<Vec<_>>());
        assert_eq!(delta.len(), 60);
        let online: Vec<_> = delta.iter().map(vector).collect();
        let t = vector(&total);
        reused.push(json!({"arm":arm,"whole_source_vector":array(&t),"all60_online_deltas":online.iter().map(array).collect::<Vec<_>>()}));
        reuse_deltas.push(online);
        reuse_totals.push(t);
    }
    let per_case:Vec<_>=(0..60).map(|i|json!({"index":i,"kind":cases[i]["kind"],"all_unit_keys":differences(&reuse_deltas[0][i],&reuse_deltas[1][i])})).collect();
    let out = json!({"schema":"n4-norm-arithmetic-incomplete-panel-v1","source":"5ac59843a0cc6546b0f007c0bd2f79212d169c43","prospective_protocol":"01e617","analysis_design":"retrospective partial reporting after actual timeout; original full comparator still rejects101","full_cold_population_accepted":false,"cold_panel_actual_exit":124,"all_actual_complete_cold_records":cold_records,"all_missing_or_incomplete_cold_records":missing,"actual_complete_cold_pair_differences":cold_differences,"complete_reused_context_processes":2,"each_reused_context_all60_packets_and_monotone_ledgers_checked":true,"reused_all_source_vectors_and_deltas":reused,"reused_total_differences":differences(&reuse_totals[0],&reuse_totals[1]),"reused_per_case_differences":per_case,"scope":"counts are unpriced source operations only. API, encoding, auxiliary and primitive leaves stay separately keyed. Never extrapolate missing cold records, combine populations, sum heterogeneous operations into cost, or infer hardware/ECDLP gain."});
    fs::write(&args[3], serde_json::to_vec_pretty(&out).unwrap()).unwrap();
    println!("partial report: {} actual complete cold records; {} missing/incomplete; two full60-case reused processes; full cold120 comparison remains rejected",cold_records.len(),missing.len());
}
