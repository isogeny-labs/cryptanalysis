"""Verify the frozen N41 resultant redundancy evidence."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
cfg = json.loads((HERE / "redundancy_protocol.json").read_text())
for source in cfg["sources"].values():
    assert sha(source["path"]) == source["sha256"], source["path"]
assert sha(HERE / "test_redundancy_sage.py") == cfg["script_sha256"]
result = json.loads((HERE / "redundancy_result.json").read_text())
assert result["protocol_sha256"] == sha(HERE / "redundancy_protocol.json")
assert result["status"] == "RESULTANT_REDUNDANCY_CHECK_COMPLETE"
assert result["resultant_in_ideal"] is True
assert result["remainder_terms"] == []
assert result["base_field"] == "GF(2)"
prior = ROOT / "n41_w9_quadratic_joint_resultant_20261023"
reduction = json.loads((prior / "reduction_result.json").read_text())
assert reduction["status"] == "PASS_N41_SOURCE_QUADRATIC_REDUCTION"
assert reduction["original_terms"] == 23 and reduction["reduced_terms"] == 54
assert len(reduction["rows"]) == 33
assert all(row["original"] == row["reduced"] for row in reduction["rows"])
probe = json.loads((prior / "probe_result.json").read_text())
assert probe["status"] == "COMPLETED_FROZEN_ABBA_PROBE"
assert [row["arm"] for row in probe["arm_results"]] == [
    "explicit_y", "resultant", "resultant", "explicit_y"]
assert all(row["status"] == "INDETERMINATE_CONFLICT_CAP"
           and row["reported_conflicts"] == 20002 for row in probe["arm_results"])
proof = (HERE / "lean_check.txt").read_text()
assert "ResultantRedundancy.joint_resultant_of_existing_links" in proof
assert "[propext, Classical.choice, Quot.sound]" in proof
source = (HERE / "ResultantRedundancy.lean").read_text()
assert "#print axioms joint_resultant_of_existing_links" in source
assert not any(term in source for term in ("sorry", "admit", "sorryAx", "native_decide"))
print("PASS_N41_RESULTANT_REDUNDANCY_ARCHIVE")
