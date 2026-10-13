"""Run the frozen one-worker unpinned N41 public-point query."""
import hashlib
import json
import resource
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "query_protocol.json").read_text())
    paths = {"runner": HERE / "run.py", "formula": HERE / "public.xcnf",
             "build_result": HERE / "build_result.json", "solver": Path(protocol["solver_path"])}
    assert {key: sha(path) for key, path in paths.items()} == protocol["sha256"]
    assert not (HERE / "query_result.json").exists()
    start = time.monotonic_ns()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    parent = psutil.Process()
    peak = 0
    stop = None
    with (HERE / "solver.stdout").open("x") as out, (HERE / "solver.stderr").open("x") as err:
        child = subprocess.Popen([protocol["solver_path"], *protocol["solver_flags"],
                                  str(HERE / "public.xcnf")], stdout=out, stderr=err)
        proc = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                rss = parent.memory_info().rss + proc.memory_info().rss
            except psutil.NoSuchProcess:
                rss = parent.memory_info().rss
            peak = max(peak, rss)
            if rss > protocol["rss_cap_bytes"]:
                stop = "RSS_CAP"
            elif time.monotonic_ns() - start >= protocol["parent_wall_cap_seconds"] * 10**9:
                stop = "WALL_CAP"
            if stop:
                child.kill()
                break
            time.sleep(0.05)
        code = child.wait()
    end = time.monotonic_ns()
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    lines = (HERE / "solver.stdout").read_text().splitlines()
    terminal = [line for line in lines if line.startswith("s ")]
    status = ("BOUNDED_UNKNOWN" if stop or "s INDETERMINATE" in terminal else
              "SAT_PENDING_MODEL_AUDIT" if "s SATISFIABLE" in terminal else
              "UNSAT" if "s UNSATISFIABLE" in terminal else "PRODUCER_FAILURE")
    result = {"status": status, "stop_reason": stop, "exit_code": code,
              "worker_count": 1, "solver_terminal_lines": terminal,
              "parent_wall_ns": end - start, "peak_combined_rss_bytes_sampled": peak,
              "child_user_seconds": after.ru_utime - before.ru_utime,
              "child_system_seconds": after.ru_stime - before.ru_stime,
              "stdout_sha256": sha(HERE / "solver.stdout"),
              "stderr_sha256": sha(HERE / "solver.stderr"),
              "protocol_sha256": sha(HERE / "query_protocol.json")}
    (HERE / "query_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(status, (end - start) / 1e9, peak, flush=True)


if __name__ == "__main__":
    main()
