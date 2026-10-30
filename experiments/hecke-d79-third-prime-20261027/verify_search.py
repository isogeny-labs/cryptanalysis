"""Independent checked-Sage enumeration and rank replay for p=223."""
import hashlib
import itertools
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ, matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
I = json.loads((HERE / "search_inputs.json").read_text())


def load(entry):
    data = (ROOT / entry["path"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == entry["sha256"]
    return json.loads(data)


def row(raw):
    return {int(k): int(v) for k, v in raw.items() if v}


def rank(rows, field):
    return int(matrix(field, [[r.get(i, 0) for i in range(20)] for r in rows]).rank())


data, prior_validation, prior_sage_validation = [load(x) for x in I["inputs"]]
assert prior_validation["status"] == prior_sage_validation["status"] == "PASS"
out = json.loads((HERE / "search-result.json").read_text())
assert (data["p"], data["curve_order"], out["p"]) == (223, 205, 223)
E = EllipticCurve(GF(223), [0, -1, 1, -10, -20])
assert int(E.order()) == 205
points = [E([x, y, 1]) for x, y in data["class_points"]]
assert len(points) == len(set(points)) == 20
base = [row(x["row"]) for x in data["base_rows"]]
base += [row(x["class_part"]) for x in data["degree13_sources"]
         if x["status"] == "CLASS_CLOSED"]
assert rank(base, QQ) == rank(base, GF(41)) == 10
sources = [x for x in data["degree13_sources"] if x["status"] == "OUTSIDE_CLASS_TRACE"]
assert len(sources) == 20
source_sum = {}
for item in sources:
    source_sum[item["source"]] = sum(
        (E([x, y, 1]) for x, y in item["outside_traces"]), E(0))
    class_part = row(item["class_part"])
    assert sum((v * points[i] for i, v in class_part.items()), E(0)) + source_sum[item["source"]] == E(0)
replayed = []
selected = []
selected_rows = []
rank_path = [{"selected": 0, "rank_qq": 10, "rank_mod41": 10}]
counts = {"1": 0, "2": 0, "3": 0}
for support in range(1, 4):
    for chosen in itertools.combinations(sources, support):
        for rest in itertools.product((-1, 1), repeat=support - 1):
            coeffs = (1,) + rest
            auxiliary = sum((c * source_sum[x["source"]] for x, c in zip(chosen, coeffs)), E(0))
            if auxiliary != E(0):
                continue
            relation = {}
            for item, c in zip(chosen, coeffs):
                for i, v in row(item["class_part"]).items():
                    relation[i] = relation.get(i, 0) + c*v
            relation = {i: v for i, v in relation.items() if v}
            assert sum((v*points[i] for i, v in relation.items()), E(0)) == E(0)
            replayed.append({"sources": [x["source"] for x in chosen],
                             "coefficients": list(coeffs),
                             "row": {str(i): v for i, v in sorted(relation.items())}})
            counts[str(support)] += 1
            before = rank(base + selected_rows, GF(41))
            after = rank(base + selected_rows + [relation], GF(41))
            if after > before:
                selected.append(len(replayed)-1)
                selected_rows.append(relation)
                rank_path.append({"selected": len(selected),
                                  "candidate_index": len(replayed)-1,
                                  "rank_qq": rank(base+selected_rows, QQ),
                                  "rank_mod41": after})
assert replayed == out["candidates"]
assert counts == out["candidate_counts"] == {"1": 0, "2": 4, "3": 20}
assert selected == out["selected_candidate_indices"]
assert rank_path == out["rank_path"]
assert rank(base+selected_rows, QQ) == rank(base+selected_rows, GF(41)) == 19
assert (out["final_rank_qq"], out["final_rank_mod41"]) == (19, 19)
projections = [5*P for P in points]
assert all(P != E(0) and 41*P == E(0) for P in projections)
generator = E([*out["projection_generator"], 1])
coordinates = [next(i for i in range(41) if i*generator == P) for P in projections]
assert coordinates == out["projection_coordinates_mod41"]
assert all(sum(v*coordinates[i] for i, v in r.items()) % 41 == 0
           for r in base+[row(c["row"]) for c in replayed])
M = matrix(GF(41), [[r.get(i, 0) for i in range(20)] for r in base+selected_rows])
assert M.right_kernel().dimension() == 1
V = {"schema": "hecke-d79-third-prime-short-cancellations-validation-v1",
     "status": "PASS", "candidates": len(replayed), "candidate_counts": counts,
     "selected": len(selected), "rank_path": rank_path,
     "projection_nonzero": 20, "right_kernel_dimension_mod41": 1}
(HERE / "search-validation.json").write_text(json.dumps(V, indent=2, sort_keys=True)+"\n")
print("D79_THIRD_PRIME_SHORT_CANCELLATIONS_PASS", "candidates", len(replayed),
      "rank_mod41", 10, "->", 19)
