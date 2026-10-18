"""One-worker parent monitor for the frozen full quadratic-rank census."""
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
protocol = json.loads((HERE / "full_protocol.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for relative, digest in protocol["repo_sha256"].items():
    assert sha(ROOT / relative) == digest, relative
for local, digest in protocol["local_sha256"].items():
    assert sha(HERE / local) == digest, local

command = [str(HERE / "full_census"), str(ROOT / protocol["input"])]
assert protocol["command"] == command
assert protocol["worker_count"] == 1

started = time.monotonic_ns()
peak = 0
stop = None
degraded = False
parent = psutil.Process()
with (HERE / "full_stdout.txt").open("x") as out, \
     (HERE / "full_stderr.txt").open("x") as err:
    child = subprocess.Popen(command, stdout=out, stderr=err,
                             start_new_session=True)
    process = psutil.Process(child.pid)
    while child.poll() is None:
        try:
            peak = max(peak, parent.memory_info().rss + process.memory_info().rss)
        except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
            if child.poll() is None:
                degraded = True
        elapsed = time.monotonic_ns() - started
        if peak > protocol["rss_cap_bytes"]:
            stop = "RSS_CAP"
        elif elapsed > protocol["wall_cap_seconds"] * 10**9:
            stop = "WALL_CAP"
        if stop:
            os.killpg(child.pid, signal.SIGTERM)
            break
        time.sleep(0.05)
    child.wait()
ended = time.monotonic_ns()

lines = (HERE / "full_stdout.txt").read_text(errors="replace").splitlines()
summary = [line for line in lines if line.startswith("SUMMARY ")]
pair_rows = [line for line in lines if line.startswith("PAIR ")]
rank_rows = [line for line in lines if line.startswith("RANK ")]
stderr = (HERE / "full_stderr.txt").read_text(errors="replace")
status = ("COMPLETE_N41_QUADRATIC_PAIR_CENSUS"
          if child.returncode == 0 and not stop and not stderr and
             len(summary) == 1 and len(pair_rows) == 1600 else
          ("BOUNDED_UNKNOWN" if stop else "PRODUCER_FAILURE"))
receipt = {"status": status, "candidate_id": None,
           "exit_code": child.returncode, "stop_reason": stop,
           "monitor_degraded": degraded, "wall_ns": ended-started,
           "sampled_peak_combined_rss_bytes": peak,
           "summary": summary, "rank_rows": rank_rows,
           "pair_rows": pair_rows,
           "stdout_sha256": sha(HERE / "full_stdout.txt"),
           "stderr_sha256": sha(HERE / "full_stderr.txt"),
           "protocol_sha256": sha(HERE / "full_protocol.json")}
(HERE / "full_result.json").write_text(json.dumps(receipt, sort_keys=True, indent=2)+"\n")
print(json.dumps({"status": status, "wall_seconds": (ended-started)/1e9,
                  "peak_rss": peak, "summary": summary}, sort_keys=True), flush=True)
sys.exit(0 if status == "COMPLETE_N41_QUADRATIC_PAIR_CENSUS" else 1)
