"""Exact group-label fiber arithmetic for frozen Z/101 visible buckets."""
import hashlib
import json
from math import factorial
from pathlib import Path

ROOT = Path(__file__).resolve().parent
protocol = json.loads((ROOT / "protocol.json").read_text())
assert protocol["schema"] == "xedni-group-fiber-bound-protocol-v1"
Q = 101


def forms(labels):
    k = len(labels)
    result = [(0, 1), (1, 0)]
    if k >= 3:
        result.append((1, 1) if labels[0] < labels[1] else (-1, 1))
    if k >= 4:
        result.append((0, 0))
    if k >= 5:
        result.append((0, 0))
    if k >= 6:
        result.append((0, 2))
    return tuple(result)


def value(form, scalar):
    return (form[0] * scalar + form[1]) % Q


def fiber(labels, old, scalar):
    points = tuple(value(f, scalar) for f in old)
    consistent = all((points[i] == points[j]) == (labels[i] == labels[j])
                     for i in range(len(old)) for j in range(i))
    return factorial(Q - len(set(points))) if consistent else 0


def eligible(old, scalar):
    return all(old[i] == old[j] or value(old[i], scalar) != value(old[j], scalar)
               for i in range(len(old)) for j in range(i))


def candidate(old, new, scalar):
    return any(f != new and value(f, scalar) == value(new, scalar) for f in old)


assert hashlib.sha256(
    (ROOT.parent / "xedni-bucket-fiber-partition-20261116" / "result.json").read_bytes()
).hexdigest() == protocol["positive_control"]["sha256"]

rows = []
for k_text, buckets in protocol["buckets"].items():
    k = int(k_text)
    assert 2 <= k <= 5 and Q > k * k
    for labels in buckets:
        labels = tuple(labels)
        assert len(labels) == k
        old = forms(labels)
        new = forms(labels + (0,))[k]
        eligible_scalars = [w for w in range(Q) if eligible(old, w)]
        candidate_scalars = [w for w in eligible_scalars if candidate(old, new, w)]
        weights = [fiber(labels, old, w) for w in eligible_scalars]
        assert len(set(weights)) <= 1, (k, labels, weights)
        eligible_mass = sum(weights)
        candidate_mass = sum(fiber(labels, old, w) for w in candidate_scalars)
        lhs = (Q - k * k) * candidate_mass
        rhs = k * eligible_mass
        assert lhs <= rhs, (k, labels, lhs, rhs)
        rows.append({
            "k": k,
            "labels": labels,
            "eligible_scalars": eligible_scalars,
            "candidate_scalars": candidate_scalars,
            "eligible_fiber_weight": str(weights[0]) if weights else "0",
            "eligible_mass": str(eligible_mass),
            "candidate_mass": str(candidate_mass),
            "left_bound": str(lhs),
            "right_bound": str(rhs),
            "bound_holds": True,
        })

result = {
    "schema": "xedni-group-fiber-bound-result-v1",
    "status": "PASS",
    "group_order": Q,
    "buckets_checked": len(rows),
    "eligible_weight_mismatches": 0,
    "candidate_bound_failures": 0,
    "rows": rows,
}
(ROOT / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps({k: v for k, v in result.items() if k != "rows"}, sort_keys=True))
