"""Rebuild the dual-tree formula and inspect source-code pinning."""
import hashlib
import json
import tempfile
from pathlib import Path

import circuit

D = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = json.loads((D / "protocol.json").read_text())
    build = json.loads((D / "build_result.json").read_text())
    assert sha(D / "circuit.py") == p["circuit_sha256"]
    assert sha(D / "build.py") == p["builder_sha256"]
    machine, wires = circuit.build(build["target_reciprocal"])
    code_variables = {wire for slot in wires["codes"] for wire in slot}
    assert len(code_variables) == 42
    unit_clauses = [clause for clause in machine.clauses
                    if len(clause.split()) == 2 and clause.endswith(" 0")]
    source_units = [clause for clause in unit_clauses
                    if abs(int(clause.split()[0])) in code_variables]
    assert not source_units
    assert len(machine.clauses) == build["ordinary_clauses"]
    assert len(machine.xors) == build["native_xor_rows"]
    assert machine.and_count == build["and_gates"]
    with tempfile.TemporaryDirectory(prefix="dual-tree-audit-", dir=D) as temp:
        reconstructed = Path(temp) / "formula.xcnf"
        machine.write(reconstructed)
        assert sha(reconstructed) == build["formula_sha256"] == sha(D / "public.xcnf")
    output = {"status": "PASS_DUAL_TREE_FORMULA_READBACK",
              "protocol_sha256": sha(D / "protocol.json"),
              "build_result_sha256": sha(D / "build_result.json"),
              "source_code_variables": len(code_variables),
              "source_code_unit_clauses": len(source_units),
              "formula_sha256": build["formula_sha256"],
              "and_gates": machine.and_count}
    (D / "formula_audit_result.json").write_text(json.dumps(output, sort_keys=True, indent=2) + "\n")
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
