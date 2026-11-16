"""Separate checked-Sage certificate for the unique rational-relation hit."""
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ

HERE = Path(__file__).resolve().parent
hit = json.loads((HERE / "hit.json").read_text())
registry = json.loads((HERE.parent / "xedni-crt-band-panel-20261115" / "result.json").read_text())
p = hit["field_prime"]
q = hit["subgroup_order"]
entry = next(row for row in registry["fields"] if row["field_prime"] == p)
assert entry["subgroup_order"] == q
base = EllipticCurve(GF(p), [-1, -2])
G = base(*entry["generator"])
target = hit["fixture_scalar"] * G
t1, t2 = hit["offsets"]
U, V = target-t1*G, target-t2*G
E = EllipticCurve(QQ, [QQ(hit["A"]), QQ(hit["B"])])
P, Q = [E(x, y) for x, y in hit["lifted_points"]]
a, b = hit["vector"]
assert E.discriminant() != 0
assert GF(p)(E.a4()) == GF(p)(-1) and GF(p)(E.a6()) == GF(p)(-2)
assert a*P+b*Q == E(0)
assert base(GF(p)(P[0]), GF(p)(P[1])) == U
assert base(GF(p)(Q[0]), GF(p)(Q[1])) == V
assert a*U+b*V == base(0)
recovered = ((a*t1+b*t2)*pow((a+b)%q,-1,q))%q
assert recovered == hit["recovered_scalar"]
assert recovered*G == target
receipt = {"status": "PASS", "field_prime": p, "subgroup_order": q,
           "curve": {"A": hit["A"], "B": hit["B"], "discriminant": str(E.discriminant())},
           "lifted_points": hit["lifted_points"], "vector": hit["vector"],
           "public_points": [[int(U[0]), int(U[1])], [int(V[0]), int(V[1])]],
           "target": [int(target[0]), int(target[1])], "recovered_scalar": recovered,
           "rational_relation": True, "both_reductions_match": True, "scalar_replay": True}
(HERE / "hit-sage-audit.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
print(json.dumps(receipt, sort_keys=True))
