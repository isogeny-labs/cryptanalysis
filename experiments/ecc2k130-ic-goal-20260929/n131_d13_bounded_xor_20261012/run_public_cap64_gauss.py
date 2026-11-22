#!/usr/bin/env python3
"""Memory-bounded preflight admitting the cap-64 formula's large XOR matrix."""

import argparse
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
FORMULA = HERE / "public_cap64/projected.xcnf"
PROTOCOL = HERE / "public_cap64_gauss_protocol.json"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
RUN = HERE / "public_cap64_gauss_stage_R1"
RUNTIME = HERE / "sage_runtime_info.json"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    protocol = json.loads(PROTOCOL.read_text())
    projection = HERE / "public_cap64/result.json"
    control = HERE / "planted_cap64/independent_audit.json"
    structure = HERE / "public_cap64/independent_audit.json"
    assert protocol["status"] == "FROZEN_PROPOSAL"
    assert protocol["target_count"] == 1 and protocol["batch"] is False
    assert protocol["stage_solver_limit_seconds"] == 120
    assert protocol["resource_limit_bytes"] == 4 * 1024**3
    assert json.loads(projection.read_text())["status"] == "PASS"
    assert json.loads(control.read_text())["status"] == "PASS"
    assert json.loads(structure.read_text())["status"] == "PASS"
    assert json.loads(control.read_text())["lifted_control"]["status"] == "PASS"
    assert json.loads(RUNTIME.read_text())["status"] == "verified"
    assert sha(RUNTIME) == protocol["source_sha256"]["runtime"]
    for key, path in (("projected_formula", FORMULA),
                      ("projection_result", projection),
                      ("control_audit", control), ("structure_audit", structure),
                      ("solver", SOLVER),
                      ("runner", Path(__file__))):
        assert sha(path) == protocol["source_sha256"][key]
    assert not RUN.exists()
    command = [str(SOLVER), *protocol["run_policy"]["solver_flags"], str(FORMULA)]
    assert command[1:-1] == protocol["run_policy"]["solver_flags"]
    if args.preflight_only:
        print(json.dumps({"status": "READY", "solver_launched": False,
                          "proposal_id": protocol["proposal_id"],
                          "formula_sha256": sha(FORMULA)}))
        return
    RUN.mkdir()
    (RUN / "sage_runtime_info.json").write_bytes(RUNTIME.read_bytes())
    started = {"status": "RUNNING", "started_utc": now(),
               "proposal_id": protocol["proposal_id"],
               "candidate_id": None, "run_id": None,
               "curve_id": protocol["curve_id"],
               "workload_id": protocol["workload_id"],
               "target_count": 1, "batch": False,
               "protocol_sha256": sha(PROTOCOL),
               "runtime_info_sha256": sha(RUNTIME),
               "solver_command": command}
    save(RUN / "started.json", started)
    stdout_path = RUN / "cryptominisat.stdout.txt"
    stderr_path = RUN / "cryptominisat.stderr.txt"
    began = time.monotonic()
    peak_rss = 0
    stop_reason = None
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr,
                                   start_new_session=True)
        save(RUN / "solver_process.json",
             {"pid": process.pid,
              "create_time_epoch": psutil.Process(process.pid).create_time(),
              "command": command})
        while process.poll() is None:
            try:
                child_rss = psutil.Process(process.pid).memory_info().rss
            except psutil.NoSuchProcess:
                child_rss = 0
            peak_rss = max(peak_rss, child_rss +
                           psutil.Process(os.getpid()).memory_info().rss)
            if peak_rss > protocol["resource_limit_bytes"]:
                stop_reason = "RSS_CAP"
                process.terminate()
                break
            if time.monotonic() - began >= protocol["stage_solver_limit_seconds"]:
                stop_reason = "WALL_CAP"
                process.terminate()
                break
            time.sleep(0.1)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            stop_reason = (stop_reason or "DRAIN_TIMEOUT") + "_KILLED"
    statuses = []
    model_lines = 0
    for line in stdout_path.open("rb"):
        if line.startswith(b"s "):
            statuses.append(line.decode("ascii", errors="replace").strip())
        elif line.startswith(b"v "):
            model_lines += 1
    if statuses == ["s SATISFIABLE"] and model_lines:
        status = "SAT_MODEL_REQUIRES_INDEPENDENT_AUDIT"
    elif stop_reason == "RSS_CAP":
        status = "OOM"
    elif stop_reason == "WALL_CAP":
        status = "CENSORED_TIME"
    elif statuses == ["s UNSATISFIABLE"]:
        status = "UNSAT"
    else:
        status = "INDETERMINATE"
    result = {"kind": "n131_d13_m12_projected_public_q_sat_stage_screen",
              "status": status, "finished_utc": now(),
              "proposal_id": protocol["proposal_id"],
              "candidate_id": None, "run_id": None,
              "curve_id": protocol["curve_id"],
              "workload_id": protocol["workload_id"],
              "target_count": 1, "batch": False,
              "solver_wall_seconds": time.monotonic() - began,
              "solver_exit_code": process.returncode,
              "stop_reason": stop_reason,
              "combined_peak_rss_bytes": peak_rss,
              "solver_status_lines": statuses,
              "solver_model_line_count": model_lines,
              "verified_relation": None,
              "source_sha256": {"protocol": sha(PROTOCOL),
                                "formula": sha(FORMULA),
                                "runtime": sha(RUNTIME),
                                "stdout": sha(stdout_path),
                                "stderr": sha(stderr_path),
                                "runner": sha(Path(__file__)),
                                "solver": sha(SOLVER)}}
    save(RUN / "result.json", result)
    print(json.dumps({"status": status, "wall_s": result["solver_wall_seconds"],
                      "peak_rss": peak_rss, "model_lines": model_lines}))


if __name__ == "__main__":
    main()
