"""Construct an algebraic superset root and reject it by exact source filtering."""

import hashlib
import json
from pathlib import Path

from sage.all import GF, PolynomialRing


HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
protocol = json.loads((HERE / "protocol.json").read_text())
assert protocol["status"] == "FROZEN"
for path, digest in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
fiber = json.loads((GOAL / "n41_symbolic_seed_fiber_20261012/panel.json").read_text())
universal = json.loads((GOAL / "n131_w15_rotated_fouratom_inverse_20261010/resultant.json").read_text())
base = PolynomialRing(GF(2), "t")
t = base.gen()
field = GF(2**41, name="t", modulus=t**41+t**3+1)
qring = PolynomialRing(field, "q")
q = qring.gen()
vring = PolynomialRing(field, "v")


def decode(value):
    return field(base([(int(value) >> i) & 1 for i in range(41)]))


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


a, b = [decode(seed << 1)**(1 << rotation)
        for seed, rotation in zip(fiber["seeds"], fiber["rotations"])]
valid_p = [(decode(x << 1)*decode(y << 1))**(1 << fiber["rotations"][0])
           for x, y in fiber["ordered_masks"][0]]
valid_q = {(decode(x << 1)*decode(y << 1))**(1 << fiber["rotations"][1])
           for x, y in fiber["ordered_masks"][1]}
seed = fiber["seeds"][1]
rotation = fiber["rotations"][1]
all_q = {(decode(x << 1)*decode((x^seed) << 1))**(1 << rotation)
         for x in range(256)}
assert len(all_q) == 128 and len(valid_q) == 32 and valid_q <= all_q
gfull = qring.one()
for value in sorted(all_q, key=encode):
    gfull *= q+value


def h_fixed(pvalue, qvalue):
    aa, bb, pp, qq = ([x**i for i in range(9)] for x in (a, b, pvalue, qvalue))
    coeff = [field.zero() for _ in range(9)]
    for ea, eb, ep, eq, ez in universal["terms"]:
        coeff[ez] += aa[ea]*bb[eb]*pp[ep]*qq[eq]
    return vring(coeff)


def h_in_q(pvalue, vvalue):
    aa, bb, pp, vv = ([x**i for i in range(9)] for x in (a, b, pvalue, vvalue))
    powers_q = [q**i for i in range(9)]
    out = qring.zero()
    for ea, eb, ep, eq, ez in universal["terms"]:
        out += aa[ea]*bb[eb]*pp[ep]*powers_q[eq]*vv[ez]
    return out


positive_v = decode(401891074226)
positive_q = (decode(fiber["ordered_masks"][1][0][0] << 1) *
              decode(fiber["ordered_masks"][1][0][1] << 1))**(1 << rotation)
assert h_fixed(valid_p[0], positive_q)(positive_v) == 0
control = None
invalid_checked = invalid_with_field_roots = invalid_root_count = 0
for bad_q in sorted(all_q-valid_q, key=encode):
    invalid_checked += 1
    planted = h_fixed(valid_p[0], bad_q)
    if planted == 0:
        continue
    roots = planted.roots()
    if roots:
        invalid_with_field_roots += 1
        invalid_root_count += len(roots)
    for vvalue, _ in roots:
        common = gfull.gcd(h_in_q(valid_p[0], vvalue))
        assert bad_q in [root for root, _ in common.roots()]
        accepted = []
        invalid_root_count = 0
        for index, pvalue in enumerate(valid_p):
            roots = [root for root, _ in gfull.gcd(h_in_q(pvalue, vvalue)).roots()]
            accepted.extend((index, encode(root)) for root in roots if root in valid_q)
            invalid_root_count += sum(root not in valid_q for root in roots)
        if not accepted:
            control = {"invalid_product": encode(bad_q),
                       "four_atom_reciprocal": encode(vvalue),
                       "planted_h_zero": True,
                       "unfiltered_superset_gcd_degree": int(common.degree()),
                       "rejected_invalid_roots": invalid_root_count,
                       "usable_source_hits": 0,
                       "first_product_index": 0,
                       "gcds": len(valid_p)}
            break
status = ("PASS_INVALID_SUPERSET_ROOT_REJECTED" if control else
          "COMPLETE_NO_INVALID_FIELD_ROOTS_FOR_FIXED_P" if invalid_with_field_roots == 0 else
          "CENSUS_WITH_VALID_OVERLAP")
assert invalid_checked == 96
output = {"status": status,
          "candidate_id": None, "target_count": 0,
          "full_product_space_size": len(all_q),
          "usable_product_count": len(valid_q),
          "fixed_first_product_index": 0,
          "positive_valid_output_checked": True,
          "excluded_products_checked": invalid_checked,
          "excluded_products_with_field_roots": invalid_with_field_roots,
          "excluded_field_roots": invalid_root_count,
          "control": control,
          "source_sha256": {"protocol": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest(),
                            "query_result": hashlib.sha256((HERE / "result.json").read_bytes()).hexdigest(),
                            "script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}}
with (HERE / "invalid_control.json").open("x") as stream:
    json.dump(output, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(output["status"], invalid_checked, invalid_with_field_roots, invalid_root_count, control, flush=True)
