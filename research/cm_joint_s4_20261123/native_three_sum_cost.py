#!/usr/bin/env sage -python
"""Frozen paired S4 component timing for the two native F_1009 bases."""

import itertools
import json
import random
import statistics
import time

from sage.all import EllipticCurve, GF

from panel import build_system

P = 1009
R = 1069
SECRET = 271
SEED = 20261125
ROWS = 64
REPEATS = 7
ARMS = ("source", "endpoint")


def native_base(curve):
    base = sorted((point for point in curve.points() if not point.is_zero()),
                  key=lambda point: (int(point[0]), int(point[1])))[:8]
    assert len(base) == 8 and all(-point in base for point in base)
    return base, sorted({int(point[0]) for point in base})


def support(base):
    return {sum(triple[1:], triple[0])
            for triple in itertools.combinations_with_replacement(base, 3)}


def main():
    process_started = time.perf_counter()
    field = GF(P)
    source = EllipticCurve(field, [4, 10])
    assert int(source.cardinality()) == R
    started = time.perf_counter()
    phi = source.isogenies_prime_degree(5)[0]
    map_seconds = time.perf_counter() - started
    endpoint = phi.codomain()
    assert int(endpoint.cardinality()) == R
    assert tuple(int(c) for c in endpoint.a_invariants()) == (0, 0, 0, 888, 852)
    started = time.perf_counter()
    source_base, source_x = native_base(source)
    endpoint_base, endpoint_x = native_base(endpoint)
    source_support = support(source_base)
    endpoint_support = support(endpoint_base)
    base_seconds = time.perf_counter() - started
    assert source_x == [0, 1, 3, 4] and endpoint_x == [0, 2, 4, 7]
    assert len(source_support - {source(0)}) == 96
    assert len(endpoint_support - {endpoint(0)}) == 92

    generator = source.gens()[0]
    target = SECRET * generator
    rng = random.Random(SEED)
    queries = []
    draws = 0
    while len(queries) < ROWS:
        a, b = rng.randrange(R), rng.randrange(1, R)
        draws += 1
        query = a * generator + b * target
        if not query.is_zero():
            queries.append((a, b, query))

    records = []
    for i, (a, b, query) in enumerate(queries):
        endpoint_query = phi(query)
        truth = {"source": query in source_support,
                 "endpoint": endpoint_query in endpoint_support}
        builds = {}
        for arm in ARMS:
            started = time.perf_counter()
            ring, equations = build_system(
                arm, field, source, phi, source_x, endpoint_x, query)
            builds[arm] = (ring, equations, time.perf_counter() - started)
        times = {arm: [] for arm in ARMS}
        sat = {}
        for repeat in range(REPEATS):
            order = list(ARMS)
            random.Random(SEED + 100 * i + repeat).shuffle(order)
            for arm in order:
                ring, equations, _ = builds[arm]
                started = time.perf_counter()
                basis = ring.ideal(equations).groebner_basis()
                times[arm].append(time.perf_counter() - started)
                verdict = ring.one() not in basis
                if arm in sat:
                    assert sat[arm] == verdict
                sat[arm] = verdict
        records.append({
            "index": i, "a": a, "b": b,
            "source_x": int(query[0]), "endpoint_x": int(endpoint_query[0]),
            "arms": {arm: {
                "truth": truth[arm], "algebraic_sat": sat[arm],
                "build_seconds": builds[arm][2],
                "solve_seconds": times[arm],
                "solve_median_seconds": statistics.median(times[arm]),
            } for arm in ARMS},
        })

    result = {
        "schema": "native-three-sum-cost/v1", "p": P, "r": R,
        "secret_public_fixture": SECRET, "seed": SEED, "draws": draws,
        "rows": ROWS, "repeats": REPEATS,
        "source_base_x": source_x, "endpoint_base_x": endpoint_x,
        "map_construction_seconds": map_seconds,
        "base_construction_seconds": base_seconds,
        "sum_build_seconds": {
            arm: sum(row["arms"][arm]["build_seconds"] for row in records)
            for arm in ARMS},
        "sum_solve_medians_seconds": {
            arm: sum(row["arms"][arm]["solve_median_seconds"] for row in records)
            for arm in ARMS},
        "exact_positive_rows": {
            arm: sum(row["arms"][arm]["truth"] for row in records)
            for arm in ARMS},
        "truth_mismatch_rows": {
            arm: [row["index"] for row in records
                  if row["arms"][arm]["truth"] != row["arms"][arm]["algebraic_sat"]]
            for arm in ARMS},
        "records": records,
        "process_wall_seconds": time.perf_counter() - process_started,
    }
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
