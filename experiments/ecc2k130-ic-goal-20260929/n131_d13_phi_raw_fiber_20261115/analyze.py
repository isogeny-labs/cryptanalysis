"""Exact torsion-class convolution; subgroup point occupancy remains heuristic."""

import hashlib
import json
from decimal import Decimal, getcontext
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def convolve(left, right):
    return [sum(left[j] * right[(i-j) % 4] for j in range(4))
            for i in range(4)]


def power(base, exponent):
    result = [1, 0, 0, 0]
    for _ in range(exponent):
        result = convolve(result, base)
    return result


def main():
    protocol = json.loads((HERE / "analysis_protocol.json").read_text())
    assert protocol["status"] == "FROZEN_BEFORE_ANALYSIS"
    assert sha(__file__) == protocol["source_sha256"]
    census = HERE / "census_result.json"
    assert sha(census) == protocol["census_result_sha256"]
    record = json.loads(census.read_text())
    original = [record["original_cofactor_classes_per_position"][str(i)] for i in range(4)]
    image = [record["image_cofactor_classes_per_position"][str(i)] for i in range(4)]
    union = [a+b for a, b in zip(original, image)]
    assert sum(union) == record["union_raw_points_per_position"] == 16536
    r = int(protocol["subgroup_order"])
    getcontext().prec = 40
    rows = {}
    for name, counts in (("original", original), ("image", image), ("union", union)):
        for m in protocol["summand_counts"]:
            classes = power(counts, m)
            assert sum(classes) == sum(counts)**m
            rows[f"{name}_m{m}"] = {
                "per_position_classes": counts,
                "ordered_tuples_by_target_cofactor_class": [str(v) for v in classes],
                "conditional_uniform_subgroup_mean_per_raw_endpoint":
                    [str(Decimal(v)/Decimal(r)) for v in classes],
                "total_tuples": str(sum(classes)),
            }
    print(json.dumps({
        "kind": "n131_d13_union_raw_class_convolution",
        "status": "PASS_EXACT_CLASS_COUNTS_WITH_LABELED_SUBGROUP_HEURISTIC",
        "protocol_sha256": sha(HERE / "analysis_protocol.json"),
        "curve_id": record["curve_id"],
        "subgroup_order": str(r),
        "interpretation": "Integer tuple counts by rational four-torsion class are exact for independent source choices in distinct Frobenius positions; division by r assumes uniform occupancy within each subgroup coset and is not a measured decomposition yield.",
        "rows": rows,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
