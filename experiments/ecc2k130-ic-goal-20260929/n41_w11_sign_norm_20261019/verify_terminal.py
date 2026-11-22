"""Hash-bound terminal gate for nonlinear N41 sign-norm certificates."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg=json.loads((HERE/"terminal_protocol.json").read_text())
assert cfg["status"]=="FROZEN_BEFORE_N41_NORM_TERMINAL"
for label,source in cfg["sources"].items():
    assert sha(source["path"])==source["sha256"],label
for name in ("protocol.json","protocol_v2.json","audit_protocol.json"):
    protocol=json.loads((HERE/name).read_text())
    for label,source in protocol["sources"].items():
        assert sha(source["path"])==source["sha256"],(name,label)
v1=json.loads((HERE/"result.json").read_text())
v2=json.loads((HERE/"result_v2.json").read_text())
audit=json.loads((HERE/"audit_result.json").read_text())
receipt=json.loads((HERE/"audit_receipt.json").read_text())
prior=json.loads(Path(cfg["sources"]["prior_terminal"]["path"]).read_text())
linear=json.loads(Path(cfg["sources"]["prior_code_box_result"]["path"]).read_text())
assert prior["status"]=="PASS_SIGN_QUADRATIC_AND_POOL_TERMINAL_AUDIT"
assert v1["status"]==v2["status"]=="COMPLETE_SIGN_NORM"
assert v1["boxes_completed"]==v2["boxes_completed"]==9
assert v1["certified_random_boxes"]==v2["certified_random_boxes"]==8
assert v1["protocol_sha256"]==sha(HERE/"protocol.json")
assert v2["protocol_sha256"]==sha(HERE/"protocol_v2.json")
assert all(row["variation_rank"]==41 and row["single_coordinate_certificate"] is False
           for row in linear["rows"])
assert v2["rows"][0]["norm_rank"]==31
assert v2["rows"][0]["zero_pairs"]==[[0,30]]
assert v2["rows"][0]["trace_mask"] is None
for row in v2["rows"][1:]:
    assert row["norm_rank"]==32 and row["zero_pairs"]==[]
    assert row["trace_mask"] is not None
    assert row["trace_anf"]==[1]+[0]*31
    assert all((row["trace_mask"]&value).bit_count()%2==1 for value in row["norms"])
assert [x["norms"] for x in v1["rows"]]==[x["norms"] for x in v2["rows"]]
assert audit["status"]=="PASS_INDEPENDENT_SAGE_NORM_AUDIT"
assert audit["boxes_checked"]==9 and audit["norm_products_checked"]==288
assert audit["determinant_factors_checked"]==9216 and audit["trace_values_checked"]==256
assert audit["zero_pairs_checked"]==1
assert audit["protocol_sha256"]==sha(HERE/"audit_protocol.json")
assert receipt["status"]=="COMPLETE" and receipt["exit_code"]==0
assert receipt["stop_reason"] is None and receipt["monitor_error"] is None
assert receipt["command"][0]=="/Volumes/SSD990/cryptanalysis/sage"
assert receipt["wall_seconds"]<120 and receipt["sampled_peak_combined_rss_bytes"]<4294967296
assert receipt["protocol_sha256"]==sha(HERE/"audit_protocol.json")
assert receipt["result_sha256"]==sha(HERE/"audit_result.json")
assert receipt["stdout_sha256"]==sha(HERE/"audit.stdout")
assert receipt["stderr_sha256"]==sha(HERE/"audit.stderr")
assert (HERE/"audit.stderr").read_bytes()==b""
for prefix in ("run","run_v2"):
    assert (HERE/(prefix+".stderr")).read_bytes()==b""
assert v2["wall_seconds"]<120 and v2["peak_rss_raw"]<4294967296
lean=(HERE/"SignNorm.lean").read_text()
assert "sorry" not in lean and "admit" not in lean and "axiom " not in lean
assert (HERE/"lean.stderr").read_bytes()==b""
output=(HERE/"lean.stdout").read_text()
assert "sorryAx" not in output
assert "SignNorm.trace_norm_excludes_box" in output
assert "SignNorm.trace_norm_excludes_each_sign" in output
terminal={"status":"PASS_N41_NONLINEAR_SIGN_NORM_GATE","candidate_id":None,
          "curve_id":v2["curve_id"],"constructed_relation_survived":True,
          "ordinary_boxes_certified":8,"norm_products_sage_replayed":288,
          "determinant_factors_sage_replayed":9216,
          "protocol_sha256":sha(HERE/"terminal_protocol.json"),
          "verifier_sha256":sha(Path(__file__))}
(HERE/"terminal_result.json").write_text(json.dumps(terminal,indent=2,sort_keys=True)+"\n")
print(json.dumps(terminal,sort_keys=True))
