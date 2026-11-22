"""Build the compact functional-root formula for the ordinary point."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LIB = ROOT / "n41_w8_functional_root_table_v2_20261013"
sys.path.insert(0, str(LIB))
import circuit
import experiment


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    frozen = json.loads((HERE / "build_protocol.json").read_text())
    for path, digest in frozen["sources"].items():
        assert sha(path) == digest, path
    experiment.checked()
    g = circuit.geometry()
    audit = json.loads((HERE / "audit_result.json").read_text())
    assert audit["status"] == "PASS_INDEPENDENT_SAGE_ORDINARY_N41_SEVEN_PAIR_RELATION"
    target_point = audit["raw_target"]
    assert target_point == frozen["raw_target"]
    target = circuit.F.inv(target_point[0])
    positive = {"raw_target": target_point,
                "states": [g["blocks"][slot]["states"][row["state_id"]]
                           for slot, row in enumerate(audit["states"])]}
    g["positive_control"] = positive
    c, wires, _ = circuit.build(target)
    initial = experiment.fixture_assignment(wires, g, target)
    values = circuit.old.complete_assignment(c, initial)
    check = circuit.old.check_assignment(c, values)
    assert check == {"clauses": len(c.clauses), "native_xor_rows": len(c.xors)}
    formula = HERE / "ordinary.xcnf"
    c.write(formula)
    result = {"status": "PASS_ORDINARY_POINT_CONSTRUCTED_ASSIGNMENT",
              "candidate_id": None, "formula_sha256": sha(formula),
              "formula_bytes": formula.stat().st_size,
              "variables": c.next_var-1, "clauses": len(c.clauses),
              "xor_rows": len(c.xors), "and_gates": c.and_count,
              "assignment_check": check,
              "initial_variables": len(initial),
              "build_protocol_sha256": sha(HERE / "build_protocol.json")}
    (HERE / "build_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(result["status"], result["variables"], result["clauses"], flush=True)


if __name__ == "__main__":
    main()
