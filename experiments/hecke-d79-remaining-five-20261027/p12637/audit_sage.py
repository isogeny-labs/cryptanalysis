"""Independent p12637 class, degree-13 factor, relation and rank replay."""
import hashlib
import importlib.util
import itertools
import json
from collections import Counter
from pathlib import Path

from sage.all import (EllipticCurve_from_j, GF, QQ, hilbert_class_polynomial,
                      matrix)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
INPUTS = json.loads((HERE / "inputs.json").read_text())
POST = json.loads((HERE / "post_inputs.json").read_text())
raw = (ROOT / POST["class_receipt"]).read_bytes()
assert hashlib.sha256(raw).hexdigest() == POST["class_receipt_sha256"]
DATA = json.loads(raw)
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
    spec = importlib.util.spec_from_file_location("hecke11_p12637_audit", SOURCE)
    H = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(H)
    funcs, jfun = H.build([13])
    R = H.Reduced(INPUTS["p"], funcs, jfun, [13])
    E, Fp = R.E, R.Fp
    assert int(E.cardinality()) == DATA["curve_order"] == INPUTS["prescreen_curve_order"] == 12655
    group_invariants = [int(x) for x in E.abelian_group().invariants()]
    assert group_invariants == [12655]
    trace_cache = {}
    class_set = set()
    strata = []
    for f in (1, 2, 4):
        roots = [int(j) for j in hilbert_class_polynomial(-79*f*f).change_ring(Fp)
                 .roots(multiplicities=False)]
        pts = set()
        for j in roots:
            if j in (0, 1728 % INPUTS["p"]):
                continue
            trace_cache[j] = abs(int(EllipticCurve_from_j(Fp(j)).trace_of_frobenius()))
            if trace_cache[j] == 2*INPUTS["v"]:
                pts.update((int(P[0]), int(P[1])) for P in R.points_with_j(Fp(j)))
        class_set |= pts
        strata.append({"conductor": f, "j_roots": len(roots),
                       "rational_class_points": len(pts)})
    saved = [tuple(A) for A in DATA["class_points"]]
    assert class_set == set(saved) and saved == sorted(class_set)
    points = [E([Fp(x), Fp(y)]) for x, y in saved]
    T = (DATA["curve_order"]//5)*points[0]
    assert T != E(0) and 5*T == E(0)
    torsion_coordinates = {k*T: k for k in range(5)}
    assert len(torsion_coordinates) == 5
    class_projection = Counter(torsion_coordinates[(DATA["curve_order"]//5)*P] for P in points)
    assert sorted(class_projection.values()) == [20, 20]
    q_projection_nonzero = sum((DATA["curve_order"]//DATA["largest_prime_factor"])*P != E(0) for P in points)
    base = [sparse(x["row"]) for x in DATA["base_rows"]]
    closed = [sparse(x["class_part"]) for x in DATA["degree13_sources"]
              if x["status"] == "CLASS_CLOSED"]
    outside = [x for x in DATA["degree13_sources"] if x["status"] == "OUTSIDE_CLASS_TRACE"]
    source_projection = Counter()
    for source in outside:
        trace_sum = sum((E([Fp(x), Fp(y)]) for x, y in source["outside_traces"]), E(0))
        source_projection[torsion_coordinates[(DATA["curve_order"]//5)*trace_sum]] += 1
    qfield = GF(DATA["largest_prime_factor"])
    for item in DATA["degree13_sources"]:
        P = points[item["source"]]
        poly = R.neighbour_x(13, P)
        pattern = [[int(f.degree()), int(m)] for f, m in poly.factor()]
        assert pattern == item["factor_pattern"]
        if item["status"] in ("EXTENSION_CAP", "REPEATED_X_UNLIFTED"):
            continue
        assert sum(x["size"] for x in item["orbits"]) == 14
        assert sum(item["modpoly_checks"].values()) == 14
        class_part = sparse(item["class_part"])
        total = sum((v*points[i] for i, v in class_part.items()), E(0))
        total += sum((E([Fp(x), Fp(y)]) for x, y in item["outside_traces"]), E(0))
        assert total == E(0)
        if item["status"] == "CLASS_CLOSED":
            assert not item["outside_traces"]
        else:
            assert item["status"] == "OUTSIDE_CLASS_TRACE"
            assert 1 <= len(item["outside_traces"]) <= 14
    for r in base+closed:
        assert sum((v*points[i] for i, v in r.items()), E(0)) == E(0)
    source_sums = [sum((E([Fp(x), Fp(y)]) for x, y in source["outside_traces"]), E(0))
                   for source in outside]
    def pair_sums(terms):
        return {(i, j, a, b): a*terms[i]+b*terms[j]
                for i in range(len(terms)) for j in range(i+1, len(terms))
                for a in (-1, 1) for b in (-1, 1)}

    def signed_zero(terms, pairs, inds, signs):
        if len(inds) == 1:
            return terms[inds[0]] == E(0)
        if len(inds) == 2:
            return pairs[inds[0], inds[1], signs[0], signs[1]] == E(0)
        left = pairs[inds[0], inds[1], signs[0], signs[1]]
        if len(inds) == 3:
            return left == -signs[2]*terms[inds[2]]
        right = pairs[inds[2], inds[3], signs[2], signs[3]]
        return left == -right

    direct_pairs = pair_sums(points)
    hecke_pairs = pair_sums(source_sums)
    direct, hecke = [], []
    for support in range(1, POST["support_max"]+1):
        for inds in itertools.combinations(range(len(points)), support):
            for rest in itertools.product(POST["coefficient_order"], repeat=support-1):
                signs = (1,) + rest
                if signed_zero(points, direct_pairs, inds, signs):
                    direct.append({"indices": list(inds), "coefficients": list(signs),
                                   "row": {str(i): s for i, s in zip(inds, signs)}})
        for inds in itertools.combinations(range(len(outside)), support):
            for rest in itertools.product(POST["coefficient_order"], repeat=support-1):
                signs = (1,) + rest
                if signed_zero(source_sums, hecke_pairs, inds, signs):
                    combined = Counter()
                    for i, s in zip(inds, signs):
                        for k, v in sparse(outside[i]["class_part"]).items():
                            combined[k] += s*v
                    hecke.append({"sources": [outside[i]["source"] for i in inds],
                                  "coefficients": list(signs),
                                  "row": {str(k): v for k, v in sorted(combined.items()) if v}})
    assert direct == ANALYSIS["direct"]["candidates"]
    assert hecke == ANALYSIS["hecke"]["candidates"]
    direct_rows = [sparse(c["row"]) for c in direct]
    hecke_rows = [sparse(c["row"]) for c in hecke]
    for r in direct_rows+hecke_rows:
        assert sum((v*points[i] for i, v in r.items()), E(0)) == E(0)
    ranks = {"base_mod_q": rank(base, qfield, len(points)),
             "base_qq": rank(base, QQ, len(points)),
             "base_closed_mod_q": rank(base+closed, qfield, len(points)),
             "base_closed_qq": rank(base+closed, QQ, len(points)),
             "direct_only_mod_q": rank(direct_rows, qfield, len(points)),
             "direct_only_qq": rank(direct_rows, QQ, len(points)),
             "base_direct_mod_q": rank(base+direct_rows, qfield, len(points)),
             "base_direct_qq": rank(base+direct_rows, QQ, len(points)),
             "base_hecke_mod_q": rank(base+closed+hecke_rows, qfield, len(points)),
             "base_hecke_qq": rank(base+closed+hecke_rows, QQ, len(points)),
             "base_both_mod_q": rank(base+closed+direct_rows+hecke_rows, qfield, len(points)),
             "base_both_qq": rank(base+closed+direct_rows+hecke_rows, QQ, len(points))}
    assert ranks == ANALYSIS["ranks"]
    receipt = {"schema": "hecke-d79-p12637-support4-sage-audit-v1", "status": "PASS",
               "curve_order": int(E.cardinality()), "class_points": len(points),
               "group_invariants": group_invariants,
               "order_five_projection_generator": [int(T[0]), int(T[1])],
               "class_projection_counts": {str(k): v for k, v in sorted(class_projection.items())},
               "source_projection_counts": {str(k): v for k, v in sorted(source_projection.items())},
               "q_projection_nonzero_points": q_projection_nonzero,
               "j_values_checked": len(trace_cache), "strata": strata,
               "degree13_patterns_checked": len(points),
               "direct_candidates_checked": len(direct), "hecke_candidates_checked": len(hecke),
               "ranks": ranks}
    (HERE / "audit.json").write_text(json.dumps(receipt, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"status": "PASS", "strata": strata,
                      "direct": len(direct), "hecke": len(hecke)}, sort_keys=True))


if __name__ == "__main__":
    main()
