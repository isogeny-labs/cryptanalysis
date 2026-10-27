"""Independent exhaustive Sage audit of class, projections, and direct rows."""
import hashlib
import importlib.util
import itertools
import json
from collections import Counter
from pathlib import Path

from sage.all import (EllipticCurve_from_j, GF, QQ, hilbert_class_polynomial,
                      matrix)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
INPUTS = json.loads((HERE / "inputs.json").read_text())
POST = json.loads((HERE / "post_inputs.json").read_text())
raw = (ROOT / POST["class_receipt"]).read_bytes()
assert hashlib.sha256(raw).hexdigest() == POST["class_receipt_sha256"]
CLASSES = json.loads(raw)
ANALYSIS = json.loads((HERE / "analysis.json").read_text())
SOURCE = ROOT / INPUTS["source_path"]
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == INPUTS["source_sha256"]


def sparse(raw):
    return {int(i): int(v) for i, v in raw.items() if v}


def rank(rows, field, width):
    if not rows:
        return 0
    return int(matrix(field, len(rows), width,
                      lambda i, j: rows[i].get(j, 0)).rank())


def main():
    spec = importlib.util.spec_from_file_location("hecke11_coset_audit", SOURCE)
    H = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(H)
    funcs, jfun = H.build([2])
    receipts = []
    assert len(CLASSES["cases"]) == len(ANALYSIS["cases"]) == len(INPUTS["primes"])
    for frozen, source, analysis in zip(INPUTS["primes"], CLASSES["cases"], ANALYSIS["cases"]):
        p, v = frozen["p"], frozen["v"]
        assert source["p"] == analysis["p"] == p
        R = H.Reduced(p, funcs, jfun, [2])
        E, Fp = R.E, R.Fp
        all_points = list(E.points())
        assert len(all_points) == source["curve_order"] == frozen["ambient_order"]
        assert [int(x) for x in E.abelian_group().invariants()] == source["group_invariants"]
        fibers = {}
        traces = {}
        class_set = set()
        for P in all_points:
            if P.is_zero():
                continue
            j = R.j(P)
            if j is None:
                continue
            J = int(j)
            fibers.setdefault(J, []).append((int(P[0]), int(P[1])))
            if J in (0, 1728 % p):
                continue
            if J not in traces:
                traces[J] = abs(int(EllipticCurve_from_j(Fp(J)).trace_of_frobenius()))
            if traces[J] == 2*v:
                class_set.add((int(P[0]), int(P[1])))
        saved = [tuple(P) for P in source["class_points"]]
        assert saved == sorted(class_set)
        strata = []
        union = set()
        for f in (1, 2, 4):
            roots = [int(j) for j in hilbert_class_polynomial(-79*f*f).change_ring(Fp)
                     .roots(multiplicities=False)]
            pts = {P for j in roots if traces.get(j) == 2*v for P in fibers.get(j, [])}
            union |= pts
            strata.append({"conductor": f, "j_roots": len(roots),
                           "rational_class_points": len(pts)})
        assert union == class_set
        points = [E([Fp(x), Fp(y)]) for x, y in saved]
        n = source["curve_order"]
        projected = [(n//5)*P for P in points]
        T = next((Q for Q in projected if Q != E(0)), None)
        if T is None:
            residues = [0 for _ in points]
        else:
            assert 5*T == E(0)
            lookup = {k*T: k for k in range(5)}
            assert len(lookup) == 5
            residues = [lookup[Q] for Q in projected]
        assert residues == source["projection_residues"]
        assert {str(k): residues.count(k) for k in range(5)} == source["projection_counts"]
        antipodal = T is not None and all(k in (1, 4) for k in residues)
        assert antipodal == source["antipodal_only"] == analysis["antipodal_only"]
        base = [sparse(r["row"]) for r in source["base_rows"]]
        for r in base:
            assert sum((c*points[i] for i, c in r.items()), E(0)) == E(0)
        q = source["largest_prime_factor"]
        assert rank(base, QQ, len(points)) == source["base_rank_qq"]
        assert rank(base, GF(q), len(points)) == source["base_rank_mod_q"]
        candidates = []
        for support in range(1, POST["support_max"]+1):
            for inds in itertools.combinations(range(len(points)), support):
                for rest in itertools.product(POST["coefficient_order"], repeat=support-1):
                    signs = (1,) + rest
                    if sum((s*points[i] for i, s in zip(inds, signs)), E(0)) == E(0):
                        candidates.append({"indices": list(inds),
                                           "coefficients": list(signs),
                                           "row": {str(i): s for i, s in zip(inds, signs)}})
        assert candidates == analysis["candidates"]
        rows = [sparse(c["row"]) for c in candidates]
        ranks = {"direct_only_mod_q": rank(rows, GF(q), len(points)),
                 "direct_only_qq": rank(rows, QQ, len(points)),
                 "base_plus_direct_mod_q": rank(base+rows, GF(q), len(points)),
                 "base_plus_direct_qq": rank(base+rows, QQ, len(points))}
        assert ranks == analysis["ranks"]
        counts = {str(s): sum(len(c["indices"]) == s for c in candidates)
                  for s in range(1, 4)}
        assert counts == analysis["candidate_counts"]
        if antipodal:
            assert counts["3"] == source["predicted_support3_count"] == 0
        receipt = {"p": p, "curve_order": n, "class_size": len(points),
                   "strata": strata, "projection_counts": source["projection_counts"],
                   "antipodal_only": antipodal, "candidate_counts": counts,
                   "ranks": ranks, "j_values_checked": len(traces)}
        receipts.append(receipt)
        (HERE / "audit.json").write_text(json.dumps(
            {"schema": "hecke-d79-coset-panel-audit-v1", "status": "RUNNING",
             "cases": receipts}, indent=2, sort_keys=True)+"\n")
        print(json.dumps({"p": p, "status": "PASS", "triple_rows": counts["3"]},
                         sort_keys=True), flush=True)
    (HERE / "audit.json").write_text(json.dumps(
        {"schema": "hecke-d79-coset-panel-audit-v1", "status": "PASS",
         "cases": receipts}, indent=2, sort_keys=True)+"\n")


if __name__ == "__main__":
    main()
