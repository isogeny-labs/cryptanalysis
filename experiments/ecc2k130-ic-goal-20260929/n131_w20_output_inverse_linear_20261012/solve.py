"""Frozen bounded search for the fresh W20 inverse-output linearized target."""

import argparse
import hashlib
import json
import resource
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
CMS = Path("/opt/homebrew/bin/cryptominisat5")
FLAGS = ["--threads=1", "--maxtime=600", "--zero-exit-status",
         "--verb=1", "--printsol=1"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open("x") as out:
        json.dump(value, out, sort_keys=True, indent=2)
        out.write("\n")


def paths():
    return {"script": Path(__file__), "formula": HERE / "ordinary.xcnf",
            "build": HERE / "ordinary_build_result.json",
            "protocol": HERE / "protocol.json", "solver": CMS.resolve()}


def freeze():
    build = json.loads((HERE / "ordinary_build_result.json").read_text())
    assert build["status"] == "PASS_W20_OUTPUT_LINEAR_ORDINARY_BUILD"
    assert build["formula"]["xcnf_sha256"] == sha(HERE / "ordinary.xcnf")
    save("solver_protocol.json", {
        "status": "FROZEN_BEFORE_W20_OUTPUT_LINEAR_ORDINARY_SEARCH",
        "candidate_id": None, "workload_id": build["workload_id"],
        "raw_preimage_index": 0, "flags": FLAGS,
        "parent_wall_cap_seconds": 615, "rss_cap_bytes": 4 * 1024**3,
        "source_sha256": {name: sha(path) for name, path in paths().items()}})
    print("FROZEN_W20_OUTPUT_LINEAR_SOLVER", flush=True)


def query():
    protocol = json.loads((HERE / "solver_protocol.json").read_text())
    assert protocol["status"] == "FROZEN_BEFORE_W20_OUTPUT_LINEAR_ORDINARY_SEARCH"
    assert protocol["source_sha256"] == {name: sha(path) for name, path in paths().items()}
    assert protocol["flags"] == FLAGS
    cmd = [str(CMS), *FLAGS, str(HERE / "ordinary.xcnf")]
    stdout_path, stderr_path = HERE / "solver.stdout.txt", HERE / "solver.stderr.txt"
    start = time.monotonic_ns()
    peak, cpu_seconds, stop_reason = 0, 0.0, None
    with stdout_path.open("x") as stdout, stderr_path.open("x") as stderr:
        process = subprocess.Popen(cmd, stdout=stdout, stderr=stderr)
        child = psutil.Process(process.pid)
        while process.poll() is None:
            try:
                peak = max(peak, child.memory_info().rss)
                cpu = child.cpu_times()
                cpu_seconds = max(cpu_seconds, cpu.user + cpu.system)
            except psutil.NoSuchProcess:
                break
            if peak > protocol["rss_cap_bytes"]:
                stop_reason = "RSS_CAP"
                process.kill()
                break
            if time.monotonic_ns() - start > protocol["parent_wall_cap_seconds"] * 10**9:
                stop_reason = "PARENT_TIMEOUT"
                process.kill()
                break
            time.sleep(0.05)
        code = process.wait()
    end = time.monotonic_ns()
    output = stdout_path.read_text(errors="replace")
    status = ("BOUNDED_UNKNOWN" if stop_reason else
              "SAT_PENDING_INDEPENDENT_REPLAY" if "s SATISFIABLE" in output else
              "UNSAT" if "s UNSATISFIABLE" in output else "BOUNDED_UNKNOWN")
    save("solver_result.json", {
        "status": status, "candidate_id": None,
        "workload_id": protocol["workload_id"], "raw_preimage_index": 0,
        "command": cmd, "exit_code": code,
        "search_wall_ns": end-start, "cpu_seconds_sampled": cpu_seconds,
        "peak_child_rss_bytes_sampled": peak,
        "peak_children_rss_raw": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
        "stop_reason": stop_reason,
        "status_lines": [line for line in output.splitlines() if line.startswith("s ")],
        "stdout_sha256": sha(stdout_path), "stderr_sha256": sha(stderr_path),
        "solver_protocol_sha256": sha(HERE / "solver_protocol.json")})
    print(json.dumps({"status": status, "search_wall_ns": end-start,
                      "cpu_seconds_sampled": cpu_seconds}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "query"))
    {"freeze": freeze, "query": query}[parser.parse_args().mode]()
