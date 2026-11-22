"""Independent Sage replay of the ten selected pair sums and public point."""

import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    fixture = json.loads((HERE / "fixture.json").read_text())
    frozen = json.loads((HERE / "protocol.json").read_text())
    control = json.loads((HERE / "control_result.json").read_text())
    runtime = json.loads((HERE / "sage_runtime_info.json").read_text())
    assert runtime["status"] == "verified"
    assert control["status"] == "PASS_TENPAIR_CONSTRUCTED_ASSIGNMENT"
    assert frozen["source_sha256"]["fixture"] == sha(HERE / "fixture.json")
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    field = GF(2**131, name="t", modulus=t**131+t**13+t**2+t+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])
    subgroup_order = 680564733841876926932320129493409985129

    def dec(value):
        return field(ring([(int(value) >> i) & 1 for i in range(131)]))

    def point(encoded):
        return curve(dec(encoded[0]), dec(encoded[1]))

    def encoded(point_):
        return [sum(int(bit) << i for i, bit in enumerate(point_[j].polynomial().list()))
                for j in range(2)]

    def source_x(mask):
        coordinate = sum((field(t**(bit + 1)) for bit in range(18)
                          if mask >> bit & 1), field.zero())
        halftrace, power = field.zero(), coordinate
        for _ in range(66):
            halftrace += power
            power = power**4
        assert halftrace**2 + halftrace == coordinate and halftrace != 0
        return 1 + 1/halftrace

    nodes = []
    columns = []
    for item in fixture["selected"]:
        source_points = []
        for mask in item["masks"]:
            options = list(curve.lift_x(source_x(mask), all=True))
            assert len(options) == 2
            # The recorded sign is checked by the recorded raw pair sum;
            # Sage's ordering of the two y roots need not match Python's.
            source_points.append(options)
        raw = point(item["raw_pair_point"])
        assert any(a + b == raw for a in source_points[0] for b in source_points[1])
        rotated = raw
        for _ in range(item["rotation"]):
            rotated = curve(rotated[0]**2, rotated[1]**2)
        assert encoded(rotated) == item["rotated_pair_point"]
        nodes.append(rotated)
        columns.extend(item["columns"])
    assert len(nodes) == 10 and len(set(columns)) == 20
    for left, right in fixture["tree"]:
        nodes.append(nodes[left] + nodes[right])
    assert len(nodes) == 19
    for expected, actual in zip(fixture["node_points"], nodes):
        assert encoded(actual) == expected
    raw = nodes[-1]
    public = point(fixture["public_target"])
    assert 4 * raw == public
    assert public != curve(0) and subgroup_order * public == curve(0)
    assert control["constructed_public_target"] == encoded(public)
    result = {"status": "PASS_SAGE_TENPAIR_SOURCE_SUM_AND_TARGET",
              "curve_id": frozen["curve_id"], "source_pair_checks": 10,
              "addition_link_checks": 9, "distinct_folded_columns": 20,
              "raw_target": encoded(raw), "public_target": encoded(public),
              "sha256": {"audit_script": sha(Path(__file__)),
                         "fixture": sha(HERE / "fixture.json"),
                         "protocol": sha(HERE / "protocol.json"),
                         "control": sha(HERE / "control_result.json"),
                         "sage_runtime": sha(HERE / "sage_runtime_info.json")}}
    with (HERE / "sage_audit_result.json").open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(result["status"], flush=True)


if __name__ == "__main__":
    main()
