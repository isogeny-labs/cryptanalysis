"""Read-only checks for this capped, ordinary-Q solver attempt."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    started = json.loads((HERE / "started.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    attempt = result["attempts"]
    assert started["workload_id"] == result["workload_id"] == "3c1992b7c92f"
    assert started["target_count"] == result["target_count"] == 1
    assert started["formula_sha256"] == result["formula_sha256"]
    assert result["status"] == "timeout" and result["solver_launched"]
    assert result["decoded_rows"] is None and result["decoded_relation_count"] == 0
    assert len(attempt) == 1
    first = attempt[0]
    assert first["solver_status"] == "indeterminate"
    assert first["solver_stop_reason"] == "parent_timeout"
    assert first["solver_exit_code"] == -15
    query = HERE / "bound_query.xcnf"
    solver_query = HERE / "attempts/model_01/query.xcnf"
    stdout = HERE / "attempts/model_01/cryptominisat.stdout.txt"
    stderr = HERE / "attempts/model_01/cryptominisat.stderr.txt"
    assert sha(query) == sha(solver_query) == first["formula_sha256"] == result["formula_sha256"]
    assert sha(stdout) == first["stdout_sha256"]
    assert sha(stderr) == first["stderr_sha256"]
    lines = stdout.read_text().splitlines()
    assert not any(line.startswith(("s SATISFIABLE", "s UNSATISFIABLE", "v ")) for line in lines)
    phases = result["phase_wall_ns"]
    assert phases["T_target_query"] + phases["T_target_PDP"] + \
           phases["T_target_relation_check"] == result["partial_query_charged_wall_ns"]
    cap = started["frozen_resource_envelope"]["combined_rss_limit_bytes"]
    assert result["rss_gate_passed"] and result["conservative_peak_rss_bound_bytes"] <= cap
    assert first["combined_peak_rss_bytes"] <= cap
    expected_source = ROOT / "run_q1358_public_q_probe.py"
    assert sha(expected_source) == started["runner_source_sha256"]
    record = {
        "status": "PASS_CENSORED_Q1358_ORDINARY_QUERY_RECEIPT",
        "curve_id": result["curve_id"],
        "workload_id": result["workload_id"],
        "target_count": 1,
        "charged_wall_ns": result["partial_query_charged_wall_ns"],
        "phase_wall_ns": phases,
        "stop_reason": first["solver_stop_reason"],
        "solver_exit_code": first["solver_exit_code"],
        "resource_cap_bytes": cap,
        "conservative_peak_rss_bound_bytes": result["conservative_peak_rss_bound_bytes"],
        "decoded_model_count": 0,
        "raw_terminal_sat_or_unsat": False,
        "input_sha256": {name: sha(HERE / name) for name in ("started.json", "result.json")},
        "attempt_sha256": {"query": sha(solver_query), "stdout": sha(stdout),
                           "stderr": sha(stderr)},
    }
    output = HERE / "terminal_verification.json"
    with output.open("x") as stream:
        json.dump(record, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(record, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
