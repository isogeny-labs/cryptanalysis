"""Census of deterministic two-point rational lifts and an auxiliary gate."""

import hashlib
import itertools
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ, ZZ, matrix

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def centered(value, p):
    n = int(value)
    return n if n <= p // 2 else n - p


def row(point, field):
    x, y = point
    x, y = field(x), field(y)
    return [y * y, x * y, y, x ** 3, x ** 2, x, field(1)]


def main():
    protocol = json.loads((HERE / "protocol-v2.json").read_text())
    finite = protocol["finite_field_curve"]
    p = finite["prime"]
    Fp = GF(p)
    Ebase = EllipticCurve(Fp, [finite["short_weierstrass_A"],
                                  finite["short_weierstrass_B"]])
    assert int(Ebase.cardinality()) == finite["expected_group_order"]
    points = sorted((point for point in Ebase.points() if not point.is_zero()),
                    key=lambda point: (int(point[0]), int(point[1])))
    assert len(points) == 42
    l = protocol["auxiliary_condition"]["prime"]
    Fl = GF(l)
    gate_count = protocol["auxiliary_condition"]["reverse_mestre_count"]
    relation = protocol["relation"]["vector"]

    statuses = Counter()
    gate_counts = Counter()
    total = reduced_hits = rational_hits = accepted = accepted_reduced_hits = accepted_rational_hits = 0
    auxiliary_orders = {}
    raw_path = HERE / "rows-v2.jsonl"
    with raw_path.open("w") as raw:
        for P1, P2 in itertools.permutations(points, 2):
            total += 1
            reduced_event = (relation[0] * P1 + relation[1] * P2).is_zero()
            reduced_hits += int(reduced_event)
            x1, y1 = centered(P1[0], p), centered(P1[1], p)
            x2, y2 = centered(P2[0], p), centered(P2[1], p)
            rec = {
                "reduced_points": [[int(P1[0]), int(P1[1])], [int(P2[0]), int(P2[1])]],
                "lifted_points": [[x1, y1], [x2, y2]],
                "reduced_relation": bool(reduced_event),
                "rational_relation": False,
                "accepted": False,
            }
            if x1 == x2:
                rec["status"] = "same_x"
            else:
                v1 = QQ(y1 * y1 - x1 ** 3)
                v2 = QQ(y2 * y2 - x2 ** 3)
                A = (v1 - v2) / (x1 - x2)
                B = v1 - A * x1
                rec["A"], rec["B"] = str(A), str(B)
                if 4 * A ** 3 + 27 * B ** 2 == 0:
                    rec["status"] = "singular_curve"
                else:
                    E = EllipticCurve(QQ, [A, B])
                    try:
                        Q1, Q2 = E([x1, y1]), E([x2, y2])
                    except (ArithmeticError, TypeError, ValueError):
                        rec["status"] = "invalid_lift"
                    else:
                        assert ZZ(A.denominator()) % p and ZZ(B.denominator()) % p
                        assert Fp(A) == Fp(finite["short_weierstrass_A"])
                        assert Fp(B) == Fp(finite["short_weierstrass_B"])
                        if reduced_event:
                            rec["rational_relation"] = bool(
                                (relation[0] * Q1 + relation[1] * Q2).is_zero())
                            rational_hits += int(rec["rational_relation"])
                        if ZZ(A.denominator()) % l == 0 or ZZ(B.denominator()) % l == 0:
                            rec["status"] = "aux_nonintegral"
                        else:
                            a, b = Fl(A), Fl(B)
                            if 4 * a ** 3 + 27 * b ** 2 == 0:
                                rec["status"] = "aux_bad_reduction"
                            else:
                                key = (int(a), int(b))
                                if key not in auxiliary_orders:
                                    auxiliary_orders[key] = int(EllipticCurve(Fl, [a, b]).cardinality())
                                rec["aux_order"] = auxiliary_orders[key]
                                rank = int(matrix(Fl, [row((x1, y1), Fl), row((x2, y2), Fl)]).rank())
                                rec["aux_incidence_rank"] = rank
                                if rank < 2:
                                    rec["status"] = "aux_rank_lt_2"
                                elif rec["aux_order"] != gate_count:
                                    rec["status"] = "aux_order_other"
                                else:
                                    rec["status"] = "accepted"
                                    rec["accepted"] = True
                                    accepted += 1
                                    accepted_reduced_hits += int(reduced_event)
                                    accepted_rational_hits += int(rec["rational_relation"])
            statuses[rec["status"]] += 1
            if "aux_order" in rec:
                gate_counts[rec["aux_order"]] += 1
            raw.write(json.dumps(rec, sort_keys=True) + "\n")

    assert total == protocol["frozen_predictions"]["total_ordered_pairs"]
    assert reduced_hits == protocol["frozen_predictions"]["reduced_relation_count_in_all_pairs"]
    assert gate_counts[gate_count] == protocol["frozen_predictions"]["eligible_aux_order_4_rows_seen_in_v1"]
    assert accepted == protocol["frozen_predictions"]["eligible_aux_order_4_rank_2_rows_seen_in_v1"]
    assert sum(statuses.values()) == total
    result = {
        "schema": "xedni-varying-curve-selection-result-v2",
        "status": "PASS",
        "protocol_sha256": sha(HERE / "protocol-v2.json"),
        "source_sha256": sha(HERE / "run_v2.py"),
        "sage_runtime_sha256": sha(HERE / "sage-runtime-info-v2.json"),
        "rows_sha256": sha(raw_path),
        "prime": p,
        "group_order": int(Ebase.cardinality()),
        "total_pairs": total,
        "reduced_relation_pairs": reduced_hits,
        "rational_relation_pairs": rational_hits,
        "accepted_pairs": accepted,
        "accepted_reduced_relation_pairs": accepted_reduced_hits,
        "accepted_rational_relation_pairs": accepted_rational_hits,
        "status_counts": dict(statuses),
        "auxiliary_curve_order_counts": dict(gate_counts),
        "full_reduced_event_rate": str(Fraction(reduced_hits, total)),
        "accepted_reduced_event_rate": str(Fraction(accepted_reduced_hits, accepted)) if accepted else None,
        "selection_enrichment": str(Fraction(accepted_reduced_hits, accepted) / Fraction(reduced_hits, total)) if accepted else None,
    }
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
