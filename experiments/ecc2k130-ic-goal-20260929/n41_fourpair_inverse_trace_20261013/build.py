"""Build the exact N41 four-pair chart with inverse-trace source gates."""
import hashlib
import importlib.util
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
PARENT = GOAL / "n131_w18_allseed_fourpair_20261012/fourpair_v2.py"
FIXTURE = GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal/control_fixture.json"
SUPPORT = GOAL / "n41_w7_entropy_cubic_20261011/w8/geometry.json"
spec = importlib.util.spec_from_file_location("fourpair_parent", PARENT)
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def trace(field, x):
    total = 0
    for _ in range(field.n):
        total ^= x
        x = field.square(x)
    assert total in (0, 1)
    return total


def check(circuit, wires, inverse_wires, fixture, field, rotations):
    values = {}
    def put(bits, number):
        for i, bit in enumerate(bits):
            values[bit] = (int(number) >> i) & 1
    masks = [x for pair in fixture["masks"] for x in pair]
    for mask, bits, inv_bits in zip(masks, wires["masks"], inverse_wires):
        put(bits, mask)
        put(inv_bits, field.inverse(mask << 1))
    for number, bits, rotation in zip(fixture["pair_reciprocals"], wires["pair_outputs"], rotations):
        put(bits, field.frob(number, (field.n - rotation) % field.n))
    for number, bits in zip(fixture["intermediate_reciprocals"], wires["middle"]):
        put(bits, number)
    gates = [(out, "and", key) for key, out in circuit.and_cache.items()]
    gates += [(out, "xor", key) for key, out in circuit.xor_cache.items()]
    def value(bit):
        return 1 if bit == -1 else 0 if bit == 0 else values[bit]
    for out, kind, key in sorted(gates):
        assert out not in values
        values[out] = value(key[0]) & value(key[1]) if kind == "and" else key[1] ^ (sum(value(v) for v in key[0]) & 1)
    assert len(values) == circuit.next_var - 1
    for line in circuit.clauses:
        lits = [int(x) for x in line.split()[:-1]]
        assert any(value(abs(v)) if v > 0 else 1 - value(abs(v)) for v in lits), line
    for line in circuit.xors:
        lits = [int(x) for x in line.split()[1:-1]]
        assert (sum(value(abs(v)) if v > 0 else 1 - value(abs(v)) for v in lits) & 1) == 1, line
    return {"status": "PASS_COMPLETE_ASSIGNMENT", "variables": len(values),
            "clauses": len(circuit.clauses), "xor_rows": len(circuit.xors)}


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    paths = {"builder": HERE / "build.py", "parent": PARENT, "fixture": FIXTURE, "support": SUPPORT}
    assert {key: sha(path) for key, path in paths.items()} == {
        key: protocol["sha256"][key] for key in paths}
    assert protocol["curve_id"] == "EC1N41Ckb1h7d5e80d3c4d0"
    field, width, rotations = parent.field_config("n41")
    support = parent.support("n41")
    accepted = {mask for mask in range(1, 1 << width) if trace(field, field.inverse(mask << 1)) == 0}
    assert accepted == set(support) and len(accepted) == 125
    trace_basis = [trace(field, 1 << i) for i in range(field.n)]
    inverse_wires = []
    original_emit = parent.emit_bdd
    def emit_gate(circuit, bits, _root, _nodes):
        algebra = parent.Algebra(circuit, field, dense_and_threshold=3000)
        endpoint = algebra.expression((wire, 1 << (i + 1)) for i, wire in enumerate(bits))
        inv_bits = [circuit.variable() for _ in range(field.n)]
        inverse_wires.append(inv_bits)
        inverse = algebra.from_bits(inv_bits)
        circuit.require_zero(algebra.add(algebra.mul(endpoint, inverse), algebra.one).bits())
        circuit.require_zero([circuit.xor(wire for wire, bit in zip(inv_bits, trace_basis) if bit)])
    parent.emit_bdd = emit_gate
    try:
        start = time.monotonic_ns()
        fixture = json.loads(FIXTURE.read_text())
        circuit, wires, metadata = parent.build("n41", fixture["target_reciprocal"])
        built = time.monotonic_ns()
        assert len(inverse_wires) == 8
        control = check(circuit, wires, inverse_wires, fixture, field, rotations)
        checked = time.monotonic_ns()
        path = HERE / "public.xcnf"
        assert not path.exists()
        circuit.write(path)
        end = time.monotonic_ns()
    finally:
        parent.emit_bdd = original_emit
    result = {"status": "PASS_EXACT_INVERSE_TRACE_CONTROL_AND_PUBLIC_FORMULA",
              "candidate_id": None, "curve_id": protocol["curve_id"],
              "support_equivalence": {"tested_nonzero_masks": 255, "accepted_masks": len(accepted)},
              "control": control, "formula_sha256": sha(path), "formula_bytes": path.stat().st_size,
              "variables": circuit.next_var - 1, "and_gates": circuit.and_count,
              "clauses": len(circuit.clauses), "xor_rows": len(circuit.xors),
              "metadata": metadata, "build_ns": built - start,
              "control_check_ns": checked - built, "write_ns": end - checked,
              "protocol_sha256": sha(HERE / "protocol.json")}
    (HERE / "build_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("status", "variables", "clauses", "xor_rows", "formula_bytes")}))


if __name__ == "__main__":
    main()
