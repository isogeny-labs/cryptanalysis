"""Search and evaluate exact pivot charts for the target-conditioned code map."""
import hashlib
import importlib.util
import json
import random
import resource
import signal
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
p = json.loads((HERE / "protocol.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in p["sources"].items():
    assert sha(path) == expected, path
assert not (HERE / "result.json").exists()
assert p["curve_id"] == "EC1N41Ckb1h7d5e80d3c4d0"
assert p["random_chart_count"] == 4096


def timeout(_signum, _frame):
    raise TimeoutError("frozen N41 pivot-chart screen cap")


signal.signal(signal.SIGALRM, timeout)
signal.alarm(p["wall_cap_seconds"])
started = time.monotonic()
spec = importlib.util.spec_from_file_location("n41_field", p["field_source"])
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
F = module.Field()
source = json.loads(Path(p["states"]).read_text())
fixture = json.loads(Path(p["fixture"]).read_text())
table = json.loads(Path(p["table"]).read_text())
panel = json.loads(Path(p["panel"]).read_text())
assert len(table) == 284 and len({row["w"] for row in table}) == 284
assert len(panel["uniform"]) == 1024 and len(panel["reachable"]) == 256
seed = source["seed"] << 1


def frob(x, count):
    for _ in range(count):
        x = F.square(x)
    return x


H = frob(F.square(F.halftrace(seed)), 24)
C = H ^ 1
t = fixture["public_reciprocal"]
basis = [frob(F.mul((1 << bit) << 1, ((1 << bit) << 1) ^ seed), 24)
         for bit in range(9) if bit != 5]
assert len(basis) == 8
allowed_codes = set(json.loads(Path(p["wires"]).read_text())["allowed_code_words"])


def rank(masks):
    pivots = {}
    for mask in masks:
        while mask:
            pivot = mask.bit_length()-1
            if pivot in pivots:
                mask ^= pivots[pivot]
            else:
                pivots[pivot] = mask
                break
    return len(pivots)


def matrix(w):
    B = F.mul(t, w)
    A = 1 ^ F.square(B)
    D = F.square(t) ^ F.square(w)
    M = F.mul(A, H) ^ F.mul(C, D)
    a = F.mul(A, D)
    b = F.mul(B, M)
    q = F.square(M) ^ F.mul(F.mul(C, H), F.square(B))
    cols = [F.mul(a, F.square(value)) ^ F.mul(b, value) for value in basis]
    rows = tuple(sum(((col >> i) & 1) << j for j, col in enumerate(cols))
                 for i in range(41))
    return rows, q


def pivot_chart(rows):
    selected = []
    independent = []
    for i, row in enumerate(rows):
        if rank(independent+[row]) > len(independent):
            selected.append(i)
            independent.append(row)
        if len(selected) == 8:
            break
    assert len(selected) == 8
    return tuple(selected)


positive = [matrix(row["w"]) for row in table]
assert all(rank(rows) == 8 for rows, _ in positive)
matrices_end = time.monotonic()

rng = random.Random(p["random_seed"])
charts = {pivot_chart(rows) for rows, _ in positive}
canonical_count = len(charts)
for _ in range(p["random_chart_count"]):
    charts.add(tuple(sorted(rng.sample(range(41), 8))))
charts = sorted(charts)
coverage = {}
for chart in charts:
    mask = 0
    for i, (rows, _) in enumerate(positive):
        if rank([rows[j] for j in chart]) == 8:
            mask |= 1 << i
    coverage[chart] = mask
all_positives = (1 << len(table)) - 1
remaining = all_positives
selected = []
while remaining:
    chart = max(charts, key=lambda item:
                ((coverage[item] & remaining).bit_count(),
                 coverage[item].bit_count(), item))
    gain = (coverage[chart] & remaining).bit_count()
    assert gain > 0
    selected.append(chart)
    remaining &= ~coverage[chart]

# Remove any row set made redundant by later selected charts.
for chart in reversed(selected.copy()):
    trial = [item for item in selected if item != chart]
    mask = 0
    for item in trial:
        mask |= coverage[item]
    if mask == all_positives:
        selected = trial
assert len(set(selected)) == len(selected)
covered = 0
gains = []
for chart in selected:
    gain = (coverage[chart] & ~covered).bit_count()
    gains.append(gain)
    covered |= coverage[chart]
assert covered == all_positives
portfolio_end = time.monotonic()


def solve_rows(rows, q, chart):
    pivots = {}
    rhs = {}
    for i in chart:
        mask = rows[i]
        value = (q >> i) & 1
        while mask:
            bit = mask.bit_length()-1
            if bit in pivots:
                mask ^= pivots[bit]
                value ^= rhs[bit]
            else:
                pivots[bit] = mask
                rhs[bit] = value
                break
        assert mask
    assert len(pivots) == 8
    code = 0
    for bit in range(8):
        value = rhs[bit] ^ ((pivots[bit] & code).bit_count() & 1)
        code |= value << bit
    matches = all((((rows[i] & code).bit_count() & 1) == ((q >> i) & 1))
                  for i in range(41))
    return [code] if matches else []


def decode(w):
    rows, q = matrix(w)
    assert rank(rows) == 8
    for chart_index, chart in enumerate(selected):
        if rank([rows[j] for j in chart]) == 8:
            codes = solve_rows(rows, q, chart)
            return codes, chart_index, False
    chart = pivot_chart(rows)
    codes = solve_rows(rows, q, chart)
    return codes, None, True


positive_first = Counter()
for entry in table:
    codes, chart_index, fallback = decode(entry["w"])
    assert not fallback and codes == [entry["code"]]
    positive_first[str(chart_index)] += 1


def check_panel(rows):
    first = Counter()
    fallback_count = 0
    image_hits = 0
    allowed_hits = 0
    for entry in rows:
        codes, chart_index, fallback = decode(entry["w"])
        assert codes == entry["linear_image_codes"]
        assert [code for code in codes if code in allowed_codes] == entry["allowed_codes"]
        fallback_count += fallback
        first[str(chart_index)] += 1
        image_hits += bool(codes)
        allowed_hits += bool(entry["allowed_codes"])
    return {"count": len(rows), "fallback_count": fallback_count,
            "first_valid_chart_counts": dict(first),
            "linear_image_hits": image_hits,
            "allowed_code_hits": allowed_hits}


uniform = check_panel(panel["uniform"])
reachable = check_panel(panel["reachable"])
finished = time.monotonic()
signal.alarm(0)
result = {"status": "PASS_N41_TARGET_PIVOT_CHART_SCREEN",
          "curve_id": p["curve_id"], "candidate_id": None,
          "source_table_entries": len(table),
          "source_codes": len(allowed_codes),
          "canonical_chart_count": canonical_count,
          "candidate_chart_count": len(charts),
          "best_single_chart_coverage": max(mask.bit_count() for mask in coverage.values()),
          "selected_chart_count": len(selected),
          "selected_charts": [list(chart) for chart in selected],
          "selected_positive_gains": gains,
          "positive_first_valid_chart_counts": dict(positive_first),
          "uniform_panel": uniform, "reachable_panel": reachable,
          "phase_seconds": {"source_and_matrices": matrices_end-started,
                            "chart_portfolio": portfolio_end-matrices_end,
                            "decoding_and_controls": finished-portfolio_end},
          "total_seconds": finished-started,
          "self_maxrss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          "protocol_sha256": sha(HERE / "protocol.json")}
(HERE / "result.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
print(json.dumps({k:result[k] for k in ("status","candidate_chart_count",
                                        "selected_chart_count",
                                        "selected_positive_gains",
                                        "uniform_panel","reachable_panel",
                                        "total_seconds")},sort_keys=True))
