use std::io::{BufRead, BufReader};
use std::process::{Command, Stdio};

#[cfg(unix)]
#[test]
fn external_json_diagnostics_arrive_before_completion() {
    let mut child = Command::new(env!("CARGO_BIN_EXE_crax"))
        .args([
            "--json",
            "crypto",
            "-c",
            "printf 'stage one\\n' >&2; sleep 1; printf '{\"answer\":42}\\n'",
        ])
        .env("CRAX_CRYPTO_BIN", "sh")
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    let mut stderr = BufReader::new(child.stderr.take().unwrap());
    let mut first_line = String::new();
    stderr.read_line(&mut first_line).unwrap();
    assert_eq!(first_line, "stage one\n");
    assert!(
        child.try_wait().unwrap().is_none(),
        "diagnostic was delayed"
    );
    let output = child.wait_with_output().unwrap();
    assert!(output.status.success());
    let report: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(report["report"]["answer"], 42);
    assert_eq!(report["diagnostics_text"], "stage one\n");
}

#[test]
fn icx_json_verbose_streams_stages_on_stderr() {
    let output = Command::new(env!("CARGO_BIN_EXE_crax"))
        .args([
            "icx",
            "run",
            "secp256k1",
            "--bits",
            "7",
            "--max-trials",
            "100",
            "--rho-runs",
            "0",
            "--json",
            "--verbose",
        ])
        .output()
        .unwrap();
    assert!(output.status.success());
    let report: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(report["operation"], "run");
    let diagnostics = String::from_utf8(output.stderr).unwrap();
    assert!(diagnostics.contains("Info:Relation collection:"));
}
