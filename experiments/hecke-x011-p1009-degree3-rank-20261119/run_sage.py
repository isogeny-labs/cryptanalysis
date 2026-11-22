"""Frozen degree-three Hecke closure and exact-rank experiment on X011/F1009."""
from collections import Counter
from pathlib import Path
from sage.all import GF, QQ, classical_modular_polynomial, matrix
import gzip
import hashlib
import importlib.util
import json
import os
import time

H = Path(__file__).resolve().parent
P = json.loads((H / "protocol.json").read_text())
pre = json.loads((H / "pre-run.json").read_text())
protocol_hash = hashlib.sha256((H / "protocol.json").read_bytes()).hexdigest()
assert pre["protocol_sha256"] == protocol_hash and pre["frozen_before_producer"]
started = time.monotonic()
archive = Path(os.environ.get("ARCHIVE_ROOT", "/Volumes/SSD990/cryptanalysis"))
source = archive / "experiments/hecke-d1407-f6-20261023/regularized/tools/hecke11.py"
assert hashlib.sha256(source.read_bytes()).hexdigest() == P["regularized_hecke_source_sha256"]
spec = importlib.util.spec_from_file_location("hecke11_p1009_degree3", source)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
t = time.monotonic()
funcs, jfun = mod.build([3])
build_seconds = time.monotonic() - t
R = mod.Reduced(P["p"], funcs, jfun, [3])
E = R.E
assert int(E.cardinality()) == P["curve_order"]
ledger = (H / P["corrected_ledger"]).resolve().read_bytes()
assert hashlib.sha256(ledger).hexdigest() == P["corrected_ledger_sha256"]
fiber = sorted((r for r in (json.loads(s) for s in gzip.decompress(ledger).splitlines())
                if r["p"] == P["p"] and r["status"] == "regular"
                and r["abs_trace"] == P["fiber_abs_trace"]),
               key=lambda r: (r["x"], r["y"]))
assert len(fiber) == P["expected_fiber_size"]
points = [E(r["x"], r["y"]) for r in fiber]
index = {Q: i for i, Q in enumerate(points)}
assert len(index) == len(points)
for r, Q in zip(fiber, points):
    assert R.j(Q) == R.Fp(r["j"])

previous = H.parent / "hecke-x011-p1009-degree2-rank-20261119"
prev_raw = (previous / "result.json").read_bytes()
assert hashlib.sha256(prev_raw).hexdigest() == P["degree2_result_sha256"]
prev = json.loads(prev_raw)
assert [(int(Q[0]), int(Q[1])) for Q in points] == [tuple(r["point"]) for r in prev["source_records"]]
direct_packed = (previous / "direct-rows.jsonl.gz").read_bytes()
assert hashlib.sha256(direct_packed).hexdigest() == P["degree2_direct_rows_gzip_sha256"]
direct_records = [json.loads(s) for s in gzip.decompress(direct_packed).splitlines()]
assert len(direct_records) == 568
direct = []
for r in direct_records:
    row = dict(zip(r["indices"], r["coefficients"]))
    assert sum((c * points[i] for i, c in row.items()), E(0)) == E(0)
    direct.append(row)


def rank(rows, ring):
    if not rows:
        return 0
    return int(matrix(ring, [[row.get(i, 0) for i in range(len(points))] for row in rows]).rank())


phi = classical_modular_polynomial(3)
statuses = Counter()
factor_patterns = Counter()
source_records = []
hecke = []
t = time.monotonic()
for i, Q in enumerate(points):
    poly = R.neighbour_x(3, Q)
    assert poly.degree() == 4
    factors = [[int(f.degree()), int(m)] for f, m in poly.factor()]
    assert sum(d * m for d, m in factors) == 4
    roots = poly.roots()
    rational_roots = sum(int(m) for _, m in roots)
    entry = {"source": i, "point": [int(Q[0]), int(Q[1])],
             "quartic": [int(c) for c in poly.list()],
             "factor_pattern": factors, "rational_root_count": rational_roots}
    if rational_roots != 4:
        entry["status"] = "INCOMPLETE_RATIONAL_NEIGHBORS"
    else:
        nb = R.neighbours_all(3, Q)
        if nb is None:
            entry["status"] = "AMBIGUOUS_RATIONAL_RECONSTRUCTION"
        else:
            assert len(nb) == 4 and sum(nb, E(0)) == R.a_l[3] * Q
            js = [R.j(T) for T in nb]
            if any(j is None for j in js):
                entry["status"] = "CUSP_NEIGHBOR"
            else:
                assert all(phi(R.j(Q), j) == 0 for j in js)
                if any(T not in index for T in nb):
                    entry["status"] = "OUTSIDE_FROZEN_FIBER"
                else:
                    row = Counter(index[T] for T in nb)
                    row[i] -= R.a_l[3]
                    row = {k: int(v) for k, v in row.items() if v}
                    assert sum((c * points[k] for k, c in row.items()), E(0)) == E(0)
                    entry["status"] = "CLASS_CLOSED"
                    entry["row"] = {str(k): v for k, v in sorted(row.items())}
                    hecke.append(row)
    statuses[entry["status"]] += 1
    factor_patterns[str(factors)] += 1
    source_records.append(entry)
    assert time.monotonic() - started < P["resource_cap_seconds"]
scan_seconds = time.monotonic() - t

t = time.monotonic()
ranks = {"degree3_only": {"QQ": rank(hecke, QQ), "F17": rank(hecke, GF(17))},
         "direct_only": {"QQ": rank(direct, QQ), "F17": rank(direct, GF(17))},
         "degree3_plus_direct": {"QQ": rank(hecke + direct, QQ),
                                 "F17": rank(hecke + direct, GF(17))}}
assert ranks["direct_only"] == prev["ranks"]["direct_only"]
rank_seconds = time.monotonic() - t
row_bytes = b"".join(json.dumps({"source": r["source"], "row": r["row"]},
                                sort_keys=True, separators=(",", ":")).encode() + b"\n"
                     for r in source_records if r["status"] == "CLASS_CLOSED")
packed = gzip.compress(row_bytes, compresslevel=9, mtime=0)
(H / "hecke-rows.jsonl.gz").write_bytes(packed)
result = {"schema": "x011-p1009-degree3-rank-result-v1", "status": "complete",
          "protocol_sha256": protocol_hash, "p": P["p"], "fiber_size": len(points),
          "source_records": source_records, "factor_patterns": dict(factor_patterns),
          "hecke_statuses": dict(statuses), "hecke_rows": len(hecke),
          "hecke_rows_gzip_sha256": hashlib.sha256(packed).hexdigest(),
          "ranks": ranks, "stage_seconds": {"function_build": round(build_seconds, 3),
          "degree3_scan": round(scan_seconds, 3), "matrix_ranks": round(rank_seconds, 3)},
          "candidate_id": None, "target_online_ms": None}
(H / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps({"factor_patterns": result["factor_patterns"],
                  "hecke_statuses": result["hecke_statuses"], "ranks": ranks}, sort_keys=True))
