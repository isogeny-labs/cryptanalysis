"""Functional affine slopes on the frozen N41 ten-pair public relation."""

import importlib.util
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
PARENT = GOAL / "n41_fullpoint_balanced_sat_20261012"
spec = importlib.util.spec_from_file_location("fullpoint_parent", PARENT / "run.py")
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
old = parent.old


def formula(lists, targets, pin, witness):
    circuit = old.KaratsubaCircuit(old.N, [0, 3])
    selectors = []
    nodes = []
    for slot in old.SLOTS:
        row = [circuit.variable() for _ in range(140)]
        old.exactly_one(circuit, row)
        selectors.append(row)
        nodes.append((circuit.linear_element(row, [state["point"][0] for state in lists[slot]]),
                      circuit.linear_element(row, [state["point"][1] for state in lists[slot]])))
    for left in range(10):
        for right in range(left + 1, 10):
            for edge in range(35):
                for a in selectors[left][4 * edge:4 * edge + 4]:
                    for b in selectors[right][4 * edge:4 * edge + 4]:
                        circuit.clauses.append(f"-{a} -{b} 0")
    slopes = []
    outputs = []
    for left, right in old.TREE:
        x1, y1 = nodes[left]
        x2, y2 = nodes[right]
        denominator = circuit.add(x1, x2)
        parent.nonzero(circuit, denominator)
        inverse = old.inverse(circuit, denominator)
        slope = circuit.mul(circuit.add(y1, y2), inverse)
        x3 = circuit.add(circuit.add(circuit.square(slope), slope), denominator)
        y3 = circuit.add(circuit.add(circuit.mul(slope, circuit.add(x1, x3)), x3), y1)
        slopes.append(slope)
        outputs.append((x3, y3))
        nodes.append((x3, y3))
    flags = [circuit.variable() for _ in range(4)]
    old.exactly_one(circuit, flags)
    circuit.require_zero(circuit.add(nodes[-1][0],
                                     circuit.linear_element(flags, [p[0] for p in targets])))
    circuit.require_zero(circuit.add(nodes[-1][1],
                                     circuit.linear_element(flags, [p[1] for p in targets])))
    if pin:
        for row, sid in zip(selectors, witness["state_ids"]):
            circuit.clauses.append(f"{row[sid]} 0")
        circuit.clauses.append(f"{flags[witness['target_index']]} 0")
    return circuit, {"selectors": selectors, "slopes": slopes,
                     "outputs": outputs, "flags": flags}


def positive_assignment(circuit, wires, witness):
    initial = {}
    for row, sid in zip(wires["selectors"], witness["state_ids"]):
        initial.update({wire: int(index == sid) for index, wire in enumerate(row)})
    initial.update({wire: int(index == witness["target_index"])
                    for index, wire in enumerate(wires["flags"])})
    values = parent.check.complete_assignment(circuit, initial)
    checked = parent.check.check_assignment(circuit, values)
    points = [tuple(p) for p in witness["point_chain"]]
    for index, (left, right) in enumerate(old.TREE):
        x1, y1 = points[left]
        x2, y2 = points[right]
        assert x1 != x2
        expected_slope = old.mul(y1 ^ y2, old.inv(x1 ^ x2))
        for bits, expected in ((wires["slopes"][index], expected_slope),
                               (wires["outputs"][index][0], points[10 + index][0]),
                               (wires["outputs"][index][1], points[10 + index][1])):
            observed = sum((values[wire] if wire > 0 else int(wire == -1)) << bit
                           for bit, wire in enumerate(bits))
            assert observed == expected
    return checked


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    extra = {"parent_runner": PARENT / "run.py",
             "inverse": GOAL / "functional_inverse_circuit.py",
             "karatsuba": GOAL.parents[1] / "experiments/koblitz-polynomial-w-pair-20260925/karatsuba_circuit.py",
             "circuit": GOAL.parents[1] / "experiments/koblitz-s5-invariant-20260924/circuit_sat.py"}
    assert {name: parent.sha(path) for name, path in extra.items()} == protocol["extra_sha256"]
    parent.HERE = HERE
    parent.formula = formula
    parent.positive_assignment = positive_assignment
    parent.main()


if __name__ == "__main__":
    main()
