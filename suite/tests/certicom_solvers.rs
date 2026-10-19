//! Functional tests on the exact challenge curves. Constructed answers below
//! validate solver wiring and full-width arithmetic, not natural-target cost.

use std::process::Command;
use std::sync::atomic::{AtomicU64, Ordering};

use cryptanalysis_suite::cryptanalysis::certicom_dlp::ChallengeGroup;
use num_bigint::BigUint;
use num_traits::{One, Zero};
use serde_json::{json, Value};

fn binary() -> Command {
    Command::new(env!("CARGO_BIN_EXE_ca-icx"))
}

fn run(args: &[&str], success: bool) -> Value {
    let output = binary().args(args).arg("--json").output().unwrap();
    assert_eq!(
        output.status.success(),
        success,
        "{args:?}: {}\n{}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
    serde_json::from_slice(&output.stdout).unwrap()
}

#[test]
fn bsgs_keeps_large_scalar_bounds_for_both_challenges() {
    let lo = BigUint::one() << 100u32;
    let secret = (&lo + BigUint::from(42u32)).to_string();
    for curve in ["ECC2-130", "ECCp-130"] {
        let report = run(
            &[
                "solve",
                curve,
                "--method",
                "bsgs",
                "--secret",
                &secret,
                "--interval-lo",
                &lo.to_string(),
                "--interval-width",
                "256",
                "--max-table-entries",
                "8",
                "--max-iterations",
                "32",
            ],
            true,
        );
        assert_eq!(report["method"], "bsgs");
        assert_eq!(report["exact_curve"], true);
        assert_eq!(report["parameters"]["field_bits"], 131);
        assert_eq!(report["scalar"], secret);
        assert_eq!(report["planted_recovered"], true);
    }
}

#[test]
fn rho_recovers_the_special_full_width_minus_one_fixture() {
    for curve in ["ECC2-130", "ECCp-130"] {
        let group = ChallengeGroup::by_name(curve).unwrap();
        let secret = (group.order() - BigUint::one()).to_string();
        let report = run(
            &[
                "solve",
                curve,
                "--method",
                "rho",
                "--secret",
                &secret,
                "--max-iterations",
                "2048",
            ],
            true,
        );
        assert_eq!(report["method"], "rho");
        assert_eq!(report["scalar"], secret);
        assert_eq!(report["planted_recovered"], true);
        assert!(report["iterations"].as_u64().unwrap() > 0);
        assert_eq!(report["table_entries"], 0);
    }
}

#[test]
fn index_calculus_executes_relation_collection_la_and_descent_on_both_exact_curves() {
    static SERIAL: AtomicU64 = AtomicU64::new(0);
    for curve in ["ECC2-130", "ECCp-130"] {
        let group = ChallengeGroup::by_name(curve).unwrap();
        let k0 = (BigUint::one() << 100u32) + BigUint::from(17u32);
        let k1 = (BigUint::one() << 107u32) + BigUint::from(53u32);
        let k2 = (BigUint::one() << 113u32) + BigUint::from(91u32);
        let secret = (&k0 * BigUint::from(2u32)).to_string();
        let base: Vec<Value> = [&k0, &k1, &k2]
            .iter()
            .map(|k| group.point_json(&group.target_from_scalar(k)))
            .collect();
        let document = json!({
            "curve": curve,
            "label": "constructed-known-answer; not a natural relation-yield measurement",
            "factor_base": base,
            "relation_queries": [(&k0 + &k1).to_string(), (&k1 + &k2).to_string(), (&k2 + &k0).to_string()],
            "descent_shifts": [BigUint::zero().to_string()],
        });
        let path = std::env::temp_dir().join(format!(
            "certicom-ic-{}-{}.json",
            std::process::id(),
            SERIAL.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::write(&path, document.to_string()).unwrap();
        let report = run(
            &[
                "solve",
                curve,
                "--method",
                "index-calculus",
                "--secret",
                &secret,
                "--preparation",
                path.to_str().unwrap(),
                "--max-iterations",
                "4",
            ],
            true,
        );
        std::fs::remove_file(path).unwrap();
        assert_eq!(report["method"], "index-calculus");
        assert_eq!(report["exact_curve"], true);
        assert_eq!(report["parameters"]["field_bits"], 131);
        assert_eq!(report["scalar"], secret);
        assert_eq!(report["index_calculus"]["rank"], 3);
        assert_eq!(report["index_calculus"]["verified_relations"], 3);
        assert_eq!(report["index_calculus"]["factor_base_logs_verified"], true);
        assert_eq!(report["index_calculus"]["descent_queries"], 1);
    }
}

#[test]
fn every_method_runs_on_the_published_point_and_reports_a_real_budget_stop() {
    for curve in ["ECC2-130", "ECCp-130"] {
        let group = ChallengeGroup::by_name(curve).unwrap();
        for method in ["rho", "bsgs", "index-calculus"] {
            let report = run(
                &[
                    "solve",
                    curve,
                    "--method",
                    method,
                    "--challenge",
                    "--max-iterations",
                    "4",
                    "--max-restarts",
                    "0",
                    "--max-table-entries",
                    "128",
                    "--factor-base-size",
                    "3",
                    "--max-base-candidates",
                    "64",
                ],
                false,
            );
            assert_eq!(report["method"], method);
            assert_eq!(report["status"], "budget_exhausted");
            assert_eq!(report["exact_curve"], true);
            assert_eq!(report["verified"], false);
            assert!(report["scalar"].is_null());
            assert_eq!(
                report["target"],
                group.point_json(&group.published_target())
            );
            assert_eq!(report["parameters"]["field_bits"], 131);
            assert_eq!(
                report["parameters"]["subgroup_order"],
                group.order().to_string()
            );
        }
    }
}

#[test]
fn invalid_targets_and_method_flags_fail_without_a_solved_result() {
    let report = run(
        &["solve", "ECCp-130", "--method", "rho", "--point", "1,1"],
        false,
    );
    assert_eq!(report["status"], "error");
    let report = run(
        &[
            "solve",
            "ECC2-130",
            "--method",
            "index-calculus",
            "--challenge",
            "--interval-width",
            "256",
        ],
        false,
    );
    assert_eq!(report["status"], "error");
    let output = binary()
        .args([
            "solve",
            "ECCp-130",
            "--method",
            "rho",
            "--challenge",
            "--secret",
            "42",
            "--json",
        ])
        .output()
        .unwrap();
    assert!(!output.status.success());
}
