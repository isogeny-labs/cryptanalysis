import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
states=here.parent/"n41_n131_w29_rotation_alignment_20261017/aligned_states.json"
source=json.loads((here/"families.json").read_text())
paths=[here/"audit_sage.py",here/"export_result.json",here/"families.json",states,here/"sage_runtime_info.json"]
protocol={"status":"FROZEN_BEFORE_INDEPENDENT_N41_TWO_CODE_X_AUDIT",
          "candidate_id":None,"curve_id":source["curve_id"],
          "states":str(states),"wall_cap_seconds":180,"worker_count":1,
          "sources":{str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
          "test":"Explicit binary-curve affine x-addition on all 2482 eligible ordered families and 39712 signed assignments, checking exported reciprocal coordinate for each"}
out=here/"audit_protocol.json"
assert not out.exists()
out.write_text(json.dumps(protocol,sort_keys=True,indent=2)+"\n")
print(hashlib.sha256(out.read_bytes()).hexdigest())
