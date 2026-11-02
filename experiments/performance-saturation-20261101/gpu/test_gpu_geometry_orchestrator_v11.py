#!/usr/bin/env python3
"""Adversarial tests for the v11 preflight/controller/finalizer sequence."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "orchestrate_gpu_geometry_v11", HERE / "orchestrate_gpu_geometry_v11.py"
)
assert SPEC is not None and SPEC.loader is not None
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


def phase_environments() -> dict[str, dict[str, str]]:
    return {
        phase: {"PATH": f"/{phase}"}
        for phase in ("preflight", "controller", "finalizer")
    }


def ignore_terminal(_preflight: int, _controller: int | None,
                    _finalizer: int, _detail: str) -> None:
    pass


def good_environment_policy() -> dict:
    return {
        "bootstrap_fixed": {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C", "TZ": "UTC",
                            "RUSTUP_HOME": "<fresh-task-root>/rustup-home",
                            "CARGO_HOME": "<fresh-task-root>/cargo-home", "TMPDIR": "<fresh-task-root>/tmp"},
        "fetch_fixed": {"PATH": "<fresh-task-root>/cargo-home/bin:/usr/bin:/bin",
                        "RUSTUP_HOME": "<fresh-task-root>/rustup-home",
                        "CARGO_HOME": "<fresh-task-root>/cargo-home", "TMPDIR": "<fresh-task-root>/tmp",
                        "LANG": "C", "LC_ALL": "C", "TZ": "UTC",
                        "RUSTC": f"<fresh-task-root>/rustup-home/toolchains/{MOD.RUST_TOOLCHAIN}/bin/rustc"},
        "network_forwarded_value_sha256": {"HTTPS_PROXY": "f" * 64},
        "launcher": {
            "fixed": {"PATH": "/usr/bin:/bin", "HOME": "<caller-owned-fresh-home>",
                      "TMPDIR": "<caller-owned-fresh-tmp>", "LANG": "C", "LC_ALL": "C", "TZ": "UTC"},
            "exact_keys": sorted(["PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "TZ", "HTTPS_PROXY"]),
            "network_forward_allowlist": list(MOD.NETWORK_ALLOWLIST),
            "network_forwarded_value_sha256": {"HTTPS_PROXY": "f" * 64},
            "python": {"executable": MOD.PYTHON, "flags": ["-I", "-S", "-B"],
                       "isolated": True, "no_site": True, "dont_write_bytecode": True,
                       "safe_path": True},
        },
        "network_forward_allowlist": list(MOD.NETWORK_ALLOWLIST), "build_inherited_keys": [],
        "build_fixed": {"PATH": "<fresh-task-root>/cargo-home/bin:/usr/bin:/bin",
                        "RUSTUP_HOME": "<fresh-task-root>/rustup-home",
                        "CARGO_HOME": "<fresh-task-root>/cargo-home", "TMPDIR": "<fresh-task-root>/tmp/<arm>",
                        "LANG": "C", "LC_ALL": "C", "TZ": "UTC",
                        "RUSTC": f"<fresh-task-root>/rustup-home/toolchains/{MOD.RUST_TOOLCHAIN}/bin/rustc",
                        "CC": "/usr/bin/x86_64-linux-gnu-gcc-14", "AR": "/usr/bin/x86_64-linux-gnu-ar",
                        "RANLIB": "/usr/bin/x86_64-linux-gnu-ranlib",
                        "CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_LINKER": "/usr/bin/x86_64-linux-gnu-gcc-14",
                        "CARGO_INCREMENTAL": "0", "CARGO_NET_OFFLINE": "true",
                        "CARGO_TERM_COLOR": "never", "SOURCE_DATE_EPOCH": "0",
                        "CARGO_TARGET_DIR": "<fresh-task-root>/target/<arm>"},
        "forbidden_inherited_patterns": list(MOD.FORBIDDEN_BUILD_PATTERNS),
        "cargo_config_policy": "fresh CARGO_HOME and no config/config.toml in source ancestors",
        "location_policy": "local_controller",
    }


def good_preflight(run_id: str = "gpu-geometry-http-rtx5090-v11-test",
                   protocol_sha: str = "a" * 64) -> dict:
    baseline, candidate = "b" * 64, "c" * 64

    def build(arm: str, binary: str) -> dict:
        return {
            "arm": arm, "command": list(MOD.BUILD_COMMAND), "returncode": 0,
            "elapsed_seconds": 1.0, "log_sha256": "d" * 64, "log_bytes": 123,
            "binary_sha256": binary, "binary_bytes": 456,
        }

    return {
        "schema": MOD.PREFLIGHT_SCHEMA, "protocol_id": MOD.PROTOCOL_ID,
        "protocol_sha256": protocol_sha, "run_id": run_id, "provider_actions": False,
        "location": "local_controller",
        "tool_sha256": MOD.sha256_file(HERE / "preflight_gpu_geometry_v11.py"),
        "source": dict(MOD.PREFLIGHT_SOURCE), "build_contract": dict(MOD.BUILD_CONTRACT),
        "started_at": "2026-11-02T00:00:00Z", "status": "passed", "error": None,
        "finished_at": "2026-11-02T00:30:00Z", "elapsed_seconds": 1800.0,
        "archive": {
            "roots": list(MOD.ARCHIVE_ROOTS), "sha256": MOD.ARCHIVE_SHA256,
            "bytes": MOD.ARCHIVE_BYTES, "files": MOD.ARCHIVE_FILES,
            "required_members": [
                MOD.F4_PATH, "cuda/ca_device.cuh", "challenges/elliptic/corpus.json",
                "suite/Cargo.lock", "bindings/rust/cryptanalysis-sys/build.rs",
            ],
        },
        "source_delta": [MOD.F4_PATH], "files_per_arm": MOD.ARCHIVE_FILES,
        "builds": [build("baseline", baseline), build("candidate", candidate)],
        "binary_contract": {
            "baseline_sha256": baseline, "baseline_aa_sha256": baseline,
            "candidate_sha256": candidate, "baseline_aa_equals_baseline": True,
            "candidate_differs": True,
        },
        "dependency_fetch": {"command": ["cargo", "fetch", "--locked", "--manifest-path", "suite/Cargo.toml"],
                             "returncode": 0, "log_sha256": "a" * 64, "log_bytes": 1,
                             "cargo_config_candidates_checked": 12, "cargo_config_all_absent": True},
        "environment_policy": good_environment_policy(),
        "toolchain": {
            "system_policy": "controller_exact_hashes",
            "system_tools_unchanged_after_builds": True,
            "bootstrap": {
                "url": MOD.RUSTUP_URL, "sha256": MOD.RUSTUP_SHA256,
                "log_sha256": "e" * 64, "log_bytes": 789,
            },
            "rustc": {
                "toolchain": MOD.RUST_TOOLCHAIN, "sha256": MOD.RUSTC_SHA256,
                "version": "rustc 1.91.1 (ed61e7d7e 2025-11-07)\nbinary: rustc",
            },
            "cargo": {
                "toolchain": MOD.RUST_TOOLCHAIN, "sha256": MOD.CARGO_SHA256,
                "version": "cargo 1.91.1 (ea2d97820 2025-10-10)",
            },
            "cc": {
                "realpath": "/usr/bin/x86_64-linux-gnu-gcc-14", "sha256": MOD.CC_SHA256,
                "version": "x86_64-linux-gnu-gcc-14 (Debian 14.2.0-19) 14.2.0",
                "target": "x86_64-linux-gnu",
                "capabilities": {"compile": True, "archive": True, "ranlib": True,
                                 "link": True, "execute": True},
            },
            "ar": {"realpath": "/usr/bin/x86_64-linux-gnu-ar", "sha256": MOD.AR_SHA256,
                   "version": "GNU ar (GNU Binutils for Debian) 2.44"},
            "ranlib": {"realpath": "/usr/bin/x86_64-linux-gnu-ranlib", "sha256": MOD.RANLIB_SHA256,
                       "version": "GNU ranlib (GNU Binutils for Debian) 2.44"},
            "linker": {"realpath": "/usr/bin/x86_64-linux-gnu-ld.bfd", "sha256": MOD.LINKER_SHA256,
                       "version": "GNU ld (GNU Binutils for Debian) 2.44"},
            "collect2": {"realpath": "/usr/libexec/gcc/x86_64-linux-gnu/14/collect2",
                         "sha256": MOD.COLLECT2_SHA256},
        },
    }


class GeometryOrchestratorTests(unittest.TestCase):
    def test_actual_dry_run_constructs_one_bound_controller_without_invoking_it(self) -> None:
        run_id, protocol_sha, preflight_sha = (
            "gpu-geometry-http-rtx5090-v11-dryrun", "a" * 64, "b" * 64,
        )
        value = {"extensions": {"tooling_source": {
            "public_ref": MOD.SOURCE_REF, "commit": "c" * 40,
        }}}
        command = MOD.controller_command(protocol_sha, run_id, value, preflight_sha)
        self.assertEqual(command[:6], [
            "/usr/bin/python3", "-I", "-S", "-B",
            "cloud/runpod_http_batch.py", "misagi-f4-geometry-v11",
        ])
        self.assertEqual(command.count("--source-commit"), 1)
        self.assertEqual(command.count("--minimal-bootstrap"), 1)
        image_at = command.index("--image")
        self.assertEqual(
            command[image_at + 1],
            "runpod/base:1.0.2-ubuntu2404@sha256:e93bf61149910d35407fc865078ceb9b2887e986befd2b7c0eee322abe47ac59",
        )
        self.assertEqual(command.count("--"), 1)
        remote = command[-1]
        self.assertIn(protocol_sha, remote)
        self.assertIn(preflight_sha, remote)
        self.assertIn("run_gpu_geometry_ab_v11.sh", remote)
        self.assertIn("/usr/bin/bash --noprofile --norc", remote)
        self.assertNotIn("extract_nsys_tools_v11.sh", remote)

    def test_remote_runner_builds_full_closure_before_nsys_install(self) -> None:
        text = (HERE / "run_gpu_geometry_ab_v11.sh").read_text(encoding="utf-8")
        preflight = (HERE / "preflight_gpu_geometry_v11.py").read_text(encoding="utf-8")
        self.assertIn('(\"suite\", \"bindings/rust\", \"include\", \"src\", \"cuda\", \"challenges\")', preflight)
        build_at = text.index("prepare-remote --repo")
        install_at = text.index('bash "$REPO/ecc2k130/runner/codegen/extract_nsys_tools_v11.sh"')
        measure_at = text.index("run_matrix()")
        self.assertLess(build_at, install_at)
        self.assertLess(install_at, measure_at)

    def test_registered_history_deepen_reaches_both_source_commits(self) -> None:
        runner = (HERE / "run_gpu_geometry_ab_v11.sh").read_text(encoding="utf-8")
        self.assertIn("HISTORY_DEEPEN_COMMITS=64", runner)
        repo = HERE.parents[2]
        for target in (
            MOD.PREFLIGHT_SOURCE["baseline_commit"],
            MOD.PREFLIGHT_SOURCE["candidate_commit"],
        ):
            distance = int(subprocess.run(
                ["git", "rev-list", "--count", f"{target}..HEAD"],
                cwd=repo, capture_output=True, text=True, check=True,
            ).stdout)
            self.assertLess(distance, 64, (target, distance))

    def test_strict_runtime_env_excludes_injected_flags_and_includes_nvrtc(self) -> None:
        text = (HERE / "run_gpu_geometry_ab_v11.sh").read_text(encoding="utf-8")
        measure = text[text.index("MEASURE_ENV=("):text.index("LD_LIBRARY_PATH_SAFE=")]
        self.assertIn("/usr/bin/env -i", measure)
        self.assertIn('"CA_NVRTC_LIB=$CA_NVRTC_LIB"', measure)
        for forbidden in ("RUSTFLAGS", "CFLAGS", "LD_PRELOAD", "RAYON_NUM_THREADS"):
            self.assertNotIn(forbidden, measure)

    def test_source_identity_assignments_survive_env_i(self) -> None:
        runner = (HERE / "run_gpu_geometry_ab_v11.sh").read_text(encoding="utf-8")
        block = runner[runner.index('"${SYSTEM_ENV[@]}" \\\nBASELINE_ORIGIN_COMMIT_SAFE='):
                       runner.index("/usr/bin/python3 -I -S -B - <<'PY'",
                                    runner.index('"${SYSTEM_ENV[@]}" \\\nBASELINE_ORIGIN_COMMIT_SAFE='))]
        for name in (
            "BASELINE_ORIGIN_COMMIT_SAFE", "CANDIDATE_COMMIT_SAFE", "CANDIDATE_TREE_SAFE",
            "BASELINE_F4_SHA256_SAFE", "CANDIDATE_F4_SHA256_SAFE", "PRODUCTION_DIFF_SHA256_SAFE",
            "CANDIDATE_ARCHIVE_SHA256_SAFE", "F4_PATH_SAFE", "TOOLING_REF_SAFE",
            "HISTORY_DEEPEN_COMMITS_SAFE", "PREFLIGHT_RECEIPT_SHA256_SAFE",
            "REMOTE_BUILD_PREFLIGHT_SHA256_SAFE", "SESSION_PATH_SAFE",
        ):
            self.assertIn(name + "=", block)
        script = r'''
set -euo pipefail
SYSTEM_ENV=(/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C TZ=UTC)
"${SYSTEM_ENV[@]}" A_SAFE=one B_SAFE=two python3 - <<'PY'
import json, os
print(json.dumps({"a": os.environ["A_SAFE"], "b": os.environ["B_SAFE"],
                  "keys": sorted(k for k in os.environ if k.endswith("_SAFE"))}, sort_keys=True))
PY
'''
        result = subprocess.run(["bash", "-c", script], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout), {"a": "one", "b": "two", "keys": ["A_SAFE", "B_SAFE"]})

    def test_frozen_all_argv_templates_and_preflight_hash(self) -> None:
        run_id, protocol_sha, preflight_sha = (
            "gpu-geometry-http-rtx5090-v11-test", "a" * 64, "f" * 64,
        )
        preflight = ["preflight", run_id, protocol_sha]
        controller = ["controller", run_id, preflight_sha]
        finalizer = ["finalizer", run_id, protocol_sha]
        value = {"extensions": {
            "launch": {
                "preflight_argv_template": ["preflight", "<run_id>", "<frozen_protocol_sha256>"],
                "controller_argv_template": ["controller", "<run_id>", "<preflight_receipt_sha256>"],
            },
            "finalization": {
                "finalizer_argv_template": ["finalizer", "<run_id>", "<frozen_protocol_sha256>"],
            },
        }}
        MOD.verify_argv_templates(
            value, preflight, controller, finalizer, run_id, protocol_sha, preflight_sha,
        )
        for index in range(3):
            tampered = [list(preflight), list(controller), list(finalizer)]
            tampered[index][-1] = "tampered"
            with self.assertRaises(ValueError):
                MOD.verify_argv_templates(
                    value, *tampered, run_id, protocol_sha, preflight_sha,
                )

    def test_local_phase_environments_drop_hostile_ambient_state(self) -> None:
        inherited = {
            "HTTPS_PROXY": "http://allowed-proxy",
            "SSL_CERT_FILE": "/allowed/ca.pem",
            "RUNPOD_API_KEY": "controller-secret",
            "PYTHONPATH": "/hostile/python", "PYTHONHOME": "/hostile/home",
            "GIT_DIR": "/hostile/git", "RUSTFLAGS": "-Ctarget-cpu=native",
            "https_proxy": "http://lowercase-not-allowed",
            "LD_PRELOAD": "/hostile/preload.so",
        }
        with tempfile.TemporaryDirectory() as directory:
            environments = MOD.exact_phase_environments(
                Path(directory) / "exact", inherited,
            )
            fixed_keys = {"PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "TZ"}
            self.assertEqual(set(environments["orchestrator"]), fixed_keys)
            self.assertEqual(set(environments["canonical"]), fixed_keys)
            self.assertEqual(set(environments["finalizer"]), fixed_keys)
            self.assertEqual(
                set(environments["preflight"]),
                fixed_keys | {"HTTPS_PROXY", "SSL_CERT_FILE"},
            )
            self.assertEqual(
                set(environments["controller"]),
                fixed_keys | {"HTTPS_PROXY", "SSL_CERT_FILE", "RUNPOD_API_KEY"},
            )
            for environment in environments.values():
                self.assertEqual(environment["PATH"], "/usr/bin:/bin")
                self.assertEqual(environment["LANG"], "C")
                self.assertEqual(environment["LC_ALL"], "C")
                self.assertEqual(environment["TZ"], "UTC")
                self.assertTrue(Path(environment["HOME"]).is_dir())
                self.assertTrue(Path(environment["TMPDIR"]).is_dir())
                for hostile in (
                    "PYTHONPATH", "PYTHONHOME", "GIT_DIR", "RUSTFLAGS",
                    "https_proxy", "LD_PRELOAD",
                ):
                    self.assertNotIn(hostile, environment)

    def test_registered_commands_use_isolated_absolute_python(self) -> None:
        run_id, digest = "gpu-geometry-http-rtx5090-v11-test", "a" * 64
        value = {"extensions": {"tooling_source": {
            "public_ref": MOD.SOURCE_REF, "commit": "c" * 40,
        }}}
        commands = (
            MOD.preflight_command(Path("/repo"), digest, run_id),
            MOD.controller_command(digest, run_id, value, "b" * 64),
            MOD.finalizer_command(Path("protocol.json"), digest, Path("tool.py"), run_id),
        )
        for command in commands:
            self.assertEqual(command[:4], ["/usr/bin/python3", "-I", "-S", "-B"])

    def test_valid_preflight_receipt_and_each_build_closure_mutation(self) -> None:
        run_id, protocol_sha = "gpu-geometry-http-rtx5090-v11-test", "a" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            value = good_preflight(run_id, protocol_sha)
            path.write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(MOD.validate_preflight_receipt(path, run_id, protocol_sha), value)
            mutations = (
                lambda item: item["archive"]["required_members"].remove("cuda/ca_device.cuh"),
                lambda item: item["archive"]["required_members"].remove("challenges/elliptic/corpus.json"),
                lambda item: item["source_delta"].append("suite/Cargo.toml"),
                lambda item: item["binary_contract"].update(candidate_differs=False),
                lambda item: item["toolchain"]["cargo"].update(sha256="0" * 64),
            )
            for mutate in mutations:
                changed = good_preflight(run_id, protocol_sha)
                mutate(changed)
                path.write_text(json.dumps(changed), encoding="utf-8")
                with self.assertRaises(ValueError):
                    MOD.validate_preflight_receipt(path, run_id, protocol_sha)

    def test_local_tool_tamper_is_refused_by_dry_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            study = repo / MOD.STUDY
            study.mkdir(parents=True)
            names = [
                "analyze_gpu_geometry_ab_v11.py", "finalize_gpu_geometry_ab_v11.py",
                "orchestrate_gpu_geometry_v11.py", "preflight_gpu_geometry_v11.py",
            ]
            paths = [study / name for name in names]
            tool = repo / "protocol_tool.py"
            for path in [*paths, tool]:
                path.write_text(path.name, encoding="utf-8")
            relative_paths = [path.relative_to(repo).as_posix() for path in paths]
            files = {relative: MOD.sha256_file(repo / relative) for relative in relative_paths}
            value = {
                "analysis_plan": {"script": {"path": names[0], "sha256": files[relative_paths[0]]}},
                "extensions": {
                    "tooling_source": {"files": files},
                    "finalization": {
                        "preflight_files": relative_paths,
                        "canonical_protocol_tool": {"path": str(tool), "sha256": MOD.sha256_file(tool)},
                        "canonical_protocol_schemas": dict(MOD.CANONICAL_SCHEMAS),
                        "script": {"path": names[1], "sha256": MOD.sha256_file(paths[1])},
                        "orchestrator": {"path": names[2], "sha256": MOD.sha256_file(paths[2])},
                        "build_preflight": {"path": names[3], "sha256": MOD.sha256_file(paths[3])},
                    },
                },
            }
            MOD.verify_tool_hashes(repo, value, tool)
            paths[3].write_text("tampered", encoding="utf-8")
            with self.assertRaises(ValueError):
                MOD.verify_tool_hashes(repo, value, tool)

    def test_failed_preflight_suppresses_controller_and_finalizes(self) -> None:
        calls: list[list[str]] = []
        factory_calls = 0

        def factory() -> list[str]:
            nonlocal factory_calls
            factory_calls += 1
            return ["controller"]

        def run(command, **_kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command, 2 if command == ["preflight"] else 0)

        result = MOD.invoke_campaign(
            ["preflight"], factory, ["finalizer"], cwd=Path("/"),
            environments=phase_environments(), ensure_terminal=ignore_terminal, run=run,
        )
        self.assertEqual(result, (2, None, 0))
        self.assertEqual(factory_calls, 0)
        self.assertEqual(calls, [["preflight"], ["finalizer"]])

    def test_finalizer_runs_after_controller_nonzero_or_exception(self) -> None:
        for mode in ("nonzero", "exception"):
            calls: list[list[str]] = []

            def run(command, **_kwargs):
                calls.append(command)
                if command == ["controller"] and mode == "exception":
                    raise OSError("transport failure")
                code = 2 if command == ["controller"] and mode == "nonzero" else 0
                return subprocess.CompletedProcess(command, code)

            result = MOD.invoke_campaign(
                ["preflight"], lambda: ["controller"], ["finalizer"], cwd=Path("/"),
                environments=phase_environments(), ensure_terminal=ignore_terminal, run=run,
            )
            self.assertEqual(result, (0, 2 if mode == "nonzero" else 125, 0))
            self.assertEqual(calls, [["preflight"], ["controller"], ["finalizer"]])

    def test_finalizer_runs_during_preflight_and_controller_interrupts(self) -> None:
        for interrupt_on in ("preflight", "controller"):
            calls: list[list[str]] = []

            def run(command, **_kwargs):
                calls.append(command)
                if command == [interrupt_on]:
                    raise KeyboardInterrupt()
                return subprocess.CompletedProcess(command, 0)

            with self.assertRaises(KeyboardInterrupt):
                MOD.invoke_campaign(
                    ["preflight"], lambda: ["controller"], ["finalizer"],
                    cwd=Path("/"), environments=phase_environments(),
                    ensure_terminal=ignore_terminal, run=run,
                )
            expected = [["preflight"], ["finalizer"]] if interrupt_on == "preflight" else [
                ["preflight"], ["controller"], ["finalizer"],
            ]
            self.assertEqual(calls, expected)

    def test_controller_factory_failure_still_finalizes(self) -> None:
        calls: list[list[str]] = []

        def factory() -> list[str]:
            raise ValueError("bad passed receipt")

        def run(command, **_kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command, 0)

        with self.assertRaises(ValueError):
            MOD.invoke_campaign(
                ["preflight"], factory, ["finalizer"], cwd=Path("/"),
                environments=phase_environments(), ensure_terminal=ignore_terminal, run=run,
            )
        self.assertEqual(calls, [["preflight"], ["finalizer"]])

    def test_finalizer_exec_failure_writes_one_incomplete_terminal_record(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            verdict = root / "verdict.json"
            protocol = root / "protocol.json"
            protocol.write_text("{}\n", encoding="utf-8")

            def run(command, **_kwargs):
                if command == ["finalizer"]:
                    raise OSError("executable unavailable")
                return subprocess.CompletedProcess(command, 0)

            def ensure(preflight_rc: int, controller_rc: int | None,
                       finalizer_rc: int, detail: str) -> None:
                MOD.ensure_terminal_fallback(
                    verdict, protocol=protocol, protocol_sha="a" * 64,
                    run_id="gpu-geometry-http-rtx5090-v11-test",
                    preflight_rc=preflight_rc, controller_rc=controller_rc,
                    finalizer_rc=finalizer_rc, detail=detail,
                )

            result = MOD.invoke_campaign(
                ["preflight"], lambda: ["controller"], ["finalizer"],
                cwd=root, environments=phase_environments(),
                ensure_terminal=ensure, run=run,
            )
            self.assertEqual(result, (0, 0, 125))
            record = json.loads(verdict.read_text(encoding="utf-8"))
            self.assertTrue(record["terminal"])
            self.assertEqual(record["verdict"], "incomplete_session")
            self.assertEqual(record["checks"][0]["code"], "orchestrator.finalizer_totality")
            with self.assertRaises(FileExistsError):
                MOD.write_once(verdict, record)

    def test_zero_exit_without_verdict_also_gets_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            verdict, protocol = root / "verdict.json", root / "protocol.json"
            protocol.write_text("{}\n", encoding="utf-8")

            def run(command, **_kwargs):
                return subprocess.CompletedProcess(command, 0)

            def ensure(preflight_rc: int, controller_rc: int | None,
                       finalizer_rc: int, detail: str) -> None:
                MOD.ensure_terminal_fallback(
                    verdict, protocol=protocol, protocol_sha="a" * 64,
                    run_id="gpu-geometry-http-rtx5090-v11-test",
                    preflight_rc=preflight_rc, controller_rc=controller_rc,
                    finalizer_rc=finalizer_rc, detail=detail,
                )

            self.assertEqual(MOD.invoke_campaign(
                ["preflight"], lambda: ["controller"], ["finalizer"],
                cwd=root, environments=phase_environments(),
                ensure_terminal=ensure, run=run,
            ), (0, 0, 0))
            self.assertEqual(
                json.loads(verdict.read_text(encoding="utf-8"))["verdict"],
                "incomplete_session",
            )

    def test_fallback_refuses_partial_or_wrong_run_terminal_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            protocol = root / "protocol.json"
            protocol.write_text("{}\n", encoding="utf-8")
            for payload in ("{", json.dumps({
                "schema": "gpu-f4-update-grid-ab-final-verdict/v1",
                "run_id": "gpu-geometry-http-rtx5090-v11-other",
                "terminal": True, "verdict": "incomplete_session",
                "checks": [], "summary": {},
            })):
                verdict = root / f"verdict-{len(payload)}.json"
                verdict.write_text(payload, encoding="utf-8")
                with self.assertRaises(ValueError):
                    MOD.ensure_terminal_fallback(
                        verdict, protocol=protocol, protocol_sha="a" * 64,
                        run_id="gpu-geometry-http-rtx5090-v11-test",
                        preflight_rc=0, controller_rc=0, finalizer_rc=125,
                        detail="failed",
                    )


if __name__ == "__main__":
    unittest.main()
