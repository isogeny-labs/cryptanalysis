//! Whole ordered records, including repeated actual subordinate constructor output.
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::fs;
#[derive(Debug, PartialEq, Serialize, Deserialize)]
struct Record {
    kind: String,
    data: Value,
}
const EDGE: [&str; 5] = [
    "N4_NONDUAL13_KERNEL_GATE",
    "N4_NEXT13_KERNEL_GATE",
    "N4_NEXT13_MAPS",
    "N4_NEXT13_POINTS",
    "N4_NEXT13_PUBLIC",
];
const MODEL: [&str; 9] = [
    "N4_NEXT13_MODEL_PARITY",
    "N4_NEXT13_CURRENT_J1",
    "N4_NONDUAL13_KERNEL_GATE",
    "N4_NONDUAL13_KERNEL_GATE",
    "N4_NEXT13_KERNEL_GATE",
    "N4_NEXT13_INTERMEDIATE_NEGATIVE",
    "N4_NEXT13_MODEL_SELECTION",
    "N4_NEXT13_PRODUCT_TRANSPORT",
    "N4_NEXT13_MATCHED_MODELS",
];
fn records(path: &str) -> Vec<Record> {
    let mut out = vec![];
    for line in fs::read_to_string(path).unwrap().lines() {
        if let Some(i) = line.find("N4_") {
            if let Some((kind, body)) = line[i..].split_once(' ') {
                if body.starts_with('{') && body.ends_with('}') {
                    out.push(Record {
                        kind: kind.into(),
                        data: serde_json::from_str(body).unwrap(),
                    });
                }
            }
        }
    }
    out
}
fn save(path: &str, v: &impl Serialize) {
    let mut b = serde_json::to_vec_pretty(v).unwrap();
    b.push(b'\n');
    fs::write(path, b).unwrap();
}
fn load(path: &str) -> Vec<Record> {
    serde_json::from_slice(&fs::read(path).unwrap()).unwrap()
}
fn count(v: &Value, n: usize) {
    assert_eq!(v.as_array().unwrap().len(), n);
}
fn check(phase: &str, raw: &str, r: &[Record]) {
    assert!(fs::read_to_string(raw)
        .unwrap()
        .contains("test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;"));
    let kinds: Vec<_> = r.iter().map(|x| x.kind.as_str()).collect();
    match phase {
        "edge" => {
            assert_eq!(kinds, EDGE);
            assert_eq!(r[0].data["actual_gcd_degree"], 12);
            assert_eq!(r[1].data["actual_gcd_degree"], 12);
            let m = &r[2].data;
            assert_eq!(m["middle_nondual_composite"], r[1].data);
            assert_eq!(m["old_backtrack_gcd_degree"], 168);
            assert_eq!(m["whole_middle169_curve_residual"], json!([]));
            assert!(!m["middle169_derivative"].as_array().unwrap().is_empty());
            for key in ["third_dual_after_forward_13", "third_forward_after_dual_13"] {
                assert_eq!(m[key]["whole_x_cross_residual"], json!([]));
                assert_eq!(m[key]["whole_y_cross_residual"], json!([]));
                assert_eq!(m[key]["degrees"], json!([169, 168]));
                assert_eq!(m[key]["coprime"], true);
            }
            let p = &r[3].data;
            count(&p["all36_source"], 36);
            count(&p["all36_target"], 36);
            count(&p["all1024_each_addition_pairs"], 1024);
            count(&p["actual_gamma3_torsion_images"], 4);
            count(&r[4].data["all_five"], 5);
        }
        "model" => {
            assert_eq!(kinds, MODEL);
            assert_eq!(
                r[2], r[3],
                "both actual prior constructor occurrences retained, not deduplicated"
            );
            assert_eq!(r[1].data["actual_original_norm_model_tag"],"Ciani-Jac-odd-product-v1-7ea9d0f9d1a48a48489425beab48274fca7bd0848e47a0bac3a027c01601e2c4");
            let old = &r[5].data;
            assert_eq!(old["actual_G2"], 1155175778390933505u64);
            assert_eq!(old["whole_prior_matched_row"]["D"], json!([12, 0, 0]));
            assert_eq!(
                old["whole_prior_matched_row"]["eligible_for_supplied_source_maps"],
                false
            );
            count(&old["all6_E2_model_rows"], 6);
            let t = &r[7].data;
            count(&t["all64_actual_coordinate_transports"], 64);
            count(
                &t["all4096_actual_coordinate_addition_and_pairing_rows"],
                4096,
            );
            count(&t["all3_actual_coefficient_conjugate_maps"], 3);
            count(&t["all135_independent_original_masks"], 135);
            assert_eq!(
                r[6].data["fixed_transported_mask_before_model_builder"],
                t["actual_transported_mask"]
            );
            let m = &r[8].data;
            assert_eq!(m["fixed_transported_mask"], t["actual_transported_mask"]);
            count(&m["all6_E3_model_rows"], 6);
            let matched: Vec<_> = m["all6_E3_model_rows"]
                .as_array()
                .unwrap()
                .iter()
                .filter(|x| x["kernel_mask"] == m["fixed_transported_mask"])
                .collect();
            assert_eq!(matched.len(), 1);
            assert_eq!(*matched[0], m["whole_matched_row"]);
            assert_eq!(
                m["matched_eligible_prime_field_model"],
                matched[0]["eligible_for_supplied_source_maps"]
            );
            if m["matched_eligible_prime_field_model"] == true {
                assert_eq!(matched[0]["smooth"], true);
                assert!(!matched[0]["sqrt_D_in_K"].is_null());
                assert!(!matched[0]["P0"].is_null());
                count(&matched[0]["normalized_Fp_coefficients"], 15);
            }
        }
        _ => panic!("phase must be edge or model"),
    }
}
fn main() {
    let a: Vec<_> = std::env::args().collect();
    match a.get(1).map(String::as_str) {
 Some("--freeze")=>{assert_eq!(a.len(),5);let r=records(&a[3]);check(&a[2],&a[3],&r);save(&a[4],&r);println!("{}: all{} ordered whole records frozen, NO masks, every occurrence retained",a[2],r.len());},
 Some("--compare")=>{assert_eq!(a.len(),6);let expected=load(&a[3]);let actual=records(&a[4]);check(&a[2],&a[4],&actual);assert_eq!(expected,actual,"whole record mismatch, NO masks");save(&a[5],&actual);println!("{}: all{} whole records exact, NO masks",a[2],actual.len());},
 Some("--control")=>{assert_eq!(a.len(),4);let r=records(&a[2]);assert_eq!(r.len(),2);assert_eq!(r[0].kind,EDGE[0]);assert_eq!(r[1].kind,EDGE[1]);assert_eq!(r[1].data["actual_gcd_degree"],168);assert_eq!(r[1].data["accepted_nondual"],false);assert!(fs::read_to_string(&a[2]).unwrap().contains("old second dual must fail next nondual kernel acceptance"));save(&a[3],&r);println!("actual old-second-dual control:168gcd/rejected gate retained");},
 Some("--report")=>{
  assert_eq!(a.len(),5);let e=load(&a[2]);let b=load(&a[3]);assert_eq!(e[0],b[2]);assert_eq!(e[0],b[3]);assert_eq!(e[1],b[4]);let maps=&e[2].data;let m=&b[8].data;let t=&b[7].data;
  assert_eq!(maps["E3"]["a"],m["E3_source_identity"]["a"]);assert_eq!(maps["E3"]["b"],m["E3_source_identity"]["b"]);
  let diag=|x:&Value|json!({"case":[x["root_index"],x["sign_index"]],"D":x["D"],"sqrt_D_in_K":x["sqrt_D_in_K"],"smooth":x["smooth"],"status":x["status"],"kernel_mask":x["kernel_mask"],"normalized_Fp_coefficients":x["normalized_Fp_coefficients"],"P0":x["P0"]});
  let d=json!({"source":"f0167e430befd4304b170689e8caebcbdabbc6ad","protocol":"bbfd74","E2_id":maps["E2_id"],"E2":maps["E2"],"E3_id":maps["E3_id"],"E3":m["E3_source_identity"],"E0_j_conjugates":maps["E0_j_conjugates"],"E1_j_conjugates":maps["E1_j_conjugates"],"E2_j_conjugates":maps["E2_j_conjugates"],"E3_j_conjugates":maps["E3_j_conjugates"],"E3_j_intersects_E0":maps["E3_j_intersects_E0"],"E3_j_intersects_E1":maps["E3_j_intersects_E1"],"E3_j_intersects_E2":maps["E3_j_intersects_E2"],"old_E2_negative":diag(&b[5].data["whole_prior_matched_row"]),"matched_case":m["matched_case"],"matched_eligible":m["matched_eligible_prime_field_model"],"matched_diagnostic":diag(&m["whole_matched_row"]),"all6_model_diagnostics":m["all6_E3_model_rows"].as_array().unwrap().iter().map(diag).collect::<Vec<_>>(),"actual_basis_permutation":t["actual_basis_permutation"],"fixed_mask":m["fixed_transported_mask"],"untransported_control_same":t["untransported_control_same_as_actual"],"candidate_middle_gcd_degree":12,"backtracking_middle_gcd_degree":168,"outcome":m["outcome"],"scope":"third elliptic and same-kernel model preflight only; no complete second Jacobian map, full2197 rational expansion or calibrated cost advantage"});save(&a[4],&d);
  println!("matched_case={} eligible={} D={} sqrtD={} smooth={} E3={} P0={} outcome={}",m["matched_case"],m["matched_eligible_prime_field_model"],m["whole_matched_row"]["D"],m["whole_matched_row"]["sqrt_D_in_K"],m["whole_matched_row"]["smooth"],maps["E3"],m["whole_matched_row"]["P0"],m["outcome"]);
 },
 _=>panic!("--freeze phase raw out; --compare phase expected raw out; --control raw out; --report edge model out") }
}
