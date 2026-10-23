use std::fs;
use std::path::PathBuf;
use std::process::{Command, Output};
use std::time::{SystemTime, UNIX_EPOCH};

struct RunDir(PathBuf);

impl RunDir {
    fn new(name: &str) -> Self {
        let nonce = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let path = std::env::temp_dir().join(format!("crax-{name}-{}-{nonce}", std::process::id()));
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
fn gnfs_resumes_saved_relations_and_rejects_corruption() {
    let run_dir = RunDir::new("gnfs-resume");
    let state = run_dir.0.join("state");
    let dir = state.to_str().unwrap();
    let common = [
        "gnfs",
        "1000000016000000063",
        "--state-dir",
        dir,
        "--checkpoint-every",
        "0",
        "--json",
    ];
    let first = run(&[&common[..], &["--max-b", "1"]].concat());
    assert!(!first.status.success());
    assert!(state.join("nfs.ckpt").is_file());
    let first_report: serde_json::Value = serde_json::from_slice(&first.stdout).unwrap();
    assert_eq!(first_report["lines_sieved"], 1);

    let resumed = run(&[&common[..], &["--resume", "--max-b", "5", "--threads", "2"]].concat());
    assert!(
        resumed.status.success(),
        "{}",
        String::from_utf8_lossy(&resumed.stderr)
    );
    let report: serde_json::Value = serde_json::from_slice(&resumed.stdout).unwrap();
    assert_eq!(report["verified"], true);
    assert_eq!(report["factor"], "1000000007");
    assert!(report["lines_sieved"].as_u64().unwrap() > 1);

    let result_before = fs::read(state.join("result.json")).unwrap();
    let checkpoint = state.join("nfs.ckpt");
    let mut bytes = fs::read(&checkpoint).unwrap();
    *bytes.last_mut().unwrap() ^= 1;
    fs::write(&checkpoint, bytes).unwrap();
    let corrupt = run(&[&common[..], &["--resume", "--max-b", "5"]].concat());
    assert!(!corrupt.status.success());
    assert!(String::from_utf8_lossy(&corrupt.stdout).contains("checksum mismatch"));
    assert_eq!(fs::read(state.join("result.json")).unwrap(), result_before);
}

#[test]
fn snfs_resumes_saved_relations() {
    let run_dir = RunDir::new("snfs-resume");
    let state = run_dir.0.join("state");
    let dir = state.to_str().unwrap();
    let common = [
        "snfs",
        "1000000016000000063",
        "--poly",
        "16000000063,0,0,1",
        "--m",
        "1000000",
        "--state-dir",
        dir,
        "--checkpoint-every",
        "0",
        "--json",
    ];
    let first = run(&[&common[..], &["--max-b", "1"]].concat());
    assert!(!first.status.success());
    assert!(state.join("nfs.ckpt").is_file());
    let first_report: serde_json::Value = serde_json::from_slice(&first.stdout).unwrap();
    assert_eq!(first_report["lines_sieved"], 1);

    let resumed = run(&[&common[..], &["--resume", "--max-b", "20"]].concat());
    assert!(
        resumed.status.success(),
        "{}",
        String::from_utf8_lossy(&resumed.stderr)
    );
    let report: serde_json::Value = serde_json::from_slice(&resumed.stdout).unwrap();
    assert_eq!(report["verified"], true);
    assert_eq!(report["factor"], "1000000007");
    assert!(report["lines_sieved"].as_u64().unwrap() > 1);
}

#[test]
fn s3_resume_checks_manifest_before_restoring_artifacts() {
    let run_dir = RunDir::new("nfs-s3-identity");
    let source = run_dir.0.join("source");
    let remote = run_dir.0.join("remote");
    let restored = run_dir.0.join("restored");
    fs::create_dir(&remote).unwrap();
    let bin = mock_s3(&run_dir);
    let dir = source.to_str().unwrap();
    let incomplete = run(&[
        "gnfs",
        "1000000016000000063",
        "--state-dir",
        dir,
        "--checkpoint-every",
        "0",
        "--max-b",
        "1",
        "--json",
    ]);
    assert!(!incomplete.status.success());
    fs::copy(source.join("manifest.json"), remote.join("manifest.json")).unwrap();
    fs::copy(source.join("nfs.ckpt"), remote.join("nfs.ckpt")).unwrap();

    let wrong_state = run_dir.0.join("wrong-state");
    let wrong = run_with_s3(
        &[
            "gnfs",
            "1000000016000000061",
            "--state-dir",
            wrong_state.to_str().unwrap(),
            "--resume",
            "--s3-uri",
            "s3://bucket/nfs",
            "--json",
        ],
        &bin,
        &remote,
        false,
    );
    assert!(!wrong.status.success());
    assert!(String::from_utf8_lossy(&wrong.stdout).contains("manifest differs"));
    assert!(!wrong_state.join("manifest.json").exists());
    assert!(!wrong_state.join("nfs.ckpt").exists());

    let interrupted = run_with_s3(
        &[
            "gnfs",
            "1000000016000000063",
            "--state-dir",
            restored.to_str().unwrap(),
            "--resume",
            "--s3-uri",
            "s3://bucket/nfs",
            "--max-b",
            "5",
            "--json",
        ],
        &bin,
        &remote,
        true,
    );
    assert!(!interrupted.status.success());
    assert!(restored.join("manifest.json").is_file());
    assert!(!restored.join("nfs.ckpt").exists());

    let resumed = run_with_s3(
        &[
            "gnfs",
            "1000000016000000063",
            "--state-dir",
            restored.to_str().unwrap(),
            "--resume",
            "--s3-uri",
            "s3://bucket/nfs",
            "--max-b",
            "5",
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
    assert_eq!(report["factor"], "1000000007");
}
