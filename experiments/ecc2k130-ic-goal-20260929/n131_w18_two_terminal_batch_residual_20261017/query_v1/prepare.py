"""Freeze two 48-state W18 terminal pools and their exact group sums."""

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / "n131_fixed_seed_ninepair_cubic_20261011"
VERIFY = ROOT / "n131_fixed_seed_halftrace_cubic_20261011"
COVERAGE = ROOT / "n131_w18_two_terminal_coverage_20261015"
OLD_POOL = ROOT / "n131_w18_terminal_fiber_20261011" / "pool.json"
sys.path.insert(0, str(BASE))
import run as base  # noqa: E402
sys.path.insert(0, str(VERIFY))
import verify as independent  # noqa: E402

FREE_SIGNS = [(0, 1), (0, 1), (0, 0), (1, 0), (1, 1), (0, 0), (1, 0)]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, data):
    with (HERE / name).open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def rotated_pair(edge, signs, rotation):
    a, b = edge["masks"]
    raw = independent.point_add(independent.point_options(a)[signs[0]],
                                independent.point_options(b)[signs[1]])
    assert raw is not None and raw[0] not in (0, 1)
    rotated = tuple(independent.frobenius(value, rotation) for value in raw)
    assert rotated[0] not in (0, 1)
    return rotated


def states(edges, rotation):
    return [{"state_id": 4*i+2*sa+sb, "edge_index": i,
             "folded_columns": edge["folded_columns"], "signs": [sa, sb],
             "rotation": rotation,
             "rotated_raw_point": list(rotated_pair(edge, (sa,sb), rotation))}
            for i, edge in enumerate(edges)
            for sa in range(2) for sb in range(2)]


def control_subtotal(fixture):
    running = None
    for slot, signs in enumerate(FREE_SIGNS):
        selected = fixture["selected"][slot]
        point = rotated_pair(selected, signs, selected["rotation"])
        unrotated = rotated_pair(selected, signs, 0)
        assert independent.mul(unrotated[0], base.standard_reciprocal(
            selected["unrotated_pair_output_z"])) == 1
        running = independent.point_add(running, point)
        if slot:
            assert running is not None
            assert independent.mul(running[0], base.standard_reciprocal(
                fixture["intermediate_z"][slot-1])) == 1
    return running


def main():
    source = json.loads((COVERAGE / "protocol.json").read_text())
    assert source["status"] == "FROZEN_TWO_TERMINAL_SOURCE_BEFORE_COUNT"
    edges = source["selected_edges"][:12]
    assert len(edges) == 12
    left, right = states(edges, 112), states(edges, 128)
    old = json.loads(OLD_POOL.read_text())
    assert [row["rotated_raw_point"] for row in right[:32]] == [
        row["rotated_raw_point"] for row in old["states"]]
    joint = []
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            if len(set(a["folded_columns"] + b["folded_columns"])) != 4:
                continue
            point = independent.point_add(tuple(a["rotated_raw_point"]),
                                          tuple(b["rotated_raw_point"]))
            joint.append({"left_state_id": i, "right_state_id": j,
                          "raw_sum": list(point) if point is not None else None})
    assert len(joint) == 2080
    distinct = len({tuple(row["raw_sum"]) if row["raw_sum"] is not None else None
                    for row in joint})
    fixture = json.loads((BASE / "control_fixture.json").read_text())
    subtotal = control_subtotal(fixture)
    control_left, control_right = 8, 0
    terminal_sum = independent.point_add(
        tuple(left[control_left]["rotated_raw_point"]),
        tuple(right[control_right]["rotated_raw_point"]))
    control_raw = independent.point_add(subtotal, terminal_sum)
    assert control_raw is not None and control_raw[0] not in (0, 1)
    assert independent.point_add(control_raw,
        (terminal_sum[0], terminal_sum[1] ^ terminal_sum[0])) == subtotal
    save("pool.json", {"status": "PASS_FROZEN_TWO_TERMINAL48_POOL",
                       "candidate_id": None,
                       "left_rotation": 112, "right_rotation": 128,
                       "left_states": left, "right_states": right,
                       "joint_states": joint,
                       "admissible_joint_states": len(joint),
                       "distinct_joint_raw_sums": distinct,
                       "source_sha256": {"script": sha(Path(__file__)),
                                         "coverage_protocol": sha(COVERAGE / "protocol.json"),
                                         "old_pool": sha(OLD_POOL),
                                         "group": sha(VERIFY / "verify.py")}})
    save("control_fixture.json", {
        "status": "PASS_CONSTRUCTED_SEVEN_FREE_TWO_TERMINAL_CONTROL",
        "free_signs": FREE_SIGNS,
        "free_subtotal": list(subtotal),
        "left_state_id": control_left,
        "right_state_id": control_right,
        "terminal_sum": list(terminal_sum),
        "raw_target": list(control_raw),
        "source_sha256": {"script": sha(Path(__file__)),
                          "original_fixture": sha(BASE / "control_fixture.json"),
                          "pool": sha(HERE / "pool.json")}})
    print(json.dumps({"status": "PASS_FROZEN_TWO_TERMINAL48_POOL",
                      "admissible": len(joint), "distinct_sums": distinct}))


if __name__ == "__main__":
    main()
