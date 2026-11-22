"""Evaluate every N131 binary selector assignment against the Sage orbit table."""

import hashlib
import json
from pathlib import Path

import binary

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n131_w18_ninepair_orbit_20261012"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = binary.orbit9.protocol()
    sage = json.loads((PARENT / "sage_audit_result.json").read_text())
    assert sage["status"] == "PASS_SAGE_ALL_524_N131_ORBIT_FIBER_CHOICES"
    target = binary.base.target_record()
    rows = binary.orbit9.orbit_rows([row["point"] for row in target["preimages"]])
    checked = [[row["raw_preimage_index"], row["target_rotation"],
                *row["point"], row["standard_reciprocal"]] for row in rows]
    digest = hashlib.sha256(json.dumps(checked, separators=(",", ":")).encode()).hexdigest()
    assert digest == sage["challenge"]["row_digest_sha256"]
    circuit = binary.base.KaratsubaCircuit(binary.pair.N, [0, 1, 2, 13])
    target_bits, fiber_bits, rotation_bits = binary.binary_target(
        circuit, [row["standard_reciprocal"] for row in rows])
    def value(values, wire):
        return 1 if wire == -1 else 0 if wire == 0 else values[wire]
    tested = 0
    for fiber in range(4):
        for rotation in range(131):
            initial = {wire: fiber >> bit & 1 for bit, wire in enumerate(fiber_bits)}
            initial.update({wire: rotation >> bit & 1
                            for bit, wire in enumerate(rotation_bits)})
            values = binary.base.complete_assignment(circuit, initial)
            binary.base.check_assignment(circuit, values)
            actual = sum(value(values, wire) << bit
                         for bit, wire in enumerate(target_bits))
            assert actual == rows[fiber * 131 + rotation]["standard_reciprocal"]
            tested += 1
    rejected = 0
    for rotation in range(131, 256):
        initial = {wire: 0 for wire in fiber_bits}
        initial.update({wire: rotation >> bit & 1
                        for bit, wire in enumerate(rotation_bits)})
        values = binary.base.complete_assignment(circuit, initial)
        failed = [line for line in circuit.clauses
                  if not any(values[abs(item)] == int(item > 0)
                             for item in map(int, line.split()[:-1]))]
        assert failed
        rejected += 1
    assert tested == 524 and rejected == 125
    result = {"status": "PASS_N131_BINARY_SELECTOR_ALL_CHOICES",
              "curve_id": protocol["curve_id"],
              "workload_id": protocol["workload_id"],
              "valid_choices_checked": tested,
              "invalid_rotation_codes_rejected": rejected,
              "sage_row_digest_sha256": digest,
              "selector_variables": circuit.next_var - 1,
              "selector_and_gates": circuit.and_count,
              "selector_clauses": len(circuit.clauses),
              "selector_xor_rows": len(circuit.xors),
              "sha256": {"auditor": sha(Path(__file__)),
                         "protocol": sha(HERE / "protocol.json"),
                         "selector": sha(HERE / "binary_selector.py"),
                         "sage_orbit": sha(PARENT / "sage_audit_result.json")}}
    with (HERE / "selector_524_result.json").open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(result["status"], tested, rejected)


if __name__ == "__main__":
    main()
