"""Rebuild the public XCNF and check that no source code bit is fixed."""
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
protocol = json.loads((D / "formula_audit_protocol.json").read_text())
for path, digest in protocol["sources"].items():
    assert sha(path) == digest, path
spec = importlib.util.spec_from_file_location("hybrid_formula_rebuild", D / "circuit.py")
circuit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(circuit)
build = json.loads((D / "build_result.json").read_text())
target = circuit.F.inv(build["public_raw_point"][0])
machine, wires = circuit.build(target)
code_wires = {wire for row in wires["codes"] for wire in row}
unit_code = []
for clause in machine.clauses:
    words = clause.split()
    if len(words) == 2 and words[-1] == "0" and abs(int(words[0])) in code_wires:
        unit_code.append(int(words[0]))
assert len(code_wires) == 42 and not unit_code
assert machine.next_var - 1 == build["variables"]
assert machine.and_count == build["and_gates"]
assert len(machine.clauses) == build["ordinary_clauses"]
assert len(machine.xors) == build["native_xor_rows"]
with tempfile.TemporaryDirectory(prefix="hybrid_formula_audit_") as temp:
    formula = Path(temp) / "public.xcnf"
    machine.write(formula)
    digest = sha(formula)
assert digest == build["formula_sha256"] == sha(D / "public.xcnf")
out = {"status": "PASS_HYBRID_XCNF_BYTE_REBUILD_AND_FREE_CODES",
       "protocol_sha256": sha(D / "formula_audit_protocol.json"),
       "formula_sha256": digest, "source_code_wires": len(code_wires),
       "unit_source_code_wires": unit_code,
       "variables": machine.next_var - 1,
       "and_gates": machine.and_count}
(D / "formula_audit_result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(out["status"])
