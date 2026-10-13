"""Independently decode native degree-one GCD and replay its source pair."""

import hashlib
import json
from pathlib import Path

from sage.all import GF, PolynomialRing


HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
native = json.loads((HERE / "native_result.json").read_text())
protocol = json.loads((HERE / "native_protocol.json").read_text())
preflight = json.loads((HERE / "result.json").read_text())
fixture = json.loads((GOAL / "n131_w18_allseed_fourpair_20261012/n131_control_fixture.json").read_text())
universal = json.loads((GOAL / "n131_w15_rotated_fouratom_inverse_20261010/resultant.json").read_text())
for path, digest in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
assert preflight["status"] == "PASS_N131_W18_CONSTRUCTED_SOURCE_RESULTANT_BRIDGE"
assert native["status"] == "COMPLETE_ALGEBRAIC_SCAN"
assert native["processed_product_states"] == native["total_product_states"] == 32947
assert len(native["hits"]) == 1 and native["hits"][0]["gcd_degree"] == 1
base = PolynomialRing(GF(2), "t")
t = base.gen()
field = GF(2**131, name="t", modulus=t**131+t**13+t**2+t+1)


def decode(value):
    return field(base([(int(value) >> i) & 1 for i in range(131)]))


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def limb_value(limbs):
    return sum(int(limb) << (64*i) for i, limb in enumerate(limbs))


hit = native["hits"][0]
p = decode(limb_value(hit["p"]))
c0 = decode(limb_value(hit["gcd_coefficients"][0]))
c1 = decode(limb_value(hit["gcd_coefficients"][1]))
assert c1 != 0
q = c0/c1
assert c0+c1*q == 0
positive_p = decode(fixture["masks"][0][0] << 1)*decode(fixture["masks"][0][1] << 1)
positive_q = (decode(fixture["masks"][1][0] << 1)*
              decode(fixture["masks"][1][1] << 1))**(1 << fixture["rotations"][1])
assert p == positive_p and q == positive_q
support_path = GOAL / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"
columns = {int(mask): int(column) for mask, column in
           (line.split() for line in support_path.read_text().splitlines())}
assert len(columns) == 131307
assert all(mask in columns for pair in fixture["masks"][:2] for mask in pair)
assert all(columns[pair[0]] != columns[pair[1]] for pair in fixture["masks"][:2])
assert [x^y for x,y in fixture["masks"][:2]] == native["seed_masks"]
a = decode(native["seed_masks"][0] << 1)
b = decode(native["seed_masks"][1] << 1)**(1 << 32)
z = decode(fixture["intermediate_reciprocals"][0])
ap, bp, pp, qp, zp = ([value**i for i in range(9)] for value in (a,b,p,q,z))
h_value = field.zero()
for ea, eb, ep, eq, ez in universal["terms"]:
    h_value += ap[ea]*bp[eb]*pp[ep]*qp[eq]*zp[ez]
assert h_value == 0
output = {
    "status": "PASS_NATIVE_W18_GCD_SOURCE_REPLAY",
    "candidate_id": None, "target_kind": "constructed_correctness_control",
    "hit_count": 1, "gcd_degree": 1,
    "first_product": encode(p), "second_product": encode(q),
    "first_masks": fixture["masks"][0], "second_masks": fixture["masks"][1],
    "second_product_usable": True, "fouratom_resultant_zero": True,
    "source_sha256": {
        "native_protocol": hashlib.sha256((HERE / "native_protocol.json").read_bytes()).hexdigest(),
        "native_result": hashlib.sha256((HERE / "native_result.json").read_bytes()).hexdigest(),
        "preflight_result": hashlib.sha256((HERE / "result.json").read_bytes()).hexdigest(),
        "sage_runtime_info": hashlib.sha256((HERE / "sage_runtime_info.json").read_bytes()).hexdigest(),
        "auditor": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    },
}
with (HERE / "native_audit.json").open("x") as stream:
    json.dump(output, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(output["status"], output["first_product"], output["second_product"])
