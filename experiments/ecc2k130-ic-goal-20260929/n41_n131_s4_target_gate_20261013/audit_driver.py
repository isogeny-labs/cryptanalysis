"""Run the frozen Sage audit with one worker and direct-PID RSS sampling."""

import hashlib
import json
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
LAUNCHER = "/Volumes/SSD990/cryptanalysis/sage"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "audit_protocol.json").read_text())
    assert protocol["status"] == "FROZEN"
    started = time.monotonic()
    status = "UNKNOWN"
    peak_rss = 0
    samples = 0
    monitor_error = None
    stdout_path, stderr_path = HERE / "sage_stdout_v3.log", HERE / "sage_stderr_v3.log"
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        child = subprocess.Popen([LAUNCHER, "-python", str(HERE / "audit_sage.py")],
                                 cwd=HERE, stdout=stdout, stderr=stderr)
        proc = psutil.Process(child.pid)
        while True:
            code = child.poll()
            if code is not None:
                status = "EXIT_0" if code == 0 else "EXIT_NONZERO"
                break
            try:
                rss = proc.memory_info().rss
                peak_rss = max(peak_rss, rss)
                samples += 1
            except (psutil.Error, PermissionError) as exc:
                monitor_error = repr(exc)
                status = "MONITOR_ERROR"
                child.terminate()
                child.wait(timeout=5)
                break
            if peak_rss > protocol["rss_cap_bytes"]:
                status = "RSS_CAP"
                child.terminate()
                child.wait(timeout=5)
                break
            if time.monotonic() - started > protocol["wall_cap_seconds"]:
                status = "WALL_CAP"
                child.terminate()
                child.wait(timeout=5)
                break
            time.sleep(0.25)
    receipt = {"status": status, "returncode": child.returncode,
               "protocol_sha256": sha(HERE / "audit_protocol.json"),
               "driver_sha256": sha(HERE / "audit_driver.py"),
               "launcher": LAUNCHER,
               "elapsed_seconds": time.monotonic() - started,
               "peak_sampled_direct_pid_rss_bytes": peak_rss,
               "rss_samples": samples, "monitor_error": monitor_error,
               "stdout_sha256": sha(stdout_path), "stderr_sha256": sha(stderr_path),
               "audit_result_present": (HERE / "audit_result.json").exists()}
    (HERE / "audit_run_v3.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
