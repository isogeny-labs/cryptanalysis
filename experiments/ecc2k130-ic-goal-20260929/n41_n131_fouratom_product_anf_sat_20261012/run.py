"""Exact fixed-seed four-atom product ANF to native-XOR SAT experiment."""
import argparse
import hashlib
import importlib.util
import json
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n41_n131_fouratom_product_anf_20261012"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
CAP_S = 120
RSS_CAP = 4 * 1024 ** 3


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


spec = importlib.util.spec_from_file_location("independent_anf", PARENT / "audit.py")
ind = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ind)


def source(case):
    words = list(map(int, (PARENT / (case + ".txt")).read_text().split()))
    n, dimension, s0, s1, r0, r1, z, m0, m1, m2, m3 = words
    low = 0x9 if n == 41 else 0x2007
    left = ind.basis(n, dimension, s0 << 1, r0, low)
    right = ind.basis(n, dimension, s1 << 1, r1, low)
    a = ind.frob(s0 << 1, r0, n, low)
    b = ind.frob(s1 << 1, r1, n, low)
    matrix = ind.matrix(a, b, z, n, low)
    anf, raw = ind.build_anf(matrix, left, right, n, low)
    archived = json.loads((PARENT / (case + ".json")).read_text())
    assert len(anf) == archived["anf_monomials"]
    assert raw == archived["raw_tensor_terms"]
    return words, low, left, right, matrix, anf


def formula(path, n, d, anf):
    # A single gate is shared by every occurrence of each square-free monomial.
    wires = {1 << bit: bit + 1 for bit in range(2 * d)}
    gates = []
    next_var = 2 * d

    def wire(mask):
        nonlocal next_var
        if mask in wires:
            return wires[mask]
        bit = mask & -mask
        parent = wire(mask ^ bit)
        next_var += 1
        wires[mask] = next_var
        gates.append((next_var, parent, wires[bit]))
        return next_var

    for mask in sorted(anf):
        if mask:
            wire(mask)
    rows = [[] for _ in range(n)]
    for mask, coefficient in sorted(anf.items()):
        if mask == 0:
            continue
        v = wires[mask]
        for bit in range(n):
            if coefficient >> bit & 1:
                rows[bit].append(v)
    constant = anf.get(0, 0)
    empty = []
    for bit, row in enumerate(rows):
        if not row:
            empty.append(bit)
    if empty:
        raise ValueError("empty field output rows need constant-only handling")
    with path.open("x") as out:
        out.write("p cnf %d %d\n" % (next_var, 3 * len(gates) + n))
        for v, a, b in gates:
            out.write("-%d %d 0\n-%d %d 0\n%d -%d -%d 0\n" %
                      (v, a, v, b, v, a, b))
        for bit, row in enumerate(rows):
            # XCNF rows require XOR(literals)=1. Negating the first literal
            # represents a zero right-hand side.
            if not (constant >> bit & 1):
                row[0] = -row[0]
            out.write("x" + " ".join(map(str, row)) + " 0\n")
    return {"variables": next_var, "primary_bits": 2 * d,
            "and_gates": len(gates), "cnf_clauses": 3 * len(gates),
            "native_xor_rows": n, "xor_literal_count": sum(map(len, rows)),
            "bytes": path.stat().st_size, "sha256": sha(path)}


def model(stdout, variable_count):
    bits = {}
    for line in stdout.splitlines():
        if line.startswith("v "):
            for token in line[2:].split():
                value = int(token)
                if value:
                    bits[abs(value)] = value > 0
    if len(bits) != variable_count:
        raise ValueError("incomplete SAT assignment: %d/%d" % (len(bits), variable_count))
    return bits


def check_formula(path, bits):
    cnf = xor = 0
    with path.open() as stream:
        for line in stream:
            if line.startswith("p "):
                continue
            is_xor = line.startswith("x")
            lits = list(map(int, line[1:].split()[:-1] if is_xor else line.split()[:-1]))
            values = [bits[abs(lit)] != (lit < 0) for lit in lits]
            if is_xor:
                assert sum(values) % 2 == 1
                xor += 1
            else:
                assert any(values)
                cnf += 1
    return {"cnf_clauses_checked": cnf, "native_xor_rows_checked": xor}


def semantic(case, bits, left, right, matrix, anf, n, low):
    d = len(left)
    mask = sum(1 << i for i in range(2 * d) if bits[i + 1])
    p = 0
    q = 0
    for i in range(d):
        if mask >> i & 1:
            p ^= left[i]
        if mask >> (d + i) & 1:
            q ^= right[i]
    value = ind.direct(matrix, p, q, n, low)
    assert value == ind.eval_anf(anf, mask) == 0
    archived = json.loads((PARENT / (case + ".json")).read_text())
    expected = archived["positive_product_masks"]
    return {"assignment_mask": mask, "product_masks": [mask & ((1 << d) - 1), mask >> d],
            "archived_source_product_masks": expected,
            "matches_archived_source_products": [mask & ((1 << d) - 1), mask >> d] == expected,
            "direct_field_value": value}


def run(case):
    assert case in ("n41_positive", "n41_negative")
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert sha(HERE / "run.py") == protocol["sha256"]["runner"]
    assert sha(PARENT / "audit.py") == protocol["sha256"]["independent_anf"]
    assert sha(SOLVER) == protocol["sha256"]["solver"]
    assert sha(PARENT / (case + ".txt")) == protocol["sha256"][case]
    started = time.monotonic_ns()
    words, low, left, right, matrix, anf = source(case)
    built = time.monotonic_ns()
    path = HERE / (case + ".xcnf")
    profile = formula(path, words[0], len(left), anf)
    ready = time.monotonic_ns()
    command = [str(SOLVER), "--threads=1", "--xor=0", "--printsol=1",
               "--random=20261012", "--maxconfl=20000000", str(path)]
    stdout_path = HERE / (case + ".stdout.txt")
    with stdout_path.open("x") as output:
        process = subprocess.Popen(command, stdout=output,
                                   stderr=subprocess.STDOUT, text=True)
        monitor = psutil.Process(process.pid)
        peak = 0
        timed_out = False
        rss_exceeded = False
        while process.poll() is None:
            try:
                peak = max(peak, monitor.memory_info().rss)
            except psutil.NoSuchProcess:
                break
            if peak > RSS_CAP:
                rss_exceeded = True
                process.kill()
                break
            if (time.monotonic_ns() - ready) / 1e9 > CAP_S:
                timed_out = True
                process.kill()
                break
            time.sleep(0.02)
        process.wait()
    stdout = stdout_path.read_text()
    solved = time.monotonic_ns()
    status = ("RSS_CAP" if rss_exceeded else "TIMEOUT" if timed_out else
              "SAT" if "s SATISFIABLE" in stdout else
              "UNSAT" if "s UNSATISFIABLE" in stdout else "UNKNOWN")
    checked = None
    meaning = None
    if status == "SAT":
        bits = model(stdout, profile["variables"])
        checked = check_formula(path, bits)
        meaning = semantic(case, bits, left, right, matrix, anf, words[0], low)
    audited = time.monotonic_ns()
    result = {"case": case, "status": status, "candidate_id": None,
              "formula": profile, "anf_monomials": len(anf), "command": command,
              "solver_returncode": process.returncode, "solver_stdout_sha256": sha(stdout_path),
              "peak_solver_rss_bytes_sampled": peak,
              "phase_ns_exploratory": {"anf_build": built - started,
                                        "formula_emit": ready - built,
                                        "solver": solved - ready,
                                        "model_and_semantic_check": audited - solved},
              "formula_model_check": checked, "semantic_check": meaning,
              "resource": {"workers": 1, "wall_cap_s": CAP_S, "rss_cap_bytes": RSS_CAP}}
    (HERE / (case + ".json")).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(case, status, profile, result["phase_ns_exploratory"], flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("case", choices=("n41_positive", "n41_negative"))
    run(parser.parse_args().case)
