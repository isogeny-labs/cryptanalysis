"""Check the seal, independent census, and actual Lean proof receipt."""
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
assert result["targets"] == 331
assert result["stored_forms"] == 36
assert result["active_cross_pairs"] == result["collision_count"] == result["hit_targets"] == 324
assert result["group_equality_tests"] == audit["group_equality_tests"] == 107244
assert len(result["rows"]) == 331
assert (HERE / "run.stderr").read_text() == ""

lean = (HERE / "formal/SymbolicCollision.lean").read_text()
receipt = (HERE / "formal/build-output.txt").read_text()
assert "Build completed successfully (3138 jobs)." in receipt
theorems = ("eval_plus", "eval_scale", "unequal_slope_eq_iff_candidate",
            "same_slope_distinct_ne", "public_group_equality_iff",
            "collision_set_eq_candidates", "collision_card_le_active_pairs",
            "symbolic_collision_bound")
for theorem in theorems:
    assert f"#print axioms {theorem}" in lean
    assert f"'XedniSymbolicCollision.{theorem}' depends on axioms: [propext" in receipt
for bad in ("sorry", "admit", "sorryAx", "native_decide", "axiom "):
    assert bad not in lean
print(json.dumps({"schema": "xedni-symbolic-collision-verify-v1", "status": "PASS",
                  "sealed_files": len(entries), "targets": 331, "hit_targets": 324,
                  "lean_theorems": len(theorems)}, sort_keys=True))
