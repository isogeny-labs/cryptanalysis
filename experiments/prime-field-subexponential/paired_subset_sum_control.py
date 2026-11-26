#!/usr/bin/env python3
"""Verify the Subset-Sum reduction to paired non-spanning transversals."""

from itertools import product
import json

from projective_scaling_control import rank_mod


PRIME = 101
CASES = (
    ((3, 5, 6, 11), 14),
    ((3, 5, 6, 11), 4),
    ((2, 7, 9, 13, 18), 22),
)


def scale(row, scalar, prime):
    return tuple(scalar * value % prime for value in row)


def instance(weights, target, prime):
    n = len(weights)
    dimension = n + 1
    pairs = []
    for index, weight in enumerate(weights):
        unit = [0] * n
        unit[index] = 1
        included = (weight, *unit)
        excluded = (0, *unit)
        pairs.append((included, excluded))
    forcing = (-target % prime, *((-1) % prime for _ in range(n)))
    pairs.append((forcing, scale(forcing, 2, prime)))
    pairs.append((scale(forcing, 3, prime), scale(forcing, 4, prime)))
    assert len(pairs) == dimension + 1
    return pairs


def main():
    panels = []
    for weights, target in CASES:
        assert sum(weights) < PRIME
        pairs = instance(weights, target, PRIME)
        dimension = len(weights) + 1
        subset_solutions = []
        for bits in product((0, 1), repeat=len(weights)):
            if sum(
                weight for weight, bit in zip(weights, bits, strict=True)
                if bit == 0
            ) == target:
                subset_solutions.append(bits)

        deficient = []
        for choices in product((0, 1), repeat=len(pairs)):
            matrix = [
                pair[choice] for pair, choice in zip(pairs, choices, strict=True)
            ]
            rank = rank_mod(matrix, PRIME)
            modular_residual = (
                sum(
                    weight
                    for weight, choice in zip(
                        weights, choices[:len(weights)], strict=True
                    )
                    if choice == 0
                )
                - target
            ) % PRIME
            assert (rank < dimension) == (modular_residual == 0)
            if rank < dimension:
                deficient.append(choices)

        redundant_pair_multiplicity = 4
        assert len(deficient) == redundant_pair_multiplicity * len(
            subset_solutions
        )
        panels.append({
            "weights": weights,
            "target": target,
            "dimension": dimension,
            "row_pairs": len(pairs),
            "row_excess": len(pairs) - dimension,
            "sign_assignments": 2 ** len(pairs),
            "subset_solutions": len(subset_solutions),
            "rank_deficient_assignments": len(deficient),
            "redundant_pair_multiplicity": redundant_pair_multiplicity,
            "determinant_equivalence_verified": True,
        })

    result = {
        "prime": PRIME,
        "panels": panels,
        "all_panels_have_fixed_row_excess_one": all(
            panel["row_excess"] == 1 for panel in panels
        ),
        "all_determinant_equivalences_verified": all(
            panel["determinant_equivalence_verified"] for panel in panels
        ),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
