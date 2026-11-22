"""Monitor one independent checked-Sage replay against the frozen resource caps."""
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg = json.loads((HERE / "audit_protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_N131_SIGN_NORM_AUDIT"
assert cfg["worker_count"] == 1
for label, source in cfg["sources"].items():
    assert sha(source["path"]) == source["sha256"], label
receipt_path = HERE / "audit_receipt.json"
assert not receipt_path.exists()
command = [cfg["sage_launcher"], "-python", str(HERE / "audit_sage.py")]
parent = psutil.Process(os.getpid())
started = time.monotonic()
peak = samples = 0
stop = monitor_error = None
stdout, stderr = HERE / "audit.stdout", HERE / "audit.stderr"
with stdout.open("xb") as out, stderr.open("xb") as err:
    child = subprocess.Popen(command, cwd="/Volumes/SSD990/cryptanalysis",
                             stdout=out, stderr=err, start_new_session=True)
    (HERE / "audit_handle.json").write_text(json.dumps(
        {"pid": child.pid, "command": command, "started_monotonic": started},
        indent=2, sort_keys=True) + "\n")
    observed = psutil.Process(child.pid)
    while child.poll() is None:
        try:
            peak = max(peak, parent.memory_info().rss + observed.memory_info().rss)
            samples += 1
        except psutil.NoSuchProcess:
            if child.poll() is not None:
                break
            stop = "MONITOR_FAILURE"
            monitor_error = "NoSuchProcessWhileLive"
            break
        except (psutil.AccessDenied, PermissionError) as exc:
            if child.poll() is None:
                stop = "MONITOR_FAILURE"
                monitor_error = type(exc).__name__
                break
        if peak > cfg["rss_cap_bytes"]:
            stop = "RSS_CAP"
            break
        if time.monotonic() - started > cfg["wall_cap_seconds"]:
            stop = "WALL_CAP"
            break
        time.sleep(.1)
    if stop and child.poll() is None:
        child.terminate()
    exit_code = child.wait()
result_path = HERE / "audit_result.json"
status = ("COMPLETE" if not stop and exit_code == 0 and result_path.exists()
          else stop or "PRODUCER_FAILURE")
receipt = {"status": status, "candidate_id": None, "curve_id": cfg["curve_id"],
           "command": command, "child_pid": child.pid, "exit_code": exit_code,
           "stop_reason": stop, "monitor_error": monitor_error,
           "wall_seconds": time.monotonic() - started,
           "sampled_peak_combined_rss_bytes": peak, "rss_samples": samples,
           "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr),
           "result_sha256": sha(result_path) if result_path.exists() else None,
           "protocol_sha256": sha(HERE / "audit_protocol.json")}
receipt_path.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
print(json.dumps({key: receipt[key] for key in
                  ("status", "wall_seconds", "sampled_peak_combined_rss_bytes")},
                 sort_keys=True))
