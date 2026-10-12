"""Exact output-inverse linearization of the N131 W20 seven-pair circuit."""

import argparse
import hashlib
import importlib.util
import json
import resource
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / "n131_w20_inverse_trace_20261012"
W20 = ROOT / "n131_w20_sevenpair_gate_20261010"
spec = importlib.util.spec_from_file_location("w20_inverse_prior", PRIOR / "run.py")
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
old, seven = prior.old, prior.seven


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open("x") as out:
        json.dump(value, out, sort_keys=True, indent=2)
        out.write("\n")


def sources():
    return {"runner": Path(__file__), "target_maker": HERE / "make_target.py",
            "public_target": HERE / "public_target.json",
            "private_fixture": HERE / "private_fixture.json",
            "sage_runtime": HERE / "sage_runtime_info.json",
            "prior_runner": PRIOR / "run.py",
            "source_table": W20 / "support_w20.tsv",
            "prior_group_audit": W20 / "sage_audit_result.json"}


def freeze():
    target = json.loads((HERE / "public_target.json").read_text())
    secret = json.loads((HERE / "private_fixture.json").read_text())
    assert target["status"] == "FROZEN_FRESH_N131_ONE_POINT_TARGET"
    assert target["workload_id"] == secret["workload_id"]
    assert target["public_target"] == secret["public_target"]
    assert sha(HERE / "public_target.json") == secret["public_sha256"]
    assert target["source_sha256"] == {"script": sha(HERE / "make_target.py"),
                                       "sage_runtime": sha(HERE / "sage_runtime_info.json")}
    baseline = json.loads((PRIOR / "protocol.json").read_text())
    assert baseline["accepted_source_codes"] == 132045
    save("protocol.json", {
        "status": "FROZEN_BEFORE_W20_OUTPUT_LINEAR_CONTROL_AND_QUERY",
        "candidate_id": None, "curve_id": target["workload"]["curve_id"],
        "workload_id": target["workload_id"],
        "public_target": target["public_target"],
        "raw_preimage_index": 0,
        "pair_slots": 7, "fixed_seed_mask": baseline["fixed_seed_mask"],
        "source_codes_per_slot": 132045,
        "source_rotations": seven.ROTATIONS,
        "pair_equation": "ab=1; P(s)=(1+h2)a+h2b",
        "source_gate": baseline["source_gate"],
        "solver_flags": ["--threads=1", "--maxtime=600", "--zero-exit-status",
                         "--verb=1", "--printsol=1"],
        "parent_wall_cap_seconds": 615,
        "rss_cap_bytes": 4 * 1024**3,
        "source_sha256": {name: sha(path) for name, path in sources().items()},
    })
    print("FROZEN_W20_OUTPUT_LINEAR", target["workload_id"], flush=True)


def protocol():
    record = json.loads((HERE / "protocol.json").read_text())
    assert record["status"] == "FROZEN_BEFORE_W20_OUTPUT_LINEAR_CONTROL_AND_QUERY"
    assert record["source_sha256"] == {name: sha(path) for name, path in sources().items()}
    return record


def build(target_a):
    seed, bits = seven.seed_and_bits()
    pair = old.pair
    circuit = old.KaratsubaCircuit(seven.N, [0, 1, 2, 13])
    algebra = old.Algebra(circuit, old.Field(), dense_and_threshold=3000)
    seed_x = seven.coordinate(seed)
    h2 = pair.gf_square(pair.gf_half_trace(seed_x))
    coefficient = 1 ^ h2
    trace_basis = [old.trace(1 << bit) for bit in range(seven.N)]
    selectors, outputs, output_inverse, rotated, witnesses = [], [], [], [], []
    for rotation in seven.ROTATIONS:
        source_bits = [circuit.variable() for _ in bits]
        out = [circuit.variable() for _ in range(seven.N)]
        inverse_out = [circuit.variable() for _ in range(seven.N)]
        selectors.append(source_bits)
        outputs.append(out)
        output_inverse.append(inverse_out)
        product = algebra.expression(zip(source_bits, seven.product_basis(seed, bits)))
        a = algebra.from_bits(out)
        b = algebra.from_bits(inverse_out)
        coeff_a = algebra.expression(
            (wire, pair.gf_mul(coefficient, 1 << bit))
            for bit, wire in enumerate(out))
        h2_b = algebra.expression(
            (wire, pair.gf_mul(h2, 1 << bit))
            for bit, wire in enumerate(inverse_out))
        circuit.require_zero(algebra.add(product, coeff_a, h2_b).bits())
        circuit.require_zero(algebra.add(algebra.mul(a, b), algebra.one).bits())
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
        output = (algebra.from_bits(intermediates[index - 1]) if index < 6
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
                     "output_inverse": output_inverse,
                     "intermediates": intermediates, "branches": branches,
                     "inverse_witnesses": witnesses}


def profile(circuit, path, build_ns, write_ns):
    return {"variables": circuit.next_var - 1,
            "and_gates": circuit.and_count,
            "clauses": len(circuit.clauses),
            "native_xor_rows": len(circuit.xors),
            "xcnf_bytes": path.stat().st_size,
            "xcnf_sha256": sha(path),
            "construction_ns": build_ns, "serialization_ns": write_ns,
            "peak_process_rss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}


def control():
    frozen = protocol()
    fixture = json.loads((W20 / "sage_audit_result.json").read_text())
    target_a = old.standard_reciprocal(fixture["constructed_raw_target_z"])
    start = time.monotonic_ns()
    circuit, wires = build(target_a)
    built = time.monotonic_ns()
    formula = HERE / "control.xcnf"
    circuit.write(formula)
    written = time.monotonic_ns()
    initial = {}
    def bind(vector, value):
        initial.update({wire: (value >> bit) & 1 for bit, wire in enumerate(vector)})
    seed, bits = seven.seed_and_bits()
    pair = old.pair
    h2 = pair.gf_square(pair.gf_half_trace(seven.coordinate(seed)))
    for item in fixture["selected"]:
        slot = item["slot"]
        code = seven.selector_code(item["masks"][0], bits)
        a = old.standard_reciprocal(item["unrotated_pair_output_z"])
        b = old.inverse(a)
        product = 0
        for bit, basis in enumerate(seven.product_basis(seed, bits)):
            if code >> bit & 1:
                product ^= basis
        assert pair.gf_mul(a, b) == 1
        assert product == pair.gf_mul(1 ^ h2, a) ^ pair.gf_mul(h2, b)
        assert pair.gf_mul(a, product) ^ pair.gf_mul(1 ^ h2, pair.gf_square(a)) ^ h2 == 0
        bind(wires["selectors"][slot], code)
        bind(wires["outputs"][slot], a)
        bind(wires["output_inverse"][slot], b)
        for side, mask in enumerate(item["masks"]):
            x = seven.coordinate(mask)
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
    save("control_result.json", {
        "status": "PASS_W20_OUTPUT_LINEAR_CONSTRUCTED_CONTROL",
        "candidate_id": None, "assignment_check": checked,
        "primary_variables": len(initial),
        "formula": profile(circuit, formula, built-start, written-built),
        "protocol_sha256": sha(HERE / "protocol.json"),
        "source_sha256": frozen["source_sha256"]})
    print("PASS_W20_OUTPUT_LINEAR_CONSTRUCTED_CONTROL", flush=True)


def ordinary():
    frozen = protocol()
    assert json.loads((HERE / "control_result.json").read_text())["status"] == "PASS_W20_OUTPUT_LINEAR_CONSTRUCTED_CONTROL"
    target = json.loads((HERE / "public_target.json").read_text())
    target_a = target["raw_standard_reciprocal_x"]
    start = time.monotonic_ns()
    circuit, _ = build(target_a)
    built = time.monotonic_ns()
    formula = HERE / "ordinary.xcnf"
    circuit.write(formula)
    written = time.monotonic_ns()
    save("ordinary_build_result.json", {
        "status": "PASS_W20_OUTPUT_LINEAR_ORDINARY_BUILD",
        "candidate_id": None, "workload_id": frozen["workload_id"],
        "public_target": frozen["public_target"],
        "raw_preimage_index": 0,
        "formula": profile(circuit, formula, built-start, written-built),
        "protocol_sha256": sha(HERE / "protocol.json")})
    print("PASS_W20_OUTPUT_LINEAR_ORDINARY_BUILD", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "control", "ordinary"))
    {"freeze": freeze, "control": control,
     "ordinary": ordinary}[parser.parse_args().mode]()
