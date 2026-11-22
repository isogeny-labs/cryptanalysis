"""Freeze the source and panel for direct joint-resultant preflight."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / "n41_w9_joint_right_s3_20261023"
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
path = HERE / "protocol.json"
assert not path.exists()
sources = {"script": HERE / "preflight.py", "freeze_script": Path(__file__),
           "panel": ROOT / "n41_w9_two_quartic_resultant_20261017/panel.json",
           "join_rows": PRIOR / "join_rows.json",
           "fixture": ROOT / "n41_w9_implicit_fivepair_tower_20261017/fixture.json",
           "prior_audit": PRIOR / "audit_result.json",
           "field_code": ROOT / "n131_w18_allseed_fourpair_20261012/fourpair_v2.py"}
cfg = {"status": "FROZEN_BEFORE_N41_QUADRATIC_RESULTANT_PREFLIGHT",
       "curve_id": "EC1N41Ckb1h7d5e80d3c4d0", "candidate_id": None,
       "public_point": [1936680952394, 910597499030],
       "sources": {name: {"path": str(source), "sha256": sha(source)}
                   for name, source in sources.items()}}
path.write_text(json.dumps(cfg, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": cfg["status"], "protocol_sha256": sha(path)}, sort_keys=True))
