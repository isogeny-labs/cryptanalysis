"""Generate a matched, positive-control Cayley-coset msolve pilot.

This is an independent fixture at p=15359, not the unavailable L20/L24/L28
inputs named in the attachment. Run with ``sage -python generate_msolve_pilot.py``.
"""

import json
import random
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing


FIELD = GF(15359)
CURVE = EllipticCurve(FIELD, [2, 8])
RING = PolynomialRing(FIELD, "X")
X = RING.gen()
HERE = Path(__file__).resolve().parent


def semaev3(x, y, z):
    a, b = CURVE.a4(), CURVE.a6()
    return (
        (x - y) ** 2 * z**2
        - 2 * ((x + y) * (x * y + a) + 2 * b) * z
        + (x * y - a) ** 2
        - 4 * b * (x + y)
    )


def eligible(x):
    rhs = x**3 + CURVE.a4() * x + CURVE.a6()
    return rhs != 0 and rhs.is_square()


def main():
    assert int(CURVE.order()) == 15581 and CURVE.order().is_prime()
    # Re((X+i)^6) and Im((X+i)^6), with i^2=-1.
    real = X**6 - 15 * X**4 + 15 * X**2 - 1
    imag = 6 * X**5 - 20 * X**3 + 6 * X
    for seed in range(1, int(FIELD.order())):
        if imag(FIELD(seed)) == 0:
            continue
        coset_label = real(FIELD(seed)) / imag(FIELD(seed))
        coset_poly = real - coset_label * imag
        roots = sorted(int(x) for x, multiplicity in coset_poly.roots() if multiplicity == 1)
        if len(roots) == 6 and all(eligible(FIELD(x)) for x in roots):
            break
    else:
        raise AssertionError("No all-eligible six-root Cayley coset found")

    shared = roots[:3]
    candidates = [x for x in range(int(FIELD.order())) if x not in roots and eligible(FIELD(x))]
    random.Random(20261125).shuffle(candidates)
    extras = candidates[:3]
    comparison_roots = shared + extras
    assert len(set(comparison_roots)) == 6
    comparison_poly = RING.prod(X - FIELD(x) for x in comparison_roots)
    points = [
        CURVE(FIELD(x), (FIELD(x) ** 3 + CURVE.a4() * FIELD(x) + CURVE.a6()).sqrt())
        for x in shared
    ]
    target = sum(points, CURVE(0))
    assert not target.is_zero()
    witness_w = points[0] + points[1]
    assert semaev3(points[0][0], points[1][0], witness_w[0]) == 0
    assert semaev3(witness_w[0], points[2][0], target[0]) == 0

    ring = PolynomialRing(FIELD, names=("x1", "x2", "x3", "w"))
    x1, x2, x3, w = ring.gens()
    system_head = [semaev3(x1, x2, w), semaev3(w, x3, FIELD(target[0]))]
    for arm, polynomial in (("cayley", coset_poly), ("matched", comparison_poly)):
        system = system_head + [polynomial(x1), polynomial(x2), polynomial(x3)]
        contents = "x1,x2,x3,w\n15359\n" + ",\n".join(str(f) for f in system) + "\n"
        (HERE / f"pilot_{arm}.ms").write_text(contents)

    record = {
        "field_prime": 15359,
        "curve_a4_a6": [2, 8],
        "curve_order": int(CURVE.order()),
        "cayley_seed": seed,
        "cayley_label": int(coset_label),
        "cayley_roots": roots,
        "matched_roots": comparison_roots,
        "shared_roots": shared,
        "target_xy": [int(t) for t in target.xy()],
        "witness_w_x": int(witness_w[0]),
        "all_roots_curve_eligible": True,
        "positive_relation_in_both_arms": True,
    }
    (HERE / "pilot_fixture.json").write_text(json.dumps(record, sort_keys=True) + "\n")
    print(json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
