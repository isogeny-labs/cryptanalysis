"""Read-only terminal audit of the frozen bilinear-family experiment."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "n41_joint_product_span_relaxation_20261013"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text())


def main():
    p = load("protocol.json")
    assert p["status"] == "FROZEN"
    for key, path in (("native_source_sha256", HERE / "native.cpp"),
                      ("native_binary_sha256", HERE / "native"),
                      ("prior_protocol_sha256", PRIOR / "protocol.json"),
                      ("prior_sage_replay_sha256", PRIOR / "sage_replay_result.json")):
        assert p[key] == sha(path), key
    receipt = load("receipt.json")
    assert receipt["status"] == "COMPLETE" and receipt["returncode"] == 0
    assert receipt["sampled_peak_rss_bytes"] < p["rss_cap_bytes"]
    assert receipt["wall_seconds"] < p["wall_cap_seconds"]
    for name, key in (("stdout.log", "stdout_sha256"),
                      ("stderr.log", "stderr_sha256"),
                      ("cases.jsonl", "cases_sha256")):
        assert receipt[key] == sha(HERE / name)
    summary = load("stdout.log")
    rows = [json.loads(x) for x in (HERE / "cases.jsonl").read_text().splitlines()]
    assert summary["status"] == "COMPLETE_BILINEAR_RANK_SCREEN"
    assert len(rows) == summary["cases"] == 1026
    assert sum(not row["rank_consistent"] for row in rows) == summary["rank_rejects"] == 2
    assert sum(row["pivot_hits"] for row in rows) == summary["pivot_hits"] == 1
    assert sum(row["direct_hits"] for row in rows) == summary["direct_hits"] == 1
    assert all(row["pivot_complete"] and row["pivot_hits"] == row["direct_hits"] for row in rows)
    audit_p, audit = load("audit_protocol.json"), load("audit_result.json")
    assert audit_p["main_protocol_sha256"] == sha(HERE / "protocol.json")
    assert audit_p["audit_source_sha256"] == sha(HERE / "audit.py")
    assert audit_p["native_cases_sha256"] == sha(HERE / "cases.jsonl")
    assert audit["protocol_sha256"] == sha(HERE / "audit_protocol.json")
    assert audit["status"] == "PASS_INDEPENDENT_FAMILY_RANK_AND_DIRECT_JOIN"
    assert audit["rank_cases_checked"] == 64 and audit["direct_cases_checked"] == 16
    audit_receipt = load("audit_receipt.json")
    assert audit_receipt["status"] == "COMPLETE" and audit_receipt["returncode"] == 0
    sage_p, sage = load("sage_protocol.json"), load("sage_result.json")
    assert sage_p["status"] == "FROZEN"
    assert sage_p["main_protocol_sha256"] == sha(HERE / "protocol.json")
    for key, name in (("source_sha256", "sage_control.py"),
                      ("runtime_sha256", "sage_runtime_info.json"),
                      ("cases_sha256", "cases.jsonl")):
        assert sage_p[key] == sha(HERE / name)
    assert sage["protocol_sha256"] == sha(HERE / "sage_protocol.json")
    assert sage["status"] == "PASS_CHECKED_SAGE_POSITIVE_FAMILY_REPLAY"
    assert sage["product_codes"] == p["positive_family"] and sage["sign_assignments"] == 2
    proof = (HERE / "BilinearGate.lean").read_text()
    assert not any(token in proof for token in ("sorry", "admit", "sorryAx"))
    log = (HERE / "lean_check.log").read_text()
    assert log.count("does not depend on any axioms") == 4 and "error:" not in log
    bound = load("transfer_bound.json")
    assert bound["status"] == "EXACT_LITERAL_BILINEAR_LIFT_BOUND"
    assert bound["protocol_sha256"] == sha(HERE / "protocol.json")
    assert bound["first_pivot_variables_lower_bound"] == 341
    assert bound["first_pivot_nullity_lower_bound_if_consistent"] == 210
    assert bound["affine_candidates_lower_bound_if_consistent"] == 2**210
    assert bound["ordered_product_family_pairs"] == 2**70
    result = {"status": "PASS_TERMINAL_AUDIT",
              "protocol_sha256": sha(HERE / "protocol.json"),
              "cases": len(rows), "rank_rejects": 2,
              "pivot_direct_equalities": len(rows),
              "independent_rank_cases": 64,
              "independent_direct_cases": 16,
              "checked_sage_sign_assignments": sage["sign_assignments"],
              "lean_axiom_free_declarations": 4}
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
