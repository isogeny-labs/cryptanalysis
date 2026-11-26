#!/usr/bin/env python3
"""Test split multiplicative cosets whose root polynomial is P(X^f)."""

import json
from collections import Counter
from itertools import combinations
from random import Random

from binary_split_norm_control import build_panel
from toy_jacobian import GenusTwo


PRIME = 101
SEED = 8_314_159
MAX_LARGE_CENSUS = 32


class FixedChoiceRandom(Random):
    def __init__(self, seed, chosen):
        super().__init__(seed)
        self.chosen = list(chosen)

    def sample(self, population, count):
        assert count == len(self.chosen)
        return list(self.chosen)


def subgroup(order):
    generator = pow(2, (PRIME - 1) // order, PRIME)
    return tuple(sorted({pow(generator, index, PRIME) for index in range(order)}))


def split_cosets(curve, order):
    group = subgroup(order)
    seen = set()
    out = []
    for scalar in range(1, PRIME):
        coset = tuple(sorted({scalar * value % PRIME for value in group}))
        if coset in seen:
            continue
        seen.add(coset)
        if all(len(curve.roots(x)) == 2 for x in coset):
            out.append(coset)
    return out


def is_composed_root_set(xs, order, include_zero):
    expected_residue = 1 if include_zero else 0
    coefficients = [1]
    for root in xs:
        new = [0] * (len(coefficients) + 1)
        for index, coefficient in enumerate(coefficients):
            new[index] = (new[index] - root * coefficient) % PRIME
            new[index + 1] = (new[index + 1] + coefficient) % PRIME
        coefficients = new
    return all(
        coefficient == 0 or degree % order == expected_residue
        for degree, coefficient in enumerate(coefficients)
    )


def summarize(rows):
    histogram = Counter(row["minimum_static_certificate_degree"] for row in rows)
    return {
        "panels": len(rows),
        "certificate_degree_histogram": {
            str(degree): count for degree, count in sorted(histogram.items())
        },
        "minimum_certificate_degree": min(histogram),
        "maximum_certificate_degree": max(histogram),
        "all_composition_checks_pass": all(
            row.get("composition_check", True) for row in rows
        ),
    }


def panel_row(panel, arm, composition_check=None):
    row = {
        "arm": arm,
        "split_abscissae": panel["split_abscissae"],
        "construction_attempts": panel["construction_attempts"],
        "minimum_static_certificate_degree": panel[
            "minimum_static_certificate_degree"
        ],
        "macaulay_columns_at_certificate": panel[
            "macaulay_columns_at_certificate"
        ],
    }
    if composition_check is not None:
        row["composition_check"] = composition_check
    return row


def configuration(curve, variables, order, include_zero, coordinator):
    tail_slots = variables + 2
    cosets_needed = (tail_slots - int(include_zero)) // order
    cosets = split_cosets(curve, order)
    choices = list(combinations(cosets, cosets_needed))
    coordinator.shuffle(choices)
    if len(choices) > MAX_LARGE_CENSUS:
        choices = choices[:MAX_LARGE_CENSUS]

    composed = []
    for index, selected in enumerate(choices):
        xs = ([0] if include_zero else []) + [
            x for coset in selected for x in coset
        ]
        chosen = [(x, curve.roots(x)) for x in xs]
        panel = build_panel(
            curve,
            variables,
            FixedChoiceRandom(f"{SEED}/composed/{variables}/{index}", chosen),
        )
        composed.append(
            panel_row(
                panel,
                "composed",
                is_composed_root_set(xs, order, include_zero),
            )
        )

    random_rows = []
    for index in range(len(composed)):
        panel = build_panel(
            curve,
            variables,
            Random(f"{SEED}/random/{variables}/{index}"),
        )
        random_rows.append(panel_row(panel, "random"))

    return {
        "variables": variables,
        "tail_slots": tail_slots,
        "coset_order": order,
        "include_zero": include_zero,
        "available_split_cosets": len(cosets),
        "available_coset_combinations": len(
            list(combinations(cosets, cosets_needed))
        ),
        "composed": summarize(composed),
        "random": summarize(random_rows),
    }


def main():
    curve = GenusTwo(PRIME)
    coordinator = Random(SEED)
    result = {
        "prime": PRIME,
        "genus": 2,
        "seed": SEED,
        "algorithm_claimed": False,
        "configurations": [
            configuration(curve, 4, 2, False, coordinator),
            configuration(curve, 5, 2, True, coordinator),
            configuration(curve, 6, 4, False, coordinator),
            configuration(curve, 7, 4, True, coordinator),
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
