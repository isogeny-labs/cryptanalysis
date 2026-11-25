#!/usr/bin/env sage -python
"""Replay fixed r=61 target-sum queries with a transposed descriptor hash.

This uses public point operations for the query; d is used only to generate
and verify the finite control instances.
"""

import json

from sage.all import EllipticCurve, GF


R, L, LAM = 61, 3, 7
CATEGORIES = ((1, 0), (-1, 0), (0, 1), (0, -1))


def key(point):
    return None if point.is_zero() else (int(point[0]), int(point[1]))


def cat_index(category, exponent):
    return (0 if category < 2 else 2 * L) + 2 * exponent + category % 2


def descriptors(G, Q):
    index = {}
    for low in range(4):
        for high in range(low, 4):
            P = CATEGORIES[low][0] * G + CATEGORIES[low][1] * Q
            P += CATEGORIES[high][0] * G + CATEGORIES[high][1] * Q
            index.setdefault(key(P), []).append((low, high, 0))
    for gap in range(1, L):
        for low in range(4):
            for high in range(4):
                P = CATEGORIES[low][0] * G + CATEGORIES[low][1] * Q
                P += LAM**gap * (CATEGORIES[high][0] * G + CATEGORIES[high][1] * Q)
                index.setdefault(key(P), []).append((low, high, gap))
    assert sum(len(v) for v in index.values()) == 42
    return index


def base(G, Q):
    rows = []
    for seed, A, B in ((G, 1, 0), (Q, 0, 1)):
        point = seed
        for exponent in range(L):
            factor = pow(LAM, exponent, R)
            for sign in (1, -1):
                rows.append((sign * point, sign * factor % R * A,
                             sign * factor % R * B))
            point = LAM * point
    return rows


def query(index, rows, G, Q, a, b):
    target = a * G + b * Q
    inv = pow(LAM, -1, R)
    matches = set()
    for third, (P, _, _) in enumerate(rows):
        shifted = target - P
        for exponent in range(L):
            for low, high, gap in index.get(key(shifted), ()):
                if exponent < L - gap:
                    i = cat_index(low, exponent)
                    j = cat_index(high, exponent + gap)
                    matches.add(tuple(sorted((i, j, third))))
            shifted = inv * shifted
    informative = []
    for indices in sorted(matches):
        A = sum(rows[i][1] for i in indices) % R
        B = sum(rows[i][2] for i in indices) % R
        assert sum((rows[i][0] for i in indices), G.curve()(0)) == target
        if (B - b) % R:
            informative.append((indices, A, B))
    return matches, informative


def main():
    E = EllipticCurve(GF(47), [1, 38])
    G = E(2, 1)
    assert int(E.cardinality()) == R and int(G.order()) == R
    with open("research/cm_joint_s4_20261123/inhomogeneous_orbit_results.json") as f:
        frozen = json.load(f)
    count = 0
    for record in frozen["records"]:
        d = record["d"]
        Q = d * G
        rows = base(G, Q)
        assert len(rows) == 12 and all(P == A * G + B * Q for P, A, B in rows)
        index = descriptors(G, Q)
        for row in record["queries"]:
            matches, informative = query(index, rows, G, Q, row["a"], row["b"])
            assert len(matches) == row["matches"]
            assert len(informative) == row["informative_matches"]
            first = row["first_informative"]
            assert (not informative) == (first is None)
            if first:
                indices, A, B = informative[0]
                assert list(indices) == first["indices"]
                assert (A, B) == (first["A"], first["B"])
                assert (A - row["a"] + d * (B - row["b"])) % R == 0
            count += 1
    assert count == 1920
    print("PASS: transposed descriptor hash matches all 1920 frozen point queries")


if __name__ == "__main__":
    main()
