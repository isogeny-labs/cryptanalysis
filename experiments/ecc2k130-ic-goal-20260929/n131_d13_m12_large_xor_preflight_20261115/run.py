"""Bounded large-XOR-matrix preflight on the first archived d13/m12 query."""

import argparse
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil

BASE = Path(__file__).resolve().parent
FORMULA = BASE / "query.xcnf"
SOURCE_ATTEMPT = BASE / "source_attempt.json"
RUNTIME = BASE / "sage_runtime_info.json"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
PROTOCOL = BASE / "protocol.json"
RUN = BASE / "large_matrix_R1"
FLAGS = ["--threads=1", "--verb=1", "--verbstat=2", "--printsol=1",
         "--restartprint=10000000", "--random=2026100618",
         "--maxtime=118.000", "--maxmatrixrows=40000",
         "--maxmatrixcols=85000", "--maxnummatrices=10",
         "--maxconfl=1000000000000"]


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def write_new(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def source_hashes():
    return {"formula": sha(FORMULA), "source_attempt": sha(SOURCE_ATTEMPT),
            "sage_runtime": sha(RUNTIME), "solver": sha(SOLVER),
            "runner": sha(Path(__file__))}


def validate_source():
    attempt = json.loads(SOURCE_ATTEMPT.read_text())
    runtime = json.loads(RUNTIME.read_text())
    assert runtime["status"] == "verified"
    assert attempt["relation_index"] == 1 and attempt["status"] == "timeout"
    assert attempt["verified_relation_count"] == 0
    details = attempt["query_details"]
    assert details["target_formula_sha256"] == sha(FORMULA)
    assert details["formula_counts"] == {"vars": 232244, "clauses": 228629,
                                          "xors": 171278}
    assert details["attempts"][0]["solver_stop_reason"] == "parent_timeout"
    assert details["attempts"][0]["solver_status"] == "indeterminate"
    assert details["attempts"][0]["solver_peak_rss_bytes"] < 4 * 1024**3


def freeze():
    validate_source()
    write_new(PROTOCOL, {
        "kind": "n131_d13_m12_unprojected_large_xor_preflight_v1",
        "status": "FROZEN_PROPOSAL", "candidate_id": None,
        "curve_id": "EC1N131Ckb1heb5f1998f20b",
        "workload_id": "3c1992b7c92f", "target_count": 1, "batch": False,
        "input_law": "first distinct known-scalar preparation point in the frozen d13/m12 single-target run; scalar withheld from solver",
        "parent_wall_cap_seconds": 120.0,
        "combined_parent_solver_rss_cap_bytes": 4 * 1024**3,
        "solver_flags": FLAGS,
        "change_from_archived_arm": ["maxtime=118.000", "maxmatrixrows=40000",
                                     "maxmatrixcols=85000"],
        "source_sha256": source_hashes(),
    })


def run(preflight_only):
    protocol = json.loads(PROTOCOL.read_text())
    assert protocol["status"] == "FROZEN_PROPOSAL"
    assert protocol["source_sha256"] == source_hashes()
    assert protocol["solver_flags"] == FLAGS
    assert protocol["parent_wall_cap_seconds"] == 120.0
    assert protocol["combined_parent_solver_rss_cap_bytes"] == 4 * 1024**3
    validate_source()
    assert not RUN.exists()
    if preflight_only:
        print("READY_UNPROJECTED_LARGE_XOR_PREFLIGHT", sha(FORMULA))
        return
    RUN.mkdir()
    command = [str(SOLVER), *FLAGS, str(FORMULA)]
    write_new(RUN / "started.json", {
        "status": "RUNNING", "started_utc": now(),
        "protocol_sha256": sha(PROTOCOL),
        "solver_command": command,
        "target_count": 1, "batch": False,
    })
    stdout_path = RUN / "cryptominisat.stdout.txt"
    stderr_path = RUN / "cryptominisat.stderr.txt"
    peak_rss = 0
    stop_reason = None
    started = time.monotonic()
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        child = subprocess.Popen(command, stdout=stdout, stderr=stderr,
                                 start_new_session=True)
        write_new(RUN / "solver_process.json", {
            "pid": child.pid, "create_time_epoch": psutil.Process(child.pid).create_time(),
            "command": command})
        while child.poll() is None:
            try:
                child_rss = psutil.Process(child.pid).memory_info().rss
            except psutil.NoSuchProcess:
                child_rss = 0
            peak_rss = max(peak_rss,
                           child_rss + psutil.Process(os.getpid()).memory_info().rss)
            if peak_rss > protocol["combined_parent_solver_rss_cap_bytes"]:
                stop_reason = "RSS_CAP"
                child.terminate()
                break
            if time.monotonic() - started >= protocol["parent_wall_cap_seconds"]:
                stop_reason = "WALL_CAP"
                child.terminate()
                break
            time.sleep(0.1)
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
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
    result = {
        "kind": "n131_d13_m12_unprojected_large_xor_preflight_result_v1",
        "status": status, "finished_utc": now(),
        "candidate_id": None, "run_id": None,
        "curve_id": protocol["curve_id"], "workload_id": protocol["workload_id"],
        "target_count": 1, "batch": False,
        "solver_wall_seconds": time.monotonic() - started,
        "solver_exit_code": child.returncode, "stop_reason": stop_reason,
        "combined_peak_rss_bytes": peak_rss,
        "solver_status_lines": statuses, "solver_model_line_count": model_lines,
        "verified_relation": None,
        "source_sha256": {"protocol": sha(PROTOCOL), "formula": sha(FORMULA),
                          "source_attempt": sha(SOURCE_ATTEMPT),
                          "sage_runtime": sha(RUNTIME), "solver": sha(SOLVER),
                          "runner": sha(Path(__file__)),
                          "stdout": sha(stdout_path), "stderr": sha(stderr_path)},
    }
    write_new(RUN / "result.json", result)
    print(json.dumps({"status": status,
                      "wall_seconds": result["solver_wall_seconds"],
                      "combined_peak_rss_bytes": peak_rss,
                      "model_lines": model_lines}, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "preflight", "run"))
    args = parser.parse_args()
    if args.mode == "freeze":
        freeze()
    else:
        run(args.mode == "preflight")
