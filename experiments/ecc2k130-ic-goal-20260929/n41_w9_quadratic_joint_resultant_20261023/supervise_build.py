"""Monitor one checked-Sage circuit builder with parent wall and RSS caps."""
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
cfg = json.loads((HERE / "build_run_protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_N41_RESULTANT_CIRCUIT_RUN"
assert cfg["worker_count"] == 1
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
for item in cfg["sources"].values():
    assert sha(item["path"]) == item["sha256"]
for name in ("build.stdout", "build.stderr", "build_result.json", "build_supervisor.json"):
    assert not (HERE / name).exists()
cmd = [cfg["sage_launcher"], "-python", str(HERE / "build_resultant.py")]
start = time.monotonic()
peak = samples = 0
stop = None
with (HERE / "build.stdout").open("xb") as stdout, (HERE / "build.stderr").open("xb") as stderr:
    child = subprocess.Popen(cmd, cwd=HERE, stdout=stdout, stderr=stderr, start_new_session=True)
    (HERE / "build_handle.json").write_text(json.dumps({"pid": child.pid,
        "command": cmd, "started_monotonic": start}, sort_keys=True, indent=2) + "\n")
    parent = psutil.Process(os.getpid())
    while child.poll() is None:
        try:
            proc = psutil.Process(child.pid)
            peak = max(peak, parent.memory_info().rss + proc.memory_info().rss)
            samples += 1
        except psutil.NoSuchProcess:
            time.sleep(0.02)
            continue
        except (psutil.AccessDenied, PermissionError):
            if child.poll() is None:
                stop = "MONITOR_FAILURE"
            break
        if peak > cfg["rss_cap_bytes"]:
            stop = "RSS_CAP"
            break
        if time.monotonic() - start > cfg["wall_cap_seconds"]:
            stop = "WALL_CAP"
            break
        time.sleep(0.02)
    termination_error = None
    if stop and child.poll() is None:
        try:
            child.terminate()
        except PermissionError as exc:
            termination_error = repr(exc)
            stop = "TERMINATION_FAILURE"
    code = child.wait()
result_path = HERE / "build_result.json"
result = json.loads(result_path.read_text()) if result_path.exists() else None
status = stop or (result["status"] if code == 0 and result else "PRODUCER_FAILURE")
if status.startswith("PASS_") and samples == 0:
    status = "MONITOR_INCOMPLETE"
receipt = {"status": status, "candidate_id": None, "curve_id": cfg["curve_id"],
           "command": cmd, "exit_code": code, "wall_seconds": time.monotonic() - start,
           "sampled_peak_combined_rss_bytes": peak, "rss_samples": samples,
           "monitor_scope": "parent plus direct child PID; checked launcher exec chain",
           "stop_reason": stop, "termination_error": termination_error,
           "result_sha256": sha(result_path) if result else None,
           "stdout_sha256": sha(HERE / "build.stdout"),
           "stderr_sha256": sha(HERE / "build.stderr"),
           "protocol_sha256": sha(HERE / "build_run_protocol.json"),
           "supervisor_sha256": sha(__file__)}
(HERE / "build_supervisor.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": status, "wall_seconds": receipt["wall_seconds"],
                  "sampled_peak_combined_rss_bytes": peak}, sort_keys=True), flush=True)
