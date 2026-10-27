"""Independent checked-Sage enumeration, row-rank, and F_5 kernel audit."""
import hashlib
import itertools
import json
import re
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ, matrix, vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
INPUTS = json.loads((HERE / "inputs.json").read_text())
HASHES = {entry["path"]: entry["sha256"] for entry in INPUTS["inputs"]}


def load(path):
    raw = (ROOT / path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == HASHES[path]
    return json.loads(raw)


def sparse(raw):
    return {int(i): int(value) for i, value in raw.items() if value}


def rank(rows, field):
    return int(matrix(field, [[row.get(i, 0) for i in range(20)] for row in rows]).rank())


old, corrected, cancellation, degree5, degree13, repeated13 = [load(entry["path"])
    for entry in INPUTS["inputs"]]
result = json.loads((HERE / "result.json").read_text())
assert old["column_points"] == corrected["column_points"]
F = GF(83)
E = EllipticCurve(F, [0, -1, 1, -10, -20])
points = []
for encoded in old["column_points"]:
    match = re.fullmatch(r"\((\d+) : (\d+) : 1\)", encoded)
    assert match is not None
    points.append(E([int(match.group(1)), int(match.group(2)), 1]))
assert len(points) == len(set(points)) == 20
base = list(map(sparse, corrected["relation_rows"]))
base += [sparse(item["row"]) for item in cancellation["closed_rows"] + cancellation["pair_rows"]]
base += [sparse(item["row"]) for item in degree13["sources"] if item["status"] == "CLASS_CLOSED"]
assert rank(base, QQ) == result["base_rank_qq"] == 17
assert rank(base, GF(5)) == result["base_rank_mod5"] == 17


def rebuild(degree, source, orbits, eigenvalue):
    class_part = Counter()
    outside = []
    for orbit in orbits:
        multiplicity = orbit.get("multiplicity", 1)
        if orbit["trace_status"] == "IN_CLASS":
            i = orbit["trace_class_index"]
            coords = orbit["trace_coordinates"]
            assert coords is not None and points[i] == E([int(coords[0]), int(coords[1]), 1])
            class_part[i] += multiplicity
        elif orbit["trace_status"] == "OUTSIDE_CLASS":
            coords = orbit["trace_coordinates"]
            assert coords is not None and all(value.isdecimal() for value in coords)
            Q = E([int(coords[0]), int(coords[1]), 1])
            assert Q not in points
            outside.extend([Q] * multiplicity)
        else:
            assert orbit["trace_status"] == "IDENTITY"
    assert len(outside) == 1
    class_part[source] -= eigenvalue
    class_part = {i: int(value) for i, value in class_part.items() if value}
    total = outside[0] + sum((coefficient * points[i] for i, coefficient in class_part.items()), E(0))
    assert total.is_zero()
    return {"degree": degree, "source": source,
            "outside": [int(outside[0][0]), int(outside[0][1])],
            "class_part": {str(i): value for i, value in sorted(class_part.items())}}


rows = []
for degree, previous in [(5, degree5), (13, degree13)]:
    for entry in previous["sources"]:
        if entry["status"] == "OUTSIDE_CLASS_TRACE":
            rows.append(rebuild(degree, entry["source"], entry["orbits"], previous["a_l"]))
assert repeated13["status"] == "UNIQUE_LIFT"
rows.append(rebuild(13, 19, repeated13["candidates"][0]["orbits"], degree13["a_l"]))
rows.sort(key=lambda item: (item["degree"], item["source"]))
assert rows == result["expanded_rows"] and len(rows) == 29

retained = []
counts = Counter()
selected = []
selected_rows = []
rank_path = [{"selected": 0, "rank_qq": 17, "rank_mod5": 17}]
outside_points = [E([*row["outside"], 1]) for row in rows]
for support_size in range(1, INPUTS["support_cap"] + 1):
    for indexes in itertools.combinations(range(len(rows)), support_size):
        for tail in itertools.product(INPUTS["coefficients"], repeat=support_size - 1):
            weights = (1,) + tail
            aux_sum = sum((weight * outside_points[index]
                           for index, weight in zip(indexes, weights)), E(0))
            if not aux_sum.is_zero():
                continue
            class_row = Counter()
            for index, weight in zip(indexes, weights):
                for column, value in rows[index]["class_part"].items():
                    class_row[int(column)] += weight * value
            class_row = {i: int(value) for i, value in class_row.items() if value}
            assert sum((value * points[i] for i, value in class_row.items()), E(0)).is_zero()
            candidate = {"support": [{"degree": rows[index]["degree"],
                                       "source": rows[index]["source"],
                                       "coefficient": weight}
                                      for index, weight in zip(indexes, weights)],
                         "row": {str(i): value for i, value in sorted(class_row.items())}}
            retained.append(candidate)
            counts[support_size] += 1
            if rank(base + selected_rows + [class_row], GF(5)) > rank_path[-1]["rank_mod5"]:
                selected.append(len(retained) - 1)
                selected_rows.append(class_row)
                rank_path.append({"selected": len(selected),
                                  "candidate_index": len(retained) - 1,
                                  "rank_qq": rank(base + selected_rows, QQ),
                                  "rank_mod5": rank(base + selected_rows, GF(5))})
assert retained == result["candidates"]
assert {str(k): v for k, v in sorted(counts.items())} == result["candidate_count_by_support"]
assert selected == result["selected_candidate_indices"] and rank_path == result["rank_path"]
assert rank(base + selected_rows, QQ) == result["final_rank_qq"] == 19
assert rank(base + selected_rows, GF(5)) == result["final_rank_mod5"] == 19

projections = [INPUTS["cofactor"] * P for P in points]
nonzero = [i for i, P in enumerate(projections) if not P.is_zero()]
assert nonzero == result["nonzero_projection_indices"]
assert all((5 * P).is_zero() for P in projections)
generator5 = projections[nonzero[0]]
logs5 = [next(k for k in range(5) if k * generator5 == P) for P in projections]
M = matrix(GF(5), [[row.get(i, 0) for i in range(20)] for row in base + selected_rows])
kernel = M.right_kernel()
assert kernel.dimension() == 1 and M * vector(GF(5), logs5) == 0
assert any(logs5)
validation = {"schema": "hecke-trace-short-relations-validation-v1",
              "expanded_rows": len(rows), "candidate_counts": {str(k): v for k, v in counts.items()},
              "selected_candidate_indices": selected, "rank_path": rank_path,
              "kernel_dimension_mod5": int(kernel.dimension()),
              "nonzero_projection_indices": nonzero,
              "projection_coordinates_mod5": logs5}
(HERE / "validation.json").write_text(json.dumps(validation, sort_keys=True, indent=2) + "\n")
print("SHORT_TRACE_RELATIONS_PASS", "candidates", len(retained),
      "selected", len(selected), "rank_mod5", 17, "->", 19,
      "kernel_dimension", int(kernel.dimension()))
