"""Read-only custody and local-search audit for the half-fixed ordinary arm."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
SOURCE = EXP / "n131_d13_union_m12_halfbranch_20261115"
PRIOR = EXP / "n131_d13_union_m12_sls600_20261115"
OFFICIAL = EXP / "n131_w2_m15_official_single_target_4g_r3_20261004" / "workload.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    p = read("query_protocol.json")
    r = read("query_result.json")
    source = json.loads((SOURCE / "formula_receipt.json").read_text())
    assert p["status"] == "FROZEN_BEFORE_QUERY"
    assert p["candidate_id"] is None
    assert p["target_count"] == p["workers"] == 1
    assert p["workload_id"] == "3c1992b7c92f"
    workload = json.loads(OFFICIAL.read_text())
    assert p["public_target"] == workload["targets"][0]
    assert p["formula_sha256"] == source["formula_sha256"]
    assert p["fixed_original_positions"] == [0, 2, 4, 6, 8, 10]
    for key, path in (
        ("formula_sha256", HERE / "ordinary.xcnf"),
        ("formula_source_receipt_sha256", SOURCE / "formula_receipt.json"),
        ("class_result_sha256", SOURCE / "class_result.json"),
        ("planted_control_sha256", SOURCE / "planted_result.json"),
        ("independent_sage_replay_sha256", SOURCE / "sage_result.json"),
        ("prior_sls_protocol_sha256", PRIOR / "query_protocol.json"),
        ("prior_sls_result_sha256", PRIOR / "query_result.json"),
        ("runner_sha256", HERE / "run_query.py"),
        ("sage_runtime_info_sha256", HERE / "sage_runtime_info.json"),
        ("solver_sha256", p["solver_path"]),
    ):
        assert p[key] == sha(path), key
    assert p["solver_flags"] == ["--threads=1", "--maxtime=600",
                                 "--zero-exit-status", "--verb=1", "--printsol=1",
                                 "--maxnummatrices=0", "--sls=1", "--slseveryn=1"]
    assert p["parent_wall_cap_s"] == 615 and p["rss_cap_bytes"] == 4 * 1024**3
    assert r["kind"] == "n131_d13_halfbranch_m12_sls600_ordinary_query"
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
    class_audit = read("class_closed_form_result.json")
    assert class_audit["status"] == "PASS_INDEPENDENT_CLASS_FORMULA"
    assert class_audit["source_sha256"] == sha(SOURCE / "class_result.json")
    assert class_audit["audit_source_sha256"] == sha(HERE / "audit_class_closed_form.py")
    assert not (HERE / "class_closed_form.stderr").read_text()
    assert not (HERE / "lean.stderr").read_text()
    assert (HERE / "lean-toolchain").read_text().strip() == "leanprover/lean4:v4.34.1"
    axioms = (HERE / "lean.stdout").read_text()
    assert "'HalfBranchClasses.union_classes' does not depend on any axioms" in axioms
    assert "'HalfBranchClasses.twelve_position_counts' does not depend on any axioms" in axioms
    print(json.dumps({"status": "PASS_CUSTODY_AND_SLS_ACTIVATION",
                      "query_status": r["status"], "ccnr_rounds": ccnr_rounds,
                      "wall_ns": r["wall_ns"],
                      "sampled_peak_combined_rss_bytes": r["sampled_peak_combined_rss_bytes"]},
                     sort_keys=True))


if __name__ == "__main__":
    main()
