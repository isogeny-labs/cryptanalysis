#!/usr/bin/env python3
"""Recompute fixed-coordinate overlap on the deterministic pencil control."""

from __future__ import annotations

from collections import Counter
import json
import math
from pathlib import Path
import sys

import runner as pencil


COEFFICIENTS = (1, 0, 0, 0, 0, 0, -1, -1, 0, 1)
RAW_POINTS = (
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


def calculate():
    points = [pencil.BASE.primitive(point) for point in RAW_POINTS]
    baseline, left, right = pencil.BASE.choose_chord_origin(
        COEFFICIENTS, points, len(points) - 1
    )
    origins, rejected = pencil._admissible_origins(  # noqa: SLF001
        points, COEFFICIENTS, baseline, (left, right)
    )
    fixed_sets = {}
    local_counts = {}
    for origin in origins:
        candidates, _ = pencil._candidate_relations(  # noqa: SLF001
            points, COEFFICIENTS, origin, 635904, pencil.BASE.NBOX
        )
        fixed_sets[origin.tag] = {
            pencil._transport_to_fixed(  # noqa: SLF001
                relation, origin.left, origin.right
            )
            for relation in candidates
        }
        local_counts[origin.tag] = len(candidates)

    baseline_set = fixed_sets["baseline"]
    seen = set()
    per_origin = []
    for origin in origins:
        fixed = fixed_sets[origin.tag]
        per_origin.append(
            {
                "origin": origin.tag,
                "local_candidates": local_counts[origin.tag],
                "overlap_baseline": len(fixed & baseline_set),
                "marginal_unique_in_origin_order": len(fixed - seen),
                "new_invertible_vs_baseline": sum(
                    math.gcd(vector[-1], 73) == 1
                    for vector in fixed - baseline_set
                ),
            }
        )
        seen.update(fixed)

    multiplicities = Counter(
        vector for fixed in fixed_sets.values() for vector in fixed
    )
    histogram = Counter(multiplicities.values())
    union = set(multiplicities)
    return {
        "schema_version": 1,
        "status": "deterministic_control_not_natural_measurement",
        "origins": len(origins),
        "rejected_origins": rejected,
        "baseline_unique_fixed": len(baseline_set),
        "pencil_local_candidates": sum(local_counts.values()),
        "pencil_unique_fixed": len(union),
        "duplicate_local_representations": sum(local_counts.values()) - len(union),
        "new_unique_vs_baseline": len(union - baseline_set),
        "baseline_invertible_target": sum(
            math.gcd(vector[-1], 73) == 1 for vector in baseline_set
        ),
        "pencil_invertible_target": sum(
            math.gcd(vector[-1], 73) == 1 for vector in union
        ),
        "new_invertible_vs_baseline": sum(
            math.gcd(vector[-1], 73) == 1 for vector in union - baseline_set
        ),
        "exclusive_to_one_origin": histogram[1],
        "present_in_all_origins": histogram[len(origins)],
        "origin_multiplicity_histogram": {
            str(key): value for key, value in sorted(histogram.items())
        },
        "per_origin": per_origin,
    }


def main():
    actual = calculate()
    rendered = json.dumps(actual, indent=2, sort_keys=True) + "\n"
    if len(sys.argv) == 3 and sys.argv[1] == "--check":
        expected = json.loads(Path(sys.argv[2]).read_text())
        if actual != expected:
            raise SystemExit("coverage control differs from retained JSON")
    elif len(sys.argv) != 1:
        raise SystemExit("usage: coverage_control.py [--check EXPECTED.json]")
    print(rendered, end="")


if __name__ == "__main__":
    main()
