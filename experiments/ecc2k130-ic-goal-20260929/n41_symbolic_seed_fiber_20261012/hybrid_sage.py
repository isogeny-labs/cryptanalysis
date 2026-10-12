"""One-sided product enumeration with an exact opposite-fiber GCD."""

import hashlib
import json
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
protocol = json.loads((HERE / "hybrid_protocol.json").read_text())
assert protocol["status"] == "FROZEN_BEFORE_HYBRID_FIBER_GCD"
for path, digest in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
panel = json.loads((HERE / "panel.json").read_text())
audit = json.loads((HERE / "audit.json").read_text())
truth = {(r["size"], r["coordinate"]): bool(r["group_law_matches"]) for r in audit["cases"]}
universal = json.loads((GOAL / "n131_w15_rotated_fouratom_inverse_20261010/resultant.json").read_text())
base = PolynomialRing(GF(2), "t")
t = base.gen()
field = GF(2**41, name="t", modulus=t**41 + t**3 + 1)
qring = PolynomialRing(field, "q")
q = qring.gen()
pring = PolynomialRing(qring, "p")


def decode(value):
    return field(base([(int(value) >> i) & 1 for i in range(41)]))


def product_roots(slot, size):
    rotation = panel["rotations"][slot]
    roots = [(decode(a << 1) * decode(b << 1)) ** (1 << rotation)
             for a, b in panel["ordered_masks"][slot][:size]]
    assert len(set(roots)) == size
    return roots


rows = []
for size in panel["sizes"]:
    for coordinate in ("positive", "negative"):
        start = time.monotonic_ns()
        a, b = [decode(s << 1) ** (1 << r)
                for s, r in zip(panel["seeds"], panel["rotations"])]
        z = decode(panel[coordinate + "_reciprocal"])
        roots_a = product_roots(0, size)
        roots_b = product_roots(1, size)
        gb = qring.one()
        for root in roots_b:
            gb *= q + root
        aa, bb, zz = ([x**i for i in range(9)] for x in (a, b, z))
        qq = [q**i for i in range(9)]
        coeff = [qring.zero() for _ in range(9)]
        for ea, eb, ep, eq, ez in universal["terms"]:
            coeff[ep] += aa[ea] * bb[eb] * qq[eq] * zz[ez]
        h = pring(coeff)
        build_ns = time.monotonic_ns() - start
        # Put the known positive product last, so a hit cannot gain an
        # artificial best-case advantage from the control's frozen ordering.
        ordered_a = roots_a[1:] + roots_a[:1]
        gcds = 0
        hit = False
        for root in ordered_a:
            gcds += 1
            if gb.gcd(h(root)).degree() > 0:
                hit = True
                break
        gcd_ns = time.monotonic_ns() - start - build_ns
        assert hit == truth[(size, coordinate)]
        rows.append({"size": size, "coordinate": coordinate, "hit": hit,
                     "gcds": gcds, "build_ns": build_ns, "gcd_ns": gcd_ns})
        print("HYBRID", size, coordinate, hit, gcds, flush=True)

output = {"status": "PASS_ONE_SIDED_FIBER_GCD_PANEL", "candidate_id": None,
          "cases": rows,
          "protocol_sha256": hashlib.sha256((HERE / "hybrid_protocol.json").read_bytes()).hexdigest()}
with (HERE / "hybrid_result.json").open("x") as stream:
    json.dump(output, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(output["status"], len(rows))
