"""Audit the target-conjugate XCNF against independent Sage residuals."""

import hashlib
import json
import tempfile
from pathlib import Path

import frob

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    protocol = frob.protocol()
    control = read("control_result.json")
    query = read("query_result.json")
    preflight = read("preflight_result.json")
    n41 = read("n41_orbit_control_result.json")
    sage = read("sage_residuals.json")
    assert control["status"] == "PASS_N131_FROBENIUS_TARGET_FIBER_CONTROL"
    assert preflight["status"] == "PASS_EXACT_524_BATCH_RESIDUAL_REPLAY"
    assert n41["status"] == "PASS_N41_FROBENIUS_ORBIT_RELATION_TRANSPORT"
    assert sage["status"] == "PASS_INDEPENDENT_SAGE_524_FROBENIUS_RESIDUALS"
    assert control["protocol_sha256"] == query["protocol_sha256"] == sha(HERE / "protocol.json")
    assert sage["source_sha256"]["query"] == sha(HERE / "query_result.json")
    assert query["curve_id"] == protocol["curve_id"] == sage["curve_id"]
    assert query["workload_id"] == protocol["workload_id"] == sage["workload_id"]
    assert query["public_target"] == protocol["public_target"]
    assert query["raw_preimage_index"] == protocol["raw_preimage_index"] == 0
    assert query["worker_count"] == protocol["worker_count"] == 1
    assert query["solver_flags"] == protocol["solver_flags"]
    assert query["target_rotations"] == sage["target_orbit_size"] == 131
    assert query["terminal_states_per_rotation"] == sage["terminal_states"] == 4
    assert query["residual_count"] == query["distinct_residuals"] == len(sage["residuals"]) == 524
    assert sage["full_signed_frobenius_base_size"] == protocol["source_geometry"]["full_signed_frobenius_base_size"]
    residuals = frob.residuals(query["raw_target"])
    assert residuals == sage["residuals"]
    _, root, nodes = frob.terminal.base.source_domain()
    circuit, wires = frob.terminal.build(
        [row["standard_reciprocal"] for row in sage["residuals"]], root, nodes)
    assert len(wires["choices"]) == 524
    with tempfile.TemporaryDirectory(prefix="n131-frob-formula-", dir="/private/tmp") as temporary:
        rebuilt = Path(temporary) / "ordinary.xcnf"
        circuit.write(rebuilt)
        assert sha(rebuilt) == query["formula"]["xcnf_sha256"]
        assert rebuilt.stat().st_size == query["formula"]["xcnf_bytes"]
    del circuit
    formula = HERE / "ordinary.xcnf"
    assert sha(formula) == query["formula"]["xcnf_sha256"]
    assert formula.stat().st_size == query["formula"]["xcnf_bytes"]
    control_formula = HERE / "control.xcnf"
    assert sha(control_formula) == control["formula"]["xcnf_sha256"]
    assert control_formula.stat().st_size == control["formula"]["xcnf_bytes"]
    phases = query["phase_ns"]
    assert set(phases) == {"target_orbit_and_residuals_ns", "formula_construction_ns",
                           "formula_serialization_ns", "solver_search_ns",
                           "terminal_parse_and_decode_ns"}
    assert all(value >= 0 for value in phases.values())
    assert sum(phases.values()) == query["target_dependent_attempt_ns"]
    assert query["target_dependent_attempt_ns"] <= (
        protocol["total_target_dependent_cap_seconds"] + 2) * 10**9
    assert query["peak_combined_rss_bytes_sampled"] <= protocol["combined_rss_cap_bytes"]
    outpath, errpath = HERE / "solver.stdout.txt", HERE / "solver.stderr.txt"
    assert sha(outpath) == query["stdout_sha256"]
    assert sha(errpath) == query["stderr_sha256"]
    stdout = outpath.read_text(errors="replace")
    assert query["status_lines"] == [line for line in stdout.splitlines() if line.startswith("s ")]
    assert query["restart_rows"] == sum(line.startswith("c rst") for line in stdout.splitlines())
    if query["status"] == "BOUNDED_UNKNOWN":
        assert not query["decoded_model_saved"]
        assert not any(line in ("s SATISFIABLE", "s UNSATISFIABLE")
                       for line in query["status_lines"])
        assert query["restart_rows"] > 0
    elif query["status"] == "SAT_PENDING_GROUP_REPLAY":
        assert query["decoded_model_saved"] and (HERE / "decoded_model.json").is_file()
    else:
        assert query["status"] == "UNSAT" and "s UNSATISFIABLE" in query["status_lines"]
    result = {"status": "PASS_N131_FROBENIUS_TARGET_FIBER_RECEIPT_AUDIT",
              "solver_status": query["status"],
              "target_dependent_attempt_ns": query["target_dependent_attempt_ns"],
              "phase_sum_ns": sum(phases.values()),
              "exact_formula_rebuild_sha256": query["formula"]["xcnf_sha256"],
              "residuals_independently_replayed": len(residuals),
              "sha256": {name: sha(HERE / name) for name in (
                  "audit.py", "protocol.json", "preflight_result.json",
                  "n41_orbit_control_result.json", "control_result.json",
                  "query_result.json", "sage_residuals.json", "solver.stdout.txt",
                  "solver.stderr.txt")}}
    with (HERE / "audit_result.json").open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(result["status"], result["solver_status"])


if __name__ == "__main__":
    main()
