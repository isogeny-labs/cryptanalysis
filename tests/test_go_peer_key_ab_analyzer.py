import copy
import argparse
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
GO_DIR = REPO / "experiments/performance-saturation-20261101/go"
ANALYZER_PATH = GO_DIR / "analyze_remote_peer_key_ab.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ANALYZER = load_module("go_peer_key_ab_aa_analyzer", GO_DIR / "analyze_remote_peer_key_ab.py")
SHARED = load_module("go_peer_key_shared", GO_DIR / "analyze_remote_ab.py")
CAMPAIGN_CORE = load_module("go_peer_key_campaign_core", GO_DIR / "run_campaign.py")
L2 = load_module("go_peer_key_l2", GO_DIR / "l2_measure.py")
EXPORTER = load_module("go_peer_key_exporter", GO_DIR / "export_remote_peer_key_ab.py")
CAMPAIGN = load_module("go_peer_key_campaign", GO_DIR / "run_remote_peer_key_campaign.py")
RUNNER = load_module("go_peer_key_remote_runner", GO_DIR / "run_remote_ab.py")
ANALYZER.shared = SHARED
ANALYZER.campaign_core = CAMPAIGN_CORE
ANALYZER.l2_core = L2
ANALYZER.export_core = EXPORTER


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def fingerprints(case: str, token: str = "a") -> dict[str, str]:
    digest = token * 64
    if case.startswith("BenchmarkStateVersionVector/"):
        return {"vector_sha256": digest}
    return {"lines_sha256": digest, "reached_vector_sha256": digest}


def analysis_row(
    case: str,
    replicate: int,
    arm: str,
    *,
    allocation_ratio: int = 5,
    ab_baseline_ns: int = 105,
    aa_left_ns: int = 100,
    aa_right_ns: int = 100,
) -> dict:
    if arm == ANALYZER.BASELINE_ARM:
        allocation, timing = 100, ab_baseline_ns
    elif arm == ANALYZER.CANDIDATE_ARM:
        allocation, timing = allocation_ratio, 100
    elif arm == ANALYZER.AA_LEFT_ARM:
        allocation, timing = 100, aa_left_ns
    else:
        allocation, timing = 100, aa_right_ns
    return {
        "warmup": False,
        "case": case,
        "replicate": replicate,
        "arm": arm,
        "parsed": {
            "fingerprints": {"answer": case},
            "metrics": {
                "B/op": allocation,
                "allocs/op": allocation,
                "ns/op": timing,
                "cpu-ns/op": timing,
            },
        },
    }


def analysis_rows(cases: list[str], **kwargs) -> list[dict]:
    return [
        analysis_row(case, replicate, arm, **kwargs)
        for case in cases
        for replicate in range(1, 21)
        for arm in ANALYZER.EXPECTED_ARMS
    ]


def valid_preflight() -> dict:
    pressure = {
        "some": {"avg10": 0.0, "avg60": 0.0, "avg300": 0.0, "total": 10.0},
        "full": {"avg10": 0.0, "avg60": 0.0, "avg300": 0.0, "total": 0.0},
    }
    return {
        "quiet": True,
        "other_cpu_seconds": 0.0,
        "other_cpu_by_task": {},
        "other_top": {},
        "psi_some_avg10_max": 0.0,
        "pressures": {"cpu": copy.deepcopy(pressure), "memory": copy.deepcopy(pressure)},
        "limits": dict(L2.PREFLIGHT_LIMITS),
    }


def valid_reservation() -> dict:
    return {
        "cpus": [2, 18],
        "smt_siblings": [2, 18],
        "evicted": True,
        "threads_moved": 0,
        "left_on_reserved": {"user_threads": [], "kernel_threads": []},
    }


def valid_execution() -> dict:
    return {
        "pinned_cpus": [2],
        "reserved_cpus": [2, 18],
        "child_affinity_observed": [2],
        "tree_affinity": {"tasks_outside": 0, "cpus_seen": [2], "examples": []},
        "subreaper": True,
        "descendants_killed": 0,
        "exit": {"returncode": 0, "signal": None, "timed_out": False},
        "wall_ns": 1_000_000_000,
        "rusage": {
            "user_s": 0.9,
            "sys_s": 0.0,
            "maxrss_kib": 1024,
            "minflt": 2,
            "majflt": 0,
            "nvcsw": 1,
            "nivcsw": 1,
        },
        "schedstat": {
            "run_ns": 900_000_000,
            "wait_ns": 0,
            "slices": 10,
            "threads_seen": 1,
            "sample_interval_seconds": 0.01,
        },
        "max_threads_observed": 1,
        "contention": {
            "samples": 100,
            "samples_with_foreign_runnable": 0,
            "foreign_examples": [],
            "pinned_cpu_jiffies_delta": {
                "user": 90,
                "nice": 0,
                "system": 10,
                "idle": 1,
                "iowait": 0,
                "irq": 0,
                "softirq": 0,
                "steal": 0,
            },
            "psi_total_delta_us": {
                "cpu": {"some": 0.0, "full": 0.0},
                "memory": {"some": 0.0, "full": 0.0},
            },
            "procs_running_after": 1,
        },
    }


def transport_fixture() -> tuple[dict, dict]:
    protocol = json.loads((GO_DIR / "protocol.v9.json").read_text(encoding="utf-8"))
    protocol["freeze"]["protocol_sha256"] = "f" * 64
    planned = protocol["extensions"]["remote_execution"]
    command = planned["command_template"].replace(
        planned["protocol_hash_token"], protocol["freeze"]["protocol_sha256"]
    )
    command_sha = hashlib.sha256(command.encode()).hexdigest()
    name = planned["pod_name_prefix"] + "0123456789ab"
    pod_id = "pod_fixture_123"
    archive_sha = "a" * 64
    manifest_sha = "b" * 64
    result_file_sha = "c" * 64
    archive_bytes = 1024
    receipt = {
        "schema": "runpod.http-batch.receipt/v1",
        "provider_actions": True,
        "source": {
            **{
                key: planned["source"][key]
                for key in ("origin", "ref", "commit", "tree", "archive_sha256")
            },
            "public_ref_checked": True,
            "public_checked_at": "2026-11-02T00:00:00+00:00",
        },
        "command": command,
        "command_sha256": command_sha,
        "outputs": [planned["output"]],
        "request": {
            "cloudType": "SECURE",
            "computeType": "CPU",
            "containerDiskInGb": 60,
            "cpuFlavorIds": ["cpu3c"],
            "cpuFlavorPriority": "custom",
            "environment_keys": planned["request_environment_keys"],
            "gpuCount": None,
            "gpuTypeIds": None,
            "imageName": planned["image"],
            "minRAMPerGPU": None,
            "minVCPUPerGPU": None,
            "ports": ["8888/http"],
            "secrets_redacted": True,
            "startup_sha256": ANALYZER.EXPECTED_STARTUP_SHA256,
            "vcpuCount": 32,
            "name": name,
        },
        "transport": planned["transport"],
        "cpu_guard": dict(ANALYZER.EXPECTED_CPU_GUARD),
        "started_at": "2026-11-02T00:00:00+00:00",
        "pod": {
            "cloud": "SECURE",
            "cost": 0.96,
            "cpu": {"id": "cpu3c", "memory": 64, "vcpuCount": 32},
            "createdAt": "2026-11-02T00:00:01Z",
            "creation_response_ambiguous": False,
            "cudaVersion": None,
            "dataCenterId": "EU-FIXTURE-1",
            "gpu": None,
            "id": pod_id,
            "image": planned["image"],
            "name": name,
            "startedAt": "2026-11-02T00:00:01Z",
            "status": "RUNNING",
        },
        "remote_status": {
            "archive": {
                "bytes": archive_bytes,
                "files": 2,
                "manifest_sha256": manifest_sha,
                "sha256": archive_sha,
                "uncompressed_bytes": 2048,
            },
            "archive_ready": True,
            "chunks": [{
                "bytes": archive_bytes,
                "index": 0,
                "offset": 0,
                "path": "/v1/result/000000",
                "sha256": archive_sha,
            }],
            "command_sha256": command_sha,
            "command_started_unix": 2.0,
            "done": True,
            "finished_unix": 3.0,
            "hardware": {"gpus": [], "nvcc": "", "pod_id": pod_id},
            "job_id": name,
            "returncode": 0,
            "schema": "runpod.http-batch.status/v1",
            "source_archive_sha256": planned["source"]["archive_sha256"],
            "source_commit": planned["source"]["commit"],
            "source_tree": planned["source"]["tree"],
            "stage": "complete",
            "started_unix": 1.0,
            "timed_out": False,
            "worker_error_type": None,
        },
        "result": {
            "archive": planned["controller_archive_path"],
            "archive_bytes": archive_bytes,
            "archive_sha256": archive_sha,
            "metadata": str(Path(planned["controller_receipt_path"]).with_suffix(".remote")),
            "files": [{"bytes": 1, "path": planned["output"] + "/failure.json", "sha256": result_file_sha}],
        },
        "cleanup": {"absence_verified": True, "delete_requested": True, "id": pod_id},
        "error": None,
        "finished_at": "2026-11-02T00:00:04+00:00",
    }
    return receipt, protocol


def benchmark_stdout(case: str) -> bytes:
    marks = fingerprints(case)
    correctness = " ".join(f"{key}={value}" for key, value in marks.items())
    return (
        correctness
        + "\n"
        + f"{case}-1 100 105 ns/op 100 cpu-ns/op 5 B/op 5 allocs/op\n"
    ).encode()


def schedule_fixture(root: Path):
    run = root / ANALYZER.EXPECTED_OUTPUT
    campaign = run / "campaign"
    for name in ("benchmark-output", "benchmark-stderr", "run-metadata"):
        (campaign / "raw" / name).mkdir(parents=True, exist_ok=True)
    protocol_sha = "f" * 64
    runner_sha, l2_sha = "e" * 64, "d" * 64
    affinity = list(range(32))
    reserved = [2, 18]
    runner_affinity = [cpu for cpu in affinity if cpu not in reserved]
    filenames = {
        ANALYZER.BASELINE_ARM: "coord-baseline.test",
        ANALYZER.CANDIDATE_ARM: "coord-candidate.test",
        ANALYZER.AA_LEFT_ARM: "coord-baseline-aa-left.test",
        ANALYZER.AA_RIGHT_ARM: "coord-baseline-aa-right.test",
    }
    digests = {
        ANALYZER.BASELINE_ARM: "b" * 64,
        ANALYZER.CANDIDATE_ARM: "c" * 64,
        ANALYZER.AA_LEFT_ARM: "b" * 64,
        ANALYZER.AA_RIGHT_ARM: "b" * 64,
    }
    binaries = {
        arm: f"/root/{ANALYZER.EXPECTED_OUTPUT}/build/{filename}"
        for arm, filename in filenames.items()
    }
    lock = {
        "path": "/tmp/crypto-bench.lock",
        "exclusive": True,
        "nonblocking": True,
        "device": 1,
        "inode": 2,
        "owner_pid": 3,
    }
    reservation = valid_reservation()
    manifest = {
        "schema": "go-coordinator-peer-key-campaign/2",
        "phase": "fixed-peer-key-ab-aa-v9",
        "protocol_sha256": protocol_sha,
        "benchmark_source_sha256": ANALYZER.EXPECTED_BENCHMARK_SHA256,
        "cases": list(ANALYZER.EXPECTED_CASES),
        "warmups": 3,
        "replicates": 20,
        "benchtime": "100x",
        "benchmark_cpu": 2,
        "session_affinity": affinity,
        "runner_affinity": runner_affinity,
        "reservation": reservation,
        "environment": dict(ANALYZER.EXPECTED_ENVIRONMENT),
        "environment_sha256": ANALYZER.EXPECTED_ENVIRONMENT_SHA256,
        "arms": [
            {"id": arm, "binary": binaries[arm], "sha256": digests[arm]}
            for arm in ANALYZER.EXPECTED_ARMS
        ],
        "order_cycle": [list(order) for order in ANALYZER.ORDER_CYCLE],
        "preflight": valid_preflight(),
        "l2_thresholds": dict(L2.THRESHOLDS),
        "session_lock": lock,
        "runner_sha256": runner_sha,
        "l2_measure_sha256": l2_sha,
    }
    write_json(campaign / "manifest.json", manifest)
    rows = []
    sequence = 0
    for case_index, case in enumerate(ANALYZER.EXPECTED_CASES, 1):
        rounds = [(True, value) for value in range(1, 4)]
        rounds += [(False, value) for value in range(1, 21)]
        for warmup, replicate in rounds:
            for position, arm in enumerate(ANALYZER.ORDER_CYCLE[(replicate - 1) % 4], 1):
                sequence += 1
                kind = "warmup" if warmup else "measured"
                run_id = (
                    f"{sequence:04d}_{kind}_case{case_index:02d}_r{replicate:02d}_"
                    f"p{position}_{arm}"
                )
                stdout = campaign / "raw/benchmark-output" / f"{run_id}.txt"
                stderr = campaign / "raw/benchmark-stderr" / f"{run_id}.txt"
                metadata = campaign / "raw/run-metadata" / f"{run_id}.json"
                stdout.write_bytes(benchmark_stdout(case))
                stderr.write_bytes(b"")
                parsed = CAMPAIGN_CORE.parse_output(stdout.read_bytes())
                execution = valid_execution()
                isolated = L2.evaluate_l2(execution, manifest["preflight"], reservation)
                item = {
                    "schema": "go-coordinator-peer-key-row/2",
                    "run_id": run_id,
                    "phase": manifest["phase"],
                    "protocol_sha256": protocol_sha,
                    "benchmark_source_sha256": ANALYZER.EXPECTED_BENCHMARK_SHA256,
                    "arm": arm,
                    "binary": binaries[arm],
                    "binary_sha256": digests[arm],
                    "case": case,
                    "case_index": case_index,
                    "replicate": replicate,
                    "warmup": warmup,
                    "order_position": position,
                    "sequence": sequence,
                    "status": "completed",
                    "outcome_class": "verified",
                    "started": "2026-11-01T00:00:00Z",
                    "finished": "2026-11-01T00:00:01Z",
                    "outer_wall_ns": execution["wall_ns"],
                    "exit_status": 0,
                    "timed_out": False,
                    "instrumentation_error": None,
                    "command": [
                        "/usr/bin/taskset", "-c", "2", binaries[arm],
                        "-test.run=^$", f"-test.bench=^{case}$", "-test.benchmem",
                        "-test.benchtime=100x", "-test.count=1", "-test.cpu=1",
                        "-test.v", "-test.timeout=20m",
                    ],
                    "environment": dict(ANALYZER.EXPECTED_ENVIRONMENT),
                    "environment_sha256": ANALYZER.EXPECTED_ENVIRONMENT_SHA256,
                    "session_affinity": affinity,
                    "runner_affinity": runner_affinity,
                    "reservation_cpus": reserved,
                    "expected_child_affinity": [2],
                    "parsed": parsed,
                    "rusage": {
                        "user_seconds": 0.9,
                        "system_seconds": 0.0,
                        "max_rss_kib": 1024,
                        "minor_faults": 2,
                        "major_faults": 0,
                        "voluntary_context_switches": 1,
                        "involuntary_context_switches": 1,
                    },
                    "execution": execution,
                    "isolation": isolated,
                    "artifacts": {
                        "stdout": f"raw/benchmark-output/{run_id}.txt",
                        "stdout_sha256": SHARED.sha256(stdout),
                        "stderr": f"raw/benchmark-stderr/{run_id}.txt",
                        "stderr_sha256": SHARED.sha256(stderr),
                        "metadata": f"raw/run-metadata/{run_id}.json",
                    },
                }
                write_json(metadata, item)
                rows.append(item)
    rows_path = campaign / "rows.jsonl"
    rows_path.write_text(
        "".join(json.dumps(item, sort_keys=True) + "\n" for item in rows), encoding="utf-8"
    )
    restoration = {
        "attempted": 0,
        "restored": 0,
        "exited": 0,
        "failures": 0,
        "passes": True,
        "records": [],
        "runner_affinity_after_restore": affinity,
        "runner_affinity_passes": True,
    }
    write_json(
        campaign / "summary.json",
        {
            "schema": "go-coordinator-peer-key-campaign-summary/2",
            "phase": manifest["phase"],
            "protocol_sha256": protocol_sha,
            "planned": 552,
            "attempted": 552,
            "failures": 0,
            "l2_failures": 0,
            "rows_sha256": SHARED.sha256(rows_path),
            "benchmark_cpu": 2,
            "session_affinity": affinity,
            "runner_affinity": runner_affinity,
            "reservation": reservation,
            "restoration": restoration,
            "session_lock": lock,
            "environment": dict(ANALYZER.EXPECTED_ENVIRONMENT),
            "environment_sha256": ANALYZER.EXPECTED_ENVIRONMENT_SHA256,
            "preflight": manifest["preflight"],
            "order_cycle": manifest["order_cycle"],
        },
    )
    protocol = {
        "freeze": {"protocol_sha256": protocol_sha},
        "links": {
            "benchmark_cases": list(ANALYZER.EXPECTED_CASES),
            "campaign_runner_sha256": runner_sha,
            "l2_measure_sha256": l2_sha,
            "benchmark_environment_sha256": ANALYZER.EXPECTED_ENVIRONMENT_SHA256,
        },
    }
    return run, rows, protocol


class InferenceTests(unittest.TestCase):
    def test_joint_aa_ab_gate_uses_exact_q_1_over_960(self) -> None:
        cases = [f"case-{index}" for index in range(6)]
        results, allocation, timing, aa_valid, pairs = ANALYZER.compute_case_results(
            analysis_rows(cases), cases
        )
        self.assertTrue(allocation)
        self.assertTrue(timing)
        self.assertTrue(aa_valid)
        self.assertEqual(pairs, 240)
        self.assertEqual(ANALYZER.LOWER_QUANTILE, Fraction(1, 960))
        metric = results[0]["metrics"]["ns/op"]
        self.assertEqual(metric["lower_quantile"], "1/960")
        self.assertEqual(metric["aa"]["simultaneous_interval"]["quantiles"], ["1/960", "959/960"])
        self.assertEqual(metric["aa"]["symmetric_noise_factor"]["numerator"], "1")

    def test_allocation_requires_both_metrics_in_every_case(self) -> None:
        rows = analysis_rows(["case"], allocation_ratio=6)
        _, allocation, timing, aa_valid, pairs = ANALYZER.compute_case_results(rows, ["case"])
        self.assertFalse(allocation)
        self.assertTrue(timing)
        self.assertTrue(aa_valid)
        self.assertEqual(pairs, 40)

    def test_aa_interval_failure_invalidates_timing_control(self) -> None:
        rows = analysis_rows(
            ["case"], aa_left_ns=106, aa_right_ns=100, ab_baseline_ns=110
        )
        results, _, timing, aa_valid, _ = ANALYZER.compute_case_results(rows, ["case"])
        self.assertTrue(timing)
        self.assertFalse(aa_valid)
        self.assertFalse(results[0]["metrics"]["ns/op"]["aa"]["contains_one"])

    def test_fixed_aa_labels_have_explicit_reverse_direction_effect(self) -> None:
        forward = analysis_rows(["case"], aa_left_ns=104, aa_right_ns=100)
        reverse = analysis_rows(["case"], aa_left_ns=100, aa_right_ns=104)
        f = ANALYZER.compute_case_results(forward, ["case"])[0][0]["metrics"]["ns/op"]["aa"]
        r = ANALYZER.compute_case_results(reverse, ["case"])[0][0]["metrics"]["ns/op"]["aa"]
        self.assertNotEqual(f["paired_median"], r["paired_median"])
        self.assertEqual(f["direction"], "aa_left_over_aa_right")


class CorrectnessAndVerdictTests(unittest.TestCase):
    def all_rows(self) -> list[dict]:
        rows = []
        for case in ANALYZER.EXPECTED_CASES:
            for warmup, rounds in ((True, range(1, 4)), (False, range(1, 21))):
                for replicate in rounds:
                    for arm in ANALYZER.EXPECTED_ARMS:
                        item = analysis_row(case, replicate, arm)
                        item["warmup"] = warmup
                        rows.append(item)
        return rows

    def test_all_552_outputs_are_compared_across_arms_and_rounds(self) -> None:
        rows = self.all_rows()
        result = ANALYZER.correctness_inventory(rows, list(ANALYZER.EXPECTED_CASES))
        self.assertEqual(result, {"matches": 138, "mismatches": 0})
        rows[1]["parsed"]["fingerprints"] = {"answer": "cross-pair-different"}
        result = ANALYZER.correctness_inventory(rows, list(ANALYZER.EXPECTED_CASES))
        self.assertEqual(result["mismatches"], 1)

    def test_warmup_and_case_invariance_mismatches_are_wrong_answers(self) -> None:
        rows = self.all_rows()
        target = next(row for row in rows if row["warmup"] and row["replicate"] == 2)
        for row in rows:
            if row["case"] == target["case"] and row["warmup"] and row["replicate"] == 2:
                row["parsed"]["fingerprints"] = {"answer": "all-four-but-new"}
        result = ANALYZER.correctness_inventory(rows, list(ANALYZER.EXPECTED_CASES))
        self.assertEqual(result["mismatches"], 1)
        self.assertTrue(ANALYZER.transport_is_complete(1, result["mismatches"]))
        self.assertFalse(ANALYZER.transport_is_complete(2, result["mismatches"]))

    def test_terminal_precedence_and_timing_invalid_status(self) -> None:
        decide = ANALYZER.choose_verdict
        self.assertEqual(decide(complete=False, correctness=False, allocation=False,
                                timing_numeric=False, timing_isolation=False), "inconclusive")
        self.assertEqual(decide(complete=True, correctness=False, allocation=False,
                                timing_numeric=False, timing_isolation=True), "wrong_answer")
        self.assertEqual(decide(complete=True, correctness=True, allocation=False,
                                timing_numeric=True, timing_isolation=False), "invalid_measurement")
        claims = ANALYZER.claim_statuses(
            complete=True, correctness=True, allocation=True,
            timing_numeric=True, timing_isolation=False,
        )
        self.assertEqual(claims["C-ab-allocation"], "supported")
        self.assertEqual(claims["C-ab-timing"], "invalid_measurement")


class L2Tests(unittest.TestCase):
    def test_valid_cumulative_observations_earn_l2(self) -> None:
        result = L2.evaluate_l2(valid_execution(), valid_preflight(), valid_reservation())
        self.assertTrue(result["passes"])
        self.assertEqual(result["earned_level"], "L2")

    def test_run_delay_failure_falls_to_l1(self) -> None:
        execution = valid_execution()
        execution["schedstat"]["wait_ns"] = 10_000_000
        result = L2.evaluate_l2(execution, valid_preflight(), valid_reservation())
        self.assertFalse(result["passes"])
        self.assertEqual(result["earned_level"], "L1")
        self.assertIn("run_delay", result["blocking"])

    def test_affinity_or_reservation_failure_falls_to_l0(self) -> None:
        execution = valid_execution()
        execution["tree_affinity"]["tasks_outside"] = 1
        result = L2.evaluate_l2(execution, valid_preflight(), valid_reservation())
        self.assertEqual(result["earned_level"], "L0")
        reservation = valid_reservation()
        reservation["left_on_reserved"]["user_threads"] = [{"tid": 10}]
        result = L2.evaluate_l2(valid_execution(), valid_preflight(), reservation)
        self.assertEqual(result["earned_level"], "L0")

    def test_negative_nonfinite_bool_and_foreign_domains_fail_closed(self) -> None:
        mutations = []
        negative = valid_execution()
        negative["schedstat"]["wait_ns"] = -1
        mutations.append(negative)
        nonfinite = valid_execution()
        nonfinite["rusage"]["user_s"] = math.nan
        mutations.append(nonfinite)
        boolean = valid_execution()
        boolean["rusage"]["nivcsw"] = False
        mutations.append(boolean)
        foreign = valid_execution()
        foreign["contention"]["samples_with_foreign_runnable"] = 101
        mutations.append(foreign)
        for execution in mutations:
            result = L2.evaluate_l2(execution, valid_preflight(), valid_reservation())
            self.assertEqual(result["earned_level"], "L0")
            self.assertIn("raw_observation_domains", result["blocking"])

    def test_zero_schedstat_bad_interval_threads_and_kernel_records_fail_closed(self) -> None:
        mutations = []
        no_threads = valid_execution()
        no_threads["schedstat"]["threads_seen"] = 0
        mutations.append(no_threads)
        no_slices = valid_execution()
        no_slices["schedstat"]["slices"] = 0
        mutations.append(no_slices)
        wrong_interval = valid_execution()
        wrong_interval["schedstat"]["sample_interval_seconds"] = 0.02
        mutations.append(wrong_interval)
        negative_threads = valid_execution()
        negative_threads["max_threads_observed"] = -1
        mutations.append(negative_threads)
        missing_observed_cpu = valid_execution()
        missing_observed_cpu["tree_affinity"]["cpus_seen"] = []
        mutations.append(missing_observed_cpu)
        for execution in mutations:
            result = L2.evaluate_l2(execution, valid_preflight(), valid_reservation())
            self.assertEqual(result["earned_level"], "L0")
            self.assertIn("raw_observation_domains", result["blocking"])
        malformed = valid_reservation()
        malformed["left_on_reserved"]["kernel_threads"] = [{"pid": 1}]
        result = L2.evaluate_l2(valid_execution(), valid_preflight(), malformed)
        self.assertEqual(result["earned_level"], "L0")
        self.assertIn("whole_core_reservation", result["blocking"])

    def test_preflight_recomputes_raw_receipt_and_rejects_bad_psi(self) -> None:
        preflight = valid_preflight()
        self.assertTrue(L2.evaluate_preflight(preflight)["passes"])
        preflight["pressures"]["cpu"]["some"]["avg10"] = True
        self.assertFalse(L2.evaluate_preflight(preflight)["passes"])
        preflight = valid_preflight()
        preflight["other_cpu_seconds"] = 0.1
        self.assertFalse(L2.evaluate_preflight(preflight)["passes"])

    def test_restoration_requires_unique_identity_and_exact_readback(self) -> None:
        receipt = {
            "attempted": 1, "restored": 1, "exited": 0, "failures": 0,
            "passes": True, "runner_affinity_after_restore": list(range(32)),
            "runner_affinity_passes": True,
            "records": [{
                "pid": 10, "tid": 11, "starttime_ticks": 12,
                "affinity": [2, 18, 20], "evicted_affinity": [20],
                "status": "restored", "restored_affinity": [2, 18, 20],
            }],
        }
        reservation = valid_reservation()
        reservation["threads_moved"] = 1
        self.assertTrue(ANALYZER._verify_restoration(receipt, reservation, list(range(32))))
        receipt["records"][0]["restored_affinity"] = [20]
        with self.assertRaisesRegex(ValueError, "readback"):
            ANALYZER._verify_restoration(receipt, reservation, list(range(32)))

    def test_restoration_rejects_bad_domains_and_inexact_eviction(self) -> None:
        base = {
            "attempted": 1, "restored": 1, "exited": 0, "failures": 0,
            "passes": True, "runner_affinity_after_restore": list(range(32)),
            "runner_affinity_passes": True,
            "records": [{
                "pid": 10, "tid": 11, "starttime_ticks": 12,
                "affinity": [2, 18, 20], "evicted_affinity": [20],
                "status": "restored", "restored_affinity": [2, 18, 20],
            }],
        }
        reservation = valid_reservation()
        reservation["threads_moved"] = 1
        mutations = []
        invalid_pid = copy.deepcopy(base)
        invalid_pid["records"][0]["pid"] = 0
        mutations.append(invalid_pid)
        invalid_tid = copy.deepcopy(base)
        invalid_tid["records"][0]["tid"] = -1
        mutations.append(invalid_tid)
        duplicate_cpu = copy.deepcopy(base)
        duplicate_cpu["records"][0]["affinity"] = [2, 18, 18, 20]
        mutations.append(duplicate_cpu)
        wrong_difference = copy.deepcopy(base)
        wrong_difference["records"][0]["evicted_affinity"] = [18, 20]
        mutations.append(wrong_difference)
        bool_count = copy.deepcopy(base)
        bool_count["attempted"] = True
        mutations.append(bool_count)
        zero_start_identity = copy.deepcopy(base)
        zero_start_identity["records"][0]["starttime_ticks"] = 0
        mutations.append(zero_start_identity)
        for receipt in mutations:
            with self.assertRaises(ValueError):
                ANALYZER._verify_restoration(receipt, reservation, list(range(32)))


class BindingTests(unittest.TestCase):
    def test_exact_552_schedule_and_raw_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run, rows, protocol = schedule_fixture(Path(temporary))
            result = ANALYZER.verify_frozen_schedule(run, rows, protocol)
            self.assertEqual(result["rows"], 552)
            rows[0]["sequence"] = 2
            with self.assertRaisesRegex(ValueError, "schedule mismatch"):
                ANALYZER.verify_frozen_schedule(run, rows, protocol)

    def test_wrong_command_environment_stdout_and_metadata_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run, rows, protocol = schedule_fixture(Path(temporary))
            rows[0]["command"][3] = rows[1]["binary"]
            with self.assertRaisesRegex(ValueError, "benchmark argv"):
                ANALYZER.verify_frozen_schedule(run, rows, protocol)
            rows[0]["command"][3] = rows[0]["binary"]
            rows[0]["environment"]["PATH"] = "/tmp"
            with self.assertRaisesRegex(ValueError, "identity mismatch"):
                ANALYZER.verify_frozen_schedule(run, rows, protocol)
            rows[0]["environment"] = dict(ANALYZER.EXPECTED_ENVIRONMENT)
            stdout = run / "campaign" / rows[0]["artifacts"]["stdout"]
            stdout.write_bytes(stdout.read_bytes().replace(b"105 ns/op", b"106 ns/op"))
            rows[0]["artifacts"]["stdout_sha256"] = SHARED.sha256(stdout)
            with self.assertRaisesRegex(ValueError, "parsed stdout"):
                ANALYZER.verify_frozen_schedule(run, rows, protocol)

    def test_extracted_run_equals_authenticated_archive_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run = Path(temporary) / ANALYZER.EXPECTED_OUTPUT
            run.mkdir()
            artifact = run / "rows.jsonl"
            artifact.write_text("sealed\n", encoding="utf-8")
            receipt = {"result": {"files": [{
                "path": f"{ANALYZER.EXPECTED_OUTPUT}/rows.jsonl",
                "bytes": artifact.stat().st_size,
                "sha256": SHARED.sha256(artifact),
            }]}}
            self.assertEqual(ANALYZER.verify_extracted_run(
                run, receipt, ANALYZER.EXPECTED_OUTPUT)["files"], 1)
            artifact.write_text("tampered\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "content mismatch"):
                ANALYZER.verify_extracted_run(run, receipt, ANALYZER.EXPECTED_OUTPUT)

    def test_four_retained_binaries_and_baseline_control_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run = Path(temporary)
            (run / "build").mkdir()
            names = {
                ANALYZER.BASELINE_ARM: "coord-baseline.test",
                ANALYZER.CANDIDATE_ARM: "coord-candidate.test",
                ANALYZER.AA_LEFT_ARM: "coord-baseline-aa-left.test",
                ANALYZER.AA_RIGHT_ARM: "coord-baseline-aa-right.test",
            }
            records, campaign = {}, {}
            for arm, name in names.items():
                path = run / "build" / name
                path.write_bytes(b"candidate" if arm == ANALYZER.CANDIDATE_ARM else b"baseline")
                records[arm] = {
                    "binary": name, "binary_bytes": path.stat().st_size,
                    "binary_sha256": SHARED.sha256(path),
                }
                campaign[arm] = {"binary": f"/run/build/{name}", "sha256": SHARED.sha256(path)}
            ANALYZER.verify_binary_artifacts(run, records, campaign)
            campaign[ANALYZER.AA_RIGHT_ARM]["sha256"] = records[ANALYZER.CANDIDATE_ARM]["binary_sha256"]
            with self.assertRaisesRegex(ValueError, "binary mismatch"):
                ANALYZER.verify_binary_artifacts(run, records, campaign)

    def test_dependency_and_toolchain_hashes_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            dependency = Path(temporary) / "dependency.py"
            dependency.write_text("VALUE = 1\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "dependency SHA-256"):
                ANALYZER.load_verified_module(dependency, "0" * 64, "tampered")
        toolchain = {
            "url": "https://go.dev/dl/" + ANALYZER.GO_ARCHIVE,
            "archive": ANALYZER.GO_ARCHIVE,
            "archive_bytes": ANALYZER.GO_ARCHIVE_BYTES,
            "archive_sha256": "0" * 64,
            "go_version": "go version go1.27.3 linux/amd64",
            "go_env": {"GOOS": "linux", "GOARCH": "amd64"},
        }
        with self.assertRaisesRegex(ValueError, "Go download"):
            ANALYZER.verify_go_toolchain(toolchain)

    def test_controller_contract_uses_v9_128_mib_budget(self) -> None:
        planned = {
            "source": {"commit": "c" * 40},
        }
        argv = ANALYZER.expected_controller_argv(planned)
        self.assertIn("go-peer-key-ab-aa-v9", argv)
        self.assertEqual(argv[argv.index("--max-result-mib") + 1], "128")
        self.assertEqual(argv[argv.index("--timeout") + 1], "25200")

    def test_transport_receipt_is_exact_and_fail_closed(self) -> None:
        receipt, protocol = transport_fixture()
        self.assertEqual(ANALYZER.verify_transport(receipt, protocol)["pod_id"], "pod_fixture_123")
        mutations: list[tuple[str, dict]] = []
        startup = copy.deepcopy(receipt)
        startup["request"]["startup_sha256"] = "0" * 64
        mutations.append(("startup", startup))
        bad_name = copy.deepcopy(receipt)
        malformed = protocol["extensions"]["remote_execution"]["pod_name_prefix"] + "0123456789abx"
        bad_name["request"]["name"] = malformed
        bad_name["pod"]["name"] = malformed
        bad_name["remote_status"]["job_id"] = malformed
        mutations.append(("name", bad_name))
        for value in (True, math.nan, 0):
            bad_cost = copy.deepcopy(receipt)
            bad_cost["pod"]["cost"] = value
            mutations.append((f"cost-{value!r}", bad_cost))
        missing_status = copy.deepcopy(receipt)
        del missing_status["remote_status"]["done"]
        mutations.append(("missing-status", missing_status))
        extra_status = copy.deepcopy(receipt)
        extra_status["remote_status"]["unexpected"] = 1
        mutations.append(("extra-status", extra_status))
        top_error = copy.deepcopy(receipt)
        top_error["error"] = {"type": "synthetic", "detail": "bad"}
        mutations.append(("top-error", top_error))
        for value in (False, -1):
            bad_archive = copy.deepcopy(receipt)
            bad_archive["remote_status"]["archive"]["uncompressed_bytes"] = value
            mutations.append((f"archive-{value!r}", bad_archive))
        for label, mutated in mutations:
            with self.subTest(label=label), self.assertRaises(ValueError):
                ANALYZER.verify_transport(mutated, protocol)

    def test_build_environment_is_allowlisted_and_provider_values_do_not_leak(self) -> None:
        with tempfile.TemporaryDirectory(prefix="go-coord-remote-ab-") as temporary:
            root = Path(temporary)
            go = root / "go/bin/go"
            go.parent.mkdir(parents=True)
            go.write_bytes(b"fixture")
            hostile = {
                "GOEXPERIMENT": "arenas",
                "GOWORK": "/tmp/hostile.work",
                "GOAMD64": "v4",
                "CC": "/tmp/hostile-cc",
                "CGO_CFLAGS": "-funsafe-math-optimizations",
            }
            with mock.patch.dict(os.environ, hostile, clear=False):
                environment = RUNNER.build_environment(go, root)
            self.assertEqual(environment["GOEXPERIMENT"], "")
            self.assertEqual(environment["CGO_CFLAGS"], "-O2 -g")
            self.assertEqual(environment["GOWORK"], "off")
            self.assertEqual(environment["GOAMD64"], "v1")
            self.assertEqual(environment["CC"], "/usr/bin/gcc")
            digest = RUNNER.environment_sha256(environment)
            self.assertEqual(ANALYZER.verify_build_environment(environment, digest), digest)

    def test_build_and_test_argv_and_aa_copy_receipts_are_exact(self) -> None:
        go_command = "/tmp/go-coord-remote-ab-fixture/go/bin/go"
        digest = "a" * 64
        baseline = {
            "command": [
                go_command, "test", "-c", "-trimpath", "-o",
                f"/workspace/cryptanalysis/{ANALYZER.EXPECTED_OUTPUT}/build/"
                "coord-baseline.test",
                ".",
            ],
            "cwd": "bindings/go",
            "environment_sha256": digest,
            "stdout": "",
            "binary": "coord-baseline.test",
            "binary_bytes": 10,
            "binary_sha256": "b" * 64,
        }
        ANALYZER.verify_build_record(
            baseline, ANALYZER.BASELINE_ARM, go_command, None
        )
        injected = copy.deepcopy(baseline)
        injected["command"].insert(-1, "-tags=hostile")
        with self.assertRaisesRegex(ValueError, "not exact"):
            ANALYZER.verify_build_record(
                injected, ANALYZER.BASELINE_ARM, go_command, None
            )
        aa = {
            **baseline,
            "command": ["byte-identical copy", "coord-baseline.test"],
            "binary": "coord-baseline-aa-left.test",
            "binary_bytes": 10,
            "binary_sha256": "b" * 64,
            "derived_from": "coord-baseline.test",
        }
        ANALYZER.verify_build_record(
            aa, ANALYZER.AA_LEFT_ARM, go_command, baseline
        )
        aa["derived_from"] = "coord-candidate.test"
        with self.assertRaisesRegex(ValueError, "not exact"):
            ANALYZER.verify_build_record(
                aa, ANALYZER.AA_LEFT_ARM, go_command, baseline
            )
        test_record = {
            "command": [go_command, "test", "./..."],
            "cwd": "bindings/go",
            "environment_sha256": digest,
            "exit_status": 0,
            "log": "baseline.txt",
            "log_bytes": 0,
            "log_sha256": "c" * 64,
        }
        ANALYZER.verify_test_record(test_record, go_command, "baseline.txt")
        test_record["command"] = [go_command, "test", "-run", "TestOnly", "./..."]
        with self.assertRaisesRegex(ValueError, "not exact"):
            ANALYZER.verify_test_record(test_record, go_command, "baseline.txt")

    def test_wrong_answer_exclusion_does_not_invent_contention(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            row = {
                "run_id": "fixture", "arm": ANALYZER.BASELINE_ARM,
                "case": ANALYZER.EXPECTED_CASES[0], "replicate": 1,
                "warmup": False, "status": "completed", "exit_status": 0,
                "timed_out": False, "outer_wall_ns": 1000,
                "parsed": {
                    "iterations": 100,
                    "metrics": {"ns/op": 1, "cpu-ns/op": 1, "B/op": 1, "allocs/op": 1},
                    "fingerprints": fingerprints(ANALYZER.EXPECTED_CASES[0]),
                },
                "rusage": {},
                "isolation": {"earned_level": "L2", "blocking": []},
                "artifacts": {
                    "stdout": "stdout", "stderr": "stderr", "metadata": "metadata"
                },
            }
            for name in row["artifacts"].values():
                (base / name).write_bytes(b"x")
            run = EXPORTER.make_run(
                row,
                base=base,
                timing_valid=True,
                mismatches={(row["case"], False, 1)},
            )
            self.assertFalse(run["measurements"]["wall_valid"])
            self.assertFalse(run["isolation"]["contended"])
            self.assertNotIn("cumulative L2", " ".join(run["isolation"]["blockers"]))
            self.assertEqual(run["verification"]["status"], "refuted")

    def test_failed_row_export_is_not_completed_and_wall_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            protocol_path = root / "protocol.v9.json"
            shutil.copy2(GO_DIR / "protocol.v9.json", protocol_path)
            source_commit = json.loads(protocol_path.read_text())["arms"][0]["instrument"]["commit"]
            frozen = subprocess.run(
                [
                    "python3",
                    "/workspace/crypto-autoresearcher/tools/experiment_protocol.py",
                    "freeze",
                    str(protocol_path),
                    "--commit",
                    source_commit,
                    "--filed-before-affected-data",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            self.assertEqual(frozen.returncode, 0, frozen.stdout)
            protocol_sha = json.loads(protocol_path.read_text())["freeze"]["protocol_sha256"]
            run, rows, _ = schedule_fixture(root)
            manifest_path = run / "campaign/manifest.json"
            campaign_manifest = json.loads(manifest_path.read_text())
            campaign_manifest["protocol_sha256"] = protocol_sha
            write_json(manifest_path, campaign_manifest)
            for row in rows:
                row["protocol_sha256"] = protocol_sha
            failed = rows[0]
            failed.update(
                {
                    "status": "not_completed",
                    "outcome_class": "instrument_error",
                    "exit_status": None,
                    "instrumentation_error": {
                        "type": "RuntimeError",
                        "message": "synthetic",
                    },
                }
            )
            for row in rows:
                write_json(run / "campaign" / row["artifacts"]["metadata"], row)
            rows_path = run / "campaign/rows.jsonl"
            rows_path.write_text(
                "".join(json.dumps(item, sort_keys=True) + "\n" for item in rows),
                encoding="utf-8",
            )
            summary_path = run / "campaign/summary.json"
            summary = json.loads(summary_path.read_text())
            summary["protocol_sha256"] = protocol_sha
            summary["failures"] = 1
            summary["rows_sha256"] = SHARED.sha256(rows_path)
            write_json(summary_path, summary)
            build_dir = run / "build"
            build_dir.mkdir()
            names = {
                ANALYZER.BASELINE_ARM: "coord-baseline.test",
                ANALYZER.CANDIDATE_ARM: "coord-candidate.test",
                ANALYZER.AA_LEFT_ARM: "coord-baseline-aa-left.test",
                ANALYZER.AA_RIGHT_ARM: "coord-baseline-aa-right.test",
            }
            arm_records = {}
            for arm, name in names.items():
                path = build_dir / name
                path.write_bytes(b"candidate" if arm == ANALYZER.CANDIDATE_ARM else b"baseline")
                arm_records[arm] = {
                    "binary": name,
                    "binary_bytes": path.stat().st_size,
                    "binary_sha256": SHARED.sha256(path),
                }
            tooling = run / "tooling"
            tooling.mkdir()
            analysis_copy = tooling / ANALYZER_PATH.name
            shutil.copy2(ANALYZER_PATH, analysis_copy)
            retained_key = str(ANALYZER_PATH.relative_to(REPO))
            tests = run / "tests"
            tests.mkdir()
            (tests / "baseline.txt").write_text("ok\n", encoding="utf-8")
            (tests / "candidate.txt").write_text("ok\n", encoding="utf-8")
            write_json(tests / "manifest.json", {"schema": "fixture"})
            write_json(
                build_dir / "manifest.json",
                {
                    "source_archive": {"commit": source_commit},
                    "toolchain": {
                        "archive": ANALYZER.GO_ARCHIVE,
                        "archive_bytes": ANALYZER.GO_ARCHIVE_BYTES,
                        "archive_sha256": ANALYZER.GO_ARCHIVE_SHA256,
                    },
                    "host": {
                        "cpuinfo_sha256": "1" * 64,
                        "cpu_model": "fixture",
                        "uname": "fixture-kernel",
                    },
                    "placement": {
                        "allowed_cpus": list(range(32)),
                        "memory_limit_bytes": ANALYZER.EXPECTED_MEMORY_BYTES,
                    },
                    "runner": {
                        "retained": {
                            retained_key: {
                                "path": f"tooling/{analysis_copy.name}",
                                "bytes": analysis_copy.stat().st_size,
                                "sha256": SHARED.sha256(analysis_copy),
                            }
                        }
                    },
                    "arms": arm_records,
                },
            )
            write_json(run / "isolation.json", {"timing_valid": False})
            output = run / "campaign/export.json"
            export = EXPORTER.produce(run, protocol_sha, source_commit, output)
            EXPORTER.validate(export, output)
            EXPORTER.write_once(output, export)
            canonical = subprocess.run(
                [
                    "python3",
                    "/workspace/crypto-autoresearcher/tools/experiment_protocol.py",
                    "check-export",
                    str(output),
                    "--protocol",
                    str(protocol_path),
                    "--verify-files",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            self.assertEqual(canonical.returncode, 0, canonical.stdout)
            exported = next(item for item in export["runs"] if item["run_id"] == failed["run_id"])
            self.assertEqual(exported["status"], "infra_error")
            self.assertEqual(exported["outcome_class"], "not_completed")
            self.assertEqual(exported["verification"]["status"], "not_run")
            self.assertFalse(exported["measurements"]["wall_valid"])


class FailureTotalExportTests(unittest.TestCase):
    def frozen_protocol(self, root: Path) -> tuple[Path, dict]:
        protocol_path = root / "protocol.v9.json"
        shutil.copy2(GO_DIR / "protocol.v9.json", protocol_path)
        source_commit = json.loads(protocol_path.read_text())["extensions"]["remote_execution"][
            "source"
        ]["commit"]
        frozen = subprocess.run(
            [
                "python3",
                "/workspace/crypto-autoresearcher/tools/experiment_protocol.py",
                "freeze",
                str(protocol_path),
                "--commit",
                source_commit,
                "--filed-before-affected-data",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        self.assertEqual(frozen.returncode, 0, frozen.stdout)
        return protocol_path, json.loads(protocol_path.read_text())

    def failure_run(self, root: Path, protocol: dict) -> tuple[Path, Path]:
        run = root / ANALYZER.EXPECTED_OUTPUT
        (run / "campaign").mkdir(parents=True)
        tooling = run / "tooling"
        tooling.mkdir()
        shutil.copy2(ANALYZER_PATH, tooling / ANALYZER_PATH.name)
        failure_path = run / "failure.json"
        write_json(
            failure_path,
            {
                "schema": "go-coordinator-remote-failure/v1",
                "protocol_sha256": protocol["freeze"]["protocol_sha256"],
                "source_commit": protocol["extensions"]["remote_execution"]["source"]["commit"],
                "phase": "fixed-peer-key-ab-aa-v9",
                "stage": "build_baseline",
                "error": {"type": "RuntimeError", "detail": "synthetic early failure"},
                "usable_prefix_rows": None,
            },
        )
        return run, failure_path

    def test_early_failure_export_is_canonical_and_formally_inconclusive_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            protocol_path, protocol = self.frozen_protocol(root)
            run, failure_path = self.failure_run(root, protocol)
            (run / "build").mkdir()
            (run / "build/manifest.json").write_bytes(b'{"schema":')
            output = run / "campaign/export.json"
            export = EXPORTER.produce_failure(
                run,
                protocol["freeze"]["protocol_sha256"],
                protocol["extensions"]["remote_execution"]["source"]["commit"],
                output,
                failure_path,
            )
            EXPORTER.write_once(output, export)
            self.assertEqual(len(export["runs"]), 552)
            self.assertTrue(all(row["status"] == "infra_error" for row in export["runs"]))
            self.assertEqual(export["backend_record"]["usable_prefix_rows"], 0)
            canonical = subprocess.run(
                [
                    "python3",
                    "/workspace/crypto-autoresearcher/tools/experiment_protocol.py",
                    "check-export",
                    str(output),
                    "--protocol",
                    str(protocol_path),
                    "--verify-files",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            self.assertEqual(canonical.returncode, 0, canonical.stdout)
            pre_summary_files = [path for path in run.rglob("*") if path.is_file()]
            summary = {
                "schema": "go-coordinator-remote-summary/v1",
                "status": "mechanical_failure",
                "protocol_sha256": protocol["freeze"]["protocol_sha256"],
                "source_commit": protocol["extensions"]["remote_execution"]["source"]["commit"],
                "failure_path": "failure.json",
                "failure_sha256": SHARED.sha256(failure_path),
                "failure_stage": "build_baseline",
                "usable_prefix_rows": 0,
                "export_path": "campaign/export.json",
                "export_sha256": SHARED.sha256(output),
                "remote_returncode": 2,
                "claims_evaluated": False,
                "output_budget_bytes": 96_000_000,
                "output_bytes_before_summary": sum(path.stat().st_size for path in pre_summary_files),
                "output_files_before_summary": len(pre_summary_files),
                "remote_summary_reserve_bytes": 65_536,
            }
            write_json(run / "remote-summary.json", summary)
            verified = ANALYZER.verify_failure_export(
                run,
                protocol_path,
                protocol,
                summary,
                Path("/workspace/crypto-autoresearcher/tools/experiment_protocol.py"),
            )
            self.assertEqual(verified["usable_prefix_rows"], 0)
            forged = json.loads(output.read_text())
            forged["runs"][0]["measurements"]["counted"]["bytes_per_op"] = 7
            forged["runs"][0]["isolation"]["contended"] = True
            write_json(output, forged)
            summary["export_sha256"] = SHARED.sha256(output)
            summary["output_bytes_before_summary"] = sum(
                path.stat().st_size
                for path in run.rglob("*")
                if path.is_file() and path != run / "remote-summary.json"
            )
            write_json(run / "remote-summary.json", summary)
            with self.assertRaisesRegex(ValueError, "exact raw recomputation"):
                ANALYZER.verify_failure_export(
                    run,
                    protocol_path,
                    protocol,
                    summary,
                    Path("/workspace/crypto-autoresearcher/tools/experiment_protocol.py"),
                )

    def test_early_failure_export_without_retained_analyzer_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            protocol_path, protocol = self.frozen_protocol(root)
            run, failure_path = self.failure_run(root, protocol)
            (run / "tooling" / ANALYZER_PATH.name).unlink()
            output = run / "campaign/export.json"
            with self.assertRaisesRegex(ValueError, "registered analyzer"):
                EXPORTER.produce_failure(
                    run,
                    protocol["freeze"]["protocol_sha256"],
                    protocol["extensions"]["remote_execution"]["source"]["commit"],
                    output,
                    failure_path,
                )

    def test_runner_does_not_publish_output_before_tooling_is_retained(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "owned-output"
            options = argparse.Namespace(
                out=output,
                mode="combined",
                protocol_sha256="f" * 64,
                phase="fixed-peer-key-ab-aa-v9",
                baseline_binary_sha256=None,
                candidate_binary_sha256=None,
                expected_cpus=32,
                expected_memory_bytes=64_000_000_000,
                expected_cpu_flavor="cpu3c",
            )
            with (
                mock.patch.object(RUNNER, "RUNNER_BINDING_PATH", str(GO_DIR / "run_remote_peer_key_ab.py")),
                mock.patch.object(RUNNER, "EXPORTER_PATH", str(GO_DIR / "export_remote_peer_key_ab.py")),
                mock.patch.object(RUNNER, "ANALYZER_PATH", str(ANALYZER_PATH)),
                mock.patch.object(RUNNER, "SUPPORT_PATHS", ()),
                mock.patch.object(RUNNER, "CAMPAIGN_RUNNER_PATH", None),
                mock.patch.object(RUNNER, "L2_MEASURE_PATH", None),
                mock.patch.object(RUNNER, "git", return_value="a" * 40),
                mock.patch.object(RUNNER.shutil, "copy2", side_effect=OSError("synthetic copy failure")),
            ):
                with self.assertRaisesRegex(OSError, "synthetic copy failure"):
                    RUNNER.run(options)
            self.assertFalse(output.exists())

    def test_owned_runner_failure_is_normalized_to_exact_exit_2(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            options = argparse.Namespace(
                out=Path(temporary) / "owned-output",
                mode="combined",
                protocol_sha256="f" * 64,
                phase="fixed-peer-key-ab-aa-v9",
            )

            def fail(owned: argparse.Namespace) -> int:
                owned.out.mkdir()
                RUNNER.set_stage("build_baseline")
                raise RuntimeError("synthetic build failure")

            with (
                mock.patch.object(RUNNER, "arguments", return_value=options),
                mock.patch.object(RUNNER, "run", side_effect=fail),
                mock.patch.object(RUNNER, "seal_failure") as seal,
                mock.patch("builtins.print"),
            ):
                self.assertEqual(RUNNER.main(), 2)
            seal.assert_called_once()
            self.assertIsInstance(seal.call_args.args[1], RuntimeError)

    def test_partial_failure_preserves_exact_prefix_and_fills_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            protocol_path, protocol = self.frozen_protocol(root)
            run, failure_path = self.failure_run(root, protocol)
            campaign = run / "campaign"
            planned = EXPORTER.expected_schedule()[0]
            stdout = campaign / "raw/benchmark-output" / f"{planned['run_id']}.txt"
            stderr = campaign / "raw/benchmark-stderr" / f"{planned['run_id']}.txt"
            metadata = campaign / "raw/run-metadata" / f"{planned['run_id']}.json"
            for path in (stdout, stderr, metadata):
                path.parent.mkdir(parents=True, exist_ok=True)
            stdout.write_bytes(benchmark_stdout(planned["case"]))
            stderr.write_bytes(b"")
            row = {
                **planned,
                "protocol_sha256": protocol["freeze"]["protocol_sha256"],
                "status": "completed",
                "exit_status": 0,
                "timed_out": False,
                "outer_wall_ns": 1_000,
                "parsed": CAMPAIGN_CORE.parse_output(stdout.read_bytes()),
                "rusage": {},
                "isolation": {"earned_level": "L2", "blocking": []},
                "started": "2026-11-02T00:00:00Z",
                "finished": "2026-11-02T00:00:01Z",
                "artifacts": {
                    "stdout": str(stdout.relative_to(campaign)),
                    "stdout_sha256": SHARED.sha256(stdout),
                    "stderr": str(stderr.relative_to(campaign)),
                    "stderr_sha256": SHARED.sha256(stderr),
                    "metadata": str(metadata.relative_to(campaign)),
                },
            }
            write_json(metadata, row)
            (campaign / "rows.jsonl").write_text(
                json.dumps(row, sort_keys=True) + "\n", encoding="utf-8"
            )
            output = campaign / "export.json"
            export = EXPORTER.produce_failure(
                run,
                protocol["freeze"]["protocol_sha256"],
                protocol["extensions"]["remote_execution"]["source"]["commit"],
                output,
                failure_path,
            )
            EXPORTER.validate(export, output)
            self.assertEqual(export["backend_record"]["usable_prefix_rows"], 1)
            self.assertEqual(export["runs"][0]["status"], "succeeded")
            self.assertTrue(all(row["status"] == "infra_error" for row in export["runs"][1:]))
            EXPORTER.write_once(output, export)
            pre_summary_files = [path for path in run.rglob("*") if path.is_file()]
            summary = {
                "schema": "go-coordinator-remote-summary/v1",
                "status": "mechanical_failure",
                "protocol_sha256": protocol["freeze"]["protocol_sha256"],
                "source_commit": protocol["extensions"]["remote_execution"]["source"]["commit"],
                "failure_path": "failure.json",
                "failure_sha256": SHARED.sha256(failure_path),
                "failure_stage": "build_baseline",
                "usable_prefix_rows": 1,
                "export_path": "campaign/export.json",
                "export_sha256": SHARED.sha256(output),
                "remote_returncode": 2,
                "claims_evaluated": False,
                "output_budget_bytes": 96_000_000,
                "output_bytes_before_summary": sum(path.stat().st_size for path in pre_summary_files),
                "output_files_before_summary": len(pre_summary_files),
                "remote_summary_reserve_bytes": 65_536,
            }
            write_json(run / "remote-summary.json", summary)
            verified = ANALYZER.verify_failure_export(
                run,
                protocol_path,
                protocol,
                summary,
                Path("/workspace/crypto-autoresearcher/tools/experiment_protocol.py"),
            )
            self.assertEqual(verified["usable_prefix_rows"], 1)
            tampered = json.loads(output.read_text())
            tampered["runs"][0]["status"] = "failed"
            write_json(output, tampered)
            summary["export_sha256"] = SHARED.sha256(output)
            summary["output_bytes_before_summary"] = sum(
                path.stat().st_size
                for path in run.rglob("*")
                if path.is_file() and path != run / "remote-summary.json"
            )
            write_json(run / "remote-summary.json", summary)
            with self.assertRaisesRegex(ValueError, "exact raw recomputation"):
                ANALYZER.verify_failure_export(
                    run,
                    protocol_path,
                    protocol,
                    summary,
                    Path("/workspace/crypto-autoresearcher/tools/experiment_protocol.py"),
                )

    def test_formal_analyzer_reaches_structured_inconclusive_before_row_loading(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run = root / ANALYZER.EXPECTED_OUTPUT
            (run / "campaign").mkdir(parents=True)
            protocol_path = root / "protocol.json"
            protocol = json.loads((GO_DIR / "protocol.v9.json").read_text())
            protocol["freeze"]["protocol_sha256"] = "f" * 64
            write_json(protocol_path, protocol)
            receipt_path = root / "receipt.json"
            write_json(
                receipt_path,
                {
                    "schema": "runpod.http-batch.receipt/v1",
                    "remote_status": {"timed_out": False, "returncode": 2},
                    "cleanup": {
                        "absence_verified": True,
                        "delete_requested": True,
                        "id": "pod",
                    },
                    "pod": {"id": "pod"},
                },
            )
            archive_path = root / "result.tar.gz"
            archive_path.write_bytes(b"fixture")
            write_json(run / "remote-summary.json", {"status": "mechanical_failure"})
            write_json(run / "campaign/export.json", {"flow": {"planned": 552}})
            options = argparse.Namespace(
                run=run,
                protocol=protocol_path,
                receipt=receipt_path,
                archive=archive_path,
                output=None,
                protocol_tool=Path(
                    "/workspace/crypto-autoresearcher/tools/experiment_protocol.py"
                ),
            )
            with (
                mock.patch.object(ANALYZER, "verify_frozen_protocol", return_value={"ok": True}),
                mock.patch.object(ANALYZER, "bind_verified_dependencies", return_value={}),
                mock.patch.object(ANALYZER, "verify_transport", return_value={"ok": True}),
                mock.patch.object(
                    SHARED,
                    "verify_archive",
                    return_value={"sha256": "a" * 64, "manifest_sha256": "b" * 64},
                ),
                mock.patch.object(
                    ANALYZER,
                    "verify_extracted_run",
                    return_value={"output": ANALYZER.EXPECTED_OUTPUT, "files": 3, "bytes": 3},
                ),
                mock.patch.object(
                    ANALYZER,
                    "verify_failure_export",
                    return_value={
                        "sha256": "c" * 64,
                        "failure_sha256": "d" * 64,
                        "usable_prefix_rows": 0,
                    },
                ),
                mock.patch.object(
                    ANALYZER,
                    "load_verified_rows",
                    side_effect=AssertionError("full-row loader must not run"),
                ),
            ):
                result = ANALYZER.analyze(options)
            self.assertEqual(result["verdict"]["overall"], "inconclusive")
            self.assertTrue(all(value == "not_evaluated" for value in result["claims"].values()))


class CampaignFailureTests(unittest.TestCase):
    def run_campaign(self, root: Path, *, fail_first: bool, restore_passes: bool):
        baseline = root / "baseline.test"
        candidate = root / "candidate.test"
        aa_left = root / "aa-left.test"
        aa_right = root / "aa-right.test"
        baseline.write_bytes(b"baseline")
        candidate.write_bytes(b"candidate")
        aa_left.write_bytes(baseline.read_bytes())
        aa_right.write_bytes(baseline.read_bytes())
        options = argparse.Namespace(
            out=root / "campaign",
            phase="fixed-peer-key-ab-aa-v9",
            protocol_sha256="f" * 64,
            baseline_binary=baseline,
            baseline_sha256=SHARED.sha256(baseline),
            candidate_binary=candidate,
            candidate_sha256=SHARED.sha256(candidate),
            aa_left_binary=aa_left,
            aa_left_sha256=SHARED.sha256(aa_left),
            aa_right_binary=aa_right,
            aa_right_sha256=SHARED.sha256(aa_right),
            warmups=3,
            replicates=20,
            cpu=2,
            reserved_cpus="2,18",
            expected_affinity=",".join(map(str, range(32))),
            timeout_seconds=10,
        )
        current_affinity = set(range(32))
        calls = 0

        def set_affinity(_pid, cpus):
            nonlocal current_affinity
            current_affinity = set(cpus)

        def measured(argv, _cpus, _env, stdout, stderr, _timeout, _reserved):
            nonlocal calls
            calls += 1
            if fail_first and calls == 1:
                raise RuntimeError("synthetic mid-row failure")
            case = argv[5].removeprefix("-test.bench=^").removesuffix("$")
            stdout.write_bytes(benchmark_stdout(case))
            stderr.write_bytes(b"")
            return valid_execution()

        restore = {
            "attempted": 0,
            "restored": 0,
            "exited": 0,
            "failures": 0 if restore_passes else 1,
            "passes": restore_passes,
            "records": [],
        }
        CAMPAIGN.ACTIVE_RESERVATION = None
        CAMPAIGN.ACTIVE_OUTPUT = None
        CAMPAIGN.ACTIVE_EXPECTED_AFFINITY = None
        with (
            mock.patch.object(CAMPAIGN, "arguments", return_value=options),
            mock.patch.object(CAMPAIGN.os, "sched_getaffinity", side_effect=lambda _pid: current_affinity),
            mock.patch.object(CAMPAIGN.os, "sched_setaffinity", side_effect=set_affinity),
            mock.patch.object(CAMPAIGN.shutil, "which", return_value="/usr/bin/taskset"),
            mock.patch.object(CAMPAIGN.l2_measure, "smt_siblings", return_value={2, 18}),
            mock.patch.object(CAMPAIGN.l2_measure, "quiet_preflight", return_value=valid_preflight()),
            mock.patch.object(CAMPAIGN.l2_measure, "evict", return_value={}),
            mock.patch.object(
                CAMPAIGN.l2_measure,
                "unmovable_on",
                return_value={"user_threads": [], "kernel_threads": []},
            ),
            mock.patch.object(CAMPAIGN.l2_measure, "run_measured", side_effect=measured),
            mock.patch.object(CAMPAIGN.l2_measure, "restore", return_value=copy.deepcopy(restore)),
            mock.patch.object(CAMPAIGN.common, "host", return_value={}),
            mock.patch("builtins.print"),
        ):
            return CAMPAIGN.campaign_main(), options.out

    def test_mid_row_exception_is_fsynced_as_attempt_and_campaign_continues(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            returncode, output = self.run_campaign(
                Path(temporary), fail_first=True, restore_passes=True
            )
            self.assertEqual(returncode, 1)
            rows = [json.loads(line) for line in (output / "rows.jsonl").read_text().splitlines()]
            self.assertEqual(len(rows), 552)
            self.assertEqual(rows[0]["status"], "not_completed")
            self.assertEqual(rows[0]["instrumentation_error"]["type"], "RuntimeError")
            summary = json.loads((output / "summary.json").read_text())
            self.assertEqual(summary["attempted"], 552)
            self.assertEqual(summary["failures"], 1)

    def test_restore_failure_is_sealed_and_only_invalidates_clocks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            returncode, output = self.run_campaign(
                Path(temporary), fail_first=False, restore_passes=False
            )
            self.assertEqual(returncode, 0)
            summary = json.loads((output / "summary.json").read_text())
            self.assertFalse(summary["restoration"]["passes"])
            self.assertEqual(summary["failures"], 0)


if __name__ == "__main__":
    unittest.main()
