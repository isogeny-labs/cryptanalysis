"""Read-only custody and local-search audit for the full ordinary arm."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
SCREEN = EXP / "n131_d13_union_arity_20261115"
PROBE = EXP / "n131_d13_union_m12_sls120_20261115"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    p = read("query_protocol.json")
    r = read("query_result.json")
    screen = json.loads((SCREEN / "result.json").read_text())
    assert p["status"] == "FROZEN_BEFORE_QUERY"
    assert p["candidate_id"] is None
    assert p["target_count"] == p["workers"] == 1
    assert p["workload_id"] == "3c1992b7c92f"
    assert p["formula_sha256"] == screen["rows"]["12"]["formula_sha256"]
    for key, path in (
        ("formula_sha256", HERE / "ordinary.xcnf"),
        ("formula_source_receipt_sha256", SCREEN / "result.json"),
        ("planted_control_sha256", SCREEN / "planted_result.json"),
        ("independent_sage_replay_sha256", SCREEN / "sage_result.json"),
        ("probe_protocol_sha256", PROBE / "query_protocol.json"),
        ("probe_result_sha256", PROBE / "query_result.json"),
        ("runner_sha256", HERE / "run_query.py"),
        ("sage_runtime_info_sha256", HERE / "sage_runtime_info.json"),
        ("solver_sha256", p["solver_path"]),
    ):
        assert p[key] == sha(path), key
    assert p["solver_flags"] == ["--threads=1", "--maxtime=600",
                                 "--zero-exit-status", "--verb=1", "--printsol=1",
                                 "--maxnummatrices=0", "--sls=1", "--slseveryn=1"]
    assert p["parent_wall_cap_s"] == 615 and p["rss_cap_bytes"] == 4 * 1024**3
    assert r["kind"] == "n131_d13_union_m12_s3_sls600_ordinary_query"
    assert r["query_protocol_sha256"] == sha(HERE / "query_protocol.json")
    assert r["command"] == [p["solver_path"], *p["solver_flags"], str(HERE / "ordinary.xcnf")]
    assert r["stdout_sha256"] == sha(HERE / "solver.stdout")
    assert r["stderr_sha256"] == sha(HERE / "solver.stderr")
    assert not (HERE / "runner.stderr").read_text()
    assert r["sampled_peak_combined_rss_bytes"] < p["rss_cap_bytes"]
    log = (HERE / "solver.stdout").read_text(errors="replace")
    assert r["terminal_lines"] == [line for line in log.splitlines() if line.startswith("s ")]
    assert r["status"] in ("BOUNDED_UNKNOWN", "SAT_PENDING_REPLAY", "UNSAT_UNCERTIFIED")
    if r["status"] == "BOUNDED_UNKNOWN":
        assert r["stop_reason"] or r["terminal_lines"] == ["s INDETERMINATE"]
    if r["status"] == "SAT_PENDING_REPLAY":
        replay = read("replay_result.json")
        assert replay["status"] == "PASS_SOURCE_BOUND_PROJECTED_RELATION"
        assert replay["query_result_sha256"] == sha(HERE / "query_result.json")
        assert replay["replay_source_sha256"] == sha(HERE / "replay_sat.py")
    assert "[matrix] Using 0 matrices" in log
    assert "disabling SLS since matrix is found" not in log
    ccnr_rounds = log.count("[ccnr] time:")
    assert ccnr_rounds > 0
    print(json.dumps({"status": "PASS_CUSTODY_AND_SLS_ACTIVATION",
                      "query_status": r["status"], "ccnr_rounds": ccnr_rounds,
                      "wall_ns": r["wall_ns"],
                      "sampled_peak_combined_rss_bytes": r["sampled_peak_combined_rss_bytes"]},
                     sort_keys=True))


if __name__ == "__main__":
    main()
