"""Independent Newton-polynomial, neighbor, direct-index and rank replay."""
from collections import Counter
from pathlib import Path
from sage.all import GF, QQ, classical_modular_polynomial, matrix
import gzip
import hashlib
import importlib.util
import json
import os

H = Path(__file__).resolve().parent
P = json.loads((H / "protocol.json").read_text())
post = json.loads((H / "post-run.json").read_text())
raw = (H / "result.json").read_bytes()
assert hashlib.sha256(raw).hexdigest() == post["producer_result_sha256"]
result = json.loads(raw)
source = Path(os.environ.get("ARCHIVE_ROOT", "/Volumes/SSD990/cryptanalysis")) / "experiments/hecke-d1407-f6-20261023/regularized/tools/hecke11.py"
assert hashlib.sha256(source.read_bytes()).hexdigest() == P["regularized_hecke_source_sha256"]
spec = importlib.util.spec_from_file_location("hecke11_p941_trace18_audit", source)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
funcs, jfun = mod.build([2, 3])
R = mod.Reduced(P["p"], funcs, jfun, [2, 3])
E = R.E
assert int(E.cardinality()) == P["curve_order"]
ledger = (H / P["corrected_ledger"]).resolve().read_bytes()
assert hashlib.sha256(ledger).hexdigest() == P["corrected_ledger_sha256"]
fiber = sorted((r for r in (json.loads(s) for s in gzip.decompress(ledger).splitlines())
                if r["p"] == P["p"] and r["status"] == "regular"
                and r["abs_trace"] == P["fiber_abs_trace"]),
               key=lambda r: (r["x"], r["y"]))
points = [E(r["x"], r["y"]) for r in fiber]
assert len(points) == P["expected_fiber_size"]
index = {Q: i for i, Q in enumerate(points)}
assert len(index) == len(points)


def independent_poly(ell, Q):
    s = [None] + [R.funcs[(ell, "x", k)](Q[0], Q[1]) for k in range(1, ell+2)]
    e1 = s[1]
    e2 = (s[1]**2-s[2])/2
    e3 = (s[1]**3-3*s[1]*s[2]+2*s[3])/6
    T = R.PT.gen()
    if ell == 2:
        return T**3-e1*T**2+e2*T-e3, s
    e4 = (s[1]**4-6*s[1]**2*s[2]+3*s[2]**2+8*s[1]*s[3]-6*s[4])/24
    return T**4-e1*T**3+e2*T**2-e3*T+e4, s


hecke = {}
statuses = {}
patterns = {}
root_histograms = {}
for ell in [2, 3]:
    phi = classical_modular_polynomial(ell)
    rows = []
    st = Counter()
    pat = Counter()
    roots = Counter()
    for i, (Q, saved) in enumerate(zip(points, result["source_records"][str(ell)])):
        assert saved["source"] == i and saved["point"] == [int(Q[0]), int(Q[1])]
        assert R.j(Q) == R.Fp(fiber[i]["j"])
        poly, sums = independent_poly(ell, Q)
        assert [int(c) for c in poly.list()] == saved["polynomial"]
        factor_pattern = [[int(f.degree()), int(m)] for f, m in poly.factor()]
        assert factor_pattern == saved["factor_pattern"]
        root_count = sum(int(m) for _, m in poly.roots())
        assert root_count == saved["rational_root_count"]
        pat[str(factor_pattern)] += 1
        roots[str(root_count)] += 1
        if root_count < ell+1:
            assert saved["status"] == "INCOMPLETE_RATIONAL_NEIGHBORS"
            status = "INCOMPLETE_RATIONAL_NEIGHBORS"
        else:
            nb = R.neighbours_all(ell, Q)
            assert nb is not None and len(nb) == ell+1
            assert sum(nb, E(0)) == R.a_l[ell]*Q
            assert sorted(int(T[0]) for T in nb) == sorted(int(x) for x, _ in poly.roots())
            for k in range(1, ell+2):
                assert sum(T[0]**k for T in nb) == sums[k]
            for k in range(ell+1):
                assert sum(T[1]*T[0]**k for T in nb) == R.funcs[(ell, "xy", k)](Q[0], Q[1])
            assert all(R.j(T) is not None and phi(R.j(Q), R.j(T)) == 0 for T in nb)
            assert all(T in index for T in nb)
            row = Counter(index[T] for T in nb)
            row[i] -= R.a_l[ell]
            row = {k: int(v) for k, v in row.items() if v}
            assert sum((v*points[k] for k, v in row.items()), E(0)) == E(0)
            assert {str(k): v for k, v in sorted(row.items())} == saved["row"]
            rows.append(row)
            status = "CLASS_CLOSED"
        assert saved["status"] == status
        st[status] += 1
    assert dict(st) == result["hecke_statuses"][str(ell)]
    assert dict(pat) == result["factor_patterns"][str(ell)]
    assert len(rows) == result["hecke_rows"][str(ell)]
    packed = (H / f"hecke{ell}-rows.jsonl.gz").read_bytes()
    assert hashlib.sha256(packed).hexdigest() == result["hecke_rows_gzip_sha256"][str(ell)]
    saved_rows = [json.loads(s) for s in gzip.decompress(packed).splitlines()]
    assert saved_rows == [{"source": r["source"], "row": r["row"]}
                          for r in result["source_records"][str(ell)] if r["status"] == "CLASS_CLOSED"]
    hecke[ell] = rows
    statuses[str(ell)] = dict(st)
    patterns[str(ell)] = dict(pat)
    root_histograms[str(ell)] = dict(roots)

# Enumerate the signed direct relations by pair lookup in Sage's point group.
replayed = []
for i, Q in enumerate(points):
    if Q == E(0):
        replayed.append({"indices": [i], "coefficients": [1]})
for i in range(len(points)):
    for j in range(i+1, len(points)):
        for sj in (-1, 1):
            total = points[i] + sj*points[j]
            if total == E(0):
                replayed.append({"indices": [i, j], "coefficients": [1, sj]})
            for sk, target in ((-1, total), (1, -total)):
                k = index.get(target)
                if k is not None and k > j:
                    replayed.append({"indices": [i, j, k], "coefficients": [1, sj, sk]})
replayed.sort(key=lambda r: (len(r["indices"]), r["indices"], r["coefficients"]))
packed = (H / "direct-rows.jsonl.gz").read_bytes()
assert hashlib.sha256(packed).hexdigest() == result["direct_rows_gzip_sha256"]
saved_direct = [json.loads(s) for s in gzip.decompress(packed).splitlines()]
assert replayed == saved_direct
direct_counts = Counter(len(r["indices"]) for r in replayed)
assert {str(k): direct_counts[k] for k in range(1, 4)} == result["direct_counts"]
direct = [dict(zip(r["indices"], r["coefficients"])) for r in replayed]


def rank(rows, ring):
    if not rows:
        return 0
    return int(matrix(ring, [[row.get(i, 0) for i in range(len(points))] for row in rows]).rank())


families = {"direct_only": direct, "degree2_only": hecke[2], "degree3_only": hecke[3],
            "degree2_plus_direct": hecke[2]+direct,
            "degree3_plus_direct": hecke[3]+direct,
            "degree2_degree3_plus_direct": hecke[2]+hecke[3]+direct}
rings = {"QQ": QQ, "F2": GF(2), "F3": GF(3), "F5": GF(5)}
ranks = {name: {field: rank(rows, ring) for field, ring in rings.items()}
         for name, rows in families.items()}
assert ranks == result["ranks"]
audit = {"schema": "x011-p941-trace18-hecke-rank-audit-v1", "status": "PASS",
         "result_sha256": post["producer_result_sha256"],
         "factor_patterns": patterns, "hecke_statuses": statuses,
         "root_histograms": root_histograms, "direct_counts": result["direct_counts"],
         "ranks": ranks}
(H / "audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": "PASS", "root_histograms": root_histograms,
                  "hecke_rows": result["hecke_rows"], "combined_ranks": ranks["degree2_degree3_plus_direct"]}, sort_keys=True))
