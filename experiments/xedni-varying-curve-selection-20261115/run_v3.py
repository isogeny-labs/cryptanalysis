"""Exact second-auxiliary-prime filter on the frozen v2 rational curves."""

import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

from audit import add, auxiliary_order, incidence_row

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol_path = HERE / "protocol-v3.json"
    protocol = json.loads(protocol_path.read_text())
    input_path = HERE / protocol["input"]["rows"]
    assert sha(input_path) == protocol["input"]["rows_sha256"]
    selected = [json.loads(line) for line in input_path.read_text().splitlines()
                if json.loads(line)["accepted"]]
    frozen = protocol["frozen_predictions"]
    assert len(selected) == frozen["input_accepted_ordered_pairs"]
    assert sum(row["reduced_relation"] for row in selected) == frozen["input_accepted_reduced_relation_pairs"]
    assert sum(row["rational_relation"] for row in selected) == frozen["input_accepted_rational_relation_pairs"]

    spec = protocol["second_auxiliary_prime"]
    l = spec["prime"]
    strict = spec["strict_order"]
    weak = spec["weak_epsilon_1_order"]
    status_counts = Counter()
    order_counts = Counter()
    local_relation_count = 0
    local_reduced_event_count = 0
    strict_count = strict_reduced = strict_rational = 0
    weak_count = weak_reduced = weak_rational = 0
    rows_path = HERE / "rows-v3.jsonl"
    with rows_path.open("w") as out:
        for old in selected:
            A, B = Fraction(old["A"]), Fraction(old["B"])
            p1 = tuple(value % l for value in old["lifted_points"][0])
            p2 = tuple(value % l for value in old["lifted_points"][1])
            row = {
                "reduced_points": old["reduced_points"],
                "lifted_points": old["lifted_points"],
                "A": old["A"], "B": old["B"],
                "reduced_relation": old["reduced_relation"],
                "rational_relation": old["rational_relation"],
                "strict_accepted": False,
                "weak_accepted": False,
            }
            if A.denominator % l == 0 or B.denominator % l == 0:
                row["status"] = "nonintegral"
            else:
                a = A.numerator * pow(A.denominator, -1, l) % l
                b = B.numerator * pow(B.denominator, -1, l) % l
                row["A_mod11"], row["B_mod11"] = a, b
                if (4 * a ** 3 + 27 * b ** 2) % l == 0:
                    row["status"] = "bad_reduction"
                else:
                    order = auxiliary_order(a, b, l)
                    rank = 1 if incidence_row(*p1, l) == incidence_row(*p2, l) else 2
                    twice_p2 = add(p2, p2, a, l)
                    relation_sum = add(p1, twice_p2, a, l)
                    local_relation = relation_sum is None
                    row.update({"aux_order": order, "aux_rank": rank,
                                "P1_mod11": p1, "P2_mod11": p2,
                                "relation_sum_mod11": relation_sum,
                                "local_relation": local_relation})
                    order_counts[order] += 1
                    local_relation_count += int(local_relation)
                    local_reduced_event_count += int(local_relation and old["reduced_relation"])
                    assert not old["rational_relation"] or local_relation
                    if rank < 2:
                        row["status"] = "rank_lt_2"
                    else:
                        row["status"] = "eligible"
                        row["strict_accepted"] = order == strict
                        row["weak_accepted"] = order == weak
                        strict_count += int(row["strict_accepted"])
                        weak_count += int(row["weak_accepted"])
                        strict_reduced += int(row["strict_accepted"] and old["reduced_relation"])
                        weak_reduced += int(row["weak_accepted"] and old["reduced_relation"])
                        strict_rational += int(row["strict_accepted"] and old["rational_relation"])
                        weak_rational += int(row["weak_accepted"] and old["rational_relation"])
            status_counts[row["status"]] += 1
            out.write(json.dumps(row, sort_keys=True) + "\n")

    print(json.dumps({
        "schema": "xedni-varying-curve-selection-result-v3",
        "status": "PASS",
        "protocol_sha256": sha(protocol_path),
        "source_sha256": sha(HERE / "run_v3.py"),
        "input_rows_sha256": sha(input_path),
        "rows_sha256": sha(rows_path),
        "second_auxiliary_prime": l,
        "input_pairs": len(selected),
        "status_counts": dict(status_counts),
        "auxiliary_curve_order_counts": dict(order_counts),
        "good_reduction_local_relation_count": local_relation_count,
        "good_reduction_local_and_reduced_relation_count": local_reduced_event_count,
        "strict_order": strict,
        "strict_accepted_pairs": strict_count,
        "strict_accepted_reduced_relations": strict_reduced,
        "strict_accepted_rational_relations": strict_rational,
        "weak_order": weak,
        "weak_accepted_pairs": weak_count,
        "weak_accepted_reduced_relations": weak_reduced,
        "weak_accepted_rational_relations": weak_rational,
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
