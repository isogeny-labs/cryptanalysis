"""One-worker frozen public-point query for the seven-pair eliminant circuit."""

import argparse
import hashlib
import json
import resource
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / "n131_fixed_seed_ninepair_cubic_20261011"
sys.path[:0] = [str(HERE), str(BASE)]
import circuit as operator  # noqa: E402
base = operator.base

RSS_CAP = 4 * 1024**3
PARENT_CAP = 600
SOLVER_CAP = 520
FLAGS = ["--threads=1", "--maxtime=520", "--zero-exit-status", "--verb=1", "--printsol=1"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inputs():
    return {"source": HERE / "query.py", "operator": HERE / "circuit.py",
            "source_protocol": HERE / "protocol.json",
            "control": HERE / "control_result.json",
            "base": BASE / "run.py", "pair": base.OLD / "fixed_pair_circuit.py",
            "support": base.SUPPORT,
            "pool": ROOT / "n131_w18_terminal_fiber_20261011/pool.json",
            "target": base.OLD / "target_preimages.json",
            "sparse": ROOT / "n41_basis_aware_quartic_20261011/sparse.py",
            "karatsuba": ROOT.parent / "koblitz-polynomial-w-pair-20260925/karatsuba_circuit.py",
            "circuit_sat": ROOT.parent / "koblitz-s5-invariant-20260924/circuit_sat.py",
            "runtime": HERE / "sage_runtime_info.json", "solver": base.SOLVER.resolve()}


def save(name, data):
    with (HERE / name).open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def freeze():
    source = json.loads((HERE / "protocol.json").read_text())
    control = json.loads((HERE / "control_result.json").read_text())
    target = base.target_record()
    assert source["status"] == "FROZEN_SEVENPAIR_ELIMINANT_BEFORE_BUILD"
    assert control["status"] == "PASS_SEVENPAIR_ELIMINANT_CONSTRUCTED_WITNESS"
    assert source["curve_id"] == target["curve_id"]
    assert control["formula"]["and_gates"] < 500000
    assert base.SOLVER.is_file()
    save("query_protocol.json", {
        "status": "FROZEN_SEVENPAIR_ELIMINANT_PUBLIC_QUERY",
        "candidate_id": None, "curve_id": source["curve_id"],
        "workload_id": source["workload_id"],
        "public_target": source["public_target"],
        "raw_preimage_index": 0, "workers": 1,
        "parent_cap_seconds": PARENT_CAP, "solver_cap_seconds": SOLVER_CAP,
        "rss_cap_bytes": RSS_CAP, "solver_flags": FLAGS,
        "sha256": {name: sha(path) for name, path in inputs().items()},
    })
    print("FROZEN_SEVENPAIR_ELIMINANT_PUBLIC_QUERY", flush=True)


def run():
    protocol = json.loads((HERE / "query_protocol.json").read_text())
    assert protocol["status"] == "FROZEN_SEVENPAIR_ELIMINANT_PUBLIC_QUERY"
    assert protocol["sha256"] == {name: sha(path) for name, path in inputs().items()}
    assert protocol["workers"] == 1 and protocol["rss_cap_bytes"] == RSS_CAP
    _, bdd_root, bdd_nodes = base.source_domain()
    public = base.target_record()
    assert public["public_target"] == protocol["public_target"]
    start = time.monotonic_ns()
    target_a = base.standard_reciprocal(public["preimages"][0]["reciprocal_x_z"])
    target_ready = time.monotonic_ns()
    circuit, wires = operator.build(target_a, bdd_root, bdd_nodes)
    built = time.monotonic_ns()
    peak_build = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != "darwin":
        peak_build *= 1024
    assert peak_build < RSS_CAP
    formula_path = HERE / "ordinary.xcnf"
    circuit.write(formula_path)
    written = time.monotonic_ns()
    profile = base.profile(circuit, formula_path, (built-target_ready)/1e9,
                           (written-built)/1e9)
    assert profile["xcnf_bytes"] < 100000000
    del circuit
    remaining = PARENT_CAP - (written-start)/1e9
    assert remaining > 30
    outpath, errpath = HERE / "solver.stdout.txt", HERE / "solver.stderr.txt"
    parent = psutil.Process()
    sampled_peak, reason = 0, None
    solver_start = time.monotonic_ns()
    with outpath.open("x") as stdout, errpath.open("x") as stderr:
        process = subprocess.Popen([str(base.SOLVER), *FLAGS, str(formula_path)],
                                   stdout=stdout, stderr=stderr)
        child = psutil.Process(process.pid)
        while process.poll() is None:
            try:
                combined = parent.memory_info().rss + child.memory_info().rss
            except psutil.NoSuchProcess:
                combined = parent.memory_info().rss
            sampled_peak = max(sampled_peak, combined)
            if combined > RSS_CAP:
                reason = "RSS_CAP"
                process.kill()
                break
            if (time.monotonic_ns()-start)/1e9 > PARENT_CAP:
                reason = "PARENT_TIMEOUT"
                process.kill()
                break
            time.sleep(0.05)
        exit_code = process.wait()
    solver_end = time.monotonic_ns()
    stdout = outpath.read_text(errors="replace")
    status = ("BOUNDED_UNKNOWN" if reason else
              "SAT_PENDING_GROUP_REPLAY" if "s SATISFIABLE" in stdout else
              "UNSAT" if "s UNSATISFIABLE" in stdout else
              "BOUNDED_UNKNOWN")
    decoded = None
    if status == "SAT_PENDING_GROUP_REPLAY":
        positive = {int(token) for line in stdout.splitlines() if line.startswith("v ")
                    for token in line.split()[1:] if token.isdigit() and int(token) > 0}
        def decode(bits):
            return sum(int(wire in positive) << bit for bit, wire in enumerate(bits))
        decoded = {"first_code": decode(wires["first_code"]),
                   "free_codes": [decode(bits) for bits in wires["selectors"]],
                   "free_pair_reciprocals": [decode(bits) for bits in wires["pair_outputs"]],
                   "terminal_choice_bits": [int(wire in positive) for wire in wires["choices"]],
                   "middle_reciprocals": [decode(bits) for bits in wires["middle"]],
                   "block_reciprocal": decode(wires["block"]),
                   "branch_bits": [int(wire in positive) for wire in wires["branches"]],
                   "formula_sha256": profile["xcnf_sha256"]}
        save("decoded_model.json", decoded)
    result = {"status": status, "candidate_id": None,
              "curve_id": protocol["curve_id"], "workload_id": protocol["workload_id"],
              "public_target": protocol["public_target"], "raw_preimage_index": 0,
              "target_standard_reciprocal": target_a,
              "formula": profile, "solver_flags": FLAGS, "worker_count": 1,
              "solver_started": True, "solver_exit_code": exit_code,
              "stop_reason": reason,
              "sampled_peak_combined_rss_bytes": sampled_peak,
              "phases_ns": {"target_query": target_ready-start,
                            "formula_build": built-target_ready,
                            "formula_write": written-built,
                            "solver": solver_end-solver_start,
                            "result_parse": time.monotonic_ns()-solver_end},
              "status_lines": [line for line in stdout.splitlines() if line.startswith("s ")],
              "restart_rows": sum(line.startswith("c [") for line in stdout.splitlines()),
              "decoded_model_saved": decoded is not None,
              "stdout_sha256": sha(outpath), "stderr_sha256": sha(errpath),
              "protocol_sha256": sha(HERE / "query_protocol.json")}
    result["charged_query_wall_ns"] = sum(result["phases_ns"].values())
    save("query_result.json", result)
    print(json.dumps({"status": status,
                      "solver_seconds": result["phases_ns"]["solver"]/1e9,
                      "peak_combined_rss_bytes": sampled_peak,
                      "restart_rows": result["restart_rows"]}, sort_keys=True), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "run"))
    globals()[parser.parse_args().mode]()
