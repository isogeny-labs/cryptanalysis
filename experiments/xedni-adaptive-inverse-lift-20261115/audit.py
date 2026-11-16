"""Checked-Sage replay of the full public-pair and adaptive-curve census."""

import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ


HERE = Path(__file__).resolve().parent
INPUT = HERE.parent / "xedni-large-order-admission-20261115" / "result.json"
PARENT_SOURCE = HERE.parent / "xedni-public-coordinate-lift-20261115" / "run.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def centered(value, p):
    value = int(value)
    return value if value <= p // 2 else value - p


def check_field(item, field, protocol):
    p, q = item["field_prime"], item["subgroup_order"]
    assert (p, q) == (field["field_prime"], field["subgroup_order"])
    E = EllipticCurve(GF(p), protocol["base_curve_coefficients"])
    assert int(E.cardinality()) == item["curve_order"]
    P = E(2, 2)
    order = int(P.order())
    assert order == field["generator_reduction_order"]
    m = order // q
    assert order == m * q == field["subgroup_multiplier_m"] * q
    G = m * P
    assert int(G.order()) == q
    Q = 17 * G
    assert [int(G[0]), int(G[1])] == field["generator"]
    assert [int(Q[0]), int(Q[1])] == field["public_target"]
    points = [Q - t * G for t in range(q)]
    counts = Counter()
    first = None
    shards = field["row_shards"]
    assert len(shards) == (q + 31) // 32
    for shard_index, shard in enumerate(shards):
        path = HERE / shard["path"]
        assert sha(path) == shard["sha256"]
        with gzip.open(path, "rt") as stream:
            rows = [json.loads(line) for line in stream]
        start = 32 * shard_index
        assert len(rows) == min(32, q - start) * q
        for offset, row in enumerate(rows):
            t1, t2 = start + offset // q, offset % q
            assert row["t"] == [t1, t2]
            R1, R2 = points[t1], points[t2]
            counts["queries"] += 1
            if R1.is_zero() or R2.is_zero():
                assert row["status"] == "identity"
                assert row["public_group_tests"] == row["curve_constructions"] == 0
            elif R1 == R2:
                assert row["status"] == "duplicate"
                assert row["public_group_tests"] == row["curve_constructions"] == 0
            else:
                assert row["public_group_tests"] == 1
                counts["public_group_tests"] += 1
                if not (R1 + R2).is_zero():
                    assert row["status"] == "public_nonrelation"
                    assert row["curve_constructions"] == 0
                else:
                    counts["public_inverse_pairs"] += 1
                    assert row["status"] == "rational_relation"
                    assert row["curve_constructions"] == 1
                    counts["curve_constructions"] += 1
                    x, y = centered(R1[0], p), centered(R1[1], p)
                    B = y * y - x * x * x + x
                    assert B == row["curve_B"] and B % p == (-2) % p
                    rational = EllipticCurve(QQ, [0, 0, 0, -1, B])
                    assert rational.discriminant() != 0
                    A, C = rational(x, y), rational(x, -y)
                    assert (A + C).is_zero()
                    assert row["lifted_points"] == [[x, y], [x, -y]]
                    assert E(x, y) == R1 and E(x, -y) == R2
                    recovered = ((t1 + t2) * pow(2, -1, q)) % q
                    assert recovered == row["recovered_scalar"] == 17
                    assert recovered * G == Q
                    counts["rational_relations"] += 1
                    if first is None:
                        first = {"t": [t1, t2],
                                 "query_index_one_based": counts["queries"]}
            counts[f"status_{row['status']}"] += 1
    assert first == field["first_rational_relation"]
    assert dict(counts) == field["counts"]
    assert counts["rational_relations"] == q - 1
    return counts


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    selection = json.loads(INPUT.read_text())
    assert result["status"] == "PASS"
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert result["source_sha256"] == sha(HERE / "run.py")
    assert result["input_sha256"] == sha(INPUT) == \
        protocol["input_selection_result_sha256"]
    assert result["parent_source_sha256"] == sha(PARENT_SOURCE) == \
        protocol["parent_finite_group_source_sha256"]
    selected = [r for r in selection["rows"] if r["selected"]]
    assert len(selected) == len(result["fields"])
    total = Counter()
    for item, field in zip(selected, result["fields"]):
        total.update(check_field(item, field, protocol))
    assert all(total.get(key, 0) == value for key, value in result["totals"].items())
    print(json.dumps({"schema": "xedni-adaptive-inverse-lift-audit-v1",
                      "status": "PASS", "fields": len(selected),
                      "queries": total["queries"],
                      "public_group_tests": total["public_group_tests"],
                      "rational_relations": total["rational_relations"]},
                     sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
