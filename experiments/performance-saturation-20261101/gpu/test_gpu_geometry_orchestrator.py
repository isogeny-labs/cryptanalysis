#!/usr/bin/env python3
"""Tests that v10 terminal finalization is unconditional and single-shot."""

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
    "orchestrate_gpu_geometry_v10", HERE / "orchestrate_gpu_geometry_v10.py"
)
assert SPEC is not None and SPEC.loader is not None
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


class GeometryOrchestratorTests(unittest.TestCase):
    def test_frozen_argv_mismatch_is_refused_before_controller(self) -> None:
        value = {
            "extensions": {
                "launch": {"controller_argv_template": ["controller", "<run_id>"]},
                "finalization": {"finalizer_argv_template": ["finalizer", "<frozen_protocol_sha256>"]},
            }
        }
        MOD.verify_argv_templates(value, ["controller", "run"], ["finalizer", "a" * 64], "run", "a" * 64)
        with self.assertRaises(ValueError):
            MOD.verify_argv_templates(value, ["controller", "tampered"], ["finalizer", "a" * 64], "run", "a" * 64)

    def test_local_tool_tamper_is_refused_by_dry_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            study = repo / MOD.STUDY
            study.mkdir(parents=True)
            analyzer = study / "analyzer.py"
            finalizer = study / "finalize_gpu_geometry_ab.py"
            orchestrator = study / "orchestrate_gpu_geometry_v10.py"
            tool = repo / "protocol_tool.py"
            for path in (analyzer, finalizer, orchestrator, tool):
                path.write_text(path.name, encoding="utf-8")
            relative_paths = [
                str(analyzer.relative_to(repo)), str(finalizer.relative_to(repo)),
                str(orchestrator.relative_to(repo)),
            ]
            files = {relative: MOD.sha256_file(repo / relative) for relative in relative_paths}
            value = {
                "analysis_plan": {"script": {"path": "analyzer.py", "sha256": files[relative_paths[0]]}},
                "extensions": {
                    "tooling_source": {"files": files},
                    "finalization": {
                        "preflight_files": relative_paths,
                        "canonical_protocol_tool": {"path": str(tool), "sha256": MOD.sha256_file(tool)},
                        "script": {"path": finalizer.name, "sha256": MOD.sha256_file(finalizer)},
                        "orchestrator": {"path": orchestrator.name, "sha256": MOD.sha256_file(orchestrator)},
                    },
                },
            }
            MOD.verify_tool_hashes(repo, value, tool)
            analyzer.write_text("tampered", encoding="utf-8")
            with self.assertRaises(ValueError):
                MOD.verify_tool_hashes(repo, value, tool)

    def test_finalizer_runs_after_remote_gate_error(self) -> None:
        calls: list[list[str]] = []

        def run(command, **_kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command, 2 if len(calls) == 1 else 0)

        result = MOD.invoke_pair(["controller"], ["finalizer"], cwd=Path("/"), run=run)
        self.assertEqual(result, (2, 0))
        self.assertEqual(calls, [["controller"], ["finalizer"]])

    def test_finalizer_runs_after_controller_exception(self) -> None:
        calls: list[list[str]] = []

        def run(command, **_kwargs):
            calls.append(command)
            if len(calls) == 1:
                raise OSError("controller transport failure")
            return subprocess.CompletedProcess(command, 0)

        result = MOD.invoke_pair(["controller"], ["finalizer"], cwd=Path("/"), run=run)
        self.assertEqual(result, (125, 0))
        self.assertEqual(calls, [["controller"], ["finalizer"]])

    def test_finalizer_runs_during_keyboard_interrupt_unwind(self) -> None:
        calls: list[list[str]] = []

        def run(command, **_kwargs):
            calls.append(command)
            if len(calls) == 1:
                raise KeyboardInterrupt()
            return subprocess.CompletedProcess(command, 0)

        with self.assertRaises(KeyboardInterrupt):
            MOD.invoke_pair(["controller"], ["finalizer"], cwd=Path("/"), run=run)
        self.assertEqual(calls, [["controller"], ["finalizer"]])


if __name__ == "__main__":
    unittest.main()
