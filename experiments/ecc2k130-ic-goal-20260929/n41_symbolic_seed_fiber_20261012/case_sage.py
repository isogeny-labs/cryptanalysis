"""Eliminate both seed-bin product variables without expanding product tuples."""

import argparse
import hashlib
import json
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
argp = argparse.ArgumentParser()
argp.add_argument("--size", type=int, choices=(4, 8, 16, 32), required=True)
argp.add_argument("--coordinate", choices=("positive", "negative"), required=True)
args = argp.parse_args()
protocol = json.loads((HERE / "protocol.json").read_text())
assert protocol["status"] == "FROZEN_BEFORE_N41_SYMBOLIC_FIBER_CASES"
for path, digest in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
panel = json.loads((HERE / "panel.json").read_text())
universal = json.loads((GOAL / "n131_w15_rotated_fouratom_inverse_20261010/resultant.json").read_text())
base = PolynomialRing(GF(2), "t")
t = base.gen()
field = GF(2**41, name="t", modulus=t**41 + t**3 + 1)
qring = PolynomialRing(field, "q")
q = qring.gen()
pring = PolynomialRing(qring, "p")
p = pring.gen()


def decode(value):
    return field(base([(int(value) >> i) & 1 for i in range(41)]))


def product_roots(slot):
    rotation = panel["rotations"][slot]
    roots = []
    for a, b in panel["ordered_masks"][slot][:args.size]:
        roots.append((decode(a << 1) * decode(b << 1)) ** (1 << rotation))
    assert len(set(roots)) == args.size
    return roots


start = time.monotonic_ns()
a, b = [decode(s << 1) ** (1 << r) for s, r in zip(panel["seeds"], panel["rotations"])]
z = decode(panel[args.coordinate + "_reciprocal"])
products_a = product_roots(0)
products_b = product_roots(1)
ga = pring.one()
for root in products_a:
    ga *= p + root
gb = qring.one()
for root in products_b:
    gb *= q + root
aa, bb, zz = ([x**i for i in range(9)] for x in (a, b, z))
qq = [q**i for i in range(9)]
coeff = [qring.zero() for _ in range(9)]
for ea, eb, ep, eq, ez in universal["terms"]:
    coeff[ep] += aa[ea] * bb[eb] * qq[eq] * zz[ez]
h = pring(coeff)
build_ns = time.monotonic_ns() - start
inner = ga.resultant(h)
inner_ns = time.monotonic_ns() - start - build_ns
joint = gb.resultant(inner)
outer_ns = time.monotonic_ns() - start - build_ns - inner_ns
output = {"status": "PASS_SYMBOLIC_FIBER_CASE", "candidate_id": None,
          "size": args.size, "coordinate": args.coordinate,
          "joint_zero": bool(joint == 0), "source_product_degree": [int(ga.degree()), int(gb.degree())],
          "four_atom_degree_p": int(h.degree()), "eliminated_degree_q": int(inner.degree()),
          "build_ns": build_ns, "first_resultant_ns": inner_ns,
          "second_resultant_ns": outer_ns,
          "protocol_sha256": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest()}
with (HERE / f"result_{args.size}_{args.coordinate}.json").open("x") as stream:
    json.dump(output, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(output["status"], args.size, args.coordinate, bool(joint == 0), flush=True)
