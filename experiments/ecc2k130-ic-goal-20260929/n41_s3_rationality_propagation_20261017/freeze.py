"""Freeze sources and public input before building the direct-leaf circuit."""
import hashlib
import json
from pathlib import Path


D = Path(__file__).resolve().parent
ROOT = D.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


sources = [
    "n41_sixpair_shared_target_20261017/circuit.py",
    "n41_sixpair_shared_target_20261017/build_result.json",
    "n41_sixpair_shared_target_20261017/join_audit_result.json",
    "n41_w8_fixed_sum_table_20261009/geometry.json",
    "n131_w20_selector_elimination_v2_20261013/selector.py",
]
g = json.loads((ROOT / sources[3]).read_text())
hit = json.loads((ROOT / sources[2]).read_text())
assert hit["raw_target"] == g["positive_control"]["raw_target"]
record = {
    "schema": 1,
    "candidate_id": None,
    "curve_id": g["curve_id"],
    "public_raw_point": hit["raw_target"],
    "fixed_seed_sum_code": g["fixed_seed_sum_code"],
    "rotations": g["rotations"][:6],
    "source_sha256": {name: sha(ROOT / name) for name in sources},
    "circuit_sha256": sha(D / "circuit.py"),
    "builder_sha256": sha(D / "build.py"),
    "geometry_sha256": sha(ROOT / sources[3]),
    "relation_sha256": sha(ROOT / sources[2]),
    "runtime_info_sha256": sha(D / "sage_runtime_info.json"),
    "producer_sha256": sha(Path(__file__)),
    "input_policy": "public target, 40 legal fixed-seed codes per slot, six free pair outputs, folded-column exclusions",
}
(D / "protocol.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
print(sha(D / "protocol.json"))
