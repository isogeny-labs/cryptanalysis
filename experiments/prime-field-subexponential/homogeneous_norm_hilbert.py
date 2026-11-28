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
PROPAGATION_SIZE_LIMIT = 384


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
    propagated = [None, None]
    degree = 2
    predicted_quotient = None
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
        if predicted_quotient is not None:
            assert quotient == predicted_quotient
            predicted_quotient = None
        ranks.append(len(pivots))
        hilbert.append(quotient)
        propagated.append(None)
        if quotient == 0:
            return hilbert, ranks, propagated
        if variable_count * quotient <= PROPAGATION_SIZE_LIMIT:
            next_quotient, presentation_size, relation_rank = (
                propagated_next_dimension(
                    pivots, variable_count, degree, prime
                )
            )
            if next_quotient == 0:
                hilbert.append(0)
                ranks.append(comb(variable_count + degree, degree + 1))
                propagated.append({
                    "source_degree": degree,
                    "presentation_generators": presentation_size,
                    "relation_rank": relation_rank,
                })
                return hilbert, ranks, propagated
            predicted_quotient = next_quotient
        degree += 1
        if degree > 2 * variable_count + 2:
            raise AssertionError("homogeneous quotient did not vanish")


def rank_mod(rows, columns, prime):
    """Rank a short dense relation presentation over the prime field."""
    rows = [[value % prime for value in row] for row in rows]
    rank = 0
    for column in range(columns):
        pivot = next(
            (index for index in range(rank, len(rows)) if rows[index][column]),
            None,
        )
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        inverse = pow(rows[rank][column], -1, prime)
        rows[rank] = [value * inverse % prime for value in rows[rank]]
        for index in range(rank + 1, len(rows)):
            if not rows[index][column]:
                continue
            scale = rows[index][column]
            rows[index] = [
                (left - scale * right) % prime
                for left, right in zip(
                    rows[index], rows[rank], strict=True
                )
            ]
        rank += 1
        if rank == columns:
            break
    return rank


def propagated_next_dimension(pivots, variable_count, degree, prime):
    """Present A_(d+1) from multiplication of the known quotient A_d."""
    monomials = exact_monomials(variable_count, degree)
    standard = [monomial for monomial in monomials if monomial not in pivots]
    quotient_dimension = len(standard)
    coordinates = {}
    standard_index = {
        monomial: index for index, monomial in enumerate(standard)
    }
    for monomial in sorted(monomials):
        if monomial in standard_index:
            vector = [0] * quotient_dimension
            vector[standard_index[monomial]] = 1
            coordinates[monomial] = vector
            continue
        vector = [0] * quotient_dimension
        for lower, coefficient in pivots[monomial].items():
            if lower == monomial:
                continue
            for index, value in enumerate(coordinates[lower]):
                vector[index] -= coefficient * value
        coordinates[monomial] = [value % prime for value in vector]

    presentation_size = variable_count * quotient_dimension
    relations = []
    for monomial in exact_monomials(variable_count, degree + 1):
        representatives = []
        for variable, exponent in enumerate(monomial):
            if not exponent:
                continue
            predecessor = list(monomial)
            predecessor[variable] -= 1
            vector = [0] * presentation_size
            offset = variable * quotient_dimension
            vector[offset:offset + quotient_dimension] = coordinates[
                tuple(predecessor)
            ]
            representatives.append(vector)
        base = representatives[0]
        for representative in representatives[1:]:
            relation = [
                (left - right) % prime
                for left, right in zip(base, representative, strict=True)
            ]
            if any(relation):
                relations.append(relation)
    relation_rank = rank_mod(relations, presentation_size, prime)
    return (
        presentation_size - relation_rank,
        presentation_size,
        relation_rank,
    )


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
    hilbert, ranks, propagated = homogeneous_hilbert_function(
        forms, dimension, curve.p
    )
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
        "propagated_vanishing_certificate": next(
            (item for item in propagated if item is not None), None
        ),
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
    rng = Random(SEED)
    for dimension in (8, 9, 10):
        extended, _, attempts = extended_panel(curve, dimension, rng)
        record = analyze_panel(curve, extended, "extended planted divisor")
        record["construction_attempts"] = attempts
        panels.append(record)
    result = {
        "prime": PRIME,
        "genus": 2,
        "extended_panel_seed": SEED,
        "scope": (
            "Exact homogeneous leading-ideal ranks for one planted split "
            "norm panel in each dimension 1 through 10."
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
