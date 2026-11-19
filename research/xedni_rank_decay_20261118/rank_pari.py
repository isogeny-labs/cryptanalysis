#!/usr/bin/env python3
"""Portable fail-closed PARI ``ellrank`` JSONL adapter.

Input rows have ``row_id`` (nonempty string), ``r`` (positive integer), and
``ainvs`` (five integral generalized-Weierstrass coefficients). Output order
matches input order. Timing fields are observations; all other serialization
is canonical JSON with sorted keys.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


SCHEMA_VERSION = 1
ADAPTER = "pari-ellrank-interval-v1"
BEGIN = "XEDNI_RANK_BEGIN"
END = "XEDNI_RANK_END"
DEFAULT_PARISIZEMAX = 2_147_483_648


def _canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _input_hash(value) -> str:
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


def _integer(value, name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an integer, not bool")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"[+-]?(0|[1-9][0-9]*)", value):
        return int(value)
    raise ValueError(f"{name} must be an integer or canonical decimal string")


def validate_row(row) -> tuple[str, int, tuple[int, ...]]:
    if not isinstance(row, dict):
        raise ValueError("row must be a JSON object")
    row_id = row.get("row_id")
    if not isinstance(row_id, str) or not row_id:
        raise ValueError("row_id must be a nonempty string")
    r = _integer(row.get("r"), "r")
    if r <= 0:
        raise ValueError("r must be positive")
    values = row.get("ainvs")
    if not isinstance(values, list) or len(values) != 5:
        raise ValueError("ainvs must contain exactly five coefficients")
    ainvs = tuple(_integer(value, f"ainvs[{index}]") for index, value in enumerate(values))
    return row_id, r, ainvs


def make_script(
    ainvs: tuple[int, ...], effort: int, parisizemax: int = DEFAULT_PARISIZEMAX
) -> str:
    coefficients = ",".join(str(value) for value in ainvs)
    return (
        f"default(parisizemax,{parisizemax});\n"
        f"E=ellinit([{coefficients}]);\n"
        f"R=ellrank(E,{effort});\n"
        f'print("{BEGIN}");\n'
        'print("LOWER=",R[1]);\n'
        'print("UPPER=",R[2]);\n'
        'print("SHA2_RANK=",R[3]);\n'
        'print("POINT_COUNT=",#R[4]);\n'
        'print("PARISIZEMAX=",default(parisizemax));\n'
        f'print("{END}");\n'
        "quit();\n"
    )


def parse_transcript(stdout: str) -> dict[str, int]:
    if stdout.count(BEGIN) != 1 or stdout.count(END) != 1:
        raise ValueError(
            f"expected one begin and one end marker, found "
            f"{stdout.count(BEGIN)} and {stdout.count(END)}"
        )
    pattern = re.compile(
        rf"(?m)^{re.escape(BEGIN)}\s*$\n(?P<body>.*?)^(?:{re.escape(END)})\s*$",
        re.DOTALL,
    )
    matches = list(pattern.finditer(stdout))
    if len(matches) != 1:
        raise ValueError(f"expected one complete marker block, found {len(matches)}")
    values: dict[str, int] = {}
    allowed = {"LOWER", "UPPER", "SHA2_RANK", "POINT_COUNT", "PARISIZEMAX"}
    for line in matches[0].group("body").splitlines():
        match = re.fullmatch(r"([A-Z0-9_]+)=([+-]?[0-9]+)", line.strip())
        if not match:
            raise ValueError(f"unparseable marker line: {line!r}")
        key, raw = match.groups()
        if key not in allowed or key in values:
            raise ValueError(f"unexpected or duplicate marker key: {key}")
        values[key] = int(raw)
    if set(values) != allowed:
        raise ValueError(f"marker keys differ: {sorted(values)}")
    lower, upper = values["LOWER"], values["UPPER"]
    if lower < 0 or upper < 0 or lower > upper:
        raise ValueError(f"invalid rank interval [{lower},{upper}]")
    if values["SHA2_RANK"] < 0 or values["POINT_COUNT"] < 0 or values["PARISIZEMAX"] <= 0:
        raise ValueError("negative auxiliary rank output")
    return values


def classify(lower: int, upper: int, r: int) -> tuple[str, str]:
    if upper < r:
        return "CERT_LT", "certified_upper_below_r"
    if lower >= r:
        return "CERT_GE", "certified_lower_at_least_r"
    return "UNKNOWN", "rank_interval_straddles_r"


def _text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value


def probe_tool(executable: str) -> dict:
    resolved = shutil.which(executable)
    if resolved is None:
        return {
            "available": False,
            "executable_requested": executable,
            "executable_resolved": None,
            "version_command": [executable, "--version"],
            "version_returncode": None,
            "version_stdout": "",
            "version_stderr": "",
            "version_timed_out": False,
            "version_timeout_seconds": 15.0,
            "version_wall_ns": 0,
            "image_probe_command": [executable, "--xedni-image-id"],
            "image_probe_returncode": None,
            "image_probe_stdout": "",
            "image_probe_stderr": "",
            "image_probe_timed_out": False,
            "image_probe_wall_ns": 0,
            "image_digest": None,
        }
    command = [resolved, "--version"]
    started = time.perf_counter_ns()
    timed_out = False
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=15, check=False)
        returncode = completed.returncode
        stdout, stderr = completed.stdout, completed.stderr
    except subprocess.TimeoutExpired as error:
        timed_out = True
        returncode = None
        stdout = _text(error.stdout)
        stderr = _text(error.stderr)
    except OSError as error:
        returncode = None
        stdout, stderr = "", f"{type(error).__name__}: {error}"
    version_wall_ns = time.perf_counter_ns() - started
    image_command = [resolved, "--xedni-image-id"]
    image_started = time.perf_counter_ns()
    image_timed_out = False
    try:
        image_completed = subprocess.run(
            image_command,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        image_returncode = image_completed.returncode
        image_stdout, image_stderr = image_completed.stdout, image_completed.stderr
    except subprocess.TimeoutExpired as error:
        image_timed_out = True
        image_returncode = None
        image_stdout = _text(error.stdout)
        image_stderr = _text(error.stderr)
    except OSError as error:
        image_returncode = None
        image_stdout, image_stderr = "", f"{type(error).__name__}: {error}"
    image_candidate = image_stdout.strip()
    image_digest = (
        image_candidate.lower()
        if image_returncode == 0
        and re.fullmatch(r"sha256:[0-9a-fA-F]{64}", image_candidate)
        else None
    )
    return {
        "available": True,
        "executable_requested": executable,
        "executable_resolved": resolved,
        "version_command": command,
        "version_returncode": returncode,
        "version_stdout": stdout,
        "version_stderr": stderr,
        "version_timed_out": timed_out,
        "version_timeout_seconds": 15.0,
        "version_wall_ns": version_wall_ns,
        "image_probe_command": image_command,
        "image_probe_returncode": image_returncode,
        "image_probe_stdout": image_stdout,
        "image_probe_stderr": image_stderr,
        "image_probe_timed_out": image_timed_out,
        "image_probe_wall_ns": time.perf_counter_ns() - image_started,
        "image_digest": image_digest,
    }


def _base(row, tool: dict) -> dict:
    return {
        "adapter": ADAPTER,
        "classification": "UNKNOWN",
        "input_sha256": _input_hash(row),
        "rank_bounds": {"lower": None, "upper": None},
        "reason": "not_run",
        "row_id": row.get("row_id") if isinstance(row, dict) else None,
        "schema_version": SCHEMA_VERSION,
        "tool": tool,
    }


def process_row(
    row, tool: dict, timeout: float, effort: int, parisizemax: int = DEFAULT_PARISIZEMAX
) -> dict:
    output = _base(row, tool)
    try:
        row_id, r, ainvs = validate_row(row)
    except ValueError as error:
        output["reason"] = "invalid_input"
        output["error"] = str(error)
        return output
    output["row_id"] = row_id
    output["r"] = r
    output["ainvs"] = [str(value) for value in ainvs]
    if not tool["available"]:
        output["reason"] = "missing_tool"
        output["error"] = f"executable not found: {tool['executable_requested']}"
        return output

    script = make_script(ainvs, effort, parisizemax)
    command = [tool["executable_resolved"], "-q", "-f"]
    execution = {
        "command": command,
        "returncode": None,
        "script": script,
        "script_sha256": hashlib.sha256(script.encode()).hexdigest(),
        "stderr": "",
        "stdout": "",
        "timed_out": False,
        "timeout_seconds": timeout,
        "wall_ns": 0,
    }
    started = time.perf_counter_ns()
    try:
        completed = subprocess.run(
            command,
            input=script,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        execution["returncode"] = completed.returncode
        execution["stdout"] = completed.stdout
        execution["stderr"] = completed.stderr
    except subprocess.TimeoutExpired as error:
        execution["timed_out"] = True
        execution["stdout"] = _text(error.stdout)
        execution["stderr"] = _text(error.stderr)
        output["reason"] = "timeout"
    except OSError as error:
        execution["stderr"] = f"{type(error).__name__}: {error}"
        output["reason"] = "launch_error"
    execution["wall_ns"] = time.perf_counter_ns() - started
    output["execution"] = execution
    if output["reason"] in {"timeout", "launch_error"}:
        return output
    if execution["returncode"] != 0:
        output["reason"] = "tool_nonzero_exit"
        return output
    try:
        parsed = parse_transcript(execution["stdout"])
    except ValueError as error:
        output["reason"] = "parser_error"
        output["error"] = str(error)
        return output
    lower, upper = parsed["LOWER"], parsed["UPPER"]
    if parsed["PARISIZEMAX"] != parisizemax:
        output["reason"] = "parisizemax_mismatch"
        output["pari"] = {
            "configured_parisizemax": parisizemax,
            "reported_parisizemax": parsed["PARISIZEMAX"],
        }
        return output
    output["classification"], output["reason"] = classify(lower, upper, r)
    output["rank_bounds"] = {"lower": lower, "upper": upper}
    output["pari"] = {
        "points_found": parsed["POINT_COUNT"],
        "sha2_quotient_rank": parsed["SHA2_RANK"],
        "parisizemax": parsed["PARISIZEMAX"],
    }
    return output


def _streams(input_path: str, output_path: str):
    source = sys.stdin if input_path == "-" else Path(input_path).open(encoding="utf-8")
    destination = sys.stdout if output_path == "-" else Path(output_path).open("w", encoding="utf-8")
    return source, destination


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="-", help="JSONL path or - for stdin")
    parser.add_argument("--output", default="-", help="JSONL path or - for stdout")
    parser.add_argument("--gp", default="gp")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--effort", type=int, default=0)
    parser.add_argument("--parisizemax", type=int, default=DEFAULT_PARISIZEMAX)
    args = parser.parse_args(argv)
    if args.timeout <= 0 or args.effort < 0 or args.parisizemax <= 0:
        parser.error("timeout and parisizemax must be positive and effort nonnegative")
    tool = probe_tool(args.gp)
    source, destination = _streams(args.input, args.output)
    close_source, close_destination = source is not sys.stdin, destination is not sys.stdout
    try:
        for line_number, line in enumerate(source, 1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                row = {"row_id": f"invalid-json-line-{line_number}"}
                result = _base(row, tool)
                result["input_sha256"] = hashlib.sha256(line.encode()).hexdigest()
                result["input_line_bytes"] = len(line.encode())
                result["reason"] = "invalid_json"
                result["error"] = str(error)
            else:
                result = process_row(
                    row, tool, args.timeout, args.effort, args.parisizemax
                )
            destination.write(_canonical(result) + "\n")
            destination.flush()
    finally:
        if close_source:
            source.close()
        if close_destination:
            destination.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
