"""Independently audit twelve-position class counts by four-character transform."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "n131_d13_union_m12_halfbranch_20261115" / "class_result.json"
RESULT = HERE / "class_closed_form_result.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    assert not RESULT.exists()
    source = json.loads(SOURCE.read_text())
    a = source["source_classes"]
    c = source["union_classes"]
    assert a == [2160, 2067, 1974, 2067]
    assert c == [6294, 2067, 6108, 2067]
    # At characters 1 and 3, both vectors have real transform value 186.
    assert a[1] == a[3] and c[1] == c[3]
    assert a[0] - a[2] == c[0] - c[2] == 186
    # Character 2 vanishes after six original-source convolutions.
    assert a[0] - a[1] + a[2] - a[3] == 0
    total = sum(a)**6 * sum(c)**6
    imbalance = 186**12
    assert total % 4 == 0 and (total - 2 * imbalance) % 4 == 0
    expected = [(total + 2 * imbalance) // 4, total // 4,
                (total - 2 * imbalance) // 4, total // 4]
    actual = [int(value) for value in source["ordered_raw_tuples_by_cofactor_class"]]
    assert expected == actual
    receipt = {
        "kind": "n131_d13_halfbranch_m12_four_character_audit_v1",
        "status": "PASS_INDEPENDENT_CLASS_FORMULA",
        "source_sha256": sha(SOURCE),
        "audit_source_sha256": sha(__file__),
        "character_1_value_each_position": 186,
        "original_character_2_value": 0,
        "total_ordered_tuples": str(total),
        "class_zero_minus_class_two": str(imbalance),
        "checked_classes": 4,
    }
    RESULT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": receipt["status"],
                      "checked_classes": receipt["checked_classes"]}, sort_keys=True))


if __name__ == "__main__":
    main()
