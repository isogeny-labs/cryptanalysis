"""Verify sealed adaptive total-bound proof and arithmetic replay."""
import hashlib
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parent
entries = (root / "SEAL.sha256").read_text().splitlines()
for entry in entries:
    digest, name = entry.split("  ", 1)
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
protocol = json.loads((root / "protocol.json").read_text())
result = json.loads((root / "result.json").read_text())
assert protocol["schema"] == "xedni-adaptive-total-bound-protocol-v1"
assert result["schema"] == "xedni-adaptive-total-bound-result-v1"
assert result["status"] == "PASS"
assert len(result["z7_stage_rows"]) == 4
assert len(result["z101_fixed_bucket_sums"]) == 4
assert result["frozen_z101_buckets"] == 12
for row in result["z7_stage_rows"] + result["z101_fixed_bucket_sums"]:
    assert row["bound_holds"]
    assert int(row["left_bound"]) <= int(row["right_bound"])
source = (root / "formal/AdaptiveTotalBound.lean").read_text()
build = (root / "formal/build-output.txt").read_text()
assert "Build completed successfully (3153 jobs)." in build
for bad in ("sorry", "admit", "sorryAx", "native_decide", "axiom "):
    assert bad not in source
assert "sorryAx" not in build and "error:" not in build
names = re.findall(r"^#print axioms (\w+)$", source, re.M)
assert len(names) == 4
for name in names:
    prefix = re.escape("'XedniAdaptiveTotalBound." + name + "'")
    matches = re.findall(prefix + r" depends on axioms: \[([^\]]+)\]", build, re.S)
    if matches:
        assert len(matches) == 1, name
        assert {a.strip() for a in matches[0].split(",")} <= {
            "propext", "Classical.choice", "Quot.sound"}, name
    else:
        assert len(re.findall(prefix + r" does not depend on any axioms", build)) == 1, name
print(json.dumps({"status": "PASS", "sealed_files": len(entries),
                  "lean_declarations": len(names), "z7_stages": 4,
                  "z101_buckets": 12}, sort_keys=True))
