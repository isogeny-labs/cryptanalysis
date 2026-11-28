#!/usr/bin/env python3
"""Ledger the affine unit rank of odd-degree hyperelliptic models."""

import json


PRIME_CHARACTERISTIC = "odd"


def main():
    panels = []
    for genus in range(2, 8):
        panels.append({
            "genus": genus,
            "odd_model_degree": 2 * genus + 1,
            "geometric_points_at_infinity": 1,
            "affine_s_unit_rank": 0,
            "affine_units_are_constant_field_units": True,
            "norm_one_constant_units_in_odd_characteristic": 2,
            "positive_rank_pell_infrastructure": False,
            "nonconstant_hilbert_90_parameters_require_poles": True,
            "even_degree_comparison": {
                "even_model_degree": 2 * genus + 2,
                "rational_points_at_infinity_when_leading_coefficient_is_square": 2,
                "affine_s_unit_rank": 1,
                "unit_multiplication_preserves_every_principal_ideal": True,
                "unit_multiplication_changes_split_prime_orientations": False,
                "regulator_coordinate_selects_ideal_class": False,
            },
        })
    result = {
        "characteristic": PRIME_CHARACTERISTIC,
        "model": "y^2=f(x), f squarefree of degree 2g+1",
        "panels": panels,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
