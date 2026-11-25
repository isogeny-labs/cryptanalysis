#!/usr/bin/env sage -python
"""Frozen finite controls for anti-Frobenius kernel versus EDS normalizer."""

import json

from sage.all import EllipticCurve, GF, PolynomialRing, ZZ


def census(name, curve, generator, labels):
    p = int(curve.base_field().cardinality())
    r = int(curve.cardinality())
    assert int(generator.order()) == r and r % 2 == 1
    exponent = pow(r * r, -1, p - 1)
    assert exponent % 2 == 1
    field = curve.base_field()
    ring = PolynomialRing(field, "X")
    X = ring.gen()
    a, b = curve.a4(), curve.a6()
    roots = [field(x) for x in range(p)
             if pow(int(field(x)**3 + a*field(x) + b), (p-1)//2, p) == p-1]
    kernel = ring.prod(X-x for x in roots)
    norm = 2*(p+1)-r
    assert norm % 2 == 1 and kernel.degree() == (norm-1)//2

    def w(point, n):
        return curve.division_polynomial(
            ZZ(n), (point[0], point[1]),
            two_torsion_multiplicity=1, force_evaluate=0)

    def normalizer(point):
        numerator = w(point, p-1)
        denominator = w(point, p-1+r)
        assert numerator != 0 and denominator != 0
        return (numerator/denominator)**exponent

    def character(value):
        assert value != 0
        return 1 if value**((p-1)//2) == 1 else -1

    first_normalizer = normalizer(generator)
    first_kernel = character(kernel(generator[0]))
    first_yphi = character(generator[1]*first_normalizer)
    orientation = first_kernel*first_yphi
    rows = []
    for d in labels:
        point = d*generator
        value = normalizer(point)
        assert normalizer(-point) == -value
        kernel_sign = character(kernel(point[0]))
        normalizer_sign = character(point[1]*value)
        rows.append({"d": d, "kernel_sign": kernel_sign,
                     "normalizer_sign": normalizer_sign,
                     "oriented_normalizer_sign": orientation*normalizer_sign,
                     "match": kernel_sign == orientation*normalizer_sign})
    mismatches = [row["d"] for row in rows if not row["match"]]
    return {"name": name, "p": p, "r": r, "a": int(a), "b": int(b),
            "generator": [int(generator[0]), int(generator[1])],
            "kernel_norm": norm, "kernel_degree": kernel.degree(),
            "orientation": orientation, "matches": len(rows)-len(mismatches),
            "first_mismatch": mismatches[0] if mismatches else None,
            "mismatches": mismatches, "rows": rows}


def main():
    f47 = GF(47)
    control = EllipticCurve(f47, [5, 8])
    assert int(control.cardinality()) == 53
    records = [census("D-163", control, control(19, 37), list(range(1, 53)))]

    f1009 = GF(1009)
    source = EllipticCurve(f1009, [4, 10])
    assert int(source.cardinality()) == 1069
    edge = source.isogenies_prime_degree(5)[0]
    endpoint = edge.codomain()
    assert tuple(int(v) for v in endpoint.a_invariants()) == (0, 0, 0, 888, 852)
    generator = source.gens()[0]
    labels = [1, 2, 3, 5, 7, 11, 13, 17]
    records.append(census("source-1009", source, generator, labels))
    records.append(census("endpoint-1009", endpoint, edge(generator), labels))
    print(json.dumps({"schema": "normalizer-kernel-equivalence/v1",
                      "pilot_D19_matches": "60/60, observed before freeze",
                      "records": records}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
