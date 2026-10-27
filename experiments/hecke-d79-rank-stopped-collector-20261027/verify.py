"""Check frozen source, result, audit, and accounting receipts."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parent.parent
plan = json.loads((here / "inputs.json").read_text())
pre = json.loads((here / "pre-run.json").read_text())
post_selection = json.loads((here / "post-selection.json").read_text())
post_run = json.loads((here / "post-run.json").read_text())
post_audit = json.loads((here / "post-audit.json").read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert sha(here / "inputs.json") == pre["inputs_sha256"]
assert sha(here / "incremental.py") == pre["incremental_sha256"]
assert sha(here / "run_sage.py") == pre["run_sage_sha256"]
assert sha(here / "selection.json") == pre["selection_sha256"] == post_selection["selection_sha256"]
assert sha(here / "result.json") == post_run["result_sha256"]
assert sha(here / "audit.json") == post_audit["audit_sha256"]
assert sha(here / "audit_sage.py") == post_audit["audit_sage_sha256"]
assert sha(here / "retrospective-validation.json") == post_audit["retrospective_validation_sha256"]
assert sha(here / "validate_existing_sage.py") == post_audit["validate_existing_sage_sha256"]
for item in [plan["control_gate_result"], plan["control_challenge_result"],
             plan["pair_index_reference"], plan["retrospective_inputs"], *plan["frozen"].values()]:
    assert sha(root / item["path"]) == item["sha256"]
result = json.loads((here / "result.json").read_text())
audit = json.loads((here / "audit.json").read_text())
assert result["status"] == "COMPLETE" and audit["status"] == "PASS"
assert len(result["cases"]) == len(audit["cases"]) == 9
assert result["cases"][0]["cohort"] == "known_success_control"
assert result["cases"][0]["rank_goal_status"] == "ACHIEVED"
assert result["cases"][0]["anchored_log_replay"] == "PASS"
for produced, checked in zip(result["cases"], audit["cases"]):
    assert (produced["p"], produced["q"], produced["final_rank_mod_q"]) == (checked["p"], checked["q"], checked["final_rank_mod_q"])
    assert produced["collector_wall_ns"] == checked["collector_wall_ns"]
    assert produced["collector_wall_ns"] == (produced["lift_sum_ns"] + produced["index_sum_ns"] +
                                               produced["rank_sum_ns"] + checked["record_io_and_overhead_ns"])
    assert produced["candidate_id"] is None and produced["target_online_ms"] is None
assert all(c["rank_goal_status"] == "BOUNDED_BELOW_GOAL" for c in result["cases"][1:])
print("PASS: sealed eight-class panel, stopped control, and independent accounting audit")
