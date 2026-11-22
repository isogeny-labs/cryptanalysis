#!/usr/bin/env python3
"""Freeze the public-to-right-block one-worker control before its full run."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
base = json.loads((HERE / "protocol.json").read_text())
preview = json.loads((HERE / "preview_targets.json").read_text())
assert base["status"] == "FROZEN"
assert preview["status"] == "PASS_PUBLIC_POINT_TO_ALL_RIGHT_BLOCK_CANDIDATES"
assert preview["candidate_count"] == preview["distinct_candidate_count"] == 8
fixture_path = GOAL / "n131_w18_allseed_fourpair_20261012/n131_control_fixture.json"
fixture = json.loads(fixture_path.read_text())
assert fixture["intermediate_reciprocals"][1] in [v for row in preview["rows"]
                                                 for v in row["right_roots"]]
support = GOAL / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"
paths = [HERE / name for name in ("protocol.json", "preview_targets.json",
                                   "derive_targets_sage.py", "sage_runtime_info.json",
                                   "native_right.cpp", "rotated_terms.hpp", "native_right",
                                   "run_pipeline.py", "clang_version.txt")]
paths.extend([fixture_path, support])
protocol = {
    "status": "FROZEN",
    "kind": "n131_w18_constructed_public_to_all_right_fibers",
    "curve_id": base["curve_id"], "target_count": 1,
    "candidate_id": None, "run_id": None,
    "target_kind": "constructed_correctness_control",
    "left_input_law": base["left_input_law"],
    "worker_count": 1,
    "total_wall_cap_seconds": 600,
    "rss_cap_bytes": 4*(1 << 30),
    "right_seed_masks": [5,1], "right_rotations": [64,96],
    "expected_usable_first_products": 32827,
    "expected_full_second_product_space": 1 << 17,
    "compile_command": ["clang++", "-O3", "-std=c++20", "-Wall", "-Wextra",
                        "native_right.cpp", "-o", "native_right"],
    "sources": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in paths},
}
path = HERE / "pipeline_protocol.json"
if path.exists():
    assert json.loads(path.read_text()) == protocol
else:
    path.write_text(json.dumps(protocol, indent=2, sort_keys=True) + "\n")
print(protocol["status"], preview["candidate_count"])
