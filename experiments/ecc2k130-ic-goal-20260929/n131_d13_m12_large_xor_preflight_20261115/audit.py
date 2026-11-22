"""Independently audit the large-matrix preflight and its raw solver trace."""

import hashlib
import json
from pathlib import Path

import psutil

BASE = Path(__file__).resolve().parent
RUN = BASE / "large_matrix_R1"
PROTOCOL = BASE / "protocol.json"
FORMULA = BASE / "query.xcnf"
SOURCE_ATTEMPT = BASE / "source_attempt.json"
RUNTIME = BASE / "sage_runtime_info.json"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    protocol = json.loads(PROTOCOL.read_text())
    attempt = json.loads(SOURCE_ATTEMPT.read_text())
    result_path = RUN / "result.json"
    result = json.loads(result_path.read_text())
    started = json.loads((RUN / "started.json").read_text())
    process = json.loads((RUN / "solver_process.json").read_text())
    stdout = RUN / "cryptominisat.stdout.txt"
    stderr = RUN / "cryptominisat.stderr.txt"
    sources = {"formula": FORMULA, "source_attempt": SOURCE_ATTEMPT,
               "sage_runtime": RUNTIME, "solver": SOLVER,
               "runner": BASE / "run.py"}
    assert protocol["source_sha256"] == {key: sha(path) for key, path in sources.items()}
    assert attempt["query_details"]["target_formula_sha256"] == sha(FORMULA)
    assert json.loads(RUNTIME.read_text())["status"] == "verified"
    assert started["protocol_sha256"] == sha(PROTOCOL)
    assert started["solver_command"] == process["command"]
    assert process["command"] == [str(SOLVER), *protocol["solver_flags"], str(FORMULA)]
    assert result["source_sha256"] == {
        "protocol": sha(PROTOCOL), "formula": sha(FORMULA),
        "source_attempt": sha(SOURCE_ATTEMPT), "sage_runtime": sha(RUNTIME),
        "solver": sha(SOLVER), "runner": sha(BASE / "run.py"),
        "stdout": sha(stdout), "stderr": sha(stderr)}
    try:
        live = psutil.Process(process["pid"])
        if abs(live.create_time() - process["create_time_epoch"]) < 0.01 and live.is_running():
            raise RuntimeError("the recorded solver process is still live")
    except psutil.NoSuchProcess:
        pass
    lines = stdout.read_text(errors="replace").splitlines()
    statuses = [line for line in lines if line.startswith("s ")]
    model_lines = [line for line in lines if line.startswith("v ")]
    assert statuses == result["solver_status_lines"]
    assert len(model_lines) == result["solver_model_line_count"]
    assert result["combined_peak_rss_bytes"] <= protocol["combined_parent_solver_rss_cap_bytes"] or result["status"] == "OOM"
    assert result["solver_wall_seconds"] <= protocol["parent_wall_cap_seconds"] + 11
    large_good = any("Good   matrix  0" in line for line in lines)
    large_dimensions = any("36627 x38097" in line for line in lines)
    large_unused = any("UNused matrix" in line and "36627 x38097" in line for line in lines)
    assert large_good and large_dimensions and not large_unused
    if statuses == ["s SATISFIABLE"] and model_lines:
        classification = "SAT_MODEL_REQUIRES_INDEPENDENT_AUDIT"
    elif result["status"] == "OOM" and result["stop_reason"] == "RSS_CAP":
        classification = "OOM"
    elif result["status"] == "CENSORED_TIME" and result["stop_reason"] == "WALL_CAP":
        classification = "CENSORED_TIME"
    elif result["status"] == "INDETERMINATE" and not model_lines and not any(
            status in ("s SATISFIABLE", "s UNSATISFIABLE") for status in statuses):
        classification = "CENSORED_SOLVER_TIME"
    elif statuses == ["s UNSATISFIABLE"] and not model_lines:
        classification = "UNSAT"
    else:
        classification = "INDETERMINATE"
    restart_lines = [line for line in lines if line.startswith("c rst")]
    output = {
        "kind": "n131_d13_m12_unprojected_large_xor_independent_terminal_audit_v1",
        "status": classification,
        "large_matrix_admitted": True,
        "large_matrix_rows": 36627, "large_matrix_columns": 38097,
        "solver_status_lines": statuses, "solver_model_line_count": len(model_lines),
        "last_restart_line": restart_lines[-1] if restart_lines else None,
        "solver_wall_seconds": result["solver_wall_seconds"],
        "combined_peak_rss_bytes": result["combined_peak_rss_bytes"],
        "process_identity_drained": True,
        "source_sha256": {"protocol": sha(PROTOCOL), "result": sha(result_path),
                          "formula": sha(FORMULA), "source_attempt": sha(SOURCE_ATTEMPT),
                          "runtime": sha(RUNTIME), "stdout": sha(stdout),
                          "stderr": sha(stderr), "solver": sha(SOLVER),
                          "auditor": sha(Path(__file__))},
    }
    with (RUN / "independent_terminal_audit.json").open("x") as stream:
        json.dump(output, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(classification, output["solver_wall_seconds"], output["combined_peak_rss_bytes"])


if __name__ == "__main__":
    main()
