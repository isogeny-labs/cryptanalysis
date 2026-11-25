"""Independently rebuild and audit the terminal signature-gated public query."""

import hashlib
import json
import tempfile
from pathlib import Path

import gate_v2

HERE = Path(__file__).resolve().parent
SAT = HERE / "sat"
prior = gate_v2.prior


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


frozen_audit = json.loads((HERE / "query_audit_protocol.json").read_text())
for key, path in {
    "audit_source": Path(__file__),
    "sat_protocol": SAT / "protocol.json",
    "public_gate_protocol": HERE / "public_gate_protocol.json",
    "fast_audit": HERE / "fast_audit_result.json",
    "query": SAT / "query_result.json",
    "ordinary_xcnf": SAT / "ordinary.xcnf",
    "stdout": SAT / "solver.stdout.txt",
    "stderr": SAT / "solver.stderr.txt",
}.items():
    assert sha(path) == frozen_audit["sha256"][key], key

protocol = prior.protocol()
query = json.loads((SAT / "query_result.json").read_text())
assert query["protocol_sha256"] == sha(SAT / "protocol.json")
assert query["curve_id"] == protocol["curve_id"]
assert query["public_target"] == protocol["public_target"]
assert query["workload_id"] == protocol["workload_id"]
assert query["worker_count"] == protocol["worker_count"] == 1
assert query["target_choice_count"] == query["distinct_target_reciprocals"] == 524
assert query["target_dependent_attempt_ns"] == sum(query["phase_ns"].values())
assert query["peak_combined_rss_bytes_sampled"] <= protocol["combined_rss_cap_bytes"]
assert query["formula"]["xcnf_sha256"] == sha(SAT / "ordinary.xcnf")
stdout = (SAT / "solver.stdout.txt").read_text(errors="replace")
stderr = (SAT / "solver.stderr.txt").read_text(errors="replace")
assert query["stdout_sha256"] == sha(SAT / "solver.stdout.txt")
assert query["stderr_sha256"] == sha(SAT / "solver.stderr.txt")
status_lines = [line for line in stdout.splitlines() if line.startswith("s ")]
assert query["status_lines"] == status_lines
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

target = prior.base.target_record()
rows = prior.orbit9.orbit_rows([row["point"] for row in target["preimages"]])
_, root, nodes = prior.base.source_domain()
circuit, _ = gate_v2.gate.build(
    [row["standard_reciprocal"] for row in rows], root, nodes)
with tempfile.TemporaryDirectory(dir=SAT) as directory:
    replay = Path(directory) / "ordinary-replay.xcnf"
    circuit.write(replay)
    assert sha(replay) == query["formula"]["xcnf_sha256"]
    assert replay.stat().st_size == query["formula"]["xcnf_bytes"]
assert circuit.next_var - 1 == query["formula"]["variables"]
assert circuit.and_count == query["formula"]["and_gates"]
assert len(circuit.clauses) == query["formula"]["clauses"]
assert len(circuit.xors) == query["formula"]["native_xor_rows"]
result = {
    "status": "PASS_N131_SIGNATURE_GATE_TERMINAL_RECEIPT_AUDIT",
    "candidate_id": None,
    "query_status": query["status"],
    "ordinary_xcnf_rebuilt_byte_for_byte": True,
    "target_dependent_attempt_ns": query["target_dependent_attempt_ns"],
    "query_audit_protocol_sha256": sha(HERE / "query_audit_protocol.json"),
}
with (HERE / "query_audit_result.json").open("x") as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(result["status"], result["query_status"])
