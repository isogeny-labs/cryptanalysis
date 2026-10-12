"""Balanced nine-pair N131 circuit with exact inverse-trace source gates."""

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n131_w18_ninepair_orbit_20261012"
SHIELD = HERE.parent / "n131_w18_ninepair_orbit_shield_20261012"
INVERSE = HERE.parent / "n131_w18_inverse_trace_terminal_20261011"
sys.path.insert(0, str(PARENT))
import orbit9  # noqa: E402
sys.path.insert(0, str(SHIELD))
import shield  # noqa: E402

base = orbit9.base
pair = base.pair
independent = orbit9.independent

# Each row adds its two earlier nodes. The last output is the selected target.
TREE = ((0, 1), (2, 3), (4, 5), (6, 7),
        (9, 10), (11, 12), (13, 14), (15, 8))


def build(target_reciprocals, bdd_root, bdd_nodes):
    assert len(target_reciprocals) == orbit9.CHOICES
    circuit = base.KaratsubaCircuit(pair.N, [0, 1, 2, 13])
    algebra = base.Algebra(circuit, base.Field(), dense_and_threshold=3000)
    h2 = pair.gf_square(pair.gf_half_trace(pair.coordinate(pair.SEED)))
    coefficient = 1 ^ h2
    selectors, outputs, nodes, inverse_witnesses = [], [], [], []
    trace_basis = [base.trace(1 << bit) for bit in range(pair.N)]
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

    choices = [circuit.variable() for _ in target_reciprocals]
    circuit.clauses.append(" ".join(map(str, choices)) + " 0")
    for index, left in enumerate(choices):
        for right in choices[index + 1:]:
            circuit.clauses.append(f"-{left} -{right} 0")
    selected_target = algebra.expression(zip(choices, target_reciprocals))
    intermediates = [[circuit.variable() for _ in range(pair.N)] for _ in range(7)]
    branches = [circuit.variable() for _ in TREE]
    ht_basis = []
    for bit in range(pair.N):
        value, image = pair.gf_square(1 << bit), 0
        for _ in range((pair.N + 1) // 2):
            image ^= value
            value = pair.gf_square(pair.gf_square(value))
        ht_basis.append(image)
    for index, (left_index, right_index) in enumerate(TREE):
        output = (algebra.from_bits(intermediates[index]) if index < 7
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
        if index < 7:
            circuit.clauses.append(" ".join(map(str, intermediates[index])) + " 0")
        nodes.append(output)

    # Preserve the exact 18-distinct-folded-column source of the shielded run.
    from itertools import combinations
    conflicts = shield.source_conflicts()
    for left_slot, right_slot in combinations(range(9), 2):
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
                     "choices": choices, "inverse_witnesses": inverse_witnesses}


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
    frozen = orbit9.protocol()
    _, root, bdd_nodes = base.source_domain()
    chain = json.loads((base.HERE / "control_fixture.json").read_text())
    pair_points = witness_points(chain)
    actual_nodes = list(pair_points)
    tree_reciprocals = []
    for left, right in TREE:
        result = independent.point_add(actual_nodes[left], actual_nodes[right])
        assert result is not None and result[0] not in (0, 1)
        actual_nodes.append(result)
        if len(tree_reciprocals) < 7:
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
    for index, wire in enumerate(wires["choices"]):
        initial[wire] = int(index == 0)
    branch_bits = []
    for index, (left_index, right_index) in enumerate(TREE):
        left = independent.inverse(actual_nodes[left_index][0])
        right = independent.inverse(actual_nodes[right_index][0])
        output = independent.inverse(actual_nodes[9 + index][0])
        total = left ^ right ^ output
        branch = (pair.gf_mul(pair.gf_mul(left, right), output) ^
                  base.halftrace(pair.gf_square(total)))
        assert branch in (0, 1)
        initial[wires["branches"][index]] = branch
        branch_bits.append(branch)
    checked = base.check_assignment(circuit, base.complete_assignment(circuit, initial))
    orbit9.save("control_result.json", {
        "status": "PASS_FULL_N131_NINEPAIR_ORBIT_CONSTRUCTED_WITNESS",
        "variant": "balanced_inverse_trace_source",
        "candidate_id": None, "tree": TREE, "tree_depth": 4,
        "constructed_public_target": list(orbit9.multiply_by_four(
            tuple(chain["raw_target"]))),
        "source_pair_checks": 9, "group_link_checks": 8,
        "branch_bits": branch_bits, "assignment_check": checked,
        "formula": base.profile(circuit, formula, (constructed-start)/1e9,
                                (written-constructed)/1e9),
        "protocol_sha256": orbit9.sha(HERE / "protocol.json")})
    print("PASS_FULL_N131_NINEPAIR_BALANCED_CONSTRUCTED_WITNESS", flush=True)


def query():
    assert json.loads((HERE / "control_result.json").read_text())["variant"] == \
        "balanced_inverse_trace_source"
    orbit9.query()


def freeze():
    gate = json.loads((INVERSE / "gate_equivalence.json").read_text())
    assert gate["status"] == "PASS_EXACT_SOURCE_GATE_EQUIVALENCE"
    assert gate["canonical_codes"] == 33191
    assert gate["same_folded_column_pairs"] == 0
    orbit9.freeze()


def sources():
    return {**orbit9_sources(), "source_shield": SHIELD / "shield.py",
            "inverse_gate_source": INVERSE / "inverse.py",
            "inverse_gate_equivalence": INVERSE / "gate_equivalence.json",
            "balanced_runner": Path(__file__)}


orbit9_sources = orbit9.sources
orbit9.HERE = HERE
orbit9.build = build
orbit9.sources = sources


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "control", "query"))
    {"freeze": freeze, "control": control,
     "query": query}[parser.parse_args().mode]()
