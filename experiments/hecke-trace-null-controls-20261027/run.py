"""Deterministic nonidentity-group null panels for short trace-sum counts."""
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
INPUTS = json.loads((HERE / "inputs.json").read_text())


def on_curve(P, p):
    if P is None:
        return True
    x, y = P
    return (y*y+y-x*x*x+x*x+10*x+20) % p == 0


def neg(P, p):
    return None if P is None else (P[0], (-P[1]-1) % p)


def add(P, Q, p):
    if P is None:
        return Q
    if Q is None:
        return P
    x, y = P
    u, v = Q
    if x == u and (y+v+1) % p == 0:
        return None
    if P == Q:
        top, bottom = 3*x*x-2*x-10, 2*y+1
    else:
        top, bottom = v-y, u-x
    slope = top*pow(bottom % p, -1, p) % p
    intercept = (y-slope*x) % p
    X = (slope*slope+1-x-u) % p
    Y = (-slope*X-intercept-1) % p
    R = X, Y
    assert on_curve(R, p)
    return R


def group_tables(p, expected_order):
    points = [None] + [(x, y) for x in range(p) for y in range(p)
                       if on_curve((x, y), p)]
    assert len(points) == expected_order and expected_order % 2 == 1
    index = {P: i for i, P in enumerate(points)}
    assert len(index) == len(points)
    inverse = [index[neg(P, p)] for P in points]
    table = [[0] * len(points) for _ in points]
    for i, P in enumerate(points):
        for j in range(i, len(points)):
            k = index[add(P, points[j], p)]
            table[i][j] = table[j][i] = k
    assert all(table[i][inverse[i]] == 0 for i in range(len(points)))
    return inverse, table


def sample_index(domain, p, panel, slot, n):
    width = n - 1
    limit = ((1 << 64) // width) * width
    retry = 0
    while True:
        payload = f"{domain}|{p}|{panel}|{slot}|{retry}".encode("utf-8")
        value = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
        if value < limit:
            return 1 + value % width
        retry += 1


def counts(values, inverse, table):
    n = len(values)
    singles = 0
    pairs = 0
    triples = 0
    for i in range(n):
        a = values[i]
        if a == 0:
            singles += 1
        for j in range(i+1, n):
            b = values[j]
            plus = table[a][b]
            minus = table[a][inverse[b]]
            pairs += (plus == 0) + (minus == 0)
            inv_plus = inverse[plus]
            inv_minus = inverse[minus]
            for k in range(j+1, n):
                c = values[k]
                triples += (c == plus) + (c == inv_plus) + (c == minus) + (c == inv_minus)
    return [singles, pairs, triples]


def summarize(panel_rows, observed, m, N):
    assert len(panel_rows) == INPUTS["panels_per_case"]
    means = [Fraction(0), Fraction(2*math.comb(m, 2), N-1),
             Fraction(4*math.comb(m, 3)*(N-2), (N-1)**2)]
    output = {}
    R = len(panel_rows)
    for support in (1, 2, 3):
        i = support-1
        values = sorted(row[i] for row in panel_rows)
        center = means[i]
        threshold = abs(Fraction(observed[str(support)])-center)
        exceed = sum(abs(Fraction(v)-center) >= threshold for v in values)
        output[str(support)] = {
            "observed": observed[str(support)],
            "mean_exact": f"{center.numerator}/{center.denominator}",
            "panel_mean_exact": f"{sum(values)}/{R}",
            "interval_2p5_50_97p5": [values[(R-1)//40], values[(R-1)//2],
                                      values[39*(R-1)//40]],
            "tail_exact": f"{1+exceed}/{R+1}",
            "below_or_equal_observed": sum(v <= observed[str(support)] for v in values),
            "above_or_equal_observed": sum(v >= observed[str(support)] for v in values)
        }
    return output


def main():
    out = {"schema": "hecke-trace-null-controls-v1",
           "domain": INPUTS["domain"],
           "panels_per_case": INPUTS["panels_per_case"],
           "cases": [], "candidate_id": None, "target_online_ms": None}
    for case in INPUTS["cases"]:
        source_bytes = (ROOT / case["search_receipt"]).read_bytes()
        assert hashlib.sha256(source_bytes).hexdigest() == case["sha256"]
        source = json.loads(source_bytes)
        p, N = case["p"], case["group_order"]
        assert source["p"] == p
        m = source["outside_sources"]
        observed = source["candidate_counts"]
        inverse, table = group_tables(p, N)
        panels = []
        for panel in range(INPUTS["panels_per_case"]):
            values = [sample_index(INPUTS["domain"], p, panel, slot, N)
                      for slot in range(m)]
            panels.append(counts(values, inverse, table))
        summary = summarize(panels, observed, m, N)
        out["cases"].append({"p": p, "group_order": N, "outside_sources": m,
                             "source_receipt_sha256": case["sha256"],
                             "observed_counts": observed,
                             "summary": summary,
                             "panel_counts": panels})
        print(json.dumps({"p": p, "m": m, "N": N,
                          "observed": observed,
                          "support3_mean": summary["3"]["mean_exact"],
                          "support3_tail": summary["3"]["tail_exact"]},
                         sort_keys=True), flush=True)
    (HERE / "result.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
