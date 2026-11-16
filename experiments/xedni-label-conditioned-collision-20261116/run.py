"""Complete Z/7 random-label and eligible-scalar collision census."""
import itertools
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
field = range(7)
rows = defaultdict(lambda: {"eligible": 0, "collision": 0, "scalars": set()})
for w in field:
    if w == 1:
        continue
    for enc in itertools.permutations(field):
        a, b = enc[1], enc[w]
        assert a != b
        row = rows[(a, b)]
        row["eligible"] += 1
        row["scalars"].add(w)
        z = (w + 1) % 7 if a < b else (2 * w) % 7
        if z in (1, w):
            row["collision"] += 1
data = []
for (a, b), value in sorted(rows.items()):
    assert value["eligible"] == 6 * 120
    assert value["collision"] in (120, 240)
    assert len(value["scalars"]) == 6
    data.append({"labels": [a, b], "eligible_encodings": value["eligible"],
                 "collision_encodings": value["collision"],
                 "collision_scalar_count": value["collision"] // 120})
out = {"schema": "xedni-label-conditioned-collision-result-v1",
       "status": "PASS", "eligible_scalars": 6,
       "label_pairs": len(data), "encodings_per_scalar_and_label_pair": 120,
       "total_eligible_encodings": sum(x["eligible_encodings"] for x in data),
       "total_collision_encodings": sum(x["collision_encodings"] for x in data),
       "rows": data}
(ROOT / "result.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
print(json.dumps({k: v for k, v in out.items() if k != "rows"}, sort_keys=True))
