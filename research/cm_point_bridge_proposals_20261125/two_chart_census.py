#!/usr/bin/env python3
"""Exact point-input two-chart census on the predeclared F_1009 pair.

The evaluator receives a point only through coordinates; the test driver uses
scalar labels solely to enumerate/check all possible nonidentity inputs.
"""
import itertools
import json
import math
import random
import statistics
from sage.all import EllipticCurve, GF

P, R, SEED, ARMS = 1009, 1069, 20261125, 128
F = GF(P)
E = EllipticCurve(F, [4, 10])
G = E.gens()[0]
phi = E.isogenies_prime_degree(5)[0]
E2 = phi.codomain()
dual = phi.dual()
assert E.cardinality() == E2.cardinality() == G.order() == R
assert phi.degree() == 5 and dual(phi(G)) == 5 * G


def native_base(C, x_orbits):
    points = sorted((T for T in C.points() if not T.is_zero()),
                    key=lambda T: (int(T[0]), int(T[1])))
    selected_x = sorted({int(T[0]) for T in points})[:x_orbits]
    return [T for T in points if int(T[0]) in selected_x]


def triple_table(base):
    origin = base[0].curve()(0)
    out = {}
    for triple in itertools.combinations_with_replacement(base, 3):
        total = sum(triple, origin)
        if not total.is_zero():
            out.setdefault(total, triple)
    return out


source8 = native_base(E, 4)
endpoint8 = native_base(E2, 4)
source16 = native_base(E, 8)
assert (len(source8), len(endpoint8), len(source16)) == (8, 8, 16)
source_table = triple_table(source8)
endpoint_table = triple_table(endpoint8)
source16_table = triple_table(source16)


def evaluate(x, y):
    """Return source/endpoint witnesses from target coordinates, without d."""
    Q = E(F(x), F(y))
    if Q.is_zero():
        return None, None
    return source_table.get(Q), endpoint_table.get(phi(Q))


source_labels, endpoint_labels, source16_labels = set(), set(), set()
for d in range(1, R):
    Q = d * G  # test driver only; evaluate never receives d
    left, right = evaluate(int(Q[0]), int(Q[1]))
    if left is not None:
        assert sum(left, E(0)) == Q
        source_labels.add(d)
    if right is not None:
        assert sum((dual(T) for T in right), E(0)) == 5 * Q
        endpoint_labels.add(d)
    if Q in source16_table:
        assert sum(source16_table[Q], E(0)) == Q
        source16_labels.add(d)
assert len(source_labels) == len(source_table)
assert len(endpoint_labels) == len(endpoint_table)

points = native_base(E, (R - 1) // 2)
orbits = {}
for T in points:
    orbits.setdefault(int(T[0]), []).append(T)
assert len(orbits) == (R - 1) // 2 and all(len(v) == 2 for v in orbits.values())
keys = list(orbits)
rng = random.Random(SEED)
random16, split8 = [], []
for _ in range(ARMS):
    xs = rng.sample(keys, 8)
    B16 = [T for x in xs for T in orbits[x]]
    random16.append(len(triple_table(B16)))
    left_xs = rng.sample(keys, 4)
    right_xs = rng.sample(keys, 4)
    Bleft = [T for x in left_xs for T in orbits[x]]
    Bright = [T for x in right_xs for T in orbits[x]]
    split8.append(len(set(triple_table(Bleft)) | set(triple_table(Bright))))

union = source_labels | endpoint_labels
result = {
    "schema": "cm-two-chart-row-census/v1", "p": P, "r": R,
    "curve": [4, 10], "isogeny_degree": 5, "seed": SEED,
    "random_arms": ARMS, "base_sizes": [8, 8],
    "all_nonzero_scalar_inputs_replayed": R - 1,
    "source_rows": len(source_labels), "endpoint_dual_rows": len(endpoint_labels),
    "intersection": len(source_labels & endpoint_labels),
    "two_chart_union": len(union), "native_source16_support": len(source16_labels),
    "random_source16": random16, "random_split_source8_plus8": split8,
    "random_source16_median": statistics.median(random16),
    "random_split_median": statistics.median(split8),
    "two_chart_vs_random_split_ge": sum(v >= len(union) for v in split8),
    "triple_candidates_two_chart": 2 * math.comb(10, 3),
    "triple_candidates_source16": math.comb(18, 3),
    "rho_addition_reference": math.sqrt(math.pi * R / 4),
}
print(json.dumps(result, sort_keys=True, indent=2))
