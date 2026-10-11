"""Exact balanced S3 comparison on the frozen nine-pair N131 public query."""

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

LINKS = [(0, 1), (2, 3), (4, 5), (6, 7), (9, 10), (11, 12), (13, 14), (15, 8)]
CAP_SECONDS = 195


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def inputs():
    return {"balanced": Path(__file__), "serial": BASE / "run.py",
            "fixture": BASE / "control_fixture.json",
            "source": base.SUPPORT, "pair": base.OLD / "fixed_pair_circuit.py",
            "sparse": ROOT / "n41_basis_aware_quartic_20261011" / "sparse.py",
            "circuit": ROOT.parent / "koblitz-polynomial-w-pair-20260925" / "karatsuba_circuit.py",
            "independent": VERIFY / "verify.py",
            "target": base.OLD / "target_preimages.json",
            "solver": base.SOLVER.resolve()}


def freeze():
    target = base.target_record()
    _, bdd_root, nodes = base.source_domain()
    assert bdd_root >= 2 and base.SOLVER.is_file()
    save("protocol.json", {"status": "FROZEN", "candidate_id": None,
                           "curve_id": target["curve_id"],
                           "workload_id": target["workload_id"],
                           "public_target": target["public_target"],
                           "raw_preimage_index": 0,
                           "seed": base.pair.SEED, "rotations": base.ROTATIONS,
                           "source_codes_per_slot": 33191,
                           "source_bdd_nodes": len(nodes), "links": LINKS,
                           "worker_count": 1, "solver_flags": base.SOLVER_FLAGS,
                           "parent_cap_seconds": CAP_SECONDS,
                           "combined_rss_cap_bytes": base.RSS_CAP,
                           "sha256": {key: sha(path) for key, path in inputs().items()}})


def check_protocol():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert protocol["sha256"] == {key: sha(path) for key, path in inputs().items()}
    assert protocol["links"] == [list(edge) for edge in LINKS]
    return protocol


def build(target_a, bdd_root, bdd_nodes):
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

    middle = [[circuit.variable() for _ in range(pair.N)] for _ in range(7)]
    branches = [circuit.variable() for _ in LINKS]
    ht_basis, trace_basis = [], []
    for bit in range(pair.N):
        value, image = pair.gf_square(1 << bit), 0
        for _ in range((pair.N + 1) // 2):
            image ^= value
            value = pair.gf_square(pair.gf_square(value))
        ht_basis.append(image)
        trace_basis.append(base.trace(1 << bit))
    nodes = rotated + [algebra.from_bits(item) for item in middle]
    for link_index, (left_index, right_index) in enumerate(LINKS):
        left, right = nodes[left_index], nodes[right_index]
        output = (nodes[9 + link_index] if link_index < 7 else
                  algebra.expression(((-1, target_a),)))
        total = algebra.add(left, right, output)
        ht = circuit.linear_element(total.bits(), ht_basis)
        circuit.require_zero(algebra.add(
            algebra.mul(algebra.mul(left, right), output),
            algebra.from_bits(ht),
            algebra.expression(((branches[link_index], 1),))).bits())
        circuit.require_zero([circuit.xor(
            wire for wire, bit in zip(total.bits(), trace_basis) if bit)])
        if link_index < 7:
            circuit.clauses.append(" ".join(map(str, middle[link_index])) + " 0")

    for bits in selectors:
        literals = {0: 0, 1: -1}
        for node in sorted(bdd_nodes):
            bit, low, high = bdd_nodes[node]
            left, right = literals[low], literals[high]
            literals[node] = circuit.xor((
                left, circuit.and_(bits[bit], circuit.xor((left, right)))))
        circuit.clauses.append(str(literals[bdd_root]) + " 0")
    return circuit, {"selectors": selectors, "outputs": outputs,
                     "middle": middle, "branches": branches}


def shifted_a(point):
    assert point is not None and point[0] not in (0, 1)
    return independent.inverse(point[0])


def reconstruct_signed_pairs(fixture):
    """Use the archived serial x-chain only to select signs in the control."""
    all_options = []
    for item in fixture["selected"]:
        a, b = item["masks"]
        expected = fixture["pair_rotated_z"][item["slot"]]
        options = set()
        for pa in independent.point_options(a):
            for pb in independent.point_options(b):
                raw = independent.point_add(pa, pb)
                if raw is None or raw[0] == 1:
                    continue
                rotated = tuple(independent.frobenius(v, item["rotation"])
                                for v in raw)
                if independent.inverse(rotated[0] ^ 1) == expected:
                    options.add(rotated)
        assert len(options) == 2
        all_options.append(sorted(options))
    for first in all_options[0]:
        selected, running = [first], first
        for index in range(1, 9):
            expected = (fixture["intermediate_z"][index - 1]
                        if index < 8 else fixture["raw_target_z"])
            choices = [(candidate, independent.point_add(running, candidate))
                       for candidate in all_options[index]]
            choices = [(candidate, summed) for candidate, summed in choices
                       if summed is not None and summed[0] != 1 and
                       independent.inverse(summed[0] ^ 1) == expected]
            assert len(choices) == 1
            candidate, running = choices[0]
            selected.append(candidate)
        if list(running) == fixture["raw_target"]:
            return selected
    raise AssertionError("control target sign reconstruction failed")


def control():
    check_protocol()
    codes, root, nodes = base.source_domain()
    fixture = json.loads((BASE / "control_fixture.json").read_text())
    target_a = base.standard_reciprocal(fixture["raw_target_z"])
    points = reconstruct_signed_pairs(fixture)
    group_nodes = points[:]
    for left, right in LINKS[:-1]:
        group_nodes.append(independent.point_add(group_nodes[left], group_nodes[right]))
    assert independent.point_add(group_nodes[15], group_nodes[8]) == tuple(fixture["raw_target"])
    assert len(group_nodes) == 16
    start = time.monotonic()
    circuit, wires = build(target_a, root, nodes)
    constructed = time.monotonic()
    formula = HERE / "control.xcnf"
    circuit.write(formula)
    written = time.monotonic()
    initial = {}
    def bind(bits, value):
        initial.update({wire: value >> bit & 1 for bit, wire in enumerate(bits)})
    h2 = base.pair.gf_square(base.pair.gf_half_trace(base.pair.coordinate(base.pair.SEED)))
    for item in fixture["selected"]:
        slot = item["slot"]
        code = base.pair.selector_code(item["masks"][0])
        assert code in codes
        a = base.standard_reciprocal(item["unrotated_pair_output_z"])
        product = base.pair.product_from_code(code)
        assert base.pair.gf_mul(1 ^ h2, base.pair.gf_square(a)) ^ base.pair.gf_mul(a, product) ^ h2 == 0
        assert base.pair.gf_frobenius(a, item["rotation"]) == shifted_a(points[slot])
        bind(wires["selectors"][slot], code)
        bind(wires["outputs"][slot], a)
    for bits, point in zip(wires["middle"], group_nodes[9:]):
        bind(bits, shifted_a(point))
    branch_bits = []
    for index, (left, right) in enumerate(LINKS):
        a, b = shifted_a(group_nodes[left]), shifted_a(group_nodes[right])
        c = shifted_a(group_nodes[9 + index]) if index < 7 else target_a
        total = a ^ b ^ c
        branch = base.pair.gf_mul(base.pair.gf_mul(a, b), c) ^ base.halftrace(base.pair.gf_square(total))
        assert branch in (0, 1)
        initial[wires["branches"][index]] = branch
        branch_bits.append(branch)
    checked = base.check_assignment(circuit, base.complete_assignment(circuit, initial))
    save("control_result.json", {"status": "PASS_BALANCED_N131_CONSTRUCTED_WITNESS",
                                 "primary_variables": len(initial), "group_links": len(LINKS),
                                 "branch_bits": branch_bits,
                                 "assignment_check": checked,
                                 "formula": base.profile(circuit, formula, constructed - start, written - constructed),
                                 "protocol_sha256": sha(HERE / "protocol.json")})
    print("PASS_BALANCED_N131_CONSTRUCTED_WITNESS", flush=True)


def query():
    protocol = check_protocol()
    control_result = json.loads((HERE / "control_result.json").read_text())
    assert control_result["status"] == "PASS_BALANCED_N131_CONSTRUCTED_WITNESS"
    target = base.target_record()
    target_a = base.standard_reciprocal(target["preimages"][0]["reciprocal_x_z"])
    _, root, nodes = base.source_domain()
    start = time.monotonic()
    circuit, wires = build(target_a, root, nodes)
    constructed = time.monotonic()
    formula = HERE / "ordinary.xcnf"
    circuit.write(formula)
    written = time.monotonic()
    details = base.profile(circuit, formula, constructed - start, written - constructed)
    del circuit
    print(json.dumps({"phase": "frozen_ordinary_formula", "formula": details}), flush=True)
    outpath, errpath = HERE / "solver.stdout.txt", HERE / "solver.stderr.txt"
    parent = psutil.Process()
    solver_start = time.monotonic()
    peak, stop_reason = 0, None
    with outpath.open("x") as stdout, errpath.open("x") as stderr:
        process = subprocess.Popen([str(base.SOLVER), *base.SOLVER_FLAGS, str(formula)],
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
            if time.monotonic() - solver_start > CAP_SECONDS:
                stop_reason = "PARENT_TIMEOUT"
                process.kill()
                break
            time.sleep(0.05)
        code = process.wait()
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
                   "formula_sha256": details["xcnf_sha256"]}
        save("decoded_model.json", decoded)
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    save("query_result.json", {"status": status, "candidate_id": None,
                               "curve_id": protocol["curve_id"],
                               "workload_id": protocol["workload_id"],
                               "public_target": protocol["public_target"],
                               "target_standard_reciprocal": target_a,
                               "formula": details, "worker_count": 1,
                               "solver_flags": base.SOLVER_FLAGS,
                               "solver_exit_code": code, "stop_reason": stop_reason,
                               "solver_wall_seconds_exploratory": time.monotonic() - solver_start,
                               "peak_combined_rss_bytes_sampled": peak,
                               "parent_peak_rss_bytes": rss if sys.platform == "darwin" else rss * 1024,
                               "status_lines": [line for line in output.splitlines() if line.startswith("s ")],
                               "restart_rows": sum(line.startswith("c [") for line in output.splitlines()),
                               "decoded_model_saved": decoded is not None,
                               "stdout_sha256": sha(outpath), "stderr_sha256": sha(errpath),
                               "protocol_sha256": sha(HERE / "protocol.json")})
    print(json.dumps({"status": status, "solver_seconds": time.monotonic() - solver_start,
                      "peak_rss": peak}), flush=True)


if __name__ == "__main__":
    assert len(sys.argv) == 2 and sys.argv[1] in ("freeze", "control", "query")
    {"freeze": freeze, "control": control, "query": query}[sys.argv[1]]()
