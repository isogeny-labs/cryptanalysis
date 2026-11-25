//! Whole record custody and exact comparison; no ignored mathematical fields.
use serde_json::{json, Value};
use std::{collections::BTreeMap, fs};
const KINDS: [&str; 4] = [
    "N4_NONDUAL13_KERNEL_GATE",
    "N4_NONDUAL13_MAPS",
    "N4_NONDUAL13_POINTS",
    "N4_NONDUAL13_PUBLIC",
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
                        out.insert(kind.to_owned(), serde_json::from_str(body).unwrap())
                            .is_none(),
                        "duplicate whole record"
                    );
                }
            }
        }
    }
    assert_eq!(out.len(), 4, "whole native kind set mismatch");
    for k in KINDS {
        assert!(out.contains_key(k));
    }
    out
}
fn save(p: &str, v: &impl serde::Serialize) {
    let mut b = serde_json::to_vec_pretty(v).unwrap();
    b.push(b'\n');
    fs::write(p, b).unwrap();
}
fn main() {
    let a: Vec<_> = std::env::args().collect();
    match a.get(1).map(String::as_str) {
        Some("--freeze") => {
            assert_eq!(a.len(), 4);
            let text = fs::read_to_string(&a[2]).unwrap();
            assert!(text.contains(
                "test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;"
            ));
            let r = records(&a[2]);
            let m = &r[KINDS[1]];
            assert_eq!(m["protocol"], "23ab48");
            assert_eq!(m["E0"], json!({"a":[214,144,205],"b":[137,218,9]}));
            assert_eq!(m["E1"], json!({"a":[196,168,69],"b":[8,82,207]}));
            assert_eq!(
                m["E1_id"],
                "N4-E13-short-936b863521fdce08d2724c468f27979cb39d9443d082b4be14209bb08f408414"
            );
            assert_eq!(m["new_kernel"]["SEA_eigenvalue"], 2);
            assert_eq!(m["actual_second_dual_kernel"]["SEA_eigenvalue"], 4);
            assert_eq!(m["nondual_composite"], r[KINDS[0]]);
            assert_eq!(m["nondual_composite"]["accepted_nondual"], true);
            assert_eq!(m["nondual_composite"]["actual_gcd_degree"], 12);
            assert_eq!(m["old_backtrack_gcd_degree"], 168);
            assert_eq!(m["whole_composite169_curve_residual"], json!([]));
            assert!(!m["composite169_derivative"].as_array().unwrap().is_empty());
            for c in [
                "second_dual_after_forward_13",
                "second_forward_after_dual_13",
            ] {
                assert_eq!(m[c]["whole_x_cross_residual"], json!([]));
                assert_eq!(m[c]["whole_y_cross_residual"], json!([]));
            }
            let p = &r[KINDS[2]];
            assert_eq!(p["all36_source"].as_array().unwrap().len(), 36);
            assert_eq!(p["all36_target"].as_array().unwrap().len(), 36);
            assert_eq!(
                p["all1024_each_addition_pairs"].as_array().unwrap().len(),
                1024
            );
            assert_eq!(r[KINDS[3]]["all_five"].as_array().unwrap().len(), 5);
            assert_eq!(r[KINDS[3]]["elliptic_phase_only"], true);
            save(&a[3], &r);
            println!("allFOUR whole records frozen without masks; E2_id={} E2={} j_intersects_E0={}; elliptic phase only, matched F223 J2 not constructed",m["E2_id"],m["E2"],m["E2_j_intersects_E0"]);
        }
        Some("--report-inputs") => {
            assert_eq!(a.len(), 4);
            let r: BTreeMap<String, Value> =
                serde_json::from_slice(&fs::read(&a[2]).unwrap()).unwrap();
            let m = &r[KINDS[1]];
            let e0id = format!(
                "{}:short",
                m["first_map"]["source_quadratic_model"].as_str().unwrap()
            );
            let intersects_e1 = m["E2_j_conjugates"]
                .as_array()
                .unwrap()
                .iter()
                .any(|x| m["E1_j_conjugates"].as_array().unwrap().contains(x));
            let out = json!({"protocol":"23ab48","claim":"252fd8","field":"K=F223[z]/(z^3-3)","E0_id":e0id,"E0":m["E0"],"E1_id":m["E1_id"],"E1":m["E1"],"E2_id":m["E2_id"],"E2":m["E2"],"all_E0_j_conjugates":m["E0_j_conjugates"],"all_E1_j_conjugates":m["E1_j_conjugates"],"all_E2_j_conjugates":m["E2_j_conjugates"],"E2_j_intersects_E0":m["E2_j_intersects_E0"],"E2_j_intersects_E1":intersects_e1,"candidate_gcd_degree":m["nondual_composite"]["actual_gcd_degree"],"backtracking_gcd_degree":m["old_backtrack_gcd_degree"],"positive_unfiltered_tests":1,"whole_records":4,"source_points":r[KINDS[2]]["all36_source"].as_array().unwrap().len(),"target_points":r[KINDS[2]]["all36_target"].as_array().unwrap().len(),"addition_pairs_each":r[KINDS[2]]["all1024_each_addition_pairs"].as_array().unwrap().len(),"public_targets":r[KINDS[3]]["all_five"].as_array().unwrap().len(),"original_order":m["first_map"]["original_order"],"ell":m["first_map"]["ell"],"J2":"not constructed; full64-product transport and matched model remain phaseB","scope":"exact native recorded inputs projected in Rust; no new Jacobian or cost conclusion"});
            save(&a[3], &out);
            println!("{}", out);
        }
        Some("--compare") => {
            assert_eq!(a.len(), 5);
            let expected: BTreeMap<String, Value> =
                serde_json::from_slice(&fs::read(&a[2]).unwrap()).unwrap();
            let actual = records(&a[3]);
            assert_eq!(expected, actual, "whole native JSON mismatch; NO masks");
            save(&a[4], &actual);
            println!("allFOUR whole native records exact; NO masks");
        }
        _ => panic!("--freeze native output; --compare expected native output"),
    }
}
