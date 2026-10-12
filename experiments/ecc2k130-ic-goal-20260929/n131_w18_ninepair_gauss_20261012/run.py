"""Frozen Gaussian-matrix admission gate on the N131 nine-pair XCNF."""

import argparse
import gzip
import hashlib
import json
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "n131_w18_ninepair_balanced_20261012"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
FLAGS = ["--threads=1", "--maxtime=110", "--maxmatrixrows=4096",
         "--maxmatrixcols=10000", "--zero-exit-status", "--verb=1",
         "--printsol=1"]
WALL_CAP_NS = 120 * 10**9
RSS_CAP_BYTES = 4 * 1024**3


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def save(name, record):
    with (HERE / name).open("x") as stream:
        json.dump(record, stream, indent=2, sort_keys=True)
        stream.write("\n")


def freeze():
    source_protocol = json.loads((SOURCE / "protocol.json").read_text())
    control = json.loads((SOURCE / "control_result.json").read_text())
    archive = json.loads((SOURCE / "archive_receipt.json").read_text())
    assert control["variant"] == "balanced_addition_tree"
    assert archive["formulas"]["control"]["raw_sha256"] == \
        control["formula"]["xcnf_sha256"]
    assert SOLVER.is_file()
    save("protocol.json", {
        "status": "FROZEN_BEFORE_UNPINNED_CONTROL",
        "candidate_id": None,
        "curve_id": source_protocol["curve_id"],
        "workload_id": source_protocol["workload_id"],
        "source_formula": "constructed nine-pair target, all selectors free",
        "control_formula_sha256": control["formula"]["xcnf_sha256"],
        "control_formula_bytes": control["formula"]["xcnf_bytes"],
        "solver_flags": FLAGS, "wall_cap_ns": WALL_CAP_NS,
        "rss_cap_bytes": RSS_CAP_BYTES, "workers": 1,
        "source_sha256": {
            "runner": sha(Path(__file__)), "solver": sha(SOLVER),
            "balanced_protocol": sha(SOURCE / "protocol.json"),
            "balanced_control": sha(SOURCE / "control_result.json"),
            "balanced_archive": sha(SOURCE / "archive_receipt.json"),
            "control_gzip": sha(SOURCE / "control.xcnf.gz")}})


def protocol():
    frozen = json.loads((HERE / "protocol.json").read_text())
    assert frozen["source_sha256"] == {
        "runner": sha(Path(__file__)), "solver": sha(SOLVER),
        "balanced_protocol": sha(SOURCE / "protocol.json"),
        "balanced_control": sha(SOURCE / "control_result.json"),
        "balanced_archive": sha(SOURCE / "archive_receipt.json"),
        "control_gzip": sha(SOURCE / "control.xcnf.gz")}
    return frozen


def run_control():
    frozen = protocol()
    formula = HERE / "control.xcnf"
    load_start = time.monotonic_ns()
    with gzip.open(SOURCE / "control.xcnf.gz", "rb") as source, formula.open("xb") as target:
        while chunk := source.read(1024 * 1024):
            target.write(chunk)
    assert sha(formula) == frozen["control_formula_sha256"]
    assert formula.stat().st_size == frozen["control_formula_bytes"]
    load_end = time.monotonic_ns()
    stdout_path, stderr_path = HERE / "solver.stdout.txt", HERE / "solver.stderr.txt"
    parent = psutil.Process()
    peak = 0
    stop = None
    solver_start = time.monotonic_ns()
    with stdout_path.open("x") as stdout, stderr_path.open("x") as stderr:
        process = subprocess.Popen([str(SOLVER), *FLAGS, str(formula)],
                                   stdout=stdout, stderr=stderr)
        child = psutil.Process(process.pid)
        while process.poll() is None:
            try:
                combined = parent.memory_info().rss + child.memory_info().rss
            except psutil.NoSuchProcess:
                combined = parent.memory_info().rss
            peak = max(peak, combined)
            if combined > RSS_CAP_BYTES:
                stop = "RSS_CAP"
            elif time.monotonic_ns() - solver_start >= WALL_CAP_NS:
                stop = "WALL_CAP"
            if stop:
                process.kill()
                break
            time.sleep(0.05)
        code = process.wait()
    solver_end = time.monotonic_ns()
    output = stdout_path.read_text(errors="replace")
    status_lines = [line for line in output.splitlines() if line.startswith("s ")]
    status = ("BOUNDED_UNKNOWN" if stop else
              "SAT_PENDING_REPLAY" if "s SATISFIABLE" in status_lines else
              "UNSAT" if "s UNSATISFIABLE" in status_lines else
              "BOUNDED_UNKNOWN")
    save("control_result.json", {
        "status": status, "stop_reason": stop,
        "solver_exit_code": code, "solver_status_lines": status_lines,
        "formula_load_ns_excluded": load_end - load_start,
        "solver_stage_wall_ns": solver_end - solver_start,
        "peak_parent_plus_solver_rss_bytes_sampled": peak,
        "actual_restart_rows": sum(line.startswith("c rst")
                                   for line in output.splitlines()),
        "gauss_matrix_lines": [line for line in output.splitlines()
                               if line.startswith("c [matrix]") or
                               line.startswith("c [find&init matx]")],
        "stdout_sha256": sha(stdout_path),
        "stderr_sha256": sha(stderr_path),
        "protocol_sha256": sha(HERE / "protocol.json")})
    print(status, (solver_end - solver_start) / 1e9, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "control"))
    {"freeze": freeze, "control": run_control}[parser.parse_args().mode]()
