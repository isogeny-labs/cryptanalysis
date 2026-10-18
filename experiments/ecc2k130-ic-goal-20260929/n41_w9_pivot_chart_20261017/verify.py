"""Read-only receipt and exact chart-coverage verifier."""
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "protocol.json").read_text())
audit_protocol = json.loads((HERE / "audit_protocol.json").read_text())
result = json.loads((HERE / "result.json").read_text())
audit = json.loads((HERE / "audit_result.json").read_text())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol["sources"].items():
    assert digest(path) == expected, path
for path, expected in audit_protocol["sources"].items():
    assert digest(path) == expected, path
assert result["protocol_sha256"] == digest(HERE / "protocol.json")
assert audit["audit_protocol_sha256"] == digest(HERE / "audit_protocol.json")
assert result["status"] == "PASS_N41_TARGET_PIVOT_CHART_SCREEN"
assert audit["status"] == "PASS_SAGE_LOW_PIVOT_CHART_REPLAY"
assert result["candidate_id"] is None and audit["candidate_id"] is None
assert result["selected_chart_count"] == len(result["selected_charts"]) == 7
assert result["source_table_entries"] == audit["positive_rows_checked"] == 284
assert result["uniform_panel"]["count"] == audit["uniform_rows_checked"] == 1024
assert result["reachable_panel"]["count"] == audit["reachable_rows_checked"] == 256
assert result["uniform_panel"]["fallback_count"] == audit["fallback_uniform"] == 69
assert result["reachable_panel"]["fallback_count"] == audit["fallback_reachable"] == 33
assert result["total_seconds"] <= protocol["wall_cap_seconds"]
assert result["self_maxrss_bytes"] <= protocol["rss_cap_bytes"]
assert math.isclose(sum(result["phase_seconds"].values()), result["total_seconds"], rel_tol=1e-12)

spec = importlib.util.spec_from_file_location("pivot_verifier_field", protocol["field_source"])
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
field = module.Field()
states = json.loads(Path(protocol["states"]).read_text())
fixture = json.loads(Path(protocol["fixture"]).read_text())
table = json.loads(Path(protocol["table"]).read_text())
seed = states["seed"] << 1


def frob(x, count):
    for _ in range(count):
        x = field.square(x)
    return x


h = frob(field.square(field.halftrace(seed)), 24)
c = h ^ 1
t = fixture["public_reciprocal"]
basis = [frob(field.mul((1 << bit) << 1, ((1 << bit) << 1) ^ seed), 24)
         for bit in range(9) if bit != 5]


def rank(rows):
    pivots = {}
    for row in rows:
        while row:
            bit = row.bit_length() - 1
            if bit in pivots:
                row ^= pivots[bit]
            else:
                pivots[bit] = row
                break
    return len(pivots)


charts = [tuple(chart) for chart in result["selected_charts"]]
assert len(set(charts)) == 7
assert all(len(set(chart)) == 8 and all(0 <= bit < 41 for bit in chart) for chart in charts)
counts = [0] * 7
for entry in table:
    w = entry["w"]
    b = field.mul(t, w)
    a0 = 1 ^ field.square(b)
    d = field.square(t) ^ field.square(w)
    m = field.mul(a0, h) ^ field.mul(c, d)
    a = field.mul(a0, d)
    bcoef = field.mul(b, m)
    q = field.square(m) ^ field.mul(field.mul(c, h), field.square(b))
    columns = [field.mul(a, field.square(value)) ^ field.mul(bcoef, value)
               for value in basis]
    rows = [sum(((column >> i) & 1) << j for j, column in enumerate(columns))
            for i in range(41)]
    code = entry["code"]
    assert all(((row & code).bit_count() & 1) == ((q >> i) & 1)
               for i, row in enumerate(rows))
    first = next((i for i, chart in enumerate(charts)
                  if rank([rows[j] for j in chart]) == 8), None)
    assert first is not None
    counts[first] += 1
assert counts == result["selected_positive_gains"]
assert counts == [result["positive_first_valid_chart_counts"][str(i)] for i in range(7)]
for stream in ("run", "audit"):
    assert (HERE / f"{stream}.stderr").stat().st_size == 0
    assert (HERE / f"{stream}.stdout").stat().st_size > 0
print("PASS_PIVOT_CHART_RECEIPT", json.dumps({"counts": counts,
      "uniform_fallback": 69, "reachable_fallback": 33}, sort_keys=True))
