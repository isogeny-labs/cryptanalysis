"""Enumerate all scalar-encoding pairs for a repeated-form prefix."""
import gzip
import hashlib
import itertools
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
p = json.loads((ROOT / "protocol.json").read_text())
q = 7
old = p["old_forms"]
new = p["new_form"]
assert old == [[0, 1], [0, 1]] and new == [1, 0]

def evaluate(form, w):
    return (form[0] * w + form[1]) % q

buckets = defaultdict(lambda: {"live": 0, "hit": 0, "by_scalar": defaultdict(int)})
for w in range(q):
    points = tuple(evaluate(f, w) for f in old)
    assert points == (1, 1)
    for perm in itertools.permutations(range(q)):
        labels = tuple(perm[x] for x in points)
        entry = buckets[labels]
        entry["live"] += 1
        entry["by_scalar"][w] += 1
        if evaluate(new, w) == points[0]:
            entry["hit"] += 1
rows = [{"labels": list(k), "live": v["live"], "hit": v["hit"],
         "by_scalar": dict(sorted(v["by_scalar"].items()))}
        for k, v in sorted(buckets.items())]
out = ROOT / "buckets.jsonl.gz"
with out.open("wb") as raw:
    with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as stream:
        for row in rows:
            stream.write((json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode())
result = {"schema": "xedni-prefix-pattern-bridge-result-v1", "status": "PASS",
          "bucket_count": len(rows), "live_mass": sum(x["live"] for x in rows),
          "hit_mass": sum(x["hit"] for x in rows),
          "eligible_scalars_per_bucket": 7, "hit_scalars_per_bucket": 1,
          "weight_per_scalar_per_bucket": 720,
          "buckets_sha256": hashlib.sha256(out.read_bytes()).hexdigest()}
assert result["bucket_count"] == 7
assert result["live_mass"] == 7 * 7 * 720
assert result["hit_mass"] == 7 * 720
assert all(x["live"] == 7 * 720 and x["hit"] == 720 and
           set(x["by_scalar"].values()) == {720} for x in rows)
assert (q - len(old)**2) * result["hit_mass"] <= len(old) * result["live_mass"]
(ROOT / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
