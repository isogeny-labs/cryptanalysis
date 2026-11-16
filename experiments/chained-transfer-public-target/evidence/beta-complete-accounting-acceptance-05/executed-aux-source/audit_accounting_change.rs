//! Exact full-tree old/new audit; every changed value is checked explicitly.
use serde_json::{json, Value};
use std::{collections::BTreeSet, env, fs};
fn diff(a: &Value, b: &Value, path: &str, out: &mut Vec<Value>) {
    if a == b {
        return;
    }
    match (a, b) {
        (Value::Object(x), Value::Object(y)) => {
            let keys: BTreeSet<_> = x.keys().chain(y.keys()).collect();
            for k in keys {
                let p = format!("{path}/{k}");
                match (x.get(k), y.get(k)) {
                    (Some(a), Some(b)) => diff(a, b, &p, out),
                    (None, Some(b)) => out.push(json!({"path":p,"change":"add","new":b})),
                    (Some(a), None) => out.push(json!({"path":p,"change":"remove","old":a})),
                    _ => unreachable!(),
                }
            }
        }
        (Value::Array(x), Value::Array(y)) if x.len() == y.len() => {
            for (i, (a, b)) in x.iter().zip(y).enumerate() {
                diff(a, b, &format!("{path}/{i}"), out);
            }
        }
        _ => out.push(json!({"path":path,"change":"replace","old":a,"new":b})),
    }
}
fn main() {
    let a: Vec<_> = env::args().collect();
    assert_eq!(a.len(), 4);
    let old: Value = serde_json::from_slice(&fs::read(&a[1]).unwrap()).unwrap();
    let new: Value = serde_json::from_slice(&fs::read(&a[2]).unwrap()).unwrap();
    assert_eq!(old.as_array().unwrap().len(), 3);
    assert_eq!(new.as_array().unwrap().len(), 3);
    assert_eq!(old[0]["kind"], "N4_BETA_COMPLETE_RATIONAL");
    assert_eq!(new[0]["kind"], "N4_BETA_COMPLETE_RATIONAL");
    let mut changes = Vec::new();
    diff(&old, &new, "", &mut changes);
    let expected = vec![
        json!({"path":"/0/data/explicit_preprocessing","change":"replace","old":"32completeFp2fibre evaluations/32rational13isogenyevaluations on actualE4/eachside4entrytable; original prime andquadratic setup included in implementation, not cost-free","new":"selected constructor calls:32torsionPhi evaluations +2separatequadraticorigintraces +16torsion source-isogeny evaluations; original/contextsetup andvalidation remain included in implementation andunpriced, not a complete primitive-cost ledger"}),
        json!({"path":"/0/data/preprocessing_call_counts","change":"add","new":{"torsion_phi_evaluations":[16,16],"quadratic_origin_traces":[1,1],"torsion_source_isogeny_evaluations":[8,8]}}),
        json!({"path":"/0/data/record_version","change":"add","new":2}),
    ];
    assert_eq!(
        changes, expected,
        "unexpected value change beyond exact prospective accounting correction"
    );
    fs::write(&a[3],serde_json::to_vec_pretty(&json!({"all_three_complete_records_walked":true,"exact_changes":changes,"every_other_field_exactly_equal":true,"ignored_fields":[],"scope":"accounting correction only; future fixture02 compares every field including the corrected values"})).unwrap()).unwrap();
    println!("ALL3 full records audited: EXACT three declared accounting-path changes; EVERY other mathematical/control/class field exact, NO ignored fields.");
}
