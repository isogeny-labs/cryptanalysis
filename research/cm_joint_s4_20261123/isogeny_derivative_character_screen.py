#!/usr/bin/env sage -python
"""Exact finite screen of a horizontal-isogeny derivative ray predicate."""

import json

from sage.all import EllipticCurve, GF


def screen(p, a, b, generator_xy, r, ell):
    field = GF(p)
    curve = EllipticCurve(field, [a, b])
    generator = curve(*generator_xy) if generator_xy else curve.gens()[0]
    assert int(curve.cardinality()) == int(generator.order()) == r
    assert r % 4 == 1
    result = []
    for edge_index, phi in enumerate(curve.isogenies_prime_degree(ell)):
        derivative = phi.x_rational_map().derivative()
        matches = 0
        first_mismatch = None
        signs = []
        for d in range(1, r):
            point = d * generator
            image = phi(point)
            assert not point.is_zero() and not image.is_zero()
            value = derivative(point[0])
            assert value != 0 and point[1] != 0 and image[1] != 0
            # Sage's checked maps are normalized; verify the exact
            # differential identity independently through point evaluation.
            assert value == image[1] / point[1]
            observed = 1 if value ** ((p - 1) // 2) == 1 else -1
            expected = 1 if pow(d, (r - 1) // 2, r) == 1 else -1
            signs.append(observed)
            matches += observed == expected
            if observed != expected and first_mismatch is None:
                first_mismatch = d
        assert len(signs) == r - 1
        assert all(signs[d - 1] == signs[r - d - 1] for d in range(1, r))
        result.append({
            "edge_index": edge_index,
            "degree": ell,
            "codomain_j": int(phi.codomain().j_invariant()),
            "kernel_polynomial": [int(c) for c in phi.kernel_polynomial().list()],
            "matches_raw": matches,
            "matches_best_global_sign": max(matches, r - 1 - matches),
            "tested_nonzero_points": r - 1,
            "differential_identity_checks": r - 1,
            "first_raw_mismatch_label": first_mismatch,
        })
    return {
        "p": p, "curve_a": a, "curve_b": b, "r": r,
        "generator": [int(generator[0]), int(generator[1])],
        "frobenius_discriminant": (p + 1 - r) ** 2 - 4 * p,
        "edges": result,
    }


if __name__ == "__main__":
    print(json.dumps({
        "schema": "isogeny-derivative-character-screen/v1",
        "scope": "retrospective finite exact screen",
        "cases": [
            screen(47, 1, 38, (2, 1), 61, 5),
            screen(47, 1, 38, (2, 1), 61, 7),
            screen(1009, 4, 10, None, 1069, 5),
        ],
    }, indent=2, sort_keys=True))
