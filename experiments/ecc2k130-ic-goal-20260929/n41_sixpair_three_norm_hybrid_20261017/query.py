"""Run the unpinned N41 public query with one bounded CryptoMiniSat worker."""
import hashlib
import json
import os
import psutil
import signal
import subprocess
import time
from pathlib import Path

D = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((D / "query_protocol.json").read_text())
    assert sha(D / "query.py") == protocol["runner_sha256"]
    for name, digest in protocol["sources"].items():
        assert sha(D / name) == digest, name
    solver = Path(protocol["solver_path"])
    assert sha(solver) == protocol["solver_sha256"]
    command = [str(solver), *protocol["solver_flags"], str(D / "public.xcnf")]
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
            if peak > protocol["rss_cap_bytes"]:
                stop = "RSS_CAP"
            elif time.monotonic_ns() - start > protocol["parent_wall_cap_s"] * 10**9:
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
              else "BOUNDED_UNKNOWN" if stop or any("INDETERMINATE" in line for line in terminal)
              else "PRODUCER_FAILURE")
    result = {"status": status, "command": command,
              "query_protocol_sha256": sha(D / "query_protocol.json"),
              "exit_code": child.returncode,
              "wall_ns": time.monotonic_ns() - start,
              "stop_reason": stop, "terminal_lines": terminal,
              "monitor_degraded": degraded,
              "sampled_peak_combined_rss_bytes": peak,
              "stdout_sha256": sha(D / "solver.stdout"),
              "stderr_sha256": sha(D / "solver.stderr")}
    (D / "query_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in (
        "status", "wall_ns", "stop_reason", "sampled_peak_combined_rss_bytes",
        "terminal_lines")}, sort_keys=True))


if __name__ == "__main__":
    main()
