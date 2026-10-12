"""Exact variable-order control for the frozen N41 ten-pair public query."""

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "n41_w8_tenpair_functional_20261012"
sys.path.insert(0, str(SOURCE))
import build as prior_build  # noqa: E402
import run as prior_run  # noqa: E402

SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
FLAGS = ("--threads=1", "--maxtime=170", "--zero-exit-status", "--verb=1", "--printsol=1")
CAP_NS = 180_000_000_000
RSS_CAP = 4 * 1024**3


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, obj):
    with path.open("x") as out:
        json.dump(obj, out, sort_keys=True, indent=2)
        out.write("\n")


def primary():
    lists, targets = prior_build.source()
    chart = json.loads((SOURCE / "positive_chart.json").read_text())
    circuit, wires = prior_build.build(lists, targets, chart, False)
    assert circuit.next_var - 1 == 289065
    ordered = wires["branches"] + [v for row in wires["selectors"] for v in row] + wires["flags"]
    assert len(ordered) == 1413 == len(set(ordered))
    return circuit, wires, chart, ordered


def renumber(literal, mapping):
    number = int(literal)
    assert number
    return str(mapping[abs(number)] * (1 if number > 0 else -1))


def build():
    source = SOURCE / "ordinary.xcnf"
    frozen = json.loads((SOURCE / "protocol.json").read_text())
    assert sha(source) == frozen["sources"][str(source)]
    circuit, wires, chart, ordered = primary()
    count = circuit.next_var - 1
    chosen = set(ordered)
    remaining = (var for var in range(1, count + 1) if var not in chosen)
    permutation = ordered + list(remaining)
    assert len(permutation) == count and len(set(permutation)) == count
    mapping = [0] * (count + 1)
    for new, old in enumerate(permutation, 1):
        mapping[old] = new

    original = source.open()
    result = HERE / "ordered.xcnf"
    cnf = xor = 0
    with original, result.open("x") as out:
        header = original.readline()
        assert header == "p cnf 289065 731771\n"
        out.write(header)
        for line in original:
            terms = line.split()
            is_xor = terms[0] == "x"
            literals = terms[1:-1] if is_xor else terms[:-1]
            assert terms[-1] == "0"
            out.write(("x " if is_xor else "") + " ".join(renumber(v, mapping) for v in literals) + " 0\n")
            xor += is_xor
            cnf += not is_xor
    assert cnf == 604526 and xor == 127245

    initial = {}
    for row, sid in zip(wires["selectors"], chart["state_ids"]):
        initial.update({wire: int(index == sid) for index, wire in enumerate(row)})
    initial.update({wire: bit for wire, bit in zip(wires["branches"], chart["branch_bits"])})
    initial.update({wire: int(index == chart["target_index"])
                    for index, wire in enumerate(wires["flags"])})
    values = prior_run.complete_assignment(circuit, initial)
    assert prior_run.check_assignment(circuit, values) == {
        "cnf_clauses": cnf, "native_xor_rows": xor}
    checks = {"cnf_clauses": 0, "native_xor_rows": 0}
    for line in result.open():
        if line.startswith("p "):
            continue
        terms = line.split()
        is_xor = terms[0] == "x"
        literals = list(map(int, terms[1:-1] if is_xor else terms[:-1]))
        if is_xor:
            assert sum(values[permutation[abs(v) - 1]] ^ (v < 0) for v in literals) & 1
            checks["native_xor_rows"] += 1
        else:
            assert any(values[permutation[abs(v) - 1]] == (v > 0) for v in literals)
            checks["cnf_clauses"] += 1
    assert checks == {"cnf_clauses": cnf, "native_xor_rows": xor}
    save(HERE / "build_result.json", {
        "status": "PASS_EXACT_RENUMBER_AND_CONSTRUCTED_MODEL",
        "candidate_id": None, "variables": count, "primary_variables": len(ordered),
        "order": "nine S3 branches; ten times 140 source selectors; four target-fiber selectors; then original auxiliaries",
        "source_xcnf_sha256": sha(source), "ordered_xcnf_sha256": sha(result),
        "source_protocol_sha256": sha(SOURCE / "protocol.json"),
        "source_chart_sha256": sha(SOURCE / "positive_chart.json"),
        "positive_assignment_checks": checks,
        "branch_old_ids": wires["branches"],
        "branch_new_ids": [mapping[v] for v in wires["branches"]],
        "source_sha256": sha(__file__), "solver_sha256": sha(SOLVER),
    })


def freeze():
    result = json.loads((HERE / "build_result.json").read_text())
    assert result["status"] == "PASS_EXACT_RENUMBER_AND_CONSTRUCTED_MODEL"
    paths = [Path(__file__), SOLVER, SOURCE / "ordinary.xcnf", SOURCE / "protocol.json",
             SOURCE / "build.py", SOURCE / "run.py", HERE / "ordered.xcnf",
             HERE / "build_result.json"]
    save(HERE / "protocol.json", {
        "status": "FROZEN_BEFORE_N41_PRIMARY_ORDER_PUBLIC_QUERY", "candidate_id": None,
        "public_target": [920359962848, 755404565011],
        "source_law": "ten free signed W8 pair states with ten-edge shield",
        "workers": 1, "solver_flags": FLAGS, "parent_wall_cap_ns": CAP_NS,
        "combined_rss_cap_bytes": RSS_CAP,
        "sources": {str(path): sha(path) for path in paths}})


def query():
    protocol = json.loads((HERE / "protocol.json").read_text())
    for path, digest in protocol["sources"].items():
        assert sha(path) == digest, path
    stdout = HERE / "solver.stdout"
    stderr = HERE / "solver.stderr"
    parent = psutil.Process()
    peak = 0
    stop = None
    start = time.monotonic_ns()
    with stdout.open("x") as out, stderr.open("x") as err:
        child = subprocess.Popen([str(SOLVER), *FLAGS, str(HERE / "ordered.xcnf")],
                                 stdout=out, stderr=err)
        proc = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                peak = max(peak, parent.memory_info().rss + proc.memory_info().rss)
                if peak > RSS_CAP:
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
    wall = time.monotonic_ns() - start
    lines = stdout.read_text(errors="replace").splitlines()
    terminals = [line for line in lines if line.startswith("s ")]
    status = ("SAT_PENDING_GROUP_REPLAY" if terminals and terminals[-1] == "s SATISFIABLE" else
              "UNSAT" if terminals and terminals[-1] == "s UNSATISFIABLE" else "BOUNDED_UNKNOWN")
    save(HERE / "query_result.json", {
        "status": status, "candidate_id": None,
        "terminal": terminals[-1] if terminals else None, "stop_reason": stop,
        "exit_code": exit_code, "solver_wall_ns": wall,
        "peak_combined_rss_bytes": peak,
        "restart_rows": sum(line.startswith("c rst") for line in lines),
        "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr),
        "protocol_sha256": sha(HERE / "protocol.json")})
    print(status, wall / 1e9, peak, flush=True)


if __name__ == "__main__":
    {"build": build, "freeze": freeze, "query": query}[sys.argv[1]]()
