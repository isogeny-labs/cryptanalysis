"""Independent replay by direct label assignments and pair-collision checks."""
import hashlib
import itertools
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
receipt = json.loads((ROOT / "result.json").read_text())
counts = {}
for name, (u, v) in {"x": (1, 2), "y": (1, 3)}.items():
    table = defaultdict(int)
    for assignment in itertools.permutations(range(7)):
        a, b = assignment[u], assignment[v]
        i, j = (0, 1) if a < b else (1, 1)
        elements = (u, v)
        z = (elements[i] + elements[j]) % 7
        if z in elements:
            raise AssertionError("unexpected collision")
        table[((i, j), a, b, assignment[z])] += 1
    counts[name] = table
assert counts["x"] == counts["y"]
saved = {((tuple(row["pair"])), *row["labels"]): row["count"]
         for row in receipt["histogram"]}
assert saved == counts["x"]
assert receipt["encodings_per_trace"] == sum(counts["x"].values()) == 5040
out = {"schema": "xedni-adaptive-oracle-coupling-audit-v1", "status": "PASS",
       "result_sha256": hashlib.sha256((ROOT / "result.json").read_bytes()).hexdigest(),
       "distinct_events": len(saved)}
(ROOT / "audit.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(json.dumps(out, sort_keys=True))
