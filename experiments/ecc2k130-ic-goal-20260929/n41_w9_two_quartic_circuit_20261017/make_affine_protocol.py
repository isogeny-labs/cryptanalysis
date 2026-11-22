"""Pin the independent, previously audited fixed-code support."""
import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
root=here.parent
paths={"script":here/"affine_census.py",
       "support":root/"n41_w9_joint_residual_20261017/support.json",
       "support_audit":root/"n41_w9_joint_residual_20261017/audit_result.json",
       "states":root/"n41_n131_w29_rotation_alignment_20261017/aligned_states.json"}
assert not (here/"affine_protocol.json").exists()
out={"status":"FROZEN_BEFORE_FIXED_CODE_AFFINE_CENSUS",
     "candidate_id":None,
     "sources":{str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                for path in paths.values()},
     **{key:str(paths[key]) for key in ("support","support_audit","states")}}
(here/"affine_protocol.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
