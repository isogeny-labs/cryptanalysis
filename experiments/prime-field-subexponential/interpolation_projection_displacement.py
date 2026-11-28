#!/usr/bin/env python3
"""Verify rank-two displacement for curve and Subset-Sum projections."""

from collections import Counter
import json
from pathlib import Path
from random import Random

from paired_span_state_control import SEED, extended_panel
from principal_minor_spectrum_control import flip_matrix
from scaled_projection_subset_sum import build_instance
from signed_hankel_minrank import rank_mod
from toy_jacobian import GenusTwo


PRIME = 101


def displacement(matrix, nodes, prime):
    return [
        [
            (nodes[row] - nodes[column]) * value % prime
            for column, value in enumerate(values)
        ]
        for row, values in enumerate(matrix)
    ]


def principal_displacement_histogram(matrix, nodes, prime):
    size = len(matrix)
    histogram = Counter()
    for mask in range(1 << size):
        selected = [index for index in range(size) if mask >> index & 1]
        block = [[matrix[row][column] for column in selected] for row in selected]
        block_nodes = [nodes[index] for index in selected]
        histogram[rank_mod(displacement(block, block_nodes, prime), prime)] += 1
    return {str(rank): count for rank, count in sorted(histogram.items())}


def curve_panel(curve, panel):
    matrix = flip_matrix(curve, panel)
    size = len(matrix)
    nodes = panel["split_abscissae"][:size]
    return {
        "square_slots": size,
        "matrix_rank": rank_mod(matrix, curve.p),
        "diagonal_node_displacement_rank": rank_mod(
            displacement(matrix, nodes, curve.p), curve.p
        ),
        "all_principal_displacement_rank_histogram": (
            principal_displacement_histogram(matrix, nodes, curve.p)
        ),
    }


def subset_sum_panel(weights, target, prime):
    _, matrix, _, _ = build_instance(weights, target, prime)
    nodes = list(range(1, len(matrix) + 1))
    return {
        "items": len(weights),
        "ambient_dimension": len(matrix),
        "matrix_rank": rank_mod(matrix, prime),
        "diagonal_node_displacement_rank": rank_mod(
            displacement(matrix, nodes, prime), prime
        ),
        "all_principal_displacement_rank_histogram": (
            principal_displacement_histogram(matrix, nodes, prime)
        ),
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
    subset_sum_instances = [
        ([3, 5, 8, 12], 13),
        ([1, 2, 4, 8, 16], 17),
        ([4, 6, 10, 15, 21, 28], 31),
    ]
    result = {
        "prime": PRIME,
        "curve_panels": [curve_panel(curve, panel) for panel in panels],
        "subset_sum_panels": [
            subset_sum_panel(weights, target, PRIME)
            for weights, target in subset_sum_instances
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
