#!/usr/bin/env python3
"""Verify and analyze the retained Go coordinator remote A/B campaign.

This analyzer was written after the v7 rows existed.  Its bootstrap output is
therefore a deterministic sensitivity analysis, not the canonical analysis
that v7 failed to preregister.  It intentionally uses only the Python standard
library and exact rational arithmetic.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import statistics
import tarfile
from typing import Any, Iterable


SCHEMA = "go-coordinator-ab-analysis/1"
BASELINE_ARM = "go-baseline"
CANDIDATE_ARM = "go-candidate"
EXPECTED_ROWS = 276
EXPECTED_WARMUPS = 36
EXPECTED_MEASURED = 240
EXPECTED_PAIRS = 120
EXPECTED_REPLICATES = 20
EXPECTED_WARMUP_REPLICATES = 3
EXPECTED_ITERATIONS = 100
ALLOCATION_THRESHOLD = Fraction(1, 20)
TIMING_THRESHOLD = Fraction(21, 20)
FAMILY_ALPHA = Fraction(1, 20)
TIMING_TESTS = 12
# A two-sided Bonferroni lower percentile.  Passing this stricter family bound
# is sufficient for the requested Holm family gate under a percentile-
# bootstrap interpretation.
BONFERRONI_LOWER_QUANTILE = FAMILY_ALPHA / (2 * TIMING_TESTS)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def safe_member_name(name: str) -> None:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or not name:
        raise ValueError(f"unsafe archive member: {name!r}")


def parse_hash_manifest(data: bytes) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in data.decode("utf-8").splitlines():
        digest, separator, name = line.partition("  ")
        if separator != "  " or len(digest) != 64 or any(
            char not in "0123456789abcdef" for char in digest
        ):
            raise ValueError(f"malformed archive hash line: {line!r}")
        safe_member_name(name)
        if name in result:
            raise ValueError(f"duplicate archive hash entry: {name}")
        result[name] = digest
    return result


def verify_archive(archive: Path, receipt: dict[str, Any]) -> dict[str, Any]:
    archive_sha = sha256(archive)
    remote_archive = receipt["remote_status"]["archive"]
    result = receipt["result"]
    if archive_sha != remote_archive["sha256"] or archive_sha != result["archive_sha256"]:
        raise ValueError("result archive SHA-256 mismatch")
    if archive.stat().st_size != remote_archive["bytes"] or archive.stat().st_size != result["archive_bytes"]:
        raise ValueError("result archive byte-count mismatch")

    with tarfile.open(archive, "r:gz") as bundle:
        members = bundle.getmembers()
        if len(members) != remote_archive["files"]:
            raise ValueError("archive member count mismatch")
        by_name: dict[str, tarfile.TarInfo] = {}
        for member in members:
            safe_member_name(member.name)
            if not member.isfile():
                raise ValueError(f"non-regular archive member: {member.name}")
            if member.name in by_name:
                raise ValueError(f"duplicate archive member: {member.name}")
            by_name[member.name] = member

        manifest_name = ".runpod-batch/files.sha256"
        manifest_member = by_name.get(manifest_name)
        if manifest_member is None:
            raise ValueError("archive hash manifest is absent")
        manifest_stream = bundle.extractfile(manifest_member)
        if manifest_stream is None:
            raise ValueError("archive hash manifest is unreadable")
        manifest_data = manifest_stream.read()
        manifest_sha = sha256_bytes(manifest_data)
        if manifest_sha != remote_archive["manifest_sha256"]:
            raise ValueError("archive hash manifest SHA-256 mismatch")
        expected = parse_hash_manifest(manifest_data)
        if set(expected) != set(by_name) - {manifest_name}:
            raise ValueError("archive hash manifest inventory mismatch")

        receipt_files = {item["path"]: item for item in result["files"]}
        if set(receipt_files) != set(expected):
            raise ValueError("receipt file inventory mismatch")
        for name, expected_sha in expected.items():
            member = by_name[name]
            stream = bundle.extractfile(member)
            if stream is None:
                raise ValueError(f"archive member is unreadable: {name}")
            digest = hashlib.sha256()
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
            if digest.hexdigest() != expected_sha:
                raise ValueError(f"archive member SHA-256 mismatch: {name}")
            receipt_item = receipt_files[name]
            if receipt_item["sha256"] != expected_sha or receipt_item["bytes"] != member.size:
                raise ValueError(f"receipt member binding mismatch: {name}")

    return {
        "sha256": archive_sha,
        "bytes": archive.stat().st_size,
        "members": len(members),
        "manifest_sha256": manifest_sha,
        "manifest_entries": len(expected),
    }


def fraction_json(value: Fraction, decimals: int = 12) -> dict[str, str]:
    return {
        "decimal": f"{float(value):.{decimals}f}",
        "numerator": str(value.numerator),
        "denominator": str(value.denominator),
    }


def median_fraction(values: Iterable[Fraction]) -> Fraction:
    items = list(values)
    if not items:
        raise ValueError("cannot take the median of an empty collection")
    return statistics.median(items)


def _joint_order_cdf_count(i: int, j: int, categories: int = 20, draws: int = 20) -> int:
    """Count sequences where order statistics 10 and 11 are <= i and <= j."""

    if i < 0 or j < 0:
        return 0
    if i >= categories:
        i = categories - 1
    if j >= categories:
        j = categories - 1
    if i > j:
        # X_(11) <= v_j implies X_(10) <= v_i.
        choices_low = j + 1
        choices_high = categories - choices_low
        return sum(
            math.comb(draws, count)
            * choices_low**count
            * choices_high ** (draws - count)
            for count in range(11, draws + 1)
        )

    choices_a = i + 1
    choices_b = j - i
    choices_c = categories - 1 - j
    total = 0
    for count_a in range(10, draws + 1):
        for count_b in range(max(0, 11 - count_a), draws - count_a + 1):
            count_c = draws - count_a - count_b
            sequences = math.comb(draws, count_a) * math.comb(
                draws - count_a, count_b
            )
            total += (
                sequences
                * choices_a**count_a
                * choices_b**count_b
                * choices_c**count_c
            )
    return total


def exact_bootstrap_median_distribution(values: list[Fraction]) -> dict[Fraction, int]:
    """Return the exact empirical bootstrap distribution of a 20-pair median.

    Twenty observations are sampled with replacement from the 20 sorted input
    ratios.  The statistic is the average of one-indexed order statistics 10
    and 11.  Counts have common denominator ``20**20``.
    """

    if len(values) != 20:
        raise ValueError(f"expected 20 paired ratios, got {len(values)}")
    ordered = sorted(values)
    support: dict[Fraction, int] = defaultdict(int)
    for i in range(20):
        for j in range(20):
            mass = (
                _joint_order_cdf_count(i, j)
                - _joint_order_cdf_count(i - 1, j)
                - _joint_order_cdf_count(i, j - 1)
                + _joint_order_cdf_count(i - 1, j - 1)
            )
            if mass < 0:
                raise AssertionError("negative order-statistic mass")
            if mass:
                if i > j:
                    raise AssertionError("order-statistic support is reversed")
                support[(ordered[i] + ordered[j]) / 2] += mass
    if sum(support.values()) != 20**20:
        raise AssertionError("bootstrap distribution does not sum to one")
    return dict(support)


def exact_quantile(distribution: dict[Fraction, int], q: Fraction) -> Fraction:
    if not 0 <= q <= 1:
        raise ValueError(f"invalid quantile: {q}")
    total = sum(distribution.values())
    cumulative = 0
    for value in sorted(distribution):
        cumulative += distribution[value]
        if cumulative * q.denominator >= total * q.numerator:
            return value
    return max(distribution)


def parse_memory_events(text: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for line in text.splitlines():
        key, value = line.split()
        result[key] = int(value)
    return result


def verify_rows(run: Path, protocol: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    campaign = run / "campaign"
    rows_path = campaign / "rows.jsonl"
    rows = [json.loads(line) for line in rows_path.read_text(encoding="utf-8").splitlines() if line]
    manifest = load_json(campaign / "manifest.json")
    summary = load_json(campaign / "summary.json")
    protocol_sha = protocol["freeze"]["protocol_sha256"]
    if len(rows) != EXPECTED_ROWS:
        raise ValueError(f"expected {EXPECTED_ROWS} rows, got {len(rows)}")
    if [row["sequence"] for row in rows] != list(range(1, EXPECTED_ROWS + 1)):
        raise ValueError("row sequence is not exact and contiguous")
    if manifest["protocol_sha256"] != protocol_sha or summary["protocol_sha256"] != protocol_sha:
        raise ValueError("campaign protocol SHA-256 mismatch")
    if any(row["protocol_sha256"] != protocol_sha for row in rows):
        raise ValueError("row protocol SHA-256 mismatch")
    if summary["planned"] != EXPECTED_ROWS or summary["attempted"] != EXPECTED_ROWS or summary["failures"] != 0:
        raise ValueError("campaign summary flow mismatch")
    if summary["rows_sha256"] != sha256(rows_path):
        raise ValueError("campaign rows SHA-256 mismatch")
    if any(row["status"] != "completed" or row["outcome_class"] != "verified" for row in rows):
        raise ValueError("campaign contains a failed or unverified row")
    if any(row["exit_status"] != 0 or row["timed_out"] for row in rows):
        raise ValueError("campaign contains a nonzero or timed-out row")
    if any(row["parsed"]["iterations"] != EXPECTED_ITERATIONS for row in rows):
        raise ValueError("campaign contains a non-100x row")

    warmups = [row for row in rows if row["warmup"]]
    measured = [row for row in rows if not row["warmup"]]
    if len(warmups) != EXPECTED_WARMUPS or len(measured) != EXPECTED_MEASURED:
        raise ValueError("campaign warmup/measured inventory mismatch")
    cases = manifest["cases"]
    if len(cases) != 6 or len(set(cases)) != 6:
        raise ValueError("campaign case inventory mismatch")
    arm_records = {arm["id"]: arm for arm in manifest["arms"]}
    if set(arm_records) != {BASELINE_ARM, CANDIDATE_ARM}:
        raise ValueError("campaign arm inventory mismatch")

    seen: set[tuple[str, bool, int, str]] = set()
    by_pair: dict[tuple[str, bool, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (row["case"], row["warmup"], row["replicate"], row["arm"])
        if key in seen:
            raise ValueError(f"duplicate row cell: {key}")
        seen.add(key)
        by_pair[key[:3]].append(row)
        if row["case"] not in cases or row["arm"] not in arm_records:
            raise ValueError("row has an unknown case or arm")
        if row["binary_sha256"] != arm_records[row["arm"]]["sha256"]:
            raise ValueError("row binary SHA-256 mismatch")
        for kind in ("stdout", "stderr", "metadata"):
            artifact = run / "campaign" / row["artifacts"][kind]
            if not artifact.is_file():
                raise ValueError(f"row artifact is absent: {artifact}")
            hash_key = f"{kind}_sha256"
            if hash_key in row["artifacts"] and sha256(artifact) != row["artifacts"][hash_key]:
                raise ValueError(f"row artifact SHA-256 mismatch: {artifact}")

    for case in cases:
        for warmup, count in ((True, EXPECTED_WARMUP_REPLICATES), (False, EXPECTED_REPLICATES)):
            for replicate in range(1, count + 1):
                pair = by_pair.get((case, warmup, replicate), [])
                if len(pair) != 2 or {row["arm"] for row in pair} != {BASELINE_ARM, CANDIDATE_ARM}:
                    raise ValueError("campaign pair inventory mismatch")
                ordered = sorted(pair, key=lambda row: row["order_position"])
                expected_first = BASELINE_ARM if replicate % 2 else CANDIDATE_ARM
                if [row["order_position"] for row in ordered] != [1, 2] or ordered[0]["arm"] != expected_first:
                    raise ValueError("campaign mirrored order mismatch")

    return rows, {
        "rows_sha256": sha256(rows_path),
        "campaign_manifest_sha256": sha256(campaign / "manifest.json"),
        "campaign_summary_sha256": sha256(campaign / "summary.json"),
        "cases": cases,
        "arms": arm_records,
        "warmups": warmups,
        "measured": measured,
    }


def analyze(options: argparse.Namespace) -> dict[str, Any]:
    run = options.run.resolve()
    protocol_path = options.protocol.resolve()
    receipt_path = options.receipt.resolve()
    archive_path = options.archive.resolve()
    protocol = load_json(protocol_path)
    receipt = load_json(receipt_path)
    if protocol["freeze"]["status"] != "frozen":
        raise ValueError("protocol is not frozen")
    if receipt["schema"] != "runpod.http-batch.receipt/v1":
        raise ValueError("unexpected transport receipt schema")
    if receipt["remote_status"]["returncode"] != 0 or receipt["remote_status"]["timed_out"]:
        raise ValueError("remote job did not complete successfully")
    if receipt["cleanup"] != {
        "absence_verified": True,
        "delete_requested": True,
        "id": receipt["pod"]["id"],
    }:
        raise ValueError("transport cleanup binding is incomplete")
    if receipt["cpu_guard"] != {
        "flavor": "cpu3c",
        "no_gpu": True,
        "provider_memory_value": 64,
        "vcpu_count": 32,
    }:
        raise ValueError("transport CPU placement mismatch")
    archive = verify_archive(archive_path, receipt)
    rows, inventory = verify_rows(run, protocol)
    build_manifest_path = run / "build" / "manifest.json"
    isolation_path = run / "isolation.json"
    remote_summary_path = run / "remote-summary.json"
    isolation = load_json(isolation_path)
    remote_summary = load_json(remote_summary_path)
    if remote_summary["protocol_sha256"] != protocol["freeze"]["protocol_sha256"]:
        raise ValueError("remote summary protocol SHA-256 mismatch")
    for key, path in (
        ("build_manifest_sha256", build_manifest_path),
        ("campaign_rows_sha256", run / "campaign" / "rows.jsonl"),
        ("isolation_sha256", isolation_path),
    ):
        if remote_summary[key] != sha256(path):
            raise ValueError(f"remote summary {key} mismatch")
    if remote_summary["fingerprint_pair_mismatches"] != 0:
        raise ValueError("remote summary records a fingerprint mismatch")

    measured = inventory["measured"]
    pair_index = {
        (row["case"], row["replicate"], row["arm"]): row for row in measured
    }
    matching_pairs = 0
    case_results: list[dict[str, Any]] = []
    all_numeric_timing_pass = True
    allocation_pass = True
    for case in inventory["cases"]:
        ratios: dict[str, list[Fraction]] = {
            "B/op": [],
            "allocs/op": [],
            "ns/op": [],
            "cpu-ns/op": [],
        }
        for replicate in range(1, EXPECTED_REPLICATES + 1):
            baseline = pair_index[(case, replicate, BASELINE_ARM)]["parsed"]
            candidate = pair_index[(case, replicate, CANDIDATE_ARM)]["parsed"]
            if baseline["fingerprints"] != candidate["fingerprints"]:
                raise ValueError(f"fingerprint mismatch: {case} replicate {replicate}")
            matching_pairs += 1
            base_metrics = baseline["metrics"]
            candidate_metrics = candidate["metrics"]
            ratios["B/op"].append(Fraction(candidate_metrics["B/op"], base_metrics["B/op"]))
            ratios["allocs/op"].append(
                Fraction(candidate_metrics["allocs/op"], base_metrics["allocs/op"])
            )
            ratios["ns/op"].append(Fraction(base_metrics["ns/op"], candidate_metrics["ns/op"]))
            ratios["cpu-ns/op"].append(
                Fraction(base_metrics["cpu-ns/op"], candidate_metrics["cpu-ns/op"])
            )

        metrics: dict[str, Any] = {}
        for metric in ("B/op", "allocs/op"):
            median = median_fraction(ratios[metric])
            passes = median <= ALLOCATION_THRESHOLD
            allocation_pass = allocation_pass and passes
            metrics[metric] = {
                "direction": "candidate_over_baseline",
                "median_ratio": fraction_json(median),
                "minimum_ratio": fraction_json(min(ratios[metric])),
                "maximum_ratio": fraction_json(max(ratios[metric])),
                "threshold": fraction_json(ALLOCATION_THRESHOLD),
                "passes": passes,
            }
        for metric in ("ns/op", "cpu-ns/op"):
            median = median_fraction(ratios[metric])
            distribution = exact_bootstrap_median_distribution(ratios[metric])
            lower = exact_quantile(distribution, BONFERRONI_LOWER_QUANTILE)
            passes = median >= TIMING_THRESHOLD and lower > 1
            all_numeric_timing_pass = all_numeric_timing_pass and passes
            metrics[metric] = {
                "direction": "baseline_over_candidate",
                "median_ratio": fraction_json(median),
                "minimum_pair_ratio": fraction_json(min(ratios[metric])),
                "maximum_pair_ratio": fraction_json(max(ratios[metric])),
                "median_threshold": fraction_json(TIMING_THRESHOLD),
                "bonferroni_lower": fraction_json(lower, decimals=15),
                "bootstrap_support_points": len(distribution),
                "passes_conservative_numeric_gate": passes,
            }
        case_results.append({"case": case, "pairs": EXPECTED_REPLICATES, "metrics": metrics})

    if matching_pairs != EXPECTED_PAIRS:
        raise AssertionError("matching pair count mismatch")

    before_events = parse_memory_events(isolation["before"]["memory_events"])
    after_events = parse_memory_events(isolation["after"]["memory_events"])
    memory_deltas = {key: after_events[key] - before_events[key] for key in before_events}
    affinity_unchanged = (
        isolation["before"]["affinity"]
        == isolation["after"]["affinity"]
        == isolation["placement"]["allowed_cpus"]
    )
    runner_timing_valid = bool(isolation["timing_valid"] and remote_summary["timing_valid"])
    mechanical_timing_gates = (
        runner_timing_valid
        and isolation["measured_rows_with_nonzero_steal_delta"] == 0
        and isolation["cgroup_nr_throttled_delta"] == 0
        and affinity_unchanged
        and all(value == 0 for value in memory_deltas.values())
        and isolation["placement"]["memory_limit_bytes"] == 64_000_000_000
    )

    analysis = {
        "schema": SCHEMA,
        "protocol_sha256": protocol["freeze"]["protocol_sha256"],
        "analysis": {
            "script": "experiments/performance-saturation-20261101/go/analyze_remote_ab.py",
            "script_sha256": sha256(Path(__file__).resolve()),
            "status": "post_hoc_deterministic_sensitivity",
        },
        "inputs": {
            "protocol_file_sha256": sha256(protocol_path),
            "receipt_sha256": sha256(receipt_path),
            "archive_sha256": archive["sha256"],
            "archive_manifest_sha256": archive["manifest_sha256"],
            "rows_sha256": inventory["rows_sha256"],
            "isolation_sha256": sha256(isolation_path),
            "build_manifest_sha256": sha256(build_manifest_path),
            "campaign_manifest_sha256": inventory["campaign_manifest_sha256"],
            "campaign_summary_sha256": inventory["campaign_summary_sha256"],
            "remote_summary_sha256": sha256(remote_summary_path),
        },
        "transport": {
            "pod_id": receipt["pod"]["id"],
            "pod_name": receipt["pod"]["name"],
            "remote_returncode": receipt["remote_status"]["returncode"],
            "archive_members_verified": archive["members"],
            "archive_manifest_entries_verified": archive["manifest_entries"],
            "exact_id_delete_requested": receipt["cleanup"]["delete_requested"],
            "exact_id_absence_verified": receipt["cleanup"]["absence_verified"],
        },
        "flow": {
            "planned": EXPECTED_ROWS,
            "completed": len(rows),
            "warmups": len(inventory["warmups"]),
            "measured": len(measured),
            "pairs": matching_pairs,
        },
        "exact": {
            "matching_fingerprint_pairs": matching_pairs,
            "mismatches": 0,
        },
        "isolation": {
            "runner_timing_valid": runner_timing_valid,
            "measured_rows_with_nonzero_steal_delta": isolation[
                "measured_rows_with_nonzero_steal_delta"
            ],
            "cgroup_nr_throttled_delta": isolation["cgroup_nr_throttled_delta"],
            "affinity_unchanged": affinity_unchanged,
            "memory_event_deltas": memory_deltas,
            "memory_limit_bytes": isolation["placement"]["memory_limit_bytes"],
            "mechanical_timing_gates_pass": mechanical_timing_gates,
            "l2_attestation_explicit": False,
            "psi_materiality_threshold_preregistered": False,
        },
        "bootstrap_sensitivity": {
            "canonical_preregistered_analysis": False,
            "method": "exact_empirical_paired_percentile_bootstrap",
            "pairs_per_case": EXPECTED_REPLICATES,
            "statistic": "average_of_bootstrap_order_statistics_10_and_11",
            "distribution": "exhaustive_joint_order_statistic_distribution",
            "probability_arithmetic": "exact_rational",
            "rng": None,
            "draws": None,
            "family_alpha": "1/20",
            "tests_in_family": TIMING_TESTS,
            "correction": "two_sided_bonferroni_conservative_for_holm",
            "lower_quantile": "1/480",
            "quantile_definition": "inf{x: CDF(x) >= 1/480}",
        },
        "cases": case_results,
        "claims": {
            "C-ab-correct": "supported",
            "C-ab-allocation": "supported" if allocation_pass else "unsupported",
            "C-ab-timing_numeric": (
                "passes_conservative_sensitivity" if all_numeric_timing_pass else "unsupported"
            ),
            "C-ab-timing_formal": (
                "conditional_on_isolation_interpretation"
                if mechanical_timing_gates and all_numeric_timing_pass
                else "invalid_or_unsupported"
            ),
        },
        "verdict": {
            "overall": "unsupported",
            "reason": (
                "allocs/op exceeds the frozen 0.05 threshold in all six cases"
                if not allocation_pass
                else "the frozen conjunctive threshold was not fully satisfied"
            ),
        },
        "limitations": [
            "analysis_plan.script was null in the frozen v7 protocol",
            "bootstrap construction and the exact Holm interval procedure were not preregistered",
            "L2 attestation and a numeric material-PSI threshold were not explicit",
        ],
    }
    return analysis


def main() -> int:
    options = parse_args()
    result = analyze(options)
    encoded = json.dumps(result, indent=2) + "\n"
    if options.output:
        options.output.parent.mkdir(parents=True, exist_ok=True)
        options.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
