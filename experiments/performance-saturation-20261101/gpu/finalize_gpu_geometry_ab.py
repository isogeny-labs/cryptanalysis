#!/usr/bin/env python3
"""Issue the sole terminal verdict for the v10 GPU geometry experiment.

This controller-side program is intentionally run only after the HTTP batch
controller has returned.  The remote analyzer cannot observe the final result
archive or exact-ID pod cleanup and therefore emits only a provisional timing
classification.  This finalizer validates the frozen protocol, transport,
archive, extracted evidence, schedule, export, and provisional analysis before
writing one immutable terminal record.

Scientific failures are represented by the record and return status zero.
Status two is reserved for bad CLI use or inability to create that record.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tarfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


PROTOCOL_ID = "gpu-f4-update-grid-ab-rtx5090-http-v10-20261101"
PROTOCOL_VERSION = 10
EXPECTED_GPU = "NVIDIA GeForce RTX 5090"
EXPECTED_PROTOCOL_TOOL_SHA256 = (
    "0f46a2b856bb1df2d155c4a676b46c6118d82c45cf8e5cc0492315aeb45c84e4"
)
EXPECTED_ANALYSIS_SCHEMA = "gpu-f4-update-grid-ab-analysis/v2"
EXPECTED_EXPORT_SCHEMA = "experiment.export/v1"
EXPECTED_RECEIPT_SCHEMA = "runpod.http-batch.receipt/v1"
EXPECTED_STATUS_SCHEMA = "runpod.http-batch.status/v1"
EXPECTED_UPDATE_LAUNCHES = 2941
EXPECTED_KERNEL_LAUNCHES = 11765
EXPECTED_RESOURCES = {
    "threads_per_block": 256,
    "registers_per_thread": 31,
    "static_shared_bytes": 16384,
    "dynamic_shared_bytes": 0,
    "local_bytes_per_thread": 0,
}
ARMS = ("baseline", "candidate")
WORKLOADS = (
    ("holdout", "k0n13m2d5", "0:13:2:1234", 5),
    ("holdout", "k0n9m3d5", "0:9:3:77", 5),
    ("holdout", "k1n11m2d5", "1:11:2:301", 5),
    ("holdout", "k1n11m2d6", "1:11:2:301", 6),
    ("primary", "k0n13m2d6", "0:13:2:1234", 6),
)
ORDER_HEADER = ("phase", "round", "workload", "role", "arm", "cell_degree")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
POD_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{1,127}$")
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,120}$")
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
REMOTE_NAMES = {
    "files.sha256",
    "job-status.json",
    "log.txt",
    "source.json",
}
MAX_JSON_BYTES = 64 * 1024 * 1024
MAX_MANIFEST_BYTES = 32 * 1024 * 1024


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def maybe_sha256_file(path: Path) -> str | None:
    try:
        return sha256_file(path) if path.is_file() else None
    except OSError:
        return None


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def protocol_hash(value: dict[str, Any]) -> str:
    return sha256_bytes(canonical({key: item for key, item in value.items() if key != "freeze"}))


def parse_utc(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        if value.endswith("Z"):
            parsed = datetime.fromisoformat(value[:-1] + "+00:00")
        else:
            parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def json_from_bytes(value: bytes) -> Any:
    return json.loads(value.decode("utf-8"), parse_constant=lambda token: (_ for _ in ()).throw(
        ValueError(f"non-finite JSON token {token}")))


def read_json(path: Path) -> Any:
    if path.stat().st_size > MAX_JSON_BYTES:
        raise ValueError("JSON exceeds frozen size limit")
    return json_from_bytes(path.read_bytes())


@dataclass
class Check:
    code: str
    category: str
    status: str
    detail: str


class Judge:
    """Accumulate all observable checks without losing terminal precedence."""

    def __init__(self) -> None:
        self.checks: list[Check] = []

    def check(self, condition: bool, code: str, category: str, detail: str) -> bool:
        self.checks.append(Check(code, category, "passed" if condition else "failed", detail))
        return condition

    def missing(self, code: str, detail: str) -> None:
        self.checks.append(Check(code, "completion", "missing", detail))

    def invalid(self, code: str, detail: str) -> None:
        self.checks.append(Check(code, "validity", "failed", detail))

    def incomplete(self, code: str, detail: str) -> None:
        self.checks.append(Check(code, "completion", "failed", detail))

    @property
    def completion_failed(self) -> bool:
        return any(item.category == "completion" and item.status != "passed" for item in self.checks)

    @property
    def validity_failed(self) -> bool:
        return any(item.category == "validity" and item.status != "passed" for item in self.checks)


def terminal_verdict(judge: Judge, provisional: str | None) -> str:
    """Frozen precedence: incomplete, invalid, not-supported, supported."""
    if judge.completion_failed:
        return "incomplete_session"
    if judge.validity_failed:
        return "invalid_measurement"
    if provisional == "geometry_not_supported":
        return "geometry_not_supported"
    if provisional == "geometry_supported":
        return "geometry_supported"
    # Absence of an admissible provisional value is completion failure in the
    # caller.  Keep this total for direct unit testing and defensive use.
    return "incomplete_session"


def expected_order() -> list[tuple[str, ...]]:
    rows: list[tuple[str, ...]] = []
    for phase, round_index in [("warmup", 0), *[("measure", index) for index in range(1, 7)]]:
        arms = ("baseline", "candidate") if round_index % 2 else ("candidate", "baseline")
        for role, tag, cell, degree in WORKLOADS:
            for arm in arms:
                rows.append((phase, str(round_index), tag, role, arm, f"{cell}:{degree}"))
    return rows


def validate_order(path: Path, judge: Judge) -> None:
    try:
        with path.open(newline="", encoding="utf-8") as stream:
            rows = [tuple(row) for row in csv.reader(stream, delimiter="\t")]
    except (OSError, UnicodeError, csv.Error) as exc:
        judge.incomplete("order.readable", f"order.tsv unreadable: {exc}")
        return
    if not rows:
        judge.incomplete("order.present", "order.tsv is empty")
        return
    judge.check(rows[0] == ORDER_HEADER, "order.header", "validity", "exact six-column order header")
    expected = expected_order()
    judge.check(
        rows[1:] == expected,
        "order.schedule",
        "validity",
        f"exact registered 70-row schedule (observed {len(rows) - 1})",
    )


def load_required_json(path: Path, label: str, judge: Judge) -> Any | None:
    if not path.is_file() or path.stat().st_size == 0:
        judge.missing(f"{label}.present", f"missing or empty {path}")
        return None
    try:
        value = read_json(path)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        judge.incomplete(f"{label}.readable", f"unreadable {label}: {exc}")
        return None
    judge.check(True, f"{label}.readable", "completion", f"{label} is readable JSON")
    return value


def load_rows(path: Path, judge: Judge) -> list[dict[str, Any]] | None:
    if not path.is_file() or path.stat().st_size == 0:
        judge.missing("rows.present", "rows.jsonl is missing or empty")
        return None
    rows: list[dict[str, Any]] = []
    try:
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            value = json.loads(line, parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-finite token {token}")))
            if not isinstance(value, dict):
                raise ValueError(f"line {line_number} is not an object")
            rows.append(value)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        judge.incomplete("rows.readable", f"rows.jsonl is partial or invalid: {exc}")
        return None
    judge.check(True, "rows.readable", "completion", "rows.jsonl is complete JSONL")
    return rows


@dataclass
class ArchiveEvidence:
    records: dict[str, dict[str, Any]]
    payloads: dict[str, bytes]
    manifest_bytes: bytes


def inspect_archive(path: Path, judge: Judge) -> ArchiveEvidence | None:
    """Verify the internal manifest and retain only small controller metadata."""
    if not path.is_file() or path.stat().st_size == 0:
        judge.missing("archive.present", "result archive is missing or empty")
        return None
    records: dict[str, dict[str, Any]] = {}
    payloads: dict[str, bytes] = {}
    manifest_bytes = b""
    try:
        with tarfile.open(path, "r:gz") as archive:
            members = archive.getmembers()
            for member in members:
                name = member.name
                pure = PurePosixPath(name)
                safe = (
                    name not in records and pure.as_posix() == name and not pure.is_absolute()
                    and ".." not in pure.parts and ".git" not in pure.parts and member.isfile()
                )
                if not safe:
                    raise ValueError(f"unsafe, duplicate, or non-file archive member {name!r}")
                stream = archive.extractfile(member)
                if stream is None:
                    raise ValueError(f"unreadable archive member {name!r}")
                digest = hashlib.sha256()
                retained = bytearray()
                retain = name.startswith(".runpod-batch/")
                size = 0
                for block in iter(lambda: stream.read(1 << 20), b""):
                    digest.update(block)
                    size += len(block)
                    if retain:
                        if len(retained) + len(block) > MAX_MANIFEST_BYTES:
                            raise ValueError(f"metadata member too large: {name}")
                        retained.extend(block)
                if size != member.size:
                    raise ValueError(f"short archive member {name!r}")
                records[name] = {"path": name, "sha256": digest.hexdigest(), "bytes": size}
                if retain:
                    payloads[name] = bytes(retained)
            manifest_name = ".runpod-batch/files.sha256"
            if manifest_name not in payloads:
                raise ValueError("archive has no internal files.sha256")
            manifest_bytes = payloads[manifest_name]
            manifest: dict[str, str] = {}
            for line in manifest_bytes.decode("utf-8").splitlines():
                digest, separator, name = line.partition("  ")
                if (
                    not separator or SHA256_RE.fullmatch(digest) is None or name in manifest
                    or name == manifest_name
                ):
                    raise ValueError("invalid internal manifest row")
                manifest[name] = digest
            actual = set(records) - {manifest_name}
            if set(manifest) != actual:
                raise ValueError("internal manifest inventory is not exact")
            for name, digest in manifest.items():
                if records[name]["sha256"] != digest:
                    raise ValueError(f"internal manifest hash mismatch for {name}")
    except (OSError, EOFError, UnicodeError, ValueError, tarfile.TarError) as exc:
        judge.incomplete("archive.integrity", f"corrupt/incomplete result archive: {exc}")
        return None
    judge.check(True, "archive.integrity", "completion", "gzip/tar/internal manifest are exact")
    return ArchiveEvidence(records, payloads, manifest_bytes)


def check_canonical(
    protocol_tool: Path,
    protocol_path: Path,
    export_path: Path | None,
    judge: Judge,
) -> None:
    if not protocol_tool.is_file():
        judge.invalid("canonical_tool.present", f"canonical tool is missing: {protocol_tool}")
        return
    actual = sha256_file(protocol_tool)
    judge.check(
        actual == EXPECTED_PROTOCOL_TOOL_SHA256,
        "canonical_tool.sha256",
        "validity",
        f"canonical tool SHA-256 {actual}",
    )
    commands = [[sys.executable, str(protocol_tool), "validate", str(protocol_path)]]
    if export_path is not None and export_path.is_file():
        commands.append([
            sys.executable, str(protocol_tool), "check-export", str(export_path),
            "--protocol", str(protocol_path), "--verify-files",
        ])
    else:
        judge.missing("canonical.export_input", "export is unavailable to canonical validator")
    for index, command in enumerate(commands):
        label = "protocol" if index == 0 else "export"
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=120, check=False)
            clean = result.returncode == 0 and "0 finding(s)" in result.stdout
            detail = (result.stdout + result.stderr).strip()[:2000]
            judge.check(clean, f"canonical.{label}", "validity", detail or "no validator output")
        except (OSError, subprocess.SubprocessError) as exc:
            judge.invalid(f"canonical.{label}", f"canonical validator failed to run: {exc}")


def substitute(template: str, run_id: str, protocol_sha: str) -> str:
    return template.replace("<run_id>", run_id).replace("<frozen_protocol_sha256>", protocol_sha)


def check_receipt_core(
    receipt: dict[str, Any],
    protocol: dict[str, Any],
    run_id: str,
    protocol_sha: str,
    session_rel: str,
    judge: Judge,
) -> None:
    extensions = protocol.get("extensions", {})
    tooling = extensions.get("tooling_source", {})
    launch = extensions.get("launch", {})
    placement = protocol.get("execution", {}).get("placement", {})
    finalization = extensions.get("finalization", {})

    expected_receipt_keys = {
        "schema", "provider_actions", "source", "command", "command_sha256",
        "outputs", "request", "transport", "started_at", "pod", "remote_status",
        "result", "cleanup", "error", "finished_at",
    }
    judge.check(set(receipt) == expected_receipt_keys, "receipt.keys", "validity", "exact controller receipt key set")

    judge.check(receipt.get("schema") == EXPECTED_RECEIPT_SCHEMA, "receipt.schema", "validity", "exact HTTP receipt schema")
    judge.check(receipt.get("provider_actions") is True, "receipt.provider_actions", "validity", "real controller receipt")
    judge.check(receipt.get("error") is None, "receipt.no_error", "completion", f"controller error={receipt.get('error')!r}")
    judge.check(receipt.get("outputs") == [session_rel], "receipt.outputs", "validity", "exact single declared output root")

    source = receipt.get("source") if isinstance(receipt.get("source"), dict) else {}
    expected_source = {
        "origin": tooling.get("public_origin"),
        "ref": tooling.get("public_ref"),
        "commit": tooling.get("commit"),
        "tree": tooling.get("tree"),
        "archive_sha256": tooling.get("git_archive_sha256"),
    }
    for key, expected in expected_source.items():
        judge.check(source.get(key) == expected, f"receipt.source.{key}", "validity", f"expected {expected!r}")
    judge.check(source.get("public_ref_checked") is True, "receipt.source.public_ref", "validity", "public ref was checked without credentials")
    judge.check(parse_utc(source.get("public_checked_at")) is not None, "receipt.source.checked_at", "validity", "public check has a timestamp")

    argv = launch.get("controller_argv_template", [])
    command_template = argv[-1] if isinstance(argv, list) and argv else None
    expected_command = substitute(command_template, run_id, protocol_sha) if isinstance(command_template, str) else None
    command = receipt.get("command")
    judge.check(command == expected_command, "receipt.command", "validity", "exact registered remote command")
    command_sha = sha256_bytes(command.encode()) if isinstance(command, str) else None
    judge.check(receipt.get("command_sha256") == command_sha, "receipt.command_sha256", "validity", "command bytes are hash-bound")

    request = receipt.get("request") if isinstance(receipt.get("request"), dict) else {}
    request_expected = finalization.get("request", {})
    for key, expected in request_expected.items():
        if key == "name_prefix":
            continue
        judge.check(request.get(key) == expected, f"receipt.request.{key}", "validity", f"expected {expected!r}")
    prefix = request_expected.get("name_prefix")
    name = request.get("name")
    name_ok = isinstance(prefix, str) and isinstance(name, str) and re.fullmatch(re.escape(prefix) + r"-[0-9a-f]{12}", name) is not None
    judge.check(name_ok, "receipt.request.name", "validity", "fresh registered prefix plus 48-bit nonce")
    exact_request_keys = (set(request_expected) - {"name_prefix"}) | {"name"}
    judge.check(set(request) == exact_request_keys, "receipt.request.keys", "validity", "request receipt has exactly the frozen key set")
    judge.check(receipt.get("transport") == finalization.get("receipt_transport"),
                "receipt.transport", "validity", "exact authenticated HTTP transport receipt")

    pod = receipt.get("pod") if isinstance(receipt.get("pod"), dict) else {}
    pod_id = pod.get("id")
    judge.check(isinstance(pod_id, str) and POD_ID_RE.fullmatch(pod_id) is not None, "receipt.pod.id", "validity", "one concrete pod ID")
    judge.check(pod.get("name") == name, "receipt.pod.name", "validity", "request/pod name agreement")
    judge.check(pod.get("status") == "RUNNING", "receipt.pod.status", "validity", "controller observed allocated pod running")
    judge.check(pod.get("creation_response_ambiguous") is False, "receipt.pod.unambiguous", "validity", "one unambiguous create result")
    judge.check(pod.get("cloud") == "SECURE", "receipt.pod.cloud", "validity", "Secure placement")
    judge.check(pod.get("image") == placement.get("image"), "receipt.pod.image", "validity", "exact image")
    gpu = pod.get("gpu") if isinstance(pod.get("gpu"), dict) else {}
    judge.check(gpu.get("id") == EXPECTED_GPU and gpu.get("count") == 1, "receipt.pod.gpu", "validity", "one exact RTX 5090")
    judge.check(isinstance(gpu.get("memory"), int) and gpu.get("memory", 0) >= placement.get("min_ram_gb", 0), "receipt.pod.ram", "validity", "minimum RAM")
    judge.check(isinstance(gpu.get("vcpuCount"), int) and gpu.get("vcpuCount", 0) >= placement.get("min_vcpu", 0), "receipt.pod.vcpu", "validity", "minimum vCPU")
    cost = pod.get("cost")
    max_price = placement.get("max_price_usd_per_hour")
    price_ok = (
        isinstance(cost, (int, float)) and not isinstance(cost, bool) and math.isfinite(cost)
        and isinstance(max_price, (int, float)) and 0 < cost <= max_price
    )
    judge.check(price_ok, "receipt.pod.price", "validity", f"finite positive hourly price <= {max_price}")

    status = receipt.get("remote_status") if isinstance(receipt.get("remote_status"), dict) else {}
    expected_status_keys = {
        "archive", "archive_ready", "chunks", "command_sha256", "command_started_unix",
        "done", "finished_unix", "hardware", "job_id", "returncode", "schema",
        "source_archive_sha256", "source_commit", "source_tree", "stage", "started_unix",
        "timed_out", "worker_error_type",
    }
    judge.check(set(status) == expected_status_keys, "remote_status.keys", "validity", "exact authenticated status key set")
    for key, expected in (("schema", EXPECTED_STATUS_SCHEMA), ("stage", "complete"), ("done", True),
                          ("archive_ready", True), ("returncode", 0), ("timed_out", False),
                          ("worker_error_type", None)):
        category = "completion" if key in {"stage", "done", "archive_ready", "returncode", "timed_out", "worker_error_type"} else "validity"
        judge.check(status.get(key) == expected, f"remote_status.{key}", category, f"expected {expected!r}")
    judge.check(status.get("job_id") == name, "remote_status.job_id", "validity", "pod/job identity agreement")
    for remote_key, source_key in (("source_commit", "commit"), ("source_tree", "tree"),
                                   ("source_archive_sha256", "archive_sha256")):
        judge.check(status.get(remote_key) == source.get(source_key), f"remote_status.{remote_key}", "validity", "remote/source identity agreement")
    judge.check(status.get("command_sha256") == receipt.get("command_sha256"), "remote_status.command", "validity", "remote command binding")
    hardware = status.get("hardware") if isinstance(status.get("hardware"), dict) else {}
    hardware_gpus = hardware.get("gpus")
    one_gpu = isinstance(hardware_gpus, list) and len(hardware_gpus) == 1 and isinstance(hardware_gpus[0], dict) and hardware_gpus[0].get("name") == EXPECTED_GPU
    judge.check(one_gpu, "remote_status.hardware", "validity", "remote status observes exactly one RTX 5090")
    judge.check(hardware.get("pod_id") == pod_id, "remote_status.pod_id", "validity", "remote/pod ID agreement")

    cleanup = receipt.get("cleanup") if isinstance(receipt.get("cleanup"), dict) else {}
    cleanup_ok = (
        cleanup.get("id") == pod_id and cleanup.get("delete_requested") is True
        and cleanup.get("absence_verified") is True
    )
    judge.check(cleanup_ok, "receipt.cleanup", "completion", "exact pod deleted and exact-ID absence verified")
    judge.check(parse_utc(receipt.get("started_at")) is not None and parse_utc(receipt.get("finished_at")) is not None,
                "receipt.timestamps", "validity", "controller timestamps parse")


def check_analysis(analysis: dict[str, Any], protocol_sha: str, run_id: str, judge: Judge) -> str | None:
    expected = {
        "schema": EXPECTED_ANALYSIS_SCHEMA,
        "protocol_id": PROTOCOL_ID,
        "protocol_version": PROTOCOL_VERSION,
        "protocol_sha256": protocol_sha,
        "session": run_id,
        "terminal": False,
        "classification_status": "provisional_mechanical",
        "terminal_adjudicator": "finalize_gpu_geometry_ab.py",
        "correctness_gate": "passed",
        "source_identity_gate": "passed",
        "numeric_isolation_gate": "passed",
        "profiled_timings_in_decision": False,
        "hardware_counters": "not collected; NCU is outside this protocol",
    }
    for key, wanted in expected.items():
        judge.check(analysis.get(key) == wanted, f"analysis.{key}", "validity", f"expected {wanted!r}")
    provisional = analysis.get("timing_classification_provisional")
    judge.check(provisional in {"geometry_supported", "geometry_not_supported"}, "analysis.provisional", "validity", "registered provisional vocabulary")
    gates = analysis.get("decision_gates")
    gate_ok = isinstance(gates, list) and len(gates) == 10
    judge.check(gate_ok, "analysis.gates.count", "validity", "exact ten-test family")
    if gate_ok:
        identities = [(item.get("workload"), item.get("metric"), item.get("kind")) for item in gates if isinstance(item, dict)]
        expected_ids = []
        for role, tag, _cell, _degree in WORKLOADS:
            expected_ids.append((tag, "device_ms", "primary_improvement" if role == "primary" else "nonregression"))
            expected_ids.append((tag, "complete_ms", "nonregression"))
        judge.check(sorted(identities) == sorted(expected_ids), "analysis.gates.identity", "validity", "each frozen gate appears exactly once")
        booleans = [item.get("passed") for item in gates if isinstance(item, dict)]
        judge.check(len(booleans) == 10 and all(type(value) is bool for value in booleans), "analysis.gates.booleans", "validity", "all gate decisions are Boolean")
        derived = "geometry_supported" if len(booleans) == 10 and all(booleans) else "geometry_not_supported"
        judge.check(provisional == derived, "analysis.provisional_consistency", "validity", "classification equals conjunction of ten gates")
    multiplicity = analysis.get("multiplicity") if isinstance(analysis.get("multiplicity"), dict) else {}
    lower_tail = multiplicity.get("one_sided_lower_tail")
    lower_tail = lower_tail if isinstance(lower_tail, dict) else {}
    judge.check(multiplicity.get("family_tests") == 10 and multiplicity.get("correction") == "Bonferroni" and
                lower_tail.get("numerator") == 1 and lower_tail.get("denominator") == 200,
                "analysis.multiplicity", "validity", "exact rational 1/200 ten-test family")
    mechanism = analysis.get("mechanism_gate") if isinstance(analysis.get("mechanism_gate"), dict) else {}
    mechanism_ok = (
        mechanism.get("status") == "passed"
        and mechanism.get("kernel_launches_per_arm") == EXPECTED_KERNEL_LAUNCHES
        and mechanism.get("update_launches_per_arm") == EXPECTED_UPDATE_LAUNCHES
        and mechanism.get("update_sequence_verified") is True
        and mechanism.get("non_update_geometry_unchanged") is True
        and mechanism.get("changed_update_launches", 0) > 0
        and mechanism.get("resources") == EXPECTED_RESOURCES
    )
    judge.check(mechanism_ok, "analysis.mechanism", "validity", "exact update sequence, launch counts, unchanged non-update geometry, and resources")
    return provisional if isinstance(provisional, str) else None


def check_rows_export(rows: list[dict[str, Any]], export: dict[str, Any], run_id: str,
                      protocol_sha: str, judge: Judge) -> None:
    judge.check(len(rows) == 70, "rows.count", "validity", f"expected 70, observed {len(rows)}")
    judge.check(export.get("schema") == EXPECTED_EXPORT_SCHEMA, "export.schema", "validity", "exact experiment.export/v1")
    proto = export.get("protocol") if isinstance(export.get("protocol"), dict) else {}
    judge.check(proto.get("sha256") == protocol_sha and proto.get("protocol_id") == PROTOCOL_ID and
                proto.get("version") == PROTOCOL_VERSION and
                proto.get("path") == "../../protocol-http-rtx5090-geometry-v10.json",
                "export.protocol", "validity", "exact frozen protocol binding")
    producer = export.get("producer") if isinstance(export.get("producer"), dict) else {}
    judge.check(producer.get("session") == run_id and producer.get("runtime") == "runpod-http-batch",
                "export.session", "validity", "session/runtime binding")
    source = export.get("source") if isinstance(export.get("source"), dict) else {}
    judge.check(source == {"repo": "cryptanalysis", "commit": "59b6d7e17100d4d16db5d25c2762a5d5cf45ef4f", "dirty": False},
                "export.source", "validity", "exact candidate source identity")
    notes = export.get("notes") if isinstance(export.get("notes"), list) else []
    tier_note = "tierB denotes the frozen per-process numeric PSI/cgroup/steal/temperature/no-foreign-process gates; it is not a claim about exclusive physical-host or L2-cache topology."
    judge.check(any(isinstance(note, dict) and note.get("text") == tier_note for note in notes),
                "export.tierb_scope", "validity", "tierB is explicitly numeric and not an L2/exclusive-host claim")
    export_runs = export.get("runs")
    judge.check(export_runs == rows, "export.rows", "validity", "export runs are byte-semantic rows.jsonl sequence")
    flow = export.get("flow") if isinstance(export.get("flow"), dict) else {}
    expected_flow = {"planned": 70, "attempted": 70, "completed": 70, "not_completed": 0,
                     "interrupted": 0, "resumed": 0, "excluded": []}
    judge.check(flow == expected_flow, "export.flow", "validity", "all 70 rows completed once")
    seen: set[tuple[Any, ...]] = set()
    expected_cells = {
        (arm, tag, 0 if phase == "warmup" else round_index - 1, phase == "warmup"):
        f"{run_id}-{phase}-r{round_index:02d}-{tag}-{arm}"
        for phase, round_index in [("warmup", 0), *[("measure", index) for index in range(1, 7)]]
        for _role, tag, _cell, _degree in WORKLOADS
        for arm in ARMS
    }
    row_ok = True
    for row in rows:
        key = (row.get("arm"), row.get("instance_id"), row.get("replicate"), row.get("warmup"))
        if key in seen:
            row_ok = False
        seen.add(key)
        measurements = row.get("measurements") if isinstance(row.get("measurements"), dict) else {}
        isolation = row.get("isolation") if isinstance(row.get("isolation"), dict) else {}
        exclusion = row.get("exclusion") if isinstance(row.get("exclusion"), dict) else {}
        if not (
            key in expected_cells and row.get("run_id") == expected_cells[key]
            and
            row.get("arm") in ARMS and row.get("instance_id") in {item[1] for item in WORKLOADS}
            and row.get("status") == "succeeded" and row.get("outcome_class") == "completed"
            and row.get("attempts") == 1 and row.get("resumed") == 0
            and isolation == {"tier": "tierB", "contended": False, "blockers": []}
            and exclusion == {"excluded": False, "rule": None}
            and measurements.get("wall_valid") is (not row.get("warmup"))
        ):
            row_ok = False
    judge.check(row_ok and seen == set(expected_cells), "rows.semantic", "validity", "exact 70 run identities; unique successful one-attempt tierB rows with correct warmup charging")


def inventory_from_directory(root: Path, prefix: str = "") -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            name = (PurePosixPath(prefix) / path.relative_to(root).as_posix()).as_posix()
            records[name] = {"path": name, "sha256": sha256_file(path), "bytes": path.stat().st_size}
    return records


def check_archive_bindings(
    archive_path: Path,
    evidence: ArchiveEvidence,
    receipt: dict[str, Any],
    session: Path,
    remote: Path,
    session_rel: str,
    judge: Judge,
) -> None:
    archive_sha = sha256_file(archive_path)
    archive_bytes = archive_path.stat().st_size
    result = receipt.get("result") if isinstance(receipt.get("result"), dict) else {}
    status = receipt.get("remote_status") if isinstance(receipt.get("remote_status"), dict) else {}
    status_archive = status.get("archive") if isinstance(status.get("archive"), dict) else {}
    judge.check(set(result) == {"archive", "archive_sha256", "archive_bytes", "metadata", "files"},
                "archive.result_keys", "validity", "exact receipt result key set")
    judge.check(result.get("archive_sha256") == archive_sha and status_archive.get("sha256") == archive_sha,
                "archive.outer_sha256", "validity", "receipt/status/local archive SHA agreement")
    judge.check(result.get("archive_bytes") == archive_bytes and status_archive.get("bytes") == archive_bytes,
                "archive.outer_bytes", "validity", "receipt/status/local archive size agreement")
    result_archive_path = result.get("archive")
    result_metadata_path = result.get("metadata")
    judge.check(isinstance(result_archive_path, str) and Path(result_archive_path).resolve() == archive_path.resolve(),
                "archive.receipt_path", "validity", "receipt names this exact archive")
    judge.check(isinstance(result_metadata_path, str) and Path(result_metadata_path).resolve() == remote.resolve(),
                "archive.metadata_path", "validity", "receipt names this exact remote metadata directory")
    judge.check(status_archive.get("manifest_sha256") == sha256_bytes(evidence.manifest_bytes),
                "archive.manifest_sha256", "validity", "remote/internal manifest SHA agreement")
    judge.check(status_archive.get("files") == len(evidence.records), "archive.file_count", "validity", "remote/archive member count agreement")
    judge.check(status_archive.get("uncompressed_bytes") == sum(item["bytes"] for item in evidence.records.values()),
                "archive.uncompressed_bytes", "validity", "remote/archive uncompressed size agreement")

    chunks = status.get("chunks")
    chunks_ok = isinstance(chunks, list) and bool(chunks)
    offset = 0
    if chunks_ok:
        with archive_path.open("rb") as stream:
            for index, item in enumerate(chunks):
                if not isinstance(item, dict) or item.get("index") != index or item.get("offset") != offset or item.get("path") != f"/v1/result/{index:06d}":
                    chunks_ok = False
                    break
                size = item.get("bytes")
                if not isinstance(size, int) or size <= 0:
                    chunks_ok = False
                    break
                block = stream.read(size)
                if len(block) != size or sha256_bytes(block) != item.get("sha256"):
                    chunks_ok = False
                    break
                offset += size
            if stream.read(1):
                chunks_ok = False
    judge.check(chunks_ok and offset == archive_bytes, "archive.chunks", "validity", "contiguous exact chunk hashes cover archive")

    receipt_files = result.get("files")
    actual_without_manifest = {
        name: record for name, record in evidence.records.items()
        if name != ".runpod-batch/files.sha256"
    }
    listed: dict[str, dict[str, Any]] = {}
    listed_duplicates = False
    if isinstance(receipt_files, list):
        for item in receipt_files:
            if isinstance(item, dict) and isinstance(item.get("path"), str):
                if item["path"] in listed:
                    listed_duplicates = True
                if set(item) != {"path", "sha256", "bytes"}:
                    listed_duplicates = True
                listed[item["path"]] = {key: item.get(key) for key in ("path", "sha256", "bytes")}
    judge.check(not listed_duplicates and listed == actual_without_manifest, "archive.receipt_inventory", "validity", "receipt inventory exactly and uniquely covers every non-manifest member")

    session_inventory = inventory_from_directory(session, session_rel) if session.is_dir() else {}
    archived_session = {name: record for name, record in evidence.records.items() if name == session_rel or name.startswith(session_rel + "/")}
    judge.check(session_inventory == archived_session, "archive.extracted_session", "validity", "extracted session exactly equals archived session inventory")
    remote_inventory = inventory_from_directory(remote, ".runpod-batch") if remote.is_dir() else {}
    archived_remote = {name: record for name, record in evidence.records.items() if name.startswith(".runpod-batch/")}
    judge.check(remote_inventory == archived_remote, "archive.extracted_remote", "validity", "extracted remote metadata exactly equals archive")
    judge.check({path.name for path in remote.iterdir() if path.is_file()} == REMOTE_NAMES if remote.is_dir() else False,
                "archive.remote_names", "validity", "exact four remote metadata files")
    judge.check(set(evidence.records) == set(archived_session) | set(archived_remote),
                "archive.no_extras", "validity", "archive contains only declared session and controller metadata")

    try:
        source = json_from_bytes(evidence.payloads[".runpod-batch/source.json"])
        job = json_from_bytes(evidence.payloads[".runpod-batch/job-status.json"])
    except (KeyError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        judge.incomplete("archive.controller_metadata", f"controller metadata is missing/corrupt: {exc}")
        return
    remote_status = receipt.get("remote_status") if isinstance(receipt.get("remote_status"), dict) else {}
    expected_source = {
        "schema": EXPECTED_STATUS_SCHEMA,
        "job_id": remote_status.get("job_id"),
        "source_commit": remote_status.get("source_commit"),
        "source_tree": remote_status.get("source_tree"),
        "source_archive_sha256": remote_status.get("source_archive_sha256"),
        "command_sha256": remote_status.get("command_sha256"),
        "returncode": 0,
        "timed_out": False,
    }
    judge.check(source == expected_source, "archive.source_metadata", "validity", "internal source receipt exactly matches remote status")
    job_ok = isinstance(job, dict) and job.get("job") == remote_status.get("job_id") and job.get("shard") == 0 and job.get("shards") == 1 and job.get("returncode") == 0 and job.get("gpus") == [EXPECTED_GPU]
    judge.check(job_ok, "archive.job_metadata", "validity", "one-shard successful job on one RTX 5090")
    judge.check(bool(evidence.payloads.get(".runpod-batch/log.txt", b"").strip()), "archive.log", "completion", "remote job log is nonempty")


def resolve_template_path(repo: Path, template: str, run_id: str) -> Path:
    return (repo / template.replace("<run_id>", run_id)).resolve()


def git_text(repo: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments], cwd=repo, capture_output=True, text=True,
        timeout=120, check=False,
    )
    if result.returncode:
        raise ValueError(f"git {' '.join(arguments[:2])} failed")
    return result.stdout.strip()


def check_freeze_chain(protocol_path: Path, protocol: dict[str, Any], repo: Path,
                       judge: Judge) -> dict[str, str | None]:
    """Authenticate draft registration -> immediate freeze in local Git history."""
    result: dict[str, str | None] = {"registration_commit": None, "freeze_commit": None}
    try:
        relative = protocol_path.relative_to(repo).as_posix()
        freeze = protocol.get("freeze") if isinstance(protocol.get("freeze"), dict) else {}
        registration = freeze.get("commit")
        if not isinstance(registration, str) or re.fullmatch(r"[0-9a-f]{40}", registration) is None:
            raise ValueError("freeze.commit is not a full registration commit")
        result["registration_commit"] = registration
        draft = json_from_bytes(subprocess.run(
            ["git", "show", f"{registration}:{relative}"], cwd=repo,
            capture_output=True, timeout=120, check=True,
        ).stdout)
        if not isinstance(draft, dict):
            raise ValueError("registered draft is not an object")
        draft_freeze = draft.get("freeze") if isinstance(draft.get("freeze"), dict) else {}
        if draft_freeze.get("status") != "draft" or protocol_hash(draft) != protocol_hash(protocol):
            raise ValueError("registration is not the canonical matching draft")
        registration_paths = git_text(repo, "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", registration).splitlines()
        if registration_paths != [relative]:
            raise ValueError("registration commit is not scoped to the v10 protocol")
        later = git_text(repo, "log", "--format=%H", "--reverse", f"{registration}..HEAD", "--", relative).splitlines()
        if len(later) != 1:
            raise ValueError("protocol must have exactly one post-registration freeze commit")
        frozen_commit = later[0]
        result["freeze_commit"] = frozen_commit
        if git_text(repo, "rev-parse", f"{frozen_commit}^") != registration:
            raise ValueError("freeze commit is not the immediate child of registration")
        freeze_paths = git_text(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", frozen_commit).splitlines()
        if freeze_paths != [relative]:
            raise ValueError("freeze commit is not scoped to the v10 protocol")
        frozen_bytes = subprocess.run(
            ["git", "show", f"{frozen_commit}:{relative}"], cwd=repo,
            capture_output=True, timeout=120, check=True,
        ).stdout
        if frozen_bytes != protocol_path.read_bytes():
            raise ValueError("working protocol bytes differ from the authenticated freeze commit")
        judge.check(True, "protocol.git_chain", "validity", f"registration {registration}; freeze {frozen_commit}")
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        judge.invalid("protocol.git_chain", f"registration/freeze chain is not authentic: {exc}")
    return result


def check_tooling(repo: Path, session: Path, protocol: dict[str, Any], judge: Judge) -> None:
    extensions = protocol.get("extensions") if isinstance(protocol.get("extensions"), dict) else {}
    tooling = extensions.get("tooling_source") if isinstance(extensions.get("tooling_source"), dict) else {}
    files = tooling.get("files") if isinstance(tooling.get("files"), dict) else {}
    local_ok = bool(files)
    for relative, expected in files.items():
        path = repo / relative
        if not isinstance(relative, str) or not isinstance(expected, str) or not path.is_file() or sha256_file(path) != expected:
            local_ok = False
    judge.check(local_ok, "tooling.local_files", "validity", "every frozen transitive tooling file hash matches")
    try:
        commit = tooling.get("commit")
        tree = git_text(repo, "rev-parse", f"{commit}^{{tree}}")
        judge.check(tree == tooling.get("tree"), "tooling.git_tree", "validity", "tooling commit/tree binding")
        process = subprocess.Popen(
            ["git", "archive", "--format=tar", str(commit)], cwd=repo,
            stdout=subprocess.PIPE,
        )
        digest = hashlib.sha256()
        assert process.stdout is not None
        for block in iter(lambda: process.stdout.read(1 << 20), b""):
            digest.update(block)
        archive_ok = process.wait(timeout=120) == 0 and digest.hexdigest() == tooling.get("git_archive_sha256")
        judge.check(archive_ok, "tooling.git_archive", "validity", "tooling commit archive binding")
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        judge.invalid("tooling.git_identity", f"cannot authenticate tooling Git identity: {exc}")

    head_path = session / "metadata" / "tooling-git-head.txt"
    hashes_path = session / "metadata" / "tooling-sha256.txt"
    try:
        judge.check(head_path.read_text(encoding="ascii") == str(tooling.get("commit")) + "\n",
                    "tooling.remote_head", "validity", "remote checkout is exact tooling commit")
        observed: dict[str, str] = {}
        for line in hashes_path.read_text(encoding="utf-8").splitlines():
            digest, separator, raw_path = line.partition("  ")
            if not separator or SHA256_RE.fullmatch(digest) is None:
                raise ValueError("malformed remote tooling hash line")
            matches = [relative for relative in files
                       if raw_path == relative or raw_path.endswith("/" + relative)]
            if len(matches) != 1:
                raise ValueError(f"remote tooling path is not uniquely registered: {raw_path!r}")
            relative = matches[0]
            if relative in observed:
                raise ValueError("duplicate remote tooling hash path")
            observed[relative] = digest
        required = extensions.get("finalization", {}).get("remote_transitive_files", [])
        expected = {relative: files.get(relative) for relative in required}
        judge.check(observed == expected, "tooling.remote_files", "validity", "remote recorded exact complete transitive tooling hash set")
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        judge.invalid("tooling.remote_files", f"remote tooling binding invalid: {exc}")


def check_host(session: Path, receipt: dict[str, Any], run_id: str, judge: Judge) -> None:
    host = load_required_json(session / "host.json", "host", judge)
    if not isinstance(host, dict):
        if host is not None:
            judge.invalid("host.object", "host.json is not an object")
        return
    pod = receipt.get("pod") if isinstance(receipt.get("pod"), dict) else {}
    expected = {
        "schema": "gpu-geometry-host/v1",
        "session_id": run_id,
        "provider": "runpod",
        "requested_cloud": "SECURE",
        "pod_id": pod.get("id"),
    }
    judge.check(all(host.get(key) == value for key, value in expected.items()),
                "host.receipt_binding", "validity", "scientific host is the exact receipt pod/session/cloud")


def check_read_only_recomputation(session: Path, protocol_sha: str,
                                  protocol: dict[str, Any], judge: Judge) -> None:
    analysis_plan = protocol.get("analysis_plan") if isinstance(protocol.get("analysis_plan"), dict) else {}
    script = analysis_plan.get("script") if isinstance(analysis_plan.get("script"), dict) else {}
    path = Path(__file__).resolve().parent / str(script.get("path", ""))
    if not path.is_file() or sha256_file(path) != script.get("sha256"):
        judge.invalid("analysis.recompute_tool", "frozen remote analyzer hash/path mismatch")
        return
    command = [
        sys.executable, str(path), "verify", "--session", str(session),
        "--expected-gpu", EXPECTED_GPU, "--protocol-sha256", protocol_sha,
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=900, check=False)
        judge.check(result.returncode == 0 and '"read_only_recomputation": "passed"' in result.stdout,
                    "analysis.raw_nsys_recomputation", "validity",
                    (result.stdout + result.stderr).strip()[:2000] or "no recomputation output")
    except (OSError, subprocess.SubprocessError) as exc:
        judge.invalid("analysis.raw_nsys_recomputation", f"read-only recomputation failed: {exc}")


def adjudicate(args: argparse.Namespace) -> dict[str, Any]:
    judge = Judge()
    repo = Path(__file__).resolve().parents[3]
    protocol_path = args.protocol.resolve()
    session = args.session.resolve()
    run_id = session.name
    judge.check(RUN_ID_RE.fullmatch(run_id) is not None, "run_id.syntax", "validity", f"run_id={run_id!r}")

    protocol = load_required_json(protocol_path, "protocol", judge)
    if not isinstance(protocol, dict):
        protocol = {}
        judge.invalid("protocol.object", "protocol is not a JSON object")
    calculated_protocol_sha = protocol_hash(protocol)
    supplied_sha = args.protocol_sha256
    freeze = protocol.get("freeze") if isinstance(protocol.get("freeze"), dict) else {}
    judge.check(protocol.get("schema") == "experiment.protocol/v1", "protocol.schema", "validity", "canonical protocol schema")
    judge.check(protocol.get("protocol_id") == PROTOCOL_ID and protocol.get("version") == PROTOCOL_VERSION,
                "protocol.identity", "validity", "exact v10 identity")
    judge.check(freeze.get("status") == "frozen" and freeze.get("protocol_sha256") == calculated_protocol_sha and supplied_sha == calculated_protocol_sha,
                "protocol.freeze", "validity", "frozen canonical hash equals supplied hash")
    judge.check(freeze.get("filed_before_affected_data") is True, "protocol.prospective", "validity", "filed before affected data")
    chain = check_freeze_chain(protocol_path, protocol, repo, judge)

    extensions = protocol.get("extensions") if isinstance(protocol.get("extensions"), dict) else {}
    output_contract = extensions.get("output_contract") if isinstance(extensions.get("output_contract"), dict) else {}
    expected_session = resolve_template_path(repo, output_contract.get("output_root", "__missing__/<run_id>"), run_id)
    expected_receipt = resolve_template_path(repo, output_contract.get("transport_receipt", "__missing__/<run_id>.json"), run_id)
    expected_archive = resolve_template_path(repo, output_contract.get("result_archive", "__missing__/<run_id>.tar.gz"), run_id)
    expected_remote = resolve_template_path(repo, output_contract.get("remote_metadata", "__missing__/<run_id>.remote"), run_id)
    expected_out = resolve_template_path(repo, output_contract.get("terminal_verdict", "__missing__/<run_id>.json"), run_id)
    for label, observed, expected in (
        ("session", session, expected_session), ("receipt", args.receipt.resolve(), expected_receipt),
        ("archive", args.archive.resolve(), expected_archive), ("remote", args.remote_metadata.resolve(), expected_remote),
        ("terminal_verdict", args.out.resolve(), expected_out),
    ):
        judge.check(observed == expected, f"paths.{label}", "validity", f"expected {expected}")
    session_rel = os.path.relpath(session, repo)

    finalization = extensions.get("finalization") if isinstance(extensions.get("finalization"), dict) else {}
    finalizer_spec = finalization.get("script") if isinstance(finalization.get("script"), dict) else {}
    self_sha = sha256_file(Path(__file__).resolve())
    judge.check(finalizer_spec.get("path") == "finalize_gpu_geometry_ab.py" and finalizer_spec.get("sha256") == self_sha,
                "finalizer.sha256", "validity", f"running finalizer SHA-256 {self_sha}")
    orchestrator_spec = finalization.get("orchestrator") if isinstance(finalization.get("orchestrator"), dict) else {}
    orchestrator_path = Path(__file__).resolve().with_name("orchestrate_gpu_geometry_v10.py")
    orchestrator_sha = maybe_sha256_file(orchestrator_path)
    judge.check(orchestrator_spec.get("path") == orchestrator_path.name and orchestrator_spec.get("sha256") == orchestrator_sha,
                "orchestrator.sha256", "validity", f"registered mandatory launcher SHA-256 {orchestrator_sha}")
    tool_spec = finalization.get("canonical_protocol_tool") if isinstance(finalization.get("canonical_protocol_tool"), dict) else {}
    judge.check(tool_spec.get("sha256") == EXPECTED_PROTOCOL_TOOL_SHA256,
                "protocol.canonical_tool_binding", "validity", "protocol pins the expected canonical tool")
    judge.check(Path(tool_spec.get("path", "")).resolve() == args.protocol_tool.resolve(),
                "paths.protocol_tool", "validity", "exact registered canonical tool path")

    required = output_contract.get("required_session_files", [])
    for relative in required if isinstance(required, list) else []:
        path = session / relative
        if path.is_file() and path.stat().st_size > 0:
            judge.check(True, f"session.required.{relative}", "completion", "required artifact present")
        else:
            judge.missing(f"session.required.{relative}", f"missing/empty {relative}")
    if not session.is_dir():
        judge.missing("session.directory", f"session directory missing: {session}")
    if not args.remote_metadata.is_dir():
        judge.missing("remote.directory", f"remote metadata directory missing: {args.remote_metadata}")
    check_tooling(repo, session, protocol, judge)

    receipt_value = load_required_json(args.receipt, "receipt", judge)
    receipt = receipt_value if isinstance(receipt_value, dict) else {}
    if receipt_value is not None and not isinstance(receipt_value, dict):
        judge.invalid("receipt.object", "receipt JSON is not an object")
    check_receipt_core(receipt, protocol, run_id, supplied_sha, session_rel, judge)
    check_host(session, receipt, run_id, judge)
    frozen_at = parse_utc(freeze.get("frozen_at"))
    receipt_started = parse_utc(receipt.get("started_at"))
    judge.check(frozen_at is not None and receipt_started is not None and frozen_at <= receipt_started,
                "protocol.frozen_before_controller", "validity", "authenticated freeze timestamp precedes controller start")
    try:
        freeze_commit_time = parse_utc(git_text(repo, "show", "-s", "--format=%cI", str(chain.get("freeze_commit"))))
    except (OSError, ValueError, subprocess.SubprocessError):
        freeze_commit_time = None
    judge.check(freeze_commit_time is not None and receipt_started is not None and freeze_commit_time <= receipt_started,
                "protocol.freeze_commit_before_controller", "validity", "Git freeze commit predates controller start")

    archive_evidence = inspect_archive(args.archive, judge)
    if archive_evidence is not None:
        check_archive_bindings(args.archive, archive_evidence, receipt, session, args.remote_metadata, session_rel, judge)

    order_path = session / "order.tsv"
    if order_path.is_file():
        validate_order(order_path, judge)
    else:
        judge.missing("order.present", "order.tsv is absent")

    rows = load_rows(session / "rows.jsonl", judge)
    export_value = load_required_json(session / "export.json", "export", judge)
    export = export_value if isinstance(export_value, dict) else {}
    if export_value is not None and not isinstance(export_value, dict):
        judge.invalid("export.object", "export JSON is not an object")
    if rows is not None and export:
        check_rows_export(rows, export, run_id, supplied_sha, judge)

    analysis_value = load_required_json(session / "analysis.json", "analysis", judge)
    analysis = analysis_value if isinstance(analysis_value, dict) else {}
    if analysis_value is not None and not isinstance(analysis_value, dict):
        judge.invalid("analysis.object", "analysis JSON is not an object")
    elif isinstance(analysis_value, dict) and not analysis_value:
        judge.invalid("analysis.content", "analysis object is present but empty")
    provisional = check_analysis(analysis, supplied_sha, run_id, judge) if analysis else None
    if analysis:
        check_read_only_recomputation(session, supplied_sha, protocol, judge)
    gate_value = load_required_json(session / "analysis-gate.json", "analysis_gate", judge)
    if isinstance(gate_value, dict):
        judge.check(gate_value.get("terminal") is False and
                    gate_value.get("classification_status") == "provisional_mechanical" and
                    gate_value.get("timing_classification_provisional") == provisional,
                    "analysis_gate.provisional", "validity", "remote command output is explicitly provisional")
    elif gate_value is not None:
        judge.invalid("analysis_gate.object", "analysis-gate.json is not an object")

    runner = session / "runner-exit.status"
    if runner.is_file():
        try:
            runner_text = runner.read_text(encoding="ascii")
            judge.check(runner_text == "0\n", "session.runner_exit", "completion", "runner exited exactly zero")
        except (OSError, UnicodeError) as exc:
            judge.incomplete("session.runner_exit", f"runner status unreadable: {exc}")
    else:
        judge.missing("session.runner_exit", "runner-exit.status is absent")
    completed = session / "completed-at.txt"
    if completed.is_file():
        try:
            completed_text = completed.read_text(encoding="ascii")
            completed_at = parse_utc(completed_text.strip()) if completed_text.count("\n") == 1 else None
            judge.check(completed_at is not None and UTC_RE.fullmatch(completed_text.strip()) is not None,
                        "session.completed_at", "completion", "single exact UTC completion marker")
            if completed_at is not None and receipt:
                finished_at = parse_utc(receipt.get("finished_at"))
                started_at = parse_utc(receipt.get("started_at"))
                judge.check(started_at is not None and finished_at is not None and started_at <= completed_at <= finished_at,
                            "session.controller_time_order", "validity", "controller start <= scientific completion <= controller finish")
        except (OSError, UnicodeError) as exc:
            judge.incomplete("session.completed_at", f"completion marker unreadable: {exc}")
    else:
        judge.missing("session.completed_at", "completed-at.txt is absent")

    check_canonical(args.protocol_tool.resolve(), protocol_path, session / "export.json", judge)

    verdict = terminal_verdict(judge, provisional)
    record = {
        "schema": "gpu-f4-update-grid-ab-final-verdict/v1",
        "protocol": {
            "path": os.path.relpath(protocol_path, args.out.resolve().parent),
            "protocol_id": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "sha256": supplied_sha,
            "file_sha256": sha256_file(protocol_path) if protocol_path.is_file() else None,
            "registration_commit": chain.get("registration_commit"),
            "freeze_commit": chain.get("freeze_commit"),
        },
        "run_id": run_id,
        "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "terminal": True,
        "verdict": verdict,
        "precedence": ["incomplete_session", "invalid_measurement", "geometry_not_supported", "geometry_supported"],
        "provisional_remote_classification": provisional,
        "evidence": {
            "receipt": {"path": str(args.receipt), "sha256": sha256_file(args.receipt) if args.receipt.is_file() else None},
            "archive": {"path": str(args.archive), "sha256": sha256_file(args.archive) if args.archive.is_file() else None},
            "session": str(session),
            "remote_metadata": str(args.remote_metadata),
            "finalizer_sha256": self_sha,
            "canonical_protocol_tool_sha256": sha256_file(args.protocol_tool) if args.protocol_tool.is_file() else None,
        },
        "checks": [item.__dict__ for item in judge.checks],
        "summary": {
            "completion_failures": sum(item.category == "completion" and item.status != "passed" for item in judge.checks),
            "validity_failures": sum(item.category == "validity" and item.status != "passed" for item in judge.checks),
            "checks": len(judge.checks),
        },
    }
    return record


def write_once(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--protocol-tool", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--remote-metadata", type=Path, required=True)
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if SHA256_RE.fullmatch(args.protocol_sha256) is None:
        parser.error("--protocol-sha256 must be 64 lowercase hexadecimal characters")
    return args


def defensive_incomplete_record(args: argparse.Namespace, exc: Exception) -> dict[str, Any]:
    """Total fallback for arbitrarily malformed but CLI-addressable evidence."""
    return {
        "schema": "gpu-f4-update-grid-ab-final-verdict/v1",
        "protocol": {
            "path": str(args.protocol),
            "protocol_id": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
            "sha256": args.protocol_sha256,
            "file_sha256": maybe_sha256_file(args.protocol),
        },
        "run_id": args.session.name,
        "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "terminal": True,
        "verdict": "incomplete_session",
        "precedence": ["incomplete_session", "invalid_measurement", "geometry_not_supported", "geometry_supported"],
        "provisional_remote_classification": None,
        "evidence": {
            "receipt": {"path": str(args.receipt), "sha256": None},
            "archive": {"path": str(args.archive), "sha256": None},
            "session": str(args.session),
            "remote_metadata": str(args.remote_metadata),
            "finalizer_sha256": maybe_sha256_file(Path(__file__).resolve()),
            "canonical_protocol_tool_sha256": None,
        },
        "checks": [{
            "code": "finalizer.defensive_totality",
            "category": "completion",
            "status": "failed",
            "detail": f"malformed/partial evidence raised {type(exc).__name__}: {str(exc)[:1000]}",
        }],
        "summary": {"completion_failures": 1, "validity_failures": 0, "checks": 1},
    }


def official_output_path(args: argparse.Namespace) -> Path:
    return Path(__file__).resolve().parent / "final-verdicts" / f"{args.session.name}.json"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        record = adjudicate(args)
    except Exception as exc:  # the terminal mapping is total over partial evidence
        record = defensive_incomplete_record(args, exc)
    official_out = official_output_path(args)
    try:
        write_once(official_out, record)
    except (OSError, ValueError, TypeError) as exc:
        print(f"GPU geometry finalizer could not create its write-once terminal record: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"out": str(official_out), "terminal": True, "verdict": record["verdict"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
