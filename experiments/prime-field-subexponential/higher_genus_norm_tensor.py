#!/usr/bin/env python3
"""Measure intrinsic quotient tensor ranks in genera three through seven."""

from collections import Counter
from itertools import combinations
import json
from math import comb
from random import Random

from higher_genus_norm_hilbert import (
    coefficient_forms,
    random_curve_coefficients,
)
from norm_hilbert_normal_form_tensor import quotient_flattening_rank
from norm_hilbert_socle import degree_pivots, quotient_coordinates


PRIME = 101
GENERA = tuple(range(3, 8))
DIMENSIONS = (8, 9)
SAMPLES = 2
SEED = 91_330_117
MAXIMUM_DEGREE = 4


def layer_data(forms, dimension, degree):
    pivots = degree_pivots(forms, dimension, degree, PRIME)
    layer_dimension = comb(
        dimension + degree - 1,
        degree,
    ) - len(pivots)
    return layer_dimension, pivots


def sample_panel(genus, dimension, coefficients):
    forms = coefficient_forms(
        dimension,
        genus,
        PRIME,
        **coefficients,
    )
    layers = []
    pivots_by_degree = []
    for degree in range(MAXIMUM_DEGREE + 1):
        layer_dimension, pivots = layer_data(forms, dimension, degree)
        layers.append(layer_dimension)
        pivots_by_degree.append(pivots)
    peak_degree = max(range(len(layers)), key=lambda degree: layers[degree])
    assert peak_degree < MAXIMUM_DEGREE
    assert layers[peak_degree + 1] <= layers[peak_degree]
    standard, coordinates = quotient_coordinates(
        pivots_by_degree[peak_degree],
        dimension,
        peak_degree,
        PRIME,
    )
    assert len(standard) == layers[peak_degree]
    ranks = [
        quotient_flattening_rank(
            dimension,
            subset,
            coordinates,
        )
        for subset in combinations(range(dimension), dimension // 2)
    ]
    ordered = sorted(ranks)
    histogram = Counter(ranks)
    return {
        "hilbert_prefix_through_degree_four": layers,
        "peak_degree": peak_degree,
        "quotient_dimension": len(standard),
        "balanced_cuts_tested": len(ranks),
        "minimum_intrinsic_rank": ordered[0],
        "median_intrinsic_rank": ordered[len(ordered) // 2],
        "maximum_intrinsic_rank": ordered[-1],
        "rank_histogram": [
            {"rank": rank, "count": count}
            for rank, count in sorted(histogram.items())
        ],
    }


def main():
    rng = Random(SEED)
    panels = []
    for genus in GENERA:
        coefficients = [
            random_curve_coefficients(genus, PRIME, rng)
            for _ in range(SAMPLES)
        ]
        for dimension in DIMENSIONS:
            samples = [
                sample_panel(genus, dimension, item)
                for item in coefficients
            ]
            summaries = [
                (
                    tuple(sample["hilbert_prefix_through_degree_four"]),
                    sample["peak_degree"],
                    sample["quotient_dimension"],
                    sample["minimum_intrinsic_rank"],
                    sample["median_intrinsic_rank"],
                    sample["maximum_intrinsic_rank"],
                )
                for sample in samples
            ]
            panels.append({
                "genus": genus,
                "projective_section_dimension": dimension,
                "samples": samples,
                "all_sample_summaries_match": len(set(summaries)) == 1,
            })
    result = {
        "prime": PRIME,
        "genera": GENERA,
        "dimensions": DIMENSIONS,
        "samples_per_genus": SAMPLES,
        "seed": SEED,
        "algorithm_claimed": False,
        "scope": (
            "Basis-invariant balanced tensor ranks of canonical peak-layer "
            "quotient maps for valid curves in genera three through seven."
        ),
        "all_sample_summaries_match": all(
            panel["all_sample_summaries_match"] for panel in panels
        ),
        "panels": panels,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
