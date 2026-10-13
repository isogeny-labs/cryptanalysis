"""Exact target-conditioned all-left-family rejection via modular products."""
import hashlib
import importlib.util
import json
import resource
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
PARENT = GOAL / "n41_symbolic_two_bucket_20261011/run.py"
PARENT_PROTOCOL = GOAL / "n41_symbolic_two_bucket_20261011/protocol.json"
spec = importlib.util.spec_from_file_location("two_bucket_parent", PARENT)
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rss_bytes():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == "darwin" else value * 1024


def run_case(ring, target, left_polys, right_data, check_individual):
    u2, basis, _products = right_data
    started = time.monotonic_ns()
    norm, updates = parent.compact_target_norm(ring, target, u2, basis)
    norm_ns = time.monotonic_ns() - started
    assert norm.degree() > 0
    begun = time.monotonic_ns()
    reduced = ring.one()
    for poly in left_polys.values():
        reduced = (reduced * poly) % norm
    modular_product_ns = time.monotonic_ns() - begun
    begun = time.monotonic_ns()
    common = norm.gcd(reduced)
    gcd_ns = time.monotonic_ns() - begun
    hits = []
    direct_ns = 0
    if check_individual or common.degree() > 0:
        begun = time.monotonic_ns()
        for seed, poly in left_polys.items():
            factor = norm.gcd(poly)
            if factor.degree() > 0:
                hits.append({"left_seed": seed, "degree": int(factor.degree()),
                             "roots": [parent.control.integer(z) for z in factor.roots(multiplicities=False)]})
        direct_ns = time.monotonic_ns() - begun
        assert (common.degree() > 0) == bool(hits)
    if check_individual:
        product = ring.one()
        for poly in left_polys.values():
            product *= poly
        assert norm.gcd(product) == common
    return {"norm_degree": int(norm.degree()), "linearized_updates": updates,
            "reduced_degree": int(reduced.degree()), "gcd_degree": int(common.degree()),
            "hits": hits, "norm_ns": norm_ns,
            "modular_product_ns": modular_product_ns, "gcd_ns": gcd_ns,
            "individual_gcd_ns": direct_ns,
            "individual_gcd_count": len(left_polys) if check_individual or common.degree() > 0 else 0}


def main():
    p = json.loads((HERE / "protocol.json").read_text())
    files = {"runner": HERE / "run.py", "parent": PARENT,
             "parent_protocol": PARENT_PROTOCOL,
             "geometry": GOAL / "n41_two_free_pair_occupancy_20261009/geometry_snapshot.json",
             "sage_runtime": HERE / "sage_runtime_info.json"}
    assert {name: sha(path) for name, path in files.items()} == p["sha256"]
    assert p["worker_count"] == 1 and p["rss_cap_bytes"] == 4294967296
    old = json.loads(PARENT_PROTOCOL.read_text())
    assert p["positive_residual"] == old["positive_residual"]
    assert p["negative_residual"] == old["negative_residual"]
    started = time.monotonic_ns()
    field, curve, ring, _geometry, left, right, left_polys = parent.setup()
    setup_ns = time.monotonic_ns() - started
    assert len(left) == len(right) == len(left_polys) == 63
    rows = []
    for case in p["cases"]:
        kind, option, right_seed = case["kind"], case["raw_option"], case["right_seed"]
        points = parent.raw_targets(field, curve, _geometry, p[kind + "_residual"])
        point = points[option]
        assert point[0] != 1
        target = 1 / (point[0] + 1)
        row = run_case(ring, target, left_polys, right[right_seed], case["check_individual"])
        row.update({"kind": kind, "raw_option": option, "right_seed": right_seed,
                    "raw_target": [parent.control.integer(point[0]),
                                   parent.control.integer(point[1])],
                    "check_individual": case["check_individual"]})
        rows.append(row)
        print(json.dumps({"case": len(rows), "kind": kind, "option": option,
                          "right_seed": right_seed, "gcd_degree": row["gcd_degree"],
                          "wall_s": (time.monotonic_ns() - started) / 1e9}), flush=True)
        if (rss_bytes() > p["rss_cap_bytes"] or
                time.monotonic_ns() - started > p["wall_cap_seconds"] * 10**9):
            break
    result = {"status": "COMPLETE_PANEL" if len(rows) == len(p["cases"]) else "CENSORED_PANEL",
              "candidate_id": None, "curve_id": p["curve_id"],
              "setup_ns": setup_ns, "rows": rows,
              "whole_wall_ns": time.monotonic_ns() - started,
              "peak_rss_bytes": rss_bytes(), "protocol_sha256": sha(HERE / "protocol.json")}
    with (HERE / "result.json").open("x") as out:
        out.write(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(result["status"], len(rows), result["whole_wall_ns"] / 1e9, flush=True)


if __name__ == "__main__":
    main()
