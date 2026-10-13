"""Ten-pair N131 circuit linking pair-code and reciprocal slots 0 and 1."""

import argparse
import json
import sys
import time
from fractions import Fraction
from pathlib import Path

from binary_selector import build as build_binary_selector

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n131_w18_ninepair_orbit_20261012"
SHIELD = HERE.parent / "n131_w18_ninepair_orbit_shield_20261012"
INVERSE = HERE.parent / "n131_w18_inverse_trace_terminal_20261011"
NINE = HERE.parent / "n131_fixed_seed_ninepair_cubic_20261011"
N41 = HERE.parent / "n41_n131_linked_frobenius_pair_20261012"
SELECTOR = HERE.parent / "n131_w18_ninepair_binary_frob_20261012"
sys.path.insert(0, str(PARENT))
import orbit9  # noqa: E402
sys.path.insert(0, str(SHIELD))
import shield  # noqa: E402

base = orbit9.base
pair = base.pair
independent = orbit9.independent

ROTATIONS = (*base.ROTATIONS, 8)
# Leaf nodes 0..9; each row adds two earlier nodes, with the last at target.
TREE = ((0, 1), (2, 3), (4, 5), (6, 7),
        (10, 11), (12, 13), (14, 15), (16, 8), (17, 9))


def binary_target(circuit, reciprocals):
    return build_binary_selector(circuit, reciprocals, pair.N,
                                 pair.gf_square, pair.gf_frobenius)


def build(target_reciprocals, bdd_root, bdd_nodes):
    assert len(target_reciprocals) == orbit9.CHOICES
    circuit = base.KaratsubaCircuit(pair.N, [0, 1, 2, 13])
    algebra = base.Algebra(circuit, base.Field(), dense_and_threshold=3000)
    h2 = pair.gf_square(pair.gf_half_trace(pair.coordinate(pair.SEED)))
    coefficient = 1 ^ h2
    selectors, outputs, nodes, inverse_witnesses = [], [], [], []
    trace_basis = [base.trace(1 << bit) for bit in range(pair.N)]
    for slot, rotation in enumerate(ROTATIONS):
        if slot == 1:
            bits, out = selectors[0], outputs[0]
        else:
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
        source = algebra.expression(
            (wire, 1 << (source_bit + 1))
            for wire, source_bit in zip(bits, pair.SOURCE_BITS))
        other = algebra.add(source, algebra.expression(((-1, pair.coordinate(pair.SEED)),)))
        witnesses = []
        for endpoint in (source, other):
            inverse_bits = [circuit.variable() for _ in range(pair.N)]
            circuit.require_zero(algebra.add(
                algebra.mul(endpoint, algebra.from_bits(inverse_bits)), algebra.one).bits())
            circuit.require_zero([circuit.xor(
                wire for wire, tracebit in zip(inverse_bits, trace_basis) if tracebit)])
            witnesses.append(inverse_bits)
        inverse_witnesses.append(witnesses)
        images = [pair.gf_frobenius(1 << bit, rotation)
                  for bit in range(pair.N)]
        nodes.append(algebra.from_bits(circuit.linear_element(out, images)))

    target_bits, fiber_bits, rotation_bits = binary_target(circuit, target_reciprocals)
    selected_target = algebra.from_bits(target_bits)
    intermediates = [[circuit.variable() for _ in range(pair.N)] for _ in range(8)]
    branches = [circuit.variable() for _ in TREE]
    ht_basis = []
    for bit in range(pair.N):
        value, image = pair.gf_square(1 << bit), 0
        for _ in range((pair.N + 1) // 2):
            image ^= value
            value = pair.gf_square(pair.gf_square(value))
        ht_basis.append(image)
    for index, (left_index, right_index) in enumerate(TREE):
        output = (algebra.from_bits(intermediates[index]) if index < 8
                  else selected_target)
        left, right = nodes[left_index], nodes[right_index]
        triple = algebra.mul(algebra.mul(left, right), output)
        total = algebra.add(left, right, output)
        ht = circuit.linear_element(total.bits(), ht_basis)
        circuit.require_zero(algebra.add(
            triple, algebra.from_bits(ht),
            algebra.expression(((branches[index], 1),))).bits())
        circuit.require_zero([circuit.xor(
            wire for wire, bit in zip(total.bits(), trace_basis) if bit)])
        if index < 8:
            circuit.clauses.append(" ".join(map(str, intermediates[index])) + " 0")
        nodes.append(output)

    # Preserve the exact 20-distinct-folded-column source.
    from itertools import combinations
    conflicts = shield.source_conflicts()
    for left_slot, right_slot in combinations(range(10), 2):
        if (left_slot, right_slot) == (0, 1):
            continue
        left_bits, right_bits = selectors[left_slot], selectors[right_slot]
        differences = [circuit.xor((left, right))
                       for left, right in zip(left_bits, right_bits)]
        circuit.clauses.append(" ".join(map(str, differences)) + " 0")
        for first_code, second_code in conflicts:
            for a, b in ((first_code, second_code), (second_code, first_code)):
                literals = shield.mismatch_literals(left_bits, a)
                literals += shield.mismatch_literals(right_bits, b)
                circuit.clauses.append(" ".join(map(str, literals)) + " 0")
    return circuit, {"selectors": selectors, "outputs": outputs,
                     "intermediates": intermediates, "branches": branches,
                     "fiber_bits": fiber_bits,
                     "rotation_bits": rotation_bits,
                     "target_bits": target_bits,
                     "inverse_witnesses": inverse_witnesses}


def point_options_from_reciprocal(reciprocal):
    x = independent.inverse(reciprocal)
    rhs = x ^ independent.square(reciprocal)
    lam = independent.halftrace(rhs)
    y = independent.mul(x, lam)
    assert independent.square(y) ^ independent.mul(x, y) == independent.mul(
        independent.square(x), x) ^ 1
    return ((x, y), (x, y ^ x))


def witness_points(chain):
    pair_options = [point_options_from_reciprocal(base.standard_reciprocal(z))
                    for z in chain["pair_rotated_z"]]
    # The prior independently checked serial fixture identifies the signs
    # without assuming that a reciprocal encodes a signed point.
    paths = [(point, [point]) for point in pair_options[0]]
    for index in range(1, 9):
        expected_x = (independent.inverse(base.standard_reciprocal(
            chain["intermediate_z"][index - 1])) if index < 8
                      else chain["raw_target"][0])
        next_paths = []
        for subtotal, chosen in paths:
            for point in pair_options[index]:
                result = independent.point_add(subtotal, point)
                if result is not None and result[0] == expected_x:
                    next_paths.append((result, chosen + [point]))
        assert next_paths, index
        paths = next_paths
    matches = [chosen for point, chosen in paths
               if point == tuple(chain["raw_target"])]
    assert matches
    return matches[0]


def control():
    frozen = protocol()
    _, root, bdd_nodes = base.source_domain()
    prior_chain = json.loads((NINE / "control_fixture.json").read_text())
    chain = json.loads((HERE / "control_fixture.json").read_text())
    pair_points = [tuple(point) for point in chain["signed_pair_points"]]
    assert len(pair_points) == 10
    assert pair_points[1] == tuple(independent.frobenius(value, 16) for value in pair_points[0])
    assert chain["selected"][0]["masks"] == chain["selected"][1]["masks"]
    assert chain["selected"][0]["unrotated_pair_output_z"] == chain["selected"][1]["unrotated_pair_output_z"]
    actual_nodes = list(pair_points)
    tree_reciprocals = []
    for left, right in TREE:
        result = independent.point_add(actual_nodes[left], actual_nodes[right])
        assert result is not None and result[0] not in (0, 1)
        actual_nodes.append(result)
        if len(tree_reciprocals) < 8:
            tree_reciprocals.append(independent.inverse(result[0]))
    assert actual_nodes[-1] == tuple(chain["raw_target"])
    rows = orbit9.orbit_rows(orbit9.constructed_preimages(chain["raw_target"]))
    start = time.monotonic_ns()
    circuit, wires = build([row["standard_reciprocal"] for row in rows], root, bdd_nodes)
    constructed = time.monotonic_ns()
    formula = HERE / "control.xcnf"
    circuit.write(formula)
    written = time.monotonic_ns()
    initial = {}
    def bind(bits, value):
        initial.update({wire: value >> bit & 1 for bit, wire in enumerate(bits)})
    h2 = pair.gf_square(pair.gf_half_trace(pair.coordinate(pair.SEED)))
    for item in chain["selected"]:
        slot = item["slot"]
        code = pair.selector_code(item["masks"][0])
        assert code in base.source_domain()[0]
        a = base.standard_reciprocal(item["unrotated_pair_output_z"])
        product = pair.product_from_code(code)
        assert (pair.gf_mul(1 ^ h2, pair.gf_square(a)) ^
                pair.gf_mul(a, product) ^ h2) == 0
        bind(wires["selectors"][slot], code)
        bind(wires["outputs"][slot], a)
        for side, mask in enumerate(item["masks"]):
            coordinate = pair.coordinate(mask)
            witness = base.inverse(coordinate)
            assert pair.gf_mul(coordinate, witness) == 1
            assert base.trace(witness) == 0
            bind(wires["inverse_witnesses"][slot][side], witness)
    for bits, reciprocal in zip(wires["intermediates"], tree_reciprocals):
        bind(bits, reciprocal)
    for wire in wires["fiber_bits"] + wires["rotation_bits"]:
        initial[wire] = 0
    branch_bits = []
    for index, (left_index, right_index) in enumerate(TREE):
        left = independent.inverse(actual_nodes[left_index][0])
        right = independent.inverse(actual_nodes[right_index][0])
        output = independent.inverse(actual_nodes[10 + index][0])
        total = left ^ right ^ output
        branch = (pair.gf_mul(pair.gf_mul(left, right), output) ^
                  base.halftrace(pair.gf_square(total)))
        assert branch in (0, 1)
        initial[wires["branches"][index]] = branch
        branch_bits.append(branch)
    checked = base.check_assignment(circuit, base.complete_assignment(circuit, initial))
    orbit9.save("control_result.json", {
        "status": "PASS_FULL_N131_LINKED_TENPAIR_CONSTRUCTED_WITNESS",
        "variant": "tenpair_linked_pair_code_reciprocal_binary_frobenius",
        "candidate_id": None, "tree": TREE, "tree_depth": 5,
        "constructed_public_target": list(orbit9.multiply_by_four(
            tuple(chain["raw_target"]))),
        "source_pair_checks": 10, "distinct_source_pair_codes": 9, "group_link_checks": 9,
        "branch_bits": branch_bits, "assignment_check": checked,
        "formula": base.profile(circuit, formula, (constructed-start)/1e9,
                                (written-constructed)/1e9),
        "protocol_sha256": orbit9.sha(HERE / "protocol.json")})
    print("PASS_FULL_N131_LINKED_TENPAIR_CONSTRUCTED_WITNESS", flush=True)


def query():
    assert json.loads((HERE / "control_result.json").read_text())["variant"] == \
        "tenpair_linked_pair_code_reciprocal_binary_frobenius"
    return query_binary()


def query_binary():
    frozen = protocol()
    target = base.target_record()
    t0 = time.monotonic_ns()
    rows = orbit9.orbit_rows([row["point"] for row in target["preimages"]])
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
    parent = orbit9.psutil.Process()
    peak, stop = 0, None
    with outpath.open("x") as stdout, errpath.open("x") as stderr:
        process = orbit9.subprocess.Popen([str(base.SOLVER), *orbit9.SOLVER_FLAGS,
                                           str(formula)], stdout=stdout, stderr=stderr)
        child = orbit9.psutil.Process(process.pid)
        while process.poll() is None:
            try:
                combined = parent.memory_info().rss + child.memory_info().rss
            except orbit9.psutil.NoSuchProcess:
                combined = parent.memory_info().rss
            peak = max(peak, combined)
            if combined > orbit9.RSS_CAP:
                stop = "RSS_CAP"
            elif time.monotonic_ns() - t0 >= orbit9.TOTAL_CAP_NS:
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
        fiber = decode(wires["fiber_bits"])
        rotation = decode(wires["rotation_bits"])
        assert fiber < 4 and rotation < pair.N
        chosen = rows[fiber * pair.N + rotation]
        assert decode(wires["target_bits"]) == chosen["standard_reciprocal"]
        decoded = {"selected_codes": [decode(bits) for bits in wires["selectors"]],
                   "pair_standard_reciprocals": [decode(bits) for bits in wires["outputs"]],
                   "intermediate_standard_reciprocals": [decode(bits) for bits in wires["intermediates"]],
                   "branch_bits": [int(wire in positive) for wire in wires["branches"]],
                   "raw_preimage_index": fiber,
                   "target_rotation": rotation,
                   "formula_sha256": profile["xcnf_sha256"]}
        orbit9.save("decoded_model.json", decoded)
    t5 = time.monotonic_ns()
    phases = {"target_orbit_and_fibers_ns": t1-t0,
              "formula_construction_ns": t2-t1,
              "formula_serialization_ns": t3-t2,
              "solver_search_ns": t4-t3,
              "terminal_parse_and_decode_ns": t5-t4}
    assert sum(phases.values()) == t5-t0
    orbit9.save("query_result.json", {"status": status, "candidate_id": None,
                                     "curve_id": frozen["curve_id"],
                                     "workload_id": frozen["workload_id"],
                                     "public_target": frozen["public_target"],
                                     "target_choice_count": orbit9.CHOICES,
                                     "distinct_target_reciprocals": len({row["standard_reciprocal"] for row in rows}),
                                     "phase_ns": phases,
                                     "target_dependent_attempt_ns": t5-t0,
                                     "formula": profile, "worker_count": 1,
                                     "solver_flags": orbit9.SOLVER_FLAGS,
                                     "solver_exit_code": code, "stop_reason": stop,
                                     "peak_combined_rss_bytes_sampled": peak,
                                     "status_lines": [line for line in output.splitlines() if line.startswith("s ")],
                                     "restart_rows": sum(line.startswith("c [") for line in output.splitlines()),
                                     "decoded_model_saved": decoded is not None,
                                     "stdout_sha256": orbit9.sha(outpath),
                                     "stderr_sha256": orbit9.sha(errpath),
                                     "protocol_sha256": orbit9.sha(HERE / "protocol.json")})
    print(json.dumps({"status": status, "target_dependent_seconds": (t5-t0)/1e9,
                      "peak_combined_rss_bytes": peak}), flush=True)


def freeze():
    n41 = json.loads((N41 / "audit_result.json").read_text())
    assert n41["status"] == "PASS_INDEPENDENT_N41_LINKED_FROBENIUS_PUBLIC_RELATION"
    assert n41["source_pairs_free"] == 9 and n41["folded_columns_nonzero"] == 18
    projection = json.loads((N41 / "projection_result.json").read_text())
    assert projection["status"] == "PASS_CONSERVATIVE_LABELED_SOURCE_PROJECTION"
    selector = json.loads((SELECTOR / "n41_control_result.json").read_text())
    assert selector["status"] == "PASS_N41_BINARY_FROBENIUS_SELECTOR_CONTROL"
    assert selector["valid_choices_checked"] == 164
    assert selector["invalid_rotation_codes_rejected"] == 92
    fixture = json.loads((HERE / "control_fixture.json").read_text())
    assert fixture["status"] == "PASS_LINKED_N131_CONSTRUCTED_SOURCE_FIXTURE"
    assert len(fixture["selected"]) == 10
    assert fixture["selected"][0]["masks"] == fixture["selected"][1]["masks"]
    gate = json.loads((INVERSE / "gate_equivalence.json").read_text())
    assert gate["status"] == "PASS_EXACT_SOURCE_GATE_EQUIVALENCE"
    assert gate["canonical_codes"] == 33191
    assert gate["same_folded_column_pairs"] == 0
    target = base.target_record()
    assert len(orbit9.orbit_rows([row["point"] for row in target["preimages"]])) == orbit9.CHOICES
    _, root, nodes = base.source_domain()
    assert root >= 2 and len(nodes) == 13093 and base.SOLVER.is_file()
    admissible = int(projection["labeled_code_tuples_admissible_lower_bound"])
    subgroup_order = int(projection["subgroup_order"])
    mean = Fraction(admissible, subgroup_order)
    orbit9.save("protocol.json", {
        "status": "FROZEN_N131_LINKED_TENPAIR_BEFORE_CONTROL_AND_QUERY",
        "candidate_id": None, "curve_id": target["curve_id"],
        "workload_id": target["workload_id"],
        "public_target": target["public_target"],
        "fixed_seed_mask": pair.SEED,
        "free_pair_rotations": ROTATIONS,
        "source_codes_per_slot": 33191,
        "source_pair_slots": 10, "free_pair_codes": 9,
        "linked_slots": [0, 1], "linked_rotation_gap": 16,
        "distinct_folded_columns_required": 18,
        "raw_preimage_count": orbit9.RAW_FIBERS,
        "frobenius_rotations": pair.N,
        "target_choice_count": orbit9.CHOICES,
        "selection_law": "two-bit raw-fiber mux and eight-bit Frobenius exponent, restricted to 0..130",
        "fiber_selector_bits": 2, "rotation_selector_bits": 8,
        "uniform_mapping_heuristic_mean_lower_exact": f"{mean.numerator}/{mean.denominator}",
        "worker_count": 1,
        "total_target_dependent_cap_seconds": orbit9.TOTAL_CAP_NS // 10**9,
        "combined_rss_cap_bytes": orbit9.RSS_CAP,
        "solver_flags": orbit9.SOLVER_FLAGS,
        "source_sha256": {name: orbit9.sha(path) for name, path in sources().items()},
    })


def sources():
    return {**orbit9_sources(), "source_shield": SHIELD / "shield.py",
            "inverse_gate_source": INVERSE / "inverse.py",
            "inverse_gate_equivalence": INVERSE / "gate_equivalence.json",
            "binary_selector": HERE / "binary_selector.py",
            "n41_linked_audit": N41 / "audit_result.json",
            "n131_linked_projection": N41 / "projection_result.json",
            "n41_selector_protocol": SELECTOR / "n41_control_protocol.json",
            "n41_selector_result": SELECTOR / "n41_control_result.json",
            "tenpair_fixture": HERE / "control_fixture.json",
            "tenpair_fixture_maker": HERE / "make_fixture.py",
            "balanced_runner": Path(__file__)}


def protocol():
    record = json.loads((HERE / "protocol.json").read_text())
    assert record["status"] == "FROZEN_N131_LINKED_TENPAIR_BEFORE_CONTROL_AND_QUERY"
    assert record["source_sha256"] == {name: orbit9.sha(path) for name, path in sources().items()}
    return record


orbit9_sources = orbit9.sources
orbit9.HERE = HERE
orbit9.build = build
orbit9.sources = sources


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "control", "query"))
    {"freeze": freeze, "control": control,
     "query": query}[parser.parse_args().mode]()
