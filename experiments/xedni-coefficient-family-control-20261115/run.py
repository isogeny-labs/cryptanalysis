"""Full public-group census for a frozen family of two-point relations."""

import hashlib
import importlib.util
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
BAND = HERE.parent / "xedni-crt-band-panel-20261115" / "result.json"
ARITH = HERE.parent / "xedni-crt-prime-panel-20261115" / "audit.py"
FIXED = HERE.parent / "xedni-direct-relation-control-20261115" / "result.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def family():
    return [(a, b) for a in range(1, 4) for b in range(-3, 4)
            if b and math.gcd(a, abs(b)) == 1]


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert protocol["schema"] == "xedni-coefficient-family-control-protocol-v1"
    for key, path in (("parent_band_result_sha256", BAND),
                      ("parent_arithmetic_source_sha256", ARITH),
                      ("reference_fixed_vector_result_sha256", FIXED)):
        assert sha(path) == protocol[key], key
    band = json.loads(BAND.read_text())
    fixed = json.loads(FIXED.read_text())
    assert band["status"] == fixed["status"] == "PASS"
    assert [f["field_prime"] for f in band["fields"]] == protocol["fields"]
    vectors = family()
    assert len(vectors) == 14 and (1, 2) in vectors and (1, -1) in vectors
    spec = importlib.util.spec_from_file_location("xedni_family_arith", ARITH)
    arith = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(arith)
    base = protocol["base_curve_coefficients"]
    fields = []
    total_queries = 0
    total_tests = 0
    for old, ref in zip(band["fields"], fixed["fields"], strict=True):
        p, r = old["field_prime"], old["subgroup_order"]
        assert p == ref["field_prime"] and r == ref["subgroup_order"]
        G, Q = tuple(old["generator"]), tuple(old["public_target"])
        assert arith.mul(r, G, base, p) is None
        sampled = [arith.add(Q, arith.neg(arith.mul(t, G, base, p), base, p), base, p)
                   for t in range(r)]
        counts = {vector: 0 for vector in vectors}
        first = {vector: None for vector in vectors}
        union_count = 0
        first_union = None
        max_multiplicity = 0
        admissible = 0
        scalar_replays = 0
        for index in range(r * r):
            t1, t2 = divmod(index, r)
            U, V = sampled[t1], sampled[t2]
            if U is None or V is None or U == V:
                continue
            admissible += 1
            hits = []
            for a, b in vectors:
                aU = arith.mul(a, U, base, p)
                bV = arith.mul(abs(b), V, base, p)
                if b < 0:
                    bV = arith.neg(bV, base, p)
                if arith.add(aU, bV, base, p) is None:
                    counts[(a, b)] += 1
                    hits.append((a, b))
                    if first[(a, b)] is None:
                        first[(a, b)] = {"query_index_one_based": index + 1,
                                         "t": [t1, t2]}
                    C = a + b
                    if C % r:
                        recovered = ((a * t1 + b * t2) * pow(C, -1, r)) % r
                        assert arith.mul(recovered, G, base, p) == Q
                        scalar_replays += 1
            max_multiplicity = max(max_multiplicity, len(hits))
            if hits:
                union_count += 1
                if first_union is None:
                    first_union = {"query_index_one_based": index + 1,
                                   "t": [t1, t2], "vectors": [list(v) for v in hits]}
        assert admissible == old["counts"]["admissible_pairs"]
        assert first[(1, 2)] == {"query_index_one_based": ref["first_direct"]["query_index_one_based"],
                                 "t": ref["first_direct"]["t"]}
        assert counts[(1, 2)] == ref["direct_relation_count"]
        fields.append({"field_prime": p, "subgroup_order": r, "queries": r * r,
                       "admissible_pairs": admissible,
                       "public_group_tests": admissible * len(vectors),
                       "union_count": union_count, "first_union": first_union,
                       "max_hit_multiplicity": max_multiplicity,
                       "scalar_replays": scalar_replays,
                       "vectors": [{"c": list(v), "coefficient_sum": sum(v),
                                    "relation_count": counts[v], "first": first[v]}
                                   for v in vectors]})
        total_queries += r * r
        total_tests += admissible * len(vectors)
    assert total_queries == protocol["max_queries"]
    print(json.dumps({"schema": "xedni-coefficient-family-control-result-v1",
                      "status": "PASS", "protocol_sha256": sha(HERE / "protocol.json"),
                      "source_sha256": sha(Path(__file__)), "queries": total_queries,
                      "public_group_tests": total_tests, "family_size": len(vectors),
                      "fields": fields}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
