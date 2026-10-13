"""Count exact native-XOR arithmetic cores for adjacent S3 links and S4."""

import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "experiments/koblitz-polynomial-w-pair-20260925"))
from karatsuba_circuit import KaratsubaCircuit


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add_many(circuit, values):
    result = circuit.constant(0)
    for value in values:
        result = circuit.add(result, value)
    return result


def s3(circuit, left, right, output):
    p = circuit.mul(left, right)
    triple = circuit.mul(p, output)
    total = add_many(circuit, (left, right, output))
    equation = add_many(circuit, (circuit.square(total), triple, circuit.square(triple)))
    circuit.require_zero(equation)


def s4(circuit, a, b, c, t):
    ab, ct = circuit.mul(a, b), circuit.mul(c, t)
    e1 = add_many(circuit, (a, b, c, t))
    e3 = circuit.add(circuit.mul(ab, circuit.add(c, t)),
                     circuit.mul(ct, circuit.add(a, b)))
    e4 = circuit.mul(ab, ct)
    x, y = circuit.square(e1), circuit.square(e3)
    xz = circuit.mul(x, e4)
    ztail = circuit.mul(e4, add_many(circuit, (x, y, xz)))
    equation = add_many(circuit, (circuit.square(y), circuit.square(x), y, ztail))
    circuit.require_zero(equation)


def build(n, low_terms, target, variant):
    start = time.monotonic()
    circuit = KaratsubaCircuit(n, low_terms)
    a, b, c = ([circuit.variable() for _ in range(n)] for _ in range(3))
    t = circuit.constant(target)
    if variant == "two_s3_links":
        z = [circuit.variable() for _ in range(n)]
        s3(circuit, a, b, z)
        s3(circuit, z, c, t)
    else:
        s4(circuit, a, b, c, t)
    return {"variant": variant, "n": n, "input_variables": 3*n,
            "intermediate_variables": n if variant == "two_s3_links" else 0,
            "total_variables": circuit.next_var-1, "and_gates": circuit.and_count,
            "xor_rows": len(circuit.xors), "clauses": len(circuit.clauses),
            "build_seconds": time.monotonic()-start}


def main():
    audit = json.loads((HERE / "audit_result.json").read_text())
    assert audit["status"] == "PASS_SYMBOLIC_RESULTANT_AND_GROUP_CONTROLS"
    rows = []
    for label, n, low_terms in (("n41", 41, (0, 3)),
                                ("n131", 131, (0, 1, 2, 13))):
        for variant in ("two_s3_links", "direct_s4"):
            row = build(n, low_terms, audit[label]["target_reciprocal"], variant)
            row["field"] = label
            rows.append(row)
    result = {"status": "ARITHMETIC_CORE_COUNTS_ONLY",
              "source_sha256": sha(HERE / "circuit_compare.py"),
              "audit_sha256": sha(HERE / "audit_result.json"),
              "karatsuba_sha256": sha(ROOT / "experiments/koblitz-polynomial-w-pair-20260925/karatsuba_circuit.py"),
              "rows": rows}
    (HERE / "circuit_counts.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(rows, sort_keys=True))


if __name__ == "__main__":
    main()
