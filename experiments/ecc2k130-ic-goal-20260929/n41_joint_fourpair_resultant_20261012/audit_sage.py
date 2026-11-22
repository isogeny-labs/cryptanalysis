"""Independent group-law replay of every target-conditioned source family."""

import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
panel = json.loads((HERE / "panel.json").read_text())
result = json.loads((HERE / "result.json").read_text())
fixture = json.loads((GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal/control_fixture.json").read_text())
geometry = json.loads((GOAL / "n41_w7_entropy_cubic_20261011/w8/geometry.json").read_text())
rows = {int(row["mask"]): row for row in geometry["rows"]}
base = PolynomialRing(GF(2), "t")
t = base.gen()
field = GF(2**41, name="t", modulus=t**41 + t**3 + 1)
curve = EllipticCurve(field, [1, 0, 0, 0, 1])


def decode(value):
    return field(base([(int(value) >> i) & 1 for i in range(41)]))


def frob(point, exponent):
    if point == curve(0):
        return point
    return curve(point[0] ** (1 << exponent), point[1] ** (1 << exponent))


def diagonal(mask):
    raw = curve(*map(decode, rows[mask]["raw_point"]))
    return raw + frob(raw, 1)


def pair_points(masks, rotation):
    a, b = map(diagonal, masks)
    return [frob(sa * a + sb * b, rotation)
            for sa in [1, -1] for sb in [1, -1]]


target = decode(panel["target_reciprocal"])
assert target != 0
expected = {row["id"]: row for row in result["families"]}
audit_rows = []
for family in panel["families"]:
    parts = [pair_points(masks, rot)
             for masks, rot in zip(family["masks"], fixture["rotations"])]
    left = [a + b for a in parts[0] for b in parts[1]]
    right = [a + b for a in parts[2] for b in parts[3]]
    matches = [(i, j) for i, a in enumerate(left) for j, b in enumerate(right)
               if a + b != curve(0) and (a + b)[0] * target == 1]
    row = expected[family["id"]]
    assert bool(matches) == row["joint_zero"], family["id"]
    audit_rows.append({"id": family["id"], "joint_zero": row["joint_zero"],
                       "group_law_match_count": len(matches),
                       "signed_assignments_checked": len(left) * len(right)})

assert len(audit_rows) == 33
assert audit_rows[0]["group_law_match_count"] > 0
output = {"status": "PASS_INDEPENDENT_N41_GROUP_LAW_PANEL",
          "candidate_id": None, "families": audit_rows,
          "total_signed_assignments": sum(row["signed_assignments_checked"] for row in audit_rows),
          "result_sha256": hashlib.sha256((HERE / "result.json").read_bytes()).hexdigest(),
          "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
with (HERE / "audit.json").open("x") as stream:
    json.dump(output, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(output["status"], output["total_signed_assignments"])
