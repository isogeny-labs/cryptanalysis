#!/usr/bin/env sage -python
"""Frozen target-sum queries against a D=-19 two-seed CM orbit base."""

import itertools
import json

from sage.all import EllipticCurve, GF


QUERY_PAIRS = (
    (54, 59), (0, 21), (28, 36), (15, 3), (33, 26), (11, 43),
    (30, 49), (7, 20), (60, 40), (28, 54), (48, 4), (55, 40),
    (57, 55), (40, 49), (19, 56), (40, 55), (47, 3), (1, 40),
    (18, 59), (46, 42), (36, 12), (39, 6), (15, 18), (27, 43),
    (20, 50), (15, 24), (23, 45), (17, 49), (37, 51),
    (20, 2), (51, 49), (48, 21),
)


def xy(point):
    return None if point.is_zero() else [int(point[0]), int(point[1])]


def query_matches(triples, target, a, b, r):
    matches = []
    informative = []
    for point, A, B, indices, coords in triples:
        if point != target:
            continue
        matches.append(indices)
        C, D = (A-a)%r, (B-b)%r
        if D:
            informative.append({"indices": indices, "A": A, "B": B,
                                "relation": [C, D], "points": coords,
                                "recovered": -C*pow(D, -1, r)%r})
        else:
            assert C == 0
    return matches, informative


def main():
    r = 61
    E = EllipticCurve(GF(47), [1, 38])
    G = E(2, 1)
    assert int(E.cardinality()) == r and int(G.order()) == r
    edge = E.isogenies_prime_degree(5)[0]
    iso = next(f for f in edge.codomain().isomorphisms(E)
               if f(edge(G)) == 7*G)

    def w(point):
        return iso(edge(point))

    records = []
    for d in range(1, r):
        Q = d*G
        entries = []
        native = []
        for seed, a0, b0 in ((G, 1, 0), (Q, 0, 1)):
            cm_point = seed
            native_point = seed
            for j in range(3):
                assert cm_point == native_point
                a, b = a0*pow(7, j, r)%r, b0*pow(7, j, r)%r
                for sign in (1, -1):
                    entries.append((sign*cm_point, sign*a%r, sign*b%r))
                    native.append((sign*native_point, sign*a%r, sign*b%r))
                cm_point = w(cm_point)
                native_point = 7*native_point
        assert entries == native and len(entries) == 12
        assert all(point == a*G+b*Q for point,a,b in entries)
        triples = []
        for indices in itertools.combinations_with_replacement(range(12), 3):
            chosen = [entries[i] for i in indices]
            point = sum((row[0] for row in chosen), E(0))
            A = sum(row[1] for row in chosen)%r
            B = sum(row[2] for row in chosen)%r
            assert point == A*G+B*Q
            triples.append((point, A, B, list(indices),
                            [xy(row[0]) for row in chosen]))
        assert len(triples) == 364

        rows = []
        for a,b in QUERY_PAIRS:
            R = a*G+b*Q
            matches, informative = query_matches(triples, R, a, b, r)
            assert all(row["recovered"] == d and d*G == Q
                       for row in informative)
            rows.append({"a": a, "b": b, "R": xy(R),
                         "matches": len(matches),
                         "informative_matches": len(informative),
                         "first_informative": informative[0]
                         if informative else None})
        records.append({"d": d, "Q": xy(Q), "queries": rows,
                        "informative_queries": sum(bool(row["informative_matches"])
                                                   for row in rows)})

    print(json.dumps({"schema": "inhomogeneous-two-seed-orbit/v1",
                      "curve": [1, 38], "p": 47, "r": r, "G": xy(G),
                      "lambda": 7, "arc_length": 3,
                      "indexed_base_size": 12, "triples_per_query": 364,
                      "query_pairs": QUERY_PAIRS,
                      "d3": records[2], "records": records},
                     sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
