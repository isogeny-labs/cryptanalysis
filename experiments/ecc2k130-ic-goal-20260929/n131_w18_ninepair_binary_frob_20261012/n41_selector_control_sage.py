#!/usr/bin/env sage -python
"""Check all N41 binary target choices against an unpinned public relation."""

import hashlib
import json
import sys
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EXPERIMENTS = ROOT.parent
sys.path.insert(0, str(EXPERIMENTS / "koblitz-s5-invariant-20260924"))
from circuit_sat import Circuit  # noqa: E402
from binary_selector import build  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate(circuit, initial):
    definitions = {int(out): ("and", int(a), int(b))
                   for (a, b), out in circuit.and_cache.items()}
    for line in circuit.xors:
        literals = [int(value) for value in line.split()[1:-1]]
        definitions[abs(literals[0])] = ("xor", literals)
    values = [None] * circuit.next_var
    for wire, bit in initial.items():
        values[wire] = bit
    def value(item):
        return 1 if item == -1 else 0 if item == 0 else values[item]
    for wire in range(1, circuit.next_var):
        if values[wire] is not None:
            continue
        definition = definitions[wire]
        if definition[0] == "and":
            values[wire] = value(definition[1]) & value(definition[2])
        else:
            literals = definition[1]
            bit = int(literals[0] > 0)
            for item in literals[1:]:
                bit ^= value(abs(item)) ^ int(item < 0)
            values[wire] = bit
    return values


def clauses_hold(circuit, values):
    for line in circuit.clauses:
        literals = [int(value) for value in line.split()[:-1]]
        if not any(values[abs(item)] == int(item > 0) for item in literals):
            return False
    for line in circuit.xors:
        literals = [int(value) for value in line.split()[1:-1]]
        if not sum(values[abs(item)] ^ int(item < 0) for item in literals) & 1:
            return False
    return True


def main():
    frozen = json.loads((HERE / "n41_control_protocol.json").read_text())
    paths = {"script": Path(__file__), "selector": HERE / "binary_selector.py",
             "circuit": EXPERIMENTS / "koblitz-s5-invariant-20260924/circuit_sat.py",
             "input": ROOT / "n41_w8_sixpair_mitm_20261011/protocol.json",
             "positive_relation": ROOT / "n41_w8_ninepair_join_control_20261012/audit_result.json",
             "runtime": HERE / "sage_runtime_info.json"}
    assert frozen["status"] == "FROZEN_N41_BINARY_SELECTOR_CONTROL"
    assert frozen["source_sha256"] == {name: sha(path) for name, path in paths.items()}
    assert json.loads(paths["runtime"].read_text())["status"] == "verified"
    input_record = json.loads(paths["input"].read_text())
    relation = json.loads(paths["positive_relation"].read_text())
    assert relation["status"] == "PASS_INDEPENDENT_N41_PUBLIC_NINE_PAIR_RELATION"
    assert relation["source_edges_distinct"] == 9
    assert relation["folded_columns_nonzero"] == 18
    assert relation["raw_target_preimage_index"] == 0
    assert relation["raw_target_replayed"] == input_record["raw_target_preimages"][0]
    polynomial = PolynomialRing(GF(2), "t")
    t = polynomial.gen()
    field = GF(2**41, name="t", modulus=t**41+t**3+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    def dec(number):
        return field(polynomial([(number >> bit) & 1 for bit in range(41)]))
    def enc(value):
        return sum(int(bit) << index for index, bit in enumerate(value.polynomial().list()))
    def square(number):
        return enc(dec(number)**2)
    def frobenius(number, exponent):
        return enc(dec(number)**(1 << exponent))
    q = curve(*map(dec, input_record["public_target_transported"]))
    reciprocals = []
    for coordinates in input_record["raw_target_preimages"]:
        point = curve(*map(dec, coordinates))
        assert 4 * point == q
        first = point
        for rotation in range(41):
            assert point[0] != 0
            reciprocals.append(enc(1 / point[0]))
            point = curve(point[0]**2, point[1]**2)
        assert point == first
    assert len(reciprocals) == 164
    circuit = Circuit(41, [0, 3])
    target_bits, fiber_bits, rotation_bits = build(circuit, reciprocals, 41,
                                                   square, frobenius)
    assert len(fiber_bits) == 2 and len(rotation_bits) == 6
    def decode(values, bits):
        return sum((1 if bit == -1 else 0 if bit == 0 else values[bit]) << index
                   for index, bit in enumerate(bits))
    valid, invalid = 0, 0
    for fiber in range(4):
        for rotation in range(1 << len(rotation_bits)):
            initial = {wire: fiber >> bit & 1 for bit, wire in enumerate(fiber_bits)}
            initial.update({wire: rotation >> bit & 1
                            for bit, wire in enumerate(rotation_bits)})
            values = evaluate(circuit, initial)
            if rotation < 41:
                assert clauses_hold(circuit, values)
                assert decode(values, target_bits) == reciprocals[fiber * 41 + rotation]
                valid += 1
            else:
                assert not clauses_hold(circuit, values)
                invalid += 1
    assert valid == 164 and invalid == 92
    assert reciprocals[0] == enc(1 / curve(*map(dec, relation["raw_target_replayed"]))[0])
    result = {"status": "PASS_N41_BINARY_FROBENIUS_SELECTOR_CONTROL",
              "curve_id": relation["curve_id"],
              "public_target_transported": input_record["public_target_transported"],
              "positive_nine_pair_relation_rank": relation["row_rank_from_empty_matrix"],
              "positive_folded_columns": relation["folded_columns_nonzero"],
              "valid_choices_checked": valid, "invalid_rotation_codes_rejected": invalid,
              "selector_variables": circuit.next_var - 1,
              "selector_and_gates": circuit.and_count,
              "selector_clauses": len(circuit.clauses),
              "selector_xor_rows": len(circuit.xors),
              "source_sha256": {name: sha(path) for name, path in paths.items()}}
    with (HERE / "n41_control_result.json").open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(result["status"], valid, invalid)


if __name__ == "__main__":
    main()
