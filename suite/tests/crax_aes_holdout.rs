//! End-to-end CLI check of captured AES holdout handling.

use serde_json::Value;
use std::{fs, path::Path, process::Command, time::SystemTime};

fn invoke(args: &[&str]) -> (bool, Value) {
    let output = Command::new(env!("CARGO_BIN_EXE_crax"))
        .arg("--json")
        .arg("aes-attack")
        .args(args)
        .output()
        .expect("start crax");
    let value = serde_json::from_slice(&output.stdout).expect("JSON CLI report");
    (output.status.success(), value)
}

fn text(path: &Path) -> &str {
    path.to_str().expect("UTF-8 temp path")
}

#[test]
fn independent_differential_and_linear_holdouts_reject_tampering_and_overlap() {
    let nonce = SystemTime::now()
        .duration_since(SystemTime::UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let dir = std::env::temp_dir().join(format!("crax-aes-holdout-{}-{nonce}", std::process::id()));
    fs::create_dir(&dir).unwrap();

    for (technique, samples) in [("differential", "24"), ("linear", "64")] {
        let training = dir.join(format!("{technique}-training.json"));
        let holdout = dir.join(format!("{technique}-holdout.json"));
        let (ok, generated) = invoke(&[
            "--technique",
            technique,
            "--samples",
            samples,
            "--export-pairs-file",
            text(&training),
            "--export-verification-file",
            text(&holdout),
        ]);
        assert!(ok && generated["accepted"] == true, "{generated}");
        let replay_args = [
            "--technique",
            technique,
            "--pairs-file",
            text(&training),
            "--verification-file",
        ];
        let (ok, replay) = invoke(&[&replay_args[..], &[text(&holdout)]].concat());
        assert!(ok && replay["accepted"] == true, "{replay}");
        assert_eq!(
            replay["verification_pairs"],
            samples.parse::<usize>().unwrap()
        );
        let holdout_field = if technique == "differential" {
            "holdout_constraints_verified"
        } else {
            "holdout_verified"
        };
        assert_eq!(replay[holdout_field], true);

        let mut changed: Value = serde_json::from_slice(&fs::read(&holdout).unwrap()).unwrap();
        let cipher_field = if technique == "differential" {
            "c0"
        } else {
            "ciphertext"
        };
        let byte_index = if technique == "differential" { 1 } else { 0 };
        let original = changed["pairs"][0][cipher_field].as_str().unwrap();
        let mut bytes = hex::decode(original).unwrap();
        bytes[byte_index] ^= 1;
        changed["pairs"][0][cipher_field] = hex::encode(bytes).into();
        let damaged = dir.join(format!("{technique}-damaged.json"));
        fs::write(&damaged, serde_json::to_vec(&changed).unwrap()).unwrap();
        let (ok, rejected) = invoke(&[&replay_args[..], &[text(&damaged)]].concat());
        assert!(
            !ok && rejected["status"] == "verification_failed",
            "{rejected}"
        );

        let training_value: Value = serde_json::from_slice(&fs::read(&training).unwrap()).unwrap();
        let plain_field = if technique == "differential" {
            "p0"
        } else {
            "plaintext"
        };
        changed["pairs"][0][plain_field] = training_value["pairs"][0][plain_field].clone();
        let overlap = dir.join(format!("{technique}-overlap.json"));
        fs::write(&overlap, serde_json::to_vec(&changed).unwrap()).unwrap();
        let (ok, rejected) = invoke(&[&replay_args[..], &[text(&overlap)]].concat());
        assert!(
            !ok && rejected["error"].as_str().unwrap().contains("distinct"),
            "{rejected}"
        );
    }

    fs::remove_dir_all(dir).unwrap();
}
