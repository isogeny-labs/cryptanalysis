"""Exact forward-root S3 circuit on the frozen unpinned N41 W8 ten-pair source."""

import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
INPUT = GOAL / "n41_w8_sixpair_mitm_20261011/join_input.tsv"
POSITIVE = GOAL / "n41_w8_tenpair_density_control_20261012/audit_result.json"
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT / "experiments/koblitz-polynomial-w-pair-20260925"), str(GOAL)]
from karatsuba_circuit import KaratsubaCircuit  # noqa: E402
from functional_inverse_circuit import inverse  # noqa: E402
from functional_pair_root_circuit import half_trace, zero_flag  # noqa: E402

N = 41
MOD = (1 << 41) | (1 << 3) | 1
SLOTS = (0, 1, 2, 3, 4, 5, 0, 1, 2, 3)
TREE = ((0, 1), (2, 3), (4, 5), (6, 7), (10, 11),
        (12, 13), (14, 15), (16, 8), (17, 9))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mul(a, b):
    out = 0
    while b:
        if b & 1:
            out ^= a
        b >>= 1
        a <<= 1
        if a & (1 << N):
            a ^= MOD
    return out


def square(a):
    return mul(a, a)


def inv(a):
    assert a
    out = 1
    power = a
    exponent = (1 << N) - 2
    while exponent:
        if exponent & 1:
            out = mul(out, power)
        power = square(power)
        exponent >>= 1
    assert mul(a, out) == 1
    return out


def add(left, right):
    if left is None:
        return right
    if right is None:
        return left
    x1, y1 = left
    x2, y2 = right
    if x1 == x2:
        if y1 != y2 or x1 == 0:
            return None
        lam = x1 ^ mul(y1, inv(x1))
        x3 = square(lam) ^ lam
        y3 = square(x1) ^ mul(lam ^ 1, x3)
    else:
        lam = mul(y1 ^ y2, inv(x1 ^ x2))
        x3 = square(lam) ^ lam ^ x1 ^ x2
        y3 = mul(lam, x1 ^ x3) ^ x3 ^ y1
    return x3, y3


def source():
    lists = [[None] * 140 for _ in range(6)]
    targets = [None] * 4
    checks = []
    with INPUT.open() as stream:
        assert stream.readline().split() == ["ECC2K41", "6", "140", "4"]
        for line in stream:
            parts = line.split()
            if parts[0] == "T":
                index, x, y = map(int, parts[1:])
                targets[index] = (x, y)
            elif parts[0] == "S":
                slot, sid, edge, a, b, sa, sb, x, y = map(int, parts[1:])
                assert edge == sid // 4 and a ^ b == 184 and a < b
                assert lists[slot][sid] is None
                lists[slot][sid] = {"edge": edge, "masks": (a, b),
                                    "signs": (sa, sb), "point": (x, y), "z": inv(x)}
            elif parts[0] == "C":
                checks.append(tuple(map(int, parts[1:])))
            else:
                raise ValueError(parts[0])
    assert all(target is not None for target in targets)
    assert all(all(state is not None for state in slot) for slot in lists)
    assert len(checks) == 128
    for x1, y1, x2, y2, x3, y3 in checks:
        got = add((x1, y1), (x2, y2))
        assert (got is None and x3 < 0) or got == (x3, y3)
    return lists, targets


def root_value(a, b, branch):
    p = mul(a, b)
    aa = 1 ^ square(p)
    cc = square(a ^ b)
    assert p
    if not aa:
        z = cc
    else:
        arg = mul(mul(aa, cc), square(inv(p)))
        h = 0
        term = arg
        for _ in range((N + 1) // 2):
            h ^= term
            term = square(square(term))
        assert square(h) ^ h == arg
        z = mul(mul(p, inv(aa)), h ^ branch)
    assert mul(aa, square(z)) ^ mul(p, z) ^ cc == 0
    return z


def positive_chart(lists, targets):
    audit = json.loads(POSITIVE.read_text())
    states = audit["source_pairs"]
    assert len(states) == 10 and audit["raw_target_preimage_index"] == 1
    ids = [row["state_id"] for row in states]
    points = [lists[slot][sid]["point"] for slot, sid in zip(SLOTS, ids)]
    assert all(tuple(row["pair_point"]) == point for row, point in zip(states, points))
    assert len({lists[slot][sid]["edge"] for slot, sid in zip(SLOTS, ids)}) == 10
    nodes = list(points)
    branches = []
    for left, right in TREE:
        point = add(nodes[left], nodes[right])
        assert point is not None and point[0]
        nodes.append(point)
        a, b, z = inv(nodes[left][0]), inv(nodes[right][0]), inv(point[0])
        choices = [branch for branch in (0, 1) if root_value(a, b, branch) == z]
        assert choices
        branches.append(choices[0])
    assert nodes[-1] == targets[1]
    return {"state_ids": ids, "branch_bits": branches, "target_index": 1,
            "point_chain": [list(point) for point in nodes],
            "target_point": list(targets[1])}


def s3_forward(circuit, a, b):
    p = circuit.mul(a, b)
    aa = circuit.add(circuit.constant(1), circuit.square(p))
    cc = circuit.square(circuit.add(a, b))
    inv_p = inverse(circuit, p)
    inv_a = inverse(circuit, aa)
    arg = circuit.mul(circuit.mul(aa, cc), circuit.square(inv_p))
    h = half_trace(circuit, arg)
    circuit.require_zero(circuit.add(circuit.add(circuit.square(h), h), arg))
    branch = circuit.variable()
    h = list(h)
    h[0] = circuit.xor((h[0], branch))
    generic = circuit.mul(circuit.mul(p, inv_a), h)
    special = zero_flag(circuit, aa)
    z = [circuit.xor((x, circuit.and_(special, circuit.xor((x, y)))))
         for x, y in zip(generic, cc)]
    circuit.clauses.append(" ".join(str(wire) for wire in z) + " 0")
    lhs = circuit.add(circuit.mul(aa, circuit.square(z)), circuit.mul(p, z))
    circuit.require_zero(circuit.add(lhs, cc))
    return z, branch


def exactly_one(circuit, wires):
    circuit.clauses.append(" ".join(map(str, wires)) + " 0")
    for i, first in enumerate(wires):
        for second in wires[i + 1:]:
            circuit.clauses.append(f"-{first} -{second} 0")


def build(lists, targets, chart, pin):
    circuit = KaratsubaCircuit(N, [0, 3])
    selectors = []
    nodes = []
    for slot in SLOTS:
        wires = [circuit.variable() for _ in range(140)]
        exactly_one(circuit, wires)
        selectors.append(wires)
        nodes.append(circuit.linear_element(wires, [row["z"] for row in lists[slot]]))
    for left in range(10):
        for right in range(left + 1, 10):
            for edge in range(35):
                for a in selectors[left][4 * edge:4 * edge + 4]:
                    for b in selectors[right][4 * edge:4 * edge + 4]:
                        circuit.clauses.append(f"-{a} -{b} 0")
    branch_wires = []
    for left, right in TREE:
        out, wire = s3_forward(circuit, nodes[left], nodes[right])
        nodes.append(out)
        branch_wires.append(wire)
    flags = [circuit.variable() for _ in range(4)]
    exactly_one(circuit, flags)
    target = circuit.linear_element(flags, [inv(point[0]) for point in targets])
    circuit.require_zero(circuit.add(nodes[-1], target))
    if pin:
        for row, sid in zip(selectors, chart["state_ids"]):
            circuit.clauses.append(f"{row[sid]} 0")
        for wire, bit in zip(branch_wires, chart["branch_bits"]):
            circuit.clauses.append(f"{wire if bit else -wire} 0")
        circuit.clauses.append(f"{flags[chart['target_index']]} 0")
    return circuit, {"selectors": selectors, "branches": branch_wires,
                     "flags": flags, "nodes": nodes}


def save(path, obj):
    with path.open("x") as stream:
        json.dump(obj, stream, sort_keys=True, indent=2)
        stream.write("\n")


def prepare():
    lists, targets = source()
    chart = positive_chart(lists, targets)
    save(HERE / "positive_chart.json", chart)
    print("PASS_N41_FUNCTIONAL_CHART", len(chart["point_chain"]), chart["branch_bits"])


def formulas():
    lists, targets = source()
    chart = json.loads((HERE / "positive_chart.json").read_text())
    assert chart == positive_chart(lists, targets)
    results = []
    for name, pin in (("control", True), ("ordinary", False)):
        start = time.monotonic_ns()
        circuit, wires = build(lists, targets, chart, pin)
        constructed = time.monotonic_ns()
        path = HERE / f"{name}.xcnf"
        circuit.write(path)
        written = time.monotonic_ns()
        results.append({"name": name, "pinned": pin,
                        "variables": circuit.next_var - 1,
                        "cnf_clauses": len(circuit.clauses),
                        "native_xor_rows": len(circuit.xors),
                        "and_gates": circuit.and_count,
                        "build_ns": constructed - start,
                        "write_ns": written - constructed,
                        "formula_bytes": path.stat().st_size,
                        "formula_sha256": sha(path)})
        print(results[-1], flush=True)
    save(HERE / "build_result.json", {"status": "BUILT_N41_TENPAIR_FUNCTIONAL_ROOT",
                                      "candidate_id": None, "formulas": results,
                                      "source_sha256": sha(__file__),
                                      "input_sha256": sha(INPUT),
                                      "positive_chart_sha256": sha(HERE / "positive_chart.json")})


if __name__ == "__main__":
    {"prepare": prepare, "formulas": formulas}[sys.argv[1]]()
