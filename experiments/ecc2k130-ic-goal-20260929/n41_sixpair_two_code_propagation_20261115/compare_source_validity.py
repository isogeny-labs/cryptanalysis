"""Check whether two-code conflicts add to source-pair validity pruning."""

import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
SOURCE = BASE.parent / "n41_w8_two_code_affine_span_20261013" / "cases.jsonl"
GEOMETRY = BASE.parent / "n41_w8_fixed_sum_table_20261009" / "geometry.json"
RESULT = BASE / "result.json"
OUTPUT = BASE / "source_validity_comparison.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compact_code(mask):
    return sum(((mask >> bit) & 1) << index
               for index, bit in enumerate(i for i in range(8) if i != 5))


def main():
    result = json.loads(RESULT.read_text())
    geometry = json.loads(GEOMETRY.read_text())
    source_rows = [json.loads(line) for line in SOURCE.read_text().splitlines()]
    assert len(source_rows) == 1554
    axes = [[compact_code(geometry["blocks"][slot]["states"][4 * index]["a"])
             for index in range(40)] for slot in (0, 1)]
    assert all(len(set(axis)) == 40 for axis in axes)
    assert axes[0] == sorted({row["first_code"] for row in result["rows"]})
    assert axes[1] == sorted({row["second_code"] for row in result["rows"]})
    valid = {(row["left_code"], row["right_code"]) for row in source_rows}
    assert len(valid) == 1554
    missing = {(left, right) for left in range(40) for right in range(40)} - valid
    conflicts = {(axes[0].index(row["first_code"]), axes[1].index(row["second_code"]))
                 for row in result["rows"] if row["status"] == "CONFLICT"}
    assert len(missing) == len(conflicts) == 46
    assert conflicts == missing
    output = {
        "kind": "n41_sixpair_two_code_source_validity_comparison_v1",
        "status": "PASS_CONFLICTS_EQUAL_SOURCE_INVALID_PAIRS",
        "source_sha256": {"result": sha(RESULT), "cases": sha(SOURCE),
                          "geometry": sha(GEOMETRY), "script": sha(Path(__file__))},
        "code_pair_count": 1600,
        "source_admissible_pairs": 1554,
        "source_invalid_pairs": 46,
        "propagation_conflicts": 46,
        "conflicts_on_admissible_pairs": 0,
        "unrejected_invalid_pairs": 0,
        "conflict_pairs_indexed": [list(pair) for pair in sorted(conflicts)],
    }
    with OUTPUT.open("x") as stream:
        json.dump(output, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(output["status"], len(conflicts))


if __name__ == "__main__":
    main()
