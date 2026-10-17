"""Build one unpinned N41 orbit formula and check all archived relations."""
import hashlib
import json
import resource
import time
from pathlib import Path

import circuit

D = Path(__file__).resolve().parent
ROOT = D.parent
GEO = ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json"
JOIN = ROOT / "n41_sixpair_target_orbit_20261016/join_result.json"
F = circuit.F


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def assignment(wires, geometry, orbit_index, state_ids):
    values = {}

    def bind(bits, number):
        values.update({wire: (number >> i) & 1 for i, wire in enumerate(bits)})

    nodes = []
    for slot, state_id in enumerate(state_ids):
        state = geometry["blocks"][slot]["states"][state_id]
        code = sum(((state["a"] >> bit) & 1) << j
                   for j, bit in enumerate(wires["source_bits"]))
        bind(wires["codes"][slot], code)
        reciprocal = F.inv(state["raw_sum"][0])
        unrotated = circuit.old.frob(reciprocal,
                                     circuit.N - geometry["rotations"][slot])
        bind(wires["outputs"][slot], unrotated)
        nodes.append(tuple(state["raw_sum"]))
    for j, wire in enumerate(wires["target_selector"]):
        values[wire] = int(j == orbit_index)
    for left, right, out in circuit.LINKS:
        point = circuit.old.replay.add(F, nodes[left], nodes[right])
        assert point is not None and point[0] != 0
        if out == 10:
            assert F.inv(point[0]) == wires["target_orbit"][orbit_index]
        else:
            assert out == len(nodes)
            nodes.append(point)
            bind(wires["middle"][out - 6], F.inv(point[0]))
    coords = [F.inv(point[0]) for point in nodes] + [
        wires["target_orbit"][orbit_index]]
    for gate, (left, right, out) in enumerate(circuit.LINKS):
        a, b, z = (coords[index] for index in (left, right, out))
        total = a ^ b ^ z
        branch = F.mul(F.mul(a, b), z) ^ F.halftrace(F.square(total))
        assert branch in (0, 1)
        values[wires["branches"][gate]] = branch
    return values


def main():
    p = read(D / "protocol.json")
    assert sha(D / "circuit.py") == p["circuit_sha256"]
    assert sha(D / "build.py") == p["builder_sha256"]
    for relative, digest in p["sources"].items():
        assert sha(ROOT / relative) == digest, relative
    geometry = read(GEO)
    join = read(JOIN)
    assert len(join["hits"]) == circuit.N == 41
    qx, qy = p["public_raw_point"]
    target = F.inv(qx)
    start = time.monotonic_ns()
    machine, wires = circuit.build(target)
    built = time.monotonic_ns()
    controls = []
    for expected_index, line in enumerate(join["hits"]):
        words = line.split()
        assert words[0] == "ORBIT_HIT" and int(words[1]) == expected_index
        state_ids = [int(x) for x in words[2:8]]
        initial = assignment(wires, geometry, expected_index, state_ids)
        completed = circuit.old.old.complete_assignment(machine, initial)
        check = circuit.old.old.check_assignment(machine, completed)
        assert check["clauses"] == len(machine.clauses)
        assert check["native_xor_rows"] == len(machine.xors)
        controls.append({"orbit_index": expected_index, "state_ids": state_ids,
                         "checked_variables": len(completed)})
    checked = time.monotonic_ns()
    path = D / "public.xcnf"
    if path.exists():
        raise FileExistsError(path)
    machine.write(path)
    output = {
        "status": "PASS_DIRECT_LEAF_ORBIT_FORMULA_BUILD",
        "candidate_id": None,
        "protocol_sha256": sha(D / "protocol.json"),
        "target_reciprocal": target,
        "target_orbit": wires["target_orbit"],
        "orbit_size": len(wires["target_orbit"]),
        "variables": machine.next_var - 1,
        "and_gates": machine.and_count,
        "ordinary_clauses": len(machine.clauses),
        "native_xor_rows": len(machine.xors),
        "formula_sha256": sha(path),
        "formula_bytes": path.stat().st_size,
        "build_ns": built - start,
        "assignment_check_ns": checked - built,
        "controls": controls,
        "peak_rss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    (D / "build_result.json").write_text(json.dumps(output, sort_keys=True, indent=2) + "\n")
    print(json.dumps({key: output[key] for key in (
        "status", "orbit_size", "variables", "and_gates", "ordinary_clauses",
        "native_xor_rows", "formula_sha256")}, sort_keys=True))


if __name__ == "__main__":
    main()
