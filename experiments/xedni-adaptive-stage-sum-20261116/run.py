"""Exhaustively test adaptive bucket identities with a known repeated form."""
import gzip
import hashlib
import itertools
import json
from collections import Counter, defaultdict
from math import factorial
from pathlib import Path

ROOT = Path(__file__).resolve().parent
p = json.loads((ROOT / "protocol.json").read_text())
assert p["initial_forms"] == [[0, 1], [1, 0]]
q = 7
scalars = tuple(w for w in range(q) if w != 1)

def evaluate(f, w):
    return (f[0] * w + f[1]) % q

def next_form(stage, labels):
    if stage == 0:
        return (1, 1) if labels[0] < labels[1] else (-1, 1)
    if stage in (1, 2):
        return (0, 0)
    assert stage == 3
    return (0, 2)

def informative_hit(forms, new, w):
    return any(f != new and evaluate(f, w) == evaluate(new, w) for f in forms)

def eligible(forms, w):
    return all(a == b or evaluate(a, w) != evaluate(b, w)
               for i, a in enumerate(forms) for b in forms[i+1:])

buckets = {}
first_hit = Counter()
for w in scalars:
    for enc in itertools.permutations(range(q)):
        forms = [(0, 1), (1, 0)]
        hit_step = None
        for stage in range(4):
            points = [evaluate(f, w) for f in forms]
            labels = tuple(enc[x] for x in points)
            assert eligible(forms, w)
            key = (stage, labels)
            if key not in buckets:
                buckets[key] = {"stage": stage, "labels": list(labels),
                                "forms": [list(f) for f in forms],
                                "live_by_scalar": Counter(), "hit_by_scalar": Counter()}
            row = buckets[key]
            assert row["forms"] == [list(f) for f in forms]
            row["live_by_scalar"][w] += 1
            nxt = next_form(stage, labels)
            if informative_hit(forms, nxt, w):
                row["hit_by_scalar"][w] += 1
                hit_step = stage
                break
            forms.append(nxt)
        first_hit[hit_step] += 1

for row in buckets.values():
    forms = [tuple(f) for f in row["forms"]]
    labels = tuple(row["labels"])
    stage = row["stage"]
    nxt = next_form(stage, labels)
    eligible_scalars = [w for w in scalars if eligible(forms, w)]
    distinct_count = len({evaluate(f, eligible_scalars[0]) for f in forms})
    weight = factorial(q - distinct_count)
    expected_live = {w: weight for w in eligible_scalars}
    expected_hit = {w: weight for w in eligible_scalars
                    if informative_hit(forms, nxt, w)}
    assert dict(row["live_by_scalar"]) == expected_live
    assert dict(row["hit_by_scalar"]) == expected_hit
    assert all((row["labels"][i] == row["labels"][j]) == (forms[i] == forms[j])
               for i in range(len(forms)) for j in range(len(forms)))
    row["next_form"] = list(nxt)
    row["eligible_scalars"] = eligible_scalars
    row["hit_scalars"] = sorted(expected_hit)
    row["weight_per_scalar"] = weight
    row["live_mass"] = sum(row["live_by_scalar"].values())
    row["hit_mass"] = sum(row["hit_by_scalar"].values())
    row["live_by_scalar"] = dict(sorted(row["live_by_scalar"].items()))
    row["hit_by_scalar"] = dict(sorted(row["hit_by_scalar"].items()))

out = ROOT / "buckets.jsonl.gz"
with out.open("wb") as raw:
    with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as stream:
        for key in sorted(buckets):
            stream.write((json.dumps(buckets[key], sort_keys=True, separators=(",", ":")) + "\n").encode())
initial = len(scalars) * factorial(q)
live = initial
stages = []
for k in range(4):
    rows = [r for r in buckets.values() if r["stage"] == k]
    predicted_live = sum(r["live_mass"] for r in rows)
    hit = sum(r["hit_mass"] for r in rows)
    assert predicted_live == live
    assert hit == first_hit[k]
    assert all((q - len(r["forms"])**2) * r["hit_mass"] <=
               len(r["forms"]) * r["live_mass"] for r in rows)
    live -= hit
    stages.append({"stage": k, "old_form_count": k+2,
                   "bucket_count": len(rows), "live_mass": predicted_live,
                   "hit_mass": hit, "next_live_mass": live,
                   "repeated_form_buckets": sum(len(r["forms"]) != len(set(map(tuple, r["forms"]))) for r in rows)})
assert live == first_hit[None]
result = {"schema": "xedni-adaptive-stage-sum-result-v2", "status": "PASS",
          "initial_mass": initial, "total_hit_mass": initial-live,
          "terminal_live_mass": live, "bucket_count": len(buckets),
          "stages": stages, "buckets_sha256": hashlib.sha256(out.read_bytes()).hexdigest()}
(ROOT / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
