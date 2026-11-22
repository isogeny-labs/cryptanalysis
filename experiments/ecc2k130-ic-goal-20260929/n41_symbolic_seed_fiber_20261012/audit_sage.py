"""Independent group-law enumeration for each symbolic product fiber."""

import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
panel = json.loads((HERE / "panel.json").read_text())
geometry = json.loads((GOAL / "n41_w7_entropy_cubic_20261011/w8/geometry.json").read_text())
rows = {int(row["mask"]): row for row in geometry["rows"]}
base = PolynomialRing(GF(2), "t")
t = base.gen()
field = GF(2**41, name="t", modulus=t**41 + t**3 + 1)
curve = EllipticCurve(field, [1, 0, 0, 0, 1])


def decode(value):
    return field(base([(int(value) >> i) & 1 for i in range(41)]))


def frob(point, rotation):
    if point == curve(0):
        return point
    return curve(point[0] ** (1 << rotation), point[1] ** (1 << rotation))


def point(mask):
    raw = curve(*map(decode, rows[mask]["raw_point"]))
    return raw + frob(raw, 1)


def signed_pair_states(slot, size):
    states = []
    for a, b in panel["ordered_masks"][slot][:size]:
        pa, pb = point(a), point(b)
        states.extend(frob(sa * pa + sb * pb, panel["rotations"][slot])
                      for sa in (1, -1) for sb in (1, -1))
    return states


result = []
for size in panel["sizes"]:
    left, right = [signed_pair_states(slot, size) for slot in (0, 1)]
    assert len(left) == 4 * size and len(right) == 4 * size
    sums = [a + b for a in left for b in right]
    for coordinate in ("positive", "negative"):
        value = decode(panel[coordinate + "_reciprocal"])
        matches = sum(p != curve(0) and p[0] * value == 1 for p in sums)
        case_file = HERE / f"result_{size}_{coordinate}.json"
        case = json.loads(case_file.read_text()) if case_file.exists() else None
        if case is not None:
            assert case["joint_zero"] == bool(matches), (size, coordinate)
        result.append({"size": size, "coordinate": coordinate, "signed_assignments": len(sums),
                       "group_law_matches": matches, "symbolic_status": case["status"] if case else None})
output = {"status": "PASS_INDEPENDENT_SEED_FIBER_GROUP_AUDIT", "candidate_id": None,
          "cases": result, "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
with (HERE / "audit.json").open("x") as stream:
    json.dump(output, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(output["status"], len(result))
