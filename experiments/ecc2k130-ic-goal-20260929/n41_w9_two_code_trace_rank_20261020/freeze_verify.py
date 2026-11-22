import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
families=json.loads((here/"families.json").read_text())
paths=[here/name for name in ("verify.py","families.json","export_result.json",
                            "rank_result.json","both_result.json","audit_result.json",
                            "lean_check.log","TwoCodeTraceRank.lean","lean-toolchain")]
protocol={"status":"FROZEN_BEFORE_INDEPENDENT_N41_TWO_CODE_RANK_AUDIT",
          "candidate_id":None,"curve_id":families["curve_id"],
          "wall_cap_seconds":300,"worker_count":1,
          "sources":{str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
          "test":"Independent low-pivot rank replay of all 2482 ordered families and first reversed families; audit source-only order relation and full 5754 feature rank"}
out=here/"verify_protocol.json"
assert not out.exists()
out.write_text(json.dumps(protocol,sort_keys=True,indent=2)+"\n")
print(hashlib.sha256(out.read_bytes()).hexdigest())
