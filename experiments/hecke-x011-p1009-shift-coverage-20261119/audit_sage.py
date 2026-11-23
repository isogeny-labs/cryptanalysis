"""Independent point-group replay of all 1020 first-hit distances."""

import json
from pathlib import Path
from sage.all import EllipticCurve, GF

HERE = Path(__file__).resolve().parent
result = json.loads((HERE / "result.json").read_text())
distances = json.loads((HERE / "distances.json").read_text())
source = json.loads((HERE.parent / "hecke-x011-p1009-degree2-rank-20261119/result.json").read_text())
E = EllipticCurve(GF(1009), [0, -1, 1, -10, -20])
G = E(2, 155)
fiber = {E(*r["point"]) for r in source["source_records"]}
assert len(fiber) == 84 and E.cardinality() == G.order() == 1020
hist = {}
positions = []
Q = E(0)
for x in range(1020):
    if Q in fiber:
        positions.append(x)
    point = Q
    for k in range(1020):
        if point in fiber:
            break
        point += G
    assert k == distances[x]
    hist[k] = hist.get(k, 0) + 1
    Q += G
assert Q == E(0)
assert {str(k): v for k, v in hist.items()} == result["histogram"]
gaps = [(positions[(i + 1) % len(positions)] - positions[i]) % 1020 for i in range(len(positions))]
gap_hist = {str(g): gaps.count(g) for g in sorted(set(gaps))}
assert gap_hist == result["cyclic_gap_histogram"]
assert max(gaps) == result["max_cyclic_gap"]
assert sum(distances) == result["mean_shift_numerator"]
assert result["target_shift_percentile_le_numerator"] == sum(d <= result["target_shift"] for d in distances)
public = E(75, 527)
assert result["target_log"] * G == public
assert public + result["target_shift"] * G in fiber
audit = {"schema": "x011-p1009-shift-coverage-audit-v1", "status": "verified",
         "points_replayed": 1020, "fiber_size": len(fiber), "max_shift": max(distances),
         "target_shift": result["target_shift"]}
(HERE / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
print(json.dumps(audit, indent=2))
