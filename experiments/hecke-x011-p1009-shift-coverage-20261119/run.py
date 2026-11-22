"""Exact first-hit distances to the frozen prepared table."""

import json
import sys
from collections import Counter
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "hecke-x011-p1009-one-target-20261119"))
from common import N, G, mul  # noqa: E402

protocol = json.loads((HERE / "protocol.json").read_text())
for name in ("source_prepared_logs", "source_public_point"):
    path = HERE / protocol[name]
    assert sha256(path.read_bytes()).hexdigest() == protocol[name + "_sha256"]
logs = json.loads((HERE / protocol["source_prepared_logs"]).read_text())
assert len(logs) == len(set(logs)) == 84
prepared = set(logs)
public = tuple(json.loads((HERE / protocol["source_public_point"]).read_text())["point"])
assert list(public) == protocol["public_target_point"]
distances = []
for x in range(N):
    distance = next(k for k in range(N) if (x + k) % N in prepared)
    distances.append(distance)
assert all(d < N for d in distances)
target_log = next(x for x in range(N) if mul(x, G) == public)
hist = Counter(distances)
ordered = sorted(prepared)
gaps = [(ordered[(i + 1) % len(ordered)] - ordered[i]) % N for i in range(len(ordered))]
assert sum(gaps) == N and min(gaps) > 0
assert max(distances) == max(gaps) - 1
assert sum(distances) == sum(g * (g - 1) // 2 for g in gaps)
gap_hist = Counter(gaps)
out = {
    "schema": "x011-p1009-shift-coverage-result-v1",
    "status": "complete",
    "group_order": N,
    "prepared_points": len(prepared),
    "direct_hits": hist[0],
    "max_shift": max(distances),
    "mean_shift_numerator": sum(distances),
    "mean_shift_denominator": N,
    "histogram": {str(k): hist[k] for k in sorted(hist)},
    "cyclic_gap_histogram": {str(k): gap_hist[k] for k in sorted(gap_hist)},
    "max_cyclic_gap": max(gaps),
    "target_log": target_log,
    "target_shift": distances[target_log],
    "target_shift_percentile_le_numerator": sum(d <= distances[target_log] for d in distances),
    "target_shift_percentile_denominator": N,
    "distances_sha256": sha256(json.dumps(distances, separators=(",", ":")).encode()).hexdigest(),
}
(HERE / "distances.json").write_text(json.dumps(distances, separators=(",", ":")) + "\n")
(HERE / "result.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=2))
