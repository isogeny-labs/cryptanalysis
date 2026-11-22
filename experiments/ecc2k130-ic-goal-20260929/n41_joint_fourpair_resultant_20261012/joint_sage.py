"""Checked-Sage joint resultant of two four-atom blocks and public target."""

import hashlib
import json
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
FOURPAIR = GOAL / "n131_w18_allseed_fourpair_20261012"
FIXTURE = FOURPAIR / "n41_diagonal/control_fixture.json"
GEOMETRY = GOAL / "n41_w7_entropy_cubic_20261011/w8/geometry.json"
UNIVERSAL = GOAL / "n131_w15_rotated_fouratom_inverse_20261010/resultant.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = json.loads((HERE / "protocol.json").read_text())
assert protocol["status"] == "FROZEN_BEFORE_N41_JOINT_RESULTANT_SAGE"
for path, digest in protocol["sources"].items():
    assert sha(path) == digest, path
panel = json.loads((HERE / "panel.json").read_text())
fixture = json.loads(FIXTURE.read_text())
geometry = json.loads(GEOMETRY.read_text())
universal = json.loads(UNIVERSAL.read_text())
assert universal["status"] == "PASS_UNIVERSAL_ROTATED_FOUR_ATOM_RESULTANT"
assert len(universal["terms"]) == 266
assert len(panel["families"]) == 33
assert panel["target_reciprocal"] == fixture["target_reciprocal"]

base = PolynomialRing(GF(2), "t")
t = base.gen()
field = GF(2**41, name="t", modulus=t**41 + t**3 + 1)
curve = EllipticCurve(field, [1, 0, 0, 0, 1])
ring = PolynomialRing(field, "z")
z = ring.gen()
target = field(base([(fixture["target_reciprocal"] >> i) & 1 for i in range(41)]))
rows = {int(row["mask"]): row for row in geometry["rows"]}


def decode(value):
    return field(base([(int(value) >> i) & 1 for i in range(41)]))


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def frob(point, exponent):
    return curve(point[0] ** (1 << exponent), point[1] ** (1 << exponent))


def pair_parameters(mask_pair, rotation):
    a, b = (decode(mask << 1) for mask in mask_pair)
    return ((a + b) ** (1 << rotation), (a * b) ** (1 << rotation))


def block_polynomial(first, second):
    a, p = first
    b, q = second
    ap = [a**i for i in range(9)]
    bp = [b**i for i in range(9)]
    pp = [p**i for i in range(9)]
    qp = [q**i for i in range(9)]
    coeff = [field.zero() for _ in range(9)]
    for ea, eb, ep, eq, ez in universal["terms"]:
        coeff[ez] += ap[ea] * bp[eb] * pp[ep] * qp[eq]
    return ring(coeff)


def upper(left, right):
    return (1 + (left * right)**2) * target**2 + left * right * target + (left + right)**2


def positive_group_replay():
    pairs = []
    occupied = set()
    for slot, (masks, signs) in enumerate(zip(fixture["masks"], fixture["sign_bits"])):
        points = []
        for mask, sign in zip(masks, signs):
            row = rows[mask]
            assert row["column"] not in occupied
            occupied.add(row["column"])
            raw = curve(*map(decode, row["raw_point"]))
            diagonal = raw + frob(raw, 1)
            assert diagonal != curve(0)
            points.append(-diagonal if sign else diagonal)
        pair = frob(points[0] + points[1], fixture["rotations"][slot])
        assert pair != curve(0) and pair[0] != 0
        assert encode(1 / pair[0]) == fixture["pair_reciprocals"][slot]
        pairs.append(pair)
    assert len(occupied) == 8
    left, right = pairs[0] + pairs[1], pairs[2] + pairs[3]
    assert [encode(1 / left[0]), encode(1 / right[0])] == fixture["intermediate_reciprocals"]
    raw = left + right
    assert [encode(raw[0]), encode(raw[1])] == fixture["raw_target"]
    assert [encode((4 * raw)[0]), encode((4 * raw)[1])] == fixture["public_target"]
    return {"left_reciprocal": encode(1 / left[0]),
            "right_reciprocal": encode(1 / right[0]),
            "raw_target": fixture["raw_target"], "public_target": fixture["public_target"]}


positive = positive_group_replay()
results = []
for family in panel["families"]:
    start = time.monotonic_ns()
    parameters = [pair_parameters(masks, rot)
                  for masks, rot in zip(family["masks"], fixture["rotations"])]
    left_poly = block_polynomial(parameters[0], parameters[1])
    right_poly = block_polynomial(parameters[2], parameters[3])
    polynomial_ns = time.monotonic_ns() - start
    assert 0 < left_poly.degree() <= 8 and 0 < right_poly.degree() <= 8
    left_roots = left_poly.roots()
    right_roots = right_poly.roots()
    assert sum(mult for _, mult in left_roots) == left_poly.degree()
    assert sum(mult for _, mult in right_roots) == right_poly.degree()
    roots_ns = time.monotonic_ns() - start - polynomial_ns
    # Res_v(H_R(v), U(z,v,target)), using the completely split right block.
    right_resultant = ring(right_poly.leading_coefficient()**2)
    for value, multiplicity in right_roots:
        factor = (target**2 + z**2) + (z * target) * value + \
                 (z**2 * target**2 + 1) * value**2
        right_resultant *= factor**multiplicity
    joint = left_poly.resultant(right_resultant)
    resultant_ns = time.monotonic_ns() - start - polynomial_ns - roots_ns
    direct = [(u, v) for u, _ in left_roots for v, _ in right_roots if upper(u, v) == 0]
    direct_ns = time.monotonic_ns() - start - polynomial_ns - roots_ns - resultant_ns
    # Independent resultant evaluation on the left split roots.
    product_check = left_poly.leading_coefficient() ** right_resultant.degree()
    for value, multiplicity in left_roots:
        product_check *= right_resultant(value)**multiplicity
    assert joint == product_check
    assert (joint == 0) == bool(direct)
    if family["id"] == "positive":
        assert joint == 0
        assert (decode(positive["left_reciprocal"]), decode(positive["right_reciprocal"])) in direct
    results.append({"id": family["id"], "kind": family["kind"],
                    "left_degree": int(left_poly.degree()), "right_degree": int(right_poly.degree()),
                    "left_roots": int(sum(mult for _, mult in left_roots)),
                    "right_roots": int(sum(mult for _, mult in right_roots)),
                    "right_resultant_degree": int(right_resultant.degree()),
                    "joint_zero": bool(joint == 0), "direct_pairs": len(direct),
                    "joint_value": str(encode(joint)),
                    "polynomial_ns": polynomial_ns, "roots_ns": roots_ns,
                    "target_resultant_ns": resultant_ns, "direct_check_ns": direct_ns})
    print("FAMILY", family["id"], bool(joint == 0), flush=True)

output = {"status": "PASS_N41_JOINT_FOURPAIR_TARGET_RESULTANT_PANEL",
          "candidate_id": None, "curve_id": fixture["curve_id"],
          "target_reciprocal": fixture["target_reciprocal"],
          "positive_group_replay": positive, "families": results,
          "positive_hits": sum(row["joint_zero"] for row in results if row["id"] == "positive"),
          "control_hits": sum(row["joint_zero"] for row in results if row["id"] != "positive"),
          "protocol_sha256": sha(HERE / "protocol.json")}
with (HERE / "result.json").open("x") as stream:
    json.dump(output, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(output["status"], len(results), output["control_hits"])
