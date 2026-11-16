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
fn main() {
    let args: Vec<_> = std::env::args().collect();
    assert_eq!(args.len(), 4);
    let root = Path::new(&args[1]);
    let fixture = load(&args[2]);
    let expected = fixture["cases"].as_array().unwrap();
    assert_eq!(expected.len(), 60);
    let mut all = vec![];
    for i in 0..60 {
        let mut vectors = Vec::new();
        for arm in ["baseline", "direct"] {
            let path = root.join(format!("cold-{arm}-{i}.txt"));
            assert_eq!(
                fs::read_to_string(root.join(format!("cold-{arm}-{i}.exit"))).unwrap(),
                "0\n"
            );
            let v = record(&path);
            assert_eq!(v["population"], "separate-case-process");
            let (total, changes) = check(&v, arm, expected, &[i]);
            assert_eq!(changes.len(), 1);
            vectors.push(vector(&total));
            all.push(json!({"population":"cold","index":i,"arm":arm,"whole_source_vector":array(vectors.last().unwrap()),"online_delta":array(&vector(&changes[0]))}));
        }
        let keys: BTreeSet<_> = vectors[0]
            .keys()
            .chain(vectors[1].keys())
            .cloned()
            .collect();
        let differences=keys.into_iter().map(|k|{let b=vectors[0].get(&k).copied().unwrap_or(0);let d=vectors[1].get(&k).copied().unwrap_or(0);json!({"phase":k.0,"backend":k.1,"modulus":k.2,"operation":k.3,"baseline":b,"direct":d,"direct_minus_baseline":d as i128-b as i128})}).collect::<Vec<_>>();
        all.push(json!({"population":"cold_differences","index":i,"all_unit_keys_including_separate_diagnostics":differences}));
    }
    for arm in ["baseline", "direct"] {
        assert_eq!(
            fs::read_to_string(root.join(format!("reused-{arm}.exit"))).unwrap(),
            "0\n"
        );
        let v = record(&root.join(format!("reused-{arm}.txt")));
        assert_eq!(v["population"], "fixed-reused-context-process");
        let (total, changes) = check(&v, arm, expected, &(0..60).collect::<Vec<_>>());
        all.push(json!({"population":"reused","arm":arm,"whole_source_vector":array(&vector(&total)),"all60_online_deltas":changes.iter().map(|x|array(&vector(x))).collect::<Vec<_>>()}));
    }
    let out = json!({"source":"5ac59843a0cc6546b0f007c0bd2f79212d169c43","protocol":"01e617","cold_records":120,"reused_records":2,"every_case_and_whole_packet_checked":true,"every_cumulative_counter_monotone_and_complete":true,"all_unit_vectors":all,"scope":"exact source counts and signed differences; diagnostics and auxiliary rows remain separately keyed, no prices or runtime gain inferred"});
    fs::write(&args[3], serde_json::to_vec_pretty(&out).unwrap()).unwrap();
    println!("all120cold+2reused whole records,60expected packets,full cumulative ledgers exact; unpriced source-count differences retained");
}
