#!/usr/bin/env python3
"""Verify scalar-orbit inflation in the two-line evaluation-code view."""

import json
from pathlib import Path

from multisection_span_control import section_basis
from toy_jacobian import GenusTwo


FIXTURE = Path(__file__).with_name("binary_split_norm_control.json")


def rank_mod(matrix, prime):
    rows = [[value % prime for value in row] for row in matrix]
    rank = 0
    for column in range(len(rows[0]) if rows else 0):
        pivot = next(
            (index for index in range(rank, len(rows)) if rows[index][column]),
            None,
        )
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        inverse = pow(rows[rank][column], -1, prime)
        rows[rank] = [value * inverse % prime for value in rows[rank]]
        for index in range(len(rows)):
            if index == rank or not rows[index][column]:
                continue
            scale = rows[index][column]
            rows[index] = [
                (left - scale * right) % prime
                for left, right in zip(rows[index], rows[rank], strict=True)
            ]
        rank += 1
    return rank


def evaluate(polynomial, value, prime):
    out = 0
    for coefficient in reversed(polynomial):
        out = (out * value + coefficient) % prime
    return out


def main():
    fixture = json.loads(FIXTURE.read_text())
    prime = fixture["prime"]
    curve = GenusTwo(prime)
    panels = []
    for panel in fixture["panels"]:
        r = panel["projective_section_dimension"]
        fixed = (r - 1) // 2 if r % 2 else r
        homogeneous = list(panel["planted_parameters"])
        homogeneous.insert(fixed, 1)
        basis = section_basis(
            curve.poly,
            tuple(panel["target_u"]),
            tuple(panel["target_v"]),
            r,
        )
        evaluations = []
        for x, y in panel["selected_signed_points"]:
            evaluations.append([
                (
                    evaluate(basis_b, x, prime) * y
                    - evaluate(basis_a, x, prime)
                ) % prime
                for basis_b, basis_a in basis
            ])
        assert all(
            sum(left * right for left, right in zip(row, homogeneous, strict=True))
            % prime
            == 0
            for row in evaluations
        )
        rank = rank_mod(evaluations, prime)
        nullity = len(homogeneous) - rank
        assert nullity == 1
        affine_solutions = prime**nullity
        panels.append({
            "projective_section_dimension": r,
            "tail_slots": panel["tail_slots"],
            "homogeneous_coefficients": len(homogeneous),
            "selected_branch_evaluation_rank": rank,
            "selected_branch_nullity": nullity,
            "affine_codewords_including_zero": affine_solutions,
            "nonzero_affine_codewords": affine_solutions - 1,
            "projective_solution_orbits": (affine_solutions - 1) // (prime - 1),
            "scalar_orbit_inflation": prime - 1,
        })
    result = {
        "prime": prime,
        "genus": fixture["genus"],
        "panels": panels,
        "all_selected_branch_kernels_are_one_dimensional": all(
            panel["selected_branch_nullity"] == 1 for panel in panels
        ),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
