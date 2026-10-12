"""All-free N131 W18 nine-pair circuit with exact raw-fiber/Frobenius target choice.

Run freeze, control, then query. Each mode writes only new files here.
"""

import argparse
import hashlib
import json
import resource
import subprocess
import sys
import time
from fractions import Fraction
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / "n131_fixed_seed_ninepair_cubic_20261011"
GROUP = ROOT / "n131_fixed_seed_halftrace_cubic_20261011"
sys.path.insert(0, str(BASE))
import run as base  # noqa: E402
sys.path.insert(0, str(GROUP))
import verify as independent  # noqa: E402

N = 131
RAW_FIBERS = 4
CHOICES = N * RAW_FIBERS
TOTAL_CAP_NS = 600 * 10**9
RSS_CAP = 4 * 1024**3
SOLVER_FLAGS = ["--threads=1", "--maxtime=540", "--zero-exit-status",
                "--verb=1", "--printsol=1"]
TORSION = (None, (0, 1), (1, 0), (1, 1))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def multiply_by_four(point):
    doubled = independent.point_add(point, point)
    return independent.point_add(doubled, doubled)


def constructed_preimages(raw_target):
    point = tuple(raw_target)
    result = [point if torsion is None else independent.point_add(point, torsion)
              for torsion in TORSION]
    assert len(set(result)) == RAW_FIBERS
    assert len({multiply_by_four(row) for row in result}) == 1
    return result


def batch_inverse(values):
    assert values and all(values)
    prefix = [1]
    for value in values:
        prefix.append(independent.mul(prefix[-1], value))
    inverse_product = independent.inverse(prefix[-1])
    result = [0] * len(values)
    for index in range(len(values) - 1, -1, -1):
        result[index] = independent.mul(inverse_product, prefix[index])
        inverse_product = independent.mul(inverse_product, values[index])
    assert inverse_product == 1
    assert all(independent.mul(a, b) == 1 for a, b in zip(values, result))
    return result


def orbit_rows(preimages):
    assert len(preimages) == RAW_FIBERS
    assert len(set(map(tuple, preimages))) == RAW_FIBERS
    assert len({multiply_by_four(tuple(point)) for point in preimages}) == 1
    rows = []
    for fiber, point in enumerate(preimages):
        current = tuple(point)
        for rotation in range(N):
            assert current is not None and current[0] not in (0, 1)
            rows.append({"raw_preimage_index": fiber, "target_rotation": rotation,
                         "point": list(current)})
            current = (independent.square(current[0]), independent.square(current[1]))
        assert current == tuple(point)
    assert len(rows) == CHOICES and len({tuple(row["point"]) for row in rows}) == CHOICES
    inverse_x = batch_inverse([row["point"][0] for row in rows])
    for row, reciprocal in zip(rows, inverse_x):
        row["standard_reciprocal"] = reciprocal
    return rows


def build(target_reciprocals, bdd_root, bdd_nodes):
    assert len(target_reciprocals) == CHOICES
    pair = base.pair
    circuit = base.KaratsubaCircuit(pair.N, [0, 1, 2, 13])
    algebra = base.Algebra(circuit, base.Field(), dense_and_threshold=3000)
    h2 = pair.gf_square(pair.gf_half_trace(pair.coordinate(pair.SEED)))
    coefficient = 1 ^ h2
    selectors, outputs, rotated = [], [], []
    for rotation in base.ROTATIONS:
        bits = [circuit.variable() for _ in range(17)]
        out = [circuit.variable() for _ in range(pair.N)]
        selectors.append(bits)
        outputs.append(out)
        product = algebra.expression(zip(bits, pair.product_basis()))
        square_term = algebra.expression(
            (wire, pair.gf_mul(coefficient, pair.gf_square(1 << bit)))
            for bit, wire in enumerate(out))
        circuit.require_zero(algebra.add(
            algebra.mul(algebra.from_bits(out), product), square_term,
            algebra.expression(((-1, h2),))).bits())
        circuit.clauses.append(" ".join(map(str, out)) + " 0")
        images = [pair.gf_frobenius(1 << bit, rotation) for bit in range(pair.N)]
        rotated.append(algebra.from_bits(circuit.linear_element(out, images)))

    choices = [circuit.variable() for _ in target_reciprocals]
    circuit.clauses.append(" ".join(map(str, choices)) + " 0")
    for index, left in enumerate(choices):
        for right in choices[index + 1:]:
            circuit.clauses.append(f"-{left} -{right} 0")
    selected_target = algebra.expression(zip(choices, target_reciprocals))
    intermediates = [[circuit.variable() for _ in range(pair.N)] for _ in range(7)]
    branches = [circuit.variable() for _ in range(8)]
    ht_basis, trace_basis = [], []
    for bit in range(pair.N):
        value, image = pair.gf_square(1 << bit), 0
        for _ in range((pair.N + 1) // 2):
            image ^= value
            value = pair.gf_square(pair.gf_square(value))
        ht_basis.append(image)
        trace_basis.append(base.trace(1 << bit))
    running = rotated[0]
    for index in range(1, 9):
        output = (algebra.from_bits(intermediates[index - 1]) if index < 8
                  else selected_target)
        triple = algebra.mul(algebra.mul(running, rotated[index]), output)
        total = algebra.add(running, rotated[index], output)
        ht = circuit.linear_element(total.bits(), ht_basis)
        circuit.require_zero(algebra.add(
            triple, algebra.from_bits(ht),
            algebra.expression(((branches[index - 1], 1),))).bits())
        circuit.require_zero([circuit.xor(
            wire for wire, bit in zip(total.bits(), trace_basis) if bit)])
        if index < 8:
            circuit.clauses.append(" ".join(map(str, intermediates[index - 1])) + " 0")
        running = output

    for bits in selectors:
        literals = {0: 0, 1: -1}
        for node in sorted(bdd_nodes):
            bit, low, high = bdd_nodes[node]
            left, right = literals[low], literals[high]
            literals[node] = circuit.xor((
                left, circuit.and_(bits[bit], circuit.xor((left, right)))))
        circuit.clauses.append(str(literals[bdd_root]) + " 0")
    return circuit, {"selectors": selectors, "outputs": outputs,
                     "intermediates": intermediates, "branches": branches,
                     "choices": choices}


def sources():
    return {"runner": Path(__file__), "parent_runner": BASE / "run.py",
            "pair_circuit": base.OLD / "fixed_pair_circuit.py",
            "sparse_algebra": ROOT / "n41_basis_aware_quartic_20261011" / "sparse.py",
            "karatsuba": ROOT.parent / "koblitz-polynomial-w-pair-20260925" / "karatsuba_circuit.py",
            "circuit_sat": ROOT.parent / "koblitz-s5-invariant-20260924" / "circuit_sat.py",
            "group_arithmetic": GROUP / "verify.py", "support": base.SUPPORT,
            "source_count": BASE / "support_result.json",
            "source_interpretation": BASE / "support_interpretation.json",
            "fixture": BASE / "control_fixture.json", "target": base.OLD / "target_preimages.json",
            "solver": base.SOLVER.resolve()}


def freeze():
    target = base.target_record()
    assert len(orbit_rows([row["point"] for row in target["preimages"]])) == CHOICES
    _, root, nodes = base.source_domain()
    assert root >= 2 and len(nodes) == 13093 and base.SOLVER.is_file()
    counts = json.loads((BASE / "support_interpretation.json").read_text())
    n131 = next(row for row in counts["rows"] if row["label"] == "n131_w18_seed212")
    numerator, denominator = map(int, n131["pair_slots"]["9"]["labeled_mean_upper_ceiling"].split("/"))
    mean = Fraction(CHOICES * numerator, denominator)
    save("protocol.json", {"status": "FROZEN_N131_NINEPAIR_ORBIT_BEFORE_CONTROL_AND_QUERY",
                           "candidate_id": None, "curve_id": target["curve_id"],
                           "workload_id": target["workload_id"],
                           "public_target": target["public_target"],
                           "fixed_seed_mask": base.pair.SEED,
                           "free_pair_rotations": base.ROTATIONS,
                           "source_codes_per_slot": 33191,
                           "raw_preimage_count": RAW_FIBERS,
                           "frobenius_rotations": N,
                           "target_choice_count": CHOICES,
                           "selection_law": "one hot among all four raw preimages and all 131 Frobenius conjugates of one public point",
                           "labeled_mean_upper_ceiling_exact": f"{mean.numerator}/{mean.denominator}",
                           "worker_count": 1,
                           "total_target_dependent_cap_seconds": TOTAL_CAP_NS // 10**9,
                           "combined_rss_cap_bytes": RSS_CAP,
                           "solver_flags": SOLVER_FLAGS,
                           "source_sha256": {name: sha(path) for name, path in sources().items()}})


def protocol():
    record = json.loads((HERE / "protocol.json").read_text())
    assert record["status"] == "FROZEN_N131_NINEPAIR_ORBIT_BEFORE_CONTROL_AND_QUERY"
    assert record["source_sha256"] == {name: sha(path) for name, path in sources().items()}
    return record


def control():
    frozen = protocol()
    codes, root, nodes = base.source_domain()
    chain = json.loads((BASE / "control_fixture.json").read_text())
    rows = orbit_rows(constructed_preimages(chain["raw_target"]))
    target_a = base.standard_reciprocal(chain["raw_target_z"])
    assert rows[0]["standard_reciprocal"] == target_a
    start = time.monotonic_ns()
    circuit, wires = build([row["standard_reciprocal"] for row in rows], root, nodes)
    constructed = time.monotonic_ns()
    formula = HERE / "control.xcnf"
    circuit.write(formula)
    written = time.monotonic_ns()
    initial = {}
    def bind(bits, value):
        initial.update({wire: value >> bit & 1 for bit, wire in enumerate(bits)})
    h2 = base.pair.gf_square(base.pair.gf_half_trace(base.pair.coordinate(base.pair.SEED)))
    for item in chain["selected"]:
        slot = item["slot"]
        code = base.pair.selector_code(item["masks"][0])
        assert code in codes
        a = base.standard_reciprocal(item["unrotated_pair_output_z"])
        product = base.pair.product_from_code(code)
        assert (base.pair.gf_mul(1 ^ h2, base.pair.gf_square(a)) ^
                base.pair.gf_mul(a, product) ^ h2) == 0
        bind(wires["selectors"][slot], code)
        bind(wires["outputs"][slot], a)
    for bits, z in zip(wires["intermediates"], chain["intermediate_z"]):
        bind(bits, base.standard_reciprocal(z))
    for index, wire in enumerate(wires["choices"]):
        initial[wire] = int(index == 0)
    rotated = [base.standard_reciprocal(z) for z in chain["pair_rotated_z"]]
    middle = [base.standard_reciprocal(z) for z in chain["intermediate_z"]]
    left, branch_bits = rotated[0], []
    for index in range(1, 9):
        right = middle[index - 1] if index < 8 else target_a
        total = left ^ rotated[index] ^ right
        branch = (base.pair.gf_mul(base.pair.gf_mul(left, rotated[index]), right) ^
                  base.halftrace(base.pair.gf_square(total)))
        assert branch in (0, 1)
        initial[wires["branches"][index - 1]] = branch
        branch_bits.append(branch)
        left = right
    checked = base.check_assignment(circuit, base.complete_assignment(circuit, initial))
    save("control_result.json", {"status": "PASS_FULL_N131_NINEPAIR_ORBIT_CONSTRUCTED_WITNESS",
                                 "candidate_id": None,
                                 "selected_choice": 0,
                                 "constructed_public_target": list(multiply_by_four(tuple(chain["raw_target"]))),
                                 "raw_preimages": [list(point) for point in constructed_preimages(chain["raw_target"])],
                                 "target_choice_count": len(rows),
                                 "distinct_target_reciprocals": len({row["standard_reciprocal"] for row in rows}),
                                 "source_pair_checks": len(chain["selected"]),
                                 "group_link_checks": len(branch_bits),
                                 "branch_bits": branch_bits,
                                 "assignment_check": checked,
                                 "formula": base.profile(circuit, formula,
                                                         (constructed-start)/1e9,
                                                         (written-constructed)/1e9),
                                 "protocol_sha256": sha(HERE / "protocol.json")})
    print("PASS_FULL_N131_NINEPAIR_ORBIT_CONSTRUCTED_WITNESS", flush=True)


def query():
    frozen = protocol()
    assert json.loads((HERE / "control_result.json").read_text())["status"] == "PASS_FULL_N131_NINEPAIR_ORBIT_CONSTRUCTED_WITNESS"
    target = base.target_record()
    t0 = time.monotonic_ns()
    rows = orbit_rows([row["point"] for row in target["preimages"]])
    t1 = time.monotonic_ns()
    _, root, nodes = base.source_domain()
    circuit, wires = build([row["standard_reciprocal"] for row in rows], root, nodes)
    t2 = time.monotonic_ns()
    formula = HERE / "ordinary.xcnf"
    circuit.write(formula)
    t3 = time.monotonic_ns()
    profile = base.profile(circuit, formula, (t2-t1)/1e9, (t3-t2)/1e9)
    assert profile["variables"] < 700000 and profile["xcnf_bytes"] < 50000000
    del circuit
    outpath, errpath = HERE / "solver.stdout.txt", HERE / "solver.stderr.txt"
    parent = psutil.Process()
    peak, stop = 0, None
    with outpath.open("x") as stdout, errpath.open("x") as stderr:
        process = subprocess.Popen([str(base.SOLVER), *SOLVER_FLAGS, str(formula)],
                                   stdout=stdout, stderr=stderr)
        child = psutil.Process(process.pid)
        while process.poll() is None:
            try:
                combined = parent.memory_info().rss + child.memory_info().rss
            except psutil.NoSuchProcess:
                combined = parent.memory_info().rss
            peak = max(peak, combined)
            if combined > RSS_CAP:
                stop = "RSS_CAP"
            elif time.monotonic_ns() - t0 >= TOTAL_CAP_NS:
                stop = "TOTAL_QUERY_TIMEOUT"
            if stop:
                process.kill()
                break
            time.sleep(0.05)
        code = process.wait()
    t4 = time.monotonic_ns()
    output = outpath.read_text(errors="replace")
    status = ("BOUNDED_UNKNOWN" if stop else
              "SAT_PENDING_GROUP_REPLAY" if "s SATISFIABLE" in output else
              "UNSAT" if "s UNSATISFIABLE" in output else "BOUNDED_UNKNOWN")
    decoded = None
    if status == "SAT_PENDING_GROUP_REPLAY":
        positive = {int(token) for line in output.splitlines() if line.startswith("v ")
                    for token in line.split()[1:] if token.isdigit() and int(token) > 0}
        def decode(bits):
            return sum(int(wire in positive) << bit for bit, wire in enumerate(bits))
        selected = [index for index, wire in enumerate(wires["choices"]) if wire in positive]
        assert len(selected) == 1
        decoded = {"selected_codes": [decode(bits) for bits in wires["selectors"]],
                   "pair_standard_reciprocals": [decode(bits) for bits in wires["outputs"]],
                   "intermediate_standard_reciprocals": [decode(bits) for bits in wires["intermediates"]],
                   "branch_bits": [int(wire in positive) for wire in wires["branches"]],
                   "raw_preimage_index": rows[selected[0]]["raw_preimage_index"],
                   "target_rotation": rows[selected[0]]["target_rotation"],
                   "formula_sha256": profile["xcnf_sha256"]}
        save("decoded_model.json", decoded)
    t5 = time.monotonic_ns()
    phases = {"target_orbit_and_fibers_ns": t1-t0,
              "formula_construction_ns": t2-t1,
              "formula_serialization_ns": t3-t2,
              "solver_search_ns": t4-t3,
              "terminal_parse_and_decode_ns": t5-t4}
    assert sum(phases.values()) == t5-t0
    save("query_result.json", {"status": status, "candidate_id": None,
                               "curve_id": frozen["curve_id"],
                               "workload_id": frozen["workload_id"],
                               "public_target": frozen["public_target"],
                               "target_choice_count": CHOICES,
                               "distinct_target_reciprocals": len({row["standard_reciprocal"] for row in rows}),
                               "phase_ns": phases,
                               "target_dependent_attempt_ns": t5-t0,
                               "formula": profile, "worker_count": 1,
                               "solver_flags": SOLVER_FLAGS,
                               "solver_exit_code": code, "stop_reason": stop,
                               "peak_combined_rss_bytes_sampled": peak,
                               "status_lines": [line for line in output.splitlines() if line.startswith("s ")],
                               "restart_rows": sum(line.startswith("c [") for line in output.splitlines()),
                               "decoded_model_saved": decoded is not None,
                               "stdout_sha256": sha(outpath), "stderr_sha256": sha(errpath),
                               "protocol_sha256": sha(HERE / "protocol.json")})
    print(json.dumps({"status": status, "target_dependent_seconds": (t5-t0)/1e9,
                      "peak_combined_rss_bytes": peak}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "control", "query"))
    {"freeze": freeze, "control": control, "query": query}[parser.parse_args().mode]()
