import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
families=json.loads((here/"families.json").read_text())
paths=[here/name for name in ("verify_retry.py","families.json","export_result.json",
                            "rank_result.json","both_result.json","audit_result.json",
                            "lean_check.log","TwoCodeTraceRank.lean","lean-toolchain",
                            "verify.py","verify_protocol.json","verification_attempt1_failure.json",
                            "verification.stderr","verification.stdout")]
protocol={"status":"FROZEN_BEFORE_INDEPENDENT_N41_TWO_CODE_RANK_RETRY",
          "candidate_id":None,"curve_id":families["curve_id"],
          "wall_cap_seconds":300,"worker_count":1,
          "sources":{str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
          "test":"Correct orientation swap after preserved first verifier failure; independent low-pivot rank replay of complete ordered source plus reversed families"}
out=here/"verify_retry_protocol.json"
assert not out.exists()
out.write_text(json.dumps(protocol,sort_keys=True,indent=2)+"\n")
print(hashlib.sha256(out.read_bytes()).hexdigest())
