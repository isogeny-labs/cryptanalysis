"""Independent group-table and affine-candidate audit of the replay."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
result = json.loads((ROOT / "result.json").read_text())
assert len(result["rows"]) == 42
for row in result["rows"]:
    a, b = row["labels"]
    # Each fixed pair of visible labels admits 5! encodings for every
    # collision-free scalar w in {0,2,3,4,5,6}.
    candidates = set()
    for w in (0, 2, 3, 4, 5, 6):
        old = (1, w)
        # Compute group output by an explicit 7x7 addition table.
        add = [[(i + j) % 7 for j in range(7)] for i in range(7)]
        next_point = add[old[0]][old[1]] if a < b else add[old[1]][old[1]]
        if next_point == old[0] or next_point == old[1]:
            candidates.add(w)
    assert candidates == ({0} if a < b else {0, 4})
    assert row["attempts"] == 6 * 120
    assert row["group_hits"] == row["symbolic_hits"] == len(candidates) * 120
    assert row["mismatches"] == 0
assert result["scalar_encoding_pairs"] == 30240
assert result["group_hits"] == result["symbolic_hits"] == 7560
assert result["mismatches"] == 0
audit = {"schema": "xedni-group-trace-invariant-audit-v1", "status": "PASS",
         "result_sha256": hashlib.sha256((ROOT / "result.json").read_bytes()).hexdigest(),
         "rows": len(result["rows"])}
(ROOT / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
print(json.dumps(audit, sort_keys=True))
