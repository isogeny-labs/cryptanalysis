"""Frozen p941 trace-18 Hecke degree-2/3 closure and direct-relation ranks."""
from collections import Counter
from pathlib import Path
from sage.all import GF, QQ, classical_modular_polynomial, matrix
import gzip
import hashlib
import importlib.util
import itertools
import json
import os
import time

H = Path(__file__).resolve().parent
P = json.loads((H / "protocol.json").read_text())
pre = json.loads((H / "pre-run.json").read_text())
protocol_hash = hashlib.sha256((H / "protocol.json").read_bytes()).hexdigest()
assert pre["protocol_sha256"] == protocol_hash and pre["frozen_before_producer"]
started = time.monotonic()
p = P["p"]
source = Path(os.environ.get("ARCHIVE_ROOT", "/Volumes/SSD990/cryptanalysis")) / "experiments/hecke-d1407-f6-20261023/regularized/tools/hecke11.py"
assert hashlib.sha256(source.read_bytes()).hexdigest() == P["regularized_hecke_source_sha256"]
spec = importlib.util.spec_from_file_location("hecke11_p941_trace18", source)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
t = time.monotonic()
funcs, jfun = mod.build([2, 3])
build_seconds = time.monotonic() - t
R = mod.Reduced(p, funcs, jfun, [2, 3])
E = R.E
assert int(E.cardinality()) == P["curve_order"]
ledger = (H / P["corrected_ledger"]).resolve().read_bytes()
assert hashlib.sha256(ledger).hexdigest() == P["corrected_ledger_sha256"]
fiber = sorted((r for r in (json.loads(s) for s in gzip.decompress(ledger).splitlines())
                if r["p"] == p and r["status"] == "regular"
                and r["abs_trace"] == P["fiber_abs_trace"]),
               key=lambda r: (r["x"], r["y"]))
assert len(fiber) == P["expected_fiber_size"]
points = [E(r["x"], r["y"]) for r in fiber]
index = {Q: i for i, Q in enumerate(points)}
assert len(index) == len(points)
for r, Q in zip(fiber, points):
    assert R.j(Q) == R.Fp(r["j"])


def rank(rows, ring):
    if not rows:
        return 0
    return int(matrix(ring, [[row.get(i, 0) for i in range(len(points))] for row in rows]).rank())


records = {}
hecke = {}
statuses = {}
patterns = {}
scan_times = {}
for ell in P["hecke_degrees"]:
    t = time.monotonic()
    phi = classical_modular_polynomial(ell)
    current = []
    rows = []
    st = Counter()
    pat = Counter()
    for i, Q in enumerate(points):
        poly = R.neighbour_x(ell, Q)
        assert poly.degree() == ell + 1
        factors = [[int(f.degree()), int(m)] for f, m in poly.factor()]
        assert sum(d*m for d, m in factors) == ell + 1
        rational_count = sum(int(m) for _, m in poly.roots())
        entry = {"source": i, "point": [int(Q[0]), int(Q[1])],
                 "polynomial": [int(c) for c in poly.list()],
                 "factor_pattern": factors, "rational_root_count": rational_count}
        if rational_count != ell + 1:
            entry["status"] = "INCOMPLETE_RATIONAL_NEIGHBORS"
        else:
            nb = R.neighbours_all(ell, Q)
            if nb is None:
                entry["status"] = "AMBIGUOUS_RATIONAL_RECONSTRUCTION"
            else:
                assert len(nb) == ell + 1 and sum(nb, E(0)) == R.a_l[ell] * Q
                js = [R.j(T) for T in nb]
                if any(j is None for j in js):
                    entry["status"] = "CUSP_NEIGHBOR"
                else:
                    assert all(phi(R.j(Q), j) == 0 for j in js)
                    if any(T not in index for T in nb):
                        entry["status"] = "OUTSIDE_FROZEN_FIBER"
                    else:
                        row = Counter(index[T] for T in nb)
                        row[i] -= R.a_l[ell]
                        row = {k: int(v) for k, v in row.items() if v}
                        assert sum((v*points[k] for k, v in row.items()), E(0)) == E(0)
                        entry["status"] = "CLASS_CLOSED"
                        entry["row"] = {str(k): v for k, v in sorted(row.items())}
                        rows.append(row)
        st[entry["status"]] += 1
        pat[str(factors)] += 1
        current.append(entry)
        assert time.monotonic() - started < P["resource_cap_seconds"]
    records[str(ell)] = current
    hecke[ell] = rows
    statuses[str(ell)] = dict(st)
    patterns[str(ell)] = dict(pat)
    scan_times[str(ell)] = round(time.monotonic() - t, 3)
    row_bytes = b"".join(json.dumps({"source": r["source"], "row": r["row"]},
                                    sort_keys=True, separators=(",", ":")).encode() + b"\n"
                         for r in current if r["status"] == "CLASS_CLOSED")
    (H / f"hecke{ell}-rows.jsonl.gz").write_bytes(gzip.compress(row_bytes, compresslevel=9, mtime=0))


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
    assert (Y*Y+Y-X*X*X+X*X+10*X+20) % p == 0
    return (X, Y)


coords = [(int(Q[0]), int(Q[1])) for Q in points]
direct_records = []
direct = []
direct_counts = Counter()
t = time.monotonic()
for support in range(1, 4):
    for inds in itertools.combinations(range(len(points)), support):
        for tail in itertools.product((-1, 1), repeat=support-1):
            signs = (1,) + tail
            total = None
            for k, sign in zip(inds, signs):
                total = add(total, coords[k] if sign == 1 else neg(coords[k]))
            if total is not None:
                continue
            row = dict(zip(inds, signs))
            assert sum((v*points[k] for k, v in row.items()), E(0)) == E(0)
            direct_records.append({"indices": list(inds), "coefficients": list(signs)})
            direct.append(row)
            direct_counts[support] += 1
    assert time.monotonic() - started < P["resource_cap_seconds"]
direct_seconds = time.monotonic() - t
direct_bytes = b"".join(json.dumps(r, sort_keys=True, separators=(",", ":")).encode() + b"\n"
                        for r in direct_records)
direct_packed = gzip.compress(direct_bytes, compresslevel=9, mtime=0)
(H / "direct-rows.jsonl.gz").write_bytes(direct_packed)

t = time.monotonic()
families = {"direct_only": direct, "degree2_only": hecke[2], "degree3_only": hecke[3],
            "degree2_plus_direct": hecke[2]+direct,
            "degree3_plus_direct": hecke[3]+direct,
            "degree2_degree3_plus_direct": hecke[2]+hecke[3]+direct}
rings = {"QQ": QQ, "F2": GF(2), "F3": GF(3), "F5": GF(5)}
ranks = {name: {field: rank(rows, ring) for field, ring in rings.items()}
         for name, rows in families.items()}
rank_seconds = time.monotonic() - t
result = {"schema": "x011-p941-trace18-hecke-rank-result-v1", "status": "complete",
          "protocol_sha256": protocol_hash, "p": p, "fiber_size": len(points),
          "source_records": records, "factor_patterns": patterns, "hecke_statuses": statuses,
          "hecke_rows": {str(ell): len(hecke[ell]) for ell in hecke},
          "hecke_rows_gzip_sha256": {str(ell): hashlib.sha256((H / f"hecke{ell}-rows.jsonl.gz").read_bytes()).hexdigest() for ell in hecke},
          "direct_counts": {str(k): direct_counts[k] for k in range(1, 4)},
          "direct_rows_gzip_sha256": hashlib.sha256(direct_packed).hexdigest(),
          "ranks": ranks,
          "stage_seconds": {"function_build": round(build_seconds, 3), "hecke_scan": scan_times,
                            "direct_enumeration": round(direct_seconds, 3),
                            "matrix_ranks": round(rank_seconds, 3)},
          "candidate_id": None, "target_online_ms": None}
(H / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps({"hecke_statuses": statuses, "direct_counts": result["direct_counts"],
                  "ranks": ranks}, sort_keys=True))
