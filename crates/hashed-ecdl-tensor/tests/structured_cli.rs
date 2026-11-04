//! File/stdin consumer controls over public known-answer fixtures.
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    io::Write,
    process::{Command, Output, Stdio},
};

fn run(args: &[&str], input: &str) -> Output {
    let mut child = Command::new(env!("CARGO_BIN_EXE_tensor-structured"))
        .args(args)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child
        .stdin
        .take()
        .unwrap()
        .write_all(input.as_bytes())
        .unwrap();
    child.wait_with_output().unwrap()
}
fn fixture() -> Value {
    serde_json::from_str(include_str!("../examples/structured-prime.json")).unwrap()
}
fn success(output: Output) -> Value {
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    serde_json::from_slice(&output.stdout).unwrap()
}
fn rejection(input: &str, expected: &str) {
    let output = run(&["-"], input);
    assert!(!output.status.success());
    assert!(output.stdout.is_empty(), "failure must not emit a receipt");
    assert!(
        String::from_utf8_lossy(&output.stderr).contains(expected),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
}
#[test]
fn structured_consumer_counts_replays_and_rejects_a_rehashed_forgery() {
    let receipt = success(run(&["-"], &fixture().to_string()));
    assert_eq!(receipt["standing"], "producer_assertion");
    assert_eq!(
        receipt["semantic"]["relation_policy"],
        "ordered_signed_tuples_repetition_and_inverse_pairs_allowed"
    );
    let answers = receipt["semantic"]["answers"].as_array().unwrap();
    assert_eq!(
        answers
            .iter()
            .map(|a| a["count"].as_str().unwrap())
            .collect::<Vec<_>>(),
        ["2", "1", "1"]
    );
    assert!(answers
        .iter()
        .all(|a| a["witness"].as_array().unwrap().len() == 2));
    let queries = receipt["diagnostics"]["query_diagnostics"]
        .as_array()
        .unwrap();
    let total = receipt["diagnostics"]["setup_charged_steps"]
        .as_u64()
        .unwrap()
        + queries
            .iter()
            .map(|q| q["charged_steps"].as_u64().unwrap())
            .sum::<u64>();
    assert_eq!(receipt["diagnostics"]["total_charged_steps"], total);
    let replay = success(run(&["replay", "-"], &receipt.to_string()));
    assert_eq!(replay["status"], "replayed");
    assert_eq!(replay["semantic_sha256"], receipt["semantic_sha256"]);
    let mut capped = fixture();
    capped["steps"] = json!(
        receipt["diagnostics"]["setup_charged_steps"]
            .as_u64()
            .unwrap()
            + queries[0]["charged_steps"].as_u64().unwrap()
    );
    // The first query can complete, but the batch must emit no partial receipt
    // when the common budget is exhausted during a subsequent query.
    rejection(&capped.to_string(), "resource limit");
    let duplicate = receipt
        .to_string()
        .replacen("\"answers\":", "\"answers\":[],\"answers\":", 1);
    let output = run(&["replay", "-"], &duplicate);
    assert!(!output.status.success() && output.stdout.is_empty());
    assert!(String::from_utf8_lossy(&output.stderr).contains("duplicate field"));
    let mut wrong_source = receipt.clone();
    wrong_source["selected_source_pins"]["structured.rs"] = json!("00");
    let output = run(&["replay", "-"], &wrong_source.to_string());
    assert!(!output.status.success() && output.stdout.is_empty());
    let mut forged = receipt.clone();
    forged["semantic"]["answers"][0]["count"] = json!("999");
    forged["semantic_sha256"] = json!(format!(
        "{:x}",
        Sha256::digest(serde_json::to_vec(&forged["semantic"]).unwrap())
    ));
    let output = run(&["replay", "-"], &forged.to_string());
    assert!(!output.status.success() && output.stdout.is_empty());
    assert!(String::from_utf8_lossy(&output.stderr).contains("semantic replay differs"));
    let mut forged = receipt;
    forged["standing"] = json!("verified");
    let output = run(&["replay", "-"], &forged.to_string());
    assert!(!output.status.success() && output.stdout.is_empty());
}
#[test]
fn malformed_requests_and_resource_failures_emit_no_receipt() {
    for (field, value, expected) in [
        ("schema", json!("unknown"), "schema"),
        ("membership", json!("unknown"), "membership"),
        ("arity", json!(1), "arity"),
        ("targets", json!([]), "target"),
        ("image_x", json!([]), "image"),
        ("targets", json!([["5", "1"]]), "subgroup"),
        ("generator", json!(["0", "2"]), "generator"),
        ("p", json!("-5"), "decimal"),
        ("steps", json!(0), "resource limit"),
        ("vector", json!(1), "resource limit"),
        ("bits", json!(1), "resource limit"),
        ("unknown", json!(true), "unknown field"),
    ] {
        let mut request = fixture();
        request[field] = value;
        rejection(&request.to_string(), expected);
    }
    let duplicated = fixture()
        .to_string()
        .replacen("\"arity\":2", "\"arity\":2,\"arity\":2", 1);
    rejection(&duplicated, "duplicate field");
    rejection("{", "structured JSON");
    let output = run(&[], "");
    assert!(!output.status.success() && output.stdout.is_empty());
    assert!(run(&["--help"], "").status.success());
}
#[test]
fn both_membership_paths_preserve_exact_empty_fibre_results() {
    for membership in ["circuit", "fibre_message"] {
        let mut request = fixture();
        request["membership"] = json!(membership);
        request["image_x"] = json!(["0"]);
        let receipt = success(run(&["-"], &request.to_string()));
        for answer in receipt["semantic"]["answers"].as_array().unwrap() {
            assert_eq!(answer["count"], "0");
            assert!(answer["witness"].is_null());
        }
    }
}
