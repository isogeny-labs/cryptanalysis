#!/usr/bin/env python3
"""Verify modular Subset Sum inside half-rank scaled projections."""

from itertools import product
import json

from interpolation_projection_control import (
    add_identity,
    determinant,
    matrix_multiply,
    principal,
    symmetric_under,
)
from signed_hankel_minrank import rank_mod


PRIME = 101


def block_diagonal(left, right):
    left_size = len(left)
    right_size = len(right)
    return [
        row + [0] * right_size for row in left
    ] + [
        [0] * left_size + row for row in right
    ]


def build_instance(weights, target, prime):
    items = len(weights)
    assert items >= 2 and sum(weights) < prime and target < prime
    inverse_items = pow(items, -1, prime)
    inverse_target = pow(target, -1, prime)
    coefficients = [
        -weight * inverse_target % prime for weight in weights
    ]

    hard_projection = [
        [inverse_items] * items for _ in range(items)
    ]
    padding = items - 2
    identity_padding = [
        [int(row == column) for column in range(padding)]
        for row in range(padding)
    ]
    projection = block_diagonal(hard_projection, identity_padding)
    scales = [items * value % prime for value in coefficients] + [1] * padding
    scaled_projection = [
        [scale * value % prime for value in row]
        for scale, row in zip(scales, projection, strict=True)
    ]
    return projection, scaled_projection, coefficients, padding


def analyze(weights, target, prime):
    items = len(weights)
    projection, scaled_projection, coefficients, padding = build_instance(
        weights, target, prime
    )
    ambient = len(projection)
    expected_rank = ambient // 2
    assert matrix_multiply(projection, projection, prime) == projection
    assert rank_mod(projection, prime) == expected_rank

    symmetry_weights = [pow(value, -1, prime) for value in coefficients]
    symmetry_weights += [1] * padding
    assert symmetric_under(symmetry_weights, scaled_projection, prime)

    subset_solutions = 0
    singular_subsets = 0
    all_values_match = True
    for bits in product((0, 1), repeat=ambient):
        selected = [index for index, bit in enumerate(bits) if bit]
        value = determinant(
            add_identity(principal(scaled_projection, selected), prime),
            prime,
        ) if selected else 1
        hard_bits = bits[:items]
        expected = (
            1 + sum(
                coefficient for coefficient, bit in zip(
                    coefficients, hard_bits, strict=True
                ) if bit
            )
        ) % prime
        padding_factor = pow(2, sum(bits[items:]), prime)
        all_values_match &= value == expected * padding_factor % prime
        singular_subsets += value == 0
        if not any(bits[items:]):
            subset_solutions += sum(
                weight for weight, bit in zip(weights, hard_bits, strict=True)
                if bit
            ) == target

    assert all_values_match
    assert singular_subsets == subset_solutions * (1 << padding)
    return {
        "weights": weights,
        "target": target,
        "items": items,
        "ambient_dimension": ambient,
        "projection_rank": expected_rank,
        "projection_rank_is_exactly_half": 2 * expected_rank == ambient,
        "projection_is_symmetric_idempotent": True,
        "scaled_projection_is_diagonally_self_adjoint": True,
        "modular_subset_sum_solutions": subset_solutions,
        "singular_principal_subsets": singular_subsets,
        "padding_multiplicity": 1 << padding,
        "all_determinant_values_match_subset_sum_formula": True,
    }


def main():
    panels = [
        ([3, 5, 8, 12], 13),
        ([1, 2, 4, 8, 16], 17),
        ([4, 6, 10, 15, 21, 28], 31),
    ]
    result = {
        "prime": PRIME,
        "statement": (
            "Modular Subset Sum embeds in singular principal-submatrix search "
            "for diagonally scaled symmetric projections of half ambient rank."
        ),
        "panels": [analyze(weights, target, PRIME) for weights, target in panels],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
