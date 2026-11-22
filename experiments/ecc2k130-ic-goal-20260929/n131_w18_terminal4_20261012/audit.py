"""Audit frozen four-state query inputs, phase accounting, and transcripts."""

import hashlib
import json
from pathlib import Path

import terminal

HERE = Path(__file__).resolve().parent
BASELINE = HERE.parent / "n131_w18_terminal_fiber_20261011" / "query_result.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    protocol = terminal.check_protocol()
    pool, source = terminal.pool(), read("source_count.json")
    control, query, sage = (read(name) for name in (
        "control_result.json", "query_result.json", "sage_audit_result.json"))
    baseline = json.loads(BASELINE.read_text())
    assert protocol["terminal_signed_states"] == len(pool["states"]) == 4
    assert source["selected_signed_states"] == 4
    assert source["uniform_raw_point_mean_upper_decimal"] == "141.609150594"
    assert control["status"] == "PASS_EXACT_N131_TERMINAL4_CONTROL"
    assert sage["status"] == "PASS_INDEPENDENT_SAGE_TERMINAL4_FIBERS"
    assert control["protocol_sha256"] == query["protocol_sha256"] == sha(HERE / "protocol.json")
    assert sage["sha256"]["query"] == sha(HERE / "query_result.json")
    assert sage["sha256"]["control"] == sha(HERE / "control_result.json")
    assert query["public_target"] == protocol["public_target"] == baseline["public_target"]
    assert query["workload_id"] == protocol["workload_id"] == baseline["workload_id"]
    assert query["raw_preimage_index"] == protocol["raw_preimage_index"] == 0
    assert query["worker_count"] == protocol["worker_count"] == 1
    assert query["solver_flags"] == protocol["solver_flags"]
    assert query["peak_combined_rss_bytes_sampled"] <= protocol["combined_rss_cap_bytes"]
    phases = query["phase_ns"]
    assert set(phases) == {"target_residual_generation_ns", "formula_construction_ns",
                           "formula_serialization_ns", "solver_search_ns",
                           "terminal_parse_and_model_decode_ns"}
    assert all(value >= 0 for value in phases.values())
    assert sum(phases.values()) == query["target_dependent_attempt_ns"]
    assert query["target_dependent_attempt_ns"] <= (protocol["parent_total_query_cap_seconds"] + 2) * 10**9
    for name, receipt in (("control", control), ("ordinary", query)):
        formula = HERE / (name + ".xcnf")
        assert sha(formula) == receipt["formula"]["xcnf_sha256"]
        assert formula.stat().st_size == receipt["formula"]["xcnf_bytes"]
    outpath, errpath = HERE / "solver.stdout.txt", HERE / "solver.stderr.txt"
    assert sha(outpath) == query["stdout_sha256"]
    assert sha(errpath) == query["stderr_sha256"]
    stdout = outpath.read_text(errors="replace")
    assert query["status_lines"] == [line for line in stdout.splitlines() if line.startswith("s ")]
    assert query["restart_rows"] == sum(line.startswith("c rst") for line in stdout.splitlines())
    if query["status"] == "BOUNDED_UNKNOWN":
        assert not query["decoded_model_saved"]
        assert all(line == "s UNKNOWN" for line in query["status_lines"])
    else:
        assert query["status"] in ("SAT_PENDING_GROUP_REPLAY", "UNSAT")
    delta = {key: baseline["formula"][key] - query["formula"][key]
             for key in ("variables", "and_gates", "clauses", "native_xor_rows")}
    assert all(value > 0 for value in delta.values())
    result = {"status": "PASS_N131_TERMINAL4_RECEIPT_AUDIT",
              "solver_status": query["status"], "stop_reason": query["stop_reason"],
              "formula_reduction_vs_32_state": delta,
              "target_dependent_attempt_ns": query["target_dependent_attempt_ns"],
              "phase_sum_ns": sum(phases.values()),
              "source_ceiling_decimal": source["uniform_raw_point_mean_upper_decimal"],
              "sha256": {name: sha(HERE / name) for name in (
                  "audit.py", "protocol.json", "query_result.json", "control_result.json",
                  "sage_audit_result.json", "solver.stdout.txt", "solver.stderr.txt")}}
    with (HERE / "audit_result.json").open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(result["status"], result["formula_reduction_vs_32_state"])


if __name__ == "__main__":
    main()
