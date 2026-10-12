"""Direct nested Sylvester resultants, with no root enumeration."""

import hashlib
import json
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
protocol = json.loads((HERE / "direct_protocol.json").read_text())
assert protocol["status"] == "FROZEN_BEFORE_DIRECT_NESTED_RESULTANT"
for path, digest in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
panel = json.loads((HERE / "panel.json").read_text())
reference = json.loads((HERE / "result.json").read_text())
fixture = json.loads((GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal/control_fixture.json").read_text())
universal = json.loads((GOAL / "n131_w15_rotated_fouratom_inverse_20261010/resultant.json").read_text())
base = PolynomialRing(GF(2), "t")
t = base.gen()
field = GF(2**41, name="t", modulus=t**41+t**3+1)
ring = PolynomialRing(field, "z")
z = ring.gen()
vring = PolynomialRing(ring, "v")
v = vring.gen()
target = field(base([(panel["target_reciprocal"] >> i) & 1 for i in range(41)]))
ref = {row["id"]: row for row in reference["families"]}


def decode(value):
    return field(base([(int(value) >> i) & 1 for i in range(41)]))


def pair_parameters(masks, rotation):
    a, b = (decode(mask << 1) for mask in masks)
    return ((a+b)**(1 << rotation), (a*b)**(1 << rotation))


def block(first, second):
    a, p = first
    b, q = second
    aa = [a**i for i in range(9)]
    bb = [b**i for i in range(9)]
    pp = [p**i for i in range(9)]
    qq = [q**i for i in range(9)]
    coeff = [field.zero() for _ in range(9)]
    for ea, eb, ep, eq, ez in universal["terms"]:
        coeff[ez] += aa[ea]*bb[eb]*pp[ep]*qq[eq]
    return ring(coeff)


upper = (1+(z*v)**2)*target**2 + z*v*target + (z+v)**2
rows = []
for family in panel["families"]:
    start = time.monotonic_ns()
    params = [pair_parameters(masks, rot)
              for masks, rot in zip(family["masks"], fixture["rotations"])]
    left = block(params[0], params[1])
    right = block(params[2], params[3])
    build_ns = time.monotonic_ns()-start
    inner = vring(right.list()).resultant(upper)
    inner_ns = time.monotonic_ns()-start-build_ns
    joint = left.resultant(inner)
    outer_ns = time.monotonic_ns()-start-build_ns-inner_ns
    assert (joint == 0) == ref[family["id"]]["joint_zero"]
    assert str(sum(int(bit) << i for i, bit in enumerate(joint.polynomial().list()))) == ref[family["id"]]["joint_value"]
    rows.append({"id":family["id"],"joint_zero":bool(joint==0),
                 "build_ns":build_ns,"inner_resultant_ns":inner_ns,
                 "outer_resultant_ns":outer_ns,"inner_degree":int(inner.degree())})
    print("DIRECT",family["id"],flush=True)

output={"status":"PASS_DIRECT_NESTED_RESULTANT_PANEL","candidate_id":None,
        "families":rows,"protocol_sha256":hashlib.sha256((HERE/'direct_protocol.json').read_bytes()).hexdigest()}
with (HERE/'direct_result.json').open('x') as out:
    json.dump(output,out,indent=2,sort_keys=True);out.write('\n')
print(output["status"],len(rows))
