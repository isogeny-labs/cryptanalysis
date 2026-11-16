"""Verify the sealed adaptive program theorem and complete finite replay."""
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
    ("LabelConditionedCollision", "xedni-label-conditioned-collision-20261116"),
    ("GroupTraceInvariant", "xedni-group-trace-invariant-20261116"),
):
    path = ROOT / "formal" / (name + ".lean")
    assert path.is_symlink()
    assert path.resolve() == (ROOT.parent / parent / "formal" / (name + ".lean")).resolve()
result = json.loads((ROOT / "result.json").read_text())
audit = json.loads((ROOT / "audit.json").read_text())
assert result["status"] == audit["status"] == "PASS"
assert result["cases"] == audit["cases"] == 30240
assert result["commands"] == audit["commands"] == 90720
assert result["invariant_mismatches"] == 0
assert result["first_collision_step_counts"] == {
    "1": 5040, "2": 5040, "3": 15840, "None": 4320}
assert result["operation_counts"] == {"add": 53280, "sub": 37440}
assert audit["result_sha256"] == hashlib.sha256((ROOT / "result.json").read_bytes()).hexdigest()
for shard in result["shards"]:
    assert hashlib.sha256((ROOT / shard["path"]).read_bytes()).hexdigest() == shard["sha256"]
source = (ROOT / "formal/AdaptiveProgramInvariant.lean").read_text()
build = (ROOT / "formal/build-output.txt").read_text()
assert "Build completed successfully (3142 jobs)." in build
names = ("Op", "Program", "formOp", "pointOp", "op_commutes", "runGroup",
         "runForms", "run_invariant", "seedForms", "seedPoints",
         "seed_invariant", "dlp_program_invariant")
for name in names:
    assert f"#print axioms {name}" in source
    assert f"'XedniAdaptiveProgramInvariant.{name}'" in build
for banned in ("sorry", "admit", "sorryAx", "native_decide", "axiom "):
    assert banned not in source
print(json.dumps({"schema": "xedni-adaptive-program-invariant-verify-v1",
                  "status": "PASS", "sealed_files": len(entries),
                  "lean_declarations": len(names)}, sort_keys=True))
