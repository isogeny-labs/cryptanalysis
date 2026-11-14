//! Report data derived natively from the full conserved census; no cost prices.
use serde_json::{json, Value};
use std::{collections::BTreeMap, env, fs};
fn vectors(rows: &[Value]) -> Value {
    let mut backends: BTreeMap<String, BTreeMap<String, u64>> = BTreeMap::new();
    let mut total: BTreeMap<String, u64> = BTreeMap::new();
    for row in rows {
        if row["modulus"] != 223 || row["diagnostic_or_auxiliary"] == true {
            continue;
        }
        let n = row["count"].as_u64().unwrap();
        let op = row["operation"].as_str().unwrap();
        let backend = row["backend"].as_str().unwrap();
        for map in [&mut total, backends.entry(backend.into()).or_default()] {
            let x = map.entry(op.into()).or_default();
            *x = x.checked_add(n).unwrap();
        }
    }
    let (mut mul_bottom, mut inv_bottom) = (0u64, 0u64);
    let stacks:Vec<_>=backends.iter().map(|(name,counts)|{
  let mul=*counts.get("mul").unwrap_or(&0);let inv=*counts.get("inv").unwrap_or(&0);
  let v=json!({"backend":name,"mul":mul,"inv":inv,"mul_bottom":mul_bottom,"inv_bottom":inv_bottom,"all_operations":counts});
  mul_bottom=mul_bottom.checked_add(mul).unwrap();inv_bottom=inv_bottom.checked_add(inv).unwrap();v
 }).collect();
    assert_eq!(mul_bottom, *total.get("mul").unwrap_or(&0));
    assert_eq!(inv_bottom, *total.get("inv").unwrap_or(&0));
    json!({"totals":total,"stacks":stacks})
}
fn main() {
    let args: Vec<_> = env::args().collect();
    assert_eq!(args.len(), 3);
    let data: Value = serde_json::from_slice(&fs::read(&args[1]).unwrap()).unwrap();
    assert_eq!(data["all_event_counts_conserved"], true);
    let panels:Vec<_>=data["scalar_panels"].as_array().unwrap().iter().map(|p|json!({"target":p["target"],"arm":p["arm"],"samples":p["samples"],"q223":vectors(p["counts"].as_array().unwrap())})).collect();
    let solver: Vec<_> = [
        "solver-original",
        "solver-candidate",
        "public-G-preparation",
    ]
    .iter()
    .map(|group| {
        let rows: Vec<_> = data["grouped"]
            .as_array()
            .unwrap()
            .iter()
            .filter(|r| r["group"] == *group)
            .cloned()
            .collect();
        json!({"group":group,"q223":vectors(&rows)})
    })
    .collect();
    let doc = json!({"schema":"n4-arithmetic-report-v1","source_rows":data["source_rows"],"scalar_panels":panels,"solver_and_preparation":solver,"unit":"raw q223 source-operation vectors; API and aux excluded; mul/sq/const_two remain distinct; no prices, ratios or cold pipeline claim"});
    fs::write(&args[2], serde_json::to_vec_pretty(&doc).unwrap()).unwrap();
    println!("Six deterministic75-sample q223 vectors plus both solver arms and separate preparation; all backend stacks conserved; unpriced.");
}
