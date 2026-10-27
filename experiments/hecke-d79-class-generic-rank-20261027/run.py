"""Exhaustive direct signed relations among the frozen D79 p317 class points."""
import hashlib
import itertools
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
INPUTS = json.loads((HERE / "inputs.json").read_text())
P = INPUTS["p"]


def load(entry):
    data = (ROOT / entry["path"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == entry["sha256"]
    return json.loads(data)


def neg(A):
    return None if A is None else (A[0], (-A[1] - 1) % P)


def add(A, B):
    if A is None:
        return B
    if B is None:
        return A
    x, y = A
    u, v = B
    if x == u and (y + v + 1) % P == 0:
        return None
    if A == B:
        top, bottom = 3*x*x - 2*x - 10, 2*y + 1
    else:
        top, bottom = v-y, u-x
    slope = top*pow(bottom % P, -1, P) % P
    intercept = (y-slope*x) % P
    X = (slope*slope+1-x-u) % P
    Y = (-slope*X-intercept-1) % P
    C = X, Y
    assert (Y*Y+Y-X*X*X+X*X+10*X+20) % P == 0
    return C


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


def row(raw):
    return {int(i): int(v) for i, v in raw.items() if v}


def main():
    data = load(INPUTS["class_receipt"])
    search = load(INPUTS["search_receipt"])
    assert all(load(entry)["status"] == "PASS" for entry in INPUTS["validation_receipts"])
    assert data["p"] == search["p"] == P
    assert data["curve_order"] == INPUTS["curve_order"]
    points = [tuple(A) for A in data["class_points"]]
    assert len(points) == INPUTS["class_size"]
    base = [row(x["row"]) for x in data["base_rows"]]
    assert len(base) == rank(base) == rank(base, 61) == INPUTS["base_rank"]
    coords = search["projection_coordinates_mod61"]
    assert len(coords) == len(points)
    candidates, selected, selected_rows = [], [], []
    counts = Counter()
    rank_path = [{"selected": 0, "rank_qq": len(base), "rank_mod61": len(base)}]
    for support in range(1, INPUTS["support_max"]+1):
        for inds in itertools.combinations(range(len(points)), support):
            for rest in itertools.product(INPUTS["coefficient_order"], repeat=support-1):
                signs = (1,) + rest
                total = None
                for i, sign in zip(inds, signs):
                    total = add(total, points[i] if sign == 1 else neg(points[i]))
                if total is not None:
                    continue
                r = dict(zip(inds, signs))
                assert sum(sign*coords[i] for i, sign in r.items()) % 61 == 0
                idx = len(candidates)
                candidates.append({"indices": list(inds), "coefficients": list(signs),
                                   "row": {str(i): v for i, v in r.items()}})
                counts[support] += 1
                if rank(base+selected_rows+[r], 61) > rank(base+selected_rows, 61):
                    selected.append(idx)
                    selected_rows.append(r)
                    rank_path.append({"selected": len(selected), "candidate_index": idx,
                                      "rank_qq": rank(base+selected_rows),
                                      "rank_mod61": rank(base+selected_rows, 61)})
    direct = [row(c["row"]) for c in candidates]
    closed = [row(x["class_part"]) for x in data["degree13_sources"]
              if x["status"] == "CLASS_CLOSED"]
    hecke = [row(c["row"]) for c in search["candidates"]]
    assert len(closed) == 5 and len(hecke) == 80
    ranks = {"direct_only_qq": rank(direct), "direct_only_mod61": rank(direct, 61),
             "base_plus_direct_qq": rank(base+direct),
             "base_plus_direct_mod61": rank(base+direct, 61),
             "base_plus_closed_qq": rank(base+closed),
             "base_plus_closed_mod61": rank(base+closed, 61),
             "base_plus_hecke_qq": rank(base+closed+hecke),
             "base_plus_hecke_mod61": rank(base+closed+hecke, 61),
             "base_plus_direct_plus_hecke_qq": rank(base+closed+direct+hecke),
             "base_plus_direct_plus_hecke_mod61": rank(base+closed+direct+hecke, 61)}
    assert ranks["base_plus_closed_mod61"] == 23
    assert ranks["base_plus_hecke_mod61"] == 38
    assert rank_path[-1]["rank_mod61"] == ranks["base_plus_direct_mod61"]
    out = {"schema": "hecke-d79-class-generic-rank-v1", "p": P,
           "class_size": len(points), "curve_order": data["curve_order"],
           "candidate_counts": {str(k): counts[k] for k in range(1, 4)},
           "candidates": candidates, "selected_candidate_indices": selected,
           "rank_path": rank_path, "ranks": ranks,
           "candidate_id": None, "target_online_ms": None}
    (HERE / "result.json").write_text(json.dumps(out, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"counts": out["candidate_counts"], "selected": len(selected),
                      "ranks": ranks}, sort_keys=True))


if __name__ == "__main__":
    main()
