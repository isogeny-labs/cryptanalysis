"""Independent F_83 group and rational-rank audit of trace cancellation."""
import hashlib
import json
import re
from collections import Counter, defaultdict
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
    answer = None
    while n:
        if n & 1:
            answer = add(answer, P)
        P = add(P, P)
        n >>= 1
    return answer


def sparse(raw):
    return {int(i): int(value) for i, value in raw.items() if value}


def rank(rows):
    pivots = {}
    for original in rows:
        values = {i: Fraction(v) for i, v in original.items() if v}
        while values:
            i = min(values)
            if i not in pivots:
                scale = values[i]
                pivots[i] = {j: v / scale for j, v in values.items()}
                break
            scale = values[i]
            for j, v in pivots[i].items():
                values[j] = values.get(j, 0) - scale * v
                if values[j] == 0:
                    del values[j]
    return len(pivots)


old, corrected, prior = [load(entry["path"]) for entry in INPUTS["inputs"][:3]]
lift = json.loads((HERE / "lift-result.json").read_text())
result = json.loads((HERE / "result.json").read_text())
assert old["column_points"] == corrected["column_points"]
points = list(map(point, old["column_points"]))
assert len(points) == 20 and all(on_curve(P) for P in points)
assert lift["status"] == "UNIQUE_LIFT" and lift["candidate_count"] == 1
assert lift["source"] == 18 and lift["repeated_x"] == "0"
assert sorted(map(int, lift["candidates"][0]["repeated_y_pair"])) == [40, 42]
assert sum(map(int, lift["candidates"][0]["repeated_y_pair"])) % 83 == int(lift["repeated_y_sum"])
assert all(on_curve((0, y)) for y in (40, 42))


def expanded(source, orbits):
    row = Counter()
    trace_sum = None
    for orbit in orbits:
        multiplicity = orbit.get("multiplicity", 1)
        assert multiplicity > 0
        if orbit["trace_status"] == "IDENTITY":
            assert orbit["trace_coordinates"] is None
            continue
        coords = orbit["trace_coordinates"]
        assert coords is not None and all(value.isdecimal() for value in coords)
        trace = tuple(map(int, coords))
        assert on_curve(trace)
        trace_sum = add(trace_sum, mul(multiplicity, trace))
        if orbit["trace_status"] == "IN_CLASS":
            index = orbit["trace_class_index"]
            assert points[index] == trace
            row[("C", index)] += multiplicity
        else:
            assert orbit["trace_status"] == "OUTSIDE_CLASS"
            assert trace not in points and orbit["trace_class_index"] is None
            row[("O", *trace)] += multiplicity
    assert trace_sum == mul(prior["a_l"], points[source])
    row[("C", source)] -= prior["a_l"]
    return {key: value for key, value in row.items() if value}


rows = {item["source"]: expanded(item["source"], item["orbits"])
        for item in prior["sources"] if "orbits" in item}
rows[18] = expanded(18, lift["candidates"][0]["orbits"])
assert len(rows) == result["source_count"] == 20

closed = []
for item in result["closed_rows"]:
    source = item["source"]
    assert all(key[0] == "C" for key in rows[source])
    row = {key[1]: value for key, value in rows[source].items()}
    assert row == sparse(item["row"])
    closed.append(row)
assert [item["source"] for item in result["closed_rows"]] == [0, 1, 3, 6, 10, 18]

groups = defaultdict(list)
for source, row in sorted(rows.items()):
    outside = {key: v for key, v in row.items() if key[0] == "O"}
    if outside:
        assert len(outside) == 1 and next(iter(outside.values())) == 1
        groups[next(iter(outside))].append(source)
assert [{"point": list(key[1:]), "sources": sources}
        for key, sources in sorted(groups.items())] == result["outside_groups"]
pair_rows = []
for item in result["pair_rows"]:
    first, later = item["first_source"], item["later_source"]
    assert first < later
    outside = next(key for key in rows[first] if key[0] == "O")
    assert outside == next(key for key in rows[later] if key[0] == "O")
    assert list(outside[1:]) == item["outside_trace_point"]
    difference = Counter(rows[later])
    for key, value in rows[first].items():
        difference[key] -= value
    difference = {key: value for key, value in difference.items() if value}
    assert all(key[0] == "C" for key in difference)
    class_row = {key[1]: value for key, value in difference.items()}
    assert class_row == sparse(item["row"])
    group_sum = None
    for i, coefficient in class_row.items():
        group_sum = add(group_sum, mul(coefficient, points[i]))
    assert group_sum is None
    pair_rows.append(class_row)
assert [(item["first_source"], item["later_source"]) for item in result["pair_rows"]] == [
    (8, 19), (2, 4), (7, 9), (11, 15)]
base = list(map(sparse, corrected["relation_rows"]))
assert rank(base) == result["base_rank_qq"] == 10
assert rank(base + closed) == result["rank_after_closed_qq"] == 14
assert rank(base + closed + pair_rows) == result["rank_after_pairs_qq"] == 16
assert [rank(base + (closed + pair_rows)[:i]) for i in range(11)] == result["rank_path_qq"]
print("ORBIT_CANCELLATION_PASS", "closed", len(closed), "pair_rows", len(pair_rows),
      "rank", 10, "->", 14, "->", 16)
