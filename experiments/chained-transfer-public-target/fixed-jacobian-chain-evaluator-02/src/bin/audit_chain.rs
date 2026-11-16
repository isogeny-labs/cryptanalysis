//! Entire ordered finite-run records, with original constructor controls pinned.
use serde_json::{json, Value};
use std::{fs, path::Path};
const OLD: [&str; 5] = [
    "N4_NONDUAL13_KERNEL_GATE",
    "N4_NEXT13_KERNEL_GATE",
    "N4_TWIST_ORDER_CANDIDATE",
    "N4_TWIST_GENERATOR_ATTEMPTS",
    "N4_FOURTH_KERNEL_GATE",
];
fn expected_tags() -> Vec<&'static str> {
    let mut tags = OLD.to_vec();
    tags.push("N4_FIXED_CHAIN_SETUP");
    tags.extend(["N4_FIXED_CHAIN_COFACTOR_ATTEMPTS"; 3]);
    for _ in 0..3 {
        tags.extend(["N4_FIXED_CHAIN_EXCEPTIONAL_CASE"; 224]);
        tags.push("N4_FIXED_CHAIN_ALL_EXCEPTIONALS");
    }
    tags.extend(OLD);
    tags.extend([
        "N4_FIXED_CHAIN_ALL_MIXED",
        "N4_FIXED_CHAIN_ALL_PUBLIC",
        "N4_FIXED_CHAIN_ALL_ADDITIONS",
        "N4_FIXED_CHAIN_SELECTED_CALL_VECTORS",
        "N4_FIXED_CHAIN_ACTUAL_REJECTIONS",
        "N4_FIXED_CHAIN_FULL_POPULATION",
    ]);
    tags
}
fn records(prior: &str, path: &str) -> Vec<Value> {
    let prior: Vec<Value> = serde_json::from_slice(&fs::read(prior).unwrap()).unwrap();
    assert_eq!(prior.len(), 16);
    let text = fs::read_to_string(path).unwrap();
    assert_eq!(
        text.lines()
            .filter(|line| line.starts_with(
                "test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;"
            ))
            .count(),
        1
    );
    let rows = text
        .lines()
        .filter_map(|line| {
            line.find("N4_").map(|i| {
                let (kind, data) = line[i..].split_once(' ').unwrap();
                json!({"kind":kind,"data":serde_json::from_str::<Value>(data).unwrap()})
            })
        })
        .collect::<Vec<_>>();
    let tags = expected_tags();
    assert_eq!(tags.len(), 695);
    assert_eq!(
        rows.len(),
        tags.len(),
        "every whole constructor, streamed case and full panel record required"
    );
    for (row, tag) in rows.iter().zip(tags) {
        assert_eq!(row["kind"], tag);
    }
    for (i, original) in [0, 1, 2, 3, 9].into_iter().enumerate() {
        assert_eq!(
            rows[i], prior[original],
            "whole existing constructor control changed"
        );
    }
    let mut index = 9;
    for domain in 0..3 {
        for case in 0..224 {
            let row = &rows[index]["data"];
            assert_eq!(row["domain"], domain);
            assert_eq!(row["index"], case);
            assert_eq!(
                row["whole_descriptor"]["both_outgoing_maps"]
                    .as_array()
                    .unwrap()
                    .len(),
                2
            );
            index += 1;
        }
        let summary = &rows[index]["data"];
        assert_eq!(summary["domain"], domain);
        assert_eq!(summary["all224_descriptors"].as_array().unwrap().len(), 224);
        index += 1;
    }
    for i in 0..5 {
        assert_eq!(
            rows[index + i],
            rows[i],
            "independent point-check constructor occurrence must remain whole and exact"
        );
    }
    index += 5;
    assert_eq!(rows[index]["data"]["all144"].as_array().unwrap().len(), 144);
    assert_eq!(
        rows[index + 1]["data"]["all120"].as_array().unwrap().len(),
        120
    );
    let additions = rows[index + 2]["data"]["all_three_pairs"]
        .as_array()
        .unwrap();
    assert_eq!(additions.len(), 3);
    for pair in additions {
        assert_eq!(pair["all96"].as_array().unwrap().len(), 96);
    }
    assert_eq!(
        rows[index + 3]["data"]["all48"].as_array().unwrap().len(),
        48
    );
    let full = &rows.last().unwrap()["data"];
    for (name, wanted) in [
        ("domains", 3),
        ("exceptional_descriptors", 672),
        ("exceptional_outgoing_evaluations", 1344),
        ("mixed", 144),
        ("public", 120),
        ("addition_pairs_per_undirected_pair", 96),
        ("undirected_pairs", 3),
        ("comparison_vectors", 48),
        ("full_group_order", 11086844),
        ("source_prime", 2771711),
    ] {
        assert_eq!(full[name], wanted);
    }
    assert_eq!(
        full["all_four_halves_and_duplicate_corrections_required"],
        true
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
            output(&a[4], &records(&a[2], &a[3]));
        }
        Some("--compare") => {
            assert_eq!(a.len(), 6);
            let expected: Vec<Value> = serde_json::from_slice(&fs::read(&a[3]).unwrap()).unwrap();
            let actual = records(&a[2], &a[4]);
            assert_eq!(
                actual, expected,
                "ALL whole ordered records must match; no masks or deduplication"
            );
            output(&a[5], &actual);
        }
        _ => panic!("--freeze OLD16 NATIVE OUT | --compare OLD16 EXPECTED NATIVE OUT"),
    }
}
