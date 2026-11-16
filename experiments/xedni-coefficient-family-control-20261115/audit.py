"""Independent modular-equation audit of every frozen coefficient-family query."""

import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
BAND = HERE.parent / "xedni-crt-band-panel-20261115" / "result.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    band = json.loads(BAND.read_text())
    assert sha(HERE / "protocol.json") == result["protocol_sha256"]
    assert sha(HERE / "run.py") == result["source_sha256"]
    assert sha(BAND) == protocol["parent_band_result_sha256"]
    assert result["status"] == "PASS"
    vectors = [(a, b) for a in range(1, 4) for b in range(-3, 4)
               if b != 0 and math.gcd(a, abs(b)) == 1]
    assert len(vectors) == result["family_size"] == 14
    all_queries = all_tests = all_hits = 0
    for record, parent in zip(result["fields"], band["fields"], strict=True):
        p, r, w = parent["field_prime"], parent["subgroup_order"], parent["fixture_scalar"]
        assert p == record["field_prime"] and r == record["subgroup_order"]
        assert record["queries"] == r * r
        observed = {v: 0 for v in vectors}
        first = {v: None for v in vectors}
        union = admissible = tests = replays = 0
        first_union = None
        max_mult = 0
        for index in range(r * r):
            t1, t2 = divmod(index, r)
            # P_i=(w-t_i)G; identity and equality can be tested in scalar coordinates.
            if t1 == w or t2 == w or t1 == t2:
                continue
            admissible += 1
            hits = []
            for a, b in vectors:
                tests += 1
                if (a * (w - t1) + b * (w - t2)) % r == 0:
                    observed[(a, b)] += 1
                    hits.append((a, b))
                    if first[(a, b)] is None:
                        first[(a, b)] = {"query_index_one_based": index + 1,
                                         "t": [t1, t2]}
                    if a + b:
                        assert ((a * t1 + b * t2) * pow(a + b, -1, r)) % r == w
                        replays += 1
            max_mult = max(max_mult, len(hits))
            if hits:
                union += 1
                if first_union is None:
                    first_union = {"query_index_one_based": index + 1,
                                   "t": [t1, t2], "vectors": [list(v) for v in hits]}
        assert record["admissible_pairs"] == admissible == (r - 1) * (r - 2)
        assert record["public_group_tests"] == tests
        assert record["union_count"] == union
        assert record["first_union"] == first_union
        assert record["max_hit_multiplicity"] == max_mult
        assert record["scalar_replays"] == replays
        assert [tuple(v["c"]) for v in record["vectors"]] == vectors
        for item in record["vectors"]:
            v = tuple(item["c"])
            assert item["coefficient_sum"] == sum(v)
            assert item["relation_count"] == observed[v]
            assert item["first"] == first[v]
        # Distinct primitive directions have determinant magnitude < r and
        # can intersect only at the excluded pair (w,w).
        nonzero = [v for v in vectors if sum(v)]
        assert len(nonzero) == 13
        assert all(0 < abs(a * d - b * c) < r
                   for i, (a, b) in enumerate(nonzero)
                   for c, d in nonzero[i + 1:])
        assert observed[(1, -1)] == 0
        assert all(observed[v] == r - 1 for v in nonzero)
        assert max_mult == 1 and union == 13 * (r - 1)
        all_queries += r * r
        all_tests += tests
        all_hits += union
    assert all_queries == result["queries"] == protocol["max_queries"]
    assert all_tests == result["public_group_tests"]
    print(json.dumps({"schema": "xedni-coefficient-family-control-audit-v1",
                      "status": "PASS", "source_sha256": sha(Path(__file__)),
                      "queries": all_queries, "public_group_tests": all_tests,
                      "union_hits": all_hits}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
