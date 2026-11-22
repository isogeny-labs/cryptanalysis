"""Verify the sealed adaptive trace, independent audit, and Lean proof receipt."""
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
assert result["target_count"] == len(result["rows"]) == 331
assert result["new_form_cap"] == 24
assert result["active_pairs"] == 276
assert result["distinct_candidates"] == result["hit_targets"] == 192
assert result["forms_created"] == audit["forms_created"] == 6299
assert result["group_equality_tests"] == audit["group_equality_tests"] == 61484
assert (HERE / "run.stderr").read_text() == ""

lean = (HERE / "formal/AdaptiveCollision.lean").read_text()
receipt = (HERE / "formal/build-output.txt").read_text()
assert "Build completed successfully (3138 jobs)." in receipt
theorems = ("miss_history_unique", "prehit_strategy_fixed",
            "same_slope_distinct_ne", "public_group_collision_iff",
            "collision_iff_candidate", "adaptive_collision_success_set",
            "adaptive_collision_card_le_pairs", "adaptive_collision_card_le_square")
for theorem in theorems:
    assert f"#print axioms {theorem}" in lean
    assert f"'XedniAdaptiveCollision.{theorem}' depends on axioms: [propext" in receipt
for bad in ("sorry", "admit", "sorryAx", "native_decide", "axiom "):
    assert bad not in lean
print(json.dumps({"schema": "xedni-adaptive-collision-trace-verify-v1", "status": "PASS",
                  "sealed_files": len(entries), "target_count": 331,
                  "hit_targets": 192, "lean_theorems": len(theorems)}, sort_keys=True))
