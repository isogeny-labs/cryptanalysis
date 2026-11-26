#!/usr/bin/env python3
"""Semi-regular witness degrees for r+g quadratic branch equations."""

import json
from math import comb, log2


def coefficient(equations, excess, degree):
    return sum(
        (-1) ** j * comb(excess, j) * comb(equations, degree - j)
        for j in range(min(excess, degree) + 1)
    )


def first_nonpositive(equations, excess):
    return next(
        degree
        for degree in range(equations + excess + 1)
        if coefficient(equations, excess, degree) <= 0
    )


def integer_log2(value):
    shift = max(0, value.bit_length() - 53)
    return log2(value >> shift) + shift


def row(genus, prime_bits):
    equations = genus * prime_bits
    variables = equations - genus
    sign_change = first_nonpositive(equations, genus)
    predicted_witness_degree = sign_change + 1
    columns = comb(variables + predicted_witness_degree, variables)
    log_columns = integer_log2(columns)
    return {
        "genus_excess": genus,
        "prime_bits": prime_bits,
        "binary_slots_equations": equations,
        "variables": variables,
        "first_nonpositive_hilbert_degree": sign_change,
        "predicted_witness_degree": predicted_witness_degree,
        "degree_over_variables": predicted_witness_degree / variables,
        "log2_macaulay_columns": log_columns,
        "column_exponent_in_p": log_columns / prime_bits,
    }


def main():
    print(
        json.dumps(
            {
                "model": (
                    "semi-regular r+g affine quadrics; coefficients of "
                    "(1-z^2)^(r+g)/(1-z)^r=(1+z)^(r+g)(1-z)^g"
                ),
                "binary_threshold": "m=g log2(p), r=m-g",
                "asymptotic_degree_over_variables": 0.5,
                "asymptotic_log2_columns_over_variables": 1.3774437510817343,
                "algorithm_claimed": False,
                "rows": [
                    row(genus, bits)
                    for genus in range(2, 8)
                    for bits in (32, 64, 128, 256)
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
