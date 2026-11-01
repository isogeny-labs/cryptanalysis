#!/usr/bin/env python3
"""Frozen analysis/exporter for the CPU baseline A/A v5 campaign."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
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
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def write_text_once(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(value)


def verify_protocol(path: Path) -> dict[str, Any]:
    protocol = load_json(path)
    runner.verify_bootstrap_identity(protocol)
    subprocess.run(
        [str(runner.PYTHON), str(TOOL_PATH), "validate", str(path)],
        check=True, timeout=60,
    )
    freeze = protocol["freeze"]
    observed = subprocess.check_output(
        [str(runner.PYTHON), str(TOOL_PATH), "hash", str(path)], text=True,
        timeout=60,
    ).strip()
    if freeze["status"] != "frozen" or observed != freeze["protocol_sha256"]:
        raise ValueError("protocol freeze/hash mismatch")
    script = protocol["analysis_plan"]["script"]
    if script["sha256"] != sha256(Path(__file__).resolve()):
        raise ValueError("analysis script differs from frozen SHA-256")
    ext = protocol["extensions"]["cpu_baseline_aa_v5"]
    if ext["runner_sha256"] != sha256(runner.RUNNER):
        raise ValueError("runner differs from frozen SHA-256")
    runner.verify_identity(protocol)
    return protocol


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
    stdout_path = directory / "stdout.txt"
    stderr_path = directory / "stderr.txt"
    provenance: list[str] = []
    incomplete: list[str] = []
    if not receipt_path.is_file() or not stdout_path.is_file() or not stderr_path.is_file():
        return None, provenance, [f"{relative}: missing outer attempt receipt or stream"]
    try:
        receipt = load_json(receipt_path)
    except (ValueError, json.JSONDecodeError) as error:
        return None, [f"{relative}: malformed outer receipt: {error}"], incomplete
    if receipt.get("schema") != "cpu-baseline-aa-v5-attempt/v1" or receipt.get("record") != expected:
        provenance.append(f"{relative}: outer command record mismatch")
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
    if expected_status is not None and receipt.get("exit_status") != expected_status:
        provenance.append(f"{path}: isolation and outer statuses differ")
    if require_quiet:
        if receipt.get("contended_samples") != 0:
            incomplete.append(f"{path}: contended isolation samples")
        if receipt.get("left_on_reserved") not in ({}, []):
            incomplete.append(f"{path}: threads remained on reserved CPUs")
    return provenance, incomplete


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


def analyze_wall(run_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], dict[str, str]]:
    normalized: list[dict[str, Any]] = []
    provenance_findings: list[str] = []
    incomplete_findings: list[str] = []
    false_directions: list[str] = []
    fingerprints: dict[str, set[str]] = {}
    observed_cells: set[tuple[str, str]] = set()
    schedule_records: dict[str, Any] = {}
    first_host: dict[str, Any] | None = None
    wall_plan = runner.build_plan()["wall"]
    for index, spec in enumerate(session_specs(run_root), 1):
        expected_record = wall_plan[index - 1]
        attempt_name = f"wall-{index:02d}-{spec['id']}"
        status, provenance, incomplete = validate_attempt(
            run_root, attempt_name, expected_record, require_zero=True,
        )
        provenance_findings.extend(provenance)
        incomplete_findings.extend(incomplete)
        iso_provenance, iso_incomplete = validate_isolation(
            expected_record, status, require_quiet=True,
        )
        provenance_findings.extend(iso_provenance)
        incomplete_findings.extend(iso_incomplete)
        compare_path = run_root / f"wall-{spec['panel']}/{spec['language']}/compare/compare.json"
        if not compare_path.is_file():
            incomplete_findings.append(f"{spec['id']}: missing compare.json")
            continue
        compare = load_json(compare_path)
        if first_host is None:
            first_host = compare.get("host", {})
        ids = set(spec["ids"])
        raw = compare.get("raw", {})
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
        for field, expected in identity.items():
            if compare.get(field) != expected:
                provenance_findings.append(
                    f"{spec['id']}: compare {field}={compare.get(field)!r}, expected {expected!r}"
                )
        if not compare.get("valid"):
            provenance_findings.append(f"{spec['id']}: perfindex exactness invalid")
        observed = parse_observed_schedule(spec["stderr"]) if spec["stderr"].is_file() else []
        expected = expected_schedule(spec["ids"])
        digest = canonical_sha256(observed)
        want_digest = RUST_SCHEDULE_SHA256 if spec["language"] == "rust" else C_SCHEDULE_SHA256
        schedule_records[spec["id"]] = {
            "observed_sha256": digest, "expected_sha256": want_digest,
            "rows": len(observed), "passes": observed == expected and digest == want_digest,
        }
        if observed != expected or digest != want_digest:
            provenance_findings.append(f"{spec['id']}: observed schedule mismatch")
        for kernel in sorted(ids):
            if kernel not in kernel_rows or kernel not in raw:
                continue
            observed_cells.add((spec["panel"], kernel))
            verdict = kernel_rows[kernel].get("verdict")
            if verdict in {"faster", "slower"}:
                false_directions.append(f"{spec['panel']}/{kernel}:{verdict}")
            elif verdict != "neutral":
                provenance_findings.append(f"{spec['id']}/{kernel}: invalid verdict {verdict!r}")
            fingerprints.setdefault(kernel, set())
            record = raw[kernel]
            if not isinstance(record, dict) or set(record) < {"A", "B"}:
                incomplete_findings.append(f"{spec['id']}/{kernel}: missing mirrored arms")
                continue
            if len(record["A"]) != 6 or len(record["B"]) != 6:
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
                    normalized.append({
                        "run_id": f"wall-{spec['panel']}-{runner.safe_id(kernel)}-r{replicate:02d}-{arm}",
                        "arm": spec["arms"][arm], "instance_id": kernel,
                        "seed": 20260926, "replicate": replicate, "warmup": False,
                        "status": "succeeded", "wall_seconds": median_ns / 1e9 if isinstance(median_ns, int) else None,
                        "tier": "nonqualified", "verification": "verified" if isinstance(fingerprint, str) else "error",
                        "output_fingerprint": fingerprint, "work_contract": fingerprint,
                        "complete_invocations": 1,
                    })
    bad_fingerprints = [kernel for kernel, values in fingerprints.items() if len(values) != 1]
    provenance_findings.extend(f"{kernel}: fingerprint mismatch across arms/rounds/thread panels" for kernel in bad_fingerprints)
    exact_fingerprints = {
        kernel: next(iter(values)) for kernel, values in fingerprints.items() if len(values) == 1
    }
    gate = {
        "schema": "cpu-baseline-aa-v5-wall-gate/v1",
        "planned_invocations": 1056, "observed_invocations": len(normalized),
        "planned_cells": 88, "observed_cells": len(observed_cells),
        "false_direction_count": len(false_directions),
        "false_directions": false_directions, "schedule": schedule_records,
        "provenance_findings": provenance_findings,
        "incomplete_findings": incomplete_findings,
        "exactness_passes": not provenance_findings,
    }
    if provenance_findings:
        gate["verdict"] = "invalid_exactness_or_provenance"
    elif incomplete_findings or len(normalized) != 1056 or len(observed_cells) != 88:
        gate["verdict"] = "inconclusive_contention_or_incomplete"
    elif false_directions:
        gate["verdict"] = "baseline_aa_false_direction_nonqualified"
    else:
        gate["verdict"] = "baseline_aa_complete_nonqualified"
    return gate, normalized, first_host or {}, exact_fingerprints


def complete_planned_rows(run_root: Path, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Represent every planned execution cell, including a terminal wall stop."""
    by_key = {(row["arm"], row["instance_id"], row["replicate"]): row for row in rows}
    wall_plan = runner.build_plan()["wall"]
    qualification_blockers = [
        "nonqualified local KVM: no provider allocation receipt",
        "no physical-host exclusivity, fixed-frequency, IRQ, SMT, or NUMA attestation",
        "core hardware PMU unavailable; software events only",
    ]
    for index, spec in enumerate(session_specs(run_root), 1):
        record = wall_plan[index - 1]
        attempt_path = run_root / (
            f"orchestration/attempts/wall-{index:02d}-{spec['id']}/receipt.json"
        )
        attempted = attempt_path.is_file()
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
                            "status": "infra_error" if attempted else "cancelled",
                            "wall_seconds": None, "tier": "nonqualified",
                            "verification": "error", "complete_invocations": 0,
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
                if not output.is_file() or output.stat().st_size == 0:
                    phase_findings.append(f"{name}: successful perf-stat attempt lacks CSV output")
        statuses_by_phase[phase] = statuses
        result[phase] = {
            "planned": 88, "attempted": len(statuses),
            "succeeded": sum(code == 0 for code in statuses),
            "failed": sum(code != 0 for code in statuses),
            "missing_attempts": missing_attempts, "diagnostic_findings": phase_findings,
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
    selection = load_json(selection_path) if selection_path.is_file() else {"status": "absent"}
    record_findings: list[str] = []
    record_statuses: list[int] = []
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
        if not command_plan_path.is_file() or json.loads(command_plan_path.read_text()) != expected_record_commands:
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
            if status == 0 and (not output.is_file() or output.stat().st_size == 0):
                record_findings.append(f"{name}: successful perf-record attempt lacks data output")
    else:
        unexpected = sorted((run_root / "orchestration/attempts").glob("perf-record-*/receipt.json"))
        if unexpected:
            record_findings.append("perf-record attempts exist without a complete frozen selection")

    result["perf_record"] = {
        "planned": 8, "attempted": len(record_statuses), "selection": selection,
        "succeeded": sum(code == 0 for code in record_statuses),
        "failed": sum(code != 0 for code in record_statuses),
        "diagnostic_findings": record_findings,
    }
    all_findings.extend(record_findings)
    result["schedule_complete"] = (
        len(statuses_by_phase.get("callgrind", [])) == 88
        and len(statuses_by_phase.get("perf_stat", [])) == 88
        and (expected_record_commands is None or len(record_statuses) == 8)
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
                host: dict[str, Any], gate: dict[str, Any], profiles: dict[str, Any]) -> dict[str, Any]:
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
                    relative_file(run_root, run_root / "analysis/wall-gate.json", "analysis")],
        "unmasked_at": None,
    }
    ignored = {run_root / "export.json"}
    export["files"] = []
    for path in sorted(run_root.rglob("*")):
        if path.is_file() and path not in ignored:
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
        "text": f"The wall gate recorded {gate['observed_invocations']} invocations and {gate['false_direction_count']} false directional verdicts; every wall clock remains nonqualified.",
        "by": "analyze_cpu_baseline_aa_v5.py",
    }]
    export["reviews_dir"] = "reviews"
    export["backend_record"] = {
        "wall_verdict": gate["verdict"],
        "command_plan_sha256": sha256(run_root / "orchestration/command-plan.json"),
        "command_plan_preimage_sha256": runner.build_plan()["digests"]["plan_preimage"],
        "profile_schedule_complete": profiles["schedule_complete"],
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
    gate, rows, host, wall_fingerprints = analyze_wall(run_root)
    gate_path = run_root / "analysis/wall-gate.json"
    if gate_path.exists():
        if load_json(gate_path) != gate:
            raise ValueError("existing wall gate differs from independent recomputation")
    else:
        write_json_once(gate_path, gate)
    wall_complete = gate["verdict"] in {
        "baseline_aa_complete_nonqualified", "baseline_aa_false_direction_nonqualified",
    }
    if options.wall_gate_only:
        return 0 if wall_complete else 1

    if wall_complete:
        complete_path = run_root / "orchestration/complete.json"
        if not complete_path.is_file() or load_json(complete_path).get("status") != "orchestration_complete":
            raise ValueError("final analysis requires the one-shot orchestration completion receipt")
        profiles = profile_inventory(run_root, wall_fingerprints)
    else:
        profiles = profiles_not_reached("wall gate terminated the campaign before diagnostics")
    rows = complete_planned_rows(run_root, rows)
    rows_path = run_root / "rows.jsonl"
    with rows_path.open("x", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    analysis = {
        "schema": "cpu-baseline-aa-v5-analysis/v1",
        "protocol_sha256": protocol["freeze"]["protocol_sha256"],
        "wall": gate, "profiles": profiles,
        "diagnostic_policy": "Callgrind/perf failures do not alter the wall A/A verdict and no profile supports a speedup claim.",
        "verdict": gate["verdict"],
    }
    analysis_path = run_root / "analysis/analysis.json"
    write_json_once(analysis_path, analysis)
    report_path = run_root / "analysis/REPORT.md"
    write_text_once(report_path, (
        "# CPU baseline A/A v5\n\n"
        f"Wall verdict: `{gate['verdict']}`.\n\n"
        f"Retained invocations: {gate['observed_invocations']}/1056; false directional verdicts: {gate['false_direction_count']}.\n\n"
        "All wall clocks are nonqualified local observations. Callgrind and perf are diagnostics only.\n"
    ))
    export = make_export(protocol_path, protocol, run_root, rows_path, analysis_path,
                         report_path, host, gate, profiles)
    findings = tool.schema_errors(export, "experiment.export/v1") or tool.lint_export(
        export, protocol, run_root, True,
    )
    if findings:
        raise ValueError("export validation failed:\n  " + "\n  ".join(findings))
    export_path = run_root / "export.json"
    write_json_once(export_path, export)
    subprocess.run([
        str(runner.PYTHON), str(TOOL_PATH), "check-export", "--protocol",
        str(protocol_path), "--verify-files", str(export_path),
    ], check=True, cwd=run_root, timeout=60)
    return 0 if wall_complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
