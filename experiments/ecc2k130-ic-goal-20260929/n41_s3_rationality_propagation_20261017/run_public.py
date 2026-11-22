"""Run one unpinned public S3 query under the matched N41 solver envelope."""
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
    p = json.loads((D / "query_protocol.json").read_text())
    assert sha(D / "run_public.py") == p["runner_sha256"]
    for name, digest in p["sources"].items():
        assert sha(D / name) == digest, name
    assert sha(Path(p["solver_path"])) == p["solver_sha256"]
    command = [p["solver_path"], *p["solver_flags"], str(D / "public.xcnf")]
    parent = psutil.Process(os.getpid())
    start = time.monotonic_ns()
    peak = 0
    degraded = False
    stop = None
    with (D / "solver.stdout").open("x") as out, (D / "solver.stderr").open("x") as err:
        child = subprocess.Popen(command, stdout=out, stderr=err, start_new_session=True)
        process = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                peak = max(peak, parent.memory_info().rss + process.memory_info().rss)
            except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
                if child.poll() is None:
                    degraded = True
            if peak > p["rss_cap_bytes"]:
                stop = "RSS_CAP"
            elif time.monotonic_ns() - start > p["parent_wall_cap_s"] * 10**9:
                stop = "PARENT_WALL_CAP"
            if stop:
                os.killpg(child.pid, signal.SIGTERM)
                break
            time.sleep(0.05)
        child.wait()
    stdout = (D / "solver.stdout").read_text(errors="replace")
    terminal = [line for line in stdout.splitlines() if line.startswith("s ")]
    status = ("SAT_PENDING_REPLAY" if "s SATISFIABLE" in terminal
              else "UNSAT_UNCERTIFIED" if "s UNSATISFIABLE" in terminal
              else "BOUNDED_UNKNOWN" if stop or any("INDETERMINATE" in x for x in terminal)
              else "PRODUCER_FAILURE")
    result = {"status": status, "exit_code": child.returncode,
              "command": command, "wall_ns": time.monotonic_ns() - start,
              "stop_reason": stop, "terminal_lines": terminal,
              "sampled_peak_combined_rss_bytes": peak,
              "monitor_degraded": degraded,
              "query_protocol_sha256": sha(D / "query_protocol.json"),
              "stdout_sha256": sha(D / "solver.stdout"),
              "stderr_sha256": sha(D / "solver.stderr")}
    (D / "query_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in (
        "status", "wall_ns", "sampled_peak_combined_rss_bytes", "terminal_lines")},
        sort_keys=True))


if __name__ == "__main__":
    main()
