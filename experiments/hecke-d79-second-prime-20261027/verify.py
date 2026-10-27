"""Independent integer-field group and exact rank replay of p=179 output."""
import itertools
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = json.loads((HERE / "result.json").read_text())
P = 179


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


def rank(rows, modulus=None):
    pivots = {}
    for source in rows:
        if modulus is None:
            values = {i: Fraction(v) for i, v in source.items() if v}
        else:
            values = {i: v % modulus for i, v in source.items() if v % modulus}
        while values:
            i = min(values)
            if i not in pivots:
                scale = values[i]
                if modulus is None:
                    pivots[i] = {j: v/scale for j, v in values.items()}
                else:
                    inverse = pow(scale, -1, modulus)
                    pivots[i] = {j: v*inverse % modulus for j, v in values.items()}
                break
            scale = values[i]
            for j, v in pivots[i].items():
                value = values.get(j, 0)-scale*v
                if modulus is not None:
                    value %= modulus
                if value:
                    values[j] = value
                else:
                    values.pop(j, None)
    return len(pivots)


def row(raw):
    return {int(i): int(v) for i, v in raw.items() if v}


assert R["schema"] == "hecke-d79-second-prime-v1"
assert (R["DK"], R["f"], R["p"], R["trace_magnitude"]) == (-79, 2, 179, 20)
assert (R["curve_order"], R["largest_prime_factor"]) == (195, 13)
points = [tuple(A) for A in R["class_points"]]
assert len(points) == R["class_size"] == len(set(points)) == 20
assert points == sorted(points) and all(on_curve(A) for A in points)
assert sum(1 for x in range(P) for y in range(P) if on_curve((x, y))) + 1 == 195
base = []
for item in R["base_rows"]:
    assert item["degree"] in (2, 5) and 0 <= item["source"] < 20
    rr = row(item["row"])
    total = None
    for i, coeff in rr.items():
        total = add(total, mul(coeff, points[i]))
    assert total is None
    base.append(rr)
assert rank(base) == R["base_rank_qq"] == 10
assert rank(base, 13) == R["base_rank_mod_q"] == 10
closed = []
outside = []
assert [item["source"] for item in R["degree13_sources"]] == list(range(20))
for item in R["degree13_sources"]:
    assert item["factor_pattern"] == [[1, 1], [1, 1], [3, 1], [3, 1], [3, 1], [3, 1]]
    assert item["splitting_degree"] == 3
    assert sum(orb["size"] for orb in item["orbits"]) == 14
    total = None
    class_count = Counter({item["source"]: -4})
    outs = []
    for orb in item["orbits"]:
        assert orb["size"] in (1, 3)
        if orb["status"] == "IDENTITY":
            assert orb["trace"] is None
            continue
        T = tuple(orb["trace"])
        assert on_curve(T)
        total = add(total, T)
        if orb["status"] == "IN_CLASS":
            assert T in points
            class_count[points.index(T)] += 1
        else:
            assert orb["status"] == "OUTSIDE_CLASS" and T not in points
            outs.append(T)
    assert total == mul(4, points[item["source"]])
    assert row(item["class_part"]) == {i: v for i, v in class_count.items() if v}
    assert item["outside_traces"] == [list(T) for T in sorted(outs)]
    if outs:
        assert item["status"] == "OUTSIDE_CLASS_TRACE"
        outside.append(item)
    else:
        assert item["status"] == "CLASS_CLOSED"
        closed.append(row(item["class_part"]))
assert R["degree13_statuses"] == {"CLASS_CLOSED": 1, "OUTSIDE_CLASS_TRACE": 19}
assert rank(base+closed) == R["rank_with_closed_qq"] == 11
assert rank(base+closed, 13) == R["rank_with_closed_mod_q"] == 11
replayed_pairs = []
for a, b in itertools.combinations(outside, 2):
    if a["outside_traces"] == b["outside_traces"]:
        replayed_pairs.append([a["source"], b["source"]])
assert replayed_pairs == [x["sources"] for x in R["equal_trace_pairs"]] == []
assert rank(base+closed, 13) == R["rank_with_pairs_mod_q"]
assert rank(base+closed) == R["rank_with_pairs_qq"]
V = {"schema": "hecke-d79-second-prime-validation-v1", "status": "PASS",
     "curve_order_independent_enumeration": 195, "class_points": 20,
     "base_rows": len(base), "degree13_closed": len(closed),
     "degree13_outside": len(outside), "equal_trace_pairs": len(replayed_pairs),
     "rank_path_QQ": [10, 11, 11], "rank_path_F13": [10, 11, 11]}
(HERE / "validation.json").write_text(json.dumps(V, indent=2, sort_keys=True)+"\n")
print("D79_SECOND_PRIME_PASS", "rank_F13", "10 -> 11", "outside", len(outside))
