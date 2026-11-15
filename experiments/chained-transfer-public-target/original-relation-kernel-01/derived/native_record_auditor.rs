use serde_json::Value;
use std::{collections::BTreeMap, env, fs};

fn records(text: &str) -> Vec<Value> {
    let mut rows = Vec::new();
    for line in text.lines() {
        if let Some(start) = line.find("N4_") {
            let (kind, payload) = line[start..].split_once(' ').expect("record payload");
            let data: Value = serde_json::from_str(payload).expect("complete whole record JSON");
            rows.push(serde_json::json!({"kind":kind,"data":data}));
        }
    }
    let mut counts = BTreeMap::new();
    for row in &rows {
        *counts
            .entry(row["kind"].as_str().unwrap())
            .or_insert(0usize) += 1;
    }
    for (tag, n) in [
        ("SETUP", 1),
        ("INPUT", 3),
        ("ATTEMPT", 60),
        ("CASE", 15),
        ("REJECTIONS", 3),
        ("TARGET", 3),
        ("SCOPE", 1),
    ] {
        assert_eq!(
            counts
                .get(format!("N4_ORIGINAL_MODEL_IC_{tag}").as_str())
                .copied()
                .unwrap_or(0),
            n,
            "missing entire or partial record population {tag}"
        );
    }
    let mut attempts = BTreeMap::new();
    let mut success = BTreeMap::new();
    for row in &rows {
        let d = &row["data"];
        let kind = row["kind"].as_str().unwrap();
        if kind == "N4_ORIGINAL_MODEL_IC_ATTEMPT" {
            let side = d["side"].as_u64().unwrap();
            let q = d["public_index"].as_u64().unwrap();
            let a = d["attempt"].as_u64().unwrap();
            assert!(side < 3 && q < 5 && a < 4);
            assert!(attempts.insert((side, q, a), true).is_none());
            assert_eq!(d["nfb"], [30, 36, 48, 64][a as usize]);
            assert_eq!(d["seed"], 102 + a);
            assert_eq!(d["actual_opaque_chain_equals_independent_Phi"], true);
            if d["report"]["ok"] == true {
                assert_eq!(d["actual_target_group_check"], true);
                assert_eq!(d["independent_original_source_check"], true);
                assert!(d["report"]["k_found"].as_u64().is_some());
                *success.entry((side, q)).or_insert(0u64) += 1;
            }
        } else if kind == "N4_ORIGINAL_MODEL_IC_REJECTIONS" {
            assert_eq!(d["all_rejected"], true);
            assert_eq!(d["all_controls"].as_array().unwrap().len(), 10);
        } else if kind == "N4_ORIGINAL_MODEL_IC_TARGET" {
            assert_eq!(d["public_cases_solved"], 5);
            assert_eq!(d["all_twenty_attempts_retained"], true);
        } else if kind == "N4_ORIGINAL_MODEL_IC_SCOPE" {
            assert_eq!(d["attempts"], 60);
            assert_eq!(d["public_cases_solved"], 15);
        }
    }
    assert_eq!(attempts.len(), 60);
    assert_eq!(success.len(), 15);
    let mut cases = BTreeMap::new();
    for row in &rows {
        if row["kind"] == "N4_ORIGINAL_MODEL_IC_CASE" {
            let d = &row["data"];
            let key = (
                d["side"].as_u64().unwrap(),
                d["public_index"].as_u64().unwrap(),
            );
            assert_eq!(d["all_four_attempts_retained"], true);
            assert_eq!(
                d["successful_attempts"].as_u64(),
                success.get(&key).copied()
            );
            assert!(cases.insert(key, true).is_none());
        }
    }
    assert_eq!(cases.len(), 15);
    rows
}
fn main() {
    let args = env::args().collect::<Vec<_>>();
    let output = match args.get(1).map(String::as_str) {
        Some("--freeze") if args.len() == 4 => {
            let rows = records(&fs::read_to_string(&args[2]).unwrap());
            (&args[3], rows)
        }
        Some("--compare") if args.len() == 5 => {
            let expected: Vec<Value> =
                serde_json::from_str(&fs::read_to_string(&args[2]).unwrap()).unwrap();
            let actual = records(&fs::read_to_string(&args[3]).unwrap());
            assert_eq!(expected, actual, "whole same-run records differ");
            (&args[4], actual)
        }
        _ => panic!("usage: --freeze RAW OUT | --compare EXPECTED RAW OUT"),
    };
    fs::write(output.0, serde_json::to_vec(&output.1).unwrap()).unwrap();
}
