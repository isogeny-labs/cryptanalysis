"""Exact target-conditioned join of N41 shared-seed four-point families."""

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
ARITHMETIC = ROOT / "n41_two_free_pair_occupancy_20261009/arithmetic_snapshot.py"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_arithmetic():
    spec = importlib.util.spec_from_file_location("n41_finite_join_arithmetic", ARITHMETIC)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_families(curve, rows, deadline):
    points, columns = {}, {}
    for x, y, col, mask, branch, sign in rows:
        assert branch == 0 and curve.on_curve((x, y))
        columns[mask] = col
        if sign == 0:
            points[mask] = (x, y)
    assert len(points) == 32 and len(set(columns.values())) == 26
    families, edge_sums = [], {}
    for seed in range(1, 64):
        assert time.monotonic() < deadline
        edges = [(a, a ^ seed) for a in sorted(points)
                 if a < (a ^ seed) and (a ^ seed) in points
                 and columns[a] != columns[a ^ seed]]
        for a, b in edges:
            pa, pb = points[a], points[b]
            edge_sums[(a, b)] = [curve.add(pa, pb), curve.add(pa, curve.neg(pb)),
                                  curve.add(curve.neg(pa), pb),
                                  curve.add(curve.neg(pa), curve.neg(pb))]
        for (a, b), (c, d) in itertools.combinations(edges, 2):
            quartet = (a, b, c, d)
            cols = tuple(columns[v] for v in quartet)
            if len(set(cols)) != 4:
                continue
            # Global negation leaves x fixed; both signs are restored at query time.
            roots = {}
            for left in edge_sums[(a, b)][:2]:
                for right in edge_sums[(c, d)]:
                    p = curve.add(left, right)
                    assert p is not None and p[0] not in roots
                    roots[p[0]] = p
            assert len(roots) == 8
            families.append((seed, quartet, cols, roots))
    assert len(families) == 1620
    return families


def target_join(curve, families, target, deadline):
    index = defaultdict(list)
    for fid, family in enumerate(families):
        for x in family[3]:
            index[x].append(fid)
    probes = 0
    hits = set()
    disjoint_hits = set()
    certificate = None
    for left_id, (_, left_masks, left_cols, roots) in enumerate(families):
        if left_id % 16 == 0:
            assert time.monotonic() < deadline
        for p in roots.values():
            for signed in (p, curve.neg(p)):
                # A right root has x(target - signed). Both lifts are in its family.
                right_x = curve.add(target, curve.neg(signed))
                assert right_x is not None
                probes += 1
                for right_id in index.get(right_x[0], ()):
                    pair = (left_id, right_id)
                    hits.add(pair)
                    right = families[right_id]
                    if len(set(left_cols + right[2])) != 8:
                        continue
                    disjoint_hits.add(pair)
                    if certificate is None:
                        witness = next(q for q in (right[3][right_x[0]],
                                                   curve.neg(right[3][right_x[0]]))
                                       if curve.add(signed, q) == target)
                        certificate = {"left_family": left_id, "right_family": right_id,
                                       "left_masks": list(left_masks),
                                       "right_masks": list(right[1]),
                                       "left_point": list(signed), "right_point": list(witness),
                                       "target": list(target)}
    return {"root_probes": probes, "ordered_family_hits": len(hits),
            "ordered_disjoint_family_hits": len(disjoint_hits),
            "left_families_with_hit": len({a for a, _ in hits}),
            "left_families_with_disjoint_hit": len({a for a, _ in disjoint_hits}),
            "witness": certificate}


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert protocol["status"] == "FROZEN_N41_FINITE_FAMILY_TARGET_JOIN"
    assert protocol["sha256"] == {"source": digest(Path(__file__)),
                                   "geometry": digest(GEOMETRY),
                                   "arithmetic": digest(ARITHMETIC)}
    geometry = json.loads(GEOMETRY.read_text())["n41"]
    assert geometry["curve_id"] == protocol["curve_id"]
    arithmetic = load_arithmetic()
    curve = arithmetic.Curve(arithmetic.Field(41, [0, 3]), 0)
    start = time.monotonic()
    deadline = start + protocol["cap_seconds"]
    families = build_families(curve,
                              geometry["point_rows_by_unique_rotation"]["0"], deadline)
    public = tuple(geometry["public_target_q"])
    assert curve.on_curve(public)
    pos_pair = next((i, j) for i, j in itertools.combinations(range(len(families)), 2)
                    if len(set(families[i][2] + families[j][2])) == 8)
    p = next(iter(families[pos_pair[0]][3].values()))
    q = next(iter(families[pos_pair[1]][3].values()))
    positive = curve.add(p, q)
    assert positive is not None and curve.on_curve(positive)
    rows = {}
    for label, target in (("constructed_positive", positive), ("frozen_public", public)):
        t0 = time.monotonic_ns()
        rows[label] = target_join(curve, families, target, deadline)
        rows[label]["target"] = list(target)
        rows[label]["elapsed_ns"] = time.monotonic_ns() - t0
    assert rows["constructed_positive"]["ordered_disjoint_family_hits"] > 0
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != "darwin":
        peak *= 1024
    result = {"status": "COMPLETE", "curve_id": protocol["curve_id"],
              "candidate_id": None, "families": len(families),
              "family_x_roots": sum(len(f[3]) for f in families),
              "full_ordered_family_pairs": len(families)**2,
              "positive_source_families": list(pos_pair),
              "targets": rows, "elapsed_ns": time.monotonic_ns() - int(start * 1e9),
              "peak_rss_bytes": peak, "source_sha256": digest(Path(__file__)),
              "protocol_sha256": digest(HERE / "protocol.json")}
    assert result["elapsed_ns"] < protocol["cap_seconds"] * 10**9
    assert peak < protocol["rss_cap_bytes"]
    (HERE / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "families": len(families),
                      "public_hits": rows["frozen_public"]["ordered_disjoint_family_hits"],
                      "positive_hits": rows["constructed_positive"]["ordered_disjoint_family_hits"],
                      "seconds": result["elapsed_ns"] / 1e9}))


if __name__ == "__main__":
    main()
