#!/usr/bin/env python3
"""Adversarial standard-library tests for the v10 terminal finalizer."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "finalize_gpu_geometry_ab", HERE / "finalize_gpu_geometry_ab.py"
)
assert SPEC is not None and SPEC.loader is not None
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


def failures(judge: MOD.Judge, code: str) -> list[MOD.Check]:
    return [item for item in judge.checks if item.code == code and item.status != "passed"]


def minimal_protocol() -> dict:
    command = (
        "GPU_STUDY_SECURE=1 bash run_gpu_geometry_ab.sh '<run_id>' "
        "'<frozen_protocol_sha256>'"
    )
    return {
        "execution": {
            "placement": {
                "image": "runpod/base:1.0.2-ubuntu2404",
                "min_ram_gb": 62,
                "min_vcpu": 16,
                "max_price_usd_per_hour": 1.19,
            }
        },
        "extensions": {
            "tooling_source": {
                "public_origin": "https://github.com/isogeny-labs/cryptanalysis.git",
                "public_ref": "refs/heads/codex/runpod-http-gpu-geometry-v10-20261101",
                "commit": "1" * 40,
                "tree": "2" * 40,
                "git_archive_sha256": "3" * 64,
            },
            "launch": {"controller_argv_template": [command]},
            "finalization": {
                "request": {
                    "name_prefix": "misagi-f4-geometry-v10",
                    "cloudType": "SECURE",
                    "computeType": "GPU",
                    "gpuTypeIds": [MOD.EXPECTED_GPU],
                    "gpuCount": 1,
                }
            },
        },
    }


def good_receipt(protocol_sha: str = "a" * 64) -> dict:
    name = "misagi-f4-geometry-v10-012345abcdef"
    command = f"GPU_STUDY_SECURE=1 bash run_gpu_geometry_ab.sh 'run-1' '{protocol_sha}'"
    source = {
        "origin": "https://github.com/isogeny-labs/cryptanalysis.git",
        "ref": "refs/heads/codex/runpod-http-gpu-geometry-v10-20261101",
        "commit": "1" * 40,
        "tree": "2" * 40,
        "archive_sha256": "3" * 64,
        "public_ref_checked": True,
        "public_checked_at": "2026-11-01T00:00:00+00:00",
    }
    return {
        "schema": MOD.EXPECTED_RECEIPT_SCHEMA,
        "provider_actions": True,
        "error": None,
        "outputs": ["experiments/performance-saturation-20261101/gpu/runs-http/run-1"],
        "source": source,
        "command": command,
        "command_sha256": MOD.sha256_bytes(command.encode()),
        "request": {
            "name": name,
            "cloudType": "SECURE",
            "computeType": "GPU",
            "gpuTypeIds": [MOD.EXPECTED_GPU],
            "gpuCount": 1,
        },
        "pod": {
            "id": "pod_123",
            "name": name,
            "creation_response_ambiguous": False,
            "cloud": "SECURE",
            "image": "runpod/base:1.0.2-ubuntu2404",
            "cost": 1.19,
            "gpu": {"id": MOD.EXPECTED_GPU, "count": 1, "memory": 62, "vcpuCount": 32},
        },
        "remote_status": {
            "schema": MOD.EXPECTED_STATUS_SCHEMA,
            "stage": "complete",
            "done": True,
            "archive_ready": True,
            "returncode": 0,
            "timed_out": False,
            "worker_error_type": None,
            "job_id": name,
            "source_commit": source["commit"],
            "source_tree": source["tree"],
            "source_archive_sha256": source["archive_sha256"],
            "command_sha256": MOD.sha256_bytes(command.encode()),
            "hardware": {
                "pod_id": "pod_123",
                "gpus": [{"name": MOD.EXPECTED_GPU}],
            },
        },
        "cleanup": {"id": "pod_123", "delete_requested": True, "absence_verified": True},
        "started_at": "2026-11-01T00:00:00+00:00",
        "finished_at": "2026-11-01T00:10:00+00:00",
    }


def good_analysis(provisional: str = "geometry_supported") -> dict:
    gates = []
    for role, tag, _cell, _degree in MOD.WORKLOADS:
        gates.append({
            "workload": tag,
            "metric": "device_ms",
            "kind": "primary_improvement" if role == "primary" else "nonregression",
            "passed": provisional == "geometry_supported",
        })
        gates.append({
            "workload": tag,
            "metric": "complete_ms",
            "kind": "nonregression",
            "passed": provisional == "geometry_supported",
        })
    return {
        "schema": MOD.EXPECTED_ANALYSIS_SCHEMA,
        "protocol_id": MOD.PROTOCOL_ID,
        "protocol_version": MOD.PROTOCOL_VERSION,
        "protocol_sha256": "a" * 64,
        "session": "run-1",
        "terminal": False,
        "classification_status": "provisional_mechanical",
        "timing_classification_provisional": provisional,
        "terminal_adjudicator": "finalize_gpu_geometry_ab.py",
        "correctness_gate": "passed",
        "source_identity_gate": "passed",
        "numeric_isolation_gate": "passed",
        "profiled_timings_in_decision": False,
        "hardware_counters": "not collected; NCU is outside this protocol",
        "decision_gates": gates,
        "multiplicity": {
            "family_tests": 10,
            "correction": "Bonferroni",
            "one_sided_lower_tail": {"numerator": 1, "denominator": 200},
        },
        "mechanism_gate": {
            "status": "passed",
            "kernel_launches_per_arm": MOD.EXPECTED_KERNEL_LAUNCHES,
            "update_launches_per_arm": MOD.EXPECTED_UPDATE_LAUNCHES,
            "update_sequence_verified": True,
            "non_update_geometry_unchanged": True,
            "changed_update_launches": 1,
            "resources": dict(MOD.EXPECTED_RESOURCES),
        },
    }


class FinalizerAdversarialTests(unittest.TestCase):
    def test_exact_order_and_header_only_or_truncated_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "order.tsv"
            full = [MOD.ORDER_HEADER, *MOD.expected_order()]
            path.write_text("\n".join("\t".join(row) for row in full) + "\n", encoding="utf-8")
            judge = MOD.Judge()
            MOD.validate_order(path, judge)
            self.assertFalse(failures(judge, "order.schedule"))

            for rows in ([MOD.ORDER_HEADER], full[:-1]):
                path.write_text("\n".join("\t".join(row) for row in rows) + "\n", encoding="utf-8")
                judge = MOD.Judge()
                MOD.validate_order(path, judge)
                self.assertTrue(failures(judge, "order.schedule"))
                self.assertEqual(MOD.terminal_verdict(judge, "geometry_supported"), "invalid_measurement")

    def test_swapped_duplicate_extra_and_wrong_cell_order(self) -> None:
        base = MOD.expected_order()
        variants = []
        swapped = list(base); swapped[0], swapped[1] = swapped[1], swapped[0]; variants.append(swapped)
        variants.append([base[0], *base])
        variants.append([*base, base[-1]])
        wrong = list(base); wrong[3] = (*wrong[3][:-1], "wrong:cell:5"); variants.append(wrong)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "order.tsv"
            for rows in variants:
                path.write_text("\t".join(MOD.ORDER_HEADER) + "\n" +
                                "\n".join("\t".join(row) for row in rows) + "\n", encoding="utf-8")
                judge = MOD.Judge(); MOD.validate_order(path, judge)
                self.assertTrue(failures(judge, "order.schedule"))

    def test_missing_cleanup_is_incomplete_and_precedes_wrong_source(self) -> None:
        receipt = good_receipt()
        receipt["cleanup"] = None
        receipt["source"]["ref"] = "refs/heads/wrong"
        judge = MOD.Judge()
        MOD.check_receipt_core(
            receipt, minimal_protocol(), "run-1", "a" * 64,
            "experiments/performance-saturation-20261101/gpu/runs-http/run-1", judge,
        )
        self.assertTrue(failures(judge, "receipt.cleanup"))
        self.assertTrue(failures(judge, "receipt.source.ref"))
        self.assertEqual(MOD.terminal_verdict(judge, "geometry_supported"), "incomplete_session")

    def test_remote_gate_error_and_partial_output_are_incomplete(self) -> None:
        receipt = good_receipt()
        receipt["remote_status"].update(returncode=2, stage="complete", done=True)
        receipt["error"] = {"type": "BatchError", "detail": "remote GateError"}
        judge = MOD.Judge()
        MOD.check_receipt_core(
            receipt, minimal_protocol(), "run-1", "a" * 64,
            "experiments/performance-saturation-20261101/gpu/runs-http/run-1", judge,
        )
        self.assertTrue(judge.completion_failed)
        self.assertEqual(MOD.terminal_verdict(judge, None), "incomplete_session")

    def test_corrupt_archive_and_export_are_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "result.tar.gz"
            archive.write_bytes(b"truncated gzip")
            judge = MOD.Judge()
            self.assertIsNone(MOD.inspect_archive(archive, judge))
            self.assertTrue(judge.completion_failed)

            export = root / "export.json"
            export.write_text('{"schema":', encoding="utf-8")
            judge = MOD.Judge()
            self.assertIsNone(MOD.load_required_json(export, "export", judge))
            self.assertTrue(judge.completion_failed)

    def test_wrong_source_and_ref_are_invalid_when_complete(self) -> None:
        receipt = good_receipt()
        receipt["source"]["commit"] = "f" * 40
        receipt["source"]["ref"] = "refs/heads/wrong"
        judge = MOD.Judge()
        MOD.check_receipt_core(
            receipt, minimal_protocol(), "run-1", "a" * 64,
            "experiments/performance-saturation-20261101/gpu/runs-http/run-1", judge,
        )
        self.assertTrue(failures(judge, "receipt.source.commit"))
        self.assertTrue(failures(judge, "receipt.source.ref"))

    def test_analysis_is_provisional_and_mechanism_bound(self) -> None:
        judge = MOD.Judge()
        observed = MOD.check_analysis(good_analysis(), "a" * 64, "run-1", judge)
        self.assertEqual(observed, "geometry_supported")
        self.assertFalse(judge.completion_failed)
        self.assertFalse(judge.validity_failed)

        bad = good_analysis()
        bad["mechanism_gate"]["resources"]["registers_per_thread"] = 32
        judge = MOD.Judge(); MOD.check_analysis(bad, "a" * 64, "run-1", judge)
        self.assertTrue(failures(judge, "analysis.mechanism"))

    def test_provisional_classification_cannot_disagree_with_gates(self) -> None:
        bad = good_analysis("geometry_not_supported")
        for gate in bad["decision_gates"]:
            gate["passed"] = True
        judge = MOD.Judge(); MOD.check_analysis(bad, "a" * 64, "run-1", judge)
        self.assertTrue(failures(judge, "analysis.provisional_consistency"))

    def test_terminal_precedence_and_both_scientific_outcomes(self) -> None:
        judge = MOD.Judge()
        self.assertEqual(MOD.terminal_verdict(judge, "geometry_supported"), "geometry_supported")
        self.assertEqual(MOD.terminal_verdict(judge, "geometry_not_supported"), "geometry_not_supported")
        judge.invalid("bad", "bad identity")
        self.assertEqual(MOD.terminal_verdict(judge, "geometry_supported"), "invalid_measurement")
        judge.incomplete("missing", "missing cleanup")
        self.assertEqual(MOD.terminal_verdict(judge, "geometry_supported"), "incomplete_session")

    def test_terminal_record_is_write_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "verdict.json"
            MOD.write_once(path, {"verdict": "geometry_supported"})
            with self.assertRaises(FileExistsError):
                MOD.write_once(path, {"verdict": "geometry_not_supported"})
            self.assertEqual(json.loads(path.read_text())["verdict"], "geometry_supported")


if __name__ == "__main__":
    unittest.main()
