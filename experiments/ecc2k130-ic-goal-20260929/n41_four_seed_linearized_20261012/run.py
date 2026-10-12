"""Four fixed seed sums in the compact all-source N41 public circuit."""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
SOURCE = GOAL / "n131_w18_allseed_fourpair_20261012"
PANEL = GOAL / "n41_four_family_joint_20261012"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
sys.path.insert(0, str(SOURCE))
import fourpair_v2  # noqa: E402


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def panel():
    prior = json.loads((PANEL / "protocol.json").read_text())
    return [prior["positive_seed_tuple"], *prior["negative_seed_tuples"]]


def freeze():
    fixture = json.loads((SOURCE / "n41_diagonal/control_fixture.json").read_text())
    tuples = panel()
    assert tuples[0] == [a ^ b for a, b in fixture["masks"]]
    paths = [Path(__file__), SOURCE / "fourpair_v2.py",
             SOURCE / "n41_diagonal/control_fixture.json",
             GOAL / "n41_w7_entropy_cubic_20261011/w8/geometry.json",
             GOAL.parent / "koblitz-polynomial-w-pair-20260925/karatsuba_circuit.py",
             GOAL / "n41_basis_aware_quartic_20261011/sparse.py",
             PANEL / "protocol.json", SOLVER]
    save("protocol.json", {
        "status": "FROZEN_BEFORE_COMPACT_FOUR_SEED_PANEL", "candidate_id": None,
        "curve_id": fixture["curve_id"], "target_reciprocal": fixture["target_reciprocal"],
        "public_target": fixture["public_target"], "seed_tuples": tuples,
        "seed_constraint": "for each slot and bit, mask_a XOR mask_b equals selected seed bit",
        "solver_flags": ["--threads=1", "--maxtime=40", "--zero-exit-status", "--verb=1", "--printsol=1"],
        "workers": 1, "parent_cap_seconds": 45, "rss_cap_bytes": 4 * 1024**3,
        "sources": {str(path): sha(path) for path in paths}})


def build(index):
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert all(sha(path) == value for path, value in protocol["sources"].items())
    fixture = json.loads((SOURCE / "n41_diagonal/control_fixture.json").read_text())
    seeds = protocol["seed_tuples"][index]
    start = time.monotonic_ns()
    circuit, wires, meta = fourpair_v2.build("n41", fixture["target_reciprocal"])
    for slot, seed in enumerate(seeds):
        for bit, (left, right) in enumerate(zip(wires["masks"][2*slot], wires["masks"][2*slot+1])):
            # XCNF rows demand odd literal parity. Negating one literal sets an even XOR.
            circuit.xors.append(f"x {left if seed >> bit & 1 else -left} {right} 0")
    check = None
    if index == 0:
        field, _, rotations = fourpair_v2.field_config("n41")
        check = fourpair_v2.check_assignment(circuit, wires, fixture, field, rotations)
    path = HERE / f"case_{index}.xcnf"
    circuit.write(path)
    save(f"case_{index}_build.json", {
        "status": "PASS_EXACT_SEED_SUM_FORMULA", "seed_tuple": seeds,
        "variables": circuit.next_var - 1, "and_gates": circuit.and_count,
        "cnf_clauses": len(circuit.clauses), "xor_rows": len(circuit.xors),
        "seed_xor_rows": 32, "mask_wires": wires["masks"],
        "pair_output_wires": wires["pair_outputs"], "middle_wires": wires["middle"],
        "formula_sha256": sha(path), "formula_bytes": path.stat().st_size,
        "construction_ns": time.monotonic_ns() - start, "positive_assignment_check": check,
        "source_metadata": meta, "protocol_sha256": sha(HERE / "protocol.json")})
    print("BUILT", index, circuit.next_var - 1, len(circuit.clauses), len(circuit.xors), flush=True)


def query(index):
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert all(sha(path) == value for path, value in protocol["sources"].items())
    build_result = json.loads((HERE / f"case_{index}_build.json").read_text())
    formula = HERE / f"case_{index}.xcnf"
    assert sha(formula) == build_result["formula_sha256"]
    stdout, stderr = HERE / f"case_{index}.stdout", HERE / f"case_{index}.stderr"
    start = time.monotonic_ns()
    peak, stop = 0, None
    with stdout.open("x") as out, stderr.open("x") as err:
        child = subprocess.Popen([str(SOLVER), *protocol["solver_flags"], str(formula)],
                                  stdout=out, stderr=err)
        proc = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                peak = max(peak, proc.memory_info().rss)
            except psutil.NoSuchProcess:
                pass
            if peak > protocol["rss_cap_bytes"]:
                stop = "RSS_CAP"
            if time.monotonic_ns() - start > protocol["parent_cap_seconds"] * 10**9:
                stop = "WALL_CAP"
            if stop:
                child.kill()
                break
            time.sleep(.025)
        code = child.wait()
    terminals = [line for line in stdout.read_text(errors="replace").splitlines()
                 if line.startswith("s ")]
    terminal = terminals[-1] if terminals else None
    status = ("SAT_PENDING_REPLAY" if terminal == "s SATISFIABLE" else
              "UNSAT" if terminal == "s UNSATISFIABLE" else
              "BOUNDED_UNKNOWN" if stop or terminal in (None, "s INDETERMINATE") else
              "PRODUCER_FAILURE")
    save(f"case_{index}_result.json", {
        "status": status, "terminal": terminal, "stop_reason": stop,
        "exit_code": code, "wall_ns": time.monotonic_ns()-start,
        "peak_solver_rss_bytes": peak,
        "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr),
        "build_sha256": sha(HERE / f"case_{index}_build.json"),
        "protocol_sha256": sha(HERE / "protocol.json")})
    print("RESULT", index, status, flush=True)


if __name__ == "__main__":
    action = sys.argv[1]
    if action == "freeze":
        freeze()
    elif action == "build":
        build(int(sys.argv[2]))
    elif action == "query":
        query(int(sys.argv[2]))
    else:
        raise ValueError(action)
