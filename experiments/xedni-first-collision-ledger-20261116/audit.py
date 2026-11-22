"""Independently recompute every stage and bucket from the frozen replay."""
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from math import factorial
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent / "xedni-adaptive-program-invariant-20261116"
result = json.loads((ROOT / "result.json").read_text())
path = ROOT / "buckets.jsonl.gz"
assert hashlib.sha256(path.read_bytes()).hexdigest() == result["bucket_rows_sha256"]
with gzip.open(path, "rt") as stream:
    saved = {(item["step"], tuple(item["labels"])): item
             for item in map(json.loads, stream)}
actual = defaultdict(lambda: {"live": Counter(), "hit": Counter()})
for shard in sorted((PARENT / "rows").glob("w*.jsonl.gz")):
    with gzip.open(shard, "rt") as stream:
        for line in stream:
            row = json.loads(line)
            points = row["points"]
            forms = row["forms"]
            first = None
            for stage in range(1, 4):
                position = stage + 1
                if points[position] in points[:position] and first is None:
                    first = stage
                    assert any(points[position] == points[j] and forms[position] != forms[j]
                               for j in range(position))
            assert first == row["first_collision_step"]
            for stage in range(1, 4):
                if first is not None and first < stage:
                    break
                prefix = tuple(row["encoding"][p] for p in points[:stage + 1])
                key = (stage, prefix)
                actual[key]["live"][row["w"]] += 1
                if first == stage:
                    actual[key]["hit"][row["w"]] += 1
assert set(saved) == set(actual)
for key, counts in actual.items():
    row = saved[key]
    weight = factorial(7 - len(key[1]))
    assert row["weight"] == weight
    assert row["eligible_scalar_counts"] == {
        str(k): v for k, v in sorted(counts["live"].items())}
    assert row["next_hit_scalar_counts"] == {
        str(k): v for k, v in sorted(counts["hit"].items())}
    assert all(x == weight for x in counts["live"].values())
    assert all(x == weight for x in counts["hit"].values())
    assert row["live_mass"] == sum(counts["live"].values())
    assert row["first_hit_mass"] == sum(counts["hit"].values())
initial = result["initial_mass"]
for stage in result["stages"]:
    rows = [v for (k, _), v in saved.items() if k == stage["step"]]
    assert stage["live_mass"] == initial == sum(x["live_mass"] for x in rows)
    assert stage["first_hit_mass"] == sum(x["first_hit_mass"] for x in rows)
    assert stage["min_eligible_scalars"] == min(x["eligible_scalar_count"] for x in rows)
    assert stage["max_next_hit_scalars"] == max(x["next_hit_scalar_count"] for x in rows)
    assert stage["min_eligible_scalars"] * stage["first_hit_mass"] <= (
        stage["max_next_hit_scalars"] * stage["live_mass"])
    initial -= stage["first_hit_mass"]
    assert initial == stage["next_live_mass"]
assert result["initial_mass"] == result["total_first_hit_mass"] + result["terminal_live_mass"]
assert result["terminal_live_mass"] == initial
audit = {"schema": "xedni-first-collision-ledger-audit-v1", "status": "PASS",
         "bucket_rows": len(saved), "result_sha256": hashlib.sha256((ROOT / "result.json").read_bytes()).hexdigest()}
(ROOT / "audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
print(json.dumps(audit, sort_keys=True))
