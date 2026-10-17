"""Build the public six-pair formula and check the archived relation assignment."""
import hashlib
import json
import resource
import time
from pathlib import Path

import circuit


D = Path(__file__).resolve().parent
ROOT = D.parent
HIT = ROOT / "n41_sixpair_shared_target_20261017" / "join_audit_result.json"
GEO = ROOT / "n41_w8_fixed_sum_table_20261009" / "geometry.json"
F = circuit.F


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assignment(wires, geometry, hit, target_reciprocal):
    values = {}
    def bind(bits, number):
        values.update({wire: (number >> i) & 1 for i, wire in enumerate(bits)})
    nodes = []
    for slot, pair in enumerate(hit["pair_rows"]):
        state = geometry["blocks"][slot]["states"][pair["state_id"]]
        assert state["raw_sum"] == pair["raw_sum"]
        assert state["a"] == pair["masks"][0]
        code = sum(((state["a"] >> bit) & 1) << j
                   for j, bit in enumerate(wires["source_bits"]))
        bind(wires["codes"][slot], code)
        reciprocal = F.inv(state["raw_sum"][0])
        unrotated = circuit.old.frob(reciprocal,
                                     circuit.N - geometry["rotations"][slot])
        bind(wires["outputs"][slot], unrotated)
        nodes.append(tuple(state["raw_sum"]))
    intermediates = []
    for left, right, out in circuit.LINKS:
        point = circuit.old.replay.add(F, nodes[left], nodes[right])
        assert point is not None and point[0] != 0
        if out == 10:
            assert list(point) == hit["raw_target"]
        else:
            assert out == len(nodes)
            nodes.append(point)
            reciprocal = F.inv(point[0])
            intermediates.append(reciprocal)
            bind(wires["middle"][out - 6], reciprocal)
    coords = [F.inv(point[0]) for point in nodes] + [target_reciprocal]
    assert len(coords) == 11
    for gate, (left, right, out) in enumerate(circuit.LINKS):
        a, b, z = (coords[i] for i in (left, right, out))
        total = a ^ b ^ z
        branch = F.mul(F.mul(a, b), z) ^ F.halftrace(F.square(total))
        assert branch in (0, 1)
        values[wires["branches"][gate]] = branch
    return values


def main():
    p = json.loads((D / "protocol.json").read_text())
    assert sha(D / "circuit.py") == p["circuit_sha256"]
    assert sha(D / "build.py") == p["builder_sha256"]
    assert sha(GEO) == p["geometry_sha256"]
    assert sha(HIT) == p["relation_sha256"]
    geometry = json.loads(GEO.read_text())
    hit = json.loads(HIT.read_text())
    assert hit["raw_target"] == p["public_raw_point"]
    target = F.inv(hit["raw_target"][0])
    start = time.monotonic_ns()
    machine, wires = circuit.build(target)
    built = time.monotonic_ns()
    initial = assignment(wires, geometry, hit, target)
    completed = circuit.old.old.complete_assignment(machine, initial)
    check = circuit.old.old.check_assignment(machine, completed)
    checked = time.monotonic_ns()
    path = D / "public.xcnf"
    if path.exists():
        raise FileExistsError(path)
    machine.write(path)
    written = time.monotonic_ns()
    result = {
        "status": "PASS_PUBLIC_S3_RATIONALITY_FORMULA_BUILD",
        "protocol_sha256": sha(D / "protocol.json"),
        "target_reciprocal": target,
        "variables": machine.next_var - 1,
        "and_gates": machine.and_count,
        "ordinary_clauses": len(machine.clauses),
        "native_xor_rows": len(machine.xors),
        "leaf_and_checkpoints": wires["leaf_and_checkpoints"],
        "formula_sha256": sha(path),
        "formula_bytes": path.stat().st_size,
        "build_ns": built - start,
        "assignment_check_ns": checked - built,
        "serialize_ns": written - checked,
        "assignment_check": check,
        "peak_rss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    (D / "build_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in (
        "status", "variables", "and_gates", "ordinary_clauses",
        "native_xor_rows", "formula_sha256", "assignment_check")}, sort_keys=True))


if __name__ == "__main__":
    main()
