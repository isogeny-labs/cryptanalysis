"""Confirm the second fixed-prime interval on all 31 v1 unresolved rows."""
import hashlib
import json
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ, prime_range

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "xedni-optimized-family-lift-replay-20261115"
protocol = json.loads((HERE / "protocol-v2.json").read_text())
assert hashlib.sha256((HERE / "result.json").read_bytes()).hexdigest() == protocol["parent_v1_result_sha256"]
assert hashlib.sha256((HERE / "rows.jsonl").read_bytes()).hexdigest() == protocol["parent_v1_rows_sha256"]
v1 = json.loads((HERE / "result.json").read_text())
assert v1["status"] == "complete" and v1["cumulative_certified"] == 9657
unresolved = [r for r in map(json.loads, (HERE / "rows.jsonl").open()) if r["status"] == "torsion_only"]
assert len(unresolved) == 31
PRIMES = [int(p) for p in prime_range(503, 998)]
deadline = time.monotonic() + protocol["run_cap_seconds"]
raw_by_path = {}
for row in unresolved:
    path = row["source_path"]
    if path not in raw_by_path:
        raw_by_path[path] = [json.loads(line) for line in (PARENT / path).open()]

out_rows = []
for old in unresolved:
    if time.monotonic() >= deadline:
        break
    source = raw_by_path[old["source_path"]][old["source_ordinal_zero_based"]]
    assert source["query_index_one_based"] == old["query_index_one_based"]
    assert source["vector"] == old["vector"]
    coefficients = [QQ(c) for c in source["coefficients"]]
    E = EllipticCurve(QQ, coefficients)
    first = None
    checks = []
    for prime in PRIMES:
        if any(c.denominator() % prime == 0 for c in coefficients):
            checks.append({"prime": prime, "status": "nonintegral"})
            continue
        F = GF(prime)
        if F(E.discriminant()) == 0:
            checks.append({"prime": prime, "status": "bad_reduction"})
            continue
        curve = EllipticCurve(F, [F(c) for c in coefficients])
        order = int(curve.cardinality())
        tests = None
        if order % 4 == 0:
            P, Q = [curve(F(x), F(y)) for x, y in source["points"]]
            doubles = {2*T for T in curve.points()}
            tests = [P not in doubles, Q not in doubles, P+Q not in doubles]
            if all(tests):
                first = prime
        checks.append({"prime": prime, "status": "complete", "curve_order": order,
                       "quotient_nonzero_tests": tests})
        if first is not None:
            break
    out_rows.append({"source_path": old["source_path"], "source_ordinal_zero_based": old["source_ordinal_zero_based"],
                     "query_index_one_based": source["query_index_one_based"], "vector": source["vector"],
                     "inherited_odd_order_prime": old["inherited_odd_order_prime"],
                     "quotient_prime": first, "status": "certified_independent" if first is not None else "torsion_only",
                     "prime_checks": checks})
    print(old["source_path"], old["source_ordinal_zero_based"], first, flush=True)
with (HERE / "rows-v2.jsonl").open("w") as stream:
    for row in out_rows:
        stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
result = {"schema": "xedni-crt-extended-quotient-result-v2",
          "status": "complete" if len(out_rows) == 31 else "capped_300s",
          "parent_v1_result_sha256": protocol["parent_v1_result_sha256"],
          "parent_v1_rows_sha256": protocol["parent_v1_rows_sha256"],
          "prime_count": len(PRIMES), "first_prime": PRIMES[0], "last_prime": PRIMES[-1],
          "unresolved_input_rows": len(unresolved), "processed_rows": len(out_rows),
          "new_certificates": sum(r["status"] == "certified_independent" for r in out_rows),
          "still_torsion_only": sum(r["status"] == "torsion_only" for r in out_rows),
          "cumulative_certified": v1["cumulative_certified"] + sum(r["status"] == "certified_independent" for r in out_rows),
          "rows_sha256": hashlib.sha256((HERE / "rows-v2.jsonl").read_bytes()).hexdigest()}
(HERE / "result-v2.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, indent=2, sort_keys=True))
