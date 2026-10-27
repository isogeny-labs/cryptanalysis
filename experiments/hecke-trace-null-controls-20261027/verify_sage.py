"""Independent checked-Sage replay of all frozen null panels."""
import hashlib
import json
import math
from collections import Counter
from fractions import Fraction
from pathlib import Path

from sage.all import EllipticCurve, GF

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
I = json.loads((HERE / "inputs.json").read_text())
R = json.loads((HERE / "result.json").read_text())
assert R["domain"] == I["domain"] and R["panels_per_case"] == I["panels_per_case"] == 4096


def key(P):
    return None if P.is_zero() else (int(P[0]), int(P[1]))


def build_group(p, N):
    E = EllipticCurve(GF(p), [0, -1, 1, -10, -20])
    assert int(E.order()) == N
    points = [E(0)] + sorted((P for P in E.points() if not P.is_zero()), key=key)
    assert len(points) == N
    indexes = {key(P): i for i, P in enumerate(points)}
    inverses = [indexes[key(-P)] for P in points]
    table = [[0]*N for _ in range(N)]
    for i, P in enumerate(points):
        for j in range(i, N):
            k = indexes[key(P+points[j])]
            table[i][j] = table[j][i] = k
    return inverses, table


def draw(domain, p, panel, slot, N):
    modulus = N-1
    ceiling = (2**64 // modulus)*modulus
    counter = 0
    while True:
        message = (domain + "|" + str(p) + "|" + str(panel) + "|" +
                   str(slot) + "|" + str(counter)).encode()
        value = int.from_bytes(hashlib.sha256(message).digest()[0:8], "big")
        if value < ceiling:
            return 1 + value % modulus
        counter += 1


def recount(values, inverses, table):
    # Suffix frequencies avoid the producer's inner triple loop.
    m = len(values)
    suffix = [Counter() for _ in range(m)]
    later = Counter()
    for j in range(m-1, -1, -1):
        suffix[j] = later.copy()
        later[values[j]] += 1
    single = sum(v == 0 for v in values)
    pair = triple = 0
    for i in range(m):
        for j in range(i+1, m):
            plus = table[values[i]][values[j]]
            minus = table[values[i]][inverses[values[j]]]
            pair += int(plus == 0) + int(minus == 0)
            for s in (plus, minus):
                triple += suffix[j][s] + suffix[j][inverses[s]]
    return [single, pair, triple]


summary = []
for input_case, saved in zip(I["cases"], R["cases"], strict=True):
    p, N = input_case["p"], input_case["group_order"]
    source_bytes = (ROOT / input_case["search_receipt"]).read_bytes()
    assert hashlib.sha256(source_bytes).hexdigest() == input_case["sha256"]
    source = json.loads(source_bytes)
    m = source["outside_sources"]
    assert saved["p"] == p and saved["group_order"] == N
    assert saved["outside_sources"] == m and saved["observed_counts"] == source["candidate_counts"]
    inverses, table = build_group(p, N)
    panels = []
    for panel in range(4096):
        values = [draw(I["domain"], p, panel, slot, N) for slot in range(m)]
        panels.append(recount(values, inverses, table))
    assert panels == saved["panel_counts"]
    means = [Fraction(0), Fraction(2*math.comb(m, 2), N-1),
             Fraction(4*math.comb(m, 3)*(N-2), (N-1)**2)]
    for support in (1, 2, 3):
        i = support-1
        values = sorted(row[i] for row in panels)
        expected = saved["summary"][str(support)]
        mu = means[i]
        observed = source["candidate_counts"][str(support)]
        exceed = sum(abs(Fraction(v)-mu) >= abs(Fraction(observed)-mu)
                     for v in values)
        assert expected["mean_exact"] == f"{mu.numerator}/{mu.denominator}"
        assert expected["panel_mean_exact"] == f"{sum(values)}/4096"
        assert expected["interval_2p5_50_97p5"] == [values[4095//40],
                                                       values[4095//2],
                                                       values[39*4095//40]]
        assert expected["tail_exact"] == f"{1+exceed}/4097"
    summary.append({"p": p, "panels_replayed": 4096,
                    "candidate_counts": source["candidate_counts"],
                    "support3_mean": saved["summary"]["3"]["mean_exact"],
                    "support3_tail": saved["summary"]["3"]["tail_exact"]})

V = {"schema": "hecke-trace-null-controls-validation-v1",
     "status": "PASS", "cases": summary,
     "total_panels_replayed": 3*4096,
     "group_arithmetic": "independent Sage EllipticCurve(GF(p), [0,-1,1,-10,-20])",
     "count_algorithm": "suffix-frequency pair sums"}
(HERE / "validation.json").write_text(json.dumps(V, indent=2, sort_keys=True) + "\n")
print("HECKE_TRACE_NULL_CONTROLS_PASS", "panels", 3*4096)
