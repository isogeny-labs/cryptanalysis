#!/usr/bin/env python3
"""Check the quadratic target-support bound against the frozen census."""

import itertools
import json
import math
from pathlib import Path


def ratios(r, multiplier, length):
    powers = [pow(multiplier, j, r) for j in range(length)]
    signed = {sign*x%r for x in powers for sign in (1, -1)}
    out = set()
    for a in signed:
        for b in signed:
            for c in signed:
                out.add((a+b)*pow(c, -1, r)%r)
                if (b+c)%r:
                    out.add(a*pow((b+c)%r, -1, r)%r)
    out.discard(0)
    return out


def labelled_support(r, multiplier, length, seed1, seed2):
    labels = []
    for a, b in (seed1, seed2):
        for j in range(length):
            for sign in (1, -1):
                v = sign*pow(multiplier, j, r)%r
                labels.append((v*a%r, v*b%r))
    out = set()
    for inds in itertools.combinations_with_replacement(range(len(labels)), 3):
        A = sum(labels[i][0] for i in inds)%r
        B = sum(labels[i][1] for i in inds)%r
        if B:
            d = -A*pow(B, -1, r)%r
            if d:
                out.add(d)
    return out


def main():
    r, multiplier, length = 61, 7, 3
    u_set = ratios(r, multiplier, length)
    actual = labelled_support(r, multiplier, length, (1, 0), (0, 1))
    observed = json.loads(Path(__file__).with_name(
        "two_seed_orbit_results.json").read_text())
    observed_support = {row["d"] for row in observed["records"]
                        if row["informative_relations"]}
    assert actual == {-u%r for u in u_set} == observed_support
    assert len(actual) == 46 <= 8*length*(2*length-1)

    seed1, seed2 = (1, 1), (2, 3)
    assert (seed1[0]*seed2[1]-seed2[0]*seed1[1])%r
    transformed = labelled_support(r, multiplier, length, seed1, seed2)
    exceptions = {d for d in range(1, r)
                  if (seed1[0]+seed1[1]*d)%r == 0
                  or (seed2[0]+seed2[1]*d)%r == 0}
    predicted = set()
    for u in u_set:
        denominator = (seed1[1]*u+seed2[1])%r
        if denominator:
            d = -(seed1[0]*u+seed2[0])*pow(denominator, -1, r)%r
            if d:
                predicted.add(d)
    assert transformed-exceptions == predicted-exceptions
    assert len(transformed-exceptions) <= 8*length*(2*length-1)

    p192_r = 6277101735386680763835789423176059013767194773182842284081
    max_length = 1 << 43
    cap = 8*max_length*(2*max_length-1)+2
    half_success_attempts = ((p192_r-1)+2*cap-1)//(2*cap)
    rho = math.sqrt(math.pi*p192_r/4)
    assert half_success_attempts > rho
    print("D-19 support", len(actual), "of", r-1)
    print("transformed support", len(transformed-exceptions),
          "nondegenerate; exceptions", sorted(exceptions))
    print("P-192 log2 support cap", math.log2(cap))
    print("P-192 log2 attempts for 50% coverage", math.log2(half_success_attempts))
    print("P-192 log2 rho reference", math.log2(rho))


if __name__ == "__main__":
    main()
