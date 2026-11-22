"""Exhaustively check one fresh and one colliding generic-oracle transition."""
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "protocol.json").read_text())
q = 5
x = tuple(protocol["initial_traces"]["x"])
y = tuple(protocol["initial_traces"]["y"])
assert x == (0, 1, 2) and y == (0, 2, 3)
fresh_x = x + ((x[-1] + x[-1]) % q,)
fresh_y = y + ((y[-1] + y[-1]) % q,)
boundary_x = x + ((x[1] + x[2]) % q,)
boundary_y = y + ((y[1] + y[2]) % q,)
assert (fresh_x, fresh_y) == ((0, 1, 2, 4), (0, 2, 3, 1))
assert (boundary_x, boundary_y) == ((0, 1, 2, 3), (0, 2, 3, 0))
encodings = list(itertools.permutations(range(q)))
assert len(encodings) == 120


def histogram(points):
    counts = Counter(tuple(enc[g] for g in points) for enc in encodings)
    return {",".join(map(str, key)): value for key, value in sorted(counts.items())}


sigma = dict(zip(fresh_x, fresh_y))
sigma.update(zip(sorted(set(range(q)) - set(fresh_x)),
                 sorted(set(range(q)) - set(fresh_y))))
assert sorted(sigma) == sorted(sigma.values()) == list(range(q))
inverse = {target: source for source, target in sigma.items()}
paired_encodings = set()
for enc in encodings:
    partner = tuple(enc[inverse[g]] for g in range(q))
    assert tuple(partner[g] for g in y) == tuple(enc[g] for g in x)
    assert partner[fresh_y[-1]] == enc[fresh_x[-1]]
    paired_encodings.add(partner)
assert len(paired_encodings) == 120

histograms = {name: histogram(points) for name, points in
              (("initial_x", x), ("initial_y", y),
               ("fresh_x", fresh_x), ("fresh_y", fresh_y),
               ("boundary_x", boundary_x), ("boundary_y", boundary_y))}
assert histograms["initial_x"] == histograms["initial_y"]
assert histograms["fresh_x"] == histograms["fresh_y"]
assert histograms["boundary_x"] != histograms["boundary_y"]
result = {"schema": "xedni-random-label-oracle-step-result-v1", "status": "PASS",
          "protocol_sha256": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest(),
          "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          "encodings": len(encodings), "fresh_traces": [fresh_x, fresh_y],
          "boundary_traces": [boundary_x, boundary_y],
          "coupling_permutation": [sigma[i] for i in range(q)],
          "paired_encodings": len(paired_encodings), "histograms": histograms,
          "tuple_counts": {key: len(value) for key, value in histograms.items()}}
print(json.dumps(result, sort_keys=True, indent=2))
