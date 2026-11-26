#!/usr/bin/env python3
"""Verify the paired hyperplane-transversal view on exact split panels."""

from itertools import product
import json
from math import comb
from pathlib import Path

from binary_split_norm_control import null_vector
from multisection_span_control import section_basis
from projective_scaling_control import evaluate, rank_mod
from toy_jacobian import GenusTwo


FIXTURE = Path(__file__).with_name("binary_split_norm_control.json")


def normalize_projective(vector, prime):
    pivot = next(value for value in vector if value % prime)
    inverse = pow(pivot % prime, -1, prime)
    return tuple(value * inverse % prime for value in vector)


def dot(row, vector, prime):
    return sum(
        left * right for left, right in zip(row, vector, strict=True)
    ) % prime


def main():
    fixture = json.loads(FIXTURE.read_text())
    prime = fixture["prime"]
    genus = fixture["genus"]
    curve = GenusTwo(prime)
    panels = []
    for panel in fixture["panels"]:
        r = panel["projective_section_dimension"]
        dimension = r + 1
        basis = section_basis(
            curve.poly,
            tuple(panel["target_u"]),
            tuple(panel["target_v"]),
            r,
        )
        row_pairs = []
        for x, planted_y in panel["selected_signed_points"]:
            other_y = next(y for y in curve.roots(x) if y != planted_y)
            pair = []
            for y in (planted_y, other_y):
                pair.append([
                    (
                        evaluate(basis_b, x, prime) * y
                        - evaluate(basis_a, x, prime)
                    ) % prime
                    for basis_b, basis_a in basis
                ])
            row_pairs.append(pair)

        deficient = []
        projective_solutions = set()
        for choices in product((0, 1), repeat=len(row_pairs)):
            selected = [
                row_pairs[index][choice]
                for index, choice in enumerate(choices)
            ]
            rank = rank_mod(selected, prime)
            if rank == dimension:
                continue
            kernel = null_vector(selected, prime)
            assert kernel is not None
            normalized = normalize_projective(kernel, prime)
            assert all(
                dot(row_pairs[index][choice], normalized, prime) == 0
                for index, choice in enumerate(choices)
            )
            assert all(
                dot(pair[0], normalized, prime) == 0
                or dot(pair[1], normalized, prime) == 0
                for pair in row_pairs
            )
            projective_solutions.add(normalized)
            deficient.append({
                "choices": choices,
                "rank": rank,
                "normalized_kernel": normalized,
            })

        assert deficient
        assert deficient[0]["choices"] == (0,) * len(row_pairs)
        panels.append({
            "projective_section_dimension": r,
            "homogeneous_dimension": dimension,
            "row_pairs": len(row_pairs),
            "row_excess": len(row_pairs) - dimension,
            "sign_assignments": 2 ** len(row_pairs),
            "full_size_minors": comb(len(row_pairs), dimension),
            "rank_deficient_assignments": len(deficient),
            "distinct_projective_kernels": len(projective_solutions),
            "nonzero_affine_representatives_per_kernel": prime - 1,
            "planted_assignment_is_unique": len(deficient) == 1,
            "projective_kernel_is_unique": len(projective_solutions) == 1,
        })

    result = {
        "prime": prime,
        "genus": genus,
        "panels": panels,
        "all_row_excesses_equal_genus_minus_one": all(
            panel["row_excess"] == genus - 1 for panel in panels
        ),
        "all_panels_have_one_signing_and_one_projective_kernel": all(
            panel["planted_assignment_is_unique"]
            and panel["projective_kernel_is_unique"]
            for panel in panels
        ),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
