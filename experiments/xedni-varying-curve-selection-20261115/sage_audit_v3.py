"""Sage crosscheck of every saved second-prime curve and relation."""

import hashlib
import json
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ, matrix

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / "protocol-v3.json").read_text())
    result = json.loads((HERE / "result-v3.json").read_text())
    raw = HERE / "rows-v3.jsonl"
    assert sha(raw) == result["rows_sha256"]
    rows = [json.loads(line) for line in raw.read_text().splitlines()]
    l = protocol["second_auxiliary_prime"]["prime"]
    F = GF(l)
    counts = Counter()
    local_hits = 0
    for row in rows:
        A, B = QQ(row["A"]), QQ(row["B"])
        assert A.denominator() % l and B.denominator() % l
        E = EllipticCurve(F, [F(A), F(B)])
        Q1 = E([F(x) for x in row["lifted_points"][0]])
        Q2 = E([F(x) for x in row["lifted_points"][1]])
        assert [int(Q1[0]), int(Q1[1])] == row["P1_mod11"]
        assert [int(Q2[0]), int(Q2[1])] == row["P2_mod11"]
        order = int(E.cardinality())
        assert order == row["aux_order"]
        counts[order] += 1
        x1, y1 = Q1[0], Q1[1]
        x2, y2 = Q2[0], Q2[1]
        row1 = [y1 * y1, x1 * y1, y1, x1 ** 3, x1 ** 2, x1, F(1)]
        row2 = [y2 * y2, x2 * y2, y2, x2 ** 3, x2 ** 2, x2, F(1)]
        assert int(matrix(F, [row1, row2]).rank()) == row["aux_rank"]
        sum_point = Q1 + 2 * Q2
        local = sum_point.is_zero()
        assert local == row["local_relation"]
        if local:
            assert row["relation_sum_mod11"] is None
        else:
            assert [int(sum_point[0]), int(sum_point[1])] == row["relation_sum_mod11"]
        local_hits += int(local)
        assert row["strict_accepted"] == (row["aux_rank"] == 2 and order == protocol["second_auxiliary_prime"]["strict_order"])
        assert row["weak_accepted"] == (row["aux_rank"] == 2 and order == protocol["second_auxiliary_prime"]["weak_epsilon_1_order"])
    assert len(rows) == result["input_pairs"]
    assert counts == {int(k): v for k, v in result["auxiliary_curve_order_counts"].items()}
    assert local_hits == result["good_reduction_local_relation_count"]
    print(json.dumps({
        "schema": "xedni-varying-curve-selection-sage-audit-v3",
        "status": "PASS",
        "source_sha256": sha(HERE / "sage_audit_v3.py"),
        "runtime_sha256": sha(HERE / "sage-runtime-info-v3.json"),
        "rows_sha256": sha(raw),
        "checked_rows": len(rows),
        "auxiliary_order_counts": dict(counts),
        "local_relation_count": local_hits,
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
