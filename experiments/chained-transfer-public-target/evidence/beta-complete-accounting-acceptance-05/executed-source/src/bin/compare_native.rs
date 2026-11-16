//! Whole-record comparator. All scientific JSON fields are compared; no masks.
use serde_json::{json, Value};
use std::{collections::BTreeSet, env, fs};
fn rows(path: &str) -> Vec<Value> {
    let raw = fs::read_to_string(path).unwrap();
    let mut out = Vec::new();
    for line in raw.lines() {
        if let Some(i) = line.find("N4_BETA_") {
            let (kind, data) = line[i..].split_once(' ').unwrap();
            out.push(json!({"kind":kind,"data":serde_json::from_str::<Value>(data).unwrap()}));
        }
    }
    let kinds: BTreeSet<_> = out.iter().map(|v| v["kind"].as_str().unwrap()).collect();
    assert_eq!(kinds.len(), out.len(), "duplicate native record");
    out
}
fn complete(v: &[Value]) {
    let kinds: BTreeSet<_> = v.iter().map(|v| v["kind"].as_str().unwrap()).collect();
    assert_eq!(
        kinds,
        BTreeSet::from([
            "N4_BETA_ALL_EXCEPTIONAL",
            "N4_BETA_BASECHANGE_FIBRES",
            "N4_BETA_COMPLETE_RATIONAL"
        ])
    );
    assert_eq!(v.len(), 3);
}
fn main() {
    let a: Vec<_> = env::args().collect();
    if a.get(1).map(String::as_str) == Some("--inherit") {
        assert_eq!(a.len(), 5);
        let old = rows(&a[2]);
        let current = rows(&a[3]);
        complete(&current);
        assert!((1..=2).contains(&old.len()));
        for want in &old {
            let got = current
                .iter()
                .find(|r| r["kind"] == want["kind"])
                .expect("inherited record missing");
            assert_eq!(got, want, "whole inherited native record differs; NO masks");
        }
        fs::write(&a[4],serde_json::to_vec_pretty(&json!({"inherited_complete_records":old.len(),"current_complete_records":3,"whole_inherited_values_exact":true,"masks":[]})).unwrap()).unwrap();
        println!(
            "ALL{} inherited whole records exact; NO masks; allTHREE current records present.",
            old.len()
        );
        return;
    }
    assert_eq!(a.len(), 4);
    let actual = rows(&a[2]);
    complete(&actual);
    if a[1] == "--freeze" {
        println!("Freeze ALL3 complete native records from accepted run; NO fields excluded.");
    } else {
        let expected: Vec<Value> = serde_json::from_slice(&fs::read(&a[1]).unwrap()).unwrap();
        complete(&expected);
        assert_eq!(expected, actual, "whole native records differ; NO masks");
        println!("ALL3 whole complete-rational/fibre/448-exceptional records EXACT; NO masks.");
    }
    fs::write(&a[3], serde_json::to_vec_pretty(&actual).unwrap()).unwrap();
}
