#!/usr/bin/env sage -python
"""Exact fixed-pair support census for mixed signed eight-point bases."""

import json
from itertools import combinations_with_replacement

from sage.all import EllipticCurve, GF


def signed_orbits(curve):
    by_x = {}
    for point in curve.points():
        if not point.is_zero():
            by_x.setdefault(int(point[0]), []).append(point)
    assert all(len(pair) == 2 and pair[0] == -pair[1] for pair in by_x.values())
    return [by_x[x] for x in sorted(by_x)]


def support(curve, base):
    sums = {sum(triple, curve(0)) for triple in combinations_with_replacement(base, 3)}
    return len(sums - {curve(0)})


def main():
    source = EllipticCurve(GF(1009), [4, 10])
    phi = source.isogenies_prime_degree(5)[0]
    endpoint = phi.codomain()
    r = int(source.cardinality())
    assert r == int(endpoint.cardinality()) == 1069
    assert int(phi.degree()) == 5
    source_orbits = signed_orbits(source)
    endpoint_orbits = signed_orbits(endpoint)
    inv5 = pow(5, -1, r)
    dual = phi.dual()

    def pullback(point):
        result = inv5 * dual(point)
        assert phi(result) == point
        return result

    rows = []
    for source_pairs in range(5):
        endpoint_pairs = 4 - source_pairs
        native = sum(source_orbits[:source_pairs], [])
        pulled = [pullback(point)
                  for pair in endpoint_orbits[:endpoint_pairs] for point in pair]
        base = native + pulled
        assert len(base) == len(set(base)) == 8
        actual = support(source, base)
        assert actual <= 96
        rows.append({
            "source_pairs": source_pairs,
            "endpoint_pairs": endpoint_pairs,
            "source_x": [int(pair[0][0]) for pair in source_orbits[:source_pairs]],
            "endpoint_x": [int(pair[0][0]) for pair in endpoint_orbits[:endpoint_pairs]],
            "distinct_nonidentity_three_sums": actual,
        })
    assert [row["distinct_nonidentity_three_sums"] for row in rows] == [92, 92, 96, 96, 96]
    print(json.dumps({
        "schema": "signed-three-sum-ceiling/v1",
        "source": [int(x) for x in source.a_invariants()],
        "endpoint": [int(x) for x in endpoint.a_invariants()],
        "p": 1009, "r": r, "isogeny_degree": 5,
        "triple_multisets": 120,
        "forced_duplicate_count": 24,
        "support_upper_bound": 96,
        "rows": rows,
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
