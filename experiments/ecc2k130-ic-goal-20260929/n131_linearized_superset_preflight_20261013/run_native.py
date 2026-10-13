#!/usr/bin/env python3
"""Bounded one-worker native W18 constructed-block GCD stage."""

import hashlib
import json
import os
import signal
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil


HERE = Path(__file__).resolve().parent
GOAL = HERE.parent


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    protocol = json.loads((HERE / "native_protocol.json").read_text())
    assert protocol["status"] == "FROZEN"
    for path, digest in protocol["sources"].items():
        assert sha(Path(path)) == digest, path
    output = HERE / "native_result.json"
    stdout_path = HERE / "native.stdout.txt"
    stderr_path = HERE / "native.stderr.txt"
    receipt_path = HERE / "native_run_status.json"
    for path in (output, stdout_path, stderr_path, receipt_path):
        if path.exists():
            raise FileExistsError(path)
    command = [str(HERE / "native_w18"), str(HERE / "native_input.txt"),
               str(output), str(protocol["query_cap_seconds"]),
               str(protocol["rss_cap_bytes"]),
               str(GOAL / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv")]
    started = datetime.now(timezone.utc).isoformat()
    began = time.monotonic()
    peak_rss = peak_cpu = 0
    stop_reason = None
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr,
                                   start_new_session=True)
        child = psutil.Process(process.pid)
        while process.poll() is None:
            try:
                peak_rss = max(peak_rss, child.memory_info().rss)
                cpu = child.cpu_times()
                peak_cpu = max(peak_cpu, cpu.user+cpu.system)
            except psutil.NoSuchProcess:
                pass
            if peak_rss > protocol["rss_cap_bytes"]:
                stop_reason = "RSS_CAP"
            elif time.monotonic()-began >= protocol["parent_wall_cap_seconds"]:
                stop_reason = "PARENT_WALL_CAP"
            if stop_reason:
                os.killpg(process.pid, signal.SIGTERM)
                break
            time.sleep(.1)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            stop_reason = (stop_reason or "DRAIN_TIMEOUT") + "_KILLED"
    status = ("EXIT_0" if process.returncode == 0 and stop_reason is None
              else "CENSORED_TIME" if stop_reason == "PARENT_WALL_CAP"
              else "OOM" if stop_reason == "RSS_CAP"
              else "PRODUCER_OR_RUNTIME_FAILURE")
    receipt = {
        "status": status, "started_utc": started,
        "command": command, "exit_code": process.returncode,
        "stop_reason": stop_reason,
        "parent_wall_seconds": time.monotonic()-began,
        "sampled_peak_rss_bytes": peak_rss,
        "sampled_peak_cpu_seconds": peak_cpu,
        "source_sha256": {
            "protocol": sha(HERE / "native_protocol.json"),
            "input": sha(HERE / "native_input.txt"),
            "binary": sha(HERE / "native_w18"),
            "stdout": sha(stdout_path), "stderr": sha(stderr_path),
            "native_result": sha(output) if output.exists() else None,
        },
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: receipt[k] for k in ("status", "parent_wall_seconds",
                                                 "sampled_peak_rss_bytes")}), flush=True)


if __name__ == "__main__":
    main()
