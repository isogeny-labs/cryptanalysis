#!/usr/bin/env python3
"""Independent-language fixed control for target-dependent chord recovery."""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = ROOT / "research/xedni_plane_group_20261117/sweep.py"
SPEC = importlib.util.spec_from_file_location("xedni_plane_group_20261117", BASE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot import {BASE_PATH}")
BASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BASE)


def main():
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
    assert all(BASE.on_cubic(coefficients, point) for point in points)

    target_index = 8
    chord_known_index = 0
    target_origin = BASE.third_intersection(
        coefficients, points[target_index], points[chord_known_index]
    )
    known_origin, _, _ = BASE.choose_chord_origin(coefficients, points, 8)
    assert target_origin not in set(points)

    relation = (-2, -1, 0, 0, 0, 0, 2, 0, 0)
    assert relation[target_index] == 0
    coefficient_sum = sum(relation)
    effective_coefficient = relation[target_index] + coefficient_sum
    assert coefficient_sum == -1 and effective_coefficient == -1
    assert (
        BASE.relation_sum(coefficients, target_origin, relation, points)
        == target_origin
    )
    assert (
        BASE.relation_sum(coefficients, known_origin, relation, points)
        != known_origin
    )
    assert (
        BASE.relation_sum(
            coefficients, target_origin, relation, points, BASE.Q_PRIMES[0]
        )
        == BASE.primitive(target_origin, BASE.Q_PRIMES[0])
    )

    order = 73
    multipliers = tuple(range(1, 10))
    known_term = (
        sum(
            scalar * multiplier
            for index, (scalar, multiplier) in enumerate(
                zip(relation, multipliers)
            )
            if index != target_index
        )
        + coefficient_sum * multipliers[chord_known_index]
    )
    residue = (effective_coefficient * multipliers[target_index] + known_term) % order
    assert residue == 0
    assert math.gcd(effective_coefficient, order) == 1
    recovered = (-known_term * pow(effective_coefficient, -1, order)) % order
    assert recovered == multipliers[target_index]

    mutated = list(relation)
    mutated[6] += 1
    assert (
        BASE.relation_sum(coefficients, target_origin, mutated, points)
        != target_origin
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "relation": list(relation),
                "explicit_target_coefficient": relation[target_index],
                "coefficient_sum": coefficient_sum,
                "effective_target_coefficient": effective_coefficient,
                "source_residue": residue,
                "recovered_target": recovered,
                "known_origin_rejects_relation": True,
                "mutation_rejected": True,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
