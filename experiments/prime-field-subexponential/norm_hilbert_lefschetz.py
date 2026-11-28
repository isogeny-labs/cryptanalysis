#!/usr/bin/env python3
"""Test weak and strong Lefschetz maps in norm-convolution quotients."""

import json
from pathlib import Path
from random import Random

from homogeneous_norm_hilbert import rank_mod
from norm_hilbert_socle import degree_pivots, quotient_coordinates
from norm_hilbert_universality import (
    DETERMINISTIC_COEFFICIENTS,
    coefficient_forms,
)


PRIME = 101
DIMENSIONS = tuple(range(3, 10))
RANDOM_FORMS = 16
SEED = 884_113


def matrix_multiply(left, right, prime):
    return [
        [
            sum(
                left[row][middle] * right[middle][column]
                for middle in range(len(right))
            ) % prime
            for column in range(len(right[0]))
        ]
        for row in range(len(left))
    ]


def quotient_data(dimension, hilbert):
    forms = coefficient_forms(
        dimension,
        PRIME,
        **DETERMINISTIC_COEFFICIENTS,
    )
    data = []
    for degree, expected in enumerate(hilbert):
        pivots = degree_pivots(forms, dimension, degree, PRIME)
        standard, coordinates = quotient_coordinates(
            pivots, dimension, degree, PRIME
        )
        assert len(standard) == expected
        data.append((standard, coordinates))
    return data


def multiplication_matrices(data, coefficients):
    matrices = []
    for degree in range(len(data) - 1):
        source, _ = data[degree]
        target, target_coordinates = data[degree + 1]
        matrix = []
        for coordinate in range(len(target)):
            row = []
            for monomial in source:
                value = 0
                for variable, coefficient in enumerate(coefficients):
                    product = list(monomial)
                    product[variable] += 1
                    value += coefficient * target_coordinates[
                        tuple(product)
                    ][coordinate]
                row.append(value % PRIME)
            matrix.append(row)
        matrices.append(matrix)
    return matrices


def lefschetz_profile(data, hilbert, coefficients):
    matrices = multiplication_matrices(data, coefficients)
    power_ranks = []
    failures = []
    for source_degree in range(len(hilbert) - 1):
        product = matrices[source_degree]
        for target_degree in range(source_degree + 1, len(hilbert)):
            if target_degree > source_degree + 1:
                product = matrix_multiply(
                    matrices[target_degree - 1], product, PRIME
                )
            rank = rank_mod(product, len(product[0]), PRIME)
            expected = min(
                hilbert[source_degree], hilbert[target_degree]
            )
            record = {
                "source_degree": source_degree,
                "target_degree": target_degree,
                "rank": rank,
                "maximum_possible_rank": expected,
            }
            power_ranks.append(record)
            if rank != expected:
                failures.append(record)
    weak = all(
        record["rank"] == record["maximum_possible_rank"]
        for record in power_ranks
        if record["target_degree"] == record["source_degree"] + 1
    )
    return {
        "weak_lefschetz": weak,
        "strong_lefschetz": not failures,
        "power_ranks": power_ranks,
        "failures": failures,
    }


def random_form(dimension, rng):
    while True:
        coefficients = tuple(rng.randrange(PRIME) for _ in range(dimension))
        if any(coefficients):
            return coefficients


def main():
    source = json.loads(
        Path(__file__).with_name("homogeneous_norm_hilbert.json").read_text(
            encoding="utf-8"
        )
    )
    references = {
        panel["projective_section_dimension"]: tuple(
            value
            for value in panel[
                "homogeneous_hilbert_function_through_zero"
            ]
            if value
        )
        for panel in source["panels"]
    }
    rng = Random(SEED)
    panels = []
    for dimension in DIMENSIONS:
        hilbert = references[dimension]
        data = quotient_data(dimension, hilbert)
        ones = lefschetz_profile(data, hilbert, (1,) * dimension)
        random_records = []
        representative = None
        for _ in range(RANDOM_FORMS):
            coefficients = random_form(dimension, rng)
            record = lefschetz_profile(data, hilbert, coefficients)
            if representative is None:
                representative = {
                    "coefficients": coefficients,
                    **record,
                }
            random_records.append(record)
        panels.append({
            "projective_section_dimension": dimension,
            "hilbert_function": hilbert,
            "lefschetz_chain_count": max(hilbert),
            "all_ones_weak_lefschetz": ones["weak_lefschetz"],
            "all_ones_failures": ones["failures"],
            "random_forms_tested": RANDOM_FORMS,
            "random_weak_lefschetz_forms": sum(
                record["weak_lefschetz"] for record in random_records
            ),
            "random_strong_lefschetz_forms": sum(
                record["strong_lefschetz"] for record in random_records
            ),
            "representative_strong_form": representative,
        })
    result = {
        "prime": PRIME,
        "seed": SEED,
        "dimensions": DIMENSIONS,
        "random_forms_per_dimension": RANDOM_FORMS,
        "deterministic_coefficients": DETERMINISTIC_COEFFICIENTS,
        "algorithm_claimed": False,
        "scope": (
            "Exact multiplication ranks for powers of linear forms in the "
            "deterministic norm-convolution quotients."
        ),
        "all_random_forms_weak_lefschetz": all(
            panel["random_weak_lefschetz_forms"] == RANDOM_FORMS
            for panel in panels
        ),
        "random_strong_lefschetz_forms": sum(
            panel["random_strong_lefschetz_forms"] for panel in panels
        ),
        "random_forms_tested": RANDOM_FORMS * len(panels),
        "panels": panels,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
