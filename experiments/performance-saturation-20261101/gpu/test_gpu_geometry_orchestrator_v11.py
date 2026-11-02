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
        "toolchain": {
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
                "version": "cc (Debian 14.2.0-19) 14.2.0",
            },
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
        self.assertEqual(command[:3], ["python3", "cloud/runpod_http_batch.py", "misagi-f4-geometry-v11"])
        self.assertEqual(command.count("--source-commit"), 1)
        self.assertEqual(command.count("--"), 1)
        remote = command[-1]
        self.assertIn(protocol_sha, remote)
        self.assertIn(preflight_sha, remote)
        self.assertIn("run_gpu_geometry_ab_v11.sh", remote)
        self.assertNotIn("install_nsys_tools.sh", remote)

    def test_remote_runner_builds_full_closure_before_nsys_install(self) -> None:
        text = (HERE / "run_gpu_geometry_ab_v11.sh").read_text(encoding="utf-8")
        archive = "suite bindings/rust include src cuda challenges"
        self.assertIn(archive, text)
        build_at = text.index("for arm in baseline candidate; do")
        install_at = text.index('bash "$REPO/ecc2k130/runner/codegen/install_nsys_tools.sh"')
        measure_at = text.index("run_matrix()")
        self.assertLess(build_at, install_at)
        self.assertLess(install_at, measure_at)

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

        result = MOD.invoke_campaign(["preflight"], factory, ["finalizer"], cwd=Path("/"), run=run)
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
                ["preflight"], lambda: ["controller"], ["finalizer"], cwd=Path("/"), run=run,
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
                    cwd=Path("/"), run=run,
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
            MOD.invoke_campaign(["preflight"], factory, ["finalizer"], cwd=Path("/"), run=run)
        self.assertEqual(calls, [["preflight"], ["finalizer"]])


if __name__ == "__main__":
    unittest.main()
