"""Freeze independent reverse-order feature and low-pivot audit."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / "n41_n131_triple_x_prefix_capacity_20261023"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
path = HERE / "audit_protocol.json"
assert not path.exists()
sources = {"auditor": HERE / "audit_rank.py",
           "freeze": Path(__file__),
           "sets": HERE / "extended_sets.jsonl",
           "source_result": HERE / "extended_result.json",
           "rank_rows": HERE / "extended_rank_rows.jsonl",
           "rank_result": HERE / "extended_rank_result.json",
           "prior_result": ROOT / "result_v2.json"}
cfg = {"status": "FROZEN_BEFORE_N131_QUADRATIC_RANK_AUDIT",
       "candidate_id": None,
       "family_count": 280, "field_degree": 131,
       "wall_cap_seconds": 300,
       "sources": {name: {"path": str(p), "sha256": sha(p)}
                   for name, p in sources.items()}}
path.write_text(json.dumps(cfg, sort_keys=True, indent=2) + "\n")
print(cfg["status"])
