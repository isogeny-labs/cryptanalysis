#!/usr/bin/env python3
"""Frozen paired analysis for the target-origin-pencil Xedni search."""

from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
import sys


COUNTS = (
    "scheduled",
    "ok",
    "baseline_relations",
    "candidate_relations",
    "baseline_recoveries",
    "candidate_recoveries",
    "candidate_only_recoveries",
    "baseline_only_recoveries",
    "both_recoveries",
    "neither_recovery",
    "baseline_origins",
    "candidate_origins",
    "baseline_table_entries",
    "candidate_table_entries",
    "baseline_modular_candidates",
    "candidate_modular_candidates",
    "baseline_unique_fixed_candidates",
    "candidate_unique_fixed_candidates",
    "baseline_duplicate_fixed_candidates",
    "candidate_duplicate_fixed_candidates",
    "baseline_transports",
    "candidate_transports",
    "baseline_exact_checks",
    "candidate_exact_checks",
    "baseline_source_replays",
    "candidate_source_replays",
    "baseline_wall_ns",
    "candidate_wall_ns",
)


def _bucket():
    return Counter({field: 0 for field in COUNTS})


def _add(bucket, row):
    bucket["scheduled"] += 1
    if row["status"] != "ok":
        return
    bucket["ok"] += 1
    baseline_relation = row.get("baseline_success", 0)
    candidate_relation = row.get("candidate_success", 0)
    baseline_recovery = row.get("baseline_dl_recovered", 0)
    candidate_recovery = row.get("candidate_dl_recovered", 0)
    bucket["baseline_relations"] += baseline_relation
    bucket["candidate_relations"] += candidate_relation
    bucket["baseline_recoveries"] += baseline_recovery
    bucket["candidate_recoveries"] += candidate_recovery
    if baseline_recovery and candidate_recovery:
        bucket["both_recoveries"] += 1
    elif candidate_recovery:
        bucket["candidate_only_recoveries"] += 1
    elif baseline_recovery:
        bucket["baseline_only_recoveries"] += 1
    else:
        bucket["neither_recovery"] += 1
    for label in ("baseline", "candidate"):
        arm = row[label]
        bucket[f"{label}_origins"] += arm["origins"]
        bucket[f"{label}_table_entries"] += arm["origin_table_entries"]
        bucket[f"{label}_modular_candidates"] += arm["modular_candidates"]
        bucket[f"{label}_unique_fixed_candidates"] += arm[
            "unique_fixed_candidates"
        ]
        bucket[f"{label}_duplicate_fixed_candidates"] += arm[
            "duplicate_fixed_candidates"
        ]
        bucket[f"{label}_transports"] += arm["transport_count"]
        bucket[f"{label}_exact_checks"] += arm["exact_checks"]
        bucket[f"{label}_source_replays"] += arm["source_replays"]
        bucket[f"{label}_wall_ns"] += arm["wall_ns"]


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: analyze.py ROWS.jsonl SUMMARY.json")
    source, destination = map(Path, sys.argv[1:])
    rows = [json.loads(line) for line in source.read_text().splitlines() if line.strip()]
    expected = 1600
    status_counts = Counter(row["status"] for row in rows)
    overall = _bucket()
    by_r = defaultdict(_bucket)
    by_cell = defaultdict(_bucket)
    invariant_failures = []
    for row_number, row in enumerate(rows, 1):
        key = f"p={row['p']}/family={row['family']}/lift={row['lift']}/r={row['r']}"
        for bucket in (overall, by_r[str(row["r"])], by_cell[key]):
            _add(bucket, row)
        if row["status"] != "ok":
            continue
        failures = []
        if row.get("candidate_success", 0) < row.get("baseline_success", 0):
            failures.append("lost_relation")
        if row.get("candidate_dl_recovered", 0) < row.get("baseline_dl_recovered", 0):
            failures.append("lost_recovery")
        if row["candidate"]["per_origin_candidate_digests"].get("baseline") != row[
            "baseline"
        ]["per_origin_candidate_digests"].get("baseline"):
            failures.append("baseline_candidate_set_changed")
        for label in ("baseline", "candidate"):
            selected = row[label]["selected"]
            if selected is not None and selected["source_residue"] != 0:
                failures.append(f"{label}_source_replay")
        if failures:
            invariant_failures.append({"row": row_number, "failures": failures})

    improvement_observed = (
        overall["candidate_only_recoveries"] > 0
        and overall["baseline_only_recoveries"] == 0
        and not invariant_failures
        and status_counts.get("relation_cert_failed", 0) == 0
        and status_counts.get("origin_pencil_internal_error", 0) == 0
    )
    summary = {
        "schema_version": 1,
        "expected_rows": expected,
        "observed_rows": len(rows),
        "complete": len(rows) == expected,
        "status_counts": dict(sorted(status_counts.items())),
        "invariant_failures": invariant_failures,
        "stage_improvement_observed": improvement_observed,
        "overall": dict(overall),
        "by_r": {key: dict(value) for key, value in sorted(by_r.items())},
        "by_cell": {key: dict(value) for key, value in sorted(by_cell.items())},
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
