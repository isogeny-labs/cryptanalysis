"""Replay the inverse-trace N131 ordinary formula and terminal receipt."""

import hashlib
import json
import tempfile
from pathlib import Path

import inverse9

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n131_w18_ninepair_orbit_20261012"
SHIELD = HERE.parent / "n131_w18_ninepair_orbit_shield_20261012"
INVERSE = HERE.parent / "n131_w18_inverse_trace_terminal_20261011"
BALANCED = HERE.parent / "n131_w18_ninepair_balanced_20261012"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    frozen = inverse9.orbit9.protocol()
    control = json.loads((HERE / "control_result.json").read_text())
    query = json.loads((HERE / "query_result.json").read_text())
    sage = json.loads((PARENT / "sage_audit_result.json").read_text())
    shield_audit = json.loads((SHIELD / "shield_audit_result.json").read_text())
    baseline = json.loads((SHIELD / "protocol.json").read_text())
    for key in ("curve_id", "workload_id", "public_target", "fixed_seed_mask",
                "free_pair_rotations", "source_codes_per_slot", "target_choice_count",
                "worker_count", "combined_rss_cap_bytes", "solver_flags",
                "total_target_dependent_cap_seconds"):
        assert frozen[key] == baseline[key], key
    assert {key: value for key, value in frozen["source_sha256"].items()
            if key not in ("runner", "source_shield", "balanced_runner",
                           "inverse_gate_source", "inverse_gate_equivalence")} == \
        {key: value for key, value in baseline["source_sha256"].items()
         if key not in ("runner", "source_shield")}
    assert frozen["source_sha256"]["source_shield"] == \
        baseline["source_sha256"]["source_shield"]
    assert control["status"] == "PASS_FULL_N131_NINEPAIR_ORBIT_CONSTRUCTED_WITNESS"
    assert control["variant"] == "balanced_inverse_trace_source"
    assert control["tree"] == [list(edge) for edge in inverse9.TREE]
    assert control["tree_depth"] == 4
    assert control["protocol_sha256"] == sha(HERE / "protocol.json")
    assert control["formula"]["xcnf_sha256"] == sha(HERE / "control.xcnf")
    assert control["assignment_check"] == {
        "clauses": control["formula"]["clauses"],
        "native_xor_rows": control["formula"]["native_xor_rows"]}
    assert shield_audit["status"] == "PASS_EXACT_N131_NINEPAIR_SOURCE_SHIELD"
    gate = json.loads((INVERSE / "gate_equivalence.json").read_text())
    gate_control = json.loads((HERE / "control_gate_sage.json").read_text())
    assert gate["status"] == "PASS_EXACT_SOURCE_GATE_EQUIVALENCE"
    assert gate["canonical_codes"] == 33191
    assert gate["same_folded_column_pairs"] == 0
    assert gate_control["status"] == "PASS_SAGE_N131_NINEPAIR_INVERSE_TRACE_CONTROL"
    assert gate_control["inverse_witness_checks"] == 18
    assert gate_control["distinct_folded_columns"] == 18
    assert len(inverse9.shield.source_conflicts()) == 65
    assert sage["status"] == "PASS_SAGE_ALL_524_N131_ORBIT_FIBER_CHOICES"
    assert sage["challenge"]["public_target"] == frozen["public_target"]
    assert sage["challenge"]["choices_checked"] == 524
    assert sage["constructed"]["choices_checked"] == 524
    assert query["protocol_sha256"] == sha(HERE / "protocol.json")
    assert query["public_target"] == frozen["public_target"]
    assert query["workload_id"] == frozen["workload_id"]
    assert query["target_choice_count"] == query["distinct_target_reciprocals"] == 524
    comparison_protocol = json.loads((BALANCED / "protocol.json").read_text())
    comparison_control = json.loads((BALANCED / "control_result.json").read_text())
    comparison_query = json.loads((BALANCED / "query_result.json").read_text())
    for key in ("curve_id", "workload_id", "public_target", "fixed_seed_mask",
                "free_pair_rotations", "source_codes_per_slot", "target_choice_count",
                "worker_count", "combined_rss_cap_bytes", "solver_flags",
                "total_target_dependent_cap_seconds"):
        assert frozen[key] == comparison_protocol[key], key
    assert comparison_control["variant"] == "balanced_addition_tree"
    assert comparison_query["status"] == "BOUNDED_UNKNOWN"
    assert query["worker_count"] == 1
    assert query["solver_flags"] == frozen["solver_flags"]
    assert query["target_dependent_attempt_ns"] == sum(query["phase_ns"].values())
    assert query["peak_combined_rss_bytes_sampled"] <= frozen["combined_rss_cap_bytes"]
    assert query["formula"]["xcnf_sha256"] == sha(HERE / "ordinary.xcnf")
    stdout = (HERE / "solver.stdout.txt").read_text(errors="replace")
    stderr = (HERE / "solver.stderr.txt").read_text(errors="replace")
    assert query["stdout_sha256"] == sha(HERE / "solver.stdout.txt")
    assert query["stderr_sha256"] == sha(HERE / "solver.stderr.txt")
    status_lines = [line for line in stdout.splitlines() if line.startswith("s ")]
    assert query["status_lines"] == status_lines
    assert query["restart_rows"] == sum(line.startswith("c [") for line in stdout.splitlines())
    actual_restart_rows = sum(line.startswith("c rst") for line in stdout.splitlines())
    assert actual_restart_rows > 0
    if query["status"] == "BOUNDED_UNKNOWN":
        assert query["stop_reason"] in ("TOTAL_QUERY_TIMEOUT", "RSS_CAP", None)
        assert not status_lines and not query["decoded_model_saved"]
    elif query["status"] == "SAT_PENDING_GROUP_REPLAY":
        assert "s SATISFIABLE" in status_lines
        assert query["decoded_model_saved"]
    elif query["status"] == "UNSAT":
        assert "s UNSATISFIABLE" in status_lines
    else:
        raise AssertionError("unclassified terminal status")
    target = inverse9.base.target_record()
    rows = inverse9.orbit9.orbit_rows([row["point"] for row in target["preimages"]])
    _, root, nodes = inverse9.base.source_domain()
    circuit, _ = inverse9.build([row["standard_reciprocal"] for row in rows], root, nodes)
    with tempfile.TemporaryDirectory(dir=HERE) as directory:
        replay = Path(directory) / "ordinary-replay.xcnf"
        circuit.write(replay)
        assert sha(replay) == query["formula"]["xcnf_sha256"]
        assert replay.stat().st_size == query["formula"]["xcnf_bytes"]
    assert circuit.next_var - 1 == query["formula"]["variables"]
    assert circuit.and_count == query["formula"]["and_gates"]
    assert len(circuit.clauses) == query["formula"]["clauses"]
    assert len(circuit.xors) == query["formula"]["native_xor_rows"]
    result = {
        "status": "PASS_N131_INVERSE_TRACE_TREE_RECEIPT_AUDIT",
        "candidate_id": None, "query_status": query["status"],
        "actual_solver_restart_rows": actual_restart_rows,
        "stderr_empty": stderr == "",
        "ordinary_xcnf_rebuilt_byte_for_byte": True,
        "target_dependent_attempt_ns": query["target_dependent_attempt_ns"],
        "paired_formula_difference": {
            key: query["formula"][key] - comparison_query["formula"][key]
            for key in ("variables", "and_gates", "clauses", "native_xor_rows", "xcnf_bytes")},
        "sha256": {"auditor": sha(Path(__file__)),
                   "protocol": sha(HERE / "protocol.json"),
                   "control": sha(HERE / "control_result.json"),
                   "query": sha(HERE / "query_result.json"),
                   "ordinary_formula": sha(HERE / "ordinary.xcnf"),
                   "stdout": sha(HERE / "solver.stdout.txt"),
                   "stderr": sha(HERE / "solver.stderr.txt"),
                   "control_gate_sage": sha(HERE / "control_gate_sage.json"),
                   "comparison_protocol": sha(BALANCED / "protocol.json"),
                   "comparison_query": sha(BALANCED / "query_result.json")}}
    with (HERE / "audit_result.json").open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(result["status"], query["status"], actual_restart_rows)


if __name__ == "__main__":
    main()
