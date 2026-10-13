"""Unpinned seed-first two-family search on the frozen positive residual."""
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
spec = importlib.util.spec_from_file_location("two_bucket_parent_search", PARENT)
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rss_bytes():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == "darwin" else value * 1024


def main():
    p = json.loads((HERE / "search_protocol.json").read_text())
    files = {"runner": HERE / "run_search.py", "parent": PARENT,
             "panel_protocol": HERE / "protocol.json", "global_result": HERE / "global_result.json",
             "sage_runtime": HERE / "sage_runtime_info.json"}
    assert {key: sha(path) for key, path in files.items()} == p["sha256"]
    panel = json.loads((HERE / "protocol.json").read_text())
    assert p["residual"] == panel["positive_residual"]
    assert p["right_seed_order"] == list(range(1, 64))
    assert p["raw_option_order"] == list(range(4))
    started = time.monotonic_ns()
    field, curve, ring, geometry, _left, right, left_polys = parent.setup()
    setup_ns = time.monotonic_ns() - started
    begin = time.monotonic_ns()
    global_left = ring.one()
    for poly in left_polys.values():
        global_left *= poly
    product_ns = time.monotonic_ns() - begin
    begin = time.monotonic_ns()
    raw = parent.raw_targets(field, curve, geometry, p["residual"])
    reciprocals = [1 / (point[0] + 1) for point in raw]
    projection_ns = time.monotonic_ns() - begin
    decisions = 0
    norm_ns = gcd_ns = localize_ns = 0
    hit = None
    status = "EXHAUSTED"
    for seed in p["right_seed_order"]:
        u2, basis, _products = right[seed]
        for option in p["raw_option_order"]:
            begin = time.monotonic_ns()
            norm, _updates = parent.compact_target_norm(ring, reciprocals[option], u2, basis)
            norm_ns += time.monotonic_ns() - begin
            begin = time.monotonic_ns()
            common = norm.gcd(global_left)
            gcd_ns += time.monotonic_ns() - begin
            decisions += 1
            if common.degree() > 0:
                begin = time.monotonic_ns()
                families = []
                for left_seed, poly in left_polys.items():
                    factor = norm.gcd(poly)
                    if factor.degree() > 0:
                        families.append({"left_seed": left_seed,
                                         "roots": [parent.control.integer(z) for z in
                                                   factor.roots(multiplicities=False)]})
                localize_ns += time.monotonic_ns() - begin
                assert families
                hit = {"right_seed": seed, "raw_option": option,
                       "raw_target": [parent.control.integer(raw[option][0]),
                                      parent.control.integer(raw[option][1])],
                       "gcd_degree": int(common.degree()), "left_families": families}
                status = "ALGEBRAIC_HIT_PENDING_GROUP_REPLAY"
                break
        if hit:
            break
        if time.monotonic_ns() - started > p["wall_cap_seconds"] * 10**9:
            status = "CENSORED_TIME"
            break
        if rss_bytes() > p["rss_cap_bytes"]:
            status = "CENSORED_MEMORY"
            break
    result = {"status": status, "candidate_id": None, "curve_id": p["curve_id"],
              "decisions": decisions, "hit": hit,
              "setup_ns": setup_ns, "global_product_ns": product_ns,
              "target_projection_ns": projection_ns,
              "norm_ns": norm_ns, "gcd_ns": gcd_ns, "localize_ns": localize_ns,
              "whole_wall_ns": time.monotonic_ns() - started,
              "peak_rss_bytes": rss_bytes(),
              "protocol_sha256": sha(HERE / "search_protocol.json")}
    with (HERE / "search_result.json").open("x") as out:
        out.write(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(status, decisions, result["whole_wall_ns"] / 1e9, flush=True)


if __name__ == "__main__":
    main()
