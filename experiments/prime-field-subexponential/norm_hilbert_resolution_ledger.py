#!/usr/bin/env python3
"""Lower-bound free-resolution width from norm-ideal Hilbert numerators."""

import json
from math import comb, log2
from pathlib import Path

from homogeneous_norm_hilbert import semiregular_hilbert_function


MODEL_DIMENSIONS = (8, 16, 32, 64, 128)


def hilbert_numerator(hilbert, variable_count):
    numerator = [0] * (len(hilbert) + variable_count)
    for degree, value in enumerate(hilbert):
        for shift in range(variable_count + 1):
            numerator[degree + shift] += (
                value * (-1 if shift % 2 else 1)
                * comb(variable_count, shift)
            )
    return numerator


def exact_panel(panel):
    dimension = panel["projective_section_dimension"]
    hilbert = panel["homogeneous_hilbert_function_through_zero"][:-1]
    numerator = hilbert_numerator(hilbert, dimension)
    maximum = max(map(abs, numerator))
    total = sum(map(abs, numerator))
    return {
        "projective_section_dimension": dimension,
        "hilbert_function": hilbert,
        "hilbert_numerator_nonzero_coefficients": [
            {"degree": degree, "coefficient": value}
            for degree, value in enumerate(numerator)
            if value
        ],
        "largest_absolute_numerator_coefficient": maximum,
        "minimum_free_summands_in_one_shift": maximum,
        "numerator_l1_norm": total,
        "minimum_total_free_summands": total,
    }


def model_panel(dimension):
    hilbert = semiregular_hilbert_function(dimension)[:-1]
    numerator = hilbert_numerator(hilbert, dimension)
    maximum = max(map(abs, numerator))
    total = sum(map(abs, numerator))
    return {
        "variables": dimension,
        "last_positive_hilbert_degree": len(hilbert) - 1,
        "log2_maximum_numerator_coefficient_per_variable": (
            log2(maximum) / dimension
        ),
        "log2_numerator_l1_norm_per_variable": (
            log2(total) / dimension
        ),
    }


def main():
    source = json.loads(
        Path(__file__).with_name("homogeneous_norm_hilbert.json").read_text(
            encoding="utf-8"
        )
    )
    result = {
        "scope": (
            "Exact Hilbert-numerator lower bounds for explicit graded free "
            "resolutions, plus a semi-regular model ledger."
        ),
        "algorithm_claimed": False,
        "exact_panels": [exact_panel(panel) for panel in source["panels"]],
        "semi_regular_model_only": [
            model_panel(dimension) for dimension in MODEL_DIMENSIONS
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
