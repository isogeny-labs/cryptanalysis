"""Independent receipt and exact formula rebuild for the four-fiber query."""

import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
V3 = GOAL / "n41_linked_functional_fullpoint_20261012/v3"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


frozen = read(HERE / "audit_protocol.json")
assert frozen["status"] == "FROZEN_BEFORE_N41_LINKED_FIBER_TERMINAL_AUDIT"
for key, path in {
    "audit_source": Path(__file__), "runner": HERE / "run.py",
    "protocol": HERE / "protocol.json", "result": HERE / "result.json",
    "v3_runner": V3 / "run.py",
}.items():
    assert frozen["sha256"][key] == sha(path), key

protocol, result = read(HERE / "protocol.json"), read(HERE / "result.json")
assert result["status"] == "BOUNDED_UNKNOWN"
assert result["protocol_sha256"] == sha(HERE / "protocol.json")
assert result["public_point"] == protocol["public_point"]
assert result["fiber_order"] == protocol["fiber_order"] == [0, 1, 2, 3]
assert result["worker_count"] == protocol["worker_count"] == 1
assert result["total_target_dependent_ns"] < protocol["total_cap_seconds"] * 10**9
assert len(result["slices"]) == 4

spec = importlib.util.spec_from_file_location("fiber_audit_v3", V3 / "run.py")
solver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(solver)
lists, targets = solver.old.source()
witness = solver.linked_witness(lists, targets)
circuit, wires = solver.formula(lists, targets, False, None)
with tempfile.TemporaryDirectory(dir=HERE) as directory:
    replay = Path(directory) / "replay.xcnf"
    circuit.write(replay)
    assert sha(replay) == sha(HERE / "base.xcnf") == result["base_formula_sha256"]
    assert replay.stat().st_size == result["base_formula_bytes"]
    search_ns = 0
    serialization_ns = 0
    restart_rows = 0
    for row in result["slices"]:
        index = row["fiber"]
        assert index in range(4) and row["status"] == "PARENT_TIME_CAP"
        assert row["slice_parent_cap_seconds"] == protocol["slice_parent_cap_seconds"]
        circuit.clauses.append(f"{wires['flags'][index]} 0")
        circuit.write(replay)
        raw = HERE / f"fiber{index}.xcnf"
        assert sha(replay) == sha(raw) == row["formula_sha256"]
        assert replay.stat().st_size == raw.stat().st_size == row["formula_bytes"]
        if index == witness["target_index"]:
            checked = solver.parent.positive_assignment(circuit, wires, witness)
            assert checked == {"clauses": len(circuit.clauses),
                               "native_xor_rows": len(circuit.xors)}
        circuit.clauses.pop()
        receipt = read(HERE / f"fiber{index}.json")
        assert sha(HERE / f"fiber{index}.json") == row["receipt_sha256"]
        assert receipt["status"] == receipt["stop"] == "PARENT_TIME_CAP"
        assert receipt["terminal_lines"] == [] and receipt["model_check"] is None
        assert receipt["exit_code"] == -9 and receipt["restart_rows"] > 0
        assert receipt["stdout_sha256"] == sha(HERE / f"fiber{index}.stdout")
        assert receipt["stderr_sha256"] == sha(HERE / f"fiber{index}.stderr")
        assert receipt["peak_combined_rss_bytes_sampled"] < protocol["combined_rss_cap_bytes"]
        search_ns += receipt["wall_ns_exploratory"]
        serialization_ns += row["serialization_ns"]
        restart_rows += receipt["restart_rows"]
bookkeeping_ns = (result["total_target_dependent_ns"] -
                  result["base_build_ns_exploratory"] -
                  result["base_serialization_ns"] -
                  serialization_ns - search_ns)
assert bookkeeping_ns >= 0
phase_ns = {
    "base_construction": result["base_build_ns_exploratory"],
    "base_serialization": result["base_serialization_ns"],
    "slice_serialization": serialization_ns,
    "solver_intervals": search_ns,
    "bookkeeping_and_receipt_checks": bookkeeping_ns,
}
assert sum(phase_ns.values()) == result["total_target_dependent_ns"]
output = {"status": "PASS_N41_LINKED_FOUR_FIBER_TERMINAL_AUDIT",
          "candidate_id": None, "portfolio_status": result["status"],
          "all_four_formulas_rebuilt_byte_for_byte": True,
          "known_witness_fiber": witness["target_index"],
          "total_restarts": restart_rows,
          "phase_ns": phase_ns,
          "audit_protocol_sha256": sha(HERE / "audit_protocol.json")}
with (HERE / "audit_result.json").open("x") as stream:
    json.dump(output, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(output["status"], output["portfolio_status"], flush=True)
