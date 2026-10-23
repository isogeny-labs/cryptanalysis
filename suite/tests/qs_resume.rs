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
         if [ \"$1\" = s3api ]; then printf '{\"KeyCount\":1}\\n'; exit 0; fi\n\
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

fn run_with_s3(
    args: &[&str],
    bin: &std::path::Path,
    remote: &std::path::Path,
    fail_sync: bool,
) -> Output {
    let path = format!(
        "{}:{}",
        bin.display(),
        std::env::var("PATH").unwrap_or_default()
    );
    Command::new(env!("CARGO_BIN_EXE_crax"))
        .args(args)
        .env("PATH", path)
        .env("CA_TEST_NFS_REMOTE", remote)
        .env("CA_TEST_NFS_FAIL_SYNC", if fail_sync { "1" } else { "0" })
        .output()
        .unwrap()
}

fn mock_s3(run_dir: &RunDir) -> PathBuf {
    let bin = run_dir.0.join("aws-bin");
    fs::create_dir(&bin).unwrap();
    let script = bin.join("aws");
    fs::write(
        &script,
        r#"#!/bin/sh
set -eu
remote=$CA_TEST_NFS_REMOTE
if [ "$1" = s3api ]; then printf '{"KeyCount":1}\n'; exit 0; fi
[ "$1" = s3 ] || exit 2
if [ "$2" = cp ]; then
  case "$3" in
    s3://*/manifest.json)
      if [ "$4" = - ]; then cat "$remote/manifest.json"; else cp "$remote/manifest.json" "$4"; fi ;;
    s3://*) name=$(basename "$3"); cp "$remote/$name" "$4" ;;
    *) case "$4" in s3://*) name=$(basename "$4"); cp "$3" "$remote/$name" ;; *) cp "$3" "$4" ;; esac ;;
  esac
  exit 0
fi
[ "$2" = sync ] || exit 2
[ "$CA_TEST_NFS_FAIL_SYNC" = 0 ] || exit 1
dst=$4
mkdir -p "$dst"
for file in "$remote"/*; do
  [ -f "$file" ] || continue
  [ "$(basename "$file")" = manifest.json ] && continue
  cp "$file" "$dst/"
done
"#,
    )
    .unwrap();
    use std::os::unix::fs::PermissionsExt;
    fs::set_permissions(&script, fs::Permissions::from_mode(0o755)).unwrap();
    bin
}

#[test]
fn qs_s3_resume_retries_after_interrupted_payload_restore() {
    let run_dir = RunDir::new();
    let source = run_dir.0.join("source");
    let remote = run_dir.0.join("remote");
    let restored = run_dir.0.join("restored");
    fs::create_dir(&remote).unwrap();
    let bin = mock_s3(&run_dir);
    let dir = source.to_str().unwrap();
    let incomplete = run(&[
        "qs",
        "100000000003900003000000000117",
        "--state-dir",
        dir,
        "--checkpoint-every",
        "0",
        "--max-a-values",
        "4",
        "--json",
    ]);
    assert!(!incomplete.status.success());
    fs::copy(source.join("manifest.json"), remote.join("manifest.json")).unwrap();
    fs::copy(source.join("qs.ckpt"), remote.join("qs.ckpt")).unwrap();

    let wrong_state = run_dir.0.join("wrong-state");
    let wrong = run_with_s3(
        &[
            "qs",
            "100000000003900003000000000119",
            "--state-dir",
            wrong_state.to_str().unwrap(),
            "--resume",
            "--s3-uri",
            "s3://bucket/qs",
            "--json",
        ],
        &bin,
        &remote,
        false,
    );
    assert!(!wrong.status.success());
    assert!(String::from_utf8_lossy(&wrong.stdout).contains("manifest differs"));
    assert!(!wrong_state.join("manifest.json").exists());
    assert!(!wrong_state.join("qs.ckpt").exists());

    let interrupted = run_with_s3(
        &[
            "qs",
            "100000000003900003000000000117",
            "--state-dir",
            restored.to_str().unwrap(),
            "--resume",
            "--s3-uri",
            "s3://bucket/qs",
            "--max-a-values",
            "40",
            "--json",
        ],
        &bin,
        &remote,
        true,
    );
    assert!(!interrupted.status.success());
    assert!(restored.join("manifest.json").is_file());
    assert!(!restored.join("qs.ckpt").exists());

    let resumed = run_with_s3(
        &[
            "qs",
            "100000000003900003000000000117",
            "--state-dir",
            restored.to_str().unwrap(),
            "--resume",
            "--s3-uri",
            "s3://bucket/qs",
            "--max-a-values",
            "40",
            "--json",
        ],
        &bin,
        &remote,
        false,
    );
    assert!(
        resumed.status.success(),
        "{}",
        String::from_utf8_lossy(&resumed.stderr)
    );
    let report: serde_json::Value = serde_json::from_slice(&resumed.stdout).unwrap();
    assert_eq!(report["verified"], true);
    assert_eq!(report["factor"], "1000000000039");
}
