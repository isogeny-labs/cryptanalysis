#!/usr/bin/env python3
"""Freeze the constructed N131 W18 sparse-superset native stage."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
preflight = json.loads((HERE / "result.json").read_text())
fixture = json.loads((GOAL / "n131_w18_allseed_fourpair_20261012/n131_control_fixture.json").read_text())
assert preflight["status"] == "PASS_N131_W18_CONSTRUCTED_SOURCE_RESULTANT_BRIDGE"
assert preflight["usable_pair_counts_by_slot"][:2] == [32947,32916]
assert fixture["intermediate_reciprocals"][0] == 1397139031383803385761202952286479025964
input_tokens = (HERE / "native_input.txt").read_text().split()
assert input_tokens == ["131", "18", "0", "32", "14", "6",
                        str(fixture["intermediate_reciprocals"][0])]
paths = [HERE / name for name in ("native_w18.cpp", "rotated_terms.hpp", "native_w18",
                                   "native_input.txt", "run_native.py", "clang_version.txt",
                                   "protocol.json", "result.json")]
paths.extend([GOAL / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv",
              GOAL / "n131_w18_allseed_fourpair_20261012/n131_control_fixture.json"])
protocol = {
    "status": "FROZEN",
    "kind": "n131_w18_constructed_first_fouratom_linearized_superset_scan",
    "curve_id": fixture["curve_id"], "candidate_id": None,
    "target_kind": "constructed_correctness_control",
    "worker_count": 1,
    "query_cap_seconds": 600, "parent_wall_cap_seconds": 610,
    "rss_cap_bytes": 4*(1 << 30),
    "expected_usable_first_products": 32947,
    "full_second_product_space_size": 1 << 17,
    "compile_command": ["clang++", "-O3", "-std=c++20", "-Wall", "-Wextra",
                        "native_w18.cpp", "-o", "native_w18"],
    "sources": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in paths},
}
path = HERE / "native_protocol.json"
if path.exists():
    assert json.loads(path.read_text()) == protocol
else:
    path.write_text(json.dumps(protocol, indent=2, sort_keys=True) + "\n")
print(protocol["status"], protocol["expected_usable_first_products"])
