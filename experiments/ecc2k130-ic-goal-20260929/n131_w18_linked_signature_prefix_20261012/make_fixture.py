"""Construct a ten-pair N131 witness with source slots 0 and 1 linked."""

import copy
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OLD = ROOT / "n131_w18_tenpair_binary_frob_20261012"
NINE = ROOT / "n131_fixed_seed_ninepair_cubic_20261011"
sys.path.insert(0, str(OLD))
import ten as old  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    prior = json.loads((NINE / "control_fixture.json").read_text())
    original = json.loads((OLD / "control_fixture.json").read_text())
    pair_points = old.witness_points(prior) + [tuple(original["last_pair_point"])]
    pair_points[1] = tuple(old.independent.frobenius(value, 16)
                           for value in pair_points[0])
    selected = copy.deepcopy(original["selected"])
    selected[1] = {**copy.deepcopy(selected[0]), "slot": 1, "rotation": 16}
    assert selected[0]["masks"] == selected[1]["masks"]
    nodes = list(pair_points)
    for a, b in old.TREE:
        result = old.independent.point_add(nodes[a], nodes[b])
        assert result is not None and result[0] not in (0, 1)
        nodes.append(result)
    raw = nodes[-1]
    result = {
        "status": "PASS_LINKED_N131_CONSTRUCTED_SOURCE_FIXTURE",
        "seed_mask": 212,
        "selected": selected,
        "signed_pair_points": [list(point) for point in pair_points],
        "raw_target": list(raw),
        "public_target": list(old.orbit9.multiply_by_four(raw)),
        "source_sha256": {
            "maker": sha(Path(__file__)),
            "old_fixture": sha(OLD / "control_fixture.json"),
            "prior_fixture": sha(NINE / "control_fixture.json"),
        },
    }
    with (HERE / "control_fixture.json").open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(result["status"], list(raw), result["public_target"])


if __name__ == "__main__":
    main()
