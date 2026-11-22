"""Freeze the complete N41 final-pair two-quadratic root audit."""
import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
root=here.parent
paths={
    "script":here/"audit_sage.py",
    "states":root/"n41_n131_w29_rotation_alignment_20261017/aligned_states.json",
    "fixture":root/"n41_w9_implicit_fivepair_tower_20261017/fixture.json",
    "w_table":root/"n41_w9_target_w_bdd_20261017/w_table.json",
    "w_audit":root/"n41_w9_target_w_bdd_20261017/audit_result.json",
    "quartic_audit":root/"n41_w9_two_quartic_resultant_20261017/run_result.json",
    "runtime":here/"sage_runtime_info.json",
}
assert not (here/"audit_protocol.json").exists()
out={"status":"FROZEN_BEFORE_TWO_QUADRATIC_AUDIT",
     "candidate_id":None,"curve_id":"EC1N41Ckb1h7d5e80d3c4d0",
     "wall_cap_seconds":120,"rss_envelope_bytes":4*1024**3,
     "method":"solve fixed-seed source-pair quadratic, then solve target-conditioned S3 quadratic for each pair root",
     "sources":{str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                for path in paths.values()},
     **{key:str(paths[key]) for key in ("states","fixture","w_table","w_audit")}}
(here/"audit_protocol.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
