//! Native CLI controls for opt-in solver paths; no runtime measurements.
use hashed_ecdl_tensor::optimized;
use serde_json::{json, Value};
use std::path::{Path, PathBuf};
use std::process::{Command, Output};

const BINARY: &str = env!("CARGO_BIN_EXE_hashed-ecdl");
const PROBLEM: &str = r#"{
    "p":"17", "a":"2", "b":"2", "r":"19", "cofactor":"1",
    "generator":["5","1"], "target":["10","6"], "slots":2,
    "hash_prime":"37", "threshold":"12", "trials":32, "columns":64,
    "fixture_seed":42, "steps":100000000
}"#;

struct Fixture(PathBuf);

impl Fixture {
    fn new() -> Self {
        let nonce = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let dir =
            std::env::temp_dir().join(format!("optimized-cli-{}-{nonce}", std::process::id()));
        std::fs::create_dir(&dir).unwrap();
        std::fs::write(dir.join("problem.json"), PROBLEM).unwrap();
        Self(dir)
    }

    fn path(&self, name: &str) -> PathBuf {
        self.0.join(name)
    }

    fn solve(&self, options: &Path, receipt: &Path) -> Output {
        Command::new(BINARY)
            .arg("solve-hashed-optimized")
            .arg(self.path("problem.json"))
            .arg(options)
            .arg(receipt)
            .output()
            .unwrap()
    }

    fn verify(&self, receipt: &Path) -> Output {
        Command::new(BINARY)
            .arg("verify")
            .arg(receipt)
            .output()
            .unwrap()
    }
}

impl Drop for Fixture {
    fn drop(&mut self) {
        let _ = std::fs::remove_dir_all(&self.0);
    }
}

fn success(result: &Output) {
    assert!(
        result.status.success(),
        "stdout: {}\nstderr: {}",
        String::from_utf8_lossy(&result.stdout),
        String::from_utf8_lossy(&result.stderr)
    );
}

#[test]
fn default_options_match_the_old_joint_receipt_and_replay() {
    let fixture = Fixture::new();
    let options = fixture.path("options.json");
    let output = fixture.path("optimized.json");
    std::fs::write(&options, "{}").unwrap();
    let result = fixture.solve(&options, &output);
    success(&result);
    assert_eq!(
        result.stdout,
        format!("receipt written {}\n", output.display()).as_bytes()
    );
    let bytes = std::fs::read(&output).unwrap();
    let receipt: Value = serde_json::from_slice(&bytes).unwrap();
    assert_eq!(receipt["schema"], "hashed-ecdl-tensor/v1");
    assert_eq!(receipt["diagnostics"]["backend"], "PreparedOptimized");
    assert_eq!(
        receipt["diagnostics"]["options"],
        serde_json::to_value(optimized::Options::default()).unwrap()
    );
    assert!(receipt["diagnostics"]["statistics"].is_object());
    assert_eq!(receipt["diagnostics"]["scalar_decimal"], "3");
    assert!(receipt["diagnostics"]["charged_steps"].as_u64().unwrap() > 0);
    success(&fixture.verify(&output));

    let old_output = fixture.path("old-joint.json");
    let old = Command::new(BINARY)
        .arg("solve-hashed-joint")
        .arg(fixture.path("problem.json"))
        .arg(&old_output)
        .output()
        .unwrap();
    success(&old);
    let old_receipt: Value = serde_json::from_slice(&std::fs::read(old_output).unwrap()).unwrap();
    assert_eq!(receipt["certificate"], old_receipt["certificate"]);
    assert!(!fixture.solve(&options, &output).status.success());
    assert_eq!(bytes, std::fs::read(&output).unwrap());
}

#[test]
fn all_five_options_produce_a_v1_receipt_with_effective_configuration() {
    let fixture = Fixture::new();
    let options = fixture.path("options.json");
    let output = fixture.path("all-five.json");
    let configured = json!({
        "subgroup_provenance": true,
        "batch_chunk": 8,
        "relation_graph": true,
        "extra_scans": 4,
        "walk": {"table_size":16,"block_length":16},
        "joint_targets": true
    });
    std::fs::write(&options, serde_json::to_vec(&configured).unwrap()).unwrap();
    let result = fixture.solve(&options, &output);
    success(&result);
    assert_eq!(
        result.stdout,
        format!("receipt written {}\n", output.display()).as_bytes()
    );
    let receipt: Value = serde_json::from_slice(&std::fs::read(&output).unwrap()).unwrap();
    assert_eq!(receipt["certificate"]["version"], 1);
    assert_eq!(receipt["diagnostics"]["options"], configured);
    assert_eq!(receipt["diagnostics"]["scalar_decimal"], "3");
    success(&fixture.verify(&output));
}

#[test]
fn options_reject_duplicates_unknown_fields_and_wrong_shapes_before_output() {
    let fixture = Fixture::new();
    let options = fixture.path("options.json");
    let output = fixture.path("must-not-exist.json");
    for invalid in [
        r#"{"batch_chunk":1,"batch_chunk":8}"#,
        r#"{"batch_chunk":1,"\u0062atch_chunk":8}"#,
        r#"{"walk":null,"walk":null}"#,
        r#"{"walk":{"table_size":16,"table_size":32,"block_length":16}}"#,
        r#"{"walk":{"table_size":16,"block_length":16,"unknown":0}}"#,
        r#"{"unknown":true}"#,
        r#"{"subgroup_provenance":1}"#,
        r#"{"extra_scans":-1}"#,
        r#"{"batch_chunk":"8"}"#,
        r#"{"batch_chunk":null}"#,
        r#"{"subgroup_provenance":null}"#,
        r#"{"relation_graph":null}"#,
        r#"{"extra_scans":null}"#,
        r#"{"joint_targets":null}"#,
        r#"{"walk":[]}"#,
        "null",
        "[]",
        "{}true",
    ] {
        std::fs::write(&options, invalid).unwrap();
        let result = fixture.solve(&options, &output);
        assert!(
            !result.status.success(),
            "unexpectedly accepted {invalid}: {}",
            String::from_utf8_lossy(&result.stdout)
        );
        assert!(!output.exists(), "invalid options created a receipt");
    }
}

#[test]
fn optimized_command_keeps_the_strict_problem_reader() {
    let fixture = Fixture::new();
    let options = fixture.path("options.json");
    let output = fixture.path("must-not-exist.json");
    std::fs::write(&options, "{}").unwrap();
    let duplicated = format!("{{\"target\":null,{}", &PROBLEM.trim()[1..]);
    std::fs::write(fixture.path("problem.json"), duplicated).unwrap();
    let result = fixture.solve(&options, &output);
    assert!(!result.status.success());
    assert!(String::from_utf8_lossy(&result.stderr).contains("duplicate field"));
    assert!(!output.exists());
}

#[test]
fn option_file_read_is_bounded_before_solving_or_creating_output() {
    let fixture = Fixture::new();
    let options = fixture.path("oversize.json");
    let output = fixture.path("must-not-exist.json");
    std::fs::write(&options, vec![b' '; 16 * 1024 * 1024 + 1]).unwrap();
    let result = fixture.solve(&options, &output);
    assert!(!result.status.success());
    assert!(String::from_utf8_lossy(&result.stderr).contains("exceeds 16 MiB"));
    assert!(!output.exists());
}

#[test]
fn replay_uses_the_certificate_not_the_options_or_statistics_diagnostics() {
    let fixture = Fixture::new();
    let options = fixture.path("options.json");
    let output = fixture.path("receipt.json");
    std::fs::write(&options, "{}").unwrap();
    success(&fixture.solve(&options, &output));
    let mut receipt: Value = serde_json::from_slice(&std::fs::read(&output).unwrap()).unwrap();
    receipt["diagnostics"] = json!({
        "backend": "untrusted diagnostic text",
        "options": {"unknown":"diagnostic data are not execution authority"},
        "statistics": null
    });
    std::fs::write(&output, serde_json::to_vec(&receipt).unwrap()).unwrap();
    success(&fixture.verify(&output));
    receipt["certificate"]["scalar"] = json!([0]);
    std::fs::write(&output, serde_json::to_vec(&receipt).unwrap()).unwrap();
    assert!(!fixture.verify(&output).status.success());
}

#[test]
fn optimized_command_requires_both_options_and_a_new_receipt_path() {
    let fixture = Fixture::new();
    let output = fixture.path("must-not-exist.json");
    let result = Command::new(BINARY)
        .arg("solve-hashed-optimized")
        .arg(fixture.path("problem.json"))
        .arg(&output)
        .output()
        .unwrap();
    assert!(!result.status.success());
    assert!(String::from_utf8_lossy(&result.stderr)
        .contains("solve-hashed-optimized PROBLEM.json OPTIONS.json NEW_RECEIPT.json"));
    assert!(!output.exists());
}
