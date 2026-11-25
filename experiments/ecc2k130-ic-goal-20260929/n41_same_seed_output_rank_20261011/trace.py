"""Identify the rank-40 affine hull with the universal trace-zero hyperplane."""

import hashlib
import importlib.util
import itertools
import json
import resource
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
GEOMETRY = ROOT / "n41_two_free_pair_occupancy_20261009/geometry_snapshot.json"
ARITH = ROOT / "n41_two_free_pair_occupancy_20261009/arithmetic_snapshot.py"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


arith = load("n41_trace_field", ARITH)


def main():
    p = json.loads((HERE / "trace_protocol.json").read_text())
    assert p["status"] == "FROZEN_N41_SHARED_SEED_TRACE_IDENTIFICATION"
    assert p["sha256"] == {"source": sha(__file__),
                           "rank": sha(HERE / "result.json"),
                           "geometry": sha(GEOMETRY),
                           "arithmetic": sha(ARITH)}
    rank = json.loads((HERE / "result.json").read_text())
    assert rank["seed_affine_rank_histogram"] == {"40": 63}
    geometry = json.loads(GEOMETRY.read_text())["n41"]
    field = arith.Field(41, [0, 3])
    curve = arith.Curve(field, 0)
    trace_mask = sum(arith.trace(field, 1 << i) << i for i in range(41))
    assert trace_mask != 0
    trace_bit = lambda x: bin(x & trace_mask).count("1") & 1
    points = {}
    columns = {}
    for x, y, column, mask, branch, sign in geometry["point_rows_by_unique_rotation"]["0"]:
        columns[mask] = column
        if sign == 0:
            points[mask] = (x, y)
            assert trace_bit(x) == 0
    assert len(points) == 32
    assert trace_bit(geometry["public_target_q"][0]) == 0
    start = time.monotonic_ns()
    edge_sums = {}
    checked = 0
    by_seed = Counter()
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
            raise TimeoutError("trace replay reached frozen cap")
        for (a, b), (c, d) in itertools.combinations(edges, 2):
            if len({columns[v] for v in (a, b, c, d)}) != 4:
                continue
            for left in edge_sums[(a, b)][:2]:
                for right in edge_sums[(c, d)]:
                    output = curve.add(left, right)
                    assert output is not None
                    assert trace_bit(output[0]) == 0
                    checked += 1
                    by_seed[seed] += 1
    assert checked == rank["distinct_x_by_key_sum"] == 12960
    assert len(by_seed) == 63
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != "darwin":
        peak *= 1024
    out = {"status": "PASS_UNIVERSAL_TRACE_HYPERPLANE",
           "candidate_id": None, "curve_id": p["curve_id"],
           "trace_mask": trace_mask,
           "source_masks_checked": 32,
           "seed_families_checked": len(by_seed),
           "distinct_signed_x_checked": checked,
           "public_target_trace_bit": trace_bit(geometry["public_target_q"][0]),
           "seed_affine_rank": 40,
           "extra_affine_equations_per_seed": 0,
           "elapsed_ns": time.monotonic_ns() - start,
           "peak_rss_bytes": peak,
           "protocol_sha256": sha(HERE / "trace_protocol.json"),
           "source_sha256": sha(__file__)}
    assert out["elapsed_ns"] / 1e9 < p["cap_seconds"]
    assert peak < p["rss_cap_bytes"]
    (HERE / "trace_result.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": out["status"], "trace_mask": trace_mask,
                      "x_checked": checked, "seconds": out["elapsed_ns"] / 1e9}))


if __name__ == "__main__":
    main()
