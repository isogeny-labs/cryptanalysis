"""Parent-capped planted control for the frozen three-pair binary."""
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
PAIRS = HERE.parent / "n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = json.loads((HERE / "control_protocol.json").read_text())
    files = {"runner": HERE / "run_control.py", "binary": HERE / "triple",
             "fixture": HERE / "fixture.json", "pairs": PAIRS}
    assert p["status"] == "FROZEN_BEFORE_CONSTRUCTED_QUERY"
    assert p["sha256"] == {key: sha(path) for key, path in files.items()}
    fixture = json.loads((HERE / "fixture.json").read_text())
    x, y = fixture["projected_target"]
    cmd = [str(HERE / "triple"), str(PAIRS), str(x), str(y), "6", "1", "10"]
    started = time.monotonic_ns()
    peak, stop = 0, None
    with (HERE / "control.stdout").open("x") as out, (HERE / "control.stderr").open("x") as err:
        child = subprocess.Popen(cmd, stdout=out, stderr=err)
        owner, worker = psutil.Process(os.getpid()), psutil.Process(child.pid)
        while child.poll() is None:
            try:
                peak = max(peak, owner.memory_info().rss + worker.memory_info().rss)
            except psutil.NoSuchProcess:
                break
            if peak > 4 * 1024**3:
                stop = "RSS_CAP"
            elif time.monotonic_ns() - started >= 60 * 10**9:
                stop = "PARENT_TIME_CAP"
            if stop:
                child.kill()
                break
            time.sleep(0.025)
        code = child.wait()
    ended = time.monotonic_ns()
    lines = (HERE / "control.stdout").read_text().splitlines()
    hits = [line for line in lines if line.startswith("HIT ")]
    status = ("HIT_PENDING_INDEPENDENT_REPLAY" if code == 0 and len(hits) == 1
              else stop or "CONTROL_FAILURE")
    result = {"status": status, "exit_code": code, "stop_reason": stop,
              "parent_wall_ns": ended - started, "peak_combined_rss_bytes_sampled": peak,
              "hit_line": hits[0] if hits else None,
              "stdout_sha256": sha(HERE / "control.stdout"),
              "stderr_sha256": sha(HERE / "control.stderr"),
              "protocol_sha256": sha(HERE / "control_protocol.json")}
    with (HERE / "control_result.json").open("x") as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write("\n")
    print(status, result["hit_line"], flush=True)


if __name__ == "__main__":
    main()
