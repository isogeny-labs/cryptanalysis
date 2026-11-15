"""Control the Sage field/chart operations used by SAT model replay."""

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
REPLAY = HERE / "replay_sat.py"
PLANTED = EXP / "n131_d13_union_arity_20261115" / "planted_result.json"
RESULT = HERE / "replay_primitives_result.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    assert not RESULT.exists()
    spec = importlib.util.spec_from_file_location("independent_replay", REPLAY)
    replay = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(replay)
    planted = json.loads(PLANTED.read_text())
    geometry = json.loads(replay.GEOMETRY.read_text())
    field, decode, encode = replay.sage_field()
    curve = replay.EllipticCurve(field, [1, 0, 0, 0, 1])
    zero = curve(0)
    masks = [int(x, 16) for x in geometry["domain"]["basis_coordinate_masks_hex"]]
    for position, (code, branch, expected_phi) in enumerate(zip(
            planted["leaf_codes"], planted["leaf_branch_bits"],
            planted["leaf_phi_masks"])):
        mask = 0
        for bit, basis_mask in enumerate(masks):
            if code >> bit & 1:
                mask ^= basis_mask
        source_phi = decode(mask) ** (2**position)
        x = 1 / source_phi + 1
        points = curve.lift_x(x, all=True)
        assert len(points) == 2
        point = points[0]
        if branch:
            point += curve(point[0]**2, point[1]**2)
        assert encode(replay.chart(point, zero)) == expected_phi
    official = geometry["official_single_target_cofactor_fiber"]["four_verified_lifts"]
    q = curve(decode(int(official[0]["target_coordinates"][0])),
              decode(int(official[0]["target_coordinates"][1])))
    order = int(json.loads((EXP / "n131_d13_union_arity_20261115" / "result.json").read_text())["subgroup_order"])
    assert order * q == zero
    receipt = {"kind": "n131_d13_union_m12_sls600_replay_primitives_control_v1",
               "status": "PASS_TWELVE_SOURCE_CHARTS_AND_PUBLIC_SUBGROUP",
               "replay_source_sha256": sha(REPLAY),
               "planted_result_sha256": sha(PLANTED),
               "checked_leaf_charts": 12,
               "public_subgroup_order": str(order)}
    RESULT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": receipt["status"],
                      "checked_leaf_charts": 12}, sort_keys=True))


if __name__ == "__main__":
    main()
