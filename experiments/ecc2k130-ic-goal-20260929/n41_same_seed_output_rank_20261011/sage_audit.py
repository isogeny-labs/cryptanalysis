#!/usr/bin/env sage -python
"""Independent Sage replay of exact affine ranks and field trace."""

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
GEOMETRY = ROOT / "n41_two_free_pair_occupancy_20261009/geometry_snapshot.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def lift(F, integer):
    result = F.zero()
    power = F.one()
    while integer:
        if integer & 1:
            result += power
        power *= F.gen()
        integer >>= 1
    return result


def encode(value):
    return sum(int(coefficient) << index
               for index, coefficient in enumerate(value.polynomial()))


def rank_low(values):
    values = list(values)
    if not values:
        return 0
    first = values[0]
    pivots = {}
    for value in values[1:]:
        value ^= first
        while value:
            bit = (value & -value).bit_length() - 1
            if bit in pivots:
                value ^= pivots[bit]
            else:
                pivots[bit] = value
                break
    return len(pivots)


def main():
    p = json.loads((HERE / "sage_protocol.json").read_text())
    assert p["status"] == "FROZEN_SAGE_SHARED_SEED_RANK_AUDIT"
    assert p["sha256"] == {"source": sha(__file__),
                           "rank": sha(HERE / "result.json"),
                           "trace": sha(HERE / "trace_result.json"),
                           "geometry": sha(GEOMETRY),
                           "runtime": sha(HERE / "sage_runtime_info.json")}
    expected = json.loads((HERE / "result.json").read_text())
    trace_result = json.loads((HERE / "trace_result.json").read_text())
    geometry = json.loads(GEOMETRY.read_text())["n41"]
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    F = GF(2**41, "t", modulus=t**41+t**3+1)
    E = EllipticCurve(F, [1, 0, 0, 0, 1])
    assert sum(int((F.gen()**i).trace()) << i for i in range(41)) == trace_result["trace_mask"] == 1
    q = E(lift(F, geometry["public_target_q"][0]), lift(F, geometry["public_target_q"][1]))
    assert int(q[0].trace()) == 0
    points = {}
    columns = {}
    negatives = {}
    for x, y, column, mask, branch, sign in geometry["point_rows_by_unique_rotation"]["0"]:
        assert branch == 0
        P = E(lift(F, x), lift(F, y))
        columns[mask] = column
        (points if sign == 0 else negatives)[mask] = P
    assert len(points) == len(negatives) == 32
    assert all(negatives[mask] == -points[mask] for mask in points)
    start = time.monotonic_ns()
    x_by_key = defaultdict(set)
    x_by_seed = defaultdict(set)
    quartet_count = Counter()
    for seed in range(1, 64):
        edges = [(a, a ^ seed) for a in sorted(points)
                 if a < (a ^ seed) and (a ^ seed) in points
                 and columns[a] != columns[a ^ seed]]
        edge_sum = {}
        for a, b in edges:
            pa, pb = points[a], points[b]
            edge_sum[(a, b)] = [pa+pb, pa-pb, -pa+pb, -pa-pb]
        if (time.monotonic_ns()-start)/1e9 >= p["cap_seconds"]:
            raise TimeoutError("Sage rank replay reached frozen cap")
        for (a, b), (c, d) in itertools.combinations(edges, 2):
            if len({columns[v] for v in (a, b, c, d)}) < 4:
                continue
            key = (seed, min(a ^ c, a ^ c ^ seed))
            xs = {encode((L+R)[0]) for L in edge_sum[(a, b)][:2]
                  for R in edge_sum[(c, d)]}
            assert len(xs) == 8
            assert all(int(lift(F, x).trace()) == 0 for x in xs)
            x_by_key[key].update(xs)
            x_by_seed[seed].update(xs)
            quartet_count[key] += 1
    key_hist = Counter((quartet_count[key], rank_low(xs)) for key, xs in x_by_key.items())
    seed_hist = Counter(rank_low(xs) for xs in x_by_seed.values())
    actual_key = {f"{count}:{rank}": n for (count, rank), n in sorted(key_hist.items())}
    actual_seed = {str(rank): n for rank, n in sorted(seed_hist.items())}
    assert actual_key == expected["key_rank_histogram"]
    assert actual_seed == expected["seed_affine_rank_histogram"]
    assert sum(map(len, x_by_key.values())) == expected["distinct_x_by_key_sum"] == 12960
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != "darwin":
        peak *= 1024
    out = {"status": "PASS_INDEPENDENT_SAGE_SHARED_SEED_RANK",
           "candidate_id": None, "curve_id": p["curve_id"],
           "key_rank_histogram": actual_key,
           "seed_affine_rank_histogram": actual_seed,
           "trace_mask": trace_result["trace_mask"],
           "distinct_x_checked": 12960,
           "elapsed_ns": time.monotonic_ns()-start,
           "peak_rss_bytes": peak,
           "protocol_sha256": sha(HERE / "sage_protocol.json")}
    assert out["elapsed_ns"]/1e9 < p["cap_seconds"]
    assert peak < p["rss_cap_bytes"]
    (HERE / "sage_audit.json").write_text(json.dumps(out, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"status": out["status"], "key_histogram": actual_key,
                      "seed_histogram": actual_seed,
                      "seconds": out["elapsed_ns"]/1e9}))


if __name__ == "__main__":
    main()
