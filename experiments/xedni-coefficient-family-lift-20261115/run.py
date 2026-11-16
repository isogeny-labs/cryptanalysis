"""Replay rational relations for a frozen coefficient family on archived CRT lifts."""

import gzip
import hashlib
import importlib.util
import json
import math
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BAND = ROOT / "xedni-crt-band-panel-20261115"
SHIFT = ROOT / "xedni-point-lift-shift-20261115"
FAMILY = ROOT / "xedni-coefficient-family-control-20261115"
ARITH = ROOT / "xedni-crt-prime-panel-20261115" / "audit.py"
ORDER = ROOT / "xedni-crt-curve-choice-20261115" / "cost_audit.py"
SHIFT_SOURCE = SHIFT / "run.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def point_on(point, coeffs):
    x, y = map(Fraction, point)
    a1, a2, a3, a4, a6 = coeffs
    return y*y + a1*x*y + a3*y == x*x*x + a2*x*x + a4*x + a6


def signed_mul(n, point, coeffs, arith, prime=None):
    out = arith.mul(abs(n), point, coeffs, prime)
    if n < 0 and out is not None:
        if prime is None:
            x, y = out
            out = (x, -y - coeffs[0]*x - coeffs[2])
        else:
            out = arith.neg(out, coeffs, prime)
    return out


def rational_relation(a, b, points, coeffs, arith):
    U, V = points
    return arith.add(signed_mul(a, U, coeffs, arith),
                     signed_mul(b, V, coeffs, arith), coeffs, None) is None


def shifted_points(centered, p, k):
    (x1, y1), (x2, y2) = centered
    dx = x1 - x2
    d = abs(dx)
    assert d != 0
    k0 = (-(y1 - y2) * pow(p, -1, d)) % d if d > 1 else 0
    expected = min((k0, k0-d), key=lambda n: (abs(n), n)) if d > 1 else 0
    assert k == expected
    return [(x1, y1 + k*p), (x2, y2)]


def reconstruct(points, p, row, orders, arith, cost):
    i7, i11 = row["attempts_7"], row["attempts_11"]
    assert 1 <= i7 <= len(orders[7]) and 1 <= i11 <= len(orders[11])
    c7, c11 = orders[7][i7-1], orders[11][i11-1]
    for ell, free, wanted in ((7, c7, 4), (11, c11, 6)):
        a4, a6, delta = cost.curve_data(points, free, ell)
        assert delta != 0
        chars = [0 if x == 0 else (1 if pow(x, (ell-1)//2, ell) == 1 else -1)
                 for x in range(ell)]
        assert cost.count_points((*free, a4, a6), ell, chars) == wanted
    free = [arith.crt_free(p, c7[i], c11[i]) for i in range(3)]
    coeffs = list(arith.solve_rational(points, free))
    assert arith.delta(coeffs) != 0
    assert all(point_on(point, coeffs) for point in points)
    for ell, desired in ((p, (0, 0, 0, p-1, p-2)), (7, None), (11, None)):
        actual = tuple(arith.mod_rational(c, ell) for c in coeffs)
        if desired is None:
            free_aux = c7 if ell == 7 else c11
            aux = cost.curve_data(points, free_aux, ell)
            desired = (*free_aux, aux[0], aux[1])
        assert actual == desired
    return coeffs


def family_hits(sampled, vectors, r, base, p, arith):
    out = {}
    for t1 in range(r):
        for t2 in range(r):
            U, V = sampled[t1], sampled[t2]
            if U is None or V is None or U == V:
                continue
            hits = []
            for a, b in vectors:
                if arith.add(signed_mul(a, U, base, arith, p),
                             signed_mul(b, V, base, arith, p), base, p) is None:
                    hits.append((a, b))
            if hits:
                out[(t1, t2)] = hits
    return out


def run_arm(label, folder, reference, family, vectors, orders, arith, cost, protocol):
    fields = []
    for old, control in zip(reference["fields"], family["fields"], strict=True):
        p, r = old["field_prime"], old["subgroup_order"]
        assert p == control["field_prime"] and r == control["subgroup_order"]
        G, Q = tuple(old["generator"]), tuple(old["public_target"])
        base = protocol["base_curve_coefficients"]
        sampled = [arith.add(Q, arith.neg(arith.mul(t, G, base, p), base, p), base, p)
                   for t in range(r)]
        hits = family_hits(sampled, vectors, r, base, p, arith)
        assert sum(len(v) for v in hits.values()) == control["union_count"]
        assert len(hits) == control["union_count"]
        raw_hash = hashlib.sha256()
        counts = Counter()
        counts["public_group_tests"] = control["public_group_tests"]
        by_vector = Counter()
        first = None
        witnesses = []
        index = 0
        for shard in old["row_shards"]:
            raw = gzip.open(folder / "rows" / shard, "rb").read()
            raw_hash.update(raw)
            for line in raw.splitlines():
                row = json.loads(line)
                t1, t2 = divmod(index, r)
                assert row["t"] == [t1, t2]
                index += 1
                counts["queries"] += 1
                counts["auxiliary_probes"] += row["attempts_7"] + row["attempts_11"]
                counts["attempts_7"] += row["attempts_7"]
                counts["attempts_11"] += row["attempts_11"]
                counts["status_" + row["status"]] += 1
                row_hits = hits.get((t1, t2), [])
                counts["reduced_family_relations"] += len(row_hits)
                if not row_hits or not row["accepted"]:
                    continue
                counts["accepted_reduced_family_relations"] += len(row_hits)
                U, V = sampled[t1], sampled[t2]
                centered = [(arith.centered(x, p), arith.centered(y, p)) for x, y in (U, V)]
                if label == "shifted":
                    points = shifted_points(centered, p, row["k"])
                else:
                    points = centered
                assert points[0][0] != points[1][0]
                coeffs = reconstruct(points, p, row, orders, arith, cost)
                counts["reconstructed_curves"] += 1
                pts = [tuple(map(Fraction, point)) for point in points]
                for a, b in row_hits:
                    counts["rational_group_tests"] += 1
                    rational = rational_relation(a, b, pts, coeffs, arith)
                    if (a, b) == (1, 2):
                        assert rational == row["rational_relation"]
                    if rational:
                        C = a+b
                        assert C % r
                        recovered = ((a*t1+b*t2)*pow(C, -1, r)) % r
                        assert arith.mul(recovered, G, base, p) == Q
                        by_vector[(a, b)] += 1
                        counts["rational_relations"] += 1
                        event = {"query_index_one_based": index, "t": [t1, t2],
                                 "vector": [a, b], "recovered_scalar": recovered,
                                 "auxiliary_probe_prefix": counts["auxiliary_probes"],
                                 "points": [list(point) for point in points],
                                 "coefficients": [str(c) for c in coeffs]}
                        witnesses.append(event)
                        if first is None:
                            first = {k: event[k] for k in ("query_index_one_based", "t", "vector",
                                                          "auxiliary_probe_prefix")}
        assert index == r*r == control["queries"]
        assert raw_hash.hexdigest() == old["rows_sha256"]
        assert counts["auxiliary_probes"] == old["counts"].get("attempts_7", 0) + old["counts"].get("attempts_11", 0)
        assert counts["auxiliary_probes"] <= protocol["maximum_archived_auxiliary_probes_per_arm"]
        expected = old["counts"].get("accepted_rational_relations", old["counts"].get("rational_relations", 0))
        assert by_vector[(1, 2)] == expected
        fixed = next((w for w in witnesses if w["vector"] == [1, 2]), None)
        parent_first = old["first_rational_relation"]
        assert (fixed is None) == (parent_first is None)
        if fixed is not None:
            assert fixed["t"] == parent_first["t"]
            assert fixed["query_index_one_based"] == parent_first["query_index_one_based"]
        fields.append({"field_prime": p, "subgroup_order": r,
                       "counts": dict(counts), "by_vector": [
                           {"c": list(v), "rational_relations": by_vector[v]} for v in vectors],
                       "first_rational": first, "witnesses": witnesses})
    return {"arm": label, "fields": fields,
            "totals": dict(sum((Counter(f["counts"]) for f in fields), Counter()))}


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert protocol["schema"] == "xedni-coefficient-family-lift-protocol-v1"
    paths = (("centered_result_sha256", BAND / "result.json"),
             ("shifted_result_sha256", SHIFT / "result.json"),
             ("family_result_sha256", FAMILY / "result.json"),
             ("arithmetic_source_sha256", ARITH),
             ("candidate_order_source_sha256", ORDER),
             ("shift_source_sha256", SHIFT_SOURCE))
    for key, path in paths:
        assert sha(path) == protocol[key], key
    arith = load_module("xedni_family_lift_arith", ARITH)
    cost = load_module("xedni_family_lift_order", ORDER)
    centered = json.loads((BAND / "result.json").read_text())
    shifted = json.loads((SHIFT / "result.json").read_text())
    family = json.loads((FAMILY / "result.json").read_text())
    assert centered["status"] == shifted["status"] == family["status"] == "PASS"
    assert [f["field_prime"] for f in centered["fields"]] == protocol["fields"]
    vectors = [(a, b) for a in range(1, 4) for b in range(-3, 4)
               if b and math.gcd(a, abs(b)) == 1]
    assert [tuple(v["c"]) for v in family["fields"][0]["vectors"]] == vectors
    orders = {ell: cost.candidates(ell) for ell in (7, 11)}
    arms = [run_arm(label, folder, reference, family, vectors, orders, arith, cost, protocol)
            for label, folder, reference in (("centered", BAND, centered),
                                             ("shifted", SHIFT, shifted))]
    assert all(arm["totals"]["queries"] == protocol["maximum_queries_per_arm"]
               for arm in arms)
    print(json.dumps({"schema": "xedni-coefficient-family-lift-result-v1",
                      "status": "PASS", "protocol_sha256": sha(HERE / "protocol.json"),
                      "source_sha256": sha(Path(__file__)), "arms": arms},
                     sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
