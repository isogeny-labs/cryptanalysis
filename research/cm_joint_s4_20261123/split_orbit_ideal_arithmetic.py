#!/usr/bin/env sage -python
"""Verify the idempotent ideal arithmetic of finite split point orbits."""

import json

from sage.all import EllipticCurve, GF, PolynomialRing, prod


CASES = (
    (47, 1, 38, 2, 1, 61),
    (43, 1, 3, 9, 15, 47),
)


def check_case(p, a, b, gx, gy, r):
    field = GF(p)
    curve = EllipticCurve(field, [a, b])
    generator = curve(gx, gy)
    assert int(curve.cardinality()) == int(generator.order()) == r
    ring = PolynomialRing(field, "X")
    X = ring.gen()
    roots = sorted({int((d * generator)[0]) for d in range(1, r)})
    assert len(roots) == (r - 1) // 2
    orbit_poly = prod(X - field(x) for x in roots)
    assert orbit_poly.gcd(orbit_poly.derivative()) == 1
    for x in roots:
        linear = X - field(x)
        cofactor = orbit_poly // linear
        gcd, bezout_linear, bezout_cofactor = linear.xgcd(cofactor)
        assert gcd == 1
        assert bezout_linear * linear + bezout_cofactor * cofactor == 1
        # In A=F_p[X]/(F_G), this says linear is in (linear)^2.
        assert (linear - bezout_linear * linear * linear) % orbit_poly == 0
    x, y = roots[:2]
    first_two = (X - field(x)) * (X - field(y))
    assert orbit_poly % first_two == 0
    assert first_two.degree() == 2
    target = 3 * generator
    assert int(target[0]) in roots
    return {
        "p": p, "r": r, "curve_a": a, "curve_b": b,
        "generator": [gx, gy], "orbit_degree": len(roots),
        "squarefree": True,
        "maximal_ideal_idempotence_checks": len(roots),
        "selected_prime_root_from_target": int(target[0]),
        "each_maximal_ideal_quotient_size": p,
        "first_two_distinct_ideal_product_quotient_size": p * p,
    }


if __name__ == "__main__":
    print(json.dumps({"schema": "split-orbit-ideal-arithmetic/v1",
                      "cases": [check_case(*case) for case in CASES]},
                     indent=2, sort_keys=True))
