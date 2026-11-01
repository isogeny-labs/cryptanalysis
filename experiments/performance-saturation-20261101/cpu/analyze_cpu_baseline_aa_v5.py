#!/usr/bin/env python3
"""Frozen analysis/exporter for the CPU baseline A/A v5 campaign."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import re
import secrets
import statistics
import subprocess
from typing import Any

import run_cpu_baseline_aa_v5 as runner


TOOL_PATH = Path("/workspace/crypto-autoresearcher/tools/experiment_protocol.py")
SPEC = importlib.util.spec_from_file_location("cpu_v5_experiment_protocol", TOOL_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load canonical experiment protocol tool")
tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tool)

RUST_SCHEDULE_SHA256 = "70e0ae24634d5e2bd5374d350502a52f18c560654202d8bfd8e04cedf145a86d"
C_SCHEDULE_SHA256 = "4fcd6f17862034e515a7064f498388a5e01578f2b7cb84b8051de55636bf0864"
WEIGHTS_PATH = runner.REPO / "docs/perf/weights.json"
HOST_IDENTITY_FIELDS = ("cpu", "cpu_flags", "logical_cores", "memory", "os", "arch", "rustc")


def load_frozen_perfindex():
    spec = importlib.util.spec_from_file_location("cpu_v5_perfindex", runner.PERFINDEX)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the frozen perfindex implementation")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def write_json_once(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            observed = load_json(path)
        except (OSError, ValueError, json.JSONDecodeError):
            observed = None
        if observed is not None and observed == value:
            return
    data = (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    ).encode("utf-8")
    atomic_publish(path, data)


def write_text_once(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text(encoding="utf-8", errors="replace") == value:
            return
    atomic_publish(path, value.encode("utf-8"))


def atomic_publish(path: Path, data: bytes) -> None:
    """Fsync a derived artifact, then atomically publish its final pathname."""
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}-{secrets.token_hex(8)}")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        offset = 0
        while offset < len(data):
            offset += os.write(descriptor, data[offset:])
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    try:
        os.replace(temporary, path)
    except BaseException:
        try:
            temporary.unlink()
        except OSError:
            pass
        raise
    parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(parent)
    finally:
        os.close(parent)


def verify_protocol(path: Path) -> dict[str, Any]:
    protocol = load_json(path)
    runner.verify_bootstrap_identity(protocol)
    subprocess.run(
        runner.closed_python_command(TOOL_PATH, "validate", str(path)),
        check=True, timeout=60,
    )
    freeze = protocol["freeze"]
    observed = subprocess.check_output(
        runner.closed_python_command(TOOL_PATH, "hash", str(path)),
        text=True, timeout=60,
    ).strip()
    if freeze["status"] != "frozen" or observed != freeze["protocol_sha256"]:
        raise ValueError("protocol freeze/hash mismatch")
    script = protocol["analysis_plan"]["script"]
    if script["sha256"] != sha256(Path(__file__).resolve()):
        raise ValueError("analysis script differs from frozen SHA-256")
    ext = protocol["extensions"]["cpu_baseline_aa_v5"]
    if ext["runner_sha256"] != sha256(runner.RUNNER):
        raise ValueError("runner differs from frozen SHA-256")
    return protocol


def parse_utc(value: Any) -> dt.datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0):
        return None
    return parsed


def validate_benchmark_row(
    row: Any, kernel: str, round_index: int | None = None,
    expected_samples: int | None = None,
) -> list[str]:
    findings: list[str] = []
    if not isinstance(row, dict):
        return ["benchmark row is not an object"]
    if row.get("id") != kernel:
        findings.append("benchmark row ID differs from the planned kernel")
    if round_index is not None and row.get("round") != round_index:
        findings.append("benchmark row round differs from the planned round")
    fingerprint = row.get("fingerprint")
    if not isinstance(fingerprint, str) or not fingerprint:
        findings.append("benchmark row lacks an exact output fingerprint")
    samples = row.get("samples_ns")
    median = row.get("median_ns")
    if (
        not isinstance(samples, list) or not 3 <= len(samples) <= 5
        or any(not isinstance(value, int) or isinstance(value, bool) or value <= 0 for value in samples)
    ):
        findings.append("benchmark row samples_ns is not 3..5 positive integer samples")
    elif expected_samples is not None and len(samples) != expected_samples:
        findings.append(f"benchmark row has {len(samples)} samples, expected {expected_samples}")
    elif (
        not isinstance(median, (int, float)) or isinstance(median, bool)
        or median <= 0 or median != statistics.median(samples)
    ):
        findings.append("benchmark row median_ns differs from samples_ns")
    return findings


def parse_single_benchmark_stdout(text: Any) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(text, str):
        return None, "captured stdout is not text"
    rows: list[dict[str, Any]] = []
    try:
        for line in text.splitlines():
            if line.startswith("{"):
                value = json.loads(line)
                if not isinstance(value, dict):
                    return None, "captured JSON row is not an object"
                rows.append(value)
    except json.JSONDecodeError as error:
        return None, f"captured stdout JSON is malformed: {error}"
    if len(rows) != 1:
        return None, f"captured stdout has {len(rows)} JSON rows, expected exactly one"
    return rows[0], None


def expected_schedule(ids: tuple[str, ...]) -> list[dict[str, Any]]:
    import random

    rng = random.Random(20260926)
    kernels = sorted(ids)
    result: list[dict[str, Any]] = []
    for round_index in range(1, 7):
        order = kernels[:]
        rng.shuffle(order)
        arms = ["A", "B"] if round_index % 2 == 1 else ["B", "A"]
        for kernel in order:
            result.append({"arms": arms, "id": kernel, "round": round_index})
    return result


def parse_observed_schedule(stderr: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    pattern = re.compile(r"^round (\d+)/6 ([^:]+): ((?:A|B)=.+)$")
    for line in stderr.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match is None:
            continue
        arms = [field.split("=", 1)[0] for field in match.group(3).split()]
        rows.append({"arms": arms, "id": match.group(2), "round": int(match.group(1))})
    return rows


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"expected JSON objects in {path}")
        rows.append(value)
    return rows


def load_jsonl_with_trailing_partial(path: Path) -> tuple[list[dict[str, Any]], bool]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    rows: list[dict[str, Any]] = []
    trailing_partial = False
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            if index == len(lines) - 1:
                trailing_partial = True
                break
            raise
        if not isinstance(value, dict):
            raise ValueError(f"expected JSON objects in {path}")
        rows.append(value)
    return rows, trailing_partial


def isolation_path(record: dict[str, Any]) -> Path:
    argv = record["argv"]
    index = argv.index("--out")
    return Path(argv[index + 1])


def child_argv(record: dict[str, Any]) -> list[str]:
    argv = record["argv"]
    return argv[argv.index("--") + 1:]


def validate_attempt(run_root: Path, relative: str, expected: dict[str, Any],
                     require_zero: bool) -> tuple[int | None, list[str], list[str]]:
    """Return (status, provenance findings, completeness/operational findings)."""
    directory = run_root / "orchestration/attempts" / relative
    receipt_path = directory / "receipt.json"
    started_path = directory / "started.json"
    stdout_path = directory / "stdout.txt"
    stderr_path = directory / "stderr.txt"
    provenance: list[str] = []
    incomplete: list[str] = []
    if not started_path.is_file():
        if receipt_path.exists() or stdout_path.exists() or stderr_path.exists():
            provenance.append(f"{relative}: outer receipt/stream exists without a durable start")
        else:
            incomplete.append(f"{relative}: outer attempt was not started")
    else:
        try:
            started = load_json(started_path)
            if (
                started.get("schema") != "cpu-baseline-aa-v5-attempt-start/v1"
                or started.get("record") != expected
                or parse_utc(started.get("started_at")) is None
            ):
                provenance.append(f"{relative}: durable outer attempt start mismatch")
        except (OSError, ValueError, json.JSONDecodeError) as error:
            provenance.append(f"{relative}: malformed durable outer attempt start: {error}")
    if not receipt_path.is_file() or not stdout_path.is_file() or not stderr_path.is_file():
        return None, provenance, [f"{relative}: missing outer attempt receipt or stream"]
    try:
        receipt = load_json(receipt_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return None, [f"{relative}: malformed outer receipt: {error}"], incomplete
    if receipt.get("schema") != "cpu-baseline-aa-v5-attempt/v1" or receipt.get("record") != expected:
        provenance.append(f"{relative}: outer command record mismatch")
    launched_path = directory / "launched.json"
    if receipt.get("launch_error") is None:
        if not launched_path.is_file():
            provenance.append(f"{relative}: completed outer attempt lacks launch PID/PGID receipt")
        else:
            try:
                launched = load_json(launched_path)
            except (OSError, ValueError, json.JSONDecodeError) as error:
                provenance.append(f"{relative}: malformed launch PID/PGID receipt: {error}")
            else:
                if (
                    launched.get("schema") != "cpu-baseline-aa-v5-attempt-launch/v1"
                    or launched.get("record") != expected
                    or launched.get("started_at") != receipt.get("started_at")
                    or not isinstance(launched.get("pid"), int) or launched["pid"] <= 0
                    or not isinstance(launched.get("process_group"), int)
                    or launched["process_group"] <= 0
                ):
                    provenance.append(f"{relative}: launch PID/PGID receipt mismatch")
    started_at = parse_utc(receipt.get("started_at"))
    finished_at = parse_utc(receipt.get("finished_at"))
    if started_at is None or finished_at is None or finished_at < started_at:
        provenance.append(f"{relative}: invalid outer attempt timestamps")
    elif started_path.is_file():
        try:
            if load_json(started_path).get("started_at") != receipt.get("started_at"):
                provenance.append(f"{relative}: outer start/finish timestamp binding differs")
        except (ValueError, json.JSONDecodeError):
            pass
    if receipt.get("stdout_sha256") != sha256(stdout_path) or receipt.get("stderr_sha256") != sha256(stderr_path):
        provenance.append(f"{relative}: captured stream hash mismatch")
    status = receipt.get("returncode")
    if not isinstance(status, int):
        provenance.append(f"{relative}: invalid returncode")
        status = None
    elif require_zero and status != 0:
        incomplete.append(f"{relative}: command exited {status}")
    return status, provenance, incomplete


def validate_isolation(record: dict[str, Any], expected_status: int | None,
                       require_quiet: bool) -> tuple[list[str], list[str]]:
    """Validate a native isolated_bench reserve receipt without timing it."""
    path = isolation_path(record)
    provenance: list[str] = []
    incomplete: list[str] = []
    if not path.is_file():
        return provenance, [f"{path}: missing isolation receipt"]
    try:
        rows = load_jsonl(path)
    except (ValueError, json.JSONDecodeError) as error:
        return [f"{path}: malformed isolation receipt: {error}"], incomplete
    if len(rows) != 1:
        return [f"{path}: expected exactly one isolation record, found {len(rows)}"], incomplete
    receipt = rows[0]
    if receipt.get("schema") != "isolated-bench/1" or receipt.get("mode") != "reserve":
        provenance.append(f"{path}: wrong isolation schema or mode")
    argv = record["argv"]
    expected_label = argv[argv.index("--label") + 1]
    if receipt.get("label") != expected_label:
        provenance.append(f"{path}: isolation label differs from command plan")
    if receipt.get("command") != child_argv(record):
        provenance.append(f"{path}: isolated child argv differs from command plan")
    if receipt.get("reserved_cpus") != [0, 1, 2, 3]:
        incomplete.append(f"{path}: reserved CPU set is not 0-3")
    isolation_status = receipt.get("exit_status")
    normalized_status = (
        isolation_status & 0xFF if isinstance(isolation_status, int) else None
    )
    if expected_status is not None and normalized_status != expected_status:
        provenance.append(f"{path}: isolation and outer statuses differ after frozen normalization")
    if require_quiet:
        if receipt.get("contended_samples") != 0:
            incomplete.append(f"{path}: contended isolation samples")
        if receipt.get("left_on_reserved") not in ({}, []):
            incomplete.append(f"{path}: threads remained on reserved CPUs")
    return provenance, incomplete


def validate_registry_contract() -> tuple[dict[str, dict[str, Any]], dict[str, Any], list[str]]:
    findings: list[str] = []
    registry: dict[str, dict[str, Any]] = {}
    detail: dict[str, Any] = {}
    specs = (
        ("rust", runner.V4_ROOT / "registry/rust.jsonl", 262, set(runner.RUST_IDS)),
        ("c", runner.V4_ROOT / "registry/c.jsonl", 34, set(runner.C_IDS)),
    )
    for language, path, expected_rows, selected in specs:
        try:
            rows = load_jsonl(path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            findings.append(f"{language} registry malformed: {error}")
            continue
        ids = [row.get("id") for row in rows]
        duplicates = sorted({kid for kid in ids if isinstance(kid, str) and ids.count(kid) > 1})
        malformed = [index for index, row in enumerate(rows) if not all(
            isinstance(row.get(field), str) and row[field] for field in ("id", "area", "tier", "desc")
        )]
        if len(rows) != expected_rows:
            findings.append(f"{language} registry row count {len(rows)} != {expected_rows}")
        if duplicates:
            findings.append(f"{language} registry duplicate IDs: {duplicates}")
        if malformed:
            findings.append(f"{language} registry malformed metadata rows: {malformed}")
        present = {kid for kid in ids if isinstance(kid, str)}
        if language == "c" and present != selected:
            findings.append("C registry IDs differ from the frozen complete 34-cell set")
        elif language == "rust" and not selected.issubset(present):
            findings.append("Rust registry lacks a frozen selected ID")
        for row in rows:
            if row.get("id") in selected:
                registry[row["id"]] = row
        detail[language] = {
            "rows": len(rows), "unique_ids": len(present),
            "selected_ids": sorted(selected), "duplicates": duplicates,
        }
    selection_path = runner.V4_ROOT / "preflight/exact-selection.json"
    try:
        selection = load_json(selection_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        findings.append(f"exact-selection receipt malformed: {error}")
        selection = {}
    expected_selection = {
        "source_commit": "781722ef89e74b62079d2bc0cb82217061ac188c",
        "perfindex_sha256": "28084cd77fe28d3b031f4dc1474241ee051b2072c7b62dc7a17e0049c3e3674f",
        "rust_expected_count": 10, "rust_selected_count": 10,
        "c_expected_count": 34, "c_selected_count": 34,
        "suffix_variant_selected": False, "gate_pass": True,
    }
    for field, expected in expected_selection.items():
        if selection.get(field) != expected:
            findings.append(f"exact-selection {field} differs from {expected!r}")
    if set(selection.get("rust_selected_ids", [])) != set(runner.RUST_IDS):
        findings.append("exact-selection Rust IDs differ from the frozen ten")
    detail["exact_selection"] = {
        field: selection.get(field) for field in expected_selection
    }
    detail["passes"] = not findings
    return registry, detail, findings


def recompute_wall_summary(
    compare: dict[str, Any], ids: tuple[str, ...], registry: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any] | None, list[str], list[str]]:
    """Validate raw samples, then replay the frozen perfindex analysis exactly."""
    provenance: list[str] = []
    incomplete: list[str] = []
    raw = compare.get("raw")
    if not isinstance(raw, dict):
        return None, ["raw comparison is not an object"], incomplete
    for kernel in ids:
        record = raw.get(kernel)
        if not isinstance(record, dict):
            incomplete.append(f"{kernel}: raw arm record missing")
            continue
        if record.get("A2") not in ([], None):
            provenance.append(f"{kernel}: unexpected A2 rows in --no-aa campaign")
        for arm in ("A", "B"):
            arm_rows = record.get(arm)
            if not isinstance(arm_rows, list) or len(arm_rows) != 6:
                incomplete.append(f"{kernel}/{arm}: expected six raw rows")
                continue
            for replicate, row in enumerate(arm_rows):
                if not isinstance(row, dict):
                    provenance.append(f"{kernel}/{arm}/{replicate + 1}: raw row is not an object")
                    continue
                if row.get("id") != kernel or row.get("round") != replicate:
                    provenance.append(f"{kernel}/{arm}/{replicate + 1}: ID or round mismatch")
                samples = row.get("samples_ns")
                median = row.get("median_ns")
                if (
                    not isinstance(samples, list) or not 3 <= len(samples) <= 5
                    or any(not isinstance(value, int) or isinstance(value, bool) or value <= 0 for value in samples)
                ):
                    incomplete.append(f"{kernel}/{arm}/{replicate + 1}: invalid raw samples_ns")
                elif (
                    not isinstance(median, (int, float)) or isinstance(median, bool)
                    or median <= 0 or median != statistics.median(samples)
                ):
                    provenance.append(f"{kernel}/{arm}/{replicate + 1}: median_ns differs from samples_ns")
    if provenance or incomplete:
        return None, provenance, incomplete
    if any(kernel not in registry for kernel in ids):
        return None, ["selected cell lacks frozen registry metadata"], incomplete
    kernels = [registry[kernel] for kernel in sorted(ids)]
    rng = random.Random(20260926)
    for _ in range(6):
        order = kernels[:]
        rng.shuffle(order)
    weights = json.loads(WEIGHTS_PATH.read_text(encoding="utf-8"))["areas"]
    try:
        perfindex = load_frozen_perfindex()
        summary = perfindex.summarize(kernels, raw, weights, rng)
    except (OSError, ImportError, RuntimeError, SyntaxError, KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        return None, [f"frozen perfindex replay failed: {error}"], incomplete
    return summary, provenance, incomplete


def read_retained_wall_attempts(
    run_root: Path, spec: dict[str, Any], registry: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], list[str], list[str]]:
    compare_dir = run_root / f"wall-{spec['panel']}/{spec['language']}/compare"
    attempts_dir = compare_dir / "attempts"
    provenance: list[str] = []
    incomplete: list[str] = []
    normalized: list[dict[str, Any]] = []
    raw = {kernel: {"A": [], "B": [], "A2": []} for kernel in spec["ids"]}
    if not attempts_dir.is_dir():
        return normalized, raw, provenance, [f"{spec['id']}: no durable wall attempts directory"]
    files = sorted(path for path in attempts_dir.glob("*.json") if not path.name.endswith(".started.json"))
    started_files = sorted(attempts_dir.glob("*.started.json"))
    receipts: list[dict[str, Any]] = []
    starts: list[dict[str, Any]] = []
    for path in started_files:
        try:
            starts.append(load_json(path))
        except (ValueError, json.JSONDecodeError) as error:
            provenance.append(f"{spec['id']}: malformed durable start {path.name}: {error}")
    for path in files:
        try:
            receipts.append(load_json(path))
        except (ValueError, json.JSONDecodeError) as error:
            provenance.append(f"{spec['id']}: malformed durable attempt {path.name}: {error}")
    journal_path = compare_dir / "attempts.jsonl"
    if journal_path.is_file():
        try:
            journal, trailing = load_jsonl_with_trailing_partial(journal_path)
            if journal != receipts:
                if journal == receipts[:len(journal)]:
                    incomplete.append(
                        f"{spec['id']}: durable JSONL journal is a crash-consistent prefix of authoritative objects"
                    )
                else:
                    provenance.append(f"{spec['id']}: durable JSONL journal contradicts per-attempt objects")
            if trailing:
                incomplete.append(f"{spec['id']}: attempts JSONL has a trailing partial line; authoritative files used")
        except (ValueError, json.JSONDecodeError) as error:
            provenance.append(f"{spec['id']}: malformed durable JSONL journal: {error}")
    else:
        incomplete.append(f"{spec['id']}: missing durable JSONL journal")
    schedule = runner.wall_schedule(spec["id"])
    expected = [
        (item["round"], item["kernel"], arm)
        for item in schedule for arm in item["arms"]
    ]
    events_path = compare_dir / "events.jsonl"
    if events_path.is_file():
        try:
            events, trailing = load_jsonl_with_trailing_partial(events_path)
            expected_events: list[dict[str, Any]] = []
            by_sequence = {receipt.get("sequence"): receipt for receipt in receipts}
            for start in starts:
                expected_events.append(start)
                if start.get("sequence") in by_sequence:
                    expected_events.append(by_sequence[start["sequence"]])
            if events != expected_events:
                if events == expected_events[:len(events)]:
                    incomplete.append(
                        f"{spec['id']}: event journal is a crash-consistent prefix of authoritative files"
                    )
                else:
                    provenance.append(f"{spec['id']}: event journal contradicts authoritative attempt files")
            if trailing:
                incomplete.append(f"{spec['id']}: event journal has a trailing partial line; authoritative files used")
        except (ValueError, json.JSONDecodeError) as error:
            provenance.append(f"{spec['id']}: malformed event journal: {error}")
    else:
        incomplete.append(f"{spec['id']}: missing durable event journal")
    if len(starts) < len(receipts) or len(starts) > len(receipts) + 1:
        provenance.append(f"{spec['id']}: start/finish file cardinality is impossible")
    start_sequences = [row.get("sequence") for row in starts]
    finish_sequences = [row.get("sequence") for row in receipts]
    if start_sequences != list(range(1, len(starts) + 1)):
        provenance.append(f"{spec['id']}: durable start sequence is not a unique ordered prefix")
    if finish_sequences != list(range(1, len(receipts) + 1)):
        provenance.append(f"{spec['id']}: durable finish sequence is not a unique ordered prefix")
    if len(receipts) > len(expected):
        provenance.append(f"{spec['id']}: more durable attempts than the frozen schedule")
    binary = runner.RUST_BINARY if spec["language"] == "rust" else runner.C_BINARY
    taskset = "0" if spec["panel"] == "1t" else "0-3"
    failed_sequences: list[int] = []
    for index, receipt in enumerate(receipts):
        if index >= len(expected):
            break
        round_index, kernel, arm = expected[index]
        expected_argv = [
            str(runner.TASKSET), "-c", taskset, str(binary), "run", "--filter",
            kernel, "--exact", "--samples", "5", "--max-seconds", "2.0",
        ]
        expected_fields = {
            "schema": "cpu-baseline-aa-v5-wall-attempt/v1", "sequence": index + 1,
            "session": spec["id"], "round": round_index, "kernel": kernel,
            "arm": arm, "argv": expected_argv,
        }
        if index >= len(starts):
            provenance.append(f"{spec['id']}: durable attempt {index + 1} lacks a start record")
        else:
            expected_start = {
                "schema": "cpu-baseline-aa-v5-wall-attempt-start/v1", "event": "started",
                "sequence": index + 1, "session": spec["id"], "round": round_index,
                "kernel": kernel, "arm": arm, "argv": expected_argv,
            }
            if any(starts[index].get(field) != value for field, value in expected_start.items()):
                provenance.append(f"{spec['id']}: durable start {index + 1} differs from frozen schedule")
            if starts[index].get("started_at") != receipt.get("started_at"):
                provenance.append(f"{spec['id']}: start/finish timestamp binding differs at {index + 1}")
        if any(receipt.get(field) != value for field, value in expected_fields.items()):
            provenance.append(f"{spec['id']}: durable attempt {index + 1} differs from frozen schedule")
            continue
        started_at = parse_utc(receipt.get("started_at"))
        finished_at = parse_utc(receipt.get("finished_at"))
        if started_at is None or finished_at is None or finished_at < started_at:
            provenance.append(f"{spec['id']}: invalid attempt timestamps at {index + 1}")
        if receipt.get("event") != "finished":
            provenance.append(f"{spec['id']}: terminal event marker missing at {index + 1}")
        child_status = receipt.get("child_returncode")
        effective = receipt.get("effective_returncode")
        timed_out = receipt.get("timed_out")
        parse_error = receipt.get("parse_error")
        row = receipt.get("row")
        if (
            not isinstance(child_status, int) or not isinstance(effective, int)
            or not isinstance(timed_out, bool)
            or parse_error is not None and not isinstance(parse_error, str)
        ):
            provenance.append(f"{spec['id']}: invalid status fields at {index + 1}")
        else:
            expected_effective = child_status if child_status != 0 else (2 if parse_error else 0)
            if effective != expected_effective:
                provenance.append(f"{spec['id']}: child/effective status contradiction at {index + 1}")
            if timed_out and (child_status != 124 or effective != 124):
                provenance.append(f"{spec['id']}: timeout/status contradiction at {index + 1}")
        protocol_arm = spec["arms"][arm]
        contract, _ = runner.work_contract(spec["id"], kernel, registry.get(kernel, {}))
        base = {
            "run_id": f"wall-{spec['panel']}-{runner.safe_id(kernel)}-r{round_index + 1:02d}-{arm}",
            "arm": protocol_arm, "instance_id": kernel, "seed": 20260926,
            "replicate": round_index + 1, "warmup": False, "tier": "nonqualified",
            "attempts": 1,
            "started_at": receipt.get("started_at"),
            "finished_at": receipt.get("finished_at"),
            "worker": "local-cpu-reservation", "backend_ref": f"{spec['id']}:{index + 1}",
            "work_contract": contract,
        }
        if effective == 0 and isinstance(row, dict):
            stdout_row, stdout_error = parse_single_benchmark_stdout(receipt.get("stdout"))
            expected_row = None if stdout_row is None else {**stdout_row, "round": round_index}
            row_findings = validate_benchmark_row(row, kernel, round_index)
            if stdout_error or expected_row != row or row_findings:
                detail = "; ".join([item for item in [stdout_error, *row_findings] if item])
                provenance.append(
                    f"{spec['id']}: retained success row/stream mismatch at {index + 1}"
                    + (f": {detail}" if detail else "")
                )
                continue
            if child_status != 0 or timed_out or parse_error is not None:
                provenance.append(f"{spec['id']}: successful row has contradictory status at {index + 1}")
            raw[kernel][arm].append(row)
            fingerprint = row.get("fingerprint")
            median = row.get("median_ns")
            normalized.append({
                **base, "status": "succeeded",
                "wall_seconds": median / 1e9 if isinstance(median, (int, float)) else None,
                "verification": "verified" if isinstance(fingerprint, str) and fingerprint else "error",
                "output_fingerprint": fingerprint,
                "complete_invocations": 1,
            })
        else:
            failed_sequences.append(index + 1)
            if row is not None:
                provenance.append(f"{spec['id']}: failed attempt unexpectedly retains a success row at {index + 1}")
            normalized.append({
                **base, "status": "timeout" if receipt.get("timed_out") else "failed",
                "wall_seconds": None, "verification": "error",
                "complete_invocations": 0,
            })
            if index != len(receipts) - 1:
                provenance.append(f"{spec['id']}: attempts continued after a failed wall invocation")
    if failed_sequences and len(starts) > failed_sequences[0]:
        provenance.append(f"{spec['id']}: an invocation started after a failed wall invocation")
    if not failed_sequences and len(starts) == len(receipts) + 1 and len(receipts) < len(expected):
        round_index, kernel, arm = expected[len(receipts)]
        start = starts[-1]
        if (
            start.get("schema") != "cpu-baseline-aa-v5-wall-attempt-start/v1"
            or start.get("event") != "started" or start.get("sequence") != len(starts)
            or start.get("session") != spec["id"] or start.get("round") != round_index
            or start.get("kernel") != kernel or start.get("arm") != arm
        ):
            provenance.append(f"{spec['id']}: in-flight start record differs from frozen schedule")
        else:
            started_at = parse_utc(start.get("started_at"))
            if started_at is None:
                provenance.append(f"{spec['id']}: invalid in-flight start timestamp")
            contract, _ = runner.work_contract(spec["id"], kernel, registry.get(kernel, {}))
            normalized.append({
                "run_id": f"wall-{spec['panel']}-{runner.safe_id(kernel)}-r{round_index + 1:02d}-{arm}",
                "arm": spec["arms"][arm], "instance_id": kernel,
                "seed": 20260926, "replicate": round_index + 1, "warmup": False,
                "tier": "nonqualified", "attempts": 1, "status": "interrupted",
                "wall_seconds": None, "verification": "error", "complete_invocations": 0,
                "started_at": start.get("started_at"), "finished_at": None,
                "worker": "local-cpu-reservation", "backend_ref": f"{spec['id']}:{len(starts)}",
                "work_contract": contract,
            })
    if len(starts) < len(expected):
        incomplete.append(f"{spec['id']}: retained {len(starts)}/{len(expected)} wall attempt starts")
    return normalized, raw, provenance, incomplete


def validate_wall_session_manifest(
    run_root: Path, spec: dict[str, Any],
) -> tuple[dict[str, Any] | None, list[str], list[str]]:
    compare_dir = run_root / f"wall-{spec['panel']}/{spec['language']}/compare"
    path = compare_dir / "session.json"
    binary = runner.RUST_BINARY if spec["language"] == "rust" else runner.C_BINARY
    threads = 1 if spec["panel"] == "1t" else 4
    provenance: list[str] = []
    incomplete: list[str] = []
    expected = {
        "schema": "cpu-baseline-aa-v5-wall-session/v1", "session": spec["id"],
        "binary": str(binary), "threads": threads,
        "taskset": "0" if threads == 1 else "0-3", "rounds": 6,
        "samples": 5, "max_seconds": 2.0, "invocation_timeout_seconds": 1800,
        "schedule_sha256": runner.digest_value(runner.wall_schedule(spec["id"])),
        "binary_sha256": (
            runner.RUST_BINARY_SHA256 if spec["language"] == "rust" else runner.C_BINARY_SHA256
        ),
        "registry_sha256": (
            runner.RUST_REGISTRY_SHA256 if spec["language"] == "rust" else runner.C_REGISTRY_SHA256
        ),
        "perfindex_sha256": runner.PERFINDEX_SHA256,
    }
    expected_environment = runner.wall_environment(threads)
    start_path = compare_dir / "session-start.json"
    if not start_path.is_file():
        incomplete.append(f"{spec['id']}: missing durable session-start manifest")
    else:
        try:
            start = load_json(start_path)
            expected_start = {
                "schema": "cpu-baseline-aa-v5-wall-session-start/v1",
                "session": spec["id"], "binary": str(binary),
                "environment": expected_environment,
                "binary_sha256": expected["binary_sha256"],
                "registry_sha256": expected["registry_sha256"],
                "perfindex_sha256": expected["perfindex_sha256"],
                "environment_error": None,
            }
            if any(start.get(field) != value for field, value in expected_start.items()):
                provenance.append(f"{spec['id']}: session-start manifest differs from frozen values")
            if parse_utc(start.get("started_at")) is None:
                provenance.append(f"{spec['id']}: session-start timestamp is invalid")
        except (ValueError, json.JSONDecodeError) as error:
            provenance.append(f"{spec['id']}: malformed session-start manifest: {error}")
    registry_path = runner.V4_ROOT / f"registry/{spec['language']}.jsonl"
    try:
        expected_rows = load_jsonl(registry_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        expected_rows = []
        provenance.append(f"{spec['id']}: cannot read frozen registry for prelude validation: {error}")
    if spec["language"] == "rust":
        expected_rows = [row for row in expected_rows if row.get("tier") == "Quick"]
    list_argv = [str(binary), "list"] + (["--full"] if spec["language"] == "c" else [])
    prelude_blocked = False
    for ordinal, role in enumerate(("base", "cand"), 1):
        started_path = compare_dir / f"prelude/{ordinal:02d}-{role}.started.json"
        receipt_path = compare_dir / f"prelude/{ordinal:02d}-{role}.json"
        if not started_path.is_file() or not receipt_path.is_file():
            incomplete.append(f"{spec['id']}: missing {role} registry prelude receipt")
            prelude_blocked = True
            continue
        try:
            started = load_json(started_path)
            receipt = load_json(receipt_path)
        except (ValueError, json.JSONDecodeError) as error:
            provenance.append(f"{spec['id']}: malformed {role} registry prelude: {error}")
            continue
        structural_mismatch = (
            started.get("schema") != "cpu-baseline-aa-v5-registry-prelude-start/v1"
            or started.get("ordinal") != ordinal or started.get("role") != role
            or started.get("argv") != list_argv
            or receipt.get("schema") != "cpu-baseline-aa-v5-registry-prelude/v1"
            or receipt.get("ordinal") != ordinal or receipt.get("role") != role
            or receipt.get("argv") != list_argv
            or receipt.get("started_at") != started.get("started_at")
            or parse_utc(started.get("started_at")) is None
            or parse_utc(receipt.get("finished_at")) is None
        )
        if structural_mismatch:
            provenance.append(f"{spec['id']}: {role} registry prelude differs from frozen semantics")
            continue
        stdout_rows: list[dict[str, Any]] = []
        stdout_error = None
        try:
            stdout_rows = [
                json.loads(line) for line in receipt.get("stdout", "").splitlines()
                if line.startswith("{")
            ]
        except (AttributeError, json.JSONDecodeError) as error:
            stdout_error = str(error)
        if stdout_error or receipt.get("rows") != stdout_rows:
            provenance.append(f"{spec['id']}: {role} registry receipt is not bound to stdout")
        registry_mismatch = receipt.get("rows") != expected_rows
        if registry_mismatch:
            provenance.append(f"{spec['id']}: {role} live registry differs from the frozen registry receipt")
        child_status = receipt.get("child_returncode")
        effective = receipt.get("effective_returncode")
        parse_error = receipt.get("parse_error")
        timed_out = receipt.get("timed_out")
        if not isinstance(child_status, int) or not isinstance(effective, int) or not isinstance(timed_out, bool):
            provenance.append(f"{spec['id']}: {role} registry status fields are malformed")
        else:
            want_effective = child_status if child_status != 0 else (2 if parse_error else 0)
            if effective != want_effective:
                provenance.append(f"{spec['id']}: {role} registry status fields contradict")
            if effective != 0:
                prelude_blocked = True
                incomplete.append(f"{spec['id']}: {role} registry prelude exited {effective}")
            if timed_out and child_status != 124:
                provenance.append(f"{spec['id']}: {role} registry timeout status contradicts")
        if registry_mismatch and not isinstance(parse_error, str):
            provenance.append(f"{spec['id']}: {role} registry mismatch lacks parse_error")
    session: dict[str, Any] | None = None
    if not path.is_file():
        incomplete.append(f"{spec['id']}: missing durable session manifest")
    else:
        try:
            session = load_json(path)
        except (ValueError, json.JSONDecodeError) as error:
            provenance.append(f"{spec['id']}: malformed session manifest: {error}")
        if session is not None:
            provenance.extend(
                f"{spec['id']}: session manifest {field} mismatch"
                for field, value in expected.items() if session.get(field) != value
            )
            if session.get("environment") != expected_environment:
                provenance.append(f"{spec['id']}: sanitized environment differs from frozen values")
    host = session.get("host") if session is not None else None
    if not isinstance(host, dict):
        if session is not None:
            provenance.append(f"{spec['id']}: session host is absent or malformed")
        host = None
    else:
        try:
            expected_host = load_json(
                runner.V4_ROOT / (
                    "build/base-rust/build.json" if spec["language"] == "rust"
                    else "build/base-c/build.json"
                )
            )["host"]
        except (OSError, KeyError, ValueError, json.JSONDecodeError) as error:
            provenance.append(f"{spec['id']}: cannot read frozen v4 build host: {error}")
        else:
            if any(host.get(field) != expected_host.get(field) for field in HOST_IDENTITY_FIELDS):
                provenance.append(f"{spec['id']}: host identity differs from frozen v4 build host")
    if prelude_blocked and session is not None:
        provenance.append(f"{spec['id']}: session manifest exists after a blocked registry prelude")
    end_path = compare_dir / "session-end.json"
    if not end_path.is_file():
        incomplete.append(f"{spec['id']}: missing session-end identity snapshot")
    else:
        try:
            end = load_json(end_path)
        except (ValueError, json.JSONDecodeError) as error:
            provenance.append(f"{spec['id']}: malformed session-end identity snapshot: {error}")
        else:
            expected_end = {
                "schema": "cpu-baseline-aa-v5-wall-session-end/v1", "session": spec["id"],
                "binary_sha256": expected["binary_sha256"],
                "registry_sha256": expected["registry_sha256"],
                "perfindex_sha256": expected["perfindex_sha256"],
                "completed_invocations": len(runner.wall_schedule(spec["id"])) * 2,
            }
            if any(end.get(field) != value for field, value in expected_end.items()) or parse_utc(end.get("finished_at")) is None:
                provenance.append(f"{spec['id']}: session-end identity snapshot differs from frozen values")
    return host, provenance, incomplete


def session_specs(run_root: Path) -> list[dict[str, Any]]:
    attempts = run_root / "orchestration/attempts"
    return [
        {"id": "rust-1t", "ids": runner.RUST_IDS, "panel": "1t", "language": "rust",
         "arms": {"A": "base-1t", "B": "base-aa-1t"},
         "stderr": attempts / "wall-01-rust-1t/stderr.txt"},
        {"id": "c-1t", "ids": runner.C_IDS, "panel": "1t", "language": "c",
         "arms": {"A": "base-1t", "B": "base-aa-1t"},
         "stderr": attempts / "wall-02-c-1t/stderr.txt"},
        {"id": "rust-4t", "ids": runner.RUST_IDS, "panel": "4t", "language": "rust",
         "arms": {"A": "base-4t", "B": "base-aa-4t"},
         "stderr": attempts / "wall-03-rust-4t/stderr.txt"},
        {"id": "c-4t", "ids": runner.C_IDS, "panel": "4t", "language": "c",
         "arms": {"A": "base-4t", "B": "base-aa-4t"},
         "stderr": attempts / "wall-04-c-4t/stderr.txt"},
    ]


TERMINAL_STATUSES = {
    "preflight_identity_blocked", "wall_command_failed", "wall_gate_failed",
    "interrupted_by_operator", "orchestration_exception", "orphaned_after_process_loss",
}


def validate_terminal_state(
    run_root: Path, wall_plan: list[dict[str, Any]],
) -> tuple[str | None, list[str]]:
    path = run_root / "orchestration/terminal.json"
    if not path.is_file():
        return None, []
    try:
        terminal = load_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return None, [f"malformed terminal receipt: {error}"]
    findings: list[str] = []
    status = terminal.get("status")
    if (
        terminal.get("schema") != "cpu-baseline-aa-v5-terminal/v1"
        or terminal.get("continuation") != "forbidden"
        or parse_utc(terminal.get("finished_at")) is None
        or status not in TERMINAL_STATUSES
    ):
        findings.append("terminal receipt violates the frozen schema/status vocabulary")
    if status == "wall_command_failed":
        first_failed: dict[str, Any] | None = None
        for index, record in enumerate(wall_plan, 1):
            receipt_path = run_root / f"orchestration/attempts/wall-{index:02d}-{record['id']}/receipt.json"
            if not receipt_path.is_file():
                continue
            try:
                receipt = load_json(receipt_path)
            except (OSError, ValueError, json.JSONDecodeError):
                continue
            if isinstance(receipt.get("returncode"), int) and receipt["returncode"] != 0:
                first_failed = record
                break
        if first_failed is None or terminal.get("record") != first_failed:
            findings.append("wall_command_failed terminal does not bind the first nonzero planned receipt")
    if status == "preflight_identity_blocked":
        preflight_path = run_root / "orchestration/preflight.json"
        try:
            preflight = load_json(preflight_path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            findings.append(f"preflight_identity_blocked terminal lacks a valid preflight receipt: {error}")
        else:
            preflight_findings = preflight.get("findings")
            if (
                not isinstance(preflight_findings, list) or not preflight_findings
                or terminal.get("findings") != preflight_findings
            ):
                findings.append(
                    "preflight_identity_blocked terminal findings differ from the preflight receipt"
                )
    return status if isinstance(status, str) else None, findings


def validate_campaign_preflight(
    run_root: Path, protocol: dict[str, Any] | None = None,
) -> tuple[list[str], list[str], dict[str, Any]]:
    provenance: list[str] = []
    incomplete: list[str] = []
    snapshots: dict[str, Any] = {}
    preflight_path = run_root / "orchestration/preflight.json"
    preflight_inventory: list[dict[str, Any]] | None = None
    if not preflight_path.is_file():
        incomplete.append("missing orchestration preflight receipt")
    else:
        try:
            receipt = load_json(preflight_path)
        except (ValueError, json.JSONDecodeError) as error:
            provenance.append(f"malformed orchestration preflight receipt: {error}")
        else:
            if receipt.get("schema") != "cpu-baseline-aa-v5-preflight/v1" or parse_utc(receipt.get("checked_at")) is None:
                provenance.append("orchestration preflight receipt has invalid schema or timestamp")
            recorded = receipt.get("findings")
            inventory = receipt.get("required_files")
            if not isinstance(inventory, list) or any(not isinstance(item, dict) for item in inventory):
                provenance.append("orchestration preflight required-file inventory is malformed")
            else:
                preflight_inventory = inventory
            if not isinstance(recorded, list) or any(not isinstance(item, str) for item in recorded):
                provenance.append("orchestration preflight findings are malformed")
                recorded = []
            runtime_observations = receipt.get("runtime_observations")
            if not isinstance(runtime_observations, dict):
                provenance.append("orchestration preflight runtime observations are malformed")
            elif protocol is not None and preflight_inventory is not None:
                retained_findings = runner.identity_findings(
                    protocol, preflight_inventory, runtime_observations,
                )
                if recorded != retained_findings:
                    provenance.append("recorded preflight findings differ from retained identity observations")
            expected_status = "passed" if not recorded else "blocked_identity_mismatch"
            if receipt.get("status") != expected_status:
                provenance.append("orchestration preflight status contradicts its findings")
            provenance.extend(f"preflight identity: {item}" for item in recorded)
    identity_snapshots: dict[str, list[dict[str, Any]]] = {}
    for label in ("before", "wall-after"):
        path = run_root / f"orchestration/identity-{label}.json"
        if not path.is_file():
            incomplete.append(f"missing identity-{label} snapshot")
            continue
        try:
            identity = load_json(path)
        except (ValueError, json.JSONDecodeError) as error:
            provenance.append(f"malformed identity-{label} snapshot: {error}")
            continue
        files = identity.get("required_files")
        if (
            identity.get("schema") != "cpu-baseline-aa-v5-identity-snapshot/v1"
            or identity.get("label") != label or parse_utc(identity.get("captured_at")) is None
            or not isinstance(files, list) or any(not isinstance(item, dict) for item in files)
        ):
            provenance.append(f"identity-{label} snapshot violates the frozen schema")
            continue
        identity_snapshots[label] = files
    if preflight_inventory is not None and identity_snapshots.get("before") != preflight_inventory:
        provenance.append("preflight and identity-before required-file inventories differ")
    if (
        "before" in identity_snapshots and "wall-after" in identity_snapshots
        and identity_snapshots["before"] != identity_snapshots["wall-after"]
    ):
        provenance.append("required-file identity changed during the campaign")
    for label in ("before", "wall-after"):
        path = run_root / f"orchestration/system-{label}.json"
        if not path.is_file():
            incomplete.append(f"missing system-{label} snapshot")
            continue
        try:
            snapshot = load_json(path)
        except (ValueError, json.JSONDecodeError) as error:
            provenance.append(f"malformed system-{label} snapshot: {error}")
            continue
        snapshots["after" if label == "wall-after" else label] = snapshot
        if (
            snapshot.get("schema") != "cpu-baseline-aa-v5-system-snapshot/v1"
            or snapshot.get("label") != label
            or parse_utc(snapshot.get("captured_at")) is None
            or snapshot.get("affinity") != [0, 1, 2, 3, 4]
        ):
            provenance.append(f"system-{label} snapshot violates the frozen schema/host affinity")
        for field in ("proc_stat", "proc_meminfo", "proc_softirqs", "pressure", "cgroup"):
            if snapshot.get(field) in (None, {}, ""):
                incomplete.append(f"system-{label} snapshot lacks {field}")
    return provenance, incomplete, snapshots


def integer_fields(text: Any) -> dict[str, int] | None:
    if not isinstance(text, str):
        return None
    result: dict[str, int] = {}
    for line in text.splitlines():
        fields = line.split()
        if len(fields) >= 2 and fields[1].lstrip("-").isdigit():
            result[fields[0]] = int(fields[1])
    return result


def proc_stat_counts(text: Any) -> dict[str, int] | None:
    if not isinstance(text, str):
        return None
    result: dict[str, int] = {}
    for line in text.splitlines():
        fields = line.split()
        if not fields:
            continue
        if fields[0] == "cpu" and len(fields) >= 9 and all(item.isdigit() for item in fields[1:9]):
            result["steal"] = int(fields[8])
        elif fields[0] in {"intr", "softirq", "ctxt", "processes"} and len(fields) >= 2 and fields[1].isdigit():
            result[fields[0]] = int(fields[1])
    return result if {"steal", "intr", "softirq", "ctxt"}.issubset(result) else None


def pressure_totals(value: Any) -> dict[str, int] | None:
    if not isinstance(value, dict):
        return None
    result: dict[str, int] = {}
    for resource in ("cpu", "io", "memory"):
        text = value.get(resource)
        if not isinstance(text, str):
            return None
        for line in text.splitlines():
            fields = line.split()
            if not fields:
                continue
            total = next((item.split("=", 1)[1] for item in fields[1:] if item.startswith("total=")), None)
            if total is None or not total.isdigit():
                return None
            result[f"{resource}.{fields[0]}"] = int(total)
    return result


def analyze_system_noise(snapshots: dict[str, Any]) -> tuple[dict[str, Any], list[str], list[str]]:
    """Compute preregistered monotone host/cgroup deltas without timing claims."""
    before = snapshots.get("before")
    after = snapshots.get("after")
    detail: dict[str, Any] = {"available": False, "deltas": {}, "blockers": []}
    provenance: list[str] = []
    incomplete: list[str] = []
    if not isinstance(before, dict) or not isinstance(after, dict):
        return detail, provenance, ["before/after system snapshots are not both available"]
    if before.get("cgroup_path") != after.get("cgroup_path"):
        provenance.append("cgroup path changed during the campaign")
    stable_host_fields = (
        "platform", "uname", "affinity", "online_cpus", "smt_active", "smt_control",
        "numa_online", "microcode", "governors",
    )
    for field in stable_host_fields:
        if before.get(field) != after.get(field):
            provenance.append(f"stable host field changed during the campaign: {field}")
    stable_cgroup_fields = (
        "cpu.max", "cpuset.cpus.effective", "cpuset.mems.effective", "memory.high",
        "memory.max", "memory.swap.max", "pids.max",
    )
    before_cgroup = before.get("cgroup", {})
    after_cgroup = after.get("cgroup", {})
    for field in stable_cgroup_fields:
        if before_cgroup.get(field) != after_cgroup.get(field):
            provenance.append(f"stable cgroup field changed during the campaign: {field}")
    parsers = {
        "proc": (proc_stat_counts(before.get("proc_stat")), proc_stat_counts(after.get("proc_stat"))),
        "cpu_cgroup": (
            integer_fields(before.get("cgroup", {}).get("cpu.stat")),
            integer_fields(after.get("cgroup", {}).get("cpu.stat")),
        ),
        "memory_events": (
            integer_fields(before.get("cgroup", {}).get("memory.events")),
            integer_fields(after.get("cgroup", {}).get("memory.events")),
        ),
        "pressure": (pressure_totals(before.get("pressure")), pressure_totals(after.get("pressure"))),
    }
    deltas: dict[str, dict[str, int]] = {}
    for name, (first, last) in parsers.items():
        if first is None or last is None:
            incomplete.append(f"cannot parse {name} counters from system snapshots")
            continue
        keys = sorted(set(first) & set(last))
        delta = {key: last[key] - first[key] for key in keys}
        if any(value < 0 for value in delta.values()):
            provenance.append(f"{name} counters decreased during the campaign")
        deltas[name] = delta
    blockers: list[str] = []
    if not before.get("governors") or all(value is None for value in before.get("governors", {}).values()):
        blockers.append("CPU governor is unavailable")
    before_frequencies = before.get("frequencies", {})
    after_frequencies = after.get("frequencies", {})
    for cpu in sorted(set(before_frequencies) | set(after_frequencies)):
        first = before_frequencies.get(cpu, {})
        last = after_frequencies.get(cpu, {})
        for field in ("scaling_min_freq", "scaling_max_freq"):
            if first.get(field) != last.get(field):
                provenance.append(f"stable CPU frequency bound changed: {cpu}/{field}")
        if first.get("scaling_cur_freq") != last.get("scaling_cur_freq"):
            blockers.append(f"observed CPU frequency changed: {cpu}")
    if not before_frequencies or all(
        all(value is None for value in fields.values()) for fields in before_frequencies.values()
    ):
        blockers.append("CPU frequency observability is unavailable")
    unavailable_limits = [
        field for field in stable_cgroup_fields
        if before_cgroup.get(field) is None
    ]
    if unavailable_limits:
        blockers.append("unavailable cgroup limit fields: " + ",".join(unavailable_limits))
    proc = deltas.get("proc", {})
    if proc.get("steal", 0) > 0:
        incomplete.append("aggregate CPU steal time increased during the campaign")
    if proc.get("intr", 0) > 0 or proc.get("softirq", 0) > 0:
        blockers.append("aggregate host interrupt/softirq activity occurred")
    cpu = deltas.get("cpu_cgroup", {})
    if cpu.get("nr_throttled", 0) > 0 or cpu.get("throttled_usec", 0) > 0:
        incomplete.append("campaign cgroup was CPU-throttled")
    memory = deltas.get("memory_events", {})
    if any(memory.get(key, 0) > 0 for key in ("high", "max", "oom", "oom_kill")):
        incomplete.append("campaign cgroup recorded a memory limit/failure event")
    pressure = deltas.get("pressure", {})
    if any(value > 0 for value in pressure.values()):
        blockers.append("aggregate pressure-stall totals increased")
    detail.update({"available": not incomplete, "deltas": deltas, "blockers": blockers})
    return detail, provenance, incomplete


def validate_campaign_after(run_root: Path) -> tuple[dict[str, Any], list[str], list[str]]:
    provenance: list[str] = []
    incomplete: list[str] = []
    identities: dict[str, list[dict[str, Any]]] = {}
    systems: dict[str, dict[str, Any]] = {}
    for label in ("before", "campaign-after"):
        identity_path = run_root / f"orchestration/identity-{label}.json"
        system_path = run_root / f"orchestration/system-{label}.json"
        if not identity_path.is_file() or not system_path.is_file():
            incomplete.append(f"missing campaign boundary identity/system snapshot: {label}")
            continue
        try:
            identity = load_json(identity_path)
            system = load_json(system_path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            provenance.append(f"malformed campaign boundary snapshot {label}: {error}")
            continue
        if (
            identity.get("schema") != "cpu-baseline-aa-v5-identity-snapshot/v1"
            or identity.get("label") != label or parse_utc(identity.get("captured_at")) is None
            or not isinstance(identity.get("required_files"), list)
        ):
            provenance.append(f"campaign identity snapshot {label} violates the frozen schema")
        else:
            identities[label] = identity["required_files"]
        if (
            system.get("schema") != "cpu-baseline-aa-v5-system-snapshot/v1"
            or system.get("label") != label or parse_utc(system.get("captured_at")) is None
        ):
            provenance.append(f"campaign system snapshot {label} violates the frozen schema")
        else:
            systems["after" if label == "campaign-after" else label] = system
    if (
        "before" in identities and "campaign-after" in identities
        and identities["before"] != identities["campaign-after"]
    ):
        provenance.append("required-file identity changed before campaign finalization")
    noise, noise_provenance, noise_incomplete = analyze_system_noise(systems)
    provenance.extend(noise_provenance)
    incomplete.extend(noise_incomplete)
    return noise, provenance, incomplete


def analyze_wall(
    run_root: Path, protocol: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], dict[str, str]]:
    normalized: list[dict[str, Any]] = []
    provenance_findings: list[str] = []
    incomplete_findings: list[str] = []
    false_directions: list[str] = []
    fingerprints: dict[str, set[str]] = {}
    observed_cells: set[tuple[str, str]] = set()
    schedule_records: dict[str, Any] = {}
    cell_analysis: list[dict[str, Any]] = []
    first_host: dict[str, Any] | None = None
    session_hosts: list[tuple[str, dict[str, Any]]] = []
    preflight_provenance, preflight_incomplete, snapshots = validate_campaign_preflight(
        run_root, protocol,
    )
    provenance_findings.extend(preflight_provenance)
    incomplete_findings.extend(preflight_incomplete)
    system_noise, noise_provenance, noise_incomplete = analyze_system_noise(snapshots)
    provenance_findings.extend(noise_provenance)
    incomplete_findings.extend(noise_incomplete)
    registry, registry_detail, registry_findings = validate_registry_contract()
    provenance_findings.extend(registry_findings)
    wall_plan = runner.build_plan()["wall"]
    wall_stop_seen = False
    for index, spec in enumerate(session_specs(run_root), 1):
        expected_record = wall_plan[index - 1]
        attempt_name = f"wall-{index:02d}-{spec['id']}"
        outer_start = run_root / f"orchestration/attempts/{attempt_name}/started.json"
        outer_receipt = run_root / f"orchestration/attempts/{attempt_name}/receipt.json"
        session_evidence = run_root / f"wall-{spec['panel']}/{spec['language']}/compare"
        if not outer_start.is_file() and session_evidence.exists() and any(session_evidence.rglob("*")):
            provenance_findings.append(f"{spec['id']}: wall session evidence exists without an outer start")
        if wall_stop_seen and outer_start.is_file():
            provenance_findings.append(f"{spec['id']}: wall session started after the frozen stop point")
        status, provenance, incomplete = validate_attempt(
            run_root, attempt_name, expected_record, require_zero=True,
        )
        provenance_findings.extend(provenance)
        incomplete_findings.extend(incomplete)
        if not outer_start.is_file() or not outer_receipt.is_file() or status not in (0, None):
            wall_stop_seen = True
        iso_provenance, iso_incomplete = validate_isolation(
            expected_record, status, require_quiet=True,
        )
        provenance_findings.extend(iso_provenance)
        incomplete_findings.extend(iso_incomplete)
        session_host, session_provenance, session_incomplete = validate_wall_session_manifest(
            run_root, spec,
        )
        provenance_findings.extend(session_provenance)
        incomplete_findings.extend(session_incomplete)
        if session_host is not None:
            session_hosts.append((spec["id"], session_host))
            if first_host is None:
                first_host = session_host
        retained_rows, retained_raw, retained_provenance, retained_incomplete = read_retained_wall_attempts(
            run_root, spec, registry,
        )
        normalized.extend(retained_rows)
        provenance_findings.extend(retained_provenance)
        incomplete_findings.extend(retained_incomplete)
        for row in retained_rows:
            fingerprint = row.get("output_fingerprint")
            if row.get("status") == "succeeded" and isinstance(fingerprint, str) and fingerprint:
                fingerprints.setdefault(row["instance_id"], set()).add(fingerprint)
        observed = parse_observed_schedule(spec["stderr"]) if spec["stderr"].is_file() else []
        expected = expected_schedule(spec["ids"])
        want_digest = RUST_SCHEDULE_SHA256 if spec["language"] == "rust" else C_SCHEDULE_SHA256
        compare_path = run_root / f"wall-{spec['panel']}/{spec['language']}/compare/compare.json"
        if not compare_path.is_file():
            incomplete_findings.append(f"{spec['id']}: missing compare.json")
            prefix_passes = observed == expected[:len(observed)]
            schedule_records[spec["id"]] = {
                "observed_sha256": canonical_sha256(observed),
                "expected_sha256": want_digest, "rows": len(observed),
                "passes": False, "prefix_passes": prefix_passes,
            }
            if not prefix_passes:
                provenance_findings.append(f"{spec['id']}: observed partial schedule is not a frozen prefix")
            continue
        try:
            compare = load_json(compare_path)
        except (ValueError, json.JSONDecodeError) as error:
            provenance_findings.append(f"{spec['id']}: malformed compare.json: {error}")
            continue
        compare_host = compare.get("host")
        if not isinstance(compare_host, dict) or session_host is None or any(
            compare_host.get(field) != session_host.get(field) for field in HOST_IDENTITY_FIELDS
        ):
            provenance_findings.append(f"{spec['id']}: compare host differs from durable session host")
        ids = set(spec["ids"])
        raw = compare.get("raw", {})
        if raw != retained_raw:
            provenance_findings.append(f"{spec['id']}: compare raw rows differ from durable per-attempt files")
        kernel_list = compare.get("kernels", [])
        if not isinstance(raw, dict) or not isinstance(kernel_list, list) or any(
            not isinstance(row, dict) or not isinstance(row.get("id"), str) for row in kernel_list
        ):
            provenance_findings.append(f"{spec['id']}: malformed cell inventory")
            continue
        kernel_rows = {row["id"]: row for row in kernel_list}
        if len(kernel_rows) != len(kernel_list):
            provenance_findings.append(f"{spec['id']}: duplicate kernel summary IDs")
        extra = (set(raw) | set(kernel_rows)) - ids
        missing = ids - (set(raw) & set(kernel_rows))
        if extra:
            provenance_findings.append(f"{spec['id']}: unplanned cells {sorted(extra)}")
        if missing:
            incomplete_findings.append(f"{spec['id']}: missing planned cells {sorted(missing)}")
        if compare.get("rounds") != 6:
            provenance_findings.append(f"{spec['id']}: round count differs from six")
        expected_binary = str(runner.RUST_BINARY if spec["language"] == "rust" else runner.C_BINARY)
        expected_threads = 1 if spec["panel"] == "1t" else 4
        identity = {
            "mode": "wall", "unit": "ms", "base": expected_binary,
            "cand": expected_binary, "threads": expected_threads,
            "samples_per_invocation": 5,
        }
        for field, expected_value in identity.items():
            if compare.get(field) != expected_value:
                provenance_findings.append(
                    f"{spec['id']}: compare {field}={compare.get(field)!r}, expected {expected_value!r}"
                )
        if not compare.get("valid"):
            provenance_findings.append(f"{spec['id']}: perfindex exactness invalid")
        recomputed, replay_provenance, replay_incomplete = recompute_wall_summary(
            compare, spec["ids"], registry,
        )
        provenance_findings.extend(f"{spec['id']}: {item}" for item in replay_provenance)
        incomplete_findings.extend(f"{spec['id']}: {item}" for item in replay_incomplete)
        recomputed_rows: dict[str, dict[str, Any]] = {}
        if recomputed is not None:
            for field in (
                "valid", "performance_index", "performance_index_ci95",
                "areas", "kernels", "rounds",
            ):
                if compare.get(field) != recomputed[field]:
                    provenance_findings.append(
                        f"{spec['id']}: reported {field} differs from independent frozen replay"
                    )
            recomputed_rows = {row["id"]: row for row in recomputed["kernels"]}
        digest = canonical_sha256(observed)
        schedule_records[spec["id"]] = {
            "observed_sha256": digest, "expected_sha256": want_digest,
            "rows": len(observed), "passes": observed == expected and digest == want_digest,
        }
        if observed != expected or digest != want_digest:
            if observed == expected[:len(observed)]:
                incomplete_findings.append(f"{spec['id']}: observed schedule is only a frozen prefix")
            else:
                provenance_findings.append(f"{spec['id']}: observed schedule mismatch")
        for kernel in sorted(ids):
            if kernel not in kernel_rows or kernel not in raw:
                continue
            observed_cells.add((spec["panel"], kernel))
            replay_row = recomputed_rows.get(kernel)
            verdict = replay_row.get("verdict") if replay_row is not None else None
            if verdict in {"faster", "slower"}:
                false_directions.append(f"{spec['panel']}/{kernel}:{verdict}")
            elif verdict != "neutral":
                provenance_findings.append(f"{spec['id']}/{kernel}: no valid independently replayed verdict")
            if replay_row is not None:
                cell_analysis.append({
                    "session": spec["id"], "panel": spec["panel"],
                    "language": spec["language"], **replay_row,
                })
            fingerprints.setdefault(kernel, set())
            record = raw[kernel]
            if not isinstance(record, dict) or set(record) != {"A", "B", "A2"}:
                incomplete_findings.append(f"{spec['id']}/{kernel}: missing mirrored arms")
                continue
            if (
                not isinstance(record["A"], list) or not isinstance(record["B"], list)
                or record["A2"] != []
                or len(record["A"]) != 6 or len(record["B"]) != 6
            ):
                incomplete_findings.append(f"{spec['id']}/{kernel}: missing mirrored pairs")
                continue
            for arm in ("A", "B"):
                for replicate, row in enumerate(record[arm], 1):
                    if not isinstance(row, dict):
                        provenance_findings.append(
                            f"{spec['id']}/{kernel}/{arm}/{replicate}: raw row is not an object"
                        )
                        continue
                    fingerprint = row.get("fingerprint")
                    samples = row.get("samples_ns")
                    median_ns = row.get("median_ns")
                    if row.get("round") != replicate - 1:
                        provenance_findings.append(
                            f"{spec['id']}/{kernel}/{arm}/{replicate}: raw round mismatch"
                        )
                    if not isinstance(fingerprint, str) or not fingerprint:
                        provenance_findings.append(f"{spec['id']}/{kernel}/{arm}/{replicate}: missing fingerprint")
                    else:
                        fingerprints[kernel].add(fingerprint)
                    if not isinstance(samples, list) or not 3 <= len(samples) <= 5:
                        incomplete_findings.append(f"{spec['id']}/{kernel}/{arm}/{replicate}: sample count outside 3..5")
                    if not isinstance(median_ns, int) or median_ns <= 0:
                        incomplete_findings.append(f"{spec['id']}/{kernel}/{arm}/{replicate}: invalid median_ns")
    if session_hosts:
        reference = session_hosts[0][1]
        for session_id, host in session_hosts[1:]:
            if any(host.get(field) != reference.get(field) for field in HOST_IDENTITY_FIELDS):
                provenance_findings.append(f"{session_id}: host identity differs across wall sessions")
    bad_fingerprints = [kernel for kernel, values in fingerprints.items() if len(values) != 1]
    provenance_findings.extend(f"{kernel}: fingerprint mismatch across arms/rounds/thread panels" for kernel in bad_fingerprints)
    exact_fingerprints = {
        kernel: next(iter(values)) for kernel, values in fingerprints.items() if len(values) == 1
    }
    preflight_blocked = False
    preflight_path = run_root / "orchestration/preflight.json"
    if preflight_path.is_file():
        try:
            preflight_receipt = load_json(preflight_path)
            recorded_findings = preflight_receipt.get("findings")
            preflight_inventory = preflight_receipt.get("required_files")
            runtime_observations = preflight_receipt.get("runtime_observations")
            preflight_blocked = (
                preflight_receipt.get("schema") == "cpu-baseline-aa-v5-preflight/v1"
                and preflight_receipt.get("status") == "blocked_identity_mismatch"
                and isinstance(recorded_findings, list) and bool(recorded_findings)
                and isinstance(preflight_inventory, list)
                and isinstance(runtime_observations, dict)
                and protocol is not None and recorded_findings == runner.identity_findings(
                    protocol, preflight_inventory, runtime_observations,
                )
                and parse_utc(preflight_receipt.get("checked_at")) is not None
            )
        except (ValueError, json.JSONDecodeError):
            pass
    terminal_status, terminal_findings = validate_terminal_state(run_root, wall_plan)
    provenance_findings.extend(terminal_findings)
    wall_acquisition_started = any(
        (run_root / f"orchestration/attempts/wall-{index:02d}-{spec['id']}/started.json").is_file()
        or (run_root / f"wall-{spec['panel']}/{spec['language']}/compare").exists()
        or isolation_path(wall_plan[index - 1]).exists()
        for index, spec in enumerate(session_specs(run_root), 1)
    )
    acquisition_paths = [
        run_root / "orchestration/attempts",
        run_root / "wall-1t",
        run_root / "wall-4t",
        run_root / "profiles",
        run_root / "orchestration/perf-record-selection.json",
        run_root / "orchestration/perf-record-command-plan.json",
    ]
    unexpected_acquisition = [
        str(path.relative_to(run_root)) for path in acquisition_paths if path.exists()
    ]
    if preflight_blocked and unexpected_acquisition:
        provenance_findings.append(
            "blocked preflight has forbidden wall/profile acquisition evidence: "
            + ", ".join(unexpected_acquisition)
        )
    if terminal_status == "preflight_identity_blocked" and not preflight_blocked:
        provenance_findings.append(
            "preflight_identity_blocked terminal lacks a causally matching blocked preflight"
        )
    clean_preflight_block = (
        preflight_blocked and terminal_status == "preflight_identity_blocked"
        and not wall_acquisition_started and not unexpected_acquisition
        and not terminal_findings
    )
    if preflight_blocked and not clean_preflight_block:
        provenance_findings.append("blocked preflight lacks its clean zero-acquisition terminal state")
    gate = {
        "schema": "cpu-baseline-aa-v5-wall-gate/v1",
        "planned_invocations": 1056,
        "retained_attempts": len(normalized),
        "completed_successes": sum(row.get("status") == "succeeded" for row in normalized),
        "failed_or_interrupted": sum(row.get("status") != "succeeded" for row in normalized),
        "observed_invocations": sum(row.get("status") == "succeeded" for row in normalized),
        "exported_planned_rows": 1056,
        "planned_cells": 88, "observed_cells": len(observed_cells),
        "false_direction_count": len(false_directions),
        "false_directions": false_directions, "schedule": schedule_records,
        "registry_contract": registry_detail,
        "system_noise": system_noise,
        "preflight_blocked": preflight_blocked,
        "clean_preflight_block": clean_preflight_block,
        "terminal_status": terminal_status,
        "cell_analysis": cell_analysis,
        "provenance_findings": provenance_findings,
        "incomplete_findings": incomplete_findings,
        "exactness_passes": not provenance_findings,
    }
    if clean_preflight_block:
        gate["verdict"] = "blocked_artifact_or_isolation"
    elif provenance_findings:
        gate["verdict"] = "invalid_exactness_or_provenance"
    elif incomplete_findings or sum(row.get("status") == "succeeded" for row in normalized) != 1056 or len(observed_cells) != 88:
        gate["verdict"] = "inconclusive_contention_or_incomplete"
    elif false_directions:
        gate["verdict"] = "baseline_aa_false_direction_nonqualified"
    else:
        gate["verdict"] = "baseline_aa_complete_nonqualified"
    return gate, normalized, first_host or {}, exact_fingerprints


def complete_planned_rows(
    run_root: Path, rows: list[dict[str, Any]], system_blockers: list[str],
) -> list[dict[str, Any]]:
    """Represent every planned execution cell, including a terminal wall stop."""
    by_key = {(row["arm"], row["instance_id"], row["replicate"]): row for row in rows}
    wall_plan = runner.build_plan()["wall"]
    qualification_blockers = [
        "nonqualified local KVM: no provider allocation receipt",
        "no physical-host exclusivity, fixed-frequency, IRQ, SMT, or NUMA attestation",
        "core hardware PMU unavailable; software events only",
        *system_blockers,
    ]
    registry = validate_registry_contract()[0]
    for index, spec in enumerate(session_specs(run_root), 1):
        record = wall_plan[index - 1]
        iso_contended: bool | None = None
        blockers = list(qualification_blockers)
        path = isolation_path(record)
        if path.is_file():
            try:
                receipts = load_jsonl(path)
                if len(receipts) == 1:
                    iso = receipts[0]
                    iso_contended = (
                        iso.get("contended_samples", 0) != 0
                        or iso.get("left_on_reserved") not in ({}, [])
                    )
                    if iso_contended:
                        blockers.append("isolated_bench reported local contention")
            except (ValueError, json.JSONDecodeError):
                blockers.append("malformed isolation receipt")
        else:
            blockers.append("missing isolation receipt")
        for kernel in spec["ids"]:
            for harness_arm, protocol_arm in spec["arms"].items():
                for replicate in range(1, 7):
                    key = (protocol_arm, kernel, replicate)
                    if key not in by_key:
                        by_key[key] = {
                            "run_id": f"wall-{spec['panel']}-{runner.safe_id(kernel)}-r{replicate:02d}-{harness_arm}",
                            "arm": protocol_arm, "instance_id": kernel,
                            "seed": 20260926, "replicate": replicate,
                            "warmup": False,
                            "status": "cancelled",
                            "wall_seconds": None, "tier": "nonqualified",
                            "verification": "error", "complete_invocations": 0,
                            "started_at": None, "finished_at": None,
                            "worker": None, "backend_ref": None,
                            "work_contract": runner.work_contract(
                                spec["id"], kernel, registry.get(kernel, {}),
                            )[0],
                            # The canonical schema requires attempts >= 1. A
                            # post-stop cell is a retained cancelled
                            # orchestration attempt, never a measured call.
                            "attempts": 1,
                        }
                    by_key[key]["isolation_contended"] = iso_contended
                    by_key[key]["isolation_blockers"] = blockers
                    by_key[key].setdefault("attempts", 1)
    completed = list(by_key.values())
    completed.sort(key=lambda row: (row["arm"], row["instance_id"], row["replicate"]))
    if len(completed) != 1056:
        raise ValueError(f"planned-row completion produced {len(completed)}, expected 1056")
    return completed


def profiles_not_reached(reason: str) -> dict[str, Any]:
    return {
        "callgrind": {"planned": 88, "attempted": 0, "succeeded": 0, "failed": 0,
                      "missing_attempts": [], "diagnostic_findings": [reason],
                      "aa_pair_mismatches": []},
        "perf_stat": {"planned": 88, "attempted": 0, "succeeded": 0, "failed": 0,
                      "missing_attempts": [], "diagnostic_findings": [reason]},
        "perf_record": {"planned": 8, "attempted": 0, "succeeded": 0, "failed": 0,
                        "selection": {"status": "not_reached_wall_gate"},
                        "diagnostic_findings": [reason]},
        "schedule_complete": False,
        "diagnostic_findings": [reason],
    }


def validate_perf_stat_csv(path: Path) -> list[str]:
    expected = {
        "task-clock": "msec", "cpu-clock": "msec",
        "context-switches": "", "page-faults": "",
    }
    observed: dict[str, float] = {}
    try:
        with path.open(newline="", encoding="utf-8") as stream:
            for row in csv.reader(line for line in stream if line.strip() and not line.startswith("#")):
                if len(row) < 3:
                    return ["perf-stat CSV has a short non-comment row"]
                event = row[2].strip()
                if event not in expected or event in observed:
                    return [f"perf-stat CSV has unexpected or duplicate event {event!r}"]
                if row[1].strip() != expected[event]:
                    return [
                        f"perf-stat event {event} unit {row[1].strip()!r} differs from {expected[event]!r}"
                    ]
                value_text = row[0].strip()
                try:
                    value = float(value_text)
                except ValueError:
                    return [f"perf-stat event {event} is not numeric: {value_text!r}"]
                if value < 0 or value != value or value in (float("inf"), float("-inf")):
                    return [f"perf-stat event {event} has invalid value"]
                if event in {"task-clock", "cpu-clock"} and value <= 0:
                    return [f"perf-stat event {event} must be positive"]
                observed[event] = value
    except OSError as error:
        return [f"cannot read perf-stat CSV: {error}"]
    return [] if set(observed) == set(expected) else [f"perf-stat event set {sorted(observed)} differs from frozen four"]


def validate_perf_data(path: Path, parse_with_perf: bool = True) -> list[str]:
    try:
        with path.open("rb") as stream:
            header = stream.read(8)
        size = path.stat().st_size
    except OSError as error:
        return [f"cannot read perf-record data: {error}"]
    if header != b"PERFILE2":
        return [f"perf-record data has wrong magic {header!r}"]
    if size < 104:
        return [f"perf-record data is too short ({size} bytes)"]
    if parse_with_perf:
        completed = subprocess.run(
            [
                str(runner.SYSTEM_ENV), "-i", "PATH=/usr/bin:/bin", "LC_ALL=C", "LANG=C",
                f"LD_LIBRARY_PATH={runner.PERF_LIB}", str(runner.PERF), "evlist", "-i", str(path),
            ],
            cwd=runner.REPO, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=60,
        )
        if completed.returncode != 0:
            return [f"perf-record data is not parseable by frozen perf evlist: {completed.stderr[-500:]}"]
        if "cpu-clock" not in completed.stdout:
            return ["perf-record data lacks the frozen cpu-clock event"]
        scripted = subprocess.run(
            [
                str(runner.SYSTEM_ENV), "-i", "PATH=/usr/bin:/bin", "LC_ALL=C", "LANG=C",
                f"LD_LIBRARY_PATH={runner.PERF_LIB}", str(runner.PERF), "script", "-i", str(path),
            ],
            cwd=runner.REPO, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=60,
        )
        if scripted.returncode != 0:
            return [f"perf-record samples are not parseable by frozen perf script: {scripted.stderr[-500:]}"]
        lines = scripted.stdout.splitlines()
        if not any("cpu-clock:" in line for line in lines):
            return ["perf-record contains no cpu-clock sample"]
        if not any(line[:1].isspace() and line.strip() for line in lines):
            return ["perf-record contains no callchain frame despite -g --call-graph dwarf"]
    return []


def validate_profile_stdout(
    run_root: Path, name: str, record: dict[str, Any], wall_fingerprint: str | None,
) -> tuple[list[str], str]:
    path = run_root / "orchestration/attempts" / name / "stdout.txt"
    findings: list[str] = []
    if not path.is_file():
        return ["captured benchmark stdout is missing"], ""
    row, error = parse_single_benchmark_stdout(path.read_text(encoding="utf-8", errors="replace"))
    if error is not None or row is None:
        return [error or "captured benchmark row is missing"], ""
    findings.extend(validate_benchmark_row(row, record["kernel"], expected_samples=5))
    if wall_fingerprint is None or row.get("fingerprint") != wall_fingerprint:
        findings.append("profiled benchmark fingerprint differs from the complete wall contract")
    session = "rust-1t" if record["kernel"] in runner.RUST_IDS else "c-1t"
    registry = validate_registry_contract()[0]
    contract, _ = runner.work_contract(session, record["kernel"], registry.get(record["kernel"], {}))
    return findings, contract


def profile_inventory(run_root: Path, wall_fingerprints: dict[str, str]) -> dict[str, Any]:
    """Audit all diagnostic attempts; failures are retained but never wall evidence."""
    plan = runner.build_plan()
    result: dict[str, Any] = {}
    all_findings: list[str] = []
    statuses_by_phase: dict[str, list[int]] = {}

    for phase in ("callgrind", "perf_stat"):
        statuses: list[int] = []
        missing_attempts: list[str] = []
        phase_findings: list[str] = []
        phase_contracts: dict[str, str] = {}
        for record in plan[phase]:
            name = f"{phase}-{record['ordinal']:03d}-{record['arm']}"
            status, provenance, incomplete = validate_attempt(
                run_root, name, record, require_zero=False,
            )
            phase_findings.extend(provenance)
            phase_findings.extend(incomplete)
            if status is None:
                missing_attempts.append(name)
                continue
            statuses.append(status)
            iso_provenance, iso_incomplete = validate_isolation(
                record, status, require_quiet=False,
            )
            phase_findings.extend(iso_provenance)
            phase_findings.extend(iso_incomplete)
            output = Path(record["output"])
            if phase == "callgrind" and status == 0:
                row, error = runner.validated_callgrind_result(
                    run_root, record, wall_fingerprints.get(record["kernel"]),
                )
                if row is None:
                    phase_findings.append(f"{name}: {error}")
            elif phase == "perf_stat" and status == 0:
                stdout_findings, contract = validate_profile_stdout(
                    run_root, name, record, wall_fingerprints.get(record["kernel"]),
                )
                phase_findings.extend(f"{name}: {item}" for item in stdout_findings)
                phase_contracts[name] = contract
                if not output.is_file() or output.stat().st_size == 0:
                    phase_findings.append(f"{name}: successful perf-stat attempt lacks CSV output")
                else:
                    phase_findings.extend(f"{name}: {item}" for item in validate_perf_stat_csv(output))
        statuses_by_phase[phase] = statuses
        result[phase] = {
            "planned": 88, "attempted": len(statuses),
            "succeeded": sum(code == 0 for code in statuses),
            "failed": sum(code != 0 for code in statuses),
            "missing_attempts": missing_attempts, "diagnostic_findings": phase_findings,
            "work_contracts": phase_contracts,
        }
        all_findings.extend(phase_findings)

    pair_mismatches: list[str] = []
    by_pair: dict[str, dict[str, dict[str, Any]]] = {}
    for record in plan["callgrind"]:
        row, _ = runner.validated_callgrind_result(
            run_root, record, wall_fingerprints.get(record["kernel"]),
        )
        if row is not None:
            by_pair.setdefault(record["kernel"], {})[record["arm"]] = row
    for kernel, arms in sorted(by_pair.items()):
        if set(arms) == {"A", "B"} and (
            arms["A"].get("fingerprint") != arms["B"].get("fingerprint")
            or arms["A"].get("ir") != arms["B"].get("ir")
        ):
            pair_mismatches.append(kernel)
    result["callgrind"]["aa_pair_mismatches"] = pair_mismatches
    all_findings.extend(f"callgrind A/A mismatch: {kernel}" for kernel in pair_mismatches)

    selection_path = run_root / "orchestration/perf-record-selection.json"
    record_findings: list[str] = []
    if selection_path.is_file():
        try:
            selection = load_json(selection_path)
        except (ValueError, json.JSONDecodeError) as error:
            selection = {"status": "malformed"}
            record_findings.append(f"perf-record selection is malformed: {error}")
    else:
        selection = {"status": "absent"}
    record_statuses: list[int] = []
    record_contracts: dict[str, str] = {}
    expected_record_commands: list[dict[str, Any]] | None = None
    c_counts: dict[str, int] = {}
    for record in plan["callgrind"]:
        if record["arm"] != "A" or record["kernel"] not in runner.C_IDS:
            continue
        row, _ = runner.validated_callgrind_result(
            run_root, record, wall_fingerprints.get(record["kernel"]),
        )
        if row is not None:
            c_counts[record["kernel"]] = row["ir"]
    if len(c_counts) == len(runner.C_IDS):
        selected = runner.select_perf_record_from_counts(c_counts)
        expected_record_commands = [
            runner.perf_record_command(index, kernel)
            for index, kernel in enumerate(selected, 1)
        ]
        expected_selection = {
            "status": "selected", "selected": selected,
            "commands_sha256": runner.digest_value(expected_record_commands),
            "c_baseline_ir": dict(sorted(c_counts.items())),
        }
        if selection != expected_selection:
            record_findings.append("perf-record selection differs from the frozen Ir ranking rule")
        command_plan_path = run_root / "orchestration/perf-record-command-plan.json"
        try:
            observed_commands = (
                json.loads(command_plan_path.read_text()) if command_plan_path.is_file() else None
            )
        except (OSError, json.JSONDecodeError) as error:
            observed_commands = None
            record_findings.append(f"perf-record selected command plan is malformed: {error}")
        if observed_commands != expected_record_commands:
            record_findings.append("perf-record selected command plan missing or mismatched")
    else:
        missing = [kernel for kernel in runner.C_IDS if kernel not in c_counts]
        expected_selection = {"status": "not_attempted_missing_c_callgrind_a", "missing": missing}
        if selection != expected_selection:
            record_findings.append("perf-record not-attempted receipt differs from missing C Callgrind inputs")
        if (run_root / "orchestration/perf-record-command-plan.json").exists():
            record_findings.append("perf-record command plan exists despite incomplete selection inputs")

    if expected_record_commands is not None:
        for record in expected_record_commands:
            name = f"perf-record-{record['ordinal']:03d}"
            status, provenance, incomplete = validate_attempt(
                run_root, name, record, require_zero=False,
            )
            record_findings.extend(provenance)
            record_findings.extend(incomplete)
            if status is None:
                continue
            record_statuses.append(status)
            iso_provenance, iso_incomplete = validate_isolation(
                record, status, require_quiet=False,
            )
            record_findings.extend(iso_provenance)
            record_findings.extend(iso_incomplete)
            output = Path(record["output"])
            if status == 0:
                stdout_findings, contract = validate_profile_stdout(
                    run_root, name, record, wall_fingerprints.get(record["kernel"]),
                )
                record_findings.extend(f"{name}: {item}" for item in stdout_findings)
                record_contracts[name] = contract
            if status == 0 and (not output.is_file() or output.stat().st_size == 0):
                record_findings.append(f"{name}: successful perf-record attempt lacks data output")
            elif status == 0:
                record_findings.extend(f"{name}: {item}" for item in validate_perf_data(output))
    else:
        unexpected = sorted((run_root / "orchestration/attempts").glob("perf-record-*/receipt.json"))
        if unexpected:
            record_findings.append("perf-record attempts exist without a complete frozen selection")

    result["perf_record"] = {
        "planned": 8, "attempted": len(record_statuses), "selection": selection,
        "succeeded": sum(code == 0 for code in record_statuses),
        "failed": sum(code != 0 for code in record_statuses),
        "diagnostic_findings": record_findings, "work_contracts": record_contracts,
    }
    all_findings.extend(record_findings)
    result["schedule_complete"] = (
        len(statuses_by_phase.get("callgrind", [])) == 88
        and len(statuses_by_phase.get("perf_stat", [])) == 88
        and expected_record_commands is not None
        and len(record_statuses) == 8
    )
    result["diagnostic_findings"] = all_findings
    return result


def relative_file(root: Path, path: Path, kind: str) -> dict[str, Any]:
    return {"path": str(path.relative_to(root)), "sha256": sha256(path),
            "bytes": path.stat().st_size, "kind": kind}


def memory_bytes(value: Any) -> int | None:
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"(\d+)\s+kB", value)
    return int(match.group(1)) * 1024 if match else None


def verify_start(run_root: Path, protocol: dict[str, Any], plan_path: Path,
                 plan: dict[str, Any]) -> None:
    start_path = run_root / "orchestration/start.json"
    if not start_path.is_file():
        raise ValueError("missing orchestration start receipt")
    start = load_json(start_path)
    expected = {
        "protocol_sha256": protocol["freeze"]["protocol_sha256"],
        "plan_sha256": sha256(plan_path),
        "plan_preimage_sha256": plan["digests"]["plan_preimage"],
        "other_cpu_work_paused_confirmed": True,
        "resume_policy": "forbidden",
    }
    for field, value in expected.items():
        if start.get(field) != value:
            raise ValueError(f"orchestration start receipt mismatch: {field}")


def make_export(protocol_path: Path, protocol: dict[str, Any], run_root: Path,
                rows_path: Path, analysis_path: Path, report_path: Path,
                cells_path: Path, host: dict[str, Any], gate: dict[str, Any],
                profiles: dict[str, Any]) -> dict[str, Any]:
    export = tool.from_rows(
        rows_path, protocol, str(protocol_path), "cpu-baseline-aa-v5", {}, "",
    )
    # from_rows intentionally parses numeric-looking counted values.  A
    # fingerprint is an opaque exact string even in the all-decimal corner
    # case, so restore both exact fields from the normalized source rows.
    normalized_by_id = {
        row["run_id"]: row
        for row in (
            json.loads(line) for line in rows_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }
    for exported_row in export["runs"]:
        source_row = normalized_by_id[exported_row["run_id"]]
        if source_row.get("output_fingerprint") is not None:
            exported_row["measurements"]["counted"]["output_fingerprint"] = source_row["output_fingerprint"]
        if source_row.get("work_contract") is not None:
            exported_row["measurements"]["counted"]["work_contract"] = source_row["work_contract"]
        exported_row["attempts"] = source_row.get("attempts", 1)
        for field in ("started_at", "finished_at", "worker", "backend_ref"):
            exported_row[field] = source_row.get(field)
        exported_row["isolation"]["contended"] = source_row.get("isolation_contended")
        exported_row["isolation"]["blockers"] = source_row.get("isolation_blockers", [])
    export["producer"] = {"runtime": "codex_cli", "model": None, "session": None, "role": "executor"}
    export["source"] = {"repo": "cryptanalysis", "commit": "781722ef89e74b62079d2bc0cb82217061ac188c", "dirty": False}
    export["backend"] = "local"
    protocol_arms = {arm["id"]: arm for arm in protocol["arms"]}
    for arm in export["arms"]:
        instrument = protocol_arms[arm["id"]]["instrument"]
        arm["binary_sha256"] = instrument["binary_sha256"]
        arm["commit"] = instrument["commit"]
    host_files = [
        run_root / "wall-1t/rust/compare/session.json",
        run_root / "wall-1t/c/compare/session.json",
        run_root / "wall-4t/rust/compare/session.json",
        run_root / "wall-4t/c/compare/session.json",
        run_root / "wall-1t/rust/compare/compare.json",
        run_root / "wall-1t/c/compare/compare.json",
        run_root / "wall-4t/rust/compare/compare.json",
        run_root / "wall-4t/c/compare/compare.json",
    ]
    host_file = next((path for path in host_files if path.is_file()), None)
    export["host"] = {
        "path": str(host_file.relative_to(run_root)) if host_file else None,
        "sha256": sha256(host_file) if host_file else None, "class_id": None,
        "summary": {
            "cpu_model": host.get("cpu"), "logical_cpus": host.get("logical_cores"),
            "memory_bytes": memory_bytes(host.get("memory")), "kernel": host.get("os"),
            "hypervisor": "KVM", "isolation_tier_max": "nonqualified", "gpu": None,
            "instance_type": None, "spot": None,
        },
    }
    export["analysis"] = {
        "script": {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__).resolve()),
                   "bytes": Path(__file__).stat().st_size, "kind": "analysis"},
        "blinded": False, "blinding_key_sha256": None,
        "outputs": [relative_file(run_root, analysis_path, "analysis"),
                    relative_file(run_root, report_path, "report"),
                    relative_file(run_root, run_root / "analysis/wall-gate.json", "analysis"),
                    relative_file(run_root, cells_path, "analysis")],
        "unmasked_at": None,
    }
    ignored = {
        run_root / "export.json",
        run_root / "orchestration/finalization.json",
        run_root / "orchestration/finalization-failure.json",
    }
    export["files"] = []
    for path in sorted(run_root.rglob("*")):
        if path.is_file() and path not in ignored and not (
            path.name.startswith(".") and ".tmp-" in path.name
        ):
            kind = "raw"
            if path.name.endswith("receipt.json") or path.name.endswith("isolation.jsonl"):
                kind = "receipt"
            elif path.suffix in {".md"}:
                kind = "report"
            elif path.name in {"analysis.json", "wall-gate.json"}:
                kind = "analysis"
            export["files"].append(relative_file(run_root, path, kind))
    export["notes"] = [{
        "kind": "observation",
        "text": (
            f"The wall gate retained {gate['retained_attempts']} attempts, completed "
            f"{gate['completed_successes']} invocations, and found "
            f"{gate['false_direction_count']} false directional verdicts; every wall clock remains nonqualified."
        ),
        "by": "analyze_cpu_baseline_aa_v5.py",
    }]
    export["reviews_dir"] = "reviews"
    export["backend_record"] = {
        "wall_verdict": gate["verdict"],
        "command_plan_sha256": sha256(run_root / "orchestration/command-plan.json"),
        "command_plan_preimage_sha256": runner.build_plan()["digests"]["plan_preimage"],
        "profile_schedule_complete": profiles["schedule_complete"],
        "wall_counts": {
            key: gate[key] for key in (
                "planned_invocations", "retained_attempts", "completed_successes",
                "failed_or_interrupted", "exported_planned_rows",
            )
        },
        "profile_attempts": {
            phase: profiles[phase]["attempted"]
            for phase in ("callgrind", "perf_stat", "perf_record")
        },
    }
    export["flow"] = tool.compute_flow(export["runs"])
    return export


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--wall-gate-only", action="store_true")
    options = parser.parse_args()
    protocol_path = options.protocol.resolve()
    run_root = options.run_root.resolve()
    if run_root != runner.RUN_ROOT.resolve():
        raise ValueError(f"run root is not the frozen one-shot path: {run_root}")
    protocol = verify_protocol(protocol_path)
    plan_path = run_root / "orchestration/command-plan.json"
    plan = load_json(plan_path)
    expected_plan = runner.build_plan()
    if plan != expected_plan:
        raise ValueError("retained command plan differs from frozen generator")
    if plan["digests"] != protocol["extensions"]["cpu_baseline_aa_v5"]["command_plan_digests"]:
        raise ValueError("retained command-plan digest mismatch")
    verify_start(run_root, protocol, plan_path, plan)
    gate, rows, host, wall_fingerprints = analyze_wall(run_root, protocol)
    wall_complete = gate["verdict"] in {
        "baseline_aa_complete_nonqualified", "baseline_aa_false_direction_nonqualified",
    }
    if options.wall_gate_only:
        return 0 if wall_complete else 1
    gate_path = run_root / "analysis/wall-gate.json"
    write_json_once(gate_path, gate)

    campaign_noise, campaign_provenance, campaign_incomplete = validate_campaign_after(run_root)

    complete_path = run_root / "orchestration/complete.json"
    terminal_path = run_root / "orchestration/terminal.json"
    orchestration_complete = False
    if complete_path.is_file():
        complete_receipt = load_json(complete_path)
        orchestration_complete = (
            complete_receipt.get("status") == "orchestration_complete"
            and parse_utc(complete_receipt.get("finished_at")) is not None
        )
        if not orchestration_complete:
            raise ValueError("orchestration completion receipt is malformed")
    terminal: dict[str, Any] | None = None
    if terminal_path.is_file():
        terminal = load_json(terminal_path)
        if (
            terminal.get("schema") != "cpu-baseline-aa-v5-terminal/v1"
            or terminal.get("continuation") != "forbidden"
            or parse_utc(terminal.get("finished_at")) is None
            or terminal.get("status") not in TERMINAL_STATUSES
        ):
            raise ValueError("terminal receipt is malformed")
    if orchestration_complete and terminal is not None:
        raise ValueError("completed orchestration also has a contradictory terminal receipt")
    if wall_complete:
        if not orchestration_complete and terminal is None:
            raise ValueError("complete wall panel without completion/terminal seal; use finalize")
        profiles = profile_inventory(run_root, wall_fingerprints)
    else:
        profiles = profiles_not_reached("wall gate terminated the campaign before diagnostics")
    profiles["campaign_boundary_noise"] = campaign_noise
    profiles["campaign_boundary_provenance_findings"] = campaign_provenance
    profiles["campaign_boundary_incomplete_findings"] = campaign_incomplete
    rows = complete_planned_rows(run_root, rows, gate["system_noise"]["blockers"])
    expected_seed_table = {
        (row["arm"], row["instance_id"], row["replicate"]): row["seed"]
        for row in runner.export_seed_table()
    }
    observed_seed_table = {
        (row["arm"], row["instance_id"], row["replicate"]): row["seed"]
        for row in rows
    }
    if observed_seed_table != expected_seed_table or len(rows) != len(expected_seed_table):
        raise ValueError("export rows differ from the frozen descriptive one-based seed table")
    rows_path = run_root / "rows.jsonl"
    rows_text = "".join(
        json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows
    )
    write_text_once(rows_path, rows_text)
    final_verdict = gate["verdict"]
    if wall_complete and not orchestration_complete:
        final_verdict = "inconclusive_contention_or_incomplete"
    analysis = {
        "schema": "cpu-baseline-aa-v5-analysis/v1",
        "protocol_sha256": protocol["freeze"]["protocol_sha256"],
        "wall": gate, "profiles": profiles,
        "diagnostic_policy": "Callgrind/perf failures do not alter the wall A/A verdict and no profile supports a speedup claim.",
        "campaign_status": (
            "orchestration_complete" if orchestration_complete
            else "sealed_terminal_incomplete"
        ),
        "terminal": terminal,
        "verdict": final_verdict,
    }
    analysis_path = run_root / "analysis/analysis.json"
    write_json_once(analysis_path, analysis)
    cells_path = run_root / "analysis/cells.json"
    write_json_once(cells_path, {
        "schema": "cpu-baseline-aa-v5-cell-table/v1",
        "planned_cells": 88, "observed_cells": len(gate["cell_analysis"]),
        "cells": gate["cell_analysis"],
    })
    report_path = run_root / "analysis/REPORT.md"
    write_text_once(report_path, (
        "# CPU baseline A/A v5\n\n"
        f"Final verdict: `{final_verdict}` (wall gate: `{gate['verdict']}`).\n\n"
        f"Planned: 1056; retained attempts: {gate['retained_attempts']}; "
        f"completed successes: {gate['completed_successes']}; failed/interrupted: "
        f"{gate['failed_or_interrupted']}; exported planned rows: 1056.\n\n"
        f"False directional verdicts: {gate['false_direction_count']}.\n\n"
        "All wall clocks are nonqualified local observations. Callgrind and perf are diagnostics only.\n"
    ))
    candidate = make_export(protocol_path, protocol, run_root, rows_path, analysis_path,
                            report_path, cells_path, host, gate, profiles)
    export_path = run_root / "export.json"
    if export_path.is_file():
        try:
            export = load_json(export_path)
        except (OSError, ValueError, json.JSONDecodeError):
            export = candidate
        else:
            candidate["created"] = export.get("created")
            if export != candidate:
                if (run_root / "orchestration/finalization.json").is_file():
                    raise ValueError("validated export differs from deterministic recomputation")
                export = candidate
    else:
        export = candidate
    findings = tool.schema_errors(export, "experiment.export/v1") or tool.lint_export(
        export, protocol, run_root, True,
    )
    if findings:
        raise ValueError("export validation failed:\n  " + "\n  ".join(findings))
    write_json_once(export_path, export)
    subprocess.run(
        runner.closed_python_command(
            TOOL_PATH, "check-export", "--protocol", str(protocol_path),
            "--verify-files", str(export_path),
        ),
        check=True, cwd=run_root, timeout=60,
    )
    scientific_returncode = 0 if wall_complete and orchestration_complete else 1
    finalization_path = run_root / "orchestration/finalization.json"
    finalization = {
        "schema": "cpu-baseline-aa-v5-finalization/v1", "status": "validated",
        "export_sha256": sha256(export_path),
        "analyzer_sha256": sha256(Path(__file__).resolve()),
        "scientific_returncode": scientific_returncode,
        "completed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    if finalization_path.exists():
        try:
            observed_finalization = load_json(finalization_path)
        except (OSError, ValueError, json.JSONDecodeError):
            write_json_once(finalization_path, finalization)
            observed_finalization = finalization
        for field in ("schema", "status", "export_sha256", "analyzer_sha256", "scientific_returncode"):
            if observed_finalization.get(field) != finalization[field]:
                raise ValueError(f"existing finalization receipt differs at {field}")
        if parse_utc(observed_finalization.get("completed_at")) is None:
            raise ValueError("existing finalization receipt has an invalid timestamp")
    else:
        write_json_once(finalization_path, finalization)
    return scientific_returncode


if __name__ == "__main__":
    raise SystemExit(main())
