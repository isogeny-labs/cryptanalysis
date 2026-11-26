#!/usr/bin/env python3
"""Build norm systems from actual split signed fibers and measure certificates."""

import json
from random import Random

from sympy import Integer, Poly, symbols

from binary_graeffe_macaulay import certificate_panel
from multisection_span_control import section_basis
from toy_jacobian import GenusTwo


PRIME = 101
SEED = 99


def null_vector(matrix, prime):
    rows = [row[:] for row in matrix]
    row_count = len(rows)
    columns = len(rows[0])
    pivots = []
    rank = 0
    for column in range(columns):
        pivot = next(
            (i for i in range(rank, row_count) if rows[i][column] % prime),
            None,
        )
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        inverse = pow(rows[rank][column] % prime, -1, prime)
        rows[rank] = [value * inverse % prime for value in rows[rank]]
        for i in range(row_count):
            if i == rank or rows[i][column] % prime == 0:
                continue
            scale = rows[i][column] % prime
            rows[i] = [
                (left - scale * right) % prime
                for left, right in zip(rows[i], rows[rank], strict=True)
            ]
        pivots.append(column)
        rank += 1
        if rank == row_count:
            break
    free = [column for column in range(columns) if column not in pivots]
    if len(free) != 1:
        return None
    result = [0] * columns
    result[free[0]] = 1
    for i, column in reversed(list(enumerate(pivots))):
        result[column] = -sum(
            rows[i][other] * result[other] for other in free
        ) % prime
    return result


def product_from_roots(poly, roots):
    result = (1,)
    for root in roots:
        result = poly.mul(result, (-root % poly.p, 1))
    return result


def build_panel(curve, r, rng):
    poly = curve.poly
    genus = 2
    tail_slots = genus + r
    fixed = (r - 1) // 2 if r % 2 else r
    split = [
        (x, curve.roots(x))
        for x in range(curve.p)
        if len(curve.roots(x)) == 2
    ]
    for attempt in range(1_000):
        chosen = rng.sample(split, tail_slots)
        points = [(x, roots[rng.randrange(2)]) for x, roots in chosen]
        total = curve.identity
        for x, y in points:
            total = curve.add(total, curve.point_divisor(x, y))
        u, v = curve.neg(total)
        if len(u) != genus + 1:
            continue
        if any(poly.evaluate(u, x) == 0 for x, _ in points):
            continue
        w = poly.exact_quotient(
            poly.sub(curve.coefficients, poly.mul(v, v)),
            u,
        )
        basis = section_basis(poly, u, v, r)
        evaluations = [
            [
                (
                    poly.evaluate(basis_b, x) * y
                    - poly.evaluate(basis_a, x)
                ) % curve.p
                for basis_b, basis_a in basis
            ]
            for x, y in points
        ]
        homogeneous = null_vector(evaluations, curve.p)
        if homogeneous is None or homogeneous[fixed] == 0:
            continue
        inverse = pow(homogeneous[fixed], -1, curve.p)
        homogeneous = [value * inverse % curve.p for value in homogeneous]

        variables = symbols(f"z0:{r}")
        parameters = []
        cursor = 0
        planted = []
        for index in range(r + 1):
            if index == fixed:
                parameters.append(Integer(1))
            else:
                parameters.append(variables[cursor])
                planted.append(homogeneous[index])
                cursor += 1

        coefficients = [Integer(0)] * (tail_slots + 1)
        for i, (bi, ai) in enumerate(basis):
            for j, (bj, aj) in enumerate(basis):
                numerator = poly.sub(
                    poly.mul(poly.mul(bi, bj), curve.coefficients),
                    poly.mul(ai, aj),
                )
                quotient = poly.exact_quotient(numerator, u)
                for degree, value in enumerate(quotient):
                    coefficients[degree] += (
                        parameters[i] * parameters[j] * value
                    )
        leading = int(coefficients[tail_slots]) % curve.p
        assert leading in (1, curve.p - 1)
        if leading == curve.p - 1:
            coefficients = [-value for value in coefficients]

        roots = tuple(x for x, _ in points)
        expected = product_from_roots(poly, roots)
        substitution = dict(zip(variables, planted, strict=True))
        evaluated = tuple(
            int(coefficient.subs(substitution)) % curve.p
            for coefficient in coefficients
        )
        if evaluated != expected:
            continue
        equations = [
            Poly(coefficients[i] - expected[i], *variables, modulus=curve.p)
            for i in range(tail_slots)
        ]
        item = {
            "projective_section_dimension": r,
            "tail_slots": tail_slots,
            "variables": r,
            "equations": len(equations),
            "input_degrees": [
                equation.total_degree() for equation in equations
            ],
            "split_abscissae": roots,
            "selected_signed_points": points,
            "target_u": u,
            "target_v": v,
            "planted_parameters": planted,
            "construction_attempts": attempt + 1,
            "norm_splits_completely": True,
        }
        item.update(
            certificate_panel(
                equations, planted, variables, curve.p, limit=12
            )
        )
        return item
    raise AssertionError("failed to construct a split planted panel")


def main():
    curve = GenusTwo(PRIME)
    rng = Random(SEED)
    result = {
        "prime": PRIME,
        "genus": 2,
        "seed": SEED,
        "curve_coefficients": curve.coefficients,
        "panels": [build_panel(curve, r, rng) for r in range(1, 8)],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
