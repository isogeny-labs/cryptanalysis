"""Evaluate the same frozen target-conditioned norms against one reusable left product."""
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
spec = importlib.util.spec_from_file_location("two_bucket_parent_global", PARENT)
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rss_bytes():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == "darwin" else value * 1024


def main():
    p = json.loads((HERE / "global_protocol.json").read_text())
    files = {"runner": HERE / "run_global.py", "parent": PARENT,
             "panel_protocol": HERE / "protocol.json", "panel_result": HERE / "result.json",
             "sage_runtime": HERE / "sage_runtime_info.json"}
    assert {key: sha(path) for key, path in files.items()} == p["sha256"]
    panel_protocol = json.loads((HERE / "protocol.json").read_text())
    panel = json.loads((HERE / "result.json").read_text())
    assert len(panel["rows"]) == len(panel_protocol["cases"]) == 8
    started = time.monotonic_ns()
    field, curve, ring, geometry, _left, right, left_polys = parent.setup()
    setup_ns = time.monotonic_ns() - started
    begin = time.monotonic_ns()
    global_left = ring.one()
    for poly in left_polys.values():
        global_left *= poly
    global_product_ns = time.monotonic_ns() - begin
    assert global_left.degree() == sum(poly.degree() for poly in left_polys.values())
    rows = []
    for case, expected in zip(panel_protocol["cases"], panel["rows"]):
        kind, option, seed = case["kind"], case["raw_option"], case["right_seed"]
        point = parent.raw_targets(field, curve, geometry,
                                   panel_protocol[kind + "_residual"])[option]
        target = 1 / (point[0] + 1)
        u2, basis, _products = right[seed]
        begin = time.monotonic_ns()
        norm, _updates = parent.compact_target_norm(ring, target, u2, basis)
        norm_ns = time.monotonic_ns() - begin
        begin = time.monotonic_ns()
        common = norm.gcd(global_left)
        global_gcd_ns = time.monotonic_ns() - begin
        assert common.degree() == expected["gcd_degree"]
        row = {"kind": kind, "raw_option": option, "right_seed": seed,
               "gcd_degree": int(common.degree()), "norm_ns": norm_ns,
               "global_gcd_ns": global_gcd_ns,
               "panel_modular_product_ns": expected["modular_product_ns"],
               "panel_modular_gcd_ns": expected["gcd_ns"]}
        rows.append(row)
        print(json.dumps({"case": len(rows), "degree": row["gcd_degree"],
                          "global_gcd_s": global_gcd_ns / 1e9}), flush=True)
        if time.monotonic_ns() - started > p["wall_cap_seconds"] * 10**9:
            break
    result = {"status": "COMPLETE_PAIRED_PANEL" if len(rows) == 8 else "CENSORED_PANEL",
              "candidate_id": None, "curve_id": p["curve_id"],
              "global_left_degree": int(global_left.degree()),
              "setup_ns": setup_ns, "global_product_ns": global_product_ns,
              "rows": rows, "whole_wall_ns": time.monotonic_ns() - started,
              "peak_rss_bytes": rss_bytes(),
              "protocol_sha256": sha(HERE / "global_protocol.json")}
    with (HERE / "global_result.json").open("x") as out:
        out.write(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(result["status"], result["whole_wall_ns"] / 1e9, flush=True)


if __name__ == "__main__":
    main()
