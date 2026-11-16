"""Exact first-hit controls for complete Z/7 and three-point Z/101 programs."""
import hashlib
import itertools
import json
from collections import Counter
from fractions import Fraction
from math import factorial
from pathlib import Path

ROOT = Path(__file__).resolve().parent
protocol = json.loads((ROOT / "protocol.json").read_text())
assert protocol["schema"] == "xedni-full-hit-bound-protocol-v1"


def first_hit(points, forms):
    for j in range(len(points)):
        if any(forms[i] != forms[j] and points[i] == points[j]
               for i in range(j)):
            return j
    return None


q = 7
counts7 = Counter()
for w in range(q):
    for labels in itertools.permutations(range(q)):
        plus = labels[1] < labels[w]
        points = (1, w, (1 + w if plus else 1 - w) % q, 0, 0, 2)
        forms = ((0, 1), (1, 0), (1 if plus else -1, 1),
                 (0, 0), (0, 0), (0, 2))
        hit = first_hit(points, forms)
        counts7["survived" if hit is None else str(hit)] += 1
assert sum(counts7.values()) == q * factorial(q)
assert counts7["0"] == 0 and counts7["1"] == factorial(q)
prior_path = ROOT.parent / "xedni-bucket-fiber-partition-20261116" / "result.json"
prior_bytes = prior_path.read_bytes()
assert hashlib.sha256(prior_bytes).hexdigest() == protocol["controls"]["z7_exhaustive"]["prior_result_sha256"]
prior = json.loads(prior_bytes)
for k, row in prior["by_length"].items():
    assert counts7[k] == row["first_hit"]

q = 101
half_factorial = factorial(q) // 2
counts101 = Counter()
case_rows = []
cases101 = 0
for w in range(q):
    for branch in ("minus",) if w == 1 else ("plus", "minus"):
        cases101 += 1
        weight = factorial(q) if w == 1 else half_factorial
        point2 = (1 + w if branch == "plus" else 1 - w) % q
        form2 = (1 if branch == "plus" else -1, 1)
        hit = first_hit((1, w, point2), ((0, 1), (1, 0), form2))
        counts101["survived" if hit is None else str(hit)] += weight
        if hit is not None:
            case_rows.append({"scalar": w, "branch": branch,
                              "first_hit": hit, "encoding_weight": str(weight)})
assert sum(counts101.values()) == q * factorial(q)
assert counts101["0"] == 0
assert counts101["1"] == factorial(q)
assert counts101["2"] == 3 * half_factorial
assert len(case_rows) == 4
total_hit101 = counts101["1"] + counts101["2"]
probability101 = Fraction(total_hit101, q * factorial(q))
assert probability101 == Fraction(5, 202)
lhs101 = (q - 3 * 3) * total_hit101
rhs101 = ((q - 3 * 3) + 3 * 3 * q) * factorial(q)
assert lhs101 <= rhs101

result = {
    "schema": "xedni-full-hit-bound-result-v1",
    "status": "PASS",
    "z7": {"executions": 7 * factorial(7),
           "first_hit_counts": dict(sorted(counts7.items())),
           "total_hit": sum(v for k, v in counts7.items() if k != "survived")},
    "z101": {"executions": str(q * factorial(q)),
             "first_hit_counts": {k: str(v) for k, v in sorted(counts101.items())},
             "hit_probability": f"{probability101.numerator}/{probability101.denominator}",
             "bound_left": str(lhs101), "bound_right": str(rhs101),
             "nonzero_case_rows": case_rows},
}
(ROOT / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": "PASS", "z7_executions": 7 * factorial(7),
                  "z101_cases": cases101,
                  "z101_hit_probability": str(probability101)}, sort_keys=True))
