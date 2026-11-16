//! Whole native-record equality; only the prospectively frozen wall fields vary.
use serde_json::{json, Value};
use std::{env, fs};
fn canonical(mut rows: Vec<Value>) -> Vec<String> {
    assert_eq!(rows.len(), 86, "all86 original records required");
    for row in &mut rows {
        if row["kind"] == "N4_NORM_SAMPLER_ATTEMPT" {
            for arm in ["original", "candidate"] {
                let data = &mut row["data"][arm];
                for p in data["phases"].as_array_mut().unwrap() {
                    assert!(p.as_object_mut().unwrap().remove("wall").is_some());
                }
                let stats = data["stats"].as_array_mut().unwrap();
                assert!(
                    stats.iter().filter(|x| x[0] == "wall_total").count() <= 1,
                    "duplicate wall_total"
                );
                stats.retain(|x| x[0] != "wall_total");
            }
        }
    }
    let mut out: Vec<_> = rows
        .iter()
        .map(|x| serde_json::to_string(x).unwrap())
        .collect();
    out.sort();
    out
}
fn main() {
    let args: Vec<_> = env::args().collect();
    assert_eq!(args.len(), 4);
    let golden: Vec<Value> = serde_json::from_slice(&fs::read(&args[1]).unwrap()).unwrap();
    let raw = fs::read_to_string(&args[2]).unwrap();
    let mut rows = vec![];
    for line in raw.lines() {
        if let Some(start) = line.find("N4_NORM_SAMPLER_") {
            let (kind, data) = line[start..].split_once(' ').unwrap();
            let data: Value = serde_json::from_str(data).unwrap();
            rows.push(json!({"kind":kind,"data":data}));
        }
    }
    let expected = canonical(golden);
    let actual = canonical(rows.clone());
    if expected != actual {
        let index = expected
            .iter()
            .zip(&actual)
            .position(|(a, b)| a != b)
            .unwrap();
        let e: Value = serde_json::from_str(&expected[index]).unwrap();
        let a: Value = serde_json::from_str(&actual[index]).unwrap();
        eprintln!(
            "First unequal row {index}: kind {} / {}",
            e["kind"], a["kind"]
        );
        fn difference(a: &Value, b: &Value, path: String) -> Option<(String, Value, Value)> {
            if a == b {
                return None;
            }
            if let (Some(x), Some(y)) = (a.as_object(), b.as_object()) {
                for key in x.keys().chain(y.keys()) {
                    let av = x.get(key).unwrap_or(&Value::Null);
                    let bv = y.get(key).unwrap_or(&Value::Null);
                    if let Some(d) = difference(av, bv, format!("{path}/{key}")) {
                        return Some(d);
                    }
                }
            } else if let (Some(x), Some(y)) = (a.as_array(), b.as_array()) {
                for i in 0..x.len().max(y.len()) {
                    let av = x.get(i).unwrap_or(&Value::Null);
                    let bv = y.get(i).unwrap_or(&Value::Null);
                    if let Some(d) = difference(av, bv, format!("{path}/{i}")) {
                        return Some(d);
                    }
                }
            }
            Some((path, a.clone(), b.clone()))
        }
        panic!(
            "whole original JSON mismatch: {:?}",
            difference(&e, &a, String::new())
        );
    }
    fs::write(&args[3], serde_json::to_vec(&rows).unwrap()).unwrap();
    println!("ALL86 whole original native JSON equal; ONLY ATTEMPT original/candidate phase.wall and stats.wall_total masked; ALL counters/classes/calls/failures/tentative answers exact.");
}
