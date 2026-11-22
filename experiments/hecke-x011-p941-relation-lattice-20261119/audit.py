"""Independent pure-Python curve and SymPy integer-lattice confirmation."""
from pathlib import Path
from sympy import Matrix, ZZ, __version__ as sympy_version
from sympy.matrices.normalforms import smith_normal_form
import flint
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
    return (y*y+y-x*x*x+x*x+10*x+20) % p == 0


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
    slope = top*pow(bottom % p, -1, p) % p
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
    curve_count += len(square_roots.get((1+4*rhs) % p, ()))
assert curve_count == result["curve_order"] == P["curve_order"] == 900
ledger = (H / P["corrected_ledger"]).resolve().read_bytes()
assert hashlib.sha256(ledger).hexdigest() == P["corrected_ledger_sha256"]
fiber = sorted((r for r in (json.loads(s) for s in gzip.decompress(ledger).splitlines())
                if r["p"] == p and r["status"] == "regular"
                and r["abs_trace"] == P["fiber_abs_trace"]),
               key=lambda r: (r["x"], r["y"]))
points = [(r["x"], r["y"]) for r in fiber]
assert len(points) == result["point_count"] == P["expected_fiber_size"]
assert all(on_curve(A) for A in points)
i, j = P["generating_pair_indices"]
A, B = points[i], points[j]
assert [list(A), list(B)] == P["generating_pair_points"]
assert mul(180, A) is None and all(mul(180//q, A) is not None for q in [2, 3, 5])
assert mul(60, B) is None and all(mul(60//q, B) is not None for q in [2, 3, 5])
span = {add(mul(a, A), mul(b, B)) for a in range(180) for b in range(60)}
assert len(span) == result["generating_pair_span"] == 900

prior = H.parent / "hecke-x011-p941-trace18-hecke-rank-20261119"
prior_raw = (prior / "result.json").read_bytes()
assert hashlib.sha256(prior_raw).hexdigest() == P["rank_experiment_result_sha256"]
prior_result = json.loads(prior_raw)
assert [r["point"] for r in prior_result["source_records"]["2"]] == [list(Q) for Q in points]
direct_packed = (prior / "direct-rows.jsonl.gz").read_bytes()
assert hashlib.sha256(direct_packed).hexdigest() == P["direct_rows_gzip_sha256"]
direct = [dict(zip(r["indices"], r["coefficients"]))
          for r in (json.loads(s) for s in gzip.decompress(direct_packed).splitlines())]
hecke_packed = (prior / "hecke2-rows.jsonl.gz").read_bytes()
assert hashlib.sha256(hecke_packed).hexdigest() == P["degree2_rows_gzip_sha256"]
hecke = [{int(k): int(v) for k, v in r["row"].items()}
         for r in (json.loads(s) for s in gzip.decompress(hecke_packed).splitlines())]
rows = hecke + direct
assert len(hecke) == 56 and len(direct) == 1529
for row in rows:
    total = None
    for k, v in row.items():
        total = add(total, mul(v, points[k]))
    assert total is None
assert time.monotonic() - started < P["resource_cap_seconds"]

M = Matrix([[row.get(k, 0) for k in range(112)] for row in rows])
smith = smith_normal_form(M, domain=ZZ)
diagonal = [abs(int(smith[k, k])) for k in range(112)]
assert diagonal == [1]*110 + [5, 180]
F = flint.fmpz_mat([[row.get(k, 0) for k in range(112)] for row in rows])
F_smith = F.snf()
assert [abs(int(F_smith[k, k])) for k in range(112)] == diagonal
F_hnf = F.hnf()
nonzero_rows = [i for i in range(F_hnf.nrows())
                if any(F_hnf[i, k] for k in range(F_hnf.ncols()))]
assert len(nonzero_rows) == 112
F_basis = flint.fmpz_mat([[F_hnf[i, k] for k in range(112)] for i in nonzero_rows])
hnf_det = abs(int(F_basis.det()))
assert hnf_det == 900 == result["hnf_basis_determinant"] == result["lattice_index"]
basis_raw = (H / "hnf-basis.json").read_bytes()
assert hashlib.sha256(basis_raw).hexdigest() == result["hnf_basis_sha256"]
basis = json.loads(basis_raw)
assert len(basis) == 112 and all(len(row) == 112 for row in basis)
assert all(basis[i][j] == 0 for i in range(112) for j in range(i))
basis_det = 1
for i in range(112):
    basis_det *= basis[i][i]
assert abs(basis_det) == 900
audit = {"schema": "x011-p941-relation-lattice-audit-v1", "status": "PASS",
         "result_sha256": post["producer_result_sha256"],
         "sympy_version": sympy_version, "flint_version": flint.__version__,
         "curve_count": curve_count, "generating_pair_span": len(span),
         "rows_checked": len(rows), "smith_nonunit_factors": [5, 180],
         "independent_hnf_determinant": hnf_det}
(H / "audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": "PASS", "curve_count": curve_count,
                  "pair_span": len(span), "rows_checked": len(rows), "index": hnf_det}, sort_keys=True))
