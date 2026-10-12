"""Ten free W18 pair slots with a balanced nine-link N131 addition tree."""

import argparse
import hashlib
import itertools
import json
import random
import resource
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
NINE = GOAL / "n131_w18_ninepair_balanced_20261012"
ORBIT = GOAL / "n131_w18_ninepair_orbit_20261012"
SHIELD = GOAL / "n131_w18_ninepair_orbit_shield_20261012"
sys.path[:0] = [str(NINE), str(ORBIT), str(SHIELD)]
import balanced as prior  # noqa: E402
import orbit9  # noqa: E402
import shield  # noqa: E402

base = orbit9.base
pair = base.pair
group = orbit9.independent
ROTATIONS = tuple(base.ROTATIONS) + (0,)
TREE = ((0, 1), (2, 3), (4, 5), (6, 7), (8, 9),
        (10, 11), (12, 13), (14, 15), (17, 16))
SELECTION_SEED = 20261012


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def sources():
    return {**orbit9.sources(), "prior_balanced": NINE / "balanced.py",
            "prior_proof": NINE / "BalancedTree.lean",
            "shield": SHIELD / "shield.py", "tenpair": Path(__file__),
            "runtime": HERE / "sage_runtime_info.json",
            "n41_tenpair_audit": GOAL / "n41_w8_tenpair_density_control_20261012/audit_result.json"}


def choose_fixture():
    codes, _, _ = base.source_domain()
    columns = {int(mask): int(column) for mask, column in
               (line.split() for line in base.SUPPORT.read_text().splitlines())}
    h2 = pair.gf_square(pair.gf_half_trace(pair.coordinate(pair.SEED)))
    for attempt in range(32):
        shuffled = list(codes)
        random.Random(SELECTION_SEED + attempt).shuffle(shuffled)
        occupied, selected, points = set(), [], []
        for slot, rotation in enumerate(ROTATIONS):
            for code in shuffled:
                mask = pair.mask_from_code(code)
                other = mask ^ pair.SEED
                if mask not in columns or other not in columns:
                    continue
                two_columns = (columns[mask], columns[other])
                if two_columns[0] == two_columns[1] or occupied.intersection(two_columns):
                    continue
                product = pair.product_from_code(code)
                chosen = None
                for left_sign, right_sign in itertools.product(range(2), repeat=2):
                    left = group.point_options(mask)[left_sign]
                    right = group.point_options(other)[right_sign]
                    raw = group.point_add(left, right)
                    if raw is None or raw[0] in (0, 1):
                        continue
                    a = group.inverse(raw[0])
                    if (pair.gf_mul(1 ^ h2, pair.gf_square(a)) ^
                            pair.gf_mul(a, product) ^ h2):
                        continue
                    rotated = (group.frobenius(raw[0], rotation),
                               group.frobenius(raw[1], rotation))
                    chosen = (raw, rotated, a, (left_sign, right_sign))
                    break
                if chosen is None:
                    continue
                raw, rotated, a, signs = chosen
                occupied.update(two_columns)
                selected.append({"slot": slot, "rotation": rotation,
                                 "code": code, "masks": [mask, other],
                                 "columns": list(two_columns),
                                 "source_signs": list(signs),
                                 "raw_pair_point": list(raw),
                                 "rotated_pair_point": list(rotated),
                                 "unrotated_pair_reciprocal": a})
                points.append(rotated)
                shuffled.remove(code)
                break
            else:
                raise RuntimeError("could not select ten distinct-column pair slots")
        nodes = list(points)
        for left, right in TREE:
            result = group.point_add(nodes[left], nodes[right])
            if result is None or result[0] in (0, 1):
                break
            nodes.append(result)
        if len(nodes) != 19:
            continue
        raw_target = nodes[-1]
        try:
            rows = orbit9.orbit_rows(orbit9.constructed_preimages(raw_target))
        except AssertionError:
            continue
        assert len(rows) == orbit9.CHOICES
        return {"status": "CONSTRUCTED_TENPAIR_FIXTURE", "seed": SELECTION_SEED,
                "attempt": attempt, "rotations": ROTATIONS, "tree": TREE,
                "selected": selected, "node_points": [list(point) for point in nodes],
                "raw_target": list(raw_target),
                "public_target": list(orbit9.multiply_by_four(raw_target)),
                "folded_columns": sorted(occupied)}
    raise RuntimeError("no nonexceptional constructed ten-pair fixture")


def build(target_reciprocals, bdd_root, bdd_nodes):
    assert len(target_reciprocals) == orbit9.CHOICES
    circuit = base.KaratsubaCircuit(pair.N, [0, 1, 2, 13])
    algebra = base.Algebra(circuit, base.Field(), dense_and_threshold=3000)
    h2 = pair.gf_square(pair.gf_half_trace(pair.coordinate(pair.SEED)))
    coefficient = 1 ^ h2
    selectors, outputs, nodes = [], [], []
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
        images = [pair.gf_frobenius(1 << bit, rotation)
                  for bit in range(pair.N)]
        nodes.append(algebra.from_bits(circuit.linear_element(out, images)))

    choices = [circuit.variable() for _ in target_reciprocals]
    circuit.clauses.append(" ".join(map(str, choices)) + " 0")
    for index, left in enumerate(choices):
        for right in choices[index + 1:]:
            circuit.clauses.append(f"-{left} -{right} 0")
    selected_target = algebra.expression(zip(choices, target_reciprocals))
    intermediates = [[circuit.variable() for _ in range(pair.N)] for _ in range(8)]
    branches = [circuit.variable() for _ in TREE]
    ht_basis, trace_basis = [], []
    for bit in range(pair.N):
        value, image = pair.gf_square(1 << bit), 0
        for _ in range((pair.N + 1) // 2):
            image ^= value
            value = pair.gf_square(pair.gf_square(value))
        ht_basis.append(image)
        trace_basis.append(base.trace(1 << bit))
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

    for bits in selectors:
        literals = {0: 0, 1: -1}
        for node in sorted(bdd_nodes):
            bit, low, high = bdd_nodes[node]
            left, right = literals[low], literals[high]
            literals[node] = circuit.xor((
                left, circuit.and_(bits[bit], circuit.xor((left, right)))))
        circuit.clauses.append(str(literals[bdd_root]) + " 0")

    conflicts = shield.source_conflicts()
    for left_slot, right_slot in itertools.combinations(range(10), 2):
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
                     "choices": choices}


def freeze():
    fixture = json.loads((HERE / "fixture.json").read_text())
    target = base.target_record()
    codes, root, bdd_nodes = base.source_domain()
    assert len(codes) == 33191 and len(bdd_nodes) == 13093 and root >= 2
    save("protocol.json", {"status": "FROZEN_BEFORE_TENPAIR_CONTROL",
                           "candidate_id": None, "curve_id": target["curve_id"],
                           "constructed_public_target": fixture["public_target"],
                           "previous_public_target": target["public_target"],
                           "pair_slots": 10, "rotations": ROTATIONS,
                           "tree": TREE, "source_codes_per_slot": len(codes),
                           "target_choice_count": orbit9.CHOICES,
                           "required_distinct_folded_columns": 20,
                           "constructed_solver_cap_seconds": 120,
                           "combined_rss_cap_bytes": 4 * 1024**3,
                           "selection_seed": SELECTION_SEED,
                           "source_sha256": {**{name: sha(path) for name, path in sources().items()},
                                             "fixture": sha(HERE / "fixture.json")}})


def control():
    frozen = json.loads((HERE / "protocol.json").read_text())
    assert frozen["status"] == "FROZEN_BEFORE_TENPAIR_CONTROL"
    assert frozen["source_sha256"] == {**{name: sha(path) for name, path in sources().items()},
                                       "fixture": sha(HERE / "fixture.json")}
    fixture = json.loads((HERE / "fixture.json").read_text())
    _, root, bdd_nodes = base.source_domain()
    rows = orbit9.orbit_rows(orbit9.constructed_preimages(tuple(fixture["raw_target"])))
    started = time.monotonic_ns()
    circuit, wires = build([row["standard_reciprocal"] for row in rows], root, bdd_nodes)
    built = time.monotonic_ns()
    formula = HERE / "control.xcnf"
    circuit.write(formula)
    written = time.monotonic_ns()
    initial = {}
    def bind(bits, value):
        initial.update({wire: value >> bit & 1 for bit, wire in enumerate(bits)})
    for item in fixture["selected"]:
        slot = item["slot"]
        bind(wires["selectors"][slot], item["code"])
        bind(wires["outputs"][slot], item["unrotated_pair_reciprocal"])
    points = [tuple(row) for row in fixture["node_points"]]
    for bits, point in zip(wires["intermediates"], points[10:18]):
        bind(bits, group.inverse(point[0]))
    for index, wire in enumerate(wires["choices"]):
        initial[wire] = int(index == 0)
    branch_bits = []
    for index, (left_index, right_index) in enumerate(TREE):
        left = group.inverse(points[left_index][0])
        right = group.inverse(points[right_index][0])
        output = group.inverse(points[10 + index][0])
        total = left ^ right ^ output
        branch = (pair.gf_mul(pair.gf_mul(left, right), output) ^
                  base.halftrace(pair.gf_square(total)))
        assert branch in (0, 1)
        initial[wires["branches"][index]] = branch
        branch_bits.append(branch)
    checked = base.check_assignment(circuit, base.complete_assignment(circuit, initial))
    save("control_result.json", {"status": "PASS_TENPAIR_CONSTRUCTED_ASSIGNMENT",
                                 "candidate_id": None, "pair_slots": 10,
                                 "group_link_checks": 9, "selected_choice": 0,
                                 "constructed_public_target": fixture["public_target"],
                                 "branch_bits": branch_bits,
                                 "assignment_check": checked,
                                 "formula": base.profile(circuit, formula,
                                                         (built-started)/1e9,
                                                         (written-built)/1e9),
                                 "parent_peak_rss_bytes": resource.getrusage(
                                     resource.RUSAGE_SELF).ru_maxrss,
                                 "protocol_sha256": sha(HERE / "protocol.json")})
    print("PASS_TENPAIR_CONSTRUCTED_ASSIGNMENT", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("fixture", "freeze", "control"))
    mode = parser.parse_args().mode
    {"fixture": lambda: save("fixture.json", choose_fixture()),
     "freeze": freeze, "control": control}[mode]()
