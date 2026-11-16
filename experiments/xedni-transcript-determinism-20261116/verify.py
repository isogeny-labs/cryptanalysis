"""Verify the sealed transcript-determinism theorem and both finite replays."""
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
):
    path = ROOT / "formal" / (name + ".lean")
    assert path.is_symlink()
    assert path.resolve() == (ROOT.parent / parent / "formal" / (name + ".lean")).resolve()
parent = ROOT.parent / "xedni-adaptive-program-invariant-20261116" / "result.json"
protocol = json.loads((ROOT / "protocol.json").read_text())
assert hashlib.sha256(parent.read_bytes()).hexdigest() == protocol["parent_result_sha256"]
amendment = json.loads((ROOT / "candidate-protocol.json").read_text())
assert hashlib.sha256((ROOT / "result.json").read_bytes()).hexdigest() == amendment["parent_transcript_result_sha256"]
assert hashlib.sha256((ROOT / "transcripts.jsonl.gz").read_bytes()).hexdigest() == amendment["parent_transcript_rows_sha256"]
result = json.loads((ROOT / "result.json").read_text())
audit = json.loads((ROOT / "audit.json").read_text())
candidate = json.loads((ROOT / "candidate-result.json").read_text())
candidate_audit = json.loads((ROOT / "candidate-audit.json").read_text())
assert all(x["status"] == "PASS" for x in (result, audit, candidate, candidate_audit))
assert result["cases"] == audit["cases"] == candidate["cases"] == candidate_audit["cases"] == 30240
assert result["distinct_transcripts"] == audit["distinct_transcripts"] == candidate["transcripts"] == candidate_audit["transcripts"] == 4686
assert result["shared_by_multiple_scalars"] == 720
assert result["form_or_command_mismatches"] == candidate["candidate_membership_mismatches"] == 0
assert candidate["informative_hit_cases"] == 25920
assert candidate["candidate_size_counts"] == {"3": 21, "4": 60, "5": 1305, "6": 1500, "7": 1800}
assert audit["result_sha256"] == hashlib.sha256((ROOT / "result.json").read_bytes()).hexdigest()
assert candidate_audit["result_sha256"] == hashlib.sha256((ROOT / "candidate-result.json").read_bytes()).hexdigest()
source = (ROOT / "formal/TranscriptDeterminism.lean").read_text()
build = (ROOT / "formal/build-output.txt").read_text()
assert "Build completed successfully (3143 jobs)." in build
names = ("programLe", "prefixLabels", "formsFromTranscript", "runGroup_prefix",
         "runForms_eq_transcript", "dlp_forms_from_transcript", "dlp_group_from_transcript",
         "dlp_collision_mem_candidates", "transcript_candidate_bound")
for name in names:
    assert f"#print axioms {name}" in source
    matches = [line for line in build.splitlines()
               if f"'XedniTranscriptDeterminism.{name}'" in line]
    assert len(matches) == 1, name
    receipt = matches[0]
    if "depends on axioms:" in receipt:
        listed = receipt.split("depends on axioms: [", 1)[1].split("]", 1)[0]
        assert set(listed.split(", ")) <= {"propext", "Classical.choice", "Quot.sound"}, name
    else:
        assert "does not depend on any axioms" in receipt, name
assert "sorryAx" not in build
for banned in ("sorry", "admit", "sorryAx", "native_decide", "axiom "):
    assert banned not in source
print(json.dumps({"schema": "xedni-transcript-determinism-verify-v1",
                  "status": "PASS", "sealed_files": len(entries),
                  "lean_declarations": len(names)}, sort_keys=True))
