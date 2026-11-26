#!/usr/bin/env python3
"""Semi-regular branch-product ledgers for fiber degrees two through four."""

import json
from math import ceil, comb, log2


def integer_log2(value):
    shift = max(0, value.bit_length() - 53)
    return log2(value >> shift) + shift


def bounded_composition_coefficients(parts, width):
    coefficients = [1]
    for _ in range(parts):
        out = []
        window = 0
        for index in range(len(coefficients) + width - 1):
            if index < len(coefficients):
                window += coefficients[index]
            if index >= width:
                window -= coefficients[index - width]
            out.append(window)
        coefficients = out
    return coefficients


def first_nonpositive(base, excess):
    for degree in range(len(base) + excess):
        value = sum(
            (-1) ** j
            * comb(excess, j)
            * (base[degree - j] if 0 <= degree - j < len(base) else 0)
            for j in range(min(excess, degree) + 1)
        )
        if value <= 0:
            return degree
    raise AssertionError("finite Hilbert numerator never changed sign")


def entropy(value):
    if value in (0, 1):
        return 0.0
    return -value * log2(value) - (1 - value) * log2(1 - value)


def asymptotic_column_rate(branch_degree):
    alpha = (branch_degree - 1) / 2
    return (1 + alpha) * entropy(1 / (1 + alpha))


def row(genus, branch_degree, prime_bits):
    equations = ceil(genus * prime_bits / log2(branch_degree))
    variables = equations - genus
    base = bounded_composition_coefficients(equations, branch_degree)
    sign_change = first_nonpositive(base, genus)
    witness_degree = sign_change + 1
    columns = comb(variables + witness_degree, variables)
    log_columns = integer_log2(columns)
    return {
        "genus_excess": genus,
        "branch_degree": branch_degree,
        "prime_bits": prime_bits,
        "slot_equations": equations,
        "variables": variables,
        "predicted_witness_degree": witness_degree,
        "degree_over_variables": witness_degree / variables,
        "log2_macaulay_columns": log_columns,
        "column_exponent_in_p": log_columns / prime_bits,
    }


def main():
    asymptotics = []
    for branch_degree in (2, 3, 4):
        rate = asymptotic_column_rate(branch_degree)
        asymptotics.append(
            {
                "branch_degree": branch_degree,
                "degree_over_variables": (branch_degree - 1) / 2,
                "log2_columns_over_variables": rate,
                "column_exponent_per_genus": rate / log2(branch_degree),
            }
        )
    print(
        json.dumps(
            {
                "model": (
                    "semi-regular r+g equations of branch degree d; "
                    "Hilbert numerator (1+...+z^(d-1))^(r+g)(1-z)^g"
                ),
                "coverage_threshold": "m=g log(p)/log(d), r=m-g",
                "algorithm_claimed": False,
                "asymptotics": asymptotics,
                "rows": [
                    row(genus, degree, bits)
                    for genus in range(2, 8)
                    for degree in (2, 3, 4)
                    for bits in (64, 128)
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
