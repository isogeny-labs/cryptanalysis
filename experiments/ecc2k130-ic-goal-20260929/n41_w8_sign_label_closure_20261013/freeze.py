"""Freeze the N41 seven-pair sign and source-label audit."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
GEOMETRY = ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json"
PRIOR = ROOT / "n41_w8_functional_root_table_v2_20261013"
paths = [HERE / "audit.py", GEOMETRY, PRIOR / "circuit.py",
         PRIOR / "protocol.json", PRIOR / "public_result.json", PRIOR / "control_result.json"]
geometry = json.loads(GEOMETRY.read_text())
record = {
    "status": "FROZEN", "candidate_id": None,
    "kind": "n41_w8_fixed_seed_sevenpair_sign_label_closure",
    "geometry_path": str(GEOMETRY),
    "curve_id": geometry["curve_id"],
    "public_point": geometry["positive_control"]["subgroup_target"],
    "raw_target": geometry["positive_control"]["raw_target"],
    "sources": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
}
with (HERE / "protocol.json").open("x") as stream:
    json.dump(record, stream, indent=2, sort_keys=True)
    stream.write("\n")
print("FROZEN_N41_W8_SIGN_LABEL_CLOSURE")
