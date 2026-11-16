"""Enumerate first-hit and live-stage identities in a fixed adaptive Z/7 program."""
import gzip
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
protocol = json.loads((ROOT / "protocol.json").read_text())
assert protocol["schema"] == "xedni-first-hit-partition-protocol-v1"
Q = 7
STAGES = tuple(protocol["stages"])
assert STAGES == (1, 2, 3, 4, 5)


def forms(labels):
    fs = [(0, 1), (1, 0)]
    fs.append((1, 1) if labels[0] < labels[1] else (-1, 1))
    fs.extend([(0, 0), (0, 0), (0, 2)])
    return tuple((a % Q, b % Q) for a, b in fs)


def evaluate(f, w):
    return (f[0] * w + f[1]) % Q


def points(w, enc):
    out = [1, w]
    out.append((1 + w) % Q if enc[1] < enc[w] else (1 - w) % Q)
    return tuple(out + [0, 0, 2])


first_counts = Counter()
live_counts = Counter()
hit_counts = Counter()
rows = []
for w in range(Q):
    for enc in itertools.permutations(range(Q)):
        ps = points(w, enc)
        labels = tuple(enc[p] for p in ps)
        fs = forms(labels)
        assert ps == tuple(evaluate(f, w) for f in fs)
        raw = {1: ps[0] == ps[1]}
        staged = {1: w == 1}
        predicted = {1: w == 1}
        assert raw[1] == staged[1]
        for k in range(2, 6):
            old = fs[:k]
            pattern = all((ps[i] == ps[j]) == (old[i] == old[j])
                          for i in range(k) for j in range(i))
            raw[k] = any(old[i] != fs[k] and ps[i] == ps[k]
                         for i in range(k))
            staged[k] = pattern and raw[k]
            eligible = all(evaluate(old[i], w) != evaluate(old[j], w)
                           for i in range(k) for j in range(i) if old[i] != old[j])
            next_root = any(old[i] != fs[k] and
                            evaluate(old[i], w) == evaluate(fs[k], w)
                            for i in range(k))
            predicted[k] = eligible and next_root
            assert staged[k] == predicted[k]
            hit_counts[k] += int(staged[k])
        first_raw = next((k for k in STAGES if raw[k]), None)
        first_staged = next((k for k in STAGES if staged[k]), None)
        first_predicted = next((k for k in STAGES if predicted[k]), None)
        assert first_raw == first_staged == first_predicted
        first_counts[str(first_raw)] += 1
        for k in range(1, 7):
            live = first_staged is None or first_staged >= k
            no_prior_raw = all(not raw[j] for j in STAGES if j < k)
            assert live == no_prior_raw
            live_counts[k] += int(live)
        rows.append({"w": w, "encoding": enc, "first": first_staged})

total = Q * 5040
for k in STAGES:
    assert live_counts[k] == live_counts[k + 1] + first_counts[str(k)]
assert live_counts[1] == total
assert sum(first_counts.values()) == total
assert live_counts[6] == first_counts["None"]

raw_path = ROOT / "first-hit-rows.jsonl.gz"
with raw_path.open("wb") as file:
    with gzip.GzipFile(fileobj=file, mode="wb", mtime=0, filename="") as stream:
        for row in rows:
            stream.write((json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode())
result = {
    "schema": "xedni-first-hit-partition-result-v1", "status": "PASS",
    "executions": total, "stage_predicates": total * 5,
    "mismatches": 0,
    "first_counts": dict(sorted(first_counts.items())),
    "live_counts": {str(k): live_counts[k] for k in range(1, 7)},
    "staged_hit_counts": {str(k): hit_counts[k] for k in range(2, 6)},
    "rows_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
}
(ROOT / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
