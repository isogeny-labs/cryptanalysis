"""Check all frozen identities, journal digests, and phase accounting."""
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
assert sha(here / "selection.json") == pre["selection_sha256"] == post_selection["selection_sha256"]
assert sha(here / "run_sage.py") == pre["run_sage_sha256"]
assert sha(here / "index.json") == post_run["index_sha256"]
assert sha(here / "audit.json") == post_audit["audit_sha256"]
assert sha(here / "audit_sage.py") == post_audit["audit_sage_sha256"]
for item in [plan["control_gate_result"], plan["pair_index_reference"], plan["incremental_module"],
             *plan["frozen"].values(), post_run["direct_audit_module"]]:
    assert sha(root / item["path"]) == item["sha256"]
index = json.loads((here / "index.json").read_text())
audit = json.loads((here / "audit.json").read_text())
assert index["status"] == "COMPLETE" and audit["status"] == "PASS"
assert len(index["cases"]) == len(audit["cases"]) == 9
assert index["candidate_id"] is None and index["target_online_ms"] is None
for item, checked in zip(index["cases"], audit["cases"]):
    journal = here / item["journal"]
    summary_path = here / item["summary"]
    assert sha(journal) == item["journal_sha256"]
    assert sha(summary_path) == item["summary_sha256"]
    summary = json.loads(summary_path.read_text())
    records = [json.loads(line) for line in journal.read_text().splitlines() if line]
    assert len(records) == summary["source_count"] == item["source_count"]
    assert (item["p"], item["q"]) == (summary["p"], summary["q"]) == (checked["p"], checked["q"])
    assert summary["collector_wall_ns"] == (summary["lift_sum_ns"] + summary["index_sum_ns"] +
                                               summary["rank_sum_ns"] + summary["checkpoint_sum_ns"] +
                                               summary["loop_overhead_ns"])
    assert summary["candidate_id"] is None and summary["target_online_ms"] is None
assert index["cases"][0]["rank_goal_status"] == "ACHIEVED"
assert all(x["rank_goal_status"] == "BOUNDED_BELOW_GOAL" for x in index["cases"][1:])
print("PASS: nine sealed case journals, independent audit, and exclusive phase sums")
