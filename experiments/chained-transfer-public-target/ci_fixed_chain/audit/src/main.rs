//! Whole ordered geometry records and original constructor controls, no masks.
use serde_json::{json, Value};
use std::{fs, path::Path};
fn main() {
    let args = std::env::args().collect::<Vec<_>>();
    assert_eq!(args.len(), 6);
    assert_eq!(args[1], "--compare");
    let old: Vec<Value> = serde_json::from_slice(&fs::read(&args[2]).unwrap()).unwrap();
    let expected: Vec<Value> = serde_json::from_slice(&fs::read(&args[3]).unwrap()).unwrap();
    assert_eq!(old.len(), 16);
    assert_eq!(expected.len(), 13);
    let text = fs::read_to_string(&args[4]).unwrap();
    assert_eq!(
        text.lines()
            .filter(|line| line.starts_with(
                "test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;"
            ))
            .count(),
        1
    );
    let actual = text
        .lines()
        .filter_map(|line| {
            line.find("N4_").map(|i| {
                let (kind, data) = line[i..].split_once(' ').unwrap();
                json!({"kind":kind,"data":serde_json::from_str::<Value>(data).unwrap()})
            })
        })
        .collect::<Vec<_>>();
    let tags = [
        "N4_CHAIN_OLD_LITERAL_PARITY",
        "N4_NONDUAL13_KERNEL_GATE",
        "N4_NEXT13_KERNEL_GATE",
        "N4_TWIST_ORDER_CANDIDATE",
        "N4_TWIST_GENERATOR_ATTEMPTS",
        "N4_FOURTH_KERNEL_GATE",
        "N4_CHAIN_ACTUAL_ELLIPTIC_CERTIFICATES",
        "N4_CHAIN_FIXED_GEOMETRY",
        "N4_CHAIN_ACTUAL_REJECTIONS",
        "N4_CHAIN_FIXED_GEOMETRY",
        "N4_CHAIN_ACTUAL_REJECTIONS",
        "N4_CHAIN_FIXED_GEOMETRY",
        "N4_CHAIN_ACTUAL_REJECTIONS",
    ];
    assert_eq!(
        actual.len(),
        tags.len(),
        "all thirteen whole ordered records required"
    );
    for (row, tag) in actual.iter().zip(tags) {
        assert_eq!(row["kind"], tag);
    }
    for (i, original) in [0, 1, 2, 3, 9].into_iter().enumerate() {
        assert_eq!(
            actual[i + 1],
            old[original],
            "entire original constructor occurrence changed"
        );
    }
    for index in 0..3 {
        let row = &actual[7 + 2 * index]["data"];
        assert_eq!(row["index"], index);
        assert_eq!(row["all224_line_offsets"].as_array().unwrap().len(), 224);
        assert_eq!(row["all_six_rows"].as_array().unwrap().len(), 6);
        assert_eq!(row["all_correction_fibres"].as_array().unwrap().len(), 2);
        for fibre in row["all_correction_fibres"].as_array().unwrap() {
            assert_eq!(fibre["all_actual_preimages"].as_array().unwrap().len(), 2);
        }
        assert_eq!(row["quadratic_origin_calls"], 1);
        assert_eq!(actual[8 + 2 * index]["data"]["index"], index);
    }
    assert_eq!(
        actual, expected,
        "ALL whole ordered fields must match; no masks or deduplication"
    );
    assert!(!Path::new(&args[5]).exists());
    fs::write(&args[5], serde_json::to_vec_pretty(&actual).unwrap()).unwrap();
}
