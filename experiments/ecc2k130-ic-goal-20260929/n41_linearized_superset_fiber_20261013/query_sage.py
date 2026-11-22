"""Exact right-fiber membership via a linearized superset plus source filter."""

import hashlib
import json
import time
from pathlib import Path

from sage.all import GF, PolynomialRing


HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
protocol = json.loads((HERE / "protocol.json").read_text())
assert protocol["status"] == "FROZEN"
for path, digest in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
source_panel = json.loads((GOAL / "n41_joint_fourpair_resultant_20261012/panel.json").read_text())
fiber = json.loads((GOAL / "n41_symbolic_seed_fiber_20261012/panel.json").read_text())
universal = json.loads((GOAL / "n131_w15_rotated_fouratom_inverse_20261010/resultant.json").read_text())
baseline = json.loads((GOAL / "n41_target_derived_fiber_gcd_20261013/subset_result.json").read_text())
reference = {r["id"]: r for r in baseline["cases"]}
base = PolynomialRing(GF(2), "t")
t = base.gen()
field = GF(2**41, name="t", modulus=t**41+t**3+1)
zring = PolynomialRing(field, "z")
vring = PolynomialRing(field, "v")
qring = PolynomialRing(field, "q")
q = qring.gen()
pring = PolynomialRing(qring, "p")


def decode(value):
    return field(base([(int(value) >> i) & 1 for i in range(41)]))


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def pair_parameters(masks, rotation):
    a, b = (decode(mask << 1) for mask in masks)
    return ((a+b)**(1 << rotation), (a*b)**(1 << rotation))


def left_block(masks):
    a, p = pair_parameters(masks[0], 0)
    b, r = pair_parameters(masks[1], 7)
    aa, bb, pp, rr = ([x**i for i in range(9)] for x in (a, b, p, r))
    coeff = [field.zero() for _ in range(9)]
    for ea, eb, ep, eq, ez in universal["terms"]:
        coeff[ez] += aa[ea]*bb[eb]*pp[ep]*rr[eq]
    return zring(coeff)


setup_start = time.monotonic_ns()
T = decode(protocol["target_reciprocal"])
right_a, right_b = [decode(seed << 1)**(1 << rotation)
                    for seed, rotation in zip(fiber["seeds"], fiber["rotations"])]
valid_p = [(decode(a << 1)*decode(b << 1))**(1 << fiber["rotations"][0])
           for a, b in fiber["ordered_masks"][0]]
valid_q = {(decode(a << 1)*decode(b << 1))**(1 << fiber["rotations"][1])
           for a, b in fiber["ordered_masks"][1]}
assert len(valid_p) == len(valid_q) == 32
seed = fiber["seeds"][1]
rotation = fiber["rotations"][1]
all_q = {(decode(a << 1)*decode((a ^ seed) << 1))**(1 << rotation)
         for a in range(256)}
assert len(all_q) == 128 and valid_q <= all_q
gfull = qring.one()
for value in sorted(all_q, key=encode):
    gfull *= q+value
assert gfull.degree() == 128
nonzero_exponents = [i for i, coefficient in enumerate(gfull.list()) if coefficient]
assert all(i > 0 and i & (i-1) == 0 for i in nonzero_exponents)
assert len(nonzero_exponents) <= 8
setup_ns = time.monotonic_ns()-setup_start


def gcd_source_filter(v):
    aa, bb, vv = ([x**i for i in range(9)] for x in (right_a, right_b, v))
    qq = [q**i for i in range(9)]
    coeff = [qring.zero() for _ in range(9)]
    for ea, eb, ep, eq, ez in universal["terms"]:
        coeff[ep] += aa[ea]*bb[eb]*qq[eq]*vv[ez]
    h = pring(coeff)
    gcds = false_roots = 0
    for index, pvalue in enumerate(valid_p):
        gcds += 1
        common = gfull.gcd(h(pvalue))
        for qvalue, _ in common.roots():
            if qvalue in valid_q:
                return True, gcds, false_roots, index, encode(qvalue)
            false_roots += 1
    return False, gcds, false_roots, None, None


cases = []
for family in source_panel["families"]:
    if family["id"] not in protocol["left_family_ids"]:
        continue
    case_start = time.monotonic_ns()
    left_roots = left_block(family["masks"][:2]).roots()
    assert len(left_roots) == 8
    derived = []
    for z, _ in left_roots:
        upper = vring([T*T+z*z, z*T, 1+(z*T)**2])
        assert upper != 0
        derived.extend((z, v) for v, _ in upper.roots())
    hits = []
    gcds = false_roots = 0
    for z, v in derived:
        hit, count, false, p_index, qvalue = gcd_source_filter(v)
        gcds += count
        false_roots += false
        if hit:
            hits.append({"left_reciprocal": encode(z),
                         "right_reciprocal": encode(v),
                         "first_product_index": p_index,
                         "second_product_root": qvalue})
    assert len(derived) == reference[family["id"]]["target_derived_right_candidates"]
    assert bool(hits) == bool(reference[family["id"]]["hits"])
    cases.append({"id": family["id"], "target_derived_right_candidates": len(derived),
                  "gcds": gcds, "rejected_superset_roots": false_roots,
                  "hits": hits, "internal_wall_ns": time.monotonic_ns()-case_start})
    print("CASE", family["id"], gcds, false_roots, len(hits), flush=True)

output = {"status": "PASS_LINEARIZED_SUPERSET_SOURCE_FILTER_PANEL",
          "target_count": 1, "candidate_id": None, "run_id": None,
          "full_product_space_size": len(all_q), "usable_product_count": len(valid_q),
          "linearized_polynomial_nonzero_exponents": nonzero_exponents,
          "setup_ns": setup_ns, "cases": cases,
          "protocol_sha256": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest()}
with (HERE / "result.json").open("x") as stream:
    json.dump(output, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(output["status"], flush=True)
