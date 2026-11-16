"""Fixed-prime quotient certificate for every admitted rational lift pair."""
import gzip
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing, QQ

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "xedni-varying-curve-selection-20261115" / "rows-v2.jsonl.gz"
EXPECTED = "9a594d96f369fb14f1a4cf6270b1c811ceda515e1c2a7eccab4d011ca8f3f322"
assert hashlib.sha256(PARENT.read_bytes()).hexdigest() == EXPECTED
with gzip.open(PARENT, "rt") as stream:
    source = [json.loads(line) for line in stream]
assert len(source) == 1722
R = PolynomialRing(QQ, "t")
t = R.gen()
records = []
for index, row in enumerate(source):
    if not row["accepted"]:
        continue
    A, B = QQ(row["A"]), QQ(row["B"])
    roots = (t**3 + A*t + B).roots(ring=QQ)
    checks = []
    for prime in (7, 11):
        if A.denominator() % prime == 0 or B.denominator() % prime == 0:
            checks.append({"prime": prime, "status": "nonintegral"})
            continue
        F = GF(prime)
        a, b = F(A), F(B)
        if 4*a**3 + 27*b**2 == 0:
            checks.append({"prime": prime, "status": "bad_reduction"})
            continue
        E = EllipticCurve(F, [a, b])
        p, q = [E(F(x), F(y)) for x, y in row["lifted_points"]]
        doubles = {2*T for T in E.points()}
        tests = [p not in doubles, q not in doubles, p+q not in doubles]
        checks.append({"prime": prime, "status": "complete", "curve_order": int(E.cardinality()),
                       "point_orders": [int(p.order()), int(q.order())],
                       "quotient_nonzero_tests": tests, "quotient_independent": all(tests)})
    certificate = next((c["prime"] for c in checks if c.get("quotient_independent")), None)
    records.append({"parent_row_index": index, "A": str(A), "B": str(B),
                    "lifted_points": row["lifted_points"],
                    "reduced_relation": row["reduced_relation"],
                    "rational_relation": row["rational_relation"],
                    "rational_2_torsion_x_roots": [str(root) for root, _ in roots],
                    "prime_checks": checks, "certificate_prime": certificate})
assert len(records) == 20
result = {"schema": "xedni-auxiliary-mod2-independence-result-v2",
          "parent_rows_sha256": EXPECTED, "population": len(source),
          "accepted_rows": len(records),
          "certified_rows": sum(r["certificate_prime"] is not None and not r["rational_2_torsion_x_roots"] for r in records),
          "certificates_by_prime": {str(p): sum(r["certificate_prime"] == p for r in records) for p in (7, 11)},
          "reduced_relation_certified_rows": sum(r["reduced_relation"] and r["certificate_prime"] is not None for r in records),
          "uncertified_parent_indices": [r["parent_row_index"] for r in records
                                         if r["certificate_prime"] is None or r["rational_2_torsion_x_roots"]]}
(HERE / "rows-v2.json").write_text(json.dumps(records, indent=2, sort_keys=True) + "\n")
(HERE / "result-v2.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, indent=2, sort_keys=True))
