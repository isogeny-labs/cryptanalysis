"""Target-derived right coordinates, followed by an exact unresolved-fiber GCD."""

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
assert source_panel["target_reciprocal"] == protocol["target_reciprocal"]
base = PolynomialRing(GF(2), "t")
t = base.gen()
field = GF(2**41, name="t", modulus=t**41 + t**3 + 1)
vring = PolynomialRing(field, "v")
v = vring.gen()
qring = PolynomialRing(field, "q")
q = qring.gen()
pring = PolynomialRing(qring, "p")
zring = PolynomialRing(field, "z")
T = field(base([(protocol["target_reciprocal"] >> i) & 1 for i in range(41)]))


def decode(value):
    return field(base([(int(value) >> i) & 1 for i in range(41)]))


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def pair_parameters(masks, rotation):
    a, b = (decode(mask << 1) for mask in masks)
    return ((a+b)**(1 << rotation), (a*b)**(1 << rotation))


def left_block(masks):
    a, p = pair_parameters(masks[0], 0)
    b, q0 = pair_parameters(masks[1], 7)
    aa, bb, pp, qq = ([x**i for i in range(9)] for x in (a, b, p, q0))
    coeff = [field.zero() for _ in range(9)]
    for ea, eb, ep, eq, ez in universal["terms"]:
        coeff[ez] += aa[ea]*bb[eb]*pp[ep]*qq[eq]
    return zring(coeff)


def target_right_roots(left):
    # Upper reciprocal-coordinate equation on the finite chart.
    polynomial = vring([T*T+left*left, left*T, 1+(left*T)**2])
    if polynomial == 0:
        return None
    return [root for root, _ in polynomial.roots()]


def right_fiber_test(right, gb, roots_a, a, b):
    aa, bb, zz = ([x**i for i in range(9)] for x in (a, b, right))
    qq = [q**i for i in range(9)]
    coeff = [qring.zero() for _ in range(9)]
    for ea, eb, ep, eq, ez in universal["terms"]:
        coeff[ep] += aa[ea]*bb[eb]*qq[eq]*zz[ez]
    h = pring(coeff)
    gcds = 0
    for index, root in enumerate(roots_a):
        gcds += 1
        common = gb.gcd(h(root))
        if common.degree() > 0:
            qroots = [encode(value) for value, _ in common.roots()]
            assert qroots
            return True, gcds, index, qroots
    return False, gcds, None, []


start_all = time.monotonic_ns()
right_a, right_b = [decode(seed << 1)**(1 << rotation)
                    for seed, rotation in zip(fiber["seeds"], fiber["rotations"])]
right_roots_a = [(decode(a << 1)*decode(b << 1))**(1 << fiber["rotations"][0])
                 for a, b in fiber["ordered_masks"][0]]
right_roots_b = [(decode(a << 1)*decode(b << 1))**(1 << fiber["rotations"][1])
                 for a, b in fiber["ordered_masks"][1]]
assert len(set(right_roots_a)) == len(set(right_roots_b)) == 32
gb = qring.one()
for root in right_roots_b:
    gb *= q+root
setup_ns = time.monotonic_ns()-start_all
cases = []
for family in source_panel["families"]:
    if family["id"] != "positive" and not family["id"].startswith(("slot0_", "slot1_")):
        continue
    case_start = time.monotonic_ns()
    left = left_block(family["masks"][:2])
    left_roots = left.roots()
    assert left.degree() == 8 and sum(m for _, m in left_roots) == 8
    left_ns = time.monotonic_ns()-case_start
    candidate_rows = []
    for left_root, _ in left_roots:
        candidates = target_right_roots(left_root)
        assert candidates is not None  # exceptional all-right case is retained as failure
        for right in candidates:
            candidate_rows.append((left_root, right))
    upper_ns = time.monotonic_ns()-case_start-left_ns
    hits = []
    gcds = 0
    for left_root, right in candidate_rows:
        hit, count, p_index, q_roots = right_fiber_test(
            right, gb, right_roots_a, right_a, right_b)
        gcds += count
        if hit:
            hits.append({"left_reciprocal": encode(left_root),
                         "right_reciprocal": encode(right),
                         "first_product_index": p_index,
                         "second_product_roots": q_roots})
    fiber_ns = time.monotonic_ns()-case_start-left_ns-upper_ns
    cases.append({"id": family["id"], "left_roots": len(left_roots),
                  "target_derived_right_candidates": len(candidate_rows),
                  "gcds": gcds, "hits": hits,
                  "left_block_ns": left_ns, "target_upper_ns": upper_ns,
                  "right_fiber_ns": fiber_ns})
    print("CASE", family["id"], len(candidate_rows), gcds, len(hits), flush=True)

output = {
    "status": "EXACT_TARGET_DERIVED_FIBER_QUERY_FINISHED",
    "candidate_id": None, "run_id": None,
    "target_count": 1, "batch": False,
    "right_bin_sizes": [len(right_roots_a), len(right_roots_b)],
    "setup_ns": setup_ns, "cases": cases,
    "total_wall_ns": time.monotonic_ns()-start_all,
    "protocol_sha256": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest(),
}
with (HERE / "result.json").open("x") as stream:
    json.dump(output, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(output["status"], len(cases), flush=True)
