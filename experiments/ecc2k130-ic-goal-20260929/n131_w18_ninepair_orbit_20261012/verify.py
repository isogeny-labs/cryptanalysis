"""Audit frozen N131 nine-pair orbit receipts and rebuild the ordinary XCNF."""

import hashlib
import json
import tempfile
from pathlib import Path

import orbit9

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    frozen = orbit9.protocol()
    control = json.loads((HERE / "control_result.json").read_text())
    sage = json.loads((HERE / "sage_audit_result.json").read_text())
    query = json.loads((HERE / "query_result.json").read_text())
    assert frozen["target_choice_count"] == 524
    assert control["status"] == "PASS_FULL_N131_NINEPAIR_ORBIT_CONSTRUCTED_WITNESS"
    assert control["protocol_sha256"] == sha(HERE / "protocol.json")
    assert control["formula"]["xcnf_sha256"] == sha(HERE / "control.xcnf")
    assert control["assignment_check"]["clauses"] == control["formula"]["clauses"]
    assert control["assignment_check"]["native_xor_rows"] == control["formula"]["native_xor_rows"]
    assert sage["status"] == "PASS_SAGE_ALL_524_N131_ORBIT_FIBER_CHOICES"
    assert sage["sha256"]["protocol"] == sha(HERE / "protocol.json")
    assert sage["sha256"]["runner"] == sha(HERE / "orbit9.py")
    assert sage["sha256"]["control"] == sha(HERE / "control_result.json")
    assert sage["challenge"]["public_target"] == frozen["public_target"]
    assert sage["challenge"]["choices_checked"] == 524
    assert sage["constructed"]["choices_checked"] == 524
    assert query["protocol_sha256"] == sha(HERE / "protocol.json")
    assert query["public_target"] == frozen["public_target"]
    assert query["workload_id"] == frozen["workload_id"]
    assert query["target_choice_count"] == 524
    assert query["distinct_target_reciprocals"] == 524
    assert query["worker_count"] == frozen["worker_count"] == 1
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
    assert actual_restart_rows > 0  # Solver entered search.
    if query["status"] == "BOUNDED_UNKNOWN":
        assert query["stop_reason"] in (None, "TOTAL_QUERY_TIMEOUT", "RSS_CAP")
        assert not any(line in ("s SATISFIABLE", "s UNSATISFIABLE")
                       for line in status_lines)
        assert not query["decoded_model_saved"]
    elif query["status"] == "SAT_PENDING_GROUP_REPLAY":
        assert "s SATISFIABLE" in status_lines
        assert query["decoded_model_saved"] and (HERE / "decoded_model.json").is_file()
    elif query["status"] == "UNSAT":
        assert "s UNSATISFIABLE" in status_lines
    else:
        raise AssertionError("unclassified query status")

    target = orbit9.base.target_record()
    rows = orbit9.orbit_rows([row["point"] for row in target["preimages"]])
    _, root, nodes = orbit9.base.source_domain()
    circuit, _ = orbit9.build([row["standard_reciprocal"] for row in rows], root, nodes)
    with tempfile.TemporaryDirectory(dir=HERE) as directory:
        replay = Path(directory) / "ordinary-replay.xcnf"
        circuit.write(replay)
        assert sha(replay) == query["formula"]["xcnf_sha256"]
        assert replay.stat().st_size == query["formula"]["xcnf_bytes"]
    assert circuit.next_var - 1 == query["formula"]["variables"]
    assert circuit.and_count == query["formula"]["and_gates"]
    assert len(circuit.clauses) == query["formula"]["clauses"]
    assert len(circuit.xors) == query["formula"]["native_xor_rows"]
    result = {"status": "PASS_N131_NINEPAIR_ORBIT_RECEIPT_AUDIT",
              "candidate_id": None,
              "query_status": query["status"],
              "actual_solver_restart_rows": actual_restart_rows,
              "query_record_restart_rows_field_is_bracket_diagnostic_count": query["restart_rows"],
              "stderr_empty": stderr == "",
              "ordinary_xcnf_rebuilt_byte_for_byte": True,
              "target_dependent_attempt_ns": query["target_dependent_attempt_ns"],
              "sha256": {"verifier": sha(Path(__file__)),
                         "protocol": sha(HERE / "protocol.json"),
                         "control": sha(HERE / "control_result.json"),
                         "sage_audit": sha(HERE / "sage_audit_result.json"),
                         "query": sha(HERE / "query_result.json"),
                         "ordinary_formula": sha(HERE / "ordinary.xcnf"),
                         "stdout": sha(HERE / "solver.stdout.txt"),
                         "stderr": sha(HERE / "solver.stderr.txt")}}
    with (HERE / "audit_result.json").open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(result["status"], query["status"], actual_restart_rows)


if __name__ == "__main__":
    main()
