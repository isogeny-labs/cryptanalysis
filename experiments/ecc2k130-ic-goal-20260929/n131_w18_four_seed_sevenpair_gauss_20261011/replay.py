"""Frozen Gaussian-matrix replay of the same N131 ordinary XCNF."""

import gzip
import hashlib
import json
import resource
import signal
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "n131_w18_four_seed_sevenpair_ordinary_20261011"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
FLAGS = ["--threads=1", "--maxtime=4500", "--zero-exit-status",
         "--verb=1", "--printsol=1", "--maxmatrixrows=4000",
         "--maxmatrixcols=10000", "--maxnummatrices=7"]
CPU_SOFT, CPU_HARD, WALL_CAP = 300, 305, 4500
RSS_CAP = 4 * 1024**3


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save(name, record):
    with (HERE / name).open("x") as stream:
        json.dump(record, stream, indent=2, sort_keys=True)
        stream.write("\n")


def freeze():
    base = json.loads((BASE / "protocol.json").read_text())
    formula = BASE / "ordinary.xcnf"
    assert base["status"] == "FROZEN_N131_SEVENPAIR_AFFINE_ORDINARY_QUERY"
    assert formula.is_file()
    save("protocol.json", {
        "status": "FROZEN_N131_SEVENPAIR_GAUSS_REPLAY",
        "scope": "same public-point XCNF; solver-stage diagnostic only",
        "candidate_id": None,
        "curve_id": base["curve_id"],
        "workload_id": base["workload_id"],
        "public_target": base["public_target"],
        "base_protocol_sha256": sha(BASE / "protocol.json"),
        "base_formula_sha256": sha(formula),
        "base_formula_bytes": formula.stat().st_size,
        "runner_sha256": sha(Path(__file__)),
        "solver_path": str(SOLVER),
        "solver_sha256": sha(SOLVER),
        "solver_flags": FLAGS,
        "worker_count": 1,
        "solver_cpu_soft_limit_seconds": CPU_SOFT,
        "solver_cpu_hard_limit_seconds": CPU_HARD,
        "solver_wall_cap_seconds": WALL_CAP,
        "combined_rss_cap_bytes": RSS_CAP,
    })
    print("FROZEN_N131_SEVENPAIR_GAUSS_REPLAY", flush=True)


def limits():
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_SOFT, CPU_HARD))


def restore_formula(protocol):
    archive = BASE / "ordinary.xcnf.gz"
    audit = json.loads((BASE / "audit_result.json").read_text())
    archive_receipt = json.loads((BASE / "archive_receipt.json").read_text())
    base_query = json.loads((BASE / "query_result.json").read_text())
    assert audit["status"] in {
        "PASS_CENSORED_N131_SEVENPAIR_QUERY_RECEIPT",
        "PASS_VERIFIED_ORDINARY_SEVENPAIR_RELATION_RECEIPT",
    }
    assert archive_receipt["raw_sha256"] == protocol["base_formula_sha256"]
    assert base_query["formula"]["xcnf_sha256"] == protocol["base_formula_sha256"]
    assert sha(BASE / "protocol.json") == protocol["base_protocol_sha256"]
    formula = HERE / "formula.xcnf"
    with gzip.open(archive, "rb") as source, formula.open("xb") as target:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            target.write(chunk)
    assert sha(formula) == protocol["base_formula_sha256"]
    assert formula.stat().st_size == protocol["base_formula_bytes"]
    return formula


def audit_model(formula, output, expected_vars):
    assignment = {}
    for line in output.splitlines():
        if line.startswith("v "):
            for raw in line.split()[1:]:
                lit = int(raw)
                if lit:
                    assert abs(lit) not in assignment
                    assignment[abs(lit)] = lit > 0
    assert len(assignment) == expected_vars

    def value(lit):
        return assignment[abs(lit)] if lit > 0 else not assignment[abs(lit)]

    clauses = xors = failed_clauses = failed_xors = 0
    with formula.open() as stream:
        header = stream.readline().split()
        assert header[:3] == ["p", "cnf", str(expected_vars)]
        for line in stream:
            parts = line.split()
            assert parts[-1] == "0"
            if parts[0].startswith("x"):
                head = parts[0]
                rhs = not head.startswith("x-")
                first = int(head[2:] if not rhs else head[1:])
                parity = sum(value(lit) for lit in
                             [first] + [int(item) for item in parts[1:-1]]) & 1
                failed_xors += parity != rhs
                xors += 1
            else:
                failed_clauses += not any(value(int(item)) for item in parts[:-1])
                clauses += 1
    assert int(header[3]) == clauses + xors
    assert failed_clauses == failed_xors == 0
    return {"status": "PASS_COMPLETE_XCNF_ASSIGNMENT",
            "assigned_variables": len(assignment), "clauses": clauses,
            "native_xor_rows": xors,
            "failed_clauses": failed_clauses, "failed_xor_rows": failed_xors}


def run():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert protocol["status"] == "FROZEN_N131_SEVENPAIR_GAUSS_REPLAY"
    assert protocol["runner_sha256"] == sha(Path(__file__))
    assert protocol["solver_sha256"] == sha(SOLVER)
    assert protocol["solver_flags"] == FLAGS
    formula = restore_formula(protocol)
    base_query = json.loads((BASE / "query_result.json").read_text())
    t0 = time.monotonic_ns()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    parent = psutil.Process()
    peak, sampled_cpu, stop = 0, 0.0, None
    stdout_path, stderr_path = HERE / "solver.stdout.txt", HERE / "solver.stderr.txt"
    with stdout_path.open("x") as stdout, stderr_path.open("x") as stderr:
        child = subprocess.Popen([str(SOLVER), *FLAGS, str(formula)],
                                 stdout=stdout, stderr=stderr, preexec_fn=limits)
        process = psutil.Process(child.pid)
        print(json.dumps({"solver_pid": child.pid,
                          "formula_sha256": protocol["base_formula_sha256"]}), flush=True)
        while child.poll() is None:
            try:
                cpu = process.cpu_times()
                sampled_cpu = max(sampled_cpu, cpu.user + cpu.system)
                peak = max(peak, parent.memory_info().rss +
                           process.memory_info().rss)
            except psutil.NoSuchProcess:
                pass
            if peak > RSS_CAP:
                stop = "RSS_CAP"
            elif time.monotonic_ns() - t0 >= WALL_CAP * 10**9:
                stop = "SOLVER_WALL_CAP"
            if stop:
                child.kill()
                break
            time.sleep(0.2)
        code = child.wait()
    t1 = time.monotonic_ns()
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = (after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime)
    output = stdout_path.read_text(errors="replace")
    status_lines = [line for line in output.splitlines() if line.startswith("s ")]
    status = ("SAT_PENDING_GROUP_REPLAY" if "s SATISFIABLE" in status_lines else
              "UNSAT" if "s UNSATISFIABLE" in status_lines else "BOUNDED_UNKNOWN")
    if status == "BOUNDED_UNKNOWN" and stop is None:
        stop = ("CPU_SOFT_LIMIT" if code == -signal.SIGXCPU else
                "CPU_HARD_LIMIT" if code == -signal.SIGKILL and cpu >= CPU_SOFT else
                "SOLVER_EXIT_WITHOUT_STATUS")
    model_audit = None
    if status == "SAT_PENDING_GROUP_REPLAY":
        model_audit = audit_model(formula, output, base_query["formula"]["variables"])
        save("model_audit.json", model_audit)
    save("run_result.json", {
        "status": status, "candidate_id": None,
        "scope": protocol["scope"],
        "curve_id": protocol["curve_id"],
        "workload_id": protocol["workload_id"],
        "public_target": protocol["public_target"],
        "formula_sha256": sha(formula),
        "solver_flags": FLAGS, "worker_count": 1,
        "solver_wall_ns": t1-t0,
        "solver_cpu_seconds_rusage": cpu,
        "solver_cpu_seconds_sampled": sampled_cpu,
        "peak_combined_rss_bytes_sampled": peak,
        "solver_exit_code": code,
        "stop_reason": stop,
        "status_lines": status_lines,
        "restart_rows": sum(line.startswith("c rst") for line in output.splitlines()),
        "model_audit": model_audit,
        "stdout_sha256": sha(stdout_path),
        "stderr_sha256": sha(stderr_path),
        "protocol_sha256": sha(HERE / "protocol.json"),
        "base_audit_sha256": sha(BASE / "audit_result.json"),
    })
    print(json.dumps({"status": status, "stop_reason": stop,
                      "solver_cpu_seconds": cpu,
                      "solver_wall_seconds": (t1-t0)/1e9}), flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {"freeze", "run"}:
        raise SystemExit("usage: replay.py freeze|run")
    {"freeze": freeze, "run": run}[sys.argv[1]]()
