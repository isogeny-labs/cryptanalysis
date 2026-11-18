#!/usr/bin/env python3
"""Frozen paired analysis for the target-bearing Xedni relation selector."""

from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
import sys


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: analyze.py ROWS.jsonl SUMMARY.json")
    source, destination = map(Path, sys.argv[1:])
    rows = [json.loads(line) for line in source.read_text().splitlines() if line.strip()]
    expected = 1600
    status = Counter(row["status"] for row in rows)
    fields = (
        "scheduled", "ok", "baseline_success", "target_success",
        "baseline_recovered", "target_recovered", "baseline_checks",
        "target_checks", "candidate_only", "baseline_only", "both", "neither",
    )
    by_r = defaultdict(lambda: Counter({field: 0 for field in fields}))
    by_cell = defaultdict(lambda: Counter({field: 0 for field in fields}))
    invariant_failures = []
    for row_number, row in enumerate(rows, 1):
        key = f"p={row['p']}/family={row['family']}/lift={row['lift']}/r={row['r']}"
        for bucket in (by_r[str(row["r"])], by_cell[key]):
            bucket["scheduled"] += 1
            if row["status"] != "ok":
                continue
            bucket["ok"] += 1
            baseline_success = row.get("baseline_success", 0)
            target_success = row.get("target_success", 0)
            baseline_recovered = row.get("baseline_dl_recovered", 0)
            target_recovered = row.get("target_dl_recovered", 0)
            bucket["baseline_success"] += baseline_success
            bucket["target_success"] += target_success
            bucket["baseline_recovered"] += baseline_recovered
            bucket["target_recovered"] += target_recovered
            bucket["baseline_checks"] += row.get("baseline_checks", 0)
            bucket["target_checks"] += row.get("target_checks", 0)
            if baseline_recovered and target_recovered:
                bucket["both"] += 1
            elif target_recovered:
                bucket["candidate_only"] += 1
            elif baseline_recovered:
                bucket["baseline_only"] += 1
            else:
                bucket["neither"] += 1
            if target_success != baseline_success or target_recovered < baseline_recovered:
                invariant_failures.append(row_number)
    summary = {
        "schema_version": 1,
        "expected_rows": expected,
        "observed_rows": len(rows),
        "complete": len(rows) == expected,
        "status_counts": dict(sorted(status.items())),
        "invariant_failures": invariant_failures,
        "by_r": {key: dict(value) for key, value in sorted(by_r.items())},
        "by_cell": {key: dict(value) for key, value in sorted(by_cell.items())},
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
