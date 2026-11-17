#!/usr/bin/env python3
"""CT176 bounded external cold-process collector, not a DLP solve or PCC verifier.

Default is plan-only. Actual execution requires BOTH --execute and
--admission-approved, an already-verified native binary, and explicit
permission under the existing owner/provider budget gates.
"""
import argparse
import base64
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import socket
import subprocess
import sys
import time

SCHEMA = "ct176-cold-public-process-panel/v1"
CHILD_SCHEMA = "ct175-single-public-packet-cold-route/v1"
FIXTURE_GIT_BLOB = "9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3"
SEED = 20261117
BLOCKS = 8
ARMS = (
    "direct_composite",
    "strongest_retained_lift_chain",
    "strongest_retained_lift_chain",
    "direct_composite",
    "direct_composite",
    "direct_composite",
)
EXPECTED_COUNTS = 48 * BLOCKS * len(ARMS)
SCALARS = (0, 1, 2, 17, 12345, 2771710)
MAX_CAPTURE = 131072


def jwrite(fh, item):
    fh.write(json.dumps(item, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n")
    fh.flush()
    os.fsync(fh.fileno())


def checked_int(value, label, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{label}: expected integer >= {minimum}, not boolean/float")
    return value


def words(value, label):
    if type(value) is not list or len(value) != 19:
        raise ValueError(f"{label}: expected 19-word array")
    for i, word in enumerate(value):
        if checked_int(word, f"{label}[{i}]") > 0xFFFFFFFF:
            raise ValueError(f"{label}[{i}]: exceeds u32")
    return value


def decimal_string(value, label):
    if type(value) is not str or not value or not value.isascii() or not value.isdecimal():
        raise ValueError(f"{label}: expected decimal string")
    if str(int(value)) != value:
        raise ValueError(f"{label}: noncanonical decimal string")
    return value


def counter_object(value, expected, label):
    if type(value) is not dict or set(value) != set(expected) or len(value) != 21:
        raise ValueError(f"{label}: missing/extra counter fields")
    for name, old in expected.items():
        checked_int(old, f"{label}: fixture.{name}")
        if checked_int(value[name], f"{label}.{name}") != old:
            raise ValueError(f"{label}.{name}: does not match frozen fixture")


def fixture_rows(path):
    raw = Path(path).read_bytes()
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + bytes([0]) + raw).hexdigest()
    if blob != FIXTURE_GIT_BLOB:
        raise ValueError(f"fixture Git blob mismatch: expected {FIXTURE_GIT_BLOB}; got {blob}")
    data = json.loads(raw)
    if type(data) is not dict or set(data) != {"scope", "all48"}:
        raise ValueError("frozen fixture top-level schema mismatch")
    rows = data["all48"]
    if type(rows) is not list or len(rows) != 48:
        raise ValueError("frozen fixture requires exactly 48 rows")
    seen = set()
    for i, row in enumerate(rows):
        if type(row) is not dict or set(row) != {
            "from", "to", "sector", "scalar_OUTSIDE_runtime",
            "input", "whole_outputs_equal",
            "direct_composite", "literal_sequential_Jacobian_maps",
            "strongest_retained_lift_chain"
        }:
            raise ValueError(f"row {i}: unexpected field schema")
        a = checked_int(row["from"], "from")
        b = checked_int(row["to"], "to")
        sector = checked_int(row["sector"], "sector")
        scalar = checked_int(row["scalar_OUTSIDE_runtime"], "scalar label")
        if (a, b) not in ((0, 2), (2, 0)) or sector >= 4 or scalar not in SCALARS:
            raise ValueError(f"row {i}: invalid cohort")
        if (a, b, sector, scalar) in seen:
            raise ValueError(f"row {i}: duplicate cohort")
        seen.add((a, b, sector, scalar))
        words(row["input"], f"row {i} input")
        words(row["whole_outputs_equal"], f"row {i} output")
        for arm in ("direct_composite", "literal_sequential_Jacobian_maps",
                    "strongest_retained_lift_chain"):
            counter_object(row[arm], row[arm], f"row {i} {arm}")
    expected = {(a, b, sector, label)
                for a, b in ((0, 2), (2, 0))
                for sector in range(4) for label in SCALARS}
    if seen != expected:
        raise ValueError("frozen fixture missing direction/sector/scalar classes")
    return rows, hashlib.sha256(raw).hexdigest()


def verify_native(record, row, index, arm):
    """Strictly compare actual child output with original public fixture.

    This is a producer-authored validator; it is NOT independent signed PCC.
    """
    if type(record) is not dict or record.get("schema") != CHILD_SCHEMA:
        raise ValueError("wrong CT175 child schema")
    expected_scalars = {
        "packet_index": index, "from": row["from"], "to": row["to"],
        "sector": row["sector"],
        "scalar_label_outside_runtime": row["scalar_OUTSIDE_runtime"],
        "fixture_rows_checked": 48,
        "preflight_native_routes": 0,
        "preflight_native_inverses": 0,
    }
    for k, expected in expected_scalars.items():
        if type(record.get(k)) is not int or record[k] != expected:
            raise ValueError(f"{k}: wrong type or value")
    if record.get("arm") != arm:
        raise ValueError("wrong arm")
    if record.get("rustc_child_process_spawned") is not False:
        raise ValueError("rustc child spawned or provenance field missing")
    if record.get("external_os_loader_wall_included") is not False:
        raise ValueError("child external-wall accounting changed")
    if words(record.get("public_source_packet"), "source") != row["input"]:
        raise ValueError("public source input differs")
    if words(record.get("verified_canonical_target"), "target") != row["whole_outputs_equal"]:
        raise ValueError("public target differs")
    counter_object(record.get("native_calls"), row[arm], "native_calls")
    sample = record.get("native_sample")
    if type(sample) is not dict or sample.get("complete_counter_match") is not True:
        raise ValueError("native sample verification absent")
    decimal_string(sample.get("elapsed_ns_decimal"), "native route wall ns")
    decimal_string(record.get("same_process_setup_ns_decimal"), "native setup ns")
    decimal_string(record.get("in_process_total_ns_decimal"), "native in-process total ns")
    rss = record.get("peak_rss_kib_linux")
    if rss is not None:
        checked_int(rss, "VmHWM kib")
    return True


def sample_order():
    for block in range(BLOCKS):
        roster = list(range(48))
        random.Random(SEED + block).shuffle(roster)
        for index in roster:
            for position, arm in enumerate(ARMS):
                yield block, index, position, arm


def host_metadata():
    affinity = (sorted(os.sched_getaffinity(0))
                if hasattr(os, "sched_getaffinity") else None)
    return {
        "hostname": socket.gethostname(), "machine": platform.machine(),
        "system": platform.system(), "release": platform.release(),
        "python": platform.python_version(), "cpu_affinity": affinity,
    }


def run_sample(binary, index, arm, row, timeout_seconds):
    argv = [str(binary), "--cold-route", str(index), arm]
    start_ns = time.perf_counter_ns()
    try:
        child = subprocess.run(argv, capture_output=True, timeout=timeout_seconds,
                               check=False, shell=False)
        error = None
        exit_code = child.returncode
        stdout, stderr = child.stdout, child.stderr
    except subprocess.TimeoutExpired as exc:
        exit_code = None
        stdout, stderr = exc.stdout or b"", exc.stderr or b""
        error = "timeout"
    except OSError as exc:
        exit_code = None
        stdout, stderr = b"", str(exc).encode("utf-8", "backslashreplace")
        error = "process spawn failed"
    wall_ns = time.perf_counter_ns() - start_ns
    if len(stdout) > MAX_CAPTURE or len(stderr) > MAX_CAPTURE:
        error = "unbounded stdout or stderr (capture limit exceeded)"
    report = {
        "argv": argv, "external_wall_ns_decimal": str(wall_ns),
        "exit_code": exit_code, "stdout": stdout.decode("utf-8", "backslashreplace"),
        "stderr": stderr.decode("utf-8", "backslashreplace"),
        "stdout_base64": base64.b64encode(stdout).decode("ascii"),
        "stderr_base64": base64.b64encode(stderr).decode("ascii"),
        "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
        "peak_rss_kib_linux": None, "verified": False, "error": error
    }
    if error is not None:
        return report
    if exit_code != 0:
        report["error"] = "child nonzero exit"
        return report
    try:
        lines = report["stdout"].strip().splitlines()
        if len(lines) != 1:
            raise ValueError("child must emit exactly one JSON line")
        record = json.loads(lines[0], parse_constant=lambda x: (_ for _ in ()).throw(
            ValueError(f"invalid JSON numeric constant {x}")))
        verify_native(record, row, index, arm)
        report["peak_rss_kib_linux"] = record.get("peak_rss_kib_linux")
        report["verified"] = True
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        report["error"] = f"child evidence refusal: {exc}"
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fixture", required=True, type=Path)
    p.add_argument("--executable", type=Path)
    p.add_argument("--executable-sha256", type=str)
    p.add_argument("--output", type=Path)
    p.add_argument("--timeout-seconds", type=int, default=120)
    p.add_argument("--execute", action="store_true")
    p.add_argument("--admission-approved", action="store_true")
    args = p.parse_args()
    rows, fixture_sha = fixture_rows(args.fixture)
    plan = {
        "schema": SCHEMA, "standing": "[pcc:unverified]",
        "fixture_git_blob": FIXTURE_GIT_BLOB, "fixture_sha256": fixture_sha,
        "blocks": BLOCKS, "seed": SEED, "processes": EXPECTED_COUNTS,
        "arms_in_each_block": list(ARMS), "packets": len(rows),
        "host": host_metadata(),
        "scope": "fresh-process cold transfer-only, NOT complete prime-field ECDLP",
    }
    if not args.execute:
        print(json.dumps({"plan_only": True, **plan}, sort_keys=True))
        return 0
    if not args.admission_approved:
        p.error("native execution requires --admission-approved AND external owner/budget authorization")
    if args.executable is None or args.output is None or args.executable_sha256 is None:
        p.error("execution requires executable, executable-sha256 and output")
    if args.timeout_seconds <= 0:
        p.error("timeout-seconds must be positive")
    binary = args.executable.resolve(strict=True)
    if not binary.is_file() or not os.access(binary, os.X_OK):
        p.error("binary is not an executable file")
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    if digest != args.executable_sha256:
        p.error(f"executable SHA-256 mismatch: observed {digest}")
    plan["executable_path"] = str(binary)
    plan["executable_sha256"] = digest
    plan["timeout_seconds"] = args.timeout_seconds
    # Exclusive creation means an incomplete run cannot be silently overwritten.
    with args.output.open("x", encoding="utf-8") as fh:
        jwrite(fh, {"type": "manifest", **plan,
                     "started_utc": datetime.datetime.now(
                         datetime.timezone.utc).isoformat()})
        completed = 0
        failure = None
        host = plan["host"]
        for block, index, position, arm in sample_order():
            if host_metadata() != host:
                failure = f"host/affinity changed before block {block}, index {index}"
                break
            trial = run_sample(binary, index, arm, rows[index], args.timeout_seconds)
            jwrite(fh, {"type": "sample", "block": block, "packet_index": index,
                        "position": position, "arm": arm, **trial})
            completed += 1
            if not trial["verified"]:
                failure = trial["error"] or "unverified child"
                break
        jwrite(fh, {
            "type": "terminal", "attempted": completed,
            "planned": EXPECTED_COUNTS, "verified_complete": (
                failure is None and completed == EXPECTED_COUNTS),
            "refusal": failure, "ended_utc": datetime.datetime.now(
                datetime.timezone.utc).isoformat(),
        })
    if failure is None and completed != EXPECTED_COUNTS:
        failure = "incomplete process population"
    if failure:
        print(f"CT176 REFUSED: {failure}; raw evidence retained at {args.output}",
              file=sys.stderr)
        return 1
    print(f"CT176 producer-only panel complete: {completed} processes; {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
