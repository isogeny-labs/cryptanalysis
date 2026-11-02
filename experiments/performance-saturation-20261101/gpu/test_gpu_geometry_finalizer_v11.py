#!/usr/bin/env python3
"""Adversarial standard-library tests for the v11 terminal finalizer."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "finalize_gpu_geometry_ab_v11", HERE / "finalize_gpu_geometry_ab_v11.py"
)
assert SPEC is not None and SPEC.loader is not None
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


def failures(judge: MOD.Judge, code: str) -> list[MOD.Check]:
    return [item for item in judge.checks if item.code == code and item.status != "passed"]


def minimal_protocol() -> dict:
    command = (
        "GPU_STUDY_SECURE=1 bash run_gpu_geometry_ab_v11.sh '<run_id>' "
        "'<frozen_protocol_sha256>' '<preflight_receipt_sha256>'"
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
                "public_ref": "refs/heads/codex/runpod-http-gpu-geometry-v11-20261101",
                "commit": "1" * 40,
                "tree": "2" * 40,
                "git_archive_sha256": "3" * 64,
            },
            "launch": {"controller_argv_template": [command]},
            "finalization": {
                "receipt_transport": {"kind": "authenticated-http"},
                "request": {
                    "name_prefix": "misagi-f4-geometry-v11",
                    "cloudType": "SECURE",
                    "computeType": "GPU",
                    "gpuTypeIds": [MOD.EXPECTED_GPU],
                    "gpuCount": 1,
                }
            },
        },
    }


def good_receipt(protocol_sha: str = "a" * 64) -> dict:
    name = "misagi-f4-geometry-v11-012345abcdef"
    command = f"GPU_STUDY_SECURE=1 bash run_gpu_geometry_ab_v11.sh 'run-1' '{protocol_sha}' '{'b' * 64}'"
    source = {
        "origin": "https://github.com/isogeny-labs/cryptanalysis.git",
        "ref": "refs/heads/codex/runpod-http-gpu-geometry-v11-20261101",
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
        "transport": {"kind": "authenticated-http"},
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
            "status": "RUNNING",
            "creation_response_ambiguous": False,
            "cloud": "SECURE",
            "image": "runpod/base:1.0.2-ubuntu2404",
            "cost": 1.19,
            "gpu": {"id": MOD.EXPECTED_GPU, "count": 1, "memory": 62, "vcpuCount": 32},
        },
        "remote_status": {
            "archive": {},
            "chunks": [],
            "command_started_unix": 1793491200,
            "finished_unix": 1793491800,
            "started_unix": 1793491200,
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
        "result": {},
        "cleanup": {"id": "pod_123", "delete_requested": True, "absence_verified": True},
        "started_at": "2026-11-01T00:00:00+00:00",
        "finished_at": "2026-11-01T00:10:00+00:00",
    }


def good_preflight(protocol_sha: str = "a" * 64) -> dict:
    baseline, candidate = "c" * 64, "d" * 64
    build = lambda arm, binary: {
        "arm": arm,
        "command": list(MOD.EXPECTED_BUILD_COMMAND),
        "returncode": 0,
        "elapsed_seconds": 1.25,
        "log_sha256": "e" * 64,
        "log_bytes": 123,
        "binary_sha256": binary,
        "binary_bytes": 456,
    }
    return {
        "schema": MOD.EXPECTED_PREFLIGHT_SCHEMA,
        "protocol_id": MOD.PROTOCOL_ID,
        "protocol_sha256": protocol_sha,
        "run_id": "run-1",
        "provider_actions": False,
        "tool_sha256": MOD.sha256_file(HERE / "preflight_gpu_geometry_v11.py"),
        "source": dict(MOD.EXPECTED_PREFLIGHT_SOURCE),
        "build_contract": dict(MOD.EXPECTED_BUILD_CONTRACT),
        "started_at": "2026-10-31T23:00:00Z",
        "status": "passed",
        "error": None,
        "finished_at": "2026-10-31T23:30:00Z",
        "elapsed_seconds": 1800.0,
        "archive": {
            "roots": list(MOD.EXPECTED_ARCHIVE_ROOTS),
            "sha256": MOD.EXPECTED_ARCHIVE_SHA256,
            "bytes": MOD.EXPECTED_ARCHIVE_BYTES,
            "files": MOD.EXPECTED_ARCHIVE_FILES,
            "required_members": list(MOD.EXPECTED_REQUIRED_MEMBERS),
        },
        "source_delta": [MOD.EXPECTED_F4_PATH],
        "files_per_arm": MOD.EXPECTED_ARCHIVE_FILES,
        "builds": [build("baseline", baseline), build("candidate", candidate)],
        "binary_contract": {
            "baseline_sha256": baseline,
            "baseline_aa_sha256": baseline,
            "candidate_sha256": candidate,
            "baseline_aa_equals_baseline": True,
            "candidate_differs": True,
        },
        "toolchain": {
            "bootstrap": {
                "url": MOD.EXPECTED_RUSTUP_URL,
                "sha256": MOD.EXPECTED_RUSTUP_SHA256,
                "log_sha256": "f" * 64,
                "log_bytes": 789,
            },
            "rustc": {
                "toolchain": MOD.EXPECTED_TOOLCHAIN,
                "sha256": MOD.EXPECTED_RUSTC_SHA256,
                "version": "rustc 1.91.1 (ed61e7d7e 2025-11-07)\nbinary: rustc",
            },
            "cargo": {
                "toolchain": MOD.EXPECTED_TOOLCHAIN,
                "sha256": MOD.EXPECTED_CARGO_SHA256,
                "version": "cargo 1.91.1 (ea2d97820 2025-10-10)",
            },
            "cc": {
                "realpath": "/usr/bin/x86_64-linux-gnu-gcc-14",
                "sha256": MOD.EXPECTED_CC_SHA256,
                "version": "cc (Debian 14.2.0-19) 14.2.0",
            },
        },
    }


def good_analysis(provisional: str = "geometry_supported") -> dict:
    gates = []
    aa_gates = []
    for role, tag, _cell, _degree in MOD.WORKLOADS:
        gates.append({
            "workload": tag,
            "metric": "device_ms",
            "kind": "primary_improvement" if role == "primary" else "nonregression",
            "passed": provisional == "geometry_supported",
        })
        for metric in ("device_ms", "complete_ms"):
            aa_gates.append({
                "workload": tag,
                "metric": metric,
                "kind": "same_session_aa_interval_admissible",
                "lower": {"numerator": 99, "denominator": 100},
                "upper": {"numerator": 101, "denominator": 100},
                "noise_floor": {"numerator": 100, "denominator": 99},
                "resolution_ceiling": {"numerator": 51, "denominator": 50},
                "passed": True,
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
        "terminal_adjudicator": "finalize_gpu_geometry_ab_v11.py",
        "correctness_gate": "passed",
        "source_identity_gate": "passed",
        "numeric_isolation_gate": "passed",
        "same_session_aa_gate": "passed",
        "profiled_timings_in_decision": False,
        "hardware_counters": "not collected; NCU is outside this protocol",
        "decision_gates": gates,
        "aa_control_gates": aa_gates,
        "multiplicity": {
            "family_intervals": 20,
            "ab_intervals": 10,
            "aa_intervals": 10,
            "sides": 2,
            "correction": "Bonferroni",
            "per_tail_probability": {"numerator": 1, "denominator": 800},
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
    def test_utc_parser_accepts_z_and_offsets_but_rejects_naive_or_malformed(self) -> None:
        zulu = MOD.parse_utc("2026-11-01T01:02:03Z")
        offset = MOD.parse_utc("2026-11-01T03:02:03+02:00")
        self.assertIsNotNone(zulu)
        self.assertEqual(offset, zulu)
        self.assertEqual(zulu.isoformat(), "2026-11-01T01:02:03+00:00")
        for value in ("2026-11-01T01:02:03", "not-a-time", "", None, {}, 7):
            self.assertIsNone(MOD.parse_utc(value))

    def test_clean_build_preflight_golden_path_and_mutations(self) -> None:
        judge = MOD.Judge()
        finished = MOD.check_preflight_receipt(good_preflight(), "run-1", "a" * 64, judge)
        self.assertIsNotNone(finished)
        self.assertFalse(judge.completion_failed)
        self.assertFalse(judge.validity_failed)
        self.assertTrue(all(check.status == "passed" for check in judge.checks))

        for mutation, code in (
            (lambda value: value["archive"]["required_members"].remove("cuda/ca_device.cuh"),
             "preflight.archive"),
            (lambda value: value["archive"]["required_members"].remove("challenges/elliptic/corpus.json"),
             "preflight.archive"),
            (lambda value: value["toolchain"]["rustc"].update(sha256="0" * 64),
             "preflight.toolchain"),
            (lambda value: value["binary_contract"].update(candidate_differs=False),
             "preflight.binary_contract"),
        ):
            value = good_preflight()
            mutation(value)
            judge = MOD.Judge()
            MOD.check_preflight_receipt(value, "run-1", "a" * 64, judge)
            self.assertTrue(failures(judge, code), code)

    def test_failed_or_truncated_preflight_is_incomplete(self) -> None:
        failed = {
            key: value for key, value in good_preflight().items()
            if key in {
                "schema", "protocol_id", "protocol_sha256", "run_id", "provider_actions", "tool_sha256",
                "source", "build_contract", "started_at", "status", "error", "finished_at",
                "elapsed_seconds",
            }
        }
        failed["status"] = "failed"
        failed["error"] = {"type": "PreflightError", "detail": "missing cuda"}
        judge = MOD.Judge()
        MOD.check_preflight_receipt(failed, "run-1", "a" * 64, judge)
        self.assertTrue(failures(judge, "preflight.status"))
        self.assertTrue(failures(judge, "preflight.error"))
        self.assertEqual(MOD.terminal_verdict(judge, None), "incomplete_session")

        judge = MOD.Judge()
        MOD.check_preflight_receipt({"status": "passed"}, "run-1", "a" * 64, judge)
        self.assertTrue(judge.completion_failed or judge.validity_failed)

    def test_remote_tool_hashes_require_repo_relative_paths(self) -> None:
        relative = "experiments/performance-saturation-20261101/gpu/run_gpu_geometry_ab_v11.sh"
        digest = "a" * 64
        self.assertEqual(
            MOD.parse_remote_tool_hashes(f"{digest}  {relative}\n", {relative: digest}, [relative]),
            {relative: digest},
        )
        for bad in (
            f"{digest}  /root/runpod-http-source/repo/{relative}\n",
            f"{digest}  {relative}\n{digest}  {relative}\n",
        ):
            with self.assertRaises(ValueError):
                MOD.parse_remote_tool_hashes(bad, {relative: digest}, [relative])

    def test_receipt_and_scientific_completion_timestamp_order(self) -> None:
        receipt = good_receipt()
        judge = MOD.Judge()
        MOD.check_receipt_core(
            receipt, minimal_protocol(), "run-1", "a" * 64, "b" * 64,
            "experiments/performance-saturation-20261101/gpu/runs-http/run-1", judge,
        )
        started = MOD.parse_utc(receipt["started_at"])
        completed = MOD.parse_utc("2026-11-01T00:05:00Z")
        finished = MOD.parse_utc(receipt["finished_at"])
        self.assertIsNotNone(started)
        self.assertIsNotNone(completed)
        self.assertIsNotNone(finished)
        self.assertLessEqual(started, completed)
        self.assertLessEqual(completed, finished)
        self.assertFalse(failures(judge, "receipt.timestamps"))
        self.assertFalse(failures(judge, "receipt.timestamp_order"))
        MOD.check_scientific_completion_order(receipt, completed, judge)
        self.assertFalse(failures(judge, "session.controller_time_order"))

        judge = MOD.Judge()
        too_late = MOD.parse_utc("2026-11-01T00:10:01Z")
        self.assertIsNotNone(too_late)
        MOD.check_scientific_completion_order(receipt, too_late, judge)
        self.assertTrue(failures(judge, "session.controller_time_order"))

        judge = MOD.Judge()
        MOD.check_scientific_completion_order(
            {"started_at": {}, "finished_at": ["malformed"]}, completed, judge,
        )
        self.assertTrue(failures(judge, "session.controller_time_order"))

        receipt["finished_at"] = "2026-10-31T23:59:59Z"
        judge = MOD.Judge()
        MOD.check_receipt_core(
            receipt, minimal_protocol(), "run-1", "a" * 64, "b" * 64,
            "experiments/performance-saturation-20261101/gpu/runs-http/run-1", judge,
        )
        self.assertTrue(failures(judge, "receipt.timestamp_order"))

    def test_valid_receipt_core_golden_path_has_zero_failures(self) -> None:
        judge = MOD.Judge()
        MOD.check_receipt_core(
            good_receipt(), minimal_protocol(), "run-1", "a" * 64, "b" * 64,
            "experiments/performance-saturation-20261101/gpu/runs-http/run-1", judge,
        )
        self.assertGreater(len(judge.checks), 40)
        self.assertFalse(judge.completion_failed)
        self.assertFalse(judge.validity_failed)
        self.assertTrue(all(check.status == "passed" for check in judge.checks))

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

    def test_candidate_always_middle_schedule_is_rejected(self) -> None:
        rows = []
        rounds = [("warmup", 0), *[("measure", index) for index in range(1, 7)]]
        for phase, round_index in rounds:
            arms = (("baseline", "candidate", "baseline-aa") if round_index % 2
                    else ("baseline-aa", "candidate", "baseline"))
            for role, tag, cell, degree in MOD.WORKLOADS:
                for arm in arms:
                    rows.append((phase, str(round_index), tag, role, arm, f"{cell}:{degree}"))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "order.tsv"
            path.write_text("\t".join(MOD.ORDER_HEADER) + "\n" +
                            "\n".join("\t".join(row) for row in rows) + "\n", encoding="utf-8")
            judge = MOD.Judge(); MOD.validate_order(path, judge)
            self.assertTrue(failures(judge, "order.schedule"))

    def test_registered_six_permutations_are_position_and_direction_balanced(self) -> None:
        first_tag = MOD.WORKLOADS[0][1]
        rows = [row for row in MOD.expected_order()
                if row[0] == "measure" and row[2] == first_tag]
        orders = [[row[4] for row in rows[index:index + 3]] for index in range(0, 18, 3)]
        self.assertEqual(len({tuple(order) for order in orders}), 6)
        for arm in MOD.ARMS:
            self.assertEqual([order[position] for order in orders for position in range(3)].count(arm), 6)
            self.assertEqual([order.index(arm) for order in orders].count(0), 2)
            self.assertEqual([order.index(arm) for order in orders].count(1), 2)
            self.assertEqual([order.index(arm) for order in orders].count(2), 2)
        for left in MOD.ARMS:
            for right in MOD.ARMS:
                if left < right:
                    self.assertEqual(sum(order.index(left) < order.index(right) for order in orders), 3)

    def test_missing_cleanup_is_incomplete_and_precedes_wrong_source(self) -> None:
        receipt = good_receipt()
        receipt["cleanup"] = None
        receipt["source"]["ref"] = "refs/heads/wrong"
        judge = MOD.Judge()
        MOD.check_receipt_core(
            receipt, minimal_protocol(), "run-1", "a" * 64, "b" * 64,
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
            receipt, minimal_protocol(), "run-1", "a" * 64, "b" * 64,
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
            receipt, minimal_protocol(), "run-1", "a" * 64, "b" * 64,
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

    def test_failed_same_session_aa_is_provisional_invalid_measurement(self) -> None:
        value = good_analysis("geometry_supported")
        value["aa_control_gates"][0].update(
            lower={"numerator": 9, "denominator": 10},
            upper={"numerator": 11, "denominator": 10},
            noise_floor={"numerator": 10, "denominator": 9},
            passed=False,
        )
        value["same_session_aa_gate"] = "failed"
        value["timing_classification_provisional"] = "invalid_measurement"
        judge = MOD.Judge(); observed = MOD.check_analysis(value, "a" * 64, "run-1", judge)
        self.assertFalse(judge.validity_failed)
        self.assertEqual(MOD.terminal_verdict(judge, observed), "invalid_measurement")

    def test_wide_aa_interval_containing_one_is_rejected(self) -> None:
        value = good_analysis("geometry_supported")
        gate = value["aa_control_gates"][0]
        gate.update(
            lower={"numerator": 9, "denominator": 10},
            upper={"numerator": 11, "denominator": 10},
            noise_floor={"numerator": 10, "denominator": 9},
            passed=True,
        )
        judge = MOD.Judge(); MOD.check_analysis(value, "a" * 64, "run-1", judge)
        self.assertTrue(failures(judge, "analysis.aa_gates.resolution"))

    def test_parseable_malformed_provisional_is_invalid_not_incomplete(self) -> None:
        bad = good_analysis()
        bad["timing_classification_provisional"] = "surprise"
        judge = MOD.Judge(); observed = MOD.check_analysis(bad, "a" * 64, "run-1", judge)
        self.assertEqual(observed, "surprise")
        self.assertFalse(judge.completion_failed)
        self.assertTrue(judge.validity_failed)
        self.assertEqual(MOD.terminal_verdict(judge, observed), "invalid_measurement")

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

    def test_unexpected_partial_structure_still_writes_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            out = root / "verdict.json"
            argv = [
                "--protocol", str(root / "protocol.json"),
                "--protocol-sha256", "a" * 64,
                "--protocol-tool", str(root / "tool.py"),
                "--preflight-receipt", str(root / "preflight.json"),
                "--receipt", str(root / "receipt.json"),
                "--archive", str(root / "archive.tar.gz"),
                "--remote-metadata", str(root / "remote"),
                "--session", str(root / "run-1"),
                "--out", str(out),
            ]
            with mock.patch.object(MOD, "adjudicate", side_effect=AttributeError("bad nested value")), \
                    mock.patch.object(MOD, "official_output_path", return_value=out):
                self.assertEqual(MOD.main(argv), 0)
            record = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(record["verdict"], "incomplete_session")
            self.assertTrue(record["terminal"])


if __name__ == "__main__":
    unittest.main()
