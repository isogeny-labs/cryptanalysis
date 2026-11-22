#!/usr/bin/env python3
"""Freeze one public-target N41 algebraic filter panel before execution."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
source_panel = GOAL / "n41_joint_fourpair_resultant_20261012/panel.json"
fiber_panel = GOAL / "n41_symbolic_seed_fiber_20261012/panel.json"
resultant = GOAL / "n131_w15_rotated_fouratom_inverse_20261010/resultant.json"
geometry = GOAL / "n41_w7_entropy_cubic_20261011/w8/geometry.json"
fixture = GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal/control_fixture.json"
source = json.loads(source_panel.read_text())
fiber = json.loads(fiber_panel.read_text())
control = json.loads(fixture.read_text())
assert source["curve_id"] == fiber["curve_id"] == control["curve_id"]
assert source["target_reciprocal"] == control["target_reciprocal"]
assert source["public_target"] == control["public_target"]
assert fiber["ordered_masks"][0][0] == control["masks"][2]
assert fiber["ordered_masks"][1][0] == control["masks"][3]
families = [f for f in source["families"] if f["id"] == "positive"
            or f["id"].startswith(("slot0_", "slot1_"))]
assert len(families) == 17
assert [f["id"] for f in families] == ["positive"] + [
    f"slot{i}_alternative{j}" for i in (0, 1) for j in range(8)]
files = [source_panel, fiber_panel, resultant, geometry, fixture,
         HERE / "query_sage.py", HERE / "audit_sage.py", HERE / "sage_runtime_info.json"]
protocol = {
    "status": "FROZEN", "kind": "n41_target_derived_upper_root_fiber_gcd",
    "candidate_id": None, "run_id": None,
    "curve_id": source["curve_id"], "target_count": 1, "batch": False,
    "public_target": source["public_target"],
    "target_reciprocal": source["target_reciprocal"],
    "left_family_ids": [f["id"] for f in families],
    "right_seed_bin_sizes": [32, 32],
    "query_wall_cap_seconds": 180, "audit_wall_cap_seconds": 180,
    "process_tree_rss_cap_bytes": 4 * (1 << 30), "worker_count": 1,
    "timing_boundary": "target-derived upper roots and right-fiber GCDs; source panel and Sage import are outside internal times but inside parent wall",
    "sources": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in files},
}
path = HERE / "protocol.json"
if path.exists():
    assert json.loads(path.read_text()) == protocol
else:
    path.write_text(json.dumps(protocol, indent=2, sort_keys=True) + "\n")
print(protocol["status"], len(families))
