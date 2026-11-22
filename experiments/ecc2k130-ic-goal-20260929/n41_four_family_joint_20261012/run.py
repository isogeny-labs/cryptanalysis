"""Exact four-family, target-coupled N41 output search."""

import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
PARENT = GOAL / "n41_pair_image_bdd_20261012"
FOURPAIR = GOAL / "n131_w18_allseed_fourpair_20261012"
FUNCTIONAL = GOAL / "n41_w8_tenpair_functional_20261012"
FORWARD = GOAL / "n41_allseed_fourpair_forward_20261012"
SOURCE = FOURPAIR / "n41_diagonal/pairs.tsv"
FIXTURE = FOURPAIR / "n41_diagonal/control_fixture.json"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
sys.path[:0] = [str(PARENT), str(FOURPAIR), str(FUNCTIONAL)]
import build as output_build  # noqa: E402
import fourpair_v2 as source  # noqa: E402
from karatsuba_circuit import KaratsubaCircuit  # noqa: E402
_functional_spec = importlib.util.spec_from_file_location("family_functional_build", FUNCTIONAL / "build.py")
functional_build = importlib.util.module_from_spec(_functional_spec)
_functional_spec.loader.exec_module(functional_build)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, obj):
    with (HERE / name).open("x") as stream:
        json.dump(obj, stream, sort_keys=True, indent=2)
        stream.write("\n")


def plan():
    fixture = json.loads(FIXTURE.read_text())
    positive = [a ^ b for a, b in fixture["masks"]]
    rows, targets = output_build.load_pairs()
    assert targets[0][0] == fixture["target_reciprocal"]
    seeds = [sorted({r["masks"][0] ^ r["masks"][1] for r in slot}) for slot in rows]
    negative = []
    for index in range(2):
        chosen = []
        for slot in range(4):
            material = f"{fixture['target_reciprocal']}|{digest(SOURCE)}|{index}|{slot}"
            j = int(hashlib.sha256(material.encode()).hexdigest(), 16) % len(seeds[slot])
            chosen.append(seeds[slot][j])
        assert chosen != positive
        negative.append(chosen)
    paths = [Path(__file__), SOURCE, FIXTURE, SOLVER, PARENT / "build.py",
             FOURPAIR / "fourpair_v2.py", FORWARD / "build.py", FUNCTIONAL / "build.py",
             GOAL.parent / "koblitz-polynomial-w-pair-20260925/karatsuba_circuit.py"]
    save("protocol.json", {
        "status": "FROZEN_BEFORE_FOUR_FAMILY_QUERIES", "candidate_id": None,
        "curve_id": fixture["curve_id"], "public_target": fixture["public_target"],
        "target_reciprocal": fixture["target_reciprocal"],
        "positive_seed_tuple": positive, "negative_seed_tuples": negative,
        "selection_rule": "positive from prior checked chart; negative from target/source SHA-256",
        "families": "all source states whose two masks XOR to the selected seed",
        "solver_flags": ["--threads=1", "--maxtime=40", "--zero-exit-status", "--verb=1", "--printsol=1"],
        "parent_cap_seconds": 45, "rss_cap_bytes": 4 * 1024**3,
        "sources": {str(p): digest(p) for p in paths},
    })


def query(label):
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert all(digest(path) == sha for path, sha in protocol["sources"].items())
    seeds = (protocol["positive_seed_tuple"] if label == "positive" else
             protocol["negative_seed_tuples"][int(label[-1])])
    fixture = json.loads(FIXTURE.read_text())
    rows, _ = output_build.load_pairs()
    field, _, _ = source.field_config("n41")
    circuit = KaratsubaCircuit(41, [0, 3])
    outputs = []
    family_sizes = []
    for slot, seed in enumerate(seeds):
        states = [r for r in rows[slot] if r["masks"][0] ^ r["masks"][1] == seed]
        xs = sorted({r["point"][0] for r in states})
        values = {field.inverse(x) for x in xs}
        assert xs and all(xs)
        bits = [circuit.variable() for _ in range(41)]
        root, nodes = source.bdd(values, 41)
        source.emit_bdd(circuit, bits, root, nodes)
        outputs.append(bits)
        family_sizes.append({"states": len(states), "outputs": len(values), "bdd_nodes": len(nodes)})
        if label == "positive":
            assert fixture["pair_reciprocals"][slot] in values
    nodes = list(outputs)
    branches = []
    for left, right in ((0, 1), (2, 3), (4, 5)):
        out, branch = functional_build.s3_forward(circuit, nodes[left], nodes[right])
        nodes.append(out)
        branches.append(branch)
    circuit.require_zero(circuit.add(nodes[-1], circuit.constant(protocol["target_reciprocal"])))
    check = None
    if label == "positive":
        chart = json.loads((FORWARD / "chart.json").read_text())
        primary = {wire: value >> bit & 1 for bits, value in
                   zip(outputs, fixture["pair_reciprocals"]) for bit, wire in enumerate(bits)}
        primary.update({wire: bit for wire, bit in
                        zip(branches, chart["root_branch_bits"][4:])})
        assignment = output_build.prior_run.complete_assignment(circuit, primary)
        check = output_build.prior_run.check_assignment(circuit, assignment)
    formula = HERE / f"{label}.xcnf"
    circuit.write(formula)
    build = {"seed_tuple": seeds, "family_sizes": family_sizes,
             "variables": circuit.next_var - 1, "clauses": len(circuit.clauses),
             "xor_rows": len(circuit.xors), "formula_sha256": digest(formula),
             "formula_bytes": formula.stat().st_size, "positive_assignment_check": check,
             "output_wires": outputs, "branch_wires": branches}
    save(f"{label}_build.json", build)
    flags = protocol["solver_flags"]
    stdout, stderr = HERE / f"{label}.stdout", HERE / f"{label}.stderr"
    start = time.monotonic_ns()
    peak = 0
    stop = None
    with stdout.open("x") as out, stderr.open("x") as err:
        child = subprocess.Popen([str(SOLVER), *flags, str(formula)], stdout=out, stderr=err)
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
    save(f"{label}_result.json", {
        "status": status, "terminal": terminal, "stop_reason": stop,
        "exit_code": code, "wall_ns": time.monotonic_ns() - start,
        "peak_solver_rss_bytes": peak, "stdout_sha256": digest(stdout),
        "stderr_sha256": digest(stderr), "protocol_sha256": digest(HERE / "protocol.json"),
        "build_sha256": digest(HERE / f"{label}_build.json")})
    print(label, status, round((time.monotonic_ns()-start)/1e9, 3), flush=True)


if __name__ == "__main__":
    {"plan": lambda: plan(), "query": lambda: query(sys.argv[2])}[sys.argv[1]]()
