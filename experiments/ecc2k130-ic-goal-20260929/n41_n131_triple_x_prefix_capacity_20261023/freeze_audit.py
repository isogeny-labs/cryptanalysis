"""Freeze independent Sage matrix replay of the saved x-coordinate sets."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
path = HERE / "audit_protocol.json"
assert not path.exists()
sources = {"auditor": HERE / "audit_sage.py",
           "freeze": Path(__file__),
           "producer_protocol": HERE / "protocol_v2.json",
           "producer_result": HERE / "result_v2.json",
           "x_sets": HERE / "x_sets_v2.json",
           "runtime": HERE / "sage_runtime_info.json",
           "first_failure": HERE / "failure_v1.json",
           "freeze_failure": HERE / "freeze_failure_v2.json"}
cfg = {"status": "FROZEN_BEFORE_TRIPLE_X_RANK_AUDIT",
       "candidate_id": None,
       "sources": {name: {"path": str(source), "sha256": sha(source)}
                   for name, source in sources.items()}}
path.write_text(json.dumps(cfg, sort_keys=True, indent=2) + "\n")
print(cfg["status"])
