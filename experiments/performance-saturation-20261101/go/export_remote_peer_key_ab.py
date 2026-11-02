#!/usr/bin/env python3
"""Produce and mechanically validate the v9 A/B+A/A experiment export."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any


SCHEMA = "experiment.export/v1"
PROTOCOL_ID = "GO-COORD-PEER-KEY-20261101-REMOTE-AB-AA-V9"
PROTOCOL_VERSION = 9
PROTOCOL_PATH = "experiments/performance-saturation-20261101/go/protocol.v9.json"
ANALYZER_NAME = "analyze_remote_peer_key_ab.py"
BASELINE_ARM = "go-baseline"
CANDIDATE_ARM = "go-candidate"
AA_LEFT_ARM = "go-baseline-aa-left"
AA_RIGHT_ARM = "go-baseline-aa-right"
ARMS = {
    BASELINE_ARM: "baseline",
    CANDIDATE_ARM: "candidate",
    AA_LEFT_ARM: "control_aa",
    AA_RIGHT_ARM: "control_aa",
}
ORDER_CYCLE = (
    (BASELINE_ARM, CANDIDATE_ARM, AA_LEFT_ARM, AA_RIGHT_ARM),
    (CANDIDATE_ARM, BASELINE_ARM, AA_RIGHT_ARM, AA_LEFT_ARM),
    (AA_LEFT_ARM, AA_RIGHT_ARM, BASELINE_ARM, CANDIDATE_ARM),
    (AA_RIGHT_ARM, AA_LEFT_ARM, CANDIDATE_ARM, BASELINE_ARM),
)
CASES = [
    "BenchmarkStateVersionVector/log_1024",
    "BenchmarkStateVersionVector/log_8192",
    "BenchmarkStateDeltaSinceCaughtUp/log_1024",
    "BenchmarkStateDeltaSinceCaughtUp/log_8192",
    "BenchmarkStateDeltaSinceOneBehind/log_1024",
    "BenchmarkStateDeltaSinceOneBehind/log_8192",
]
EXPECTED_ROWS = 552
EXPECTED_MEASURED = 480
EXPECTED_WARMUPS = 72
FIXTURE_SEED = 24_301


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--failure-record",
        type=Path,
        help="seal a canonical 552-cell mechanical-failure export",
    )
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def stable_host_class_id(host: dict[str, Any]) -> str:
    """Validate and name the canonical stable placement represented by host."""

    identity = host.get("placement_identity")
    digest = host.get("placement_identity_sha256")
    model = host.get("cpu_model")
    logical_cpus = host.get("logical_cpus")
    affinity = host.get("affinity")
    topology = host.get("cpu_topology")
    order = host.get("topology_order")
    cpuset = host.get("cpuset_cpus")
    memory_max = host.get("memory_max")
    devices = host.get("nvidia_devices")
    if (
        not isinstance(identity, dict)
        or identity.get("schema") != "go-cpu-placement-identity/v1"
        or not isinstance(digest, str)
        or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        or not isinstance(model, str)
        or not model.strip()
        or type(logical_cpus) is not int
        or logical_cpus <= 0
        or not isinstance(affinity, list)
        or not affinity
        or any(type(cpu) is not int or cpu < 0 for cpu in affinity)
        or len(set(affinity)) != len(affinity)
        or logical_cpus < len(affinity)
        or not isinstance(topology, list)
        or len(topology) != len(affinity)
        or any(not isinstance(row, dict) for row in topology)
        or not isinstance(order, list)
        or set(order) != set(affinity)
        or len(order) != len(affinity)
        or not isinstance(cpuset, str)
        or not isinstance(memory_max, str)
        or re.fullmatch(r"[1-9][0-9]*", memory_max) is None
        or not isinstance(devices, list)
        or any(not isinstance(path, str) or not path for path in devices)
    ):
        raise ValueError("stable host-placement identity is malformed")
    parsed_cpuset: set[int] = set()
    try:
        for field in cpuset.split(","):
            if "-" in field:
                left, right = field.split("-", 1)
                parsed_cpuset.update(range(int(left), int(right) + 1))
            else:
                parsed_cpuset.add(int(field))
    except ValueError as error:
        raise ValueError("stable host-placement cpuset is malformed") from error
    if parsed_cpuset != set(affinity):
        raise ValueError("stable host-placement cpuset differs from affinity")
    fields = ("cpu", "package", "die", "numa", "core", "thread_siblings")
    normalized_topology = [{field: row.get(field) for field in fields} for row in topology]
    expected = {
        "schema": "go-cpu-placement-identity/v1",
        "cpu_model": model.strip(),
        "logical_cpus": logical_cpus,
        "affinity": list(affinity),
        "cpu_topology": normalized_topology,
        "topology_order": list(order),
        "cpuset_cpus": sorted(parsed_cpuset),
        "memory_limit_bytes": int(memory_max),
        "nvidia_devices": sorted(devices),
    }
    if identity != expected:
        raise ValueError("stable host-placement identity differs from raw host fields")
    actual = hashlib.sha256(json.dumps(
        identity, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    ).encode("utf-8")).hexdigest()
    if actual != digest:
        raise ValueError("stable host-placement identity SHA-256 mismatch")
    return "runpod-secure-cpu3c-" + digest[:12]


def file_entry(path: Path, base: Path, kind: str) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"export artifact is absent: {path}")
    return {
        "path": Path(os.path.relpath(path, base)).as_posix(),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "kind": kind,
    }


def flow(runs: list[dict[str, Any]]) -> dict[str, Any]:
    excluded: dict[str, list[str]] = defaultdict(list)
    for row in runs:
        if row["exclusion"]["excluded"]:
            excluded[row["exclusion"]["rule"] or "unspecified"].append(row["run_id"])
    return {
        "planned": len(runs),
        "attempted": sum(row["attempts"] >= 1 for row in runs),
        "completed": sum(row["outcome_class"] == "completed" for row in runs),
        "not_completed": sum(row["outcome_class"] == "not_completed" for row in runs),
        "interrupted": sum(row["status"] == "interrupted" for row in runs),
        "resumed": sum(row["resumed"] > 0 for row in runs),
        "excluded": [
            {"rule": rule, "run_ids": run_ids}
            for rule, run_ids in sorted(excluded.items())
        ],
    }


def row_status(row: dict[str, Any]) -> str:
    if row.get("timed_out"):
        return "timeout"
    if row.get("status") == "completed" and row.get("exit_status") == 0:
        return "succeeded"
    if row.get("status") == "not_completed" or row.get("outcome_class") == "instrument_error":
        return "infra_error"
    return "failed"


def mismatch_cells(rows: list[dict[str, Any]]) -> set[tuple[str, bool, int]]:
    pairs: dict[tuple[str, bool, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        pairs[(row["case"], row["warmup"], row["replicate"])][row["arm"]] = row
    mismatches: set[tuple[str, bool, int]] = set()
    references: dict[str, dict[str, Any]] = {}
    for cell, pair in pairs.items():
        expected = (
            {"vector_sha256"}
            if cell[0].startswith("BenchmarkStateVersionVector/")
            else {"lines_sha256", "reached_vector_sha256"}
        )
        fingerprints: dict[str, dict[str, Any]] = {}
        complete = set(pair) == set(ARMS)
        for arm in ARMS:
            if not complete:
                break
            row = pair[arm]
            parsed = row.get("parsed") if isinstance(row.get("parsed"), dict) else {}
            observed = parsed.get("fingerprints")
            if (
                row.get("status") != "completed"
                or row.get("exit_status") != 0
                or row.get("timed_out") is not False
                or not isinstance(observed, dict)
                or set(observed) != expected
            ):
                complete = False
                break
            fingerprints[arm] = observed
        if complete:
            reference = references.setdefault(cell[0], fingerprints[BASELINE_ARM])
            if any(value != reference for value in fingerprints.values()):
                mismatches.add(cell)
    return mismatches


def expected_schedule() -> list[dict[str, Any]]:
    expected: list[dict[str, Any]] = []
    sequence = 0
    for case_index, case in enumerate(CASES, 1):
        rounds = [(True, replicate) for replicate in range(1, 4)]
        rounds.extend((False, replicate) for replicate in range(1, 21))
        for warmup, replicate in rounds:
            arms = ORDER_CYCLE[(replicate - 1) % len(ORDER_CYCLE)]
            for order_position, arm in enumerate(arms, 1):
                sequence += 1
                kind = "warmup" if warmup else "measured"
                expected.append(
                    {
                        "sequence": sequence,
                        "case": case,
                        "case_index": case_index,
                        "replicate": replicate,
                        "warmup": warmup,
                        "order_position": order_position,
                        "arm": arm,
                        "run_id": (
                            f"{sequence:04d}_{kind}_case{case_index:02d}_"
                            f"r{replicate:02d}_p{order_position}_{arm}"
                        ),
                    }
                )
    return expected


def make_run(
    row: dict[str, Any],
    *,
    base: Path,
    timing_valid: bool,
    mismatches: set[tuple[str, bool, int]],
) -> dict[str, Any]:
    status = row_status(row)
    parsed = row.get("parsed") if isinstance(row.get("parsed"), dict) else {}
    metrics = parsed.get("metrics") if isinstance(parsed.get("metrics"), dict) else {}
    fingerprints = (
        parsed.get("fingerprints")
        if isinstance(parsed.get("fingerprints"), dict)
        else {}
    )
    rusage = row.get("rusage") if isinstance(row.get("rusage"), dict) else {}
    pair_mismatch = (row["case"], row["warmup"], row["replicate"]) in mismatches
    verification = (
        "refuted"
        if pair_mismatch
        else "verified"
        if status == "succeeded" and fingerprints
        else "not_run"
    )
    exclusion_rule = (
        "wrong_answer: complete four-arm fingerprint cell or case invariant differs"
        if pair_mismatch
        else None
    )
    counted: dict[str, int | float | str] = {}
    if "B/op" in metrics:
        counted["bytes_per_op"] = metrics["B/op"]
    if "allocs/op" in metrics:
        counted["allocs_per_op"] = metrics["allocs/op"]
    if fingerprints:
        counted["correctness_fingerprints"] = json.dumps(
            fingerprints, sort_keys=True, separators=(",", ":")
        )
    counters = {
        "benchmark_iterations": parsed.get("iterations", 0),
        "outer_wall_ns": row.get("outer_wall_ns", 0),
    }
    for source, destination in (
        ("ns/op", "wall_ns_per_op"),
        ("cpu-ns/op", "cpu_ns_per_op"),
        ("log_entries", "log_entries"),
        ("lines/op", "lines_per_op"),
    ):
        if source in metrics:
            counters[destination] = metrics[source]
    for key in (
        "voluntary_context_switches",
        "involuntary_context_switches",
        "major_faults",
        "minor_faults",
    ):
        if key in rusage:
            counters[f"rusage_{key}"] = rusage[key]
    artifacts = [
        file_entry(base / row["artifacts"][kind], base, "raw" if kind == "metadata" else "log")
        for kind in ("stdout", "stderr", "metadata")
    ]
    measured_replicate = row["replicate"] - 1
    export_replicate = measured_replicate if not row["warmup"] else row["replicate"] - 1
    row_isolation = row.get("isolation") if isinstance(row.get("isolation"), dict) else {}
    tier = row_isolation.get("earned_level")
    if tier not in {"L0", "L1", "L2", "L3"}:
        tier = "L0"
    wall_valid = bool(
        timing_valid
        and tier in {"L2", "L3"}
        and not row["warmup"]
        and status == "succeeded"
        and not pair_mismatch
    )
    blockers = list(row_isolation.get("blocking", []))
    if not timing_valid:
        blockers.append(
            "session did not establish every preregistered cumulative L2 isolation gate; see session receipts"
        )
    if pair_mismatch:
        blockers.append("paired correctness fingerprint mismatch")
    return {
        "run_id": row["run_id"],
        "arm": row["arm"],
        "instance_id": str(CASES.index(row["case"])),
        "seed": FIXTURE_SEED,
        "replicate": export_replicate,
        "warmup": bool(row["warmup"]),
        "status": status,
        "outcome_class": "completed" if status in {"succeeded", "failed"} else "not_completed",
        "attempts": 1,
        "resumed": 0,
        "checkpoint": None,
        "measurements": {
            "counted": counted,
            # The registered wall metric is the Go benchmark's in-loop ns/op,
            # not the outer process-launch duration retained below as a counter.
            "wall_seconds": (
                metrics["ns/op"] / 1_000_000_000
                if isinstance(metrics.get("ns/op"), (int, float))
                and not isinstance(metrics.get("ns/op"), bool)
                else None
            ),
            "wall_valid": wall_valid,
            "cpu_user_seconds": rusage.get("user_seconds"),
            "cpu_sys_seconds": rusage.get("system_seconds"),
            "max_rss_bytes": (
                rusage["max_rss_kib"] * 1024
                if isinstance(rusage.get("max_rss_kib"), int)
                else None
            ),
            "counters": counters,
        },
        "isolation": {
            "tier": tier,
            "contended": bool(
                not row["warmup"]
                and status == "succeeded"
                and tier not in {"L2", "L3"}
            ),
            "blockers": blockers,
        },
        "verification": {
            "status": verification,
            "verifier": "fixed Go benchmark fixture fingerprints, paired across exact arms",
        },
        "exclusion": {
            "excluded": pair_mismatch,
            "rule": exclusion_rule,
        },
        "artifacts": artifacts,
        "started_at": row.get("started"),
        "finished_at": row.get("finished"),
        "worker": None,
        "backend_ref": row["run_id"],
    }


def make_failure_run(planned: dict[str, Any], failure: dict[str, Any]) -> dict[str, Any]:
    """Represent a frozen schedule cell blocked by a workflow-level failure.

    The export schema requires attempts >= 1.  The single combined provider
    job is the attempt: the row was planned and entered that workflow, but its
    benchmark child was never completed because an upstream stage failed.
    """

    replicate = planned["replicate"] - 1
    return {
        "run_id": planned["run_id"],
        "arm": planned["arm"],
        "instance_id": str(CASES.index(planned["case"])),
        "seed": FIXTURE_SEED,
        "replicate": replicate,
        "warmup": planned["warmup"],
        "status": "infra_error",
        "outcome_class": "not_completed",
        "attempts": 1,
        "resumed": 0,
        "checkpoint": None,
        "measurements": {
            "counted": {},
            "wall_seconds": None,
            "wall_valid": False,
            "cpu_user_seconds": None,
            "cpu_sys_seconds": None,
            "max_rss_bytes": None,
            "counters": {},
        },
        "isolation": {
            "tier": "L0",
            "contended": False,
            "blockers": [
                "combined workflow mechanical failure before this child completed: "
                + str(failure["stage"])
            ],
        },
        "verification": {
            "status": "not_run",
            "verifier": "benchmark child did not complete",
        },
        "exclusion": {"excluded": False, "rule": None},
        "artifacts": [],
        "started_at": None,
        "finished_at": None,
        "worker": None,
        "backend_ref": planned["run_id"],
    }


def usable_prefix(run: Path, protocol_sha256: str) -> list[dict[str, Any]]:
    """Return only the exact, contiguous, fully materialized row prefix."""

    rows_path = run / "campaign" / "rows.jsonl"
    if not rows_path.is_file():
        return []
    try:
        rows = [json.loads(line) for line in rows_path.read_text(encoding="utf-8").splitlines() if line]
    except (OSError, UnicodeError, json.JSONDecodeError):
        return []
    expected = expected_schedule()
    prefix: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if index >= len(expected) or not isinstance(row, dict):
            break
        planned = expected[index]
        if (
            any(row.get(key) != value for key, value in planned.items())
            or row.get("protocol_sha256") != protocol_sha256
        ):
            break
        artifacts = row.get("artifacts")
        if not isinstance(artifacts, dict):
            break
        complete_artifacts = True
        for key in ("stdout", "stderr", "metadata"):
            relative = artifacts.get(key)
            if not isinstance(relative, str):
                complete_artifacts = False
                break
            path = run / "campaign" / relative
            try:
                path.resolve().relative_to((run / "campaign").resolve())
            except ValueError:
                complete_artifacts = False
                break
            if not path.is_file():
                complete_artifacts = False
                break
        if not complete_artifacts:
            break
        prefix.append(row)
    return prefix


def _failure_file_inventory(
    run: Path,
    output: Path,
    row_runs: list[dict[str, Any]],
    analysis_script: Path | None,
) -> list[dict[str, Any]]:
    base = output.parent
    already = {
        (base / artifact["path"]).resolve()
        for row in row_runs
        for artifact in row["artifacts"]
    }
    if analysis_script is not None:
        already.add(analysis_script.resolve())
    excluded = {output.resolve(), (run / "remote-summary.json").resolve()}
    records: list[dict[str, Any]] = []
    for path in sorted(run.rglob("*")):
        if path.is_symlink() or (path.exists() and not path.is_file() and not path.is_dir()):
            raise ValueError("failure output contains a non-regular entry")
        if not path.is_file() or path.resolve() in already or path.resolve() in excluded:
            continue
        suffix = path.suffix.lower()
        kind = "log" if suffix in {".txt", ".log"} else "summary"
        records.append(file_entry(path, base, kind))
    return records


def produce_failure(
    run: Path,
    protocol_sha256: str,
    source_commit: str,
    output: Path,
    failure_path: Path,
    *,
    created: str | None = None,
    rewrite_failure_receipt: bool = True,
) -> dict[str, Any]:
    """Produce a canonical export even when build/test/campaign setup failed."""

    if re.fullmatch(r"[0-9a-f]{64}", protocol_sha256) is None:
        raise ValueError("protocol SHA-256 must be 64 lowercase hex characters")
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("source commit must be 40 lowercase hex characters")
    run, output, failure_path = run.resolve(), output.resolve(), failure_path.resolve()
    if failure_path != run / "failure.json":
        raise ValueError("failure receipt must be the output-root failure.json")
    failure = load_json(failure_path)
    if (
        failure.get("schema") != "go-coordinator-remote-failure/v1"
        or failure.get("protocol_sha256") != protocol_sha256
        or failure.get("source_commit") != source_commit
        or not isinstance(failure.get("stage"), str)
        or not failure["stage"]
        or not isinstance(failure.get("error"), dict)
        or set(failure["error"]) != {"type", "detail"}
    ):
        raise ValueError("mechanical failure receipt is malformed")

    prefix = usable_prefix(run, protocol_sha256)
    if rewrite_failure_receipt:
        failure["usable_prefix_rows"] = len(prefix)
        # Rewrite once before hashing/exporting so the prefix count is receipt-bound.
        failure_path.write_text(
            json.dumps(failure, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
    elif failure.get("usable_prefix_rows") != len(prefix):
        raise ValueError("failure receipt usable prefix differs from raw evidence")
    mismatches = mismatch_cells(prefix)
    exported_prefix = [
        make_run(row, base=run / "campaign", timing_valid=False, mismatches=mismatches)
        for row in prefix
    ]
    schedule = expected_schedule()
    exported_runs = exported_prefix + [
        make_failure_run(planned, failure) for planned in schedule[len(prefix) :]
    ]

    build_path = run / "build" / "manifest.json"
    build: dict[str, Any] = {}
    if build_path.is_file():
        try:
            loaded_build = load_json(build_path)
        except (OSError, UnicodeError, json.JSONDecodeError):
            # A signal or storage error may interrupt the ordinary manifest
            # write.  Preserve those raw bytes in the failure file inventory,
            # but never let a partial optional receipt prevent failure sealing.
            loaded_build = {}
        if isinstance(loaded_build, dict):
            build = loaded_build
    arm_records = build.get("arms") if isinstance(build.get("arms"), dict) else {}
    arms = []
    for arm, role in ARMS.items():
        record = arm_records.get(arm) if isinstance(arm_records.get(arm), dict) else {}
        digest = record.get("binary_sha256")
        binary_name = record.get("binary")
        binary = run / "build" / binary_name if isinstance(binary_name, str) else None
        if (
            re.fullmatch(r"[0-9a-f]{64}", str(digest)) is None
            or binary is None
            or not binary.is_file()
            or sha256(binary) != digest
        ):
            digest = None
        arms.append(
            {
                "id": arm,
                "role": role,
                "binary_sha256": digest,
                "commit": source_commit,
                "image_digest": "runpod/base:1.0.2-ubuntu2404",
            }
        )

    analysis_script = run / "tooling" / ANALYZER_NAME
    if not analysis_script.is_file():
        raise ValueError("registered analyzer is absent from the owned output root")
    base = output.parent
    files = _failure_file_inventory(run, output, exported_runs, analysis_script)
    export = {
        "schema": SCHEMA,
        "export_id": "GO-COORD-PEER-KEY-REMOTE-AB-AA-V9-EXPORT",
        "created": created or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "protocol": {
            "path": PROTOCOL_PATH,
            "sha256": protocol_sha256,
            "protocol_id": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
        },
        "producer": {
            "runtime": "runpod-http-batch",
            "model": None,
            "session": None,
            "role": "executor",
        },
        "source": {"repo": "cryptanalysis", "commit": source_commit, "dirty": False},
        "backend": "runpod",
        "host": {
            "path": file_entry(failure_path, base, "host")["path"],
            "sha256": sha256(failure_path),
            "class_id": None,
            "summary": {
                "cpu_model": None,
                "logical_cpus": None,
                "memory_bytes": None,
                "kernel": None,
                "hypervisor": "RunPod Secure CPU pod",
                "isolation_tier_max": "L0",
                "gpu": None,
                "instance_type": "cpu3c",
                "spot": False,
            },
        },
        "arms": arms,
        "runs": exported_runs,
        "flow": flow(exported_runs),
        "files": files,
        "analysis": {
            "script": (
                file_entry(analysis_script, base, "analysis")
                if analysis_script is not None else None
            ),
            "blinded": False,
            "blinding_key_sha256": None,
            "outputs": [],
            "unmasked_at": None,
        },
        "notes": [
            {
                "kind": "observation",
                "text": "The combined workflow sealed a mechanical failure before all frozen child executions completed.",
                "by": "export_remote_peer_key_ab.py",
            }
        ],
        "reviews_dir": "reviews",
        "backend_record": {
            "campaign_schema": "go-coordinator-peer-key-campaign/2",
            "completion_status": "mechanical_failure",
            "planned_rows": EXPECTED_ROWS,
            "usable_prefix_rows": len(prefix),
            "failure_record_sha256": sha256(failure_path),
        },
    }
    validate(export, output)
    return export


def produce(
    run: Path,
    protocol_sha256: str,
    source_commit: str,
    output: Path,
    *,
    created: str | None = None,
) -> dict[str, Any]:
    if len(protocol_sha256) != 64 or any(c not in "0123456789abcdef" for c in protocol_sha256):
        raise ValueError("protocol SHA-256 must be 64 lowercase hex characters")
    if len(source_commit) != 40 or any(c not in "0123456789abcdef" for c in source_commit):
        raise ValueError("source commit must be 40 lowercase hex characters")
    run = run.resolve()
    output = output.resolve()
    campaign = run / "campaign"
    base = output.parent
    rows_path = campaign / "rows.jsonl"
    rows = [
        json.loads(line)
        for line in rows_path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    build = load_json(run / "build" / "manifest.json")
    isolation = load_json(run / "isolation.json")
    campaign_manifest = load_json(campaign / "manifest.json")
    campaign_summary = load_json(campaign / "summary.json")
    if len(rows) != EXPECTED_ROWS:
        raise ValueError(f"expected {EXPECTED_ROWS} rows, got {len(rows)}")
    if [row.get("sequence") for row in rows] != list(range(1, EXPECTED_ROWS + 1)):
        raise ValueError("row sequence is not exact and contiguous")
    if sum(not row["warmup"] for row in rows) != EXPECTED_MEASURED:
        raise ValueError("measured row count mismatch")
    if sum(row["warmup"] for row in rows) != EXPECTED_WARMUPS:
        raise ValueError("warmup row count mismatch")
    if (
        campaign_manifest.get("protocol_sha256") != protocol_sha256
        or campaign_summary.get("protocol_sha256") != protocol_sha256
        or campaign_manifest.get("phase") != "fixed-peer-key-ab-aa-v9"
        or campaign_summary.get("phase") != "fixed-peer-key-ab-aa-v9"
        or campaign_manifest.get("cases") != CASES
        or any(row.get("protocol_sha256") != protocol_sha256 for row in rows)
    ):
        raise ValueError("campaign protocol/phase/case binding mismatch")
    for row, planned in zip(rows, expected_schedule(), strict=True):
        if any(row.get(key) != value for key, value in planned.items()):
            raise ValueError(f"row schedule mismatch at sequence {planned['sequence']}")
    source_archive = build.get("source_archive", {})
    if source_archive.get("commit") != source_commit:
        raise ValueError("build source archive commit differs from export source")
    toolchain = build.get("toolchain", {})
    if (
        toolchain.get("archive") != "go1.27.3.linux-amd64.tar.gz"
        or toolchain.get("archive_bytes") != 70_588_678
        or toolchain.get("archive_sha256")
        != "65efbc80fdc1fa2cd2631cad5b481777a68e8725f34e89f50fc6ac714e379b40"
    ):
        raise ValueError("Go download receipt differs from the registered archive")
    for arm, filename in (
        (BASELINE_ARM, "coord-baseline.test"),
        (CANDIDATE_ARM, "coord-candidate.test"),
        (AA_LEFT_ARM, "coord-baseline-aa-left.test"),
        (AA_RIGHT_ARM, "coord-baseline-aa-right.test"),
    ):
        binary = run / "build" / filename
        record = build.get("arms", {}).get(arm, {})
        if (
            record.get("binary") != filename
            or binary.stat().st_size != record.get("binary_bytes")
            or sha256(binary) != record.get("binary_sha256")
        ):
            raise ValueError(f"retained binary binding mismatch: {arm}")
    if not (
        build["arms"][BASELINE_ARM]["binary_sha256"]
        == build["arms"][AA_LEFT_ARM]["binary_sha256"]
        == build["arms"][AA_RIGHT_ARM]["binary_sha256"]
    ):
        raise ValueError("A/A controls are not byte-identical to the baseline")
    mismatches = mismatch_cells(rows)
    timing_valid = bool(isolation.get("timing_valid"))
    exported_runs = [
        make_run(
            row,
            base=campaign,
            timing_valid=timing_valid,
            mismatches=mismatches,
        )
        for row in rows
    ]
    tier_rank = {None: -1, "L0": 0, "L1": 1, "L2": 2, "L3": 3}
    tier_max = max(
        (item["isolation"]["tier"] for item in exported_runs),
        key=lambda tier: tier_rank.get(tier, -1),
        default=None,
    )
    initial_host = build["host"]
    placement = build["placement"]
    host_class_id = stable_host_class_id(initial_host)
    analysis_script = run / "tooling" / ANALYZER_NAME
    top_files = [
        file_entry(rows_path, base, "raw"),
        file_entry(campaign / "manifest.json", base, "summary"),
        file_entry(campaign / "summary.json", base, "summary"),
        file_entry(run / "build" / "manifest.json", base, "summary"),
        file_entry(run / "tests" / "manifest.json", base, "summary"),
        file_entry(run / "tests" / "baseline.txt", base, "log"),
        file_entry(run / "tests" / "candidate.txt", base, "log"),
        file_entry(run / "build" / "coord-baseline.test", base, "other"),
        file_entry(run / "build" / "coord-candidate.test", base, "other"),
        file_entry(run / "build" / "coord-baseline-aa-left.test", base, "other"),
        file_entry(run / "build" / "coord-baseline-aa-right.test", base, "other"),
        file_entry(run / "isolation.json", base, "host"),
    ]
    retained = build.get("runner", {}).get("retained", {})
    if not isinstance(retained, dict):
        raise ValueError("build manifest retained-tooling inventory is malformed")
    for record in retained.values():
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            raise ValueError("build manifest retained-tooling record is malformed")
        retained_path = run / record["path"]
        if retained_path.resolve() == analysis_script.resolve():
            continue
        top_files.append(file_entry(retained_path, base, "analysis"))
    export = {
        "schema": SCHEMA,
        "export_id": "GO-COORD-PEER-KEY-REMOTE-AB-AA-V9-EXPORT",
        "created": created or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "protocol": {
            "path": PROTOCOL_PATH,
            "sha256": protocol_sha256,
            "protocol_id": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
        },
        "producer": {
            "runtime": "runpod-http-batch",
            "model": None,
            "session": None,
            "role": "executor",
        },
        "source": {"repo": "cryptanalysis", "commit": source_commit, "dirty": False},
        "backend": "runpod",
        "host": {
            "path": file_entry(run / "isolation.json", base, "host")["path"],
            "sha256": sha256(run / "isolation.json"),
            "class_id": host_class_id,
            "summary": {
                "cpu_model": initial_host.get("cpu_model"),
                "logical_cpus": len(placement["allowed_cpus"]),
                "memory_bytes": placement["memory_limit_bytes"],
                "kernel": initial_host.get("uname"),
                "hypervisor": "RunPod Secure CPU pod",
                "isolation_tier_max": tier_max,
                "gpu": None,
                "instance_type": "cpu3c",
                "spot": False,
            },
        },
        "arms": [
            {
                "id": arm,
                "role": role,
                "binary_sha256": build["arms"][arm]["binary_sha256"],
                "commit": source_commit,
                "image_digest": "runpod/base:1.0.2-ubuntu2404",
            }
            for arm, role in ARMS.items()
        ],
        "runs": exported_runs,
        "flow": flow(exported_runs),
        "files": top_files,
        "analysis": {
            "script": file_entry(analysis_script, base, "analysis"),
            "blinded": False,
            "blinding_key_sha256": None,
            "outputs": [],
            "unmasked_at": None,
        },
        "notes": [
            {
                "kind": "observation",
                "text": "Combined mode produced this write-once export before formal post-run analysis; verdicts are not stored in notes.",
                "by": "export_remote_peer_key_ab.py",
            }
        ],
        "reviews_dir": "reviews",
        "backend_record": {
            "campaign_schema": "go-coordinator-peer-key-campaign/2",
            "rows_sha256": sha256(rows_path),
            "build_manifest_sha256": sha256(run / "build" / "manifest.json"),
            "tests_manifest_sha256": sha256(run / "tests" / "manifest.json"),
            "isolation_sha256": sha256(run / "isolation.json"),
            "fingerprint_pair_mismatches": len(mismatches),
        },
    }
    validate(export, output)
    return export


def validate(export: dict[str, Any], output: Path) -> None:
    if export.get("schema") != SCHEMA:
        raise ValueError("export schema mismatch")
    if export.get("protocol", {}).get("protocol_id") != PROTOCOL_ID:
        raise ValueError("export protocol identity mismatch")
    runs = export.get("runs")
    if not isinstance(runs, list) or len(runs) != EXPECTED_ROWS:
        raise ValueError("export run inventory mismatch")
    if export.get("flow") != flow(runs):
        raise ValueError("export flow mismatch")
    cells = {
        (row["arm"], row["instance_id"], row["replicate"], row["warmup"])
        for row in runs
    }
    if len(cells) != EXPECTED_ROWS:
        raise ValueError("export contains duplicate execution cells")
    measured = [row for row in runs if not row["warmup"]]
    if len(measured) != EXPECTED_MEASURED:
        raise ValueError("export measured inventory mismatch")
    for arm in ARMS:
        for instance in map(str, range(len(CASES))):
            replicates = {
                row["replicate"]
                for row in measured
                if row["arm"] == arm and row["instance_id"] == instance
            }
            if replicates != set(range(20)):
                raise ValueError(f"export measured cell mismatch: {arm} {instance}")
    backend = export.get("backend_record", {})
    if backend.get("completion_status") == "mechanical_failure":
        prefix = backend.get("usable_prefix_rows")
        if (
            type(prefix) is not int
            or not 0 <= prefix <= EXPECTED_ROWS
            or backend.get("planned_rows") != EXPECTED_ROWS
            or re.fullmatch(r"[0-9a-f]{64}", str(backend.get("failure_record_sha256", "")))
            is None
        ):
            raise ValueError("failure export backend receipt is malformed")
        for index, (row, planned) in enumerate(zip(runs, expected_schedule(), strict=True)):
            expected_replicate = planned["replicate"] - 1
            if (
                row.get("run_id") != planned["run_id"]
                or row.get("arm") != planned["arm"]
                or row.get("instance_id") != str(CASES.index(planned["case"]))
                or row.get("replicate") != expected_replicate
                or row.get("warmup") is not planned["warmup"]
            ):
                raise ValueError("failure export frozen schedule mismatch")
            if index >= prefix and (
                row.get("status") != "infra_error"
                or row.get("outcome_class") != "not_completed"
                or row.get("attempts") != 1
                or row.get("verification", {}).get("status") != "not_run"
                or row.get("measurements", {}).get("wall_valid") is not False
                or row.get("artifacts") != []
            ):
                raise ValueError("failure export suffix is not an explicit infra error")
    base = output.parent
    files = list(export["files"])
    files.extend(artifact for row in runs for artifact in row["artifacts"])
    analysis_script = export["analysis"]["script"]
    if analysis_script is not None:
        files.append(analysis_script)
    for entry in files:
        path = base / entry["path"]
        if (
            not path.is_file()
            or path.stat().st_size != entry["bytes"]
            or sha256(path) != entry["sha256"]
        ):
            raise ValueError(f"export file binding mismatch: {entry['path']}")


def write_once(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    with path.open("x", encoding="utf-8") as stream:
        stream.write(encoded)


def main() -> int:
    options = parse_args()
    if options.failure_record is None:
        export = produce(
            options.run,
            options.protocol_sha256,
            options.source_commit,
            options.output,
        )
    else:
        export = produce_failure(
            options.run,
            options.protocol_sha256,
            options.source_commit,
            options.output,
            options.failure_record,
        )
    write_once(options.output, export)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
