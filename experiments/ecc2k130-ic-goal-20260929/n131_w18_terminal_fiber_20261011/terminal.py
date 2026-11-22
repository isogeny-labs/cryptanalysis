"""Eight W18 pairs with a target-conditioned 32-state terminal residual."""

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
VERIFY = ROOT / "n131_fixed_seed_halftrace_cubic_20261011"
sys.path.insert(0, str(BASE))
import run as base  # noqa: E402
sys.path.insert(0, str(VERIFY))
import verify as independent  # noqa: E402
import prepare  # noqa: E402

ROTATIONS = base.ROTATIONS[:8]
SOLVER_CAP = 180
PARENT_CAP = 195
SOLVER_FLAGS = ["--threads=1", "--maxtime=180", "--zero-exit-status",
                "--verb=1", "--printsol=1"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, data):
    with (HERE / name).open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def sources():
    return {"terminal": Path(__file__), "preparer": HERE / "prepare.py",
            "pool": HERE / "pool.json", "source_count": HERE / "source_count.json",
            "serial": BASE / "run.py", "pair": base.OLD / "fixed_pair_circuit.py",
            "sparse": ROOT / "n41_basis_aware_quartic_20261011" / "sparse.py",
            "karatsuba": ROOT.parent / "koblitz-polynomial-w-pair-20260925" / "karatsuba_circuit.py",
            "circuit_sat": ROOT.parent / "koblitz-s5-invariant-20260924" / "circuit_sat.py",
            "support": base.SUPPORT, "fixture": BASE / "control_fixture.json",
            "group": VERIFY / "verify.py", "target": base.OLD / "target_preimages.json",
            "solver": base.SOLVER.resolve()}


def pool():
    data = json.loads((HERE / "pool.json").read_text())
    assert data["status"] == "PASS_FROZEN_TARGET_INDEPENDENT_TERMINAL_POOL"
    assert len(data["states"]) == 32
    return data


def freeze():
    target = base.target_record()
    counts = json.loads((HERE / "source_count.json").read_text())
    assert counts["status"] == "PASS_EXACT_SELECTED_TERMINAL_SOURCE_COUNT"
    _, root, nodes = base.source_domain()
    assert root >= 2 and len(nodes) == 13093 and base.SOLVER.is_file()
    save("protocol.json", {"status": "FROZEN_TERMINAL_FIBER_BEFORE_QUERY",
                           "candidate_id": None,
                           "curve_id": target["curve_id"],
                           "workload_id": target["workload_id"],
                           "public_target": target["public_target"],
                           "raw_preimage_index": 0,
                           "fixed_seed_mask": base.pair.SEED,
                           "free_pair_rotations": ROTATIONS,
                           "fixed_terminal_rotation": 128,
                           "source_codes_per_free_pair": 33191,
                           "terminal_signed_states": 32,
                           "terminal_selection_law": pool()["selection_law"],
                           "worker_count": 1,
                           "solver_flags": SOLVER_FLAGS,
                           "solver_cap_seconds": SOLVER_CAP,
                           "parent_solver_cap_seconds": PARENT_CAP,
                           "combined_rss_cap_bytes": base.RSS_CAP,
                           "source_sha256": {name: sha(path) for name, path in sources().items()}})


def check_protocol():
    data = json.loads((HERE / "protocol.json").read_text())
    assert data["status"] == "FROZEN_TERMINAL_FIBER_BEFORE_QUERY"
    assert data["source_sha256"] == {name: sha(path) for name, path in sources().items()}
    assert data["solver_flags"] == SOLVER_FLAGS
    return data


def residuals(raw_target, states):
    result = []
    for row in states:
        point = prepare.subtract(raw_target, row["rotated_raw_point"])
        assert point is not None and point[0] not in (0, 1)
        a = independent.inverse(point[0])
        assert independent.mul(a, point[0]) == 1
        result.append({"point": list(point), "standard_reciprocal": a})
    assert len(result) == 32
    assert len({row["standard_reciprocal"] for row in result}) == 32
    return result


def build(residual_values, bdd_root, bdd_nodes):
    pair = base.pair
    circuit = base.KaratsubaCircuit(pair.N, [0, 1, 2, 13])
    algebra = base.Algebra(circuit, base.Field(), dense_and_threshold=3000)
    h2 = pair.gf_square(pair.gf_half_trace(pair.coordinate(pair.SEED)))
    coefficient = 1 ^ h2
    selectors, outputs, rotated = [], [], []
    for rotation in ROTATIONS:
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

    choices = [circuit.variable() for _ in residual_values]
    circuit.clauses.append(" ".join(map(str, choices)) + " 0")
    for index, left in enumerate(choices):
        for right in choices[index + 1:]:
            circuit.clauses.append(f"-{left} -{right} 0")
    selected_residual = algebra.expression(zip(choices, residual_values))
    middle = [[circuit.variable() for _ in range(pair.N)] for _ in range(6)]
    branches = [circuit.variable() for _ in range(7)]
    ht_basis, trace_basis = [], []
    for bit in range(pair.N):
        value, image = pair.gf_square(1 << bit), 0
        for _ in range((pair.N + 1) // 2):
            image ^= value
            value = pair.gf_square(pair.gf_square(value))
        ht_basis.append(image)
        trace_basis.append(base.trace(1 << bit))
    running = rotated[0]
    for index in range(1, 8):
        output = (algebra.from_bits(middle[index - 1]) if index < 7
                  else selected_residual)
        total = algebra.add(running, rotated[index], output)
        ht = circuit.linear_element(total.bits(), ht_basis)
        circuit.require_zero(algebra.add(
            algebra.mul(algebra.mul(running, rotated[index]), output),
            algebra.from_bits(ht),
            algebra.expression(((branches[index - 1], 1),))).bits())
        circuit.require_zero([circuit.xor(
            wire for wire, bit in zip(total.bits(), trace_basis) if bit)])
        if index < 7:
            circuit.clauses.append(" ".join(map(str, middle[index - 1])) + " 0")
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
                     "middle": middle, "branches": branches, "choices": choices}


def control():
    check_protocol()
    fixture = json.loads((BASE / "control_fixture.json").read_text())
    state_pool = pool()
    residual_rows = residuals(fixture["raw_target"], state_pool["states"])
    chosen = state_pool["control_choice_index"]
    expected = base.standard_reciprocal(fixture["intermediate_z"][6])
    assert residual_rows[chosen]["standard_reciprocal"] == expected
    _, root, nodes = base.source_domain()
    start = time.monotonic_ns()
    circuit, wires = build([row["standard_reciprocal"] for row in residual_rows],
                           root, nodes)
    constructed = time.monotonic_ns()
    formula = HERE / "control.xcnf"
    circuit.write(formula)
    written = time.monotonic_ns()
    initial = {}
    def bind(bits, value):
        initial.update({wire: value >> bit & 1 for bit, wire in enumerate(bits)})
    h2 = base.pair.gf_square(base.pair.gf_half_trace(base.pair.coordinate(base.pair.SEED)))
    for item in fixture["selected"][:8]:
        slot = item["slot"]
        code = base.pair.selector_code(item["masks"][0])
        a = base.standard_reciprocal(item["unrotated_pair_output_z"])
        product = base.pair.product_from_code(code)
        assert base.pair.gf_mul(1 ^ h2, base.pair.gf_square(a)) ^ base.pair.gf_mul(a, product) ^ h2 == 0
        assert base.pair.gf_frobenius(a, item["rotation"]) == base.standard_reciprocal(fixture["pair_rotated_z"][slot])
        bind(wires["selectors"][slot], code)
        bind(wires["outputs"][slot], a)
    for bits, z in zip(wires["middle"], fixture["intermediate_z"][:6]):
        bind(bits, base.standard_reciprocal(z))
    for index, wire in enumerate(wires["choices"]):
        initial[wire] = int(index == chosen)
    rotated = [base.standard_reciprocal(z) for z in fixture["pair_rotated_z"][:8]]
    middle = [base.standard_reciprocal(z) for z in fixture["intermediate_z"][:6]]
    left, branch_bits = rotated[0], []
    for index in range(1, 8):
        right = middle[index - 1] if index < 7 else expected
        total = left ^ rotated[index] ^ right
        branch = base.pair.gf_mul(base.pair.gf_mul(left, rotated[index]), right) ^ base.halftrace(base.pair.gf_square(total))
        assert branch in (0, 1)
        initial[wires["branches"][index - 1]] = branch
        branch_bits.append(branch)
        left = right
    checked = base.check_assignment(circuit, base.complete_assignment(circuit, initial))
    save("control_result.json", {"status": "PASS_EXACT_N131_TERMINAL_FIBER_CONTROL",
                                 "candidate_id": None, "control_choice_index": chosen,
                                 "residuals": residual_rows,
                                 "branch_bits": branch_bits,
                                 "primary_variables": len(initial),
                                 "assignment_check": checked,
                                 "formula": base.profile(circuit, formula,
                                                         (constructed-start)/1e9,
                                                         (written-constructed)/1e9),
                                 "protocol_sha256": sha(HERE / "protocol.json")})
    print("PASS_EXACT_N131_TERMINAL_FIBER_CONTROL", flush=True)


def query():
    protocol = check_protocol()
    control_result = json.loads((HERE / "control_result.json").read_text())
    assert control_result["status"] == "PASS_EXACT_N131_TERMINAL_FIBER_CONTROL"
    target = base.target_record()
    raw_target = target["preimages"][0]["point"]
    _, root, nodes = base.source_domain()
    t0 = time.monotonic_ns()
    residual_rows = residuals(raw_target, pool()["states"])
    t1 = time.monotonic_ns()
    circuit, wires = build([row["standard_reciprocal"] for row in residual_rows],
                           root, nodes)
    t2 = time.monotonic_ns()
    formula = HERE / "ordinary.xcnf"
    circuit.write(formula)
    t3 = time.monotonic_ns()
    details = base.profile(circuit, formula, (t2-t1)/1e9, (t3-t2)/1e9)
    del circuit
    print(json.dumps({"phase": "frozen_ordinary_formula", "formula": details}), flush=True)
    outpath, errpath = HERE / "solver.stdout.txt", HERE / "solver.stderr.txt"
    parent = psutil.Process()
    peak, stop_reason = 0, None
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
            if combined > base.RSS_CAP:
                stop_reason = "RSS_CAP"
                process.kill()
                break
            if time.monotonic_ns() - t3 > PARENT_CAP * 10**9:
                stop_reason = "PARENT_TIMEOUT"
                process.kill()
                break
            time.sleep(0.05)
        code = process.wait()
    t4 = time.monotonic_ns()
    output = outpath.read_text(errors="replace")
    status = ("BOUNDED_UNKNOWN" if stop_reason else
              "SAT_PENDING_GROUP_REPLAY" if "s SATISFIABLE" in output else
              "UNSAT" if "s UNSATISFIABLE" in output else "BOUNDED_UNKNOWN")
    decoded = None
    if status == "SAT_PENDING_GROUP_REPLAY":
        positive = {int(token) for line in output.splitlines() if line.startswith("v ")
                    for token in line.split()[1:] if token.isdigit() and int(token) > 0}
        def decode(bits):
            return sum(int(wire in positive) << bit for bit, wire in enumerate(bits))
        decoded = {"selected_codes": [decode(bits) for bits in wires["selectors"]],
                   "pair_standard_reciprocals": [decode(bits) for bits in wires["outputs"]],
                   "middle_standard_reciprocals": [decode(bits) for bits in wires["middle"]],
                   "branch_bits": [int(wire in positive) for wire in wires["branches"]],
                   "terminal_choice_index": next(index for index, wire in enumerate(wires["choices"])
                                                 if wire in positive),
                   "formula_sha256": details["xcnf_sha256"]}
        save("decoded_model.json", decoded)
    t5 = time.monotonic_ns()
    phase = {"target_residual_generation_ns": t1-t0,
             "formula_construction_ns": t2-t1,
             "formula_serialization_ns": t3-t2,
             "solver_search_ns": t4-t3,
             "terminal_parse_and_model_decode_ns": t5-t4}
    assert sum(phase.values()) == t5-t0
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    save("query_result.json", {"status": status, "candidate_id": None,
                               "curve_id": protocol["curve_id"],
                               "workload_id": protocol["workload_id"],
                               "public_target": protocol["public_target"],
                               "raw_preimage_index": 0,
                               "raw_target": raw_target,
                               "residuals": residual_rows,
                               "phase_ns": phase,
                               "target_dependent_attempt_ns": t5-t0,
                               "formula": details, "worker_count": 1,
                               "solver_flags": SOLVER_FLAGS,
                               "solver_exit_code": code, "stop_reason": stop_reason,
                               "peak_combined_rss_bytes_sampled": peak,
                               "parent_peak_rss_bytes": rss if sys.platform == "darwin" else rss*1024,
                               "status_lines": [line for line in output.splitlines() if line.startswith("s ")],
                               "restart_rows": sum(line.startswith("c rst") for line in output.splitlines()),
                               "decoded_model_saved": decoded is not None,
                               "stdout_sha256": sha(outpath), "stderr_sha256": sha(errpath),
                               "protocol_sha256": sha(HERE / "protocol.json")})
    print(json.dumps({"status": status,
                      "attempt_seconds": (t5-t0)/1e9,
                      "peak_rss": peak}), flush=True)


if __name__ == "__main__":
    assert len(sys.argv) == 2 and sys.argv[1] in ("freeze", "control", "query")
    {"freeze": freeze, "control": control, "query": query}[sys.argv[1]]()
