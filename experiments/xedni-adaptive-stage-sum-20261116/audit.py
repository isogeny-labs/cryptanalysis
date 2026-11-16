"""Independent algebraic and orbit-count audit of adaptive prefix buckets."""
import gzip
import hashlib
import json
from collections import Counter
from math import factorial
from pathlib import Path

root = Path(__file__).resolve().parent
protocol = json.loads((root / "protocol.json").read_text())
assert protocol["schema"] == "xedni-adaptive-stage-sum-protocol-v2"
assert len(protocol["commands"]) == 4
q = 7
scalars = set(range(q)) - {1}

def val(f, w):
    return (f[0] * w + f[1]) % q

def new_form(k, labels):
    return ([1, 1] if labels[0] < labels[1] else [-1, 1]) if k == 0 else ([0, 2] if k == 3 else [0, 0])

def expected_forms(k, labels):
    fs = [[0, 1], [1, 0]]
    for j in range(k):
        fs.append(new_form(j, labels[:j+2]))
    return fs

raw = root / "buckets.jsonl.gz"
with gzip.open(raw, "rt") as stream:
    rows = [json.loads(line) for line in stream]
assert len(rows) == len({(r["stage"], tuple(r["labels"])) for r in rows})
by_stage = {k: [] for k in range(4)}
for r in rows:
    k = r["stage"]
    labels = r["labels"]
    fs = r["forms"]
    assert fs == expected_forms(k, labels)
    assert r["next_form"] == new_form(k, labels)
    assert len(fs) == len(labels) == k+2
    eligible = set()
    hits = set()
    for w in scalars:
        points = [val(f,w) for f in fs]
        if any((fs[i] != fs[j]) and points[i] == points[j]
               for i in range(len(fs)) for j in range(i)):
            continue
        eligible.add(w)
        nxt = val(r["next_form"],w)
        if any(f != r["next_form"] and x == nxt for f,x in zip(fs,points)):
            hits.add(w)
    assert sorted(eligible) == r["eligible_scalars"]
    assert sorted(hits) == r["hit_scalars"]
    distinct = len({val(f,next(iter(eligible))) for f in fs})
    weight = factorial(q-distinct)
    assert r["weight_per_scalar"] == weight
    assert r["live_by_scalar"] == {str(w):weight for w in sorted(eligible)}
    assert r["hit_by_scalar"] == {str(w):weight for w in sorted(hits)}
    assert r["live_mass"] == len(eligible)*weight
    assert r["hit_mass"] == len(hits)*weight
    assert all((labels[i] == labels[j]) == (fs[i] == fs[j])
               for i in range(len(fs)) for j in range(len(fs)))
    by_stage[k].append(r)
result = json.loads((root / "result.json").read_text())
assert result["schema"] == "xedni-adaptive-stage-sum-result-v2"
assert result["buckets_sha256"] == hashlib.sha256(raw.read_bytes()).hexdigest()
assert result["bucket_count"] == len(rows) == 1932
assert result["initial_mass"] == 6*factorial(7) == 30240
live = result["initial_mass"]
for k, stage in enumerate(result["stages"]):
    assert stage["stage"] == k
    assert stage["bucket_count"] == len(by_stage[k])
    assert stage["live_mass"] == live == sum(r["live_mass"] for r in by_stage[k])
    assert stage["hit_mass"] == sum(r["hit_mass"] for r in by_stage[k])
    live -= stage["hit_mass"]
    assert stage["next_live_mass"] == live
    assert stage["repeated_form_buckets"] == sum(len({tuple(f) for f in r["forms"]}) < len(r["forms"])
                                                 for r in by_stage[k])
assert result["terminal_live_mass"] == live == 12600
assert result["total_hit_mass"] + live == result["initial_mass"]
assert result["stages"][3]["repeated_form_buckets"] == 840
assert all(r["weight_per_scalar"] == 6 for r in by_stage[3])
pilot = json.loads((root / "pilot-result-v1.json").read_text())
assert result["stages"][:3] == pilot["stages"]
audit = {"schema":"xedni-adaptive-stage-sum-audit-v2","status":"PASS",
         "rows_checked":len(rows),"repeated_prefix_rows":len(by_stage[3]),
         "result_sha256":hashlib.sha256((root / "result.json").read_bytes()).hexdigest()}
(root / "audit.json").write_text(json.dumps(audit,sort_keys=True,indent=2)+"\n")
print(json.dumps(audit,sort_keys=True))
