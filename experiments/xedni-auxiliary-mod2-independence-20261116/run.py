"""Exact finite-field and rational 2-torsion audit of the frozen selected lifts."""
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing, QQ

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "xedni-varying-curve-selection-20261115" / "rows-v2.jsonl.gz"
EXPECTED = "9a594d96f369fb14f1a4cf6270b1c811ceda515e1c2a7eccab4d011ca8f3f322"
assert hashlib.sha256(PARENT.read_bytes()).hexdigest() == EXPECTED
with gzip.open(PARENT, "rt") as stream:
    rows = [json.loads(line) for line in stream]
assert len(rows) == 1722
F7, F47 = GF(7), GF(47)
base = EllipticCurve(F47, [-1, -2])
assert base.cardinality() == 43
R = PolynomialRing(QQ, "t")
t = R.gen()
curves = {}
audit = []
for index, row in enumerate(rows):
    if not row["accepted"]:
        continue
    A, B = QQ(row["A"]), QQ(row["B"])
    E = EllipticCurve(QQ, [A, B])
    E7 = EllipticCurve(F7, [F7(A), F7(B)])
    assert E7.cardinality() == row["aux_order"] == 4
    assert F47(A) == F47(-1) and F47(B) == F47(-2)
    P, Q = [E(x, y) for x, y in row["lifted_points"]]
    p7, q7 = [E7(F7(x), F7(y)) for x, y in row["lifted_points"]]
    p47, q47 = [base(F47(x), F47(y)) for x, y in row["lifted_points"]]
    assert [[int(T[0]), int(T[1])] for T in (p47, q47)] == row["reduced_points"]
    roots = (t**3 + A*t + B).roots(ring=QQ)
    key = (str(A), str(B))
    curves[key] = {"A": str(A), "B": str(B), "rational_2_torsion_x_roots": [str(root) for root, _ in roots],
                   "mod7_curve_order": int(E7.cardinality()), "mod47_curve_order": 43}
    audit.append({"parent_row_index": index, "A": str(A), "B": str(B),
                  "lifted_points": row["lifted_points"], "reduced_relation": row["reduced_relation"],
                  "rational_relation": row["rational_relation"],
                  "mod7_points": [[int(T[0]), int(T[1])] for T in (p7, q7)],
                  "mod7_orders": [int(p7.order()), int(q7.order())],
                  "mod7_distinct": bool(p7 != q7),
                  "rational_2_torsion_x_roots": [str(root) for root, _ in roots],
                  "frozen_relation_replay": bool((P + 2*Q).is_zero())})
assert len(audit) == 20
summary = {"schema": "xedni-auxiliary-mod2-independence-result-v1",
           "parent_rows_sha256": EXPECTED, "total_rows": len(rows),
           "parent_statuses": dict(Counter(row["status"] for row in rows)),
           "accepted_rows": len(audit), "accepted_reduced_relations": sum(a["reduced_relation"] for a in audit),
           "accepted_rational_relations": sum(a["rational_relation"] for a in audit),
           "mod7_independent_pair_rows": sum(a["mod7_orders"] == [2, 2] and a["mod7_distinct"] for a in audit),
           "rational_2_torsion_free_curve_count": sum(not c["rational_2_torsion_x_roots"] for c in curves.values()),
           "curves": list(curves.values())}
(HERE / "rows.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
(HERE / "result.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
print(json.dumps(summary, indent=2, sort_keys=True))
