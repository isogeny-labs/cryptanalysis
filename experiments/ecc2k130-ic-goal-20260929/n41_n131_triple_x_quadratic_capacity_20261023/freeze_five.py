"""Freeze degree-two feature test on the prior exact five-code panel."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / "n41_n131_triple_x_prefix_capacity_20261023"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
path = HERE / "five_protocol.json"
assert not path.exists()
sources = {"runner": HERE / "run_five.py",
           "freeze": Path(__file__),
           "x_sets": ROOT / "x_sets_v2.json",
           "prior_result": ROOT / "result_v2.json",
           "prior_audit": ROOT / "audit_result.json",
           "runtime": ROOT / "sage_runtime_info.json"}
cfg = {"status": "FROZEN_BEFORE_TRIPLE_X_QUADRATIC_FIVE",
       "candidate_id": None,
       "degree": 2, "include_linear_bits": True,
       "field_degrees": [41, 131],
       "wall_cap_seconds": 120,
       "sources": {name: {"path": str(p), "sha256": sha(p)}
                   for name, p in sources.items()}}
path.write_text(json.dumps(cfg, sort_keys=True, indent=2) + "\n")
print(cfg["status"])
