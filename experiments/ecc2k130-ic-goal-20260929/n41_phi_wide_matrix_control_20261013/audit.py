#!/usr/bin/env python3
"""Independent terminal audit of the frozen N41 matrix-policy control."""

import hashlib
import json
from pathlib import Path

import psutil


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "n41_phi_second_link_control_20261009"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    process = json.loads((HERE / "process.json").read_text())
    baseline = json.loads((SOURCE / "result.json").read_text())["attempts"][0]
    baseline_text = (SOURCE / "baseline.stdout.txt").read_text()
    raw_text = (HERE / "solver.stdout.txt").read_text()
    assert protocol["status"] == "FROZEN"
    assert protocol["target_count"] == 1 and protocol["batch"] is False
    assert protocol["input_sha256"]["formula"] == sha(Path(protocol["formula"]))
    assert protocol["input_sha256"]["solver"] == sha(Path(protocol["solver"]))
    assert protocol["input_sha256"]["runner"] == sha(HERE / "run.py")
    for name in ("baseline_protocol", "baseline_audit", "planted_control"):
        source_name = {"baseline_protocol": "protocol.json",
                       "baseline_audit": "audit.json",
                       "planted_control": "planted_control.json"}[name]
        assert protocol["input_sha256"][name] == sha(SOURCE / source_name)
    for name, path in (("protocol", HERE / "protocol.json"),
                       ("formula", Path(protocol["formula"])),
                       ("solver", Path(protocol["solver"])),
                       ("stdout", HERE / "solver.stdout.txt"),
                       ("stderr", HERE / "solver.stderr.txt"),
                       ("process", HERE / "process.json")):
        assert result["source_sha256"][name] == sha(path)
    assert process["command"] == [protocol["solver"], *protocol["flags"],
                                  protocol["formula"]]
    try:
        live = psutil.Process(process["pid"])
        same_process_alive = abs(live.create_time() - process["create_time_epoch"]) < .01
    except psutil.NoSuchProcess:
        same_process_alive = False
    assert not same_process_alive
    assert result["status"] == "CENSORED_TIME"
    assert result["stop_reason"] == "WALL_CAP" and result["exit_code"] == -15
    assert 120 <= result["solver_stage_wall_seconds"] < 130
    assert result["sampled_peak_combined_rss_bytes"] < protocol["combined_rss_cap_bytes"]
    assert result["status_lines"] == [] and result["model_lines"] == 0
    assert not any(line.startswith(("s ", "v ")) for line in raw_text.splitlines())
    assert "[matrix] Too many rows in matrix: 5335" in baseline_text
    assert "[matrix] UNused matrix      5335 x 5768" in baseline_text
    assert "[matrix] Good   matrix  0" in raw_text
    assert "   5335 x 5768" in raw_text
    assert baseline["status"] == "CENSORED_TIME"
    assert baseline["source_sha256"]["formula"] == result["source_sha256"]["formula"]
    audit = {
        "status": "PASS_CENSORED_N41_MATRIX_POLICY_CONTROL",
        "target_count": 1, "formula_sha256": result["source_sha256"]["formula"],
        "solver_sha256": result["source_sha256"]["solver"],
        "baseline_matrix_excluded": "5335x5768",
        "control_matrix_admitted": "5335x5768",
        "baseline_status": baseline["status"], "control_status": result["status"],
        "baseline_solver_wall_seconds": baseline["wall_seconds"],
        "control_solver_wall_seconds": result["solver_stage_wall_seconds"],
        "baseline_sampled_cpu_seconds": baseline["sampled_peak_cpu_seconds"],
        "control_sampled_cpu_seconds": result["sampled_peak_solver_cpu_seconds"],
        "control_peak_combined_rss_bytes": result["sampled_peak_combined_rss_bytes"],
        "raw_solver_status_lines": result["status_lines"],
        "raw_model_lines": result["model_lines"],
        "solver_process_drained": True,
        "source_sha256": {
            "protocol": sha(HERE / "protocol.json"),
            "result": sha(HERE / "result.json"),
            "process": sha(HERE / "process.json"),
            "stdout": sha(HERE / "solver.stdout.txt"),
            "stderr": sha(HERE / "solver.stderr.txt"),
            "baseline_result": sha(SOURCE / "result.json"),
        },
    }
    (HERE / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(audit["status"])


if __name__ == "__main__":
    main()
