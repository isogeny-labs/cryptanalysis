"""Enumerate short zero-sum combinations of saved auxiliary trace points."""
import hashlib
import itertools
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


old, corrected, cancellation, degree5, degree13, repeated13 = [load(entry["path"])
    for entry in INPUTS["inputs"]]
assert old["column_points"] == corrected["column_points"]
points = list(map(point, old["column_points"]))
assert len(points) == 20 and all(on_curve(P) for P in points)
base = list(map(sparse, corrected["relation_rows"]))
base += [sparse(item["row"]) for item in cancellation["closed_rows"] + cancellation["pair_rows"]]
base += [sparse(item["row"]) for item in degree13["sources"] if item["status"] == "CLASS_CLOSED"]
assert rank(base) == rank(base, 5) == 17


def expanded(degree, source, orbits, eigenvalue):
    class_part = Counter()
    outside = []
    for orbit in orbits:
        multiplicity = orbit.get("multiplicity", 1)
        if orbit["trace_status"] == "IN_CLASS":
            class_part[orbit["trace_class_index"]] += multiplicity
        elif orbit["trace_status"] == "OUTSIDE_CLASS":
            coords = tuple(map(int, orbit["trace_coordinates"]))
            assert on_curve(coords)
            outside.extend([coords] * multiplicity)
        else:
            assert orbit["trace_status"] == "IDENTITY"
    class_part[source] -= eigenvalue
    class_part = {i: v for i, v in class_part.items() if v}
    assert len(outside) == 1
    group_sum = outside[0]
    for i, coefficient in class_part.items():
        group_sum = add(group_sum, mul(coefficient, points[i]))
    assert group_sum is None
    return {"degree": degree, "source": source,
            "outside": list(outside[0]), "class_part": class_part}


rows = []
for degree, prior in [(5, degree5), (13, degree13)]:
    for entry in prior["sources"]:
        if entry["status"] == "OUTSIDE_CLASS_TRACE":
            rows.append(expanded(degree, entry["source"], entry["orbits"], prior["a_l"]))
assert repeated13["status"] == "UNIQUE_LIFT" and repeated13["source"] == 19
rows.append(expanded(13, 19, repeated13["candidates"][0]["orbits"], degree13["a_l"]))
rows.sort(key=lambda item: (item["degree"], item["source"]))
assert len(rows) == 29

projections = [mul(INPUTS["cofactor"], P) for P in points]
assert any(P is not None for P in projections)
assert all(mul(5, P) is None for P in projections)
candidate_count_by_support = Counter()
candidates = []
selected = []
selected_rows = []
rank_path = [{"selected": 0, "rank_qq": rank(base), "rank_mod5": rank(base, 5)}]
for support_size in range(1, INPUTS["support_cap"] + 1):
    for indexes in itertools.combinations(range(len(rows)), support_size):
        for tail in itertools.product(INPUTS["coefficients"], repeat=support_size - 1):
            coefficients = (INPUTS["first_coefficient"],) + tail
            auxiliary = None
            for index, coefficient in zip(indexes, coefficients):
                auxiliary = add(auxiliary, mul(coefficient, tuple(rows[index]["outside"])))
            if auxiliary is not None:
                continue
            combined = Counter()
            for index, coefficient in zip(indexes, coefficients):
                for column, value in rows[index]["class_part"].items():
                    combined[column] += coefficient * value
            combined = {i: int(v) for i, v in combined.items() if v}
            group_sum = None
            projection_sum = None
            for i, coefficient in combined.items():
                group_sum = add(group_sum, mul(coefficient, points[i]))
                projection_sum = add(projection_sum, mul(coefficient, projections[i]))
            assert group_sum is None and projection_sum is None
            candidate_count_by_support[support_size] += 1
            candidate = {"support": [{"degree": rows[index]["degree"],
                                       "source": rows[index]["source"],
                                       "coefficient": coefficient}
                                      for index, coefficient in zip(indexes, coefficients)],
                         "row": {str(i): v for i, v in sorted(combined.items())}}
            candidate_index = len(candidates)
            candidates.append(candidate)
            if rank(base + selected_rows + [combined], 5) > rank_path[-1]["rank_mod5"]:
                selected.append(candidate_index)
                selected_rows.append(combined)
                rank_path.append({"selected": len(selected),
                                  "candidate_index": candidate_index,
                                  "rank_qq": rank(base + selected_rows),
                                  "rank_mod5": rank(base + selected_rows, 5)})

output = {"schema": "hecke-trace-short-relations-v1", "p": 83,
          "subgroup_modulus": 5, "points": len(points), "expanded_rows": [
              {"degree": item["degree"], "source": item["source"],
               "outside": item["outside"],
               "class_part": {str(i): v for i, v in sorted(item["class_part"].items())}}
              for item in rows],
          "candidate_count_by_support": {str(k): v for k, v in sorted(candidate_count_by_support.items())},
          "candidates": candidates, "selected_candidate_indices": selected,
          "rank_path": rank_path,
          "nonzero_projection_indices": [i for i, P in enumerate(projections) if P is not None],
          "base_rank_qq": rank(base), "base_rank_mod5": rank(base, 5),
          "final_rank_qq": rank(base + selected_rows),
          "final_rank_mod5": rank(base + selected_rows, 5),
          "full_relation_rank_ceiling_mod5": 19}
(HERE / "result.json").write_text(json.dumps(output, sort_keys=True, indent=2) + "\n")
print(json.dumps({"expanded_rows": len(rows), "candidate_count_by_support": output["candidate_count_by_support"],
                  "selected": len(selected), "rank_path": rank_path,
                  "nonzero_projection_indices": output["nonzero_projection_indices"]}, sort_keys=True))
