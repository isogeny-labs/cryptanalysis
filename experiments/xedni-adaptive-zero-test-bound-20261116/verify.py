"""Check the sealed result, the independent audit, and the Lean build receipt."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
entries = (HERE / "SEAL.sha256").read_text().splitlines()
for line in entries:
    digest, relative = line.split("  ", 1)
    path = HERE / relative
    assert path.is_file(), relative
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, relative

result = json.loads((HERE / "result.json").read_text())
audit = json.loads((HERE / "audit.json").read_text())
assert result["status"] == audit["status"] == "PASS"
assert audit["result_sha256"] == hashlib.sha256((HERE / "result.json").read_bytes()).hexdigest()
assert result["hit_targets"] == result["distinct_candidates"] == 15
assert result["hit_targets"] <= result["query_count_cap"]
assert result["group_relation_tests"] == audit["group_relation_tests"] == 5188
assert len(result["rows"]) == result["subgroup_order"] == 331
assert (HERE / "run.stderr").read_text() == ""

lean = (HERE / "formal/AdaptiveZeroTest.lean").read_text()
receipt = (HERE / "formal/build-output.txt").read_text()
assert "Build completed successfully (3138 jobs)." in receipt
for theorem in ("hit_iff_candidate", "group_hit_iff_candidate",
                "adaptive_zero_test_success_set", "adaptive_zero_test_hit_bound"):
    assert f"#print axioms {theorem}" in lean
    assert f"'XedniAdaptiveZeroTest.{theorem}' depends on axioms: [propext, Classical.choice, Quot.sound]" in receipt
for bad in ("sorry", "admit", "sorryAx", "native_decide", "axiom "):
    assert bad not in lean
print(json.dumps({"schema": "xedni-adaptive-zero-test-verify-v1", "status": "PASS",
                  "sealed_files": len(entries), "targets": 331, "hit_targets": 15,
                  "group_relation_tests": 5188, "lean_theorems": 4}, sort_keys=True))
