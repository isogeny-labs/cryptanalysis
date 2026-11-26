#!/usr/bin/env python3
"""Rank control for affine-linear interpolation on Cartesian branch lists."""

import json
from itertools import product

from toy_jacobian import GenusTwo


PRIME = 101
FOLDING = 3
BLOCK_STARTS = (3, 29, 43, 49)
GAMMA = 2


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


def constraint_matrix(curve, degree_bound):
    rows = []
    for start in BLOCK_STARTS:
        branch_pairs = [
            curve.roots(start * pow(GAMMA, offset, PRIME) % PRIME)
            for offset in range(FOLDING)
        ]
        assert all(len(pair) == 2 for pair in branch_pairs)
        for values in product(*branch_pairs):
            row = []
            for symbol in (1, *values):
                row.extend(
                    symbol * pow(start, degree, PRIME) % PRIME
                    for degree in range(degree_bound + 1)
                )
            rows.append(row)
    return rows


def main():
    curve = GenusTwo(PRIME)
    panels = []
    for degree_bound in range(0, len(BLOCK_STARTS) + 3):
        matrix = constraint_matrix(curve, degree_bound)
        columns = (FOLDING + 1) * (degree_bound + 1)
        rank = rank_mod(matrix, PRIME)
        expected_rank = (FOLDING + 1) * min(
            len(BLOCK_STARTS), degree_bound + 1
        )
        panels.append({
            "coefficient_degree_bound": degree_bound,
            "constraints": len(matrix),
            "columns": columns,
            "rank": rank,
            "nullity": columns - rank,
            "expected_cartesian_rank": expected_rank,
            "all_symbol_coefficients_forced_to_vanish_at_block_starts": (
                rank == expected_rank
            ),
        })
    result = {
        "prime": PRIME,
        "genus": 2,
        "folding": FOLDING,
        "block_starts": BLOCK_STARTS,
        "cartesian_tuples_per_block": 2**FOLDING,
        "interpolant": "Q0(X)+sum_j Qj(X)Yj",
        "panels": panels,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
