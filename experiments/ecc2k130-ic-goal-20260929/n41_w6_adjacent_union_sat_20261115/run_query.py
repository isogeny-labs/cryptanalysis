"""Run one bounded unpinned ordinary N41 union-source SAT query."""

import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = json.loads((HERE / "query_protocol.json").read_text())
    assert p["status"] == "FROZEN_BEFORE_QUERY"
    assert p["runner_sha256"] == sha(__file__)
    assert p["formula_sha256"] == sha(HERE / "ordinary.xcnf")
    assert p["build_result_sha256"] == sha(HERE / "build_result.json")
    assert p["solver_sha256"] == sha(p["solver_path"])
    cmd = [p["solver_path"], *p["solver_flags"], str(HERE / "ordinary.xcnf")]
    start = time.monotonic_ns()
    parent = psutil.Process(os.getpid())
    peak, stop, degraded = 0, None, False
    with (HERE / "solver.stdout").open("x") as out, (HERE / "solver.stderr").open("x") as err:
        child = subprocess.Popen(cmd, stdout=out, stderr=err, start_new_session=True)
        process = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                peak = max(peak, parent.memory_info().rss + process.memory_info().rss)
            except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
                if child.poll() is None:
                    degraded = True
            if peak >= p["rss_cap_bytes"]:
                stop = "RSS_CAP"
            elif time.monotonic_ns()-start >= p["parent_wall_cap_s"]*10**9:
                stop = "PARENT_WALL_CAP"
            if stop:
                os.killpg(child.pid, signal.SIGTERM)
                break
            time.sleep(0.05)
        child.wait()
    stdout = (HERE / "solver.stdout").read_text(errors="replace")
    terminal = [line for line in stdout.splitlines() if line.startswith("s ")]
    status = ("SAT_PENDING_REPLAY" if "s SATISFIABLE" in terminal
              else "UNSAT_UNCERTIFIED" if "s UNSATISFIABLE" in terminal
              else "BOUNDED_UNKNOWN" if stop or any("INDETERMINATE" in x for x in terminal)
              else "PRODUCER_FAILURE")
    record = {"kind": "n41_w6_adjacent_union_s3_unpinned_ordinary_query",
              "status": status, "query_protocol_sha256": sha(HERE / "query_protocol.json"),
              "command": cmd, "exit_code": child.returncode,
              "wall_ns": time.monotonic_ns()-start,
              "sampled_peak_combined_rss_bytes": peak,
              "monitor_degraded": degraded, "stop_reason": stop,
              "terminal_lines": terminal,
              "stdout_sha256": sha(HERE / "solver.stdout"),
              "stderr_sha256": sha(HERE / "solver.stderr")}
    (HERE / "query_result.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: record[k] for k in ("status", "wall_ns",
                      "sampled_peak_combined_rss_bytes", "terminal_lines")}, sort_keys=True))


if __name__ == "__main__":
    main()
