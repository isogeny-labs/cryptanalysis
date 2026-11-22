"""Freeze, control, and bounded ordinary search for N41 functional-root XCNF."""

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
sys.path.insert(0, str(HERE))
import build  # noqa: E402

SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
FLAGS = ("--threads=1", "--maxtime=170", "--zero-exit-status", "--verb=1", "--printsol=1")
CAP_NS = 180 * 10**9
RSS_CAP = 4 * 1024**3


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def freeze():
    result = json.loads((HERE / "build_result.json").read_text())
    audit = json.loads((HERE / "audit_result.json").read_text())
    assert result["status"] == "BUILT_N41_TENPAIR_FUNCTIONAL_ROOT"
    assert audit["status"] == "PASS_INDEPENDENT_SAGE_N41_FUNCTIONAL_ROOT_CHART"
    paths = (Path(__file__), HERE / "build.py", HERE / "build_result.json",
             HERE / "positive_chart.json", HERE / "audit_result.json",
             HERE / "audit_protocol.json", HERE / "sage_runtime_info.json",
             HERE / "control.xcnf", HERE / "ordinary.xcnf",
             build.INPUT, build.POSITIVE, SOLVER,
             GOAL / "functional_inverse_circuit.py",
             GOAL / "functional_pair_root_circuit.py",
             build.ROOT / "experiments/koblitz-polynomial-w-pair-20260925/karatsuba_circuit.py")
    save(HERE / "protocol.json", {
        "status": "FROZEN_BEFORE_N41_FUNCTIONAL_CONTROL_AND_PUBLIC_QUERY",
        "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
        "candidate_id": None,
        "public_target": [920359962848, 755404565011],
        "target_law": "four raw preimages of one frozen public point",
        "source_law": "ten free signed W8 pair states with exact ten-edge shield",
        "workers": 1, "cap_ns": CAP_NS,
        "combined_rss_cap_bytes": RSS_CAP, "solver_flags": FLAGS,
        "sources": {str(path): sha(path) for path in paths},
    })


def complete_assignment(circuit, initial):
    definitions = {int(out): ("and", int(a), int(b))
                   for (a, b), out in circuit.and_cache.items()}
    for line in circuit.xors:
        literals = [int(item) for item in line.split()[1:-1]]
        definitions[abs(literals[0])] = ("xor", literals)
    values = [None] * circuit.next_var
    for wire, bit in initial.items():
        assert values[wire] is None or values[wire] == bit
        values[wire] = bit
    for wire in range(1, circuit.next_var):
        if values[wire] is not None:
            continue
        definition = definitions[wire]
        if definition[0] == "and":
            def value(item):
                return 1 if item == -1 else 0 if item == 0 else values[item]
            values[wire] = value(definition[1]) & value(definition[2])
        else:
            literals = definition[1]
            bit = int(literals[0] > 0)
            for item in literals[1:]:
                bit ^= values[abs(item)] ^ int(item < 0)
            values[wire] = bit
    return values


def check_assignment(circuit, values):
    for index, line in enumerate(circuit.clauses):
        lits = [int(value) for value in line.split()[:-1]]
        assert any(values[abs(lit)] == int(lit > 0) for lit in lits), index
    for index, line in enumerate(circuit.xors):
        lits = [int(value) for value in line.split()[1:-1]]
        assert sum(values[abs(lit)] ^ int(lit < 0) for lit in lits) & 1, index
    return {"cnf_clauses": len(circuit.clauses), "native_xor_rows": len(circuit.xors)}


def control():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert protocol["status"] == "FROZEN_BEFORE_N41_FUNCTIONAL_CONTROL_AND_PUBLIC_QUERY"
    for path, digest in protocol["sources"].items():
        assert sha(path) == digest, path
    lists, targets = build.source()
    chart = json.loads((HERE / "positive_chart.json").read_text())
    checks = []
    for name, pinned in (("control", True), ("ordinary", False)):
        circuit, wires = build.build(lists, targets, chart, pinned)
        initial = {}
        for row, sid in zip(wires["selectors"], chart["state_ids"]):
            initial.update({wire: int(index == sid) for index, wire in enumerate(row)})
        initial.update({wire: bit for wire, bit in
                        zip(wires["branches"], chart["branch_bits"])})
        initial.update({wire: int(index == chart["target_index"])
                        for index, wire in enumerate(wires["flags"])})
        values = complete_assignment(circuit, initial)
        check = check_assignment(circuit, values)
        temp = HERE / f"{name}.replay.xcnf"
        circuit.write(temp)
        assert sha(temp) == protocol["sources"][str(HERE / f"{name}.xcnf")]
        temp.unlink()
        checks.append({"formula": name, "primary_bits": len(initial),
                       "variables": circuit.next_var - 1, **check})
        print("PASS_CONSTRUCTED_ASSIGNMENT", name, check, flush=True)
    save(HERE / "control_result.json", {
        "status": "PASS_FULL_N41_FUNCTIONAL_CONSTRUCTED_ASSIGNMENT",
        "protocol_sha256": sha(HERE / "protocol.json"),
        "audit_result_sha256": sha(HERE / "audit_result.json"),
        "checks": checks})


def query():
    protocol = json.loads((HERE / "protocol.json").read_text())
    control_result = json.loads((HERE / "control_result.json").read_text())
    assert control_result["status"] == "PASS_FULL_N41_FUNCTIONAL_CONSTRUCTED_ASSIGNMENT"
    assert control_result["protocol_sha256"] == sha(HERE / "protocol.json")
    for path, digest in protocol["sources"].items():
        assert sha(path) == digest, path
    stdout_path, stderr_path = HERE / "solver.stdout", HERE / "solver.stderr"
    parent = psutil.Process()
    peak, stop = 0, None
    start = time.monotonic_ns()
    with stdout_path.open("x") as stdout, stderr_path.open("x") as stderr:
        child = subprocess.Popen([str(SOLVER), *FLAGS, str(HERE / "ordinary.xcnf")],
                                 stdout=stdout, stderr=stderr)
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
        exit_code = child.wait()
    elapsed = time.monotonic_ns() - start
    lines = stdout_path.read_text(errors="replace").splitlines()
    terminals = [line for line in lines if line.startswith("s ")]
    status = ("SAT_PENDING_GROUP_REPLAY" if terminals and terminals[-1] == "s SATISFIABLE" else
              "UNSAT" if terminals and terminals[-1] == "s UNSATISFIABLE" else
              "BOUNDED_UNKNOWN")
    save(HERE / "query_result.json", {
        "status": status, "candidate_id": None,
        "terminal": terminals[-1] if terminals else None,
        "stop_reason": stop, "exit_code": exit_code,
        "solver_wall_ns": elapsed, "peak_combined_rss_bytes": peak,
        "restart_rows": sum(line.startswith("c rst") for line in lines),
        "stdout_sha256": sha(stdout_path), "stderr_sha256": sha(stderr_path),
        "protocol_sha256": sha(HERE / "protocol.json"),
        "control_result_sha256": sha(HERE / "control_result.json")})
    print(status, elapsed / 1e9, peak, flush=True)


if __name__ == "__main__":
    {"freeze": freeze, "control": control, "query": query}[sys.argv[1]]()
