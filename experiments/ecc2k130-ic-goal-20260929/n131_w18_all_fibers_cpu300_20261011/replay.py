"""CPU-limited replay of the frozen all-fiber ordinary-point XCNF."""

import gzip
import hashlib
import json
import os
import resource
import signal
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n131_w18_all_fibers_inverse_20261011"
ARCHIVE = PARENT / "ordinary.xcnf.gz"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
CPU_SOFT = 300
CPU_HARD = 305
WALL_CAP = 4500
RSS_CAP = 4 * 1024**3
FLAGS = ["--threads=1", "--maxtime=4500", "--zero-exit-status",
         "--verb=1", "--printsol=1"]


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save(path, data):
    with path.open("x") as stream:
        json.dump(data, stream, sort_keys=True, indent=2)
        stream.write("\n")


def expected():
    query = json.loads((PARENT / "query_result.json").read_text())
    receipt = json.loads((PARENT / "archive_receipt.json").read_text())
    assert query["status"] == "BOUNDED_UNKNOWN"
    assert receipt["status"] == "PASS_ARCHIVE_BYTE_REPLAY"
    assert query["formula"]["xcnf_sha256"] == receipt["ordinary"]["raw_sha256"]
    assert sha(ARCHIVE) == receipt["ordinary"]["gzip_sha256"]
    return query, receipt


def freeze():
    query, receipt = expected()
    assert SOLVER.is_file()
    save(HERE / "protocol.json", {
        "status": "FROZEN_CPU300_REPLAY",
        "candidate_id": None,
        "curve_id": query["curve_id"],
        "workload_id": query["workload_id"],
        "public_target": query["public_target"],
        "parent_query_sha256": sha(PARENT / "query_result.json"),
        "parent_protocol_sha256": sha(PARENT / "protocol.json"),
        "archive_sha256": sha(ARCHIVE),
        "formula_sha256": receipt["ordinary"]["raw_sha256"],
        "formula_bytes": receipt["ordinary"]["raw_bytes"],
        "solver_path": str(SOLVER),
        "solver_sha256": sha(SOLVER),
        "runner_sha256": sha(__file__),
        "solver_flags": FLAGS,
        "worker_count": 1,
        "solver_cpu_soft_limit_seconds": CPU_SOFT,
        "solver_cpu_hard_limit_seconds": CPU_HARD,
        "outer_wall_cap_seconds": WALL_CAP,
        "combined_rss_cap_bytes": RSS_CAP,
        "accounting": "solver-stage replay; original target-dependent construction is reported separately",
    })
    print("FROZEN_CPU300_REPLAY", flush=True)


def unpack():
    _, receipt = expected()
    path = HERE / "ordinary.xcnf"
    digest = hashlib.sha256()
    size = 0
    with gzip.open(ARCHIVE, "rb") as src, path.open("xb") as dst:
        for chunk in iter(lambda: src.read(1 << 20), b""):
            dst.write(chunk)
            digest.update(chunk)
            size += len(chunk)
    assert size == receipt["ordinary"]["raw_bytes"]
    assert digest.hexdigest() == receipt["ordinary"]["raw_sha256"]
    return path


def limits():
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_SOFT, CPU_HARD))


def replay():
    protocol = json.loads((HERE / "protocol.json").read_text())
    query, receipt = expected()
    assert protocol["status"] == "FROZEN_CPU300_REPLAY"
    assert protocol["parent_query_sha256"] == sha(PARENT / "query_result.json")
    assert protocol["parent_protocol_sha256"] == sha(PARENT / "protocol.json")
    assert protocol["formula_sha256"] == receipt["ordinary"]["raw_sha256"]
    assert protocol["solver_sha256"] == sha(SOLVER)
    assert protocol["runner_sha256"] == sha(__file__)
    formula = unpack()
    started = time.monotonic_ns()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    stdout_path, stderr_path = HERE / "solver.stdout.txt", HERE / "solver.stderr.txt"
    parent = psutil.Process()
    peak = 0
    cpu_sample = 0.0
    stop = None
    with stdout_path.open("x") as stdout, stderr_path.open("x") as stderr:
        child = subprocess.Popen([str(SOLVER), *FLAGS, str(formula)],
                                 stdout=stdout, stderr=stderr, preexec_fn=limits)
        process = psutil.Process(child.pid)
        print(json.dumps({"solver_pid": child.pid, "formula_sha256":
                          protocol["formula_sha256"]}), flush=True)
        while child.poll() is None:
            try:
                cpu = process.cpu_times()
                cpu_sample = max(cpu_sample, cpu.user + cpu.system)
                combined = parent.memory_info().rss + process.memory_info().rss
                peak = max(peak, combined)
            except psutil.NoSuchProcess:
                pass
            if peak > RSS_CAP:
                stop = "RSS_CAP"
            elif time.monotonic_ns() - started >= WALL_CAP * 10**9:
                stop = "OUTER_WALL_CAP"
            if stop:
                child.kill()
                break
            time.sleep(0.2)
        code = child.wait()
    ended = time.monotonic_ns()
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu_rusage = (after.ru_utime + after.ru_stime -
                  before.ru_utime - before.ru_stime)
    output = stdout_path.read_text(errors="replace")
    status_lines = [line for line in output.splitlines() if line.startswith("s ")]
    status = ("SAT_PENDING_GROUP_REPLAY" if "s SATISFIABLE" in status_lines else
              "UNSAT" if "s UNSATISFIABLE" in status_lines else "BOUNDED_UNKNOWN")
    if status == "BOUNDED_UNKNOWN" and stop is None:
        stop = ("CPU_SOFT_LIMIT" if code == -signal.SIGXCPU else
                "CPU_HARD_LIMIT" if code == -signal.SIGKILL and cpu_rusage >= CPU_SOFT else
                "SOLVER_EXIT_WITHOUT_STATUS")
    save(HERE / "replay_result.json", {
        "status": status, "candidate_id": None,
        "curve_id": query["curve_id"], "workload_id": query["workload_id"],
        "public_target": query["public_target"],
        "protocol_sha256": sha(HERE / "protocol.json"),
        "formula_sha256": sha(formula),
        "solver_sha256": sha(SOLVER),
        "solver_flags": FLAGS,
        "worker_count": 1,
        "solver_stage_wall_ns": ended - started,
        "solver_cpu_seconds_rusage": cpu_rusage,
        "solver_cpu_seconds_sampled": cpu_sample,
        "peak_combined_rss_bytes_sampled": peak,
        "solver_exit_code": code, "stop_reason": stop,
        "status_lines": status_lines,
        "restart_rows": sum(line.startswith("c rst") for line in output.splitlines()),
        "stdout_sha256": sha(stdout_path), "stderr_sha256": sha(stderr_path),
        "outer_wall_cap_seconds": WALL_CAP,
        "solver_cpu_soft_limit_seconds": CPU_SOFT,
        "combined_rss_cap_bytes": RSS_CAP,
    })
    formula.unlink()
    print(json.dumps({"status": status, "stop_reason": stop,
                      "solver_cpu_seconds": cpu_rusage,
                      "solver_stage_wall_seconds": (ended-started)/1e9}), flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {"freeze", "replay"}:
        raise SystemExit("usage: replay.py freeze|replay")
    {"freeze": freeze, "replay": replay}[sys.argv[1]]()
