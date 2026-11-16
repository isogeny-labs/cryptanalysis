"""Verify the sealed adaptive coupling theorem and complete census."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for line in (ROOT / "SEAL.sha256").read_text().splitlines():
    digest, relative = line.split("  ", 1)
    assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest, relative
for name, parent in (
    ("OracleStep", "xedni-random-label-oracle-step-20261116"),
    ("RandomLabelCoupling", "xedni-random-label-coupling-20261116"),
):
    path = ROOT / "formal" / (name + ".lean")
    assert path.is_symlink()
    assert path.resolve() == (ROOT.parent / parent / "formal" / (name + ".lean")).resolve()
result = json.loads((ROOT / "result.json").read_text())
audit = json.loads((ROOT / "audit.json").read_text())
assert result["status"] == audit["status"] == "PASS"
assert result["encodings_per_trace"] == 5040
assert result["distinct_branch_label_events"] == audit["distinct_events"] == 210
assert audit["result_sha256"] == hashlib.sha256((ROOT / "result.json").read_bytes()).hexdigest()
source = (ROOT / "formal/AdaptiveOracleCoupling.lean").read_text()
build = (ROOT / "formal/build-output.txt").read_text()
assert "Build completed successfully (3140 jobs)." in build
for name in ("branchCount", "fresh_branch_count_eq", "adaptive_fresh_event_count_eq"):
    assert f"#print axioms {name}" in source
    assert f"'XedniAdaptiveOracleCoupling.{name}' depends on axioms: [propext, Classical.choice, Quot.sound]" in build
for banned in ("sorry", "admit", "sorryAx", "native_decide", "axiom "):
    assert banned not in source
print(json.dumps({"schema": "xedni-adaptive-oracle-coupling-verify-v1",
                  "status": "PASS", "lean_declarations": 3}, sort_keys=True))
