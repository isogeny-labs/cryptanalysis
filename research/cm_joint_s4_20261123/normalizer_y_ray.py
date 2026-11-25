#!/usr/bin/env sage -python
"""Exact D=-19 test of the oriented character of y(Q)*Phi(Q)."""

import json

from sage.all import EllipticCurve, GF, ZZ

P = 47
R = 61


def main():
    field = GF(P)
    curve = EllipticCurve(field, [1, 38])
    generator = curve(2, 1)
    assert int(curve.cardinality()) == R and int(generator.order()) == R
    exponent = pow(R * R, -1, P - 1)
    assert exponent % 2 == 1

    def w(point, n):
        return curve.division_polynomial(
            ZZ(n), (point[0], point[1]),
            two_torsion_multiplicity=1, force_evaluate=0)

    def phi(point):
        numerator = w(point, P - 1)
        denominator = w(point, P - 1 + R)
        assert numerator != 0 and denominator != 0
        return (numerator / denominator) ** exponent

    def character(value):
        assert value != 0
        return 1 if value ** ((P - 1) // 2) == 1 else -1

    phi_generator = phi(generator)
    assert phi_generator == field(40)
    orientation = character(generator[1] * phi_generator)
    rows = []
    for d in range(1, R):
        point = d * generator
        value = phi(point)
        assert phi(-point) == -value
        raw = character(point[1] * value)
        oriented = orientation * raw
        truth = 1 if pow(d, (R - 1) // 2, R) == 1 else -1
        rows.append({"d": d, "raw": raw, "oriented": oriented,
                     "ray_character": truth, "phi": int(value),
                     "y": int(point[1])})
    mismatches = [row["d"] for row in rows
                  if row["oriented"] != row["ray_character"]]
    print(json.dumps({
        "schema": "normalizer-y-ray/v1", "p": P, "r": R,
        "curve": [1, 38], "generator": [2, 1],
        "phi_generator": int(phi_generator), "orientation": orientation,
        "count": len(rows), "agreement": len(rows) - len(mismatches),
        "first_mismatch": mismatches[0] if mismatches else None,
        "mismatches": mismatches, "rows": rows,
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
