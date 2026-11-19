"""Independent checked-Sage replay of the trace-fiber point ledger."""
from collections import Counter
from pathlib import Path
import hashlib
import json
from sage.all import EllipticCurve, GF

H = Path(__file__).resolve().parent
P = json.loads((H / "protocol.json").read_text())
R = json.loads((H / "result.json").read_text())
assert hashlib.sha256((H / "protocol.json").read_bytes()).hexdigest() == R["protocol_sha256"]
source = H / P["j_source"]
blob = source.read_bytes()
assert hashlib.sha256(blob).hexdigest() == P["j_source_sha256"]
terms = json.loads(blob)["A_terms"]
raw = (H / "points.jsonl").read_bytes()
assert hashlib.sha256(raw).hexdigest() == R["ledger_sha256"]
ledger = [json.loads(line) for line in raw.splitlines()]
assert len(ledger) == R["ledger_rows"]

for item in R["summary"]:
    p = item["p"]
    F = GF(p)
    E = EllipticCurve(F, [0, -1, 1, -10, -20])
    assert int(E.cardinality()) == item["x011_points"]
    saved = {(row["x"], row["y"]): row for row in ledger if row["p"] == p}
    assert len(saved) == item["x011_points"] - 1
    counts = Counter()
    exceptions = Counter({"infinity": 1})
    orders = {}
    for point in E.points():
        if point.is_zero():
            continue
        x, y = F(point[0]), F(point[1])
        row = saved.pop((int(x), int(y)))
        if x == F(16):
            assert row["status"] == "x16_denominator_zero"
            exceptions[row["status"]] += 1
            continue
        A = sum((F(num) / F(den)) * x**ax * y**ay
                for ax, ay, (num, den) in terms)
        j = A / (x - 16)**11
        assert int(j) == row["j"]
        if j == 0 or j == F(1728):
            assert row["status"] == "extra_twist_j"
            exceptions[row["status"]] += 1
            continue
        if j not in orders:
            k = j / (F(1728) - j)
            C = EllipticCurve(F, [0, 0, 0, 3*k, 2*k])
            assert C.j_invariant() == j
            orders[j] = int(C.cardinality())
        trace = abs(p + 1 - orders[j])
        assert row["status"] == "regular" and row["abs_trace"] == trace
        counts[trace] += 1
    assert not saved
    assert dict(exceptions) == item["exceptions"]
    assert {str(t): n for t, n in sorted(counts.items())} == item["trace_histogram"]
    assert len(orders) == item["distinct_regular_j"]

receipt = {"schema": "x011-trace-fiber-audit-v1", "status": "PASS",
           "primes": P["primes"], "ledger_rows": len(ledger),
           "result_sha256": hashlib.sha256((H / "result.json").read_bytes()).hexdigest()}
(H / "audit-result.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
print(json.dumps(receipt, sort_keys=True))
