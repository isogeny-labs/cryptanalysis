#!/usr/bin/env python3
"""Test standard displacement operators on structured residual tables."""

from collections import Counter
from itertools import product
import json
from random import Random

import binary_split_norm_control as split_control
from conjugate_hankel_quotient import (
    cofactor_kernel,
    independent_row_indices,
    matrix_add,
    matrix_multiply,
    matrix_vector,
    nullspace_basis,
)
from signed_hankel_minrank import evaluate, lagrange_weights, rank_mod
from structured_abscissa_search import FixedChoiceRandom, progression_candidates
from structured_tensor_width_search import geometric_candidates, hankel
from toy_jacobian import GenusTwo


PRIME = 101
GENUS = 2
SEED = 9_220_271


def residual_tables(panel, curve):
    """Return the two center-quotient residual truth tables."""
    prime = curve.p
    dimension = panel["projective_section_dimension"]
    b_degree = (dimension - 1) // 2
    c_degree = dimension // 2
    columns = b_degree + 1
    rows = panel["tail_slots"] - c_degree - 1
    xs = panel["split_abscissae"]
    weights = lagrange_weights(xs, prime)
    u = panel["target_u"]
    v = panel["target_v"]
    centers = []
    signed_parts = []
    for x, y in panel["selected_signed_points"]:
        inverse_u = pow(evaluate(u, x, prime), -1, prime)
        centers.append(-evaluate(v, x, prime) * inverse_u % prime)
        signed_parts.append(y * inverse_u % prime)

    center = hankel(centers, xs, weights, rows, columns, prime)
    assert rank_mod(center, prime) == GENUS
    quotient = nullspace_basis(
        list(map(list, zip(*center, strict=True))), prime
    )
    assert len(quotient) == columns - 1
    pivot_rows = independent_row_indices(center, GENUS, prime)
    tables = [[] for _ in pivot_rows]
    for bits in product((0, 1), repeat=len(xs)):
        values = [
            (1 if bit == 0 else -1) * value % prime
            for bit, value in zip(bits, signed_parts, strict=True)
        ]
        signed = hankel(values, xs, weights, rows, columns, prime)
        projected = matrix_multiply(quotient, signed, prime)
        assert rank_mod(projected, prime) == columns - 1
        kernel = cofactor_kernel(projected, prime)
        residual = matrix_vector(
            matrix_add(center, signed, prime), kernel, prime
        )
        for table, row_index in zip(tables, pivot_rows, strict=True):
            table.append(residual[row_index])
    return tables


def flatten(values, variables):
    """Use the natural balanced split of the truth-table bit positions."""
    row_positions = list(range(variables // 2))
    column_positions = list(range(variables // 2, variables))
    matrix = [
        [0] * (1 << len(column_positions))
        for _ in range(1 << len(row_positions))
    ]
    for index, value in enumerate(values):
        row = sum(
            ((index >> position) & 1) << cursor
            for cursor, position in enumerate(row_positions)
        )
        column = sum(
            ((index >> position) & 1) << cursor
            for cursor, position in enumerate(column_positions)
        )
        matrix[row][column] = value
    return matrix


def bit_reverse(value, bits):
    out = 0
    for _ in range(bits):
        out = (out << 1) | (value & 1)
        value >>= 1
    return out


def orders(size):
    bits = (size - 1).bit_length()
    return {
        "binary": list(range(size)),
        "gray": [index ^ (index >> 1) for index in range(size)],
        "bit_reverse": [bit_reverse(index, bits) for index in range(size)],
        "gray_bit_reverse": [
            bit_reverse(index ^ (index >> 1), bits)
            for index in range(size)
        ],
    }


def reorder(matrix, row_order, column_order):
    return [
        [matrix[row][column] for column in column_order]
        for row in row_order
    ]


def displacement(matrix, kind, cyclic, prime):
    """Apply standard Stein or Sylvester shift displacements."""
    row_count = len(matrix)
    column_count = len(matrix[0])

    def entry(row, column):
        if cyclic:
            return matrix[row % row_count][column % column_count]
        if 0 <= row < row_count and 0 <= column < column_count:
            return matrix[row][column]
        return 0

    out = [[0] * column_count for _ in range(row_count)]
    for row in range(row_count):
        for column in range(column_count):
            if kind == "stein_diagonal":
                value = entry(row, column) - entry(row - 1, column - 1)
            elif kind == "stein_antidiagonal":
                value = entry(row, column) - entry(row - 1, column + 1)
            elif kind == "sylvester_diagonal":
                value = entry(row - 1, column) - entry(row, column + 1)
            elif kind == "sylvester_antidiagonal":
                value = entry(row - 1, column) - entry(row, column - 1)
            else:
                raise ValueError(kind)
            out[row][column] = value % prime
    return out


KINDS = (
    "stein_diagonal",
    "stein_antidiagonal",
    "sylvester_diagonal",
    "sylvester_antidiagonal",
)


def table_profile(values, variables, prime):
    matrix = flatten(values, variables)
    row_orders = orders(len(matrix))
    column_orders = orders(len(matrix[0]))
    trials = []
    for row_name, row_order in row_orders.items():
        for column_name, column_order in column_orders.items():
            arranged = reorder(matrix, row_order, column_order)
            for kind in KINDS:
                for cyclic in (False, True):
                    rank = rank_mod(
                        displacement(arranged, kind, cyclic, prime), prime
                    )
                    trials.append({
                        "rank": rank,
                        "kind": kind,
                        "cyclic": cyclic,
                        "row_order": row_name,
                        "column_order": column_name,
                    })
    minimum = min(trial["rank"] for trial in trials)
    witnesses = [trial for trial in trials if trial["rank"] == minimum]
    return {
        "flattening_shape": [len(matrix), len(matrix[0])],
        "flattening_rank": rank_mod(matrix, prime),
        "minimum_displacement_rank": minimum,
        "minimum_witness_count": len(witnesses),
        "minimum_witnesses": witnesses[:4],
        "displacement_rank_histogram": {
            str(rank): count
            for rank, count in sorted(Counter(
                trial["rank"] for trial in trials
            ).items())
        },
    }


def make_panel(curve, variables, fibers, label):
    rng = FixedChoiceRandom(f"{SEED}/{label}", fibers)
    return split_control.build_panel(curve, variables, rng)


def analyze(panel, family, parameters, curve):
    variables = len(panel["split_abscissae"])
    profiles = [
        table_profile(table, variables, curve.p)
        for table in residual_tables(panel, curve)
    ]
    return {
        "family": family,
        "slots": variables,
        "parameters": parameters,
        "split_abscissae": panel["split_abscissae"],
        "minimum_displacement_rank": min(
            profile["minimum_displacement_rank"] for profile in profiles
        ),
        "profiles": profiles,
    }


def summarize(records):
    grouped = {}
    for record in records:
        key = f'{record["family"]}/{record["slots"]}'
        grouped.setdefault(key, Counter())[
            record["minimum_displacement_rank"]
        ] += 1
    return {
        key: {str(rank): count for rank, count in sorted(histogram.items())}
        for key, histogram in sorted(grouped.items())
    }


def main():
    curve = GenusTwo(PRIME)
    structured = []
    for length in (7, 8, 9):
        variables = length - GENUS
        for index, candidate in enumerate(progression_candidates(curve, length)):
            panel = make_panel(
                curve, variables, candidate["fibers"], f"ap/{length}/{index}"
            )
            structured.append(analyze(
                panel,
                "arithmetic_progression",
                {"offset": candidate["offset"], "step": candidate["step"]},
                curve,
            ))
        for index, candidate in enumerate(geometric_candidates(curve, length)):
            panel = make_panel(
                curve, variables, candidate["fibers"], f"gp/{length}/{index}"
            )
            structured.append(analyze(
                panel,
                "geometric_progression",
                {"scale": candidate["scale"], "ratio": candidate["ratio"]},
                curve,
            ))

    random_records = []
    for index, record in enumerate(structured):
        variables = record["slots"] - GENUS
        rng = Random(f"{SEED}/random/{variables}/{index}")
        panel = split_control.build_panel(curve, variables, rng)
        random_records.append(analyze(
            panel, "random", {"index": index}, curve
        ))

    result = {
        "prime": PRIME,
        "genus": GENUS,
        "seed": SEED,
        "operators": list(KINDS),
        "orderings": list(orders(8)),
        "structured_summary": summarize(structured),
        "random_summary": summarize(random_records),
        "structured_records": structured,
        "random_records": random_records,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
