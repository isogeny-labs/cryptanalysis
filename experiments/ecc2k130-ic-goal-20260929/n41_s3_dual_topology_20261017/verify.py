"""Read back source, formula, proof, chart, group and public-query receipts."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    p, b, q, r = (read(D / name) for name in
                   ("protocol.json", "build_result.json", "query_protocol_v2.json",
                    "query_v2_result.json"))
    audit, formula, chart = (read(D / name) for name in
                             ("audit_result.json", "formula_audit_result.json",
                              "chart_audit_result.json"))
    assert p["candidate_id"] is None and q["candidate_id"] is None
    assert p["second_links"] == [[0, 3, 6], [1, 4, 7], [2, 5, 8],
                                  [6, 7, 9], [9, 8, 10]]
    assert sha(D / "circuit.py") == p["circuit_sha256"]
    assert sha(D / "build.py") == p["builder_sha256"]
    assert sha(D / "sage_runtime_info.json") == p["runtime_info_sha256"]
    for relative, digest in p["sources"].items():
        assert sha(ROOT / relative) == digest, relative
    prior = read(ROOT / "n41_s3_rationality_propagation_20261017/verification.json")
    assert prior["status"] == "PASS_PUBLIC_DIRECT_LEAF_RECEIPTS"
    assert b["status"] == "PASS_DUAL_TREE_PUBLIC_FORMULA_BUILD"
    assert b["protocol_sha256"] == sha(D / "protocol.json")
    assert b["assignment_check"]["clauses"] == b["ordinary_clauses"]
    assert b["assignment_check"]["native_xor_rows"] == b["native_xor_rows"]
    assert b["first_tree_and_gates"] == 16851
    assert b["second_tree_added_and_gates"] == b["and_gates"] - 16851
    assert sha(D / "public.xcnf") == b["formula_sha256"] == formula["formula_sha256"]
    assert formula["status"] == "PASS_DUAL_TREE_FORMULA_READBACK"
    assert formula["source_code_variables"] == 42 and formula["source_code_unit_clauses"] == 0
    assert audit["status"] == "PASS_INDEPENDENT_DUAL_TREE_GROUP_REPLAY"
    assert audit["protocol_sha256"] == sha(D / "protocol.json")
    assert audit["build_result_sha256"] == sha(D / "build_result.json")
    assert audit["audit_source_sha256"] == sha(D / "audit_sage.py")
    assert audit["witness_state_ids"] == [12, 122, 116, 47, 128, 34]
    assert audit["distinct_columns"] == 12
    assert all(item["target_reached"] and item["intermediate_count"] == 4
               for item in audit["trees"])
    assert chart["status"] == "PASS_DUAL_TREE_CHART_AUDIT"
    assert chart["audit_source_sha256"] == sha(D / "chart_audit_sage.py")
    assert chart["valid_first_level_pair_counts"] == [24864] * 3
    assert chart["first_level_zero_x_or_identity"] == []
    assert chart["valid_node9_zero_x_or_identity"] == []
    assert (D / "lean_build.exit").read_text().strip() == "0"
    assert (D / "lean_build.stderr").read_text() == ""
    assert "'DualTree.same_sum' depends on axioms: [propext]" in (D / "lean_build.stdout").read_text()
    lean = (D / "DualTree.lean").read_text()
    assert not any(token in lean for token in ("sorry", "admit", "sorryAx", "native_decide"))
    assert sha(D / "run_public_v2.py") == q["runner_sha256"]
    assert sha(Path(q["solver_path"])) == q["solver_sha256"]
    assert q["worker_count"] == 1 and q["rss_cap_bytes"] == 4 * (1 << 30)
    assert q["parent_wall_cap_s"] == 600 and q["solver_flags"][0] == "--threads=1"
    for name, digest in q["sources"].items():
        assert sha(D / name) == digest, name
    assert sha(D / "query_protocol_v2.json") == r["query_protocol_sha256"]
    assert sha(D / "solver_v2.stdout") == r["stdout_sha256"]
    assert sha(D / "solver_v2.stderr") == r["stderr_sha256"]
    assert r["status"] in ("BOUNDED_UNKNOWN", "SAT_PENDING_REPLAY")
    assert not r["monitor_degraded"]
    assert r["sampled_peak_combined_rss_bytes"] < q["rss_cap_bytes"]
    assert (D / "solver_v2.stderr").read_text() == ""
    failure = read(D / "build_v1_failure.json")
    assert failure["status"] == "PRODUCER_FAILURE"
    assert failure["protocol_sha256"] == sha(D / "protocol_v1.json")
    assert failure["stderr_sha256"] == sha(D / "build_v1.stderr")
    launch_failure = read(D / "query_launch_v1_failure.json")
    assert launch_failure["status"] == "PRODUCER_FAILURE"
    assert launch_failure["query_protocol_sha256"] == sha(D / "query_protocol_v2.json")
    assert launch_failure["raw_replay_exit_code"] == 1
    assert launch_failure["raw_replay_stdout_sha256"] == sha(D / "query_launch_v1.stdout")
    assert launch_failure["raw_replay_stderr_sha256"] == sha(D / "query_launch_v1.stderr")
    output = {"status": "PASS_BOUNDED_DUAL_TREE_READBACK" if r["status"] == "BOUNDED_UNKNOWN"
              else "PENDING_SAT_MODEL_REPLAY",
              "protocol_sha256": sha(D / "protocol.json"),
              "build_result_sha256": sha(D / "build_result.json"),
              "query_result_sha256": sha(D / "query_v2_result.json"),
              "query_status": r["status"],
              "verified_group_relation_state_ids": audit["witness_state_ids"],
              "source_code_variables": formula["source_code_variables"],
              "dual_chart_exceptions": 0,
              "lean_axioms": ["propext"]}
    (D / "verification.json").write_text(json.dumps(output, sort_keys=True, indent=2) + "\n")
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
