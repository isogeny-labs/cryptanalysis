#!/usr/bin/env python3
"""Measure block-Hankel displacement of hyperelliptic norm Hessians."""

from collections import Counter
import json
from pathlib import Path
from random import Random

from sympy import Poly, symbols

from interpolation_projection_control import matrix_multiply
from multisection_span_control import section_basis
from norm_hessian_algebra import quadratic_form_matrix
from paired_span_state_control import SEED, extended_panel
from signed_hankel_minrank import rank_mod
from toy_jacobian import GenusTwo


PRIME = 101


def transpose(matrix):
    return [list(column) for column in zip(*matrix, strict=True)]


def subtract(left, right, prime):
    return [
        [(a - b) % prime for a, b in zip(lrow, rrow, strict=True)]
        for lrow, rrow in zip(left, right, strict=True)
    ]


def block_shift(first_size, second_size):
    size = first_size + second_size
    shift = [[0] * size for _ in range(size)]
    for start, block_size in ((0, first_size), (first_size, second_size)):
        for index in range(1, block_size):
            shift[start + index][start + index - 1] = 1
    return shift


def homogeneous_hessians(curve, panel):
    poly = curve.poly
    r = panel["projective_section_dimension"]
    u = tuple(panel["target_u"])
    v = tuple(panel["target_v"])
    basis = section_basis(poly, u, v, r)
    variables = symbols(f"s0:{r + 1}")
    coefficients = [0] * (r + 3)
    for i, (bi, ai) in enumerate(basis):
        for j, (bj, aj) in enumerate(basis):
            numerator = poly.sub(
                poly.mul(poly.mul(bi, bj), curve.coefficients),
                poly.mul(ai, aj),
            )
            quotient = poly.exact_quotient(numerator, u)
            for degree, value in enumerate(quotient):
                coefficients[degree] += variables[i] * variables[j] * value
    return variables, [
        quadratic_form_matrix(
            Poly(coefficient, *variables, modulus=curve.p),
            variables,
            curve.p,
        )
        for coefficient in coefficients[:-1]
    ]


def analyze(curve, panel, source, attempts=None):
    r = panel["projective_section_dimension"]
    first_size = (r - 1) // 2 + 1
    second_size = r // 2 + 1
    _, hessians = homogeneous_hessians(curve, panel)
    shift = block_shift(first_size, second_size)
    shift_transpose = transpose(shift)
    ranks = [
        rank_mod(
            subtract(
                matrix_multiply(shift, hessian, curve.p),
                matrix_multiply(hessian, shift_transpose, curve.p),
                curve.p,
            ),
            curve.p,
        )
        for hessian in hessians
    ]
    result = {
        "projective_section_dimension": r,
        "homogeneous_parameter_dimension": r + 1,
        "first_polynomial_block_size": first_size,
        "second_polynomial_block_size": second_size,
        "coefficient_hessians": len(hessians),
        "panel_source": source,
        "block_hankel_displacement_ranks": ranks,
        "displacement_rank_histogram": {
            str(rank): count for rank, count in sorted(Counter(ranks).items())
        },
        "maximum_displacement_rank": max(ranks),
        "rank_bound_four_holds": max(ranks) <= 4,
    }
    if attempts is not None:
        result["construction_attempts"] = attempts
    return result


def main():
    source = json.loads(
        Path(__file__).with_name("binary_split_norm_control.json").read_text()
    )
    curve = GenusTwo(PRIME)
    panels = [
        analyze(curve, panel, "binary_split_norm_control.json")
        for panel in source["panels"]
    ]
    rng = Random(SEED)
    for dimension in range(8, 21):
        panel, _, attempts = extended_panel(curve, dimension, rng)
        panels.append(
            analyze(curve, panel, "extended planted divisor", attempts)
        )
    result = {
        "prime": PRIME,
        "genus": 2,
        "seed": SEED,
        "proved_displacement_rank_bound": 4,
        "panels": panels,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
