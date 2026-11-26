#!/usr/bin/env python3
"""Measure linear spans of higher-dimensional hyperelliptic tail sections."""

from argparse import ArgumentParser
import json
from math import comb
from pathlib import Path
from random import Random

from toy_jacobian import PrimePolynomials


PRIME = 1_000_003
SEED = 904_211


def rank_mod(rows, prime):
    rows = [[value % prime for value in row] for row in rows]
    rank = 0
    for column in range(len(rows[0]) if rows else 0):
        pivot = next((i for i in range(rank, len(rows)) if rows[i][column]), None)
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        inverse = pow(rows[rank][column], -1, prime)
        rows[rank] = [value * inverse % prime for value in rows[rank]]
        for i in range(len(rows)):
            if i == rank or not rows[i][column]:
                continue
            multiple = rows[i][column]
            rows[i] = [(left - multiple * right) % prime
                       for left, right in zip(rows[i], rows[rank], strict=True)]
        rank += 1
        if rank == len(rows):
            break
    return rank


def pad(poly, length):
    return tuple(poly[i] if i < len(poly) else 0 for i in range(length))


def random_curve(genus, rng):
    poly = PrimePolynomials(PRIME)
    while True:
        u = poly.canonical([rng.randrange(PRIME) for _ in range(genus)] + [1])
        v = poly.canonical([rng.randrange(PRIME) for _ in range(genus)])
        w = poly.canonical([rng.randrange(PRIME) for _ in range(genus + 1)] + [1])
        f = poly.add(poly.mul(v, v), poly.mul(u, w))
        derivative = poly.canonical(i * value for i, value in enumerate(f) if i)
        if len(f) == 2 * genus + 2 and poly.xgcd(f, derivative)[0] == (1,):
            return poly, u, v, w, f


def monomial(poly, degree):
    return poly.canonical([0] * degree + [1])


def section_basis(poly, u, v, r):
    basis = []
    for degree in range((r - 1) // 2 + 1):
        b = monomial(poly, degree)
        basis.append((b, poly.mul(b, v)))
    for degree in range(r // 2 + 1):
        c = monomial(poly, degree)
        basis.append(((), poly.mul(u, c)))
    assert len(basis) == r + 1
    return basis


def panel(genus, r, curve):
    poly, u, v, _, f = curve
    q = genus + r
    basis = section_basis(poly, u, v, r)
    products = []
    for i, (first_b, first_a) in enumerate(basis):
        for second_b, second_a in basis[i:]:
            numerator = poly.sub(poly.mul(poly.mul(first_b, second_b), f),
                                  poly.mul(first_a, second_a))
            quotient = poly.exact_quotient(numerator, u)
            assert len(quotient) <= q + 1
            products.append(pad(quotient, q + 1))
    rank = rank_mod(products, PRIME)
    constant = (1,) + (0,) * q
    return {
        "genus": genus,
        "tail_excess": r,
        "tail_slots": q,
        "section_dimension": len(basis),
        "quadratic_products": len(products),
        "ambient_coefficients": q + 1,
        "measured_span_rank": rank,
        "linear_annihilators": q + 1 - rank,
        "quadratic_dimension_bound": min(q + 1, comb(r + 2, 2)),
        "hyperelliptic_span_bound": min(q + 1, 3 * r),
        "constant_in_span": rank_mod(products + [constant], PRIME) == rank,
    }


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rng = Random(SEED)
    curves = {genus: random_curve(genus, rng) for genus in range(2, 8)}
    result = {
        "prime": PRIME,
        "seed": SEED,
        "curves": {
            str(genus): {"u": curve[1], "v": curve[2], "w": curve[3], "f": curve[4]}
            for genus, curve in curves.items()
        },
        "panels": [panel(genus, r, curves[genus])
                   for genus in range(2, 8)
                   for r in range(1, genus // 2 + 2)],
    }
    output = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
