"""Freeze the W8 public target, source laws, exact-slot policy, and runtime."""
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
    "circuit": HERE / "circuit_deferred.py",
    "freeze": Path(__file__),
    "runtime": HERE / "sage_runtime_info.json",
    "public_relation": ROOT / "n41_w8_sixpair_sat_20261016/join_audit_result.json",
    "prior_circuit": ROOT / "n41_w8_sixpair_sat_20261016/circuit.py",
    "source_geometry": ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json",
}
cfg = {"status": "FROZEN_BEFORE_N41_SIXPAIR_DEFERRED_BUILD",
       "candidate_id": None, "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
       "exact_slots": [0, 1, 2], "deferred_slots": [3, 4, 5],
       "source_width": 8, "pair_count": 6,
       "sources": {name: {"path": str(source), "sha256": sha(source)}
                   for name, source in sources.items()}}
path.write_text(json.dumps(cfg, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": cfg["status"], "protocol_sha256": sha(path)}, sort_keys=True))
