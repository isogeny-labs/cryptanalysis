#!/usr/bin/env python3
"""Independently classify a saved projected public-Q SAT-stage execution."""

import hashlib
import json
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
FORMULA = HERE / "public_cap64/projected.xcnf"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    run = HERE / "public_cap64_gauss_stage_R1"
    protocol_path = HERE / "public_cap64_gauss_protocol.json"
    output = run / "independent_terminal_audit.json"
    if output.exists():
        raise FileExistsError(output)
    protocol = json.loads(protocol_path.read_text())
    result_path = run / "result.json"
    result = json.loads(result_path.read_text())
    started = json.loads((run / "started.json").read_text())
    process = json.loads((run / "solver_process.json").read_text())
    stdout = run / "cryptominisat.stdout.txt"
    stderr = run / "cryptominisat.stderr.txt"
    if (started["protocol_sha256"] != sha(protocol_path) or
            result["source_sha256"]["protocol"] != sha(protocol_path) or
            result["source_sha256"]["formula"] != sha(FORMULA) or
            result["source_sha256"]["solver"] != sha(SOLVER) or
            result["source_sha256"]["stdout"] != sha(stdout) or
            result["source_sha256"]["stderr"] != sha(stderr) or
            started["solver_command"] != process["command"] or
            process["command"][0] != str(SOLVER) or
            process["command"][-1] != str(FORMULA) or
            process["command"][1:-1] != protocol["run_policy"]["solver_flags"] or
            started["proposal_id"] != result["proposal_id"] or
            result["proposal_id"] != protocol["proposal_id"]):
        raise ValueError("saved run provenance disagrees with frozen inputs")
    try:
        live = psutil.Process(process["pid"])
        if abs(live.create_time() - process["create_time_epoch"]) < 0.01 and live.is_running():
            raise RuntimeError("solver process identity is still live")
    except psutil.NoSuchProcess:
        pass
    status_lines = []
    model_lines = 0
    for line in stdout.open("rb"):
        if line.startswith(b"s "):
            status_lines.append(line.decode("ascii", errors="replace").strip())
        elif line.startswith(b"v "):
            model_lines += 1
    if status_lines != result["solver_status_lines"] or model_lines != result["solver_model_line_count"]:
        raise ValueError("saved solver status/model count differs from raw output")
    if result["status"] == "CENSORED_TIME" and result["stop_reason"] == "WALL_CAP" and not model_lines:
        classification = "CENSORED_TIME"
    elif (result["status"] == "INDETERMINATE" and
          result["solver_wall_seconds"] >= 115 and not model_lines and
          not any(line in ("s SATISFIABLE", "s UNSATISFIABLE") for line in status_lines)):
        classification = "CENSORED_SOLVER_TIME"
    elif result["status"] == "OOM" and result["stop_reason"] == "RSS_CAP" and not model_lines:
        classification = "OOM"
    elif result["status"] == "SAT_MODEL_REQUIRES_INDEPENDENT_AUDIT" and status_lines == ["s SATISFIABLE"] and model_lines:
        classification = "SAT_MODEL_REQUIRES_INDEPENDENT_AUDIT"
    elif result["status"] == "UNSAT" and status_lines == ["s UNSATISFIABLE"] and not model_lines:
        classification = "UNSAT"
    else:
        classification = "INDETERMINATE"
    audit = {
        "kind": "n131_d13_m12_projected_public_q_independent_terminal_audit",
        "status": classification,
        "proposal_id": protocol["proposal_id"],
        "solver_exit_code": result["solver_exit_code"],
        "solver_wall_seconds": result["solver_wall_seconds"],
        "combined_peak_rss_bytes": result["combined_peak_rss_bytes"],
        "solver_status_lines": status_lines,
        "solver_model_line_count": model_lines,
        "process_identity_drained": True,
        "source_sha256": {"result": sha(result_path), "protocol": sha(protocol_path),
                          "formula": sha(FORMULA), "stdout": sha(stdout),
                          "stderr": sha(stderr), "solver": sha(SOLVER),
                          "audit_script": sha(Path(__file__))},
    }
    output.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": classification, "run_number": 1}))


if __name__ == "__main__":
    main()
