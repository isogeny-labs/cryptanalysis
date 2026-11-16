"""Independent algebraic candidate and permutation-fiber audit."""
import hashlib
import json
from math import factorial
from pathlib import Path

ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT / "result.json").read_text())
assert data["label_pairs"] == 7 * 6
assert data["encodings_per_scalar_and_label_pair"] == factorial(5)
assert data["total_eligible_encodings"] == 6 * factorial(7)
for row in data["rows"]:
    a, b = row["labels"]
    eligible = {0, 2, 3, 4, 5, 6}
    if a < b:
        candidates = {w for w in eligible if (w + 1) % 7 in (1, w)}
        assert candidates == {0}
    else:
        candidates = {w for w in eligible if (2 * w) % 7 in (1, w)}
        assert candidates == {0, 4}
    assert row["eligible_encodings"] == len(eligible) * factorial(5)
    assert row["collision_encodings"] == len(candidates) * factorial(5)
    assert row["collision_scalar_count"] == len(candidates)
assert data["total_collision_encodings"] == (21 + 42) * factorial(5)
out = {"schema": "xedni-label-conditioned-collision-audit-v1",
       "status": "PASS", "result_sha256": hashlib.sha256((ROOT / "result.json").read_bytes()).hexdigest(),
       "label_pairs": len(data["rows"])}
(ROOT / "audit.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
print(json.dumps(out, sort_keys=True))
