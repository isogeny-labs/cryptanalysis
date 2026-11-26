#!/usr/bin/env python3
"""Exhaust the modular-square-root/rational-reconstruction formulation.

For each signed split-fiber panel, every sign assignment prescribes a square
root S of f modulo U0.  Rather than interpolate S explicitly, solve directly
for bounded polynomials R,B with R(x_i)=S(x_i)B(x_i).  At the critical degree
budget there are m homogeneous equations in m+1 coefficients, so a generic
assignment has one projective reconstruction candidate.  The target Mumford
congruence R == vB (mod u) supplies the missing genus-many conditions.
"""

from itertools import product
import json
from pathlib import Path

from toy_jacobian import GenusTwo


FIXTURE = Path(__file__).with_name("binary_split_norm_control.json")


def kernel_vector(matrix, prime):
    """Return (nullity, one null vector) over F_prime."""
    rows = [[value % prime for value in row] for row in matrix]
    row_count = len(rows)
    columns = len(rows[0]) if rows else 0
    pivots = []
    rank = 0
    for column in range(columns):
        pivot = next(
            (i for i in range(rank, row_count) if rows[i][column]),
            None,
        )
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        inverse = pow(rows[rank][column], -1, prime)
        rows[rank] = [value * inverse % prime for value in rows[rank]]
        for i in range(row_count):
            if i == rank or rows[i][column] == 0:
                continue
            scale = rows[i][column]
            rows[i] = [
                (left - scale * right) % prime
                for left, right in zip(rows[i], rows[rank], strict=True)
            ]
        pivots.append(column)
        rank += 1
        if rank == row_count:
            break

    free = [column for column in range(columns) if column not in pivots]
    if not free:
        return 0, None
    vector = [0] * columns
    vector[free[-1]] = 1
    for i, column in reversed(list(enumerate(pivots))):
        vector[column] = -sum(
            rows[i][other] * vector[other] for other in free
        ) % prime
    return len(free), vector


def product_from_roots(poly, roots):
    result = (1,)
    for root in roots:
        result = poly.mul(result, (-root % poly.p, 1))
    return result


def reconstruction_matrix(xs, ys, r_degree, b_degree, prime):
    rows = []
    for x, y in zip(xs, ys, strict=True):
        r_part = [pow(x, degree, prime) for degree in range(r_degree + 1)]
        b_part = [
            -y * pow(x, degree, prime) % prime
            for degree in range(b_degree + 1)
        ]
        rows.append(r_part + b_part)
    return rows


def main():
    fixture = json.loads(FIXTURE.read_text())
    prime = fixture["prime"]
    genus = fixture["genus"]
    curve = GenusTwo(prime)
    poly = curve.poly
    panels = []
    for panel in fixture["panels"]:
        r = panel["projective_section_dimension"]
        xs = panel["split_abscissae"]
        planted_ys = [point[1] for point in panel["selected_signed_points"]]
        u = tuple(panel["target_u"])
        v = tuple(panel["target_v"])
        b_degree = (r - 1) // 2
        c_degree = r // 2
        r_degree = max(len(u) - 1 + c_degree, len(v) - 1 + b_degree)
        coefficient_count = r_degree + b_degree + 2
        assert coefficient_count == len(xs) + 1
        modulus = product_from_roots(poly, xs)

        nullities = {}
        regular = 0
        regular_target_hits = []
        irregular_target_hits = []
        norm_checks = 0
        for signs in product((1, -1), repeat=len(xs)):
            ys = [
                y if sign == 1 else -y % prime
                for y, sign in zip(planted_ys, signs, strict=True)
            ]
            matrix = reconstruction_matrix(xs, ys, r_degree, b_degree, prime)
            nullity, vector = kernel_vector(matrix, prime)
            nullities[nullity] = nullities.get(nullity, 0) + 1
            if vector is None:
                continue
            r_poly = poly.canonical(vector[:r_degree + 1])
            b_poly = poly.canonical(vector[r_degree + 1:])
            assert all(
                poly.evaluate(r_poly, x)
                == y * poly.evaluate(b_poly, x) % prime
                for x, y in zip(xs, ys, strict=True)
            )
            norm = poly.sub(
                poly.mul(r_poly, r_poly),
                poly.mul(curve.coefficients, poly.mul(b_poly, b_poly)),
            )
            quotient = poly.exact_quotient(norm, modulus)
            norm_checks += 1

            is_regular = bool(b_poly) and all(
                poly.evaluate(b_poly, x) != 0 for x in xs
            )
            if is_regular:
                regular += 1

            target_remainder = poly.rem(
                poly.sub(r_poly, poly.mul(v, b_poly)),
                u,
            )
            if target_remainder:
                continue
            c_poly = poly.exact_quotient(
                poly.sub(r_poly, poly.mul(v, b_poly)),
                u,
            )
            assert len(c_poly) - 1 <= c_degree
            scalar = poly.exact_quotient(quotient, u)
            if is_regular:
                assert len(scalar) == 1 and scalar[0]
                regular_target_hits.append(signs)
            else:
                irregular_target_hits.append(signs)

        planted = (1,) * len(xs)
        assert regular_target_hits == [planted]
        panels.append({
            "projective_section_dimension": r,
            "tail_slots": len(xs),
            "r_degree_bound": r_degree,
            "b_degree_bound": b_degree,
            "c_degree_bound": c_degree,
            "homogeneous_coefficients": coefficient_count,
            "sign_assignments": 2 ** len(xs),
            "reconstruction_nullity_histogram": {
                str(key): value for key, value in sorted(nullities.items())
            },
            "regular_reconstruction_candidates": regular,
            "norm_divisibility_checks": norm_checks,
            "regular_target_congruence_candidates": len(regular_target_hits),
            "irregular_target_congruence_candidates": len(irregular_target_hits),
            "unique_regular_target_candidate_is_planted":
                regular_target_hits == [planted],
        })

    result = {
        "prime": prime,
        "genus": genus,
        "curve_coefficients": curve.coefficients,
        "panels": panels,
        "all_sign_assignments_have_projective_reconstruction": all(
            panel["reconstruction_nullity_histogram"]
            == {"1": panel["sign_assignments"]}
            for panel in panels
        ),
        "all_panels_have_one_regular_target_congruence_candidate": all(
            panel["regular_target_congruence_candidates"] == 1
            for panel in panels
        ),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
