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
            "session failed at least one preregistered cumulative L2 or A/A eligibility gate; see ../isolation.json"
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
        "outcome_class": "completed" if status == "succeeded" else "not_completed",
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
            "contended": not wall_valid and not row["warmup"],
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


def produce(
    run: Path,
    protocol_sha256: str,
    source_commit: str,
    output: Path,
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
    if len(rows) != EXPECTED_ROWS:
        raise ValueError(f"expected {EXPECTED_ROWS} rows, got {len(rows)}")
    if [row.get("sequence") for row in rows] != list(range(1, EXPECTED_ROWS + 1)):
        raise ValueError("row sequence is not exact and contiguous")
    if sum(not row["warmup"] for row in rows) != EXPECTED_MEASURED:
        raise ValueError("measured row count mismatch")
    if sum(row["warmup"] for row in rows) != EXPECTED_WARMUPS:
        raise ValueError("warmup row count mismatch")
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
        "created": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
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
            "class_id": "runpod-secure-cpu3c-" + initial_host["cpuinfo_sha256"][:12],
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
    base = output.parent
    files = list(export["files"])
    files.extend(artifact for row in runs for artifact in row["artifacts"])
    files.append(export["analysis"]["script"])
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
    export = produce(
        options.run,
        options.protocol_sha256,
        options.source_commit,
        options.output,
    )
    write_once(options.output, export)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
