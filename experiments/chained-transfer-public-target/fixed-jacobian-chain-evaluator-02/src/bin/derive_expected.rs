//! Exact prospective counter transformation of the entire genuine baseline.
use ghs_original_engines::digest::sha256;
use serde_json::Value;
use std::{collections::BTreeSet, fs, path::Path};
fn keys(value: &Value) -> BTreeSet<&str> {
    value
        .as_object()
        .unwrap()
        .keys()
        .map(String::as_str)
        .collect()
}
fn schema<'a>(names: &'a [&'a str]) -> BTreeSet<&'a str> {
    names.iter().copied().collect()
}
fn main() {
    let args: Vec<String> = std::env::args().collect();
    assert_eq!(args.len(), 3, "DERIVE ORIGINAL-WHOLE695 OUTPUT");
    assert!(!Path::new(&args[2]).exists());
    let bytes = fs::read(&args[1]).unwrap();
    assert_eq!(bytes.len(), 123633074, "whole genuine baseline byte length");
    let hash = sha256(&bytes)
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect::<String>();
    assert_eq!(
        hash,
        "da48602ba10420d3363be3df874ca3c8eb805cad0615eeb403710a6a03a60f36"
    );
    let mut rows: Vec<Value> = serde_json::from_slice(&bytes).unwrap();
    assert_eq!(rows.len(), 695);
    assert_eq!(
        rows.iter()
            .filter(|r| r["kind"] == "N4_FIXED_CHAIN_SELECTED_CALL_VECTORS")
            .count(),
        1
    );
    let row = &mut rows[692];
    assert_eq!(keys(row), schema(&["kind", "data"]));
    assert_eq!(row["kind"], "N4_FIXED_CHAIN_SELECTED_CALL_VECTORS");
    assert_eq!(keys(&row["data"]), schema(&["all48", "scope"]));
    let vectors = row["data"]["all48"].as_array_mut().unwrap();
    assert_eq!(vectors.len(), 48);
    let call_keys = schema(&[
        "external_packet_parse",
        "external_norm_and_geometry",
        "external_full_order",
        "infinity_halves",
        "two_torsion_halves",
        "generic_halving_factorization",
        "generic_ordinate",
        "explicit_half_check",
        "quadratic_source_phi",
        "correction_difference",
        "correction_dictionary_lookup",
        "matching_corrections_checked",
        "source_lift_addition",
        "degree13_elliptic_evaluation",
        "degree169_elliptic_evaluation",
        "quadratic_target_phi",
        "target_correction_addition",
        "final_actual_norm",
        "final_full_order",
        "inverse_full_group_scalar",
    ]);
    for (i, vector) in vectors.iter_mut().enumerate() {
        assert_eq!(
            keys(vector),
            schema(&[
                "from",
                "to",
                "scalar_OUTSIDE_runtime",
                "sector",
                "input",
                "direct_composite",
                "literal_sequential_Jacobian_maps",
                "strongest_retained_lift_chain",
                "whole_outputs_equal",
            ])
        );
        let (from, to) = if i < 24 { (0, 2) } else { (2, 0) };
        assert_eq!(vector["from"], from);
        assert_eq!(vector["to"], to);
        assert_eq!(vector["sector"], i % 4);
        assert_eq!(
            vector["scalar_OUTSIDE_runtime"],
            [0u64, 1, 2, 17, 12345, 2771710][(i % 24) / 4]
        );
        for (route, n13, n169, doubling, phis) in [
            ("direct_composite", 0, 2, 1, 1),
            ("literal_sequential_Jacobian_maps", 4, 0, 2, 2),
            ("strongest_retained_lift_chain", 4, 0, 1, 1),
        ] {
            let counters = &mut vector[route];
            assert_eq!(
                keys(counters),
                call_keys,
                "entire original counter schema required"
            );
            assert!(counters
                .as_object()
                .unwrap()
                .values()
                .all(|v| v.as_u64().is_some()));
            assert_eq!(counters["degree13_elliptic_evaluation"], n13);
            assert_eq!(counters["degree169_elliptic_evaluation"], n169);
            for key in [
                "external_packet_parse",
                "external_norm_and_geometry",
                "external_full_order",
                "final_actual_norm",
                "final_full_order",
            ] {
                assert_eq!(counters[key], 1);
            }
            for key in [
                "quadratic_source_phi",
                "quadratic_target_phi",
                "correction_dictionary_lookup",
            ] {
                assert_eq!(counters[key], phis);
            }
            counters["degree13_elliptic_evaluation"] = Value::from(n13 / 2);
            counters["degree169_elliptic_evaluation"] = Value::from(n169 / 2);
            counters
                .as_object_mut()
                .unwrap()
                .insert("transported_norm_doubling".into(), Value::from(doubling));
        }
    }
    // Serialize the whole clone: no other field or ordered occurrence is removed.
    let output = serde_json::to_vec(&rows).unwrap();
    fs::write(&args[2], &output).unwrap();
    println!(
        "whole695 baselineSHA={hash} exact48 counter transforms outputBytes={} outputSHA={}",
        output.len(),
        sha256(&output)
            .iter()
            .map(|b| format!("{b:02x}"))
            .collect::<String>()
    );
}
