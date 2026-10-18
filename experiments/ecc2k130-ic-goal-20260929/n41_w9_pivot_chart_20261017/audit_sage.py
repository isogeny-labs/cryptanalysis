"""Independent Sage field and low-pivot replay of N41 chart decoding."""
import hashlib
import json
import resource
import time
from collections import Counter
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ap = json.loads((HERE / "audit_protocol.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in ap["sources"].items():
    assert sha(path) == expected, path
assert not (HERE / "audit_result.json").exists()
started = time.monotonic()
p = json.loads((HERE / "protocol.json").read_text())
result = json.loads((HERE / "result.json").read_text())
source = json.loads(Path(p["states"]).read_text())
fixture = json.loads(Path(p["fixture"]).read_text())
table = json.loads(Path(p["table"]).read_text())
panel = json.loads(Path(p["panel"]).read_text())
assert result["status"] == "PASS_N41_TARGET_PIVOT_CHART_SCREEN"
assert result["protocol_sha256"] == sha(HERE / "protocol.json")
charts = [tuple(chart) for chart in result["selected_charts"]]
assert len(charts) == result["selected_chart_count"]
assert len(set(charts)) == len(charts)
assert all(len(chart) == len(set(chart)) == 8 and
           all(0 <= bit < 41 for bit in chart) for chart in charts)

K = PolynomialRing(GF(2), "u")
u = K.gen()
F = GF(2**41, name="u", modulus=u**41 + u**3 + 1)


def dec(number):
    return F(K([(int(number) >> i) & 1 for i in range(41)]))


def enc(value):
    return sum(int(coef) << i for i, coef in enumerate(value.polynomial().list()))


seed = dec(source["seed"] << 1)
half = F(0)
term = seed
for _ in range(21):
    half += term
    term = term**4
assert half**2+half == seed
H = (half**2)**(2**24)
C = 1+H
t = dec(fixture["public_reciprocal"])
basis = [(dec((1 << bit) << 1)*dec(((1 << bit) << 1) ^
          (source["seed"] << 1)))**(2**24)
         for bit in range(9) if bit != 5]
allowed = set(json.loads(Path(p["wires"]).read_text())["allowed_code_words"])


def matrix(w_int):
    w = dec(w_int)
    B = t*w
    A = 1+B**2
    D = t**2+w**2
    M = A*H+C*D
    a = A*D
    b = B*M
    q = M**2+C*H*B**2
    cols = [enc(a*value**2+b*value) for value in basis]
    return [sum(((col >> i) & 1) << j for j,col in enumerate(cols))
            for i in range(41)], enc(q)


def low_pivot_solve(rows, q, indices):
    matrix_rows = [[rows[i], (q >> i) & 1] for i in indices]
    assert len(matrix_rows) == 8
    for column in range(8):
        pivot = next((j for j in range(column, 8)
                      if (matrix_rows[j][0] >> column) & 1), None)
        if pivot is None:
            return None
        matrix_rows[column], matrix_rows[pivot] = (
            matrix_rows[pivot], matrix_rows[column])
        for j in range(8):
            if j != column and (matrix_rows[j][0] >> column) & 1:
                matrix_rows[j][0] ^= matrix_rows[column][0]
                matrix_rows[j][1] ^= matrix_rows[column][1]
    assert [row[0] for row in matrix_rows] == [1 << i for i in range(8)]
    code = sum(row[1] << i for i,row in enumerate(matrix_rows))
    return code


def first_valid(rows, q):
    for index, chart in enumerate(charts):
        code = low_pivot_solve(rows, q, chart)
        if code is not None:
            return index, code
    return None, None


positive_counts = Counter()
for entry in table:
    rows, q = matrix(entry["w"])
    chart_index, code = first_valid(rows, q)
    assert chart_index is not None and code == entry["code"]
    assert all(((rows[i] & code).bit_count() & 1) == ((q >> i) & 1)
               for i in range(41))
    positive_counts[str(chart_index)] += 1
assert dict(positive_counts) == result["positive_first_valid_chart_counts"]


def check_panel(entries, receipt):
    first = Counter()
    for entry in entries:
        rows, q = matrix(entry["w"])
        chart_index, code = first_valid(rows, q)
        first[str(chart_index)] += 1
        if chart_index is None:
            # A chart outside the portfolio can still solve the full-rank map.
            selected = []
            for i in range(41):
                candidate = selected+[i]
                if len(candidate) <= 8 and independent([rows[j] for j in candidate]):
                    selected = candidate
                if len(selected) == 8:
                    break
            assert len(selected) == 8
            code = low_pivot_solve(rows, q, selected)
        matches = all(((rows[i] & code).bit_count() & 1) == ((q >> i) & 1)
                      for i in range(41))
        codes = [code] if matches else []
        assert codes == entry["linear_image_codes"]
        assert [value for value in codes if value in allowed] == entry["allowed_codes"]
    assert dict(first) == receipt["first_valid_chart_counts"]
    assert first["None"] == receipt["fallback_count"]


def independent(masks):
    pivots = {}
    for mask in masks:
        while mask:
            bit = (mask & -mask).bit_length()-1
            if bit in pivots:
                mask ^= pivots[bit]
            else:
                pivots[bit] = mask
                break
    return len(pivots) == len(masks)


check_panel(panel["uniform"], result["uniform_panel"])
check_panel(panel["reachable"], result["reachable_panel"])
audit = {"status": "PASS_SAGE_LOW_PIVOT_CHART_REPLAY",
         "curve_id": result["curve_id"], "candidate_id": None,
         "positive_rows_checked": len(table),
         "uniform_rows_checked": len(panel["uniform"]),
         "reachable_rows_checked": len(panel["reachable"]),
         "selected_chart_count": len(charts),
         "fallback_uniform": result["uniform_panel"]["fallback_count"],
         "fallback_reachable": result["reachable_panel"]["fallback_count"],
         "elapsed_seconds": time.monotonic()-started,
         "self_maxrss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         "audit_protocol_sha256": sha(HERE / "audit_protocol.json")}
(HERE / "audit_result.json").write_text(json.dumps(audit,sort_keys=True,indent=2)+"\n")
print(json.dumps(audit,sort_keys=True))
