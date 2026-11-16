//! All ordered native records, including all nine unchanged prior records.
use serde_json::{json, Value};
use std::{fs, path::Path};
const OLD: [&str; 9] = [
    "N4_NONDUAL13_KERNEL_GATE",
    "N4_NEXT13_KERNEL_GATE",
    "N4_TWIST_ORDER_CANDIDATE",
    "N4_TWIST_GENERATOR_ATTEMPTS",
    "N4_TWIST_MAPS_AND_CERTIFICATES",
    "N4_TWIST_POINTS",
    "N4_TWIST_FIXED_KERNELS",
    "N4_TWIST_ALL_MODELS",
    "N4_TWIST_MATCHED_PAIR",
];
const NEW: [&str; 7] = [
    "N4_FOURTH_KERNEL_GATE",
    "N4_FOURTH_MAPS",
    "N4_FOURTH_POINT_PANELS",
    "N4_FOURTH_PUBLIC",
    "N4_FOURTH_FIXED_KERNELS",
    "N4_FOURTH_ALL_MODELS",
    "N4_FOURTH_MATCHED_ENDPOINTS",
];
fn raw(path: &str, unfiltered: bool) -> Vec<Value> {
    let text = fs::read_to_string(path).unwrap();
    if unfiltered {
        assert_eq!(
            text.lines()
                .filter(|x| x.starts_with(
                    "test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;"
                ))
                .count(),
            1
        );
    }
    text.lines()
        .filter_map(|line| {
            line.find("N4_").map(|i| {
                let (kind, body) = line[i..].split_once(' ').unwrap();
                json!({"kind":kind,"data":serde_json::from_str::<Value>(body).unwrap()})
            })
        })
        .collect()
}
fn old(path: &str) -> Vec<Value> {
    let rows: Vec<Value> = serde_json::from_slice(&fs::read(path).unwrap()).unwrap();
    assert_eq!(rows.len(), 9);
    for (row, kind) in rows.iter().zip(OLD) {
        assert_eq!(row["kind"], kind);
    }
    rows
}
fn all(prior: &[Value], path: &str) -> Vec<Value> {
    let rows = raw(path, true);
    assert_eq!(
        rows.len(),
        16,
        "all original nine and new seven whole records required"
    );
    for (row, kind) in rows.iter().zip(OLD.into_iter().chain(NEW)) {
        assert_eq!(row["kind"], kind);
    }
    assert_eq!(
        &rows[..9],
        prior,
        "ALL nine previous whole records must remain exact; no masks or deduplication"
    );
    rows
}
fn output(path: &str, rows: &[Value]) {
    assert!(!Path::new(path).exists());
    fs::write(path, serde_json::to_vec_pretty(rows).unwrap()).unwrap();
}
fn main() {
    let a = std::env::args().collect::<Vec<_>>();
    match a.get(1).map(String::as_str) {
        Some("--freeze") => {
            assert_eq!(a.len(), 5);
            output(&a[4], &all(&old(&a[2]), &a[3]));
        }
        Some("--compare") => {
            assert_eq!(a.len(), 6);
            let expected: Vec<Value> = serde_json::from_slice(&fs::read(&a[3]).unwrap()).unwrap();
            let rows = all(&old(&a[2]), &a[4]);
            assert_eq!(rows, expected, "every whole ordered record must match");
            output(&a[5], &rows);
        }
        Some("--control") => {
            assert_eq!(a.len(), 5);
            let prior = old(&a[2]);
            let rows = raw(&a[3], false);
            assert_eq!(rows.len(), 5);
            assert_eq!(
                &rows[..4],
                &prior[..4],
                "every actual prior constructor record retained"
            );
            let gate = &rows[4];
            assert_eq!(gate["kind"], "N4_FOURTH_KERNEL_GATE");
            let d = &gate["data"];
            assert_eq!(d["accepted_nondual"], false);
            assert_eq!(d["actual_gcd_degree"], 168);
            assert_eq!(d["expected_gcd_degree"], 12);
            assert_eq!(d["actual_gcd"], d["psi13_squared_monic"]);
            assert_ne!(d["actual_gcd"], d["previous_forward_denominator"]);
            output(&a[4], &rows);
        }
        _ => {
            panic!("--freeze old9 raw out | --compare old9 new16 raw out | --control old9 raw out")
        }
    }
}
