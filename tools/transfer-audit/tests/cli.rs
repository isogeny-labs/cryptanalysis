use std::{fs, process::Command};
#[test]
fn cli_replay_tamper_and_overwrite() {
    let dir = std::env::temp_dir().join(format!("transfer-audit-cli-{}", std::process::id()));
    fs::create_dir(&dir).unwrap();
    let input = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("fixtures/toy-f8.json");
    let out = dir.join("certificate.json");
    let run = || {
        Command::new(env!("CARGO_BIN_EXE_transfer-audit"))
            .arg("audit")
            .arg("--input")
            .arg(&input)
            .arg("--output")
            .arg(&out)
            .output()
            .unwrap()
    };
    assert!(run().status.success());
    let original = fs::read(&out).unwrap();
    assert!(!run().status.success());
    assert_eq!(fs::read(&out).unwrap(), original);
    let check = || {
        Command::new(env!("CARGO_BIN_EXE_transfer-audit"))
            .arg("verify")
            .arg("--certificate")
            .arg(&out)
            .output()
            .unwrap()
    };
    assert!(check().status.success());
    let mut cert: serde_json::Value = serde_json::from_slice(&original).unwrap();
    cert["isogeny_class"]["members"]
        .as_array_mut()
        .unwrap()
        .pop();
    fs::write(&out, serde_json::to_vec(&cert).unwrap()).unwrap();
    assert!(!check().status.success());
    fs::remove_dir_all(dir).unwrap();
}
