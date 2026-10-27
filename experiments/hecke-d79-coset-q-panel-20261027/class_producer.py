"""Frozen D79 conductor-four class and order-five projection panel."""
import hashlib
import importlib.util
import json
import time
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve_from_j, GF, QQ, factor, hilbert_class_polynomial, matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
INPUTS = json.loads((HERE / "inputs.json").read_text())
SOURCE = ROOT / INPUTS["source_path"]


def save(data):
    (HERE / "class-result.json").write_text(json.dumps(data, indent=2, sort_keys=True)+"\n")


def rank(rows, width, field):
    if not rows:
        return 0
    return int(matrix(field, [[r.get(i, 0) for i in range(width)] for r in rows]).rank())


def main():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == INPUTS["source_sha256"]
    t0 = time.perf_counter_ns()
    spec = importlib.util.spec_from_file_location("hecke11_coset_panel", SOURCE)
    H = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(H)
    funcs, jfun = H.build([2, 5])
    source_build_ns = time.perf_counter_ns()-t0
    out = {"schema": "hecke-d79-coset-class-panel-v1",
           "source_sha256": INPUTS["source_sha256"],
           "source_build_wall_ns": source_build_ns, "cases": [],
           "status": "RUNNING", "candidate_id": None, "target_online_ms": None}
    save(out)
    H79 = hilbert_class_polynomial(-79)
    for frozen in INPUTS["primes"]:
        t_case = time.perf_counter_ns()
        p, v = frozen["p"], frozen["v"]
        assert p == v*v+316
        R = H.Reduced(p, funcs, jfun, [2, 5])
        E, Fp = R.E, R.Fp
        n = int(E.cardinality())
        q = int(max(prime for prime, _ in factor(n)))
        invariants = [int(x) for x in E.abelian_group().invariants()]
        starts = []
        for j in H79.change_ring(Fp).roots(multiplicities=False):
            tr = abs(int(EllipticCurve_from_j(j).trace_of_frobenius()))
            if tr == 2*v:
                starts.extend(R.points_with_j(j))
        seen, frontier = set(starts), list(starts)
        trace_cache = {}

        def in_class(P):
            j = R.j(P)
            if j is None or j == 0 or j == 1728:
                return False
            if j not in trace_cache:
                trace_cache[j] = abs(int(EllipticCurve_from_j(j).trace_of_frobenius()))
            return trace_cache[j] == 2*v

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
        index = {P: i for i, P in enumerate(points)}
        class_ns = time.perf_counter_ns()-t_case
        t_base = time.perf_counter_ns()
        base_rows = []
        for i, P in enumerate(points):
            for ell in (2, 5):
                nb = R.neighbours_all(ell, P)
                if nb is None:
                    continue
                assert sum(nb, E(0)) == R.a_l[ell]*P
                if all(Q in index for Q in nb):
                    row = Counter(index[Q] for Q in nb)
                    row[i] -= int(R.a_l[ell])
                    row = {k: x for k, x in row.items() if x}
                    assert sum((x*points[k] for k, x in row.items()), E(0)) == E(0)
                    base_rows.append({"source": i, "degree": ell,
                                      "row": {str(k): x for k, x in sorted(row.items())}})
        raw_rows = [{int(i): v for i, v in r["row"].items()} for r in base_rows]
        projected = [(n//5)*P for P in points]
        T = next((Q for Q in projected if Q != E(0)), None)
        if T is None:
            residues = [0 for _ in points]
            projection_status = "NO_NONZERO_CLASS_PROJECTION"
            generator = None
        else:
            assert 5*T == E(0)
            lookup = {k*T: k for k in range(5)}
            assert len(lookup) == 5 and all(Q in lookup for Q in projected)
            residues = [lookup[Q] for Q in projected]
            projection_status = "ORDER_FIVE_PROJECTION"
            generator = [int(T[0]), int(T[1])]
        counts = {str(k): residues.count(k) for k in range(5)}
        antipodal = T is not None and all(k in (1, 4) for k in residues)
        case = {"v": v, "p": p, "curve_order": n,
                "group_invariants": invariants, "largest_prime_factor": q,
                "prescreen_order_match": n == frozen["ambient_order"],
                "prescreen_group_match": invariants == frozen["group_invariants"],
                "start_count": len(starts), "class_size": len(points),
                "class_size_prediction_match": len(points) == frozen["expected_class_size"],
                "class_points": [[int(P[0]), int(P[1])] for P in points],
                "base_rows": base_rows, "base_rank_qq": rank(raw_rows, len(points), QQ),
                "base_rank_mod_q": rank(raw_rows, len(points), GF(q)),
                "projection_status": projection_status,
                "projection_generator": generator,
                "projection_residues": residues, "projection_counts": counts,
                "antipodal_only": antipodal,
                "predicted_support3_count": 0 if antipodal else None,
                "class_walk_wall_ns": class_ns,
                "base_and_projection_wall_ns": time.perf_counter_ns()-t_base}
        out["cases"].append(case)
        save(out)
        print(json.dumps({"p": p, "class_size": len(points), "q": q,
                          "projection_counts": counts, "antipodal_only": antipodal},
                         sort_keys=True), flush=True)
    out["status"] = "COMPLETE"
    save(out)


if __name__ == "__main__":
    main()
