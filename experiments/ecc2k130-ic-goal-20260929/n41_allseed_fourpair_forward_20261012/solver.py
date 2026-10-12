"""Frozen one-worker public query with complete XCNF model replay."""

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
FLAGS = ("--threads=1", "--maxtime=180", "--zero-exit-status", "--verb=1", "--printsol=1")
WALL_NS = 190 * 10**9
RSS_CAP = 4 * 1024**3


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, obj):
    with path.open("x") as stream:
        json.dump(obj, stream, sort_keys=True, indent=2)
        stream.write("\n")


def freeze():
    paths = (Path(__file__), HERE / "build.py", HERE / "build_result.json",
             HERE / "chart.json", HERE / "audit_sage.py", HERE / "audit_result.json",
             HERE / "audit_protocol.json", HERE / "sage_runtime_info.json",
             HERE / "n41_public.xcnf", SOLVER,
             GOAL / "n131_w18_allseed_fourpair_20261012/fourpair_v2.py",
             GOAL / "n41_w8_tenpair_functional_20261012/build.py",
             GOAL / "n41_w8_tenpair_functional_20261012/run.py")
    save(HERE / "solver_protocol.json", {
        "status": "FROZEN_BEFORE_UNPINNED_N41_PUBLIC_QUERY", "candidate_id": None,
        "workers": 1, "wall_cap_ns": WALL_NS, "rss_cap_bytes": RSS_CAP,
        "solver_flags": FLAGS, "sources": {str(path): sha(path) for path in paths}})


def run():
    protocol = json.loads((HERE / "solver_protocol.json").read_text())
    for path, digest in protocol["sources"].items():
        assert sha(path) == digest, path
    stdout = HERE / "solver.stdout"
    stderr = HERE / "solver.stderr"
    parent = psutil.Process()
    peak = 0
    stop = None
    start = time.monotonic_ns()
    with stdout.open("x") as out, stderr.open("x") as err:
        child = subprocess.Popen([str(SOLVER), *FLAGS, str(HERE / "n41_public.xcnf")],
                                 stdout=out, stderr=err)
        proc = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                rss = parent.memory_info().rss + proc.memory_info().rss
                peak = max(peak, rss)
                if rss > RSS_CAP:
                    stop = "RSS_CAP"
            except psutil.NoSuchProcess:
                pass
            if time.monotonic_ns() - start > WALL_NS:
                stop = "WALL_CAP"
            if stop:
                child.kill()
                break
            time.sleep(0.025)
        code = child.wait()
    elapsed = time.monotonic_ns() - start
    lines = stdout.read_text(errors="replace").splitlines()
    terminals = [line for line in lines if line.startswith("s ")]
    terminal = terminals[-1] if terminals else None
    status = ("SAT_PENDING_MODEL_AND_GROUP_REPLAY" if terminal == "s SATISFIABLE" else
              "UNSAT" if terminal == "s UNSATISFIABLE" else "BOUNDED_UNKNOWN")
    save(HERE / "solver_result.json", {
        "status": status, "terminal": terminal, "stop_reason": stop, "exit_code": code,
        "wall_ns": elapsed, "peak_combined_rss_bytes": peak,
        "restart_rows": sum(line.startswith("c rst") for line in lines),
        "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr),
        "protocol_sha256": sha(HERE / "solver_protocol.json")})
    print(status, round(elapsed / 1e9, 3), peak, flush=True)


def verify():
    protocol = json.loads((HERE / "solver_protocol.json").read_text())
    result = json.loads((HERE / "solver_result.json").read_text())
    assert result["protocol_sha256"] == sha(HERE / "solver_protocol.json")
    for path, digest in protocol["sources"].items():
        assert sha(path) == digest, path
    stdout, stderr = HERE / "solver.stdout", HERE / "solver.stderr"
    assert result["stdout_sha256"] == sha(stdout)
    assert result["stderr_sha256"] == sha(stderr)
    lines = stdout.read_text(errors="replace").splitlines()
    terminals = [line for line in lines if line.startswith("s ")]
    assert (terminals[-1] if terminals else None) == result["terminal"]
    model = None
    if result["status"] == "SAT_PENDING_MODEL_AND_GROUP_REPLAY":
        assignment = {}
        for line in lines:
            if line.startswith("v "):
                for word in line.split()[1:]:
                    literal = int(word)
                    if literal:
                        assert abs(literal) not in assignment
                        assignment[abs(literal)] = literal > 0
        with (HERE / "n41_public.xcnf").open() as stream:
            head = stream.readline().split()
            assert head[:2] == ["p", "cnf"]
            variables, rows = map(int, head[2:])
            assert set(assignment) == set(range(1, variables + 1))
            cnf = xor = 0
            for line in stream:
                parts = line.split()
                is_xor = parts[0] == "x"
                lits = list(map(int, parts[1 if is_xor else 0:-1]))
                assert parts[-1] == "0" and lits
                values = [assignment[abs(lit)] == (lit > 0) for lit in lits]
                if is_xor:
                    assert sum(values) & 1
                    xor += 1
                else:
                    assert any(values)
                    cnf += 1
        assert cnf + xor == rows
        model = {"variables": variables, "cnf_clauses": cnf, "native_xor_rows": xor}
    save(HERE / "solver_audit.json", {
        "status": "PASS_FROZEN_N41_PUBLIC_SOLVER_RECEIPT_AUDIT",
        "solver_status": result["status"], "model_check": model,
        "result_sha256": sha(HERE / "solver_result.json")})
    print("PASS_FROZEN_N41_PUBLIC_SOLVER_RECEIPT_AUDIT", result["status"])


if __name__ == "__main__":
    {"freeze": freeze, "run": run, "verify": verify}[sys.argv[1]]()
