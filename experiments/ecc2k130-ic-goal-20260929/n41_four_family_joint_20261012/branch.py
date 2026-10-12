"""One checked-root branch on the exact positive four-family formula."""
import hashlib
import json
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
PARENT = GOAL / "n41_allseed_fourpair_forward_20261012"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def make():
    build = json.loads((HERE / "positive_build.json").read_text())
    chart = json.loads((PARENT / "chart.json").read_text())
    bits = chart["root_branch_bits"][4:]
    pins = [wire if bit else -wire for wire, bit in zip(build["branch_wires"], bits)]
    assert len(pins) == 3
    src, dst = HERE / "positive.xcnf", HERE / "positive_branch.xcnf"
    with src.open() as inp, dst.open("x") as out:
        header = inp.readline().split()
        assert header[:2] == ["p", "cnf"]
        variables, clauses = map(int, header[2:])
        out.write(f"p cnf {variables} {clauses + len(pins)}\n")
        for line in inp:
            out.write(line)
        for lit in pins:
            out.write(f"{lit} 0\n")
    paths = [Path(__file__), src, dst, HERE / "positive_build.json", PARENT / "chart.json", SOLVER]
    save(HERE / "branch_protocol.json", {
        "status": "FROZEN_BEFORE_POSITIVE_FAMILY_ROOT_BRANCH", "candidate_id": None,
        "pins": pins, "solver_flags": ["--threads=1", "--maxtime=40", "--zero-exit-status", "--verb=1", "--printsol=1"],
        "parent_cap_seconds": 45, "rss_cap_bytes": 4 * 1024**3,
        "sources": {str(path): sha(path) for path in paths}})


def run():
    protocol = json.loads((HERE / "branch_protocol.json").read_text())
    assert all(sha(path) == value for path, value in protocol["sources"].items())
    stdout, stderr = HERE / "positive_branch.stdout", HERE / "positive_branch.stderr"
    start = time.monotonic_ns()
    peak, stop = 0, None
    with stdout.open("x") as out, stderr.open("x") as err:
        child = subprocess.Popen([str(SOLVER), *protocol["solver_flags"],
                                  str(HERE / "positive_branch.xcnf")], stdout=out, stderr=err)
        proc = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                peak = max(peak, proc.memory_info().rss)
            except psutil.NoSuchProcess:
                pass
            if peak > protocol["rss_cap_bytes"]:
                stop = "RSS_CAP"
            if time.monotonic_ns() - start > protocol["parent_cap_seconds"] * 10**9:
                stop = "WALL_CAP"
            if stop:
                child.kill()
                break
            time.sleep(.025)
        code = child.wait()
    terminals = [line for line in stdout.read_text(errors="replace").splitlines()
                 if line.startswith("s ")]
    terminal = terminals[-1] if terminals else None
    status = ("SAT_PENDING_REPLAY" if terminal == "s SATISFIABLE" else
              "UNSAT" if terminal == "s UNSATISFIABLE" else
              "BOUNDED_UNKNOWN" if stop or terminal in (None, "s INDETERMINATE") else
              "PRODUCER_FAILURE")
    save(HERE / "positive_branch_result.json", {
        "status": status, "terminal": terminal, "stop_reason": stop,
        "exit_code": code, "wall_ns": time.monotonic_ns() - start,
        "peak_solver_rss_bytes": peak, "stdout_sha256": sha(stdout),
        "stderr_sha256": sha(stderr), "protocol_sha256": sha(HERE / "branch_protocol.json")})
    print(status, flush=True)


if __name__ == "__main__":
    import sys
    {"make": make, "run": run}[sys.argv[1]]()
