"""Monitor one checked-Sage sign screen under the frozen parent caps."""
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
import psutil

HERE = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg = json.loads((HERE/"coefficient_export_protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_COEFFICIENT_EXPORT" and cfg["worker_count"] == 1
for label, source in cfg["sources"].items():
    assert sha(source["path"]) == source["sha256"], label
assert not (HERE/"coefficient_export_receipt.json").exists()
command = [cfg["sage_launcher"], "-python", str(HERE/"export_pool_coefficients_sage.py")]
parent = psutil.Process(os.getpid())
started = time.monotonic()
peak = samples = 0
stop = monitor_error = None
with (HERE/"coefficient_export.stdout").open("xb") as out, (HERE/"coefficient_export.stderr").open("xb") as err:
    child = subprocess.Popen(command, cwd="/Volumes/SSD990/cryptanalysis",
                             stdout=out, stderr=err, start_new_session=True)
    (HERE/"coefficient_export_handle.json").write_text(json.dumps(
        {"pid": child.pid, "command": command, "started_monotonic": started},
        sort_keys=True, indent=2)+"\n")
    observed = psutil.Process(child.pid)
    while child.poll() is None:
        try:
            peak = max(peak, parent.memory_info().rss+observed.memory_info().rss)
            samples += 1
        except psutil.NoSuchProcess:
            if child.poll() is not None:
                break
            time.sleep(.1)
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
        if time.monotonic()-started > cfg["wall_cap_seconds"]:
            stop = "WALL_CAP"
            break
        time.sleep(.1)
    if stop and child.poll() is None:
        child.terminate()
    exit_code = child.wait()
result_file = HERE/"pool_coefficients.json"
status = ("COMPLETE" if not stop and exit_code == 0 and result_file.exists()
          else stop or "PRODUCER_FAILURE")
receipt = {"status": status, "candidate_id": None, "command": command,
           "child_pid": child.pid, "exit_code": exit_code, "stop_reason": stop,
           "monitor_error": monitor_error, "wall_seconds": time.monotonic()-started,
           "sampled_peak_combined_rss_bytes": peak, "rss_samples": samples,
           "stdout_sha256": sha(HERE/"coefficient_export.stdout"),
           "stderr_sha256": sha(HERE/"coefficient_export.stderr"),
           "result_sha256": sha(result_file) if result_file.exists() else None,
           "protocol_sha256": sha(HERE/"coefficient_export_protocol.json")}
(HERE/"coefficient_export_receipt.json").write_text(json.dumps(receipt, sort_keys=True, indent=2)+"\n")
print(json.dumps({key: receipt[key] for key in ("status", "wall_seconds",
                                               "sampled_peak_combined_rss_bytes")}, sort_keys=True))
