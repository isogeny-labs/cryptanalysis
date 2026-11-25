#!/usr/bin/env sage -python
"""Finite split-orbit algebra selected by supplied point coordinates."""

import json
from math import ceil, log2

from sage.all import EllipticCurve, GF, PolynomialRing, prod


def main():
    p, r = 47, 61
    field = GF(p)
    curve = EllipticCurve(field, [1, 38])
    generator = curve(2, 1)
    assert int(curve.cardinality()) == r and int(generator.order()) == r
    ring = PolynomialRing(field, "X")
    X = ring.gen()
    roots = [int((d*generator)[0]) for d in range(1, (r+1)//2)]
    assert len(set(roots)) == (r-1)//2
    orbit_poly = prod(X-field(x) for x in roots)
    assert orbit_poly.degree() == 30 and orbit_poly.gcd(orbit_poly.derivative()) == 1
    assert all(degree == 1 and multiplicity == 1
               for factor, multiplicity in orbit_poly.factor()
               for degree in (factor.degree(),))

    # The assignment itself reads only the supplied point's coordinate.
    def selected_prime(point):
        x = field(point[0])
        assert orbit_poly(x) == 0
        ideal = ring.ideal(orbit_poly, X-x)
        assert ideal.gen() == X-x or ideal.gen() == x-X
        return int(x)

    target = 3*generator  # Public fixture label, used only to check orientation.
    root_G = selected_prime(generator)
    root_Q = selected_prime(target)
    assert selected_prime(-target) == root_Q
    assert root_Q == int(target[0])
    assert len({selected_prime(d*generator) for d in range(1, r)}) == 30
    assert len({(int((d*generator)[0]), int((d*generator)[1]))
                for d in range(1, r)}) == 60

    # The known scalar action permutes prime selectors. Matching its index
    # for an arbitrary supplied target remains a point-log computation.
    action = {a: {selected_prime(d*generator): selected_prime(a*d*generator)
                  for d in range(1, (r+1)//2)} for a in range(1, r)}
    assert all(len(set(permutation.values())) == 30 for permutation in action.values())
    assert action[3][root_G] == root_Q
    assert {a for a in range(1, r) if action[a][root_G] == root_Q} == {3, r-3}

    p192 = 6277101735386680763835789423207666416083908700390324961279
    r192 = 6277101735386680763835789423176059013767194773182842284081
    relative_degree = (r192-1)//2
    dense_bytes = relative_degree * ceil(p192.bit_length()/8)
    print(json.dumps({
        "schema": "reduced-ray-prime-bridge/v1",
        "p": p, "r": r, "x_orbit_degree": 30,
        "signed_orbit_degree": 60,
        "orbit_polynomial_coefficients": [int(c) for c in orbit_poly.list()],
        "x_generator": root_G, "x_target": root_Q,
        "target_public_fixture_label": 3,
        "action_indices_mapping_generator_prime_to_target_prime": [3, r-3],
        "p192_relative_x_orbit_degree_bits": relative_degree.bit_length(),
        "p192_dense_one_vector_bytes_bits": dense_bytes.bit_length(),
        "p192_dense_one_vector_bytes_log2": log2(dense_bytes),
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
