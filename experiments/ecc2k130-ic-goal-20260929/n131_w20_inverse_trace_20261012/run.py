"""Exact inverse-trace source gate for the existing N131 W20 seven-pair query."""

import argparse
import hashlib
import json
import resource
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
W20 = ROOT / "n131_w20_sevenpair_gate_20261010"
W18 = ROOT / "n131_fixed_seed_ninepair_cubic_20261011"
BASE = ROOT / "n131_fixed_seed_eight_pair_circuit_20261010"
sys.path[:0] = [str(W20), str(W18)]
import sevenpair_circuit as seven  # noqa: E402
import run as old  # noqa: E402


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open("x") as out:
        json.dump(value, out, indent=2, sort_keys=True)
        out.write("\n")


def sources():
    return {"runner": Path(__file__), "support": W20 / "support_w20.tsv",
            "count": W20 / "count_result_v2.json",
            "group_audit": W20 / "sage_audit_result.json",
            "sevenpair": W20 / "sevenpair_circuit.py",
            "field": BASE / "fixed_pair_circuit.py",
            "karatsuba": ROOT.parent / "koblitz-polynomial-w-pair-20260925" / "karatsuba_circuit.py",
            "sparse": ROOT / "n41_basis_aware_quartic_20261011" / "sparse.py",
            "prior_runner": W18 / "run.py",
            "ordinary_target": BASE / "target_preimages.json"}


def coordinate(mask):
    return seven.coordinate(mask)


def freeze():
    seed, bits = seven.seed_and_bits()
    assert len(bits) == 19
    # Tr(x)=0 over the whole W20 span; this is the fixed-field premise that
    # turns rationality of y^2+xy=x^3+1 into Tr(1/x)=0 for x != 0.
    basis_traces = [old.trace(1 << (i + 1)) for i in range(seven.WIDTH)]
    assert basis_traces == [0] * seven.WIDTH
    columns = {int(mask): int(column) for mask, column, shift in
               (line.split() for line in (W20 / "support_w20.tsv").read_text().splitlines())}
    valid = set()
    for mask, column in columns.items():
        other = mask ^ seed
        if mask < other and other in columns and column != columns[other]:
            valid.add(seven.selector_code(mask, bits))
    count = json.loads((W20 / "count_result_v2.json").read_text())
    assert len(valid) == count["selected_valid_unordered_pairs_per_slot"] == 132045
    selected = json.loads((W20 / "sage_audit_result.json").read_text())["selected"]
    for item in selected:
        for mask in item["masks"]:
            x = coordinate(mask)
            assert x and old.trace(old.inverse(x)) == 0
    target = json.loads((BASE / "target_preimages.json").read_text())
    save("protocol.json", {"status": "FROZEN_BEFORE_W20_INVERSE_TRACE_BUILD",
                           "candidate_id": None, "curve_id": target["curve_id"],
                           "workload_id": target["workload_id"],
                           "raw_preimage_index": 0, "fixed_seed_mask": seed,
                           "selector_bits": bits, "basis_traces": basis_traces,
                           "accepted_source_codes": len(valid),
                           "pair_slots": 7, "source_rotations": seven.ROTATIONS,
                           "solver_wall_cap_seconds": 600,
                           "parent_wall_cap_seconds": 615,
                           "rss_cap_bytes": 4 * 1024**3,
                           "source_gate": "two_nonzero_inverse_witnesses_with_zero_trace",
                           "source_sha256": {name: sha(path) for name, path in sources().items()}})
    print("FROZEN_W20_INVERSE_TRACE", len(valid), flush=True)


def protocol():
    data = json.loads((HERE / "protocol.json").read_text())
    assert data["source_sha256"] == {name: sha(path) for name, path in sources().items()}
    assert data["status"] == "FROZEN_BEFORE_W20_INVERSE_TRACE_BUILD"
    return data


def build(target_a):
    seed, bits = seven.seed_and_bits()
    pair = old.pair
    circuit = old.KaratsubaCircuit(seven.N, [0, 1, 2, 13])
    algebra = old.Algebra(circuit, old.Field(), dense_and_threshold=3000)
    seed_x = coordinate(seed)
    h2 = pair.gf_square(pair.gf_half_trace(seed_x))
    coefficient = 1 ^ h2
    trace_basis = [old.trace(1 << bit) for bit in range(seven.N)]
    selectors, outputs, rotated, witnesses = [], [], [], []
    for rotation in seven.ROTATIONS:
        source_bits = [circuit.variable() for _ in bits]
        out = [circuit.variable() for _ in range(seven.N)]
        selectors.append(source_bits)
        outputs.append(out)
        product = algebra.expression(zip(source_bits, seven.product_basis(seed, bits)))
        square_term = algebra.expression(
            (wire, pair.gf_mul(coefficient, pair.gf_square(1 << bit)))
            for bit, wire in enumerate(out))
        circuit.require_zero(algebra.add(
            algebra.mul(algebra.from_bits(out), product), square_term,
            algebra.expression(((-1, h2),))).bits())
        circuit.clauses.append(" ".join(map(str, out)) + " 0")
        source = algebra.expression(
            (wire, 1 << (source_bit + 1))
            for wire, source_bit in zip(source_bits, bits))
        other = algebra.add(source, algebra.expression(((-1, seed_x),)))
        slot_witnesses = []
        for endpoint in (source, other):
            inverse_bits = [circuit.variable() for _ in range(seven.N)]
            circuit.require_zero(algebra.add(
                algebra.mul(endpoint, algebra.from_bits(inverse_bits)), algebra.one).bits())
            circuit.require_zero([circuit.xor(
                wire for wire, bit in zip(inverse_bits, trace_basis) if bit)])
            slot_witnesses.append(inverse_bits)
        witnesses.append(slot_witnesses)
        images = [pair.gf_frobenius(1 << bit, rotation) for bit in range(seven.N)]
        rotated.append(algebra.from_bits(circuit.linear_element(out, images)))

    intermediates = [[circuit.variable() for _ in range(seven.N)] for _ in range(5)]
    branches = [circuit.variable() for _ in range(6)]
    ht_basis = []
    for bit in range(seven.N):
        value, image = pair.gf_square(1 << bit), 0
        for _ in range((seven.N + 1) // 2):
            image ^= value
            value = pair.gf_square(pair.gf_square(value))
        ht_basis.append(image)
    running = rotated[0]
    for index in range(1, 7):
        output = (algebra.from_bits(intermediates[index -1]) if index < 6
                  else algebra.expression(((-1, target_a),)))
        total = algebra.add(running, rotated[index], output)
        ht = circuit.linear_element(total.bits(), ht_basis)
        circuit.require_zero(algebra.add(
            algebra.mul(algebra.mul(running, rotated[index]), output),
            algebra.from_bits(ht),
            algebra.expression(((branches[index - 1], 1),))).bits())
        circuit.require_zero([circuit.xor(
            wire for wire, bit in zip(total.bits(), trace_basis) if bit)])
        if index < 6:
            circuit.clauses.append(" ".join(map(str, intermediates[index - 1])) + " 0")
        running = output
    return circuit, {"selectors": selectors, "outputs": outputs,
                     "intermediates": intermediates, "branches": branches,
                     "inverse_witnesses": witnesses}


def profile(circuit, path, build_ns, write_ns):
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {"variables": circuit.next_var - 1, "and_gates": circuit.and_count,
            "clauses": len(circuit.clauses), "native_xor_rows": len(circuit.xors),
            "xcnf_bytes": path.stat().st_size, "xcnf_sha256": sha(path),
            "construction_ns": build_ns, "serialization_ns": write_ns,
            "peak_process_rss_raw": rss}


def control():
    frozen = protocol()
    fixture = json.loads((W20 / "sage_audit_result.json").read_text())
    target_a = old.standard_reciprocal(fixture["constructed_raw_target_z"])
    start = time.monotonic_ns()
    circuit, wires = build(target_a)
    built = time.monotonic_ns()
    path = HERE / "control.xcnf"
    circuit.write(path)
    written = time.monotonic_ns()
    initial = {}
    def bind(vector, value):
        initial.update({wire: (value >> bit) & 1 for bit, wire in enumerate(vector)})
    seed, bits = seven.seed_and_bits()
    pair = old.pair
    h2 = pair.gf_square(pair.gf_half_trace(coordinate(seed)))
    for item in fixture["selected"]:
        slot = item["slot"]
        code = seven.selector_code(item["masks"][0], bits)
        a = old.standard_reciprocal(item["unrotated_pair_output_z"])
        product = 0
        for bit, basis in enumerate(seven.product_basis(seed, bits)):
            if code >> bit & 1:
                product ^= basis
        assert pair.gf_mul(1 ^ h2, pair.gf_square(a)) ^ pair.gf_mul(a, product) ^ h2 == 0
        bind(wires["selectors"][slot], code)
        bind(wires["outputs"][slot], a)
        for side, mask in enumerate(item["masks"]):
            x = coordinate(mask)
            inv = old.inverse(x)
            assert pair.gf_mul(x, inv) == 1 and old.trace(inv) == 0
            bind(wires["inverse_witnesses"][slot][side], inv)
    for vector, z in zip(wires["intermediates"], fixture["intermediate_z"]):
        bind(vector, old.standard_reciprocal(z))
    rotated = [pair.gf_frobenius(old.standard_reciprocal(item["unrotated_pair_output_z"]),
                                 item["rotation"]) for item in fixture["selected"]]
    middle = [old.standard_reciprocal(z) for z in fixture["intermediate_z"]]
    left = rotated[0]
    for index in range(1, 7):
        right = middle[index - 1] if index < 6 else target_a
        total = left ^ rotated[index] ^ right
        branch = pair.gf_mul(pair.gf_mul(left, rotated[index]), right) ^ old.halftrace(pair.gf_square(total))
        assert branch in (0, 1)
        initial[wires["branches"][index - 1]] = branch
        left = right
    checked = old.check_assignment(circuit, old.complete_assignment(circuit, initial))
    save("control_result.json", {"status": "PASS_W20_INVERSE_TRACE_CONSTRUCTED_CONTROL",
                                 "candidate_id": None, "assignment_check": checked,
                                 "primary_variables": len(initial),
                                 "formula": profile(circuit, path, built-start, written-built),
                                 "protocol_sha256": sha(HERE / "protocol.json"),
                                 "source_sha256": frozen["source_sha256"]})
    print("PASS_W20_INVERSE_TRACE_CONSTRUCTED_CONTROL", flush=True)


def ordinary():
    protocol()
    assert json.loads((HERE / "control_result.json").read_text())["status"] == "PASS_W20_INVERSE_TRACE_CONSTRUCTED_CONTROL"
    target = json.loads((BASE / "target_preimages.json").read_text())
    target_a = old.standard_reciprocal(target["preimages"][0]["reciprocal_x_z"])
    start = time.monotonic_ns()
    circuit, _ = build(target_a)
    built = time.monotonic_ns()
    path = HERE / "ordinary.xcnf"
    circuit.write(path)
    written = time.monotonic_ns()
    save("ordinary_build_result.json", {"status": "PASS_W20_INVERSE_TRACE_ORDINARY_BUILD",
                                       "candidate_id": None, "workload_id": target["workload_id"],
                                       "raw_preimage_index": 0,
                                       "formula": profile(circuit, path, built-start, written-built),
                                       "protocol_sha256": sha(HERE / "protocol.json")})
    print("PASS_W20_INVERSE_TRACE_ORDINARY_BUILD", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "control", "ordinary"))
    mode = parser.parse_args().mode
    {"freeze": freeze, "control": control, "ordinary": ordinary}[mode]()
