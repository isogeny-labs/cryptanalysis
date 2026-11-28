#!/usr/bin/env python3
"""Measure sparsity and balanced-cut rank of the principal-minor pullback."""

from collections import Counter
from itertools import combinations
import json
from math import comb
from pathlib import Path
from random import Random

from interpolation_projection_control import (
    add_identity,
    determinant,
    matrix_inverse,
    matrix_multiply,
    principal,
)
from paired_arrangement_mobius import candidate_rows
from paired_span_state_control import SEED, extended_panel
from signed_hankel_minrank import rank_mod
from toy_jacobian import GenusTwo


PRIME = 101


def flip_matrix(curve, panel):
    size = panel["projective_section_dimension"] + 1
    reduced = dict(panel)
    reduced["split_abscissae"] = panel["split_abscissae"][:size]
    rows = candidate_rows(curve, reduced)
    base = [rows[2 * index] for index in range(size)]
    alternate = [rows[2 * index + 1] for index in range(size)]
    differences = [
        [(right - left) % curve.p for left, right in zip(first, second, strict=True)]
        for first, second in zip(base, alternate, strict=True)
    ]
    return matrix_multiply(differences, matrix_inverse(base, curve.p), curve.p)


def subset_indices(mask, size):
    return [index for index in range(size) if mask >> index & 1]


def principal_minor_values(matrix, prime):
    size = len(matrix)
    values = []
    coefficients = []
    for mask in range(1 << size):
        selected = subset_indices(mask, size)
        if selected:
            block = principal(matrix, selected)
            coefficients.append(determinant(block, prime))
            values.append(determinant(add_identity(block, prime), prime))
        else:
            coefficients.append(1)
            values.append(1)
    return coefficients, values


def walsh_transform(values, prime):
    result = values[:]
    stride = 1
    while stride < len(result):
        for start in range(0, len(result), 2 * stride):
            for offset in range(stride):
                left = result[start + offset]
                right = result[start + stride + offset]
                result[start + offset] = (left + right) % prime
                result[start + stride + offset] = (left - right) % prime
        stride *= 2
    return result


def support_by_degree(values, size):
    count = Counter()
    for mask, value in enumerate(values):
        if value:
            count[mask.bit_count()] += 1
    return {str(degree): count[degree] for degree in sorted(count)}


def balanced_cut_ranks(values, size, prime):
    left_size = size // 2
    histogram = Counter()
    for left in combinations(range(size), left_size):
        left = tuple(left)
        right = tuple(index for index in range(size) if index not in left)
        rows = []
        for left_mask in range(1 << len(left)):
            row = []
            fixed = sum(
                1 << index for bit, index in enumerate(left)
                if left_mask >> bit & 1
            )
            for right_mask in range(1 << len(right)):
                mask = fixed | sum(
                    1 << index for bit, index in enumerate(right)
                    if right_mask >> bit & 1
                )
                row.append(values[mask])
            rows.append(row)
        histogram[rank_mod(rows, prime)] += 1
    return {str(rank): count for rank, count in sorted(histogram.items())}


def analyze(curve, panel):
    matrix = flip_matrix(curve, panel)
    size = len(matrix)
    projection_rank = (size // 2)
    coefficients, values = principal_minor_values(matrix, curve.p)
    walsh = walsh_transform(values, curve.p)
    coefficient_support = sum(value != 0 for value in coefficients)
    walsh_support = sum(value != 0 for value in walsh)
    coefficient_profile = support_by_degree(coefficients, size)
    walsh_profile = support_by_degree(walsh, size)
    return {
        "square_slots": size,
        "projection_rank": projection_rank,
        "boolean_degree": max(
            mask.bit_count() for mask, value in enumerate(coefficients) if value
        ),
        "principal_minor_coefficient_support": coefficient_support,
        "maximum_possible_degree_bounded_support": sum(
            comb(size, degree) for degree in range(projection_rank + 1)
        ),
        "principal_minor_support_by_degree": coefficient_profile,
        "walsh_support": walsh_support,
        "walsh_support_by_degree": walsh_profile,
        "balanced_cut_rank_histogram": balanced_cut_ranks(
            values, size, curve.p
        ),
        "maximum_balanced_cut_rank": 1 << (size // 2),
    }


def main():
    source = json.loads(
        Path(__file__).with_name("binary_split_norm_control.json").read_text()
    )
    curve = GenusTwo(PRIME)
    panels = list(source["panels"])
    rng = Random(SEED)
    for dimension in range(8, 11):
        panel, _, _ = extended_panel(curve, dimension, rng)
        panels.append(panel)
    result = {
        "prime": PRIME,
        "genus": 2,
        "panels": [analyze(curve, panel) for panel in panels],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
