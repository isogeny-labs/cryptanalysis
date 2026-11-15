//! Exact whole-record custody and model-outcome projection. No masked fields.
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
};
const KINDS: [&str; 6] = [
    "N4_NONDUAL13_MODEL_PARITY",
    "N4_NONDUAL13_CURRENT_J1",
    "N4_NONDUAL13_KERNEL_GATE",
    "N4_NONDUAL13_MODEL_SELECTION",
    "N4_NONDUAL13_PRODUCT_TRANSPORT",
    "N4_NONDUAL13_MATCHED_MODELS",
];
fn records(path: &str) -> BTreeMap<String, Value> {
    let text = fs::read_to_string(path).unwrap();
    let mut out = BTreeMap::new();
    for line in text.lines() {
        if let Some(i) = line.find("N4_NONDUAL13_") {
            if let Some((kind, body)) = line[i..].split_once(' ') {
                if body.starts_with('{') && body.ends_with('}') {
                    assert!(KINDS.contains(&kind), "unexpected native kind");
                    assert!(
                        out.insert(kind.into(), serde_json::from_str(body).unwrap())
                            .is_none(),
                        "duplicate whole record"
                    );
                }
            }
        }
    }
    assert_eq!(out.len(), 6, "whole native kind set mismatch");
    for k in KINDS {
        assert!(out.contains_key(k));
    }
    out
}
fn save(path: &str, value: &impl serde::Serialize) {
    let mut b = serde_json::to_vec_pretty(value).unwrap();
    b.push(b'\n');
    fs::write(path, b).unwrap();
}
fn main() {
    let a: Vec<_> = std::env::args().collect();
    match a.get(1).map(String::as_str) {
        Some("--freeze") => {
            assert_eq!(a.len(), 4);
            assert!(fs::read_to_string(&a[2]).unwrap().contains(
                "test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;"
            ));
            let r = records(&a[2]);
            let t = &r[KINDS[4]];
            assert_eq!(
                t["all64_actual_coordinate_transports"]
                    .as_array()
                    .unwrap()
                    .len(),
                64
            );
            assert_eq!(
                t["all4096_actual_coordinate_addition_and_pairing_rows"]
                    .as_array()
                    .unwrap()
                    .len(),
                4096
            );
            assert_eq!(
                t["all3_actual_coefficient_conjugate_maps"]
                    .as_array()
                    .unwrap()
                    .len(),
                3
            );
            assert_eq!(
                t["all135_independent_original_masks"]
                    .as_array()
                    .unwrap()
                    .len(),
                135
            );
            assert_eq!(r[KINDS[1]]["actual_original_norm_model_tag"],"Ciani-Jac-odd-product-v1-7ea9d0f9d1a48a48489425beab48274fca7bd0848e47a0bac3a027c01601e2c4");
            let m = &r[KINDS[5]];
            assert_eq!(m["all6_E2_model_rows"].as_array().unwrap().len(), 6);
            assert_eq!(
                r[KINDS[3]]["fixed_transported_mask_before_model_builder"],
                t["actual_transported_mask"]
            );
            assert_eq!(m["fixed_transported_mask"], t["actual_transported_mask"]);
            let matches: Vec<_> = m["all6_E2_model_rows"]
                .as_array()
                .unwrap()
                .iter()
                .filter(|row| row["kernel_mask"] == t["actual_transported_mask"])
                .collect();
            assert_eq!(matches.len(), 1);
            assert_eq!(*matches[0], m["whole_matched_row"]);
            let eligible = m["whole_matched_row"]["smooth"] == true
                && !m["whole_matched_row"]["sqrt_D_in_K"].is_null();
            assert_eq!(m["matched_eligible_prime_field_model"], eligible);
            let all: BTreeSet<_> = m["all135_and_rational_kernel_summary"]["all135_kernels"]
                .as_array()
                .unwrap()
                .iter()
                .map(|x| x["mask"].as_u64().unwrap())
                .collect();
            let independent: BTreeSet<_> = t["all135_independent_original_masks"]
                .as_array()
                .unwrap()
                .iter()
                .map(|x| x.as_u64().unwrap())
                .collect();
            assert_eq!(all, independent);
            save(&a[3], &r);
            println!("allSIX whole native records frozen NOmasks; matched_case={} eligible={} normalized_Fp_coefficients={} P0={} outcome={}",m["matched_case"],m["matched_eligible_prime_field_model"],m["whole_matched_row"]["normalized_Fp_coefficients"],m["whole_matched_row"]["P0"],m["outcome"]);
        }
        Some("--compare") => {
            assert_eq!(a.len(), 5);
            let expected: BTreeMap<String, Value> =
                serde_json::from_slice(&fs::read(&a[2]).unwrap()).unwrap();
            let actual = records(&a[3]);
            assert_eq!(expected, actual, "whole native JSON mismatch; NO masks");
            save(&a[4], &actual);
            println!("allSIX whole model/torsion records exact; NO masks");
        }
        Some("--report-inputs") => {
            assert_eq!(a.len(), 4);
            let r: BTreeMap<String, Value> =
                serde_json::from_slice(&fs::read(&a[2]).unwrap()).unwrap();
            let m = &r[KINDS[5]];
            let t = &r[KINDS[4]];
            let data = json!({"source":"87b61e80a62bc0ff6ee832f85e3c0826c74a1bb0","protocol":"23ab48","E2":m["E2_source_identity"],"matched_case":m["matched_case"],"matched_eligible":m["matched_eligible_prime_field_model"],"whole_matched_row":m["whole_matched_row"],"all6_model_rows":m["all6_E2_model_rows"],"actual_basis_permutation":t["actual_basis_permutation"],"fixed_mask":t["actual_transported_mask"],"untransported_control_same":t["untransported_control_same_as_actual"],"all_rational_masks":t["all_rational_masks"],"all135summary":m["all135_and_rational_kernel_summary"],"scope":"actual model/torsion preflight only, no second Jacobian map or cost advantage"});
            save(&a[3], &data);
            println!("matched_case={} eligible={} D={} sqrt_D={} smooth={} status={}; untransported_same={}; no second Jacobian map",m["matched_case"],m["matched_eligible_prime_field_model"],m["whole_matched_row"]["D"],m["whole_matched_row"]["sqrt_D_in_K"],m["whole_matched_row"]["smooth"],m["whole_matched_row"]["status"],t["untransported_control_same_as_actual"]);
        }
        _ => panic!(
            "--freeze raw output; --compare expected raw output; --report-inputs expected output"
        ),
    }
}
