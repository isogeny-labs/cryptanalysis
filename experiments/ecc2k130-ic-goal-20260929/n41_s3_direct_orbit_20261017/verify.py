"""Read back the compact-orbit source, 41 controls, proof and public query."""
import ast
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
    p, build, q, result, audit = (read(D / name) for name in (
        "protocol.json", "build_result.json", "query_protocol_v2.json",
        "query_v2_result.json", "formula_audit_result.json"))
    assert p["candidate_id"] is None and q["candidate_id"] is None
    assert sha(D / "circuit.py") == p["circuit_sha256"]
    assert sha(D / "build.py") == p["builder_sha256"]
    assert sha(D / "sage_runtime_info.json") == p["runtime_info_sha256"]
    for relative, digest in p["sources"].items():
        assert sha(ROOT / relative) == digest, relative
    prior_leaf = read(ROOT / "n41_s3_rationality_propagation_20261017/verification.json")
    assert prior_leaf["status"] == "PASS_PUBLIC_DIRECT_LEAF_RECEIPTS"
    prior_join = read(ROOT / "n41_sixpair_target_orbit_20261016/join_result.json")
    prior_group = read(ROOT / "n41_sixpair_target_orbit_20261016/join_audit.json")
    assert prior_group["status"] == "PASS_N41_41_ORBIT_GROUP_AND_ROW_AUDIT"
    assert prior_group["join_sha256"] == sha(ROOT / "n41_sixpair_target_orbit_20261016/join_result.json")
    assert prior_group["relation_count"] == 41 and prior_group["final_rank"] == 41
    assert build["status"] == "PASS_DIRECT_LEAF_ORBIT_FORMULA_BUILD"
    assert build["protocol_sha256"] == sha(D / "protocol.json")
    assert build["orbit_size"] == 41 and len(set(build["target_orbit"])) == 41
    assert build["and_gates"] == 18491
    assert build["ordinary_clauses"] == 57984
    assert build["native_xor_rows"] == 3112
    assert len(build["controls"]) == 41
    for j, control in enumerate(build["controls"]):
        words = prior_join["hits"][j].split()
        assert control["orbit_index"] == int(words[1]) == j
        assert control["state_ids"] == [int(x) for x in words[2:8]]
        assert control["checked_variables"] == build["variables"] + 1
    assert audit["status"] == "PASS_DIRECT_LEAF_ORBIT_FORMULA_READBACK"
    assert audit["audit_source_sha256"] == sha(D / "audit_formula.py")
    assert audit["protocol_sha256"] == sha(D / "protocol.json")
    assert audit["build_result_sha256"] == sha(D / "build_result.json")
    assert audit["source_code_variables"] == 42
    assert audit["target_selector_variables"] == 41
    assert audit["selector_pair_exclusions"] == 820
    assert audit["source_or_selector_unit_clauses"] == 0
    assert sha(D / "public.xcnf") == audit["formula_sha256"] == build["formula_sha256"]
    assert (D / "lean_build.exit").read_text().strip() == "0"
    assert (D / "lean_build.stderr").read_text() == ""
    assert "'SixPairTargetOrbit.relation_pullback' depends on axioms: [propext, Quot.sound]" in (
        D / "lean_build.stdout").read_text()
    assert sha(D / "OrbitTransport.lean") == sha(
        ROOT / "n41_sixpair_target_orbit_20261016/OrbitTransport.lean")
    lean = (D / "OrbitTransport.lean").read_text()
    assert not any(token in lean for token in ("sorry", "admit", "sorryAx", "native_decide"))
    failure = read(D / "freeze_v1_failure.json")
    assert failure["status"] == "PRODUCER_FAILURE" and failure["exit_code"] == 1
    assert failure["source_sha256"] == sha(D / "freeze_v1.py")
    assert failure["stdout_sha256"] == sha(D / "freeze_v1.stdout")
    assert failure["stderr_sha256"] == sha(D / "freeze_v1.stderr")
    ast.parse((D / "replay_sat_sage.py").read_text())
    assert sha(D / "run_public_v2.py") == q["runner_sha256"]
    assert sha(Path(q["solver_path"])) == q["solver_sha256"]
    assert q["worker_count"] == 1 and q["rss_cap_bytes"] == 4 * (1 << 30)
    assert q["parent_wall_cap_s"] == 600 and q["solver_flags"][0] == "--threads=1"
    for name, digest in q["sources"].items():
        assert sha(D / name) == digest, name
    assert sha(D / "query_protocol_v2.json") == result["query_protocol_sha256"]
    assert sha(D / "solver_v2.stdout") == result["stdout_sha256"]
    assert sha(D / "solver_v2.stderr") == result["stderr_sha256"]
    assert (D / "solver_v2.stderr").read_text() == ""
    assert not result["monitor_degraded"]
    assert result["sampled_peak_combined_rss_bytes"] < q["rss_cap_bytes"]
    assert result["status"] in ("BOUNDED_UNKNOWN", "SAT_PENDING_REPLAY")
    status = ("PASS_BOUNDED_DIRECT_ORBIT_READBACK" if result["status"] == "BOUNDED_UNKNOWN"
              else "PENDING_SAT_MODEL_REPLAY")
    if result["status"] == "BOUNDED_UNKNOWN":
        assert result["stop_reason"] == "PARENT_WALL_CAP"
        assert not result["terminal_lines"]
    output = {"status": status,
              "protocol_sha256": sha(D / "protocol.json"),
              "build_result_sha256": sha(D / "build_result.json"),
              "query_result_sha256": sha(D / "query_v2_result.json"),
              "query_status": result["status"],
              "checked_archived_orbit_assignments": len(build["controls"]),
              "independent_archived_group_replays": prior_group["relation_count"],
              "conditional_model_replay_sha256": sha(D / "replay_sat_sage.py"),
              "lean_axioms": ["propext", "Quot.sound"]}
    (D / "verification.json").write_text(json.dumps(output, sort_keys=True, indent=2) + "\n")
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
