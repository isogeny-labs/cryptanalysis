"""Exact target/source variable order on the frozen functional full-point XCNF."""

import hashlib
import importlib.util
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
SOURCE = GOAL / "n41_fullpoint_functional_slope_20261012"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
CAP = 180
RSS_CAP = 4 * 1024 ** 3


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


parent = load("functional_fullpoint_source", SOURCE / "run.py")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    with path.open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def check_build_inputs():
    frozen = json.loads((HERE / "build_protocol.json").read_text())
    sources = {"runner": HERE / "run.py", "source_xcnf": SOURCE / "public.xcnf",
               "source_runner": SOURCE / "run.py", "source_protocol": SOURCE / "protocol.json",
               "source_positive": SOURCE / "control.json", "solver": SOLVER}
    assert {key: sha(path) for key, path in sources.items()} == frozen["sha256"]
    return frozen


def primary():
    lists, targets = parent.old.source()
    chart = parent.old.positive_chart(lists, targets)
    circuit, wires = parent.formula(lists, targets, False, chart)
    assert circuit.next_var - 1 == 121456
    chosen = wires["flags"] + [wire for row in wires["selectors"] for wire in row]
    assert len(chosen) == 1404 == len(set(chosen))
    return circuit, wires, chart, chosen


def permutation(chosen, count):
    selected = set(chosen)
    order = chosen + [old for old in range(1, count + 1) if old not in selected]
    assert len(order) == count and len(set(order)) == count
    mapping = [0] * (count + 1)
    for new, old in enumerate(order, 1):
        mapping[old] = new
    assert all(mapping[1:])
    return order, mapping


def transform(literal, mapping):
    value = int(literal)
    assert value
    return mapping[abs(value)] * (1 if value > 0 else -1)


def build():
    check_build_inputs()
    start = time.monotonic_ns()
    circuit, wires, chart, chosen = primary()
    built = time.monotonic_ns()
    with tempfile.NamedTemporaryFile(dir="/private/tmp", suffix=".xcnf") as temporary:
        circuit.write(Path(temporary.name))
        assert sha(temporary.name) == sha(SOURCE / "public.xcnf")
    order, mapping = permutation(chosen, circuit.next_var - 1)
    output = HERE / "ordered.xcnf"
    cnf = xor = 0
    with (SOURCE / "public.xcnf").open() as original, output.open("x") as dest:
        header = original.readline()
        dest.write(header)
        for line in original:
            words = line.split()
            is_xor = words[0] == "x"
            literals = words[1:-1] if is_xor else words[:-1]
            assert words[-1] == "0"
            dest.write(("x " if is_xor else "") +
                       " ".join(map(str, (transform(v, mapping) for v in literals))) + " 0\n")
            xor += is_xor
            cnf += not is_xor
    assert cnf == 325702 and xor == 52354
    initial = {}
    for row, sid in zip(wires["selectors"], chart["state_ids"]):
        initial.update({wire: int(i == sid) for i, wire in enumerate(row)})
    initial.update({wire: int(i == chart["target_index"])
                    for i, wire in enumerate(wires["flags"])})
    values = parent.parent.check.complete_assignment(circuit, initial)
    assert parent.parent.check.check_assignment(circuit, values) == {
        "clauses": cnf, "native_xor_rows": xor}
    checks = {"cnf_clauses": 0, "native_xor_rows": 0}
    with output.open() as stream:
        next(stream)
        for line in stream:
            words = line.split()
            is_xor = words[0] == "x"
            literals = list(map(int, words[1:-1] if is_xor else words[:-1]))
            if is_xor:
                assert sum(values[order[abs(v) - 1]] ^ int(v < 0) for v in literals) & 1
                checks["native_xor_rows"] += 1
            else:
                assert any(values[order[abs(v) - 1]] == int(v > 0) for v in literals)
                checks["cnf_clauses"] += 1
    assert checks == {"cnf_clauses": cnf, "native_xor_rows": xor}
    ended = time.monotonic_ns()
    save(HERE / "build.json", {"status": "PASS_EXACT_FUNCTIONAL_FULLPOINT_RENUMBER",
                              "candidate_id": None, "variables": circuit.next_var - 1,
                              "target_flags_new": [mapping[v] for v in wires["flags"]],
                              "source_selector_count": 1400,
                              "source_xcnf_sha256": sha(SOURCE / "public.xcnf"),
                              "ordered_xcnf_sha256": sha(output),
                              "ordered_xcnf_bytes": output.stat().st_size,
                              "checks": checks,
                              "build_ns_exploratory": built - start,
                              "renumber_and_check_ns_exploratory": ended - built})
    print("PASS_EXACT_FUNCTIONAL_FULLPOINT_RENUMBER", flush=True)


def freeze():
    check_build_inputs()
    result = json.loads((HERE / "build.json").read_text())
    assert result["status"] == "PASS_EXACT_FUNCTIONAL_FULLPOINT_RENUMBER"
    paths = [HERE / "run.py", HERE / "build_protocol.json", HERE / "build.json",
             HERE / "ordered.xcnf", SOURCE / "public.xcnf", SOURCE / "run.py", SOLVER]
    save(HERE / "query_protocol.json", {
        "status": "FROZEN_BEFORE_N41_FUNCTIONAL_SOURCE_ORDER_PUBLIC_QUERY",
        "candidate_id": None, "public_point": [920359962848, 755404565011],
        "workers": 1, "parent_cap_s": CAP, "combined_rss_cap_bytes": RSS_CAP,
        "command": [str(SOLVER), "--threads=1", "--maxtime=175",
                    "--zero-exit-status", "--verb=1", "--printsol=1",
                    str(HERE / "ordered.xcnf")],
        "sha256": {str(path): sha(path) for path in paths}})
    print("FROZEN_BEFORE_QUERY", flush=True)


def query():
    protocol = json.loads((HERE / "query_protocol.json").read_text())
    for path, digest in protocol["sha256"].items():
        assert sha(path) == digest, path
    stdout, stderr = HERE / "solver.stdout", HERE / "solver.stderr"
    start = time.monotonic_ns()
    peak = 0
    stop = None
    with stdout.open("x") as out, stderr.open("x") as err:
        child = subprocess.Popen(protocol["command"], stdout=out, stderr=err)
        worker, owner = psutil.Process(child.pid), psutil.Process(os.getpid())
        while child.poll() is None:
            try:
                peak = max(peak, worker.memory_info().rss + owner.memory_info().rss)
            except psutil.NoSuchProcess:
                break
            if peak > RSS_CAP:
                stop = "RSS_CAP"
            elif (time.monotonic_ns() - start) / 1e9 > CAP:
                stop = "PARENT_TIME_CAP"
            if stop:
                child.kill()
                break
            time.sleep(0.025)
        child.wait()
    duration = time.monotonic_ns() - start
    log = stdout.read_text(errors="replace")
    terminals = [line for line in log.splitlines() if line.startswith("s ")]
    status = ("SAT_PENDING_INDEPENDENT_REPLAY" if "s SATISFIABLE" in terminals else
              "UNSAT" if "s UNSATISFIABLE" in terminals else
              "BOUNDED_UNKNOWN" if "s INDETERMINATE" in terminals else
              stop or "UNKNOWN")
    save(HERE / "query.json", {"status": status, "candidate_id": None,
                              "terminal_lines": terminals, "stop": stop,
                              "exit_code": child.returncode,
                              "solver_wall_ns_exploratory": duration,
                              "peak_combined_rss_bytes_sampled": peak,
                              "restart_rows": sum(line.startswith("c rst") for line in log.splitlines()),
                              "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr),
                              "query_protocol_sha256": sha(HERE / "query_protocol.json")})
    print(status, duration / 1e9, flush=True)


if __name__ == "__main__":
    import sys
    {"build": build, "freeze": freeze, "query": query}[sys.argv[1]]()
