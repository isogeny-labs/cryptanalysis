//! Whole native beta-field/torsion records; no masks or dropped fields.
use serde_json::{json, Value};
use std::{env, fs};
fn rows(raw: &str) -> Vec<Value> {
    let mut out = vec![];
    for line in raw.lines() {
        if let Some(i) = line.find("N4_BETA_") {
            let (kind, data) = line[i..].split_once(' ').unwrap();
            out.push(json!({"kind":kind,"data":serde_json::from_str::<Value>(data).unwrap()}));
        }
    }
    assert_eq!(out.len(), 3, "allthree complete native records required");
    out
}
fn main() {
    let a: Vec<_> = env::args().collect();
    assert_eq!(a.len(), 4);
    let actual = rows(&fs::read_to_string(&a[2]).unwrap());
    if a[1] != "--freeze" {
        let expected: Vec<Value> = serde_json::from_slice(&fs::read(&a[1]).unwrap()).unwrap();
        assert_eq!(
            expected, actual,
            "whole native beta records differ; NO masks permitted"
        );
    }
    fs::write(&a[3], serde_json::to_vec_pretty(&actual).unwrap()).unwrap();
    println!("ALL3 whole beta torsion/finite-hypothesis/quadratic-Picard records exact; NO masks, every coordinate/class/control/count retained.");
}
