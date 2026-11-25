#!/usr/bin/env python3
"""Roster-complete analysis of full-pencil versus deduplicated search."""

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

COMMON_METRICS = (
    "origins",
    "origin_table_entries",
    "modular_candidates",
    "unique_fixed_candidates",
    "duplicate_fixed_candidates",
    "transport_count",
    "exact_checks",
    "source_replays",
    "construction_ns",
    "exact_check_ns",
    "wall_ns",
)
DEDUP_ONLY_METRICS = ("hash_probes", "peak_retained_entries", "dedup_ns")
FIELDS = (
    "scheduled",
    "ok",
    "semantic_matches",
    "reference_relations",
    "dedup_relations",
    "reference_recoveries",
    "dedup_recoveries",
    "strict_exact_check_reductions",
    "equal_exact_check_rows",
    "exact_check_regressions",
) + tuple(f"{label}_{field}" for label in ("reference", "dedup") for field in COMMON_METRICS) + (
    "dedup_hash_probes",
    "dedup_dedup_ns",
    "dedup_peak_retained_entries_max",
)


def _bucket():
    return Counter({field: 0 for field in FIELDS})


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
    bucket["semantic_matches"] += int(row.get("semantic_parity") is True)
    bucket["reference_relations"] += _metric(row, "reference_success")
    bucket["dedup_relations"] += _metric(row, "dedup_success")
    bucket["reference_recoveries"] += _metric(row, "reference_dl_recovered")
    bucket["dedup_recoveries"] += _metric(row, "dedup_dl_recovered")
    reference = row.get("reference", {})
    dedup = row.get("dedup", {})
    for label, arm in (("reference", reference), ("dedup", dedup)):
        for field in COMMON_METRICS:
            bucket[f"{label}_{field}"] += _metric(arm, field)
    bucket["dedup_hash_probes"] += _metric(dedup, "hash_probes")
    bucket["dedup_dedup_ns"] += _metric(dedup, "dedup_ns")
    bucket["dedup_peak_retained_entries_max"] = max(
        bucket["dedup_peak_retained_entries_max"], _metric(dedup, "peak_retained_entries")
    )
    reference_checks = _metric(reference, "exact_checks")
    dedup_checks = _metric(dedup, "exact_checks")
    if dedup_checks < reference_checks:
        bucket["strict_exact_check_reductions"] += 1
    elif dedup_checks == reference_checks:
        bucket["equal_exact_check_rows"] += 1
    else:
        bucket["exact_check_regressions"] += 1


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


def _bit(mapping, field, failures, default_missing=False):
    if not isinstance(mapping, dict):
        failures.append("row_not_object")
        return 0
    if field not in mapping and default_missing:
        return 0
    value = mapping.get(field)
    if not isinstance(value, int) or isinstance(value, bool) or value not in (0, 1):
        failures.append(f"invalid_{field}")
        return 0
    return value


def _selected_signature(arm, label, failures):
    if not isinstance(arm, dict):
        failures.append(f"{label}_arm_not_object")
        return None, 0, 0
    if "selected" not in arm:
        failures.append(f"{label}_selected_missing")
        return None, 0, 0
    selected = arm["selected"]
    if selected is None:
        return None, 0, 0
    if not isinstance(selected, dict):
        failures.append(f"{label}_selected_not_object")
        return None, 0, 0
    required = ("fixed_relation", "source_residue", "recovered_target", "recovered_correctly")
    if any(field not in selected for field in required):
        failures.append(f"{label}_selected_fields_missing")
    if selected.get("source_residue") != 0:
        failures.append(f"{label}_source_replay")
    recovered = selected.get("recovered_correctly")
    if not isinstance(recovered, int) or isinstance(recovered, bool) or recovered not in (0, 1):
        failures.append(f"{label}_invalid_recovered_correctly")
        recovered = 0
    signature = (
        selected.get("fixed_relation"),
        selected.get("source_residue"),
        selected.get("recovered_target"),
        selected.get("recovered_correctly"),
    )
    return signature, 1, recovered


def _check_ok_row(row):
    failures = []
    if row.get("semantic_parity") is not True:
        failures.append("semantic_parity")
    reference_success = _bit(row, "reference_success", failures)
    dedup_success = _bit(row, "dedup_success", failures)
    reference_recovery = _bit(row, "reference_dl_recovered", failures)
    dedup_recovery = _bit(row, "dedup_dl_recovered", failures)
    top_success = _bit(row, "success", failures)
    top_recovery = _bit(row, "dl_recovered", failures, default_missing=True)

    reference = row.get("reference")
    dedup = row.get("dedup")
    for label, arm, extra_metrics in (
        ("reference", reference, ()),
        ("dedup", dedup, DEDUP_ONLY_METRICS),
    ):
        if not isinstance(arm, dict):
            failures.append(f"{label}_arm_not_object")
            continue
        for field in COMMON_METRICS + extra_metrics:
            value = arm.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                failures.append(f"invalid_{label}_{field}")

    reference_signature, reference_selected, reference_selected_recovery = _selected_signature(
        reference, "reference", failures
    )
    dedup_signature, dedup_selected, dedup_selected_recovery = _selected_signature(
        dedup, "dedup", failures
    )
    if reference_signature != dedup_signature:
        failures.append("selected_signature")
    if reference_success != reference_selected:
        failures.append("reference_success_selected_mismatch")
    if dedup_success != dedup_selected:
        failures.append("dedup_success_selected_mismatch")
    if reference_recovery != reference_selected_recovery:
        failures.append("reference_recovery_selected_mismatch")
    if dedup_recovery != dedup_selected_recovery:
        failures.append("dedup_recovery_selected_mismatch")
    if reference_success != dedup_success:
        failures.append("relation_status")
    if reference_recovery != dedup_recovery:
        failures.append("recovery_status")
    if top_success != dedup_success:
        failures.append("top_level_success_mismatch")
    if top_recovery != dedup_recovery:
        failures.append("top_level_recovery_mismatch")

    if isinstance(reference, dict) and isinstance(dedup, dict):
        reference_digest = reference.get("candidate_digest")
        dedup_full_digest = dedup.get("full_candidate_digest")
        if not isinstance(reference_digest, str) or not reference_digest:
            failures.append("reference_candidate_digest_missing")
        if not isinstance(dedup_full_digest, str) or not dedup_full_digest:
            failures.append("dedup_full_candidate_digest_missing")
        if reference_digest != dedup_full_digest:
            failures.append("full_candidate_digest")
        for field in ("retained_candidate_digest", "first_representative_mapping_digest"):
            if not isinstance(dedup.get(field), str) or not dedup[field]:
                failures.append(f"dedup_{field}_missing")

        reference_modular = _metric(reference, "modular_candidates")
        dedup_modular = _metric(dedup, "modular_candidates")
        reference_unique = _metric(reference, "unique_fixed_candidates")
        reference_duplicate = _metric(reference, "duplicate_fixed_candidates")
        dedup_unique = _metric(dedup, "unique_fixed_candidates")
        dedup_duplicate = _metric(dedup, "duplicate_fixed_candidates")
        reference_checks = _metric(reference, "exact_checks")
        dedup_checks = _metric(dedup, "exact_checks")
        if reference_modular != dedup_modular:
            failures.append("modular_candidate_count")
        for field in (
            "origins",
            "origin_table_entries",
            "unique_fixed_candidates",
            "duplicate_fixed_candidates",
            "transport_count",
        ):
            if _metric(reference, field) != _metric(dedup, field):
                failures.append(f"paired_{field}")
        if reference_unique + reference_duplicate != reference_modular:
            failures.append("reference_candidate_partition")
        if dedup_unique + dedup_duplicate != dedup_modular:
            failures.append("dedup_candidate_partition")
        if _metric(dedup, "hash_probes") != dedup_modular:
            failures.append("dedup_hash_probe_count")
        if _metric(dedup, "peak_retained_entries") != dedup_unique:
            failures.append("dedup_peak_retained_entries")
        if _metric(reference, "transport_count") != reference_modular:
            failures.append("reference_transport_count")
        if _metric(dedup, "transport_count") != dedup_modular:
            failures.append("dedup_transport_count")
        if reference_checks > reference_modular:
            failures.append("reference_exact_check_bound")
        if dedup_checks > dedup_unique:
            failures.append("dedup_exact_check_bound")
        if dedup_checks > reference_checks:
            failures.append("exact_check_regression")
        if _metric(reference, "source_replays") != reference_success:
            failures.append("reference_source_replay_count")
        if _metric(dedup, "source_replays") != dedup_success:
            failures.append("dedup_source_replay_count")
        for field in ("per_origin_candidates", "per_origin_candidate_digests"):
            reference_value = reference.get(field)
            dedup_value = dedup.get(field)
            if not isinstance(reference_value, dict) or not isinstance(dedup_value, dict):
                failures.append(f"{field}_missing")
            elif reference_value != dedup_value:
                failures.append(f"paired_{field}")
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

    aggregate_reduced = overall["dedup_exact_checks"] < overall["reference_exact_checks"]
    exact_check_reduction_observed = (
        roster["complete"]
        and not invalid_status_counts
        and not invariant_failures
        and overall["ok"] > 0
        and overall["exact_check_regressions"] == 0
        and overall["strict_exact_check_reductions"] > 0
        and aggregate_reduced
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
        "aggregate_exact_checks_reduced": aggregate_reduced,
        "exact_check_reduction_observed": exact_check_reduction_observed,
        "complete_work_optimization_established": False,
        "complete_work_optimization_reason": (
            "No prospectively frozen calibrated total-work weighting or isolated benchmark; "
            "wall_ns is diagnostic only."
        ),
        "overall": dict(overall),
        "by_r": {key: dict(value) for key, value in sorted(by_r.items())},
        "by_cell": {key: dict(value) for key, value in sorted(by_cell.items())},
    }


def _synthetic_arm(label, exact_checks):
    arm = {field: 1 for field in COMMON_METRICS}
    arm.update(
        {
            "origins": 2,
            "origin_table_entries": 8,
            "modular_candidates": 4,
            "unique_fixed_candidates": 3,
            "duplicate_fixed_candidates": 1,
            "transport_count": 4,
            "exact_checks": exact_checks,
            "source_replays": 1,
            "selected": {
                "fixed_relation": [1, 0],
                "source_residue": 0,
                "recovered_target": 7,
                "recovered_correctly": 1,
            },
        }
    )
    if label == "reference":
        arm["candidate_digest"] = "same-full-digest"
    else:
        arm.update(
            {
                "hash_probes": 4,
                "peak_retained_entries": 3,
                "dedup_ns": 1,
                "full_candidate_digest": "same-full-digest",
                "retained_candidate_digest": "retained-digest",
                "first_representative_mapping_digest": "mapping-digest",
            }
        )
    arm["per_origin_candidates"] = {"baseline": 4}
    arm["per_origin_candidate_digests"] = {"baseline": "origin-digest"}
    return arm


def _synthetic_ok(key, reference_checks=4, dedup_checks=2):
    return {
        "p": key[0], "family": key[1], "lift": key[2], "r": key[3], "idx": key[4],
        "status": "ok",
        "success": 1,
        "dl_recovered": 1,
        "semantic_parity": True,
        "reference_success": 1,
        "dedup_success": 1,
        "reference_dl_recovered": 1,
        "dedup_dl_recovered": 1,
        "reference": _synthetic_arm("reference", reference_checks),
        "dedup": _synthetic_arm("dedup", dedup_checks),
    }


def selftest():
    key0 = (31, "generic", "balanced", 6, 0)
    key1 = (31, "generic", "balanced", 6, 1)
    keys = frozenset({key0, key1})
    strict = _synthetic_ok(key0)
    exclusion = {"p": 31, "family": "generic", "lift": "balanced", "r": 6, "idx": 1, "status": "small_order"}
    assert analyze_rows([strict, exclusion], keys)["exact_check_reduction_observed"]
    assert not analyze_rows([strict], keys)["exact_check_reduction_observed"]
    assert not analyze_rows([strict, strict], keys)["exact_check_reduction_observed"]
    invalid = dict(exclusion, status="group_error")
    assert not analyze_rows([strict, invalid], keys)["exact_check_reduction_observed"]
    equal = _synthetic_ok(key0, 3, 3)
    assert not analyze_rows([equal, exclusion], keys)["exact_check_reduction_observed"]
    regression = _synthetic_ok(key0, 1, 2)
    regression_summary = analyze_rows([regression, exclusion], keys)
    assert not regression_summary["exact_check_reduction_observed"]
    assert regression_summary["invariant_failures"]
    return {
        "status": "PASS",
        "tests": [
            "complete_with_allowed_exclusion",
            "partial",
            "duplicate",
            "invalid_status",
            "equal_checks",
            "per_row_regression",
        ],
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
