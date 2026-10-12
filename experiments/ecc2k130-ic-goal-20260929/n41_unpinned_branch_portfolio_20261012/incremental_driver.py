"""Frozen one-worker parent for the CryptoMiniSat assumption portfolio."""

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
LADDER = GOAL / "n41_allseed_fourpair_pin_ladder_20261012"
SOLVER = HERE / "incremental"
LIBRARY = Path("/opt/homebrew/lib/libcryptominisat5.dylib")
RSS_CAP = 4 * 1024**3
CONTROL_NS = 35 * 10**9
QUERY_NS = 190 * 10**9
CPU_SECONDS_PER_SOLVE = 1.0


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, obj):
    with path.open("x") as out:
        json.dump(obj, out, sort_keys=True, indent=2)
        out.write("\n")


def freeze():
    parent_protocol = json.loads((HERE / "protocol.json").read_text())
    wires = parent_protocol["root_branch_wires"]
    assert len(wires) == 7
    paths = (Path(__file__), HERE / "incremental.cpp", SOLVER, LIBRARY,
             PARENT / "n41_public.xcnf", LADDER / "all_pair.xcnf",
             HERE / "protocol.json", PARENT / "audit_result.json")
    save(HERE / "incremental_protocol.json", {
        "status": "FROZEN_BEFORE_INCREMENTAL_CONTROL_AND_UNPINNED_QUERY",
        "candidate_id": None, "workers": 1, "root_branch_wires": wires,
        "branch_order": list(range(128)), "control_pattern": 73,
        "control_wall_cap_ns": CONTROL_NS, "query_wall_cap_ns": QUERY_NS,
        "cpu_seconds_per_solve": CPU_SECONDS_PER_SOLVE,
        "rss_cap_bytes": RSS_CAP,
        "compile_command": "clang++ -std=c++17 -O2 -I/opt/homebrew/include -L/opt/homebrew/lib incremental.cpp -lcryptominisat5 -o incremental",
        "sources": {str(path): sha(path) for path in paths}})


def command(mode, wires):
    control = mode == "control"
    formula = LADDER / "all_pair.xcnf" if control else PARENT / "n41_public.xcnf"
    first, last = (73, 74) if control else (0, 128)
    return [str(SOLVER), str(formula), str(HERE / f"{mode}_"),
            str(CPU_SECONDS_PER_SOLVE), str(first), str(last),
            *(str(wire) for wire in wires)]


def run(mode):
    assert mode in ("control", "query")
    protocol = json.loads((HERE / "incremental_protocol.json").read_text())
    assert all(sha(path) == digest for path, digest in protocol["sources"].items())
    if mode == "query":
        control = json.loads((HERE / "control_audit.json").read_text())
        assert control["status"] == "PASS_INCREMENTAL_PINNED_MODEL_AUDIT"
    cap = CONTROL_NS if mode == "control" else QUERY_NS
    stdout, stderr = HERE / f"{mode}.stdout", HERE / f"{mode}.stderr"
    parent, peak, stop = psutil.Process(), 0, None
    start = time.monotonic_ns()
    with stdout.open("x") as out, stderr.open("x") as err:
        child = subprocess.Popen(command(mode, protocol["root_branch_wires"]),
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
            if time.monotonic_ns() - start > cap:
                stop = "WALL_CAP"
            if stop:
                child.kill()
                break
            time.sleep(.025)
        code = child.wait()
    lines = stdout.read_text(errors="replace").splitlines()
    loads = [line for line in lines if line.startswith("LOAD ")]
    slices = [line for line in lines if line.startswith("SLICE ")]
    models = [line for line in lines if line.startswith("MODEL ")]
    if models:
        status = "SAT_PENDING_REPLAY"
    elif code not in (0, -9):
        status = "PRODUCER_FAILURE"
    elif mode == "query" and len(slices) == 128 and all(line.split()[2] == "UNSAT" for line in slices):
        status = "COMPLETE_UNSAT"
    else:
        status = "BOUNDED_UNKNOWN"
    save(HERE / f"{mode}_result.json", {
        "status": status, "stop_reason": stop, "exit_code": code,
        "wall_ns": time.monotonic_ns() - start,
        "peak_combined_rss_bytes": peak,
        "loads": loads, "slice_count": len(slices), "model_rows": models,
        "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr),
        "protocol_sha256": sha(HERE / "incremental_protocol.json")})
    print(mode, status, len(slices), flush=True)


def audit(mode):
    protocol = json.loads((HERE / "incremental_protocol.json").read_text())
    result = json.loads((HERE / f"{mode}_result.json").read_text())
    assert all(sha(path) == digest for path, digest in protocol["sources"].items())
    assert result["protocol_sha256"] == sha(HERE / "incremental_protocol.json")
    stdout, stderr = HERE / f"{mode}.stdout", HERE / f"{mode}.stderr"
    assert result["stdout_sha256"] == sha(stdout)
    assert result["stderr_sha256"] == sha(stderr)
    lines = stdout.read_text(errors="replace").splitlines()
    loads = [line for line in lines if line.startswith("LOAD ")]
    slices = [line for line in lines if line.startswith("SLICE ")]
    models = [line for line in lines if line.startswith("MODEL ")]
    assert loads == result["loads"] and len(slices) == result["slice_count"]
    assert models == result["model_rows"]
    model_check = None
    if models:
        assert len(models) == 1 and len(slices) >= 1
        index = int(models[0].split()[1])
        assert index == int(slices[-1].split()[1]) and slices[-1].split()[2] == "SAT"
        model_path = HERE / f"{mode}_{index}.model"
        values = [int(line) for line in model_path.read_text().splitlines()]
        assignment = {abs(lit): lit > 0 for lit in values}
        formula = LADDER / "all_pair.xcnf" if mode == "control" else PARENT / "n41_public.xcnf"
        with formula.open() as stream:
            head = stream.readline().split()
            assert head[:2] == ["p", "cnf"]
            variables, rows = map(int, head[2:])
            assert len(values) == variables and set(assignment) == set(range(1, variables + 1))
            cnf = xor = 0
            for line in stream:
                parts = line.split()
                is_xor = parts[0] == "x"
                lits = list(map(int, parts[1 if is_xor else 0:-1]))
                assert parts[-1] == "0" and lits
                true_lits = [assignment[abs(lit)] == (lit > 0) for lit in lits]
                assert (sum(true_lits) & 1) if is_xor else any(true_lits)
                if is_xor:
                    xor += 1
                else:
                    cnf += 1
            assert cnf + xor == rows
        assert all(assignment[wire] == bool(index >> bit & 1)
                   for bit, wire in enumerate(protocol["root_branch_wires"]))
        model_check = {"index": index, "variables": variables,
                       "cnf_clauses": cnf, "native_xor_rows": xor,
                       "model_sha256": sha(model_path)}
    if mode == "control":
        assert result["status"] == "SAT_PENDING_REPLAY" and model_check["index"] == 73
        status = "PASS_INCREMENTAL_PINNED_MODEL_AUDIT"
    else:
        status = "PASS_INCREMENTAL_UNPINNED_RECEIPT_AUDIT"
    save(HERE / f"{mode}_audit.json", {
        "status": status, "recorded_status": result["status"],
        "model_check": model_check,
        "result_sha256": sha(HERE / f"{mode}_result.json")})
    print(mode, "AUDITED", result["status"])


if __name__ == "__main__":
    action = sys.argv[1]
    if action == "freeze":
        freeze()
    elif action in ("run", "audit"):
        {"run": run, "audit": audit}[action](sys.argv[2])
    else:
        raise ValueError(action)
