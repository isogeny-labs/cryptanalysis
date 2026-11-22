"""Rebuild the compact orbit formula and inspect every selector clause."""
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
    result = json.loads((D / "build_result.json").read_text())
    assert sha(D / "circuit.py") == p["circuit_sha256"]
    assert sha(D / "build.py") == p["builder_sha256"]
    machine, wires = circuit.build(result["target_reciprocal"])
    codes = {wire for slot in wires["codes"] for wire in slot}
    selectors = wires["target_selector"]
    assert len(codes) == 42 and len(selectors) == 41
    assert len(set(selectors)) == 41 and codes.isdisjoint(selectors)
    units = [clause for clause in machine.clauses
             if len(clause.split()) == 2 and clause.endswith(" 0")]
    assert not any(abs(int(clause.split()[0])) in codes for clause in units)
    assert not any(abs(int(clause.split()[0])) in selectors for clause in units)
    all_selector_clause = " ".join(map(str, selectors)) + " 0"
    assert machine.clauses.count(all_selector_clause) == 1
    for i in range(41):
        for j in range(i + 1, 41):
            assert f"-{selectors[i]} -{selectors[j]} 0" in machine.clauses
    assert wires["target_orbit"] == result["target_orbit"]
    assert len(set(wires["target_orbit"])) == 41
    assert machine.and_count == result["and_gates"]
    assert len(machine.clauses) == result["ordinary_clauses"]
    assert len(machine.xors) == result["native_xor_rows"]
    with tempfile.TemporaryDirectory(prefix="orbit-formula-audit-", dir=D) as temp:
        rebuilt = Path(temp) / "public.xcnf"
        machine.write(rebuilt)
        assert sha(rebuilt) == sha(D / "public.xcnf") == result["formula_sha256"]
    audit = {"status": "PASS_DIRECT_LEAF_ORBIT_FORMULA_READBACK",
             "protocol_sha256": sha(D / "protocol.json"),
             "build_result_sha256": sha(D / "build_result.json"),
             "audit_source_sha256": sha(D / "audit_formula.py"),
             "formula_sha256": result["formula_sha256"],
             "source_code_variables": len(codes),
             "target_selector_variables": len(selectors),
             "selector_pair_exclusions": 41 * 40 // 2,
             "source_or_selector_unit_clauses": 0}
    (D / "formula_audit_result.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()
