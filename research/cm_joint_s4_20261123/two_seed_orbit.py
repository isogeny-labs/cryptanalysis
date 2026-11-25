#!/usr/bin/env sage -python
"""Frozen D=-19 two-seed horizontal-orbit relation census."""

import itertools
import json

from sage.all import EllipticCurve, GF


def point_xy(point):
    return [int(point[0]), int(point[1])]


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
        cm_entries = []
        scalar_entries = []
        for seed_name, seed, a0, b0 in (("G", G, 1, 0), ("Q", Q, 0, 1)):
            cm_point = seed
            scalar_point = seed
            for j in range(3):
                assert cm_point == scalar_point == pow(7, j, r)*seed
                a, b = a0*pow(7, j, r)%r, b0*pow(7, j, r)%r
                for sign in (1, -1):
                    cm_entries.append((sign*cm_point, sign*a%r, sign*b%r,
                                       seed_name, j, sign))
                    scalar_entries.append((sign*scalar_point, sign*a%r,
                                           sign*b%r, seed_name, j, sign))
                cm_point = w(cm_point)
                scalar_point = 7*scalar_point
        assert cm_entries == scalar_entries and len(cm_entries) == 12
        assert all(P == a*G+b*Q for P,a,b,_,_,_ in cm_entries)

        zero_count = 0
        informative_count = 0
        first = None
        for indices in itertools.combinations_with_replacement(range(12), 3):
            chosen = [cm_entries[i] for i in indices]
            if not sum((row[0] for row in chosen), E(0)).is_zero():
                continue
            zero_count += 1
            A = sum(row[1] for row in chosen)%r
            B = sum(row[2] for row in chosen)%r
            assert (A*G+B*Q).is_zero() and (A+B*d)%r == 0
            if B:
                informative_count += 1
                recovered = -A*pow(B, -1, r)%r
                assert recovered == d and recovered*G == Q
                if first is None:
                    first = {"indices": list(indices), "A": A, "B": B,
                             "recovered": recovered,
                             "points": [point_xy(row[0]) for row in chosen],
                             "labels": [[row[1], row[2]] for row in chosen]}
            else:
                assert A == 0
        records.append({"d": d, "Q": point_xy(Q),
                        "distinct_points": len({row[0] for row in cm_entries}),
                        "zero_relations": zero_count,
                        "informative_relations": informative_count,
                        "first_informative": first})
    output = {"schema": "two-seed-orbit/v1", "p": 47, "r": r,
              "curve": [1, 38], "G": point_xy(G), "lambda": 7,
              "orbit_length": 3, "indexed_base_size": 12,
              "triples_per_target": 364,
              "all_targets": len(records),
              "informative_targets": sum(bool(row["informative_relations"])
                                         for row in records),
              "d3": records[2], "records": records}
    print(json.dumps(output, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
