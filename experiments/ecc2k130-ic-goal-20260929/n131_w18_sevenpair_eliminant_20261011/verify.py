"""Verify frozen seven-pair eliminant control and public-query receipts."""

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    runner = load("sevenpair_receipt_runner", HERE / "run.py")
    query = load("sevenpair_receipt_query", HERE / "query.py")
    protocol, control = read("protocol.json"), read("control_result.json")
    qp, result = read("query_protocol.json"), read("query_result.json")
    assert protocol["status"] == "FROZEN_SEVENPAIR_ELIMINANT_BEFORE_BUILD"
    assert protocol["source_sha256"] == {name: sha(path) for name, path in runner.sources().items()}
    assert control["status"] == "PASS_SEVENPAIR_ELIMINANT_CONSTRUCTED_WITNESS"
    assert control["protocol_sha256"] == sha(HERE / "protocol.json")
    assert control["constructed_target_raw"] == protocol["constructed_target_raw"]
    assert control["constructed_block_raw"] == protocol["constructed_block_raw"]
    assert control["first_product"] == 3328 and control["terminal_code"] == 10
    assert control["assignment_check"]["clauses"] == control["formula"]["clauses"]
    assert control["assignment_check"]["native_xor_rows"] == control["formula"]["native_xor_rows"]
    assert control["formula"]["xcnf_sha256"] == sha(HERE / "control.xcnf")
    assert not (HERE / "control.stderr.txt").read_bytes()
    assert qp["status"] == "FROZEN_SEVENPAIR_ELIMINANT_PUBLIC_QUERY"
    assert qp["sha256"] == {name: sha(path) for name, path in query.inputs().items()}
    assert result["protocol_sha256"] == sha(HERE / "query_protocol.json")
    assert result["curve_id"] == qp["curve_id"] == protocol["curve_id"]
    assert result["workload_id"] == qp["workload_id"] == protocol["workload_id"]
    assert result["public_target"] == qp["public_target"] == protocol["public_target"]
    assert result["worker_count"] == qp["workers"] == 1
    assert result["solver_flags"] == qp["solver_flags"]
    assert result["solver_started"]
    assert result["status"] == "BOUNDED_UNKNOWN"
    assert result["stop_reason"] == "PARENT_TIMEOUT"
    assert result["solver_exit_code"] == -9
    assert result["status_lines"] == []
    assert result["stdout_sha256"] == sha(HERE / "solver.stdout.txt")
    assert result["stderr_sha256"] == sha(HERE / "solver.stderr.txt")
    assert result["formula"]["xcnf_sha256"] == sha(HERE / "ordinary.xcnf")
    assert result["charged_query_wall_ns"] == sum(result["phases_ns"].values())
    if result["stop_reason"] == "RSS_CAP":
        assert result["sampled_peak_combined_rss_bytes"] > qp["rss_cap_bytes"]
    else:
        assert result["sampled_peak_combined_rss_bytes"] < qp["rss_cap_bytes"]
    if result["stop_reason"] != "PARENT_TIMEOUT":
        assert result["charged_query_wall_ns"] < qp["parent_cap_seconds"]*10**9
    else:
        assert qp["parent_cap_seconds"]*10**9 <= result["charged_query_wall_ns"] < 600_100_000_000
    assert result["formula"]["variables"] == 499045
    assert result["formula"]["and_gates"] == 228256
    assert result["formula"]["clauses"] == 686791
    assert result["formula"]["native_xor_rows"] == 268804
    stdout = (HERE / "solver.stdout.txt").read_text(errors="replace")
    assert result["status_lines"] == [line for line in stdout.splitlines() if line.startswith("s ")]
    assert result["restart_rows"] == sum(line.startswith("c [") for line in stdout.splitlines())
    assert not result["decoded_model_saved"]
    print(json.dumps({"status": "PASS_SEVENPAIR_ELIMINANT_RECEIPTS",
                      "ordinary_status": result["status"],
                      "and_gates": result["formula"]["and_gates"],
                      "restart_rows": result["restart_rows"]}, sort_keys=True))


if __name__ == "__main__":
    main()
