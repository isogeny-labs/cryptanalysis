#!/usr/bin/env sage -python
"""Exploratory coordinate-to-squared-ray coefficient census."""

import json
import random
import statistics

from sage.all import EllipticCurve, GF, QuadraticField, ZZ


SEED = 20261125
NULL_ARMS = 128


def ray_coefficient(x, p, r, scale=1):
    # x is the canonical integer representative in [0,p). An isomorphic
    # Weierstrass reparameterization changes x to scale^2*x.
    c = ((scale * scale * x) % p - 1) % r
    return None if c == 0 else -pow(c, -1, r) % r


def sign(value, r):
    assert value is not None and value != 0
    return 1 if pow(value, (r-1)//2, r) == 1 else -1


def census(name, curve, generator, scales=()):
    p = int(curve.base_field().cardinality())
    r = int(curve.cardinality())
    assert int(generator.order()) == r
    points = [d*generator for d in range(r)]
    xs = [None] + [int(point[0]) for point in points[1:]]
    disc = ZZ((p + 1 - r)**2 - 4*p)
    assert disc.is_fundamental_discriminant()
    K = QuadraticField(disc, "s")
    pi = (p + 1 - r + K.gen())/2
    eta = pi - 1
    n = K.ideal(eta)
    n2 = n*n
    for x in xs[1:4]:
        c = x - 1
        if c % r:
            assert (K.ideal(c) + n).norm() == 1
            assert (K.ideal(x - pi) + n).norm() == 1
            assert (x - pi)/c - (1 - eta/c) in n2

    def values(scale):
        return [None] + [ray_coefficient(x, p, r, scale) for x in xs[1:]]

    def character_row(scale):
        z = values(scale)
        assert z[1] is not None
        domain = [d for d in range(1, r) if z[d] is not None]
        hits = sum(sign(z[d] * pow(z[1], -1, r) % r, r) == sign(d, r)
                   for d in domain)
        return {"hits": hits, "domain": len(domain), "rate": hits / len(domain)}

    z = values(1)
    domain = [d for d in range(1, r) if z[d] is not None]
    valid_pairs = [(a, b) for a in domain for b in domain
                   if (a+b) % r and z[(a+b) % r] is not None]
    additive = sum(z[(a+b) % r] == (z[a]+z[b]) % r for a,b in valid_pairs)
    row = {
        "name": name, "p": p, "r": r, "undefined": r-1-len(domain),
        "z1": z[1], "z2": z[2],
        "scalar_rule_matches": sum(z[d] == d*z[1] % r for d in domain),
        "additive_matches": additive, "valid_pairs": len(valid_pairs),
        "character": character_row(1),
    }
    if scales:
        null = [character_row(u)["rate"] for u in scales]
        row["isomorphic_scale_null"] = {
            "arms": len(null), "min": min(null),
            "median": statistics.median(null), "max": max(null),
            "ge_actual": sum(v >= row["character"]["rate"] for v in null),
        }
        row["scale_rates"] = null
    return row


def main():
    control = EllipticCurve(GF(47), [1, 38])
    source = EllipticCurve(GF(1009), [4, 10])
    G = source.gens()[0]
    phi = source.isogenies_prime_degree(5)[0]
    assert int(control.cardinality()) == 61
    assert int(source.cardinality()) == 1069
    assert int(phi.codomain().cardinality()) == 1069
    scales = random.Random(SEED).sample(range(1, 1009), NULL_ARMS)
    rows = [census("D-19", control, control(2,1)),
            census("source", source, G, scales),
            census("horizontal_endpoint", phi.codomain(), phi(G), scales)]
    source_rates = rows[1].pop("scale_rates")
    endpoint_rates = rows[2].pop("scale_rates")
    actual_delta = rows[2]["character"]["rate"] - rows[1]["character"]["rate"]
    null_delta = [b-a for a,b in zip(source_rates, endpoint_rates)]
    print(json.dumps({
        "schema": "coordinate-ideal-ray-screen/v1", "seed": SEED,
        "null_arms": NULL_ARMS, "rows": rows,
        "endpoint_minus_source": {
            "actual": actual_delta, "null_min": min(null_delta),
            "null_median": statistics.median(null_delta),
            "null_max": max(null_delta),
            "null_ge_actual": sum(v >= actual_delta for v in null_delta),
        },
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
