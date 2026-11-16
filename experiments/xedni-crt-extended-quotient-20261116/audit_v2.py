"""Independent Python replay of all 31 second-interval certificates."""
import hashlib
import json
from fractions import Fraction
from pathlib import Path

import audit  # Runs the 1,801-row independent v1 audit and exposes its group law.

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE.parent / "xedni-optimized-family-lift-replay-20261115"
protocol = json.loads((HERE / "protocol-v2.json").read_text())
result = json.loads((HERE / "result-v2.json").read_text())
assert hashlib.sha256((HERE / "result.json").read_bytes()).hexdigest() == protocol["parent_v1_result_sha256"]
assert hashlib.sha256((HERE / "rows.jsonl").read_bytes()).hexdigest() == protocol["parent_v1_rows_sha256"]
assert hashlib.sha256((HERE / "rows-v2.jsonl").read_bytes()).hexdigest() == result["rows_sha256"]


def primes(lo, hi):
    from math import isqrt
    return [p for p in range(lo, hi) if p > 1 and all(p % d for d in range(2, isqrt(p)+1))]


prime_list = primes(503, 998)
assert (len(prime_list), prime_list[0], prime_list[-1]) == (result["prime_count"], result["first_prime"], result["last_prime"])
unresolved = [r for r in map(json.loads, (HERE / "rows.jsonl").open()) if r["status"] == "torsion_only"]
rows = [r for r in map(json.loads, (HERE / "rows-v2.jsonl").open())]
assert len(unresolved) == len(rows) == 31
raw_cache = {}
for old, row in zip(unresolved, rows):
    path, ordinal = old["source_path"], old["source_ordinal_zero_based"]
    assert row["source_path"] == path and row["source_ordinal_zero_based"] == ordinal
    if path not in raw_cache:
        raw_cache[path] = [json.loads(line) for line in (ARCHIVE / path).open()]
    raw = raw_cache[path][ordinal]
    assert row["query_index_one_based"] == raw["query_index_one_based"]
    assert row["vector"] == raw["vector"]
    assert row["inherited_odd_order_prime"] == old["inherited_odd_order_prime"]
    coefficients = [Fraction(c) for c in raw["coefficients"]]
    first = None
    checks = row["prime_checks"]
    for prime, check in zip(prime_list, checks):
        assert check["prime"] == prime
        if any(c.denominator % prime == 0 for c in coefficients):
            assert check["status"] == "nonintegral"
            continue
        a = tuple(audit.field(c, prime) for c in coefficients)
        if audit.disc(a, prime) == 0:
            assert check["status"] == "bad_reduction"
            continue
        assert check["status"] == "complete"
        points = audit.finite_points(a, prime)
        order = len(points)+1
        assert check["curve_order"] == order
        tests = None
        if order % 4 == 0:
            doubled = {audit.sum_points(T, T, a, prime) for T in points + [None]}
            P, Q = [tuple(v % prime for v in pair) for pair in raw["points"]]
            assert P in points and Q in points
            tests = [P not in doubled, Q not in doubled, audit.sum_points(P, Q, a, prime) not in doubled]
            if all(tests):
                first = prime
        assert check["quotient_nonzero_tests"] == tests
    assert first == row["quotient_prime"]
    assert row["status"] == "certified_independent" and first is not None
    assert checks[-1]["prime"] == first
assert result["new_certificates"] == 31
assert result["cumulative_certified"] == 9688 and result["still_torsion_only"] == 0
receipt = {"status": "PASS", "rows": 31, "new_certificates": 31,
           "cumulative_certified": 9688,
           "method": "independent Python general Weierstrass point and doubling-set enumeration"}
(HERE / "audit-v2.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
print(json.dumps(receipt, sort_keys=True))
