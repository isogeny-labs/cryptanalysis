"""Exhaustive stage-hit equivalence check for a fixed adaptive Z/7 program."""
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
protocol = json.loads((ROOT / "protocol.json").read_text())
assert protocol["schema"] == "xedni-stage-hit-equivalence-protocol-v1"
Q = 7
stages = tuple(protocol["stage_lengths"])
assert stages == (2, 3, 4, 5)


def forms(labels):
    fs = [(0, 1), (1, 0)]
    if len(labels) >= 3:
        fs.append((1, 1) if labels[0] < labels[1] else (-1, 1))
    if len(labels) >= 4:
        fs.append((0, 0))
    if len(labels) >= 5:
        fs.append((0, 0))
    if len(labels) >= 6:
        fs.append((0, 2))
    return tuple((a % Q, b % Q) for a, b in fs)


def value(form, w):
    return (form[0] * w + form[1]) % Q


def actual(w, enc):
    points = [1, w]
    points.append((1 + w) % Q if enc[1] < enc[w] else (1 - w) % Q)
    points.extend([0, 0, 2])
    return tuple(points)


counts = {k: Counter() for k in stages}
fiber = Counter()
rows = []
for w in range(Q):
    for enc in itertools.permutations(range(Q)):
        points = actual(w, enc)
        labels = tuple(enc[x] for x in points)
        fs = forms(labels)
        assert tuple(value(f, w) for f in fs) == points
        for k in stages:
            old = fs[:k]
            new = fs[k]
            old_points = points[:k]
            pattern = all((old_points[i] == old_points[j]) == (old[i] == old[j])
                          for i in range(k) for j in range(i))
            hit = any(old[i] != new and old_points[i] == points[k]
                      for i in range(k))
            eligible = all(value(old[i], w) != value(old[j], w)
                           for i in range(k) for j in range(i) if old[i] != old[j])
            roots = any(old[i] != new and value(old[i], w) == value(new, w)
                        for i in range(k))
            observed = pattern and hit
            predicted = eligible and roots
            assert observed == predicted, (w, enc, k, observed, predicted)
            fiber[(k, w, labels[:k])] += 1
            counts[k]["cases"] += 1
            counts[k]["event" if observed else "complement"] += 1
            counts[k]["eligible" if eligible else "ineligible"] += 1
            counts[k]["hit" if hit else "no_hit"] += 1
            if observed:
                rows.append({"stage": k, "scalar": w, "labels": labels[:k],
                             "encoding": enc})

# An independent count uses only the reconstructed scalar trace and the
# number of unused labels; it does not replay the group program.
for (k, w, labels), observed in fiber.items():
    values = tuple(value(f, w) for f in forms(labels))
    consistent = all((labels[i] == labels[j]) == (values[i] == values[j])
                     for i in range(k) for j in range(i))
    remaining = Q - len(set(values))
    expected = 1
    for i in range(2, remaining + 1):
        expected *= i
    assert observed == (expected if consistent else 0)

raw = ROOT / "stage-hit-rows.jsonl"
with raw.open("w") as stream:
    for row in rows:
        stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
result = {
    "schema": "xedni-stage-hit-equivalence-result-v1",
    "status": "PASS", "scalar_count": Q, "encoding_count_per_scalar": 5040,
    "stage_count": len(stages), "stage_cases": Q * 5040 * len(stages),
    "mismatches": 0, "fiber_cells_observed": len(fiber),
    "by_stage": {str(k): dict(sorted(counts[k].items())) for k in stages},
    "event_rows": len(rows),
    "event_rows_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
}
(ROOT / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
