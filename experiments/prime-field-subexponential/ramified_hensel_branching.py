#!/usr/bin/env python3
"""Ledger the free local branches behind the fixed-f ramified signature."""

import json
from pathlib import Path

from binary_split_norm_control import product_from_roots
from toy_jacobian import GenusTwo


PRIME = 101


def analyze(curve, panel):
    poly = curve.poly
    r = panel["projective_section_dimension"]
    b_degree = (r - 1) // 2
    modulus = product_from_roots(poly, panel["split_abscissae"])
    u = tuple(panel["target_u"])
    norm_right_side = poly.neg(poly.mul(u, modulus))
    coprime = poly.xgcd(curve.coefficients, norm_right_side)[0] == (1,)
    assert coprime

    f_degree = len(curve.coefficients) - 1
    hensel_precision = b_degree // f_degree + 2
    free_residue_dimension = (hensel_precision - 1) * f_degree
    return {
        "projective_section_dimension": r,
        "b_degree_bound": b_degree,
        "curve_polynomial_degree": f_degree,
        "norm_right_side_is_coprime_to_curve_polynomial": coprime,
        "minimum_f_adic_precision_determining_b": hensel_precision,
        "free_b_residue_dimension_per_root_signature": free_residue_dimension,
        "unrestricted_local_lifts_per_root_signature": (
            PRIME ** free_residue_dimension
        ),
        "degree_bounded_b_candidates_per_root_signature": (
            PRIME ** (b_degree + 1)
        ),
        "first_ramified_square_root_signature_count_over_algebraic_closure_at_most": (
            2 ** f_degree
        ),
    }


def main():
    source = json.loads(
        Path(__file__).with_name("binary_split_norm_control.json").read_text()
    )
    curve = GenusTwo(PRIME)
    result = {
        "prime": PRIME,
        "genus": 2,
        "curve_polynomial_degree": len(curve.coefficients) - 1,
        "panels": [analyze(curve, panel) for panel in source["panels"]],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
