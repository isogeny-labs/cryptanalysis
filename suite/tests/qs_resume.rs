use std::fs;
use std::path::PathBuf;
use std::process::{Command, Output};
use std::time::{SystemTime, UNIX_EPOCH};

struct RunDir(PathBuf);

impl RunDir {
    fn new() -> Self {
        let nonce = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let path = std::env::temp_dir().join(format!("crax-qs-{}-{nonce}", std::process::id()));
        fs::create_dir(&path).unwrap();
        Self(path)
    }
}

impl Drop for RunDir {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.0);
    }
}

fn run(args: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_crax"))
        .args(args)
        .output()
        .unwrap()
}

#[test]
fn fresh_s3_restore_checks_manifest_before_syncing_payloads() {
    use std::os::unix::fs::PermissionsExt;

    let run_dir = RunDir::new();
    let bin = run_dir.0.join("bin");
    fs::create_dir(&bin).unwrap();
    let aws = bin.join("aws");
    fs::write(
        &aws,
        "#!/bin/sh\n\
         printf '%s\\n' \"$*\" >> \"$AWS_LOG\"\n\
         if [ \"$1\" = s3 ] && [ \"$2\" = cp ] && [ \"$4\" = - ]; then\n\
           printf '%s\\n' '{\"schema_version\":1,\"method\":\"other\"}'\n\
           exit 0\n\
         fi\n\
         echo 'unexpected AWS operation' >&2\n\
         exit 98\n",
    )
    .unwrap();
    let mut permissions = fs::metadata(&aws).unwrap().permissions();
    permissions.set_mode(0o755);
    fs::set_permissions(&aws, permissions).unwrap();

    let state = run_dir.0.join("fresh-state");
    let log = run_dir.0.join("aws.log");
    let path = format!(
        "{}:{}",
        bin.display(),
        std::env::var("PATH").unwrap_or_default()
    );
    let output = Command::new(env!("CARGO_BIN_EXE_crax"))
        .args(["qs", "100000000003900003000000000117", "--state-dir"])
        .arg(&state)
        .args(["--resume", "--s3-uri", "s3://bucket/qs-run", "--json"])
        .env("PATH", path)
        .env("AWS_LOG", &log)
        .output()
        .unwrap();

    assert!(!output.status.success());
    let report = format!(
        "{}{}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(
        report.contains("S3 qs manifest differs from the requested run"),
        "{report}"
    );
    let calls = fs::read_to_string(log).unwrap();
    assert!(calls.contains("s3 cp s3://bucket/qs-run/manifest.json - --only-show-errors"));
    assert!(
        !calls.contains("s3 sync"),
        "unexpected payload restore: {calls}"
    );
}

#[test]
fn qs_resumes_polynomial_batches_and_preserves_result_on_bad_checkpoint() {
    let run_dir = RunDir::new();
    let state = run_dir.0.join("state");
    let dir = state.to_str().unwrap();
    let common = [
        "qs",
        "100000000003900003000000000117",
        "--state-dir",
        dir,
        "--checkpoint-every",
        "0",
        "--json",
    ];
    let first = run(&[&common[..], &["--max-a-values", "4"]].concat());
    assert!(!first.status.success());
    assert!(state.join("qs.ckpt").is_file());
    let first_report: serde_json::Value = serde_json::from_slice(&first.stdout).unwrap();
    assert_eq!(first_report["a_values"], 4);
    assert!(first_report["full_relations"].as_u64().unwrap() > 0);

    let second = run(&[
        &common[..],
        &["--resume", "--max-a-values", "40", "--threads", "2"],
    ]
    .concat());
    assert!(
        second.status.success(),
        "{}",
        String::from_utf8_lossy(&second.stderr)
    );
    let report: serde_json::Value = serde_json::from_slice(&second.stdout).unwrap();
    assert_eq!(report["verified"], true);
    assert_eq!(report["factor"], "1000000000039");
    assert!(report["a_values"].as_u64().unwrap() > 4);

    let before = fs::read(state.join("result.json")).unwrap();
    let mismatch = run(&[
        &common[..],
        &["--resume", "--max-a-values", "40", "--seed", "2"],
    ]
    .concat());
    assert!(!mismatch.status.success());
    assert_eq!(fs::read(state.join("result.json")).unwrap(), before);

    let checkpoint = state.join("qs.ckpt");
    let mut bytes = fs::read(&checkpoint).unwrap();
    *bytes.last_mut().unwrap() ^= 1;
    fs::write(&checkpoint, bytes).unwrap();
    let corrupt = run(&[&common[..], &["--resume", "--max-a-values", "40"]].concat());
    assert!(!corrupt.status.success());
    assert!(String::from_utf8_lossy(&corrupt.stdout).contains("checksum mismatch"));
    assert_eq!(fs::read(state.join("result.json")).unwrap(), before);
}
