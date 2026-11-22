"""Independent Sage group replay of the linked N131 constructed control."""

import hashlib
import itertools
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SUPPORT = ROOT / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"
R = 680564733841876926932320129493409985129
N = 131


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE / "fixture_audit_protocol.json").read_text())
for name, path in {
    "audit_source": HERE / "audit_fixture_sage.py",
    "fixture": HERE / "control_fixture.json",
    "control": HERE / "control_result.json",
    "source_table": SUPPORT,
    "sage_runtime": HERE / "sage_runtime_info.json",
}.items():
    assert sha(path) == protocol["sha256"][name], name

fixture = json.loads((HERE / "control_fixture.json").read_text())
control = json.loads((HERE / "control_result.json").read_text())
assert fixture["status"] == "PASS_LINKED_N131_CONSTRUCTED_SOURCE_FIXTURE"
assert control["status"] == "PASS_FULL_N131_LINKED_TENPAIR_CONSTRUCTED_WITNESS"
assert control["constructed_public_target"] == fixture["public_target"]
columns = {int(mask): int(column) for mask, column in
           (line.split() for line in SUPPORT.read_text().splitlines())}

ring = PolynomialRing(GF(2), "t")
t = ring.gen()
field = GF(2**N, name="t", modulus=t**N + t**13 + t**2 + t + 1)
curve = EllipticCurve(field, [1, 0, 0, 0, 1])


def dec(value):
    return field(ring([(int(value) >> i) & 1 for i in range(N)]))


def enc(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def halftrace(value):
    result, power = field.zero(), value
    for _ in range((N + 1) // 2):
        result += power
        power = power**4
    assert result**2 + result == value
    return result


def frob(point, exponent):
    return curve(point[0]**(1 << exponent), point[1]**(1 << exponent))


selected = fixture["selected"]
assert len(selected) == len(fixture["signed_pair_points"]) == 10
assert selected[0]["masks"] == selected[1]["masks"]
assert selected[0]["unrotated_pair_output_z"] == selected[1]["unrotated_pair_output_z"]
assert selected[0]["rotation"] == 0 and selected[1]["rotation"] == 16
all_columns = [columns[m] for item in selected for m in item["masks"]]
assert len(set(all_columns)) == 18
assert all_columns[:2] == all_columns[2:4]
assert len(all_columns[4:]) == len(set(all_columns[4:])) == 16
assert not (set(all_columns[:2]) & set(all_columns[4:]))

group_points = []
for slot, item in enumerate(selected):
    a, b = item["masks"]
    assert a ^ b == 212 and a in columns and b in columns
    assert item["folded_columns"] == [columns[a], columns[b]]
    point = curve(*map(dec, fixture["signed_pair_points"][slot]))
    raw = frob(point, (N - item["rotation"]) % N)
    assert enc(1 / (raw[0] + 1)) == item["unrotated_pair_output_z"]
    atom_options = []
    for mask in (a, b):
        coordinate = dec(mask << 1)
        u = halftrace(coordinate)
        atom_options.append(curve.lift_x(1 + 1/u, all=True))
    assert any(x + y == raw for x, y in itertools.product(*atom_options))
    group_points.append(point)
assert group_points[1] == frob(group_points[0], 16)

raw_target = curve(*map(dec, fixture["raw_target"]))
assert sum(group_points, curve(0)) == raw_target
public = 4 * raw_target
assert [enc(public[0]), enc(public[1])] == fixture["public_target"]
assert R * public == curve(0)
result = {
    "status": "PASS_INDEPENDENT_SAGE_N131_LINKED_CONSTRUCTED_GROUP_REPLAY",
    "candidate_id": None,
    "source_pair_slots": 10,
    "free_source_pair_codes": 9,
    "distinct_folded_columns": len(set(all_columns)),
    "raw_target": fixture["raw_target"],
    "public_target": fixture["public_target"],
    "sha256": protocol["sha256"],
}
with (HERE / "sage_fixture_result.json").open("x") as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(result["status"], result["distinct_folded_columns"])
