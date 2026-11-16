"""Replay a fixed public point through the frozen CRT lift policy."""

import gzip
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ, crt

import run_v2 as algorithm

HERE = Path(__file__).resolve().parent


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    return sha_bytes(path.read_bytes())


def main():
    protocol = json.loads((HERE / "protocol-target.json").read_text())
    parent = json.loads((HERE / "protocol-v2.json").read_text())
    assert sha(HERE / "run_v2.py") == protocol["parent_source_sha256"]
    catalog_bytes = gzip.decompress((HERE / "rows-v2.jsonl.gz").read_bytes())
    assert sha_bytes(catalog_bytes) == protocol["parent_census_rows_sha256"]
    catalog = {}
    for line in catalog_bytes.decode().splitlines():
        row = json.loads(line)
        key = tuple(tuple(point) for point in row["reduced_points"])
        assert key not in catalog
        catalog[key] = row
    assert len(catalog) == 1722

    curve = protocol["curve"]
    p = curve["field_prime"]
    q = curve["subgroup_order"]
    E = EllipticCurve(GF(p), curve["coefficients"])
    G = E(curve["generator"])
    Q = E(curve["public_target"])
    assert int(E.cardinality()) == q and int(G.order()) == q
    assert Q == protocol["fixture"]["known_scalar_for_independent_replay"] * G
    s = protocol["target_input_law"]["s"]
    assert s == [1, 1]
    l7 = parent["auxiliary_gates"]["first"]["prime"]
    l11 = parent["auxiliary_gates"]["second"]["prime"]
    order7 = parent["auxiliary_gates"]["first"]["required_order"]
    strict11 = parent["auxiliary_gates"]["second"]["strict_order"]
    weak11 = parent["auxiliary_gates"]["second"]["weak_epsilon_1_order"]
    modulus = parent["coefficient_policy"]["crt_modulus"]
    order_lists = {l: algorithm.coefficient_order(l) for l in (l7, l11)}
    characters = {}
    for l in (l7, l11):
        squares = {y * y % l for y in range(1, l)}
        characters[l] = [0 if z == 0 else 1 if z in squares else -1 for z in range(l)]

    statuses = Counter()
    admissible = accepted = reduced_hits = rational_hits = 0
    recovered = []
    raw_lines = []
    for t1, t2 in itertools.product(range(q), repeat=2):
        P1, P2 = Q - t1 * G, Q - t2 * G
        row = {"t": [t1, t2], "status": None, "accepted": False,
               "reduced_relation": False, "rational_relation": False,
               "recovered_scalar": None}
        if P1.is_zero() or P2.is_zero():
            row["status"] = "identity"
        elif P1 == P2:
            row["status"] = "duplicate"
        else:
            admissible += 1
            key = ((int(P1[0]), int(P1[1])), (int(P2[0]), int(P2[1])))
            prior = catalog[key]
            reduced = (P1 + 2 * P2).is_zero()
            assert reduced == prior["reduced_relation"]
            row["reduced_relation"] = bool(reduced)
            points = [(algorithm.centered(P1[0], p), algorithm.centered(P1[1], p)),
                      (algorithm.centered(P2[0], p), algorithm.centered(P2[1], p))]
            row["reduced_points"] = key
            dx = points[0][0] - points[1][0]
            if dx == 0:
                row["status"] = "same_x_47"
            elif dx % l7 == 0:
                row["status"] = "same_x_7"
            elif dx % l11 == 0:
                row["status"] = "same_x_11"
            else:
                c7, _ = algorithm.first_candidate(points, l7, order7,
                                                  order_lists[l7], characters[l7])
                assert c7 is not None
                c11, _ = algorithm.first_candidate(points, l11, strict11,
                                                   order_lists[l11], characters[l11])
                arm = "strict"
                if c11 is None:
                    c11, _ = algorithm.first_candidate(points, l11, weak11,
                                                       order_lists[l11], characters[l11])
                    arm = "weak"
                assert c11 is not None
                free = []
                for i in range(3):
                    n = int(crt([0, c7[i], c11[i]], [p, l7, l11]))
                    free.append(n if n <= modulus // 2 else n - modulus)
                a1, a2, a3 = free
                a4, a6 = algorithm.solved(points, a1, a2, a3)
                assert algorithm.delta(QQ(a1), QQ(a2), QQ(a3), a4, a6) != 0
                EQ = EllipticCurve(QQ, [a1, a2, a3, a4, a6])
                lifts = [EQ([x, y]) for x, y in points]
                rational = (lifts[0] + 2 * lifts[1]).is_zero() if reduced else False
                assert [str(c) for c in (a1, a2, a3, a4, a6)] == [str(prior[k]) for k in ("a1", "a2", "a3", "a4", "a6")]
                assert arm == prior["arm"] and rational == prior["rational_relation"]
                row.update({"status": "accepted", "accepted": True,
                            "reduced_relation": bool(reduced),
                            "rational_relation": bool(rational)})
                accepted += 1
                reduced_hits += int(reduced)
                rational_hits += int(rational)
                if rational:
                    denominator = (s[0] + 2 * s[1]) % q
                    assert denominator != 0
                    scalar = ((t1 + 2 * t2) * pow(denominator, -1, q)) % q
                    assert scalar * G == Q
                    row["recovered_scalar"] = scalar
                    row["rational_curve"] = [str(c) for c in (a1, a2, a3, a4, a6)]
                    recovered.append(scalar)
            assert row["status"] == prior["status"]
        statuses[row["status"]] += 1
        raw_lines.append(json.dumps(row, sort_keys=True) + "\n")

    predicted = protocol["frozen_predictions_from_parent_census"]
    assert len(raw_lines) == predicted["target_queries"]
    assert admissible == predicted["admissible_ordered_pairs"]
    assert accepted == predicted["crt_accepted_pairs"]
    assert reduced_hits == predicted["accepted_reduced_relation_pairs"]
    assert rational_hits == predicted["accepted_rational_relation_pairs"]
    assert sorted(set(recovered)) == predicted["all_recovered_scalars"]
    raw_bytes = "".join(raw_lines).encode()
    compressed = gzip.compress(raw_bytes, mtime=0)
    (HERE / "target-rows.jsonl.gz").write_bytes(compressed)
    print(json.dumps({
        "schema": "xedni-crt-fixed-target-result-v1", "status": "PASS",
        "protocol_sha256": sha(HERE / "protocol-target.json"),
        "source_sha256": sha(HERE / "target_replay.py"),
        "parent_source_sha256": sha(HERE / "run_v2.py"),
        "parent_rows_sha256": sha_bytes(catalog_bytes),
        "runtime_sha256": sha(HERE / "sage-runtime-info-target.json"),
        "target_rows_sha256": sha_bytes(raw_bytes),
        "target_rows_gzip_sha256": sha_bytes(compressed),
        "generator": curve["generator"], "public_target": curve["public_target"],
        "target_queries": len(raw_lines), "admissible_pairs": admissible,
        "crt_accepted_pairs": accepted, "accepted_reduced_relations": reduced_hits,
        "accepted_rational_relations": rational_hits,
        "recovered_scalars": recovered, "status_counts": dict(statuses),
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
