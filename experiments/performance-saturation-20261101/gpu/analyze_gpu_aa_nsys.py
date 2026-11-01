#!/usr/bin/env python3
"""Validate and summarize the preregistered Nsys-only RTX 5090 A/A study.

This helper deliberately knows the complete workload and correctness oracle.
The shell runner asks it for the plan, uses it as a gate after each phase, and
only then asks it to write rows.jsonl and analysis.json.  It never overwrites
an analysis artifact.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import re
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ARMS = ("control", "current")
MEASURED_ROUNDS = tuple(range(1, 7))
VERBOSE_RE = re.compile(
    r"^F4_F2_ECHELON: .*? upload ([0-9]+(?:\.[0-9]+)?) ms, "
    r"device ([0-9]+(?:\.[0-9]+)?) ms, download ([0-9]+(?:\.[0-9]+)?) ms,"
    r" ([0-9.eE+-]+) word XORs$",
    re.MULTILINE,
)
CUDA_BACKEND_RE = re.compile(
    r"^cuda:(?P<gpu>[^\r\n]+?) sm_[0-9]+ x[1-9][0-9]* "
    r"code=(?:sm_[0-9]+|compute_[0-9]+|CA_F4_PTX)$"
)


@dataclass(frozen=True)
class Workload:
    role: str
    tag: str
    cell: str
    degree: int
    curve: str
    m: int
    target_x: int
    rows: int
    cols: int
    rank: int
    refuted: bool
    pinned: int
    word_ops: int


# The primary and holdout are also members of the fixed five-cell panel.
WORKLOADS = (
    Workload("panel", "k0n13m2d5", "0:13:2:1234", 5, "K_0/2^13", 2, 1234,
             30225, 53871, 27250, True, 0, 10745652033),
    Workload("panel", "k0n9m3d5", "0:9:3:77", 5, "K_0/2^9", 3, 77,
             33147, 87118, 31069, False, 1, 1196809344),
    Workload("panel", "k1n11m2d5", "1:11:2:301", 5, "K_1/2^11", 2, 301,
             14861, 21196, 12091, False, 0, 986408355),
    Workload("holdout", "k1n11m2d6", "1:11:2:301", 6, "K_1/2^11", 2, 301,
             68156, 60040, 46747, False, 0, 57968918179),
    Workload("primary", "k0n13m2d6", "0:13:2:1234", 6, "K_0/2^13", 2, 1234,
             168363, 188203, 130583, True, 0, 1110114894889),
)
BY_TAG = {w.tag: w for w in WORKLOADS}


class GateError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_status(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8").strip()
        return int(text)
    except (OSError, ValueError) as exc:
        raise GateError(f"invalid or missing status file {path}: {exc}") from exc


def require_nonempty(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise GateError(f"missing or empty artifact: {path}")


def validate_gpu_inventory(session: Path, expected_gpu: str) -> None:
    """Require one well-formed recorded GPU whose name exactly matches the contract."""
    path = session / "metadata" / "gpu.csv"
    require_nonempty(path)
    try:
        with path.open(newline="", encoding="utf-8") as stream:
            rows = [row for row in csv.reader(stream) if any(field.strip() for field in row)]
    except (OSError, csv.Error) as exc:
        raise GateError(f"invalid GPU inventory {path}: {exc}") from exc
    if len(rows) != 1:
        raise GateError(f"{path}: expected exactly one GPU row, found {len(rows)}")
    row = rows[0]
    if len(row) != 11 or any(not field.strip() for field in row):
        raise GateError(f"{path}: malformed GPU inventory row")
    observed_gpu = row[2].strip()
    if observed_gpu != expected_gpu:
        raise GateError(
            f"{path}: GPU={observed_gpu!r}, expected exactly {expected_gpu!r}"
        )


def validate_cuda_backend(backend: object, expected_gpu: str) -> str:
    """Parse the production backend receipt and bind it to one exact GPU name."""
    if not isinstance(backend, str):
        raise GateError(f"malformed CUDA backend {backend!r}")
    match = CUDA_BACKEND_RE.fullmatch(backend)
    if match is None:
        raise GateError(f"malformed CUDA backend {backend!r}")
    observed_gpu = match.group("gpu")
    if observed_gpu != expected_gpu:
        raise GateError(
            f"unexpected CUDA GPU {observed_gpu!r}, expected exactly {expected_gpu!r}"
        )
    return backend


def expected_fields(workload: Workload) -> dict[str, Any]:
    return {
        "harness": "f4_matrix_bench",
        "curve": workload.curve,
        "m": workload.m,
        "target_x": workload.target_x,
        "degree": workload.degree,
        "rows": workload.rows,
        "cols": workload.cols,
        "rank": workload.rank,
        "refuted": workload.refuted,
        "pinned": workload.pinned,
        "word_ops": workload.word_ops,
    }


def validate_execution(
    prefix: Path, workload: Workload, expected_gpu: str
) -> dict[str, Any]:
    report_path = prefix.with_suffix(".json")
    log_path = prefix.with_suffix(".log")
    smi_path = prefix.with_suffix(".smi.csv")
    status_path = prefix.with_suffix(".status")
    for path in (report_path, log_path, smi_path, status_path):
        require_nonempty(path)
    status = read_status(status_path)
    if status != 0:
        raise GateError(f"execution failed with status {status}: {prefix}")

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError(f"invalid report {report_path}: {exc}") from exc
    for field, expected in expected_fields(workload).items():
        observed = report.get(field)
        if observed != expected:
            raise GateError(
                f"{report_path}: {field}={observed!r}, expected {expected!r}"
            )
    if report.get("echelon_mode") != "cuda":
        raise GateError(f"{report_path}: not forced through CUDA")
    validate_cuda_backend(report.get("echelon_backend"), expected_gpu)

    log = log_path.read_text(encoding="utf-8", errors="replace")
    matches = list(VERBOSE_RE.finditer(log))
    if len(matches) != 1:
        raise GateError(f"{log_path}: expected one verbose timing line, found {len(matches)}")
    upload_ms, device_ms, download_ms = (float(v) for v in matches[0].groups()[:3])
    if not all(math.isfinite(v) and v >= 0 for v in (upload_ms, device_ms, download_ms)):
        raise GateError(f"{log_path}: non-finite or negative timing")
    return {
        "report": report,
        "upload_ms": upload_ms,
        "device_ms": device_ms,
        "download_ms": download_ms,
        "artifacts": {
            p.name: {"path": str(p), "sha256": sha256_file(p), "bytes": p.stat().st_size}
            for p in (report_path, log_path, smi_path, status_path)
        },
    }


def raw_prefix(session: Path, phase: str, round_index: int, tag: str, arm: str) -> Path:
    return session / "raw" / phase / f"r{round_index:02d}" / tag / arm


def gate_raw(session: Path, phase: str, expected_gpu: str) -> list[dict[str, Any]]:
    if phase == "warmup":
        rounds = (0,)
    elif phase == "measure":
        rounds = MEASURED_ROUNDS
    else:
        raise GateError(f"unknown raw phase {phase!r}")
    rows: list[dict[str, Any]] = []
    for round_index in rounds:
        for workload in WORKLOADS:
            for arm in ARMS:
                observed = validate_execution(
                    raw_prefix(session, phase, round_index, workload.tag, arm),
                    workload,
                    expected_gpu,
                )
                rows.append({
                    "phase": phase,
                    "round": round_index,
                    "workload": workload,
                    "arm": arm,
                    **observed,
                })
    return rows


def gate_nsys(session: Path, expected_gpu: str) -> None:
    workload = BY_TAG["k0n13m2d6"]
    for arm in ARMS:
        prefix = session / "profiles" / "nsys" / arm / workload.tag
        validate_execution(prefix, workload, expected_gpu)
        require_nonempty(prefix.with_suffix(".nsys-rep"))
        require_nonempty(prefix.with_suffix(".stats.csv"))
        status_path = prefix.with_suffix(".stats.status")
        require_nonempty(status_path)
        if read_status(status_path) != 0:
            raise GateError(f"nsys stats failed: {prefix}")


def parse_binary_hashes(session: Path) -> dict[str, str]:
    path = session / "binary-sha256.tsv"
    require_nonempty(path)
    hashes: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split("\t")
        if len(fields) != 2 or fields[0] not in ARMS or not re.fullmatch(r"[0-9a-f]{64}", fields[1]):
            raise GateError(f"malformed binary hash row in {path}: {line!r}")
        hashes[fields[0]] = fields[1]
    if set(hashes) != set(ARMS):
        raise GateError(f"{path}: expected hashes for {ARMS}, got {sorted(hashes)}")
    if len(set(hashes.values())) != 1:
        raise GateError(f"A/A binaries are not byte-identical: {hashes}")
    return hashes


def percentile(values: list[float], q: float) -> float:
    if not values:
        raise ValueError("empty percentile")
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def exact_paired_bootstrap_ratio(current: list[float], control: list[float]) -> tuple[float, float]:
    """Exact ordinary paired bootstrap for six observations (6^6 draws)."""
    if len(current) != len(control) or len(current) != 6:
        raise ValueError("the frozen design requires exactly six pairs")
    ratios: list[float] = []
    for indices in itertools.product(range(6), repeat=6):
        denominator = sum(control[i] for i in indices)
        if denominator <= 0:
            raise ValueError("non-positive control time")
        ratios.append(sum(current[i] for i in indices) / denominator)
    return percentile(ratios, 0.025), percentile(ratios, 0.975)


def rows_by_key(rows: Iterable[dict[str, Any]]) -> dict[tuple[str, int, str], dict[str, Any]]:
    out: dict[tuple[str, int, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["workload"].tag, row["round"], row["arm"])
        if key in out:
            raise GateError(f"duplicate execution cell {key}")
        out[key] = row
    return out


def exclusive_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def exclusive_jsonl(path: Path, values: Iterable[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        for value in values:
            stream.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def artifact_list(row: dict[str, Any], session: Path) -> list[dict[str, Any]]:
    out = []
    for artifact in row["artifacts"].values():
        path = Path(artifact["path"])
        out.append({
            "path": str(path.relative_to(session)),
            "sha256": artifact["sha256"],
            "bytes": artifact["bytes"],
        })
    return sorted(out, key=lambda item: item["path"])


def row_record(row: dict[str, Any], session: Path) -> dict[str, Any]:
    workload: Workload = row["workload"]
    report = row["report"]
    phase = row["phase"]
    round_index = row["round"]
    return {
        "schema": "gpu-aa-row/v1",
        "run_id": f"{session.name}-{phase}-r{round_index:02d}-{workload.tag}-{row['arm']}",
        "arm": row["arm"],
        "instance_id": workload.tag,
        "instance_role": workload.role,
        "replicate": round_index,
        "warmup": phase == "warmup",
        "seed": 0,
        "status": "verified",
        "outcome_class": "completed",
        "attempts": 1,
        "resumed": 0,
        "wall_valid": True,
        "measurements": {
            "upload_ms": row["upload_ms"],
            "device_ms": row["device_ms"],
            "download_ms": row["download_ms"],
            "rank": report["rank"],
            "refuted": report["refuted"],
            "pinned": report["pinned"],
            "word_ops": report["word_ops"],
            "rows": report["rows"],
            "cols": report["cols"],
        },
        "verification": {
            "status": "passed",
            "gate": "exact rank/refuted/pinned/word_ops and fixed matrix shape",
        },
        "host": {"manifest": "host.json"},
        "artifacts": artifact_list(row, session),
    }


def analyze(session: Path, expected_gpu: str) -> dict[str, Any]:
    validate_gpu_inventory(session, expected_gpu)
    hashes = parse_binary_hashes(session)
    warmups = gate_raw(session, "warmup", expected_gpu)
    measured = gate_raw(session, "measure", expected_gpu)
    gate_nsys(session, expected_gpu)
    keyed = rows_by_key(measured)

    cells: dict[str, Any] = {}
    for workload in WORKLOADS:
        current = [keyed[(workload.tag, r, "current")]["device_ms"] for r in MEASURED_ROUNDS]
        control = [keyed[(workload.tag, r, "control")]["device_ms"] for r in MEASURED_ROUNDS]
        pair_ratios = [a / b for a, b in zip(current, control)]
        ci_low, ci_high = exact_paired_bootstrap_ratio(current, control)
        cells[workload.tag] = {
            "role": workload.role,
            "rounds": list(MEASURED_ROUNDS),
            "current_device_ms": current,
            "control_device_ms": control,
            "current_median_ms": statistics.median(current),
            "control_median_ms": statistics.median(control),
            "paired_current_over_control": pair_ratios,
            "median_pair_ratio": statistics.median(pair_ratios),
            "ratio_of_sums": sum(current) / sum(control),
            "exact_paired_bootstrap_ratio_ci95": [ci_low, ci_high],
        }

    analysis = {
        "schema": "gpu-aa-nsys-analysis/v1",
        "scope": (
            "byte-identical current/control A/A calibration with post-timing "
            "Nsight Systems diagnostics; no candidate and no speedup claim"
        ),
        "session": session.name,
        "binary_sha256": hashes["current"],
        "byte_identical_arms": True,
        "warmup_executions": len(warmups),
        "measured_executions": len(measured),
        "measured_pairs": len(measured) // 2,
        "correctness_gate": "passed",
        "profiler_order": ["nsys"],
        "profiler_gate": "passed",
        "hardware_counters": "not collected; NCU is outside this protocol",
        "primary": "k0n13m2d6",
        "holdout": "k1n11m2d6",
        "cells": cells,
        "interpretation": (
            "The intervals quantify this session's A/A timing floor only. "
            "They neither establish equivalence nor license a performance claim."
        ),
    }
    rows = [row_record(row, session) for row in [*warmups, *measured]]
    exclusive_jsonl(session / "rows.jsonl", rows)
    exclusive_json(session / "analysis.json", analysis)
    return analysis


def command_plan(args: argparse.Namespace) -> int:
    if args.tsv:
        for workload in WORKLOADS:
            print("\t".join((workload.role, workload.tag, workload.cell, str(workload.degree))))
    else:
        print(json.dumps([w.__dict__ for w in WORKLOADS], sort_keys=True, indent=2))
    return 0


def command_gate(args: argparse.Namespace) -> int:
    session = args.session.resolve()
    validate_gpu_inventory(session, args.expected_gpu)
    parse_binary_hashes(session)
    if args.phase in ("warmup", "measure"):
        count = len(gate_raw(session, args.phase, args.expected_gpu))
    elif args.phase == "nsys":
        gate_nsys(session, args.expected_gpu)
        count = 2
    else:
        raise AssertionError(args.phase)
    print(json.dumps({"gate": "passed", "phase": args.phase, "executions": count}))
    return 0


def command_analyze(args: argparse.Namespace) -> int:
    result = analyze(args.session.resolve(), args.expected_gpu)
    print(json.dumps({
        "analysis": "written",
        "session": result["session"],
        "correctness_gate": result["correctness_gate"],
        "primary_ratio_ci95": result["cells"][result["primary"]]["exact_paired_bootstrap_ratio_ci95"],
    }, sort_keys=True))
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan", help="print the immutable five-cell plan")
    plan.add_argument("--tsv", action="store_true")
    plan.set_defaults(func=command_plan)
    gate = sub.add_parser("gate", help="check one completed runner phase")
    gate.add_argument("--session", type=Path, required=True)
    gate.add_argument("--phase", choices=("warmup", "measure", "nsys"), required=True)
    gate.add_argument("--expected-gpu", required=True)
    gate.set_defaults(func=command_gate)
    summary = sub.add_parser("analyze", help="gate everything and write final A/A artifacts")
    summary.add_argument("--session", type=Path, required=True)
    summary.add_argument("--expected-gpu", required=True)
    summary.set_defaults(func=command_analyze)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return args.func(args)
    except (GateError, OSError, ValueError) as exc:
        print(f"gpu A/A analysis refused: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
