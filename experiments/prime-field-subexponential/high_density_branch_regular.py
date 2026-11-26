#!/usr/bin/env python3
"""Macaulay stabilization for dense random binary branch systems."""

import json
from itertools import product
from math import comb
from random import Random

GENUS_EXCESS = 2
SEED = 5_910_223
PANELS = (
    (4, 7),
    (4, 3),
    (5, 11),
    (5, 5),
)


def monomials(variables, bound):
    out = []

    def visit(index, left, prefix):
        if index == variables - 1:
            for value in range(left + 1):
                out.append(tuple(prefix + [value]))
            return
        for value in range(left + 1):
            visit(index + 1, left - value, prefix + [value])

    visit(0, bound, [])
    return sorted(set(out), key=lambda exponent: (sum(exponent), exponent))


def add_echelon_row(pivots, row, prime):
    while row:
        leading = max(row, key=lambda exponent: (sum(exponent), exponent))
        coefficient = row[leading] % prime
        if leading not in pivots:
            inverse = pow(coefficient, -1, prime)
            pivots[leading] = {
                monomial: value * inverse % prime
                for monomial, value in row.items()
                if value % prime
            }
            return
        pivot = pivots[leading]
        for monomial, value in pivot.items():
            new_value = (row.get(monomial, 0) - coefficient * value) % prime
            if new_value:
                row[monomial] = new_value
            elif monomial in row:
                del row[monomial]


def random_form(variable_count, prime, rng):
    linear = [rng.randrange(prime) for _ in range(variable_count)]
    while not any(linear):
        linear = [rng.randrange(prime) for _ in range(variable_count)]
    return [rng.randrange(prime), *linear]


def multiply_forms(left, right, prime):
    variable_count = len(left) - 1
    zero = (0,) * variable_count
    out = {zero: left[0] * right[0] % prime}
    for index in range(variable_count):
        exponent = [0] * variable_count
        exponent[index] = 1
        exponent = tuple(exponent)
        out[exponent] = (
            left[0] * right[index + 1]
            + right[0] * left[index + 1]
        ) % prime
    for i in range(variable_count):
        for j in range(variable_count):
            exponent = [0] * variable_count
            exponent[i] += 1
            exponent[j] += 1
            exponent = tuple(exponent)
            out[exponent] = (
                out.get(exponent, 0) + left[i + 1] * right[j + 1]
            ) % prime
    return {monomial: value for monomial, value in out.items() if value}


def unique_affine_solution(forms, variable_count, prime):
    rows = [
        [value % prime for value in form[1:]] + [(-form[0]) % prime]
        for form in forms
    ]
    rank = 0
    pivots = []
    for column in range(variable_count):
        pivot = next(
            (i for i in range(rank, len(rows)) if rows[i][column]), None
        )
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        inverse = pow(rows[rank][column], -1, prime)
        rows[rank] = [value * inverse % prime for value in rows[rank]]
        for i in range(len(rows)):
            if i == rank or not rows[i][column]:
                continue
            scale = rows[i][column]
            rows[i] = [
                (a - scale * b) % prime
                for a, b in zip(rows[i], rows[rank], strict=True)
            ]
        pivots.append(column)
        rank += 1
    if any(not any(row[:-1]) and row[-1] for row in rows):
        return "inconsistent", None
    if rank < variable_count:
        return "positive_dimensional", None
    solution = [0] * variable_count
    for row, column in zip(rows[:rank], pivots, strict=True):
        solution[column] = row[-1]
    return "point", tuple(solution)


def roots_of_branch_system(branches, variable_count, prime):
    roots = set()
    for choices in product((0, 1), repeat=len(branches)):
        selected = [pair[choice] for pair, choice in zip(branches, choices)]
        status, solution = unique_affine_solution(
            selected, variable_count, prime
        )
        if status == "positive_dimensional":
            return None
        if status == "point":
            roots.add(solution)
    return roots


def evaluate_form(form, point, prime):
    return (
        form[0]
        + sum(
            coefficient * value
            for coefficient, value in zip(form[1:], point, strict=True)
        )
    ) % prime


def roots_are_transverse(branches, roots, prime):
    return all(
        all(
            sum(evaluate_form(form, root, prime) == 0 for form in pair) == 1
            for pair in branches
        )
        for root in roots
    )


def stabilization_profile(equations, root_count, variable_count, prime):
    profile = []
    first = None
    for degree in range(2, 7):
        pivots = {}
        for equation in equations:
            for multiplier in monomials(variable_count, degree - 2):
                row = {
                    tuple(
                        left + right
                        for left, right in zip(
                            monomial, multiplier, strict=True
                        )
                    ): coefficient
                    for monomial, coefficient in equation.items()
                }
                add_echelon_row(pivots, row, prime)
        columns = comb(variable_count + degree, variable_count)
        quotient_dimension = columns - len(pivots)
        profile.append(
            {
                "degree": degree,
                "columns": columns,
                "rank": len(pivots),
                "quotient_dimension": quotient_dimension,
            }
        )
        if quotient_dimension == root_count and first is None:
            first = degree
        if quotient_dimension < root_count:
            raise AssertionError("Macaulay quotient below rational root count")
    return first, profile


def panel(variable_count, prime, rng):
    equation_count = variable_count + GENUS_EXCESS
    for attempt in range(1, 1001):
        branches = [
            (
                random_form(variable_count, prime, rng),
                random_form(variable_count, prime, rng),
            )
            for _ in range(equation_count)
        ]
        roots = roots_of_branch_system(branches, variable_count, prime)
        if not roots or not roots_are_transverse(branches, roots, prime):
            continue
        equations = [
            multiply_forms(left, right, prime) for left, right in branches
        ]
        degree, profile = stabilization_profile(
            equations, len(roots), variable_count, prime
        )
        return {
            "variables": variable_count,
            "equations": equation_count,
            "prime": prime,
            "expected_branch_points": 2**equation_count / prime**GENUS_EXCESS,
            "distinct_rational_roots": len(roots),
            "generation_attempts": attempt,
            "macaulay_stabilization_degree": degree,
            "macaulay_profile_through_degree_six": profile,
        }
    raise AssertionError("failed to generate a finite nonempty panel")


def main():
    rng = Random(SEED)
    result = {
        "seed": SEED,
        "genus_excess_equations": GENUS_EXCESS,
        "model": "random products of two affine branch forms",
        "scope": (
            "Finite random control; stabilization means the truncated "
            "quotient dimension equals the exhaustively enumerated rational "
            "root count when stabilization is observed through degree six. "
            "No asymptotic solving-degree claim is made."
        ),
        "algorithm_claimed": False,
        "panels": [panel(variables, prime, rng) for variables, prime in PANELS],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
