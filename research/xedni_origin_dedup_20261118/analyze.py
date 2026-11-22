#!/usr/bin/env python3
"""Frozen analysis for the full-pencil versus deduplicated Xedni search."""

from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
import sys


FIELDS = (
    "scheduled",
    "ok",
    "semantic_matches",
    "reference_relations",
    "dedup_relations",
    "reference_recoveries",
    "dedup_recoveries",
    "reference_modular_candidates",
    "dedup_modular_candidates",
    "dedup_unique_fixed_candidates",
    "dedup_duplicate_fixed_candidates",
    "reference_exact_checks",
    "dedup_exact_checks",
    "dedup_hash_probes",
    "reference_wall_ns",
    "dedup_wall_ns",
)


def _bucket():
    return Counter({field: 0 for field in FIELDS})


def _add(bucket, row):
    bucket["scheduled"] += 1
    if row["status"] != "ok":
        return
    bucket["ok"] += 1
    bucket["semantic_matches"] += int(row.get("semantic_parity", False))
    bucket["reference_relations"] += row["reference_success"]
    bucket["dedup_relations"] += row["dedup_success"]
    bucket["reference_recoveries"] += row["reference_dl_recovered"]
    bucket["dedup_recoveries"] += row["dedup_dl_recovered"]
    reference = row["reference"]
    dedup = row["dedup"]
    for field in ("modular_candidates", "exact_checks", "wall_ns"):
        bucket[f"reference_{field}"] += reference[field]
        bucket[f"dedup_{field}"] += dedup[field]
    bucket["dedup_unique_fixed_candidates"] += dedup["unique_fixed_candidates"]
    bucket["dedup_duplicate_fixed_candidates"] += dedup[
        "duplicate_fixed_candidates"
    ]
    bucket["dedup_hash_probes"] += dedup["hash_probes"]


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: analyze.py ROWS.jsonl SUMMARY.json")
    source, destination = map(Path, sys.argv[1:])
    rows = [json.loads(line) for line in source.read_text().splitlines() if line.strip()]
    status_counts = Counter(row["status"] for row in rows)
    overall = _bucket()
    by_r = defaultdict(_bucket)
    failures = []
    for number, row in enumerate(rows, 1):
        for bucket in (overall, by_r[str(row["r"])]):
            _add(bucket, row)
        if row["status"] != "ok":
            continue
        row_failures = []
        if not row.get("semantic_parity", False):
            row_failures.append("semantic_parity")
        if row["reference"]["candidate_digest"] != row["dedup"][
            "full_candidate_digest"
        ]:
            row_failures.append("full_candidate_digest")
        if row["reference_success"] != row["dedup_success"]:
            row_failures.append("relation_status")
        if row["reference_dl_recovered"] != row["dedup_dl_recovered"]:
            row_failures.append("recovery_status")
        if row_failures:
            failures.append({"row": number, "failures": row_failures})
    exact_checks_reduced = (
        overall["dedup_exact_checks"] < overall["reference_exact_checks"]
    )
    valid_optimization = (
        len(rows) == 1600
        and overall["ok"] == 1600
        and not failures
        and exact_checks_reduced
    )
    summary = {
        "schema_version": 1,
        "expected_rows": 1600,
        "observed_rows": len(rows),
        "complete": len(rows) == 1600,
        "status_counts": dict(sorted(status_counts.items())),
        "invariant_failures": failures,
        "exact_checks_reduced": exact_checks_reduced,
        "valid_stage_optimization": valid_optimization,
        "overall": dict(overall),
        "by_r": {key: dict(value) for key, value in sorted(by_r.items())},
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
