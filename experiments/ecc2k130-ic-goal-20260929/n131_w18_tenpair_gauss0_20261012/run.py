"""Run one frozen XCNF under CryptoMiniSat without Gaussian matrices."""

import argparse
import gzip
import hashlib
import json
import subprocess
import time
from pathlib import Path

import psutil


HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n131_w18_tenpair_binary_frob_20261012"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(mode):
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert protocol["status"] == "FROZEN_N131_TENPAIR_GAUSS0_SOLVER_VARIANT"
    for name, path in {
        "runner": HERE / "run.py",
        "smoke_source": HERE / "smoke.py",
        "smoke_result": HERE / "smoke_result.json",
        "parent_protocol": PARENT / "protocol.json",
        "parent_control": PARENT / "control_result.json",
        "parent_query": PARENT / "query_result.json",
        "parent_archive": PARENT / "archive_receipt.json",
        "control_formula_gzip": PARENT / "control.xcnf.gz",
        "ordinary_formula_gzip": PARENT / "ordinary.xcnf.gz",
        "solver": SOLVER.resolve(),
    }.items():
        assert sha(path) == protocol["sha256"][name]
    assert mode in ("control", "ordinary")
    assert not (HERE / (mode + "_result.json")).exists()
    compressed = PARENT / (mode + ".xcnf.gz")
    formula = HERE / (mode + ".xcnf")
    load_start = time.monotonic_ns()
    with gzip.open(compressed, "rb") as src, formula.open("xb") as dst:
        while block := src.read(1024 * 1024):
            dst.write(block)
    load_end = time.monotonic_ns()
    assert sha(formula) == protocol["source_formula_sha256"][mode]
    seconds = (protocol["control_solver_seconds"] if mode == "control"
               else protocol["ordinary_solver_seconds"])
    flags = [*protocol["solver_flags_common"], "--maxnummatrices=0",
             "--maxtime=%d" % seconds]
    parent = psutil.Process()
    outpath = HERE / (mode + ".stdout.txt")
    errpath = HERE / (mode + ".stderr.txt")
    peak, stop = 0, None
    start = time.monotonic_ns()
    with outpath.open("x") as stdout, errpath.open("x") as stderr:
        process = subprocess.Popen([str(SOLVER), *flags, str(formula)],
                                   stdout=stdout, stderr=stderr)
        child = psutil.Process(process.pid)
        while process.poll() is None:
            try:
                combined = parent.memory_info().rss + child.memory_info().rss
            except psutil.NoSuchProcess:
                combined = parent.memory_info().rss
            peak = max(peak, combined)
            if combined > protocol["combined_rss_cap_bytes"]:
                stop = "RSS_CAP"
            elif time.monotonic_ns() - start >= (protocol["ordinary_total_wall_cap_seconds"]
                                                 if mode == "ordinary" else 75) * 10**9:
                stop = "TOTAL_WALL_CAP"
            if stop:
                process.kill()
                break
            time.sleep(0.05)
        code = process.wait()
    end = time.monotonic_ns()
    output = outpath.read_text(errors="replace")
    lines = [line for line in output.splitlines() if line.startswith("s ")]
    status = ("BOUNDED_UNKNOWN" if stop else
              "SAT_PENDING_GROUP_REPLAY" if "s SATISFIABLE" in lines else
              "UNSAT" if "s UNSATISFIABLE" in lines else
              "BOUNDED_UNKNOWN")
    result = {
        "status": status,
        "mode": mode,
        "candidate_id": None,
        "formula_sha256": sha(formula),
        "formula_decompression_ns_excluded": load_end - load_start,
        "solver_wall_ns": end - start,
        "peak_combined_rss_bytes_sampled": peak,
        "stop_reason": stop,
        "solver_exit_code": code,
        "solver_flags": flags,
        "worker_count": 1,
        "status_lines": lines,
        "actual_restart_rows": sum(line.startswith("c rst") for line in output.splitlines()),
        "matrix_disable_diagnostics": sum(line.startswith("c TODO disable matrix") for line in output.splitlines()),
        "stdout_sha256": sha(outpath),
        "stderr_sha256": sha(errpath),
        "protocol_sha256": sha(HERE / "protocol.json"),
    }
    (HERE / (mode + "_result.json")).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(mode, status, (end - start) / 1e9, peak, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("control", "ordinary"))
    run(parser.parse_args().mode)
