"""Lift degree-13 Hecke fibers and census Frobenius orbit traces."""
import hashlib
import importlib.util
import json
import math
import re
from collections import Counter
from pathlib import Path

from sage.all import GF, QQ, classical_modular_polynomial, matrix, set_random_seed, vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
INPUTS = json.loads((HERE / "inputs.json").read_text())
HASHES = {entry["path"]: entry["sha256"] for entry in INPUTS["inputs"]}
OLD, FIXED, CANCEL, PRIOR, HECKE = [entry["path"] for entry in INPUTS["inputs"]]


def raw(path):
    data = (ROOT / path).read_bytes()
    assert hashlib.sha256(data).hexdigest() == HASHES[path]
    return data


def load(path):
    return json.loads(raw(path))


def load_module(path):
    raw(path)
    spec = importlib.util.spec_from_file_location("_orbit_hecke11", ROOT / path)
    assert spec is not None and spec.loader is not None
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def row(raw_row):
    return {int(i): int(v) for i, v in raw_row.items() if v}


def rank(rows, width):
    return matrix(QQ, [[entry.get(i, 0) for i in range(width)] for entry in rows]).rank()


def rank_mod(rows, width, modulus):
    from sage.all import GF as FiniteField
    return int(matrix(FiniteField(modulus), [[entry.get(i, 0) for i in range(width)]
                                             for entry in rows]).rank())


def main():
    old = load(OLD)
    fixed = load(FIXED)
    cancellation = load(CANCEL)
    prior = load(PRIOR)
    assert old["DK"] == fixed["DK"] == -79
    assert old["f"] == fixed["f"] == 2
    assert old["p"] == fixed["p"] == 83
    assert old["column_points"] == fixed["column_points"]
    H = load_module(HECKE)
    ell = INPUTS["degree"]
    set_random_seed(13083)
    funcs, jfun = H.build([ell])
    reduced = H.Reduced(83, funcs, jfun, [ell])
    points = []
    for encoded in old["column_points"]:
        match = re.fullmatch(r"\((\d+) : (\d+) : 1\)", encoded)
        assert match is not None
        points.append(reduced.E([int(match.group(1)), int(match.group(2)), 1]))
    assert len(points) == len(set(points)) == 20
    fixed_rows = list(map(row, fixed["relation_rows"]))
    fixed_rank = rank(fixed_rows, len(points))
    assert fixed_rank == fixed["rank"] == 10
    existing_rows = fixed_rows + [row(item["row"]) for item in
                                  cancellation["closed_rows"] + cancellation["pair_rows"]]
    assert rank(existing_rows, len(points)) == cancellation["rank_after_pairs_qq"] == 16
    assert rank_mod(existing_rows, len(points), 5) == 16
    prior_outside = {tuple(item["trace_coordinates"]) for source in prior["sources"]
                     for item in source.get("orbits", []) if item["trace_status"] == "OUTSIDE_CLASS"}
    modpoly = classical_modular_polynomial(ell)
    field_cache = {}
    result = []
    accepted = []
    for source in INPUTS["source_indices"]:
        P = points[source]
        poly = reduced.neighbour_x(ell, P)
        factors = list(poly.factor())
        pattern = [{"degree": int(f.degree()), "multiplicity": int(m)} for f, m in factors]
        assert sum(item["degree"] * item["multiplicity"] for item in pattern) == ell + 1
        splitting_degree = math.lcm(*(item["degree"] for item in pattern))
        entry = {"source": source, "factor_pattern": pattern,
                 "splitting_degree": splitting_degree,
                 "squarefree": all(item["multiplicity"] == 1 for item in pattern)}
        if splitting_degree > INPUTS["extension_degree_cap"]:
            entry["status"] = "EXTENSION_CAP"
            result.append(entry)
            continue
        if not entry["squarefree"]:
            entry["status"] = "REPEATED_X_UNLIFTED"
            result.append(entry)
            continue
        if splitting_degree not in field_cache:
            F = GF(83 ** splitting_degree, name=f"z{splitting_degree}")
            E = reduced.E.change_ring(F)
            class_points = [E(F(Q[0]), F(Q[1])) for Q in points]
            field_cache[splitting_degree] = (F, E, class_points)
        F, E, class_points = field_cache[splitting_degree]
        class_index = {Q: i for i, Q in enumerate(class_points)}
        lifted_P = class_points[source]
        roots = [x for x, multiplicity in poly.change_ring(F).roots() for _ in range(multiplicity)]
        assert len(roots) == ell + 1 and len(set(roots)) == ell + 1
        roots.sort(key=str)
        moments = [F(reduced.funcs[ell, "xy", k](P[0], P[1])) for k in range(ell + 1)]
        V = matrix(F, [[x ** k for x in roots] for k in range(ell + 1)])
        ys = V.solve_right(vector(F, moments))
        assert all(sum(ys[j] * roots[j] ** k for j in range(ell + 1)) == moments[k]
                   for k in range(ell + 1))
        neighbors = [E(x, y) for x, y in zip(roots, ys)]
        jP = reduced.j(P)
        assert jP is not None
        A, x0, _ = jfun
        def jext(Q):
            if Q.is_zero() or Q[0] == F(x0):
                return None
            numerator = sum(F(c) * Q[0] ** int(a) * Q[1] ** int(b)
                            for (a, b), c in A.items())
            return numerator / (Q[0] - F(x0)) ** 11
        assert all(jext(Q) is not None and modpoly(F(jP), jext(Q)) == 0 for Q in neighbors)
        assert sum(neighbors, E(0)) == reduced.a_l[ell] * lifted_P
        unseen = set(neighbors)
        orbits = []
        closed = True
        aggregate = Counter()
        while unseen:
            seed = min(unseen, key=lambda Q: (str(Q[0]), str(Q[1])))
            orbit = []
            Q = seed
            while Q not in orbit:
                orbit.append(Q)
                Q = E(Q[0] ** 83, Q[1] ** 83)
            assert Q == seed and all(item in unseen for item in orbit)
            unseen.difference_update(orbit)
            trace = sum(orbit, E(0))
            assert E(trace[0] ** 83, trace[1] ** 83) == trace if not trace.is_zero() else True
            if trace.is_zero():
                trace_status, trace_index = "IDENTITY", None
            elif trace in class_index:
                trace_status, trace_index = "IN_CLASS", class_index[trace]
                aggregate[trace_index] += 1
            else:
                trace_status, trace_index = "OUTSIDE_CLASS", None
                closed = False
            orbits.append({"size": len(orbit), "trace_status": trace_status,
                           "trace_class_index": trace_index,
                           "trace_coordinates": None if trace.is_zero() else [str(trace[0]), str(trace[1])],
                           "matches_degree5_outside": not trace.is_zero() and
                           (str(trace[0]), str(trace[1])) in prior_outside})
        assert sum(item["size"] for item in orbits) == ell + 1
        entry["orbits"] = sorted(orbits, key=lambda item: (item["size"], item["trace_status"], str(item["trace_coordinates"])))
        if closed:
            aggregate[source] -= int(reduced.a_l[ell])
            relation = {i: int(v) for i, v in aggregate.items() if v}
            assert sum((value * class_points[i] for i, value in relation.items()), E(0)).is_zero()
            entry["status"] = "CLASS_CLOSED"
            entry["row"] = {str(i): v for i, v in sorted(relation.items())}
            accepted.append(relation)
        else:
            entry["status"] = "OUTSIDE_CLASS_TRACE"
        result.append(entry)
    status = dict(Counter(item["status"] for item in result))
    output = {"schema": "hecke-degree13-orbit-v1", "DK": -79, "conductor": 2,
              "p": 83, "degree": ell, "points": len(points), "a_l": int(reduced.a_l[ell]),
              "extension_degree_cap": INPUTS["extension_degree_cap"],
              "corrected_degree2_rows": len(fixed_rows), "corrected_degree2_rank_qq": fixed_rank,
              "existing_rank_qq": rank(existing_rows, len(points)),
              "existing_rank_mod5": rank_mod(existing_rows, len(points), 5),
              "accepted_trace_rows": len(accepted),
              "rank_with_trace_rows_qq": rank(existing_rows + accepted, len(points)),
              "rank_with_trace_rows_mod5": rank_mod(existing_rows + accepted, len(points), 5),
              "statuses": status, "sources": result}
    (HERE / "result.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    patterns = Counter(str([(item["degree"], item["multiplicity"])
                            for item in source["factor_pattern"]]) for source in result)
    print(json.dumps({"statuses": status, "accepted_trace_rows": len(accepted),
                      "rank_with_trace_rows_qq": output["rank_with_trace_rows_qq"],
                      "rank_with_trace_rows_mod5": output["rank_with_trace_rows_mod5"],
                      "factor_patterns": dict(patterns)}, sort_keys=True))


if __name__ == "__main__":
    main()
