"""Build exact first-collision bucket and stopping ledgers from frozen rows."""
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from math import factorial
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROGRAM = ROOT.parent / "xedni-adaptive-program-invariant-20261116"
CANDIDATE = ROOT.parent / "xedni-transcript-determinism-20261116"
protocol = json.loads((ROOT / "protocol.json").read_text())
assert hashlib.sha256((PROGRAM / "result.json").read_bytes()).hexdigest() == protocol["parent_program_result_sha256"]
assert hashlib.sha256((CANDIDATE / "candidate-result.json").read_bytes()).hexdigest() == protocol["parent_candidate_result_sha256"]
parent = json.loads((PROGRAM / "result.json").read_text())

buckets = {}
for shard in parent["shards"]:
    path = PROGRAM / shard["path"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == shard["sha256"]
    with gzip.open(path, "rt") as stream:
        for line in stream:
            row = json.loads(line)
            first = row["first_collision_step"]
            for step in (1, 2, 3):
                if first is not None and first < step:
                    continue
                prefix_len = step + 1
                prefix = tuple(row["encoding"][p] for p in row["points"][:prefix_len])
                assert len(set(prefix)) == prefix_len
                key = (step, prefix)
                if key not in buckets:
                    buckets[key] = {"step": step, "labels": list(prefix),
                                    "live": Counter(), "first_hit": Counter()}
                entry = buckets[key]
                entry["live"][row["w"]] += 1
                if first == step:
                    assert any(row["points"][prefix_len] == row["points"][j]
                               and row["forms"][prefix_len] != row["forms"][j]
                               for j in range(prefix_len))
                    entry["first_hit"][row["w"]] += 1

for entry in buckets.values():
    weight = factorial(7 - len(entry["labels"]))
    assert all(count == weight for count in entry["live"].values())
    assert all(count == weight for count in entry["first_hit"].values())
    assert set(entry["first_hit"]) <= set(entry["live"])
    entry["weight"] = weight
    entry["eligible_scalar_count"] = len(entry["live"])
    entry["next_hit_scalar_count"] = len(entry["first_hit"])
    entry["live_mass"] = sum(entry["live"].values())
    entry["first_hit_mass"] = sum(entry["first_hit"].values())
    entry["eligible_scalar_counts"] = dict(sorted(entry.pop("live").items()))
    entry["next_hit_scalar_counts"] = dict(sorted(entry.pop("first_hit").items()))

out = ROOT / "buckets.jsonl.gz"
with out.open("wb") as raw:
    with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as stream:
        for key in sorted(buckets):
            stream.write((json.dumps(buckets[key], sort_keys=True, separators=(",", ":")) + "\n").encode())

stages = []
current = parent["cases"]
for step in (1, 2, 3):
    rows = [value for (k, _), value in buckets.items() if k == step]
    live = sum(x["live_mass"] for x in rows)
    hit = sum(x["first_hit_mass"] for x in rows)
    assert live == current
    d = min(x["eligible_scalar_count"] for x in rows)
    c = max(x["next_hit_scalar_count"] for x in rows)
    assert all(d * x["first_hit_mass"] <= c * x["live_mass"] for x in rows)
    assert d * hit <= c * live
    current -= hit
    stages.append({"step": step, "prefix_length": step + 1,
                   "bucket_count": len(rows), "weight_per_scalar": factorial(6 - step),
                   "live_mass": live, "first_hit_mass": hit, "next_live_mass": current,
                   "min_eligible_scalars": d, "max_next_hit_scalars": c,
                   "bucket_ratio_check": True})
assert sum(x["first_hit_mass"] for x in stages) + current == parent["cases"]
result = {"schema": "xedni-first-collision-ledger-result-v1", "status": "PASS",
          "initial_mass": parent["cases"], "total_first_hit_mass": parent["cases"] - current,
          "terminal_live_mass": current, "bucket_rows": len(buckets),
          "stages": stages, "bucket_rows_sha256": hashlib.sha256(out.read_bytes()).hexdigest()}
(ROOT / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
