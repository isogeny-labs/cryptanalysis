"""Freeze N41 source-quadratic reduction after the direct-resultant probe."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / "n41_w9_joint_right_s3_20261023"
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
path = HERE / "reduction_protocol.json"
assert not path.exists()
probe = json.loads((HERE / "probe_result.json").read_text())
assert probe["status"] == "COMPLETED_FROZEN_ABBA_PROBE"
sources = {"script": HERE / "reduce_symbolic_sage.py",
           "freeze_script": Path(__file__),
           "runtime": HERE / "sage_runtime_info.json",
           "probe_result": HERE / "probe_result.json",
           "preflight_result": HERE / "preflight_result.json",
           "states": ROOT / "n41_n131_w29_rotation_alignment_20261017/aligned_states.json",
           "panel": ROOT / "n41_w9_two_quartic_resultant_20261017/panel.json",
           "join_rows": PRIOR / "join_rows.json",
           "fixture": ROOT / "n41_w9_implicit_fivepair_tower_20261017/fixture.json"}
cfg = {"status": "FROZEN_BEFORE_N41_SOURCE_QUADRATIC_REDUCTION",
       "candidate_id": None, "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
       "wall_cap_seconds": 120, "rss_cap_bytes": 4294967296,
       "sources": {name: {"path": str(source), "sha256": sha(source)}
                   for name,source in sources.items()}}
path.write_text(json.dumps(cfg, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": cfg["status"], "protocol_sha256": sha(path)}, sort_keys=True))
