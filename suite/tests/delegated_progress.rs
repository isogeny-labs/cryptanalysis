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

#[cfg(unix)]
#[test]
fn delegated_kangaroo_preserves_default_and_explicit_operation_budgets() {
    use std::os::unix::fs::PermissionsExt;
    let unique = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let dir = std::env::temp_dir().join(format!(
        "crax-native-budget-{}-{unique}",
        std::process::id()
    ));
    std::fs::create_dir(&dir).unwrap();
    let native = dir.join("cryptanalysis");
    std::fs::write(
        &native,
        br#"#!/bin/sh
budget=missing
while [ "$#" -gt 0 ]; do
    if [ "$1" = "--max-ops" ]; then
        shift
        budget="$1"
    fi
    shift
done
printf '{"status":"limit","observed_max_ops":%s}\n' "$budget"
exit 1
"#,
    )
    .unwrap();
    std::fs::set_permissions(&native, std::fs::Permissions::from_mode(0o700)).unwrap();
    for progress in [
        vec!["--verbose"],
        vec!["--progress-every", "1"],
        vec!["--state-dir", "unused-test-state"],
    ] {
        for (solver, explicit, expected) in [
            ("kangaroo", None, 1_000_000),
            ("kangaroo", Some("17"), 17),
            ("bsgs", None, 0),
        ] {
            let mut command = Command::new(env!("CARGO_BIN_EXE_crax"));
            command.args([
                "--json", solver, "--group", "zp", "--p", "1019", "--order", "1018", "--g", "2",
                "--x", "500", "--lo", "0", "--hi", "300",
            ]);
            command.args(&progress).env("CRAX_NATIVE_BIN", &native);
            if let Some(budget) = explicit {
                command.args(["--max-ops", budget]);
            }
            let output = command.output().unwrap();
            assert!(!output.status.success());
            let report: serde_json::Value = serde_json::from_slice(&output.stdout)
                .unwrap_or_else(|e| panic!("{e}: {}", String::from_utf8_lossy(&output.stderr)));
            assert_eq!(
                report["observed_max_ops"], expected,
                "{solver} {progress:?} {explicit:?}"
            );
        }
    }
    std::fs::remove_dir_all(dir).unwrap();
}
