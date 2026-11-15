use serde_json::Value;
use std::{collections::BTreeMap, env, fs};
fn records(text: &str) -> Vec<Value> {
    let mut rows = Vec::new();
    let mut counts = BTreeMap::new();
    for line in text.lines() {
        if let Some(i) = line.find("N4_") {
            let (k, b) = line[i..].split_once(' ').expect("whole record");
            let d: Value = serde_json::from_str(b).unwrap();
            *counts.entry(k.to_owned()).or_insert(0usize) += 1;
            rows.push(serde_json::json!({"kind":k,"data":d}));
        }
    }
    for (tag, n) in [
        ("SETUP", 1),
        ("PROVENANCE", 1),
        ("INPUT", 3),
        ("SCALARS", 3),
        ("ATTEMPT", 60),
        ("CASE", 15),
        ("TARGET", 3),
        ("SCOPE", 1),
    ] {
        assert_eq!(
            counts
                .get(&format!("N4_ORIGINAL_FIXED_SAMPLER_{tag}"))
                .copied()
                .unwrap_or(0),
            n,
            "missing whole record population {tag}"
        );
    }
    let mut attempts = BTreeMap::new();
    let mut cases = BTreeMap::new();
    let mut scalars = BTreeMap::new();
    for row in &rows {
        let d = &row["data"];
        match row["kind"].as_str().unwrap() {
            "N4_ORIGINAL_FIXED_SAMPLER_INPUT" => {
                assert_eq!(d["strong_known_point_reference_exact"], true);
            }
            "N4_ORIGINAL_FIXED_SAMPLER_SCALARS" => {
                let side = d["side"].as_u64().unwrap();
                assert!(side < 3);
                assert_eq!(d["scalars"].as_array().unwrap().len(), 75);
                assert_eq!(d["all75"].as_array().unwrap().len(), 75);
                for s in d["all75"].as_array().unwrap() {
                    assert_eq!(s["sampler_class"], s["original_Picard_class"]);
                    assert_eq!(s["all_five_triples"].as_array().unwrap().len(), 5);
                    for t in s["all_five_triples"].as_array().unwrap() {
                        assert_eq!(t["all_three_exact"], true);
                    }
                }
                assert!(scalars.insert(side, true).is_none());
            }
            "N4_ORIGINAL_FIXED_SAMPLER_ATTEMPT" => {
                let side = d["side"].as_u64().unwrap();
                let q = d["public_index"].as_u64().unwrap();
                let a = d["attempt"].as_u64().unwrap();
                assert!(side < 3 && q < 5 && a < 4);
                assert!(attempts.insert((side, q, a), true).is_none());
                assert_eq!(d["nfb"], [30, 36, 48, 64][a as usize]);
                assert_eq!(d["seed"], 102 + a);
                assert_eq!(d["all_frozen_nontiming_fields_equal"], true);
                assert_eq!(d["original"]["ok"], d["candidate"]["ok"]);
                if d["original"]["ok"] == true {
                    for k in [
                        "original_target_group_check",
                        "candidate_target_group_check",
                        "original_source_check",
                        "candidate_source_check",
                    ] {
                        assert_eq!(d[k], true);
                    }
                }
            }
            "N4_ORIGINAL_FIXED_SAMPLER_CASE" => {
                let key = (
                    d["side"].as_u64().unwrap(),
                    d["public_index"].as_u64().unwrap(),
                );
                assert!(d["common_correct_settings"].as_u64().unwrap() > 0);
                assert_eq!(d["all_four_outcomes"].as_array().unwrap().len(), 4);
                assert!(cases.insert(key, true).is_none());
            }
            "N4_ORIGINAL_FIXED_SAMPLER_SCOPE" => {
                for (k, n) in [
                    ("models", 3),
                    ("scalar_pairs", 225),
                    ("triples", 1125),
                    ("paired_attempts", 60),
                    ("solver_reports", 120),
                    ("common_solved_cases", 15),
                ] {
                    assert_eq!(d[k], n);
                }
            }
            _ => {}
        }
    }
    assert_eq!(attempts.len(), 60);
    assert_eq!(cases.len(), 15);
    assert_eq!(scalars.len(), 3);
    rows
}
fn main() {
    let a = env::args().collect::<Vec<_>>();
    let (o, r) = match a.get(1).map(String::as_str) {
        Some("--freeze") if a.len() == 4 => (&a[3], records(&fs::read_to_string(&a[2]).unwrap())),
        Some("--compare") if a.len() == 5 => {
            let e: Vec<Value> = serde_json::from_slice(&fs::read(&a[2]).unwrap()).unwrap();
            let r = records(&fs::read_to_string(&a[3]).unwrap());
            assert_eq!(e, r, "whole same-run records differ");
            (&a[4], r)
        }
        _ => panic!("--freeze RAW OUT | --compare EXPECTED RAW OUT"),
    };
    fs::write(o, serde_json::to_vec(&r).unwrap()).unwrap();
}
