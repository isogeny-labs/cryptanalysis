"""Frozen source-mask/root-branch pin ladder on the N41 public XCNF."""

import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
PARENT = GOAL / "n41_allseed_fourpair_forward_20261012"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
SPECS = {
    "three_pair": {"pinned_masks": 6, "pinned_branches": 0, "solver_seconds": 90, "parent_seconds": 95},
    "all_pair": {"pinned_masks": 8, "pinned_branches": 0, "solver_seconds": 30, "parent_seconds": 35},
    "two_pair_branch": {"pinned_masks": 4, "pinned_branches": 7, "solver_seconds": 90, "parent_seconds": 95},
}
RSS_CAP = 4 * 1024**3

_spec = importlib.util.spec_from_file_location("fourpair_forward_build", PARENT / "build.py")
build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def flags(name):
    return ("--threads=1", f"--maxtime={SPECS[name]['solver_seconds']}",
            "--zero-exit-status", "--verb=1", "--printsol=1")


def construct():
    chart = json.loads((PARENT / "chart.json").read_text())
    built = {}
    for name, spec in SPECS.items():
        circuit, wires, metadata = build.formula("n41", chart["target_reciprocal"])
        for mask_bits, mask in zip(wires["masks"][:spec["pinned_masks"]], chart["masks"]):
            for bit, wire in enumerate(mask_bits):
                circuit.clauses.append(f"{wire if mask >> bit & 1 else -wire} 0")
        for wire, bit in zip(wires["branches"][:spec["pinned_branches"]],
                             chart["root_branch_bits"]):
            circuit.clauses.append(f"{wire if bit else -wire} 0")
        primary = {}
        for bits, mask in zip(wires["masks"], chart["masks"]):
            primary.update({wire: (mask >> bit) & 1 for bit, wire in enumerate(bits)})
        primary.update({wire: bit for wire, bit in
                        zip(wires["branches"], chart["root_branch_bits"])})
        complete = build.prior_run.complete_assignment(circuit, primary)
        checked = build.prior_run.check_assignment(circuit, complete)
        output = HERE / f"{name}.xcnf"
        circuit.write(output)
        built[name] = {
            "status": "PASS_CONSTRUCTED_POSITIVE_ASSIGNMENT", "candidate_id": None,
            "spec": spec, "metadata": metadata,
            "variables": circuit.next_var - 1, "cnf_clauses": len(circuit.clauses),
            "native_xor_rows": len(circuit.xors), "positive_assignment_check": checked,
            "formula_sha256": sha(output),
            "wire_map": {"mask_bits": wires["masks"], "root_branches": wires["branches"]},
        }
        print("BUILT", name, circuit.next_var - 1, flush=True)
    save(HERE / "build_result.json", {
        "status": "PASS_THREE_PIN_LADDER_FORMULAS", "parent_chart_sha256": sha(PARENT / "chart.json"),
        "variants": built})


def freeze():
    parent_paths = (PARENT / "build.py", PARENT / "chart.json", PARENT / "audit_result.json",
                    PARENT / "build_result.json", PARENT / "sage_runtime_info.json",
                    GOAL / "n131_w18_allseed_fourpair_20261012/fourpair_v2.py",
                    GOAL / "n41_w8_tenpair_functional_20261012/build.py",
                    GOAL / "n41_w8_tenpair_functional_20261012/run.py")
    paths = (Path(__file__), HERE / "build_result.json", SOLVER, *parent_paths,
             *(HERE / f"{name}.xcnf" for name in SPECS))
    save(HERE / "protocol.json", {
        "status": "FROZEN_BEFORE_THREE_N41_PIN_CONTROLS", "candidate_id": None,
        "workers": 1, "rss_cap_bytes": RSS_CAP,
        "specs": {name: {**spec, "flags": flags(name)} for name, spec in SPECS.items()},
        "sources": {str(path): sha(path) for path in paths}})


def run(name):
    protocol = json.loads((HERE / "protocol.json").read_text())
    for path, digest in protocol["sources"].items():
        assert sha(path) == digest, path
    spec = SPECS[name]
    stdout, stderr = HERE / f"{name}.stdout", HERE / f"{name}.stderr"
    parent = psutil.Process()
    peak = 0
    stop = None
    start = time.monotonic_ns()
    with stdout.open("x") as out, stderr.open("x") as err:
        child = subprocess.Popen([str(SOLVER), *flags(name), str(HERE / f"{name}.xcnf")],
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
              "UNSAT" if terminal == "s UNSATISFIABLE" else "BOUNDED_UNKNOWN")
    save(HERE / f"{name}.result.json", {
        "status": status, "variant": name, "terminal": terminal, "stop_reason": stop,
        "exit_code": code, "wall_ns": time.monotonic_ns() - start,
        "peak_combined_rss_bytes": peak,
        "restart_rows": sum(line.startswith("c rst") for line in lines),
        "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr),
        "protocol_sha256": sha(HERE / "protocol.json")})
    print(name, status, flush=True)


def audit(name):
    protocol = json.loads((HERE / "protocol.json").read_text())
    build_result = json.loads((HERE / "build_result.json").read_text())
    result = json.loads((HERE / f"{name}.result.json").read_text())
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert result["variant"] == name
    assert all(sha(path) == digest for path, digest in protocol["sources"].items())
    stdout, stderr = HERE / f"{name}.stdout", HERE / f"{name}.stderr"
    assert result["stdout_sha256"] == sha(stdout)
    assert result["stderr_sha256"] == sha(stderr)
    lines = stdout.read_text(errors="replace").splitlines()
    terminals = [line for line in lines if line.startswith("s ")]
    assert (terminals[-1] if terminals else None) == result["terminal"]
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
        with (HERE / f"{name}.xcnf").open() as stream:
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
        wire_map = build_result["variants"][name]["wire_map"]
        masks = [sum(int(assignment[wire]) << bit for bit, wire in enumerate(bits))
                 for bits in wire_map["mask_bits"]]
        branches = [int(assignment[wire]) for wire in wire_map["root_branches"]]
        model = {"variables": variables, "cnf_clauses": cnf, "native_xor_rows": xor,
                 "masks": masks, "root_branch_bits": branches}
    elif result["status"] == "BOUNDED_UNKNOWN":
        assert result["stop_reason"] in ("WALL_CAP", "RSS_CAP") or result["terminal"] is None
    save(HERE / f"{name}.audit.json", {
        "status": "PASS_FROZEN_PIN_CONTROL_RECEIPT_AUDIT", "recorded_status": result["status"],
        "model_check": model, "result_sha256": sha(HERE / f"{name}.result.json")})
    print(name, "AUDITED", result["status"], flush=True)


if __name__ == "__main__":
    action = sys.argv[1]
    if action == "construct":
        construct()
    elif action == "freeze":
        freeze()
    elif action == "run":
        run(sys.argv[2])
    elif action == "audit":
        audit(sys.argv[2])
    else:
        raise ValueError(action)
