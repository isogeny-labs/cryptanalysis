"""Partition regular X_0(11)(F_p) points by absolute source trace."""
from collections import Counter, defaultdict
from pathlib import Path
import gzip
import hashlib
import json
import time

H = Path(__file__).resolve().parent
P = json.loads((H / "protocol.json").read_text())
source = H / P["j_source"]
blob = source.read_bytes()
assert hashlib.sha256(blob).hexdigest() == P["j_source_sha256"]
cache = json.loads(blob)
terms = cache["A_terms"]
started = time.monotonic()


def modrat(pair, p):
    n, d = pair
    assert d % p
    return n * pow(d, -1, p) % p


def curve_order_from_j(j, p):
    assert j % p not in (0, 1728 % p)
    k = j * pow((1728 - j) % p, -1, p) % p
    a, b = 3 * k % p, 2 * k % p
    assert 1728 * 4 * pow(a, 3, p) * pow((4 * pow(a, 3, p) + 27 * b * b) % p, -1, p) % p == j
    total = 1
    for x in range(p):
        v = (x*x*x + a*x + b) % p
        total += 1 if v == 0 else 2 if pow(v, (p-1)//2, p) == 1 else 0
    return total


ledger = []
summary = []
for p in P["primes"]:
    rhs_to_ys = defaultdict(list)
    for y in range(p):
        rhs_to_ys[(y*y+y) % p].append(y)
    points = [(x, y) for x in range(p)
              for y in rhs_to_ys[(x*x*x-x*x-10*x-20) % p]]
    total_points = len(points) + 1
    j_orders = {}
    trace_counts = Counter()
    exceptions = Counter({"infinity": 1})
    distinct_j = set()
    for x, y in points:
        row = {"p": p, "x": x, "y": y}
        if x == modrat(cache["x0"], p):
            row["status"] = "x16_denominator_zero"
            exceptions[row["status"]] += 1
        else:
            num = sum(modrat(coeff, p) * pow(x, ax, p) * pow(y, ay, p)
                      for ax, ay, coeff in terms) % p
            den = pow((x - 16) % p, 11, p)
            j = num * pow(den, -1, p) % p
            row["j"] = j
            if j in (0, 1728 % p):
                row["status"] = "extra_twist_j"
                exceptions[row["status"]] += 1
            else:
                if j not in j_orders:
                    j_orders[j] = curve_order_from_j(j, p)
                order = j_orders[j]
                trace = abs(p + 1 - order)
                row.update({"status": "regular", "abs_trace": trace})
                trace_counts[trace] += 1
                distinct_j.add(j)
        ledger.append(row)
    assert sum(trace_counts.values()) + sum(exceptions.values()) == total_points
    archived = next((x for x in P["archived_trace_targets"] if x["p"] == p), None)
    summary.append({"p": p, "x011_points": total_points,
                    "regular_points": sum(trace_counts.values()),
                    "distinct_regular_j": len(distinct_j),
                    "abs_trace_fibers": len(trace_counts),
                    "max_abs_trace_fiber": max(trace_counts.values()),
                    "trace_histogram": {str(k): v for k, v in sorted(trace_counts.items())},
                    "exceptions": dict(exceptions),
                    "archived_trace_fiber": None if archived is None else {
                        "abs_trace": archived["abs_trace"],
                        "full_fiber_points": trace_counts[archived["abs_trace"]],
                        "archived_class_points": archived["archived_class_points"]}})
    assert time.monotonic() - started < P["resource_cap_seconds"]

raw = "".join(json.dumps(x, sort_keys=True, separators=(",", ":")) + "\n" for x in ledger)
packed = gzip.compress(raw.encode(), compresslevel=9, mtime=0)
(H / "points.jsonl.gz").write_bytes(packed)
result = {"schema": "x011-trace-fiber-result-v1", "status": "complete",
          "protocol_sha256": hashlib.sha256((H / "protocol.json").read_bytes()).hexdigest(),
          "source_sha256": P["j_source_sha256"],
          "ledger_sha256": hashlib.sha256(raw.encode()).hexdigest(),
          "ledger_gzip_sha256": hashlib.sha256(packed).hexdigest(),
          "ledger_gzip_bytes": len(packed),
          "ledger_rows": len(ledger), "summary": summary,
          "elapsed_wall_seconds": round(time.monotonic() - started, 3)}
(H / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps({"summary": [{k: v for k, v in s.items() if k != "trace_histogram"}
                               for s in summary], "elapsed_wall_seconds": result["elapsed_wall_seconds"]}, indent=2))
