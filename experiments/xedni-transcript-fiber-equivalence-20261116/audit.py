"""Audit all positive fibers by independent orbit assignment enumeration."""
import gzip
import hashlib
import itertools
import json
from math import factorial
from pathlib import Path

root = Path(__file__).resolve().parent
q = 7
expected = {}
for w in range(q):
    for sign in (1,-1):
        points = (1,w,(1+sign*w)%q,0,0,2)
        unique = sorted(set(points))
        weight = factorial(q-len(unique))
        for assigned in itertools.permutations(range(q),len(unique)):
            lab = dict(zip(unique,assigned))
            labels = tuple(lab[x] for x in points)
            if (labels[0] < labels[1]) != (sign == 1):
                continue
            key = (w,labels)
            assert key not in expected
            expected[key] = weight
raw = root / "positive-fibers.jsonl.gz"
with gzip.open(raw,"rt") as stream:
    observed = {}
    for line in stream:
        row = json.loads(line)
        key = (row["w"],tuple(row["labels"]))
        assert key not in observed
        observed[key] = row["encoding_count"]
assert observed == expected
assert sum(expected.values()) == q*factorial(q) == 35280
result = json.loads((root / "result.json").read_text())
assert result["positive_fiber_cells"] == len(expected) == 8820
assert result["zero_fiber_cells"] == q**7-len(expected) == 814723
assert result["positive_rows_sha256"] == hashlib.sha256(raw.read_bytes()).hexdigest()
audit = {"schema":"xedni-transcript-fiber-equivalence-audit-v1","status":"PASS",
         "positive_fibers_checked":len(expected),
         "total_weight":sum(expected.values()),
         "result_sha256":hashlib.sha256((root / "result.json").read_bytes()).hexdigest()}
(root / "audit.json").write_text(json.dumps(audit,sort_keys=True,indent=2)+"\n")
print(json.dumps(audit,sort_keys=True))
