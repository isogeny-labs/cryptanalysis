#!/usr/bin/env sage -python
"""Independent Sage census of all N41 shared-seed quartet output sets."""

import hashlib
import itertools
import json
import resource
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / "n41_same_seed_derivative_collapse_20261011"
GEOMETRY = ROOT / "n41_two_free_pair_occupancy_20261009/geometry_snapshot.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def lift(F, value):
    t = F.gen()
    out = F.zero()
    index = 0
    while value:
        if value & 1:
            out += t**index
        index += 1
        value >>= 1
    return out


def encode(value):
    return sum(int(coefficient) << index
               for index, coefficient in enumerate(value.polynomial()))


def key(point):
    if not point:
        return None
    return (encode(point[0]), encode(point[1]))


def main():
    p = json.loads((HERE / "protocol_v2.json").read_text())
    assert p["status"] == "FROZEN_SAGE_N41_SHARED_SEED_AUDIT_V2"
    assert p["sha256"] == {"audit": sha(__file__),
                           "geometry": sha(GEOMETRY),
                           "producer": sha(PRIOR / "result_v2.json"),
                           "runtime": sha(HERE / "sage_runtime_info.json")}
    producer = json.loads((PRIOR / "result_v2.json").read_text())
    expected = producer["rotations"]["0"]
    geometry = json.loads(GEOMETRY.read_text())["n41"]
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    F = GF(2**41, "t", modulus=t**41 + t**3 + 1)
    E = EllipticCurve(F, [1, 0, 0, 0, 1])
    start = time.monotonic_ns()
    points = {}
    columns = {}
    negative = {}
    for x, y, column, mask, branch, sign in geometry["point_rows_by_unique_rotation"]["0"]:
        assert branch == 0
        point = E(lift(F, x), lift(F, y))
        columns[mask] = column
        (points if sign == 0 else negative)[mask] = point
    assert len(points) == len(negative) == 32
    assert all(negative[mask] == -points[mask] for mask in points)
    assert len(set(columns.values())) == 26
    edges_by_seed = {}
    edge_sums = {}
    for seed in range(1, 64):
        edges = [(a, a ^ seed) for a in sorted(points)
                 if a < (a ^ seed) and (a ^ seed) in points
                 and columns[a] != columns[a ^ seed]]
        edges_by_seed[seed] = edges
        for a, b in edges:
            pa, pb = points[a], points[b]
            edge_sums[(a, b)] = [pa + pb, pa - pb, -pa + pb, -pa - pb]
    sign0_by_key = defaultdict(set)
    full_by_key = defaultdict(set)
    quartets_by_key = defaultdict(list)
    individual_total = 0
    individual_sizes = Counter()
    for seed, edges in edges_by_seed.items():
        if (time.monotonic_ns() - start) / 1e9 >= p["cap_seconds"]:
            raise TimeoutError("Sage audit reached frozen 120-second cap")
        for (a, b), (c, d) in itertools.combinations(edges, 2):
            if len({a, b, c, d}) < 4 or len({columns[v] for v in (a, b, c, d)}) < 4:
                continue
            difference = min(a ^ c, a ^ c ^ seed)
            family = (seed, difference)
            left, right = edge_sums[(a, b)], edge_sums[(c, d)]
            sign0_by_key[family].add(key(left[0] + right[0]))
            outputs = {key(P + Q) for P in left for Q in right}
            assert len(outputs) == 16
            full_by_key[family].update(outputs)
            quartets_by_key[family].append(((a, b, c, d), outputs))
            individual_total += len(outputs)
            individual_sizes[len(outputs)] += 1
    repeated = [family for family, rows in quartets_by_key.items() if len(rows) > 1]
    got = {"source_quartets": sum(len(rows) for rows in quartets_by_key.values()),
           "seed_difference_keys": len(quartets_by_key),
           "repeated_keys": len(repeated),
           "quartets_per_key_histogram": {str(k): v for k, v in sorted(Counter(
               len(rows) for rows in quartets_by_key.values()).items())},
           "sign0_single_output_repeated_keys": sum(
               len(sign0_by_key[family]) == 1 for family in repeated),
           "sign0_total_distinct_by_key": sum(map(len, sign0_by_key.values())),
           "all_sign_identical_output_sets_repeated_keys": sum(
               all(rows[0][1] == other[1] for other in rows[1:])
               for family, rows in quartets_by_key.items() if len(rows) > 1),
           "all_sign_total_distinct_by_key": sum(map(len, full_by_key.values())),
           "all_sign_individual_output_total": individual_total,
           "all_sign_output_size_histogram": {str(k): v for k, v in sorted(individual_sizes.items())}}
    for name, actual in got.items():
        assert actual == expected[name], (name, actual, expected[name])
    sample = expected["example_nocollapse"]
    family = (sample["seed"], sample["difference"])
    assert sorted(list(sign0_by_key[family]))[:3] == [tuple(v) for v in sample["sign0_outputs"]]
    assert [list(q[0]) for q in quartets_by_key[family][:3]] == sample["quartets"]
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != "darwin":
        peak *= 1024
    result = {"status": "PASS_INDEPENDENT_SAGE_SHARED_SEED_CENSUS",
              "candidate_id": None, "curve_id": geometry["curve_id"],
              "checked": got, "elapsed_ns": time.monotonic_ns() - start,
              "peak_rss_bytes": peak,
              "protocol_sha256": sha(HERE / "protocol_v2.json"),
              "producer_sha256": sha(PRIOR / "result_v2.json")}
    assert result["elapsed_ns"] / 1e9 < p["cap_seconds"]
    assert peak < p["rss_cap_bytes"]
    (HERE / "sage_audit_v2.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "quartets": got["source_quartets"],
                      "repeated_keys": got["repeated_keys"],
                      "distinct_outputs": got["all_sign_total_distinct_by_key"],
                      "seconds": result["elapsed_ns"] / 1e9}))


if __name__ == "__main__":
    main()
