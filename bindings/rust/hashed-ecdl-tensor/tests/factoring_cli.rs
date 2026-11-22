use std::process::Command;

#[test]
fn runner_factors_public_fixture_and_emits_no_success_on_exhaustion() {
    let output = Command::new(env!("CARGO_BIN_EXE_tensor-factor"))
        .args(["12", "100000000"])
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let value: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(value["factors"], serde_json::json!(["2", "2", "3"]));
    assert_eq!(value["algorithm"], "divisor-prefix-counting");
    for args in [["12", "0"], ["0", "100000000"], ["-1", "100000000"]] {
        let output = Command::new(env!("CARGO_BIN_EXE_tensor-factor"))
            .args(args)
            .output()
            .unwrap();
        assert!(!output.status.success());
        assert!(output.stdout.is_empty());
        assert!(!output.stderr.is_empty());
    }
}
