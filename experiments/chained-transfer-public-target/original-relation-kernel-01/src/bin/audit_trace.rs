//! Whole passive capture/parity auditor, separate from rank/character interpretation.
#[allow(dead_code)]
mod inherited {
    include!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/derived/native_record_auditor.rs"
    ));
    pub fn whole(text: &str) -> Vec<serde_json::Value> {
        records(text)
    }
}
#[allow(dead_code)]
#[path = "../../../../../../crypto/src/hash/sha256.rs"]
mod original_sha256;
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    env, fs,
};
type Row = Vec<(usize, u64)>;
const ELL: u64 = 2_773_073;
fn digest(b: &[u8]) -> String {
    original_sha256::sha256(b)
        .iter()
        .map(|x| format!("{x:02x}"))
        .collect()
}
fn read(p: &str) -> Value {
    serde_json::from_slice(&fs::read(p).unwrap()).unwrap()
}
fn projected_report(mut v: Value) -> Value {
    let names = [
        "fb",
        "relations",
        "matrix",
        "linear_algebra",
        "log_recovery",
        "descent",
        "verify",
    ];
    let phases = v["phases"].as_array_mut().unwrap();
    assert_eq!(phases.len(), names.len());
    for (p, name) in phases.iter_mut().zip(names) {
        assert_eq!(p["phase"], name);
        let w = p["wall"].as_f64().unwrap();
        assert!(w.is_finite() && w >= 0.0);
        p["wall"] = Value::Null;
    }
    let mut total = 0;
    for p in v["stats"].as_array_mut().unwrap() {
        let p = p.as_array_mut().unwrap();
        assert_eq!(p.len(), 2);
        assert!(p[0].is_string());
        if p[0] == "wall_total" {
            let t = p[1].as_f64().unwrap();
            assert!(t.is_finite() && t >= 0.0);
            p[1] = Value::Null;
            total += 1;
        }
    }
    assert_eq!(total, 1);
    v
}
fn rows(v: &Value, n: usize) -> Vec<Row> {
    let rows: Vec<Row> = serde_json::from_value(v.clone()).unwrap();
    assert!(rows.iter().flatten().all(|(c, _)| *c < n));
    rows
}
fn apply(row: &Row, z: &[u64]) -> u64 {
    row.iter().fold(0u64, |a, &(c, v)| {
        ((a as u128 + ((v % ELL) as u128 * (z[c] % ELL) as u128) % ELL as u128) % ELL as u128)
            as u64
    })
}
fn main() {
    let args: Vec<_> = env::args().collect();
    assert_eq!(args.len(), 7, "--audit BASELINE NATIVE TRACE JOURNAL OUT");
    assert_eq!(args[1], "--audit");
    assert!(!std::path::Path::new(&args[6]).exists());
    let baseline = read(&args[2]);
    let actual = inherited::whole(&fs::read_to_string(&args[3]).unwrap());
    let expected = baseline.as_array().unwrap();
    assert_eq!(expected.len(), 100);
    assert_eq!(actual.len(), 100);
    let mut native_attempts = BTreeMap::new();
    for (old, new) in expected.iter().zip(&actual) {
        assert_eq!(old["kind"], new["kind"]);
        match old["kind"].as_str().unwrap() {
            "N4_ORIGINAL_MODEL_IC_ATTEMPT" => {
                let mut a = old["data"].clone();
                let mut b = new["data"].clone();
                assert_eq!(
                    projected_report(a["report"].take()),
                    projected_report(b["report"].take()),
                    "whole report/counter/non-time parity"
                );
                assert_eq!(a, b, "whole input/scalar/check parity");
                let d = &new["data"];
                let key = [
                    d["side"].as_u64().unwrap() as usize,
                    d["public_index"].as_u64().unwrap() as usize,
                    d["attempt"].as_u64().unwrap() as usize,
                ];
                assert!(native_attempts.insert(key, d.clone()).is_none());
            }
            "N4_ORIGINAL_MODEL_IC_SCOPE" => {
                let mut a = old["data"].clone();
                let mut b = new["data"].clone();
                assert_eq!(
                    a["solver_source"],
                    "literal existing new-target class_solver.rs, no edits"
                );
                assert_eq!(b["solver_source"],"exact original algorithm plus the published passive insertion manifest; separate diagnostic provenance");
                a.as_object_mut().unwrap().remove("solver_source");
                b.as_object_mut().unwrap().remove("solver_source");
                assert_eq!(a, b, "only declared truthful solver provenance differs");
            }
            _ => assert_eq!(
                old, new,
                "entire constructor/input/case/rejection/target record parity"
            ),
        }
    }
    assert_eq!(native_attempts.len(), 60);
    let trace = read(&args[4]);
    assert_eq!(
        trace["schema"],
        "original-fixed-model-passive-relation-trace/v1"
    );
    assert_eq!(trace["protocol"], "8e7e1c/CBC published before code");
    let calls = trace["whole_calls"].as_array().unwrap();
    assert_eq!(calls.len(), 60);
    assert_eq!(trace["models"].as_array().unwrap().len(), 3);
    let journal: Vec<Value> = fs::read_to_string(&args[5])
        .unwrap()
        .lines()
        .map(|s| serde_json::from_str(s).unwrap())
        .collect();
    assert_eq!(journal.len(), 660);
    let mut identities = BTreeSet::new();
    let mut position = 0;
    let mut diagnostics = Vec::new();
    for call in calls {
        let id: [usize; 3] = serde_json::from_value(call["identity"].clone()).unwrap();
        assert!(id[0] < 3 && id[1] < 5 && id[2] < 4 && identities.insert(id));
        let native = &native_attempts[&id];
        assert_eq!(call["generator"], native["generator"]);
        assert_eq!(call["target"], native["target"]);
        assert_eq!(
            call["report"], native["report"],
            "trace report includes exact same-run raw timings"
        );
        assert_eq!(call["ell"], ELL);
        assert_eq!(call["q"], 223);
        assert_eq!(call["seed"], 102 + id[2]);
        let n = [30, 36, 48, 64][id[2]];
        assert_eq!(call["params"]["nfb"], n);
        assert_eq!(call["params"]["rows_mult"], 1.2);
        assert_eq!(call["params"]["max_desc"], 100000);
        assert_eq!(call["params"]["sge"], false);
        assert_eq!(call["params"]["maxw"], 12);
        assert_eq!(call["params"]["lp2"], true);
        let available = &call["available"];
        let fb = available["factor_base"].as_array().unwrap();
        assert_eq!(fb.len(), n);
        assert_eq!(available["columns"], n);
        assert_eq!(available["eta_column"], n - 1);
        assert_eq!(fb[0], trace["models"][id[0]]["P0"]);
        assert_eq!(call["model"], trace["models"][id[0]]["model"]);
        let mut all = rows(&available["full_rows"], n);
        assert!(!all.is_empty());
        all.extend(rows(&available["combined_lp_cycle_rows"], n));
        assert!(available["graph"].is_object());
        let selected = &call["selected"];
        let original = rows(&selected["original_rows"], n);
        let held = rows(&selected["all_heldout_rows"], n);
        assert!(held.len() <= 60);
        let mut remaining = BTreeMap::<Row, usize>::new();
        for row in &all {
            *remaining.entry(row.clone()).or_default() += 1;
        }
        for row in original.iter().chain(&held) {
            let count = remaining
                .get_mut(row)
                .expect("selected/heldout row was not available");
            assert!(*count > 0);
            *count -= 1;
        }
        let used: Vec<bool> = serde_json::from_value(selected["active"].clone()).unwrap();
        let remap: Vec<u32> = serde_json::from_value(selected["remap"].clone()).unwrap();
        assert_eq!(used.len(), n);
        assert_eq!(remap.len(), n);
        let active = used.iter().filter(|&&v| v).count();
        let mut next = 0;
        for i in 0..n {
            if used[i] {
                assert_eq!(remap[i] as usize, next);
                next += 1;
            } else {
                assert_eq!(remap[i], u32::MAX);
            }
        }
        let mapped = rows(&selected["remapped_rows"], active);
        let recomputed: Vec<Row> = original
            .iter()
            .map(|row| {
                row.iter()
                    .map(|&(c, v)| {
                        assert!(used[c]);
                        (remap[c] as usize, v)
                    })
                    .collect()
            })
            .collect();
        assert_eq!(mapped, recomputed);
        let kernel = &call["kernel"];
        assert_eq!(kernel["active"], selected["active"]);
        assert_eq!(kernel["remap"], selected["remap"]);
        let z: Vec<u64> = serde_json::from_value(kernel["actual_vector"].clone()).unwrap();
        assert_eq!(z.len(), active);
        assert!(z.iter().any(|&v| v != 0));
        assert!(z.iter().all(|&v| v < ELL));
        assert!(mapped.iter().all(|r| apply(r, &z) == 0));
        let table: Vec<(u64, u64)> =
            serde_json::from_value(call["known_logs"]["entire_known_point_log_table"].clone())
                .unwrap();
        assert!(!table.is_empty());
        assert!(table.windows(2).all(|v| v[0].0 < v[1].0));
        assert!(table.iter().all(|v| v.1 < ELL));
        let starts = call["descent_starts"]["three_raw_canonical_class_keys"]
            .as_array()
            .unwrap();
        assert_eq!(starts.len(), 3);
        assert!(starts.iter().all(|v| v.as_array().unwrap().len() == 19));
        let splits = call["descent_splits"].as_array().unwrap();
        assert_eq!(splits.len(), 3);
        let ys: Vec<u64> = serde_json::from_value(call["recovery"]["all_three_y"].clone()).unwrap();
        assert_eq!(ys.len(), 3);
        for (leg, split) in splits.iter().enumerate() {
            assert_eq!(split["leg"], leg);
            assert_eq!(split["computed_y"], ys[leg]);
            assert_eq!(split["entire_split_points"].as_array().unwrap().len(), 3);
            assert!(split["entire_added_factor_base_indices"]
                .as_array()
                .unwrap()
                .iter()
                .all(|v| (v.as_u64().unwrap() as usize) < n));
        }
        let den = call["recovery"]["denominator"].as_u64().unwrap();
        let k = call["recovery"]["candidate"].as_u64().unwrap();
        assert_eq!(den, (ys[1] + ELL - ys[0]) % ELL);
        assert_ne!(den, 0);
        assert_eq!(
            (k as u128 * den as u128 % ELL as u128) as u64,
            (ys[2] + ELL - ys[0]) % ELL
        );
        assert_eq!(call["report"]["k_found"], k);
        let stages = [
            "begin",
            "available",
            "selected",
            "kernel",
            "known_logs",
            "descent_starts",
            "descent_split",
            "descent_split",
            "descent_split",
            "recovery",
            "finish",
        ];
        for (index, stage) in stages.iter().enumerate() {
            let row = &journal[position];
            position += 1;
            assert_eq!(row["stage"], *stage);
            assert_eq!(row["identity"], call["identity"]);
            if *stage == "begin" {
                let mut wanted = serde_json::Map::new();
                for name in [
                    "identity",
                    "field",
                    "model",
                    "generator",
                    "target",
                    "ell",
                    "q",
                    "quartic",
                    "params",
                    "seed",
                ] {
                    wanted.insert(name.into(), call[name].clone());
                }
                assert_eq!(row["data"], Value::Object(wanted));
            } else if *stage == "descent_split" {
                assert_eq!(row["data"], splits[index - 6]);
            } else if *stage == "finish" {
                assert_eq!(row["data"], call["report"]);
            } else {
                assert_eq!(row["data"], call[*stage]);
            }
        }
        diagnostics.push(json!({"identity":id,"complete_available_rows":all.len(),"training_rows":original.len(),"heldout_rows":held.len(),"active_columns":active,"known_points":table.len(),"selected_kernel_residual_zero":true,"whole_report_counter_parity":true}));
    }
    assert_eq!(position, journal.len());
    assert_eq!(identities.len(), 60);
    let receipt = json!({"protocol":"8e7e1c/CBC","whole_original_native_records":100,"whole_calls":60,"whole_journal_events":660,"all_four_capture_stages_complete":true,"all60full_reports_inputs_scalar_checks_counters_nontime_values_match_original":true,"explicit_truthful_solver_provenance_change_checked":true,"calls":diagnostics,"whole_inputs":[{"path":args[2],"sha256":digest(&fs::read(&args[2]).unwrap())},{"path":args[3],"sha256":digest(&fs::read(&args[3]).unwrap())},{"path":args[4],"sha256":digest(&fs::read(&args[4]).unwrap())},{"path":args[5],"sha256":digest(&fs::read(&args[5]).unwrap())}],"scope":"unsigned whole passive capture/report parity and selected-kernel checks only; no rank/global-character interpretation"});
    fs::write(&args[6], serde_json::to_vec_pretty(&receipt).unwrap()).unwrap();
    println!("whole60 passive calls/660 journal events/report parity/capture checks accepted");
}
