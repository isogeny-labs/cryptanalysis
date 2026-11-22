"""Read-only custody check for the N131 same-cap default control."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    p = read("query_protocol.json")
    r = read("query_result.json")
    assert p["status"] == "FROZEN_BEFORE_QUERY"
    assert p["candidate_id"] is None
    assert p["target_count"] == p["workers"] == 1
    assert p["workload_id"] == "3c1992b7c92f"
    assert p["formula_sha256"] == sha(HERE / "ordinary.xcnf")
    assert p["formula_source_receipt_sha256"] == sha(p["formula_source_receipt"])
    assert p["runner_sha256"] == sha(HERE / "run_query.py")
    assert p["sage_runtime_info_sha256"] == sha(HERE / "sage_runtime_info.json")
    assert p["solver_sha256"] == sha(p["solver_path"])
    assert p["solver_flags"] == ["--threads=1", "--maxtime=120",
                                  "--zero-exit-status", "--verb=1", "--printsol=1"]
    assert p["parent_wall_cap_s"] == 135
    assert p["rss_cap_bytes"] == 4*1024**3
    tuned = HERE.parent / "n131_d13_union_m10_gauss_20261115"
    assert p["tuned_protocol_sha256"] == sha(tuned / "query_protocol.json")
    assert p["tuned_result_sha256"] == sha(tuned / "query_result.json")
    assert r["query_protocol_sha256"] == sha(HERE / "query_protocol.json")
    assert r["stdout_sha256"] == sha(HERE / "solver.stdout")
    assert r["stderr_sha256"] == sha(HERE / "solver.stderr")
    assert not (HERE / "runner.stderr").read_text()
    assert r["sampled_peak_combined_rss_bytes"] < p["rss_cap_bytes"] or r["stop_reason"] == "RSS_CAP"
    assert r["status"] in ("BOUNDED_UNKNOWN", "UNSAT_UNCERTIFIED",
                           "SAT_PENDING_REPLAY", "PRODUCER_FAILURE")
    assert any("Using 0 matrices recovered" in line
               for line in r["matrix_usage_lines"])
    if r["status"] == "SAT_PENDING_REPLAY":
        raise RuntimeError("SAT model requires independent source-bound replay")
    print(json.dumps({"status": "PASS_CUSTODY", "probe_status": r["status"],
                      "wall_ns": r["wall_ns"],
                      "sampled_peak_combined_rss_bytes": r["sampled_peak_combined_rss_bytes"]},
                     sort_keys=True))


if __name__ == "__main__":
    main()
