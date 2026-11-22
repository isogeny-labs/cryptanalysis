"""Independent checked-Sage replay of the N41 four-pair forward-root chart."""

import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
SOURCE = GOAL / "n131_w18_allseed_fourpair_20261012"
GEOMETRY = GOAL / "n41_w7_entropy_cubic_20261011/w8/geometry.json"
FIXTURE = SOURCE / "n41_diagonal/control_fixture.json"
TREE = ((0, 1), (2, 3), (4, 5), (6, 7), (8, 9), (10, 11), (12, 13))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = json.loads((HERE / "audit_protocol.json").read_text())
assert protocol["status"] == "FROZEN_BEFORE_SAGE_AUDIT"
for path, digest in protocol["sources"].items():
    assert sha(path) == digest, path
chart = json.loads((HERE / "chart.json").read_text())
fixture = json.loads(FIXTURE.read_text())
geometry = json.loads(GEOMETRY.read_text())
rows = {int(row["mask"]): row for row in geometry["rows"]}
ring = PolynomialRing(GF(2), "t")
t = ring.gen()
field = GF(2**41, name="t", modulus=t**41 + t**3 + 1)
curve = EllipticCurve(field, [1, 0, 0, 0, 1])


def decode(value):
    return field(ring([(int(value) >> i) & 1 for i in range(41)]))


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def xy(point):
    return [encode(point[0]), encode(point[1])]


def frob(point, exponent):
    return curve(point[0] ** (1 << exponent), point[1] ** (1 << exponent))


def halftrace(value):
    answer = field.zero()
    for _ in range(21):
        answer += value
        value = value**4
    return answer


leaves = []
occupied = set()
for slot, (pair, signs) in enumerate(zip(fixture["masks"], fixture["sign_bits"])):
    for mask, sign in zip(pair, signs):
        assert mask in rows and rows[mask]["column"] not in occupied
        occupied.add(rows[mask]["column"])
        original = curve(*map(decode, rows[mask]["raw_point"]))
        diagonal = original + frob(original, 1)
        assert diagonal != curve(0) and diagonal[0] != 0
        assert 1 / diagonal[0] == decode(mask << 1)
        leaf = frob(-diagonal if sign else diagonal, fixture["rotations"][slot])
        leaves.append(leaf)
assert len(occupied) == 8
assert chart["masks"] == [mask for pair in fixture["masks"] for mask in pair]
assert chart["sign_bits"] == [bit for pair in fixture["sign_bits"] for bit in pair]
nodes = list(leaves)
checks = []
for index, (left, right) in enumerate(TREE):
    point = nodes[left] + nodes[right]
    assert point != curve(0) and point[0] != 0
    nodes.append(point)
    a, b, z = 1 / nodes[left][0], 1 / nodes[right][0], 1 / point[0]
    p, aa, cc = a * b, 1 + (a * b)**2, (a + b)**2
    assert aa * z**2 + p * z + cc == 0
    bit = chart["root_branch_bits"][index]
    if aa == 0:
        produced = cc
    else:
        argument = aa * cc / p**2
        h = halftrace(argument)
        assert h**2 + h == argument
        produced = (p / aa) * (h + bit)
    assert produced == z
    checks.append({"index": index, "branch": bit, "exceptional_aa_zero": bool(aa == 0),
                   "reciprocal": encode(z)})
assert [xy(point) for point in nodes] == chart["point_chain"]
assert xy(nodes[-1]) == fixture["raw_target"]
assert 1 / nodes[-1][0] == decode(fixture["target_reciprocal"])
assert xy(4 * nodes[-1]) == fixture["public_target"]
result = {"status": "PASS_INDEPENDENT_N41_ALLSEED_FORWARD_CHART",
          "curve_id": fixture["curve_id"], "distinct_folded_columns": len(occupied),
          "source_points": len(leaves), "root_links": len(checks), "checks": checks,
          "raw_target": xy(nodes[-1]), "public_target": xy(4 * nodes[-1]),
          "protocol_sha256": sha(HERE / "audit_protocol.json")}
with (HERE / "audit_result.json").open("x") as stream:
    json.dump(result, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(result["status"], len(checks))
