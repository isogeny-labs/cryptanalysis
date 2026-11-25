#!/usr/bin/env sage -python
"""Same-base S4 screen with redundant degree-5 horizontal endpoint equations.

Run: /Volumes/SSD990/cryptanalysis/sage -python research/cm_joint_s4_20261123/panel.py --repeats 11
Every arm uses the same eight signed source points and natural query stream.
This is a component test; its exact point checks do not time witness extraction.
"""

import argparse
import json
import random
import statistics
import time

from sage.all import EllipticCurve, GF, PolynomialRing, prod

P, R, SECRET, SEED = 1009, 1069, 271, 20261123
ARMS = ("source", "endpoint", "wires", "joint", "joint_no_source")


def s3(u, v, w, a, b):
    """Third summation polynomial for y^2 = x^3 + ax + b."""
    return ((u - v)**2 * w**2
            - 2 * ((u + v) * (u * v + a) + 2 * b) * w
            + (u * v - a)**2 - 4 * b * (u + v))


def evaluate_poly(poly, x):
    return sum(poly[i] * x**i for i in range(poly.degree() + 1))


def s4_equation(xs, z, target_x, curve):
    a, b = curve.a4(), curve.a6()
    return s3(xs[0], xs[1], z, a, b).resultant(
        s3(xs[2], target_x, z, a, b), z)


def build_system(arm, field, source, phi, source_x, endpoint_x, query):
    if arm == "source":
        names = ("x1", "x2", "x3", "z")
    elif arm == "endpoint":
        names = ("u1", "u2", "u3", "v")
    elif arm == "wires":
        names = ("x1", "x2", "x3", "z", "u1", "u2", "u3")
    elif arm == "joint":
        names = ("x1", "x2", "x3", "z", "u1", "u2", "u3", "v")
    else:
        names = ("x1", "x2", "x3", "u1", "u2", "u3", "v")
    ring = PolynomialRing(field, names=names, order="degrevlex")
    vars = ring.gens()
    equations = []
    if arm == "source":
        xs, z = vars[:3], vars[3]
        equations.append(s4_equation(xs, z, query[0], source))
        equations.extend(prod(x - field(c) for c in source_x) for x in xs)
    elif arm == "endpoint":
        us, v = vars[:3], vars[3]
        equations.append(s4_equation(us, v, phi(query)[0], phi.codomain()))
        equations.extend(prod(u - field(c) for c in endpoint_x) for u in us)
    else:
        xs = vars[:3]
        if arm in ("wires", "joint"):
            z, us = vars[3], vars[4:7]
            equations.append(s4_equation(xs, z, query[0], source))
        else:
            us = vars[3:6]
        equations.extend(prod(x - field(c) for c in source_x) for x in xs)
        rational_map = phi.x_rational_map()
        numerator, denominator = rational_map.numerator(), rational_map.denominator()
        equations.extend(evaluate_poly(numerator, x) - u * evaluate_poly(denominator, x)
                         for x, u in zip(xs, us))
        if arm in ("joint", "joint_no_source"):
            v = vars[-1]
            equations.append(s4_equation(us, v, phi(query)[0], phi.codomain()))
    return ring, equations


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    field = GF(P)
    source = EllipticCurve(field, [4, 10])
    assert int(source.cardinality()) == R
    started = time.perf_counter()
    phi = source.isogenies_prime_degree(5)[0]
    map_construction_seconds = time.perf_counter() - started
    generator = source.gens()[0]
    target = SECRET * generator
    base = sorted((point for point in source.points() if not point.is_zero()),
                  key=lambda point: (int(phi(point)[0]), int(phi(point)[1])))[:8]
    assert all(-point in base for point in base)
    base_set = set(base)
    source_x = sorted({int(point[0]) for point in base})
    endpoint_x = sorted({int(phi(point)[0]) for point in base})
    assert len(source_x) == len(endpoint_x) == 4
    rng = random.Random(SEED)
    queries = []
    counts = {True: 0, False: 0}
    for trial in range(1, R):
        a, b = rng.randrange(R), rng.randrange(1, R)
        query = a * generator + b * target
        if query.is_zero():
            continue
        triple = next(((x, y, query - x - y) for x in base for y in base
                       if query - x - y in base_set), None)
        truth = triple is not None
        if counts[truth] == 2:
            continue
        counts[truth] += 1
        queries.append((trial, a, b, query, truth, triple))
        if counts[True] == counts[False] == 2:
            break
    assert len(queries) == 4
    records = []
    for trial, a, b, query, truth, triple in queries:
        builds = {}
        for arm in ARMS:
            started = time.perf_counter()
            ring, equations = build_system(
                arm, field, source, phi, source_x, endpoint_x, query)
            builds[arm] = (ring, equations, time.perf_counter() - started)
        # Interleave rounds so warm-up/order effects do not favor one arm.
        timings = {arm: [] for arm in ARMS}
        sat = {}
        for repeat in range(args.repeats):
            order = list(ARMS)
            random.Random(SEED + trial + repeat).shuffle(order)
            for arm in order:
                ring, equations, _ = builds[arm]
                started = time.perf_counter()
                basis = ring.ideal(equations).groebner_basis()
                timings[arm].append(time.perf_counter() - started)
                value = ring.one() not in basis
                assert value == truth, (arm, trial, truth, value)
                sat[arm] = value
        records.append({
            "trial": trial, "a": a, "b": b, "truth": truth,
            "query_x": int(query[0]),
            "witness_x": None if triple is None else [int(point[0]) for point in triple],
            "arms": {arm: {
                "variables": builds[arm][0].ngens(),
                "equations": len(builds[arm][1]),
                "build_seconds": round(builds[arm][2], 6),
                "solve_median_seconds": round(statistics.median(timings[arm]), 6),
                "solve_range_seconds": [round(min(timings[arm]), 6),
                                        round(max(timings[arm]), 6)],
                "sat": sat[arm],
            } for arm in ARMS},
        })
    print(json.dumps({
        "p": P, "r": R, "base_signed_size": len(base),
        "base_source_x": source_x, "map_degree": 5,
        "map_construction_seconds": round(map_construction_seconds, 6),
        "repeats": args.repeats, "records": records,
        "sum_query_solve_medians_seconds": {
            arm: round(sum(row["arms"][arm]["solve_median_seconds"] for row in records), 6)
            for arm in ARMS},
        "scope": "Natural balanced four-query S4 component panel with exact group truth; no full relation collection, rank, descent, or rho timing.",
    }, sort_keys=True))


if __name__ == "__main__":
    main()
