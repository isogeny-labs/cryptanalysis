"""Two-pair pinned diagnostic on the same public target; not a natural-yield query."""

import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("fourpair_forward_build", HERE / "build.py")
build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build)
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
FLAGS = ("--threads=1", "--maxtime=60", "--zero-exit-status", "--verb=1", "--printsol=1")
WALL_NS = 65 * 10**9
RSS_CAP = 4 * 1024**3


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with path.open("x") as out:
        json.dump(value, out, sort_keys=True, indent=2)
        out.write("\n")


def construct():
    chart = json.loads((HERE / "chart.json").read_text())
    target = chart["target_reciprocal"]
    circuit, wires, meta = build.formula("n41", target)
    for bits, mask in zip(wires["masks"][:4], chart["masks"][:4]):
        for bit, wire in enumerate(bits):
            circuit.clauses.append(f"{wire if mask >> bit & 1 else -wire} 0")
    output = HERE / "two_pair_pinned.xcnf"
    circuit.write(output)
    save(HERE / "pin_build.json", {
        "status": "PASS_TWO_PAIR_PIN_CONTROL_BUILT", "candidate_id": None,
        "pinned_source_masks": 4, "pinned_source_pairs": 2,
        "remaining_source_masks": 4, "free_root_branches": 7,
        "metadata": meta, "variables": circuit.next_var - 1,
        "cnf_clauses": len(circuit.clauses), "native_xor_rows": len(circuit.xors),
        "formula_sha256": sha(output)})
    print("PASS_TWO_PAIR_PIN_CONTROL_BUILT", circuit.next_var - 1, flush=True)


def freeze():
    paths = (HERE / "pin_control.py", HERE / "build.py", HERE / "chart.json",
             HERE / "audit_result.json", HERE / "pin_build.json",
             HERE / "two_pair_pinned.xcnf", SOLVER)
    save(HERE / "pin_protocol.json", {
        "status": "FROZEN_BEFORE_PIN_DIAGNOSTIC", "candidate_id": None,
        "workers": 1, "wall_cap_ns": WALL_NS, "rss_cap_bytes": RSS_CAP,
        "flags": FLAGS, "sources": {str(path): sha(path) for path in paths}})


def run():
    protocol = json.loads((HERE / "pin_protocol.json").read_text())
    for path, digest in protocol["sources"].items():
        assert sha(path) == digest, path
    start = time.monotonic_ns()
    stop = None
    peak = 0
    with (HERE / "pin_solver.stdout").open("x") as out, \
         (HERE / "pin_solver.stderr").open("x") as err:
        child = subprocess.Popen([str(SOLVER), *FLAGS,
                                  str(HERE / "two_pair_pinned.xcnf")], stdout=out, stderr=err)
        proc = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                rss = proc.memory_info().rss + psutil.Process().memory_info().rss
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
            time.sleep(.025)
        code = child.wait()
    stdout = HERE / "pin_solver.stdout"
    lines = stdout.read_text(errors="replace").splitlines()
    terminals = [line for line in lines if line.startswith("s ")]
    terminal = terminals[-1] if terminals else None
    status = ("SAT_PENDING_REPLAY" if terminal == "s SATISFIABLE" else
              "UNSAT" if terminal == "s UNSATISFIABLE" else "BOUNDED_UNKNOWN")
    save(HERE / "pin_result.json", {
        "status": status, "terminal": terminal, "stop_reason": stop,
        "exit_code": code, "wall_ns": time.monotonic_ns() - start,
        "peak_combined_rss_bytes": peak,
        "restart_rows": sum(line.startswith("c rst") for line in lines),
        "stdout_sha256": sha(stdout), "stderr_sha256": sha(HERE / "pin_solver.stderr"),
        "protocol_sha256": sha(HERE / "pin_protocol.json")})
    print(status, flush=True)


if __name__ == "__main__":
    {"construct": construct, "freeze": freeze, "run": run}[sys.argv[1]]()
