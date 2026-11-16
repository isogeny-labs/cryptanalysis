"""Verify sealed random-label coupling proof and exhaustive census."""
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
assert result["encodings"] == 120
assert [r["distinct_label_tuples"] for r in result["rows"]] == [60, 60, 60, 20]
assert len(result["couplings"]) == 2
assert all(c["paired_encodings"] == 120 for c in result["couplings"])

lean = (HERE / "formal/RandomLabelCoupling.lean").read_text()
receipt = (HERE / "formal/build-output.txt").read_text()
assert "Build completed successfully (3138 jobs)." in receipt
theorems = ("relabelEquiv", "injective_trace_label_coupling",
            "label_event_card_eq", "affine_trace_label_event_card_eq")
for theorem in theorems:
    assert f"#print axioms {theorem}" in lean
    assert f"'XedniRandomLabelCoupling.{theorem}' depends on axioms: [propext" in receipt
for bad in ("sorry", "admit", "sorryAx", "native_decide", "axiom "):
    assert bad not in lean
print(json.dumps({"schema": "xedni-random-label-coupling-verify-v1",
                  "status": "PASS", "sealed_files": len(entries),
                  "encodings": 120, "lean_theorems": len(theorems)},
                 sort_keys=True))
