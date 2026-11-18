#!/usr/bin/env python3
"""Frozen descriptive analysis for the r=6..9 plane-cubic feasibility panel."""

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
    by_r = defaultdict(lambda: Counter(scheduled=0, ok=0, fp_rel=0, success=0, recovered=0))
    by_cell = defaultdict(lambda: Counter(scheduled=0, ok=0, fp_rel=0, success=0, recovered=0))
    for row in rows:
        key = f"p={row['p']}/family={row['family']}/lift={row['lift']}/r={row['r']}"
        for bucket in (by_r[str(row["r"])], by_cell[key]):
            bucket["scheduled"] += 1
            if row["status"] == "ok":
                bucket["ok"] += 1
                bucket["fp_rel"] += row.get("fp_rel", 0)
                bucket["success"] += row.get("success", 0)
                bucket["recovered"] += row.get("dl_recovered", 0)
    summary = {
        "schema_version": 1,
        "expected_rows": expected,
        "observed_rows": len(rows),
        "complete": len(rows) == expected,
        "status_counts": dict(sorted(status.items())),
        "by_r": {key: dict(value) for key, value in sorted(by_r.items())},
        "by_cell": {key: dict(value) for key, value in sorted(by_cell.items())},
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
