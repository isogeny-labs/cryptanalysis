#!/usr/bin/env sage -python
"""Frozen equal-yield mixed-base S4 solve-cost panel."""

import argparse
import gzip
import itertools
import json
import random
import statistics
import time

from sage.all import EllipticCurve, GF

from panel import build_system


P = 1009
R = 1069
TARGET_SCALAR_PUBLIC_FIXTURE = 271
QUERY_SEEDS = (20261129, 20261130)
ROWS_PER_SEED = 32
REPEATS = 5
SCALE_SEED = 20261129
RANDOM_BASE_SEED = 20261130
ARMS = ("source_a", "source_b", "mixed", "random_1", "random_2")


def signed_orbits(curve):
    by_x = {}
    for point in curve.points():
        if not point.is_zero():
            by_x.setdefault(int(point[0]), []).append(point)
    assert all(len(orbit) == 2 and orbit[0] == -orbit[1]
               for orbit in by_x.values())
    return [by_x[x] for x in sorted(by_x)]


def support(curve, base):
    return {sum(triple, curve(0))
            for triple in itertools.combinations_with_replacement(base, 3)} - {curve(0)}


def inputs():
    field = GF(P)
    source = EllipticCurve(field, [4, 10])
    phi = source.isogenies_prime_degree(5)[0]
    endpoint = phi.codomain()
    assert int(source.cardinality()) == int(endpoint.cardinality()) == R
    assert tuple(int(c) for c in endpoint.a_invariants()) == (0, 0, 0, 888, 852)
    source_orbits = signed_orbits(source)
    endpoint_orbits = signed_orbits(endpoint)
    source_base = sum(source_orbits[:4], [])
    mixed_base = sum(source_orbits[:2], [])
    inv5 = pow(5, -1, R)
    dual = phi.dual()
    for orbit in endpoint_orbits[:2]:
        for point in orbit:
            pulled = inv5 * dual(point)
            assert phi(pulled) == point
            mixed_base.append(pulled)
    assert len(set(mixed_base)) == 8
    bases = {"source_a": source_base, "source_b": source_base,
             "mixed": mixed_base}
    excluded = {frozenset(source_base), frozenset(mixed_base)}
    rng = random.Random(RANDOM_BASE_SEED)
    while len(bases) < len(ARMS):
        candidate = sum(rng.sample(source_orbits, 4), [])
        key = frozenset(candidate)
        if key not in excluded and len(support(source, candidate)) == 96:
            bases[f"random_{len(bases)-2}"] = candidate
            excluded.add(key)
    base_x = {arm: sorted({int(point[0]) for point in base})
              for arm, base in bases.items()}
    assert base_x["source_a"] == base_x["source_b"] == [0, 1, 3, 4]
    assert base_x["mixed"] == [0, 1, 478, 742]
    supports = {arm: support(source, base) for arm, base in bases.items()}
    assert all(len(s) == 96 for s in supports.values())
    assert all(len(base_x[arm]) == 4 for arm in ARMS)
    scales = (1, *random.Random(SCALE_SEED).sample(range(2, P), 2))
    return field, source, phi, bases, base_x, supports, scales


def queries(source):
    generator = source.gens()[0]
    target = TARGET_SCALAR_PUBLIC_FIXTURE * generator
    output = []
    for seed in QUERY_SEEDS:
        rng = random.Random(seed)
        accepted = 0
        draws = 0
        while accepted < ROWS_PER_SEED:
            a, b = rng.randrange(R), rng.randrange(1, R)
            draws += 1
            point = a * generator + b * target
            if point.is_zero():
                continue
            output.append((seed, accepted, draws, a, b, point))
            accepted += 1
    return output


def scaled_curve(field, scale):
    return EllipticCurve(field, [4*field(scale)**4, 10*field(scale)**6])


def scaled_point(curve, point, scale):
    field = curve.base_field()
    return curve(field(scale)**2*point[0], field(scale)**3*point[1])


def run(output_path):
    process_started_wall = time.perf_counter_ns()
    process_started_cpu = time.process_time_ns()
    setup_started = time.perf_counter_ns()
    field, source, phi, bases, base_x, supports, scales = inputs()
    setup_ns = time.perf_counter_ns() - setup_started
    query_rows = queries(source)
    records = []
    for scale in scales:
        curve = scaled_curve(field, scale)
        xs = {arm: sorted({int(field(scale)**2*field(x)) for x in base_x[arm]})
              for arm in ARMS}
        assert all(len(xs[arm]) == 4 for arm in ARMS)
        for seed, index, draw, a, b, source_point in query_rows:
            point = scaled_point(curve, source_point, scale)
            truth = {arm: source_point in supports[arm] for arm in ARMS}
            systems = {}
            for arm in ARMS:
                start_wall = time.perf_counter_ns()
                start_cpu = time.process_time_ns()
                ring, equations = build_system(
                    "source", field, curve, None, xs[arm], (), point)
                systems[arm] = (ring, equations,
                                time.perf_counter_ns()-start_wall,
                                time.process_time_ns()-start_cpu)
            samples = {arm: [] for arm in ARMS}
            for repeat in range(REPEATS):
                order = list(ARMS)
                random.Random(seed + 10000*scale + 100*index + repeat).shuffle(order)
                for arm in order:
                    ring, equations, _, _ = systems[arm]
                    start_wall = time.perf_counter_ns()
                    start_cpu = time.process_time_ns()
                    basis = ring.ideal(equations).groebner_basis()
                    cpu_ns = time.process_time_ns()-start_cpu
                    wall_ns = time.perf_counter_ns()-start_wall
                    sat = ring.one() not in basis
                    assert sat == truth[arm], (seed, index, scale, arm, truth[arm], sat)
                    samples[arm].append((wall_ns, cpu_ns, int(sat)))
            records.append({
                "scale": scale, "seed": seed, "index": index,
                "draw": draw, "a": a, "b": b,
                "source_x": int(source_point[0]),
                "arms": {arm: {
                    "truth": int(truth[arm]),
                    "build_wall_ns": systems[arm][2],
                    "build_cpu_ns": systems[arm][3],
                    "samples_wall_cpu_sat": samples[arm],
                } for arm in ARMS},
            })

    def metric(scale, arm, clock, seed=None):
        rows = (row for row in records if row["scale"] == scale
                and (seed is None or row["seed"] == seed))
        return sum(statistics.median(sample[clock]
                   for sample in row["arms"][arm]["samples_wall_cpu_sat"])
                   for row in rows)

    summary = {
        "schema": "mixed-equal-yield-cost/v1", "p": P, "r": R,
        "target_scalar_public_fixture": TARGET_SCALAR_PUBLIC_FIXTURE,
        "query_seeds": QUERY_SEEDS, "rows_per_seed": ROWS_PER_SEED,
        "repeats": REPEATS, "scales": scales, "base_x": base_x,
        "support": {arm: len(supports[arm]) for arm in ARMS},
        "setup_wall_ns": setup_ns,
        "sum_query_median_ns": {
            str(scale): {arm: {"wall": metric(scale, arm, 0),
                              "cpu": metric(scale, arm, 1),
                              "cpu_by_seed": {str(seed): metric(scale, arm, 1, seed)
                                              for seed in QUERY_SEEDS}}
                         for arm in ARMS}
            for scale in scales},
        "positive_rows": {str(scale): {arm: sum(row["arms"][arm]["truth"]
                          for row in records if row["scale"] == scale)
                          for arm in ARMS} for scale in scales},
        "total_process_wall_ns": time.perf_counter_ns()-process_started_wall,
        "total_process_cpu_ns": time.process_time_ns()-process_started_cpu,
    }
    payload = {"summary": summary, "records": records}
    with gzip.open(output_path, "wt", encoding="utf-8", compresslevel=9) as out:
        json.dump(payload, out, sort_keys=True, separators=(",", ":"))
    print(json.dumps(summary, sort_keys=True, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run(args.output)
