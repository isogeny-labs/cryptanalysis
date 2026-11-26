#!/usr/bin/env python3
"""Enumerate short multiplicative-orbit blocks of split genus-two fibers."""

import json

from toy_jacobian import GenusTwo


PRIME = 101
FOLDING = 3


def prime_factors(value):
    factors = []
    divisor = 2
    while divisor * divisor <= value:
        if value % divisor == 0:
            factors.append(divisor)
            while value % divisor == 0:
                value //= divisor
        divisor += 1
    if value > 1:
        factors.append(value)
    return factors


def primitive_root(prime):
    factors = prime_factors(prime - 1)
    return next(
        value
        for value in range(2, prime)
        if all(pow(value, (prime - 1) // factor, prime) != 1 for factor in factors)
    )


def main():
    curve = GenusTwo(PRIME)
    gamma = primitive_root(PRIME)
    blocks = []
    seen = set()
    for start in range(1, PRIME):
        xs = tuple(start * pow(gamma, index, PRIME) % PRIME for index in range(FOLDING))
        if len(set(xs)) < FOLDING or not all(len(curve.roots(x)) == 2 for x in xs):
            continue
        key = tuple(sorted(xs))
        if key in seen:
            continue
        seen.add(key)
        blocks.append({
            "start": start,
            "abscissae": xs,
            "branch_tuples": 2**FOLDING,
        })
    result = {
        "prime": PRIME,
        "genus": 2,
        "folding": FOLDING,
        "primitive_root": gamma,
        "nonzero_starts": PRIME - 1,
        "heuristic_split_starts": (PRIME - 1) / 2**FOLDING,
        "distinct_split_orbit_blocks": len(blocks),
        "blocks": blocks,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
