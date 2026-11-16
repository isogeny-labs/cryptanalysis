//! Whole ordered native records. No masks, candidate reselection or deduplication.
use serde_json::{json, Value};
use std::{fs, path::Path};
fn read(path: &str) -> Vec<Value> {
    let text = fs::read_to_string(path).unwrap();
    assert_eq!(
        text.lines()
            .filter(|x| x.starts_with(
                "test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;"
            ))
            .count(),
        1,
        "one complete unfiltered native pass required"
    );
    let rows = text
        .lines()
        .filter_map(|line| {
            line.find("N4_").map(|i| {
                let (kind, body) = line[i..].split_once(' ').unwrap();
                json!({"kind":kind,"data":serde_json::from_str::<Value>(body).unwrap()})
            })
        })
        .collect::<Vec<_>>();
    let required = [
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
    assert_eq!(
        rows.len(),
        required.len(),
        "every complete constructor and fixed-pair record required"
    );
    for (r, kind) in rows.iter().zip(required) {
        assert_eq!(r["kind"], kind);
    }
    rows
}
fn main() {
    let args = std::env::args().collect::<Vec<_>>();
    match args.get(1).map(String::as_str) {
        Some("--freeze") => {
            assert_eq!(args.len(), 4);
            assert!(!Path::new(&args[3]).exists());
            let rows = read(&args[2]);
            fs::write(&args[3], serde_json::to_vec_pretty(&rows).unwrap()).unwrap();
        }
        Some("--compare") => {
            assert_eq!(args.len(), 5);
            assert!(!Path::new(&args[4]).exists());
            let expected: Vec<Value> =
                serde_json::from_slice(&fs::read(&args[2]).unwrap()).unwrap();
            let rows = read(&args[3]);
            assert_eq!(
                expected, rows,
                "WHOLE ordered record differs; NO masks or deduplication"
            );
            fs::write(&args[4], serde_json::to_vec_pretty(&rows).unwrap()).unwrap();
        }
        _ => panic!("--freeze raw output | --compare expected raw output"),
    }
}
