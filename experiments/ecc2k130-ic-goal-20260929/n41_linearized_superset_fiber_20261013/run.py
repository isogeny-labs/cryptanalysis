#!/usr/bin/env python3
"""Run one frozen Sage phase with a bounded wall and sampled RSS receipt."""

import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil


HERE = Path(__file__).resolve().parent
SAGE = HERE.parents[2] / "sage"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if len(sys.argv) != 1:
        raise SystemExit("usage: run.py")
    phase = "query"
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert protocol["status"] == "FROZEN"
    for path, digest in protocol["sources"].items():
        assert sha(Path(path)) == digest, path
    script = HERE / "query_sage.py"
    output = HERE / f"{phase}_run_status.json"
    stdout_path = HERE / f"{phase}_stdout.log"
    stderr_path = HERE / f"{phase}_stderr.log"
    for path in (output, stdout_path, stderr_path):
        if path.exists():
            raise FileExistsError(path)
    command = [str(SAGE), "-python", str(script)]
    cap_seconds = protocol[f"{phase}_wall_cap_seconds"]
    cap_rss = protocol["process_tree_rss_cap_bytes"]
    started = datetime.now(timezone.utc).isoformat()
    began = time.monotonic()
    peak = 0
    peak_cpu = 0.0
    degraded = False
    stop_reason = None
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr,
                                   start_new_session=True)
        root = psutil.Process(process.pid)
        while process.poll() is None:
            try:
                processes = [root, *root.children(recursive=True)]
            except (psutil.AccessDenied, PermissionError, psutil.NoSuchProcess):
                processes = [root]
                degraded = True
            rss = 0
            cpu = 0.0
            for item in processes:
                try:
                    rss += item.memory_info().rss
                    usage = item.cpu_times()
                    cpu += usage.user + usage.system
                except (psutil.AccessDenied, PermissionError, psutil.NoSuchProcess):
                    degraded = True
            peak = max(peak, rss)
            peak_cpu = max(peak_cpu, cpu)
            if peak > cap_rss:
                stop_reason = "RSS_CAP"
            elif time.monotonic() - began >= cap_seconds:
                stop_reason = "WALL_CAP"
            if stop_reason:
                os.killpg(process.pid, signal.SIGTERM)
                break
            time.sleep(0.1)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            stop_reason = (stop_reason or "DRAIN_TIMEOUT") + "_KILLED"
    wall = time.monotonic() - began
    status = ("EXIT_0" if process.returncode == 0 and stop_reason is None
              else "CENSORED_TIME" if stop_reason == "WALL_CAP"
              else "OOM" if stop_reason == "RSS_CAP"
              else "PRODUCER_OR_RUNTIME_FAILURE")
    receipt = {
        "status": status, "phase": phase, "started_utc": started,
        "command": command, "exit_code": process.returncode,
        "stop_reason": stop_reason, "parent_wall_seconds": wall,
        "sampled_peak_process_tree_rss_bytes": peak,
        "sampled_peak_process_tree_cpu_seconds": peak_cpu,
        "process_tree_monitor_degraded": degraded,
        "source_sha256": {
            "protocol": sha(HERE / "protocol.json"),
            "script": sha(script), "stdout": sha(stdout_path),
            "stderr": sha(stderr_path), "sage_runtime_info": sha(HERE / "sage_runtime_info.json"),
        },
    }
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: receipt[k] for k in ("phase", "status", "parent_wall_seconds",
                                                 "sampled_peak_process_tree_rss_bytes",
                                                 "process_tree_monitor_degraded")}), flush=True)


if __name__ == "__main__":
    main()
