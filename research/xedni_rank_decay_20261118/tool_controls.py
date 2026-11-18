#!/usr/bin/env python3
"""Deterministic synthetic controls for the rank-tool adapters.

The default suite never submits an experimental curve.  It drives both
adapters through a local fake executable so every classification and failure
branch can be checked without trusting PARI or Magma.  ``--gp`` additionally
runs two published known-rank calibration curves through a real PARI binary.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile

import rank_magma
import rank_pari


FAKE_TOOL = r'''#!/usr/bin/env python3
import sys
import time

if "--version" in sys.argv:
    print("GP/PARI CALCULATOR Version 0.0-fake")
    raise SystemExit(0)

source = sys.stdin.read()
if "GetVersion()" in source:
    print("XEDNI_MAGMA_VERSION=2.29-10-fake")
    raise SystemExit(0)

is_pari = "ellrank(" in source
if "9106" in source:
    print("synthetic nonzero", file=sys.stderr)
    raise SystemExit(7)
if "9107" in source:
    time.sleep(2)

if "9101" in source:
    lower, upper = 0, 0
elif "9102" in source:
    lower, upper = 2, 2
elif "9103" in source:
    lower, upper = 0, 2
elif "9105" in source:
    lower, upper = 3, 1
else:
    lower, upper = 0, 0

print("XEDNI_RANK_BEGIN")
print(f"LOWER={lower}")
print(f"UPPER={upper}")
if is_pari:
    print("SHA2_RANK=0")
    print("POINT_COUNT=0")
if "9104" not in source:
    print("XEDNI_RANK_END")
if "9108" in source:
    print("XEDNI_RANK_END")
'''


def install_fake_tool(directory: Path) -> Path:
    """Install the hermetic fake rank executable in a temporary directory."""

    path = directory / "fake-rank-tool"
    path.write_text(FAKE_TOOL, encoding="utf-8")
    path.chmod(0o755)
    return path


def _row(suffix: int, r: int = 1) -> dict:
    return {"row_id": f"synthetic-{suffix}", "r": r, "ainvs": [0, 0, 0, 0, suffix]}


def _matches(actual: dict, expected: dict) -> bool:
    return all(actual.get(key) == value for key, value in expected.items())


def _record(name: str, actual: dict, expected: dict) -> dict:
    return {
        "actual": actual,
        "expected_top_level": expected,
        "name": name,
        "passed": _matches(actual, expected),
    }


def synthetic_controls(fake: Path, timeout: float) -> list[dict]:
    pari_tool = rank_pari.probe_tool(str(fake))
    magma_tool = rank_magma.probe_tool(str(fake))
    records = []
    cases = [
        ("pari_cert_lt", _row(9101), {"classification": "CERT_LT", "reason": "certified_upper_below_r"}),
        ("pari_cert_ge", _row(9102), {"classification": "CERT_GE", "reason": "certified_lower_at_least_r"}),
        ("pari_interval_unknown", _row(9103), {"classification": "UNKNOWN", "reason": "rank_interval_straddles_r"}),
        ("pari_mutated_missing_end", _row(9104), {"classification": "UNKNOWN", "reason": "parser_error"}),
        ("pari_mutated_bad_interval", _row(9105), {"classification": "UNKNOWN", "reason": "parser_error"}),
        ("pari_nonzero", _row(9106), {"classification": "UNKNOWN", "reason": "tool_nonzero_exit"}),
        ("pari_timeout", _row(9107), {"classification": "UNKNOWN", "reason": "timeout"}),
        ("pari_duplicate_end", _row(9108), {"classification": "UNKNOWN", "reason": "parser_error"}),
    ]
    for name, row, expected in cases:
        row_timeout = timeout if row["ainvs"][-1] == 9107 else 2.0
        records.append(_record(name, rank_pari.process_row(row, pari_tool, row_timeout, 0), expected))

    invalid = {"row_id": "synthetic-malformed", "r": 1, "ainvs": [0, 0, 0, 0]}
    records.append(
        _record(
            "pari_malformed_input",
            rank_pari.process_row(invalid, pari_tool, 2.0, 0),
            {"classification": "UNKNOWN", "reason": "invalid_input"},
        )
    )
    missing = rank_pari.probe_tool(str(fake.parent / "does-not-exist"))
    records.append(
        _record(
            "pari_missing_tool",
            rank_pari.process_row(_row(9101), missing, 2.0, 0),
            {"classification": "UNKNOWN", "reason": "missing_tool"},
        )
    )

    magma_cases = [
        ("magma_cert_lt", _row(9101), {"classification": "CERT_LT", "reason": "certified_upper_below_r"}),
        ("magma_cert_ge", _row(9102), {"classification": "CERT_GE", "reason": "certified_lower_at_least_r"}),
        ("magma_interval_unknown", _row(9103), {"classification": "UNKNOWN", "reason": "rank_interval_straddles_r"}),
        ("magma_mutated_missing_end", _row(9104), {"classification": "UNKNOWN", "reason": "parser_error"}),
        ("magma_timeout", _row(9107), {"classification": "UNKNOWN", "reason": "timeout"}),
    ]
    for name, row, expected in magma_cases:
        row_timeout = timeout if row["ainvs"][-1] == 9107 else 2.0
        records.append(_record(name, rank_magma.process_row(row, magma_tool, row_timeout), expected))

    missing_magma = rank_magma.probe_tool(str(fake.parent / "no-magma"))
    records.append(
        _record(
            "magma_missing_tool",
            rank_magma.process_row(_row(9101), missing_magma, 2.0),
            {"classification": "UNKNOWN", "reason": "missing_tool"},
        )
    )
    return records


def real_pari_controls(executable: str, timeout: float) -> list[dict]:
    """Run known-rank calibration curves; these are controls, not study rows."""

    tool = rank_pari.probe_tool(executable)
    curves = [
        (
            "pari_known_11a1_rank_0",
            {"row_id": "control-lmfdb-11a1-r0", "r": 1, "ainvs": [0, -1, 1, -10, -20]},
            {"classification": "CERT_LT", "reason": "certified_upper_below_r"},
        ),
        (
            "pari_known_37a1_rank_1",
            {"row_id": "control-lmfdb-37a1-r1", "r": 1, "ainvs": [0, 0, 1, -1, 0]},
            {"classification": "CERT_GE", "reason": "certified_lower_at_least_r"},
        ),
    ]
    return [
        _record(name, rank_pari.process_row(row, tool, timeout, 0), expected)
        for name, row, expected in curves
    ]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gp", help="also run known-rank controls with this PARI executable")
    parser.add_argument("--timeout", type=float, default=0.05, help="synthetic timeout-control limit")
    parser.add_argument("--real-timeout", type=float, default=60.0)
    args = parser.parse_args(argv)
    if args.timeout <= 0 or args.real_timeout <= 0:
        parser.error("timeouts must be positive")

    with tempfile.TemporaryDirectory(prefix="xedni-rank-controls-") as temporary:
        records = synthetic_controls(install_fake_tool(Path(temporary)), args.timeout)
    if args.gp:
        records.extend(real_pari_controls(args.gp, args.real_timeout))
    report = {
        "control_suite": "xedni-rank-tool-controls-v1",
        "failed": sum(not item["passed"] for item in records),
        "passed": sum(item["passed"] for item in records),
        "records": records,
        "schema_version": 1,
    }
    print(json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
