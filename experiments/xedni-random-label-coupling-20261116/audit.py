"""Independent enumeration of label-tuple counts and trace collisions."""
import hashlib
import itertools
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "protocol.json").read_text())
result = json.loads((HERE / "result.json").read_text())
assert result["protocol_sha256"] == hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest()
assert result["source_sha256"] == hashlib.sha256((HERE / "run.py").read_bytes()).hexdigest()
q = protocol["group_order"]
counts = []
for row in result["rows"]:
    w = row["w"]
    points = tuple((a * w + b) % q for a, b in protocol["forms"])
    assert tuple(row["trace"]) == points
    tally = defaultdict(int)
    for labels in itertools.permutations(range(q)):
        tally[tuple(labels[point] for point in points)] += 1
    encoded = {",".join(map(str, key)): value for key, value in sorted(tally.items())}
    assert row["histogram"] == encoded
    assert row["injective"] == (len(set(points)) == len(points))
    assert row["distinct_label_tuples"] == len(tally)
    assert sum(tally.values()) == 120
    counts.append(len(tally))
assert counts == [60, 60, 60, 20]
assert all(value == 2 for value in result["rows"][0]["histogram"].values())
assert all(value == 6 for value in result["rows"][3]["histogram"].values())
assert result["encodings"] == 120
for coupling in result["couplings"]:
    assert coupling["paired_encodings"] == 120
    assert sorted(coupling["group_permutation"]) == list(range(q))
print(json.dumps({"schema": "xedni-random-label-coupling-audit-v1", "status": "PASS",
                  "result_sha256": hashlib.sha256((HERE / "result.json").read_bytes()).hexdigest(),
                  "encodings": 120, "tuple_counts": counts}, sort_keys=True))
