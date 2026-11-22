#!/usr/bin/env python3
"""Check long-sum inversion by evaluation-code rank over a small prime field."""

from itertools import combinations
import json
from random import Random

from sage.all import GF, HyperellipticCurve, Matrix, PolynomialRing


def section_evaluations(target, points, degree, genus):
    """Return evaluations for the degree-m line bundle target + m*infinity."""
    u, v = target[0], target[1]
    ring = u.parent()
    field = ring.base_ring()
    x = ring.gen()
    u_degree = int(u.degree())
    pole_order = degree + u_degree
    monomials = [(x**i, ring.zero()) for i in range(pole_order // 2 + 1)]
    monomials += [
        (ring.zero(), x**i) for i in range((pole_order - (2 * genus + 1)) // 2 + 1)
    ]

    # A numerator over u must vanish at the conjugate of the reduced divisor.
    residues = [(a - b * v) % u for a, b in monomials]
    constraints = Matrix(
        field, u_degree, len(monomials), lambda i, j: residues[j][i]
    )
    section_basis = constraints.right_kernel().basis_matrix()
    assert section_basis.nrows() == degree + 1 - genus

    # Multiplying row i by u(x_i) preserves every zero and rank test.
    assert all(u(xi) != 0 for xi, _ in points)
    numerator_values = Matrix(
        field, [[a(xi) + b(xi) * yi for a, b in monomials] for xi, yi in points]
    )
    return numerator_values * section_basis.transpose()


def main():
    seed = 20261118
    rng = Random(seed)
    prime, genus, degree = 29, 2, 5
    field = GF(prime)
    ring = PolynomialRing(field, "x")
    x = ring.gen()
    curve = HyperellipticCurve(x**5 + 16*x**4 + 20*x**3 + 14*x**2 + 12*x + 4)
    group = curve.jacobian()(field)
    points = sorted(
        [(point[0], point[1]) for point in curve.rational_points() if point[2] == 1],
        key=lambda point: tuple(map(int, point)),
    )
    base = rng.sample(points, 11)
    point_classes = {point: group((x - point[0], ring(point[1]))) for point in points}
    zero = 0 * point_classes[points[0]]
    target_points = [rng.sample(base, degree) for _ in range(6)]
    target_points += [rng.sample(points, 2) for _ in range(6)]
    outcomes = []

    for index, sources in enumerate(target_points):
        target = sum((point_classes[point] for point in sources), zero)
        usable = [point for point in base if target[0](point[0]) != 0]
        evaluations = section_evaluations(target, usable, degree, genus)
        checks = solutions = 0
        for subset in combinations(range(len(usable)), degree):
            rank = evaluations.matrix_from_rows(list(subset)).rank()
            decomposes = sum((point_classes[usable[i]] for i in subset), zero) == target
            assert decomposes == (rank < evaluations.ncols())
            checks += 1
            solutions += int(decomposes)
        outcomes.append({
            "target_source": "base sum" if index < 6 else "curve point sum",
            "usable_base_size": len(usable),
            "subsets_checked": checks,
            "decompositions": solutions,
        })

    print(json.dumps({
        "prime": prime,
        "genus": genus,
        "decomposition_length": degree,
        "seed": seed,
        "total_subsets_checked": sum(row["subsets_checked"] for row in outcomes),
        "total_decompositions": sum(row["decompositions"] for row in outcomes),
        "targets": outcomes,
    }, indent=2))


if __name__ == "__main__":
    main()
