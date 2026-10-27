"""Independent F_83 arithmetic and rank audit of source-19 lift."""
import hashlib
import json
import re
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
        numerator, denominator = 3 * x1 * x1 - 2 * x1 - 10, 2 * y1 + 1
    else:
        numerator, denominator = y2 - y1, x2 - x1
    slope = numerator * pow(denominator % 83, -1, 83) % 83
    intercept = (y1 - slope * x1) % 83
    x3 = (slope * slope + 1 - x1 - x2) % 83
    y3 = (-slope * x3 - intercept - 1) % 83
    answer = x3, y3
    assert on_curve(answer)
    return answer


def mul(n, P):
    if n < 0:
        return mul(-n, neg(P))
    result = None
    while n:
        if n & 1:
            result = add(result, P)
        P = add(P, P)
        n >>= 1
    return result


def sparse(raw):
    return {int(i): int(value) for i, value in raw.items() if value}


def rank(rows, modulus=None):
    pivots = {}
    for original in rows:
        values = {i: (Fraction(v) if modulus is None else v % modulus)
                  for i, v in original.items() if v}
        values = {i: v for i, v in values.items() if v}
        while values:
            i = min(values)
            if i not in pivots:
                scale = 1 / values[i] if modulus is None else pow(values[i], -1, modulus)
                pivots[i] = {j: (v * scale if modulus is None else v * scale % modulus)
                             for j, v in values.items()}
                break
            scale = values[i]
            for j, v in pivots[i].items():
                values[j] = values.get(j, 0) - scale * v
                if modulus is not None:
                    values[j] %= modulus
                if values[j] == 0:
                    del values[j]
    return len(pivots)


old, corrected, cancellation, prior13, prior5 = [load(entry["path"])
    for entry in INPUTS["inputs"][:5]]
result = json.loads((HERE / "lift-result.json").read_text())
assert old["column_points"] == corrected["column_points"]
points = list(map(point, old["column_points"]))
assert all(on_curve(P) for P in points)
assert result["status"] == "UNIQUE_LIFT" and result["candidate_count"] == 1
assert result["source"] == INPUTS["source"] == 19
assert result["factor_pattern"] == [{"degree": 1, "multiplicity": 2},
                                     {"degree": 12, "multiplicity": 1}]
assert result["repeated_x"] == "4" and result["repeated_y_sum"] == "82"
ys = [y for y in range(83) if on_curve((4, y))]
assert ys == [38, 44]
assert [str(y) for y in ys] == sorted(result["candidates"][0]["repeated_y_pair"])
assert [(a, b) for a in ys for b in ys if a <= b and (a + b) % 83 == 82] == [(38, 44)]
orbits = result["candidates"][0]["orbits"]
assert sum(item["size"] * item["multiplicity"] for item in orbits) == 14
assert [item["size"] for item in orbits] == [1, 1, 12]
trace_sum = None
outside = []
for item in orbits:
    assert item["multiplicity"] == 1
    coords = item["trace_coordinates"]
    assert coords is not None and all(value.isdecimal() for value in coords)
    trace = tuple(map(int, coords))
    assert on_curve(trace)
    trace_sum = add(trace_sum, trace)
    if item["trace_status"] == "IN_CLASS":
        assert points[item["trace_class_index"]] == trace
    else:
        assert item["trace_status"] == "OUTSIDE_CLASS"
        assert trace not in points and item["trace_class_index"] is None
        outside.append(trace)
assert trace_sum == mul(prior13["a_l"], points[19])
assert outside == [(18, 31)] and result["class_row"] is None
assert add(points[2], points[3]) is None
assert outside[0] == mul(4, points[19])
prior_outside = {tuple(item["trace_coordinates"]) for prior in (prior5, prior13)
                 for source in prior["sources"] for item in source.get("orbits", [])
                 if item["trace_status"] == "OUTSIDE_CLASS"}
assert result["outside_trace_matches_prior"] == []
assert tuple(map(str, outside[0])) not in prior_outside
rows = list(map(sparse, corrected["relation_rows"]))
rows += [sparse(item["row"]) for item in cancellation["closed_rows"] + cancellation["pair_rows"]]
rows += [sparse(item["row"]) for item in prior13["sources"] if item["status"] == "CLASS_CLOSED"]
assert rank(rows) == result["existing_rank_qq"] == result["rank_after_qq"] == 17
assert rank(rows, 5) == result["existing_rank_mod5"] == result["rank_after_mod5"] == 17
print("DEGREE13_REPEATED_PASS", "candidate_count", 1,
      "outside_trace", outside[0], "rank_QQ_F5", 17)
