"""Freeze W23 source-law extension before generating 280 triple-x families."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
path = HERE / "extended_protocol.json"
assert not path.exists()
sources = {
    "producer": HERE / "generate_extended_sage.py",
    "freeze": Path(__file__),
    "prior_result": ROOT / "n41_n131_triple_x_prefix_capacity_20261023/result_v2.json",
    "prior_sets": ROOT / "n41_n131_triple_x_prefix_capacity_20261023/x_sets_v2.json",
    "first_variant_panel": ROOT / "n41_n131_rr_code_family_span_20261017/panel_n131_v2.json",
    "sixpair_panel": ROOT / "n41_n131_sixpair_rr_root_span_20261016/frozen_panels.json",
    "runtime": HERE / "sage_runtime_info.json",
}
cfg = {"status": "FROZEN_BEFORE_N131_W23_EXTENDED_TRIPLE_X",
       "candidate_id": None,
       "curve_id": "EC1N131Ckb1heb5f1998f20b",
       "first_five": [[3, 898617], [10, 898608], [41, 898579],
                      [46, 898580], [47, 898581]],
       "scan_after_mask": 47,
       "family_count": 280,
       "fixed_edges": [1, 2],
       "exclude_folded_columns_of_edges": [1, 2, 3, 4, 5],
       "wall_cap_seconds": 300,
       "sources": {name: {"path": str(p), "sha256": sha(p)}
                   for name, p in sources.items()}}
path.write_text(json.dumps(cfg, sort_keys=True, indent=2) + "\n")
print(cfg["status"])
