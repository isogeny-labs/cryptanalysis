"""Terminal checks for the frozen norm-ANF panel and independent replays."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
read = lambda name: json.loads((HERE/name).read_text())
producer = read("result.json")
partial1 = read("audit_result.json")
partial2 = read("audit_result_v2.json")
ordinary = read("audit_result_v3.json")
assert producer["status"] == "COMPLETE_N41_NORM_ANF"
assert producer["candidate_id"] is None
assert [row["target_index"] for row in producer["rows"]] == [0,1]
assert all(row["codes_checked"]==1024 for row in producer["rows"])
assert all(row["anf_nonzero_coefficients"]==1024 and row["anf_degree"]==10 for row in producer["rows"])
assert producer["rows"][0]["zero_codes"]==[253]
assert producer["rows"][1]["zero_codes"]==[]
assert partial1["status"]==partial2["status"]=="WALL_CAP_PARTIAL_AUDIT"
assert partial1["rows"][0]["codes_checked"]==partial2["rows"][0]["codes_checked"]==1024
assert partial1["rows"][1]["codes_checked"]==542
assert partial2["rows"][1]["codes_checked"]==393
assert ordinary["status"]=="PASS_INDEPENDENT_N41_NORM_ANF_AUDIT"
assert ordinary["rows"][0]["target_index"]==1 and ordinary["rows"][0]["codes_checked"]==1024
for reference, index in [(partial1["rows"][0],0),(partial2["rows"][0],0),(ordinary["rows"][0],1)]:
    expected=producer["rows"][index]
    assert reference["anf_coefficients_sha256"]==expected["anf_coefficients_sha256"]
    assert reference["zero_codes"]==expected["zero_codes"]
    assert reference["anf_nonzero_coefficients"]==expected["anf_nonzero_coefficients"]
for protocol_name, result_name, script_name, digest_key in [
    ("protocol.json","result.json","run_sage.py","script_sha256"),
    ("audit_protocol.json","audit_result.json","audit_sage.py","auditor_sha256"),
    ("audit_protocol_v2.json","audit_result_v2.json","audit_sage_v2.py","auditor_sha256"),
    ("audit_protocol_v3.json","audit_result_v3.json","audit_sage_v3.py","auditor_sha256")]:
    protocol=read(protocol_name);result=read(result_name)
    for source in protocol["sources"].values():
        assert sha(source["path"])==source["sha256"],source["path"]
    key="protocol_sha256" if protocol_name=="protocol.json" else "audit_protocol_sha256"
    assert result[key]==sha(HERE/protocol_name)
    assert result[digest_key]==sha(HERE/script_name)
lean=read("lean_check.json")
assert lean["status"]=="LEAN_BUILD_PASS"
assert lean["module_sha256"]==sha(HERE/"ANFButterfly.lean")
assert "does not depend on any axioms" in (HERE/"lean.stdout").read_text()
assert (HERE/"lean.stderr").read_text()==""
print("PASS_N41_NORM_ANF_FROZEN_PANEL")
