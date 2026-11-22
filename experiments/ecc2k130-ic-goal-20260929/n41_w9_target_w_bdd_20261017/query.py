"""One-worker bounded unpinned public N41 query with target-w BDD."""
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "query_protocol.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol["sources"].items():
    assert sha(path) == expected, path
assert not (HERE / "query_result.json").exists()
build = json.loads((HERE / "build_result.json").read_text())
base = json.loads(Path(protocol["base_build_result"]).read_text())
audit = json.loads((HERE / "audit_result.json").read_text())
assert build["formula_sha256"] == sha(HERE / "formula.xcnf")
assert audit["status"] == "PASS_ALL_CODE_QUARTIC_ROOTS_EQUAL_TARGET_TABLE"
assert build["candidate_id"] is None

command = [protocol["solver"], "--threads=1",
           f"--maxtime={protocol['solver_cap_seconds']}",
           "--zero-exit-status", "--verb=1", "--printsol=1",
           str(HERE / "formula.xcnf")]
start = time.monotonic()
parent = psutil.Process(os.getpid())
peak = 0
samples = 0
monitor_error = None
stop = None
with (HERE / "solver.stdout").open("xb") as out, (HERE / "solver.stderr").open("xb") as err:
    child = subprocess.Popen(command, stdout=out, stderr=err,
                             start_new_session=True)
    observed = psutil.Process(child.pid)
    while child.poll() is None:
        try:
            peak = max(peak, parent.memory_info().rss + observed.memory_info().rss)
            samples += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError) as exc:
            if child.poll() is None:
                monitor_error = type(exc).__name__
                stop = "MONITOR_FAILURE"
                break
        if peak > protocol["rss_cap_bytes"]:
            stop = "RSS_CAP"
            break
        if time.monotonic() - start > protocol["parent_wall_cap_seconds"]:
            stop = "WALL_CAP"
            break
        time.sleep(.1)
    if stop and child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
    exit_code = child.wait()
wall = time.monotonic() - start
stream = (HERE / "solver.stdout").read_text(errors="replace")
if stop:
    status = "BOUNDED_UNKNOWN" if stop == "WALL_CAP" else stop
elif "s SATISFIABLE" in stream:
    status = "SAT_MODEL_UNVERIFIED"
elif "s UNSATISFIABLE" in stream:
    status = "UNSAT_UNVERIFIED"
elif "s INDETERMINATE" in stream:
    status = "BOUNDED_UNKNOWN"
else:
    status = "PRODUCER_FAILURE_NO_TERMINAL_STATUS"
restarts = [line for line in stream.splitlines() if line.startswith("c rst")]
result = {"status": status, "candidate_id": None,
          "curve_id": protocol["curve_id"], "worker_count": 1,
          "command": command, "solver_exit_code": exit_code,
          "stop_reason": stop, "monitor_error": monitor_error,
          "solver_terminal_sat": "s SATISFIABLE" in stream,
          "solver_terminal_unsat": "s UNSATISFIABLE" in stream,
          "solver_terminal_indeterminate": "s INDETERMINATE" in stream,
          "last_restart_line": restarts[-1] if restarts else None,
          "solver_stdout_sha256": sha(HERE / "solver.stdout"),
          "solver_stderr_sha256": sha(HERE / "solver.stderr"),
          "query_parent_wall_seconds": wall,
          "target_dependent_base_build_seconds": base["total_seconds"],
          "target_dependent_bdd_build_seconds": build["total_seconds"],
          "charged_stage_wall_seconds": base["total_seconds"] +
                                        build["total_seconds"] + wall,
          "sampled_peak_combined_rss_bytes": peak,
          "rss_samples": samples,
          "protocol_sha256": sha(HERE / "query_protocol.json")}
(HERE / "query_result.json").write_text(json.dumps(result, sort_keys=True, indent=2)+"\n")
print(json.dumps({k: result[k] for k in ("status", "stop_reason",
                                          "query_parent_wall_seconds",
                                          "charged_stage_wall_seconds",
                                          "sampled_peak_combined_rss_bytes")}, sort_keys=True))
