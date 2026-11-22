"""Build the unpinned hybrid and verify the archived ordinary relation assignment."""
import hashlib
import json
import resource
import time
from pathlib import Path

import circuit

D = Path(__file__).resolve().parent
ROOT = D.parent
F = circuit.F
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_text())


def bind(values, wires, number):
    values.update({wire: (number >> bit) & 1 for bit, wire in enumerate(wires)})


def add(point_a, point_b):
    result = circuit.direct.old.replay.add(F, point_a, point_b)
    assert result is not None and result[0] != 0
    return result


def main():
    protocol = read(D / "protocol.json")
    assert sha(D / "build.py") == protocol["builder_sha256"]
    assert sha(D / "circuit.py") == protocol["circuit_sha256"]
    for relative, digest in protocol["sources"].items():
        assert sha(ROOT / relative) == digest, relative
    geometry = read(ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json")
    hit = read(ROOT / "n41_sixpair_shared_target_20261017/join_audit_result.json")
    assert hit["raw_target"] == protocol["public_raw_point"]
    target = F.inv(hit["raw_target"][0])
    start = time.monotonic_ns()
    machine, wires = circuit.build(target)
    built = time.monotonic_ns()
    points = [tuple(row["raw_sum"]) for row in hit["pair_rows"]]
    left = add(add(points[0], points[1]), points[2])
    right34 = add(points[3], points[4])
    right345 = add(right34, points[5])
    total = add(left, right345)
    assert total == tuple(hit["raw_target"])
    initial = {}
    for slot, row in enumerate(hit["pair_rows"]):
        code = sum(((row["masks"][0] >> bit) & 1) << j
                   for j, bit in enumerate(wires["source_bits"]))
        bind(initial, wires["codes"][slot], code)
        if slot >= 3:
            c = F.inv(row["raw_sum"][0])
            unrotated = circuit.direct.old.frob(c,
                circuit.N - geometry["rotations"][slot])
            bind(initial, wires["right_outputs"][slot - 3], unrotated)
    bind(initial, wires["left_sum"], F.inv(left[0]))
    bind(initial, wires["right34"], F.inv(right34[0]))
    bind(initial, wires["right345"], F.inv(right345[0]))
    triples = [(points[3], points[4], right34),
               (right34, points[5], right345),
               (left, right345, total)]
    for gate, (a, b, z) in enumerate(triples):
        ra, rb, rz = (F.inv(p[0]) for p in (a, b, z))
        branch = F.mul(F.mul(ra, rb), rz) ^ F.halftrace(F.square(ra ^ rb ^ rz))
        assert branch in (0, 1)
        initial[wires["branches"][gate]] = branch
    completed = circuit.direct.old.old.complete_assignment(machine, initial)
    checked = circuit.direct.old.old.check_assignment(machine, completed)
    assert checked["clauses"] == len(machine.clauses)
    assert checked["native_xor_rows"] == len(machine.xors)
    check_end = time.monotonic_ns()
    formula_path = D / "public.xcnf"
    if formula_path.exists():
        raise FileExistsError(formula_path)
    machine.write(formula_path)
    out = {"status": "PASS_UNPINNED_THREE_NORM_HYBRID_BUILD",
           "candidate_id": None, "protocol_sha256": sha(D / "protocol.json"),
           "public_raw_point": hit["raw_target"],
           "source_codes": [row["masks"][0] for row in hit["pair_rows"]],
           "variables": machine.next_var - 1, "and_gates": machine.and_count,
           "norm_checkpoint_and_gates": wires["norm_checkpoint"],
           "ordinary_clauses": len(machine.clauses),
           "native_xor_rows": len(machine.xors),
           "formula_sha256": sha(formula_path),
           "formula_bytes": formula_path.stat().st_size,
           "build_ns": built - start,
           "assignment_check_ns": check_end - built,
           "checked_variables": len(completed),
           "sampled_peak_self_rss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (D / "build_result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
    print(json.dumps({key: out[key] for key in (
        "status", "variables", "and_gates", "ordinary_clauses", "native_xor_rows",
        "formula_sha256")}, sort_keys=True))


if __name__ == "__main__":
    main()
