#!/usr/bin/env python3
"""Freeze exact source and result inputs for independent group replay."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
result = json.loads((HERE / "pipeline_result.json").read_text())
assert result["status"] == "COMPLETE_ALL_TARGET_DERIVED_RIGHT_CANDIDATES"
assert len(result["attempts"]) == 8
assert [row["raw_gcd_hits"] for row in result["attempts"]] == [0,0,0,0,0,1,0,0]
paths = [HERE / name for name in ("protocol.json", "pipeline_protocol.json",
                                   "pipeline_result.json", "target_candidates.json",
                                   "attempt_05/native_result.json", "audit_sage.py",
                                   "run_audit.py", "run_pipeline.py",
                                   "sage_runtime_info.json")]
paths.extend([GOAL / "n131_w18_allseed_fourpair_20261012/n131_control_fixture.json",
              GOAL / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"])
protocol = {
    "status": "FROZEN",
    "kind": "n131_w18_target_derived_right_block_group_replay",
    "target_count": 1, "candidate_id": None,
    "wall_cap_seconds": 120, "rss_cap_bytes": 4*(1 << 30),
    "worker_count": 1,
    "sources": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in paths},
}
path = HERE / "audit_protocol.json"
if path.exists():
    assert json.loads(path.read_text()) == protocol
else:
    path.write_text(json.dumps(protocol, indent=2, sort_keys=True) + "\n")
print(protocol["status"])
