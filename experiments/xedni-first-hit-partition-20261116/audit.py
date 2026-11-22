"""Independently audit live/eligible equality on recorded executions."""
import gzip
import json
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parent
result = json.loads((root / "result.json").read_text())
assert result["status"] == "PASS"
counts = Counter()
checks = 0
with gzip.open(root / "first-hit-rows.jsonl.gz", "rt") as rows:
    for line in rows:
        row = json.loads(line)
        w, enc, first = row["w"], row["encoding"], row["first"]
        assert sorted(enc) == list(range(7))
        branch_plus = enc[1] < enc[w]
        forms = [(0, 1), (1, 0), (1 if branch_plus else -1, 1),
                 (0, 0), (0, 0), (0, 2)]
        for k in range(1, 7):
            eligible = True
            for j in range(k):
                for i in range(j):
                    if forms[i] != forms[j] and (forms[i][0] * w + forms[i][1] -
                                                forms[j][0] * w - forms[j][1]) % 7 == 0:
                        eligible = False
            live = first is None or first >= k
            assert eligible == live, (row, k)
            counts[k] += int(eligible)
            checks += 1
assert checks == 35280 * 6
assert {str(k): counts[k] for k in range(1, 7)} == result["live_counts"]
audit = {"schema": "xedni-first-hit-eligibility-audit-v1", "status": "PASS",
         "checks": checks, "mismatches": 0,
         "eligible_counts": {str(k): counts[k] for k in range(1, 7)}}
(root / "audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
print(json.dumps(audit, sort_keys=True))
