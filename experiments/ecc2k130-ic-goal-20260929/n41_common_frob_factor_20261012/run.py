"""One-worker frozen N41 five-pair target join with full resource receipts."""

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
PAIRS = GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv"
PARENT_CPP = GOAL / "n41_w8_ninepair_join_control_20261012/join9.cpp"
RSS_CAP = 4 * 1024**3
TIME_CAP = 180


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    files = {"runner": HERE / "run.py", "source": HERE / "join5.cpp",
             "binary": HERE / "join5", "pairs": PAIRS,
             "parent_cpp": PARENT_CPP, "target": HERE / "target.json"}
    assert protocol["status"] == "FROZEN_BEFORE_N41_PUBLIC_JOIN"
    assert protocol["sha256"] == {name: sha(path) for name, path in files.items()}
    assert protocol["one_worker"] is True
    assert protocol["parent_time_cap_s"] == TIME_CAP
    assert protocol["combined_rss_cap_bytes"] == RSS_CAP
    assert protocol["left_kept_cap"] == 2000000
    assert protocol["right_kept_cap"] == 5000000
    target = json.loads((HERE / "target.json").read_text())
    assert target["status"] == "PASS_CHECKED_SAGE_TARGET_FACTOR"
    assert target["public_point"] == protocol["public_point"]
    assert target["transformed_target"] == protocol["transformed_target"]
    x, y = target["transformed_target"]
    command = [str(HERE / "join5"), str(PAIRS), str(x), str(y)]
    stdout, stderr = HERE / "stdout.log", HERE / "stderr.log"
    start = time.monotonic_ns()
    peak = 0
    stop = None
    with stdout.open("x") as out, stderr.open("x") as err:
        child = subprocess.Popen(command, stdout=out, stderr=err)
        owner, worker = psutil.Process(os.getpid()), psutil.Process(child.pid)
        while child.poll() is None:
            try:
                peak = max(peak, owner.memory_info().rss + worker.memory_info().rss)
            except psutil.NoSuchProcess:
                break
            if peak > RSS_CAP:
                stop = "RSS_CAP"
            elif time.monotonic_ns() - start >= TIME_CAP*10**9:
                stop = "PARENT_TIME_CAP"
            if stop:
                child.kill()
                break
            time.sleep(0.025)
        code = child.wait()
    ended = time.monotonic_ns()
    lines = stdout.read_text().splitlines()
    source = [line for line in lines if line.startswith("SOURCE_PASS ")]
    left = [line for line in lines if line.startswith("LEFT_DONE ")]
    hits = [line for line in lines if line.startswith("HIT ")]
    exhausted = [line for line in lines if line.startswith("EXHAUSTED ")]
    assert len(source) <= 1 and len(left) <= 1 and len(hits) <= 1 and len(exhausted) <= 1
    status = ("HIT_PENDING_INDEPENDENT_REPLAY" if code == 0 and hits else
              "EXHAUSTED" if code == 0 and exhausted else
              stop or "PRODUCER_FAILURE")
    result = {"status": status, "stop_reason": stop, "exit_code": code,
              "parent_wall_ns": ended-start,
              "peak_combined_rss_bytes_sampled": peak,
              "source_line": source[0] if source else None,
              "left_line": left[0] if left else None,
              "hit_line": hits[0] if hits else None,
              "exhausted_line": exhausted[0] if exhausted else None,
              "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr),
              "protocol_sha256": sha(HERE / "protocol.json")}
    with (HERE / "result.json").open("x") as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write("\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
