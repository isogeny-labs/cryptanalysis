"""Freeze the complete XCNF source-label clause audit."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / "n41_w8_functional_root_table_v2_20261013"
paths = [HERE / "audit_formula.py", HERE / "result.json", PRIOR / "circuit.py",
         PRIOR / "public.xcnf", PRIOR / "control_result.json",
         ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json"]
record = {"status": "FROZEN", "kind": "n41_w8_sevenpair_xcnf_exact_source_label_clauses",
          "sources": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
with (HERE / "formula_protocol.json").open("x") as stream:
    json.dump(record, stream, indent=2, sort_keys=True)
    stream.write("\n")
print("FROZEN_SEVENPAIR_LABEL_FORMULA_AUDIT")
