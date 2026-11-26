#!/usr/bin/env python3
"""Macaulay profiles for transverse multi-planted binary branch systems."""

import json
from random import Random

from high_density_branch_regular import (
    GENUS_EXCESS,
    evaluate_form,
    multiply_forms,
    roots_are_transverse,
    roots_of_branch_system,
    stabilization_profile,
)


PRIME = 101
SEED = 90_117
PANELS = (
    (4, 1),
    (4, 4),
    (4, 6),
    (5, 1),
    (5, 5),
    (5, 8),
    (6, 1),
    (6, 6),
    (6, 10),
)


def nullspace_basis(rows, columns, prime):
    work = [[value % prime for value in row] for row in rows]
    rank = 0
    pivots = []
    for column in range(columns):
        pivot = next(
            (i for i in range(rank, len(work)) if work[i][column]), None
        )
        if pivot is None:
            continue
        work[rank], work[pivot] = work[pivot], work[rank]
        inverse = pow(work[rank][column], -1, prime)
        work[rank] = [value * inverse % prime for value in work[rank]]
        for i in range(len(work)):
            if i == rank or not work[i][column]:
                continue
            scale = work[i][column]
            work[i] = [
                (left - scale * right) % prime
                for left, right in zip(work[i], work[rank], strict=True)
            ]
        pivots.append(column)
        rank += 1
    free = [column for column in range(columns) if column not in pivots]
    basis = []
    for free_column in free:
        vector = [0] * columns
        vector[free_column] = 1
        for row, pivot_column in reversed(
            list(zip(work[:rank], pivots, strict=True))
        ):
            vector[pivot_column] = -sum(
                row[column] * vector[column] for column in free
            ) % prime
        basis.append(vector)
    return basis


def form_through(points, variable_count, rng):
    rows = [[1, *point] for point in points]
    basis = nullspace_basis(rows, variable_count + 1, PRIME)
    if not basis:
        return None
    for _ in range(100):
        coefficients = [rng.randrange(PRIME) for _ in basis]
        if not any(coefficients):
            continue
        form = [
            sum(
                coefficient * vector[index]
                for coefficient, vector in zip(
                    coefficients, basis, strict=True
                )
            ) % PRIME
            for index in range(variable_count + 1)
        ]
        if any(form[1:]):
            return form
    return None


def branches_with_plants(plants, variable_count, rng):
    equation_count = variable_count + GENUS_EXCESS
    branches = []
    for _ in range(equation_count):
        for _ in range(1000):
            choices = [rng.randrange(2) for _ in plants]
            groups = [
                [point for point, choice in zip(plants, choices) if choice == side]
                for side in (0, 1)
            ]
            if any(len(group) > variable_count for group in groups):
                continue
            forms = [
                form_through(group, variable_count, rng) for group in groups
            ]
            if any(form is None for form in forms):
                continue
            if all(
                evaluate_form(forms[1 - choice], point, PRIME) != 0
                for point, choice in zip(plants, choices, strict=True)
            ):
                branches.append(tuple(forms))
                break
        else:
            return None
    return branches


def panel(variable_count, planted_count, rng):
    for attempt in range(1, 1001):
        plants = {
            tuple(rng.randrange(PRIME) for _ in range(variable_count))
            for _ in range(planted_count)
        }
        if len(plants) != planted_count:
            continue
        plants = tuple(sorted(plants))
        branches = branches_with_plants(plants, variable_count, rng)
        if branches is None:
            continue
        roots = roots_of_branch_system(branches, variable_count, PRIME)
        if roots is None or not set(plants).issubset(roots):
            continue
        if not roots_are_transverse(branches, roots, PRIME):
            continue
        equations = [
            multiply_forms(left, right, PRIME) for left, right in branches
        ]
        degree, profile = stabilization_profile(
            equations, len(roots), variable_count, PRIME
        )
        return {
            "variables": variable_count,
            "equations": len(branches),
            "requested_planted_roots": planted_count,
            "distinct_rational_roots": len(roots),
            "unintended_extra_roots": len(roots) - planted_count,
            "generation_attempts": attempt,
            "macaulay_stabilization_degree": degree,
            "macaulay_profile_through_degree_six": profile,
        }
    raise AssertionError("failed to construct transverse multi-planted panel")


def main():
    rng = Random(SEED)
    print(
        json.dumps(
            {
                "prime": PRIME,
                "seed": SEED,
                "genus_excess_equations": GENUS_EXCESS,
                "model": "transverse multi-planted products of two affine forms",
                "scope": (
                    "Finite algebraic control. Multiple roots are planted by "
                    "hyperplanes through prescribed points; every branch "
                    "assignment is exhaustively checked. No asymptotic "
                    "solving-degree claim is made."
                ),
                "algorithm_claimed": False,
                "panels": [
                    panel(variables, roots, rng) for variables, roots in PANELS
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
