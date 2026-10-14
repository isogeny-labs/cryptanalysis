import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
protocol = json.loads((HERE / "exception_audit_run_protocol.json").read_text())
assert protocol["status"] == "FROZEN"
for path, expected in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
command = [str(ROOT / "sage"), "-python", str(HERE / "audit_exception_sage.py")]
parent = psutil.Process(os.getpid())
start = time.monotonic_ns()
peak_rss = peak_cpu = 0
monitor_degraded = False
stop_reason = None
with (HERE / "exception_audit.stdout").open("x") as out, (HERE / "exception_audit.stderr").open("x") as err:
    child = subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True)
    process = psutil.Process(child.pid)
    while child.poll() is None:
        try:
            peak_rss = max(peak_rss, parent.memory_info().rss + process.memory_info().rss)
            cpu = process.cpu_times()
            peak_cpu = max(peak_cpu, cpu.user + cpu.system)
        except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
            monitor_degraded = True
        if peak_rss > protocol["rss_cap_bytes"]:
            stop_reason = "RSS_CAP"
        elif time.monotonic_ns() - start > protocol["wall_cap_seconds"] * 1_000_000_000:
            stop_reason = "WALL_CAP"
        if stop_reason:
            os.killpg(child.pid, signal.SIGTERM)
            break
        time.sleep(.1)
    child.wait()
wall_ns = time.monotonic_ns() - start
result = {
    "status": "EXIT_0" if child.returncode == 0 else (stop_reason or "EXIT_ERROR"),
    "command": command, "exit_code": child.returncode,
    "wall_ns": wall_ns, "sampled_peak_combined_rss_bytes": peak_rss,
    "sampled_peak_child_cpu_seconds": peak_cpu,
    "monitor_degraded": monitor_degraded,
    "stop_reason": stop_reason,
    "protocol_sha256": hashlib.sha256((HERE / "exception_audit_run_protocol.json").read_bytes()).hexdigest(),
    "sha256": {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
               for name in ("exception_audit.stdout", "exception_audit.stderr", "exception_audit_result.json")
               if (HERE / name).exists()},
}
with (HERE / "exception_audit_run_result.json").open("x") as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(result["status"], wall_ns / 1e9)
