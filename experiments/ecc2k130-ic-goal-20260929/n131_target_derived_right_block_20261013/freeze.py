#!/usr/bin/env python3
"""Freeze one constructed public point and supplied left block for target handling."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
fixture_path = GOAL / "n131_w18_allseed_fourpair_20261012/n131_control_fixture.json"
fixture = json.loads(fixture_path.read_text())
assert fixture["status"] == "PASS_N131_DIAGONAL_ALLSEED_FOURPAIR_CONSTRUCTED_CHART"
source_paths = [fixture_path, HERE / "derive_targets_sage.py",
                HERE / "sage_runtime_info.json"]
protocol = {
    "status": "FROZEN",
    "kind": "n131_w18_constructed_public_target_derived_right_block",
    "curve_id": fixture["curve_id"], "target_count": 1,
    "candidate_id": None, "run_id": None,
    "target_kind": "constructed_correctness_control",
    "public_target": fixture["public_target"],
    "left_block_reciprocal": fixture["intermediate_reciprocals"][0],
    "left_input_law": "known source-block correctness fixture; not generated from the public target",
    "subgroup_order": 680564733841876926932320129493409985129,
    "torsion_search_max_x_code": 128,
    "worker_count": 1,
    "target_derivation_wall_cap_seconds": 120,
    "combined_pipeline_wall_cap_seconds": 600,
    "rss_cap_bytes": 4*(1 << 30),
    "sources": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in source_paths},
}
path = HERE / "protocol.json"
if path.exists():
    assert json.loads(path.read_text()) == protocol
else:
    path.write_text(json.dumps(protocol, indent=2, sort_keys=True) + "\n")
print(protocol["status"], protocol["curve_id"])
