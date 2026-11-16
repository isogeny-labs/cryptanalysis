//! Whole original geometry population; no record masks or deduplication.
use serde_json::{json, Value};
use std::{fs, path::Path};
fn main() {
    let args = std::env::args().collect::<Vec<_>>();
    assert!(args.len() == 6 || args.len() == 7);
    let mode = &args[1];
    assert!(mode == "--freeze" || mode == "--compare");
    let old16: Vec<Value> = serde_json::from_slice(&fs::read(&args[2]).unwrap()).unwrap();
    assert_eq!(old16.len(), 16);
    let old13: Vec<Value> = serde_json::from_slice(&fs::read(&args[3]).unwrap()).unwrap();
    assert_eq!(old13.len(), 13);
    let (native, output) = if mode == "--freeze" {
        assert_eq!(args.len(), 6);
        (&args[4], &args[5])
    } else {
        assert_eq!(args.len(), 7);
        (&args[5], &args[6])
    };
    assert!(!Path::new(output).exists());
    let text = fs::read_to_string(native).unwrap();
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
        "N4_NONDUAL13_KERNEL_GATE",
        "N4_NEXT13_KERNEL_GATE",
        "N4_TWIST_ORDER_CANDIDATE",
        "N4_TWIST_GENERATOR_ATTEMPTS",
        "N4_FOURTH_KERNEL_GATE",
        "N4_CHAIN_ACTUAL_ELLIPTIC_CERTIFICATES",
        "N4_ORIGINAL_FULL_CENSUS_PARITY",
        "N4_CHAIN_FIXED_GEOMETRY",
        "N4_CHAIN_ACTUAL_REJECTIONS",
        "N4_CHAIN_FIXED_GEOMETRY",
        "N4_CHAIN_ACTUAL_REJECTIONS",
        "N4_CHAIN_FIXED_GEOMETRY",
        "N4_CHAIN_ACTUAL_REJECTIONS",
    ];
    assert_eq!(actual.len(), 16, "all16 whole records required");
    for (row, tag) in actual.iter().zip(tags) {
        assert_eq!(row["kind"], tag);
    }
    assert_eq!(
        actual[0], old13[0],
        "complete old known-answer parity record changed"
    );
    for (i, original) in [0, 1, 0, 1, 2, 3, 9].into_iter().enumerate() {
        assert_eq!(
            actual[i + 1],
            old16[original],
            "every original constructor occurrence required whole"
        );
    }
    let parity = actual[9]["data"]["all_three_whole_parities"]
        .as_array()
        .unwrap();
    assert_eq!(parity.len(), 3);
    for i in 0..3 {
        assert_eq!(parity[i]["domain"], i);
        assert_eq!(
            parity[i]["all_six_whole_original_rows"]["all_six_whole_rows"],
            parity[i]["all_six_actual_runtime_rows"]
        );
        let row = &actual[10 + 2 * i]["data"];
        assert_eq!(row["index"], i);
        assert_eq!(
            row["all_six_rows"],
            parity[i]["all_six_actual_runtime_rows"]
        );
        assert_eq!(row["all224_line_offsets"].as_array().unwrap().len(), 224);
        assert_eq!(row["all_six_rows"].as_array().unwrap().len(), 6);
        assert_eq!(row["quadratic_origin_calls"], 1);
        assert_eq!(row["all_correction_fibres"].as_array().unwrap().len(), 2);
        for fibre in row["all_correction_fibres"].as_array().unwrap() {
            assert_eq!(fibre["all_actual_preimages"].as_array().unwrap().len(), 2);
        }
        assert_eq!(actual[11 + 2 * i]["data"]["index"], i);
        for name in [
            "wrong_order",
            "foreign_prime",
            "foreign_mask",
            "foreign_source",
            "zero_generator",
            "foreign_point_field",
            "foreign_point_model",
            "foreign_class_field",
            "foreign_class_model",
            "altered_curve",
        ] {
            assert!(
                !actual[11 + 2 * i]["data"][name]
                    .as_str()
                    .unwrap()
                    .is_empty(),
                "actual {name} rejection required"
            );
        }
    }
    assert_eq!(actual[9]["data"]["all18_equal"], true);
    if mode == "--compare" {
        let expected: Vec<Value> = serde_json::from_slice(&fs::read(&args[4]).unwrap()).unwrap();
        assert_eq!(expected.len(), 16);
        assert_eq!(
            actual, expected,
            "entire16 ordered records/fields must agree"
        );
    }
    fs::write(output, serde_json::to_vec(&actual).unwrap()).unwrap();
}
