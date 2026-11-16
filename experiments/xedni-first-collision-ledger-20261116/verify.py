"""Verify sealed first-collision ledger theorem and full bucket replay."""
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
    ("AdaptiveProgramInvariant", "xedni-adaptive-program-invariant-20261116"),
    ("TranscriptDeterminism", "xedni-transcript-determinism-20261116"),
):
    path = ROOT / "formal" / (name + ".lean")
    assert path.is_symlink()
    assert path.resolve() == (ROOT.parent / parent / "formal" / (name + ".lean")).resolve()
protocol = json.loads((ROOT / "protocol.json").read_text())
program = ROOT.parent / "xedni-adaptive-program-invariant-20261116" / "result.json"
candidate = ROOT.parent / "xedni-transcript-determinism-20261116" / "candidate-result.json"
assert hashlib.sha256(program.read_bytes()).hexdigest() == protocol["parent_program_result_sha256"]
assert hashlib.sha256(candidate.read_bytes()).hexdigest() == protocol["parent_candidate_result_sha256"]
result = json.loads((ROOT / "result.json").read_text())
audit = json.loads((ROOT / "audit.json").read_text())
assert result["status"] == audit["status"] == "PASS"
assert result["initial_mass"] == 30240
assert result["total_first_hit_mass"] == 25920
assert result["terminal_live_mass"] == 4320
assert result["bucket_rows"] == audit["bucket_rows"] == 1092
assert [x["bucket_count"] for x in result["stages"]] == [42, 210, 840]
assert [x["weight_per_scalar"] for x in result["stages"]] == [120, 24, 6]
assert [x["first_hit_mass"] for x in result["stages"]] == [5040, 5040, 15840]
assert [x["min_eligible_scalars"] for x in result["stages"]] == [6, 5, 4]
assert [x["max_next_hit_scalars"] for x in result["stages"]] == [1, 1, 4]
assert audit["result_sha256"] == hashlib.sha256((ROOT / "result.json").read_bytes()).hexdigest()
assert result["bucket_rows_sha256"] == hashlib.sha256((ROOT / "buckets.jsonl.gz").read_bytes()).hexdigest()
source = (ROOT / "formal/FirstCollisionLedger.lean").read_text()
build = (ROOT / "formal/build-output.txt").read_text()
assert "Build completed successfully (3144 jobs)." in build
names = ("live_le_initial", "first_hit_mass_identity", "first_hit_total_bound",
         "uniform_bucket_count_bound", "conditional_square_over_gap")
for name in names:
    assert f"#print axioms {name}" in source
    lines = [line for line in build.splitlines()
             if f"'XedniFirstCollisionLedger.{name}'" in line]
    assert len(lines) == 1, name
    if "depends on axioms:" in lines[0]:
        listed = lines[0].split("depends on axioms: [", 1)[1].split("]", 1)[0]
        assert set(listed.split(", ")) <= {"propext", "Classical.choice", "Quot.sound"}, name
    else:
        assert "does not depend on any axioms" in lines[0], name
assert "sorryAx" not in build
for bad in ("sorry", "admit", "sorryAx", "native_decide", "axiom "):
    assert bad not in source
print(json.dumps({"schema": "xedni-first-collision-ledger-verify-v1",
                  "status": "PASS", "sealed_files": len(entries),
                  "lean_declarations": len(names)}, sort_keys=True))
