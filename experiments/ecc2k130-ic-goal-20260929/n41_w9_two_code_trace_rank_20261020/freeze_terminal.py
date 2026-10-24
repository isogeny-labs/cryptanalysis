import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
families=json.loads((here/"families.json").read_text())
names=["terminal.py","RESULT.md","PROOF_MAP.md","families.json","export_protocol.json",
       "export_result.json","rank_protocol.json","rank_result.json","both_protocol.json",
       "both_result.json","audit_protocol.json","audit_result.json","verify_protocol.json",
       "verify.py","verification_attempt1_failure.json","verification.stderr","verification.stdout",
       "verify_retry_protocol.json","verification_retry_result.json","verification_retry.stdout",
       "verification_retry.stderr","lean_check.log","TwoCodeTraceRank.lean","lean-toolchain"]
paths=[here/name for name in names]
protocol={"status":"FROZEN_BEFORE_N41_TWO_CODE_TRACE_RANK_TERMINAL_AUDIT",
          "candidate_id":None,"curve_id":families["curve_id"],
          "sources":{str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}}
out=here/"terminal_protocol.json"
assert not out.exists()
out.write_text(json.dumps(protocol,sort_keys=True,indent=2)+"\n")
print(hashlib.sha256(out.read_bytes()).hexdigest())
