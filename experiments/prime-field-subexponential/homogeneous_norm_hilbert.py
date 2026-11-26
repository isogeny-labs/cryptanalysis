#!/usr/bin/env python3
"""Measure the homogeneous Hilbert function of split norm equations."""

from math import comb, log2
import json
from pathlib import Path
from random import Random

from sympy import Integer, Poly, symbols

from binary_graeffe_macaulay import add_echelon_row, polynomial_dict
from multisection_span_control import section_basis
from paired_span_state_control import SEED, extended_panel
from toy_jacobian import GenusTwo


PRIME = 101
ASYMPTOTIC_DIMENSIONS = (8, 16, 32, 64, 128)


def exact_monomials(variable_count, degree):
    """Return all exponent vectors of one exact total degree."""
    out = []

    def visit(index, left, prefix):
        if index == variable_count - 1:
            out.append(tuple(prefix + [left]))
            return
        for value in range(left + 1):
            visit(index + 1, left - value, prefix + [value])

    visit(0, degree, [])
    return out


def leading_norm_forms(curve, panel):
    """Build the quadratic leading forms after projective dehomogenization."""
    poly = curve.poly
    dimension = panel["projective_section_dimension"]
    u = tuple(panel["target_u"])
    v = tuple(panel["target_v"])
    fixed = (dimension - 1) // 2 if dimension % 2 else dimension
    basis = section_basis(poly, u, v, dimension)
    variables = symbols(f"z0:{dimension}")
    parameters = []
    cursor = 0
    for index in range(dimension + 1):
        if index == fixed:
            parameters.append(Integer(1))
        else:
            parameters.append(variables[cursor])
            cursor += 1

    coefficients = [Integer(0)] * (dimension + 3)
    for i, (bi, ai) in enumerate(basis):
        for j, (bj, aj) in enumerate(basis):
            numerator = poly.sub(
                poly.mul(poly.mul(bi, bj), curve.coefficients),
                poly.mul(ai, aj),
            )
            quotient = poly.exact_quotient(numerator, u)
            for degree, value in enumerate(quotient):
                coefficients[degree] += parameters[i] * parameters[j] * value

    forms = []
    for coefficient in coefficients[:-1]:
        terms = polynomial_dict(
            Poly(coefficient, *variables, modulus=curve.p), curve.p
        )
        leading = {
            monomial: value
            for monomial, value in terms.items()
            if sum(monomial) == 2
        }
        if leading:
            forms.append(leading)
    return forms


def homogeneous_hilbert_function(forms, variable_count, prime):
    """Compute exact-degree quotient dimensions until the first zero."""
    hilbert = [1, variable_count]
    ranks = [0, 0]
    degree = 2
    while True:
        pivots = {}
        for form in forms:
            for multiplier in exact_monomials(variable_count, degree - 2):
                row = {
                    tuple(left + right for left, right in zip(
                        monomial, multiplier, strict=True
                    )): coefficient
                    for monomial, coefficient in form.items()
                }
                add_echelon_row(pivots, row, prime)
        columns = comb(variable_count + degree - 1, degree)
        quotient = columns - len(pivots)
        ranks.append(len(pivots))
        hilbert.append(quotient)
        if quotient == 0:
            return hilbert, ranks
        degree += 1
        if degree > 2 * variable_count + 2:
            raise AssertionError("homogeneous quotient did not vanish")


def semiregular_coefficient(variable_count, degree):
    """Coefficient of (1-t^2)^(r+2)/(1-t)^r before truncation."""
    return sum(
        (-1) ** index
        * comb(variable_count + 2, index)
        * comb(variable_count + degree - 2 * index - 1, variable_count - 1)
        for index in range(degree // 2 + 1)
    )


def semiregular_hilbert_function(variable_count):
    values = []
    for degree in range(2 * variable_count + 3):
        value = semiregular_coefficient(variable_count, degree)
        if value <= 0:
            values.append(0)
            return values
        values.append(value)
    raise AssertionError("semi-regular series did not truncate")


def analyze_panel(curve, panel, source):
    dimension = panel["projective_section_dimension"]
    forms = leading_norm_forms(curve, panel)
    hilbert, ranks = homogeneous_hilbert_function(forms, dimension, curve.p)
    semiregular = semiregular_hilbert_function(dimension)
    comparison_length = max(len(hilbert), len(semiregular))
    padded_actual = hilbert + [0] * (comparison_length - len(hilbert))
    padded_semiregular = semiregular + [0] * (
        comparison_length - len(semiregular)
    )
    differences = [
        actual - predicted
        for actual, predicted in zip(
            padded_actual, padded_semiregular, strict=True
        )
    ]
    return {
        "projective_section_dimension": dimension,
        "source": source,
        "nonzero_quadratic_leading_forms": len(forms),
        "homogeneous_hilbert_function_through_zero": hilbert,
        "homogeneous_macaulay_ranks": ranks,
        "semi_regular_hilbert_function_through_zero": semiregular,
        "coefficientwise_difference": differences,
        "maximum_absolute_difference": max(map(abs, differences)),
        "quotient_length": sum(hilbert),
        "maximum_hilbert_coefficient": max(hilbert),
    }


def asymptotic_model(dimension):
    values = semiregular_hilbert_function(dimension)[:-1]
    return {
        "variables": dimension,
        "last_positive_degree": len(values) - 1,
        "log2_quotient_length_per_variable": (
            log2(sum(values)) / dimension
        ),
        "log2_peak_per_variable": log2(max(values)) / dimension,
    }


def main():
    fixture = Path(__file__).with_name("binary_split_norm_control.json")
    source = json.loads(fixture.read_text(encoding="utf-8"))
    curve = GenusTwo(PRIME)
    panels = [
        analyze_panel(curve, panel, fixture.name)
        for panel in source["panels"]
    ]
    extended, _, attempts = extended_panel(curve, 8, Random(SEED))
    record = analyze_panel(curve, extended, "extended planted divisor")
    record["construction_attempts"] = attempts
    panels.append(record)
    result = {
        "prime": PRIME,
        "genus": 2,
        "extended_panel_seed": SEED,
        "scope": (
            "Exact homogeneous leading-ideal ranks for one planted split "
            "norm panel in each dimension 1 through 8."
        ),
        "algorithm_claimed": False,
        "panels": panels,
        "semi_regular_model_only": [
            asymptotic_model(dimension)
            for dimension in ASYMPTOTIC_DIMENSIONS
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
