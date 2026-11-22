"""Monitored one-worker CryptoMiniSat pair with exact status preservation."""

import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "protocol.json").read_text())
assert protocol["status"] == "FROZEN"
for path, expected in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
parent = psutil.Process(os.getpid())
rows = []
for case in protocol["cases"]:
    name = case["name"]
    command = [protocol["solver"], "--threads", "1", "--verb", "1",
               "--maxtime", str(protocol["solver_cap_seconds"]),
               str(HERE / f"{name}.xcnf")]
    start = time.monotonic_ns()
    peak = 0
    degraded = False
    stop = None
    with (HERE / f"{name}.stdout").open("x") as out, \
            (HERE / f"{name}.stderr").open("x") as err:
        child = subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True)
        process = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                peak = max(peak, parent.memory_info().rss + process.memory_info().rss)
            except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
                degraded = True
            if peak > protocol["rss_cap_bytes"]:
                stop = "RSS_CAP"
            elif time.monotonic_ns() - start > protocol["parent_cap_seconds"] * 10**9:
                stop = "PARENT_WALL_CAP"
            if stop:
                os.killpg(child.pid, signal.SIGTERM)
                break
            time.sleep(.1)
        child.wait()
    wall = time.monotonic_ns() - start
    stdout = (HERE / f"{name}.stdout").read_text(errors="replace")
    raw_status = [line.strip() for line in stdout.splitlines() if line.startswith("s ")]
    rows.append({"name": name, "command": command, "exit_code": child.returncode,
                 "wall_ns": wall, "sampled_peak_combined_rss_bytes": peak,
                 "monitor_degraded": degraded, "stop_reason": stop,
                 "raw_solver_status_lines": raw_status,
                 "stdout_sha256": hashlib.sha256((HERE / f"{name}.stdout").read_bytes()).hexdigest(),
                 "stderr_sha256": hashlib.sha256((HERE / f"{name}.stderr").read_bytes()).hexdigest()})
    with (HERE / "journal.jsonl").open("a") as stream:
        stream.write(json.dumps(rows[-1], sort_keys=True) + "\n")
result = {"status": "COMPLETE_MONITORED_PAIR", "cases": rows,
          "protocol_sha256": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest()}
with (HERE / "run_result.json").open("x") as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(result["status"], [(row["name"], row["raw_solver_status_lines"])
                                for row in rows])
