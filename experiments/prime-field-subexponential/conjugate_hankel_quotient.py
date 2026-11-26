#!/usr/bin/env python3
"""Test the fixed-rank center in the conjugate signed-Hankel system."""

from collections import Counter
from itertools import combinations, product
import json
from pathlib import Path

from signed_hankel_minrank import evaluate, lagrange_weights, rank_mod
from toy_jacobian import GenusTwo


FIXTURE = Path(__file__).with_name("binary_split_norm_control.json")


def nullspace_basis(matrix, prime):
    rows = [[value % prime for value in row] for row in matrix]
    columns = len(rows[0]) if rows else 0
    pivots = []
    rank = 0
    for column in range(columns):
        pivot = next(
            (index for index in range(rank, len(rows))
             if rows[index][column]),
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
        pivots.append(column)
        rank += 1
    free = [column for column in range(columns) if column not in pivots]
    basis = []
    for free_column in free:
        vector = [0] * columns
        vector[free_column] = 1
        for row_index, pivot_column in reversed(list(enumerate(pivots))):
            vector[pivot_column] = -sum(
                rows[row_index][other] * vector[other]
                for other in free
            ) % prime
        basis.append(vector)
    return basis


def matrix_add(left, right, prime):
    return [
        [(a + b) % prime for a, b in zip(lrow, rrow, strict=True)]
        for lrow, rrow in zip(left, right, strict=True)
    ]


def matrix_vector(matrix, vector, prime):
    return [
        sum(a * b for a, b in zip(row, vector, strict=True)) % prime
        for row in matrix
    ]


def matrix_multiply(left, right, prime):
    columns = list(zip(*right, strict=True))
    return [
        [
            sum(a * b for a, b in zip(row, column, strict=True)) % prime
            for column in columns
        ]
        for row in left
    ]


def determinant(matrix, prime):
    rows = [[value % prime for value in row] for row in matrix]
    result = 1
    for column in range(len(rows)):
        pivot = next(
            (index for index in range(column, len(rows))
             if rows[index][column]),
            None,
        )
        if pivot is None:
            return 0
        if pivot != column:
            rows[column], rows[pivot] = rows[pivot], rows[column]
            result = -result
        pivot_value = rows[column][column]
        result = result * pivot_value % prime
        inverse = pow(pivot_value, -1, prime)
        for index in range(column + 1, len(rows)):
            scale = rows[index][column] * inverse % prime
            for cursor in range(column, len(rows)):
                rows[index][cursor] = (
                    rows[index][cursor] - scale * rows[column][cursor]
                ) % prime
    return result % prime


def cofactor_kernel(matrix, prime):
    columns = len(matrix[0])
    assert len(matrix) == columns - 1
    return [
        ((-1) ** column) * determinant(
            [row[:column] + row[column + 1:] for row in matrix],
            prime,
        ) % prime
        for column in range(columns)
    ]


def independent_row_indices(matrix, count, prime):
    selected = []
    current = []
    for index, row in enumerate(matrix):
        if rank_mod(current + [row], prime) > len(current):
            selected.append(index)
            current.append(row)
            if len(selected) == count:
                break
    assert len(selected) == count
    return selected


def multilinear_profile(values, variables, prime):
    coefficients = list(values)
    for bit in range(variables):
        step = 1 << bit
        for mask in range(1 << variables):
            if mask & step:
                coefficients[mask] = (
                    coefficients[mask] - coefficients[mask ^ step]
                ) % prime
    support = [mask for mask, value in enumerate(coefficients) if value]
    histogram = Counter(mask.bit_count() for mask in support)
    cut_ranks = []
    for prefix_variables in range(1, variables):
        suffix_size = 1 << (variables - prefix_variables)
        flattening = [
            values[start:start + suffix_size]
            for start in range(0, len(values), suffix_size)
        ]
        cut_ranks.append(rank_mod(flattening, prime))
    balanced_rank_histogram = Counter()
    balanced_size = variables // 2
    for selected in combinations(range(variables), balanced_size):
        selected = set(selected)
        row_positions = sorted(selected)
        column_positions = [
            position for position in range(variables)
            if position not in selected
        ]
        flattening = [
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
            flattening[row][column] = value
        balanced_rank_histogram[rank_mod(flattening, prime)] += 1
    return {
        "support": len(support),
        "degree": max(histogram, default=-1),
        "degree_histogram": {
            str(degree): count for degree, count in sorted(histogram.items())
        },
        "truth_table_cut_ranks": cut_ranks,
        "maximum_truth_table_cut_rank": max(cut_ranks, default=1),
        "balanced_cut_rank_histogram": {
            str(rank): count
            for rank, count in sorted(balanced_rank_histogram.items())
        },
        "minimum_balanced_cut_rank": min(
            balanced_rank_histogram, default=1
        ),
        "maximum_balanced_cut_rank": max(
            balanced_rank_histogram, default=1
        ),
    }


def hankel(values, xs, weights, rows, columns, prime):
    moments = [
        sum(
            value * weight * pow(x, exponent, prime)
            for value, x, weight in zip(values, xs, weights, strict=True)
        ) % prime
        for exponent in range(rows + columns - 1)
    ]
    return (
        [
            [moments[row + column] for column in range(columns)]
            for row in range(rows)
        ],
        moments,
    )


def main():
    fixture = json.loads(FIXTURE.read_text())
    prime = fixture["prime"]
    genus = fixture["genus"]
    curve = GenusTwo(prime)
    panels = []
    for panel in fixture["panels"]:
        r = panel["projective_section_dimension"]
        b_degree = (r - 1) // 2
        c_degree = r // 2
        columns = b_degree + 1
        rows = panel["tail_slots"] - c_degree - 1
        assert rows == columns + genus - 1
        xs = panel["split_abscissae"]
        weights = lagrange_weights(xs, prime)
        u = panel["target_u"]
        v = panel["target_v"]
        f = curve.coefficients
        centers = []
        signed_parts = []
        quadratic_checks = []
        for x, y in panel["selected_signed_points"]:
            u_value = evaluate(u, x, prime)
            v_value = evaluate(v, x, prime)
            f_value = evaluate(f, x, prime)
            inverse_u = pow(u_value, -1, prime)
            center = -v_value * inverse_u % prime
            signed = y * inverse_u % prime
            w_value = (f_value - v_value * v_value) * inverse_u % prime
            for branch in (center + signed, center - signed):
                branch %= prime
                quadratic_checks.append(
                    (
                        u_value * branch * branch
                        + 2 * v_value * branch
                        - w_value
                    ) % prime
                )
            centers.append(center)
            signed_parts.append(signed)
        assert not any(quadratic_checks)

        center_matrix, center_moments = hankel(
            centers, xs, weights, rows, columns, prime
        )
        signed_matrix, _ = hankel(
            signed_parts, xs, weights, rows, columns, prime
        )
        planted_matrix = matrix_add(center_matrix, signed_matrix, prime)
        center_rank = rank_mod(center_matrix, prime)
        planted_rank = rank_mod(planted_matrix, prime)
        assert center_rank <= genus
        assert planted_rank < columns

        recurrence_checks = []
        for exponent in range(max(0, 2 * b_degree)):
            recurrence_checks.append(
                sum(
                    coefficient * center_moments[exponent + degree]
                    for degree, coefficient in enumerate(u)
                ) % prime
            )
        assert not any(recurrence_checks)

        quotient = nullspace_basis(
            list(map(list, zip(*center_matrix, strict=True))),
            prime,
        )
        assert len(quotient) == rows - center_rank
        projected_rank_histogram = Counter()
        residual_zero_signings = 0
        residual_tables = []
        quotient_reduction_applies = (
            center_rank == genus and columns > genus
        )
        if quotient_reduction_applies:
            assert len(quotient) == columns - 1
            pivot_rows = independent_row_indices(
                center_matrix, genus, prime
            )
            residual_tables = [[] for _ in pivot_rows]
            for bits in product((0, 1), repeat=len(xs)):
                signs = tuple(1 if bit == 0 else -1 for bit in bits)
                values = [
                    sign * value % prime
                    for sign, value in zip(signs, signed_parts, strict=True)
                ]
                signed, _ = hankel(
                    values, xs, weights, rows, columns, prime
                )
                projected = matrix_multiply(quotient, signed, prime)
                projected_rank = rank_mod(projected, prime)
                projected_rank_histogram[projected_rank] += 1
                assert projected_rank == columns - 1
                kernel = cofactor_kernel(projected, prime)
                assert any(kernel)
                total = matrix_add(center_matrix, signed, prime)
                residual = matrix_vector(total, kernel, prime)
                for table, row_index in zip(
                    residual_tables, pivot_rows, strict=True
                ):
                    table.append(residual[row_index])
                if not any(residual):
                    residual_zero_signings += 1
            assert residual_zero_signings == 1

        panels.append({
            "projective_section_dimension": r,
            "tail_slots": len(xs),
            "hankel_rows": rows,
            "hankel_columns": columns,
            "center_rank": center_rank,
            "center_rank_bound": genus,
            "planted_total_rank": planted_rank,
            "center_recurrence_checks": len(recurrence_checks),
            "all_center_recurrences_zero": not any(recurrence_checks),
            "all_local_quadratics_zero": not any(quadratic_checks),
            "quotient_reduction_applies": quotient_reduction_applies,
            "quotient_rows": len(quotient),
            "projected_rank_histogram": {
                str(rank): count
                for rank, count in sorted(projected_rank_histogram.items())
            },
            "residual_multilinear_profiles": [
                multilinear_profile(table, len(xs), prime)
                for table in residual_tables
            ],
            "residual_zero_signings": residual_zero_signings,
        })

    result = {
        "prime": prime,
        "genus": genus,
        "panels": panels,
        "all_center_ranks_at_most_genus": all(
            panel["center_rank"] <= genus for panel in panels
        ),
        "all_applicable_quotients_retain_unique_signing": all(
            not panel["quotient_reduction_applies"]
            or panel["residual_zero_signings"] == 1
            for panel in panels
        ),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
