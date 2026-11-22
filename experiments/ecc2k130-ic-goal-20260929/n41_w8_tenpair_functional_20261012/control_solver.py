"""Bounded solver propagation control with known N41 source and root bits."""

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
FLAGS = ("--threads=1", "--maxtime=30", "--zero-exit-status", "--verb=1", "--printsol=1")
CAP_NS = 35 * 10**9
RSS_CAP = 4 * 1024**3


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, obj):
    with path.open("x") as out:
        json.dump(obj, out, indent=2, sort_keys=True)
        out.write("\n")


def freeze():
    prior = json.loads((HERE / "control_result.json").read_text())
    assert prior["status"] == "PASS_FULL_N41_FUNCTIONAL_CONSTRUCTED_ASSIGNMENT"
    paths = (Path(__file__), HERE / "control.xcnf", HERE / "protocol.json",
             HERE / "control_result.json", HERE / "audit_result.json", SOLVER)
    save(HERE / "control_solver_protocol.json", {
        "status": "FROZEN_BEFORE_N41_FUNCTIONAL_SOLVER_CONTROL",
        "workers": 1, "cap_ns": CAP_NS,
        "rss_cap_bytes": RSS_CAP, "solver_flags": FLAGS,
        "sources": {str(path): sha(path) for path in paths}})


def run():
    frozen = json.loads((HERE / "control_solver_protocol.json").read_text())
    for path, digest in frozen["sources"].items():
        assert sha(path) == digest, path
    outpath, errpath = HERE / "control_solver.stdout", HERE / "control_solver.stderr"
    parent = psutil.Process()
    peak, stop = 0, None
    start = time.monotonic_ns()
    with outpath.open("x") as out, errpath.open("x") as err:
        child = subprocess.Popen([str(SOLVER), *FLAGS, str(HERE / "control.xcnf")],
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
            if time.monotonic_ns() - start > CAP_NS:
                stop = "WALL_CAP"
            if stop:
                child.kill()
                break
            time.sleep(0.025)
        code = child.wait()
    elapsed = time.monotonic_ns() - start
    lines = outpath.read_text(errors="replace").splitlines()
    terminals = [line for line in lines if line.startswith("s ")]
    status = ("SAT" if terminals and terminals[-1] == "s SATISFIABLE" else
              "UNSAT" if terminals and terminals[-1] == "s UNSATISFIABLE" else
              "BOUNDED_UNKNOWN")
    save(HERE / "control_solver_result.json", {
        "status": status, "terminal": terminals[-1] if terminals else None,
        "stop": stop, "exit_code": code,
        "solver_wall_ns": elapsed, "peak_combined_rss_bytes": peak,
        "restart_rows": sum(line.startswith("c rst") for line in lines),
        "stdout_sha256": sha(outpath), "stderr_sha256": sha(errpath),
        "protocol_sha256": sha(HERE / "control_solver_protocol.json")})
    print(status, elapsed / 1e9, peak)


def verify():
    frozen = json.loads((HERE / "control_solver_protocol.json").read_text())
    result = json.loads((HERE / "control_solver_result.json").read_text())
    assert result["protocol_sha256"] == sha(HERE / "control_solver_protocol.json")
    for path, digest in frozen["sources"].items():
        assert sha(path) == digest
    outpath, errpath = HERE / "control_solver.stdout", HERE / "control_solver.stderr"
    assert result["stdout_sha256"] == sha(outpath)
    assert result["stderr_sha256"] == sha(errpath)
    lines = outpath.read_text(errors="replace").splitlines()
    terminals = [line for line in lines if line.startswith("s ")]
    assert (terminals[-1] if terminals else None) == result["terminal"]
    assert sum(line.startswith("c rst") for line in lines) == result["restart_rows"]
    assert result["peak_combined_rss_bytes"] < RSS_CAP
    if result["status"] == "SAT":
        assignment = {}
        for line in lines:
            if line.startswith("v "):
                for word in line.split()[1:]:
                    literal = int(word)
                    if literal:
                        assert abs(literal) not in assignment
                        assignment[abs(literal)] = literal > 0
        cnf = xor = 0
        with (HERE / "control.xcnf").open() as stream:
            head = stream.readline().split()
            assert head[:2] == ["p", "cnf"]
            variables, rows = map(int, head[2:])
            assert set(assignment) == set(range(1, variables + 1))
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
        check = {"variables": variables, "cnf_clauses": cnf, "native_xor_rows": xor}
    else:
        assert result["status"] == "BOUNDED_UNKNOWN"
        check = None
    save(HERE / "control_solver_audit.json", {
        "status": "PASS_N41_FUNCTIONAL_SOLVER_CONTROL_AUDIT",
        "control_status": result["status"],
        "model_check": check,
        "protocol_sha256": sha(HERE / "control_solver_protocol.json"),
        "result_sha256": sha(HERE / "control_solver_result.json")})
    print("PASS_N41_FUNCTIONAL_SOLVER_CONTROL_AUDIT", result["status"])


if __name__ == "__main__":
    {"freeze": freeze, "run": run, "verify": verify}[sys.argv[1]]()
