#!/usr/bin/env python3
"""Verify the self-adjoint interpolation-projection flip formulation."""

from itertools import product
import json
from pathlib import Path
from random import Random

from binary_split_norm_control import product_from_roots
from multisection_span_control import section_basis
from paired_arrangement_mobius import candidate_rows
from paired_span_state_control import SEED, extended_panel
from signed_hankel_minrank import rank_mod
from toy_jacobian import GenusTwo


PRIME = 101


def matrix_multiply(left, right, prime):
    return [
        [
            sum(a * b for a, b in zip(row, column, strict=True)) % prime
            for column in zip(*right, strict=True)
        ]
        for row in left
    ]


def matrix_inverse(matrix, prime):
    size = len(matrix)
    rows = [
        [value % prime for value in row]
        + [int(index == column) for column in range(size)]
        for index, row in enumerate(matrix)
    ]
    for column in range(size):
        pivot = next(
            index for index in range(column, size) if rows[index][column]
        )
        rows[column], rows[pivot] = rows[pivot], rows[column]
        inverse = pow(rows[column][column], -1, prime)
        rows[column] = [value * inverse % prime for value in rows[column]]
        for index in range(size):
            if index == column or not rows[index][column]:
                continue
            scale = rows[index][column]
            rows[index] = [
                (left - scale * right) % prime
                for left, right in zip(rows[index], rows[column], strict=True)
            ]
    return [row[size:] for row in rows]


def determinant(matrix, prime):
    rows = [[value % prime for value in row] for row in matrix]
    result = 1
    for column in range(len(rows)):
        pivot = next(
            (index for index in range(column, len(rows)) if rows[index][column]),
            None,
        )
        if pivot is None:
            return 0
        if pivot != column:
            rows[column], rows[pivot] = rows[pivot], rows[column]
            result = -result
        value = rows[column][column]
        result = result * value % prime
        inverse = pow(value, -1, prime)
        for index in range(column + 1, len(rows)):
            if not rows[index][column]:
                continue
            scale = rows[index][column] * inverse % prime
            rows[index] = [
                (left - scale * right) % prime
                for left, right in zip(rows[index], rows[column], strict=True)
            ]
    return result % prime


def diagonal_left(values, matrix, prime):
    return [
        [value * entry % prime for entry in row]
        for value, row in zip(values, matrix, strict=True)
    ]


def add_identity(matrix, prime):
    return [
        [
            (value + int(row == column)) % prime
            for column, value in enumerate(values)
        ]
        for row, values in enumerate(matrix)
    ]


def principal(matrix, selected):
    selected = tuple(selected)
    return [[matrix[row][column] for column in selected] for row in selected]


def derivative(poly, polynomial):
    return poly.canonical(
        degree * value for degree, value in enumerate(polynomial) if degree
    )


def symmetric_under(weights, matrix, prime):
    return all(
        weights[row] * matrix[row][column] % prime
        == weights[column] * matrix[column][row] % prime
        for row in range(len(matrix))
        for column in range(len(matrix))
    )


def analyze(curve, panel):
    prime = curve.p
    dimension = panel["projective_section_dimension"]
    size = dimension + 1
    xs = panel["split_abscissae"][:size]
    reduced_panel = dict(panel)
    reduced_panel["split_abscissae"] = xs
    rows = candidate_rows(curve, reduced_panel)
    base = [rows[2 * index] for index in range(size)]
    alternate = [rows[2 * index + 1] for index in range(size)]
    assert rank_mod(base, prime) == size
    base_inverse = matrix_inverse(base, prime)
    differences = [
        [(right - left) % prime for left, right in zip(first, second, strict=True)]
        for first, second in zip(base, alternate, strict=True)
    ]
    flip_matrix = matrix_multiply(differences, base_inverse, prime)

    b_columns = (dimension - 1) // 2 + 1
    coordinate_projection = [
        [int(row == column and row < b_columns) for column in range(size)]
        for row in range(size)
    ]
    projection = matrix_multiply(
        matrix_multiply(base, coordinate_projection, prime),
        base_inverse,
        prime,
    )
    assert matrix_multiply(projection, projection, prime) == projection
    assert rank_mod(projection, prime) == b_columns

    root_polynomial = product_from_roots(curve.poly, xs)
    root_derivative = derivative(curve.poly, root_polynomial)
    u = panel["target_u"]
    v = panel["target_v"]
    flip_scales = []
    projection_weights = []
    flip_weights = []
    for index, x in enumerate(xs):
        y = curve.roots(x)[0]
        y_minus_v = (y - curve.poly.evaluate(v, x)) % prime
        assert y and y_minus_v
        u_value = curve.poly.evaluate(u, x)
        derivative_value = curve.poly.evaluate(root_derivative, x)
        assert u_value and derivative_value
        flip_scales.append(-2 * y * pow(y_minus_v, -1, prime) % prime)
        projection_weights.append(pow(
            u_value * y_minus_v * derivative_value % prime, -1, prime
        ))
        flip_weights.append(pow(
            y * u_value * derivative_value % prime, -1, prime
        ))

    assert diagonal_left(flip_scales, projection, prime) == flip_matrix
    assert symmetric_under(projection_weights, projection, prime)
    assert symmetric_under(flip_weights, flip_matrix, prime)

    base_determinant = determinant(base, prime)
    deficient = 0
    for bits in product((0, 1), repeat=size):
        selected_matrix = [
            (alternate if bit else base)[index]
            for index, bit in enumerate(bits)
        ]
        direct = determinant(selected_matrix, prime)
        update = diagonal_left(bits, flip_matrix, prime)
        lemma = base_determinant * determinant(
            add_identity(update, prime), prime
        ) % prime
        selected = [index for index, bit in enumerate(bits) if bit]
        principal_value = determinant(
            add_identity(principal(flip_matrix, selected), prime), prime
        ) if selected else 1
        assert direct == lemma == base_determinant * principal_value % prime
        deficient += direct == 0

    return {
        "projective_section_dimension": dimension,
        "square_slots": size,
        "b_block_rank": b_columns,
        "projection_is_idempotent": True,
        "projection_has_expected_rank": True,
        "flip_is_diagonal_scaled_projection": True,
        "projection_is_residue_diagonally_self_adjoint": True,
        "flip_is_residue_diagonally_self_adjoint": True,
        "all_principal_minor_identities_verified": True,
        "sign_assignments": 1 << size,
        "deficient_assignments": deficient,
    }


def main():
    source = json.loads(
        Path(__file__).with_name("binary_split_norm_control.json").read_text()
    )
    curve = GenusTwo(PRIME)
    result = {
        "prime": PRIME,
        "genus": 2,
        "sources": [
            "binary_split_norm_control.json",
            "extended planted divisors from paired_span_state_control.py",
        ],
        "panels": [analyze(curve, panel) for panel in source["panels"]],
    }
    rng = Random(SEED)
    for dimension in range(8, 11):
        panel, _, _ = extended_panel(curve, dimension, rng)
        result["panels"].append(analyze(curve, panel))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
