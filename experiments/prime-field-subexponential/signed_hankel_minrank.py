#!/usr/bin/env python3
"""Verify the signed Hankel-MinRank formulation on split norm controls."""

from itertools import product
import json
from pathlib import Path

from toy_jacobian import GenusTwo


FIXTURE = Path(__file__).with_name("binary_split_norm_control.json")


def rank_mod(matrix, prime):
    rows = [[value % prime for value in row] for row in matrix]
    rank = 0
    columns = len(rows[0]) if rows else 0
    for column in range(columns):
        pivot = next(
            (i for i in range(rank, len(rows)) if rows[i][column]),
            None,
        )
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        inverse = pow(rows[rank][column], -1, prime)
        rows[rank] = [value * inverse % prime for value in rows[rank]]
        for i in range(len(rows)):
            if i == rank or rows[i][column] == 0:
                continue
            scale = rows[i][column]
            rows[i] = [
                (left - scale * right) % prime
                for left, right in zip(rows[i], rows[rank], strict=True)
            ]
        rank += 1
    return rank


def evaluate(polynomial, value, prime):
    out = 0
    for coefficient in reversed(polynomial):
        out = (out * value + coefficient) % prime
    return out


def lagrange_weights(abscissae, prime):
    weights = []
    for i, x in enumerate(abscissae):
        derivative = 1
        for j, other in enumerate(abscissae):
            if i != j:
                derivative = derivative * (x - other) % prime
        weights.append(pow(derivative, -1, prime))
    return weights


def hankel_matrix(panel, signs, prime, genus):
    r = panel["projective_section_dimension"]
    b_degree = (r - 1) // 2
    c_degree = r // 2
    columns = b_degree + 1
    rows = len(panel["split_abscissae"]) - c_degree - 1
    assert rows == columns + genus - 1
    xs = panel["split_abscissae"]
    selected_ys = [point[1] for point in panel["selected_signed_points"]]
    u = panel["target_u"]
    v = panel["target_v"]
    weights = lagrange_weights(xs, prime)
    multipliers = []
    for x, selected_y, sign in zip(xs, selected_ys, signs, strict=True):
        y = selected_y if sign == 1 else -selected_y % prime
        denominator = evaluate(u, x, prime)
        assert denominator
        multipliers.append(
            (y - evaluate(v, x, prime))
            * pow(denominator, -1, prime)
            % prime
        )
    moments = []
    for exponent in range(rows + columns - 1):
        moments.append(
            sum(
                multiplier * weight * pow(x, exponent, prime)
                for x, multiplier, weight in zip(
                    xs, multipliers, weights, strict=True
                )
            )
            % prime
        )
    return [
        [moments[row + column] for column in range(columns)]
        for row in range(rows)
    ]


def main():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    prime = fixture["prime"]
    genus = fixture["genus"]
    curve = GenusTwo(prime)
    assert tuple(fixture["curve_coefficients"]) == curve.coefficients
    panels = []
    for panel in fixture["panels"]:
        arity = panel["tail_slots"]
        deficient = []
        full_rank = (panel["projective_section_dimension"] - 1) // 2 + 1
        for bits in product((1, -1), repeat=arity):
            matrix = hankel_matrix(panel, bits, prime, genus)
            rank = rank_mod(matrix, prime)
            if rank < full_rank:
                deficient.append({"signs": bits, "rank": rank})
        assert deficient
        assert tuple(deficient[0]["signs"]) == (1,) * arity
        panels.append({
            "projective_section_dimension":
                panel["projective_section_dimension"],
            "tail_slots": arity,
            "hankel_rows": len(
                hankel_matrix(panel, (1,) * arity, prime, genus)
            ),
            "hankel_columns": full_rank,
            "sign_assignments": 2**arity,
            "rank_deficient_assignments": len(deficient),
            "deficient_records": deficient,
            "planted_assignment_rank": deficient[0]["rank"],
            "equivalence_to_split_norm_verified": len(deficient) == 1,
        })
    result = {
        "prime": prime,
        "genus": genus,
        "panels": panels,
        "all_panels_have_unique_rank_deficient_sign_assignment": all(
            panel["equivalence_to_split_norm_verified"] for panel in panels
        ),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
