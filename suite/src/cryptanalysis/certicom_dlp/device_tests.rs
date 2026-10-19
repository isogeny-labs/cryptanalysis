//! Default: execute the exact device source on the CPU and label it emulation.
//! To exercise actual hardware set CERTICOM_TEST_BACKEND=cuda|metal and
//! CERTICOM_TEST_WORKER to the built native worker's absolute path.
use super::tests::index_fixture;
use super::worker::{decode_point, integer, Backend, DeviceOptions, DeviceWorker};
use super::*;
use num_bigint::RandBigInt;
use rand::{rngs::StdRng, SeedableRng};
use std::path::PathBuf;
use std::process::Command;
use std::sync::OnceLock;
use std::time::{Duration, Instant};

fn test_dir() -> &'static PathBuf {
    static DIR: OnceLock<PathBuf> = OnceLock::new();
    DIR.get_or_init(|| {
        let path =
            std::env::temp_dir().join(format!("certicom-device-tests-{}", std::process::id()));
        std::fs::create_dir_all(&path).unwrap();
        path
    })
}
fn emulator() -> PathBuf {
    static BINARY: OnceLock<PathBuf> = OnceLock::new();
    BINARY
        .get_or_init(|| {
            let manifest = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
            let source = manifest
                .ancestors()
                .map(|p| p.join("gpu/certicom/emulator.cpp"))
                .find(|p| p.is_file())
                .expect("tracked gpu/certicom source must be materialized");
            let binary = test_dir().join("certicom_emulator");
            let output = Command::new(std::env::var("CXX").unwrap_or_else(|_| "c++".into()))
                .args(["-O2", "-std=c++17", "-Wall", "-Wextra", "-Werror"])
                .arg(source)
                .arg("-o")
                .arg(&binary)
                .output()
                .unwrap();
            assert!(
                output.status.success(),
                "{}",
                String::from_utf8_lossy(&output.stderr)
            );
            binary
        })
        .clone()
}
fn device_options() -> (DeviceOptions, PathBuf) {
    let (backend, path) = match std::env::var("CERTICOM_TEST_BACKEND").ok().as_deref() {
        None | Some("gpu-emulator") => (Backend::GpuEmulator, emulator()),
        Some("cuda") => (
            Backend::Cuda,
            PathBuf::from(
                std::env::var("CERTICOM_TEST_WORKER")
                    .expect("CUDA hardware test requires its worker"),
            ),
        ),
        Some("metal") => (
            Backend::Metal,
            PathBuf::from(
                std::env::var("CERTICOM_TEST_WORKER")
                    .expect("Metal hardware test requires its worker"),
            ),
        ),
        Some(other) => panic!("unknown CERTICOM_TEST_BACKEND {other:?}"),
    };
    (
        DeviceOptions {
            backend,
            batch_size: 7,
            rho_walks: 4,
            timeout_seconds: 120,
            ..DeviceOptions::default()
        },
        path,
    )
}
fn device(group: &ChallengeGroup, target: &ChallengePoint) -> DeviceWorker {
    let (opts, path) = device_options();
    DeviceWorker::open(group, target, &opts, &path, opts.backend).unwrap()
}

#[test]
fn device_source_matches_independent_rust_full_width_arithmetic() {
    for name in ["ECC2-130", "ECCp-130"] {
        let group = ChallengeGroup::by_name(name).unwrap();
        let mut worker = device(&group, &group.published_target());
        let mut rng = StdRng::seed_from_u64(0x131);
        let mut scalars = vec![
            BigUint::zero(),
            BigUint::one(),
            BigUint::from(2u32),
            group.order() - BigUint::one(),
            (BigUint::one() << 130u32) + BigUint::from(123u32),
        ];
        scalars.extend((0..12).map(|_| rng.gen_biguint_below(group.order())));
        let bases = [
            group.generator(),
            group.published_target(),
            group.identity(),
        ];
        let requests: Vec<_> = scalars
            .iter()
            .enumerate()
            .map(|(i, k)| (bases[i % 3].clone(), k.clone()))
            .collect();
        let results = worker.mul(&group, &requests).unwrap();
        for ((p, k), result) in requests.iter().zip(results) {
            assert_eq!(result, group.mul(p, k), "{name}, scalar {k}");
        }
        let g = group.generator();
        let mut pairs = vec![
            (g.clone(), g.clone()),
            (g.clone(), group.neg(&g)),
            (group.identity(), g.clone()),
            (g.clone(), group.identity()),
        ];
        for k in &scalars {
            pairs.push((group.target_from_scalar(k), group.published_target()));
        }
        for ((p, q), result) in pairs.iter().zip(worker.add(&group, &pairs).unwrap()) {
            assert_eq!(result, group.add(p, q), "{name}: add");
        }
        assert!(worker.execution().kernel_launches > 2);
        assert_eq!(
            worker.execution().backend,
            device_options().0.backend.name()
        );
    }
}

#[test]
fn device_rho_bsgs_and_complete_ic_recover_exact_curve_fixtures() {
    for name in ["ECC2-130", "ECCp-130"] {
        let group = ChallengeGroup::by_name(name).unwrap();
        let opts = SolverOptions {
            max_iterations: 2048,
            max_restarts: 16,
            max_table_entries: 8,
            factor_base_size: 3,
            max_base_candidates: 64,
            ..SolverOptions::default()
        };
        let lo = BigUint::one() << 100u32;
        let secret = &lo + BigUint::from(42u32);
        let target = group.target_from_scalar(&secret);
        let report = bsgs_on_device(
            &group,
            &target,
            &lo,
            &BigUint::from(256u32),
            &opts,
            &mut device(&group, &target),
        )
        .unwrap();
        assert_eq!(report.scalar_value, Some(secret));
        assert!(report.execution.kernel_launches > 0);
        let secret = group.order() - BigUint::one();
        let target = group.target_from_scalar(&secret);
        let report = rho_on_device(&group, &target, &opts, &mut device(&group, &target)).unwrap();
        assert_eq!(report.scalar_value, Some(secret));
        assert!(report.execution.device_rho_iterations > 0);
        let (input, secret) = index_fixture(&group);
        let target = group.target_from_scalar(&secret);
        let report = index_calculus_on_device(
            &group,
            &target,
            &opts,
            Some(&input),
            &mut device(&group, &target),
        )
        .unwrap();
        assert_eq!(report.scalar_value, Some(secret));
        assert!(report.execution.device_point_additions > 0);
        let stages = report.index_calculus.unwrap();
        assert_eq!(stages.rank, 3);
        assert!(stages.factor_base_logs_verified);
        assert_eq!(stages.descent_queries, 1);
        assert_eq!(stages.linear_algebra_backend, "cpu-biguint");
    }
}

#[test]
fn device_published_targets_stop_with_real_work_and_no_scalar() {
    for name in ["ECC2-130", "ECCp-130"] {
        let group = ChallengeGroup::by_name(name).unwrap();
        let target = group.published_target();
        let opts = SolverOptions {
            max_iterations: 4,
            max_restarts: 0,
            max_table_entries: 8,
            factor_base_size: 3,
            max_base_candidates: 64,
            ..SolverOptions::default()
        };
        let reports = [
            bsgs_on_device(
                &group,
                &target,
                &BigUint::zero(),
                group.order(),
                &opts,
                &mut device(&group, &target),
            )
            .unwrap(),
            rho_on_device(&group, &target, &opts, &mut device(&group, &target)).unwrap(),
            index_calculus_on_device(&group, &target, &opts, None, &mut device(&group, &target))
                .unwrap(),
        ];
        for report in reports {
            assert_eq!(report.status, "budget_exhausted");
            assert!(report.scalar.is_none());
            assert!(!report.verified);
            assert!(report.execution.kernel_launches > 0);
        }
    }
}

#[test]
fn worker_backend_binding_encoding_and_candidate_checks_fail_closed() {
    let group = ChallengeGroup::by_name("ECCp-130").unwrap();
    let target = group.published_target();
    let opts = DeviceOptions {
        backend: Backend::Cuda,
        ..DeviceOptions::default()
    };
    assert!(DeviceWorker::open(&group, &target, &opts, &emulator(), Backend::Cuda).is_err());
    let mut worker = device(&group, &target);
    let other = ChallengeGroup::by_name("ECC2-130").unwrap();
    assert!(bsgs_on_device(
        &other,
        &other.published_target(),
        &BigUint::zero(),
        &BigUint::from(64u32),
        &SolverOptions::default(),
        &mut worker
    )
    .is_err());
    assert!(decode_point(&group, &[0; 11]).is_err());
    let mut infinity = [0; 11];
    infinity[10] = 1;
    infinity[0] = 1;
    assert!(decode_point(&group, &infinity).is_err());
    assert!(integer(&(BigUint::one() << 131u32)).is_err());
    assert!(SolveReport::pending(&group, "rho")
        .recover(&group, &target, BigUint::zero())
        .is_err());
}

#[test]
fn expired_sessions_reject_no_io_results_for_every_solver() {
    for name in ["ECC2-130", "ECCp-130"] {
        let group = ChallengeGroup::by_name(name).unwrap();
        let target = group.identity();
        let device_opts = DeviceOptions {
            backend: Backend::GpuEmulator,
            timeout_seconds: 1,
            ..DeviceOptions::default()
        };
        let mut worker = DeviceWorker::open(
            &group,
            &target,
            &device_opts,
            &emulator(),
            Backend::GpuEmulator,
        )
        .unwrap();
        std::thread::sleep(Duration::from_millis(1100));
        let opts = SolverOptions {
            max_iterations: 0,
            ..SolverOptions::default()
        };
        for result in [
            rho_on_device(&group, &target, &opts, &mut worker),
            bsgs_on_device(
                &group,
                &target,
                &BigUint::zero(),
                &BigUint::one(),
                &opts,
                &mut worker,
            ),
            index_calculus_on_device(&group, &target, &opts, None, &mut worker),
        ] {
            assert!(
                matches!(result, Err(ref error) if error.contains("deadline")),
                "{name}: expired session accepted a report: {result:?}"
            );
        }
        assert!(worker.mul(&group, &[]).is_err());
        assert!(worker.add(&group, &[]).is_err());
        assert!(worker.rho(&[], 1).is_err());
    }
}

#[test]
#[cfg(unix)]
fn worker_exit_and_deadline_cannot_hang_or_return_a_solution() {
    use std::os::unix::fs::PermissionsExt;
    let group = ChallengeGroup::by_name("ECCp-130").unwrap();
    let target = group.published_target();
    let opts = DeviceOptions {
        backend: Backend::GpuEmulator,
        timeout_seconds: 1,
        ..DeviceOptions::default()
    };
    let exit = test_dir().join("exit-worker.sh");
    std::fs::write(
        &exit,
        "#!/bin/sh\nprintf 'CERTICOM_WORKER 1 gpu-emulator test\\n'\nexit 0\n",
    )
    .unwrap();
    std::fs::set_permissions(&exit, std::fs::Permissions::from_mode(0o700)).unwrap();
    let mut worker =
        DeviceWorker::open(&group, &target, &opts, &exit, Backend::GpuEmulator).unwrap();
    assert!(worker
        .mul(&group, &[(group.generator(), BigUint::one())])
        .is_err());
    let stall = test_dir().join("stall-worker.sh");
    std::fs::write(&stall, "#!/bin/sh\nexec sleep 10\n").unwrap();
    std::fs::set_permissions(&stall, std::fs::Permissions::from_mode(0o700)).unwrap();
    let start = Instant::now();
    assert!(DeviceWorker::open(&group, &target, &opts, &stall, Backend::GpuEmulator).is_err());
    assert!(start.elapsed() < Duration::from_secs(5));
}
