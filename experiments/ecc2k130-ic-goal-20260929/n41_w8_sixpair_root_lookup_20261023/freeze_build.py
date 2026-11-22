"""Freeze exact source-table circuit inputs before construction."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
path = HERE / "build_protocol.json"
assert not path.exists()
sources = {
    "builder": HERE / "build.py",
    "freeze": Path(__file__),
    "circuit": HERE / "circuit.py",
    "prior_circuit": ROOT / "n41_w8_sixpair_sat_20261016/circuit.py",
    "geometry": ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json",
    "public_relation": ROOT / "n41_w8_sixpair_sat_20261016/join_audit_result.json",
    "runtime": HERE / "sage_runtime_info.json",
}
cfg = {"status": "FROZEN_BEFORE_N41_ROOT_LOOKUP_BUILD",
       "candidate_id": None, "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
       "source_edges_per_slot": 40,
       "rotations": [0, 6, 12, 18, 24, 30],
       "sources": {name: {"path": str(source), "sha256": sha(source)}
                   for name, source in sources.items()}}
path.write_text(json.dumps(cfg, sort_keys=True, indent=2) + "\n")
print(cfg["status"])
