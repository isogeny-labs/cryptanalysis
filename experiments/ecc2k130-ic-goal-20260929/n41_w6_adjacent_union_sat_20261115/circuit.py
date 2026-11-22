"""Exact six-leaf N41 union lookup and balanced S3 chain in native-XOR CNF."""

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OLD = ROOT / "n41_sixpair_shared_target_20261017" / "circuit.py"
UNION = ROOT / "n41_w6_adjacent_union_screen_20261115" / "union_rows.json"
spec = importlib.util.spec_from_file_location("n41_sixpair_circuit_union_source", OLD)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
F = old.F
N = 41
LINKS = old.BALANCED_LINKS


def tables():
    data = json.loads(UNION.read_text())
    assert [x["rotation"] for x in data] == [0, 5, 10, 15, 20, 25]
    answer = []
    for block in data:
        rows = block["rows"]
        assert len(rows) == 64
        table = []
        for branch in ("original", "image"):
            for i in range(0, 64, 2):
                assert rows[i][branch][0] == rows[i+1][branch][0]
                x = rows[i][branch][0]
                assert x not in (0, 1)
                table.append(F.inv(x))
        assert len(table) == len(set(table)) == 64
        answer.append(table)
    return answer


def build(target_x):
    table = tables()
    machine = old.old.KaratsubaCircuit(N, [0, 3])
    alg = old.old.Algebra(machine, old.Field(), dense_and_threshold=3000)
    codes, leaves, middle, branches = [], [], [], []
    for slot in range(6):
        selector = [machine.variable() for _ in range(6)]
        output = [machine.variable() for _ in range(N)]
        codes.append(selector)
        leaves.append(output)
        for code, value in enumerate(table[slot]):
            mismatch = [-wire if code >> j & 1 else wire
                        for j, wire in enumerate(selector)]
            for bit, wire in enumerate(output):
                literal = wire if value >> bit & 1 else -wire
                machine.clauses.append(" ".join(map(str, [*mismatch, literal])) + " 0")
    middle = [[machine.variable() for _ in range(N)] for _ in range(4)]
    branches = [machine.variable() for _ in range(5)]
    ht_basis = []
    for bit in range(N):
        value, image = F.square(1 << bit), 0
        for _ in range((N + 1) // 2):
            image ^= value
            value = F.square(F.square(value))
        ht_basis.append(image)
    trace_basis = [old.trace(1 << bit) for bit in range(N)]
    target_reciprocal = F.inv(target_x)
    nodes = [alg.from_bits(row) for row in leaves + middle]
    nodes.append(alg.expression(((-1, target_reciprocal),)))
    for gate, (left, right, upper) in enumerate(LINKS):
        a, b, z = nodes[left], nodes[right], nodes[upper]
        total = alg.add(a, b, z)
        half_trace = machine.linear_element(total.bits(), ht_basis)
        machine.require_zero(alg.add(alg.mul(alg.mul(a, b), z),
                                     alg.from_bits(half_trace),
                                     alg.expression(((branches[gate], 1),))).bits())
        machine.require_zero([machine.xor(w for w, t in zip(total.bits(), trace_basis) if t)])
        if upper < 10:
            machine.clauses.append(" ".join(map(str, middle[upper-6])) + " 0")
    return machine, {"codes": codes, "leaves": leaves, "middle": middle,
                     "branches": branches, "target_reciprocal": target_reciprocal,
                     "table": table}
