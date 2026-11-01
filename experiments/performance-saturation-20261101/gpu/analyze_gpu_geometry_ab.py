#!/usr/bin/env python3
"""Gate and analyse the prospective RTX 5090 F4 update-grid A/B study.

The analyzer is deliberately the executable registry for the five matrices,
the exact answer oracle, the numeric isolation gate, the finite paired
bootstrap, the Nsight Systems mechanism check, and the experiment.export/v1
writer.  It uses only the Python standard library and never overwrites an
artifact.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import re
import sqlite3
import statistics
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable


ARMS = ("baseline", "candidate")
MEASURED_ROUNDS = tuple(range(1, 7))
EXPECTED_GPU = "NVIDIA GeForce RTX 5090"
PROTOCOL_ID = "gpu-f4-update-grid-ab-rtx5090-http-20261101"
PROTOCOL_VERSION = 8
PROTOCOL_RELATIVE = "../../protocol-http-rtx5090-geometry-v8.json"
ANALYZER_RELATIVE = "../../analyze_gpu_geometry_ab.py"
BASELINE_ORIGIN_COMMIT = "7c712913b7e912494e87c35e854cfd0129bad89c"
CANDIDATE_COMMIT = "59b6d7e17100d4d16db5d25c2762a5d5cf45ef4f"
BASELINE_F4_SHA256 = "da8c53c757cac0dfd81d1f75bfc5845610b645338215e52710efa11d57783944"
CANDIDATE_F4_SHA256 = "77832323d4d5a2b6b49fa2ca26fe40de1a80c0a8e17a9bb1949081a30fa84953"
PRODUCTION_DIFF_SHA256 = "34bf0033dd2bbd14b30ef2eaacaceb2d3bf9869504fca043585b1c78b48e43d3"
F4_PATH = "suite/src/cryptanalysis/f4_gpu.rs"
FAMILY_TESTS = 10
LOWER_TAIL = Fraction(1, 20 * FAMILY_TESTS)  # alpha=.05 / ten gates
PRIMARY_EFFECT = Fraction(51, 50)  # at least 1.02x baseline/candidate
NONREGRESSION = Fraction(50, 51)  # candidate no more than 2% slower
EXPECTED_UPDATE_LAUNCHES = 2941

VERBOSE_RE = re.compile(
    r"^F4_F2_ECHELON: .*? upload ([0-9]+(?:\.[0-9]+)?) ms, "
    r"device ([0-9]+(?:\.[0-9]+)?) ms, download ([0-9]+(?:\.[0-9]+)?) ms,"
    r" ([0-9.eE+-]+) word XORs$",
    re.MULTILINE,
)
CUDA_BACKEND_RE = re.compile(
    r"^cuda:(?P<gpu>[^\r\n]+?) sm_[0-9]+ x(?P<sms>[1-9][0-9]*) "
    r"code=(?:sm_[0-9]+|compute_[0-9]+|CA_F4_PTX)$"
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


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


WORKLOADS = (
    Workload("holdout", "k0n13m2d5", "0:13:2:1234", 5, "K_0/2^13", 2, 1234,
             30225, 53871, 27250, True, 0, 10745652033),
    Workload("holdout", "k0n9m3d5", "0:9:3:77", 5, "K_0/2^9", 3, 77,
             33147, 87118, 31069, False, 1, 1196809344),
    Workload("holdout", "k1n11m2d5", "1:11:2:301", 5, "K_1/2^11", 2, 301,
             14861, 21196, 12091, False, 0, 986408355),
    Workload("holdout", "k1n11m2d6", "1:11:2:301", 6, "K_1/2^11", 2, 301,
             68156, 60040, 46747, False, 0, 57968918179),
    Workload("primary", "k0n13m2d6", "0:13:2:1234", 6, "K_0/2^13", 2, 1234,
             168363, 188203, 130583, True, 0, 1110114894889),
)
BY_TAG = {workload.tag: workload for workload in WORKLOADS}


class GateError(RuntimeError):
    """An observed artifact violates a frozen gate."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(path: Path, base: Path, kind: str | None = None) -> dict[str, Any]:
    record: dict[str, Any] = {
        "path": str(path.relative_to(base)),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }
    if kind is not None:
        record["kind"] = kind
    return record


def require_nonempty(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise GateError(f"missing or empty artifact: {path}")


def load_json(path: Path) -> Any:
    require_nonempty(path)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GateError(f"invalid JSON {path}: {exc}") from exc


def read_status(path: Path) -> int:
    require_nonempty(path)
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError) as exc:
        raise GateError(f"invalid status {path}: {exc}") from exc


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


def validate_gpu_inventory(session: Path, expected_gpu: str) -> dict[str, str]:
    path = session / "metadata" / "gpu.csv"
    require_nonempty(path)
    try:
        with path.open(newline="", encoding="utf-8") as stream:
            rows = [row for row in csv.reader(stream) if any(field.strip() for field in row)]
    except (OSError, csv.Error) as exc:
        raise GateError(f"invalid GPU inventory {path}: {exc}") from exc
    if len(rows) != 1 or len(rows[0]) != 11 or any(not field.strip() for field in rows[0]):
        raise GateError(f"{path}: expected exactly one complete eleven-field GPU row")
    row = [field.strip() for field in rows[0]]
    if row[2] != expected_gpu:
        raise GateError(f"{path}: GPU={row[2]!r}, expected {expected_gpu!r}")
    return {"uuid": row[1], "name": row[2], "driver": row[5], "compute_cap": row[3]}


def validate_backend(value: object, expected_gpu: str) -> tuple[str, int]:
    if not isinstance(value, str):
        raise GateError(f"malformed CUDA backend {value!r}")
    match = CUDA_BACKEND_RE.fullmatch(value)
    if match is None or match.group("gpu") != expected_gpu:
        raise GateError(f"unexpected CUDA backend {value!r}")
    return value, int(match.group("sms"))


def validate_source_identities(session: Path) -> dict[str, Any]:
    value = load_json(session / "source-identities.json")
    expected = {
        "baseline_origin_commit": BASELINE_ORIGIN_COMMIT,
        "candidate_commit": CANDIDATE_COMMIT,
        "baseline_f4_sha256": BASELINE_F4_SHA256,
        "candidate_f4_sha256": CANDIDATE_F4_SHA256,
        "production_diff_sha256": PRODUCTION_DIFF_SHA256,
        "production_path": F4_PATH,
        "only_production_path_differs": True,
    }
    for key, wanted in expected.items():
        if value.get(key) != wanted:
            raise GateError(f"source identity {key}={value.get(key)!r}, expected {wanted!r}")
    archive_sha = value.get("candidate_archive_sha256")
    if not isinstance(archive_sha, str) or SHA256_RE.fullmatch(archive_sha) is None:
        raise GateError("source identity has no candidate archive SHA-256")
    return value


def parse_binary_hashes(session: Path) -> dict[str, str]:
    path = session / "binary-sha256.tsv"
    require_nonempty(path)
    hashes: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split("\t")
        if len(fields) != 2 or fields[0] not in ARMS or SHA256_RE.fullmatch(fields[1]) is None:
            raise GateError(f"malformed binary hash row: {line!r}")
        hashes[fields[0]] = fields[1]
    if set(hashes) != set(ARMS):
        raise GateError(f"missing binary hashes: {hashes}")
    if hashes["baseline"] == hashes["candidate"]:
        raise GateError("the two one-factor instruments unexpectedly have identical bytes")
    return hashes


def parse_psi_line(text: str, kind: str) -> dict[str, float]:
    for line in text.splitlines():
        fields = line.split()
        if fields and fields[0] == kind:
            out: dict[str, float] = {}
            for field in fields[1:]:
                key, value = field.split("=", 1)
                if key.startswith("avg"):
                    out[key] = float(value)
            if "avg10" not in out:
                break
            return out
    raise GateError(f"missing pressure {kind!r} line")


def capture_isolation() -> dict[str, Any]:
    """Capture one read-only cgroup/pressure/steal snapshot."""
    cgroup_rel = None
    for line in Path("/proc/self/cgroup").read_text(encoding="utf-8").splitlines():
        if line.startswith("0::"):
            cgroup_rel = line[3:]
            break
    if cgroup_rel is None:
        raise GateError("cgroup v2 unified path is unavailable")
    cgroup = Path("/sys/fs/cgroup") / cgroup_rel.lstrip("/")

    def key_values(path: Path) -> dict[str, int]:
        require_nonempty(path)
        out: dict[str, int] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            fields = line.split()
            if len(fields) == 2:
                out[fields[0]] = int(fields[1])
        return out

    cpu_pressure = Path("/proc/pressure/cpu").read_text(encoding="utf-8")
    memory_pressure = Path("/proc/pressure/memory").read_text(encoding="utf-8")
    cpu_line = Path("/proc/stat").read_text(encoding="utf-8").splitlines()[0].split()
    if not cpu_line or cpu_line[0] != "cpu" or len(cpu_line) < 9:
        raise GateError("malformed aggregate /proc/stat CPU line")
    return {
        "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cgroup": str(cgroup),
        "cpu_psi": {
            "some": parse_psi_line(cpu_pressure, "some"),
            "full": parse_psi_line(cpu_pressure, "full"),
        },
        "memory_psi": {
            "some": parse_psi_line(memory_pressure, "some"),
            "full": parse_psi_line(memory_pressure, "full"),
        },
        "cpu_stat": key_values(cgroup / "cpu.stat"),
        "memory_events": key_values(cgroup / "memory.events"),
        "steal_jiffies": int(cpu_line[8]),
    }


def validate_isolation(before_path: Path, after_path: Path) -> dict[str, Any]:
    before, after = load_json(before_path), load_json(after_path)
    if before.get("cgroup") != after.get("cgroup"):
        raise GateError("cgroup changed during an execution")
    for snap_name, snap in (("before", before), ("after", after)):
        if float(snap["cpu_psi"]["some"]["avg10"]) > 10.0:
            raise GateError(f"{snap_name} CPU PSI some avg10 exceeds 10")
        if float(snap["cpu_psi"]["full"]["avg10"]) != 0.0:
            raise GateError(f"{snap_name} CPU PSI full avg10 is nonzero")
        for kind in ("some", "full"):
            if float(snap["memory_psi"][kind]["avg10"]) != 0.0:
                raise GateError(f"{snap_name} memory PSI {kind} avg10 is nonzero")
    deltas: dict[str, int] = {}
    for field in ("nr_throttled", "throttled_usec"):
        delta = int(after["cpu_stat"].get(field, 0)) - int(before["cpu_stat"].get(field, 0))
        deltas[f"cpu.{field}"] = delta
        if delta != 0:
            raise GateError(f"cgroup CPU throttling changed: {field}={delta}")
    for field in ("high", "max", "oom", "oom_kill", "oom_group_kill"):
        delta = int(after["memory_events"].get(field, 0)) - int(before["memory_events"].get(field, 0))
        deltas[f"memory.{field}"] = delta
        if delta != 0:
            raise GateError(f"cgroup memory event changed: {field}={delta}")
    steal_delta = int(after["steal_jiffies"]) - int(before["steal_jiffies"])
    deltas["steal_jiffies"] = steal_delta
    if steal_delta != 0:
        raise GateError(f"aggregate CPU steal changed by {steal_delta} jiffies")
    return {"tier": "tierB", "contended": False, "deltas": deltas}


def validate_smi(path: Path, gpu_uuid: str) -> dict[str, Any]:
    require_nonempty(path)
    with path.open(newline="", encoding="utf-8") as stream:
        try:
            rows = list(csv.DictReader(stream))
        except csv.Error as exc:
            raise GateError(f"malformed telemetry {path}: {exc}") from exc
    if not rows:
        raise GateError(f"no GPU telemetry samples in {path}")
    temperatures: list[float] = []
    pstates: set[str] = set()
    for row in rows:
        observed_uuid = (row.get("uuid") or "").strip()
        if observed_uuid != gpu_uuid:
            raise GateError(f"{path}: telemetry UUID {observed_uuid!r} != {gpu_uuid!r}")
        temperatures.append(float((row.get("temperature.gpu") or "nan").strip()))
        pstates.add((row.get("pstate") or "").strip())
    if not all(math.isfinite(value) and value < 90.0 for value in temperatures):
        raise GateError(f"{path}: invalid or >=90C GPU temperature")
    if "" in pstates:
        raise GateError(f"{path}: missing GPU pstate")
    return {"samples": len(rows), "max_temperature_c": max(temperatures), "pstates": sorted(pstates)}


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


def validate_execution(prefix: Path, workload: Workload, gpu: dict[str, str]) -> dict[str, Any]:
    suffixes = (
        ".json", ".log", ".smi.csv", ".status", ".started-at", ".finished-at",
        ".isolation-before.json", ".isolation-after.json",
    )
    paths = [prefix.parent / f"{prefix.name}{suffix}" for suffix in suffixes]
    for path in paths:
        require_nonempty(path)
    if read_status(prefix.parent / f"{prefix.name}.status") != 0:
        raise GateError(f"execution failed: {prefix}")
    report = load_json(prefix.parent / f"{prefix.name}.json")
    for field, expected in expected_fields(workload).items():
        if report.get(field) != expected:
            raise GateError(f"{prefix}: {field}={report.get(field)!r}, expected {expected!r}")
    if report.get("echelon_mode") != "cuda":
        raise GateError(f"{prefix}: not forced through CUDA")
    backend, sm_count = validate_backend(report.get("echelon_backend"), gpu["name"])
    log_path = prefix.parent / f"{prefix.name}.log"
    matches = list(VERBOSE_RE.finditer(log_path.read_text(encoding="utf-8", errors="replace")))
    if len(matches) != 1:
        raise GateError(f"{log_path}: expected one verbose timing line, found {len(matches)}")
    upload, device, download = (Fraction(value) for value in matches[0].groups()[:3])
    if min(upload, device, download) < 0:
        raise GateError(f"{log_path}: negative timing")
    isolation = validate_isolation(
        prefix.parent / f"{prefix.name}.isolation-before.json",
        prefix.parent / f"{prefix.name}.isolation-after.json",
    )
    telemetry = validate_smi(prefix.parent / f"{prefix.name}.smi.csv", gpu["uuid"])
    return {
        "prefix": prefix,
        "report": report,
        "backend": backend,
        "sm_count": sm_count,
        "upload_ms": upload,
        "device_ms": device,
        "download_ms": download,
        "complete_ms": upload + device + download,
        "isolation": isolation,
        "telemetry": telemetry,
        "artifacts": paths,
    }


def raw_prefix(session: Path, phase: str, round_index: int, tag: str, arm: str) -> Path:
    return session / "raw" / phase / f"r{round_index:02d}" / tag / arm


def gate_raw(session: Path, phase: str, expected_gpu: str) -> list[dict[str, Any]]:
    rounds = (0,) if phase == "warmup" else MEASURED_ROUNDS if phase == "measure" else None
    if rounds is None:
        raise GateError(f"unknown raw phase {phase!r}")
    gpu = validate_gpu_inventory(session, expected_gpu)
    rows: list[dict[str, Any]] = []
    for round_index in rounds:
        for workload in WORKLOADS:
            for arm in ARMS:
                observed = validate_execution(
                    raw_prefix(session, phase, round_index, workload.tag, arm), workload, gpu
                )
                rows.append({
                    "phase": phase,
                    "round": round_index,
                    "workload": workload,
                    "arm": arm,
                    **observed,
                })
    return rows


def median_fraction(values: Iterable[Fraction]) -> Fraction:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("median of empty values")
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def simultaneous_lower(baseline: list[Fraction], candidate: list[Fraction]) -> Fraction:
    if len(baseline) != 6 or len(candidate) != 6:
        raise ValueError("the frozen design requires exactly six pairs")
    if min(candidate) <= 0:
        raise ValueError("candidate timing is non-positive")
    ratios = [base / cand for base, cand in zip(baseline, candidate)]
    distribution = [
        median_fraction(ratios[index] for index in indices)
        for indices in itertools.product(range(6), repeat=6)
    ]
    distribution.sort()
    index = (len(distribution) * LOWER_TAIL.numerator) // LOWER_TAIL.denominator
    return distribution[index]


def fraction_record(value: Fraction) -> dict[str, Any]:
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "decimal": format(float(value), ".17g"),
    }


def kernel_rows(path: Path) -> list[dict[str, Any]]:
    require_nonempty(path)
    try:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        query = """
            SELECT k.start, s.value AS name, k.gridX, k.gridY, k.gridZ,
                   k.blockX, k.blockY, k.blockZ, k.registersPerThread,
                   k.staticSharedMemory, k.dynamicSharedMemory,
                   k.localMemoryPerThread
            FROM CUPTI_ACTIVITY_KIND_KERNEL AS k
            JOIN StringIds AS s ON k.shortName = s.id
            ORDER BY k.start
        """
        rows = [dict(row) for row in connection.execute(query)]
        connection.close()
    except sqlite3.Error as exc:
        raise GateError(f"cannot read Nsys SQLite {path}: {exc}") from exc
    if not rows:
        raise GateError(f"no CUDA kernels in {path}")
    return rows


def parts_for(sm_count: int, tiles: int, blocks_per_sm: int) -> int:
    return max(1, min(32, (blocks_per_sm * sm_count + tiles - 1) // tiles))


def infer_tile_candidates(materialise_grid: int, update_grid: int, sm_count: int) -> tuple[int, ...]:
    candidates = []
    for tiles in range(max(1, 4 * materialise_grid - 3), 4 * materialise_grid + 1):
        if tiles * parts_for(sm_count, tiles, 4) == update_grid:
            candidates.append(tiles)
    if not candidates:
        raise GateError(
            f"cannot infer any word-tile count from materialise={materialise_grid}, "
            f"baseline update={update_grid}, sm_count={sm_count}"
        )
    return tuple(candidates)


def infer_tiles(materialise_grid: int, update_grid: int, sm_count: int) -> int:
    """Return the tile count only when the baseline trace determines it uniquely."""
    candidates = infer_tile_candidates(materialise_grid, update_grid, sm_count)
    if len(candidates) != 1:
        raise GateError(
            f"word tiles are ambiguous for materialise={materialise_grid}, "
            f"baseline update={update_grid}, sm_count={sm_count}: {list(candidates)}"
        )
    return candidates[0]


def validate_update_resource(row: dict[str, Any]) -> None:
    expected = {
        "blockX": 256,
        "blockY": 1,
        "blockZ": 1,
        "registersPerThread": 31,
        "staticSharedMemory": 16384,
        "dynamicSharedMemory": 0,
        "localMemoryPerThread": 0,
    }
    for field, value in expected.items():
        if row[field] != value:
            raise GateError(f"f4e_update {field}={row[field]}, expected {value}")


def mechanism_gate(baseline_path: Path, candidate_path: Path, sm_count: int) -> dict[str, Any]:
    baseline, candidate = kernel_rows(baseline_path), kernel_rows(candidate_path)
    expected_total = EXPECTED_UPDATE_LAUNCHES * 4 + 1
    if len(baseline) != expected_total or len(candidate) != expected_total:
        raise GateError(
            f"expected {expected_total} kernels per trace, got {len(baseline)} and {len(candidate)}"
        )
    expected_names = ["f4e_gather", "f4e_panel_block", "f4e_materialise", "f4e_update"]
    transitions: dict[str, int] = {}
    changed = 0
    for launch in range(EXPECTED_UPDATE_LAUNCHES):
        offset = launch * 4
        bgroup, cgroup = baseline[offset:offset + 4], candidate[offset:offset + 4]
        if [row["name"] for row in bgroup] != expected_names:
            raise GateError(f"baseline kernel order differs at update launch {launch}")
        if [row["name"] for row in cgroup] != expected_names:
            raise GateError(f"candidate kernel order differs at update launch {launch}")
        for index in range(3):
            fields = (
                "name", "gridX", "gridY", "gridZ", "blockX", "blockY", "blockZ",
                "registersPerThread", "staticSharedMemory", "dynamicSharedMemory",
                "localMemoryPerThread",
            )
            if tuple(bgroup[index][field] for field in fields) != tuple(
                cgroup[index][field] for field in fields
            ):
                raise GateError(f"non-update kernel geometry/resource differs at launch {launch}")
        bupdate, cupdate = bgroup[3], cgroup[3]
        validate_update_resource(bupdate)
        validate_update_resource(cupdate)
        remaining_words = EXPECTED_UPDATE_LAUNCHES - launch
        expected_materialise = (remaining_words + 127) // 128
        tiles = (remaining_words + 31) // 32
        expected_baseline = tiles * parts_for(sm_count, tiles, 4)
        expected_candidate = tiles * parts_for(sm_count, tiles, 6)
        if bgroup[2]["gridX"] != expected_materialise:
            raise GateError(
                f"materialise grid mismatch at launch {launch}: "
                f"{bgroup[2]['gridX']} != {expected_materialise}"
            )
        if bupdate["gridX"] != expected_baseline or cupdate["gridX"] != expected_candidate:
            raise GateError(
                f"update grid mismatch at launch {launch}: tiles={tiles}, "
                f"baseline={bupdate['gridX']}/{expected_baseline}, "
                f"candidate={cupdate['gridX']}/{expected_candidate}"
            )
        if cupdate["gridX"] < bupdate["gridX"]:
            raise GateError(f"candidate update grid shrank at launch {launch}")
        if cupdate["gridX"] > bupdate["gridX"]:
            changed += 1
        key = f"{tiles}:{bupdate['gridX']}->{cupdate['gridX']}"
        transitions[key] = transitions.get(key, 0) + 1
    if baseline[-1]["name"] != "f4e_low" or candidate[-1]["name"] != "f4e_low":
        raise GateError("the final f4e_low launch is missing")
    fields = (
        "name", "gridX", "gridY", "gridZ", "blockX", "blockY", "blockZ",
        "registersPerThread", "staticSharedMemory", "dynamicSharedMemory",
        "localMemoryPerThread",
    )
    if tuple(baseline[-1][field] for field in fields) != tuple(candidate[-1][field] for field in fields):
        raise GateError("final f4e_low geometry/resource differs")
    if changed == 0:
        raise GateError("the candidate did not change any update launch grid")
    return {
        "status": "passed",
        "sm_count": sm_count,
        "update_launches_per_arm": EXPECTED_UPDATE_LAUNCHES,
        "changed_update_launches": changed,
        "unchanged_update_launches": EXPECTED_UPDATE_LAUNCHES - changed,
        "transitions": dict(sorted(transitions.items())),
        "resources": {
            "threads_per_block": 256,
            "registers_per_thread": 31,
            "static_shared_bytes": 16384,
            "dynamic_shared_bytes": 0,
            "local_bytes_per_thread": 0,
        },
    }


def gate_nsys(session: Path, expected_gpu: str) -> dict[str, Any]:
    gpu = validate_gpu_inventory(session, expected_gpu)
    observations: dict[str, dict[str, Any]] = {}
    sm_counts: set[int] = set()
    for arm in ARMS:
        prefix = session / "profiles" / "nsys" / arm / "k0n13m2d6"
        observed = validate_execution(prefix, BY_TAG["k0n13m2d6"], gpu)
        observations[arm] = observed
        sm_counts.add(observed["sm_count"])
        for suffix in (".nsys-rep", ".sqlite", ".stats.csv", ".stats.status"):
            require_nonempty(prefix.parent / f"{prefix.name}{suffix}")
        if read_status(prefix.parent / f"{prefix.name}.stats.status") != 0:
            raise GateError(f"Nsys stats failed: {prefix}")
    if len(sm_counts) != 1:
        raise GateError(f"Nsys arms observed different SM counts: {sm_counts}")
    return mechanism_gate(
        session / "profiles" / "nsys" / "baseline" / "k0n13m2d6.sqlite",
        session / "profiles" / "nsys" / "candidate" / "k0n13m2d6.sqlite",
        sm_counts.pop(),
    )


def keyed_rows(rows: Iterable[dict[str, Any]]) -> dict[tuple[str, int, str], dict[str, Any]]:
    out: dict[tuple[str, int, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["workload"].tag, row["round"], row["arm"])
        if key in out:
            raise GateError(f"duplicate execution cell {key}")
        out[key] = row
    return out


def row_artifacts(row: dict[str, Any], session: Path) -> list[dict[str, Any]]:
    return sorted(
        (file_record(path, session, "raw") for path in row["artifacts"]),
        key=lambda item: item["path"],
    )


def row_record(row: dict[str, Any], session: Path) -> dict[str, Any]:
    workload: Workload = row["workload"]
    warmup = row["phase"] == "warmup"
    replicate = 0 if warmup else row["round"] - 1
    prefix: Path = row["prefix"]
    started = (prefix.parent / f"{prefix.name}.started-at").read_text(encoding="utf-8").strip()
    finished = (prefix.parent / f"{prefix.name}.finished-at").read_text(encoding="utf-8").strip()
    report = row["report"]
    return {
        "run_id": f"{session.name}-{row['phase']}-r{row['round']:02d}-{workload.tag}-{row['arm']}",
        "arm": row["arm"],
        "instance_id": workload.tag,
        "seed": 0,
        "replicate": replicate,
        "warmup": warmup,
        "status": "succeeded",
        "outcome_class": "completed",
        "attempts": 1,
        "resumed": 0,
        "checkpoint": None,
        "measurements": {
            "counted": {
                "word_ops": str(report["word_ops"]),
                "rank": report["rank"],
                "refuted": 1 if report["refuted"] else 0,
                "pinned": report["pinned"],
                "rows": report["rows"],
                "cols": report["cols"],
            },
            "wall_seconds": float(row["complete_ms"] / 1000),
            "wall_valid": not warmup,
            "cpu_user_seconds": None,
            "cpu_sys_seconds": None,
            "max_rss_bytes": None,
            "counters": {
                "upload_ms": float(row["upload_ms"]),
                "device_ms": float(row["device_ms"]),
                "download_ms": float(row["download_ms"]),
                "complete_ms": float(row["complete_ms"]),
                "gpu_telemetry_samples": row["telemetry"]["samples"],
                "gpu_max_temperature_c": row["telemetry"]["max_temperature_c"],
            },
        },
        "isolation": {"tier": "tierB", "contended": False, "blockers": []},
        "verification": {
            "status": "verified",
            "verifier": "exact matrix shape/rank/refuted/pinned/word_ops plus forced CUDA backend",
        },
        "exclusion": {"excluded": False, "rule": None},
        "artifacts": row_artifacts(row, session),
        "started_at": started,
        "finished_at": finished,
        "worker": None,
        "backend_ref": None,
    }


def write_export(
    session: Path,
    protocol_sha256: str,
    hashes: dict[str, str],
    rows: list[dict[str, Any]],
    analysis_path: Path,
) -> dict[str, Any]:
    host_path = session / "host.json"
    host = load_json(host_path)
    gpu = validate_gpu_inventory(session, EXPECTED_GPU)
    analysis_script = (session / ANALYZER_RELATIVE).resolve()
    require_nonempty(analysis_script)
    files = [
        file_record(session / "rows.jsonl", session, "raw"),
        file_record(session / "order.tsv", session, "raw"),
        file_record(session / "binary-sha256.tsv", session, "summary"),
        file_record(session / "source-identities.json", session, "summary"),
        file_record(session / "metadata" / "gpu.csv", session, "host"),
    ]
    return {
        "schema": "experiment.export/v1",
        "export_id": f"{session.name}-export",
        "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "protocol": {
            "path": PROTOCOL_RELATIVE,
            "sha256": protocol_sha256,
            "protocol_id": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
        },
        "producer": {
            "runtime": "runpod-http-batch",
            "model": None,
            "session": session.name,
            "role": "executor",
        },
        "source": {"repo": "cryptanalysis", "commit": CANDIDATE_COMMIT, "dirty": False},
        "backend": "runpod",
        "host": {
            "path": "host.json",
            "sha256": sha256_file(host_path),
            "class_id": host.get("machine_id"),
            "summary": {
                "cpu_model": host.get("cpu_model"),
                "logical_cpus": host.get("logical_cpus"),
                "memory_bytes": host.get("memory_bytes"),
                "kernel": host.get("kernel"),
                "hypervisor": "Runpod Secure Cloud",
                "isolation_tier_max": "tierB",
                "gpu": gpu["name"],
                "instance_type": host.get("machine_id"),
                "spot": False,
            },
        },
        "arms": [
            {"id": arm, "role": arm, "binary_sha256": hashes[arm], "commit": CANDIDATE_COMMIT}
            for arm in ARMS
        ],
        "runs": rows,
        "flow": {
            "planned": len(rows),
            "attempted": len(rows),
            "completed": len(rows),
            "not_completed": 0,
            "interrupted": 0,
            "resumed": 0,
            "excluded": [],
        },
        "files": files,
        "analysis": {
            "script": file_record(analysis_script, session, "analysis"),
            "blinded": False,
            "blinding_key_sha256": None,
            "outputs": [file_record(analysis_path, session, "analysis")],
            "unmasked_at": None,
        },
        "notes": [
            {
                "kind": "observation",
                "text": "wall_seconds is the charged upload+device+download F4 stage, not process lifetime; profiled durations are excluded.",
                "by": "frozen analyzer",
            }
        ],
        "reviews_dir": "reviews",
    }


def analyze(session: Path, expected_gpu: str, protocol_sha256: str) -> dict[str, Any]:
    if SHA256_RE.fullmatch(protocol_sha256) is None:
        raise GateError("protocol SHA-256 is malformed")
    validate_gpu_inventory(session, expected_gpu)
    validate_source_identities(session)
    hashes = parse_binary_hashes(session)
    warmups = gate_raw(session, "warmup", expected_gpu)
    measured = gate_raw(session, "measure", expected_gpu)
    mechanism = gate_nsys(session, expected_gpu)
    keyed = keyed_rows(measured)

    cells: dict[str, Any] = {}
    gates: list[dict[str, Any]] = []
    for workload in WORKLOADS:
        metrics: dict[str, Any] = {}
        for metric in ("device_ms", "complete_ms"):
            baseline = [keyed[(workload.tag, round_index, "baseline")][metric]
                        for round_index in MEASURED_ROUNDS]
            candidate = [keyed[(workload.tag, round_index, "candidate")][metric]
                         for round_index in MEASURED_ROUNDS]
            pair_ratios = [base / cand for base, cand in zip(baseline, candidate)]
            observed = median_fraction(pair_ratios)
            lower = simultaneous_lower(baseline, candidate)
            metrics[metric] = {
                "baseline_ms": [format(float(value), ".17g") for value in baseline],
                "candidate_ms": [format(float(value), ".17g") for value in candidate],
                "paired_baseline_over_candidate": [fraction_record(value) for value in pair_ratios],
                "median_pair_speedup": fraction_record(observed),
                "simultaneous_one_sided_lower": fraction_record(lower),
                "bootstrap_resamples": 6 ** 6,
                "lower_tail_probability": fraction_record(LOWER_TAIL),
            }
            decisive = (workload.role == "primary" and metric == "device_ms") or metric == "complete_ms" or workload.role == "holdout"
            if decisive:
                threshold = PRIMARY_EFFECT if workload.role == "primary" and metric == "device_ms" else NONREGRESSION
                passed = (observed >= threshold and lower > 1) if threshold == PRIMARY_EFFECT else (
                    observed >= threshold and lower >= threshold
                )
                gates.append({
                    "workload": workload.tag,
                    "metric": metric,
                    "kind": "primary_improvement" if threshold == PRIMARY_EFFECT else "nonregression",
                    "threshold": fraction_record(threshold),
                    "median": fraction_record(observed),
                    "lower": fraction_record(lower),
                    "passed": passed,
                })
        cells[workload.tag] = {"role": workload.role, "metrics": metrics}
    if len(gates) != FAMILY_TESTS:
        raise GateError(f"internal decision family has {len(gates)} gates, expected {FAMILY_TESTS}")
    verdict = "geometry_supported" if all(gate["passed"] for gate in gates) else "geometry_not_supported"
    analysis = {
        "schema": "gpu-f4-update-grid-ab-analysis/v1",
        "protocol_sha256": protocol_sha256,
        "session": session.name,
        "verdict": verdict,
        "correctness_gate": "passed",
        "source_identity_gate": "passed",
        "numeric_isolation_gate": "passed",
        "mechanism_gate": mechanism,
        "multiplicity": {
            "family_tests": FAMILY_TESTS,
            "family_alpha": "0.05",
            "correction": "Bonferroni",
            "one_sided_lower_tail": fraction_record(LOWER_TAIL),
        },
        "decision_gates": gates,
        "cells": cells,
        "profiled_timings_in_decision": False,
        "hardware_counters": "not collected; NCU is outside this protocol",
    }
    rows = [row_record(row, session) for row in [*warmups, *measured]]
    rows_path = session / "rows.jsonl"
    analysis_path = session / "analysis.json"
    exclusive_jsonl(rows_path, rows)
    exclusive_json(analysis_path, analysis)
    export = write_export(session, protocol_sha256, hashes, rows, analysis_path)
    exclusive_json(session / "export.json", export)
    return analysis


def command_plan(args: argparse.Namespace) -> int:
    if args.tsv:
        for workload in WORKLOADS:
            print("\t".join((workload.role, workload.tag, workload.cell, str(workload.degree))))
    else:
        print(json.dumps([workload.__dict__ for workload in WORKLOADS], sort_keys=True, indent=2))
    return 0


def command_snapshot(args: argparse.Namespace) -> int:
    exclusive_json(args.out, capture_isolation())
    return 0


def command_gate(args: argparse.Namespace) -> int:
    session = args.session.resolve()
    validate_source_identities(session)
    parse_binary_hashes(session)
    if args.phase in ("warmup", "measure"):
        count = len(gate_raw(session, args.phase, args.expected_gpu))
        extra: dict[str, Any] = {}
    else:
        extra = gate_nsys(session, args.expected_gpu)
        count = 2
    print(json.dumps({"gate": "passed", "phase": args.phase, "executions": count, **extra}, sort_keys=True))
    return 0


def command_analyze(args: argparse.Namespace) -> int:
    analysis = analyze(args.session.resolve(), args.expected_gpu, args.protocol_sha256)
    print(json.dumps({
        "analysis": "written",
        "export": "written",
        "session": analysis["session"],
        "verdict": analysis["verdict"],
    }, sort_keys=True))
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan", help="print the immutable five-cell plan")
    plan.add_argument("--tsv", action="store_true")
    plan.set_defaults(func=command_plan)
    snapshot = sub.add_parser("snapshot-isolation", help="write one isolation snapshot")
    snapshot.add_argument("--out", type=Path, required=True)
    snapshot.set_defaults(func=command_snapshot)
    gate = sub.add_parser("gate", help="check one completed phase")
    gate.add_argument("--session", type=Path, required=True)
    gate.add_argument("--phase", choices=("warmup", "measure", "nsys"), required=True)
    gate.add_argument("--expected-gpu", default=EXPECTED_GPU)
    gate.set_defaults(func=command_gate)
    summary = sub.add_parser("analyze", help="gate all artifacts and write analysis/export")
    summary.add_argument("--session", type=Path, required=True)
    summary.add_argument("--expected-gpu", default=EXPECTED_GPU)
    summary.add_argument("--protocol-sha256", required=True)
    summary.set_defaults(func=command_analyze)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return args.func(args)
    except (GateError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"GPU geometry A/B analysis refused: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
