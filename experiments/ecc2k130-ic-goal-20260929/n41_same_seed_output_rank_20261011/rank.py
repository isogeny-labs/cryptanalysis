"""Affine ranks of exact shared-seed four-point x-coordinate families."""

import hashlib
import importlib.util
import itertools
import json
import resource
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / "n41_same_seed_derivative_collapse_20261011/result_v2.json"
GEOMETRY = ROOT / "n41_two_free_pair_occupancy_20261009/geometry_snapshot.json"
ARITH = ROOT / "n41_two_free_pair_occupancy_20261009/arithmetic_snapshot.py"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


arith = load("n41_rank_field", ARITH)


def linear_rank(values):
    pivots = {}
    for value in values:
        while value:
            lead = value.bit_length() - 1
            if lead in pivots:
                value ^= pivots[lead]
            else:
                pivots[lead] = value
                break
    return len(pivots)


def affine_rank(values):
    values = list(values)
    if not values:
        return 0
    base = values[0]
    return linear_rank((value ^ base for value in values[1:]))


def main():
    p = json.loads((HERE / "protocol.json").read_text())
    assert p["status"] == "FROZEN_N41_SHARED_SEED_OUTPUT_RANK"
    assert p["sha256"] == {"source": sha(__file__), "prior": sha(SOURCE),
                           "geometry": sha(GEOMETRY), "arithmetic": sha(ARITH)}
    previous = json.loads(SOURCE.read_text())["rotations"]["0"]
    rows = json.loads(GEOMETRY.read_text())["n41"]["point_rows_by_unique_rotation"]["0"]
    curve = arith.Curve(arith.Field(41, [0, 3]), 0)
    points = {}
    columns = {}
    for x, y, column, mask, branch, sign in rows:
        assert branch == 0 and curve.on_curve((x, y))
        columns[mask] = column
        if sign == 0:
            points[mask] = (x, y)
    assert len(points) == 32
    start = time.monotonic_ns()
    by_key = defaultdict(set)
    by_seed = defaultdict(set)
    quartets_by_key = Counter()
    edge_sums = {}
    for seed in range(1, 64):
        edges = [(a, a ^ seed) for a in sorted(points)
                 if a < (a ^ seed) and (a ^ seed) in points
                 and columns[a] != columns[a ^ seed]]
        for a, b in edges:
            pa, pb = points[a], points[b]
            na, nb = curve.neg(pa), curve.neg(pb)
            edge_sums[(a, b)] = [curve.add(pa, pb), curve.add(pa, nb),
                                 curve.add(na, pb), curve.add(na, nb)]
        if (time.monotonic_ns() - start) / 1e9 >= p["cap_seconds"]:
            raise TimeoutError("rank census reached frozen cap")
        for (a, b), (c, d) in itertools.combinations(edges, 2):
            if len({columns[v] for v in (a, b, c, d)}) != 4:
                continue
            key = (seed, min(a ^ c, a ^ c ^ seed))
            left, right = edge_sums[(a, b)], edge_sums[(c, d)]
            # Global negation preserves x, so first source sign may be fixed.
            xs = {curve.add(L, R)[0] for L in left[:2] for R in right}
            assert len(xs) == 8
            by_key[key].update(xs)
            by_seed[seed].update(xs)
            quartets_by_key[key] += 1
    assert sum(quartets_by_key.values()) == previous["source_quartets"] == 1620
    assert len(by_key) == previous["seed_difference_keys"] == 1188
    assert sum(map(len, by_key.values())) * 2 == previous["all_sign_total_distinct_by_key"]
    key_rank = Counter()
    full_sample_rank = Counter()
    key_examples = []
    for key, xs in by_key.items():
        count = quartets_by_key[key]
        rank = affine_rank(xs)
        key_rank[(count, rank)] += 1
        full_sample_rank[(count, int(rank == len(xs) - 1))] += 1
        if rank < len(xs) - 1 and len(key_examples) < 10:
            key_examples.append({"seed": key[0], "difference": key[1],
                                 "quartets": count, "x_count": len(xs),
                                 "affine_rank": rank})
    seed_rank = Counter(affine_rank(xs) for xs in by_seed.values())
    assert len(by_seed) == 63
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != "darwin":
        peak *= 1024
    result = {"status": "COMPLETE", "candidate_id": None,
              "curve_id": p["curve_id"],
              "quartets": sum(quartets_by_key.values()),
              "seed_difference_keys": len(by_key),
              "distinct_x_by_key_sum": sum(map(len, by_key.values())),
              "key_rank_histogram": {f"{count}:{rank}": n for (count, rank), n in sorted(key_rank.items())},
              "key_full_sample_rank_histogram": {f"{count}:{full}": n for (count, full), n in sorted(full_sample_rank.items())},
              "seed_affine_rank_histogram": {str(rank): n for rank, n in sorted(seed_rank.items())},
              "rank_deficit_examples": key_examples,
              "elapsed_ns": time.monotonic_ns() - start,
              "peak_rss_bytes": peak,
              "protocol_sha256": sha(HERE / "protocol.json"),
              "source_sha256": sha(__file__)}
    assert result["elapsed_ns"] / 1e9 < p["cap_seconds"]
    assert peak < p["rss_cap_bytes"]
    (HERE / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"],
                      "key_rank_histogram": result["key_rank_histogram"],
                      "seed_affine_rank_histogram": result["seed_affine_rank_histogram"],
                      "elapsed_seconds": result["elapsed_ns"] / 1e9}))


if __name__ == "__main__":
    main()
