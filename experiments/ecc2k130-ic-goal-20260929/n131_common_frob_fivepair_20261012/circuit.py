"""Five free all-seed W18 diagonal pairs with exact source and target fibers."""

import importlib.util
from collections import defaultdict
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
PARENT = GOAL / "n131_w18_allseed_fourpair_20261012/fourpair_v2.py"
spec = importlib.util.spec_from_file_location("allseed_fourpair_parent", PARENT)
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)


def exactly_one(circuit, flags):
    circuit.clauses.append(" ".join(map(str, flags)) + " 0")
    for a, b in combinations(flags, 2):
        circuit.clauses.append(f"-{a} -{b} 0")


def build(target_reciprocals):
    """Return exact nonexceptional-chart XCNF and selected source wires."""
    assert len(target_reciprocals) in (1, 4)
    field = parent.Field(131, [0, 1, 2, 13])
    width = 18
    columns = parent.support("n131")
    assert len(columns) == 131307
    root, nodes = parent.bdd(set(columns), width)
    circuit = parent.KaratsubaCircuit(131, [0, 1, 2, 13])
    algebra = parent.Algebra(circuit, field, dense_and_threshold=3000)
    masks, outputs, points = [], [], []
    for _ in range(5):
        pair_masks = []
        for _ in range(2):
            bits = [circuit.variable() for _ in range(width)]
            pair_masks.append(bits)
            masks.append(bits)
            parent.emit_bdd(circuit, bits, root, nodes)
        out = [circuit.variable() for _ in range(131)]
        circuit.clauses.append(" ".join(map(str, out)) + " 0")
        outputs.append(out)
        a, b = [algebra.expression((wire, 1 << (i+1))
                   for i, wire in enumerate(bits)) for bits in pair_masks]
        product = algebra.mul(a, b)
        c = algebra.from_bits(out)
        cp = algebra.mul(c, product)
        equation = algebra.add(algebra.square(cp), cp,
                               algebra.square(algebra.add(a, b)),
                               algebra.square(c))
        circuit.require_zero(equation.bits())
        points.append(c)
    grouped = defaultdict(list)
    for mask, column in columns.items():
        grouped[column].append(mask)
    collision_pairs = [(a, b) for group in grouped.values()
                       for a, b in combinations(sorted(group), 2)]
    def mismatch(bits, code):
        return [(-wire if code >> i & 1 else wire)
                for i, wire in enumerate(bits)]
    shield_clauses = 0
    for i in range(10):
        for j in range(i+1, 10):
            different = [circuit.xor((a, b)) for a, b in zip(masks[i], masks[j])]
            circuit.clauses.append(" ".join(map(str, different)) + " 0")
            for a, b in collision_pairs:
                for left, right in ((a, b), (b, a)):
                    circuit.clauses.append(" ".join(map(str,
                        mismatch(masks[i], left)+mismatch(masks[j], right))) + " 0")
                    shield_clauses += 1
    middle = []
    for _ in range(3):
        bits = [circuit.variable() for _ in range(131)]
        circuit.clauses.append(" ".join(map(str, bits)) + " 0")
        middle.append(bits)
    def s3(a, b, z):
        ab = algebra.mul(a, b)
        abz = algebra.mul(ab, z)
        equation = algebra.add(algebra.square(abz), abz,
                               algebra.square(algebra.add(a, b)), algebra.square(z))
        circuit.require_zero(equation.bits())
    m0, m1, m2 = [algebra.from_bits(bits) for bits in middle]
    s3(points[0], points[1], m0)
    s3(points[2], points[3], m1)
    s3(m0, m1, m2)
    flags = []
    if len(target_reciprocals) == 1:
        target = algebra.expression(((-1, int(target_reciprocals[0])),))
    else:
        flags = [circuit.variable() for _ in range(4)]
        exactly_one(circuit, flags)
        target_bits = circuit.linear_element(flags, list(map(int, target_reciprocals)))
        target = algebra.from_bits(target_bits)
    s3(m2, points[4], target)
    wires = {"masks": masks, "pair_outputs": outputs,
             "middle": middle, "target_flags": flags}
    metadata = {"source_masks": len(columns), "folded_columns": len(grouped),
                "source_bdd_nodes": len(nodes),
                "same_column_mask_pairs": len(collision_pairs),
                "folded_column_shield_clauses": shield_clauses,
                "pair_count": 5, "source_rotations": [0]*5,
                "target_reciprocals": list(map(int, target_reciprocals)),
                "sparse_mul_calls": algebra.sparse_mul_calls,
                "generic_mul_calls": algebra.generic_mul_calls}
    return circuit, wires, metadata


def check_assignment(circuit, wires, fixture):
    """Evaluate every gate and clause on the checked Sage constructed chart."""
    assert len(wires["target_flags"]) == 0
    values = {}
    def put(bits, number):
        for i, wire in enumerate(bits):
            values[wire] = int(number) >> i & 1
    for pair, group in zip(fixture["masks"],
                           [wires["masks"][i:i+2] for i in range(0, 10, 2)]):
        for mask, bits in zip(pair, group):
            put(bits, mask)
    for value, bits in zip(fixture["pair_reciprocals"], wires["pair_outputs"]):
        put(bits, value)
    for value, bits in zip(fixture["intermediate_reciprocals"], wires["middle"]):
        put(bits, value)
    gates = [(out, "and", key) for key, out in circuit.and_cache.items()]
    gates += [(out, "xor", key) for key, out in circuit.xor_cache.items()]
    def value(wire):
        return 1 if wire == -1 else 0 if wire == 0 else values[wire]
    for out, kind, key in sorted(gates):
        assert out not in values
        values[out] = (value(key[0]) & value(key[1])) if kind == "and" else (
            key[1] ^ sum(value(wire) for wire in key[0]) % 2)
    assert len(values) == circuit.next_var-1
    for line in circuit.clauses:
        literals = [int(word) for word in line.split()[:-1]]
        assert any((value(abs(lit)) if lit > 0 else 1-value(abs(lit)))
                   for lit in literals), line
    for line in circuit.xors:
        literals = [int(word) for word in line.split()[1:-1]]
        assert sum(value(abs(lit)) if lit > 0 else 1-value(abs(lit))
                   for lit in literals) % 2 == 1, line
    return {"status": "PASS_COMPLETE_N131_FIVEPAIR_ASSIGNMENT",
            "variables": len(values), "cnf_clauses_checked": len(circuit.clauses),
            "native_xor_rows_checked": len(circuit.xors)}
