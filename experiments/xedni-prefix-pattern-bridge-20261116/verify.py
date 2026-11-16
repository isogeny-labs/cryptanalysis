"""Check sealed proof receipts and repeated-form experiment artifacts."""
import gzip
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
entries = (root / "SEAL.sha256").read_text().splitlines()
for line in entries:
    digest, name = line.split("  ", 1)
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
for name, parent in (
    ("RandomLabelCoupling", "xedni-random-label-coupling-20261116"),
    ("SymbolicCollision", "xedni-symbolic-collision-bound-20261116"),
    ("LabelConditionedCollision", "xedni-label-conditioned-collision-20261116"),
    ("GroupTraceInvariant", "xedni-group-trace-invariant-20261116"),
    ("AdaptiveProgramInvariant", "xedni-adaptive-program-invariant-20261116"),
    ("TranscriptDeterminism", "xedni-transcript-determinism-20261116"),
    ("FirstCollisionLedger", "xedni-first-collision-ledger-20261116"),
):
    path = root / "formal" / (name + ".lean")
    assert path.is_symlink()
    assert path.resolve() == (root.parent / parent / "formal" / (name + ".lean")).resolve()
result = json.loads((root / "result.json").read_text())
audit = json.loads((root / "audit.json").read_text())
assert result["status"] == audit["status"] == "PASS"
assert (result["bucket_count"], result["live_mass"], result["hit_mass"]) == (7, 35280, 5040)
assert (result["eligible_scalars_per_bucket"], result["hit_scalars_per_bucket"],
        result["weight_per_scalar_per_bucket"]) == (7, 1, 720)
assert audit["result_sha256"] == hashlib.sha256((root / "result.json").read_bytes()).hexdigest()
raw = root / "buckets.jsonl.gz"
assert result["buckets_sha256"] == hashlib.sha256(raw.read_bytes()).hexdigest()
with gzip.open(raw, "rt") as stream:
    assert sum(1 for _ in stream) == audit["rows_checked"] == 7
source = (root / "formal/PrefixPatternBridge.lean").read_text()
build = (root / "formal/build-output.txt").read_text()
assert "Build completed successfully (3145 jobs)." in build
names = ("equal_pattern_perm", "equal_pattern_label_event_card_eq",
         "eligible", "eval_eq_iff_form_eq", "eligible_card_lower",
         "nextCandidates", "next_candidates_card_le", "new_eq_mem_candidates",
         "eligible_label_event_card_eq", "prefixFiber",
         "weighted_next_candidate_bound", "weighted_first_hit_bound")
for name in names:
    assert f"#print axioms {name}" in source
    lines = [line for line in build.splitlines() if f"'XedniPrefixPatternBridge.{name}'" in line]
    assert len(lines) == 1, name
    if "depends on axioms:" in lines[0]:
        axioms = lines[0].split("depends on axioms: [", 1)[1].split("]", 1)[0]
        assert set(axioms.split(", ")) <= {"propext", "Classical.choice", "Quot.sound"}, name
    else:
        assert "does not depend on any axioms" in lines[0], name
for banned in ("sorry", "admit", "sorryAx", "native_decide", "axiom "):
    assert banned not in source
print(json.dumps({"schema": "xedni-prefix-pattern-bridge-verify-v1",
                  "status": "PASS", "sealed_files": len(entries),
                  "lean_declarations": len(names)}, sort_keys=True))
