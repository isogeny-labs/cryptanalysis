"""Seven four-seed W18 pairs and one selected terminal on the N131 curve."""

import hashlib
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / "n131_w18_all_fibers_inverse_20261011"
COUNT = ROOT / "n131_w18_four_seed_sevenpair_source_20261011" / "result.json"
SUPPORT = ROOT / "n131_w16_w18_sixpair_width_gate_20261010" / "support_w18.tsv"
FIXTURE = ROOT / "n131_fixed_seed_ninepair_cubic_20261011" / "control_fixture.json"
sys.path.insert(0, str(PRIOR))
import all_fibers as prior  # noqa: E402

SEEDS = (212, 213, 214, 215)
ROTATIONS = (0, 16, 32, 48, 64, 80, 96)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def support():
    columns = {int(a): int(b) for a, b in
               (line.split() for line in SUPPORT.read_text().splitlines())}
    assert len(columns) == 131307
    groups = defaultdict(list)
    for mask, column in columns.items():
        groups[column].append(mask)
    collisions = [tuple(sorted((a, b))) for members in groups.values()
                  for a, b in __import__("itertools").combinations(members, 2)]
    return columns, groups, collisions


def clause(circuit, literals):
    values = [wire for wire in literals if wire != 0]
    circuit.clauses.append(" ".join(map(str, values)) + " 0")


def forbid_mask(bits, value):
    """A clause false precisely when an endpoint equals a mask."""
    literals = []
    for bit, wire in enumerate(bits):
        expected = value >> bit & 1
        if wire in (0, -1):
            if (wire == -1) != bool(expected):
                return None  # equality is structurally impossible
        else:
            literals.append(-wire if expected else wire)
    return literals


def distinct_columns(circuit, endpoints, choices, states, groups, collisions):
    for i, left in enumerate(endpoints):
        for right in endpoints[i + 1:]:
            differences = [circuit.xor((a, b)) for a, b in zip(left, right)]
            if -1 not in differences:  # This endpoint pair always differs.
                clause(circuit, differences)
            for a, b in collisions:
                for x, y in ((a, b), (b, a)):
                    first, second = forbid_mask(left, x), forbid_mask(right, y)
                    if first is not None and second is not None:
                        clause(circuit, [*first, *second])
    for choice, state in zip(choices, states):
        for column in state["folded_columns"]:
            for mask in groups[column]:
                for endpoint in endpoints:
                    mismatch = forbid_mask(endpoint, mask)
                    if mismatch is not None:
                        clause(circuit, [-choice, *mismatch])


def mask_bits(circuit, selector, seed_bits, pair):
    left = [selector[pair.SOURCE_BITS.index(i)] if i in pair.SOURCE_BITS else 0
            for i in range(18)]
    right = []
    for bit, wire in enumerate(left):
        if bit in (0, 1):
            right.append(circuit.xor((wire, seed_bits[bit])))
        elif pair.SEED >> bit & 1:
            right.append(circuit.xor((wire, -1)))
        else:
            right.append(wire)
    return left, right


def build(values):
    assert len(values) == 128
    pair = prior.terminal.base.pair
    base = prior.terminal.base
    columns, groups, collisions = support()
    circuit = base.KaratsubaCircuit(pair.N, [0, 1, 2, 13])
    algebra = base.Algebra(circuit, base.Field(), dense_and_threshold=3000)
    trace_basis = [base.trace(1 << bit) for bit in range(pair.N)]
    source_basis = [pair.coordinate(1 << bit) for bit in pair.SOURCE_BITS]
    seed_basis = (pair.coordinate(1), pair.coordinate(2))
    seed_base = pair.coordinate(212)
    h2 = {seed: pair.gf_square(pair.gf_half_trace(pair.coordinate(seed)))
          for seed in SEEDS}
    h0, dh0, dh1 = h2[212], h2[212] ^ h2[213], h2[212] ^ h2[214]
    assert h2[215] == h0 ^ dh0 ^ dh1
    selectors, seeds, outputs, rotated, inverses = [], [], [], [], []
    endpoints = []
    for rotation in ROTATIONS:
        bits = [circuit.variable() for _ in pair.SOURCE_BITS]
        choice = [circuit.variable() for _ in range(2)]
        out = [circuit.variable() for _ in range(pair.N)]
        selectors.append(bits)
        seeds.append(choice)
        outputs.append(out)
        left_mask, right_mask = mask_bits(circuit, bits, choice, pair)
        endpoints.extend((left_mask, right_mask))
        source = algebra.expression(zip(bits, source_basis))
        seed = algebra.expression(((-1, seed_base),
                                   (choice[0], seed_basis[0]),
                                   (choice[1], seed_basis[1])))
        other = algebra.add(source, seed)
        witness_pair = []
        for endpoint in (source, other):
            inverse = [circuit.variable() for _ in range(pair.N)]
            circuit.require_zero(algebra.add(
                algebra.mul(endpoint, algebra.from_bits(inverse)),
                algebra.one).bits())
            circuit.require_zero([circuit.xor(
                wire for wire, bit in zip(inverse, trace_basis) if bit)])
            witness_pair.append(inverse)
        inverses.append(witness_pair)
        product_terms = [(wire, pair.gf_square(x) ^ pair.gf_mul(x, seed_base))
                         for wire, x in zip(bits, source_basis)]
        for seed_wire, delta in zip(choice, seed_basis):
            product_terms.extend((circuit.and_(seed_wire, wire), pair.gf_mul(x, delta))
                                 for wire, x in zip(bits, source_basis))
        product = algebra.expression(product_terms)
        square_terms = [(wire, pair.gf_mul(1 ^ h0, pair.gf_square(1 << bit)))
                        for bit, wire in enumerate(out)]
        for seed_wire, delta in ((choice[0], dh0), (choice[1], dh1)):
            square_terms.extend((circuit.and_(seed_wire, wire),
                                 pair.gf_mul(delta, pair.gf_square(1 << bit)))
                                for bit, wire in enumerate(out))
        square_term = algebra.expression(square_terms)
        h2_term = algebra.expression(((-1, h0), (choice[0], dh0),
                                      (choice[1], dh1)))
        circuit.require_zero(algebra.add(
            algebra.mul(product, algebra.from_bits(out)),
            square_term, h2_term).bits())
        clause(circuit, out)
        images = [pair.gf_frobenius(1 << bit, rotation) for bit in range(pair.N)]
        rotated.append(algebra.from_bits(circuit.linear_element(out, images)))

    choices = [circuit.variable() for _ in values]
    clause(circuit, choices)
    for i, left in enumerate(choices):
        for right in choices[i + 1:]:
            clause(circuit, [-left, -right])
    selected = algebra.expression(zip(choices, values))
    states = prior.terminal.pool()["states"] * 4
    distinct_columns(circuit, endpoints, choices, states, groups, collisions)
    middle = [[circuit.variable() for _ in range(pair.N)] for _ in range(5)]
    branches = [circuit.variable() for _ in range(6)]
    ht_basis = []
    for bit in range(pair.N):
        value, image = pair.gf_square(1 << bit), 0
        for _ in range((pair.N + 1) // 2):
            image ^= value
            value = pair.gf_square(pair.gf_square(value))
        ht_basis.append(image)
    running = rotated[0]
    for index in range(1, 7):
        output = algebra.from_bits(middle[index - 1]) if index < 6 else selected
        total = algebra.add(running, rotated[index], output)
        ht = circuit.linear_element(total.bits(), ht_basis)
        circuit.require_zero(algebra.add(
            algebra.mul(algebra.mul(running, rotated[index]), output),
            algebra.from_bits(ht),
            algebra.expression(((branches[index - 1], 1),))).bits())
        circuit.require_zero([circuit.xor(
            wire for wire, bit in zip(total.bits(), trace_basis) if bit)])
        if index < 6:
            clause(circuit, middle[index - 1])
        running = output
    return circuit, {"selectors": selectors, "seeds": seeds,
                     "outputs": outputs, "inverse_witnesses": inverses,
                     "middle": middle, "branches": branches,
                     "choices": choices, "collision_pairs": len(collisions),
                     "source_masks": len(columns)}


def control():
    fixture = json.loads(FIXTURE.read_text())
    curve = prior.terminal.independent
    pair = prior.terminal.base.pair
    chosen = fixture["selected"][:7]
    states = prior.terminal.pool()["states"]
    assert len(chosen) == 7 and len(states) == 32
    points = []
    for row in chosen:
        a, b = row["masks"]
        left, right = curve.point_options(a)[0], curve.point_options(b)[0]
        point = curve.point_add(left, right)
        assert point is not None and point[0] not in (0, 1)
        rotation = row["rotation"]
        points.append((curve.frobenius(point[0], rotation),
                       curve.frobenius(point[1], rotation)))
    total = None
    partial = []
    for point in points:
        total = curve.point_add(total, point)
        assert total is not None and total[0] not in (0, 1)
        partial.append(total)
    raw = curve.point_add(total, tuple(states[0]["rotated_raw_point"]))
    assert raw is not None
    public = prior.point_mul(4, raw)
    preimages = [curve.point_add(raw, torsion) for torsion in prior.TORSION]
    assert all(prior.point_mul(4, point) == public for point in preimages)
    residuals = prior.residuals(preimages)
    expected = curve.inverse(total[0])
    assert residuals[0]["standard_reciprocal"] == expected
    t0 = time.monotonic_ns()
    circuit, wires = build([row["standard_reciprocal"] for row in residuals])
    t1 = time.monotonic_ns()
    path = HERE / "control.xcnf"
    circuit.write(path)
    t2 = time.monotonic_ns()
    initial = {}

    def bind(bits, value):
        initial.update({wire: value >> bit & 1 for bit, wire in enumerate(bits)})

    for slot, (row, point) in enumerate(zip(chosen, points)):
        a, b = row["masks"]
        assert a ^ b == 212
        bind(wires["selectors"][slot], pair.selector_code(a))
        bind(wires["seeds"][slot], 0)
        unrotated = curve.point_add(curve.point_options(a)[0],
                                    curve.point_options(b)[0])
        bind(wires["outputs"][slot], curve.inverse(unrotated[0]))
        for side, mask in enumerate((a, b)):
            bind(wires["inverse_witnesses"][slot][side],
                 curve.inverse(pair.coordinate(mask)))
        assert curve.inverse(point[0]) == curve.frobenius(
            curve.inverse(unrotated[0]), row["rotation"])
    for bits, point in zip(wires["middle"], partial[1:6]):
        bind(bits, curve.inverse(point[0]))
    for i, wire in enumerate(wires["choices"]):
        initial[wire] = int(i == 0)
    for i, wire in enumerate(wires["branches"]):
        left, right = curve.inverse(partial[i][0]), curve.inverse(points[i+1][0])
        output = curve.inverse(partial[i+1][0])
        delta = left ^ right ^ output
        branch = (curve.mul(curve.mul(left, right), output) ^
                  curve.halftrace(curve.square(delta)))
        assert branch in (0, 1)
        initial[wire] = branch
    checked = prior.terminal.base.check_assignment(
        circuit, prior.terminal.base.complete_assignment(circuit, initial))
    save("control_result.json", {
        "status": "PASS_N131_FOUR_SEED_SEVENPAIR_CONSTRUCTED_CONTROL",
        "candidate_id": None, "curve_id": "EC1N131Ckb1heb5f1998f20b",
        "control_public_point": list(public),
        "control_raw_point": list(raw),
        "seven_pair_rotated_points": [list(p) for p in points],
        "terminal_point": states[0]["rotated_raw_point"],
        "selected_choice_index": 0,
        "primary_variables": len(initial),
        "assignment_check": checked,
        "formula": prior.terminal.base.profile(circuit, path,
                                                (t1-t0)/1e9, (t2-t1)/1e9),
        "source_sha256": sha(Path(__file__)),
        "source_count_sha256": sha(COUNT),
        "support_sha256": sha(SUPPORT),
    })
    print("PASS_N131_FOUR_SEED_SEVENPAIR_CONSTRUCTED_CONTROL", flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] != "control":
        raise SystemExit("usage: circuit.py control")
    control()
