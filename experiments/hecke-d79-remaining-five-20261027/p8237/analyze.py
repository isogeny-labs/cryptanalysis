"""Same-receipt direct and Hecke short-relation rank/cost diagnostics."""
import hashlib
import itertools
import json
import math
import resource
import time
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
PLAN = json.loads((HERE / "post_inputs.json").read_text())
raw = (ROOT / PLAN["class_receipt"]).read_bytes()
assert hashlib.sha256(raw).hexdigest() == PLAN["class_receipt_sha256"]
DATA = json.loads(raw)
assert DATA["status"] == "COMPLETE" and DATA["p"] == 8237
P = DATA["p"]


def neg(A):
    return None if A is None else (A[0], (-A[1]-1) % P)


def add(A, B):
    if A is None:
        return B
    if B is None:
        return A
    x, y = A
    u, v = B
    if x == u and (y+v+1) % P == 0:
        return None
    if A == B:
        top, bottom = 3*x*x-2*x-10, 2*y+1
    else:
        top, bottom = v-y, u-x
    slope = top*pow(bottom % P, -1, P) % P
    intercept = (y-slope*x) % P
    X = (slope*slope+1-x-u) % P
    Y = (-slope*X-intercept-1) % P
    C = X, Y
    assert (Y*Y+Y-X*X*X+X*X+10*X+20) % P == 0
    return C


def mul(n, A):
    if n < 0:
        return mul(-n, neg(A))
    C = None
    while n:
        if n & 1:
            C = add(C, A)
        A = add(A, A)
        n >>= 1
    return C


def row(raw):
    return {int(i): int(v) for i, v in raw.items() if v}


def rank(rows, modulus=None):
    pivots = {}
    for raw in rows:
        if modulus is None:
            v = {i: Fraction(x) for i, x in raw.items() if x}
        else:
            v = {i: x % modulus for i, x in raw.items() if x % modulus}
        while v:
            i = min(v)
            if i not in pivots:
                z = v[i]
                pivots[i] = ({j: x/z for j, x in v.items()} if modulus is None else
                             {j: x*pow(z, -1, modulus) % modulus for j, x in v.items()})
                break
            z = v[i]
            for j, x in pivots[i].items():
                y = v.get(j, 0)-z*x
                if modulus is not None:
                    y %= modulus
                if y:
                    v[j] = y
                else:
                    v.pop(j, None)
    return len(pivots)


POINTS = [tuple(A) for A in DATA["class_points"]]
BASE = [row(x["row"]) for x in DATA["base_rows"]]
CLOSED = [row(x["class_part"]) for x in DATA["degree13_sources"]
          if x["status"] == "CLASS_CLOSED"]
OUTSIDE = [x for x in DATA["degree13_sources"] if x["status"] == "OUTSIDE_CLASS_TRACE"]
assert len(POINTS) == 40 and len(BASE) >= 20
assert len(CLOSED) + len(OUTSIDE) == 40
assert all(1 <= len(x["outside_traces"]) <= 14 for x in OUTSIDE)
Q = DATA["largest_prime_factor"]


def enumerate_direct():
    candidates = []
    trials = 0
    for support in range(1, PLAN["support_max"]+1):
        for inds in itertools.combinations(range(len(POINTS)), support):
            for rest in itertools.product(PLAN["coefficient_order"], repeat=support-1):
                signs = (1,) + rest
                trials += 1
                total = None
                for i, sign in zip(inds, signs):
                    total = add(total, POINTS[i] if sign == 1 else neg(POINTS[i]))
                if total is None:
                    candidates.append({"indices": list(inds), "coefficients": list(signs),
                                       "row": {str(i): s for i, s in zip(inds, signs)}})
    return candidates, trials


def enumerate_hecke():
    candidates = []
    trials = 0
    for support in range(1, PLAN["support_max"]+1):
        for inds in itertools.combinations(range(len(OUTSIDE)), support):
            for rest in itertools.product(PLAN["coefficient_order"], repeat=support-1):
                signs = (1,) + rest
                trials += 1
                total = None
                combined = Counter()
                for i, sign in zip(inds, signs):
                    for raw_trace in OUTSIDE[i]["outside_traces"]:
                        T = tuple(raw_trace)
                        total = add(total, T if sign == 1 else neg(T))
                    for k, v in row(OUTSIDE[i]["class_part"]).items():
                        combined[k] += sign*v
                if total is None:
                    combined = {k: v for k, v in combined.items() if v}
                    candidates.append({"sources": [OUTSIDE[i]["source"] for i in inds],
                                       "coefficients": list(signs),
                                       "row": {str(k): v for k, v in sorted(combined.items())}})
    return candidates, trials


def selected_path(rows, baseline):
    selected = []
    selected_rows = []
    path = [{"selected": 0, "rank_mod_q": rank(baseline, Q),
             "rank_qq": rank(baseline)}]
    for i, r in enumerate(rows):
        if rank(baseline+selected_rows+[r], Q) > rank(baseline+selected_rows, Q):
            selected.append(i)
            selected_rows.append(r)
            path.append({"selected": len(selected), "candidate_index": i,
                         "rank_mod_q": rank(baseline+selected_rows, Q),
                         "rank_qq": rank(baseline+selected_rows)})
    return selected, path


def expected_triples(m, N):
    x = Fraction(4*math.comb(m, 3)*(N-2), (N-1)**2)
    return f"{x.numerator}/{x.denominator}"


def main():
    assert rank(BASE, Q) == DATA["base_rank_mod_q"]
    assert rank(BASE) == DATA["base_rank_qq"]
    measurements = []
    reference = {}
    for repetition, order in enumerate(PLAN["arm_order"]):
        measurement_row = {"repetition": repetition, "order": order.split(",")}
        for arm in measurement_row["order"]:
            start = time.perf_counter_ns()
            candidates, trials = (enumerate_direct() if arm == "direct" else enumerate_hecke())
            elapsed = time.perf_counter_ns()-start
            if arm in reference:
                assert candidates == reference[arm]["candidates"] and trials == reference[arm]["trials"]
            else:
                reference[arm] = {"candidates": candidates, "trials": trials}
            measurement_row[arm] = {"enumeration_wall_ns": elapsed, "trials": trials,
                                    "verified_candidates": len(candidates)}
        measurements.append(measurement_row)
    direct = reference["direct"]["candidates"]
    hecke = reference["hecke"]["candidates"]
    source_sums = []
    for source in OUTSIDE:
        total = None
        for raw_trace in source["outside_traces"]:
            total = add(total, tuple(raw_trace))
        source_sums.append(total)
    nonidentity_source_sums = all(T is not None for T in source_sums)
    direct_rows = [row(c["row"]) for c in direct]
    hecke_rows = [row(c["row"]) for c in hecke]
    verification_start = time.perf_counter_ns()
    for r in direct_rows+hecke_rows:
        total = None
        for i, v in r.items():
            total = add(total, mul(v, POINTS[i]))
        assert total is None
    verification_ns = time.perf_counter_ns()-verification_start
    rank_start = time.perf_counter_ns()
    direct_selected, direct_path = selected_path(direct_rows, BASE)
    hecke_selected, hecke_path = selected_path(hecke_rows, BASE+CLOSED)
    ranks = {"base_mod_q": rank(BASE, Q), "base_qq": rank(BASE),
             "base_closed_mod_q": rank(BASE+CLOSED, Q),
             "base_closed_qq": rank(BASE+CLOSED),
             "direct_only_mod_q": rank(direct_rows, Q),
             "direct_only_qq": rank(direct_rows),
             "base_direct_mod_q": rank(BASE+direct_rows, Q),
             "base_direct_qq": rank(BASE+direct_rows),
             "base_hecke_mod_q": rank(BASE+CLOSED+hecke_rows, Q),
             "base_hecke_qq": rank(BASE+CLOSED+hecke_rows),
             "base_both_mod_q": rank(BASE+CLOSED+direct_rows+hecke_rows, Q),
             "base_both_qq": rank(BASE+CLOSED+direct_rows+hecke_rows)}
    rank_ns = time.perf_counter_ns()-rank_start
    out = {"schema": "hecke-d79-p8237-support4-analysis-v1",
           "p": P, "class_size": len(POINTS), "curve_order": DATA["curve_order"],
           "rank_modulus": Q, "source_receipt_sha256": PLAN["class_receipt_sha256"],
           "direct": {"candidate_counts": {str(s): sum(len(c["indices"]) == s for c in direct)
                                           for s in range(1, PLAN["support_max"]+1)},
                      "trials": reference["direct"]["trials"], "candidates": direct,
                      "selected_candidate_indices": direct_selected, "rank_path": direct_path,
                      "null_expected_support3_exact": expected_triples(len(POINTS), DATA["curve_order"])},
           "hecke": {"candidate_counts": {str(s): sum(len(c["sources"]) == s for c in hecke)
                                          for s in range(1, PLAN["support_max"]+1)},
                     "trials": reference["hecke"]["trials"], "candidates": hecke,
                     "outside_trace_count_by_source": [len(x["outside_traces"]) for x in OUTSIDE],
                     "aggregate_source_sum_nonidentity": nonidentity_source_sums,
                     "selected_candidate_indices": hecke_selected, "rank_path": hecke_path,
                     "null_expected_support3_exact":
                         expected_triples(len(OUTSIDE), DATA["curve_order"])
                         if nonidentity_source_sums else None},
           "ranks": ranks, "measurements": measurements,
           "verification_wall_ns": verification_ns,
           "rank_analysis_wall_ns": rank_ns,
           "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
           "candidate_id": None, "target_online_ms": None}
    (HERE / "analysis.json").write_text(json.dumps(out, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"direct_counts": out["direct"]["candidate_counts"],
                      "hecke_counts": out["hecke"]["candidate_counts"],
                      "ranks": ranks}, sort_keys=True))


if __name__ == "__main__":
    main()
