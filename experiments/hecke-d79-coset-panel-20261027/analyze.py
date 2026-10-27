"""Pure-integer-field direct relation census for frozen coset classes."""
import hashlib
import itertools
import json
import math
import time
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / "post_inputs.json").read_text())
raw = (ROOT / PLAN["class_receipt"]).read_bytes()
assert hashlib.sha256(raw).hexdigest() == PLAN["class_receipt_sha256"]
CLASSES = json.loads(raw)
assert CLASSES["status"] == "COMPLETE"


def on_curve(A, p):
    if A is None:
        return True
    x, y = A
    return (y*y+y-x*x*x+x*x+10*x+20) % p == 0


def neg(A, p):
    return None if A is None else (A[0], (-A[1]-1) % p)


def add(A, B, p):
    if A is None:
        return B
    if B is None:
        return A
    x, y = A
    u, v = B
    if x == u and (y+v+1) % p == 0:
        return None
    if A == B:
        top, bottom = 3*x*x-2*x-10, 2*y+1
    else:
        top, bottom = v-y, u-x
    slope = top*pow(bottom % p, -1, p) % p
    intercept = (y-slope*x) % p
    X = (slope*slope+1-x-u) % p
    Y = (-slope*X-intercept-1) % p
    C = X, Y
    assert on_curve(C, p)
    return C


def rank(rows, modulus=None):
    pivots = {}
    for raw in rows:
        if modulus is None:
            v = {i: Fraction(x) for i, x in raw.items() if x}
        else:
            v = {i: x % modulus for i, x in raw.items() if x % modulus}
        while v:
            i = min(v)
            if i not in pivots:
                z = v[i]
                pivots[i] = ({j: x/z for j, x in v.items()} if modulus is None else
                             {j: x*pow(z, -1, modulus) % modulus for j, x in v.items()})
                break
            z = v[i]
            for j, x in pivots[i].items():
                y = v.get(j, 0)-z*x
                if modulus is not None:
                    y %= modulus
                if y:
                    v[j] = y
                else:
                    v.pop(j, None)
    return len(pivots)


def row(raw):
    return {int(i): int(v) for i, v in raw.items() if v}


def main():
    out = {"schema": "hecke-d79-coset-direct-census-v1", "cases": [],
           "candidate_id": None, "target_online_ms": None}
    for source in CLASSES["cases"]:
        start = time.perf_counter_ns()
        p, n, q = source["p"], source["curve_order"], source["largest_prime_factor"]
        points = [tuple(A) for A in source["class_points"]]
        assert len(points) == len(set(points)) and all(on_curve(A, p) for A in points)
        base = [row(r["row"]) for r in source["base_rows"]]
        assert rank(base) == source["base_rank_qq"]
        assert rank(base, q) == source["base_rank_mod_q"]
        candidates = []
        trials = 0
        for support in range(1, PLAN["support_max"]+1):
            for inds in itertools.combinations(range(len(points)), support):
                for rest in itertools.product(PLAN["coefficient_order"], repeat=support-1):
                    signs = (1,) + rest
                    trials += 1
                    total = None
                    for i, sign in zip(inds, signs):
                        total = add(total, points[i] if sign == 1 else neg(points[i], p), p)
                    if total is None:
                        candidates.append({"indices": list(inds),
                                           "coefficients": list(signs),
                                           "row": {str(i): sign for i, sign in zip(inds, signs)}})
        enumeration_ns = time.perf_counter_ns()-start
        rank_start = time.perf_counter_ns()
        direct_rows = [row(c["row"]) for c in candidates]
        selected, selected_rows = [], []
        path = [{"selected": 0, "rank_mod_q": rank(base, q), "rank_qq": rank(base)}]
        for i, r in enumerate(direct_rows):
            if rank(base+selected_rows+[r], q) > rank(base+selected_rows, q):
                selected.append(i)
                selected_rows.append(r)
                path.append({"selected": len(selected), "candidate_index": i,
                             "rank_mod_q": rank(base+selected_rows, q),
                             "rank_qq": rank(base+selected_rows)})
        ranks = {"direct_only_mod_q": rank(direct_rows, q),
                 "direct_only_qq": rank(direct_rows),
                 "base_plus_direct_mod_q": rank(base+direct_rows, q),
                 "base_plus_direct_qq": rank(base+direct_rows)}
        assert path[-1]["rank_mod_q"] == ranks["base_plus_direct_mod_q"]
        counts = {str(s): sum(len(c["indices"]) == s for c in candidates)
                  for s in range(1, 4)}
        if source["antipodal_only"]:
            assert counts["3"] == source["predicted_support3_count"] == 0
        mean = Fraction(4*math.comb(len(points), 3)*(n-2), (n-1)**2)
        case = {"p": p, "class_size": len(points), "curve_order": n,
                "rank_modulus": q, "antipodal_only": source["antipodal_only"],
                "predicted_support3_count": source["predicted_support3_count"],
                "candidate_counts": counts, "candidate_sign_patterns": trials,
                "candidates": candidates, "selected_candidate_indices": selected,
                "rank_path": path, "ranks": ranks,
                "iid_nonidentity_support3_mean_exact": f"{mean.numerator}/{mean.denominator}",
                "enumeration_wall_ns": enumeration_ns,
                "rank_analysis_wall_ns": time.perf_counter_ns()-rank_start}
        out["cases"].append(case)
        (HERE / "analysis.json").write_text(json.dumps(out, indent=2, sort_keys=True)+"\n")
        print(json.dumps({"p": p, "counts": counts, "ranks": ranks,
                          "antipodal_only": source["antipodal_only"]},
                         sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
