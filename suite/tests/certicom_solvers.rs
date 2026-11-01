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
    let mut command = binary();
    command.args(args).arg("--json");
    let mut injected_backend = None;
    // A hardware qualification run uses the same assertions and exact inputs.
    // Default runs retain the portable CPU path.
    if !args.contains(&"--backend") {
        if let Ok(backend) = std::env::var("CERTICOM_TEST_BACKEND") {
            let worker = std::env::var("CERTICOM_TEST_WORKER")
                .expect("backend test requires its native worker");
            command.args([
                "--backend",
                &backend,
                "--gpu-worker",
                &worker,
                "--gpu-rho-walks",
                "4",
                "--gpu-batch-size",
                "16",
            ]);
            injected_backend = Some(backend);
        }
    }
    let output = command.output().unwrap();
    // Arguments and captured streams can contain scalar inputs or results.
    // Keep failure diagnostics to the exit status.
    assert_eq!(
        output.status.success(),
        success,
        "Certicom CLI returned an unexpected exit status: {}",
        output.status
    );
    let report: Value = serde_json::from_slice(&output.stdout).unwrap();
    if let Some(backend) = injected_backend {
        if report["status"] != "error" {
            let execution = &report["execution"];
            assert_eq!(execution["backend"], backend);
            if success {
                assert!(execution["kernel_launches"].as_u64().unwrap() > 0);
            }
        }
    }
    report
}

#[test]
fn cpu_auto_and_explicit_gpu_selection_report_the_actual_backend() {
    let cpu = run(
        &[
            "solve",
            "ECCp-130",
            "--method",
            "bsgs",
            "--secret",
            "42",
            "--interval-width",
            "256",
            "--backend",
            "cpu",
        ],
        true,
    );
    assert_eq!(cpu["execution"]["backend"], "cpu");
    assert_eq!(cpu["execution"]["kernel_launches"], 0);
    let automatic = run(
        &[
            "solve",
            "ECC2-130",
            "--method",
            "bsgs",
            "--secret",
            "42",
            "--interval-width",
            "256",
            "--backend",
            "auto",
        ],
        true,
    );
    assert!(["cpu", "cuda", "metal"].contains(&automatic["execution"]["backend"].as_str().unwrap()));
    let missing =
        std::env::temp_dir().join(format!("certicom-missing-worker-{}", std::process::id()));
    for backend in ["cuda", "metal"] {
        let error = run(
            &[
                "solve",
                "ECCp-130",
                "--method",
                "bsgs",
                "--secret",
                "42",
                "--interval-width",
                "256",
                "--backend",
                backend,
                "--gpu-worker",
                missing.to_str().unwrap(),
            ],
            false,
        );
        assert_eq!(error["status"], "error");
        assert!(error.get("scalar").is_none());
    }
}

#[test]
#[cfg(unix)]
fn host_preparation_expiry_cannot_return_a_verified_scalar() {
    use std::io::Write;
    use std::os::unix::fs::PermissionsExt;

    let directory =
        std::env::temp_dir().join(format!("certicom-cli-deadline-{}", std::process::id()));
    std::fs::create_dir_all(&directory).unwrap();
    let worker = directory.join("worker.sh");
    std::fs::write(
        &worker,
        "#!/bin/sh\nprintf 'CERTICOM_WORKER 1 gpu-emulator deadline-control\\n'\nexec sleep 10\n",
    )
    .unwrap();
    std::fs::set_permissions(&worker, std::fs::Permissions::from_mode(0o700)).unwrap();
    let preparation = directory.join("preparation.fifo");
    assert!(Command::new("mkfifo")
        .arg(&preparation)
        .status()
        .unwrap()
        .success());
    let path = preparation.clone();
    let (done, completed) = std::sync::mpsc::channel();
    let writer = std::thread::spawn(move || {
        // Opening the FIFO waits until the CLI has opened its worker and then
        // begins reading preparation. Expire the session during that host I/O.
        let mut file = std::fs::OpenOptions::new().write(true).open(path).unwrap();
        std::thread::sleep(std::time::Duration::from_millis(1100));
        file.write_all(
            br#"{"curve":"ECCp-130","factor_base":[],"relation_queries":[],"descent_shifts":[]}"#,
        )
        .unwrap();
        done.send(()).unwrap();
    });
    let report = run(
        &[
            "solve",
            "ECCp-130",
            "--method",
            "index-calculus",
            "--secret",
            "0",
            "--backend",
            "gpu-emulator",
            "--gpu-worker",
            worker.to_str().unwrap(),
            "--gpu-timeout-seconds",
            "1",
            "--preparation",
            preparation.to_str().unwrap(),
        ],
        false,
    );
    completed
        .recv_timeout(std::time::Duration::from_secs(5))
        .expect("CLI did not read the controlled preparation input");
    writer.join().unwrap();
    std::fs::remove_dir_all(directory).unwrap();
    assert_eq!(report["status"], "error");
    assert!(report.to_string().contains("deadline"));
    assert!(report.get("scalar").is_none());
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
        assert!(
            report["scalar"] == secret,
            "recovered scalar differs from the constructed fixture"
        );
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
        assert!(
            report["scalar"] == secret,
            "recovered scalar differs from the constructed fixture"
        );
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
        assert!(
            report["scalar"] == secret,
            "recovered scalar differs from the constructed fixture"
        );
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
