"""Independent pure-Python group checks and SymPy integer-lattice replay."""
from pathlib import Path
from sympy import Matrix, ZZ, __version__ as sympy_version
from sympy.matrices.normalforms import hermite_normal_form, smith_normal_form
import gzip
import hashlib
import json
import time

H = Path(__file__).resolve().parent
P = json.loads((H / "protocol.json").read_text())
post = json.loads((H / "post-run.json").read_text())
raw = (H / "result.json").read_bytes()
assert hashlib.sha256(raw).hexdigest() == post["producer_result_sha256"]
result = json.loads(raw)
started = time.monotonic()
p = P["p"]


def on_curve(A):
    x, y = A
    return (y*y + y - x*x*x + x*x + 10*x + 20) % p == 0


def neg(A):
    return None if A is None else (A[0], (-A[1]-1) % p)


def add(A, B):
    if A is None:
        return B
    if B is None:
        return A
    x, y = A
    u, v = B
    if x == u and (y+v+1) % p == 0:
        return None
    top, bottom = (3*x*x-2*x-10, 2*y+1) if A == B else (v-y, u-x)
    slope = top * pow(bottom % p, -1, p) % p
    intercept = (y-slope*x) % p
    X = (slope*slope+1-x-u) % p
    Y = (-slope*X-intercept-1) % p
    C = (X, Y)
    assert on_curve(C)
    return C


def mul(n, A):
    if n < 0:
        return mul(-n, neg(A))
    out = None
    while n:
        if n & 1:
            out = add(out, A)
        A = add(A, A)
        n >>= 1
    return out


square_roots = {}
for y in range(p):
    square_roots.setdefault(y*y % p, set()).add(y)
curve_count = 1
for x in range(p):
    rhs = (x*x*x-x*x-10*x-20) % p
    disc = (1+4*rhs) % p
    curve_count += len(square_roots.get(disc, ()))
assert curve_count == P["curve_order"] == result["curve_order"]
ledger_raw = (H / P["corrected_ledger"]).resolve().read_bytes()
assert hashlib.sha256(ledger_raw).hexdigest() == P["corrected_ledger_sha256"]
fiber = sorted((r for r in (json.loads(s) for s in gzip.decompress(ledger_raw).splitlines())
                if r["p"] == p and r["status"] == "regular"
                and r["abs_trace"] == P["fiber_abs_trace"]),
               key=lambda r: (r["x"], r["y"]))
points = [(r["x"], r["y"]) for r in fiber]
assert len(points) == result["point_count"] == P["expected_fiber_size"]
assert all(on_curve(A) for A in points)
G = points[result["generator_index"]]
assert list(G) == result["generator_point"]
assert mul(1020, G) is None
assert all(mul(1020 // q, G) is not None for q in [2, 3, 5, 17])
assert result["generator_order"] == 1020

prior = H.parent / "hecke-x011-p1009-degree2-rank-20261119"
direct_packed = (prior / "direct-rows.jsonl.gz").read_bytes()
assert hashlib.sha256(direct_packed).hexdigest() == P["direct_rows_gzip_sha256"]
direct = [dict(zip(r["indices"], r["coefficients"]))
          for r in (json.loads(s) for s in gzip.decompress(direct_packed).splitlines())]
degree3 = H.parent / "hecke-x011-p1009-degree3-rank-20261119"
degree3_raw = (degree3 / "result.json").read_bytes()
assert hashlib.sha256(degree3_raw).hexdigest() == P["degree3_result_sha256"]
degree3_result = json.loads(degree3_raw)
assert [r["point"] for r in degree3_result["source_records"]] == [list(A) for A in points]
hecke_packed = (degree3 / "hecke-rows.jsonl.gz").read_bytes()
assert hashlib.sha256(hecke_packed).hexdigest() == P["degree3_rows_gzip_sha256"]
hecke = [{int(k): int(v) for k, v in r["row"].items()}
         for r in (json.loads(s) for s in gzip.decompress(hecke_packed).splitlines())]
rows = hecke + direct
assert len(hecke) == 28 and len(direct) == 568
for row in rows:
    total = None
    for i, c in row.items():
        total = add(total, mul(c, points[i]))
    assert total is None
assert time.monotonic() - started < P["resource_cap_seconds"]

M = Matrix([[row.get(i, 0) for i in range(84)] for row in rows])
smith = smith_normal_form(M, domain=ZZ)
diagonal = [abs(int(smith[i, i])) for i in range(84)]
assert diagonal == [1]*83 + [1020]
column_hnf = hermite_normal_form(M.T)
assert column_hnf.shape == (84, 84)
hnf_det = abs(int(column_hnf.det(method="domain-ge")))
assert hnf_det == 1020 == result["hnf_basis_determinant"] == result["lattice_index"]
saved_basis = json.loads((H / "hnf-basis.json").read_text())
assert hashlib.sha256((H / "hnf-basis.json").read_bytes()).hexdigest() == result["hnf_basis_sha256"]
assert abs(int(Matrix(saved_basis).det(method="domain-ge"))) == 1020
audit = {"schema": "x011-p1009-relation-lattice-audit-v1", "status": "PASS",
         "result_sha256": post["producer_result_sha256"], "sympy_version": sympy_version,
         "curve_count": curve_count, "generator_order": 1020, "rows_checked": len(rows),
         "smith_nonunit_factors": [1020], "independent_hnf_determinant": hnf_det}
(H / "audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": "PASS", "curve_count": curve_count,
                  "rows_checked": len(rows), "index": hnf_det}, sort_keys=True))
