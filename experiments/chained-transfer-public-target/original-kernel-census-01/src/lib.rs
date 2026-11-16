//! Finite original-source family only. Prospective0158c5 publishedc1cbc188.
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{collections::BTreeSet, fs, path::PathBuf, process::Command};
include!("../generated/bits.rs");

pub const PREFIX: &str = "N4_ORIGINAL_KERNEL_";
pub const DOMAINS: [&str; 3] = ["originalE2", "originalE3", "originalE4"];
pub const CLASSES: [&str; 7] = [
    "HEADER",
    "TRANSPORT",
    "VERTEX",
    "PAIR",
    "TRIPLE",
    "REJECTIONS",
    "SUMMARY",
];

pub fn digest(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
pub fn record(kind: &str, data: Value) -> Value {
    json!({"kind":format!("{PREFIX}{kind}"),"data":data})
}
pub fn vector_list(mask: u64) -> Vec<u8> {
    vs(mask)
}
pub fn binary_span(basis: [u8; 3]) -> u64 {
    span(basis)
}
pub fn kernel_dimension(mask: u64) -> u32 {
    dimension(mask)
}
pub fn frobenius(v: u8) -> u8 {
    frob(v)
}
pub fn alternating(a: u8, b: u8) -> u32 {
    pairing(a, b)
}

pub struct Inputs {
    pub header: Value,
    pub models: [Vec<Value>; 3],
    pub transports: [Value; 2],
}
fn read_pinned(name: &str, pins: &Value) -> Value {
    let root = PathBuf::from(std::env::var("N4_ORIGINAL_KERNEL_INPUTS").unwrap());
    let p = root.join(name);
    let compressed = fs::read(&p).unwrap();
    assert_eq!(digest(&compressed), pins[name]["sha256"].as_str().unwrap());
    assert_eq!(
        compressed.len() as u64,
        pins[name]["bytes"].as_u64().unwrap()
    );
    let output = Command::new("xz")
        .args(["-dc", "--"])
        .arg(&p)
        .output()
        .unwrap();
    assert!(output.status.success());
    serde_json::from_slice(&output.stdout).unwrap()
}
fn unique_record_field(rows: &Value, key: &str) -> Value {
    let hits = rows
        .as_array()
        .unwrap()
        .iter()
        .filter_map(|x| x["data"].get(key))
        .collect::<Vec<_>>();
    assert_eq!(hits.len(), 1, "{key}");
    hits[0].clone()
}
fn unique_record(rows: &Value, kind: &str) -> Value {
    let hits = rows
        .as_array()
        .unwrap()
        .iter()
        .filter(|x| x["kind"] == kind)
        .collect::<Vec<_>>();
    assert_eq!(hits.len(), 1, "{kind}");
    hits[0]["data"].clone()
}
pub fn inputs() -> Inputs {
    let pins: Value = serde_json::from_str(include_str!("../input-pins.json")).unwrap();
    let second = read_pinned("original-E2.json.xz", &pins);
    let e2 = second["N4_NONDUAL13_MATCHED_MODELS"]["all6_E2_model_rows"]
        .as_array()
        .unwrap()
        .clone();
    drop(second);
    let third = read_pinned("original-E3.json.xz", &pins);
    let e3 = unique_record_field(&third, "all6_E3_model_rows")
        .as_array()
        .unwrap()
        .clone();
    let t23 = unique_record(&third, "N4_NEXT13_PRODUCT_TRANSPORT");
    drop(third);
    let fourth = read_pinned("original-E4.json.xz", &pins);
    let e4 = unique_record_field(&fourth, "all6_original_rows")
        .as_array()
        .unwrap()
        .clone();
    let t34 = unique_record(&fourth, "N4_FOURTH_FIXED_KERNELS")["all_original_transport"].clone();
    drop(fourth);
    let models = [e2, e3, e4];
    for (domain, rows) in models.iter().enumerate() {
        assert_eq!(rows.len(), 6);
        let curated = read_pinned(&format!("curated-E{}.json.xz", domain + 2), &pins);
        assert_eq!(
            curated["all_six_whole_rows"],
            json!(rows),
            "every original field required"
        );
    }
    Inputs {
        header: json!({"protocol":"0158c5/c1cbc188 before implementation","published_compiled_source":std::env::var("N4_ORIGINAL_KERNEL_SOURCE").unwrap(),"original_prime":2773073,"full_source_order":11092292,"all_six_whole_input_files":pins,"scope":"finite original six-model family; old prime-only choices and fixed negatives unchanged"}),
        models,
        transports: [t23, t34],
    }
}

pub fn transport_map(t: &Value) -> [u8; 64] {
    let rows = t["all64_actual_coordinate_transports"].as_array().unwrap();
    assert_eq!(rows.len(), 64);
    let mut map = [255; 64];
    for (a, row) in rows.iter().enumerate() {
        assert_eq!(row["source_vector"], a);
        let image = row["image_vector"].as_u64().unwrap();
        assert!(image < 64);
        map[a] = image as u8;
    }
    map
}
pub fn all_masks(t: &Value) -> BTreeSet<u64> {
    let rows = t["all135_independent_original_masks"].as_array().unwrap();
    assert_eq!(rows.len(), 135);
    let masks = rows
        .iter()
        .map(|x| x.as_u64().unwrap())
        .collect::<BTreeSet<_>>();
    assert_eq!(masks.len(), 135);
    for &mask in &masks {
        assert_eq!(dimension(mask), 3);
    }
    masks
}
pub fn validate_transport(t: &Value) -> [u8; 64] {
    let map = transport_map(t);
    assert_eq!(map[0], 0);
    assert_eq!(map.iter().copied().collect::<BTreeSet<_>>().len(), 64);
    let permutation = t["actual_basis_permutation"].as_array().unwrap();
    assert_eq!(permutation.len(), 4);
    assert_eq!(permutation[0], 0);
    assert_eq!(
        permutation
            .iter()
            .map(|x| x.as_u64().unwrap())
            .collect::<BTreeSet<_>>(),
        (0..4).collect::<BTreeSet<u64>>()
    );
    let rows = t["all64_actual_coordinate_transports"].as_array().unwrap();
    for a in 0..64u8 {
        let mut from_basis = 0;
        for bit in 0..6 {
            if a & (1 << bit) != 0 {
                from_basis ^= map[1usize << bit];
            }
        }
        assert_eq!(map[a as usize], from_basis);
        let from_factors = (0..3).fold(0, |out, i| {
            out | ((permutation[((a >> (2 * i)) & 3) as usize].as_u64().unwrap() as u8) << (2 * i))
        });
        assert_eq!(map[a as usize], from_factors);
        assert_eq!(rows[a as usize]["Frobenius_source_vector"], frob(a));
        assert_eq!(
            rows[a as usize]["Frobenius_image_vector"],
            frob(map[a as usize])
        );
        assert_eq!(map[frob(a) as usize], frob(map[a as usize]));
    }
    let pairs = t["all4096_actual_coordinate_addition_and_pairing_rows"]
        .as_array()
        .unwrap();
    assert_eq!(pairs.len(), 4096);
    for a in 0..64u8 {
        for b in 0..64u8 {
            let row = &pairs[a as usize * 64 + b as usize];
            assert_eq!(row["a"], a);
            assert_eq!(row["b"], b);
            assert_eq!(map[(a ^ b) as usize], map[a as usize] ^ map[b as usize]);
            assert_eq!(pairing(a, b), pairing(map[a as usize], map[b as usize]));
            assert_eq!(row["source_pairing"], pairing(a, b));
            assert_eq!(
                row["image_pairing"],
                pairing(map[a as usize], map[b as usize])
            );
            assert_eq!(
                row["source_sum_actual"],
                rows[(a ^ b) as usize]["source_actual_coordinates"]
            );
            assert_eq!(
                row["image_sum_actual"],
                rows[(a ^ b) as usize]["image_actual_coordinates"]
            );
        }
    }
    let masks = all_masks(t);
    let stable = masks
        .iter()
        .copied()
        .filter(|&g| vs(g).iter().all(|&v| g & (1u64 << frob(v)) != 0))
        .collect::<BTreeSet<_>>();
    assert_eq!(
        t["all_rational_masks"]
            .as_array()
            .unwrap()
            .iter()
            .map(|x| x.as_u64().unwrap())
            .collect::<BTreeSet<_>>(),
        stable
    );
    t["all3_actual_coefficient_conjugate_maps"]
        .as_array()
        .map(|x| assert_eq!(x.len(), 3))
        .unwrap();
    map
}
pub fn eligibility(row: &Value) -> bool {
    let d = row["D"].as_array().unwrap();
    assert_eq!(d.len(), 3);
    assert_eq!(d[1], 0);
    assert_eq!(d[2], 0);
    let d = d[0].as_u64().unwrap();
    assert!(d < 223);
    let square = (0..223u64).any(|root| root * root % 223 == d);
    assert_eq!(row["D_square_in_Fp_and_K"], square);
    let root = &row["sqrt_D_in_K"];
    assert_eq!(!root.is_null(), square);
    if !root.is_null() {
        let a = root.as_array().unwrap();
        assert_eq!(a.len(), 3);
        assert_eq!(a[1], 0);
        assert_eq!(a[2], 0);
        let a = a[0].as_u64().unwrap();
        assert!(a < 223);
        assert_eq!(a * a % 223, d);
    }
    let factors = row["seven_smoothness_factors"].as_array().unwrap();
    assert_eq!(factors.len(), 7);
    let smooth = factors.iter().all(|x| {
        let a = x.as_array().unwrap();
        assert_eq!(a.len(), 3);
        a.iter().any(|v| v.as_u64().unwrap() != 0)
    });
    assert_eq!(row["smooth"], smooth);
    assert_eq!(row["original_smoothness_certificate_agrees"], true);
    let eligible = smooth && !root.is_null();
    assert_eq!(row["eligible_for_supplied_source_maps"], eligible);
    let coefficients = row["normalized_Fp_coefficients"].as_array().unwrap();
    assert_eq!(coefficients.len(), 15);
    assert!(coefficients.iter().all(|x| x.as_u64().unwrap() < 223));
    if eligible {
        assert_ne!(d, 0);
        let p = row["P0"].as_array().unwrap();
        assert_eq!(p.len(), 3);
        assert!(p.iter().all(|x| x.as_u64().unwrap() < 223));
        assert!(row["all_rational_points"]
            .as_array()
            .unwrap()
            .contains(&row["P0"]));
    }
    eligible
}
pub fn validate_model(domain: usize, index: usize, row: &Value, masks: &BTreeSet<u64>) -> bool {
    assert!(domain < 3 && index < 6);
    assert_eq!(row["root_index"], index / 2);
    assert_eq!(row["sign_index"], index % 2);
    let mask = row["kernel_mask"].as_u64().unwrap();
    assert_eq!(dimension(mask), 3);
    assert!(masks.contains(&mask));
    assert!(vs(mask).iter().all(|&v| mask & (1u64 << frob(v)) != 0));
    eligibility(row)
}
pub fn transported_bitset(mask: u64, map: &[u8; 64]) -> u64 {
    bits(
        &vs(mask)
            .iter()
            .map(|&v| map[v as usize])
            .collect::<Vec<_>>(),
    )
}
pub fn transported_basis(mask: u64, map: &[u8; 64]) -> u64 {
    let mut basis = Vec::new();
    let mut space = BTreeSet::from([0u8]);
    for v in 0..64u8 {
        if mask & (1u64 << v) != 0 && !space.contains(&v) {
            let old = space.clone();
            space.extend(old.iter().map(|&x| x ^ v));
            basis.push(v);
        }
    }
    assert_eq!(basis.len(), 3);
    assert_eq!(bits(&space.into_iter().collect::<Vec<_>>()), mask);
    span([
        map[basis[0] as usize],
        map[basis[1] as usize],
        map[basis[2] as usize],
    ])
}

fn rejected(f: impl FnOnce() + std::panic::UnwindSafe) -> bool {
    assert!(
        std::panic::catch_unwind(f).is_err(),
        "malformed input was accepted"
    );
    true
}
fn rejection_controls(inputs: &Inputs, masks: &BTreeSet<u64>) -> Value {
    let hook = std::panic::take_hook();
    std::panic::set_hook(Box::new(|_| {}));
    let mut duplicate = inputs.transports[0].clone();
    duplicate["actual_basis_permutation"][1] = json!(0);
    let duplicate_permutation = rejected(|| {
        validate_transport(&duplicate);
    });
    let mut coordinate = inputs.transports[0].clone();
    coordinate["all64_actual_coordinate_transports"][1]["source_vector"] = json!(0);
    let duplicated_coordinate = rejected(|| {
        validate_transport(&coordinate);
    });
    let mut pair = inputs.transports[0].clone();
    let old = pair["all4096_actual_coordinate_addition_and_pairing_rows"][1]["source_pairing"]
        .as_u64()
        .unwrap();
    pair["all4096_actual_coordinate_addition_and_pairing_rows"][1]["source_pairing"] =
        json!(old ^ 1);
    let altered_pairing = rejected(|| {
        validate_transport(&pair);
    });
    let mut zero = inputs.models[0][0].clone();
    zero["kernel_mask"] = json!(0);
    let zero_kernel = rejected(|| {
        validate_model(0, 0, &zero, masks);
    });
    let mut kernel = inputs.models[0][0].clone();
    kernel["kernel_mask"] = json!(kernel["kernel_mask"].as_u64().unwrap() ^ 1);
    let altered_kernel = rejected(|| {
        validate_model(0, 0, &kernel, masks);
    });
    let mut eligible = inputs.models[0][0].clone();
    eligible["eligible_for_supplied_source_maps"] = json!(!eligible
        ["eligible_for_supplied_source_maps"]
        .as_bool()
        .unwrap());
    let altered_eligibility = rejected(|| {
        validate_model(0, 0, &eligible, masks);
    });
    std::panic::set_hook(hook);
    json!({"duplicate_permutation_rejected":duplicate_permutation,"duplicated_coordinate_rejected":duplicated_coordinate,"altered_stored_pairing_rejected":altered_pairing,"zero_kernel_rejected":zero_kernel,"altered_kernel_rejected":altered_kernel,"altered_eligibility_rejected":altered_eligibility,"method":"actual cloned malformed inputs passed to original validation functions; each must panic"})
}
pub fn records(use_basis: bool) -> Vec<Value> {
    let inputs = inputs();
    let maps = inputs.transports.each_ref().map(|t| validate_transport(t));
    let masks = all_masks(&inputs.transports[0]);
    assert_eq!(masks, all_masks(&inputs.transports[1]));
    let flags: [[bool; 6]; 3] = std::array::from_fn(|d| {
        std::array::from_fn(|i| validate_model(d, i, &inputs.models[d][i], &masks))
    });
    for rows in &inputs.models {
        assert_eq!(
            rows.iter()
                .map(|r| r["kernel_mask"].as_u64().unwrap())
                .collect::<BTreeSet<_>>()
                .len(),
            6
        );
    }
    let mut out = vec![record("HEADER", inputs.header.clone())];
    for edge in 0..2 {
        out.push(record("TRANSPORT",json!({"edge":edge,"from":DOMAINS[edge],"to":DOMAINS[edge+1],"whole_original_transport":inputs.transports[edge],"all64_basis_and_factor_images_checked":true,"all4096_actual_coordinate_sum_pairing_rows_checked":true,"all135_original_masks_checked":true,"scope":"finite revalidation of actual old coordinate certificate; no new elliptic or Miller backend"})));
    }
    for d in 0..3 {
        for i in 0..6 {
            out.push(record("VERTEX",json!({"domain":d,"source":DOMAINS[d],"index":i,"case":[i/2,i%2],"kernel_mask":inputs.models[d][i]["kernel_mask"],"supplied_source_eligible":flags[d][i],"whole_original_row":inputs.models[d][i]})));
        }
    }
    let mut compatible = [[[false; 6]; 6]; 2];
    let mut supported = compatible;
    for edge in 0..2 {
        for i in 0..6 {
            let source = inputs.models[edge][i]["kernel_mask"].as_u64().unwrap();
            let by_bits = transported_bitset(source, &maps[edge]);
            let by_basis = transported_basis(source, &maps[edge]);
            assert_eq!(by_bits, by_basis);
            let image = if use_basis { by_basis } else { by_bits };
            assert_eq!(dimension(image), 3);
            assert!(masks.contains(&image));
            let vectors = vs(source)
                .iter()
                .map(|&a| json!({"source_vector":a,"image_vector":maps[edge][a as usize]}))
                .collect::<Vec<_>>();
            assert_eq!(vectors.len(), 8);
            for j in 0..6 {
                let target = inputs.models[edge + 1][j]["kernel_mask"].as_u64().unwrap();
                let same = image == target;
                compatible[edge][i][j] = same;
                supported[edge][i][j] = same && flags[edge][i] && flags[edge + 1][j];
                let mut failed = Vec::new();
                if !flags[edge][i] {
                    failed.push("source_supplied_model_ineligible");
                }
                if !flags[edge + 1][j] {
                    failed.push("target_supplied_model_ineligible");
                }
                if !same {
                    failed.push("transported_kernel_mismatch");
                }
                out.push(record("PAIR",json!({"edge":edge,"pair_index":edge*36+i*6+j,"source_index":i,"target_index":j,"source_case":[i/2,i%2],"target_case":[j/2,j%2],"source_mask":source,"target_mask":target,"all8_source_and_image_vectors":vectors,"transported_source_mask":image,"kernel_compatible":same,"source_eligible":flags[edge][i],"target_eligible":flags[edge+1][j],"eligible_endpoints":flags[edge][i]&&flags[edge+1][j],"supported_compatible":supported[edge][i][j],"failed_conditions":failed})));
            }
        }
    }
    let mut accepted = Vec::new();
    for i in 0..6 {
        for j in 0..6 {
            for k in 0..6 {
                let pass = supported[0][i][j] && supported[1][j][k];
                if pass {
                    accepted.push([i, j, k]);
                }
                let mut failed = Vec::new();
                for (d, index) in [i, j, k].into_iter().enumerate() {
                    if !flags[d][index] {
                        failed.push(format!("{}_supplied_model_ineligible", DOMAINS[d]));
                    }
                }
                if !compatible[0][i][j] {
                    failed.push("E2_to_E3_kernel_mismatch".to_owned());
                }
                if !compatible[1][j][k] {
                    failed.push("E3_to_E4_kernel_mismatch".to_owned());
                }
                out.push(record("TRIPLE",json!({"indices":[i,j,k],"cases":[[i/2,i%2],[j/2,j%2],[k/2,k%2]],"pair_indices":[i*6+j,36+j*6+k],"all_three_eligibility_flags":[flags[0][i],flags[1][j],flags[2][k]],"both_kernel_compatibility":[compatible[0][i][j],compatible[1][j][k]],"both_supported_pair_flags":[supported[0][i][j],supported[1][j][k]],"supported_compatible_chain":pass,"failed_conditions":failed})));
            }
        }
    }
    out.push(record("REJECTIONS", rejection_controls(&inputs, &masks)));
    out.push(record("SUMMARY",json!({"vertices":18,"adjacent_candidate_pairs":72,"triples":216,"ordered_whole_records":311,"eligible_vertices_per_domain":flags.map(|r|r.into_iter().filter(|&x|x).count()),"kernel_compatible_pairs_per_edge":compatible.map(|r|r.into_iter().flatten().filter(|&x|x).count()),"supported_compatible_pairs_per_edge":supported.map(|r|r.into_iter().flatten().filter(|&x|x).count()),"all_accepted_triples_lexicographic":accepted,"accepted_triple_count":accepted.len(),"old_fixed_negatives_and_prime_only_cases_unchanged":true,"scope":"exhaustive finite original six-model family only; geometric HLP/base-field/program bridges remain; no evaluator or cost result"})));
    assert_eq!(out.len(), 311);
    out
}
pub fn assert_order(rows: &[Value]) {
    let mut kinds = vec!["HEADER"];
    kinds.extend(["TRANSPORT"; 2]);
    kinds.extend(["VERTEX"; 18]);
    kinds.extend(["PAIR"; 72]);
    kinds.extend(["TRIPLE"; 216]);
    kinds.extend(["REJECTIONS", "SUMMARY"]);
    assert_eq!(rows.len(), 311, "all311 whole occurrences required");
    for (r, k) in rows.iter().zip(kinds) {
        assert_eq!(r["kind"], format!("{PREFIX}{k}"));
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn exhaustive_original_kernel_family() {
        let rows = records(false);
        assert_order(&rows);
        for row in rows {
            println!("{} {}", row["kind"].as_str().unwrap(), row["data"]);
        }
    }
}
