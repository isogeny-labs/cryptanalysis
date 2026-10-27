"""Multiplicity-aware degree-5 lift for the one repeated-x source."""
import hashlib
import importlib.util
import itertools
import json
import re
from collections import Counter
from pathlib import Path

from sage.all import GF, classical_modular_polynomial, matrix, vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
INPUTS = json.loads((HERE / "inputs.json").read_text())
HASHES = {entry["path"]: entry["sha256"] for entry in INPUTS["inputs"]}
OLD, FIXED, PRIOR, HECKE = [entry["path"] for entry in INPUTS["inputs"]]


def raw(path):
    data = (ROOT / path).read_bytes()
    assert hashlib.sha256(data).hexdigest() == HASHES[path]
    return data


def load(path):
    return json.loads(raw(path))


def module(path):
    raw(path)
    spec = importlib.util.spec_from_file_location("_cancel_hecke11", ROOT / path)
    assert spec is not None and spec.loader is not None
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def main():
    old = load(OLD)
    fixed = load(FIXED)
    prior = load(PRIOR)
    assert old["column_points"] == fixed["column_points"]
    assert prior["sources"][INPUTS["repeated_source"]]["status"] == "REPEATED_X_UNLIFTED"
    H = module(HECKE)
    ell = INPUTS["degree"]
    funcs, jfun = H.build([ell])
    reduced = H.Reduced(83, funcs, jfun, [ell])
    points = []
    for encoded in old["column_points"]:
        match = re.fullmatch(r"\((\d+) : (\d+) : 1\)", encoded)
        assert match is not None
        points.append(reduced.E([int(match.group(1)), int(match.group(2)), 1]))
    source = INPUTS["repeated_source"]
    P = points[source]
    poly = reduced.neighbour_x(ell, P)
    pattern = [(int(f.degree()), int(m)) for f, m in poly.factor()]
    assert pattern == [(1, 2), (4, 1)] or sorted(pattern) == [(1, 2), (4, 1)]
    F = GF(83 ** INPUTS["extension_degree"], name="z4")
    E = reduced.E.change_ring(F)
    class_points = [E(F(Q[0]), F(Q[1])) for Q in points]
    class_index = {Q: i for i, Q in enumerate(class_points)}
    lifted_P = class_points[source]
    roots = poly.change_ring(F).roots()
    assert sorted(int(m) for _, m in roots) == [1, 1, 1, 1, 2]
    roots.sort(key=lambda item: str(item[0]))
    repeated_x = next(x for x, multiplicity in roots if multiplicity == 2)
    xs = [x for x, _ in roots]
    moments = [F(reduced.funcs[ell, "xy", k](P[0], P[1])) for k in range(ell + 1)]
    V = matrix(F, [[x ** k for x in xs] for k in range(5)])
    weighted_y = V.solve_right(vector(F, moments[:5]))
    assert all(sum(weighted_y[j] * xs[j] ** k for j in range(5)) == moments[k]
               for k in range(ell + 1))
    simple = [E(x, weighted_y[j]) for j, (x, multiplicity) in enumerate(roots)
              if multiplicity == 1]
    repeated_lifts = E.lift_x(repeated_x, all=True)
    modpoly = classical_modular_polynomial(ell)
    A, x0, _ = jfun
    jP = reduced.j(P)
    assert jP is not None
    def jext(Q):
        if Q.is_zero() or Q[0] == F(x0):
            return None
        numerator = sum(F(c) * Q[0] ** int(a) * Q[1] ** int(b)
                        for (a, b), c in A.items())
        return numerator / (Q[0] - F(x0)) ** 11
    candidates = []
    for pair in itertools.combinations_with_replacement(repeated_lifts, 2):
        if pair[0][1] + pair[1][1] != weighted_y[xs.index(repeated_x)]:
            continue
        neighbors = simple + list(pair)
        if not all(sum(Q[0] ** k * Q[1] for Q in neighbors) == moments[k]
                   for k in range(ell + 1)):
            continue
        if not all(jext(Q) is not None and modpoly(F(jP), jext(Q)) == 0 for Q in neighbors):
            continue
        if sum(neighbors, E(0)) != reduced.a_l[ell] * lifted_P:
            continue
        counts = Counter(neighbors)
        orbits = []
        while counts:
            seed = min(counts, key=lambda Q: (str(Q[0]), str(Q[1])))
            orbit = []
            Q = seed
            while Q not in orbit:
                orbit.append(Q)
                Q = E(Q[0] ** 83, Q[1] ** 83)
            assert Q == seed
            multiplicity = counts[seed]
            assert all(counts[Q] == multiplicity for Q in orbit)
            for Q in orbit:
                del counts[Q]
            trace = sum(orbit, E(0))
            assert trace.is_zero() or E(trace[0] ** 83, trace[1] ** 83) == trace
            if trace.is_zero():
                status, index = "IDENTITY", None
            elif trace in class_index:
                status, index = "IN_CLASS", class_index[trace]
            else:
                status, index = "OUTSIDE_CLASS", None
            orbits.append({"size": len(orbit), "multiplicity": int(multiplicity),
                           "trace_status": status, "trace_class_index": index,
                           "trace_coordinates": None if trace.is_zero() else [str(trace[0]), str(trace[1])]})
        assert sum(item["size"] * item["multiplicity"] for item in orbits) == ell + 1
        candidates.append({"repeated_y_pair": [str(Q[1]) for Q in pair],
                           "orbits": sorted(orbits, key=lambda item: (item["size"], item["trace_status"], str(item["trace_coordinates"])))})
    output = {"schema": "hecke-repeated-x-lift-v1", "source": source,
              "factor_pattern": [{"degree": degree, "multiplicity": multiplicity} for degree, multiplicity in pattern],
              "repeated_x": str(repeated_x), "repeated_y_sum": str(weighted_y[xs.index(repeated_x)]),
              "candidate_count": len(candidates), "candidates": candidates,
              "status": "UNIQUE_LIFT" if len(candidates) == 1 else "AMBIGUOUS_OR_MISSING_LIFT"}
    (HERE / "lift-result.json").write_text(json.dumps(output, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": output["status"], "candidate_count": len(candidates),
                      "repeated_x": output["repeated_x"], "repeated_y_sum": output["repeated_y_sum"],
                      "candidates": candidates}, sort_keys=True))


if __name__ == "__main__":
    main()
