"""Verify frozen finite rows and the checked theorem build receipt."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
for entry in (root / "SEAL.sha256").read_text().splitlines():
    digest, name = entry.split("  ", 1)
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
result = json.loads((root / "result.json").read_text())
assert result["status"] == "PASS"
assert result["mismatches"] == 0
assert result["stage_cases"] == 141120
assert sum(row["cases"] for row in result["by_stage"].values()) == 141120
assert sum(row.get("event", 0) for row in result["by_stage"].values()) == result["event_rows"]
raw = (root / "stage-hit-rows.jsonl").read_bytes()
assert hashlib.sha256(raw).hexdigest() == result["event_rows_sha256"]
assert len(raw.splitlines()) == result["event_rows"]
for line in raw.splitlines():
    row = json.loads(line)
    assert row["stage"] in (2, 3, 4, 5)
    assert len(row["labels"]) == row["stage"]
    assert sorted(row["encoding"]) == list(range(7))
build = (root / "formal" / "build-output.txt").read_text()
assert "Build completed successfully" in build
assert "sorryAx" not in build
assert "error:" not in build
for name in ("eligible_iff_eval_pattern", "next_hit_iff_candidates",
             "group_pattern_iff_eligible", "group_next_hit_iff_candidates",
             "dlp_stage_hit_iff_eligible_next"):
    assert "'XedniStageHitEquivalence." + name + "' depends on axioms:" in build
source = (root / "formal" / "StageHitEquivalence.lean").read_text()
for banned in ("sorry", "admit", "sorryAx", "native_decide", "axiom "):
    assert banned not in source
print("PASS: 141120 stage cases, 17640 event rows, five Lean axiom receipts")
