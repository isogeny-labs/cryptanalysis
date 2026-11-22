#!/usr/bin/env python3
"""Portable fail-closed Magma ``RankBounds`` JSONL adapter."""

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

import rank_pari


SCHEMA_VERSION = 1
ADAPTER = "magma-rankbounds-2descent-v1"
BEGIN = rank_pari.BEGIN
END = rank_pari.END


def make_script(ainvs: tuple[int, ...], effort: int = 1) -> str:
    coefficients = ",".join(str(value) for value in ainvs)
    return (
        "SetSeed(1);\n"
        "Q := Rationals();\n"
        f"E := EllipticCurve([Q | {coefficients}]);\n"
        f'print "{BEGIN}";\n'
        f"lower, upper := RankBounds(E : Effort := {effort});\n"
        'printf "LOWER=%o\\n", lower;\n'
        'printf "UPPER=%o\\n", upper;\n'
        f'print "{END}";\n'
        "quit;\n"
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
    for line in matches[0].group("body").splitlines():
        match = re.fullmatch(r"(LOWER|UPPER)=([+-]?[0-9]+)", line.strip())
        if not match:
            raise ValueError(f"unparseable marker line: {line!r}")
        key, raw = match.groups()
        if key in values:
            raise ValueError(f"duplicate marker key: {key}")
        values[key] = int(raw)
    if set(values) != {"LOWER", "UPPER"}:
        raise ValueError(f"marker keys differ: {sorted(values)}")
    if values["LOWER"] < 0 or values["UPPER"] < 0 or values["LOWER"] > values["UPPER"]:
        raise ValueError(f"invalid rank interval [{values['LOWER']},{values['UPPER']}]")
    return values


def probe_tool(executable: str) -> dict:
    resolved = shutil.which(executable)
    version_script = (
        "major, minor, patch := GetVersion();\n"
        'printf "XEDNI_MAGMA_VERSION=%o.%o-%o\\n", major, minor, patch;\n'
        "quit;\n"
    )
    if resolved is None:
        return {
            "available": False,
            "executable_requested": executable,
            "executable_resolved": None,
            "version_command": [executable, "-b"],
            "version_returncode": None,
            "version_script": version_script,
            "version_stdout": "",
            "version_stderr": "",
            "version_timed_out": False,
            "version_timeout_seconds": 15.0,
            "version_wall_ns": 0,
        }
    command = [resolved, "-b"]
    started = time.perf_counter_ns()
    timed_out = False
    try:
        completed = subprocess.run(
            command,
            input=version_script,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
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
    return {
        "available": True,
        "executable_requested": executable,
        "executable_resolved": resolved,
        "version_command": command,
        "version_returncode": returncode,
        "version_script": version_script,
        "version_stdout": stdout,
        "version_stderr": stderr,
        "version_timed_out": timed_out,
        "version_timeout_seconds": 15.0,
        "version_wall_ns": time.perf_counter_ns() - started,
    }


def _base(row, tool: dict) -> dict:
    return {
        "adapter": ADAPTER,
        "classification": "UNKNOWN",
        "input_sha256": hashlib.sha256(rank_pari._canonical(row).encode()).hexdigest(),
        "rank_bounds": {"lower": None, "upper": None},
        "reason": "not_run",
        "row_id": row.get("row_id") if isinstance(row, dict) else None,
        "schema_version": SCHEMA_VERSION,
        "tool": tool,
    }


def _text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value


def process_row(row, tool: dict, timeout: float, effort: int = 1) -> dict:
    output = _base(row, tool)
    try:
        row_id, r, ainvs = rank_pari.validate_row(row)
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

    script = make_script(ainvs, effort)
    command = [tool["executable_resolved"], "-b"]
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
    output["classification"], output["reason"] = rank_pari.classify(lower, upper, r)
    output["rank_bounds"] = {"lower": lower, "upper": upper}
    return output


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="-", help="JSONL path or - for stdin")
    parser.add_argument("--output", default="-", help="JSONL path or - for stdout")
    parser.add_argument("--magma", default="magma")
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--effort", type=int, default=1)
    args = parser.parse_args(argv)
    if args.timeout <= 0 or args.effort < 1:
        parser.error("timeout must be positive and effort at least one")
    tool = probe_tool(args.magma)
    source, destination = rank_pari._streams(args.input, args.output)
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
                result = process_row(row, tool, args.timeout, args.effort)
            destination.write(rank_pari._canonical(result) + "\n")
            destination.flush()
    finally:
        if close_source:
            source.close()
        if close_destination:
            destination.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
