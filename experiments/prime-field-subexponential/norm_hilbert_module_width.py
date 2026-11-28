#!/usr/bin/env python3
"""Measure norm-quotient generator width after generic linear sections."""

import json
from math import comb, isqrt, log2
from pathlib import Path
from random import Random

from homogeneous_norm_hilbert import homogeneous_hilbert_function, rank_mod
from norm_hilbert_universality import (
    DETERMINISTIC_COEFFICIENTS,
    coefficient_forms,
)


PRIME = 101
DIMENSIONS = tuple(range(3, 10))
FLAGS_PER_DIMENSION = 3
SEED = 63_105_907
MODEL_DIMENSIONS = (32, 64, 128, 256)
MODEL_FRACTIONS = ((0, 1), (1, 4), (1, 2), (3, 4), (7, 8))


def random_invertible_matrix(dimension, rng):
    while True:
        matrix = [
            [rng.randrange(PRIME) for _ in range(dimension)]
            for _ in range(dimension)
        ]
        if rank_mod(matrix, dimension, PRIME) == dimension:
            return matrix


def restrict_forms(forms, matrix, remaining_variables):
    """Substitute x_i=sum_j matrix[i][j] y_j in quadratic forms."""
    restricted = []
    for form in forms:
        image = {}
        for monomial, coefficient in form.items():
            support = []
            for variable, exponent in enumerate(monomial):
                support.extend([variable] * exponent)
            if len(support) != 2:
                raise AssertionError("expected a quadratic monomial")
            left, right = support
            for first in range(remaining_variables):
                for second in range(remaining_variables):
                    exponent = [0] * remaining_variables
                    exponent[first] += 1
                    exponent[second] += 1
                    exponent = tuple(exponent)
                    image[exponent] = (
                        image.get(exponent, 0)
                        + coefficient
                        * matrix[left][first]
                        * matrix[right][second]
                    ) % PRIME
        restricted.append({
            monomial: coefficient
            for monomial, coefficient in image.items()
            if coefficient
        })
    return restricted


def positive_difference(hilbert):
    differences = [hilbert[0]]
    differences.extend(
        hilbert[index] - hilbert[index - 1]
        for index in range(1, len(hilbert))
    )
    positive = []
    for value in differences:
        if value <= 0:
            break
        positive.append(value)
    return tuple(positive)


def predicted_sections(reference):
    current = tuple(value for value in reference if value)
    sections = {}
    for linear_forms in range(1, len(reference) + 20):
        current = positive_difference(current)
        if not current:
            break
        sections[linear_forms] = current
        if len(current) == 1:
            break
    return sections


def exact_panel(dimension, reference, rng):
    forms = coefficient_forms(
        dimension,
        PRIME,
        **DETERMINISTIC_COEFFICIENTS,
    )
    predicted = predicted_sections(reference)
    observations = {linear_forms: [] for linear_forms in range(1, dimension)}
    for _ in range(FLAGS_PER_DIMENSION):
        matrix = random_invertible_matrix(dimension, rng)
        for remaining in range(dimension - 1, 0, -1):
            restricted = restrict_forms(forms, matrix, remaining)
            hilbert, _, _ = homogeneous_hilbert_function(
                restricted,
                remaining,
                PRIME,
            )
            observations[dimension - remaining].append(
                tuple(value for value in hilbert if value)
            )

    sections = []
    for linear_forms, profiles in observations.items():
        expected = predicted[linear_forms]
        sections.append({
            "linear_forms": linear_forms,
            "remaining_variables": dimension - linear_forms,
            "predicted_hilbert_function": expected,
            "predicted_module_generator_lower_bound": sum(expected),
            "observed_profiles": sorted(set(profiles)),
            "all_flags_match_prediction": all(
                profile == expected for profile in profiles
            ),
        })
    return {
        "variables": dimension,
        "flags_tested": FLAGS_PER_DIMENSION,
        "sections": sections,
    }


def model_hilbert(variable_count, linear_forms):
    """Positive part of (1+t)^(r+2)(1-t)^(k+2)."""
    values = []
    for degree in range(2 * variable_count + 3):
        coefficient = sum(
            (-1) ** index
            * comb(linear_forms + 2, index)
            * comb(variable_count + 2, degree - index)
            for index in range(
                max(0, degree - variable_count - 2),
                min(linear_forms + 2, degree) + 1,
            )
        )
        if coefficient <= 0:
            break
        values.append(coefficient)
    return values


def model_record(variable_count, linear_forms, label):
    values = model_hilbert(variable_count, linear_forms)
    length = sum(values)
    return {
        "variables": variable_count,
        "linear_forms": linear_forms,
        "remaining_variables": variable_count - linear_forms,
        "section_label": label,
        "last_positive_degree": len(values) - 1,
        "module_generator_lower_bound": length,
        "log2_generator_bound_per_original_variable": (
            log2(length) / variable_count
        ),
    }


def model_panel(variable_count):
    records = []
    used = set()
    for numerator, denominator in MODEL_FRACTIONS:
        linear_forms = variable_count * numerator // denominator
        records.append(model_record(
            variable_count,
            linear_forms,
            f"k={numerator}r/{denominator}",
        ))
        used.add(linear_forms)
    remaining = isqrt(variable_count)
    linear_forms = variable_count - remaining
    if linear_forms not in used:
        records.append(model_record(
            variable_count,
            linear_forms,
            "r-k=floor(sqrt(r))",
        ))
    return {"variables": variable_count, "sections": records}


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
    rng = Random(SEED)
    exact = [
        exact_panel(dimension, references[dimension], rng)
        for dimension in DIMENSIONS
    ]
    result = {
        "prime": PRIME,
        "seed": SEED,
        "dimensions": DIMENSIONS,
        "flags_per_dimension": FLAGS_PER_DIMENSION,
        "deterministic_coefficients": DETERMINISTIC_COEFFICIENTS,
        "algorithm_claimed": False,
        "scope": (
            "Module-generator lower bounds from generic linear sections of "
            "the deterministic norm-convolution quotients."
        ),
        "all_exact_sections_match_iterated_positive_differences": all(
            section["all_flags_match_prediction"]
            for panel in exact
            for section in panel["sections"]
        ),
        "exact_panels": exact,
        "semi_regular_model_only": [
            model_panel(dimension) for dimension in MODEL_DIMENSIONS
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
