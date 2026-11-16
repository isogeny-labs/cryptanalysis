"""Verify the sealed fresh-oracle-step theorem and exhaustive transition."""
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

dependency = HERE / "formal/RandomLabelCoupling.lean"
assert dependency.is_symlink()
assert dependency.resolve() == (
    HERE.parent / "xedni-random-label-coupling-20261116/formal/RandomLabelCoupling.lean"
).resolve()
result = json.loads((HERE / "result.json").read_text())
audit = json.loads((HERE / "audit.json").read_text())
assert result["status"] == audit["status"] == "PASS"
assert audit["result_sha256"] == hashlib.sha256((HERE / "result.json").read_bytes()).hexdigest()
assert result["encodings"] == result["paired_encodings"] == 120
assert result["tuple_counts"] == {
    "initial_x": 60, "initial_y": 60,
    "fresh_x": 120, "fresh_y": 120,
    "boundary_x": 120, "boundary_y": 60,
}
lean = (HERE / "formal/OracleStep.lean").read_text()
receipt = (HERE / "formal/build-output.txt").read_text()
assert "Build completed successfully (3139 jobs)." in receipt
theorems = ("fresh_snoc_injective", "fresh_oracle_step_coupling",
            "fresh_oracle_step_event_count", "fresh_add_oracle_step")
for theorem in theorems:
    assert f"#print axioms {theorem}" in lean
    assert f"'XedniRandomLabelOracleStep.{theorem}' depends on axioms: [propext" in receipt
for bad in ("sorry", "admit", "sorryAx", "native_decide", "axiom "):
    assert bad not in lean
print(json.dumps({"schema": "xedni-random-label-oracle-step-verify-v1",
                  "status": "PASS", "sealed_files": len(entries),
                  "encodings": 120, "lean_theorems": len(theorems)},
                 sort_keys=True))
