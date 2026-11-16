"""Check the sealed Lean and exact-arithmetic group-fiber receipts."""
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
assert protocol["schema"] == "xedni-group-fiber-bound-protocol-v1"
assert result["schema"] == "xedni-group-fiber-bound-result-v1"
assert result["status"] == "PASS" and result["buckets_checked"] == 12
assert result["eligible_weight_mismatches"] == 0
assert result["candidate_bound_failures"] == 0
assert len(result["rows"]) == 12
for row in result["rows"]:
    assert row["bound_holds"]
    assert int(row["left_bound"]) <= int(row["right_bound"])
    assert int(row["candidate_mass"]) <= int(row["eligible_mass"])
source = (root / "formal/GroupFiberBound.lean").read_text()
build = (root / "formal/build-output.txt").read_text()
assert "Build completed successfully (3152 jobs)." in build
for bad in ("sorry", "admit", "sorryAx", "native_decide", "axiom "):
    assert bad not in source
assert "sorryAx" not in build and "error:" not in build
names = re.findall(r"^#print axioms (\w+)$", source, re.M)
assert len(names) == 4
for name in names:
    prefix = re.escape("'XedniGroupFiberBound." + name + "'")
    matches = re.findall(prefix + r" depends on axioms: \[([^\]]+)\]", build, re.S)
    if matches:
        assert len(matches) == 1, name
        assert {a.strip() for a in matches[0].split(",")} <= {
            "propext", "Classical.choice", "Quot.sound"}, name
    else:
        assert len(re.findall(prefix + r" does not depend on any axioms", build)) == 1, name
print(json.dumps({"status": "PASS", "sealed_files": len(entries),
                  "lean_declarations": len(names), "buckets": 12}, sort_keys=True))
