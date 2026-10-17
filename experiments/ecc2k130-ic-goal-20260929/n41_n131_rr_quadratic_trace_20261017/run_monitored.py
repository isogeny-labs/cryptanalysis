"""Apply a one-worker wall/RSS envelope and retain the raw producer output."""
import hashlib
import json
import os
import psutil
import signal
import subprocess
import time
from pathlib import Path


D = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = json.loads((D / "protocol.json").read_text())
    rp = json.loads((D / "run_protocol.json").read_text())
    assert sha(D / "protocol.json") == rp["protocol_sha256"]
    assert sha(D / "run_monitored.py") == rp["monitor_sha256"]
    assert sha(D / "sage_runtime_info.json") == rp["runtime_info_sha256"]
    command = ["/Volumes/SSD990/cryptanalysis/sage", "-python", str(D / "run.py")]
    start = time.monotonic()
    peak = 0
    stop = None
    parent = psutil.Process(os.getpid())
    with (D / "run.stdout").open("x") as out, (D / "run.stderr").open("x") as err:
        child = subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True)
        process = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                peak = max(peak, parent.memory_info().rss + process.memory_info().rss)
            except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
                if child.poll() is None:
                    stop = "MONITOR_DEGRADED"
            if peak > p["rss_cap_bytes"]:
                stop = "RSS_CAP"
            elif time.monotonic() - start > p["wall_cap_s"]:
                stop = "PARENT_WALL_CAP"
            if stop:
                os.killpg(child.pid, signal.SIGTERM)
                break
            time.sleep(0.01)
        child.wait()
    receipt = {
        "status": "PRODUCER_COMPLETED" if child.returncode == 0 and stop is None else "BOUNDED_OR_FAILED",
        "protocol_sha256": sha(D / "protocol.json"),
        "run_protocol_sha256": sha(D / "run_protocol.json"),
        "command": command,
        "exit_code": child.returncode,
        "stop_reason": stop,
        "parent_wall_s": time.monotonic() - start,
        "sampled_peak_combined_rss_bytes": peak,
        "stdout_sha256": sha(D / "run.stdout"),
        "stderr_sha256": sha(D / "run.stderr"),
        "result_sha256": sha(D / "result.json") if (D / "result.json").exists() else None,
    }
    (D / "run_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
