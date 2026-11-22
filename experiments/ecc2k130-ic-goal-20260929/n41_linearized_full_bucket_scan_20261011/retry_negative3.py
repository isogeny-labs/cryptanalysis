"""One frozen repeat of the censored eighth raw lift, with the same cap."""

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


def main():
    p = json.loads((HERE / "retry_protocol.json").read_text())
    paths = {"source": Path(__file__), "run": HERE / "run.py",
             "protocol": HERE / "protocol.json", "targets": HERE / "targets.json",
             "first_result": HERE / "result.json"}
    assert p["sha256"] == {key: sha(path) for key, path in paths.items()}
    target = json.loads((HERE / "targets.json").read_text())["rows"][7]
    assert target["kind"] == "negative" and target["option"] == 3
    geometry = json.loads(run.GEOMETRY.read_text())["n41"]
    setup_start = time.monotonic_ns()
    left = run.left_domain(geometry["window_basis_halftrace"][2])
    right = {s: run.bucket(geometry["window_basis_halftrace"][3], s)
             for s in range(1, 64)}
    setup_ns = time.monotonic_ns()-setup_start
    start = time.monotonic_ns()
    decisions = 0
    hits = []
    status = "COMPLETE"
    for z, left_seeds in left.items():
        for right_seed in run.right_hit(z, target["target_z"], right):
            for left_seed in left_seeds:
                hits.append({"left_seed": left_seed, "right_seed": right_seed,
                             "left_z": z})
        decisions += 63
        if time.monotonic_ns()-start > p["per_lift_cap_seconds"]*10**9:
            status = "CENSORED_TIME"
            break
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rss = rss if sys.platform == "darwin" else rss*1024
    result = {"status": status, "kind": "negative", "option": 3,
              "setup_ns": setup_ns, "query_ns": time.monotonic_ns()-start,
              "left_coordinates": len(left), "bucket_decisions": decisions,
              "hits": hits, "peak_rss_bytes": rss,
              "protocol_sha256": sha(HERE / "retry_protocol.json")}
    (HERE / "retry_result.json").write_text(json.dumps(result, sort_keys=True, indent=2)+"\n")
    print(json.dumps({"status": status, "decisions": decisions,
                      "hits": len(hits), "query_s": result["query_ns"]/1e9}))


if __name__ == "__main__":
    main()
