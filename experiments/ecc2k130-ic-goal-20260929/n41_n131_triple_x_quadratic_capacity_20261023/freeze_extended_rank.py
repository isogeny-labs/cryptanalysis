"""Freeze the full 280-family quadratic rank pass before computation."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / "n41_n131_triple_x_prefix_capacity_20261023"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
path = HERE / "extended_rank_protocol.json"
assert not path.exists()
sources = {"runner": HERE / "rank_extended.py",
           "freeze": Path(__file__),
           "sets": HERE / "extended_sets.jsonl",
           "source_result": HERE / "extended_result.json",
           "source_protocol": HERE / "extended_protocol.json",
           "prior_result": ROOT / "result_v2.json",
           "five_result": HERE / "five_result.json"}
cfg = {"status": "FROZEN_BEFORE_N131_EXTENDED_QUADRATIC_RANK",
       "candidate_id": None, "field_degree": 131,
       "source_families": 280, "feature_degree": 2,
       "include_linear_bits": True, "wall_cap_seconds": 300,
       "sources": {name: {"path": str(p), "sha256": sha(p)}
                   for name, p in sources.items()}}
path.write_text(json.dumps(cfg, sort_keys=True, indent=2) + "\n")
print(cfg["status"])
