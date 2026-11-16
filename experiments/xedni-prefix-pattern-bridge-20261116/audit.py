"""Independently audit the repeated-form census by orbit counting."""
import gzip
import hashlib
import json
from math import factorial
from pathlib import Path

root = Path(__file__).resolve().parent
protocol = json.loads((root / "protocol.json").read_text())
assert protocol["old_forms"] == [[0, 1], [0, 1]]
assert protocol["new_form"] == [1, 0]
raw = root / "buckets.jsonl.gz"
with gzip.open(raw, "rt") as stream:
    rows = [json.loads(line) for line in stream]
assert len(rows) == 7
assert [row["labels"] for row in rows] == [[x, x] for x in range(7)]
weight = factorial(6)
for row in rows:
    assert row["by_scalar"] == {str(w): weight for w in range(7)}
    assert row["live"] == 7 * weight
    assert row["hit"] == weight
result = json.loads((root / "result.json").read_text())
assert result["bucket_count"] == len(rows)
assert result["live_mass"] == sum(row["live"] for row in rows)
assert result["hit_mass"] == sum(row["hit"] for row in rows)
assert result["buckets_sha256"] == hashlib.sha256(raw.read_bytes()).hexdigest()
audit = {"schema": "xedni-prefix-pattern-bridge-audit-v1", "status": "PASS",
         "result_sha256": hashlib.sha256((root / "result.json").read_bytes()).hexdigest(),
         "rows_checked": len(rows)}
(root / "audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
print(json.dumps(audit, sort_keys=True))
