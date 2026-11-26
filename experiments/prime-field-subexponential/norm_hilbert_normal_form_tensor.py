#!/usr/bin/env python3
"""Measure balanced tensor ranks of norm-quotient normal-form maps."""

from collections import Counter
from itertools import combinations
import json
from pathlib import Path

from norm_hilbert_socle import degree_pivots, quotient_coordinates
from norm_hilbert_universality import (
    DETERMINISTIC_COEFFICIENTS,
    coefficient_forms,
)


PRIME = 101
DIMENSIONS = tuple(range(3, 11))


def sparse_rank(rows, prime):
    pivots = {}
    for source in rows:
        row = {
            key: value % prime
            for key, value in source.items()
            if value % prime
        }
        while row:
            leading = max(row)
            if leading not in pivots:
                inverse = pow(row[leading], -1, prime)
                pivots[leading] = {
                    key: value * inverse % prime
                    for key, value in row.items()
                }
                break
            scale = row[leading]
            for key, value in pivots[leading].items():
                reduced = (row.get(key, 0) - scale * value) % prime
                if reduced:
                    row[key] = reduced
                elif key in row:
                    del row[key]
    return len(pivots)


def flattening_rank(variable_count, left_variables, standard, coordinates):
    left = tuple(sorted(left_variables))
    left_set = set(left)
    right = tuple(
        index for index in range(variable_count) if index not in left_set
    )
    rows = {}
    for source, vector in coordinates.items():
        source_left = tuple(source[index] for index in left)
        source_right = tuple(source[index] for index in right)
        for target_index, coefficient in enumerate(vector):
            if not coefficient:
                continue
            target = standard[target_index]
            row_key = (
                tuple(target[index] for index in left),
                source_left,
            )
            column_key = (
                tuple(target[index] for index in right),
                source_right,
            )
            row = rows.setdefault(row_key, {})
            row[column_key] = (
                row.get(column_key, 0) + coefficient
            ) % PRIME
    return sparse_rank(rows.values(), PRIME)


def quotient_flattening_rank(variable_count, left_variables, coordinates):
    """Schmidt rank of the canonical quotient map with output on the left."""
    left = tuple(sorted(left_variables))
    left_set = set(left)
    right = tuple(
        index for index in range(variable_count) if index not in left_set
    )
    rows = {}
    for source, vector in coordinates.items():
        source_left = tuple(source[index] for index in left)
        source_right = tuple(source[index] for index in right)
        for target_index, coefficient in enumerate(vector):
            if not coefficient:
                continue
            row = rows.setdefault((target_index, source_left), {})
            row[source_right] = (
                row.get(source_right, 0) + coefficient
            ) % PRIME
    return sparse_rank(rows.values(), PRIME)


def analyze(dimension, reference):
    positive = tuple(value for value in reference if value)
    peak_degree = max(
        range(len(positive)), key=lambda degree: positive[degree]
    )
    forms = coefficient_forms(
        dimension,
        PRIME,
        **DETERMINISTIC_COEFFICIENTS,
    )
    pivots = degree_pivots(forms, dimension, peak_degree, PRIME)
    standard, coordinates = quotient_coordinates(
        pivots,
        dimension,
        peak_degree,
        PRIME,
    )
    assert len(standard) == positive[peak_degree]
    cut_size = dimension // 2
    records = []
    for subset in combinations(range(dimension), cut_size):
        records.append({
            "left_variables": subset,
            "intrinsic_quotient_map_rank": quotient_flattening_rank(
                dimension,
                subset,
                coordinates,
            ),
            "operator_schmidt_rank": flattening_rank(
                dimension,
                subset,
                standard,
                coordinates,
            ),
        })
    ranks = [record["operator_schmidt_rank"] for record in records]
    histogram = Counter(ranks)
    ordered = sorted(ranks)
    minimum = ordered[0]
    quotient_ranks = [
        record["intrinsic_quotient_map_rank"] for record in records
    ]
    quotient_histogram = Counter(quotient_ranks)
    ordered_quotient = sorted(quotient_ranks)
    quotient_minimum = ordered_quotient[0]
    return {
        "variables": dimension,
        "peak_degree": peak_degree,
        "source_monomials": len(coordinates),
        "quotient_dimension": len(standard),
        "balanced_cut_size": cut_size,
        "balanced_cuts_tested": len(records),
        "minimum_operator_schmidt_rank": minimum,
        "median_operator_schmidt_rank": ordered[len(ordered) // 2],
        "maximum_operator_schmidt_rank": ordered[-1],
        "minimum_rank_cuts": [
            record["left_variables"]
            for record in records
            if record["operator_schmidt_rank"] == minimum
        ],
        "rank_histogram": [
            {"rank": rank, "count": count}
            for rank, count in sorted(histogram.items())
        ],
        "minimum_intrinsic_quotient_map_rank": quotient_minimum,
        "median_intrinsic_quotient_map_rank": ordered_quotient[
            len(ordered_quotient) // 2
        ],
        "maximum_intrinsic_quotient_map_rank": ordered_quotient[-1],
        "minimum_intrinsic_rank_cuts": [
            record["left_variables"]
            for record in records
            if record["intrinsic_quotient_map_rank"] == quotient_minimum
        ],
        "intrinsic_quotient_rank_histogram": [
            {"rank": rank, "count": count}
            for rank, count in sorted(quotient_histogram.items())
        ],
    }


def main():
    source = json.loads(
        Path(__file__).with_name("homogeneous_norm_hilbert.json").read_text(
            encoding="utf-8"
        )
    )
    references = {
        panel["projective_section_dimension"]: panel[
            "homogeneous_hilbert_function_through_zero"
        ]
        for panel in source["panels"]
    }
    panels = [
        analyze(dimension, references[dimension])
        for dimension in DIMENSIONS
    ]
    result = {
        "prime": PRIME,
        "dimensions": DIMENSIONS,
        "deterministic_coefficients": DETERMINISTIC_COEFFICIENTS,
        "algorithm_claimed": False,
        "scope": (
            "Exact balanced tensor ranks of the canonical quotient and "
            "standard monomial normal-form maps at the peak graded layer."
        ),
        "all_balanced_variable_subsets_tested": True,
        "panels": panels,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
