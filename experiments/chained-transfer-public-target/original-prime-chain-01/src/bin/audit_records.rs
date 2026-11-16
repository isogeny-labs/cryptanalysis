//! Require every whole ordered original-prime native record and old control.
use serde_json::{json, Value};
use std::{fs, path::Path};
const OLD: [&str; 7] = [
    "N4_NONDUAL13_KERNEL_GATE",
    "N4_NEXT13_KERNEL_GATE",
    "N4_NONDUAL13_KERNEL_GATE",
    "N4_NEXT13_KERNEL_GATE",
    "N4_TWIST_ORDER_CANDIDATE",
    "N4_TWIST_GENERATOR_ATTEMPTS",
    "N4_FOURTH_KERNEL_GATE",
];
fn tags() -> Vec<&'static str> {
    let mut a = OLD.to_vec();
    a.push("N4_ORIGINAL_PRIME_SETUP");
    for _ in 0..3 {
        a.extend([
            "N4_ORIGINAL_PRIME_SOURCE_MODEL",
            "N4_ORIGINAL_PRIME_COFACTOR_ATTEMPTS",
        ]);
        a.extend(["N4_ORIGINAL_PRIME_EXCEPTIONAL_CASE"; 224]);
        a.extend(["N4_ORIGINAL_PRIME_PUBLIC_CASE"; 128]);
    }
    a.extend(["N4_ORIGINAL_PRIME_ADDITIONS"; 3]);
    a.extend([
        "N4_ORIGINAL_PRIME_ORIGINAL_PUBLIC",
        "N4_ORIGINAL_PRIME_SELECTED_VECTORS",
        "N4_ORIGINAL_PRIME_REJECTIONS",
        "N4_ORIGINAL_PRIME_FULL_POPULATION",
    ]);
    a
}
fn records(old: &str, native: &str) -> Vec<Value> {
    let old: Vec<Value> = serde_json::from_slice(&fs::read(old).unwrap()).unwrap();
    assert_eq!(old.len(), 16);
    let text = fs::read_to_string(native).unwrap();
    assert_eq!(
        text.lines()
            .filter(|l| l.starts_with(
                "test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;"
            ))
            .count(),
        1
    );
    let rows = text
        .lines()
        .filter_map(|l| {
            l.find("N4_").map(|i| {
                let (k, v) = l[i..].split_once(' ').unwrap();
                json!({"kind":k,"data":serde_json::from_str::<Value>(v).unwrap()})
            })
        })
        .collect::<Vec<_>>();
    let expected = tags();
    assert_eq!(expected.len(), 1077);
    assert_eq!(
        rows.len(),
        expected.len(),
        "every entire original constructor/model/case/public/addition/vector record required"
    );
    for (r, t) in rows.iter().zip(expected) {
        assert_eq!(r["kind"], t)
    }
    for (i, index) in [0, 1, 0, 1, 2, 3, 9].into_iter().enumerate() {
        assert_eq!(
            rows[i], old[index],
            "whole original constructor occurrence changed"
        )
    }
    let mut index = 8;
    for domain in 0..3 {
        let model = &rows[index]["data"];
        assert_eq!(model["domain"], domain);
        assert_eq!(
            model["all_six_whole_original_rows"]
                .as_array()
                .unwrap()
                .len(),
            6
        );
        assert_eq!(model["all224_line_offsets"].as_array().unwrap().len(), 224);
        index += 1;
        let cf = &rows[index]["data"];
        assert_eq!(cf["domain"], domain);
        assert_eq!(cf["all228"].as_array().unwrap().len(), 228);
        assert_eq!(cf["all_four_actual_classes"].as_array().unwrap().len(), 4);
        index += 1;
        for i in 0..224 {
            let x = &rows[index]["data"];
            assert_eq!(x["domain"], domain);
            assert_eq!(x["index"], i);
            assert_eq!(x["both_outgoing_maps"].as_array().unwrap().len(), 2);
            index += 1;
        }
        for i in 0..128 {
            let x = &rows[index]["data"];
            assert_eq!(x["domain"], domain);
            assert_eq!(x["index"], i);
            assert_eq!(x["both_outgoing_maps"].as_array().unwrap().len(), 2);
            index += 1;
        }
    }
    for _ in 0..3 {
        assert_eq!(rows[index]["data"]["all64"].as_array().unwrap().len(), 64);
        index += 1;
    }
    let public = &rows[index]["data"];
    assert_eq!(
        public["whole_original_five_controls"],
        old[12]["data"]["all5_original_public_controls"]
    );
    assert_eq!(public["all15"].as_array().unwrap().len(), 15);
    index += 1;
    assert_eq!(rows[index]["data"]["all12"].as_array().unwrap().len(), 12);
    index += 1;
    assert_eq!(
        rows[index]["data"]["all_three_domains"]
            .as_array()
            .unwrap()
            .len(),
        3
    );
    index += 1;
    assert_eq!(index, 1076);
    let full = &rows[index]["data"];
    for (k, n) in [
        ("domains", 3),
        ("whole_old_model_rows", 18),
        ("projected_exceptional_descriptors", 672),
        ("exceptional_outgoing_evaluations", 1344),
        ("public_points", 384),
        ("public_outgoing_evaluations", 768),
        ("addition_pairs_per_undirected_pair", 64),
        ("original_public_endpoint_transfers", 15),
        ("selected_vectors", 12),
        ("selected_routes", 5),
        ("prime", 2773073),
        ("full_source_order", 11092292),
    ] {
        assert_eq!(full[k], n)
    }
    rows
}
fn output(path: &str, rows: &[Value]) {
    assert!(!Path::new(path).exists());
    fs::write(path, serde_json::to_vec(rows).unwrap()).unwrap()
}
fn main() {
    let a = std::env::args().collect::<Vec<_>>();
    match a.get(1).map(String::as_str) {
        Some("--freeze") => {
            assert_eq!(a.len(), 5);
            output(&a[4], &records(&a[2], &a[3]))
        }
        Some("--compare") => {
            assert_eq!(a.len(), 6);
            let expected: Vec<Value> = serde_json::from_slice(&fs::read(&a[3]).unwrap()).unwrap();
            let actual = records(&a[2], &a[4]);
            assert_eq!(
                actual, expected,
                "ALL whole ordered records; no masks/deduplication"
            );
            output(&a[5], &actual)
        }
        _ => panic!("--freeze OLD16 NATIVE OUT | --compare OLD16 EXPECTED NATIVE OUT"),
    }
}
