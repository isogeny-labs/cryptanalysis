"""Build exact N41 union-source XCNF and replay a known ordinary relation."""

import hashlib
import json
import resource
import time
from pathlib import Path

import circuit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
F = circuit.F


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bind_bits(values, wires, number):
    values.update({wire: (number >> i) & 1 for i, wire in enumerate(wires)})


def assignment(wires, chosen, rows, target):
    values = {}
    points = []
    for slot, chosen_id in enumerate(chosen):
        row = rows[slot]["rows"][chosen_id % 64]
        branch = "image" if chosen_id >= 64 else "original"
        point = tuple(row[branch])
        points.append(point)
        code = (chosen_id % 64)//2 + (32 if chosen_id >= 64 else 0)
        bind_bits(values, wires["codes"][slot], code)
        bind_bits(values, wires["leaves"][slot], F.inv(point[0]))
        assert wires["table"][slot][code] == F.inv(point[0])
    assert tuple(target) == tuple(circuit.old.replay.add(F, 
        circuit.old.replay.add(F, circuit.old.replay.add(F, points[0], points[1]),
                               circuit.old.replay.add(F, points[2], points[3])),
        circuit.old.replay.add(F, points[4], points[5])))
    nodes = points[:]
    for gate, (left, right, upper) in enumerate(circuit.LINKS):
        summed = circuit.old.replay.add(F, nodes[left], nodes[right])
        assert summed is not None and summed[0] not in (0, 1)
        if upper == 10:
            assert tuple(summed) == tuple(target)
        else:
            assert upper == len(nodes)
            nodes.append(summed)
            bind_bits(values, wires["middle"][upper-6], F.inv(summed[0]))
        a = F.inv(nodes[left][0])
        b = F.inv(nodes[right][0])
        z = F.inv(summed[0])
        total = a ^ b ^ z
        branch_value = F.mul(F.mul(a, b), z) ^ F.halftrace(F.square(total))
        assert branch_value in (0, 1)
        values[wires["branches"][gate]] = branch_value
    return values


def main():
    p = json.loads((HERE / "protocol_v2.json").read_text())
    assert p["status"] == "FROZEN_AMENDED_BEFORE_BUILD"
    assert sha(__file__) == p["builder_sha256"]
    assert sha(HERE / "circuit.py") == p["circuit_sha256"]
    assert sha(HERE / "independent_replay.py") == p["helper_source_sha256"]
    for path, digest in p["source_sha256"].items():
        assert sha(ROOT / path) == digest
    rows = json.loads((ROOT / "n41_w6_adjacent_union_screen_20261115" /
                       "union_rows.json").read_text())
    receipt = json.loads((ROOT / "n41_w6_adjacent_union_screen_20261115" /
                          "ordinary_receipt.json").read_text())
    target = receipt["target"]
    start = time.monotonic_ns()
    machine, wires = circuit.build(target[0])
    built = time.monotonic_ns()
    initial = assignment(wires, receipt["chosen_ids"], rows, target)
    completed = circuit.old.old.complete_assignment(machine, initial)
    check = circuit.old.old.check_assignment(machine, completed)
    assert check["clauses"] == len(machine.clauses)
    assert check["native_xor_rows"] == len(machine.xors)
    checked = time.monotonic_ns()
    output = HERE / "ordinary.xcnf"
    assert not output.exists()
    machine.write(output)
    result = {
        "kind": "n41_w6_adjacent_union_s3_exact_formula_build",
        "status": "PASS_PLANTED_ASSIGNMENT_ON_ORDINARY_PUBLIC_TARGET",
        "protocol_sha256": sha(HERE / "protocol_v2.json"),
        "target": target,
        "chosen_ids_positive_control": receipt["chosen_ids"],
        "leaf_selector_bits_per_position": 6,
        "leaf_x_per_position": 64,
        "variables": machine.next_var-1,
        "and_gates": machine.and_count,
        "ordinary_clauses": len(machine.clauses),
        "native_xor_rows": len(machine.xors),
        "formula_sha256": sha(output),
        "formula_bytes": output.stat().st_size,
        "build_ns": built-start,
        "assignment_check_ns": checked-built,
        "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    (HERE / "build_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
