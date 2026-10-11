"""Exact N41 census of shared-seed four-point output compression."""

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
GEOMETRY = ROOT / "n41_two_free_pair_occupancy_20261009/geometry_snapshot.json"
ARITH = ROOT / "n41_two_free_pair_occupancy_20261009/arithmetic_snapshot.py"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


arithmetic = load("n41_shared_seed_arithmetic", ARITH)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def point_key(point):
    return None if point is None else tuple(point)


def census(curve, rows):
    by_mask = {}
    columns = {}
    for x, y, column, mask, branch, sign in rows:
        assert branch == 0 and curve.on_curve((x, y))
        columns.setdefault(mask, column)
        assert columns[mask] == column
        if sign == 0:
            assert mask not in by_mask
            by_mask[mask] = (x, y)
    assert len(by_mask) == 32 and len(set(columns.values())) == 26
    masks = set(by_mask)
    pairs = {}
    for seed in range(1, 64):
        edges = [(a, a ^ seed) for a in sorted(masks)
                 if a < (a ^ seed) and (a ^ seed) in masks
                 and columns[a] != columns[a ^ seed]]
        pairs[seed] = edges
    sign0 = defaultdict(set)
    full = defaultdict(set)
    exact_sets = defaultdict(list)
    source_quartets = 0
    sign_assignments = 0
    example_nocollapse = None
    for seed, edges in pairs.items():
        for (a, b), (c, d) in itertools.combinations(edges, 2):
            if len({a, b, c, d}) != 4 or len({columns[v] for v in (a, b, c, d)}) != 4:
                continue
            u = min(a ^ c, a ^ c ^ seed)
            key = (seed, u)
            quartet = (a, b, c, d)
            points = [by_mask[v] for v in quartet]
            raw = curve.add(curve.add(points[0], points[1]),
                            curve.add(points[2], points[3]))
            assert raw is not None
            sign0[key].add(point_key(raw))
            outputs = set()
            for signs in itertools.product((0, 1), repeat=4):
                leaves = [curve.neg(p) if sign else p for p, sign in zip(points, signs)]
                total = curve.add(curve.add(leaves[0], leaves[1]),
                                  curve.add(leaves[2], leaves[3]))
                outputs.add(point_key(total))
                sign_assignments += 1
            full[key].update(outputs)
            exact_sets[key].append((quartet, outputs))
            source_quartets += 1
    assert set(sign0) == set(full) == set(exact_sets)
    repeated = [key for key, rows in exact_sets.items() if len(rows) > 1]
    identical_full = sum(all(rows[0][1] == other[1] for other in rows[1:])
                         for key, rows in exact_sets.items() if len(rows) > 1)
    if repeated:
        for key in sorted(repeated):
            if len(sign0[key]) > 1:
                rows = exact_sets[key]
                example_nocollapse = {"seed": key[0], "difference": key[1],
                                      "quartets": [list(row[0]) for row in rows[:3]],
                                      "sign0_outputs": [list(p) for p in sorted(sign0[key])[:3]]}
                break
    return {"rational_masks": len(masks), "folded_columns": len(set(columns.values())),
            "seed_counts": {str(s): len(edges) for s, edges in pairs.items()},
            "source_quartets": source_quartets,
            "signed_assignments": sign_assignments,
            "seed_difference_keys": len(exact_sets),
            "repeated_keys": len(repeated),
            "quartets_per_key_histogram": dict(sorted(Counter(map(len, exact_sets.values())).items())),
            "sign0_single_output_repeated_keys": sum(len(sign0[key]) == 1 for key in repeated),
            "sign0_total_distinct_by_key": sum(map(len, sign0.values())),
            "all_sign_identical_output_sets_repeated_keys": identical_full,
            "all_sign_total_distinct_by_key": sum(map(len, full.values())),
            "all_sign_individual_output_total": sum(len(outputs) for rows in exact_sets.values()
                                                    for _, outputs in rows),
            "all_sign_output_size_histogram": dict(sorted(Counter(
                len(outputs) for rows in exact_sets.values() for _, outputs in rows).items())),
            "example_nocollapse": example_nocollapse}


def main():
    p = json.loads((HERE / "protocol.json").read_text())
    assert p["status"] == "FROZEN_N41_SAME_SEED_DERIVATIVE_CENSUS"
    assert p["sha256"] == {"run": sha(__file__), "geometry": sha(GEOMETRY),
                           "arithmetic": sha(ARITH)}
    data = json.loads(GEOMETRY.read_text())["n41"]
    field = arithmetic.Field(41, [0, 3])
    curve = arithmetic.Curve(field, 0)
    start = time.monotonic_ns()
    rows = {}
    for rotation in p["rotations"]:
        run_start = time.monotonic_ns()
        rows[str(rotation)] = census(curve, data["point_rows_by_unique_rotation"][str(rotation)])
        rows[str(rotation)]["elapsed_ns"] = time.monotonic_ns() - run_start
        assert (time.monotonic_ns() - start) / 1e9 < p["cap_seconds"]
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != "darwin":
        peak *= 1024
    result = {"status": "COMPLETE", "candidate_id": None,
              "curve_id": data["curve_id"], "rotations": rows,
              "elapsed_ns": time.monotonic_ns() - start,
              "peak_rss_bytes": peak, "protocol_sha256": sha(HERE / "protocol.json"),
              "source_sha256": sha(__file__)}
    assert peak < p["rss_cap_bytes"]
    (HERE / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "rotations": {
        key: {name: value for name, value in row.items() if name in
              ("source_quartets", "seed_difference_keys", "repeated_keys",
               "sign0_single_output_repeated_keys", "all_sign_identical_output_sets_repeated_keys")}
        for key, row in rows.items()}, "seconds": result["elapsed_ns"] / 1e9}))


if __name__ == "__main__":
    main()
