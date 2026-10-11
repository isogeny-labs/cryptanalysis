#!/usr/bin/env sage -python
"""Independent Sage enumeration and target join for the N41 family census."""

import hashlib
import itertools
import json
import resource
import sys
import time
from collections import defaultdict
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
GEOMETRY = ROOT / "n41_two_free_pair_occupancy_20261009/geometry_snapshot.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lift(F, integer):
    result, power = F.zero(), F.one()
    while integer:
        if integer & 1:
            result += power
        power *= F.gen()
        integer >>= 1
    return result


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial()))


def point_xy(point):
    return [encode(point[0]), encode(point[1])]


def main():
    protocol = json.loads((HERE / "sage_protocol.json").read_text())
    assert protocol["status"] == "FROZEN_N41_FINITE_JOIN_SAGE_AUDIT"
    assert protocol["sha256"] == {"source": sha(Path(__file__)),
                                   "result": sha(HERE / "result.json"),
                                   "geometry": sha(GEOMETRY),
                                   "runtime": sha(HERE / "sage_runtime_info.json")}
    expected = json.loads((HERE / "result.json").read_text())
    geometry = json.loads(GEOMETRY.read_text())["n41"]
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    F = GF(2**41, "t", modulus=t**41+t**3+1)
    E = EllipticCurve(F, [1, 0, 0, 0, 1])
    source, negatives, cols = {}, {}, {}
    for x, y, col, mask, branch, sign in geometry["point_rows_by_unique_rotation"]["0"]:
        assert branch == 0
        P = E(lift(F, x), lift(F, y))
        cols[mask] = col
        if sign == 0:
            source[mask] = P
        else:
            negatives[mask] = P
    assert len(source) == len(negatives) == 32
    assert all(negatives[mask] == -source[mask] for mask in source)
    start = time.monotonic_ns()
    families = []
    for seed in range(1, 64):
        assert (time.monotonic_ns()-start)/1e9 < protocol["cap_seconds"]
        edges = [(a, a ^ seed) for a in sorted(source)
                 if a < (a ^ seed) and (a ^ seed) in source
                 and cols[a] != cols[a ^ seed]]
        pairs = {(a, b): [source[a]+source[b], source[a]-source[b],
                          -source[a]+source[b], -source[a]-source[b]]
                 for a, b in edges}
        for (a, b), (c, d) in itertools.combinations(edges, 2):
            masks = (a, b, c, d)
            column_set = {cols[v] for v in masks}
            if len(column_set) != 4:
                continue
            outputs = {}
            for left in pairs[(a, b)][:2]:
                for right in pairs[(c, d)]:
                    P = left + right
                    assert P != E(0)
                    x = encode(P[0])
                    assert x not in outputs
                    outputs[x] = P
            assert len(outputs) == 8
            families.append((masks, column_set, outputs))
    assert len(families) == expected["families"] == 1620
    index = defaultdict(list)
    for fid, (_, _, roots) in enumerate(families):
        for x in roots:
            index[x].append(fid)
    pos_pair = next((i, j) for i, j in itertools.combinations(range(len(families)), 2)
                    if len(families[i][1] | families[j][1]) == 8)
    assert list(pos_pair) == expected["positive_source_families"]
    positive = next(iter(families[pos_pair[0]][2].values())) + next(iter(families[pos_pair[1]][2].values()))
    public = E(*[lift(F, value) for value in geometry["public_target_q"]])
    rows = {}
    for label, target in (("constructed_positive", positive), ("frozen_public", public)):
        hits, valid = set(), set()
        for left_id, (_, left_cols, roots) in enumerate(families):
            for P in roots.values():
                for signed in (P, -P):
                    right_x = encode((target-signed)[0])
                    for right_id in index.get(right_x, ()):
                        hits.add((left_id, right_id))
                        if len(left_cols | families[right_id][1]) == 8:
                            valid.add((left_id, right_id))
        observed = {"target": point_xy(target), "ordered_family_hits": len(hits),
                    "ordered_disjoint_family_hits": len(valid),
                    "left_families_with_hit": len({a for a, _ in hits}),
                    "left_families_with_disjoint_hit": len({a for a, _ in valid})}
        original = expected["targets"][label]
        assert all(observed[k] == original[k] for k in observed)
        if original["witness"]:
            w = original["witness"]
            A = E(*[lift(F, v) for v in w["left_point"]])
            B = E(*[lift(F, v) for v in w["right_point"]])
            assert A+B == target
            assert len({cols[m] for m in w["left_masks"]+w["right_masks"]}) == 8
        rows[label] = observed
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != "darwin":
        peak *= 1024
    out = {"status": "PASS_INDEPENDENT_SAGE_FINITE_JOIN", "targets": rows,
           "families": len(families), "elapsed_ns": time.monotonic_ns()-start,
           "peak_rss_bytes": peak, "protocol_sha256": sha(HERE / "sage_protocol.json")}
    assert out["elapsed_ns"] < protocol["cap_seconds"]*10**9
    assert peak < protocol["rss_cap_bytes"]
    (HERE / "sage_audit.json").write_text(json.dumps(out, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"status": out["status"], "seconds": out["elapsed_ns"]/1e9,
                      "positive_hits": rows["constructed_positive"]["ordered_disjoint_family_hits"],
                      "public_hits": rows["frozen_public"]["ordered_disjoint_family_hits"]}))


if __name__ == "__main__":
    main()
