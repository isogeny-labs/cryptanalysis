"""Independent integer/rational tangent admission replay on frozen rows."""
import hashlib
import json
import math
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
protocol = json.loads((HERE / "protocol.json").read_text())
source = ROOT / "xedni-vector-shift-lift-search-20261116" / "rows.jsonl"
assert hashlib.sha256(source.read_bytes()).hexdigest() == protocol["source_rows_sha256"]
counts = Counter()
by_field = {}
exceptions = []


def square_condition(points):
    (x, y), (u, v) = [[Fraction(z) for z in pair] for pair in points]
    return (y + v) ** 2 == (x - u) ** 2 * (2*x + u)


for number, line in enumerate(source.open(), start=1):
    row = json.loads(line)
    if row["kind"] in ("positive_control", "negative_control"):
        condition = square_condition(row["rational_points"])
        expected = row["kind"] == "positive_control"
        assert condition == expected == row["rational_relation"]
        counts[row["kind"]] += 1
        continue
    if row["vector"] != protocol["selected_vector"]:
        continue
    counts["candidate_attempts"] += 1
    p = row["field_prime"]
    field = by_field.setdefault(str(p), Counter())
    field["attempts"] += 1
    status = row["status"]
    counts[f"status:{status}"] += 1
    field[f"status:{status}"] += 1
    if row["public_relation_diagnostic"]:
        counts["public_relation_attempts"] += 1
        field["public_relation_attempts"] += 1
    if row["lifted_points"][0][0] == row["lifted_points"][1][0]:
        assert status == "same_x"
        counts["same_x"] += 1
        continue
    (x, y), (u, v) = row["lifted_points"]
    square_target = 2*x + u
    is_integer_square = square_target >= 0 and math.isqrt(square_target) ** 2 == square_target
    is_integral_slope = (y + v) % (x - u) == 0
    if is_integer_square:
        counts["integer_square_target"] += 1
        field["integer_square_target"] += 1
    if is_integral_slope:
        counts["integral_chord_slope"] += 1
        field["integral_chord_slope"] += 1
    if is_integer_square and is_integral_slope:
        counts["both_necessary_conditions"] += 1
        field["both_necessary_conditions"] += 1
    if y == 0:
        counts["zero_first_y"] += 1
    condition = square_condition(row["lifted_points"])
    if condition:
        counts["square_condition"] += 1
        field["square_condition"] += 1
        if not row["public_relation_diagnostic"]:
            exceptions.append({"row": number, "reason": "square_without_public_relation"})
    if row["rational_relation"] is not None:
        counts["admitted_curve"] += 1
        field["admitted_curve"] += 1
        if condition != row["rational_relation"]:
            exceptions.append({"row": number, "reason": "criterion_disagrees_with_group_law"})

assert not exceptions, exceptions[:5]
assert counts["candidate_attempts"] == 8*4*16*4
assert counts["positive_control"] == counts["negative_control"] == 8
result = {"schema": "xedni-tangent-admission-result-v1", "status": "PASS",
          "source_rows_sha256": protocol["source_rows_sha256"],
          "protocol_sha256": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest(),
          "counts": dict(sorted(counts.items())),
          "by_field": {p: dict(sorted(c.items())) for p, c in sorted(by_field.items(), key=lambda pc: int(pc[0]))},
          "exceptions": exceptions}
(HERE / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, indent=2, sort_keys=True))
