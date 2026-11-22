"""Count exact four-torsion-class tuples for six fixed source branches."""

import hashlib
import json
from decimal import Decimal, getcontext
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "protocol.json"
FORMULA = HERE / "formula_receipt.json"
RESULT = HERE / "class_result.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def multiply(left, right):
    out = [0, 0, 0, 0]
    for a in range(4):
        for b in range(4):
            out[(a + b) % 4] += left[a] * right[b]
    return out


def main():
    p = json.loads(PROTOCOL.read_text())
    assert p["status"] == "FROZEN_BEFORE_BUILD"
    assert p["class_source_sha256"] == sha(__file__)
    for name, digest in p["input_sha256"].items():
        assert sha(p["inputs"][name]) == digest
    assert not RESULT.exists()
    formula = json.loads(FORMULA.read_text())
    assert formula["status"] == "PASS_FORMULA_BUILD"
    assert formula["fixed_original_positions"] == p["fixed_original_positions"]
    census = json.loads(Path(p["inputs"]["raw_census"]).read_text())
    assert census["status"] == "PASS_EXACT_POSITION_CENSUS"
    original = [int(census["original_cofactor_classes_per_position"][str(i)])
                for i in range(4)]
    image = [int(census["image_cofactor_classes_per_position"][str(i)])
             for i in range(4)]
    union = [a + b for a, b in zip(original, image)]
    assert sum(original) == sum(image) == 8268
    assert sum(union) == 16536
    counts = [1, 0, 0, 0]
    for position in range(p["summand_count"]):
        counts = multiply(counts, original if position in p["fixed_original_positions"]
                          else union)
    assert sum(counts) == 8268**6 * 16536**6
    order = int(p["subgroup_order"])
    getcontext().prec = 55
    result = {
        "kind": "n131_d13_halfbranch_m12_class_screen_v1",
        "status": "PASS_EXACT_CLASS_COUNTS",
        "protocol_sha256": sha(PROTOCOL),
        "formula_receipt_sha256": sha(FORMULA),
        "source_classes": original,
        "image_classes": image,
        "union_classes": union,
        "fixed_original_positions": p["fixed_original_positions"],
        "ordered_raw_tuples_by_cofactor_class": [str(value) for value in counts],
        "conditional_uniform_subgroup_mean_per_endpoint": [str(Decimal(value) / Decimal(order))
                                                            for value in counts],
        "interpretation": "Class tuple counts are exact for independent position choices; uniform occupancy within a subgroup coset is a model, not measured relation yield.",
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"],
                      "conditional_uniform_means": result["conditional_uniform_subgroup_mean_per_endpoint"]},
                     sort_keys=True))


if __name__ == "__main__":
    main()
