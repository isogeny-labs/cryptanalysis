use serde_json::Value;
use std::{
    fs,
    path::PathBuf,
    process::Command,
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT: AtomicU64 = AtomicU64::new(0);
fn directory() -> PathBuf {
    let path = std::env::temp_dir().join(format!(
        "ic-fixed-test-{}-{}",
        std::process::id(),
        NEXT.fetch_add(1, Ordering::Relaxed)
    ));
    fs::create_dir(&path).unwrap();
    path
}
fn params() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("docs/ic/params/k0n9-fixed.json")
}

fn run(path: &PathBuf, params: &PathBuf, stage: &str, pairs: u32) -> (bool, Value) {
    let output = Command::new(env!("CARGO_BIN_EXE_ca-ic"))
        .args(["fixed", "--params"])
        .arg(params)
        .arg("--dir")
        .arg(path)
        .args([
            "--stage",
            stage,
            "--pair-budget",
            &pairs.to_string(),
            "--attempts",
            "256",
            "--query-seconds",
            "2",
            "--json",
        ])
        .output()
        .unwrap();
    let report = serde_json::from_slice(&output.stdout)
        .unwrap_or_else(|_| panic!("{}", String::from_utf8_lossy(&output.stderr)));
    (output.status.success(), report)
}

#[test]
fn fixed_cli_preserves_incomplete_then_resumes_and_reuses() {
    let path = directory();
    let params = params();
    let (success, partial) = run(&path, &params, "pairs", 7);
    assert!(!success);
    assert_eq!(partial["status"], "pair_budget");
    let (success, pending) = run(&path, &params, "status", 0);
    assert!(success, "{pending}");
    assert_eq!(pending["base_point"], "known");
    assert_eq!(pending["targets"]["target-0"]["in_base_subgroup"], true);
    assert_eq!(pending["targets"]["target-0"]["scalar_known"], false);
    assert!(pending["targets"]["target-0"]["scalar_source"].is_null());
    assert!(pending["targets"]["target-0"]
        .get("candidate_residual")
        .is_none());
    assert_eq!(pending["attempts_saved"], partial["attempts_saved"]);
    assert_eq!(pending["relations_saved"], partial["relations_saved"]);
    let (success, complete) = run(&path, &params, "all", 10000);
    assert!(success, "{complete}");
    assert_eq!(complete["status"], "complete");
    assert!(complete["targets"]
        .as_object()
        .unwrap()
        .values()
        .all(|v| v["verified"] == true));
    let (success, status) = run(&path, &params, "status", 0);
    assert!(success, "{status}");
    assert!(status["targets"].as_object().unwrap().values().all(|v| {
        v["scalar_known"] == true && v["scalar_source"] == "checkpoint" && v.get("scalar").is_none()
    }));
    assert_eq!(status["attempts_saved"], complete["attempts_saved"]);
    assert_eq!(status["relations_saved"], complete["relations_saved"]);
    let (success, replay) = run(&path, &params, "all", 0);
    assert!(success, "{replay}");
    assert!(replay["reuse"]["new_attempts"].is_null());
    assert!(replay["reuse"]["pair_candidates_built"].is_null());
    assert_eq!(replay["relations_saved"], complete["relations_saved"]);
    fs::remove_dir_all(path).unwrap();
}

#[test]
fn fixed_cli_reports_supplied_scalar_and_missing_base_point() {
    let path = directory();
    let campaign = path.join("campaign");
    let input = path.join("params.json");
    let mut document: Value = serde_json::from_slice(&fs::read(params()).unwrap()).unwrap();
    document["targets"][0] = serde_json::json!({
        "id": "known",
        "x": document["generator"]["x"],
        "y": document["generator"]["y"],
        "known_log": "0x1",
    });
    document["targets"][1]["known_log"] = Value::Null;

    fs::write(&input, serde_json::to_vec(&document).unwrap()).unwrap();
    let (success, report) = run(&campaign, &input, "status", 0);
    assert!(success, "{report}");
    assert_eq!(report["targets"]["known"]["scalar_known"], true);
    assert_eq!(report["targets"]["known"]["scalar_source"], "provided");
    assert!(report["targets"]["known"].get("scalar").is_none());
    assert_eq!(report["targets"]["target-1"]["scalar_known"], false);
    assert_eq!(report["attempts_saved"], 0);

    document["targets"][0]["known_log"] = 2.into();
    fs::write(&input, serde_json::to_vec(&document).unwrap()).unwrap();
    let (success, report) = run(&campaign, &input, "status", 0);
    assert!(!success);
    assert!(report["message"].as_str().unwrap().contains("known_log"));

    document.as_object_mut().unwrap().remove("generator");
    fs::write(&input, serde_json::to_vec(&document).unwrap()).unwrap();
    let absent = path.join("absent");
    let (success, report) = run(&absent, &input, "status", 0);
    assert!(!success);
    assert_eq!(report["base_point"], "missing");
    assert!(!absent.exists());
    fs::remove_dir_all(path).unwrap();
}

#[test]
fn fixed_cli_reports_candidate_residuals_and_subgroup_membership() {
    use serde_json::json;

    let path = directory();
    let campaign = path.join("campaign");
    let input = path.join("params.json");
    let mut document: Value = serde_json::from_slice(&fs::read(params()).unwrap()).unwrap();
    let generator = &document["generator"];
    document["targets"] = json!([
        {"id": "matching", "x": generator["x"], "y": generator["y"], "candidate_log": "0x1"},
        {"id": "mismatching", "x": generator["x"], "y": generator["y"], "candidate_log": 2},
        {"id": "zero", "x": generator["x"], "y": generator["y"], "candidate_log": 0}
    ]);
    fs::write(&input, serde_json::to_vec(&document).unwrap()).unwrap();
    let (success, report) = run(&campaign, &input, "status", 0);
    assert!(success, "{report}");
    let targets = &report["targets"];
    assert_eq!(
        targets["matching"],
        json!({"in_base_subgroup": true, "scalar_known": true, "scalar_source": "candidate",
               "candidate_residual": {"is_identity": true}})
    );
    assert_eq!(targets["mismatching"]["in_base_subgroup"], true);
    assert_eq!(targets["mismatching"]["scalar_known"], false);
    // Q = P, so Q - [2]P = -P; on this binary curve -P = (x, x + y).
    assert_eq!(
        targets["mismatching"]["candidate_residual"],
        json!({"is_identity": false, "basis": "type-ii-onb", "x": "0xc", "y": "0xe3"})
    );
    assert_eq!(
        targets["zero"]["candidate_residual"],
        json!({"is_identity": false, "basis": "type-ii-onb", "x": "0xc", "y": "0xef"})
    );
    assert_eq!(report["attempts_saved"], 0);
    assert_eq!(report["relations_saved"], 0);

    document["targets"][0]["candidate_log"] = document["curve"]["subgroup_order"].clone();
    fs::write(&input, serde_json::to_vec(&document).unwrap()).unwrap();
    let (success, report) = run(&campaign, &input, "status", 0);
    assert!(!success);
    assert!(report["message"].as_str().unwrap().contains("scalar range"));

    // The point (0, 1) has order two and 0x1ff encodes one in the degree-nine ONB.
    document["targets"] = json!([{"id": "torsion", "x": 0, "y": "0x1ff"}]);
    fs::write(&input, serde_json::to_vec(&document).unwrap()).unwrap();
    let invalid_campaign = path.join("invalid-campaign");
    let (success, report) = run(&invalid_campaign, &input, "status", 0);
    assert!(!success);
    assert_eq!(report["base_point"], "known");
    assert_eq!(report["targets"]["torsion"]["in_base_subgroup"], false);
    assert!(!invalid_campaign.exists());
    fs::remove_dir_all(path).unwrap();
}

#[test]
fn fixed_cli_reports_missing_interpreter() {
    let path = directory();
    let output = Command::new(env!("CARGO_BIN_EXE_ca-ic"))
        .args([
            "fixed",
            "--params",
            "unused.json",
            "--python",
            "/nonexistent/ic-python",
            "--dir",
        ])
        .arg(&path)
        .arg("--json")
        .output()
        .unwrap();
    assert!(!output.status.success());
    let report: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(report["status"], "error");
    assert!(report["message"]
        .as_str()
        .unwrap()
        .contains("could not run fixed workflow"));
    fs::remove_dir_all(path).unwrap();
}

#[test]
fn fixed_cli_preflights_ecc2k130_entirely_in_rust() {
    let path = directory();
    let output = Command::new(env!("CARGO_BIN_EXE_ca-ic"))
        .args(["fixed", "--params"])
        .arg(PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("docs/ic/params/ecc2k130-fixed.json"))
        .arg("--dir")
        .arg(&path)
        .args([
            "--stage",
            "preflight",
            "--python",
            "/nonexistent/not-used-by-native-preflight",
            "--json",
        ])
        .output()
        .unwrap();
    let report: Value = serde_json::from_slice(&output.stdout)
        .unwrap_or_else(|_| panic!("{}", String::from_utf8_lossy(&output.stderr)));
    assert!(output.status.success(), "{report}");
    assert_eq!(report["engine"], "rust-native");
    assert_eq!(report["degree"], 131);
    assert_eq!(report["generator_on_curve"], true);
    assert_eq!(report["generator_in_subgroup"], true);
    assert_eq!(report["target_on_curve"], true);
    assert_eq!(report["target_in_subgroup"], true);
    assert_eq!(report["factor_base"]["orbit_columns"], 14);
    assert_eq!(report["factor_base"]["signed_points"], 3_668);
    assert_eq!(report["ready_for_persistent_collection"], true);
    assert_eq!(report["targets"]["ecc2k-130"]["scalar_known"], false);
    assert_eq!(
        fs::read_dir(&path).unwrap().count(),
        0,
        "native preflight must not create campaign state"
    );
    fs::remove_dir_all(path).unwrap();
}

#[test]
fn fixed_cli_embeds_native_preflight_in_ecc2k130_campaign_reports() {
    let path = directory();
    let params =
        PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("docs/ic/params/ecc2k130-fixed.json");
    let (success, report) = run(&path, &params, "status", 0);
    assert!(success, "{report}");
    assert_eq!(report["degree"], 131);
    assert_eq!(report["orbit_columns"], 14);
    assert_eq!(report["signed_base_points"], 3_668);
    assert_eq!(report["targets"]["ecc2k-130"]["scalar_known"], false);
    assert_eq!(report["rust_native_preflight"]["engine"], "rust-native");
    assert_eq!(
        report["rust_native_preflight"]["factor_base"]["orbit_columns"],
        report["orbit_columns"]
    );
    assert_eq!(
        report["rust_native_preflight"]["factor_base"]["signed_points"],
        report["signed_base_points"]
    );
    fs::remove_dir_all(path).unwrap();
}

#[test]
fn fixed_cli_routes_with_json_model_and_checks_missing_model() {
    let path = directory();
    let model = path.join("selector model.json");
    let mut domains = serde_json::Map::new();
    domains.insert(
        "b".repeat(64),
        serde_json::json!({
            "x_weight": [0, 9], "x_frobenius_distance": [0, 9],
            "rank_fraction": [0, 1], "direct_target": [0, 1]
        }),
    );
    fs::write(
        &model,
        serde_json::to_vec(&serde_json::json!({
            "format": "fixed-ic-selector-v1",
            "arms": {"pairs": 0.0, "sat-short": 0.1, "sat-medium": 0.5},
            "features": ["x_weight", "x_frobenius_distance", "rank_fraction", "direct_target"],
            "fallback": "pairs", "tree": {"arm": "sat-short"}, "domains": domains
        }))
        .unwrap(),
    )
    .unwrap();
    let mut command = Command::new(env!("CARGO_BIN_EXE_ca-ic"));
    command
        .args(["fixed", "--params"])
        .arg(PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("docs/ic/params/k0n9-fixed.json"))
        .arg("--dir")
        .arg(path.join("campaign"))
        .args(["--solver", "learned", "--attempts", "256", "--json"]);
    let missing = command.output().unwrap();
    assert!(!missing.status.success());
    let error: Value = serde_json::from_slice(&missing.stdout).unwrap();
    assert!(error["message"]
        .as_str()
        .unwrap()
        .contains("selector-model"));
    let output = command
        .arg("--selector-model")
        .arg(&model)
        .output()
        .unwrap();
    let report: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert!(output.status.success(), "{report}");
    assert_eq!(report["status"], "complete");
    assert!(report["selector_model_sha256"].is_string());
    assert!(
        report["reuse"]["selector_reason_unseen_parameters_or_budget"]
            .as_u64()
            .unwrap()
            > 0
    );
    fs::remove_dir_all(path).unwrap();
}
