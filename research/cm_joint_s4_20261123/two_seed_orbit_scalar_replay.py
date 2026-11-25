#!/usr/bin/env python3
"""Independent label-arithmetic replay of the two-seed orbit census."""

import itertools
import json
from pathlib import Path


def main():
    r = 61
    path = Path(__file__).with_name("two_seed_orbit_results.json")
    observed = json.loads(path.read_text())
    assert observed["r"] == r and observed["orbit_length"] == 3
    labels = []
    for a0, b0 in ((1, 0), (0, 1)):
        for j in range(3):
            for sign in (1, -1):
                labels.append((sign*a0*pow(7, j, r)%r,
                               sign*b0*pow(7, j, r)%r))
    assert len(labels) == 12
    sums = []
    for indices in itertools.combinations_with_replacement(range(12), 3):
        A = sum(labels[i][0] for i in indices)%r
        B = sum(labels[i][1] for i in indices)%r
        sums.append((A, B))
    assert len(sums) == 364
    informative_targets = 0
    for record in observed["records"]:
        d = record["d"]
        zero = [(A, B) for A, B in sums if (A+B*d)%r == 0]
        informative = [(A, B) for A, B in zero if B]
        assert len(zero) == record["zero_relations"]
        assert len(informative) == record["informative_relations"]
        informative_targets += bool(informative)
        if record["first_informative"] is not None:
            first = record["first_informative"]
            assert (first["A"], first["B"]) in informative
            assert -first["A"]*pow(first["B"], -1, r)%r == d
    assert informative_targets == observed["informative_targets"] == 46
    print("60 target counts replayed; 46 informative targets")


if __name__ == "__main__":
    main()
