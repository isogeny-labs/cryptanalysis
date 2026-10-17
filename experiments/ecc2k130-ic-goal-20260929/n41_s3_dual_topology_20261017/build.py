"""Build and check the unpinned dual-tree N41 target formula."""
import hashlib
import importlib.util
import json
import resource
import time
from pathlib import Path

import circuit

D = Path(__file__).resolve().parent
ROOT = D.parent
BASE = ROOT / "n41_s3_rationality_propagation_20261017"
HIT = ROOT / "n41_sixpair_shared_target_20261017/join_audit_result.json"
GEO = ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json"
spec = importlib.util.spec_from_file_location("n41_direct_leaf_builder", BASE / "build.py")
base_builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base_builder)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assignment(wires, geometry, hit, target_reciprocal):
    values = base_builder.assignment(wires, geometry, hit, target_reciprocal)
    nodes = [tuple(row["raw_sum"]) for row in hit["pair_rows"]]
    for left, right, out in circuit.DUAL_LINKS:
        point = circuit.old.replay.add(circuit.F, nodes[left], nodes[right])
        assert point is not None and point[0] != 0
        if out == 10:
            assert list(point) == hit["raw_target"]
        else:
            assert out == len(nodes)
            nodes.append(point)
            reciprocal = circuit.F.inv(point[0])
            values.update({wire: (reciprocal >> bit) & 1
                           for bit, wire in enumerate(wires["dual_middle"][out - 6])})
    coords = [circuit.F.inv(point[0]) for point in nodes] + [target_reciprocal]
    for gate, (left, right, out) in enumerate(circuit.DUAL_LINKS):
        a, b, z = (coords[index] for index in (left, right, out))
        total = a ^ b ^ z
        branch = (circuit.F.mul(circuit.F.mul(a, b), z) ^
                  circuit.F.halftrace(circuit.F.square(total)))
        assert branch in (0, 1)
        values[wires["dual_branches"][gate]] = branch
    return values


def main():
    protocol = json.loads((D / "protocol.json").read_text())
    assert sha(D / "circuit.py") == protocol["circuit_sha256"]
    assert sha(D / "build.py") == protocol["builder_sha256"]
    for relative, digest in protocol["sources"].items():
        assert sha(ROOT / relative) == digest, relative
    geometry = json.loads(GEO.read_text())
    hit = json.loads(HIT.read_text())
    assert hit["raw_target"] == protocol["public_raw_point"]
    target_reciprocal = circuit.F.inv(hit["raw_target"][0])
    start = time.monotonic_ns()
    machine, wires = circuit.build(target_reciprocal)
    built = time.monotonic_ns()
    initial = assignment(wires, geometry, hit, target_reciprocal)
    completed = circuit.old.old.complete_assignment(machine, initial)
    check = circuit.old.old.check_assignment(machine, completed)
    assert check["clauses"] == len(machine.clauses)
    assert check["native_xor_rows"] == len(machine.xors)
    checked = time.monotonic_ns()
    path = D / "public.xcnf"
    if path.exists():
        raise FileExistsError(path)
    machine.write(path)
    result = {
        "status": "PASS_DUAL_TREE_PUBLIC_FORMULA_BUILD",
        "candidate_id": None,
        "protocol_sha256": sha(D / "protocol.json"),
        "target_reciprocal": target_reciprocal,
        "variables": machine.next_var - 1,
        "and_gates": machine.and_count,
        "first_tree_and_gates": wires["first_tree_and_count"],
        "second_tree_added_and_gates": machine.and_count - wires["first_tree_and_count"],
        "ordinary_clauses": len(machine.clauses),
        "native_xor_rows": len(machine.xors),
        "formula_sha256": sha(path),
        "formula_bytes": path.stat().st_size,
        "build_ns": built - start,
        "assignment_check_ns": checked - built,
        "assignment_check": check,
        "peak_rss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    (D / "build_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in (
        "status", "variables", "and_gates", "first_tree_and_gates",
        "second_tree_added_and_gates", "ordinary_clauses", "native_xor_rows",
        "formula_sha256", "assignment_check")}, sort_keys=True))


if __name__ == "__main__":
    main()
