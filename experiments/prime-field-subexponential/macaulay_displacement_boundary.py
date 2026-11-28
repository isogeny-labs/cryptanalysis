#!/usr/bin/env python3
"""Measure the top-layer displacement boundary of affine norm Macaulay matrices."""

from math import comb, gcd
import json
from pathlib import Path

from binary_graeffe_macaulay import monomials, polynomial_dict
from norm_hessian_algebra import panel_equations
from signed_hankel_minrank import rank_mod
from toy_jacobian import GenusTwo


PRIME = 101


def fraction_string(numerator, denominator):
    common = gcd(numerator, denominator)
    return f"{numerator // common}/{denominator // common}"


def boundary_rows(equation, variables, degree, shifted_variable, prime):
    count = len(variables)
    coefficients = polynomial_dict(equation, prime)
    boundary = [
        exponent
        for exponent in monomials(count, degree - 2)
        if sum(exponent) == degree - 2
    ]
    columns = monomials(count, degree)
    column_index = {exponent: index for index, exponent in enumerate(columns)}
    rows = []
    for multiplier in boundary:
        row = [0] * len(columns)
        for monomial, coefficient in coefficients.items():
            if sum(monomial) > 1:
                continue
            exponent = list(multiplier)
            exponent[shifted_variable] += 1
            exponent = tuple(
                left + right
                for left, right in zip(exponent, monomial, strict=True)
            )
            assert sum(exponent) <= degree
            row[column_index[exponent]] = coefficient
        rows.append(row)
    return rows, len(columns)


def analyze(curve, panel):
    variables, equations = panel_equations(curve, panel)
    count = len(variables)
    degree = panel["minimum_static_certificate_degree"]
    zero = (0,) * count
    selected_index = next(
        index
        for index, equation in enumerate(equations)
        if polynomial_dict(equation, curve.p).get(zero, 0)
    )
    selected = equations[selected_index]
    constant = polynomial_dict(selected, curve.p)[zero]
    rows, columns = boundary_rows(selected, variables, degree, 0, curve.p)
    measured_rank = rank_mod(rows, curve.p)
    predicted_rank = comb(count + degree - 3, count - 1)
    assert len(rows) == predicted_rank
    assert measured_rank == predicted_rank
    total_multiplier_monomials = comb(count + degree - 2, count)
    total_rows = len(equations) * total_multiplier_monomials
    return {
        "projective_section_dimension": count,
        "certificate_degree": degree,
        "selected_equation_index": selected_index,
        "selected_equation_constant": constant,
        "top_multiplier_degree": degree - 2,
        "top_multiplier_boundary_monomials": predicted_rank,
        "measured_single_shift_boundary_rank": measured_rank,
        "boundary_rank_equals_boundary_monomials": True,
        "macaulay_columns_through_degree": columns,
        "macaulay_multiplier_monomials_per_equation": (
            total_multiplier_monomials
        ),
        "macaulay_rows_before_echelon": total_rows,
        "boundary_rank_over_columns": fraction_string(
            measured_rank, columns
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
        "panels": [analyze(curve, panel) for panel in source["panels"]],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
