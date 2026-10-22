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
