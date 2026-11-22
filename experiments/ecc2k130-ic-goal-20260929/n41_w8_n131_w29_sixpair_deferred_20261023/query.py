"""One-worker bounded unpinned N41 public SAT query with RSS monitor."""
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg = json.loads((HERE / "query_protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_N41_DEFERRED_PUBLIC_QUERY"
for name, item in cfg["sources"].items():
    assert sha(item["path"]) == item["sha256"], name
assert cfg["worker_count"] == 1
result_path = HERE / "query_result.json"
assert not result_path.exists()
command = [cfg["solver"], "--threads=1",
           f"--maxtime={cfg['solver_wall_cap_seconds']}",
           "--zero-exit-status", "--verb=1", "--printsol=1",
           str(HERE / "n41_public_deferred.xcnf")]
started = time.monotonic()
peak = 0
samples = 0
stop = None
monitor_error = None
parent = psutil.Process(os.getpid())
stdout = HERE / "query.stdout"
stderr = HERE / "query.stderr"
with stdout.open("xb") as out, stderr.open("xb") as err:
    child = subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True)
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
        if peak > cfg["rss_cap_bytes"]:
            stop = "RSS_CAP"
            break
        if time.monotonic() - started > cfg["parent_wall_cap_seconds"]:
            stop = "WALL_CAP"
            break
        time.sleep(0.1)
    if stop and child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
    exit_code = child.wait()
stream = stdout.read_text(errors="replace")
if stop == "WALL_CAP" or "s INDETERMINATE" in stream:
    status = "BOUNDED_UNKNOWN"
elif stop:
    status = stop
elif "s SATISFIABLE" in stream:
    status = "SAT_MODEL_UNVERIFIED"
elif "s UNSATISFIABLE" in stream:
    status = "UNSAT_UNCERTIFIED"
else:
    status = "PRODUCER_FAILURE_NO_TERMINAL_STATUS"
restarts = [line for line in stream.splitlines() if line.startswith("c rst")]
result = {"status": status, "candidate_id": None, "curve_id": cfg["curve_id"],
          "public_point": cfg["public_point"], "command": command,
          "stop_reason": stop, "monitor_error": monitor_error,
          "solver_exit_code": exit_code,
          "solver_terminal_sat": "s SATISFIABLE" in stream,
          "solver_terminal_unsat": "s UNSATISFIABLE" in stream,
          "solver_terminal_indeterminate": "s INDETERMINATE" in stream,
          "last_restart_line": restarts[-1] if restarts else None,
          "wall_seconds": time.monotonic() - started,
          "sampled_peak_combined_rss_bytes": peak, "rss_samples": samples,
          "solver_stdout_sha256": sha(stdout), "solver_stderr_sha256": sha(stderr),
          "protocol_sha256": sha(HERE / "query_protocol.json")}
result_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps({k: result[k] for k in ("status", "wall_seconds",
                                             "sampled_peak_combined_rss_bytes")}, sort_keys=True))
