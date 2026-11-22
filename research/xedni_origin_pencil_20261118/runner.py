#!/usr/bin/env python3
"""Paired known-origin versus target-origin-pencil Xedni relation search."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import time


ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = ROOT / "research/xedni_plane_group_20261117/sweep.py"
SPEC = importlib.util.spec_from_file_location("xedni_plane_group_20261117", BASE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot import {BASE_PATH}")
BASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BASE)

ORIGINAL_RUN_TRIAL = BASE.run_trial
CURRENT_SOURCE: tuple[int, tuple[int, ...], int] | None = None
LAST_DIAGNOSTICS: dict | None = None


@dataclass(frozen=True)
class Origin:
    tag: str
    point: tuple[int, int, int]
    left: int
    right: int


def _transport_to_fixed(relation, left, right):
    """Translate origin-local coefficients to flex-origin coefficients."""
    coefficient_sum = sum(relation)
    fixed = list(relation)
    fixed[left] += coefficient_sum
    fixed[right] += coefficient_sum
    if sum(fixed) != 3 * coefficient_sum:
        raise ArithmeticError("chord-origin coefficient transport failed")
    return tuple(fixed)


def _transport_from_fixed(fixed, left, right):
    """Translate fixed coefficients to a specified chord-origin chart."""
    fixed_sum = sum(fixed)
    if fixed_sum % 3:
        raise ArithmeticError("fixed coefficient sum is not divisible by three")
    coefficient_sum = fixed_sum // 3
    relation = list(fixed)
    relation[left] -= coefficient_sum
    relation[right] -= coefficient_sum
    if sum(relation) != coefficient_sum:
        raise ArithmeticError("inverse chord-origin coefficient transport failed")
    return tuple(relation)


def _source_replay(fixed, multipliers, target, order):
    residue = sum(
        coefficient * multiplier
        for coefficient, multiplier in zip(fixed, multipliers)
    ) % order
    target_coefficient = fixed[-1] % order
    recovered = None
    if math.gcd(target_coefficient, order) == 1:
        known = sum(
            coefficient * multiplier
            for coefficient, multiplier in zip(fixed[:-1], multipliers[:-1])
        )
        recovered = (-known * pow(target_coefficient, -1, order)) % order
    return residue, recovered, int(recovered == target % order)


def _candidate_relations(points, coefficients, origin, discriminant, bound):
    """Enumerate the complete auxiliary-field zero set for one origin."""
    q = next(prime for prime in BASE.Q_PRIMES if discriminant % prime)
    cq = tuple(coefficient % q for coefficient in coefficients)
    oq = BASE.primitive(origin.point, q)
    pq = [BASE.primitive(point, q) for point in points]
    tables = [
        {
            scalar: BASE.group_mul(cq, oq, scalar, point, q)
            for scalar in range(-bound, bound + 1)
        }
        for point in pq
    ]
    half = (len(points) + 1) // 2

    def enumerate_sums(indices):
        rows = [((), oq)]
        for index in indices:
            rows = [
                (
                    relation + (scalar,),
                    BASE.group_add(cq, oq, total, tables[index][scalar], q),
                )
                for relation, total in rows
                for scalar in range(-bound, bound + 1)
            ]
        return rows

    left = {}
    for relation, total in enumerate_sums(range(half)):
        left.setdefault(total, []).append(relation)
    candidates = []
    for relation, total in enumerate_sums(range(half, len(points))):
        opposite = BASE.group_neg(cq, oq, total, q)
        for prefix in left.get(opposite, ()):
            candidate = prefix + relation
            if any(candidate):
                candidates.append(candidate)
    return candidates, len(points) * (2 * bound + 1)


def _candidate_digest(rows):
    payload = json.dumps(rows, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()


def _build_search_space(origins, points, coefficients, discriminant, bound, order):
    rows = []
    table_entries = 0
    per_origin = {}
    per_origin_digest_rows = {}
    for origin_index, origin in enumerate(origins):
        candidates, entries = _candidate_relations(
            points, coefficients, origin, discriminant, bound
        )
        table_entries += entries
        per_origin[origin.tag] = len(candidates)
        per_origin_digest_rows[origin.tag] = []
        for relation in candidates:
            fixed = _transport_to_fixed(relation, origin.left, origin.right)
            per_origin_digest_rows[origin.tag].append(
                [list(relation), list(fixed)]
            )
            rows.append(
                {
                    "origin_index": origin_index,
                    "origin_tag": origin.tag,
                    "relation": relation,
                    "fixed": fixed,
                    "key": (
                        math.gcd(fixed[-1], order) != 1,
                        sum(map(abs, relation)),
                        origin_index,
                        relation,
                    ),
                }
            )
    rows.sort(key=lambda row: row["key"])
    digest_rows = [
        [row["origin_tag"], list(row["relation"]), list(row["fixed"])]
        for row in rows
    ]
    per_origin_digests = {
        tag: _candidate_digest(digest_rows_for_origin)
        for tag, digest_rows_for_origin in per_origin_digest_rows.items()
    }
    return (
        rows,
        table_entries,
        per_origin,
        per_origin_digests,
        _candidate_digest(digest_rows),
    )


def _search(origins, points, coefficients, discriminant, bound, source):
    order, multipliers, target = source
    started = time.perf_counter_ns()
    rows, table_entries, per_origin, per_origin_digests, digest = _build_search_space(
        origins, points, coefficients, discriminant, bound, order
    )
    construction_ns = time.perf_counter_ns() - started
    unique_fixed_candidates = len({row["fixed"] for row in rows})
    checks = 0
    selected = None
    check_started = time.perf_counter_ns()
    for row in rows:
        checks += 1
        origin = origins[row["origin_index"]]
        if (
            BASE.relation_sum(coefficients, origin.point, row["relation"], points)
            == origin.point
        ):
            residue, recovered, recovered_correctly = _source_replay(
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
    exact_check_ns = time.perf_counter_ns() - check_started
    return {
        "origins": len(origins),
        "origin_table_entries": table_entries,
        "modular_candidates": len(rows),
        "unique_fixed_candidates": unique_fixed_candidates,
        "duplicate_fixed_candidates": len(rows) - unique_fixed_candidates,
        "transport_count": len(rows),
        "exact_checks": checks,
        "source_replays": int(selected is not None),
        "construction_ns": construction_ns,
        "exact_check_ns": exact_check_ns,
        "wall_ns": time.perf_counter_ns() - started,
        "per_origin_candidates": per_origin,
        "per_origin_candidate_digests": per_origin_digests,
        "candidate_digest": digest,
        "selected": selected,
    }


def _admissible_origins(points, coefficients, baseline_origin, baseline_pair):
    selected = {BASE.primitive(point) for point in points}
    origins = [
        Origin("baseline", BASE.primitive(baseline_origin), *baseline_pair)
    ]
    rejected = []
    target_index = len(points) - 1
    for partner in range(target_index):
        tag = f"target-{partner}"
        try:
            point = BASE.third_intersection(
                coefficients, points[target_index], points[partner]
            )
        except (ArithmeticError, ValueError) as error:
            rejected.append({"tag": tag, "reason": f"construction:{error}"})
            continue
        if point in selected:
            rejected.append({"tag": tag, "reason": "selected_point"})
            continue
        origins.append(Origin(tag, point, target_index, partner))
    return origins, rejected


def find_relation(points, coefficients, origin, discriminant, bound):
    """Run both frozen arms and return the candidate in baseline coordinates."""
    global LAST_DIAGNOSTICS
    if CURRENT_SOURCE is None:
        raise RuntimeError("origin-pencil selector called without source data")
    baseline_point, baseline_left, baseline_right = BASE.choose_chord_origin(
        coefficients, points, len(points) - 1
    )
    if baseline_point != BASE.primitive(origin):
        raise ArithmeticError("baseline origin changed before paired search")
    origins, rejected = _admissible_origins(
        points,
        coefficients,
        baseline_point,
        (baseline_left, baseline_right),
    )
    baseline = _search(
        origins[:1], points, coefficients, discriminant, bound, CURRENT_SOURCE
    )
    candidate = _search(
        origins, points, coefficients, discriminant, bound, CURRENT_SOURCE
    )
    if baseline["per_origin_candidate_digests"]["baseline"] != candidate[
        "per_origin_candidate_digests"
    ]["baseline"]:
        raise ArithmeticError("candidate arm did not preserve baseline candidates")
    LAST_DIAGNOSTICS = {
        "baseline": baseline,
        "candidate": candidate,
        "candidate_origin_rejections": rejected,
    }
    selected = candidate["selected"]
    if selected is None:
        return None
    if selected["source_residue"]:
        raise ArithmeticError("selected relation failed fixed-origin source replay")
    fixed = tuple(selected["fixed_relation"])
    baseline_relation = _transport_from_fixed(
        fixed, baseline_left, baseline_right
    )
    if BASE.relation_sum(coefficients, origin, baseline_relation, points) != origin:
        raise ArithmeticError("selected relation failed baseline-origin transport")
    return baseline_relation


def _source_instance(p, family, lift, r, index, master, pools):
    """Replay the frozen source RNG prefix without trusting the producer row."""
    rng = random.Random(f"{master}|{p}|{family}|{lift}|{r}|{index}")
    curves, square_table = pools[(p, family)]
    a, b, cardinality = curves[index % len(curves)]
    for _ in range(200):
        x = rng.randrange(p)
        ordinates = square_table.get((x**3 + a * x + b) % p)
        if ordinates:
            break
    else:
        return None
    base = (x, rng.choice(ordinates))
    order = BASE.old.divisors_order(cardinality, base, a, p)
    if order < 2 * r + 1:
        return None
    classes, multipliers = set(), []
    while len(multipliers) < r - 1:
        multiplier = rng.randrange(1, order)
        if multiplier in classes or order - multiplier in classes:
            continue
        classes.add(multiplier)
        multipliers.append(multiplier)
    while True:
        target = rng.randrange(1, order)
        if target not in classes and order - target not in classes:
            break
    multipliers.append(target)
    return order, tuple(multipliers), target


def run_trial(binary, tempdir, p, family, lift, r, index, master, pools):
    global CURRENT_SOURCE, LAST_DIAGNOSTICS
    source = _source_instance(p, family, lift, r, index, master, pools)
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
        row["status"] = "origin_pencil_internal_error"
        return row

    baseline = LAST_DIAGNOSTICS["baseline"]["selected"]
    candidate = LAST_DIAGNOSTICS["candidate"]["selected"]
    row["baseline_success"] = int(baseline is not None)
    row["candidate_success"] = int(candidate is not None)
    row["baseline_dl_recovered"] = int(
        baseline is not None and baseline["recovered_correctly"]
    )
    row["candidate_dl_recovered"] = int(
        candidate is not None and candidate["recovered_correctly"]
    )
    if row["success"] != row["candidate_success"]:
        row["status"] = "origin_pencil_internal_error"
    if row.get("dl_recovered", 0) != row["candidate_dl_recovered"]:
        row["status"] = "origin_pencil_internal_error"
    if row["candidate_success"] < row["baseline_success"]:
        row["status"] = "origin_pencil_lost_baseline_relation"
    if row["candidate_dl_recovered"] < row["baseline_dl_recovered"]:
        row["status"] = "origin_pencil_lost_baseline_recovery"
    return row


def selftest():
    coefficients = (1, 0, 0, 0, 0, 0, -1, -1, 0, 1)
    raw_points = (
        ("0", "1", "1"),
        ("2", "-7", "8"),
        ("56", "419", "1"),
        ("-6244", "24655", "21952"),
        ("5232472", "-8824453", "11089567"),
        ("8246188998", "30795303833", "588480472"),
        ("-51055373209680", "101098481076377", "85923747076383"),
        ("1796402375990961480", "-2098030206970736191", "2631958890650432000"),
        ("160221897655974195623120", "396235626125845757178647", "25634128246348207648607"),
    )
    points = [BASE.primitive(map(int, point)) for point in raw_points]
    baseline_origin, left, right = BASE.choose_chord_origin(coefficients, points, 8)
    origins, rejected = _admissible_origins(
        points, coefficients, baseline_origin, (left, right)
    )

    control = (-2, -1, 0, 0, 0, 0, 2, 0, 0)
    target_origin = next(origin for origin in origins if origin.tag == "target-0")
    assert BASE.relation_sum(
        coefficients, target_origin.point, control, points
    ) == target_origin.point
    fixed = _transport_to_fixed(control, target_origin.left, target_origin.right)
    assert fixed[-1] == -1
    baseline_control = _transport_from_fixed(fixed, left, right)
    assert BASE.relation_sum(
        coefficients, baseline_origin, baseline_control, points
    ) == baseline_origin
    residue, recovered, correct = _source_replay(
        fixed, tuple(range(1, 10)), 9, 73
    )
    assert residue == 0 and recovered == 9 and correct == 1

    zero_target_fixed = (1, -1, 0, 0, 0, 0, 0, 0, 0)
    zero_local = _transport_from_fixed(zero_target_fixed, 8, 0)
    assert zero_local[-1] + sum(zero_local) == 0

    source = (73, tuple(range(1, 10)), 9)
    baseline = _search(
        origins[:1], points, coefficients, 635904, BASE.NBOX, source
    )
    candidate = _search(origins, points, coefficients, 635904, BASE.NBOX, source)
    assert candidate["per_origin_candidate_digests"]["baseline"] == baseline[
        "per_origin_candidate_digests"
    ]["baseline"]
    assert candidate["selected"] is not None
    assert candidate["selected"]["source_residue"] == 0
    return {
        "status": "PASS",
        "admitted_origins": len(origins),
        "rejected_origins": rejected,
        "control_local_relation": list(control),
        "control_fixed_relation": list(fixed),
        "control_baseline_relation": list(baseline_control),
        "zero_fixed_target_preserved": True,
        "baseline_modular_candidates": baseline["modular_candidates"],
        "candidate_modular_candidates": candidate["modular_candidates"],
        "baseline_unique_fixed_candidates": baseline["unique_fixed_candidates"],
        "candidate_unique_fixed_candidates": candidate["unique_fixed_candidates"],
        "candidate_duplicate_fixed_candidates": candidate[
            "duplicate_fixed_candidates"
        ],
        "candidate_selected_origin": candidate["selected"]["origin_tag"],
        "candidate_recovered_target": candidate["selected"]["recovered_correctly"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("selftest", "run"))
    args, remainder = parser.parse_known_args()
    if args.command == "selftest":
        if remainder:
            parser.error("selftest takes no arguments")
        print(json.dumps(selftest(), sort_keys=True))
        return
    BASE.find_relation = find_relation
    BASE.run_trial = run_trial
    BASE.sys.argv = [str(BASE_PATH), "run", *remainder]
    BASE.main()


if __name__ == "__main__":
    main()
