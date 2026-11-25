#!/usr/bin/env python3
"""Exact eight-point native-base three-sum census for the fixed F_1009 pair."""

import itertools
import json
import random
import statistics

P = 1009
R = 1069
SEED = 20261125
ARMS = 128
CURVES = (("source", 4, 10), ("codomain", 888, 852))


def neg(point):
    if point is None:
        return None
    return (point[0], -point[1] % P)


def add(left, right, a):
    if left is None:
        return right
    if right is None:
        return left
    x1, y1 = left
    x2, y2 = right
    if x1 == x2 and (y1 + y2) % P == 0:
        return None
    if x1 == x2:
        slope = (3 * x1 * x1 + a) * pow(2 * y1, -1, P) % P
    else:
        slope = (y2 - y1) * pow(x2 - x1, -1, P) % P
    x3 = (slope * slope - x1 - x2) % P
    return (x3, (slope * (x1 - x3) - y1) % P)


def multiply(n, point, a):
    out = None
    while n:
        if n & 1:
            out = add(out, point, a)
        point = add(point, point, a)
        n >>= 1
    return out


def x_orbits(a, b):
    square_roots = {}
    for y in range(P):
        square_roots.setdefault(y * y % P, []).append(y)
    orbits = []
    for x in range(P):
        ys = square_roots.get((x * x * x + a * x + b) % P, ())
        if ys:
            assert len(ys) == 2  # group order is odd
            orbits.append(tuple((x, y) for y in ys))
    return orbits


def support(base, a):
    sums = set()
    for triple in itertools.combinations_with_replacement(base, 3):
        total = add(add(triple[0], triple[1], a), triple[2], a)
        if total is not None:
            sums.add(total)
    return len(sums)


def census(name, a, b):
    assert (4 * a**3 + 27 * b**2) % P != 0
    orbits = x_orbits(a, b)
    points = [point for orbit in orbits for point in orbit]
    assert len(points) == R - 1 and len(orbits) == (R - 1) // 2
    for point in points:
        assert add(point, neg(point), a) is None
        assert multiply(R, point, a) is None
    native_base = [point for orbit in orbits[:4] for point in orbit]
    native = support(native_base, a)
    rng = random.Random(SEED)
    controls = []
    for _ in range(ARMS):
        chosen = rng.sample(orbits, 4)
        controls.append(support([point for orbit in chosen for point in orbit], a))
    return {
        "name": name, "a": a, "b": b,
        "native_x": [orbit[0][0] for orbit in orbits[:4]],
        "native_support": native,
        "native_hit_fraction": f"{native}/{R-1}",
        "random_support": controls,
        "random_min": min(controls),
        "random_median": statistics.median(controls),
        "random_max": max(controls),
        "random_ge_native": sum(value >= native for value in controls),
    }


def main():
    result = {
        "schema": "native-three-sum/v1", "p": P, "r": R,
        "seed": SEED, "random_arms_per_curve": ARMS,
        "curves": [census(*curve) for curve in CURVES],
    }
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
