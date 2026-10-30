"""Prespecified p12197 conductor-four degree-13 Hecke trace census."""
import hashlib
import importlib.util
import itertools
import json
import math
import resource
import time
from collections import Counter
from pathlib import Path

from sage.all import (EllipticCurve_from_j, GF, QQ, classical_modular_polynomial,
                      factor, hilbert_class_polynomial, is_prime, matrix, vector)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
INPUTS = json.loads((HERE / "inputs.json").read_text())
SOURCE = ROOT / INPUTS["source_path"]
SOURCE_HASH = "7e66144e76bf62f7e645d87cc58be2bb0f7cc5e52601665650ef0706a6f715fb"


def save(obj):
    (HERE / "result.json").write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def rank(rows, width, field):
    return int(matrix(field, [[r.get(i, 0) for i in range(width)] for r in rows]).rank())


def main():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == INPUTS["source_sha256"] == SOURCE_HASH
    parent = ROOT / INPUTS["producer_parent_path"]
    assert hashlib.sha256(parent.read_bytes()).hexdigest() == INPUTS["producer_parent_sha256"]
    class_parent = ROOT / INPUTS["parent_class_receipt"]
    class_raw = class_parent.read_bytes()
    assert hashlib.sha256(class_raw).hexdigest() == INPUTS["parent_class_sha256"]
    frozen_class = next(c for c in json.loads(class_raw)["cases"] if c["p"] == INPUTS["p"])
    phase_wall_ns = {}
    last = time.perf_counter_ns()

    def mark(name):
        nonlocal last
        now = time.perf_counter_ns()
        phase_wall_ns[name] = now-last
        last = now

    spec = importlib.util.spec_from_file_location("hecke11_second_prime", SOURCE)
    H = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(H)
    v = INPUTS["v"]
    p = v*v + 316
    assert (v, p) == (INPUTS["v"], INPUTS["p"]) and is_prime(p)
    funcs, jfun = H.build([2, 5, 13])
    R = H.Reduced(p, funcs, jfun, [2, 5, 13])
    E, Fp = R.E, R.Fp
    n = int(E.order())
    q = int(max(prime for prime, _ in factor(n)))
    mark("source_build")
    out = {"schema": "hecke-d79-p12197-rank-producer-v1", "DK": -79, "f": 4,
           "p": p, "trace_magnitude": 2 * v, "curve_order": n,
           "largest_prime_factor": q, "source_sha256": SOURCE_HASH,
           "prescreen_order_match": n == INPUTS["prescreen_curve_order"],
           "prescreen_q_match": q == INPUTS["prescreen_largest_prime_factor"],
           "candidate_id": None, "target_online_ms": None}
    starts = []
    for j in hilbert_class_polynomial(-79).change_ring(Fp).roots(multiplicities=False):
        tr = abs(int(EllipticCurve_from_j(j).trace_of_frobenius()))
        assert tr == 2 * v, (j, tr)
        starts.extend(R.points_with_j(j))
    if not starts:
        mark("class_walk")
        out["phase_wall_ns"] = phase_wall_ns
        out["total_measured_wall_ns"] = sum(phase_wall_ns.values())
        out["peak_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        out.update(status="NO_RATIONAL_START", start_count=0)
        save(out)
        return
    seen, frontier = set(starts), list(starts)
    trace_cache = {}

    def in_class(P):
        j = R.j(P)
        if j is None or j == 0 or j == 1728:
            return False
        if j not in trace_cache:
            trace_cache[j] = abs(int(EllipticCurve_from_j(j).trace_of_frobenius()))
        return trace_cache[j] == 2 * v

    while frontier:
        nxt = []
        for P in frontier:
            for ell in (2, 5):
                for Q in R.neighbour_candidates(ell, P):
                    if Q not in seen and in_class(Q):
                        seen.add(Q)
                        nxt.append(Q)
        frontier = nxt
    points = sorted(seen, key=lambda P: (int(P[0]), int(P[1])))
    mark("class_walk")
    index = {P: i for i, P in enumerate(points)}
    out["start_count"] = len(starts)
    out["class_points"] = [[int(P[0]), int(P[1])] for P in points]
    out["class_size"] = len(points)
    assert out["class_points"] == frozen_class["class_points"]
    assert len(points) == INPUTS["expected_class_size"]
    out["parent_class_match"] = True
    rows = []
    for i, P in enumerate(points):
        for ell in (2, 5):
            nb = R.neighbours_all(ell, P)
            if nb is None:
                continue
            assert sum(nb, E(0)) == R.a_l[ell] * P
            if all(Q in index for Q in nb):
                row = Counter(index[Q] for Q in nb)
                row[i] -= int(R.a_l[ell])
                entry = {k: x for k, x in row.items() if x}
                assert sum((x * points[k] for k, x in entry.items()), E(0)).is_zero()
                rows.append({"source": i, "degree": ell,
                             "row": {str(k): x for k, x in sorted(entry.items())}})
    base = [{int(k): x for k, x in item["row"].items()} for item in rows]
    out["base_rows"] = rows
    out["base_rank_qq"] = rank(base, len(points), QQ)
    out["base_rank_mod_q"] = rank(base, len(points), GF(q))
    mark("base_rows")
    print(json.dumps({"phase": "base", "class_size": len(points),
                      "rows": len(rows), "rank": out["base_rank_mod_q"]}), flush=True)

    modpoly = classical_modular_polynomial(13)
    cache = {}
    sources, closed, outside_equations = [], [], []
    out["degree13_sources"] = sources
    out["status"] = "RUNNING_DEGREE13"
    save(out)
    for i, P in enumerate(points):
        poly = R.neighbour_x(13, P)
        factors = list(poly.factor())
        pattern = [[int(f.degree()), int(mult)] for f, mult in factors]
        assert pattern == INPUTS["expected_degree13_pattern"]
        d = math.lcm(*(degree for degree, _ in pattern))
        entry = {"source": i, "factor_pattern": pattern, "splitting_degree": d}
        if d > 12:
            entry["status"] = "EXTENSION_CAP"
            sources.append(entry)
            continue
        if any(mult != 1 for _, mult in pattern):
            entry["status"] = "REPEATED_X_UNLIFTED"
            sources.append(entry)
            continue
        if d not in cache:
            F = GF(p ** d, name=f"z{d}")
            EE = E.change_ring(F)
            lifted = [EE(F(Q[0]), F(Q[1])) for Q in points]
            cache[d] = F, EE, lifted, {Q: k for k, Q in enumerate(lifted)}
        F, EE, lifted, lifted_index = cache[d]
        roots = sorted(poly.change_ring(F).roots(multiplicities=False), key=str)
        assert len(roots) == 14
        moments = [F(R.funcs[13, "xy", k](P[0], P[1])) for k in range(14)]
        V = matrix(F, [[x ** k for x in roots] for k in range(14)])
        ys = V.solve_right(vector(F, moments))
        nb = [EE(x, y) for x, y in zip(roots, ys)]
        assert sum(nb, EE(0)) == R.a_l[13] * lifted[i]
        assert all(sum(ys[j] * roots[j] ** k for j in range(14)) == moments[k]
                   for k in range(14))
        jP = R.j(P)
        A, x0, _ = jfun
        cusp_count = 0
        modpoly_checked = 0
        for Q in nb:
            if Q[0] == F(x0):
                cusp_count += 1
                continue
            numer = sum(F(c) * Q[0] ** int(a) * Q[1] ** int(b)
                        for (a, b), c in A.items())
            jQ = numer / (Q[0] - F(x0)) ** 11
            assert modpoly(F(jP), jQ) == 0
            modpoly_checked += 1
        assert cusp_count + modpoly_checked == 14
        entry["modpoly_checks"] = {"finite_j": modpoly_checked,
                                   "cusp_j_pole": cusp_count}
        unseen = set(nb)
        orbits = []
        class_row = Counter({i: -int(R.a_l[13])})
        outside = []
        while unseen:
            seed = min(unseen, key=lambda Q: (str(Q[0]), str(Q[1])))
            orbit, Q = [], seed
            while Q not in orbit:
                orbit.append(Q)
                Q = EE(Q[0] ** p, Q[1] ** p)
            assert Q == seed and all(Q in unseen for Q in orbit)
            unseen.difference_update(orbit)
            T = sum(orbit, EE(0))
            if T.is_zero():
                status, coord = "IDENTITY", None
            elif T in lifted_index:
                status, coord = "IN_CLASS", [int(T[0]), int(T[1])]
                class_row[lifted_index[T]] += 1
            else:
                status, coord = "OUTSIDE_CLASS", [int(T[0]), int(T[1])]
                outside.append(tuple(coord))
            orbits.append({"size": len(orbit), "status": status, "trace": coord})
        entry["orbits"] = orbits
        entry["class_part"] = {str(k): x for k, x in sorted(class_row.items()) if x}
        entry["outside_traces"] = [list(x) for x in sorted(outside)]
        if not outside:
            entry["status"] = "CLASS_CLOSED"
            closed.append({int(k): x for k, x in entry["class_part"].items()})
        else:
            entry["status"] = "OUTSIDE_CLASS_TRACE"
            outside_equations.append(entry)
        sources.append(entry)
        save(out)
        print(json.dumps({"phase": "degree13", "source": i, "status": entry["status"],
                          "pattern": pattern}), flush=True)
    out["degree13_sources"] = sources
    out["degree13_statuses"] = dict(Counter(item["status"] for item in sources))
    mark("degree13_fibers")
    out["rank_with_closed_qq"] = rank(base + closed, len(points), QQ)
    out["rank_with_closed_mod_q"] = rank(base + closed, len(points), GF(q))
    paired = []
    pair_rows = []
    for a, b in itertools.combinations(outside_equations, 2):
        if a["outside_traces"] != b["outside_traces"]:
            continue
        row = Counter({int(k): x for k, x in a["class_part"].items()})
        row.subtract({int(k): x for k, x in b["class_part"].items()})
        row = {k: x for k, x in row.items() if x}
        assert sum((x * points[k] for k, x in row.items()), E(0)).is_zero()
        paired.append({"sources": [a["source"], b["source"]],
                       "outside_traces": a["outside_traces"],
                       "row": {str(k): x for k, x in sorted(row.items())}})
        pair_rows.append(row)
    out["equal_trace_pairs"] = paired
    out["rank_with_pairs_qq"] = rank(base + closed + pair_rows, len(points), QQ)
    out["rank_with_pairs_mod_q"] = rank(base + closed + pair_rows, len(points), GF(q))
    mark("pair_rows")
    out["phase_wall_ns"] = phase_wall_ns
    out["total_measured_wall_ns"] = sum(phase_wall_ns.values())
    out["peak_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    out["status"] = "COMPLETE"
    save(out)
    print(json.dumps({"phase": "complete", "class_size": len(points),
                      "statuses": out["degree13_statuses"],
                      "ranks": [out["base_rank_mod_q"], out["rank_with_closed_mod_q"],
                                out["rank_with_pairs_mod_q"]],
                      "equal_trace_pairs": len(paired)}), flush=True)


if __name__ == "__main__":
    main()
