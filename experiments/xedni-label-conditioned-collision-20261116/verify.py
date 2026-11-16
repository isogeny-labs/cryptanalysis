"""Verify sealed label-conditioned collision proof and census."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
entries = (ROOT / "SEAL.sha256").read_text().splitlines()
for line in entries:
    digest, relative = line.split("  ", 1)
    assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest, relative
for name, parent in (
    ("RandomLabelCoupling", "xedni-random-label-coupling-20261116"),
    ("SymbolicCollision", "xedni-symbolic-collision-bound-20261116"),
):
    path = ROOT / "formal" / (name + ".lean")
    assert path.is_symlink()
    assert path.resolve() == (ROOT.parent / parent / "formal" / (name + ".lean")).resolve()
result = json.loads((ROOT / "result.json").read_text())
audit = json.loads((ROOT / "audit.json").read_text())
assert result["status"] == audit["status"] == "PASS"
assert result["label_pairs"] == audit["label_pairs"] == 42
assert result["encodings_per_scalar_and_label_pair"] == 120
assert result["total_collision_encodings"] == 7560
assert result["total_eligible_encodings"] == 30240
assert audit["result_sha256"] == hashlib.sha256((ROOT / "result.json").read_bytes()).hexdigest()
source = (ROOT / "formal/LabelConditionedCollision.lean").read_text()
build = (ROOT / "formal/build-output.txt").read_text()
assert "Build completed successfully (3140 jobs)." in build
for name in ("fiberCount", "fiber_count_eq", "collision_fiber_mass_le"):
    assert f"#print axioms {name}" in source
    assert f"'XedniLabelConditionedCollision.{name}' depends on axioms: [propext, Classical.choice, Quot.sound]" in build
for banned in ("sorry", "admit", "sorryAx", "native_decide", "axiom "):
    assert banned not in source
print(json.dumps({"schema": "xedni-label-conditioned-collision-verify-v1",
                  "status": "PASS", "sealed_files": len(entries),
                  "lean_declarations": 3}, sort_keys=True))
