"""Extend the checked nine-pair constructed assignment by one disjoint W18 pair."""

import hashlib
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
NINE = ROOT / "n131_fixed_seed_ninepair_cubic_20261011"
GROUP = ROOT / "n131_fixed_seed_halftrace_cubic_20261011"
SUPPORT = ROOT / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"
sys.path.insert(0, str(GROUP))
import verify as independent  # noqa: E402


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def shifted_reciprocal(point):
    assert point is not None and point[0] not in (0, 1)
    return independent.inverse(point[0] ^ 1)


prior = json.loads((NINE / "control_fixture.json").read_text())
columns = {int(mask): int(column) for mask, column in
           (line.split() for line in SUPPORT.read_text().splitlines())}
occupied = {column for item in prior["selected"] for column in item["folded_columns"]}
options = [(a, a ^ 212) for a in sorted(columns)
           if a < a ^ 212 and a ^ 212 in columns
           and columns[a] != columns[a ^ 212]
           and not ({columns[a], columns[a ^ 212]} & occupied)]
assert options
a, b = options[0]
raw_pair = independent.point_add(independent.point_options(a)[0],
                                 independent.point_options(b)[0])
assert raw_pair is not None and raw_pair[0] not in (0, 1)
rotation = 8
rotated = tuple(independent.frobenius(value, rotation) for value in raw_pair)
target = independent.point_add(tuple(prior["raw_target"]), rotated)
assert target is not None and target[0] not in (0, 1)
new_item = {"slot": 9, "rotation": rotation, "masks": [a, b],
            "folded_columns": [columns[a], columns[b]],
            "unrotated_pair_output_z": shifted_reciprocal(raw_pair),
            "product_p": independent.mul(independent.coordinate(a),
                                          independent.coordinate(b))}
result = {
    "status": "PASS_TENPAIR_CONSTRUCTED_SOURCE_FIXTURE",
    "seed_mask": 212,
    "selected": prior["selected"] + [new_item],
    "prior_raw_target": prior["raw_target"],
    "last_pair_point": list(rotated),
    "raw_target": list(target),
    "raw_target_z": shifted_reciprocal(target),
    "source_sha256": {"maker": sha(Path(__file__)),
                      "prior_fixture": sha(NINE / "control_fixture.json"),
                      "support": sha(SUPPORT),
                      "group_arithmetic": sha(GROUP / "verify.py")},
}
with (HERE / "control_fixture.json").open("x") as stream:
    json.dump(result, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(result["status"], [a, b], list(target))
