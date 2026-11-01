#!/usr/bin/env python3
"""Preregistered deterministic analysis for the fixed-peer-key Go A/B study.

The interval calculation enumerates the exact empirical paired-bootstrap
median distribution.  It uses no pseudo-random generator or Monte Carlo draw.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from typing import Any


HERE = Path(__file__).resolve().parent
LEGACY_SPEC = importlib.util.spec_from_file_location(
    "go_remote_ab_shared", HERE / "analyze_remote_ab.py"
)
if LEGACY_SPEC is None or LEGACY_SPEC.loader is None:
    raise RuntimeError("cannot load shared Go A/B analysis primitives")
shared = importlib.util.module_from_spec(LEGACY_SPEC)
LEGACY_SPEC.loader.exec_module(shared)


SCHEMA = "go-coordinator-peer-key-ab-analysis/1"
BASELINE_ARM = "go-baseline"
CANDIDATE_ARM = "go-candidate"
EXPECTED_ROWS = 276
EXPECTED_PAIRS = 120
EXPECTED_REPLICATES = 20
ALLOCATION_THRESHOLD = Fraction(1, 20)
TIMING_THRESHOLD = Fraction(21, 20)
LOWER_QUANTILE = Fraction(1, 480)
EXPECTED_SOURCE_IDENTITIES = {
    "baseline_commit": "7c712913b7e912494e87c35e854cfd0129bad89c",
    "baseline_tree": "735e671e9492fb890a4e87825644c46bace88e4a",
    "baseline_coord_blob": "0d3f53806361e7442bc1d108c16b8b847f029918",
    "benchmark_commit": "050af6a5edbaccee4028574492597049a06cfd83",
    "benchmark_blob": "650f6a4a953d5adef537ce87aa3e114b432f32d7",
    "candidate_commit": "37b96362a53a7364dd4cc2a18f450a3627ec08d3",
    "candidate_parent": "7c712913b7e912494e87c35e854cfd0129bad89c",
    "candidate_tree": "5a2653198b943e93c9f7ae7906ad39d74baf7a79",
    "candidate_coord_blob": "edba225c5a1ff613d71a21aa8d2c528096831b6f",
    "candidate_merge_base": "7c712913b7e912494e87c35e854cfd0129bad89c",
}
EXPECTED_BENCHMARK_SHA256 = (
    "b13eafcc112ada81b104c3fde3ad51a75cb80e9a051f9644a66fc27d30218dbd"
)
EXPECTED_DIFF_SHA256 = (
    "e29818ed168eaa886dfdc4be3c90777b1026b89246b760fd76d31614f33e8417"
)
EXPECTED_COMMON_TEST = {
    "common_test_commit": "37b96362a53a7364dd4cc2a18f450a3627ec08d3",
    "common_test_blob": "b487d974638f5fe81a2921fa002b8ce481b956ad",
    "common_test_sha256": "4bf65f9fa27f46e04d287e8fc49ce33d00e9fb74e176a25677b04d9f883e35b8",
    "common_test_path": "bindings/go/coord_test.go",
}
EXPECTED_CPU_GUARD = {
    "flavor": "cpu3c",
    "no_gpu": True,
    "provider_memory_value": 64,
    "vcpu_count": 32,
}
EXPECTED_MEMORY_BYTES = 64_000_000_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def parse_pressure(text: Any) -> dict[str, dict[str, Fraction]]:
    if not isinstance(text, str):
        raise ValueError("PSI record is absent or not text")
    result: dict[str, dict[str, Fraction]] = {}
    for line in text.splitlines():
        fields = line.split()
        if not fields or fields[0] not in {"some", "full"}:
            raise ValueError(f"malformed PSI line: {line!r}")
        values: dict[str, Fraction] = {}
        for field in fields[1:]:
            key, separator, value = field.partition("=")
            if not separator or re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value) is None:
                raise ValueError(f"malformed PSI field: {field!r}")
            if key.startswith("avg"):
                values[key] = Fraction(value)
        if "avg10" not in values or fields[0] in result:
            raise ValueError(f"PSI avg10 is absent or duplicated: {line!r}")
        result[fields[0]] = values
    if set(result) != {"some", "full"}:
        raise ValueError("PSI record must contain exactly some and full lines")
    return result


def pressure_snapshot_passes(snapshot: dict[str, Any]) -> bool:
    cpu = parse_pressure(snapshot.get("psi_cpu"))
    memory = parse_pressure(snapshot.get("psi_memory"))
    return (
        cpu["some"]["avg10"] <= 10
        and cpu["full"]["avg10"] == 0
        and memory["some"]["avg10"] == 0
        and memory["full"]["avg10"] == 0
    )


def counter_map(text: Any) -> dict[str, int]:
    if not isinstance(text, str):
        raise ValueError("cgroup counter record is absent or not text")
    result: dict[str, int] = {}
    for line in text.splitlines():
        fields = line.split()
        if (
            len(fields) != 2
            or re.fullmatch(r"[A-Za-z0-9_.-]+", fields[0]) is None
            or re.fullmatch(r"[0-9]+", fields[1]) is None
            or fields[0] in result
        ):
            raise ValueError(f"malformed cgroup counter line: {line!r}")
        result[fields[0]] = int(fields[1])
    if not result:
        raise ValueError("empty cgroup counter record")
    return result


def counter_deltas(before: Any, after: Any) -> dict[str, int]:
    left = counter_map(before)
    right = counter_map(after)
    if set(left) != set(right):
        raise ValueError("cgroup counter inventory changed")
    deltas = {key: right[key] - left[key] for key in sorted(left)}
    if any(value < 0 for value in deltas.values()):
        raise ValueError("cgroup counter decreased")
    return deltas


def choose_verdict(
    *,
    complete: bool,
    correctness: bool,
    allocation: bool,
    timing_numeric: bool,
    timing_isolation: bool,
) -> str:
    """Apply the preregistered terminal order without data-dependent choices."""

    if not complete:
        return "inconclusive"
    if not correctness:
        return "wrong_answer"
    timing = timing_numeric and timing_isolation
    if allocation and timing:
        return "supported_within_scope"
    if allocation:
        return "allocation_only"
    if timing:
        return "timing_only"
    if not timing_isolation:
        return "invalid_measurement"
    return "unsupported"


def transport_is_complete(returncode: Any, mismatches: int) -> bool:
    """Accept the deliberate post-seal mismatch exit for wrong-answer reporting."""

    return returncode == 0 or mismatches > 0


def compute_case_results(
    rows: list[dict[str, Any]], cases: list[str]
) -> tuple[list[dict[str, Any]], bool, bool, int]:
    measured = [row for row in rows if not row["warmup"]]
    by_cell = {(row["case"], row["replicate"], row["arm"]): row for row in measured}
    matching_pairs = 0
    allocation_pass = True
    timing_pass = True
    results: list[dict[str, Any]] = []
    for case in cases:
        ratios: dict[str, list[Fraction]] = defaultdict(list)
        for replicate in range(1, EXPECTED_REPLICATES + 1):
            baseline = by_cell[(case, replicate, BASELINE_ARM)]["parsed"]
            candidate = by_cell[(case, replicate, CANDIDATE_ARM)]["parsed"]
            if baseline["fingerprints"] != candidate["fingerprints"]:
                raise ValueError("case analysis called before correctness passed")
            matching_pairs += 1
            left = baseline["metrics"]
            right = candidate["metrics"]
            for metric in ("B/op", "allocs/op"):
                ratios[metric].append(Fraction(right[metric], left[metric]))
            for metric in ("ns/op", "cpu-ns/op"):
                ratios[metric].append(Fraction(left[metric], right[metric]))

        metrics: dict[str, Any] = {}
        for metric in ("B/op", "allocs/op"):
            median = shared.median_fraction(ratios[metric])
            passes = median <= ALLOCATION_THRESHOLD
            allocation_pass = allocation_pass and passes
            metrics[metric] = {
                "direction": "candidate_over_baseline",
                "paired_median": shared.fraction_json(median),
                "threshold": shared.fraction_json(ALLOCATION_THRESHOLD),
                "passes": passes,
            }
        for metric in ("ns/op", "cpu-ns/op"):
            median = shared.median_fraction(ratios[metric])
            distribution = shared.exact_bootstrap_median_distribution(ratios[metric])
            lower = shared.exact_quantile(distribution, LOWER_QUANTILE)
            passes = median >= TIMING_THRESHOLD and lower > 1
            timing_pass = timing_pass and passes
            metrics[metric] = {
                "direction": "baseline_over_candidate",
                "paired_median": shared.fraction_json(median),
                "median_threshold": shared.fraction_json(TIMING_THRESHOLD),
                "simultaneous_lower_bound": shared.fraction_json(lower, decimals=15),
                "lower_quantile": "1/480",
                "bootstrap_support_points": len(distribution),
                "passes": passes,
            }
        results.append({"case": case, "pairs": EXPECTED_REPLICATES, "metrics": metrics})
    return results, allocation_pass, timing_pass, matching_pairs


def correctness_inventory(
    rows: list[dict[str, Any]], cases: list[str]
) -> tuple[int, int]:
    measured = [row for row in rows if not row["warmup"]]
    by_cell = {(row["case"], row["replicate"], row["arm"]): row for row in measured}
    matches = 0
    mismatches = 0
    for case in cases:
        for replicate in range(1, EXPECTED_REPLICATES + 1):
            baseline = by_cell[(case, replicate, BASELINE_ARM)]["parsed"]["fingerprints"]
            candidate = by_cell[(case, replicate, CANDIDATE_ARM)]["parsed"]["fingerprints"]
            if baseline == candidate:
                matches += 1
            else:
                mismatches += 1
    return matches, mismatches


def verify_tests(run: Path, protocol_sha256: str) -> dict[str, Any]:
    path = run / "tests" / "manifest.json"
    manifest = shared.load_json(path)
    if manifest != {
        "schema": "go-coordinator-remote-tests/v1",
        "protocol_sha256": protocol_sha256,
        "arms": manifest.get("arms"),
    }:
        raise ValueError("test manifest top-level contract mismatch")
    arms = manifest["arms"]
    if set(arms) != {BASELINE_ARM, CANDIDATE_ARM}:
        raise ValueError("test manifest arm inventory mismatch")
    for arm, record in arms.items():
        if record["exit_status"] != 0 or record["command"][-2:] != ["test", "./..."]:
            raise ValueError(f"correctness tests did not pass for {arm}")
        log = run / "tests" / record["log"]
        if (
            not log.is_file()
            or log.stat().st_size != record["log_bytes"]
            or shared.sha256(log) != record["log_sha256"]
        ):
            raise ValueError(f"correctness test log binding mismatch for {arm}")
    return {"manifest_sha256": shared.sha256(path), "arms": arms}


def verify_build(
    run: Path, protocol: dict[str, Any], campaign_arms: dict[str, Any]
) -> dict[str, Any]:
    path = run / "build" / "manifest.json"
    manifest = shared.load_json(path)
    if manifest.get("schema") != "go-coordinator-remote-build/v1" or manifest.get("mode") != "combined":
        raise ValueError("build manifest is not the preregistered combined mode")
    if manifest.get("expected_cpu_flavor") != "cpu3c":
        raise ValueError("build manifest CPU flavor mismatch")
    sources = manifest.get("sources", {})
    for key, expected in EXPECTED_SOURCE_IDENTITIES.items():
        if sources.get(key) != expected:
            raise ValueError(f"build source identity mismatch: {key}")
    if sources.get("benchmark_sha256") != EXPECTED_BENCHMARK_SHA256:
        raise ValueError("benchmark source SHA-256 mismatch")
    if sources.get("candidate_diff_sha256") != EXPECTED_DIFF_SHA256:
        raise ValueError("candidate diff SHA-256 mismatch")
    for key, expected in EXPECTED_COMMON_TEST.items():
        if sources.get(key) != expected:
            raise ValueError(f"common correctness-test identity mismatch: {key}")
    if sources.get("only_changed_path") != "bindings/go/coord.go":
        raise ValueError("synthetic arms differ outside coord.go")
    if manifest.get("toolchain", {}).get("go_version") != "go version go1.27.3 linux/amd64":
        raise ValueError("Go toolchain identity mismatch")
    runner = manifest.get("runner", {})
    links = protocol["links"]
    if runner != {
        "engine": links["remote_runner"],
        "engine_sha256": links["remote_runner_sha256"],
        "binding": links["remote_binding"],
        "binding_sha256": links["remote_binding_sha256"],
    }:
        raise ValueError("runner or constant-binding wrapper mismatch")
    if manifest.get("runner_sha256") != links["remote_runner_sha256"]:
        raise ValueError("legacy runner SHA-256 field mismatch")
    if set(manifest.get("arms", {})) != {BASELINE_ARM, CANDIDATE_ARM}:
        raise ValueError("build arm inventory mismatch")
    for arm in (BASELINE_ARM, CANDIDATE_ARM):
        if manifest["arms"][arm]["binary_sha256"] != campaign_arms[arm]["sha256"]:
            raise ValueError(f"build/campaign binary mismatch: {arm}")
    return {"manifest_sha256": shared.sha256(path), "manifest": manifest}


def verify_transport(receipt: dict[str, Any], protocol: dict[str, Any]) -> dict[str, Any]:
    planned = protocol["extensions"]["remote_execution"]
    token = planned["protocol_hash_token"]
    template = planned["command_template"]
    if template.count(token) != 1:
        raise ValueError("remote command template must contain one protocol-hash token")
    expected_command = template.replace(token, protocol["freeze"]["protocol_sha256"])
    command_sha256 = hashlib.sha256(expected_command.encode("utf-8")).hexdigest()
    if receipt.get("command") != expected_command:
        raise ValueError("transport command differs from frozen template")
    if receipt.get("command_sha256") != command_sha256:
        raise ValueError("transport command SHA-256 mismatch")
    if receipt.get("outputs") != [planned["output"]]:
        raise ValueError("transport output inventory mismatch")
    if receipt.get("provider_actions") is not True:
        raise ValueError("transport did not record the single provider action path")
    if receipt.get("transport") != planned["transport"]:
        raise ValueError("transport mechanism mismatch")

    source = receipt.get("source", {})
    for key in ("origin", "ref", "commit", "tree"):
        if source.get(key) != planned["source"][key]:
            raise ValueError(f"transport source identity mismatch: {key}")
    if source.get("public_ref_checked") is not True:
        raise ValueError("transport did not verify the dedicated public source ref")
    archive_sha = source.get("archive_sha256")
    if not isinstance(archive_sha, str) or re.fullmatch(r"[0-9a-f]{64}", archive_sha) is None:
        raise ValueError("source archive SHA-256 is malformed")

    request = receipt.get("request", {})
    expected_request = {
        "cloudType": "SECURE",
        "computeType": "CPU",
        "containerDiskInGb": planned["container_disk_gb"],
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
        "startup_sha256": request.get("startup_sha256"),
        "vcpuCount": 32,
        "name": request.get("name"),
    }
    if request != expected_request:
        raise ValueError("RunPod request differs from frozen CPU request")
    if re.fullmatch(r"[0-9a-f]{64}", request.get("startup_sha256", "")) is None:
        raise ValueError("RunPod startup identity is malformed")
    name = request.get("name")
    if not isinstance(name, str) or not name.startswith(planned["pod_name_prefix"]):
        raise ValueError("RunPod job name prefix mismatch")

    pod = receipt.get("pod", {})
    if (
        pod.get("name") != name
        or pod.get("cloud") != "SECURE"
        or pod.get("cpu") != {"id": "cpu3c", "memory": 64, "vcpuCount": 32}
        or pod.get("image") != planned["image"]
        or pod.get("gpu") is not None
        or pod.get("cudaVersion") is not None
        or pod.get("creation_response_ambiguous") is not False
        or not isinstance(pod.get("cost"), (int, float))
        or pod["cost"] > planned["max_price_usd_per_hour"]
        or not isinstance(pod.get("id"), str)
        or not pod["id"]
    ):
        raise ValueError("observed RunPod placement differs from frozen request")

    remote = receipt.get("remote_status", {})
    if (
        remote.get("command_sha256") != command_sha256
        or remote.get("source_archive_sha256") != archive_sha
        or remote.get("source_commit") != planned["source"]["commit"]
        or remote.get("source_tree") != planned["source"]["tree"]
        or remote.get("job_id") != name
        or remote.get("hardware", {}).get("pod_id") != pod["id"]
        or remote.get("hardware", {}).get("gpus") != []
    ):
        raise ValueError("remote worker source/command/hardware binding mismatch")
    return {
        "pod_id": pod["id"],
        "pod_name": name,
        "source_commit": source["commit"],
        "source_tree": source["tree"],
        "source_archive_sha256": archive_sha,
        "command_sha256": command_sha256,
        "provider_actions": receipt["provider_actions"],
        "output": planned["output"],
    }


def verify_isolation(
    rows: list[dict[str, Any]],
    isolation: dict[str, Any],
    receipt: dict[str, Any],
    build_manifest: dict[str, Any],
) -> dict[str, Any]:
    if receipt.get("cpu_guard") != EXPECTED_CPU_GUARD:
        raise ValueError("transport CPU placement mismatch")
    placement = isolation["placement"]
    initial = build_manifest["host"]
    allowed = placement["allowed_cpus"]
    exact_placement = (
        build_manifest["placement"] == placement
        and len(allowed) == 32
        and len(set(allowed)) == 32
        and placement["memory_limit_bytes"] == EXPECTED_MEMORY_BYTES
        and len(placement["benchmark_cpus"]) == 1
        and placement["benchmark_cpus"][0] == placement["topology_order"][0]
        and initial["affinity"]
        == isolation["before"]["affinity"]
        == isolation["after"]["affinity"]
        == allowed
        and initial["topology_order"]
        == isolation["before"]["topology_order"]
        == isolation["after"]["topology_order"]
        == placement["topology_order"]
        and initial["cpuinfo_sha256"]
        == isolation["before"]["cpuinfo_sha256"]
        == isolation["after"]["cpuinfo_sha256"]
        and initial["cpu_model"]
        == isolation["before"]["cpu_model"]
        == isolation["after"]["cpu_model"]
        and initial["cpuset_cpus"]
        == isolation["before"]["cpuset_cpus"]
        == isolation["after"]["cpuset_cpus"]
        and initial["memory_max"]
        == isolation["before"]["memory_max"]
        == isolation["after"]["memory_max"]
        == str(EXPECTED_MEMORY_BYTES)
        and initial["nvidia_devices"]
        == isolation["before"]["nvidia_devices"]
        == isolation["after"]["nvidia_devices"]
        == []
    )
    row_steal_failures = 0
    row_affinity_failures = 0
    row_pressure_failures = 0
    for row in rows:
        before = row["host_before"]
        after = row["host_after"]
        row_steal_failures += int(
            not isinstance(before.get("steal_ticks"), int)
            or not isinstance(after.get("steal_ticks"), int)
            or before["steal_ticks"] != after["steal_ticks"]
        )
        row_affinity_failures += int(
            row.get("expected_affinity") != allowed
            or before.get("self_affinity") != allowed
            or after.get("self_affinity") != allowed
        )
        for snapshot in (before, after):
            try:
                passes = pressure_snapshot_passes(snapshot)
            except ValueError:
                passes = False
            row_pressure_failures += int(not passes)
    cpu_deltas = counter_deltas(
        isolation["before"]["cpu_stat"], isolation["after"]["cpu_stat"]
    )
    memory_deltas = counter_deltas(
        isolation["before"]["memory_events"], isolation["after"]["memory_events"]
    )
    throttle_delta = cpu_deltas.get("nr_throttled")
    global_steal_zero = (
        isinstance(isolation["before"].get("steal_ticks"), int)
        and isolation["before"]["steal_ticks"] == isolation["after"].get("steal_ticks")
    )
    passes = (
        exact_placement
        and global_steal_zero
        and row_steal_failures == 0
        and row_affinity_failures == 0
        and row_pressure_failures == 0
        and throttle_delta == 0
        and all(delta == 0 for delta in memory_deltas.values())
    )
    reported = {
        "rows": len(rows),
        "row_pressure_observations": len(rows) * 2,
        "rows_with_nonzero_steal_delta": row_steal_failures,
        "rows_with_affinity_change": row_affinity_failures,
        "pressure_observations_failing_numeric_gate": row_pressure_failures,
        "cgroup_nr_throttled_delta": throttle_delta,
        "memory_event_deltas": memory_deltas,
        "placement_unchanged": exact_placement,
        "timing_valid": passes and isolation.get("fingerprint_pair_mismatches") == 0,
    }
    for key, value in reported.items():
        if isolation.get(key) != value:
            raise ValueError(f"runner isolation field disagrees with analyzer: {key}")
    return {
        "passes": passes,
        "exact_placement": exact_placement,
        "provider_cpu_guard": receipt["cpu_guard"],
        "global_steal_zero": global_steal_zero,
        "row_steal_failures": row_steal_failures,
        "row_affinity_failures": row_affinity_failures,
        "row_pressure_observations": len(rows) * 2,
        "row_pressure_failures": row_pressure_failures,
        "cgroup_nr_throttled_delta": throttle_delta,
        "memory_event_deltas": memory_deltas,
    }


def analyze(options: argparse.Namespace) -> dict[str, Any]:
    run = options.run.resolve()
    protocol_path = options.protocol.resolve()
    receipt_path = options.receipt.resolve()
    archive_path = options.archive.resolve()
    protocol = shared.load_json(protocol_path)
    receipt = shared.load_json(receipt_path)
    if protocol.get("freeze", {}).get("status") != "frozen":
        raise ValueError("protocol is not frozen")
    protocol_sha256 = protocol["freeze"]["protocol_sha256"]
    if protocol["analysis_plan"]["script"] != Path(__file__).name:
        raise ValueError("protocol analysis script path mismatch")
    if protocol["analysis_plan"]["script_sha256"] != shared.sha256(Path(__file__).resolve()):
        raise ValueError("protocol analysis script SHA-256 mismatch")
    if receipt.get("schema") != "runpod.http-batch.receipt/v1":
        raise ValueError("unexpected transport receipt schema")
    if receipt.get("remote_status", {}).get("timed_out"):
        raise ValueError("remote job timed out")
    if receipt.get("cleanup") != {
        "absence_verified": True,
        "delete_requested": True,
        "id": receipt.get("pod", {}).get("id"),
    }:
        raise ValueError("transport cleanup binding is incomplete")
    transport = verify_transport(receipt, protocol)
    archive = shared.verify_archive(archive_path, receipt)
    rows, inventory = shared.verify_rows(run, protocol)
    tests = verify_tests(run, protocol_sha256)
    build = verify_build(run, protocol, inventory["arms"])
    isolation_path = run / "isolation.json"
    summary_path = run / "remote-summary.json"
    isolation_record = shared.load_json(isolation_path)
    summary = shared.load_json(summary_path)
    expected_summary_hashes = {
        "build_manifest_sha256": build["manifest_sha256"],
        "tests_manifest_sha256": tests["manifest_sha256"],
        "campaign_rows_sha256": inventory["rows_sha256"],
        "isolation_sha256": shared.sha256(isolation_path),
    }
    if summary.get("protocol_sha256") != protocol_sha256:
        raise ValueError("remote summary protocol SHA-256 mismatch")
    for key, value in expected_summary_hashes.items():
        if summary.get(key) != value:
            raise ValueError(f"remote summary {key} mismatch")

    matches, mismatches = correctness_inventory(rows, inventory["cases"])
    correctness = mismatches == 0 and matches == EXPECTED_PAIRS
    if summary.get("fingerprint_pair_mismatches") != mismatches:
        raise ValueError("remote summary correctness count mismatch")
    isolation = verify_isolation(rows, isolation_record, receipt, build["manifest"])
    if summary.get("timing_valid") != (isolation["passes"] and correctness):
        raise ValueError("remote summary timing-valid field mismatch")

    remote_returncode = receipt["remote_status"]["returncode"]
    # A complete cross-arm mismatch is a scientific wrong answer even when the
    # runner deliberately exits nonzero after sealing all rows and manifests.
    transport_complete = transport_is_complete(remote_returncode, mismatches)
    cases: list[dict[str, Any]] = []
    allocation_pass = False
    timing_numeric_pass = False
    analyzed_pairs = 0
    if correctness and transport_complete:
        cases, allocation_pass, timing_numeric_pass, analyzed_pairs = compute_case_results(
            rows, inventory["cases"]
        )
    verdict = choose_verdict(
        complete=transport_complete and len(rows) == EXPECTED_ROWS,
        correctness=correctness,
        allocation=allocation_pass,
        timing_numeric=timing_numeric_pass,
        timing_isolation=isolation["passes"],
    )
    return {
        "schema": SCHEMA,
        "protocol_sha256": protocol_sha256,
        "analysis": {
            "script": protocol["analysis_plan"]["script"],
            "script_sha256": shared.sha256(Path(__file__).resolve()),
            "status": "preregistered_deterministic",
        },
        "inputs": {
            "protocol_file_sha256": shared.sha256(protocol_path),
            "receipt_sha256": shared.sha256(receipt_path),
            "archive_sha256": archive["sha256"],
            "archive_manifest_sha256": archive["manifest_sha256"],
            "build_manifest_sha256": build["manifest_sha256"],
            "tests_manifest_sha256": tests["manifest_sha256"],
            "rows_sha256": inventory["rows_sha256"],
            "isolation_sha256": shared.sha256(isolation_path),
            "remote_summary_sha256": shared.sha256(summary_path),
        },
        "transport": transport,
        "flow": {
            "planned": EXPECTED_ROWS,
            "completed": len(rows),
            "warmups": len(inventory["warmups"]),
            "measured": len(inventory["measured"]),
            "matching_pairs": matches,
            "mismatching_pairs": mismatches,
            "analyzed_pairs": analyzed_pairs,
            "remote_returncode": remote_returncode,
        },
        "correctness": {
            "passes": correctness,
            "rule": "all 120 measured baseline/candidate fingerprint pairs are exactly equal",
        },
        "isolation": isolation,
        "inference": {
            "method": "exact_empirical_paired_bootstrap_median_distribution",
            "pairs_per_case": EXPECTED_REPLICATES,
            "statistic": "average_of_bootstrap_order_statistics_10_and_11",
            "distribution": "exhaustive_joint_order_statistic_distribution",
            "probability_arithmetic": "exact_rational",
            "rng": None,
            "monte_carlo_draws": None,
            "family_alpha": "1/20",
            "timing_tests": 12,
            "correction": "two_sided_bonferroni",
            "lower_quantile": "1/480",
            "quantile_definition": "inf{x: CDF(x) >= 1/480}",
        },
        "cases": cases,
        "claims": {
            "C-ab-correct": "supported" if correctness else "wrong_answer",
            "C-ab-allocation": "supported" if correctness and allocation_pass else "unsupported",
            "C-ab-timing": (
                "supported"
                if correctness and timing_numeric_pass and isolation["passes"]
                else "invalid_measurement"
                if correctness and not isolation["passes"]
                else "unsupported"
            ),
        },
        "verdict": {
            "overall": verdict,
            "allocation_gate_passes": allocation_pass,
            "timing_numeric_gate_passes": timing_numeric_pass,
            "timing_isolation_gate_passes": isolation["passes"],
        },
    }


def main() -> int:
    options = parse_args()
    result = analyze(options)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if options.output:
        options.output.parent.mkdir(parents=True, exist_ok=True)
        options.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
