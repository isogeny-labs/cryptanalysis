"""Rebuild the ten-pair ordinary XCNF and audit the terminal solver receipt."""

import hashlib
import json
import tempfile
from pathlib import Path

import ten


HERE = Path(__file__).resolve().parent
N41 = HERE.parent / "n41_w8_tenpair_density_control_20261012"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


frozen = ten.protocol()
control = json.loads((HERE / "control_result.json").read_text())
query = json.loads((HERE / "query_result.json").read_text())
sage = json.loads((HERE / "sage_fixture_result.json").read_text())
n41 = json.loads((N41 / "audit_result.json").read_text())
assert frozen["source_pair_slots"] == 10
assert frozen["distinct_folded_columns_required"] == 20
assert len(frozen["free_pair_rotations"]) == 10
assert frozen["worker_count"] == 1
assert frozen["total_target_dependent_cap_seconds"] == 600
assert frozen["combined_rss_cap_bytes"] == 4 * 1024**3
assert n41["status"] == "PASS_INDEPENDENT_N41_PUBLIC_TENPAIR_RELATION"
assert sage["status"] == "PASS_INDEPENDENT_SAGE_TENPAIR_CONSTRUCTED_GROUP_REPLAY"
assert sage["distinct_folded_columns"] == 20
assert control["status"] == "PASS_FULL_N131_TENPAIR_ORBIT_CONSTRUCTED_WITNESS"
assert control["variant"] == "tenpair_balanced_inverse_trace_binary_frobenius"
assert control["source_pair_checks"] == 10 and control["group_link_checks"] == 9
assert control["tree"] == [list(edge) for edge in ten.TREE]
assert control["protocol_sha256"] == sha(HERE / "protocol.json")
assert control["formula"]["xcnf_sha256"] == sha(HERE / "control.xcnf")
assert control["assignment_check"] == {
    "clauses": control["formula"]["clauses"],
    "native_xor_rows": control["formula"]["native_xor_rows"]}
assert query["protocol_sha256"] == sha(HERE / "protocol.json")
assert query["public_target"] == frozen["public_target"]
assert query["workload_id"] == frozen["workload_id"]
assert query["target_choice_count"] == query["distinct_target_reciprocals"] == 524
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
actual_restarts = sum(line.startswith("c rst") for line in stdout.splitlines())
assert actual_restarts > 0
if query["status"] == "BOUNDED_UNKNOWN":
    assert query["stop_reason"] in ("TOTAL_QUERY_TIMEOUT", "RSS_CAP", None)
    assert status_lines in ([], ["s INDETERMINATE"])
    assert not query["decoded_model_saved"]
elif query["status"] == "SAT_PENDING_GROUP_REPLAY":
    assert "s SATISFIABLE" in status_lines and query["decoded_model_saved"]
elif query["status"] == "UNSAT":
    assert "s UNSATISFIABLE" in status_lines
else:
    raise AssertionError("unclassified terminal status")

target = ten.base.target_record()
rows = ten.orbit9.orbit_rows([row["point"] for row in target["preimages"]])
_, root, nodes = ten.base.source_domain()
circuit, _ = ten.build([row["standard_reciprocal"] for row in rows], root, nodes)
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
    "status": "PASS_N131_TENPAIR_BINARY_FROBENIUS_RECEIPT_AUDIT",
    "candidate_id": None,
    "query_status": query["status"],
    "actual_solver_restart_rows": actual_restarts,
    "stderr_empty": stderr == "",
    "ordinary_xcnf_rebuilt_byte_for_byte": True,
    "target_dependent_attempt_ns": query["target_dependent_attempt_ns"],
    "sha256": {"auditor": sha(Path(__file__)),
               "protocol": sha(HERE / "protocol.json"),
               "control": sha(HERE / "control_result.json"),
               "query": sha(HERE / "query_result.json"),
               "ordinary_formula": sha(HERE / "ordinary.xcnf"),
               "stdout": sha(HERE / "solver.stdout.txt"),
               "stderr": sha(HERE / "solver.stderr.txt")},
}
with (HERE / "audit_result.json").open("x") as stream:
    json.dump(result, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(result["status"], query["status"], actual_restarts)
