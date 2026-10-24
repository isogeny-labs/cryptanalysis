"""Read-only terminal audit for the joint right-pair S3 experiment."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE/name).read_text())


join=read("join_rows.json")
build_p=read("build_protocol.json")
build=read("build_result.json")
compact_p=read("compact_build_protocol.json")
compact=read("compact_build_result.json")
probe_p=read("probe_protocol.json")
probe=read("probe_result.json")
compact_p1=read("compact_probe_protocol.json")
failure=read("compact_probe_failure_v1.json")
retry_p=read("compact_retry_protocol.json")
retry=read("compact_retry_result.json")
audit=read("audit_result.json")
assert build["status"]=="PASS_N41_JOINT_RIGHT_S3_CIRCUIT"
assert compact["status"]=="PASS_N41_COMPACT_JOINT_RIGHT_S3_CIRCUIT"
assert audit["status"]=="PASS_INDEPENDENT_GROUP_JOINT_S3_AUDIT"
assert join["positive_count"]==join["target_link_zero_count"]==1
assert len(join["rows"])==audit["checked_rows"]==33
assert audit["complete_relation_rows"]==audit["target_gate_zero_rows"]==1
assert audit["join_rows_sha256"]==sha(HERE/"join_rows.json")
assert audit["build_result_sha256"]==sha(HERE/"build_result.json")
assert audit["compact_build_result_sha256"]==sha(HERE/"compact_build_result.json")
assert audit["auditor_sha256"]==sha(HERE/"audit_sage.py")
for p in (build_p,compact_p,probe_p,compact_p1,retry_p):
    for path,digest in p["sources"].items():
        assert sha(path)==digest,path
for p,r,name in ((build_p,build,"build_protocol.json"),
                 (compact_p,compact,"compact_build_protocol.json"),
                 (probe_p,probe,"probe_protocol.json"),
                 (retry_p,retry,"compact_retry_protocol.json")):
    assert r["protocol_sha256"]==sha(HERE/name)
assert build["formula_sha256"]==sha(HERE/"formula.xcnf")
assert compact["formula_sha256"]==sha(HERE/"compact_formula.xcnf")
assert build["input_wires_sha256"]==sha(HERE/"input_wires.json")
assert compact["input_wires_sha256"]==sha(HERE/"compact_input_wires.json")
assert len(build["controls_checked"])==len(compact["controls_checked"])==33
for circuit in (build,compact):
    assert circuit["controls_checked"][0]["joint_target_zero"]
    assert all(not row["joint_target_zero"] for row in circuit["controls_checked"][1:])
assert failure["status"]=="MONITOR_CONTROL_FAILURE"
assert failure["compact_arm_1_stdout_sha256"]==sha(HERE/"compact_probe_1_compact.stdout")
assert failure["compact_arm_1_exit_code"] is None
assert failure["compact_arm_1_peak_combined_rss_bytes"] is None
assert failure["remaining_arms_status"]=="NOT_RUN"
for dataset,arms in ((probe,["baseline","joint","joint","baseline"]),
                     (retry,["baseline","compact","compact","baseline"])):
    assert dataset["status"]=="COMPLETED_FROZEN_ABBA_PROBE"
    assert [r["arm"] for r in dataset["arm_results"]]==arms
    assert all(r["status"]=="INDETERMINATE_CONFLICT_CAP" and
               r["monitor_error"] is None and r["stop_reason"] is None and
               r["sampled_peak_combined_rss_bytes"]<4*1024**3
               for r in dataset["arm_results"])
    assert dataset["arm_results"][0]["reported_decisions"]==31602
    assert dataset["arm_results"][3]["reported_decisions"]==31602
assert [r["reported_decisions"] for r in probe["arm_results"]]==[31602,34472,34472,31602]
assert [r["reported_decisions"] for r in retry["arm_results"]]==[31602,35089,35089,31602]
assert build["and_gates"]==120495 and compact["and_gates"]==110073
assert compact["and_gates"]<111680
assert 34472>0.9*31602 and 35089>0.9*31602
assert all(retry["arm_results"][i]["wall_seconds"]>
           1.25*retry["arm_results"][j]["wall_seconds"]
           for i,j in ((1,0),(2,3)))
lean=(HERE/"lean.stdout").read_text()
assert (HERE/"lean.stderr").read_text()==""
for theorem in ("regroup_five","joint_target_link_full"):
    assert f"'JointAssociation.{theorem}' does not depend on any axioms" in lean
print(json.dumps({"status":"PASS_TERMINAL_AUDIT",
                  "checked_controls":33,
                  "redundant_joint_decisions":34472,
                  "compact_joint_decisions":35089,
                  "baseline_decisions":31602,
                  "promotion_gate":"FAIL_FIXED_WORK"},sort_keys=True))
