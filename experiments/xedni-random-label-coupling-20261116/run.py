"""Enumerate every bijective encoding for a finite collision-free trace."""
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "protocol.json").read_text())
q = protocol["group_order"]
assert q == 5
forms = [tuple(x) for x in protocol["forms"]]
encodings = list(itertools.permutations(range(q)))
assert len(encodings) == 120


def trace(w):
    return tuple((a * w + b) % q for a, b in forms)


def histogram(w):
    points = trace(w)
    return Counter(tuple(enc[g] for g in points) for enc in encodings)


def extend_trace_map(x, y):
    assert len(set(x)) == len(x) and len(set(y)) == len(y)
    sigma = dict(zip(x, y))
    missing_x = sorted(set(range(q)) - set(x))
    missing_y = sorted(set(range(q)) - set(y))
    sigma.update(zip(missing_x, missing_y))
    assert sorted(sigma) == sorted(sigma.values()) == list(range(q))
    return tuple(sigma[i] for i in range(q))


base = trace(1)
rows = []
for w in protocol["target_scalars"]:
    points = trace(w)
    hist = histogram(w)
    rows.append({"w": w, "trace": points, "injective": len(set(points)) == len(points),
                 "histogram": {",".join(map(str, k)): v for k, v in sorted(hist.items())},
                 "distinct_label_tuples": len(hist)})

couplings = []
for w in (2, 3):
    target = trace(w)
    sigma = extend_trace_map(base, target)
    inverse = {v: i for i, v in enumerate(sigma)}
    paired = set()
    for enc in encodings:
        new_enc = tuple(enc[inverse[g]] for g in range(q))
        assert tuple(new_enc[g] for g in target) == tuple(enc[g] for g in base)
        paired.add(new_enc)
    assert len(paired) == 120
    couplings.append({"from_w": 1, "to_w": w, "group_permutation": sigma,
                      "paired_encodings": len(paired)})

assert rows[0]["histogram"] == rows[1]["histogram"] == rows[2]["histogram"]
assert rows[0]["histogram"] != rows[3]["histogram"]
result = {"schema": "xedni-random-label-coupling-result-v1", "status": "PASS",
          "protocol_sha256": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest(),
          "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          "encodings": len(encodings), "rows": rows, "couplings": couplings}
print(json.dumps(result, sort_keys=True, indent=2))
