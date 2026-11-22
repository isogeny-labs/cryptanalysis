"""Independent source, quartic, neighbor, and rank replay for the p1009 degree-three run."""
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
spec = importlib.util.spec_from_file_location("hecke11_p1009_degree3_audit", source)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
funcs, jfun = mod.build([3])
R = mod.Reduced(P["p"], funcs, jfun, [3])
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
phi = classical_modular_polynomial(3)
patterns = Counter()
statuses = Counter()
rows = []
root_counts = []
for i, (Q, saved) in enumerate(zip(points, result["source_records"])):
    assert saved["source"] == i and saved["point"] == [int(Q[0]), int(Q[1])]
    assert R.j(Q) == R.Fp(fiber[i]["j"])
    s = [None] + [R.funcs[(3, "x", k)](Q[0], Q[1]) for k in range(1, 5)]
    e1 = s[1]
    e2 = (s[1]**2 - s[2]) / 2
    e3 = (s[1]**3 - 3*s[1]*s[2] + 2*s[3]) / 6
    e4 = (s[1]**4 - 6*s[1]**2*s[2] + 3*s[2]**2 + 8*s[1]*s[3] - 6*s[4]) / 24
    T = R.PT.gen()
    poly = T**4 - e1*T**3 + e2*T**2 - e3*T + e4
    assert [int(c) for c in poly.list()] == saved["quartic"]
    pattern = [[int(f.degree()), int(m)] for f, m in poly.factor()]
    assert pattern == saved["factor_pattern"]
    rational_count = sum(int(m) for _, m in poly.roots())
    assert rational_count == saved["rational_root_count"]
    root_counts.append(rational_count)
    patterns[str(pattern)] += 1
    if rational_count < 4:
        assert pattern == [[1, 1], [3, 1]]
        status = "INCOMPLETE_RATIONAL_NEIGHBORS"
    else:
        assert rational_count == 4 and pattern == [[1, 1]] * 4
        nb = R.neighbours_all(3, Q)
        assert nb is not None and len(nb) == 4
        assert sum(nb, E(0)) == R.a_l[3] * Q
        assert sorted(int(T[0]) for T in nb) == sorted(int(x) for x, _ in poly.roots())
        for k in range(1, 5):
            assert sum(T[0]**k for T in nb) == s[k]
        for k in range(4):
            assert sum(T[1]*T[0]**k for T in nb) == R.funcs[(3, "xy", k)](Q[0], Q[1])
        assert all(R.j(T) is not None and phi(R.j(Q), R.j(T)) == 0 for T in nb)
        assert all(T in index for T in nb)
        row = Counter(index[T] for T in nb)
        row[i] -= R.a_l[3]
        row = {k: int(v) for k, v in row.items() if v}
        assert sum((v*points[k] for k, v in row.items()), E(0)) == E(0)
        assert {str(k): v for k, v in sorted(row.items())} == saved["row"]
        rows.append(row)
        status = "CLASS_CLOSED"
    assert saved["status"] == status
    statuses[status] += 1
assert dict(patterns) == result["factor_patterns"]
assert dict(statuses) == result["hecke_statuses"]
assert len(rows) == result["hecke_rows"] == 28
packed = (H / "hecke-rows.jsonl.gz").read_bytes()
assert hashlib.sha256(packed).hexdigest() == result["hecke_rows_gzip_sha256"]
saved_rows = [json.loads(s) for s in gzip.decompress(packed).splitlines()]
assert saved_rows == [{"source": r["source"], "row": r["row"]}
                      for r in result["source_records"] if r["status"] == "CLASS_CLOSED"]
previous = H.parent / "hecke-x011-p1009-degree2-rank-20261119"
direct_records = [json.loads(s) for s in gzip.decompress((previous / "direct-rows.jsonl.gz").read_bytes()).splitlines()]
direct = [dict(zip(r["indices"], r["coefficients"])) for r in direct_records]
assert all(sum((v*points[k] for k, v in row.items()), E(0)) == E(0) for row in direct)


def rank(rs, ring):
    return int(matrix(ring, [[row.get(i, 0) for i in range(84)] for row in rs]).rank())


ranks = {"degree3_only": {"QQ": rank(rows, QQ), "F17": rank(rows, GF(17))},
         "direct_only": {"QQ": rank(direct, QQ), "F17": rank(direct, GF(17))},
         "degree3_plus_direct": {"QQ": rank(rows+direct, QQ),
                                 "F17": rank(rows+direct, GF(17))}}
assert ranks == result["ranks"]
direct_matrix = matrix(QQ, [[row.get(i, 0) for i in range(84)] for row in direct])
kernel_basis = direct_matrix.right_kernel().basis()
assert len(kernel_basis) == 1
kernel = [int(x) for x in kernel_basis[0]]
assert all(QQ(x) == y for x, y in zip(kernel, kernel_basis[0]))
assert set(kernel) == {0, 1}
assert all(sum(v*kernel[k] for k, v in row.items()) == 0 for row in direct)
gain_source = next(r["source"] for r in result["source_records"]
                   if r["status"] == "CLASS_CLOSED"
                   and sum(int(v)*kernel[int(k)] for k, v in r["row"].items()) != 0)
gain_row = next(r for r in result["source_records"] if r["source"] == gain_source)
gain_dot = sum(int(v)*kernel[int(k)] for k, v in gain_row["row"].items())
assert gain_source == 2 and gain_dot == 5
witness = {"schema": "x011-p1009-degree3-qq-rank-witness-v1", "direct_kernel": kernel,
           "direct_rows_checked": len(direct), "gain_source": gain_source,
           "gain_row": gain_row["row"], "gain_dot": gain_dot}
witness_bytes = (json.dumps(witness, sort_keys=True, separators=(",", ":")) + "\n").encode()
(H / "rank-witness.json").write_bytes(witness_bytes)
projected = [60 * Q for Q in points]
S = next(T for T in projected if T != E(0))
assert int(S.order()) == 17
log_table = {k*S: k for k in range(17)}
assert len(log_table) == 17
projection_vector = [log_table[T] for T in projected]
assert any(projection_vector)
assert all(sum(v*projection_vector[k] for k, v in row.items()) % 17 == 0
           for row in rows + direct)
projection = {"schema": "x011-p1009-degree3-f17-projection-v1",
              "generator": [int(S[0]), int(S[1])], "projection_multiplier": 60,
              "modulus": 17, "vector": projection_vector,
              "checked_rows": len(rows) + len(direct)}
projection_bytes = (json.dumps(projection, sort_keys=True, separators=(",", ":")) + "\n").encode()
(H / "projection.json").write_bytes(projection_bytes)
audit = {"schema": "x011-p1009-degree3-rank-audit-v1", "status": "PASS",
         "result_sha256": post["producer_result_sha256"],
         "factor_patterns": dict(patterns), "hecke_statuses": dict(statuses),
         "root_counts": dict(Counter(str(c) for c in root_counts)), "ranks": ranks,
         "projection_sha256": hashlib.sha256(projection_bytes).hexdigest(),
         "rank_witness_sha256": hashlib.sha256(witness_bytes).hexdigest()}
(H / "audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": "PASS", "root_counts": audit["root_counts"], "ranks": ranks}, sort_keys=True))
