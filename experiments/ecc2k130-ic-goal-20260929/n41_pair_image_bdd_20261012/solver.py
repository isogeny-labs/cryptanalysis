"""Frozen CryptoMiniSat controls for the exact N41 output-first pair BDD."""

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
PARENT = GOAL / "n41_allseed_fourpair_forward_20261012"
FIXTURE = GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal/control_fixture.json"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
RSS_CAP = 4 * 1024**3
SPECS = {
    "control": {"solver_seconds": 30, "parent_seconds": 35},
    "ordinary": {"solver_seconds": 180, "parent_seconds": 190},
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with path.open("x") as out:
        json.dump(value, out, sort_keys=True, indent=2)
        out.write("\n")


def flags(mode):
    return ("--threads=1", f"--maxtime={SPECS[mode]['solver_seconds']}",
            "--zero-exit-status", "--verb=1", "--printsol=1")


def make_control():
    build = json.loads((HERE / "build_result.json").read_text())
    fixture = json.loads(FIXTURE.read_text())
    chart = json.loads((PARENT / "chart.json").read_text())
    pins = []
    for bits, value in zip(build["pair_output_bits"], fixture["pair_reciprocals"]):
        pins.extend(wire if value >> bit & 1 else -wire for bit, wire in enumerate(bits))
    pins.extend(wire if bit else -wire for wire, bit in
                zip(build["root_branch_wires"], chart["root_branch_bits"][4:]))
    assert len(pins) == 167
    source, output = HERE / "public.xcnf", HERE / "control.xcnf"
    with source.open() as inp, output.open("x") as out:
        head = inp.readline().split()
        assert head[:2] == ["p", "cnf"]
        variables, rows = map(int, head[2:])
        out.write(f"p cnf {variables} {rows + len(pins)}\n")
        for line in inp:
            out.write(line)
        for literal in pins:
            out.write(f"{literal} 0\n")
    save(HERE / "control_build.json", {
        "status": "PASS_CONSTRUCTED_PRIMARY_PIN_CONTROL", "pins": pins,
        "formula_sha256": sha(output), "source_formula_sha256": sha(source),
        "variables": variables, "rows": rows + len(pins)})


def freeze():
    paths = (Path(__file__), HERE / "build.py", HERE / "public.xcnf",
             HERE / "control.xcnf", HERE / "control_build.json",
             HERE / "build_result.json", HERE / "census_result.json",
             HERE / "output_values.json", HERE / "build_audit.json",
             PARENT / "chart.json", FIXTURE, SOLVER)
    save(HERE / "solver_protocol.json", {
        "status": "FROZEN_BEFORE_N41_OUTPUT_BDD_SOLVER_CONTROL_AND_QUERY",
        "candidate_id": None, "workers": 1, "rss_cap_bytes": RSS_CAP,
        "specs": {mode: {**spec, "flags": flags(mode)} for mode, spec in SPECS.items()},
        "sources": {str(path): sha(path) for path in paths}})


def run(mode):
    assert mode in SPECS
    protocol = json.loads((HERE / "solver_protocol.json").read_text())
    assert all(sha(path) == digest for path, digest in protocol["sources"].items())
    spec = SPECS[mode]
    formula = HERE / ("control.xcnf" if mode == "control" else "public.xcnf")
    stdout, stderr = HERE / f"{mode}.stdout", HERE / f"{mode}.stderr"
    parent, peak, stop = psutil.Process(), 0, None
    start = time.monotonic_ns()
    with stdout.open("x") as out, stderr.open("x") as err:
        child = subprocess.Popen([str(SOLVER), *flags(mode), str(formula)],
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
            if time.monotonic_ns() - start > spec["parent_seconds"] * 10**9:
                stop = "WALL_CAP"
            if stop:
                child.kill()
                break
            time.sleep(.025)
        code = child.wait()
    lines = stdout.read_text(errors="replace").splitlines()
    terminals = [line for line in lines if line.startswith("s ")]
    terminal = terminals[-1] if terminals else None
    status = ("SAT_PENDING_REPLAY" if terminal == "s SATISFIABLE" else
              "UNSAT" if terminal == "s UNSATISFIABLE" else
              "BOUNDED_UNKNOWN" if stop or terminal in (None, "s INDETERMINATE") else
              "PRODUCER_FAILURE")
    save(HERE / f"{mode}_result.json", {
        "status": status, "terminal": terminal, "stop_reason": stop,
        "exit_code": code, "wall_ns": time.monotonic_ns() - start,
        "peak_combined_rss_bytes": peak,
        "restart_rows": sum(line.startswith("c rst") for line in lines),
        "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr),
        "protocol_sha256": sha(HERE / "solver_protocol.json")})
    print(mode, status, flush=True)


def audit(mode):
    protocol = json.loads((HERE / "solver_protocol.json").read_text())
    result = json.loads((HERE / f"{mode}_result.json").read_text())
    assert all(sha(path) == digest for path, digest in protocol["sources"].items())
    assert result["protocol_sha256"] == sha(HERE / "solver_protocol.json")
    stdout, stderr = HERE / f"{mode}.stdout", HERE / f"{mode}.stderr"
    assert result["stdout_sha256"] == sha(stdout)
    assert result["stderr_sha256"] == sha(stderr)
    lines = stdout.read_text(errors="replace").splitlines()
    terminals = [line for line in lines if line.startswith("s ")]
    assert (terminals[-1] if terminals else None) == result["terminal"]
    assert sum(line.startswith("c rst") for line in lines) == result["restart_rows"]
    model = None
    if result["status"] == "SAT_PENDING_REPLAY":
        assignment = {}
        for line in lines:
            if line.startswith("v "):
                for word in line.split()[1:]:
                    literal = int(word)
                    if literal:
                        assert abs(literal) not in assignment
                        assignment[abs(literal)] = literal > 0
        formula = HERE / ("control.xcnf" if mode == "control" else "public.xcnf")
        with formula.open() as stream:
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
                assert (sum(values) & 1) if is_xor else any(values)
                if is_xor:
                    xor += 1
                else:
                    cnf += 1
            assert cnf + xor == rows
        build = json.loads((HERE / "build_result.json").read_text())
        output_values = [sum(int(assignment[wire]) << bit for bit, wire in enumerate(bits))
                         for bits in build["pair_output_bits"]]
        branch_values = [int(assignment[wire]) for wire in build["root_branch_wires"]]
        model = {"variables": variables, "cnf_clauses": cnf, "native_xor_rows": xor,
                 "pair_reciprocals": output_values, "root_branch_bits": branch_values}
    save(HERE / f"{mode}_audit.json", {
        "status": "PASS_FROZEN_N41_OUTPUT_BDD_SOLVER_AUDIT",
        "recorded_status": result["status"], "model_check": model,
        "result_sha256": sha(HERE / f"{mode}_result.json")})
    print(mode, "AUDITED", result["status"], flush=True)


if __name__ == "__main__":
    action = sys.argv[1]
    if action == "make_control":
        make_control()
    elif action == "freeze":
        freeze()
    elif action in ("run", "audit"):
        {"run": run, "audit": audit}[action](sys.argv[2])
    else:
        raise ValueError(action)
