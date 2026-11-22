#!/usr/bin/env python3
"""Freeze the N131 W18 constructed-chart bridge inputs."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
paths = [GOAL / "n131_w18_allseed_fourpair_20261012/n131_control_fixture.json",
         GOAL / "n131_w15_rotated_fouratom_inverse_20261010/resultant.json",
         GOAL / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv",
         HERE / "check.py"]
fixture = json.loads(paths[0].read_text())
assert fixture["status"] == "PASS_N131_DIAGONAL_ALLSEED_FOURPAIR_CONSTRUCTED_CHART"
protocol = {
    "status": "FROZEN", "kind": "n131_w18_linearized_superset_source_resultant_bridge",
    "curve_id": fixture["curve_id"], "candidate_id": None,
    "target_kind": "constructed_correctness_control",
    "worker_count": 1,
    "input_sha256": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in paths},
    "sources": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in paths},
}
path = HERE / "protocol.json"
if path.exists():
    assert json.loads(path.read_text()) == protocol
else:
    path.write_text(json.dumps(protocol, indent=2, sort_keys=True) + "\n")
print(protocol["status"], fixture["curve_id"])
