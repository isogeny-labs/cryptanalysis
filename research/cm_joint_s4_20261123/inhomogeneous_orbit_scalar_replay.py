#!/usr/bin/env python3
"""Independent coefficient replay of all frozen target-sum queries."""

import itertools
import json
from pathlib import Path


QUERY_PAIRS = (
    (54, 59), (0, 21), (28, 36), (15, 3), (33, 26), (11, 43),
    (30, 49), (7, 20), (60, 40), (28, 54), (48, 4), (55, 40),
    (57, 55), (40, 49), (19, 56), (40, 55), (47, 3), (1, 40),
    (18, 59), (46, 42), (36, 12), (39, 6), (15, 18), (27, 43),
    (20, 50), (15, 24), (23, 45), (17, 49), (37, 51),
    (20, 2), (51, 49), (48, 21),
)


def main():
    r = 61
    path = Path(__file__).with_name("inhomogeneous_orbit_results.json")
    result = json.loads(path.read_text())
    assert [tuple(row) for row in result["query_pairs"]] == list(QUERY_PAIRS)
    labels = []
    for a0, b0 in ((1, 0), (0, 1)):
        for j in range(3):
            for sign in (1, -1):
                v = sign*pow(7, j, r)%r
                labels.append((v*a0%r, v*b0%r))
    triples = []
    for inds in itertools.combinations_with_replacement(range(12), 3):
        triples.append((sum(labels[i][0] for i in inds)%r,
                        sum(labels[i][1] for i in inds)%r,
                        list(inds)))
    assert len(triples) == 364 and len(result["records"]) == 60
    informative_query_total = 0
    for record in result["records"]:
        d = record["d"]
        assert len(record["queries"]) == len(QUERY_PAIRS)
        informative_for_d = 0
        for (a,b), row in zip(QUERY_PAIRS, record["queries"]):
            assert (a,b) == (row["a"], row["b"])
            matches = [(A,B,inds) for A,B,inds in triples
                       if (A+B*d-a-b*d)%r == 0]
            informative = [(A,B,inds) for A,B,inds in matches
                           if (B-b)%r]
            assert len(matches) == row["matches"]
            assert len(informative) == row["informative_matches"]
            if informative:
                informative_for_d += 1
                first = row["first_informative"]
                assert (first["A"],first["B"],first["indices"]) == informative[0]
                C,D = first["relation"]
                assert (C,D) == ((first["A"]-a)%r,(first["B"]-b)%r)
                assert -C*pow(D,-1,r)%r == first["recovered"] == d
            else:
                assert row["first_informative"] is None
        assert informative_for_d == record["informative_queries"]
        informative_query_total += informative_for_d
    assert informative_query_total == 1884
    assert result["d3"]["informative_queries"] == 31
    print("1920 query counts replayed; 1884 informative; d=3: 31/32")


if __name__ == "__main__":
    main()
