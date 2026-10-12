"""Independent receipt checks for the frozen Gaussian solver replay."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "n131_w18_four_seed_sevenpair_ordinary_20261011"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "run_result.json").read_text())
    base = json.loads((BASE / "query_result.json").read_text())
    base_audit = json.loads((BASE / "audit_result.json").read_text())
    archive = json.loads((BASE / "archive_receipt.json").read_text())
    assert protocol["status"] == "FROZEN_N131_SEVENPAIR_GAUSS_REPLAY"
    assert protocol["runner_sha256"] == sha(HERE / "replay.py")
    assert protocol["solver_sha256"] == sha(Path(protocol["solver_path"]))
    assert protocol["base_protocol_sha256"] == sha(BASE / "protocol.json")
    assert protocol["base_formula_sha256"] == base["formula"]["xcnf_sha256"]
    assert protocol["base_formula_sha256"] == archive["raw_sha256"]
    assert protocol["base_formula_bytes"] == archive["raw_bytes"]
    assert base_audit["status"] in {
        "PASS_CENSORED_N131_SEVENPAIR_QUERY_RECEIPT",
        "PASS_VERIFIED_ORDINARY_SEVENPAIR_RELATION_RECEIPT",
    }
    assert result["base_audit_sha256"] == sha(BASE / "audit_result.json")
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert result["formula_sha256"] == sha(HERE / "formula.xcnf")
    assert result["formula_sha256"] == protocol["base_formula_sha256"]
    assert (HERE / "formula.xcnf").stat().st_size == protocol["base_formula_bytes"]
    assert (result["curve_id"], result["workload_id"], result["public_target"]) == (
        protocol["curve_id"], protocol["workload_id"], protocol["public_target"])
    assert (result["public_target"], result["curve_id"]) == (
        base["public_target"], base["curve_id"])
    assert result["solver_flags"] == protocol["solver_flags"]
    assert result["worker_count"] == protocol["worker_count"] == 1
    assert result["solver_cpu_seconds_rusage"] >= 0
    assert result["solver_cpu_seconds_sampled"] >= 0
    assert result["peak_combined_rss_bytes_sampled"] > 0
    assert result["solver_wall_ns"] >= 0
    stdout = (HERE / "solver.stdout.txt").read_text(errors="replace")
    assert result["stdout_sha256"] == sha(HERE / "solver.stdout.txt")
    assert result["stderr_sha256"] == sha(HERE / "solver.stderr.txt")
    assert result["status_lines"] == [line for line in stdout.splitlines()
                                      if line.startswith("s ")]
    assert result["restart_rows"] == sum(line.startswith("c rst")
                                         for line in stdout.splitlines())
    if result["status"] == "BOUNDED_UNKNOWN":
        assert result["stop_reason"] is not None
        assert "s SATISFIABLE" not in result["status_lines"]
        assert "s UNSATISFIABLE" not in result["status_lines"]
        assert result["model_audit"] is None
        status = "PASS_BOUNDED_GAUSS_REPLAY_RECEIPT"
    elif result["status"] == "SAT_PENDING_GROUP_REPLAY":
        assert "s SATISFIABLE" in result["status_lines"]
        assert result["model_audit"]["status"] == "PASS_COMPLETE_XCNF_ASSIGNMENT"
        assert result["model_audit"] == json.loads((HERE / "model_audit.json").read_text())
        status = "PASS_GAUSS_XCNF_MODEL_PENDING_GROUP_REPLAY"
    elif result["status"] == "UNSAT":
        assert "s UNSATISFIABLE" in result["status_lines"]
        assert result["model_audit"] is None
        status = "PASS_GAUSS_UNSAT_FORMULA_RECEIPT"
    else:
        raise AssertionError("unexpected solver status")
    matrix_summary = [line for line in stdout.splitlines()
                      if "[matrix] Using " in line or
                      "[matrix] unused matrices:" in line]
    receipt = {
        "status": status,
        "candidate_id": None,
        "scope": protocol["scope"],
        "curve_id": protocol["curve_id"],
        "workload_id": protocol["workload_id"],
        "public_target": protocol["public_target"],
        "solver_status": result["status"],
        "stop_reason": result["stop_reason"],
        "solver_cpu_seconds_rusage": result["solver_cpu_seconds_rusage"],
        "solver_wall_ns": result["solver_wall_ns"],
        "restart_rows": result["restart_rows"],
        "matrix_summary": matrix_summary,
        "sha256": {"protocol": sha(HERE / "protocol.json"),
                   "runner": sha(HERE / "replay.py"),
                   "result": sha(HERE / "run_result.json"),
                   "formula": sha(HERE / "formula.xcnf"),
                   "stdout": sha(HERE / "solver.stdout.txt"),
                   "stderr": sha(HERE / "solver.stderr.txt"),
                   "audit": sha(Path(__file__))},
    }
    with (HERE / "audit_result.json").open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(status, flush=True)


if __name__ == "__main__":
    main()
