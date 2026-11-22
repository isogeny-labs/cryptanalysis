#!/usr/bin/env python3
"""Freeze a complete four-family replay after the capped 17-family sweep."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
base = json.loads((HERE / "protocol.json").read_text())
partial = json.loads((HERE / "query_run_status.json").read_text())
assert partial["status"] == "CENSORED_TIME"
ids = ["positive", "slot0_alternative0", "slot0_alternative1",
       "slot1_alternative0"]
assert all(item in base["left_family_ids"] for item in ids)
sources = dict(base["sources"])
for name in ("protocol.json", "query_run_status.json", "query_stdout.log",
             "query_subset_sage.py", "audit_subset_sage.py", "run_subset_phase.py"):
    path = HERE / name
    sources[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
protocol = {
    **base,
    "kind": "n41_target_derived_upper_root_fiber_gcd_four_family_replay",
    "left_family_ids": ids,
    "sources": sources,
    "parent_sweep_status": "CENSORED_TIME",
    "selection_rule": "positive and first two slot-0 plus first slot-1 same-seed controls, frozen before subset execution",
}
path = HERE / "subset_protocol.json"
if path.exists():
    assert json.loads(path.read_text()) == protocol
else:
    path.write_text(json.dumps(protocol, indent=2, sort_keys=True) + "\n")
print(protocol["status"], len(ids))
