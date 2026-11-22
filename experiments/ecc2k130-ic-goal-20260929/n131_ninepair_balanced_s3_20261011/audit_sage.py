#!/usr/bin/env sage -python
"""Independent Sage replay of the balanced nine-pair constructed witness."""

import hashlib
import itertools
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / "n131_fixed_seed_ninepair_cubic_20261011"
OLD = ROOT / "n131_fixed_seed_eight_pair_circuit_20261010"
R = 680564733841876926932320129493409985129
LINKS = [(0, 1), (2, 3), (4, 5), (6, 7), (9, 10), (11, 12), (13, 14), (15, 8)]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    fixture = json.loads((BASE / "control_fixture.json").read_text())
    control = json.loads((HERE / "control_result.json").read_text())
    protocol = json.loads((HERE / "protocol.json").read_text())
    runtime = json.loads((HERE / "sage_runtime_info.json").read_text())
    assert runtime["status"] == "verified"
    assert protocol["sha256"]["fixture"] == sha(BASE / "control_fixture.json")
    assert control["protocol_sha256"] == sha(HERE / "protocol.json")
    assert protocol["links"] == [list(edge) for edge in LINKS]
    poly = PolynomialRing(GF(2), "t")
    t = poly.gen()
    field = GF(2**131, name="t", modulus=t**131+t**13+t**2+t+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])

    def encode(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))

    def decode(integer):
        return sum((field(t**bit) for bit in range(131) if integer >> bit & 1),
                   field.zero())

    def coordinate(mask):
        return sum((field(t**(bit+1)) for bit in range(18) if mask >> bit & 1),
                   field.zero())

    def halftrace(value):
        result, power = field.zero(), value
        for _ in range(66):
            result += power
            power = power**4
        assert result**2 + result == value
        return result

    def all_pair_outputs(item):
        lifts = []
        for mask in item["masks"]:
            u = halftrace(coordinate(mask))
            x = 1 + 1/u
            options = sorted(curve.lift_x(x, all=True), key=lambda p: encode(p[1]))
            assert len(options) == 2
            lifts.append(options)
        output = []
        for left, right in itertools.product(*lifts):
            raw = left + right
            if raw == curve(0) or raw[0] in (0, 1):
                continue
            if encode(1/(raw[0] + 1)) != item["unrotated_pair_output_z"]:
                continue
            rotation = item["rotation"]
            point = curve(raw[0]**(1 << rotation), raw[1]**(1 << rotation))
            assert encode(1/(point[0] + 1)) == fixture["pair_rotated_z"][item["slot"]]
            if point not in output:
                output.append(point)
        assert len(output) == 2
        return output

    selected = fixture["selected"]
    assert len(selected) == 9
    points = []
    for item in selected[:8]:
        slot = item["slot"]
        lifts = []
        for mask in item["masks"]:
            u = halftrace(coordinate(mask))
            x = 1 + 1/u
            lifts.append(sorted(curve.lift_x(x, all=True),
                                key=lambda p: encode(p[1])))
        raw = lifts[0][slot & 1] + lifts[1][(slot >> 1) & 1]
        points.append(curve(raw[0]**(1 << item["rotation"]),
                            raw[1]**(1 << item["rotation"])))
    assert sum(points, curve(0)) == curve(
        [decode(x) for x in json.loads((OLD / "planted_chain_result.json").read_text())["raw_target"]])
    target = curve([decode(x) for x in fixture["raw_target"]])
    ninth = [point for point in all_pair_outputs(selected[8])
             if sum(points, curve(0)) + point == target]
    assert len(ninth) == 1
    points.append(ninth[0])
    assert R * (4 * target) == curve(0)
    nodes = points[:]
    for left, right in LINKS[:-1]:
        nodes.append(nodes[left] + nodes[right])
    assert nodes[15] + nodes[8] == target
    assert all(point != curve(0) and point[0] != 0 for point in nodes)
    branch_bits = []
    for index, (left, right) in enumerate(LINKS):
        output = nodes[9 + index] if index < 7 else target
        a, b, c = 1/nodes[left][0], 1/nodes[right][0], 1/output[0]
        total = a + b + c
        assert total.trace() == 0
        branch = a*b*c + halftrace(total**2)
        assert branch in (field.zero(), field.one())
        branch_bits.append(int(branch))
    assert branch_bits == control["branch_bits"]
    result = {"status": "PASS_INDEPENDENT_SAGE_BALANCED_GROUP_REPLAY",
              "curve_id": protocol["curve_id"], "pair_slots": len(points),
              "group_links": len(LINKS), "branch_bits": branch_bits,
              "raw_target": fixture["raw_target"],
              "projected_target": [encode((4 * target)[0]), encode((4 * target)[1])],
              "sha256": {"script": sha(Path(__file__)),
                         "protocol": sha(HERE / "protocol.json"),
                         "control": sha(HERE / "control_result.json"),
                         "fixture": sha(BASE / "control_fixture.json"),
                         "sage_runtime": sha(HERE / "sage_runtime_info.json")}}
    with (HERE / "sage_audit_result.json").open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(result["status"])


if __name__ == "__main__":
    main()
