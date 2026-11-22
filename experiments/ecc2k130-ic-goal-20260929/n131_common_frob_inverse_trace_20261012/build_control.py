"""Freeze and fully evaluate the constructed N131 five-pair formula."""

import hashlib
import json
import time
from pathlib import Path

import circuit

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
PARENT = GOAL / "n131_w18_allseed_fourpair_20261012/fourpair_v2.py"
SPARSE = GOAL / "n41_basis_aware_quartic_20261011/sparse.py"
KARATSUBA = HERE.parents[1] / "koblitz-polynomial-w-pair-20260925/karatsuba_circuit.py"
SUPPORT = GOAL / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"
SOURCE_EQUIV = GOAL / "n131_w18_inverse_trace_terminal_20261011/gate_equivalence.json"
WIDTH_AUDIT = GOAL / "n131_w16_w18_sixpair_width_gate_20261010/native_audit_result.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "control_protocol.json").read_text())
    files = {"runner": HERE / "build_control.py", "circuit": HERE / "circuit.py",
             "parent": PARENT, "sparse": SPARSE, "karatsuba": KARATSUBA,
             "support": SUPPORT, "source_equivalence": SOURCE_EQUIV,
             "width_audit": WIDTH_AUDIT, "fixture": HERE / "fixture.json",
             "sage_runtime": HERE / "sage_runtime_info.json"}
    assert protocol["status"] == "FROZEN_BEFORE_N131_INVERSE_TRACE_CONTROL"
    assert protocol["sha256"] == {name: sha(path) for name, path in files.items()}
    equivalent = json.loads(SOURCE_EQUIV.read_text())
    assert equivalent["status"] == "PASS_EXACT_SOURCE_GATE_EQUIVALENCE"
    assert equivalent["source_support_sha256"] == sha(SUPPORT)
    assert next(row for row in json.loads(WIDTH_AUDIT.read_text())["widths"]
                if row["degree"] == 18)["rational_masks"] == 131307
    fixture = json.loads((HERE / "fixture.json").read_text())
    assert fixture["status"] == "PASS_N131_FIVEPAIR_CONSTRUCTED_CHART"
    start = time.monotonic_ns()
    formula, wires, metadata = circuit.build([fixture["raw_target_reciprocal"]])
    built = time.monotonic_ns()
    checked = circuit.check_assignment(formula, wires, fixture)
    checked_at = time.monotonic_ns()
    output = HERE / "control.xcnf"
    assert not output.exists()
    formula.write(output)
    ended = time.monotonic_ns()
    result = {"status": checked["status"], "candidate_id": None,
              "curve_id": fixture["curve_id"], "fixture_sha256": sha(HERE / "fixture.json"),
              "variables": formula.next_var-1, "and_gates": formula.and_count,
              "cnf_clauses": len(formula.clauses), "native_xor_rows": len(formula.xors),
              "xcnf_bytes": output.stat().st_size, "xcnf_sha256": sha(output),
              "assignment_check": checked, "metadata": metadata,
              "construction_ns": built-start, "assignment_check_ns": checked_at-built,
              "serialization_ns": ended-checked_at,
              "protocol_sha256": sha(HERE / "control_protocol.json")}
    with (HERE / "control_result.json").open("x") as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write("\n")
    print(result["status"], result["variables"], result["cnf_clauses"], flush=True)


if __name__ == "__main__":
    main()
