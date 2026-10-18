"""Freeze a terminal SAT model before independent Sage curve replay."""
import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
root=here.parent
assert not (here/"replay_protocol.json").exists()
query=json.loads((here/"query_result.json").read_text())
assert query["status"]=="SAT_MODEL_UNVERIFIED"
paths=[here/name for name in ("replay_model_sage.py","query_result.json",
                              "solver.stdout","solver.stderr","input_wires.json",
                              "formula.xcnf","sage_runtime_info.json")]
paths += [root/"n41_n131_w29_rotation_alignment_20261017/aligned_states.json",
          root/"n41_w9_implicit_fivepair_tower_20261017/fixture.json"]
out={"status":"FROZEN_BEFORE_SAGE_MODEL_GROUP_REPLAY",
     "candidate_id":None,
     "sources":{str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                for path in paths},
     "states":str(paths[-2]),"fixture":str(paths[-1])}
(here/"replay_protocol.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
