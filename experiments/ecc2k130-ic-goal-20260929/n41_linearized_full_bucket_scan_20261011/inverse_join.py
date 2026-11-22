"""Eliminate all right seed families with a reusable output map and S3 inverse."""

import hashlib
import json
import resource
import sys
import time
from pathlib import Path

import run

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def domain(basis_u):
    output = {}
    for seed in range(1, 64):
        u2, basis = run.bucket(basis_u, seed)
        for p in {run.xor_selected(basis, mask) for mask in range(32)}:
            for z in run.roots(1 ^ p, p, u2):
                output.setdefault(z, set()).add(seed)
    return output


def main():
    protocol = json.loads((HERE / "inverse_protocol.json").read_text())
    paths = {"source": Path(__file__), "field": HERE / "run.py",
             "targets": HERE / "targets.json", "geometry": run.GEOMETRY,
             "first_result": HERE / "result.json"}
    assert protocol["sha256"] == {key: sha(path) for key, path in paths.items()}
    geometry = json.loads(run.GEOMETRY.read_text())["n41"]
    targets = json.loads((HERE / "targets.json").read_text())["rows"]
    setup_start = time.monotonic_ns()
    left = domain(geometry["window_basis_halftrace"][2])
    right = domain(geometry["window_basis_halftrace"][3])
    setup_ns = time.monotonic_ns()-setup_start
    rows = []
    for target in targets:
        start = time.monotonic_ns()
        q = target["target_z"]
        qq = run.square(q)
        hits = []
        roots_tested = 0
        status = "COMPLETE"
        for a, left_seeds in left.items():
            c = run.mul(run.square(a) ^ a, qq ^ q)
            d = run.square(a ^ q)
            options = [d] if c == 1 else run.roots(1 ^ c, c, d)
            roots_tested += len(options)
            for b in options:
                for left_seed in left_seeds:
                    for right_seed in right.get(b, ()):
                        hits.append({"left_seed": left_seed, "right_seed": right_seed,
                                     "left_z": a, "right_z": b})
            if time.monotonic_ns()-start > protocol["per_lift_cap_seconds"]*10**9:
                status = "CENSORED_TIME"
                break
        rows.append({"kind": target["kind"], "option": target["option"],
                     "status": status, "left_coordinates": len(left),
                     "roots_tested": roots_tested, "hits": hits,
                     "query_ns": time.monotonic_ns()-start})
        print(json.dumps({"kind": target["kind"], "option": target["option"],
                          "status": status, "roots_tested": roots_tested,
                          "hits": len(hits), "query_s": rows[-1]["query_ns"]/1e9}), flush=True)
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rss = rss if sys.platform == "darwin" else rss*1024
    result = {"status": "COMPLETE" if all(r["status"] == "COMPLETE" for r in rows)
              else "CENSORED", "candidate_id": None,
              "proposal_id": protocol["proposal_id"], "setup_ns": setup_ns,
              "left_distinct_coordinates": len(left), "right_distinct_coordinates": len(right),
              "rows": rows, "peak_rss_bytes": rss,
              "source_sha256": sha(Path(__file__)),
              "protocol_sha256": sha(HERE / "inverse_protocol.json")}
    (HERE / "inverse_result.json").write_text(json.dumps(result, sort_keys=True, indent=2)+"\n")


if __name__ == "__main__":
    main()
