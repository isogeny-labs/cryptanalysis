"""Freeze the independent normalized-kernel arithmetic panel."""
import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
root=here.parent
paths={
    "script":here/"kernel_sage.py",
    "panel":root/"n41_w9_two_quartic_resultant_20261017/panel.json",
    "states":root/"n41_n131_w29_rotation_alignment_20261017/aligned_states.json",
    "fixture":root/"n41_w9_implicit_fivepair_tower_20261017/fixture.json",
    "prior_audit":root/"n41_w9_two_quartic_circuit_20261017/bezout_result.json",
    "runtime":here/"sage_runtime_info.json",
}
assert not (here/"kernel_protocol.json").exists()
out={"status":"FROZEN_BEFORE_NORMALIZED_KERNEL_SAGE_PANEL",
     "candidate_id":None,"wall_cap_seconds":120,
     "sources":{str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                for path in paths.values()},
     **{name:str(paths[name]) for name in ("panel","states","fixture")}}
(here/"kernel_protocol.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
