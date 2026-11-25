#!/usr/bin/env python3
"""Replay exponent-shift support and the materialized-base cost gate."""

import itertools
import json
import math
from pathlib import Path


def choose3(n):
    return math.comb(n+2, 3)


def ceiling(blocks, length):
    n = 2*blocks
    return choose3(n*length)-choose3(n*(length-1))


def support(order, multiplier, length, seeds, min_zero_only=False):
    entries = []
    for a, b in seeds:
        for j in range(length):
            for sign in (1, -1):
                power = sign*pow(multiplier, j, order)%order
                entries.append((power*a%order, power*b%order, j))
    found = set()
    representatives = 0
    for indices in itertools.combinations_with_replacement(
            range(len(entries)), 3):
        selected = [entries[i] for i in indices]
        if min_zero_only and min(row[2] for row in selected) != 0:
            continue
        representatives += 1
        A = sum(row[0] for row in selected)%order
        B = sum(row[1] for row in selected)%order
        if B:
            d = -A*pow(B, -1, order)%order
            if d:
                found.add(d)
    return found, representatives


def main():
    frozen = json.loads(Path(__file__).with_name(
        "two_seed_orbit_results.json").read_text())
    expected = {row["d"] for row in frozen["records"]
                if row["informative_relations"]}
    cases = [
        ("frozen-D19", 61, 7, 3, [(1, 0), (0, 1)]),
        ("three-block", 1069, 31, 3, [(1, 0), (0, 1), (1, 1)]),
    ]
    for name, r, lam, length, seeds in cases:
        full, total = support(r, lam, length, seeds)
        shifted, normalized = support(r, lam, length, seeds, True)
        assert full == shifted
        assert total == choose3(2*len(seeds)*length)
        assert normalized == ceiling(len(seeds), length)
        assert len(full) <= normalized
        if name == "frozen-D19":
            assert full == expected and len(full) == 46
        print(name, "support", len(full), "full triples", total,
              "shift-normalized triples", normalized)

    r = 6277101735386680763835789423176059013767194773182842284081
    max_points = 1 << 45
    # 3.14159 < pi < 3.14160: certify the crossover by integer arithmetic.
    def scaled_comparison(blocks):
        length = max_points//(2*blocks)
        cap = ceiling(blocks, length)
        lhs = (r-1)**2*100000
        upper = 314160*r*cap*cap
        lower = 314159*r*cap*cap
        return length, cap, lhs, lower, upper

    for blocks in range(2, 37):
        _, _, lhs, _, upper = scaled_comparison(blocks)
        assert lhs > upper
    length, cap, lhs, lower, _ = scaled_comparison(37)
    assert lhs < lower
    rho = math.sqrt(math.pi*r/4)
    for blocks in (2, 5, 16, 32, 36, 37, 64):
        length, cap, _, _, _ = scaled_comparison(blocks)
        half_coverage = (r-1)/(2*cap)
        print("P-192", blocks, "blocks", "L", length,
              "log2 cap", round(math.log2(cap), 3),
              "log2 half-cover tests", round(math.log2(half_coverage), 3),
              "ratio-to-rho", round(half_coverage/rho, 3))
    print("first non-excluded block count at one equivalent/test: 37")


if __name__ == "__main__":
    main()
