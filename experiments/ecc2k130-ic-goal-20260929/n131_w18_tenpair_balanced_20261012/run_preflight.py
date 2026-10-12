"""Frozen, resource-capped constructed-target SAT preflight for ten pairs."""

import hashlib
import json
import subprocess
import time
from pathlib import Path

import psutil
import tenpair

HERE = Path(__file__).resolve().parent
FLAGS = ["--threads=1", "--maxtime=110", "--zero-exit-status",
         "--verb=1", "--printsol=1"]


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load(name):
    return json.loads((HERE / name).read_text())


def prepare():
    frozen, control = load("protocol.json"), load("control_result.json")
    assert control["status"] == "PASS_TENPAIR_CONSTRUCTED_ASSIGNMENT"
    assert control["protocol_sha256"] == sha(HERE / "protocol.json")
    assert control["formula"]["xcnf_sha256"] == sha(HERE / "control.xcnf")
    assert sha(HERE / "tenpair.py") == frozen["source_sha256"]["tenpair"]
    tenpair.save("solver_protocol.json", {
        "status": "FROZEN_BEFORE_CONSTRUCTED_SOLVER_PREFLIGHT",
        "formula_sha256": control["formula"]["xcnf_sha256"],
        "protocol_sha256": sha(HERE / "protocol.json"),
        "control_result_sha256": sha(HERE / "control_result.json"),
        "runner_sha256": sha(Path(__file__)),
        "solver_path": str(tenpair.base.SOLVER),
        "solver_sha256": sha(tenpair.base.SOLVER),
        "solver_flags": FLAGS,
        "wall_cap_seconds": frozen["constructed_solver_cap_seconds"],
        "combined_rss_cap_bytes": frozen["combined_rss_cap_bytes"],
    })


def run():
    frozen, control, plan = (load(name) for name in (
        "protocol.json", "control_result.json", "solver_protocol.json"))
    assert plan["status"] == "FROZEN_BEFORE_CONSTRUCTED_SOLVER_PREFLIGHT"
    for name, actual in (("runner_sha256", sha(Path(__file__))),
                         ("solver_sha256", sha(tenpair.base.SOLVER)),
                         ("formula_sha256", sha(HERE / "control.xcnf")),
                         ("protocol_sha256", sha(HERE / "protocol.json")),
                         ("control_result_sha256", sha(HERE / "control_result.json"))):
        assert plan[name] == actual, name
    assert plan["wall_cap_seconds"] == frozen["constructed_solver_cap_seconds"]
    assert plan["combined_rss_cap_bytes"] == frozen["combined_rss_cap_bytes"]
    assert plan["formula_sha256"] == control["formula"]["xcnf_sha256"]
    stdout_path, stderr_path = HERE / "solver.stdout.txt", HERE / "solver.stderr.txt"
    parent = psutil.Process()
    peak, stop_reason = 0, None
    start = time.monotonic_ns()
    with stdout_path.open("x") as stdout, stderr_path.open("x") as stderr:
        process = subprocess.Popen([plan["solver_path"], *plan["solver_flags"],
                                    str(HERE / "control.xcnf")],
                                   stdout=stdout, stderr=stderr)
        child = psutil.Process(process.pid)
        while process.poll() is None:
            try:
                combined = parent.memory_info().rss + child.memory_info().rss
            except psutil.NoSuchProcess:
                combined = parent.memory_info().rss
            peak = max(peak, combined)
            if combined > plan["combined_rss_cap_bytes"]:
                stop_reason = "RSS_CAP"
            elif time.monotonic_ns() - start >= plan["wall_cap_seconds"] * 10**9:
                stop_reason = "WALL_CAP"
            if stop_reason:
                process.kill()
                break
            time.sleep(0.05)
        exit_code = process.wait()
    end = time.monotonic_ns()
    output = stdout_path.read_text(errors="replace")
    status_lines = [line for line in output.splitlines() if line.startswith("s ")]
    if stop_reason == "RSS_CAP":
        status = "CENSORED_RSS"
    elif stop_reason == "WALL_CAP" or (not status_lines and end-start >= 110 * 10**9):
        status = "CENSORED_TIME"
    elif "s SATISFIABLE" in status_lines:
        status = "SAT_PENDING_INDEPENDENT_REPLAY"
    elif "s UNSATISFIABLE" in status_lines:
        status = "UNSAT_CONTRADICTS_CONSTRUCTED_ASSIGNMENT"
    else:
        status = "SOLVER_ERROR"
    tenpair.save("solver_result.json", {
        "status": status,
        "constructed_public_target": frozen["constructed_public_target"],
        "elapsed_seconds_exploratory": (end-start)/10**9,
        "peak_combined_rss_bytes_sampled": peak,
        "stop_reason": stop_reason,
        "exit_code": exit_code,
        "status_lines": status_lines,
        "restart_rows": sum(line.startswith("c [") for line in output.splitlines()),
        "stdout_sha256": sha(stdout_path),
        "stderr_sha256": sha(stderr_path),
        "solver_protocol_sha256": sha(HERE / "solver_protocol.json"),
    })
    print(status, (end-start)/10**9, peak, flush=True)


if __name__ == "__main__":
    import sys
    {"prepare": prepare, "run": run}[sys.argv[1]]()
