"""Gate public N131 sign-norm query on the independently replayed positive relation."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg=json.loads((HERE/"positive_gate_protocol.json").read_text())
assert cfg["status"]=="FROZEN_BEFORE_N131_POSITIVE_GATE"
for label,source in cfg["sources"].items():
    assert sha(source["path"])==source["sha256"],label
panel=json.loads((HERE/"panel.json").read_text())
result=json.loads((HERE/"positive_result.json").read_text())
receipt=json.loads((HERE/"positive_receipt.json").read_text())
coeff=json.loads((HERE/"positive_coefficients.json").read_text())
control=json.loads(Path(cfg["sources"]["control"]["path"]).read_text())
prior=json.loads(Path(cfg["sources"]["prior_replay"]["path"]).read_text())
n41=json.loads(Path(cfg["sources"]["n41_gate"]["path"]).read_text())
assert n41["status"]=="PASS_N41_NONLINEAR_SIGN_NORM_GATE"
assert control["status"]=="COMPLETE_CONSTRUCTED_CONTROL"
assert prior["curve_id"]==control["curve_id"]==panel["curve_id"]
assert prior["raw_target"]==control["target_raw_point"]==panel["boxes"][0]["target_point"]
assert prior["distinct_columns"]==control["distinct_folded_columns"]==10
assert result["status"]=="COMPLETE_N131_SIGN_NORM"
assert result["boxes_completed"]==1 and result["rows"][0]["box_index"]==0
assert result["rows"][0]["group_hits"]==[[0,27]]
assert panel["boxes"][0]["known_positive"]==[0,27]
assert result["rows"][0]["trace_mask"] is None
assert result["rows"][0]["norms"][0]==0
assert coeff["status"]=="COMPLETE_N131_SIGN_NORM"
assert len(coeff["boxes"])==1 and len(coeff["boxes"][0]["rows"])==32
assert receipt["status"]=="COMPLETE" and receipt["exit_code"]==0
assert receipt["stop_reason"] is None and receipt["monitor_error"] is None
assert receipt["wall_seconds"]<120 and receipt["sampled_peak_combined_rss_bytes"]<4294967296
assert receipt["command"][0]=="/Volumes/SSD990/cryptanalysis/sage"
assert receipt["result_sha256"]==sha(HERE/"positive_result.json")
assert receipt["coefficients_sha256"]==sha(HERE/"positive_coefficients.json")
assert receipt["stdout_sha256"]==sha(HERE/"positive.stdout")
assert receipt["stderr_sha256"]==sha(HERE/"positive.stderr")
assert (HERE/"positive.stderr").read_bytes()==b""
gate={"status":"PASS_N131_SIGN_NORM_POSITIVE_GATE","candidate_id":None,
      "curve_id":panel["curve_id"],"source_codes":[3,18,19,22,29],
      "root_sign_witness":[0,27],"wall_seconds":receipt["wall_seconds"],
      "sampled_peak_combined_rss_bytes":receipt["sampled_peak_combined_rss_bytes"],
      "protocol_sha256":sha(HERE/"positive_gate_protocol.json"),
      "verifier_sha256":sha(Path(__file__))}
(HERE/"positive_gate.json").write_text(json.dumps(gate,indent=2,sort_keys=True)+"\n")
print(json.dumps(gate,sort_keys=True))
