"""Confirm the exact integer relation lattice for the frozen p1009 row families."""
from pathlib import Path
from sage.all import GF, ZZ, EllipticCurve, matrix
import gzip
import hashlib
import json
import time

H = Path(__file__).resolve().parent
P = json.loads((H / "protocol.json").read_text())
pre = json.loads((H / "pre-run.json").read_text())
protocol_hash = hashlib.sha256((H / "protocol.json").read_bytes()).hexdigest()
assert pre["protocol_sha256"] == protocol_hash and pre["frozen_before_confirmation"]
started = time.monotonic()
ledger_raw = (H / P["corrected_ledger"]).resolve().read_bytes()
assert hashlib.sha256(ledger_raw).hexdigest() == P["corrected_ledger_sha256"]
fiber = sorted((r for r in (json.loads(s) for s in gzip.decompress(ledger_raw).splitlines())
                if r["p"] == P["p"] and r["status"] == "regular"
                and r["abs_trace"] == P["fiber_abs_trace"]),
               key=lambda r: (r["x"], r["y"]))
assert len(fiber) == P["expected_fiber_size"]
E = EllipticCurve(GF(P["p"]), [0, -1, 1, -10, -20])
assert int(E.cardinality()) == P["curve_order"]
points = [E(r["x"], r["y"]) for r in fiber]
generator_index = next(i for i, Q in enumerate(points) if int(Q.order()) == P["curve_order"])
generator = points[generator_index]
assert generator_index == 0

prior = H.parent / "hecke-x011-p1009-degree2-rank-20261119"
direct_packed = (prior / "direct-rows.jsonl.gz").read_bytes()
assert hashlib.sha256(direct_packed).hexdigest() == P["direct_rows_gzip_sha256"]
direct = [dict(zip(r["indices"], r["coefficients"]))
          for r in (json.loads(s) for s in gzip.decompress(direct_packed).splitlines())]
degree3 = H.parent / "hecke-x011-p1009-degree3-rank-20261119"
prior_result_raw = (degree3 / "result.json").read_bytes()
assert hashlib.sha256(prior_result_raw).hexdigest() == P["degree3_result_sha256"]
prior_result = json.loads(prior_result_raw)
assert [r["point"] for r in prior_result["source_records"]] == [[int(Q[0]), int(Q[1])] for Q in points]
hecke_packed = (degree3 / "hecke-rows.jsonl.gz").read_bytes()
assert hashlib.sha256(hecke_packed).hexdigest() == P["degree3_rows_gzip_sha256"]
hecke = [{int(k): int(v) for k, v in r["row"].items()}
         for r in (json.loads(s) for s in gzip.decompress(hecke_packed).splitlines())]
assert len(direct) == 568 and len(hecke) == 28
rows = hecke + direct
for row in rows:
    assert sum((v * points[k] for k, v in row.items()), E(0)) == E(0)
assert time.monotonic() - started < P["resource_cap_seconds"]
M = matrix(ZZ, [[row.get(i, 0) for i in range(84)] for row in rows])
t = time.monotonic()
elementary = [int(x) for x in M.elementary_divisors()]
snf_seconds = time.monotonic() - t
nonzero = [abs(x) for x in elementary if x]
assert len(nonzero) == 84
assert nonzero[:-1] == [1] * 83 and nonzero[-1] == 1020
index = 1
for x in nonzero:
    index *= x
assert index == P["curve_order"]
assert time.monotonic() - started < P["resource_cap_seconds"]
t = time.monotonic()
raw_hnf = M.hermite_form()
basis = matrix(ZZ, [list(row) for row in raw_hnf.rows() if any(row)])
hnf_seconds = time.monotonic() - t
assert basis.nrows() == basis.ncols() == 84
basis_det = abs(int(basis.det()))
assert basis_det == index
basis_bytes = (json.dumps([[int(x) for x in row] for row in basis.rows()],
                          separators=(",", ":")) + "\n").encode()
(H / "hnf-basis.json").write_bytes(basis_bytes)
result = {"schema": "x011-p1009-relation-lattice-result-v1", "status": "complete",
          "protocol_sha256": protocol_hash, "point_count": len(points),
          "row_counts": {"degree3": len(hecke), "direct": len(direct)},
          "matrix_shape": [int(M.nrows()), int(M.ncols())],
          "matrix_rank": len(nonzero), "smith_nonunit_factors": [x for x in nonzero if x != 1],
          "smith_zero_count": len(elementary) - len(nonzero),
          "lattice_index": index, "hnf_basis_determinant": basis_det,
          "hnf_basis_sha256": hashlib.sha256(basis_bytes).hexdigest(),
          "curve_order": int(E.cardinality()), "generator_index": generator_index,
          "generator_point": [int(generator[0]), int(generator[1])],
          "generator_order": int(generator.order()),
          "stage_seconds": {"smith": round(snf_seconds, 3), "hermite": round(hnf_seconds, 3)},
          "candidate_id": None, "target_online_ms": None}
(H / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps({"lattice_index": index, "smith_nonunit_factors": result["smith_nonunit_factors"],
                  "generator_index": generator_index, "generator_order": result["generator_order"]}, sort_keys=True))
