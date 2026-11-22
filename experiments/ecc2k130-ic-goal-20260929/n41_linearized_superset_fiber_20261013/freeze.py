#!/usr/bin/env python3
"""Freeze the two-family linearized-superset membership control."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
PRIOR = GOAL / "n41_target_derived_fiber_gcd_20261013"
source = json.loads((PRIOR / "subset_protocol.json").read_text())
assert source["status"] == "FROZEN" and source["target_count"] == 1
ids = ["positive", "slot1_alternative0"]
assert all(item in source["left_family_ids"] for item in ids)
paths = [GOAL / "n41_joint_fourpair_resultant_20261012/panel.json",
         GOAL / "n41_symbolic_seed_fiber_20261012/panel.json",
         GOAL / "n131_w15_rotated_fouratom_inverse_20261010/resultant.json",
         PRIOR / "subset_result.json", PRIOR / "subset_audit.json",
         HERE / "sage_runtime_info.json", HERE / "query_sage.py", HERE / "run.py"]
protocol = {
    "status": "FROZEN", "kind": "n41_target_derived_linearized_superset_gcd",
    "curve_id": source["curve_id"], "target_count": 1, "batch": False,
    "candidate_id": None, "run_id": None,
    "public_target": source["public_target"],
    "target_reciprocal": source["target_reciprocal"],
    "left_family_ids": ids, "right_seed_bin_size": 32,
    "full_product_space_size": 128,
    "query_wall_cap_seconds": 180,
    "process_tree_rss_cap_bytes": 4*(1 << 30),
    "worker_count": 1,
    "control_change": "replace valid-root product polynomial by full linearized product-space polynomial and filter recovered roots to the usable source",
    "sources": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in paths},
}
path = HERE / "protocol.json"
if path.exists():
    assert json.loads(path.read_text()) == protocol
else:
    path.write_text(json.dumps(protocol, indent=2, sort_keys=True) + "\n")
print(protocol["status"], len(ids))
