"""Check the frozen public formula and CPU-limited solver-stage receipt."""

import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n131_w18_all_fibers_inverse_20261011"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "replay_result.json").read_text())
    previous = json.loads((PARENT / "query_result.json").read_text())
    archive = json.loads((PARENT / "archive_receipt.json").read_text())
    stdout = (HERE / "solver.stdout.txt").read_text(errors="replace")
    assert protocol["status"] == "FROZEN_CPU300_REPLAY"
    assert protocol["runner_sha256"] == sha(HERE / "replay.py")
    assert protocol["parent_query_sha256"] == sha(PARENT / "query_result.json")
    assert protocol["parent_protocol_sha256"] == sha(PARENT / "protocol.json")
    assert protocol["archive_sha256"] == sha(PARENT / "ordinary.xcnf.gz")
    assert protocol["formula_sha256"] == previous["formula"]["xcnf_sha256"]
    assert protocol["formula_sha256"] == archive["ordinary"]["raw_sha256"]
    with gzip.open(PARENT / "ordinary.xcnf.gz", "rb") as stream:
        raw = stream.read()
    assert len(raw) == protocol["formula_bytes"]
    assert hashlib.sha256(raw).hexdigest() == protocol["formula_sha256"]
    assert result["formula_sha256"] == protocol["formula_sha256"]
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert result["solver_sha256"] == protocol["solver_sha256"]
    assert result["public_target"] == previous["public_target"]
    assert result["workload_id"] == previous["workload_id"]
    assert result["worker_count"] == 1
    assert result["stdout_sha256"] == sha(HERE / "solver.stdout.txt")
    assert result["stderr_sha256"] == sha(HERE / "solver.stderr.txt")
    assert result["restart_rows"] == sum(line.startswith("c rst")
                                         for line in stdout.splitlines())
    assert result["status_lines"] == [line for line in stdout.splitlines()
                                      if line.startswith("s ")]
    assert result["solver_stage_wall_ns"] > 0
    assert result["solver_cpu_seconds_rusage"] >= 0
    assert result["solver_cpu_seconds_sampled"] >= 0
    assert result["peak_combined_rss_bytes_sampled"] > 0
    assert sum(previous["phase_ns"].values()) == previous["target_dependent_attempt_ns"]
    if result["status"] == "BOUNDED_UNKNOWN":
        assert result["stop_reason"] is not None
        assert not result["status_lines"]
    elif result["status"] == "SAT_PENDING_GROUP_REPLAY":
        assert "s SATISFIABLE" in result["status_lines"]
    else:
        assert result["status"] == "UNSAT"
        assert "s UNSATISFIABLE" in result["status_lines"]
    receipt = {
        "status": "PASS_FROZEN_FORMULA_CPU_REPLAY_RECEIPT",
        "candidate_id": None,
        "formula_sha256": protocol["formula_sha256"],
        "public_target": result["public_target"],
        "previous_online_attempt_ns": previous["target_dependent_attempt_ns"],
        "previous_solver_cpu_seconds_sampled": previous["solver_cpu_seconds_sampled"],
        "replay_solver_cpu_seconds_rusage": result["solver_cpu_seconds_rusage"],
        "replay_solver_stage_wall_ns": result["solver_stage_wall_ns"],
        "replay_status": result["status"],
        "replay_stop_reason": result["stop_reason"],
        "replay_restart_rows": result["restart_rows"],
    }
    with (HERE / "audit_result.json").open("x") as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(receipt["status"])


if __name__ == "__main__":
    main()
