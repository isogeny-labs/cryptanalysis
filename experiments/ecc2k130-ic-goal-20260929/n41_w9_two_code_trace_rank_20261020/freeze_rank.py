import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
paths=[here/"rank.py",here/"export_result.json",here/"export_protocol.json",here/"families.json"]
source=json.loads((here/"families.json").read_text())
protocol={"status":"FROZEN_BEFORE_N41_TWO_CODE_TRACE_RANK",
          "candidate_id":None,"curve_id":source["curve_id"],
          "degree":2,"code_bits":16,"field_bits":41,"feature_columns":5754,
          "wall_cap_seconds":120,"worker_count":1,
          "sources":{str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
          "test":"Highest-pivot exact rank of m(code)*(1,z_bits) for all reciprocal outputs in seeded eligible code-family order; stop at full rank"}
out=here/"rank_protocol.json"
assert not out.exists()
out.write_text(json.dumps(protocol,sort_keys=True,indent=2)+"\n")
print(hashlib.sha256(out.read_bytes()).hexdigest())
