"""Paired bounded CryptoMiniSat runs on the frozen N131 terminal circuit."""

import gzip
import hashlib
import json
import os
import resource
import signal
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / "n131_w18_terminal_fiber_20261011"
ARCHIVE = ROOT / "archive_receipt.json"
GZIP = ROOT / "ordinary.xcnf.gz"
BINARY = Path("/opt/homebrew/bin/cryptominisat5")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_case(name, flags, circuit, protocol):
    stdout_path = HERE / f"{name}.stdout.txt"
    stderr_path = HERE / f"{name}.stderr.txt"
    argv = [str(BINARY), "--threads=1", "--maxtime=90", "--zero-exit-status",
            "--verb=1", "--printsol=1", *flags, str(circuit)]
    start = time.monotonic_ns()
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        process = subprocess.Popen(argv, stdout=stdout, stderr=stderr,
                                   start_new_session=True)
        monitor = psutil.Process(process.pid)
        stop = None
        sampled_peak = 0
        while process.poll() is None:
            try:
                sampled_peak = max(sampled_peak, monitor.memory_info().rss)
            except psutil.NoSuchProcess:
                break
            if sampled_peak >= protocol["rss_guard_bytes"]:
                stop = "RSS_GUARD"
                break
            if time.monotonic_ns() - start >= protocol["parent_cap_seconds"] * 10**9:
                stop = "PARENT_WALL_CAP"
                break
            time.sleep(0.05)
        if stop:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                code = process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                code = process.wait()
        else:
            code = process.wait()
    wall = time.monotonic_ns() - start
    output = stdout_path.read_text(errors="replace")
    sat = "s SATISFIABLE" in output
    unsat = "s UNSATISFIABLE" in output
    assert not (sat and unsat)
    peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    status = ("SAT" if sat else "UNSAT" if unsat else
              "BOUNDED_UNKNOWN" if stop or code == 0 else "PRODUCER_FAILURE")
    return {
        "status": status, "stop_reason": stop, "exit_code": code,
        "argv": argv, "wall_ns": wall, "peak_child_rss_bytes": peak,
        "max_sampled_rss_bytes": sampled_peak,
        "restart_rows": sum(line.startswith("c rst ") for line in output.splitlines()),
        "matrix_lines": [line for line in output.splitlines()
                         if "[matrix]" in line or "[gauss]" in line],
        "solver_started": "c CryptoMiniSat version" in output,
        "stdout_sha256": sha(stdout_path), "stderr_sha256": sha(stderr_path),
        "stderr_bytes": stderr_path.stat().st_size,
    }


def main():
    protocol = json.loads((HERE / "protocol_v2.json").read_text())
    assert protocol["status"] == "FROZEN_SELECTIVE_GAUSS_PAIR_V2"
    assert protocol["sha256"] == {
        "source": sha(Path(__file__)), "archive": sha(ARCHIVE),
        "gzip": sha(GZIP), "solver": sha(BINARY)}
    archive = json.loads(ARCHIVE.read_text())["ordinary"]
    assert archive["gzip_sha256"] == sha(GZIP)
    raw = gzip.decompress(GZIP.read_bytes())
    assert len(raw) == archive["raw_bytes"]
    assert hashlib.sha256(raw).hexdigest() == archive["raw_sha256"]
    circuit = HERE / "ordinary.xcnf"
    circuit.write_bytes(raw)
    rows = {}
    for name, flags in (
        ("default", []),
        ("selective", ["--maxmatrixrows=4000", "--maxmatrixcols=10000"]),
    ):
        rows[name] = run_case(name, flags, circuit, protocol)
        assert rows[name]["solver_started"]
        assert rows[name]["peak_child_rss_bytes"] < protocol["rss_cap_bytes"]
        assert rows[name]["max_sampled_rss_bytes"] < protocol["rss_cap_bytes"]
    circuit.unlink()
    result = {
        "status": "COMPLETE", "candidate_id": None,
        "curve_id": protocol["curve_id"],
        "raw_xcnf_sha256": archive["raw_sha256"],
        "run_order": ["default", "selective"], "cases": rows,
        "protocol_sha256": sha(HERE / "protocol_v2.json"),
        "source_sha256": sha(Path(__file__)),
    }
    (HERE / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "cases": {
        name: {k: row[k] for k in ("status", "wall_ns", "peak_child_rss_bytes", "restart_rows")}
        for name, row in rows.items()}}))


if __name__ == "__main__":
    main()
