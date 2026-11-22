#!/usr/bin/env python3
"""Paired target-bearing relation selector over the frozen Xedni lift path."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path
import random


ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = ROOT / "research/xedni_plane_group_20261117/sweep.py"
SPEC = importlib.util.spec_from_file_location("xedni_plane_group_20261117", BASE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot import {BASE_PATH}")
BASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BASE)

ORIGINAL_RUN_TRIAL = BASE.run_trial
CURRENT_ORDER: int | None = None
LAST_DIAGNOSTICS: dict | None = None


def _candidate_relations(points, coefficients, origin, discriminant, bound):
    """Return every auxiliary-field zero in the frozen coefficient box."""
    q = next(prime for prime in BASE.Q_PRIMES if discriminant % prime)
    cq = tuple(coefficient % q for coefficient in coefficients)
    oq = BASE.primitive(origin, q)
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
    return candidates


def _select_exact(candidates, points, coefficients, origin, key):
    checks = 0
    for candidate in sorted(candidates, key=key):
        checks += 1
        if BASE.relation_sum(coefficients, origin, candidate, points) == origin:
            return candidate, checks
    return None, checks


def find_relation(points, coefficients, origin, discriminant, bound):
    """Compare the frozen ordering with recoverable-target-first ordering."""
    global LAST_DIAGNOSTICS
    if CURRENT_ORDER is None:
        raise RuntimeError("target selector called without a subgroup order")
    candidates = _candidate_relations(points, coefficients, origin, discriminant, bound)
    baseline, baseline_checks = _select_exact(
        candidates,
        points,
        coefficients,
        origin,
        lambda relation: (sum(map(abs, relation)), relation),
    )
    target, target_checks = _select_exact(
        candidates,
        points,
        coefficients,
        origin,
        lambda relation: (
            math.gcd(relation[-1], CURRENT_ORDER) != 1,
            sum(map(abs, relation)),
            relation,
        ),
    )
    LAST_DIAGNOSTICS = {
        "modular_candidates": len(candidates),
        "baseline_checks": baseline_checks,
        "target_checks": target_checks,
        "baseline_relation": list(baseline) if baseline is not None else None,
        "target_relation": list(target) if target is not None else None,
    }
    return target


def _source_instance(p, family, lift, r, index, master, pools):
    """Replay only the frozen source RNG prefix needed for source certificates."""
    rng = random.Random(f"{master}|{p}|{family}|{lift}|{r}|{index}")
    curves, square_table = pools[(p, family)]
    a, _b, cardinality = curves[index % len(curves)]
    for _ in range(200):
        x = rng.randrange(p)
        ordinates = square_table.get((x**3 + a * x + _b) % p)
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
    return order, multipliers, target


def run_trial(binary, tempdir, p, family, lift, r, index, master, pools):
    global CURRENT_ORDER, LAST_DIAGNOSTICS
    source = _source_instance(p, family, lift, r, index, master, pools)
    CURRENT_ORDER = source[0] if source is not None else None
    LAST_DIAGNOSTICS = None
    try:
        row = ORIGINAL_RUN_TRIAL(
            binary, tempdir, p, family, lift, r, index, master, pools
        )
    finally:
        CURRENT_ORDER = None
    if row["status"] != "ok":
        return row
    if source is None or LAST_DIAGNOSTICS is None:
        row["status"] = "selector_internal_error"
        return row

    order, multipliers, target = source
    origin_left, origin_right = row["origin_pair"]
    origin_multiplier = -(multipliers[origin_left] + multipliers[origin_right])
    row.update(LAST_DIAGNOSTICS)
    for label in ("baseline", "target"):
        relation = row[f"{label}_relation"]
        row[f"{label}_success"] = int(relation is not None)
        row[f"{label}_dl_recovered"] = 0
        if relation is None:
            continue
        residue, recovered = BASE.source_recovery(
            relation, multipliers, origin_multiplier, order
        )
        if residue:
            row["status"] = "selector_source_cert_failed"
            return row
        row[f"{label}_dl_recovered"] = int(recovered == target % order)
    if row["success"] != row["target_success"]:
        row["status"] = "selector_internal_error"
    if row.get("dl_recovered", 0) != row["target_dl_recovered"]:
        row["status"] = "selector_internal_error"
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
    origin, _, _ = BASE.choose_chord_origin(coefficients, points, 8)
    global CURRENT_ORDER, LAST_DIAGNOSTICS
    CURRENT_ORDER = 73
    LAST_DIAGNOSTICS = None
    try:
        selected = find_relation(points, coefficients, origin, 635904, BASE.NBOX)
    finally:
        CURRENT_ORDER = None
    assert LAST_DIAGNOSTICS is not None
    baseline = LAST_DIAGNOSTICS["baseline_relation"]
    assert baseline is not None and baseline[-1] == 0
    assert selected is not None and math.gcd(selected[-1], 73) == 1
    assert BASE.relation_sum(coefficients, origin, baseline, points) == origin
    assert BASE.relation_sum(coefficients, origin, selected, points) == origin
    return {
        "status": "PASS",
        "baseline_relation": baseline,
        "target_relation": list(selected),
        "baseline_checks": LAST_DIAGNOSTICS["baseline_checks"],
        "target_checks": LAST_DIAGNOSTICS["target_checks"],
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
