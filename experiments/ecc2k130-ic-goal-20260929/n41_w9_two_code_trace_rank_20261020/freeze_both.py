import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
source=json.loads((here/"families.json").read_text())
paths=[here/"rank_both.py",here/"rank_result.json",here/"export_result.json",here/"families.json"]
protocol={"status":"FROZEN_BEFORE_N41_BOTH_ORIENTATION_RANK",
          "candidate_id":None,"curve_id":source["curve_id"],
          "feature_columns":5754,"wall_cap_seconds":120,"worker_count":1,
          "sources":{str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
          "test":"Process all eligible left<right output families then their exact commutative reversed orientations; stop at full degree-two code-affine feature rank"}
out=here/"both_protocol.json"
assert not out.exists()
out.write_text(json.dumps(protocol,sort_keys=True,indent=2)+"\n")
print(hashlib.sha256(out.read_bytes()).hexdigest())
