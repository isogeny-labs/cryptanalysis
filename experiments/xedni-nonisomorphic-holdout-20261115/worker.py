"""One checked-Sage rank/torsion candidate cell."""
import json
import sys
from sage.all import EllipticCurve, GF, QQ

p, q, m, u = map(int, sys.argv[1:5])
F = GF(p)
E0 = EllipticCurve(F, [-1, -2])
P0 = E0(2, 2)
assert int(P0.order()) == m * q
G = m * P0
R = u * G
assert not R.is_zero() and int(G.order()) == q
x0, y0 = map(int, R.xy())
x = x0 if x0 <= p // 2 else x0 - p
y = y0 if y0 <= p // 2 else y0 - p
B = y*y - x*x*x + x
E = EllipticCurve(QQ, [-1, B])
P = E(x, y)
assert E.discriminant() != 0 and int(E.discriminant()) % p != 0
assert E.change_ring(F).a_invariants() == E0.a_invariants()
assert E.change_ring(F)(x, y) == R
T = int(E.torsion_subgroup().order())
assert T*P != E(0)
row = {"field_prime":p,"subgroup_order":q,"multiplier_m":m,"u":u,
       "reduced_point":[x0,y0],"centered_point":[x,y],"curve_B":B,
       "discriminant":int(E.discriminant()),"j_invariant":str(E.j_invariant()),
       "torsion_order":T,"point_nontorsion":True}
try:
    row["rank"] = int(E.rank(proof=True))
    row["rank_status"] = "proved"
except Exception as exc:
    row["rank"] = None
    row["rank_status"] = "error"
    row["rank_error"] = type(exc).__name__ + ": " + str(exc)[:200]
print(json.dumps(row, sort_keys=True))
