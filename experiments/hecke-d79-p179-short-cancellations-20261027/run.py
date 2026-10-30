"""Enumerate short signed group-law cancellations of p=179 outside traces."""
import hashlib
import itertools
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
INPUTS = json.loads((HERE / "inputs.json").read_text())
P = 179


def load(entry):
    data = (ROOT / entry["path"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == entry["sha256"]
    return json.loads(data)


def on_curve(A):
    if A is None:
        return True
    x, y = A
    return (y*y+y-x*x*x+x*x+10*x+20) % P == 0


def neg(A):
    return None if A is None else (A[0], (-A[1]-1) % P)


def add(A, B):
    if A is None:
        return B
    if B is None:
        return A
    x, y = A
    u, v = B
    if x == u and (y+v+1) % P == 0:
        return None
    if A == B:
        top, bottom = 3*x*x-2*x-10, 2*y+1
    else:
        top, bottom = v-y, u-x
    slope = top*pow(bottom % P, -1, P) % P
    intercept = (y-slope*x) % P
    X = (slope*slope+1-x-u) % P
    Y = (-slope*X-intercept-1) % P
    C = X, Y
    assert on_curve(C)
    return C


def mul(n, A):
    if n < 0:
        return mul(-n, neg(A))
    C = None
    while n:
        if n & 1:
            C = add(C, A)
        A = add(A, A)
        n >>= 1
    return C


def sum_points(points):
    T = None
    for Q in points:
        T = add(T, Q)
    return T


def row(raw):
    return {int(i): int(v) for i, v in raw.items() if v}


def rank(rows, modulus=None):
    pivots = {}
    for raw in rows:
        if modulus is None:
            values = {i: Fraction(v) for i, v in raw.items() if v}
        else:
            values = {i: v % modulus for i, v in raw.items() if v % modulus}
        while values:
            i = min(values)
            if i not in pivots:
                x = values[i]
                pivots[i] = ({j: v/x for j, v in values.items()} if modulus is None else
                             {j: v*pow(x, -1, modulus) % modulus for j, v in values.items()})
                break
            x = values[i]
            for j, v in pivots[i].items():
                y = values.get(j, 0)-x*v
                if modulus is not None:
                    y %= modulus
                if y:
                    values[j] = y
                else:
                    values.pop(j, None)
    return len(pivots)


def main():
    data, validation, sage_validation = [load(e) for e in INPUTS["inputs"]]
    assert validation["status"] == sage_validation["status"] == "PASS"
    assert data["p"] == P and data["curve_order"] == 195
    points = [tuple(A) for A in data["class_points"]]
    assert len(points) == 20 and all(on_curve(A) for A in points)
    sources = [x for x in data["degree13_sources"] if x["status"] == "OUTSIDE_CLASS_TRACE"]
    assert len(sources) == 19
    baseline = [row(x["row"]) for x in data["base_rows"]]
    baseline += [row(x["class_part"]) for x in data["degree13_sources"]
                 if x["status"] == "CLASS_CLOSED"]
    assert rank(baseline) == rank(baseline, 13) == 11
    for source in sources:
        class_part = row(source["class_part"])
        outside = [tuple(A) for A in source["outside_traces"]]
        assert all(on_curve(A) for A in outside)
        assert sum_points([mul(v, points[i]) for i, v in class_part.items()] + outside) is None
    candidates = []
    selected = []
    selected_rows = []
    rank_path = [{"selected": 0, "rank_qq": 11, "rank_mod13": 11}]
    counts = Counter()
    for support in range(1, INPUTS["support_max"] + 1):
        for chosen in itertools.combinations(sources, support):
            for rest in itertools.product(INPUTS["coefficient_order"], repeat=support-1):
                coeffs = (1,) + rest
                auxiliary = []
                relation = Counter()
                for item, coeff in zip(chosen, coeffs):
                    auxiliary.extend(mul(coeff, tuple(T)) for T in item["outside_traces"])
                    for i, v in row(item["class_part"]).items():
                        relation[i] += coeff*v
                if sum_points(auxiliary) is not None:
                    continue
                relation = {i: v for i, v in relation.items() if v}
                assert sum_points(mul(v, points[i]) for i, v in relation.items()) is None
                record = {"sources": [x["source"] for x in chosen],
                          "coefficients": list(coeffs),
                          "row": {str(i): v for i, v in sorted(relation.items())}}
                idx = len(candidates)
                candidates.append(record)
                counts[support] += 1
                before = rank(baseline + selected_rows, 13)
                after = rank(baseline + selected_rows + [relation], 13)
                if after > before:
                    selected.append(idx)
                    selected_rows.append(relation)
                    rank_path.append({"selected": len(selected), "candidate_index": idx,
                                      "rank_qq": rank(baseline + selected_rows),
                                      "rank_mod13": after})
    projections = [mul(15, A) for A in points]
    generator = next((A for A in projections if A is not None), None)
    assert generator is not None and mul(13, generator) is None
    multiples = {mul(i, generator): i for i in range(13)}
    assert len(multiples) == 13 and all(A in multiples for A in projections)
    coordinates = [multiples[A] for A in projections]
    final_rows = baseline + selected_rows
    all_rows = baseline + [row(c["row"]) for c in candidates]
    assert all(sum(v*coordinates[i] for i, v in r.items()) % 13 == 0 for r in all_rows)
    out = {"schema": "hecke-d79-p179-short-cancellations-v1",
           "p": P, "class_size": len(points), "outside_sources": len(sources),
           "support_max": INPUTS["support_max"],
           "candidate_counts": {str(k): counts[k] for k in range(1, INPUTS["support_max"]+1)},
           "candidates": candidates, "selected_candidate_indices": selected,
           "rank_path": rank_path, "final_rank_qq": rank(final_rows),
           "final_rank_mod13": rank(final_rows, 13),
           "projection_generator": list(generator),
           "projection_coordinates_mod13": coordinates,
           "projection_nonzero_indices": [i for i, A in enumerate(projections) if A is not None],
           "candidate_id": None, "target_online_ms": None}
    (HERE / "result.json").write_text(json.dumps(out, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"candidates": len(candidates), "counts": out["candidate_counts"],
                      "selected": len(selected), "rank_mod13": [11, out["final_rank_mod13"]]},
                     sort_keys=True))


if __name__ == "__main__":
    main()
