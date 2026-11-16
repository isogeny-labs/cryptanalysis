"""Independent exact verifier using only Python integer and fraction arithmetic."""
import gzip
import hashlib
import json
from fractions import Fraction
from math import gcd, lcm, isqrt
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "xedni-varying-curve-selection-20261115" / "rows-v2.jsonl.gz"
EXPECTED = "9a594d96f369fb14f1a4cf6270b1c811ceda515e1c2a7eccab4d011ca8f3f322"
assert hashlib.sha256(PARENT.read_bytes()).hexdigest() == EXPECTED


def mod(frac, p):
    frac = Fraction(frac)
    return frac.numerator * pow(frac.denominator, -1, p) % p


def add(P, Q, a, p):
    if P is None:
        return Q
    if Q is None:
        return P
    x1, y1 = P
    x2, y2 = Q
    if x1 == x2 and (y1 + y2) % p == 0:
        return None
    if P == Q:
        slope = (3*x1*x1 + a) * pow(2*y1, -1, p) % p
    else:
        slope = (y2-y1) * pow((x2-x1) % p, -1, p) % p
    x3 = (slope*slope-x1-x2) % p
    return x3, (slope*(x1-x3)-y1) % p


def order(P, a, p):
    T = None
    for n in range(1, p + 2 + 2*isqrt(p)):
        T = add(T, P, a, p)
        if T is None:
            return n
    raise AssertionError("Hasse cap exceeded")


def divisors(n):
    n = abs(n)
    assert n != 0
    small = [d for d in range(1, isqrt(n)+1) if n % d == 0]
    return sorted(set(small + [n//d for d in small]))


def roots_of_cubic(A, B):
    L = lcm(A.denominator, B.denominator)
    c1, c0 = int(L*A), int(L*B)
    found = set()
    for u in divisors(c0):
        for v in divisors(L):
            if gcd(u, v) != 1:
                continue
            for sign in (-1, 1):
                x = Fraction(sign*u, v)
                if L*x**3 + c1*x + c0 == 0:
                    found.add(x)
    return sorted(found)


with gzip.open(PARENT, "rt") as stream:
    source = [json.loads(line) for line in stream]
recorded = json.loads((HERE / "rows.json").read_text())
summary = json.loads((HERE / "result.json").read_text())
assert len(source) == 1722 and len(recorded) == 20
accepted = [(i, row) for i, row in enumerate(source) if row["accepted"]]
assert len(accepted) == 20
qualifying = 0
for (i, row), result in zip(accepted, recorded):
    assert i == result["parent_row_index"]
    A, B = Fraction(row["A"]), Fraction(row["B"])
    a, b = mod(A, 7), mod(B, 7)
    points = [(x, y) for x in range(7) for y in range(7)
              if (y*y-x*x*x-a*x-b) % 7 == 0]
    assert len(points) + 1 == 4
    P, Q = [tuple(c % 7 for c in pair) for pair in row["lifted_points"]]
    assert P in points and Q in points
    orders = [order(P, a, 7), order(Q, a, 7)]
    assert result["mod7_orders"] == orders
    assert result["mod7_points"] == [list(P), list(Q)]
    assert result["mod7_distinct"] == (P != Q)
    assert result["rational_2_torsion_x_roots"] == [str(x) for x in roots_of_cubic(A, B)]
    qualifying += orders == [2, 2] and P != Q
assert qualifying == summary["mod7_independent_pair_rows"] == 16
assert summary["accepted_reduced_relations"] == 2
assert summary["rational_2_torsion_free_curve_count"] == 3
receipt = {"status": "PASS", "parent_rows": 1722, "accepted_rows": 20,
           "mod7_independent_pair_rows": qualifying, "rational_2_torsion_free_curves": 3,
           "method": "independent Python finite-field group law and rational-root enumeration"}
(HERE / "audit.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
print(json.dumps(receipt, sort_keys=True))
