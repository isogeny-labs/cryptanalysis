"""Verify sealed first-hit proof and exhaustive finite records."""
import gzip
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
audit = json.loads((root / "audit.json").read_text())
assert protocol["schema"] == "xedni-first-hit-partition-protocol-v1"
assert result["status"] == audit["status"] == "PASS"
assert result["executions"] == 35280
assert result["stage_predicates"] == 176400
assert audit["checks"] == 211680
assert result["mismatches"] == audit["mismatches"] == 0
assert sum(result["first_counts"].values()) == result["executions"]
assert audit["eligible_counts"] == result["live_counts"]
for k in range(1, 6):
    assert result["live_counts"][str(k)] == (
        result["live_counts"][str(k + 1)] +
        result["first_counts"].get(str(k), 0))
raw = root / "first-hit-rows.jsonl.gz"
assert hashlib.sha256(raw.read_bytes()).hexdigest() == result["rows_sha256"]
with gzip.open(raw, "rt") as rows:
    assert sum(1 for _ in rows) == 35280
source = (root / "formal/FirstHitPartition.lean").read_text()
build = (root / "formal/build-output.txt").read_text()
assert "Build completed successfully (3150 jobs)." in build
for bad in ("sorry", "admit", "sorryAx", "native_decide", "axiom "):
    assert bad not in source
assert "sorryAx" not in build and "error:" not in build
names = re.findall(r"^#print axioms (\w+)$", source, re.M)
assert len(names) >= 18
for name in names:
    prefix = re.escape("'XedniFirstHitPartition." + name + "'")
    matches = re.findall(prefix + r" depends on axioms: \[([^\]]+)\]", build, re.S)
    if matches:
        assert len(matches) == 1, name
        assert {a.strip() for a in matches[0].split(",")} <= {
            "propext", "Classical.choice", "Quot.sound"}, name
    else:
        assert len(re.findall(prefix + r" does not depend on any axioms", build)) == 1, name
print(json.dumps({"status": "PASS", "sealed_files": len(entries),
                  "lean_declarations": len(names), "executions": 35280}, sort_keys=True))
