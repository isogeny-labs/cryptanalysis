"""One-worker wall/RSS-bounded unpinned ten-pair public-point join."""

import hashlib
import json
import resource
import subprocess
import time
from pathlib import Path

import psutil


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
INPUT = ROOT / "n41_w8_sixpair_mitm_20261011/join_input.tsv"
PARENT = ROOT / "n41_w8_ninepair_join_control_20261012"
protocol = json.loads((HERE / "protocol.json").read_text())
for name, path in {
    "source": HERE / "join10.cpp",
    "included_group_source": PARENT / "join9.cpp",
    "binary": HERE / "join10",
    "runner": HERE / "run.py",
    "input": INPUT,
    "ninepair_public_point_audit": PARENT / "audit_result.json",
}.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest() == protocol["sha256"][name]
assert protocol["status"] == "FROZEN_UNPINNED_N41_TENPAIR_PUBLIC_POINT_CONTROL"
assert not (HERE / "receipt.json").exists()
start = time.monotonic_ns()
before = resource.getrusage(resource.RUSAGE_CHILDREN)
parent = psutil.Process()
peak, stop = 0, None
with (HERE / "stdout.log").open("x") as out, (HERE / "stderr.log").open("x") as err:
    child = subprocess.Popen([str(HERE / "join10"), str(INPUT)], stdout=out, stderr=err)
    process = psutil.Process(child.pid)
    while child.poll() is None:
        try:
            rss = parent.memory_info().rss + process.memory_info().rss
        except psutil.NoSuchProcess:
            rss = parent.memory_info().rss
        peak = max(peak, rss)
        if rss > protocol["combined_rss_cap_bytes"]:
            stop = "RSS_CAP"
        elif time.monotonic_ns() - start >= protocol["total_wall_cap_seconds"] * 10**9:
            stop = "TOTAL_WALL_CAP"
        if stop:
            child.kill()
            break
        time.sleep(0.05)
    code = child.wait()
end = time.monotonic_ns()
after = resource.getrusage(resource.RUSAGE_CHILDREN)
stdout = (HERE / "stdout.log").read_text()
stderr = (HERE / "stderr.log").read_text()
hit = next((line for line in stdout.splitlines() if line.startswith("HIT ")), None)
exhausted = next((line for line in stdout.splitlines() if line.startswith("EXHAUSTED ")), None)
left = next((line for line in stdout.splitlines() if line.startswith("LEFT_DONE ")), None)
status = ("BOUNDED_UNKNOWN" if stop else "HIT_PENDING_INDEPENDENT_REPLAY" if hit and code == 0
          else "EXHAUSTED" if exhausted and code == 0 else "ERROR")
receipt = {
    "status": status,
    "candidate_id": None,
    "worker_count": 1,
    "target_law": protocol["target_law"],
    "public_point_source": "n41_w8_sixpair_mitm_20261011/join_input.tsv",
    "stop_reason": stop,
    "exit_code": code,
    "runner_wall_ns": end - start,
    "peak_combined_rss_bytes_sampled": peak,
    "child_user_seconds": after.ru_utime - before.ru_utime,
    "child_system_seconds": after.ru_stime - before.ru_stime,
    "left_line": left,
    "hit_line": hit,
    "exhausted_line": exhausted,
    "stderr": stderr,
    "stdout_sha256": hashlib.sha256((HERE / "stdout.log").read_bytes()).hexdigest(),
    "stderr_sha256": hashlib.sha256((HERE / "stderr.log").read_bytes()).hexdigest(),
    "protocol_sha256": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest(),
}
(HERE / "receipt.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
print(status, (end - start) / 1e9, peak, flush=True)
