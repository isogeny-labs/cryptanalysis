"""Replay the public twisted-Edwards and isogeny-network checks.

Run with ``sage -python verify.py``.  The program uses exact finite-field
arithmetic and prints one JSON record.  It performs no DLP search.
"""

import json
from itertools import combinations

from sage.all import EllipticCurve, GF, PolynomialRing


def edwards_sum(y1, y2, y3, a, d):
    return (
        d * y1**2 * y2**2 * y3**2
        - d * (y1**2 * y2**2 + y1**2 * y3**2 + y2**2 * y3**2)
        + a * (y1**2 + y2**2 + y3**2)
        - 2 * (a - d) * y1 * y2 * y3
        - a
    )


def edwards_check(field):
    a, d = field(3), field(2)
    points = []
    for y_integer in range(2, 200):
        y = field(y_integer)
        denominator = a - d * y**2
        if denominator == 0:
            continue
        x_squared = (1 - y**2) / denominator
        if x_squared != 0 and x_squared.is_square():
            points.append((x_squared.sqrt(), y))
        if len(points) >= 5:
            break
    p1, p2 = points[0], points[2]
    x1, y1 = p1
    x2, y2 = p2
    product = d * x1 * x2 * y1 * y2
    assert 1 + product != 0 and 1 - product != 0
    x_sum = (x1 * y2 + y1 * x2) / (1 + product)
    y_sum = (y1 * y2 - a * x1 * x2) / (1 - product)
    assert a * x_sum**2 + y_sum**2 == 1 + d * x_sum**2 * y_sum**2
    assert edwards_sum(y1, y2, y_sum, a, d) == 0

    ring = PolynomialRing(field, names=("y1", "y2", "y3", "y4", "z"))
    v1, v2, v3, v4, z = ring.gens()
    f3 = edwards_sum(v1, v2, v3, a, d)
    f4 = edwards_sum(v1, v2, z, a, d).resultant(
        edwards_sum(v3, v4, z, a, d), z
    )
    assert len(f3.monomials()) == 9
    assert len(f4.monomials()) == 57
    assert f4(-v1, -v2, v3, v4, z) == f4
    assert f4(-v1, v2, v3, -v4, z) == f4
    assert f4(-v1, v2, v3, v4, z) != f4
    return {
        "field_prime": int(field.order()),
        "a": int(a),
        "d": int(d),
        "sample_y": [int(y1), int(y2), int(y_sum)],
        "sample_relation_value": 0,
        "f3_monomials": len(f3.monomials()),
        "f4_monomials": len(f4.monomials()),
        "f4_even_sign_invariant": True,
        "f4_single_sign_invariant": False,
    }


def coordinate_bound_pullback(phi, bound, field):
    codomain = phi.codomain()
    dual = phi.dual()
    pulled_back = set()
    for x_integer in range(bound):
        x = field(x_integer)
        # Sage's rational isogeny codomains use short Weierstrass models here.
        assert codomain.a1() == codomain.a2() == codomain.a3() == 0
        y_squared = x**3 + codomain.a4() * x + codomain.a6()
        if not y_squared.is_square():
            continue
        y = y_squared.sqrt()
        for ordinate in {y, -y}:
            q = codomain(x, ordinate)
            p = dual(q)
            pulled_back.add(tuple(int(t) for t in p.xy()))
    return pulled_back


def network_check(field):
    supplied = EllipticCurve(field, [-3, 12])
    assert int(supplied.order()) == 10074
    curve = EllipticCurve(field, [-3, 7])
    order = int(curve.order())
    assert order == 10193 and curve.order().is_prime()
    target = 137 * curve.gens()[0]
    degrees = (2, 3, 5, 7, 11, 13, 17, 19)
    network = [
        (degree, phi)
        for degree in degrees
        for phi in curve.isogenies_prime_degree(degree)
    ]
    assert [degree for degree, _ in network] == [7, 11, 11, 19, 19]
    sets = []
    for degree, phi in network:
        assert phi.dual()(phi(target)) == degree * target
        assert phi.codomain().order() == curve.order()
        sets.append(coordinate_bound_pullback(phi, 250, field))
    overlaps = [len(sets[i] & sets[j]) for i, j in combinations(range(len(sets)), 2)]
    assert [len(s) for s in sets] == [262, 258, 256, 276, 262]
    assert len(set().union(*sets)) == 1246
    assert overlaps == [6, 2, 2, 4, 10, 16, 10, 12, 6, 6]
    return {
        "field_prime": int(field.order()),
        "supplied_curve_order": int(supplied.order()),
        "prime_order_curve_a4_a6": [-3, 7],
        "prime_order_curve_order": order,
        "network_degrees": [degree for degree, _ in network],
        "coordinate_bound": 250,
        "pullback_sizes": [len(s) for s in sets],
        "sum_of_sizes": sum(map(len, sets)),
        "union_size": len(set().union(*sets)),
        "pairwise_overlaps": overlaps,
        "dual_identity_checked": True,
    }


def main():
    field = GF(10007)
    print(json.dumps({"edwards": edwards_check(field), "network": network_check(field)}, sort_keys=True))


if __name__ == "__main__":
    main()
