"""Monitor the checked-Sage all-state replay in one worker."""
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "sage_protocol.json").read_text())
assert protocol["status"] == "FROZEN"
for path, expected in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
parent = psutil.Process(os.getpid())
command = ["/Volumes/SSD990/cryptanalysis/sage", "-python", str(HERE / "audit_sage.py")]
start = time.monotonic_ns()
peak = 0
degraded = False
stop = None
with (HERE / "sage.stdout").open("x") as out, (HERE / "sage.stderr").open("x") as err:
    child = subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True)
    process = psutil.Process(child.pid)
    while child.poll() is None:
        try:
            peak = max(peak, parent.memory_info().rss + process.memory_info().rss)
        except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
            if child.poll() is None:
                degraded = True
        if peak > protocol["rss_cap_bytes"]:
            stop = "RSS_CAP"
        elif time.monotonic_ns() - start > protocol["wall_cap_seconds"] * 10**9:
            stop = "WALL_CAP"
        if stop:
            os.killpg(child.pid, signal.SIGTERM)
            break
        time.sleep(.1)
    child.wait()
receipt = {
    "status": "EXIT_0" if child.returncode == 0 else stop or "EXIT_ERROR",
    "command": command, "exit_code": child.returncode,
    "wall_ns": time.monotonic_ns() - start,
    "sampled_peak_combined_rss_bytes": peak,
    "monitor_degraded": degraded, "stop_reason": stop,
    "protocol_sha256": hashlib.sha256((HERE / "sage_protocol.json").read_bytes()).hexdigest(),
    "sha256": {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
               for name in ("sage.stdout", "sage.stderr", "sage_result.json")
               if (HERE / name).exists()},
}
with (HERE / "sage_run_result.json").open("x") as stream:
    json.dump(receipt, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(receipt["status"], receipt["wall_ns"] / 1e9)
