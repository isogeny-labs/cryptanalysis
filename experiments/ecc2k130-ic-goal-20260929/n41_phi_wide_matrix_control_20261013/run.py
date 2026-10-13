#!/usr/bin/env python3
"""Bounded native-XOR matrix-policy control on a frozen N41 public query."""

import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "n41_phi_second_link_control_20261009"
FORMULA = SOURCE / "source_pinned.xcnf"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
CAP_SECONDS = 120
CAP_RSS_BYTES = 2 * (1 << 30)
FLAGS = ["--threads=1", "--verb=1", "--printsol=1", "--xor=0",
         "--random=2026100913", "--maxmatrixrows=6000",
         "--maxmatrixcols=6000", "--maxnummatrices=10", "--maxtime=118"]


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def preflight():
    baseline_protocol = json.loads((SOURCE / "protocol.json").read_text())
    baseline = json.loads((SOURCE / "audit.json").read_text())
    planted = json.loads((SOURCE / "planted_control.json").read_text())
    assert baseline_protocol["status"] == "FROZEN"
    assert baseline_protocol["target_count"] == 1
    assert sha(FORMULA) == baseline_protocol["source_sha256"]["source_pinned"]
    assert sha(SOLVER) == baseline_protocol["source_sha256"]["solver"]
    assert planted["status"] == "PASS_FULL_PLANTED_XCNF_AND_LOOKUP_ROOT"
    assert baseline["status"].startswith("PASS")
    protocol = {
        "kind": "n41_phi_wide_xor_matrix_public_query_control",
        "status": "FROZEN", "target_count": 1, "batch": False,
        "candidate_id": None, "run_id": None,
        "curve_id": baseline_protocol["curve_id"],
        "proposal_id": baseline_protocol["proposal_id"],
        "target_coordinates": baseline_protocol["target_coordinates"],
        "cap_seconds": CAP_SECONDS, "combined_rss_cap_bytes": CAP_RSS_BYTES,
        "flags": FLAGS, "solver": str(SOLVER), "formula": str(FORMULA),
        "control_change": "allow the previously excluded 5335x5768 XOR matrix",
        "baseline_status": "CENSORED_TIME",
        "input_sha256": {
            "formula": sha(FORMULA), "solver": sha(SOLVER),
            "baseline_protocol": sha(SOURCE / "protocol.json"),
            "baseline_audit": sha(SOURCE / "audit.json"),
            "planted_control": sha(SOURCE / "planted_control.json"),
            "runner": sha(Path(__file__)),
        },
    }
    protocol_path = HERE / "protocol.json"
    if protocol_path.exists():
        assert json.loads(protocol_path.read_text()) == protocol
    else:
        write_json(protocol_path, protocol)
    return protocol


def run(protocol):
    for name in ("result.json", "solver.stdout.txt", "solver.stderr.txt", "process.json"):
        if (HERE / name).exists():
            raise FileExistsError(HERE / name)
    command = [str(SOLVER), *FLAGS, str(FORMULA)]
    stdout_path = HERE / "solver.stdout.txt"
    stderr_path = HERE / "solver.stderr.txt"
    began = time.monotonic()
    peak_rss = 0
    peak_cpu = 0.0
    stop_reason = None
    parent = psutil.Process(os.getpid())
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr,
                                   start_new_session=True)
        child = psutil.Process(process.pid)
        write_json(HERE / "process.json", {
            "pid": process.pid, "create_time_epoch": child.create_time(),
            "command": command, "started_utc": datetime.now(timezone.utc).isoformat(),
        })
        while process.poll() is None:
            try:
                cpu = child.cpu_times()
                peak_cpu = max(peak_cpu, cpu.user + cpu.system)
                peak_rss = max(peak_rss,
                               child.memory_info().rss + parent.memory_info().rss)
            except psutil.NoSuchProcess:
                pass
            if peak_rss > CAP_RSS_BYTES:
                stop_reason = "RSS_CAP"
                process.terminate()
                break
            if time.monotonic() - began >= CAP_SECONDS:
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
    models = 0
    matrices = []
    with stdout_path.open("rb") as stream:
        for line in stream:
            if line.startswith(b"s "):
                statuses.append(line.decode("ascii", "replace").strip())
            elif line.startswith(b"v "):
                models += 1
            elif b"[matrix] Good" in line or b"[matrix] UNused" in line:
                matrices.append(line.decode("ascii", "replace").strip())
    if "s SATISFIABLE" in statuses:
        status = "SAT_MODEL_PENDING_INDEPENDENT_REPLAY" if models else "MODEL_MISSING"
    elif "s UNSATISFIABLE" in statuses:
        status = "UNSAT_FORMULA"
    elif stop_reason == "RSS_CAP":
        status = "OOM"
    elif stop_reason == "WALL_CAP" or "s INDETERMINATE" in statuses:
        status = "CENSORED_TIME"
    else:
        status = "PRODUCER_OR_SOLVER_FAILURE"
    result = {
        "status": status, "kind": protocol["kind"],
        "target_count": 1, "batch": False,
        "candidate_id": None, "run_id": None,
        "complete_online_wall_seconds": None,
        "attempts": 1, "verified_relations": 0,
        "solver_stage_wall_seconds": time.monotonic() - began,
        "sampled_peak_solver_cpu_seconds": peak_cpu,
        "sampled_peak_combined_rss_bytes": peak_rss,
        "exit_code": process.returncode, "stop_reason": stop_reason,
        "status_lines": statuses, "model_lines": models,
        "matrix_lines": matrices,
        "source_sha256": {
            "protocol": sha(HERE / "protocol.json"),
            "formula": sha(FORMULA), "solver": sha(SOLVER),
            "stdout": sha(stdout_path), "stderr": sha(stderr_path),
            "process": sha(HERE / "process.json"),
        },
    }
    write_json(HERE / "result.json", result)
    print(json.dumps({k: result[k] for k in ("status", "stop_reason",
                                                 "solver_stage_wall_seconds",
                                                 "sampled_peak_combined_rss_bytes",
                                                 "model_lines")}), flush=True)


if __name__ == "__main__":
    run(preflight())
