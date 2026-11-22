#!/usr/bin/env python3
"""Paired full-pencil versus fixed-coordinate-deduplicated Xedni search."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import multiprocessing
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parents[2]
PARENT_PATH = ROOT / "research/xedni_origin_pencil_20261118/runner.py"
SPEC = importlib.util.spec_from_file_location("xedni_origin_pencil_20261118", PARENT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot import {PARENT_PATH}")
PENCIL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PENCIL
SPEC.loader.exec_module(PENCIL)

BASE = PENCIL.BASE
ORIGINAL_RUN_TRIAL = PENCIL.ORIGINAL_RUN_TRIAL
CURRENT_SOURCE: tuple[int, tuple[int, ...], int] | None = None
LAST_DIAGNOSTICS: dict | None = None
AUDIT_CONTEXT = None


def _audit_alias_slice(rows):
    coefficients, points, origins = AUDIT_CONTEXT
    masks = {}
    for row in rows:
        origin = origins[row["origin_index"]]
        exact = (
            BASE.relation_sum(coefficients, origin.point, row["relation"], points)
            == origin.point
        )
        mask = 2 if exact else 1
        masks[row["fixed"]] = masks.get(row["fixed"], 0) | mask
    return len(rows), masks


def _select(rows, origins, points, coefficients, source):
    order, multipliers, target = source
    checks = 0
    selected = None
    started = time.perf_counter_ns()
    for row in rows:
        checks += 1
        origin = origins[row["origin_index"]]
        if (
            BASE.relation_sum(coefficients, origin.point, row["relation"], points)
            == origin.point
        ):
            residue, recovered, recovered_correctly = PENCIL._source_replay(  # noqa: SLF001
                row["fixed"], multipliers, target, order
            )
            selected = {
                "origin_tag": origin.tag,
                "origin_pair": [origin.left, origin.right],
                "local_relation": list(row["relation"]),
                "fixed_relation": list(row["fixed"]),
                "source_residue": residue,
                "recovered_target": recovered,
                "recovered_correctly": recovered_correctly,
            }
            break
    return selected, checks, time.perf_counter_ns() - started


def _dedup_search(origins, points, coefficients, discriminant, bound, source):
    order, _, _ = source
    started = time.perf_counter_ns()
    rows, table_entries, per_origin, per_origin_digests, full_digest = (
        PENCIL._build_search_space(  # noqa: SLF001
            origins, points, coefficients, discriminant, bound, order
        )
    )
    construction_ns = time.perf_counter_ns() - started
    dedup_started = time.perf_counter_ns()
    seen = set()
    retained = []
    mapping_rows = []
    for full_index, row in enumerate(rows):
        fixed = row["fixed"]
        if fixed in seen:
            continue
        seen.add(fixed)
        retained.append(row)
        mapping_rows.append(
            [
                full_index,
                row["origin_tag"],
                list(row["relation"]),
                list(fixed),
            ]
        )
    dedup_ns = time.perf_counter_ns() - dedup_started
    selected, checks, exact_check_ns = _select(
        retained, origins, points, coefficients, source
    )
    retained_digest = PENCIL._candidate_digest(  # noqa: SLF001
        [
            [row["origin_tag"], list(row["relation"]), list(row["fixed"])]
            for row in retained
        ]
    )
    mapping_digest = hashlib.sha256(
        json.dumps(mapping_rows, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "origins": len(origins),
        "origin_table_entries": table_entries,
        "modular_candidates": len(rows),
        "unique_fixed_candidates": len(retained),
        "duplicate_fixed_candidates": len(rows) - len(retained),
        "transport_count": len(rows),
        "hash_probes": len(rows),
        "peak_retained_entries": len(retained),
        "exact_checks": checks,
        "source_replays": int(selected is not None),
        "construction_ns": construction_ns,
        "dedup_ns": dedup_ns,
        "exact_check_ns": exact_check_ns,
        "wall_ns": time.perf_counter_ns() - started,
        "per_origin_candidates": per_origin,
        "per_origin_candidate_digests": per_origin_digests,
        "full_candidate_digest": full_digest,
        "retained_candidate_digest": retained_digest,
        "first_representative_mapping_digest": mapping_digest,
        "selected": selected,
    }


def find_relation(points, coefficients, origin, discriminant, bound):
    """Run full and deduplicated pencils, returning dedup in baseline coordinates."""
    global LAST_DIAGNOSTICS
    if CURRENT_SOURCE is None:
        raise RuntimeError("dedup selector called without source data")
    baseline_point, baseline_left, baseline_right = BASE.choose_chord_origin(
        coefficients, points, len(points) - 1
    )
    if baseline_point != BASE.primitive(origin):
        raise ArithmeticError("baseline origin changed before paired search")
    origins, rejected = PENCIL._admissible_origins(  # noqa: SLF001
        points,
        coefficients,
        baseline_point,
        (baseline_left, baseline_right),
    )
    reference = PENCIL._search(  # noqa: SLF001
        origins, points, coefficients, discriminant, bound, CURRENT_SOURCE
    )
    dedup = _dedup_search(
        origins, points, coefficients, discriminant, bound, CURRENT_SOURCE
    )
    if reference["candidate_digest"] != dedup["full_candidate_digest"]:
        raise ArithmeticError("dedup arm changed the ordered full pencil")
    reference_selected = reference["selected"]
    dedup_selected = dedup["selected"]
    reference_signature = (
        None
        if reference_selected is None
        else (
            reference_selected["fixed_relation"],
            reference_selected["source_residue"],
            reference_selected["recovered_target"],
            reference_selected["recovered_correctly"],
        )
    )
    dedup_signature = (
        None
        if dedup_selected is None
        else (
            dedup_selected["fixed_relation"],
            dedup_selected["source_residue"],
            dedup_selected["recovered_target"],
            dedup_selected["recovered_correctly"],
        )
    )
    if reference_signature != dedup_signature:
        raise ArithmeticError("dedup changed selected fixed relation or recovery")
    LAST_DIAGNOSTICS = {
        "reference": reference,
        "dedup": dedup,
        "candidate_origin_rejections": rejected,
        "semantic_parity": True,
    }
    if dedup_selected is None:
        return None
    if dedup_selected["source_residue"]:
        raise ArithmeticError("dedup relation failed fixed-origin source replay")
    fixed = tuple(dedup_selected["fixed_relation"])
    baseline_relation = PENCIL._transport_from_fixed(  # noqa: SLF001
        fixed, baseline_left, baseline_right
    )
    if BASE.relation_sum(coefficients, origin, baseline_relation, points) != origin:
        raise ArithmeticError("dedup relation failed baseline-origin transport")
    return baseline_relation


def run_trial(binary, tempdir, p, family, lift, r, index, master, pools):
    global CURRENT_SOURCE, LAST_DIAGNOSTICS
    source = PENCIL._source_instance(  # noqa: SLF001
        p, family, lift, r, index, master, pools
    )
    CURRENT_SOURCE = source
    LAST_DIAGNOSTICS = None
    try:
        row = ORIGINAL_RUN_TRIAL(
            binary, tempdir, p, family, lift, r, index, master, pools
        )
    finally:
        CURRENT_SOURCE = None
    if LAST_DIAGNOSTICS is not None:
        row.update(LAST_DIAGNOSTICS)
    if row["status"] != "ok":
        return row
    if source is None or LAST_DIAGNOSTICS is None:
        row["status"] = "origin_dedup_internal_error"
        return row
    reference = LAST_DIAGNOSTICS["reference"]["selected"]
    dedup = LAST_DIAGNOSTICS["dedup"]["selected"]
    row["reference_success"] = int(reference is not None)
    row["dedup_success"] = int(dedup is not None)
    row["reference_dl_recovered"] = int(
        reference is not None and reference["recovered_correctly"]
    )
    row["dedup_dl_recovered"] = int(
        dedup is not None and dedup["recovered_correctly"]
    )
    if row["success"] != row["dedup_success"]:
        row["status"] = "origin_dedup_internal_error"
    if row.get("dl_recovered", 0) != row["dedup_dl_recovered"]:
        row["status"] = "origin_dedup_internal_error"
    if (
        row["reference_success"] != row["dedup_success"]
        or row["reference_dl_recovered"] != row["dedup_dl_recovered"]
    ):
        row["status"] = "origin_dedup_semantic_mismatch"
    return row


def _control_instance():
    coefficients = (1, 0, 0, 0, 0, 0, -1, -1, 0, 1)
    raw_points = (
        (0, 1, 1),
        (2, -7, 8),
        (56, 419, 1),
        (-6244, 24655, 21952),
        (5232472, -8824453, 11089567),
        (8246188998, 30795303833, 588480472),
        (-51055373209680, 101098481076377, 85923747076383),
        (1796402375990961480, -2098030206970736191, 2631958890650432000),
        (
            160221897655974195623120,
            396235626125845757178647,
            25634128246348207648607,
        ),
    )
    points = [BASE.primitive(point) for point in raw_points]
    baseline, left, right = BASE.choose_chord_origin(coefficients, points, 8)
    origins, rejected = PENCIL._admissible_origins(  # noqa: SLF001
        points, coefficients, baseline, (left, right)
    )
    return coefficients, points, origins, rejected


def selftest(audit_aliases=False):
    global AUDIT_CONTEXT
    coefficients, points, origins, rejected = _control_instance()
    source = (73, tuple(range(1, 10)), 9)
    reference = PENCIL._search(  # noqa: SLF001
        origins, points, coefficients, 635904, BASE.NBOX, source
    )
    dedup = _dedup_search(
        origins, points, coefficients, 635904, BASE.NBOX, source
    )
    assert reference["candidate_digest"] == dedup["full_candidate_digest"]
    assert reference["selected"] is not None and dedup["selected"] is not None
    assert reference["selected"]["fixed_relation"] == dedup["selected"][
        "fixed_relation"
    ]
    alias_checks = 0
    alias_classes = 0
    alias_workers = 0
    alias_wall_ns = 0
    if audit_aliases:
        rows, _, _, _, _ = PENCIL._build_search_space(  # noqa: SLF001
            origins, points, coefficients, 635904, BASE.NBOX, source[0]
        )
        alias_workers = 4
        chunk_size = (len(rows) + alias_workers - 1) // alias_workers
        chunks = [
            rows[start : start + chunk_size]
            for start in range(0, len(rows), chunk_size)
        ]
        AUDIT_CONTEXT = (coefficients, points, origins)
        audit_started = time.perf_counter_ns()
        with multiprocessing.get_context("fork").Pool(alias_workers) as pool:
            partials = pool.map(_audit_alias_slice, chunks)
        alias_wall_ns = time.perf_counter_ns() - audit_started
        exactness_masks = {}
        for checks, masks in partials:
            alias_checks += checks
            for fixed, mask in masks.items():
                exactness_masks[fixed] = exactness_masks.get(fixed, 0) | mask
        inconsistent = [fixed for fixed, mask in exactness_masks.items() if mask == 3]
        assert not inconsistent
        alias_classes = len(exactness_masks)
        AUDIT_CONTEXT = None
    return {
        "status": "PASS",
        "origins": len(origins),
        "rejected_origins": rejected,
        "full_candidates": reference["modular_candidates"],
        "retained_candidates": dedup["unique_fixed_candidates"],
        "duplicates_removed": dedup["duplicate_fixed_candidates"],
        "reference_exact_checks": reference["exact_checks"],
        "dedup_exact_checks": dedup["exact_checks"],
        "selected_fixed_relation": dedup["selected"]["fixed_relation"],
        "selected_recovery": dedup["selected"]["recovered_target"],
        "alias_audit_enabled": audit_aliases,
        "alias_checks": alias_checks,
        "alias_classes": alias_classes,
        "alias_workers": alias_workers,
        "alias_wall_ns": alias_wall_ns,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("selftest", "audit-aliases", "run"))
    args, remainder = parser.parse_known_args()
    if args.command in {"selftest", "audit-aliases"}:
        if remainder:
            parser.error(f"{args.command} takes no arguments")
        print(json.dumps(selftest(args.command == "audit-aliases"), sort_keys=True))
        return
    BASE.find_relation = find_relation
    BASE.run_trial = run_trial
    BASE.sys.argv = [str(PARENT_PATH), "run", *remainder]
    BASE.main()


if __name__ == "__main__":
    main()
