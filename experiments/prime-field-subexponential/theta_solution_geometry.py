#!/usr/bin/env python3
"""Measure affine, Hamming, and Fourier structure of theta-hit signings."""

from collections import Counter, deque
from itertools import combinations
import json
from pathlib import Path
from random import Random
from statistics import median

from paired_span_state_control import SEED, extended_panel
from principal_minor_spectrum_control import flip_matrix, principal_minor_values
from toy_jacobian import GenusTwo


PRIME = 101


def binary_rank(values, width):
    basis = [0] * width
    rank = 0
    for value in values:
        item = value
        while item:
            pivot = item.bit_length() - 1
            if basis[pivot]:
                item ^= basis[pivot]
            else:
                basis[pivot] = item
                rank += 1
                break
    return rank


def integer_walsh(values):
    result = values[:]
    stride = 1
    while stride < len(result):
        for start in range(0, len(result), 2 * stride):
            for offset in range(stride):
                left = result[start + offset]
                right = result[start + stride + offset]
                result[start + offset] = left + right
                result[start + stride + offset] = left - right
        stride *= 2
    return result


def component_sizes(solutions, width):
    remaining = set(solutions)
    sizes = []
    while remaining:
        root = remaining.pop()
        queue = deque([root])
        size = 0
        while queue:
            item = queue.popleft()
            size += 1
            for bit in range(width):
                neighbor = item ^ (1 << bit)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def compact_metrics(solutions, width):
    count = len(solutions)
    base = solutions[0]
    affine_rank = binary_rank([value ^ base for value in solutions[1:]], width)
    distances = Counter(
        (left ^ right).bit_count() for left, right in combinations(solutions, 2)
    )
    xor_counts = Counter(left ^ right for left in solutions for right in solutions)
    solution_set = set(solutions)
    walsh = integer_walsh([
        int(mask in solution_set) for mask in range(1 << width)
    ])
    nontrivial = [abs(value) for value in walsh[1:]]
    return {
        "affine_rank": affine_rank,
        "hamming_one_edges": distances[1],
        "maximum_nontrivial_walsh_absolute_value": max(nontrivial),
        "maximum_ordered_pair_xor_multiplicity_off_zero": max(
            multiplicity for value, multiplicity in xor_counts.items() if value
        ) if count > 1 else 0,
    }


def matched_random_summary(count, width):
    rng = Random(SEED + 1000 * width + count)
    samples = [
        compact_metrics(rng.sample(range(1 << width), count), width)
        for _ in range(64)
    ]
    return {
        key: {
            "minimum": min(sample[key] for sample in samples),
            "median": median(sample[key] for sample in samples),
            "maximum": max(sample[key] for sample in samples),
        }
        for key in samples[0]
    }


def analyze(curve, panel):
    matrix = flip_matrix(curve, panel)
    width = len(matrix)
    _, determinant_values = principal_minor_values(matrix, curve.p)
    solutions = [
        mask for mask, value in enumerate(determinant_values) if value == 0
    ]
    count = len(solutions)
    compact = compact_metrics(solutions, width)

    distances = Counter(
        (left ^ right).bit_count() for left, right in combinations(solutions, 2)
    )
    xor_counts = Counter(left ^ right for left in solutions for right in solutions)
    solution_set = set(solutions)
    indicator = [int(mask in solution_set) for mask in range(1 << width)]
    walsh = integer_walsh(indicator)
    nontrivial = [abs(value) for value in walsh[1:]]
    coordinate_weights = [
        sum(mask >> bit & 1 for mask in solutions) for bit in range(width)
    ]
    hamming_edges = distances[1]

    return {
        "square_slots": width,
        "theta_hits": count,
        "f2_affine_span_dimension": compact["affine_rank"],
        "f2_ambient_dimension": width,
        "pairwise_hamming_distance_histogram": {
            str(distance): multiplicity
            for distance, multiplicity in sorted(distances.items())
        },
        "minimum_pairwise_hamming_distance": min(distances) if distances else None,
        "hamming_one_edges": hamming_edges,
        "hamming_component_sizes": component_sizes(solutions, width),
        "coordinate_one_counts": coordinate_weights,
        "maximum_nontrivial_walsh_absolute_value": max(nontrivial),
        "perfect_nontrivial_walsh_modes": sum(
            value == count for value in nontrivial
        ),
        "nonzero_nontrivial_walsh_modes": sum(value != 0 for value in nontrivial),
        "maximum_ordered_pair_xor_multiplicity_off_zero": max(
            multiplicity for value, multiplicity in xor_counts.items() if value
        ) if count > 1 else 0,
        "distinct_nonzero_pair_xors": sum(value != 0 for value in xor_counts),
        "matched_random_64_sample_summary": matched_random_summary(count, width),
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
