"""Freeze exact source panels and targets before the prefix-capacity census."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
path = HERE / "protocol.json"
assert not path.exists()
sources = {
    "run": HERE / "run_sage.py",
    "freeze": Path(__file__),
    "n41_geometry": ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json",
    "n41_relation": ROOT / "n41_w8_sixpair_sat_20261016/join_audit_result.json",
    "n131_first_variants": ROOT / "n41_n131_rr_code_family_span_20261017/panel_n131_v2.json",
    "n131_sixpair_panel": ROOT / "n41_n131_sixpair_rr_root_span_20261016/frozen_panels.json",
    "n131_public": ROOT / "n131_w23_sixpair_public_sat_20261017/protocol.json",
    "runtime": HERE / "sage_runtime_info.json",
}
cfg = {"status": "FROZEN_BEFORE_TRIPLE_X_PREFIX_CAPACITY",
       "candidate_id": None,
       "curve_ids": ["EC1N41Ckb1h7d5e80d3c4d0",
                     "EC1N131Ckb1heb5f1998f20b"],
       "n41_first_masks": [217, "ascending_valid_disjoint_until_8"],
       "n41_fixed_masks": [196, 157],
       "n131_first_variants": "four_archived_plus_next_valid_disjoint_mask_above_46",
       "n131_fixed_edges": [1, 2],
       "n131_fixed_suffix_edges": [3, 4, 5],
       "wall_cap_seconds": 120,
       "sources": {name: {"path": str(source), "sha256": sha(source)}
                   for name, source in sources.items()}}
path.write_text(json.dumps(cfg, sort_keys=True, indent=2) + "\n")
print(cfg["status"])
