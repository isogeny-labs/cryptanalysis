"""Verify the sealed group-trace theorem and full finite replay."""
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
):
    path = ROOT / "formal" / (name + ".lean")
    assert path.is_symlink()
    assert path.resolve() == (ROOT.parent / parent / "formal" / (name + ".lean")).resolve()
protocol = json.loads((ROOT / "protocol.json").read_text())
parent_result = ROOT.parent / "xedni-label-conditioned-collision-20261116" / "result.json"
assert hashlib.sha256(parent_result.read_bytes()).hexdigest() == protocol["parent_result_sha256"]
result = json.loads((ROOT / "result.json").read_text())
audit = json.loads((ROOT / "audit.json").read_text())
assert result["status"] == audit["status"] == "PASS"
assert len(result["rows"]) == audit["rows"] == 42
assert result["scalar_encoding_pairs"] == 30240
assert result["group_hits"] == result["symbolic_hits"] == 7560
assert result["mismatches"] == 0
assert audit["result_sha256"] == hashlib.sha256((ROOT / "result.json").read_bytes()).hexdigest()
source = (ROOT / "formal/GroupTraceInvariant.lean").read_text()
build = (ROOT / "formal/build-output.txt").read_text()
assert "Build completed successfully (3141 jobs)." in build
names = ("groupTrace", "next_group_hit_informative", "next_group_hit_mem_collision_set",
         "groupFiberCount", "actualGroupHits", "actual_group_hit_fiber_mass_le")
for name in names:
    assert f"#print axioms {name}" in source
    assert f"'XedniGroupTraceInvariant.{name}' depends on axioms: [propext" in build
for banned in ("sorry", "admit", "sorryAx", "native_decide", "axiom "):
    assert banned not in source
print(json.dumps({"schema": "xedni-group-trace-invariant-verify-v1",
                  "status": "PASS", "sealed_files": len(entries),
                  "lean_declarations": len(names)}, sort_keys=True))
