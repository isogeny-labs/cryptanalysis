"""Audit the bounded Gaussian-admission control and preserved solver log."""

import gzip
import hashlib
import json
from pathlib import Path

import run

HERE = Path(__file__).resolve().parent


def sha_raw_gzip(path):
    digest = hashlib.sha256()
    size = 0
    with gzip.open(path, "rb") as stream:
        while chunk := stream.read(1024 * 1024):
            size += len(chunk)
            digest.update(chunk)
    return digest.hexdigest(), size


def main():
    frozen = run.protocol()
    result = json.loads((HERE / "control_result.json").read_text())
    assert result["protocol_sha256"] == run.sha(HERE / "protocol.json")
    digest, size = sha_raw_gzip(run.SOURCE / "control.xcnf.gz")
    assert (digest, size) == (frozen["control_formula_sha256"],
                              frozen["control_formula_bytes"])
    formula = HERE / "control.xcnf"
    if formula.exists():
        assert run.sha(formula) == digest and formula.stat().st_size == size
    stdout_path, stderr_path = HERE / "solver.stdout.txt", HERE / "solver.stderr.txt"
    assert run.sha(stdout_path) == result["stdout_sha256"]
    assert run.sha(stderr_path) == result["stderr_sha256"]
    stdout = stdout_path.read_text(errors="replace")
    stderr = stderr_path.read_text(errors="replace")
    assert stderr == ""
    assert result["solver_status_lines"] == [line for line in stdout.splitlines()
                                              if line.startswith("s ")]
    assert result["actual_restart_rows"] == sum(
        line.startswith("c rst") for line in stdout.splitlines())
    assert result["actual_restart_rows"] > 0
    assert result["gauss_matrix_lines"] == [line for line in stdout.splitlines()
                                            if line.startswith("c [matrix]") or
                                            line.startswith("c [find&init matx]")]
    assert "c [matrix] Using 5 matrices recovered from 268800 xors T: 0.06 T-out: N" in stdout
    enabled = [line for line in stdout.splitlines()
               if line.startswith("c [matrix] Good")]
    assert len(enabled) >= 5 and len(enabled) % 5 == 0
    assert sum("3315 x 9132" in line for line in enabled) >= 4
    auto_disabled = [line for line in stdout.splitlines()
                     if "Disabling GJ-elim" in line]
    assert auto_disabled
    assert result["status"] == "BOUNDED_UNKNOWN"
    assert result["stop_reason"] == "WALL_CAP"
    assert result["solver_exit_code"] == -9
    assert not result["solver_status_lines"]
    assert frozen["wall_cap_ns"] <= result["solver_stage_wall_ns"] < \
        frozen["wall_cap_ns"] + 10**9
    assert result["peak_parent_plus_solver_rss_bytes_sampled"] <= \
        frozen["rss_cap_bytes"]
    receipt = {
        "status": "PASS_GAUSS_CONTROL_TERMINAL_AUDIT",
        "query_status": result["status"],
        "solver_stage_wall_ns": result["solver_stage_wall_ns"],
        "actual_restart_rows": result["actual_restart_rows"],
        "matrix_admitted_per_initialization": 5,
        "matrix_initializations": len(enabled) // 5,
        "matrix_auto_disable_rows": len(auto_disabled),
        "formula_replay_sha256": digest,
        "stderr_empty": True,
        "sha256": {"auditor": run.sha(Path(__file__)),
                   "protocol": run.sha(HERE / "protocol.json"),
                   "result": run.sha(HERE / "control_result.json"),
                   "stdout": run.sha(stdout_path),
                   "stderr": run.sha(stderr_path)}}
    with (HERE / "audit_result.json").open("w") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(receipt["status"], receipt["matrix_admitted_per_initialization"], flush=True)


if __name__ == "__main__":
    main()
