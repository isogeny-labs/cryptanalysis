use serde_json::Value;
use std::{
    fs,
    path::Path,
    process::Command,
    time::{SystemTime, UNIX_EPOCH},
};
#[test]
fn immutable_qualification_and_no_overwrite() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR"));
    let bin = env!("CARGO_BIN_EXE_curve25519-torus-qualification");
    let temp = std::env::temp_dir().join(format!(
        "torus-native-{}-{}",
        std::process::id(),
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    fs::create_dir(&temp).unwrap();
    let frozen = temp.join("frozen");
    let out = temp.join("out");
    assert!(Command::new(bin)
        .arg("freeze")
        .arg(&frozen)
        .status()
        .unwrap()
        .success());
    let exe = frozen.join("qualifier");
    let mut run = Command::new(&exe);
    run.arg("qualify")
        .arg(root.join("cases"))
        .arg(root.join("known-triples.json"))
        .arg(&out);
    assert!(run.status().unwrap().success());
    let pre = fs::read(out.join("qualification-pre-call.json")).unwrap();
    let post: Value =
        serde_json::from_slice(&fs::read(out.join("qualification-post-call.json")).unwrap())
            .unwrap();
    assert_eq!(post["cases"].as_array().unwrap().len(), 5);
    for row in post["cases"].as_array().unwrap() {
        assert_eq!(row["solver_invoked"], false);
        assert_eq!(row["max_degree"], 2);
        if row["case"] == "actual_planted" {
            assert_eq!(row["variables"], 395);
            assert_eq!(row["known_triples_checked"], 1);
        }
    }
    let public: Value =
        serde_json::from_slice(&fs::read(out.join("actual_planted/case.json")).unwrap()).unwrap();
    assert!(public.get("kind").is_none());
    assert!(public.get("known_u_triples").is_none());
    assert!(!run.status().unwrap().success());
    assert_eq!(
        pre,
        fs::read(out.join("qualification-pre-call.json")).unwrap()
    );
    let mut perms = fs::metadata(&exe).unwrap().permissions();
    // Restore owner write permission only to delete this temporary test copy.
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        perms.set_mode(0o700);
    }
    fs::set_permissions(&exe, perms).unwrap();
    fs::remove_dir_all(temp).unwrap();
}
