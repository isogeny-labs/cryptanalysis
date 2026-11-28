#!/usr/bin/env python3
"""Compute socle vectors for the deterministic norm-convolution ideals."""

import json
from pathlib import Path

from binary_graeffe_macaulay import add_echelon_row
from homogeneous_norm_hilbert import exact_monomials, rank_mod
from norm_hilbert_universality import (
    DETERMINISTIC_COEFFICIENTS,
    coefficient_forms,
)


PRIME = 101
DIMENSIONS = tuple(range(3, 10))


def degree_pivots(forms, variable_count, degree, prime):
    pivots = {}
    if degree < 2:
        return pivots
    for form in forms:
        for multiplier in exact_monomials(variable_count, degree - 2):
            row = {
                tuple(left + right for left, right in zip(
                    monomial, multiplier, strict=True
                )): coefficient
                for monomial, coefficient in form.items()
            }
            add_echelon_row(pivots, row, prime)
    return pivots


def quotient_coordinates(pivots, variable_count, degree, prime):
    monomials = exact_monomials(variable_count, degree)
    standard = [monomial for monomial in monomials if monomial not in pivots]
    standard_index = {
        monomial: index for index, monomial in enumerate(standard)
    }
    coordinates = {}
    for monomial in sorted(monomials):
        if monomial in standard_index:
            vector = [0] * len(standard)
            vector[standard_index[monomial]] = 1
            coordinates[monomial] = vector
            continue
        vector = [0] * len(standard)
        for lower, coefficient in pivots[monomial].items():
            if lower == monomial:
                continue
            for index, value in enumerate(coordinates[lower]):
                vector[index] -= coefficient * value
        coordinates[monomial] = [value % prime for value in vector]
    return standard, coordinates


def multiplication_rank(source, target_coordinates, target_dimension,
                        variable_count, prime):
    rows = []
    for variable in range(variable_count):
        for coordinate in range(target_dimension):
            row = []
            for monomial in source:
                product = list(monomial)
                product[variable] += 1
                row.append(target_coordinates[tuple(product)][coordinate])
            rows.append(row)
    return rank_mod(rows, len(source), prime)


def analyze(dimension, reference):
    forms = coefficient_forms(
        dimension,
        PRIME,
        **DETERMINISTIC_COEFFICIENTS,
    )
    positive = tuple(value for value in reference if value)
    data = []
    for degree, expected in enumerate(positive):
        pivots = degree_pivots(forms, dimension, degree, PRIME)
        standard, coordinates = quotient_coordinates(
            pivots, dimension, degree, PRIME
        )
        assert len(standard) == expected
        data.append((standard, coordinates))

    socle = []
    for degree, (source, _) in enumerate(data):
        if degree + 1 == len(data):
            dimension_at_degree = len(source)
        else:
            target, target_coordinates = data[degree + 1]
            multiplication = multiplication_rank(
                source,
                target_coordinates,
                len(target),
                dimension,
                PRIME,
            )
            dimension_at_degree = len(source) - multiplication
        socle.append(dimension_at_degree)
    nonzero = [
        {"degree": degree, "dimension": value}
        for degree, value in enumerate(socle)
        if value
    ]
    return {
        "projective_section_dimension": dimension,
        "hilbert_function": positive,
        "socle_vector": socle,
        "nonzero_socle_components": nonzero,
        "is_level": len(nonzero) == 1,
        "socle_degree": len(positive) - 1,
        "type": sum(socle),
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
            "Exact socle vectors of the deterministic norm-convolution "
            "quotients in dimensions 3 through 9."
        ),
        "even_dimensions_level_with_power_of_two_type": all(
            panel["is_level"]
            and panel["type"]
            == 2 ** (panel["projective_section_dimension"] // 2)
            for panel in panels
            if panel["projective_section_dimension"] % 2 == 0
        ),
        "odd_dimensions_have_terminal_type_one": all(
            panel["nonzero_socle_components"][-1]["dimension"] == 1
            for panel in panels
            if panel["projective_section_dimension"] % 2 == 1
        ),
        "panels": panels,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
