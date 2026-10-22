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
