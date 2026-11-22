"""Checked Sage group replay of one constructed S3 pair join."""

import hashlib
import itertools
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode(field, value):
    return sum((field.gen() ** i for i in range(41) if value >> i & 1), field.zero())


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial()))


def main():
    protocol = json.loads((HERE / "sage_protocol.json").read_text())
    assert protocol["status"] == "FROZEN"
    assert protocol["sage_replay_sha256"] == sha(HERE / "sage_replay.py")
    assert protocol["sage_runtime_sha256"] == sha(HERE / "sage_runtime_info.json")
    assert protocol["join_stdout_sha256"] == sha(HERE / "join_stdout.log")
    binary = PolynomialRing(GF(2), "T")
    T = binary.gen()
    field = GF(2**41, "T", modulus=T**41 + T**3 + 1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    masks = protocol["masks"]
    choices = [curve.lift_x(decode(field, mask << 1), all=True) for mask in masks]
    assert all(len(points) == 2 for points in choices)
    joined = json.loads((HERE / "join_stdout.log").read_text())
    target = joined["cases"]["constructed"]["target_reciprocal"]
    pair_coords = joined["cases"]["constructed"]["first_exact"]
    hits = []
    for indices in itertools.product(range(2), repeat=4):
        points = [choices[i][index] for i, index in enumerate(indices)]
        left, right = points[0] + points[1], points[2] + points[3]
        total = left + right
        if not left or not right or not total:
            continue
        if encode(1 / left[0]) != pair_coords[0]:
            continue
        if encode(1 / right[0]) != pair_coords[1]:
            continue
        if encode(1 / total[0]) == target:
            hits.append({"sign_indices": list(indices),
                         "sum_point": [encode(total[0]), encode(total[1])],
                         "left_point": [encode(left[0]), encode(left[1])],
                         "right_point": [encode(right[0]), encode(right[1])]})
    assert hits
    result = {"status": "PASS_CHECKED_SAGE_CONSTRUCTED_GROUP_REPLAY",
              "protocol_sha256": sha(HERE / "sage_protocol.json"),
              "curve_id": protocol["curve_id"], "masks": masks,
              "target_reciprocal": target, "pair_reciprocals": pair_coords,
              "valid_sign_assignments": len(hits), "first": hits[0]}
    (HERE / "sage_replay_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
