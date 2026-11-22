"""Run the frozen N41 target-conditioned residual probe under a parent cap."""
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
PAIRS = HERE.parent / "n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv"
FILES = {"source": HERE / "residual.cpp", "binary": HERE / "residual",
         "runner": HERE / "run.py", "pairs": PAIRS,
         "parent_cpp": HERE.parent / "n41_w8_ninepair_join_control_20261012/join9.cpp"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert protocol["status"] == "FROZEN_BEFORE_PUBLIC_N41_QUERY"
    assert protocol["sha256"] == {key: sha(value) for key, value in FILES.items()}
    assert protocol["one_worker"] and protocol["combined_rss_cap_bytes"] == 4 * 1024**3
    cmd = [str(HERE / "residual"), str(PAIRS),
           *map(str, protocol["transformed_target"]),
           str(protocol["double_count"]), str(protocol["kept_limit"]),
           str(protocol["worker_query_cap_s"])]
    start = time.monotonic_ns()
    peak, stop = 0, None
    with (HERE / "stdout.log").open("x") as out, (HERE / "stderr.log").open("x") as err:
        child = subprocess.Popen(cmd, stdout=out, stderr=err)
        parent, worker = psutil.Process(os.getpid()), psutil.Process(child.pid)
        while child.poll() is None:
            try:
                peak = max(peak, parent.memory_info().rss + worker.memory_info().rss)
            except psutil.NoSuchProcess:
                break
            if peak > protocol["combined_rss_cap_bytes"]:
                stop = "RSS_CAP"
            elif time.monotonic_ns() - start >= protocol["parent_time_cap_s"] * 10**9:
                stop = "PARENT_TIME_CAP"
            if stop:
                child.kill()
                break
            time.sleep(0.025)
        code = child.wait()
    end = time.monotonic_ns()
    stdout = (HERE / "stdout.log").read_text().splitlines()
    hits = [line for line in stdout if line.startswith("HIT ")]
    exhausted = [line for line in stdout if line.startswith("EXHAUSTED ")]
    status = ("HIT_PENDING_INDEPENDENT_REPLAY" if code == 0 and len(hits) == 1
              else "EXHAUSTED" if code == 0 and len(exhausted) == 1
              else stop or "PRODUCER_FAILURE")
    result = {"status": status, "exit_code": code, "stop_reason": stop,
              "parent_wall_ns": end - start, "peak_combined_rss_bytes_sampled": peak,
              "source_line": next((s for s in stdout if s.startswith("SOURCE_PASS ")), None),
              "double_line": next((s for s in stdout if s.startswith("DOUBLE_READY ")), None),
              "hit_line": hits[0] if hits else None,
              "exhausted_line": exhausted[0] if exhausted else None,
              "stdout_sha256": sha(HERE / "stdout.log"),
              "stderr_sha256": sha(HERE / "stderr.log"),
              "protocol_sha256": sha(HERE / "protocol.json")}
    with (HERE / "result.json").open("x") as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write("\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
