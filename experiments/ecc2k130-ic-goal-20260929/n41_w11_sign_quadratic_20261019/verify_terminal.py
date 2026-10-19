"""Verify frozen sources, stage receipts, Lean output, and independent replays."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg=json.loads((HERE/"terminal_protocol.json").read_text())
assert cfg["status"]=="FROZEN_BEFORE_TERMINAL_AUDIT"
for label,source in cfg["sources"].items():
    assert sha(source["path"])==source["sha256"],label

def read(name):
    return json.loads((HERE/name).read_text())

for name in ("protocol.json","run_protocol.json","code_box_protocol.json",
             "code_box_run_protocol.json","audit_protocol.json","columns_protocol.json"):
    protocol=read(name)
    for label,source in protocol["sources"].items():
        assert sha(source["path"])==source["sha256"],(name,label)

panel=read("panel.json")
box_panel=read("code_box_panel.json")
screen=read("result.json")
box=read("code_box_result.json")
aud=read("audit_result.json")
columns=read("columns_result.json")
assert panel["status"]=="FROZEN_SIGN_PANEL" and len(panel["rows"])==33
assert box_panel["status"]=="FROZEN_CODE_BOX_PANEL" and len(box_panel["boxes"])==9
assert panel["protocol_sha256"]==sha(HERE/"protocol.json")
assert box_panel["protocol_sha256"]==sha(HERE/"code_box_protocol.json")
assert screen["status"]=="COMPLETE_SIGN_SCREEN"
assert screen["families_completed"]==33
assert screen["positive_hit_families"]==1
assert screen["random_hit_families"]==0
assert screen["random_certificate_families"]==32
assert screen["rows"][0]["matched_signs"]==[30]
assert screen["rows"][0]["certificate_mask"] is None
assert all(row["certificate_mask"] is not None and not row["matched_signs"]
           for row in screen["rows"][1:])
assert box["status"]=="COMPLETE_CODE_BOX_AUDIT" and box["boxes_completed"]==9
assert all(row["variation_rank"]==41 and row["first_full_rank_root_count"]==3
           and row["single_coordinate_certificate"] is False for row in box["rows"])
assert box["rows"][0]["group_hits"]==[[0,30]]
assert box["rows"][0]["sign_family_certificates"]==31
assert all(row["group_hits"]==[] and row["sign_family_certificates"]==32
           for row in box["rows"][1:])
assert aud["status"]=="PASS_INDEPENDENT_SOURCE_AND_GROUP_AUDIT"
assert aud["source_states_rebuilt"]==400
assert aud["sign_assignments_replayed"]==1056
assert aud["code_box_assignments_replayed"]==9216
assert aud["positive_sign_hits"]==[30] and aud["positive_box_hits"]==[[0,30]]
assert columns["status"]=="PASS_INDEPENDENT_COLUMN_AUDIT"
assert columns["source_states_checked"]==400
assert columns["source_codes_checked"]==156
assert columns["sign_families_checked"]==33 and columns["code_boxes_checked"]==9

for prefix,protocol_name,result_name in (
    ("", "run_protocol.json", "result.json"),
    ("code_box_", "code_box_run_protocol.json", "code_box_result.json"),
    ("audit_", "audit_protocol.json", "audit_result.json"),
    ("columns_", "columns_protocol.json", "columns_result.json")):
    receipt=read(prefix+"receipt.json" if prefix else "receipt.json")
    protocol=read(protocol_name)
    assert receipt["status"]=="COMPLETE" and receipt["exit_code"]==0
    assert receipt["stop_reason"] is None and receipt["monitor_error"] is None
    assert receipt["command"][0]=="/Volumes/SSD990/cryptanalysis/sage"
    assert receipt["wall_seconds"]<protocol["wall_cap_seconds"]==120
    assert receipt["sampled_peak_combined_rss_bytes"]<protocol["rss_cap_bytes"]==4294967296
    assert receipt["protocol_sha256"]==sha(HERE/protocol_name)
    assert receipt["result_sha256"]==sha(HERE/result_name)
    stdout_name=(prefix+"run.stdout" if prefix else "run.stdout")
    stderr_name=(prefix+"run.stderr" if prefix else "run.stderr")
    # Code-box, audit, and column supervisors use their own fixed stream names.
    if prefix=="code_box_":
        stdout_name,stderr_name="code_box.stdout","code_box.stderr"
    elif prefix=="audit_":
        stdout_name,stderr_name="audit.stdout","audit.stderr"
    elif prefix=="columns_":
        stdout_name,stderr_name="columns.stdout","columns.stderr"
    assert receipt["stdout_sha256"]==sha(HERE/stdout_name)
    assert receipt["stderr_sha256"]==sha(HERE/stderr_name)
    assert (HERE/stderr_name).read_bytes()==b""

for name,protocol in (("result.json","run_protocol.json"),
                      ("code_box_result.json","code_box_run_protocol.json"),
                      ("audit_result.json","audit_protocol.json"),
                      ("columns_result.json","columns_protocol.json")):
    result=read(name)
    assert result["protocol_sha256"]==sha(HERE/protocol)
    assert result["candidate_id"] is None
lean_source=(HERE/"SignQuadratic.lean").read_text()
assert "sorry" not in lean_source and "admit" not in lean_source
assert "axiom " not in lean_source
assert (HERE/"lean.stderr").read_bytes()==b""
lean_output=(HERE/"lean.stdout").read_text()
assert "sorryAx" not in lean_output
assert "SignQuadratic.pair_coefficient" in lean_output
assert "SignQuadratic.certificate_nonzero" in lean_output
assert (HERE/"lean_attempt1.stderr").read_bytes()==b""
assert "error:" in (HERE/"lean_attempt1.stdout").read_text()
terminal={"status":"PASS_SIGN_QUADRATIC_TERMINAL_AUDIT","candidate_id":None,
          "curve_id":panel["curve_id"],
          "sign_families_certified":32,
          "larger_boxes_full_rank":9,
          "larger_boxes_first_full_rank_root_count":3,
          "source_states_independently_rebuilt":400,
          "assignments_independently_replayed":1056+9216,
          "protocol_sha256":sha(HERE/"terminal_protocol.json"),
          "verifier_sha256":sha(Path(__file__))}
(HERE/"terminal_result.json").write_text(json.dumps(terminal,indent=2,sort_keys=True)+"\n")
print(json.dumps(terminal,sort_keys=True))
