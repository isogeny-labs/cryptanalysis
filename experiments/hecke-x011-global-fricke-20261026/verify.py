"""Exact X_0(11) model checks for the global Fricke identification."""
import json
from pathlib import Path

from sage.all import CuspForms, EllipticCurve, GF


OUT = Path(__file__).with_name("verification.json")
E = EllipticCurve("11a1")
O = E(0)
T = E(16, -61)
U = E(16, 60)
f = CuspForms(11, 2).newforms("a")[0]

assert list(E.a_invariants()) == [0, -1, 1, -10, -20]
assert E.conductor() == 11
assert E.modular_degree() == 1
assert E.j_invariant() not in (0, 1728)
assert T.order() == 5
assert -T == U
assert f.atkin_lehner_eigenvalue(11) == -1
assert E.ap(11) == 1

# The external modular-curve coordinate identification names O and T as
# cusps infinity and zero. Here we verify the curve and group-law data it uses.
def W(P):
    return T - P


assert W(O) == T and W(T) == O
assert W(W(U)) == U

finite_field_checks = {}
for p in (7, 13, 23, 23743):
    F = GF(p)
    Ep = EllipticCurve(F, [0, -1, 1, -10, -20])
    Tp = Ep(F(16), F(-61))
    assert 5 * Tp == Ep(0)
    pts = Ep.points() if p < 100 else [Ep(0), Tp, Ep(F(16), F(60))]
    assert all(Tp - (Tp - P) == P for P in pts)
    finite_field_checks[str(p)] = {"checked_points": len(pts), "reduced_T_order": int(Tp.order())}

result = {
    "status": "EXACT_MODEL_AND_GROUP_CHECK_PASS",
    "curve": "11a1",
    "a_invariants": [int(a) for a in E.a_invariants()],
    "conductor": int(E.conductor()),
    "modular_degree": int(E.modular_degree()),
    "j_invariant": str(E.j_invariant()),
    "cusp_zero_coordinate_from_reference": [16, -61],
    "T_order": int(T.order()),
    "fricke_eigenvalue_weight_two": int(f.atkin_lehner_eigenvalue(11)),
    "a11": int(E.ap(11)),
    "finite_field_checks": finite_field_checks,
}
OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, sort_keys=True))
