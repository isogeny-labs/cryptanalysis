#!/usr/bin/env python3
"""Roster-complete paired analysis for the target-origin-pencil panel."""

from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
import sys


PRIMES = (31, 67, 127, 251)
FAMILIES = ("generic", "j0")
LIFTS = ("balanced", "wide")
R_VALUES = (6, 7, 8, 9)
TRIALS_PER_CELL = 25
EXPECTED_KEYS = frozenset(
    (p, family, lift, r, idx)
    for p in PRIMES
    for family in FAMILIES
    for lift in LIFTS
    for r in R_VALUES
    for idx in range(TRIALS_PER_CELL)
)
ALLOWED_EXCLUSIONS = frozenset(
    {"no_point", "small_order", "identity", "no_integer_solution", "rank_deficient"}
)
VALID_STATUSES = ALLOWED_EXCLUSIONS | {"ok"}

ARM_FIELDS = (
    "origins",
    "origin_table_entries",
    "modular_candidates",
    "unique_fixed_candidates",
    "duplicate_fixed_candidates",
    "transport_count",
    "exact_checks",
    "source_replays",
    "wall_ns",
)
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
) + tuple(f"{label}_{field}" for label in ("baseline", "candidate") for field in ARM_FIELDS)


def _bucket():
    return Counter({field: 0 for field in COUNTS})


def _status(row):
    if not isinstance(row, dict) or not isinstance(row.get("status"), str):
        return "<missing-or-invalid>"
    return row["status"]


def _metric(mapping, field):
    value = mapping.get(field) if isinstance(mapping, dict) else None
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _add(bucket, row):
    bucket["scheduled"] += 1
    if _status(row) != "ok":
        return
    bucket["ok"] += 1
    baseline_relation = _metric(row, "baseline_success")
    candidate_relation = _metric(row, "candidate_success")
    baseline_recovery = _metric(row, "baseline_dl_recovered")
    candidate_recovery = _metric(row, "candidate_dl_recovered")
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
        arm = row.get(label, {})
        for field in ARM_FIELDS:
            bucket[f"{label}_{field}"] += _metric(arm, field)


def _row_key(row):
    if not isinstance(row, dict):
        return None
    p, family, lift, r, idx = (row.get(name) for name in ("p", "family", "lift", "r", "idx"))
    if any(isinstance(value, bool) for value in (p, r, idx)):
        return None
    if not all(isinstance(value, int) for value in (p, r, idx)):
        return None
    if not isinstance(family, str) or not isinstance(lift, str):
        return None
    return p, family, lift, r, idx


def _key_record(key, count=None):
    record = {"p": key[0], "family": key[1], "lift": key[2], "r": key[3], "idx": key[4]}
    if count is not None:
        record["count"] = count
    return record


def _roster(rows, expected_keys):
    keyed = Counter()
    malformed_rows = []
    for number, row in enumerate(rows, 1):
        key = _row_key(row)
        if key is None:
            malformed_rows.append(number)
        else:
            keyed[key] += 1
    present = set(keyed)
    missing = sorted(expected_keys - present)
    unexpected = sorted(present - expected_keys)
    duplicates = sorted((key, count) for key, count in keyed.items() if count != 1)
    complete = (
        len(rows) == len(expected_keys)
        and not malformed_rows
        and not missing
        and not unexpected
        and not duplicates
    )
    return {
        "complete": complete,
        "missing_count": len(missing),
        "missing_keys": [_key_record(key) for key in missing],
        "unexpected_count": len(unexpected),
        "unexpected_keys": [_key_record(key) for key in unexpected],
        "duplicate_count": len(duplicates),
        "duplicate_keys": [_key_record(key, count) for key, count in duplicates],
        "malformed_row_numbers": malformed_rows,
    }


def _bit(mapping, field, failures, label=None, default_missing=False):
    if not isinstance(mapping, dict):
        failures.append(f"{label or 'row'}_not_object")
        return 0
    if field not in mapping and default_missing:
        return 0
    value = mapping.get(field)
    name = f"{label}_{field}" if label else field
    if not isinstance(value, int) or isinstance(value, bool) or value not in (0, 1):
        failures.append(f"invalid_{name}")
        return 0
    return value


def _selected_state(arm, label, failures):
    if not isinstance(arm, dict):
        failures.append(f"{label}_arm_not_object")
        return 0, 0
    if "selected" not in arm:
        failures.append(f"{label}_selected_missing")
        return 0, 0
    selected = arm["selected"]
    if selected is None:
        return 0, 0
    if not isinstance(selected, dict):
        failures.append(f"{label}_selected_not_object")
        return 0, 0
    if selected.get("source_residue") != 0:
        failures.append(f"{label}_source_replay")
    recovered = selected.get("recovered_correctly")
    if not isinstance(recovered, int) or isinstance(recovered, bool) or recovered not in (0, 1):
        failures.append(f"{label}_invalid_recovered_correctly")
        return 1, 0
    return 1, recovered


def _check_ok_row(row):
    failures = []
    baseline_success = _bit(row, "baseline_success", failures)
    candidate_success = _bit(row, "candidate_success", failures)
    baseline_recovery = _bit(row, "baseline_dl_recovered", failures)
    candidate_recovery = _bit(row, "candidate_dl_recovered", failures)
    top_success = _bit(row, "success", failures)
    top_recovery = _bit(row, "dl_recovered", failures, default_missing=True)

    arms = {}
    for label in ("baseline", "candidate"):
        arm = row.get(label)
        arms[label] = arm
        if not isinstance(arm, dict):
            failures.append(f"{label}_arm_not_object")
            continue
        for field in ARM_FIELDS:
            value = arm.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                failures.append(f"invalid_{label}_{field}")

    baseline_selected, baseline_selected_recovery = _selected_state(
        arms["baseline"], "baseline", failures
    )
    candidate_selected, candidate_selected_recovery = _selected_state(
        arms["candidate"], "candidate", failures
    )
    if baseline_success != baseline_selected:
        failures.append("baseline_success_selected_mismatch")
    if candidate_success != candidate_selected:
        failures.append("candidate_success_selected_mismatch")
    if baseline_recovery != baseline_selected_recovery:
        failures.append("baseline_recovery_selected_mismatch")
    if candidate_recovery != candidate_selected_recovery:
        failures.append("candidate_recovery_selected_mismatch")
    if top_success != candidate_success:
        failures.append("top_level_success_mismatch")
    if top_recovery != candidate_recovery:
        failures.append("top_level_recovery_mismatch")
    if candidate_success < baseline_success:
        failures.append("lost_relation")
    if candidate_recovery < baseline_recovery:
        failures.append("lost_recovery")

    for label, selected_flag in (
        ("baseline", baseline_selected),
        ("candidate", candidate_selected),
    ):
        arm = arms[label]
        if not isinstance(arm, dict):
            continue
        modular = _metric(arm, "modular_candidates")
        unique = _metric(arm, "unique_fixed_candidates")
        duplicate = _metric(arm, "duplicate_fixed_candidates")
        if unique + duplicate != modular:
            failures.append(f"{label}_candidate_partition")
        if _metric(arm, "transport_count") != modular:
            failures.append(f"{label}_transport_count")
        if _metric(arm, "exact_checks") > modular:
            failures.append(f"{label}_exact_check_bound")
        if _metric(arm, "source_replays") != selected_flag:
            failures.append(f"{label}_source_replay_count")
    if isinstance(arms["baseline"], dict) and isinstance(arms["candidate"], dict):
        for field in ("origins", "origin_table_entries", "modular_candidates"):
            if _metric(arms["candidate"], field) < _metric(arms["baseline"], field):
                failures.append(f"candidate_lost_baseline_{field}")

    baseline_digests = (
        arms["baseline"].get("per_origin_candidate_digests", {})
        if isinstance(arms["baseline"], dict)
        else {}
    )
    candidate_digests = (
        arms["candidate"].get("per_origin_candidate_digests", {})
        if isinstance(arms["candidate"], dict)
        else {}
    )
    if not isinstance(baseline_digests, dict) or "baseline" not in baseline_digests:
        failures.append("baseline_candidate_digest_missing")
    elif not isinstance(candidate_digests, dict) or "baseline" not in candidate_digests:
        failures.append("candidate_baseline_digest_missing")
    elif candidate_digests["baseline"] != baseline_digests["baseline"]:
        failures.append("baseline_candidate_set_changed")
    baseline_counts = (
        arms["baseline"].get("per_origin_candidates", {})
        if isinstance(arms["baseline"], dict)
        else {}
    )
    candidate_counts = (
        arms["candidate"].get("per_origin_candidates", {})
        if isinstance(arms["candidate"], dict)
        else {}
    )
    if not isinstance(baseline_counts, dict) or "baseline" not in baseline_counts:
        failures.append("baseline_candidate_count_missing")
    elif not isinstance(candidate_counts, dict) or "baseline" not in candidate_counts:
        failures.append("candidate_baseline_count_missing")
    elif candidate_counts["baseline"] != baseline_counts["baseline"]:
        failures.append("baseline_candidate_count_changed")
    return sorted(set(failures))


def analyze_rows(rows, expected_keys=EXPECTED_KEYS):
    expected_keys = frozenset(expected_keys)
    roster = _roster(rows, expected_keys)
    status_counts = Counter(_status(row) for row in rows)
    invalid_status_counts = {
        status: count for status, count in sorted(status_counts.items()) if status not in VALID_STATUSES
    }
    overall = _bucket()
    by_r = defaultdict(_bucket)
    by_cell = defaultdict(_bucket)
    invariant_failures = []
    for row_number, row in enumerate(rows, 1):
        _add(overall, row)
        key = _row_key(row)
        if key is not None:
            p, family, lift, r, _ = key
            _add(by_r[str(r)], row)
            _add(by_cell[f"p={p}/family={family}/lift={lift}/r={r}"], row)
        if _status(row) == "ok":
            failures = _check_ok_row(row)
            if failures:
                record = {"row": row_number, "failures": failures}
                if key is not None:
                    record["key"] = _key_record(key)
                invariant_failures.append(record)

    improvement_observed = (
        roster["complete"]
        and not invalid_status_counts
        and not invariant_failures
        and overall["ok"] > 0
        and overall["candidate_only_recoveries"] > 0
        and overall["baseline_only_recoveries"] == 0
    )
    return {
        "schema_version": 2,
        "expected_rows": len(expected_keys),
        "observed_rows": len(rows),
        "complete": roster["complete"],
        "roster": roster,
        "allowed_exclusion_statuses": sorted(ALLOWED_EXCLUSIONS),
        "status_counts": dict(sorted(status_counts.items())),
        "invalid_status_counts": invalid_status_counts,
        "invariant_failures": invariant_failures,
        "stage_improvement_observed": improvement_observed,
        "overall": dict(overall),
        "by_r": {key: dict(value) for key, value in sorted(by_r.items())},
        "by_cell": {key: dict(value) for key, value in sorted(by_cell.items())},
    }


def _synthetic_arm(selected=None):
    arm = {field: 1 for field in ARM_FIELDS}
    arm["duplicate_fixed_candidates"] = 0
    arm["source_replays"] = int(selected is not None)
    arm["per_origin_candidates"] = {"baseline": 1}
    arm["per_origin_candidate_digests"] = {"baseline": "same"}
    arm["selected"] = selected
    return arm


def _synthetic_ok(key, baseline_recovery=0, candidate_recovery=1):
    selected = lambda recovered: {
        "source_residue": 0,
        "recovered_correctly": int(bool(recovered)),
    }
    baseline_success = int(bool(baseline_recovery))
    candidate_success = int(bool(candidate_recovery))
    row = {
        "p": key[0], "family": key[1], "lift": key[2], "r": key[3], "idx": key[4],
        "status": "ok",
        "success": candidate_success,
        "dl_recovered": candidate_recovery,
        "baseline_success": baseline_success,
        "candidate_success": candidate_success,
        "baseline_dl_recovered": baseline_recovery,
        "candidate_dl_recovered": candidate_recovery,
        "baseline": _synthetic_arm(selected(baseline_recovery) if baseline_success else None),
        "candidate": _synthetic_arm(selected(candidate_recovery) if candidate_success else None),
    }
    return row


def selftest():
    keys = frozenset({(31, "generic", "balanced", 6, 0), (31, "generic", "balanced", 6, 1)})
    good = _synthetic_ok((31, "generic", "balanced", 6, 0))
    exclusion = {"p": 31, "family": "generic", "lift": "balanced", "r": 6, "idx": 1, "status": "small_order"}
    assert analyze_rows([good, exclusion], keys)["stage_improvement_observed"]
    assert not analyze_rows([good], keys)["stage_improvement_observed"]
    assert not analyze_rows([good, good], keys)["stage_improvement_observed"]
    invalid = dict(exclusion, status="group_error")
    assert not analyze_rows([good, invalid], keys)["stage_improvement_observed"]
    lost = _synthetic_ok((31, "generic", "balanced", 6, 0), 1, 0)
    assert not analyze_rows([lost, exclusion], keys)["stage_improvement_observed"]
    return {
        "status": "PASS",
        "tests": ["complete_with_allowed_exclusion", "partial", "duplicate", "invalid_status", "lost_baseline"],
    }


def main():
    if sys.argv[1:] == ["--selftest"]:
        print(json.dumps(selftest(), sort_keys=True))
        return
    if len(sys.argv) != 3:
        raise SystemExit("usage: analyze-v2.py ROWS.jsonl SUMMARY.json\n       analyze-v2.py --selftest")
    source, destination = map(Path, sys.argv[1:])
    rows = [json.loads(line) for line in source.read_text().splitlines() if line.strip()]
    summary = analyze_rows(rows)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
