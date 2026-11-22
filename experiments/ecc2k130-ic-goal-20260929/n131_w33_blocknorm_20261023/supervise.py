"""One-worker parent wall and RSS cap for the checked Sage block-norm runs."""
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
CASE = sys.argv[1]
assert CASE in ("n41", "n131")
cfg = json.loads((HERE / f"protocol_{CASE}.json").read_text())
assert cfg["status"] == f"FROZEN_BEFORE_{CASE.upper()}_BLOCK_NORM"
assert cfg["worker_count"] == 1
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
for item in cfg["sources"].values():
    assert sha(item["path"]) == item["sha256"]
for file in (HERE / f"{CASE}.stdout", HERE / f"{CASE}.stderr",
             HERE / f"{CASE}_result.json", HERE / f"{CASE}_supervisor.json"):
    assert not file.exists(), file
cmd = [cfg["sage_launcher"], "-python", str(HERE / "blocknorm_sage.py"), CASE]
start = time.monotonic()
peak = 0
samples = 0
stop = None
with (HERE / f"{CASE}.stdout").open("xb") as stdout, (HERE / f"{CASE}.stderr").open("xb") as stderr:
    child = subprocess.Popen(cmd, cwd=HERE, stdout=stdout, stderr=stderr, start_new_session=True)
    parent = psutil.Process(os.getpid())
    while child.poll() is None:
        try:
            proc = psutil.Process(child.pid)
            members = [parent, proc, *proc.children(recursive=True)]
            rss = sum(member.memory_info().rss for member in members)
            peak = max(peak, rss)
            samples += 1
        except psutil.NoSuchProcess:
            time.sleep(0.02)
            continue
        if peak > cfg["rss_cap_bytes"]:
            stop = "RSS_CAP"
            break
        if time.monotonic() - start > cfg["wall_cap_seconds"]:
            stop = "WALL_CAP"
            break
        time.sleep(0.02)
    if stop and child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
    code = child.wait()
result_path = HERE / f"{CASE}_result.json"
result = json.loads(result_path.read_text()) if result_path.exists() else None
status = stop or (result["status"] if code == 0 and result else "PRODUCER_FAILURE")
receipt = {"status": status, "case": CASE, "candidate_id": None,
           "curve_id": cfg["curve_id"], "command": cmd, "exit_code": code,
           "wall_seconds": time.monotonic() - start,
           "sampled_peak_combined_rss_bytes": peak, "rss_samples": samples,
           "stop_reason": stop, "result_sha256": sha(result_path) if result else None,
           "stdout_sha256": sha(HERE / f"{CASE}.stdout"),
           "stderr_sha256": sha(HERE / f"{CASE}.stderr"),
           "protocol_sha256": sha(HERE / f"protocol_{CASE}.json"),
           "supervisor_sha256": sha(__file__)}
(HERE / f"{CASE}_supervisor.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": status, "wall_seconds": receipt["wall_seconds"],
                  "sampled_peak_combined_rss_bytes": peak}, sort_keys=True), flush=True)
