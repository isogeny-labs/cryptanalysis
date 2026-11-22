"""Independent exact norm check and finite-field replay of the v2 correction."""
from pathlib import Path
from sage.all import ZZ, GF, PolynomialRing, EllipticCurve
import gzip
import hashlib
import json

H = Path(__file__).resolve().parent
source = json.loads((H / "jfun.json").read_text())
R = PolynomialRing(ZZ, "X")
X = R.gen()
a = sum(ZZ(n) * X**i for i, j, (n, d) in source["A_terms"] if j == 0 and d == 1)
b = sum(ZZ(n) * X**i for i, j, (n, d) in source["A_terms"] if j == 1 and d == 1)
assert len(source["A_terms"]) == sum(1 for _, _, (_, d) in source["A_terms"] if d == 1)
rhs = X**3 - X**2 - 10*X - 20
norm = a*a - a*b - b*b*rhs
quotient, remainder = norm.quo_rem((X - 16)**11)
assert remainder == 0
assert a(16) + 60*b(16) == 0
conjugate = a(16) - 61*b(16)
assert conjugate != 0
assert quotient(16) == -121*conjugate

old = [json.loads(line) for line in gzip.open(H / "points.jsonl.gz", "rt")]
new = [json.loads(line) for line in gzip.open(H / "points_v2.jsonl.gz", "rt")]
assert len(old) == len(new) == 2222
changed = []
for before, after in zip(old, new):
    assert (before["p"], before["x"], before["y"]) == (after["p"], after["x"], after["y"])
    if before != after:
        p = before["p"]
        assert (before["x"], before["y"], before["status"]) == (16, 60, "x16_denominator_zero")
        assert after["j"] == -121 % p
        assert after["status"] == "regular"
        F = GF(p)
        j = F(after["j"])
        k = j / (F(1728) - j)
        curve = EllipticCurve(F, [0, 0, 0, 3*k, 2*k])
        assert abs(p + 1 - curve.cardinality()) == after["abs_trace"]
        changed.append({"p": p, "j": after["j"], "abs_trace": after["abs_trace"]})
assert [x["p"] for x in changed] == [317, 941, 1009]
result = json.loads((H / "result_v2.json").read_text())
assert result["replaced"] == [{"p": r["p"], "point": [16, 60], "j": r["j"], "abs_trace": r["abs_trace"]} for r in changed]
assert hashlib.sha256((H / "points_v2.jsonl.gz").read_bytes()).hexdigest() == result["ledger_gzip_sha256"]
receipt = {"schema": "x011-trace-fiber-audit-v2", "status": "PASS", "exact_j_at_16_60": -121,
           "norm_remainder_zero": True, "conjugate_numerator": int(conjugate),
           "changed": changed, "ledger_rows": len(new)}
(H / "audit-v2.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
print(json.dumps(receipt, sort_keys=True))
