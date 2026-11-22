"""One-worker, bounded native join with hash-checked frozen inputs."""
import hashlib
import json
import subprocess
import time
from pathlib import Path
import psutil

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = json.loads((HERE / "query_protocol.json").read_text())
    for name, digest in p["source_sha256"].items():
        assert sha(HERE / name) == digest, name
    assert p["wall_cap_seconds"] == 180 and p["rss_cap_bytes"] == 4*1024**3
    assert p["worker_count"] == 1
    stdout = HERE / "join.stdout"
    stderr = HERE / "join.stderr"
    started = time.monotonic_ns()
    reason = None
    peak = 0
    with stdout.open("x") as out, stderr.open("x") as err:
        proc = subprocess.Popen([str(HERE / "join7"), str(HERE / "input.tsv")],
                                stdout=out, stderr=err, cwd=HERE)
        child = psutil.Process(proc.pid)
        while proc.poll() is None:
            try:
                peak = max(peak, child.memory_info().rss + psutil.Process().memory_info().rss)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            if peak > p["rss_cap_bytes"]:
                reason = "RSS_CAP"
                proc.terminate()
                break
            if (time.monotonic_ns()-started)/1e9 > p["wall_cap_seconds"]:
                reason = "PARENT_TIMEOUT"
                proc.terminate()
                break
            time.sleep(0.05)
        try:
            returncode = proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            returncode = proc.wait()
    wall_ns = time.monotonic_ns()-started
    lines = stdout.read_text().splitlines()
    terminal = [line for line in lines if line.startswith(("HIT ", "COMPLETE_HITS ", "MISS_COMPLETE ", "LEFT_DONE ", "CHECK_PASS "))]
    status = "PASS_ORDINARY_RAW_RELATION" if any(x.startswith("COMPLETE_HITS ") for x in lines) and returncode == 0 else (reason or "NATIVE_ERROR")
    receipt = {"status": status, "returncode": returncode,
               "wall_ns": wall_ns, "peak_combined_rss_sample_bytes": peak,
               "termination_reason": reason, "terminal_lines": terminal,
               "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr),
               "protocol_sha256": sha(HERE / "query_protocol.json"),
               "candidate_id": None}
    (HERE / "query_result.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(status, "wall_seconds", round(wall_ns/1e9,3), "rss", peak, flush=True)


if __name__ == "__main__":
    main()
