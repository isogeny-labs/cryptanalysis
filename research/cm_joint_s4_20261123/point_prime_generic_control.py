#!/usr/bin/env sage -python
"""Check the point-selected-prime construction on two unrelated ordinary curves."""

import json

from sage.all import EllipticCurve, GF, PolynomialRing, prod


CASES = (
    (47, 1, 38, 2, 1, 61, -19),
    (43, 1, 3, 9, 15, 47, -163),
)


def check_case(p, a, b, gx, gy, r, expected_discriminant):
    field = GF(p)
    curve = EllipticCurve(field, [a, b])
    generator = curve(gx, gy)
    assert int(curve.cardinality()) == int(generator.order()) == r
    trace = p + 1 - r
    discriminant = trace * trace - 4 * p
    assert discriminant == expected_discriminant
    assert p != r and trace % p != 0
    assert int(curve.j_invariant()) not in (0, 1728 % p)

    ring = PolynomialRing(field, "X")
    X = ring.gen()
    roots = {int((u * generator)[0]) for u in range(1, r)}
    assert len(roots) == (r - 1) // 2
    orbit_poly = prod(X - field(x) for x in roots)
    assert orbit_poly.gcd(orbit_poly.derivative()) == 1

    def selected_prime(point):
        x = field(point[0])
        assert orbit_poly(x) == 0
        assert ring.ideal(orbit_poly, X - x) == ring.ideal(X - x)
        return int(x)

    target = 3 * generator
    generator_root = selected_prime(generator)
    target_root = selected_prime(target)
    assert selected_prime(-target) == target_root
    indices = [u for u in range(1, r)
               if selected_prime(u * generator) == target_root]
    assert indices == [3, r - 3]
    assert len({selected_prime(u * generator) for u in range(1, r)}) == (r - 1) // 2

    return {
        "p": p, "curve_a": a, "curve_b": b, "r": r,
        "frobenius_discriminant": discriminant,
        "j": int(curve.j_invariant()),
        "generator": [gx, gy],
        "target_public_fixture_label": 3,
        "x_generator": generator_root, "x_target": target_root,
        "orbit_polynomial_degree": int(orbit_poly.degree()),
        "distinct_selected_primes": len(roots),
        "indices_mapping_generator_prime_to_target_prime": indices,
    }


if __name__ == "__main__":
    print(json.dumps({"schema": "point-prime-generic-control/v1",
                      "cases": [check_case(*case) for case in CASES]},
                     indent=2, sort_keys=True))
