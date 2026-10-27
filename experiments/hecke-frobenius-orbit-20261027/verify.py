"""Independent F_83 point arithmetic and exact rank replay for trace rows."""
import hashlib
import json
import re
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
INPUTS = json.loads((HERE / "inputs.json").read_text())
HASHES = {entry["path"]: entry["sha256"] for entry in INPUTS["inputs"]}


def load(path):
    data = (ROOT / path).read_bytes()
    assert hashlib.sha256(data).hexdigest() == HASHES[path]
    return json.loads(data)


def point(encoded):
    match = re.fullmatch(r"\((\d+) : (\d+) : 1\)", encoded)
    assert match is not None
    return int(match.group(1)), int(match.group(2))


def on_curve(P):
    if P is None:
        return True
    x, y = P
    return (y * y + y - x * x * x + x * x + 10 * x + 20) % 83 == 0


def neg(P):
    return None if P is None else (P[0], (-P[1] - 1) % 83)


def add(P, Q):
    if P is None:
        return Q
    if Q is None:
        return P
    x1, y1 = P
    x2, y2 = Q
    if x1 == x2 and (y1 + y2 + 1) % 83 == 0:
        return None
    if P == Q:
        numerator = 3 * x1 * x1 - 2 * x1 - 10
        denominator = 2 * y1 + 1
    else:
        numerator = y2 - y1
        denominator = x2 - x1
    slope = numerator * pow(denominator % 83, -1, 83) % 83
    intercept = (y1 - slope * x1) % 83
    x3 = (slope * slope + 1 - x1 - x2) % 83
    y3 = (-slope * x3 - intercept - 1) % 83
    answer = (x3, y3)
    assert on_curve(answer)
    return answer


def mul(n, P):
    if n < 0:
        return mul(-n, neg(P))
    out = None
    while n:
        if n & 1:
            out = add(out, P)
        P = add(P, P)
        n >>= 1
    return out


def row(raw):
    return {int(i): int(value) for i, value in raw.items() if value}


def rank(rows):
    pivots = {}
    for original in rows:
        values = {i: Fraction(value) for i, value in original.items() if value}
        while values:
            i = min(values)
            if i not in pivots:
                scale = values[i]
                pivots[i] = {j: value / scale for j, value in values.items()}
                break
            scale = values[i]
            for j, value in pivots[i].items():
                values[j] = values.get(j, 0) - scale * value
                if values[j] == 0:
                    del values[j]
    return len(pivots)


old, corrected = map(load, [INPUTS["inputs"][0]["path"], INPUTS["inputs"][1]["path"]])
result = json.loads((HERE / "result.json").read_text())
assert old["column_points"] == corrected["column_points"]
points = list(map(point, old["column_points"]))
assert len(points) == 20 and all(on_curve(P) for P in points)
assert result["degree"] == 5 and result["p"] == 83
assert result["a_l"] == 1
assert [item["source"] for item in result["sources"]] == INPUTS["source_indices"]
base_rows = list(map(row, corrected["relation_rows"]))
accepted = []
statuses = Counter()
patterns = Counter()
for item in result["sources"]:
    source = item["source"]
    statuses[item["status"]] += 1
    pattern = tuple((factor["degree"], factor["multiplicity"]) for factor in item["factor_pattern"])
    patterns[pattern] += 1
    assert sum(degree * multiplicity for degree, multiplicity in pattern) == 6
    assert item["splitting_degree"] == 4
    if item["status"] == "REPEATED_X_UNLIFTED":
        assert not item["squarefree"] and "orbits" not in item
        continue
    assert item["squarefree"]
    assert sum(orbit["size"] for orbit in item["orbits"]) == 6
    trace_sum = None
    class_counts = Counter()
    outside = False
    for orbit in item["orbits"]:
        if orbit["trace_status"] == "IDENTITY":
            assert orbit["trace_coordinates"] is None and orbit["trace_class_index"] is None
            continue
        coords = orbit["trace_coordinates"]
        assert coords is not None and all(coord.isdecimal() for coord in coords)
        trace = tuple(map(int, coords))
        assert on_curve(trace)
        trace_sum = add(trace_sum, trace)
        if orbit["trace_status"] == "IN_CLASS":
            index = orbit["trace_class_index"]
            assert points[index] == trace
            class_counts[index] += 1
        else:
            assert orbit["trace_status"] == "OUTSIDE_CLASS"
            assert trace not in points and orbit["trace_class_index"] is None
            outside = True
    assert trace_sum == mul(result["a_l"], points[source])
    if outside:
        assert item["status"] == "OUTSIDE_CLASS_TRACE" and "row" not in item
    else:
        assert item["status"] == "CLASS_CLOSED"
        class_counts[source] -= result["a_l"]
        expected = {i: v for i, v in class_counts.items() if v}
        assert row(item["row"]) == expected
        total = None
        for i, coefficient in expected.items():
            total = add(total, mul(coefficient, points[i]))
        assert total is None
        accepted.append(expected)
assert dict(statuses) == result["statuses"]
assert patterns == Counter({((1, 1), (1, 1), (4, 1)): 19,
                            ((1, 2), (4, 1)): 1})
assert rank(base_rows) == result["corrected_degree2_rank_qq"] == 10
assert len(accepted) == result["accepted_trace_rows"] == 5
assert rank(base_rows + accepted) == result["rank_with_trace_rows_qq"] == 13
print("FROBENIUS_ORBIT_TRACE_PASS", "closed", len(accepted),
      "rank", rank(base_rows), "->", rank(base_rows + accepted),
      "statuses", dict(statuses))
