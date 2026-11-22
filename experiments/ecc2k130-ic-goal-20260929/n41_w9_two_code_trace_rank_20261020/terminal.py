"""Audit the entire frozen two-code trace-rank evidence chain."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
protocol_path=HERE/"terminal_protocol.json"
protocol=json.loads(protocol_path.read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path,digest in protocol["sources"].items():
    assert sha(path)==digest,path
for prefix,result_name in (("export","export_result.json"),
                           ("rank","rank_result.json"),
                           ("both","both_result.json"),
                           ("audit","audit_result.json"),
                           ("verify_retry","verification_retry_result.json")):
    p=HERE/f"{prefix}_protocol.json"
    r=json.loads((HERE/result_name).read_text())
    for path,digest in json.loads(p.read_text())["sources"].items():
        assert sha(path)==digest,(prefix,path)
    assert r["protocol_sha256"]==sha(p)
    assert r["candidate_id"] is None
failure=json.loads((HERE/"verification_attempt1_failure.json").read_text())
assert failure["status"]=="ASSERTION_FAILURE_REVERSED_ORIENTATION_VERIFIER"
assert failure["protocol_sha256"]==sha(HERE/"verify_protocol.json")
assert failure["script_sha256"]==sha(HERE/"verify.py")
assert failure["stderr_sha256"]==sha(HERE/"verification.stderr")
assert failure["stdout_sha256"]==sha(HERE/"verification.stdout")
assert not (HERE/"verification_result.json").exists()
v=json.loads((HERE/"verification_retry_result.json").read_text())
assert v["status"]=="PASS_INDEPENDENT_N41_TWO_CODE_RANK_AUDIT"
assert [v["code_monomial_rank"],v["ordered_feature_rank"],v["both_orientation_rank"]]==[136,5712,5754]
assert v["first_full_reversed_family"]==7
assert not (HERE/"verification_retry.stderr").read_text()
log=(HERE/"lean_check.log").read_text()
assert "error:" not in log and "sorryAx" not in log
assert "sorry" not in (HERE/"TwoCodeTraceRank.lean").read_text()
out={"status":"PASS_N41_TWO_CODE_TRACE_RANK_TERMINAL_AUDIT",
     "candidate_id":None,"curve_id":protocol["curve_id"],
     "families":2482,"signed_assignments":39712,"ordered_rank":5712,
     "full_rank":5754,"first_full_reversed_family":7,
     "first_verifier_status":failure["status"],
     "protocol_sha256":sha(protocol_path)}
dest=HERE/"terminal_result.json"
assert not dest.exists()
dest.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
print(json.dumps(out,sort_keys=True))
